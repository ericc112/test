"""Moneyline breakdowns: every factor behind a game, for the page's Breakdown sheet. python -m edge ml notes

For each game on the ML board, ESPN's game report gives:
  market      DraftKings moneyline (open -> now where ESPN shows both), spread, total; ESPN's Matchup Predictor
  form        last five results with scores, goals/points for and against, days of rest, streak
  table       standing, record, points for/against per game; against-the-spread record (NFL, CFB, MLB)
  head to head  the last meetings and the series summary
  availability  injury reports (NFL, MLB: out, doubtful, questionable, IL), MLB probable starters with their numbers
  team stats  season averages (NFL, CFB) and each team's leaders
  setting     venue, neutral site, weather where ESPN reports it, and ESPN's preview
Plus our own numbers (book, model, blended chance, fair price, EV, rating) and, for each side, the case for it and
the case against it, built from those facts. Nothing here is a guarantee: the write-up gives a probability.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import html
import json
import re

from . import grade as G

SITE = "https://site.api.espn.com/apis/site/v2/sports"
OUT_STATUSES = ("out", "doubtful", "questionable", "injured reserve", "il", "day-to-day", "suspension")


def _when(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def _txt(s: str, n: int) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    t = " ".join(t.split())
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def _num(v):
    try:
        return float(str(v).replace("+", ""))
    except (TypeError, ValueError):
        return None


def market(s: dict, comp: dict) -> dict:
    out = {}
    pc = (s.get("pickcenter") or [{}])[0] or {}
    o = next((x for x in (s.get("odds") or []) if isinstance(x, dict)), {}) or {}
    src = pc or o
    out["details"] = src.get("details")
    out["total"] = src.get("overUnder")
    out["spread"] = src.get("spread")
    ml = o.get("moneyline") or {}
    for side in ("home", "away", "draw"):
        leg = ml.get(side) if isinstance(ml.get(side), dict) else {}
        op, cl = _num((leg.get("open") or {}).get("odds")), _num((leg.get("close") or {}).get("odds"))
        if cl is None:
            t = pc.get(f"{side}TeamOdds") or ({} if side != "draw" else pc.get("drawOdds") or {})
            cl = _num(t.get("moneyLine"))
        if op is not None or cl is not None:
            out[side] = {"open": op, "now": cl}
    pr = s.get("predictor") or {}
    if pr.get("homeTeam"):
        out["predictor"] = {"home": _num(pr["homeTeam"].get("gameProjection")), "away": _num((pr.get("awayTeam") or {}).get("gameProjection"))}
    return out


def last_five(s: dict, team_id: str, now: dt.datetime) -> dict:
    blk = next((x for x in s.get("lastFiveGames") or [] if str((x.get("team") or {}).get("id")) == team_id), None)
    if not blk:
        return {}
    games, pf, pa = [], [], []
    evs = sorted(blk.get("events", []), key=lambda e: e.get("gameDate") or "")[-5:]   # oldest -> newest
    for e in evs:
        home = str(e.get("homeTeamId")) == team_id
        us, them = (e.get("homeTeamScore"), e.get("awayTeamScore")) if home else (e.get("awayTeamScore"), e.get("homeTeamScore"))
        try:
            pf.append(float(us)), pa.append(float(them))
        except (TypeError, ValueError):
            pass
        games.append({"d": (e.get("gameDate") or "")[:10], "opp": (e.get("opponent") or {}).get("abbreviation") or (e.get("opponent") or {}).get("displayName"),
                      "at": e.get("atVs"), "score": f"{us}-{them}", "r": e.get("gameResult"), "comp": e.get("leagueAbbreviation")})
    last = _when(evs[-1].get("gameDate")) if evs else None
    return {"games": games[::-1], "form": "".join(g["r"] or "?" for g in games),          # list newest first; form reads oldest -> newest
            "pf": round(sum(pf) / len(pf), 2) if pf else None, "pa": round(sum(pa) / len(pa), 2) if pa else None,
            "rest": (now - last).days if last else None}


def table_row(s: dict, team_id: str) -> dict:
    for g in (s.get("standings") or {}).get("groups", []):
        entries = (g.get("standings") or {}).get("entries", [])
        for i, e in enumerate(entries):
            if str(e.get("id")) == team_id:
                st = {x.get("name"): x.get("displayValue", x.get("value")) for x in e.get("stats", [])}
                return {"pos": i + 1, "of": len(entries), "group": g.get("header") or (s.get("standings") or {}).get("header"),
                        "w": st.get("wins"), "l": st.get("losses"), "d": st.get("ties"), "pts": st.get("points"),
                        "pf": st.get("pointsFor"), "pa": st.get("pointsAgainst"), "gp": st.get("gamesPlayed")}
    return {}


def injuries(s: dict, team_id: str, n: int = 8) -> list:
    blk = next((x for x in s.get("injuries") or [] if str((x.get("team") or {}).get("id")) == team_id), None)
    out = []
    for i in (blk or {}).get("injuries", []):
        st = str(i.get("status") or "")
        if not any(k in st.lower() for k in OUT_STATUSES):
            continue
        a = i.get("athlete") or {}
        out.append({"name": a.get("displayName"), "pos": ((a.get("position") or {}).get("abbreviation")), "status": st,
                    "what": ((i.get("details") or {}).get("type") or i.get("type") or {}).get("description") if isinstance((i.get("details") or {}).get("type") or i.get("type"), dict) else (i.get("details") or {}).get("type")})
    return out[:n]


def leaders(s: dict, team_id: str, n: int = 3) -> list:
    blk = next((x for x in s.get("leaders") or [] if str((x.get("team") or {}).get("id")) == team_id), None)
    out = []
    for cat in (blk or {}).get("leaders", [])[:n]:
        top = (cat.get("leaders") or [{}])[0]
        a = top.get("athlete") or {}
        if a:
            out.append({"cat": cat.get("displayName"), "name": a.get("displayName"), "value": top.get("displayValue")})
    return out


def team_stats(s: dict, team_id: str) -> list:
    for t in (s.get("boxscore") or {}).get("teams", []):
        if str((t.get("team") or {}).get("id")) == team_id:
            return [{"k": x.get("label") or x.get("name"), "v": x.get("displayValue")} for x in (t.get("statistics") or [])[:10]
                    if x.get("displayValue") not in (None, "")]
    return []


def ats(s: dict, team_id: str) -> str | None:
    blk = next((x for x in s.get("againstTheSpread") or [] if str((x.get("team") or {}).get("id")) == team_id), None)
    rec = (blk or {}).get("records") or []
    return "; ".join(f"{r.get('type', '')}: {r.get('summary', '')}".strip(": ") for r in rec[:3]) or None


def probable(comp: dict, team_id: str) -> dict | None:
    """MLB probable starter with his numbers (ESPN: statistics.splits.categories, or a plain list)."""
    c = next((x for x in comp.get("competitors", []) if str(x.get("id")) == team_id), None)
    for p in (c or {}).get("probables") or []:
        a = p.get("athlete") or {}
        raw = p.get("statistics")
        cats = ((raw.get("splits") or {}).get("categories") or []) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
        st = {}
        for x in cats:
            if isinstance(x, dict):
                st[x.get("abbreviation") or x.get("name")] = x.get("displayValue")
        if st.get("FI") is not None:
            st["IP"] = f"{st.get('FI')}.{st.get('PI') or 0}"
        keep = ("ERA", "W", "L", "IP", "K", "BB", "H", "HR", "WHIP")
        return {"name": a.get("displayName") or a.get("fullName"), "record": p.get("record") if isinstance(p.get("record"), str) else None,
                "stats": {k: st[k] for k in keep if st.get(k) not in (None, "")}}
    return None


def h2h(s: dict, home_id: str) -> dict:
    for ser in s.get("seasonseries") or []:
        evs = []
        for e in (ser.get("events") or [])[:5]:
            cs = e.get("competitors") or []
            sc = " ".join(f"{(c.get('team') or {}).get('abbreviation', '')} {c.get('score', '')}".strip() for c in cs)
            evs.append({"d": (e.get("date") or "")[:10], "score": sc, "status": ((e.get("statusType") or {}).get("shortDetail") or "")})
        return {"title": ser.get("title"), "summary": ser.get("summary"), "games": evs}
    return {}


def setting(s: dict, comp: dict) -> dict:
    gi = s.get("gameInfo") or {}
    v = gi.get("venue") or {}
    w = gi.get("weather") or {}
    addr = v.get("address") or {}
    out = {"venue": v.get("fullName"), "city": ", ".join(x for x in (addr.get("city"), addr.get("state") or addr.get("country")) if x),
           "neutral": bool(comp.get("neutralSite")), "grass": v.get("grass")}
    if w:
        out["weather"] = {k: w.get(k) for k in ("displayValue", "temperature", "highTemperature", "lowTemperature", "gust", "precipitation") if w.get(k) is not None}
    art = s.get("article") or {}
    if art.get("headline"):
        out["preview"] = {"headline": art.get("headline"), "text": _txt(art.get("story") or art.get("description") or "", 900)}
    return out


def _cases(team: str, opp: str, me: dict, them: dict, mk: dict, side: dict, home: bool, sport: str, draw_p: float | None) -> tuple[list, list]:
    """The case for a side and the case against it, from the facts gathered (numbers, not adjectives)."""
    pro, con = [], []
    f1, f2 = me.get("form") or {}, them.get("form") or {}
    w1, w2 = (f1.get("form") or "").count("W"), (f2.get("form") or "").count("W")
    if f1.get("form") and f2.get("form") and w1 != w2:
        (pro if w1 > w2 else con).append(f"Form: {team} {f1['form']} in their last {len(f1['form'])} (oldest to newest) vs {opp} {f2['form']}")
    if f1.get("pf") is not None and f2.get("pf") is not None and f1.get("pa") is not None and f2.get("pa") is not None:
        m1, m2 = f1["pf"] - f1["pa"], f2["pf"] - f2["pa"]
        unit = "goals" if sport == "soccer" else "runs" if sport == "mlb" else "points"
        (pro if m1 > m2 else con).append(f"Recent margin: {team} {m1:+.1f} {unit} a game over the last five, {opp} {m2:+.1f}")
    if home:
        pro.append(f"Home: {team} play at home" + (f" ({me.get('setting_venue')})" if me.get("setting_venue") else ""))
    elif home is False:
        con.append(f"Road: {team} are away from home")
    t1, t2 = me.get("table") or {}, them.get("table") or {}
    if t1.get("pos") and t2.get("pos") and t1.get("group") == t2.get("group"):
        (pro if t1["pos"] < t2["pos"] else con).append(f"Table: {team} {t1['pos']} of {t1['of']} vs {opp} {t2['pos']}")
    r1, r2 = (me.get("form") or {}).get("rest"), (them.get("form") or {}).get("rest")
    if r1 is not None and r2 is not None and abs(r1 - r2) >= 2:
        (pro if r1 > r2 else con).append(f"Rest: {team} get {r1} days since their last game by kickoff, {opp} {r2}")
    i1, i2 = me.get("injuries") or [], them.get("injuries") or []
    # fresh absences only: a 60-day IL or injured-reserve player has been out for weeks and is in the line already
    def big(xs):
        out = []
        for x in xs:
            st = str(x.get("status", "")).lower()
            if "60-day" in st or "injured reserve" in st or st == "ir":
                continue
            if st.startswith(("out", "doubt")) or "day-il" in st or "10-day" in st or "15-day" in st or st.startswith("questionable"):
                out.append(x)
        return out
    if big(i2):
        pro.append(f"{opp} injury list ({len(big(i2))}): " + ", ".join(f"{x['name']} ({x.get('pos') or ''} {x['status']})".replace(" )", ")") for x in big(i2)[:4]))
    if big(i1):
        con.append(f"{team} injury list ({len(big(i1))}): " + ", ".join(f"{x['name']} ({x.get('pos') or ''} {x['status']})".replace(" )", ")") for x in big(i1)[:4]))
    pr = mk.get("predictor") or {}
    mine = pr.get("home" if home else "away") if home is not None else None
    if mine is not None:
        (pro if mine >= 50 else con).append(f"ESPN's Matchup Predictor gives {team} {mine:.0f}%")
    leg = mk.get("home" if home else "away") or {}
    if leg.get("open") is not None and leg.get("now") is not None and leg["open"] != leg["now"]:
        moved_to = _imp(leg["now"]) > _imp(leg["open"])
        (pro if moved_to else con).append(f"Line move: {team} {leg['open']:+.0f} at open, {leg['now']:+.0f} now ({'money on them' if moved_to else 'drifting against them'})")
    if side.get("p_model") is not None and side.get("p_mkt") is not None:
        gap = side["p_model"] - side["p_mkt"]
        if abs(gap) >= 0.03:
            (pro if gap > 0 else con).append(f"Our model {side['p_model']:.0%} vs the book's {side['p_mkt']:.0%} ({gap:+.0%})")
    if side.get("ev") is not None:
        (pro if side["ev"] >= 0 else con).append(f"Price: {side['price']:+.0f} pays {'more' if side['ev'] >= 0 else 'less'} than our {side['p']:.0%} is worth (EV {side['ev']:+.1%}, fair {side['fair']:+d})")
    if draw_p:
        con.append(f"Draw risk: about {draw_p:.0%} of these end level, and a draw loses a moneyline")
    if sport in ("nfl", "cfb") and (me.get("table") or {}).get("gp"):
        pass
    return pro, con


def _imp(am: float) -> float:
    return 100 / (am + 100) if am > 0 else -am / (-am + 100)


def notes_for(g: dict, now: dt.datetime) -> dict:
    """Every factor for one board game (g: a game from ml.board())."""
    sport = g["sport"]
    base = {"id": g["id"], "lg": g["lg"], "sport": sport, "name": g["name"], "start": g["start"], "model": g.get("model"), "sides": g["sides"]}
    if sport == "tennis":
        return {**base, "teams": {}, "market": {}, "setting": {}, "note": "Tennis: the tennis model's view (Elo, surface, form, fatigue); ESPN has no tennis odds or previews."}
    path = {"nfl": "football/nfl", "cfb": "football/college-football", "mlb": "baseball/mlb", "soccer": "soccer/all"}[sport]
    s = G._get(f"{SITE}/{path}/summary?event={g['id']}")
    comp = s["header"]["competitions"][0]
    mk = market(s, comp)
    st = setting(s, comp)
    teams = {}
    for k in ("home", "away"):
        t = g[k]
        teams[k] = {"name": t["name"], "abbr": t.get("abbr"), "record": t.get("record"), "form": last_five(s, t["id"], _when(g["start"]) or now),
                    "table": table_row(s, t["id"]), "injuries": injuries(s, t["id"]), "leaders": leaders(s, t["id"]),
                    "stats": team_stats(s, t["id"]), "ats": ats(s, t["id"]), "starter": probable(comp, t["id"]) if sport == "mlb" else None}
    hh = h2h(s, g["home"]["id"])
    draw = next((x["p"] for x in g["sides"] if x["side"] == "draw"), None)
    cases = {}
    for side in g["sides"]:
        if side["side"] == "draw":
            continue
        k = side["side"]
        o = "away" if k == "home" else "home"
        me = dict(teams[k], setting_venue=st.get("venue") if k == "home" and not st.get("neutral") else None)
        pro, con = _cases(teams[k]["name"], teams[o]["name"], me, teams[o], mk, side, None if st.get("neutral") else k == "home", sport, draw)
        cases[k] = {"for": pro, "against": con}
    return {**base, "market": mk, "teams": teams, "h2h": hh, "setting": st, "cases": cases}


def build(b: dict, now: dt.datetime | None = None, workers: int = 8, ids: set | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    games = [g for g in b.get("games", []) if ids is None or g["id"] in ids]
    out = {}

    def one(g):
        try:
            return g["id"], notes_for(g, now)
        except Exception as e:
            return g["id"], {"id": g["id"], "lg": g["lg"], "name": g["name"], "error": f"{type(e).__name__}"}
    with cf.ThreadPoolExecutor(workers) as ex:
        for k, v in ex.map(one, games):
            out[k] = v
    return out


def pack(notes: dict, limit: int = 235_000) -> list[dict]:
    """Notes packed into documents under the db's 256 KB limit: [{games: {id: notes}}, ...]."""
    packs, cur, size = [], {}, 50
    for k, v in notes.items():
        n = len(json.dumps(v, separators=(",", ":"))) + len(k) + 6
        if cur and size + n > limit:
            packs.append({"games": cur})
            cur, size = {}, 50
        cur[k] = v
        size += n
    if cur:
        packs.append({"games": cur})
    return packs
