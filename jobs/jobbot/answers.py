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
from dataclasses import asdict, dataclass, field
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
        if len(nums) == 1 and ("+" in o or "more" in o.lower()) and have >= nums[0]:
            return o
        if len(nums) == 1 and re.search(r"less|under|<", o, re.I) and have < nums[0]:
            return o
    return None


def _relocate(q, c):
    p = c.profile
    for place in (p.get("city"), p.get("state")):
        if place and contains_phrase(q.label, place):
            return "Yes"
    return yn(p.get("willing_to_relocate"))


def _start(q, c):
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


def _how_heard(q, c):
    first = c.profile.get("how_heard") or "Job board"
    return [first, "Job board", "Online job board", "Job posting", "Website", "Company website",
            "Careers page", "Internet search", "Other"]


def _today(q, c):
    d = date.today()
    return d.isoformat() if q.input_type == "date" else d.strftime("%m/%d/%Y")


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


def _eeo(field_name):
    def f(q, c):
        v = c.profile.get(field_name) or "decline"
        if q.kind in ("text", "textarea") and v == "decline":
            return Answer(None, "skip")
        return Answer(v, "profile", alternatives=["decline"] if v != "decline" else [])
    return f


RULES = [
    # Voluntary self-identification (EEO)
    (r"sexual orientation|transgender|lgbt", ANY, lambda q, c: Answer("decline", "profile")),
    (r"\bgender\b|\bsex\b", ANY, _eeo("eeo_gender")),
    (r"hispanic|latin[oax]", ANY, _eeo("eeo_hispanic")),
    (r"\brace\b|ethnicit", ANY, _eeo("eeo_race")),
    (r"veteran", ANY, _eeo("eeo_veteran")),
    (r"disabilit", ANY, _eeo("eeo_disability")),
    # Messages and consent
    (r"text messages?|\bsms\b|whatsapp|newsletter|marketing|promotional|job alerts|talent (community|network|pool)|"
     r"(receive|get) (future )?(updates|communications|news|emails)", CHOICE, lambda q, c: yn(c.profile.get("marketing_opt_in"))),
    # Work authorisation and visas
    (r"(do|does) you (currently )?(have|hold|possess).{0,40}(work permit|visa|authori[sz]ation|right to work)",
     ANY, lambda q, c: yn(c.profile.get("work_authorized"))),
    (r"authori[sz]ed to work|eligible to work|right to work|work authori[sz]ation|legally (able|permitted|allowed|eligible)",
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
     r"consent to|by (checking|submitting|clicking)|certify that|attest|true and (complete|accurate)",
     CHOICE, _consent),
    # Education
    (r"\bdegree\b|level of education|highest education|education level|highest level", ANY, _p("degree")),
    (r"discipline|\bmajor\b|field of study|area of study|concentration", ANY, _p("discipline")),
    (r"graduat|year of completion|end date year", ANY, _p("graduation_year")),
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
    (r"street|address line|mailing address|^address$|home address", TEXT, _p("address")),
]
_COMPILED = [(re.compile(rx, re.I), kinds, fn) for rx, kinds, fn in RULES]

NAME_GUARD = re.compile(r"company|school|university|manager|refer|reference|emergency|recruiter|employer|business|project|team|pronunc", re.I)


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


def rule_answer(q, ctx):
    label = norm(q.label)
    for rx, kinds, fn in _COMPILED:
        if q.kind not in kinds or not rx.search(label):
            continue
        if fn is _full_name and NAME_GUARD.search(label):
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
        if re.search(r"resume|\bcv\b|curriculum", label) or (not label and q.required):
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
