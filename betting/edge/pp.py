"""PrizePicks boards, priced: python -m edge pp --league CS2 [--match Liquid] [--log]

The partner API (partner-api.prizepicks.com) serves every board without a captcha. Each prop is
routed to a pricer:
  CS2     MAPS 1-2 Kills / Headshots      cs2.py model (bo3.gg) + series history
  soccer  Passes Attempted                soccer.py model (ESPN) + recent starts
          Shots / Shots On Target /       DraftKings milestone ladder (Poisson fit, ~7% vig removed)
          Goalie Saves                    + recent matches
Everything else is listed as unpriced. Probabilities go through blend.final_probability, so the
gates, learned corrections and confidence labels are the same as `edge prob`.
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import datetime as dt
import difflib
import json
import math
import os
import re
import time
import unicodedata
import urllib.error

import numpy as np

from . import cs2, lol, soccer
from .blend import HERE, final_probability
from .grade import _get

PP = "https://partner-api.prizepicks.com"
SITE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
CORE = "https://sports.core.api.espn.com/v2/sports/soccer/leagues"
SOCCER = {"UCL": "uefa.champions", "UEL": "uefa.europa", "UECL": "uefa.europa.conf", "EPL": "eng.1", "LALIGA": "esp.1",
          "SERIEA": "ita.1", "BUNDES": "ger.1", "LIGUE1": "fra.1", "MLS": "usa.1", "UCLW": "uefa.wchampions"}
DK_TYPES = {"Shots": ("Shots Milestones", "shots"), "Shots On Target": ("Shots on Target Milestones", "sot"),
            "Goalie Saves": ("Goalkeeper Saves Milestones", "gk_saves")}
ROSTER_STAT = {"shots": "totalShots", "sot": "shotsOnTarget", "gk_saves": "saves"}
MILESTONE_HOLD = 0.93   # one-sided DraftKings milestone prices carry roughly 7% hold


# ------------------------------------------------------------------ board
PP_CACHE = os.path.join(HERE, ".cache", "pp")


def pp_get(url: str, max_age: int = 120):
    """PrizePicks rate-limits (429): cache responses for two minutes and back off on 429."""
    path = os.path.join(PP_CACHE, re.sub(r"[^A-Za-z0-9]+", "_", url[len(PP):]) + ".json")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age:
        with open(path) as f:
            return json.load(f)
    for wait in (5, 15, 30, None):
        try:
            out = _get(url)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or wait is None:
                raise
            time.sleep(wait)
    os.makedirs(PP_CACHE, exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f)
    return out


def leagues() -> dict:
    return {x["attributes"]["name"].upper(): x["id"] for x in pp_get(f"{PP}/leagues", max_age=86400)["data"]}


def board(league: str, odds_types=("standard",)) -> list[dict]:
    lid = leagues().get(league.upper())
    if lid is None:
        raise ValueError(f"unknown PrizePicks league {league}")
    d = pp_get(f"{PP}/projections?league_id={lid}&per_page=10000")
    inc = {(x["type"], x["id"]): x["attributes"] for x in d.get("included", [])}
    out = []
    for p in d["data"]:
        a = p["attributes"]
        if odds_types and a.get("odds_type") not in odds_types:
            continue
        rel = p.get("relationships", {})
        pl = inc.get(("new_player", (rel.get("new_player", {}).get("data") or {}).get("id")), {})
        gm = inc.get(("game", (rel.get("game", {}).get("data") or {}).get("id")), {})
        teams = ((gm.get("metadata") or {}).get("game_info") or {}).get("teams") or {}
        out.append({"league": league.upper(), "player": pl.get("display_name") or pl.get("name"), "team": pl.get("team"),
                    "team_name": pl.get("team_name"), "position": pl.get("position"), "opp": re.sub(r"\s*MAPS.*$", "", a.get("description") or ""),
                    "stat": a.get("stat_type"), "line": float(a.get("line_score")), "odds_type": a.get("odds_type"),
                    # goblins and demons are More-only in the app. The partner feed's allowed_wager_types says "over" on
                    # almost every standard line too, but the app shows Less on them (Rice passes 79.5, 10/13): not trusted
                    "over_only": a.get("odds_type") in ("goblin", "demon"),
                    "feed_over_only": a.get("allowed_wager_types") == "over",
                    "start": a.get("start_time"), "home": (teams.get("home") or {}).get("abbreviation"),
                    "away": (teams.get("away") or {}).get("abbreviation")})
    return out


# ------------------------------------------------------------------ soccer helpers
def _fold(s: str) -> list[str]:
    """Accent-free name tokens without club filler words: 'Sporting Clube de Portugal' -> ['sporting', 'clube', 'portugal']."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\b(fc|cf|cp|sc|ac|afc|club|de|the|sv|fk|bk|ssc|as)\b|[^a-z ]", " ", s).split()


def _close(a: str, b: str) -> float:
    ta, tb = set(_fold(a)), set(_fold(b))
    return 1.0 if ta & tb else difflib.SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()


def espn_event(slug: str, start: str, home: str, away: str) -> dict | None:
    day = dt.datetime.fromisoformat(start).date()
    for d in (day, day - dt.timedelta(days=1), day + dt.timedelta(days=1)):
        for e in _get(f"{SITE}/{slug}/scoreboard?dates={d:%Y%m%d}").get("events", []):
            cs = {c["homeAway"]: c["team"] for c in e["competitions"][0]["competitors"]}
            score = min(max(_close(home, cs["home"].get(k, "")) for k in ("displayName", "shortDisplayName", "abbreviation")),
                        max(_close(away, cs["away"].get(k, "")) for k in ("displayName", "shortDisplayName", "abbreviation")))
            if score >= 0.7:
                return {"id": e["id"], "home_id": str(cs["home"]["id"]), "away_id": str(cs["away"]["id"]),
                        "home_name": cs["home"]["displayName"], "away_name": cs["away"]["displayName"]}
    return None


def espn_player(slug: str, team_id: str, name: str) -> tuple[str | None, list[str]]:
    ath = _get(f"{SITE}/{slug}/teams/{team_id}/roster").get("athletes", [])
    best = max(ath, key=lambda a: _close(name, a.get("displayName", "")) + (0.5 if _fold(name) == _fold(a.get("displayName", "")) else 0), default=None)
    gks = [str(a["id"]) for a in ath if (a.get("position") or {}).get("abbreviation") in ("G", "GK")]
    if best is None or _close(name, best.get("displayName", "")) < 0.75:
        return None, gks
    return str(best["id"]), gks


def dk_ladders(slug: str, event_id: str) -> dict:
    items, page = [], 1
    while True:
        d = _get(f"{CORE}/{slug}/events/{event_id}/competitions/{event_id}/odds/100/propBets?lang=en&region=us&limit=1000&page={page}")
        items += d.get("items", [])
        if page >= d.get("pageCount", 1):
            break
        page += 1
    lad = collections.defaultdict(dict)
    for x in items:
        a = (x.get("athlete") or {}).get("$ref", "")
        m = re.search(r"/athletes/(\d+)", a)
        cur = x.get("current") or {}
        k, a = (cur.get("target") or {}).get("value"), (cur.get("over") or {}).get("american")
        if m and k is not None and a not in (None, ""):
            lad[(x["type"]["name"], m.group(1))][int(k)] = float(a)
    return lad


def ladder_lambda(ladder: dict) -> float | None:
    """Poisson mean that best fits a de-vigged 'k+' ladder (points between 10% and 90% implied)."""
    imp = {k: (100 / (a + 100) if a > 0 else -a / (-a + 100)) * MILESTONE_HOLD for k, a in ladder.items()}
    pts = {k: v for k, v in imp.items() if 0.1 <= v <= 0.9}
    if not pts:
        return None
    sf = lambda lam, k: 1 - sum(math.exp(-lam) * lam ** j / math.factorial(j) for j in range(k))
    return float(min(np.linspace(0.05, 12, 400), key=lambda lam: sum((sf(lam, k) - v) ** 2 for k, v in pts.items())))


def poisson_sides(lam: float, line: float) -> tuple[float, float, float]:
    pmf = lambda j: math.exp(-lam) * lam ** j / math.factorial(j)
    under = sum(pmf(j) for j in range(int(math.ceil(line))))      # strictly below the line
    push = pmf(int(line)) if float(line).is_integer() else 0.0
    return 1 - under - push, under, push


# ------------------------------------------------------------------ pricers
def _finish(p: dict, market_key: str, sport: str, p_over, p_under, p_push, hist_over, hist_under, mk_over=None, notes=""):
    """Pick the side, blend model/market/history, attach the confidence label."""
    sides = ["over"] if p["over_only"] else ["over", "under"]
    best = None
    for side in sides:
        pm = None if p_over is None else (p_over if side == "over" else p_under) / max(1 - (p_push or 0), 1e-9)
        pk = None if mk_over is None else (mk_over if side == "over" else 1 - mk_over)
        dec = hist_over + hist_under
        ph = None if not dec else (hist_over if side == "over" else hist_under) / dec
        if pm is None and pk is None and ph is None:
            continue
        e = final_probability(pm, pk, ph, f"{sport}:{market_key}:{side}", dec)
        if best is None or e.p > best["p_final"]:
            best = {"side": side, "p_final": e.p, "confidence": e.confidence, "p_model": pm, "p_market": pk, "p_hist": ph,
                    "hist_n": dec, "agree": e.agreement}
    if best is None:
        return {**p, "error": "nothing to price with"}
    return {**p, **best, "market_key": market_key, "sport": sport, "push": p_push or 0.0, "notes": notes}


def price_cs2(props: list[dict]) -> list[dict]:
    by_match = collections.defaultdict(list)
    for p in props:
        if p["stat"] in ("MAPS 1-2 Kills", "MAPS 1-2 Headshots"):
            by_match[tuple(sorted((p["team"], p["opp"])))].append({**p, "stat_key": "kills" if "Kills" in p["stat"] else "hs"})
    out = []

    def run(key):
        legs = by_match[key]
        res = cs2.price_match(key[0], key[1], [{"player": l["player"], "team": l["team"], "stat": l["stat_key"], "line": l["line"]} for l in legs])
        rows = []
        for l, r in zip(legs, res):
            if "error" in r:
                rows.append({**l, "error": r["error"]})
                continue
            mk = "cs_kills_m12" if l["stat_key"] == "kills" else "cs_headshots_m12"
            flag = ("NEW TO TEAM: priced from previous team" if r["newcomer"] else
                    f"THIN SAMPLE: {r['maps']} maps with this roster" if r["thin"] else "")
            note = (flag + ", role unconfirmed (L5); " if flag else "") + f"median {r['median']:.0f}, per-map win {r['p_map']:.0%}"
            row = _finish(l, mk, "cs2", r["p_over"], r["p_under"], r["p_push"], r["hist_over"], r["hist_under"], notes=note)
            if flag and "confidence" in row:
                row["confidence"] = "Low"  # unproven role: never an entry leg until the lineup and role are confirmed
            rows.append({**row, "event_id": r["event_id"], "player_id": l["player"], "proj": r["median"], "script": f"cs2:{r['event_id']}",
                         "newcomer": r["newcomer"] or r["thin"]})
        return rows

    with cf.ThreadPoolExecutor(3) as ex:
        for rows in ex.map(run, list(by_match)):
            out += rows
    out += [{**p, "error": "stat not priced yet"} for p in props if p["stat"] not in ("MAPS 1-2 Kills", "MAPS 1-2 Headshots")]
    return out


def price_soccer(props: list[dict]) -> list[dict]:
    out, cache = [], {}
    for p in props:
        slug = SOCCER.get(p["league"])
        if p["stat"] not in ("Passes Attempted", *DK_TYPES) or not slug:
            out.append({**p, "error": "stat not priced yet"})
            continue
        try:
            ek = ("ev", p["start"], p["home"], p["away"])
            if ek not in cache:
                cache[ek] = espn_event(slug, p["start"], p["home"], p["away"])
            ev = cache[ek]
            if not ev:
                out.append({**p, "error": "ESPN event not found"})
                continue
            home_side = max(_close(p["team_name"] or p["team"], ev["home_name"]), _close(p["team"], ev["home_name"])) >= \
                max(_close(p["team_name"] or p["team"], ev["away_name"]), _close(p["team"], ev["away_name"]))
            tid = ev["home_id"] if home_side else ev["away_id"]
            pid, gks = espn_player(slug, tid, p["player"])
            if not pid:
                out.append({**p, "error": "player not found on ESPN roster"})
                continue
            base = {"event_id": ev["id"], "player_id": pid, "script": f"soccer:{ev['id']}"}
            if p["stat"] == "Passes Attempted":
                m = soccer.passes_model(pid, tid, line=p["line"], event_id=ev["id"])
                ho = sum(v > p["line"] for v in m["hist_vals"])
                hu = sum(v < p["line"] for v in m["hist_vals"])
                note = (f"KEEPER: priced from his own {m['sample']} starts (keepers pass more when their team has less of the ball); "
                        f"median {m['median']:.0f}; confirm lineup") if m.get("keeper") else \
                    f"median {m['median']:.0f}, possession {m['possession']:.0%}, press factor {m['press_factor']:.2f}; share and history from {m.get('basis')}; confirm lineup"
                out.append({**_finish(p, "passes_att", "soccer", m["p_over"], m["p_under"], m["p_push"], ho, hu, notes=note), **base, "proj": m["median"]})
                continue
            dk_type, key = DK_TYPES[p["stat"]]
            lk = ("dk", ev["id"])
            if lk not in cache:
                cache[lk] = dk_ladders(slug, ev["id"])
            lad = cache[lk].get((dk_type, pid))
            note = ""
            if not lad and key == "gk_saves":  # DraftKings sometimes lists the team's keeper under another name
                lad = next((cache[lk][(dk_type, g)] for g in gks if (dk_type, g) in cache[lk]), None)
                note = "keeper ladder taken from the team's listed goalkeeper; "
            lam = ladder_lambda(lad) if lad else None
            mk_over = poisson_sides(lam, p["line"]) if lam else None
            hk = ("hist", tid)
            if hk not in cache:
                cache[hk] = soccer.team_matches(str(tid), 10)
            vals = []
            for mt in cache[hk]:
                for r in mt["summary"].get("rosters", []):
                    if str(r["team"]["id"]) == str(tid):
                        for a in r.get("roster", []):
                            if str(a["athlete"]["id"]) == pid and (a.get("starter") or a.get("subbedIn")):
                                v = {x["name"]: x.get("value") for x in a.get("stats", [])}.get(ROSTER_STAT[key])
                                if v is not None:
                                    vals.append(v)
            ho, hu = sum(v > p["line"] for v in vals), sum(v < p["line"] for v in vals)
            if mk_over:
                note += f"DraftKings implies {lam:.1f}" + (f", push {mk_over[2]:.0%}" if mk_over[2] else "")
            else:
                note += "no DraftKings ladder for this player (often means not expected to start)"
            o, u, pu = mk_over if mk_over else (None, None, 0.0)
            row = _finish(p, key, "soccer", None, None, pu, ho, hu, mk_over=None if not mk_over else o / max(o + u, 1e-9), notes=note)
            out.append({**row, **base, "proj": lam})
        except Exception as e:  # one bad lookup shouldn't sink the board
            out.append({**p, "error": f"{type(e).__name__}: {e}"[:80]})
    return out


_GOL_IDS: dict = {}


def gol_id(name: str) -> str | None:
    """gol.gg player id from the player list embedded in every gol.gg page."""
    if not _GOL_IDS:
        h = lol._page("https://gol.gg/tournament/list/")
        for pid, nm in re.findall(r"value:\s*'p_(\d+)',\s*name:\s*'([^']+?) - [A-Z]{2}'", h):
            _GOL_IDS.setdefault(nm.lower(), pid)
    return _GOL_IDS.get(str(name).lower())


def price_lol(props: list[dict]) -> list[dict]:
    """LoL 'MAPS 1-3 Kills': lol.py model (bo3.gg series odds, gol.gg games) + series-level history."""
    out, matches = [], None
    for p in props:
        if p["stat"] != "MAPS 1-3 Kills" or "+" in str(p["player"]):
            out.append({**p, "error": "stat not priced yet"})
            continue
        try:
            pid = gol_id(p["player"])
            if not pid:
                out.append({**p, "error": "player not found on gol.gg"})
                continue
            games = lol.player_games(pid)
            if matches is None:
                matches = []
                for st in ("upcoming", "current"):
                    matches += _get(f"{lol.BO3}/matches?page%5Blimit%5D=100&sort=start_date&filter%5Bmatches.status%5D%5Bin%5D={st}"
                                    f"&filter%5Bmatches.discipline_id%5D%5Beq%5D=3&with=teams").get("results", [])
            # his team = the bo3 side whose name runs through his recent series titles; the opponent must
            # then match PrizePicks' opponent tag (an abbreviation like 'BFX' or a name like 'Galions')
            titles = " ".join(g["title"].lower() for g in games[:15])
            words = lambda n: [w for w in re.findall(r"[a-z0-9]+", (n or "").lower()) if len(w) > 1]
            hits = lambda n: sum(titles.count(w) for w in words(n))
            opp = str(p["opp"]).lower()
            def opp_ok(n):
                n = (n or "").lower()
                initials = "".join(w[0] for w in words(n))
                compact = re.sub(r"[^a-z0-9]", "", n)
                it = iter(compact)
                abbrev = bool(opp) and opp[0] == compact[:1] and all(ch in it for ch in re.sub(r"[^a-z0-9]", "", opp))  # 'bfx' in 'bnkfearx'
                return opp in n or any(opp in w or w in opp for w in words(n) if len(w) > 2) or opp == initials or abbrev or \
                    difflib.SequenceMatcher(None, opp, compact).ratio() > 0.6
            def score(m):
                a, b = (m.get("team1") or {}).get("name"), (m.get("team2") or {}).get("name")
                return max((hits(a) > 0) + opp_ok(b), (hits(b) > 0) + opp_ok(a))
            m = max(matches, key=score) if matches else None
            if not m or score(m) < 2 or not (m.get("bet_updates") or {}).get("team_1", {}).get("coeff"):
                out.append({**p, "error": "match/odds not found on bo3.gg"})
                continue
            if m.get("status") != "upcoming":
                out.append({**p, "error": "match already under way"})
                continue
            bo = m.get("bo_type") or 5
            ps, team = lol.team_series_p(m, games)
            pg = lol.per_game_p(ps, bo)
            r = lol.price(games, pg, bo, p["line"])
            o, u, n = lol.history(games, p["line"])
            note = f"median {r['median']:.0f}, {team} series {ps:.0%} (per game {pg:.0%}), Bo{bo}; {n} series of history"
            row = _finish(p, "kills_m123", "lol", r["p_over"], r["p_under"], r["p_push"], o, u, notes=note)
            out.append({**row, "event_id": str(m["id"]), "player_id": pid, "proj": r["median"], "script": f"lol:{m['id']}"})
        except Exception as e:
            out.append({**p, "error": f"{type(e).__name__}: {str(e)[:60]}"})
    return out


def price_board(props: list[dict]) -> list[dict]:
    """Price props from any mix of leagues: each league goes to its own pricer."""
    out = []
    for lg in dict.fromkeys(p["league"] for p in props):
        batch = [p for p in props if p["league"] == lg]
        if lg == "CS2":
            out += price_cs2(batch)
        elif lg in SOCCER:
            out += price_soccer(batch)
        elif lg == "LOL":
            out += price_lol(batch)
        else:
            out += [{**p, "error": "league not priced yet"} for p in batch]
    return out
