"""Learning loop: score graded bets, recalibrate the blend, learn per-segment bias, record lessons."""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import os
from collections import defaultdict

import numpy as np

from .blend import ADJ_PATH, DEFAULT_ADJ, HERE, final_probability, load_adjustments, _lookup
from .odds import american_to_decimal, implied, logit, sigmoid

BETS_PATH = os.path.join(HERE, "data", "bets.csv")
LESSONS_PATH = os.path.join(HERE, "LESSONS.md")

FIELDS = ["id", "date", "sport", "event", "event_id", "player", "player_id", "market", "line", "side", "book",
          "price", "payout_mult", "entry_id", "stake", "p_model", "p_market", "p_hist", "hist_n", "p_final",
          "confidence", "action", "segment", "group", "status", "result_value", "closing_price", "miss_reason", "notes"]

PRIOR_STRENGTH = 25.0   # how hard the blend weights are pulled back to their prior (in "bets" of evidence)
SEGMENT_K = 30.0        # shrinkage for per-segment bias: weight = n / (n + K)
BIAS_CLIP = 0.4


def _f(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


def read_bets(path: str = BETS_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def write_bets(rows: list[dict], path: str = BETS_PATH) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def graded(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("status") in ("won", "lost")]


# ---------------------------------------------------------------- metrics
def brier(ps, ys):
    return float(np.mean([(p - y) ** 2 for p, y in zip(ps, ys)])) if ps else float("nan")


def logloss(ps, ys):
    return float(np.mean([-(y * math.log(max(p, 1e-6)) + (1 - y) * math.log(max(1 - p, 1e-6))) for p, y in zip(ps, ys)])) if ps else float("nan")


def calibration_table(ps, ys, edges=(0, 0.5, 0.55, 0.6, 0.65, 0.7, 1.01)):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        idx = [i for i, p in enumerate(ps) if lo <= p < hi]
        if idx:
            out.append({"bucket": f"{lo:.2f}-{min(hi, 1):.2f}", "n": len(idx),
                        "predicted": float(np.mean([ps[i] for i in idx])), "actual": float(np.mean([ys[i] for i in idx]))})
    return out


def entry_results(rows: list[dict]) -> list[dict]:
    """Power-style entries: all legs must win. Pending/void legs leave the entry ungraded."""
    by = defaultdict(list)
    for r in rows:
        if r.get("entry_id"):
            by[r["entry_id"]].append(r)
    out = []
    for eid, legs in by.items():
        if any(l["status"] in ("pending", "void", "") for l in legs):
            continue
        stake, mult = _f(legs[0]["stake"]) or 0, _f(legs[0]["payout_mult"]) or 0
        won = all(l["status"] in ("won", "push") for l in legs)
        out.append({"entry_id": eid, "legs": len(legs), "won": won, "profit": stake * (mult - 1) if won else -stake, "stake": stake})
    return out


# ---------------------------------------------------------------- fitting
def _components(r: dict, adj: dict):
    seg = r.get("segment", "")
    pm, pk, ph = _f(r.get("p_model")), _f(r.get("p_market")), _f(r.get("p_hist"))
    hn = int(_f(r.get("hist_n")) or 0)
    if pm is not None:
        pm = sigmoid(logit(pm) + _lookup(adj["model_bias_logit"], seg))
    if ph is not None:
        anchor = pk if pk is not None else 0.5
        w = hn / (hn + 10) if hn else 0.5
        ph = w * ph + (1 - w) * anchor
    return pm, pk, ph


def fit_blend(rows: list[dict], adj: dict) -> dict:
    """Penalised logistic regression of outcome on logit(model), logit(market), logit(hist), pulled toward the prior."""
    X, y = [], []
    for r in graded(rows):
        pm, pk, ph = _components(r, adj)
        if pm is None or pk is None:
            continue
        ph = pk if ph is None else ph
        X.append([1.0, logit(pm), logit(pk), logit(ph)])
        y.append(1.0 if r["status"] == "won" else 0.0)
    b = adj["blend"]
    prior = np.array([b["intercept"], b["w_model"], b["w_market"], b["w_hist"]])
    if len(y) < 10:
        return {**b, "n_fit": len(y), "note": "fewer than 10 graded bets with model+market: kept prior"}
    X, y = np.array(X), np.array(y)
    th = prior.copy()
    lam = PRIOR_STRENGTH
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ th))
        g = X.T @ (p - y) + lam * (th - prior)
        H = X.T @ (X * (p * (1 - p))[:, None]) + lam * np.eye(4)
        step = np.linalg.solve(H, g)
        th -= step
        if np.abs(step).max() < 1e-8:
            break
    return {"intercept": round(float(th[0]), 4), "w_model": round(float(th[1]), 4), "w_market": round(float(th[2]), 4),
            "w_hist": round(float(th[3]), 4), "n_fit": int(len(y))}


def learn_segment_bias(rows: list[dict], adj: dict) -> dict:
    """Shrunk one-step logistic correction per segment, measured after the blend (excluding old outcome bias)."""
    base = {**adj, "outcome_bias_logit": {}}
    acc = defaultdict(lambda: [0.0, 0.0, 0])
    for r in graded(rows):
        seg = r.get("segment", "")
        if not seg:
            continue
        pm, pk, ph = _f(r.get("p_model")), _f(r.get("p_market")), _f(r.get("p_hist"))
        if pm is None and pk is None and ph is None:
            continue
        p = final_probability(pm, pk, ph, seg, int(_f(r.get("hist_n")) or 0), base).p
        y = 1.0 if r["status"] == "won" else 0.0
        a = acc[seg]
        a[0] += y - p
        a[1] += p * (1 - p)
        a[2] += 1
    out = {}
    for seg, (res, info, n) in acc.items():
        if n < 5 or info <= 0:
            continue
        delta = (res / info) * n / (n + SEGMENT_K)
        out[seg] = round(float(max(-BIAS_CLIP, min(BIAS_CLIP, delta))), 3)
    return out


def find_avoid_segments(rows: list[dict]) -> list[str]:
    acc = defaultdict(list)
    for r in graded(rows):
        p = _f(r.get("p_final"))
        if p is not None and r.get("segment"):
            acc[r["segment"]].append((p, 1.0 if r["status"] == "won" else 0.0))
    bad = []
    for seg, v in acc.items():
        n = len(v)
        if n < 20:
            continue
        mp = np.mean([p for p, _ in v])
        hr = np.mean([y for _, y in v])
        z = (hr - mp) / math.sqrt(max(mp * (1 - mp) / n, 1e-9))
        if hr - mp < -0.08 and z < -2:
            bad.append(seg)
    return sorted(bad)


# ---------------------------------------------------------------- report + update
def report(rows: list[dict]) -> str:
    g = graded(rows)
    lines = [f"Bets logged: {len(rows)} | graded: {len(g)} | pending: {sum(r.get('status') == 'pending' for r in rows)}"]
    if not g:
        return "\n".join(lines + ["Nothing graded yet: run `python -m edge grade` after games finish."])
    ps = [_f(r["p_final"]) for r in g]
    ys = [1.0 if r["status"] == "won" else 0.0 for r in g]
    lines.append(f"Hit rate {np.mean(ys):.1%} vs predicted {np.mean(ps):.1%} | Brier {brier(ps, ys):.3f} | log loss {logloss(ps, ys):.3f}")
    withm = [(_f(r["p_final"]), _f(r["p_market"]), y) for r, y in zip(g, ys) if _f(r.get("p_market")) is not None]
    if withm:
        bo = brier([a for a, _, _ in withm], [y for _, _, y in withm])
        bm = brier([m for _, m, _ in withm], [y for _, _, y in withm])
        lines.append(f"Skill vs market (Brier, n={len(withm)}): ours {bo:.3f} vs market {bm:.3f} -> {'beating' if bo < bm else 'NOT beating'} the market")
    clv = [implied(_f(r["closing_price"])) - implied(_f(r["price"])) for r in g if _f(r.get("closing_price")) is not None and _f(r.get("price")) is not None]
    if clv:
        lines.append(f"CLV (implied-prob points, n={len(clv)}): avg {np.mean(clv) * 100:+.2f} | positive {np.mean([c > 0 for c in clv]):.0%}")
    singles = [r for r in g if not r.get("entry_id") and _f(r.get("price")) is not None and _f(r.get("stake"))]
    if singles:
        prof = sum((_f(r["stake"]) * (american_to_decimal(_f(r["price"])) - 1)) if r["status"] == "won" else -_f(r["stake"]) for r in singles)
        risk = sum(_f(r["stake"]) for r in singles)
        lines.append(f"Single-bet ROI: {prof / risk:+.1%} on {risk:.2f} staked")
    ent = entry_results(rows)
    if ent:
        lines.append(f"Entries: {sum(e['won'] for e in ent)}/{len(ent)} cashed | profit {sum(e['profit'] for e in ent):+.2f} on {sum(e['stake'] for e in ent):.2f}")
    for key in ("confidence", "action"):
        tiers = defaultdict(list)
        for r, y in zip(g, ys):
            tiers[r.get(key) or "?"].append((_f(r["p_final"]), y))
        lines.append(f"Hit rate by {key}: " + " | ".join(
            f"{t} {np.mean([y for _, y in v]):.0%} of {len(v)} (pred {np.mean([p for p, _ in v]):.0%})" for t, v in sorted(tiers.items())))
    lines.append("Calibration (predicted -> actual):")
    for c in calibration_table(ps, ys):
        flag = "  <-- off by >8 pts" if c["n"] >= 15 and abs(c["actual"] - c["predicted"]) > 0.08 else ""
        lines.append(f"  {c['bucket']}: n={c['n']:3d}  {c['predicted']:.1%} -> {c['actual']:.1%}{flag}")
    seg = defaultdict(list)
    for r, y in zip(g, ys):
        seg[r.get("segment", "?")].append((_f(r["p_final"]), y))
    lines.append("By segment (n, predicted, actual):")
    for s, v in sorted(seg.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"  {s:38s} n={len(v):3d}  {np.mean([p for p, _ in v]):.1%} -> {np.mean([y for _, y in v]):.1%}")
    misses = [r for r in g if r["status"] == "lost" and (_f(r["p_final"]) or 0) >= 0.62]
    if misses:
        lines.append("High-confidence misses (tag a root cause with `python -m edge tag <id> \"reason\"`):")
        for r in misses:
            lines.append(f"  #{r['id']} {r['player']} {r['market']} {r['side']} {r['line']} p={r['p_final']} result={r['result_value']} reason={r.get('miss_reason') or 'UNTAGGED'}")
    reasons = defaultdict(int)
    for r in g:
        if r.get("miss_reason"):
            reasons[r["miss_reason"]] += 1
    if reasons:
        lines.append("Miss reasons so far: " + ", ".join(f"{k} x{v}" for k, v in sorted(reasons.items(), key=lambda kv: -kv[1])))
    return "\n".join(lines)


def update(rows: list[dict] | None = None, adj_path: str = ADJ_PATH, lessons_path: str = LESSONS_PATH, today: str | None = None) -> dict:
    rows = read_bets() if rows is None else rows
    adj = load_adjustments(adj_path)
    old = json.loads(json.dumps(adj))
    # Refit from the fixed prior every run (not from last run's weights) so the same results are never counted twice.
    adj.setdefault("blend_prior", dict(DEFAULT_ADJ["blend"]))
    fit = fit_blend(rows, {**adj, "blend": adj["blend_prior"]})
    adj["blend"] = {k: fit[k] for k in ("intercept", "w_model", "w_market", "w_hist")}
    adj["blend_fit"] = {k: v for k, v in fit.items() if k in ("n_fit", "note")}
    adj["outcome_bias_logit"] = learn_segment_bias(rows, adj)
    new_avoid = find_avoid_segments(rows)
    adj["avoid_segments"] = sorted(set(old.get("avoid_segments", [])) | set(new_avoid))
    adj["updated"] = today or dt.date.today().isoformat()
    with open(adj_path, "w") as f:
        json.dump(adj, f, indent=2)

    notes = []
    for k in ("w_model", "w_market", "w_hist"):
        if abs(adj["blend"][k] - old["blend"][k]) > 0.05:
            notes.append(f"Blend weight {k} moved {old['blend'][k]:.2f} -> {adj['blend'][k]:.2f}: trust that source {'more' if adj['blend'][k] > old['blend'][k] else 'less'}.")
    for seg, v in adj["outcome_bias_logit"].items():
        if abs(v - old.get("outcome_bias_logit", {}).get(seg, 0)) >= 0.15:
            notes.append(f"Segment {seg}: results run {'above' if v > 0 else 'below'} our probabilities; now auto-adjusting {v:+.2f} logit.")
    for seg in new_avoid:
        if seg not in old.get("avoid_segments", []):
            notes.append(f"Segment {seg} added to AVOID list: hit rate >8 pts under prediction over 20+ bets.")
    if notes and lessons_path:
        with open(lessons_path, "a") as f:
            f.write(f"\n### Auto-learned {adj['updated']}\n" + "".join(f"- {n}\n" for n in notes))
    return {"adjustments": adj, "lessons_added": notes}
