# JobBot

A local web app that searches job boards for you, ranks what it finds against your profile, and fills in (and, if you allow it, submits) applications.

It's set up for **business majors looking for internships**. Full-time jobs are one checkbox away in **Search setup** (*What you're looking for*), for when you graduate. It only shows and applies to roles that suit a business degree (finance & accounting, consulting & strategy, operations & supply chain, marketing & communications, sales & business development, HR & people, project & product management, and business analytics). Engineering, design, healthcare, trades, hospitality and similar roles are filtered out. You can narrow it to some of those areas, list specific titles, or switch the filter off.

```
 watch ──► rank ──► fill the form ──► you review ──► submit ──► track
 employer  0-100    real browser      answers +       one click     applied /
 sites     score    (Playwright)      screenshot      or automatic   history
 every 5 min
```

## Internships first

By default JobBot looks for internships only: summer, semester and co-op internships, including *Summer Analyst* and similar programs. Part-time, seasonal and temporary jobs are always left out.

- **Every source asks for internships:** Workday sites are queried through their own intern/student filter (each employer's *Intern* worker type or *Students & Graduates* category), The Muse by its *Internship* level, Himalayas and Jobicy by intern searches. Greenhouse, Lever and Ashby boards are read in full and filtered by title and the board's own job-type labels.
- **Only internships you can still do:** an internship for a season that's already over (e.g. *Summer 2026* in October 2026) is hidden. Internships for MBA or graduate students are hidden while you're an undergraduate, and undergraduate programs are hidden if you're in grad school. A UK-style *Graduate Program* (for new graduates) is not counted as grad school.
- **The term you want ranks first:** set *Internship terms you want* (e.g. *Summer 2027*) in **Profile → Student**. Each listing shows its season, e.g. *Internship · Summer 2027*.
- **Student questions are answered for you:** fill in **Profile → Student** (currently enrolled, year in school, expected graduation, GPA, minor) and JobBot answers GPA ranges, graduation date in any format (*May 2028*, *Spring 2028*, *Class of 2028*, a date picker or separate month and year boxes), year in school, "will you return to school", which term, and "can you commit to the full 12 weeks". Leave GPA blank to answer GPA questions yourself.
- **It won't make up your history:** Greenhouse's employment block takes the company and title from your profile, but the dates of past jobs are left for you. The end date in an education block is your graduation date.

## New postings, as soon as they're published

Indeed, LinkedIn and other aggregators copy jobs from employers' sites, often hours or days later. JobBot goes to the source instead. It reads each employer's own job system, which is the same data the company's careers page shows:

- **Greenhouse, Lever and Ashby** (Stripe, Toast, Brex, Ramp, Plaid…)
- **Workday** (Capital One, Citi, Wells Fargo, Bank of America, PwC, Accenture, Fidelity, BlackRock, Nike, Target…)

While JobBot is running, a watcher re-checks every employer on your list every 5 minutes (adjustable down to 1).
- **Unchanged boards cost nothing:** they answer with an empty "no change" (HTTP 304), so this is cheap for both sides. Only new postings that fit your search are downloaded in full.
- **New postings are flagged and acted on:** anything that appears after JobBot's first look at a board is marked **Just posted**, listed at the top of the dashboard, and (optionally) sent as a desktop alert. Strong matches are filled straight away, so they're waiting in your review queue.
- **Speed is measured:** the dashboard shows how long, after the employer published it, each new posting took to reach you. In testing, new Stripe and Cloudflare postings were caught 0.6 to 1.3 minutes after they went live.

JobBot ships watching about 50 employers with lots of business roles. Add or remove them in **Search setup**: type a company name, or paste a link to one of its job posts (for Workday, a link from its `…myworkdayjobs.com` careers site).

Workday asks applicants to create an account with each employer, so for Workday jobs JobBot alerts you and links to the posting instead of filling the form.

It runs on your own computer: it needs a real browser, your resume, and your personal details, and none of that should live on someone else's server.

## Quick start

Needs Python 3.10+.

```bash
cd jobs
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m jobbot            # opens http://localhost:8765 (add --phone to use it on your phone too)
```

Then, in the app:

1. **Profile**: your details, work authorisation, resume (PDF works best), and the **Student** section (graduation date, year in school, GPA, the internship term you want).
2. **Search setup**: choose internships and/or full-time jobs, pick your business areas and locations, and add **companies to watch**. There's a one-click list of companies with lots of business roles (Stripe, Toast, Brex, Flexport, Ramp…), or type any company name and JobBot finds its Greenhouse, Lever or Ashby board.
3. Press **Search now**, open a match, and press **Fill application**. JobBot fills the real form in a browser and shows you every answer plus a screenshot. Nothing is sent.
4. Answer anything it flagged, then **Submit application**.
5. When you trust it, turn on **Automation & AI → Search automatically** (and, optionally, **Submit automatically**).

## Use it on your phone

JobBot runs on your computer, and your phone can open it too:

```bash
python3 -m jobbot --phone
```

The terminal (and **Automation & AI → Phone** on the computer) shows a QR code. Scan it with your phone's camera and JobBot opens in your phone's browser. The link carries a private key: the phone stays signed in, and any other device that hasn't opened the link gets nothing. **New link** signs every phone out.

- Your phone has to be on the **same Wi-Fi** as the computer, and the computer has to stay on with JobBot running: it's the computer that searches and fills the forms.
- The first time, your computer may ask whether Python can accept incoming connections. Choose **Allow** (private networks).
- **Campus, office and public Wi-Fi often block devices from reaching each other.** Install [Tailscale](https://tailscale.com) (free) on the computer and the phone, sign both into the same account, then start JobBot with `python3 -m jobbot --phone-address <computer's Tailscale name or 100.x address>`. That works from anywhere, including over cellular data, and the connection is encrypted.
- Tip: on the phone, use **Share → Add to Home Screen** to open JobBot like an app.

## How applying works

| Step | What happens | Sends anything? |
|---|---|---|
| **Fill** | Opens the application form, answers every question it can, takes a screenshot. Your resume is only attached at Submit. | No |
| **Review** | You see each question, the answer, and where it came from (Profile, Answer bank, You, AI) | No |
| **Submit** | Fills the form again with the answers you reviewed, presses Submit, and checks for a confirmation | Yes |

Each answer comes from the first of these that applies:

1. what you typed for this job in the review screen
2. your **answer bank**: "question contains X → answer Y", saved once and reused everywhere (answers you give in the review screen can be saved here with one tick)
3. rules that read your profile: name, contact details, links, location, work authorisation and sponsorship, education and student questions, salary, start date, "how did you hear about us" (for jobs found on the employer's own site: their website or careers page), EEO questions (default: decline to answer)
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

All free, public, no API keys. Every job links back to its original listing. The first four are employers' own job systems. The rest are aggregators, which are useful for companies you don't watch but lag behind.

| Source | What it covers | Refresh |
|---|---|---|
| Greenhouse boards | Employers you watch (e.g. Stripe, Toast) | every 5 min (watcher) |
| Lever boards | Employers you watch (e.g. Palantir, Spotify) | every 5 min (watcher) |
| Ashby boards | Employers you watch (e.g. Ramp, Notion) | every 5 min (watcher) |
| Workday career sites | Employers you watch (e.g. Capital One, Citi, PwC) | every 5 min (watcher) |
| Remotive | Remote jobs | 6 h (their terms ask for ≤ 4 calls a day) |
| Remote OK | Latest remote jobs | 1 h |
| Jobicy | Remote jobs | 1 h |
| Himalayas | Remote jobs (listing pages use a bot check, so these are *Apply on site*) | 1 h |
| Arbeitnow | Europe, mostly Germany (off by default) | 1 h |
| The Muse | Large US/global board, queried by business categories | 1 h |

### The business-major filter

Every job is classified by its **title** first, because board categories are unreliable on their own: The Muse files baristas and welders under "Business Operations". A role passes when its title names a business function (e.g. *Financial Analyst*, *Account Executive*, *Supply Chain Analyst*, *Talent Acquisition Partner*), and nothing in it marks a technical, clinical or trade role (*engineer*, *developer*, *designer*, *nurse*, *technician*, *warehouse*…). Words like *medical*, *technical* or *retail* only pass alongside a clear business role, so *Medical Sales Representative* and *Retail Buyer* stay while *Store Manager* goes. Vague titles (*Associate*, *Analyst*) are decided by the job's department: Finance yes, Engineering no. Boards that support it are also queried by business category (The Muse, Jobicy) or business role names (Himalayas).

Jobs are ranked 0-100. The score combines title match, your skills found in the description, location fit, how recent the posting is, and pay against your minimum. Roles that ask for a business degree get a small boost, as do jobs JobBot can apply to directly. A remote job limited to other countries, or an on-site job elsewhere, loses points. The same job on two boards is shown once, preferring the one JobBot can apply to directly.

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
  sources/        one module per job board (fetch + normalise); http.py does ETag/304 polling
  fields.py       business-major classifier (areas, blocked roles, board categories)
  scoring.py      0-100 match score with reasons
  ats.py          recognise Greenhouse/Lever/Ashby, resolve aggregator Apply links
  answers.py      question → answer rules, answer bank, safety checks
  llm.py          optional Claude answers and cover letters
  apply/          Playwright engine + in-page form extractor (extract.js)
  pipeline.py     search, rescore, auto-submit policy, scheduler, employer-site watcher
  worker.py       background browser worker
  server.py       FastAPI app; static/ holds the UI
```
