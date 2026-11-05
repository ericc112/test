"""PrizePicks NHL board: shots on goal, hits, faceoffs won, points, assists, goals, blocked shots, time on ice and
plus/minus, priced by a player simulation of each game plus DraftKings' milestone ladders where they exist.

Simulation (per game, 20,000 runs): team goals from DraftKings' total and moneyline (a shared scoring shock), split
among skaters by goal rate x simulated ice time; assists the same way (0-2 per goal); shots, hits and blocked shots as
Poisson counts on each player's per-60 rate x ice time x a team pace shock x the opponent's factor x the player's own
game swing; faceoffs taken on rate x ice time and won at his win rate against the opponent's (log5); plus/minus from
even-strength goals and his share of even-strength ice time. Rates come from this season's ESPN box scores (recency
weighted, shrunk toward the team's position average); ice time from his last five games.

Market: DraftKings' "N+" milestone ladders (shots on goal, points, assists, goals), de-vigged and fit with a Poisson,
priced at the PrizePicks line. Hits, faceoffs, blocks, ice time and plus/minus have no DraftKings line in the feed.

Blend: this player model is new and untested against closing lines, so it gets the weights the NBA fair test
supported (model 0.2, market 0.8, no history) and a missing market counts as 50%; a leg without a market can't rise
above Low. History, the last 5, head-to-head, the matchup and ice time are shown as reasons, not inputs.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import math
import os

import numpy as np

from gamesim import data, nhl as gnhl

STATS = {"Shots On Goal": "sog", "Hits": "hits", "Faceoffs Won": "fow", "Points": "points", "Assists": "assists",
         "Goals": "goals", "Blocked Shots": "blocks", "Time On Ice": "toi", "Plus/Minus": "pm"}
LABEL = {"sog": "shots on goal", "hits": "hits", "fow": "faceoffs won", "points": "points", "assists": "assists", "goals": "goals",
         "blocks": "blocked shots", "toi": "time on ice", "pm": "plus/minus"}
LADDER = {"sog": "Shots on Goal Milestones", "points": "Points Milestones", "assists": "Assists Milestones", "goals": "Goals Milestones"}
ESPN = {"UTA": "UTAH", "VGK": "VGK", "LA": "LA", "NJ": "NJ", "TB": "TB", "SJ": "SJ"}
BLEND = {"intercept": 0.0, "w_model": 0.2, "w_market": 0.8, "w_hist": 0.0}
MILESTONE_HOLD = 0.93
N_SIMS = 20000
SEASON_START = "20261001"
BREAK_EVEN = {"standard": 0.577}
LEAGUE_LOG = {}


def espn_abbr(a: str | None) -> str:
    return ESPN.get((a or "").upper(), (a or "").upper())


def _mins(x) -> float:
    try:
        m, s = (str(x).split(":") + ["0"])[:2]
        return float(m) + float(s) / 60
    except ValueError:
        return 0.0


# ------------------------------------------------------------------ data: skater box scores
def skater_games(end: str, start: str = SEASON_START) -> list[dict]:
    """A season's final games with every skater's line (ESPN box scores, cached)."""
    out = []
    for g in gnhl.season_games(start, end):
        if not g.get("final"):
            continue
        p = os.path.join(data.CACHE, f"nhl_sum_{g['id']}.json")
        if not os.path.exists(p):
            continue
        s = json.load(open(p))
        sk = {}
        for t in (s.get("boxscore") or {}).get("players", []):
            ab = t["team"]["abbreviation"]
            P = {}
            for cat in t.get("statistics", []):
                if cat.get("name") not in ("forwards", "defenses"):
                    continue
                lab = cat["labels"]
                for a in cat["athletes"]:
                    st = dict(zip(lab, a.get("stats", [])))
                    toi = _mins(st.get("TOI"))
                    if toi <= 0:
                        continue
                    f = lambda k: data.f(st.get(k), 0) or 0.0
                    P[str(a["athlete"]["id"])] = {"name": a["athlete"]["displayName"], "pos": "D" if cat["name"] == "defenses" else "F",
                                                  "toi": toi, "pptoi": _mins(st.get("PPTOI")), "estoi": _mins(st.get("ESTOI")),
                                                  "goals": f("G"), "assists": f("A"), "sog": f("S"), "hits": f("HT"), "blocks": f("BS"),
                                                  "fw": f("FW"), "fl": f("FL"), "pm": f("+/-")}
            sk[ab] = P
        out.append({"id": g["id"], "date": g["date"], "home": g["home"], "away": g["away"],
                    "score": {g["home"]: g["score"]["home"], g["away"]: g["score"]["away"]}, "skaters": sk})
    return out


def stat_value(p: dict, m: str) -> float:
    if m == "points":
        return p["goals"] + p["assists"]
    if m == "fow":
        return p["fw"]
    return p[m]


# ------------------------------------------------------------------ profiles
PRIOR_MIN = {"goals": 300.0, "assists": 300.0, "sog": 200.0, "hits": 100.0, "blocks": 100.0}
LAST_SEASON = ("20251001", "20260420")


def last_season_rates(_memo={}) -> dict:
    """Each skater's 2025-26 per-60 rates (all teams), from cached ESPN box scores: the prior for this season's
    rates (in the NBA work, last season's numbers were the single most valuable input)."""
    if "r" in _memo:
        return _memo["r"]
    acc = collections.defaultdict(lambda: collections.defaultdict(float))
    for g in skater_games(LAST_SEASON[1], LAST_SEASON[0]):
        for t, P in g["skaters"].items():
            for pid, x in P.items():
                a = acc[pid]
                for k in ("toi", "goals", "assists", "sog", "hits", "blocks", "fw", "fl"):
                    a[k] += x[k]
    _memo["r"] = {pid: {**{k: a[k] / a["toi"] * 60 for k in ("goals", "assists", "sog", "hits", "blocks")},
                        "fo": (a["fw"] + a["fl"]) / a["toi"] * 60, "fo_win": a["fw"] / max(a["fw"] + a["fl"], 1), "fo_n": a["fw"] + a["fl"],
                        "toi": a["toi"]}
                  for pid, a in acc.items() if a["toi"] >= 200}
    return _memo["r"]


def profiles(team: str, games: list[dict], out_names: set) -> dict:
    """Rotation for one team: projected ice time (recency weighted, last 5 games he played), per-60 rates shrunk
    toward his own 2025-26 rate (else the team's position average) by PRIOR_MIN minutes, faceoff share and win rate."""
    tg = sorted([g for g in games if team in g["skaters"]], key=lambda g: g["date"])
    if not tg:
        return {}
    recent = set()
    for g in tg[-2:]:
        recent |= set(g["skaters"][team])
    acc = collections.defaultdict(lambda: collections.defaultdict(float))
    logs = collections.defaultdict(list)
    for g in tg:
        for pid, p in g["skaters"][team].items():
            a = acc[pid]
            a["name"], a["pos"] = p["name"], p["pos"]
            for k in ("toi", "pptoi", "estoi", "goals", "assists", "sog", "hits", "blocks", "fw", "fl"):
                a[k] += p[k]
            a["gp"] += 1
            logs[pid].append(p)
    pos_tot = collections.defaultdict(lambda: collections.defaultdict(float))
    for a in acc.values():
        for k in ("toi", "goals", "assists", "sog", "hits", "blocks", "fw", "fl"):
            pos_tot[a["pos"]][k] += a[k]
    out = {}
    for pid, a in acc.items():
        if pid not in recent or any(_same(a["name"], n) for n in out_names):
            continue
        L = logs[pid][-5:]
        w = np.array([0.85 ** (len(L) - 1 - i) for i in range(len(L))])
        toi = float(np.average([x["toi"] for x in L], weights=w))
        sd = max(float(np.std([x["toi"] for x in logs[pid][-10:]])) if len(logs[pid]) > 1 else 2.0, 1.5)
        pt = pos_tot[a["pos"]]
        ls = last_season_rates().get(pid)

        def rate(k):
            prior = (ls[k] / 60) if ls else pt[k] / max(pt["toi"], 1)
            return (a[k] + PRIOR_MIN[k] * prior) / (a["toi"] + PRIOR_MIN[k]) * 60
        fo = a["fw"] + a["fl"]
        out[pid] = {"id": pid, "name": a["name"], "pos": a["pos"], "team": team, "gp": int(a["gp"]), "toi": toi, "toi_sd": sd,
                    "toi_avg": a["toi"] / a["gp"], "pptoi": a["pptoi"] / a["gp"], "estoi": a["estoi"] / a["gp"],
                    "r_goals": rate("goals"), "r_assists": rate("assists"), "r_sog": rate("sog"), "r_hits": rate("hits"),
                    "r_blocks": rate("blocks"),
                    "r_fo": (fo + 100 * ((ls["fo"] / 60) if ls else (pt["fw"] + pt["fl"]) / max(pt["toi"], 1))) / (a["toi"] + 100) * 60,
                    "fo_win": (a["fw"] + 60 * (ls["fo_win"] if ls and ls["fo_n"] >= 100 else 0.5)) / (fo + 60),
                    "prior": "2025-26" if ls else "position average", "thin": a["gp"] < 3, "logs": logs[pid]}
    return out


def _same(a: str, b: str) -> bool:
    from .nba_pp import _norm
    return _norm(a) == _norm(b)


def team_factors(games: list[dict]) -> dict:
    """Per team, per game: shots, hits and blocks it records and allows, faceoff win rate, and league averages."""
    f = collections.defaultdict(lambda: collections.defaultdict(list))
    for g in games:
        for t in (g["home"], g["away"]):
            o = g["away"] if t == g["home"] else g["home"]
            if t not in g["skaters"] or o not in g["skaters"]:
                continue
            S, O = g["skaters"][t].values(), g["skaters"][o].values()
            for k in ("sog", "hits", "blocks", "goals"):
                f[t][k + "_for"].append(sum(p[k] for p in S))
                f[t][k + "_against"].append(sum(p[k] for p in O))
            f[t]["fw"].append(sum(p["fw"] for p in S)); f[t]["fl"].append(sum(p["fl"] for p in S))
    out = {t: {k: float(np.mean(v)) for k, v in d.items()} for t, d in f.items()}
    lg = {k: float(np.mean([d[k] for d in out.values()])) for k in next(iter(out.values()))} if out else {}
    for t, d in out.items():
        d["fo_pct"] = d["fw"] / max(d["fw"] + d["fl"], 1)
    return {"teams": out, "league": lg}


# ------------------------------------------------------------------ market
def dk_ladders(gid: str) -> dict:
    """{(stat, athlete id): {k: american price of k+}} from ESPN's DraftKings propBets feed."""
    import re
    items, page = [], 1
    while True:
        d = data._json(f"https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/{gid}/competitions/{gid}/odds/100/propBets"
                       f"?lang=en&region=us&limit=1000&page={page}", f"nhl_props_{gid}_{page}.json", 900)
        items += d.get("items", [])
        if page >= d.get("pageCount", 1):
            break
        page += 1
    lad = collections.defaultdict(dict)
    inv = {v: k for k, v in LADDER.items()}
    for x in items:
        name = (x.get("type") or {}).get("name")
        if name not in inv:
            continue
        m = re.search(r"/athletes/(\d+)", (x.get("athlete") or {}).get("$ref", ""))
        k = ((x.get("current") or {}).get("target") or {}).get("value")
        a = ((x.get("odds") or {}).get("american") or {}).get("value")
        if m and k is not None and a not in (None, ""):
            try:
                lad[(inv[name], m.group(1))][int(k)] = float(str(a).replace("+", ""))
            except ValueError:
                pass
    return lad


def ladder_lambda(ladder: dict) -> float | None:
    """Poisson mean that best fits a de-vigged 'k+' ladder (points between 10% and 90% implied)."""
    imp = {k: (100 / (a + 100) if a > 0 else -a / (-a + 100)) * MILESTONE_HOLD for k, a in ladder.items()}
    pts = {k: v for k, v in imp.items() if 0.1 <= v <= 0.9}
    if not pts:
        return None
    sf = lambda lam, k: 1 - sum(math.exp(-lam) * lam ** j / math.factorial(j) for j in range(k))
    return float(min(np.linspace(0.02, 12, 600), key=lambda lam: sum((sf(lam, k) - v) ** 2 for k, v in pts.items())))


def poisson_over(lam: float, line: float) -> float:
    """P(over) excluding a push, for a Poisson count."""
    pmf = lambda j: math.exp(-lam) * lam ** j / math.factorial(j)
    under = sum(pmf(j) for j in range(int(math.ceil(line))))
    push = pmf(int(line)) if float(line).is_integer() else 0.0
    return (1 - under - push) / max(1 - push, 1e-9)


# ------------------------------------------------------------------ game: environment and simulation
def team_lambdas(total: float | None, ml_home: float | None, ml_away: float | None, default: float = 6.1) -> tuple[float, float]:
    """Expected goals (home, away) from DraftKings' total and moneyline: the home share is solved so independent
    Poisson scoring (ties split, as overtime) gives the no-vig home win probability."""
    tot = float(total) if total else default
    imp = lambda a: 100 / (a + 100) if a > 0 else -a / (-a + 100)
    if ml_home is None or ml_away is None:
        return tot * 0.51, tot * 0.49
    ph = imp(ml_home) / (imp(ml_home) + imp(ml_away))
    k = np.arange(0, 15)
    pmf = lambda lam: np.exp(-lam) * lam ** k / np.array([math.factorial(int(j)) for j in k])

    def win(s):
        a, b = pmf(tot * s), pmf(tot * (1 - s))
        M = np.outer(a, b)
        return float(np.tril(M, -1).sum() + 0.5 * np.trace(M))
    lo, hi = 0.2, 0.8
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if win(mid) < ph else (lo, mid)
    s = (lo + hi) / 2
    return tot * s, tot * (1 - s)


def _alloc(rng, total: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Split each run's team count among players (sequential binomials = multinomial), w: (runs, players)."""
    n, P = w.shape
    out = np.zeros((n, P), dtype=np.int64)
    rem, wr = total.astype(np.int64).copy(), w.sum(1)
    for j in range(P):
        p = np.where(wr > 0, w[:, j] / np.maximum(wr, 1e-12), 0.0)
        x = rng.binomial(rem, np.clip(p, 0, 1))
        out[:, j] = x
        rem -= x
        wr = wr - w[:, j]
    return out


def simulate(game: dict, prof: dict, tf: dict, n: int = N_SIMS, seed: int = 11) -> dict:
    """One game, n runs: per player arrays for every PrizePicks stat, plus team goals."""
    rng = np.random.default_rng(seed)
    H, A = game["home"], game["away"]
    lh, la = team_lambdas(game.get("total"), game.get("ml_home"), game.get("ml_away"))
    lg, T = tf["league"], tf["teams"]
    res = {"teams": {}, "players": {}}
    goals = {}
    for t, o, lam in ((H, A, lh), (A, H, la)):
        shock = rng.gamma(1 / 0.12 ** 2, 0.12 ** 2, n)
        goals[t] = rng.poisson(lam * shock)
    for t, o in ((H, A), (A, H)):
        ps = list(prof[t].values())
        if not ps:
            continue
        ft, fo_ = T.get(t, {}), T.get(o, {})
        pace = rng.lognormal(-0.01 ** 2 / 2, 0.10, n)
        f_sog = (fo_.get("sog_against", lg.get("sog_against", 28)) / max(lg.get("sog_against", 28), 1))
        f_hit = (fo_.get("hits_against", lg.get("hits_against", 22)) / max(lg.get("hits_against", 22), 1))
        f_blk = (fo_.get("sog_for", lg.get("sog_for", 28)) / max(lg.get("sog_for", 28), 1))
        toi = np.clip(rng.normal([p["toi"] for p in ps], [p["toi_sd"] for p in ps], (n, len(ps))), 0.0, 32.0)
        z0 = rng.normal(size=(n, len(ps)))
        sw = lambda: np.exp(0.22 * (0.6 * z0 + 0.8 * rng.normal(size=(n, len(ps)))) - 0.22 ** 2 / 2)
        v_s, v_h, v_b = sw(), sw(), sw()
        r = lambda k: np.array([p[k] for p in ps])
        sog = rng.poisson(r("r_sog") * toi / 60 * pace[:, None] * f_sog * v_s)
        hits = rng.poisson(r("r_hits") * toi / 60 * pace[:, None] * f_hit * v_h)
        blocks = rng.poisson(r("r_blocks") * toi / 60 * pace[:, None] * f_blk * v_b)
        fo = rng.poisson(r("r_fo") * toi / 60)
        opp_fo = fo_.get("fo_pct", 0.5)
        pw = r("fo_win")
        log5 = pw * (1 - opp_fo) / np.maximum(pw * (1 - opp_fo) + (1 - pw) * opp_fo, 1e-9)
        fow = rng.binomial(fo, log5)
        g = _alloc(rng, goals[t], r("r_goals") * toi * v_s)
        n_ast = rng.binomial(2 * goals[t], 0.77)                       # ~1.55 assists per goal
        a = np.minimum(_alloc(rng, n_ast, r("r_assists") * toi * v_s), goals[t][:, None])
        es = np.maximum(r("estoi"), 0.1)
        on = np.clip(5 * es / es.sum(), 0, 0.95)
        gf_es, ga_es = rng.binomial(goals[t], 0.76), rng.binomial(goals[o], 0.76)
        pm = rng.binomial(gf_es[:, None], on) - rng.binomial(ga_es[:, None], on)
        for j, p in enumerate(ps):
            res["players"][p["id"]] = {"name": p["name"], "team": t, "pos": p["pos"], "sog": sog[:, j], "hits": hits[:, j],
                                       "blocks": blocks[:, j], "fow": fow[:, j], "goals": g[:, j], "assists": a[:, j],
                                       "points": g[:, j] + a[:, j], "toi": toi[:, j], "pm": pm[:, j], "prof": p}
        res["teams"][t] = {"goals": goals[t]}
    return res


# ------------------------------------------------------------------ pricing a line
def _side_probs(arr: np.ndarray, line: float) -> tuple[float, float, float]:
    over = float(np.mean(arr > line))
    push = float(np.mean(arr == line)) if float(line).is_integer() else 0.0
    return over, 1 - over - push, push


def price_leg(G: dict, name: str, m: str, line: float, over_only: bool = False, side: str | None = None) -> dict | None:
    """One PrizePicks line priced from a simulated game G (see price_board). `side` forces a side (verify)."""
    from .blend import final_probability, load_adjustments
    from .nba_pp import find_player
    sim = G["sim"]
    plist = [{"name": p["name"], "id": pid} for pid, p in sim["players"].items()]
    hit = find_player(name, plist) if plist else None
    if not hit:
        return None
    pid = hit["id"]
    p = sim["players"][pid]
    arr = p[m]
    so, su, push = _side_probs(arr, line)
    lam = None
    if m in LADDER and (m, pid) in G["ladders"]:
        lam = ladder_lambda(G["ladders"][(m, pid)])
    mk_over = poisson_over(lam, line) if lam is not None else None
    logs = p["prof"]["logs"]
    ho = sum(stat_value(x, m) > line for x in logs); hu = sum(stat_value(x, m) < line for x in logs)
    adj = load_adjustments()
    adj["blend_by_sport"] = {**(adj.get("blend_by_sport") or {}), "nhl": BLEND}
    flags = []
    if p["prof"]["thin"]:
        flags.append(f"THIN SAMPLE: {p['prof']['gp']} games with the team")
    med = float(np.median(arr))
    if m != "pm" and abs(line - med) > max(1.5 if m != "toi" else 2.5, 0.5 * med):
        flags.append(f"line {line} is far from the model median {med:.1f}: the book likely knows a role or usage the box scores don't")
    best = None
    for sd in (["over"] if over_only else ["over", "under"]):
        if side and sd != side:
            continue
        pm = (so if sd == "over" else su) / max(1 - push, 1e-9)
        pk = None if mk_over is None else (mk_over if sd == "over" else 1 - mk_over)
        e = final_probability(pm, 0.5 if pk is None else pk, None, f"nhl:nhl_{m}:{sd}", 0, adj)
        conf = e.confidence
        why = []
        if pk is None and conf in ("High", "Medium"):
            conf, why = "Low", ["no DraftKings line for this stat: the untested player model alone can't carry a leg"]
        if flags and conf in ("High", "Medium"):
            conf = "Low"
        if best is None or e.p > best["p_final"]:
            best = {"side": sd, "p_model": round(pm, 4), "p_market": None if pk is None else round(pk, 4), "p_hist": None, "hist_n": 0,
                    "p_final": e.p, "confidence": conf, "why": why}
    return {"player_id": pid, "sim_name": p["name"], "team_espn": p["team"], "dk_lambda": lam, "median": float(np.median(arr)),
            "mean": float(np.mean(arr)), "q25": float(np.percentile(arr, 25)), "q75": float(np.percentile(arr, 75)),
            "toi_proj": p["prof"]["toi"], "flags": flags, "hist": (int(ho), int(hu)), **best}


def research(p: dict, m: str, line: float, opp: str, games: list[dict]) -> dict:
    logs = [(g["date"][:10], next((t for t in (g["home"], g["away"]) if t != p["team"]), ""), g["skaters"][p["team"]][p["id"]])
            for g in sorted(games, key=lambda g: g["date"]) if p["team"] in g["skaters"] and p["id"] in g["skaters"][p["team"]]]
    vals = [(d, o, stat_value(x, m), x["toi"]) for d, o, x in logs]
    cnt = lambda L: [sum(v > line for _, _, v, _ in L), sum(v < line for _, _, v, _ in L), len(L)]
    h2h = [x for x in vals if x[1] == opp]
    avg = lambda L: float(np.mean([v for _, _, v, _ in L])) if L else None
    return {"season": cnt(vals), "last5": cnt(vals[-5:]), "h2h": cnt(h2h), "season_avg": avg(vals), "last5_avg": avg(vals[-5:]),
            "h2h_avg": avg(h2h), "last_games": [v for _, _, v, _ in vals[-5:]], "toi_avg": float(np.mean([t for *_, t in vals])) if vals else None}


def verdict(r: dict) -> str:
    be = BREAK_EVEN.get(r.get("odds_type"))
    if be is None:
        return "PASS (payout multiplier unknown for this line type)"
    if r["confidence"] == "High" and r["p_final"] >= 0.65 and r["p_final"] >= be + 0.02:
        return f"ENTRY LEG (High, {r['p_final']:.0%} vs break-even {be:.1%})"
    if r["confidence"] in ("High", "Medium"):
        return "LEAN (Medium: show, don't enter)" if r["confidence"] == "Medium" else "LEAN (High but under 65%)"
    return "PASS (below the gate)"


# ------------------------------------------------------------------ the board
def tonight_games(day: dt.date) -> list[dict]:
    """ESPN's NHL games for a US day, with DraftKings' total, moneylines and tonight's injury report."""
    out = []
    sb = data._json(f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates={day:%Y%m%d}", f"nhl_sb_{day:%Y%m%d}.json", 900)
    for e in sb.get("events", []):
        s = data._json(f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event={e['id']}", f"nhl_sum_{e['id']}.json", 900)
        g = gnhl.parse(s)
        if not g:
            continue
        outs = {t["team"]["abbreviation"]: {i["athlete"]["displayName"] for i in t.get("injuries", []) or []
                                            if (i.get("status") or "").lower() in ("out", "injured reserve", "doubtful")}
                for t in s.get("injuries", []) or []}
        out.append({"id": g["id"], "date": g["date"], "home": g["home"], "away": g["away"], "status": e["competitions"][0]["status"]["type"]["name"],
                    "total": (g.get("line") or {}).get("total"), "ml_home": (g.get("line") or {}).get("ml_home"),
                    "ml_away": (g.get("line") or {}).get("ml_away"), "out": outs})
    return out


def price_board(props: list[dict], n: int = N_SIMS, log=print, store: dict | None = None) -> list[dict]:
    props = [p for p in props if p["stat"] in STATS and p.get("odds_type") == "standard"]
    if not props:
        return []
    days = sorted({dt.datetime.fromisoformat(p["start"]).date() for p in props if p.get("start")})
    games = [g for d in days for g in tonight_games(d)]
    by = {(espn_abbr(g["away"]), espn_abbr(g["home"])): g for g in games}
    hist = skater_games(dt.date.today().strftime("%Y%m%d"))
    tf = team_factors(hist)
    rows = []
    for key in sorted({(espn_abbr(p.get("away")), espn_abbr(p.get("home"))) for p in props}):
        g = by.get(key) or by.get((key[0].replace("UTAH", "UTA"), key[1]))
        mine = [p for p in props if (espn_abbr(p.get("away")), espn_abbr(p.get("home"))) == key]
        if not g:
            rows += [{**p, "error": "game not on ESPN's schedule"} for p in mine]
            continue
        before = [x for x in hist if x["date"] < g["date"]]
        prof = {t: profiles(t, before, g["out"].get(t, set())) for t in (g["home"], g["away"])}
        log(f"  {g['away']} @ {g['home']}: {len(mine)} lines, simulating...")
        G = {"game": g, "sim": simulate(g, prof, tf, n), "ladders": dk_ladders(g["id"]), "hist": before, "tf": tf}
        if store is not None:
            store[g["id"]] = G
        for p in mine:
            m = STATS[p["stat"]]
            x = price_leg(G, p["player"], m, p["line"], p.get("over_only", False))
            if not x:
                rows.append({**p, "error": "player not in the projected rotation (scratched, injured or new)"})
                continue
            opp = g["home"] if x["team_espn"] == g["away"] else g["away"]
            sp = G["sim"]["players"][x["player_id"]]
            note = (f"nhl sim median {x['median']:.1f} (25-75th {x['q25']:.0f}-{x['q75']:.0f}), toi {x['toi_proj']:.1f}"
                    + (f"; DraftKings ladder mean {x['dk_lambda']:.2f}" if x["dk_lambda"] is not None else "; no DraftKings line")
                    + (f"; flags: {', '.join(x['flags'])}" if x["flags"] else "") + (f"; {x['why'][0]}" if x["why"] else "")
                    + f"; history {x['hist'][0]} over / {x['hist'][1]} under; pulled {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%MZ}")
            rows.append({**p, **x, "event_id": g["id"], "team": x["team_espn"], "opp": opp, "market_key": f"nhl_{m}", "stat_key": m,
                         "sport": "nhl", "script": f"nhl:{g['id']}", "game": f"{g['away']} @ {g['home']}", "start": g["date"],
                         "proj": x["median"], "opp_proj": round(x["toi_proj"], 1), "notes": note, "newcomer": bool(x["flags"]),
                         "research": research(sp["prof"], m, p["line"], opp, before), "dk_line": None})
    return rows


# ------------------------------------------------------------------ lists (same shape as nfl_pp, for the shared picks command)
def days(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    from zoneinfo import ZoneInfo
    by = collections.defaultdict(list)
    for r in rows:
        if "error" in r or not r.get("start"):
            continue
        t = dt.datetime.fromisoformat(r["start"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
        by[t.strftime("%Y-%m-%d")].append(r)
    return [(dt.date.fromisoformat(d).strftime("%a %b %-d"), by[d]) for d in sorted(by)]


def per_game_cap(rows: list[dict], top: int) -> int:
    g = len({r["script"] for r in rows})
    return 1 if g >= top else min(3, -(-top // max(g, 1)))


def _take(cand: list[dict], top: int, per_game: int, accept=None) -> list[dict]:
    seen, out = collections.Counter(), []
    for r in cand:
        if seen[r["script"]] >= per_game or any(o["player"] == r["player"] for o in out if o["script"] == r["script"]):
            continue
        if accept and not accept(r):
            continue
        seen[r["script"]] += 1
        out.append(r)
        if len(out) == top:
            break
    return out


RANK = {"High": 0, "Medium": 1, "Low": 2}


def pick_order(rows: list[dict], top: int = 5, per_game: int = 1) -> list[dict]:
    ok = sorted([r for r in rows if "error" not in r], key=lambda r: (RANK.get(r["confidence"], 3), -r["p_final"]))
    return _take(ok, top, per_game)


def history_order(rows: list[dict], store: dict, top: int = 5, min_games: int = 5, per_game: int = 1) -> list[dict]:
    """The hit-rate method, for comparison (LESSONS L27): the side each line cleared more often this season (5+
    games), ranked by that rate, then the last 5, then sample size. Each leg carries the model's and DraftKings'
    numbers for that same side."""
    cand = []
    for r in rows:
        if "error" in r or not r.get("research"):
            continue
        o, u, n = r["research"]["season"]
        if n < min_games or o == u:
            continue
        side = "over" if o > u else "under"
        if side == "under" and r.get("over_only"):
            continue
        k = 0 if side == "over" else 1
        rate = lambda t: t[k] / t[2] if t[2] else 0.0
        x = r if side == r["side"] else {**r, **price_leg(store[r["event_id"]], r["player"], r["stat_key"], r["line"], side=side)}
        cand.append({**x, "method": "history", "hist_rank": (rate(r["research"]["season"]), rate(r["research"]["last5"]), n)})
    cand.sort(key=lambda r: tuple(-v for v in r["hist_rank"]))
    return _take(cand, top, per_game)


def most_likely_run(G: dict) -> dict:
    """The most common final score, then the run with that score closest to every skater's median shots and ice time."""
    sim = G["sim"]
    t = list(sim["teams"])
    a, b = sim["teams"][t[0]]["goals"], sim["teams"][t[1]]["goals"]
    pairs, counts = np.unique(np.stack([a, b], 1), axis=0, return_counts=True)
    top = pairs[np.argmax(counts)]
    idx = np.where((a == top[0]) & (b == top[1]))[0]
    z = np.zeros(len(idx))
    for p in sim["players"].values():
        for k in ("sog", "toi", "hits"):
            v = p[k]
            sd = float(np.std(v))
            if sd > 1e-9:
                z += ((v[idx] - np.median(v)) / sd) ** 2
    run = int(idx[int(np.argmin(z))])
    return {"run": run, "score": {x: int(sim["teams"][x]["goals"][run]) for x in t}, "share": float(counts.max() / len(a))}


def likely_order(rows: list[dict], store: dict, top: int = 5, drop: list | None = None, per_game: int = 1) -> list[dict]:
    """Kept when the player's line in the game's most likely run, the median and this season's record agree on the
    side, and no reason shown points the other way (drops recorded in `drop`)."""
    runs = {e: most_likely_run(G) for e, G in store.items()}
    cand = []
    for r in rows:
        if "error" in r or r["event_id"] not in runs or not r.get("research"):
            continue
        G, L = store[r["event_id"]], runs[r["event_id"]]
        p = G["sim"]["players"].get(str(r["player_id"]))
        if not p:
            continue
        val = float(p[r["stat_key"]][L["run"]])
        gap = val - r["line"]
        if gap == 0:
            continue
        side = "over" if gap > 0 else "under"
        if side == "under" and r.get("over_only"):
            continue
        if (r["median"] - r["line"]) * gap <= 0:
            continue
        o, u, n = r["research"]["season"]
        if n < 3 or (o if side == "over" else u) < (u if side == "over" else o):
            continue
        x = r if side == r["side"] else {**r, **price_leg(G, r["player"], r["stat_key"], r["line"], side=side)}
        box = {k: float(p[k][L["run"]]) for k in ("toi", "sog", "hits", "blocks", "fow", "goals", "assists")}
        cand.append({**x, "method": "likely", "ml": {"score": L["score"], "share": L["share"], "value": val, "gap": gap, "box": box}})
    cand.sort(key=lambda r: (RANK.get(r["confidence"], 3), -r["p_final"]))

    def accept(r):
        r["reasons"] = reasons(r, store[r["event_id"]])
        against = [x["name"] for x in r["reasons"] if x["verdict"] == "against"]
        if against and drop is not None:
            drop.append({"player": r["player"], "side": r["side"], "line": r["line"], "stat": LABEL[r["stat_key"]],
                         "p": round(r["p_final"], 3), "against": against})
        return not against
    return _take(cand, top, per_game, accept)


def allowed(G: dict, team: str, m: str) -> dict | None:
    """What `team` allows per game in this stat (all opposing skaters), rank of 32 (1 = allows the most), league average."""
    if m in ("toi", "pm"):
        return None
    per = collections.defaultdict(list)
    for g in G["hist"]:
        for t in (g["home"], g["away"]):
            o = g["away"] if t == g["home"] else g["home"]
            if o in g["skaters"]:
                per[t].append(sum(stat_value(x, m) for x in g["skaters"][o].values()))
    if team not in per or len(per[team]) < 3:
        return None
    avg = {t: float(np.mean(v)) for t, v in per.items()}
    ranked = sorted(avg.values(), reverse=True)
    return {"per_game": avg[team], "rank": ranked.index(avg[team]) + 1, "teams": len(ranked),
            "league": float(np.mean([x for v in per.values() for x in v]))}


def reasons(r: dict, G: dict) -> list[dict]:
    over = r["side"] == "over"
    sgn = 1 if over else -1
    rs = r.get("research") or {}
    vd = lambda lean: "neutral" if lean == 0 else "supports" if lean == sgn else "against"
    cmp = lambda a, b: (a > b) - (a < b)
    comb = lambda *v: "against" if "against" in v else "supports" if "supports" in v else "neutral"
    out = []
    add = lambda name, verdict, text: out.append({"name": name, "verdict": verdict, "text": text})
    lean = lambda x, ref, band: 0 if x is None or not ref else (1 if x / ref - 1 > band else -1 if x / ref - 1 < -band else 0)
    ml = r.get("ml")
    if ml:
        sc = ", ".join(f"{k} {v}" for k, v in ml["score"].items())
        add("most likely game", vd(cmp(ml["value"], r["line"])), f"{ml['value']:.{1 if r['stat_key'] == 'toi' else 0}f} in the most likely game ({sc}) vs a {r['line']} line")
    add("simulation median", vd(cmp(r["median"], r["line"])), f"median {r['median']:.1f} (25-75th {r['q25']:.0f}-{r['q75']:.0f})")
    pk = r.get("p_market")
    if pk is None:
        add("DraftKings", "neutral", "no DraftKings line for this stat")
    else:
        add("DraftKings", "supports" if pk >= 0.52 else "against" if pk <= 0.48 else "neutral",
            f"{pk:.0%} for this side from DraftKings' ladder (mean {r['dk_lambda']:.2f})")
    o, u, n = rs.get("season", [0, 0, 0]); avg = rs.get("season_avg")
    add("this season", comb(vd(cmp(o, u)), vd(cmp(avg, r["line"])) if avg is not None else "neutral"),
        f"{o} over / {u} under in {n}" + (f", average {avg:.1f}" if avg is not None else ""))
    lo, lu, _ = rs.get("last5", [0, 0, 0]); la = rs.get("last5_avg")
    add("last 5", comb(vd(cmp(lo, lu)), vd(cmp(la, r["line"])) if la is not None else "neutral"),
        f"{lo} over / {lu} under" + (f" ({', '.join(f'{v:g}' for v in rs.get('last_games', []))})" if rs.get("last_games") else ""))
    h = rs.get("h2h", [0, 0, 0])
    if h[2]:
        add("head-to-head", comb(vd(cmp(h[0], h[1])), vd(cmp(rs.get("h2h_avg"), r["line"]))),
            f"{h[0]} over / {h[1]} under vs {r['opp']} this season (average {rs['h2h_avg']:.1f})")
    else:
        add("head-to-head", "neutral", f"no meeting with {r['opp']} this season")
    a = allowed(G, r["opp"], r["stat_key"])
    if a:
        lp = lean(a["per_game"], a["league"], 0.03)
        word = "more than" if lp > 0 else "less than" if lp < 0 else "about"
        add("matchup", vd(lp), f"{r['opp']} allows {a['per_game']:.1f} {LABEL[r['stat_key']]} a game to opposing skaters, {word} the league's "
            f"{a['league']:.1f} (rank {a['rank']}/{a['teams']}, 1 = allows the most)")
    else:
        add("matchup", "neutral", "no opponent number for this stat")
    ta = rs.get("toi_avg")
    outs = sorted(G["game"]["out"].get(r["team"], set()))
    if ta:
        lv = lean(r["toi_proj"], ta, 0.05)
        add("ice time", vd(lv) if r["stat_key"] != "pm" else "neutral",
            f"projected {r['toi_proj']:.1f} min vs {ta:.1f} this season" + (f"; out for his team: {', '.join(outs[:4])}" if outs else ""))
    else:
        add("ice time", "neutral", "no ice-time history")
    if r.get("flags"):
        add("role", "against", "; ".join(r["flags"]))
    return out


def gap_rows(ok: list[dict]) -> list[dict]:
    """Where an edge can come from: lines DraftKings' ladder prices furthest from 50/50."""
    rs = sorted([r for r in ok if r.get("p_market") is not None], key=lambda r: -abs(r["p_market"] - 0.5))
    return [{"player": r["player"], "stat": LABEL[r["stat_key"]], "pp": r["line"], "dk": f"mean {r['dk_lambda']:.2f}", "side": r["side"],
             "p": round(r["p_final"], 4), "conf": r["confidence"], "game": r["game"]} for r in rs]


def write_up(r: dict, verified: str = "", warns: list | None = None) -> str:
    f = lambda v: "-" if v is None else f"{v:.0%}"
    lines = [f"### {r.get('bet_id', '')}{r['player']} ({r['team']}) {r['side'].upper()} {r['line']} {LABEL[r['stat_key']]} — {r['game']}",
             f"**{r['p_final']:.1%} {r['confidence']}** · {verdict(r)}" + (f" · back-check: **{verified}**" if verified else ""),
             f"- Sources: DraftKings ladder {f(r['p_market'])}" + (f" (mean {r['dk_lambda']:.2f})" if r.get("dk_lambda") is not None else " (no DraftKings line)")
             + f" · simulation {f(r['p_model'])} · this season {r['hist'][0]} over / {r['hist'][1]} under",
             f"- Simulation: median {r['median']:.1f}, 25–75th {r['q25']:.0f}–{r['q75']:.0f}, {r['toi_proj']:.1f} min projected"]
    if r.get("ml"):
        sc = ", ".join(f"{k} {v}" for k, v in r["ml"]["score"].items())
        lines.insert(2, f"- Most likely game ({sc}): {r['ml']['value']:g} {LABEL[r['stat_key']]} ({r['ml']['gap']:+.1f} vs the line)")
    if r["flags"]:
        lines.append("- Role flags: " + "; ".join(r["flags"]))
    if r.get("reasons"):
        mark = {"supports": "✓", "neutral": "–", "against": "✗"}
        lines.append("- Reasons:" if r.get("ml") else "- Context check (shown, not used to drop the leg):")
        lines += [f"  - {mark[x['verdict']]} {x['name']}: {x['text']}" for x in r["reasons"]]
    if warns:
        lines.append("- Back-check warnings: " + "; ".join(warns))
    return "\n".join(lines)


def game_for(event_id: str, n: int = N_SIMS) -> dict | None:
    """Rebuild one game the way price_board does (for edge verify)."""
    s = data._json(f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary?event={event_id}", f"nhl_sum_{event_id}.json", 900)
    g0 = gnhl.parse(s)
    if not g0:
        return None
    from zoneinfo import ZoneInfo
    day = dt.datetime.fromisoformat(g0["date"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).date()
    g = next((x for x in tonight_games(day) if x["id"] == str(event_id)), None)
    if not g:
        return None
    hist = skater_games(dt.date.today().strftime("%Y%m%d"))
    before = [x for x in hist if x["date"] < g["date"]]
    tf = team_factors(hist)
    prof = {t: profiles(t, before, g["out"].get(t, set())) for t in (g["home"], g["away"])}
    return {"game": g, "sim": simulate(g, prof, tf, n), "ladders": dk_ladders(g["id"]), "hist": before, "tf": tf}
