"""Live state of the user's takes: python -m edge live TAKES_DIR --out LIVE.json [--watch SECONDS]

TAKES_DIR holds the page's `takes` as ArtifactData listed them. For every open take on a game that has started or starts
within 12 hours, the game's live box score gives the stat so far, the clock and the score, and the take reads as:
  pre    not started yet
  live   in progress, still open (with what it needs and the pace when the game clock says how far along it is)
  hit    already over the line on an over (it can't lose), or a final that cleared
  dead   already over the line on an under (it can't win)
  miss / push / void   finished
LIVE.json is the page's `live/now` document. With --watch the file is rewritten every SECONDS while any game is live, and a
line is printed whenever a take's number or status changes (a Monitor turns each line into an upload).
"""
from __future__ import annotations

import csv
import datetime as dt
import glob
import json
import math
import os
import time

from . import grade as G

HORIZON_H = 12


def _espn_state(s: dict) -> dict:
    comp = s["header"]["competitions"][0]
    st = comp["status"]
    cs = sorted(comp["competitors"], key=lambda c: c.get("homeAway") != "away")
    score = " – ".join(f"{(c.get('team') or {}).get('abbreviation', '')} {c.get('score', '')}".strip() for c in cs)
    return {"state": st["type"]["state"], "detail": st["type"].get("shortDetail") or st["type"].get("detail", ""),
            "score": score, "period": st.get("period") or 0, "clock": st.get("displayClock") or "", "start": comp.get("date")}


def _clock_frac(period: int, clock: str, periods: int, minutes: float) -> float | None:
    """Share of regulation played, from period and the clock counting down."""
    if not period:
        return None
    try:
        m, s = (clock or "0:00").split(":")
        left = int(m) + int(float(s)) / 60
    except ValueError:
        return None
    done = (min(period, periods) - 1) * minutes + max(0.0, minutes - left)
    return max(0.0, min(1.0, done / (periods * minutes)))


def _ord(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _when(s: str | None) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")) if s else None
    except ValueError:
        return None


def game_state(sport: str, event_id: str, cache: dict) -> dict:
    """{state: pre|in|post, detail, score, frac (share of regulation played, or None)}, from the payload the grader reads."""
    if sport == "nhl":
        b = cache.get(("nhl", event_id)) or cache.setdefault(("nhl", event_id), G._get(
            f"https://api-web.nhle.com/v1/gamecenter/{event_id}/boxscore"))
        gs = b.get("gameState")
        state = "post" if gs in ("OFF", "FINAL") else "in" if gs in ("LIVE", "CRIT") else "pre"
        per = (b.get("periodDescriptor") or {}).get("number") or 0
        clk = b.get("clock") or {}
        inter = clk.get("inIntermission")
        detail = "Final" if state == "post" else "" if state == "pre" else \
            (f"End of {_ord(per)}" if inter
             else f"P{per} {clk.get('timeRemaining', '')}" if per <= 3 else f"OT {clk.get('timeRemaining', '')}")
        score = f"{b['awayTeam']['abbrev']} {b['awayTeam'].get('score', 0)} – {b['homeTeam']['abbrev']} {b['homeTeam'].get('score', 0)}"
        frac = 1.0 if state == "post" else None if state == "pre" else \
            (min(per, 3) / 3 if inter else _clock_frac(per, clk.get("timeRemaining", ""), 3, 20))
        return {"state": state, "detail": detail, "score": score if state != "pre" else "", "frac": frac, "start": b.get("startTimeUTC")}
    if sport == "mlb":
        d = G._get(f"https://statsapi.mlb.com/api/v1/schedule?gamePk={event_id}&hydrate=linescore,team")
        g = d["dates"][0]["games"][0]
        ab = g["status"]["abstractGameState"]
        state = "post" if ab == "Final" else "in" if ab == "Live" else "pre"
        ls = g.get("linescore") or {}
        inn, half = ls.get("currentInning") or 0, ls.get("inningState") or ""
        t = g["teams"]
        score = f"{t['away']['team'].get('abbreviation', '')} {t['away'].get('score', 0)} – {t['home']['team'].get('abbreviation', '')} {t['home'].get('score', 0)}"
        detail = "Final" if state == "post" else "" if state == "pre" else f"{half} {_ord(inn)}".strip()
        frac = 1.0 if state == "post" else None if state == "pre" or not inn else \
            min(1.0, (inn - 1 + {"Top": 0.25, "Middle": 0.5, "Bottom": 0.75, "End": 1.0}.get(half, 0.5)) / 9)
        return {"state": state, "detail": detail, "score": score if state != "pre" else "", "frac": frac, "start": g.get("gameDate")}
    league = {"nfl": "football/nfl", "nba": "basketball/nba", "cfb": "football/college-football"}.get(sport)
    if league:
        key = ("cfb" if sport == "cfb" else sport, event_id)
        s = cache.get(key) or cache.setdefault(key, G._get(f"https://site.api.espn.com/apis/site/v2/sports/{league}/summary?event={event_id}"))
        e = _espn_state(s)
        frac = 1.0 if e["state"] == "post" else None if e["state"] == "pre" else \
            _clock_frac(e["period"], e["clock"], 4, 12 if sport == "nba" else 15)
        return {"state": e["state"], "detail": e["detail"] if e["state"] != "pre" else "", "score": e["score"] if e["state"] != "pre" else "",
                "frac": frac, "start": e["start"]}
    if sport == "soccer":
        key = ("soccer", event_id)
        s = cache.get(key) or cache.setdefault(key, G._get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={event_id}"))
        e = _espn_state(s)
        try:
            mins = float(str(e["clock"]).split("'")[0].split("+")[0])
        except ValueError:
            mins = None
        frac = 1.0 if e["state"] == "post" else None if e["state"] == "pre" or mins is None else min(1.0, mins / 90)
        return {"state": e["state"], "detail": e["detail"] if e["state"] != "pre" else "", "score": e["score"] if e["state"] != "pre" else "",
                "frac": frac, "start": e["start"]}
    return {"state": "unknown", "detail": "", "score": "", "frac": None}


def verdict(value: float | None, line: float, over: bool, state: str) -> tuple[str, str]:
    """(status, what it needs) for a take with `value` so far."""
    if value is None:
        return ("void", "didn't play") if state == "post" else ("pre" if state == "pre" else "live", "")
    if state == "post":
        if value == line:
            return "push", ""
        return ("hit" if (value > line) == over else "miss"), ""
    if over and value > line:
        return "hit", "cleared"
    if not over and value > line:
        return "dead", "over the line"
    if state == "pre":
        return "pre", ""
    if over:
        need = math.floor(line) + 1 - value
        return "live", f"needs {need:g} more"
    room = math.ceil(line) - 1 - value if line == int(line) else math.floor(line) - value
    return "live", ("can't add any more" if room <= 0 else f"{room:g} more allowed")


def take_rows(takes_dir: str) -> list[dict]:
    out = []
    for f in sorted(glob.glob(os.path.join(takes_dir, "**", "*.json"), recursive=True)):
        try:
            d = json.load(open(f))
        except ValueError:
            continue
        d = d.get("data", d)
        if d.get("player") and d.get("id"):
            out.append(d)
    return out


def snapshot(takes: list[dict], bets: dict, now: dt.datetime | None = None) -> dict:
    """The live/now document for the open takes."""
    now = now or dt.datetime.now(dt.timezone.utc)
    cache, states, items = {}, {}, []
    for t in takes:
        if t.get("status") not in (None, "", "new", "pending", "logged", "open"):
            continue
        r = bets.get(str(t.get("bets_id") or ""))
        if not r or not r.get("event_id"):
            continue
        start = _when(t.get("start"))
        if start and (start - now).total_seconds() > HORIZON_H * 3600:
            continue
        sport, ev = r["sport"], str(r["event_id"])
        item = {"id": t["id"], "bets_id": r["id"], "player": t["player"], "stat": t.get("stat"), "line": float(t["line"]),
                "side": t.get("side"), "lg": t.get("lg"), "rating": t.get("rating"), "start": t.get("start"), "ty": t.get("ty")}
        try:
            if (sport, ev) not in states:
                states[(sport, ev)] = game_state(sport, ev, cache)
            gs = states[(sport, ev)]
            gstart = _when(gs.get("start")) or start
            if gs["state"] == "pre" and gstart and (gstart - now).total_seconds() > HORIZON_H * 3600:
                continue                                # the take had no start time: the game's own says it's not today
            value = None
            if gs["state"] in ("in", "post") and sport in G.GRADERS:
                st, v = G.GRADERS[sport](ev, r["player_id"], r["market"], cache, live=True)
                value = v if st == "final" else (0.0 if gs["state"] == "in" else None)
        except Exception as e:  # one feed down shouldn't blank the others
            items.append({**item, "status": "unknown", "note": f"live feed unavailable ({type(e).__name__})"})
            continue
        over = str(r["side"]).lower() in ("over", "more")
        status, need = verdict(value, item["line"], over, gs["state"])
        pace = round(value / gs["frac"], 1) if value is not None and gs["state"] == "in" and (gs["frac"] or 0) >= 0.15 else None
        if not item["start"] and gstart:
            item["start"] = gstart.isoformat()
        items.append({**item, "value": value, "status": status, "need": need, "pace": pace, "state": gs["state"],
                      "detail": gs["detail"], "score": gs["score"], "frac": None if gs["frac"] is None else round(gs["frac"], 3)})
    order = {"live": 0, "hit": 1, "dead": 2, "pre": 3, "miss": 4, "push": 5, "void": 6, "unknown": 7}
    items.sort(key=lambda i: (order.get(i["status"], 9), i.get("start") or "", i["player"]))
    live_n = sum(i.get("state") == "in" for i in items)
    return {"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "in_progress": live_n, "items": items}


def load_bets(path: str = None) -> dict:
    path = path or os.path.join(os.path.dirname(__file__), "..", "data", "bets.csv")
    return {r["id"]: r for r in csv.DictReader(open(path))}


def _sig(doc: dict) -> list:
    return [(i["id"], i.get("value"), i.get("status"), i.get("detail")) for i in doc["items"]]


def run(takes_dir: str, out: str, watch: int = 0, max_minutes: int = 300) -> dict:
    takes, bets = take_rows(takes_dir), load_bets()
    doc = snapshot(takes, bets)
    json.dump(doc, open(out, "w"), separators=(",", ":"))
    print(f"live {doc['updated']} in_progress {doc['in_progress']} takes {len(doc['items'])}", flush=True)
    if not watch:
        return doc
    last, t0 = _sig(doc), time.time()
    while time.time() - t0 < max_minutes * 60:
        if doc["in_progress"] == 0 and not any(i["status"] == "pre" and i.get("start") and
                                               dt.datetime.fromisoformat(i["start"]) < dt.datetime.now(dt.timezone.utc)
                                               for i in doc["items"]):
            print("live done: no game in progress", flush=True)
            break
        time.sleep(watch)
        try:
            doc = snapshot(takes, bets)
        except Exception as e:
            print(f"live error {type(e).__name__}", flush=True)
            continue
        sig = _sig(doc)
        if sig != last:
            json.dump(doc, open(out, "w"), separators=(",", ":"))
            changed = [i for i in doc["items"] if (i["id"], i.get("value"), i.get("status"), i.get("detail")) not in set(last)]
            print(f"live {doc['updated']} in_progress {doc['in_progress']} changed {len(changed)}", flush=True)
            last = sig
    return doc
