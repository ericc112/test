"""Model inputs for one game (as of kickoff), and the out-of-sample backtest against closing lines.

Every input is computed from data dated before the game: team ratings and pace from that season's earlier
plays, QB ratings from earlier plays (last season at half weight), the drive model from drives before the week.
The backtest replays finished games this way and scores the model against the closing no-vig market.
"""
from __future__ import annotations

import numpy as np

from . import drives as dm
from . import engine, players, ratings
from .data import f


def no_vig(a: float | None, b: float | None) -> float | None:
    """Two-way American prices -> probability of the first side with the vig removed (multiplicative)."""
    if a is None or b is None:
        return None
    imp = lambda x: 100 / (x + 100) if x > 0 else -x / (-x + 100)
    pa, pb = imp(a), imp(b)
    return pa / (pa + pb)


def fair_american(p: float) -> str:
    if p <= 0 or p >= 1:
        return "n/a"
    return f"{-100 * p / (1 - p):+.0f}" if p > 0.5 else f"{100 * (1 - p) / p:+.0f}"   # even money is +100


def inputs_for(sched_row: dict, plays_season: list[dict], plays_prior: list[dict], drives_all: list[dict],
               qb_home: str | None = None, qb_away: str | None = None, fg_wind_logit: float = 0.0, lam: float | None = None) -> dict:
    """Ratings, pace and QB adjustments for one game, from data strictly before its date.
    qb_home/qb_away are gsis ids; default is the starter nflverse lists for the game."""
    before, season = sched_row["gameday"], sched_row["season"]
    rp = ratings.rating_plays(plays_season, before=before)
    R = ratings.team_ratings(rp, lam or ratings.LAMBDA_TEAM)
    Q = ratings.qb_ratings(rp, ratings.rating_plays(plays_prior))
    pc = ratings.pace(drives_all, before=before, season=season)
    out = {"ratings": R, "qbs": Q, "pace": pc, "rating_plays": rp, "fg_wind_logit": fg_wind_logit}
    for side, team, qb in (("home", sched_row["home_team"], qb_home or sched_row["home_qb_id"]),
                           ("away", sched_row["away_team"], qb_away or sched_row["away_qb_id"])):
        t = R["teams"].get(team, {"off_epa": 0.0, "def_epa": 0.0, "off_sr": 0.0, "def_sr": 0.0, "db_share": 0.6})
        qd = players.qb_delta(team, qb, rp, Q, t["db_share"])
        out[side] = {"team": team, "off_epa": t["off_epa"], "def_epa": t["def_epa"], "off_sr": t["off_sr"], "def_sr": t["def_sr"],
                     "db_share": t["db_share"], "pace_ratio": pc["teams"].get(team, pc["league"]) / pc["league"],
                     "qb_delta": qd["delta"], "qb": qd, "qb_id": qb}
    return out


def market(sched_row: dict) -> dict:
    """Closing lines from the nflverse schedule, home perspective, vig removed."""
    sp = f(sched_row["spread_line"])
    return {"p_home": no_vig(f(sched_row["home_moneyline"]), f(sched_row["away_moneyline"])),
            "spread_home": None if sp is None else -sp,
            "p_cover": no_vig(f(sched_row["home_spread_odds"]), f(sched_row["away_spread_odds"])),
            "total": f(sched_row["total_line"]), "p_over": no_vig(f(sched_row["over_odds"]), f(sched_row["under_odds"]))}


def run(sched: list[dict], plays_season: list[dict], plays_prior: list[dict], season: str, weeks: list[int],
        n: int = 10000, seed: int = 11, lam: float | None = None) -> dict:
    """Replay finished games week by week; every input from data before that game."""
    drives_all = dm.build_drives(plays_prior + plays_season)
    allp = plays_prior + plays_season
    recs = []
    for w in weeks:
        games = [g for g in sched if g["season"] == season and g["game_type"] == "REG" and int(g["week"]) == w and g["result"]]
        if not games:
            continue
        first_day = min(g["gameday"] for g in games)
        model = dm.fit(allp, drives_all, before=first_day)
        for g in games:
            inp = inputs_for(g, plays_season, plays_prior, drives_all, lam=lam)
            mk = market(g)
            sim = engine.simulate({"home": inp["home"], "away": inp["away"]}, model, n=n, seed=seed + int(g["gameday"].replace("-", "")) % 1000)
            S = engine.summary(sim, mk["spread_home"], mk["total"])
            res = f(g["result"])
            recs.append({"game": g["game_id"], "week": w, "p_home": S["home_win"][0] / max(1 - S["tie"][0], 1e-9),
                         "mk_home": mk["p_home"], "won": None if res == 0 else float(res > 0),
                         "p_cover": S.get("home_cover", (None,))[0], "mk_cover": mk["p_cover"],
                         "covered": None if mk["spread_home"] is None or res + mk["spread_home"] == 0 else float(res + mk["spread_home"] > 0),
                         "p_over": S.get("over", (None,))[0], "mk_over": mk["p_over"],
                         "overed": None if mk["total"] is None or f(g["total"]) == mk["total"] else float(f(g["total"]) > mk["total"])})
    return {"records": recs, "metrics": metrics(recs)}


def _score(ps, ys):
    ps = np.clip(np.array(ps, float), 1e-4, 1 - 1e-4)
    ys = np.array(ys, float)
    return float(np.mean((ps - ys) ** 2)), float(-np.mean(ys * np.log(ps) + (1 - ys) * np.log(1 - ps)))


def metrics(recs: list[dict]) -> dict:
    out = {}
    for key, mkey, ykey in (("win", "mk_home", "won"), ("cover", "mk_cover", "covered"), ("total", "mk_over", "overed")):
        pk = {"win": "p_home", "cover": "p_cover", "total": "p_over"}[key]
        rs = [r for r in recs if r[ykey] is not None and r[mkey] is not None and r[pk] is not None]
        if not rs:
            continue
        pm, pmk, ys = [r[pk] for r in rs], [r[mkey] for r in rs], [r[ykey] for r in rs]
        bm, lm = _score(pm, ys)
        bk, lk = _score(pmk, ys)
        diff = np.array(pm) - np.array(pmk)
        cal = []
        for lo, hi in ((0, .3), (.3, .45), (.45, .55), (.55, .7), (.7, 1.01)):
            m = (np.array(pm) >= lo) & (np.array(pm) < hi)
            if m.any():
                cal.append((lo, min(hi, 1.0), int(m.sum()), float(np.array(pm)[m].mean()), float(np.array(ys)[m].mean())))
        out[key] = {"n": len(rs), "brier_model": bm, "brier_market": bk, "logloss_model": lm, "logloss_market": lk,
                    "rms_vs_market": float(np.sqrt(np.mean(diff ** 2))), "mean_vs_market": float(diff.mean()), "calibration": cal}
    return out


def run_pbp(sched: list[dict], plays_season: list[dict], plays_prior: list[dict], season: str, weeks: list[int],
            n: int = 10000, seed: int = 11) -> dict:
    """Same out-of-sample replay with the play-by-play engine (league model and ratings rebuilt each week)."""
    from . import nfl_pbp
    recs = []
    for w in weeks:
        games = [g for g in sched if g["season"] == season and g["game_type"] == "REG" and int(g["week"]) == w and g["result"]]
        if not games:
            continue
        B = nfl_pbp.build(plays_season, plays_prior, sched, min(g["gameday"] for g in games))
        for g in games:
            pr = B["ratings"] if g["gameday"] == min(x["gameday"] for x in games) else \
                nfl_pbp.play_ratings([p for p in plays_season if p["game_date"] < g["gameday"]], plays_prior)
            sides = {"home": nfl_pbp.side_inputs(pr, g["home_team"], g["away_team"], g["home_qb_id"], B["M"]),
                     "away": nfl_pbp.side_inputs(pr, g["away_team"], g["home_team"], g["away_qb_id"], B["M"])}
            mk = market(g)
            sim = nfl_pbp.simulate(sides, B["M"], n=n, seed=seed + int(g["gameday"].replace("-", "")) % 1000, hfa=B["M"]["hfa"])
            S = engine.summary(sim, mk["spread_home"], mk["total"])
            res = f(g["result"])
            recs.append({"game": g["game_id"], "week": w, "p_home": S["home_win"][0] / max(1 - S["tie"][0], 1e-9),
                         "mk_home": mk["p_home"], "won": None if res == 0 else float(res > 0),
                         "p_cover": S.get("home_cover", (None,))[0], "mk_cover": mk["p_cover"],
                         "covered": None if mk["spread_home"] is None or res + mk["spread_home"] == 0 else float(res + mk["spread_home"] > 0),
                         "p_over": S.get("over", (None,))[0], "mk_over": mk["p_over"],
                         "overed": None if mk["total"] is None or f(g["total"]) == mk["total"] else float(f(g["total"]) > mk["total"]),
                         "sim_total": S["total_mean"], "sim_margin": S["margin_mean"]})
    return {"records": recs, "metrics": metrics(recs)}
