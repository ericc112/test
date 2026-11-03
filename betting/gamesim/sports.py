"""One-game runner for the non-NFL engines (NBA and college basketball now; NHL, MLB and soccer plug in the same way).

python -m gamesim --sport nba --game <ESPN event id>

Same deliverable as the NFL report: 50,000 simulations at the sport's natural unit, win/cover/total probabilities
with Monte Carlo and structural error bars, fair odds, top scores and margins, a factor table, the market
comparison with the vig removed, the PLAY/PASS rule (error widened for line moves the model can't explain),
and the out-of-sample backtest that sets the structural error.
"""
from __future__ import annotations

import datetime as dt
import os

import numpy as np

from . import engine, nba, report
from .backtest import fair_american, no_vig
from .report import pct, pts

HERE = os.path.dirname(os.path.abspath(__file__))


def _season_start(lg: str) -> str:
    today = dt.date.today()
    y = today.year if today.month >= 9 else today.year - 1
    return f"{y}1018" if lg == "nba" else f"{y}1101"


def run_basketball(lg: str, game_id: str, sims: int = 50000, seed: int = 2026, out: str | None = None) -> str:
    path, minutes, periods, shot_clock = nba.SPORT[lg]
    yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y%m%d")
    games = nba.season_games(lg, _season_start(lg), yesterday)
    target = nba.parse(nba.data._json(f"https://site.api.espn.com/apis/site/v2/sports/{path}/summary?event={game_id}", f"{lg}_sum_{game_id}.json", 900))
    day = target["date"][:10]
    R = nba.calibrate(nba.ratings(games, day, minutes), games, day, minutes, shot_clock)
    H = nba.side(R, target["home"], target["away"], not target["neutral"])
    A = nba.side(R, target["away"], target["home"], False)
    ln = target["line"]
    t0 = dt.datetime.now()
    sim = nba.simulate(H, A, R, minutes, n=sims, seed=seed, shot_clock=shot_clock)
    t_sim = (dt.datetime.now() - t0).total_seconds()
    S = engine.summary(sim, ln["spread_home"], ln["total"])
    bt = nba.backtest(games, minutes, shot_clock, n=6000)
    M = bt["metrics"]
    rms = {k: M[k]["rms_vs_market"] for k in M}
    # factor table: neutral, then each factor alone
    avg = nba.side(R, "_", "_", False)
    base_p = lambda h, a, env=True: float((lambda s: (s["home"] > s["away"]).mean())(nba.simulate(h, a, R, minutes, n=sims, seed=seed, env=env, shot_clock=shot_clock)))
    rates = lambda x: {**avg, **{k: x[k] for k in ("to", "three", "p2", "p3", "ft_rate", "ftp", "orb")}}
    base = base_p(avg, dict(avg))
    full = float((sim["home"] > sim["away"]).mean())
    factors = [("Neutral baseline (two average teams, no home court)", base, 0.0),
               ("Ratings gap (turnovers, shot mix, 2P/3P%, FT trips, FT%, offensive rebounds)", None, None),
               ("Pace", None, None), ("Home court (calibrated to this season's home margin)", None, None),
               ("Shooting-luck variance (vs none)", None, None), ("Rest / back-to-back (no fitted coefficient)", base, 0.0),
               ("Player absences (no player layer for basketball yet)", base, 0.0), ("ALL FACTORS (full model)", full, full - base)]
    v1 = base_p(rates(nba.side(R, target["home"], target["away"], False)), rates(A))
    v2 = base_p({**avg, "pace_off": H["pace_off"]}, {**avg, "pace_off": A["pace_off"]})
    v3 = base_p(nba.side(R, "_", "_", True), dict(avg))
    v4 = full - base_p(H, A, env=False)
    factors[1], factors[2], factors[3] = (factors[1][0], v1, v1 - base), (factors[2][0], v2, v2 - base), (factors[3][0], v3, v3 - base)
    factors[4] = (factors[4][0], full, v4)
    # market and decision rule
    p_h = S["home_win"][0]
    nv_h = no_vig(ln["ml_home"], ln["ml_away"])
    nv_c = no_vig(ln["spread_home_odds"], ln["spread_away_odds"])
    nv_o = no_vig(ln["over_odds"], ln["under_odds"])
    marg, tot = sim["home"] - sim["away"], sim["home"] + sim["away"]
    news = {"win": 0.0, "cover": 0.0, "total": 0.0}
    moves = {}
    if ln.get("ml_home_open") is not None and ln.get("ml_away_open") is not None and nv_h is not None:
        moves["win"] = abs(nv_h - no_vig(ln["ml_home_open"], ln["ml_away_open"]))
    if ln.get("spread_home_open") is not None and ln["spread_home"] is not None:
        moves["cover"] = abs(float(np.mean(marg + ln["spread_home"] > 0)) - float(np.mean(marg + ln["spread_home_open"] > 0)))
    if ln.get("total_open") is not None and ln["total"] is not None:
        moves["total"] = abs(float(np.mean(tot > ln["total"])) - float(np.mean(tot > ln["total_open"])))
    for k, v in moves.items():
        news[k] = v / 2                       # no player layer: the whole move is unexplained news
    key = {"win": "home_win", "cover": "home_cover", "total": "over"}
    err = {k: report.total_error(S[key[k]][1], rms.get(k, 0.13), news[k]) for k in key if key[k] in S}
    sp, tl, home, away = ln["spread_home"], ln["total"], target["home"], target["away"]
    bets = [(f"{home} moneyline", p_h, nv_h, err["win"]), (f"{away} moneyline", 1 - p_h, None if nv_h is None else 1 - nv_h, err["win"])]
    if "home_cover" in S:
        pc = S["home_cover"][0]
        bets += [(f"{home} {sp:+g}", pc, nv_c, err["cover"]), (f"{away} {-sp:+g}", 1 - pc, None if nv_c is None else 1 - nv_c, err["cover"])]
    if "over" in S:
        po = S["over"][0]
        bets += [(f"Over {tl}", po, nv_o, err["total"]), (f"Under {tl}", 1 - po, None if nv_o is None else 1 - nv_o, err["total"])]
    dec = [(nm, pm, pk, e, report.decision(pm, pk, e)) for nm, pm, pk, e in bets]
    # render
    L = []
    w = L.append
    T = R["teams"]
    w(f"# {away} at {home}: {sims:,}-simulation {lg.upper()} model")
    w(f"\n{target['date'][:16].replace('T', ' ')}Z. Seed {seed}. Engine: **possession by possession** ({sim['stats']['possessions']:,} possessions, "
      f"{sim['possessions'].mean():.0f} per game, {sim['stats']['iterations']} vectorised steps, {t_sim:.1f} s).")
    if ln["ml_home"] is not None:
        w(f"\n**Market ({ln['provider']} via ESPN):** {home} {ln['ml_home']:+.0f} / {away} {ln['ml_away']:+.0f}"
          + (f"; spread {home} {sp:+g}" if sp is not None else "") + (f"; total {tl}" if tl is not None else "")
          + (f". Opened {home} {ln['ml_home_open']:+.0f}" if ln.get("ml_home_open") is not None else "")
          + (f", {ln['spread_home_open']:+g}" if ln.get("spread_home_open") is not None else "") + (f", {ln['total_open']}" if ln.get("total_open") is not None else "") + ".")
    w(f"\n## 1. Inputs\n\nRatings: opponent-adjusted ridge on this season's games before {day} ({R['n_games']} games; ESPN box scores). "
      f"Early-season samples are thin: every rate is shrunk toward the league by {nba.LAM:.0f} games.\n")
    w("| Team | Games | TO rate | 3PA share | 2P% | 3P% | FT trips/shot | FT% | OReb% | Pace effect |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for t, x in ((away, A), (home, H)):
        w(f"| {t} | {T.get(t, {}).get('games', 0)} | {x['to']:.3f} | {x['three']:.3f} | {x['p2']:.3f} | {x['p3']:.3f} | {x['ft_rate']:.3f} | {x['ftp']:.3f} | "
          f"{x['orb']:.3f} | {x['pace_off']:+.1f} |")
    w(f"\n(Rates are this matchup: offense + opponent's defense + home.) League pace {R['league']['pace']:.1f}. Calibrated to this season: "
      f"possession length ×{R['dur_scale']:.3f}, extra free throws on {100 * R['and1']:.0f}% of makes (and-ones, technicals, 3-shot fouls), "
      f"home court ×{R['home_scale']:.2f} → a league-average game scores {R['ppg_target']:.1f} a team with a {R['home_margin']:+.1f} home margin. "
      f"Shooting-luck sd: 2P {R['sd_p2']:.3f}, 3P {R['sd_p3']:.3f}; pace sd {R['sd_pace']:.1f}.")
    w("\n**Not modelled (flagged):** player minutes, injuries and lineups (no player layer yet), rest and back-to-backs, referees. "
      "Any line move the model can't explain widens the error bar.")
    w(f"\n## 2. Results ({sims:,} simulations)\n")
    w(f"| | {away} | {home} |\n|---|---|---|")
    w(f"| Win probability | {pct(1 - p_h)} ± {100 * S['home_win'][1]:.2f} (MC) ± {100 * err['win']:.1f} (total) | {pct(p_h)} ± {100 * S['home_win'][1]:.2f} (MC) ± {100 * err['win']:.1f} (total) |")
    w(f"| Fair moneyline | {fair_american(1 - p_h)} | {fair_american(p_h)} |")
    w(f"| Average points | {S['away_mean']:.1f} | {S['home_mean']:.1f} |")
    w(f"\nOvertime {pct(S['ot'][0])}. Margin mean {S['margin_mean']:+.1f}, sd {S['margin_sd']:.1f}. Total mean {S['total_mean']:.1f}, median {S['total_median']:.0f}, sd {S['total_sd']:.1f}.")
    if "home_cover" in S:
        w(f"\n{home} covers {sp:+g}: {pct(S['home_cover'][0])} ± {100 * err['cover']:.1f}.")
    if "over" in S:
        w(f" Over {tl}: {pct(S['over'][0])} ± {100 * err['total']:.1f}.")
    w("\nTop 10 margins: " + ", ".join(f"{m:+d} ({pct(p)})" for m, p in S["top_margins"]))
    w(f"\nTop 10 final scores ({home}–{away}): " + ", ".join(f"{h}–{a2} ({pct(p, 2)})" for h, a2, p in S["top_scores"]))
    w("\n## 3. Market comparison and decision rule\n\nPLAY only if edge ≥ 2 points and edge − 1.5 × total error > 0. Total error = √(MC² + backtest RMS gap² + "
      "(half the unexplained line move)²).\n")
    w("| Bet | Model | No-vig market | Edge | Total error | Edge − 1.5 × error | Verdict |\n|---|---|---|---|---|---|---|")
    for nm, pm, pk, e, d in dec:
        w(f"| {nm} | {pct(pm)} | {pct(pk)} | {pts(d['edge'])} | ±{100 * e:.1f} pts | {pts(d['margin'])} | **{d['verdict']}** |")
    w("\n## 4. Factor table\n\nHome win probability, each factor added alone to a neutral matchup (same seed).\n")
    w(f"| Factor | {home} win | vs neutral |\n|---|---|---|")
    for nm, v, d in factors:
        w(f"| {nm} | {pct(v)} | {pts(d)} |")
    w(f"\n## 5. Validation (out of sample)\n\nEvery game this season where both teams had 3+ earlier games, simulated from earlier games only "
      "(ratings and calibration rebuilt each day), against the closing no-vig lines.\n")
    w("| Market | Games | Brier: model | Brier: market | Log loss: model | Log loss: market | RMS gap |\n|---|---|---|---|---|---|---|")
    for k, v in M.items():
        w(f"| {k} | {v['n']} | {v['brier_model']:.4f} | {v['brier_market']:.4f} | {v['logloss_model']:.4f} | {v['logloss_market']:.4f} | {pct(v['rms_vs_market'])} |")
    best = max(dec, key=lambda d: d[4]["edge"] if d[4]["edge"] is not None else -9)
    w(f"\n## 6. Summary\n\n- **Headline:** {home} {pct(p_h)} to win (±{100 * err['win']:.1f}), fair {fair_american(p_h)}; no-vig market {pct(nv_h)}.")
    w(f"- **Largest edge:** {best[0]} {pts(best[4]['edge'])}, margin after the error rule {pts(best[4]['margin'])}.")
    w("- **Verdict:** " + "; ".join(f"{d[0]} **{d[4]['verdict']}**" for d in dec) + ".")
    w("- **Biggest uncertainty:** thin early-season ratings and no player layer (who plays, minutes). The backtest shows the model "
      f"{'well behind' if M.get('win', {}).get('brier_model', 1) > M.get('win', {}).get('brier_market', 0) else 'level with'} the market on winners.")
    w("- No locks and no promised returns.")
    txt = "\n".join(L) + "\n"
    path_out = out or os.path.join(HERE, "reports", f"{lg}_{game_id}.md")
    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    with open(path_out, "w") as f:
        f.write(txt)
    return txt


def run_hockey(game_id: str, sims: int = 50000, seed: int = 2026, out: str | None = None) -> str:
    from . import nhl
    yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y%m%d")
    y = dt.date.today().year if dt.date.today().month >= 9 else dt.date.today().year - 1
    games = nhl.season_games(f"{y}1005", yesterday)
    en = nhl.empty_net_rates(f"{y}1005", yesterday, max_games=120)
    target = nhl.parse(nhl.data._json(f"https://site.api.espn.com/apis/site/v2/sports/{nhl.PATH}/summary?event={game_id}", f"nhl_sum_{game_id}.json", 900))
    day = target["date"][:10]
    R = nhl.calibrate(nhl.ratings(games, day), en)
    home, away, ln = target["home"], target["away"], target["line"]
    gh, ga = R["starters"].get(home, {}), R["starters"].get(away, {})          # projected: each team's most recent starter
    H = nhl.side(R, home, away, True, ga.get("id"))
    A = nhl.side(R, away, home, False, gh.get("id"))
    t0 = dt.datetime.now()
    sim = nhl.simulate(H, A, R, en, n=sims, seed=seed)
    t_sim = (dt.datetime.now() - t0).total_seconds()
    sp, tl = ln["spread_home"], ln["total"]
    S = engine.summary(sim, sp, tl)
    bt = nhl.backtest(games, en, n=6000)
    M = bt["metrics"]
    rms = {k: M[k]["rms_vs_market"] for k in M}
    rms.setdefault("cover", rms.get("win", 0.1))
    avg = nhl.side(R, "_", "_", False)
    pw = lambda h, a, **kw: float((lambda s: (s["home"] > s["away"]).mean())(nhl.simulate(h, a, R, en, n=sims, seed=seed, **kw)))
    base = pw(avg, dict(avg), home_ice=False)
    full = float((sim["home"] > sim["away"]).mean())
    no_g = pw(nhl.side(R, home, away, True), nhl.side(R, away, home, False))
    factors = [("Neutral baseline (two average teams, no home ice)", base, 0.0)]
    for nm, v in (("Team ratings (shots for/against, finishing, power plays drawn and converted)",
                   pw(nhl.side(R, home, away, True), nhl.side(R, away, home, False), home_ice=False)),
                  ("Home ice (calibrated to last season's home margin)", pw(avg, dict(avg)))):
        factors.append((nm, v, v - base))
    factors += [("Projected goalies (vs league-average save %)", full, full - no_g),
                ("Finishing luck variance (vs none)", full, full - pw(H, A, env=False)),
                ("Rest / back-to-back (no fitted coefficient)", base, 0.0), ("Skater injuries (no player layer)", base, 0.0),
                ("ALL FACTORS (full model)", full, full - base)]
    p_h = S["home_win"][0]
    nv_h = no_vig(ln["ml_home"], ln["ml_away"])
    nv_c = no_vig(ln["spread_home_odds"], ln["spread_away_odds"])
    nv_o = no_vig(ln["over_odds"], ln["under_odds"])
    tot = sim["home"] + sim["away"]
    news = {"win": 0.0, "cover": 0.0, "total": 0.0}
    if ln.get("ml_home_open") is not None and ln.get("ml_away_open") is not None and nv_h is not None:
        news["win"] = news["cover"] = abs(nv_h - no_vig(ln["ml_home_open"], ln["ml_away_open"])) / 2
    if ln.get("total_open") is not None and tl is not None:
        news["total"] = abs(float(np.mean(tot > tl)) - float(np.mean(tot > ln["total_open"]))) / 2
    key = {"win": "home_win", "cover": "home_cover", "total": "over"}
    err = {k: report.total_error(S[key[k]][1], rms.get(k, 0.1), news[k]) for k in key if key[k] in S}
    bets = [(f"{home} moneyline", p_h, nv_h, err["win"]), (f"{away} moneyline", 1 - p_h, None if nv_h is None else 1 - nv_h, err["win"])]
    if "home_cover" in S and nv_c is not None:
        pc = S["home_cover"][0]
        bets += [(f"{home} {sp:+g} (puck line)", pc, nv_c, err["cover"]), (f"{away} {-sp:+g} (puck line)", 1 - pc, 1 - nv_c, err["cover"])]
    if "over" in S:
        po = S["over"][0]
        bets += [(f"Over {tl}", po, nv_o, err["total"]), (f"Under {tl}", 1 - po, None if nv_o is None else 1 - nv_o, err["total"])]
    dec = [(nm, pm, pk, e, report.decision(pm, pk, e)) for nm, pm, pk, e in bets]
    L, w = [], None
    w = L.append
    w(f"# {away} at {home}: {sims:,}-simulation NHL model")
    w(f"\n{target['date'][:16].replace('T', ' ')}Z. Seed {seed}. Engine: **event clock in 10-second ticks** ({sim['stats']['ticks']:,} ticks, "
      f"{sim['stats']['iterations']} vectorised steps, {t_sim:.1f} s).")
    if ln["ml_home"] is not None:
        w(f"\n**Market ({ln['provider']} via ESPN):** {home} {ln['ml_home']:+.0f} / {away} {ln['ml_away']:+.0f}; puck line {home} {sp:+g}; total {tl}"
          + (f". Opened {home} {ln['ml_home_open']:+.0f}" if ln.get("ml_home_open") is not None else "") + (f", {ln['total_open']}" if ln.get("total_open") is not None else "") + ".")
    w(f"\n## 1. Inputs\n\nRatings from this season's games before {day} ({R['n_games']} games, ESPN box scores), opponent-adjusted, each stat shrunk "
      f"by an empirical-Bayes prior: shots {R['lam']['shots']:.0f} games, finishing {R['lam']['fin']:.0f}, power plays drawn {R['lam']['ppo']:.0f}, "
      f"power-play % {R['lam']['ppc']:.0f}. Finishing and power-play % are mostly luck this early, so they sit near the league.\n")
    w("| Attack | Shots/60 | EV finishing × opposing goalie | PP chances | PP conversion | Faces goalie (PROJECTED) | Goalie Sv% (shrunk) |")
    w("|---|---|---|---|---|---|---|")
    for t, x, g in ((away, A, gh), (home, H, ga)):
        sv = R["goalies"].get(g.get("id"), {}).get("sv")
        w(f"| {t} | {x['shots']:.1f} | {x['fin']:.4f} | {x['ppo']:.2f} | {x['ppc']:.3f} | {g.get('name', 'unknown')} | {'n/a' if sv is None else f'{sv:.3f}'} |")
    w(f"\nGoalies are projected as each team's most recent starter, since no confirmed starters are published in the data. "
      f"Save % is shrunk with {nhl.GOALIE_K:.0f} shots of league average ({R['league']['sv']:.3f}). Empty net: "
      f"{en['for_per_min']:.3f} goals/min for and {en['against_per_min']:.3f} against with the goalie pulled ({en['minutes']:.0f} pulled minutes in "
      f"{en['games']} games, {en['source']}). Home ice: ×{R['home_mult']:.3f} on even-strength scoring, calibrated to {R['home_prior']['margin']:+.3f} "
      f"goals a game ({R['home_prior']['source']}, {R['home_prior']['games']} home games; flagged as last season's data; this season so far "
      f"{R['home_margin']:+.3f}). League {R['gpg']:.2f} goals a team; OT decided in overtime {pct(R['league']['ot_decided'])}, home shootout win {pct(R['league']['so_home'])}.")
    w("\n**Not modelled (flagged):** skater injuries and line combinations, rest and back-to-backs, score effects other than pulling the goalie.")
    w(f"\n## 2. Results ({sims:,} simulations)\n\n| | {away} | {home} |\n|---|---|---|")
    w(f"| Win probability (incl. OT/shootout) | {pct(1 - p_h)} ± {100 * S['home_win'][1]:.2f} (MC) ± {100 * err['win']:.1f} (total) | "
      f"{pct(p_h)} ± {100 * S['home_win'][1]:.2f} (MC) ± {100 * err['win']:.1f} (total) |")
    w(f"| Fair moneyline | {fair_american(1 - p_h)} | {fair_american(p_h)} |\n| Average goals | {S['away_mean']:.2f} | {S['home_mean']:.2f} |")
    w(f"\nOvertime {pct(S['ot'][0])}, shootout {pct(float(sim['shootout'].mean()))}. Total mean {S['total_mean']:.2f}, median {S['total_median']:.0f}, sd {S['total_sd']:.2f}.")
    if "home_cover" in S:
        w(f" {home} {sp:+g}: {pct(S['home_cover'][0])} ± {100 * err['cover']:.1f}.")
    if "over" in S:
        w(f" Over {tl}: {pct(S['over'][0])} ± {100 * err['total']:.1f}.")
    w("\nTop 10 margins: " + ", ".join(f"{m:+d} ({pct(p)})" for m, p in S["top_margins"]))
    w(f"\nTop 10 final scores ({home}–{away}): " + ", ".join(f"{h}–{a2} ({pct(p, 1)})" for h, a2, p in S["top_scores"]))
    w("\n## 3. Market comparison and decision rule\n\nPLAY only if edge ≥ 2 points and edge − 1.5 × total error > 0. Total error = √(MC² + backtest RMS gap² + "
      "(half the line move)²); there's no player layer, so any move is unexplained.\n")
    w("| Bet | Model | No-vig market | Edge | Total error | Edge − 1.5 × error | Verdict |\n|---|---|---|---|---|---|---|")
    for nm, pm, pk, e, d in dec:
        w(f"| {nm} | {pct(pm)} | {pct(pk)} | {pts(d['edge'])} | ±{100 * e:.1f} pts | {pts(d['margin'])} | **{d['verdict']}** |")
    w(f"\n## 4. Factor table\n\nHome win probability, each factor added alone to a neutral matchup (same seed).\n\n| Factor | {home} win | vs neutral |\n|---|---|---|")
    for nm, v, d in factors:
        w(f"| {nm} | {pct(v)} | {pts(d)} |")
    w("\n## 5. Validation (out of sample)\n\nEvery game this season where both teams had 4+ earlier games, simulated from earlier games only with the "
      "actual starting goalies, against the closing no-vig lines.\n")
    w("| Market | Games | Brier: model | Brier: market | Log loss: model | Log loss: market | RMS gap |\n|---|---|---|---|---|---|---|")
    for k, v in M.items():
        w(f"| {k} | {v['n']} | {v['brier_model']:.4f} | {v['brier_market']:.4f} | {v['logloss_model']:.4f} | {v['logloss_market']:.4f} | {pct(v['rms_vs_market'])} |")
    best = max(dec, key=lambda d: d[4]["edge"] if d[4]["edge"] is not None else -9)
    w(f"\n## 6. Summary\n\n- **Headline:** {home} {pct(p_h)} to win (±{100 * err['win']:.1f}), fair {fair_american(p_h)}; no-vig market {pct(nv_h)}.")
    w(f"- **Largest edge:** {best[0]} {pts(best[4]['edge'])}, margin after the error rule {pts(best[4]['margin'])}.")
    w("- **Verdict:** " + "; ".join(f"{d[0]} **{d[4]['verdict']}**" for d in dec) + ".")
    w("- **Biggest uncertainty:** the starting goalies are projected, not confirmed. Early-season ratings are thin, and the model trails the market in the backtest.")
    w("- No locks and no promised returns.")
    txt = "\n".join(L) + "\n"
    path_out = out or os.path.join(HERE, "reports", f"nhl_{game_id}.md")
    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    with open(path_out, "w") as f:
        f.write(txt)
    return txt
