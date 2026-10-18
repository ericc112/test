"""Job listings read from what you saw on a job board.

Screenshots, a screen recording, a PDF or copied text from Runway, LinkedIn, Handshake or any other
board. JobBot reads the text itself (OCR on this computer, no AI), splits it into listings (title,
company, location, when it was posted and the board's own match score), keeps the business roles at
or above a minimum score and looks for each one on the employer's own careers site.
"""
import glob
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from . import ats, fields, finder, places
from .textutil import norm

IMAGES = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")
VIDEOS = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi")
TEXTS = (".txt", ".csv", ".tsv", ".md")
PAGES = (".html", ".htm")
MAX_FRAMES = 240  # four minutes of recording at one still a second
MIN_CONFIDENCE = 0.5
LOOKUP_BUDGET = 25  # seconds to look one job up on its employer's site (a listing JobBot misread can't be found anyway)

TITLE_WORD = re.compile(
    r"\b(intern(ship)?s?|co-?op|analyst|associate|coordinator|assistant|specialist|trainee|apprentice(ship)?|"
    r"fellow(ship)?|program(me)?|rotational|graduate|engineer|manager|representative|consultant|planner|buyer|"
    r"scientist|developer|designer|accountant|auditor|advisor|administrator|officer|strategist|director|"
    r"technician|clerk|recruiter|scholar|leadership development)\b", re.I)
HEADER = re.compile(r"^(role|roles|title|job|jobs|position|company|location|date|posted|match( score)?|score|save|"
                    r"apply|status|internships?|jobs for you|recommended( for you)?)$", re.I)
SCORE = re.compile(r"^(?:match(?:\s*score)?\s*:?\s*)?(\d{1,3})\s?%(?:\s*match)?$|^(?:match(?:\s*score)?\s*:?\s*)(\d{1,3})$"
                   r"|^(\d{1,3})$", re.I)
POSTED = re.compile(
    r"^(?:posted\s*:?\s*|reposted\s*)?(?:\d+\+?\s*(?:s|sec|secs|seconds?|m|min|mins|minutes?|h|hr|hrs|hours?|d|days?|w|wk|wks|"
    r"weeks?|mo|mos|months?)\s*ago|today|yesterday|just now|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:,?\s*\d{4})?|\d{1,2}/\d{1,2}(?:/\d{2,4})?)$",
    re.I)
NOISE = re.compile(r"^(save|saved|apply|apply now|easy apply|quick apply|applied|promoted|new|viewed|actively recruiting|"
                   r"be an early applicant|see more|show more|full[- ]time|part[- ]time|internship|contract|temporary|"
                   r"entry[- ]level|\W*)$|\$\s?\d|/\s?(hr|hour|yr|year)\b|alumni work|connections? works? here|"
                   r"early applicant|reviewing applicants|job search alert|posted in the past|past 24 hours|\bbenefits?\b|"
                   r"401\(k\)|\b(medical|dental|vision)\b|^(on|off|in)$", re.I)  # "in": the LinkedIn logo
CONTINUES = re.compile(r"(?:[-–—&,/]|\b(?:and|of|for|to|in|the|with|&))\s*$", re.I)  # a title wrapped onto a second line
LOCATION = re.compile(
    r"^(?i:remote|hybrid|on-?site|in-?office|united states|usa)\b|"
    r"^[A-Z][A-Za-z.'\- ]*,\s?(?:(?:" + "|".join(sorted(places.STATE_CODES)) + r")\b|(?i:" + places._STATE_NAMES + r")\b|"
    r"(?:Canada|Mexico|United Kingdom|UK|India|Germany|France|Ireland|Singapore|Japan|China|Brazil|Australia)\b)|"
    r"(?i:\((?:remote|hybrid|on-?site)\))$")
SEP = re.compile(r"\s*(?:·|•|\||—|–|\s-\s|\s\.\s|\s:|:\s)\s*")  # OCR sometimes reads "·" as "." or ":"
SENTENCE = re.compile(r"[.!?]$")


class ReadError(Exception):
    """An upload JobBot can't read, with a message for the owner."""


@dataclass
class Line:
    """A piece of text and where it sits on the screen (pixels; for copied text, one row per line)."""
    text: str
    x: float
    y: float
    h: float


# ------------------------------------------------------------------ reading

_ENGINE = None


def _engine():
    global _ENGINE
    if _ENGINE is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as e:
            raise ReadError("JobBot's text reader isn't installed here: pip install -r requirements-ocr.txt") from e
        _ENGINE = RapidOCR()
    return _ENGINE


def ocr(image):
    """The text in a screenshot, as Lines."""
    result, _ = _engine()(image)
    lines = []
    for box, text, conf in result or []:
        text = _clean(str(text))
        if not text or float(conf) < MIN_CONFIDENCE:
            continue
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        lines.append(Line(text, min(xs), min(ys), max(ys) - min(ys)))
    return lines


def _clean(text):
    """Text without icons OCR reads as characters (a verified badge comes out as "①")."""
    return " ".join("".join(ch for ch in text if unicodedata.category(ch) not in ("So", "No", "Co", "Cn")).split())


def text_lines(text):
    """Copied text: one Line per line of text."""
    rows = [" ".join(t.split()) for t in (text or "").splitlines()]
    return [Line(t, 0, i * 10.0, 10.0) for i, t in enumerate(r for r in rows if r)]


def frames(video, out_dir, per_second=1):
    """Stills from a screen recording: one a second, minus the ones that repeat the last (a pause in scrolling)."""
    if not shutil.which("ffmpeg"):
        raise ReadError("JobBot can't read videos here (ffmpeg isn't installed). Upload screenshots instead.")
    pattern = os.path.join(out_dir, "frame-%04d.png")
    try:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", video, "-vf", f"fps={per_second},mpdecimate,scale='min(1280,iw)':-2",
                        "-fps_mode", "vfr", "-frames:v", str(MAX_FRAMES), pattern], check=True, timeout=300,
                       capture_output=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        raise ReadError("JobBot couldn't open that video. Record it again, or upload screenshots.") from e
    return sorted(glob.glob(os.path.join(out_dir, "frame-*.png")))


def _pdf_text(path):
    from pypdf import PdfReader
    text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if not text.strip():
        raise ReadError("That PDF is a picture with no text in it. Upload screenshots instead.")
    return text


def _page_text(html_text):
    """A saved web page: its visible text, one block per line, and its links."""
    body = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html_text)
    links = [{"t": finder._text(t), "u": u} for u, t in re.findall(r'(?is)<a\b[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', body)]
    body = re.sub(r"(?i)<(br|/p|/div|/li|/h\d|/tr|/a|/span)\b[^>]*>", "\n", body)
    return "\n".join(finder._text(line) for line in body.split("\n")), links


def read(path):
    """Lines read from one upload, grouped by screen (each screenshot or video still is its own group)."""
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGES:
        return [ocr(path)], []
    if ext in VIDEOS:
        with tempfile.TemporaryDirectory() as tmp:
            return [ocr(f) for f in frames(path, tmp)], []
    if ext == ".pdf":
        return [text_lines(_pdf_text(path))], []
    if ext in PAGES:
        with open(path, encoding="utf-8", errors="replace") as f:
            text, links = _page_text(f.read())
        return [text_lines(text)], links
    if ext in TEXTS or ext == "":
        with open(path, encoding="utf-8", errors="replace") as f:
            return [text_lines(f.read())], []
    raise ReadError(f"JobBot can't read {ext} files. Upload screenshots (PNG or JPG), a screen recording or copied text.")


# ------------------------------------------------------------------ splitting into listings

def rows(lines):
    """Lines side by side (a title and, to its right, its date and score) as one row, top to bottom."""
    out = []
    for line in sorted(lines, key=lambda l: (l.y + l.h / 2, l.x)):
        mid = line.y + line.h / 2
        if out and abs(mid - out[-1]["mid"]) < 0.6 * max(line.h, out[-1]["h"]):
            out[-1]["parts"].append(line)
        else:
            out.append({"mid": mid, "h": line.h, "parts": [line]})
    for r in out:
        r["parts"].sort(key=lambda l: l.x)
    return out


def _is_title(line, typical_h):
    t = line.text.strip()
    lead = SEP.split(t)[0]  # "Plano, TX · Internship" is a location line, not an internship called that
    return (6 <= len(t) <= 110 and (t[0].isupper() or t[0].isdigit()) and TITLE_WORD.search(t)
            and not NOISE.search(lead) and not LOCATION.search(lead)
            and not HEADER.match(t) and not POSTED.match(t) and not SCORE.match(t) and not SENTENCE.search(t)
            and len(t.split()) <= 14 and line.h >= 0.85 * typical_h)


def _clean_title(t):
    t = re.sub(r"^[\W_]+", "", t)
    t = re.sub(r"\s+(new|promoted|easy apply|actively recruiting)$", "", t, flags=re.I).strip()
    return re.sub(r"[\s(\-–—&,/]+$", "", t)  # a title cut off at the card's edge: "Analyst, 1898 &"


def _continues(title, nxt):
    """Whether the next line is the rest of a title the app wrapped onto two lines."""
    t = nxt.strip()
    if not t or POSTED.match(t) or SCORE.match(t) or LOCATION.search(SEP.split(t)[0]):
        return False
    if NOISE.search(t) and not re.fullmatch(r"intern(ship)?|co-?op", t, re.I):  # "Land Development," / "Internship"
        return False
    if title.rstrip().endswith("("):
        return ")" in t
    return t[0].islower() or t[0] == "(" or bool(CONTINUES.search(title))


def _main_column(lines):
    """Where the listings' text starts: the most common left edge of longer lines. Logos sit to its left."""
    xs = [round(l.x / 20) for l in lines if len(l.text) > 12]
    return statistics.mode(xs) * 20 if xs else None


def _join_titles(rws, typical_h):
    """Rows with each two-line title joined into one."""
    out, skip = [], False
    for i, r in enumerate(rws):
        if skip:
            skip = False
            continue
        first = r["parts"][0]
        nxt = rws[i + 1] if i + 1 < len(rws) else None
        if (nxt and nxt["mid"] - r["mid"] <= 1.8 * typical_h and len(nxt["parts"]) == 1
                and _continues(first.text, nxt["parts"][0].text)):
            joined = Line(f"{first.text} {nxt['parts'][0].text}", first.x, first.y, first.h)
            if _is_title(joined, typical_h):  # the first line alone may lack the job word: "Land Development," / "Internship"
                r = {**r, "parts": [joined] + r["parts"][1:]}
                skip = True
        out.append(r)
    return out


def _piece(t):
    """What one piece of a listing is: score, posted, location, noise or other."""
    m = SCORE.match(t)
    if m:
        n = int(next(g for g in m.groups() if g))
        return ("score", n) if n <= 100 else ("other", t)
    if POSTED.match(t):
        return "posted", t
    if NOISE.search(t) or (SENTENCE.search(t) and len(t.split()) > 4) or len(t.split()) > 8:  # tags, pay, description
        return "noise", t
    if LOCATION.search(t):
        return "location", re.sub(r",(?=\S)", ", ", t)
    return "other", t


def _listing(title, rest):
    out = {"title": title, "company": "", "location": "", "posted": "", "score": None}
    for text in rest:
        for t in SEP.split(text):
            kind, value = _piece(t.strip())
            if kind == "score" and out["score"] is None:
                out["score"] = value
            elif kind == "posted" and not out["posted"]:
                out["posted"] = value
            elif kind == "location" and not out["location"]:
                out["location"] = value
            elif kind == "other" and not out["company"] and not TITLE_WORD.fullmatch(value):
                out["company"] = value
    return out


def _cards(rws):
    """Rows grouped into cards, where a screen leaves more space between jobs than inside one; None when it doesn't."""
    gaps = sorted(b["mid"] - a["mid"] for a, b in zip(rws, rws[1:]))
    if len(gaps) < 3:
        return None
    jump = max(range(1, len(gaps)), key=lambda i: gaps[i] / max(gaps[i - 1], 1e-6))
    if gaps[jump] / max(gaps[jump - 1], 1e-6) < 1.6 or len(gaps) - jump < 2:
        return None
    cut = (gaps[jump] + gaps[jump - 1]) / 2
    cards = [[rws[0]]]
    for a, b in zip(rws, rws[1:]):
        if b["mid"] - a["mid"] > cut:
            cards.append([])
        cards[-1].append(b)
    return cards


def _by_titles(rws, typical_h):
    """Listings in a block of rows: each title row and the rows under it, up to the next title."""
    found, cur = [], None
    for r in rws:
        first = r["parts"][0]
        if _is_title(first, typical_h):
            cur = {"title": _clean_title(first.text), "rest": [p.text for p in r["parts"][1:]], "last": r["mid"], "n": 0}
            found.append(cur)
        elif cur and r["mid"] - cur["last"] <= 4 * typical_h and cur["n"] < 4:
            cur["rest"].extend(p.text for p in r["parts"])
            cur["last"], cur["n"] = r["mid"], cur["n"] + 1
        else:
            cur = None
    return [_listing(f["title"], f["rest"]) for f in found]


def split(lines):
    """Listings on one screen. Cards (the usual look) are read whole, so a company shown above its title counts too."""
    if not lines:
        return []
    col = _main_column(lines)
    if col is not None:
        lines = [l for l in lines if l.x >= col - 40 or len(l.text) > 14]  # company logos left of the text
    if not lines:
        return []
    typical_h = statistics.median(l.h for l in lines)
    rws = _join_titles(rows(lines), typical_h)
    out = []
    for card in _cards(rws) or [rws]:
        titles = [i for i, r in enumerate(card) if _is_title(r["parts"][0], typical_h)]
        if len(titles) != 1 or len(card) == len(rws):
            out += _by_titles(card, typical_h)
            continue
        i = titles[0]
        near = sorted((j for j in range(len(card)) if j != i), key=lambda j: (abs(j - i), j < i))
        rest = [p.text for p in card[i]["parts"][1:]] + [p.text for j in near for p in card[j]["parts"]]
        out.append(_listing(_clean_title(card[i]["parts"][0].text), rest))
    return out


def merge(listings):
    """One listing per job across screens (a recording shows each job in several stills)."""
    out = {}
    for l in listings:
        key = (norm(l["title"]), norm(l["company"]))
        have = out.setdefault(key, dict(l))
        for f, v in l.items():
            if v not in (None, "") and have.get(f) in (None, ""):
                have[f] = v
    with_company = {k[0] for k in out if k[1]}
    return [l for k, l in out.items() if k[1] or k[0] not in with_company]  # a card cut off at the screen's edge


def _with_links(listings, links):
    """Copied web pages carry each job's link: match them to listings by title."""
    by_title = {}
    for link in links or []:
        by_title.setdefault(norm(link.get("t") or ""), link.get("u"))
    for l in listings:
        l["url"] = l.get("url") or by_title.get(norm(l["title"])) or ""
    return listings


# ------------------------------------------------------------------ keeping and finding

def pick(listings, min_score=90, search=None):
    """(kept, dropped): business roles the board scored at least min_score (or didn't score at all)."""
    search = search or {"field": "business"}
    kept, dropped = [], []
    for l in listings:
        ok, why = fields.classify({"title": l["title"]}, search)
        if not ok and why == "Not clearly a business role" and l["score"] is not None:
            ok, why = True, "Business (the title doesn't say which area)"  # a screenshot shows no department; the board's score vouches
        if not ok:
            dropped.append({**l, "why": why})
        elif len(l["company"]) < 2:
            dropped.append({**l, "why": "Company not read"})
        elif l["score"] is not None and l["score"] < min_score:
            dropped.append({**l, "why": f"Board score {l['score']}, under {min_score}"})
        else:
            kept.append({**l, "area": why})
    return kept, dropped


def _locate(l):
    if l.get("url") and not ats.JOB_BOARDS.search(l["url"]):
        return {**l, "found": True}  # already the employer's own link
    try:  # a board's copy, or no link at all: the same job where the employer posts it
        url = finder.find(l["title"], l["company"], l["location"], budget=LOOKUP_BUDGET)
    except Exception:  # noqa: BLE001 - one job's lookup failing must not lose the others
        url = None
    if url:
        return {**l, "url": url, "found": True}
    return {**l, "url": "", "found": False, "why": "Not found on the employer's site"}


def locate(listings, workers=4):
    """Each listing with the employer's own posting (url), where JobBot finds it."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(_locate, listings))


def run(paths, text=None, links=None, min_score=90, search=None, find=True):
    """Read uploads and copied text; returns {"read", "kept", "dropped", "errors"}."""
    listings, errors, all_links = [], [], list(links or [])
    for path in paths:
        try:
            screens, page_links = read(path)
        except ReadError as e:
            errors.append({"file": os.path.basename(path), "why": str(e)})
            continue
        all_links += page_links
        for screen in screens:
            listings += split(screen)
    if text:
        listings += split(text_lines(text))
    listings = _with_links(merge(listings), all_links)
    kept, dropped = pick(listings, min_score, search)
    if find:
        kept = locate(kept)
    return {"read": len(listings), "kept": kept, "dropped": dropped, "errors": errors}


def write(result, path):
    with open(path, "w") as f:
        json.dump(result, f, indent=1)
