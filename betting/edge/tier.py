"""80% tier scanner: PrizePicks props with a DraftKings price behind them, priced and rated by the same blend and gates.

8-10 needs a sportsbook price (model-only 80%s hit 56%), so this scans the leagues where ESPN carries DraftKings
player ladders (NHL, MLB, NBA): for each PrizePicks line, market = the DraftKings "k+" milestone at that line (de-vigged),
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
SPORT = {"NHL": ("hockey/nhl", "hockey/leagues/nhl"), "MLB": ("baseball/mlb", "baseball/leagues/mlb"),
         "NBA": ("basketball/nba", "basketball/leagues/nba")}
# PrizePicks team abbreviation -> ESPN's (scoreboard, roster, game logs)
ALIAS = {"MLB": {"LA": "LAD"}, "NBA": {"NYK": "NY", "SAS": "SA", "GSW": "GS", "NOP": "NO", "UTA": "UTAH", "WAS": "WSH"}}
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
    # 'Total X' over/under pairs stay unmapped: only the k+ milestone ladders are priced one-way here
    "NBA": {"Points": ("Points Milestones", "points"), "Rebounds": ("Rebounds Milestones", "rebounds"),
            "Assists": ("Assists Milestones", "assists"), "Pts+Rebs+Asts": ("Points + Assists + Rebounds Milestones", "pra"),
            "Pts+Asts": ("Points + Assists Milestones", "pts_asts"), "Pts+Rebs": ("Points + Rebounds Milestones", "pts_rebs"),
            "3-PT Made": ("3-Point Field Goals Milestones", "threes"), "Steals": ("Steals Milestones", "steals"),
            "Blocked Shots": ("Blocks Milestones", "blocks")},
}
# market key -> ESPN game-log columns summed (3PT is 'made-attempted')
NBA_COLS = {"points": ("PTS",), "rebounds": ("REB",), "assists": ("AST",), "pra": ("PTS", "REB", "AST"), "pts_asts": ("PTS", "AST"),
            "pts_rebs": ("PTS", "REB"), "threes": ("3PT",), "steals": ("STL",), "blocks": ("BLK",)}


def espn_team(league: str, team: str) -> str:
    return ALIAS.get(league, {}).get(team, team)


def implied(am: float) -> float:
    return 100 / (am + 100) if am > 0 else -am / (-am + 100)


def devig_one_way(p: float) -> float:
    """One-sided milestone prices carry ~7% hold on mid prices and less on heavy favourites (7% -> 3%)."""
    hold = 0.93 + 0.04 * min(1.0, max(0.0, (p - 0.6) / 0.3))
    return min(0.99, p * hold)


def market_over(lad: dict, line: float) -> tuple[float | None, str]:
    """De-vigged chance of the over at a PrizePicks line from a DraftKings 'k+' ladder.

    Half lines read one rung ('More 1.5' = 2+). A whole line pushes when the stat lands on it, so the over is
    P(L+1 or more) out of the non-push outcomes: 'Less 2.0' wins on 0-1 only, not 0-2.
    """
    k = int(math.floor(line)) + 1
    if k not in lad:
        return None, f"no {k}+ rung"
    over = devig_one_way(implied(lad[k]))
    if line != int(line) or int(line) <= 0:
        return over, f"DK {k}+ {lad[k]:+.0f}"
    if int(line) not in lad:
        return None, f"whole line {line:g}: no {int(line)}+ rung to price the push"
    at = max(over, devig_one_way(implied(lad[int(line)])))
    push = at - over
    return over / (1 - push), f"DK {k}+ {lad[k]:+.0f}, {int(line)}+ {lad[int(line)]:+.0f}; push {push:.0%} removed"


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


def nba_log(aid: str) -> list[dict]:
    """Regular-season games, newest first, this season then last. All-Star games and total rows are skipped; playoffs
    and preseason are a different kind of game (L26) and stay out."""
    today = dt.date.today()
    yr = today.year + (1 if today.month >= 8 else 0)              # ESPN names the season by the year it ends
    out = []
    for season in (yr, yr - 1):
        try:
            g = _get(f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{aid}/gamelog?season={season}")
        except Exception:
            continue
        for st in g.get("seasonTypes", []):
            if "Regular Season" not in st.get("displayName", ""):
                continue
            for cat in st.get("categories", []):
                if cat.get("type") != "event":
                    continue
                for ev in cat.get("events") or []:
                    m = g.get("events", {}).get(ev["eventId"]) or {}
                    team = m.get("team") or {}
                    if team.get("isAllStar"):
                        continue
                    out.append({"date": m.get("gameDate", "")[:10], "team": team.get("abbreviation"), "s": dict(zip(g["labels"], ev["stats"]))})
    return sorted(out, key=lambda r: r["date"], reverse=True)


def nba_value(s: dict, market_key: str) -> float | None:
    tot = 0.0
    for c in NBA_COLS[market_key]:
        v = s.get(c)
        if v in (None, "", "-"):
            return None
        tot += float(str(v).split("-")[0])
    return tot


def recount_values(sport: str, market_key: str, team: str, pid: str) -> list[float] | None:
    """Per-game values the scan's history used, newest first (up to 30); None when the market has no reader here."""
    if sport == "NHL":
        key = next((k for k, mk in LW.NHL_STATS.values() if mk == market_key), None)
        return None if key is None else [float(g["x"].get(key) or 0) for g in LW.nhl_log(pid)][:30]
    if sport == "NBA":
        if market_key not in NBA_COLS:
            return None
        cur = espn_team("NBA", team)                                # same team only: a new team is a new role (L5)
        return [v for v in (nba_value(g["s"], market_key) for g in nba_log(pid) if g["team"] == cur) if v is not None][:30]
    return None


def history(sport: str, stat: str, team: str, player: str, line: float, aid: str | None = None) -> tuple[float | None, int, str | None]:
    """Share of his recent games on each side of the line (this season first, up to 30 games), and his league id."""
    if sport == "NBA":
        if not aid:
            return None, 0, None
        vals, pid = recount_values("NBA", STATS["NBA"][stat][1], team, aid), aid
    elif sport == "NHL":
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


def scan(leagues=("NHL", "MLB"), day: dt.date | None = None, log=print, days: int = 2) -> list[dict]:
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
        for d in (day + dt.timedelta(days=i) for i in range(days)):
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
        eid = events.get((lg, p["team"])) or events.get((lg, espn_team(lg, p["team"])))
        if not eid:
            return {**p, "error": "game not found / started"}
        key = (lg, p["team"])
        if key not in rost:
            try:
                rost[key] = roster(lg, espn_team(lg, p["team"]))
            except Exception:
                rost[key] = {}
        aid = rost[key].get(LW._fold(p["player"]))
        ladder_name, mk = STATS[lg][p["stat"]]
        lad_p = lad.get((lg, eid), {}).get((ladder_name, aid or ""))
        if not lad_p:
            return {**p, "error": "no DraftKings ladder"}
        mk_over, mnote = market_over(lad_p, p["line"])
        if mk_over is None:
            return {**p, "error": mnote}
        h_over, n, pid = history(lg, p["stat"], p["team"], p["player"], p["line"], aid)
        best = None
        for side in (["over"] if p["over_only"] else ["over", "under"]):
            pk = mk_over if side == "over" else 1 - mk_over
            ph = None if h_over is None else (h_over if side == "over" else 1 - h_over)
            seg = f"{lg.lower()}:{mk}:{side}"
            e = final_probability(None, pk, ph, seg, n)
            r = {**p, "side": side, "market_key": mk, "p_market": pk, "p_hist": ph, "hist_n": n, "p_final": e.p,
                 "confidence": e.confidence, "rating": rating(e.p, e.confidence, pk), "player_id": pid, "event_id": eid,
                 "notes": f"{mnote}; " + "; ".join(e.notes)}
            if best is None or r["p_final"] > best["p_final"]:
                best = r
        return best

    with cf.ThreadPoolExecutor(6) as ex:
        return list(ex.map(one, props))


_PK: dict = {}


def grade_id(r: dict) -> str:
    """The id our graders want: NHL gameId (api-web), MLB gamePk (statsapi); NBA grades on ESPN's own event id."""
    if r["league"] == "NBA":
        return str(r["event_id"])
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
