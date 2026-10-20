# JobBot page (artifact): fixes the page itself needs

The JobBot page (https://claude.ai/artifact/VgAScmZAL2HXzL9FwQG8fj) is a Claude artifact. **Its source is not in
this repo**, so the UI bugs below can't be fixed here. This branch changes what the page *reads* (`page-feed`,
see `jobbot/pagefeed.py`); the page has to be updated (in the Claude session that owns it) to use it, then
republished. Paste this file into that session.

## New fields on each listing (`jobs/p<n>` items)
| field | meaning |
|---|---|
| `n`, `more` | one card per company + title. `n` = how many postings; `more` = `[{k, u, loc, st}]` for the other locations. Show "Houston, TX + 5 more" and let the user pick a location; Apply sends that location's `k`/`u`. |
| `b` | Best-match order: score plus a recency boost (+8 under 1 day, +5 under 3, +2 under 7). The list arrives already in this order, with at most 3 cards per company in the first 60. Keep showing `s` as the score. |
| `new` | first appeared in this refresh. For "New since last visit", store the last visit time in the page and compare with `f`. |
| `f500`, `rank`, `web`, `car` | Fortune 500 flag, rank, website and careers page (from `fortune500.json`, only when the company is in it). |
| `logo`, `dom`, `ini` | logo URL (site favicon), domain, and initials to show when there is no logo or it fails to load (`onerror`). |

New `meta/feed` fields: `postings`, `grouped`, `new_this_run`, `posted_last_day`, `non_f500` (companies outside
the Fortune 500, from the hand-picked watch list), `feed_errors` / `feeds_failed` (which feeds failed this run).

## Page changes needed (items 1-9)
1. **Filter counts:** compute each dropdown's counts from the list filtered by search and every *other* active filter.
2. **Pay sort:** sort after filtering (one `filtered → sorted → paged` pipeline), by `hr` descending, missing pay last.
3. **Search/list mismatch:** derive results from the current input value (or a single state value) every render; no cached result list.
4. **Applying tab:** hide pay, area, season and location filters there (or show status filters instead).
5. **Dead ends:** status `closed` (or a note saying the posting is closed / taken down) → "Closed", no Try again. For CAPTCHA, email code,
   verification link, password reset and rate limits show "What you need to do" with an Open posting button, and for email
   steps a Gmail search link (e.g. `https://mail.google.com/mail/u/0/#search=<company>`).
6. **Polish:** area chips `flex-wrap: wrap` (or `overflow-x: auto`); show the Sharing tip below the header, not over the top-right corner.
7. **Repeats:** use `more`/`n` for one card per title; render with a "Load more" button (e.g. 50 at a time) instead of cutting at 200;
   a "New since last visit" badge and filter; show `feeds_failed` next to "Updated … ago". "Refresh now" can only ask for a refresh
   (write a `meta/refresh_request` document) — the list is rebuilt by the scheduled `LIST_REFRESH.md` session.
8. **Logos and profile:** `<img src=logo>` with the `ini` badge as fallback; clicking the company shows rank, website and careers link
   (only fields present; don't show made-up industry/HQ/size — they aren't in the data yet).
9. **Apply:** see below.

## Why Apply doesn't send right away (item 9)
Tapping Apply writes an `approved` document to `data/users/me/apps/items`. Nothing runs at that moment: an artifact is a page
in a sandbox; it can read and write its own database but cannot start a Claude session, run Python or open a browser. The
applications are sent by the scheduled cloud session in `CLOUD_WORKER.md`, which picks up every `approved` request on each run
(already automatic; you don't need to message the chat), currently every 3 hours.

To make it feel instant, pick one:
- **Run the worker more often** (e.g. every 15-30 minutes). Simplest; empty runs stop at once ("Nothing to apply to").
- **Small backend:** a hosted service (e.g. a VM or Fly.io/Render container with Chromium) that watches the database or receives a
  webhook when Apply is tapped and runs `python3 -m jobbot apply-batch`. This needs the artifact's database to be reachable from
  outside (or the page to call the webhook directly, if the artifact sandbox allows network requests), plus the profile, resume and
  `JOBBOT_WORKDAY_PASSWORD` stored on that server.
- **Run JobBot locally** (`python3 -m jobbot --phone`): its own UI submits immediately.

Card status to show: `approved` → "Queued (next run in ~N min)", `working` → "Submitting", `submitted` → "Submitted",
`needs_you`/`needs_input`/`manual` → "Needs you".
