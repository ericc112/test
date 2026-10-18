"""Find a job you saw on LinkedIn, Indeed or another job board on the employer's own careers site.

Job boards copy employers' postings, and their Apply buttons either sign you in to the board (LinkedIn's Easy
Apply, Indeed Apply) or hide the employer's link from visitors who aren't signed in. So JobBot reads the posting's
title, company and location, and looks for the same job where the employer posts it: the job systems it already
knows for that company, the company's own careers page, and the Greenhouse, Lever, Ashby and Workable boards
under the company's name.
"""
import html
import json
import re
import time
import urllib.parse

from . import config
from .sources import company_key, http
from .textutil import norm, similarity

LINKEDIN_ID = re.compile(r"linkedin\.com/jobs/view/(?:[^/?#]*-)?(\d{6,})|linkedin\.com/.*[?&]currentJobId=(\d{6,})", re.I)
# Job boards that copy employers' postings: never where the employer's own posting is.
BOARDS = re.compile(r"(^|\.)(linkedin|indeed|glassdoor|ziprecruiter|monster|dice|simplyhired|wellfound|angel|joinhandshake|"
                    r"careerbuilder|joinrunway|google|facebook|twitter|x|instagram|youtube)\.", re.I)
MATCH = 0.86  # how alike two titles must be to count as the same job (exact matches win outright)
BUDGET = 60  # seconds one search may take


# ---------------------------------------------------------------- the posting on the job board
def _text(fragment):
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", fragment or "").split()))


def details(url):
    """{"title", "company", "location", "website"} from a job board's posting, or None if it can't be read."""
    m = LINKEDIN_ID.search(url or "")
    if m:
        try:
            _, page = http.get_html(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{m.group(1) or m.group(2)}")
        except http.FetchError:
            return None
        grab = lambda rx: _text((re.search(rx, page, re.S) or [None, ""])[1])  # noqa: E731
        found = {"title": grab(r'<h2[^>]*top-card-layout__title[^>]*>(.*?)</h2>'),
                 "company": grab(r'<a[^>]*topcard__org-name-link[^>]*>(.*?)</a>'),
                 "location": grab(r'<span[^>]*topcard__flavor--bullet[^>]*>(.*?)</span>'), "website": ""}
        return found if found["title"] and found["company"] else None
    try:
        _, page = http.get_html(url)
    except http.FetchError:
        return None  # Indeed and Glassdoor turn scripted visits away
    for block in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page, re.S):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        for item in data if isinstance(data, list) else data.get("@graph", [data]):
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                org = item.get("hiringOrganization") or {}
                place = item.get("jobLocation") or {}
                place = (place[0] if isinstance(place, list) and place else place) or {}
                addr = place.get("address") or {} if isinstance(place, dict) else {}
                return {"title": _text(item.get("title")), "company": _text(org.get("name") if isinstance(org, dict) else org),
                        "location": ", ".join(x for x in (addr.get("addressLocality"), addr.get("addressRegion")) if x)
                        if isinstance(addr, dict) else "",
                        "website": _own_site((org.get("sameAs") or org.get("url") or "") if isinstance(org, dict) else "")}
    return None


def _own_site(url):
    url = url if isinstance(url, str) else ""
    return "" if BOARDS.search(urllib.parse.urlparse(url).netloc) else url


# ---------------------------------------------------------------- where the employer posts jobs
ATS_LINK = re.compile(
    r"https?://(?:[\w-]+\.wd\d+\.myworkdayjobs\.com/[^\"'\s<>\\]+|(?:job-boards|boards)(?:\.eu)?\.greenhouse\.io/[\w-]+|"
    r"jobs(?:\.eu)?\.lever\.co/[\w.-]+|jobs\.ashbyhq\.com/[^/\"'\s<>\\]+|apply\.workable\.com/[\w-]+|[\w-]+\.workable\.com|"
    r"(?:jobs|careers)\.smartrecruiters\.com/[\w-]+|[\w-]+\.tbe\.taleo\.net/[^\"'\s<>\\]+|[\w-]+\.icims\.com[^\"'\s<>\\]*|"
    r"[\w.-]+\.(?:paylocity|ultipro|ukg|adp|jobvite|bamboohr|applytojob|breezy|dayforcehcm|recruitee|jazzhr|rippling)"
    r"\.(?:com|net|hr|io)[^\"'\s<>\\]*)", re.I)
CAREERS_LINK = re.compile(r"\bcareers?\b|\bjobs\b|join (us|our team)|work (with|for|at) us|opportunities", re.I)


def boards(company, website=""):
    """Places to look for this company's postings, as (kind, ref), cheapest first: the job systems JobBot knows
    for it, boards under its name, then whatever its careers site links to. A generator: the search stops at a match."""
    from .sources import REGISTRY
    from .sources import workday as _wd  # noqa: F401  (registers the source)
    seen, key = set(), company_key(company)

    def fresh(board):
        if board and board not in seen:
            seen.add(board)
            return True
        return False

    for name, kind, slug in config.SUGGESTED_COMPANIES:
        if company_key(name) == key and kind in ("workday", "greenhouse", "lever", "ashby") and fresh((kind, slug.split("#")[0])):
            yield kind, slug.split("#")[0]
    for slug in _slugs(company)[:2]:
        for kind in ("greenhouse", "lever", "ashby"):  # not Workable: it turns away guessed names (HTTP 429)
            if fresh((kind, slug)):
                yield kind, slug
    for page_url in _careers_pages(company, website):
        links = [page_url] if ATS_LINK.match(page_url) else []
        if not links and fresh(("page", page_url)):
            yield "page", page_url
        try:
            final, body = http.get_html(page_url, timeout=12)
        except http.FetchError:
            body, final = "", page_url
        links += [m.rstrip(".,);&") for m in ATS_LINK.findall(html.unescape(body))]
        for link in dict.fromkeys(links):
            if STATIC.search(link):
                continue
            board = _board(link, REGISTRY)
            if fresh(board):
                yield board
        if re.search(r'action="/search/?"', body) and re.search(r'name="q"', body):  # a SuccessFactors careers site
            board = ("search", urllib.parse.urljoin(final, "/search/"))
            if fresh(board):
                yield board


STATIC = re.compile(r"\.(css|js|png|jpe?g|gif|svg|ico|woff2?|ttf|pdf)(\?|$)|//static", re.I)


def _board(link, registry):
    host = urllib.parse.urlparse(link).netloc.lower()
    if "myworkdayjobs.com" in host:
        k = registry["workday"].key_from_url(link)
        return ("workday", k) if k else None
    m = re.search(r"greenhouse\.io/(?:embed/job_board\?for=)?([\w-]+)", link)
    if m:
        return ("greenhouse", m.group(1))
    m = re.search(r"lever\.co/([\w.-]+)", link) or re.search(r"ashbyhq\.com/([^/?#]+)", link)
    if m:
        return ("lever" if "lever.co" in link else "ashby", m.group(1))
    m = re.search(r"apply\.workable\.com/([\w-]+)", link) or re.match(r"https?://([\w-]+)\.workable\.com", link)
    if m and m.group(1) not in ("www", "apply"):
        return ("workable", m.group(1))
    m = re.search(r"smartrecruiters\.com/([\w-]+)", link)
    if m:
        return ("smartrecruiters", m.group(1))
    m = re.match(r"(https?://[\w-]+\.tbe\.taleo\.net/[\w-]+)/ats/", link)
    if m:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
        return ("taleo", f"{m.group(1)}|{q['org'][0]}|{q.get('cws', ['1'])[0]}") if q.get("org") else None
    if host.endswith(".icims.com"):
        return ("icims", f"https://{host}")
    return ("page", link)


def _careers_pages(company, website=""):
    """The company's careers pages, found from its website (given, or guessed from its name)."""
    sites = [website] if _own_site(website).startswith("http") else []
    sites += [f"https://www.{slug}.com" for slug in _slugs(company)[:2]]
    for site in sites:
        try:
            final, body = http.get_html(site, timeout=12)
        except http.FetchError:
            continue
        pages = []
        for href, text in re.findall(r'<a[^>]+href="([^"#][^"]*)"[^>]*>(.*?)</a>', body, re.S)[:800]:
            href = html.unescape(href)
            if ATS_LINK.match(href) or CAREERS_LINK.search(_text(text)) or re.search(r"/careers?\b|/jobs\b", href):
                pages.append(urllib.parse.urljoin(final, href))
        pages = list(dict.fromkeys(p for p in pages if p.startswith("http") and _own_site(p)))
        return [p for p in pages if ATS_LINK.match(p)][:3] + [p for p in pages if not ATS_LINK.match(p)][:3]
    return []


def _slugs(company):
    words = re.findall(r"[a-z0-9]+", norm(re.sub(r"\b(inc|llc|ltd|corp|corporation|co|company|group|holdings)\b\.?", "",
                                                 (company or "").lower())))
    return list(dict.fromkeys(s for s in ("".join(words), "-".join(words), words[0] if words else "") if s))


# ---------------------------------------------------------------- searching each kind of board
def _search(kind, ref, title, retries=1):
    """[(title, url, location)] for postings on one board that could be this job."""
    if kind == "workday":
        from .sources import workday as wd
        base, api = wd._api(ref)
        site = wd.parse_key(ref)[2]
        data = http.post_json(f"{api}/jobs", {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": title}, retries=retries)
        return [(p.get("title") or "", f"{base}/{site}{p['externalPath']}", p.get("locationsText") or "")
                for p in data.get("jobPostings") or [] if p.get("externalPath")]
    if kind == "greenhouse":
        data = http.get_json(f"https://boards-api.greenhouse.io/v1/boards/{ref}/jobs", retries=retries)
        return [(j.get("title") or "", j.get("absolute_url") or "", (j.get("location") or {}).get("name") or "")
                for j in data.get("jobs") or []]
    if kind == "lever":
        data = http.get_json(f"https://api.lever.co/v0/postings/{ref}", {"mode": "json"}, retries=retries)
        return [(j.get("text") or "", j.get("hostedUrl") or "", (j.get("categories") or {}).get("location") or "")
                for j in data or []]
    if kind == "ashby":
        data = http.get_json(f"https://api.ashbyhq.com/posting-api/job-board/{ref}", retries=retries)
        return [(j.get("title") or "", j.get("jobUrl") or "", j.get("location") or "") for j in data.get("jobs") or []]
    if kind == "workable":
        data = http.get_json(f"https://apply.workable.com/api/v1/widget/accounts/{ref}", retries=retries)
        return [(j.get("title") or "", j.get("url") or j.get("shortlink") or "",
                 ", ".join(x for x in (j.get("city"), j.get("state")) if x)) for j in data.get("jobs") or []]
    if kind == "smartrecruiters":
        data = http.get_json(f"https://api.smartrecruiters.com/v1/companies/{ref}/postings", {"q": title}, retries=retries)
        return [(j.get("name") or "", f"https://jobs.smartrecruiters.com/{ref}/{j.get('id')}",
                 (j.get("location") or {}).get("city") or "") for j in data.get("content") or []]
    if kind == "taleo":  # Taleo Business Edition lists every opening in an RSS feed
        root, org, cws = ref.split("|")
        _, feed = http.get_html(f"{root}/ats/servlet/Rss?org={org}&cws={cws}")
        out = []
        for item in re.findall(r"<item>(.*?)</item>", feed, re.S):
            name = _text((re.search(r"<title>(.*?)</title>", item, re.S) or [None, ""])[1])
            rid = re.search(r"rid=(\d+)", item)
            if name and rid:
                out.append((name, f"{root}/ats/careers/v2/viewRequisition?org={org}&cws={cws}&rid={rid.group(1)}", ""))
        return out
    if kind == "icims":
        return _links(f"{ref}/jobs/search?" + urllib.parse.urlencode({"ss": 1, "searchKeyword": title, "in_iframe": 1}),
                      r"/jobs/\d+/")
    if kind == "search":
        return _links(f"{ref}?" + urllib.parse.urlencode({"q": title}), r"/job/")
    return _links(ref)


def _links(url, must=""):
    """Job-looking links on a listing page: [(text, url, "")]."""
    final, body = http.get_html(url)
    out = []
    for href, text in re.findall(r'<a[^>]+href="([^"#][^"]*)"[^>]*>(.*?)</a>', body, re.S):
        href, text = html.unescape(href), _text(text)
        if 4 <= len(text) <= 150 and (not must or re.search(must, href)) and _own_site(urllib.parse.urljoin(final, href)):
            out.append((text, urllib.parse.urljoin(final, href), ""))
    return out


def _best(hits, title, location=""):
    """The posting that is this job: an exact title wins (the one in this city if several), else a near-identical title."""
    city = norm(location.split(",")[0]) if location else ""
    want = norm(title)
    scored = []
    for text, url, where in hits:
        if not url:
            continue
        have = norm(text)
        score = 1.0 if have == want else similarity(text, title)
        if len(want) >= 12 and have.startswith(want) and re.match(r"^[\s,(-]+[a-z .]+(,\s*[a-z .]+)?\)?$", have[len(want):]):
            score = max(score, 0.95)  # the same title with a location after it: "... - Houston, TX"
        if city and (city in norm(where) or city in norm(text)):
            score += 0.05
        scored.append((score, url))
    scored.sort(reverse=True)
    return scored[0][1] if scored and scored[0][0] >= MATCH else None


def find(title, company, location="", website=""):
    """The employer's own posting of this job, or None."""
    if not title or not company:
        return None
    start = time.time()
    guessed = {(kind, slug) for slug in _slugs(company)[:2] for kind in ("greenhouse", "lever", "ashby")}
    for kind, ref in boards(company, website):
        if time.time() - start > BUDGET:
            break
        try:
            hit = _best(_search(kind, ref, title, retries=0 if (kind, ref) in guessed else 1), title, location)
        except (http.FetchError, ValueError, KeyError, TypeError, AttributeError):
            continue
        if hit:
            return hit
    return None
