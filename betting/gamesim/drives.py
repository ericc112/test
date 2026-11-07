"""The drive model: how ratings and game situation turn into drive results, clock and field position.

Everything here is fitted on drives that came before the game being simulated:
  - drive result: multinomial logistic regression over {TD, FG attempt, punt, turnover, turnover on downs,
    safety} on start field position, offense and defense ratings (EPA and success, each from games *before*
    that drive's week), home, two-minute situations and late-game script (trailing / leading in the 4th);
  - FG make probability by kick distance (logistic), FG distance by start field position, extra point and
    two-point rates, the chance a turnover is returned for a touchdown;
  - drive duration by result and situation, scaled by each offense's neutral pace;
  - where the next drive starts, given how this one ended and where it started (kickoffs, punts, turnovers).
The link from ratings to drives borrows last season's drives for sample size (team ratings never do).
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from .data import f
from .ratings import rating_plays, team_ratings

CLASSES = ["td", "fg", "punt", "turnover", "downs", "safety"]
TD, FG, PUNT, TO, DOWNS, SAFETY = range(6)
RESULT = {"Touchdown": TD, "Field goal": FG, "Missed field goal": FG, "Punt": PUNT, "Turnover": TO, "Opp touchdown": TO,
          "Turnover on downs": DOWNS, "Safety": SAFETY}
SCRIMMAGE = ("pass", "run", "qb_kneel", "qb_spike", "punt", "field_goal")
L2 = 2.0


def _top(s: str) -> float:
    try:
        m, sec = s.split(":")
        return int(m) * 60 + int(sec)
    except (ValueError, AttributeError):
        return 0.0


def clock_situation(half_sec, qtr, diff) -> str:
    """Tempo bucket for drive length: two-minute drill, 4th-quarter lead (milking), 4th-quarter deficit (hurry), normal."""
    if half_sec < 150:
        return "two"
    if qtr >= 4 and half_sec < 600:
        return "lead" if diff > 0 else "trail" if diff < 0 else "norm"
    return "norm"


def build_drives(plays: list[dict]) -> list[dict]:
    """One row per drive: teams, start spot/clock/score, result, plays, time of possession, FG distance."""
    by = defaultdict(list)
    for p in plays:
        if p["posteam"] and p["fixed_drive"]:
            by[(p["game_id"], p["fixed_drive"])].append(p)
    out = []
    for (gid, dn), ps in by.items():
        first = next((p for p in ps if p["play_type"] in SCRIMMAGE and f(p["yardline_100"]) is not None), None)
        if first is None:
            continue
        res = ps[-1]["fixed_drive_result"]
        fgd = next((f(p["kick_distance"]) for p in ps if p["play_type"] == "field_goal" and f(p["kick_distance"])), None)
        out.append({"game_id": gid, "drive": int(f(dn, 0)), "season": first["season"], "week": int(f(first["week"], 0)),
                    "game_date": first["game_date"], "posteam": first["posteam"], "defteam": first["defteam"],
                    "home": first["posteam"] == first["home_team"], "yl": f(first["yardline_100"]),
                    "half_sec": f(first["half_seconds_remaining"], 1800), "qtr": int(f(first["qtr"], 1)),
                    "score_diff": f(first["score_differential"], 0) or 0.0, "result": res, "cls": RESULT.get(res),
                    "opp_td": res == "Opp touchdown", "plays": int(f(ps[-1]["drive_play_count"], 0) or 0),
                    "top": _top(ps[-1]["drive_time_of_possession"]), "fg_dist": fgd,
                    "start": first["drive_start_transition"]})
    out.sort(key=lambda d: (d["game_id"], d["drive"]))
    return out


def situation(yl, ratings_off, ratings_def, home, half_sec, qtr, diff):
    """Feature vector for one drive (also used, vectorised, by the engine)."""
    late = (qtr >= 4) & (half_sec < 600)
    return np.stack([np.ones_like(yl), yl / 100, (yl / 100) ** 2, ratings_off[0], ratings_def[0], ratings_off[1] * 0.5,
                     ratings_def[1] * 0.5, home.astype(float), (late & (diff < 0) & (diff >= -16)).astype(float),
                     (late & (diff > 0)).astype(float), (half_sec < 150).astype(float)], axis=-1)


def week_ratings(plays: list[dict]) -> dict:
    """{(season, week): ratings from that season's plays in earlier weeks} - the no-leak ratings drives are fitted on."""
    rp = rating_plays(plays)
    by_season = defaultdict(list)
    for p in rp:
        by_season[p["season"]].append(p)
    out = {}
    for s, ps in by_season.items():
        weeks = sorted({int(p["week"]) for p in ps})
        for w in range(1, max(weeks) + 2):
            out[(s, w)] = team_ratings([p for p in ps if int(p["week"]) < w])
    return out


def _softmax_fit(X, y, K, l2=L2, iters=40):
    n, P = X.shape
    W = np.zeros((K, P))
    Y = np.eye(K)[y]
    for _ in range(iters):
        Z = X @ W.T
        Z -= Z.max(1, keepdims=True)
        Pm = np.exp(Z)
        Pm /= Pm.sum(1, keepdims=True)
        G = (Pm - Y).T @ X + l2 * W
        G[:, 0] -= l2 * W[:, 0]          # no penalty on intercepts
        H = np.zeros((K * P, K * P))
        for a in range(K):
            for b in range(K):
                w = Pm[:, a] * ((a == b) - Pm[:, b])
                H[a * P:(a + 1) * P, b * P:(b + 1) * P] = X.T @ (X * w[:, None])
        H += l2 * np.eye(K * P)
        H += 1e-6 * np.eye(K * P)
        step = np.linalg.lstsq(H, G.reshape(-1), rcond=None)[0].reshape(K, P)
        W -= step
        if np.abs(step).max() < 1e-7:
            break
    return W


def fit(plays: list[dict], drives: list[dict] | None = None, before: str | None = None, wind: dict | None = None) -> dict:
    """Fit every piece of the drive model on plays/drives strictly before `before`."""
    plays = [p for p in plays if not before or p["game_date"] < before]
    drives = [d for d in (drives or build_drives(plays)) if not before or d["game_date"] < before]
    wr = week_ratings(plays)

    def r_of(d, side):
        t = wr.get((d["season"], d["week"]), {"teams": {}})["teams"]
        x = t.get(d[side], {})
        return (x.get("off_epa" if side == "posteam" else "def_epa", 0.0), x.get("off_sr" if side == "posteam" else "def_sr", 0.0))

    fit_d = [d for d in drives if d["cls"] is not None and d["yl"] is not None]
    yl = np.array([d["yl"] for d in fit_d])
    ro = np.array([r_of(d, "posteam") for d in fit_d]).T
    rd = np.array([r_of(d, "defteam") for d in fit_d]).T
    X = situation(yl, ro, rd, np.array([d["home"] for d in fit_d]), np.array([d["half_sec"] for d in fit_d]),
                  np.array([d["qtr"] for d in fit_d]), np.array([d["score_diff"] for d in fit_d]))
    y = np.array([d["cls"] for d in fit_d])
    W = _softmax_fit(X, y, len(CLASSES))

    # field goals: make probability by distance, and distance by start bucket
    # wind: game-level mph from the nflverse schedule (domes count as 0), centred on its mean
    wind = wind or {}
    fga = [(f(p["kick_distance"]), p["field_goal_result"] == "made", wind.get(p["game_id"], 0.0)) for p in plays
           if p["play_type"] == "field_goal" and f(p["kick_distance"]) and p["field_goal_result"]]
    wbar = float(np.mean([w for _, _, w in fga])) if fga else 0.0
    Xf = np.array([[1.0, (d - 40) / 10, (w - wbar) / 10] for d, _, w in fga])
    yf = np.array([m for _, m, _ in fga], dtype=float)
    bf = np.zeros(3)
    for _ in range(30):
        pf = 1 / (1 + np.exp(-Xf @ bf))
        H = Xf.T @ (Xf * (pf * (1 - pf))[:, None]) + 1e-6 * np.eye(3)
        bf -= np.linalg.solve(H, Xf.T @ (pf - yf))
    fg_wind = {"coef_per_10mph": float(bf[2]), "mean_wind": wbar, "n_with_wind": sum(1 for *_, w in fga if w > 0)}
    bf = bf[:2]
    bucket = lambda v: int(min(9, max(0, v // 10)))
    fg_dist = defaultdict(list)
    for d in drives:
        if d["cls"] == FG and d["fg_dist"]:
            fg_dist[bucket(d["yl"])].append(d["fg_dist"])
    # conversions and defensive touchdowns
    xp = [p["extra_point_result"] == "good" for p in plays if p["extra_point_result"] in ("good", "failed", "blocked")]
    two = [p["two_point_conv_result"] == "success" for p in plays if p["two_point_conv_result"] in ("success", "failure")]
    tos = [d for d in drives if d["cls"] == TO]
    # durations by result and two-minute status; and next-drive start spots
    dur = defaultdict(list)
    for d in drives:
        if d["cls"] is not None and d["top"] > 0:
            dur[(d["cls"], clock_situation(d["half_sec"], d["qtr"], d["score_diff"]))].append(d["top"])
    for k in [k for k, v in dur.items() if len(v) < 30 and k[1] != "norm"]:
        dur[k] = dur[(k[0], "norm")]          # too few drives in that situation: fall back to normal tempo
    nxt = defaultdict(list)
    kick = []
    for a, b in zip(drives, drives[1:]):
        if a["game_id"] != b["game_id"] or a["posteam"] == b["posteam"] or b["yl"] is None or a["yl"] is None:
            continue
        if b["start"] in ("KICKOFF", "ONSIDE_KICK") and a["cls"] in (TD, FG, None):
            kick.append(b["yl"])
        elif a["cls"] in (PUNT, TO, DOWNS, FG, SAFETY):
            nxt[(a["cls"], bucket(a["yl"]))].append(b["yl"])
    # game-to-game wobble in a team's offensive EPA/play beyond play-level noise
    rp = rating_plays(plays)
    g = defaultdict(list)
    for p in rp:
        g[(p["season"], p["posteam"], p["game_id"])].append(float(p["epa"]))
    team_means = defaultdict(list)
    for (s, t, gid), v in g.items():
        team_means[(s, t)].append((np.mean(v), np.var(v) / max(len(v), 1)))
    resid, noise = [], []
    for v in team_means.values():
        if len(v) < 3:
            continue
        m = np.mean([x for x, _ in v])
        resid += [(x - m) ** 2 * len(v) / (len(v) - 1) for x, _ in v]
        noise += [s2 for _, s2 in v]
    sigma_game = float(np.sqrt(max(np.mean(resid) - np.mean(noise), 0.0))) if resid else 0.08
    # shared pace: covariance of the two teams' (log) drive lengths in the same game, relative to their averages
    td = defaultdict(list)
    for d in drives:
        if d["top"] > 0 and d["cls"] in (PUNT, TD, FG, TO, DOWNS) and clock_situation(d["half_sec"], d["qtr"], d["score_diff"]) == "norm":
            td[(d["game_id"], d["posteam"])].append(np.log(d["top"]))
    team_avg = defaultdict(list)
    for (gid, t), v in td.items():
        team_avg[t].append(np.mean(v))
    tavg = {t: np.mean(v) for t, v in team_avg.items()}
    pairs = defaultdict(dict)
    for (gid, t), v in td.items():
        pairs[gid][t] = np.mean(v) - tavg[t]
    xy = np.array([list(v.values()) for v in pairs.values() if len(v) == 2])
    pace_sd = float(np.sqrt(max(np.cov(xy.T)[0, 1], 0.0))) if len(xy) > 20 else 0.05
    return {"W": W, "classes": CLASSES, "fg_beta": bf, "fg_dist": {k: np.array(v) for k, v in fg_dist.items()},
            "xp": float(np.mean(xp)) if xp else 0.95, "two": float(np.mean(two)) if two else 0.48,
            "p_def_td": sum(d["opp_td"] for d in tos) / max(len(tos), 1),
            "dur": {k: np.array(v) for k, v in dur.items()}, "next": {k: np.array(v) for k, v in nxt.items()},
            "kick": np.array(kick) if kick else np.array([70.0]), "sigma_game": sigma_game, "pace_sd": pace_sd, "fg_wind": fg_wind,
            "n_drives": len(fit_d), "n_fga": len(fga), "seasons": sorted({d["season"] for d in fit_d}),
            "class_rates": np.bincount(y, minlength=len(CLASSES)) / len(y)}
