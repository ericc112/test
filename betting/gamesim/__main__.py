"""python -m gamesim --game 2026_09_JAX_BAL [--sims 50000] [--seed 2026] [--qb-home NAME] [--qb-away NAME]

Runs the whole pipeline for one game and writes a Markdown report (gamesim/reports/<game>.md):
inputs with sources, 50,000-simulation results with error bars, market comparison and decision rule,
factor table, starter scenarios, and the out-of-sample backtest.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import time

import numpy as np

from . import backtest, data, drives, engine, players, report
from .backtest import fair_american
from .report import pct, pts

HERE = os.path.dirname(os.path.abspath(__file__))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gamesim")
    ap.add_argument("--game", default="2026_09_JAX_BAL", help="nflverse game_id (NFL) or ESPN event id (other sports)")
    ap.add_argument("--sport", default="nfl", choices=("nfl", "nba", "ncaab", "nhl"))
    ap.add_argument("--sims", type=int, default=50000)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--qb-home", help="override the projected home starter (name as on the depth chart)")
    ap.add_argument("--qb-away")
    ap.add_argument("--bootstrap", type=int, default=40)
    ap.add_argument("--engine", choices=("pbp", "drive"), default="pbp", help="play-by-play (default) or drive-by-drive")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.sport != "nfl":
        from . import sports
        txt = (sports.run_hockey(a.game, a.sims, a.seed, a.out) if a.sport == "nhl"
               else sports.run_basketball(a.sport, a.game, a.sims, a.seed, a.out))
        print(txt)
        return

    sched = data.schedule()
    row = next(g for g in sched if g["game_id"] == a.game)
    season = int(row["season"])
    week = int(row["week"])
    P = data.pbp(season)
    P0 = data.pbp(season - 1)
    dk = data.espn_game(row["espn"]) if row["espn"] else None
    home, away = row["home_team"], row["away_team"]
    ctx = players.context(row, dk["kickoff"] if dk else row["gameday"] + "T17:00:00Z")

    # wind by game for the field-goal model (domes and closed roofs count as calm)
    wind = {g["game_id"]: (0.0 if g["roof"] in ("dome", "closed") else data.f(g["wind"], 0.0) or 0.0)
            for g in sched if g["season"] in (str(season), str(season - 1))}
    allp = P0 + P
    drives_all = drives.build_drives(allp)
    model = drives.fit(allp, drives_all, before=row["gameday"], wind=wind)
    wx = ctx.get("weather")
    fgw = model["fg_wind"]
    fg_wind_logit = fgw["coef_per_10mph"] * (wx["wind_mph"] - fgw["mean_wind"]) / 10 if wx else 0.0

    # starters: projected from the depth chart unless overridden
    starters = {}
    for side, team, override in (("home", home, a.qb_home), ("away", away, a.qb_away)):
        q = players.starting_qb(season, team)
        if override:
            q = {**q, "name": override, "gsis": players.gsis_for(season, team, override), "status": "override (--qb)",
                 "source": "command line"}
        starters[side] = q
    inp = backtest.inputs_for(row, P, P0, drives_all, qb_home=starters["home"]["gsis"], qb_away=starters["away"]["gsis"],
                              fg_wind_logit=fg_wind_logit)

    spread_home = dk["spread_home"] if dk and dk["spread_home"] is not None else -data.f(row["spread_line"], 0)
    total = dk["total"] if dk and dk["total"] is not None else data.f(row["total_line"])
    pbp = None
    if a.engine == "pbp":
        from . import nfl_pbp
        B = nfl_pbp.build(P, P0, sched, row["gameday"], wind=wind)
        Mp, prt = B["M"], B["ratings"]
        mk_sides = lambda qh, qa: {"home": nfl_pbp.side_inputs(prt, home, away, qh, Mp), "away": nfl_pbp.side_inputs(prt, away, home, qa, Mp)}
        sides = mk_sides(starters["home"]["gsis"], starters["away"]["gsis"])
        ts = time.time()
        sim = nfl_pbp.simulate(sides, Mp, n=a.sims, seed=a.seed, hfa=Mp["hfa"], fg_wind_logit=fg_wind_logit)
        t_sim = time.time() - ts
        pbp = {"M": Mp, "sides": sides, "mk_sides": mk_sides, "stats": sim["stats"], "plays": float(sim["plays"].mean())}
    else:
        ts = time.time()
        sim = engine.simulate({"home": inp["home"], "away": inp["away"], "fg_wind_logit": fg_wind_logit}, model, n=a.sims, seed=a.seed)
        t_sim = time.time() - ts
    S = engine.summary(sim, spread_home, total)

    # validation: replay this season's earlier weeks (from week 4) out of sample
    bt = (backtest.run_pbp if pbp else backtest.run)(sched, P, P0, str(season), list(range(4, week)), n=10000)
    M = bt["metrics"]
    rms = backtest.pooled_rms(M, backtest.prior_metrics("pbp" if pbp else "drive"))   # + last season's full backtest
    info = backtest.info_weights(bt["records"] + backtest.prior_records("pbp" if pbp else "drive"))

    # starter scenarios for both teams: each of the top three QBs on the depth chart
    scen = []
    for side, team in (("home", home), ("away", away)):
        for name in players.starting_qb(season, team)["depth"][:3]:
            g = players.gsis_for(season, team, name)
            kw = {"qb_home": g, "qb_away": starters["away"]["gsis"]} if side == "home" else {"qb_home": starters["home"]["gsis"], "qb_away": g}
            i2 = backtest.inputs_for(row, P, P0, drives_all, fg_wind_logit=fg_wind_logit, **kw)
            if pbp:
                sd2 = pbp["mk_sides"](kw["qb_home"], kw["qb_away"])
                s2 = engine.summary(nfl_pbp.simulate(sd2, pbp["M"], n=a.sims, seed=a.seed, hfa=pbp["M"]["hfa"], fg_wind_logit=fg_wind_logit), spread_home, total)
            else:
                s2 = engine.summary(engine.simulate({"home": i2["home"], "away": i2["away"], "fg_wind_logit": fg_wind_logit}, model,
                                                    n=a.sims, seed=a.seed), spread_home, total)
            scen.append({"team": team, "qb": name, "is_starter": name == starters[side]["name"], "qb_epa": i2[side]["qb"]["starter_epa"],
                         "qb_db": i2[side]["qb"]["starter_db"], "delta": i2[side]["qb_delta"],
                         "p_home": s2["home_win"][0] / max(1 - s2["tie"][0], 1e-9), "cover": s2["home_cover"][0], "over": s2["over"][0],
                         "total_mean": s2["total_mean"]})
    rng_of = lambda k: (max(x[k] for x in scen if x["team"] == home) - min(x[k] for x in scen if x["team"] == home)) / 4
    scen_sd = {"win": rng_of("p_home"), "cover": rng_of("cover"), "total": rng_of("over")}

    if pbp:
        p_se = report.param_se_pbp(row, P, P0, pbp["M"], starters["home"]["gsis"], starters["away"]["gsis"], B=min(a.bootstrap, 20))
        factors = report.factor_table_pbp(pbp["sides"], pbp["mk_sides"](None, None), pbp["M"], a.sims, a.seed, fg_wind_logit)
    else:
        p_se = report.param_se(row, P, P0, drives_all, model, starters["home"]["gsis"], starters["away"]["gsis"], B=a.bootstrap)
        factors = report.factor_table(inp, model, a.sims, a.seed)

    # market comparison and the decision rule
    tie = S["tie"][0]
    p_h = S["home_win"][0] / max(1 - tie, 1e-9)
    mc_w = S["home_win"][1] / max(1 - tie, 1e-9)
    err_w = report.total_error(mc_w, rms.get("win", 0.12), scen_sd["win"])
    err_c = report.total_error(S["home_cover"][1], rms.get("cover", 0.12), scen_sd["cover"])
    err_t = report.total_error(S["over"][1], rms.get("total", 0.10), scen_sd["total"])
    nv_h = no_vig_h = backtest.no_vig(dk["ml_home"], dk["ml_away"]) if dk else None
    nv_c = backtest.no_vig(dk["spread_home_odds"], dk["spread_away_odds"]) if dk else None
    nv_o = backtest.no_vig(dk["over_odds"], dk["under_odds"]) if dk else None
    pc, po = S["home_cover"][0], S["over"][0]
    bets = [(f"{home} moneyline", p_h, nv_h, err_w), (f"{away} moneyline", 1 - p_h, None if nv_h is None else 1 - nv_h, err_w),
            (f"{home} {spread_home:+g}", pc, nv_c, err_c), (f"{away} {-spread_home:+g}", 1 - pc, None if nv_c is None else 1 - nv_c, err_c),
            (f"Over {total}", po, nv_o, err_t), (f"Under {total}", 1 - po, None if nv_o is None else 1 - nv_o, err_t)]
    dec = [(name, pm, pk, d["err_used"], d) for name, pm, pk, e in bets
           for d in [report.decision(pm, pk, e, info[report.market_of(name)]["b_lo"])]]

    # Missing input: the market has moved on news the model can't see (open vs current DraftKings line).
    # The part of that move the model's own starter scenarios don't explain widens the error bar (sd = half of it).
    home_rows = [x for x in scen if x["team"] == home]
    news = {"win": 0.0, "cover": 0.0, "total": 0.0, "detail": "no opening line"}
    if dk and dk.get("ml_home_open") is not None and dk.get("ml_away_open") is not None:
        mv_w = abs(nv_h - backtest.no_vig(dk["ml_home_open"], dk["ml_away_open"]))
        marg, tot = sim["home"] - sim["away"], sim["home"] + sim["away"]
        sp_o = dk.get("spread_home_open")
        mv_c = abs(float(np.mean(marg + spread_home > 0)) - float(np.mean(marg + sp_o > 0))) if sp_o is not None else 0.0
        t_o = dk.get("total_open")
        mv_t = abs(float(np.mean(tot > total)) - float(np.mean(tot > t_o))) if t_o is not None else 0.0
        ex = lambda k: max(x[k] for x in home_rows) - min(x[k] for x in home_rows)
        news = {"win": max(0.0, mv_w - ex("p_home")) / 2, "cover": max(0.0, mv_c - ex("cover")) / 2, "total": max(0.0, mv_t - ex("over")) / 2,
                "moves": {"win": mv_w, "cover": mv_c, "total": mv_t}, "explained": {"win": ex("p_home"), "cover": ex("cover"), "total": ex("over")},
                "open": {"ml_home": dk["ml_home_open"], "ml_away": dk["ml_away_open"], "spread_home": sp_o, "total": t_o}}
    errw = {"win": report.total_error(mc_w, rms.get("win", 0.12), scen_sd["win"]) ** 2, "cover": err_c ** 2, "total": err_t ** 2}
    wide = {k: float(np.sqrt(errw[k] + news[k] ** 2)) for k in ("win", "cover", "total")}
    which = ["win", "win", "cover", "cover", "total", "total"]
    dec_wide = [(name, pm, pk, d2["err_used"], d2) for (name, pm, pk, e, d), k in zip(dec, which)
                for d2 in [report.decision(pm, pk, wide[k], info[k]["b_lo"])]]

    out = render(a, row, dk, ctx, model, inp, starters, S, p_h, mc_w, err_w, err_c, err_t, rms, scen, scen_sd, p_se, factors,
                 dec, M, spread_home, total, wx, fg_wind_logit, season, home, away, time.time() - t0, t_sim, news, dec_wide, wide, pbp)
    path = a.out or os.path.join(HERE, "reports", f"{a.game}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(out)
    print(out)
    print(f"\n[report written to {path}]")


def render(a, row, dk, ctx, model, inp, starters, S, p_h, mc_w, err_w, err_c, err_t, rms, scen, scen_sd, p_se, factors, dec, M,
           spread_home, total, wx, fg_wind_logit, season, home, away, secs, t_sim, news, dec_wide, wide, pbp=None):
    L = []
    w = L.append
    R = inp["ratings"]["teams"]
    w(f"# {away} at {home}: {a.sims:,}-simulation game model")
    eng = "play-by-play" if pbp else "drive-by-drive"
    w(f"\n{row['gameday']} {row['gametime']} ET, {row['stadium']} ({row['roof']}, {row['surface']}). Seed {a.seed}. Engine: **{eng}**. "
      f"Run {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}; {secs:.0f} s in total, of which the {a.sims:,} simulations took {t_sim:.1f} s"
      + (f" ({pbp['stats']['snaps']:,} snaps, {pbp['plays']:.0f} per game, {pbp['stats']['iterations']} vectorised steps)." if pbp else "."))
    if dk:
        w(f"\n**Market ({dk['provider']} via ESPN, pulled {dk['pulled']}):** {home} {dk['ml_home']:+.0f} / {away} {dk['ml_away']:+.0f}; "
          f"spread {home} {spread_home:+g} ({dk['spread_home_odds']:+.0f}) / {away} {-spread_home:+g} ({dk['spread_away_odds']:+.0f}); "
          f"total {total} (o {dk['over_odds']:+.0f} / u {dk['under_odds']:+.0f}).")

    w("\n## 1. Inputs")
    w(f"\nTeam ratings: ridge-adjusted for opponent, {season} plays before {row['gameday']} only "
      f"({inp['ratings']['n_plays']:,} plays, garbage time out). EPA per play; defense = EPA allowed (negative is good).\n")
    w("| Team | Off EPA/play | Def EPA/play | Off success | Def success | Dropback share | Neutral sec/play | Plays/game |")
    w("|---|---|---|---|---|---|---|---|")
    for side in ("away", "home"):
        t = inp[side]
        r = R.get(t["team"], {})
        w(f"| {t['team']} | {t['off_epa']:+.3f} | {t['def_epa']:+.3f} | {t['off_sr']:+.3f} | {t['def_sr']:+.3f} | {t['db_share']:.0%} | "
          f"{inp['pace']['teams'].get(t['team'], inp['pace']['league']):.1f} | {r.get('plays_per_game', 0):.1f} |")
    w(f"\nLeague neutral pace {inp['pace']['league']:.1f} s/play. Home field enters through the drive model "
      f"(home coefficient fitted on {', '.join(model['seasons'])} drives).")
    w("\n**Starting quarterbacks**\n")
    w("| Team | Starter | Status | Source | Starter EPA/dropback (n) | Season QB mix | Adjustment to offense |")
    w("|---|---|---|---|---|---|---|")
    for side in ("away", "home"):
        q, t = starters[side], inp[side]
        qd = t["qb"]
        mix = ", ".join(f"{k} {v:.0%}" for k, v in sorted(qd["shares"].items(), key=lambda x: -x[1]) if v >= 0.01)
        se = "n/a" if qd["starter_epa"] is None else f"{qd['starter_epa']:+.3f} ({qd['starter_db']:.0f})"
        w(f"| {t['team']} | {q['name']} | **{q['status'].upper()}** | {q['source']} | {se} | {qd['mix']:+.3f} ({mix}) | {t['qb_delta']:+.3f} EPA/play |")
    w("\nQB ratings borrow last season's dropbacks at half weight (flagged: the only place a prior season feeds a rating).")
    w("\n**Absences** (status from the named source; adjustment in EPA/play)\n")
    w("| Team | Player | Pos | Status | Injury | Source | Adjustment |")
    w("|---|---|---|---|---|---|---|")
    for side in ("away", "home"):
        for x in players.absences(season, inp[side]["team"], dk["injuries"] if dk else []):
            adj = "via QB rating" if x["pos"] == "QB" else "0 (no per-player impact rating; flagged)"
            w(f"| {inp[side]['team']} | {x['name']} | {x['pos']} | {x['status']} | {x['detail'] or ''} | {x['source']} | {adj} |")
    w("\n**Rotation players** (average snap share, last three games, nflverse/PFR). In the model through the team ratings; "
      "the QB through his own rating. No coverage-matchup data is available, so matchups are not modelled.\n")
    for side in ("away", "home"):
        st = players.snap_table(season, inp[side]["team"])
        off = ", ".join(f"{s['player']} {s['pos']} {s['off_pct']:.0%}" for s in st if s["off_pct"] >= 0.3)[:900]
        de = ", ".join(f"{s['player']} {s['pos']} {s['def_pct']:.0%}" for s in st if s["def_pct"] >= 0.3)[:900]
        w(f"- **{inp[side]['team']} offense:** {off}\n- **{inp[side]['team']} defense:** {de}")
    w("\n**Context**\n")
    w(f"- Rest: {home} {ctx['rest_home']:.0f} days, {away} {ctx['rest_away']:.0f} days ({ctx['rest_source']}). Equal, so no effect; the model has no fitted rest coefficient.")
    w(f"- Travel: {ctx['travel_miles']} miles, same time zone ({ctx['travel_source']}). No fitted travel coefficient; part of the average home edge.")
    w("- Altitude: Baltimore is at sea level. No adjustment.")
    if wx:
        w(f"- Weather at kickoff ({wx['source']}, pulled {wx['pulled']}): wind {wx['wind_mph']} mph (gusts {wx['gust_mph']}), precipitation "
          f"{wx['precip_mm']} mm (chance {wx['precip_prob']}%), {wx['temp_f']}°F. FG make model: {model['fg_wind']['coef_per_10mph']:+.3f} logit per 10 mph "
          f"(fitted on {model['fg_wind']['n_with_wind']} outdoor attempts) gives {fg_wind_logit:+.3f} logit here. Wind on passing is not modelled.")
    else:
        w("- Weather: **missing** (forecast unavailable). No adjustment; error bar not reduced.")
    w(f"- Referee: {ctx['referee'] or '**missing** (crew not in the schedule data yet)'}. No adjustment.")

    w("\n## 2. Engine")
    if pbp:
        Mp, sd = pbp["M"], pbp["sides"]
        w(f"\nEvery snap, with down, distance, spot, clock and timeouts. Fitted on {Mp['n_plays']:,} scrimmage plays and {Mp['n_fourth']:,} fourth downs "
          f"before the game: run or pass call, 4th-down go/punt/FG, pass result (complete, incomplete, INT, sack), yards from real plays of the same down "
          f"group, distance and spot (inside the 20 as a share of the distance to goal), penalties ({100 * Mp['pen']['p']:.1f}% of snaps), seconds to the "
          f"next snap by result and tempo, timeouts, the two-minute warning, punts, kickoffs, onside kicks (recovered {100 * Mp['onside_rate']:.0f}% of "
          f"{Mp['n_onside']}), FGs by distance and wind, XP {100 * Mp['xp']:.1f}%, two-point {100 * Mp['two']:.1f}%. Game environment per simulation: "
          f"each offense's yards shock (sd {Mp['yard_sd']:.3f}, also tilting its completion rate). Home edge {100 * Mp['hfa']:.1f}% in yards, calibrated "
          f"to the observed {Mp['home_margin_target']:+.2f}-point home margin.\n")
        w("| Offense | QB in data | Completion (logit vs league) | Sack | INT | Yards per catch × | Yards per carry × | Pass tendency (logit) |")
        w("|---|---|---|---|---|---|---|---|")
        for side, team in (("away", away), ("home", home)):
            x = sd[side]
            w(f"| {team} ({starters[side]['name']}) | {'yes' if x['qb_known'] else 'no (league average)'} | {x['comp']:+.3f} | {x['sack']:+.3f} | {x['int']:+.3f} | "
              f"{x['ypc_mult']:.3f} | {x['ypr_mult']:.3f} | {x['pass_offset']:+.3f} |")
    w(f"\n{'For reference, the drive model (`--engine drive`): ' if pbp else ''}Drive by drive with the game clock. The drive model covers TD, FG try, punt, turnover, downs and safety, fitted on "
      f"{model['n_drives']:,} drives. FG makes come from distance and wind ({model['n_fga']:,} attempts). XP {model['xp']:.1%}, two-point "
      f"{model['two']:.1%}, return TD on {model['p_def_td']:.1%} of turnovers. Shared game environment per sim: offense shock "
      f"sd {model['sigma_game']:.3f} EPA/play, pace shock sd {model['pace_sd']:.3f} (log). Endgame: kneel-downs, two-minute and "
      f"4th-quarter tempo, a two-point chart, and 2025 regular-season overtime (10 minutes, both teams get a possession).")

    w(f"\n## 3. Results ({a.sims:,} simulations)")
    se_line = lambda p, se, e: f"{pct(p)} ± {100 * se:.2f} (MC) ± {100 * e:.1f} (total)"
    w(f"\n| | {away} | {home} |\n|---|---|---|")
    w(f"| Win probability (ties excluded, as books grade) | {se_line(1 - p_h, mc_w, err_w)} | {se_line(p_h, mc_w, err_w)} |")
    w(f"| Fair moneyline | {fair_american(1 - p_h)} | {fair_american(p_h)} |")
    w(f"| Average points | {S['away_mean']:.1f} | {S['home_mean']:.1f} |")
    w(f"\nTie {pct(S['tie'][0], 2)}; overtime {pct(S['ot'][0])}. Monte Carlo SE on the win probability is ±{100 * mc_w:.2f} points "
      f"(about 0.22 at 50,000 runs). Rating bootstrap SD is ±{100 * p_se:.1f} points.")
    w(f"\n**Margin** ({home} minus {away}): mean {S['margin_mean']:+.1f}, sd {S['margin_sd']:.1f}. {home} covers {spread_home:+g}: "
      f"{pct(S['home_cover'][0])} ± {100 * err_c:.1f} (push {pct(S['spread_push'], 2)}).")
    w("\nTop 10 margins: " + ", ".join(f"{m:+d} ({pct(p)})" for m, p in S["top_margins"]))
    w(f"\nTop 10 final scores ({home}–{away}): " + ", ".join(f"{h}–{aw} ({pct(p, 2)})" for h, aw, p in S["top_scores"]))
    w(f"\n**Total:** mean {S['total_mean']:.1f}, median {S['total_median']:.0f}, sd {S['total_sd']:.1f}. Over {total}: "
      f"{pct(S['over'][0])} ± {100 * err_t:.1f}.")
    w("\nPlayer props are out of scope here. The kit's `edge nfl` simulator prices them from correlated draws.")

    w("\n## 4. Market comparison and decision rule")
    w(f"\nRule: PLAY only if the edge over the no-vig price is at least 2 points **and** the edge minus 1.5 × total error is above zero.\n")
    w("| Bet | Model | No-vig market | Edge | Total error | Edge − 1.5 × error | Verdict |")
    w("|---|---|---|---|---|---|---|")
    for name, pm, pk, e, d in dec:
        w(f"| {name} | {pct(pm)} | {pct(pk)} | {pts(d['edge'])} | ±{100 * e:.1f} pts | {pts(d['margin'])} | **{d['verdict']}** |")
    w("\nTotal error = √(MC² + structural² + starter spread²). Structural = out-of-sample RMS gap to the closing no-vig market "
      f"in this season's backtest (win {pct(rms.get('win'))}, cover {pct(rms.get('cover'))}, total {pct(rms.get('total'))}). "
      f"Starter spread = range across the three depth-chart QBs ÷ 4 (win {pct(scen_sd['win'])}).")

    if news.get("moves"):
        o = news["open"]
        w(f"\n**Missing input: news the model can't see.** DraftKings opened {home} {o['ml_home']:+.0f} / {away} {o['ml_away']:+.0f}, "
          f"spread {home} {o['spread_home']:+g}, total {o['total']}. Now it's {home} {dk['ml_home']:+.0f}, {spread_home:+g}, {total}. "
          f"That's a {pct(news['moves']['win'])} swing in no-vig win probability. The model's three {home} starters explain "
          f"{pct(news['explained']['win'])} of it, so the rest is information the model doesn't have (who starts, health, practice reports). "
          f"As your rule says, the error bar widens rather than the model guessing: sd = half the unexplained move "
          f"(win {pct(news['win'])}, cover {pct(news['cover'])}, total {pct(news['total'])}).\n")
        w("| Bet | Model | No-vig market | Edge | Widened error | Edge − 1.5 × error | Verdict |")
        w("|---|---|---|---|---|---|---|")
        for name, pm, pk, e, d in dec_wide:
            w(f"| {name} | {pct(pm)} | {pct(pk)} | {pts(d['edge'])} | ±{100 * e:.1f} pts | {pts(d['margin'])} | **{d['verdict']}** |")
    if M.get("total") and M["total"]["brier_model"] > 0.25:
        w(f"\nTotals: the model's out-of-sample Brier on totals ({M['total']['brier_model']:.4f}) is worse than a coin flip (0.2500), and "
          f"it runs {pts(M['total']['mean_vs_market'])} toward overs against the market. It has shown no skill on totals.")

    w("\n## 5. Factor table")
    w("\nHome win probability with each factor added alone to a neutral matchup (same seed for every run).\n")
    w(f"| Factor | {home} win | vs neutral |\n|---|---|---|")
    for name, val, d in factors:
        w(f"| {name} | {pct(val)} | {pts(d)} |")
    w("\nThe factors interact through the clock and score, so the rows don't add exactly to the full model.")

    w("\n## 6. Starter scenarios")
    w("\nEach of the top three QBs on each depth chart, the other team's projected starter held fixed.\n")
    w(f"| Team | QB | EPA/dropback (n) | Drive-model EPA/play adjustment | {home} win | {home} cover {spread_home:+g} | Over {total} | Mean total |")
    w("|---|---|---|---|---|---|---|---|")
    for x in scen:
        se = "no data" if x["qb_epa"] is None else f"{x['qb_epa']:+.3f} ({x['qb_db']:.0f})"
        w(f"| {x['team']} | {x['qb']}{' (projected)' if x['is_starter'] else ''} | {se} | {x['delta']:+.3f} | {pct(x['p_home'])} | "
          f"{pct(x['cover'])} | {pct(x['over'])} | {x['total_mean']:.1f} |")

    w("\n## 7. Validation (out of sample)")
    wk = int(row["week"])
    w(f"\nThis season's weeks 4–{wk - 1}, each game simulated using only data from before it, against the closing "
      "no-vig lines in the nflverse schedule. "
      + ("The play ratings' shrinkage (150 plays) is a fixed prior, not tuned on any games.\n" if pbp else
         "Rating shrinkage was tuned on the previous season, never on these games.\n"))
    w("| Market | Games | Brier: model | Brier: market | Log loss: model | Log loss: market | RMS gap to market |")
    w("|---|---|---|---|---|---|---|")
    for k, v in M.items():
        w(f"| {k} | {v['n']} | {v['brier_model']:.4f} | {v['brier_market']:.4f} | {v['logloss_model']:.4f} | {v['logloss_market']:.4f} | {pct(v['rms_vs_market'])} |")
    if "win" in M:
        w("\nCalibration (home win): " + "; ".join(f"model {pct(c[3], 0)} → actual {pct(c[4], 0)} (n={c[2]})" for c in M["win"]["calibration"]))
    w("\n## 8. Missing or flagged inputs")
    w("\n- Starting QBs are **projected** from the depth chart. The official inactive list comes 90 minutes before kickoff.")
    w("- No per-player impact ratings for non-QBs, and no coverage matchups: absences other than QB get 0, covered by the structural error.")
    w("- No fitted rest, travel or referee terms. Rest and time zone are equal here; the referee crew isn't published yet.")
    w("- Onside kicks and timeouts are not modelled. Wind affects field goals only.")
    w(f"- The drive model borrows {int(season) - 1} drives (link function only); team ratings are {season}-only.")
    w(f"\n## 9. Summary\n")
    best = max(dec, key=lambda d: (d[4]["edge"] or -1))
    hp = dec[0]
    w(f"- **Headline:** {home} {pct(p_h)} to win (±{100 * err_w:.1f} backtest error; ±{100 * wide['win']:.1f} widened for the missing input), fair moneyline {fair_american(p_h)} / {away} {fair_american(1 - p_h)}. "
      f"No-vig market: {home} {pct(hp[2])}.")
    w(f"- **Edge:** {hp[0]} {pts(hp[4]['edge'])}. Largest edge on the board: {best[0]}, {pts(best[4]['edge'])}, "
      f"margin after the error rule {pts(best[4]['margin'])}.")
    w(f"- **Verdict, backtest error only:** " + ("; ".join(f"{d[0]} {d[4]['verdict']}" for d in dec)) + ".")
    final = dec_wide if news.get("moves") else dec
    w(f"- **Verdict, error widened for the missing input (the one that counts):** " + ("; ".join(f"{d[0]} **{d[4]['verdict']}**" for d in final)) + ".")
    w(f"- **Biggest uncertainty:** {home}'s starting QB. The three depth-chart QBs move {home}'s win probability "
      f"from {pct(min(x['p_home'] for x in scen if x['team'] == home))} to {pct(max(x['p_home'] for x in scen if x['team'] == home))}. "
      + (f"The market's move from {home} {news['open']['spread_home']:+g} to {spread_home:+g} says it knows more about that than the model does."
         if news.get("open") else "The market may know more about it than the model does."))
    w("- No locks and no promised returns. This is a probability with its error bar.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
