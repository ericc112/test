"""Small text helpers shared by sources, scoring and the answer engine."""
import html
import re
from difflib import SequenceMatcher

_TAG = re.compile(r"<[^>]+>")
_BLOCK = re.compile(r"</?(p|div|br|li|ul|ol|h[1-6]|tr|section)[^>]*>", re.I)
_WS = re.compile(r"[ \t\r\f\v]+")


def html_to_text(s):
    """Turn job-description HTML (possibly entity-escaped twice) into plain text."""
    if not s:
        return ""
    s = html.unescape(s)
    if "&lt;" in s or "&amp;" in s:
        s = html.unescape(s)
    s = _BLOCK.sub("\n", s)
    s = _TAG.sub(" ", s)
    s = html.unescape(s)
    lines = [_WS.sub(" ", line).strip() for line in s.splitlines()]
    out, blank = [], False
    for line in lines:
        if not line:
            if not blank and out:
                out.append("")
            blank = True
            continue
        out.append(line)
        blank = False
    return "\n".join(out).strip()


def norm(s):
    """Lowercase, drop required-markers and punctuation noise, collapse spaces."""
    s = (s or "").lower().replace("’", "'").replace(" ", " ")
    s = re.sub(r"[✱*]+", " ", s)
    s = re.sub(r"[^a-z0-9'+#./&\- ]+", " ", s)
    s = re.sub(r"\s[-/&]\s", " ", f" {s} ")
    return re.sub(r"\s+", " ", s).strip()


def words(s):
    return re.findall(r"[a-z0-9+#.]+", norm(s))


def similarity(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def contains_phrase(text, phrase):
    """Whole-word, case-insensitive phrase match ("java" doesn't match "javascript")."""
    p = norm(phrase)
    if not p:
        return False
    return re.search(r"(?<![a-z0-9])" + re.escape(p) + r"(?![a-z0-9])", norm(text)) is not None


def split_list(value):
    """Accept a list or a comma/newline separated string."""
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = re.split(r"[,\n;]", value or "")
    return [i.strip() for i in items if i and str(i).strip()]


DECLINE_RE = re.compile(
    r"decline|don'?t wish|do not wish|prefer not|not to (say|answer|disclose|self[- ]?identify)|"
    r"choose not|not (want|wish) to|rather not|i don'?t want",
    re.I,
)

ALIASES = {
    "united states": ["united states", "united states of america", "usa", "us", "u.s.", "u.s.a."],
    "united kingdom": ["united kingdom", "uk", "u.k.", "great britain", "england"],
    "bachelor's": ["bachelor", "bachelors", "bachelor's degree", "bs", "ba", "b.s.", "b.a.", "bsc", "b.sc."],
    "master's": ["master", "masters", "master's degree", "ms", "ma", "m.s.", "m.a.", "msc", "mba"],
    "doctorate": ["phd", "ph.d.", "doctor of philosophy", "doctorate", "doctoral"],
    "associate's": ["associate", "associates", "associate's degree"],
    "high school": ["high school", "high school diploma", "ged"],
}


def _alias_set(value):
    v = norm(value)
    for canon, names in ALIASES.items():
        if v == canon or v in names:
            return {canon, *names}
    return {v}


# Options that say "No" or "Yes" without the word: "Not to my knowledge", "I have never been employed by…", "I agree".
NO_LIKE = re.compile(r"^(not to my knowledge|not that i('m| am) aware|none\b|never\b|n/?a\b|not applicable|i('m| am) not\b|"
                     r"i (have never|have not|haven't|do not|don't|did not|didn't|will not|won't|no longer)\b)")
YES_LIKE = re.compile(r"^(i (agree|acknowledge|consent|accept|confirm|certify|understand|can|will|have read|attest)\b|i('m| am) able\b|"
                      r"by (checking|clicking|selecting) this box,? i (consent|agree|acknowledge|accept))")


def _numbers(s):
    return [float(m.group(1).replace(",", "")) * (1000 if m.group(2) else 1)
            for m in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(k)?\b", s or "", re.I)]


def in_range(value, option):
    """Whether a number falls in a range option: "$60,000-$70,000", "Less than 1 year", "More than 1 year, less than
    3 years", "5+ Years", "0 - 6 months", "No previous relevant work experience" (zero)."""
    o, nums = norm(option), _numbers(option)
    if re.search(r"\bmonths?\b", o) and not re.search(r"\byears?\b", o):
        nums = [n / 12 for n in nums]
    if not nums:
        return value == 0 and bool(re.match(r"(no|none)\b", o))
    above = re.search(r"\b(more than|over|above|greater than)\b", o)
    below = re.search(r"\b(less than|under|below|fewer than)\b", o)
    if len(nums) >= 2:
        lo, hi = nums[:2]
        return (lo < value if above else lo <= value) and (value < hi if below else value <= hi)
    n = nums[0]
    if below or re.search(r"\bup to\b|or (less|fewer|below)", o):
        return value < n if below and not re.search(r"or (less|fewer|below)", o) else value <= n
    if above or re.search(r"\+|or more|at least|\bplus\b", o):
        return value > n if above and not re.search(r"or more", o) else value >= n
    return value == n


def pick_option(answer, options):
    """Choose the option that best matches an answer. Returns the option text or None."""
    if answer is None or not options:
        return None
    opts = [o for o in options if norm(o)]
    if not opts:
        return None
    a = norm(str(answer))
    if not a:
        return None
    if a == "decline":
        for o in opts:
            if DECLINE_RE.search(o):
                return o
        return None
    names = _alias_set(a)
    for o in opts:
        if norm(o) in names:
            return o
    # A number picks the range it falls in: 65000 → "$60,000-$70,000", 0 → "Less than 1 year".
    num = re.fullmatch(r"\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(k)?\s*(years?|yrs?)?", str(answer).strip(), re.I)
    if num:
        value = float(num.group(1).replace(",", "")) * (1000 if num.group(2) else 1)
        ranged = [o for o in opts if in_range(value, o)]
        if ranged:
            return ranged[0]
    # Yes/No style answers: "Yes" matches "Yes, I intend to work remotely."; "No" also "Not to my knowledge".
    if a in ("yes", "no"):
        for o in opts:
            if re.match(rf"^{a}\b", norm(o)):
                return o
        like = NO_LIKE if a == "no" else YES_LIKE
        return next((o for o in opts if like.match(norm(o))), None)
    for o in opts:
        no = norm(o)
        if any(re.match(rf"^{re.escape(n)}\b", no) for n in names if len(n) > 1):
            return o
    contained = [o for o in opts if len(norm(o)) >= 3 and (a in norm(o) or norm(o) in a)]
    if contained:
        return min(contained, key=lambda o: abs(len(norm(o)) - len(a)))
    # Every meaningful word of the answer appears in the option ("NYU Stern" ≠ "Andrews University").
    key_words = {w for w in words(a) if w not in _FILLER}
    if key_words:
        covering = [o for o in opts if key_words <= set(words(o))]
        if covering:
            return min(covering, key=lambda o: len(norm(o)))
    best = max(opts, key=lambda o: similarity(a, o))
    return best if similarity(a, best) >= 0.9 else None


_FILLER = {"of", "the", "and", "at", "in", "a", "an", "for", "&"}
