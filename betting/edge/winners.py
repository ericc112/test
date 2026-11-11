"""Projected winners, night by night: every game's simulated winner, win chance and score, the betting favorite, and
(once played) the final and whether the simulation had it right. Shown on the Sim Lab's Winners tab.

Sources:
  NBA   data/nba_pretip/DATE.json (nba_pp.save_pretip: each game's last pre-tip prediction, with the projected score);
        nights before that existed fall back to the saved priced boards (win chance only).
  NHL   data/winners/nhl/DATE.json, NFL data/winners/nfl/DATE.json (save() from each pricer, pre-tip only). Both of those
        simulations start from the betting line (NHL goal rates from the moneyline and total, the NFL drive model
        calibrated toward the spread), so their winners mostly follow the favorite; the NBA engine rates teams itself.
  Tennis data/winners/tennis/DATE.json (tennis_watch.save_winners, by Central European date): win chance, the projected
        winner's most likely exact scoreline, the set split and expected games. "away" is player A, "home" player B.
Finals come from ESPN's scoreboards (NBA from the box scores the kit already caches; tennis from Tennis Explorer's
results pages, matched on both players' page ids)."""
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


def _set_games(x: str) -> int:
    """Tennis Explorer set cell -> games ('63' is 6 games with 3 tiebreak points on the loser's side)."""
    v = int(x)
    return int(x[0]) if v > 7 else v


def _tennis_finals(date: str, recs: dict) -> dict:
    """{gid: final} for saved tennis matches on one Central European date, from Tennis Explorer's results pages (the
    winner is listed first). A match with an unfinished set count is final only once well past its start (a
    retirement); otherwise it is still being played."""
    from . import tennis as T, tennis_market as TM
    from .tennis_watch import TE_TZ
    d0 = dt.date.fromisoformat(date)
    now = dt.datetime.now(dt.timezone.utc)
    today_cet = now.astimezone(TE_TZ).date()
    rows = []
    for tour in sorted({r.get("tour") for r in recs.values() if r.get("tour")}):
        for d in (d0, d0 + dt.timedelta(days=1)):          # a match moved to the next day (rain, late finish)
            if d > today_cet:
                continue
            path = os.path.join(T.TE_DIR, f"te_{tour}_{d.isoformat()}.html")
            done_by = dt.datetime.combine(d + dt.timedelta(days=2), dt.time(), TE_TZ).timestamp()
            stale = os.path.exists(path) and os.path.getmtime(path) < done_by
            try:
                rows += TM.day(d, tour, T.TE_DIR, max_age=1800 if stale else 10 ** 9)
            except Exception:
                continue
    by_slug = {}
    for x in rows:
        if x.get("slug1") and x.get("slug2"):
            by_slug.setdefault(frozenset((x["slug1"], x["slug2"])), x)
    out = {}
    for gid, r in recs.items():
        sl = r.get("slugs") or []
        x = by_slug.get(frozenset(sl)) if len(sl) == 2 else None
        if not x:
            continue
        try:
            s1, s2 = int(x.get("s1") or 0), int(x.get("s2") or 0)
            g1, g2 = [_set_games(v) for v in x.get("g1") or []], [_set_games(v) for v in x.get("g2") or []]
        except ValueError:
            continue
        need = (r.get("best_of") or 3) // 2 + 1
        started = dt.datetime.fromisoformat(r["start"]) if r.get("start") else now
        ret = max(s1, s2) < need
        if ret and now < started + dt.timedelta(hours=5):
            continue
        a_won = x["slug1"] == sl[0]
        sets = list(zip(g1, g2))                              # winner's games first
        out[gid] = {"final": True, "winner": "a" if a_won else "b", "ret": ret,
                    "sets_won": [s1, s2] if a_won else [s2, s1],
                    "line": ", ".join(f"{a}-{b}" for a, b in sets if a or b) + (" ret." if ret else ""),
                    "odds": [x.get("o1"), x.get("o2")] if a_won else [x.get("o2"), x.get("o1")]}
    return out


def _tennis_games(nights: dict, today: str) -> None:
    from .tennis_watch import TE_TZ
    t_cet = dt.datetime.now(dt.timezone.utc).astimezone(TE_TZ).date().isoformat()
    for date, recs in _saved_nights("tennis", sorted(nights.get("__dates__", []))).items():
        fin = _tennis_finals(date, recs) if date <= t_cet else {}
        for gid, r in recs.items():
            f = fin.get(gid) or {}
            pa = r.get("p_a")
            ma = r.get("market_a")
            if ma is None and f.get("odds") and all(f["odds"]):        # closing price from the results page
                o_a, o_b = f["odds"]
                ma = (1 / o_a) / (1 / o_a + 1 / o_b)
            g = {"sport": "tennis", "gid": gid, "tour": r.get("tour"), "event": r.get("event"), "surface": r.get("surface"),
                 "away": r.get("away"), "home": r.get("home"), "start": r.get("start"),
                 "p_home": None if pa is None else round(1 - float(pa), 3),
                 "market_home": None if ma is None else round(1 - float(ma), 3),
                 "proj": r.get("games"), "line": r.get("line"), "line_p": r.get("line_p"), "sets": r.get("sets"),
                 "length": r.get("length"), "top": r.get("top"),
                 "rates": r.get("rates"), "best_of": r.get("best_of", 3),
                 "p_home_ratings": None if r.get("p_a_ratings") is None else round(1 - float(r["p_a_ratings"]), 3)}
            if f.get("final"):
                hw = f["winner"] == "b"
                g["final"] = [f["sets_won"][0], f["sets_won"][1]] if f["winner"] == "a" else [f["sets_won"][1], f["sets_won"][0]]
                g["final_line"] = f["line"]; g["final_winner"] = f["winner"]; g["ret"] = f["ret"]
                if g["p_home"] is not None:
                    g["sim_right"] = (g["p_home"] > 0.5) == hw
                if g["market_home"] is not None and g["market_home"] != 0.5:
                    g["market_right"] = (g["market_home"] > 0.5) == hw
            nights.setdefault(date, []).append(g)


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
    nights["__dates__"] = dates
    try:
        _tennis_games(nights, today)
    except Exception:
        pass
    nights.pop("__dates__", None)
    out = []
    for date in sorted(nights, reverse=True):
        ts = lambda g: dt.datetime.fromisoformat(g["start"].replace("Z", "+00:00")).timestamp() if g.get("start") else 0
        G = sorted(nights[date], key=lambda g: (ts(g), g["sport"]))
        done = [g for g in G if "final" in g]
        rec = lambda k: [sum(1 for g in done if g.get(k) is True), sum(1 for g in done if g.get(k) is False)]
        out.append({"date": date, "games": G, "sim": rec("sim_right"), "market": rec("market_right")})
    tot = lambda k: [sum(n[k][0] for n in out), sum(n[k][1] for n in out)]
    by_sport = {}
    for s in ("nba", "nhl", "nfl", "tennis"):
        done = [g for n in out for g in n["games"] if g["sport"] == s and "final" in g]
        if done:
            by_sport[s] = {"sim": [sum(1 for g in done if g.get("sim_right") is True), sum(1 for g in done if g.get("sim_right") is False)],
                           "market": [sum(1 for g in done if g.get("market_right") is True), sum(1 for g in done if g.get("market_right") is False)]}
    return {"today": today, "nights": out, "record": {"sim": tot("sim"), "market": tot("market"), "by_sport": by_sport},
            "pulled": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
