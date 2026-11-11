"""NBA props on PrizePicks, priced: python -m edge pp --league NBA [--match DAL] [--log]
and the daily write-up:          python -m edge nba-picks [--top 5] [--log]

Every NBA prop the simulation scores (Points, Rebounds, Assists, 3-PT Made, Pts+Rebs+Asts, Pts+Rebs, Pts+Asts,
Rebs+Asts) is priced from three sources and blended by blend.final_probability, like every other pricer:
  model    the Sim Lab possession engine with its player layer, 50,000 runs of the game (minutes, usage, garbage
           time, score effects, availability, player-rating team strength, head-to-head): the share of runs over
           the line. The engine is the page's own worker code, run in Node (simlab/props_sim.js).
  market   DraftKings' no-vig price for the same player and stat. When DraftKings' line differs from PrizePicks',
           the simulated distribution is slid until it gives DraftKings' price at DraftKings' line, then read at
           PrizePicks' line.
  history  this season's games he played: over vs under this line.
The research facts (season / last-5 / head-to-head counts, per 36, what the opponent allows) ride along for the
write-up. The fair test found they don't predict beyond the price (LESSONS L27): context, never a reason.
"""
from __future__ import annotations

import concurrent.futures as cf
import collections
import datetime as dt
import json
import os
import re
import subprocess
import unicodedata

import numpy as np

from gamesim.data import slate_today

from . import viz as _viz

from .blend import HERE

STATS = {"Points": "pts", "Rebounds": "reb", "Assists": "ast", "3-PT Made": "tpm", "Pts+Rebs+Asts": "pra",
         "Pts+Rebs": "pr", "Pts+Asts": "pa", "Rebs+Asts": "ra"}
LABEL = {"pts": "points", "reb": "rebounds", "ast": "assists", "tpm": "3-pointers made", "pra": "pts + reb + ast",
         "pr": "pts + reb", "pa": "pts + ast", "ra": "reb + ast"}
PARTS = {"pts": (0,), "reb": (1,), "ast": (2,), "tpm": (3,), "pra": (0, 1, 2), "pr": (0, 1), "pa": (0, 2), "ra": (1, 2)}
PARTS_KEYS = {k: tuple(("pts", "reb", "ast", "tpm")[i] for i in v) for k, v in PARTS.items()}
ALIAS = {"WAS": "WSH", "UTA": "UTAH", "SAS": "SA", "NYK": "NY", "GSW": "GS", "NOP": "NO", "PHO": "PHX", "BRK": "BKN"}
CACHE = os.path.join(HERE, ".cache", "pp")
NODE_SCRIPT = os.path.join(HERE, "simlab", "props_sim.js")
N_SIMS = 50000
BREAK_EVEN = {"2-pick power": 0.577, "3-pick power": 0.585, "5/6-pick flex": 0.542}
# Fix 6: the verdict uses each line type's own payout. Standard lines (MORE-ONLY standard overs pay the same) use the
# 2-pick power break-even; goblins and demons pay a multiplier the partner API doesn't publish, so they can't be
# ENTRY legs until the multiplier shown in the app is entered (None = unknown).
BREAK_EVEN_BY_TYPE = {"standard": BREAK_EVEN["2-pick power"], "goblin": None, "demon": None}
_MEMO: dict = {}


def espn_abbr(a: str | None) -> str:
    return ALIAS.get((a or "").upper(), (a or "").upper())


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\b(jr|sr|ii|iii|iv)\b\.?", " ", s)
    return re.sub(r"[^a-z]", "", s)


def find_player(name: str, players: list[dict]) -> dict | None:
    """Exact normalized name, else same last name and first initial, else a close spelling."""
    import difflib
    n = _norm(name)
    for p in players:
        if _norm(p["name"]) == n:
            return p
    parts = str(name).lower().split()
    if len(parts) >= 2:
        hits = [p for p in players if p["name"].lower().split()[-1:] == parts[-1:] and p["name"][:1].lower() == parts[0][:1]]
        if len(hits) == 1:
            return hits[0]
    best = max(players, key=lambda p: difflib.SequenceMatcher(None, _norm(p["name"]), n).ratio(), default=None)
    return best if best and difflib.SequenceMatcher(None, _norm(best["name"]), n).ratio() >= 0.85 else None


# ------------------------------------------------------------------ distributions
def sides_at(h: list, line: float) -> tuple[float, float, float]:
    """P(over), P(under), P(push) from counts by whole value."""
    a = np.asarray(h, float); n = a.sum(); x = np.arange(len(a))
    return float(a[x > line].sum() / n), float(a[x < line].sum() / n), float(a[x == line].sum() / n)


def _surv(a: np.ndarray, t: float) -> float:
    """P(X > t) with each whole value spread over [k - 0.5, k + 0.5] (exact at half lines)."""
    x = np.arange(len(a))
    return float((a * np.clip(x + 0.5 - t, 0.0, 1.0)).sum() / a.sum())


def market_at(h: list, dk_line: float, q_over: float, line: float) -> tuple[float, float]:
    """DraftKings' no-vig over at its own line, carried to PrizePicks' line along the simulated shape: slide the
    distribution by s until P(X + s > dk_line) = q_over, then read P(X + s > line). Returns (p_over, shift)."""
    a = np.asarray(h, float)
    lo, hi = -40.0, 40.0
    for _ in range(60):
        s = (lo + hi) / 2
        if _surv(a, dk_line - s) < q_over:
            lo = s
        else:
            hi = s
    s = (lo + hi) / 2
    return _surv(a, line - s), s


def quantile(h: list, q: float) -> int:
    c = np.cumsum(np.asarray(h, float)); return int(np.searchsorted(c, q * c[-1]))


def mean(h: list) -> float:
    a = np.asarray(h, float); return float((a * np.arange(len(a))).sum() / a.sum())


def _imp(a) -> float | None:
    try:
        v = float(str(a).replace("+", ""))
    except (TypeError, ValueError):
        return None
    return 100 / (v + 100) if v > 0 else -v / (-v + 100)



_DABBLE = {}


def dabble_nba(max_age: float = 600) -> dict:
    """{(player, stat key): [{line, over, under}]} from Dabble's open NBA pick'em props (decimal prices on both sides;
    they sum to about 100%). Cached for max_age seconds. Empty when Dabble can't be reached."""
    import time
    if _DABBLE.get("t") and time.time() - _DABBLE["t"] < max_age:
        return _DABBLE["map"]
    from . import shop
    out = {}
    try:
        cid = shop.competitions().get("NBA")
        rows = shop.dabble_board("NBA", cid) if cid else []
    except Exception:
        rows = []
    inv = {tuple(sorted(v)): k for k, v in shop.STAT_MAP["NBA"].items()}
    for r in rows:
        key = STATS.get(inv.get(tuple(sorted(r["stats"])), ""))
        if key and r.get("over") and r.get("under"):
            out.setdefault((_norm(r["player"]), key), []).append({"line": float(r["line"]), "over": r["over"], "under": r["under"]})
    _DABBLE.update(t=time.time(), map=out)
    return out


GAP_2ND = 2.0          # a PrizePicks line this far from the book's needs a second book that agrees (user audit, 2026-11-06)


def markets_for(lines: dict | None, pid, name: str, stat: str, line: float) -> tuple[list[dict], dict | None]:
    """Every book with a price for the stat: DraftKings (when priced) then Dabble's nearest line. Returns
    (list of {book, line, over, under, q}, raw DraftKings)."""
    out = []
    dk = ((lines or {}).get(pid) or {}).get(stat)
    if dk and dk.get("over") and dk.get("under"):
        qo, qu = _imp(dk["over"]), _imp(dk["under"])
        if qo and qu:
            out.append({"book": "DraftKings", "line": float(dk["line"]), "over": dk["over"], "under": dk["under"], "q": qo / (qo + qu)})
    alts = dabble_nba().get((_norm(name), stat)) or []
    if alts:
        b = min(alts, key=lambda a: (abs(a["line"] - line), a["line"]))
        a_, u_ = 1 / float(b["over"]), 1 / float(b["under"])
        out.append({"book": "Dabble", "line": b["line"], "over": b["over"], "under": b["under"], "q": a_ / (a_ + u_)})
    return out, dk


def market_for(lines: dict | None, pid, name: str, stat: str, line: float) -> tuple[dict | None, dict | None]:
    """The market for a player's stat: DraftKings when it posts a priced line, otherwise Dabble's line nearest the
    PrizePicks line (user, 2026-11-06: use other books when DraftKings has no price). Returns (market, raw DraftKings):
    market = {book, line, over, under, q} with q the no-vig over at the book's own line, or None."""
    dk = ((lines or {}).get(pid) or {}).get(stat)
    if dk and dk.get("over") and dk.get("under"):
        qo, qu = _imp(dk["over"]), _imp(dk["under"])
        if qo and qu:
            return {"book": "DraftKings", "line": float(dk["line"]), "over": dk["over"], "under": dk["under"], "q": qo / (qo + qu)}, dk
    alts = dabble_nba().get((_norm(name), stat)) or []
    if alts:
        b = min(alts, key=lambda a: (abs(a["line"] - line), a["line"]))
        a_, u_ = 1 / float(b["over"]), 1 / float(b["under"])
        return {"book": "Dabble", "line": b["line"], "over": b["over"], "under": b["under"], "q": a_ / (a_ + u_)}, dk
    return None, dk

# ------------------------------------------------------------------ engine + simulation
def run_sims(eng: dict, gids: list[str], n: int = N_SIMS, workers: int = 4) -> dict:
    """50,000 runs per game in parallel Node processes, each running the page's worker code."""
    os.makedirs(CACHE, exist_ok=True)
    chunks = [gids[i::workers] for i in range(workers) if gids[i::workers]]
    procs = []
    for k, ch in enumerate(chunks):
        games = []
        for gid in ch:
            s = eng["sides"][gid]
            games.append({"id": gid, "sides": {"home": s["home"], "away": s["away"]}, "pl": [s["players"]["home"], s["players"]["away"]]})
        ip, op = os.path.join(CACHE, f"nba_sim_in_{k}.json"), os.path.join(CACHE, f"nba_sim_out_{k}.json")
        with open(ip, "w") as f:
            json.dump({"R": eng["R"], "n": n, "seed": 7000 + 100 * k, "games": games}, f)
        procs.append((subprocess.Popen(["node", NODE_SCRIPT, ip, op]), op))
    out = {}
    for p, op in procs:
        if p.wait() != 0:
            raise RuntimeError("props_sim.js failed")
        with open(op) as f:
            out.update(json.load(f)["games"])
    return out


SIM_KNOBS = {"minutes_alpha": "MINUTES_ALPHA", "swing_rho": "SWING_RHO", "shock": "PLAYER_SHOCK", "prior_min": "PLAYER_PRIOR_MIN",
             "min_sd_scale": "MIN_SD_SCALE", "minutes_share": "MINUTES_SHARE", "minutes_pad": "MINUTES_PAD",
             "ast_fix": "AST_FIX", "team_market_w": "TEAM_MARKET_W"}


def nba_model_params(version: int | None = None) -> dict:
    """A logic version's parameters with its version number (default: the published one)."""
    from . import nba_model
    if version is None:
        return board_logic()
    return {**nba_model.params_for(version), "_version": version}


def current_sim(version: int | None = None) -> dict:
    """The simulation settings of a logic version (default: the published one); {} = the engine's defaults (v1)."""
    from . import nba_model
    return dict((nba_model.params_for(version) if version is not None else nba_model.params("current") or {}).get("sim") or {})


def build(dates: set | None = None, gids: set | None = None, n: int = N_SIMS, sim: dict | None = None) -> dict:
    """Tonight's NBA games (ESPN), the engine inputs (simlab.nba_engine) and the player distributions. Memoized per
    process, so `edge verify` on several picks re-runs the engine once. `sim` overrides simulation settings (a
    shadow logic's), restored afterwards."""
    from gamesim import nba as gnba
    if sim is None:                       # default: the published (current) logic's simulation settings
        sim = current_sim()
    saved = {k: getattr(gnba, a) for k, a in SIM_KNOBS.items()}
    for k, v in sim.items():
        setattr(gnba, SIM_KNOBS[k], v)
    try:
        return _build(dates, gids, n, tuple(sorted(sim.items())))
    finally:
        for k, v in saved.items():
            setattr(gnba, SIM_KNOBS[k], v)


def _build(dates, gids, n, simkey) -> dict:
    from . import simlab
    key = (tuple(sorted(dates or [])), tuple(sorted(gids or [])), n, simkey)
    if key in _MEMO:
        return _MEMO[key]
    if gids:              # the back-check right after pricing: reuse that run if it covers these games (< 15 min old)
        now = dt.datetime.now(dt.timezone.utc)
        for k, v in _MEMO.items():
            if isinstance(v, dict) and "sims" in v and set(gids) <= set(v["sims"]) and k[2] == n and k[3] == simkey and \
                    now - dt.datetime.strptime(v["pulled"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc) < dt.timedelta(minutes=15):
                return v
    today = simlab.us_today()
    games = simlab.league_games("basketball/nba", [-1, 0, 1], today)
    if dates:
        games = [g for g in games if _us_date(g["start"]) in dates]
    if gids:
        games = [g for g in games if g["id"] in gids]
    eng = simlab.nba_engine(games, today) if games else {"sides": {}, "R": {}}
    snapshot_dk(eng, games)
    sims = run_sims(eng, [g["id"] for g in games], n=n) if games else {}
    if simkey == tuple(sorted(current_sim().items())):      # the published logic's run (not a shadow's): keep it for the nightly audit
        try:
            save_pretip(eng, games, sims)
        except Exception:
            pass
    _MEMO[key] = {"games": {g["id"]: g for g in games}, "eng": eng, "sims": sims, "pulled": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
    return _MEMO[key]


SNAP_DIR = os.path.join(HERE, "data", "nba_dk_snap")


def snapshot_dk(eng: dict, games: list[dict]):
    """Fix 4: every DraftKings pull is stamped and kept (data/nba_dk_snap/DATE.jsonl), so each published leg's
    closing line can be read back for closing line value."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    os.makedirs(SNAP_DIR, exist_ok=True)
    with open(os.path.join(SNAP_DIR, f"{slate_today()}.jsonl"), "a") as f:
        for g in games:
            lines = ((eng["sides"].get(g["id"]) or {}).get("players") or {}).get("lines") or {}
            if lines:
                f.write(json.dumps({"at": now, "gid": g["id"], "start": g["start"], "lines": lines}) + "\n")


PRETIP_DIR = os.path.join(HERE, "data", "nba_pretip")


def save_pretip(eng: dict, games: list[dict], sims: dict) -> None:
    """Each game's last pre-tip prediction (data/nba_pretip/<US date>.json, one entry per game, overwritten only
    while the game hasn't started): win chance, expected score, the market line, who was ruled out, and every
    player's projected minutes and simulated averages. edge/sim_audit.py compares it with the box score."""
    now = dt.datetime.now(dt.timezone.utc)
    by_day = {}
    for g in games:
        start = dt.datetime.fromisoformat(g["start"].replace("Z", "+00:00"))
        sim, sd = sims.get(g["id"]), eng["sides"].get(g["id"])
        if not sim or not sd or start <= now:
            continue
        players = {}
        for side in ("home", "away"):
            prof = {p["id"]: p for p in ((sd.get("players") or {}).get(side) or {}).get("players", [])}
            for pid, sp in sim.get("players", {}).items():
                if sp.get("side") != side:
                    continue
                h = sp.get("hist") or {}
                avg = lambda k: round(mean(h[k]), 2) if h.get(k) and sum(h[k]) else None
                pr = prof.get(pid) or {}
                players[pid] = {"name": sp.get("name"), "side": side, "min_proj": round(float(pr.get("min") or 0), 1),
                                "min_raw": round(float(pr.get("min_raw") or 0), 1), "starter_last": bool(pr.get("starter")),
                                "season_min": (pr.get("season") or {}).get("min"),
                                **{k: avg(k) for k in ("min", "pts", "reb", "ast", "tpm")}}
        outs = {side: [r["name"] for r in ((sd.get("availability") or {}).get(side) or {}).get("rows", []) if r.get("out_tonight")] for side in ("home", "away")}
        rec = {"gid": g["id"], "home": g["home"], "away": g["away"], "start": g["start"], "pulled": now.strftime("%Y-%m-%dT%H:%MZ"),
               "p_home": sim.get("p_home"), "mean_home": sim.get("mean_home"), "mean_away": sim.get("mean_away"),
               "spread": g.get("spread"), "total": g.get("total"), "ml_home": g.get("ml_home"), "ml_away": g.get("ml_away"),
               "outs": outs, "injuries": [{"name": i["name"], "team": i.get("team"), "status": i.get("status")} for i in (sd.get("players") or {}).get("injuries", [])],
               "market_anchor": sd.get("market_anchor"), "players": players}
        by_day.setdefault(_us_date(g["start"]), {})[g["id"]] = rec
    os.makedirs(PRETIP_DIR, exist_ok=True)
    for day, recs in by_day.items():
        path = os.path.join(PRETIP_DIR, f"{day}.json")
        cur = json.load(open(path)) if os.path.exists(path) else {}
        cur.update(recs)
        json.dump(cur, open(path, "w"), default=float)


def _us_date(iso: str) -> str:
    """US calendar date of an ISO timestamp (any offset): UTC minus 10 hours, as gamesim.data.us_day."""
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (t.astimezone(dt.timezone.utc) - dt.timedelta(hours=10)).strftime("%Y-%m-%d")


def slate_props(props: list[dict], slate: str) -> list[dict]:
    """Only the slate's games: PrizePicks posts the next day's lines early, and those belong on tomorrow's page and ledger
    date, not tonight's. A prop with no start time is kept."""
    return [p for p in props if not p.get("start") or _us_date(p["start"]) == slate]


# ------------------------------------------------------------------ pricing
def research(p: dict, stat: str, line: float, opp: str, allowed: dict | None) -> dict:
    """Context for the write-up (not a blend input beyond the season history): this season's over/under count at
    the line, last 5, last 5 meetings with tonight's opponent, per 36, and what the opponent allows."""
    rs = p.get("research") or {}
    log, h2h = rs.get("log") or [], rs.get("h2h") or []
    v = lambda r, off: sum(r[off + i] for i in PARTS[stat])
    over = lambda rows, off: sum(v(r, off) > line for r in rows)
    under = lambda rows, off: sum(v(r, off) < line for r in rows)
    mins = sum(r[3] for r in log)
    per36 = 36 * sum(v(r, 4) for r in log) / mins if mins else None
    h2m = sum(r[1] for r in h2h)
    out = {"season": [over(log, 4), under(log, 4), len(log)], "last5": [over(log[-5:], 4), under(log[-5:], 4), len(log[-5:])],
           "h2h": [over(h2h, 2), under(h2h, 2), len(h2h)], "per36": per36,
           "h2h_per36": 36 * sum(v(r, 2) for r in h2h) / h2m if h2m else None,
           "season_avg": float(np.mean([v(r, 4) for r in log])) if log else None, "last_games": [v(r, 4) for r in log[-5:]],
           "h2h_games": [[r[0], v(r, 2), r[1]] for r in h2h],
           "games": [[r[0], r[1], r[2], r[3], v(r, 4)] for r in log]}          # date, opponent, home, minutes, value (cards)
    if allowed and len(PARTS[stat]) == 1:
        a = allowed.get(["pts", "reb", "ast", "tpm"][PARTS[stat][0]]) or {}
        if a.get("per_game") is not None:
            out["opp_allows"] = {"per_game": a["per_game"], "league": a["league"], "rank": a["rank"], "teams": a["teams"]}
    return out


def _lg(p: float) -> float:
    p = min(max(p, 1e-4), 1 - 1e-4)
    return float(np.log(p / (1 - p)))


def _sg(z: float) -> float:
    return float(1 / (1 + np.exp(-z)))


ENTRY_BREAK_EVEN = {2: 1 / 3, 3: 1 / 5}     # PrizePicks power: 2 legs pay 3x, 3 legs pay 5x (P(all hit) needed)


def joint_probability(legs: list[dict], n: int = N_SIMS) -> dict:
    """Fix 7: P(every leg hits) for a proposed entry. Legs in the same game come from the same simulated runs (their
    correlation included); legs in different games multiply. Each leg: {event_id, player_id, stat, line, side, p}
    where p is the leg's calibrated probability, used for the cross-game product."""
    by_game = {}
    for l in legs:
        by_game.setdefault(str(l["event_id"]), []).append(l)
    ctx = build(gids=set(by_game), n=n)
    total, parts = 1.0, []
    for gid, L in by_game.items():
        if len(L) == 1:
            total *= L[0]["p"]
            parts.append({"game": gid, "legs": 1, "p": L[0]["p"], "how": "single leg: its calibrated probability"})
            continue
        s = ctx["eng"]["sides"][gid]
        inp = {"id": gid, "sides": {"home": s["home"], "away": s["away"]}, "pl": [s["players"]["home"], s["players"]["away"]],
               "legs": [{"pid": str(l["player_id"]), "stat": l["stat"], "line": float(l["line"]), "side": l["side"]} for l in L]}
        os.makedirs(CACHE, exist_ok=True)
        ip, op = os.path.join(CACHE, "joint_in.json"), os.path.join(CACHE, "joint_out.json")
        with open(ip, "w") as f:
            json.dump({"R": ctx["eng"]["R"], "n": n, "seed": 9100, "games": [inp]}, f)
        if subprocess.run(["node", NODE_SCRIPT, ip, op]).returncode != 0:
            raise RuntimeError("props_sim.js failed")
        j = json.load(open(op))["games"][gid]["joint"]
        # the simulation's joint rate, scaled by how far the calibrated legs sit from the raw simulated ones
        raw_prod = float(np.prod(j["legs"])) or 1e-9
        cal_prod = float(np.prod([l["p"] for l in L]))
        pj = min(1.0, j["all"] * cal_prod / raw_prod)
        total *= pj
        parts.append({"game": gid, "legs": len(L), "p": pj, "sim_joint": j["all"], "sim_legs": j["legs"],
                      "how": f"same-game joint from {n:,} runs (independence would say {raw_prod:.3f}, the runs say {j['all']:.3f})"})
    be = ENTRY_BREAK_EVEN.get(len(legs))
    return {"p_all": total, "break_even": be, "clears": be is not None and total > be, "parts": parts}


def market_sides(h: list, dk_line: float, q_over: float, line: float) -> tuple[float, float]:
    """Fix 6 (push consistency): the market's over and under at PrizePicks' line along the simulated shape, each
    exclusive of a push, so the side probability is P(side) / (1 - P(push)) as for the model and history."""
    a = np.asarray(h, float)
    _, s = market_at(h, dk_line, q_over, dk_line)
    if float(line).is_integer():
        over = _surv(a, line + 0.5 - s); under = 1 - _surv(a, line - 0.5 - s)
        return over / max(over + under, 1e-9), s
    return _surv(a, line - s), s


def _label(p: float, comps: dict, hist_n: int, segment: str, adj: dict, high_thin: dict | None) -> tuple[str, bool, float]:
    """The confidence gates of blend.final_probability on a (possibly recalibrated) probability, plus Fix 5's
    thin-history High rule when the logic enables it."""
    vals = list(comps.values())
    leaning = [v for v in vals if abs(v - 0.5) >= 0.01]
    agree = bool(leaning) and (all(v > 0.5 for v in leaning) or all(v < 0.5 for v in leaning))
    spread = max(vals) - min(vals) if vals else 0.0
    g = adj["gates"]
    if segment and any(segment.startswith(x) for x in adj["avoid_segments"]):
        return "Avoid", agree, spread
    high = (p >= g["high"] and agree and spread <= g["max_spread_high"] and len(comps) >= 2 and hist_n >= g["min_hist_n_high"]
            and ("market" in comps or (hist_n >= g.get("no_market_min_hist_n", 20) and spread <= g.get("no_market_max_spread", 0.10))))
    if not high and high_thin and p >= g["high"] and agree and "model" in comps and "market" in comps and hist_n < g["min_hist_n_high"]:
        high = abs(comps["model"] - comps["market"]) <= high_thin.get("max_spread", 0.08)
    if high:
        cap = next((x for x in adj.get("cap_medium_segments", {}) if segment.startswith(x)), None)
        return ("Medium" if cap else "High"), agree, spread
    if p >= g["medium"] and agree and len(comps) >= 2:
        return "Medium", agree, spread
    return "Low", agree, spread


AGREE_MAX = 0.05      # High needs the simulation and the market within 5 points (user audit, 2026-11-06)


def gate_label(conf: str, pm, pk, notes: str, stat: str) -> tuple[str, list[str]]:
    """High means agreement: a market price, simulation and market within AGREE_MAX, tonight's tilt in this stat
    within TILT_MAX (or its cause logged), and no minutes gap (L28). Anything less is held at Medium (LEAN): the
    display follows the entry gate. Returns (label, reasons it was held)."""
    held = []
    if conf != "High":
        return conf, held
    if pk is None:
        held.append("no market price")
    elif pm is not None and abs(float(pm) - float(pk)) > AGREE_MAX:
        held.append(f"simulation {float(pm):.0%} vs market {float(pk):.0%}: {abs(float(pm) - float(pk)) * 100:.0f} points apart")
    m = re.search(r"raw tilt ([+-]\d+\.\d+)", notes or "")
    causes = json.load(open(TILT_CAUSES)) if os.path.exists(TILT_CAUSES) else {}
    if m and abs(float(m.group(1))) > TILT_MAX and stat not in causes:
        held.append(f"tonight's {LABEL.get(stat, stat)} tilt {m.group(1)} logit is past {TILT_MAX} with no cause logged")
    if "minutes gap:" in (notes or ""):
        held.append("minutes not confirmed (L28)")
    if "single-sourced gap" in (notes or ""):
        held.append("the PrizePicks line's gap from the book is confirmed by only one book")
    if "second book disagrees" in (notes or ""):
        held.append("the second book prices the other side")
    return ("Medium" if held else conf), held

def recompute(pm, pk, ph, hist_n: int, segment: str, logic: dict) -> tuple[float, str]:
    """edge verify's recompute for an NBA leg: the blend, missing-market rule, cap and gates of the logic version
    that priced it (Fix 7: verify checks truth under the right logic)."""
    from .blend import final_probability
    adj = _logic_adj(logic)
    neutral = pk is None and logic.get("missing_market") == "neutral"
    e = final_probability(pm, 0.5 if neutral else pk, ph, segment, hist_n, adj)
    p = e.p
    if logic.get("recal"):
        p = float(_sg(logic["recal"]["a"] + logic["recal"]["b"] * _lg(p)))
    if logic.get("cap"):
        p = min(p, logic["cap"])
    dg = logic.get("disagree")
    if dg and pk is not None and pm is not None and abs(pm - pk) > dg["gap"]:
        p = min(p, pk + dg.get("margin", 0.0))
    comps = {k: v for k, v in e.components.items() if not (neutral and k == "market")}
    return round(p, 4), _label(p, comps, hist_n, segment, adj, logic.get("high_thin"))[0]


def _logic_adj(logic: dict) -> dict:
    from .blend import load_adjustments
    adj = load_adjustments()
    if logic.get("blend"):
        adj["blend_by_sport"] = {**(adj.get("blend_by_sport") or {}), "nba": {k: logic["blend"][k] for k in ("intercept", "w_model", "w_market", "w_hist")}}
    if logic.get("gates"):
        adj["gates"] = {**adj["gates"], **logic["gates"]}
    return adj


TILT_CAUSES = os.path.join(HERE, "data", "nba_tilt_causes.json")
TILT_MAX = 0.25        # Fix 7: tonight's raw simulation-vs-DraftKings gap beyond this blocks ENTRY legs in that stat


def price_nba(props: list[dict], n: int = N_SIMS, logic: dict | None = None) -> list[dict]:
    """Price the board under one pricing logic (edge/nba_model.py; None = the current published logic)."""
    from .blend import final_probability
    from . import nba_model
    if logic is None:
        logic = {**nba_model.params("current"), "_version": nba_model.load()["current"]["version"]}
    logic = {**nba_model.V1, **logic}
    adj = _logic_adj(logic)
    want = [p for p in props if p["stat"] in STATS]
    out = [{**p, "error": "stat not priced yet"} for p in props if p["stat"] not in STATS]
    if not want:
        return out
    ctx = build({_us_date(p["start"]) for p in want if p.get("start")}, n=n, sim=logic.get("sim") or {})
    by_pair = {frozenset((g["home"], g["away"])): g for g in ctx["games"].values()}
    staged = []
    extra_by_id = {}
    for p in want:
        g = by_pair.get(frozenset((espn_abbr(p["home"]), espn_abbr(p["away"]))))
        if not g or g["id"] not in ctx["sims"]:
            out.append({**p, "error": "game not in tonight's simulation"})
            continue
        team = espn_abbr(p["team"])
        side = "home" if team == g["home"] else "away" if team == g["away"] else None
        sd = ctx["eng"]["sides"][g["id"]]
        prof = (sd["players"].get(side) or {}).get("players", []) if side else []
        pl = find_player(p["player"], prof)
        if not pl:
            inj = [i for i in sd["players"].get("injuries", []) if find_player(p["player"], [{"name": i["name"]}])]
            out.append({**p, "error": "listed " + inj[0]["status"].lower() if inj else "not in the projected rotation"})
            continue
        top5 = pl["id"] in {x["id"] for x in sorted(prof, key=lambda x: -x["min"])[:5]}
        sim = ctx["sims"][g["id"]]["players"].get(pl["id"])
        stat, line = STATS[p["stat"]], float(p["line"])
        h = sim["hist"][stat]
        po, pu, ppush = sides_at(h, line)
        mks, raw_dk = markets_for(sd["players"].get("lines"), pl["id"], pl["name"], stat, line)
        dk = mks[0] if mks else None
        dk2 = None
        if len(mks) > 1:
            m2 = mks[1]
            dk2 = {**m2, "carried": m2["q"] if abs(m2["line"] - line) < 1e-9 else
                   (market_sides(h, m2["line"], m2["q"], line)[0] if logic["push"] == "exclusive" else market_at(h, m2["line"], m2["q"], line)[0])}
        mk_over, mk_note = None, "no DraftKings or Dabble line for this player and stat yet"
        if dk:
            q, bk = dk["q"], dk["book"]
            pre = "" if bk == "DraftKings" else "no DraftKings line; "
            if abs(dk["line"] - line) < 1e-9:
                mk_over, mk_note = q, f"{pre}{bk} {dk['line']} at {dk['over']}/{dk['under']} (no-vig over {q:.0%})"
            else:
                mk_over = market_sides(h, dk["line"], q, line)[0] if logic["push"] == "exclusive" else market_at(h, dk["line"], q, line)[0]
                mk_note = f"{pre}{bk} {dk['line']} at {dk['over']}/{dk['under']} (no-vig over {q:.0%}), carried to {line}: {mk_over:.0%}"
        elif raw_dk:
            mk_note = f"DraftKings line {raw_dk['line']} but its sides are unlabelled (L2): market not used"
        if dk:
            dk = {**dk, "carried": mk_over}
            if abs(dk["line"] - line) >= GAP_2ND:
                mk_note += (f"; second book {dk2['book']} {dk2['line']}: {dk2['carried']:.0%} over at {line}" if dk2 else
                            f"; single-sourced gap: PrizePicks {line} vs {dk['book']} {dk['line']} with no second book")
        staged.append((p, g, side, sd, pl, sim, stat, line, h, po, pu, ppush, dk, mk_over, mk_note, top5))
        extra_by_id[id(p)] = {"dk2": dk2}
    # tonight's raw tilt per stat on main lines (L7 measurement; Fix 7 tilt monitor)
    gaps = {}
    for (p, g, side, sd, pl, sim, stat, line, h, po, pu, ppush, dk, mk_over, mk_note, top5) in staged:
        if mk_over is not None and dk.get("book") == "DraftKings" and p.get("odds_type") == "standard" and abs(dk["line"] - line) <= 1.0 and 0 < po < 1 - ppush:
            gaps.setdefault(stat, []).append(_lg(po / max(1 - ppush, 1e-9)) - _lg(mk_over))
    tilt = {k: float(np.mean(v)) for k, v in gaps.items() if len(v) >= 10}
    causes = json.load(open(TILT_CAUSES)) if os.path.exists(TILT_CAUSES) else {}
    for (p, g, side, sd, pl, sim, stat, line, h, po, pu, ppush, dk, mk_over, mk_note, top5) in staged:
        if logic["bias"] == "night_flat":
            b = tilt.get(stat, 0.0)
        elif logic["bias"] == "table":
            t = (logic.get("bias_table") or {}).get(stat, {})
            b = t.get("top5" if top5 else "bench", t.get("all", 0.0))
        else:
            b = 0.0
        if b and 0 < po < 1 - ppush:
            o = _sg(_lg(po / (1 - ppush)) - b) * (1 - ppush)
            po, pu = o, 1 - ppush - o
        opp = g["away"] if side == "home" else g["home"]
        rs = research(pl, stat, line, opp, (sd.get("opp_allowed") or {}).get(side))
        if logic["history"] == "off":
            ho = hu = 0
        elif logic["history"] == "aware":
            ho, hu = aware_counts(pl, stat, line)
        else:
            ho, hu = rs["season"][0], rs["season"][1]
        flags = []
        if pl.get("games", 0) < 5:
            flags.append(f"THIN SAMPLE: {pl.get('games', 0)} games with the team")
        if pl.get("returning"):
            flags.append("RETURNING from injury: minutes unconfirmed")
        q_inj = [i for i in sd["players"].get("injuries", []) if find_player(pl["name"], [{"name": i["name"]}]) and (i["status"] or "").lower() in ("questionable", "day-to-day", "probable")]
        if q_inj:
            flags.append(f"listed {q_inj[0]['status']}: confirm he plays")
        mh = sim["hist"]["min"]
        note = (", ".join(flags) + ", role unconfirmed (L5); " if flags else "") + \
            f"sim median {quantile(h, 0.5)} (mean {mean(h):.1f}, 25-75th {quantile(h, 0.25)}-{quantile(h, 0.75)}), minutes {mean(mh):.1f}; {mk_note}" + \
            (f"; model de-biased {-b:+.2f} logit ({'tonight' if logic['bias'] == 'night_flat' else 'fitted ' + ('top5' if top5 else 'bench')} simulation-vs-DraftKings gap on {LABEL[stat]}, L7)" if b else "") + \
            (f"; raw tilt {tilt[stat]:+.2f}" if stat in tilt else "") + f"; pulled {ctx['pulled']}; logic v{logic.get('_version', 1)}"
        # side choice and blend (as pp._finish, under this logic's weights)
        best = None
        for sd_ in (["over"] if p["over_only"] else ["over", "under"]):
            pm = (po if sd_ == "over" else pu) / max(1 - ppush, 1e-9)
            pk = None if mk_over is None else (mk_over if sd_ == "over" else 1 - mk_over)
            dec = ho + hu
            ph = None if not dec else (ho if sd_ == "over" else hu) / dec
            # Fix 2: with no DraftKings price, a market-dominant logic treats the market as no information (50%)
            # instead of handing the model the market's weight
            neutral = pk is None and logic.get("missing_market") == "neutral"
            e = final_probability(pm, 0.5 if neutral else pk, ph, f"nba:{stat}:{sd_}", int(round(dec)), adj)
            comps = {k: v for k, v in e.components.items() if not (neutral and k == "market")}
            if best is None or e.p > best["p"]:
                best = {"side": sd_, "p": e.p, "pm": pm, "pk": pk, "ph": ph, "dec": dec, "comps": comps}
        p_uncal = best["p"]
        se_logit = 0.0
        if logic.get("recal"):
            a_, b_ = logic["recal"]["a"], logic["recal"]["b"]
            x = np.array([1.0, _lg(p_uncal)])
            pf = _sg(a_ + b_ * _lg(p_uncal))
            cov = np.array(logic["recal"].get("cov") or [[0, 0], [0, 0]])
            se_logit = float(np.sqrt(max(x @ cov @ x, 0.0)))
        else:
            pf = p_uncal
        if logic.get("cap"):
            pf = min(pf, logic["cap"])        # Fix 3: the selected side's probability is capped (70%+ legs ran hot)
        dg = logic.get("disagree")
        if dg and best["pk"] is not None and abs(best["pm"] - best["pk"]) > dg["gap"]:
            pf = min(pf, best["pk"] + dg.get("margin", 0.0))   # sources disagree: shrink to the market (user audit, 2026-11-06)
        if logic.get("se_w") is not None:     # Fix 3: the blend's own uncertainty, from the model weight's
            se_logit = (logic["se_w"] * abs(_lg(best["pm"]) - _lg(best["pk"]))) if best["pk"] is not None else 0.5
        conf, agree, spread = _label(pf, best["comps"], int(round(best["dec"])), f"nba:{stat}:{best['side']}", adj, logic.get("high_thin"))
        if flags:
            conf = "Low"          # unconfirmed role or minutes: never an entry leg (L5)
        from .verify import minutes_gap
        mg = minutes_gap(best["side"], pl.get("min"), [r_[3] for r_ in ((pl.get("research") or {}).get("log") or [])[-5:]])
        if mg:
            note += f"; minutes gap: {mg}"
        d2 = extra_by_id.get(id(p), {}).get("dk2")
        if dk and abs(dk["line"] - line) >= GAP_2ND and d2 and d2.get("carried") is not None:
            s2 = d2["carried"] if best["side"] == "over" else 1 - d2["carried"]
            if s2 < 0.5:                       # the second book prices the other side: the gap isn't confirmed (verify FAILs it too)
                note += f"; second book disagrees: {d2['book']} {s2:.0%} for the {best['side']} at {line}"
        conf, held = gate_label(conf, best["pm"], best["pk"], note, stat)
        if held:
            note += "; High held at Medium: " + ", ".join(held)
        se_p = float(pf * (1 - pf) * se_logit + np.sqrt(pf * (1 - pf) / ctx["sims"][g["id"]]["n"]))
        be = BREAK_EVEN_BY_TYPE.get(p.get("odds_type"))
        tilt_block = abs(tilt.get(stat, 0.0)) > TILT_MAX and stat not in causes
        row = {**p, "side": best["side"], "p_final": round(pf, 4), "confidence": conf, "p_model": best["pm"], "p_market": best["pk"],
               "p_hist": best["ph"], "hist_n": int(round(best["dec"])), "agree": agree, "market_key": stat, "sport": "nba",
               "push": ppush, "notes": note, "p_uncal": p_uncal, "se_p": se_p, "break_even": be, "tilt_raw": tilt.get(stat),
               "tilt_block": tilt_block, "entry_rule": logic["entry"], "held": held}
        row["verdict_v"] = verdict(row)
        out.append({**row, "event_id": g["id"], "player_id": pl["id"], "proj": quantile(h, 0.5), "opp_proj": round(mean(mh), 1),
                    "script": f"nba:{g['id']}", "newcomer": bool(flags), "research": rs, "game": f"{g['away']} @ {g['home']}",
                    "opp_espn": opp, "sim_mean": mean(h), "q25": quantile(h, 0.25), "q75": quantile(h, 0.75), "dk": dk, "dist": _viz.dist_from_counts(h),
                    "h2h_factor": (pl.get("h2h") or {}).get(stat) if len(PARTS[stat]) == 1 else None, "stat_key": stat,
                    "p_home": ctx["sims"][g["id"]]["p_home"], "pulled": ctx["pulled"], "n_sims": ctx["sims"][g["id"]]["n"],
                    "bias_logit": b, "bias_n": len(gaps.get(stat, [])), "top5": top5,
                    "p_model_raw": sides_at(h, line)[0 if best["side"] == "over" else 1] / max(1 - ppush, 1e-9),
                    "dk2": extra_by_id.get(id(p), {}).get("dk2"),
                    "role": {"starter": bool(pl.get("starter")), "min": round(float(pl.get("min") or 0), 1), "min_sd": round(float(pl.get("min_sd") or 0), 1),
                             "season_min": round(float((pl.get("season") or {}).get("min") or 0), 1),
                             "last5_min": [r_[3] for r_ in ((pl.get("research") or {}).get("log") or [])[-5:]]},
                    "rotation": [{"name": x["name"], "min": round(float(x.get("min") or 0), 1), "season": round(float((x.get("season") or {}).get("min") or 0), 1),
                                  "starter": bool(x.get("starter"))} for x in sorted((sd["players"].get(side) or {}).get("players", []), key=lambda x: -(x.get("min") or 0))[:10]],
                    "team_injuries": [{"name": i["name"], "status": i["status"]} for i in sd["players"].get("injuries", [])
                                      if find_player(i["name"], [{"name": x["name"]} for x in (sd["players"].get(side) or {}).get("players", [])] +
                                                     [{"name": x["name"]} for x in (sd.get("availability") or {}).get(side, {}).get("rows", [])])],
                    "outs": [{"name": x["name"], "value": x.get("value")} for x in (sd.get("availability") or {}).get(side, {}).get("rows", []) if x.get("out_tonight")],
                    "with_without": with_without(pl, stat, (sd.get("out_played") or {}).get(side),
                                                 [x for x in (sd.get("availability") or {}).get(side, {}).get("rows", []) if x.get("out_tonight")])})
    return out


def with_without(pl: dict, stat: str, out_played: dict | None, outs: list[dict], top: int = 2) -> list[dict]:
    """This season's games split by whether each teammate out tonight played (user audit, 2026-11-06: show the
    redistribution, not just the injury): games, average minutes and average value in each half, for the `top` most
    valuable players out. Box scores only; small samples are shown as such."""
    log = (pl.get("research") or {}).get("log") or []
    if not log or not out_played:
        return []
    v = lambda r: sum(r[4 + i] for i in PARTS[stat])
    half = lambda L: {"n": len(L), "min": round(float(np.mean([r[3] for r in L])), 1) if L else None,
                      "avg": round(float(np.mean([v(r) for r in L])), 1) if L else None}
    res = []
    for o in sorted(outs or [], key=lambda o: -(o.get("value") or 0))[:top]:
        dates = out_played.get(o["name"])
        if dates is None:
            continue
        d = set(dates)
        res.append({"name": o["name"], "with": half([r for r in log if r[0] in d]), "without": half([r for r in log if r[0] not in d])})
    return res


def aware_counts(pl: dict, stat: str, line: float) -> tuple[float, float]:
    """Fix 2: this season's games weighted by minutes played / projected minutes (capped at 1.5), dropping early
    exits (under half his projection)."""
    log = (pl.get("research") or {}).get("log") or []
    pm = max(pl.get("min") or 0.0, 1.0)
    o = u = 0.0
    for r in log:
        if r[3] < 0.5 * pm:
            continue
        v = sum(r[4 + i] for i in PARTS[stat]); w = min(r[3] / pm, 1.5)
        if v > line:
            o += w
        elif v < line:
            u += w
    return o, u


def model_market_bias(rows: list[dict]) -> dict:
    """The per-stat correction applied tonight: mean logit(simulation over) - logit(DraftKings over) on main lines
    (LESSONS L7: measured every scan, taken out of the model before blending)."""
    out = {}
    for r in rows:
        if "error" not in r and r.get("bias_logit"):
            out[r["stat_key"]] = {"n": r["bias_n"], "bias_logit": r["bias_logit"]}
    return out


# ------------------------------------------------------------------ the daily write-up
def pick_order(rows: list[dict], top: int = 5) -> list[dict]:
    """Best legs by calibrated probability: High before Medium before Low, standard lines only, one leg per game
    (legs in one game share its script)."""
    rank = {"High": 0, "Medium": 1, "Low": 2}
    ok = [r for r in rows if "error" not in r and r.get("odds_type") == "standard"]
    ok.sort(key=lambda r: (rank.get(r["confidence"], 3), -r["p_final"]))
    seen, out = set(), []
    for r in ok:
        if r["script"] in seen:
            continue
        seen.add(r["script"])
        out.append(r)
        if len(out) == top:
            break
    return out


def board_logic() -> dict:
    """The published logic, as price_nba applies it."""
    from . import nba_model
    return {**nba_model.V1, **(nba_model.params("current") or {}), "_version": nba_model.load()["current"]["version"]}


def side_numbers(r: dict, side: str, logic: dict | None = None) -> dict:
    """The blend's numbers for `side` of a priced leg under the logic that priced the board: the components flipped
    to that side, history only if the logic uses it, and the probability and label from `recompute` (the same code
    edge verify runs), so a re-sided leg in the history or most-likely list verifies like any other."""
    logic = logic or board_logic()
    same = side == r["side"]
    flip = lambda v: None if v is None else (v if same else 1 - v)
    pm, pk = flip(r["p_model"]), flip(r["p_market"])
    o, u, _ = (r.get("research") or {}).get("season", [0, 0, 0])
    if logic.get("history") == "off" or not (o + u):
        ph, n = None, 0
    else:
        ph, n = (o if side == "over" else u) / (o + u), o + u
    p, conf = recompute(pm, pk, ph, n, f"nba:{r['stat_key']}:{side}", logic)
    return {"p_model": pm, "p_market": pk, "p_hist": ph, "hist_n": n, "p_final": p,
            "confidence": "Low" if r.get("newcomer") else conf}


def history_order(rows: list[dict], top: int = 5, min_games: int = 5, per_game: int = 1) -> list[dict]:
    """The hit-rate method, for comparison: the side each standard line has cleared more often this season (5+ games),
    ranked by that season hit rate, then the last 5, then head-to-head, then sample size; at most `per_game` legs per
    game (one player once; legs from one game never go in one entry together). Each leg
    carries what the model, DraftKings and the blend say about that same side (LESSONS L27: history alone has shown no
    information beyond the price)."""
    logic = board_logic()
    cand = []
    for r in rows:
        if "error" in r or r.get("odds_type") != "standard" or not r.get("research"):
            continue
        rs = r["research"]
        o, u, n = rs["season"]
        if n < min_games:
            continue
        side = "over" if o >= u or r.get("over_only") else "under"
        if side == "under" and r.get("over_only"):
            continue
        k = 0 if side == "over" else 1
        rate = lambda t: t[k] / t[2] if t[2] else 0.0
        cand.append({**r, "side": side, **side_numbers(r, side, logic),
                     "hist_rank": (rate(rs["season"]), rate(rs["last5"]), rate(rs["h2h"]), n), "method": "history"})
    cand.sort(key=lambda r: tuple(-x for x in r["hist_rank"]))
    seen, players, out = {}, set(), []
    for r in cand:
        if seen.get(r["script"], 0) >= per_game or (r["script"], r["player"]) in players:
            continue
        seen[r["script"]] = seen.get(r["script"], 0) + 1
        players.add((r["script"], r["player"]))
        out.append(r)
        if len(out) == top:
            break
    return out


LIKELY_SCRIPT = os.path.join(HERE, "simlab", "likely_sim.js")


def run_likely(ctx: dict, gids: list[str], n: int = N_SIMS, workers: int = 4) -> dict:
    """The most likely game for each game (the page's eng_likely: the most common final score of n runs, then the run
    closest to every rotation player's typical line), with its box score. Parallel Node processes."""
    eng = ctx["eng"]
    chunks = [gids[i::workers] for i in range(workers) if gids[i::workers]]
    procs = []
    os.makedirs(CACHE, exist_ok=True)
    for k, ch in enumerate(chunks):
        ip, op = os.path.join(CACHE, f"likely_in_{k}.json"), os.path.join(CACHE, f"likely_out_{k}.json")
        with open(ip, "w") as f:
            json.dump({"R": eng["R"], "n": n, "games": [{"id": gid, "seed": 4242 + i, "sides": {"home": eng["sides"][gid]["home"], "away": eng["sides"][gid]["away"]},
                                                         "pl": [eng["sides"][gid]["players"]["home"], eng["sides"][gid]["players"]["away"]]} for i, gid in enumerate(ch)]}, f)
        procs.append((subprocess.Popen(["node", LIKELY_SCRIPT, ip, op]), op))
    out = {}
    for p, op in procs:
        if p.wait() == 0:
            with open(op) as f:
                out.update(json.load(f))
    return out


def _usage(players: list[dict], pid: str) -> float | None:
    """Share of the team's projected possessions used (FGA + 0.44 FTA + TOV, per minute x projected minutes)."""
    u = {p["id"]: (p["fga2"] + p["fga3"] + 0.44 * p["fta"] + p["tov"]) * p["min"] for p in players}
    tot = sum(u.values())
    return u.get(pid, 0.0) / tot if tot else None


def _season_usage(team: str, pid: str, before: str, _memo={}) -> float | None:
    """His share of the team's possessions used in this season's games he played (box scores)."""
    from gamesim import nba as gnba
    y = gnba.season_of(before[:10])
    end = (dt.date.fromisoformat(before[:10]) - dt.timedelta(days=1)).strftime("%Y%m%d")
    if (y, end) not in _memo:
        _memo[(y, end)] = gnba.season_games("nba", f"{y}1018", end)
    G = _memo[(y, end)]
    me = tot = 0.0
    for g in G:
        if not g["final"] or team not in (g["home"], g["away"]):
            continue
        rows = gnba._box_cached("nba", g["id"]).get(team, [])
        if not any(r["id"] == pid and not r["dnp"] and r["min"] > 0 for r in rows):
            continue
        for r in rows:
            if r["dnp"] or r["min"] <= 0:
                continue
            u = r["fga"] + 0.44 * r["fta"] + r["tov"]
            tot += u
            me += u if r["id"] == pid else 0.0
    return me / tot if tot else None


def likely_order(rows: list[dict], ctx: dict, likely: dict, top: int | None = None, per_game: int = 99) -> list[dict]:
    """The most-likely-game list: each standard line compared with the player's line in that game's most likely
    simulated run. Kept only when the run's side agrees with the simulation's median (a one-run fluke is dropped) and
    with this season's record at the line; ranked by the calibrated probability for that side (High before Medium),
    then the run's gap over his simulated spread; one leg per game. Each leg
    carries the blend's numbers for that side, the run's box line, the usage shift from teammates out, and what the
    opponent allows to his position."""
    logic = board_logic()
    cand = []
    for r in rows:
        if "error" in r or r.get("odds_type") != "standard" or r["event_id"] not in likely:
            continue
        L = likely[r["event_id"]]
        g = ctx["games"][r["event_id"]]
        side_team = "home" if espn_abbr(r["team"]) == g["home"] else "away"
        me = next((x for x in (L.get("box") or {}).get(side_team, []) if str(x["id"]) == str(r["player_id"])), None)
        if not me:
            continue
        val = sum(me[k] for k in PARTS_KEYS[r["stat_key"]])
        gap = val - r["line"]
        if gap == 0:
            continue
        side = "over" if gap > 0 else "under"
        if side == "under" and r.get("over_only"):
            continue
        if (r["proj"] - r["line"]) * gap < 0:              # the run disagrees with the simulation's median: a fluke
            continue
        rs = r.get("research") or {}
        o, u, n = rs.get("season", [0, 0, 0])
        if n < 3 or (o if side == "over" else u) < (u if side == "over" else o):     # history must not lean the other way
            continue
        spread = max((r["q75"] - r["q25"]) / 1.35, 1.0)
        cand.append({**r, "side": side, **side_numbers(r, side, logic), "method": "likely", "z_gap": abs(gap) / spread,
                     "ml": {"score": L["score"], "home": g["home"], "away": g["away"], "line": me, "value": val, "gap": gap, "maxZ": L.get("maxZ")}})
    # one simulated run is a single draw: it only decides the side together with the median and this season;
    # the order comes from the calibrated probability (ranking by the run's gap rewarded its most extreme lines)
    rank = {"High": 0, "Medium": 1, "Low": 2}
    cand.sort(key=lambda r: (rank.get(r["confidence"], 3), -r["p_final"], -r["z_gap"]))
    seen, out = collections.Counter(), []
    ctx["likely_dropped"] = []          # legs that ranked high enough but had a reason against them (for the report)
    players = set()
    for r in cand:
        # every leg that passes (top=None), one per player; same-game legs are flagged, never two in one entry
        if seen[r["script"]] >= per_game or (r["script"], r["player"]) in players or r["p_final"] < 0.5:
            continue                        # (the blend has to favor the side too: a sub-50% leg isn't a pick)
        _likely_context(r, ctx)
        r["reasons"] = likely_reasons(r)
        against = [x["name"] for x in r["reasons"] if x["verdict"] == "against"]
        if against:                         # every reason must point the same way as the pick (or be neutral)
            ctx.setdefault("likely_dropped", []).append({"player": r["player"], "team": r["team"], "side": r["side"], "line": r["line"],
                                                         "stat": LABEL[r["stat_key"]], "p": round(r["p_final"], 3), "against": against})
            continue
        seen[r["script"]] += 1
        players.add((r["script"], r["player"]))
        out.append(r)
        if top and len(out) == top:
            break
    return out


def _likely_context(r: dict, ctx: dict):
    """Usage tonight vs this season, teammates out, and what the opponent allows to his position."""
    sd = ctx["eng"]["sides"][r["event_id"]]
    side_team = "home" if espn_abbr(r["team"]) == ctx["games"][r["event_id"]]["home"] else "away"
    prof = sd["players"][side_team]["players"]
    out_rows = [x for x in (sd.get("availability") or {}).get(side_team, {}).get("rows", []) if x.get("out_tonight")]
    self_flag = any(find_player(r["player"], [{"name": x["name"]}]) for x in out_rows)
    out_rows = [x for x in out_rows if not find_player(r["player"], [{"name": x["name"]}])]   # never his own name
    r["usage"] = {"tonight": _usage(prof, r["player_id"]), "season": _season_usage(espn_abbr(r["team"]), r["player_id"], ctx["games"][r["event_id"]]["start"]),
                  "out": [{"name": x["name"], "value": x["value"], "missed": x["missed_share"]} for x in out_rows],
                  "min_tonight": next((p["min"] for p in prof if p["id"] == r["player_id"]), None),
                  "min_season": next(((p.get("season") or {}).get("min") for p in prof if p["id"] == r["player_id"]), None),
                  "self_absent": self_flag}
    pos = next((p.get("research", {}).get("pos") for p in prof if p["id"] == r["player_id"]), None)
    oa = (sd.get("opp_allowed") or {}).get(side_team) or {}
    r["pos"] = pos
    r["pos_allows"] = {k: {**(oa.get(k, {}).get("pos", {}).get(pos) or {}), "all": oa.get(k, {}).get("per_game"), "all_rank": oa.get(k, {}).get("rank"),
                           "league": oa.get(k, {}).get("league"), "all_100": oa.get(k, {}).get("per_100"),
                           "league_all_100": oa.get(k, {}).get("league_100")} for k in PARTS_KEYS[r["stat_key"]]} if pos else {}


def _lean(x: float | None, ref: float | None, band: float) -> int:
    """+1 if x is above ref by more than the band (a fraction of ref), -1 if below, 0 if inside it or unknown."""
    if x is None or not ref:
        return 0
    r = x / ref - 1
    return 1 if r > band else -1 if r < -band else 0


def _combine(*v: str) -> str:
    """A reason built from several readings: against if any reading is against, else supports if any supports."""
    return "against" if "against" in v else "supports" if "supports" in v else "neutral"


def history_line(r: dict, vd=None, cmp=None) -> tuple[str, str]:
    """One history reason (user audit, 2026-11-06: season, last 5 and head-to-head are overlapping views of the same
    games, so they count once): this season's count and average, the season rate at tonight's projected minutes,
    the last-5 count with its average (trend shown), head-to-head only when those games had comparable minutes.
    The verdict is against when any of the season count, the season average, the minutes-scaled rate or the last-5
    average points the other way."""
    rs = r.get("research") or {}
    sgn = 1 if r["side"] == "over" else -1
    vd = vd or (lambda lean: "neutral" if lean == 0 else "supports" if lean == sgn else "against")
    cmp = cmp or (lambda a, b: (a > b) - (a < b))
    o, u, n = rs.get("season", [0, 0, 0]); avg = rs.get("season_avg")
    k = u if r["side"] == "under" else o
    lg = rs.get("last_games") or []; l5 = sum(lg) / len(lg) if lg else None
    lo, lu, ln = rs.get("last5", [0, 0, 0]); k5 = lu if r["side"] == "under" else lo
    pm_ = (r.get("role") or {}).get("min") or r.get("opp_proj")
    mw = rs["per36"] * pm_ / 36 if rs.get("per36") is not None and pm_ else None
    parts, verdicts = [], []
    if n:
        parts.append(f"{k}/{n} {r['side']} this season (avg {avg:.1f})" if avg is not None else f"{k}/{n} {r['side']} this season")
        verdicts += [vd(cmp(o, u)), vd(cmp(avg, r["line"])) if avg is not None else "neutral"]
    if mw is not None:
        parts.append(f"his season rate at tonight's {pm_:.0f} min gives {mw:.1f}")
        verdicts.append(vd(cmp(mw, r["line"])))
    if ln and l5 is not None:
        trend = "" if avg is None or abs(l5 - avg) < 0.5 else (f", up from {avg:.1f}" if l5 > avg else f", down from {avg:.1f}")
        parts.append(f"last 5: {k5}/{ln} {r['side']}, avg {l5:.1f}{trend}")
        verdicts.append(vd(cmp(l5, r["line"])))
    hg = rs.get("h2h_games") or []
    if hg:
        hm = sum(x[2] for x in hg) / len(hg)
        hk = sum((x[1] < r["line"]) if r["side"] == "under" else (x[1] > r["line"]) for x in hg)
        if pm_ and abs(hm - pm_) <= 0.15 * pm_:          # comparable minutes: within 15% of tonight's projection
            parts.append(f"vs {r.get('opp_espn', 'them')}: {hk}/{len(hg)} {r['side']} on {hm:.0f} min a game")
        else:
            parts.append(f"vs {r.get('opp_espn', 'them')}: {len(hg)} games on {hm:.0f} min a game (not counted: tonight projects {pm_:.0f})")
    if not parts:
        return "neutral", "no games this season"
    v = "against" if "against" in verdicts else "supports" if "supports" in verdicts else "neutral"
    return v, " · ".join(parts)

def likely_reasons(r: dict) -> list[dict]:
    """Every reason shown for a pick, each judged against the pick's side: "supports", "neutral" (no evidence either
    way, or inside a small band around average) or "against". A reason built from several numbers (this season's count
    and average, the head-to-head count and per-36, the matchup by position and for the whole team) is against when any
    of its numbers points the other way, so a card never shows a number that contradicts a tick. The most-likely-game
    list drops any pick with a reason against it; the other lists show the marks."""
    over = r["side"] == "over"
    sgn = 1 if over else -1
    rs = r.get("research") or {}
    out = []
    vd = lambda lean: "neutral" if lean == 0 else "supports" if lean == sgn else "against"
    cmp = lambda a, b: (a > b) - (a < b)

    def add(name, verdict, text):
        out.append({"name": name, "verdict": verdict, "text": text})
    ml = r.get("ml")
    if ml:
        add("most likely game", vd(cmp(ml["value"], r["line"])), f"{ml['value']:.0f} in the most likely game vs a {r['line']} line")
    if r.get("proj") is not None:
        add("simulation median", vd(cmp(r["proj"], r["line"])), f"median {r['proj']} (25-75th {r['q25']}-{r['q75']})")
    pk = r.get("p_market")
    if pk is not None:
        add((r.get("dk") or {}).get("book", "DraftKings"), "supports" if pk >= 0.52 else "against" if pk <= 0.48 else "neutral",
            f"{pk:.0%} for this side after the vig" + (f" (line {r['dk']['line']})" if r.get("dk") else ""))
    else:
        add("DraftKings", "neutral", "no DraftKings price at this line")
    add("history", *history_line(r, vd, cmp))
    pa = {k: v for k, v in (r.get("pos_allows") or {}).items() if v.get("per_game") is not None and v.get("league_per_game")}
    word = lambda l: "softer than" if l > 0 else "tougher than" if l < 0 else "about"
    if pa and all(v.get("per_100") is not None and v.get("league_per_100") for v in pa.values()):
        # per 100 possessions the opponent defended (user audit, 2026-11-06): a fast team allows more per game without
        # being softer, so the lean is read with pace taken out; per game shown alongside
        a100 = sum(v["per_100"] for v in pa.values()); l100 = sum(v["league_per_100"] for v in pa.values())
        allowed = sum(v["per_game"] for v in pa.values())
        ta = [v for v in pa.values() if v.get("all_100") is not None and v.get("league_all_100")]
        t100, tl100 = sum(v["all_100"] for v in ta), sum(v["league_all_100"] for v in ta)
        lp, lt = _lean(a100, l100, 0.03), _lean(t100, tl100, 0.03) if ta else 0
        add("matchup", _combine(vd(lp), vd(lt)),
            f"{r['opp_espn']} allows {a100:.1f} {'+'.join(pa)} per 100 possessions to {r['pos']}s (ESPN's G / F / C), {word(lp)} the league's "
            f"{l100:.1f} (ranks " + ", ".join(f"{k} {v.get('rank_100') or v['rank']}/30" for k, v in pa.items()) + f"; {allowed:.1f} a game)"
            + (f"; {t100:.1f} per 100 to all players, {word(lt)} the league's {tl100:.1f}" if ta else ""))
    elif pa:
        allowed = sum(v["per_game"] for v in pa.values()); league = sum(v["league_per_game"] for v in pa.values())
        ta = [v for v in pa.values() if v.get("all") is not None and v.get("league")]
        team, tleague = sum(v["all"] for v in ta), sum(v["league"] for v in ta)
        lp, lt = _lean(allowed, league, 0.03), _lean(team, tleague, 0.03) if ta else 0
        add("matchup", _combine(vd(lp), vd(lt)),
            f"{r['opp_espn']} allows {allowed:.1f} {'+'.join(pa)} a game to {r['pos']}s (ESPN's G / F / C), {word(lp)} the league's {league:.1f} (ranks "
            + ", ".join(f"{k} {v['rank']}/30" for k, v in pa.items()) + ")"
            + (f"; {team:.1f} to all players, {word(lt)} the league's {tleague:.1f}" if ta else ""))
    else:
        add("matchup", "neutral", "no positional numbers for him")
    us = r.get("usage") or {}
    ut, uss, mt, ms = us.get("tonight"), us.get("season"), us.get("min_tonight"), us.get("min_season")
    if ut and uss and mt and ms:
        scoring = bool({"pts", "tpm"} & set(PARTS_KEYS[r["stat_key"]]))
        vol = (ut * mt) / (uss * ms) if scoring else mt / ms           # possessions he uses (scoring stats), or minutes (reb, ast)
        lv = _lean(vol, 1.0, 0.03)
        add("usage", vd(lv), f"{ut:.0%} of team possessions tonight vs {uss:.0%} this season, {mt:.0f} min vs {ms:.0f}: "
            + (f"about {abs(vol - 1):.0%} {'more' if vol > 1 else 'less'} {'volume' if scoring else 'playing time'}" if lv else "about the same volume")
            + (f"; out: {', '.join(x['name'] for x in us['out'])}" if us.get("out") else ""))
    else:
        add("usage", "neutral", "not enough minutes data")
    if us.get("self_absent"):
        add("availability", "against", "missing from his team's latest box score: confirm he plays")
    return out


MARK = {"supports": "✓", "neutral": "–", "against": "✗"}


def reasons_md(r: dict, head: str) -> list[str]:
    """The reasons as a markdown list, each marked supports (✓), neutral (–) or against (✗)."""
    if not r.get("reasons"):
        return []
    return [head] + [f"  - {MARK[x['verdict']]} {x['name']}: {x['text']}" for x in r["reasons"]]


def likely_write_up(r: dict, verified: str = "", warns: list | None = None) -> str:
    st, line, ml = r["stat_key"], r["line"], r["ml"]
    f = lambda v: "-" if v is None else f"{v:.0%}"
    b = ml["line"]
    lines = [f"### {r.get('bet_id', '')}{r['player']} ({r['team']}) {r['side'].upper()} {line} {LABEL[st]} — {r['game']}",
             f"**Most likely game: {ml['away']} {ml['score'][1]}–{ml['score'][0]} {ml['home']}; he goes {int(b['pts'])} pts / {int(b['reb'])} reb / {int(b['ast'])} ast"
             f" / {int(b['tpm'])} 3PM in {b['min']:.0f} min = {ml['value']:.0f} {LABEL[st]} ({ml['gap']:+.0f} vs the line).** Simulation median {r['proj']} (25–75th {r['q25']}–{r['q75']}).",
             f"- Blended: simulation {f(r['p_model'])}, DraftKings {f(r['p_market'])}, this season {f(r['p_hist'])} → **{r['p_final']:.1%} {r['confidence']}** · {verdict(r)}"
             + (f" · back-check: **{verified}**" if verified else ""),
             ]
    lines += reasons_md(r, "- Reasons (each one supports the pick or is neutral; a pick with any reason against it isn't listed):")
    us = r.get("usage") or {}
    if us.get("out"):
        lines.append("- Out tonight: " + ", ".join(f"{o['name']} ({o['value']:+.1f} Game Score a game)" for o in us["out"]))
    lines.append("- Context, not proof: one simulated game is a single draw, and hit rates, head-to-head and positional allowances added no information beyond the price in the fair test (LESSONS L27).")
    if warns:
        lines.append("- Back-check warnings: " + "; ".join(warns))
    return "\n".join(lines)


def history_write_up(r: dict, verified: str = "", warns: list | None = None) -> str:
    rs, st, line = r["research"], r["stat_key"], r["line"]
    f = lambda v: "-" if v is None else f"{v:.0%}"
    k = 0 if r["side"] == "over" else 1
    cnt = lambda t: f"{t[k]}/{t[2]}" if t[2] else "-"
    lines = [f"### {r.get('bet_id', '')}{r['player']} ({r['team']}) {r['side'].upper()} {line} {LABEL[st]} — {r['game']}",
             f"**History: {cnt(rs['season'])} this season, {cnt(rs['last5'])} last 5, {cnt(rs['h2h'])} vs {r['opp_espn']}**"
             + (f" · per 36 {rs['per36']:.1f}" + (f" (vs {r['opp_espn']} {rs['h2h_per36']:.1f})" if rs.get("h2h_per36") is not None else "") if rs.get("per36") is not None else ""),
             f"- Season average {rs['season_avg']:.1f}; last 5: {', '.join(str(int(x)) for x in rs['last_games'])}" if rs.get("season_avg") is not None else "",
             f"- What the model says about this side: simulation {f(r['p_model'])}, DraftKings {f(r['p_market'])}, blended **{r['p_final']:.1%} {r['confidence']}** · {verdict(r)}"
             + (f" · back-check: **{verified}**" if verified else "")]
    lines += reasons_md(r, "- Context check (✓ supports, – neutral, ✗ against the side; shown, not used to drop the leg):")
    if warns:
        lines.append("- Back-check warnings: " + "; ".join(warns))
    return "\n".join(x for x in lines if x)


def page_row(r: dict, verified: str, warns: list, bet_id: str | None) -> dict:
    """One pick for the Sim Lab page (picks.js)."""
    rs = r.get("research") or {}
    rnd = lambda v, k=3: None if v is None else round(float(v), k)
    return {"id": bet_id, "event_id": r.get("event_id"), "player_id": r.get("player_id"), "stat_key": r["stat_key"],
            "p_uncal": rnd(r.get("p_uncal"), 4), "se_p": rnd(r.get("se_p"), 4), "top5": r.get("top5"),
            "player": r["player"], "team": r["team"], "game": r["game"], "opp": r.get("opp_espn"), "stat": LABEL[r["stat_key"]],
            "side": r["side"], "line": r["line"], "p": rnd(r["p_final"], 4), "conf": r["confidence"], "verdict": verdict(r),
            "model": rnd(r["p_model"]), "market": rnd(r["p_market"]), "hist": rnd(r["p_hist"]), "hist_n": r["hist_n"],
            "median": r.get("proj"), "mean": rnd(r.get("sim_mean"), 1), "q25": r.get("q25"), "q75": r.get("q75"), "minutes": r.get("opp_proj"),
            "dk": None if not r.get("dk") else {"line": r["dk"]["line"], "over": r["dk"].get("over"), "under": r["dk"].get("under"), "book": r["dk"].get("book", "DraftKings"),
                                                "q": rnd(r["dk"].get("q"), 4), "carried": rnd(r["dk"].get("carried"), 4)},
            "dk2": None if not r.get("dk2") else {k: (rnd(v, 4) if isinstance(v, float) else v) for k, v in r["dk2"].items()},
            "role": r.get("role"), "rotation": r.get("rotation"), "team_injuries": r.get("team_injuries"), "outs": r.get("outs"),
            "with_without": r.get("with_without"),
            "held": r.get("held"), "pulled": r.get("pulled"), "odds_type": r.get("odds_type"), "p_home": rnd(r.get("p_home"), 3),
            "season": rs.get("season"), "last5": rs.get("last5"), "h2h": rs.get("h2h"), "per36": rnd(rs.get("per36"), 1),
            "h2h_per36": rnd(rs.get("h2h_per36"), 1), "season_avg": rnd(rs.get("season_avg"), 1), "last_games": rs.get("last_games"),
            "h2h_games": rs.get("h2h_games"), "opp_allows": rs.get("opp_allows"), "flags": "role unconfirmed" in (r.get("notes") or ""),
            "verified": verified, "warns": warns, "start": r.get("start"), "games": rs.get("games"), "dist": r.get("dist"),
            "ml": r.get("ml"), "usage": r.get("usage"), "pos": r.get("pos"), "pos_allows": r.get("pos_allows"), "reasons": r.get("reasons")}


def verdict(r: dict) -> str:
    """ENTRY LEG / LEAN / PASS. v1 rule ("flat2"): High, 65%+, break-even + 2 pts. Fix 3 rule ("se1"): High and
    (recalibrated p - break-even) > 1 standard error of p. Either way: the line type's own break-even (goblins and
    demons need their multiplier), no role flag, and no unexplained tilt in that stat tonight (Fix 7)."""
    be = r.get("break_even", BREAK_EVEN["2-pick power"]) if "break_even" in r else BREAK_EVEN["2-pick power"]
    if r["confidence"] == "High" and not r.get("newcomer"):
        if be is None:
            return "PASS for entries (payout multiplier unknown: enter the app's multiplier to price it)"
        if r.get("tilt_block"):
            return f"PASS for entries (tonight's {LABEL.get(r.get('stat_key'), '')} tilt {r.get('tilt_raw', 0):+.2f} logit is past the 0.25 limit, cause not logged)"
        ok = (r["p_final"] - be > (r.get("se_p") or 0.0)) if r.get("entry_rule") == "se1" else (r["p_final"] >= 0.65 and r["p_final"] >= be + 0.02)
        if ok:
            return "ENTRY LEG (High, clears the 2-pick break-even" + (" by more than its standard error)" if r.get("entry_rule") == "se1" else " by 2+ pts)")
        return "LEAN (High but not clear of the break-even)"
    if r["confidence"] == "Medium":
        return "LEAN (Medium: show, don't enter)"
    return "PASS (below the gate)"


def write_up(r: dict, verified: str = "", warns: list | None = None) -> str:
    rs, st, line = r["research"], r["stat_key"], r["line"]
    f = lambda v: "-" if v is None else f"{v:.0%}"
    side_n = lambda trip: f"{trip[0]} over / {trip[1]} under" + (f" / {trip[2] - trip[0] - trip[1]} push" if trip[2] - trip[0] - trip[1] else "") + f" in {trip[2]}"
    lines = [f"### {r.get('bet_id', '')}{r['player']} ({r['team']}) {r['side'].upper()} {line} {LABEL[st]} — {r['game']}",
             f"**{r['p_final']:.1%} {r['confidence']}** · {verdict(r)}" + (f" · back-check: **{verified}**" if verified else ""),
             "", "| Source | Probability | Basis |", "|---|---|---|",
             f"| Model ({r['n_sims']:,} runs) | {f(r['p_model'])} | median {r['proj']}, mean {r['sim_mean']:.1f}, 25–75th {r['q25']}–{r['q75']}, {r['opp_proj']} minutes"
             + (f"; raw {f(r['p_model_raw'])} before tonight's bias fix ({-r['bias_logit']:+.2f} logit, L7)" if r.get("bias_logit") else "") + " |",
             f"| Market ({(r.get('dk') or {}).get('book', 'DraftKings')}) | {f(r['p_market'])} | " + (f"{r['dk']['line']} at {r['dk']['over']}/{r['dk']['under']}" if r.get("dk") and r["dk"].get("over") else "not posted / not usable") + " |",
             f"| History (this season) | {f(r['p_hist'])} | {side_n(rs['season'])} at {line} (regressed toward the market, or 50% without one, by n/(n+10)) |",
             "", "**Why (model and market):**"]
    gap = r["sim_mean"] - line
    lines.append(f"- The simulation puts him at {r['sim_mean']:.1f} {LABEL[st]} on {r['opp_proj']} minutes, {abs(gap):.1f} {'above' if gap > 0 else 'below'} the line; {f(r['p_model'])} of runs land {r['side']}.")
    if r.get("p_market") is not None:
        lines.append(f"- {(r.get('dk') or {}).get('book', 'DraftKings')}'s price says {f(r['p_market'])} for the {r['side']}" +
                     (": it agrees with the side." if r["p_market"] >= 0.5 else ": it leans the other way, and the blend is pulled toward it."))
    else:
        lines.append("- No sportsbook price yet (DraftKings or Dabble), so nothing checks the model: this can't be High until one posts (agreement rule).")
    lines.append(f"- Game: home win {r['p_home']:.0%} in the simulation; blowout minutes are already in the runs (garbage time).")
    lines += ["", "**Research (context, not a reason: hit rates and streaks didn't predict beyond the price on 2,330 lines, LESSONS L27):**",
              f"- This season: {side_n(rs['season'])} at {line} (average {rs['season_avg']:.1f})" if rs.get("season_avg") is not None else "- This season: no games",
              f"- Last 5: {side_n(rs['last5'])} ({', '.join(str(int(x)) for x in rs['last_games'])})",
              (f"- vs {r['opp_espn']}, last {rs['h2h'][2]} meeting{'s' if rs['h2h'][2] != 1 else ''} (any season): {side_n(rs['h2h'])} ({', '.join(f'{int(v)} in {int(m)} min' for _, v, m in rs['h2h_games'][::-1])})"
               if rs["h2h"][2] else f"- vs {r['opp_espn']}: no meetings in the last two seasons")]
    if rs.get("per36") is not None:
        lines.append(f"- Per 36: {rs['per36']:.1f}" + (f"; vs {r['opp_espn']}: {rs['h2h_per36']:.1f}" if rs.get("h2h_per36") is not None else "")
                     + (f" (head-to-head adjustment in the sim: ×{r['h2h_factor']:.3f})" if r.get("h2h_factor") else ""))
    if rs.get("opp_allows"):
        a = rs["opp_allows"]
        lines.append(f"- {r['opp_espn']} allows {a['per_game']:.1f} {LABEL[st]} a game to opposing players: rank {a['rank']} of {a['teams']} (league {a['league']:.1f}); already in the team simulation")
    lines += [""] + reasons_md(r, "**Context check** (✓ supports, – neutral, ✗ against the side; this list is ranked by the tested blend, so a ✗ is shown, not used to drop the leg):")
    lines += ["", "**What would change it:** a minutes change (injury report, rest, a starter sitting), a line move on DraftKings, or a blowout script."]
    if warns:
        lines.append("**Back-check warnings:** " + "; ".join(warns))
    return "\n".join(lines)
