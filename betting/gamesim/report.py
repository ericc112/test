"""Outputs and market comparison: probabilities with error bars, fair odds, distributions, factor table,
QB scenarios, the decision rule, and the out-of-sample validation."""
from __future__ import annotations

import numpy as np

from . import engine, ratings
from .backtest import fair_american, no_vig

EDGE_MIN = 0.02        # decision rule: edge over no-vig >= 2 points ...
ERR_MULT = 1.5         # ... and edge - 1.5 x total error > 0


def decision(p_model: float, p_market: float | None, err: float) -> dict:
    if p_market is None:
        return {"edge": None, "margin": None, "verdict": "PASS (no market price)"}
    edge = p_model - p_market
    margin = edge - ERR_MULT * err
    play = edge >= EDGE_MIN and margin > 0
    return {"edge": edge, "margin": margin, "verdict": "PLAY" if play else "PASS"}


def total_error(mc: float, structural: float, scenario: float = 0.0) -> float:
    """Monte Carlo error, structural error (backtest RMS vs the closing no-vig market, which already contains
    rating noise and everything the model leaves out) and starter-uncertainty spread, added in quadrature."""
    return float(np.sqrt(mc ** 2 + structural ** 2 + scenario ** 2))


def factor_table(inp: dict, model: dict, n: int, seed: int) -> list[tuple]:
    """Home win probability for a neutral matchup, then each factor added alone, then everything.
    Common random numbers (same seed) keep the differences from being Monte Carlo noise."""
    neutral = {"off_epa": 0.0, "off_sr": 0.0, "def_epa": 0.0, "def_sr": 0.0, "pace_ratio": 1.0, "qb_delta": 0.0}
    h, a = inp["home"], inp["away"]
    strip = lambda s, **kw: {**neutral, **kw}

    def p(home, away, hfa=False, wind=0.0, env=True):
        s = engine.simulate({"home": home, "away": away, "fg_wind_logit": wind}, model, n=n, seed=seed, hfa=hfa, env=env)
        S = engine.summary(s)
        return S["home_win"][0] / max(1 - S["tie"][0], 1e-9)
    base = p(dict(neutral), dict(neutral))
    rows = [("Neutral baseline (two average teams, no home field)", base, 0.0)]
    rat = lambda s: strip(s, off_epa=s["off_epa"], off_sr=s["off_sr"], def_epa=s["def_epa"], def_sr=s["def_sr"])
    tests = [
        ("Team ratings gap (offense/defense EPA and success, season QB mix)", p(rat(h), rat(a))),
        ("Starting QBs vs the season mix (injury/absence adjustment)", p(strip(h, qb_delta=h["qb_delta"]), strip(a, qb_delta=a["qb_delta"]))),
        ("Pace (seconds per play)", p(strip(h, pace_ratio=h["pace_ratio"]), strip(a, pace_ratio=a["pace_ratio"]))),
        ("Home-field advantage (fitted in the drive model)", p(dict(neutral), dict(neutral), hfa=True)),
        ("Weather (wind on field goals)", p(dict(neutral), dict(neutral), wind=inp.get("fg_wind_logit", 0.0))),
    ]
    for name, val in tests:
        rows.append((name, val, val - base))
    full = p({**h}, {**a}, hfa=True, wind=inp.get("fg_wind_logit", 0.0))
    no_env = p({**h}, {**a}, hfa=True, wind=inp.get("fg_wind_logit", 0.0), env=False)
    rows.append(("Correlated game environment (vs drawing drives independently)", full, full - no_env))
    rows.append(("Rest (both teams on 4 days)", base, 0.0))
    rows.append(("Travel / time zone (no fitted coefficient)", base, 0.0))
    rows.append(("Non-QB injuries (no per-player impact rating)", base, 0.0))
    rows.append(("ALL FACTORS (full model)", full, full - base))
    return rows


def param_se(sched_row: dict, plays_season: list[dict], plays_prior: list[dict], drives_all: list[dict], model: dict,
             qb_home: str, qb_away: str, B: int = 40, n: int = 4000, seed: int = 99) -> float:
    """Rating uncertainty: resample this season's earlier games with replacement, re-fit the ratings and QB
    ratings, re-simulate. Returns the bootstrap SD of the home win probability (Monte Carlo part removed)."""
    from .backtest import inputs_for
    rng = np.random.default_rng(seed)
    before = sched_row["gameday"]
    by_game = {}
    for p in plays_season:
        if p["game_date"] < before:
            by_game.setdefault(p["game_id"], []).append(p)
    gids = list(by_game)
    vals = []
    for b in range(B):
        pick = rng.choice(len(gids), len(gids), replace=True)
        boot = [pl for i in pick for pl in by_game[gids[i]]]
        inp = inputs_for(sched_row, boot, plays_prior, drives_all, qb_home=qb_home, qb_away=qb_away)
        s = engine.simulate({"home": inp["home"], "away": inp["away"]}, model, n=n, seed=seed + b)
        S = engine.summary(s)
        vals.append(S["home_win"][0] / max(1 - S["tie"][0], 1e-9))
    v = np.var(vals, ddof=1) - np.mean(vals) * (1 - np.mean(vals)) / n
    return float(np.sqrt(max(v, 0.0)))


def pct(x, d=1):
    return "n/a" if x is None else f"{100 * x:.{d}f}%"


def pts(x, d=1):
    return "n/a" if x is None else f"{100 * x:+.{d}f} pts"


NEUTRAL_PBP = {"comp": 0.0, "sack": 0.0, "int": 0.0, "ypc_mult": 1.0, "ypr_mult": 1.0, "pass_offset": 0.0}


def factor_table_pbp(sides: dict, sides_no_qb: dict, M: dict, n: int, seed: int, fg_wind_logit: float) -> list[tuple]:
    """Play-by-play engine: home win probability for a neutral matchup, then each factor added alone."""
    from . import nfl_pbp
    N = NEUTRAL_PBP

    def p(h, a, hfa=0.0, wind=0.0, env=True):
        s = nfl_pbp.simulate({"home": {**N, **h}, "away": {**N, **a}}, M, n=n, seed=seed, hfa=hfa, fg_wind_logit=wind, env=env)
        S = engine.summary(s)
        return S["home_win"][0] / max(1 - S["tie"][0], 1e-9)
    pick = lambda s, ks: {k: s[k] for k in ks}
    H, A = sides["home"], sides["away"]
    base = p({}, {})
    rows = [("Neutral baseline (two average teams, no home field)", base, 0.0)]
    tests = [("Passing matchup: QB vs pass defense (completion, sack, INT, yards per catch)", p(pick(H, ["comp", "sack", "int", "ypc_mult"]), pick(A, ["comp", "sack", "int", "ypc_mult"]))),
             ("Rushing matchup: yards per carry vs run defense", p(pick(H, ["ypr_mult"]), pick(A, ["ypr_mult"]))),
             ("Play-calling tendency (neutral pass rate)", p(pick(H, ["pass_offset"]), pick(A, ["pass_offset"]))),
             ("Home-field advantage (calibrated to the observed home margin)", p({}, {}, hfa=M["hfa"])),
             ("Weather (wind on field goals)", p({}, {}, wind=fg_wind_logit))]
    for name, v in tests:
        rows.append((name, v, v - base))
    full = p(H, A, hfa=M["hfa"], wind=fg_wind_logit)
    noqb = p(sides_no_qb["home"], sides_no_qb["away"], hfa=M["hfa"], wind=fg_wind_logit)
    rows.append(("Starting QBs (vs league-average QBs, same defenses)", full, full - noqb))
    rows.append(("Correlated game environment (vs plays drawn independently)", full, full - p(H, A, hfa=M["hfa"], wind=fg_wind_logit, env=False)))
    rows.append(("Rest (both teams on 4 days)", base, 0.0))
    rows.append(("Travel / time zone (no fitted coefficient)", base, 0.0))
    rows.append(("Non-QB injuries (no per-player impact rating)", base, 0.0))
    rows.append(("ALL FACTORS (full model)", full, full - base))
    return rows


def param_se_pbp(sched_row: dict, plays_season: list[dict], plays_prior: list[dict], M: dict, qb_home: str, qb_away: str,
                 B: int = 20, n: int = 4000, seed: int = 99) -> float:
    """Rating uncertainty for the play engine: resample this season's earlier games, re-fit play ratings, re-simulate."""
    from . import nfl_pbp
    rng = np.random.default_rng(seed)
    by_game = {}
    for p in plays_season:
        if p["game_date"] < sched_row["gameday"]:
            by_game.setdefault(p["game_id"], []).append(p)
    gids = list(by_game)
    vals = []
    for b in range(B):
        boot = [pl for i in rng.choice(len(gids), len(gids), replace=True) for pl in by_game[gids[i]]]
        pr = nfl_pbp.play_ratings(boot, plays_prior)
        sides = {"home": nfl_pbp.side_inputs(pr, sched_row["home_team"], sched_row["away_team"], qb_home, M),
                 "away": nfl_pbp.side_inputs(pr, sched_row["away_team"], sched_row["home_team"], qb_away, M)}
        S = engine.summary(nfl_pbp.simulate(sides, M, n=n, seed=seed + b, hfa=M["hfa"]))
        vals.append(S["home_win"][0] / max(1 - S["tie"][0], 1e-9))
    v = np.var(vals, ddof=1) - np.mean(vals) * (1 - np.mean(vals)) / n
    return float(np.sqrt(max(v, 0.0)))
