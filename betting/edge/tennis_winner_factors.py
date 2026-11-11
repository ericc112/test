"""Do the factors a handicapper looks at add anything to the ratings' match winner? (user, 2026-11-11)

The user listed what decides a tennis match beyond serve and return: surface, form against who they beat, margin,
improving or declining, fatigue and rest, recent retirements and layoffs, head-to-head, event history, handedness,
pressure (break points saved and converted, tiebreaks, deciding sets, coming back from a set down), first serves, aces
and double faults. Each one that the TennisMyLife match database records is built here walk-forward: for every match,
from that player's matches before it (earlier rounds of the same event included), and tested as a term on the
ratings' winner probability (tennis_hist.Ratings with the pricer's settings, refitted as of each event, day-to-day form
included): fitted on 2025-01-01 to 2026-08-31, scored once on 2026-09-01 on. A factor earns a place only if it lowers
the test log loss with a 95% bootstrap interval that excludes zero; then it runs in shadow before it is published
(user rule: 200+ graded matches or 14 days, better on log loss and calibration).

Not testable from reliable data and so not used (they stay off the probability, not guessed): injuries beyond
recorded retirements and walkovers, altitude, weather and wind, ball type, court speed, travel, motivation and crowd.
  python -m edge.tennis_winner_factors        -> data/tennis_bt/winner_factors.json"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict

import numpy as np

from .blend import HERE

TUNE = (20250101, 20260831)
TEST = (20260901, 99999999)
OUT = os.path.join(HERE, "data", "tennis_bt", "winner_factors.json")
SET_RE = re.compile(r"(\d+)-(\d+)(?:\(\d+\))?")

FACTORS = {
    "elo_overall": "Elo win chance, all surfaces (logit)",
    "elo_surface": "Elo win chance on this surface only (logit)",
    "surface_win52": "win share on this surface, last 52 weeks",
    "form10_vs_expected": "last 10 matches: wins minus what Elo expected against those opponents",
    "dominance52": "share of games won, last 52 weeks",
    "trend90": "Elo change over the last 90 days (improving or declining)",
    "minutes_event": "minutes already played at this event",
    "matches14": "matches in the last 14 days",
    "deep_run_prev": "matches won at the previous event, if it started within 14 days",
    "layoff": "no match in the previous 45 days",
    "retired90": "retirements or walkovers given in the last 90 days",
    "h2h": "head-to-head wins minus losses",
    "h2h_surface": "head-to-head wins minus losses on this surface",
    "event_history": "win share at this tournament in earlier years",
    "lefty": "left-handed against a right-hander",
    "bp_saved": "break points saved, last 52 weeks",
    "bp_converted": "break points converted, last 52 weeks",
    "tiebreaks": "tiebreaks won, last 52 weeks",
    "deciders": "deciding sets won, last 52 weeks",
    "comeback": "matches won after losing the first set, last 52 weeks",
    "first_in": "first serves in, last 52 weeks",
    "ace_minus_df": "aces minus double faults per service point, last 52 weeks",
}


def _sets(score: str):
    return [(int(a), int(b)) for a, b in SET_RE.findall(score or "")]


def _logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


class _Player:
    __slots__ = ("hist", "elo_hist")

    def __init__(self):
        self.hist, self.elo_hist = [], []


def features(matches: list[dict], tour: str) -> dict:
    """{id(match): {"w": {...}, "l": {...}, "elo": (overall p for the winner, surface p for the winner)}} walk-forward."""
    M = sorted([m for m in matches if m["tour"] == tour], key=lambda m: (m["start"], m["ro"], m["date"]))
    P = defaultdict(_Player)
    R, Rs, N, Ns = {}, {}, {}, {}
    h2h = defaultdict(list)                       # frozenset(pair) -> [(day, winner, surface)]
    out = {}
    for m in M:
        day, surf, w, l = m["day"], m["surface"], m["w"], m["l"]
        rw, rl = R.get(w, 1500.0), R.get(l, 1500.0)
        sw, sl = Rs.get((w, surf), 1500.0), Rs.get((l, surf), 1500.0)
        e_all = 1 / (1 + 10 ** ((rl - rw) / 400))
        e_surf = 1 / (1 + 10 ** ((sl - sw) / 400))
        e_mix = 1 / (1 + 10 ** ((0.5 * (rl + sl) - 0.5 * (rw + sw)) / 400))
        feats = {}
        for me, op in ((w, l), (l, w)):
            H_ = P[me].hist
            yr = [x for x in H_ if day - x["day"] <= 365]
            f = {}
            ss = [x for x in yr if x["surf"] == surf and x["done"]]
            f["surface_win52"] = (sum(x["won"] for x in ss) + 3) / (len(ss) + 6)
            done = [x for x in H_ if x["done"]][-10:]
            f["form10_vs_expected"] = sum(x["won"] - x["exp"] for x in done)
            gw = sum(x["gw"] for x in yr); gt = sum(x["gw"] + x["gl"] for x in yr)
            f["dominance52"] = (gw + 30) / (gt + 60)
            eh = P[me].elo_hist
            old = next((e for d, e in reversed(eh) if day - d >= 90), 1500.0)
            f["trend90"] = (R.get(me, 1500.0) - old) / 100
            f["minutes_event"] = sum((x["min"] or 0) for x in H_ if x["ev"] == m["ev"]) / 60
            f["matches14"] = sum(1 for x in H_ if day - x["day"] <= 14)
            prev_ev = next((x for x in reversed(H_) if x["ev"] != m["ev"]), None)
            f["deep_run_prev"] = (sum(x["won"] for x in H_ if prev_ev and x["ev"] == prev_ev["ev"] and x["done"])
                                  if prev_ev and day - prev_ev["day"] <= 14 else 0)
            last = H_[-1]["day"] if H_ else None
            f["layoff"] = float(last is None or day - last > 45)
            f["retired90"] = sum(1 for x in H_ if day - x["day"] <= 90 and x["retired"])
            pair = h2h.get(frozenset((me, op)), [])
            f["h2h"] = max(-3, min(3, sum(1 if x[1] == me else -1 for x in pair)))
            f["h2h_surface"] = max(-3, min(3, sum(1 if x[1] == me else -1 for x in pair if x[2] == surf)))
            evh = [x for x in H_ if x["tname"] == m["tname"] and x["ev"] != m["ev"] and x["done"]]
            f["event_history"] = (sum(x["won"] for x in evh) + 2) / (len(evh) + 4)
            f["lefty"] = float(m[f"{'w' if me == w else 'l'}_hand"] == "L" and m[f"{'l' if me == w else 'w'}_hand"] == "R")
            bps = sum(x["bps"] for x in yr); bpf = sum(x["bpf"] for x in yr)
            bpc = sum(x["bpc"] for x in yr); bpo = sum(x["bpo"] for x in yr)
            f["bp_saved"] = (bps + 0.60 * 40) / (bpf + 40)
            f["bp_converted"] = (bpc + 0.40 * 40) / (bpo + 40)
            tbw = sum(x["tbw"] for x in yr); tb = sum(x["tb"] for x in yr)
            f["tiebreaks"] = (tbw + 3) / (tb + 6)
            dw = sum(x["dw"] for x in yr); dn = sum(x["dn"] for x in yr)
            f["deciders"] = (dw + 3) / (dn + 6)
            cw = sum(x["cw"] for x in yr); cl = sum(x["cl"] for x in yr)
            f["comeback"] = (cw + 0.3 * 6) / (cl + 6)
            sv = sum(x["svpt"] for x in yr)
            f["first_in"] = (sum(x["in1"] for x in yr) + 0.62 * 300) / (sv + 300)
            f["ace_minus_df"] = (sum(x["ace"] for x in yr) - sum(x["df"] for x in yr)) / (sv + 300)
            feats[me] = f
        out[id(m)] = {"w": feats[w], "l": feats[l], "elo": (e_all, e_surf, e_mix)}
        # ---- record the match for both players
        sets = _sets(m["score"])
        done = bool(m["sc"])
        raw = m.get("raw") or {}
        gi = lambda k: int(raw.get(k) or 0) if str(raw.get(k) or "").isdigit() else 0
        bo = m["bo"] or 3
        need = bo // 2 + 1
        for me, op, s in ((w, l, "w"), (l, w, "l")):
            o = "l" if s == "w" else "w"
            mine = [(a, b) if s == "w" else (b, a) for a, b in sets]
            tb = [x for x in mine if max(x) == 7 and min(x) == 6]
            dec = done and len(sets) == 2 * need - 1
            lost1 = bool(mine) and mine[0][0] < mine[0][1]
            P[me].hist.append({"day": day, "surf": surf, "done": done, "won": s == "w", "exp": e_mix if s == "w" else 1 - e_mix,
                               "gw": sum(a for a, _ in mine) if done else 0, "gl": sum(b for _, b in mine) if done else 0,
                               "min": m["minutes"], "ev": m["ev"], "tname": m["tname"],
                               "retired": (not done) and s == "l" and bool(re.search(r"RET|W/O|DEF|ABN", m["score"] or "", re.I)),
                               "bps": gi(f"{s}_bpSaved"), "bpf": gi(f"{s}_bpFaced"),
                               "bpc": gi(f"{o}_bpFaced") - gi(f"{o}_bpSaved"), "bpo": gi(f"{o}_bpFaced"),
                               "tbw": sum(1 for a, b in tb if a > b), "tb": len(tb), "dw": int(dec and s == "w"), "dn": int(dec),
                               "cw": int(done and lost1 and s == "w"), "cl": int(done and lost1),
                               "svpt": gi(f"{s}_svpt"), "in1": gi(f"{s}_1stIn"), "ace": gi(f"{s}_ace"), "df": gi(f"{s}_df")})
        h2h[frozenset((w, l))].append((day, w, surf)) if done else None
        if done:
            kw, kl = 250 / (N.get(w, 0) + 5) ** 0.4, 250 / (N.get(l, 0) + 5) ** 0.4
            R[w], R[l] = rw + kw * (1 - e_all), rl - kl * (1 - e_all)
            ksw, ksl = 250 / (Ns.get((w, surf), 0) + 5) ** 0.4, 250 / (Ns.get((l, surf), 0) + 5) ** 0.4
            Rs[(w, surf)], Rs[(l, surf)] = sw + ksw * (1 - e_surf), sl - ksl * (1 - e_surf)
            N[w], N[l] = N.get(w, 0) + 1, N.get(l, 0) + 1
            Ns[(w, surf)], Ns[(l, surf)] = Ns.get((w, surf), 0) + 1, Ns.get((l, surf), 0) + 1
            P[w].elo_hist.append((day, R[w])); P[l].elo_hist.append((day, R[l]))
    return out


def _fit(X, y, off, ridge=1.0):
    """Logistic regression with an offset (the ratings' logit), Newton steps, ridge on standardized columns."""
    b = np.zeros(X.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-(off + X @ b)))
        Hm = (X * (p * (1 - p))[:, None]).T @ X + ridge * np.eye(X.shape[1])
        step = np.linalg.solve(Hm, X.T @ (y - p) - ridge * b)
        b += step
        if np.abs(step).max() < 1e-8:
            break
    se = np.sqrt(np.diag(np.linalg.inv(Hm)))
    return b, se


def _ll(p, y):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def run(out: str | None = None, log=print) -> dict:
    from . import tennis as T
    from . import tennis_hist as H
    from .tennis_factor_study import predict
    st = T.tml_state(refresh=False)
    study = json.load(open(T.STUDY))
    res = {"_factors": FACTORS, "_method": __doc__.split("\n\n")[1].strip()}
    rng = np.random.default_rng(11)
    for tour in ("ATP", "WTA"):
        ch, fm = study[tour]["chosen"], study[tour]["form"]["B1"]
        log(f"{tour}: walk-forward features...")
        F = features(st["matches"], tour)
        log(f"{tour}: walk-forward ratings (refitted as of each event)...")
        sel, Pp, pts = predict(st["matches"], tour, {"B1": H.Ratings(H=ch["H"], lam=ch["lam"])}, TUNE[0], TEST[1], log=log)
        keys = list(FACTORS)
        rows = {"tune": [], "test": []}
        for i, m in enumerate(sel):
            if not m["sc"] or min(pts["B1"][i]) < 400 or id(m) not in F:
                continue
            per = "tune" if m["start"] <= TUNE[1] else "test"
            pw, pl = Pp["B1"][i]
            base = float(H.win_by_bo(np.array([pw]), np.array([pl]), [m["bo"] or 3], fm["sd"], fm["rho"])[0])
            fw, fl, (e_all, e_surf, _) = F[id(m)]["w"], F[id(m)]["l"], F[id(m)]["elo"]
            x = []
            for k in keys:
                if k == "elo_overall":
                    x.append(float(_logit(e_all)))
                elif k == "elo_surface":
                    x.append(float(_logit(e_surf)))
                else:
                    x.append(fw[k] - fl[k])
            rows[per].append((float(_logit(base)), x, m["ev"]))
        out_t = {}
        data = {}
        for per in ("tune", "test"):
            off = np.array([r[0] for r in rows[per]]); X = np.array([r[1] for r in rows[per]], float)
            flip = rng.random(len(off)) < 0.5               # orient each match at random: A is the winner half the time
            off = np.where(flip, -off, off); X = np.where(flip[:, None], -X, X); y = (~flip).astype(float)
            data[per] = (off, X, y, np.array([r[2] for r in rows[per]]))
        off_a, X_a, y_a, _ = data["tune"]; off_b, X_b, y_b, ev_b = data["test"]
        mu, sd = X_a.mean(0), X_a.std(0) + 1e-9
        Za, Zb = (X_a - mu) / sd, (X_b - mu) / sd
        base_b = 1 / (1 + np.exp(-off_b))
        ll0 = _ll(base_b, y_b)
        # ratings-only calibration on the tune period (a scale on the logit), so a factor isn't credited for that
        s_fit, _ = _fit(off_a[:, None], y_a, np.zeros(len(off_a)), ridge=1e-6)
        cal_b = 1 / (1 + np.exp(-(s_fit[0] * off_b)))
        llc = _ll(cal_b, y_b)

        def boot(d):
            u, inv = np.unique(ev_b, return_inverse=True)          # resample events (matches in an event are linked)
            tot, cnt = np.bincount(inv, d, len(u)), np.bincount(inv, None, len(u))
            bs = []
            for _ in range(1000):
                s = rng.integers(0, len(u), len(u))
                bs.append(tot[s].sum() / cnt[s].sum())
            return [round(float(np.percentile(bs, 2.5)), 5), round(float(np.percentile(bs, 97.5)), 5)]

        out_t["matches"] = {"tune": int(len(y_a)), "test": int(len(y_b))}
        out_t["test_log_loss"] = {"ratings": round(float(ll0.mean()), 4), "ratings_recalibrated": round(float(llc.mean()), 4), "coin": round(float(np.log(2)), 4)}
        out_t["test_accuracy_ratings"] = round(float(((base_b > 0.5) == (y_b == 1)).mean()), 4)
        single = {}
        for j, k in enumerate(keys):
            cols = [j]
            b, se = _fit(np.c_[off_a, Za[:, cols]], y_a, np.zeros(len(off_a)), ridge=1.0)
            p = 1 / (1 + np.exp(-(np.c_[off_b, Zb[:, cols]] @ b)))
            d = llc - _ll(p, y_b)                                  # positive = the factor helps beyond calibrated ratings
            ci = boot(d)
            single[k] = {"coef_per_sd": round(float(b[1]), 4), "z_tune": round(float(b[1] / se[1]), 2),
                         "test_gain": round(float(d.mean()), 5), "ci95": ci, "helps": bool(ci[0] > 0)}
        out_t["single"] = single
        b, se = _fit(np.c_[off_a, Za], y_a, np.zeros(len(off_a)), ridge=5.0)
        p_all = 1 / (1 + np.exp(-(np.c_[off_b, Zb] @ b)))
        d_all = llc - _ll(p_all, y_b)
        out_t["all_factors"] = {"test_gain": round(float(d_all.mean()), 5), "ci95": boot(d_all),
                                "test_log_loss": round(float(_ll(p_all, y_b).mean()), 4),
                                "test_accuracy": round(float(((p_all > 0.5) == (y_b == 1)).mean()), 4),
                                "coef_per_sd": {k: round(float(c), 4) for k, c in zip(keys, b[1:])},
                                "ratings_weight": round(float(b[0]), 3)}
        chosen = [k for k in keys if single[k]["z_tune"] >= 2 or single[k]["z_tune"] <= -2]
        if chosen:
            cols = [keys.index(k) for k in chosen]
            b, se = _fit(np.c_[off_a, Za[:, cols]], y_a, np.zeros(len(off_a)), ridge=2.0)
            p_s = 1 / (1 + np.exp(-(np.c_[off_b, Zb[:, cols]] @ b)))
            d_s = llc - _ll(p_s, y_b)
            out_t["selected_on_tune"] = {"factors": chosen, "test_gain": round(float(d_s.mean()), 5), "ci95": boot(d_s),
                                         "test_log_loss": round(float(_ll(p_s, y_b).mean()), 4),
                                         "test_accuracy": round(float(((p_s > 0.5) == (y_b == 1)).mean()), 4),
                                         "coef_per_sd": {k: round(float(c), 4) for k, c in zip(chosen, b[1:])},
                                         "scaler": {k: [round(float(mu[keys.index(k)]), 5), round(float(sd[keys.index(k)]), 5)] for k in chosen},
                                         "ratings_weight": round(float(b[0]), 3)}
        res[tour] = out_t
        log(f"{tour}: ratings {out_t['test_log_loss']} | all factors {out_t['all_factors']['test_gain']:+.4f} {out_t['all_factors']['ci95']}")
    res["_note"] = ("test_gain = test log loss of the calibrated ratings minus the ratings plus the factor (per match; positive = the factor "
                    "helps). A factor earns a shadow run only if its 95% interval (bootstrap over events) is above zero.")
    json.dump(res, open(out or OUT, "w"), indent=1)
    return res


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
