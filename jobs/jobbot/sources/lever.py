"""Lever company job boards (api.lever.co). Auto-apply supported."""
import sys

from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register

NAME = "lever"
LABEL = "Lever boards"
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60


def keys(search):
    return list(search.get("companies", {}).get(NAME, []))


def probe(site):
    try:
        data = http.get_json(f"https://api.lever.co/v0/postings/{site}", {"mode": "json", "limit": 1}, retries=0)
        return isinstance(data, list)
    except http.FetchError:
        return False


def _salary(j):
    s = j.get("salaryRange") or {}
    lo, hi = s.get("min"), s.get("max")
    if not (lo or hi):
        return None, None, None
    cur = s.get("currency") or ""
    text = f"{cur} {lo or ''}-{hi or ''} {s.get('interval') or ''}".strip()
    if (s.get("interval") or "").startswith("per-year") or not s.get("interval"):
        return lo, hi, text
    return None, None, text


def fetch(site, search):
    data = http.get_json(f"https://api.lever.co/v0/postings/{site}", {"mode": "json"})
    out = []
    for j in data:
        cat = j.get("categories") or {}
        loc = cat.get("location") or ", ".join(cat.get("allLocations") or [])
        parts = [j.get("descriptionPlain") or html_to_text(j.get("description"))]
        for lst in j.get("lists") or []:
            parts.append(lst.get("text", ""))
            parts.append(html_to_text(lst.get("content")))
        parts.append(j.get("additionalPlain") or "")
        lo, hi, stext = _salary(j)
        out.append(make_job(
            NAME, f"{site}:{j['id']}", j.get("text"), display_name(site), j.get("hostedUrl"),
            apply_url=j.get("applyUrl"), ats="lever", ats_board=site, ats_job_id=j["id"],
            location=loc,
            remote=(j.get("workplaceType") == "remote") or "remote" in loc.lower(),
            description="\n".join(p for p in parts if p).strip(),
            posted_at=iso(j.get("createdAt")),
            salary_min=lo, salary_max=hi, salary_text=stext,
            tags=[t for t in (cat.get("commitment"), j.get("workplaceType")) if t],
            categories=[t for t in (cat.get("department"), cat.get("team")) if t],
        ))
    return out


register(sys.modules[__name__])
