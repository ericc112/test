"""Tennis match-winner prices from Tennis Explorer (tennisexplorer.com): the daily results pages list every ATP
(tour and Challenger) and WTA match with its closing odds, and the same pages carry today's and tomorrow's odds.
Pages are fetched slowly (THROTTLE seconds apart) and cached."""
from __future__ import annotations

import datetime as dt
import html
import os
import re
import time
import unicodedata
import urllib.request

TE = "https://www.tennisexplorer.com"
THROTTLE = 3.0
_last = [0.0]


def _get(url: str, path: str, max_age: float) -> str:
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age:
        return open(path, encoding="utf-8", errors="replace").read()
    wait = THROTTLE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (edge tennis research)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        s = r.read().decode("utf-8", errors="replace")
    _last[0] = time.time()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(s)
    return s


def _cells(row: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]


def _odds(x: str):
    try:
        v = float(x)
        return v if v > 1.0 else None
    except ValueError:
        return None


def parse(s: str, date: str, tour: str) -> list[dict]:
    """Matches on a results page: tournament, both players (as listed, the winner first once played), sets, games and
    the two closing odds (H for the first-listed player)."""
    out, tourn, pend = [], None, None
    i = s.find('class="result')
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", s[i:], re.S):
        c = _cells(row)
        if not c:
            continue
        if len(c) >= 9 and c[1] == "S" and c[2] == "1":
            tourn, pend = c[0], None
            continue
        slugs = re.findall(r'href="/player/([^"/]+)/', row)
        if len(c) >= 8 and re.match(r"^(\d\d:\d\d|today|tomorrow|---)", c[0] or "") and slugs:
            odds = [x for x in c[2:] if re.match(r"^\d+\.\d{2}$", x)]        # the last two decimal cells (layouts differ by page)
            pend = {"date": date, "tour": tour, "tourn": tourn, "time": c[0][:5], "p1": re.sub(r"\s*\(\d+\)|\s*\(\w+\)$", "", c[1]).strip(),
                    "s1": c[2], "g1": [x for x in c[3:8] if x.isdigit()], "o1": _odds(odds[-2]) if len(odds) >= 2 else None,
                    "o2": _odds(odds[-1]) if len(odds) >= 2 else None, "slug1": slugs[0]}
        elif pend and len(c) >= 7 and slugs:
            pend.update({"p2": re.sub(r"\s*\(\d+\)|\s*\(\w+\)$", "", c[0]).strip(), "s2": c[1], "g2": [x for x in c[2:7] if x], "slug2": slugs[0]})
            out.append(pend)
            pend = None
    return out


def day(date: dt.date, tour: str, cache: str, max_age: float = 10 ** 9, upcoming: bool = False) -> list[dict]:
    """A day's matches with closing odds (results page), or with the current odds for matches still to play
    (upcoming=True: the matches page)."""
    t = {"ATP": "atp-single", "WTA": "wta-single"}[tour]
    kind = "matches" if upcoming else "results"
    url = f"{TE}/{kind}/?type={t}&year={date.year}&month={date.month:02d}&day={date.day:02d}"
    today = dt.date.today()
    age = 1800 if date >= today - dt.timedelta(days=1) else max_age
    name = f"te_{'matches_' if upcoming else ''}{tour}_{date.isoformat()}.html"
    return parse(_get(url, os.path.join(cache, name), age), date.isoformat(), tour)


def fair(o1, o2):
    """De-vigged win probability for the first-listed player (proportional)."""
    if not o1 or not o2:
        return None
    a, b = 1 / o1, 1 / o2
    return a / (a + b)


def surname_key(name: str) -> str:
    """'Davidovich Fokina A.' / 'Alejandro Davidovich Fokina' -> 'davidovichfokina' (surname letters only)."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\s+[a-z]\.(\s*[a-z]\.)*$", "", s.strip())      # Tennis Explorer's trailing initials
    return re.sub(r"[^a-z]", "", s)


def tml_key(full: str) -> list[str]:
    """Surname candidates for a TennisMyLife full name ('Alejandro Davidovich Fokina'): the last 1, 2 and 3 words."""
    w = unicodedata.normalize("NFKD", full).encode("ascii", "ignore").decode().lower().split()
    return [re.sub(r"[^a-z]", "", "".join(w[-k:])) for k in (1, 2, 3) if len(w) > k - 1 and len(w) >= k]
