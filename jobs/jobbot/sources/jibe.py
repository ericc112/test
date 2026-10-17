"""Jibe career sites (iCIMS's "Jibe" front end, e.g. jobs.statefarm.com, careers.amd.com).

Insurers, utilities, banks and retailers. Reads the public JSON the careers page loads
({host}/api/jobs). Applications happen on the employer's iCIMS site, which needs an
account, so JobBot alerts you and links to the posting.

A board key is the careers host, e.g. "jobs.statefarm.com".
"""
import re
import sys

from .. import fields, scoring
from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register, suggested_names

NAME = "jibe"
LABEL = "Jibe career sites"
EMPLOYER = True
INCREMENTAL = True
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60
PAGE = 100
PAGES = 3

HOST_RE = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)+$")
NAMES = suggested_names(NAME)


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


def _search(host, keyword="", page=1, limit=PAGE):
    params = {"page": page, "limit": limit, "sortBy": "posted_date", "descending": "true"}
    if keyword:
        params["keywords"] = keyword
    data = http.get_json(f"https://{host}/api/jobs", params)
    if not isinstance(data, dict) or "jobs" not in data:
        raise http.FetchError(f"not a Jibe site: {host}")
    return data.get("totalCount") or 0, [j.get("data") or {} for j in data.get("jobs") or []]


def probe(key):
    try:
        total, _ = _search(host_of(key), limit=1)
        return total > 0
    except (http.FetchError, ValueError):
        return False


def to_job(host, d, company):
    slug = str(d.get("slug") or d.get("req_id") or "")
    url = (d.get("meta_data") or {}).get("canonical_url") or f"https://{host}/jobs/{slug}?lang={d.get('language') or 'en-us'}"
    loc = d.get("full_location") or d.get("location_name") or ""
    if d.get("country") and d["country"] not in loc:
        loc = f"{loc}, {d['country']}" if loc else d["country"]
    desc = " ".join(x for x in (d.get("description"), d.get("responsibilities"), d.get("qualifications")) if x)
    kind = (d.get("employment_type") or "").replace("_", " ").title()  # INTERN, FULL_TIME...
    text = " ".join(str(v) for k, v in d.items() if k.startswith("tags") and v)
    return make_job(
        NAME, f"{host}:{slug}", d.get("title"), d.get("hiring_organization") or d.get("brand") or company, url,
        ats="manual", location=loc[:200], remote=d.get("location_type") == "ANYWHERE" or bool(re.search(r"\bremote\b", text, re.I)),
        posted_at=iso(d.get("posted_date")), description=html_to_text(desc),
        tags=[t for t in (kind,) if t], categories=[c.get("name") for c in d.get("categories") or [] if c.get("name")],
    )


def fetch(key, search, known=None):
    known = known or set()
    host = host_of(key)
    intern = key.endswith("#intern")
    company = company_name(key)
    out = []
    for page in range(1, PAGES + 1):
        _, posts = _search(host, "intern" if intern else "", page)
        unseen = 0
        for d in posts:
            if not d.get("title") or not (d.get("slug") or d.get("req_id")):
                continue
            job = to_job(host, d, company)
            if job["id"] in known:
                continue
            unseen += 1
            if scoring.relevant(job, search) and not scoring.exclusion(job, search):
                out.append(job)
        if len(posts) < PAGE or (known and unseen == 0):
            break  # newest first: a page with nothing new means we've caught up
    return out


register(sys.modules[__name__])
