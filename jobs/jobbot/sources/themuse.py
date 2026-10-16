"""The Muse (themuse.com/api/public/jobs): large US/global board, filtered locally."""
import sys

from .. import fields
from ..textutil import html_to_text
from . import http, iso, make_job, register

NAME = "themuse"
LABEL = "The Muse"
MIN_INTERVAL = 60 * 60
FORCE_MIN_INTERVAL = 10 * 60
PAGES = 5


def keys(search):
    locs = [l for l in search.get("locations") or [] if l.strip()]
    mapped = ["Flexible / Remote" if l.strip().lower() == "remote" else l for l in locs]
    return mapped or ["Flexible / Remote"]


def fetch(location, search):
    out = []
    for page in range(PAGES):
        params = {"page": page, "descending": "true", "location": location}
        if search.get("field"):
            params["category"] = fields.source_terms(search, "muse")
        data = http.get_json("https://www.themuse.com/api/public/jobs", params)
        for j in data.get("results", []):
            locs = [l.get("name", "") for l in j.get("locations") or []]
            out.append(make_job(
                NAME, j["id"], j.get("name"), (j.get("company") or {}).get("name"),
                (j.get("refs") or {}).get("landing_page"),
                location="; ".join(locs), remote=any("remote" in l.lower() for l in locs),
                description=html_to_text(j.get("contents")), posted_at=iso(j.get("publication_date")),
                tags=[lv.get("name") for lv in j.get("levels") or []],
                categories=[c.get("name") for c in j.get("categories") or []],
            ))
        if page + 1 >= data.get("page_count", 0):
            break
    return out


register(sys.modules[__name__])
