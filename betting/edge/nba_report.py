"""Nightly NBA tables (permanent parts of the nba-picks report):
  skill      Brier and log loss of each component alone and of the blend, on graded NBA legs (Fix 2)
  labels     legs, average predicted, realized and gap per label, overall and per stat (Fix 5)
  holdout    the same headline numbers on the permanent holdout (Wednesday legs, never fitted on; Fix 8)
  clv        closing line value of every published leg (Fix 4)
  tilt       tonight's raw simulation-vs-DraftKings gap by stat and segment (Fix 1 / Fix 7)
"""
from __future__ import annotations

import math

import numpy as np

from .learn import graded, is_holdout


def _f(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


def _scores(ps, ys):
    if not ps:
        return None
    p = np.clip(ps, 1e-4, 1 - 1e-4); y = np.array(ys)
    return {"n": len(ps), "brier": float(np.mean((p - y) ** 2)), "logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))}


def skill(rows: list[dict]) -> dict:
    out = {}
    for k in ("p_model", "p_market", "p_hist", "p_final"):
        R = [r for r in rows if _f(r.get(k)) is not None]
        out[k.replace("p_", "")] = _scores([_f(r[k]) for r in R], [1.0 if r["status"] == "won" else 0.0 for r in R])
    both = [r for r in rows if all(_f(r.get(k)) is not None for k in ("p_model", "p_market"))]
    out["same_legs_n"] = len(both)
    if both:
        y = [1.0 if r["status"] == "won" else 0.0 for r in both]
        out["same_legs"] = {k: _scores([_f(r[k]) for r in both], y) for k in ("p_model", "p_market", "p_final")}
    return out


def labels(rows: list[dict], by_stat: bool = False) -> list[dict]:
    groups = {}
    for r in rows:
        if _f(r.get("p_final")) is None:
            continue
        k = (r.get("confidence"), r.get("market") if by_stat else "all")
        groups.setdefault(k, []).append(r)
    out = []
    for (lab, st), R in sorted(groups.items(), key=lambda kv: (str(kv[0][1]), str(kv[0][0]))):
        pred = float(np.mean([_f(r["p_final"]) for r in R])); real = float(np.mean([r["status"] == "won" for r in R]))
        out.append({"label": lab, "stat": st, "legs": len(R), "pred": pred, "real": real, "gap": real - pred,
                    "se": math.sqrt(max(real * (1 - real), 1e-9) / len(R))})
    return out


def nightly(bets: list[dict]) -> dict:
    nba = [r for r in graded(bets) if r.get("sport") == "nba"]
    hold = [r for r in nba if is_holdout(r)]
    pub = [r for r in nba if r.get("action") in ("bet", "lean")]
    return {"graded": len(nba), "holdout": len(hold), "skill_all": skill(nba), "skill_holdout": skill(hold),
            "labels": labels(nba), "labels_by_stat": labels(nba, True), "labels_holdout": labels(hold),
            "published": {"n": len(pub), "hit": float(np.mean([r["status"] == "won" for r in pub])) if pub else None,
                          "pred": float(np.mean([_f(r["p_final"]) for r in pub])) if pub else None}}


def markdown(t: dict, clv: dict | None = None, tilt: dict | None = None) -> str:
    f = lambda v, d=3: "-" if v is None else f"{v:.{d}f}"
    L = ["## Track record (graded NBA legs)", ""]
    if not t["graded"]:
        L.append("No NBA legs graded yet: the tables fill in as tonight's legs settle. Headline accuracy is reported on the Wednesday holdout only.")
    else:
        L += [f"Graded NBA legs: {t['graded']} (holdout, never fitted on: {t['holdout']}).", "",
              "| Source | Legs | Brier | Log loss | Holdout Brier | Holdout log loss |", "|---|---|---|---|---|---|"]
        for k in ("model", "market", "hist", "final"):
            a, h = t["skill_all"].get(k), t["skill_holdout"].get(k)
            L.append(f"| {k} | {a['n'] if a else 0} | {f(a and a['brier'])} | {f(a and a['logloss'])} | {f(h and h['brier'])} | {f(h and h['logloss'])} |")
        L += ["", "| Label | Legs | Avg predicted | Realized | Gap |", "|---|---|---|---|---|"]
        L += [f"| {x['label']} | {x['legs']} | {x['pred']:.1%} | {x['real']:.1%} | {x['gap']:+.1%} |" for x in t["labels"]]
        if t["published"]["n"]:
            L.append(f"\nPublished legs: {t['published']['n']}, predicted {t['published']['pred']:.1%}, realized {t['published']['hit']:.1%}.")
    if clv is not None:
        L += ["", "## Closing line value (published legs)", ""]
        if clv.get("with_clv"):
            L.append(f"{clv['with_clv']} of {clv['legs']} published legs have a DraftKings close: mean CLV {clv['mean_clv']:+.3f}, "
                     f"beat the close {clv['beat_close']:.0%}." + (f" Flagged (100+ legs losing to the close): {', '.join(clv['flags'])}." if clv.get("flags") else ""))
        else:
            L.append(f"{clv.get('legs', 0)} published legs, none with a DraftKings close yet.")
        if clv.get("missing"):
            L.append("Without CLV: " + ", ".join(f"{k} ({v})" for k, v in clv["missing"].items()) + ".")
    if tilt:
        L += ["", "## Tonight's raw tilt (simulation vs DraftKings, logit, main lines)", "", "| Stat | All | Top five | Bench |", "|---|---|---|---|"]
        L += [f"| {st} | {f(v.get('all'), 2)} | {f(v.get('top5'), 2)} | {f(v.get('bench'), 2)} |" for st, v in sorted(tilt.items())]
    return "\n".join(L)


def tilt_by_segment(rows: list[dict]) -> dict:
    """Tonight's raw gap from priced rows (standard main lines with a DraftKings price)."""
    lg = lambda p: math.log(min(max(p, 1e-4), 1 - 1e-4) / (1 - min(max(p, 1e-4), 1 - 1e-4)))
    acc = {}
    for r in rows:
        if "error" in r or r.get("odds_type") != "standard" or r.get("p_market") is None or not r.get("dk"):
            continue
        if abs(r["dk"]["line"] - r["line"]) > 1.0 or r.get("p_model_raw") is None:
            continue
        g = lg(r["p_model_raw"]) - lg(r["p_market"])          # both at the selected side: same sign convention
        g = g if r["side"] == "over" else -g
        for seg in ("all", "top5" if r.get("top5") else "bench"):
            acc.setdefault(r["stat_key"], {}).setdefault(seg, []).append(g)
    return {st: {seg: float(np.mean(v)) for seg, v in d.items() if len(v) >= 5} for st, d in acc.items()}
