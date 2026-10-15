# CLAUDE.md

This repo holds a sports-betting analyst kit in `betting/`. For any conversation about bets, props, lines, pick'em or DFS, act as the analyst defined in `betting/ANALYST_PROMPT.md`.

## At the start of every betting session
1. Read `betting/ANALYST_PROMPT.md` (role, two modes, rules) and `betting/LESSONS.md` (binding checklist). Apply both before publishing any number.
2. Check `betting/data/bets.csv` for `pending` bets whose games have finished. If there are any, run:
   ```bash
   cd betting && python3 -m edge grade && python3 -m edge review && python3 -m edge learn
   ```
   Then summarize the report for the user: CLV, skill vs market, ROI, hit rate vs predicted, calibration.
3. **Examine every loss, not just High misses.** `grade` writes a post-mortem for each new loss (`review` catches any it missed): box score or play-by-play detail, which input failed (volume, rate, price, script), linked legs from the same game script, and a suggested tag. For each loss:
   - read the detail yourself and check the suggested tag against it (e.g. did the hitter's damage come off the starter or the bullpen?);
   - confirm the cause with `python3 -m edge tag ID "tag" --lesson "what to change"`;
   - tell the user, per loss, what happened, the cause, and what changes.
   Two losses in a segment with the same fixable cause means adding a rule to `betting/LESSONS.md`.
4. Mention any learned corrections now active (`betting/data/adjustments.json`: blend weights, outcome bias, avoid list, Medium caps).
5. Ask the session-start questions from the prompt: sport, slate date, books/apps, mode, bankroll.

## Back-check before publishing (mandatory)
Every pick you name to the user, at any confidence, must pass `python3 -m edge verify ID` in this session first. Do not quote any number that hasn't been through it.
- **What the back-check covers:**
  - It rebuilds the final probability and label from stored components with today's weights.
  - It re-fetches and recounts history at the prop's own unit (series for "maps 1-3", maps 1-2 for CS2, games for single-game props).
  - It re-runs the model on current odds (LoL, CS2).
  - It confirms the line and side are on the PrizePicks board.
  - It applies the lesson rules, and flags other open legs on the same script.
  - Soccer passes (L26): it FAILS a goalkeeper priced with the outfield model, and recounts history in tonight's kind of competition (European cup vs domestic). A FAIL there means re-price, not override.
  - Soccer lineups (L29): it FAILS an over on a player who isn't in the starting XI, and WARNS until the XI is out.
  - MLB lineups: it FAILS a batter prop on a player missing from the posted lineup and a pitcher prop on anyone but the listed starter, and WARNS until lineups post (about 3 hours before first pitch). An 8+ isn't published on a WARN here.
  - Line gap: it FAILS an unpriced PrizePicks standard line read at 70%+ that isn't held at Low, the same hold the scan applies. `--fix` lowers it, and `--refresh` never lifts a role, line-gap or circumstances hold back up.
- **NOT VERIFIED means not published.** Either fix it with `--fix` (not-started picks only) or withdraw it, and tell the user which.
- **Started or finished picks are never rewritten.** Their audit result is added as a note.
- **Show the verdict next to every pick.** Include each WARN, e.g. "Boom line not readable automatically: confirm 8.5 Less on your screen".
- **After `edge learn` changes weights,** run `python3 -m edge verify --open --refresh` before recommending anything.
- **Never type a number into `edge prob` by hand when a pricer exists** (`edge pp`, `edge passes`, `edge/lol.py`, `edge/cs2.py`). Copy-typing is how 0.728 became 0.78.

## User preference: 1-10 rating on every prop
The user wants **every prop rated 1-10** (`blend.rating`, shown by `edge pp`, `edge prob` and `edge verify`). The gates don't change; the label sets the band and the probability places it inside:
- Every probability passes through a calibration map that `edge learn` fits from graded results, separately for priced and unpriced picks (`adjustments.json` "calibration"). A model-only 80% currently reads 73%.
- **8-10 = the 80% tier.** The user's bar: these must hit at least 80%. Requires every High gate and a blended chance at or above the rating floor (0.80; `edge learn` raises it while graded 8+ picks hit under 80% over 20+). When a sportsbook prices the prop, the book must also make it a 75%+ shot on its own (a book under 75% caps it at 7).
  - **No book price is not a gate (user's call, 10/15):** a prop no book prices is graded from its game logs: history plus the matchup model, or the game-log model (recency-weighted mean, gamma-Poisson) where there is no matchup model. The no-market calibration applies.
  - It can reach 8 when it clears the no-market High gates (20+ games, sources within 10 points) and its own floor, `rating_floor_no_market` (0.80). `edge learn` tunes that floor on unpriced 8+ results only, never mixed with priced ones. The scorecard shows them as their own row ("8-10, no book price").
  - Their record before this was weak (unpriced Highs at 65-80% hit 6 of 11), so watch that row and say so when it runs under 80%.
  - Bands: 8 at the floor, 9 at floor+5, 10 at floor+10.
  - **Role check, no book price (L5):** a workload 25%+ off his average over the last 5 games (touches/attempts, ice time, plate appearances) holds the prop at Low. The back-check accepts that downgrade.
- **5-7 = Medium**, or a High that isn't in the 80% tier (7): a good number that missed a gate (a book under 75%, thin history, sources too far apart, a learned cap). Never above 7, however high the probability.
- **1-4 = Low**: sources disagree, single source, role unknown (L5/L26), or under 58%. Avoid-list segments are 1.
Show the rating next to every prop. A prop rated 8+ must pass `edge verify` this session, with its verdict and WARNs shown; a NOT VERIFIED or judgment-downgraded prop (role check) drops to its new label's band. Ratings of 7 or below come straight from the pricer: mark them as ratings, not picks. Recommend only 8+.

## User preference: prove the takes (be proactive)
Don't wait to be asked whether a take worked. After every slate, grade it, then report the results of every prop rated today, grouped by rating band. The source is the "Scorecard by rating" line of `edge report`: does an 8 actually hit more than a 5, and does each band hit what it predicted? Call out each 8+ that missed, with its post-mortem tag. When a pick is in a live game the user is following, check in with the live state before being asked. Every take shows its evidence: the raw game-by-game numbers and the market price, not just the rating. Schedule the post-slate check-in yourself (`send_later`) when the user has open picks and the games finish after the conversation pauses.

## User preference: track the user's takes (from 10/15)
The user marks the props they actually play with the **Take** button on the Eight-Plus Board (every props row, player view, regular line, slip result, ticket and card). Takes are saved as `takes/<id>` in the page's db: `{lg, player, tm, op, stat, line, side, ty, start, rating, p, pm, proj, src, bets_id, status:"new"}`.
- **Reports track the takes, not every rating.** At every check-in and after every slate, lead with the takes: each one's result, hit or miss, its rating, and the takes record by band (`edge takes` prints it). The full "Scorecard by rating" stays below, shorter, because it is what calibrates the model.
- **Every prop is still logged quietly** (`edge tier --log`, `edge pp --log`, inject). The learning needs all of them; the user just doesn't need to hear about each one.
- **Processing:** list `takes` with ArtifactData into a fresh folder (`out_dir`), run `python3 -m edge takes DIR --out RES.json`, then one batch `update` (`if_version`) per take writing back `bets_id`, `status`, `result`, `rating`, `p`, `checked`.
  - It links a take to its bets.csv row (same player, market, line, side and slate day) and marks it the user's entry (`entry_id take-<id>`). A take with no row is priced and logged through `edge inject`.
  - The page shows the status live (Open, tracked / Hit / Miss).
- A take rated 7 or below is still the user's call: grade it and report it like the rest, without lecturing. If a take is NOT VERIFIED or a circumstance flag lands on it before the game, tell the user right away.
- A losing take gets the same post-mortem as any loss (step 3 at the start of the session), first in the report. `edge takes` writes its cause back to the take doc (`tag`, `lesson`, `detail`) and the page shows it under "Why it missed".
- **The My takes tab** (a tab in the sport bar) is the user's track record: hits and misses, hit rate against what we predicted, last-10 form and streak, by rating band, sport and line type, and every take by day. Keep it current: write every take's status after each grading.
- **Grade everything, not just takes (user, 10/15).** Every prop we rated is graded, and every loss, taken or not, gets the step-3 post-mortem. Each lesson says what read would have caught it (role, minutes, matchup, line, news) and what changes in the model. Fixable causes feed `edge learn` and LESSONS.md.
- **Rows without a game id never grade.** `edge grade` now backfills ids for MLB/NHL/NFL/NBA rows from the team, the start time and the ESPN id. If a pending row from a finished slate is still ungraded after `grade`, find out why and fix it; don't leave it.

## Role and competition check (L26, mandatory)
Before naming any prop, ask two questions the pricer may not: **is this player's role one the model was built for**, and **does his history come from the same kind of game as tonight?**
- Goalkeepers' passes go up when their team has less of the ball (goal kicks, back-passes under a press). Haikin: 19-27 passes in Norway at 55-78% possession, 22-44 in the Champions League. They are priced by `soccer.keeper_passes` from same-competition starts, never by team possession x share.
- **Possession forecast (L28):** for passes props the possession forecast is the biggest input (Anton swung from 80% to 42% under between 48% and 56%). Cross-league ties use European-match possession, and the pick's sensitivity to possession is checked before naming it.
- **Game state, not just competition (L27):** a centre-back's or midfielder's passes swing with his team's possession. History and share of team passes come from starts at a possession close to tonight's forecast (within 7 points). A big game against an equal side is not his average league game.
- Any player whose competition level tonight differs from most of his history (European cup vs domestic, playoffs vs regular season, international vs regional esports) is recounted in that competition. If the two disagree by more than 20 points, the same-competition sample wins or the pick is withdrawn.
- Same idea elsewhere: a CS2 AWPer's headshots, an NHL goalie in a rotation, a backup or rookie on a new role (L5), a returning player on a minutes cap. If the model doesn't know the role, say so and don't publish above Low.
- When the user questions a number, dig in with the raw match-by-match data before defending it.
- When the user says a line is wrong, pull the live PrizePicks board (`pp.board(LEAGUE, odds_types=("standard","goblin","demon"))`) and compare every line on the list. A player often has several standard lines on different stats (Lloyd 10/15: Rush Yards 42.5 and Rush+Rec Yds 58.5).
- Every prop below 8 carries its real reason (`lo` on board rows: line gap, role change, sources split, thin history, book under 75%, ...). The page spells it out with the three sources (model, sportsbook, history) on every card. Never label a hold "sources disagree" unless the sources really point to different sides.

## Circumstances check (L31, mandatory)
The numbers don't see who sits, who rests, a new or smaller role, a star teammate out, a blowout, the wind or the probable goalie. `edge/situation.py` reads them for every prop that `edge tier`, `edge inject` and `edge verify` rate:
- **Sources:** tonight's ESPN game report (injury and rest statuses, spread and total, weather, probable goalies, recent games for back-to-backs) and the player's latest Rotowire note.
- **OUT** (listed out, on IR/IL, not the probable goalie): withdrawn.
- **HOLD**, to Low:
  - listed doubtful
  - resting, or a note saying he sits, rests or plays limited minutes, when the bet is an over
  - a note giving him a bigger role when the bet is an under, or a smaller role when it's an over (L5)
- **CAP**, to Medium at most:
  - listed questionable or a game-time decision
  - a team leader newly out when the bet is an under
  - NBA spread of 12+ on overs
  - NFL gusts of 20+ mph or 70%+ rain on passing and kicking overs
  - MLB 60%+ rain on pitcher overs
  - an NHL goalie on the second night of a back-to-back
- **INFO** (total, opponent's players out, weather, a back-to-back): shown next to the number.
- `edge verify` re-reads it at publish time and FAILS a not-started pick it would lower; a NOT VERIFIED pick is withdrawn (delete its page doc).
- Before naming any 8+, read its circumstances line and the player's note yourself, and say what they show. Things the reader can't parse (a coach's quote, a playoff team resting starters, a trade) are still yours to catch.

## While working
- For "only 8+" on PrizePicks, run `python3 -m edge tier --log` (NHL, MLB: DraftKings ladder + game log at every line, calibrated, rated). Then `edge verify` every 8+ and drop any NOT VERIFIED.
  - `edge tier` prices every PrizePicks prop it can read from game logs, whether or not a book prices it. NFL is included, with an 8-day slate window and readers for TDs, FG made and kicking points.
  - Rows with no book price are marked "no book price" on the board.
  - NBA preseason (L30): `edge tier --league NBA` also reads PrizePicks' NBAP board. Preseason props are priced with the preseason minutes model and preseason history, with the book at half weight. Every prop is matched to the game on its own date.
- **Esports and soccer on the page (user, 10/15):** `edge board --props` also prices, logs and exports PrizePicks' CS2, LoL, Valorant and SOCCER boards (`--extra`, standard and goblin lines for games not yet started), each with a card built from the pricer's series-by-series or match-by-match history.
  - CS2: maps 1-2 and map 1 kills and headshots (bo3.gg). LoL: maps 1-3 kills (gol.gg + bo3.gg odds).
  - Valorant (`edge/val.py`): maps 1-2 kills and first bloods. Player maps come from vlr.gg match pages: its robots.txt allows them, requests are spaced 0.6 s apart and finished matches are cached. Series odds come from bo3.gg (discipline 2). Graded from the vlr.gg match page.
  - Soccer: the Soccer tab reads every PrizePicks soccer board (`pp.soccer_board`): the mixed SOCCER board plus EPL, UCL, La Liga, Serie A, Bundesliga, Ligue 1, MLS and Liga MX (EPL props are only on the EPL board). Each game is found on ESPN across the leagues in `pp.SOCCER_SLUGS`.
    - Shots, shots on target and saves use the DraftKings ladder when ESPN has one. Passes use the soccer passes model (keepers by `keeper_passes`, L26).
    - Goals, assists, goal + assist and fouls come from ESPN's match reports. They have no book line, so the game-log model and history price them.
    - Without a ladder, the game-log model is the second source next to history (25 recent matches in any competition). Tackles and clearances aren't in the match reports and aren't priced yet. First-half and second-half boards (EPL1H, ...) are a different window and aren't read.
  - Their records so far are weak (CS2 kills unders 43% of 81, soccer shots overs 29% of 48). The learned biases correct for it, so 8+ will be rare there. Say so rather than stretch.
- For a PrizePicks board, start with `python3 -m edge pp --league <CS2|VAL|LOL|SOCCER|...> [--match TEAM] --log`: it prices every supported prop with the same blend and gates, marks MORE-ONLY lines (no under available) and thin or new-to-team players. Read the flagged legs yourself before recommending anything.
- Final probabilities come from `python3 -m edge prob --model .. --market .. --hist .. --hist-n .. --segment sport:market:side`. Report the confidence it returns; don't override it upward.
- Log every evaluated prop (bets, leans and passes) with `python3 -m edge add ...` (fields: header of `bets.csv`; market keys: `betting/README.md`). Include `event_id` and `player_id` so it can be auto-graded, and `proj` (projected median) and `opp_proj` (projected BF / PA / TOI / rounds) so a loss can be traced to volume or rate.
- Before the user submits an entry, run `python3 -m edge card` and remove any leg it flags as unpriced or under break-even (LESSONS L20).
- Pick'em break-evens: `python3 -m edge breakeven`. Squad Ride: `python3 -m edge squad ...`.
- Never hand-edit `adjustments.json` to chase a recent result. Only `edge learn` changes it.

## Eight-Plus Board page
The user follows 8+ picks on a live page: https://claude.ai/artifact/AhjWxmRgkijq4UkjhFEhsn (data in its `db`: `picks/<bets.csv id>`, `meta/summary`, `boards/pp-<LG>` / `boards/book-<LG>` for the All props explorer: every PrizePicks or sportsbook line we priced, with its rating and projection, `meta/regular` for regular-line plays, `takes/<id>` for the props the user tapped Take on (see above), and `cards/<LG>-<i>` for the tap-to-open prop cards: last games with opponent and home/away, averages, head-to-head, venue split, matchup rank). After any scan that finds 8+ picks, and after grading, refresh it: `python3 -m edge board --out <fresh dir>` (add `--props` after a morning or pre-slate scan), set `next_scan` in `meta/summary.json`, list `picks` with ArtifactData for versions, then one batch `set` per file (with `if_version` on existing docs). Delete a pick's doc when it is withdrawn.

### Keep the board in step with PrizePicks (user, 10/15)
PrizePicks moves lines, adds props and pulls them all day. **The user wants the board refreshed once a day for now (10/15); refresh more often only when they ask.** The scheduled task "Daily board refresh" fires into this session at 10:55 am Central: it grades finished slates, processes takes and the inbox, runs the full scan (`edge board --props --league NHL,MLB,NBA,NFL --extra CS2,LOL,VAL,SOCCER`), uploads it, verifies new 8+ and sends one short message. When the user asks for a refresh in between, run `python3 -m edge refresh LIVE --out OUT`:
- LIVE is the page's `boards` and `cards` as ArtifactData lists them (out_dir).
- It compares every league's PrizePicks board with what we priced. A standard line that moved is re-priced at the new number; new props and new goblin lines are priced; pulled props and started games drop off. New and re-priced rows are logged.
- It diffs against `.cache/board_state/pp-<LG>.json`: every line the last full scan or refresh priced, including the ones the 256 KB board document had to trim. After a container restart that state is gone, so a big board (more than 150 new props) is flagged for a full scan (`edge board --props --league .. --extra ..`), which rebuilds it.
- It writes the changed `boards/pp-<LG>` and `cards/<LG>-r` (cards for props added since the last full scan) to OUT for one batch upload, and lists new 8+ props. Those need `edge verify` and a picks refresh before they show as picks.
- The full scan (`edge board --props`) still runs before each slate; it is what rebuilds every card and the regular lines.
- A refresh between daily runs messages the user only for a new 8+ pick, a withdrawn pick, or a moved or pulled line on one of their takes.

### Inbox (Check a slip)
The page's "Check a slip" section takes screenshots or a screen recording (a slip, a board, someone's pick). The page splits a video into distinct frames on the device. Claude reads the props off the frames (the page's `sample` call), matches them to our boards and cards, and writes a short analysis. Each check is saved as `inbox/<id>` with status "new": `{kind, app, entry, props:[{player, sport, stat, line, side, odds_type, price}], page, analysis, frames:[asset ids], video}`.
- **When to process:** at every check-in, whenever the user says they checked a slip, and at once when a page comment to Claude reads "Grade inbox <id>".
  - The page sends that comment on the same tap as "Read and grade", so it can arrive before the doc is saved (reading takes about a minute). If `inbox/<id>` isn't there yet, `send_later` 2 minutes and look again.
  - Process the doc right away, write the results and a short analysis back to it (the page fills them in live), and answer the comment in one line.
  - The analysis reads like an analyst's: game type (preseason, playoffs, back-to-back), minutes and role tonight, matchup, then the numbers (L30).
- `edge inject` grades MLB, NHL, NBA and NFL props with or without a book price. It finds the player's game by name ("S. Gilgeous-Alexander" works) and grades it in that game's competition: an NBA preseason game uses the preseason minutes model (L30). With no side picked (a board, a post), it grades both sides and keeps the better one. NHL faceoffs and other stats outside the game logs are reported as not gradable.
- **Video only, no props** (the viewer's browser couldn't decode it, e.g. HEVC on desktop Chromium): fetch it with `Artifact read path=<asset id>` and split it with ffmpeg (1 fps, drop near-duplicate frames). Read the frames yourself and write the props into the doc first.
- **Then:** save the doc to a file and run `python3 -m edge inject FILE --out RES.json`. It prices each MLB/NHL/NBA prop like a scan row, logs it (a slip's legs as `user_entry`; a leg already logged is linked, not duplicated; a tennis leg links to the match priced with `edge tennis pre`), and runs `edge verify` on each.
- Write back with one ArtifactData `update` (`if_version`): `status: "logged"`, `processed`, `results`, `new_ids`.
- Tell the user per prop: rating, chance, verdict and WARNs, and whether it's a play. Commit `betting/data/`.
- The page's own read is a first look from the boards, not the published number: only `edge inject` + `edge verify` numbers are quoted as ratings.

## Persist the learning
Cloud containers are temporary. After any `grade`, `review`, `learn`, `add` or `tag`, commit `betting/data/`, `betting/LESSONS.md` and `betting/POSTMORTEMS.md` and push, or the learning is lost.

## Data sources that work
- Every book's player-prop prices: The Odds API with `$ODDS_API_KEY` from the environment (`edge/oddsapi.py`; `python3 -m edge odds` checks it). `edge tier` uses it first and falls back to ESPN's DraftKings ladders. Never print, log or commit the key.

No-key sources:
- Odds and DraftKings props: `https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{id}/competitions/{id}/odds/100/propBets`. Over/under order is not labelled: verify sides against the "N+" milestone price (LESSONS L2).
- Soccer: ESPN `site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event=ID` (any league), plus per-player match stats (passes, saves, minutes) from `sports.core.api.espn.com/v2/sports/soccer/leagues/{league}/events/{id}/competitions/{id}/competitors/{team}/roster/{player}/statistics/0`. DraftKings soccer props are on the same propBets endpoint (league `uefa.champions`, `eng.1`, ...).
- PrizePicks boards: `https://partner-api.prizepicks.com/projections?league_id=ID&per_page=10000` (league ids from `/leagues`; the main api.prizepicks.com is captcha-blocked). It rate-limits: `edge pp` caches and backs off.
- Tennis: ESPN `site.api.espn.com/apis/site/v2/sports/tennis/{atp|wta}/scoreboard[?dates=YYYYMMDD]` (results, set scores, live games and server; no point score, no odds). `python3 -m edge tennis refresh` updates `betting/data/tennis/` and refits; for a live match run `edge tennis live NAME --odds A B --points X-Y` (add `--pre-odds` when you have the pre-match price) and rate it like any other pick.
- MLB: `statsapi.mlb.com`. NHL: `api-web.nhle.com` and `api.nhle.com/stats` (send a User-Agent header). NFL: ESPN `site.api.espn.com`. CS2: `api.bo3.gg` (HLTV blocks scripted access).
- Valorant: `www.vlr.gg` match, team and match-list pages (`/team/matches/{id}/?group=completed`; robots.txt disallows only `/search/auto` and `/rr/`; keep the 0.6 s spacing). bo3.gg has Valorant schedules and odds but no per-map player stats.

## Tests
`cd betting && python3 -m unittest discover -s tests` (numpy is the only dependency).
