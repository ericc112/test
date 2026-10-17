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
- **NOT VERIFIED means not published.** Either fix it with `--fix` (not-started picks only) or withdraw it, and tell the user which.
- **Started or finished picks are never rewritten.** Their audit result is added as a note.
- **Show the verdict next to every pick.** Include each WARN, e.g. "Boom line not readable automatically: confirm 8.5 Less on your screen".
- **After `edge learn` changes weights,** run `python3 -m edge verify --open --refresh` before recommending anything.
- **Never type a number into `edge prob` by hand when a pricer exists** (`edge pp`, `edge passes`, `edge/lol.py`, `edge/cs2.py`). Copy-typing is how 0.728 became 0.78.

## While working
- For a PrizePicks board, start with `python3 -m edge pp --league <CS2|UCL|...> [--match TEAM] --log`: it prices every supported prop with the same blend and gates, marks MORE-ONLY lines (no under available) and thin or new-to-team players. Read the flagged legs yourself before recommending anything.
- Final probabilities come from `python3 -m edge prob --model .. --market .. --hist .. --hist-n .. --segment sport:market:side`. Report the confidence it returns; don't override it upward.
- Log every evaluated prop (bets, leans and passes) with `python3 -m edge add ...` (fields: header of `bets.csv`; market keys: `betting/README.md`). Include `event_id` and `player_id` so it can be auto-graded, and `proj` (projected median) and `opp_proj` (projected BF / PA / TOI / rounds) so a loss can be traced to volume or rate.
- Before the user submits an entry, run `python3 -m edge card` and remove any leg it flags as unpriced or under break-even (LESSONS L20).
- Pick'em break-evens: `python3 -m edge breakeven`. Squad Ride: `python3 -m edge squad ...`.
- Never hand-edit `adjustments.json` to chase a recent result. Only `edge learn` changes it.

## Persist the learning
Cloud containers are temporary. After any `grade`, `review`, `learn`, `add` or `tag`, commit `betting/data/`, `betting/LESSONS.md` and `betting/POSTMORTEMS.md` and push, or the learning is lost.

## Data sources that work (no API keys)
- Odds and DraftKings props: `https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{id}/competitions/{id}/odds/100/propBets`. Over/under order is not labelled: verify sides against the "N+" milestone price (LESSONS L2).
- Soccer: ESPN `site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event=ID` (any league), plus per-player match stats (passes, saves, minutes) from `sports.core.api.espn.com/v2/sports/soccer/leagues/{league}/events/{id}/competitions/{id}/competitors/{team}/roster/{player}/statistics/0`. DraftKings soccer props are on the same propBets endpoint (league `uefa.champions`, `eng.1`, ...).
- PrizePicks boards: `https://partner-api.prizepicks.com/projections?league_id=ID&per_page=10000` (league ids from `/leagues`; the main api.prizepicks.com is captcha-blocked). It rate-limits: `edge pp` caches and backs off.
- MLB: `statsapi.mlb.com`. NHL: `api-web.nhle.com` and `api.nhle.com/stats` (send a User-Agent header). NFL: ESPN `site.api.espn.com`. CS2: `api.bo3.gg` (HLTV blocks scripted access).

## Tests
`cd betting && python3 -m unittest discover -s tests` (numpy is the only dependency).

## Job search app (`jobs/`)
`jobs/` is a separate project: JobBot, a local web app that searches job boards, ranks matches and fills/submits applications (see `jobs/README.md`). The betting instructions above don't apply to it. Personal data lives in `jobs/data/` (git-ignored); never commit it. Tests: `cd jobs && python3 -m unittest discover -s tests -t .`
