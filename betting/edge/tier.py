"""80% tier scanner: PrizePicks props with a DraftKings price behind them, priced and rated by the same blend and gates.

8-10 needs a sportsbook price (model-only 80%s hit 56%), so this scans the leagues where ESPN carries DraftKings
player ladders (NHL, MLB): for each PrizePicks line, market = the DraftKings "k+" milestone at that line (de-vigged),
history = the player's game log at that line (this season first, up to 30 games), blended with `final_probability`,
calibrated, rated. Only 8+ is printed by default; everything priced can be logged.
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import datetime as dt
import math
import re

from .blend import final_probability, rating
from .grade import _get
from . import lowline as LW

SITE = "https://site.api.espn.com/apis/site/v2/sports"
CORE = "https://sports.core.api.espn.com/v2/sports"
SPORT = {"NHL": ("hockey/nhl", "hockey/leagues/nhl"), "MLB": ("baseball/mlb", "baseball/leagues/mlb")}
# PrizePicks stat -> (DraftKings ladder, our market key, game-log reader)
STATS = {
    "NHL": {"Shots On Goal": ("Shots on Goal Milestones", "skater_sog"), "Points": ("Points Milestones", "skater_points"),
            "Assists": ("Assists Milestones", "skater_assists"), "Power Play Points": ("Powerplay Points Milestones", "skater_ppp"),
            "Goals": ("Goals Milestones", "skater_goals")},
    "MLB": {"Hits": ("Hits Milestones", "batter_hits"), "Total Bases": ("Total Bases Milestones", "batter_total_bases"),
            "Hits+Runs+RBIs": ("Hits + Runs + RBIs Milestones", "batter_hrr"), "Runs": ("Runs Milestones", "batter_runs"),
            "RBIs": ("RBIs Milestones", "batter_rbi"), "Hitter Strikeouts": ("Strikeouts (Batter) Milestones", "batter_strikeouts"),
            "Walks": ("Walks (Batter) Milestones", "batter_walks"), "Singles": ("Singles Milestones", "batter_singles"),
            "Doubles": ("Doubles Milestones", "batter_doubles"), "Home Runs": ("Home Runs Milestones", "batter_home_runs"),
            "Stolen Bases": ("Stolen Bases Milestones", "batter_sb"), "Pitcher Strikeouts": ("Strikeouts Thrown Milestones", "pitcher_strikeouts")},
}


def implied(am: float) -> float:
    return 100 / (am + 100) if am > 0 else -am / (-am + 100)


def devig_one_way(p: float) -> float:
    """One-sided milestone prices carry ~7% hold on mid prices and less on heavy favourites (7% -> 3%)."""
    hold = 0.93 + 0.04 * min(1.0, max(0.0, (p - 0.6) / 0.3))
    return min(0.99, p * hold)


def scoreboard(sport: str, day: dt.date) -> list[dict]:
    return _get(f"{SITE}/{SPORT[sport][0]}/scoreboard?dates={day:%Y%m%d}").get("events", [])


def ladders(sport: str, event_id: str) -> dict:
    """{(ladder name, ESPN athlete id): {k: american odds for 'k+'}} plus the athlete's display name."""
    items, page = [], 1
    while True:
        try:
            d = _get(f"{CORE}/{SPORT[sport][1]}/events/{event_id}/competitions/{event_id}/odds/100/propBets?limit=1000&page={page}")
        except Exception:
            return {}                                              # no props posted for this game (404) yet
        items += d.get("items", [])
        if page >= d.get("pageCount", 1):
            break
        page += 1
    lad = collections.defaultdict(dict)
    for x in items:
        m = re.search(r"/athletes/(\d+)", (x.get("athlete") or {}).get("$ref", ""))
        cur = x.get("current") or {}
        k = (cur.get("target") or {}).get("value")
        am = (cur.get("over") or {}).get("american") or ((x.get("odds") or {}).get("american") or {}).get("value")
        if m and k is not None and am not in (None, "") and "Fewer" not in str((cur.get("target") or {}).get("displayValue", "")):
            try:
                lad[(x["type"]["name"], m.group(1))][int(float(k))] = float(am)
            except ValueError:
                continue
    return lad


def roster(sport: str, team_abbr: str) -> dict:
    d = _get(f"{SITE}/{SPORT[sport][0]}/teams/{team_abbr.lower()}/roster")
    out = {}
    for grp in d.get("athletes", []):
        for a in (grp.get("items") if isinstance(grp, dict) and "items" in grp else [grp]):
            if isinstance(a, dict) and a.get("displayName"):
                out[LW._fold(a["displayName"])] = str(a["id"])
    return out


def mlb_pitch_log(pid: str) -> list[dict]:
    out = []
    year = dt.date.today().year
    for gt in ("R", "F", "D", "L"):
        try:
            sp = _get(f"https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=gameLog&group=pitching&season={year}&gameType={gt}")["stats"]
        except Exception:
            continue
        for x in (sp[0]["splits"] if sp else []):
            if x["stat"].get("gamesStarted"):
                out.append({"date": x["date"], "season": str(year), "x": x["stat"], "vol": x["stat"].get("battersFaced", 0)})
    return sorted(out, key=lambda r: r["date"], reverse=True)


def history(sport: str, stat: str, team: str, player: str, line: float) -> tuple[float | None, int, str | None]:
    """Share of his recent games on each side of the line (this season first, up to 30 games), and his league id."""
    if sport == "NHL":
        pid = LW.nhl_player(team, player)
        if not pid:
            return None, 0, None
        key = LW.NHL_STATS[stat][0]
        vals = [float(g["x"].get(key) or 0) for g in LW.nhl_log(pid)]
    elif stat == "Pitcher Strikeouts":
        pid = LW.mlb_player(team, player)
        vals = [float(g["x"].get("strikeOuts") or 0) for g in mlb_pitch_log(pid)] if pid else []
    else:
        pid = LW.mlb_player(team, player)
        if not pid:
            return None, 0, None
        gl = [g for g in LW.mlb_log(pid) if (g["vol"] or 0) >= 3]
        vals = [v for v in (LW.value("MLB", stat, g) for g in gl) if v is not None]
    vals = vals[:30]
    n = sum(v != line for v in vals)
    return (sum(v > line for v in vals) / n if n else None), n, pid


def scan(leagues=("NHL", "MLB"), day: dt.date | None = None, log=print) -> list[dict]:
    from . import pp
    day = day or dt.date.today()
    props = []
    for lg in leagues:
        try:
            props += [p for p in pp.board(lg, ("standard", "goblin", "demon")) if p["stat"] in STATS[lg]]
        except Exception as e:
            log(f"{lg}: board unavailable ({type(e).__name__})")
    log(f"{len(props)} PrizePicks props with a DraftKings ladder type ...")
    events, lad, rost = {}, {}, {}
    for lg in leagues:
        for d in (day, day + dt.timedelta(days=1)):
            for e in scoreboard(lg, d):
                c = e["competitions"][0]
                if c["status"]["type"]["state"] != "pre":
                    continue
                teams = {t["team"]["abbreviation"]: t["team"] for t in c["competitors"]}
                for ab in teams:
                    events.setdefault((lg, ab), e["id"])           # tonight's game wins over tomorrow's
    games = sorted(set((k[0], v) for k, v in events.items()))
    with cf.ThreadPoolExecutor(6) as ex:
        for key, l in zip(games, ex.map(lambda kv: ladders(*kv), games)):
            lad[key] = l

    def one(p):
        lg = p["league"]
        eid = events.get((lg, p["team"])) or events.get((lg, {"WSH": "WSH", "LA": "LAD"}.get(p["team"], p["team"])))
        if not eid:
            return {**p, "error": "game not found / started"}
        key = (lg, p["team"])
        if key not in rost:
            try:
                rost[key] = roster(lg, p["team"])
            except Exception:
                rost[key] = {}
        aid = rost[key].get(LW._fold(p["player"]))
        ladder_name, mk = STATS[lg][p["stat"]]
        lad_p = lad.get((lg, eid), {}).get((ladder_name, aid or ""))
        if not lad_p:
            return {**p, "error": "no DraftKings ladder"}
        k = int(math.floor(p["line"])) + 1                         # 'More 1.5' = k+ at 2
        if k not in lad_p:
            return {**p, "error": f"no {k}+ rung"}
        mk_over = devig_one_way(implied(lad_p[k]))
        h_over, n, pid = history(lg, p["stat"], p["team"], p["player"], p["line"])
        best = None
        for side in (["over"] if p["over_only"] else ["over", "under"]):
            pk = mk_over if side == "over" else 1 - mk_over
            ph = None if h_over is None else (h_over if side == "over" else 1 - h_over)
            seg = f"{lg.lower()}:{mk}:{side}"
            e = final_probability(None, pk, ph, seg, n)
            r = {**p, "side": side, "market_key": mk, "p_market": pk, "p_hist": ph, "hist_n": n, "p_final": e.p,
                 "confidence": e.confidence, "rating": rating(e.p, e.confidence, pk), "player_id": pid, "event_id": eid,
                 "notes": f"DK {k}+ {lad_p[k]:+.0f}; " + "; ".join(e.notes)}
            if best is None or r["p_final"] > best["p_final"]:
                best = r
        return best

    with cf.ThreadPoolExecutor(6) as ex:
        return list(ex.map(one, props))


_PK: dict = {}


def grade_id(r: dict) -> str:
    """The id our graders want: NHL gameId (api-web), MLB gamePk (statsapi); ESPN ids don't grade."""
    day = (r.get("start") or dt.date.today().isoformat())[:10]
    key = (r["league"], r["team"], day)
    if key not in _PK:
        _PK[key] = ""
        try:
            if r["league"] == "MLB":
                for d in _get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={day}&hydrate=team")["dates"]:
                    for g in d["games"]:
                        if r["team"] in (g["teams"]["away"]["team"].get("abbreviation"), g["teams"]["home"]["team"].get("abbreviation")):
                            _PK[key] = str(g["gamePk"])
            else:
                for wk in _get(f"https://api-web.nhle.com/v1/schedule/{day}").get("gameWeek", [])[:1]:
                    for g in wk["games"]:
                        if r["team"] in (g["awayTeam"]["abbrev"], g["homeTeam"]["abbrev"]):
                            _PK[key] = str(g["id"])
        except Exception:
            pass
    return _PK[key]
