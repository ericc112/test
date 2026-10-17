"""Readable job locations: "CA - Glendale" -> "Glendale, CA", remote and hybrid noted, US states listed.

Boards write locations every which way ("NC - Charlotte", "California - San Francisco",
"1000 Nicollet Mall, Minneapolis,MN 55403-2542", "Hybrid - New York, NY", "United States"
for a remote job). describe() turns them into one short line plus the US states involved,
so jobs can be shown and filtered by place.
"""
import re

from .scoring import _STATE_NAMES, _STATES

STATE_CODES = set(_STATES)
NAME_TO_CODE = {n: c for n, c in zip(_STATE_NAMES.split("|"), [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME",
    "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
    "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"])}
NAME_TO_CODE.update({"district of columbia": "DC", "washington dc": "DC", "washington d.c.": "DC"})
# Cities often written without a state.
CITIES = {"new york": "NY", "new york city": "NY", "nyc": "NY", "manhattan": "NY", "brooklyn": "NY",
          "san francisco": "CA", "south san francisco": "CA", "los angeles": "CA", "san jose": "CA", "san diego": "CA",
          "palo alto": "CA", "menlo park": "CA", "mountain view": "CA", "sunnyvale": "CA", "irvine": "CA",
          "seattle": "WA", "bellevue": "WA", "redmond": "WA", "chicago": "IL", "boston": "MA", "cambridge": "MA",
          "austin": "TX", "dallas": "TX", "houston": "TX", "plano": "TX", "irving": "TX", "san antonio": "TX",
          "denver": "CO", "atlanta": "GA", "minneapolis": "MN", "charlotte": "NC", "raleigh": "NC",
          "philadelphia": "PA", "pittsburgh": "PA", "miami": "FL", "tampa": "FL", "orlando": "FL", "jacksonville": "FL",
          "detroit": "MI", "phoenix": "AZ", "salt lake city": "UT", "nashville": "TN", "columbus": "OH",
          "cincinnati": "OH", "cleveland": "OH", "indianapolis": "IN", "st. louis": "MO", "saint louis": "MO",
          "kansas city": "MO", "milwaukee": "WI", "omaha": "NE", "baltimore": "MD", "jersey city": "NJ",
          "newark": "NJ", "hartford": "CT", "bentonville": "AR", "las vegas": "NV", "honolulu": "HI"}
US_ONLY = re.compile(r"^\s*(usa?|u\.s\.a?\.?|united states( of america)?|us[- ]remote|remote[,\s-]*(usa?|united states)?)\s*$", re.I)
WORK_MODE = re.compile(r"\b(hybrid|remote|in[- ]?office|on[- ]?site|onsite|flexible|hq)\b", re.I)
ST_DASH_CITY = re.compile(r"^([A-Z]{2})\s+-\s+(.+)$")  # Workday "CA - Glendale" (spaces: "CA-Toronto" is Canada)
NAME_DASH_CITY = re.compile(r"^([A-Za-z .]+?)\s*-\s*(.+)$")  # "California - San Francisco"
CITY_COMMA_ST = re.compile(r"([A-Za-z][A-Za-z .'-]*?)\s*,\s*([A-Z]{2})\b(?!\s*-)")  # "Bethesda, MD", "Minneapolis,MN 55403"
CITY_COMMA_NAME = re.compile(r"([A-Za-z][A-Za-z .'-]*?)\s*,\s*(" + _STATE_NAMES + r")\b", re.I)


def _title(s):
    return " ".join(w if w.isupper() and len(w) <= 3 else w.capitalize() for w in s.split())


def _part(p):
    """One location ("NC - Charlotte") -> (city, state code) or None."""
    p = WORK_MODE.sub("", p).strip(" -·,()")
    if not p:
        return None
    m = ST_DASH_CITY.match(p)
    if m and m.group(1) in STATE_CODES:
        return _title(m.group(2).strip()), m.group(1)
    m = NAME_DASH_CITY.match(p)
    if m and m.group(1).strip().lower() in NAME_TO_CODE:
        return _title(m.group(2).strip()), NAME_TO_CODE[m.group(1).strip().lower()]
    hits = [m for m in CITY_COMMA_ST.finditer(p) if m.group(2) in STATE_CODES]
    if hits:
        m = hits[-1]
        return _title(m.group(1).split(",")[-1].strip()), m.group(2)
    m = CITY_COMMA_NAME.search(p)
    if m:
        return _title(m.group(1).split(",")[-1].strip()), NAME_TO_CODE[m.group(2).lower()]
    if p.lower() in NAME_TO_CODE:
        return "", NAME_TO_CODE[p.lower()]
    city = p.split(",")[0].strip().lower()
    if city in CITIES and (p.count(",") == 0 or re.search(r",\s*(usa?|united states)\s*$", p, re.I)):
        return _title(city) if city != "nyc" else "New York", CITIES[city]
    return None


def describe(job):
    """{"text", "states", "remote", "hybrid", "us"} for one job."""
    loc = " ".join((job.get("location") or "").split())
    low = loc.lower()
    remote = bool(job.get("remote")) or "remote" in low
    hybrid = "hybrid" in low
    parts = [p for p in re.split(r";|·|\|| / |\n", loc) if p.strip()]
    if len(parts) == 1 and loc.count(",") >= 2 and not CITY_COMMA_ST.search(loc) and not CITY_COMMA_NAME.search(loc):
        parts = loc.split(",")  # "New York, Seattle, South San Francisco HQ"
    places = [x for x in (_part(p) for p in parts) if x]
    states = sorted({st for _, st in places})
    us = bool(states) or bool(US_ONLY.match(loc)) or not loc and remote
    if places:
        seen, names = set(), []
        for city, st in places:
            name = f"{city}, {st}" if city else NAME_FROM_CODE.get(st, st)
            if name not in seen:
                seen.add(name)
                names.append(name)
        text = "; ".join(names[:2]) + (f" +{len(names) - 2} more" if len(names) > 2 else "")
    elif us:
        text = "United States"
    else:
        cleaned = [" ".join(WORK_MODE.sub("", p).split()).strip(" -·,/()") for p in parts]
        text = "; ".join(c for c in cleaned if c)
    if remote and (not places or text == "United States"):
        text = "Remote (US)" if us else f"Remote · {text}" if text else "Remote"
    elif not text:
        text = "Hybrid" if hybrid else ""
    elif remote:
        text += " · Remote"
    elif hybrid:
        text += " · Hybrid"
    return {"text": text, "states": states, "remote": remote, "hybrid": hybrid, "us": us}


NAME_FROM_CODE = {c: n.title() for n, c in NAME_TO_CODE.items() if " d" not in n and n != "washington dc"}
NAME_FROM_CODE["DC"] = "Washington, DC"
