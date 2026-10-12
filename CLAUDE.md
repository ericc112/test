# CLAUDE.md

This repo holds a sports-betting analyst kit in `betting/`. For any conversation about bets, props, lines, pick'em or DFS, act as the analyst defined in `betting/ANALYST_PROMPT.md`.

## At the start of every betting session
1. Read `betting/ANALYST_PROMPT.md` (role, two modes, rules) and `betting/LESSONS.md` (binding checklist). Apply both before publishing any number.
2. Check `betting/data/bets.csv` for `pending` bets whose games have finished. If there are any, run:
   ```bash
   cd betting && python3 -m edge grade && python3 -m edge learn
   ```
   Then summarize the report for the user: CLV, skill vs market, ROI, hit rate vs predicted, calibration, and untagged high-confidence misses. Ask for a root cause on each miss and record it with `python3 -m edge tag ID "reason"`.
3. Mention any learned corrections now active (`betting/data/adjustments.json`: blend weights, outcome bias, avoid list).
4. Ask the session-start questions from the prompt: sport, slate date, books/apps, mode, bankroll.

## While working
- Final probabilities come from `python3 -m edge prob --model .. --market .. --hist .. --hist-n .. --segment sport:market:side`. Report the confidence it returns; don't override it upward.
- Log every evaluated prop (bets, leans and passes) with `python3 -m edge add ...` (fields: header of `bets.csv`; market keys: `betting/README.md`). Include `event_id` and `player_id` so it can be auto-graded.
- Pick'em break-evens: `python3 -m edge breakeven`. Squad Ride: `python3 -m edge squad ...`.
- Never hand-edit `adjustments.json` to chase a recent result. Only `edge learn` changes it.

## Persist the learning
Cloud containers are temporary. After any `grade`, `learn`, `add` or `tag`, commit `betting/data/` and `betting/LESSONS.md` and push, or the learning is lost.

## Data sources that work (no API keys)
- Odds and DraftKings props: `https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{id}/competitions/{id}/odds/100/propBets`. Over/under order is not labelled: verify sides against the "N+" milestone price (LESSONS L2).
- MLB: `statsapi.mlb.com`. NHL: `api-web.nhle.com` and `api.nhle.com/stats` (send a User-Agent header). NFL: ESPN `site.api.espn.com`. CS2: `api.bo3.gg` (HLTV blocks scripted access).

## Tests
`cd betting && python3 -m unittest discover -s tests` (numpy is the only dependency).
