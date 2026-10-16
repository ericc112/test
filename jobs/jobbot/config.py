"""Paths and default settings.

Everything personal (profile, resume, database, screenshots) lives under DATA_DIR,
which is git-ignored. Override it with the JOBBOT_DATA environment variable.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("JOBBOT_DATA", ROOT / "data"))
DB_PATH = DATA_DIR / "jobbot.db"
FILES_DIR = DATA_DIR / "files"
SHOTS_DIR = DATA_DIR / "screenshots"

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0 Safari/537.36"
)

DEFAULT_PROFILE = {
    "first_name": "",
    "last_name": "",
    "preferred_name": "",
    "pronouns": "",
    "email": "",
    "phone": "",
    "address": "",
    "city": "",
    "state": "",
    "postal_code": "",
    "country": "United States",
    "linkedin": "",
    "github": "",
    "website": "",
    "twitter": "",
    "current_company": "",
    "current_title": "",
    "years_experience": "",
    "school": "",
    "degree": "",
    "discipline": "",
    "graduation_year": "",
    # Students
    "currently_enrolled": True,
    "school_year": "",  # Freshman | Sophomore | Junior | Senior | Graduate student
    "expected_graduation": "",  # e.g. "May 2028"
    "gpa": "",
    "minor": "",
    "internship_terms": "",  # e.g. "Summer 2027"
    "languages": "English",
    "skills": "",
    "summary": "",
    "work_authorized": True,
    "needs_sponsorship": False,
    "willing_to_relocate": False,
    # remote | hybrid | onsite | any
    "remote_preference": "any",
    "salary_expectation": "",
    "availability": "Two weeks after an offer",
    "how_heard": "Job board",
    # Voluntary self-identification. "decline" picks the "I don't wish to answer" option.
    "eeo_gender": "decline",
    "eeo_race": "decline",
    "eeo_hispanic": "decline",
    "eeo_veteran": "decline",
    "eeo_disability": "decline",
    # Tick required "I have read the privacy notice" style boxes.
    "accept_privacy_terms": True,
    # SMS / WhatsApp / newsletter opt-ins.
    "marketing_opt_in": False,
    "cover_letter": (
        "Dear {company} hiring team,\n\n"
        "I'm excited to apply for the {title} role. {summary}\n\n"
        "I'd welcome the chance to talk about how I can help {company}.\n\n"
        "Best regards,\n{name}"
    ),
    "resume_file": "",
    "resume_text": "",
    "cover_letter_file": "",
}

# Answers you give once and reuse everywhere. "q" is matched against the question
# text (case-insensitive substring, or a regex when "regex" is true).
DEFAULT_ANSWERS = [
    {"q": r"\b(18|eighteen) years|of legal (working )?age", "a": "Yes", "regex": True},
    {"q": r"background (check|screen|investigation)", "a": "Yes", "regex": True},
    {"q": r"drug (test|screen)", "a": "Yes", "regex": True},
    {"q": "security clearance", "a": "No"},
    {"q": r"non-?compete|non-?solicit", "a": "No", "regex": True},
    {
        "q": r"(ever|previously|formerly|currently) (been )?(employed|work(ed|ing)) (by|for|at)|former employee",
        "a": "No",
        "regex": True,
    },
    {"q": r"(were|are) you referred|referred by|employee referral", "a": "No", "regex": True},
    {"q": r"available .{0,25}(full[- ]time|40 hours)|commit to (the )?(full|entire)|(10|11|12|ten|eleven|twelve)[- ]week",
     "a": "Yes", "regex": True},
]

DEFAULT_SEARCH = {
    # "business" keeps only roles that suit a business major (see fields.py); "" = any field.
    "field": "business",
    # Business areas to include (all by default).
    "families": ["finance", "consulting", "operations", "marketing", "sales", "hr", "management", "analytics"],
    # internship and/or full_time. Part-time, seasonal and temporary roles never match.
    "job_types": ["internship"],
    # Optional: only titles containing every word of one of these lines.
    "keywords": [],
    "exclude": ["director", "vice president", "vp", "head of"],
    "locations": ["Remote", "United States"],
    # any | remote_only | onsite_only
    "remote": "any",
    "min_salary": 0,
    "max_age_days": 30,
    "sources": {
        "greenhouse": True,
        "lever": True,
        "ashby": True,
        "remotive": True,
        "remoteok": True,
        "jobicy": True,
        "himalayas": True,
        "arbeitnow": False,
        "themuse": True,
        "workday": True,
        "oracle": True,
    },
    # Employer job boards to watch; filled from SUGGESTED_COMPANIES below.
    "companies": {},
}

# Employers with many business roles whose own job systems JobBot can read
# (checked October 2026). Watched by default; remove any in Search setup.
# Greenhouse/Lever/Ashby jobs can be applied to directly. Workday needs an account
# with each employer, so those are alerts with a link.
SUGGESTED_COMPANIES = [
    ("Stripe", "greenhouse", "stripe"), ("Toast", "greenhouse", "toast"), ("Datadog", "greenhouse", "datadog"),
    ("Databricks", "greenhouse", "databricks"), ("MongoDB", "greenhouse", "mongodb"), ("Cloudflare", "greenhouse", "cloudflare"),
    ("Brex", "greenhouse", "brex"), ("Flexport", "greenhouse", "flexport"), ("Okta", "greenhouse", "okta"),
    ("Samsara", "greenhouse", "samsara"), ("Ramp", "ashby", "ramp"), ("Coinbase", "greenhouse", "coinbase"),
    ("Airbnb", "greenhouse", "airbnb"), ("Klaviyo", "greenhouse", "klaviyo"), ("Notion", "ashby", "notion"),
    ("Plaid", "ashby", "plaid"), ("Palantir", "lever", "palantir"), ("Instacart", "greenhouse", "instacart"),
    ("Affirm", "greenhouse", "affirm"), ("Gusto", "greenhouse", "gusto"), ("Pinterest", "greenhouse", "pinterest"),
    ("Robinhood", "greenhouse", "robinhood"), ("Spotify", "lever", "spotify"), ("SoFi", "greenhouse", "sofi"),
    ("Capital One", "workday", "capitalone|wd12|Capital_One"), ("Citi", "workday", "citi|wd5|2"),
    ("Wells Fargo", "workday", "wf|wd1|WellsFargoJobs"), ("Bank of America", "workday", "ghr|wd1|Lateral-US"),
    ("Morgan Stanley", "workday", "ms|wd5|External"), ("U.S. Bank", "workday", "usbank|wd1|US_Bank_Careers"),
    ("PNC", "workday", "pnc|wd5|External"), ("Truist", "workday", "truist|wd1|Careers"),
    ("Northern Trust", "workday", "ntrs|wd1|northerntrust"), ("State Street", "workday", "statestreet|wd1|Global"),
    ("BlackRock", "workday", "blackrock|wd1|BlackRock_Professional"), ("Fidelity", "workday", "fmr|wd1|FidelityCareers"),
    ("T. Rowe Price", "workday", "troweprice|wd5|TRowePrice"), ("Mastercard", "workday", "mastercard|wd1|CorporateCareers"),
    ("PayPal", "workday", "paypal|wd1|jobs"), ("S&P Global", "workday", "spgi|wd5|SPGI_Careers"),
    ("PwC", "workday", "pwc|wd3|Global_Experienced_Careers"), ("Accenture", "workday", "accenture|wd103|AccentureCareers"),
    ("Travelers", "workday", "travelers|wd5|External"), ("Allstate", "workday", "allstate|wd5|allstate_careers"),
    ("Nike", "workday", "nike|wd1|nke"), ("Target", "workday", "target|wd5|targetcareers"),
    ("Unilever", "workday", "unilever|wd3|Unilever_Experienced_Professionals"), ("Gap Inc.", "workday", "gapinc|wd1|GAPINC"),
    ("Nordstrom", "workday", "nordstrom|wd501|nordstrom_careers"), ("Salesforce", "workday", "salesforce|wd12|External_Career_Site"),
    ("Disney", "workday", "disney|wd5|disneycareer"),
]


def _fortune500():
    """The 2026 Fortune 500 with each company's careers site and the feeds JobBot reads (fortune500.json)."""
    try:
        return json.loads(Path(__file__).with_name("fortune500.json").read_text())
    except (OSError, ValueError):
        return []


FORTUNE500 = _fortune500()
_known = {(kind, slug) for _, kind, slug in SUGGESTED_COMPANIES}
for _co in FORTUNE500:
    for _kind, _slug in _co.get("feeds", []):
        if (_kind, _slug) not in _known:
            SUGGESTED_COMPANIES.append((_co["name"], _kind, _slug))
            _known.add((_kind, _slug))
WATCHLIST_VERSION = 2  # raise when the default watch list grows, so saved searches pick up the new employers


def _default_companies():
    out = {"greenhouse": [], "lever": [], "ashby": [], "workday": [], "oracle": []}
    for _, kind, slug in SUGGESTED_COMPANIES:
        out.setdefault(kind, []).append(slug)
    return out


DEFAULT_SEARCH["companies"] = _default_companies()
DEFAULT_SEARCH["watchlist_version"] = WATCHLIST_VERSION

DEFAULT_AUTOMATION = {
    # Check employer job boards (Greenhouse, Lever, Ashby, Workday, Oracle) every few minutes
    # while JobBot runs, so new postings are caught as soon as they're published.
    "watch_enabled": True,
    "watch_minutes": 5,
    # List and alert new postings that score at least this (location and fit included).
    "alert_min_score": 50,
    # Also search the aggregator boards on a timer (they lag behind employer sites).
    "enabled": False,
    "interval_hours": 6,
    # Fill (but don't send) applications for matches at or above this score.
    "auto_prepare": True,
    "prepare_min_score": 60,
    # Actually press Submit without asking. Off by default on purpose.
    "auto_submit": False,
    "submit_min_score": 75,
    "auto_submit_ai_answers": False,
    "daily_limit": 15,
    "company_limit_30d": 3,
    # Show the browser window. Lets you finish CAPTCHAs or tricky questions yourself.
    "headless": True,
    "assist_timeout_min": 10,
}

DEFAULT_LLM = {
    "enabled": False,
    # Leave blank to use the ANTHROPIC_API_KEY environment variable.
    "api_key": "",
    "model": "claude-opus-5-5",
    # Let Claude answer required free-text questions the profile can't cover.
    "answer_questions": True,
    # Also draft optional "Why do you want to work here?" style answers.
    "answer_optional": False,
    # Write a tailored cover letter when a form asks for one.
    "cover_letters": True,
}

DEFAULTS = {
    "profile": DEFAULT_PROFILE,
    "answers": DEFAULT_ANSWERS,
    "search": DEFAULT_SEARCH,
    "automation": DEFAULT_AUTOMATION,
    "llm": DEFAULT_LLM,
}


def ensure_dirs():
    for d in (DATA_DIR, FILES_DIR, SHOTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
