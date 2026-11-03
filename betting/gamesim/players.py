"""Player layer and context: starting QBs, absences as numeric rating adjustments, snap shares, rest/travel/weather.

  - Starting QB: ESPN depth chart QB1 (via nflverse, with its snapshot time). Until the official inactive list
    (90 minutes before kickoff) every starter is PROJECTED, and the report says so.
  - QB change: the season offense rating already contains the QBs who played. Starting someone else moves it by
    dropback share x (starter's EPA/dropback - the season's dropback-weighted QB mix), in EPA per play.
  - Other absences: listed with their source and status. There is no defensible per-player impact rating for
    non-QBs from free data, so they get 0 and are flagged; the backtest error (which also ignored them) covers it.
  - Snap shares (nflverse/PFR) for every rotation player, last three games, as context.
  - Rest days (nflverse schedule), travel distance and time zones (Open-Meteo geocoding), forecast weather.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from . import data
from .ratings import qb_mix

CITY = {"ARI": "Glendale", "ATL": "Atlanta", "BAL": "Baltimore", "BUF": "Orchard Park", "CAR": "Charlotte", "CHI": "Chicago",
        "CIN": "Cincinnati", "CLE": "Cleveland", "DAL": "Arlington", "DEN": "Denver", "DET": "Detroit", "GB": "Green Bay",
        "HOU": "Houston", "IND": "Indianapolis", "JAX": "Jacksonville", "KC": "Kansas City", "LA": "Inglewood", "LAC": "Inglewood",
        "LV": "Paradise", "MIA": "Miami Gardens", "MIN": "Minneapolis", "NE": "Foxborough", "NO": "New Orleans", "NYG": "East Rutherford",
        "NYJ": "East Rutherford", "PHI": "Philadelphia", "PIT": "Pittsburgh", "SEA": "Seattle", "SF": "Santa Clara", "TB": "Tampa",
        "TEN": "Nashville", "WAS": "Landover"}


def starting_qb(season: int, team: str) -> dict:
    snap, rows = data.depth_chart(season, team)
    qbs = sorted([r for r in rows if r["pos_abb"] == "QB"], key=lambda r: int(data.f(r["pos_rank"], 9)))
    if not qbs:
        return {"name": None, "gsis": None, "source": "no depth chart", "status": "missing", "depth": []}
    return {"name": qbs[0]["player_name"], "gsis": qbs[0]["gsis_id"], "status": "projected",
            "source": f"ESPN depth chart via nflverse, snapshot {snap}", "depth": [q["player_name"] for q in qbs]}


def gsis_for(season: int, team: str, name: str) -> str | None:
    _, rows = data.depth_chart(season, team)
    return next((r["gsis_id"] for r in rows if r["player_name"].lower() == name.lower()), None)


def qb_delta(team: str, starter_gsis: str | None, team_plays: list[dict], qbs: dict, db_share: float) -> dict:
    """EPA/play adjustment to a team's offense for its starting QB vs the QBs behind its season rating."""
    mix, shares = qb_mix(team_plays, team, qbs)
    q = qbs.get(starter_gsis) if starter_gsis else None
    if q is None:
        return {"delta": 0.0, "mix": mix, "shares": shares, "starter_epa": None, "starter_db": 0,
                "note": "starter has no dropbacks in the data: no adjustment (flagged)"}
    return {"delta": db_share * (q["epa_db"] - mix), "mix": mix, "shares": shares, "starter_epa": q["epa_db"],
            "starter_db": q["dropbacks"], "note": ""}


def absences(season: int, team: str, espn_injuries: list[dict]) -> list[dict]:
    """Game-week designations (ESPN) plus the latest official report (nflverse), with source and adjustment."""
    out = []
    for i in espn_injuries:
        if i["team"] == team:
            out.append({"name": i["name"], "pos": i["pos"], "status": i["status"], "detail": i["detail"],
                        "source": "ESPN game summary (designation)", "adj": 0.0 if i["pos"] != "QB" else None})
    inj = data.injuries(season)
    wk = max((int(x["week"]) for x in inj if x["team"] == team), default=0)
    for x in inj:
        if x["team"] == team and int(x["week"]) == wk and x["report_status"] in ("Out", "Doubtful", "Questionable"):
            if not any(o["name"] == x["full_name"] for o in out):
                out.append({"name": x["full_name"], "pos": x["position"], "status": x["report_status"], "detail": x["report_primary_injury"],
                            "source": f"Official injury report week {wk} (nflverse)", "adj": 0.0 if x["position"] != "QB" else None})
    return out


def snap_table(season: int, team: str, last: int = 3) -> list[dict]:
    rows = [r for r in data.snaps(season) if r["team"] == team and r["game_type"] == "REG"]
    weeks = sorted({int(r["week"]) for r in rows})[-last:]
    acc = defaultdict(lambda: {"off": [], "def": [], "pos": ""})
    for r in rows:
        if int(r["week"]) in weeks:
            a = acc[r["player"]]
            a["pos"] = r["position"]
            a["off"].append(data.f(r["offense_pct"], 0))
            a["def"].append(data.f(r["defense_pct"], 0))
    out = [{"player": p, "pos": v["pos"], "off_pct": sum(v["off"]) / len(weeks), "def_pct": sum(v["def"]) / len(weeks), "weeks": weeks}
           for p, v in acc.items()]
    return sorted([o for o in out if max(o["off_pct"], o["def_pct"]) >= 0.3], key=lambda o: -(o["off_pct"] + o["def_pct"]))


def context(sched_row: dict, kickoff_iso: str) -> dict:
    home, away = sched_row["home_team"], sched_row["away_team"]
    out = {"rest_home": data.f(sched_row["home_rest"]), "rest_away": data.f(sched_row["away_rest"]), "roof": sched_row["roof"],
           "surface": sched_row["surface"], "referee": sched_row["referee"] or None, "stadium": sched_row["stadium"],
           "rest_source": "nflverse schedule"}
    try:
        h, a = data.city(CITY[home]), data.city(CITY[away])
        out["travel_miles"] = round(data.miles(h, a))
        out["coords_home"] = h
        out["travel_source"] = "Open-Meteo geocoding (city centres)"
    except Exception as e:
        out["travel_miles"], out["travel_source"] = None, f"missing ({type(e).__name__})"
    out["weather"] = None
    if sched_row["roof"] in ("outdoors", "open") and out.get("coords_home"):
        k = dt.datetime.fromisoformat(kickoff_iso.replace("Z", "+00:00")).replace(tzinfo=None)
        out["weather"] = data.forecast(*out["coords_home"], k)
    return out
