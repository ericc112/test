"""Field-of-study filters. "business" keeps only roles that suit a business major.

A job is classified mainly by its title: job-board categories are too noisy on their
own (The Muse files baristas and welders under "Business Operations"). Department and
category labels only help with vague titles ("Associate", "Analyst") or veto
engineering-department roles.
"""
import re

from .textutil import norm

# Each business area: title pattern, board-specific category names, search terms
# for keyword-search boards, and department/category words that point to it.
FAMILIES = {
    "finance": {
        "label": "Finance & Accounting",
        "title": r"accountant|accounting|accounts (payable|receivable)|bookkeep\w*|financ\w*|fp&a|treasury|\btax\b|"
                 r"audit\w*|payroll|billing|credit|underwrit\w*|investment|banking|banker|equity research|private equity|"
                 r"venture capital|portfolio|wealth|valuation|corporate development|m&a|controller|\bcpa\b|risk|compliance|"
                 r"summer (analyst|associate)",
        "dept": r"financ|accounting|treasury|\btax\b|fp&a|audit|risk|compliance|investment|banking|capital markets",
        "muse": ["Accounting and Finance"],
        "jobicy": ["accounting-finance"],
        "search": ["financial analyst", "accountant"],
        "intern_search": ["finance intern", "accounting intern"],
    },
    "consulting": {
        "label": "Consulting & Strategy",
        "title": r"consult\w*|strateg\w*|business analyst|business operations|bizops|chief of staff",
        "dept": r"strateg|consult|business operations|bizops|corporate development",
        "muse": ["Business Operations", "Management"],
        "jobicy": ["business"],
        "search": ["business analyst", "consultant"],
        "intern_search": ["business analyst intern", "consulting intern"],
    },
    "operations": {
        "label": "Operations & Supply Chain",
        "title": r"operations|\bops\b|supply chain|procurement|purchasing|\bbuyer\b|sourcing|logistics|inventory|"
                 r"demand plan\w*|planning analyst|vendor|merchandis\w*|category manager",
        "dept": r"operations|supply chain|procurement|logistics|sourcing|merchandis",
        "muse": ["Business Operations"],
        "jobicy": ["management"],
        "search": ["operations analyst", "supply chain analyst"],
        "intern_search": ["operations intern", "supply chain intern"],
    },
    "marketing": {
        "label": "Marketing & Communications",
        "title": r"marketing|marketer|\bbrand\b|communications?|public relations|\bpr\b|social media|content (marketing|strategist|manager)|"
                 r"\bseo\b|\bsem\b|growth marketing|campaign|advertising|media (buyer|planner)|e-?commerce|market research|\bevents?\b|"
                 r"community manager|copywriter",
        "dept": r"marketing|brand|communications|\bcomms\b|\bpr\b|growth|content|advertising",
        "muse": ["Advertising and Marketing"],
        "jobicy": ["marketing"],
        "search": ["marketing"],
        "intern_search": ["marketing intern"],
    },
    "sales": {
        "label": "Sales & Business Development",
        "title": r"\bsales\b|account executive|account manager|account management|business development|\bbdr\b|\bsdr\b|"
                 r"partnerships?|partner manager|alliances|customer success|client success|relationship manager|revenue|"
                 r"\bchannel\b|key account|territory manager|revops",
        "dept": r"\bsales\b|business development|partnership|customer success|account management|revenue|go.to.market|\bgtm\b",
        "muse": ["Sales", "Account Management"],
        "jobicy": ["marketing", "business"],
        "search": ["account executive", "business development"],
        "intern_search": ["sales intern", "business development intern"],
    },
    "hr": {
        "label": "HR & People",
        "title": r"human resources|\bhr\b|\bhris\b|people (operations|partner|ops|team|programs)|recruit\w*|talent|sourcer|"
                 r"compensation|benefits|total rewards|learning (and|&) development|\bl&d\b|workforce",
        "dept": r"\bpeople\b|\bhr\b|human resources|talent|recruit",
        "muse": ["Human Resources and Recruitment"],
        "jobicy": ["hr"],
        "search": ["human resources", "recruiter"],
        "intern_search": ["human resources intern", "recruiting intern"],
    },
    "management": {
        "label": "Project & Product Management",
        "title": r"project manager|project coordinator|program manager|program coordinator|\bpmo\b|product manager|"
                 r"product owner|product operations|management (trainee|program|associate)|leadership (development|program)|"
                 r"rotational|general manager|business manager|office manager",
        "dept": r"\bproduct\b|program management|\bpmo\b",
        "muse": ["Project Management", "Product Management", "Management"],
        "jobicy": ["project-management", "management"],
        "search": ["project manager", "product manager"],
        "intern_search": ["project management intern", "product management intern"],
    },
    "analytics": {
        "label": "Business Analytics",
        "title": r"business intelligence|\bbi analyst|data analyst|analytics|insights|pricing|market analyst|commercial analyst|"
                 r"reporting analyst|revenue analyst",
        "dept": r"analytics|business intelligence|insights",
        "muse": ["Data and Analytics"],
        "jobicy": ["data-science"],
        "search": ["business intelligence analyst", "data analyst"],
        "intern_search": ["data analyst intern", "business intelligence intern"],
    },
}

# Never a business-major role, whatever else the title says.
HARD_BLOCK = re.compile(
    r"\b(engineer\w*|developer|software|programmer|devops|sre|data scientist|scientist|machine learning|researcher|"
    r"designer|ux|ui|technical program manager|nurse|rn|lpn|cna|physician|doctor|dentist|pharmacist|therapist|"
    r"veterinar\w*|caregiver|mechanic|electrician|plumber|welder|hvac|carpenter|driver|cdl|courier|warehouse|forklift|"
    r"picker|packer|laborer|cook|chef|barista|bartender|dishwasher|housekeep\w*|janitor|custodian|cashier|crew member|"
    r"teacher|tutor|professor|lifeguard|attorney|lawyer|paralegal|counsel|machinist|assembler|installer|pilot|"
    r"firefighter|police|appointment setter|telemarket\w*|door.to.door|commission.only|construction|"
    r"data partner|annotat\w*|ads assessor|rater|ai trainer|data label\w*|"
    r"stylist|beauty advisor|retail sales associate|sales floor|store associate|crew)\b",
    re.I,
)
# Not business on their own, but fine next to a clear business role
# ("Medical Sales Representative", "Retail Buyer", "IT Account Executive").
SOFT_BLOCK = re.compile(
    r"\b(technical|technician|it|security|cyber\w*|clinical|medical|dental|retail|store|server|operator|inspector|"
    r"surveyor|instructor|counselor|guard|solar|architect|design|research|lab|technology)\b",
    re.I,
)
VAGUE_ROLE = re.compile(
    r"\b(analyst|associate|coordinator|specialist|manager|lead|strategist|planner|representative|executive|"
    r"administrator|advisor|officer|partner|generalist|trainee|intern|internship)\b",
    re.I,
)
TECH_DEPT = re.compile(
    r"engineering|software|r&d|data science|machine learning|infrastructure|devops|security|information technology|"
    r"\bit\b|hardware|manufacturing|healthcare|clinical|nursing|education|teaching|quality assurance|\bqa\b|"
    r"artificial intelligence|design",
    re.I,
)
BUSINESS_DEGREE = re.compile(
    r"business administration|\bbba\b|\bmba\b|degree in (business|finance|accounting|marketing|economics|management)|"
    r"(business|finance|accounting|marketing|economics|management) (degree|major)|"
    r"bachelor'?s.{0,40}\b(business|finance|accounting|marketing|economics)\b",
    re.I,
)

# Specific functions first, so "Marketing Operations" is Marketing and "Sales Operations" is Sales.
PRIORITY = ["finance", "marketing", "sales", "hr", "analytics", "management", "operations", "consulting"]
GENERIC_BUSINESS = re.compile(r"\bbusiness\b", re.I)

_TITLE = {k: re.compile(r"(?<![a-z0-9])(?:" + FAMILIES[k]["title"] + r")", re.I) for k in PRIORITY}
_DEPT = {k: re.compile(f["dept"], re.I) for k, f in FAMILIES.items()}

FIELDS = {"business": {"label": "Business major", "families": list(FAMILIES)}}

# ---------------------------------------------------------------- job types
JOB_TYPES = {"internship": "Internships", "full_time": "Full-time jobs"}
DEFAULT_JOB_TYPES = ["internship"]

INTERN_TITLE = re.compile(
    r"\b(intern|interns|internship|internships|co-?op|externship|summer (analyst|associate|scholar|fellow\w*|program)|"
    r"off-?cycle|working student|werkstudent|praktikant\w*|praktikum|stagiaire)\b",
    re.I,
)
INTERN_LABEL = re.compile(r"\bintern(ship)?s?\b|co-?op|student program", re.I)  # board fields ("Intern (Fixed Term)")
PART_TIME = re.compile(r"part[- ]?time", re.I)
TEMPORARY = re.compile(r"\b(seasonal|temporary|temp|contract|contractor|freelance)\b", re.I)


def job_type(job):
    """internship | part_time | temporary | full_time, from the title and the board's own labels."""
    title = job.get("title") or ""
    tags = " | ".join(str(t) for t in job.get("tags") or [] if t)  # employment type, commitment, worker type
    cats = " | ".join(str(t) for t in job.get("categories") or [] if t)  # departments, or a board's keyword lists
    labels = tags + " | " + cats
    if INTERN_TITLE.search(title) or INTERN_LABEL.search(tags):
        return "internship"
    # A department called "Internships" counts, but not a keyword list ("Analyst-Intern") on a job typed Full Time.
    if INTERN_LABEL.search(cats) and not re.search(r"\bfull[- ]?time\b", tags, re.I):
        return "internship"
    if PART_TIME.search(title) or PART_TIME.search(labels):
        return "part_time"
    if TEMPORARY.search(title) or re.search(r"\b(seasonal|temporary|contract)\b", labels, re.I):
        return "temporary"
    return "full_time"


def wanted_types(search):
    return [t for t in (search.get("job_types") or DEFAULT_JOB_TYPES) if t in JOB_TYPES] or DEFAULT_JOB_TYPES


def type_ok(job, search):
    """Return (ok, reason). Part-time, seasonal and temporary roles never match."""
    kind = job_type(job)
    wanted = wanted_types(search)
    if kind in wanted:
        return True, None
    if wanted == ["internship"]:
        return False, "Not an internship"
    if wanted == ["full_time"]:
        return False, "Internship" if kind == "internship" else "Not full-time"
    return False, "Part-time or temporary"


GRAD_ONLY = re.compile(r"\b(mba|ph\.?d|doctoral|post-?doc|master'?s|graduate (interns?|internships?|students?)|jd|law student)\b", re.I)
GRAD_REQUIRED = re.compile(r"\b(pursuing|enrolled in)\s+(an?\s+)?(mba|master'?s|graduate degree|graduate program|ph\.?d)", re.I)
UNDERGRAD = re.compile(r"\b(undergrad\w*|bachelor'?s|college student)\b", re.I)


SKILLBRIDGE = re.compile(r"\bskill\s?bridge\b", re.I)


def level_mismatch(job, profile):
    """Internships meant for MBA/PhD students when you're an undergraduate (or the reverse),
    or for service members leaving the military (DoD SkillBridge) when you're a student."""
    if job_type(job) != "internship":
        return None
    if profile.get("currently_enrolled") and SKILLBRIDGE.search(job.get("title") or ""):
        return "For service members leaving the military (SkillBridge)"
    year = (profile.get("school_year") or "").lower()
    degree = (profile.get("degree") or "").lower()
    if not (year or degree):
        return None  # we don't know which you are
    grad = year == "graduate student" or bool(re.search(r"master|mba|ph\.?d|doctor", degree))
    title = job.get("title") or ""
    desc = job.get("description") or ""
    grad_only = (GRAD_ONLY.search(title) and not UNDERGRAD.search(title)) or \
        (GRAD_REQUIRED.search(desc) and not re.search(r"undergrad|bachelor", desc, re.I))
    if not grad and grad_only:
        return "For MBA or graduate students"
    if grad and UNDERGRAD.search(title) and not GRAD_ONLY.search(title):
        return "For undergraduates"
    return None


# ---------------------------------------------------------------- internship seasons
_SEASON = re.compile(
    r"\b(spring|summer|fall|autumn|winter)\b[\s,/-]*'?(20\d\d|\d\d)\b|\b(20\d\d)\b.{0,40}?\b(spring|summer|fall|autumn|winter)\b",
    re.I,
)
_SEASON_END = {"spring": (5, 31), "summer": (8, 31), "fall": (12, 31), "autumn": (12, 31), "winter": (3, 31)}


def season_of(title):
    """'Summer 2027 Finance Intern' → ('Summer', 2027)."""
    m = _SEASON.search(title or "")
    if not m:
        return None
    season = (m.group(1) or m.group(4)).lower()
    year = int(m.group(2) or m.group(3))
    year = year + 2000 if year < 100 else year
    return ("Fall" if season == "autumn" else season.capitalize()), year


def season_over(title, today):
    s = season_of(title)
    if not s:
        return False
    month, day = _SEASON_END[s[0].lower()]
    return (s[1], month, day) < (today.year, today.month, today.day)


def enabled_families(search):
    chosen = search.get("families") or list(FAMILIES)
    return [f for f in chosen if f in FAMILIES] or list(FAMILIES)


def _labels(job):
    vals = list(job.get("categories") or []) + list(job.get("tags") or [])
    return " | ".join(str(v) for v in vals if v)


def classify(job, search):
    """Return (True, area label) for a business-major role, else (False, reason)."""
    title = norm(job.get("title"))
    if not title:
        return False, "No title"
    if HARD_BLOCK.search(title):
        return False, "Not a business role"
    matched = [k for k, rx in _TITLE.items() if rx.search(title)]
    if not matched and GENERIC_BUSINESS.search(title):
        matched = ["consulting"]
    cats = _labels(job)
    if not matched:
        if SOFT_BLOCK.search(title) or not VAGUE_ROLE.search(title):
            return False, "Not a business role"
        if cats and TECH_DEPT.search(cats):
            return False, "Not a business role"
        matched = [k for k in PRIORITY if cats and _DEPT[k].search(cats)]
        if not matched:
            return False, "Not clearly a business role"
    elif cats and TECH_DEPT.search(cats) and set(matched) <= {"management", "analytics", "operations"} \
            and not any(_DEPT[k].search(cats) for k in FAMILIES):
        return False, "Engineering-side role"
    wanted = enabled_families(search)
    hit = next((k for k in matched if k in wanted), None)
    if not hit:
        return False, f"{FAMILIES[matched[0]]['label']} isn't one of your areas"
    return True, FAMILIES[hit]["label"]


def asks_for_business_degree(job):
    return bool(BUSINESS_DEGREE.search(job.get("description") or ""))


def source_terms(search, kind):
    """Board-specific filters for the enabled areas (muse categories, jobicy industries, search terms)."""
    out = []
    for f in enabled_families(search):
        for v in FAMILIES[f].get(kind, []):
            if v not in out:
                out.append(v)
    return out
