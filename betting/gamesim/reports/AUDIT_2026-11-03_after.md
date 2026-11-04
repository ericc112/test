# Model audit, 2026-11-03: fixes and before/after verification

Findings, recorded before any fix: `AUDIT_2026-11-03.md`. Only CRITICAL and MAJOR items that were repairs were
changed. Design changes are listed as proposals at the end and were **not** applied.

## Final verdict

1. **Mechanically sound? Mostly yes, after the fixes.**
   - *Passes:* RNG, sampling, identical teams (about 50/50 with margin 0 in all three sports), reproduction of inputs, convergence, endgame triggers and player sums all pass.
   - *Structural gaps that remain, measured and listed below:*
     - NBA margins are too wide (no score effects).
     - NBA player ranges are too narrow.
     - NFL safeties are still 2–3× real, and the key numbers 3 and 7 are off.
     - The NHL is slightly over-dispersed.
2. **Calibrated? No.**
   - *NBA winners:* underconfident by about 6 points in every bucket (table below).
   - *NBA and NFL spreads and totals:* no skill.
   - *NHL winners:* roughly calibrated.
   - *Recalibration (Platt scaling):* fitted on an earlier period, it made the later period worse or no better every time, so it was not applied.
3. **Beats the market out of sample? No.**
   - *NBA:* worse (winner Brier gap +0.015, 95% CI +0.009 to +0.020, 974 games).
   - *NFL:* worse (+0.016, CI +0.001 to +0.032, 2025 regular season).
   - *NHL:* not distinguishable from the market (+0.001, CI −0.002 to +0.005, 936 games), and not better.
   - *Disagreements carry no information:* given the closing line, the model's disagreement has a weight of about 0 (NBA −0.05 ± 0.22, NFL −0.17 ± 0.29, NHL +0.43 ± 0.37). Where it disagrees most, outcomes follow the market.
4. **Largest remaining source of error: the inputs, not the simulation.**
   - Team strength comes from box-score ratings with no lineup or injury information. Removing DET's best player changes DET's simulated points by 0.01.
   - Early in the season these ratings are noisy, and the market already knows all of this.
   - The engines turn ratings into scores faithfully; the ratings are what the market beats.

No locks, no guarantees: the honest result is that the closing line is the better forecast in every sport tested.

**Update, Nov 4: score effects and player ratings added to the NBA model** (section at the end).
- *Margin spread:* fixed. Two average teams now have a 14.3-point margin SD (was 16.8).
- *Underconfidence:* 2–5 points per bucket, down from about 6.
- *Gap to the market:* on held-out games the winner Brier gap halves, from +0.016 to +0.008. The market is still better, and the model's disagreement with it still carries no information.

## Fixes (each with before → after)

| ID | Fix | Before | After |
|---|---|---|---|
| C1 | NBA: a team down 1–2 fouls once the shot clock is off (Python and browser) | Leader up 2, ball, 20 s: **100.0%**. Up 1, 15 s: **100.0%** | **93.5%** and **82.6%** |
| M1 | Live ratings cutoff = every game of earlier US days | 92 of 107 NBA games used (last night's 15 dropped), 192 of 196 NHL | 107 of 107, 196 of 196 |
| M2 | Backtests grouped by US day, cutoff before that day | Same-evening games leaked into ratings | None (cutoff 10:00Z of the US day) |
| M3 | NBA pace shock = out-of-fold pace residual minus the engine's own possession noise | Shock SD 5.04, total-points SD 22.1 | Shock SD 3.28, total-points SD 20.6 (real residual vs the closing total: 18.5–18.9) |
| M5 | NFL: own 10 to goal line is its own yards zone and sack pool; no kneel at the own 1; offensive penalties half the distance | 0.191 safeties a game, 0.0074 from kneels | 0.100 (neutral), 0.0 from kneels. Real: 0.044, so **partial**, rest is a proposal |
| M7 | Player ranges and the line checker show their measured calibration | Ranges and probabilities with no error statement | Page states 24–27% outside the 10–90% range (should be 20%), and no edge at the median line on points or rebounds |
| M8 | NHL goalies named next to the numbers, with basis | Only "Projected goalies" in the factor table | "Goalies assumed: X and Y, each team's most recent starter, not a confirmed starter" |
| M9 | Odds parsers tolerate "OFF" | Crash on the 2025-26 NHL season | 1,313 games load |
| M10 | NBA/NHL scoring level fitted on the home configuration | NBA total with home +2.2 over target, NHL +0.05 | NBA 226.76 vs 226.81, NHL 6.422 vs 6.413 |
| M11 | Home edge fitted as a difference on common random numbers | NHL home margin 0.066 (target 0.130) | 0.118 (target 0.130); home win %, two average teams: 51.0 → 52.1 |
| M12 | PLAY-rule error ≥ the part of the disagreement not shown to carry information out of sample; structural RMS pooled with last season | PLAY in 4–28% of games, depending on sport and market | PASS in every game: the trusted weight is 0 everywhere (table below) |

NFL safety rates come from two average teams over 8,000 games. NBA figures are for two average teams over 60,000 games unless noted.

## Phase 1 re-run (browser engines)

| Check | Before | After |
|---|---|---|
| Identical teams, NBA | 49.90% ±0.16, margin +0.01 | 50.16% ±0.16, margin +0.04 |
| Identical teams, NHL | 49.88% ±0.16, −0.01 | 50.18% ±0.16, +0.00 |
| Identical teams, NFL | 50.52% ±0.35, +0.05 | 49.94% ±0.35, −0.08 |
| NBA, home +2, home ball, 20 s | 1.0000 | 0.9353 |
| NBA, home +1, home ball, 15 s | 1.0000 | 0.8260 |
| NBA, home +2, away ball, 20 s | 0.8168 | 0.7974 |
| Player layer: points = team score / minutes = 240 | yes / max 3.07 short | yes / max 2.69 short (m2, not fixed) |
| NFL safeties (neutral / with home) | 0.191 / 0.189 | 0.100 / 0.117 |
| NFL margin 3 / 7 (real 14.6% / 8.7%) | 12.9% / 10.5% | 13.2% / 11.3% (not fixed: proposal) |
| RNG reseed (m1) | stale spare survives reseed | unchanged (MINOR, not fixed) |

## Phase 3 re-run

| Check | Before | After | Reference |
|---|---|---|---|
| NBA total-points SD, PHI@DET-day ratings | 22.10 | 20.63 | 18.5–18.9 vs the close; 19.1 vs the model's own mean |
| NBA margin SD | 16.85 | 16.71 | 14.1 (proposal 1) |
| NBA overtime rate | 2.1% | 3.1% | 4.4–4.7% |
| NBA per-team possession SD | 6.20 | 5.26 | 4.85 (out-of-fold target) |
| NBA points per possession, analytic vs simulated | 1.0872/1.0854 | 1.0783/1.0772 | equal (passes) |
| Convergence, 4 sizes × 3 seeds | χ² 7.6 on 8 df | χ² 7.2 on 8 df | passes |
| NHL home margin, two average teams | 0.066 | 0.118 | 0.130 |
| NHL total SD / P(total ≥ 10) / OT rate | 2.40 / 9.3% / 20.2% | 2.40 / 9.3% / 20.2% | 2.14–2.30 / 5.6–7.1% / 21.9–24.8% (not fixed: score effects) |
| NFL second-half pass share (trailing / close / leading) | 69.1/55.1/40.9 | 68.8/54.9/40.6 | 68.8/55.7/40.5 |

## Phase 4: out of sample vs the closing market (before → after)

Brier score; lower is better. CI is the 95% bootstrap interval of model minus market.

| Sample | Market | Model before | Model after | Market Brier | After − market (CI) |
|---|---|---|---|---|---|
| NBA 2025-26, 974 games | winner | 0.2098 | 0.2096 | 0.1948 | +0.0086 to +0.0203 |
| | spread | 0.2609 | 0.2608 | 0.2499 | +0.0053 to +0.0167 |
| | total | 0.2700 | 0.2670 | 0.2499 | +0.0092 to +0.0253 |
| NHL 2025-26, 936 games | winner | 0.2447 | 0.2451 | 0.2439 | −0.0024 to +0.0048 |
| | total | 0.2501 | 0.2504 | 0.2485 | −0.0008 to +0.0044 |
| NFL 2025, weeks 3–18, 240 games | winner | 0.2317 | 0.2317 | 0.2158 | +0.0014 to +0.0316 |
| | spread | 0.2753 | 0.2754 | 0.2487 | +0.0096 to +0.0447 |
| | total | 0.2540 | 0.2545 | 0.2503 | −0.0068 to +0.0154 |
| NBA 2026-27 to date, 59 games | winner | 0.2265 | 0.2261 | 0.1943 | |
| NHL 2026-27 to date, 126 games | winner | 0.2366 | 0.2360 | 0.2296 | |
| NFL 2026, weeks 4–8, 72 games | winner | 0.2373 | 0.2367 | 0.2232 | |

Log loss tells the same story; for example NBA winners went 0.6089 → 0.6084 against the market's 0.5710.

**NBA totals bias** (simulated minus actual): +5.9 → +4.2 points. The home-edge part is fixed. The rest is the league scoring level drifting during the season, which the season-to-date average can't follow (proposal 6).

**NHL note:** the home-edge fix now delivers the designed target, last season's home margin (0.32 goals in 2024-25). Home ice in 2025-26 fell to 0.13, so the broken calibration had accidentally been closer. That is a limit of the design (proposal 5), not of the fix.

**NFL note:** the 2025 "after" run includes the yards-zone and kneel repairs. The half-the-distance penalty repair landed after it started; that repair changes about 0.08 safeties a game.

### Calibration of winners (model favourite's stated probability vs how often it won), after

| Bucket | NBA 2025-26 games / stated / hit | NHL 2025-26 games / stated / hit | NFL 2025 games / stated / hit |
|---|---|---|---|
| 50–55 | 222 / 52.7% / 53.6% | 396 / 52.4% / 50.0% | 44 / 52.5% / 47.7% |
| 55–60 | 195 / 57.5% / **64.6%** | 311 / 57.4% / 54.0% | 44 / 57.3% / 54.5% |
| 60–65 | 181 / 62.5% / **69.6%** | 156 / 61.9% / 67.3% | 37 / 62.1% / 54.1% |
| 65–70 | 142 / 67.4% / **73.9%** | 46 / 67.0% / 56.5% | 31 / 67.5% / 71.0% |
| 70+ | 234 / 75.8% / **81.6%** | 27 / 72.8% / 70.4% | 83 / 77.4% / **71.1%** |

NBA is underconfident in every bucket. NFL is overconfident at the top (favourites it gives 77% won 71%), and NHL is roughly calibrated. Recalibration was tested and **not** applied, because it never helped a later period:
- *NBA, Platt scaling fitted on November–January 2025-26:* February–April Brier 0.1948, against 0.1912 raw (worse; CI of the difference +0.002 to +0.005).
- *NBA, fitted on all of 2025-26:* this season 0.2276 against 0.2261 raw (no gain).
- *NHL:* 0.2419 vs 0.2412 on the second half of 2025-26, and 0.2423 vs 0.2360 this season (worse).

### Does the disagreement with the market carry information? (decision rule, M12)

Logistic regression of the result on logit(market) and logit(model) − logit(market), out of sample. The second
weight is the share of the model's disagreement that is real (1 = face value, 0 = noise).

| | Winners | Spreads | Totals |
|---|---|---|---|
| NBA 2025-26 + 2026-27 (1,033 games) | −0.07 ± 0.21 | −0.04 ± 0.16 | +0.09 ± 0.14 |
| NHL 2025-26 + 2026-27 (1,062 games) | +0.27 ± 0.34 | — | −0.10 ± 0.38 |
| NFL 2025 (240 games) | −0.17 ± 0.29 | −0.25 ± 0.23 | +0.06 ± 0.40 |

**PLAY rule, before (page error terms):**
- *NBA, 2025-26 (974 games):*
  - Winners: 54 plays (5.5% of games), ROI +3.1% (CI −43% to +55%).
  - Spreads: 37 plays (3.8%), ROI +8.7% (CI −22% to +40%).
  - Totals: 272 plays (28%), ROI −8.5% (CI −19% to +4%).
- *NFL, 2025 (240 games):*
  - Winners: 55 plays (23%), ROI −8.2%.
  - Spreads: 56 plays (23%), ROI −21.3%.
- *NHL, 2025-26 (936 games):*
  - Winners: 100 plays (11%), ROI +6.2% (CI −16% to +28%).
  - Totals: 83 plays (9%), ROI −17.3%.
- *Edge-only, any 2-point edge:* NBA winners lost 11.4% (CI −22% to −0.5%) over 858 bets; NBA spreads −9.8% (CI −16% to −3%) over 802.

**After:** the trusted weight (95% lower bound) is 0 in every sport and market, so the error never falls below the edge and every game is a PASS.

## Not fixed: MINOR (listed in the findings)

m1 RNG reseed, m2 the 48-minute cap, m3 the 8-overtime tie-break, m4 NHL dispersion, m5 NFL SD 4–6% narrow, m6 player backtest with known DNPs, m7 empty-net overlap, m8 early-season NBA home edge, m9 input sourcing notes.

## Proposals (not applied: need approval)

1. **NBA score effects.** Make efficiency and pace depend on margin and time, calibrated so the margin residual SD is about 14.1 and overtime about 4.5% (M4; also the NHL part of m4).
2. **NBA injuries in team strength.** Adjust the ratings by the minutes-weighted value of absent players (M6). Likely the largest single NBA gain.
3. **NFL scoring structure.**
   - Add a "backed up" term (inside the own 10) to the run/pass call and pass-result models. Real teams there drop back 1.25 times a game, not 1.70, and take almost no sacks inside the own 6.
   - Fit two-point decisions from data for all quarters.
   - Isolate the touchdown/field-goal mix.
   - Make home advantage symmetric with a fitted scoring level (M5, M10).
4. **Player game-to-game variance.** A per-player volume and efficiency shock, calibrated so the PIT tails return to about 20% (M7).
5. **NHL and NBA home edge.** Shrink in-season home margins toward last season's instead of using one or the other (m8; the NHL 2025-26 note).
6. **League scoring level.** Recency-weight it so totals follow in-season drift (NBA totals bias +4.2).
7. **Blend with the market.** If the model is used at all, use it as a small correction to the closing line, with the weight estimated out of sample. Today that weight is about 0, which is the same conclusion as the verdict.

## Applied after review: NBA availability (proposal 2)

The user asked for the proposal most likely to matter in real life.

**Method** (`gamesim.nba`: `player_values`, `availability_shift`, `INJURY_BETA`):
- *Player value:* Game Score per minute above the team's bench level, shrunk by 200 minutes, times his minutes when he plays.
- *Tonight's shift:* value × (out tonight − share of the rating games he missed). A player who sat half the games is half priced in, so nothing is counted twice.
- *Scale:* fitted on 2025-26 Nov–Jan (682 games): **0.50 ± 0.10** margin points per Game Score point (full season: 0.53 ± 0.07).
- *Where it applies:* to the offense, via one logit step on make rates. In the backtest, availability is "who sat" from the box score. Live, it is the injury report's Out/Doubtful list plus players gone from the roster.

**Held-out test, 2025-26 Feb–Apr (501 games never used in the fit):**

| | Without | With | 95% CI of change | Market |
|---|---|---|---|---|
| Winner Brier | 0.1912 | **0.1807** | −0.0162 to −0.0053 | 0.1645 |
| Spread Brier | 0.2636 | **0.2563** | −0.0145 to −0.0003 | 0.2500 |
| Total Brier | 0.2641 | 0.2664 | −0.0053 to +0.0101 (no change) | 0.2498 |
| Winner log loss | 0.5692 | 0.5432 | | 0.5002 |
| Margin RMSE (ratings-only fit check) | 15.20 | 14.65 | | 14.13 (residual vs the close) |

**Whole season and current season:**
- *Whole 2025-26 season:* winner Brier 0.2096 → 0.2030 (market 0.1948), spread 0.2608 → 0.2551.
- *2026-27 to date (59 games):* 0.2261 → 0.2234 (not significant).
- *Gap to the market:* the winner gap on the held-out games shrinks from +0.027 to +0.016, but the market is still better.
- *Disagreement with the market:* its weight is still about 0 (winners −0.09 ± 0.26), so the PLAY rule still passes everything.

## Added after review: the most likely game

"Watch a simulated game" now plays the most representative of the 50,000 runs:
1. **Score:** the most common final score (NBA smoothed over ±2 points a team).
2. **Run:** among those runs, the one closest to the typical path (halftime score, every NBA rotation player's line, usual overtime outcome).
3. **Replay:** that run is replayed exactly from its own seed.

Backtest on finished games it never saw (`likely_bt.py`):

| | NBA, 501 games (2025-26 Feb–Apr) | NHL, 441 games (2025-26 Feb–Apr) | NFL, 73 games (2026 wk 4–8) |
|---|---|---|---|
| Winner right: most likely game / one random game / betting favourite | **75.0%** / 59.1% / 75.2% | **55.3%** / 51.9% / 56.9% | **60.3%** / 42.5% / 64.4% |
| Margin MAE: most likely / random / closing spread | **11.9** / 17.9 / 11.0 | **2.18** / 3.01 / 2.24* | **9.2** / 13.2 / 9.0 |
| Total MAE: most likely / random / closing total | **15.6** / 22.9 / 14.4 | **1.94** / 2.65 / 1.87 | **9.9** / 17.4 / 10.4 |
| Exact final score hit | 0.6% | 6.1% | 1.4% |

\*The NHL "spread" is a ±1.5 puck line, not a margin estimate.

The most likely game is far closer to reality than a random simulated game and about as close as the closing line, but not better.

## Tested after review, not switched on: preseason prior moved with the players

**Idea:**
- Start each team from last season's strength, regressed toward average.
- Correct it for players who left or arrived (Game Score value × the availability scale).
- Let it fade as this season's games come in (worth k games).

**Fair test:** tune on 2025-26 with 2024-25 as "last season", then judge on 2026-27 with 2025-26 as "last season". The tuning never sees 2026-27. Expected margins are the engine's analytic means with availability, so only the prior differs.

**Results:**

| | Without prior | With prior |
|---|---|---|
| Tuned on all of 2025-26 (979 games), best k 4, rho 0.4: margin RMSE | 14.478 | 14.464 |
| — Oct–Dec | 14.42 | 14.26 |
| — Jan–Apr | 14.50 | 14.53 |
| Tuned on Oct–Dec only (k 25, rho 0.55): Oct–Dec | 14.42 | 14.11 (the line: 14.11) |
| Tuned on Oct–Dec only (k 25, rho 0.55): Jan–Apr | 14.50 | 14.74 (significantly worse) |
| **Held out, 2026-27 (93 games): margin RMSE** | 15.08 | 14.83 (CI of the change includes 0; the line: 13.49) |
| Held out, 2026-27: winners right | 59 | 55 |
| Held out, 2026-27: games closer to the result | | 48% |

**Verdict: not a reliable gain, so `PRIOR_K` stays unset.** The code (`preseason_prior`, `prior_shifts`, `with_prior`) and its tests remain for a later, better-specified attempt; candidates are a weight that stops after the first weeks, and a better player value than Game Score.

## Applied after review: player layer prior and role swings (proposal 4)

**Fixes:**
1. Shrink each player's per-minute volume and shooting toward **his own last season**, worth 100 minutes, instead of his team's average.
2. A per-player, per-game **role swing**: a log-normal of 0.35 on shots, rebounds and assists, drawn separately for each.

**Tuning:** 2026-27 games before Nov 2 only.
- *Prior strength:* projected-points MAE fell from 4.88 (team average) to 4.76 (100 minutes, best of 100 to 3,200). Starters' bias moved from −0.70 to +0.50.
- *Role swing:* the 10–90% ranges held 29% of points outside them with no swing; 0.30 gave 22%, 0.40 gave 19%, so 0.35 was used.

**Fair test, the same 143 Nov 2 starters with DraftKings pre-game points lines:**

| | Before | After |
|---|---|---|
| Over/under calls right | 71 of 143 | 69 of 143 |
| Brier (a coin flip is 0.250) | 0.278 | 0.275 |
| Points MAE | 5.31 | 5.23 (the line: 4.83) |
| Stars (lines ≥ 20): projection minus line | −2.4 | −1.2 |
| On the 96 priced lines: model's calls right / the book's lean right | 43 / 51 | 40 / 51 |

**Season calibration after (59 games, 1,164 player-games):** outside the 10–90% range for points 19.5%, rebounds 17.2%, assists 21.3%, 3s 24.1%. The projection MAE now beats a plain season average (points 4.76 vs 4.85, rebounds 1.92 vs 1.99).

**Verdict:**
- The projections and ranges are more accurate, so both fixes are switched on (`PLAYER_PRIOR_MIN`, `PLAYER_SHOCK`).
- The over/under calls did **not** improve and remain at coin-flip level. The book's lines are better, and the page says so.

## Applied after review: player minutes (why the points projections were off)

**What was wrong:**
- Shot share and efficiency per minute were roughly right; minutes were not. A game a player missed counted as 0 minutes in his recent average. Players who sit tonight are already removed through the injury report, so this double-counted the absence.
- Then 13–14 players were scaled to 240 minutes, which cut starters too.
- Examples, projected vs played: Curry 19 vs 33, Sengun 20 vs 38, Markkanen 20 vs 31, Ty Jerome 22 vs 37.

**Fix (`MINUTES_WHEN_PLAYING`):**
- Expected minutes = chance he plays × recency-weighted minutes when he plays.
- The chance counts coach's-decision benchings in the last 5 games; injured or off-roster games don't count either way.
- A player on none of the last 3 box scores gets no minutes.
- The role swing was retuned on pre-Nov 2 games: 0.30 puts about 20% of points, rebounds and assists outside the range (0.35 had been tuned before the minutes fix).

**Fair test, the same 143 Nov 2 starters and DraftKings lines (who sat known in both runs, prior and swing 0.35 in both):**

| | Old minutes | New minutes |
|---|---|---|
| Starters' minutes off by | 5.5 | 4.8 |
| Off by 8+ minutes | 23% | 17% |
| Points MAE | 5.36 | 5.11 (the line: 4.83) |
| Brier | 0.273 | 0.259 (coin 0.250, the book 0.249) |
| Over/under calls right | 66 of 143 | 67 of 143 |
| On priced lines: model right / book's lean right | 44 / 51 | 46 / 51 |

**Season, after all three player fixes (1,232 player-games):** points MAE 4.62, against 4.83 for a season average (originally 4.80 vs 4.85). Outside the 10–90% range: points 18.9%, rebounds 17.3%, assists 22.7%.

**Verdict:** switched on. Projections, minutes and probabilities are better. Over/under calls are still a coin flip; the book's lines are better.

## Player projections vs the "elite projection" spec (applied after review)

**Flaws found against the spec, and what happened to each:**

- **F1. Minutes ignored the simulated score** (spec steps 1 and 5): starters didn't lose minutes in simulated blowouts. **Fixed:** garbage time. Once a 4th-quarter lead reaches 12 + 1.5 × minutes left, each team's top five keep 30% of their role. It was fitted to real starters' minutes by final margin (2,566 team-games):

  | Final margin | Simulated change vs close games | Real change |
  |---|---|---|
  | 15–20 | −1.5 min | −1.6 |
  | 20–25 | −2.5 | −2.7 |
  | 25–30 | −3.5 | −3.7 |
  | 30+ | −4.6 | −4.6 |
  | 30+, before the fix | −0.1 | |

- **F2. No pull toward the market** (step 7). **Fixed:** with a DraftKings line, the final projection is the line + w × (simulated − line), with w = 0.26 / 0.24 / 0.62 for points / rebounds / assists, fitted on pre-Nov 2 lines (624 / 579 / 444). Held out on Nov 2 (208 / 196 / 158 lines):

  | | Points | Rebounds | Assists |
  |---|---|---|---|
  | MAE, before → after (the line) | 5.01 → 4.72 (4.72) | 2.00 → 1.81 (1.83) | 1.77 → 1.71 (1.68) |
  | Brier, before → after (the book) | 0.258 → 0.247 (0.250) | 0.252 → 0.247 (0.247) | 0.265 → 0.258 (0.244) |
  | Calls right, before → after | 105 → 112 | 114 → 113 | 74 → 74 |

- **F3. No recency weighting of rates** (step 2). **Tested, no gain:** with actual minutes, points MAE was 3.833 → 3.835 at a decay of 0.9. Left off. With actual minutes, points MAE is 3.8 against 5.1 with projected minutes: minutes are the dominant error.
- **F4. Outputs** (step 6). **Fixed:** the projection card shows:
  - minutes with a 25th–75th range;
  - the projection, the simulated mean, median and 25th–75th for points, rebounds and assists;
  - the DraftKings line, over/under, and the book's no-vig over;
  - error bars (backtest MAE);
  - the season average and the movers vs it (minutes, per-minute rate, this game);
  - the biggest risk;
  - what isn't modelled.
- **F5. No formula-vs-simulation reconciliation** (step 5). **Fixed:** flagged past 10%, with a stat-specific reason.
- **F6. Inputs the free data doesn't have.** Not fixable here; they are named on the card and covered by the error bars:
  - potential assists and rebound chances (tracking data);
  - on/off splits (lineup data);
  - position-specific defence;
  - confirmed lineups and minutes restrictions;
  - personal fouls (only as minutes variance);
  - rest days.

**Worked example, Gilgeous-Alexander, OKC @ CLE, Nov 2 (pre-game, 50,000 runs, graded after):**

| | Projection | 25th–75th | DraftKings line | P(over) | Actual |
|---|---|---|---|---|---|
| Minutes | 34.9 | 32–38 | | | 39 |
| Points | 29.3 (simulated 28.6) | 22–36 | 29.5 | 47% (book no-vig 49%) | 43 |
| Rebounds | 3.8 (simulated 4.9) | 2–5 | 3.5 | 51% | 3 |
| Assists | 4.4 (simulated 3.7) | 3–6 | 5.5 | 31% | 8 |

With six teammates out, his real usage rose far beyond the model's proportional redistribution: shot share 23.9% → 25.8%, minutes 32.6 → 36.2 before scaling. This is the on/off gap named in F6.

## Applied after review: score effects and team strength from player ratings (Nov 4)

The user asked for three improvements used by stronger public models. Each was tuned on earlier games, judged on games it never saw, and kept only if it helped.

**1. Pre-tip refresh.** A scheduled task regenerates the page data at 5:37 pm and 8:37 pm ET every day, picking up the injury report, DraftKings player lines and last night's results, then republishes the page.

**2. Score effects** (`simulate`, `COMEBACK_SD = 14.0`):
- *Method:* a team ahead of its expected margin path eases off and one behind pushes. This is a logit shift on make rates, proportional to how far the score is from that path, so the mean margin doesn't move.
- *Fit:* κ is set so two average teams have a 14-point margin SD, matching the real residual against the closing spread (14.05–14.17). It comes out at κ ≈ 0.037–0.039; the browser engine uses the same term.
- *Effect on two average teams:* margin SD 16.8 → 14.3 (browser) and 17.2 → 14.5 (Python, 2025-26 inputs). The total is unchanged because the and-one rate is refitted.
- *Why it matters:* the 16.8-point spread was the main reason every winner probability was too timid.

**3. Team strength from player ratings** (`PlayerRatings`, `with_player_ratings`, `PLAYER_RATING_W = 0.59`):
- *Ratings:* a game-level ridge regression of the final margin on who played, with each team's players weighted by their share of its minutes. Each player's effect is shrunk toward a Game Score prior. It is fitted on every game before the cutoff: this season plus the last two at full weight.
- *Tonight's margin:* the expected lineup at its projected minutes. The model's margin then moves 59% of the way to this number (total unchanged).
- *What it adds:* a player's value carries across teams and seasons, and it sees what a box score misses once a player has enough games.
- *Tuning (2025-26 Nov–Jan only):* a 14-point grid of shrinkage (5–80 games) and last-season weight (0.25–1.0). Every setting gave a blended margin RMSE of 14.15–14.20, so the gain doesn't hinge on the choice. Picked: 20 games and weight 1.0; the blend weight of 0.59 was fitted on the same games.

**Fair test, real simulations, same games** (before = the availability model above):

| | Before | Player ratings | Both (kept) | 95% CI, both − before | Market |
|---|---|---|---|---|---|
| **2025-26 Feb–Apr, 501 held-out games** | | | | | |
| Winner Brier | 0.1807 | 0.1780 | **0.1727** | −0.0112 to −0.0047 | 0.1645 |
| Winner log loss | 0.5432 | 0.5378 | **0.5235** | | 0.5002 |
| Spread Brier | 0.2563 | 0.2548 | 0.2563 | −0.0039 to +0.0038 (no change) | 0.2500 |
| Total Brier | 0.2664 | 0.2665 | 0.2664 | no change | 0.2498 |
| Margin RMSE | 14.65 | 14.53 | 14.54 | | 14.17 |
| **2026-27 to date, 59 games** | | | | | |
| Winner Brier | 0.2234 | 0.2033 | **0.1999** | −0.0405 to −0.0064 | 0.1943 |
| Spread Brier | 0.2542 | 0.2453 | 0.2450 | −0.028 to +0.009 | 0.2497 |
| Margin RMSE | 14.23 | 13.49 | 13.49 | | 13.38 |

- *Score effects on their own:* better for winners (Feb–Apr 0.1807 → 0.1761, CI −0.0063 to −0.0029) but **worse for spreads** (0.2563 → 0.2587, CI +0.0012 to +0.0037). On top of player ratings they still help winners (0.1780 → 0.1727) and cost spreads a little (0.2548 → 0.2563). Against the original model, spreads come out level.
- *Why spreads get worse:* a sharper, more realistic margin distribution turns the model's disagreement with the spread into more confident calls, and that disagreement carries no information.
- *Whole 2025-26 season:* winner Brier 0.2030 → 0.1987 (market 0.1948). Winners picked right: 687 → 684 of 974 (market favourite 676). The gain is in how confident the model is, not in which side it picks.
- *Monday Nov 2 alone:* 12 → 11 of 15 winners (market favourite 10). One game flipped, which is noise at 15 games.

**Calibration of winners, 2025-26 (model favourite's stated probability vs how often it won):**

| Bucket | Before: said / won | After: said / won | Market said (after's games) |
|---|---|---|---|
| 50–60% | 54.9 / 62.2 | 55.0 / 59.4 | 56.6 |
| 60–70% | 64.5 / 67.2 | 65.0 / 67.7 | 67.5 |
| 70–80% | 74.3 / 83.1 | 74.7 / 80.0 | 78.2 |
| 80%+ | 84.1 / 89.0 | 85.2 / 87.0 | 86.7 |

**Against the market:**
- *Gap:* on the held-out games the winner Brier gap halves, from +0.016 to +0.008, but the market is still better.
- *Disagreement with the line:* its weight is still about 0 (winners +0.07 ± 0.28, spreads −0.02 ± 0.24, totals −0.08 ± 0.15). The PLAY rule still passes every game.

**Not re-measured on the new engine:** the most-likely-game backtest and the player-layer calibration. Fewer simulated blowouts mean slightly fewer garbage-time minutes for starters. The garbage-time rule was fitted on minutes by final margin, so it should carry over.
