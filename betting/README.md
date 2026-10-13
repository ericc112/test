# Prop-betting analyst kit

This kit has three parts:
- **A refined analyst playbook**: `ANALYST_PROMPT.md`, v2 of the original prompt, with a hit-rate mode for pick'em.
- **Binding lessons from past mistakes**: `LESSONS.md`.
- **A small Python package** (`edge/`) that prices props, builds pick'em entries, grades bets automatically and learns from the results.

Requirements: Python 3.10+ and numpy. Run every command from this `betting/` directory.

## Daily loop
```bash
python -m edge report        # where we stand: CLV, skill vs market, ROI, calibration, misses
python -m edge grade         # settle pending bets from MLB Stats API / NHL API / ESPN / bo3.gg; post-mortem each new loss
python -m edge review        # post-mortem any loss without one (--all re-diagnoses, --accept records suggested tags)
python -m edge tag 14 "opportunity" --lesson "pulled at 75 pitches"   # confirm the cause of every loss
python -m edge learn         # refit blend + segment biases, avoid list, Medium caps, append LESSONS.md
python -m edge verify 46 45           # back-check picks before publishing (also --open, --refresh, --fix)
python -m edge best --date 2026-10-12  # High legs >= 65%, one per game script, best 2-leg entry
python -m edge card --date 2026-10-12  # same-script legs, and any leg unpriced or under break-even (--breakeven .577)
```

Pricing helpers:
```bash
python -m edge prob --model .65 --market .60 --hist .80 --hist-n 15 --segment cs2:cs_headshots_m12:under
python -m edge breakeven
python -m edge passes --player 393432 --team 175 --opp 2250 --line 50.5 --home   # soccer passes attempted (ESPN ids)
python -m edge squad --means 245 283 207 --sds 70 78 65 --milestones 807 977 1044 --pair-corr 0 1 0.3
python -m edge add sport=mlb event_id=849812 player="Logan Henderson" player_id=701656 \
    market=pitcher_outs line=15.5 side=under p_model=.58 p_market=.567 p_hist=.526 hist_n=19 proj=14 opp_proj=19
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
- **High**: all sources on one side, ≥ 65%, spread ≤ 12 pts, history n ≥ 10, and a sportsbook price or 20+ games of history within 10 pts of the model. Never High without a price where the model needs a big correction (L19), or in a segment capped by `learn`.
- **Medium**: sources agree, ≥ 2 sources, ≥ 58%.
- **Low**: everything else, including any single-source estimate.
- **Avoid**: the segment is on the losing-history list.

## How it learns (`edge/learn.py`)
| Step | What it does | Guard against overreacting |
|---|---|---|
| Blend refit | Penalized logistic regression of outcomes on the three logits | Pulled toward a fixed prior (strength 25 bets); refit from the prior every run so results are never double-counted; needs ≥ 10 graded bets with model + market |
| Segment bias | One-step logistic correction per `sport:market:side` after the blend | Shrunk by n/(n+30), clipped to ±0.4 logit, needs ≥ 5 bets |
| Avoid list | Segment ≥ 20 bets, hit rate > 8 pts under prediction, z < −2 | Sticky; remove by hand once fixed |
| Post-mortems | Every loss: feed detail, volume vs projection, sources, same-script links, suggested tag (`review.py`) | Root cause confirmed by hand; `variance` and `correlated` never trigger rules |
| Medium caps | Segment with 3+ losses from the same fixable cause and hitting below prediction gets no High legs | Recomputed every run, so the cap lifts once results recover |
| Lessons | Material changes are appended to `LESSONS.md`; 2 same-cause losses in a segment are flagged once | A flagged cause means writing a new checklist rule |

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
| `edge/verify.py` | Pre-publish back-check: recompute, recount at the prop's unit, re-price, line offered, lesson rules, correlation |
| `edge/lol.py` | LoL maps 1-3 kills: gol.gg games (current season), bo3.gg series odds, series-level history |
| `edge/pp.py` | PrizePicks board fetch and routing to pricers; More-only and goblin/demon handling |
| `edge/cs2.py` | CS2 maps 1-2 kills/headshots model from bo3.gg, with roster-era detection and newcomer flags |
| `edge/soccer.py` | Soccer passes attempted: possession × match passes × share × minutes, from ESPN |
| `edge/review.py` | Post-mortem for every loss: feed detail, linked legs, suggested root cause |
| `edge/card.py` | One leg per game script, best entry, entry-leg pricing check |
| `data/postmortems.csv` | One diagnosis per loss, with the lesson recorded for it |
| `POSTMORTEMS.md` | Readable post-mortem log, grouped by date and independent cause |
| `tests/test_edge.py` | `python -m unittest discover -s tests` |

## Market keys the grader understands
- **mlb** (`event_id` = gamePk, `player_id` = MLBAM id): `pitcher_strikeouts`, `pitcher_outs`, `pitcher_hits_allowed`, `pitcher_earned_runs`, `pitcher_walks`, `pitcher_pitches`, `first_inning_pitches`, `batter_hits`, `batter_walks`, `batter_strikeouts`, `batter_total_bases`, `batter_home_runs`, `batter_singles`, `batter_hrr`
- **nhl** (`event_id` = NHL gameId, `player_id` = NHL id): `skater_sog`, `skater_points`, `skater_goals`, `goalie_saves`
- **nfl** and **cfb** (`event_id` = ESPN event, `player_id` = ESPN athlete id): `pass_yds`, `pass_att`, `rush_yds`, `rush_att`, `rec_yds`, `receptions`, `anytime_td`
- **cs2** (`event_id` = bo3.gg match id, `player_id` = nickname): `cs_kills_m12`, `cs_headshots_m12`
- **soccer** (`event_id` = ESPN event, `player_id` = ESPN athlete id; any league): `passes_att`, `gk_saves`, `shots`, `sot`, `tackles`, `fouls`. A player who doesn't play is voided, as the apps do.

## Price a PrizePicks board (`edge/pp.py`)
```bash
python -m edge pp --league CS2                       # every standard CS2 prop, ranked by final probability
python -m edge pp --league CS2 --match Liquid --log  # one match, and log each priced prop to bets.csv
python -m edge pp --league UCL --match Inter --types standard,goblin,demon
```
- **Board source:** the PrizePicks partner API, which needs no captcha. Responses are cached for 2 minutes, with backoff when it rate-limits (429).
- **More-only lines:** goblins, demons and some standard lines only allow More. They're marked `MORE-ONLY` and priced on the over side only.
- **CS2 maps 1–2 kills and headshots** (`edge/cs2.py`, bo3.gg):
  - The map winner is drawn from the series moneyline.
  - Rounds come from each team's maps with that result.
  - Each player has a kill rate for map wins and one for map losses, plus a headshot rate. The current roster means maps with at least 4 of today's 5.
  - Players new to the team, or with fewer than 8 maps on it, are flagged and capped at Low (L5).
  - Finished games are cached in `.cache/`.
- **Soccer** (ESPN + DraftKings):
  - Passes attempted use the passes model below.
  - Shots, shots on target and keeper saves use the DraftKings milestone ladder, fitted to a Poisson with about 7% hold removed, plus the player's last 10 matches.
  - A missing ladder usually means DraftKings doesn't expect him to start. A keeper with no ladder borrows his team's listed keeper.
- **Not priced yet:** other stats and leagues are listed as unpriced.
- **Output:** a ranked table, then the best 2-leg entry from High legs in different matches, or "sit out".

## Soccer passes attempted (`edge/soccer.py`)
```bash
python -m edge passes --player 393432 --team 175 --event 401915418 --line 50.5   # ESPN ids; --opp/--home without an event
```
**player passes = team passes × his share per 90 × minutes**, and **team passes = possession × 100 × team passes per possession point × opponent press factor**.

| Factor | How it's measured | Why |
|---|---|---|
| Possession | Half stats (log5 of both teams' recent possession, ±2 pts home), half market (0.5 + 0.21 × (P(win) − P(loss)) − 0.02 home, from the DraftKings 3-way line) | The blend beats either alone: 6.8 pts error vs 7.2 stats-only, 9.5 for 50/50 |
| Team tempo | The team's passes per point of possession | Some teams pass more with the same share of the ball |
| Press / defensive block | Passes the opponent allows per point of possession, vs its league | A high press or compact block cuts passes per minute on the ball |
| Game script | Result drawn from the 3-way line; winners end ~2.9 pts below forecast possession, losers ~2.9 above | Teams that lead sit deeper |
| Share and minutes | His passes ÷ team passes per 90 over recent starts; minutes drawn from those starts | Captures role and sub risk |
| Spread | Team passes ±19% (forecast error) × share ±14.5% × Poisson | Calibrated on 190 starter-matches (PIT sd 0.284, ideal 0.289) |

The backtest covered 250 top-four-league matches, using each team's other matches only. Team-pass error was 70.6, against 74.2 for possession × tempo and 81.1 for the team average.

It also flags a team that played 3 or fewer days ago (rotation risk). Confirm the lineup about an hour before kickoff.

## Limitations
- Entry grading assumes power-style entries, where every leg must hit. Flex and Squad Ride payouts need manual entry for now.
- Fantasy-point props have no grader yet, because scoring differs by app.
- Calibration is meaningless until roughly 50–100 graded bets. Until then the priors dominate by design.
