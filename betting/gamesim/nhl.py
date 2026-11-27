"""NHL event engine: the game clock in 10-second ticks, goals as events at even strength and on power plays.

Data (named sources): ESPN game summaries (team shots, power-play goals and chances, penalties, every goalie's
shots against and saves with time on ice, goals by strength, the DraftKings closing lines), and NHL API
play-by-play (who has a goalie in net) for empty-net rates.

Ratings from this season's earlier games (opponent-adjusted ridge, home term): shots per 60 for and against,
finishing (even-strength goals per shot), power-play chances drawn and conceded, power-play conversion and
penalty kill; goalie save percentage by goalie, shrunk toward the league. The starting goalie is PROJECTED
(the team's most recent starter) unless confirmed.
One simulated game:
  - environment: a finishing shock per team and a save shock per goalie (sd fitted from game-to-game wobble);
  - each tick: penalty chance for each team; at even strength each team scores with its shot rate x finishing x
    (1 - goalie save%); on a power play the attacking team scores at its conversion rate over the two minutes
    (and shorthanded goals at the league rate);
  - endgame: a team down 1 pulls its goalie with about 2 minutes left (down 2: about 3), using the empty-net
    scoring rates measured from NHL play-by-play; 3-on-3 overtime at the fitted overtime scoring rate; shootout.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from collections import defaultdict

import numpy as np

from . import data

PATH = "hockey/nhl"
LAM = 5.0           # games of league-average prior on team rates
GOALIE_K = 600.0    # shots of league-average prior on a goalie's save percentage
TICK = 10.0


def parse(s: dict) -> dict | None:
    comp = s["header"]["competitions"][0]
    st = comp["status"]["type"]["name"]
    t = {x["homeAway"]: x for x in comp["competitors"]}
    g = {"id": s["header"]["id"], "date": comp["date"], "final": st == "STATUS_FINAL", "home": t["home"]["team"]["abbreviation"],
         "away": t["away"]["team"]["abbreviation"], "score": {"home": data.f(t["home"].get("score"), 0), "away": data.f(t["away"].get("score"), 0)},
         "periods": len(t["home"].get("linescores", []) or []), "box": {}, "goalies": {}}
    sd = {x["team"]["abbreviation"]: ("home" if x["team"]["abbreviation"] == g["home"] else "away") for x in s.get("boxscore", {}).get("teams", [])}
    for x in s.get("boxscore", {}).get("teams", []):
        v = {k["name"]: data.f(k["displayValue"], 0) for k in x.get("statistics", [])}
        g["box"][sd[x["team"]["abbreviation"]]] = {"shots": v.get("shotsTotal", 0), "ppg": v.get("powerPlayGoals", 0), "ppo": v.get("powerPlayOpportunities", 0),
                                                   "shg": v.get("shortHandedGoals", 0), "pen": v.get("penalties", 0), "so": v.get("shootoutGoals", 0)}
    for x in s.get("boxscore", {}).get("players", []):
        side = sd.get(x["team"]["abbreviation"])
        for cat in x.get("statistics", []):
            if cat.get("name") != "goalies":
                continue
            lab = cat["labels"]
            gl = []
            for a in cat["athletes"]:
                st_ = dict(zip(lab, a["stats"]))
                mm, ss = (str(st_.get("TOI", "0:0")).split(":") + ["0"])[:2]
                gl.append({"name": a["athlete"]["displayName"], "id": a["athlete"]["id"], "sa": data.f(st_.get("SA"), 0), "sv": data.f(st_.get("SV"), 0),
                           "toi": (data.f(mm, 0) or 0) * 60 + (data.f(ss, 0) or 0)})
            if side:
                g["goalies"][side] = sorted(gl, key=lambda q: -q["toi"])
    ev = defaultdict(float)
    for p in s.get("plays", []) or []:
        if p.get("scoringPlay") and (p.get("period") or {}).get("number", 1) <= 3:
            team = (p.get("team") or {}).get("id")
            strength = (p.get("strength") or {}).get("abbreviation", "even-strength")
            ev[(team, strength)] += 1
    g["goals_by_strength"] = {f"{k[0]}|{k[1]}": v for k, v in ev.items()}
    g["team_ids"] = {sd[x["team"]["abbreviation"]]: x["team"]["id"] for x in s.get("boxscore", {}).get("teams", [])}
    pc = (s.get("pickcenter") or [{}])[0]
    h, a = pc.get("homeTeamOdds") or {}, pc.get("awayTeamOdds") or {}
    num = lambda x: data.f(str(x).replace("+", ""), None) if x not in (None, "") else None
    opn = lambda grp, sd_, k: num(((((pc.get(grp) or {}).get(sd_) or {}).get("open") or {}).get(k) or "").replace("o", "").replace("u", "") or None)
    g["line"] = {"ml_home": num(h.get("moneyLine")), "ml_away": num(a.get("moneyLine")), "total": pc.get("overUnder"),
                 "over_odds": num(pc.get("overOdds")), "under_odds": num(pc.get("underOdds")), "spread_home": -1.5 if (h.get("favorite")) else 1.5,
                 "spread_home_odds": num(h.get("spreadOdds")), "spread_away_odds": num(a.get("spreadOdds")),
                 "ml_home_open": opn("moneyline", "home", "odds"), "ml_away_open": opn("moneyline", "away", "odds"),
                 "spread_home_open": None, "total_open": opn("total", "over", "line"), "provider": (pc.get("provider") or {}).get("name")}
    return g


def season_games(start: str, end: str) -> list[dict]:
    os.makedirs(os.path.join(data.CACHE, "nhl"), exist_ok=True)
    d0, d1 = dt.datetime.strptime(start, "%Y%m%d"), dt.datetime.strptime(end, "%Y%m%d")
    ids, day = [], d0
    while day <= d1:
        try:
            sb = data._json(f"https://site.api.espn.com/apis/site/v2/sports/{PATH}/scoreboard?dates={day:%Y%m%d}", f"nhl_sb_{day:%Y%m%d}.json",
                            None if day.date() < dt.date.today() - dt.timedelta(days=1) else 1800)
            ids += [e["id"] for e in sb.get("events", []) if (e.get("season") or {}).get("type") in (2, None)]
        except RuntimeError:
            pass
        day += dt.timedelta(days=1)
    out = []
    for gid in ids:
        p = os.path.join(data.CACHE, "nhl", f"{gid}.json")
        g = json.load(open(p)) if os.path.exists(p) else None
        if g is None or not g.get("final"):
            try:
                g = parse(data._json(f"https://site.api.espn.com/apis/site/v2/sports/{PATH}/summary?event={gid}", f"nhl_sum_{gid}.json", 900))
            except (RuntimeError, KeyError):
                g = None
            if g and g["final"]:
                json.dump(g, open(p, "w"))
        if g:
            out.append(g)
    return sorted(out, key=lambda g: g["date"])


def empty_net_rates(day_from: str, day_to: str, max_games: int = 120) -> dict:
    """Goals per minute for and against with the goalie pulled, from NHL API play-by-play (situationCode digits:
    away goalie in net, away skaters, home skaters, home goalie in net)."""
    path = os.path.join(data.CACHE, f"nhl_en_{day_from}_{day_to}.json")
    if os.path.exists(path):
        return json.load(open(path))
    secs = for_g = ag_g = 0.0
    n = 0
    day = dt.datetime.strptime(day_from, "%Y%m%d")
    while day <= dt.datetime.strptime(day_to, "%Y%m%d") and n < max_games:
        try:
            sch = data._json(f"https://api-web.nhle.com/v1/schedule/{day:%Y-%m-%d}", f"nhlapi_sch_{day:%Y%m%d}.json", None)
            games = [g for w in sch.get("gameWeek", [])[:1] for g in w.get("games", []) if g.get("gameState") in ("OFF", "FINAL") and g.get("gameType") == 2]
        except RuntimeError:
            games = []
        for g in games:
            if n >= max_games:
                break
            try:
                pbp = data._json(f"https://api-web.nhle.com/v1/gamecenter/{g['id']}/play-by-play", f"nhlapi_pbp_{g['id']}.json", None)
            except RuntimeError:
                continue
            n += 1
            prev_t, prev_code = None, None
            for p in pbp.get("plays", []):
                pd = p.get("periodDescriptor", {})
                if pd.get("number") != 3:
                    continue
                mm, ss = (p.get("timeInPeriod", "0:0").split(":") + ["0"])[:2]
                t = int(mm) * 60 + int(ss)
                code = p.get("situationCode")
                if prev_code and len(prev_code) == 4 and prev_t is not None and (prev_code[0] == "0" or prev_code[3] == "0"):
                    secs += max(0, t - prev_t)
                if code and len(code) == 4 and (code[0] == "0" or code[3] == "0") and p.get("typeDescKey") == "goal":
                    owner = p.get("details", {}).get("eventOwnerTeamId")
                    pulled_home = code[3] == "0"
                    scorer_home = owner == pbp.get("homeTeam", {}).get("id")
                    if scorer_home == pulled_home:
                        for_g += 1        # the team with the extra attacker scored
                    else:
                        ag_g += 1         # empty-net goal against
                prev_t, prev_code = t, code
        day += dt.timedelta(days=1)
    out = {"minutes": secs / 60, "for_per_min": for_g / max(secs / 60, 1e-9), "against_per_min": ag_g / max(secs / 60, 1e-9),
           "goals_for": for_g, "goals_against": ag_g, "games": n, "source": "NHL API play-by-play"}
    json.dump(out, open(path, "w"))
    return out


def prior_home_margin(season_end: str = "2026-04-16") -> dict:
    """Home ice as a league constant: last complete season's home goal margin per game (NHL API standings).
    Flagged in the report as the one prior-season input; early-season home samples are too noisy."""
    d = data._json(f"https://api-web.nhle.com/v1/standings/{season_end}", f"nhlapi_standings_{season_end}.json", None)
    st = d["standings"]
    gp = sum(t["homeGamesPlayed"] for t in st)
    return {"margin": (sum(t["homeGoalsFor"] for t in st) - sum(t["homeGoalsAgainst"] for t in st)) / max(gp, 1), "games": gp,
            "source": f"NHL API standings {season_end}"}


def eb_lambda(rows: list[dict], k: str, lo: float = 2.0, hi: float = 400.0) -> float:
    """Empirical-Bayes prior strength in games: game-to-game noise variance over the variance of true team
    differences (between-team variance of means minus their sampling variance). Noisy stats like finishing
    and power-play % get a strong prior, stable ones like shot rates a light one. No outcomes are used."""
    by = defaultdict(list)
    for r in rows:
        by[r["off"]].append(r[k])
    v = [x for x in by.values() if len(x) >= 3]
    if len(v) < 8:
        return LAM
    within = float(np.mean([np.var(x, ddof=1) for x in v]))
    means = np.array([np.mean(x) for x in v])
    talent = float(np.var(means, ddof=1) - np.mean([np.var(x, ddof=1) / len(x) for x in v]))
    return float(np.clip(within / max(talent, 1e-12), lo, hi))


def ratings(games: list[dict], before: str) -> dict:
    G = [g for g in games if g["final"] and g["date"] < before and len(g["box"]) == 2 and g["goalies"]]
    rows = []
    gsv = defaultdict(lambda: [0.0, 0.0])
    starters = {}
    for g in G:
        for s, o in (("home", "away"), ("away", "home")):
            b, ob = g["box"][s], g["box"][o]
            tid = g["team_ids"].get(s)
            evg = g["goals_by_strength"].get(f"{tid}|even-strength", max(g["score"][s] - b["ppg"] - b["shg"], 0))
            rows.append({"off": g[s], "def": g[o], "home": float(s == "home"), "shots": b["shots"], "fin": evg / max(b["shots"] - 0.12 * b["shots"], 1),
                         "ppo": b["ppo"], "ppc": b["ppg"] / max(b["ppo"], 1),
                         "w": {"shots": 1.0, "fin": max(b["shots"], 1), "ppo": 1.0, "ppc": max(b["ppo"], 0.5)}})
            for q in g["goalies"].get(s, []):
                gsv[q["id"]][0] += q["sv"]
                gsv[q["id"]][1] += q["sa"]
            if g["goalies"].get(s):
                starters[g[s]] = g["goalies"][s][0]
    teams = sorted({r["off"] for r in rows} | {r["def"] for r in rows})
    ix = {t: i for i, t in enumerate(teams)}
    nT = len(teams)
    out = {"teams": {t: {"games": sum(1 for r in rows if r["off"] == t)} for t in teams}, "league": {}, "n_games": len(G)}
    out["lam"] = {}
    for k in ("shots", "fin", "ppo", "ppc"):
        lam_games = eb_lambda(rows, k)
        out["lam"][k] = lam_games
        X = np.zeros((len(rows), 2 + 2 * nT))
        y = np.array([r[k] for r in rows])
        w = np.array([r["w"][k] for r in rows], float)
        for j, r in enumerate(rows):
            X[j, 0], X[j, 1] = 1, r["home"]
            X[j, 2 + ix[r["off"]]] = 1
            X[j, 2 + nT + ix[r["def"]]] = 1
        pen = np.r_[0, 0, np.full(2 * nT, lam_games * (w.mean() if len(w) else 1.0))]
        beta = np.linalg.solve(X.T @ (X * w[:, None]) + np.diag(pen) + 1e-9 * np.eye(X.shape[1]), X.T @ (w * y))
        out["league"][k], out["league"]["home_" + k] = float(beta[0]), float(beta[1])
        for t in teams:
            out["teams"][t]["off_" + k], out["teams"][t]["def_" + k] = float(beta[2 + ix[t]]), float(beta[2 + nT + ix[t]])
    lg_sv = sum(v[0] for v in gsv.values()) / max(sum(v[1] for v in gsv.values()), 1)
    out["goalies"] = {gid: {"sv": (v[0] + GOALIE_K * lg_sv) / (v[1] + GOALIE_K), "shots": v[1]} for gid, v in gsv.items()}
    out["league"]["sv"] = lg_sv
    out["starters"] = starters
    tot_shg = sum(g["box"][s]["shg"] for g in G for s in ("home", "away"))
    tot_ppo = sum(g["box"][s]["ppo"] for g in G for s in ("home", "away"))
    out["league"]["shg_per_pp"] = tot_shg / max(tot_ppo, 1)
    ot = [g for g in G if g["periods"] >= 4]
    ot_goals = sum(1 for g in ot if g["periods"] == 4 and g["score"]["home"] != g["score"]["away"] and g["box"]["home"]["so"] + g["box"]["away"]["so"] == 0)
    out["league"]["ot_decided"] = ot_goals / max(len(ot), 1)
    so = [g for g in ot if g["box"]["home"]["so"] + g["box"]["away"]["so"] > 0]
    out["league"]["so_home"] = sum(g["score"]["home"] > g["score"]["away"] for g in so) / max(len(so), 1) if so else 0.5
    # finishing wobble per team-game beyond binomial noise (relative sd), for the per-game shock
    by = defaultdict(list)
    for r in rows:
        by[r["off"]].append(r)
    res, noi = [], []
    for v in by.values():
        if len(v) >= 3:
            m = np.mean([x["fin"] for x in v])
            res += [(x["fin"] - m) ** 2 * len(v) / (len(v) - 1) for x in v]
            noi += [m * (1 - m) / max(x["w"]["fin"], 1) for x in v]
    lgfin = out["league"]["fin"]
    out["sd_fin"] = float(np.sqrt(max(np.mean(res) - np.mean(noi), 0)) / lgfin) if res else 0.0
    hm = [g["score"]["home"] - g["score"]["away"] for g in G]
    out["home_margin"] = float(np.mean(hm)) if hm else 0.2
    gpg = [g["score"][s] for g in G for s in ("home", "away")]
    out["gpg"] = float(np.mean(gpg)) if gpg else 3.1
    out["total_sd_target"] = float(np.std([g["score"]["home"] + g["score"]["away"] for g in G])) if len(G) > 30 else None
    return out


def side(R: dict, team: str, opp: str, home: bool, goalie_id: str | None = None) -> dict:
    """Matchup rates for one team's attack against the other's defence and goalie (the opponent's goalie)."""
    L, T, O = R["league"], R["teams"].get(team, {}), R["teams"].get(opp, {})
    g = lambda k: L[k] + T.get("off_" + k, 0.0) + O.get("def_" + k, 0.0)       # home ice: one calibrated multiplier in simulate()
    gl = R["goalies"].get(goalie_id, {}).get("sv", L["sv"]) if goalie_id else L["sv"]
    sv_factor = (1 - gl) / (1 - L["sv"])
    return {"shots": max(g("shots"), 15.0), "fin": max(g("fin"), 0.02) * sv_factor, "ppo": max(g("ppo"), 0.5), "ppc": min(max(g("ppc"), 0.05), 0.45)}


def simulate(home: dict, away: dict, R: dict, en: dict, n: int = 50000, seed: int = 2026, env: bool = True, trace: int = 0,
             home_ice: bool = True) -> dict:
    rng = np.random.default_rng(seed)
    S = (home, away)
    ticks_per_60 = 3600 / TICK
    ev_rate = np.array([s["shots"] * 0.88 * s["fin"] for s in S]) / ticks_per_60 * R.get("goal_scale", 1.0)   # EV goals per tick
    if home_ice:
        ev_rate[0] *= R.get("home_mult", 1.0)
    pen_rate = np.array([S[1]["ppo"], S[0]["ppo"]]) / ticks_per_60          # penalties taken by each team per tick
    ppc = np.array([s["ppc"] for s in S])
    pp_hazard = -np.log(1 - ppc) / 12                                        # a 2-minute power play = 12 ticks
    shg = R["league"]["shg_per_pp"] / 12
    shock = np.exp(rng.normal(0, R.get("sd_fin", 0.0), (n, 2))) if env else np.ones((n, 2))
    score = np.zeros((n, 2), dtype=np.int64)
    pp_left = np.zeros((n, 2), dtype=np.int64)          # ticks of power play left for team i
    so_flag = np.zeros(n, dtype=bool)
    log = [[] for _ in range(trace)]
    T = int(3600 / TICK)
    for k in range(T):
        left = (T - k) * TICK
        u = rng.random((n, 6))
        # penalties at even strength start a power play for the other team
        evs = (pp_left[:, 0] == 0) & (pp_left[:, 1] == 0)
        p_on_home = evs & (u[:, 0] < pen_rate[0])
        p_on_away = evs & ~p_on_home & (u[:, 1] < pen_rate[1])
        pp_left[p_on_home, 1] = 12
        pp_left[p_on_away, 0] = 12
        diff = score[:, 0] - score[:, 1]
        pull_home = (diff == -1) & (left <= 120) | (diff == -2) & (left <= 180)
        pull_away = (diff == 1) & (left <= 120) | (diff == 2) & (left <= 180)
        en_for, en_ag = en["for_per_min"] * TICK / 60, en["against_per_min"] * TICK / 60
        for i in (0, 1):
            j = 1 - i
            on_pp, on_pk = pp_left[:, i] > 0, pp_left[:, j] > 0
            pulled_i = pull_home if i == 0 else pull_away
            pulled_j = pull_away if i == 0 else pull_home
            h = np.where(on_pp, pp_hazard[i], np.where(on_pk, shg, ev_rate[i] * shock[:, i]))
            h = np.where(pulled_i, np.maximum(h, en_for), h)
            h = np.where(pulled_j, en_ag, h)
            goal = u[:, 2 + i] < h
            score[goal, i] += 1
            ended = goal & on_pp
            pp_left[ended, i] = 0
            if trace:
                for g in np.flatnonzero(goal[:trace]):
                    log[g].append({"t": (k + 1) * TICK, "team": i, "pp": bool(on_pp[g]), "en": bool(pulled_j[g]), "score": (int(score[g, 0]), int(score[g, 1]))})
        pp_left = np.maximum(pp_left - 1, 0)
    # overtime (3-on-3) and shootout
    tied = score[:, 0] == score[:, 1]
    otg = tied & (rng.random(n) < R["league"].get("ot_decided", 0.6))
    p_home_ot = ev_rate[0] * shock[:, 0] / (ev_rate[0] * shock[:, 0] + ev_rate[1] * shock[:, 1])
    hw = rng.random(n) < p_home_ot
    score[otg & hw, 0] += 1
    score[otg & ~hw, 1] += 1
    so_ = tied & ~otg
    hs = rng.random(n) < R["league"].get("so_home", 0.5)
    score[so_ & hs, 0] += 1
    score[so_ & ~hs, 1] += 1
    so_flag[so_] = True
    return {"home": score[:, 0], "away": score[:, 1], "ot": tied, "shootout": so_flag, "trace": log,
            "stats": {"iterations": T, "ticks": T * n}}


def calibrate(R: dict, en: dict, n: int = 20000) -> dict:
    """League goal scale (a league-average game reproduces this season's goals per game) and the home multiplier
    on even-strength scoring (reproduces last full season's home goal margin)."""
    R["goal_scale"], R["home_mult"] = 1.0, 1.0
    prior = prior_home_margin()
    R["home_target"], R["home_prior"] = prior["margin"], prior
    avg = side(R, "_", "_", False)
    for _ in range(3):
        s = simulate(avg, dict(avg), R, en, n=n, seed=1, env=False, home_ice=False)
        R["goal_scale"] *= R["gpg"] / max(float((s["home"].mean() + s["away"].mean()) / 2), 0.5)
    # home edge as the difference from a no-home-ice run on the same random numbers: the target (~0.13 goals) is
    # only ~7 standard errors of one 20,000-game run, so fitting the raw margin put that run's noise into the edge
    s0 = simulate(avg, dict(avg), R, en, n=n, seed=2, env=False, home_ice=False)
    m0 = float((s0["home"] - s0["away"]).mean())
    lo, hi = 0.9, 1.4
    for _ in range(8):
        R["home_mult"] = (lo + hi) / 2
        s = simulate(avg, dict(avg), R, en, n=n, seed=2, env=False)
        if float((s["home"] - s["away"]).mean()) - m0 < R["home_target"]:
            lo = R["home_mult"]
        else:
            hi = R["home_mult"]
    R["home_mult"] = (lo + hi) / 2
    # goal scale again with home ice on, so the home edge doesn't add to the total
    for _ in range(2):
        s = simulate(avg, dict(avg), R, en, n=n, seed=1, env=False)
        R["goal_scale"] *= R["gpg"] / max(float((s["home"].mean() + s["away"].mean()) / 2), 0.5)
    # finishing-shock size: match the observed spread of total goals (the raw residual estimate also carries goalie noise)
    if R.get("total_sd_target"):
        raw = R["sd_fin"]
        lo, hi = 0.0, max(raw, 0.05)
        for _ in range(6):
            R["sd_fin"] = (lo + hi) / 2
            s = simulate(avg, dict(avg), R, en, n=n, seed=3)
            if float((s["home"] + s["away"]).std()) < R["total_sd_target"]:
                lo = R["sd_fin"]
            else:
                hi = R["sd_fin"]
        R["sd_fin"] = (lo + hi) / 2
        R["sd_fin_raw"] = raw
    return R


def backtest(games: list[dict], en: dict, min_games: int = 4, n: int = 6000, seed: int = 3) -> dict:
    from .backtest import metrics, no_vig
    recs = []
    by_day = defaultdict(list)
    for g in games:
        if g["final"] and len(g["box"]) == 2 and g["line"]["ml_home"] is not None:
            by_day[data.us_day(g["date"])].append(g)          # US day: no same-evening games leak in
    for day in sorted(by_day):
        cut = data.cutoff(day)
        R = ratings(games, cut)
        if R["n_games"] < 30:
            continue
        R = calibrate(R, en, n=6000)
        for g in by_day[day]:
            if min(R["teams"].get(g["home"], {}).get("games", 0), R["teams"].get(g["away"], {}).get("games", 0)) < min_games:
                continue
            gh = g["goalies"].get("home", [{}])[0].get("id") if g["goalies"].get("home") else None     # the actual starter (known at puck drop)
            ga = g["goalies"].get("away", [{}])[0].get("id") if g["goalies"].get("away") else None
            sim = simulate(side(R, g["home"], g["away"], True, ga), side(R, g["away"], g["home"], False, gh), R, en, n=n, seed=seed + len(recs))
            h, a = sim["home"], sim["away"]
            ln = g["line"]
            res = g["score"]["home"] - g["score"]["away"]
            tot = g["score"]["home"] + g["score"]["away"]
            tl = ln["total"]
            recs.append({"game": g["id"], "week": day, "p_home": float((h > a).mean()), "mk_home": no_vig(ln["ml_home"], ln["ml_away"]),
                         "won": float(res > 0), "p_cover": None, "mk_cover": None, "covered": None,
                         "p_over": None if tl is None else float((h + a > tl).mean() / max(1 - (h + a == tl).mean(), 1e-9)),
                         "mk_over": no_vig(ln["over_odds"], ln["under_odds"]), "overed": None if tl is None or tot == tl else float(tot > tl)})
    return {"records": recs, "metrics": metrics(recs)}
