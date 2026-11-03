"""Team ratings from play-by-play, using only plays before the game being rated (no leakage).

Each rating is a ridge regression on plays: y = mu + offense[posteam] + defense[defteam] + home * (posteam is home).
  - EPA/play and success rate, offense and defense, opponent-adjusted (a defense rating is EPA *allowed*,
    so positive = worse defense).
  - QB rating: EPA per dropback with a QB effect and a pass-defense effect. The offense rating carries whichever
    QBs played; a starter change is applied as dropback share x (new QB - the season's QB mix) in EPA/play.
  - Pace: seconds per play on drives in neutral script (quarters 1-3, score within 10), shrunk to the league.
Garbage time (win probability under 5% or over 95%), kneels and spikes are left out.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from .data import f

LAMBDA_TEAM = 75.0      # plays of league-average prior on every team rating (tuned on 2025 weeks 6-18 only: Brier 0.2370 at 75 vs 0.2399 at 400)
LAMBDA_QB = 250.0       # dropbacks of league-average prior on every QB rating
PRIOR_SEASON_WEIGHT = 0.5   # QB ratings borrow last season's dropbacks at half weight (flagged in the report)


def rating_plays(plays: list[dict], before: str | None = None, season: str | None = None) -> list[dict]:
    """Scrimmage plays usable for ratings, strictly before `before` (YYYY-MM-DD)."""
    out = []
    for p in plays:
        if season and p["season"] != season:
            continue
        if before and p["game_date"] >= before:
            continue
        if p["play_type"] not in ("pass", "run") or p["epa"] in ("", "NA") or p["qb_kneel"] == "1" or p["qb_spike"] == "1":
            continue
        if not p["posteam"] or not p["defteam"]:
            continue
        wp = f(p["wp"])
        if wp is not None and (wp < 0.05 or wp > 0.95):
            continue
        out.append(p)
    return out


def _ridge(rows, key_a, key_b, y_fn, lam_a, lam_b, weights=None):
    """Two-way additive ridge: y = mu + a[key_a] + b[key_b] + h*home. Returns (mu, h, a, b, counts_a)."""
    A = sorted({key_a(r) for r in rows})
    B = sorted({key_b(r) for r in rows})
    ia, ib = {k: i for i, k in enumerate(A)}, {k: i for i, k in enumerate(B)}
    na, nb = len(A), len(B)
    P = 2 + na + nb
    XtX = np.zeros((P, P))
    Xty = np.zeros(P)
    cnt = np.zeros(na)
    for j, r in enumerate(rows):
        w = 1.0 if weights is None else weights[j]
        y = y_fn(r)
        idx = [0, 2 + ia[key_a(r)], 2 + na + ib[key_b(r)]]
        if r["posteam"] == r["home_team"]:
            idx.append(1)
        for u in idx:
            Xty[u] += w * y
            for v in idx:
                XtX[u, v] += w
        cnt[ia[key_a(r)]] += w
    pen = np.zeros(P)
    pen[2:2 + na] = lam_a
    pen[2 + na:] = lam_b
    beta = np.linalg.solve(XtX + np.diag(pen) + np.eye(P) * 1e-9, Xty)
    return beta[0], beta[1], dict(zip(A, beta[2:2 + na])), dict(zip(B, beta[2 + na:])), dict(zip(A, cnt))


def team_ratings(plays: list[dict], lam: float = LAMBDA_TEAM) -> dict:
    """Offense/defense EPA and success ratings, home term, dropback share and pace for every team."""
    if not plays:
        return {"mu_epa": 0.0, "hfa_epa": 0.0, "mu_sr": 0.45, "teams": {}, "n_plays": 0}
    mu, h, off, de, n = _ridge(plays, lambda r: r["posteam"], lambda r: r["defteam"], lambda r: float(r["epa"]), lam, lam)
    mus, hs, offs, des, _ = _ridge(plays, lambda r: r["posteam"], lambda r: r["defteam"], lambda r: float(r["success"] or 0), lam, lam)
    db = defaultdict(lambda: [0, 0])
    games = defaultdict(set)
    for p in plays:
        db[p["posteam"]][0] += p["qb_dropback"] == "1"
        db[p["posteam"]][1] += 1
        games[p["posteam"]].add(p["game_id"])
    teams = {}
    for t in set(off) | set(de):
        d, tot = db[t]
        teams[t] = {"off_epa": off.get(t, 0.0), "def_epa": de.get(t, 0.0), "off_sr": offs.get(t, 0.0), "def_sr": des.get(t, 0.0),
                    "db_share": (d + 0.6 * 60) / (tot + 60), "plays": tot, "games": len(games[t]),
                    "plays_per_game": tot / max(len(games[t]), 1)}
    return {"mu_epa": mu, "hfa_epa": h, "mu_sr": mus, "hfa_sr": hs, "teams": teams, "n_plays": len(plays)}


def qb_ratings(plays_now: list[dict], plays_prior: list[dict] | None = None) -> dict:
    """EPA per dropback by QB (passer id), adjusted for the pass defense faced; prior season at half weight."""
    rows, w = [], []
    for src, wt in ((plays_now, 1.0), (plays_prior or [], PRIOR_SEASON_WEIGHT)):
        for p in src:
            if p["qb_dropback"] == "1" and p["passer_player_id"]:
                rows.append(p)
                w.append(wt)
    if not rows:
        return {}
    mu, h, q, d, n = _ridge(rows, lambda r: r["passer_player_id"], lambda r: r["defteam"] + ":" + r["season"], lambda r: float(r["epa"]),
                            LAMBDA_QB, LAMBDA_TEAM, weights=w)
    names = {}
    for p in rows:
        names[p["passer_player_id"]] = p["passer_player_name"]
    return {pid: {"name": names[pid], "epa_db": v, "dropbacks": n[pid]} for pid, v in q.items()}


def qb_mix(plays: list[dict], team: str, qbs: dict) -> tuple[float, dict]:
    """Dropback-weighted QB rating behind a team's season offense rating, and each QB's share."""
    c = defaultdict(int)
    for p in plays:
        if p["posteam"] == team and p["qb_dropback"] == "1" and p["passer_player_id"]:
            c[p["passer_player_id"]] += 1
    tot = sum(c.values())
    if not tot:
        return 0.0, {}
    mix = sum(qbs.get(pid, {"epa_db": 0.0})["epa_db"] * k for pid, k in c.items()) / tot
    return mix, {qbs.get(pid, {"name": pid})["name"]: k / tot for pid, k in c.items()}


def pace(drives: list[dict], before: str | None = None, season: str | None = None, k: float = 30.0) -> dict:
    """Neutral-script seconds per play by offense, shrunk toward the league with k drives."""
    by = defaultdict(lambda: [0.0, 0.0, 0])
    lg = [0.0, 0.0]
    for d in drives:
        if (season and d["season"] != season) or (before and d["game_date"] >= before):
            continue
        if d["qtr"] > 3 or abs(d["score_diff"]) > 10 or d["plays"] < 3 or d["top"] <= 0:
            continue
        b = by[d["posteam"]]
        b[0] += d["top"]
        b[1] += d["plays"]
        b[2] += 1
        lg[0] += d["top"]
        lg[1] += d["plays"]
    league = lg[0] / lg[1] if lg[1] else 28.0
    out = {t: (v[0] + k * 6 * league) / (v[1] + k * 6) for t, v in by.items()}
    return {"league": league, "teams": out}
