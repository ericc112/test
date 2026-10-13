"""Card discipline: one leg per game script, only top-tier legs, best hit-rate entry (LESSONS L16)."""
from __future__ import annotations

from collections import defaultdict

from .blend import final_probability, load_adjustments
from .pickem import entry_summary


def _f(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


def script_key(r: dict) -> str:
    """Legs that ride on the same game script. Explicit `group` wins; otherwise one script per game."""
    return r.get("group") or f"{r.get('sport', '')}:{r.get('event_id', '')}"


def rescore(rows: list[dict], adj: dict | None = None) -> list[dict]:
    """Recompute p_final/confidence with today's adjustments (gates and corrections may have changed)."""
    adj = adj or load_adjustments()
    out = []
    for r in rows:
        if r.get("status") not in ("pending", ""):
            continue
        e = final_probability(_f(r.get("p_model")), _f(r.get("p_market")), _f(r.get("p_hist")),
                              r.get("segment", ""), int(_f(r.get("hist_n")) or 0), adj)
        out.append({**r, "p_now": e.p, "conf_now": e.confidence, "notes_now": "; ".join(e.notes)})
    return out


def exposure(rows: list[dict]) -> dict[str, list[dict]]:
    """Group the legs you are actually playing (bet/lean/user_entry) by script."""
    g = defaultdict(list)
    for r in rows:
        if r.get("action") in ("bet", "lean", "user_entry"):
            g[script_key(r)].append(r)
    return g


def best_legs(rows: list[dict], min_p: float = 0.65, tiers=("High",), date: str | None = None) -> list[dict]:
    """Top leg per script among legs that pass the gate, ranked by probability."""
    pool = [r for r in rescore([r for r in rows if not date or r.get("date") == date])
            if r["conf_now"] in tiers and r["p_now"] >= min_p]
    best = {}
    for r in pool:
        k = script_key(r)
        if k not in best or r["p_now"] > best[k]["p_now"]:
            best[k] = r
    return sorted(best.values(), key=lambda r: -r["p_now"])


def best_entry(legs: list[dict], size: int = 2, payout: dict | None = None) -> dict | None:
    """Legs come from different scripts, so treat them as independent."""
    if len(legs) < size:
        return None
    pick = legs[:size]
    s = entry_summary([r["p_now"] for r in pick], payout or {size: 1.0})
    return {"legs": pick, "p_all": s["p_all"]}
