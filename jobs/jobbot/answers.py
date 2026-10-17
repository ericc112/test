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
from datetime import date, timedelta

from .textutil import contains_phrase, norm, pick_option, split_list, words

TEXT = {"text", "textarea", "combobox"}
CHOICE = {"select", "radio", "buttons", "checkboxes", "combobox", "checkbox"}
ANY = TEXT | CHOICE

# Employers who explicitly ask for a human. JobBot leaves these to you.
HUMAN_ONLY = re.compile(
    r"not an? (ro)?bot|auto-?apply|auto-?applying|automated (tool|application|submission|software)|"
    r"prove (that )?you(?:'re| are) (a )?human|written (by|without)|without (the )?(use of |using )?(ai|chatgpt|llm)|"
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
    rest = ["Job board", "Online job board", "Job posting", "Website", "Company website", "Careers page",
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
    season = "Spring" if month <= 5 else "Summer" if month <= 8 else "Fall"
    first = exp or year
    # Most specific first: a bare year would match "Fall 2028" as happily as "Spring 2028".
    alts = [f"{MONTHS[month - 1].capitalize()} {year}", f"{season} {year}", f"Class of {year}", f"{month:02d}/{year}", year]
    return Answer(first, "profile", alternatives=[a for a in alts if a and a != first])


def _school_year(q, c):
    y = (c.profile.get("school_year") or "").strip()
    if not y:
        return None
    alts = {"freshman": ["First year", "1st year"], "sophomore": ["Second year", "2nd year"],
            "junior": ["Third year", "3rd year"], "senior": ["Fourth year", "4th year"],
            "graduate student": ["Graduate", "Master's", "MBA"]}
    return Answer(y, "profile", alternatives=alts.get(y.lower(), []))


def _enrolled(q, c):
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
    if re.search(r"\bintern(ship)?\b|co-?op", (c.job or {}).get("title") or "", re.I):
        return ["Internship", "Intern", "Co-op", "Student"]
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
    plain = [o for o in q.options if re.match(r"bachelor'?s?\b(?! (of|in)\b)", norm(o))]
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


def _sponsorship(q, c):
    """No sponsorship needed is a plain "No": never "No – I hold a temporary visa status that provides work
    authorization", which some forms list first among several kinds of No."""
    if re.search(r"without (the )?(need (for|of) )?(any |employer |visa )*sponsor", q.label or "", re.I):
        # "Are you authorized to work ... without the need for sponsorship?" asks about authorization.
        return yn(bool(c.profile.get("work_authorized")) and not c.profile.get("needs_sponsorship"))
    if c.profile.get("needs_sponsorship"):
        return "Yes"
    nos = [o for o in q.options or [] if re.match(r"\s*no\b", o, re.I)]
    return next((o for o in nos if not TEMPORARY_STATUS.search(o)), "No")


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


def _blank(q, c):
    return Answer("", "blank")  # should be empty: clear anything already in it


def _eeo(field_name):
    def f(q, c):
        v = c.profile.get(field_name) or "decline"
        if q.kind in ("text", "textarea") and v == "decline":
            return Answer(None, "skip")
        return Answer(v, "profile", alternatives=["decline"] if v != "decline" else [])
    return f


RULES = [
    # Voluntary self-identification (EEO)
    (r"sexual orientation|transgender|lgbt|first[- ]generation", CHOICE, lambda q, c: Answer("decline", "profile")),
    (r"\bgender\b|\bsex\b", ANY, _eeo("eeo_gender")),
    (r"hispanic|latin[oax]", ANY, _eeo("eeo_hispanic")),
    (r"\brace\b|ethnicit", ANY, _eeo("eeo_race")),
    (r"veteran", ANY, _veteran),
    (r"disabilit", ANY, _disability),
    (r"check one of the boxes|select one of the (boxes|options) below", CHOICE, _check_one),
    # Messages and consent
    (r"text messages?|\bsms\b|whatsapp|newsletter|marketing|promotional|job alerts|talent (community|network|pool)|"
     r"(receive|get) (future )?(updates|communications|news|emails)", CHOICE, lambda q, c: yn(c.profile.get("marketing_opt_in"))),
    # Work authorisation and visas. Sponsorship first: "require sponsorship for work authorization" isn't
    # asking whether you're authorized.
    (r"sponsor|\bstem opt\b|optional practical training|curricular practical training|\bcpt\b", ANY, _sponsorship),
    (r"(do|does) you (currently )?(have|hold|possess).{0,40}(work permit|visa|authori[sz]ation|right to work)",
     ANY, lambda q, c: yn(c.profile.get("work_authorized"))),
    (r"authori[sz]ed (to work|for employment)|legally authori[sz]ed|eligible to work|right to work|work authori[sz]ation|"
     r"legally (able|permitted|allowed|eligible)",
     ANY, lambda q, c: yn(c.profile.get("work_authorized"))),
    (r"sponsor|\bvisa\b|h-?1b|work permit|immigration", ANY, lambda q, c: yn(c.profile.get("needs_sponsorship"))),
    # Where and how you'll work
    (r"relocat", CHOICE | {"text"}, _relocate),
    (r"work (remotely|from home|from a remote)|plan to work remote|intend to work remote|remote work",
     CHOICE, lambda q, c: yn(c.profile.get("remote_preference") in ("remote", "any"))),
    (r"in[- ]office|on[- ]?site|hybrid|commut|days (a|per) week|(come|coming) (in|into) (the|our) office",
     CHOICE, lambda q, c: yn(c.profile.get("remote_preference") in ("hybrid", "onsite", "any"))),
    (r"(previously|ever|already) applied", CHOICE, lambda q, c: "No"),
    # Pay and timing
    (r"salary|compensation|pay (range|expectation)|desired (pay|rate)|expected (pay|rate|annual)|rate expectation",
     ANY, _p("salary_expectation")),
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
    (r"have you graduated|already graduated", CHOICE, lambda q, c: yn(not c.profile.get("currently_enrolled"))),
    (r"return(ing)? to (school|university|college|campus)|continue (your|with) (studies|education|degree)",
     CHOICE, _enrolled),
    # Before "currently pursuing" and "degree": "Please select the degree type you are currently pursuing",
    # "Expected Graduation / Graduation Date? If you are continuing ... your current degree program".
    (r"\bgraduation\b.{0,25}\bdate\b|expected graduation|anticipated graduation", ANY, _graduation),
    (r"degree type|type of degree|which degree|what degree", ANY, _degree),
    (r"currently (enrolled|pursuing|attending|a student|studying)|are you (a |currently a |currently )?(current |full[- ]time )?"
     r"(student|enrolled)|enrolled (in|at) (a|an|your)|pursuing (a|an|your) .{0,30}degree", CHOICE | {"text"}, _enrolled),
    (r"(year|level|standing) (in|of) (school|study|college|university|program)|class standing|"
     r"current (academic )?(year|standing|level)|what year are you|academic (year|standing|level)|year of study|grade level|"
     r"student classification|classification as a student",
     ANY, _school_year),
    (r"which (term|season|session)|internship (term|season|period|session|dates|start)|what (term|season)|"
     r"(summer|fall|spring|winter) (internship|program)|available (for|during) (the )?(summer|fall|spring|winter)|start term",
     ANY, _terms),
    (r"\bminor\b", TEXT | {"select"}, _p("minor")),
    (r"^(type to )?add (your )?skills|^(your )?skills$", ANY, _skills),
    (r"(type|kind) of (role|position|job|employment) (are )?you|^(role|position|employment|job) type$", CHOICE, _role_type),
    # Education
    (r"\bdegree\b|level of education|highest education|education level|highest level", ANY, _degree),
    (r"discipline|\bmajor\b|field of study|area of study|concentration", ANY, _p("discipline")),
    (r"graduat|year of completion|class of|class year", ANY, _graduation),
    (r"\b(school|university|college|institution)\b", TEXT | {"select"}, _school),
    (r"language", ANY, _languages),
    # Documents
    (r"cover letter", TEXT | {"file"}, _cover_letter),
    (r"resume|\bcv\b|curriculum", {"textarea", "text"}, _skip),
    (r"additional information|anything else|comments|message to (the )?hiring", {"text", "textarea"}, _skip),
    # Signature blocks (e.g. the voluntary disability form)
    (r"^(today'?s )?date$|^signature date$|^date signed$", {"text"}, _today),
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
    (r"\bstate\b|province", TEXT | {"select"}, _p("state")),
    (r"\bzip\b|postal", TEXT, _p("postal_code")),
    (r"address line 2|^address 2$|\bline 2\b|apartment|\bapt\b|\bsuite\b", TEXT,
     lambda q, c: c.profile.get("address_line2") or _blank(q, c)),
    (r"street|address line|mailing address|^address$|home address", TEXT, _p("address")),
]
_COMPILED = [(re.compile(rx, re.I), kinds, fn) for rx, kinds, fn in RULES]

NAME_GUARD = re.compile(r"company|school|university|manager|refer|reference|emergency|recruiter|employer|business|project|team|pronunc", re.I)
# "Are you a first-generation college student?" mentions a college but isn't asking which one.
SCHOOL_GUARD = re.compile(r"^\W*(are|do|did|have|has|is|were|will|would|tell|describe|why|how)\b|first[- ]generation", re.I)


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
        return Answer(None, "human", note="The employer's AI-use policy: read it and agree yourself.")
    if key in ctx.planned and ctx.planned[key][0] not in (None, ""):
        a = Answer(ctx.planned[key][0], ctx.planned[key][1])
    else:
        banked = _bank_lookup(q.label or "", ctx.bank)
        a = Answer(banked, "bank") if banked is not None else rule_answer(q, ctx)
    if a is None:
        return Answer(None, "")
    if a.source == "skip":
        return a
    return resolve_options(q, a)


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
    })
    return d
