"""Auto-grade pending bets from official/free stat feeds (MLB Stats API, NHL API, ESPN, bo3.gg)."""
from __future__ import annotations

import json
import os
import ssl
import unicodedata
import urllib.request

_CA = "/root/.ccr/ca-bundle.crt"
_CTX = ssl.create_default_context(cafile=_CA) if os.path.exists(_CA) else ssl.create_default_context()


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=_CTX, timeout=30) as r:
        return json.load(r)


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
    "batter_hits": ("batting", lambda s: s.get("hits")),
    "batter_walks": ("batting", lambda s: s.get("baseOnBalls")),
    "batter_strikeouts": ("batting", lambda s: s.get("strikeOuts")),
    "batter_total_bases": ("batting", lambda s: s.get("totalBases")),
    "batter_home_runs": ("batting", lambda s: s.get("homeRuns")),
    "batter_singles": ("batting", lambda s: None if s.get("hits") is None else s["hits"] - s.get("doubles", 0) - s.get("triples", 0) - s.get("homeRuns", 0)),
    "batter_hrr": ("batting", lambda s: None if s.get("hits") is None else s["hits"] + s.get("runs", 0) + s.get("rbi", 0)),
}


def mlb_value(event_id: str, player_id: str, market: str, cache: dict):
    key = ("mlb", event_id)
    if key not in cache:
        sched = _get(f"https://statsapi.mlb.com/api/v1/schedule?gamePk={event_id}")
        game = sched["dates"][0]["games"][0]
        cache[key] = {"final": game["status"]["abstractGameState"] == "Final",
                      "box": _get(f"https://statsapi.mlb.com/api/v1/game/{event_id}/boxscore")}
    c = cache[key]
    if not c["final"]:
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
NHL_STATS = {"skater_sog": "sog", "skater_points": "points", "skater_goals": "goals", "goalie_saves": "saves"}


def nhl_value(event_id: str, player_id: str, market: str, cache: dict):
    key = ("nhl", event_id)
    if key not in cache:
        cache[key] = _get(f"https://api-web.nhle.com/v1/gamecenter/{event_id}/boxscore")
    b = cache[key]
    if b.get("gameState") not in ("OFF", "FINAL"):
        return "pending", None
    for side in ("homeTeam", "awayTeam"):
        for grp in ("forwards", "defense", "goalies"):
            for p in b["playerByGameStats"][side].get(grp, []):
                if str(p["playerId"]) == str(player_id):
                    return "final", p.get(NHL_STATS[market])
    return "void", None


# ------------------------------------------------------------------ NFL (event_id = ESPN event, player_id = ESPN athlete id)
NFL_STATS = {
    "pass_yds": ("passing", "YDS"), "rush_yds": ("rushing", "YDS"), "rush_att": ("rushing", "CAR"),
    "rec_yds": ("receiving", "YDS"), "receptions": ("receiving", "REC"),
}


def nfl_value(event_id: str, player_id: str, market: str, cache: dict):
    key = ("nfl", event_id)
    if key not in cache:
        cache[key] = _get(f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={event_id}")
    s = cache[key]
    if s["header"]["competitions"][0]["status"]["type"]["name"] != "STATUS_FINAL":
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


# ------------------------------------------------------------------ CS2 (event_id = bo3.gg match id, player_id = nickname)
def cs2_value(event_id: str, player_id: str, market: str, cache: dict):
    key = ("cs2", event_id)
    if key not in cache:
        games = _get(f"https://api.bo3.gg/api/v1/games?filter%5Bgames.match_id%5D%5Beq%5D={event_id}")["results"]
        cache[key] = sorted(games, key=lambda g: g.get("number") or 0)
    games = cache[key]
    m12 = [g for g in games if g.get("number") in (1, 2)]
    if len(m12) < 2 or any(g.get("status") != "finished" for g in m12):
        return "pending", None
    field = {"cs_kills_m12": "kills", "cs_headshots_m12": "headshots"}[market]
    total, seen = 0, 0
    for g in m12:
        stats = _get(f"https://api.bo3.gg/api/v1/games/{g['id']}/players_stats")
        if not stats:  # map finished but demo not parsed yet: wait, don't void
            return "pending", None
        for p in stats:
            nick = ((p.get("steam_profile") or {}).get("player") or {}).get("nickname") or (p.get("steam_profile") or {}).get("nickname")
            if _norm(nick) == _norm(player_id):
                total += p[field]
                seen += 1
    return ("final", total) if seen == 2 else ("void", None)


GRADERS = {"mlb": mlb_value, "nhl": nhl_value, "nfl": nfl_value, "cs2": cs2_value}


def settle(value: float, line: float, side: str) -> str:
    if value == line:
        return "push"
    over = value > line
    return "won" if (over and side == "over") or (not over and side == "under") else "lost"


def grade_rows(rows: list[dict]) -> dict:
    cache, counts = {}, {"graded": 0, "still_pending": 0, "void": 0, "errors": 0}
    for r in rows:
        if r.get("status") not in ("pending", ""):
            continue
        fn = GRADERS.get(r.get("sport", "").lower())
        if not fn or not r.get("event_id") or not r.get("player_id"):
            counts["errors"] += 1
            continue
        try:
            state, value = fn(r["event_id"], r["player_id"], r["market"], cache)
        except Exception as e:  # network/parse problems leave the bet pending
            r["notes"] = (r.get("notes", "") + f" | grade error: {type(e).__name__}").strip(" |")
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
