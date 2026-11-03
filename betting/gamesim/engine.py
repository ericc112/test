"""The simulation: one NFL game, drive by drive, with the clock, vectorised over all simulations at once.

Each simulated game first draws its environment, then plays drives inside it:
  - environment: a game-day shock to each offense's EPA/play (sd fitted from game-to-game wobble) and a shared
    pace shock that stretches or shortens every drive for both teams (fitted from how teams' drive lengths
    move together within games);
  - each drive: result from the fitted drive model at the current spot, clock and score; its length from the
    observed lengths for that result and tempo (normal, two-minute drill, protecting a 4th-quarter lead,
    chasing a 4th-quarter deficit), scaled by the offense's pace; then points and the next start spot;
  - scoring keeps the 3/7 structure: TDs with an extra point or a two-point try (two-point chart in the 4th
    quarter and overtime), FGs made by distance, safeties, defensive return TDs;
  - endgame: a team leading with two minutes or less kneels it out; drives that run out of clock at the half
    keep their score only in proportion to the time left (FG tries get most of it);
  - overtime (regular season since 2025): 10 minutes, both teams get a possession, then sudden death; ties stand.
"""
from __future__ import annotations

import numpy as np

from .drives import DOWNS, FG, PUNT, SAFETY, TD, TO, situation

TWO_POINT_CHART = {-2, -5, -9, -10, -12, -13, 1, 5, 12}   # margin after the TD's 6 points: go for two
END = 6


TEMPO = {"norm": 0, "two": 1, "lead": 2, "trail": 3}


def _codes(pools: dict, enc) -> dict:
    return {enc(k): v for k, v in pools.items() if len(v)}


def _pick(rng, pools: dict, codes: np.ndarray, default: np.ndarray) -> np.ndarray:
    """Draw one value per integer code from that code's empirical pool."""
    codes = np.asarray(codes)
    out = np.empty(codes.size)
    for k in np.unique(codes):
        m = codes == k
        pool = pools.get(int(k))
        if pool is None or len(pool) == 0:
            pool = default
        out[m] = pool[rng.integers(0, len(pool), int(m.sum()))]
    return out


def simulate(game: dict, model: dict, n: int = 50000, seed: int = 2026, hfa: bool = True, env: bool = True,
             trace: int = 0) -> dict:
    """game: {"home": {...}, "away": {...}, "fg_wind_logit": float}; each side has off_epa, off_sr, def_epa, def_sr,
    pace_ratio and qb_delta (EPA/play added to the offense). Returns final scores and game details per simulation."""
    rng = np.random.default_rng(seed)
    W = model["W"]
    sides = (game["home"], game["away"])
    off_epa = np.array([s["off_epa"] + s.get("qb_delta", 0.0) for s in sides])
    off_sr = np.array([s["off_sr"] for s in sides])
    def_epa = np.array([s["def_epa"] for s in sides])
    def_sr = np.array([s["def_sr"] for s in sides])
    pace = np.array([s.get("pace_ratio", 1.0) for s in sides])
    shock = rng.normal(0, model["sigma_game"], (n, 2)) if env else np.zeros((n, 2))
    pace_sh = np.exp(rng.normal(0, model["pace_sd"], n)) if env else np.ones(n)
    dur_pool = _codes(model["dur"], lambda k: k[0] * 4 + TEMPO[k[1]])
    next_pool = _codes(model["next"], lambda k: k[0] * 10 + k[1])
    fg_pool = _codes(model["fg_dist"], int)
    kick_pool = {0: model["kick"]}
    fg_b = model["fg_beta"]
    fg_wind = game.get("fg_wind_logit", 0.0)
    all_fg = np.concatenate([v for v in model["fg_dist"].values()]) if model["fg_dist"] else np.array([40.0])
    bucket = lambda v: np.clip(v // 10, 0, 9).astype(int)

    score = np.zeros((n, 2), dtype=np.int64)
    half = np.ones(n, dtype=np.int64)          # 1, 2, 3 = overtime
    clock = np.full(n, 1800.0)                 # seconds left in this half (600 in overtime)
    recv1 = (rng.random(n) < 0.5).astype(np.int64)   # who receives the opening kickoff (0 home, 1 away)
    poss = recv1.copy()
    yl = _pick(rng, kick_pool, np.zeros(n, int), model["kick"])
    done = np.zeros(n, dtype=bool)
    ot_poss = np.zeros((n, 2), dtype=np.int64)
    drives = np.zeros(n, dtype=np.int64)
    went_ot = np.zeros(n, dtype=bool)
    first_score = np.full(n, -1)
    log = [[] for _ in range(trace)]          # optional drive-by-drive record of the first `trace` games
    stats = {"iterations": 0, "drives": 0}

    for _ in range(80):
        a = np.flatnonzero(~done)
        if a.size == 0:
            break
        stats["iterations"] += 1
        stats["drives"] += int(a.size)
        pre = {"half": half[a].copy(), "clock": clock[a].copy(), "yl": yl[a].copy(), "score": score[a].copy()} if trace else None
        o, d = poss[a], 1 - poss[a]
        diff = score[a, o] - score[a, d]
        qtr = np.where(half[a] == 1, np.where(clock[a] > 900, 1, 2), np.where(half[a] == 2, np.where(clock[a] > 900, 3, 4), 5))
        # kneel-downs: leading with two minutes or less in the 4th (or overtime), or running out the first half
        kneel = ((half[a] >= 2) & (qtr >= 4) & (diff > 0) & (clock[a] <= 120)) | ((half[a] == 1) & (clock[a] <= 30) & (yl[a] > 60))
        r_off = (off_epa[o] + shock[a, o], off_sr[o])
        r_def = (def_epa[d], def_sr[d])
        home_flag = (o == 0) & hfa
        X = situation(yl[a], r_off, r_def, home_flag, clock[a], qtr, diff)
        Z = X @ W.T
        Z -= Z.max(1, keepdims=True)
        P = np.exp(Z)
        P /= P.sum(1, keepdims=True)
        cls = (rng.random(a.size)[:, None] > np.cumsum(P, 1)).sum(1)
        cls = np.minimum(cls, SAFETY)
        # drive length by result and tempo, scaled by the offense's pace and the game's shared pace
        tempo = np.where(clock[a] < 150, 1, np.where((qtr >= 4) & (clock[a] < 600), np.where(diff > 0, 2, np.where(diff < 0, 3, 0)), 0))
        dur = _pick(rng, dur_pool, cls * 4 + tempo, model["dur"].get((PUNT, "norm"), np.array([150.0])))
        dur = dur * np.where(tempo == 1, 1.0, pace[o] * pace_sh[a])
        # out of time: the score stands only in proportion to the clock left (FG tries keep most of it)
        short = dur > clock[a]
        keep = np.where(cls == FG, np.minimum(1, 2 * clock[a] / np.maximum(dur, 1)), clock[a] / np.maximum(dur, 1))
        cut = short & (rng.random(a.size) > keep)
        cls = np.where(cut | kneel, END, cls)
        dur = np.where(kneel, clock[a], np.minimum(dur, clock[a]))
        drives[a] += 1

        # points and the next start spot
        new_poss = d.copy()
        new_yl = _pick(rng, kick_pool, np.zeros(a.size, int), model["kick"])          # default: kickoff to the defense
        b = bucket(yl[a])
        is_td = cls == TD
        m6 = diff + 6
        late = qtr >= 4
        go2 = is_td & late & np.isin(m6, list(TWO_POINT_CHART))
        conv = np.where(go2, 2 * (rng.random(a.size) < model["two"]), 1 * (rng.random(a.size) < model["xp"]))
        pts_off = np.where(is_td, 6 + conv, 0)
        is_fg = cls == FG
        dist = np.where(is_fg, _pick(rng, fg_pool, b, all_fg), 0)
        p_make = 1 / (1 + np.exp(-(fg_b[0] + fg_b[1] * (dist - 40) / 10 + fg_wind)))
        made = is_fg & (rng.random(a.size) < p_make)
        pts_off = pts_off + np.where(made, 3, 0)
        missed = is_fg & ~made
        for c in (PUNT, TO, DOWNS):
            m = cls == c
            if m.any():
                new_yl[m] = _pick(rng, next_pool, c * 10 + b[m], np.clip(100 - yl[a][m], 1, 99))
        if missed.any():
            new_yl[missed] = _pick(rng, next_pool, FG * 10 + b[missed], np.clip(100 - yl[a][missed] - 7, 1, 99))
        def_td = (cls == TO) & (rng.random(a.size) < model["p_def_td"])
        pts_def = np.where(def_td, 6 + (rng.random(a.size) < model["xp"]), 0) + np.where(cls == SAFETY, 2, 0)
        new_poss = np.where(def_td, o, new_poss)           # after a return TD the original offense receives the kickoff
        if (cls == SAFETY).any():
            new_yl[cls == SAFETY] = _pick(rng, next_pool, np.full(int((cls == SAFETY).sum()), SAFETY * 10), np.array([60.0]))
        # end of half from a cut drive or kneel: no change of possession matters, the half is over
        score[a, o] += pts_off
        score[a, d] += pts_def
        scored = (pts_off > 0) | (pts_def > 0)
        fs = (first_score[a] < 0) & scored
        first_score[a[fs]] = np.where(pts_off[fs] > 0, o[fs], d[fs])
        if trace:
            names = ["TD", "FG try", "Punt", "Turnover", "Downs", "Safety", "End of half / kneel"]
            for j in np.flatnonzero(a < trace):
                g = int(a[j])
                log[g].append({"half": int(pre["half"][j]), "clock": float(pre["clock"][j]), "off": int(o[j]), "start_yl": float(pre["yl"][j]),
                               "p_td": float(P[j, TD]), "result": names[int(cls[j])], "fg_dist": float(dist[j]) if cls[j] == FG else None,
                               "fg_made": bool(made[j]) if cls[j] == FG else None, "conv": int(conv[j]) if cls[j] == TD else None,
                               "def_td": bool(def_td[j]), "secs": float(dur[j]), "pts_off": int(pts_off[j]), "pts_def": int(pts_def[j]),
                               "score_after": (int(score[g, 0]), int(score[g, 1]))})
        clock[a] -= dur
        poss[a] = new_poss
        yl[a] = np.clip(new_yl, 1, 99)

        # overtime bookkeeping: both teams get a possession, then the next score wins
        ot = half[a] == 3
        if ot.any():
            ot_poss[a[ot], o[ot]] += 1
            both = (ot_poss[a, 0] >= 1) & (ot_poss[a, 1] >= 1)
            fin = ot & both & (score[a, 0] != score[a, 1])
            done[a[fin]] = True
        # half and game transitions
        over = (clock[a] <= 0) & ~done[a]
        h_now = half[a].copy()                          # decide every transition from the state before any of them
        k4 = a[kneel & (h_now >= 2)]                   # a kneel in the 4th quarter or overtime ends the game
        done[k4] = True
        over &= ~done[a]
        h1 = a[over & (h_now == 1)]
        h2 = a[over & (h_now == 2)]
        h3 = a[over & (h_now == 3)]
        half[h1], clock[h1], poss[h1] = 2, 1800.0, 1 - recv1[h1]
        yl[h1] = _pick(rng, kick_pool, np.zeros(h1.size, int), model["kick"])
        tied = score[h2, 0] == score[h2, 1]
        done[h2[~tied]] = True
        t = h2[tied]
        half[t], clock[t], went_ot[t] = 3, 600.0, True
        poss[t] = (rng.random(t.size) < 0.5).astype(np.int64)
        yl[t] = _pick(rng, kick_pool, np.zeros(t.size, int), model["kick"])
        done[h3] = True                                  # overtime clock ran out: a tie stands

    return {"home": score[:, 0], "away": score[:, 1], "ot": went_ot, "drives": drives, "first_score": first_score,
            "trace": log, "stats": stats}


def summary(sim: dict, spread_home: float | None = None, total: float | None = None) -> dict:
    """Probabilities with Monte Carlo standard errors, distributions and the most common results."""
    h, a = sim["home"], sim["away"]
    n = len(h)
    se = lambda p: float(np.sqrt(p * (1 - p) / n))
    out = {"n": n}
    for name, m in (("home_win", h > a), ("away_win", a > h), ("tie", h == a)):
        p = float(m.mean())
        out[name] = (p, se(p))
    out["ot"] = (float(sim["ot"].mean()), se(float(sim["ot"].mean())))
    marg, tot = h - a, h + a
    out["margin_mean"], out["margin_sd"] = float(marg.mean()), float(marg.std())
    out["total_mean"], out["total_median"], out["total_sd"] = float(tot.mean()), float(np.median(tot)), float(tot.std())
    out["home_mean"], out["away_mean"] = float(h.mean()), float(a.mean())
    if spread_home is not None:
        c = marg + spread_home
        win, push = float((c > 0).mean()), float((c == 0).mean())
        out["home_cover"] = (win / max(1 - push, 1e-9), se(win)) if push < 1 else (0.0, 0.0)
        out["spread_push"] = push
    if total is not None:
        ov, push = float((tot > total).mean()), float((tot == total).mean())
        out["over"] = (ov / max(1 - push, 1e-9), se(ov))
        out["total_push"] = push
    vals, cnt = np.unique(np.stack([h, a], 1), axis=0, return_counts=True)
    top = np.argsort(-cnt)[:10]
    out["top_scores"] = [(int(vals[i, 0]), int(vals[i, 1]), float(cnt[i] / n)) for i in top]
    mv, mc = np.unique(marg, return_counts=True)
    topm = np.argsort(-mc)[:10]
    out["top_margins"] = [(int(mv[i]), float(mc[i] / n)) for i in topm]
    return out
