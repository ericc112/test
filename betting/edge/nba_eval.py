"""Before/after on identical legs (same DraftKings lines and results), walk-forward by day:
  before = current published logic: simulation v1 (minutes^0.8, independent swings), tonight's flat bias vs DK,
           the old blend (.45/.41/.07, +.046, history regressed), old gates, flat entry rule
  after  = candidate: simulation (minutes^1.0, shared swing .8), segment bias table fitted on earlier days,
           market-dominant blend (model .2 / market .8, no history, no intercept), selected side capped at 70%,
           derived gates, standard-error entry rule
  python -m edge.nba_eval BEFORE_TAG AFTER_TAG   (live-like availability corpora)"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

from . import nba_fit as F
from .blend import HERE

OLD_GATES = {"high": 0.65, "medium": 0.58, "max_spread_high": 0.12, "min_hist_n_high": 10}
NEW_GATES = {"high": 0.62, "medium": 0.54, "max_spread_high": 0.16, "min_hist_n_high": 0}
BE = 0.577


def key(r):
    return (r["gid"], r["pid"], r["stat"], r["line"])


def legs_with_keys(tag):
    L = F.load_legs(tag)
    return {key(l): l for l in L}


def walk(tag, mode):
    res = F.run(tag)
    rows = res["rows"]
    out = {}
    L = F.load_legs(tag)
    keys = [key(l) for l in L]
    by_day = {}
    for l in L:
        by_day.setdefault(l["day"], []).append(l)
    # F.run iterates days in order and appends test legs in the same order as load_legs within a day
    i = 0
    for d in sorted(by_day):
        tr = [l for l in L if l["day"] < d]
        if len(tr) < F.MIN_TRAIN:
            continue
        for l in by_day[d]:
            out[key(l)] = rows[i]; i += 1
    return out


def metrics(sel, pkey, gates, entry):
    y = np.array([r["y_sel"] for r in sel]); p = np.clip([r[pkey] for r in sel], 1e-4, 1 - 1e-4)
    lab = F.label_table(sel, pkey, gates)
    if entry == "flat2":
        E = [r for r in sel if r[pkey] >= 0.65 and r[pkey] >= BE + 0.02 and lab_of(r, pkey, gates) == "High"]
    else:
        E = [r for r in sel if lab_of(r, pkey, gates) == "High" and r[pkey] - BE > r[pkey] * (1 - r[pkey]) * 0.1 * abs(F.lg(r["model_o"]) - F.lg(r["market"])) + np.sqrt(r[pkey] * (1 - r[pkey]) / 10000)]
    return {"n": len(sel), "logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), "brier": float(np.mean((p - y) ** 2)),
            "labels": lab, "entry": {"n": len(E), "pred": float(np.mean([r[pkey] for r in E])) if E else None, "real": float(np.mean([r["y_sel"] for r in E])) if E else None},
            "buckets": F.buckets(sel, pkey)}


def lab_of(r, pkey, gates):
    t = F.label_table([r], pkey, gates)
    return next(iter(t))


if __name__ == "__main__":
    before, after = sys.argv[1], sys.argv[2]
    A, B = walk(before, "old"), walk(after, "new")
    common = sorted(set(A) & set(B))
    ra = [A[k] for k in common]; rb = [B[k] for k in common]
    sa = F.selected(ra, "old"); sb = F.selected(rb, "w0.2")
    for r in sb:
        r["p_cap"] = min(r["p_sel"], 0.70)
    out = {"legs": len(common), "days": sorted({r["day"] for r in ra})}
    out["before"] = metrics(sa, "p_sel", OLD_GATES, "flat2")
    out["after"] = metrics(sb, "p_cap", NEW_GATES, "se1")
    # over-side scores (not selection-dependent) and the market baseline
    y = np.array([r["y"] for r in rb])
    for nm, rows, k in (("before_blend", ra, "old"), ("after_blend", rb, "w0.2"), ("market", rb, "market"), ("model_before", ra, "model"), ("model_after", rb, "model")):
        p = np.clip([r[k] for r in rows], 1e-4, 1 - 1e-4)
        out[f"over_{nm}"] = {"logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), "brier": float(np.mean((p - y) ** 2))}
    out["after_vs_market"] = F.boot_diff(rb, "w0.2", "market")
    out["after_vs_before"] = F.boot_diff([{**b, "old_": a["old"]} for a, b in zip(ra, rb)], "w0.2", "old_")
    # MAE of the simulated mean vs the DraftKings line
    La, Lb = legs_with_keys(before), legs_with_keys(after)
    out["mae"] = {"line": float(np.mean([abs(Lb[k]["y"] - Lb[k]["line"]) for k in common])),
                  "sim_before": float(np.mean([abs(La[k]["sim_mean"] - La[k]["y"]) for k in common])),
                  "sim_after": float(np.mean([abs(Lb[k]["sim_mean"] - Lb[k]["y"]) for k in common])),
                  "median_before": float(np.mean([abs(La[k]["sim_med"] - La[k]["y"]) for k in common])),
                  "median_after": float(np.mean([abs(Lb[k]["sim_med"] - Lb[k]["y"]) for k in common]))}
    # the model's information beyond DraftKings: y ~ logit(q) + b (logit(model) - logit(q))
    X = np.array([[1.0, F.lg(r["market"]), F.lg(r["model"]) - F.lg(r["market"])] for r in rb]); yy = np.array([r["y"] for r in rb])
    b, cov = F.logistic(X, yy, l2=0.0)
    out["info_weight"] = {"b": float(b[2]), "ci95": [float(b[2] - 1.96 * np.sqrt(cov[2, 2])), float(b[2] + 1.96 * np.sqrt(cov[2, 2]))],
                          "market_slope": float(b[1]), "intercept": float(b[0])}
    # pick'em edge of the entry legs at the 2-pick power payout (structural: assumes PrizePicks posts DraftKings' line)
    e = out["after"]["entry"]
    if e["n"]:
        h = e["real"]; se = np.sqrt(h * (1 - h) / e["n"])
        out["entry_edge"] = {"hit": h, "ci95": [h - 1.96 * se, h + 1.96 * se], "break_even": BE, "roi_2pick_power": 3 * h * h - 1}
    json.dump(out, open(os.path.join(HERE, "data", "nba_bt", "final_eval.json"), "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k not in ("days",)}, indent=1, default=float)[:6000])
