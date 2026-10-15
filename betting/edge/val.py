"""Valorant maps 1-2 kills and first bloods, priced from vlr.gg match pages and bo3.gg series odds (no keys).

Same simulation as cs2.py: each map is won with the per-map probability inverted from the Bo3 moneyline (bo3.gg,
discipline 2); rounds come from the two teams' recent maps with that result; kills ~ Poisson(kills per round for that
result x rounds x form noise) and first bloods ~ Poisson(first bloods per round x rounds). Rates use the current roster's
maps (at least 4 of today's 5), regressed toward the player's longer-run numbers. A player new to the team, or with few
maps on it, is flagged (L5).

vlr.gg's robots.txt allows match, team and player pages (only /search/auto and /rr/ are disallowed). Requests are spaced
out, and finished match pages are cached on disk, so a slate costs one fetch per new match.
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import html
import os
import re
import threading
import time
import urllib.request

import numpy as np

from . import cs2
from .blend import HERE
from .grade import _CTX

V = "https://www.vlr.gg"
CACHE = os.path.join(HERE, ".cache", "vlr")
GENERIC = {"kills": 0.72, "fb": 0.10}       # pro averages per round: the prior for players with little data
WIN_MULT = {"kills": (1.10, 0.88), "fb": (1.12, 0.86)}
FORM_CV = 0.08
THIN_MAPS = 8
_LOCK, _LAST = threading.Lock(), [0.0]


def page(path: str, cache: bool = False) -> str:
    """One vlr.gg page. Spaced at least 0.6 s apart; finished match pages come from disk after the first read."""
    f = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9]+", "_", path)[:150] + ".html")
    if cache and os.path.exists(f):
        with open(f, encoding="utf-8") as fh:
            return fh.read()
    with _LOCK:
        wait = 0.6 - (time.time() - _LAST[0])
        if wait > 0:
            time.sleep(wait)
        _LAST[0] = time.time()
    for i in range(3):
        try:
            req = urllib.request.Request(V + path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=_CTX, timeout=30) as r:
                body = r.read().decode("utf-8", "replace")
            break
        except Exception:
            if i == 2:
                raise
            time.sleep(2 * (i + 1))
    if cache:
        os.makedirs(CACHE, exist_ok=True)
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(body)
    return body


def _txt(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


# ------------------------------------------------------------------ vlr.gg pages
def upcoming() -> list[dict]:
    """Upcoming and live matches: id, path, the two team names."""
    h = page("/matches")
    out = []
    for m in re.finditer(r'<a href="(/(\d+)/[^"]+)" class="wf-module-item match-item[^"]*"(.*?)</a>', h, re.S):
        names = [_txt(x) for x in re.findall(r'class="match-item-vs-team-name">\s*<div class="text-of">(.*?)</div>', m.group(3), re.S)]
        if len(names) == 2:
            out.append({"id": m.group(2), "path": m.group(1), "teams": names})
    return out


def find_match(team: str, opp: str) -> dict | None:
    return next((m for m in upcoming() if any(cs2.same_name(team, n) for n in m["teams"])
                 and any(cs2.same_name(opp, n) for n in m["teams"])), None)


def parse_match(h: str) -> dict:
    """A match page: date, Bo, the two teams (id, name) and every played map with each player's kills and first bloods."""
    ts = re.search(r'data-utc-ts="([\d\- :]+)"', h)
    bo = re.search(r">\s*Bo(\d)\s*<", h)
    teams = re.findall(r'match-header-link wf-link-hover mod-[12]"\s+href="/team/(\d+)/[^"]*"\s*>.*?<div class="wf-title-med[^"]*">(.*?)</div>', h, re.S)
    order = [g for g, dis in re.findall(r'vm-stats-gamesnav-item[^"]*"\s+data-game-id="(\d+)"\s+data-disabled="(\d)"', h) if dis == "0"]
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'<div class="vm-stats-game[^"]*" data-game-id="(\w+)">', h)]
    blocks = {gid: h[a:(starts[i + 1][0] if i + 1 < len(starts) else len(h))] for i, (a, gid) in enumerate(starts)}
    maps = []
    for num, gid in enumerate(order or [g for _, g in starts if g != "all"], start=1):
        b = blocks.get(gid)
        if not b:
            continue
        names = [_txt(x) for x in re.findall(r'class="team-name">(.*?)</div>', b, re.S)][:2]
        scores = [("mod-win" in c, int(v)) for c, v in re.findall(r'<div class="score([^"]*)"[^>]*>\s*(\d+)\s*</div>', b)[:2]]
        mname = re.search(r'class="map-name">\s*<span[^>]*>\s*([A-Za-z]+)', b)
        players = []
        for chunk in b.split('ovw-player-name text-of">')[1:]:
            nick = _txt(chunk.split("</div>", 1)[0])
            k = re.search(r'data-col="kills"><span class="side mod-both">(\d+)<', chunk)
            fb = re.search(r'data-col="fb"><span class="stats-sq"><span class="side mod-both[^"]*">(\d+)<', chunk)
            if nick and k:
                players.append({"nick": nick, "kills": int(k.group(1)), "fb": int(fb.group(1)) if fb else None})
        if len(names) < 2 or len(scores) < 2 or len(players) < 10:
            continue
        rounds = scores[0][1] + scores[1][1]
        for i, p in enumerate(players[:10]):
            side = 0 if i < 5 else 1
            p.update({"team": names[side], "opp": names[1 - side], "win": scores[side][0]})
        maps.append({"num": num, "game": gid, "map": mname.group(1) if mname else "", "rounds": rounds, "players": players[:10]})
    return {"date": ts.group(1)[:10] if ts else "", "bo": int(bo.group(1)) if bo else 3,
            "teams": [{"id": t, "name": _txt(n)} for t, n in teams[:2]], "maps": maps, "final": ">final<" in h.replace("\n", "").replace("\t", "")}


def team_maps(team_id: str, n: int = 25) -> list[dict]:
    """Player-map rows (both sides) from the team's last n completed matches."""
    h = page(f"/team/matches/{team_id}/?group=completed")
    paths = list(dict.fromkeys(re.findall(r'<a href="(/\d+/[^"/?]+)" class="wf-card fc-flex m-item">', h)))[:n]

    def one(path):
        try:
            m = parse_match(page(path, cache=True))
        except Exception:
            return []
        mid = path.split("/")[1]
        return [{"date": m["date"], "match": mid, "bo": m["bo"], "game": mp["game"], "num": mp["num"], "rounds": mp["rounds"],
                 "team_id": cs2.norm(p["team"]), "team": p["team"], "opp": p["opp"], "nick": p["nick"], "kills": p["kills"],
                 "fb": p["fb"], "win": p["win"]}
                for mp in m["maps"] if mp["rounds"] >= 13 for p in mp["players"]]

    with cf.ThreadPoolExecutor(3) as ex:
        return [r for rows in ex.map(one, paths) for r in rows]


# ------------------------------------------------------------------ pricing
def price(player_rows: list[dict], all_rows: list[dict], p_map: float, rounds_w, rounds_l, stat: str, line: float,
          maps: int = 2, n: int = 200_000, seed: int = 23) -> dict:
    """stat 'kills' or 'fb' over the first `maps` maps of the series."""
    rng = np.random.default_rng(seed)
    S = lambda x: sum(r[stat] or 0 for r in x if r[stat] is not None)
    R = lambda x: sum(r["rounds"] for r in x if r[stat] is not None)
    g = GENERIC[stat]
    rall = (S(all_rows) + g * 300) / (R(all_rows) + 300)
    mw, ml = WIN_MULT[stat]
    w = [r for r in player_rows if r["win"]]
    lo = [r for r in player_rows if not r["win"]]
    rw = (S(w) + rall * mw * 300) / (R(w) + 300)
    rl = (S(lo) + rall * ml * 300) / (R(lo) + 300)
    win = rng.random((n, maps)) < p_map
    rounds = np.where(win, rng.choice(rounds_w, (n, maps)), rng.choice(rounds_l, (n, maps)))
    x = rng.poisson(np.where(win, rw, rl) * rounds * rng.gamma(1 / FORM_CV ** 2, FORM_CV ** 2, (n, maps))).sum(1)
    by = collections.defaultdict(dict)
    meta = {}
    for r in player_rows:
        if r["num"] <= maps and (r.get("bo") or 3) >= 3 and r[stat] is not None:
            by[r["match"]][r["num"]] = r[stat]
            meta[r["match"]] = (r["date"], r["opp"])
    series = {m: sum(v.values()) for m, v in by.items() if len(v) == maps}
    games = sorted(({"d": meta[m][0], "o": meta[m][1], "h": None, "v": v} for m, v in series.items()), key=lambda gm: gm["d"], reverse=True)
    return {"p_over": float((x > line).mean()), "p_under": float((x < line).mean()), "p_push": float((x == line).mean()),
            "mean": float(x.mean()), "median": float(np.median(x)), "series": list(series.values()), "games": games,
            "hist_over": sum(v > line for v in series.values()), "hist_under": sum(v < line for v in series.values()),
            "rate_w": rw, "rate_l": rl, "maps": len(player_rows)}


def price_match(team: str, opp: str, props: list[dict]) -> list[dict]:
    """props: dicts with player, team (name), stat ('kills'|'fb'), line, maps (2 = maps 1-2). Pricing attached."""
    m = find_match(team, opp)
    if not m:
        return [{**p, "error": "match not found on vlr.gg"} for p in props]
    head = parse_match(page(m["path"]))
    if len(head["teams"]) < 2:
        return [{**p, "error": "teams not on the vlr.gg match page"} for p in props]
    data = {}
    for t in head["teams"]:
        rows = team_maps(t["id"])
        five, era = cs2.current_era(rows, cs2.norm(t["name"]))
        data[t["name"]] = {"rows": rows, "five": five, "era": era, "key": cs2.norm(t["name"])}
    bo3 = None
    try:
        bo3 = cs2.find_match(team, opp, disc=2)
    except Exception:
        pass
    out = []
    for p in props:
        tname = next((nm for nm in data if cs2.same_name(nm, p["team"])), None)
        if tname is None:
            out.append({**p, "error": "team not matched"})
            continue
        me = data[tname]
        oname = next(nm for nm in data if nm != tname)
        ps = None
        if bo3:
            tid = next((((bo3.get(k) or {}).get("id")) for k in ("team1", "team2") if cs2.same_name((bo3.get(k) or {}).get("name") or "", tname)), None)
            ps = cs2.series_win_prob(bo3, tid) if tid else None
        p_map = cs2.map_p_from_series(ps) if ps is not None else 0.5
        rw = [r["rounds"] for r in me["era"] if r["win"]] + [r["rounds"] for r in data[oname]["era"] if not r["win"]]
        rl = [r["rounds"] for r in me["era"] if not r["win"]] + [r["rounds"] for r in data[oname]["era"] if r["win"]]
        prow = [r for r in me["era"] if cs2.same_name(r["nick"], p["player"])]
        allr = [r for r in me["rows"] if cs2.same_name(r["nick"], p["player"]) and r["team_id"] == me["key"]]
        if not prow:
            out.append({**p, "error": "no maps found for player with this roster"})
            continue
        r = price(prow, allr or prow, p_map, np.array(rw or [23]), np.array(rl or [23]), p["stat"], p["line"], p.get("maps", 2))
        out.append({**p, **r, "event_id": m["id"], "match": m["path"], "p_series": ps, "p_map": p_map,
                    "newcomer": False, "thin": len(prow) < THIN_MAPS, "date": head["date"]})
    return out


# ------------------------------------------------------------------ grading (event_id = vlr.gg match id, player_id = nick)
def result(event_id: str, player: str, stat: str, maps: int = 2) -> tuple[str, float | None]:
    """('final', value) once maps 1..maps are posted; 'void' if the series ended sooner or he didn't play them."""
    h = page(f"/{event_id}/")
    m = parse_match(h)
    if not m["final"]:
        return "pending", None
    got = [mp for mp in m["maps"] if mp["num"] <= maps]
    if len(got) < maps:
        return "void", None
    vals = [p[stat] for mp in got for p in mp["players"] if cs2.same_name(p["nick"], player) and p[stat] is not None]
    return ("final", float(sum(vals))) if len(vals) == maps else ("void", None)
