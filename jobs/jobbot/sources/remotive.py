"""Remotive remote jobs (remotive.com/api). Their terms ask for at most ~4 calls a day."""
import re
import sys

from ..textutil import html_to_text
from . import http, iso, make_job, register

NAME = "remotive"
LABEL = "Remotive"
MIN_INTERVAL = 6 * 3600
FORCE_MIN_INTERVAL = 6 * 3600  # honoured even on "search now"


def keys(search):
    # Remotive's free feed returns the same recent jobs whatever you search for,
    # so one call per refresh covers it (and keeps us well inside their terms).
    return ["latest"]


def _salary(text):
    nums = [float(n) * (1000 if k else 1) for n, k in re.findall(r"(\d+(?:\.\d+)?)\s*([kK])?", text or "")]
    nums = [n for n in nums if n >= 1000]
    return (nums[0], nums[-1]) if nums else (None, None)


def fetch(keyword, search):
    data = http.get_json("https://remotive.com/api/remote-jobs")
    out = []
    for j in data.get("jobs", []):
        lo, hi = _salary(j.get("salary"))
        out.append(make_job(
            NAME, j["id"], j.get("title"), j.get("company_name"), j.get("url"),
            location=j.get("candidate_required_location") or "Remote", remote=True,
            description=html_to_text(j.get("description")), posted_at=iso(j.get("publication_date")),
            salary_text=j.get("salary") or None, salary_min=lo, salary_max=hi,
            tags=(j.get("tags") or [])[:12], categories=[j["category"]] if j.get("category") else [],
        ))
    return out


register(sys.modules[__name__])
