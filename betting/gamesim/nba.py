"""NBA possession-by-possession engine (also used for college basketball with its own data and clock).

Data (named source): ESPN game summaries - team box scores (shots, threes, free throws, rebounds, turnovers),
and the DraftKings closing lines kept in each summary for the backtest.

Ratings, from this season's earlier games only (opponent-adjusted ridge on game-level rates, home term):
  turnover rate per possession, three-point share of shots, 2P% and 3P%, free-throw trips per shot, FT%,
  offensive rebound rate, pace (possessions per 48).
One simulated game:
  - environment: a pace shock shared by both teams and a shooting-luck shock per team (2P/3P logit),
    both sized from real game-to-game variation beyond binomial noise;
  - each possession: turnover, or a shot (3 or 2) or a foul trip (two free throws); a miss can be rebounded
    by the offense and the possession continues; clock off the possession comes from the team's pace;
  - endgame: inside the last minute the trailing team fouls on defence when down 3-8 (the leader shoots two),
    a team down 3 takes a three, a leader with the ball inside 24 seconds runs the clock; 5-minute overtimes.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from collections import defaultdict

import numpy as np

from . import data

SPORT = {"nba": ("basketball/nba", 48, 4, 24), "ncaab": ("basketball/mens-college-basketball", 40, 2, 30)}
SB_QUERY = {"nba": "", "ncaab": "&groups=50&limit=400"}       # college: all of Division I
LAM = 4.0     # games of league-average prior on every team rate


def _cache(lg):
    p = os.path.join(data.CACHE, lg)
    os.makedirs(p, exist_ok=True)
    return p


def _split(v):
    a, b = (str(v).split("-") + ["0"])[:2]
    return float(a or 0), float(b or 0)


def parse(s: dict) -> dict | None:
    comp = s["header"]["competitions"][0]
    if comp["status"]["type"]["name"] != "STATUS_FINAL" and comp["status"]["type"]["name"] != "STATUS_SCHEDULED":
        return None
    t = {x["homeAway"]: x for x in comp["competitors"]}
    g = {"id": s["header"]["id"], "date": comp["date"], "final": comp["status"]["type"]["name"] == "STATUS_FINAL",
         "home": t["home"]["team"]["abbreviation"], "away": t["away"]["team"]["abbreviation"],
         "score": {"home": data.f(t["home"].get("score"), 0), "away": data.f(t["away"].get("score"), 0)},
         "periods": len(t["home"].get("linescores", []) or []), "box": {}, "neutral": comp.get("neutralSite", False)}
    side = {x["team"]["abbreviation"]: ("home" if x["team"]["abbreviation"] == g["home"] else "away") for x in s.get("boxscore", {}).get("teams", [])}
    for x in s.get("boxscore", {}).get("teams", []):
        st = {k["name"]: k["displayValue"] for k in x.get("statistics", [])}
        if "fieldGoalsMade-fieldGoalsAttempted" not in st:
            continue
        fgm, fga = _split(st["fieldGoalsMade-fieldGoalsAttempted"])
        tpm, tpa = _split(st["threePointFieldGoalsMade-threePointFieldGoalsAttempted"])
        ftm, fta = _split(st["freeThrowsMade-freeThrowsAttempted"])
        g["box"][side[x["team"]["abbreviation"]]] = {"fgm": fgm, "fga": fga, "tpm": tpm, "tpa": tpa, "ftm": ftm, "fta": fta,
                                                     "orb": data.f(st.get("offensiveRebounds"), 0), "drb": data.f(st.get("defensiveRebounds"), 0),
                                                     "tov": data.f(st.get("totalTurnovers") or st.get("turnovers"), 0)}
    pc = (s.get("pickcenter") or [{}])[0]
    h, a = pc.get("homeTeamOdds") or {}, pc.get("awayTeamOdds") or {}
    sp = pc.get("spread")
    if sp is not None and (h.get("favorite") is True and sp > 0 or h.get("favorite") is False and sp < 0):
        sp = -sp
    num = lambda x: data.f(str(x).replace("+", ""), None) if x not in (None, "") else None
    opn = lambda grp, sd, k: num(((((pc.get(grp) or {}).get(sd) or {}).get("open") or {}).get(k) or "").replace("o", "").replace("u", "") or None)
    g["line"] = {"ml_home_open": opn("moneyline", "home", "odds"), "ml_away_open": opn("moneyline", "away", "odds"),
                 "spread_home_open": opn("pointSpread", "home", "line"), "total_open": opn("total", "over", "line"),
                 "spread_home": sp, "total": pc.get("overUnder"), "ml_home": num(h.get("moneyLine")), "ml_away": num(a.get("moneyLine")),
                 "spread_home_odds": num(h.get("spreadOdds")), "spread_away_odds": num(a.get("spreadOdds")),
                 "over_odds": num(pc.get("overOdds")), "under_odds": num(pc.get("underOdds")), "provider": (pc.get("provider") or {}).get("name")}
    return g


def season_games(lg: str, start: str, end: str) -> list[dict]:
    """Regular-season games between two dates (YYYYMMDD), finished ones cached for good."""
    path, *_ = SPORT[lg]
    d0, d1 = dt.datetime.strptime(start, "%Y%m%d"), dt.datetime.strptime(end, "%Y%m%d")
    ids = []
    day = d0
    while day <= d1:
        try:
            sb = data._json(f"https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard?dates={day:%Y%m%d}{SB_QUERY[lg]}",
                            f"{lg}_sb_{day:%Y%m%d}.json", None if day.date() < dt.date.today() - dt.timedelta(days=1) else 1800)
            for e in sb.get("events", []):
                if (e.get("season") or {}).get("type") in (2, None):
                    ids.append(e["id"])
        except RuntimeError:
            pass
        day += dt.timedelta(days=1)
    out = []
    for gid in ids:
        p = os.path.join(_cache(lg), f"{gid}.json")
        g = None
        if os.path.exists(p):
            with open(p) as f:
                g = json.load(f)
        if g is None or not g.get("final"):
            try:
                g = parse(data._json(f"https://site.api.espn.com/apis/site/v2/sports/{path}/summary?event={gid}", f"{lg}_sum_{gid}.json", 900))
            except (RuntimeError, KeyError):
                g = None
            if g and g["final"]:
                with open(p, "w") as f:
                    json.dump(g, f)
        if g:
            out.append(g)
    return sorted(out, key=lambda g: g["date"])


# ------------------------------------------------------------------ ratings
def poss(b, ob):
    return b["fga"] - b["orb"] + b["tov"] + 0.44 * b["fta"]


def ratings(games: list[dict], before: str, minutes: int) -> dict:
    """Opponent-adjusted team rates from games strictly before `before` (ISO date)."""
    G = [g for g in games if g["final"] and g["date"] < before and len(g["box"]) == 2]
    rows = []
    for g in G:
        for s, o in (("home", "away"), ("away", "home")):
            b, ob = g["box"][s], g["box"][o]
            p = poss(b, ob)
            mins = minutes + 5 * max(0, g["periods"] - (4 if minutes == 48 else 2))
            rows.append({"off": g[s], "def": g[o], "home": float(s == "home" and not g["neutral"]),
                         "to": b["tov"] / max(p, 1), "three": b["tpa"] / max(b["fga"], 1),
                         "p2": (b["fgm"] - b["tpm"]) / max(b["fga"] - b["tpa"], 1), "p3": b["tpm"] / max(b["tpa"], 1),
                         "ft_rate": (b["fta"] / 2.0) / max(b["fga"] + b["fta"] / 2.0, 1), "ftp": b["ftm"] / max(b["fta"], 1),
                         "orb": b["orb"] / max(b["orb"] + ob["drb"], 1), "pace": p * minutes / mins,
                         "w": {"to": p, "three": b["fga"], "p2": b["fga"] - b["tpa"], "p3": b["tpa"], "ft_rate": b["fga"], "ftp": b["fta"],
                               "orb": b["orb"] + ob["drb"], "pace": 1.0}})
    teams = sorted({r["off"] for r in rows} | {r["def"] for r in rows})
    ix = {t: i for i, t in enumerate(teams)}
    nT = len(teams)
    out = {"teams": {t: {} for t in teams}, "league": {}, "n_games": len(G)}
    for k in ("to", "three", "p2", "p3", "ft_rate", "ftp", "orb", "pace"):
        if not rows:
            break
        X = np.zeros((len(rows), 2 + 2 * nT))
        y = np.array([r[k] for r in rows])
        w = np.array([r["w"][k] for r in rows], float)
        for j, r in enumerate(rows):
            X[j, 0] = 1
            X[j, 1] = r["home"]
            X[j, 2 + ix[r["off"]]] = 1
            if k not in ("ftp",):
                X[j, 2 + nT + ix[r["def"]]] = 1
        wbar = w.mean()
        pen = np.r_[0, 0, np.full(2 * nT, LAM * wbar)]
        A = X.T @ (X * w[:, None]) + np.diag(pen) + 1e-9 * np.eye(X.shape[1])
        beta = np.linalg.solve(A, X.T @ (w * y))
        out["league"][k] = float(beta[0])
        out["league"]["home_" + k] = float(beta[1])
        for t in teams:
            out["teams"][t]["off_" + k] = float(beta[2 + ix[t]])
            out["teams"][t]["def_" + k] = float(beta[2 + nT + ix[t]])
            out["teams"][t]["games"] = sum(1 for r in rows if r["off"] == t)
    # game-to-game wobble beyond binomial noise: shooting (2P/3P) and pace
    def wobble(key, n_key):
        res, noi = [], []
        by = defaultdict(list)
        for r in rows:
            by[r["off"]].append(r)
        for v in by.values():
            if len(v) < 3:
                continue
            m = np.mean([x[key] for x in v])
            for x in v:
                res.append((x[key] - m) ** 2 * len(v) / (len(v) - 1))
                noi.append(m * (1 - m) / max(x["w"][n_key], 1) if n_key else 0.0)
        return float(np.sqrt(max(np.mean(res) - np.mean(noi), 0))) if res else 0.0
    out["sd_p2"], out["sd_p3"] = wobble("p2", "p2"), wobble("p3", "p3")
    out["sd_pace"] = wobble("pace", None)
    hm = [g["score"]["home"] - g["score"]["away"] for g in G if not g["neutral"]]
    out["home_margin"] = float(np.mean(hm)) if hm else 2.5
    return out


def side(R: dict, team: str, opp: str, home: bool, use_home: bool = True) -> dict:
    """Matchup rates for one offense against one defense (league + offense + defense effects, + home)."""
    L, T, O = R["league"], R["teams"].get(team, {}), R["teams"].get(opp, {})
    hs = R.get("home_scale", 1.0)
    g = lambda k: L[k] + T.get("off_" + k, 0.0) + O.get("def_" + k, 0.0) + (hs * L.get("home_" + k, 0.0) if home and use_home else 0.0)
    clip = lambda x, a, b: float(min(max(x, a), b))
    return {"to": clip(g("to"), 0.05, 0.25), "three": clip(g("three"), 0.2, 0.6), "p2": clip(g("p2"), 0.4, 0.65),
            "p3": clip(g("p3"), 0.25, 0.45), "ft_rate": clip(g("ft_rate"), 0.05, 0.25), "ftp": clip(L["ftp"] + T.get("off_ftp", 0.0), 0.6, 0.9),
            "orb": clip(g("orb"), 0.15, 0.4), "pace_off": T.get("off_pace", 0.0) + O.get("def_pace", 0.0)}


# ------------------------------------------------------------------ simulation
def simulate(home: dict, away: dict, R: dict, minutes: int = 48, n: int = 50000, seed: int = 2026, env: bool = True,
             shot_clock: int = 24, trace: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    S = (home, away)
    lo = lambda p: np.log(p / (1 - p))
    sg = lambda z: 1 / (1 + np.exp(-z))
    pace = R["league"]["pace"] + (home["pace_off"] + away["pace_off"]) / 2
    pace_g = pace * (np.exp(rng.normal(0, R["sd_pace"] / max(pace, 1), n)) if env else np.ones(n))
    sec_per_poss = (minutes * 60) / (2 * pace_g) * R.get("dur_scale", 1.0)   # both teams' possessions share the clock
    and1 = R.get("and1", 0.0)
    sh2 = rng.normal(0, R["sd_p2"], (n, 2)) if env else np.zeros((n, 2))
    sh3 = rng.normal(0, R["sd_p3"], (n, 2)) if env else np.zeros((n, 2))
    arr = lambda k: np.array([s[k] for s in S])
    p_to, p_3, p_2, p_3m, p_ft, ftp, p_orb = arr("to"), arr("three"), arr("p2"), arr("p3"), arr("ft_rate"), arr("ftp"), arr("orb")
    L2 = lo(p_2)[None, :] + sh2 / (p_2 * (1 - p_2))[None, :]       # shocks are in probability units: move logits to match
    L3 = lo(p_3m)[None, :] + sh3 / (p_3m * (1 - p_3m))[None, :]
    score = np.zeros((n, 2), dtype=np.int64)
    clock = np.full(n, minutes * 60.0)
    poss_t = (rng.random(n) < 0.5).astype(np.int64)                 # jump ball
    # score effects: a team ahead of its expected path eases off and one behind pushes, as a logit shift on make rates
    # proportional to how far the game is from the expected margin at that point (the mean margin is unchanged)
    kappa = R.get("comeback", 0.0)
    mu = pace * (ppp_expected(home, and1) - ppp_expected(away, and1)) if kappa else 0.0
    done = np.zeros(n, dtype=bool)
    ot = np.zeros(n, dtype=np.int64)
    nposs = np.zeros(n, dtype=np.int64)
    log = [[] for _ in range(trace)]
    stats = {"iterations": 0, "possessions": 0}
    for _ in range(2000):
        a = np.flatnonzero(~done)
        if a.size == 0:
            break
        stats["iterations"] += 1
        stats["possessions"] += a.size
        o, d = poss_t[a], 1 - poss_t[a]
        c = clock[a]
        diff = score[a, o] - score[a, d]
        k = a.size
        u = rng.random((k, 6))
        late = c <= 60
        # endgame choices
        # the defence trails: it fouls at once when down 3-8 in the last minute, and when down 1-2 once the shot clock
        # is off (otherwise the leader would run out the clock untouched)
        foul = late & (c > 2) & (((diff >= 3) & (diff <= 8)) | ((diff >= 1) & (diff <= 2) & (c <= shot_clock)))
        hold = (c <= shot_clock) & (diff > 0) & ~foul                           # leader runs out the clock
        need3 = late & (diff == -3)
        dur = np.where(foul, rng.uniform(2, 6, k), np.where(hold, c, rng.gamma(4.0, 1.0, k) * sec_per_poss[a] / 4.0))
        pts = np.zeros(k, dtype=np.int64)
        # a fouled leader shoots two
        fl = foul
        pts += np.where(fl, (u[:, 0] < ftp[o]).astype(int) + (u[:, 1] < ftp[o]).astype(int), 0)
        live = ~fl & ~hold
        to = live & (u[:, 2] < p_to[o])
        shoot = live & ~to
        trip = shoot & ~need3 & (u[:, 3] < p_ft[o])
        pts += np.where(trip, (rng.random(k) < ftp[o]).astype(int) + (rng.random(k) < ftp[o]).astype(int), 0)
        fga = shoot & ~trip
        # shots with offensive rebounds continuing the possession (up to three attempts)
        if kappa:
            el = np.minimum(minutes * 60.0 - c, minutes * 60.0) / (minutes * 60.0)
            dev = (score[a, 0] - score[a, 1]) - mu * np.where(ot[a] > 0, 1.0, el)
            cb = -kappa * np.where(o == 0, dev, -dev) / 10.0
        else:
            cb = 0.0
        pending = fga.copy()
        extra_t = np.zeros(k)
        for attempt in range(3):
            if not pending.any():
                break
            is3 = pending & (need3 | (rng.random(k) < p_3[o]))
            made = pending & (rng.random(k) < np.where(is3, sg(L3[a, o] + cb), sg(L2[a, o] + cb)))
            pts += np.where(made, np.where(is3, 3, 2), 0)
            pts += (made & (rng.random(k) < and1) & (rng.random(k) < ftp[o])).astype(int)     # and-one
            miss = pending & ~made
            orb = miss & (rng.random(k) < p_orb[o])
            extra_t += np.where(orb, 5.0, 0.0)
            pending = orb
        dur = np.minimum(dur + extra_t, c)
        score[a, o] += pts
        clock[a] = c - dur
        nposs[a] += 1
        if trace:
            for j in np.flatnonzero(a < trace):
                log[int(a[j])].append({"clock": float(c[j]), "off": int(o[j]), "pts": int(pts[j]), "foul": bool(fl[j]), "to": bool(to[j]),
                                       "hold": bool(hold[j]), "score": (int(score[a[j], 0]), int(score[a[j], 1]))})
        poss_t[a] = d
        end = clock[a] <= 0
        e = a[end]
        tied = score[e, 0] == score[e, 1]
        done[e[~tied]] = True
        t = e[tied]
        clock[t] = 300.0
        ot[t] += 1
        poss_t[t] = (rng.random(t.size) < 0.5).astype(np.int64)
        done[t[ot[t] > 8]] = True
    return {"home": score[:, 0], "away": score[:, 1], "ot": ot > 0, "possessions": nposs, "trace": log, "stats": stats}


# Score effects: target margin SD for two average teams (None = off: independent possessions). Without them two
# average teams had a 16.8-point margin SD against ~14 in real games (the residual vs the closing spread), which made
# every winner probability too timid. Fair test (2025-26 Feb-Apr, 501 held-out games, with player ratings on): winner
# Brier 0.1780 -> 0.1727 (CI -0.0069 to -0.0037), spreads slightly worse (0.2548 -> 0.2563), totals unchanged.
COMEBACK_SD = 14.0


def pace_resid_sd(G: list[dict], before: str, minutes: int, folds: int = 5) -> float | None:
    """Out-of-fold SD of game pace (possessions per team per 48) around the team pace ratings: each fold's games are
    predicted from ratings fitted on the other folds, so the residual holds game-to-game variation plus the rating
    error a forecast actually faces, not in-sample fit."""
    if len(G) < 40:
        return None
    res = []
    for k in range(folds):
        test = G[k::folds]
        ids = {g["id"] for g in test}
        Rk = ratings([g for g in G if g["id"] not in ids], before, minutes)
        T, L = Rk["teams"], Rk["league"]["pace"]
        for g in test:
            if g["home"] not in T or g["away"] not in T:
                continue
            h, a = T[g["home"]], T[g["away"]]
            fit = L + (h.get("off_pace", 0) + a.get("def_pace", 0) + a.get("off_pace", 0) + h.get("def_pace", 0)) / 2
            mins = minutes + 5 * max(0, g["periods"] - (4 if minutes == 48 else 2))
            obs = (poss(g["box"]["home"], g["box"]["away"]) + poss(g["box"]["away"], g["box"]["home"])) / 2 * minutes / mins
            res.append(obs - fit)
    return float(np.std(res)) if len(res) > 20 else None


def calibrate(R: dict, games: list[dict], before: str, minutes: int, shot_clock: int, n: int = 12000) -> dict:
    """Fit three league constants so a league-average game reproduces this season's games before `before`:
    possession length (sim possessions = box-score pace), and-one rate (points per game) and home edge
    (observed home margin). Stored in R and used by simulate()."""
    G = [g for g in games if g["final"] and g["date"] < before and len(g["box"]) == 2]
    ppg = float(np.mean([g["score"][s] for g in G for s in ("home", "away")])) if G else 110.0
    avg = side(R, "_", "_", False)
    R["dur_scale"], R["and1"], R["home_scale"] = 1.0, 0.0, 1.0
    for _ in range(3):                     # possession length: simulated possessions per team = box-score pace
        s0 = simulate(avg, dict(avg), R, minutes, n=n, seed=1, shot_clock=shot_clock)
        R["dur_scale"] *= float(s0["possessions"].mean() / 2) / R["league"]["pace"]
    # pace shock: only the game-to-game pace variation the possession process doesn't already produce. The raw
    # per-team pace SD (ratings()) also holds team differences and the engine's own possession-count noise, so using
    # it as the shock double-counted (total-points SD 22.1 vs 18.5-18.9 real). Target: out-of-fold residual of game
    # pace around the team pace ratings, minus the engine's intrinsic possession SD.
    s_i = simulate(avg, dict(avg), {**R, "sd_pace": 0.0}, minutes, n=n, seed=3, shot_clock=shot_clock)
    intr = float((s_i["possessions"][~s_i["ot"]] / 2).std())
    obs = pace_resid_sd(G, before, minutes)
    R["sd_pace_raw"], R["sd_pace_target"], R["sd_pace_intrinsic"] = R["sd_pace"], obs, intr
    R["sd_pace"] = float(np.sqrt(max(obs ** 2 - intr ** 2, 0.0))) if obs else R["sd_pace"]
    # score effects: pull strength so two average teams' margin spread matches real games around the closing spread
    # (residual SD 14.1 in 2025-26 and 2026-27; the market's own error is part of that, so 14.0)
    R["comeback"] = 0.0
    if COMEBACK_SD:
        clo, chi = 0.0, 0.12
        for _ in range(7):
            R["comeback"] = (clo + chi) / 2
            sc = simulate(avg, dict(avg), R, minutes, n=n, seed=4, shot_clock=shot_clock)
            if float((sc["home"] - sc["away"]).std()) > COMEBACK_SD:
                clo = R["comeback"]
            else:
                chi = R["comeback"]
        R["comeback"] = (clo + chi) / 2
    lo, hi = 0.0, 0.4                       # extra free throws per made shot (and-ones, technicals, 3-shot fouls)
    for _ in range(9):
        R["and1"] = (lo + hi) / 2
        s1 = simulate(avg, dict(avg), R, minutes, n=n, seed=1, shot_clock=shot_clock)
        if float((s1["home"].mean() + s1["away"].mean()) / 2) < ppg:
            lo = R["and1"]
        else:
            hi = R["and1"]
    R["and1"] = (lo + hi) / 2
    target = R["home_margin"]
    # home edge as the difference from a no-home run on the same random numbers: one seeded run's own margin noise
    # (SE ~0.2 points) otherwise lands in the fitted home scale
    s0 = simulate(avg, dict(avg), R, minutes, n=n, seed=2, shot_clock=shot_clock)
    m0 = float((s0["home"] - s0["away"]).mean())
    lo, hi = 0.0, 4.0
    for _ in range(7):
        R["home_scale"] = (lo + hi) / 2
        sh = simulate(side(R, "_", "_", True), side(R, "_", "_", False), R, minutes, n=n, seed=2, shot_clock=shot_clock)
        if float((sh["home"] - sh["away"]).mean()) - m0 < target:
            lo = R["home_scale"]
        else:
            hi = R["home_scale"]
    R["home_scale"] = (lo + hi) / 2
    # scoring level on the configuration games are actually played in (a home side): the home edge was added on top
    # of an away-style baseline, which put it into the total too (+2 points)
    hs = side(R, "_", "_", True)
    lo, hi = max(R["and1"] - 0.1, 0.0), R["and1"] + 0.05
    for _ in range(8):
        R["and1"] = (lo + hi) / 2
        s1 = simulate(hs, dict(avg), R, minutes, n=n, seed=1, shot_clock=shot_clock)
        if float((s1["home"].mean() + s1["away"].mean()) / 2) < ppg:
            lo = R["and1"]
        else:
            hi = R["and1"]
    R["and1"] = (lo + hi) / 2
    R["ppg_target"] = ppg
    return R


def sides_with_availability(R: dict, games: list[dict], g: dict, cut: str, absent: dict, lg: str = "nba") -> tuple:
    """Home and away sides with each offense moved by INJURY_BETA x the value it is missing tonight (absent: {side:
    set of player ids out tonight}). Returns (home side, away side, detail)."""
    h, a = side(R, g["home"], g["away"], not g.get("neutral", False)), side(R, g["away"], g["home"], False)
    det = {}
    for s_ in ("home", "away"):
        det[s_] = availability_shift(player_values(lg, games, g[s_], cut), absent.get(s_, set()))
        det[s_]["points"] = -INJURY_BETA * det[s_]["lost"]
    return shift_offense(h, R, det["home"]["points"]), shift_offense(a, R, det["away"]["points"]), det


def absent_from_box(lg: str, games: list[dict], g: dict, cut: str) -> dict:
    """Backtest availability: players in the rating sample who did not play in this game (injury report plus late
    scratches; known at tip-off, mostly earlier)."""
    box = _box_cached(lg, g["id"])
    out = {}
    for s_ in ("home", "away"):
        played = {r["id"] for r in box.get(g[s_], []) if not r["dnp"] and r["min"] > 0}
        out[s_] = {pid for pid in player_values(lg, games, g[s_], cut)["players"] if pid not in played}
    return out


def backtest(games: list[dict], minutes: int, shot_clock: int, min_games: int = 3, n: int = 6000, seed: int = 3,
             availability: bool = True) -> dict:
    from .backtest import metrics, no_vig
    recs = []
    by_day = defaultdict(list)
    for g in games:
        if g["final"] and len(g["box"]) == 2 and g["line"]["ml_home"] is not None:
            by_day[data.us_day(g["date"])].append(g)          # US day: no same-evening games leak in
    PR = None
    if availability and minutes == 48 and PLAYER_RATING_W and by_day:
        PR = PlayerRatings("nba", games, season_of(min(by_day)))
    for day in sorted(by_day):
        cut = data.cutoff(day)
        prf = PR.fit(cut) if PR else None
        R = ratings(games, cut, minutes)
        if R["n_games"] < 20:
            continue
        R = calibrate(R, games, cut, minutes, shot_clock, n=6000)
        for g in by_day[day]:
            if min(R["teams"].get(g["home"], {}).get("games", 0), R["teams"].get(g["away"], {}).get("games", 0)) < min_games:
                continue
            ln = g["line"]
            if availability and minutes == 48:               # fitted on the NBA only
                H, A, det = sides_with_availability(R, games, g, cut, absent_from_box("nba" if minutes == 48 else "ncaab", games, g, cut),
                                                    "nba" if minutes == 48 else "ncaab")
                ctx = prior_context("nba", int(g["date"][:4]) if g["date"][5:7] >= "09" else int(g["date"][:4]) - 1) if PRIOR_K else None
                box = _box_cached("nba", g["id"])          # the active roster at tip-off
                H, A, _ = with_prior(H, A, R, ctx, g["home"], g["away"], {g[s_]: {r["id"] for r in box.get(g[s_], [])} for s_ in ("home", "away")})
                if PR and prf["n_games"] >= 100:
                    pm = PR.margin(prf, PR.lineup_played(g["id"], g["home"], cut), PR.lineup_played(g["id"], g["away"], cut), g["neutral"])
                    det["players"] = {"margin": pm["margin"], "model": expected_margin(H, A, R)}
                    H, A, det["players"]["shift"] = with_player_ratings(H, A, R, pm["margin"])
            else:
                H, A, det = side(R, g["home"], g["away"], not g["neutral"]), side(R, g["away"], g["home"], False), None
            sim = simulate(H, A, R, minutes, n=n, seed=seed + len(recs), shot_clock=shot_clock)
            h, a = sim["home"], sim["away"]
            res = g["score"]["home"] - g["score"]["away"]
            tot = g["score"]["home"] + g["score"]["away"]
            sp, tl = ln["spread_home"], ln["total"]
            recs.append({"game": g["id"], "week": day, "p_home": float((h > a).mean()), "mk_home": no_vig(ln["ml_home"], ln["ml_away"]),
                         "won": float(res > 0),
                         "p_cover": None if sp is None else float((h - a + sp > 0).mean() / max(1 - (h - a + sp == 0).mean(), 1e-9)),
                         "mk_cover": no_vig(ln["spread_home_odds"], ln["spread_away_odds"]),
                         "covered": None if sp is None or res + sp == 0 else float(res + sp > 0),
                         "p_over": None if tl is None else float((h + a > tl).mean()), "mk_over": no_vig(ln["over_odds"], ln["under_odds"]),
                         "overed": None if tl is None or tot == tl else float(tot > tl), "sim_total": float((h + a).mean()), "total": tot,
                         "sim_margin": float((h - a).mean()), "margin": res,
                         "avail_points": None if det is None else [det["home"]["points"], det["away"]["points"]],
                         "players_margin": None if not det or "players" not in det else det["players"]["margin"],
                         "model_margin": None if not det or "players" not in det else det["players"]["model"]})
    return {"records": recs, "metrics": metrics(recs)}


# ------------------------------------------------------------------ player layer
def _box_players(s: dict) -> dict:
    """{team abbr: [player rows]} from an ESPN summary (MIN, PTS, FG, 3PT, FT, REB, AST, TO, STL, BLK, OREB, DREB, ...)."""
    out = {}
    for t in (s.get("boxscore") or {}).get("players", []) or []:
        if not t.get("statistics"):
            continue
        st = t["statistics"][0]
        lab = st.get("labels") or []
        rows = []
        for a in st.get("athletes", []):
            if not (a.get("athlete") or {}).get("id"):
                continue                           # occasional placeholder rows without a player
            v = dict(zip(lab, a.get("stats") or []))
            fg, tp, ft = _split(v.get("FG", "0-0")), _split(v.get("3PT", "0-0")), _split(v.get("FT", "0-0"))
            rows.append({"id": a["athlete"]["id"], "name": a["athlete"]["displayName"], "pos": (a["athlete"].get("position") or {}).get("abbreviation", ""),
                         "starter": bool(a.get("starter")), "dnp": bool(a.get("didNotPlay")) or not v, "reason": a.get("reason") or "",
                         "min": data.f(v.get("MIN"), 0) or 0, "pts": data.f(v.get("PTS"), 0) or 0, "fgm": fg[0], "fga": fg[1], "tpm": tp[0], "tpa": tp[1],
                         "ftm": ft[0], "fta": ft[1], "oreb": data.f(v.get("OREB"), 0) or 0, "dreb": data.f(v.get("DREB"), 0) or 0,
                         "ast": data.f(v.get("AST"), 0) or 0, "tov": data.f(v.get("TO"), 0) or 0,
                         "stl": data.f(v.get("STL"), 0) or 0, "blk": data.f(v.get("BLK"), 0) or 0, "pf": data.f(v.get("PF"), 0) or 0})
        out[t["team"]["abbreviation"]] = rows
    return out


def reb_credit(games: list[dict], before: str) -> float:
    """Share of missed field goals that end as a player rebound in the box score (the rest are team rebounds and
    rebounds of missed free throws, which the possession engine doesn't produce separately)."""
    G = [g for g in games if g["final"] and g["date"] < before and len(g["box"]) == 2]
    miss = sum(g["box"][s]["fga"] - g["box"][s]["fgm"] for g in G for s in ("home", "away"))
    reb = sum(g["box"][s]["orb"] + g["box"][s]["drb"] for g in G for s in ("home", "away"))
    return float(min(1.0, reb / miss)) if miss else 0.93


# Player layer, fair-tested 2026-11-03: tuned on 2026-27 games before Nov 2, judged on the Nov 2 starters' DraftKings
# points lines. Projection MAE 5.31 -> 5.23, stars' gap to the line -2.4 -> -1.2, Brier 0.278 -> 0.275 (a coin flip
# is 0.250); over/under calls 71 -> 69 of 143, no better: the book's lean got 51 of 96 to the model's 40.
# Fair test on the Nov 2 starters (same lines, who sat known): starters' minutes off by 5.5 -> 4.8, points MAE
# 5.36 -> 5.11, Brier 0.273 -> 0.259 (book 0.249), over/under calls 66 -> 67 of 143.
# Garbage time (browser player layer): starters hand 70% of their role to the bench once a 4th-quarter lead reaches
# a + b x minutes left. Fitted 2026-11-03 on pre-Nov 2 games to real starters' minutes by final margin (2,566 team-games
# 2025-27): simulated -1.5/-2.5/-3.5/-4.6 minutes at 15-20/20-25/25-30/30+ points vs real -1.6/-2.7/-3.7/-4.6.
PLAYER_GARBAGE = {"a": 12.0, "b": 1.5, "g": 0.3}
# Market anchor for player props (when DraftKings has a line): final mean = line + w x (simulated mean - line), and the
# simulated distribution is shifted to it. w fitted 2026-11-03 on 2026-27 games before Nov 2 (624 / 579 / 444 player
# lines); on the held-out Nov 2 lines it cut the MAE from 5.01 to 4.72 (points), 2.00 to 1.81 (rebounds), 1.77 to 1.71
# (assists), and the Brier from 0.258 / 0.252 / 0.265 to 0.247 / 0.247 / 0.258.
PROP_ANCHOR = {"pts": 0.26, "reb": 0.24, "ast": 0.62}
PLAYER_RATE_DECAY = None      # per-game decay of the weight on older games in a player's rates (None: equal weights)
MINUTES_WHEN_PLAYING = True   # chance he plays x minutes when he plays (see player_profiles)
PLAYER_PRIOR_MIN = 100.0  # minutes of the player's own last-season per-minute rates in his prior (else team average)
PLAYER_SHOCK = 0.30       # per-player per-game role swing (log SD): ~20% of results outside the 10-90% range (was 29%); retuned after the minutes fix
SWING_RHO = 0.0           # share of the role swing common to shots, boards and assists (Fix 6; 0 = independent, under test)
AST_FIX = False           # assist weights corrected for "no assist to the shooter" (simlab worker nbAstFix; under test 2026-11-07)


def season_player_totals(lg: str, games: list[dict], before: str = "2099-01-01") -> dict:
    """Each player's season totals across all his teams: {pid: {min, fgm, fga, tpm, tpa, ftm, fta, ast, oreb, dreb, tov}}."""
    out = {}
    for g in games:
        if not (g["final"] and g["date"] < before):
            continue
        for rows in _box_cached(lg, g["id"]).values():
            for r in rows:
                if r["dnp"] or r["min"] <= 0:
                    continue
                o = out.setdefault(r["id"], defaultdict(float))
                for k in ("min", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "ast", "oreb", "dreb", "tov"):
                    o[k] += r[k]
    return out


# How the 240 minutes are shared when the rotation's projected minutes don't add up to 240: each player gets
# c x minutes^MINUTES_ALPHA (capped at 42), c set so the team sums to 240. 1.0 = everyone scaled by the same factor;
# above 1 the bench absorbs a surplus, below 1 the top of the rotation gives more back. Fair test on box scores
# (players who played, raw projection = chance x minutes when playing): with 1.0 the five biggest projections ran
# +2.1 to +2.6 minutes over what they played; 0.8 was best on 2025-26 Nov-Jan (MAE 4.80 -> 4.70) and held out on
# Feb-Apr (5.05 -> 4.89) and 2026-27 (4.71 -> 4.53). Bench-first (above 1) was worse everywhere.
MINUTES_ALPHA = 0.8
# Scale on each player's game-to-game minutes spread in the simulation (1.0 = his observed SD, floor 3). Parameter
# under test (Fix 1): the observed SD includes blowouts and in-game injuries the engine already produces.
MIN_SD_SCALE = 1.0


# How minutes freed by absences are shared (2026-11-07 fair test on box scores, tuned on 2025-26, scored on 2026-27):
# "alpha" scales everyone by minutes^MINUTES_ALPHA; "headroom" lets each player rise only toward his own ceiling (his
# high in his last 10 games + MINUTES_PAD), so stars already near their usual load barely move and the rotation
# players below theirs absorb the minutes. Starters' minutes MAE 5.13 -> 4.77 (2025-26) and 4.70 -> 4.38 (2026-27).
MINUTES_SHARE = "alpha"
MINUTES_PAD = 3.0


def allocate_headroom(raw: list[float], ceil: list[float], total: float = 240.0, cap: float = 42.0) -> list[float]:
    """Fill the gap to `total` in proportion to each player's room below his ceiling; a surplus (or everyone at his
    ceiling) falls back to allocate_minutes."""
    s = sum(raw)
    if s <= 0 or s >= total:
        return allocate_minutes(raw)
    c = [min(cap, max(m, x)) for m, x in zip(raw, ceil)]
    x, need = list(raw), total - s
    for _ in range(20):
        room = [max(ci - v, 0.0) for ci, v in zip(c, x)]
        R = sum(room)
        if need <= 1e-6 or R <= 0:
            break
        x = [min(ci, v + need * r / R) for ci, v, r in zip(c, x, room)]
        need = total - sum(x)
    return allocate_minutes(x, alpha=1.0) if need > 1e-6 else x


def allocate_minutes(raw: list[float], alpha: float | None = None, total: float = 240.0, cap: float = 42.0) -> list[float]:
    a = MINUTES_ALPHA if alpha is None else alpha
    w = [max(m, 0.0) ** a for m in raw]
    if not sum(w):
        return [0.0 for _ in raw]
    lo, hi = 0.0, 10.0 * total / sum(w)
    for _ in range(60):
        c = (lo + hi) / 2
        if sum(min(cap, c * x) for x in w) < total:
            lo = c
        else:
            hi = c
    return [float(min(cap, (lo + hi) / 2 * x)) for x in w]


def player_profiles(lg: str, games: list[dict], team: str, before: str, out_names: set | None = None, recent: int = 5,
                    prior_tot: dict | None = None, prior_min: float | None = -1.0, rate_mult: dict | None = None) -> dict:
    """Rotation for one team from this season's box scores before `before`: projected minutes (recency-weighted
    over the last `recent` team games, 0 when a player sat), per-minute rates for 2PA, 3PA, FTA, assists, offensive
    and defensive rebounds and turnovers (shrunk toward the team's per-player average by 60 minutes), and 2P%, 3P%,
    FT% (shrunk toward the team's by 40, 50 and 25 attempts). Players listed Out are removed and the rest are scaled
    to 240 minutes. A player who sat the last game injured and is not listed Out now is projected at 90% of his
    season minutes and flagged `returning`. Who is on the floor together is not modelled: shares scale with each
    player's minutes."""
    out_names = {n.lower() for n in (out_names or set())}
    if prior_min == -1.0:
        prior_min = PLAYER_PRIOR_MIN
    tg = [g for g in games if g["final"] and g["date"] < before and team in (g["home"], g["away"])]
    boxes = []
    for g in tg:
        p = os.path.join(data.CACHE, f"{lg}_sum_{g['id']}.json")
        if os.path.exists(p):
            with open(p) as f:
                bp = _box_players(json.load(f))
            if team in bp:
                boxes.append((g["date"], bp[team]))
    boxes.sort(key=lambda x: x[0])
    if not boxes:
        return {"players": [], "games": 0, "ast_rate": 0.6}
    T = defaultdict(float)
    acc = {}
    for j, (_, rows) in enumerate(boxes):
        wj = PLAYER_RATE_DECAY ** (len(boxes) - 1 - j) if PLAYER_RATE_DECAY else 1.0   # recent games count more
        for r in rows:
            for k in ("min", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "oreb", "dreb", "ast", "tov"):
                T[k] += r[k]
            a = acc.setdefault(r["id"], {"name": r["name"], "pos": r["pos"], "tot": defaultdict(float), "mins": [], "starter": False,
                                         "pts_raw": 0.0, "reb_raw": 0.0, "ast_raw": 0.0})
            if not r["dnp"] and r["min"] > 0:
                a["pts_raw"] += r["pts"]; a["reb_raw"] += r["oreb"] + r["dreb"]; a["ast_raw"] += r["ast"]
            if not r["dnp"]:
                for k in ("min", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "oreb", "dreb", "ast", "tov"):
                    a["tot"][k] += wj * r[k]
                a["mins"].append(r["min"])
    last = boxes[-recent:]
    for pid, a in acc.items():
        w = [0.85 ** (len(last) - 1 - i) for i in range(len(last))]
        mins = [next((r["min"] for r in rows if r["id"] == pid and not r["dnp"]), 0.0) for _, rows in last]
        a["proj"] = float(np.dot(w, mins) / sum(w))
        if MINUTES_WHEN_PLAYING:
            # Minutes when he plays: recency-weighted over his last `recent` appearances. Whoever sits tonight is
            # removed through the injury report, so counting the games he missed as 0 minutes double-counted his
            # absence (Curry projected 19 minutes after missing 2 of 7). Out of the rotation: no minutes in any of the
            # team's last 3 games (unless he's back from injury, below).
            # Expected minutes = chance he plays x minutes when he plays. The chance counts coach's-decision benchings
            # in the team's last `recent` games; games he missed injured or off the roster don't count either way.
            # Starters sit near 1, so the 240-minute scaling comes out of the deep bench, not the stars.
            played = [r["min"] for _, rows in boxes for r in rows if r["id"] == pid and not r["dnp"] and r["min"] > 0][-recent:]
            wp = [0.85 ** (len(played) - 1 - i) for i in range(len(played))]
            avail = []
            for _, rows in last:
                r = next((r for r in rows if r["id"] == pid), None)
                if r is None:
                    continue
                if not r["dnp"] and r["min"] > 0:
                    avail.append(1.0)
                elif not r["reason"] or "COACH" in r["reason"].upper():
                    avail.append(0.0)
            rate = float(np.mean(avail)) if avail else 0.0
            a["play_rate"] = rate
            a["proj"] = rate * float(np.dot(wp, played) / sum(wp)) if played else 0.0
            if not any(any(r["id"] == pid for r in rows) for _, rows in boxes[-3:]):
                a["proj"] = 0.0                      # not on any of the last 3 box scores: not with the team now
        a["starter"] = any(r["id"] == pid and r["starter"] for r in last[-1][1])
        lr = next((r for r in last[-1][1] if r["id"] == pid), None)
        hurt = bool(lr and lr["dnp"] and lr["reason"] and "COACH" not in lr["reason"].upper())
        a["returning"] = hurt and len(a["mins"]) > 0
        if a["returning"]:                       # sat the last game injured and is not listed Out now
            a["proj"] = 0.9 * float(np.mean(a["mins"]))
    team_min = max(T["min"], 1)
    per_player = lambda k: T[k] / team_min                          # team per-player-minute rate
    tp2 = (T["fgm"] - T["tpm"]) / max(T["fga"] - T["tpa"], 1)
    tp3, tft = T["tpm"] / max(T["tpa"], 1), T["ftm"] / max(T["fta"], 1)
    K = 60.0
    players = []
    for pid, a in acc.items():
        if a["name"].lower() in out_names or a["proj"] < 3:
            continue
        t = a["tot"]
        pt = (prior_tot or {}).get(pid)
        if prior_min and pt and pt["min"] >= 100:
            # prior: the player's own last season (his usage and shooting), worth prior_min minutes
            Kp = prior_min
            pr = lambda k: pt[k] / pt["min"]
            rate = lambda k: (t[k] + Kp * pr(k)) / (t["min"] + Kp)
            fga2 = (t["fga"] - t["tpa"] + Kp * (pr("fga") - pr("tpa"))) / (t["min"] + Kp)
            c2, c3, cf = min(pt["fga"] - pt["tpa"], 150.0), min(pt["tpa"], 150.0), min(pt["fta"], 100.0)
            p2 = (t["fgm"] - t["tpm"] + c2 * (pt["fgm"] - pt["tpm"]) / max(pt["fga"] - pt["tpa"], 1) + 10 * tp2) / (t["fga"] - t["tpa"] + c2 + 10)
            p3 = (t["tpm"] + c3 * pt["tpm"] / max(pt["tpa"], 1) + 15 * tp3) / (t["tpa"] + c3 + 15)
            ftp = (t["ftm"] + cf * pt["ftm"] / max(pt["fta"], 1) + 10 * tft) / (t["fta"] + cf + 10)
            src = "last season"
        else:
            rate = lambda k: (t[k] + K * per_player(k)) / (t["min"] + K)
            fga2 = (t["fga"] - t["tpa"] + K * (per_player("fga") - per_player("tpa"))) / (t["min"] + K)
            p2 = (t["fgm"] - t["tpm"] + 40 * tp2) / (t["fga"] - t["tpa"] + 40)
            p3 = (t["tpm"] + 50 * tp3) / (t["tpa"] + 50)
            ftp = (t["ftm"] + 25 * tft) / (t["fta"] + 25)
            src = "team average"
        m_ = (rate_mult or {}).get(pid) or {}
        f_pts, f_reb, f_ast, f_tpm = (m_.get(k, 1.0) for k in ("pts", "reb", "ast", "tpm"))
        gp = max(len(a["mins"]), 1)
        season = {"gp": len(a["mins"]), "min": float(np.mean(a["mins"])) if a["mins"] else 0.0,
                  "pts": a["pts_raw"] / gp, "reb": a["reb_raw"] / gp, "ast": a["ast_raw"] / gp}
        players.append({"id": pid, "name": a["name"], "pos": a["pos"], "min": a["proj"], "min_sd": float(MIN_SD_SCALE * max(3.0, np.std(a["mins"]) if len(a["mins"]) > 1 else 5.0)),
                        "season": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in season.items()},
                        "games": len(a["mins"]), "starter": a["starter"], "returning": a["returning"],
                        "min_ceil": (max(a["mins"][-10:]) if a["mins"] else 0.0) + MINUTES_PAD,
                        # head-to-head multipliers (nba_research.H2H_COEF): usage x pts factor, 3PA x 3PM factor
                        "fga2": fga2 * f_pts, "fga3": rate("tpa") * f_tpm, "fta": rate("fta") * f_pts, "ast": rate("ast") * f_ast,
                        "oreb": rate("oreb") * f_reb, "dreb": rate("dreb") * f_reb,
                        "tov": rate("tov"), "p2": p2, "p3": p3, "ftp": ftp, "prior": src,
                        "h2h": {k: round(v, 4) for k, v in (("pts", f_pts), ("reb", f_reb), ("ast", f_ast), ("tpm", f_tpm))} if m_ else None})
    for p in players:
        p["min_raw"] = p["min"]
    if players:
        if MINUTES_SHARE == "headroom":
            alloc = allocate_headroom([p["min"] for p in players], [p["min_ceil"] for p in players])
        else:
            alloc = allocate_minutes([p["min"] for p in players])
        for p, m in zip(players, alloc):
            p["min"] = m
    players.sort(key=lambda p: -p["min"])
    return {"players": players, "games": len(boxes), "ast_rate": T["ast"] / max(T["fgm"], 1), "shock": PLAYER_SHOCK, "swing_rho": SWING_RHO, "ast_fix": AST_FIX,
            "garbage": PLAYER_GARBAGE}


def player_backtest(lg: str, games: list[dict], before: str, min_prior: int = 3, prior_tot: dict | None = None) -> dict:
    """Out-of-sample check of the player inputs: for each finished game, profiles from earlier games only (players who
    did not play removed, as if the injury report were known) give expected points, rebounds and assists as
    minutes x per-minute rates; compared with the box score and with the season-to-date per-game average. This scores
    the minutes-and-rates part; the simulation adds the matchup's pace and shooting on top."""
    from collections import defaultdict as dd
    fin = sorted([g for g in games if g["final"] and g["date"] < before], key=lambda g: g["date"])
    err = dd(list)
    for g in fin:
        p = os.path.join(data.CACHE, f"{lg}_sum_{g['id']}.json")
        if not os.path.exists(p):
            continue
        box = _box_players(json.load(open(p)))
        for team in (g["home"], g["away"]):
            rows = box.get(team) or []
            sat = {r["name"] for r in rows if r["dnp"]}
            pr = player_profiles(lg, games, team, g["date"], sat, prior_tot=prior_tot)
            if pr["games"] < min_prior:
                continue
            prof = {q["id"]: q for q in pr["players"]}
            hist = dd(list)                     # season-to-date per-game averages, the baseline
            for h in [x for x in fin if x["date"] < g["date"] and team in (x["home"], x["away"])]:
                hp = os.path.join(data.CACHE, f"{lg}_sum_{h['id']}.json")
                for r in (_box_players(json.load(open(hp))).get(team) or []) if os.path.exists(hp) else []:
                    if not r["dnp"]:
                        hist[r["id"]].append(r)
            for r in rows:
                if r["dnp"] or r["id"] not in prof or not hist.get(r["id"]):
                    continue
                q = prof[r["id"]]
                pred = {"pts": q["min"] * (2 * q["fga2"] * q["p2"] + 3 * q["fga3"] * q["p3"] + q["fta"] * q["ftp"]),
                        "reb": q["min"] * (q["oreb"] + q["dreb"]), "ast": q["min"] * q["ast"]}
                act = {"pts": r["pts"], "reb": r["oreb"] + r["dreb"], "ast": r["ast"]}
                base = {"pts": np.mean([x["pts"] for x in hist[r["id"]]]), "reb": np.mean([x["oreb"] + x["dreb"] for x in hist[r["id"]]]),
                        "ast": np.mean([x["ast"] for x in hist[r["id"]]])}
                for k in pred:
                    err[k].append((pred[k] - act[k], base[k] - act[k]))
    out = {"n": len(err["pts"])}
    for k, v in err.items():
        a = np.array(v)
        out[k] = {"mae": float(np.abs(a[:, 0]).mean()), "bias": float(a[:, 0].mean()), "base_mae": float(np.abs(a[:, 1]).mean())}
    return out



# ------------------------------------------------------------------ availability: who is out, priced into team strength
INJURY_K = 200.0          # minutes of bench-level prior on a player's per-minute value
# Margin points per Game Score point of value lost (availability_shift). Fitted on 2025-26 Nov-Jan (682 games,
# ratings-only residuals): 0.50 +- 0.10; full season 0.53 +- 0.07. On the held-out Feb-Apr games it cut the margin
# RMSE from 15.20 to 14.65 points.
INJURY_BETA = 0.50


def _box_cached(lg: str, gid: str, _memo={}):
    key = (lg, gid)
    if key not in _memo:
        p = os.path.join(data.CACHE, f"{lg}_sum_{gid}.json")
        if os.path.exists(p):
            with open(p) as f:
                _memo[key] = _box_players(json.load(f))
        else:
            _memo[key] = {}
    return _memo[key]


def _gmsc(r: dict) -> float:
    """Hollinger Game Score from one box-score line."""
    return (r["pts"] + 0.4 * r["fgm"] - 0.7 * r["fga"] - 0.4 * (r["fta"] - r["ftm"]) + 0.7 * r["oreb"] + 0.3 * r["dreb"]
            + r.get("stl", 0) + 0.7 * r["ast"] + 0.7 * r.get("blk", 0) - 0.4 * r.get("pf", 0) - r["tov"])


def player_values(lg: str, games: list[dict], team: str, before: str) -> dict:
    """Each player's worth to `team` in the games its ratings were fitted on (finished, before `before`): Game Score
    per minute above the team's bench level (players outside its top five by minutes), shrunk toward the bench by
    INJURY_K minutes; his minutes when he plays; and the share of those team games he missed, which the team rating
    already reflects."""
    tg = [g for g in games if g["final"] and g["date"] < before and team in (g["home"], g["away"])]
    acc, n = {}, 0
    for g in tg:
        rows = _box_cached(lg, g["id"]).get(team)
        if not rows:
            continue
        n += 1
        for r in rows:
            a = acc.setdefault(r["id"], {"name": r["name"], "gs": 0.0, "min": 0.0, "gp": 0})
            if not r["dnp"] and r["min"] > 0:
                a["gs"] += _gmsc(r)
                a["min"] += r["min"]
                a["gp"] += 1
    if not n:
        return {"games": 0, "players": {}}
    top = sorted(acc.values(), key=lambda a: -a["min"])
    bench = [a for a in top[5:] if a["min"] > 0]
    repl = sum(a["gs"] for a in bench) / max(sum(a["min"] for a in bench), 1.0) if bench else 0.25
    out = {}
    for pid, a in acc.items():
        if a["gp"] == 0:
            continue
        pm = (a["gs"] + INJURY_K * repl) / (a["min"] + INJURY_K)
        out[pid] = {"name": a["name"], "value": (pm - repl) * a["min"] / a["gp"], "min": a["min"] / a["gp"],
                    "gp": a["gp"], "missed_share": 1.0 - a["gp"] / n}
    return {"games": n, "replacement_per_min": repl, "players": out}


def availability_shift(vals: dict, absent: set) -> dict:
    """Game Score points per game the team is missing tonight relative to the lineup its rating was fitted on:
    sum over players of value x (absent tonight - share of the rating games he missed). A player who already sat
    half the games is half priced in; one back from a long absence makes the team better than its rating."""
    tot, rows = 0.0, []
    for pid, v in vals["players"].items():
        d = v["value"] * ((1.0 if pid in absent else 0.0) - v["missed_share"])
        if abs(d) > 0.05:
            rows.append({"id": pid, "name": v["name"], "value": round(v["value"], 2), "missed_share": round(v["missed_share"], 2),
                         "out_tonight": pid in absent, "shift": round(d, 2)})
        tot += d
    return {"lost": tot, "rows": sorted(rows, key=lambda r: -abs(r["shift"]))}


def ppp_expected(s: dict, and1: float) -> float:
    """Expected points per possession from one side's rates (the possession engine's structure, analytically)."""
    pm = s["three"] * s["p3"] + (1 - s["three"]) * s["p2"]
    shot = s["three"] * s["p3"] * 3 + (1 - s["three"]) * s["p2"] * 2 + pm * and1 * s["ftp"]
    miss = (1 - pm) * s["orb"]
    return (1 - s["to"]) * (s["ft_rate"] * 2 * s["ftp"] + (1 - s["ft_rate"]) * shot * (1 + miss + miss * miss))


def shift_offense(s: dict, R: dict, points: float) -> dict:
    """Move a side's 2- and 3-point make rates by one common logit step so it scores `points` more per game
    (negative: fewer), at the game's pace."""
    if not points:
        return s
    pace = R["league"]["pace"] + s.get("pace_off", 0.0)
    target = points / max(pace, 1.0)
    lo = lambda p: np.log(p / (1 - p))
    sg = lambda z: 1 / (1 + np.exp(-z))
    base = ppp_expected(s, R.get("and1", 0.0))
    def at(d):
        t = dict(s)
        t["p2"], t["p3"] = float(sg(lo(s["p2"]) + d)), float(sg(lo(s["p3"]) + d))
        return t
    slope = (ppp_expected(at(0.01), R.get("and1", 0.0)) - base) / 0.01
    return at(target / slope if slope else 0.0)


def absent_tonight(lg: str, games: list[dict], team: str, before: str, out_names: set) -> set:
    """Live availability: players listed Out or Doubtful, plus players from the rating sample who are no longer on the
    roster (missing from the team's latest box score altogether, e.g. traded). A player on the latest box who sat
    injured and isn't listed now counts as back."""
    vals = player_values(lg, games, team, before)
    tg = sorted((g for g in games if g["final"] and g["date"] < before and team in (g["home"], g["away"])), key=lambda g: g["date"])
    roster = {r["id"] for r in (_box_cached(lg, tg[-1]["id"]).get(team) or [])} if tg else set()
    names = {n.lower() for n in out_names}
    return {pid for pid, v in vals["players"].items() if v["name"].lower() in names or (roster and pid not in roster)}


# ------------------------------------------------------------------ team strength from player ratings
# Weight on the player-rating margin against the team-rating model's (None: off). Fitted on 2025-26 Nov-Jan only
# (473 games, regression of the result on the gap). Held out (real simulations, availability on, no score effects):
# 2025-26 Feb-Apr winner Brier 0.1807 -> 0.1780, margin RMSE 14.65 -> 14.53; 2026-27 to date 0.2234 -> 0.2033
# (CI -0.038 to -0.003), margin RMSE 14.23 -> 13.49. LAM and DELTA were picked on the Nov-Jan games from a 14-point grid.
PLAYER_RATING_W = 0.59
PLAYER_RATING_LAM = 20.0     # ridge: each player's effect is shrunk toward his box-score prior by this many games
PLAYER_RATING_DELTA = 1.0    # weight on last season's games (the season before that: squared)
PLAYER_RATING_KMIN = 300.0   # minutes of new-player Game Score rate in each player's box-score prior


def season_of(date: str) -> int:
    """Season by its start year (Oct-Jun: the season that began in October)."""
    return int(date[:4]) if date[5:7] >= "09" else int(date[:4]) - 1


class PlayerRatings:
    """Team strength from the players on the floor. A game-level ridge regression of the final margin on who played
    (each team's players weighted by 5 x their share of its minutes, + home, - away):
        margin = home edge + c x (box-score prior of the floor) + sum of player effects,
    each player's box-score prior being his Game Score per 48 above the league (shrunk toward new-player level by
    PLAYER_RATING_KMIN minutes) and his effect shrunk toward 0, i.e. toward that prior, by PLAYER_RATING_LAM games.
    Fitted on every game before the cutoff: this season at full weight, last season at DELTA, the one before at
    DELTA^2. It carries a player's value from team to team and from last season, and it sees what a box score misses
    (defence, spacing) once a player has enough games. Tonight's margin: the expected lineup at its minutes."""

    def __init__(self, lg: str, games: list[dict], year: int, lam: float | None = None, delta: float | None = None,
                 prepared: list[dict] | None = None):
        self.lg, self.year = lg, year
        self.lam = PLAYER_RATING_LAM if lam is None else lam
        self.delta = PLAYER_RATING_DELTA if delta is None else delta
        self.games = prepared if prepared is not None else self._prepare(lg, games, year)
        self.pids = sorted({p for g in self.games for p, *_ in g["rows"]})
        self.ix = {p: i for i, p in enumerate(self.pids)}
        self.hist = defaultdict(list)                   # (date, minutes) of every appearance, any team
        for g in self.games:
            for p, _, m, _ in g["rows"]:
                self.hist[p].append((g["date"], m))
        self._reset()

    @staticmethod
    def _prepare(lg: str, games: list[dict], year: int) -> list[dict]:
        """One row per finished game with box scores: date, season, home flag, margin, and per player (id, signed
        5 x minute share, minutes, Game Score). This season's games plus the two before."""
        G = {g["id"]: g for g in games}
        for yy in (year, year - 1):                     # LAST_SEASON[y] is the season before y
            span = LAST_SEASON.get(yy) if lg == "nba" else None
            if span:
                for g in season_games(lg, *span):
                    G.setdefault(g["id"], g)
        out = []
        for g in sorted(G.values(), key=lambda g: g["date"]):
            if not g["final"] or season_of(g["date"]) > year:
                continue
            box = _box_cached(lg, g["id"])
            sides = []
            for s_, sg in (("home", 1.0), ("away", -1.0)):
                rows = [r for r in box.get(g[s_], []) if not r["dnp"] and r["min"] > 0]
                tot = sum(r["min"] for r in rows)
                sides.append([(r["id"], sg * 5.0 * r["min"] / tot, r["min"], _gmsc(r)) for r in rows] if tot else [])
            if not sides[0] or not sides[1]:
                continue
            out.append({"id": g["id"], "date": g["date"], "season": season_of(g["date"]), "h": 0.0 if g["neutral"] else 1.0,
                        "y": g["score"]["home"] - g["score"]["away"], "rows": sides[0] + sides[1]})
        return out

    def _reset(self):
        P = len(self.pids)
        self.k, self.cut = 0, ""
        self.Gm, self.gH, self.gy = np.zeros((P, P)), np.zeros(P), np.zeros(P)
        self.HH = self.Hy = 0.0
        self.MIN, self.GS = np.zeros(P), np.zeros(P)

    def fit(self, before: str) -> dict:
        """Ratings from games strictly before `before` (incremental when cutoffs only move forward)."""
        if before < self.cut:
            self._reset()
        while self.k < len(self.games) and self.games[self.k]["date"] < before:
            g = self.games[self.k]
            w = self.delta ** (self.year - g["season"])
            i = np.array([self.ix[p] for p, *_ in g["rows"]]); x = np.array([v for _, v, _, _ in g["rows"]])
            self.Gm[np.ix_(i, i)] += w * np.outer(x, x)
            np.add.at(self.gH, i, w * g["h"] * x); np.add.at(self.gy, i, w * g["y"] * x)
            self.HH += w * g["h"] ** 2; self.Hy += w * g["h"] * g["y"]
            np.add.at(self.MIN, i, w * np.array([m for *_, m, _ in g["rows"]]))
            np.add.at(self.GS, i, w * np.array([s for *_, s in g["rows"]]))
            self.k += 1
        self.cut = before
        P = len(self.pids)
        if self.k < 100:
            return {"n_games": self.k, "r": np.zeros(P), "h": 0.0, "c": 0.0}
        small = (self.MIN > 0) & (self.MIN < 300)
        gbar = self.GS.sum() / self.MIN.sum()
        gnew = self.GS[small].sum() / max(self.MIN[small].sum(), 1.0) if small.any() else gbar
        prior = 48.0 * ((self.GS + PLAYER_RATING_KMIN * gnew) / (self.MIN + PLAYER_RATING_KMIN) - gbar)
        Gp = self.Gm @ prior
        A = np.zeros((P + 2, P + 2)); b = np.zeros(P + 2)
        A[0, 0], A[0, 1], A[0, 2:] = self.HH, self.gH @ prior, self.gH
        A[1, 1], A[1, 2:] = prior @ Gp, Gp
        A[2:, 2:] = self.Gm + self.lam * np.eye(P)
        A = np.triu(A) + np.triu(A, 1).T + 1e-9 * np.eye(P + 2)
        b[0], b[1], b[2:] = self.Hy, self.gy @ prior, self.gy
        beta = np.linalg.solve(A, b)
        return {"n_games": self.k, "h": float(beta[0]), "c": float(beta[1]), "r": beta[1] * prior + beta[2:],
                "new_player": float(48.0 * (gnew - gbar) * beta[1])}

    def minutes_when_playing(self, pid: str, before: str) -> float | None:
        h = [m for d, m in self.hist.get(pid, []) if d < before][-10:]
        if not h:
            return None
        w = 0.85 ** np.arange(len(h))[::-1]
        return float((w * np.array(h)).sum() / w.sum())

    def rating(self, fit: dict, pid: str) -> float:
        i = self.ix.get(pid)
        return float(fit["r"][i]) if i is not None else fit.get("new_player", 0.0)

    def margin(self, fit: dict, home: dict, away: dict, neutral: bool = False) -> dict:
        """Expected home margin from two lineups {player id: expected minutes} (each scaled to 240)."""
        val = {}
        for s_, L in (("home", home), ("away", away)):
            tot = sum(L.values())
            val[s_] = sum(5.0 * m / tot * self.rating(fit, p) for p, m in L.items()) if tot else 0.0
        return {"margin": val["home"] - val["away"] + (0.0 if neutral else fit["h"]), "home": val["home"], "away": val["away"], "h": fit["h"]}

    def lineup_played(self, gid: str, team: str, before: str) -> dict:
        """Backtest lineup: the players who played (the availability convention), each at his minutes when playing
        from earlier games (12 if none)."""
        rows = [r for r in _box_cached(self.lg, gid).get(team, []) if not r["dnp"] and r["min"] > 0]
        return {r["id"]: (self.minutes_when_playing(r["id"], before) or 12.0) for r in rows}


def expected_margin(H: dict, A: dict, R: dict) -> float:
    """The team-rating model's expected home margin from its two sides (possessions x points per possession)."""
    pace = R["league"]["pace"] + (H.get("pace_off", 0.0) + A.get("pace_off", 0.0)) / 2
    return pace * (ppp_expected(H, R.get("and1", 0.0)) - ppp_expected(A, R.get("and1", 0.0)))


def with_player_ratings(H: dict, A: dict, R: dict, pr_margin: float | None, w: float | None = None) -> tuple:
    """Move the model's margin w of the way to the player-rating margin (total unchanged). Returns (H, A, shift)."""
    w = PLAYER_RATING_W if w is None else w
    if not w or pr_margin is None:
        return H, A, 0.0
    d = w * (pr_margin - expected_margin(H, A, R))
    H2, A2 = apply_prior(H, A, R, d, 0.0)
    return H2, A2, d


# ------------------------------------------------------------------ preseason prior: last season, moved with the players
# Early in a season each team's rating is a handful of games shrunk toward league average. The prior replaces "average"
# with last season's strength, regressed toward average (PRIOR_RHO) and corrected for players who left or arrived (their
# Game Score value x INJURY_BETA), and fades as this season's games pile up (worth PRIOR_K games). Both constants are
# set by the fair test: tuned on 2025-26 (prior from 2024-25), judged on 2026-27 (prior from 2025-26).
# OFF: the fair test (2026-11-03) did not show a reliable gain. Tuned on all of 2025-26 (979 games) the best setting
# (k 4, rho 0.4) moved the margin RMSE 14.478 -> 14.464: better Oct-Dec (14.42 -> 14.26), slightly worse Jan-Apr
# (14.50 -> 14.53). On the held-out 2026-27 games (93) it moved 15.08 -> 14.83 (CI of the change includes 0) while
# winners right fell from 59 to 55. Tuned on Oct-Dec only (k 25, rho 0.55) it hurt Jan-Apr significantly.
PRIOR_K = None
PRIOR_RHO = None


def team_net(R: dict, team: str) -> float:
    """Points per game better than a league-average team on a neutral floor, at league pace."""
    and1 = R.get("and1", 0.07)
    return R["league"]["pace"] * (ppp_expected(side(R, team, "_", False), and1) - ppp_expected(side(R, "_", team, False), and1))


def season_player_values(lg: str, games: list[dict], before: str) -> dict:
    """Every player's season: {pid: {name, value (per game he played, vs his team's bench), gp, teams: {team: share of
    that team's games he played}}}. A player traded mid-season gets his games-weighted value across teams."""
    teams = sorted({g[s] for g in games if g["final"] and g["date"] < before for s in ("home", "away")})
    out = {}
    for t in teams:
        v = player_values(lg, games, t, before)
        for pid, p in v["players"].items():
            o = out.setdefault(pid, {"name": p["name"], "vsum": 0.0, "gp": 0, "teams": {}})
            o["vsum"] += p["value"] * p["gp"]
            o["gp"] += p["gp"]
            o["teams"][t] = 1.0 - p["missed_share"]
    for o in out.values():
        o["value"] = o["vsum"] / max(o["gp"], 1)
    return out


def preseason_prior(R_last: dict, last_vals: dict, team: str, roster_now: set, games_last: int = 82) -> dict:
    """Last season's net rating for `team`, plus the value of players who arrived minus those who left (each weighted
    by how much he played: arrivals by games played last season, leavers by their share of this team's games)."""
    arrived = [(p["name"], p["value"] * min(p["gp"] / games_last, 1.0)) for pid, p in last_vals.items()
               if pid in roster_now and team not in p["teams"]]
    left = [(p["name"], p["value"] * p["teams"][team]) for pid, p in last_vals.items()
            if team in p["teams"] and pid not in roster_now]
    delta = INJURY_BETA * (sum(v for _, v in arrived) - sum(v for _, v in left))
    return {"net_last": team_net(R_last, team) if team in R_last["teams"] else 0.0, "roster_delta": delta,
            "arrived": sorted(arrived, key=lambda x: -x[1])[:4], "left": sorted(left, key=lambda x: -x[1])[:4]}


def prior_shifts(R: dict, prior: dict, home: str, away: str, k: float | None = None, rho: float | None = None) -> tuple:
    """Margin points each team moves by when its current rating is blended with the prior (weight k / (k + games))."""
    k, rho = PRIOR_K if k is None else k, PRIOR_RHO if rho is None else rho
    out = []
    for t in (home, away):
        n = R["teams"].get(t, {}).get("games", 0)
        w = k / (k + n) if k else 0.0
        target = rho * (prior[t]["net_last"] + prior[t]["roster_delta"])
        out.append(w * (target - (team_net(R, t) if t in R["teams"] else 0.0)))
    return tuple(out)


def apply_prior(H: dict, A: dict, R: dict, s_home: float, s_away: float) -> tuple:
    """Move the margin by s_home - s_away without moving the total: each offense up by half its own shift and down by
    half the opponent's."""
    d = (s_home - s_away) / 2
    return shift_offense(H, R, d), shift_offense(A, R, -d)


LAST_SEASON = {2025: ("20241022", "20250413"), 2026: ("20251021", "20260412")}   # regular season of the year before


def prior_context(lg: str, season_year: int, _memo={}) -> dict | None:
    """Last season's ratings and player values (for the preseason prior), or None if that season isn't available."""
    key = (lg, season_year)
    if key not in _memo:
        span = LAST_SEASON.get(season_year)
        if lg != "nba" or span is None:
            _memo[key] = None
        else:
            G0 = season_games(lg, *span)
            R0 = ratings(G0, "2099-01-01", 48)
            R0["and1"] = 0.07
            _memo[key] = {"R0": R0, "lv": season_player_values(lg, G0, "2099-01-01"), "season": span}
    return _memo[key]


def latest_roster(lg: str, games: list[dict], team: str, before: str) -> set:
    """Players on the team's most recent box score before `before` (played or not)."""
    tg = sorted((g for g in games if g["final"] and g["date"] < before and team in (g["home"], g["away"])), key=lambda g: g["date"])
    return {r["id"] for r in (_box_cached(lg, tg[-1]["id"]).get(team) or [])} if tg else set()


def with_prior(H: dict, A: dict, R: dict, ctx: dict | None, home: str, away: str, rosters: dict) -> tuple:
    """Apply the preseason prior (no-op while PRIOR_K is unset or there's no last-season context)."""
    if not ctx or not PRIOR_K:
        return H, A, None
    prior = {t: preseason_prior(ctx["R0"], ctx["lv"], t, rosters[t]) for t in (home, away)}
    sh, sa = prior_shifts(R, prior, home, away)
    H2, A2 = apply_prior(H, A, R, sh, sa)
    for t, s in ((home, sh), (away, sa)):
        prior[t]["shift"] = s
    return H2, A2, prior



def dk_player_lines(lg: str, gid: str, tip: str | None = None) -> dict:
    """DraftKings player lines (points, rebounds, assists, 3s and the four combos) for one game from ESPN's propBets
    feed: {pid: {stat: {line, over,
    under, updated}}}. Lines changed after tip-off are replaced by the opening line. The feed doesn't label which price is
    the over (lesson L2): the pair is matched to the milestone price ("N+") where one exists, else sides stay unknown.
    Empty when DraftKings hasn't posted yet (404)."""
    import urllib.request
    u = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/{'nba' if lg == 'nba' else lg}/events/{gid}/competitions/{gid}/odds/100/propBets?limit=1000"
    try:
        items = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)).get("items", [])
    except Exception:
        return {}
    TY = {"Total Points": "pts", "Total Assists": "ast", "Total Rebounds": "reb", "Total 3-Point Field Goals": "tpm",
          "Total Points, Rebounds, and Assists": "pra", "Total Points and Rebounds": "pr", "Total Points and Assists": "pa",
          "Total Assists and Rebounds": "ra"}
    MS = {"Points Milestones": "pts", "Assists Milestones": "ast", "Rebounds Milestones": "reb", "3-Point Field Goals Milestones": "tpm",
          "Points + Assists + Rebounds Milestones": "pra", "Points + Rebounds Milestones": "pr", "Points + Assists Milestones": "pa",
          "Rebounds + Assists Milestones": "ra"}
    raw, ms = {}, {}
    for i in items:
        if not i.get("athlete"):
            continue
        pid = i["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
        late = bool(tip) and (i.get("lastUpdated") or "") >= tip[:16]
        tgt = ((i.get("open") if late else i.get("current")) or i.get("current") or {}).get("target") or {}
        price = (i.get("odds") or {}).get("american") or {}
        am = price.get("open") if late else price.get("value")
        nm = i["type"]["name"]
        if nm in TY and tgt.get("value") is not None:
            raw.setdefault((pid, TY[nm]), {"line": tgt["value"], "prices": [], "updated": i.get("lastUpdated")})["prices"].append(am)
        elif nm in MS and tgt.get("value") is not None:
            ms[(pid, MS[nm], int(tgt["value"]))] = am
    f = lambda a: data.f(str(a).replace("+", ""), 0.0)
    out = {}
    for (pid, st), L in raw.items():
        d = {"line": L["line"], "updated": L["updated"], "over": None, "under": None}
        m = ms.get((pid, st, int(L["line"] + 0.5)))
        if m and len(L["prices"]) == 2:
            o = min(range(2), key=lambda j: abs(f(L["prices"][j]) - f(m)))
            d["over"], d["under"] = L["prices"][o], L["prices"][1 - o]
        out.setdefault(pid, {})[st] = d
    return out
