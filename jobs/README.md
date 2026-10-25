# JobBot

A local web app that watches employers' own career sites for you, ranks what it finds against your profile, and fills in (and, if you allow it, submits) applications.

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
- **Oracle Recruiting Cloud** (JPMorgan Chase, and about 30 more large employers)
- **SAP SuccessFactors**, **Jibe** and **Phenom** career sites (John Deere, Union Pacific, State Farm, AMD, Molson Coors…)
- **Amazon's own careers site**

While JobBot is running, a watcher re-checks every employer on your list every 5 minutes (adjustable down to 1).
- **Unchanged boards cost nothing:** they answer with an empty "no change" (HTTP 304), so this is cheap for both sides. Only new postings that fit your search are downloaded in full.
- **New postings are flagged and acted on:** anything that appears after JobBot's first look at a board is marked **Just posted**, listed at the top of the dashboard, and (optionally) sent as a desktop alert. Strong matches are filled straight away, so they're waiting in your review queue.
- **Speed is measured:** the dashboard shows how long, after the employer published it, each new posting took to reach you. In testing, new Stripe and Cloudflare postings were caught 0.6 to 1.3 minutes after they went live.

JobBot ships watching about 50 employers with lots of business roles, plus every **Fortune 500** company whose careers site runs on one of the systems above: 322 of them. `jobbot/fortune500.json` lists the 498 companies in Fortune's data (it skips ranks 161 and 351), with each one's careers site and job system. Each feed was checked against the live site, including the employer each Workday site says it hires for. Of the other 176, 45 use systems JobBot can't read yet (Eightfold, iCIMS, Taleo, Avature and others), and 131 have no public job feed JobBot could find (Walmart, Apple and Microsoft among them). Add or remove them in **Search setup**: type a company name, or paste a link to one of its job posts (for Workday, a link from its `…myworkdayjobs.com` careers site).

Workday, Taleo and other careers sites ask applicants to create an account with each employer. Once you set the password (see *Employer accounts* below), JobBot signs in or creates that account and fills the form; without one it alerts you and links to the posting.

It runs on your own computer: it needs a real browser, your resume, and your personal details, and none of that should live on someone else's server.

## Opening JobBot

The easy way: double-click **Start-JobBot.bat** in this folder. The first time you run it, it installs what JobBot needs (the Python packages and its browser) and then opens JobBot for you; after that, a double-click just opens it. Leave its window open while you use JobBot — closing it turns JobBot off.

Prefer to type it yourself? The commands are:

```bash
cd jobs
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m jobbot
```

Either way, JobBot opens in your browser at **http://localhost:8765**. That page only exists while JobBot is running — it lives on your own computer, not on the internet, so if the page won't load, JobBot isn't running: double-click Start-JobBot.bat again.

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

## Apply from your phone, without a computer

The JobBot page on claude.ai (see `CLOUD_WORKER.md`) lists the internships and can apply for you:

1. Open **Your profile** on the page, fill in your details and upload your resume (PDF). Only you can see it.
2. Set `JOBBOT_WORKDAY_PASSWORD` in your Claude cloud environment's settings (the environment menu → **Edit** → environment variables): the one password JobBot uses for your accounts on employers' careers sites (Workday, Taleo, iCIMS, SuccessFactors and the rest). Never paste it into a chat or the page.
3. Tap **Apply** on an internship. That's it: a scheduled Claude cloud session runs JobBot every 3 hours (or right away when you tap **Start now**), fills in the application and sends it. The result, every answer and a screenshot show up under **Applying**.
4. If the form asks something your profile and saved answers don't cover, the cloud session answers it the way JobBot's AI does (the best answer your information supports; see [AI answers](#ai-answers-optional)) and sends the application, with those answers labelled **AI**. Only a question whose honest answer needs a fact JobBot doesn't have shows up under **Applying** with the employer's own choices: answer it and tap **Apply with these answers**.

The page lists the internships JobBot can send by itself; tick **Show ones you apply to on their site** for the rest. A scheduled cloud session rebuilds the list twice a day (`jobs/LIST_REFRESH.md`, which runs `python3 -m jobbot page-feed --search`), so it is never more than a day old, and leaves out postings 30 or more days old. **Add a link** takes a posting from any site, LinkedIn and Indeed included (see *Where it can apply*). The cloud session only sends applications you tapped Apply on, and stops if a site shows a CAPTCHA, a bot check or an email confirmation.

### Jobs from screenshots (Runway or any job board)

The page's **Upload** tab takes screenshots, a short screen recording of you scrolling a job board, a PDF, or listings you copied there. The cloud worker reads them itself, without AI: OCR for pictures (one still a second from a recording, skipping repeats), then it splits the text into listings (title, company, location, when posted, and the board's own match score). It keeps the business roles the board scored at or above your minimum (90 unless you change it), looks each one up on the employer's own careers site, and lists it with **Apply**. Nothing is sent until you tap Apply. Pictures carry no links, so a job the employer's site doesn't list by that title comes back "not found" with a search link. JobBot never signs in to the board: you take the screenshots.

The same runs on the command line (`pip install -r requirements-ocr.txt` first for pictures and recordings):

```bash
python3 -m jobbot read-listings shot1.png shot2.png scroll.mp4 --min-score 90 --out found.json
python3 -m jobbot read-listings --text copied.txt --no-find      # just read, don't look anything up
```

## How applying works

| Step | What happens | Sends anything? |
|---|---|---|
| **Fill** | Opens the application form, answers every question it can, takes a screenshot. Your resume is only attached at Submit. | No |
| **Review** | You see each question, the answer, and where it came from (Profile, Answer bank, You, AI) | No |
| **Submit** | Fills the form again with the answers you reviewed, presses Submit, and checks for a confirmation | Yes |

Each answer comes from the first of these that applies:

1. what you typed for this job in the review screen
2. your **answer bank**: "question contains X → answer Y", saved once and reused everywhere (answers you give in the review screen can be saved here with one tick)
3. rules that read your profile: name, contact details, links, location, work authorisation and sponsorship, education and student questions, salary, start date, "how did you hear about us" (for jobs found on the employer's own site: their website or careers page), EEO questions (default: decline to answer); common screening questions: conflicts of interest, government and political ties, background, availability and shifts, locations, cohorts and areas of interest (this job's first, then near you, then "no preference"), residency, languages, tools you've used, your last available date (from the program dates in the posting), the employer's AI screening and contact about other jobs (agreed; marketing follows your opt-in), with answers matched to however the form words its options ("Not to my knowledge", "I have never been employed by…", a salary or experience range); and ties to the employer: "Have you worked here before?" and "Does anyone in your family work here?" are Yes for the companies you list in your profile and No everywhere else, with their "If yes, give the details" follow-ups left blank or "N/A"
4. Claude, if you turn on AI, for required questions nothing else covered: the best answer your information supports (see [AI answers](#ai-answers-optional))

Without AI, a required question with no answer is never guessed: the job goes to *Review → Needs you* with the question ready to answer. With AI on, that only happens when the honest answer needs a fact JobBot doesn't have (a reference's phone number, a license number).

### Where it can apply

| Form | Fill | Submit |
|---|---|---|
| Greenhouse, Lever, Ashby (company boards you add, plus aggregator jobs whose Apply link leads there) | ✅ | ✅ (and auto-submit) |
| Workday career sites (Target, Capital One, P&G and the other Workday employers JobBot watches), once you set the password | ✅ signs in, or creates your account with that employer | ✅ (and auto-submit) |
| Taleo Business Edition sites (`…tbe.taleo.net`, e.g. Olin) | ✅ signs in, or creates your account | ✅ (and auto-submit) |
| Any other careers site: iCIMS, SuccessFactors, Workable, SmartRecruiters, Jobvite, Paylocity, employers' own forms… | ✅ best effort: follows Apply, signs in or creates your account if asked, fills each page and presses Next until Submit, including forms inside a frame | Only when you press Submit |
| LinkedIn, Indeed, Glassdoor, ZipRecruiter and other job boards | ✅ on the employer's own site, when JobBot finds the same job there | Only when you press Submit |
| LinkedIn Easy Apply, Indeed Apply, Oracle and Amazon careers sites | ❌ (marked *Apply on site*, with a link) | ❌ |

**Job boards.** LinkedIn, Indeed and the like copy employers' postings, and their Apply needs you signed in to the board (LinkedIn shows the employer's link only to members). JobBot never signs in to a job board; it reads the posting's title, company and location, and looks for the same job where the employer posts it: the job systems it knows for that company, the company's careers page (and the Workday, Taleo, iCIMS, SuccessFactors, Greenhouse, Lever, Ashby, Workable or SmartRecruiters site it links to), and boards under the company's name (`jobbot/finder.py`). Some employers' sites turn scripted visits away; then the job is marked *Apply on site* and you can paste the employer's link instead.

### Employer accounts

Workday, Taleo and many other careers sites make you sign in to each employer's site. JobBot uses your profile email (or `JOBBOT_WORKDAY_EMAIL`) and **one password** you choose, signs in when you have an account there, and creates it the first time it applies to that employer otherwise (Workday's rule: 8+ characters with upper and lower case, a number and a symbol). It reads the password from the environment variable `JOBBOT_WORKDAY_PASSWORD`: start JobBot with it set (`JOBBOT_WORKDAY_PASSWORD='…' python3 -m jobbot`), or, for the phone page, set it in your Claude cloud environment. Without one, these jobs are marked *Apply on site*.

Filling in can save a draft in your account with that employer (Workday stops at its Review step); nothing is sent until you press Submit. If a site asks you to confirm your email, JobBot stops: click the link in the email, then try again. If you already have an account there with another password, JobBot says so: use the site's "Forgot password" to set it to JobBot's.

### Things it won't do

- **Solve CAPTCHAs or get past bot checks.** If a site shows one, the job is marked *Blocked* or *Apply on site*. Turn off *headless* in settings and JobBot waits in a visible browser window while you finish it yourself.
- **Answer questions meant for you.** Questions like "prove you're not a bot" or puzzles are left for you, as are employers' **AI-use attestations**. When a form contains an AI-use policy, AI answers are switched off for that application.
- **Submit anything you didn't approve.** Auto-submit is off by default. When on, it only submits Greenhouse, Lever, Ashby, Workday or Taleo forms where every required question was answered and the match score clears your threshold. It skips forms with AI-written answers unless you allow them, and it stops at your daily limit (default 15) and your per-company limit (default 3 per 30 days).
- **Retry an unconfirmed submit.** If Submit was pressed but no confirmation appeared, the job is marked *Unconfirmed*. Check your email instead of applying twice.

## Job sources

All free, public, no API keys. Every job links back to its original listing. The first nine are employers' own job systems. With the Fortune 500 on the list (about 450 feeds) the watcher spreads its checks out, so each employer is re-checked about every 5 minutes. The rest are job boards. They re-list employers' jobs later and link to their own pages instead of the employer's, so they're off by default; turn any of them on in **Search setup → Sources**.

| Source | What it covers | Refresh |
|---|---|---|
| Greenhouse boards | Employers you watch (e.g. Stripe, Toast) | every 5 min (watcher) |
| Lever boards | Employers you watch (e.g. Palantir, Spotify) | every 5 min (watcher) |
| Ashby boards | Employers you watch (e.g. Ramp, Notion) | every 5 min (watcher) |
| Workday career sites | Employers you watch (e.g. Capital One, Citi, PwC) | every 5 min (watcher) |
| Oracle Recruiting Cloud | Employers you watch (e.g. JPMorgan Chase) | every 5 min (watcher) |
| SuccessFactors career sites | Employers you watch (e.g. John Deere, CHS, Hershey) | every 5 min (watcher) |
| Jibe career sites | Employers you watch (e.g. State Farm, AMD, Principal) | every 5 min (watcher) |
| Phenom career sites | Employers you watch (e.g. Molson Coors, Zimmer Biomet) | every 5 min (watcher) |
| Amazon careers site | Amazon's US postings | every 5 min (watcher) |
| Remotive | Remote jobs (off by default) | 6 h (their terms ask for ≤ 4 calls a day) |
| Remote OK | Latest remote jobs (off by default) | 1 h |
| Jobicy | Remote jobs (off by default) | 1 h |
| Himalayas | Remote jobs (off by default; listing pages use a bot check, so these are *Apply on site*) | 1 h |
| Arbeitnow | Europe, mostly Germany (off by default) | 1 h |
| The Muse | Large US/global board, queried by business categories (off by default) | 1 h |

### The business-major filter

Every job is classified by its **title** first, because board categories are unreliable on their own: The Muse files baristas and welders under "Business Operations". A role passes when its title names a business function (e.g. *Financial Analyst*, *Account Executive*, *Supply Chain Analyst*, *Talent Acquisition Partner*), and nothing in it marks a technical, clinical or trade role (*engineer*, *developer*, *designer*, *nurse*, *technician*, *warehouse*…). Words like *medical*, *technical* or *retail* only pass alongside a clear business role, so *Medical Sales Representative* and *Retail Buyer* stay while *Store Manager* goes. Vague titles (*Associate*, *Analyst*) are decided by the job's department: Finance yes, Engineering no. Boards that support it are also queried by business category (The Muse, Jobicy) or business role names (Himalayas).

**Paid internships only** (on by default, in **Search setup**). Anything that says it's unpaid, for academic credit only, or commission- or equity-only is hidden. On job boards, an internship must also say it's paid (a pay rate, "paid internship", "hourly rate"…), because that's where unpaid listings hide; internships on employers' own careers sites stay even when the posting doesn't give the rate.

**Pay is shown in dollars per hour.** JobBot reads it from the board's salary fields or the pay range in the description ("$29 - $33 per hour", "Base Salary: $45,000 – $60,000"), and ignores dollar figures that aren't wages (funding, stipends, referral bonuses). Yearly or monthly pay is converted at 40 hours a week and marked "≈". When a posting lists rates by degree level, the undergraduate rate is shown.

Jobs are ranked 0-100. The score combines title match, your skills found in the description, location fit, how recent the posting is, and pay against your minimum. Roles that ask for a business degree get a small boost, as do jobs JobBot can apply to directly. A remote job limited to other countries, or an on-site job elsewhere, loses points. The same job on two boards is shown once, preferring the one JobBot can apply to directly.

## AI answers (optional)

In **Automation & AI**, turn on *Use Claude* and paste an Anthropic API key (or set `ANTHROPIC_API_KEY`). Claude then:

- answers the required questions your profile and answer bank don't cover (free text and multiple choice), in one request per page of the form;
- writes a tailored cover letter when a form has a cover-letter box (optional);
- optionally drafts answers to optional "Why do you want to work here?" questions.

It sees your profile, your answer bank, your resume text and the job posting, and gives the answer you would give, so applications don't stop for you:

- **facts** come from your profile and resume, and from what follows from them (living in Texas means you're not a California resident; a U.S. citizen needs no sponsorship);
- **choices** like cohort, start and end dates, office or shift go to whatever fits you and the posting (the program's dates, the location nearest you);
- **"Why us?" and experience questions** get a specific answer built from your real experience;
- **acknowledgements and consents** are agreed to, and conflict questions it has no sign of (relatives there, a non-compete) are answered "no";
- **sensitive questions** (criminal history, disability, demographics) get "decline to answer" when the form offers it.

It never invents employers, dates, grades, certifications or results, or a legal status your profile doesn't give; a question that would need one is left for you. AI answers are labelled **AI** in the review screen. To let applications with AI answers go out on their own, also tick *Auto-submit even when some answers were written by AI*. The default model is `claude-opus-5-5`; with prompt caching, answering a page's leftover questions usually costs a few cents.

## Command line

```bash
python3 -m jobbot serve [--port 8765] [--no-browser]   # the web app (default)
python3 -m jobbot search [--force]                     # fetch all enabled sources once
python3 -m jobbot list [--status new,ready]            # what's stored
python3 -m jobbot prepare JOB_ID                       # fill one application (no submit)
python3 -m jobbot submit JOB_ID                        # fill and submit one application
python3 -m jobbot apply-batch requests.json --profile profile.json [--resume cv.pdf] --out results.json  # the cloud worker's runner
python3 -m jobbot read-listings FILES... [--text copied.txt] [--min-score 90] --out found.json  # jobs from screenshots or recordings
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
  sources/        one module per job source (fetch + normalise); http.py does ETag/304 polling
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
