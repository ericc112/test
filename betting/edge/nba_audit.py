"""Fix 1 instrumentation on a backtest corpus (edge/nba_backtest.py): where the simulation's points leak.
  python -m edge.nba_audit TAG [TAG2 ...]
For each corpus: the raw simulation-vs-DraftKings logit gap per stat (all, projected top five, bench), the same
gap against what actually happened, and the leak by level: team possessions, points, FGA, FTA, 3PA, offensive
rebounds, assists; player minutes; per-minute rates; the distribution's centre (median vs mean)."""
from __future__ import annotations

import gzip
import json
import os
import sys

import numpy as np

from .blend import HERE

STATS = ("pts", "reb", "ast", "tpm", "pra", "pr", "pa", "ra")


def lg(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def load(tag: str) -> dict:
    return json.load(gzip.open(os.path.join(HERE, "data", "nba_bt", f"corpus_{tag}.json.gz"), "rt"))


def priced(legs):
    """Main-line legs with a de-vigged DraftKings price and a non-degenerate simulated over."""
    return [l for l in legs if l["q"] is not None and 0 < l["p_over"] < 1 - l["p_push"]]


def tilt(legs, by=None) -> dict:
    """Mean logit(simulation over, push excluded) - logit(DraftKings over); and each against the result."""
    out = {}
    for st in STATS:
        L = [l for l in priced(legs) if l["stat"] == st and (by is None or by(l))]
        if len(L) < 5:
            continue
        sim = np.array([l["p_over"] / (1 - l["p_push"]) for l in L]); q = np.array([l["q"] for l in L])
        y = np.array([1.0 if l["y"] > l["line"] else 0.0 for l in L]); dec = np.array([l["y"] != l["line"] for l in L])
        out[st] = {"n": len(L), "gap_dk": float(np.mean(lg(sim) - lg(q))), "sim_over": float(sim.mean()), "dk_over": float(q.mean()),
                   "act_over": float(y[dec].mean()) if dec.any() else None,
                   "mean_minus_line": float(np.mean([l["sim_mean"] - l["line"] for l in L])), "median_minus_line": float(np.mean([l["sim_med"] - l["line"] for l in L])),
                   "actual_minus_line": float(np.mean([l["y"] - l["line"] for l in L]))}
    return out


def leak(c: dict) -> dict:
    T, P = c["teams"], c["players"]
    tm = lambda k: float(np.mean([t[f"sim_{k}"] - t[f"act_{k}"] for t in T if t.get(f"act_{k}") is not None]))
    out = {"team": {k: tm(k) for k in ("pts", "poss", "fga", "fta", "3pa", "orb", "ast")}}
    for lab, sel in (("top5", lambda p: p["top5"]), ("bench", lambda p: not p["top5"])):
        S = [p for p in P if sel(p)]
        mins = np.array([[p["sim_min"], p["act_min"]] for p in S])
        rate = {}
        for k in ("pts", "reb", "ast", "f3m", "fta"):
            sim_r = sum(p[f"sim_{k}"] for p in S) / sum(p["sim_min"] for p in S)
            act_r = sum(p[f"act_{k}"] for p in S) / sum(p["act_min"] for p in S)
            rate[k] = {"sim_per36": 36 * sim_r, "act_per36": 36 * act_r, "ratio": sim_r / act_r}
        out[lab] = {"n": len(S), "min_bias": float((mins[:, 0] - mins[:, 1]).mean()), "min_mae": float(np.abs(mins[:, 0] - mins[:, 1]).mean()),
                    "per36": rate, "pts_bias": float(np.mean([p["sim_pts"] - p["act_pts"] for p in S]))}
    return out


def report(tag: str) -> dict:
    c = load(tag)
    L = c["legs"]
    res = {"tag": tag, "cfg": c["cfg"], "legs": len(L), "priced": len(priced(L)), "tilt": tilt(L),
           "tilt_top5": tilt(L, lambda l: l["top5"]), "tilt_bench": tilt(L, lambda l: not l["top5"]), "leak": leak(c)}
    return res


def show(r: dict):
    print(f"\n=== {r['tag']} {r['cfg']} | {r['legs']} legs, {r['priced']} priced")
    print(f"{'stat':5} {'n':>5} {'gap_dk':>7} {'top5':>7} {'bench':>7} | sim_over dk_over act_over | mean-line med-line act-line")
    for st in STATS:
        a = r["tilt"].get(st)
        if not a:
            continue
        t5, bn = r["tilt_top5"].get(st, {}), r["tilt_bench"].get(st, {})
        print(f"{st:5} {a['n']:5d} {a['gap_dk']:+7.2f} {t5.get('gap_dk', float('nan')):+7.2f} {bn.get('gap_dk', float('nan')):+7.2f} | "
              f"{a['sim_over']:.3f}    {a['dk_over']:.3f}   {a['act_over']:.3f}   | {a['mean_minus_line']:+6.2f}    {a['median_minus_line']:+6.2f}  {a['actual_minus_line']:+6.2f}")
    lk = r["leak"]
    print("team (sim - actual):", {k: round(v, 2) for k, v in lk["team"].items()})
    for lab in ("top5", "bench"):
        x = lk[lab]
        print(f"{lab}: n {x['n']} minutes bias {x['min_bias']:+.2f} (MAE {x['min_mae']:.2f}), points bias {x['pts_bias']:+.2f}; per-36 sim/actual: "
              + ", ".join(f"{k} {v['sim_per36']:.1f}/{v['act_per36']:.1f}" for k, v in x["per36"].items()))


if __name__ == "__main__":
    for t in sys.argv[1:]:
        show(report(t))


def audit_sides(year: int = 2026) -> dict:
    """Fix 4: how safely the feed's unlabelled over/under pairs are matched. For each main line: is a milestone at the
    same threshold available, does the chosen 'over' sit on it, is the pair near-symmetric (where a swap barely moves
    the de-vigged price), and is the ladder monotone around the line (P(k-1+) >= P(over) >= P(k+1+))."""
    from .nba_backtest import dk_lines, imp
    hist = json.load(gzip.open(os.path.join(HERE, "data", "nba_dk_hist", f"{year}.json.gz"), "rt"))
    n = has = sym = bad_gap = mono_bad = mono_n = asym_flip = 0
    gaps = []
    for gid, g in hist.items():
        for pid, L in dk_lines(g).items():
            for st, r in L.items():
                n += 1
                if r["match"] is None:
                    continue
                has += 1
                m = r["match"]; gaps.append(m["gap_over"])
                if m["sym"] < 0.02:
                    sym += 1
                if m["gap_over"] > 0.05:
                    bad_gap += 1
                    if m["sym"] >= 0.02 and m["gap_other"] - m["gap_over"] < 0.02:
                        asym_flip += 1          # asymmetric pair yet the milestone can't tell the sides apart: a real risk
                k = int(r["line"] + 0.5); lad = {int(a): b for a, b in r["ms"].items()}
                lo_k = max((x for x in lad if x < k), default=None); hi_k = min((x for x in lad if x > k), default=None)
                if lo_k is not None and hi_k is not None:          # nearest milestones either side (ladders skip values)
                    mono_n += 1
                    po = imp(r["over"])
                    if not (imp(lad[lo_k]) + 0.03 >= po >= imp(lad[hi_k]) - 0.03):
                        mono_bad += 1
    return {"lines": n, "with_milestone": has, "share_with_milestone": has / max(n, 1), "near_symmetric": sym,
            "over_far_from_milestone(>5pts)": bad_gap, "ambiguous_asymmetric": asym_flip, "ambiguous_rate": asym_flip / max(has, 1),
            "ladder_checked": mono_n, "ladder_inconsistent": mono_bad, "ladder_inconsistent_rate": mono_bad / max(mono_n, 1),
            "median_gap_over": float(np.median(gaps)) if gaps else None}


def pit(tag: str) -> dict:
    """Shape vs reality (Fix 4 substitute: the feed has one milestone per line, not a ladder): where each result
    falls in the simulated distribution, randomized within ties. Uniform = right shape; a hump in the middle =
    simulated spread too wide; mass at the ends = too narrow. Also the over rate by segment: simulation, DraftKings,
    actual."""
    c = load(tag); rng = np.random.default_rng(0)
    out = {}
    for seg, sel in (("all", lambda l: True), ("top5", lambda l: l["top5"]), ("bench", lambda l: not l["top5"])):
        L = [l for l in priced(c["legs"]) if sel(l) and l["y"] != l["line"]]
        # PIT needs the CDF at y: rebuild from p_over at the line only is not enough, so use quartiles: share of
        # results inside the simulated 25th-75th range (should be ~50%) and below the median (should be ~50%)
        inside = np.mean([l["sim_q25"] <= l["y"] <= l["sim_q75"] for l in L])
        below_med = np.mean([l["y"] < l["sim_med"] for l in L])
        out[seg] = {"n": len(L), "inside_25_75": float(inside), "below_median": float(below_med),
                    "sim_over": float(np.mean([l["p_over"] / (1 - l["p_push"]) for l in L])), "dk_over": float(np.mean([l["q"] for l in L])),
                    "act_over": float(np.mean([l["y"] > l["line"] for l in L])),
                    "mean_minus_median": float(np.mean([l["sim_mean"] - l["sim_med"] for l in L]))}
    return out


def skill(tag: str) -> dict:
    """The simulation alone against what happened, on DraftKings' main lines: log loss, Brier, and the over-rate gap
    per segment (calibration in the large). Lower log loss = a better simulation."""
    c = load(tag)
    L = [l for l in priced(c["legs"]) if l["y"] != l["line"]]
    out = {}
    for seg, sel in (("all", lambda l: True), ("top5", lambda l: l["top5"]), ("bench", lambda l: not l["top5"])):
        S = [l for l in L if sel(l)]
        p = np.clip([l["p_over"] / (1 - l["p_push"]) for l in S], 1e-4, 1 - 1e-4); y = np.array([float(l["y"] > l["line"]) for l in S])
        q = np.clip([l["q"] for l in S], 1e-4, 1 - 1e-4)
        out[seg] = {"n": len(S), "ll_sim": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), "ll_dk": float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q))),
                    "brier_sim": float(np.mean((p - y) ** 2)), "over_gap": float(p.mean() - y.mean()), "dk_gap": float(q.mean() - y.mean())}
    return out


def joint_check(tag: str = "base", min_games: int = 40) -> dict:
    """Fix 6: combos come from the same simulated box scores (joint). Compare each player's simulated points-assists
    and points-rebounds correlation with his real game-to-game correlation (three seasons, min_games+ games)."""
    import sys as _s
    _s.path.insert(0, HERE)
    from gamesim import nba as gnba, nba_research as gres
    c = load(tag)
    sim = {}
    for p in c["players"]:
        sim.setdefault(p["pid"], []).append((p["corr_pa"], p["corr_pr"]))
    G = gnba.season_games("nba", "20261018", "20261103")
    RS = gres.Research("nba", G, 2026)
    rows = []
    for pid, v in sim.items():
        L = [e for e in RS.logs.get(pid, []) if e["min"] >= 10]
        if len(L) < min_games:
            continue
        pts = np.array([e["pts"] for e in L]); ast = np.array([e["ast"] for e in L]); reb = np.array([e["reb"] for e in L])
        rows.append({"pid": pid, "n": len(L), "real_pa": float(np.corrcoef(pts, ast)[0, 1]), "sim_pa": float(np.mean([x[0] for x in v])),
                     "real_pr": float(np.corrcoef(pts, reb)[0, 1]), "sim_pr": float(np.mean([x[1] for x in v]))})
    d_pa = np.array([r["sim_pa"] - r["real_pa"] for r in rows]); d_pr = np.array([r["sim_pr"] - r["real_pr"] for r in rows])
    return {"players": len(rows), "pa": {"real_mean": float(np.mean([r["real_pa"] for r in rows])), "sim_mean": float(np.mean([r["sim_pa"] for r in rows])),
                                         "mean_diff": float(d_pa.mean()), "share_over_0.15": float(np.mean(np.abs(d_pa) > 0.15))},
            "pr": {"real_mean": float(np.mean([r["real_pr"] for r in rows])), "sim_mean": float(np.mean([r["sim_pr"] for r in rows])),
                   "mean_diff": float(d_pr.mean()), "share_over_0.15": float(np.mean(np.abs(d_pr) > 0.15))}}
