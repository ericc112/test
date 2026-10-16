"""Moneylines (game winners) and the 50 -> 1k challenge: python -m edge ml board|challenge

board: every NFL, college football, MLB, soccer and tennis game in the next few days with a moneyline, rated like a prop.
  market  DraftKings' moneyline from ESPN's scoreboard, de-vigged (soccer is 3-way: a draw loses a moneyline). With
          $ODDS_API_KEY set, every book's price instead: the consensus de-vigged and the best price per side.
  model   a simple, independent team model: NFL from points for/against per game (shrunk early in the season), MLB from
          Pythagorean run records (log5 + home field), soccer from goals for/against per game (Poisson, with the draw),
          tennis from the tennis model (edge tennis). College football has no model yet: market only.
  final   the same blend, gates and 1-10 rating as props (segment sport:moneyline:side). A market-only price is a single
          source and rates Low; an even-money side (~50%) rates 1-4 however it is priced. That's honest: a moneyline near
          +100 is a coin flip, and the rating measures the chance it wins.
  ev      p_final x decimal price - 1 at the best price: what the challenge picks on.

challenge: the user's 50 -> 1k ladder, all of the challenge roll on one straight moneyline per step.
  At fair prices every route from 50 to 1000 succeeds about 50/1000 = 5% of the time; the vig takes some of that and only
  a real edge adds to it. The plan that wastes least: double at about even money (+100 to +130) until one more double
  would overshoot, then a favourite priced to land on the target (from 800, a -400 to make 1000).
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os

from . import grade as G

SITE = "https://site.api.espn.com/apis/site/v2/sports"
STAND = "https://site.api.espn.com/apis/v2/sports"
LEAGUES = {  # label -> (ESPN path, sport key for logging/grading)
    "NFL": ("football/nfl", "nfl"), "CFB": ("football/college-football", "cfb"), "MLB": ("baseball/mlb", "mlb"),
}
SOCCER = {"EPL": "eng.1", "La Liga": "esp.1", "Serie A": "ita.1", "Bundesliga": "ger.1", "Ligue 1": "fra.1", "MLS": "usa.1",
          "Liga MX": "mex.1", "UCL": "uefa.champions", "Europa": "uefa.europa", "Eredivisie": "ned.1", "Primeira": "por.1",
          "Championship": "eng.2", "NWSL": "usa.nwsl", "Brasileirão": "bra.1", "Argentina": "arg.1"}
DAYS = 4
HFA = {"nfl": 1.5, "cfb": 2.5}        # points
SIGMA = {"nfl": 13.5, "cfb": 15.5}    # final-margin spread, points
MLB_HOME_LOGIT = 0.16                 # ~54% home win rate
SOCCER_HOME = 1.12                    # home goals multiplier (away divided by it)


def _num(o) -> float | None:
    try:
        s = str(o).strip().upper()
        return 100.0 if s in ("EVEN", "EV") else float(s.replace("+", ""))
    except (TypeError, ValueError):
        return None


def implied(am: float) -> float:
    return 100 / (am + 100) if am > 0 else -am / (-am + 100)


def decimal(am: float) -> float:
    return 1 + (am / 100 if am > 0 else 100 / -am)


def american(p: float) -> int:
    p = min(0.995, max(0.005, p))
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))


def devig(prices: dict) -> dict:
    """Proportional de-vig of 2- or 3-way prices: {outcome: american} -> {outcome: fair p}."""
    imp = {k: implied(v) for k, v in prices.items() if v is not None}
    s = sum(imp.values())
    return {k: v / s for k, v in imp.items()} if s else {}


def _phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# ------------------------------------------------------------------ standings-based team models
def _entries(d: dict) -> list:
    out = []
    if "standings" in d:
        out += d["standings"].get("entries", [])
    for c in d.get("children", []):
        out += _entries(c)
    return out


def standings(path: str, cache: dict) -> dict:
    """{team id: {gp, pf, pa}} from ESPN standings (the first block of stats: the overall record)."""
    if path in cache:
        return cache[path]
    out = {}
    try:
        d = G._get(f"{STAND}/{path}/standings")
    except Exception:
        cache[path] = out
        return out
    for e in _entries(d):
        st = {}
        for s in e.get("stats", []):
            st.setdefault(s.get("name"), s.get("value"))
        gp = st.get("gamesPlayed") or sum(st.get(k) or 0 for k in ("wins", "losses", "ties"))
        if gp and st.get("pointsFor") is not None:
            out[str(e["team"]["id"])] = {"gp": float(gp), "pf": float(st["pointsFor"]), "pa": float(st.get("pointsAgainst") or 0)}
    cache[path] = out
    return out


def model_football(sport: str, home: dict, away: dict, neutral: bool, table: dict) -> tuple[float | None, int, str]:
    h, a = table.get(home["id"]), table.get(away["id"])
    if not h or not a:
        return None, 0, ""
    def rating(t):                                # points per game margin, shrunk toward 0 by 4 games
        return (t["pf"] - t["pa"]) / t["gp"] * t["gp"] / (t["gp"] + 4)
    margin = rating(h) - rating(a) + (0 if neutral else HFA[sport])
    p = _phi(margin / SIGMA[sport])
    return p, int(min(h["gp"], a["gp"])), f"margin {margin:+.1f} from points per game"


def model_mlb(home: dict, away: dict, table: dict) -> tuple[float | None, int, str]:
    h, a = table.get(home["id"]), table.get(away["id"])
    if not h or not a:
        return None, 0, ""
    def pyth(t):
        return t["pf"] ** 1.83 / (t["pf"] ** 1.83 + t["pa"] ** 1.83)
    ph, pa = pyth(h), pyth(a)
    p = (ph - ph * pa) / (ph + pa - 2 * ph * pa)
    p = 1 / (1 + math.exp(-(math.log(p / (1 - p)) + MLB_HOME_LOGIT)))
    return p, int(min(h["gp"], a["gp"])), f"Pythagorean {ph:.3f} vs {pa:.3f} (starters not modelled)"


def model_soccer(home: dict, away: dict, neutral: bool, table: dict) -> tuple[dict | None, int, str]:
    h, a = table.get(home["id"]), table.get(away["id"])
    if not h or not a or not table:
        return None, 0, ""
    gp = sum(t["gp"] for t in table.values())
    mu = sum(t["pf"] for t in table.values()) / gp if gp else 1.35
    def rate(x, n):                                # per-game rate relative to the league, shrunk by 5 games
        return ((x / n / mu) * n + 5) / (n + 5) if n else 1.0
    adv = 1.0 if neutral else SOCCER_HOME
    lh = mu * rate(h["pf"], h["gp"]) * rate(a["pa"], a["gp"]) * adv
    la = mu * rate(a["pf"], a["gp"]) * rate(h["pa"], h["gp"]) / adv
    pois = lambda lam, k: math.exp(-lam) * lam ** k / math.factorial(k)
    ph = pd = pa_ = 0.0
    for i in range(11):
        for j in range(11):
            q = pois(lh, i) * pois(la, j)
            if i > j:
                ph += q
            elif i == j:
                pd += q
            else:
                pa_ += q
    s = ph + pd + pa_
    return {"home": ph / s, "draw": pd / s, "away": pa_ / s}, int(min(h["gp"], a["gp"])), f"expected goals {lh:.2f}-{la:.2f}"


# ------------------------------------------------------------------ games and prices
def _team(c: dict) -> dict:
    t = c.get("team") or {}
    return {"id": str(t.get("id")), "name": t.get("displayName") or t.get("name"), "abbr": t.get("abbreviation") or t.get("shortDisplayName"),
            "record": ((c.get("records") or [{}])[0]).get("summary")}


def _dk(comp: dict) -> dict:
    for o in comp.get("odds") or []:
        if not isinstance(o, dict):
            continue
        ml = o.get("moneyline") or {}
        pr = {}
        for k in ("home", "away", "draw"):
            leg = ml.get(k) if isinstance(ml.get(k), dict) else {}
            pr[k] = _num((leg.get("close") or {}).get("odds") or (leg.get("open") or {}).get("odds"))
        if pr.get("home") is None:
            pr["home"] = _num((o.get("homeTeamOdds") or {}).get("moneyLine"))
            pr["away"] = _num((o.get("awayTeamOdds") or {}).get("moneyLine"))
            pr["draw"] = _num((o.get("drawOdds") or {}).get("moneyLine"))
        pr = {k: v for k, v in pr.items() if v is not None}
        if pr.get("home") is not None and pr.get("away") is not None:
            return pr
    return {}


def team_games(now: dt.datetime, days: int = DAYS) -> list[dict]:
    out, seen = [], set()
    paths = [(lab, p, sp) for lab, (p, sp) in LEAGUES.items()] + [(lab, f"soccer/{slug}", "soccer") for lab, slug in SOCCER.items()]
    for lab, path, sport in paths:
        for k in range(days):
            day = (now + dt.timedelta(days=k)).strftime("%Y%m%d")
            q = f"?dates={day}" + ("&groups=80&limit=300" if sport == "cfb" else "")
            try:
                d = G._get(f"{SITE}/{path}/scoreboard{q}")
            except Exception:
                continue
            for e in d.get("events", []):
                comp = e["competitions"][0]
                if e["id"] in seen or comp["status"]["type"]["state"] != "pre":
                    continue
                cs = {c.get("homeAway"): c for c in comp.get("competitors", [])}
                if "home" not in cs or "away" not in cs:
                    continue
                seen.add(e["id"])
                out.append({"lg": lab, "sport": sport, "path": path, "id": e["id"], "start": e.get("date"), "name": e.get("name"),
                            "neutral": bool(comp.get("neutralSite")), "home": _team(cs["home"]), "away": _team(cs["away"]),
                            "prices": _dk(comp), "book": "DraftKings"})
    return out


def tennis_games() -> list[dict]:
    from . import tennis as T
    out = []
    try:
        ms = T.live_matches()
    except Exception:
        return out
    for s in ms:
        if s.get("state") != "pre" or len(s.get("ids") or []) != 2:
            continue
        out.append({"lg": f"{s['tour'].upper()}", "sport": "tennis", "path": "tennis", "id": f"{s['tour']}/{s['event_id']}/{s['comp_id']}",
                    "start": s.get("start") or s.get("date"), "name": f"{s['names'][0]} vs {s['names'][1]}", "neutral": True,
                    "home": {"id": s["ids"][0], "name": s["names"][0], "abbr": s["names"][0].split()[-1]},
                    "away": {"id": s["ids"][1], "name": s["names"][1], "abbr": s["names"][1].split()[-1]},
                    "prices": {}, "book": "", "tennis": s})
    return out


# ------------------------------------------------------------------ The Odds API (all books), when the key is set
ODDS_KEYS = {"NFL": "americanfootball_nfl", "CFB": "americanfootball_ncaaf", "MLB": "baseball_mlb", "EPL": "soccer_epl",
             "La Liga": "soccer_spain_la_liga", "Serie A": "soccer_italy_serie_a", "Bundesliga": "soccer_germany_bundesliga",
             "Ligue 1": "soccer_france_ligue_one", "MLS": "soccer_usa_mls", "Liga MX": "soccer_mexico_ligamx",
             "UCL": "soccer_uefa_champs_league", "Europa": "soccer_uefa_europa_league", "Eredivisie": "soccer_netherlands_eredivisie",
             "Primeira": "soccer_portugal_primeira_liga", "Championship": "soccer_efl_champ", "Brasileirão": "soccer_brazil_campeonato",
             "Argentina": "soccer_argentina_primera_division"}


def attach_books(games: list[dict]) -> int:
    """Every book's moneyline from The Odds API onto the games (consensus fair p and the best price per side)."""
    from . import oddsapi as O
    if not O.enabled():
        return 0
    n = 0
    keys = dict(ODDS_KEYS)
    try:
        for s in O._fetch("/sports", {}, 3600):
            if s.get("active") and s["key"].startswith(("tennis_atp", "tennis_wta")):
                keys[s["key"]] = s["key"]
    except Exception:
        pass
    for lab, key in keys.items():
        try:
            evs = O._fetch(f"/sports/{key}/odds", {"regions": "us,eu", "markets": "h2h", "oddsFormat": "american"}, 600)
        except Exception:
            continue
        for ev in evs:
            g = next((g for g in games if (g["lg"] == lab or (key.startswith("tennis") and g["sport"] == "tennis"))
                      and _same(g["home"]["name"], ev.get("home_team")) and _same(g["away"]["name"], ev.get("away_team"))), None)
            if not g:
                g = next((g for g in games if key.startswith("tennis") and g["sport"] == "tennis"
                          and _same(g["home"]["name"], ev.get("away_team")) and _same(g["away"]["name"], ev.get("home_team"))), None)
                flip = True
            else:
                flip = False
            if not g:
                continue
            books = {}
            for bk in ev.get("bookmakers", []):
                for m in bk.get("markets", []):
                    if m.get("key") != "h2h":
                        continue
                    pr = {}
                    for o in m.get("outcomes", []):
                        side = "draw" if o["name"].lower() == "draw" else \
                            ("home" if _same(o["name"], ev.get("home_team")) else "away")
                        if flip and side != "draw":
                            side = "away" if side == "home" else "home"
                        pr[side] = o.get("price")
                    if pr.get("home") is not None and pr.get("away") is not None:
                        books[bk["key"]] = pr
            if books:
                g["books"] = books
                n += 1
    return n


def _same(a: str | None, b: str | None) -> bool:
    import difflib
    import re
    import unicodedata
    def f(s):
        s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
        return re.sub(r"\b(fc|cf|sc|ac|afc|club|de|the)\b|[^a-z ]", " ", s).split()
    ta, tb = set(f(a)), set(f(b))
    return bool(ta & tb) and (len(ta & tb) >= min(len(ta), len(tb), 2) or difflib.SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio() > 0.6)


# ------------------------------------------------------------------ pricing
def price_game(g: dict, cache: dict, adj: dict) -> dict:
    from .blend import final_probability, rating
    sport = g["sport"]
    sides = ["home", "away"] + (["draw"] if sport == "soccer" else [])
    # market: every book's consensus, else DraftKings
    fair, best = {}, {}
    if g.get("books"):
        from .oddsapi import SHARP
        acc = {s: [] for s in sides}
        for bk, pr in g["books"].items():
            fv = devig({s: pr.get(s) for s in sides if pr.get(s) is not None})
            w = SHARP.get(bk, 1.0)
            for s, p in fv.items():
                acc[s].append((w, p))
                if s not in best or decimal(pr[s]) > decimal(best[s][0]):
                    best[s] = (pr[s], bk)
        for s, lst in acc.items():
            if lst:
                z = sum(w * math.log(p / (1 - p)) for w, p in lst) / sum(w for w, _ in lst)
                fair[s] = 1 / (1 + math.exp(-z))
        tot = sum(fair.values())
        fair = {s: p / tot for s, p in fair.items()} if tot else {}
        book = f"best of {len(g['books'])} books"
    elif g.get("prices"):
        fair = devig({s: g["prices"].get(s) for s in sides if g["prices"].get(s) is not None})
        best = {s: (g["prices"][s], "DraftKings") for s in sides if g["prices"].get(s) is not None}
        book = "DraftKings"
    else:
        book = ""
    # model
    model, n, why = {}, 0, ""
    if sport in ("nfl", "mlb"):                  # college football: no model yet (standings mix overall and conference)
        table = standings(g["path"], cache)
        p, n, why = (model_mlb(g["home"], g["away"], table) if sport == "mlb"
                     else model_football(sport, g["home"], g["away"], g["neutral"], table))
        if p is not None:
            model = {"home": p, "away": 1 - p}
    elif sport == "soccer":
        pr, n, why = model_soccer(g["home"], g["away"], g["neutral"], standings(g["path"], cache))
        if pr:
            model = pr
    elif sport == "tennis":
        from . import tennis as T
        s = g["tennis"]
        try:
            pre = T.prematch(s["ids"][0], s["ids"][1], s["tour"], s["surface"], s["bo"], s["event"])
            model = {"home": pre["p_model"], "away": 1 - pre["p_model"]}
            n, why = 25, f"tennis model (Elo, surface, form): {pre['p_model']:.0%}"
        except Exception:
            model = {}
    out = []
    for s in sides:
        team = g["home"] if s == "home" else g["away"] if s == "away" else {"name": "Draw", "abbr": "Draw", "id": "draw"}
        pm, pmod = fair.get(s), model.get(s)
        if pm is None and pmod is None:
            continue
        est = final_probability(pmod, pm, None, segment=f"{sport}:moneyline:{s if s == 'draw' else 'team'}", hist_n=n, adj=adj)
        price = best.get(s, (None, ""))[0]
        ev = round(est.p * decimal(price) - 1, 4) if price is not None else None
        out.append({"side": s, "team": team["name"], "abbr": team.get("abbr"), "team_id": team.get("id"), "price": price,
                    "book": best.get(s, (None, ""))[1], "p_mkt": None if pm is None else round(pm, 4),
                    "p_model": None if pmod is None else round(pmod, 4), "p": est.p, "conf": est.confidence,
                    "rating": rating(est.p, est.confidence, pm), "ev": ev, "fair": american(est.p)})
    return {"lg": g["lg"], "sport": sport, "id": g["id"], "start": g["start"], "name": g["name"], "neutral": g["neutral"],
            "home": g["home"], "away": g["away"], "book": book, "model": why, "sides": out}


def board(now: dt.datetime | None = None, days: int = DAYS, tennis: bool = True) -> dict:
    from .blend import load_adjustments
    now = now or dt.datetime.now(dt.timezone.utc)
    adj = dict(load_adjustments())
    adj["calibration"] = {}                     # the props' calibration maps were fitted on props, not game winners
    games = team_games(now, days) + (tennis_games() if tennis else [])
    attach_books(games)
    cache, rows = {}, []
    for g in games:
        try:
            r = price_game(g, cache, adj)
        except Exception as e:
            r = {"lg": g["lg"], "sport": g["sport"], "id": g["id"], "start": g["start"], "name": g["name"], "error": type(e).__name__}
        if r.get("sides"):
            rows.append(r)
    rows.sort(key=lambda r: (r.get("start") or "", r["lg"]))
    return {"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "games": rows,
            "source": "every book (The Odds API)" if any(r.get("book", "").startswith("best") for r in rows) else "DraftKings via ESPN"}


# ------------------------------------------------------------------ the challenge
def step_plan(roll: float, target: float) -> dict:
    """What this step needs: double at about even money, or a favourite that lands on the target."""
    m = target / roll if roll else float("inf")
    if m <= 1:
        return {"need": 1.0, "lo": None, "hi": None, "kind": "done"}
    if m >= 2:
        return {"need": 2.0, "lo": 2.0, "hi": 2.35, "kind": "double"}       # +100 to +135
    return {"need": m, "lo": m, "hi": m + 0.12, "kind": "finish"}


def candidates(b: dict, roll: float, target: float, now: dt.datetime | None = None, n: int = 5,
               min_lead_min: int = 15, max_ahead_h: int = 48) -> list[dict]:
    now = now or dt.datetime.now(dt.timezone.utc)
    plan = step_plan(roll, target)
    if plan["kind"] == "done":
        return []
    out = []
    for g in b.get("games", []):
        try:
            st = dt.datetime.fromisoformat(str(g["start"]).replace("Z", "+00:00"))
        except ValueError:
            continue
        mins = (st - now).total_seconds() / 60
        if mins < min_lead_min or mins > max_ahead_h * 60:
            continue
        for s in g["sides"]:
            if s["side"] == "draw" or s.get("price") is None or s.get("p_mkt") is None:
                continue
            d = decimal(s["price"])
            if not (plan["lo"] <= d <= plan["hi"]):
                continue
            # our edge is only as good as the model behind it: the model must lean this way too, and not by a mile
            # (a 15-point gap between a standings model and the market is the model being wrong, not the book)
            if s.get("p_model") is None or s["p_model"] < s["p_mkt"] or s["p_model"] - s["p_mkt"] > 0.15:
                continue
            if (s.get("ev") or 0) < 0:                   # the price must beat our chance, or the step loses ground
                continue
            out.append({"lg": g["lg"], "sport": g["sport"], "event_id": g["id"], "start": g["start"], "game": g["name"],
                        "team": s["team"], "team_id": s["team_id"], "side": s["side"], "price": s["price"], "book": s["book"],
                        "p": s["p"], "p_mkt": s["p_mkt"], "p_model": s["p_model"], "ev": s["ev"], "rating": s["rating"],
                        "to": round(roll * d, 2), "kind": plan["kind"]})
    # the likelier winner first (every candidate pays about the same), then the better price
    out.sort(key=lambda c: (-round(c["p"], 2), -(c["ev"] or -1)))
    return out[:n]


def chance(roll: float, target: float, p_step: float | None = None, price: float | None = None) -> float:
    """Rough chance of reaching the target from here: at fair prices, roll/target; the current step at its own odds."""
    if roll >= target:
        return 1.0
    if p_step is not None and price is not None:
        after = roll * decimal(price)
        return round(p_step * min(1.0, after / target), 4)
    return round(roll / target, 4)


def ml_result(sport: str, event_id: str, team_id: str, cache: dict) -> tuple[str, float | None]:
    return G.ml_value(sport, event_id, team_id, cache)


def advance(state: dict, b: dict, now: dt.datetime | None = None) -> dict:
    """Grade the open step if its game is final, move the roll, and list the next step's candidates."""
    now = now or dt.datetime.now(dt.timezone.utc)
    st = json.loads(json.dumps(state))                  # never edit the caller's copy
    st.setdefault("start", 50.0)
    st.setdefault("target", 1000.0)
    st.setdefault("roll", st["start"])
    st.setdefault("history", [])
    st.setdefault("status", "active")
    op = st.get("open")
    if op and op.get("status") in (None, "pending", "placed"):
        try:
            state_, v = ml_result(op["sport"], str(op["event_id"]), str(op["team_id"]), {})
        except Exception as e:
            state_, v = "pending", None
            op["note"] = f"grade error {type(e).__name__}"
        if state_ in ("final", "done"):
            won = v == 1
            op["status"] = "won" if won else "lost"
            op["graded"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
            st["roll"] = round(op["stake"] * decimal(op["price"]), 2) if won else round(st["roll"] - op["stake"], 2)
            op["roll_after"] = st["roll"]
            st["history"].append(op)
            st["open"] = None
            if not won and st["roll"] <= 0.5:
                st["status"] = "busted"
            elif st["roll"] >= st["target"]:
                st["status"] = "won"
        elif state_ == "void":
            op["status"] = "void"
            st["history"].append(op)
            st["open"] = None
    st["step"] = len([h for h in st["history"] if h.get("status") in ("won", "lost")]) + 1
    if st["status"] == "active" and not st.get("open"):
        st["candidates"] = candidates(b, st["roll"], st["target"], now)
        st["plan"] = step_plan(st["roll"], st["target"])
    else:
        st["candidates"] = []
    st["chance"] = chance(st["roll"], st["target"], st["open"]["p"] if st.get("open") else None,
                          st["open"]["price"] if st.get("open") else None) if st["status"] == "active" else (1.0 if st["status"] == "won" else 0.0)
    st["updated"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return st


def log_rows(b: dict) -> list[str]:
    """Every game is logged once, on its likelier side (a team; never the draw), so moneylines are graded and learned."""
    import csv
    from . import tier
    path = os.path.join(os.path.dirname(__file__), "..", "data", "bets.csv")
    have = {(r["event_id"], r["player_id"], r["market"]) for r in csv.DictReader(open(path))}
    added = []
    for g in b.get("games", []):
        teams = [s for s in g["sides"] if s["side"] != "draw"]
        if not teams:
            continue
        s = max(teams, key=lambda x: x["p"])
        if (str(g["id"]), str(s["team_id"]), "moneyline") in have:
            continue
        opp = next((t for t in teams if t is not s), None)
        row = {"date": dt.date.today().isoformat(), "sport": g["sport"], "event": g["name"], "event_id": g["id"],
               "player": s["team"], "player_id": s["team_id"], "market": "moneyline", "line": 0.5, "side": "over",
               "book": s.get("book") or "", "price": s.get("price") if s.get("price") is not None else "",
               "p_model": s.get("p_model") if s.get("p_model") is not None else "", "p_market": s.get("p_mkt") if s.get("p_mkt") is not None else "",
               "p_final": s["p"], "confidence": s["conf"], "action": "lean" if s["rating"] >= 5 else "pass",
               "segment": f"{g['sport']}:moneyline:team", "group": f"{g['sport']}:{g['id']}", "status": "pending",
               "notes": f"edge ml; {g['lg']} {g['name']}; {g.get('model') or 'market only'}; start {g['start']}"
                        + (f"; vs {opp['team']} {opp.get('price')}" if opp else "")}
        try:
            added.append(tier.add_row(row) if hasattr(tier, "add_row") else _append(path, row))
        except Exception:
            continue
    return added


def _append(path: str, row: dict) -> str:
    import csv
    rows = list(csv.DictReader(open(path)))
    fields = list(rows[0].keys()) if rows else list(row.keys())
    nid = str(max((int(r["id"]) for r in rows if str(r.get("id", "")).isdigit()), default=0) + 1)
    out = {k: "" for k in fields}
    out.update({k: v for k, v in row.items() if k in fields})
    out["id"] = nid
    with open(path, "a", newline="") as f:
        csv.DictWriter(f, fieldnames=fields).writerow(out)
    return nid


def log_step(op: dict, step: int) -> str:
    """The challenge step the user locked in: a real bet in bets.csv (their entry, the whole challenge roll)."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "bets.csv")
    row = {"date": dt.date.today().isoformat(), "sport": op["sport"], "event": op.get("game", ""), "event_id": op["event_id"],
           "player": op["team"], "player_id": op["team_id"], "market": "moneyline", "line": 0.5, "side": "over",
           "book": op.get("book") or "", "price": op["price"], "payout_mult": round(decimal(op["price"]), 4),
           "entry_id": f"challenge-{step}", "stake": op["stake"], "p_model": op.get("p_model") if op.get("p_model") is not None else "",
           "p_market": op.get("p_mkt") if op.get("p_mkt") is not None else "", "p_final": op.get("p") or "",
           "confidence": "", "action": "user_entry", "segment": f"{op['sport']}:moneyline:team",
           "group": f"{op['sport']}:{op['event_id']}", "status": "pending",
           "notes": f"50-to-1k challenge step {step}; start {op.get('start')}"}
    return _append(path, row)


def cli(args) -> None:
    if args.action == "board":
        b = board(days=args.days, tennis=not args.no_tennis)
        json.dump(b, open(args.out, "w"), separators=(",", ":"))
        n = len(b["games"])
        print(f"{n} games ({b['source']}) -> {args.out}")
        if args.log:
            ids = log_rows(b)
            print(f"logged {len(ids)} new moneyline rows")
        top = sorted((dict(s, game=g["name"], lg=g["lg"], start=g["start"]) for g in b["games"] for s in g["sides"]),
                     key=lambda x: (-x["rating"], -x["p"]))[:12]
        for x in top:
            pr = f"{x['price']:+.0f}" if x.get("price") is not None else "no price"
            print(f"{x['rating']:>2}/10 {x['lg']:12s} {x['team']} ({pr}, fair {x['fair']:+d}) {x['p']:.0%} "
                  f"[market {x['p_mkt'] if x['p_mkt'] is not None else '-'} model {x['p_model'] if x['p_model'] is not None else '-'}] {x['game']}")
        return
    if args.action == "challenge":
        st = {}
        if args.state and os.path.exists(args.state):
            st = json.load(open(args.state))
            st = st.get("data", st)
        b = json.load(open(args.board))
        if st.get("open") and not st["open"].get("bets_id"):
            st["open"]["bets_id"] = log_step(st["open"], len([h for h in st.get("history", []) if h.get("status") in ("won", "lost")]) + 1)
        st = advance(st, b)
        json.dump(st, open(args.out, "w"), separators=(",", ":"))
        print(f"challenge: {st['status']}, roll ${st['roll']:.2f} -> ${st['target']:.0f}, step {st['step']}, chance from here ~{st['chance']:.1%}")
        if st.get("open"):
            o = st["open"]
            print(f"open: {o['team']} ML {o['price']:+.0f} for ${o['stake']:.2f} ({o['game']}, {o['start']}) #{o.get('bets_id')}")
        for c in st.get("candidates", []):
            print(f"  candidate: {c['team']} ML {c['price']:+.0f} {c['p']:.0%} (market {c['p_mkt']:.0%}, model {c['p_model']:.0%}) "
                  f"EV {c['ev']:+.1%} -> ${c['to']:.2f} | {c['lg']} {c['game']} {c['start']}")
