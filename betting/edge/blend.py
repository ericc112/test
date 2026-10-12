"""Combine model, market and history into one calibrated hit probability, using learned adjustments."""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass

from .odds import logit, sigmoid

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADJ_PATH = os.path.join(HERE, "data", "adjustments.json")

DEFAULT_ADJ = {
    "blend": {"intercept": 0.0, "w_model": 0.45, "w_market": 0.40, "w_hist": 0.15},
    "model_bias_logit": {},     # systematic model-vs-market gaps found in scans (applied to p_model only)
    "outcome_bias_logit": {},   # learned from graded results (applied to the final probability)
    "avoid_segments": [],
    "gates": {"high": 0.62, "medium": 0.56, "max_spread_high": 0.12, "min_hist_n_high": 10},
}


def load_adjustments(path: str = ADJ_PATH) -> dict:
    if not os.path.exists(path):
        return json.loads(json.dumps(DEFAULT_ADJ))
    with open(path) as f:
        adj = json.load(f)
    for k, v in DEFAULT_ADJ.items():
        adj.setdefault(k, v)
    return adj


def segment_key(sport: str, market: str, side: str) -> str:
    return f"{sport}:{market}:{side}".lower()


def _lookup(table: dict, segment: str) -> float:
    """Most specific match wins: 'mlb:pitcher_outs:under' > 'mlb:pitcher_outs' > 'mlb'."""
    parts = segment.split(":")
    for i in range(len(parts), 0, -1):
        key = ":".join(parts[:i])
        if key in table:
            return float(table[key])
    return 0.0


@dataclass
class Estimate:
    p: float
    confidence: str
    agreement: bool
    spread: float
    components: dict
    notes: list


def final_probability(p_model: float | None, p_market: float | None = None, p_hist: float | None = None,
                      segment: str = "", hist_n: int = 0, adj: dict | None = None) -> Estimate:
    """Blend on the logit scale. Missing components hand their weight to the ones present."""
    adj = adj or load_adjustments()
    b = adj["blend"]
    notes = []
    comps = {}
    if p_model is not None:
        mb = _lookup(adj["model_bias_logit"], segment)
        comps["model"] = sigmoid(logit(p_model) + mb)
        if mb:
            notes.append(f"model de-biased by {mb:+.2f} logit for {segment}")
    if p_market is not None:
        comps["market"] = p_market
    if p_hist is not None:
        # regress small-sample history toward the market (or 0.5) before using it
        anchor = p_market if p_market is not None else 0.5
        w = hist_n / (hist_n + 10) if hist_n else 0.5
        comps["hist"] = w * p_hist + (1 - w) * anchor
    if not comps:
        raise ValueError("need at least one probability")
    weights = {"model": b["w_model"], "market": b["w_market"], "hist": b["w_hist"]}
    total_w = sum(weights.values())
    present_w = sum(weights[k] for k in comps)
    z = b["intercept"] + sum(weights[k] * total_w / present_w * logit(v) for k, v in comps.items())
    ob = _lookup(adj["outcome_bias_logit"], segment)
    if ob:
        notes.append(f"outcome bias {ob:+.2f} logit learned for {segment}")
    p = sigmoid(z + ob)

    vals = list(comps.values())
    leaning = [v for v in vals if abs(v - 0.5) >= 0.01]  # a component at ~50% is neutral, not a disagreement
    agreement = bool(leaning) and (all(v > 0.5 for v in leaning) or all(v < 0.5 for v in leaning))
    spread = max(vals) - min(vals)
    g = adj["gates"]
    if segment and any(segment.startswith(s) for s in adj["avoid_segments"]):
        conf = "Avoid"
        notes.append("segment is on the avoid list (losing history)")
    elif p >= g["high"] and agreement and spread <= g["max_spread_high"] and len(comps) >= 2 and hist_n >= g["min_hist_n_high"]:
        conf = "High"
    elif p >= g["medium"] and agreement and len(comps) >= 2:
        conf = "Medium"
    else:
        conf = "Low"
    if not agreement:
        notes.append("components disagree on the side: downgrade or pass")
    if len(comps) == 1:
        notes.append("single-source estimate: capped at Low until a market price or history confirms it")
    return Estimate(p=round(p, 4), confidence=conf, agreement=agreement, spread=round(spread, 4),
                    components={k: round(v, 4) for k, v in comps.items()}, notes=notes)
