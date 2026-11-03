"""NFL play-by-play engine: every snap, with downs, distance, field position, clock and timeouts.

Fitted on nflverse play-by-play before the game (team and QB ratings from the current season only):
  play call      run vs pass on downs 1-3 (logistic: down, distance, field position, score, clock, team tendency);
                 4th down go / punt / field goal (multinomial: distance, field position, score, clock, FG range)
  pass result    complete / incomplete / interception / sack (multinomial on situation) plus QB and pass-defense
                 offsets (opponent-adjusted ridge per dropback; last season's dropbacks at half weight for QBs)
  yards          gains drawn from real plays of the same type, distance and field zone, scaled by the matchup
                 (offense yards per completion / per carry against what the defense allows) and the game shock
  turnovers      interceptions (air yards + return from real picks), lost fumbles, pick-sixes falling out of the returns
  penalties      pre-snap / no-play penalties by side, with real yardages and automatic first downs
  clock          seconds until the next snap drawn from real snap-to-snap times by play result and tempo
                 (normal, hurry-up, milking a lead); timeouts used by the trailing team late; two-minute warning
  special teams  punts (net distance and touchbacks by spot), kickoffs (real start spots), onside kicks when
                 trailing late (real recovery rate), field goals by distance and wind, extra points, two-point tries
  endgame        kneel-downs when the clock can be run out, last-snap field goals, 2025 overtime rules
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from . import ratings as R
from .data import f
from .drives import _softmax_fit, build_drives
from .engine import TWO_POINT_CHART, _pick

RUN, PASS, PUNT, FGA, KNEEL = range(5)
COMP, INC, INT, SACK = range(4)
TEMPO = {"norm": 0, "hurry": 1, "milk": 2}
CAT = {"run_in": 0, "comp_in": 1, "inc": 2, "oob": 3, "sack": 4, "pen": 5, "kneel": 6}
LAM_RATE = 150.0      # dropbacks / carries of league-average prior on team and QB play ratings


def _i(x, d=0):
    v = f(x)
    return d if v is None else int(v)


def tempo_of(qtr, half_sec, diff):
    """Hurry-up: end of the first half, or chasing in the 4th. Milk: protecting a 4th-quarter lead."""
    q, h, d = np.asarray(qtr), np.asarray(half_sec), np.asarray(diff)
    hurry = ((q == 2) & (h < 120)) | ((q >= 4) & (h < 300) & (d <= 0)) | ((q >= 4) & (h < 600) & (d < -8))
    milk = (q >= 4) & (h < 600) & (d > 0)
    return np.where(hurry, 1, np.where(milk, 2, 0))


def _ybin(togo):
    t = np.asarray(togo)
    return np.where(t <= 3, 0, np.where(t <= 7, 1, np.where(t <= 12, 2, 3)))


def _zbin(yl):
    y = np.asarray(yl)
    return np.where(y <= 10, 0, np.where(y <= 20, 1, np.where(y <= 40, 2, np.where(y <= 80, 3, 4))))


RZ_EDGES = np.array([1, 2, 3, 5, 7, 10, 13, 16, 20])


def pool_key(down, togo, yl):
    """Yards pool: inside the 20 by fine distance-to-goal bucket (real gains stop at the goal line, so borrowing a
    gain from a different spot would bias touchdowns); elsewhere by down group x distance x field zone."""
    down, togo, yl = np.asarray(down), np.asarray(togo), np.asarray(yl)
    dg = (down >= 3).astype(int)
    rz = 100 + dg * 10 + np.searchsorted(RZ_EDGES, np.ceil(yl))
    out = dg * 20 + _ybin(togo) * 5 + _zbin(yl)
    return np.where(yl <= 20, rz, out)


def _gain(g0, yl, mult):
    """Whole-yard gain. Inside the 20 the pool holds shares of the distance to goal (1.0 = touchdown, never scaled
    down); elsewhere raw yards, with gains scaled by the matchup and game multipliers."""
    rz = yl <= 20
    rz_gain = np.where(g0 >= 1.0, yl, np.where(g0 > 0, np.maximum(1, np.minimum(np.rint(g0 * yl * mult), yl - 1)), g0))
    out_gain = np.where(g0 > 0, np.maximum(1, np.rint(g0 * mult)), g0)
    return np.where(rz, rz_gain, out_gain)


def _call_x(down, togo, yl, diff, tempo, q2end):
    return np.stack([np.ones_like(yl, dtype=float), (down == 2).astype(float), (down == 3).astype(float), np.log(np.maximum(togo, 1)),
                     yl / 100, np.clip(diff, -21, 21) / 10, (tempo == 1).astype(float), (tempo == 2).astype(float),
                     q2end.astype(float)], -1)


def _fourth_x(yl, togo, diff, qtr, half_sec):
    late = (qtr >= 4) & (half_sec < 600)
    return np.stack([np.ones_like(yl, dtype=float), yl / 100, (yl / 100) ** 2, np.log(np.maximum(togo, 1)), np.clip(diff, -21, 21) / 10,
                     (late & (diff < 0)).astype(float), (late & (diff > 0)).astype(float), ((qtr == 2) & (half_sec < 120)).astype(float),
                     np.clip((yl + 17 - 45) / 10, -3, 3)], -1)


def _pass_x(down, togo, yl, tempo):
    return np.stack([np.ones_like(yl, dtype=float), (down == 2).astype(float), (down == 3).astype(float), np.log(np.maximum(togo, 1)),
                     yl / 100, (yl <= 10).astype(float), (tempo == 1).astype(float)], -1)


def _logistic(X, y, l2=1.0, iters=30):
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b))
        g = X.T @ (p - y) + l2 * np.r_[0, b[1:]]
        H = X.T @ (X * (p * (1 - p))[:, None]) + l2 * np.eye(X.shape[1])
        b -= np.linalg.solve(H, g)
    return b


def fit(plays: list[dict], before: str, wind: dict | None = None, fg_beta=None, fg_wind=None) -> dict:
    """League play model from all plays before `before` (2025 and earlier 2026)."""
    P = [p for p in plays if p["game_date"] < before]
    P.sort(key=lambda p: (p["game_id"], f(p["play_id"], 0)))
    scr = [p for p in P if p["play_type"] in ("run", "pass") and p["down"] and p["qb_kneel"] != "1" and p["qb_spike"] != "1"
           and f(p["yardline_100"]) is not None and f(p["ydstogo"]) is not None]
    g = lambda k: np.array([f(p[k], 0) or 0 for p in scr], dtype=float)
    down, togo, yl, diff = g("down"), g("ydstogo"), g("yardline_100"), g("score_differential")
    qtr, hs = g("qtr"), g("half_seconds_remaining")
    tempo = tempo_of(qtr, hs, diff)
    q2end = (qtr == 2) & (hs < 120)
    is_pass = np.array([p["play_type"] == "pass" for p in scr])
    # run vs pass (downs 1-3)
    m = down <= 3
    b_call = _logistic(_call_x(down[m], togo[m], yl[m], diff[m], tempo[m], q2end[m]), is_pass[m].astype(float))
    # 4th down: go / punt / field goal
    fourth = [p for p in P if p["down"] == "4" and p["play_type"] in ("run", "pass", "punt", "field_goal") and f(p["yardline_100"]) is not None]
    g4 = lambda k: np.array([f(p[k], 0) or 0 for p in fourth], dtype=float)
    y4 = np.array([{"run": 0, "pass": 0, "punt": 1, "field_goal": 2}[p["play_type"]] for p in fourth])
    W4 = _softmax_fit(_fourth_x(g4("yardline_100"), g4("ydstogo"), g4("score_differential"), g4("qtr"), g4("half_seconds_remaining")), y4, 3, l2=1.0)
    # pass results
    ps = [p for p in scr if p["play_type"] == "pass"]
    pr = np.array([SACK if p["sack"] == "1" else INT if p["interception"] == "1" else COMP if p["complete_pass"] == "1" else INC for p in ps])
    gp = lambda k: np.array([f(p[k], 0) or 0 for p in ps], dtype=float)
    pd_, pt, pyl, pdi, pq, phs = gp("down"), gp("ydstogo"), gp("yardline_100"), gp("score_differential"), gp("qtr"), gp("half_seconds_remaining")
    Wp = _softmax_fit(_pass_x(pd_, pt, pyl, tempo_of(pq, phs, pdi)), pr, 4, l2=1.0)
    # yards pools by distance bin x field zone
    pools = defaultdict(list)
    keys = pool_key(down, togo, yl)
    for p, key, y0 in zip(scr, keys.tolist(), yl.tolist()):
        yg = f(p["yards_gained"], 0) or 0
        if key >= 100 and yg > 0 and p["play_type"] in ("run", "pass"):
            yg = min(yg / y0, 1.0)         # inside the 20: a gain is a share of the distance to goal (1.0 = touchdown)
        if p["play_type"] == "run":
            pools[("run", key)].append(yg)
        elif p["complete_pass"] == "1":
            pools[("comp", key)].append(yg)
        elif p["sack"] == "1":
            pools[("sack", 0)].append(yg)
        elif p["interception"] == "1":
            pools[("int_air", 0)].append(f(p["air_yards"], 10) or 10)
            pools[("int_ret", 0)].append(f(p["return_yards"], 0) or 0)
    fum_run = np.mean([p["fumble_lost"] == "1" for p in scr if p["play_type"] == "run"])
    fum_comp = np.mean([p["fumble_lost"] == "1" for p in ps if p["complete_pass"] == "1"])
    # penalties (no-play snaps), by side
    snaps = [p for p in P if p["down"] and p["play_type"] in ("run", "pass", "no_play", "punt", "field_goal")]
    pens = [p for p in snaps if p["play_type"] == "no_play" and p["penalty"] == "1" and f(p["penalty_yards"]) is not None]
    p_pen = len(pens) / max(len(snaps), 1)
    off_pen = [p for p in pens if p["penalty_team"] == p["posteam"]]
    def_pen = [p for p in pens if p["penalty_team"] == p["defteam"]]
    pen = {"p": p_pen, "p_off": len(off_pen) / max(len(pens), 1), "off_yds": np.array([f(p["penalty_yards"]) for p in off_pen] or [5.0]),
           "def_yds": np.array([f(p["penalty_yards"]) for p in def_pen] or [5.0]),
           "def_first": float(np.mean([p["first_down_penalty"] == "1" for p in def_pen])) if def_pen else 0.3}
    # clock: seconds to the next snap, by result and tempo (no timeout in between, not across the 2:00 warning)
    run_off = defaultdict(list)
    for a, b in zip(P, P[1:]):
        if a["game_id"] != b["game_id"] or a["qtr"] != b["qtr"] and not (a["qtr"] in ("1", "3") and b["qtr"] in ("2", "4")):
            continue
        if b["timeout"] == "1" or a["play_type"] not in ("run", "pass", "no_play", "qb_kneel") or not a["down"]:
            continue
        if a["touchdown"] == "1" or a["interception"] == "1" or a["fumble_lost"] == "1":
            continue
        dt = (f(a["game_seconds_remaining"], 0) or 0) - (f(b["game_seconds_remaining"], 0) or 0)
        hs = f(a["half_seconds_remaining"], 0) or 0
        if dt < 0 or dt > 60 or (hs > 120 and hs - dt < 120):
            continue
        if a["play_type"] == "qb_kneel":
            cat = "kneel"
        elif a["play_type"] == "no_play":
            cat = "pen"
        elif a["sack"] == "1":
            cat = "sack"
        elif a["play_type"] == "pass" and a["complete_pass"] != "1":
            cat = "inc"
        elif a["out_of_bounds"] == "1":
            cat = "oob"
        else:
            cat = "comp_in" if a["play_type"] == "pass" else "run_in"
        t = int(tempo_of(_i(a["qtr"]), hs, f(a["score_differential"], 0) or 0))
        run_off[CAT[cat] * 3 + t].append(dt)
    # special teams
    punts = [p for p in P if p["play_type"] == "punt" and p["punt_blocked"] != "1" and f(p["yardline_100"]) is not None]
    punt_pool = defaultdict(list)
    for p in punts:
        y = f(p["yardline_100"])
        z = int(min(9, y // 10))
        if p["touchback"] == "1":
            punt_pool[z].append(80.0)                                     # receiver's distance to goal
        else:
            net = (f(p["kick_distance"], 40) or 40) - (f(p["return_yards"], 0) or 0)
            punt_pool[z].append(float(np.clip(100 - (y - net), 1, 99)))
    kicks = [p for p in P if p["play_type"] == "kickoff"]
    onside = [p for p in kicks if (f(p["kick_distance"], 60) or 60) <= 15]
    drives = build_drives(P)
    kick_start = np.array([d["yl"] for d in drives if d["start"] in ("KICKOFF",) and d["yl"] is not None] or [70.0])
    xp = [p["extra_point_result"] == "good" for p in P if p["extra_point_result"] in ("good", "failed", "blocked")]
    two = [p["two_point_conv_result"] == "success" for p in P if p["two_point_conv_result"] in ("success", "failure")]
    # game-to-game wobble in a team's yards per play and completion rate, beyond play-level noise
    by = defaultdict(list)
    for p in scr:
        by[(p["season"], p["posteam"], p["game_id"])].append(f(p["yards_gained"], 0) or 0)
    tm = defaultdict(list)
    for (s, t, gid), v in by.items():
        tm[(s, t)].append((np.mean(v), np.var(v) / max(len(v), 1)))
    res, noi = [], []
    for v in tm.values():
        if len(v) >= 3:
            mu = np.mean([x for x, _ in v])
            res += [(x - mu) ** 2 * len(v) / (len(v) - 1) for x, _ in v]
            noi += [s2 for _, s2 in v]
    lg_ypp = float(np.mean([f(p["yards_gained"], 0) or 0 for p in scr]))
    hy = [f(p["yards_gained"], 0) or 0 for p in scr if p["posteam"] == p["home_team"]]
    ay = [f(p["yards_gained"], 0) or 0 for p in scr if p["posteam"] == p["away_team"]]
    hfa_ypp = float(np.mean(hy) / np.mean(ay) - 1) if hy and ay else 0.0     # home offenses' yards per play edge
    yard_sd = float(np.sqrt(max(np.mean(res) - np.mean(noi), 0))) / lg_ypp if res else 0.15
    return {"b_call": b_call, "W4": W4, "Wp": Wp, "pools": {k: np.array(v, float) for k, v in pools.items()},
            "fum_run": float(fum_run), "fum_comp": float(fum_comp), "pen": pen,
            "run_off": {k: np.array(v, float) for k, v in run_off.items() if len(v) >= 20},
            "punt": {k: np.array(v, float) for k, v in punt_pool.items()}, "kick": kick_start,
            "onside_rate": float(np.mean([p["own_kickoff_recovery"] == "1" for p in onside])) if onside else 0.1,
            "n_onside": len(onside), "xp": float(np.mean(xp)) if xp else 0.95, "two": float(np.mean(two)) if two else 0.48,
            "fg_beta": fg_beta, "fg_wind": fg_wind, "yard_sd": yard_sd, "lg_ypp": lg_ypp,
            "lg": {"comp": float(np.mean(pr == COMP)), "sack": float(np.mean(pr == SACK)), "int": float(np.mean(pr == INT)),
                   "ypc_pass": float(np.mean([f(p["yards_gained"], 0) or 0 for p in ps if p["complete_pass"] == "1"])),
                   "ypr": float(np.mean([f(p["yards_gained"], 0) or 0 for p in scr if p["play_type"] == "run"])),
                   "pass_rate": float(is_pass[m].mean())},
            "hfa_ypp": hfa_ypp,
            "n_plays": len(scr), "n_fourth": len(fourth)}


def play_ratings(plays_now: list[dict], plays_prior: list[dict]) -> dict:
    """Opponent-adjusted play ratings. Passing is keyed by QB (so a starter change uses the starter's own numbers),
    rushing by team; defenses by team. Each is an additive effect on the league rate / yards (ridge)."""
    rp_now = [p for p in plays_now if p["play_type"] in ("run", "pass") and p["down"] and p["qb_kneel"] != "1" and p["qb_spike"] != "1"]
    rp_prior = [p for p in plays_prior if p["play_type"] in ("run", "pass") and p["down"] and p["qb_kneel"] != "1" and p["qb_spike"] != "1"]
    out = {"qb": defaultdict(dict), "team_off": defaultdict(dict), "team_def": defaultdict(dict), "pass_rate": {}}
    drop = [(p, 1.0) for p in rp_now if p["play_type"] == "pass" and p["passer_player_id"]] + \
           [(p, R.PRIOR_SEASON_WEIGHT) for p in rp_prior if p["play_type"] == "pass" and p["passer_player_id"]]
    rows, w = [x for x, _ in drop], [x for _, x in drop]
    for key, fn in (("comp", lambda r: float(r["complete_pass"] == "1")), ("sack", lambda r: float(r["sack"] == "1")),
                    ("int", lambda r: float(r["interception"] == "1"))):
        if rows:
            _, _, q, d, _ = R._ridge(rows, lambda r: r["passer_player_id"], lambda r: r["defteam"] + ":" + r["season"], fn, LAM_RATE, LAM_RATE, weights=w)
            for k, v in q.items():
                out["qb"][k][key] = v
            for k, v in d.items():
                if k.endswith(":" + (plays_now[0]["season"] if plays_now else "")):
                    out["team_def"][k.split(":")[0]][key] = v
    comps = [(p, wt) for p, wt in drop if p["complete_pass"] == "1"]
    if comps:
        _, _, q, d, _ = R._ridge([p for p, _ in comps], lambda r: r["passer_player_id"], lambda r: r["defteam"] + ":" + r["season"],
                                 lambda r: f(r["yards_gained"], 0) or 0, LAM_RATE / 2, LAM_RATE / 2, weights=[x for _, x in comps])
        for k, v in q.items():
            out["qb"][k]["ypc"] = v
        for k, v in d.items():
            if plays_now and k.endswith(":" + plays_now[0]["season"]):
                out["team_def"][k.split(":")[0]]["ypc"] = v
    runs = [p for p in rp_now if p["play_type"] == "run"]
    if runs:
        _, _, o, d, _ = R._ridge(runs, lambda r: r["posteam"], lambda r: r["defteam"], lambda r: f(r["yards_gained"], 0) or 0, LAM_RATE, LAM_RATE)
        for k, v in o.items():
            out["team_off"][k]["ypr"] = v
        for k, v in d.items():
            out["team_def"][k]["ypr"] = v
    # neutral-situation pass rate by team (downs 1-2, quarters 1-3, score within 7), shrunk
    c = defaultdict(lambda: [0, 0])
    lg = [0, 0]
    for p in rp_now:
        if p["down"] in ("1", "2") and _i(p["qtr"]) <= 3 and abs(f(p["score_differential"], 0) or 0) <= 7:
            c[p["posteam"]][0] += p["play_type"] == "pass"
            c[p["posteam"]][1] += 1
            lg[0] += p["play_type"] == "pass"
            lg[1] += 1
    lgr = lg[0] / lg[1] if lg[1] else 0.55
    out["pass_rate"] = {t: (v[0] + 60 * lgr) / (v[1] + 60) for t, v in c.items()}
    out["lg_neutral_pass"] = lgr
    return out


def side_inputs(pr: dict, team: str, opp: str, qb: str | None, M: dict) -> dict:
    """Offsets for one offense against one defense, in the units the engine uses."""
    lg = M["lg"]
    q = pr["qb"].get(qb, {}) if qb else {}
    d = pr["team_def"].get(opp, {})
    lo = lambda p: np.log(p / (1 - p))
    off = {}
    for k in ("comp", "sack", "int"):
        base = lg[k]
        p = np.clip(base + q.get(k, 0.0) + d.get(k, 0.0), 0.005, 0.95)
        off[k] = float(lo(p) - lo(base))
    ypc = max(lg["ypc_pass"] + q.get("ypc", 0.0) + d.get("ypc", 0.0), 4.0) / lg["ypc_pass"]
    ypr_lg = lg["ypr"]
    ypr = max(ypr_lg + pr["team_off"].get(team, {}).get("ypr", 0.0) + d.get("ypr", 0.0), 1.5) / ypr_lg
    tend = pr["pass_rate"].get(team, pr["lg_neutral_pass"])
    return {"comp": off["comp"], "sack": off["sack"], "int": off["int"], "ypc_mult": float(ypc), "ypr_mult": float(ypr),
            "pass_offset": float(lo(tend) - lo(pr["lg_neutral_pass"])), "qb_known": bool(q)}


def simulate(sides: dict, M: dict, n: int = 50000, seed: int = 2026, hfa: float = 0.0, fg_wind_logit: float = 0.0,
             env: bool = True, trace: int = 0) -> dict:
    """sides: {"home": side_inputs(...), "away": side_inputs(...)}. hfa: yards multiplier bonus for the home offense."""
    rng = np.random.default_rng(seed)
    S = (sides["home"], sides["away"])
    arr = lambda k: np.array([s[k] for s in S])
    comp_o, sack_o, int_o = arr("comp"), arr("sack"), arr("int")
    ypc_m, ypr_m, pass_o = arr("ypc_mult"), arr("ypr_mult"), arr("pass_offset")
    home_bonus = np.array([1 + hfa, 1.0])
    z = rng.standard_normal((n, 2)) if env else np.zeros((n, 2))
    ymult = np.exp(M["yard_sd"] * z - M["yard_sd"] ** 2 / 2)
    pools, pen = M["pools"], M["pen"]
    run_pool = {k[1]: v for k, v in pools.items() if k[0] == "run"}
    comp_pool = {k[1]: v for k, v in pools.items() if k[0] == "comp"}
    fgb = M["fg_beta"]

    score = np.zeros((n, 2), dtype=np.int64)
    half = np.ones(n, dtype=np.int64)
    clock = np.full(n, 1800.0)
    recv1 = (rng.random(n) < 0.5).astype(np.int64)
    poss = recv1.copy()
    yl = _pick(rng, {0: M["kick"]}, np.zeros(n, int), M["kick"])
    down = np.ones(n, dtype=np.int64)
    togo = np.minimum(10.0, yl)
    tos = np.full((n, 2), 3, dtype=np.int64)
    done = np.zeros(n, dtype=bool)
    ot_poss = np.zeros((n, 2), dtype=np.int64)
    went_ot = np.zeros(n, dtype=bool)
    nplays = np.zeros(n, dtype=np.int64)
    log = [[] for _ in range(trace)]
    stats = {"iterations": 0, "snaps": 0}
    lo = lambda p: np.log(p / (1 - p))

    def kickoff_to(idx, receiver, trailing_kicker_late=None):
        """Kick off to `receiver` (array, per sim in idx). Onside when the kicking team trails late."""
        st = _pick(rng, {0: M["kick"]}, np.zeros(idx.size, int), M["kick"])
        rec = receiver.copy()
        if trailing_kicker_late is not None and trailing_kicker_late.any():
            ons = trailing_kicker_late & (rng.random(idx.size) < M["onside_rate"])
            rec = np.where(ons, 1 - receiver, receiver)
            st = np.where(ons, 55.0, np.where(trailing_kicker_late, 50.0, st))      # failed onside: good field for the receiver
        poss[idx], yl[idx], down[idx] = rec, st, 1
        togo[idx] = np.minimum(10.0, st)

    for _ in range(600):
        a = np.flatnonzero(~done)
        if a.size == 0:
            break
        stats["iterations"] += 1
        stats["snaps"] += a.size
        o, d = poss[a], 1 - poss[a]
        diff = score[a, o] - score[a, d]
        hs = clock[a]
        qtr = np.where(half[a] == 1, np.where(hs > 900, 1, 2), np.where(half[a] == 2, np.where(hs > 900, 3, 4), 5))
        tp = tempo_of(qtr, hs, diff)
        y, dn, tg = yl[a], down[a], togo[a]
        nplays[a] += 1
        # ---- choose the play
        act = np.full(a.size, RUN)
        kneel = (qtr >= 4) & (diff > 0) & (dn <= 3) & (hs <= 42 * (4 - dn) - 38 * tos[a, d])
        kneel |= (qtr == 2) & (hs <= 40) & (y >= 60) & (diff >= 0)
        is4 = (dn == 4) & ~kneel
        if is4.any():
            Z = _fourth_x(y[is4], tg[is4], diff[is4], qtr[is4], hs[is4]) @ M["W4"].T
            Pz = np.exp(Z - Z.max(1, keepdims=True))
            Pz /= Pz.sum(1, keepdims=True)
            ch = (rng.random(is4.sum())[:, None] > np.cumsum(Pz, 1)).sum(1)
            act[is4] = np.where(ch == 1, PUNT, np.where(ch == 2, FGA, RUN))
        lastsnap = (hs <= 8) & (y + 17 <= 58) & ((qtr == 2) | ((qtr >= 4) & (diff >= -3) & (diff <= 0)))
        act = np.where(lastsnap & ~kneel, FGA, act)
        call = (act == RUN) & ~kneel
        xb = _call_x(np.minimum(dn, 3), tg, y, diff, tp, (qtr == 2) & (hs < 120)) @ M["b_call"] + pass_o[o]   # 4th-down go: 3rd-down mix
        act = np.where(call & (rng.random(a.size) < 1 / (1 + np.exp(-xb))), PASS, act)
        act = np.where(kneel, KNEEL, act)
        # pre-snap / no-play penalty
        penal = (act <= PASS) & (rng.random(a.size) < pen["p"])
        # ---- results
        gain = np.zeros(a.size)
        cat = np.full(a.size, CAT["run_in"])
        turnover = np.zeros(a.size, dtype=bool)        # possession changes at the spot (fumble, INT, downs)
        new_yl_to = np.zeros(a.size)
        pts_o = np.zeros(a.size, dtype=np.int64)
        pts_d = np.zeros(a.size, dtype=np.int64)
        kick_after = np.zeros(a.size, dtype=bool)      # scoring team kicks off
        punt_rec = np.zeros(a.size, dtype=bool)
        key = pool_key(dn, tg, y)
        # runs
        m = (act == RUN) & ~penal
        if m.any():
            g0 = _pick(rng, run_pool, key[m], pools[("run", 13)])
            gain[m] = _gain(g0, y[m], ypr_m[o[m]] * ymult[a[m], o[m]] * home_bonus[o[m]])
            fum = rng.random(m.sum()) < M["fum_run"]
            ii = np.flatnonzero(m)[fum]
            turnover[ii], new_yl_to[ii] = True, 100 - (y[ii] - gain[ii])
        # passes
        m = (act == PASS) & ~penal
        if m.any():
            Z = _pass_x(dn[m], tg[m], y[m], tp[m]) @ M["Wp"].T
            om = o[m]
            Z[:, COMP] += comp_o[om] + 0.5 * M["yard_sd"] * z[a[m], om]
            Z[:, SACK] += sack_o[om]
            Z[:, INT] += int_o[om]
            Pz = np.exp(Z - Z.max(1, keepdims=True))
            Pz /= Pz.sum(1, keepdims=True)
            r = (rng.random(m.sum())[:, None] > np.cumsum(Pz, 1)).sum(1)
            ii = np.flatnonzero(m)
            c = ii[r == COMP]
            if c.size:
                g0 = _pick(rng, comp_pool, key[c], pools[("comp", 13)])
                gain[c] = _gain(g0, y[c], ypc_m[o[c]] * ymult[a[c], o[c]] * home_bonus[o[c]])
                cat[c] = CAT["comp_in"]
                fum = c[rng.random(c.size) < M["fum_comp"]]
                turnover[fum], new_yl_to[fum] = True, 100 - (y[fum] - gain[fum])
            cat[ii[r == INC]] = CAT["inc"]
            s_ = ii[r == SACK]
            if s_.size:
                gain[s_] = _pick(rng, {0: pools[("sack", 0)]}, np.zeros(s_.size, int), pools[("sack", 0)])
                cat[s_] = CAT["sack"]
            t_ = ii[r == INT]
            if t_.size:
                air = _pick(rng, {0: pools[("int_air", 0)]}, np.zeros(t_.size, int), pools[("int_air", 0)])
                ret = _pick(rng, {0: pools[("int_ret", 0)]}, np.zeros(t_.size, int), pools[("int_ret", 0)])
                spot = y[t_] - air                                       # offense's distance to goal at the pick
                nyl = np.where(spot <= 0, 80.0, 100 - spot - ret)       # in the end zone: touchback
                turnover[t_], new_yl_to[t_] = True, nyl
                cat[t_] = CAT["inc"]
        # out of bounds on gains (sideline): share of completions/runs that stop the clock
        oob = ((cat == CAT["run_in"]) | (cat == CAT["comp_in"])) & (act <= PASS) & ~penal & (rng.random(a.size) < np.where(cat == CAT["comp_in"], 0.22, 0.12))
        cat = np.where(oob, CAT["oob"], cat)
        # penalties
        if penal.any():
            ii = np.flatnonzero(penal)
            offp = rng.random(ii.size) < pen["p_off"]
            yd_o = _pick(rng, {0: pen["off_yds"]}, np.zeros(ii.size, int), pen["off_yds"])
            yd_d = _pick(rng, {0: pen["def_yds"]}, np.zeros(ii.size, int), pen["def_yds"])
            gain[ii] = np.where(offp, -yd_o, np.minimum(yd_d, np.maximum(y[ii] - 1, 1)))
            cat[ii] = CAT["pen"]
        # ---- apply scrimmage results
        scrim = (act <= PASS) | (act == KNEEL)
        newy = y - np.where(act == KNEEL, -1.0, gain)          # kneel loses a yard
        td = scrim & ~turnover & (newy <= 0) & ~penal
        safety = scrim & ~turnover & (newy >= 100)
        pick6 = turnover & (new_yl_to <= 0)
        # downs and distance
        first = scrim & ~turnover & ~td & ~safety & ((gain >= tg) | (penal & ~(rng.random(a.size) < pen["p_off"]) & (rng.random(a.size) < pen["def_first"])))
        first &= ~(act == KNEEL)
        nd = np.where(first, 1, np.where(penal, dn, dn + 1))
        ntg = np.where(first, np.minimum(10.0, newy), tg - gain)
        downs_lost = scrim & ~turnover & ~td & ~safety & ~first & (nd > 4) & (act != KNEEL)
        # punts and field goals
        is_p = act == PUNT
        if is_p.any():
            ii = np.flatnonzero(is_p)
            nyl = _pick(rng, M["punt"], np.minimum(9, (y[ii] // 10)).astype(int), np.array([70.0]))
            punt_rec[ii], new_yl_to[ii] = True, nyl
        is_f = act == FGA
        made = np.zeros(a.size, dtype=bool)
        if is_f.any():
            dist = y[is_f] + 17
            pm = 1 / (1 + np.exp(-(fgb[0] + fgb[1] * (dist - 40) / 10 + fg_wind_logit)))
            mk = rng.random(is_f.sum()) < pm
            ii = np.flatnonzero(is_f)
            made[ii[mk]] = True
            miss = ii[~mk]
            new_yl_to[miss] = np.minimum(100 - (y[miss] + 7), 80.0)
        # points
        late = qtr >= 4
        m6 = diff + 6
        go2 = td & late & np.isin(m6, list(TWO_POINT_CHART))
        conv = np.where(go2, 2 * (rng.random(a.size) < M["two"]), 1 * (rng.random(a.size) < M["xp"]))
        pts_o += np.where(td, 6 + conv, 0) + np.where(made, 3, 0)
        pts_d += np.where(pick6, 6 + (rng.random(a.size) < M["xp"]), 0) + np.where(safety, 2, 0)
        score[a, o] += pts_o
        score[a, d] += pts_d
        # ---- clock
        rk = cat * 3 + tp
        secs = _pick(rng, M["run_off"], rk, np.array([30.0]))
        secs = np.where((act == PUNT) | (act == FGA) | td | turnover | safety, 8.0, secs)
        stop_cat = (cat == CAT["inc"]) | (cat == CAT["oob"]) | (cat == CAT["pen"])
        # timeouts: trailing defense late, or offense in a two-minute drill, after a play that keeps the clock running
        need = ~stop_cat & scrim & ~td & ~turnover & ~safety & (act != KNEEL)
        def_to = need & (qtr >= 4) & (hs < 180) & (diff > 0) & (tos[a, d] > 0)
        off_to = need & ~def_to & (((qtr == 2) & (hs < 120)) | ((qtr >= 4) & (hs < 120) & (diff <= 0))) & (tos[a, o] > 0)
        use = def_to | off_to
        secs = np.where(use, np.minimum(secs, 7.0), secs)
        tos[a[def_to], d[def_to]] -= 1
        tos[a[off_to], o[off_to]] -= 1
        newclock = hs - secs
        warn = (half[a] <= 2) & (hs > 120) & (newclock < 120)            # two-minute warning stops the clock
        newclock = np.where(warn, 120.0, newclock)
        newclock = np.where(act == KNEEL, hs - 40.0, newclock)
        clock[a] = newclock
        # ---- possession updates
        keep = scrim & ~turnover & ~td & ~safety & ~downs_lost & (act != KNEEL)
        yl[a[keep]] = np.clip(newy[keep], 1, 99)
        down[a[keep]], togo[a[keep]] = nd[keep], np.maximum(ntg[keep], 1)
        flip = turnover & ~pick6 | downs_lost | punt_rec | (is_f & ~made)
        tgt = np.where(downs_lost, 100 - newy, new_yl_to)
        fi = np.flatnonzero(flip)
        poss[a[fi]] = d[fi]
        yl[a[fi]] = np.clip(tgt[fi], 1, 99)
        down[a[fi]], togo[a[fi]] = 1, np.minimum(10.0, yl[a[fi]])
        # scores: the scoring team kicks off (after a safety, the team that gave it up free-kicks)
        sc_o = td | made
        if sc_o.any():
            ii = np.flatnonzero(sc_o)
            trail = (score[a[ii], o[ii]] < score[a[ii], d[ii]]) & (qtr[ii] >= 4) & (clock[a[ii]] < 150)
            kickoff_to(a[ii], d[ii], trail)
        sc_d = pick6 | safety
        if pick6.any():                                   # return TD: the team that threw it receives the kickoff
            ii = np.flatnonzero(pick6)
            kickoff_to(a[ii], o[ii])
        if safety.any():                                  # safety: the team that conceded free-kicks to the scorers
            ii = np.flatnonzero(safety)
            kickoff_to(a[ii], d[ii])
        if trace:
            for j in np.flatnonzero(a < trace):
                gidx = int(a[j])
                log[gidx].append({"half": int(half[gidx]), "clock": float(hs[j]), "off": int(o[j]), "down": int(dn[j]), "togo": float(tg[j]),
                                  "yl": float(y[j]), "act": ["run", "pass", "punt", "FG", "kneel"][int(act[j])], "pen": bool(penal[j]),
                                  "cat": [k for k, v in CAT.items() if v == int(cat[j])][0], "gain": float(gain[j]), "td": bool(td[j]),
                                  "turnover": bool(turnover[j]), "made": bool(made[j]), "secs": float(secs[j]), "to_used": bool(use[j]),
                                  "score": (int(score[gidx, 0]), int(score[gidx, 1]))})
        # ---- overtime and halves
        ot = half[a] == 3
        if ot.any():
            ch = ot & (flip | sc_o | sc_d)
            ot_poss[a[ch], o[ch]] += 1
            both = (ot_poss[a, 0] >= 1) & (ot_poss[a, 1] >= 1)
            done[a[ot & both & (score[a, 0] != score[a, 1])]] = True
        k4 = a[(act == KNEEL) & (qtr >= 4)]
        done[k4] = True
        over = (clock[a] <= 0) & ~done[a]
        h_now = half[a].copy()
        h1, h2, h3 = a[over & (h_now == 1)], a[over & (h_now == 2)], a[over & (h_now == 3)]
        half[h1], clock[h1] = 2, 1800.0
        tos[h1] = 3
        kickoff_to(h1, 1 - recv1[h1])
        tied = score[h2, 0] == score[h2, 1]
        done[h2[~tied]] = True
        t = h2[tied]
        half[t], clock[t], went_ot[t] = 3, 600.0, True
        tos[t] = 2
        kickoff_to(t, (rng.random(t.size) < 0.5).astype(np.int64))
        done[h3] = True
    return {"home": score[:, 0], "away": score[:, 1], "ot": went_ot, "plays": nplays, "trace": log, "stats": stats}


def calibrate_hfa(M: dict, target_margin: float, n: int = 20000, seed: int = 5) -> float:
    """Home yards bonus that reproduces the observed average home margin (two average teams)."""
    neutral = {"comp": 0.0, "sack": 0.0, "int": 0.0, "ypc_mult": 1.0, "ypr_mult": 1.0, "pass_offset": 0.0}
    lo, hi = 0.0, 0.15
    for _ in range(8):
        mid = (lo + hi) / 2
        s = simulate({"home": dict(neutral), "away": dict(neutral)}, M, n=n, seed=seed, hfa=mid)
        if float((s["home"] - s["away"]).mean()) < target_margin:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def build(plays_now: list[dict], plays_prior: list[dict], sched: list[dict], before: str, wind: dict | None = None) -> dict:
    """Everything the play engine needs for games on `before`: league play model (fit on all earlier plays), the
    calibrated home edge, and play ratings from this season's earlier plays (QBs borrow last season at half weight)."""
    from . import drives as dm
    allp = [p for p in plays_prior + plays_now if p["game_date"] < before]
    DM = dm.fit(allp, dm.build_drives(allp), before=before, wind=wind)
    M = fit(allp, before, fg_beta=DM["fg_beta"], fg_wind=DM["fg_wind"])
    past = [g for g in sched if g["result"] and g["game_type"] == "REG" and g["gameday"] < before and
            g["season"] in {p["season"] for p in allp} and g["location"] != "Neutral"]
    M["home_margin_target"] = float(np.mean([f(g["result"], 0) for g in past])) if past else 1.6
    M["hfa"] = calibrate_hfa(M, M["home_margin_target"])
    pr = play_ratings([p for p in plays_now if p["game_date"] < before], plays_prior)
    return {"M": M, "ratings": pr, "drive_model": DM}
