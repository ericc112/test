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
    "gates": {"high": 0.65, "medium": 0.58, "max_spread_high": 0.12, "min_hist_n_high": 10,
              "no_market_min_hist_n": 20, "no_market_max_spread": 0.10, "max_model_bias_without_market": 0.25},
    "hist_weight_scale": {},   # e.g. {"mlb:pitcher_outs": 0.5}: trust history less for these segments (postseason leash)
    "cap_medium_segments": {},  # set by `edge learn` from post-mortems: repeated same-cause losses -> no High legs
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

    @property
    def rating(self) -> int:
        return rating(self.p, self.confidence, self.components.get("market"))


RATING_FLOOR = 0.80      # the 8-10 tier must hit 80%: learn raises this while graded 8+ picks fall short
TIER_MARKET_MIN = 0.75   # ... and the sportsbook itself must make it a 75%+ shot (model-only 80%+ picks hit 56%, n=9)


def rating_floor(adj: dict | None = None) -> float:
    try:
        return float((adj or load_adjustments()).get("rating_floor", RATING_FLOOR))
    except Exception:
        return RATING_FLOOR


def rating(p: float | None, confidence: str | None, p_market: float | None = None, floor: float | None = None) -> int:
    """1-10 confidence score. The label decides the band and the probability places it inside the band, so no number
    can buy its way past a gate. 8-10 is the 80% tier: High (every gate passed) AND blended chance >= the floor (0.80,
    raised by `edge learn` if graded 8+ picks hit less) AND a sportsbook price that makes it a 75%+ shot on its own.
    A High without all three is a 7. 5-7 Medium, 1-4 Low, 1 for Avoid."""
    if p is None or not confidence or confidence == "Avoid":
        return 1
    if confidence == "High":
        fl = rating_floor() if floor is None else floor
        if p_market is not None and p_market >= TIER_MARKET_MIN and p >= fl:
            return 10 if p >= round(fl + 0.10, 4) else 9 if p >= round(fl + 0.05, 4) else 8
        return 7
    if confidence == "Medium":
        return 7 if p >= 0.66 else 6 if p >= 0.62 else 5
    return 4 if p >= 0.58 else 3 if p >= 0.54 else 2 if p >= 0.50 else 1


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
        scale = _lookup(adj.get("hist_weight_scale", {}), segment) or 1.0
        if scale != 1.0:
            notes.append(f"history weight scaled x{scale} for {segment}")
        w *= scale
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
    # calibration learned from graded results (`edge learn`): a model-only 80% has hit ~73%; priced picks are honest
    cal = (adj.get("calibration") or {}).get("market" if "market" in comps else "no_market")
    if cal:
        raw = p
        p = sigmoid(cal["a"] + cal["b"] * logit(min(0.995, max(0.005, raw))))
        if abs(p - raw) >= 0.005:
            notes.append(f"calibrated {raw:.3f} -> {p:.3f} ({'priced' if 'market' in comps else 'no market'} picks' record)")

    vals = list(comps.values())
    leaning = [v for v in vals if abs(v - 0.5) >= 0.01]  # a component at ~50% is neutral, not a disagreement
    agreement = bool(leaning) and (all(v > 0.5 for v in leaning) or all(v < 0.5 for v in leaning))
    spread = max(vals) - min(vals)
    g = adj["gates"]
    if segment and any(segment.startswith(s) for s in adj["avoid_segments"]):
        conf = "Avoid"
        notes.append("segment is on the avoid list (losing history)")
    elif (p >= g["high"] and agreement and spread <= g["max_spread_high"] and len(comps) >= 2 and hist_n >= g["min_hist_n_high"]
          and ("market" in comps or (hist_n >= g.get("no_market_min_hist_n", 20) and spread <= g.get("no_market_max_spread", 0.10)))):
        conf = "High"
    elif p >= g["medium"] and agreement and len(comps) >= 2:
        conf = "Medium"
    else:
        conf = "Low"
    cap = next((s for s in adj.get("cap_medium_segments", {}) if segment and segment.startswith(s)), None)
    if conf == "High" and cap:
        conf = "Medium"
        notes.append(f"capped at Medium: {adj['cap_medium_segments'][cap]}")
    # LESSONS L19: a model that needed a large correction in this market can't carry a High label unchecked by a price
    if conf == "High" and "market" not in comps and "model" in comps and \
            abs(_lookup(adj["model_bias_logit"], segment)) >= g.get("max_model_bias_without_market", 0.25):
        conf = "Medium"
        notes.append("capped at Medium: model is known to run off the market here and there is no market price to check it (L19)")
    if not agreement:
        notes.append("components disagree on the side: downgrade or pass")
    if len(comps) == 1:
        notes.append("single-source estimate: capped at Low until a market price or history confirms it")
    return Estimate(p=round(p, 4), confidence=conf, agreement=agreement, spread=round(spread, 4),
                    components={k: round(v, 4) for k, v in comps.items()}, notes=notes)
