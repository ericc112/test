"""Oracle Recruiting Cloud career sites ({host}.oraclecloud.com/hcmUI/CandidateExperience/.../sites/{site}).

Banks, insurers, manufacturers and retailers (JPMorgan Chase among them). Reads the same
public JSON the employer's careers page loads. Like Workday, these sites have you sign in
with the employer, so JobBot alerts you and links to the posting instead of filling it.

A board key is "host|site", e.g. "jpmc.fa.oraclecloud.com|CX_1001".
"""
import re
import sys

from .. import fields, scoring
from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register, suggested_names

NAME = "oracle"
LABEL = "Oracle career sites"
EMPLOYER = True
INCREMENTAL = True
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60
PAGE = 25
PAGES = 4  # intern feeds: the 100 best matches for "intern"; others: the newest 100 postings
DETAIL_LIMIT = 15

URL_RE = re.compile(r"https?://([\w.-]+\.oraclecloud\.com)/hcmUI/CandidateExperience/[a-z]{2}(?:-[A-Z]{2})?/sites/([\w]+)", re.I)
NAMES = suggested_names(NAME, lambda slug: slug.split("|")[0])
_looked_at = set()


def keys(search):
    wanted = fields.wanted_types(search)
    out = []
    for k in search.get("companies", {}).get(NAME, []):
        if k.count("|") != 1:
            continue
        if "full_time" in wanted:
            out.append(k)
        if "internship" in wanted:
            out.append(f"{k}#intern")
    return out


def parse_key(key):
    host, site = key.split("#")[0].split("|")
    return host, site


def key_from_url(url):
    m = URL_RE.match(url or "")
    return f"{m.group(1).lower()}|{m.group(2)}" if m else None


def id_prefix(key):
    return f"{NAME}:{parse_key(key)[0].split('.')[0]}:"


def company_name(key):
    host = parse_key(key)[0]
    return NAMES.get(host) or display_name(host.split(".")[0])


def _search(host, site, keyword="", offset=0, limit=PAGE):
    finder = f"findReqs;siteNumber={site},limit={limit},offset={offset},sortBy=" + ("RELEVANCY" if keyword else "POSTING_DATES_DESC")
    if keyword:
        finder += f',keyword="{keyword}"'
    data = http.get_json(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitions",
                         {"onlyData": "true", "expand": "requisitionList.secondaryLocations", "finder": finder})
    item = (data.get("items") or [{}])[0]
    return item.get("TotalJobsCount") or 0, item.get("requisitionList") or []


def probe(key):
    try:
        total, _ = _search(*parse_key(key), limit=1)
        return total > 0
    except (http.FetchError, ValueError, KeyError):
        return False


def _details(host, site, req_id):
    data = http.get_json(f"https://{host}/hcmRestApi/resources/latest/recruitingCEJobRequisitionDetails",
                         {"onlyData": "true", "expand": "all", "finder": f'ById;Id="{req_id}",siteNumber={site}'}, retries=1)
    d = (data.get("items") or [{}])[0]
    parts = [d.get("ExternalDescriptionStr"), d.get("ExternalResponsibilitiesStr"), d.get("ExternalQualificationsStr"),
             d.get("CorporateDescriptionStr")]
    return html_to_text(" ".join(p for p in parts if p))


def fetch(key, search, known=None):
    known = known or set()
    host, site = parse_key(key)
    tenant = host.split(".")[0]
    name = company_name(key)
    intern = key.endswith("#intern")
    out, details_left = [], DETAIL_LIMIT
    for page in range(PAGES):
        _, reqs = _search(host, site, "intern" if intern else "", page * PAGE)
        unseen = 0
        for r in reqs:
            if not r.get("Title") or not r.get("Id"):
                continue
            locs = [r.get("PrimaryLocation")] + [s.get("Name") for s in r.get("secondaryLocations") or []]
            workplace = r.get("WorkplaceType") or ""
            job = make_job(
                NAME, f"{tenant}:{r['Id']}", r["Title"], name,
                f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{r['Id']}",
                ats="manual", location="; ".join(l for l in locs if l)[:200],
                remote="remote" in workplace.lower(), posted_at=iso(r.get("PostedDate")),
                description=r.get("ShortDescriptionStr") or "", tags=[t for t in (workplace,) if t],
            )
            if job["id"] in known:
                continue
            if job["id"] not in _looked_at:
                unseen += 1
                _looked_at.add(job["id"])
            if not scoring.relevant(job, search) or scoring.exclusion(job, search):
                continue
            if details_left > 0:
                details_left -= 1
                try:
                    job["description"] = _details(host, site, r["Id"]) or job["description"]
                except http.FetchError:
                    pass
            out.append(job)
        if len(reqs) < PAGE or (known and unseen == 0 and not intern):
            break  # newest first: a page with nothing new means we've caught up
    return out


register(sys.modules[__name__])
