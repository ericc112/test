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
