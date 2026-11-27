"""Deeper tennis history (TennisMyLife match database) and the candidate factors tested on it.

Data: stats.tennismylife.org yearly CSVs in Jeff Sackmann's format (ATP tour from 2018, ATP Challenger, WTA tour),
one row per match with both players' serve counts (serve points, 1st serves in / won, 2nd serves won, aces, double
faults, service games), minutes, round, best of, hand, ranking at the time, surface and an indoor flag (ATP). The
"ongoing" files carry this week's events. Cross-checked against Tennis Abstract (Fritz d. Fils, Paris 2026: identical
serve counts). The author notes the WTA files are less proven than the ATP ones; they are used for WTA tour players
only, and Tennis Abstract stays the fallback.

Factors (each is kept only if it improves the walk-forward test, LESSONS L30):
  - ratings: each player's serve and return skill solved jointly with every opponent's (so a 70% serve-point rate
    against weak returners counts for less), recent matches weighted more (half-life H), surface deviations shrunk;
  - Elo on results (overall and surface), for who wins;
  - fatigue: minutes already played at the event, previous match length;
  - indoor vs outdoor; left- vs right-handed matchups.
"""
from __future__ import annotations

import csv
import datetime as dt
import os
import re

import numpy as np

URL = "https://stats.tennismylife.org/data/"
SURF = {"Hard": 0, "Clay": 1, "Grass": 2, "Carpet": 0}
ROUND = {"Q1": 0, "Q2": 1, "Q3": 2, "Q4": 3, "R128": 4, "R64": 5, "R32": 6, "R16": 7, "RR": 7, "QF": 8, "SF": 9, "BR": 10, "F": 10}


def files(years=range(2018, 2027)) -> list[tuple[str, str]]:
    """(file name, tour) for the yearly files and this week's ongoing files."""
    out = []
    for y in years:
        out += [(f"{y}.csv", "ATP"), (f"{y}_challenger.csv", "ATP"), (f"{y}_wta.csv", "WTA")]
    out += [("ongoing_tourneys.csv", "ATP"), ("challenger_ongoing_tourneys.csv", "ATP"), ("wta_ongoing_tourneys.csv", "WTA")]
    return out


def download(folder: str, years=range(2018, 2027), refresh_ongoing: bool = True) -> None:
    import urllib.request
    os.makedirs(folder, exist_ok=True)
    for f, _ in files(years):
        path = os.path.join(folder, f)
        if os.path.exists(path) and not (refresh_ongoing and ("ongoing" in f or f.startswith(str(dt.date.today().year)))):
            continue
        req = urllib.request.Request(URL + f, headers={"User-Agent": "Mozilla/5.0 (edge tennis research)"})
        with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as out:
            out.write(r.read())


def parse_score(score: str):
    if not score or re.search(r"RET|W/O|DEF|ABD|UNP|Walkover", score, re.I):
        return None
    sets = re.findall(r"(\d+)-(\d+)(?:\((\d+)\))?", score)
    if not sets:
        return None
    g = [(int(a), int(b)) for a, b, _ in sets]
    return {"sets": len(g), "games": sum(a + b for a, b in g), "games_w": sum(a for a, _ in g), "games_l": sum(b for _, b in g),
            "tiebreaks": sum(1 for a, b in g if {a, b} == {7, 6}), "first_set": g[0][0] + g[0][1]}


def _int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def load(folder: str, years=range(2018, 2027)) -> list[dict]:
    """Every match, both tours, with serve counts; ordered by event start, then round."""
    rows, seen = [], set()
    for f, tour in files(years):
        path = os.path.join(folder, f)
        if not os.path.exists(path):
            continue
        for r in csv.DictReader(open(path, encoding="utf-8", errors="replace")):
            key = (tour, r["tourney_id"], r["match_num"], r["winner_id"], r["loser_id"])
            if key in seen:                      # ongoing files repeat finished rows of the yearly file
                continue
            seen.add(key)
            d = _int(r["tourney_date"])
            if not d or r["surface"] not in SURF:
                continue
            m = {"tour": tour, "level": r["tourney_level"], "ev": f"{tour}-{r['tourney_id']}", "tname": r["tourney_name"],
                 "date": d, "surface": r["surface"], "indoor": {"I": 1, "O": 0}.get(r["indoor"]), "round": r["round"],
                 "ro": ROUND.get(r["round"], 6), "bo": _int(r["best_of"]) or 3, "minutes": _int(r["minutes"]),
                 "w": r["winner_id"], "l": r["loser_id"], "w_name": r["winner_name"], "l_name": r["loser_name"],
                 "w_hand": r["winner_hand"], "l_hand": r["loser_hand"], "w_rank": _int(r["winner_rank"]), "l_rank": _int(r["loser_rank"]),
                 "score": r["score"], "sc": parse_score(r["score"])}
            for s in ("w", "l"):
                sv, a, b = _int(r[f"{s}_svpt"]), _int(r[f"{s}_1stWon"]), _int(r[f"{s}_2ndWon"])
                m[f"{s}_n"], m[f"{s}_k"] = (sv, a + b) if sv and a is not None and b is not None and sv >= 10 else (None, None)
            m["w_ht"], m["l_ht"] = _int(r.get("winner_ht")), _int(r.get("loser_ht"))
            if m["w_n"] and m["l_n"]:            # the rest of the serve line, for scouting profiles (edge/tennis_scout.py)
                m["raw"] = {f"{s}_{k}": r.get(f"{s}_{k}") for s in ("w", "l") for k in ("ace", "df", "svpt", "1stIn", "1stWon", "2ndWon", "SvGms", "bpSaved", "bpFaced")}
            rows.append(m)
    start = {}
    for m in rows:
        start[m["ev"]] = min(start.get(m["ev"], m["date"]), m["date"])
    for m in rows:
        m["start"] = start[m["ev"]]
        m["day"] = dt.date(m["start"] // 10000, m["start"] // 100 % 100, m["start"] % 100).toordinal()
    rows.sort(key=lambda m: (m["start"], m["ro"], m["date"]))
    return rows


# ------------------------------------------------------------------ serve / return ratings
class Ratings:
    """p(A wins a point on serve vs B) = t[surface, indoor] + a_A + ds_A,s - b_B - dr_B,s, fitted by weighted
    alternating least squares on every match's serve points (weight = points x 0.5^(age / H)), with ridge priors:
    lam points toward 0 for a and b, lam_s points for the surface deviations. With opponent=False the opponent's
    return skill is left out (plain averages, the current model's way)."""

    def __init__(self, H: float = 365.0, lam: float = 600.0, lam_s: float = 1500.0, indoor: bool = False, opponent: bool = True,
                 max_age: int = 3 * 365, hand: bool = False):
        self.H, self.lam, self.lam_s, self.indoor, self.opponent, self.max_age, self.hand = H, lam, lam_s, indoor, opponent, max_age, hand

    def fit(self, obs: dict, asof_day: int):
        """obs: arrays from observations() for one tour; only rows dated before asof_day (and within max_age) count."""
        keep = (obs["day"] < asof_day) & (asof_day - obs["day"] <= self.max_age)
        srv, ret, surf, ind, n, k, lh = (obs[x][keep] for x in ("srv", "ret", "surf", "ind", "n", "k", "lh"))
        age = asof_day - obs["day"][keep]
        idx = obs["idx"]
        P = len(idx)
        w = n * 0.5 ** (age / self.H)
        p = k / n
        cell = surf * 2 + (ind if self.indoor else 0)
        t = np.bincount(cell, w * p, 6) / np.maximum(np.bincount(cell, w, 6), 1e-9)
        t[np.bincount(cell, w, 6) == 0] = np.average(p, weights=w)
        hc = np.zeros(4)
        a, b = np.zeros(P), np.zeros(P)
        ds, dr = np.zeros(P * 3), np.zeros(P * 3)
        si, ri = srv * 3 + surf, ret * 3 + surf
        for _ in range(25):
            base = t[cell] + (hc[lh] if self.hand else 0)
            a = np.bincount(srv, w * (p - base - ds[si] + (b[ret] + dr[ri]) * self.opponent), P) / (np.bincount(srv, w, P) + self.lam)
            ds = np.bincount(si, w * (p - base - a[srv] + (b[ret] + dr[ri]) * self.opponent), P * 3) / (np.bincount(si, w, P * 3) + self.lam_s)
            if self.opponent:
                b = np.bincount(ret, w * (base + a[srv] + ds[si] - dr[ri] - p), P) / (np.bincount(ret, w, P) + self.lam)
                dr = np.bincount(ri, w * (base + a[srv] + ds[si] - b[ret] - p), P * 3) / (np.bincount(ri, w, P * 3) + self.lam_s)
            else:   # plain return average, the same shrinkage: the share of return points won above the tour's
                b = np.bincount(ret, w * (base - p), P) / (np.bincount(ret, w, P) + self.lam)
                dr = np.bincount(ri, w * (base - b[ret] - p), P * 3) / (np.bincount(ri, w, P * 3) + self.lam_s)
            if self.hand:
                res = p - t[cell] - a[srv] - ds[si] + (b[ret] + dr[ri])
                hc = np.bincount(lh, w * res, 4) / (np.bincount(lh, w, 4) + 5000.0)
        self.t, self.a, self.b, self.ds, self.dr, self.hc = t, a, b, ds, dr, hc
        self.pts_s, self.pts_r = np.bincount(srv, w, P), np.bincount(ret, w, P)
        self.P = P
        return self

    def p(self, i: int, j: int, surface: str, indoor, hand_i: str = "R", hand_j: str = "R", plain_vs: bool = False) -> float:
        s = SURF[surface]
        ok = lambda x: x is not None and x < self.P
        base = self.t[s * 2 + ((indoor or 0) if self.indoor else 0)] + (self.hc[2 * (hand_i == "L") + (hand_j == "L")] if self.hand else 0)
        a = (self.a[i] + self.ds[i * 3 + s]) if ok(i) else 0.0
        b = (self.b[j] + self.dr[j * 3 + s]) if ok(j) else 0.0
        return float(np.clip(base + a - b, 0.3, 0.92))

    def points(self, i):
        return (float(self.pts_s[i]) if i is not None and i < self.P else 0.0), (float(self.pts_r[i]) if i is not None and i < self.P else 0.0)


def observations(matches: list[dict], tour: str) -> dict:
    """Every serve-point record of a tour as arrays (server, returner, surface, indoor, points, won, day, hands)."""
    idx, cols = {}, {x: [] for x in ("srv", "ret", "surf", "ind", "n", "k", "day", "lh")}
    for m in matches:
        if m["tour"] != tour:
            continue
        for s, o in (("w", "l"), ("l", "w")):
            if m[f"{s}_n"]:
                cols["srv"].append(idx.setdefault(m[s], len(idx))); cols["ret"].append(idx.setdefault(m[o], len(idx)))
                cols["surf"].append(SURF[m["surface"]]); cols["ind"].append(m["indoor"] or 0)
                cols["n"].append(m[f"{s}_n"]); cols["k"].append(m[f"{s}_k"]); cols["day"].append(m["day"])
                cols["lh"].append(2 * (m[f"{s}_hand"] == "L") + (m[f"{o}_hand"] == "L"))
    for m in matches:                       # players with no serve counts still get an index (ratings 0)
        if m["tour"] == tour:
            idx.setdefault(m["w"], len(idx)); idx.setdefault(m["l"], len(idx))
    out = {x: np.array(v) for x, v in cols.items()}
    out["idx"] = idx
    return out


# ------------------------------------------------------------------ Elo
def elo_walk(matches: list[dict], tour: str):
    """Elo before every match (overall and surface, K = 250 / (n + 5)^0.4, FiveThirtyEight's tennis form). Returns
    {id(match): (Elo win probability for the winner, n matches winner, n matches loser)}."""
    R, Rs, N, Ns, out = {}, {}, {}, {}, {}
    for m in matches:
        if m["tour"] != tour:
            continue
        w, l, s = m["w"], m["l"], m["surface"]
        rw, rl = R.get(w, 1500.0), R.get(l, 1500.0)
        sw, sl = Rs.get((w, s), 1500.0), Rs.get((l, s), 1500.0)
        e = 1 / (1 + 10 ** ((0.5 * (rl + sl) - 0.5 * (rw + sw)) / 400))
        out[id(m)] = (e, N.get(w, 0), N.get(l, 0))
        if not m["sc"]:
            continue                                # retirements and walkovers don't move Elo
        e1 = 1 / (1 + 10 ** ((rl - rw) / 400)); e2 = 1 / (1 + 10 ** ((sl - sw) / 400))
        kw, kl = 250 / (N.get(w, 0) + 5) ** 0.4, 250 / (N.get(l, 0) + 5) ** 0.4
        R[w], R[l] = rw + kw * (1 - e1), rl - kl * (1 - e1)
        ksw, ksl = 250 / (Ns.get((w, s), 0) + 5) ** 0.4, 250 / (Ns.get((l, s), 0) + 5) ** 0.4
        Rs[(w, s)], Rs[(l, s)] = sw + ksw * (1 - e2), sl - ksl * (1 - e2)
        N[w], N[l] = N.get(w, 0) + 1, N.get(l, 0) + 1
        Ns[(w, s)], Ns[(l, s)] = Ns.get((w, s), 0) + 1, Ns.get((l, s), 0) + 1
    return out, R, Rs, N


# ------------------------------------------------------------------ exact match-win probability (iid points)
def _hold(p):
    q = 1 - p
    return p ** 4 * (1 + 4 * q + 10 * q * q) + 20 * p ** 3 * q ** 3 * p * p / (1 - 2 * p * q)


def _tiebreak(pa, pb, target=7):
    """P(A wins a tiebreak A starts serving), point by point to target-all, then the two-point closed form."""
    pa, pb = np.asarray(pa, float), np.asarray(pb, float)
    S = {(0, 0): np.ones_like(pa)}
    win = np.zeros_like(pa)
    for k in range(2 * target - 2):                 # points 1 .. 2(target-1)
        a_srv = ((k + 1) // 2) % 2 == 0
        pw = pa if a_srv else 1 - pb
        N = {}
        for (i, j), pr in S.items():
            for di, pp in ((1, pw), (0, 1 - pw)):
                ni, nj = i + di, j + 1 - di
                if ni == target:
                    win = win + pr * pp
                elif nj == target:
                    pass
                else:
                    N[(ni, nj)] = N.get((ni, nj), 0) + pr * pp
        S = N
    q, r = pa * (1 - pb), (1 - pa) * pb
    deuce = S.get((target - 1, target - 1), 0)
    return win + deuce * q / (q + r)


def _set(pa, pb, a_first=True):
    ha, hb = _hold(pa), _hold(pb)
    S = {(0, 0): np.ones_like(ha)}
    win = np.zeros_like(ha)
    for g in range(12):
        a_srv = (g % 2 == 0) == a_first
        pw = ha if a_srv else 1 - hb
        N = {}
        for (i, j), pr in S.items():
            for di, pp in ((1, pw), (0, 1 - pw)):
                ni, nj = i + di, j + 1 - di
                if ni >= 6 and ni - nj >= 2:
                    win = win + pr * pp
                elif nj >= 6 and nj - ni >= 2:
                    pass
                else:
                    N[(ni, nj)] = N.get((ni, nj), 0) + pr * pp
        S = N
    tb = _tiebreak(pa, pb) if a_first else 1 - _tiebreak(pb, pa)
    return win + S.get((6, 6), 0) * tb


def match_win(pa, pb, best_of=3):
    s = 0.5 * (_set(pa, pb, True) + _set(pa, pb, False))
    return s * s * (1 + 2 * (1 - s)) if best_of == 3 else s ** 3 * (1 + 3 * (1 - s) + 6 * (1 - s) ** 2)


_GH = np.polynomial.hermite_e.hermegauss(7)


def match_win_form(pa, pb, best_of, sd, rho, va=0.0, vb=0.0):
    """P(A wins) with each match's serve rates drawn around pa, pb (day-to-day form sd, correlation rho, plus the
    rates' estimation variances), by 7 x 7 Gauss-Hermite quadrature."""
    pa, pb = np.atleast_1d(np.asarray(pa, float)), np.atleast_1d(np.asarray(pb, float))
    va, vb = np.broadcast_to(va, pa.shape), np.broadcast_to(vb, pa.shape)
    x, wq = _GH
    wq = wq / wq.sum()
    out = np.zeros_like(pa)
    ca = np.sqrt(sd * sd + va)
    cb_rho = rho * sd * sd / ca
    cb_rest = np.sqrt(np.maximum(sd * sd + vb - cb_rho ** 2, 1e-12))
    for x1, w1 in zip(x, wq):
        for x2, w2 in zip(x, wq):
            qa = np.clip(pa + ca * x1, 0.3, 0.95)
            qb = np.clip(pb + cb_rho * x1 + cb_rest * x2, 0.3, 0.95)
            out += w1 * w2 * match_win(qa, qb, best_of)
    return out


def shift_to(pa, pb, target, best_of, sd, rho, va=0.0, vb=0.0):
    """The shift d (pa + d, pb - d: the same total, so the same expected length) that makes P(A wins) = target."""
    lo, hi = np.full_like(np.atleast_1d(pa), -0.2, dtype=float), np.full_like(np.atleast_1d(pa), 0.2, dtype=float)
    for _ in range(30):
        mid = (lo + hi) / 2
        f = match_win_form(pa + mid, pb - mid, best_of, sd, rho, va, vb)
        lo, hi = np.where(f < target, mid, lo), np.where(f < target, hi, mid)
    return (lo + hi) / 2


# ------------------------------------------------------------------ fatigue
def fatigue(matches: list[dict]) -> dict:
    """{(id(match), player id): (minutes at this event before this match, minutes of his previous match there,
    matches at this event before this one)} from earlier rounds of the same event (complete or not)."""
    by = {}
    for m in matches:
        by.setdefault(m["ev"], []).append(m)
    out = {}
    for ev, L in by.items():
        L.sort(key=lambda m: (m["ro"], m["date"]))
        played = {}
        for m in L:
            for s in ("w", "l"):
                prev = played.get(m[s], [])
                out[(id(m), m[s])] = (sum(x or 0 for x in prev), (prev[-1] or 0) if prev else 0, len(prev))
            for s in ("w", "l"):
                played.setdefault(m[s], []).append(m["minutes"])
    return out


def win_by_bo(pa, pb, bo, sd, rho):
    """match_win_form over arrays with mixed formats (grouped by best-of)."""
    pa, pb, bo = np.asarray(pa, float), np.asarray(pb, float), np.asarray(bo)
    out = np.zeros_like(pa)
    for b in np.unique(bo):
        k = bo == b
        out[k] = match_win_form(pa[k], pb[k], int(b), sd, rho)
    return out


def shift_by_bo(pa, pb, target, bo, sd, rho):
    pa, pb, target, bo = np.asarray(pa, float), np.asarray(pb, float), np.asarray(target, float), np.asarray(bo)
    out = np.zeros_like(pa)
    for b in np.unique(bo):
        k = bo == b
        out[k] = shift_to(pa[k], pb[k], target[k], int(b), sd, rho)
    return out
