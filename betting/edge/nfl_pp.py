"""PrizePicks NFL board, priced by the NFL simulator anchored on DraftKings' lines.

The NFL backtest (README, weeks 3-8, 5,354 DraftKings closing props) says DraftKings' line is the better centre and
the simulation the better shape: alone the simulation shows no edge over the line, but re-centred on the DraftKings
line it prices lines 10-20 yards away well (Brier 0.196, buckets within ~5 pts). A PrizePicks line that differs from
DraftKings' is exactly that case. So each PrizePicks leg gets:

  market   P(side) from the simulated distribution re-centred on DraftKings' line for the same player and stat
           (nfl.anchored_over). The feed has no prices, so DraftKings' line counts as a 50/50 median.
  model    the simulation's own P(side) at the PrizePicks line, shrunk toward 50% by MODEL_SHRINK.
  history  this season's over/under count at the PrizePicks line.

blended by blend.final_probability (same gates and learned corrections as `edge prob`). A leg with no DraftKings line
for that player and stat has no market component and is held at Low: the simulation alone has no edge on a line.
Role flags (back from injury, under 3 games with the team, line far from the model) also hold a leg at Low.
"""
from __future__ import annotations

import datetime as dt

import numpy as np

from . import nfl

STATS = {"Pass Yards": "pass_yds", "Pass Attempts": "pass_att", "Pass Completions": "completions", "Pass TDs": "pass_td",
         "INT": "pass_int", "Rush Yards": "rush_yds", "Rush Attempts": "rush_att", "Receiving Yards": "rec_yds",
         "Receptions": "receptions", "Rush+Rec Yds": "rush_rec_yds"}
LABEL = {v: k.lower() for k, v in STATS.items()}
ESPN = {"JAC": "JAX", "LA": "LAR", "WAS": "WSH", "LAR": "LAR"}           # PrizePicks abbreviation -> ESPN
BREAK_EVEN = {"standard": 0.577}                                          # 2-pick power; goblin/demon multipliers unknown


COUNT_MARKETS = {"receptions", "rush_att", "completions", "pass_att", "pass_td", "pass_int"}
JUICED = {"pass_td", "pass_int"}


def anchored_count(arr: np.ndarray, dk_line: float, line: float) -> float:
    """P(over `line`) for a count stat, from the simulated distribution tilted (exponentially) so that DraftKings'
    line is its median: P(X > dk_line) = 1/2. Unlike a half-unit shift this keeps the integer support, so a push at a
    whole-number PrizePicks line stays a push (Burrow over 2.0 pass TDs wins on 3+, pushes on 2)."""
    k, c = np.unique(np.round(arr).astype(int), return_counts=True)
    pk = c / c.sum()
    z = (k - k.mean()) / max(k.std(), 1e-9)

    def tilt(theta):
        w = pk * np.exp(theta * z)
        return w / w.sum()
    lo, hi = -8.0, 8.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if tilt(mid)[k > dk_line].sum() < 0.5:
            lo = mid
        else:
            hi = mid
    w = tilt((lo + hi) / 2)
    over = float(w[k > line].sum())
    push = float(w[k == line].sum()) if float(line).is_integer() else 0.0
    return over / max(1 - push, 1e-9)


def espn_abbr(a: str | None) -> str:
    return ESPN.get((a or "").upper(), (a or "").upper())


def match_events(props: list[dict], season: int, week: int) -> dict:
    """PrizePicks game (away, home) -> ESPN event for this week."""
    evs = nfl.week_events(season, week)
    by_teams = {}
    for e in evs:
        by_teams[(e["away_abbr"], e["home_abbr"])] = e
    out = {}
    for p in props:
        k = (espn_abbr(p.get("away")), espn_abbr(p.get("home")))
        if k in by_teams:
            out[(p.get("away"), p.get("home"))] = by_teams[k]
    return out


def price_leg(res: dict, name: str, market: str, line: float, over_only: bool = False, side: str | None = None) -> dict | None:
    """One PrizePicks line priced from a priced game (nfl.price_game). `side` forces a side (verify); otherwise the
    better side is chosen. None when the player or stat isn't in the simulation."""
    from .blend import final_probability
    from .nba_pp import find_player
    sim = res["sim"]
    plist = [{"name": p.get("name", ""), "id": pid} for pid, p in sim["players"].items() if market in p]
    hit = find_player(name, plist) if plist else None
    if not hit:
        return None
    pid = hit["id"]
    p = sim["players"][pid]
    arr = p[market]
    dk = next((r for r in res["rows"] if str(r["player_id"]) == str(pid) and r["market"] == market), None)
    dk_line = dk["line"] if dk else None
    so, su, push = nfl.side_probs(arr, line)
    if dk_line is None:
        a_over = None
    elif abs(dk_line - line) < 1e-9:
        a_over = 0.5            # PrizePicks posts DraftKings' line: with no prices in the feed the market says 50/50
    elif market in COUNT_MARKETS:
        a_over = anchored_count(arr, dk_line, line)
    else:
        a_over = nfl.anchored_over(arr, dk_line, line)
    ho, hu = nfl.player_history(pid, p["team"], res["history"], market, line)
    med, mu = float(np.median(arr)), float(np.mean(arr))
    flags = nfl.role_flags(p, market, line, med, mu)
    best = None
    for sd in (["over"] if over_only else ["over", "under"]):
        if side and sd != side:
            continue
        pm = nfl.calibrated((so if sd == "over" else su) / max(1 - push, 1e-9), market)
        pk = None if a_over is None else (a_over if sd == "over" else 1 - a_over)
        dec = ho + hu
        ph = (ho if sd == "over" else hu) / dec if dec else None
        e = final_probability(pm, pk, ph, f"nfl:{market}:{sd}", dec)
        conf = e.confidence
        why = []
        if pk is None and conf in ("High", "Medium"):
            conf, why = "Low", ["no DraftKings line for this player and stat: the simulation alone has no edge on a line"]
        if flags and conf in ("High", "Medium"):
            conf = "Low"
        if market in JUICED and conf in ("High", "Medium"):
            conf, why = "Low", why + ["TD and interception lines are often heavily juiced and the feed has no prices: DraftKings' line isn't a 50/50 median here"]
        if best is None or e.p > best["p_final"]:
            best = {"side": sd, "p_model": round(pm, 4), "p_market": None if pk is None else round(pk, 4),
                    "p_hist": None if ph is None else round(ph, 4), "hist_n": dec, "p_final": e.p, "confidence": conf, "why": why}
    vol_key = {"rec_yds": "targets", "receptions": "targets", "rush_yds": "rush_att", "rush_att": "rush_att",
               "rush_rec_yds": "rush_att"}.get(market, "pass_att")
    vol = p.get(vol_key)
    return {"player_id": str(pid), "sim_name": p.get("name"), "team_espn": sim["teams"][p["team"]]["abbr"], "dk_line": dk_line,
            "median": med, "mean": mu, "q25": float(np.percentile(arr, 25)), "q75": float(np.percentile(arr, 75)),
            "volume": (vol_key, float(np.mean(vol))) if vol is not None else None, "flags": flags,
            "hist": (ho, hu), **best}


def verdict(r: dict) -> str:
    be = BREAK_EVEN.get(r.get("odds_type"))
    if be is None:
        return "PASS (payout multiplier unknown for this line type)"
    if r["confidence"] == "High" and r["p_final"] >= 0.65 and r["p_final"] >= be + 0.02:
        return f"ENTRY LEG (High, {r['p_final']:.0%} vs break-even {be:.1%})"
    if r["confidence"] in ("High", "Medium"):
        return "LEAN (Medium: show, don't enter)" if r["confidence"] == "Medium" else "LEAN (High but under 65%)"
    return "PASS (below the gate)"


def price_board(props: list[dict], n: int = 50000, season: int = 2026, week: int | None = None, log=print) -> list[dict]:
    """Price every supported standard PrizePicks NFL line, one simulation per game."""
    props = [p for p in props if p["stat"] in STATS and p.get("odds_type") == "standard"]
    if week is None:
        week = current_week(season)
    games = match_events(props, season, week)
    rows = []
    for key, ev in sorted(games.items(), key=lambda kv: kv[1]["date"]):
        mine = [p for p in props if (p.get("away"), p.get("home")) == key]
        log(f"  {ev['away_abbr']} @ {ev['home_abbr']}: {len(mine)} lines, simulating...")
        try:
            res = nfl.price_game(ev["id"], n=n, season=season)
        except Exception as e:                          # one game's feed failing never sinks the board
            rows += [{**p, "error": f"{type(e).__name__}: {e}"[:120]} for p in mine]
            continue
        for p in mine:
            m = STATS[p["stat"]]
            x = price_leg(res, p["player"], m, p["line"], p.get("over_only", False))
            if not x:
                rows.append({**p, "error": "player or stat not in the simulation"})
                continue
            opp = ev["home_abbr"] if x["team_espn"] == ev["away_abbr"] else ev["away_abbr"]
            gap = None if x["dk_line"] is None else p["line"] - x["dk_line"]
            note = (f"nfl sim median {x['median']:.1f} (25-75th {x['q25']:.0f}-{x['q75']:.0f})"
                    + (f", {x['volume'][0]} {x['volume'][1]:.1f}" if x["volume"] else "")
                    + (f"; DraftKings line {x['dk_line']} (PrizePicks {gap:+g})" if x["dk_line"] is not None else "; no DraftKings line")
                    + (f"; flags: {', '.join(x['flags'])}" if x["flags"] else "") + (f"; {x['why'][0]}" if x["why"] else "")
                    + f"; history {x['hist'][0]} over / {x['hist'][1]} under; pulled {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%MZ}")
            rows.append({**p, **x, "event_id": ev["id"], "team": x["team_espn"], "opp": opp, "market_key": m, "sport": "nfl",
                         "script": f"nfl:{ev['id']}", "game": f"{ev['away_abbr']} @ {ev['home_abbr']}", "start": ev["date"],
                         "proj": x["median"], "opp_proj": None if not x["volume"] else round(x["volume"][1], 1), "notes": note,
                         "gap": gap, "newcomer": bool(x["flags"])})
    return rows


def current_week(season: int) -> int:
    """The first week with a game that hasn't finished."""
    for wk in range(1, 19):
        evs = nfl.week_events(season, wk)
        if any(e["status"] != "STATUS_FINAL" for e in evs):
            return wk
    return 18


def pick_order(rows: list[dict], top: int = 5) -> list[dict]:
    """Best legs by probability, High before Medium, one per game."""
    rank = {"High": 0, "Medium": 1, "Low": 2}
    ok = sorted([r for r in rows if "error" not in r], key=lambda r: (rank.get(r["confidence"], 3), -r["p_final"]))
    seen, out = set(), []
    for r in ok:
        if r["script"] in seen:
            continue
        seen.add(r["script"])
        out.append(r)
        if len(out) == top:
            break
    return out


def write_up(r: dict, verified: str = "", warns: list | None = None) -> str:
    f = lambda v: "-" if v is None else f"{v:.0%}"
    lines = [f"### {r.get('bet_id', '')}{r['player']} ({r['team']}) {r['side'].upper()} {r['line']} {LABEL[r['market_key']]} — {r['game']}",
             f"**{r['p_final']:.1%} {r['confidence']}** · {verdict(r)}" + (f" · back-check: **{verified}**" if verified else ""),
             f"- Sources: DraftKings-anchored {f(r['p_market'])}"
             + (f" (DraftKings line {r['dk_line']}, PrizePicks {r['gap']:+g})" if r["dk_line"] is not None else " (no DraftKings line)")
             + f" · simulation {f(r['p_model'])} (shrunk) · this season {r['hist'][0]} over / {r['hist'][1]} under",
             f"- Simulation: median {r['median']:.1f}, 25–75th {r['q25']:.0f}–{r['q75']:.0f}"
             + (f", {r['volume'][1]:.1f} {r['volume'][0].replace('_', ' ')}" if r["volume"] else "")]
    if r["flags"]:
        lines.append("- Role flags: " + "; ".join(r["flags"]))
    if warns:
        lines.append("- Back-check warnings: " + "; ".join(warns))
    return "\n".join(lines)
