"""Remote OK (remoteok.com/api): latest remote jobs, filtered locally."""
import sys

from ..textutil import html_to_text
from . import http, iso, make_job, register

NAME = "remoteok"
LABEL = "Remote OK"
MIN_INTERVAL = 60 * 60
FORCE_MIN_INTERVAL = 10 * 60


def keys(search):
    return ["latest"]


def fetch(key, search):
    data = http.get_json("https://remoteok.com/api")
    out = []
    for j in data:
        if not isinstance(j, dict) or "id" not in j or not j.get("position"):
            continue
        lo, hi = j.get("salary_min") or None, j.get("salary_max") or None
        out.append(make_job(
            NAME, j["id"], j.get("position"), j.get("company"), j.get("url"),
            apply_url=j.get("apply_url") or j.get("url"),
            location=j.get("location") or "Remote", remote=True,
            description=html_to_text(j.get("description")),
            posted_at=iso(j.get("date") or j.get("epoch")),
            salary_min=lo, salary_max=hi,
            salary_text=f"${lo:,.0f} - ${hi:,.0f}" if lo and hi else None,
            tags=(j.get("tags") or [])[:12],
        ))
    return out


register(sys.modules[__name__])
