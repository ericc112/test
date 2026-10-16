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
    },
    "consulting": {
        "label": "Consulting & Strategy",
        "title": r"consult\w*|strateg\w*|business analyst|business operations|bizops|chief of staff",
        "dept": r"strateg|consult|business operations|bizops|corporate development",
        "muse": ["Business Operations", "Management"],
        "jobicy": ["business"],
        "search": ["business analyst", "consultant"],
    },
    "operations": {
        "label": "Operations & Supply Chain",
        "title": r"operations|\bops\b|supply chain|procurement|purchasing|\bbuyer\b|sourcing|logistics|inventory|"
                 r"demand plan\w*|planning analyst|vendor|merchandis\w*|category manager",
        "dept": r"operations|supply chain|procurement|logistics|sourcing|merchandis",
        "muse": ["Business Operations"],
        "jobicy": ["management"],
        "search": ["operations analyst", "supply chain analyst"],
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
    },
    "hr": {
        "label": "HR & People",
        "title": r"human resources|\bhr\b|\bhris\b|people (operations|partner|ops|team|programs)|recruit\w*|talent|sourcer|"
                 r"compensation|benefits|total rewards|learning (and|&) development|\bl&d\b|workforce",
        "dept": r"\bpeople\b|\bhr\b|human resources|talent|recruit",
        "muse": ["Human Resources and Recruitment"],
        "jobicy": ["hr"],
        "search": ["human resources", "recruiter"],
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
    },
    "analytics": {
        "label": "Business Analytics",
        "title": r"business intelligence|\bbi analyst|data analyst|analytics|insights|pricing|market analyst|commercial analyst|"
                 r"reporting analyst|revenue analyst",
        "dept": r"analytics|business intelligence|insights",
        "muse": ["Data and Analytics"],
        "jobicy": ["data-science"],
        "search": ["business intelligence analyst", "data analyst"],
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
    r"data partner|annotat\w*|ads assessor|rater|ai trainer|data label\w*)\b",
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
        for v in FAMILIES[f][kind]:
            if v not in out:
                out.append(v)
    return out
