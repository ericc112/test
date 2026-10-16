"""Greenhouse company job boards (boards-api.greenhouse.io). Auto-apply supported."""
import sys

from .. import ats
from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register

NAME = "greenhouse"
LABEL = "Greenhouse boards"
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60


def keys(search):
    return list(search.get("companies", {}).get(NAME, []))


def probe(board):
    """True if a Greenhouse board with this token exists."""
    try:
        data = http.get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", retries=0)
        return isinstance(data.get("jobs"), list)
    except http.FetchError:
        return False


def fetch(board, search):
    data = http.get_json(
        f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", {"content": "true"}
    )
    out = []
    for j in data.get("jobs", []):
        loc = (j.get("location") or {}).get("name") or ""
        out.append(make_job(
            NAME, f"{board}:{j['id']}", j.get("title"),
            j.get("company_name") or display_name(board),
            j.get("absolute_url"),
            apply_url=ats.form_url("greenhouse", board, j["id"]),
            ats="greenhouse", ats_board=board, ats_job_id=str(j["id"]),
            location=loc, remote="remote" in loc.lower(),
            description=html_to_text(j.get("content")),
            posted_at=iso(j.get("first_published") or j.get("updated_at")),
            categories=[d.get("name") for d in j.get("departments") or [] if d.get("name")],
        ))
    return out


register(sys.modules[__name__])
