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
| `gamesim/` | One-game NFL model: ridge EPA ratings, drive-by-drive clocked simulation, out-of-sample backtest, error bars and decision rule (`python -m gamesim --game ID`) |
| `edge/nfl.py` | NFL game simulator (drives → points → volume → shares → per-play yards), DraftKings-line pricing, backtest |
| `edge/review.py` | Post-mortem for every loss: feed detail, linked legs, suggested root cause |
| `edge/card.py` | One leg per game script, best entry, entry-leg pricing check |
| `data/postmortems.csv` | One diagnosis per loss, with the lesson recorded for it |
| `POSTMORTEMS.md` | Readable post-mortem log, grouped by date and independent cause |
| `tests/test_edge.py` | `python -m unittest discover -s tests` |

## Market keys the grader understands
- **mlb** (`event_id` = gamePk, `player_id` = MLBAM id): `pitcher_strikeouts`, `pitcher_outs`, `pitcher_hits_allowed`, `pitcher_earned_runs`, `pitcher_walks`, `pitcher_pitches`, `first_inning_pitches`, `batter_hits`, `batter_walks`, `batter_strikeouts`, `batter_total_bases`, `batter_home_runs`, `batter_singles`, `batter_hrr`
- **nhl** (`event_id` = NHL gameId, `player_id` = NHL id): `skater_sog`, `skater_points`, `skater_goals`, `goalie_saves`
- **nfl** and **cfb** (`event_id` = ESPN event, `player_id` = ESPN athlete id): `pass_yds`, `pass_att`, `completions`, `pass_td`, `pass_int`, `rush_yds`, `rush_att`, `rec_yds`, `receptions`, `rush_rec_yds`, `anytime_td`
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

## NFL game simulator (`edge/nfl.py`)
```bash
python -m edge nfl --week 9                         # games, ESPN event ids, DraftKings spread/total
python -m edge nfl --event 401873037                # 50,000 simulations, every DraftKings prop line priced
python -m edge nfl --event 401873037 --alt "Henry:rush_yds:72.5" --log   # price an app line; log every prop
python -m edge nfl --backtest 3-8                   # replay finished weeks against DraftKings closing lines
```
**One simulated game:**
- **Drives.** About 10 per team. Each ends in a TD, a FG or nothing, at rates solved so expected points equal the DraftKings implied team total. That gives points, margin and each team's opening drive.
- **Volume.** Plays and dropback rate shift with the simulated margin, at slopes fitted on this season (a team leading by 14 drops back about 7 points less).
- **Shares.** Targets and carries come from the games each player played for this team, recency-weighted. Each game they wobble (Dirichlet) and split by multinomial. Inactive players' volume goes to their teammates.
- **Yards and TDs.**
  - Each catch is a Gamma draw and each carry a shifted Gamma, scaled by the opponent and by a team efficiency shock tied to its scoring.
  - QB yards are the sum of his receivers' yards; INTs are a Binomial draw.
  - Each TD goes half by this game's work and half by season TD share.
- **Who plays.** The injury report (Out/Doubtful) removes players. A player DraftKings posts a prop for counts as active, which is how a back-from-injury player re-enters before he has a box score. A listed player with no 2026 games gets a role read off his line so his teammates' shares are right, but he is never priced.

**What the backtest says (2026 weeks 3–8, 5,354 DraftKings closing props, only earlier games used):**

| | Simulation | DraftKings line |
|---|---|---|
| Avg miss, receiving yards | 22.6 | 20.8 |
| Avg miss, rushing yards | 19.5 | 18.0 |
| Avg miss, passing yards | 60.0 | 56.2 |
| Spread of outcomes (PIT sd, ideal 0.289) | 0.28–0.29 on yardage | — |
| Raw "83%" sides at the line | hit 71% | — |
| Calibrated, out of sample (fit wk 3–5, test 6–8) | Brier 0.2488 vs 0.2500; 55%+ leans hit 52.8% of 286 | — |
| Alt lines ±10/20 yds, centred on the DK line | Brier 0.196, buckets within ~5 pts | — |

- **The line is the better centre.** The simulation's medians miss by more than the DraftKings line on every yardage market, and alone it shows no edge over the closing line. That's why `MODEL_SHRINK` pulls its P(over) most of the way to the line before the blend (weight 0.15 on yardage, 0.3 on receptions, 0.5 on pass TDs).
- **The simulation is the better shape.** Use `--alt` to price a PrizePicks or alt line that differs from DraftKings: it re-centres the simulated distribution on the DK line (`anchored_over`).
- **No prices.** The NFL prop feed carries lines but no prices, so there is no market component and no label above Medium.
- **Role flags cap a leg at Low:** back from injury, under 3 games with the team, or a line far from the model (the book likely knows something).

## Sim Lab: the browser simulator (`simlab/index.html`, `edge/simlab.py`)
A published page that runs 50,000 simulations per game in the viewer's browser, so it costs no Claude usage to run.
- **Leagues:** NFL with every player prop (a JavaScript port of `edge/nfl.py`), plus game-level models for college football (drives), NBA and college basketball (margin/total), NHL and soccer (Poisson goals fitted to the no-vig moneyline and total; soccer adds a Dixon-Coles low-score fix), and a custom form for any game, baseball included.
- **What you can watch:** the run counting up to 50,000 with the probabilities converging (±2 SE band); live re-simulation from a score and clock you type in; a simulated game played out event by event, with win probability re-simulated 50,000 times at every event.
- **Data:** the page can't fetch anything itself (artifact CSP), so lines, injuries and NFL player inputs ship in `data.js`. Refresh with:
```bash
python -m edge simlab --out simlab/data.js     # then republish index.html with data.js beside it
```
- **Same honesty as the kit:** the backtest table and the calibration weights ship with the data. Its numbers are model output, not picks: `edge verify` still applies before naming one.

## Limitations
- Entry grading assumes power-style entries, where every leg must hit. Flex and Squad Ride payouts need manual entry for now.
- Fantasy-point props have no grader yet, because scoring differs by app.
- Calibration is meaningless until roughly 50–100 graded bets. Until then the priors dominate by design.
