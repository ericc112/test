"""Projected winners, night by night: every game's simulated winner, win chance and score, the betting favorite, and
(once played) the final and whether the simulation had it right. Shown on the Sim Lab's Winners tab.

Sources:
  NBA   data/nba_pretip/DATE.json (nba_pp.save_pretip: each game's last pre-tip prediction, with the projected score);
        nights before that existed fall back to the saved priced boards (win chance only).
  NHL   data/winners/nhl/DATE.json, NFL data/winners/nfl/DATE.json (save() from each pricer, pre-tip only). Both of those
        simulations start from the betting line (NHL goal rates from the moneyline and total, the NFL drive model
        calibrated toward the spread), so their winners mostly follow the favorite; the NBA engine rates teams itself.
Finals come from ESPN's scoreboards (NBA from the box scores the kit already caches)."""
from __future__ import annotations

import datetime as dt
import glob
import gzip
import json
import os

import numpy as np

from .blend import HERE

WIN_DIR = os.path.join(HERE, "data", "winners")
PRETIP_DIR = os.path.join(HERE, "data", "nba_pretip")
SITE = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_PATH = {"nba": "basketball/nba", "nhl": "hockey/nhl", "nfl": "football/nfl"}


def _us_date(iso: str) -> str:
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (t.astimezone(dt.timezone.utc) - dt.timedelta(hours=10)).strftime("%Y-%m-%d")


def _imp(a):
    if a is None:
        return None
    a = float(a)
    return 100 / (a + 100) if a > 0 else -a / (-a + 100)


def novig(ml_home, ml_away):
    a, b = _imp(ml_home), _imp(ml_away)
    return a / (a + b) if a and b else None


def save(sport: str, gid: str, home: str, away: str, start: str, home_pts, away_pts, ml_home=None, ml_away=None, spread=None, total=None) -> None:
    """Keep one game's pre-tip projection (ignored once the game has started). home_pts / away_pts: per-run scores."""
    now = dt.datetime.now(dt.timezone.utc)
    if dt.datetime.fromisoformat(start.replace("Z", "+00:00")) <= now:
        return
    h, a = np.asarray(home_pts, float), np.asarray(away_pts, float)
    rec = {"gid": str(gid), "home": home, "away": away, "start": start, "pulled": now.strftime("%Y-%m-%dT%H:%MZ"),
           "p_home": float((h > a).mean() + 0.5 * (h == a).mean()), "mean_home": float(h.mean()), "mean_away": float(a.mean()),
           "ml_home": ml_home, "ml_away": ml_away, "spread": spread, "total": total}
    d = os.path.join(WIN_DIR, sport); os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{_us_date(start)}.json")
    cur = json.load(open(path)) if os.path.exists(path) else {}
    cur[str(gid)] = rec
    json.dump(cur, open(path, "w"))


def _nba_nights(dates: list[str]) -> dict:
    out = {}
    for d in dates:
        p = os.path.join(PRETIP_DIR, f"{d}.json")
        recs = {}
        if os.path.exists(p):
            for gid, r in json.load(open(p)).items():
                if r.get("start") and _us_date(r["start"]) == d:
                    recs[gid] = {k: r.get(k) for k in ("gid", "home", "away", "start", "pulled", "p_home", "mean_home", "mean_away", "ml_home", "ml_away", "spread", "total")}
        bp = os.path.join(HERE, "data", "nba_boards", f"{d}.json.gz")       # fallback: win chance from the priced board
        if os.path.exists(bp):
            for r in json.load(gzip.open(bp, "rt")):
                gid = str(r.get("event_id")); pulled = r.get("pulled") or ""
                if gid in recs or r.get("p_home") is None or not r.get("start") or _us_date(r["start"]) != d:
                    continue
                tip = dt.datetime.fromisoformat(r["start"]).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
                if pulled and pulled <= tip:
                    g = (r.get("game") or " @ ").split(" @ ")
                    recs[gid] = {"gid": gid, "away": g[0], "home": g[-1], "start": r["start"], "pulled": pulled, "p_home": r["p_home"]}
        if recs:
            out[d] = recs
    return out


def _saved_nights(sport: str, dates: list[str]) -> dict:
    out = {}
    for d in dates:
        p = os.path.join(WIN_DIR, sport, f"{d}.json")
        if os.path.exists(p):
            out[d] = json.load(open(p))
    return out


def _finals(sport: str, date: str) -> dict:
    """{gid: {home_score, away_score, final, ml_home, ml_away}} for one US date."""
    out = {}
    if sport == "nba":
        try:
            from gamesim import data as gs_data, nba as gnba
            d = dt.date.fromisoformat(date)
            for g in gnba.season_games("nba", d.strftime("%Y%m%d"), (d + dt.timedelta(days=1)).strftime("%Y%m%d")):
                if gs_data.us_day(g["date"]) == date:
                    ln = g.get("line") or {}
                    out[g["id"]] = {"home_score": g["score"]["home"], "away_score": g["score"]["away"], "final": g["final"],
                                    "ml_home": ln.get("ml_home"), "ml_away": ln.get("ml_away"), "spread": ln.get("spread_home")}
        except Exception:
            pass
        return out
    from .grade import _get
    d = dt.date.fromisoformat(date)
    for dd in (d, d + dt.timedelta(days=1)):
        try:
            sb = _get(f"{SITE}/{ESPN_PATH[sport]}/scoreboard?dates={dd.strftime('%Y%m%d')}")
        except Exception:
            continue
        for ev in sb.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            t = {c["homeAway"]: c for c in comp.get("competitors", [])}
            if "home" not in t:
                continue
            out[ev["id"]] = {"home_score": float(t["home"].get("score") or 0), "away_score": float(t["away"].get("score") or 0),
                             "final": comp.get("status", {}).get("type", {}).get("completed", False)}
    return out


def export(days: int = 14, today: str | None = None) -> dict:
    from gamesim.data import slate_today
    today = today or slate_today()
    t0 = dt.date.fromisoformat(today)
    dates = [(t0 - dt.timedelta(days=k)).isoformat() for k in range(days)] + [(t0 + dt.timedelta(days=1)).isoformat()]
    nights = {}
    for sport in ("nba", "nhl", "nfl"):
        src = _nba_nights(dates) if sport == "nba" else _saved_nights(sport, dates)
        for date, recs in src.items():
            fin = _finals(sport, date) if date <= today else {}
            for gid, r in recs.items():
                f = fin.get(gid) or {}
                mh = novig(r.get("ml_home") or f.get("ml_home"), r.get("ml_away") or f.get("ml_away"))
                g = {"sport": sport, "gid": gid, "home": r.get("home"), "away": r.get("away"), "start": r.get("start"),
                     "p_home": None if r.get("p_home") is None else round(float(r["p_home"]), 3),
                     "proj": None if r.get("mean_home") is None else [round(float(r["mean_away"]), 1), round(float(r["mean_home"]), 1)],
                     "market_home": None if mh is None else round(mh, 3), "spread": r.get("spread") if r.get("spread") is not None else f.get("spread")}
                if f.get("final"):
                    g["final"] = [f["away_score"], f["home_score"]]
                    hw = f["home_score"] > f["away_score"]
                    if g["p_home"] is not None:
                        g["sim_right"] = (g["p_home"] > 0.5) == hw
                    if mh is not None:
                        g["market_right"] = (mh > 0.5) == hw
                nights.setdefault(date, []).append(g)
    out = []
    for date in sorted(nights, reverse=True):
        G = sorted(nights[date], key=lambda g: (g["start"] or "", g["sport"]))
        done = [g for g in G if "final" in g]
        rec = lambda k: [sum(1 for g in done if g.get(k) is True), sum(1 for g in done if g.get(k) is False)]
        out.append({"date": date, "games": G, "sim": rec("sim_right"), "market": rec("market_right")})
    tot = lambda k: [sum(n[k][0] for n in out), sum(n[k][1] for n in out)]
    by_sport = {}
    for s in ("nba", "nhl", "nfl"):
        done = [g for n in out for g in n["games"] if g["sport"] == s and "final" in g]
        if done:
            by_sport[s] = {"sim": [sum(1 for g in done if g.get("sim_right") is True), sum(1 for g in done if g.get("sim_right") is False)],
                           "market": [sum(1 for g in done if g.get("market_right") is True), sum(1 for g in done if g.get("market_right") is False)]}
    return {"today": today, "nights": out, "record": {"sim": tot("sim"), "market": tot("market"), "by_sport": by_sport},
            "pulled": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
