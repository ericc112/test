"""Multi-book player-prop prices from The Odds API (https://the-odds-api.com). Key: $ODDS_API_KEY (never in the repo).

For a PrizePicks line, every book's price at that exact line is turned into a fair over-probability:
  - two-way over/under at the line: multiplicative de-vig, the method that leaves the favourite the lowest number,
    so an 80% leg is never overstated by the de-vig choice;
  - a one-way alternate ('Over 2.5' only): the milestone hold used for DraftKings ladders (tier.devig_one_way).
The consensus is a logit-space weighted mean, sharp books weighted up (Pinnacle 3x). Books that disagree by more
than 10 points are flagged.

Quota: an event-odds call costs (markets requested) x (bookmaker groups of 10). Only the markets on tonight's
PrizePicks board are requested, and responses are cached on disk (odds 10 min, event lists 1 h).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.the-odds-api.com/v4"
KEY_ENV = "ODDS_API_KEY"
CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache", "oddsapi")
SPORT_KEYS = {"NBA": "basketball_nba", "NHL": "icehockey_nhl", "MLB": "baseball_mlb", "NFL": "americanfootball_nfl",
              "CFB": "americanfootball_ncaaf", "WNBA": "basketball_wnba"}
# one bookmaker group (<= 10 keys) = one region's cost
BOOKS = os.environ.get("ODDS_API_BOOKS", "pinnacle,draftkings,fanduel,betmgm,williamhill_us,espnbet,betrivers,fanatics,betonlineag,bovada")
SHARP = {"pinnacle": 3.0, "circasports": 2.0, "betonlineag": 1.5}
DISAGREE = 0.10

# PrizePicks stat -> The Odds API market key (its alternate ladder is the same key + '_alternate' where offered)
MARKETS = {
    "NBA": {"Points": "player_points", "Rebounds": "player_rebounds", "Assists": "player_assists", "3-PT Made": "player_threes",
            "Pts+Rebs+Asts": "player_points_rebounds_assists", "Pts+Rebs": "player_points_rebounds",
            "Pts+Asts": "player_points_assists", "Rebs+Asts": "player_rebounds_assists", "Blocked Shots": "player_blocks",
            "Steals": "player_steals", "Turnovers": "player_turnovers", "Blks+Stls": "player_blocks_steals"},
    "NHL": {"Shots On Goal": "player_shots_on_goal", "Points": "player_points", "Assists": "player_assists", "Goals": "player_goals",
            "Power Play Points": "player_power_play_points", "Blocked Shots": "player_blocked_shots", "Goalie Saves": "player_total_saves"},
    "MLB": {"Hits": "batter_hits", "Total Bases": "batter_total_bases", "Hits+Runs+RBIs": "batter_hits_runs_rbis",
            "Runs": "batter_runs_scored", "RBIs": "batter_rbis", "Hitter Strikeouts": "batter_strikeouts", "Walks": "batter_walks",
            "Singles": "batter_singles", "Home Runs": "batter_home_runs", "Pitcher Strikeouts": "pitcher_strikeouts",
            "Pitching Outs": "pitcher_outs", "Hits Allowed": "pitcher_hits_allowed", "Earned Runs Allowed": "pitcher_earned_runs",
            "Walks Allowed": "pitcher_walks"},
    "NFL": {"Pass Yards": "player_pass_yds", "Rush Yards": "player_rush_yds", "Receiving Yards": "player_reception_yds",
            "Receptions": "player_receptions", "Pass TDs": "player_pass_tds", "Rush+Rec Yds": "player_rush_reception_yds",
            "Pass Attempts": "player_pass_attempts", "Pass Completions": "player_pass_completions",
            "Rush Attempts": "player_rush_attempts", "INT": "player_pass_interceptions", "Longest Reception": "player_reception_longest"},
}
NO_ALTERNATE = {"player_turnovers", "player_blocks_steals", "player_pass_interceptions", "player_reception_longest",
                "player_pass_attempts", "player_pass_completions", "player_rush_attempts", "batter_hits_runs_rbis", "pitcher_outs",
                "pitcher_earned_runs"}

quota = {"remaining": None, "used": None, "last": None}


def enabled() -> bool:
    return bool(os.environ.get(KEY_ENV))


def _fetch(path: str, params: dict, max_age: int):
    """GET with the key added; cached on disk by URL without the key; quota headers kept in `quota`."""
    q = urllib.parse.urlencode(sorted(params.items()))
    os.makedirs(CACHE, exist_ok=True)
    cpath = os.path.join(CACHE, hashlib.sha1(f"{path}?{q}".encode()).hexdigest() + ".json")
    if os.path.exists(cpath) and time.time() - os.path.getmtime(cpath) < max_age:
        with open(cpath) as f:
            return json.load(f)
    from .grade import _CTX
    url = f"{API}{path}?{q}&apiKey={urllib.parse.quote(os.environ[KEY_ENV])}"
    req = urllib.request.Request(url, headers={"User-Agent": "edge/1.0"})
    with urllib.request.urlopen(req, context=_CTX, timeout=30) as r:
        out = json.load(r)
        quota.update(remaining=r.headers.get("x-requests-remaining"), used=r.headers.get("x-requests-used"),
                     last=r.headers.get("x-requests-last"))
    with open(cpath, "w") as f:
        json.dump(out, f)
    return out


def events(league: str) -> list[dict]:
    return _fetch(f"/sports/{SPORT_KEYS[league]}/events", {}, 3600)


def event_odds(league: str, event_id: str, markets: set[str]) -> dict:
    mk = sorted(m for m in markets if m)
    if not mk:
        return {}
    full = sorted(set(mk) | {m + "_alternate" for m in mk if m not in NO_ALTERNATE})
    params = {"bookmakers": BOOKS, "oddsFormat": "american"}
    try:
        return _fetch(f"/sports/{SPORT_KEYS[league]}/events/{event_id}/odds", {**params, "markets": ",".join(full)}, 600)
    except urllib.error.HTTPError as e:
        if e.code != 422:                                   # 422: a market key this sport doesn't carry; retry mains only
            raise
        return _fetch(f"/sports/{SPORT_KEYS[league]}/events/{event_id}/odds", {**params, "markets": ",".join(mk)}, 600)


def _fold(s: str) -> str:
    from .lowline import _fold as f
    return f(s)


def match_event(evs: list[dict], team_name: str, start: str | None) -> dict | None:
    """The Odds API event whose home or away team contains PrizePicks' team name, starting within 6 hours of its start."""
    t0 = None
    if start:
        try:
            t0 = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
        except ValueError:
            t0 = None
    tn = _fold(team_name or "")
    for e in evs:
        if tn and (tn in _fold(e.get("home_team", "")) or tn in _fold(e.get("away_team", ""))):
            if t0 is None:
                return e
            ct = dt.datetime.fromisoformat(e["commence_time"].replace("Z", "+00:00"))
            if abs((ct - t0).total_seconds()) < 6 * 3600:
                return e
    return None


def _implied(am: float) -> float:
    return 100 / (am + 100) if am > 0 else -am / (-am + 100)


def book_prices(odds: dict, market: str, player: str, line: float) -> dict[str, float]:
    """{bookmaker: fair P(over)} at exactly `line`, from the main and alternate markets."""
    from .tier import devig_one_way
    who = _fold(player)
    out = {}
    for bk in odds.get("bookmakers", []):
        over = under = None
        for m in bk.get("markets", []):
            if m.get("key") not in (market, market + "_alternate"):
                continue
            for o in m.get("outcomes", []):
                if _fold(o.get("description", "")) != who or o.get("point") is None or abs(float(o["point"]) - line) > 1e-9:
                    continue
                if o.get("name") == "Over" and over is None:
                    over = float(o["price"])
                elif o.get("name") == "Under" and under is None:
                    under = float(o["price"])
        if over is not None and under is not None:
            po, pu = _implied(over), _implied(under)
            out[bk["key"]] = po / (po + pu)
        elif over is not None and line != int(line):        # one-way ladder rung; whole lines need the push priced
            out[bk["key"]] = devig_one_way(_implied(over))
    return out


def main_line(odds: dict, market: str, player: str) -> float | None:
    """The books' main over/under number for this player (median across books): the market's projection."""
    who, pts = _fold(player), []
    for bk in odds.get("bookmakers", []):
        for m in bk.get("markets", []):
            if m.get("key") == market:
                pts += [float(o["point"]) for o in m.get("outcomes", []) if o.get("name") == "Over"
                        and o.get("point") is not None and _fold(o.get("description", "")) == who]
    if not pts:
        return None
    pts.sort()
    return pts[len(pts) // 2]


def consensus(prices: dict[str, float]) -> dict | None:
    if not prices:
        return None
    lg = lambda p: math.log(min(max(p, 1e-4), 1 - 1e-4) / (1 - min(max(p, 1e-4), 1 - 1e-4)))
    w = {k: SHARP.get(k, 1.0) for k in prices}
    z = sum(w[k] * lg(p) for k, p in prices.items()) / sum(w.values())
    p = 1 / (1 + math.exp(-z))
    lo, hi = min(prices.values()), max(prices.values())
    return {"p_over": p, "n": len(prices), "sharp": [k for k in prices if k in SHARP], "lo": lo, "hi": hi,
            "disagree": hi - lo > DISAGREE, "books": prices}


def describe(c: dict, side: str = "over") -> str:
    f = (lambda p: p) if side == "over" else (lambda p: 1 - p)
    sharp = f" incl. {', '.join(c['sharp'])}" if c["sharp"] else ""
    rng = sorted((f(c["lo"]), f(c["hi"])))
    return (f"{c['n']} book{'s' if c['n'] > 1 else ''}{sharp}: {f(c['p_over']):.3f} (range {rng[0]:.2f}-{rng[1]:.2f})"
            + ("; books disagree" if c["disagree"] else ""))


def check(league: str = "NBA") -> str:
    """One cheap call to prove the key works: the event list (no quota cost) and the quota headers."""
    if not enabled():
        return f"${KEY_ENV} is not set"
    evs = _fetch(f"/sports/{SPORT_KEYS[league]}/events", {}, 0)
    return f"key OK: {len(evs)} {league} events listed; requests remaining {quota['remaining']}, used {quota['used']}"
