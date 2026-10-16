"""Greenhouse company job boards (boards-api.greenhouse.io). Auto-apply supported.

Polling is incremental: the light job list (no descriptions) is fetched with an ETag,
so an unchanged board costs a 304. Descriptions are fetched only for jobs we haven't
seen that pass your filters; the first look at a board uses one bulk request instead.
"""
import sys

from .. import ats, scoring
from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register

NAME = "greenhouse"
LABEL = "Greenhouse boards"
EMPLOYER = True  # the employer's own applicant-tracking system: listings appear here first
INCREMENTAL = True
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60
DETAIL_LIMIT = 25  # more new jobs than this in one poll: fetch them all in one bulk call
API = "https://boards-api.greenhouse.io/v1/boards"


def keys(search):
    return list(search.get("companies", {}).get(NAME, []))


def id_prefix(board):
    return f"{NAME}:{board}:"


def probe(board):
    """True if a Greenhouse board with this token exists."""
    try:
        data = http.get_json(f"{API}/{board}/jobs", retries=0)
        return isinstance(data.get("jobs"), list)
    except http.FetchError:
        return False


VAGUE_LOCATION = ("hybrid", "remote", "in office", "in-office", "onsite", "on-site", "multiple locations", "flexible")


def _job(board, j):
    loc = (j.get("location") or {}).get("name") or ""
    offices = [o.get("name") for o in j.get("offices") or []
               if o.get("name") and o.get("name").lower() != "no office" and o.get("name").lower() not in loc.lower()]
    if offices and (loc.strip().lower() in VAGUE_LOCATION or "," not in loc):
        loc = f"{loc} · {'; '.join(offices[:3])}" if loc else "; ".join(offices[:3])  # "Hybrid" → where?
    job = make_job(
        NAME, f"{board}:{j['id']}", j.get("title"),
        j.get("company_name") or display_name(board),
        j.get("absolute_url"),
        apply_url=ats.form_url("greenhouse", board, j["id"]),
        ats="greenhouse", ats_board=board, ats_job_id=str(j["id"]),
        location=loc, remote="remote" in loc.lower(),
        posted_at=iso(j.get("first_published") or j.get("updated_at")),
    )
    if "content" in j:
        job["description"] = html_to_text(j.get("content"))
        job["categories"] = [d.get("name") for d in j.get("departments") or [] if d.get("name")]
    return job


def fetch(board, search, known=None):
    """Jobs on this board we haven't stored yet. Raises http.NotModified if nothing changed."""
    known = known or set()
    listing = http.get_json(f"{API}/{board}/jobs", conditional=True).get("jobs", [])
    new = [j for j in listing if f"{id_prefix(board)}{j['id']}" not in known]
    # Only spend a request on jobs that could pass your search (title, location, age).
    worth = [j for j in new if scoring.relevant(_job(board, j), search)
             and not scoring.exclusion(_job(board, j), search)]
    if not worth:
        return []
    if len(worth) > DETAIL_LIMIT:
        full = {j["id"]: j for j in http.get_json(f"{API}/{board}/jobs", {"content": "true"}).get("jobs", [])}
    else:
        full = {}
        for j in worth:
            try:
                full[j["id"]] = http.get_json(f"{API}/{board}/jobs/{j['id']}", retries=1)
            except http.FetchError:
                pass  # try again next poll
    return [_job(board, full[j["id"]]) for j in worth if j["id"] in full]


register(sys.modules[__name__])
