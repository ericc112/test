# Prop-betting analyst kit

This kit has three parts:
- **A refined analyst playbook**: `ANALYST_PROMPT.md`, v2 of the original prompt, with a hit-rate mode for pick'em.
- **Binding lessons from past mistakes**: `LESSONS.md`.
- **A small Python package** (`edge/`) that prices props, builds pick'em entries, grades bets automatically and learns from the results.

Requirements: Python 3.10+ and numpy. Run every command from this `betting/` directory.

## Daily loop
```bash
python -m edge report        # where we stand: CLV, skill vs market, ROI, calibration, misses
python -m edge grade         # settle pending bets from MLB Stats API / NHL API / ESPN / bo3.gg
python -m edge learn         # refit blend + segment biases, update avoid list, append LESSONS.md
python -m edge tag 14 "role/lineup"   # root-cause any high-confidence miss
```

Pricing helpers:
```bash
python -m edge prob --model .65 --market .60 --hist .80 --hist-n 15 --segment cs2:cs_headshots_m12:under
python -m edge breakeven
python -m edge squad --means 245 283 207 --sds 70 78 65 --milestones 807 977 1044 --pair-corr 0 1 0.3
python -m edge add sport=mlb event_id=849812 player="Logan Henderson" player_id=701656 \
    market=pitcher_outs line=15.5 side=under p_model=.58 p_market=.567 p_hist=.526 hist_n=19
```

## How the probability is built (`edge/blend.py`)
Three sources are combined on the logit scale:

```
final = sigmoid(intercept + w_model·logit(model) + w_market·logit(market) + w_hist·logit(history) + segment_bias)
```

- **model**: your simulation. `model_bias_logit` corrects known systematic gaps for that market type.
- **market**: the no-vig sportsbook probability.
- **history**: the player's hit rate at the line, regressed toward the market by n/(n+10).

Missing sources hand their weight to the ones present. Confidence comes from the agreement rule:
- **High**: all sources on one side, ≥ 62%, spread ≤ 12 pts, history n ≥ 10.
- **Medium**: sources agree, ≥ 2 sources, ≥ 56%.
- **Low**: everything else, including any single-source estimate.
- **Avoid**: the segment is on the losing-history list.

## How it learns (`edge/learn.py`)
| Step | What it does | Guard against overreacting |
|---|---|---|
| Blend refit | Penalized logistic regression of outcomes on the three logits | Pulled toward a fixed prior (strength 25 bets); refit from the prior every run so results are never double-counted; needs ≥ 10 graded bets with model + market |
| Segment bias | One-step logistic correction per `sport:market:side` after the blend | Shrunk by n/(n+30), clipped to ±0.4 logit, needs ≥ 5 bets |
| Avoid list | Segment ≥ 20 bets, hit rate > 8 pts under prediction, z < −2 | Sticky; remove by hand once fixed |
| Lessons | Material changes are appended to `LESSONS.md`; tagged misses are tallied | Two same-cause misses mean a new checklist rule |

## Files
| Path | Purpose |
|---|---|
| `ANALYST_PROMPT.md` | v2 system prompt: two modes, three-source probability, robustness tests, learning loop |
| `LESSONS.md` | Checklist rules from real mistakes, plus an auto-learned section |
| `data/bets.csv` | Every evaluated prop (bets, leans, passes), with components and p_final |
| `data/adjustments.json` | Learned blend weights, model/outcome biases, avoid list, gates |
| `edge/odds.py` | De-vig (multiplicative/power), fair odds, EV, quarter-Kelly with 2% cap |
| `edge/pickem.py` | Break-evens, correlated entry odds (Gaussian copula), best-entry search, Squad Ride milestones |
| `edge/grade.py` | Auto-grading by `sport` + `market` (see the stat keys at the top of the file) |
| `tests/test_edge.py` | `python -m unittest discover -s tests` |

## Market keys the grader understands
- **mlb** (`event_id` = gamePk, `player_id` = MLBAM id): `pitcher_strikeouts`, `pitcher_outs`, `pitcher_hits_allowed`, `pitcher_earned_runs`, `pitcher_walks`, `pitcher_pitches`, `first_inning_pitches`, `batter_hits`, `batter_walks`, `batter_strikeouts`, `batter_total_bases`, `batter_home_runs`, `batter_singles`, `batter_hrr`
- **nhl** (`event_id` = NHL gameId, `player_id` = NHL id): `skater_sog`, `skater_points`, `skater_goals`, `goalie_saves`
- **nfl** (`event_id` = ESPN event, `player_id` = ESPN athlete id): `pass_yds`, `pass_att`, `rush_yds`, `rush_att`, `rec_yds`, `receptions`, `anytime_td`
- **cs2** (`event_id` = bo3.gg match id, `player_id` = nickname): `cs_kills_m12`, `cs_headshots_m12`

## Limitations
- Entry grading assumes power-style entries, where every leg must hit. Flex and Squad Ride payouts need manual entry for now.
- Fantasy-point props have no grader yet, because scoring differs by app.
- Calibration is meaningless until roughly 50–100 graded bets. Until then the priors dominate by design.
