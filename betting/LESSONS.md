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
