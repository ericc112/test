# gamesim: one game, 50,000 times

| Sport | Command | Engine (natural unit) | Out-of-sample backtest vs closing market (Brier, winner) |
|---|---|---|---|
| NFL | `python3 -m gamesim --game 2026_09_JAX_BAL` | every snap (`nfl_pbp.py`); `--engine drive` for the drive model | 0.237 vs 0.223 (72 games) |
| NBA | `python3 -m gamesim --sport nba --game <ESPN id>` | every possession (`nba.py`) | 0.227 vs 0.194 (59 games) |
| NHL | `python3 -m gamesim --sport nhl --game <ESPN id>` | 10-second event clock (`nhl.py`) | 0.237 vs 0.230 (126 games) |

No engine beats the closing market, and each report says so. Status and what's next: `PLAN.md`.

```bash
cd betting
python3 -m gamesim --game 2026_09_JAX_BAL                 # nflverse game_id; writes gamesim/reports/<game>.md
python3 -m gamesim --game 2026_09_JAX_BAL --qb-home "Lamar Jackson"   # starter override
python3 -m unittest tests.test_gamesim                     # sanity tests
```
It needs numpy only. The first run downloads about 30 MB from nflverse and caches it in `betting/.cache/gamesim/`.

## Modules
| Module | Job |
|---|---|
| `data.py` | Named sources, cached with pull times: nflverse play-by-play, schedule, injuries, depth charts and snaps; ESPN/DraftKings lines with prices and openers; Open-Meteo forecast and geocoding |
| `ratings.py` | (a) Ratings. Opponent-adjusted ridge regressions on plays before the game: offense/defense EPA/play and success rate, home term, dropback share, neutral pace. QB EPA/dropback with a pass-defense adjustment |
| `players.py` | (b) Player layer. Projected starting QB from the depth chart, QB swap as an EPA/play adjustment, absences with their source, snap shares, rest, travel, weather |
| `drives.py` | The fitted drive model: result probabilities, FG make by distance and wind, conversions, return TDs, drive lengths by tempo, next start spots, game-level wobble |
| `engine.py` | (c) Simulation. Vectorised drive-by-drive game with the clock, shared game environment, endgame and overtime |
| `backtest.py` / `report.py` | (d) Outputs. Inputs per game, out-of-sample backtest, market comparison with the vig removed, error bars, factor table, decision rule |

## How each factor enters
| Factor | Where | How |
|---|---|---|
| Team strength | ratings → drive model | Offense EPA and success, opponent defense EPA and success allowed. These are features of the drive-result regression, so a better offense makes TDs likelier at every spot. Ridge shrinkage of 75 plays was tuned on 2025 weeks 6–18 only |
| QB / absences | players → ratings | Starter's EPA/dropback minus the season QB mix, times dropback share. Non-QB absences: no defensible impact rating, so 0 and flagged |
| Home field | drive model | Home indicator in the drive regression, fitted on 2025–26 drives |
| Pace | drive lengths | Drive length is drawn from real drives of the same result and tempo, scaled by the offense's neutral seconds per play |
| Game environment | engine | Each simulation draws a game-day EPA shock per offense (sd fitted from game-to-game wobble beyond play noise) and a shared pace shock (fitted from within-game co-movement). Everything happens inside that draw, which widens totals and margins realistically |
| Field position | engine | Next start spot drawn from real drives, given how and where the last one ended |
| Scoring | engine | TD + XP or two-point (chart in the 4th quarter and OT); FG make by distance (+ wind); safeties; return TDs. That keeps 3 and 7 as the key margins |
| Endgame | engine | Kneel-downs when leading with 2:00 or less; two-minute, protect-lead and chase tempo; partial credit when the half runs out mid-drive; 2025 OT rules (10 minutes, both teams possess, ties stand) |
| Rest, travel, referee | — | Not fitted: listed and flagged. Here rest (4 v 4 days) and time zone are equal; the referee crew isn't published yet |
| Weather | drive model | FG make probability gets a wind term fitted on outdoor attempts with schedule wind; forecast from Open-Meteo |

## Error bars
- **Monte Carlo:** √(p(1−p)/n), ≈ 0.22 points at 50,000 runs.
- **Structural:** the out-of-sample RMS gap between the model and the closing no-vig market in this season's backtest. It already contains rating noise and everything the model leaves out. A rating bootstrap is reported alongside it.
- **Starter spread:** the range across the depth chart's top three QBs ÷ 4.
- **Missing input:** if the market moved between open and now by more than the model's starter scenarios explain, half the unexplained move is added. That is news the model doesn't have, so the error bar widens instead of the model guessing.

All terms add in quadrature. Decision rule: PLAY only if edge ≥ 2 points and edge − 1.5 × total error > 0.

## What the backtest says
On 2026 weeks 4–8 (72 games, out of sample), the model is worse than the closing market on winners and totals:

| | Model | Market |
|---|---|---|
| Brier, winner | 0.234 | 0.223 |
| Brier, total | 0.259 | 0.251 |
| Brier, against the spread | 0.247 | 0.252 |

The spread result covers 70 games, too few to read as skill. Treat its disagreements with the market as model error until a larger sample says otherwise.
