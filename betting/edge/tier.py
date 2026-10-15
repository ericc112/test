"""80% tier scanner: PrizePicks props with a DraftKings price behind them, priced and rated by the same blend and gates.

8-10 needs a sportsbook price (model-only 80%s hit 56%). With $ODDS_API_KEY set, market = the consensus of every book's
fair price at the PrizePicks line (edge/oddsapi.py, sharp books weighted up; books more than 10 points apart cap the
rating at 7). Without it, or when no book prices the line, market = the DraftKings "k+" milestone that ESPN carries
(NHL, MLB, NBA), de-vigged;
history = the player's game log at that line (this season first, up to 30 games), blended with `final_probability`,
calibrated, rated. Only 8+ is printed by default; everything priced can be logged.
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import datetime as dt
import functools
import math
import re

from .blend import final_probability, rating
from .grade import _get
from . import lowline as LW

SITE = "https://site.api.espn.com/apis/site/v2/sports"
CORE = "https://sports.core.api.espn.com/v2/sports"
SPORT = {"NHL": ("hockey/nhl", "hockey/leagues/nhl"), "MLB": ("baseball/mlb", "baseball/leagues/mlb"),
         "NBA": ("basketball/nba", "basketball/leagues/nba"), "NFL": ("football/nfl", "football/leagues/nfl")}
# PrizePicks team abbreviation -> ESPN's (scoreboard, roster, game logs)
ALIAS = {"MLB": {"LA": "LAD"}, "NFL": {"WAS": "WSH"}, "NBA": {"NYK": "NY", "SAS": "SA", "GSW": "GS", "NOP": "NO", "UTA": "UTAH", "WAS": "WSH"}}
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
# Stats with no ESPN DraftKings ladder, priced only when The Odds API key is set (edge/oddsapi.py): stat -> market key
EXTRA = {"NHL": {"Blocked Shots": "skater_blocks", "Goalie Saves": "goalie_saves"},
         "MLB": {"Pitching Outs": "pitcher_outs", "Hits Allowed": "pitcher_hits_allowed", "Earned Runs Allowed": "pitcher_earned_runs",
                 "Walks Allowed": "pitcher_walks"},
         "NBA": {"Rebs+Asts": "rebs_asts", "Turnovers": "turnovers", "Blks+Stls": "blks_stls"},
         "NFL": {"Pass Yards": "pass_yds", "Rush Yards": "rush_yds", "Receiving Yards": "rec_yds", "Receptions": "receptions",
                 "Pass TDs": "pass_tds", "Rush+Rec Yds": "rush_rec_yds", "Pass Attempts": "pass_att", "Pass Completions": "pass_cmp",
                 "Rush Attempts": "rush_att", "INT": "pass_int", "Longest Reception": "longest_rec"}}
# market key -> ESPN game-log columns summed (3PT is 'made-attempted')
NBA_COLS = {"points": ("PTS",), "rebounds": ("REB",), "assists": ("AST",), "pra": ("PTS", "REB", "AST"), "pts_asts": ("PTS", "AST"),
            "pts_rebs": ("PTS", "REB"), "threes": ("3PT",), "steals": ("STL",), "blocks": ("BLK",), "rebs_asts": ("REB", "AST"),
            "turnovers": ("TO",), "blks_stls": ("BLK", "STL")}
# starting pitchers: market key -> statsapi pitching field
PITCH_COLS = {"pitcher_strikeouts": "strikeOuts", "pitcher_outs": "outs", "pitcher_hits_allowed": "hits",
              "pitcher_earned_runs": "earnedRuns", "pitcher_walks": "baseOnBalls"}
# NFL: market key -> ESPN game-log (category, label) columns summed
NFL_COLS = {"pass_yds": [("passing", "YDS")], "rush_yds": [("rushing", "YDS")], "rec_yds": [("receiving", "YDS")],
            "receptions": [("receiving", "REC")], "pass_tds": [("passing", "TD")], "pass_att": [("passing", "ATT")],
            "pass_cmp": [("passing", "CMP")], "rush_att": [("rushing", "CAR")], "pass_int": [("passing", "INT")],
            "longest_rec": [("receiving", "LNG")], "rush_rec_yds": [("rushing", "YDS"), ("receiving", "YDS")]}


def market_key(league: str, stat: str) -> str | None:
    return (STATS.get(league, {}).get(stat) or (None, None))[1] or EXTRA.get(league, {}).get(stat)


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
    for attempt in range(3):                                       # ESPN times out now and then; a missing day is []
        try:
            return _get(f"{SITE}/{SPORT[sport][0]}/scoreboard?dates={day:%Y%m%d}").get("events", [])
        except Exception:
            if attempt == 2:
                return []
    return []


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


@functools.lru_cache(maxsize=None)
def roster_names(sport: str, team_abbr: str) -> tuple:
    """((display name, ESPN athlete id), ...) for an ESPN team abbreviation."""
    d = _get(f"{SITE}/{SPORT[sport][0]}/teams/{team_abbr.lower()}/roster")
    out = []
    for grp in d.get("athletes", []):
        for a in (grp.get("items") if isinstance(grp, dict) and "items" in grp else [grp]):
            if isinstance(a, dict) and a.get("displayName"):
                out.append((a["displayName"], str(a["id"])))
    return tuple(out)


def roster(sport: str, team_abbr: str) -> dict:
    return {LW._fold(n): i for n, i in roster_names(sport, team_abbr)}


def _memo():
    """Game logs and player lookups are fetched once per run: one player can have a dozen priced lines."""
    for name in ("nhl_log", "mlb_log", "nfl_log", "nhl_player", "mlb_player"):
        f = getattr(LW, name)
        if not hasattr(f, "cache_info"):
            setattr(LW, name, functools.lru_cache(maxsize=None)(f))


@functools.lru_cache(maxsize=None)
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
                out.append({"date": x["date"], "season": str(year), "x": x["stat"], "vol": x["stat"].get("battersFaced", 0),
                            "opp": LW.mlb_abbr((x.get("opponent") or {}).get("id")), "home": bool(x.get("isHome"))})
    return sorted(out, key=lambda r: r["date"], reverse=True)


@functools.lru_cache(maxsize=None)
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
                    out.append({"date": m.get("gameDate", "")[:10], "team": team.get("abbreviation"), "s": dict(zip(g["labels"], ev["stats"])),
                                "opp": (m.get("opponent") or {}).get("abbreviation", ""), "home": m.get("atVs") == "vs"})
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
        if market_key == "goalie_saves":                            # starts only: saves = shots against - goals against
            return [float((g["x"].get("shotsAgainst") or 0) - (g["x"].get("goalsAgainst") or 0))
                    for g in LW.nhl_log(pid) if g["x"].get("gamesStarted")][:30]
        key = next((k for k, mk in LW.NHL_STATS.values() if mk == market_key), None)
        return None if key is None else [float(g["x"].get(key) or 0) for g in LW.nhl_log(pid)][:30]
    if sport == "MLB" and market_key in PITCH_COLS:
        return [float(g["x"].get(PITCH_COLS[market_key]) or 0) for g in mlb_pitch_log(pid)][:30]
    if sport == "NFL":
        cols = NFL_COLS.get(market_key)
        if not cols:
            return None
        out = []
        for g in LW.nfl_log(pid):
            v = [g["x"].get(c) for c in cols]
            if not all(x is None for x in v):
                out.append(sum(LW._num(x) for x in v if x is not None))
        return out[:30]
    if sport == "NBA":
        if market_key not in NBA_COLS:
            return None
        cur = espn_team("NBA", team)                                # same team only: a new team is a new role (L5)
        return [v for v in (nba_value(g["s"], market_key) for g in nba_log(pid) if g["team"] == cur) if v is not None][:30]
    return None


def card_games(sport: str, stat: str, team: str, player: str, aid: str | None = None) -> list[dict]:
    """His recent games for one stat, newest first (up to 30): {d: date, o: opponent, h: home?, v: value}. The same
    windows `history` counts (NBA: current team only; MLB batters: 3+ plate appearances; NHL saves: starts only)."""
    mk, out = market_key(sport, stat), []
    if sport == "NHL":
        try:
            pid = LW.nhl_player(NHL_API.get(team, team), player)
        except Exception:
            pid = None
        key = next((k for k, m in LW.NHL_STATS.values() if m == mk), None)
        for g in (LW.nhl_log(pid) if pid else []):
            x = g["x"]
            if mk == "goalie_saves":
                if not x.get("gamesStarted"):
                    continue
                v = (x.get("shotsAgainst") or 0) - (x.get("goalsAgainst") or 0)
            elif key:
                v = x.get(key) or 0
            else:
                break
            out.append({"d": g["date"], "o": x.get("opponentAbbrev", ""), "h": x.get("homeRoadFlag") == "H", "v": float(v)})
    elif sport == "MLB":
        pid = LW.mlb_player(team, player)
        if pid and mk in PITCH_COLS:
            out = [{"d": g["date"], "o": g.get("opp", ""), "h": g.get("home"), "v": float(g["x"].get(PITCH_COLS[mk]) or 0)}
                   for g in mlb_pitch_log(pid)]
        elif pid:
            for g in LW.mlb_log(pid):
                v = LW.value("MLB", stat, g) if (g["vol"] or 0) >= 3 else None
                if v is not None:
                    out.append({"d": g["date"], "o": g.get("opp", ""), "h": g.get("home"), "v": float(v)})
    elif sport == "NBA" and aid and mk in NBA_COLS:
        cur = espn_team("NBA", team)
        for g in nba_log(aid):
            v = nba_value(g["s"], mk) if g["team"] == cur else None
            if v is not None:
                out.append({"d": g["date"], "o": g.get("opp", ""), "h": g.get("home"), "v": v})
    elif sport == "NFL" and aid and mk in NFL_COLS:
        for g in LW.nfl_log(aid):
            v = [g["x"].get(c) for c in NFL_COLS[mk]]
            if not all(x is None for x in v):
                out.append({"d": g["date"], "o": g.get("opp", ""), "h": g.get("home"), "v": sum(LW._num(x) for x in v if x is not None)})
    return out[:30]


def history(sport: str, stat: str, team: str, player: str, line: float, aid: str | None = None) -> tuple[float | None, int, str | None]:
    """Share of his recent games on each side of the line (this season first, up to 30 games), and his league id."""
    mk = market_key(sport, stat)
    if sport in ("NBA", "NFL"):                                     # ESPN athlete id, from the ESPN roster
        if not aid:
            return None, 0, None
        vals, pid = recount_values(sport, mk, team, aid) or [], aid
    elif sport == "NHL":
        try:
            pid = LW.nhl_player(NHL_API.get(team, team), player)
        except Exception:                                           # unknown team code at the NHL API: no history
            pid = None
        if not pid:
            return None, 0, None
        vals = recount_values("NHL", mk, team, pid) or []
    elif mk in PITCH_COLS:
        pid = LW.mlb_player(team, player)
        vals = (recount_values("MLB", mk, team, pid) or []) if pid else []
    else:
        pid = LW.mlb_player(team, player)
        if not pid:
            return None, 0, None
        gl = [g for g in LW.mlb_log(pid) if (g["vol"] or 0) >= 3]
        vals = [v for v in (LW.value("MLB", stat, g) for g in gl) if v is not None]
    vals = vals[:30]
    _LAST_VALS[(sport, stat, team, player, line)] = vals
    n = sum(v != line for v in vals)
    return (sum(v > line for v in vals) / n if n else None), n, pid


_LAST_VALS: dict = {}


def recent_avg(sport: str, stat: str, team: str, player: str, line: float, k: int = 10) -> float | None:
    """Average of his last k games from the values `history` just counted for this prop."""
    v = _LAST_VALS.get((sport, stat, team, player, line)) or []
    return round(sum(v[:k]) / len(v[:k]), 2) if v else None


def ladder_line(rungs: dict) -> float | None:
    """The market's 50/50 number from a 'k+' ladder: where the de-vigged P(X >= k) crosses one half, on the
    half-point scale lines use (P(X >= k) = 0.5 is a line of k - 0.5)."""
    pts = sorted((k, devig_one_way(implied(a))) for k, a in rungs.items())
    for (k1, q1), (k2, q2) in zip(pts, pts[1:]):
        if q1 >= 0.5 > q2:
            return round(k1 - 0.5 + (q1 - 0.5) / (q1 - q2) * (k2 - k1), 1)
    return None


def projection(cx, rungs: dict | None, main_line: float | None, avg: float | None) -> tuple[float | None, str]:
    """One number to show beside the chance: the matchup model's mean when there is one, else the market's
    50/50 line (DraftKings ladder or the books' main line), else his recent average."""
    if cx:
        return round(cx[2], 1), "matchup model"
    m = ladder_line(rungs) if rungs else None
    if m is not None:
        return m, "DraftKings line"
    if main_line is not None:
        return main_line, "books' main line"
    return (round(avg, 1), "last 10 average") if avg is not None else (None, "")


def scan(leagues=("NHL", "MLB"), day: dt.date | None = None, log=print, days: int = 2) -> list[dict]:
    from . import pp
    from . import oddsapi as OA
    from . import context as CX
    _memo()
    day = day or dt.date.today()
    oa_on = OA.enabled()
    props = []
    for lg in leagues:
        try:
            props += [p for p in pp.board(lg, ("standard", "goblin", "demon"))
                      if p["stat"] in STATS.get(lg, {}) or (oa_on and p["stat"] in OA.MARKETS.get(lg, {}) and market_key(lg, p["stat"]))]
        except Exception as e:
            log(f"{lg}: board unavailable ({type(e).__name__})")
    log(f"{len(props)} PrizePicks props with a sportsbook market type ..." + ("" if oa_on else " (DraftKings via ESPN only: set $ODDS_API_KEY for every book)"))
    # The Odds API: one call per game, only the markets on this board (quota = markets x book groups)
    oa_evs, oa_odds = {}, {}
    if oa_on:
        for lg in leagues:
            if lg not in OA.SPORT_KEYS:
                continue
            try:
                oa_evs[lg] = OA.events(lg)
            except Exception as e:
                log(f"{lg}: odds API unavailable ({type(e).__name__}: {e})")
                continue
            need = collections.defaultdict(set)
            for p in props:
                if p["league"] == lg:
                    ev = OA.match_event(oa_evs[lg], p.get("team_name"), p.get("start"))
                    if ev and OA.MARKETS.get(lg, {}).get(p["stat"]):
                        need[ev["id"]].add(OA.MARKETS[lg][p["stat"]])
            for oid, mks in need.items():
                try:
                    oa_odds[(lg, oid)] = OA.event_odds(lg, oid, mks)
                except Exception as e:
                    log(f"{lg} {oid}: odds API error ({type(e).__name__}: {e})")
        log(f"odds API: {len(oa_odds)} games priced across books; requests remaining {OA.quota['remaining']}")
    LAST_OA.clear()
    LAST_OA.update(oa_odds)
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
        mk = market_key(lg, p["stat"])
        mk_over, mnote, cons = None, "", None
        if lg in oa_evs:                                            # every book first, sharp books weighted up
            ev = OA.match_event(oa_evs[lg], p.get("team_name"), p.get("start"))
            om = OA.MARKETS.get(lg, {}).get(p["stat"])
            if ev and om:
                cons = OA.consensus(OA.book_prices(oa_odds.get((lg, ev["id"]), {}), om, p["player"], p["line"]))
                if cons:
                    mk_over = cons["p_over"]
        lad_p = lad.get((lg, eid), {}).get((STATS[lg][p["stat"]][0], aid or "")) if p["stat"] in STATS.get(lg, {}) else None
        main = None
        if lg in oa_evs:
            ev = OA.match_event(oa_evs[lg], p.get("team_name"), p.get("start"))
            om = OA.MARKETS.get(lg, {}).get(p["stat"])
            main = OA.main_line(oa_odds.get((lg, ev["id"]), {}), om, p["player"]) if ev and om else None
        if mk_over is None:                                         # fallback: DraftKings ladder through ESPN
            if p["stat"] not in STATS.get(lg, {}):
                return {**p, "error": "no sportsbook price at this line"}
            if not lad_p:
                return {**p, "error": "no DraftKings ladder"}
            mk_over, mnote = market_over(lad_p, p["line"])
            if mk_over is None:
                return {**p, "error": mnote}
        h_over, n, pid = history(lg, p["stat"], p["team"], p["player"], p["line"], aid)
        # context (matchup, ice time, strikeout rates) is the model component on regular lines; goblins keep market + history
        cx = CX.price(lg, p["stat"], p.get("opp"), pid, p["line"], day.year)
        use_model = cx is not None and p.get("odds_type") == "standard"
        avg10 = recent_avg(lg, p["stat"], p["team"], p["player"], p["line"])
        proj, proj_src = projection(cx, lad_p, main, avg10)
        best = None
        for side in (["over"] if p["over_only"] else ["over", "under"]):
            pk = mk_over if side == "over" else 1 - mk_over
            ph = None if h_over is None else (h_over if side == "over" else 1 - h_over)
            pmod = (cx[0] if side == "over" else 1 - cx[0]) if use_model else None
            seg = f"{lg.lower()}:{mk}:{side}"
            e = final_probability(pmod, pk, ph, seg, n)
            rt = rating(e.p, e.confidence, pk)
            note = OA.describe(cons, side) if cons else mnote
            if cons and cons["disagree"] and rt >= 8:               # books more than 10 points apart: not an 80% read
                rt, note = 7, note + " (held at 7)"
            r = {**p, "side": side, "market_key": mk, "p_market": pk, "p_hist": ph, "hist_n": n, "p_final": e.p, "p_model": pmod,
                 "confidence": e.confidence, "rating": rt, "player_id": pid, "event_id": eid, "context": cx[1] if cx else [],
                 "proj": proj, "proj_src": proj_src, "avg10": avg10,
                 "notes": f"{note}; " + "; ".join(e.notes) + (f"; context: {' / '.join(cx[1])}" if cx else "")}
            if best is None or r["p_final"] > best["p_final"]:
                best = r
        return best

    def safe(p):
        try:
            return one(p)
        except Exception as e:                                      # one bad lookup never sinks the whole board
            return {**p, "error": f"{type(e).__name__}: {str(e)[:60]}"}

    with cf.ThreadPoolExecutor(6) as ex:
        return list(ex.map(safe, props))


LAST_OA: dict = {}          # (league, Odds API event id) -> odds fetched by the last scan, reused by book_scan at no quota cost
NHL_API = {"TB": "TBL", "NJ": "NJD", "SJ": "SJS", "LA": "LAK", "UTAH": "UTA"}   # ESPN -> NHL API team codes


def _rate(lg: str, stat: str, team: str, player: str, aid: str | None, line: float, side: str, p_market: float,
          rungs: dict | None = None, main: float | None = None, opp: str = "") -> dict:
    from . import context as CX
    h_over, n, pid = history(lg, stat, team, player, line, aid)
    ph = None if h_over is None else (h_over if side == "over" else 1 - h_over)
    e = final_probability(None, p_market, ph, f"{lg.lower()}:{market_key(lg, stat)}:{side}", n)
    avg10 = recent_avg(lg, stat, team, player, line)
    cx = CX.price(lg, stat, opp, pid, line, dt.date.today().year)
    proj, src = projection(cx, rungs, main, avg10)
    return {"p_hist": ph, "hist_n": n, "p_final": e.p, "confidence": e.confidence, "rating": rating(e.p, e.confidence, p_market),
            "proj": proj, "proj_src": src, "avg10": avg10, "context": cx[1] if cx else []}


def book_scan(leagues=("NHL", "MLB", "NBA"), day: dt.date | None = None, days: int = 1, log=print, max_rows: int = 600) -> list[dict]:
    """Sportsbook props with our rating: every DraftKings 'k+' rung ESPN carries (one-way, de-vigged), plus every
    book's over/under lines the last `scan` pulled from The Odds API. Same blend, gates and rating as the PrizePicks scan."""
    from . import oddsapi as OA
    _memo()
    day = day or dt.date.today()
    out = []
    for lg in leagues:
        if lg not in SPORT:
            continue
        evs = []
        for d in (day + dt.timedelta(days=i) for i in range(days)):
            for e in scoreboard(lg, d):
                c = e["competitions"][0]
                if c["status"]["type"]["state"] == "pre":
                    evs.append((e, {t["team"]["abbreviation"]: t["team"].get("displayName", "") for t in c["competitors"]}))
        cands = []
        rev = {lad: stat for stat, (lad, _) in STATS.get(lg, {}).items()}
        for e, teams in evs:
            who = {}
            for ab in teams:
                try:
                    for nm, aid in roster_names(lg, ab):
                        who[aid] = (nm, ab, next((o for o in teams if o != ab), ""))
                except Exception:
                    continue
            for (lad_name, aid), rungs in ladders(lg, e["id"]).items():
                if lad_name not in rev or aid not in who:
                    continue
                nm, ab, opp = who[aid]
                for k, am in rungs.items():
                    imp = implied(am)
                    if 0.5 <= imp <= 0.985 and k >= 1:
                        cands.append({"league": lg, "player": nm, "team": ab, "opp": opp, "stat": rev[lad_name], "line": k - 0.5,
                                      "side": "over", "price": am, "book": "DraftKings", "p_market": devig_one_way(imp),
                                      "aid": aid, "start": e.get("date", ""), "rungs": rungs})
            # every book, from odds the PrizePicks scan already paid for
            names = {LW._fold(v): ab for ab, v in teams.items()}
            for (olg, oid), odds in LAST_OA.items():
                if olg != lg or not odds or {LW._fold(odds.get("home_team", "")), LW._fold(odds.get("away_team", ""))} != set(names):
                    continue
                stat_of = {m: st for st, m in OA.MARKETS.get(lg, {}).items()}
                lines = collections.defaultdict(dict)                # (player, market, point) -> {side: (price, book)}
                for bk in odds.get("bookmakers", []):
                    for m in bk.get("markets", []):
                        base = m["key"].replace("_alternate", "")
                        if base not in stat_of or not market_key(lg, stat_of[base]):
                            continue
                        for o in m.get("outcomes", []):
                            if o.get("point") is None or o.get("name") not in ("Over", "Under"):
                                continue
                            key, sd = (o.get("description", ""), base, float(o["point"])), o["name"].lower()
                            if sd not in lines[key] or o["price"] > lines[key][sd][0]:
                                lines[key][sd] = (o["price"], bk.get("title") or bk["key"])
                for (pl, base, pt), best in lines.items():
                    c = OA.consensus(OA.book_prices(odds, base, pl, pt))
                    if not c:
                        continue
                    aid, ab, opp = None, "", ""
                    for a, (nm, t, o) in who.items():
                        if LW._fold(nm) == LW._fold(pl):
                            aid, ab, opp = a, t, o
                    for sd, (price, book) in best.items():
                        pm = c["p_over"] if sd == "over" else 1 - c["p_over"]
                        if pm >= 0.5:
                            cands.append({"league": lg, "player": pl, "team": ab, "opp": opp, "stat": stat_of[base], "line": pt,
                                          "side": sd, "price": price, "book": book + (f" (best of {c['n']})" if c["n"] > 1 else ""),
                                          "p_market": pm, "aid": aid, "start": e.get("date", ""), "disagree": c["disagree"],
                                          "main": OA.main_line(odds, base, pl)})
        cands.sort(key=lambda r: -r["p_market"])
        cands = cands[:max_rows]

        def one(r):
            try:
                rr = {**r, **_rate(lg, r["stat"], r["team"], r["player"], r["aid"], r["line"], r["side"], r["p_market"],
                                   r.get("rungs"), r.get("main"), r.get("opp", ""))}
                rr.pop("rungs", None)
            except Exception:
                return None
            if rr.get("disagree") and rr["rating"] >= 8:
                rr["rating"] = 7
            return rr
        with cf.ThreadPoolExecutor(6) as ex:
            rows = [r for r in ex.map(one, cands) if r]
        log(f"{lg}: {len(rows)} sportsbook props rated")
        out += rows
    return out


_PK: dict = {}


def grade_id(r: dict) -> str:
    """The id our graders want: NHL gameId (api-web), MLB gamePk (statsapi); NBA grades on ESPN's own event id."""
    if r["league"] in ("NBA", "NFL"):
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
