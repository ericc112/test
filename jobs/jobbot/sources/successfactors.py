"""SAP SuccessFactors career sites (e.g. careers.chsinc.com, jobs.deere.com).

Manufacturers, utilities, railroads and insurers. These sites have no public JSON, so JobBot
reads the same search results page a visitor sees ({host}/search/?title=intern), newest first,
and opens a posting only when its title is a match. Applying needs an account with the
employer, so JobBot alerts you and links to the posting.

A board key is the careers host, e.g. "careers.chsinc.com".
"""
import html
import re
import sys
from datetime import datetime, timezone

from .. import fields, scoring
from ..textutil import html_to_text
from . import display_name, http, make_job, register, suggested_names

NAME = "successfactors"
LABEL = "SuccessFactors career sites"
EMPLOYER = True
INCREMENTAL = True
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60
PAGE = 25  # rows per results page (fixed by the site)
PAGES = 4
DETAIL_LIMIT = 15

HOST_RE = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
NAMES = suggested_names(NAME)
ROW_RE = re.compile(r'<(?:tr class="data-row|li class="job-tile)[^>]*>')  # where a row starts: table or tile layout
LINK_RE = re.compile(r'<a\b[^>]*class="jobTitle-link[^"]*"[^>]*>', re.S)
HREF_RE = re.compile(r'href="([^"]*/job/[^"]+)"')  # "/job/..." or a path such as "/eightfold/job/..."
LOC_RE = re.compile(r'<span class="jobLocation">(.*?)</span>|-section-location-value">(.*?)<', re.S)
DATE_RE = re.compile(r'<span class="jobDate[^"]*">(.*?)</span>|-section-date-value">(.*?)<', re.S)
TOTAL_RE = re.compile(r"of\s*<b>\s*([\d,]+)\s*</b>")


def keys(search):
    wanted = fields.wanted_types(search)
    out = []
    for k in search.get("companies", {}).get(NAME, []):
        if not HOST_RE.match(k):
            continue
        if "full_time" in wanted:
            out.append(k)
        if "internship" in wanted:
            out.append(f"{k}#intern")
    return out


def host_of(key):
    return key.split("#")[0]


def id_prefix(key):
    return f"{NAME}:{host_of(key)}:"


def company_name(key):
    host = host_of(key)
    return NAMES.get(host) or display_name(host.split(".")[-2])


def _text(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment or "")).split())


def _date(text):
    for fmt in ("%b %d, %Y", "%d %b %Y", "%m/%d/%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            continue
    return None


def parse_results(body):
    """Rows of a results page: [{path, title, location, posted_at}] and the result count."""
    rows = []
    starts = [m.start() for m in ROW_RE.finditer(body)]
    for start, end in zip(starts, starts[1:] + [len(body)]):
        row = body[start:end]
        a = LINK_RE.search(row)
        href = HREF_RE.search(a.group(0)) if a else None
        if not href:
            continue
        title = row[a.end():row.find("</a>", a.end())]
        loc = LOC_RE.search(row)
        date = DATE_RE.search(row)
        rows.append({"path": html.unescape(href.group(1)), "title": _text(title),
                     "location": _text(loc.group(1) or loc.group(2)) if loc else "",
                     "posted_at": _date(_text(date.group(1) or date.group(2))) if date else None})
    total = TOTAL_RE.search(body)
    return rows, int(total.group(1).replace(",", "")) if total else None  # tile pages don't say


def _search(host, intern, start=0):
    params = {"q": "", "sortColumn": "referencedate", "sortDirection": "desc", "startrow": start}
    if intern:
        params["title"] = "intern"
    _, body = http.get(f"https://{host}/search/", params, accept="text/html,application/xhtml+xml")
    if 'id="noresults"' in body:
        return [], 0  # nothing matched; the jobs below that notice are just the site's newest postings
    if "jobTitle-link" not in body:
        raise http.FetchError(f"not a SuccessFactors career site: {host}")
    return parse_results(body)


def probe(key):
    try:
        rows, total = _search(host_of(key), False)
        return bool(rows)
    except http.FetchError:
        return False


def parse_detail(body):
    m = re.search(r'<span class="jobdescription">(.*?)</span>\s*</span>', body, re.S) or \
        re.search(r'itemprop="description"[^>]*>(.*?)</(?:span|div)>\s*</div>', body, re.S)
    posted = re.search(r'itemprop="datePosted" content="([^"]+)"', body)
    when = None
    if posted:
        try:
            when = datetime.strptime(posted.group(1), "%a %b %d %H:%M:%S UTC %Y").replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            pass
    return (html_to_text(m.group(1)) if m else ""), when


def fetch(key, search, known=None):
    known = known or set()
    host = host_of(key)
    intern = key.endswith("#intern")
    company = company_name(key)
    out, details_left = [], DETAIL_LIMIT
    for page in range(PAGES):
        rows, total = _search(host, intern, page * PAGE)
        unseen = 0
        for r in rows:
            ext = r["path"].rstrip("/").rsplit("/", 1)[-1]  # /job/City-Title-ST-12345/1431172000/
            job = make_job(NAME, f"{host}:{ext}", r["title"], company, f"https://{host}{r['path']}",
                           ats="manual", location=r["location"][:200], posted_at=r["posted_at"],
                           remote=bool(re.search(r"\bremote\b", r["location"], re.I)), description="")
            if job["id"] in known:
                continue
            unseen += 1
            if not scoring.relevant(job, search) or scoring.exclusion(job, search):
                continue
            if details_left > 0:
                details_left -= 1
                try:
                    _, body = http.get(job["url"], retries=1, accept="text/html,application/xhtml+xml")
                    job["description"], when = parse_detail(body)
                    job["posted_at"] = when or job["posted_at"]
                    if scoring.exclusion(job, search):  # the description can rule it out (e.g. unpaid)
                        continue
                except http.FetchError:
                    pass
            out.append(job)
        if (total is not None and (page + 1) * PAGE >= total) or len(rows) < PAGE or (known and unseen == 0):
            break  # newest first: a page with nothing new means we've caught up
    return out


register(sys.modules[__name__])
