"""Recognise applicant-tracking systems (ATS) and find a job's real application form."""
import re
import urllib.parse
from html.parser import HTMLParser

from .sources import http

# Forms JobBot knows how to fill and submit end to end.
SUPPORTED = ("greenhouse", "lever", "ashby")

# Sites that need an account or block automation. JobBot links you there instead.
LOGIN_WALLED = re.compile(
    r"linkedin\.com|indeed\.com|myworkdayjobs\.com|workday\.com|icims\.com|taleo\.net|"
    r"successfactors|glassdoor\.|ziprecruiter\.com|monster\.com|dice\.com|wellfound\.com|"
    r"angel\.co|upwork\.com|oraclecloud\.com",
    re.I,
)

_ATS_IN_HTML = re.compile(
    r"https?://(?:job-boards|boards)(?:\.eu)?\.greenhouse\.io/[^\"'\s<>\\]+|"
    r"https?://jobs(?:\.eu)?\.lever\.co/[^\"'\s<>\\]+|"
    r"https?://jobs\.ashbyhq\.com/[^\"'\s<>\\]+",
    re.I,
)


def detect(url):
    """Return (ats, board, job_id, host) for Greenhouse/Lever/Ashby URLs, else Nones."""
    none = (None, None, None, None)
    if not url:
        return none
    try:
        u = urllib.parse.urlparse(url.replace("&amp;", "&"))
    except ValueError:
        return none
    host, path = u.netloc.lower(), u.path
    qs = urllib.parse.parse_qs(u.query)
    if host.endswith("greenhouse.io"):
        if "for" in qs and "token" in qs:
            return "greenhouse", qs["for"][0], qs["token"][0], host
        m = re.match(r"^/([\w-]+)/jobs/(\d+)", path)
        if m:
            return "greenhouse", m.group(1), m.group(2), host
    if host in ("jobs.lever.co", "jobs.eu.lever.co"):
        m = re.match(r"^/([\w.-]+)/([0-9a-f-]{36})", path)
        if m:
            return "lever", m.group(1), m.group(2), host
    if host == "jobs.ashbyhq.com":
        m = re.match(r"^/([^/]+)/([0-9a-f-]{36})", path)
        if m:
            return "ashby", urllib.parse.unquote(m.group(1)), m.group(2), host
    return none


def form_url(ats, board, job_id, host=None):
    """URL of the hosted application form."""
    if ats == "greenhouse":
        base = "job-boards.eu.greenhouse.io" if host and ".eu." in host else "job-boards.greenhouse.io"
        return f"https://{base}/embed/job_app?for={urllib.parse.quote(board)}&token={job_id}"
    if ats == "lever":
        return f"https://{host or 'jobs.lever.co'}/{board}/{job_id}/apply"
    if ats == "ashby":
        return f"https://jobs.ashbyhq.com/{urllib.parse.quote(board)}/{job_id}/application"
    return None


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def _classify(url):
    ats, board, job_id, host = detect(url)
    if ats:
        return {"ats": ats, "ats_board": board, "ats_job_id": job_id,
                "apply_url": form_url(ats, board, job_id, host)}
    if LOGIN_WALLED.search(url or ""):
        return {"ats": "manual", "apply_url": url}
    return None


def resolve(job):
    """Work out where a job is actually applied to.

    Returns a dict of job fields to update: ats is one of SUPPORTED, "generic"
    (an unknown web form JobBot can try to fill but you should review), or
    "manual" (account required or no form found).
    """
    for u in (job.get("apply_url"), job.get("url")):
        hit = _classify(u)
        if hit:
            return hit
    page = job.get("apply_url") or job.get("url")
    if not page:
        return {"ats": "manual"}
    try:
        final, body = http.get_html(page)
    except http.FetchError:
        return {"ats": "generic", "apply_url": page}
    hit = _classify(final)
    if hit:
        return hit
    for m in _ATS_IN_HTML.findall(body):
        hit = _classify(m.rstrip(".,);"))
        if hit and hit["ats"] in SUPPORTED:
            return hit
    parser = _Links()
    try:
        parser.feed(body)
    except Exception:  # malformed HTML: keep whatever links were parsed
        pass
    page_host = urllib.parse.urlparse(final).netloc
    candidates = []
    for href, text in parser.links:
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue
        t = text.lower()
        if not re.search(r"\bapply\b", t) or "blog" in href:
            continue
        candidates.append(urllib.parse.urljoin(final, href))
    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        if len(seen) > 3:
            break
        try:
            target, _ = http.get_html(c)
        except http.FetchError:
            target = c
        hit = _classify(target)
        if hit:
            return hit
        if urllib.parse.urlparse(target).netloc != page_host:
            return {"ats": "generic", "apply_url": target}
    return {"ats": "generic", "apply_url": page}
