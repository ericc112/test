"""Jobicy remote jobs (jobicy.com/api/v2)."""
import sys
import threading
import time

from .. import fields
from ..textutil import html_to_text
from . import http, iso, make_job, register

NAME = "jobicy"
LABEL = "Jobicy"
MIN_INTERVAL = 60 * 60
FORCE_MIN_INTERVAL = 10 * 60
_lock = threading.Lock()  # Jobicy answers 403 to concurrent requests


def keys(search):
    # With a field filter, browse Jobicy's matching industries; otherwise search by tag.
    wanted = fields.wanted_types(search)
    out = ["tag:internship"] if "internship" in wanted else []
    if "full_time" in wanted:
        if search.get("field") and not search.get("keywords"):
            out += [f"industry:{i}" for i in fields.source_terms(search, "jobicy")]
        else:
            out += [f"tag:{k}" for k in search.get("keywords") or []]
    return out


def fetch(key, search):
    kind, _, value = key.partition(":")
    if not value:  # keys from older versions were plain keywords
        kind, value = "tag", key
    with _lock:
        try:
            data = http.get_json("https://jobicy.com/api/v2/remote-jobs", {"count": 50, kind: value})
        except http.FetchError as e:
            if "HTTP 403" not in str(e):
                raise
            time.sleep(15)  # Jobicy throttles bursts with a 403; one slower retry
            data = http.get_json("https://jobicy.com/api/v2/remote-jobs", {"count": 50, kind: value})
        time.sleep(4)
    out = []
    for j in data.get("jobs", []):
        lo, hi = j.get("salaryMin"), j.get("salaryMax")
        period = (j.get("salaryPeriod") or "").lower()
        annual = period in ("", "yearly", "annual", "year")
        out.append(make_job(
            NAME, j["id"], j.get("jobTitle"), j.get("companyName"), j.get("url"),
            location=j.get("jobGeo") or "Remote", remote=True,
            description=html_to_text(j.get("jobDescription")), posted_at=iso(j.get("pubDate")),
            salary_min=lo if annual else None, salary_max=hi if annual else None,
            salary_text=f"{j.get('salaryCurrency') or ''} {lo}-{hi} {period}".strip() if lo else None,
            tags=j.get("jobType") or [], categories=j.get("jobIndustry") or [],
        ))
    return out


register(sys.modules[__name__])
