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
        foul = late & (diff >= 3) & (diff <= 8) & (c > 2)                       # defence trails by 3-8: foul at once
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
        pending = fga.copy()
        extra_t = np.zeros(k)
        for attempt in range(3):
            if not pending.any():
                break
            is3 = pending & (need3 | (rng.random(k) < p_3[o]))
            made = pending & (rng.random(k) < np.where(is3, sg(L3[a, o]), sg(L2[a, o])))
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
    lo, hi = 0.0, 4.0
    for _ in range(7):
        R["home_scale"] = (lo + hi) / 2
        sh = simulate(side(R, "_", "_", True), side(R, "_", "_", False), R, minutes, n=n, seed=2, shot_clock=shot_clock)
        if float((sh["home"] - sh["away"]).mean()) < target:
            lo = R["home_scale"]
        else:
            hi = R["home_scale"]
    R["home_scale"] = (lo + hi) / 2
    R["ppg_target"] = ppg
    return R


def backtest(games: list[dict], minutes: int, shot_clock: int, min_games: int = 3, n: int = 6000, seed: int = 3) -> dict:
    from .backtest import metrics, no_vig
    recs = []
    by_day = defaultdict(list)
    for g in games:
        if g["final"] and len(g["box"]) == 2 and g["line"]["ml_home"] is not None:
            by_day[g["date"][:10]].append(g)
    for day in sorted(by_day):
        R = ratings(games, day, minutes)
        if R["n_games"] < 20:
            continue
        R = calibrate(R, games, day, minutes, shot_clock, n=6000)
        for g in by_day[day]:
            if min(R["teams"].get(g["home"], {}).get("games", 0), R["teams"].get(g["away"], {}).get("games", 0)) < min_games:
                continue
            ln = g["line"]
            sim = simulate(side(R, g["home"], g["away"], not g["neutral"]), side(R, g["away"], g["home"], False), R, minutes,
                           n=n, seed=seed + len(recs), shot_clock=shot_clock)
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
                         "overed": None if tl is None or tot == tl else float(tot > tl), "sim_total": float((h + a).mean()), "total": tot})
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
            v = dict(zip(lab, a.get("stats") or []))
            fg, tp, ft = _split(v.get("FG", "0-0")), _split(v.get("3PT", "0-0")), _split(v.get("FT", "0-0"))
            rows.append({"id": a["athlete"]["id"], "name": a["athlete"]["displayName"], "pos": (a["athlete"].get("position") or {}).get("abbreviation", ""),
                         "starter": bool(a.get("starter")), "dnp": bool(a.get("didNotPlay")) or not v, "reason": a.get("reason") or "",
                         "min": data.f(v.get("MIN"), 0) or 0, "pts": data.f(v.get("PTS"), 0) or 0, "fgm": fg[0], "fga": fg[1], "tpm": tp[0], "tpa": tp[1],
                         "ftm": ft[0], "fta": ft[1], "oreb": data.f(v.get("OREB"), 0) or 0, "dreb": data.f(v.get("DREB"), 0) or 0,
                         "ast": data.f(v.get("AST"), 0) or 0, "tov": data.f(v.get("TO"), 0) or 0})
        out[t["team"]["abbreviation"]] = rows
    return out


def reb_credit(games: list[dict], before: str) -> float:
    """Share of missed field goals that end as a player rebound in the box score (the rest are team rebounds and
    rebounds of missed free throws, which the possession engine doesn't produce separately)."""
    G = [g for g in games if g["final"] and g["date"] < before and len(g["box"]) == 2]
    miss = sum(g["box"][s]["fga"] - g["box"][s]["fgm"] for g in G for s in ("home", "away"))
    reb = sum(g["box"][s]["orb"] + g["box"][s]["drb"] for g in G for s in ("home", "away"))
    return float(min(1.0, reb / miss)) if miss else 0.93


def player_profiles(lg: str, games: list[dict], team: str, before: str, out_names: set | None = None, recent: int = 5) -> dict:
    """Rotation for one team from this season's box scores before `before`: projected minutes (recency-weighted
    over the last `recent` team games, 0 when a player sat), per-minute rates for 2PA, 3PA, FTA, assists, offensive
    and defensive rebounds and turnovers (shrunk toward the team's per-player average by 60 minutes), and 2P%, 3P%,
    FT% (shrunk toward the team's by 40, 50 and 25 attempts). Players listed Out are removed and the rest are scaled
    to 240 minutes. A player who sat the last game injured and is not listed Out now is projected at 90% of his
    season minutes and flagged `returning`. Who is on the floor together is not modelled: shares scale with each
    player's minutes."""
    out_names = {n.lower() for n in (out_names or set())}
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
    for _, rows in boxes:
        for r in rows:
            for k in ("min", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "oreb", "dreb", "ast", "tov"):
                T[k] += r[k]
            a = acc.setdefault(r["id"], {"name": r["name"], "pos": r["pos"], "tot": defaultdict(float), "mins": [], "starter": False})
            if not r["dnp"]:
                for k in ("min", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "oreb", "dreb", "ast", "tov"):
                    a["tot"][k] += r[k]
                a["mins"].append(r["min"])
    last = boxes[-recent:]
    for pid, a in acc.items():
        w = [0.85 ** (len(last) - 1 - i) for i in range(len(last))]
        mins = [next((r["min"] for r in rows if r["id"] == pid and not r["dnp"]), 0.0) for _, rows in last]
        a["proj"] = float(np.dot(w, mins) / sum(w))
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
        rate = lambda k: (t[k] + K * per_player(k)) / (t["min"] + K)
        players.append({"id": pid, "name": a["name"], "pos": a["pos"], "min": a["proj"], "min_sd": float(max(3.0, np.std(a["mins"]) if len(a["mins"]) > 1 else 5.0)),
                        "games": len(a["mins"]), "starter": a["starter"], "returning": a["returning"],
                        "fga2": (t["fga"] - t["tpa"] + K * (per_player("fga") - per_player("tpa"))) / (t["min"] + K), "fga3": rate("tpa"),
                        "fta": rate("fta"), "ast": rate("ast"), "oreb": rate("oreb"), "dreb": rate("dreb"), "tov": rate("tov"),
                        "p2": (t["fgm"] - t["tpm"] + 40 * tp2) / (t["fga"] - t["tpa"] + 40), "p3": (t["tpm"] + 50 * tp3) / (t["tpa"] + 50),
                        "ftp": (t["ftm"] + 25 * tft) / (t["fta"] + 25)})
    tot = sum(p["min"] for p in players)
    if tot > 0:
        for p in players:
            p["min"] = float(min(42.0, p["min"] * 240.0 / tot))
    players.sort(key=lambda p: -p["min"])
    return {"players": players, "games": len(boxes), "ast_rate": T["ast"] / max(T["fgm"], 1)}


def player_backtest(lg: str, games: list[dict], before: str, min_prior: int = 3) -> dict:
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
            pr = player_profiles(lg, games, team, g["date"], sat)
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
