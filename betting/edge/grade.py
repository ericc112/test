"""Auto-grade pending bets from official/free stat feeds (MLB Stats API, NHL API, ESPN, bo3.gg, gol.gg)."""
from __future__ import annotations

import json
import os
import ssl
import time
import unicodedata
import urllib.error
import urllib.request

_CA = "/root/.ccr/ca-bundle.crt"
_CTX = ssl.create_default_context(cafile=_CA) if os.path.exists(_CA) else ssl.create_default_context()


def _get(url: str, tries: int = 3):
    """JSON from a feed. A dropped connection (SSL EOF, reset, timeout) is retried; an HTTP error is not."""
    for i in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, context=_CTX, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ConnectionError, TimeoutError, ssl.SSLError):
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def _norm(s) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


# ------------------------------------------------------------------ MLB (event_id = gamePk, player_id = MLBAM id)
MLB_STATS = {
    "pitcher_strikeouts": ("pitching", lambda s: s.get("strikeOuts")),
    "pitcher_outs": ("pitching", lambda s: s.get("outs")),
    "pitcher_hits_allowed": ("pitching", lambda s: s.get("hits")),
    "pitcher_earned_runs": ("pitching", lambda s: s.get("earnedRuns")),
    "pitcher_walks": ("pitching", lambda s: s.get("baseOnBalls")),
    "pitcher_pitches": ("pitching", lambda s: s.get("numberOfPitches")),
    "pitcher_bf": ("pitching", lambda s: s.get("battersFaced")),
    "batter_hits": ("batting", lambda s: s.get("hits")),
    "batter_walks": ("batting", lambda s: s.get("baseOnBalls")),
    "batter_strikeouts": ("batting", lambda s: s.get("strikeOuts")),
    "batter_total_bases": ("batting", lambda s: s.get("totalBases")),
    "batter_home_runs": ("batting", lambda s: s.get("homeRuns")),
    "batter_singles": ("batting", lambda s: None if s.get("hits") is None else s["hits"] - s.get("doubles", 0) - s.get("triples", 0) - s.get("homeRuns", 0)),
    "batter_hrr": ("batting", lambda s: None if s.get("hits") is None else s["hits"] + s.get("runs", 0) + s.get("rbi", 0)),
    # PrizePicks hitter fantasy score: 1B 3, 2B 5, 3B 8, HR 10, R 2, RBI 2, BB 2, HBP 2, SB 5
    "batter_fs_pp": ("batting", lambda s: None if s.get("hits") is None else
                     3 * (s["hits"] - s.get("doubles", 0) - s.get("triples", 0) - s.get("homeRuns", 0)) + 5 * s.get("doubles", 0)
                     + 8 * s.get("triples", 0) + 10 * s.get("homeRuns", 0) + 2 * (s.get("runs", 0) + s.get("rbi", 0) + s.get("baseOnBalls", 0)
                     + s.get("hitByPitch", 0)) + 5 * s.get("stolenBases", 0)),
}


def mlb_value(event_id: str, player_id: str, market: str, cache: dict, live: bool = False):
    key = ("mlb", event_id)
    if key not in cache:
        sched = _get(f"https://statsapi.mlb.com/api/v1/schedule?gamePk={event_id}")
        game = sched["dates"][0]["games"][0]
        cache[key] = {"final": game["status"]["abstractGameState"] == "Final",
                      "box": _get(f"https://statsapi.mlb.com/api/v1/game/{event_id}/boxscore")}
    c = cache[key]
    if not c["final"] and not live:                      # live: the box score so far (edge live)
        return "pending", None
    if market == "first_inning_pitches":
        pbp = _get(f"https://statsapi.mlb.com/api/v1/game/{event_id}/playByPlay")
        n = sum(sum(1 for e in p["playEvents"] if e.get("isPitch")) for p in pbp["allPlays"]
                if p["about"]["inning"] == 1 and str(p["matchup"]["pitcher"]["id"]) == str(player_id))
        return ("final", n) if n else ("void", None)
    group, fn = MLB_STATS[market]
    for side in ("home", "away"):
        pl = c["box"]["teams"][side]["players"].get(f"ID{player_id}")
        if pl:
            stats = pl.get("stats", {}).get(group) or {}
            v = fn(stats) if stats else None
            return ("final", v) if v is not None else ("void", None)
    return "void", None


# ------------------------------------------------------------------ NHL (event_id = gameId, player_id = NHL id)
NHL_STATS = {"skater_sog": "sog", "skater_points": "points", "skater_goals": "goals", "skater_assists": "assists", "goalie_saves": "saves",
             "skater_hits": "hits", "skater_toi": "toi", "skater_blocks": "blockedShots"}


def _nhl_num(v):
    """Box-score values: plain numbers, or 'mm:ss' for time on ice (returned in minutes)."""
    if isinstance(v, str) and ":" in v:
        m, s = v.split(":")
        return round(int(m) + int(s) / 60, 2)
    return v


def nhl_value(event_id: str, player_id: str, market: str, cache: dict, live: bool = False):
    key = ("nhl", event_id)
    if key not in cache:
        cache[key] = _get(f"https://api-web.nhle.com/v1/gamecenter/{event_id}/boxscore")
    b = cache[key]
    if b.get("gameState") not in ("OFF", "FINAL") and not live:
        return "pending", None
    for side in ("homeTeam", "awayTeam"):
        for grp in ("forwards", "defense", "goalies"):
            for p in (b.get("playerByGameStats") or {}).get(side, {}).get(grp, []):
                if str(p["playerId"]) == str(player_id):
                    return "final", _nhl_num(p.get(NHL_STATS[market]))
    return "void", None


# ------------------------------------------------------------------ NFL (event_id = ESPN event, player_id = ESPN athlete id)
NFL_STATS = {
    "pass_yds": ("passing", "YDS"), "rush_yds": ("rushing", "YDS"), "rush_att": ("rushing", "CAR"),
    "rec_yds": ("receiving", "YDS"), "receptions": ("receiving", "REC"), "pass_tds": ("passing", "TD"),
    "pass_int": ("passing", "INT"), "longest_rec": ("receiving", "LONG"), "pass_cmp": ("passing", "C/ATT"),
    "fg_made": ("kicking", "FG"), "kicking_pts": ("kicking", "PTS"),
}


def nfl_value(event_id: str, player_id: str, market: str, cache: dict, league: str = "nfl", live: bool = False):
    key = (league, event_id)
    if key not in cache:
        cache[key] = _get(f"https://site.api.espn.com/apis/site/v2/sports/football/{league}/summary?event={event_id}")
    s = cache[key]
    if s["header"]["competitions"][0]["status"]["type"]["name"] != "STATUS_FINAL" and not live:
        return "pending", None

    def stat(cat_name, label):
        for team in s["boxscore"].get("players", []):
            for cat in team["statistics"]:
                if cat["name"] != cat_name:
                    continue
                for a in cat["athletes"]:
                    if str(a["athlete"]["id"]) == str(player_id):
                        v = a["stats"][cat["labels"].index(label)]
                        return float(str(v).split("/")[0].replace(",", ""))
        return None

    if market == "anytime_td":
        tds = [stat("rushing", "TD"), stat("receiving", "TD")]
        if all(t is None for t in tds):
            return "void", None
        return "final", sum(t or 0 for t in tds)
    if market == "rush_rec_yds":
        yds = [stat("rushing", "YDS"), stat("receiving", "YDS")]
        if all(y is None for y in yds):
            return "void", None
        return "final", sum(y or 0 for y in yds)
    if market == "pass_rush_yds":
        yds = [stat("passing", "YDS"), stat("rushing", "YDS")]
        if all(y is None for y in yds):
            return "void", None
        return "final", sum(y or 0 for y in yds)
    if market == "pass_att":
        for team in s["boxscore"].get("players", []):
            for cat in team["statistics"]:
                if cat["name"] == "passing":
                    for a in cat["athletes"]:
                        if str(a["athlete"]["id"]) == str(player_id):
                            return "final", float(a["stats"][0].split("/")[1])
        return "void", None
    v = stat(*NFL_STATS[market])
    return ("final", v) if v is not None else ("void", None)


# ------------------------------------------------------------------ NBA (event_id = ESPN event, player_id = ESPN athlete id)
NBA_STATS = {"points": ("points",), "rebounds": ("rebounds",), "assists": ("assists",), "pra": ("points", "rebounds", "assists"),
             "pts_asts": ("points", "assists"), "pts_rebs": ("points", "rebounds"), "rebs_asts": ("rebounds", "assists"),
             "threes": ("threePointFieldGoalsMade-threePointFieldGoalsAttempted",), "steals": ("steals",), "blocks": ("blocks",),
             "turnovers": ("turnovers",), "blks_stls": ("blocks", "steals")}


def nba_value(event_id: str, player_id: str, market: str, cache: dict, live: bool = False):
    key = ("nba", event_id)
    if key not in cache:
        cache[key] = _get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}")
    s = cache[key]
    if s["header"]["competitions"][0]["status"]["type"]["name"] != "STATUS_FINAL" and not live:
        return "pending", None
    for team in s.get("boxscore", {}).get("players", []):
        for blk in team["statistics"]:
            for a in blk["athletes"]:
                if str(a["athlete"]["id"]) != str(player_id):
                    continue
                if a.get("didNotPlay") or not a.get("stats"):
                    return "void", None                            # DNP: the apps remove the leg
                st = dict(zip(blk["keys"], a["stats"]))
                return "final", sum(float(str(st[k]).split("-")[0]) for k in NBA_STATS[market])
    return "void", None


# ------------------------------------------------------------------ CS2 (event_id = bo3.gg match id, player_id = nickname)
def cs2_value(event_id: str, player_id: str, market: str, cache: dict):
    from . import cs2
    key = ("cs2", event_id)
    if key not in cache:
        games = _get(f"https://api.bo3.gg/api/v1/games?filter%5Bgames.match_id%5D%5Beq%5D={event_id}")["results"]
        cache[key] = sorted(games, key=lambda g: g.get("number") or 0)
    games = cache[key]
    need = 1 if market.endswith("_m1") else 2                     # cs_kills_m12 = maps 1-2, cs_kills_m1 = map 1
    m12 = [g for g in games if g.get("number") in range(1, need + 1)]
    if len(m12) < need or any(g.get("status") != "finished" for g in m12):
        return "pending", None
    field = "kills" if market.startswith("cs_kills") else "headshots"
    total, seen = 0, 0
    for g in m12:
        stats = _get(f"https://api.bo3.gg/api/v1/games/{g['id']}/players_stats")
        if not stats:  # map finished but demo not parsed yet: wait, don't void
            return "pending", None
        for p in stats:
            nick = ((p.get("steam_profile") or {}).get("player") or {}).get("nickname") or (p.get("steam_profile") or {}).get("nickname")
            if cs2.norm(nick) == cs2.norm(player_id):   # 'dev1ce' on the server is 'device' on the board
                total += p[field]
                seen += 1
    return ("final", total) if seen == need else ("void", None)


# ------------------------------------------------------------------ Valorant (event_id = vlr.gg match id, player_id = nick)
def val_value(event_id: str, player_id: str, market: str, cache: dict):
    """val_kills_m12 / val_fb_m12 / val_kills_m1 from the vlr.gg match page once the series is final."""
    from . import val
    stat = "fb" if "_fb_" in market else "kills"
    return val.result(event_id, player_id, stat, 1 if market.endswith("_m1") else 2)


# ------------------------------------------------------------------ Soccer (event_id = ESPN event, player_id = ESPN athlete id)
SOCCER_STATS = {
    "passes_att": lambda s: (s.get("accuratePasses") or 0) + (s.get("inaccuratePasses") or 0),
    "gk_saves": lambda s: s.get("saves"),
    "shots": lambda s: s.get("totalShots"),
    "sot": lambda s: s.get("shotsOnTarget"),
    "tackles": lambda s: s.get("totalTackles"),
    "fouls": lambda s: s.get("foulsCommitted"),
    "goals": lambda s: s.get("totalGoals"),
    "assists": lambda s: s.get("goalAssists"),
    "g_a": lambda s: None if s.get("totalGoals") is None else (s.get("totalGoals") or 0) + (s.get("goalAssists") or 0),
}


def soccer_player_stats(league: str, event_id: str, team_id: str, player_id: str) -> dict:
    d = _get(f"https://sports.core.api.espn.com/v2/sports/soccer/leagues/{league}/events/{event_id}/competitions/{event_id}"
             f"/competitors/{team_id}/roster/{player_id}/statistics/0")
    return {s["name"]: s.get("value") for c in d["splits"]["categories"] for s in c["stats"]}


def soccer_value(event_id: str, player_id: str, market: str, cache: dict, live: bool = False):
    key = ("soccer", event_id)
    if key not in cache:
        cache[key] = _get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={event_id}")
    s = cache[key]
    if not s["header"]["competitions"][0]["status"]["type"].get("completed") and not live:
        return "pending", None
    for r in s.get("rosters", []):
        for p in r.get("roster", []):
            if str(p["athlete"]["id"]) == str(player_id):
                if not (p.get("starter") or p.get("subbedIn")):
                    return "void", None  # didn't play: pick'em apps void the pick
                st = soccer_player_stats(s["header"]["league"]["slug"], event_id, r["team"]["id"], player_id)
                v = SOCCER_STATS[market](st)
                return ("final", v) if v is not None else ("void", None)
    return "void", None


def cfb_value(event_id: str, player_id: str, market: str, cache: dict):
    """College football: same ESPN box score format as the NFL."""
    return nfl_value(event_id, player_id, market, cache, league="college-football")


# ------------------------------------------------------------------ LoL (event_id = bo3.gg match id, player_id = gol.gg id)
def lol_value(event_id: str, player_id: str, market: str, cache: dict):
    """Kills over maps 1..n (market kills_m123 -> games 1-3) from gol.gg once the series is posted there."""
    import re
    from . import lol
    need = len(re.search(r"_m(\d+)$", market).group(1))
    key = ("lol", event_id)
    if key not in cache:
        cache[key] = lol.match_by_id(int(event_id))
    m = cache[key]
    if not m or m.get("status") != "finished":
        return "pending", None
    played = (m.get("team1_score") or 0) + (m.get("team2_score") or 0)
    if played < need:
        return "void", None  # fewer maps than the prop covers: pick'em apps void it
    games = lol.series_games(lol.player_games(player_id), m["start_date"])
    if len(games) < need:
        return "pending", None  # gol.gg posts a few hours after the series
    return "final", sum(g["k"] for g in games[:need])


def tennis_value(event_id: str, player_id: str, market: str, cache: dict):
    """Match winner: 1 if the backed player won (line 0.5, side over). ESPN's winner flag; retirements count as ESPN posts them."""
    from . import tennis
    return tennis.result(event_id, player_id)


GRADERS = {"tennis": tennis_value, "mlb": mlb_value, "nhl": nhl_value, "nba": nba_value, "nfl": nfl_value, "cfb": cfb_value, "cs2": cs2_value, "soccer": soccer_value, "lol": lol_value,
           "val": val_value}


def settle(value: float, line: float, side: str) -> str:
    if value == line:
        return "push"
    over = value > line
    return "won" if (over and side == "over") or (not over and side == "under") else "lost"


def grade_rows(rows: list[dict]) -> dict:
    cache, counts = {}, {"graded": 0, "still_pending": 0, "void": 0, "manual": 0, "errors": 0}
    for r in rows:
        if r.get("status") not in ("pending", ""):
            continue
        fn = GRADERS.get(r.get("sport", "").lower())
        if not fn or not r.get("event_id") or not r.get("player_id"):
            counts["manual"] += 1  # no auto-grader for this sport/market: grade by hand
            continue
        try:
            state, value = fn(r["event_id"], r["player_id"], r["market"], cache)
        except Exception as e:  # network/parse problems leave the bet pending
            msg = f"grade error: {type(e).__name__}"
            if msg not in r.get("notes", ""):
                r["notes"] = (r.get("notes", "") + f" | {msg}").strip(" |")
            counts["errors"] += 1
            continue
        if state == "pending":
            counts["still_pending"] += 1
        elif state == "void":
            r["status"] = "void"
            counts["void"] += 1
        else:
            r["result_value"] = value
            r["status"] = settle(float(value), float(r["line"]), r["side"].lower())
            counts["graded"] += 1
    return counts
