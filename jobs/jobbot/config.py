"""Paths and default settings.

Everything personal (profile, resume, database, screenshots) lives under DATA_DIR,
which is git-ignored. Override it with the JOBBOT_DATA environment variable.
"""
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
        "q": r"(ever|previously|formerly|currently) (been )?(employed|worked) (by|for|at)|former employee",
        "a": "No",
        "regex": True,
    },
    {"q": r"(were|are) you referred|referred by|employee referral", "a": "No", "regex": True},
]

DEFAULT_SEARCH = {
    # "business" keeps only roles that suit a business major (see fields.py); "" = any field.
    "field": "business",
    # Business areas to include (all by default).
    "families": ["finance", "consulting", "operations", "marketing", "sales", "hr", "management", "analytics"],
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
    },
    # Company job boards to watch. These are the ones JobBot can apply to directly.
    "companies": {"greenhouse": [], "lever": [], "ashby": []},
}

# Companies whose Greenhouse/Lever/Ashby boards list many business roles
# (checked October 2026). Offered as one-click additions in Search setup.
SUGGESTED_COMPANIES = [
    ("Stripe", "greenhouse", "stripe"), ("Toast", "greenhouse", "toast"), ("Datadog", "greenhouse", "datadog"),
    ("Databricks", "greenhouse", "databricks"), ("MongoDB", "greenhouse", "mongodb"), ("Cloudflare", "greenhouse", "cloudflare"),
    ("Brex", "greenhouse", "brex"), ("Flexport", "greenhouse", "flexport"), ("Okta", "greenhouse", "okta"),
    ("Samsara", "greenhouse", "samsara"), ("Ramp", "ashby", "ramp"), ("Coinbase", "greenhouse", "coinbase"),
    ("Airbnb", "greenhouse", "airbnb"), ("Klaviyo", "greenhouse", "klaviyo"), ("Notion", "ashby", "notion"),
    ("Plaid", "ashby", "plaid"), ("Palantir", "lever", "palantir"), ("Instacart", "greenhouse", "instacart"),
    ("Affirm", "greenhouse", "affirm"), ("Gusto", "greenhouse", "gusto"), ("Pinterest", "greenhouse", "pinterest"),
    ("Robinhood", "greenhouse", "robinhood"), ("Spotify", "lever", "spotify"), ("SoFi", "greenhouse", "sofi"),
]

DEFAULT_AUTOMATION = {
    # Run a search on a timer while the server is up.
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
