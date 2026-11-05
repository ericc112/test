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
