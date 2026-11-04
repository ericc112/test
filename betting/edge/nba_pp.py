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
import datetime as dt
import json
import os
import re
import subprocess
import unicodedata

import numpy as np

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


def build(dates: set | None = None, gids: set | None = None, n: int = N_SIMS) -> dict:
    """Tonight's NBA games (ESPN), the engine inputs (simlab.nba_engine) and the player distributions. Memoized per
    process, so `edge verify` on several picks re-runs the engine once."""
    from . import simlab
    key = (tuple(sorted(dates or [])), tuple(sorted(gids or [])), n)
    if key in _MEMO:
        return _MEMO[key]
    if gids:              # the back-check right after pricing: reuse that run if it covers these games (< 15 min old)
        now = dt.datetime.now(dt.timezone.utc)
        for k, v in _MEMO.items():
            if isinstance(v, dict) and "sims" in v and set(gids) <= set(v["sims"]) and k[2] == n and \
                    now - dt.datetime.strptime(v["pulled"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc) < dt.timedelta(minutes=15):
                return v
    today = dt.date.today()
    games = simlab.league_games("basketball/nba", [-1, 0, 1], today)
    if dates:
        games = [g for g in games if _us_date(g["start"]) in dates]
    if gids:
        games = [g for g in games if g["id"] in gids]
    eng = simlab.nba_engine(games, today) if games else {"sides": {}, "R": {}}
    sims = run_sims(eng, [g["id"] for g in games], n=n) if games else {}
    _MEMO[key] = {"games": {g["id"]: g for g in games}, "eng": eng, "sims": sims, "pulled": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")}
    return _MEMO[key]


def _us_date(iso: str) -> str:
    """US calendar date of an ISO timestamp (any offset): UTC minus 10 hours, as gamesim.data.us_day."""
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (t.astimezone(dt.timezone.utc) - dt.timedelta(hours=10)).strftime("%Y-%m-%d")


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
           "h2h_games": [[r[0], v(r, 2), r[1]] for r in h2h]}
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


def price_nba(props: list[dict], n: int = N_SIMS) -> list[dict]:
    from .pp import _finish
    want = [p for p in props if p["stat"] in STATS]
    out = [{**p, "error": "stat not priced yet"} for p in props if p["stat"] not in STATS]
    if not want:
        return out
    ctx = build({_us_date(p["start"]) for p in want if p.get("start")}, n=n)
    by_pair = {frozenset((g["home"], g["away"])): g for g in ctx["games"].values()}
    staged = []
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
        sim = ctx["sims"][g["id"]]["players"].get(pl["id"])
        stat, line = STATS[p["stat"]], float(p["line"])
        h = sim["hist"][stat]
        po, pu, ppush = sides_at(h, line)
        dk = ((sd["players"].get("lines") or {}).get(pl["id"]) or {}).get(stat)
        mk_over, mk_note = None, "no DraftKings line for this player and stat yet"
        if dk and dk.get("over") and dk.get("under"):
            qo, qu = _imp(dk["over"]), _imp(dk["under"])
            q = qo / (qo + qu)
            if abs(dk["line"] - line) < 1e-9:
                mk_over, mk_note = q, f"DraftKings {dk['line']} at {dk['over']}/{dk['under']} (no-vig over {q:.0%})"
            else:
                mk_over, _ = market_at(h, dk["line"], q, line)
                mk_note = f"DraftKings {dk['line']} at {dk['over']}/{dk['under']} (no-vig over {q:.0%}), carried to {line}: {mk_over:.0%}"
        elif dk:
            mk_note = f"DraftKings line {dk['line']} but its sides are unlabelled (L2): market not used"
        staged.append((p, g, side, sd, pl, sim, stat, line, h, po, pu, ppush, dk, mk_over, mk_note))
    # L7: the simulation's tilt against DraftKings across the whole board is bias, not edge. Measure it per stat on
    # tonight's props that have a DraftKings price and take it out of the model before blending.
    gaps = {}
    for (p, g, side, sd, pl, sim, stat, line, h, po, pu, ppush, dk, mk_over, mk_note) in staged:
        # main lines only (DraftKings' own line within a point): alt lines read the market off the simulated tails,
        # where logit gaps blow up
        if mk_over is not None and p.get("odds_type") == "standard" and abs(dk["line"] - line) <= 1.0 and 0 < po < 1 - ppush:
            gaps.setdefault(stat, []).append(_lg(po / max(1 - ppush, 1e-9)) - _lg(mk_over))
    bias = {k: float(np.mean(v)) for k, v in gaps.items() if len(v) >= 10}
    for (p, g, side, sd, pl, sim, stat, line, h, po, pu, ppush, dk, mk_over, mk_note) in staged:
        b = bias.get(stat, 0.0)
        if b and 0 < po < 1 - ppush:
            o = _sg(_lg(po / (1 - ppush)) - b) * (1 - ppush)
            po, pu = o, 1 - ppush - o
        opp = g["away"] if side == "home" else g["home"]
        rs = research(pl, stat, line, opp, (sd.get("opp_allowed") or {}).get(side))
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
            (f"; model de-biased {-b:+.2f} logit (tonight's simulation-vs-DraftKings gap on {LABEL[stat]}, n {len(gaps[stat])}, L7)" if b else "")
        row = _finish(p, stat, "nba", po, pu, ppush, rs["season"][0], rs["season"][1], mk_over=mk_over, notes=note)
        if flags and "confidence" in row:
            row["confidence"] = "Low"     # unconfirmed role or minutes: never an entry leg (L5)
        out.append({**row, "event_id": g["id"], "player_id": pl["id"], "proj": quantile(h, 0.5), "opp_proj": round(mean(mh), 1),
                    "script": f"nba:{g['id']}", "newcomer": bool(flags), "research": rs, "game": f"{g['away']} @ {g['home']}",
                    "opp_espn": opp, "sim_mean": mean(h), "q25": quantile(h, 0.25), "q75": quantile(h, 0.75), "dk": dk,
                    "h2h_factor": (pl.get("h2h") or {}).get(stat) if len(PARTS[stat]) == 1 else None, "stat_key": stat,
                    "p_home": ctx["sims"][g["id"]]["p_home"], "pulled": ctx["pulled"], "n_sims": ctx["sims"][g["id"]]["n"],
                    "bias_logit": b, "bias_n": len(gaps.get(stat, [])), "p_model_raw": sides_at(h, line)[0 if row.get("side") == "over" else 1] / max(1 - ppush, 1e-9) if "side" in row else None})
    return out


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


def history_order(rows: list[dict], top: int = 5, min_games: int = 5) -> list[dict]:
    """The hit-rate method, for comparison: the side each standard line has cleared more often this season (5+ games),
    ranked by that season hit rate, then the last 5, then head-to-head, then sample size; one leg per game. Each leg
    carries what the model, DraftKings and the blend say about that same side (LESSONS L27: history alone has shown no
    information beyond the price)."""
    from .blend import final_probability
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
        same = side == r["side"]
        flip = lambda v: None if v is None else (v if same else 1 - v)
        pm, pk, ph = flip(r["p_model"]), flip(r["p_market"]), (o if side == "over" else u) / max(o + u, 1)
        e = final_probability(pm, pk, ph, f"nba:{r['stat_key']}:{side}", o + u)
        conf = "Low" if r.get("newcomer") else e.confidence
        cand.append({**r, "side": side, "p_model": pm, "p_market": pk, "p_hist": ph, "hist_n": o + u, "p_final": e.p, "confidence": conf,
                     "hist_rank": (rate(rs["season"]), rate(rs["last5"]), rate(rs["h2h"]), n), "method": "history"})
    cand.sort(key=lambda r: tuple(-x for x in r["hist_rank"]))
    seen, out = set(), []
    for r in cand:
        if r["script"] in seen:
            continue
        seen.add(r["script"])
        out.append(r)
        if len(out) == top:
            break
    return out


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
    if warns:
        lines.append("- Back-check warnings: " + "; ".join(warns))
    return "\n".join(x for x in lines if x)


def page_row(r: dict, verified: str, warns: list, bet_id: str | None) -> dict:
    """One pick for the Sim Lab page (picks.js)."""
    rs = r.get("research") or {}
    rnd = lambda v, k=3: None if v is None else round(float(v), k)
    return {"id": bet_id, "player": r["player"], "team": r["team"], "game": r["game"], "opp": r.get("opp_espn"), "stat": LABEL[r["stat_key"]],
            "side": r["side"], "line": r["line"], "p": rnd(r["p_final"], 4), "conf": r["confidence"], "verdict": verdict(r),
            "model": rnd(r["p_model"]), "market": rnd(r["p_market"]), "hist": rnd(r["p_hist"]), "hist_n": r["hist_n"],
            "median": r.get("proj"), "mean": rnd(r.get("sim_mean"), 1), "q25": r.get("q25"), "q75": r.get("q75"), "minutes": r.get("opp_proj"),
            "dk": None if not r.get("dk") else {"line": r["dk"]["line"], "over": r["dk"].get("over"), "under": r["dk"].get("under")},
            "season": rs.get("season"), "last5": rs.get("last5"), "h2h": rs.get("h2h"), "per36": rnd(rs.get("per36"), 1),
            "h2h_per36": rnd(rs.get("h2h_per36"), 1), "season_avg": rnd(rs.get("season_avg"), 1), "last_games": rs.get("last_games"),
            "h2h_games": rs.get("h2h_games"), "opp_allows": rs.get("opp_allows"), "flags": "role unconfirmed" in (r.get("notes") or ""),
            "verified": verified, "warns": warns, "start": r.get("start")}


def verdict(r: dict) -> str:
    be = BREAK_EVEN["2-pick power"]
    if r["confidence"] == "High" and r["p_final"] >= 0.65 and r["p_final"] >= be + 0.02 and not r.get("newcomer"):
        return "ENTRY LEG (High, clears the 2-pick break-even by 2+ pts)"
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
             f"| Market (DraftKings) | {f(r['p_market'])} | " + (f"{r['dk']['line']} at {r['dk']['over']}/{r['dk']['under']}" if r.get("dk") and r["dk"].get("over") else "not posted / not usable") + " |",
             f"| History (this season) | {f(r['p_hist'])} | {side_n(rs['season'])} at {line} (regressed toward the market, or 50% without one, by n/(n+10)) |",
             "", "**Why (model and market):**"]
    gap = r["sim_mean"] - line
    lines.append(f"- The simulation puts him at {r['sim_mean']:.1f} {LABEL[st]} on {r['opp_proj']} minutes, {abs(gap):.1f} {'above' if gap > 0 else 'below'} the line; {f(r['p_model'])} of runs land {r['side']}.")
    if r.get("p_market") is not None:
        lines.append(f"- DraftKings' price says {f(r['p_market'])} for the {r['side']}" +
                     (": it agrees with the side." if r["p_market"] >= 0.5 else ": it leans the other way, and the blend is pulled toward it."))
    else:
        lines.append("- No sportsbook price yet, so nothing checks the model: this can't be High until DraftKings posts (agreement rule).")
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
    lines += ["", "**What would change it:** a minutes change (injury report, rest, a starter sitting), a line move on DraftKings, or a blowout script."]
    if warns:
        lines.append("**Back-check warnings:** " + "; ".join(warns))
    return "\n".join(lines)
