# JobBot

A local web app that searches job boards for you, ranks what it finds against your profile, and fills in (and, if you allow it, submits) applications.

```
 search ──► rank ──► fill the form ──► you review ──► submit ──► track
 9 boards    0-100    real browser      answers +       one click     applied /
             score    (Playwright)      screenshot      or automatic   history
```

It runs on your own computer: it needs a real browser, your resume, and your personal details, and none of that should live on someone else's server.

## Quick start

Needs Python 3.10+.

```bash
cd jobs
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m jobbot            # opens http://localhost:8765
```

Then, in the app:

1. **Profile**: your details, work authorisation, and resume (PDF works best).
2. **Search setup**: job titles, locations, and **companies to watch** (type a company name; JobBot finds its Greenhouse, Lever or Ashby board).
3. Press **Search now**, open a match, and press **Fill application**. JobBot fills the real form in a browser and shows you every answer plus a screenshot. Nothing is sent.
4. Answer anything it flagged, then **Submit application**.
5. When you trust it, turn on **Automation & AI → Search automatically** (and, optionally, **Submit automatically**).

## How applying works

| Step | What happens | Sends anything? |
|---|---|---|
| **Fill** | Opens the application form, answers every question it can, takes a screenshot. Your resume is only attached at Submit. | No |
| **Review** | You see each question, the answer, and where it came from (Profile, Answer bank, You, AI) | No |
| **Submit** | Fills the form again with the answers you reviewed, presses Submit, and checks for a confirmation | Yes |

Each answer comes from the first of these that applies:

1. what you typed for this job in the review screen
2. your **answer bank**: "question contains X → answer Y", saved once and reused everywhere (answers you give in the review screen can be saved here with one tick)
3. rules that read your profile: name, contact details, links, location, work authorisation and sponsorship, education, salary, start date, "how did you hear about us", EEO questions (default: decline to answer)
4. Claude, if you turn on AI, for required questions nothing else covered

A required question with no answer is **never guessed**. The job goes to *Review → Needs you* with the question ready to answer.

### Where it can apply

| Form | Fill | Submit |
|---|---|---|
| Greenhouse, Lever, Ashby (company boards you add, plus aggregator jobs whose Apply link leads there) | ✅ | ✅ (and auto-submit) |
| Other web forms reached from an aggregator listing | ✅ best effort | Only when you press Submit |
| LinkedIn, Indeed, Workday, iCIMS, Taleo and other sign-in sites | ❌ | ❌ (marked *Apply on site*, with a link) |

### Things it won't do

- **Solve CAPTCHAs or get past bot checks.** If a site shows one, the job is marked *Blocked* or *Apply on site*. Turn off *headless* in settings and JobBot waits in a visible browser window while you finish it yourself.
- **Answer questions meant for you.** Questions like "prove you're not a bot" or puzzles are left for you, as are employers' **AI-use attestations**. When a form contains an AI-use policy, AI answers are switched off for that application.
- **Submit anything you didn't approve.** Auto-submit is off by default. When on, it only submits Greenhouse, Lever or Ashby forms where every required question was answered and the match score clears your threshold. It skips forms with AI-written answers unless you allow them, and it stops at your daily limit (default 15) and your per-company limit (default 3 per 30 days).
- **Retry an unconfirmed submit.** If Submit was pressed but no confirmation appeared, the job is marked *Unconfirmed*. Check your email instead of applying twice.

## Job sources

All free, public, no API keys. Every job links back to its original listing.

| Source | What it covers | Refresh |
|---|---|---|
| Greenhouse boards | Companies you add (e.g. Stripe, Airbnb) | 30 min |
| Lever boards | Companies you add (e.g. Palantir) | 30 min |
| Ashby boards | Companies you add (e.g. Ramp, Notion) | 30 min |
| Remotive | Remote jobs | 6 h (their terms ask for ≤ 4 calls a day) |
| Remote OK | Latest remote jobs | 1 h |
| Jobicy | Remote jobs | 1 h |
| Himalayas | Remote jobs (listing pages use a bot check, so these are *Apply on site*) | 1 h |
| Arbeitnow | Europe, mostly Germany (off by default) | 1 h |
| The Muse | Large US/global board (off by default) | 1 h |

Jobs are ranked 0-100. The score combines title match, your skills found in the description, location fit, how recent the posting is, and pay against your minimum. A remote job limited to other countries, or an on-site job elsewhere, loses points. The same job on two boards is shown once, preferring the one JobBot can apply to directly.

## AI answers (optional)

In **Automation & AI**, turn on *Use Claude* and paste an Anthropic API key (or set `ANTHROPIC_API_KEY`). Claude then:

- answers required free-text questions your profile and answer bank don't cover, all in one request per application;
- writes a tailored cover letter when a form has a cover-letter box (optional);
- optionally drafts answers to optional "Why do you want to work here?" questions.

It only sees your profile, your resume text and the job posting. It's told to use only facts from them and to leave a question for you rather than guess. AI answers are labelled **AI** in the review screen. The default model is `claude-opus-5-5`.

## Command line

```bash
python3 -m jobbot serve [--port 8765] [--no-browser]   # the web app (default)
python3 -m jobbot search [--force]                     # fetch all enabled sources once
python3 -m jobbot list [--status new,ready]            # what's stored
python3 -m jobbot prepare JOB_ID                       # fill one application (no submit)
python3 -m jobbot submit JOB_ID                        # fill and submit one application
python3 -m jobbot settings search '{"keywords": ["data engineer"], ...}'
```

## Privacy

- Everything lives in `jobs/data/`: the SQLite database, your resume, screenshots, and your API key if you save one. The folder is git-ignored. Set `JOBBOT_DATA=/some/path` to keep it elsewhere.
- The server listens on `127.0.0.1` only. It has no login, so don't expose it with `--host 0.0.0.0` on a shared network.
- Job boards see ordinary page requests from your computer. Employers only receive what you (or auto-submit) send.

## Tests

```bash
cd jobs
python3 -m unittest discover -s tests -t .
```

The browser tests drive local fixture forms modelled on Greenhouse, Lever and Ashby (`tests/fixtures/`). They cover filling, submitting, confirmations, CAPTCHAs, validation errors, bot walls, new-tab Apply links and human-only questions, without touching the network. They're skipped if Chromium isn't installed.

## Layout

```
jobbot/
  sources/        one module per job board (fetch + normalise)
  scoring.py      0-100 match score with reasons
  ats.py          recognise Greenhouse/Lever/Ashby, resolve aggregator Apply links
  answers.py      question → answer rules, answer bank, safety checks
  llm.py          optional Claude answers and cover letters
  apply/          Playwright engine + in-page form extractor (extract.js)
  pipeline.py     search, rescore, auto-submit policy, scheduler
  worker.py       background browser worker
  server.py       FastAPI app; static/ holds the UI
```
