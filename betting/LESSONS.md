# Lessons (binding checklist rules)

Each lesson came from a real mistake or near-miss. Before publishing a number, check every rule. `python -m edge learn` appends auto-learned items at the bottom.

| # | What happened (2026-10-12) | Root cause | Rule now enforced |
|---|---|---|---|
| L1 | Traded hitters (Adell, Lowe, Bailey, Hicks, Mateo) showed one team's season stats | Stats feed returned per-team splits; the last one overwrote the season total | Use combined-team totals only (team = none); check PA sums |
| L2 | Prop over/under sides were assumed from list order | Feed has no side label | Verify the side against the "N+" milestone price before using any prop |
| L3 | sml showed a 100% probability | Kill share divided by team kills on maps he didn't play | Rates only over games/maps the player played. Any p > 95% or < 5% is a bug until proven otherwise |
| L4 | Recommended Bo Nix to Squad Ride for rushing upside; the contest scored **passing yards** | Didn't read what the contest scores | Confirm the scored stat, line type, push rules and multipliers before choosing players |
| L5 | Hartman under (role cut) was recommended, then line projections showed him at 2C/PP2 | Role-change thesis without lineup confirmation | Role-change edges stay LEAN until lines, batting order or inactives confirm them |
| L6 | Many NHL/MLB props showed 9–12% "edges" against DraftKings | Model error read as edge; Gritsyuk's ice-time demotion was already priced | Halving test: an edge must survive being shrunk halfway to the market |
| L7 | Hitter model ran +3.6 pts above market on hits overs across the board | Postseason bullpens and run environment not modeled | Measure model-vs-market bias per market type every scan; apply `model_bias_logit` |
| L8 | CS2 ex-Keyd overs (raw) flipped to unders after opponent adjustment | Raw stats came against weak opponents | Raw-vs-adjusted test: pass when they disagree on the side |
| L9 | User asked "why the favorite's player under?" Map winner effect was under-modeled at first | Team kills/round differ by map result (~3.9 winner vs ~2.9 loser) | Simulate map/game winners explicitly; show conditional hit rates by result |
| L10 | PrizePicks "last 5" chart (3/5 over) suggested More on 1st-inning pitches; full season was 9/19 | Recency-cherry-picked display | Always use full season plus simulation; app charts are not evidence |
| L11 | App showed 5:00 PM for a game MLB lists at 8:00 PM ET | App time zone/display error | Take lock time from the official schedule |
| L12 | A $100 entry was built on a $239 balance (42%) | No stake check in the flow | Flag any entry > 2% of bankroll before discussing picks |
| L13 | Griffin outs 12.5 vs 13.5 were treated as meaningfully different | Exits cluster at inning boundaries | Value alt lines by the mass at exact values (13 outs: 1 of 31 starts) |
| L14 | Conflicting odds in search summaries (LAD −110/MIL −102 at one source) | Summaries/pages can be wrong or stale | Use primary feeds for prices; record pull time |
| L15 | Henderson K under 5.5 was offered at ~55% while his history said over in 12 of 18 starts | History source not checked | Three-source agreement rule: model, market and history must agree for Medium/High |
| L16 | Yamamoto was pulled after 2.2 IP / 75 pitches; one blow-up sank four legs (his outs over, pitches over and ER under, plus Yelich's H+R+RBI under: 3 of his 4 came off Yamamoto) | Correlation was checked per pair, never across the whole card | Cap total exposure to any single game script (e.g. "starter dominates") at 2% of bankroll across all entries; list each card's scripts before adding legs |
| L17 | Yamamoto outs over rated ~69% partly on 18+ outs in 26/29 regular-season starts; in the playoffs the Dodgers hooked him at 75 pitches | Regular-season leash history overstates playoff leash (deep, rested bullpens; must-win games) | In the postseason, shrink outs/pitch-count history halfway toward the market and cap starter-length props at Medium. Second case 2026-10-12: Griffin pulled at 12 outs on 63 pitches. In hit-rate mode, no postseason starter outs/pitches overs at all |
| L18 | Rasmussen hits-allowed U4.5 (~59%, Medium) gave up 4 hits to the first 7 batters vs a low-strikeout Cleveland lineup | Hits model used his overall H/BF with a light opponent tweak; ignored that low-K opponents put more balls in play; single-game hits are BABIP-luck heavy | Model hits allowed as BF × (1 − K% − BB%) × hit-rate-on-contact with opponent contact rate; cap hits-allowed unders at Medium and never play them vs bottom-third-K% lineups in hit-rate mode |
| L19 | David Hamilton H+R+RBI U1.5 was rated High (68%) with no sportsbook price; he reached base 4 of 4 and 3 of his 5 came off the bullpen | Our H+R+RBI model runs ~7.6 pts toward unders (needs a -0.31 logit fix), and with no market nothing checked it | A segment whose model needs a correction of 0.25 logit or more can't be High without a sportsbook price (enforced in `blend.py`) |
| L20 | Yamamoto ER U1.5 sat in a $50 Boom entry while we priced that side at 47% (we had the over at 55%) | Entry legs weren't run through the model before submitting | Price every leg of an entry before it's submitted; `python -m edge card` flags any leg that is unpriced or under the entry's break-even |
| L21 | CS2 favourite-player kill unders lost in stomps: divine U29.5 had 32 (LP 13-5, 13-11), SkulL U30.5 had 32 and ju1ces U30.5 had 35 (Rooster 13-3, 13-6 over Fruju) | The model uses a player's average kills per round in map wins; in blowouts the winning side's stars frag closer to 1 per round, which outweighs the shorter maps | When a team is 65%+ per map, its players' kill unders are capped at Medium and never go in hit-rate entries; headshot unders survived (SkulL HS U15.5 won) because HS% doesn't rise in stomps |
| L22 | H+R+RBI unders lost on late bullpen innings: Ramirez 5 of 6 off the bullpen, Adell 3 of 3 (2-RBI double in the 9th), Turang and Hamilton earlier | The hitter model treats late relief innings as average; postseason middle relief and blowout arms gave up most of the damage | Segment is capped at Medium by `edge learn` (50% vs 57% predicted over 12); no H+R+RBI unders in hit-rate entries until it recovers |
| L23 | Cuzz U10.5 (LoL maps 1-3 kills) was labelled High with history "80% of 40"; counted by series it was 13 of 20 (65%), which drops it to Medium | History was counted per game (or from simulated blocks), not at the unit the prop settles on | Count history at the prop's own unit: series totals for "maps 1-3" props, maps 1-2 totals for CS2, games for single-game props. Never per-game rows for a multi-game prop |
| L24 | In one night: Cuzz and Tangyuan published as High on per-game history, a model number mistyped into a blend (0.78 for 0.728), malbsMd U32 recommended when PrizePicks only offered the over, labels left stale after the weights changed | Picks went out on a single pass, with numbers copied by hand and nothing re-derived | Every pick passes `edge verify` before it is named: recompute, recount from raw data at the prop's unit, re-price on current odds, line offered, lesson rules, correlation. NOT VERIFIED means not published |
| L25 | CS2 maps 1-2 kill unders hit 7 of 20 (35%) against 59% predicted over 2026-10-12/13. One overtime map (Ancient, 30 rounds) sank six unders at once; three losses were tagged `model bias` | The model treats overtime as rare, and it leans on kill-per-round rates that run low for players who are good in close maps | The segment is on the AVOID list and capped at Medium. No CS2 kill unders until the model prices P(overtime) × 6+ extra rounds explicitly and a fresh 20-bet sample lands within 5 pts of prediction |
| L26 | A tout's post (2026-11-02 MNF) showed "50,000-run" sim averages within a few yards of the box score and a ✅ on every pick, including 76% and 71% on WR overs | A list of post-game winners is not a track record. It hides the losses and the number of picks; one game's result is mostly noise (receiving yards have an sd of ~35); 50,000 runs shrink simulation error, not model error. Our own 50k sim, backtested on 5,354 DraftKings closing props, missed by more than the line and showed no edge alone | Judge a model only by calibration and Brier against closing lines over hundreds of props (`edge nfl --backtest`, `edge report`). Never quote a single game's hits as accuracy. Any side above ~60% against a fair DraftKings line is a bug or missing news until a price confirms it |
| L27 | A tout's NBA write-up (2026-11-04, Keldon Johnson o3.5 reb) rested on 7/7 this season, 5/5 vs DAL, 6+ in 4 of the last 5, and "Dallas allows 43.1 rebounds" | Hit rates against tonight's line are already in the line. Tested on 2,330 DraftKings lines with prices (2026-27): season and last-5 hit rates carry no weight beyond the no-vig price (−0.08 ± 0.11, −0.06 ± 0.11); players over in 80–100% of their last 5 went over 39% (84 lines) vs 50% priced. His 5/5 vs DAL was 8.8 reb per 36, his normal 8.7. Dallas's 43.1 was 20th of 30, below the league's 44.2 | Never cite a hit rate, streak or head-to-head record as a reason for a side. Read head-to-head as per-36 against his own rate (the Sim Lab research card does), and the opponent's allowed numbers with their rank. Only head-to-head improved projections in the fair test (~0.1%, already in the sim via `nba_research.H2H_COEF`) |
| L28 | Nov 4, first graded NBA night: 266 legs hit 45.9% vs 63.3% predicted. Bench overs lost on minutes (Keldon Johnson 19 min vs 25 projected, Sensabaugh 12 vs 17, Beringer 13 vs 25) and starter unders lost on minutes (Derrick White 36 vs 25, SGA 35 vs 31.5). Across the board v1 projected starters 2.8 min short and the bench 2.1 long; 74 of 134 pass losses and 6 of 10 published losses trace to it | v1's minutes exponent 0.8 moved minutes from starters to the bench (found in Fix 1, still published); Beringer's also took minutes freed by Anthony Edwards that went to wings, not to a backup center | v2 (exponent 1.0) promoted 2026-11-05 on 848 graded shadow legs (log loss 0.7121 → 0.6945, label gap 11.6 → 4.4 pts). `edge verify` WARNs when an over is projected 3+ min above his last-5 minutes or an under 3+ below (`minutes` check): such a pick rests on the minutes projection, not his rate. Minutes freed by an absence should go to the same position (open model work) |
| L29 | Isaiah Collier (3 min) and Jaylin Williams (out) had their PrizePicks lines pulled before tip; Collier's lean still graded as a loss | A pulled or moved line before tip is role or injury news the box scores don't show yet | When `verify` reports a line pulled from the board, withdraw the leg and treat the player's other legs in that game as unconfirmed until the injury report or lineup confirms him |
| L30 | User rule (2026-11-06), for tennis: "only evaluate picks based off aspects that make a difference" — a tennis player's last 5 came against different opponents. NBA, NFL and NHL are excluded at the user's direction ("it matters for basketball"; "revert everything except for tennis"): their lists keep this season, last 5 / last 3, head-to-head, matchup, usage and ice-time reasons and the history-only list, with L27's test result shown beside them. The rule below applies to tennis. The lists still showed season / last-5 hit rates, head-to-head records, opponent allowances and usage, and the most-likely gate dropped legs on them: on the Nov 6 NBA board 117 of 127 dropped legs were dropped only for those | Tested twice. NBA (L27): hit rates and streaks add nothing beyond the price; recent form, opponent allowances and positional allowances add nothing beyond the simulation. Tennis (742 walk-forward matches, line at the simulation's median, fit on one half and scored on the other): recent record +0.02 ± 0.08, last 5 −0.09 ± 0.08, head-to-head (64 matches) −0.36 ± 0.26, average games +0.08 ± 0.08 for total games, all worse out of sample; games won and match winner the same (earlier win rate +0.22 ± 0.11 but unstable out of sample) | A reason counts only if it is a tested input or a real risk: the most likely game, the simulation's median, the sportsbook's price, availability, role and sample flags. Hit rates, streaks, head-to-head records, opponent allowances and usage summaries are never shown as reasons and never drop a leg; there is no history-only list. A new factor (fatigue, opponent-adjusted form, surface type) earns a place only by improving the walk-forward test |
| L31 | Tennis factors 1-3 (2026-11-06): does opponent strength, recent form, fatigue, indoor/outdoor or handedness make the simulation better? Tested walk-forward on the TennisMyLife match database (91,679 matches; tuned Jan 2025 - Aug 2026, scored Sep - Nov 2026) and Tennis Explorer closing odds | Opponent-adjusted serve/return ratings: winner log loss ATP 0.669 -> 0.640 (accuracy 59% -> 65%), WTA 0.666 -> 0.657. The market's winner price beats every model input (ATP 0.608; model and Elo add nothing beyond it: weights -0.03, -0.12 vs 1.22) and, used as the simulation's winner, improves ATP games-won lines 0.686 -> 0.673 (not WTA, 350 matches). Total games at a median line stayed at a coin flip (0.692-0.698) for every version. Heavier recency (half-life 180 days) was worse than 1-2 years; Elo helped only without a market; fatigue (minutes at the event), indoor and handedness made no reliable difference | Tennis ratings are opponent-adjusted; ATP games won and totals take the market's winner price when listed; no fatigue, indoor, handedness or recent-form terms. A tennis total without Dabble's price stays Low: nothing tested predicts it beyond the line |
| L32 | User audit of Collin Murray-Boyles (2026-11-06): the card printed High and "verified" while the simulation and market were 10+ points apart, tonight's tilt in that stat had no logged cause, his minutes weren't confirmed, a 14.5 line 2+ points off DraftKings' was priced from one book, and the history block listed season, last-5 and H2H hit rates as three separate reasons | High meant "the blended number cleared 62%", not "the sources agree"; the display showed the pricer's label instead of the gate's, and a PrizePicks line far from the book's was converted through one book with no second look | NBA High = agreement: a market price, simulation and market within 5 points, tilt in limits or explained, minutes confirmed (L28), and a line 2+ points from DraftKings' confirmed by a second book. Any miss holds the leg at Medium and the card shows why. `verify` FAILs a gap line with no agreeing second book. History is one minutes-weighted line (season, last-5 average, H2H only at similar minutes). Shrinking to the market on disagreement runs as shadow v3 |

## Every loss gets a post-mortem
`python -m edge grade` writes one for each new loss, and `python -m edge review` covers any that were missed. That includes passes, Low legs and user entries, not just High picks. Each post-mortem pulls the box score or play-by-play, finds which input failed (volume, rate, price, script), links legs that lost on the same game script, and suggests a tag. Confirm it with `python -m edge tag ID "tag" --lesson "what to change"`. The readable log is `POSTMORTEMS.md`.

## Miss-tag taxonomy
`variance` · `opportunity` · `correlated` · `role/lineup` · `model bias` · `market info` · `stale line` · `data error` · `format misread`

- `opportunity`: far less volume than projected (early hook, ice-time cut, blowout, lost plate appearances).
- `correlated`: lost because another leg's script failed; the cause is recorded on that leg.

Two losses in a segment with the same tag (other than `variance` or `correlated`) means adding a rule above; `edge learn` flags it. Three, with the segment hitting below prediction, caps that segment at Medium until results recover.

## Auto-learned

### Auto-learned 2026-10-13
- Segment mlb:batter_hrr:under capped at Medium (no High legs) until results recover: 3 losses tagged 'model bias'; hit 50% vs 57% predicted over 12.
- 2 losses in mlb:pitcher_outs:over share the cause 'opportunity': write a checklist rule for it in the table above.
- 2 losses in cs2:cs_kills_m12:under share the cause 'model bias': write a checklist rule for it in the table above.
- 3 losses in mlb:batter_hrr:under share the cause 'model bias': write a checklist rule for it in the table above.

### Auto-learned 2026-11-03
- Segment cs2:cs_kills_m12:under: results run below our probabilities; now auto-adjusting -0.40 logit.
- Segment cs2:cs_headshots_m12:over: results run below our probabilities; now auto-adjusting -0.29 logit.
- Segment cs2:cs_kills_m12:under added to AVOID list: hit rate >8 pts under prediction over 20+ bets.

### Auto-learned 2026-11-03
- Segment cs2:cs_kills_m12:under capped at Medium (no High legs) until results recover: 3 losses tagged 'model bias'; hit 35% vs 59% predicted over 20.

### Auto-learned 2026-11-05
- Segment nba:pr:under capped at Medium (no High legs) until results recover: 10 losses tagged 'model bias'; hit 19% vs 60% predicted over 16.
- Segment nba:pts:under capped at Medium (no High legs) until results recover: 9 losses tagged 'model bias'; hit 33% vs 59% predicted over 15.
- Segment nba:pa:over capped at Medium (no High legs) until results recover: 3 losses tagged 'model bias'; hit 50% vs 59% predicted over 14.
- Segment nba:pra:over capped at Medium (no High legs) until results recover: 10 losses tagged 'model bias'; hit 43% vs 70% predicted over 42.
- Segment nba:pr:over capped at Medium (no High legs) until results recover: 5 losses tagged 'role/lineup'; hit 54% vs 64% predicted over 24.
- Segment nba:pts:over capped at Medium (no High legs) until results recover: 6 losses tagged 'model bias'; hit 32% vs 63% predicted over 19.
- Segment nba:reb:over capped at Medium (no High legs) until results recover: 4 losses tagged 'model bias'; hit 53% vs 64% predicted over 19.
- Segment nba:pa:under capped at Medium (no High legs) until results recover: 7 losses tagged 'model bias'; hit 31% vs 58% predicted over 13.
- Segment nba:pra:under capped at Medium (no High legs) until results recover: 4 losses tagged 'model bias'; hit 45% vs 61% predicted over 11.
- Segment nba:reb:under capped at Medium (no High legs) until results recover: 4 losses tagged 'model bias'; hit 50% vs 59% predicted over 8.
- Segment nba:ra:over capped at Medium (no High legs) until results recover: 4 losses tagged 'model bias'; hit 58% vs 63% predicted over 31.
- Segment nba:ra:under capped at Medium (no High legs) until results recover: 12 losses tagged 'model bias'; hit 54% vs 65% predicted over 35.
- 10 losses in nba:pr:under share the cause 'model bias': write a checklist rule for it in the table above.
- 9 losses in nba:pts:under share the cause 'model bias': write a checklist rule for it in the table above.
- 3 losses in nba:pa:over share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:pra:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 10 losses in nba:pra:over share the cause 'model bias': write a checklist rule for it in the table above.
- 5 losses in nba:pr:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 5 losses in nba:pr:over share the cause 'model bias': write a checklist rule for it in the table above.
- 3 losses in nba:pts:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 6 losses in nba:pts:over share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:reb:over share the cause 'model bias': write a checklist rule for it in the table above.
- 2 losses in nba:reb:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 7 losses in nba:pa:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:pra:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:reb:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:ra:over share the cause 'model bias': write a checklist rule for it in the table above.
- 12 losses in nba:ra:under share the cause 'model bias': write a checklist rule for it in the table above.

### Auto-learned 2026-11-05
- 10 losses in nba:pr:under share the cause 'model bias': write a checklist rule for it in the table above.
- 9 losses in nba:pts:under share the cause 'model bias': write a checklist rule for it in the table above.
- 3 losses in nba:pa:over share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:pra:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 10 losses in nba:pra:over share the cause 'model bias': write a checklist rule for it in the table above.
- 5 losses in nba:pr:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 5 losses in nba:pr:over share the cause 'model bias': write a checklist rule for it in the table above.
- 3 losses in nba:pts:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 6 losses in nba:pts:over share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:reb:over share the cause 'model bias': write a checklist rule for it in the table above.
- 2 losses in nba:reb:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 7 losses in nba:pa:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:pra:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:reb:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:ra:over share the cause 'model bias': write a checklist rule for it in the table above.
- 12 losses in nba:ra:under share the cause 'model bias': write a checklist rule for it in the table above.

### Auto-learned 2026-11-05
- 10 losses in nba:pr:under share the cause 'model bias': write a checklist rule for it in the table above.
- 9 losses in nba:pts:under share the cause 'model bias': write a checklist rule for it in the table above.
- 3 losses in nba:pa:over share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:pra:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 10 losses in nba:pra:over share the cause 'model bias': write a checklist rule for it in the table above.
- 5 losses in nba:pr:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 5 losses in nba:pr:over share the cause 'model bias': write a checklist rule for it in the table above.
- 3 losses in nba:pts:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 6 losses in nba:pts:over share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:reb:over share the cause 'model bias': write a checklist rule for it in the table above.
- 2 losses in nba:reb:over share the cause 'role/lineup': write a checklist rule for it in the table above.
- 7 losses in nba:pa:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:pra:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:reb:under share the cause 'model bias': write a checklist rule for it in the table above.
- 4 losses in nba:ra:over share the cause 'model bias': write a checklist rule for it in the table above.
- 12 losses in nba:ra:under share the cause 'model bias': write a checklist rule for it in the table above.

### Auto-learned 2026-11-05
- 2 losses in nba:tpm:under share the cause 'model bias': write a checklist rule for it in the table above.

### Auto-learned 2026-11-06
- Segment nba:reb:over: results run above our probabilities; now auto-adjusting +0.15 logit.
