# JobBot fix report — Oct 21, 2026

Work done in the snapshot of Eric's public repo `ericc112/test` at `~/workspace/jobbot/test-main/jobs`
(the `jobbot` package + static UI + tests). No real job application was submitted or attempted at any
point; all verification ran against the test suite's local fixtures. Eric's profile data files were not
changed, and no personal data was invented — the profile's street address is still missing (see the end).

## Test results

| Run | Result |
|---|---|
| Baseline, no Chromium installed | 240 tests run, OK, 36 skipped (the browser tests skip) |
| Baseline, Chromium installed, suite run on its own | **240 tests, all OK** (2–3 skipped) |
| Final, after the fixes | **254 tests, all OK, 2 skipped** — the baseline 240 plus 14 new tests |

Baseline note: the browser/watcher tests are timing-sensitive. When several suites were run in
parallel during the investigation, intermittent failures appeared in `tests/test_engine.py` and
`tests/test_watch.py` (4 failures + 1 error in the worst loaded run); run on their own, both the
baseline and the final suite are fully green. The final suite was run the same way as the clean
baseline (one full `unittest discover` run, nothing else loading the machine).

New tests added: 14 (answers ×2, pagefeed ×4, worker ×3, server ×3, CLI ×1, engine ×1), plus three
pre-existing tests updated for intended behavior changes (the closed-posting result string, and two
pagefeed tests whose synthetic listings now needed distinct titles because same-title listings group
into one card — the feature working as designed).

## Per-issue status

### 1. Filter dropdown counts ignore the other filters — CANNOT FIX IN THIS REPO (page-side)
The counts in the Location/Season/area dropdowns are computed by the **claude.ai artifact page**,
whose frontend source is not in this repository (the only UI in the repo is the local app's
`jobbot/static/`, which shows no per-option counts at all). The page has every listing client-side
(all feed pages), so the fix belongs in the page's count computation: count each facet over the list
filtered by the *other* active filters and the search text. The feed data already carries everything
needed (`st`, `se`, `a`, `loc`, pay fields). Nothing in the repo computes these counts, so there is
nothing here to patch.

### 2. "Highest pay" sort breaks while a search is active — FIXED locally / page-side on the artifact
- Artifact page: page-side sorting of the rendered list; not in this repo (same situation as #1).
- Local app: sorting was already correct (filters and sort are one SQL query, so sort always applies
  to the filtered list), but there was no pay sort at all. **Added one**: `db.SORTS["pay"]`
  (highest listed pay first, no-pay jobs last) and a "Highest pay" option in the Jobs sort dropdown.
  Because it's the same query's `ORDER BY`, it composes with search text and every filter by
  construction.

### 3. Stale search/list disagreement after clearing search — FIXED locally / page-side on the artifact
- Artifact page: not in this repo.
- Local app: found a real race — two overlapping list loads could complete out of order, so a slower
  earlier response could overwrite a newer one (the list briefly showing results for text already
  cleared). **Fixed** with a load-sequence guard in `viewJobs`: only the newest load may render.

### 4. Applying-tab filters that don't apply — CANNOT FIX IN THIS REPO (page-side)
The "Applying" tab and its filter bar live in the artifact page, not this repo. The local app's
equivalent (Review queue) has four purpose-built tabs and no filter dropdowns, so there's nothing to
hide or adapt locally. Page-side fix: on the Applying tab, hide the pay/area/season filters and make
Location reflect the tab's own jobs.

### 5. Applying-tab dead ends — FIXED (the parts that live in this repo)
- **Closed postings**: the engine detected "this posting is no longer up" but reported it as the
  generic `manual` status — the same status as "apply on the site yourself" — so the UI kept
  offering **Fill again / Try again** forever. Now it reports a distinct **`closed`** result
  (`apply/engine.py`), which is a real job status end-to-end (`db.STATUSES`, worker passes it
  through). Local UI: closed jobs get a "Closed" chip, no Fill button (row or drawer), the API
  refuses Fill/Submit on them with a clear 409, they group with Skipped in the Jobs filter, and they
  can still be restored to New by hand. `CLOUD_WORKER.md` gained the matching row
  (`closed` → `closed`, no Try again) so the cloud worker writes the right page status.
- **Rate limit**: was a generic `error`. Now `blocked` with the note "Wait a while, then try again —
  nothing is wrong with the application."
- **CAPTCHA / email code / verification link**: already produced specific, actionable messages in
  this snapshot ("Turn off headless mode in Settings and submit again to finish it yourself";
  "Open it to verify your account, then tap Try again"), shown under the job row and in the drawer.
  No change needed.
- Also hardened (see #11): a Workday field JobBot *couldn't* correct now says exactly what the site
  holds — "Couldn't change this — the site has "Germany (+49)" here. Fix it before you submit" —
  instead of a generic couldn't-enter note.

### 6. UI polish (chip row cut off; "Sharing tip" popover) — CANNOT FIX IN THIS REPO (page-side)
Both are artifact-page elements. ("Sharing tip" doesn't exist anywhere in the local app.) The local
app's chip/meta/filter rows already wrap (`flex-wrap` in `app.css`); nothing to change locally.

### 7. Repetitive / stale listings
- **(a) Coverage — PARTIALLY FIXED; the wall itself is data, not code.** The numbers check out:
  `fortune500.json` has 498 companies; 322 `watched` (a readable feed), 45 `unsupported`
  (no working feed: Eightfold, iCIMS, Taleo and Avature have no reader in the codebase at all, and
  the rest are site variants the existing readers don't handle), 131 `not_found` (no public feed —
  Walmart, Apple, Microsoft among them). Those 176 can't be fixed in code: unsupported systems need a
  whole new source module each (a project per ATS, and several need accounts/API keys), and
  no-public-feed companies have nothing to read. What *was* improvable: per-company failure
  reporting existed only as raw rows behind `/api/sources`. **Added `python3 -m jobbot coverage`**:
  prints the three groups with the unsupported-system breakdown and names every watched feed that
  failed its last recorded run, per company (also `--out report.json`). Covered by a test.
- **(b) Same role in many locations + one company dominating Best match — FIXED (page feed).**
  `pagefeed.build` now (i) folds same company + same (normalized) title into one card: the
  best-scored posting, with `locs` (every location) and `n` (how many it folds in); `meta.grouped`
  counts the folded listings. (ii) A spread pass caps any company at 3 cards in any 10 of the
  Best-match order; held-back cards keep their order after the rest. Both tested.
- **(c) Only the first 200 render — FIXED locally / page-side on the artifact.** The feed itself was
  never capped (60 per page document, all pages written). The local Review view *did* hard-load
  `limit=200`, so anything past 200 in a tab was unreachable: it now paginates with Load more
  (100/page), and "Submit all" fetches the full ready list instead of just the loaded rows. The
  local Jobs view already had Load more. The artifact page rendering only 200 is page-side.
- **(d) Staleness — data side FIXED; controls verified.** Feed items now carry `nw: true` when the
  listing wasn't in the previous build, and `meta.new_count` counts them — the page can badge and
  filter "New since last visit" from that (the badge itself is page-side). First-seen times were
  already preserved across refreshes (`--previous`). Locally, "Refresh now" already exists as the
  **Search now** button (forces a fresh search) plus a "Just posted" (48 h) marker and desktop
  alerts for employer-site postings.
- **(e) Gusto — VERIFIED CLEAN.** Gusto is *not* in `fortune500.json`. It's in
  `config.SUGGESTED_COMPANIES`, the deliberate hand-picked watchlist ("employers with many business
  roles"), which is a separate set from the Fortune 500 file — nothing is slipping into the Fortune
  500 set.

### 8. Company logos + profiles — FIXED (with an honest data limit)
New `jobbot/companies.py` reads the Fortune 500 file and serves, per company: rank, website,
careers page, job systems, domain, and logo URLs (Clearbit logo service, with the Google favicon
service as fallback — both free, no keys; the card's `<img>` falls back automatically and removes
itself if both fail). Local UI: logos on job rows and in the drawer, and an "About <company>" card
in the drawer with rank #N, website, careers-page link and job system. New `GET /api/companies`
endpoint; job rows/detail/state now carry `company_info`. Feed items carry `rk` (rank) and `dom`
(domain) so the artifact page can show logos too.
**Data limit**: `fortune500.json` contains only rank, name, website, careers, feeds, systems,
status. It has **no industry, HQ, or company size**, and no description — those were not invented.
Adding them means sourcing a company dataset; the profile view shows everything the file actually
has.

### 9. Apply must not need a chat message — ALREADY WORKS LOCALLY; artifact limitation is structural
In this snapshot the local app already does it end-to-end: Fill/Submit (row, drawer, or bulk) →
`POST /api/jobs/{id}/action` → the background `Worker` picks it up immediately and processes it,
with live status on the card/drawer (Queued → Filling… → Ready / Needs you / Applied) — no chat
involved. Verified by the server/worker tests.
**The artifact page cannot do this, and no code in this repo can change that**: a claude.ai artifact
has no way to run code or reach a browser. Its Apply button only writes an `approved` document; a
*scheduled Claude cloud session* must notice it and run `apply-batch` (the `CLOUD_WORKER.md`
contract — every ~3 hours, or immediately when the session is started). Making Apply feel instant
on the page is an operational change to that scheduled session (run it more often / keep the
"Start now" trigger), not a code fix. One related safety gap *was* fixed here: see #10.

### 10. Remove button / Removed tab / cancel-on-remove — PARTIAL (page-side built elsewhere; local gaps fixed)
The Remove button + Removed tab + Undo described by the Claude session live in the **artifact
page**; they are not in this repo and can't be verified from it. The local app's equivalents:
Skip → status `skipped` (excluded from the page feed and from search results — skipped jobs do
**not** resurface on refresh; `upsert_job` never overwrites status) and Restore ("Move back to
New") — those already existed. Two real gaps found and fixed:
- **Removing a queued application now cancels it.** `Worker.remove(job_id)` drops the job from the
  queue (and resets a `queued` job to New); Skip — single or bulk — calls it, there's a
  "Remove from queue" button in the drawer, and as a backstop `Worker.process` refuses to run a job
  whose status became `skipped` while it waited. All three covered by tests.
- A per-job dequeue API action (`dequeue`) backs the drawer button.

### 11. Profile defaults + form filler
- **Country = United States**: already the default (`config.DEFAULT_PROFILE`), and it merges under
  any stored profile, in local *and* cloud runs (`apply-batch` merges non-empty profile values over
  the defaults). **Phone country code +1**: handled as the same country answer on phone-code
  widgets (e.g. Workday's "Country Phone Code" → "United States of America (+1)").
- **The Germany bug — root cause.** The string "Germany" appears nowhere in JobBot's code, and no
  default produces it: the value came from **the employer's form itself**. Workday (and similar
  sites) pre-fill Country / Country Phone Code from the account or from parsing the uploaded resume;
  a misread resume or a draft saved by an earlier run can put the wrong country there. JobBot's
  correction path only replaces a pre-filled value when it can match your profile's answer against
  the form, and when it *can't* correct it, the field went out with a generic "couldn't enter"
  note — easy to miss in a screenshot of filled fields. Fixes: the correction is now regression-
  tested (the Workday fixture can pre-fill "Germany (+49)"; a test proves JobBot replaces it with
  United States), and when a correction fails the field note names the site's value: "Couldn't
  change this — the site has "Germany (+49)" here. Fix it before you submit."
- **"How did you hear about us" = LinkedIn — FIXED.** LinkedIn was not a named candidate in
  `answers._how_heard` at all: with the default profile it was reachable only as the "any option"
  fallback (the form's *first* option) or via the second level of a Workday prompt. It's now a
  named candidate, ranked after your profile's own answer and — for jobs found on the employer's own
  site — after the company-website options (that site-first behavior is deliberate and tested).
  If your profile's "How did you hear" field says LinkedIn, it wins everywhere, including employer
  sites (tested).
- **"Have you worked here before" = No**: already covered (default answer bank regex for
  ever/previously/formerly employed + an existing test). No change.
- **General (non-Workday) filler**: exists and is tested — the generic `Engine` handles arbitrary
  careers sites (account creation, multi-page forms, submit, verification stops) against fixtures
  (`AnySiteTests`). Principal is a Jibe-board employer; its applications route through this engine
  (or straight to the employer's own form). The Workday "questions that appear mid-step" fix from
  the latest commits — the `_refill` pass — is present and tested
  (`test_a_question_that_appears_later_and_a_dropped_pick_are_filled`).

## Files changed

Code: `jobbot/companies.py` (new), `jobbot/pagefeed.py`, `jobbot/server.py`, `jobbot/worker.py`,
`jobbot/db.py`, `jobbot/answers.py`, `jobbot/__main__.py`, `jobbot/apply/engine.py`,
`jobbot/apply/workday.py`, `jobbot/static/app.js`, `jobbot/static/app.css`, `CLOUD_WORKER.md`.
Tests: `tests/test_answers.py`, `tests/test_pagefeed.py`, `tests/test_worker.py`,
`tests/test_server.py`, `tests/test_cli.py`, `tests/test_engine.py`,
`tests/fixtures/workday_like.html` (the country-code prompt can now be pre-filled wrong, to prove
the correction).

## What Eric needs to do to use the fixed version

1. **Get the changes back into the JobBot he actually runs.** This work is in a downloaded snapshot
   (`~/workspace/jobbot/test-main/jobs`), not in his Claude session. Either:
   - push these files back to the `ericc112/test` GitHub repo and have the Claude session pull, or
   - paste/attach this report + the changed files into the Claude session and ask it to apply them, or
   - run JobBot locally from this folder (`python -m jobbot serve`) — the local app needs no Claude
     session at all, and it's where instant Apply, logos, profiles, the pay sort and queue-cancel
     already work end-to-end.
2. **Set "How did you hear about us" to LinkedIn in the profile** (page profile, or local Profile →
   "How you found the job"). The filler can now always pick LinkedIn when a form offers it, but the
   profile value is what makes it win *everywhere*, including employer sites.
3. **Still missing: a street address.** The profile has city/state/ZIP but no street address; forms
   that require one will keep stopping at "Needs you" until it's added. Nothing was invented to
   fill it.
4. **For the artifact page specifically**: the page-side items (#1, #3, #4, #6, the page half of #2
   and #7c, the "New since last visit" badge from #7d's new `nw` field, and instant-feeling Apply
   from #9) need changes in the artifact/session itself — the feed now supplies grouped cards,
   `nw` markers, ranks and domains for it to use, and `CLOUD_WORKER.md` now maps the `closed`
   status; the cloud worker session's schedule is what decides how fast an approved application
   actually starts.
