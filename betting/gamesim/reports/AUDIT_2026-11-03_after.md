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
