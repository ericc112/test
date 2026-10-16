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
Each take also carries its pulse: every change in the stat with the play and the game clock (NHL, MLB and NBA from the
play-by-play; other sports from the box-score changes the watcher sees).
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


# ------------------------------------------------------------------ pulse: every change in the stat, play by play
# Each tick: k (play id), f (share of regulation played), c (game clock), x (the play), d (change), v (total after it),
# at (wall-clock time: the feed's own, or when the watcher first saw it, or estimated from the clock)
GAME_MIN = {"nhl": 150, "nba": 140, "mlb": 180, "nfl": 195, "cfb": 210, "soccer": 115}   # wall-clock length, to place ticks
HIT_TB = {"single": 1, "double": 2, "triple": 3, "home_run": 4}
NHL_PULSE = ("skater_sog", "skater_goals", "skater_assists", "skater_points", "skater_hits", "skater_blocks", "goalie_saves")
MLB_PULSE = ("batter_total_bases", "batter_hits", "batter_singles", "batter_home_runs", "batter_strikeouts", "batter_walks",
             "batter_hrr", "batter_fs_pp", "pitcher_strikeouts", "pitcher_hits_allowed", "pitcher_walks")
NBA_PULSE = {"points": ("pts",), "rebounds": ("reb",), "assists": ("ast",), "threes": ("3pm",), "pra": ("pts", "reb", "ast"),
             "pts_asts": ("pts", "ast"), "pts_rebs": ("pts", "reb"), "rebs_asts": ("reb", "ast")}


def _mins(s: str) -> float:
    try:
        m, x = str(s).split(":")
        return int(m) + float(x) / 60
    except ValueError:
        return 0.0


def _short(t: str, n: int = 90) -> str:
    t = " ".join(str(t or "").split())
    return t if len(t) <= n else t[:n - 1].rstrip() + "…"


def nhl_ticks(event_id: str, player_id: str, market: str, cache: dict) -> list | None:
    if market not in NHL_PULSE:
        return None
    pbp = cache.get(("nhlpbp", event_id)) or cache.setdefault(("nhlpbp", event_id), G._get(
        f"https://api-web.nhle.com/v1/gamecenter/{event_id}/play-by-play"))
    pid, out, v = int(player_id), [], 0
    for p in pbp.get("plays", []):
        t, d = p.get("typeDescKey"), p.get("details") or {}
        shot = f" ({d['shotType']})" if d.get("shotType") else ""
        hit = None
        if market == "skater_sog" and t == "shot-on-goal" and d.get("shootingPlayerId") == pid:
            hit = "Shot on goal" + shot
        elif market == "skater_sog" and t == "goal" and d.get("scoringPlayerId") == pid:
            hit = "Goal" + shot
        elif market in ("skater_goals", "skater_points") and t == "goal" and d.get("scoringPlayerId") == pid:
            hit = "Goal" + shot
        elif market in ("skater_assists", "skater_points") and t == "goal" and pid in (d.get("assist1PlayerId"), d.get("assist2PlayerId")):
            hit = "Assist"
        elif market == "skater_hits" and t == "hit" and d.get("hittingPlayerId") == pid:
            hit = "Hit"
        elif market == "skater_blocks" and t == "blocked-shot" and d.get("blockingPlayerId") == pid:
            hit = "Blocked shot"
        elif market == "goalie_saves" and t == "shot-on-goal" and d.get("goalieInNetId") == pid:
            hit = "Save" + shot
        if not hit:
            continue
        per = (p.get("periodDescriptor") or {}).get("number") or 1
        v += 1
        out.append({"k": f"nhl{p.get('eventId')}", "f": round(min(1.0, ((min(per, 3) - 1) * 20 + _mins(p.get("timeInPeriod", "0:00"))) / 60), 3),
                    "c": f"{_ord(per) if per <= 3 else 'OT'} {p.get('timeRemaining', '')}".strip(), "x": hit, "d": 1, "v": v})
    return out


def mlb_ticks(event_id: str, player_id: str, market: str, cache: dict) -> list | None:
    if market not in MLB_PULSE:
        return None
    pbp = cache.get(("mlbpbp", event_id)) or cache.setdefault(("mlbpbp", event_id), G._get(
        f"https://statsapi.mlb.com/api/v1/game/{event_id}/playByPlay"))
    pid, out, v = int(player_id), [], 0
    for p in pbp.get("allPlays", []):
        ab = p.get("about") or {}
        if not ab.get("isComplete"):
            continue
        r, m = p.get("result") or {}, p.get("matchup") or {}
        et, rbi = r.get("eventType") or "", r.get("rbi") or 0
        bat, pit = (m.get("batter") or {}).get("id"), (m.get("pitcher") or {}).get("id")
        scored = any((x.get("details") or {}).get("runner", {}).get("id") == pid and (x.get("movement") or {}).get("end") == "score"
                     for x in p.get("runners", []))
        tb, walk, k = HIT_TB.get(et, 0), et in ("walk", "intent_walk"), et.startswith("strikeout")
        d = 0
        if market.startswith("batter_"):
            if bat == pid:
                d = {"batter_total_bases": tb, "batter_hits": int(bool(tb)), "batter_singles": int(et == "single"),
                     "batter_home_runs": int(et == "home_run"), "batter_strikeouts": int(k), "batter_walks": int(walk),
                     "batter_hrr": int(bool(tb)) + rbi,
                     "batter_fs_pp": {1: 3, 2: 5, 3: 8, 4: 10}.get(tb, 0) + 2 * rbi + 2 * (walk or et == "hit_by_pitch")}[market]
            if scored and market in ("batter_hrr", "batter_fs_pp"):
                d += 1 if market == "batter_hrr" else 2                     # a run scored, his own at-bat or not
        elif pit == pid:
            d = {"pitcher_strikeouts": int(k), "pitcher_hits_allowed": int(bool(tb)), "pitcher_walks": int(walk)}[market]
        if not d:
            continue
        inn, half = ab.get("inning") or 1, ab.get("halfInning")
        v += d
        out.append({"k": f"mlb{ab.get('atBatIndex')}", "f": round(min(1.0, (inn - 1 + (0.25 if half == "top" else 0.75)) / 9), 3),
                    "c": f"{'Top' if half == 'top' else 'Bot'} {_ord(inn)}", "x": _short(r.get("description") or r.get("event")),
                    "d": d, "v": v, "at": ab.get("endTime")})
    return out


def nba_ticks(event_id: str, player_id: str, market: str, cache: dict) -> list | None:
    comps = NBA_PULSE.get(market)
    if not comps:
        return None
    s = cache.get(("nba", event_id)) or cache.setdefault(("nba", event_id), G._get(
        f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={event_id}"))
    pid, out, v = str(player_id), [], 0
    for p in s.get("plays", []):
        parts = [str((x.get("athlete") or {}).get("id")) for x in p.get("participants", [])]
        typ, sv = (p.get("type") or {}).get("text", ""), p.get("scoreValue") or 0
        scoring = bool(p.get("scoringPlay"))
        d = 0
        if "pts" in comps and scoring and parts[:1] == [pid]:
            d += sv
        if "3pm" in comps and scoring and parts[:1] == [pid] and sv == 3:
            d += 1
        if "reb" in comps and "Rebound" in typ and parts[:1] == [pid]:
            d += 1
        if "ast" in comps and scoring and len(parts) > 1 and parts[1] == pid and "Free Throw" not in typ:
            d += 1
        if not d:
            continue
        per = (p.get("period") or {}).get("number") or 1
        clock = (p.get("clock") or {}).get("displayValue", "")
        v += d
        out.append({"k": f"nba{p.get('id')}", "f": round(min(1.0, ((min(per, 4) - 1) * 12 + 12 - _mins(clock if ":" in clock else "0:" + clock)) / 48), 3),
                    "c": f"{'Q' + str(per) if per <= 4 else 'OT'} {clock}".strip(), "x": _short(p.get("text")), "d": d, "v": v,
                    "at": p.get("wallclock")})
    return out


PULSE = {"nhl": nhl_ticks, "mlb": mlb_ticks, "nba": nba_ticks}


def ticks_for(sport: str, r: dict, gs: dict, value, cache: dict, mem: dict | None, now: dt.datetime, tid: str) -> list:
    """The take's ticks, newest last: from the play-by-play where we read it, else each change the watcher saw in the box."""
    fn = PULSE.get(sport)
    out = None
    if fn and gs["state"] in ("in", "post"):
        try:
            out = fn(str(r["event_id"]), r["player_id"], r["market"], cache)
        except Exception:
            out = None
    if out is None:                                         # no play-by-play reader: the box score's changes, as seen
        if mem is None:
            return []
        dt_ = mem.setdefault("dticks", {}).setdefault(tid, [])
        last = dt_[-1]["v"] if dt_ else 0
        if value is not None and value != last and gs["state"] in ("in", "post"):
            d = value - last
            dt_.append({"k": f"box{len(dt_)}", "f": gs.get("frac"), "c": gs.get("detail", ""), "x": f"{'+' if d > 0 else ''}{d:g} in the box score",
                        "d": d, "v": value, "at": now.strftime("%Y-%m-%dT%H:%M:%SZ")})
        out = list(dt_)
    start = _when(gs.get("start"))
    seen = mem.setdefault("seen", {}) if mem is not None else {}
    first = mem is not None and not mem.get("primed")
    for t in out:
        if t.get("at"):
            continue
        key = f"{tid}:{t['k']}"
        if key not in seen:
            est = start + dt.timedelta(minutes=(t.get("f") or 0) * GAME_MIN.get(sport, 150)) if start else now
            seen[key] = (min(est, now) if (first or mem is None) else now).strftime("%Y-%m-%dT%H:%M:%SZ")
        t["at"] = seen[key]
    return out[-25:]


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


def snapshot(takes: list[dict], bets: dict, now: dt.datetime | None = None, mem: dict | None = None) -> dict:
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
        ticks = ticks_for(sport, r, gs, value, cache, mem, now, t["id"])
        items.append({**item, "value": value, "status": status, "need": need, "pace": pace, "state": gs["state"],
                      "detail": gs["detail"], "score": gs["score"], "frac": None if gs["frac"] is None else round(gs["frac"], 3),
                      "sport": sport, "ticks": ticks})
    order = {"live": 0, "hit": 1, "dead": 2, "pre": 3, "miss": 4, "push": 5, "void": 6, "unknown": 7}
    items.sort(key=lambda i: (order.get(i["status"], 9), i.get("start") or "", i["player"]))
    live_n = sum(i.get("state") == "in" for i in items)
    if mem is not None:
        mem["primed"] = True
    return {"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "in_progress": live_n, "items": items}


def load_bets(path: str = None) -> dict:
    path = path or os.path.join(os.path.dirname(__file__), "..", "data", "bets.csv")
    return {r["id"]: r for r in csv.DictReader(open(path))}


def _sig(doc: dict) -> list:
    return [(i["id"], i.get("value"), i.get("status"), i.get("detail"), len(i.get("ticks") or [])) for i in doc["items"]]


def run(takes_dir: str, out: str, watch: int = 0, max_minutes: int = 300) -> dict:
    takes, bets = take_rows(takes_dir), load_bets()
    memf = out + ".mem.json"                                # tick times and box-score changes survive a restart
    try:
        mem = json.load(open(memf))
    except (OSError, ValueError):
        mem = {}
    doc = snapshot(takes, bets, mem=mem)
    json.dump(mem, open(memf, "w"))
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
            doc = snapshot(takes, bets, mem=mem)
            json.dump(mem, open(memf, "w"))
        except Exception as e:
            print(f"live error {type(e).__name__}", flush=True)
            continue
        sig = _sig(doc)
        if sig != last:
            json.dump(doc, open(out, "w"), separators=(",", ":"))
            changed = [i for i in doc["items"] if (i["id"], i.get("value"), i.get("status"), i.get("detail"), len(i.get("ticks") or [])) not in set(last)]
            print(f"live {doc['updated']} in_progress {doc['in_progress']} changed {len(changed)}", flush=True)
            last = sig
    return doc
