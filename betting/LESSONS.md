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

## Miss-tag taxonomy
`variance` · `role/lineup` · `data error` · `model bias` · `market info` · `format misread` · `stale line`

Two misses with the same non-variance tag means adding a rule above.

## Auto-learned
