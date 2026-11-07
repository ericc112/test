"""Inputs, each from a named source, cached under betting/.cache/gamesim/.

  nflverse (github.com/nflverse/nflverse-data releases): play-by-play with EPA and success, the schedule with
      closing lines and rest days, official injury reports, ESPN depth charts.
  ESPN game summary (site.api.espn.com): DraftKings moneyline, spread and total with prices, injury designations.
  Open-Meteo (api.open-meteo.com): hourly forecast at the stadium, and city coordinates for travel distance.
Every value keeps the source and pull time with it, so the report can cite them.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import math
import os
import ssl
import time
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(HERE, ".cache", "gamesim")
NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
_CA = "/root/.ccr/ca-bundle.crt"
_CTX = ssl.create_default_context(cafile=_CA) if os.path.exists(_CA) else ssl.create_default_context()

PBP_COLS = ["game_id", "season", "season_type", "week", "posteam", "defteam", "home_team", "away_team", "play_type", "epa",
            "success", "qb_dropback", "passer_player_id", "passer_player_name", "wp", "half_seconds_remaining",
            "game_seconds_remaining", "qtr", "score_differential", "yardline_100", "down", "fixed_drive", "fixed_drive_result",
            "drive_play_count", "drive_time_of_possession", "drive_start_transition", "field_goal_result", "kick_distance",
            "extra_point_result", "two_point_conv_result", "qb_kneel", "qb_spike", "game_date", "play_id",
            # play-level fields for the play-by-play engine
            "yards_gained", "complete_pass", "incomplete_pass", "interception", "sack", "fumble_lost", "touchdown", "penalty",
            "penalty_yards", "penalty_team", "first_down_penalty", "ydstogo", "posteam_timeouts_remaining", "defteam_timeouts_remaining",
            "out_of_bounds", "qb_scramble", "return_yards", "touchback", "timeout", "timeout_team", "two_point_attempt",
            "kickoff_attempt", "own_kickoff_recovery", "punt_attempt", "field_goal_attempt", "return_touchdown", "safety",
            "extra_point_attempt", "first_down", "punt_blocked", "fumble", "air_yards"]


def _fetch(url: str, path: str, max_age: float | None, tries: int = 4) -> str:
    if os.path.exists(path) and (max_age is None or time.time() - os.path.getmtime(path) < max_age):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gamesim/1.0"})
            with urllib.request.urlopen(req, context=_CTX, timeout=120) as r, open(path + ".part", "wb") as f:
                f.write(r.read())
            os.replace(path + ".part", path)
            return path
        except Exception as e:  # network hiccup: back off and retry
            last = e
            time.sleep(2 ** k)
    raise RuntimeError(f"could not fetch {url}: {last}")


def _json(url: str, name: str, max_age: float | None = 1800):
    with open(_fetch(url, os.path.join(CACHE, name), max_age)) as f:
        return json.load(f)


def us_day(iso: str) -> str:
    """US calendar day of an ESPN UTC timestamp ('2026-11-03T00:30Z' is the evening of Nov 2 in the US). Shifting by
    10 hours puts every US game (noon ET to 10:30 pm PT tip-offs) on its local date."""
    t = dt.datetime.strptime(iso[:16], "%Y-%m-%dT%H:%M")
    return (t - dt.timedelta(hours=10)).strftime("%Y-%m-%d")


def cutoff(day: str) -> str:
    """Ratings cutoff for games on US day `day`: everything that started before 10:00Z that morning, i.e. every game
    of earlier US days (late West-coast games included) and nothing from that day. Compare with ESPN 'date' strings."""
    return f"{day}T10:00Z"


def slate_today() -> str:
    """Today's slate as a US date (YYYY-MM-DD), the same 10-hour shift as us_day: the server clock is UTC, so from 7 pm
    ET (EST) a plain date.today() already reads tomorrow and filed the evening's NBA/NFL slate under the wrong day."""
    return us_day(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M"))


def now_cutoff() -> str:
    """Cutoff for today's slate: all games of earlier US days, including last night's (which carry today's UTC date)."""
    return cutoff(us_day(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M")))


def pulled_at(name: str) -> str:
    p = os.path.join(CACHE, name)
    return dt.datetime.fromtimestamp(os.path.getmtime(p), dt.timezone.utc).strftime("%Y-%m-%d %H:%MZ") if os.path.exists(p) else "?"


# ------------------------------------------------------------------ nflverse
def pbp(season: int, max_age: float = 6 * 3600) -> list[dict]:
    """Regular-season plays for a season, only the columns the model reads (parsed once, cached as JSON)."""
    raw = _fetch(f"{NFLVERSE}/pbp/play_by_play_{season}.csv.gz", os.path.join(CACHE, f"pbp_{season}.csv.gz"), max_age)
    slim = os.path.join(CACHE, f"pbp_{season}.slim2.json")
    if os.path.exists(slim) and os.path.getmtime(slim) >= os.path.getmtime(raw):
        with open(slim) as f:
            return json.load(f)
    out = []
    with gzip.open(raw, "rt", newline="") as f:
        r = csv.reader(f)
        hdr = next(r)
        ix = [hdr.index(c) for c in PBP_COLS]
        for row in r:
            d = {c: row[i] for c, i in zip(PBP_COLS, ix)}
            if d["season_type"] != "REG":
                continue
            out.append(d)
    with open(slim, "w") as f:
        json.dump(out, f)
    return out


def schedule(max_age: float = 6 * 3600) -> list[dict]:
    path = _fetch(f"{NFLVERSE}/schedules/games.csv", os.path.join(CACHE, "games.csv"), max_age)
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def injuries(season: int, max_age: float = 3 * 3600) -> list[dict]:
    path = _fetch(f"{NFLVERSE}/injuries/injuries_{season}.csv", os.path.join(CACHE, f"injuries_{season}.csv"), max_age)
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def depth_chart(season: int, team: str, max_age: float = 3 * 3600) -> tuple[str, list[dict]]:
    """Latest ESPN depth chart snapshot for one team (via nflverse): (snapshot time, rows)."""
    path = _fetch(f"{NFLVERSE}/depth_charts/depth_charts_{season}.csv", os.path.join(CACHE, f"depth_{season}.csv"), max_age)
    rows = []
    with open(path, newline="") as f:
        for x in csv.DictReader(f):
            if x["team"] == team:
                rows.append(x)
    last = max((x["dt"] for x in rows), default="")
    return last, [x for x in rows if x["dt"] == last]


def snaps(season: int, max_age: float = 6 * 3600) -> list[dict]:
    path = _fetch(f"{NFLVERSE}/snap_counts/snap_counts_{season}.csv", os.path.join(CACHE, f"snaps_{season}.csv"), max_age)
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------ ESPN / DraftKings
def espn_game(espn_id: str) -> dict:
    """DraftKings lines (with prices) and injury designations from the ESPN summary."""
    s = _json(f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={espn_id}", f"espn_{espn_id}.json", 900)
    pc = (s.get("pickcenter") or [{}])[0]
    h, a = pc.get("homeTeamOdds") or {}, pc.get("awayTeamOdds") or {}
    num = lambda x: f(str(x).replace("+", ""), None) if x not in (None, "") else None
    sp = pc.get("spread")
    if sp is not None and (h.get("favorite") is True and sp > 0 or h.get("favorite") is False and sp < 0):
        sp = -sp
    inj = []
    for t in s.get("injuries", []) or []:
        for i in t.get("injuries", []):
            inj.append({"team": t["team"]["abbreviation"], "name": i["athlete"]["displayName"],
                        "pos": (i["athlete"].get("position") or {}).get("abbreviation"), "status": i.get("status"),
                        "detail": (i.get("details") or {}).get("type")})
    comp = s["header"]["competitions"][0]
    opn = lambda grp, side, k: num((((pc.get(grp) or {}).get(side) or {}).get("open") or {}).get(k, "").replace("o", "").replace("u", "") or None)
    return {"ml_home_open": opn("moneyline", "home", "odds"), "ml_away_open": opn("moneyline", "away", "odds"),
            "spread_home_open": opn("pointSpread", "home", "line"), "total_open": opn("total", "over", "line"),
            "provider": (pc.get("provider") or {}).get("name", "?"), "pulled": pulled_at(f"espn_{espn_id}.json"),
            "ml_home": num(h.get("moneyLine")), "ml_away": num(a.get("moneyLine")), "spread_home": sp,
            "spread_home_odds": num(h.get("spreadOdds")), "spread_away_odds": num(a.get("spreadOdds")),
            "total": pc.get("overUnder"), "over_odds": num(pc.get("overOdds")), "under_odds": num(pc.get("underOdds")),
            "injuries": inj, "kickoff": comp["date"], "status": comp["status"]["type"]["name"]}


# ------------------------------------------------------------------ Open-Meteo
def city(name: str) -> tuple[float, float]:
    d = _json(f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.request.quote(name)}&count=1&countryCode=US",
              f"geo_{name.replace(' ', '_')}.json", None)
    r = d["results"][0]
    return r["latitude"], r["longitude"]


def forecast(lat: float, lon: float, when_utc: dt.datetime) -> dict | None:
    """Hourly forecast at kickoff and the next three hours: wind first, then precipitation, then temperature."""
    day = when_utc.strftime("%Y-%m-%d")
    nxt = (when_utc + dt.timedelta(hours=4)).strftime("%Y-%m-%d")
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}&hourly=temperature_2m,precipitation,"
           f"precipitation_probability,wind_speed_10m,wind_gusts_10m&wind_speed_unit=mph&temperature_unit=fahrenheit"
           f"&start_date={day}&end_date={nxt}&timezone=UTC")
    try:
        d = _json(url, f"wx_{lat:.2f}_{lon:.2f}_{day}.json", 3 * 3600)
    except RuntimeError:
        return None
    hrs = d["hourly"]["time"]
    pick = [i for i, t in enumerate(hrs) if when_utc.strftime("%Y-%m-%dT%H") <= t[:13] <= (when_utc + dt.timedelta(hours=3)).strftime("%Y-%m-%dT%H")]
    if not pick:
        return None
    H = d["hourly"]
    avg = lambda k: sum(H[k][i] for i in pick if H[k][i] is not None) / len(pick)
    return {"wind_mph": round(avg("wind_speed_10m"), 1), "gust_mph": round(max(H["wind_gusts_10m"][i] for i in pick), 1),
            "precip_mm": round(sum(H["precipitation"][i] for i in pick), 2),
            "precip_prob": round(avg("precipitation_probability"), 0) if H.get("precipitation_probability") else None,
            "temp_f": round(avg("temperature_2m"), 1), "pulled": pulled_at(f"wx_{lat:.2f}_{lon:.2f}_{day}.json"),
            "source": "Open-Meteo forecast"}


def miles(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def f(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default
