"""Your work history, read from your resume's text: each job's company, title, location, dates and bullets.

Application forms ask for every job again ("Work Experience 2: From, To"). The dates are in the resume, so the
answers come from there instead of from you. Resume PDFs often come out of the PDF reader one word per line; the
words are joined back up first.
"""
import re
from functools import lru_cache

_MONTH = (r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|"
          r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
_DATE = rf"(?:{_MONTH}\s+\d{{4}}|\d{{1,2}}/\d{{4}}|\d{{4}})"
RANGE = re.compile(rf"({_DATE})\s*(?:–|—|-|to|until|through)\s*({_DATE}|present|current|now|today)\b", re.I)
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

# Resume section headings, as written in capitals ("WORK EXPERIENCE", "LEADERSHIP & ACTIVITIES").
HEADING = re.compile(r"\b(PROFESSIONAL EXPERIENCE|WORK EXPERIENCE|RELEVANT EXPERIENCE|EXPERIENCE|EMPLOYMENT( HISTORY)?|"
                     r"LEADERSHIP( & ACTIVITIES| AND ACTIVITIES| EXPERIENCE)?|ACTIVITIES|INVOLVEMENT|VOLUNTEER(ING| EXPERIENCE)?|"
                     r"(ACADEMIC |PERSONAL |RELEVANT |SELECTED )?PROJECTS|EDUCATION|SKILLS( & INTERESTS| AND INTERESTS)?|CERTIFICATIONS?|AWARDS|HONORS)\b")
WORK = re.compile(r"EXPERIENCE|EMPLOYMENT")
ACTIVITY = re.compile(r"LEADERSHIP|ACTIVITIES|INVOLVEMENT|VOLUNTEER|PROJECTS")
ROLE_WORDS = re.compile(r"\b(intern|internship|co-?op|analyst|associate|assistant|manager|coordinator|specialist|consultant|"
                        r"engineer|developer|representative|lead|leader|director|president|officer|mentor|clerk|cashier|"
                        r"supervisor|administrator|advisor|tutor|volunteer|member|chair|founder|owner|technician|planner|buyer)\b", re.I)
LOCATION = re.compile(r"^(remote|[A-Z][A-Za-z .'-]+,\s*([A-Z]{2}|[A-Z][a-z]+))$")
BULLET = re.compile(r"\s*[●•▪◦■]\s*")


def _text(raw):
    """One line per line of the resume; a word-per-line PDF extraction is joined back into running text."""
    lines = [l.strip() for l in (raw or "").splitlines() if l.strip()]
    if lines and sum(len(l.split()) <= 1 for l in lines) > 0.6 * len(lines):
        return " ".join(lines)
    return "\n".join(lines)


def _when(s):
    s = s.strip().lower()
    if re.match(r"present|current|now|today", s):
        return None
    m = re.match(rf"({_MONTH})\s+(\d{{4}})", s)
    if m:
        return int(m.group(2)), MONTHS.index(m.group(1)[:3]) + 1
    m = re.match(r"(\d{1,2})/(\d{4})", s)
    if m:
        return int(m.group(2)), int(m.group(1))
    return int(s[:4]), None  # a year alone


def _header(before):
    """Company, title and location from the text just before a job's dates: "Acme | Analyst Intern | Houston, TX",
    "Analyst Intern, Acme, Houston, TX" or "Acme — Analyst Intern"."""
    tail = before[-220:]
    heads = list(HEADING.finditer(tail))
    if heads:
        tail = tail[heads[-1].end():]
    lines = [l.strip() for l in tail.split("\n") if l.strip()]
    if len(lines) > 1:  # a resume with real lines: the previous job's bullet lines aren't this one's name
        lines = [l for l in lines if not BULLET.match(l)]
    if not lines:
        return {}
    tail = " | ".join(lines[-2:]) if len(lines) >= 2 and len(lines[-1]) < 80 else lines[-1]
    parts = [p.strip(" ,;:-–—") for p in re.split(r"\s*\|\s*|\s+[–—]\s+", tail) if p.strip(" ,;:-–—")]
    if len(parts) < 2:  # "Analyst Intern, Acme, Houston, TX"
        parts = [p.strip() for p in tail.split(",") if p.strip()]
        if len(parts) >= 3 and re.fullmatch(r"[A-Z]{2}", parts[-1]):
            parts = parts[:-2] + [f"{parts[-2]}, {parts[-1]}"]
    if not parts:
        return {}
    # In running text, what comes before the first part is the end of the previous job's last bullet: the name is
    # the capitalized run at its end ("…supporting program operations Asian Business Student Association").
    parts[0] = re.split(r"[●•▪◦■]|\.\s+|%\s+|\)\s+", parts[0])[-1].strip()
    if re.search(r"\b[a-z]{3,}\b", parts[0]):
        run = re.search(r"((?:[A-Z0-9][\w.'&-]*|&|of|and|the|for|de)(?:\s+(?:[A-Z0-9][\w.'&-]*|&|of|and|the|for|de))*)$", parts[0])
        if run and re.match(r"[A-Z]", run.group(1)):
            parts[0] = run.group(1)
    out = {}
    if LOCATION.match(parts[-1]):
        out["location"] = parts.pop()
    titled = [p for p in parts if ROLE_WORDS.search(p)]
    title = titled[0] if titled else (parts[1] if len(parts) > 1 else "")
    rest = [p for p in parts if p != title]
    out["title"], out["company"] = title, (rest[0] if rest else "")
    return out


@lru_cache(maxsize=8)
def jobs(raw):
    """Jobs in the resume, in its order: work experience ("work") and leadership, activities or projects ("activity").
    Education's dates aren't jobs."""
    text = _text(raw)
    found, last = [], 0
    ranges = list(RANGE.finditer(text))
    for i, m in enumerate(ranges):
        before = text[last:m.start()]
        heads = [h.group(0) for h in HEADING.finditer(text[:m.start()])]
        section = heads[-1] if heads else ""
        nxt = ranges[i + 1].start() if i + 1 < len(ranges) else len(text)
        body = text[m.end():nxt]
        last = m.end()
        if section.startswith("EDUCATION"):
            continue
        head = _header(before)
        if not head.get("company") and not head.get("title"):
            continue
        bullets = [b.strip() for b in BULLET.split(body) if b.strip()]
        if bullets:  # the next job's name, or the next section, can trail this job's last bullet
            nxt_head = _header(body)
            names = [n for n in (nxt_head.get("company"), nxt_head.get("title")) if n and n in bullets[-1]]
            if names and i + 1 < len(ranges):
                bullets[-1] = bullets[-1][:min(bullets[-1].rfind(n) for n in names)].strip()
            heading = HEADING.search(bullets[-1])
            if heading:
                bullets[-1] = bullets[-1][:heading.start()].strip()
            if "\n" in bullets[-1] and i + 1 < len(ranges):  # a resume with real lines: the next job's own lines
                bullets[-1] = bullets[-1].split("\n")[0]
        start, end = _when(m.group(1)), _when(m.group(2))
        found.append({
            "company": head.get("company", ""), "title": head.get("title", ""), "location": head.get("location", ""),
            "start": start, "end": end, "current": end is None,
            "kind": "activity" if ACTIVITY.search(section) and not WORK.search(section) else "work",
            "description": "\n".join(b for b in bullets if len(b) > 15),
        })
    return tuple(found)


def ordered(raw):
    """Work experience first, then leadership and activities: the order forms list "Work Experience 1, 2, …" in."""
    js = list(jobs(raw or ""))
    return [j for j in js if j["kind"] == "work"] + [j for j in js if j["kind"] != "work"]
