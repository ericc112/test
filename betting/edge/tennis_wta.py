"""WTA 125 match statistics from the WTA's own data feed (api.wtatennis.com), for WTA players whose tour-level
history (TennisMyLife covers WTA tour events only) is too thin: their last year of WTA 125 matches, each with both
players' serve points played and won, aces, double faults, service games and the match time. Fetched slowly and
cached; same match format as tennis_hist.load()."""
from __future__ import annotations

import datetime as dt
import json
import os
import time
import urllib.parse
import urllib.request

API = "https://api.wtatennis.com/tennis"
THROTTLE = 2.5
_last = [0.0]


def _get(url: str, path: str, max_age: float):
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age:
        return json.load(open(path))
    wait = THROTTLE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (edge tennis research)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.loads(r.read().decode("utf-8"))
    _last[0] = time.time()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(d, open(path, "w"))
    return d


def find(name: str, cache: str):
    d = _get(f"{API}/players/?page=0&pageSize=5&name={urllib.parse.quote(name.split()[-1])}",
             os.path.join(cache, f"find_{name.replace(' ', '_')}.json"), 30 * 86400)
    from .nba_pp import _norm
    for p in d.get("content", []):
        if _norm(p["fullName"]) == _norm(name):
            return p["id"]
    return None


def _minutes(t: str):
    try:
        h, m, s = (int(x) for x in t.split(":"))
        return h * 60 + m + round(s / 60)
    except (ValueError, AttributeError):
        return None


def history(name: str, cache: str, days: int = 365, max_age: float = 12 * 3600) -> list[dict]:
    """The player's WTA 125 matches in the last `days`, with serve counts, as tennis_hist match rows (ids "wta:<id>",
    tour "WTA", level "125")."""
    from . import tennis_hist as TH
    pid = find(name, cache)
    if not pid:
        return []
    L = _get(f"{API}/players/{pid}/matches/?page=0&pageSize=60&type=S&sort=desc", os.path.join(cache, f"pm_{pid}.json"), max_age).get("matches", [])
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    events = {(m["tourn_nbr"], m["tourn_year"]): m for m in L if m.get("TournamentLevel") == "C" and m["StartDate"][:10] >= since}
    out = []
    for (tid, yr), info in events.items():
        tl = _get(f"{API}/tournaments/{tid}/{yr}/matches/", os.path.join(cache, f"tm_{tid}_{yr}.json"), max_age).get("matches", [])
        for m in tl:
            if m.get("DrawMatchType") != "S" or m.get("MatchState") != "F" or str(pid) not in (m.get("PlayerIDA"), m.get("PlayerIDB")):
                continue
            st = _get(f"{API}/tournaments/{tid}/{yr}/matches/{m['MatchID']}/stats", os.path.join(cache, f"st_{tid}_{yr}_{m['MatchID']}.json"), 30 * 86400)
            row = next((x for x in st if x.get("setnum") == 0), None) if isinstance(st, list) else None
            win_a = str(m.get("Winner")) in ("2", "A")            # the feed codes the winner of side A as 2, side B as 3
            w, l = ("a", "b") if win_a else ("b", "a")
            W, Lr = ("A", "B") if win_a else ("B", "A")
            score = m.get("ScoreString", "").replace(",", " ")
            sc = TH.parse_score(score) if score else None           # the feed writes the score from the winner's side
            start = dt.date.fromisoformat(info["StartDate"][:10])
            r = {"tour": "WTA", "level": "125", "ev": f"WTA125-{tid}-{yr}", "tname": info["TournamentName"], "date": int(start.strftime("%Y%m%d")),
                 "surface": info["Surface"].title(), "indoor": None, "round": m.get("RoundID") or "", "ro": TH.ROUND.get(m.get("RoundID") or "", 6),
                 "bo": 3, "minutes": _minutes(m.get("MatchTimeTotal")), "w": f"wta:{m['PlayerID' + W]}", "l": f"wta:{m['PlayerID' + Lr]}",
                 "w_name": f"{m['PlayerNameFirst' + W]} {m['PlayerNameLast' + W]}", "l_name": f"{m['PlayerNameFirst' + Lr]} {m['PlayerNameLast' + Lr]}",
                 "w_hand": "", "l_hand": "", "w_rank": None, "l_rank": None, "score": score, "sc": sc, "start": int(start.strftime("%Y%m%d")),
                 "day": start.toordinal()}
            for s, side in (("w", w), ("l", l)):
                n, k = (row or {}).get(f"totservplayed{side}"), (row or {}).get(f"ptstotwonserv{side}")
                r[f"{s}_n"], r[f"{s}_k"] = (int(n), int(k)) if n and k is not None and int(n) >= 10 else (None, None)
            if r["surface"] in TH.SURF:
                out.append(r)
    return out
