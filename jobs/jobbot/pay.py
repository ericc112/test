"""Pay in US dollars per hour, from a job's salary fields or the pay range in its description.

Internship pay is usually written into the description ("$29 - $33 per hour", "$45,000 -
$60,000 annually"), often next to dollar figures that aren't pay ("$6 billion in
community benefits", "a $1,000 housing stipend"). Yearly, monthly and weekly pay is
converted at 40 hours a week (2,080 hours a year) and marked as an estimate.
"""
import re

PER_HOUR = {"hour": 1.0, "week": 1 / 40, "month": 12 / 2080, "year": 1 / 2080}

_NUM = r"(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?\s?([kK])?"
MONEY = re.compile(r"(?:US)?\$\s?" + _NUM + r"(?:\s*(?:-|–|—|to)\s*(?:US)?\$?\s?" + _NUM + r")?")
UNIT_AFTER = re.compile(
    r"^\s*(?:USD|US dollars|dollars)?\s*(?:\(?\s*(?:gross|base|pre-tax)\s*\)?)?\s*"
    r"(?P<u>/\s*(?:hr|hour|h)\b|per\s+hour|an\s+hour|hourly|/\s*(?:wk|week)\b|per\s+week|weekly|"
    r"/\s*(?:mo|month)\b|per\s+month|a\s+month|monthly|each\s+month|/\s*(?:yr|year)\b|per\s+(?:year|annum)|a\s+year|annually|annual)",
    re.I)
UNIT_BEFORE = re.compile(r"(hourly|per hour|wage|annual(?:ized)?|yearly|salary|monthly|weekly)[^$]{0,40}$", re.I)
SCALE_AFTER = re.compile(r"^\s*(?:[mb]n?\b|billion|million|thousand|trillion)", re.I)
NOT_PAY = re.compile(
    r"stipend|bonus|referr|reimburs|allowance|relocation|housing|equity|fund(?:ing|ed|s)\b|raised|revenue|\barr\b|"
    r"assets|\baum\b|valuation|investor|benefits? (?:to|for) (?:the )?communit|community benefit|for using|tuition|"
    r"scholarship|award|\bfee\b|\bcost|price|budget|deal size|contract value|in sales|grant|donat|sponsorship of",
    re.I)
PAY_WORDS = re.compile(r"\bpay\b|paid|rate|salary|compensation|wage|earn|range|base|hourly|\busd\b", re.I)
BOUNDARY = re.compile(r"[.!?;]\s|\n|\s{2,}")  # sentence or line break (descriptions keep paragraphs as double spaces)
UNDERGRAD = re.compile(r"undergrad", re.I)


def _clause(text, start, end):
    """The text around one figure, within its sentence and not reaching into another figure."""
    before = text[max(0, start - 200):start]
    cuts = list(BOUNDARY.finditer(before))
    before = before[cuts[-1].end():] if cuts else before
    before = before.rsplit("$", 1)[-1] if "$" in before else before
    after = text[end:end + 200]
    cut = BOUNDARY.search(after)
    after = after[:cut.start()] if cut else after
    return before, after.split("$", 1)[0]


def _amount(whole, frac, k):
    v = float(whole.replace(",", "") + (frac or ""))
    return v * 1000 if k else v


def _unit_word(u):
    u = u.lower()
    if re.search(r"h(ou)?r|\bh\b|hourly", u):
        return "hour"
    if re.search(r"w(ee)?k", u):
        return "week"
    if re.search(r"mo(nth)?", u):
        return "month"
    return "year"


def _guess_unit(lo, hi):
    """No unit written: decide from the size of the numbers."""
    if 8 <= lo <= 200 and hi <= 250:
        return "hour"
    if 15000 <= lo <= 500000:
        return "year"
    return None


def from_text(text):
    """Pay ranges found in free text, as [(lo, hi, unit, explicit, undergrad)]."""
    out = []
    for m in MONEY.finditer(text or ""):
        lo = _amount(m.group(1), m.group(2), m.group(3))
        hi = _amount(m.group(4), m.group(5), m.group(6)) if m.group(4) else lo
        wide_before = text[max(0, m.start() - 60):m.start()]
        before, after = _clause(text, m.start(), m.end())
        if SCALE_AFTER.match(text[m.end():m.end() + 12]) or not lo or not hi:
            continue  # "$6 billion", "$4.1M", "$0.00"
        # Words like "stipend" or "funding" in the same sentence mean it isn't wages.
        if NOT_PAY.search(before + " " + after):
            continue
        um = UNIT_AFTER.match(after)
        unit, explicit = (_unit_word(um.group("u")), True) if um else (None, False)
        if not unit:
            bm = UNIT_BEFORE.search(before)
            if bm:
                unit, explicit = _unit_word(bm.group(1)) if not bm.group(1).lower().startswith(("salary", "annual", "yearly")) \
                    else "year", True
                if unit == "year" and _guess_unit(lo, hi) == "hour":  # "salary range is $29 - $33" (hourly figures)
                    unit = "hour"
        if not unit:
            if not PAY_WORDS.search(wide_before[-50:] + " " + after[:20]):
                continue
            unit = _guess_unit(lo, hi)
        if unit:
            out.append((min(lo, hi), max(lo, hi), unit, explicit, bool(UNDERGRAD.search(before + after))))
    return out


def from_fields(job):
    """The structured salary some boards provide (e.g. "USD 21-21 hourly")."""
    text = job.get("salary_text") or ""
    cur = re.match(r"\s*([A-Z]{3})\b", text)
    if cur and cur.group(1) != "USD":
        return []
    nums = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", text)]
    lo = job.get("salary_min") or (nums[0] if nums else None)
    hi = job.get("salary_max") or (nums[1] if len(nums) > 1 else lo)
    if not lo:
        return []
    um = re.search(r"hour|week|month|year|annual", text, re.I)
    unit = _unit_word(um.group(0)) if um else ("year" if job.get("salary_min") or job.get("salary_max") else _guess_unit(lo, hi or lo))
    return [(min(lo, hi or lo), max(lo, hi or lo), unit, bool(um), False)] if unit else []


def hourly(job):
    """{"lo", "hi", "basis", "text"} in USD per hour, or None when no believable US pay is listed."""
    found = from_fields(job) + from_text(job.get("description"))
    rates = []
    for lo, hi, unit, explicit, undergrad in found:
        f = PER_HOUR[unit]
        if 7 <= lo * f <= 250 and hi * f <= 300:
            rates.append((lo * f, hi * f, unit, explicit, undergrad))
    if not rates:
        return None
    # Rates listed per degree level ("Associate-level: $16, Undergraduate-level: $22, ..."): show the undergraduate ones.
    rates = [r for r in rates if r[4]] or rates
    # Prefer pay stated per hour, then pay with a stated period, over figures whose period was guessed.
    hourly_stated = [r for r in rates if r[2] == "hour" and r[3]]
    chosen = hourly_stated or [r for r in rates if r[3]] or rates
    basis = "hour" if any(r[2] == "hour" for r in chosen) else chosen[0][2]
    chosen = [r for r in chosen if (r[2] == "hour") == (basis == "hour")]
    lo, hi = min(r[0] for r in chosen), max(r[1] for r in chosen)
    return {"lo": round(lo, 2), "hi": round(hi, 2), "basis": basis, "text": fmt(lo, hi, basis != "hour")}


def fmt(lo, hi, estimate=False):
    def one(x):
        return f"{round(x)}" if estimate or abs(x - round(x)) < 0.005 else f"{x:.2f}"
    a, b = one(lo), one(hi)
    return f"{'≈' if estimate else ''}${a}{'' if a == b else '–' + b}/hr"


# ---------------------------------------------------------------- paid or not
UNPAID = re.compile(
    r"\bunpaid\b(?!\s+(leave|time off|vacation|holiday|sick))|\bnot (a )?paid\b|\bpro[- ]?bono (role|position|internship)s?\b|"
    r"\bvoluntary internships?\b|\bvolunteer (position|role|internship|opportunity)\b|"
    r"\b(academic|college|school|course|university) credit only\b|\bfor (academic|college|school|course) credit\b(?! or pay)|"
    r"\bno (monetary )?(compensation|pay|salary)\b|\bwithout (pay|compensation|salary)\b|"
    r"\b(commission|equity)[- ]only\b|\b100% commission\b",
    re.I)
PAID = re.compile(
    r"\bpaid (internship|intern|position|role|opportunity|program)s?\b|\b(internship|position|role) is (a )?paid\b|"
    r"\bcompetitive (pay|compensation|hourly|wage|salary|stipend)\b|\bhourly (pay|rate|wage)\b|"
    r"\b(pay|salary|compensation|wage) range\b|\bbase (pay|salary)\b",
    re.I)
EMPLOYER_SITES = ("greenhouse", "lever", "ashby", "workday", "oracle")  # an employer's own careers site


def status(job):
    """"paid", "unpaid" or "unknown", from what the posting says."""
    text = f"{job.get('title') or ''}\n{job.get('description') or ''}"
    if UNPAID.search(text) or re.search(r"\bvolunteer\b", job.get("title") or "", re.I):
        return "unpaid"
    if hourly(job) or PAID.search(text):
        return "paid"
    return "unknown"


def unpaid_reason(job):
    """Why a job doesn't count as paid, or None.

    Stated unpaid (or credit-, commission- or equity-only) work never counts. A posting that
    doesn't mention pay counts only from an employer's own careers site (large employers pay
    their interns); on job boards, that silence is where unpaid "internships" hide.
    """
    st = status(job)
    if st == "unpaid":
        return "Unpaid"
    if st == "unknown" and job.get("source") not in EMPLOYER_SITES:
        return "Pay not stated"
    return None
