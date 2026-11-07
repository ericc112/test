"""How each tennis player plays: a scouting profile from what was actually recorded, not from memory.

Two sources, both real match records:
  charted   the Match Charting Project (Tennis Abstract; volunteers chart every shot of a match from video): rally
            length won and lost, net approaches, forehand vs backhand winners and errors, slice and drop shots, serve
            direction, return depth, points won in three shots or fewer, break points. Deep for top players, thin below.
            Licence CC BY-NC-SA 4.0 (non-commercial, with attribution).
  matches   every match in the TennisMyLife database (tennis_hist.load), WTA 125s from the WTA's feed where added:
            aces, double faults, first serves in, points won behind the first and second serve, return points won,
            break points saved and converted, tiebreaks, level played, results.

Every line on a card is a number with the percentile it sits at among the tour's current top 150 (with enough data); the
"read" sentences are generated from those numbers only (75th percentile and up, or 25th and down). Matchup notes put
one player's strength next to the other's matching number. None of this enters the probability unless a walk-forward
test shows it helps (tennis_style_test); until then it is context, labelled as such."""
from __future__ import annotations

import csv
import datetime as dt
import os
import re
from collections import defaultdict

import numpy as np

from .blend import HERE

MCP_DIR = os.path.join(HERE, ".cache", "mcp")
MCP_URL = "https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master"
MCP_FILES = ("matches", "stats-Overview", "stats-ServeBasics", "stats-ServeDirection", "stats-ReturnOutcomes", "stats-ReturnDepth",
             "stats-Rally", "stats-NetPoints", "stats-ShotTypes", "stats-KeyPointsServe", "stats-KeyPointsReturn")
CHART_MONTHS = 24            # charted matches from the last two years
MATCH_DAYS = 365             # database matches from the last 52 weeks
MIN_CHARTED = 5              # charted matches for a charted profile (and for the percentile pool)
MIN_MATCHES = 10             # database matches for the percentile pool
LOW_LEVELS = ("125", "C", "I", "15", "25", "ITF")
POOL_RANK = 150              # percentiles compare a player with the current top 150 of the tour
MIN_SVPT = 400               # serve points (about six matches) before a serve or return line gets a percentile


def _norm(s: str) -> str:
    from .nba_pp import _norm as n
    return n(s)


def download(max_age: float = 7 * 86400) -> None:
    """Refresh the charting files (weekly is plenty: the project adds matches in batches)."""
    import time
    import urllib.request
    os.makedirs(MCP_DIR, exist_ok=True)
    for tour in ("m", "w"):
        for f in MCP_FILES:
            p = os.path.join(MCP_DIR, f"charting-{tour}-{f}.csv")
            if os.path.exists(p) and time.time() - os.path.getmtime(p) < max_age:
                continue
            req = urllib.request.Request(f"{MCP_URL}/charting-{tour}-{f}.csv", headers={"User-Agent": "Mozilla/5.0 (edge tennis research)"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if data[:1] == b"<":
                raise RuntimeError(f"charting file {f} came back as HTML")
            with open(p + ".part", "wb") as fh:
                fh.write(data)
            os.replace(p + ".part", p)


def _rows(tour: str, f: str):
    p = os.path.join(MCP_DIR, f"charting-{tour}-{f}.csv")
    if not os.path.exists(p):
        return
    with open(p, newline="", encoding="utf-8", errors="replace") as fh:
        yield from csv.DictReader(fh)


def _i(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------------ charted profiles
def charted(tour: str, since: str) -> dict:
    """{normalized name: totals over charted matches since `since` (YYYYMMDD)}; tour 'ATP' or 'WTA'."""
    t = "m" if tour == "ATP" else "w"
    keep, info = set(), {}
    for r in _rows(t, "matches"):
        d = r["match_id"][:8]
        if d.isdigit() and d >= since:
            keep.add(r["match_id"]); info[r["match_id"]] = r
    P = defaultdict(lambda: defaultdict(float))
    names = {}
    def acc(name, **kv):
        k = _norm(name); names[k] = name
        for a, v in kv.items():
            P[k][a] += v
    seen = defaultdict(set)
    for r in _rows(t, "stats-Overview"):
        if r["match_id"] in keep and r["set"] == "Total":
            seen[_norm(r["player"])].add(r["match_id"])
            acc(r["player"], serve_pts=_i(r["serve_pts"]), aces=_i(r["aces"]), dfs=_i(r["dfs"]), first_in=_i(r["first_in"]), first_won=_i(r["first_won"]),
                second_in=_i(r["second_in"]), second_won=_i(r["second_won"]), bp_faced=_i(r["bk_pts"]), bp_saved=_i(r["bp_saved"]),
                ret_pts=_i(r["return_pts"]), ret_won=_i(r["return_pts_won"]), winners=_i(r["winners"]), w_fh=_i(r["winners_fh"]), w_bh=_i(r["winners_bh"]),
                ue=_i(r["unforced"]), ue_fh=_i(r["unforced_fh"]), ue_bh=_i(r["unforced_bh"]))
    for r in _rows(t, "stats-ServeBasics"):
        if r["match_id"] in keep and r["row"] == "Total":
            acc(r["player"], sb_pts=_i(r["pts"]), aces_sb=_i(r["aces"]), unret=_i(r["unret"]), sv_forced=_i(r["forced_err"]), won_le3=_i(r["pts_won_lte_3_shots"]),
                wide=_i(r["wide"]), body=_i(r["body"]), tee=_i(r["t"]))
    for r in _rows(t, "stats-ReturnOutcomes"):
        if r["match_id"] in keep and r["row"] in ("v1st", "v2nd"):
            s = r["row"]
            acc(r["player"], **{f"r{s}_pts": _i(r["pts"]), f"r{s}_won": _i(r["pts_won"]), f"r{s}_able": _i(r["returnable"]), f"r{s}_inplay": _i(r["in_play"])})
    for r in _rows(t, "stats-ReturnDepth"):
        if r["match_id"] in keep and r["row"] == "Total":
            acc(r["player"], rd_inplay=_i(r["shallow"]) + _i(r["deep"]), rd_deep=_i(r["deep"]), rd_shallow=_i(r["shallow"]))   # very_deep is part of deep
    for r in _rows(t, "stats-Rally"):                      # 'server' / 'returner' columns name players 1 and 2
        if r["match_id"] in keep and r["row"] in ("1-3", "4-6", "7-9", "10"):
            b = {"1-3": "short", "4-6": "mid", "7-9": "long", "10": "long"}[r["row"]]
            n = _i(r["pts"])
            acc(r["server"], **{f"ra_{b}_pts": n, f"ra_{b}_won": _i(r["pl1_won"])})
            acc(r["returner"], **{f"ra_{b}_pts": n, f"ra_{b}_won": _i(r["pl2_won"])})
    for r in _rows(t, "stats-NetPoints"):
        if r["match_id"] in keep and r["row"] == "NetPoints":
            acc(r["player"], net_pts=_i(r["net_pts"]), net_won=_i(r["pts_won"]))
    for r in _rows(t, "stats-ShotTypes"):
        if r["match_id"] in keep and r["row"] in ("Total", "F", "B", "Sl", "Dr", "Fgs", "Bgs"):
            k = {"Total": "sh", "F": "fh", "B": "bh", "Sl": "sl", "Dr": "dr", "Fgs": "fgs", "Bgs": "bgs"}[r["row"]]
            acc(r["player"], **{f"{k}_shots": _i(r["shots"]), f"{k}_win": _i(r["winners"]), f"{k}_ue": _i(r["unforced"])})
    for r in _rows(t, "stats-KeyPointsReturn"):
        if r["match_id"] in keep and r["row"] == "BPO":
            acc(r["player"], bpo=_i(r["pts"]), bpo_won=_i(r["pts_won"]))
    out = {}
    for k, v in P.items():
        v = dict(v); v["n"] = len(seen.get(k, ())); v["name"] = names.get(k, k)
        out[k] = v
    return out


# ------------------------------------------------------------------ database profiles (everyone)
def from_matches(M: list[dict], tour: str, asof: dt.date, days: int = MATCH_DAYS) -> dict:
    """{player id: totals over database matches in the last `days`}: serve and return counts, break points,
    tiebreaks, levels, results."""
    lo = int((asof - dt.timedelta(days=days)).strftime("%Y%m%d")); hi = int(asof.strftime("%Y%m%d"))
    P = defaultdict(lambda: defaultdict(float))
    meta = {}
    for m in M:
        if m["tour"] != tour or not (lo <= m["date"] < hi):
            continue
        sc = m.get("sc") or {}
        for me, op, won in (("w", "l", 1), ("l", "w", 0)):
            pid = m[me]; p = P[pid]
            p["matches"] += 1; p["wins"] += won
            p["lvl_" + str(m.get("level") or "?")] += 1
            meta[pid] = {"name": m[f"{me}_name"], "hand": m.get(f"{me}_hand") or "", "ht": m.get(f"{me}_ht"), "rank": m.get(f"{me}_rank")}
            if m.get(f"{me}_n") and m.get(f"{op}_n"):     # serve and return points: every match that has them (WTA 125s too)
                p["nk_sv"] += m[f"{me}_n"]; p["nk_svw"] += m[f"{me}_k"]; p["nk_rt"] += m[f"{op}_n"]; p["nk_rtw"] += m[f"{op}_n"] - m[f"{op}_k"]
                p["nk_matches"] += 1
            raw = m.get("raw") or {}
            g = lambda k: _i(raw.get(k)) if raw else 0.0
            if raw and g(f"{me}_svpt") > 0 and g(f"{op}_svpt") > 0:
                p["svpt"] += g(f"{me}_svpt"); p["ace"] += g(f"{me}_ace"); p["df"] += g(f"{me}_df"); p["in1"] += g(f"{me}_1stIn")
                p["won1"] += g(f"{me}_1stWon"); p["won2"] += g(f"{me}_2ndWon"); p["bpf"] += g(f"{me}_bpFaced"); p["bps"] += g(f"{me}_bpSaved")
                p["rpt"] += g(f"{op}_svpt"); p["rwon"] += g(f"{op}_svpt") - g(f"{op}_1stWon") - g(f"{op}_2ndWon")
                p["r1pt"] += g(f"{op}_1stIn"); p["r1won"] += g(f"{op}_1stIn") - g(f"{op}_1stWon")
                p["r2pt"] += g(f"{op}_svpt") - g(f"{op}_1stIn"); p["r2won"] += (g(f"{op}_svpt") - g(f"{op}_1stIn")) - g(f"{op}_2ndWon")
                p["bpo"] += g(f"{op}_bpFaced"); p["bpc"] += g(f"{op}_bpFaced") - g(f"{op}_bpSaved")
                p["stat_matches"] += 1
            sets = [(int(a), int(b)) for a, b, _ in re.findall(r"(\d+)-(\d+)(?:\((\d+)\))?", m.get("score") or "")] if sc else []
            for a_, b_ in sets:
                a, b = (a_, b_) if me == "w" else (b_, a_)
                if {a, b} == {7, 6}:
                    p["tb"] += 1; p["tb_won"] += a > b
            if m.get("minutes") and sc:
                p["mins"] += m["minutes"]; p["mins_games"] += sc.get("games", 0)
            if sc and sc.get("sets") == 3 and m.get("bo", 3) == 3:
                p["deciders"] += 1; p["deciders_won"] += won
    return {pid: {**dict(v), **meta.get(pid, {})} for pid, v in P.items()}


# ------------------------------------------------------------------ features, percentiles, the read
def _r(a, b):
    return a / b if b else None


def features(db: dict | None, ch: dict | None) -> dict:
    f = {}
    if db:
        full = db.get("svpt", 0) >= MIN_SVPT                              # full serve lines (aces, first serve, break points)
        f.update({"spw": _r(db.get("nk_svw", 0), db.get("nk_sv", 0)) if db.get("nk_sv", 0) >= MIN_SVPT else None,
                  "rpw": _r(db.get("nk_rtw", 0), db.get("nk_rt", 0)) if db.get("nk_rt", 0) >= MIN_SVPT else None,
                  "win_pct": _r(db.get("wins", 0), db.get("matches", 0)) if db.get("matches", 0) >= 8 else None})
    if db and full:
        f.update({"ace_pct": _r(db.get("ace", 0), db.get("svpt", 0)), "df_pct": _r(db.get("df", 0), db.get("svpt", 0)),
                  "first_in": _r(db.get("in1", 0), db.get("svpt", 0)), "first_won": _r(db.get("won1", 0), db.get("in1", 0)),
                  "second_won": _r(db.get("won2", 0), db.get("svpt", 0) - db.get("in1", 0)),
                  "r1_won": _r(db.get("r1won", 0), db.get("r1pt", 0)), "r2_won": _r(db.get("r2won", 0), db.get("r2pt", 0)),
                  "bp_saved": _r(db.get("bps", 0), db.get("bpf", 0)) if db.get("bpf", 0) >= 40 else None,
                  "bp_conv": _r(db.get("bpc", 0), db.get("bpo", 0)) if db.get("bpo", 0) >= 40 else None,
                  "tb_won": _r(db.get("tb_won", 0), db.get("tb", 0)) if db.get("tb", 0) >= 4 else None,
                  "decider_won": _r(db.get("deciders_won", 0), db.get("deciders", 0)) if db.get("deciders", 0) >= 4 else None})
    if ch and ch.get("n", 0) >= MIN_CHARTED:
        sh = ch.get("sh_shots", 0)
        pts = sum(ch.get(f"ra_{b}_pts", 0) for b in ("short", "mid", "long"))
        f.update({"unret": _r(ch.get("aces_sb", 0) + ch.get("unret", 0) + ch.get("sv_forced", 0), ch.get("sb_pts", 0)), "won_le3": _r(ch.get("won_le3", 0), ch.get("sb_pts", 0)),
                  "ret_inplay": _r(ch.get("rv1st_inplay", 0) + ch.get("rv2nd_inplay", 0), ch.get("rv1st_pts", 0) + ch.get("rv2nd_pts", 0)),
                  "ret_deep": _r(ch.get("rd_deep", 0), ch.get("rd_inplay", 0)),
                  "short_won": _r(ch.get("ra_short_won", 0), ch.get("ra_short_pts", 0)), "long_won": _r(ch.get("ra_long_won", 0), ch.get("ra_long_pts", 0)),
                  "long_share": _r(ch.get("ra_long_pts", 0), pts),
                  "net_freq": _r(ch.get("net_pts", 0), pts), "net_won": _r(ch.get("net_won", 0), ch.get("net_pts", 0)),
                  "aggression": _r(ch.get("winners", 0) + ch.get("ue", 0), sh), "winners_per100": _r(100 * ch.get("winners", 0), sh),
                  "ue_per100": _r(100 * ch.get("ue", 0), sh),
                  "fh_win_share": _r(ch.get("w_fh", 0), ch.get("w_fh", 0) + ch.get("w_bh", 0)),
                  "bh_ue_share": _r(ch.get("ue_bh", 0), ch.get("ue_fh", 0) + ch.get("ue_bh", 0)),
                  "fh_share": _r(ch.get("fgs_shots", 0), ch.get("fgs_shots", 0) + ch.get("bgs_shots", 0)),
                  "slice_per100": _r(100 * ch.get("sl_shots", 0), sh), "drop_per100": _r(100 * ch.get("dr_shots", 0), sh),
                  "serve_t": _r(ch.get("tee", 0), ch.get("wide", 0) + ch.get("body", 0) + ch.get("tee", 0)),
                  "charted": ch.get("n", 0)})
    return f


# sentences: (feature, high text, low text, format)
READ = [
    ("ace_pct", "Big server: aces on {v} of service points", "Few free points: aces on only {v} of service points", "pct1"),
    ("unret", "Serve does damage: {v} of serves don't come back in play", "Serve gets returned: only {v} of serves not returned in play", "pct0"),
    ("won_le3", "First-strike tennis: wins {v} of service points in three shots or fewer", "Has to work on serve: only {v} of service points won in three shots or fewer", "pct0"),
    ("second_won", "Solid second serve: wins {v} behind it", "Second serve is attackable: wins only {v} behind it", "pct0"),
    ("df_pct", "Double-fault prone: {v} of service points", None, "pct1"),
    ("r2_won", "Punishes second serves: wins {v} of points against them", "Doesn't punish second serves: wins {v} against them", "pct0"),
    ("ret_inplay", "Makes opponents play: puts {v} of returns in play", "Misses returns: puts only {v} of returns in play", "pct0"),
    ("ret_deep", "Returns deep: {v} of returns in play land deep", "Returns land short: only {v} of returns in play land deep", "pct0"),
    ("long_won", "Grinder: wins {v} of rallies of 7+ shots", "Fades in long rallies: wins {v} of rallies of 7+ shots", "pct0"),
    ("short_won", "Wins the short points: {v} of rallies of 1-3 shots", "Loses the short exchanges: {v} of 1-3 shot rallies won", "pct0"),
    ("net_freq", "Comes forward: at the net on {v} of points", "Stays back: at the net on only {v} of points", "pct1"),
    ("net_won", "Effective at the net: wins {v} there", None, "pct0"),
    ("aggression", "High-risk, high-reward: {v} winners or unforced errors per shot", "Steady, low-risk: {v} winners or unforced errors per shot", "pct1"),
    ("fh_win_share", "Forehand-led: {v} of winners off the forehand", "Backhand is the weapon: only {v} of winners off the forehand", "pct0"),
    ("bh_ue_share", "Backhand breaks down: {v} of unforced errors off the backhand", "Forehand misses more: only {v} of unforced errors off the backhand", "pct0"),
    ("slice_per100", "Uses slice a lot: {v} slices per 100 shots", None, "num1"),
    ("drop_per100", "Drop-shot user: {v} per 100 shots", None, "num1"),
    ("bp_saved", "Clutch on serve: saves {v} of break points", "Leaks break points: saves only {v}", "pct0"),
    ("bp_conv", "Converts chances: {v} of break points won", "Wastes chances: converts only {v} of break points", "pct0"),
    ("tb_won", "Tiebreak record {v}", "Tiebreak record {v}", "pct0"),
]


def _fmt(v, kind):
    return f"{100 * v:.1f}%" if kind == "pct1" else f"{100 * v:.0f}%" if kind == "pct0" else f"{v:.1f}"


class Scout:
    """Profiles and percentiles for one tour, as of a date."""

    def __init__(self, st: dict, tour: str, asof: dt.date | None = None):
        self.tour, self.asof = tour, asof or dt.date.today()
        T_ = st[tour]; self.R, self.oi = T_["R"], T_["obs"]["idx"]
        since = (self.asof - dt.timedelta(days=30 * CHART_MONTHS)).strftime("%Y%m%d")
        self.ch = charted(tour, since)
        self.db = from_matches(st["matches"], tour, self.asof)
        # percentiles against the field: players currently ranked in the top POOL_RANK (latest ranking in the database)
        field = {pid for pid, d in self.db.items() if d.get("rank") and d["rank"] <= POOL_RANK}
        feats = []
        for pid in field:
            d = self.db[pid]
            if d.get("stat_matches", 0) >= MIN_MATCHES or d.get("nk_matches", 0) >= MIN_MATCHES:
                feats.append(features(d, self.ch.get(_norm(d.get("name") or ""))))
        ok = [self.oi[p] for p in field if p in self.oi and self.oi[p] < self.R.P and self.R.pts_s[self.oi[p]] >= 300 and self.R.pts_r[self.oi[p]] >= 300]
        self.rating_pool = {"serve": np.sort(self.R.a[ok]), "return": np.sort(self.R.b[ok])}
        self.pool = {k: np.array(sorted(x[k] for x in feats if x.get(k) is not None)) for k in {k for x in feats for k in x}}

    def pct(self, k, v):
        a = self.pool.get(k)
        if v is None or a is None or len(a) < 20:
            return None
        return float(np.searchsorted(a, v, side="right") / len(a))

    def card(self, pid: str, name: str) -> dict:
        d = self.db.get(pid) or {}
        ch = self.ch.get(_norm(name))
        f = features(d, ch)
        stats = {k: {"v": v, "pct": self.pct(k, v)} for k, v in f.items() if isinstance(v, float)}
        read = []
        for k, hi, lo, kind in READ:
            s = stats.get(k)
            if not s or s["pct"] is None:
                continue
            if k == "tb_won":
                if d.get("tb", 0) >= 6 and (s["pct"] >= 0.8 or s["pct"] <= 0.2):
                    read.append({"k": k, "text": f"Tiebreaks: won {int(d.get('tb_won', 0))} of {int(d.get('tb', 0))} in 52 weeks", "pct": s["pct"]})
                continue
            if s["pct"] >= 0.75 and hi:
                read.append({"k": k, "text": hi.format(v=_fmt(s["v"], kind)), "pct": s["pct"]})
            elif s["pct"] <= 0.25 and lo:
                read.append({"k": k, "text": lo.format(v=_fmt(s["v"], kind)), "pct": s["pct"]})
        lv = {k[4:]: int(v) for k, v in d.items() if k.startswith("lvl_")}
        # opponent-adjusted serve and return (the ratings the simulation uses), in points per 100 vs the tour average
        i = self.oi.get(pid)
        if i is not None and i < self.R.P and self.R.pts_s[i] >= 150:
            for k, v in (("serve", float(self.R.a[i])), ("return", float(self.R.b[i]))):
                pool = self.rating_pool[k]
                stats[f"{k}_rating"] = {"v": v, "pct": float(np.searchsorted(pool, v, side="right") / len(pool)) if len(pool) >= 20 else None}
            for k, hi, lo in (("serve_rating", "Serve, adjusted for opponents: among the best in the top 150 ({v:+.1f} points per 100 vs an average tour player)",
                               "Serve, adjusted for opponents: a weakness by top-150 standards ({v:+.1f} points per 100 vs an average tour player)"),
                              ("return_rating", "Return, adjusted for opponents: among the best in the top 150 ({v:+.1f} points per 100 vs an average tour player)",
                               "Return, adjusted for opponents: a weakness by top-150 standards ({v:+.1f} points per 100 vs an average tour player)")):
                sr = stats[k]
                if sr["pct"] is not None and (sr["pct"] >= 0.75 or sr["pct"] <= 0.25):
                    read.insert(0, {"k": k, "text": (hi if sr["pct"] >= 0.75 else lo).format(v=100 * sr["v"]), "pct": sr["pct"]})
        tot = sum(lv.values()); low = sum(v for k, v in lv.items() if k in LOW_LEVELS)
        below = bool(tot) and low / tot >= 0.5
        return {"name": name, "hand": d.get("hand"), "ht": d.get("ht"), "rank": d.get("rank"), "matches": int(d.get("matches", 0)),
                "wins": int(d.get("wins", 0)), "stat_matches": int(d.get("stat_matches", 0)), "levels": lv,
                "charted": int(ch["n"]) if ch else 0, "stats": stats, "read": read, "below_tour": below,
                "style": style_label(stats)}


def style_label(stats: dict) -> str | None:
    """A short label from the numbers (only when they're clear), e.g. 'first-strike server', 'counter-puncher'."""
    p = lambda k: (stats.get(k) or {}).get("pct")
    serve = max([x for x in (p("won_le3") and p("won_le3") + 0.05, p("ace_pct") and p("ace_pct") - 0.05, p("serve_rating")) if x is not None], default=None)
    ret = p("return_rating"); agg = p("aggression"); net = p("net_freq"); longw = p("long_won")
    tags = []
    if serve is not None and ret is not None and serve >= 0.9 and ret >= 0.9:
        tags.append("elite on serve and return")
    elif serve is not None and serve >= 0.85:
        tags.append("serve-first")
    if agg is not None and agg >= 0.75:
        tags.append("aggressive baseliner" if (net or 0) < 0.75 else "attacking all-courter")
    elif agg is not None and agg <= 0.25 and (longw or 0) >= 0.6:
        tags.append("counter-puncher")
    if net is not None and net >= 0.85 and "attacking all-courter" not in tags:
        tags.append("net-rusher")
    if ret is not None and ret >= 0.8 and "elite on serve and return" not in tags:
        tags.append("elite returner")
    return ", ".join(tags) or None


def surname(n: str) -> str:
    w = (n or "").split(" ", 1)
    return w[1] if len(w) > 1 else n


def ordinal(k: int) -> str:
    return f"{k}{'th' if 10 <= k % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(k % 10, 'th')}"


def matchup(a: dict, b: dict) -> list[str]:
    """Factual pairings: one player's strength next to the other's matching number (context, not a tested factor)."""
    out = []
    S = lambda c, k: (c["stats"].get(k) or {})
    def pc(x):
        return f"{ordinal(round(100 * x))} percentile" if x is not None else "no percentile"
    na, nb = surname(a["name"]), surname(b["name"])
    for (x, y, nx, ny) in ((a, b, na, nb), (b, a, nb, na)):
        s2, r2 = S(x, "second_won"), S(y, "r2_won")
        if s2.get("pct") is not None and r2.get("pct") is not None and s2["pct"] <= 0.3 and r2["pct"] >= 0.65:
            out.append(f"{nx}'s second serve ({100 * s2['v']:.0f}% won, {pc(s2['pct'])}) against {ny}'s second-serve return ({100 * r2['v']:.0f}%, {pc(r2['pct'])}).")
        ac, ri = S(x, "ace_pct"), S(y, "ret_inplay")
        if ac.get("pct") is not None and ac["pct"] >= 0.75 and ri.get("pct") is not None:
            out.append(f"{nx}'s serve ({100 * ac['v']:.1f}% aces, {pc(ac['pct'])}) against {ny}'s return ({100 * ri['v']:.0f}% of returns in play, {pc(ri['pct'])}).")
    la, lb = S(a, "long_won"), S(b, "long_won")
    if la.get("v") is not None and lb.get("v") is not None and abs(la["v"] - lb["v"]) >= 0.04:
        g, o = (a, b) if la["v"] > lb["v"] else (b, a)
        gv, ov = max(la["v"], lb["v"]), min(la["v"], lb["v"])
        out.append(f"Long rallies (7+ shots) favour {surname(g['name'])}: {100 * gv:.0f}% won vs {100 * ov:.0f}% for {surname(o['name'])}.")
    if (a.get("hand") == "L") != (b.get("hand") == "L") and (a.get("hand") in ("L", "R") and b.get("hand") in ("L", "R")):
        lefty = a if a.get("hand") == "L" else b
        out.append(f"{surname(lefty['name'])} is left-handed (handedness didn't improve the ratings in the walk-forward test; shown as context).")
    for x in (a, b):
        lv = x.get("levels") or {}
        tot = sum(lv.values())
        low = sum(v for k, v in lv.items() if k in LOW_LEVELS)
        if tot and low / tot >= 0.5:
            out.append(f"{surname(x['name'])} has played mostly below tour level in the last 52 weeks ({low} of {tot} recorded matches: Challengers, WTA 125s or ITF).")
    return out


def compact(card: dict) -> dict:
    """The card for the page: rounded numbers, percentiles in whole points."""
    return {**{k: card[k] for k in ("name", "hand", "ht", "rank", "matches", "wins", "stat_matches", "levels", "charted", "below_tour", "style")},
            "read": [{"text": r["text"], "pct": round(100 * r["pct"])} for r in card["read"]],
            "stats": {k: [round(v["v"], 4), None if v["pct"] is None else round(100 * v["pct"])] for k, v in card["stats"].items()}}
