"""Decide what to put in each application question.

Order of precedence for every question:
  1. your answer for this specific job (typed in the review screen)
  2. your answer bank (patterns you saved once, reused everywhere)
  3. rules that read your profile (name, email, work authorisation, ...)
  4. Claude, if enabled, for required questions nothing else could answer
Anything still unanswered and required is reported as missing, never guessed.
"""
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field, replace
import calendar
from datetime import date, timedelta

from .textutil import contains_phrase, norm, pick_option, split_list, words

TEXT = {"text", "textarea", "combobox"}
CHOICE = {"select", "radio", "buttons", "checkboxes", "combobox", "checkbox"}
ANY = TEXT | CHOICE

# Employers who explicitly ask for a human. JobBot leaves these to you.
HUMAN_ONLY = re.compile(
    r"not an? (ro)?bot|auto-?apply|auto-?applying|automated (tool|application|submission|software)|"
    r"prove (that )?you(?:'re| are) (a )?human|written (by|without)|(writ\w*|answer\w*|respon\w*|complet\w*) .{0,30}without (the )?(use of |using )?(ai|chatgpt|llm)|"
    r"security code|verification code|figure out the|decode (this|the)|encoded in a|solve (this|the following) (puzzle|challenge)",
    re.I,
)


# Employer rules about AI use. You agree to these yourself, and JobBot doesn't use
# AI-written answers on forms that contain them.
AI_POLICY = re.compile(
    r"\bai\b.{0,25}(usage|use|policy|attestation|tools?)|(use|usage) of (generative )?(ai|artificial)|"
    r"artificial intelligence|generative|chatgpt|large language model|\bllms?\b",
    re.I,
)

ACKNOWLEDGE = ["Yes", "I acknowledge", "Acknowledge", "Acknowledged", "I agree", "Agree", "I accept", "Accept",
               "I have read", "I consent", "I confirm", "Confirm", "I understand", "I certify", "I attest"]


@dataclass
class Question:
    key: str
    kind: str  # text | textarea | select | radio | checkbox | checkboxes | buttons | combobox | file
    label: str
    required: bool = False
    options: list = field(default_factory=list)
    input_type: str = ""
    name: str = ""
    multi: bool = False
    value: object = None
    section: str = ""  # "education" | "employment" when the field sits in such a block


@dataclass
class Answer:
    value: object = None  # str | list[str] | None
    source: str = ""  # user | bank | profile | ai | file | skip | human
    note: str = ""
    alternatives: list = field(default_factory=list)
    option: object = None  # chosen option text (or list for checkboxes)
    search: str = ""  # what to type into an autocomplete box
    failed: bool = False  # the browser couldn't enter it
    site_value: bool = False  # the value is the site's own pre-fill, kept because you had no answer

    def resolved(self, q):
        if q.kind == "file":
            return bool(self.value)
        if q.kind in ("select", "radio", "buttons", "checkboxes", "checkbox"):
            return self.option not in (None, [], "")
        return self.value not in (None, "", [])


@dataclass
class Context:
    profile: dict
    bank: list = field(default_factory=list)
    job: dict = field(default_factory=dict)
    overrides: dict = field(default_factory=dict)  # norm(label) -> your answer for this job
    planned: dict = field(default_factory=dict)  # norm(label) -> (answer, source) from the reviewed fill
    files: dict = field(default_factory=dict)
    llm: object = None


def yn(flag):
    return "Yes" if flag else "No"


def render_template(text, ctx):
    p = ctx.profile
    name = " ".join(x for x in (p.get("first_name"), p.get("last_name")) if x)
    vals = defaultdict(str, {
        "company": ctx.job.get("company") or "your",
        "title": ctx.job.get("title") or "open",
        "name": name,
        "first_name": p.get("first_name", ""),
        "summary": p.get("summary", ""),
    })
    out = (text or "").format_map(vals)
    return re.sub(r"[ \t]+\n", "\n", re.sub(r" {2,}", " ", out)).strip()


# --------------------------------------------------------------------- rules
# Each rule: (regex on the normalised label, allowed kinds, function(q, ctx) -> value).
# A function may return an Answer for full control, a list for alternatives, or None.

def _p(field_name):
    return lambda q, c: c.profile.get(field_name) or None


def _full_name(q, c):
    n = " ".join(x for x in (c.profile.get("first_name"), c.profile.get("last_name")) if x)
    return n or None


def _location(q, c):
    p = c.profile
    city, state, country = p.get("city"), p.get("state"), p.get("country")
    value = ", ".join(x for x in (city, state) if x) or country
    if not value:
        return None
    # Location boxes are often autocompletes: type the city, pick the first suggestion.
    return Answer(value, "profile", alternatives=[city] if city else [], search=city or value)


def _years(q, c):
    yrs = str(c.profile.get("years_experience") or "").strip()
    if not yrs:
        return None
    generic = {
        "how", "many", "years", "year", "of", "do", "you", "have", "professional", "relevant",
        "work", "working", "industry", "total", "experience", "full", "time", "full-time",
        "overall", "in", "the", "software", "engineering", "development", "a", "minimum", "at",
        "least", "with", "does", "your", "what", "is", "number", "building", "developing",
        "writing", "code", "post", "graduate", "+", "or", "more", "experienced",
    }
    content = [w for w in words(q.label) if w not in generic and not w.isdigit() and not re.match(r"^\d+\+?$", w)]
    if content:
        return None  # experience with something specific: ask the human (or Claude)
    if q.kind in TEXT and q.kind != "combobox":
        return yrs
    nums = re.findall(r"\d+", q.label)
    try:
        have = float(re.findall(r"\d+(?:\.\d+)?", yrs)[0])
    except IndexError:
        return None
    if nums and re.search(r"minimum|at least|\+|or more|more than", q.label, re.I):
        return yn(have >= float(nums[0]))
    # Ranges like "3-5 years": pick the option containing our number.
    return Answer(yrs, "profile", alternatives=[_bucket(q.options, have)] if q.options else [])


def _bucket(options, have):
    for o in options:
        nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", o)]
        if len(nums) == 2 and nums[0] <= have <= nums[1]:
            return o
        if len(nums) == 1 and re.search(r"\+|more|above|higher|at least|>", o, re.I) and have >= nums[0]:
            return o
        if len(nums) == 1 and re.search(r"less|under|below|lower|<", o, re.I) and \
                (have <= nums[0] if re.search(r"or (below|less|lower)", o, re.I) else have < nums[0]):
            return o
    return None


def _relocate(q, c):
    p = c.profile
    for place in (p.get("city"), p.get("state")):
        if place and contains_phrase(q.label, place):
            return "Yes"
    return yn(p.get("willing_to_relocate"))


# "Do you have housing within 50 miles of the position's location?": depends on where the job is, so it never comes
# from the answer bank (a No saved for a job in another city would be wrong here).
DISTANCE = re.compile(r"within \d+ miles|\b(housing|live|reside|located|commut\w*)\b.{0,40}\b(near|distance|local)\b|"
                      r"local to (the|this) (position|job|role|location)", re.I)
METROS = [  # suburbs count as the city: someone in Katy lives within 50 miles of a Houston job
    {"houston", "katy", "sugar land", "cypress", "spring", "the woodlands", "pearland", "pasadena", "baytown", "conroe",
     "missouri city", "richmond", "tomball", "humble", "kingwood", "league city", "friendswood", "bellaire", "stafford", "fulshear"},
    {"dallas", "fort worth", "arlington", "plano", "irving", "frisco", "garland", "mckinney", "richardson", "grand prairie",
     "carrollton", "denton", "lewisville", "addison", "las colinas"},
    {"austin", "round rock", "cedar park", "georgetown", "pflugerville", "san marcos", "leander", "kyle"},
    {"san antonio", "new braunfels", "schertz", "boerne", "converse", "live oak"},
]


def _near(q, c):
    where, home = norm((c.job or {}).get("location") or ""), norm(c.profile.get("city") or "")
    if not where or not home:
        return None  # yours to answer: JobBot doesn't know where this job is
    metro = next((m for m in METROS if home in m), {home})
    if not (home in where or any(city in where for city in metro)):
        return "No"
    # "Yes, I am local to Houston (Katy), TX." among one Yes per site: the one naming this job's city or yours.
    places = [city for city in metro | {home} if city in where] + [home]
    for place in places:
        hit = next((o for o in q.options if norm(o).startswith("yes") and place in norm(o)), None)
        if hit:
            return Answer(hit, "profile")
    named = [o for o in q.options if norm(o).startswith("yes") and re.search(r"[A-Za-z)]\s*,\s*[A-Z]{2}\b", o)]
    return None if named else "Yes"  # Yes options for other places only: yours to answer


def _start(q, c):
    if re.search(r"\b(month|year)\b", norm(q.label)):
        return None  # "Start date month/year" is a past job's or degree's start, not when you can begin
    if q.input_type == "date":
        return (date.today() + timedelta(days=14)).isoformat()
    return c.profile.get("availability") or None


def _cover_letter(q, c):
    if q.kind == "file":
        return Answer(c.files.get("cover_letter"), "file") if c.files.get("cover_letter") else None
    text = render_template(c.profile.get("cover_letter"), c)
    return Answer(text, "profile") if text else None


def _languages(q, c):
    langs = split_list(c.profile.get("languages"))
    if not langs:
        return None
    if q.kind == "checkboxes":
        return Answer(langs, "profile")
    if q.kind in ("text", "textarea"):
        return ", ".join(langs)
    return langs[0]


EMPLOYER_SITES = ("greenhouse", "lever", "ashby", "workday")  # found on the company's own careers site


def _how_heard(q, c):
    first = c.profile.get("how_heard") or "Job board"
    # LinkedIn is named on purpose: it is the answer Eric wants wherever the form offers it, and
    # before this it was only reachable when it happened to be the form's first option.
    rest = ["LinkedIn", "Job board", "Online job board", "Job posting", "Website", "Company website", "Careers page",
            "Internet search", "Other"]
    if (c.job or {}).get("source") in EMPLOYER_SITES and first == "Job board":
        name = re.split(r",| (inc|llc|ltd|corp)\b", (c.job or {}).get("company") or "", flags=re.I)[0].strip()
        own = [f"{name} website", f"{name} careers", f"{name} careers page"] if name else []
        return own + ["Company website", "Company careers page", "Careers page", "Website"] + rest + _any_option(q)
    return [first] + rest + _any_option(q)


def _any_option(q):
    """Any answer will do for how you heard: when none of the usual ones is offered, the first choice there is."""
    return [o for o in q.options or [] if norm(o) not in ("", "select one")][:1]


MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]


def _gpa(q, c):
    gpa = str(c.profile.get("gpa") or "").strip()
    if not gpa:
        return None
    if q.options:
        try:
            have = float(re.findall(r"\d+(?:\.\d+)?", gpa)[0])
        except IndexError:
            return None
        threshold = re.search(r"(\d(?:\.\d+)?)\s*(or (greater|higher|above|better|more)|\+)", q.label or "", re.I)
        if threshold and any(norm(o) in ("yes", "no") for o in q.options):  # "Is your cumulative GPA a 3.0 or greater?"
            return yn(have >= float(threshold.group(1)))
        # Bands that list several scales: "1st class, Higher Distinction, 3.7+/4 GPA, 8+/10 GPA, …": the highest one you meet.
        bands = [(float(m.group(1)), o) for o in q.options for m in [re.search(r"(\d\.\d+)\s*\+?\s*/\s*4\b", o)] if m]
        if len(bands) >= 2:
            met = [b for b in bands if b[0] <= have]
            return Answer(max(met)[1], "profile") if met else None
        bucket = _bucket(q.options, have)  # "3.5 - 4.0", "3.75+", "Below 3.0"
        return Answer(gpa, "profile", alternatives=[bucket] if bucket else [])
    return gpa


def _graduation(q, c):
    """Expected graduation, as a date, a month, a year, "May 2028" or "Class of 2028"."""
    p = c.profile
    exp = (p.get("expected_graduation") or "").strip()
    year = str(p.get("graduation_year") or (re.findall(r"20\d\d", exp) or [""])[0])
    if not exp and not year:
        return None
    month = next((i + 1 for i, m in enumerate(MONTHS) if m[:3] in exp.lower()), 5)
    if q.input_type in ("date", "wd_date"):
        return f"{year}-{month:02d}-01"
    if q.input_type == "month":
        return f"{year}-{month:02d}"
    label = norm(q.label)
    if q.kind in ("text", "textarea") and "year" in label and "month" not in label:
        return year
    if re.search(r"\bmonth\b", label) and "year" not in label:  # "End date month"
        name = MONTHS[month - 1].capitalize()
        return Answer(name, "profile", alternatives=[name[:3], f"{month:02d}", str(month)])
    # Ranges: "January 2027 - June 2027", "July 2027 - December 2027": the one your graduation falls in.
    for o in q.options:
        m = re.match(r"\s*([a-z]+)\.?\s+(\d{4})\s*[-–—to]+\s*([a-z]+)\.?\s+(\d{4})\s*$", o, re.I)
        names = [n[:3] for n in MONTHS]
        if m and m.group(1)[:3].lower() in names and m.group(3)[:3].lower() in names:
            start = (int(m.group(2)), names.index(m.group(1)[:3].lower()) + 1)
            end = (int(m.group(4)), names.index(m.group(3)[:3].lower()) + 1)
            if year and start <= (int(year), month) <= end:
                return Answer(o, "profile")
    # Windows: "April-June 2027", "Before April 2026", "After December 2027".
    mon = lambda s: [n[:3] for n in MONTHS].index(s[:3]) + 1 if s[:3] in [n[:3] for n in MONTHS] else None
    for o in q.options if year else []:
        no, have = norm(o), (int(year), month)
        w = re.match(r"([a-z]+)\s*(?:-|to|through)\s*([a-z]+)\s+(\d{4})$", no)
        if w and mon(w.group(1)) and mon(w.group(2)) and (int(w.group(3)), mon(w.group(1))) <= have <= (int(w.group(3)), mon(w.group(2))):
            return Answer(o, "profile")
        b = re.match(r"(before|after|later than)\s+([a-z]+)\s+(\d{4})$", no)
        if b and mon(b.group(2)):
            edge = (int(b.group(3)), mon(b.group(2)))
            if (have < edge) if b.group(1) == "before" else (have > edge):
                return Answer(o, "profile")
    season = "Spring" if month <= 5 else "Summer" if month <= 8 else "Fall"
    first = exp or year
    # Most specific first: a bare year would match "Fall 2028" as happily as "Spring 2028".
    alts = [f"{MONTHS[month - 1].capitalize()} {year}", f"{season} {year}", f"Class of {year}", f"{month:02d}/{year}", year]
    return Answer(first, "profile", alternatives=[a for a in alts if a and a != first])


def _school_year(q, c):
    y = (c.profile.get("school_year") or "").strip() or _year_from_graduation(c)
    if not y:
        return None
    alts = {"freshman": ["First year", "1st year"], "sophomore": ["Second year", "2nd year"],
            "junior": ["Third year", "3rd year"], "senior": ["Fourth year", "4th year"],
            "graduate student": ["Graduate", "Master's", "MBA"]}
    return Answer(y, "profile", alternatives=alts.get(y.lower(), []))


def _year_from_graduation(c):
    """Year in school when your profile only says when you graduate: May 2027 in the 2026-27 school year is Senior."""
    exp = c.profile.get("expected_graduation") or ""
    year = re.findall(r"20\d\d", exp)
    if not year or not c.profile.get("currently_enrolled", True) or re.search(r"master|mba|ph\.?d", norm(c.profile.get("degree") or "")):
        return ""
    month = next((i + 1 for i, m in enumerate(MONTHS) if m[:3] in exp.lower()), 5)
    school_year = lambda y, m: y if m >= 8 else y - 1  # a school year starts in August
    today = date.today()
    left = school_year(int(year[0]), month) - school_year(today.year, today.month)
    return ["Senior", "Junior", "Sophomore", "Freshman"][left] if 0 <= left <= 3 else ""


ENROLLED_IN = re.compile(r"\b(enrolled|pursuing|studying)\b.{0,60}?\b(in|toward)\b(.{3,160}?)\b(degree program|program|major)\b")
PROGRAM_IN = re.compile(r"\b(degree|program|major)s? (in|of) (.{3,160})")
NOT_A_FIELD = {"undergraduate", "graduate", "graduated", "related", "degree", "degreed", "program", "discipline", "disciplines", "pending",
               "enrollment", "master", "masters", "bachelor", "bachelors", "currently", "accredited", "university", "college", "school",
               "full", "recent", "from", "four", "year", "time", "part", "similar", "field", "fields", "other", "such"}


def _enrolled(q, c):
    label = norm(q.label)
    # "enrolled in a Human Resources Development-related degree program", "a degree program in Data Science, Statistics…":
    # yes only if that's your field.
    named = " ".join(m.group(3) for m in (ENROLLED_IN.search(label), PROGRAM_IN.search(label)) if m)
    field_words = [w for w in words(named) if len(w) > 3 and w not in NOT_A_FIELD]
    mine = norm(" ".join(str(c.profile.get(k) or "") for k in ("discipline", "minor", "degree", "degree_type")))
    if field_words and not any(w in mine for w in field_words):
        return "No" if mine.strip() else None
    return yn(c.profile.get("currently_enrolled"))


def _terms(q, c):
    terms = split_list(c.profile.get("internship_terms"))
    if not terms:
        return None
    if q.options and all(norm(o) in ("yes", "no") for o in q.options):
        asked = re.search(r"(spring|summer|fall|autumn|winter)\D{0,3}(20\d\d)?", q.label or "", re.I)
        if not asked:
            return None
        hit = any(asked.group(1).lower() in norm(t) and (not asked.group(2) or asked.group(2) in t) for t in terms)
        return yn(hit)
    if q.kind == "checkboxes":
        return Answer(terms, "profile")
    if q.kind in ("text", "textarea"):
        return ", ".join(terms)
    return Answer(terms[0], "profile", alternatives=terms[1:] + [t.split()[0] for t in terms])


def _today(q, c):
    d = date.today()
    return d.isoformat() if q.input_type in ("date", "wd_date") else d.strftime("%m/%d/%Y")


def _school(q, c):
    school = c.profile.get("school")
    if not school:
        return None
    # Long school pickers usually end with "Other (school not listed)".
    return [school, "Other"] if q.kind in ("select", "combobox") else school


BUSINESS_MAJOR = re.compile(r"supply chain|logistic|operation|financ|accounting|marketing|management|economic|business|"
                            r"entrepreneur|human resources|analytics|information systems|real estate|insurance", re.I)


def _discipline(q, c):
    major = (c.profile.get("discipline") or "").strip()
    if not major:
        return None
    if q.kind not in ("select", "combobox", "radio", "checkboxes"):
        return major
    # Short major lists ("Business", "Business Administration"...) often lack the exact major.
    # A business major then falls back to the broad business option, never to an unrelated one.
    return [major] + (["Business Administration", "Business", "Business Management"] if BUSINESS_MAJOR.search(major) else [])


def _relevant_experience(q, c):
    """"Have you completed an internship or work experience in a field relevant to the role?": yes when your profile
    has a job, done somewhere else ("Yes - with another company", not "Yes - within Baker Hughes")."""
    if not (c.profile.get("current_title") or c.profile.get("current_company")):
        return None
    yes = [o for o in q.options if norm(o).startswith("yes")]
    other = next((o for o in yes if re.search(r"\b(another|other) (company|employer|organi[sz]ation)|\boutside\b|\bexternal", o, re.I)
                  and not re.search(r"\bboth\b", o, re.I)), None)
    return Answer(other, "profile", option=other) if other else ("Yes" if not yes or len(yes) == 1 else None)


def _consent(q, c):
    if not q.required:
        return Answer(None, "skip")  # optional acknowledgements are your call
    if not c.profile.get("accept_privacy_terms"):
        return None
    return ACKNOWLEDGE


def _skip(q, c):
    return Answer(None, "skip")


COMMON_SKILLS = ["Microsoft Excel", "Excel", "PowerPoint", "Microsoft Word", "Microsoft Office", "Data Analysis",
                 "Supply Chain Management", "Supply Chain", "Inventory Management", "Inventory", "Logistics", "Procurement",
                 "Purchasing", "Forecasting", "Demand Planning", "SAP", "ERP", "SQL", "Python", "Tableau", "Power BI",
                 "Project Management", "Operations", "Marketing", "Sales", "Customer Service", "Negotiation",
                 "Communication", "Leadership", "Teamwork", "Problem Solving", "Time Management"]


def _has(skill, text):
    return bool(re.search(rf"\b{re.escape(norm(skill))}\b", text))


def _skills(q, c):
    """Skills from your profile, else every common one your resume names: the ones the posting asks for first.
    Only skills your resume shows, never ones it doesn't."""
    if c.profile.get("skills"):
        return split_list(c.profile["skills"])
    resume, posting = norm(c.profile.get("resume_text") or ""), norm((c.job or {}).get("description") or "")
    found = [s for s in COMMON_SKILLS if _has(s, resume)]
    found.sort(key=lambda s: not _has(s, posting))
    return found or None


def _role_type(q, c):
    """"Which type of role are you applying for?": an internship when the posting is one."""
    title = (c.job or {}).get("title") or ""
    if re.search(r"\bintern(ship)?\b|co-?op", title, re.I):
        season = re.search(r"summer|fall|spring|winter", f"{title} {c.profile.get('internship_terms') or ''}", re.I)
        return ([f"{season.group(0).capitalize()} Internship"] if season else []) + ["Internship", "Intern", "Co-op", "Student"]
    return ["Full Time", "Full-time", "Regular"]


DEGREE_NAMES = {
    "bba": ["Bachelor of Business Administration", "BBA", "B.B.A."],
    "bs": ["Bachelor of Science", "BS", "B.S."],
    "ba": ["Bachelor of Arts", "BA", "B.A."],
}


def _degree(q, c):
    """Your degree: its exact name ("Bachelor of Business Administration", "BBA"), else a plain bachelor's option
    ("Bachelors", "Bachelor's Degree"), never another named degree ("Bachelor of Applied Linguistics", "BA")."""
    level = c.profile.get("degree") or None
    names = DEGREE_NAMES.get(norm(c.profile.get("degree_type") or "").replace(".", ""), [])
    if not q.options or not names:
        return (names + [level] if level else names) or None
    named = [o for n in names for o in q.options if re.search(rf"(^|\W){re.escape(norm(n))}($|\W)", norm(o))]
    plain = [o for o in q.options if re.search(r"(^|\W)bachelor'?s?\b(?! (of|in)\b)", norm(o))]  # "University/Bachelors Degree"
    if named or plain:
        return Answer((named or plain)[0], "profile")
    return Answer(None, "", note="None of the options is your degree")


def _veteran(q, c):
    """Not a veteran never lands on "I am a veteran, but I am not a protected veteran", which merely contains
    the words "I am not a protected veteran"."""
    v = c.profile.get("eeo_veteran") or "decline"
    if q.kind in ("text", "textarea") and v == "decline":
        return Answer(None, "skip")
    if re.search(r"\bnot\b", v, re.I) and q.options:
        says_veteran = re.compile(r"\bi am a veteran\b|\bidentify as\b|\bam a protected\b", re.I)
        never = [o for o in q.options if re.search(r"not a veteran|never served", o, re.I) and not says_veteran.search(o)]
        not_protected = [o for o in q.options if re.search(r"not a protected veteran", o, re.I) and not says_veteran.search(o)]
        return Answer((never + not_protected or ["decline"])[0], "profile")
    return _eeo("eeo_veteran")(q, c)


TEMPORARY_STATUS = re.compile(r"temporary|i (hold|have) an? .{0,30}visa|on an? .{0,20}visa|\bopt\b|\bcpt\b|\bstem\b|h-?1b|\bead\b|\bf-?1\b", re.I)
HOLDS_TEMPORARY = re.compile(r"\bi (hold|have|am on) (an? )?(temporary|[\w-]+ visa)|temporary (visa|status|work)", re.I)
CITIZEN = re.compile(r"citizen|national\b|permanent resident|green card|u\.?s\.? worker|lawful permanent", re.I)


def _sponsorship(q, c):
    """No sponsorship needed is a plain "No": never "No – I hold a temporary visa status that provides work
    authorization", which some forms list first among several kinds of No. A U.S. citizen gets the citizen's No;
    when no No fits, the question is left for you."""
    if re.search(r"without (the )?(need (for|of) )?(any |employer |visa )*sponsor", q.label or "", re.I):
        # "Are you authorized to work ... without the need for sponsorship?" asks about authorization.
        return yn(bool(c.profile.get("work_authorized")) and not c.profile.get("needs_sponsorship"))
    if c.profile.get("needs_sponsorship"):
        return "Yes"
    if _us_person(c):  # "N/A – I am a US citizen, US national, legal permanent resident…"
        mine = [o for o in q.options or [] if CITIZEN.search(o) and not HOLDS_TEMPORARY.search(o) and not re.match(r"\s*yes\b", o, re.I)]
        if mine:
            return Answer(mine[0], "profile")
    nos = [o for o in q.options or [] if re.match(r"\s*no\b", o, re.I)]
    if not nos:  # "I do NOT need sponsorship to work in the US"
        nos = [o for o in q.options or [] if re.search(r"\b(do not|don't|will not|won't) (need|require)|\bnot need\b|without sponsorship", o, re.I)]
    if len(nos) <= 1:
        return nos[0] if nos and not HOLDS_TEMPORARY.search(nos[0]) else ("No" if not nos else None)
    citizen = re.search(r"citizen", c.profile.get("citizenship") or "", re.I)
    fits = [o for o in nos if citizen and CITIZEN.search(o) and not HOLDS_TEMPORARY.search(o)] + \
           [o for o in nos if not TEMPORARY_STATUS.search(o)]
    return Answer(fits[0], "profile") if fits else Answer(None, "", note="Which kind of No fits you?")


def _disability(q, c):
    """The voluntary disability form: "No, I don't have a disability" is its "No, I do not have a disability and
    have not had one in the past"."""
    v = c.profile.get("eeo_disability") or "decline"
    if q.kind in ("text", "textarea") and v == "decline":
        return Answer(None, "skip")
    lead = re.match(r"\s*(yes|no)\b", v, re.I)
    if lead and q.options:
        same = [o for o in q.options if re.match(rf"\s*{lead.group(1)}\b", o, re.I)]
        if len(same) == 1:
            return Answer(same[0], "profile")
    return _eeo("eeo_disability")(q, c)


def _check_one(q, c):
    """"Please check one of the boxes below": the form says what it's about only in its options."""
    opts = " ".join(q.options or [])
    if re.search(r"disabilit", opts, re.I):
        return _disability(q, c)
    if re.search(r"veteran", opts, re.I):
        return _veteran(q, c)
    return None


US_STATES = {"alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
             "connecticut": "CT", "delaware": "DE", "district of columbia": "DC", "florida": "FL", "georgia": "GA", "hawaii": "HI",
             "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
             "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
             "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
             "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
             "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC", "south dakota": "SD",
             "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
             "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY"}


def _state(q, c):
    """Your state, also as its code: Taleo lists "US-TX", others "TX"."""
    state = (c.profile.get("state") or "").strip()
    if not state:
        return None
    code = US_STATES.get(norm(state)) or (state.upper() if len(state) == 2 else "")
    return [state] + ([code, f"US-{code}", f"{code} - {state}"] if code else [])


def _us_person(c):
    cit = norm(c.profile.get("citizenship") or "")
    return bool(re.search(r"\bu\.? ?s\.?(?![a-z])|united states|american|permanent resident|green card", cit))


def _export_control(q, c):
    """Export-control questions (U.S. persons): "Are you one of the following: Citizen or National of the United
    States, U.S. Lawful Permanent Resident…" (Yes for you); "Are you a citizen of any of the following countries?
    Cuba, Iran…" (No); "Select all countries in which you hold citizenship" when the U.S. isn't listed ("Not Applicable")."""
    if not _us_person(c):
        return None  # yours to answer
    label = norm(q.label)
    if re.search(r"select all countries|countries in which you (currently )?hold", label):
        us = next((o for o in q.options if re.search(r"united states|^usa?$", norm(o))), None)
        na = next((o for o in q.options if norm(o) in ("not applicable", "n a", "none")), None)
        return us or na
    if re.search(r"citizen of any of the following countries|cuba|iran|north korea|syria", label):
        return "No"
    return "Yes"


def _authorized(q, c):
    """Authorized to work: "Yes", or the sentence some forms use instead ("I am authorized to work in this country
    for any employer")."""
    if c.profile.get("work_authorized"):
        return ["Yes", "I am authorized to work in this country for any employer",
                "authorized to work in the united states for any employer", "authorized to work for any employer"]
    return ["No", "I require sponsorship to work in this country"]


def _blank(q, c):
    return Answer("", "blank")  # should be empty: clear anything already in it


def _eeo(field_name):
    def f(q, c):
        v = c.profile.get(field_name) or "decline"
        if q.kind in ("text", "textarea") and v == "decline":
            return Answer(None, "skip")
        return Answer(v, "profile", alternatives=["decline"] if v != "decline" else [])
    return f


# Text messages, newsletters and other marketing: your Marketing opt-in.
MARKETING = re.compile(r"text messages?|\bsms\b|whatsapp|newsletter|marketing|promotional|job alerts|talent (community|network|pool)|"
                       r"(receive|get) (future )?(updates|communications|news|emails)")


# --------------------------------------------------------------------- common screening questions
# Places: "Houston, TX", "US-TX-HOUSTON-2001 RANKIN ROAD", "Massachusetts", and the states they're in.

def _codes(text, with_codes=True):
    """The U.S. states a place names, as codes: "Houston, TX" → {"TX"}, "Massachusetts" → {"MA"}."""
    found = {code for name, code in US_STATES.items() if f" {name} " in f" {norm(text)} "}
    if with_codes:  # "Houston, TX", "US-TX-HOUSTON": capital codes only, so "in" or "or" never reads as a state
        found |= set(re.findall(r"(?:^|[\s,(-])([A-Z]{2})(?=$|[\s,)-])", text or "")) & set(US_STATES.values())
    return found


def _at(option, text, metro=()):
    """An option ("Seattle, WA", "Massachusetts") is where text says: its city, or the state when it names no city."""
    city = norm(option.split(",")[0]) if "," in option else ""
    if city:
        return len(city) >= 3 and (f" {city} " in f" {norm(text)} " or city in metro)
    codes = _codes(option)
    return bool(codes and codes & _codes(text))


ANYWHERE = re.compile(r"no (strong )?preference|do not have a preference|don'?t have a preference|open to (all|any)|any (location|cohort|team|of)|"
                      r"anywhere|i can join any|no specific|flexible")
AREA_GROUPS = [{"sourcing", "procurement", "purchasing", "supply", "chain", "logistics", "operations", "planning", "inventory", "gps"},
               {"finance", "financial", "accounting", "audit", "tax", "treasury", "fp&a", "corporate"},
               {"marketing", "communications", "brand", "advertising", "media", "content"},
               {"sales", "commercial", "business development", "account", "customer"},
               {"hr", "human", "resources", "people", "talent", "learning", "development"},
               {"analytics", "data", "intelligence", "insights", "digital", "technology"}]
_GENERIC = {"intern", "interns", "internship", "internships", "summer", "spring", "fall", "winter", "program", "programs", "co-op",
            "coop", "opportunities", "opportunity", "student", "students", "undergraduate", "graduate", "analyst", "associate",
            "role", "team", "the", "and", "for", "with", "of", "&", "-", "2026", "2027", "2028", "year", "round"}


def _area_words(text):
    ws = {w for w in words(text) if len(w) > 2 and w not in _GENERIC}
    return ws | {w for g in AREA_GROUPS if ws & g for w in g}


def _preference(q, c):
    """Choices among places, teams or programs: "What is your 1st location preference?", "Select ALL areas in which you
    would accept an offer", "Please select your main area of interest", "Which internship cohort do you prefer?".
    Places: this job's, then near you, then "no preference". Areas: the ones that fit this job and your major."""
    if not q.options:
        return None
    label, opts = norm(q.label), [o for o in q.options if norm(o) not in ("", "select one")]
    anywhere = [o for o in opts if ANYWHERE.search(norm(o))]
    many = q.kind == "checkboxes"
    nth = re.search(r"\b(2nd|second|secondary)\b|\b(location|choice|preference|option)\s*#?\s*2\b", label) and 2 or \
        re.search(r"\b(3rd|third)\b|\b(location|choice|preference|option)\s*#?\s*3\b", label) and 3 or \
        re.search(r"\b(4th|fourth)\b|\b(location|choice|preference|option)\s*#?\s*4\b", label) and 4 or 1
    if nth > 1 and anywhere and not re.search(r"area|interest", label):
        return Answer(anywhere[0], "profile")
    styles = [o for o in opts if re.search(r"\b(on-?site|remote|hybrid|in[- ]office|virtual)\b", norm(o))]
    if len(styles) >= 2 and len(styles) >= len(opts) - 1:
        want = c.profile.get("remote_preference") or "any"
        fit = styles if want == "any" else [o for o in styles if re.search({"onsite": r"on-?site|in[- ]office", "remote": r"remote|virtual",
                                                                            "hybrid": r"hybrid"}.get(want, "$^"), norm(o))]
        return Answer(fit if many else fit[0], "profile") if fit else None
    places = [o for o in opts if o not in anywhere and (_codes(o) or re.search(r"[A-Za-z], [A-Z]{2}\b", o))]
    if len(places) >= max(2, len(opts) // 2):
        j, p = c.job or {}, c.profile
        job = f"{j.get('location') or ''} {j.get('title') or ''}"
        home = f"{p.get('city') or ''}, {p.get('state') or ''}"
        metro = next((m for m in METROS if norm(p.get("city") or "") in m), set())
        here = [o for o in places if _at(o, job)]
        near = [o for o in places if o not in here and (_at(o, home, metro) or _codes(o, False) & _codes(home))]
        if many:
            pick = here + near + anywhere[:1]
            return Answer(pick, "profile") if pick else None
        ranked = here + near + anywhere  # your 2nd choice is the next place, never the 1st again
        return Answer(ranked[nth - 1], "profile") if len(ranked) >= nth else None
    # Areas, teams, brands, programs.
    want = _area_words(f"{(c.job or {}).get('title') or ''} {c.profile.get('discipline') or ''}")
    scored = sorted(((len(_area_words(o) & want), i, o) for i, o in enumerate(opts) if o not in anywhere), key=lambda t: (-t[0], t[1]))
    good = [o for n, _, o in scored if n]
    if many:
        good = [o for n, _, o in scored if n and n == scored[0][0]]
    if not good:
        return Answer(anywhere[0], "profile") if anywhere else None
    if nth > 1:
        return Answer(good[nth - 1], "profile") if len(good) >= nth else None
    return Answer(good if many else good[0], "profile")


def _resident(q, c):
    """"Are you a California resident?", "Do you reside in one of the following states?": from your state."""
    mine = _codes(c.profile.get("state") or "")
    if not mine:
        return None
    if q.options and any(_codes(o) for o in q.options):
        hit = next((o for o in q.options if mine & _codes(o)), None)
        return hit or next((o for o in q.options if re.match(r"none|no\b|not applicable", norm(o))), None)
    asked = _codes(q.label, False)
    return yn(bool(mine & asked)) if asked else None


EMPLOYER_AI = re.compile(r"\b(we|company|employer|recruit\w*|talent acquisition|hiring team)\b.{0,40}\b(may|will|uses?|using)\b|"
                         r"\b\w+ (may|will) use (ai|artificial|machine|automated)|use of (ai|artificial|machine learning|automated)|"
                         r"\b(ai|automated)\b.{0,30}\b(assess|analy[sz]e|evaluate|review|screen|match|process|assist)|hiredscore|"
                         r"consent to the (use|processing)", re.I)
OWN_AI = re.compile(r"\b(did|have) you (use|used)\b|you used|your (own )?use of|how you use|written (by|without)|generated|"
                    r"(writ\w*|answer\w*|respon\w*|complet\w*|prepar\w*) .{0,30}without (the )?(use|help|assistance)|i did not use|\battest", re.I)


def _ai_screening(q):
    """The employer's own AI screening ("We may use AI tools to assess your application", HiredScore): you agree to
    it. Never a statement about your own use of AI, which stays yours."""
    if not q.options or not EMPLOYER_AI.search(q.label or "") or OWN_AI.search(q.label or ""):
        return None
    pick = pick_option("Yes", q.options)
    return Answer(pick, "profile", option=pick, note="You agree to employers' AI screening") if pick else None


def _available(q, c):
    """"What days/times are you available?", flexible shifts, working through the school year: available."""
    anytime = next((o for o in q.options if re.search(r"\bany ?time\b|\ball (days|times|shifts)\b|fully (available|flexible)", norm(o))), None)
    return Answer(anytime, "profile") if anytime else "Yes"


def _travel_help(q, c):
    """"Would you require travel assistance to interview in our McLean, VA office?": yes when it's in another state."""
    home = _codes(c.profile.get("state") or "")
    there = _codes(q.label) or _codes((c.job or {}).get("location") or "")
    return yn(not (home & there)) if home and there else None


def _english(q, c):
    for level in (r"native", r"fluent|bilingual|full professional", r"advanced|expert"):
        best = next((o for o in q.options if re.search(level, norm(o))), None)
        if best:
            return Answer(best, "profile")
    return "Yes"


def _other_languages(q, c):
    """"Are you proficient in any other languages below?": the ones in your profile, else "None of the above"."""
    langs = [l for l in split_list(c.profile.get("languages") or "English") if norm(l) != "english"]
    if not q.options:
        return ", ".join(langs) or None
    hits = [o for o in q.options if any(norm(l) in norm(o) for l in langs)]
    none = next((o for o in q.options if re.match(r"none|n/?a\b|not applicable|no\b", norm(o))), None)
    if q.kind == "checkboxes":
        return Answer(hits or ([none] if none else []), "profile") if hits or none else None
    if all(norm(o) in ("yes", "no", "select one") for o in q.options):
        return yn(bool(langs))
    return Answer((hits or [none])[0], "profile") if hits or none else None


def _tools(q, c):
    """"Which of the following programs have you used?": the ones among your skills, else "None of the above"."""
    skills = norm(" ".join(_skills(q, c) or []))
    hits = [o for o in q.options if norm(o) not in ("", "select one") and
            (_has(o, skills) or any(_has(s, norm(o)) for s in split_list(c.profile.get("skills")) if len(norm(s)) > 2))]
    if not hits:
        none = next((o for o in q.options if re.match(r"none|n/?a\b|not applicable", norm(o))), None)
        return Answer([none] if q.kind == "checkboxes" else none, "profile") if none else None
    return Answer(hits if q.kind == "checkboxes" else hits[0], "profile")


_MON = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
PROGRAM_DATES = re.compile(rf"\b{_MON}(?:\s+(\d{{1,2}}))?(?:,?\s+(20\d\d))?\s*(?:-|–|—|to|through|until)\s*{_MON}(?:\s+(\d{{1,2}}))?,?\s+(20\d\d)", re.I)


def _last_day(q, c):
    """"What is your last available work date?": the end of the program the posting gives ("January – July 2027",
    "May 17, 2027 to August 6, 2027"): you're available for all of it."""
    m = PROGRAM_DATES.search((c.job or {}).get("description") or "")
    if not m:
        return None
    month = [n[:3] for n in MONTHS].index(m.group(4)[:3].lower()) + 1
    year = int(m.group(6))
    day = int(m.group(5)) if m.group(5) else calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-{day:02d}" if q.input_type in ("date", "wd_date") or q.kind not in TEXT else f"{month:02d}/{day:02d}/{year}"


def _military(q, c):
    return "No" if re.search(r"\bnot\b", c.profile.get("eeo_veteran") or "", re.I) else None


# Ties to this employer: "Have you worked here before?", "Does anyone in your family work here?" and their "If yes,
# give the details" follow-ups. Answered from your profile's company lists (No unless this employer is on one),
# ahead of the answer bank, whose generic "No" can't know about the companies you listed.
THIS_EMPLOYER = re.compile(r"\b(here|us|our|this (company|organi[sz]ation|employer|firm|bank|business)|the company)\b")
TIE_WORK = re.compile(r"\b(work(s|ed|ing)?|employ(ed|ee|ees|ment)?|intern(ed|ship)?|co-?op|team members?|associates?|staff|contractor)\b")
TIE_WHEN = re.compile(r"\b(before|previous(ly)?|in the past|ever|former(ly)?|prior|past|current(ly)?|returning|again|at any time)\b")
TIE_NOT_YOU = re.compile(r"\b(know|anyone|someone|referr\w*|eligib\w*|rehire)\b")  # a referral, or a question for ex-employees
TIE_RELATIVES = re.compile(r"\b(relatives?|family|related to|spouse|domestic partner|parents?|siblings?|child(ren)?|in-?laws?|"
                           r"household|personal relationship|relationship with)\b")
# Questions about another organization: a government, a competitor, an auditor. ("Supplier for General Motors" is a way
# of having worked for GM, so suppliers and vendors aren't on this list.)
TIE_OTHER = re.compile(r"government|federal|public official|competitor|client|auditor|regulator|staffing agency|recruit(er|ing) (agency|firm)")
FOLLOW_UP = re.compile(r"^(if (yes|so|applicable)\b|if you('ve| (answered|selected|said|checked|chose|indicated|have|had|are|were|did|do|"
                       r"previously|ever))\b)|"
                       r"\bif (yes|so|applicable)\W*$")
TIE_DETAILS = re.compile(r"\b(relationship|relatives?|family|employee'?s name|name of (the |your )?(employee|relative|person)|"
                         r"employee (id|number)|dates? of employment|employment dates|position held|"
                         r"(previous|former) (position|title|role|manager|supervisor))\b")
_CO_SUFFIX = re.compile(r"\b(the|inc|incorporated|llc|ltd|plc|corp|corporation|co|company|companies|group|holdings)\b")


def _co(name):
    return " ".join(words(_CO_SUFFIX.sub(" ", norm(name))))


def _listed(names, company, label):
    """This employer, or one the question names, is on a comma-separated list of companies."""
    here, text = _co(company), f" {' '.join(words(label))} "
    for n in filter(None, (_co(x) for x in split_list(names))):
        if here and (n == here or n.startswith(here + " ") or here.startswith(n + " ")) or f" {n} " in text:
            return True
    return False


def _tie(label, company):
    """Which tie a question asks about: "family", "worked" or None."""
    if TIE_OTHER.search(label) or not TIE_WORK.search(label):
        return None
    ours = THIS_EMPLOYER.search(label) or (_co(company) and f" {_co(company)} " in f" {' '.join(words(label))} ")
    if TIE_RELATIVES.search(label):
        return "family" if ours or re.search(r"\b(an?|any|current|former) (employees?|team members?|associates?|staff)\b", label) else None
    if TIE_WHEN.search(label) and not TIE_NOT_YOU.search(label) and \
            (ours or re.search(r"\bformer\b|\breturning (intern|employee|associate|co-?op)|\bprevious employee", label)):
        return "worked"
    return None


def _employer_ties(q, c):
    if q.section:  # "I currently work here" in a work-experience block is about that job
        return None
    label, company, p = norm(q.label), c.job.get("company") or "", c.profile
    worked = lambda: _listed(", ".join(x for x in (p.get("current_company"), p.get("previous_employers")) if x), company, label)
    family = lambda: _listed(p.get("family_employers"), company, label)
    if FOLLOW_UP.search(label):
        tie = _tie(label, company) or ("family" if TIE_RELATIVES.search(label) else None)
        if not tie and not TIE_DETAILS.search(label):
            return None
        if tie == "family" and family() or tie == "worked" and worked() or not tie and (family() or worked()):
            return Answer(None, "")  # the details are yours to give (not the answer bank's generic "No")
        if q.kind in CHOICE:
            return Answer("N/A", "profile", alternatives=["Not applicable", "None"]) if q.required else Answer(None, "skip")
        return Answer("N/A", "profile") if q.required else Answer("", "blank")
    kin = TIE_RELATIVES.search(label)
    if kin and kin.start() < 150 and TIE_OTHER.search(label) and TIE_WORK.search(label) and not FOLLOW_UP.search(label):
        # A relative in government, at a client or a competitor: none that your profile knows of.
        unsure = next((o for o in q.options if re.search(r"not to my knowledge|not that i('m| am) aware", norm(o))), None)
        return Answer(unsure or "No", "profile")
    tie = _tie(label, company)
    if tie == "family":
        if family():
            return Answer("Yes", "profile")
        unsure = next((o for o in q.options if re.search(r"not to my knowledge|not that i('m| am) aware", norm(o))), None)
        return Answer(unsure or "No", "profile")
    if tie == "worked":
        if re.search(r"\bcurrent(ly)?\b", label) and not re.search(r"\b(former(ly)?|before|previous(ly)?|ever|past|prior)\b", label):
            return Answer(yn(_listed(p.get("current_company"), company, label)), "profile")
        return Answer(yn(worked()), "profile")
    return None


RULES = [
    # Voluntary self-identification (EEO)
    (r"sexual orientation|transgender|lgbt|first[- ]generation", CHOICE, lambda q, c: Answer("decline", "profile")),
    (r"\bgender\b|\bsex\b", ANY, _eeo("eeo_gender")),
    (r"hispanic|latin[oax]", ANY, _eeo("eeo_hispanic")),
    (r"\brace\b|ethnicit", ANY, _eeo("eeo_race")),
    (r"veteran", ANY, _veteran),
    (r"military (training|certification|experience|service)|served in the (military|armed forces)|armed forces", CHOICE, _military),
    (r"disabilit", ANY, _disability),
    (r"check one of the boxes|select one of the (boxes|options) below", CHOICE, _check_one),
    # Messages and consent. Being contacted about other jobs is part of looking for one; marketing isn't.
    (r"^(?!.*\b(text messages?|sms|whatsapp)\b).*(contact you (about|regarding|for|with) .{0,40}(jobs?|careers?|employment|opportunit)|"
     r"future (job |career |employment )?opportunit|"
     r"consider(ed)? (you |me )?for (other|future|additional|similar) (open )?(positions|roles|opportunities|openings|jobs)|career tips)",
     CHOICE, lambda q, c: "Yes"),
    (r"(contact|text|reach) you (about|regarding|on) (your|this) (application|candidacy)|"
     r"text messages? (about|regarding) (your|this|the) (application|role|position)", CHOICE, lambda q, c: "Yes"),
    (MARKETING.pattern, CHOICE, lambda q, c: yn(c.profile.get("marketing_opt_in"))),
    # Export control, before sponsorship: these quote the "Immigration and Nationality Act".
    (r"citizen or national of the united states|\bu\.? ?s\.? lawful permanent resident|\bu\.? ?s\.? person\b|"
     r"citizen of any of the following countries|countries in which you (currently )?hold citizenship", ANY, _export_control),
    # Work authorisation and visas. Sponsorship first: "require sponsorship for work authorization" isn't
    # asking whether you're authorized.
    # Before sponsorship: "Do you currently have legal authorization to work … (e.g. US Citizen, Employer Sponsored…)"
    (r"(do|does) you (currently )?(have|possess) (the )?(legal )?(authori[sz]ation|right) to work", ANY, _authorized),
    (r"sponsor|\bstem opt\b|optional practical training|curricular practical training|\bcpt\b", ANY, _sponsorship),
    (r"(do|does) you (currently )?(have|hold|possess).{0,40}(work permit|visa|authori[sz]ation|right to work)",
     ANY, _authorized),
    (r"authori[sz]ed (to work|for employment)|legally authori[sz]ed|eligible to work|right to work|work authori[sz]ation|"
     r"legally (able|permitted|allowed|eligible)",
     ANY, _authorized),
    (r"sponsor|\bvisa\b|h-?1b|work permit|immigration", ANY, lambda q, c: yn(c.profile.get("needs_sponsorship"))),
    # Where and how you'll work. "What type of work are you looking for? Most positions require you to be on-site…" first.
    (r"(type|kind) of (role|position|job|employment|work|internship|opportunity) (are )?you|^(role|position|employment|job) type$",
     CHOICE, _role_type),
    (r"(programs?|software|tools?|applications?|systems?|technolog\w*)\b.{0,60}\b(experience|proficien\w*|familiar|used|using|skilled|comfortable)|"
     r"(experience|proficien\w*|familiar\w*) (with|using|in) (the following|any of the following|these)", {"checkboxes", "select", "radio"}, _tools),
    (r"relocat", CHOICE | {"text"}, _relocate),
    (DISTANCE.pattern, CHOICE, _near),
    (r"\b(are you|currently|anticipate) .{0,30}\b(resident|residing)\b|\bresident of\b|\b(live|reside) in (one of )?(the following|any of)",
     ANY, _resident),
    (r"(days|times|hours|shifts?|schedule)\b.{0,40}\bavailab|availab\w* .{0,30}\b(days|times|weekends?|nights?|shifts|evenings?)\b|"
     r"flexible (shifts?|hours|schedule)|work (weekends|nights|evenings|overtime|flexible)|work continuously|"
     r"(throughout|during) the (school|academic) year|part[- ]time .{0,40}(classes|school|semester)", CHOICE, _available),
    (r"travel (assistance|reimbursement|accommodation)|(require|need) (any )?(assistance|help) .{0,20}travel", CHOICE, _travel_help),
    (r"interested in (a |our |the )?rotation", CHOICE, lambda q, c: "Yes"),
    (r"(locations?|offices?|sites?|cit(y|ies)|areas?|regions?|markets?|cohorts?|teams?|brands?|business (groups?|units?)|"
     r"functions?|rotations?|tracks?)\b.{0,60}\b(prefer\w*|interest\w*|consider\w*|willing|accept)\b|"
     r"\b(prefer\w*|interest\w*)\b.{0,30}\b(locations?|offices?|cohorts?|areas?|teams?|brands?|programs?|rotations?)\b|"
     r"(1st|2nd|3rd|first|second|third|main|primary|secondary) (location|choice|area)|which rotation|\bpreferences?\b",
     CHOICE | {"text"}, _preference),
    # Internships and co-ops you've done: "Yes, I have internship/co-op experience OUTSIDE of J&J".
    (r"(previously|currently) work(ed|ing)? .{0,40}\b(intern|co-?op)\b|(internship|co-?op) (or co-?op |or internship )?experience",
     CHOICE, _relevant_experience),
    (r"work (remotely|from home|from a remote)|plan to work remote|intend to work remote|remote work",
     CHOICE, lambda q, c: yn(c.profile.get("remote_preference") in ("remote", "any"))),
    (r"in[- ]office|in the office|on[- ]?site|hybrid|commut|days (a|per) week|(come|coming) (in|into) (the|our) office",
     CHOICE, lambda q, c: yn(c.profile.get("remote_preference") in ("hybrid", "onsite", "any"))),
    (r"(previously|ever|already) (applied|interviewed)|interviewed (with|at) .{0,30}before|(participated|been) in .{0,30}recruit(ment|ing) "
     r"process|attended .{0,40}(recruiting|career|info(rmation)?) (events?|sessions?|fairs?)", CHOICE, lambda q, c: "No"),
    # Pay and timing
    (r"salary|compensation|pay (range|expectation)|(desired|minimum|expected) (pay|rate|annual)|rate expectation",
     ANY, lambda q, c: c.profile.get("salary_expectation") or _bank_lookup("salary expectation", c.bank)),
    (r"last (available|possible) (work(ing)? )?(day|date)|(end|finish|last) date .{0,30}availab|available (to work )?(until|through)|"
     r"latest (end|finish|departure) date", ANY, _last_day),
    (r"start date|when (can|could|would) you (start|begin)|earliest (start|available)|notice period|"
     r"availability|available to start", ANY, _start),
    (r"how many years|years of .*experience|years.{0,20}experience", ANY, _years),
    (r"how did you (hear|find|learn|come across)|where did you (hear|find|learn|see)|"
     r"how .{0,20}(hear|heard|learn|learned|find|found) (about|of)|^source$|referral source", ANY, _how_heard),
    # Agreements
    (r"privacy|i (have read|agree|acknowledge|consent|certify|confirm|understand|accept)|acknowledg|"
     r"terms (and|&) conditions|terms of (use|service)|data (processing|protection|retention)|gdpr|"
     r"consent to|by (checking|submitting|clicking)|certify that|attest|true and (complete|accurate)|must agree|agree to proceed",
     CHOICE, _consent),
    # Students and internships
    (r"\bgpa\b|grade point", ANY, _gpa),
    # "Please select your highest level of education, including any degree you are currently pursuing": your degree,
    # not whether you're enrolled; "In which of the following subjects is your most relevant degree?": your major.
    (r"^(?!.*graduat).*(highest (level of )?(education|degree)|level of education)", ANY, _degree),  # not "when will you graduate…"
    (r"\b(subjects?|fields?|areas?|disciplines?)\b.{0,40}\bdegree\b|\bdegree\b.{0,30}\b(subject|field of study|discipline)", ANY,
     _discipline),
    (r"(completed|have|had) (an |any )?(internship|work experience).{0,60}\b(relevant|field)|relevant (internship|work experience)",
     CHOICE, _relevant_experience),
    (r"have you graduated|already graduated", CHOICE, lambda q, c: yn(not c.profile.get("currently_enrolled"))),
    (r"return(ing)? to (school|university|college|campus)|continue (your|with) (studies|education|degree)",
     CHOICE, _enrolled),
    # Before "currently pursuing" and "degree": "Please select the degree type you are currently pursuing",
    # "Expected Graduation / Graduation Date? If you are continuing ... your current degree program".
    (r"\bgraduation\b.{0,25}\bdate\b|expected graduation|anticipated graduation", ANY, _graduation),
    (r"degree type|type of degree|which degree|what degree|level of degree", ANY, _degree),
    (r"are you (currently )?an? (undergraduate|graduate|college|university|degree)\b.{0,40}\bstudent|"
     r"currently (enrolled|pursuing|attending|a student|studying)|are you (a |currently a |currently )?(current |full[- ]time )?"
     r"(student|enrolled)|enrolled (in|at) (a|an|your)|pursuing (a|an|your) .{0,30}degree", CHOICE | {"text"}, _enrolled),
    (r"(year|level|standing) (in|of) (school|study|college|university|program)|class standing|"
     r"current (academic )?(year|standing|level)|what year are you|academic (year|standing|level)|year of study|grade level|"
     r"student classification|classification as a student|class (status|level)",
     ANY, _school_year),
    (r"which (term|season|session)|internship (term|season|period|session|dates|start)|what (term|season)|"
     r"(summer|fall|spring|winter) (internship|program)|available (for|during) (the )?(summer|fall|spring|winter)|start term",
     ANY, _terms),
    (r"\bminor\b", TEXT | {"select"}, _p("minor")),
    (r"^(type to )?add (your )?skills|^(your )?skills$", ANY, _skills),

    # Education
    # "Select the month and year you are expecting to graduate with your bachelor's degree": a date, not a degree.
    (r"(month|year|date|when)\b.{0,40}graduat|expect\w* to graduate|graduat\w* (month|year|date)", ANY, _graduation),
    (r"\bdegree\b|level of education|highest education|education level|highest level", ANY, _degree),
    (r"discipline|\bmajor\b|field of study|area of study|concentration", ANY, _discipline),
    (r"graduat|year of completion|class of|class year", ANY, _graduation),
    (r"\b(school|university|college|institution)\b", TEXT | {"select"}, _school),
    (r"(proficien\w*|fluen\w*|level|command) (of|in) (the )?english|english (language )?(proficien|fluen|level|skills)|speak english",
     CHOICE, _english),
    (r"(other|additional|any|foreign|second) languages?|languages? (other than|besides) english", ANY, _other_languages),
    (r"language", ANY, _languages),
    # Documents
    (r"cover letter", TEXT | {"file"}, _cover_letter),
    (r"resume|\bcv\b|curriculum", {"textarea", "text"}, _skip),
    (r"additional information|anything else|comments|message to (the )?hiring", {"text", "textarea"}, _skip),
    # Signature blocks (e.g. the voluntary disability form)
    (r"^(today'?s )?date$|signature date$|^date signed$|^date of signature$", {"text"}, _today),  # "Candidate eSignature Date"
    (r"signature|^sign here", {"text"}, _full_name),
    # Who you are
    (r"pronunciation", TEXT, _skip),
    (r"preferred (first )?name|what would you like (us )?to call you|nick ?name",
     TEXT, lambda q, c: c.profile.get("preferred_name") or c.profile.get("first_name") or None),
    (r"\bfirst name\b|\bgiven name\b|^first$|^fname$", TEXT, _p("first_name")),
    (r"\blast name\b|\bsurname\b|\bfamily name\b|^last$|^lname$", TEXT, _p("last_name")),
    (r"^(your |full |legal |candidate )?(full |legal )?name$|\bfull name\b|\blegal name\b|^your name\b",
     TEXT, _full_name),
    (r"pronoun", ANY, _p("pronouns")),
    (r"e-?mail", TEXT, _p("email")),
    (r"phone (device )?type|type of phone", CHOICE, lambda q, c: ["Mobile", "Cell", "Cell Phone", "Mobile Phone", "Personal Cell"]),
    (r"\bextension\b|^ext\.?$", TEXT, _blank),  # "Phone Extension": your number doesn't have one
    (r"phone|mobile|\bcell\b|telephone", TEXT, _p("phone")),
    (r"linkedin", TEXT, _p("linkedin")),
    (r"github", TEXT, _p("github")),
    (r"twitter|\bx\.com\b", TEXT, _p("twitter")),
    (r"portfolio|personal (web)?site|^website|\bwebsite\b|\bblog\b|other (url|link|website)|^url$", TEXT, _p("website")),
    (r"(current|recent|previous|present|latest|last)\b.{0,25}\b(company|employer|organi[sz]ation)|"
     r"^(company|employer|organi[sz]ation|current company)$", TEXT, _p("current_company")),
    (r"(current|recent|previous|present|latest|last)\b.{0,25}\b(job title|title|role|position)|^(job )?title$",
     TEXT, _p("current_title")),
    # Where you are
    (r"\bcountr(y|ies)\b", ANY, _p("country")),
    (r"\bcity\b|where .{0,30}(live|located|based|reside)|where .{0,40}work(ing)? from|current location|"
     r"^location\b|\breside\b",
     ANY, _location),
    (r"\bstate\b|province", TEXT | {"select"}, _state),
    (r"\bzip\b|postal", TEXT, _p("postal_code")),
    (r"address line 2|^address 2$|\bline 2\b|apartment|\bapt\b|\bsuite\b", TEXT,
     lambda q, c: c.profile.get("address_line2") or _blank(q, c)),
    (r"street|address line|mailing address|^address$|home address", TEXT, _p("address")),
]
_COMPILED = [(re.compile(rx, re.I), kinds, fn) for rx, kinds, fn in RULES]
PASS_ON = {_preference, _resident, _tools, _relevant_experience}

NAME_GUARD = re.compile(r"company|school|university|manager|refer|reference|emergency|recruiter|employer|business|project|team|pronunc", re.I)
# "Are you a first-generation college student?" mentions a college but isn't asking which one.
SCHOOL_GUARD = re.compile(r"^\W*(are|do|did|have|has|is|were|will|would|tell|describe|why|how)\b|first[- ]generation|countr", re.I)


def _bank_lookup(label, bank):
    for entry in bank or []:
        pat, ans = entry.get("q"), entry.get("a")
        if not pat or ans is None:
            continue
        if entry.get("regex"):
            try:
                if re.search(pat, label, re.I):
                    return ans
            except re.error:
                continue
        elif norm(pat) and norm(pat) in norm(label):
            return ans
    return None


def _by_input_type(q, c):
    t = (q.input_type or "").lower()
    if t == "email":
        return c.profile.get("email") or None
    if t == "tel":
        return c.profile.get("phone") or None
    return None


def _coerce(result, source="profile"):
    if result is None:
        return None
    if isinstance(result, Answer):
        return result
    if isinstance(result, list):
        return Answer(result[0], source, alternatives=result[1:])
    return Answer(result, source)


HISTORY_DATE = re.compile(r"\b(start|end|from|to)\b.{0,12}\b(date|month|year)\b|^(month|year)$|current(ly)? (role|job|position|work)")


def _section_answer(q, ctx, label):
    """Fields in a repeated education/employment block. None = not handled here."""
    if q.section == "education" and re.match(r"(from|start)\b", label):  # Workday: "From"
        start = (ctx.profile.get("education_start") or "").strip()
        return _coerce(_graduation(q, replace(ctx, profile={**ctx.profile, "expected_graduation": start, "graduation_year": ""}))) \
            if start else Answer(None, "profile")
    if q.section == "education" and re.match(r"(to|end)\b|.*actual or expected", label):  # "To (Actual or Expected)"
        return _coerce(_graduation(q, ctx)) or Answer(None, "profile")
    if q.section == "employment":  # your current job, when your profile has it
        p = ctx.profile
        start = (p.get("current_job_start") or "").strip()
        if re.search(r"currently work here|current(ly)? (employed|work) (here|there)", label):
            return Answer(True if start else None, "profile")
        if re.match(r"(from|start)\b", label):
            return _coerce(_graduation(q, replace(ctx, profile={**p, "expected_graduation": start, "graduation_year": ""}))) \
                if start else Answer(None, "profile")
        if re.search(r"description|responsibilit|duties", label):
            return Answer(p.get("current_job_description") or None, "profile")
        if re.match(r"location\b", label):
            return Answer(p.get("current_job_location") or None, "profile")
    if HISTORY_DATE.search(label):
        # The end of your degree is your graduation. A past job's dates, or when a degree
        # started, only you know: leave them for you rather than guess.
        if q.section == "education" and re.search(r"\b(end|to|completion)\b", label):
            return _coerce(_graduation(q, ctx)) or Answer(None, "profile")
        return Answer(None, "profile")
    if q.section == "employment" and re.search(r"\b(company|employer)\b", label):
        return Answer(ctx.profile.get("current_company") or None, "profile")
    if q.section == "employment" and re.search(r"\b(title|position|role)\b", label):
        return Answer(ctx.profile.get("current_title") or None, "profile")
    return None


def rule_answer(q, ctx):
    label = norm(q.label)
    if q.section:
        a = _section_answer(q, ctx, label)
        if a is not None:
            return a if a.value not in (None, "", []) else None
    for rx, kinds, fn in _COMPILED:
        if q.kind not in kinds or not rx.search(label):
            continue
        if fn is _full_name and NAME_GUARD.search(label):
            continue
        if fn is _school and SCHOOL_GUARD.search(label):
            continue
        a = _coerce(fn(q, ctx))
        if a is not None:
            if not a.source:
                a.source = "profile"
            return a
        if fn in PASS_ON:
            continue  # a broad rule that didn't recognise the options: the next one may ("a preference for remote work?")
        return None  # the right rule matched but the profile has no value
    return _coerce(_by_input_type(q, ctx))


def resolve_options(q, a):
    """For choice questions, map the answer onto the question's actual options."""
    if a is None or a.value is None:
        return a
    if q.kind == "checkbox":
        v = norm(str(a.value))
        a.option = True if v in ("yes", "true", "1", "y", "checked") else (False if v in ("no", "false", "0", "n") else None)
        if a.option is False and q.required:
            a.option = None
        return a
    if q.kind == "checkboxes":
        vals = a.value if isinstance(a.value, list) else split_list(a.value)
        picked = []
        for v in vals:
            o = pick_option(v, q.options)
            if o and o not in picked:
                picked.append(o)
        for alt in a.alternatives if not picked else []:  # "Business Administration" for a major the list lacks
            o = pick_option(alt, q.options)
            if o:
                picked = [o]
                break
        a.option = picked or None
        return a
    if q.kind in ("select", "radio", "buttons") or (q.kind == "combobox" and q.options):
        for cand in [a.value, *a.alternatives]:
            o = pick_option(cand, q.options)
            if o:
                a.option = o
                return a
        a.option = None
        a.note = a.note or f"“{a.value}” isn't one of the options"
    return a


def answer(q, ctx):
    """Answer one question without AI."""
    if q.kind == "file":
        label = norm(q.label)
        if "autofill" in label:
            return Answer(None, "skip")
        # Workday's resume box is just "Upload a file (5MB max)": a bare upload field is for your resume.
        if re.search(r"resume|\bcv\b|curriculum", label) or re.match(r"(upload|attach|select|drop)( a| your)? files?\b", label) \
                or (not label and q.required):
            path = ctx.files.get("resume")
            return Answer(path, "file") if path else Answer(None, "", note="Upload your resume in Profile")
        if "cover letter" in label:
            return _coerce(_cover_letter(q, ctx)) or Answer(None, "skip")
        return Answer(None, "skip")
    key = norm(q.label)
    if key in ctx.overrides and ctx.overrides[key] not in (None, ""):
        return resolve_options(q, Answer(ctx.overrides[key], "user"))
    if HUMAN_ONLY.search(q.label or ""):
        return Answer(None, "human", note="The employer asks you to answer this yourself.")
    if AI_POLICY.search(q.label or ""):
        banked = _bank_lookup(q.label or "", ctx.bank)
        if banked is not None:
            return resolve_options(q, Answer(banked, "bank"))
        return _ai_screening(q) or Answer(None, "human", note="The employer's AI-use policy: read it and agree yourself.")
    if q.kind in CHOICE and ACK_STATEMENT.match(key) and not MARKETING.search(key):  # "By selecting I accept, I certify…": an agreement, whatever words it quotes
        ack = _coerce(_consent(q, ctx))
        if ack is not None:
            return ack if ack.source == "skip" else resolve_options(q, ack)
    tie = _employer_ties(q, ctx)
    if tie is not None:
        return tie if tie.source in ("skip", "blank") else resolve_options(q, tie)
    if key in ctx.planned and ctx.planned[key][0] not in (None, ""):
        a = Answer(ctx.planned[key][0], ctx.planned[key][1])
    else:
        banked = None if DISTANCE.search(q.label or "") else _bank_lookup(q.label or "", ctx.bank)
        a = Answer(banked, "bank") if banked is not None else rule_answer(q, ctx)
    if a is None:
        return Answer(None, "")
    if a.source == "skip":
        return a
    return resolve_options(q, a)


ACK_STATEMENT = re.compile(r"^\W*(\d+\.\s*)?(by (selecting|checking|clicking|submitting|signing)|"
                           r"i (hereby )?(attest|acknowledge|certify|confirm|understand|agree|have read|accept|declare|affirm))\b")
OPEN_QUESTION = re.compile(r"\?\s*$|^(why|what|how|tell us|describe|share|explain|please (describe|explain|share|tell))\b", re.I)


def needs_ai(q, a, optional=False):
    if a.source in ("human", "skip", "user", "bank") or q.kind == "file" or a.resolved(q):
        return False
    if q.required:
        return True
    return optional and q.kind in ("textarea", "text") and bool(OPEN_QUESTION.search(q.label or ""))


def answer_all(questions, ctx):
    """Answer every question; ask Claude (once, in a batch) for required leftovers."""
    answers = {q.key: answer(q, ctx) for q in questions}
    if ctx.llm is not None:
        optional = getattr(ctx.llm, "answer_optional", False)
        todo = [q for q in questions if needs_ai(q, answers[q.key], optional)]
        cover = [q for q in questions if q.kind in ("textarea", "text") and "cover letter" in norm(q.label)]
        if todo:
            for key, (value, note) in ctx.llm.answer_questions(todo, ctx).items():
                q = next(x for x in questions if x.key == key)
                a = resolve_options(q, Answer(value, "ai", note=note))
                if a.resolved(q):
                    answers[key] = a
        if cover and getattr(ctx.llm, "write_cover_letters", False):
            letter = ctx.llm.cover_letter(ctx)
            if letter:
                for q in cover:
                    if answers[q.key].source not in ("user", "bank"):
                        answers[q.key] = Answer(letter, "ai", note="Tailored cover letter")
    return answers


def missing(questions, answers):
    return [q for q in questions
            if q.required and (not answers[q.key].resolved(q) or answers[q.key].failed)]


def as_dict(q, a):
    d = asdict(q)
    d.update({
        "answer": a.option if a.option not in (None, []) else a.value,
        "source": a.source,
        "note": a.note,
        "resolved": a.resolved(q) and not a.failed,
        "site_value": a.site_value,
    })
    return d
