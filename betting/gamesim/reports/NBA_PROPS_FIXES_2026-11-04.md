# NBA prop pipeline: the eight fixes, with evidence (2026-11-04)

## How this was tested

No NBA prop legs had been graded yet (the first 120 were logged tonight). So every fix was tested on a walk-forward
backtest corpus (`edge/nba_backtest.py`):

- **Games:** every 2026-27 game from the first day with 20+ prior games (79 games, Oct 25 – Nov 3).
- **Inputs:** re-simulated with only what was known before tip: ratings and player profiles to the day before, the
  same engine and player layer as the live pricer.
- **Joins:** DraftKings' pre-tip lines from ESPN's feed (31,819 items; `edge/nba_dk_hist.py`), with sides matched to
  the milestone price, and the box score.
- **Size:** 7,278 legs, 5,312 with a de-vigged DraftKings price.
- **Fitting rule:** every fitted number for day d used days before d only. Judgments use the last 7 days (Fix 1) or
  every day with 300+ earlier legs (4,801 legs, 9 days).
- **Availability:** "perfect" means who sat is known (the gamesim backtest convention). "Live-like" means only
  players who also missed the previous game are known out, so late scratches stay in the rotation, as they do live.
- **What's proven vs pending:** backtest evidence is retrospective. The live rule (shadow until 200+ graded legs or
  14 days) runs from tonight, so v2 is a shadow, not published.

## 1. What caused the simulation tilt

Measured on the corpus, one change at a time (`data/nba_bt/fix1_experiments.json`). There were three causes, plus
one thing that wasn't the simulation.

| Cause | Effect | Evidence |
|---|---|---|
| **Minutes exponent 0.8** (introduced Nov 4 on a minutes-error test) | moved ~1.2 min/game from starters to the bench | starters' over rate 2.0 pts below actual and bench 2.7 above; at 1.0, both within 1 pt (+0.8 / +0.5); simulation log loss 0.7043 → 0.7015 |
| **Live availability** | players who end up not playing keep minutes in the live rotation | live-like vs perfect: starters' minutes bias +0.41 → −0.54; starter gaps widen by 0.10–0.15 logit; it reproduces most of tonight's live board tilt |
| **DraftKings' overs** | the de-vigged over runs high | on 5,312 main lines DraftKings priced 48.6% overs, 46.7% went over (−0.08 logit); starters' points in the last 7 days: DraftKings ~6 pts above the result |
| Garbage time | a smaller pull on starters | off: starters' over rate +2.4 pts, log loss −0.0006; halved or off overshoots, so it stays |

**Not the leak (props unchanged when switched off):**
- the 0.50 injury price;
- the 59% player-rating move;
- the head-to-head multiplier;
- score effects (off made props slightly worse).

**The last-season prior** is the most valuable single parameter: removing it costs +0.022 log loss.

**Shape:**
- The simulated range is too wide: 59% of results fall inside the 25th–75th percentile against 50%.
- The median is too low: 42% of results fall below it against 50%.
- Narrowing the role swing makes log loss worse, because the width is absorbing projection error. It stays.

**A further defect found on the way (Fix 6):**
- Problem: each player's shots, rebounds and assists swung independently, so the simulated points–assists
  correlation was 0.03 against a real 0.18, and points–rebounds 0.11 against 0.28. 56–57% of players were off by
  more than 0.15.
- Fix: a shared swing component (ρ = 0.8) brings them to 0.15 and 0.27, with 25–26% of players off. Prop log loss
  is unchanged-to-better (0.7009).

**Fix 1 acceptance** (raw gap vs DraftKings within ±0.10 logit on the last 7 days, every stat × segment):

| Corpus | Cells within ±0.10 of DraftKings | Cells within ±3 pts of the actual over rate |
|---|---|---|
| v1 simulation, perfect availability | 2 / 16 | 10 / 16 |
| v2 simulation, perfect availability | **13 / 16** | 8 / 16 |
| v2 simulation, live-like availability | 9 / 16 | 11 / 16 |

- **Starter cells:** they fail only against DraftKings, and only where its starter overs run high. Under live-like
  availability, starters' points simulate +2.2 pts above the actual over rate but −0.18 logit below DraftKings.
- **The conflict:** forcing the simulation onto DraftKings there would move it away from what happened. The residual
  bias is now a small segment table (pts −0.18 starters / −0.08 bench; reb ≈ 0; ast −0.25 / −0.11), fitted on
  earlier days and shrunk n/(n+50) toward the stat-wide value.
- **The live gap:** the remaining live-only gap is availability. It's handled by re-pricing inside the last hour
  before tip (Fix 4), not by a number.

## 2. The fixes: before and after

Held-out walk-forward legs, identical for both, live-like availability (`data/nba_bt/final_eval.json`):

| | Before (v1, published) | After (v2, shadow) | DraftKings alone |
|---|---|---|---|
| Over-side log loss | 0.6908 | **0.6864** | 0.6876 |
| Over-side Brier | 0.2488 | **0.2466** | 0.2472 |
| Picked-side log loss / Brier | 0.6908 / 0.2488 | 0.6863 / 0.2466 | |
| Simulation alone, log loss | 0.7087 | 0.7041 | |
| Average miss of the projection (DraftKings line: 3.83) | 3.96 mean / 3.95 median | 3.95 / 3.92 | |
| After − before, log loss | | −0.0045 (95% CI −0.0065 to −0.0024) | |
| After − DraftKings, log loss | | −0.0012 (CI −0.0026 to +0.0002) | |

- **Fix 2 (blend).**
  - Model weights 0.2 / 0.3 / 0.45 were tested; 0.2 wins (0.6864 vs 0.6867 vs 0.6883).
  - History adds nothing, raw or minutes-aware, so its weight is 0.
  - The +0.046 intercept is dropped.
  - A missing DraftKings price now counts as 50% instead of handing the model the market's weight.
  - The new blend beats the old one clearly. It beats DraftKings alone by an amount the CI can't separate from zero,
    so per the acceptance rule it ships market-dominant (model 0.2 / market 0.8) and says so.
  - Nightly per-component skill tables are in the report (`edge/nba_report.py`).
- **Fix 3 (picked side).**
  - The old blend shows the winner's curse: 55–60% legs hit 53.5%, and 70%+ legs hit 68.4% on 74.4% predicted.
  - Platt scaling, walk-forward, made held-out log loss worse (0.6860 → 0.6868), so by the shadow rule it isn't
    used. A 70% cap is used instead.
  - The ENTRY rule is now recalibrated p − break-even > 1 standard error (blend-weight uncertainty ±0.1 plus Monte
    Carlo error).
- **Fix 4 (market).**
  - The feed carries one milestone per line, not DraftKings' ladder, so the market-shape test was replaced by a shape
    test against results (above).
  - Side-match audit on 10,396 lines: 73% have a milestone at the line, the chosen over equals it exactly (median gap
    0.0), and 5 asymmetric pairs were ambiguous (0.07% against the 2% bar). The other 27% get no market input, as before.
  - Every DraftKings pull is now snapshotted for closing line value (`edge/nba_clv.py`, nightly).
  - verify FAILS market data older than 60 minutes inside the last hour before tip. The pre-tip run moved to
    6:07 / 9:07 pm ET.
- **Fix 5 (labels).** Covered in section 4. The early-season High lockout is removed because thin-history High legs
  didn't underperform (61 legs, 64.6% predicted, 65.6% real).
- **Fix 6 (pricing correctness).**
  - Push: whole-number market lines now exclude the push like the model and history (v1 counted half the push as an over).
  - Goblins and demons: the partner API doesn't publish their multipliers, so they can't be ENTRY legs until the
    app's multiplier is entered. MORE-ONLY standard overs pay standard.
  - Combos: they come from the same simulated box scores; the correlation fix is above.
  - Parameters: inventory and sensitivity in `PARAMETERS.md`. The top three are the last-season prior, the minutes
    exponent and the role swing.
- **Fix 7 (verify).**
  - ENTRY legs reprice and recount within 2 points.
  - Calibration-drift WARN on the trailing 50 published legs.
  - Tilt monitor: past ±0.25 logit blocks ENTRY in that stat until a cause is logged.
  - Same-game entries: joint probability from the simulation's shared runs (`nba_pp.joint_probability`), against the
    entry break-even (2-pick power 1/3, 3-pick 1/5).
- **Fix 8 (learn).**
  - Per-sport blend refits only from 200+ graded legs, at most monthly; the cross-sport blend is frozen.
  - The avoid list needs 50+ legs and the shortfall in both halves of its history. The existing CS2 kill-under entry
    is grandfathered as sticky, per LESSONS L25.
  - Every learned change goes to `data/learn_log.jsonl`.
  - Wednesday legs are a permanent holdout, and headline accuracy is reported on them.

**Shadow mode:** `edge/nba_model.py`.
- v1 publishes, and v2 is scored and logged every night.
- Promotion requires 200+ graded live legs or 14 days, with better log loss AND label calibration. It is checked by
  the daily run, recorded in `data/MODEL_CHANGELOG.md`, and reversible with `python -m edge.nba_model rollback`.

## 3. The model's true edge over DraftKings

- **Probability terms:** the v2 blend's log loss is 0.0012 lower than DraftKings alone. The 95% interval
  (−0.0026 to +0.0002) includes zero, so no edge is proven.
- **The model's disagreement does carry some information:** regressing results on DraftKings plus the model's
  departure gives a weight of 0.23 (CI 0.11–0.35). That is what the 0.2 model weight captures.
- **PrizePicks entries** (v2 ENTRY legs, 102 held out):
  - They hit 62.7% (CI 53.4–72.1%) against the 57.7% two-pick break-even. That is +18% at 2-pick power on the point
    estimate, and negative at the low end of the interval.
  - The source is mostly the market: these are lines DraftKings juices to one side while PrizePicks pays flat. It
    holds only where PrizePicks posts DraftKings' line (the corpus used DraftKings' lines).
- **Not proven yet.**

## 4. The recalibrated label table (held-out legs)

| Label | Before: legs, predicted, realized | After: legs, predicted, realized |
|---|---|---|
| High | none possible (history n ≥ 10 lockout) | 102, 64.7%, 62.7% (−2.0) |
| Medium | 899, 61.8%, 59.0% (−2.8) | 1,137, 57.0%, 60.3% (+3.3) |
| Low | 3,902, 53.9%, 51.5% (−2.4) | 3,562, 52.2%, 52.4% (+0.3) |

Every v2 label is within ±5 points (Fix 5 acceptance).

**Calibration buckets (Fix 3 acceptance, ±4 pts):**
- 55–60%: +3.6
- 60–65%: +0.9
- 65–70%: −1.5
- 70%+: 10 legs at the cap, 60% realized: fails on 10 legs and can't be judged until more arrive.

## 5. What remains, and what would unblock it

- **Live-shadow proof.** v2 is not published until 200+ graded live legs or 14 days beat v1. At ~120 legs a night,
  that's about two nights.
- **Availability before tip.** Historical injury reports would let the backtest model questionable players instead of
  the late-scratch proxy. Until then, re-pricing in the last hour before tip handles it live.
- **DraftKings' over shading.** It needs 100+ graded legs per stat of closing line value to decide whether to correct
  the market itself.
- **The simulated range is too wide.** It needs a better minutes projection; narrowing alone hurts.
- **Market shape from milestones.** It needs a source with DraftKings' full milestone ladder; ESPN carries one rung.
- **PrizePicks lines in the backtest.** It needs historical PrizePicks boards, which aren't available; DraftKings'
  lines were used.
- **Goblin and demon payouts.** They need the multipliers shown in the app.
- **Per-stat label tables and CLV flags.** They fill in from graded legs; the nightly report carries them permanently.
