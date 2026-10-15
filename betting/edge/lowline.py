"""Low-line unders: the "U 0.5 assists" read, done with numbers.

Count stats are skewed. When a player averages less than ln 2 = 0.69 of something a game, he records zero more
often than not, so Under 0.5 wins more than half the time (0.30 assists a game -> no assist in 74% of games; 0.35
walks -> none in 70%). PrizePicks makes most of those lines goblins/demons (More only); this scans the STANDARD
lines at 0.5-1.5, where Less is offered, and prices the under from each player's game logs:

- history: share of his last HIST_N games under the line (this season first, then last season);
- model: mean = this season's games weighted double, shrunk to last season's rate, scaled to his recent ice time /
  plate appearances (role), then a gamma-Poisson (CV FORM_CV on the mean) for P(X <= line);
- no market price: sportsbooks' 1+ ladders for these aren't on ESPN for most players, so a High needs HIST_N >= 20
  games and model and history within 10 points (the usual no-market gate).
A role change (recent ice time or plate appearances 25% off his average) is flagged and capped at Low (L5).
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import math
import re
import unicodedata
import urllib.parse

import numpy as np

from .blend import final_probability, rating
from .grade import _get

HIST_N = 30
FORM_CV = 0.25
ROLE_SHIFT = 0.25

NHL_SEASONS = ("20262027", "20252026")
NHL_STATS = {"Points": ("points", "skater_points"), "Assists": ("assists", "skater_assists"),
             "Goals": ("goals", "skater_goals"), "Shots On Goal": ("shots", "skater_sog"),
             "Power Play Points": ("powerPlayPoints", "skater_ppp")}
MLB_STATS = {"Hits": (lambda s: s["hits"], "batter_hits"), "Total Bases": (lambda s: s["totalBases"], "batter_total_bases"),
             "Singles": (lambda s: s["hits"] - s["doubles"] - s["triples"] - s["homeRuns"], "batter_singles"),
             "Walks": (lambda s: s["baseOnBalls"], "batter_walks"), "Hits+Runs+RBIs": (lambda s: s["hits"] + s["runs"] + s["rbi"], "batter_hrr"),
             "Runs": (lambda s: s["runs"], "batter_runs"), "RBIs": (lambda s: s["rbi"], "batter_rbi"),
             "Home Runs": (lambda s: s["homeRuns"], "batter_home_runs"), "Doubles": (lambda s: s["doubles"], "batter_doubles"),
             "Hitter Strikeouts": (lambda s: s["strikeOuts"], "batter_strikeouts"), "Stolen Bases": (lambda s: s["stolenBases"], "batter_sb")}
NFL_STATS = {"INT": (("passing", "INT"), "pass_int"), "Pass TDs": (("passing", "TD"), "pass_tds"),
             "Rush TDs": (("rushing", "TD"), "rush_tds"), "Receptions": (("receiving", "REC"), "receptions"),
             "Anytime TDs": ((("rushing", "TD"), ("receiving", "TD")), "anytime_td"), "FG Made": (("kicking", "FGM"), "fg_made")}


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z]", "", s)


def _same(a: str, b: str) -> bool:
    fa, fb = _fold(a), _fold(b)
    return fa == fb or (fa[-6:] == fb[-6:] and fa[:1] == fb[:1])


# ------------------------------------------------------------------ game logs: [{"date", "x": {stat: value}, "vol": TOI/PA}]
def nhl_player(team: str, name: str) -> str | None:
    ro = _get(f"https://api-web.nhle.com/v1/roster/{team}/current")
    for grp in ("forwards", "defensemen", "goalies"):
        for p in ro.get(grp, []):
            if _same(f"{p['firstName']['default']} {p['lastName']['default']}", name):
                return str(p["id"])
    return None


def nhl_log(pid: str) -> list[dict]:
    out = []
    for season in NHL_SEASONS:
        try:
            gl = _get(f"https://api-web.nhle.com/v1/player/{pid}/game-log/{season}/2").get("gameLog", [])
        except Exception:
            continue
        for g in gl:
            m, s = (g.get("toi") or "0:0").split(":")
            out.append({"date": g["gameDate"], "season": season, "x": g, "vol": int(m) + int(s) / 60})
    return sorted(out, key=lambda r: r["date"], reverse=True)


_MLB_TEAMS: dict = {}


def mlb_player(team: str, name: str) -> str | None:
    if not _MLB_TEAMS:
        for t in _get("https://statsapi.mlb.com/api/v1/teams?sportId=1")["teams"]:
            _MLB_TEAMS[t["abbreviation"]] = t["id"]
    tid = _MLB_TEAMS.get(team) or _MLB_TEAMS.get({"AZ": "ARI", "CWS": "CHW", "WSH": "WSN"}.get(team, team))
    if tid:
        for p in _get(f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster?rosterType=40Man")["roster"]:
            if _same(p["person"]["fullName"], name):
                return str(p["person"]["id"])
    r = _get("https://statsapi.mlb.com/api/v1/people/search?sportIds=1&names=" + urllib.parse.quote(name))
    hit = [p for p in r.get("people", []) if p.get("primaryPosition", {}).get("abbreviation") != "P"]
    return str(hit[0]["id"]) if hit else None


def mlb_abbr(team_id) -> str:
    """statsapi team id -> abbreviation (game logs name the opponent by id)."""
    if not _MLB_TEAMS:
        for t in _get("https://statsapi.mlb.com/api/v1/teams?sportId=1")["teams"]:
            _MLB_TEAMS[t["abbreviation"]] = t["id"]
    return next((a for a, i in _MLB_TEAMS.items() if i == team_id), "")


def mlb_log(pid: str) -> list[dict]:
    out = []
    year = dt.date.today().year
    for season, types in ((year, "R,F,D,L"), (year - 1, "R")):
        for gt in types.split(","):
            try:
                sp = _get(f"https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=gameLog&group=hitting&season={season}&gameType={gt}")["stats"]
            except Exception:
                continue
            for x in (sp[0]["splits"] if sp else []):
                out.append({"date": x["date"], "season": str(season), "x": x["stat"], "vol": x["stat"].get("plateAppearances", 0),
                            "opp": mlb_abbr((x.get("opponent") or {}).get("id")), "home": bool(x.get("isHome"))})
    return sorted(out, key=lambda r: r["date"], reverse=True)


def nfl_player(team: str, name: str) -> str | None:
    r = _get("https://site.web.api.espn.com/apis/common/v3/search?type=player&sport=football&limit=5&query=" + urllib.parse.quote(name))
    hit = [x for x in r.get("items", []) if x.get("league") == "nfl"]
    return str(hit[0]["id"]) if hit else None


def nfl_log(pid: str) -> list[dict]:
    out = []
    year = dt.date.today().year
    for season in (year, year - 1):
        try:
            gl = _get(f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{pid}/gamelog?season={season}")
        except Exception:
            continue
        cats = gl.get("categories") or []
        labels = gl.get("labels") or []
        names = gl.get("names") or []
        evs = gl.get("events") or {}
        per = {}
        for stype in gl.get("seasonTypes", []):
            if "Preseason" in stype.get("displayName", ""):
                continue
            for cat in stype.get("categories", []):
                for e in cat.get("events", []):
                    per.setdefault(e["eventId"], {})
                    stats = e.get("stats", [])
                    # labels repeat across categories (TD, YDS): key them by the owning category
                    off = 0
                    for c in cats:
                        n = c.get("count") or len(c.get("labels", []))
                        for i, lab in enumerate(labels[off:off + n]):
                            if off + i < len(stats):
                                per[e["eventId"]][(c.get("name"), lab)] = stats[off + i]
                        off += n
        for eid, x in per.items():
            # workload, so a backup who just became the starter is caught (L5): pass attempts for passers, else touches
            vol = _num(x.get(("passing", "ATT"))) or (_num(x.get(("rushing", "CAR"))) + _num(x.get(("receiving", "TGTS"))))
            ev = evs.get(eid) or {}
            out.append({"date": ev.get("gameDate", "")[:10], "season": str(season), "x": x, "vol": vol,
                        "opp": (ev.get("opponent") or {}).get("abbreviation", ""), "home": ev.get("atVs") == "vs"})
    return sorted(out, key=lambda r: r["date"], reverse=True)


def _num(v) -> float:
    try:
        return float(str(v).split("/")[0].replace("--", "0"))
    except ValueError:
        return 0.0


def value(sport: str, stat: str, g: dict) -> float | None:
    x = g["x"]
    if sport == "NHL":
        return float(x.get(NHL_STATS[stat][0]) or 0)
    if sport == "MLB":
        try:
            return float(MLB_STATS[stat][0]({k: x.get(k, 0) or 0 for k in ("hits", "doubles", "triples", "homeRuns", "baseOnBalls", "runs",
                                                                           "rbi", "totalBases", "strikeOuts", "stolenBases")}))
        except Exception:
            return None
    key = NFL_STATS[stat][0]
    keys = key if isinstance(key[0], tuple) else (key,)
    vals = [x.get(k) for k in keys]
    return None if all(v is None for v in vals) else sum(_num(v) for v in vals if v is not None)


# ------------------------------------------------------------------ pricing
def price_under(vals: list[float], seasons: list[str], vols: list[float], line: float, n_sim: int = 100_000) -> dict:
    cur = seasons[0] if seasons else ""
    w = np.array([2.0 if s == cur else 1.0 for s in seasons])
    v = np.array(vals, dtype=float)
    mean_g = float((w * v).sum() / w.sum()) if len(v) else 0.0
    vol = np.array(vols, dtype=float)
    avg_vol = float((w * vol).sum() / w.sum()) if len(vol) and vol.sum() else 0.0
    recent_vol = float(vol[:5].mean()) if len(vol) >= 3 and vol.sum() else avg_vol
    scale = recent_vol / avg_vol if avg_vol else 1.0
    mu = mean_g * min(1.4, max(0.6, scale))
    rng = np.random.default_rng(11)
    x = rng.poisson(mu * rng.gamma(1 / FORM_CV ** 2, FORM_CV ** 2, n_sim))
    under, push = (x < line).mean(), (x == line).mean()
    hist = v[:HIST_N]
    h_under = float((hist < line).sum()) / max(1, int((hist != line).sum()))
    return {"p_model": float(under / max(1e-9, 1 - push)), "push": float(push), "mean": mu, "per_game": mean_g,
            "p_hist": h_under, "hist_n": int((hist != line).sum()), "role_shift": abs(scale - 1) > ROLE_SHIFT, "scale": scale,
            "last": [int(a) if float(a).is_integer() else a for a in hist[:10]]}


def scan(leagues=("NHL", "MLB", "NFL"), max_line: float = 1.5, log=print) -> list[dict]:
    from . import pp
    props = []
    for lg in leagues:
        try:
            props += [p for p in pp.board(lg, ("standard",)) if float(p["line"]) <= max_line and p["stat"] in
                      {"NHL": NHL_STATS, "MLB": MLB_STATS, "NFL": NFL_STATS}[lg]]
        except Exception as e:
            log(f"{lg}: board unavailable ({type(e).__name__})")
    log(f"Pricing {len(props)} standard low line(s) ...")
    find = {"NHL": (nhl_player, nhl_log), "MLB": (mlb_player, mlb_log), "NFL": (nfl_player, nfl_log)}

    def one(p):
        try:
            pid = find[p["league"]][0](p["team"], p["player"])
            if not pid:
                return {**p, "error": "player not found"}
            gl = find[p["league"]][1](pid)
            rows = [(value(p["league"], p["stat"], g), g) for g in gl]
            rows = [(v, g) for v, g in rows if v is not None]
            if p["league"] == "MLB":
                rows = [(v, g) for v, g in rows if (g["vol"] or 0) >= 2]          # pinch-hit cameos aren't his role
            if len(rows) < 5:
                return {**p, "error": f"only {len(rows)} games"}
            r = price_under([v for v, _ in rows], [g["season"] for _, g in rows], [g["vol"] for _, g in rows], float(p["line"]))
            mk = {"NHL": NHL_STATS, "MLB": MLB_STATS, "NFL": NFL_STATS}[p["league"]][p["stat"]][1]
            seg = f"{p['league'].lower()}:{mk}:under"
            e = final_probability(r["p_model"], None, r["p_hist"], seg, r["hist_n"])
            conf = "Low" if r["role_shift"] and e.confidence != "Low" else e.confidence
            return {**p, **r, "player_id": pid, "market": mk, "segment": seg, "p_final": e.p, "confidence": conf,
                    "rating": rating(e.p, conf), "notes": e.notes}
        except Exception as ex:
            return {**p, "error": f"{type(ex).__name__}"}

    with cf.ThreadPoolExecutor(6) as ex:
        out = list(ex.map(one, props))
    return out
