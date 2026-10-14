"""Tennis match winner, pre-match and live (ESPN results and live scores, no keys; the price comes from your book).

Pre-match. Surface Elo (overall and surface ratings, FiveThirtyEight K schedule, blended 50/50) from every ATP and
WTA singles result ESPN has since 2024, then a logistic layer fitted on past matches for what Elo misses: fatigue
(sets played in the last 3 and 7 days), form (results vs Elo expectation over the last 10), head-to-head (shrunk
hard: it adds little beyond ratings), rust (long layoff) and best-of-5 (the better player's edge grows over 5 sets).
The layer is fitted on one season and scored on the next one it never saw (`edge tennis backtest`).

Live. The score is most of the information. The chance a player wins from any score is computed exactly with the
point -> game -> tiebreak -> set -> match Markov chain. Each player's chance of winning a point on serve is set so
the chain reproduces the pre-match probability, with the two serve levels' sum taken from how often each player
plays tiebreaks (big servers hold more, so every break matters more). "Momentum" is fitted from data, not
assumed: a shift of the serve probabilities per set of lead, chosen by how often set-one winners really went on
to win compared with what the chain said. Live serve points from your app, if you pass them, update each serve
probability (Bayesian, worth SERVE_PRIOR points of prior).
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import csv
import datetime as dt
import difflib
import json
import math
import os
import time
from functools import lru_cache

import numpy as np

from .blend import HERE
from .grade import _get

SB = "https://site.api.espn.com/apis/site/v2/sports/tennis/{tour}/scoreboard"
CORE = "https://sports.core.api.espn.com/v2/sports/tennis/leagues/{tour}/events/{event}/competitions/{comp}"
DATA = os.path.join(HERE, "data", "tennis")
MATCHES = os.path.join(DATA, "matches.csv")
MODEL = os.path.join(DATA, "model.json")
CACHE = os.path.join(HERE, ".cache", "tennis")
START = dt.date(2024, 1, 1)
STEP_DAYS = 4                 # scoreboard?dates= returns every event live that day; events last 7+ days
SLAMS = ("australian open", "roland garros", "french open", "wimbledon", "us open")
SERVE_PRIOR = 80              # live serve stats: prior worth this many points
TB_SHRINK = 30                # tiebreak index: prior worth ~30 sets (6 expected tiebreaks at a 20% rate)
FIELDS = ["date", "tour", "comp_id", "event_id", "event", "round", "city", "surface", "bo",
          "w_id", "w_name", "l_id", "l_name", "w_games", "l_games", "tb", "retired"]

# ------------------------------------------------------------------ surface (ESPN doesn't publish it)
CLAY = ("roland garros", "french open", "monte carlo", "monte-carlo", "madrid", "internazionali", "italian open", "rome",
        "roma", "barcelona", "hamburg", "munich", "bmw open", "estoril", "marrakech", "grand prix hassan", "houston",
        "u.s. men's clay", "bucharest", "geneva", "lyon", "bastad", "båstad", "nordea", "gstaad", "kitzbuhel", "kitzbühel",
        "umag", "croatia open", "buenos aires", "argentina open", "rio open", "rio de janeiro", "chile open", "santiago",
        "cordoba", "córdoba", "charleston", "credit one", "bogota", "bogotá", "rabat", "strasbourg", "palermo", "prague",
        "budapest", "lausanne", "iasi", "iași", "parma", "cluj", "bol ", "makarska", "rothesay open nottingham",
        "oeiras", "porsche tennis grand prix", "catalonia", "valencia", "rouen", "saint-malo", "kozerki", "contrexeville")
GRASS = ("wimbledon", "queen", "halle", "terra wortmann", "hertogenbosch", "libema", "mallorca", "eastbourne",
         "birmingham", "bad homburg", "berlin", "nottingham", "newport", "hall of fame", "stuttgart", "boss open")


def surface(event: str, city: str, date: str) -> str:
    """Clay/grass by tournament or city name and season; everything else is hard (indoor or out)."""
    s = f"{event} {city}".lower()
    m, day = int(date[5:7]), int(date[8:10])
    if any(k in s for k in GRASS) and (m in (6, 7) or (m == 5 and day >= 20)):   # grass qualifying starts late May
        return "grass"
    if any(k in s for k in CLAY) and m in (2, 3, 4, 5, 6, 7, 8, 9):
        return "clay"
    return "hard"


# ------------------------------------------------------------------ history from ESPN
def _parse(ev: dict, comp: dict, group: str) -> dict | None:
    if (comp.get("status", {}).get("type", {}).get("state") != "post") or "Singles" not in group:
        return None
    cs = comp.get("competitors") or []
    if len(cs) != 2 or not all(c.get("linescores") for c in cs):
        return None                                   # walkover or no score
    w = next((c for c in cs if c.get("winner")), None)
    if w is None:
        return None
    lo = cs[1] if cs[0] is w else cs[0]
    wg = [int(x.get("value") or 0) for x in w["linescores"]]
    lg = [int(x.get("value") or 0) for x in lo["linescores"]]
    if len(wg) != len(lg):
        return None
    tour = "atp" if group.startswith("Men") else "wta"
    rnd = (comp.get("round") or {}).get("displayName", "")
    slam = any(k in ev.get("name", "").lower() for k in SLAMS)
    bo = 5 if tour == "atp" and slam and "qualif" not in rnd.lower() else 3
    need = bo // 2 + 1
    sets_w = sum(1 for a, b in zip(wg, lg) if a > b)
    city = (comp.get("venue") or {}).get("fullName", "")
    d = comp.get("date", ev.get("date", ""))[:10]
    return {"date": d, "tour": tour, "comp_id": str(comp["id"]), "event_id": ev["id"], "event": ev.get("name", ""),
            "round": rnd, "city": city, "surface": surface(ev.get("name", ""), city, d), "bo": bo,
            "w_id": str(w["id"]), "w_name": w["athlete"]["displayName"], "l_id": str(lo["id"]),
            "l_name": lo["athlete"]["displayName"], "w_games": ",".join(map(str, wg)), "l_games": ",".join(map(str, lg)),
            "tb": sum(1 for a, b in zip(wg, lg) if {a, b} == {7, 6}), "retired": int(sets_w < need)}


def scoreboard(tour: str, date: str | None = None) -> dict:
    url = SB.format(tour=tour) + (f"?dates={date}" if date else "")
    for i in range(3):
        try:
            return _get(url)
        except Exception:
            if i == 2:
                raise
            time.sleep(2 * (i + 1))


def _fetch_day(day: dt.date) -> list[dict]:
    """All finished singles matches of every event running on `day` (both tours). Past days are cached."""
    key = os.path.join(CACHE, f"{day:%Y%m%d}.json")
    old = day < dt.date.today() - dt.timedelta(days=21)
    if old and os.path.exists(key):
        with open(key) as f:
            return json.load(f)
    rows = {}
    for tour in ("atp", "wta"):
        for ev in scoreboard(tour, f"{day:%Y%m%d}").get("events", []):
            for g in ev.get("groupings", []):
                for c in g.get("competitions", []):
                    r = _parse(ev, c, g.get("grouping", {}).get("displayName", ""))
                    if r:
                        rows[r["comp_id"]] = r
    out = list(rows.values())
    if old:
        os.makedirs(CACHE, exist_ok=True)
        with open(key, "w") as f:
            json.dump(out, f)
    return out


def load_matches() -> list[dict]:
    if not os.path.exists(MATCHES):
        return []
    with open(MATCHES, newline="") as f:
        return list(csv.DictReader(f))


def update_history(log=print) -> int:
    """Fetch new results (incremental: from three weeks before the latest stored match) and rewrite matches.csv."""
    have = {r["comp_id"]: r for r in load_matches()}
    last = max((r["date"] for r in have.values()), default=None)
    start = max(START, dt.date.fromisoformat(last) - dt.timedelta(days=21)) if last else START
    days = []
    d = start
    while d <= dt.date.today():
        days.append(d)
        d += dt.timedelta(days=STEP_DAYS)
    if days[-1] != dt.date.today():
        days.append(dt.date.today())
    log(f"fetching {len(days)} scoreboard days from {start} ...")
    new = 0
    with cf.ThreadPoolExecutor(6) as ex:
        for rows in ex.map(_fetch_day, days):
            for r in rows:
                new += r["comp_id"] not in have
                have[r["comp_id"]] = r
    out = sorted(have.values(), key=lambda r: (r["date"], r["comp_id"]))
    os.makedirs(DATA, exist_ok=True)
    with open(MATCHES, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r[k] for k in FIELDS} for r in out)
    log(f"{len(out)} matches stored ({new} new)")
    return new


# ------------------------------------------------------------------ the Markov chain (exact, no simulation)
def other(s: str) -> str:
    return "B" if s == "A" else "A"


def p_game(p: float, i: int = 0, j: int = 0) -> float:
    """Server wins the game from i-j points (0,1,2,3 = 0,15,30,40), winning each point on serve with p."""
    q = 1 - p
    deuce = p * p / (p * p + q * q)

    @lru_cache(None)
    def f(a, b):
        if a >= 4 and a - b >= 2:
            return 1.0
        if b >= 4 and b - a >= 2:
            return 0.0
        if a >= 3 and b >= 3:
            return deuce if a == b else (p + q * deuce if a > b else p * deuce)
        return p * f(a + 1, b) + q * f(a, b + 1)
    return f(i, j)


def tb_server(first: str, played: int) -> str:
    """Tiebreak serve order: first server serves point 1, then two each."""
    return first if played == 0 or ((played - 1) // 2) % 2 == 1 else other(first)


def p_tiebreak(pa: float, pb: float, first: str, i: int = 0, j: int = 0, target: int = 7) -> float:
    """A wins the tiebreak from i-j (A's points first). pa, pb = each player's point-win chance on own serve."""
    w, l = pa * (1 - pb), (1 - pa) * pb
    level = w / (w + l)            # from any level score past target-1 the next two points are one serve each

    @lru_cache(None)
    def f(a, b):
        if a >= target and a - b >= 2:
            return 1.0
        if b >= target and b - a >= 2:
            return 0.0
        if a == b and a >= target - 1:
            return level
        x = pa if tb_server(first, a + b) == "A" else 1 - pb
        return x * f(a + 1, b) + (1 - x) * f(a, b + 1)
    return f(i, j)


def set_outcomes(pa: float, pb: float, ga: int, gb: int, srv: str, tb_target: int = 7, pts=(0, 0)) -> dict:
    """{(set winner, server of the next game): prob} from games ga-gb, `srv` serving now, the current game (or
    tiebreak) at pts = (A's points, B's points). The tiebreak counts as one game for the service rotation."""
    hold = {"A": p_game(pa), "B": p_game(pb)}

    @lru_cache(None)
    def f(x, y, s):
        if (x >= 6 and x - y >= 2) or (x == 7 and y == 6):
            return {("A", s): 1.0}
        if (y >= 6 and y - x >= 2) or (y == 7 and x == 6):
            return {("B", s): 1.0}
        if x == 6 and y == 6:
            t = p_tiebreak(pa, pb, s, target=tb_target)
            return {("A", other(s)): t, ("B", other(s)): 1 - t}
        a_wins = hold["A"] if s == "A" else 1 - hold["B"]
        return _mix([(a_wins, f(x + 1, y, other(s))), (1 - a_wins, f(x, y + 1, other(s)))])

    if pts == (0, 0):
        return f(ga, gb, srv)
    if ga == 6 and gb == 6:                    # tiebreak in progress: srv serves the next point
        played = pts[0] + pts[1]
        first = srv if tb_server("A", played) == "A" else other(srv)
        t = p_tiebreak(pa, pb, first, pts[0], pts[1], tb_target)
        return {("A", other(first)): t, ("B", other(first)): 1 - t}
    sp, rp = (pts[0], pts[1]) if srv == "A" else (pts[1], pts[0])
    h = p_game(pa if srv == "A" else pb, min(sp, 4), min(rp, 4))
    a_wins = h if srv == "A" else 1 - h
    return _mix([(a_wins, f(ga + 1, gb, other(srv))), (1 - a_wins, f(ga, gb + 1, other(srv)))])


def _mix(parts) -> dict:
    out = collections.defaultdict(float)
    for w, d in parts:
        for k, v in d.items():
            out[k] += w * v
    return dict(out)


def p_match(pa: float, pb: float, bo: int = 3, sa: int = 0, sb: int = 0, ga: int = 0, gb: int = 0, srv: str = "A",
            pts=(0, 0), final_tb: int = 7, form: float = 0.0) -> float:
    """A wins the match from sets sa-sb, games ga-gb, `srv` serving, current game at pts.
    form shifts both serve probabilities by `form` per set of lead (the fitted in-match form effect)."""
    need = bo // 2 + 1
    clip = lambda x: min(0.95, max(0.05, x))

    def probs(x, y):
        return clip(pa + form * (x - y)), clip(pb - form * (x - y))

    @lru_cache(None)
    def m(x, y, s):
        if x == need:
            return 1.0
        if y == need:
            return 0.0
        qa, qb = probs(x, y)
        tgt = final_tb if x == y == need - 1 else 7
        return sum(v * m(x + (w == "A"), y + (w == "B"), nxt) for (w, nxt), v in set_outcomes(qa, qb, 0, 0, s, tgt).items())

    if sa == need or sb == need:
        return float(sa == need)
    qa, qb = probs(sa, sb)
    tgt = final_tb if sa == sb == need - 1 else 7
    return sum(v * m(sa + (w == "A"), sb + (w == "B"), nxt)
               for (w, nxt), v in set_outcomes(qa, qb, ga, gb, srv, tgt, pts).items())


def p_prematch(pa: float, pb: float, bo: int = 3, final_tb: int = 7, form: float = 0.0) -> float:
    """Before the coin toss: either player may serve first."""
    return 0.5 * (p_match(pa, pb, bo, srv="A", final_tb=final_tb, form=form) +
                  p_match(pa, pb, bo, srv="B", final_tb=final_tb, form=form))


def p_tb_set(pa: float, pb: float) -> float:
    """Chance a set reaches 6-6 (either player serving first)."""
    hold = {"A": p_game(pa), "B": p_game(pb)}

    @lru_cache(None)
    def f(x, y, s):
        if x == 6 and y == 6:
            return 1.0
        if (x >= 6 and x - y >= 2) or (y >= 6 and y - x >= 2):
            return 0.0
        a = hold["A"] if s == "A" else 1 - hold["B"]
        return a * f(x + 1, y, other(s)) + (1 - a) * f(x, y + 1, other(s))
    return 0.5 * (f(0, 0, "A") + f(0, 0, "B"))


def solve_serve(p_pre: float, total: float, bo: int = 3, final_tb: int = 7) -> tuple[float, float]:
    """Serve-point probabilities (pa, pb) with pa + pb = total whose chain gives A a pre-match chance of p_pre."""
    lo, hi = -0.35, 0.35
    for _ in range(40):
        d = (lo + hi) / 2
        if p_prematch(total / 2 + d, total / 2 - d, bo, final_tb) < p_pre:
            lo = d
        else:
            hi = d
    d = (lo + hi) / 2
    return total / 2 + d, total / 2 - d


# ------------------------------------------------------------------ ratings and features (walk results in date order)
BASE_SERVE = {("atp", "hard"): 0.645, ("atp", "clay"): 0.625, ("atp", "grass"): 0.675,
              ("wta", "hard"): 0.565, ("wta", "clay"): 0.555, ("wta", "grass"): 0.585}   # tour serve points won
FEATS = ["elo", "elo_bo5", "fatigue3", "fatigue7", "form", "h2h", "rust"]
LN10_400 = math.log(10) / 400


def k_factor(n: int) -> float:
    return 250 / (n + 5) ** 0.4


def _sets(r: dict) -> tuple[list[int], list[int]]:
    return [int(x) for x in r["w_games"].split(",")], [int(x) for x in r["l_games"].split(",")]


class Ratings:
    """Every feature for a match is read BEFORE that match updates anything, so backtests never see the future."""

    def __init__(self):
        self.elo = collections.defaultdict(lambda: 1500.0)
        self.selo = collections.defaultdict(lambda: 1500.0)
        self.n = collections.Counter()
        self.ns = collections.Counter()
        self.load = collections.defaultdict(list)          # player -> [(date, sets played)]
        self.resid = collections.defaultdict(lambda: collections.deque(maxlen=10))
        self.h2h = collections.defaultdict(list)           # (a, b) -> [result for a - expected for a]
        self.tb = collections.Counter()                    # player -> tiebreak sets
        self.tb_exp = collections.Counter()                # player -> tiebreak sets expected at tour rate
        self.last = {}
        self.name = {}
        self.tb_rate = {}                                  # (tour, surface) -> tour tiebreak rate per set

    def p_elo(self, a: str, b: str, surf: str) -> float:
        d = 0.5 * (self.elo[a] - self.elo[b]) + 0.5 * (self.selo[(a, surf)] - self.selo[(b, surf)])
        return 1 / (1 + 10 ** (-d / 400))

    def _sets_since(self, p: str, date: dt.date, days: int) -> int:
        lo = date - dt.timedelta(days=days)
        return sum(s for d, s in self.load[p] if lo <= d < date)

    def features(self, a: str, b: str, surf: str, date: str, bo: int) -> dict:
        d = dt.date.fromisoformat(date)
        pe = self.p_elo(a, b, surf)
        x = math.log(pe / (1 - pe))
        form = lambda p: sum(self.resid[p]) / (len(self.resid[p]) + 5)
        h = self.h2h[(a, b)]
        rust = lambda p: float(p in self.last and (d - self.last[p]).days > 45)
        return {"elo": x, "elo_bo5": x if bo == 5 else 0.0,
                "fatigue3": self._sets_since(a, d, 3) - self._sets_since(b, d, 3),
                "fatigue7": self._sets_since(a, d, 7) - self._sets_since(b, d, 7),
                "form": form(a) - form(b), "h2h": sum(h) / (len(h) + 3), "rust": rust(a) - rust(b),
                "p_elo": pe, "n_a": self.n[a], "n_b": self.n[b], "h2h_n": len(h),
                "tb_a": self.tb_index(a), "tb_b": self.tb_index(b)}

    def tb_index(self, p: str) -> float:
        """Tiebreak sets vs what the tour rate predicts, shrunk to 1: above 1 = holds serve more than most."""
        return (self.tb[p] + TB_SHRINK * 0.2) / (self.tb_exp[p] + TB_SHRINK * 0.2)

    def update(self, r: dict) -> None:
        w, l, surf = r["w_id"], r["l_id"], r["surface"]
        self.name[w], self.name[l] = r["w_name"], r["l_name"]
        d = dt.date.fromisoformat(r["date"])
        wg, lg = _sets(r)
        rate = self.tb_rate.get((r["tour"], surf), 0.18)
        for p in (w, l):
            self.load[p].append((d, len(wg)))
            self.load[p] = [x for x in self.load[p] if (d - x[0]).days <= 14]
            self.last[p] = d
            self.tb[p] += int(r["tb"])
            self.tb_exp[p] += rate * sum(1 for a, b in zip(wg, lg) if max(a, b) >= 6)
        if int(r["retired"]):
            return                                           # a retirement says little about strength
        pw = self.p_elo(w, l, surf)
        self.resid[w].append(1 - pw)
        self.resid[l].append(pw - 1)
        self.h2h[(w, l)].append(1 - pw)
        self.h2h[(l, w)].append(pw - 1)
        for key, n, tab in (((w, l), self.n, self.elo), (((w, surf), (l, surf)), self.ns, self.selo)):
            a, b = key
            e = 1 / (1 + 10 ** ((tab[b] - tab[a]) / 400))
            tab[a] += k_factor(n[a]) * (1 - e)
            tab[b] -= k_factor(n[b]) * (1 - e)
            n[a] += 1
            n[b] += 1


def tour_tb_rates(matches: list[dict]) -> dict:
    acc = collections.defaultdict(lambda: [0, 0])
    for r in matches:
        wg, lg = _sets(r)
        full = [(a, b) for a, b in zip(wg, lg) if max(a, b) >= 6]
        acc[(r["tour"], r["surface"])][0] += sum(1 for a, b in full if {a, b} == {7, 6})
        acc[(r["tour"], r["surface"])][1] += len(full)
    return {k: v[0] / v[1] for k, v in acc.items() if v[1]}


def walk(matches: list[dict], until: str | None = None):
    """Yield (row, features with A = a coin-flip orientation, y = A won) and leave the ratings after the walk."""
    R = Ratings()
    R.tb_rate = tour_tb_rates(matches)
    out = []
    for r in matches:
        if until and r["date"] > until:
            break
        flip = int(r["comp_id"]) % 2 == 0
        a, b = (r["l_id"], r["w_id"]) if flip else (r["w_id"], r["l_id"])
        f = R.features(a, b, r["surface"], r["date"], int(r["bo"]))
        out.append((r, a, b, f, 0.0 if flip else 1.0))
        R.update(r)
    return R, out


# ------------------------------------------------------------------ the fitted layer
def fit_logistic(X: np.ndarray, y: np.ndarray, prior: np.ndarray, lam: float = 5.0) -> np.ndarray:
    th = prior.copy()
    for _ in range(50):
        p = 1 / (1 + np.exp(-X @ th))
        g = X.T @ (p - y) + lam * (th - prior)
        H = X.T @ (X * (p * (1 - p))[:, None]) + lam * np.eye(len(th))
        step = np.linalg.solve(H, g)
        th -= step
        if np.abs(step).max() < 1e-9:
            break
    return th


def predict(f: dict, coef: dict) -> float:
    z = sum(coef.get(k, 0.0) * f[k] for k in FEATS)
    return 1 / (1 + math.exp(-z))


def serve_total(tour: str, surf: str, tb_a: float, tb_b: float, rates: dict) -> float:
    """Sum of the two serve-point probabilities: tour baseline, raised or lowered so the chain's tiebreak rate
    moves by the two players' tiebreak index (big servers -> more tiebreaks -> higher serve levels)."""
    base = BASE_SERVE.get((tour, surf), BASE_SERVE[(tour, "hard")])
    f = min(1.8, max(0.55, (tb_a + tb_b) / 2))
    if abs(f - 1) < 0.02:
        return 2 * base
    target = f * p_tb_set(base, base)
    lo, hi = 0.40, 0.85
    for _ in range(30):
        mid = (lo + hi) / 2
        if p_tb_set(mid, mid) < target:
            lo = mid
        else:
            hi = mid
    return lo + hi


_TABLE: dict = {}


def serve_probs(p_pre: float, total: float, bo: int, final_tb: int = 7) -> tuple[float, float]:
    """solve_serve via a cached interpolation table (the backtest needs thousands of these)."""
    key = (round(total * 200) / 200, bo, final_tb)
    if key not in _TABLE:
        ds = np.linspace(-0.3, 0.3, 61)
        _TABLE[key] = (ds, np.array([p_prematch(key[0] / 2 + d, key[0] / 2 - d, bo, final_tb) for d in ds]))
    ds, ps = _TABLE[key]
    d = float(np.interp(p_pre, ps, ds))
    return key[0] / 2 + d, key[0] / 2 - d


def final_tb_for(event: str, tour: str) -> int:
    return 10 if any(k in event.lower() for k in SLAMS) else 7


def fit(matches: list[dict], train_from: str, train_to: str, test_to: str | None = None, log=print) -> dict:
    """Fit the logistic layer and the in-match form shift on [train_from, train_to]; score on what follows."""
    R, rows = walk(matches)
    tr = [x for x in rows if train_from <= x[0]["date"] <= train_to and not int(x[0]["retired"])]
    te = [x for x in rows if x[0]["date"] > train_to and (not test_to or x[0]["date"] <= test_to) and not int(x[0]["retired"])]
    X = lambda xs: np.array([[f[k] for k in FEATS] for _, _, _, f, _ in xs])
    Y = lambda xs: np.array([y for *_, y in xs])
    prior = np.array([1.0, 0.25, 0, 0, 0, 0, 0])
    th = fit_logistic(X(tr), Y(tr), prior)
    coef = dict(zip(FEATS, map(float, th)))
    th_elo = fit_logistic(X(tr)[:, :1], Y(tr), np.array([1.0]))
    out = {"coef": coef, "elo_only": float(th_elo[0]), "n_train": len(tr), "n_test": len(te),
           "train": [train_from, train_to], "tb_rates": {f"{k[0]}:{k[1]}": v for k, v in R.tb_rate.items()}}
    if te:
        y = Y(te)
        pf = 1 / (1 + np.exp(-X(te) @ th))
        pe = 1 / (1 + np.exp(-X(te)[:, 0] * th_elo[0]))
        score = lambda p: {"acc": float(np.mean((p > 0.5) == (y == 1))), "brier": float(np.mean((p - y) ** 2)),
                           "logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))}
        out["test_full"], out["test_elo"] = score(pf), score(pe)
        out["calibration"] = _calib(pf, y)
    out["form"], out["form_test"] = fit_form(tr, te, coef, R.tb_rate, log)
    return out


def _calib(p, y, edges=(0.5, 0.6, 0.7, 0.8, 0.9, 1.01)):
    q = np.where(p >= 0.5, p, 1 - p)
    yy = np.where(p >= 0.5, y, 1 - y)
    out, lo = [], 0.5
    for hi in edges[1:]:
        m = (q >= lo) & (q < hi)
        if m.sum():
            out.append([lo, hi, int(m.sum()), float(q[m].mean()), float(yy[m].mean())])
        lo = hi
    return out


def _after_set1(r, f, coef, rates, k):
    wg, lg = _sets(r)
    p_pre = predict(f, coef)
    tour, surf, bo = r["tour"], r["surface"], int(r["bo"])
    tot = serve_total(tour, surf, f["tb_a"], f["tb_b"], rates)
    pa, pb = serve_probs(p_pre, tot, bo, final_tb_for(r["event"], tour))
    a_is_w = f["_a_is_w"]
    a_won1 = (wg[0] > lg[0]) == a_is_w
    sa, sb = (1, 0) if a_won1 else (0, 1)
    return [0.5 * (p_match(pa, pb, bo, sa, sb, srv="A", form=x) + p_match(pa, pb, bo, sa, sb, srv="B", form=x)) for x in k]


FORM_GRID = [0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04]


def fit_form(tr, te, coef, rates, log=print, n_max=1500) -> tuple[float, dict]:
    """In-match form: the serve-probability shift per set of lead that best explains who won after set one."""
    def prep(xs):
        out = []
        for r, a, b, f, y in xs:
            wg, _ = _sets(r)
            if int(r["bo"]) == 3 and len(wg) >= 2:
                out.append((r, {**f, "_a_is_w": y == 1.0}, y))
        rng = np.random.default_rng(7)
        return [out[i] for i in rng.permutation(len(out))[:n_max]]
    trs, tes = prep(tr), prep(te)
    log(f"fitting in-match form on {len(trs)} matches ...")
    P = np.array([_after_set1(r, f, coef, rates, FORM_GRID) for r, f, _ in trs])
    y = np.array([yy for *_, yy in trs])
    ll = [-np.mean(y * np.log(P[:, i]) + (1 - y) * np.log(1 - P[:, i])) for i in range(len(FORM_GRID))]
    best = FORM_GRID[int(np.argmin(ll))]
    res = {"grid_logloss_train": dict(zip(map(str, FORM_GRID), map(float, ll)))}
    if tes:
        Pt = np.array([_after_set1(r, f, coef, rates, [0.0, best]) for r, f, _ in tes])
        yt = np.array([yy for *_, yy in tes])
        for i, name in ((0, "no_form"), (1, "fitted_form")):
            p = Pt[:, i]
            res[name] = {"n": len(yt), "logloss": float(-np.mean(yt * np.log(p) + (1 - yt) * np.log(1 - p))),
                         "brier": float(np.mean((p - yt) ** 2)), "calibration": _calib(p, yt)}
    return best, res


# ------------------------------------------------------------------ production: fit, save, load
PRE_MARKET_WEIGHT = 0.75   # pre-match prior: the closing market beats any Elo model, so it carries most of the weight


def refresh(log=print) -> dict:
    """Pull new results, refit on everything since 2025, keep the out-of-sample check (train 2025, test 2026)."""
    update_history(log)
    m = load_matches()
    log("backtest: fit on 2025, score on 2026 ...")
    bt = fit(m, "2025-01-01", "2025-12-31", log=log)
    log("production fit on 2025-today ...")
    prod = fit(m, "2025-01-01", dt.date.today().isoformat(), log=log)
    model = {"fitted": dt.date.today().isoformat(), "coef": prod["coef"], "form": prod["form"],
             "tb_rates": prod["tb_rates"], "n_train": prod["n_train"],
             "backtest": {k: bt.get(k) for k in ("n_train", "n_test", "test_full", "test_elo", "calibration", "form", "form_test")}}
    with open(MODEL, "w") as f:
        json.dump(model, f, indent=1)
    return model


def load_model() -> dict:
    with open(MODEL) as f:
        m = json.load(f)
    m["rates"] = {tuple(k.split(":")): v for k, v in m["tb_rates"].items()}
    return m


@lru_cache(1)
def ratings() -> Ratings:
    R, _ = walk(load_matches())
    return R


def find_player(R: Ratings, name: str) -> str | None:
    names = {v: k for k, v in R.name.items()}
    low = {n.lower(): n for n in names}
    hit = [n for n in names if name.lower() in n.lower()]
    if len(hit) == 1:
        return names[hit[0]]
    best = difflib.get_close_matches(name.lower(), list(low), n=1, cutoff=0.75)
    return names[low[best[0]]] if best else (names[hit[0]] if hit else None)


def american_to_p(o: float) -> float:
    return 100 / (o + 100) if o > 0 else -o / (-o + 100)


def no_vig(oa: float, ob: float) -> float:
    a, b = american_to_p(oa), american_to_p(ob)
    return a / (a + b)


def prematch(a: str, b: str, tour: str, surf: str, bo: int, event: str = "", date: str | None = None,
             pre_odds: tuple | None = None) -> dict:
    """Pre-match probability for A with every factor shown."""
    M, R = load_model(), ratings()
    f = R.features(a, b, surf, date or dt.date.today().isoformat(), bo)
    p_model = predict(f, M["coef"])
    p_pre = p_model
    p_mkt = None
    if pre_odds:
        p_mkt = no_vig(*pre_odds)
        z = (1 - PRE_MARKET_WEIGHT) * math.log(p_model / (1 - p_model)) + PRE_MARKET_WEIGHT * math.log(p_mkt / (1 - p_mkt))
        p_pre = 1 / (1 + math.exp(-z))
    tot = serve_total(tour, surf, f["tb_a"], f["tb_b"], M["rates"])
    ftb = final_tb_for(event, tour)
    pa, pb = serve_probs(p_pre, tot, bo, ftb)
    contrib = {k: M["coef"][k] * f[k] for k in FEATS}
    return {"a": a, "b": b, "f": f, "p_model": p_model, "p_market_pre": p_mkt, "p_pre": p_pre, "pa": pa, "pb": pb,
            "total": tot, "final_tb": ftb, "contrib": contrib, "form": M["form"], "bo": bo}


# ------------------------------------------------------------------ live state from ESPN
def live_matches(name: str | None = None) -> list[dict]:
    """Singles matches on today's ESPN scoreboards (live first), parsed into a score state."""
    out = []
    for tour in ("atp", "wta"):
        try:
            sb = scoreboard(tour)
        except Exception:
            continue
        for ev in sb.get("events", []):
            for g in ev.get("groupings", []):
                grp = g.get("grouping", {}).get("displayName", "")
                if "Singles" not in grp:
                    continue
                for c in g.get("competitions", []):
                    cs = c.get("competitors") or []
                    if len(cs) != 2 or any(x.get("id") == "2147483647" or x.get("athlete", {}).get("displayName") in (None, "TBD") for x in cs):
                        continue
                    names = [x["athlete"]["displayName"] for x in cs]
                    if name and not any(name.lower() in n.lower() for n in names):
                        continue
                    out.append(_state(ev, c, grp))
    order = {"in": 0, "pre": 1, "post": 2}
    return sorted(out, key=lambda s: order.get(s["state"], 3))


def _state(ev: dict, c: dict, grp: str) -> dict:
    cs = sorted(c["competitors"], key=lambda x: x.get("order", 0))
    tour = "atp" if grp.startswith("Men") else "wta"
    rnd = (c.get("round") or {}).get("displayName", "")
    slam = any(k in ev.get("name", "").lower() for k in SLAMS)
    bo = 5 if tour == "atp" and slam and "qualif" not in rnd.lower() else 3
    city = (c.get("venue") or {}).get("fullName", "")
    games = [[int(x.get("value") or 0) for x in p.get("linescores") or []] for p in cs]
    n = max(len(games[0]), len(games[1]))
    games = [g + [0] * (n - len(g)) for g in games]
    sa = sb = 0
    cur = (0, 0)
    for i in range(n):
        x, y = games[0][i], games[1][i]
        done = (x >= 6 and x - y >= 2) or (y >= 6 and y - x >= 2) or (max(x, y) == 7 and min(x, y) >= 5)
        if done:
            sa += x > y
            sb += y > x
        else:
            cur = (x, y)
    srv = next((i for i, p in enumerate(cs) if p.get("possession")), None)
    return {"state": c["status"]["type"]["state"], "tour": tour, "event": ev.get("name", ""), "event_id": ev["id"],
            "comp_id": str(c["id"]), "round": rnd, "city": city, "bo": bo,
            "surface": surface(ev.get("name", ""), city, c.get("date", "")[:10] or dt.date.today().isoformat()),
            "ids": [str(p["id"]) for p in cs], "names": [p["athlete"]["displayName"] for p in cs],
            "sets": (sa, sb), "games": cur, "set_scores": list(zip(games[0], games[1])), "server": srv,
            "start": c.get("date", "")}


def live_price(pre: dict, sets=(0, 0), games=(0, 0), server: str = "A", pts=(0, 0),
               srv_a: tuple | None = None, srv_b: tuple | None = None) -> dict:
    """Chance A wins from the current score. srv_a/srv_b = (points won, points played) on serve so far, if known."""
    pa, pb = pre["pa"], pre["pb"]
    upd = []
    if srv_a and srv_a[1]:
        pa = (SERVE_PRIOR * pa + srv_a[0]) / (SERVE_PRIOR + srv_a[1])
        upd.append(f"A serve {srv_a[0]}/{srv_a[1]} -> {pa:.3f}")
    if srv_b and srv_b[1]:
        pb = (SERVE_PRIOR * pb + srv_b[0]) / (SERVE_PRIOR + srv_b[1])
        upd.append(f"B serve {srv_b[0]}/{srv_b[1]} -> {pb:.3f}")
    p = p_match(pa, pb, pre["bo"], sets[0], sets[1], games[0], games[1], server, pts, pre["final_tb"], pre["form"])
    p0 = p_match(pa, pb, pre["bo"], sets[0], sets[1], games[0], games[1], server, pts, pre["final_tb"], 0.0)
    return {"p": p, "p_no_form": p0, "pa": pa, "pb": pb, "updates": upd}


# ------------------------------------------------------------------ grading (bets.csv: event_id = tour/event/comp)
def result(event_id: str, player_id: str) -> tuple[str, float | None]:
    tour, ev, comp = event_id.split("/")
    base = CORE.format(tour=tour, event=ev, comp=comp)
    st = _get(base + "/status")["type"]
    if not st.get("completed"):
        return ("pending", None)
    items = _get(base + "/competitors")["items"]
    for it in items:
        c = _get(it["$ref"].replace("http://", "https://"))
        if str(c.get("id")) == str(player_id):
            if c.get("winner") is None:
                return ("void", None)
            return ("done", 1.0 if c["winner"] else 0.0)
    return ("void", None)


# ------------------------------------------------------------------ command line
PTS = {"0": 0, "15": 1, "30": 2, "40": 3, "AD": 4, "A": 4}


def parse_points(s: str, tiebreak: bool) -> tuple[int, int]:
    a, b = [x.strip().upper() for x in s.split("-")]
    return (int(a), int(b)) if tiebreak else (PTS[a], PTS[b])


def parse_score(s: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """'4-6 1-0' from A's side -> sets (0, 1), current games (1, 0)."""
    sa = sb = 0
    cur = (0, 0)
    for part in s.split():
        x, y = (int(v.split("(")[0]) for v in part.split("-"))
        if (x >= 6 and x - y >= 2) or (y >= 6 and y - x >= 2) or (max(x, y) == 7 and min(x, y) >= 5):
            sa += x > y
            sb += y > x
        else:
            cur = (x, y)
    return (sa, sb), cur


def _fmt_odds(p: float) -> str:
    return f"{-round(100 * p / (1 - p)):+d}" if p >= 0.5 else f"+{round(100 * (1 - p) / p)}"


def cli(args) -> None:
    from .blend import final_probability, rating
    from . import learn as L
    if args.action == "refresh":
        m = refresh()
        print(_backtest_text(m))
        return
    if args.action == "backtest":
        print(_backtest_text(load_model()))
        return
    if args.action == "list":
        for s in live_matches(args.player):
            sc = " ".join(f"{x}-{y}" for x, y in s["set_scores"])
            print(f"{s['state']:4s} {s['tour'].upper()} {s['event'][:30]:30s} {s['round'][:16]:16s} {s['names'][0]} vs {s['names'][1]}  {sc}")
        return
    R = ratings()
    st = None
    if args.action == "live":
        found = live_matches(args.player)
        if not found and not args.score:
            print(f"No match for '{args.player}' on today's ESPN scoreboards: pass --score and the opponent.")
            return
        st = found[0] if found else None
    if st:
        i = 0 if args.player.lower() in st["names"][0].lower() else 1
        a, b = st["ids"][i], st["ids"][1 - i]
        tour, surf, bo, event = st["tour"], args.surface or st["surface"], args.bo or st["bo"], st["event"]
        R.name.setdefault(a, st["names"][i])
        R.name.setdefault(b, st["names"][1 - i])
        sets = st["sets"] if i == 0 else st["sets"][::-1]
        games = st["games"] if i == 0 else st["games"][::-1]
        server = None if st["server"] is None else ("A" if st["server"] == i else "B")
    else:
        a, b = find_player(R, args.player or ""), find_player(R, args.opponent or "")
        if not a or not b:
            print(f"Player not found in the history: {args.player if not a else args.opponent}")
            return
        tour = args.tour or ("atp" if any(r["w_id"] == a or r["l_id"] == a for r in load_matches()[-6000:] if r["tour"] == "atp") else "wta")
        surf, bo, event = args.surface or "hard", args.bo or 3, args.event
        sets, games, server = (0, 0), (0, 0), None
    if args.score:
        sets, games = parse_score(args.score)
    server = args.server or server or "A"
    pre = prematch(a, b, tour, surf, bo, event, pre_odds=tuple(args.pre_odds) if args.pre_odds else
                   (tuple(args.odds) if args.action == "pre" and args.odds else None))
    na, nb = R.name.get(a, args.player), R.name.get(b, args.opponent)
    f, c = pre["f"], pre["contrib"]
    print(f"{tour.upper()} {event} ({surf}, best of {bo}{', 10-point final-set tiebreak' if pre['final_tb'] == 10 else ''}): {na} vs {nb}")
    print(f"Pre-match {na}: {pre['p_model']:.1%} model (Elo {f['p_elo']:.1%}; logit pushes: Elo {c['elo'] + c['elo_bo5']:+.2f}, "
          f"fatigue {c['fatigue3'] + c['fatigue7']:+.2f} [sets last 3d diff {f['fatigue3']:+.0f}], form {c['form']:+.2f}, "
          f"h2h {c['h2h']:+.2f} [{f['h2h_n']} meetings], rust {c['rust']:+.2f})"
          + (f" | market {pre['p_market_pre']:.1%} -> prior {pre['p_pre']:.1%}" if pre["p_market_pre"] is not None else ""))
    print(f"Serve: {na} wins {pre['pa']:.1%} of points on serve, {nb} {pre['pb']:.1%} (tiebreak index {f['tb_a']:.2f}/{f['tb_b']:.2f}); "
          f"momentum {pre['form'] * 100:.1f} serve pts per set of lead; {f['n_a']}/{f['n_b']} matches in the data")
    if args.action == "pre":
        p, p_mkt = pre["p_pre"], pre["p_market_pre"]       # model side = the market-anchored prior (L: market beats Elo pre-match)
        state_txt = "pre-match"
    else:
        tb = games == (6, 6)
        pts = parse_points(args.points, tb)
        srv_a = tuple(int(x) for x in args.srv_a.split("/")) if args.srv_a else None
        srv_b = tuple(int(x) for x in args.srv_b.split("/")) if args.srv_b else None
        lv = live_price(pre, sets, games, server, pts, srv_a, srv_b)
        p, p_mkt = lv["p"], (no_vig(*args.odds) if args.odds else None)
        state_txt = (f"sets {sets[0]}-{sets[1]}, games {games[0]}-{games[1]}, {na if server == 'A' else nb} serving, points {args.points}"
                     + ("" if args.points != "0-0" else " (ESPN has no point score: pass --points)"))
        print(f"Live ({state_txt}): {na} {p:.1%} (without momentum {lv['p_no_form']:.1%})" + (f"; {', '.join(lv['updates'])}" if lv["updates"] else ""))
    hist_n = min(f["n_a"], f["n_b"])
    e = final_probability(p, p_mkt, None, f"tennis:ml_{'live' if args.action == 'live' else 'pre'}:{tour}", hist_n)
    side_p = e.p if e.p >= 0.5 else 1 - e.p
    who = na if e.p >= 0.5 else nb
    print(f"Blend: {na} {e.p:.1%}" + (f" (market no-vig {p_mkt:.1%})" if p_mkt is not None else " (no market price: pass --odds)")
          + f" -> {who} {rating(side_p, e.confidence)}/10 {e.confidence}, fair {_fmt_odds(e.p)} / {nb} {_fmt_odds(1 - e.p)}")
    if args.odds:
        for nm, pp, o in ((na, e.p, args.odds[0]), (nb, 1 - e.p, args.odds[1])):
            dec = 1 + (o / 100 if o > 0 else 100 / -o)
            print(f"   {nm} {o:+.0f}: EV {pp * dec - 1:+.1%}")
    for n in e.notes:
        print(f"   note: {n}")
    if args.log:
        bets = L.read_bets()
        nid = max(int(x["id"]) for x in bets if x["id"].isdigit()) + 1
        backed = "A" if e.p >= 0.5 else "B"
        pid, pname = (a, na) if backed == "A" else (b, nb)
        pf = e.p if backed == "A" else 1 - e.p
        pm = p if backed == "A" else 1 - p
        pk = None if p_mkt is None else (p_mkt if backed == "A" else 1 - p_mkt)
        price = "" if not args.odds else args.odds[0 if backed == "A" else 1]
        eid = f"{tour}/{st['event_id']}/{st['comp_id']}" if st else ""
        bets.append({"id": str(nid), "date": dt.date.today().isoformat(), "sport": "tennis", "event": f"{na} vs {nb} ({event})",
                     "event_id": eid, "player": pname, "player_id": pid, "market": f"ml_{'live' if args.action == 'live' else 'pre'}",
                     "line": 0.5, "side": "over", "book": args.book, "price": price, "p_model": round(pm, 4),
                     "p_market": "" if pk is None else round(pk, 4), "p_hist": "", "hist_n": hist_n, "p_final": round(pf, 4),
                     "confidence": e.confidence, "action": "lean" if e.confidence == "High" else "pass",
                     "segment": f"tennis:ml_{'live' if args.action == 'live' else 'pre'}:{tour}", "group": f"tennis:{eid}",
                     "status": "pending", "notes": f"edge tennis {args.action}; {state_txt}; pre {pre['p_pre']:.3f}; serve {pre['pa']:.3f}/{pre['pb']:.3f}"})
        L.write_bets(bets)
        print(f"Logged #{nid} ({pname} to win).")


def _backtest_text(m: dict) -> str:
    bt = m["backtest"]
    lines = [f"Fitted {m['fitted']} on {m['n_train']} matches. Out of sample (fit 2025, scored on {bt['n_test']} matches of 2026):",
             f"  pre-match, full model: {bt['test_full']['acc']:.1%} correct, Brier {bt['test_full']['brier']:.4f}, log loss {bt['test_full']['logloss']:.4f}",
             f"  pre-match, Elo only:   {bt['test_elo']['acc']:.1%} correct, Brier {bt['test_elo']['brier']:.4f}, log loss {bt['test_elo']['logloss']:.4f}",
             "  calibration (favourite's predicted -> actual): " + "; ".join(f"{lo:.0%}-{min(hi, 1):.0%} n={n}: {p:.1%}->{y:.1%}" for lo, hi, n, p, y in bt["calibration"])]
    ft = bt.get("form_test") or {}
    if "no_form" in ft:
        lines.append(f"  after set one ({ft['no_form']['n']} matches): score-only chain log loss {ft['no_form']['logloss']:.4f}, "
                     f"with momentum {bt['form'] * 100:.1f} pts/set {ft['fitted_form']['logloss']:.4f}")
        lines.append("    with momentum: " + "; ".join(f"{lo:.0%}-{min(hi, 1):.0%} n={n}: {p:.1%}->{y:.1%}" for lo, hi, n, p, y in ft["fitted_form"]["calibration"]))
        lines.append("    score only:    " + "; ".join(f"{lo:.0%}-{min(hi, 1):.0%} n={n}: {p:.1%}->{y:.1%}" for lo, hi, n, p, y in ft["no_form"]["calibration"]))
    lines.append("Coefficients (logit per unit): " + ", ".join(f"{k} {v:+.3f}" for k, v in m["coef"].items()))
    return "\n".join(lines)
