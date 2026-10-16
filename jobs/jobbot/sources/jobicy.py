"""Jobicy remote jobs (jobicy.com/api/v2)."""
import sys
import threading
import time

from ..textutil import html_to_text
from . import http, iso, make_job, register

NAME = "jobicy"
LABEL = "Jobicy"
MIN_INTERVAL = 60 * 60
FORCE_MIN_INTERVAL = 10 * 60
_lock = threading.Lock()  # Jobicy answers 403 to concurrent requests


def keys(search):
    return list(search.get("keywords") or [])


def fetch(keyword, search):
    with _lock:
        data = http.get_json("https://jobicy.com/api/v2/remote-jobs", {"count": 50, "tag": keyword})
        time.sleep(2)
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
            tags=(j.get("jobIndustry") or []) + (j.get("jobType") or []),
        ))
    return out


register(sys.modules[__name__])
