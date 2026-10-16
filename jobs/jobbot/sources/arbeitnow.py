"""Arbeitnow (arbeitnow.com/api/job-board-api): mostly Europe/Germany, filtered locally."""
import sys

from ..textutil import html_to_text
from . import http, iso, make_job, register

NAME = "arbeitnow"
LABEL = "Arbeitnow"
MIN_INTERVAL = 60 * 60
FORCE_MIN_INTERVAL = 10 * 60
PAGES = 3


def keys(search):
    return ["latest"]


def fetch(key, search):
    out = []
    for page in range(1, PAGES + 1):
        data = http.get_json("https://www.arbeitnow.com/api/job-board-api", {"page": page})
        for j in data.get("data", []):
            out.append(make_job(
                NAME, j["slug"], j.get("title"), j.get("company_name"), j.get("url"),
                location=j.get("location") or "", remote=bool(j.get("remote")),
                description=html_to_text(j.get("description")), posted_at=iso(j.get("created_at")),
                tags=j.get("job_types") or [], categories=j.get("tags") or [],
            ))
        if not (data.get("links") or {}).get("next"):
            break
    return out


register(sys.modules[__name__])
