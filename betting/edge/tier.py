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
import unicodedata

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
EXTRA = {"NHL": {"Blocked Shots": "skater_blocks", "Goalie Saves": "goalie_saves", "Hits": "skater_hits"},
         "MLB": {"Pitching Outs": "pitcher_outs", "Hits Allowed": "pitcher_hits_allowed", "Earned Runs Allowed": "pitcher_earned_runs",
                 "Walks Allowed": "pitcher_walks"},
         "NBA": {"Rebs+Asts": "rebs_asts", "Turnovers": "turnovers", "Blks+Stls": "blks_stls"},
         "NFL": {"Pass Yards": "pass_yds", "Rush Yards": "rush_yds", "Receiving Yards": "rec_yds", "Receptions": "receptions",
                 "Pass TDs": "pass_tds", "Rush+Rec Yds": "rush_rec_yds", "Pass Attempts": "pass_att", "Pass Completions": "pass_cmp",
                 "Rush Attempts": "rush_att", "INT": "pass_int", "Longest Reception": "longest_rec", "Rush+Rec TDs": "anytime_td",
                 "FG Made": "fg_made", "Kicking Points": "kicking_pts", "Pass+Rush Yds": "pass_rush_yds"}}
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
            "longest_rec": [("receiving", "LNG")], "rush_rec_yds": [("rushing", "YDS"), ("receiving", "YDS")],
            "anytime_td": [("rushing", "TD"), ("receiving", "TD")], "fg_made": [("fieldgoals", "FG")], "kicking_pts": [("pats", "PTS")],
            "pass_rush_yds": [("passing", "YDS"), ("rushing", "YDS")]}
# slates: how many days ahead a league's next game can be (NFL plays weekly)
SLATE_DAYS = {"NFL": 8}


def nfl_num(v) -> float:
    """An ESPN NFL game-log cell: '1,204' -> 1204, '3-4' (made-attempted) -> 3, '-3' -> -3."""
    t = str(v).replace(",", "").strip()
    m = re.match(r"^(\d+)-(\d+)$", t)
    return float(m.group(1)) if m else LW._num(t)


# combo props DraftKings may not ladder: built from the parts' ladders (market key -> PrizePicks stats of the parts)
COMBO_PARTS = {"NBA": {"pra": ("Points", "Rebounds", "Assists"), "pts_asts": ("Points", "Assists"),
                       "pts_rebs": ("Points", "Rebounds"), "rebs_asts": ("Rebounds", "Assists")}}


def ladder_pmf(rungs: dict, top: int = 80) -> list[float]:
    """A 'k+' ladder as a distribution: de-vigged P(X >= k) at each rung, logit-interpolated between rungs, a geometric
    tail past the last one."""
    ks = sorted(int(k) for k in rungs)
    surv = {k: devig_one_way(implied(float(rungs[k] if k in rungs else rungs[str(k)]))) for k in ks}
    lk, lp = [0] + ks, [0.999] + [surv[k] for k in ks]
    lg = lambda q: math.log(q / (1 - q))
    s = [1.0]
    for x in range(1, top + 1):
        if x >= ks[-1]:
            v = surv[ks[-1]] * 0.75 ** (x - ks[-1])
        else:
            i = max(j for j in range(len(lk)) if lk[j] <= x)
            t = (x - lk[i]) / (lk[i + 1] - lk[i])
            v = 1 / (1 + math.exp(-((1 - t) * lg(lp[i]) + t * lg(lp[i + 1]))))
        s.append(min(s[-1], v))
    pm = [s[x] - (s[x + 1] if x < top else 0.0) for x in range(top + 1)]
    tot = sum(pm)
    return [q / tot for q in pm]


def combo_over(parts: list[dict], line: float) -> float:
    """P(sum > line) from the parts' ladders, convolved as independent; whole lines remove the push."""
    dist = [1.0]
    for rungs in parts:
        q = ladder_pmf(rungs)
        out = [0.0] * (len(dist) + len(q) - 1)
        for i, a in enumerate(dist):
            if a:
                for j, b in enumerate(q):
                    out[i + j] += a * b
        dist = out
    over = sum(dist[int(math.floor(line)) + 1:])
    if line == int(line):
        at = dist[int(line)] if int(line) < len(dist) else 0.0
        return over / max(1e-9, 1 - at)
    return over


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
def nba_log(aid: str, kind: str = "Regular Season") -> list[dict]:
    """One competition's games, newest first: regular season (this season then last) or, for a preseason game,
    preseason games from the last four preseasons (L26: a preseason star plays capped minutes, so his regular-season
    log is a different kind of game). All-Star games and total rows are skipped."""
    today = dt.date.today()
    yr = today.year + (1 if today.month >= 8 else 0)              # ESPN names the season by the year it ends
    out = []
    for season in ((yr, yr - 1) if kind == "Regular Season" else (yr, yr - 1, yr - 2, yr - 3)):
        try:
            g = _get(f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{aid}/gamelog?season={season}")
        except Exception:
            continue
        for st in g.get("seasonTypes", []):
            if kind not in st.get("displayName", ""):
                continue
            for cat in st.get("categories", []):
                if cat.get("type") != "event":
                    continue
                for ev in cat.get("events") or []:
                    m = g.get("events", {}).get(ev["eventId"]) or {}
                    team = m.get("team") or {}
                    if team.get("isAllStar"):
                        continue
                    out.append({"date": m.get("gameDate", "")[:10], "start": m.get("gameDate", ""), "team": team.get("abbreviation"),
                                "s": dict(zip(g["labels"], ev["stats"])),
                                "opp": (m.get("opponent") or {}).get("abbreviation", ""), "home": m.get("atVs") == "vs"})
    return sorted(out, key=lambda r: r["date"], reverse=True)


PRESEASON_MARKET_WEIGHT = 0.5    # preseason props are set off regular-season rates with low limits: the book counts half
PRESEASON_B2B = 0.9              # second night of a preseason back-to-back: stars play less (or sit: a void)


def _minutes(g: dict) -> float:
    try:
        return float(str(g["s"].get("MIN") or 0).split(":")[0])
    except ValueError:
        return 0.0


def preseason_model(aid: str, team: str, market_key_: str, line: float, game_day: str) -> tuple[float, list[str], float] | None:
    """An NBA preseason prop is a minutes question. Tonight's minutes: his recent preseason minutes (recency weighted),
    10% fewer on the second night of a back-to-back. Production per minute: his preseason rate, steadied with his
    regular-season rate (100 minutes of prior). Spread: gamma-Poisson with the minutes' own uncertainty.
    Returns (P(over), reasons, projected mean) like the matchup models, or None under 3 preseason games."""
    from .context import nb_over
    cur = espn_team("NBA", team)
    pre = nba_log(aid, "Preseason")
    same = [g for g in pre if g["team"] == cur]
    pre = same if len(same) >= 3 else pre
    games = [g for g in pre if _minutes(g) > 0 and nba_value(g["s"], market_key_) is not None][:10]
    if len(games) < 3:
        return None
    mins = [_minutes(g) for g in games]
    w = [0.5 ** (i / 3) for i in range(len(mins))]
    proj_min = sum(a * b for a, b in zip(w, mins)) / sum(w)
    # ESPN game logs carry the local game date (midnight UTC), not a start time: compare it as written
    b2b = games[0].get("date") == (dt.date.fromisoformat(game_day) - dt.timedelta(days=1)).isoformat()
    if b2b:
        proj_min *= PRESEASON_B2B
    pre_num, pre_min = sum(nba_value(g["s"], market_key_) for g in games), sum(mins)
    reg = [g for g in nba_log(aid) if g["team"] == cur and _minutes(g) > 0][:30]
    reg_vals = [(nba_value(g["s"], market_key_), _minutes(g)) for g in reg]
    reg_vals = [(v, m) for v, m in reg_vals if v is not None]
    reg_rate = sum(v for v, _ in reg_vals) / sum(m for _, m in reg_vals) if reg_vals else pre_num / pre_min
    rate = (pre_num + 100 * reg_rate) / (pre_min + 100)
    mean = rate * proj_min
    mean_m = sum(mins) / len(mins)
    min_sd = max(3.0, math.sqrt(sum((m - mean_m) ** 2 for m in mins) / len(mins)))
    cv = math.sqrt(0.12 ** 2 + (min_sd / proj_min) ** 2)
    p = min(0.98, max(0.02, nb_over(mean, line, cv) if mean > 0 else 0.0))
    why = [f"preseason minutes model: {proj_min:.0f} min tonight (his last {len(mins)} preseason games: {', '.join(f'{m:.0f}' for m in mins[:6])})"
           + (" x0.9, second night of a back-to-back; if he sits, PrizePicks voids it" if b2b else ""),
           f"{rate:.2f} per minute (preseason {pre_num / pre_min:.2f}, regular season {reg_rate:.2f}) = {mean:.1f} projected"]
    return p, why, mean


def preseason_adj() -> dict:
    """Today's blend with the book's weight halved (preseason prices are soft), the total weight kept."""
    from .blend import load_adjustments
    import copy
    adj = copy.deepcopy(load_adjustments())
    b = adj["blend"]
    tot = b["w_model"] + b["w_market"] + b["w_hist"]
    b["w_market"] *= PRESEASON_MARKET_WEIGHT
    k = tot / (b["w_model"] + b["w_market"] + b["w_hist"])
    for key in ("w_model", "w_market", "w_hist"):
        b[key] *= k
    return adj


def nba_value(s: dict, market_key: str) -> float | None:
    tot = 0.0
    for c in NBA_COLS[market_key]:
        v = s.get(c)
        if v in (None, "", "-"):
            return None
        tot += float(str(v).split("-")[0])
    return tot


def recount_values(sport: str, market_key: str, team: str, pid: str, competition: str = "regular") -> list[float] | None:
    """Per-game values the scan's history used, newest first (up to 30); None when the market has no reader here.
    competition='preseason' (NBA) recounts his preseason games only."""
    if sport == "NHL":
        if market_key == "goalie_saves":                            # starts only: saves = shots against - goals against
            return [float((g["x"].get("shotsAgainst") or 0) - (g["x"].get("goalsAgainst") or 0))
                    for g in LW.nhl_log(pid) if g["x"].get("gamesStarted")][:30]
        if market_key in LW.NHL_BOX:                                # hits, blocked shots: from each game's box score
            log = LW.nhl_log(pid)[:30]
            return [v for v in LW.nhl_box_values(pid, market_key, log) if v is not None]
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
                out.append(sum(nfl_num(x) for x in v if x is not None))
        return out[:30]
    if sport == "NBA":
        if market_key not in NBA_COLS:
            return None
        cur = espn_team("NBA", team)                                # same team only: a new team is a new role (L5)
        if competition == "preseason":
            games = nba_log(pid, "Preseason")
            same = [g for g in games if g["team"] == cur]
            games = same if len(same) >= 5 else games              # few preseason games: every team's count
        else:
            games = [g for g in nba_log(pid) if g["team"] == cur]
        return [v for v in (nba_value(g["s"], market_key) for g in games) if v is not None][:30]
    return None


def card_games(sport: str, stat: str, team: str, player: str, aid: str | None = None, limit: int | None = 30,
               competition: str = "regular") -> list[dict]:
    """His games for one stat, newest first: {d: date, o: opponent, h: home?, v: value}. The same windows `history`
    counts (NBA: current team only; MLB batters: 3+ plate appearances; NHL saves: starts only); `limit=None` = every
    game the logs hold (this season and last), for head-to-head."""
    mk, out = market_key(sport, stat), []
    if sport == "NHL":
        try:
            pid = LW.nhl_player(NHL_API.get(team, team), player)
        except Exception:
            pid = None
        key = next((k for k, m in LW.NHL_STATS.values() if m == mk), None)
        log = LW.nhl_log(pid) if pid else []
        box = LW.nhl_box_values(pid, mk, log[:40 if limit is None else limit]) if mk in LW.NHL_BOX and pid else None
        for i, g in enumerate(log):
            x = g["x"]
            if box is not None:
                if i >= len(box):
                    break
                if box[i] is None:
                    continue
                v = box[i]
            elif mk == "goalie_saves":
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
        pre = competition == "preseason"
        for g in nba_log(aid, "Preseason" if pre else "Regular Season"):
            v = nba_value(g["s"], mk) if (g["team"] == cur or pre) else None
            if v is not None:
                out.append({"d": g["date"], "o": g.get("opp", ""), "h": g.get("home"), "v": v})
    elif sport == "NFL" and aid and mk in NFL_COLS:
        for g in LW.nfl_log(aid):
            v = [g["x"].get(c) for c in NFL_COLS[mk]]
            if not all(x is None for x in v):
                out.append({"d": g["date"], "o": g.get("opp", ""), "h": g.get("home"), "v": sum(nfl_num(x) for x in v if x is not None)})
    return out if limit is None else out[:limit]


def history(sport: str, stat: str, team: str, player: str, line: float, aid: str | None = None,
            competition: str = "regular") -> tuple[float | None, int, str | None]:
    """Share of his recent games on each side of the line (this season first, up to 30 games), and his league id."""
    mk = market_key(sport, stat)
    if sport in ("NBA", "NFL"):                                     # ESPN athlete id, from the ESPN roster
        if not aid:
            return None, 0, None
        vals, pid = recount_values(sport, mk, team, aid, competition) or [], aid
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


def role_scale(league: str, market_key_: str, pid: str | None) -> float | None:
    """His last 5 games' workload over his 30-game average (current season counted double), as `lowline` measures it
    (L5): pass attempts or touches (NFL), ice time (NHL skaters), plate appearances (MLB batters). None where the
    workload isn't read (NBA keeps same-team games only; goalies and pitchers have their own windows)."""
    if not pid or market_key_ in ("goalie_saves",) or market_key_ in PITCH_COLS:
        return None
    try:
        log = {"NFL": LW.nfl_log, "NHL": LW.nhl_log, "MLB": LW.mlb_log}.get(league, lambda _: [])(pid)[:30]
    except Exception:
        return None
    vols = [float(g.get("vol") or 0) for g in log]
    if len(vols) < 8 or not sum(vols):
        return None
    w = [2.0 if g.get("season") == log[0].get("season") else 1.0 for g in log]
    avg = sum(a * b for a, b in zip(w, vols)) / sum(w)
    return (sum(vols[:5]) / 5) / avg if avg else None


LINE_GAP_P = 0.70          # no book price: a PrizePicks standard line is the market's median, so 70%+ against it is news, not edge


def line_gate(conf: str, notes: list, odds_type: str | None, p: float, line: float, proj: float | None, side: str) -> str:
    """No book price on a PrizePicks standard line: the line itself is the market's 50/50 number (books' main lines top
    out near 57% for us). Reading 70%+ against it means the line knows what his log doesn't (a starter hurt, a new role,
    L5), so the prop is held at Low. Goblins and demons are set off the median on purpose and are not checked."""
    if odds_type != "standard" or p < LINE_GAP_P or conf not in ("High", "Medium"):
        return conf
    notes.append(f"line gap: PrizePicks set its standard line at {line:g}" + (f" against his log's {proj:g}" if proj is not None else "")
                 + f"; {p:.0%} on the {side} says the line knows something his log doesn't (role, injury, L5): Low")
    return "Low"


def role_gate(conf: str, notes: list, scale: float | None) -> str:
    """No book price + a workload 25%+ off his average: his history is a different role, so Low (L5). A prop already
    Low gets the note too: its number comes from the old role, so it is unknown, not a fade."""
    if scale is None or abs(scale - 1) <= LW.ROLE_SHIFT:
        return conf
    notes.append(f"role change: last 5 games' workload is {scale:.0%} of his average (L5): Low until a book prices the new role"
                 + ("" if conf in ("High", "Medium") else "; the number is from his old role, not a fade"))
    return "Low" if conf in ("High", "Medium") else conf


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
            for board_lg in ((lg, "NBAP") if lg == "NBA" else (lg,)):   # NBAP: PrizePicks' separate NBA preseason board
                props += [{**p, "league": lg, "pp_league": board_lg} for p in pp.board(board_lg, ("standard", "goblin", "demon"))
                          if market_key(lg, p["stat"])]
        except Exception as e:
            log(f"{lg}: board unavailable ({type(e).__name__})")
    log(f"{len(props)} PrizePicks props we can read from game logs ..." + ("" if oa_on else " (sportsbook prices: DraftKings via ESPN only; set $ODDS_API_KEY for every book)"))
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
    events, lad, rost, comps, by_day = {}, {}, {}, {}, {}
    for lg in leagues:
        for d in (day + dt.timedelta(days=i) for i in range(max(days, SLATE_DAYS.get(lg, 0)))):
            for e in scoreboard(lg, d):
                c = e["competitions"][0]
                if c["status"]["type"]["state"] != "pre":
                    continue
                teams = {t["team"]["abbreviation"]: t["team"] for t in c["competitors"]}
                for ab in teams:
                    events.setdefault((lg, ab), e["id"])           # tonight's game wins over tomorrow's
                    by_day[(lg, ab, slate_day(e.get("date")))] = e["id"]
                    comps[(lg, e["id"])] = {1: "preseason", 3: "postseason"}.get((e.get("season") or {}).get("type"), "regular")
    games = sorted(set((k[0], v) for k, v in events.items()))
    with cf.ThreadPoolExecutor(6) as ex:
        for key, l in zip(games, ex.map(lambda kv: ladders(*kv), games)):
            lad[key] = l

    def one(p):
        lg = p["league"]
        # a prop belongs to the game on its own date: PrizePicks lists next week's opener beside tonight's preseason game
        d = slate_day(p.get("start")) if p.get("start") else None
        eid = (by_day.get((lg, p["team"], d)) or by_day.get((lg, espn_team(lg, p["team"]), d))) if d else \
            (events.get((lg, p["team"])) or events.get((lg, espn_team(lg, p["team"]))))
        if not eid:
            return {**p, "error": "game not in this scan's window or started"}
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
        if mk_over is None and lad_p:                               # fallback: DraftKings ladder through ESPN
            mk_over, mnote = market_over(lad_p, p["line"])
        parts = [lad.get((lg, eid), {}).get((STATS[lg][x][0], aid or "")) for x in COMBO_PARTS.get(lg, {}).get(mk, ())]
        if mk_over is None and parts and all(parts):                # no combo ladder: the parts' ladders combined
            mk_over = combo_over(parts, p["line"])
            mnote = f"DraftKings {' + '.join(COMBO_PARTS[lg][mk]).lower()} ladders combined: {mk_over:.3f} over"
        comp = comps.get((lg, eid), "regular") if lg == "NBA" else "regular"
        if mk_over is None:                                         # no book prices it: graded from his games, no market gate
            mnote = f"{mnote or ('no DraftKings ladder' if p['stat'] in STATS.get(lg, {}) else 'no sportsbook line')}: no book price"
        h_over, n, pid = history(lg, p["stat"], p["team"], p["player"], p["line"], aid, comp)
        # context (matchup, ice time, strikeout rates) is the model component on regular lines; goblins keep market + history.
        # With no book price the model is always used, and the game-log model stands in where there is no matchup model.
        # An NBA preseason game is a minutes question: the preseason minutes model on every line type, the book at half weight.
        if comp == "preseason":
            cx = preseason_model(aid, p["team"], mk, p["line"], slate_day(p.get("start"))) if aid else None
            mnote += f"; preseason: history from his preseason games only (L26), {n} games"
        else:
            cx = CX.price(lg, p["stat"], p.get("opp"), pid, p["line"], day.year)
        priced = mk_over is not None
        lm = None if priced or cx else CX.log_model(_LAST_VALS.get((lg, p["stat"], p["team"], p["player"], p["line"])) or [], p["line"])
        model = cx if cx and (p.get("odds_type") == "standard" or not priced or comp == "preseason") else lm
        avg10 = recent_avg(lg, p["stat"], p["team"], p["player"], p["line"])
        proj, proj_src = projection(cx, lad_p, main, avg10)
        if lm and not cx:
            proj, proj_src = round(lm[2], 1), "game-log model"
        if comp == "preseason" and cx:
            proj_src = "preseason minutes model"
        shift = None if priced else role_scale(lg, mk, pid)
        adj_c = preseason_adj() if comp == "preseason" else None
        best = None
        for side in (["over"] if p["over_only"] else ["over", "under"]):
            pk = None if not priced else mk_over if side == "over" else 1 - mk_over
            ph = None if h_over is None else (h_over if side == "over" else 1 - h_over)
            pmod = (model[0] if side == "over" else 1 - model[0]) if model else None
            seg = f"{lg.lower()}:{mk}:{side}"
            if pmod is None and pk is None and ph is None:
                continue
            e = final_probability(pmod, pk, ph, seg, n, adj_c)
            if adj_c and pk is not None:
                e.notes.append("preseason book price weighted half: preseason props are set off regular-season rates")
            e.confidence = role_gate(e.confidence, e.notes, shift)
            if not priced:
                e.confidence = line_gate(e.confidence, e.notes, p.get("odds_type"), e.p, p["line"], proj, side)
            rt = rating(e.p, e.confidence, pk)
            note = OA.describe(cons, side) if cons else mnote
            if cons and cons["disagree"] and rt >= 8:               # books more than 10 points apart: not an 80% read
                rt, note = 7, note + " (held at 7)"
            r = {**p, "side": side, "market_key": mk, "p_market": pk, "p_hist": ph, "hist_n": n, "p_final": e.p, "p_model": pmod,
                 "confidence": e.confidence, "rating": rt, "player_id": pid, "event_id": eid, "context": model[1] if model else [],
                 "competition": comp,
                 "proj": proj, "proj_src": proj_src, "avg10": avg10, "rungs": lad_p or {},
                 "notes": f"{note}; " + "; ".join(e.notes) + (f"; context: {' / '.join(model[1])}" if model else "")}
            if best is None or r["p_final"] > best["p_final"]:
                best = r
        if not best:
            return {**p, "error": "no games in his log for this stat"}
        # what the numbers can't see (L31): tonight's report, the spread, weather, goalies, a back-to-back, his latest note
        from . import situation as SI
        sit = SI.check(lg, eid, p["team"], p["player"], aid, mk, best["side"], slate_day(p.get("start")),
                       read_news=best["rating"] >= 6)
        if sit.worst == "OUT":
            return {**p, "error": "not playable tonight: " + "; ".join(t for lv, t in sit.flags if lv == "OUT")}
        conf = sit.apply(best["confidence"])
        if conf != best["confidence"]:
            best["confidence"] = conf
            best["rating"] = min(best["rating"], rating(best["p_final"], conf, best["p_market"]))
        best["context"] = list(best["context"]) + [t for lv, t in sit.flags if lv != "INFO"][:3]
        best["circumstances"] = sit.flags
        best["notes"] += "".join("; " + n for n in sit.notes())
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
                rr["rungs"] = rr.get("rungs") or {}
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
# ESPN / PrizePicks abbreviations -> the league's own API (NHL api-web, MLB statsapi)
API_ABBR = {"NHL": {"NJ": "NJD", "SJ": "SJS", "TB": "TBL", "LA": "LAK", "UTAH": "UTA", "MON": "MTL"},
            "MLB": {"CHW": "CWS", "ARI": "AZ", "OAK": "ATH", "LA": "LAD", "WAS": "WSH"}}


def slate_day(start: str | None) -> str:
    """The US date a game is listed under. ESPN gives UTC ('2026-10-16T00:00Z' is the 8 PM ET game on the 15th), so a
    zoned start time is read in New York time before the date is taken."""
    if not start:
        return dt.date.today().isoformat()
    try:
        t = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
    except ValueError:
        return start[:10]
    if t.tzinfo is None:
        return t.date().isoformat()
    from zoneinfo import ZoneInfo
    return t.astimezone(ZoneInfo("America/New_York")).date().isoformat()


def grade_id(r: dict) -> str:
    """The id our graders want: NHL gameId (api-web), MLB gamePk (statsapi); NBA grades on ESPN's own event id."""
    if r["league"] in ("NBA", "NFL"):
        return str(r["event_id"])
    day = slate_day(r.get("start"))
    key = (r["league"], r["team"], day)
    if key not in _PK:
        _PK[key] = ""
        names = {r["team"], API_ABBR.get(r["league"], {}).get(r["team"], r["team"])}   # ESPN's "NJ" is the NHL's "NJD"
        try:
            if r["league"] == "MLB":
                for d in _get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={day}&hydrate=team")["dates"]:
                    for g in d["games"]:
                        if names & {g["teams"]["away"]["team"].get("abbreviation"), g["teams"]["home"]["team"].get("abbreviation")}:
                            _PK[key] = str(g["gamePk"])
            else:
                for wk in _get(f"https://api-web.nhle.com/v1/schedule/{day}").get("gameWeek", [])[:1]:
                    for g in wk["games"]:
                        if names & {g["awayTeam"]["abbrev"], g["homeTeam"]["abbrev"]}:
                            _PK[key] = str(g["id"])
        except Exception:
            pass
    return _PK[key]


def _espn_event(league: str, team: str, day: str) -> str:
    """ESPN's event id for a team's game on a slate day (NFL and NBA grade on it)."""
    team = espn_team(league, team)
    key = (league, team, day, "espn")
    if key not in _PK:
        _PK[key] = ""
        try:
            sb = _get(f"https://site.api.espn.com/apis/site/v2/sports/{SPORT[league][0]}/scoreboard?dates={day.replace('-', '')}")
            for e in sb.get("events") or []:
                abbrs = {c["team"].get("abbreviation") for c in e["competitions"][0]["competitors"]}
                if team in abbrs and slate_day(e.get("date")) == day:
                    _PK[key] = str(e["id"])
        except Exception:
            pass
    return _PK[key]


def backfill_ids(rows: list[dict]) -> int:
    """Give pending rows logged without a game id (edge lowline, a failed schedule lookup) the id their grader wants,
    from the team in `event` ("DAL vs COL"), the ESPN id in `group` and the start time in the notes. Returns how many."""
    n = 0
    for r in rows:
        lg = (r.get("sport") or "").upper()
        if r.get("event_id") or r.get("status") != "pending" or lg not in ("MLB", "NHL", "NFL", "NBA"):
            continue
        m = re.search(r"start (\S+)", r.get("notes", ""))
        team = (r.get("event") or "").split(" vs ")[0].split(" @ ")[0].strip().upper()
        if not m or not team:
            continue
        g = (r.get("group") or "").split(":")[-1]
        if lg in ("NFL", "NBA"):
            eid = g if g.isdigit() else _espn_event(lg, team, slate_day(m.group(1)))
        else:
            eid = grade_id({"league": lg, "team": team, "start": m.group(1)})
        if eid:
            r["event_id"] = eid
            n += 1
    return n


# ------------------------------------------------------------------ one prop, priced on request (user asks, injected slips)
STAT_ALIASES = {
    "MLB": [("hits+runs+rbis", "Hits+Runs+RBIs"), ("h+r+rbi", "Hits+Runs+RBIs"), ("hrr", "Hits+Runs+RBIs"),
            ("hits allowed", "Hits Allowed"), ("earned runs", "Earned Runs Allowed"), ("walks allowed", "Walks Allowed"),
            ("pitching outs", "Pitching Outs"), ("outs", "Pitching Outs"), ("total bases", "Total Bases"), ("tb", "Total Bases"),
            ("home runs", "Home Runs"), ("homer", "Home Runs"), ("singles", "Singles"), ("doubles", "Doubles"),
            ("stolen bases", "Stolen Bases"), ("rbi", "RBIs"), ("runs", "Runs"), ("walks", "Walks"),
            ("hitter strikeouts", "Hitter Strikeouts"), ("batter strikeouts", "Hitter Strikeouts"),
            ("pitcher strikeouts", "Pitcher Strikeouts"), ("strikeouts thrown", "Pitcher Strikeouts"),
            ("strikeouts", "Strikeouts"), ("ks", "Strikeouts"), ("hits", "Hits")],
    "NHL": [("shots on goal", "Shots On Goal"), ("sog", "Shots On Goal"), ("goalie saves", "Goalie Saves"), ("saves", "Goalie Saves"),
            ("blocked shots", "Blocked Shots"), ("blocks", "Blocked Shots"), ("power play points", "Power Play Points"),
            ("ppp", "Power Play Points"), ("points", "Points"), ("assists", "Assists"), ("goals", "Goals"), ("shots", "Shots On Goal"),
            ("hits", "Hits")],
    "NBA": [("pts+rebs+asts", "Pts+Rebs+Asts"), ("pra", "Pts+Rebs+Asts"), ("pts+rebs", "Pts+Rebs"), ("pts+asts", "Pts+Asts"),
            ("rebs+asts", "Rebs+Asts"), ("blks+stls", "Blks+Stls"), ("3-pt made", "3-PT Made"), ("3pt", "3-PT Made"),
            ("3pm", "3-PT Made"), ("threes", "3-PT Made"), ("three", "3-PT Made"), ("rebounds", "Rebounds"), ("reb", "Rebounds"),
            ("assists", "Assists"), ("ast", "Assists"), ("steals", "Steals"), ("blocked shots", "Blocked Shots"),
            ("blocks", "Blocked Shots"), ("turnovers", "Turnovers"), ("points", "Points"), ("pts", "Points")],
    "NFL": [("pass+rush yds", "Pass+Rush Yds"), ("pass+rush yards", "Pass+Rush Yds"), ("rush+rec yds", "Rush+Rec Yds"),
            ("rush+rec yards", "Rush+Rec Yds"), ("rush+rec tds", "Rush+Rec TDs"), ("anytime tds", "Rush+Rec TDs"),
            ("anytime td", "Rush+Rec TDs"), ("anytime touchdown", "Rush+Rec TDs"), ("pass yards", "Pass Yards"),
            ("passing yards", "Pass Yards"), ("pass yds", "Pass Yards"), ("pass tds", "Pass TDs"), ("passing tds", "Pass TDs"),
            ("passing touchdowns", "Pass TDs"), ("pass attempts", "Pass Attempts"), ("pass completions", "Pass Completions"),
            ("completions", "Pass Completions"), ("interceptions", "INT"), ("int", "INT"), ("rush yards", "Rush Yards"),
            ("rushing yards", "Rush Yards"), ("rush yds", "Rush Yards"), ("rush attempts", "Rush Attempts"), ("carries", "Rush Attempts"),
            ("rec yards", "Receiving Yards"), ("receiving yards", "Receiving Yards"), ("yards receiving", "Receiving Yards"),
            ("rec yds", "Receiving Yards"), ("yards rushing", "Rush Yards"), ("yards passing", "Pass Yards"),
            ("longest reception", "Longest Reception"), ("receptions", "Receptions"), ("recs", "Receptions"),
            ("fg made", "FG Made"), ("field goals made", "FG Made"), ("kicking points", "Kicking Points"),
            ("rushing attempts", "Rush Attempts"), ("passing attempts", "Pass Attempts"), ("passing completions", "Pass Completions"),
            ("receiving", "Receiving Yards"), ("rushing", "Rush Yards"), ("passing", "Pass Yards")],     # '70+ Receiving' = yards
}


def canon_stat(league: str, text: str) -> str | None:
    """A stat as an app or a screenshot writes it ('H+R+RBI', 'SOG', 'Pts+Rebs+Asts') -> our PrizePicks stat name."""
    t = re.sub(r"\s+", " ", (text or "").lower().replace("hits + runs + rbis", "hits+runs+rbis").replace(" + ", "+")).strip()
    for alias, stat in STAT_ALIASES.get(league, []):
        if re.search(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", t):
            return stat
    return None


_SUFFIX = {"jr", "sr", "ii", "iii", "iv", "v"}


def name_key(name: str) -> tuple[str, str]:
    """(first initial, surname) so 'S. Gilgeous-Alexander' finds 'Shai Gilgeous-Alexander' and 'K. Walker' finds
    'Kenneth Walker III'."""
    t = [w for w in re.findall(r"[a-z]+", unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower())]
    while len(t) > 1 and t[-1] in _SUFFIX:
        t.pop()
    return (t[0][:1], "".join(t[1:])) if len(t) > 1 else ("", "".join(t))


def find_player(league: str, player: str, day: dt.date | None = None, days: int = 2) -> dict | None:
    """The player's next game that hasn't started: ESPN event id, his ESPN id, team and opponent."""
    day = day or dt.date.today()
    loose = None
    for d in (day + dt.timedelta(days=i) for i in range(days)):
        for e in scoreboard(league, d):
            c = e["competitions"][0]
            if c["status"]["type"]["state"] != "pre":
                continue
            teams = [t["team"]["abbreviation"] for t in c["competitors"]]
            for ab in teams:
                try:
                    names = roster_names(league, ab)
                except Exception:
                    continue
                for nm, aid in names:
                    m = name_match(player, nm)
                    if not m:
                        continue
                    hit = {"event_id": e["id"], "aid": aid, "name": nm, "team": ab,
                           "competition": {1: "preseason", 3: "postseason"}.get((e.get("season") or {}).get("type"), "regular"),
                           "opp": next(t for t in teams if t != ab), "start": e.get("date", "")}
                    if m == 2:
                        return hit
                    loose = loose or hit
    return loose


def name_match(given: str, roster: str) -> int:
    """2 = the same full name; 1 = an abbreviated or shortened first name with the same surname ('S. Gilgeous-Alexander',
    'Ken Walker'); 0 = no match. 'Jalen Brooks' never matches 'Jonathon Brooks': a spelled-out first name must agree."""
    if LW._fold(given) == LW._fold(roster):
        return 2
    a, b = name_key(given), name_key(roster)
    if not a[1] or a != b:
        return 0
    g = re.findall(r"[a-z]+", unicodedata.normalize("NFKD", given).encode("ascii", "ignore").decode().lower())
    r = re.findall(r"[a-z]+", unicodedata.normalize("NFKD", roster).encode("ascii", "ignore").decode().lower())
    return 1 if len(g[0]) == 1 or r[0].startswith(g[0]) or g[0].startswith(r[0]) else 0


def log_rows(rows: list[dict], min_rating: int = 1) -> list[str]:
    """Log scan or price_prop rows to bets.csv (demons and rows under min_rating skipped, logged rows skipped); new ids."""
    from . import learn as L
    bets = L.read_bets()
    seen = {(b["event_id"], b["player"].lower(), b["market"], str(float(b["line"])) if b["line"] else "", b["side"]) for b in bets}
    nid = max(int(b["id"]) for b in bets if b["id"].isdigit()) + 1
    new = []
    for r in rows:
        if r["odds_type"] == "demon" or r["rating"] < min_rating:
            continue
        gid = grade_id(r)                                           # the id stored below (MLB gamePk / NHL gameId), not ESPN's
        k = (str(gid), r["player"].lower(), r["market_key"], str(float(r["line"])), r["side"])
        if k in seen:
            continue
        seen.add(k)
        bets.append({"id": str(nid), "date": dt.date.today().isoformat(), "sport": r["league"].lower(),
                     "event": f"{r['team']} vs {r['opp']}", "event_id": gid,
                     "player": r["player"], "player_id": r["player_id"] or "", "market": r["market_key"], "line": r["line"],
                     "side": r["side"], "book": f"PrizePicks {r['odds_type']}", "p_model": "" if r.get("p_model") is None else round(r["p_model"], 4),
                     "p_market": "" if r["p_market"] is None else round(r["p_market"], 4),
                     "p_hist": "" if r["p_hist"] is None else round(r["p_hist"], 4), "hist_n": r["hist_n"], "p_final": round(r["p_final"], 4),
                     "confidence": r["confidence"], "action": "lean" if r["rating"] >= 8 else "pass",
                     "segment": f"{r['league'].lower()}:{r['market_key']}:{r['side']}", "group": f"{r['league'].lower()}:{r['event_id']}",
                     "status": "pending", "proj": "" if r.get("proj") is None else r["proj"],
                     "notes": f"edge tier; {r['notes']}; start {r.get('start')}"})
        new.append(str(nid))
        nid += 1
    L.write_bets(bets)
    return new


def price_prop(league: str, player: str, stat_text: str, line: float, side: str | None, odds_type: str = "standard",
               day: dt.date | None = None) -> dict:
    """Price one prop the way the scan does: DraftKings ladder at the line, game log at the line, the matchup model on
    regular lines, blended, calibrated, rated. No book price is not a stop: the game-log model and his history grade it.
    No side (a board or a post where nothing is picked): both sides are graded and the better one returned.
    Returns an error key when it can't be priced."""
    from . import context as CX
    _memo()
    league = league.upper()
    sd = {"more": "over", "less": "under", "over": "over", "under": "under", "higher": "over", "lower": "under"}.get((side or "").lower())
    if league not in SPORT or line is None:
        return {"error": f"can't price {league} {stat_text}: no pricer for this league or no line"}
    if sd is None:
        both = [price_prop(league, player, stat_text, line, x, odds_type, day) for x in ("over", "under")]
        ok = [b for b in both if "error" not in b]
        if not ok:
            return both[0]
        best = max(ok, key=lambda b: (b["rating"], b["p_final"]))
        other = next((b for b in ok if b is not best), None)
        return {**best, "notes": f"no side picked: graded both, {best['side']} is the better side"
                + (f" (the {other['side']} is {other['rating']}/10, {other['p_final']:.3f})" if other else "") + "; " + best["notes"]}
    side = sd
    g = find_player(league, player, day, days=max(2, SLATE_DAYS.get(league, 0)))
    if not g:
        return {"error": f"{player}: no upcoming {league} game found"}
    stat = canon_stat(league, stat_text)
    if stat == "Strikeouts":                                         # pitcher or hitter: whoever has starts
        stat = "Pitcher Strikeouts" if (LW.mlb_player(g["team"], g["name"]) and mlb_pitch_log(LW.mlb_player(g["team"], g["name"]))) else "Hitter Strikeouts"
    mk = market_key(league, stat) if stat else None
    if not mk:
        return {"error": f"{stat_text}: stat not priced for {league}", **g}
    lad_all = ladders(league, g["event_id"])
    rungs = lad_all.get((STATS[league][stat][0], g["aid"]), {}) if stat in STATS.get(league, {}) else {}
    mk_over, mnote = market_over(rungs, line) if rungs else (None, "no DraftKings ladder")
    parts = [lad_all.get((STATS[league][x][0], g["aid"])) for x in COMBO_PARTS.get(league, {}).get(mk, ())]
    if mk_over is None and parts and all(parts):                   # no combo ladder: build it from the parts'
        mk_over = combo_over(parts, line)
        mnote = f"DraftKings {' + '.join(COMBO_PARTS[league][mk]).lower()} ladders combined: {mk_over:.3f} over"
    comp = g.get("competition", "regular") if league == "NBA" else "regular"     # NBA logs split by competition
    if mk_over is None:
        mnote = f"{mnote}: no book price"
    h_over, n, pid = history(league, stat, g["team"], g["name"], line, g["aid"], comp)
    if comp != "regular":
        mnote += f"; {comp}: history from his {comp} games only (L26), {n} games"
    cx = CX.price(league, stat, g["opp"], pid, line, (day or dt.date.today()).year) if comp == "regular" else None
    if comp == "preseason":                                         # a minutes question, on any line type
        cx = preseason_model(g["aid"], g["team"], mk, line, slate_day(g.get("start")))
    lm = None if mk_over is not None or cx else CX.log_model(_LAST_VALS.get((league, stat, g["team"], g["name"], line)) or [], line)
    model = cx if cx and (odds_type == "standard" or mk_over is None or comp == "preseason") else lm
    pk = None if mk_over is None else (mk_over if side == "over" else 1 - mk_over)
    ph = None if h_over is None else (h_over if side == "over" else 1 - h_over)
    pmod = None if not model else (model[0] if side == "over" else 1 - model[0])
    if pk is None and ph is None and pmod is None:
        return {"error": f"{g['name']}: no {stat} games in his log", **g}
    e = final_probability(pmod, pk, ph, f"{league.lower()}:{mk}:{side}", n, preseason_adj() if comp == "preseason" else None)
    if comp == "preseason" and pk is not None:
        e.notes.append("preseason book price weighted half: preseason props are set off regular-season rates")
    avg10 = recent_avg(league, stat, g["team"], g["name"], line)
    proj, src = projection(cx, rungs, None, avg10)
    if comp == "preseason" and cx:
        src = "preseason minutes model"
    if lm and not cx:
        proj, src = round(lm[2], 1), "game-log model"
    if pk is None:
        e.confidence = role_gate(e.confidence, e.notes, role_scale(league, mk, pid))
        e.confidence = line_gate(e.confidence, e.notes, odds_type, e.p, line, proj, side)
    from . import situation as SI                                   # what the numbers can't see (L31)
    sit = SI.check(league, g["event_id"], g["team"], g["name"], g["aid"], mk, side, slate_day(g.get("start")))
    if sit.worst == "OUT":
        return {"error": f"{g['name']}: not playable tonight ({'; '.join(t for lv, t in sit.flags if lv == 'OUT')})", **g}
    e.confidence = sit.apply(e.confidence)
    e.notes.extend(sit.notes())
    return {**g, "league": league, "player": g["name"], "stat": stat, "market_key": mk, "line": line, "side": side,
            "odds_type": odds_type, "p_market": pk, "p_hist": ph, "hist_n": n, "p_model": pmod, "p_final": e.p,
            "confidence": e.confidence, "rating": rating(e.p, e.confidence, pk), "player_id": pid, "proj": proj, "proj_src": src,
            "context": (model[1] if model else []) + [t for lv, t in sit.flags if lv != "INFO"][:3], "competition": comp,
            "circumstances": sit.flags,
            "notes": "; ".join([mnote] + e.notes + ([f"context: {' / '.join(model[1])}"] if model else []))}
