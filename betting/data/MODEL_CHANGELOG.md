# NBA prop pricing: model changelog

Every change to the published NBA pricing logic is recorded here with its evidence and its rollback.
Logic versions live in `data/nba_model.json`; `python -m edge.nba_model status | report | promote | rollback`.

## 2026-11-04: v2 registered as SHADOW (not promoted)
- **Published logic stays v1.** v2 scores every board alongside v1 and is logged to `data/nba_shadow/`, never published.
- **v2 contents:**
  - simulation: minutes shared as c × minutes^1.0 (was ^0.8), shared role swing ρ = 0.8;
  - residual bias: per stat × top five / bench table, shrunk toward the stat-wide value;
  - blend: model 0.2 / market 0.8 / history 0, no intercept; a missing DraftKings price counts as 50%;
  - selected side capped at 70%;
  - gates derived on held-out legs: High ≥ 62%, Medium ≥ 54%, spread ≤ 16 pts, no history minimum, High needs a market price;
  - ENTRY needs p − break-even > 1 standard error;
  - whole-line market push excluded.
- **Backtest evidence** (walk-forward, 4,801 held-out legs, Oct 25 – Nov 2, live-like availability): picked-side log loss 0.6908 → 0.6863, Brier 0.2488 → 0.2466. Over-side log loss vs v1 −0.0045 (95% CI −0.0065 to −0.0024); vs DraftKings alone −0.0012 (CI −0.0026 to +0.0002). Full numbers: `data/nba_bt/final_eval.json`.
- **Promotion rule:** 200+ graded live shadow legs or 14 days, better on log loss AND label calibration. Checked daily by the scheduled run.

## 2026-11-04: process changes, effective immediately (they don't change any published probability)
- **verify:**
  - ENTRY legs (action `bet`) must reprice and recount within 2 points;
  - calibration-drift WARN on the trailing 50 published legs;
  - tilt monitor: raw gap past ±0.25 logit blocks ENTRY in that stat unless a cause is logged in `data/nba_tilt_causes.json`;
  - market data older than 60 minutes inside the last hour before tip FAILS;
  - NBA recompute uses the logic version that priced the leg.
- **learn:**
  - blends refit per sport only, from 200+ graded legs, at most monthly (the cross-sport blend is frozen at its current values);
  - avoid list needs 50+ legs with the shortfall in both halves of its history;
  - every learned change is logged to `data/learn_log.jsonl`;
  - Wednesday legs are a permanent holdout, never fitted on.
- **Data:** every DraftKings pull is snapshotted (`data/nba_dk_snap/`) for closing line value. The nightly report carries the skill, label, CLV and tilt tables.
- **Rollback:** `git revert` the commit; the published logic (v1) is unchanged by these.

## 2026-11-05: v1 -> v2 (v2 candidate (minutes^1.0, shared swing .8, segment bias, market-dominant blend, derived gates, SE entry))
- Live shadow evidence: 848 graded legs over 1 days; log loss current 0.7121272649833567 vs new 0.6944613590929176; label gap 0.11611233019070066 -> 0.04377976988033119
- Backtest evidence: {"corpus": "walk-forward 2026-10-25..11-02, live-like availability, 4,801 held-out legs (data/nba_bt/final_eval.json)", "logloss_selected": [0.6908378077671773, 0.6863245948130448], "brier_selected": [0.2487967026558354, 0.24660997726008627], "logloss_over": {"before": 0.6908378077671773, "after": 0.6863763902831964, "market": 0.6875868366393822}, "after_vs_before": {"mean": -0.004461417483980874, "ci95": [-0.006526755894954256, -0.0024379895648026294]}, "after_vs_market": {"mean": -0.0012104463561858803, "ci95": [-0.0026145046282530144, 0.00024041031556068748]}, "info_weight": {"b": 0.2286006
- Rollback: `python -m edge.nba_model rollback` restores v1.
- Caveat recorded at promotion: the live evidence is one night (12 final games). A game-clustered bootstrap of the log-loss difference gives −0.0177 (95% CI −0.0371 to +0.0017); the new logic was better in 8 of 12 games. The promotion rule (200+ legs or 14 days) is met by leg count; the backtest (CI excluding zero) and the much smaller label gap carry the rest. Watch the next 3 nights; roll back if v2 trails v1's archived numbers.
- With this promotion the simulation settings follow the logic version everywhere: pricing, the most-likely-game list and the Sim Lab export use the published logic's settings, and `edge verify` re-runs each leg under the version that priced it (`logic vN` in its notes).

## 2026-11-06: tennis v1 (new sport: ATP + WTA point-by-point simulation)
- **Data (real, no estimates):**
  - Tennis Abstract jsfrags: last-52-weeks surface splits (SPW, RPW, ace %, DF %, matches with stats) and each player's last 20 matches;
  - 282 players cached (137 ATP, 145 WTA);
  - event context comes from both players' matches at the same event, or from a sourced entry in `data/tennis_events.json` (2026 WTA Finals: Indian Wells, hard, Nov 8–15, per Wikipedia).
- **Model:**
  - Barnett–Clarke matchup;
  - every point played (tiebreak at 6-6, 10-point deciding-set tiebreak at Slams, best of 5 only at ATP Slams);
  - day-to-day form measured from the real per-match stats: residual serve-rate variance after binomial noise and leave-one-out estimation error, plus the correlation of the two players' residuals. On matches before Sep 1 this came out as ATP sd 0.046 with ρ −0.80 (431 matches) and WTA sd 0.058 with ρ −0.78 (283 matches). Each run draws the day's rates; the rate-estimate uncertainty is drawn too.
- **Walk-forward test** (matches Sep 1 – Nov 6, form measured only on earlier matches, 20-match histories):

  | | Matches | Games MAE (model / base) | Line log loss at 21.5 (model / base) | Winner log loss (model / coin) |
  |---|---|---|---|---|
  | ATP | 440 | 5.30 / 5.36 | 0.672 / 0.674 | 0.669 / 0.693 |
  | WTA | 302 | 4.87 / 4.95 | 0.673 / 0.677 | 0.653 / 0.693 |

  - Three-set Brier is level with the base rate (0.234 vs 0.234).
  - The plain fixed-rate model lost to the base rate on every measure: total games ran 0.9 (ATP) and 2.0 (WTA) too high, with too many three-setters and overconfident favourites. That is why form was added.
- **Blend:**
  - 0.2 model / 0.8 market, with Dabble total-games prices as the market, and no market means Low;
  - legs with a thin sample (a player under 8 stats-covered matches) or an unconfirmed event stay off the lists, because the rates aren't adjusted for opponent level;
  - a player with no stats-covered matches isn't priced.
- **Known limits:** no opponent-level adjustment, and no market winner price in the feeds. Aces, double faults and break points won are excluded until real counts can grade them.
- **Rollback:** `git revert` the commit (tennis is self-contained in `edge/tennis.py`).

## 2026-11-06: tennis v2 (deeper history, opponent-adjusted ratings, the market's winner price)
- **Data:**
  - TennisMyLife match database, 91,679 matches from 2018 on: ATP tour (with real match dates and minutes), ATP Challengers and WTA tour, each with both players' serve counts. Cross-checked against Tennis Abstract: identical serve counts on Fritz d. Fils.
  - WTA 125 matches from the WTA's own feed, for thin WTA players.
  - Tennis Explorer closing and current odds.
  - Tennis Abstract stays the fallback.
- **Walk-forward test** (tuned Jan 2025 – Aug 2026, scored Sep 1 – Nov 6 2026): `data/tennis_bt/factor_study.json` and `market_test.json`; code in `edge/tennis_factor_study.py`.

  ATP, 1,723 matches:

  | | Winner log loss | Games-won line log loss | Total games line log loss |
  |---|---|---|---|
  | Old (plain averages) | 0.669 | 0.686 | 0.695 |
  | Opponent-adjusted ratings | 0.640 | 0.680 | 0.694 |
  | + Elo | 0.632 | 0.682 | 0.698 |
  | + market winner | 0.608 | 0.673 | 0.692 |

  WTA, 350 matches: ratings 0.657 for the winner (old 0.666). Games won (0.667) and totals (0.692) were best on the ratings alone: the market and Elo didn't help there.
- **Adopted** (`data/tennis_bt/decision.json`):
  - opponent-adjusted ratings, half-life 730 days (ATP) / 365 days (WTA), ridge 400 points, form measured on the ratings' residuals;
  - ATP games won and total games priced with the winner set to the market's price when Tennis Explorer lists the match.
- **Not adopted:** Elo (the market beats it), fatigue (ATP +0.002 out of sample, WTA nothing; tuning terms under 1.5 SE), indoor and handedness (no change in point log-likelihood), heavier recency (180-day half-life was worse).
- **Rollback:** delete `data/tennis_bt/decision.json` (no market anchoring) and set `tml_pair` to return None (the Tennis Abstract path).

## 2026-11-06: NBA labels and display after the user's audit (Collin Murray-Boyles card)
- **High means agreement** (live, at the user's direction; `gate_label` in `edge/nba_pp.py`, applied by the pricer and by `verify`). A High leg needs all of:
  - a market price;
  - simulation and market within 5 points (`AGREE_MAX`);
  - tonight's tilt in that stat inside `TILT_MAX`, or a logged cause;
  - minutes confirmed (no L28 minutes gap);
  - a PrizePicks line 2+ points from DraftKings' (`GAP_2ND`) confirmed by a second book (Dabble).

  Any miss holds the leg at Medium, and the card lists the reasons. Probabilities are unchanged: this moves labels only.
- **Second-book check in `verify`:** a not-started leg whose line is 2+ points from DraftKings' FAILs with no second book or with one that disagrees on the side; a started leg gets a WARN.
- **Display follows the gate:** the card's label is the gated label. The market block shows the DraftKings conversion in steps (book line and price, de-vigged, carried to the PrizePicks line), the second book, the role (starter, projected minutes vs season and last 5), tonight's rotation against season minutes (who absorbs an injured starter's minutes), and the team's injuries.
- **One history line:** season and last 5 (average and trend) merged into one minutes-weighted reason; H2H counts only when those games' minutes are within 15% of tonight's projection.
- **Shadow v3 registered, not live** (`data/nba_model.json` → `shadow`): v2 plus shrinking to the market when simulation and market are more than 8 points apart. It changes probabilities, so under the user's rule it is scored live against v2 and adopted only after beating it on 200+ graded legs or 14 days, on log loss and label calibration.
- **Pre-tip lineup lock:** the scheduled re-check runs at 6:31, 7:31 and 9:31 pm ET, about 30 minutes before tip-off windows.
- **Not done yet:** opponent points allowed to forwards per 100 possessions (the engine doesn't carry team defensive possessions by position), and a with/without sample for an injured starter (the rotation table shows tonight's redistribution instead).
- **Rollback:**
  - set `AGREE_MAX = 1.0` and `GAP_2ND = 99` in `edge/nba_pp.py` (labels revert to the blend gates);
  - set `"shadow": null` in `data/nba_model.json` (drops v3);
  - `git revert` the commit for the display.

## 2026-11-07: NBA simulation study (headroom minutes, assist-share fix) → shadow v3
Prompted by the user ("maybe the simulation needs to be better") after Keyonte George's reb + ast under (a 53% Low leg, simulation 62%) went 7 in the first quarter.
- **Where the simulation stands** (corpus `data/nba_bt/corpus_x_base.json.gz`: 95 games to Nov 5, 6,431 DraftKings lines, every game re-simulated with only what was known before it):
  - On its own it loses to a coin flip at DraftKings' line: log loss 0.705 (DraftKings 0.689, coin 0.693), calibration slope 0.28.
  - It still adds information beyond the price: 0.21 ± 0.05 on its logit difference, which is the 0.2 weight the published blend already gives it. The blend scores 0.687, slightly better than DraftKings.
  - Its spread is calibrated (randomized PIT sd 0.285 vs 0.289 uniform); the earlier "too wide" reading was a whole-number artifact. The weak part is location, not spread.
  - Known minutes would cut its points error 17% (rebounds 12%, assists 8%); minutes miss by 4.8 on average.
- **Headroom minutes sharing** (`MINUTES_SHARE = "headroom"`): minutes freed by absences go to players in proportion to their room below their own ceiling (last-10 high + 3) instead of scaling everyone, so stars near their usual load barely move.
  - Box-score fair test, tuned on 2025-26 and scored on 2026-27: starters' minutes MAE 5.13 → 4.77 and 4.70 → 4.38.
  - Corpus: minutes MAE 4.77 → 4.61, and moving DraftKings' price to lines 1–5 points away (the PrizePicks case) improves by 0.012 log loss per line (game-bootstrap CI −0.027 to −0.001). The main-line blend doesn't change (+0.0003, CI −0.0004 to +0.001).
- **Assist-share fix** (`AST_FIX`, worker `nbAstFix`): assists can't go to the shooter, so drawing them in proportion to per-minute rates undercounted high-usage players and overcounted the bench.
  - Starters' simulated assists per 36: 4.19 → 4.34 (actual 4.46); bench 3.32 → 3.09 (actual 3.17).
  - Simulation log loss on assist lines −0.004. The blend is unchanged.
- **Not adopted:**
  - smaller role swing (PIT showed the spread was already right; simulation log loss worse);
  - smaller minutes spread (no change);
  - a longer minutes window (better on 2025-26, worse on 2026-27);
  - more weight on last season's rates (250/500/1000 minutes: points worse, rebounds and assists within noise).
- **Status:** both pieces are in **shadow v3**, alongside the disagreement shrink. The live logic is unchanged. v3 is promoted only after beating v2 on 200+ graded legs or 14 days, on log loss and label calibration. The shadow re-simulates with its own settings, which adds about 8 minutes to each `nba-picks` run.
- **Rollback:** `"shadow": null` in `data/nba_model.json`. Both switches default off in `gamesim/nba.py`.

## 2026-11-07: tennis scouting cards (how each player plays) and the style-matchup test
Prompted by the user: "you are only looking at the data and numbers but not truly understanding each player and how they play... you need to watch and study."
- **Study sources** (real records, nothing typed from memory):
  - the Match Charting Project: volunteers chart every shot of a match from video (Tennis Abstract, CC BY-NC-SA 4.0). It covers rally lengths won, net points, forehand and backhand winners and errors, slice and drop shots, serve direction and damage, return depth and in-play rate, and points won in three shots or fewer. Coverage is deep for top players (Alcaraz 85 charted matches since Sep 2024, Rybakina 57) and thin below tour level;
  - every match's serve line in the TennisMyLife database (aces, double faults, first serve in and won, second serve won, return points won against first and second serves, break points, tiebreaks), plus WTA 125s from the WTA feed.
- **Cards** (`edge/tennis_scout.py`, shown on the Sim Lab tennis simulator):
  - a style label only when the numbers are clear;
  - a read of what stands out (75th percentile and up, or 25th and down, against the tour's current top 150, with minimum samples);
  - opponent-adjusted serve and return from the ratings;
  - the level the numbers came from;
  - factual matchup notes;
  - every number side by side.
- **Style-matchup test** (`edge/tennis_style_test.py` → `data/tennis_bt/style_test.json`): interaction terms fitted on Jan–Aug 2026 (ratings cut 1 Jan) and scored on September onward (ratings cut 1 Sep), against the ratings' serve-point predictions.
  - ATP: small but real, +0.000024 log likelihood per point (CI +0.000008 to +0.000039, 3,807 serve rows). The main term: big servers win fewer serve points than the ratings say against strong first-serve returners, about 0.14 points per 100 per SD × SD.
  - WTA: nothing (−0.000032, CI −0.00013 to +0.00006).
  - Charted terms (first-strike vs return in-play, long-rally win rates): nothing extra, but only 466 ATP and 242 WTA test rows had charted data for both players.
- **Status:** context only; the win probability is unchanged. The ATP term is a candidate for the tennis model's next version if it holds as the test window grows.

## 2026-11-07: nightly simulation audit; team-level market anchor (shadow)
Prompted by the user after OKC @ MEM ("why did the simulation have MEM winning... learn from each night's losses, see where the simulation went wrong compared to actual and keep injecting fixes").
- **Why Memphis:** with eight games each, this season's results rated Memphis +6.9 and OKC +1.8 per 100 possessions.
  - Team strength alone made Memphis a 7.2-point home favourite. Absences were a wash (two out on each side). The player ratings trimmed it to Memphis by 4.3 (61%).
  - DraftKings had OKC by 4.5, and OKC won by 31.
  - The preseason prior that would have helped is off (it was tested on Nov 3 and didn't hold up).
- **Team-level market anchor** (`TEAM_MARKET_W`, `gamesim.nba.anchor_to_market`): moves each side's make rates so the expected margin and total sit on DraftKings' pre-tip line; pace stays the engine's.
  - On 973 games of 2025-26 the market's margin missed by 14.11 against the engine's 14.35, and totals by 18.46 against 19.52. The best blend weight was 1.0 for both.
  - Player-prop corpus (6,431 lines, 95 games of 2026-27): no measurable change (simulation 0.7046 → 0.7048, blend 0.6868 → 0.6869, carried prices unchanged).
  - **Status:** in shadow v3, so tonight's runs score it live. Game-level win chances become the market's by construction.
- **Nightly audit** (`edge sim-audit`, `edge/sim_audit.py`). Every published-logic run saves each game's last pre-tip prediction (`data/nba_pretip/`). The next day the audit compares:
  - winners and margins against the market;
  - late scratches and surprise minutes;
  - the biggest minutes misses;
  - per-minute production by role.

  `findings()` names the patterns that repeat across nights and ties each one to a switch. A fix goes through a walk-forward test and then shadow, never straight into a published number. Data bugs are fixed directly. The audit is part of the on-demand Refresh routine.
- **Nov 6 audit** (from the saved boards):
  - winners: simulation 8/9, market 8/9 (they split the two disagreements);
  - 5 late scratches;
  - 8 surprise-minutes players, mostly Boston's 39-point win at Charlotte;
  - biggest minutes misses: Brandon Miller (projected 40, played 14), Leaky Black (13 → 40) and Alijah Martin (10 → 31).

## 2026-11-07: tennis on the Winners tab (display only)
- `tennis_watch.scoreline`: exact distribution of final scorelines at fixed serve-point rates (game, set and tiebreak
  recursions; coin toss for first serve). Its win chance matches `tennis_hist.match_win` (tested).
- `tennis_watch.save_winners`: before the first serve, each match's win chance (day-to-day form included; ATP matched
  to the price as the simulator's default, WTA ratings only), the projected winner's most likely exact scoreline, the
  set split and average games, plus the ratings-only win chance. Written to data/winners/tennis/<CET date>.json.
- `winners.py` grades them against Tennis Explorer's results pages (matched on both players' page ids; a match short of
  the set count 5+ hours after its start counts as a retirement).
- No pricing or label change. Rollback: drop the tennis branch from `winners.export` and the `save_winners` call.
