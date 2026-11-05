"""Line shopping: PrizePicks vs Dabble, same player and stat (python -m edge shop [--page shop.js]).

Dabble's public API (api.dabble.com) lists each fixture's pick'em props with a decimal price on each side, and the
two sides price to about 100% (no visible vig). So for every PrizePicks line with a Dabble line on the same player
and stat this finds:

  line gaps    PrizePicks and Dabble post different numbers: the over is better on the app with the lower line, the
               under on the app with the higher one.
  price gaps   same number, but Dabble prices one side well above 50%: on PrizePicks that side pays the flat power
               price.

and turns Dabble's price into a probability at the PrizePicks line (a normal approximation around Dabble's implied
median, spread by stat). That probability is Dabble's, not ours: it is market data for shopping, not a verified pick.
A PrizePicks leg is worth a look when it clears the 2-pick power break-even (57.7%). Every number here still has to
go through the sport's pricer and `edge verify` before it is named as a pick.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import math
import os
import subprocess

DABBLE = "https://api.dabble.com"
BREAK_EVEN = 0.577
STAT_MAP = {
    "NBA": {"Points": ("points",), "Rebounds": ("rebounds",), "Assists": ("assists",), "3-PT Made": ("three-made",),
            "Pts+Rebs+Asts": ("assists", "points", "rebounds"), "Pts+Rebs": ("points", "rebounds"), "Pts+Asts": ("assists", "points"),
            "Rebs+Asts": ("assists", "rebounds"), "Blks+Stls": ("blocks", "steals"), "Blocked Shots": ("blocks",), "Steals": ("steals",),
            "Free Throws Attempted": ("ft-attempted",), "Free Throws Made": ("ft-made",), "FG Attempted": ("fg-attempted",),
            "FG Made": ("fg-made",), "3-PT Attempted": ("three-attempted",), "Two Pointers Made": ("two-made",),
            "Two Pointers Attempted": ("two-attempted",)},
    "NFL": {"Receiving Yards": ("receiving-yards",), "Rush Yards": ("rushing-yards",), "Rush+Rec Yds": ("receiving-yards", "rushing-yards"),
            "Receptions": ("receptions",), "Rush Attempts": ("rushing-attempts",), "Pass Yards": ("passing-yards",),
            "Pass TDs": ("passing-touchdowns",), "Pass Attempts": ("passing-attempts",), "Pass Completions": ("passing-completions",),
            "INT": ("interceptions",), "Longest Reception": ("longest-reception",), "Longest Rush": ("longest-rush",),
            "Longest Completion": ("longest-passing-completion",), "Pass+Rush Yds": ("passing-yards", "rushing-yards"),
            "Kicking Points": ("kicking-points",), "Tackles+Ast": ("assists", "tackles"), "Rush TDs": ("rushing-touchdowns",)},
    "NHL": {"Shots On Goal": ("shots",), "Goals": ("goals",), "Assists": ("assists",), "Points": ("points",), "Blocked Shots": ("blocked-shots",)},
}
YARDS = {"receiving-yards", "rushing-yards", "passing-yards", "longest-reception", "longest-rush", "longest-passing-completion"}


def _get(path: str) -> dict:
    r = subprocess.run(["curl", "-sS", "-m", "25", "-A", "edge-shop/1.0", f"{DABBLE}{path}"], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def _norm(name: str) -> str:
    from .nba_pp import _norm as n
    return n(name)


def competitions() -> dict:
    """Dabble competition id for each league (the regular-season competition named exactly NBA, NFL or NHL)."""
    out = {}
    for c in _get("/competitions").get("data", []):
        nm = (c.get("name") or "").upper()
        key = {"NBA": "NBA", "NFL": "NFL", "US NHL": "NHL", "NHL": "NHL"}.get(nm)
        if key and (key not in out or c.get("updated", "") > out[key][1]):
            out[key] = (c["id"], c.get("updated", ""))
    return {k: v[0] for k, v in out.items()}


def dabble_board(league: str, comp_id: str) -> list[dict]:
    """Every open pick'em prop for a league: player, team, stats, line, decimal price on each side."""
    rows = []
    for fx in _get(f"/competitions/{comp_id}/sport-fixtures").get("data", []):
        if (fx.get("status") or "").lower() not in ("open", ""):
            continue
        d = _get(f"/sportfixtures/details/{fx['id']}?filter=dfs-enabled").get("data") or {}
        price = {p["selectionId"]: p.get("price") for p in d.get("prices", [])}
        by = collections.defaultdict(dict)
        for p in d.get("playerProps", []):
            if not p.get("isDisplayed", True):
                continue
            k = (p["playerName"], tuple(sorted(p.get("stats") or [])), float(p["value"]))
            by[k]["team"] = p.get("teamAbbreviation")
            by[k][p["lineType"]] = price.get(p["selectionId"])
        for (name, stats, line), v in by.items():
            rows.append({"player": name, "team": (v.get("team") or "").upper(), "stats": stats, "line": line, "over": v.get("over"),
                         "under": v.get("under"), "game": fx.get("name"), "start": fx.get("advertisedStart")})
    return rows


def implied_over(over: float | None, under: float | None) -> float | None:
    """Dabble's probability of the over, normalized over both sides (its prices sum to ~100% anyway)."""
    if not over or not under:
        return None
    a, b = 1 / over, 1 / under
    return a / (a + b)


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _phinv(p: float) -> float:
    lo, hi = -6.0, 6.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _phi(mid) < p else (lo, mid)
    return (lo + hi) / 2


def spread(stats: tuple, line: float) -> float:
    """Rough game-to-game spread of a stat around a line: counts ~1.15 x sqrt(line), yardage ~0.5 x line."""
    if any(s in YARDS for s in stats):
        return max(8.0, 0.5 * line)
    return max(0.8, 1.15 * math.sqrt(max(line, 0.3)))


def prob_at(q_over: float, d_line: float, pp_line: float, stats: tuple) -> float:
    """Dabble's P(over) moved from its own line to the PrizePicks line: Dabble's implied median (its line shifted by
    the price) with a normal spread for the stat. Only meant for lines within a few units of each other."""
    q = min(max(q_over, 0.02), 0.98)
    if not any(x in YARDS for x in stats) and d_line < 4:      # small counts (TDs, goals, assists, low lines): Poisson
        return poisson_at(q, d_line, pp_line)
    sd = spread(stats, d_line)
    med = d_line + _phinv(q) * sd
    if float(pp_line).is_integer() and not any(x in YARDS for x in stats):
        over, under = 1 - _phi((pp_line + 0.5 - med) / sd), _phi((pp_line - 0.5 - med) / sd)   # a whole line can push
        return over / max(over + under, 1e-9)
    return 1 - _phi((pp_line - med) / sd)


def _pois_sf(lam: float, k: int) -> float:
    """P(X >= k) for a Poisson mean lam."""
    return 1 - sum(math.exp(-lam) * lam ** j / math.factorial(j) for j in range(max(k, 0)))


def poisson_at(q_over: float, d_line: float, pp_line: float) -> float:
    """Fit a Poisson so P(X > Dabble's line) = Dabble's over price, then P(over) at the PrizePicks line with a whole
    line's push excluded."""
    k = int(math.floor(d_line)) + 1
    lo, hi = 1e-3, 30.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _pois_sf(mid, k) < q_over else (lo, mid)
    lam = (lo + hi) / 2
    if float(pp_line).is_integer():
        over, under = _pois_sf(lam, int(pp_line) + 1), 1 - _pois_sf(lam, int(pp_line))
        return over / max(over + under, 1e-9)
    return _pois_sf(lam, int(math.floor(pp_line)) + 1)


def compare(league: str, comp_id: str | None = None) -> dict:
    from . import pp
    comp_id = comp_id or competitions().get(league)
    if not comp_id:
        return {"league": league, "error": "no Dabble competition"}
    P = [p for p in pp.board(league, ("standard",)) if p["stat"] in STAT_MAP[league]]
    D = dabble_board(league, comp_id)
    idx = collections.defaultdict(list)
    for d in D:
        idx[(_norm(d["player"]), d["stats"])].append(d)
    rows, matched = [], 0
    for p in P:
        stats = tuple(sorted(STAT_MAP[league][p["stat"]]))
        cands = idx.get((_norm(p["player"]), stats))
        if not cands:
            continue
        matched += 1
        d = min(cands, key=lambda x: abs(x["line"] - p["line"]))      # Dabble's line closest to PrizePicks'
        q = implied_over(d["over"], d["under"])
        gap = round(p["line"] - d["line"], 2)
        if q is None:
            continue
        if gap == 0:
            side = "over" if q >= 0.5 else "under"
            pp_p = q if side == "over" else 1 - q
            kind = "price"
        else:
            side = "over" if gap < 0 else "under"                  # PrizePicks' line is the better number for this side
            po = prob_at(q, d["line"], p["line"], stats)
            pp_p = po if side == "over" else 1 - po
            kind = "line"
        if p.get("over_only") and side == "under":
            continue
        rows.append({"league": league, "player": p["player"], "team": p.get("team"), "stat": p["stat"], "pp_line": p["line"],
                     "dabble_line": d["line"], "gap": gap, "kind": kind, "side": side, "dabble_p_over": round(q, 4),
                     "dabble_over": d["over"], "dabble_under": d["under"], "pp_p": round(pp_p, 4), "clears": pp_p >= BREAK_EVEN,
                     "better": {"over": "PrizePicks" if gap < 0 else "Dabble" if gap > 0 else "same",
                                "under": "PrizePicks" if gap > 0 else "Dabble" if gap < 0 else "same"},
                     "game": d["game"], "start": p.get("start") or d["start"]})
    rows.sort(key=lambda r: (-r["pp_p"]))
    return {"league": league, "pp_lines": len(P), "dabble_lines": len(D), "matched": matched, "rows": rows}


def run(leagues=("NBA", "NFL", "NHL")) -> dict:
    comps = competitions()
    out = {"pulled": f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%MZ}", "break_even": BREAK_EVEN, "leagues": {}}
    for lg in leagues:
        try:
            out["leagues"][lg] = compare(lg, comps.get(lg))
        except Exception as e:                                    # one league's feed failing never sinks the others
            out["leagues"][lg] = {"league": lg, "error": f"{type(e).__name__}: {e}"[:120]}
    return out


def write(out: dict, path: str | None = None, page: str | None = None) -> str:
    from .blend import HERE
    path = path or os.path.join(HERE, "data", "shop", f"{dt.date.today().isoformat()}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f)
    if page:
        with open(page, "w") as f:
            f.write("window.SIMLAB_SHOP = " + json.dumps(out) + ";\n")
    return path
