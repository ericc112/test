"""Fix 4: closing line value for every published NBA leg (both lists on the page).
  python -m edge.nba_clv [--days 30]
For each published leg: DraftKings' no-vig probability for its side when it was priced, and at the close (the last
pull before tip in data/nba_dk_snap, or the feed's own value when it wasn't touched after tip). CLV = close - priced,
in probability points (positive: the market moved our way). When DraftKings' line moved, the probability is carried
to the published line along a normal approximation of the leg's simulated spread (25th-75th / 1.35). Legs with no
DraftKings line at either time are counted and reported, never dropped."""
from __future__ import annotations

import datetime as dt
import glob
import json
import math
import os
import sys

from .blend import HERE

PICKS = os.path.join(HERE, "data", "picks")
SNAP = os.path.join(HERE, "data", "nba_dk_snap")


def _imp(a):
    try:
        v = float(str(a).replace("+", ""))
    except (TypeError, ValueError):
        return None
    return 100 / (v + 100) if v > 0 else -v / (-v + 100)


def _q(rec):
    if not rec or not rec.get("over") or not rec.get("under"):
        return None
    o, u = _imp(rec["over"]), _imp(rec["under"])
    return o / (o + u)


def _carry(q_over: float, dk_line: float, line: float, sd: float) -> float:
    """P(over `line`) given DraftKings' P(over dk_line), with a normal spread sd."""
    from statistics import NormalDist
    nd = NormalDist()
    mu = dk_line + sd * nd.inv_cdf(min(max(q_over, 1e-4), 1 - 1e-4))
    return 1 - nd.cdf((line - mu) / sd)


def clv(days: int = 30) -> dict:
    legs = []
    for path in sorted(glob.glob(os.path.join(PICKS, "*-nba.json")))[-days:]:
        day = os.path.basename(path)[:10]
        P = json.load(open(path))
        snaps = []
        sp = os.path.join(SNAP, f"{day}.jsonl")
        if os.path.exists(sp):
            snaps = [json.loads(x) for x in open(sp)]
        for lst in ("model", "history"):
            for r in P.get(lst, []):
                gid = r.get("game_id") or r.get("event_id")
                legs.append({"day": day, "list": lst, **r, "_snaps": [s for s in snaps if not gid or s["gid"] == str(gid)]})
    out, rows = {"legs": len(legs)}, []
    for l in legs:
        sd = max(((l.get("q75") or 0) - (l.get("q25") or 0)) / 1.35, 1.0)
        pub = l.get("dk")
        side = l["side"]
        q_pub = _q(pub)
        close = None
        for s in sorted(l["_snaps"], key=lambda s: s["at"]):
            if l.get("start") and s["at"] >= str(l["start"])[:16]:
                break
            rec = (s["lines"].get(str(l.get("player_id"))) or {}).get(l.get("stat_key") or "")
            if rec and _q(rec) is not None:
                close = rec
        q_close = _q(close)
        if q_pub is None or q_close is None:
            rows.append({**{k: l.get(k) for k in ("day", "list", "player", "stat", "line", "side")}, "clv": None,
                         "why": "no DraftKings price when priced" if q_pub is None else "no DraftKings price before tip"})
            continue
        a = _carry(q_pub, pub["line"], l["line"], sd); b = _carry(q_close, close["line"], l["line"], sd)
        if side == "under":
            a, b = 1 - a, 1 - b
        rows.append({**{k: l.get(k) for k in ("day", "list", "player", "stat", "line", "side")}, "clv": b - a, "q_pub": a, "q_close": b})
    got = [r for r in rows if r["clv"] is not None]
    out["with_clv"] = len(got)
    out["missing"] = {w: sum(r.get("why") == w for r in rows) for w in {r.get("why") for r in rows if r.get("why")}}
    if got:
        out["mean_clv"] = sum(r["clv"] for r in got) / len(got)
        out["beat_close"] = sum(r["clv"] > 0 for r in got) / len(got)
        by = {}
        for r in got:
            by.setdefault((r["list"], r["stat"]), []).append(r["clv"])
        out["by_list_stat"] = {f"{k[0]}:{k[1]}": {"n": len(v), "mean": sum(v) / len(v)} for k, v in by.items()}
        out["flags"] = [k for k, v in out["by_list_stat"].items() if v["n"] >= 100 and v["mean"] < 0]
    out["rows"] = rows
    return out


if __name__ == "__main__":
    r = clv()
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1))
