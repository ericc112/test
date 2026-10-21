"""Rank jobs against your search and profile. Scores run 0-100 with plain-English reasons."""
import re
from datetime import datetime, timezone

from . import fields, pay
from .textutil import ALIASES, contains_phrase, norm, split_list, words

DIRECT_APPLY = ("greenhouse", "lever", "ashby")
STOP = {"and", "or", "the", "a", "an", "of", "for", "to", "in", "with", "&", "-", "/"}
WORLDWIDE = re.compile(r"worldwide|anywhere|global|any location|all locations", re.I)
UNSTATED = re.compile(r"^\s*(hybrid|in[- ]?office|on[- ]?site|multiple locations|various( locations)?|flexible|tbd|n/?a|)\s*$", re.I)
_STATES = ("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC "
           "ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY").split()
_STATE_NAMES = ("alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|"
                "illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|"
                "mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|"
                "north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|"
                "south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming")
# "Bethesda, MD", "NC - Charlotte", "Austin, Texas", "USA", "U.S."
US_LOCATION = re.compile(
    r"\b(usa|u\.s\.a?\.?|us|united states( of america)?)\b|"
    r"(^|,\s*|\s-\s*|\(\s*)(" + "|".join(_STATES) + r")(\b|\s*-)|"
    r"^(" + "|".join(_STATES) + r")\s*-|\b(" + _STATE_NAMES + r")\b",
    re.I,
)


def looks_us(loc):
    return bool(US_LOCATION.search(loc or ""))


def _stem_match(kw_word, title_words):
    if kw_word in title_words:
        return True
    if len(kw_word) >= 5:
        root = kw_word[: max(4, len(kw_word) - 2)]
        return any(t.startswith(root) for t in title_words)
    return False


def title_match(title, keywords):
    """Return (points 0-40, matched keyword)."""
    tw = set(words(title))
    best, best_kw = 0.0, None
    for kw in keywords:
        kws = [w for w in words(kw) if w not in STOP]
        if not kws:
            continue
        if contains_phrase(title, kw):
            pts = 40
        else:
            hit = sum(_stem_match(w, tw) for w in kws)
            pts = 32 if hit == len(kws) else 20 * hit / len(kws)
        if pts > best:
            best, best_kw = pts, kw
    return best, best_kw


def relevant(job, search):
    """Pre-filter used while fetching: right field (if one is set) and, if you listed
    titles, every word of one of them is in the job title."""
    if search.get("field") and not fields.classify(job, search)[0]:
        return False
    if not fields.type_ok(job, search)[0]:
        return False
    keywords = split_list(search.get("keywords"))
    if not keywords:
        return True
    pts, _ = title_match(job.get("title", ""), keywords)
    return pts >= 32


def age_days(job):
    ts = job.get("posted_at")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400)


def days_since(ts):
    """Days since an ISO timestamp, or None when there isn't one."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400)


def pay_top(job):
    """The highest pay figure known for a job, whichever field holds it: the board's own
    salary (salary_*, set by Lever/Ashby/aggregators) wins, then the pay extracted from
    the posting text (pay_*), which is all Greenhouse/Workday jobs ever get."""
    return job.get("salary_max") or job.get("salary_min") or job.get("pay_max") or job.get("pay_min")


# A listing a full-board feed hasn't returned for this long is gone, however recent its
# posting date claims to be. Feeds that only ever report *new* postings (Workday, Greenhouse…)
# can't say whether an old one is still up, so their jobs are exempt (see pipeline.rescore).
VANISHED_DAYS = 14


def _loc_names(loc):
    n = norm(loc)
    for canon, names in ALIASES.items():
        if n == canon or n in names:
            return {canon, *names}
    return {n}


def location_fit(job, search):
    """Return (points -20..20, reason). Jobs you can't take from where you are lose points."""
    wanted = split_list(search.get("locations"))
    loc = job.get("location") or ""
    remote_wanted = search.get("remote") != "onsite_only" and (
        not wanted or any(norm(w) == "remote" for w in wanted) or search.get("remote") == "remote_only"
    )
    places = [w for w in wanted if norm(w) != "remote"]
    place_hit = next(
        (w for w in places if any(contains_phrase(loc, n) for n in _loc_names(w) if len(n) > 2)
         or (norm(w) in _loc_names("united states") and looks_us(loc))),
        None,
    )
    if job.get("remote") and remote_wanted:
        if place_hit or not places or not loc or WORLDWIDE.search(loc) or norm(loc) == "remote":
            return 20, "Remote"
        return -15, f"Remote, but only for {loc[:60]}"
    if place_hit:
        return 20, f"In {place_hit}"
    if not wanted:
        return 10, None
    if UNSTATED.match(loc):
        return 5, "Location not stated"
    if not places:  # you only asked for remote, and this job isn't
        return -20, f"On-site in {loc[:60] or 'unknown location'}"
    return -20, f"{loc[:60] or 'Unknown location'} isn't one of your locations"


def exclusion(job, search):
    """Reason the job should be hidden, or None."""
    if search.get("field"):
        ok, why = fields.classify(job, search)
        if not ok:
            return why
    ok, why = fields.type_ok(job, search)
    if not ok:
        return why
    if search.get("paid_only", True):
        why = pay.unpaid_reason(job) if fields.job_type(job) == "internship" else \
            ("Unpaid" if pay.status(job) == "unpaid" else None)
        if why:
            return why
    title = job.get("title") or ""
    if fields.job_type(job) == "internship" and fields.season_over(title, datetime.now(timezone.utc).date()):
        season, year = fields.season_of(title)
        return f"{season} {year} has already passed"
    for ex in split_list(search.get("exclude")):
        if contains_phrase(title, ex):
            return f"Title contains '{ex}'"
    mode = search.get("remote", "any")
    if mode == "remote_only" and not job.get("remote"):
        return "Not remote"
    if mode == "onsite_only" and job.get("remote"):
        return "Remote only"
    max_age = search.get("max_age_days") or 0
    days = age_days(job)
    if max_age and days is not None and days > max_age:
        return f"Posted {int(days)} days ago"
    seen = days_since(job.get("last_seen"))
    if seen is not None and seen > VANISHED_DAYS and not job.get("feed_incremental"):
        return f"No longer listed — the board hasn't shown it for {int(seen)} days"
    min_salary = search.get("min_salary") or 0
    top = pay_top(job)
    if min_salary and top and top < min_salary:
        return f"Pays up to {int(top):,}, below your minimum"
    return None


def score(job, search, profile):
    """Return (score 0-100, reasons, exclusion reason or None)."""
    reasons = []
    keywords = split_list(search.get("keywords"))
    in_field, area = fields.classify(job, search) if search.get("field") else (False, None)
    t_pts, kw = title_match(job.get("title", ""), keywords) if keywords else ((34 if in_field else 25), None)
    if fields.job_type(job) == "internship":
        reasons.append("Internship")
    if in_field:
        reasons.append(f"{area} role")
    if kw:
        reasons.append(f"Title matches “{kw}”")

    skills = split_list(profile.get("skills"))
    text = f"{job.get('title', '')}\n{job.get('description', '')}\n{' '.join(job.get('tags') or [])}"
    if skills:
        hits = [s for s in skills if contains_phrase(text, s)]
        target = max(3, min(8, len(skills)))
        s_pts = 30 * min(1.0, len(hits) / target)
        if hits:
            reasons.append(f"{len(hits)} of your skills: {', '.join(hits[:6])}")
    else:
        s_pts = 15

    l_pts, l_reason = location_fit(job, search)
    if l_reason:
        reasons.append(l_reason)

    days = age_days(job)
    if days is None:
        r_pts = 3
    else:
        r_pts = 10 if days <= 3 else 8 if days <= 7 else 5 if days <= 14 else 2 if days <= 30 else 0
        reasons.append("Posted today" if days < 1 else f"Posted {int(days)}d ago")

    total = t_pts + s_pts + l_pts + r_pts
    if in_field and fields.asks_for_business_degree(job):
        total += 6
        reasons.append("Asks for a business degree")
    if job.get("ats") in DIRECT_APPLY:
        total += 5
        reasons.append("JobBot can apply directly")
    season = fields.season_of(job.get("title"))
    terms = split_list(profile.get("internship_terms"))
    if season and terms and fields.job_type(job) == "internship":
        label = f"{season[0]} {season[1]}"
        if any(norm(t) == norm(label) for t in terms):
            total += 5
            reasons.append(f"{label}, the term you want")
        else:
            total -= 10
            reasons.append(f"{label} (you want {', '.join(terms)})")
    hourly = pay.hourly(job)
    if hourly:
        reasons.append(f"Pay: {hourly['text']}")
    elif job.get("salary_text"):
        reasons.append(f"Pay: {job['salary_text']}")
    min_salary = search.get("min_salary") or 0
    top = pay_top(job)
    if min_salary and top and top < min_salary:
        total -= 25
    excluded = exclusion(job, search) or fields.level_mismatch(job, profile)
    return max(0, min(100, round(total))), reasons, excluded
