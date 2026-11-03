# Play-by-play engines: plan and status

Asked for (2026-11-03): replace the drive-by-drive NFL engine with play-by-play, and build engines at each sport's natural unit
for all sports. Every engine: pre-game-only ratings from named free sources, vectorised 50,000-run simulation, out-of-sample
backtest vs closing no-vig lines, error bars (MC + structural from the backtest + missing inputs), the PLAY/PASS rule.

| # | Sport | Unit | Source | Status |
|---|---|---|---|---|
| 1 | NFL | play (call, sack/INT/complete, yards, penalties, clock, timeouts, 4th-down decisions, special teams) | nflverse pbp | done: `gamesim/nfl_pbp.py`, default engine. 147 snaps/game (real 147), 3rd-down 40.3% (40.1), RZ TD 56.8% (58.8). Backtest wk 4-8: win Brier 0.237 vs market 0.223 (drive engine 0.234) |
| 2 | NBA | possession (TO, 2/3PT, fouls/FTs, OREB, late fouling, OT) | ESPN box scores | done: `gamesim/nba.py` + `sports.py`. Calibrated to league pace/scoring/home margin. Backtest (59 early-season games): win Brier 0.227 vs market 0.194. No player layer yet |
| 3 | NHL | event clock, 10-s ticks (EV goals from shots × finishing × goalie, penalties → power plays, empty net, 3v3 OT, shootout) | ESPN box + NHL API pbp/standings | done: `gamesim/nhl.py` + `sports.run_hockey`. Empirical-Bayes shrinkage per stat; home ice from last season's standings (flagged). Backtest (126 games): win Brier 0.237 vs market 0.230 |
| 4 | MLB | plate appearance, base-out Markov chain | MLB Stats API | not started (stopped after NHL at the user's request, 2026-11-03) |
| 5 | Soccer | minute-by-minute chances/goals, score effects, red cards | ESPN match stats | not started (stopped after NHL) |
| 6 | CFB / CBB | NFL play engine / NBA possession engine with college parameters | ESPN | not started. `--sport ncaab` is wired to the NBA engine with a 40-minute clock but has not been run or backtested |
