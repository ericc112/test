"""Workday career sites ({tenant}.wdN.myworkdayjobs.com): banks, consultancies, big brands.

Reads the same public JSON feed the employer's careers page loads, newest postings
first, so a new listing shows up within one poll. Workday asks applicants to create an
account with each employer, so JobBot alerts you and links to the posting instead of
filling the form itself.

A board key is "tenant|wdN|site", e.g. "capitalone|wd12|Capital_One".
"""
import re
import sys
from datetime import datetime, timedelta, timezone

from .. import config, scoring
from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register

NAME = "workday"
LABEL = "Workday career sites"
EMPLOYER = True
INCREMENTAL = True
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60
PAGE = 20
MAX_PAGES = 5  # newest 100 postings; polls stop as soon as a page holds nothing new
DETAIL_LIMIT = 25

_looked_at = set()  # postings already looked at this session (incl. non-matches), for paging
URL_RE = re.compile(r"https?://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w-]+)", re.I)
NAMES = {slug.split("|")[0]: name for name, kind, slug in config.SUGGESTED_COMPANIES if kind == NAME}


def keys(search):
    return [k for k in search.get("companies", {}).get(NAME, []) if k.count("|") == 2]


def parse_key(key):
    tenant, wd, site = key.split("|")
    return tenant, wd, site


def key_from_url(url):
    m = URL_RE.match(url or "")
    return f"{m.group(1)}|{m.group(2)}|{m.group(3)}" if m else None


def id_prefix(key):
    return f"{NAME}:{parse_key(key)[0]}:"


def company_name(key):
    tenant, _, site = parse_key(key)
    return NAMES.get(tenant) or display_name(tenant)


def _api(key):
    tenant, wd, site = parse_key(key)
    return f"https://{tenant}.{wd}.myworkdayjobs.com", f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}"


def probe(key):
    try:
        data = http.post_json(f"{_api(key)[1]}/jobs", {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""}, retries=0)
        return "jobPostings" in data
    except http.FetchError:
        return False


def posted_from_text(text, now=None):
    """'Posted Today' / 'Posted Yesterday' / 'Posted 3 Days Ago' / 'Posted 30+ Days Ago' → ISO date."""
    now = now or datetime.now(timezone.utc)
    t = (text or "").lower()
    if "today" in t:
        days = 0
    elif "yesterday" in t:
        days = 1
    else:
        m = re.search(r"(\d+)\+?\s*day", t)
        if not m:
            return None
        days = int(m.group(1))
    d = (now - timedelta(days=days)).date()
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).isoformat(timespec="seconds")


def _job_key(p):
    bullets = p.get("bulletFields") or []
    if bullets and re.match(r"^[A-Za-z0-9_-]{3,}$", bullets[0] or ""):
        return bullets[0]
    return (p.get("externalPath") or "").rstrip("/").rsplit("/", 1)[-1]


def fetch(key, search, known=None):
    known = known or set()
    tenant, _, site = parse_key(key)
    base, api = _api(key)
    name = company_name(key)
    out, details_left = [], DETAIL_LIMIT
    for page in range(MAX_PAGES):
        data = http.post_json(f"{api}/jobs", {"appliedFacets": {}, "limit": PAGE, "offset": page * PAGE, "searchText": ""})
        posts = data.get("jobPostings") or []
        unseen = 0
        for p in posts:
            if not p.get("title") or not p.get("externalPath"):
                continue
            job = make_job(
                NAME, f"{tenant}:{_job_key(p)}", p["title"], name, f"{base}/{site}{p['externalPath']}",
                ats="manual", location=p.get("locationsText") or "",
                remote="remote" in (p.get("locationsText") or "").lower(),
                posted_at=posted_from_text(p.get("postedOn")),
            )
            if job["id"] in known:
                continue
            if job["id"] not in _looked_at:
                unseen += 1
                _looked_at.add(job["id"])
            if not scoring.relevant(job, search) or scoring.exclusion(job, search):
                continue
            if details_left > 0:
                details_left -= 1
                try:
                    info = http.get_json(f"{api}{p['externalPath']}", retries=1).get("jobPostingInfo") or {}
                    job["description"] = html_to_text(info.get("jobDescription"))
                    job["posted_at"] = iso(info.get("startDate")) or job["posted_at"]
                    job["location"] = info.get("location") or job["location"]
                    job["remote"] = job["remote"] or (info.get("remoteType") or "").lower() == "remote"
                    job["apply_url"] = info.get("externalUrl") or job["url"]
                    job["tags"] = [t for t in (info.get("timeType"), info.get("remoteType")) if t]
                except http.FetchError:
                    pass
            out.append(job)
        # Newest first: once a whole page is already known, we've caught up.
        if len(posts) < PAGE or (known and unseen == 0):
            break
    return out


register(sys.modules[__name__])
