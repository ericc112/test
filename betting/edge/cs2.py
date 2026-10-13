"""CS2 maps 1-2 kills and headshots, priced from bo3.gg (no keys).

Each simulated map: the winner is drawn from the series market (per-map p inverted from the Bo3
moneyline), rounds come from the team's recent maps with that result, kills ~ Poisson(KPR for that
result x rounds x 8% form noise) and headshots ~ Binomial(kills, HS%). KPR in wins and losses and
HS% use the current roster's maps (at least 4 of today's 5 on the server), regressed toward the
player's longer-run numbers (300 rounds, 150 kills). A player new to the team is priced from his
previous team's maps and flagged (LESSONS L5).
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import difflib
import json
import os
import re
import time

import numpy as np

from .blend import HERE
from .grade import _get

B = "https://api.bo3.gg/api/v1"
CACHE = os.path.join(HERE, ".cache", "bo3")
FORM_CV, HS_CONC = 0.08, 200
GENERIC_KPR, GENERIC_HS = 0.70, 0.50   # pro-level averages: the prior for players with little data
THIN_MAPS = 8                            # fewer maps than this with the current roster = role unproven


# ------------------------------------------------------------------ helpers
def get(url: str, cache: bool = False, tries: int = 3):
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9]+", "_", url[len(B):])[:180] + ".json")
    if cache and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    for i in range(tries):
        try:
            out = _get(url)
            break
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))
    if cache and out:
        os.makedirs(CACHE, exist_ok=True)
        with open(path, "w") as f:
            json.dump(out, f)
    return out


def norm(nick: str) -> str:
    """'dev1ce' and 'device', 'EliGE' and 'EliGe' compare equal."""
    s = str(nick).lower().translate(str.maketrans("10345$", "ioeass"))
    return re.sub(r"[^a-z]", "", s)


def same_name(a: str, b: str) -> bool:
    na, nb = norm(a), norm(b)
    return na == nb or (len(na) > 3 and difflib.SequenceMatcher(None, na, nb).ratio() >= 0.85)


def map_p_from_series(p_series: float) -> float:
    """Per-map win probability p with p^2 (3 - 2p) = series win probability (Bo3)."""
    lo, hi = 0.0, 1.0
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if mid * mid * (3 - 2 * mid) < p_series else (lo, mid)
    return (lo + hi) / 2


# ------------------------------------------------------------------ bo3.gg data
def find_match(team_a: str, team_b: str | None = None) -> dict | None:
    for st in ("upcoming", "current"):
        d = get(f"{B}/matches?page%5Blimit%5D=100&sort=start_date&filter%5Bmatches.status%5D%5Bin%5D={st}"
                f"&filter%5Bmatches.discipline_id%5D%5Beq%5D=1&with=teams,tournament")
        for m in d["results"]:
            names = [(m.get("team1") or {}).get("name") or "", (m.get("team2") or {}).get("name") or ""]
            if any(same_name(team_a, n) for n in names) and (not team_b or any(same_name(team_b, n) for n in names)):
                return m
    return None


def series_win_prob(match: dict, team_id: int) -> float | None:
    bu = match.get("bet_updates") or {}
    t1, t2 = bu.get("team_1") or {}, bu.get("team_2") or {}
    if not t1.get("coeff") or not t2.get("coeff"):
        return None
    i1, i2 = 1 / t1["coeff"], 1 / t2["coeff"]
    p1 = i1 / (i1 + i2)
    return p1 if t1.get("team_id") == team_id else 1 - p1


def team_maps(team_id: int, n: int = 30) -> list[dict]:
    """Player-map rows (both sides) for the team's last n finished matches. Finished games are cached on disk."""
    ms = []
    for side in ("team1_id", "team2_id"):
        ms += get(f"{B}/matches?page%5Blimit%5D={n}&sort=-start_date&filter%5Bmatches.status%5D%5Bin%5D=finished"
                  f"&filter%5Bmatches.{side}%5D%5Beq%5D={team_id}")["results"]
    ms = sorted(ms, key=lambda m: m["start_date"], reverse=True)[:n]

    def one(m):
        rows = []
        for g in get(f"{B}/games?filter%5Bgames.match_id%5D%5Beq%5D={m['id']}", cache=True)["results"]:
            if g.get("status") != "finished" or not g.get("rounds_count"):
                continue
            try:
                ps = get(f"{B}/games/{g['id']}/players_stats", cache=True)
            except Exception:
                continue
            for p in ps or []:
                pl = ((p.get("steam_profile") or {}).get("player") or {})
                if p.get("kills") is None or p.get("headshots") is None or g["rounds_count"] < 13:
                    continue
                rows.append({"date": m["start_date"][:10], "match": m["id"], "bo": m.get("bo_type"), "game": g["id"],
                             "num": g.get("number"), "rounds": g["rounds_count"], "team_id": (p.get("team_clan") or {}).get("team_id"),
                             "nick": pl.get("nickname") or (p.get("steam_profile") or {}).get("nickname"),
                             "kills": p["kills"], "hs": p["headshots"], "win": bool(p.get("win"))})
        return rows

    with cf.ThreadPoolExecutor(6) as ex:
        return [r for rows in ex.map(one, ms) for r in rows]


def current_era(rows: list[dict], team_id: int) -> tuple[set, list[dict]]:
    """Today's five = the team's players in its latest map; era = maps with at least 4 of them."""
    mine = [r for r in rows if r["team_id"] == team_id]
    if not mine:
        return set(), []
    last = max(mine, key=lambda r: (r["date"], r["num"] or 0))["game"]
    five = {r["nick"] for r in mine if r["game"] == last}
    by_game = collections.defaultdict(set)
    for r in mine:
        by_game[r["game"]].add(r["nick"])
    keep = {g for g, s in by_game.items() if len(s & five) >= 4}
    return five, [r for r in mine if r["game"] in keep]


def newcomer_maps(nick: str, n: int = 30) -> list[dict]:
    """A player not in the team's recent maps: price him from his last team's maps."""
    try:
        p = get(f"{B}/players/{nick.lower()}")
    except Exception:
        return []
    if not p.get("team_id"):
        return []
    return [r for r in team_maps(p["team_id"], n) if same_name(r["nick"], nick)]


# ------------------------------------------------------------------ pricing
def price(player_rows: list[dict], all_rows: list[dict], p_map: float, rounds_w, rounds_l, stat: str, line: float,
          n: int = 200_000, seed: int = 17) -> dict:
    rng = np.random.default_rng(seed)
    K = lambda x: sum(r["kills"] for r in x)
    H = lambda x: sum(r["hs"] for r in x)
    R = lambda x: sum(r["rounds"] for r in x)
    # the prior is his longer-run rate, itself shrunk to a generic pro when that sample is small
    kall = (K(all_rows) + GENERIC_KPR * 300) / (R(all_rows) + 300)
    hall = (H(all_rows) + GENERIC_HS * 150) / (K(all_rows) + 150)
    w = [r for r in player_rows if r["win"]]
    lo = [r for r in player_rows if not r["win"]]
    kw = (K(w) + kall * 1.11 * 300) / (R(w) + 300)
    kl = (K(lo) + kall * 0.86 * 300) / (R(lo) + 300)
    hs = (H(player_rows) + hall * 150) / (K(player_rows) + 150)
    win = rng.random((n, 2)) < p_map
    rounds = np.where(win, rng.choice(rounds_w, (n, 2)), rng.choice(rounds_l, (n, 2)))
    kills = rng.poisson(np.where(win, kw, kl) * rounds * rng.gamma(1 / FORM_CV ** 2, FORM_CV ** 2, (n, 2)))
    x = kills.sum(1) if stat == "kills" else rng.binomial(kills, rng.beta(hs * HS_CONC, (1 - hs) * HS_CONC, (n, 2))).sum(1)
    by = collections.defaultdict(list)
    for r in player_rows:
        if r["num"] in (1, 2) and (r.get("bo") or 3) >= 3:
            by[r["match"]].append(r["kills"] if stat == "kills" else r["hs"])
    series = [sum(v) for v in by.values() if len(v) == 2]
    return {"p_over": float((x > line).mean()), "p_under": float((x < line).mean()), "p_push": float((x == line).mean()),
            "mean": float(x.mean()), "median": float(np.median(x)), "series": series,
            "hist_over": sum(s > line for s in series), "hist_under": sum(s < line for s in series),
            "kpr_w": kw, "kpr_l": kl, "hs_pct": hs, "maps": len(player_rows)}


def price_match(team: str, opp: str, props: list[dict]) -> list[dict]:
    """props: dicts with player, team (name), stat ('kills'|'hs'), line. Returns them with pricing attached."""
    m = find_match(team, opp)
    if not m:
        return [{**p, "error": "match not found on bo3.gg"} for p in props]
    sides = {}
    for k in ("team1", "team2"):
        t = m.get(k) or {}
        sides[t.get("name")] = t.get("id")
    data = {}
    for name, tid in sides.items():
        rows = team_maps(tid)
        five, era = current_era(rows, tid)
        data[name] = {"id": tid, "rows": rows, "five": five, "era": era}
    out = []
    for p in props:
        tname = next((n for n in data if same_name(n, p["team"])), None)
        if tname is None:
            out.append({**p, "error": "team not matched"})
            continue
        me = data[tname]
        oname = next(n for n in data if n != tname)
        ps = series_win_prob(m, me["id"])
        p_map = map_p_from_series(ps) if ps is not None else 0.5
        # rounds: our map wins + their map losses, and vice versa
        rw = [r["rounds"] for r in me["era"] if r["win"]] + [r["rounds"] for r in data[oname]["era"] if not r["win"]]
        rl = [r["rounds"] for r in me["era"] if not r["win"]] + [r["rounds"] for r in data[oname]["era"] if r["win"]]
        rw, rl = np.array(rw or [21]), np.array(rl or [21])
        prow = [r for r in me["era"] if same_name(r["nick"], p["player"])]
        allr = [r for r in me["rows"] if same_name(r["nick"], p["player"]) and r["team_id"] == me["id"]]
        newcomer = False
        if not prow:
            prow = allr = newcomer_maps(p["player"])
            newcomer = True
        if not prow:
            out.append({**p, "error": "no maps found for player"})
            continue
        if len(prow) < THIN_MAPS and not newcomer:  # e.g. one match since joining: add his previous team's maps to the prior
            prev = newcomer_maps(p["player"])
            allr = (allr or []) + [r for r in prev if r["game"] not in {x["game"] for x in allr or []}]
        r = price(prow, allr or prow, p_map, rw, rl, p["stat"], p["line"])
        out.append({**p, **r, "event_id": str(m["id"]), "match": m.get("slug"), "p_series": ps, "p_map": p_map,
                    "newcomer": newcomer, "thin": not newcomer and len(prow) < THIN_MAPS})
    return out
