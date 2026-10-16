"""Himalayas remote jobs (himalayas.app/jobs/api/search)."""
import sys

from .. import fields
from ..textutil import html_to_text
from . import http, iso, make_job, register

NAME = "himalayas"
LABEL = "Himalayas"
MIN_INTERVAL = 60 * 60
FORCE_MIN_INTERVAL = 10 * 60
PAGES = 2


def _job_key(j):
    link = (j.get("guid") or j.get("applicationLink") or "").rstrip("/")
    return f"{j.get('companySlug') or 'job'}:{link.rsplit('/', 1)[-1]}"


def keys(search):
    wanted = fields.wanted_types(search)
    if search.get("keywords"):
        base = list(search["keywords"])
        return ([f"{k} intern" for k in base] if "internship" in wanted else []) + (base if "full_time" in wanted else [])
    if not search.get("field"):
        return ["intern", "internship"] if "internship" in wanted else []
    return ((fields.source_terms(search, "intern_search") if "internship" in wanted else [])
            + (fields.source_terms(search, "search") if "full_time" in wanted else []))


def fetch(keyword, search):
    out = []
    for page in range(PAGES):
        data = http.get_json(
            "https://himalayas.app/jobs/api/search", {"q": keyword, "page": page + 1}
        )
        jobs = data.get("jobs") or []
        for j in jobs:
            annual = (j.get("salaryPeriod") or "annual") in ("annual", "yearly")
            lo, hi = j.get("minSalary"), j.get("maxSalary")
            out.append(make_job(
                NAME, _job_key(j), j.get("title"),
                j.get("companyName"), j.get("applicationLink") or j.get("guid"),
                location=", ".join(j.get("locationRestrictions") or []) or "Remote", remote=True,
                description=html_to_text(j.get("description")) or j.get("excerpt"),
                posted_at=iso(j.get("pubDate")),
                salary_min=lo if annual else None, salary_max=hi if annual else None,
                salary_text=f"{j.get('currency') or ''} {lo}-{hi}".strip() if lo else None,
                tags=[t for t in [j.get("employmentType")] + (j.get("seniority") or [])[:4] if t],
                categories=(j.get("parentCategories") or []) + (j.get("categories") or [])[:8],
            ))
        if len(jobs) < 20:
            break
    return out


register(sys.modules[__name__])
