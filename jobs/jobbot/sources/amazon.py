"""Amazon's own careers site (amazon.jobs), read through the JSON its search page uses.

Amazon runs its own hiring system, so applications happen on amazon.jobs: JobBot alerts
you and links to the posting. The feed marks internships itself ("is_intern").
"""
import sys
from datetime import datetime, timezone

from .. import fields, scoring
from ..textutil import html_to_text
from . import http, make_job, register

NAME = "amazon"
LABEL = "Amazon careers"
EMPLOYER = True
INCREMENTAL = True
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60
PAGE = 100
PAGES = 3
API = "https://www.amazon.jobs/en/search.json"


def keys(search):
    if "amazon" not in search.get("companies", {}).get(NAME, []):
        return []
    wanted = fields.wanted_types(search)
    return (["amazon"] if "full_time" in wanted else []) + (["amazon#intern"] if "internship" in wanted else [])


def id_prefix(key):
    return f"{NAME}:"


def probe(key):
    try:
        return bool(http.get_json(API, {"base_query": "", "result_limit": 1, "offset": 0}).get("hits"))
    except http.FetchError:
        return False


def _date(text):
    try:
        return datetime.strptime(" ".join((text or "").split()), "%B %d, %Y").replace(tzinfo=timezone.utc).isoformat(timespec="seconds")
    except ValueError:
        return None


def fetch(key, search, known=None):
    known = known or set()
    intern = key.endswith("#intern")
    places = [p for p in search.get("locations") or [] if p.strip().lower() != "remote"]
    us_only = bool(places) and all(scoring.looks_us(p) for p in places)  # e.g. "United States", "New York, NY"
    out = []
    for page in range(PAGES):
        params = {"base_query": "intern" if intern else "", "sort": "recent", "result_limit": PAGE, "offset": page * PAGE}
        if us_only:
            params["country"] = "USA"
        data = http.get_json(API, params)
        posts = data.get("jobs") or []
        unseen = 0
        for p in posts:
            if not p.get("title") or not p.get("job_path"):
                continue
            desc = " ".join(x for x in (p.get("description"), p.get("basic_qualifications"),
                                        p.get("preferred_qualifications")) if x)
            job = make_job(
                NAME, str(p.get("id_icims") or p.get("id")), p["title"], "Amazon", "https://www.amazon.jobs" + p["job_path"],
                ats="manual", location=p.get("normalized_location") or p.get("location") or "",
                posted_at=_date(p.get("posted_date")), description=html_to_text(desc),
                tags=(["Internship"] if p.get("is_intern") else []) + [t for t in (p.get("job_schedule_type"),) if t],
                categories=[c for c in (p.get("job_category"), p.get("business_category")) if c],
            )
            if job["id"] in known:
                continue
            unseen += 1
            if scoring.relevant(job, search) and not scoring.exclusion(job, search):
                out.append(job)
        if len(posts) < PAGE or (known and unseen == 0):
            break
    return out


register(sys.modules[__name__])
