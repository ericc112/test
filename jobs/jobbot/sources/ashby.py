"""Ashby company job boards (api.ashbyhq.com posting API). Auto-apply supported."""
import re
import sys

from ..textutil import html_to_text
from . import display_name, http, iso, make_job, register

NAME = "ashby"
LABEL = "Ashby boards"
MIN_INTERVAL = 30 * 60
FORCE_MIN_INTERVAL = 2 * 60


def keys(search):
    return list(search.get("companies", {}).get(NAME, []))


def probe(org):
    try:
        data = http.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{org}", retries=0)
        return isinstance(data.get("jobs"), list)
    except http.FetchError:
        return False


def _money(s):
    m = re.match(r"\$?\s*([\d.,]+)\s*([kK])?", s.strip())
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return v * 1000 if m.group(2) else v


def fetch(org, search):
    data = http.get_json(
        f"https://api.ashbyhq.com/posting-api/job-board/{org}", {"includeCompensation": "true"}
    )
    out = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j.get("location") or ""] + [
            s.get("location", "") for s in j.get("secondaryLocations") or []
        ]
        comp = j.get("compensation") or {}
        stext = comp.get("scrapeableCompensationSalarySummary") or comp.get("compensationTierSummary")
        lo = hi = None
        if stext and "$" in stext:
            nums = [_money(p) for p in re.split(r"[-–]", stext)]
            nums = [n for n in nums if n]
            if nums:
                lo, hi = nums[0], nums[-1]
        out.append(make_job(
            NAME, f"{org}:{j['id']}", (j.get("title") or "").strip(), display_name(org),
            j.get("jobUrl"), apply_url=j.get("applyUrl"), ats="ashby", ats_board=org,
            ats_job_id=j["id"], location="; ".join(l for l in locs if l),
            remote=bool(j.get("isRemote")) or j.get("workplaceType") == "Remote",
            description=j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml")),
            posted_at=iso(j.get("publishedAt")), salary_min=lo, salary_max=hi, salary_text=stext,
            tags=[t for t in (j.get("employmentType"),) if t],
            categories=[t for t in (j.get("department"), j.get("team")) if t],
        ))
    return out


register(sys.modules[__name__])
