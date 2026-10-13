"""Post-mortem for every graded loss: what happened, which input failed, and what to change.

Every loss (bets, leans, passes and user entries alike) gets a diagnosis in data/postmortems.csv,
built from the official stat feeds, and a confirmed root-cause tag in bets.csv (`edge tag`).
POSTMORTEMS.md is the readable log. `edge learn` turns repeated causes into rules and confidence caps.
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict

from .blend import HERE
from .grade import _get
from .odds import implied

PM_PATH = os.path.join(HERE, "data", "postmortems.csv")
PM_MD_PATH = os.path.join(HERE, "POSTMORTEMS.md")
PM_FIELDS = ["id", "date", "sport", "event_id", "player", "market", "side", "line", "result", "p_final", "confidence",
             "action", "margin", "near_miss", "sources", "against_market", "clv", "detail", "auto_tag", "linked", "evidence", "lesson"]

TAGS = {
    "variance": "inputs held up (role, volume, price); the outcome landed on the wrong side",
    "opportunity": "far less volume than projected: early hook, ice-time cut, blowout, injury exit, lost plate appearances",
    "correlated": "lost because another leg's game script failed; the root cause is recorded on that leg",
    "role/lineup": "role, line or batting-slot assumption was wrong",
    "model bias": "we sided with the model against the market and the market was right",
    "market info": "the line moved against us after we priced it: the market knew something we didn't",
    "stale line": "we priced off an outdated line or number",
    "data error": "a stat, side or sample was wrong",
    "format misread": "misread what the contest or line scores",
}
NO_RULE_TAGS = {"variance", "correlated"}  # these never trigger a new checklist rule or a confidence cap

VOLUME_OVERS = {"pitcher_outs", "pitcher_pitches", "pitcher_strikeouts", "pitcher_hits_allowed", "pitcher_walks"}


def _f(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


def _sign(side: str) -> int:
    return 1 if side.lower() == "over" else -1


def losses(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r.get("status") == "lost"]


# ------------------------------------------------------------------ per-sport detail from the feeds
def _mlb_detail(r: dict, cache: dict) -> dict:
    eid, pid = r["event_id"], int(r["player_id"])
    if ("mlb_box", eid) not in cache:
        cache[("mlb_box", eid)] = _get(f"https://statsapi.mlb.com/api/v1/game/{eid}/boxscore")
    box = cache[("mlb_box", eid)]
    side = next((s for s in ("home", "away") if f"ID{pid}" in box["teams"][s]["players"]), None)
    if side is None:
        return {}
    me = box["teams"][side]["players"][f"ID{pid}"]
    d = {}
    if r["market"].startswith("pitcher_") or r["market"] == "first_inning_pitches":
        s = me["stats"].get("pitching") or {}
        bf, pitches = s.get("battersFaced") or 0, s.get("numberOfPitches") or 0
        d = {"role": "pitcher", "outs": s.get("outs"), "bf": bf, "pitches": pitches, "h": s.get("hits"), "er": s.get("earnedRuns"),
             "bb": s.get("baseOnBalls"), "k": s.get("strikeOuts"), "p_per_pa": round(pitches / bf, 2) if bf else None,
             "started": bool(box["teams"][side]["pitchers"]) and box["teams"][side]["pitchers"][0] == pid}
        d["opportunity"] = d["outs"] if r["market"] == "pitcher_outs" else bf
        return d
    s = me["stats"].get("batting") or {}
    opp = "away" if side == "home" else "home"
    st_id = box["teams"][opp]["pitchers"][0] if box["teams"][opp]["pitchers"] else None
    st = box["teams"][opp]["players"].get(f"ID{st_id}", {}) if st_id else {}
    sp = st.get("stats", {}).get("pitching", {})
    d = {"role": "batter", "pa": s.get("plateAppearances"), "slot": (int(me.get("battingOrder", "0")) // 100) or None,
         "h": s.get("hits"), "r": s.get("runs"), "rbi": s.get("rbi"), "bb": s.get("baseOnBalls"),
         "opp_starter": st.get("person", {}).get("fullName"), "opp_starter_id": st_id,
         "opp_starter_outs": sp.get("outs"), "opp_starter_er": sp.get("earnedRuns")}
    d["opportunity"] = d["pa"]
    if ("mlb_pbp", eid) not in cache:
        cache[("mlb_pbp", eid)] = _get(f"https://statsapi.mlb.com/api/v1/game/{eid}/playByPlay")
    pa_log, vs_starter, total = [], 0, 0
    hits = ("single", "double", "triple", "home_run")
    for p in cache[("mlb_pbp", eid)]["allPlays"]:
        pit = p["matchup"]["pitcher"]
        if p["matchup"]["batter"]["id"] == pid and p["result"].get("type") == "atBat":
            rbi = p["result"].get("rbi") or 0
            hit = p["result"].get("eventType") in hits
            pa_log.append(f"inn {p['about']['inning']} vs {pit['fullName'].split()[-1]}: {p['result'].get('event')}" + (f", {rbi} RBI" if rbi else ""))
            total += rbi + hit
            vs_starter += (rbi + hit) if pit["id"] == st_id else 0
        for x in p.get("runners", []):  # runs scored, charged to the pitcher who let him on
            if x["details"]["runner"]["id"] == pid and x["movement"].get("end") == "score":
                resp = (x["details"].get("responsiblePitcher") or {}).get("id") or pit["id"]
                pa_log.append(f"scored inn {p['about']['inning']} ({'starter' if resp == st_id else 'bullpen'})")
                total += 1
                vs_starter += resp == st_id
    d["pa_log"], d["hrr_vs_starter"], d["hrr_total"] = pa_log, vs_starter, total
    return d


def _nhl_detail(r: dict, cache: dict) -> dict:
    eid = r["event_id"]
    if ("nhl_box", eid) not in cache:
        cache[("nhl_box", eid)] = _get(f"https://api-web.nhle.com/v1/gamecenter/{eid}/boxscore")
    b = cache[("nhl_box", eid)]
    for side in ("homeTeam", "awayTeam"):
        for grp in ("forwards", "defense", "goalies"):
            for p in b["playerByGameStats"][side].get(grp, []):
                if str(p["playerId"]) == str(r["player_id"]):
                    toi = p.get("toi") or "0:00"
                    m, s = toi.split(":")
                    d = {"role": grp, "toi": round(int(m) + int(s) / 60, 1), "sog": p.get("sog"), "shifts": p.get("shifts"),
                         "pp_goals": p.get("powerPlayGoals"), "score": f"{b['awayTeam'].get('score')}-{b['homeTeam'].get('score')}"}
                    d["opportunity"] = d["toi"]
                    return d
    return {}


def _cs2_detail(r: dict, cache: dict) -> dict:
    games = sorted(_get(f"https://api.bo3.gg/api/v1/games?filter%5Bgames.match_id%5D%5Beq%5D={r['event_id']}")["results"],
                   key=lambda g: g.get("number") or 0)
    maps, rounds = [], 0
    for g in [g for g in games if g.get("number") in (1, 2)]:
        for p in _get(f"https://api.bo3.gg/api/v1/games/{g['id']}/players_stats") or []:
            nick = ((p.get("steam_profile") or {}).get("player") or {}).get("nickname") or (p.get("steam_profile") or {}).get("nickname")
            if str(nick).lower() == str(r["player_id"]).lower():
                maps.append(f"{g.get('map_name')}: {g.get('rounds_count')} rds, {'W' if p.get('win') else 'L'}, {p.get('kills')} K / {p.get('headshots')} HS")
                rounds += g.get("rounds_count") or 0
    return {"role": "cs2", "maps": maps, "opportunity": rounds} if maps else {}


def _soccer_detail(r: dict, cache: dict) -> dict:
    from .grade import soccer_player_stats
    eid = r["event_id"]
    if ("soccer_sum", eid) not in cache:
        cache[("soccer_sum", eid)] = _get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={eid}")
    s = cache[("soccer_sum", eid)]
    for ro in s.get("rosters", []):
        for p in ro.get("roster", []):
            if str(p["athlete"]["id"]) == str(r["player_id"]):
                st = soccer_player_stats(s["header"]["league"]["slug"], eid, ro["team"]["id"], r["player_id"])
                team = next(({x["name"]: x.get("displayValue") for x in t.get("statistics", [])}
                             for t in s["boxscore"]["teams"] if str(t["team"]["id"]) == str(ro["team"]["id"])), {})
                score = " - ".join(f"{c['team']['abbreviation']} {c.get('score')}" for c in s["header"]["competitions"][0]["competitors"])
                return {"role": "soccer", "minutes": st.get("minutes"), "passes": (st.get("accuratePasses") or 0) + (st.get("inaccuratePasses") or 0),
                        "team_passes": team.get("totalPasses"), "possession": team.get("possessionPct"), "saves": st.get("saves"),
                        "score": score, "opportunity": st.get("minutes")}
    return {}


def _lol_detail(r: dict, cache: dict) -> dict:
    """Game by game: result, his kills vs what the model expected for that result, and the game's total kills."""
    import re
    from . import lol
    need = len(re.search(r"_m(\d+)$", r["market"]).group(1))
    m = cache.get(("lol", r["event_id"])) or lol.match_by_id(int(r["event_id"]))
    allg = lol.player_games(r["player_id"])
    games = lol.series_games(allg, m["start_date"])[:need]
    if not games:
        return {}
    prior = [g for g in allg if g["date"] < games[0]["date"]][:40]  # the model's sample: his 40 games before the series
    mw = sum(g["k"] for g in prior if g["win"]) / max(1, sum(g["win"] for g in prior))
    ml = sum(g["k"] for g in prior if not g["win"]) / max(1, sum(not g["win"] for g in prior))
    maps, exp, tot = [], 0.0, []
    for i, g in enumerate(games, 1):
        teams = lol.game_teams(g["game"])
        both = sum(k for _, _, k in teams)
        tot.append(both)
        e = mw if g["win"] else ml
        exp += e
        maps.append(f"G{i} {'W' if g['win'] else 'L'}: {g['k']} K (expected {e:.1f}); "
                    + " - ".join(f"{t} {k}" for t, _, k in teams) + f", {both} total")
    return {"role": "lol", "maps": maps, "expected": round(exp, 1), "game_kills": tot, "opportunity": None}


DETAIL = {"mlb": _mlb_detail, "nhl": _nhl_detail, "cs2": _cs2_detail, "soccer": _soccer_detail, "lol": _lol_detail}


# ------------------------------------------------------------------ diagnosis
def _sources(r: dict) -> tuple[str, bool]:
    """Which sources were on our side (all components are stored for the side we evaluated)."""
    out, against_market = [], False
    for k, lab in (("p_model", "model"), ("p_market", "market"), ("p_hist", "hist")):
        v = _f(r.get(k))
        if v is not None:
            out.append(f"{lab} {v:.0%}{'' if v > 0.5 else ' (against)'}")
            if k == "p_market" and v < 0.5:
                against_market = True
    return ", ".join(out) or "none logged", against_market


def _near_miss(r: dict, result: float) -> bool:
    line = _f(r["line"])
    if line is None:
        return False
    if line >= 30:  # yards, pitches: within 5% of the line
        return abs(result - line) <= 0.05 * line
    return abs(result - line) <= 0.5


def diagnose(r: dict, detail: dict) -> dict:
    """Single-leg diagnosis. Cross-leg linking (correlated) happens in review()."""
    result, line, side = _f(r.get("result_value")), _f(r.get("line")), r.get("side", "over")
    p = _f(r.get("p_final"))
    margin = None if result is None or line is None else round((result - line) * _sign(side), 2)
    near = result is not None and _near_miss(r, result)
    sources, against_market = _sources(r)
    clv = None
    if _f(r.get("closing_price")) is not None and _f(r.get("price")) is not None:
        clv = round(implied(_f(r["closing_price"])) - implied(_f(r["price"])), 3)
    ev, tag = [], None
    if p is not None and p < 0.5:
        ev.append(f"we priced this side at {p:.0%}: losing was the more likely outcome")
    if r.get("action") == "pass":
        ev.append("logged as a PASS: no money on it; reviewed for calibration")
    opp_proj, opp = _f(r.get("opp_proj")), detail.get("opportunity")
    if opp_proj and opp is not None and _sign(side) > 0 and opp < 0.75 * opp_proj:
        tag = "opportunity"
        ev.append(f"opportunity {opp} vs {opp_proj:g} projected ({opp / opp_proj:.0%})")
    if tag is None and detail.get("role") == "pitcher" and r["market"] in VOLUME_OVERS and _sign(side) > 0 and (detail.get("outs") or 0) < 12:
        tag = "opportunity"
        ev.append(f"pulled after {detail['outs']} outs ({detail['pitches']} pitches, {detail['bf']} BF, {detail['p_per_pa']} P/PA)")
    if tag is None and detail.get("role") == "batter" and _sign(side) > 0 and (detail.get("pa") or 9) <= 2:
        tag = "opportunity"
        ev.append(f"only {detail['pa']} plate appearances")
    if detail.get("role") == "pitcher" and tag is None:
        ev.append(f"line: {detail.get('outs')} outs, {detail.get('bf')} BF, {detail.get('pitches')} pitches, "
                  f"{detail.get('h')} H, {detail.get('bb')} BB, {detail.get('k')} K, {detail.get('er')} ER")
    if detail.get("role") == "batter":
        ev.append(f"{detail.get('pa')} PA from the {detail.get('slot')} slot; opposing starter {detail.get('opp_starter')} "
                  f"went {detail.get('opp_starter_outs')} outs / {detail.get('opp_starter_er')} ER")
        if r["market"] == "batter_hrr" and detail.get("hrr_total"):
            pen = detail["hrr_total"] - detail["hrr_vs_starter"]
            ev.append(f"{detail['hrr_vs_starter']} of {detail['hrr_total']} H+R+RBI came off the starter, {pen} off the bullpen"
                      + (" (the bullpen part alone beat the line: not just the starter's fault)" if _sign(side) < 0 and pen > (line or 0) else ""))
    if detail.get("role") == "lol" and detail.get("expected") is not None:
        ev.append(f"{result:g} kills vs {detail['expected']} expected for the actual game results; "
                  f"games had {'/'.join(str(k) for k in detail.get('game_kills', []))} total kills")
    if tag is None and against_market and (_f(r.get("p_model")) or 0) > 0.5:
        tag = "model bias"
        ev.append("model was on our side, the market was against it, and the market was right")
    if tag is None and clv is not None and clv <= -0.03:
        tag = "market info"
        ev.append(f"line moved {clv * 100:+.1f} pts against us before close")
    if tag is None:
        tag = "variance"
        if near:
            ev.append("closest possible loss (missed by the minimum)")
    return {"margin": margin, "near_miss": near, "sources": sources, "against_market": against_market, "clv": clv,
            "auto_tag": tag, "evidence": ev}


def _starter_blown_up(d: dict) -> bool:
    return d.get("role") == "batter" and (d.get("opp_starter_outs") or 99) < 15 and (d.get("opp_starter_er") or 0) >= 3


def _hinges_on_starter(r: dict, d: dict) -> bool:
    """A hitter under lost *because* the starter was knocked out only if what he did off the bullpen alone
    would not have beaten the line."""
    if not (_starter_blown_up(d) and r.get("side") == "under"):
        return False
    if r.get("market") == "batter_hrr" and d.get("hrr_total") is not None:
        return d["hrr_total"] - d.get("hrr_vs_starter", 0) <= (_f(r.get("line")) or 0)
    return True


def link(rows: list[dict], details: dict) -> dict:
    """Group losses that rode on one game script: same event and (same player, same group, or a hitter under
    vs a starter who was knocked out while we also lost a leg on that starter)."""
    parent = {r["id"]: r["id"] for r in rows}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_event = defaultdict(list)
    for r in rows:
        by_event[(r.get("date"), r.get("event_id"))].append(r)
    for legs in by_event.values():
        for i, a in enumerate(legs):
            for b in legs[i + 1:]:
                da, db = details.get(a["id"], {}), details.get(b["id"], {})
                same = a.get("player_id") == b.get("player_id") or (a.get("group") and a.get("group") == b.get("group"))
                vs = (_hinges_on_starter(a, da) and str(da.get("opp_starter_id")) == str(b.get("player_id"))) or \
                     (_hinges_on_starter(b, db) and str(db.get("opp_starter_id")) == str(a.get("player_id")))
                # two hitters both burned by the same knocked-out starter
                both = _hinges_on_starter(a, da) and _hinges_on_starter(b, db) and da.get("opp_starter_id") == db.get("opp_starter_id")
                if same or vs or both:
                    parent[find(a["id"])] = find(b["id"])
    comps = defaultdict(list)
    for r in rows:
        comps[find(r["id"])].append(r["id"])
    return {i: sorted(c, key=int) for c in comps.values() for i in c}


def review(rows: list[dict], ids: list[str] | None = None, fetch=True, cache: dict | None = None,
           details: dict | None = None) -> list[dict]:
    """Diagnose every loss (or just `ids`). Returns post-mortem records; does not change bets.
    `details` (id -> feed detail) skips the network, for tests or replays."""
    cache = {} if cache is None else cache
    lost = losses(rows)
    if ids:  # linking only needs the other losses from the same games
        events = {(r.get("date"), r.get("event_id")) for r in lost if r["id"] in ids}
        lost = [r for r in lost if (r.get("date"), r.get("event_id")) in events]
    given, details = details or {}, {}
    for r in lost:
        fn = DETAIL.get(r.get("sport", "").lower())
        d = given.get(r["id"], {})
        if not d and fetch and fn and r.get("event_id") and r.get("player_id"):
            try:
                d = fn(r, cache)
            except Exception as e:  # feed problem: review what we have
                d = {"error": type(e).__name__}
        details[r["id"]] = d
    diag = {r["id"]: diagnose(r, details[r["id"]]) for r in lost}
    groups = link(lost, details)
    out = []
    for r in lost:
        if ids and r["id"] not in ids:
            continue
        dg = diag[r["id"]]
        grp = groups[r["id"]]
        if len(grp) > 1:
            # the root cause sits on one leg: an opportunity loss if there is one, otherwise the earliest leg
            primary = next((i for i in grp if diag[i]["auto_tag"] == "opportunity"), grp[0])
            if r["id"] != primary:
                dg["evidence"].insert(0, f"same game script as #{primary} ({diag[primary]['auto_tag']}); own read: {dg['auto_tag']}")
                dg["auto_tag"] = "correlated"
            else:
                dg["evidence"].insert(0, f"root leg of a {len(grp)}-leg script loss: {', '.join('#' + i for i in grp)}")
        d = details[r["id"]]
        det = "; ".join(d.get("pa_log", []) or d.get("maps", [])) or ", ".join(
            f"{k}={v}" for k, v in d.items() if k not in ("role", "opportunity", "opp_starter_id", "started"))
        out.append({"id": r["id"], "date": r.get("date", ""), "sport": r.get("sport", ""), "event_id": r.get("event_id", ""),
                    "player": r.get("player", ""), "market": r.get("market", ""), "side": r.get("side", ""), "line": r.get("line", ""),
                    "result": r.get("result_value", ""), "p_final": r.get("p_final", ""), "confidence": r.get("confidence", ""),
                    "action": r.get("action", ""), "margin": dg["margin"], "near_miss": dg["near_miss"], "sources": dg["sources"],
                    "against_market": dg["against_market"], "clv": "" if dg["clv"] is None else dg["clv"], "detail": det,
                    "auto_tag": dg["auto_tag"], "linked": " ".join(grp) if len(grp) > 1 else "", "evidence": " | ".join(dg["evidence"]),
                    "lesson": ""})
    return out


# ------------------------------------------------------------------ storage
def read_pm(path: str = PM_PATH) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def write_pm(pms: dict, path: str = PM_PATH) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PM_FIELDS, extrasaction="ignore")
        w.writeheader()
        for k in sorted(pms, key=int):
            w.writerow({f: pms[k].get(f, "") for f in PM_FIELDS})


def merge(new: list[dict], old: dict) -> dict:
    """New diagnoses replace old ones but keep any lesson already written."""
    out = dict(old)
    for pm in new:
        pm["lesson"] = old.get(pm["id"], {}).get("lesson", "") or pm.get("lesson", "")
        out[pm["id"]] = pm
    return out


def render_md(pms: dict, rows: list[dict], path: str = PM_MD_PATH) -> str:
    tags = {r["id"]: r.get("miss_reason", "") for r in rows}
    by_date = defaultdict(list)
    for pm in pms.values():
        by_date[pm["date"]].append(pm)
    lines = ["# Post-mortems", "",
             "Every graded loss is examined here, including passes and Low-confidence legs. "
             "`python -m edge review` writes the diagnosis; `python -m edge tag ID \"tag\" --lesson \"...\"` confirms the cause. "
             "Tags: " + ", ".join(f"`{t}`" for t in TAGS) + ".", ""]
    for date in sorted(by_date, reverse=True):
        legs = sorted(by_date[date], key=lambda p: int(p["id"]))
        roots = {p["linked"] for p in legs if p["linked"]}
        indep = len([p for p in legs if not p["linked"]]) + len(roots)
        lines += [f"## {date}: {len(legs)} losses from {indep} independent causes", "",
                  "| # | Leg | Result | Our p | Action | Sources | Auto tag | Confirmed | Evidence |", "|---|---|---|---|---|---|---|---|---|"]
        for p in legs:
            lines.append(f"| {p['id']} | {p['player']} {p['market']} {p['side']} {p['line']} | {p['result']} | {p['p_final']} ({p['confidence']}) | "
                         f"{p['action']} | {p['sources']} | {p['auto_tag']} | {tags.get(p['id']) or '**untagged**'} | {p['evidence'].replace(' | ', '; ')} |")
        les = [p for p in legs if p.get("lesson")]
        if les:
            lines += ["", "Lessons:"] + [f"- #{p['id']}: {p['lesson']}" for p in les]
        det = [p for p in legs if p.get("detail")]
        if det:
            lines += ["", "Detail from the feeds:"] + [f"- #{p['id']} {p['player']}: {p['detail']}" for p in det]
        lines.append("")
    text = "\n".join(lines)
    if path:
        with open(path, "w") as f:
            f.write(text)
    return text


def summary(pms: list[dict]) -> str:
    out = []
    for p in pms:
        out.append(f"#{p['id']} {p['player']} {p['market']} {p['side']} {p['line']} -> {p['result']} "
                   f"(p {p['p_final']}, {p['confidence']}, {p['action']}) | auto tag: {p['auto_tag']}")
        out.append(f"    sources: {p['sources']}")
        for e in p["evidence"].split(" | "):
            if e:
                out.append(f"    - {e}")
        if p.get("detail"):
            out.append(f"    detail: {p['detail']}")
    return "\n".join(out)
