# NBA prop pipeline: parameters

Every number the NBA prop pipeline uses that isn't learned from that night's data, with where it came from and how
it was tested. "Sensitivity" is the change in the simulation's own log loss on 5,312 DraftKings main lines (2026-27,
walk-forward backtest `edge/nba_backtest.py`, 5,000 runs per game) when the parameter is changed alone; lower log
loss is better, baseline 0.7043. Re-fit the ones marked **re-fit** as graded legs accumulate.

## Most sensitive (props)

1. **Last-season prior on player rates** `PLAYER_PRIOR_MIN = 100`: removing it costs +0.022 log loss (0.7262), the
   largest effect of any parameter. Keep; re-fit the weight (50 / 100 / 200 minutes) once 500+ legs are graded.
2. **Minutes allocation exponent** `MINUTES_ALPHA`: 0.8 → 1.0 improves log loss by −0.0028 and removes the
   starter/bench split (over-rate gap −2.0 / +2.7 pts → +0.8 / +0.5). See Fix 1.
3. **Per-game role swing** `PLAYER_SHOCK = 0.30`: 0.30 → 0.20 narrows the ranges (59.2% → 56.6% of results inside the
   25th-75th) but costs +0.0035 log loss: the width is covering projection error, so it stays until the location error falls.

Garbage time (`PLAYER_GARBAGE.g`) is fourth: switching it off improves log loss by −0.0006 and moves starters' over
rate by +2.4 pts.

## Inventory

| Parameter | Value | File | Origin | Tested |
|---|---|---|---|---|
| Team-rate prior `LAM` | 4 games | gamesim/nba.py | hand-set at build | team backtests only |
| Score effects `COMEBACK_SD` | 14.0 | gamesim/nba.py | fitted to the 14-point real margin SD | winners held out (Nov 4); props: off costs +0.0008 |
| Injury price `INJURY_BETA` | 0.50 pts per Game Score pt | gamesim/nba.py | fitted 2025-26 Nov-Jan, held out Feb-Apr | props: no effect (team level only) |
| Injury shrink `INJURY_K` | 200 min | gamesim/nba.py | hand-set | not tested |
| Player-rating move `PLAYER_RATING_W` | 0.59 | gamesim/nba.py | fitted 2025-26 Nov-Jan | winners held out; props: no effect |
| Player-rating ridge `PLAYER_RATING_LAM` | 20 games | gamesim/nba.py | grid on Nov-Jan | winners |
| Last-season weight `PLAYER_RATING_DELTA` | 1.0 | gamesim/nba.py | grid on Nov-Jan | winners |
| Game Score prior `PLAYER_RATING_KMIN` | 300 min | gamesim/nba.py | hand-set | not tested |
| Last-season player prior `PLAYER_PRIOR_MIN` | 100 min | gamesim/nba.py | tuned on points MAE | props: removing costs +0.022 (**re-fit**) |
| Team-average prior (no last season) | 60 min | gamesim/nba.py | hand-set | not tested |
| Shooting shrink 2P / 3P / FT | 40 / 50 / 25 attempts | gamesim/nba.py | hand-set | not tested |
| Prior attempt caps | 150 / 150 / 100 | gamesim/nba.py | hand-set | not tested |
| Minutes window / decay | 5 games, 0.85 | gamesim/nba.py | hand-set | recency decay tested earlier: no gain |
| Returning-player minutes | 90% of season | gamesim/nba.py | hand-set | not tested |
| Minutes exponent `MINUTES_ALPHA` | 0.8 (candidate 1.0) | gamesim/nba.py | minutes MAE test Nov 4 | props: 1.0 better (Fix 1) |
| Minutes SD floor / cap | 3.0 min / 42 min | gamesim/nba.py | hand-set | `MIN_SD_SCALE` knob added, not yet run |
| Role swing `PLAYER_SHOCK` | 0.30 | gamesim/nba.py | ~20% outside 10-90% (Nov 3) | 0.20 costs +0.0035 |
| Shared swing `SWING_RHO` | 0 (candidate 0.5) | gamesim/nba.py | new (Fix 6) | correlation check below |
| Garbage time a / b / g | 12 / 1.5 / 0.3 | gamesim/nba.py | fitted to starters' minutes by final margin | props: off −0.0006, starters' over rate +2.4 pts |
| Head-to-head coefficients | .059 / .068 / .102 / .066 | gamesim/nba_research.py | fitted 2025-26, held out | props backtest: no effect |
| Assisted-3 multiplier | 1.28 × team rate | simlab/index.html | hand-set | not tested |
| Bias filter | DK line within 1 pt, n ≥ 10 | edge/nba_pp.py | hand-set | replaced by the segment table (Fix 1) |
| History regression | n / (n + 10) | edge/blend.py | hand-set | history adds nothing on held-out legs (Fix 2) |
| Blend weights | .4496 / .4135 / .0705, +.0461 | data/adjustments.json | 31 cross-sport bets | replaced for NBA (Fix 2) |
| Gates High / Medium | 65% / 58% | data/adjustments.json | hand-set | re-derived (Fix 5) |
| Gate spread / history n | 12 pts / 10 games | data/adjustments.json | hand-set | re-derived (Fix 5) |
| L19 bias cap | 0.25 logit | edge/blend.py | hand-set | NBA has no model_bias_logit entries |
| Break-evens | 57.7 / 58.5 / 54.2% | edge/nba_pp.py | payout math | goblin/demon: unknown multiplier = no ENTRY |
| Verify tolerances | 0.005 / 5 / 4 pts (ENTRY 2 / 2) | edge/verify.py | hand-set | tightened for ENTRY (Fix 7) |
| Tilt monitor | ±0.25 logit | edge/nba_pp.py | Fix 7 default | re-fit with live tilt history |
| Stale market | 60 min before tip | edge/verify.py | Fix 4 default | — |
| Drift check | 50 legs, 5 pts | edge/verify.py | Fix 7 default | — |
| Learn minimums | 200 legs, 30 days; avoid 50 legs, 2 windows | edge/learn.py | Fix 8 defaults | — |
| Holdout weekday | Wednesday | edge/learn.py | Fix 8 | — |
| Promotion bar | 200 graded legs or 14 days | edge/nba_model.py | the spec | — |
