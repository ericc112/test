"""Walk-forward test of the tennis factors on the TennisMyLife database (python -m edge.tennis_factor_study DATA_DIR).

Every match is predicted from matches dated before its event started (Elo and fatigue also see the event's earlier
rounds, which were played before it). Settings are chosen on the tuning period (2025-01-01 to 2026-08-31); the test
period (2026-09-01 on) is scored once.

Variants
  B0  current way: plain 52-week serve / return averages, surface-shrunk, no opponent adjustment.
  B1  opponent-adjusted serve and return ratings, recent matches weighted more (half-life H), ridge lam.
  +indoor, +hand  the same with an indoor/outdoor tour average (ATP) or left/right-hand terms.
  +Elo  the winner probability blended with Elo (weights fit on the tuning period); the simulation's serve-point
        gap is shifted to that probability, keeping the total (so the expected length).
  +fatigue  minutes already played at the event, tested as a term on the winner beyond the model.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from . import tennis as T
from . import tennis_hist as H

TUNE = (20250101, 20260831)
TEST = 20260901


def logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def logreg(X, y, iters=60, ridge=1e-4):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ w)))
        Hm = (X * (p * (1 - p))[:, None]).T @ X + ridge * np.eye(X.shape[1])
        w += np.linalg.solve(Hm, X.T @ (y - p))
    return w, np.sqrt(np.diag(np.linalg.inv(Hm)))


def ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def predict(matches, tour, variants, lo, hi, log=print):
    """For every match of the tour with start in [lo, hi]: each variant's (p_w, p_l) serve-point probabilities, from a
    fit as of the event's start. Returns (list of matches, {variant: array (n, 2)}, {variant: points (n, 2)})."""
    obs = H.observations(matches, tour)
    idx = obs["idx"]
    sel = [m for m in matches if m["tour"] == tour and lo <= m["start"] <= hi]
    days = sorted({m["day"] for m in sel})
    out = {v: np.zeros((len(sel), 2)) for v in variants}
    pts = {v: np.zeros((len(sel), 2)) for v in variants}
    pos = {}
    for i, m in enumerate(sel):
        pos.setdefault(m["day"], []).append(i)
    for di, d in enumerate(days):
        for v, R in variants.items():
            R.fit(obs, d)
            for i in pos[d]:
                m = sel[i]
                w, l = idx[m["w"]], idx[m["l"]]
                out[v][i] = (R.p(w, l, m["surface"], m["indoor"], m["w_hand"], m["l_hand"]),
                             R.p(l, w, m["surface"], m["indoor"], m["l_hand"], m["w_hand"]))
                pts[v][i] = (sum(R.points(w)), sum(R.points(l)))
        if di % 25 == 0:
            log(f"    {tour} {di + 1}/{len(days)} event days")
    return sel, out, pts


def point_ll(sel, P):
    """Mean log-likelihood per serve point of the observed serve points under predictions P (n, 2)."""
    tot, npts = 0.0, 0
    for m, (pw, pl) in zip(sel, P):
        for s, p in (("w", pw), ("l", pl)):
            if m[f"{s}_n"]:
                n, k = m[f"{s}_n"], m[f"{s}_k"]
                tot += k * np.log(p) + (n - k) * np.log(1 - p); npts += n
    return tot / max(npts, 1)


def form_from(sel, P):
    """Day-to-day variation around a variant's predictions (tuning period): residual variance of each side's serve
    rate minus binomial noise, and the correlation of the two sides' residuals."""
    rw, rl, bn = [], [], []
    for m, (pw, pl) in zip(sel, P):
        if m["w_n"] and m["l_n"]:
            rw.append(m["w_k"] / m["w_n"] - pw); rl.append(m["l_k"] / m["l_n"] - pl)
            bn.append((pw * (1 - pw) / m["w_n"] + pl * (1 - pl) / m["l_n"]) / 2)
    rw, rl = np.array(rw), np.array(rl)
    var = max(float((np.mean(rw ** 2) + np.mean(rl ** 2)) / 2 - np.mean(bn)), 1e-5)
    return {"sd": var ** 0.5, "rho": float(np.clip(np.mean(rw * rl) / var, -0.95, 0.0))}


def run(folder: str, out_path: str | None = None, n_sims: int = 3000, log=print):
    M = H.load(folder)
    log(f"{len(M):,} matches loaded")
    fat = H.fatigue(M)
    res = {}
    for tour in ("ATP", "WTA"):
        elo, *_ = H.elo_walk(M, tour)
        # ---- 1. choose H and lam on the tuning period (point log-likelihood), with B0 for reference
        grid = {"B0": H.Ratings(H=1e9, lam=640, lam_s=800, opponent=False, max_age=365)}
        for Hh in (180, 365, 730):
            for lam in (400, 800, 1600):
                grid[f"B1 H{Hh} lam{lam}"] = H.Ratings(H=Hh, lam=lam)
        log(f"  {tour}: tuning {len(grid)} rating variants...")
        cpath = os.path.join(folder, f"_tune_{tour}.npz")
        tsel = [m for m in M if m["tour"] == tour and TUNE[0] <= m["start"] <= TUNE[1]]
        if os.path.exists(cpath) and int(np.load(cpath)["n"]) == len(tsel):
            Z = np.load(cpath)
            tP = {v: Z[f"P_{i}"] for i, v in enumerate(grid)}
        else:
            tsel, tP, tpts = predict(M, tour, grid, *TUNE, log=log)
            np.savez(cpath, n=len(tsel), **{f"P_{i}": tP[v] for i, v in enumerate(grid)})
        tune_ll = {v: point_ll(tsel, tP[v]) for v in grid}
        best = max((v for v in grid if v != "B0"), key=lambda v: tune_ll[v])
        bH, blam = (float(x[1:]) if i == 0 else float(x[3:]) for i, x in enumerate(best.split()[1:]))
        log(f"  {tour}: point log-lik per point " + ", ".join(f"{v} {tune_ll[v]:.5f}" for v in grid) + f" -> {best}")
        extra = {"B1+indoor": H.Ratings(H=bH, lam=blam, indoor=True), "B1+hand": H.Ratings(H=bH, lam=blam, hand=True)}
        esel, eP, _ = predict(M, tour, extra, *TUNE, log=log)
        for v in extra:
            tune_ll[v] = point_ll(esel, eP[v])
        log(f"  {tour}: +indoor {tune_ll['B1+indoor']:.5f}, +hand {tune_ll['B1+hand']:.5f} vs {best} {tune_ll[best]:.5f}")
        use = {"B0": grid["B0"], "B1": H.Ratings(H=bH, lam=blam,
                                                  indoor=tune_ll["B1+indoor"] > tune_ll[best] + 1e-5,
                                                  hand=tune_ll["B1+hand"] > tune_ll[best] + 1e-5)}
        tP["B1"] = tP[best] if not (use["B1"].indoor or use["B1"].hand) else predict(M, tour, {"B1": use["B1"]}, *TUNE, log=log)[1]["B1"]
        forms = {v: form_from(tsel, tP[v]) for v in ("B0", "B1")}
        # ---- 2. winner: model probability, Elo, blend, fatigue (fit on tuning)
        def winner_rows(sel, P, form):
            keep = [i for i, m in enumerate(sel) if m["sc"]]
            pm = H.win_by_bo(P[keep, 0], P[keep, 1], [sel[i]["bo"] for i in keep], form["sd"], form["rho"])
            X = []
            for j, i in enumerate(keep):
                m = sel[i]
                fw, fl = fat.get((id(m), m["w"]), (0, 0, 0)), fat.get((id(m), m["l"]), (0, 0, 0))
                X.append((pm[j], elo[id(m)][0], (fw[0] - fl[0]) / 60, (fw[1] - fl[1]) / 60))
            return np.array(X), keep
        Xt, _ = winner_rows(tsel, tP["B1"], forms["B1"])
        # orientation: rows are written winner-first, so flip half at random for fitting (y = 1 when "A" won)
        rng = np.random.default_rng(1)
        flip = rng.random(len(Xt)) < 0.5
        def oriented(X, flip):
            pm = np.where(flip, 1 - X[:, 0], X[:, 0]); pe = np.where(flip, 1 - X[:, 1], X[:, 1])
            f1 = np.where(flip, -X[:, 2], X[:, 2]); f2 = np.where(flip, -X[:, 3], X[:, 3])
            return pm, pe, f1, f2, (~flip).astype(float)
        pm, pe, f1, f2, y = oriented(Xt, flip)
        wE, seE = logreg(np.c_[logit(pm), logit(pe)], y)
        wF, seF = logreg(np.c_[logit(pm), logit(pe), f1, f2], y)
        log(f"  {tour}: winner blend on tuning: model {wE[0]:.2f}, Elo {wE[1]:.2f}; fatigue terms {wF[2]:+.3f} ± {seF[2]:.3f} (event minutes /60), "
            f"{wF[3]:+.3f} ± {seF[3]:.3f} (last match /60)")
        # ---- 3. test period, scored once
        log(f"  {tour}: test period...")
        ssel, sP, spts = predict(M, tour, use, TEST, 99999999, log=log)
        ok = [i for i, m in enumerate(ssel) if m["sc"] and min(spts["B0"][i]) >= 400]
        ssel = [ssel[i] for i in ok]
        sP = {v: sP[v][ok] for v in sP}
        Xs, _ = winner_rows(ssel, sP["B1"], forms["B1"])
        X0, _ = winner_rows(ssel, sP["B0"], forms["B0"])
        fl2 = np.random.default_rng(2).random(len(Xs)) < 0.5
        pm1, pe1, g1, g2, ys = oriented(Xs, fl2)
        pm0 = np.where(fl2, 1 - X0[:, 0], X0[:, 0])
        pb = 1 / (1 + np.exp(-(np.c_[logit(pm1), logit(pe1)] @ wE)))
        pf = 1 / (1 + np.exp(-(np.c_[logit(pm1), logit(pe1), g1, g2] @ wF)))
        win = {"B0": ll(pm0, ys), "B1": ll(pm1, ys), "Elo": ll(pe1, ys), "B1+Elo": ll(pb, ys), "B1+Elo+fatigue": ll(pf, ys), "coin": float(np.log(2))}
        acc = {"B0": float(np.mean((pm0 > .5) == ys)), "B1": float(np.mean((pm1 > .5) == ys)), "B1+Elo": float(np.mean((pb > .5) == ys))}
        # ---- 4. totals and games won: simulate B0, B1, B1 shifted to the B1+Elo winner probability
        tot = {k: [] for k in ("B0", "B1", "B1+Elo")}
        targets = 1 / (1 + np.exp(-(np.c_[logit(Xs[:, 0]), logit(Xs[:, 1])] @ wE)))           # winner-first orientation
        shifts = H.shift_by_bo(sP["B1"][:, 0], sP["B1"][:, 1], targets, [m["bo"] for m in ssel], forms["B1"]["sd"], forms["B1"]["rho"])
        log(f"  {tour}: simulating {len(ssel)} test matches x 3 variants...")
        for i, m in enumerate(ssel):
            pw0, pl0 = sP["B0"][i]; pw1, pl1 = sP["B1"][i]
            d = float(shifts[i])
            sims = {"B0": T.simulate(pw0, pl0, m["bo"], n=n_sims, seed=i, form=forms["B0"]),
                    "B1": T.simulate(pw1, pl1, m["bo"], n=n_sims, seed=i, form=forms["B1"]),
                    "B1+Elo": T.simulate(pw1 + d, pl1 - d, m["bo"], n=n_sims, seed=i, form=forms["B1"])}
            g, gw = m["sc"]["games"], m["sc"]["games_w"]
            line = float(np.floor(np.median(sims["B0"]["games"]))) + 0.5
            gline = float(np.floor(np.median(sims["B0"]["games_a"]))) + 0.5
            for k, s in sims.items():
                pmf = (np.bincount(s["games"], minlength=80)[:80] + 0.5) / (n_sims + 40)
                tot[k].append((abs(float(s["games"].mean()) - g), float(np.log(pmf[min(g, 79)])), float((s["games"] > line).mean()), g > line,
                               float((s["games_a"] > gline).mean()), gw > gline))
        T_ = {k: np.array(v, dtype=float) for k, v in tot.items()}
        totals = {k: {"games_mae": float(v[:, 0].mean()), "games_log_score": float(v[:, 1].mean()), "line_logloss": ll(v[:, 2], v[:, 3]),
                      "games_won_line_logloss": ll(v[:, 4], v[:, 5])} for k, v in T_.items()}
        levels = {}
        for lv_name, test in (("tour", lambda m: m["level"] not in ("C",)), ("challenger", lambda m: m["level"] == "C")):
            ii = [i for i, m in enumerate(ssel) if test(m)]
            if ii and tour == "ATP":
                levels[lv_name] = {"matches": len(ii), "winner_ll": {"B0": ll(pm0[ii], ys[ii]), "B1": ll(pm1[ii], ys[ii]), "B1+Elo": ll(pb[ii], ys[ii])},
                                   "line_logloss": {k: ll(T_[k][ii, 2], T_[k][ii, 3]) for k in T_}}
        res[tour] = {"tuning_point_ll": tune_ll, "chosen": {"H": bH, "lam": blam, "indoor": use["B1"].indoor, "hand": use["B1"].hand},
                     "form": forms, "elo_blend": {"w": wE.tolist(), "se": seE.tolist()},
                     "fatigue_tuning": {"w": wF.tolist(), "se": seF.tolist()},
                     "test": {"matches": len(ssel), "winner_logloss": win, "winner_acc": acc, "totals": totals, "by_level": levels}}
        log(json.dumps(res[tour]["test"], indent=1))
    if out_path:
        json.dump(res, open(out_path, "w"), indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    return res


if __name__ == "__main__":
    folder = sys.argv[1]
    run(folder, sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "tennis_bt", "factor_study.json"))


# ------------------------------------------------------------------ market anchoring (Tennis Explorer closing odds)
def attach_odds(sel: list[dict], te_cache: str, tour: str) -> list:
    """For each match, the de-vigged closing probability that its winner wins (Tennis Explorer), or None.
    Matched by both surnames, within the event's dates (TennisMyLife dates some events by their start)."""
    import datetime as dt
    from . import tennis_market as TM
    by = {}
    d0 = min(m["day"] for m in sel) if sel else 0
    d1 = max(m["day"] for m in sel) + 17 if sel else -1
    for day in range(d0, d1 + 1):
        date = dt.date.fromordinal(day)
        path = os.path.join(te_cache, f"te_{tour}_{date.isoformat()}.html")
        if not os.path.exists(path):
            continue
        for x in TM.parse(open(path, encoding="utf-8", errors="replace").read(), date.isoformat(), tour):
            if x.get("o1") and x.get("o2") and x.get("p2"):
                k = frozenset((TM.surname_key(x["p1"]), TM.surname_key(x["p2"])))
                by.setdefault(k, []).append((day, x))
    out = []
    for m in sel:
        hit = None
        for kw in TM.tml_key(m["w_name"]):
            for kl in TM.tml_key(m["l_name"]):
                for day, x in by.get(frozenset((kw, kl)), []):
                    if m["day"] - 1 <= day <= m["day"] + 16:
                        p1 = TM.fair(x["o1"], x["o2"])
                        hit = p1 if TM.surname_key(x["p1"]) == kw else 1 - p1
                        break
                if hit is not None:
                    break
            if hit is not None:
                break
        out.append(hit)
    return out


def market_test(folder: str, te_cache: str, study_path: str, n_sims: int = 3000, log=print) -> dict:
    """Does anchoring the simulation's winner probability to the market improve totals and games won? Fit window
    July-August 2026 (blend weights of market and model), test September 2026 on, the same matches for every variant."""
    S = json.load(open(study_path))
    M = H.load(folder)
    out = {}
    for tour in ("ATP", "WTA"):
        ch = S[tour]["chosen"]
        use = {"B0": H.Ratings(H=1e9, lam=640, lam_s=800, opponent=False, max_age=365),
               "B1": H.Ratings(H=ch["H"], lam=ch["lam"], indoor=ch["indoor"], hand=ch["hand"])}
        forms = S[tour]["form"]
        elo, *_ = H.elo_walk(M, tour)
        wE = np.array(S[tour]["elo_blend"]["w"])
        res = {}
        for name, lo, hi in (("fit", 20260701, 20260831), ("test", TEST, 99999999)):
            sel, P, pts = predict(M, tour, use, lo, hi, log=log)
            mk = attach_odds(sel, te_cache, tour)
            ok = [i for i, m in enumerate(sel) if m["sc"] and mk[i] is not None and min(pts["B0"][i]) >= 400]
            log(f"  {tour} {name}: {len(ok)} of {len(sel)} matches with odds and data")
            bo = [sel[i]["bo"] for i in ok]
            pm1 = H.win_by_bo(P["B1"][ok, 0], P["B1"][ok, 1], bo, forms["B1"]["sd"], forms["B1"]["rho"])
            pm0 = H.win_by_bo(P["B0"][ok, 0], P["B0"][ok, 1], bo, forms["B0"]["sd"], forms["B0"]["rho"])
            rows = [(i, pm0[j], pm1[j], elo[id(sel[i])][0], mk[i]) for j, i in enumerate(ok)]
            res[name] = (sel, P, rows)
        # blend weights (market + model + Elo) on the fit window, winner-first rows flipped at random
        sel_f, _, rows_f = res["fit"]
        X = np.array([(logit(r[2]), logit(r[3]), logit(r[4])) for r in rows_f])
        flip = np.random.default_rng(3).random(len(X)) < 0.5
        Xf = np.where(flip[:, None], -X, X)
        y = (~flip).astype(float)
        wM, seM = logreg(np.c_[Xf], y)
        log(f"  {tour}: blend on Jul-Aug (model, Elo, market) = {np.round(wM, 2)} ± {np.round(seM, 2)}")
        sel, P, rows = res["test"]
        Xt = np.array([(logit(r[2]), logit(r[3]), logit(r[4])) for r in rows])
        fl = np.random.default_rng(4).random(len(Xt)) < 0.5
        yt = (~fl).astype(float)
        o = lambda p: np.where(fl, 1 - p, p)
        p_mkt, p_b1, p_b0 = np.array([r[4] for r in rows]), np.array([r[2] for r in rows]), np.array([r[1] for r in rows])
        p_be = 1 / (1 + np.exp(-(Xt[:, :2] @ wE)))
        p_bl = 1 / (1 + np.exp(-(Xt @ wM)))
        win = {"B0": ll(o(p_b0), yt), "B1": ll(o(p_b1), yt), "B1+Elo": ll(o(p_be), yt), "market": ll(o(p_mkt), yt),
               "blend": ll(o(p_bl), yt), "coin": float(np.log(2))}
        tot = {k: [] for k in ("B0", "B1", "B1+Elo", "B1+market", "B1+blend")}
        ii = [r[0] for r in rows]
        bo_t = [sel[i]["bo"] for i in ii]
        sd, rho = forms["B1"]["sd"], forms["B1"]["rho"]
        sh = {k: H.shift_by_bo(P["B1"][ii, 0], P["B1"][ii, 1], tg, bo_t, sd, rho) for k, tg in
              (("B1+Elo", p_be), ("B1+market", p_mkt), ("B1+blend", p_bl))}
        log(f"  {tour}: simulating {len(rows)} test matches x 5 variants...")
        for j, (i, pm0, pm1, pe, pk) in enumerate(rows):
            m = sel[i]
            pw0, pl0 = P["B0"][i]; pw1, pl1 = P["B1"][i]
            sims = {"B0": T.simulate(pw0, pl0, m["bo"], n=n_sims, seed=j, form=forms["B0"]),
                    "B1": T.simulate(pw1, pl1, m["bo"], n=n_sims, seed=j, form=forms["B1"])}
            for k in ("B1+Elo", "B1+market", "B1+blend"):
                d = float(sh[k][j])
                sims[k] = T.simulate(pw1 + d, pl1 - d, m["bo"], n=n_sims, seed=j, form=forms["B1"])
            g, gw = m["sc"]["games"], m["sc"]["games_w"]
            line = float(np.floor(np.median(sims["B0"]["games"]))) + 0.5
            gline = float(np.floor(np.median(sims["B0"]["games_a"]))) + 0.5
            for k, s in sims.items():
                pmf = (np.bincount(s["games"], minlength=80)[:80] + 0.5) / (n_sims + 40)
                # games won: score the loser's side too (half the time) so a winner-first layout can't flatter it
                side_a = j % 2 == 0
                arr = s["games_a"] if side_a else s["games_b"]
                gl = float(np.floor(np.median(sims["B0"]["games_a" if side_a else "games_b"]))) + 0.5
                act = gw if side_a else m["sc"]["games_l"]
                tot[k].append((abs(float(s["games"].mean()) - g), float(np.log(pmf[min(g, 79)])), float((s["games"] > line).mean()), g > line,
                               float((arr > gl).mean()), act > gl))
        Tt = {k: np.array(v, dtype=float) for k, v in tot.items()}
        totals = {k: {"games_mae": float(v[:, 0].mean()), "games_log_score": float(v[:, 1].mean()), "line_logloss": ll(v[:, 2], v[:, 3]),
                      "games_won_line_logloss": ll(v[:, 4], v[:, 5])} for k, v in Tt.items()}
        out[tour] = {"matches": len(rows), "blend_w": wM.tolist(), "blend_se": seM.tolist(), "winner_logloss": win, "totals": totals}
        log(json.dumps(out[tour], indent=1))
    return out
