"""Walk-forward NBA prop backtest corpus: every finished game of the season re-simulated with only what was known
before it (ratings and player profiles to the day before, the players who sat as the injury report, the same
engine and player layer the pricer uses), joined to DraftKings' pre-tip lines (data/nba_dk_hist) and the box score.

  python -m edge.nba_backtest --tag base [--n 5000] [--set minutes_alpha=1.0 ...]

Writes data/nba_bt/corpus_TAG.json.gz with three tables:
  legs     one row per DraftKings player line: simulation P(over/under/push), mean, median, minutes; DraftKings
           prices (sides matched to the N+ milestone, L2) and its milestone ladder; this-season history at the line
           (raw and minutes-aware); the actual value and minutes; projected and actual starter.
  players  one row per player who played: simulated vs actual minutes, points, rebounds, assists, FGA, FTA, 3PM.
  teams    one row per team-game: simulated vs actual possessions, points, FGA, FTA, offensive rebounds.
Availability uses the backtest convention (who sat = known before tip, as gamesim.nba.backtest does).
Config knobs (one experiment = one change): minutes_alpha, prior_min, injury_beta, player_w, comeback_sd, shock,
garbage_g, h2h (0/1)."""
from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import time

import numpy as np

from .blend import HERE

sys.path.insert(0, HERE)
from gamesim import data as gs_data, nba as gnba, nba_research as gres  # noqa: E402

OUT = os.path.join(HERE, "data", "nba_bt")
CACHE = os.path.join(HERE, ".cache", "nba_bt")
NODE = os.path.join(HERE, "simlab", "props_sim.js")
STATS = ("pts", "reb", "ast", "tpm", "pra", "pr", "pa", "ra")
PARTS = {"pts": ("pts",), "reb": ("reb",), "ast": ("ast",), "tpm": ("tpm",), "pra": ("pts", "reb", "ast"),
         "pr": ("pts", "reb"), "pa": ("pts", "ast"), "ra": ("reb", "ast")}
KNOBS = {"minutes_alpha": "MINUTES_ALPHA", "prior_min": "PLAYER_PRIOR_MIN", "injury_beta": "INJURY_BETA", "player_w": "PLAYER_RATING_W",
         "comeback_sd": "COMEBACK_SD", "shock": "PLAYER_SHOCK", "min_sd_scale": "MIN_SD_SCALE", "swing_rho": "SWING_RHO",
         "minutes_share": "MINUTES_SHARE", "minutes_pad": "MINUTES_PAD", "ast_fix": "AST_FIX",
         "team_market_w": "TEAM_MARKET_W"}


def imp(a) -> float | None:
    try:
        v = float(str(a).replace("+", ""))
    except (TypeError, ValueError):
        return None
    return 100 / (v + 100) if v > 0 else -v / (-v + 100)


def apply_cfg(cfg: dict) -> dict:
    for k, attr in KNOBS.items():
        if k in cfg:
            v = cfg[k]
            setattr(gnba, attr, None if k in ("comeback_sd", "player_w") and not v else v)
    if "garbage_g" in cfg:
        gnba.PLAYER_GARBAGE = {**gnba.PLAYER_GARBAGE, "g": float(cfg["garbage_g"])}
    if "h2h" in cfg and not int(cfg["h2h"]):
        gres.H2H_COEF = {}
    if "avail" in cfg:
        global AVAIL
        AVAIL = cfg["avail"]
    return cfg


# ------------------------------------------------------------------ DraftKings history -> lines with sides
def dk_lines(game: dict) -> dict:
    """{pid: {stat: {line, over, under, q, ms, match}}} from one game's raw propBets items. Items updated after tip
    use their opening target and price (the pre-tip line), as gamesim.nba.dk_player_lines does. Sides come from the
    milestone at the same threshold (L2); `match` records how clear that match was, for the audit."""
    tip = game["date"][:16]
    tot, ms = {}, {}
    for it in game["items"]:
        late = (it.get("updated") or "") >= tip
        tgt = (it["open"] if late else it["cur"]) if (it["open"] if late else it["cur"]) is not None else it["cur"]
        pr = it["price_open"] if late else it["price"]
        if tgt is None or pr in (None, ""):
            continue
        if it["kind"] == "total":
            tot.setdefault((it["pid"], it["stat"], float(tgt)), []).append(pr)
        else:
            ms.setdefault((it["pid"], it["stat"]), {})[int(tgt)] = pr
    out = {}
    for (pid, st, ln), prices in tot.items():
        if len(prices) != 2:
            continue
        lad = ms.get((pid, st), {})
        m = lad.get(int(ln + 0.5))
        rec = {"line": ln, "ms": lad, "over": None, "under": None, "q": None, "match": None}
        if m is not None:
            ia, ib, im = imp(prices[0]), imp(prices[1]), imp(m)
            o = 0 if abs(ia - im) <= abs(ib - im) else 1
            rec["over"], rec["under"] = prices[o], prices[1 - o]
            qo, qu = imp(rec["over"]), imp(rec["under"])
            rec["q"] = qo / (qo + qu)
            rec["match"] = {"gap_over": abs(imp(rec["over"]) - im), "gap_other": abs(imp(rec["under"]) - im), "sym": abs(ia - ib)}
        prev = out.setdefault(pid, {}).get(st)
        if prev is None or (rec["q"] is not None and (prev["q"] is None or abs(rec["q"] - 0.5) < abs(prev["q"] - 0.5))):
            out[pid][st] = rec           # several targets: keep the one closest to even (the main line)
    return out


# ------------------------------------------------------------------ one day's engine inputs (as simlab.nba_engine, backtest availability)
def _R_export(R, G, cut):
    return {"pace": R["league"]["pace"], "sd_pace": R["sd_pace"], "sd_p2": R["sd_p2"], "sd_p3": R["sd_p3"], "dur_scale": R["dur_scale"],
            "and1": R["and1"], "home_scale": R["home_scale"], "comeback": R.get("comeback", 0.0), "reb_credit": round(gnba.reb_credit(G, cut), 4),
            "ppg": R["ppg_target"], "home_margin": R["home_margin"], "n_games": R["n_games"],
            "avg": gnba.side(R, "_", "_", False), "avg_home": gnba.side(R, "_", "_", True)}


AVAIL = "perfect"     # "perfect": who sat is known (gamesim backtest convention); "live": only players who also
                      # missed the team's previous game count as known out (late scratches stay in the rotation, as live)


def _prev_absent(G: list, g: dict, team: str, cut: str) -> set:
    prev = sorted((h for h in G if h["final"] and h["date"] < cut and team in (h["home"], h["away"])), key=lambda h: h["date"])
    if not prev:
        return set()
    rows = gnba._box_cached("nba", prev[-1]["id"]).get(team, [])
    return {r["name"] for r in rows if r["dnp"] or r["min"] <= 0}


def day_inputs(day: str, G: list, PT: dict, PRt, RS, games: list) -> dict:
    cut = gs_data.cutoff(day)
    key = os.path.join(CACHE, f"R_{day}_{gnba.COMEBACK_SD}.json")
    if os.path.exists(key):
        R = json.load(open(key))
    else:
        R0 = gnba.ratings(G, cut, 48)
        if R0["n_games"] < 20:
            return {}
        R = gnba.calibrate(R0, G, cut, 48, 24)
        os.makedirs(CACHE, exist_ok=True)
        json.dump(R, open(key, "w"), default=float)
    if R["n_games"] < 20:
        return {}
    prf = PRt.fit(cut) if PRt else None
    out = {}
    for g in games:
        box = gnba._box_cached("nba", g["id"])
        absent = gnba.absent_from_box("nba", G, g, cut)
        if AVAIL == "live":
            names = {r["id"]: r["name"] for t in box.values() for r in t}
            for s_ in ("home", "away"):
                known = _prev_absent(G, g, g[s_], cut)
                vals = gnba.player_values("nba", G, g[s_], cut)["players"]
                absent[s_] = {pid for pid in absent[s_] if (names.get(pid) or vals.get(pid, {}).get("name")) in known
                              or pid not in names}      # not on tonight's box at all (gone from the roster): known
        H, A, det = gnba.sides_with_availability(R, G, g, cut, absent)
        opp_of = {"home": g["away"], "away": g["home"]}
        prof = {}
        for s_ in ("home", "away"):
            rows = box.get(g[s_], [])
            played = {r["name"] for r in rows if not r["dnp"] and r["min"] > 0}
            seen = {r["name"] for h in G if h["final"] and h["date"] < cut and g[s_] in (h["home"], h["away"]) for r in gnba._box_cached("nba", h["id"]).get(g[s_], [])}
            out_names = (seen | {r["name"] for r in rows}) - played
            if AVAIL == "live":       # keep tonight's late scratches in the rotation; only last game's absentees are known
                on_box = {r["name"] for r in rows}
                out_names = {n for n in out_names if n in _prev_absent(G, g, g[s_], cut) or n not in on_box}
            h2h = {pid: RS.rate_factors(pid, opp_of[s_], cut, gres.H2H_COEF) for pid, L in RS.logs.items() if L and L[-1]["date"] < cut
                   and any(e["team"] == g[s_] for e in L[-5:])} if gres.H2H_COEF else None
            prof[s_] = gnba.player_profiles("nba", G, g[s_], cut, out_names, prior_tot=PT, rate_mult=h2h)
        if PRt and prf["n_games"] >= 100:
            pm = PRt.margin(prf, PRt.lineup_played(g["id"], g["home"], cut), PRt.lineup_played(g["id"], g["away"], cut), g["neutral"])
            H, A, _ = gnba.with_player_ratings(H, A, R, pm["margin"])
        ln = g.get("line") or {}
        H, A, _ = gnba.anchor_to_market(H, A, R, ln.get("spread_home"), ln.get("total"))
        out[g["id"]] = {"R": _R_export(R, G, cut), "sides": {"home": H, "away": A}, "pl": [prof["home"], prof["away"]]}
    return out


def run_node(inputs: dict, n: int, workers: int = 4, tag: str = "x") -> dict:
    gids = sorted(inputs)
    chunks = [gids[i::workers] for i in range(workers) if gids[i::workers]]
    procs = []
    os.makedirs(CACHE, exist_ok=True)
    for k, ch in enumerate(chunks):
        ip, op = os.path.join(CACHE, f"in_{tag}_{k}.json"), os.path.join(CACHE, f"out_{tag}_{k}.json")
        json.dump({"n": n, "games": [{"id": gid, "seed": 7000 + int(gid) % 100000, **inputs[gid]} for gid in ch]}, open(ip, "w"), default=float)
        procs.append((subprocess.Popen(["node", NODE, ip, op]), op))
    out = {}
    for p, op in procs:
        if p.wait() != 0:
            raise RuntimeError("props_sim.js failed")
        out.update(json.load(open(op))["games"])
    return out


# ------------------------------------------------------------------ distributions
def sides_at(h, line):
    a = np.asarray(h, float); n = a.sum(); x = np.arange(len(a))
    return float(a[x > line].sum() / n), float(a[x < line].sum() / n), float(a[x == line].sum() / n)


def quant(h, q):
    c = np.cumsum(np.asarray(h, float)); return int(np.searchsorted(c, q * c[-1]))


def hmean(h):
    a = np.asarray(h, float); return float((a * np.arange(len(a))).sum() / a.sum())


def hsd(h):
    a = np.asarray(h, float); x = np.arange(len(a)); m = (a * x).sum() / a.sum()
    return float(np.sqrt((a * (x - m) ** 2).sum() / a.sum()))


def build(cfg: dict, n: int = 5000, tag: str = "base", season=("20261018", "20261103"), year: int = 2026) -> dict:
    t0 = time.time()
    apply_cfg(cfg)
    G = gnba.season_games("nba", *season)
    PT = gnba.season_player_totals("nba", gnba.season_games("nba", *gnba.LAST_SEASON[year]))
    PRt = gnba.PlayerRatings("nba", G, year) if gnba.PLAYER_RATING_W else None
    RS = gres.Research("nba", G, year)
    hist = json.load(gzip.open(os.path.join(HERE, "data", "nba_dk_hist", f"{year}.json.gz"), "rt"))
    days = sorted({gs_data.us_day(g["date"]) for g in G if g["final"]})
    inputs = {}
    for day in days:
        games = [g for g in G if g["final"] and gs_data.us_day(g["date"]) == day and g["id"] in hist]
        inputs.update(day_inputs(day, G, PT, PRt, RS, games))
    print(f"[{tag}] inputs for {len(inputs)} games in {time.time() - t0:.0f}s", flush=True)
    sims = run_node(inputs, n, tag=tag)
    print(f"[{tag}] simulated in {time.time() - t0:.0f}s", flush=True)
    Gi = {g["id"]: g for g in G}
    legs, players, teams = [], [], []
    for gid, sim in sims.items():
        g = Gi[gid]; day = gs_data.us_day(g["date"]); cut = gs_data.cutoff(day)
        box = gnba._box_cached("nba", gid)
        act = {r["id"]: r for t in box.values() for r in t}
        team_of = {r["id"]: t for t, rs in box.items() for r in rs}
        lines = dk_lines(hist[gid])
        prof = {p["id"]: p for side in inputs[gid]["pl"] for p in side["players"]}
        top5 = {p["id"] for side in inputs[gid]["pl"] for p in sorted(side["players"], key=lambda p: -p["min"])[:5]}
        # team level
        for s_, mk in (("home", "mean_home"), ("away", "mean_away")):
            b, ob = g["box"][s_], g["box"]["away" if s_ == "home" else "home"]
            ps = [p for p in sim["players"].values() if p["side"] == s_]
            teams.append({"gid": gid, "day": day, "team": g[s_], "sim_pts": sim[mk], "act_pts": g["score"][s_], "sim_poss": sim["poss"] / 2,
                          "act_poss": gnba.poss(b, ob), "sim_fga": sum(p["mean"]["f2a"] + p["mean"]["f3a"] for p in ps), "act_fga": b["fga"],
                          "sim_fta": sum(p["mean"]["fta"] for p in ps), "act_fta": b["fta"], "sim_orb": sum(p["mean"]["orb"] for p in ps), "act_orb": b["orb"],
                          "sim_3pa": sum(p["mean"]["f3a"] for p in ps), "act_3pa": b["tpa"], "sim_ast": sum(p["mean"]["ast"] for p in ps), "act_ast": b.get("ast")})
        # player level
        for pid, sp in sim["players"].items():
            a = act.get(pid)
            if not a or a["dnp"] or a["min"] <= 0:
                continue
            players.append({"gid": gid, "day": day, "pid": pid, "name": sp["name"], "proj_min": prof.get(pid, {}).get("min"), "sim_min": sp["min"],
                            "act_min": a["min"], "top5": pid in top5, "starter": a["starter"], "corr_pa": sp["corr_pa"], "corr_pr": sp["corr_pr"],
                            **{f"sim_{k}": sp["mean"].get(k) for k in ("pts", "reb", "ast", "f3m", "f2a", "f3a", "fta", "tov")},
                            "act_pts": a["pts"], "act_reb": a["oreb"] + a["dreb"], "act_ast": a["ast"], "act_f3m": a["tpm"],
                            "act_f2a": a["fga"] - a["tpa"], "act_f3a": a["tpa"], "act_fta": a["fta"], "act_tov": a["tov"]})
        # legs
        for pid, L in lines.items():
            sp, a = sim["players"].get(pid), act.get(pid)
            if not sp or not a or a["dnp"] or a["min"] <= 0:
                continue
            val = {"pts": a["pts"], "reb": a["oreb"] + a["dreb"], "ast": a["ast"], "tpm": a["tpm"]}
            past = [e for e in RS.before(pid, g["date"]) if e["season"] == year]
            pmin = prof.get(pid, {}).get("min") or sp["min"]
            for st, rec in L.items():
                h = sp["hist"][st]
                po, pu, pp = sides_at(h, rec["line"])
                y = sum(val[k] for k in PARTS[st])
                vals = [(sum(e[k] for k in PARTS[st]), e["min"]) for e in past]
                ho, hu = sum(v > rec["line"] for v, _ in vals), sum(v < rec["line"] for v, _ in vals)
                keep = [(v, m) for v, m in vals if m >= 0.5 * pmin]                  # minutes-aware: no early exits
                wts = [min(m / max(pmin, 1.0), 1.5) for _, m in keep]
                hwo = sum(w for (v, _), w in zip(keep, wts) if v > rec["line"]); hwu = sum(w for (v, _), w in zip(keep, wts) if v < rec["line"])
                legs.append({"gid": gid, "day": day, "pid": pid, "name": sp["name"], "team": team_of.get(pid), "stat": st, "line": rec["line"],
                             "over": rec["over"], "under": rec["under"], "q": rec["q"], "ms": rec["ms"], "match": rec["match"],
                             "p_over": po, "p_under": pu, "p_push": pp, "sim_mean": hmean(h), "sim_med": quant(h, 0.5),
                             "sim_q25": quant(h, 0.25), "sim_q75": quant(h, 0.75), "sim_sd": hsd(h),
                             "proj_min": pmin, "sim_min": sp["min"], "act_min": a["min"], "y": y, "top5": pid in top5, "starter": a["starter"],
                             "hist_o": ho, "hist_u": hu, "hist_wo": hwo, "hist_wu": hwu, "hist_n": len(vals), "corr_pa": sp["corr_pa"],
                             "h": [int(c) for c in h][:max((i for i, c in enumerate(h) if c), default=0) + 1]})   # the simulated counts (shape tests)
    res = {"tag": tag, "cfg": cfg, "n": n, "legs": legs, "players": players, "teams": teams, "built": time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, gzip.open(os.path.join(OUT, f"corpus_{tag}.json.gz"), "wt"), default=float)
    print(f"[{tag}] {len(legs)} legs, {len(players)} player-games, {len(teams)} team-games in {time.time() - t0:.0f}s", flush=True)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="base")
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--set", nargs="*", default=[])
    ap.add_argument("--end", default="20261103", help="last game day (YYYYMMDD) in the corpus")
    a = ap.parse_args()
    cfg = {}
    for kv in a.set:
        k, v = kv.split("=")
        cfg[k] = float(v) if v.replace(".", "", 1).replace("-", "", 1).isdigit() else v
    build(cfg, n=a.n, tag=a.tag, season=("20261018", a.end))
