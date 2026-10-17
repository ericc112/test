"""Phenom career sites (e.g. careers.molsoncoors.com/us/en, jobs.newmont.com/us/en).

Reads the same search service the careers page calls ({site}/widgets, "refineSearch").
Many Phenom sites front a Workday site; those are watched through Workday instead, so
JobBot can fill them in. The rest are alerts with a link to the posting.

A board key is the site's host and locale path, e.g. "careers.molsoncoors.com/us/en".
"""
import json
import re
import sys

from .. import fields, scoring
from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register, suggested_names

NAME = "phenom"
LABEL = "Phenom career sites"
EMPLOYER = True
INCREMENTAL = True
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60
PAGE = 50
PAGES = 3
DETAIL_LIMIT = 15

KEY_RE = re.compile(r"^([a-z0-9-]+(?:\.[a-z0-9-]+)+)/([a-z]{2,6})/([a-z]{2})$")
NAMES = suggested_names(NAME)
DDO_RE = re.compile(r"phApp\.ddo\s*=\s*(\{.*?\});\s*phApp\.", re.S)


def keys(search):
    wanted = fields.wanted_types(search)
    out = []
    for k in search.get("companies", {}).get(NAME, []):
        if not KEY_RE.match(k):
            continue
        if "full_time" in wanted:
            out.append(k)
        if "internship" in wanted:
            out.append(f"{k}#intern")
    return out


def parse_key(key):
    host, country, lang = KEY_RE.match(key.split("#")[0]).groups()
    return host, country, lang


def id_prefix(key):
    return f"{NAME}:{parse_key(key)[0]}:"


def company_name(key):
    site = key.split("#")[0]
    return NAMES.get(site) or display_name(parse_key(key)[0].split(".")[-2])


def _search(key, keyword="", start=0, size=PAGE):
    host, country, lang = parse_key(key)
    payload = {"lang": f"{lang}_{country}", "deviceType": "desktop", "country": country, "pageName": "search-results",
               "ddoKey": "refineSearch", "sortBy": "", "subsearch": "", "from": start, "jobs": True, "counts": False,
               "all_fields": [], "size": size, "clearAll": False, "jdsource": "facets", "isSliderEnable": False,
               "pageId": "page20", "siteType": "external", "keywords": keyword, "global": True,
               "selected_fields": {}, "locationData": {}}
    data = http.post_json(f"https://{host}/widgets", payload).get("refineSearch") or {}
    if data.get("status") not in (200, None) or "data" not in data:
        raise http.FetchError(f"no Phenom search on {host}")
    return data.get("totalHits") or 0, data["data"].get("jobs") or []


def probe(key):
    try:
        total, _ = _search(key, size=1)
        return total > 0
    except (http.FetchError, ValueError, KeyError, AttributeError):
        return False


def job_url(key, job_id):
    host, country, lang = parse_key(key)
    return f"https://{host}/{country}/{lang}/job/{job_id}"


def to_job(key, p, company):
    host = parse_key(key)[0]
    job_id = str(p.get("jobId") or p.get("reqId"))
    kind = p.get("type") or ""  # "Student/Intern", "Full time", "Regular/Permanent"...
    remote = p.get("remote") or ""
    return make_job(
        NAME, f"{host}:{job_id}", p.get("title"), p.get("brand") or company, job_url(key, job_id),
        ats="manual", location=(p.get("cityStateCountry") or p.get("location") or p.get("country") or "")[:200],
        remote="remote" in remote.lower() or "remote" in (p.get("location") or "").lower(),
        posted_at=iso(p.get("postedDate") or p.get("dateCreated")), description=html_to_text(p.get("descriptionTeaser") or ""),
        tags=[t for t in (kind, remote) if t], categories=[c for c in (p.get("multi_category") or [p.get("category")]) if c],
    )


def _detail(url):
    _, body = http.get(url, retries=1, accept="text/html,application/xhtml+xml")
    m = DDO_RE.search(body)
    job = (json.loads(m.group(1)).get("jobDetail") or {}).get("data", {}).get("job", {}) if m else {}
    return html_to_text(job.get("description") or "")


def fetch(key, search, known=None):
    known = known or set()
    intern = key.endswith("#intern")
    company = company_name(key)
    out, details_left = [], DETAIL_LIMIT
    for page in range(PAGES):
        total, posts = _search(key, "intern" if intern else "", page * PAGE)
        for p in posts:
            if not p.get("title") or not (p.get("jobId") or p.get("reqId")):
                continue
            job = to_job(key, p, company)
            if job["id"] in known or not scoring.relevant(job, search) or scoring.exclusion(job, search):
                continue
            if details_left > 0:
                details_left -= 1
                try:
                    job["description"] = _detail(job["url"]) or job["description"]
                    if scoring.exclusion(job, search):
                        continue
                except (http.FetchError, ValueError):
                    pass
            out.append(job)
        if (page + 1) * PAGE >= total or len(posts) < PAGE:
            break
    return out


register(sys.modules[__name__])
