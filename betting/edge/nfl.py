"""NFL game simulator: python -m edge nfl --event ID [--n 50000] [--log]

One simulated game, in order (every step is vectorised over the n simulations):
  1. Drives. Each team gets ~11 possessions (pace of both teams); each drive ends in a TD, a FG or nothing.
     Per-drive TD/FG rates are solved so expected points equal the DraftKings implied team total, with
     the TD:FG mix from the team's own drives. Points, margin and the opening drive come out of this.
  2. Volume. Plays = team pace vs opponent + a margin term; dropback rate = the team's neutral rate +
     a margin term (leading teams run). Both margin slopes are fitted on this season's games.
  3. Efficiency. One pass shock and one rush shock per team, correlated with how its scoring went, so
     a QB's yards and his receivers' yards move together.
  4. Shares. Target and carry shares from this season's games he played for this team (recency-
     weighted), shrunk, with inactives removed and their volume redistributed; perturbed per game
     (Dirichlet) and split by multinomial draws.
  5. Per-play yards. Each catch ~ Gamma (his yards per catch), each carry ~ shifted Gamma (his yards
     per carry), both scaled by the opponent adjustment and the team shock.
  6. QB passing yards = the sum of his receivers' yards; completions = their catches; INTs ~ Binomial.
     Each TD goes to a rusher or receiver in proportion to his simulated work and his TD share.

`backtest()` replays finished weeks using only earlier games and the closing line, and scores the
model against DraftKings closing lines (same props, same games). That, not a few hand-picked
results, is what says whether the simulation is accurate.
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import json
import math
import os
import re
import time

import numpy as np

from .blend import HERE, final_probability
from .grade import _get

SITE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
CACHE = os.path.join(HERE, ".cache", "nfl")

# DraftKings prop names -> (market key used by grade.py, simulated stat)
DK_MARKETS = {
    "Total Passing Yards (incl. overtime)": "pass_yds",
    "Total Pass Completions (incl. overtime)": "completions",
    "Total Passing Attempts (incl. overtime)": "pass_att",
    "Total Passing Touchdowns (incl. overtime)": "pass_td",
    "Total Passing Interceptions (incl. overtime)": "pass_int",
    "Total Rushing Yards (incl. overtime)": "rush_yds",
    "Total Carries (incl. overtime)": "rush_att",
    "Total Receiving Yards (incl. overtime)": "rec_yds",
    "Total Receptions (incl. overtime)": "receptions",
    "Total Rushing Plus Receiving Yards (incl. overtime)": "rush_rec_yds",
}

# League priors (2026 weeks 1-8; league_params re-measures them from the games it is given, these are fallbacks)
PRIOR = {"catch": 0.67, "ypr": 11.0, "ypc": 4.2, "int": 0.021, "sack": 0.065, "drives": 10.2, "ypt_att": 7.06,
         "untargeted": 0.06, "rush_td_share": 0.39, "plays": 62.3, "db_rate": 0.57, "p_td_drive": 0.25, "p_fg_drive": 0.17}

# Tuning constants (checked by the backtest: PIT spread and calibration at the DK lines)
SHARE_ALPHA = 40.0        # Dirichlet concentration for per-game share wobble
CATCH_SHAPE = 1.15        # Gamma shape of yards on one catch (CV ~0.93)
CARRY_SD = 6.0            # sd of yards on one carry
CARRY_SHIFT = 3.0         # carries start at -3 yards (shifted Gamma)
RECENCY = 0.85            # weight per game back when estimating shares
PASS_SHOCK_SD = 0.16      # team pass efficiency, log sd per game
RUSH_SHOCK_SD = 0.18      # team rush efficiency, log sd per game
SHOCK_RHO = 0.55          # correlation between efficiency shock and points residual
PLAYS_SD = 6.0
PLAYS_SD_MULT = 1.25      # within-team play-count residual understates game-to-game spread (pass-attempt alt lines)
FRINGE_T = 0.03           # share of attempts to receivers outside the active list
FRINGE_C = 0.02           # share of carries to rushers outside the active list
DB_SD = 0.055


# Weight on logit(simulated P(over)) before it goes into the blend, by market. Fitted by fit_shrink() on
# the 2026 weeks 3-8 backtest against DraftKings closing lines (5,300 props); re-fit with
# `python -m edge nfl --backtest`. 0 would mean "the line is all there is"; 1 "trust the simulation".
# Out of sample (fit weeks 3-5, scored 6-8) this took Brier from 0.2500 (line as a coin flip) to 0.2488:
# the simulation adds little to the DraftKings line by itself. Its shape is the useful part (anchored_over).
MODEL_SHRINK = {"_pooled": 0.25, "pass_yds": 0.174, "completions": 0.155, "pass_td": 0.506, "rush_att": 0.25,
                "rush_yds": 0.218, "rec_yds": 0.152, "receptions": 0.309, "pass_int": 0.335, "pass_att": 0.155,
                "rush_rec_yds": 0.321, "anytime_td": 1.0}


def calibrated(p_over: float, market: str) -> float:
    """Simulated P(over) shrunk toward 50% at the DraftKings line by the backtest weight for this market."""
    w = MODEL_SHRINK.get(market, MODEL_SHRINK["_pooled"])
    p = min(max(p_over, 0.005), 0.995)
    return 1 / (1 + math.exp(-w * math.log(p / (1 - p))))


# ------------------------------------------------------------------ data
def _cached(name: str, url: str, max_age: float | None):
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9_.-]+", "_", name) + ".json")
    if os.path.exists(path) and (max_age is None or time.time() - os.path.getmtime(path) < max_age):
        with open(path) as f:
            return json.load(f)
    out = _get(url)
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f)
    return out


def week_events(season: int, week: int) -> list[dict]:
    d = _get(f"{SITE}/scoreboard?seasontype=2&week={week}&dates={season}")
    out = []
    for e in d.get("events", []):
        c = e["competitions"][0]
        teams = {t["homeAway"]: t for t in c["competitors"]}
        out.append({"id": e["id"], "date": e["date"], "week": week, "status": c["status"]["type"]["name"],
                    "home": teams["home"]["team"]["id"], "away": teams["away"]["team"]["id"],
                    "home_abbr": teams["home"]["team"]["abbreviation"], "away_abbr": teams["away"]["team"]["abbreviation"]})
    return out


def season_events(season: int, through_week: int) -> list[dict]:
    with cf.ThreadPoolExecutor(6) as ex:
        weeks = list(ex.map(lambda w: week_events(season, w), range(1, through_week + 1)))
    return [e for w in weeks for e in w]


def _num(v) -> float:
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return 0.0


def parse_summary(s: dict) -> dict:
    """Compact game record: closing line, team volume, every player's line, first drives, injuries."""
    comp = s["header"]["competitions"][0]
    teams = {t["homeAway"]: t for t in comp["competitors"]}
    home, away = teams["home"]["team"]["id"], teams["away"]["team"]["id"]
    g = {"event_id": s["header"]["id"], "date": comp["date"], "week": (s["header"].get("week")),
         "final": comp["status"]["type"]["name"] == "STATUS_FINAL", "home": home, "away": away,
         "abbr": {home: teams["home"]["team"]["abbreviation"], away: teams["away"]["team"]["abbreviation"]},
         "score": {home: _num(teams["home"].get("score", 0)), away: _num(teams["away"].get("score", 0))},
         "spread_home": None, "total": None, "teams": {}, "players": {}, "first_drive": {}, "drives": {}, "out": {}}
    pc = (s.get("pickcenter") or [])
    if pc and pc[0].get("overUnder") is not None and pc[0].get("spread") is not None:
        sp = float(pc[0]["spread"])
        fav_home = (pc[0].get("homeTeamOdds") or {}).get("favorite")
        if fav_home is True and sp > 0 or fav_home is False and sp < 0:
            sp = -sp
        g["spread_home"], g["total"] = sp, float(pc[0]["overUnder"])
    for team in s.get("boxscore", {}).get("players", []):
        tid = team["team"]["id"]
        P = collections.defaultdict(lambda: collections.defaultdict(float))
        for cat in team["statistics"]:
            lab = cat.get("labels", [])
            for a in cat.get("athletes", []):
                pid, st = str(a["athlete"]["id"]), dict(zip(lab, a.get("stats", [])))
                p = P[pid]
                p["name"] = a["athlete"]["displayName"]
                if cat["name"] == "passing" and "C/ATT" in st:
                    c, att = (st["C/ATT"].split("/") + ["0"])[:2]
                    p["comp"], p["pass_att"] = _num(c), _num(att)
                    p["pass_yds"], p["pass_td"], p["pass_int"] = _num(st.get("YDS")), _num(st.get("TD")), _num(st.get("INT"))
                    p["sacks"] = _num(str(st.get("SACKS", "0-0")).split("-")[0])
                elif cat["name"] == "rushing":
                    p["car"], p["rush_yds"], p["rush_td"] = _num(st.get("CAR")), _num(st.get("YDS")), _num(st.get("TD"))
                elif cat["name"] == "receiving":
                    p["rec"], p["rec_yds"], p["rec_td"] = _num(st.get("REC")), _num(st.get("YDS")), _num(st.get("TD"))
                    p["tgt"] = _num(st.get("TGTS"))
        g["players"][tid] = {k: dict(v) for k, v in P.items()}
        tot = lambda f: sum(v.get(f, 0.0) for v in P.values())
        g["teams"][tid] = {"pass_att": tot("pass_att"), "sacks": tot("sacks"), "car": tot("car"), "tgt": tot("tgt"),
                           "rec": tot("rec"), "rec_yds": tot("rec_yds"), "rush_yds": tot("rush_yds"),
                           "pass_td": tot("pass_td"), "rush_td": tot("rush_td"), "pass_int": tot("pass_int")}
        t = g["teams"][tid]
        t["plays"] = t["pass_att"] + t["sacks"] + t["car"]
    for d in (s.get("drives") or {}).get("previous", []):
        tid = (d.get("team") or {}).get("id")
        if not tid:
            continue
        res = (d.get("result") or d.get("displayResult") or "").upper()
        kind = "td" if "TD" in res or "TOUCHDOWN" in res else "fg" if res in ("FG", "FIELD GOAL") or "FG" == res[:2] else "none"
        if res in ("END OF HALF", "END OF GAME", "END OF 4TH QUARTER") or "END OF" in res:
            kind = "end"
        g["drives"].setdefault(tid, []).append(kind)
        g["first_drive"].setdefault(tid, kind)
    for t in s.get("injuries", []) or []:
        tid = t["team"]["id"]
        g["out"][tid] = [{"id": str(i["athlete"]["id"]), "name": i["athlete"]["displayName"], "status": i.get("status")}
                         for i in t.get("injuries", [])]
    return g


def game(event_id: str) -> dict:
    """Parsed game, cached for good once final (pre-game: refreshed every 10 minutes)."""
    path = os.path.join(CACHE, f"game_{event_id}.json")
    if os.path.exists(path):
        with open(path) as f:
            g = json.load(f)
        if g["final"] or time.time() - os.path.getmtime(path) < 600:
            return g
    g = parse_summary(_get(f"{SITE}/summary?event={event_id}"))
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w") as f:
        json.dump(g, f)
    return g


def dk_props(event_id: str) -> list[dict]:
    """DraftKings player props (line, and prices when the feed carries them). Two identical rows per prop
    are the over and the under; the feed doesn't label which is which (L2), so only matched pairs with a
    milestone check would give a side. Here only the line is used unless both prices are present."""
    path = os.path.join(CACHE, f"props_{event_id}.json")
    items, page = [], 1
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 600:
        with open(path) as f:
            return json.load(f)
    while True:
        d = _get(f"{CORE}/events/{event_id}/competitions/{event_id}/odds/100/propBets?lang=en&region=us&limit=1000&page={page}")
        items += d.get("items", [])
        if page >= d.get("pageCount", 1):
            break
        page += 1
    out, seen = [], set()
    for x in items:
        m = re.search(r"/athletes/(\d+)", (x.get("athlete") or {}).get("$ref", ""))
        name = x["type"]["name"]
        if not m:
            continue
        cur, op = x.get("current") or {}, x.get("open") or {}
        line = (cur.get("target") or {}).get("value")
        if name == "Anytime Touchdown Scorer":
            key = ("anytime_td", m.group(1))
            if key not in seen:
                seen.add(key)
                out.append({"player_id": m.group(1), "market": "anytime_td", "line": 0.5,
                            "american": (cur.get("over") or {}).get("american") or (cur.get("american"))})
            continue
        if name not in DK_MARKETS or line is None:
            continue
        key = (DK_MARKETS[name], m.group(1))
        if key in seen:
            continue
        seen.add(key)
        out.append({"player_id": m.group(1), "market": DK_MARKETS[name], "line": float(line),
                    "open": (op.get("target") or {}).get("value"), "updated": x.get("lastUpdated")})
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f)
    return out


def load_games(event_ids: list[str], workers: int = 8) -> list[dict]:
    with cf.ThreadPoolExecutor(workers) as ex:
        return list(ex.map(game, event_ids))


# ------------------------------------------------------------------ league + team + player profiles
def league_params(games: list[dict]) -> dict:
    """League rates and the two script slopes (plays and dropback rate on final margin), fitted within team."""
    rows = []
    for g in games:
        for tid in (g["home"], g["away"]):
            t = g["teams"].get(tid)
            if not t or t["plays"] < 30:
                continue
            opp = g["away"] if tid == g["home"] else g["home"]
            margin = g["score"][tid] - g["score"][opp]
            rows.append((tid, margin, t["plays"], (t["pass_att"] + t["sacks"]) / t["plays"]))
    out = dict(PRIOR)
    if len(rows) < 40:
        out.update(beta_db=-0.006, beta_plays=-0.15)
        return out
    by = collections.defaultdict(list)
    for r in rows:
        by[r[0]].append(r)
    xm, yp, yd = [], [], []
    for rs in by.values():
        a = np.array([[r[1], r[2], r[3]] for r in rs])
        a -= a.mean(axis=0)
        xm += list(a[:, 0]); yp += list(a[:, 1]); yd += list(a[:, 2])
    xm, yp, yd = map(np.array, (xm, yp, yd))
    out["beta_plays"] = float((xm @ yp) / (xm @ xm))
    out["beta_db"] = float((xm @ yd) / (xm @ xm))
    out["plays_resid_sd"] = float(np.std(yp - out["beta_plays"] * xm))
    out["db_resid_sd"] = float(np.std(yd - out["beta_db"] * xm))
    T = [t for g in games for t in g["teams"].values() if t["plays"] >= 30]
    s = lambda f: sum(t[f] for t in T)
    out["plays"] = s("plays") / len(T)
    out["db_rate"] = (s("pass_att") + s("sacks")) / s("plays")
    out["catch"] = s("rec") / max(s("tgt"), 1)
    out["ypr"] = s("rec_yds") / max(s("rec"), 1)
    out["ypt_att"] = s("rec_yds") / max(s("pass_att"), 1)
    out["untargeted"] = max(0.0, 1 - s("tgt") / max(s("pass_att"), 1))   # throwaways, spikes, batted balls
    out["ypc"] = s("rush_yds") / max(s("car"), 1)
    out["int"] = s("pass_int") / max(s("pass_att"), 1)
    out["sack"] = s("sacks") / max(s("pass_att") + s("sacks"), 1)
    out["rush_td_share"] = s("rush_td") / max(s("rush_td") + s("pass_td"), 1)
    drives = [d for g in games for d in g["drives"].values()]
    nd = [len([k for k in d if k != "end"]) for d in drives if d]
    if nd:
        out["drives"] = float(np.mean(nd))
        allk = [k for d in drives for k in d if k != "end"]
        out["p_td_drive"] = allk.count("td") / len(allk)
        out["p_fg_drive"] = allk.count("fg") / len(allk)
        firsts = [k for g in games for k in g["first_drive"].values() if k != "end"]
        out["first_drive_score"] = sum(k in ("td", "fg") for k in firsts) / max(len(firsts), 1)
        out["any_drive_score"] = (allk.count("td") + allk.count("fg")) / len(allk)
    return out


def _shrink(x_sum: float, n: float, prior: float, k: float) -> float:
    return (x_sum + k * prior) / (n + k)


def team_profile(tid: str, games: list[dict], L: dict) -> dict:
    """Offense and defense rates for one team over its earlier games, shrunk toward the league."""
    off = collections.defaultdict(float)
    dfn = collections.defaultdict(float)
    n = 0
    db_neutral, drives_n, fd, kinds = [], [], [], []
    for g in games:
        if tid not in (g["home"], g["away"]) or tid not in g["teams"]:
            continue
        opp = g["away"] if tid == g["home"] else g["home"]
        t, o = g["teams"][tid], g["teams"].get(opp)
        if not o or t["plays"] < 30:
            continue
        n += 1
        for k, v in t.items():
            off[k] += v
        for k, v in o.items():
            dfn[k] += v
        margin = g["score"][tid] - g["score"][opp]
        db_neutral.append((t["pass_att"] + t["sacks"]) / t["plays"] - L["beta_db"] * margin)
        ds = [k for k in g["drives"].get(tid, []) if k != "end"]
        if ds:
            drives_n.append(len(ds))
            kinds += ds
    p = {"n": n}
    k_eff = 4.0  # games of league average mixed into every team rate
    p["plays"] = _shrink(off["plays"], n, L["plays"], k_eff)
    p["plays_allowed"] = _shrink(dfn["plays"], n, L["plays"], k_eff)
    p["db_rate"] = _shrink(sum(db_neutral), n, L["db_rate"], k_eff)
    att_k = k_eff * 33
    p["ypa"] = _shrink(off["rec_yds"], off["pass_att"], L["ypt_att"], att_k)
    p["ypa_allowed"] = _shrink(dfn["rec_yds"], dfn["pass_att"], L["ypt_att"], att_k)
    p["ypc"] = _shrink(off["rush_yds"], off["car"], L["ypc"], k_eff * 26)
    p["ypc_allowed"] = _shrink(dfn["rush_yds"], dfn["car"], L["ypc"], k_eff * 26)
    p["int"] = _shrink(off["pass_int"], off["pass_att"], L["int"], 200)
    p["int_forced"] = _shrink(dfn["pass_int"], dfn["pass_att"], L["int"], 300)
    db_off, db_def = off["pass_att"] + off["sacks"], dfn["pass_att"] + dfn["sacks"]
    p["sack"] = _shrink(off["sacks"], db_off, L["sack"], 150)
    p["sack_forced"] = _shrink(dfn["sacks"], db_def, L["sack"], 150)
    p["rush_td_share"] = _shrink(off["rush_td"], off["rush_td"] + off["pass_td"], L["rush_td_share"], 8)
    p["drives"] = _shrink(sum(drives_n), len(drives_n), L["drives"], 3)
    ntd, nfg = kinds.count("td"), kinds.count("fg")
    p["fg_per_td"] = _shrink(nfg, ntd, L.get("p_fg_drive", 0.16) / L.get("p_td_drive", 0.22), 8)
    return p


def player_profiles(tid: str, games: list[dict], L: dict, keep: set | None = None, as_of_last: int = 3) -> dict:
    """Recency-weighted shares and rates from this team's games each player appeared in (L1/L3).
    A player counts as active if he appeared in the team's last few games or is in `keep` (DraftKings
    posted a prop for him, which is how a player back from injury shows up before the box score does)."""
    keep = keep or set()
    tg = sorted([g for g in games if tid in g["players"] and tid in g["teams"] and g["teams"][tid]["plays"] >= 30],
                key=lambda g: g["date"])
    recent_ids = set()
    for g in tg[-as_of_last:]:
        recent_ids |= set(g["players"][tid])
    acc = {}
    n_team = len(tg)
    for i, g in enumerate(tg):
        w = RECENCY ** (n_team - 1 - i)
        t = g["teams"][tid]
        for pid, p in g["players"][tid].items():
            a = acc.setdefault(pid, collections.defaultdict(float))
            a["name"] = p.get("name")
            a["games"] += 1
            a["last_game"] = i
            a["w"] += w
            if t["pass_att"]:
                a["tgt_share_w"] += w * p.get("tgt", 0) / t["pass_att"]
                a["att_share_w"] += w * p.get("pass_att", 0) / t["pass_att"]
            if t["car"]:
                a["car_share_w"] += w * p.get("car", 0) / t["car"]
            for f in ("tgt", "rec", "rec_yds", "rec_td", "car", "rush_yds", "rush_td", "pass_att", "pass_int", "comp", "pass_yds", "pass_td"):
                a[f] += p.get(f, 0.0)
            a["team_rec_td"] += t["pass_td"]
            a["team_rush_td"] += t["rush_td"]
    out = {}
    for pid, a in acc.items():
        if pid not in recent_ids and pid not in keep:
            continue  # not seen in the team's last few games and no prop posted: injured, cut or traded
        w = a["w"]
        g_ = a["games"]
        prof = {"name": a["name"], "games": int(g_), "team_games": n_team, "returning": pid not in recent_ids,
                "tgt_share": a["tgt_share_w"] / w, "car_share": a["car_share_w"] / w, "att_share": a["att_share_w"] / w,
                "catch": _shrink(a["rec"], a["tgt"], L["catch"], 15),
                "ypr": _shrink(a["rec_yds"], a["rec"], L["ypr"], 8),
                "ypc": _shrink(a["rush_yds"], a["car"], L["ypc"], 25 if a["att_share_w"] / w < 0.5 else 12),
                "int": _shrink(a["pass_int"], a["pass_att"], L["int"], 150)}
        if g_ < 3:  # one big game isn't a role
            prof["tgt_share"] *= g_ / (g_ + 0.5)
            prof["car_share"] *= g_ / (g_ + 0.5)
        # TD shares shrunk toward his volume share (4 team TDs of prior)
        prof["rec_td_share"] = (a["rec_td"] + 4 * prof["tgt_share"]) / (a["team_rec_td"] + 4)
        prof["rush_td_share"] = (a["rush_td"] + 4 * prof["car_share"]) / (a["team_rush_td"] + 4)
        prof["thin"] = g_ < 3
        out[pid] = prof
    return out


def athlete_info(pid: str, season: int) -> tuple[str | None, str | None]:
    """(team id, display name) from the ESPN athlete record, cached for a week."""
    try:
        a = _cached(f"ath_{season}_{pid}", f"{CORE}/seasons/{season}/athletes/{pid}?lang=en&region=us", 7 * 86400)
    except Exception:
        return None, None
    m = re.search(r"/teams/(\d+)", (a.get("team") or {}).get("$ref", ""))
    return (m.group(1) if m else None), a.get("displayName")


def implied_profile(lines: dict, att_mu: float, car_mu: float, L: dict) -> dict:
    """Role read off the DraftKings lines, for a listed player with no games this season. Used only so
    his teammates' shares are right; he is never priced off it."""
    tgt = car = 0.0
    if "receptions" in lines:
        tgt = (lines["receptions"] + 0.3) / L["catch"] / att_mu
    elif "rec_yds" in lines:
        tgt = lines["rec_yds"] * 1.1 / (L["ypr"] * L["catch"]) / att_mu
    if "rush_att" in lines:
        car = (lines["rush_att"] + 0.3) / car_mu
    elif "rush_yds" in lines:
        car = lines["rush_yds"] * 1.1 / L["ypc"] / car_mu
    return {"name": None, "games": 0, "team_games": 0, "returning": True, "implied": True, "thin": True,
            "tgt_share": min(tgt, 0.35), "car_share": min(car, 0.8), "att_share": 0.0, "catch": L["catch"],
            "ypr": L["ypr"], "ypc": L["ypc"], "int": L["int"], "rec_td_share": min(tgt, 0.35), "rush_td_share": min(car, 0.8)}


# ------------------------------------------------------------------ simulation helpers
def _multinomial(rng, n: np.ndarray, probs: np.ndarray) -> np.ndarray:
    """Row-wise multinomial: n (S,), probs (S, K) rows summing to 1 -> counts (S, K)."""
    S, K = probs.shape
    out = np.zeros((S, K), dtype=np.int64)
    rem = n.astype(np.int64).copy()
    left = np.ones(S)
    for j in range(K - 1):
        pj = np.clip(probs[:, j] / np.maximum(left, 1e-12), 0, 1)
        x = rng.binomial(rem, pj)
        out[:, j] = x
        rem -= x
        left -= probs[:, j]
    out[:, K - 1] = rem
    return out


def _dirichlet(rng, base: np.ndarray, S: int, alpha: float) -> np.ndarray:
    g = rng.gamma(np.maximum(base * alpha, 1e-3), 1.0, size=(S, len(base)))
    return g / g.sum(axis=1, keepdims=True)


def _gamma_sum(rng, count: np.ndarray, shape: float, scale: np.ndarray) -> np.ndarray:
    """Sum of `count` iid Gamma(shape, scale) draws = Gamma(count*shape, scale); zero when count is 0."""
    c = np.asarray(count, dtype=float)
    out = np.zeros_like(c)
    m = c > 0
    out[m] = rng.gamma(c[m] * shape, np.broadcast_to(scale, c.shape)[m])
    return out


def _fill(shares: np.ndarray, total: float, fringe: float, to_active: float = 0.75) -> np.ndarray:
    """Active shares scaled so active + fringe = total; vacated volume split to_active : rest."""
    s = float(shares.sum())
    room = total - fringe
    if s <= 0:
        return np.array([total])
    if s >= room:
        act = shares / s * room
        return np.append(act, fringe)
    act = shares * (1 + to_active * (room - s) / s)
    return np.append(act, total - act.sum())


def _roles(players: dict, out_ids: set) -> tuple[list, list, str | None]:
    """Active receivers/rushers (share above a floor) and the starting QB."""
    act = {pid: p for pid, p in players.items() if pid not in out_ids}
    qbs = sorted([(p["att_share"], pid) for pid, p in act.items() if p["att_share"] > 0.2], reverse=True)
    qb = qbs[0][1] if qbs else None
    rec = [pid for pid, p in act.items() if p["tgt_share"] >= 0.02]
    rush = [pid for pid, p in act.items() if p["car_share"] >= 0.02 or pid == qb and p["car_share"] > 0]
    return rec, rush, qb


# ------------------------------------------------------------------ the simulator
def simulate(target: dict, history: list[dict], n: int = 50000, seed: int = 7, out_ids: set | None = None,
             L: dict | None = None, listed: dict | None = None) -> dict:
    """Simulate one game. target: parsed game (needs home/away, spread_home, total). history: earlier games.
    listed: {player_id: {market: line}} from DraftKings (who the book expects to play).
    Returns {"teams": {tid: {...arrays}}, "players": {pid: {stat: array}}, "meta": {...}}."""
    rng = np.random.default_rng(seed)
    L = L or league_params(history)
    home, away = target["home"], target["away"]
    if target.get("spread_home") is None or target.get("total") is None:
        raise ValueError("no closing spread/total for this game: the script needs a market line")
    implied = {home: (target["total"] - target["spread_home"]) / 2, away: (target["total"] + target["spread_home"]) / 2}
    T = {tid: team_profile(tid, history, L) for tid in (home, away)}
    out_ids = set(out_ids or ())
    for tid, lst in (target.get("out") or {}).items():
        out_ids |= {i["id"] for i in lst if (i.get("status") or "").lower() in ("out", "doubtful", "injured reserve", "ir", "suspension")}
    opp = {home: away, away: home}

    # 1. drives -> points, margin, opening drive
    d_mu = (T[home]["drives"] + T[away]["drives"]) / 2
    D = np.clip(np.rint(rng.normal(d_mu, 1.0, n)), 7, 16).astype(int)
    extra = rng.integers(0, 2, n)                 # one team often gets one more possession
    home_first = rng.random(n) < 0.5
    nd = {home: D + np.where(home_first, extra, 0), away: D + np.where(home_first, 0, extra)}
    pts, tds, fgs, first = {}, {}, {}, {}
    for tid in (home, away):
        q = T[tid]["fg_per_td"]
        p_td = implied[tid] / ((d_mu + 0.25) * (7.0 + 3.0 * q))   # +0.25: the odd extra possession
        p_fg = q * p_td
        s = p_td + p_fg
        if s > 0.85:
            p_td, p_fg = p_td * 0.85 / s, p_fg * 0.85 / s
        maxd = nd[tid].max()
        u = rng.random((n, maxd))
        live = np.arange(maxd)[None, :] < nd[tid][:, None]
        td_m, fg_m = (u < p_td) & live, (u >= p_td) & (u < p_td + p_fg) & live
        tds[tid], fgs[tid] = td_m.sum(1), fg_m.sum(1)
        pts[tid] = 7 * tds[tid] + 3 * fgs[tid]
        first[tid] = td_m[:, 0] | fg_m[:, 0]
    margin = {home: pts[home] - pts[away], away: pts[away] - pts[home]}

    listed = listed or {}
    season = int(target["date"][:4]) if int(target["date"][5:7]) >= 3 else int(target["date"][:4]) - 1
    seen_any = {pid for g in history for ps in g["players"].values() for pid in ps}
    res = {"teams": {}, "players": {}, "meta": {"implied": implied, "league": L, "profiles": T, "out_ids": sorted(out_ids),
                                                "line_implied": []}}
    for tid in (home, away):
        o = opp[tid]
        tp, op = T[tid], T[o]
        P = player_profiles(tid, history, L, keep=set(listed))
        # 2. volume
        plays_mu = L["plays"] * (tp["plays"] / L["plays"]) * (op["plays_allowed"] / L["plays"])
        att_mu = plays_mu * tp["db_rate"] * (1 - tp["sack"])
        car_mu = plays_mu * (1 - tp["db_rate"])
        for pid, lines in listed.items():   # listed by the book, no 2026 game anywhere: role from the line
            if pid in seen_any or pid in out_ids:
                continue
            team, name = athlete_info(pid, season)
            if team == tid:
                P[pid] = {**implied_profile(lines, att_mu, car_mu, L), "name": name or pid}
                res["meta"]["line_implied"].append(pid)
        rec_ids, rush_ids, qb = _roles(P, out_ids)
        plays = np.maximum(35, rng.normal(plays_mu + L["beta_plays"] * margin[tid], L.get("plays_resid_sd", PLAYS_SD) * PLAYS_SD_MULT, n))
        db_rate = np.clip(rng.normal(tp["db_rate"] + L["beta_db"] * margin[tid], L.get("db_resid_sd", DB_SD), n), 0.3, 0.85)
        dropbacks = np.rint(plays * db_rate).astype(int)
        sack_rate = tp["sack"] * op["sack_forced"] / L["sack"]
        sacks = rng.binomial(dropbacks, min(max(sack_rate, 0.02), 0.15))
        att = dropbacks - sacks
        car = np.rint(plays).astype(int) - dropbacks
        # 3. efficiency shocks tied to the points residual
        z = (pts[tid] - pts[tid].mean()) / max(pts[tid].std(), 1e-9)
        e_pass = np.exp(PASS_SHOCK_SD * (SHOCK_RHO * z + math.sqrt(1 - SHOCK_RHO ** 2) * rng.standard_normal(n)) - PASS_SHOCK_SD ** 2 / 2)
        e_rush = np.exp(RUSH_SHOCK_SD * (SHOCK_RHO * z + math.sqrt(1 - SHOCK_RHO ** 2) * rng.standard_normal(n)) - RUSH_SHOCK_SD ** 2 / 2)
        pass_adj = (op["ypa_allowed"] / L["ypt_att"])
        rush_adj = (op["ypc_allowed"] / L["ypc"])
        # 4. shares. Attempts go to active receivers, fringe receivers, or nobody (throwaways and spikes,
        # the league's 1 - targets/attempts). Volume vacated by inactive players goes 75% to the active
        # players in proportion to their shares and 25% to the fringe (the backup who wasn't playing).
        untgt = L.get("untargeted", 0.06)
        tshare = np.concatenate([_fill(np.array([P[p]["tgt_share"] for p in rec_ids]), 1 - untgt, FRINGE_T), [untgt]])
        cshare = _fill(np.array([P[p]["car_share"] for p in rush_ids]), 1.0, FRINGE_C)
        tgt = _multinomial(rng, att, _dirichlet(rng, tshare, n, SHARE_ALPHA))
        carries = _multinomial(rng, np.maximum(car, 0), _dirichlet(rng, cshare, n, SHARE_ALPHA))
        # 5. per-play yards
        rec_tot = np.zeros(n)
        comp_tot = np.zeros(n)
        pl = {}
        for j, pid in enumerate(rec_ids + ["_fringe"]):     # last column (untargeted) never completes
            pr = P.get(pid, {"catch": L["catch"], "ypr": L["ypr"] * 0.9})
            catches = rng.binomial(tgt[:, j], min(max(pr["catch"], 0.3), 0.95))
            ypr = pr["ypr"] * pass_adj * e_pass
            yds = _gamma_sum(rng, catches, CATCH_SHAPE, ypr / CATCH_SHAPE)
            rec_tot += yds
            comp_tot += catches
            if not pid.startswith("_"):
                pl[pid] = {"targets": tgt[:, j], "receptions": catches, "rec_yds": yds}
        for j, pid in enumerate(rush_ids + ["_fringe"]):
            pr = P.get(pid, {"ypc": L["ypc"] * 0.9})
            mean = max(pr["ypc"] * rush_adj, 0.5) * e_rush
            k = (mean + CARRY_SHIFT) ** 2 / CARRY_SD ** 2
            theta = CARRY_SD ** 2 / (mean + CARRY_SHIFT)
            c = carries[:, j]
            yds = np.where(c > 0, rng.gamma(np.maximum(c * k, 1e-9), theta) - CARRY_SHIFT * c, 0.0)
            if not pid.startswith("_"):
                d = pl.setdefault(pid, {})
                d["rush_att"], d["rush_yds"] = c, yds
        # 6. QB line and TDs
        if qb:
            d = pl.setdefault(qb, {})
            irate = P[qb]["int"] * op["int_forced"] / L["int"]
            d["pass_att"], d["completions"], d["pass_yds"] = att, comp_tot, rec_tot
            d["pass_int"] = rng.binomial(att, min(max(irate, 0.005), 0.08))
        n_td = tds[tid]
        rush_p = np.clip(tp["rush_td_share"] + 0.004 * margin[tid], 0.15, 0.75)
        rush_td = rng.binomial(n_td, rush_p)
        pass_td = n_td - rush_td
        # who scores: half his simulated share of this game's work, half his (shrunk) season TD share
        def _w(ids, work, share_key, other):
            if not ids:
                return np.ones((n, 1))
            wk = np.stack([work(p) for p in ids], 1).astype(float)
            tot = wk.sum(1, keepdims=True)
            frac = np.where(tot > 0, wk / np.maximum(tot, 1e-9), 1.0 / len(ids))
            season_share = np.array([P[p][share_key] for p in ids])
            season_share = season_share / max(season_share.sum(), 1e-9)
            w = 0.5 * frac + 0.5 * season_share[None, :]
            w = w * (1 - other)
            return np.concatenate([w, np.full((n, 1), other)], 1)
        wr = _w(rec_ids, lambda p: pl[p]["receptions"], "rec_td_share", 0.06)
        wc = _w(rush_ids, lambda p: pl[p]["rush_att"], "rush_td_share", 0.04)
        rtd = _multinomial(rng, pass_td, wr / wr.sum(1, keepdims=True))
        ctd = _multinomial(rng, rush_td, wc / wc.sum(1, keepdims=True))
        for j, pid in enumerate(rec_ids):
            pl[pid]["rec_td"] = rtd[:, j]
        for j, pid in enumerate(rush_ids):
            pl.setdefault(pid, {})["rush_td"] = ctd[:, j]
        if qb:
            pl[qb]["pass_td"] = pass_td
        for pid, d in pl.items():
            z0 = np.zeros(n)
            d["rush_rec_yds"] = d.get("rush_yds", z0) + d.get("rec_yds", z0)
            d["anytime_td"] = d.get("rush_td", z0) + d.get("rec_td", z0)
            d["name"] = P[pid]["name"]
            d["team"] = tid
            d["thin"] = P[pid]["thin"]
            d["returning"] = P[pid].get("returning", False)
            d["implied"] = P[pid].get("implied", False)
            res["players"][pid] = d
        res["teams"][tid] = {"abbr": target["abbr"][tid], "points": pts[tid], "margin": margin[tid], "tds": n_td,
                             "first_drive_score": first[tid], "plays": plays, "pass_att": att, "car": car, "qb": qb}
    return res


# ------------------------------------------------------------------ pricing
ROLE_GAP = {"rec_yds": 22, "rush_yds": 22, "rush_rec_yds": 28, "pass_yds": 45, "receptions": 2.0, "rush_att": 5.0,
            "completions": 4.0, "pass_att": 5.0}


def role_flags(p: dict, market: str, line: float, median: float, mean: float) -> list[str]:
    """Reasons not to trust the simulation for this player tonight (each caps the label at Low)."""
    f = []
    if p.get("implied"):
        f.append("no 2026 games: role read off the DK line, not priced")
    elif p.get("returning"):
        f.append("back after missing the team's last 3 games: snap share unknown (L5)")
    if p.get("thin"):
        f.append("under 3 games with this team")
    gap = ROLE_GAP.get(market)
    if gap is not None and abs(median - line) > max(gap, 0.4 * line):
        f.append(f"line {line} is far from the model median {median:.1f}: the book likely knows a role/injury change (L5/L6)")
    return f


def side_probs(arr: np.ndarray, line: float) -> tuple[float, float, float]:
    over = float(np.mean(arr > line))
    push = float(np.mean(arr == line)) if float(line).is_integer() else 0.0
    return over, 1 - over - push, push


ALT_STEPS = {"rec_yds": (-20, -10, 10, 20), "rush_yds": (-20, -10, 10, 20), "rush_rec_yds": (-25, -12, 12, 25),
             "pass_yds": (-50, -25, 25, 50), "receptions": (-2, -1, 1, 2), "rush_att": (-4, -2, 2, 4),
             "completions": (-4, -2, 2, 4), "pass_att": (-5, -3, 3, 5)}


def anchored_over(arr: np.ndarray, dk_line: float, line: float) -> float:
    """P(over `line`) from the simulated shape, re-centred so the DraftKings line is the median.
    The backtest says the book's line is the better centre and the simulation the better shape:
    this is how to price an app line or alt line that differs from DraftKings."""
    med = float(np.median(arr))
    if med > 0 and dk_line > 0 and np.issubdtype(arr.dtype, np.floating) and (arr != np.round(arr)).any():
        adj = arr * (dk_line / med)                    # yardage: scale (keeps the right skew)
    else:
        adj = arr + (dk_line - med)                    # counts: shift
    # the DK line is a median by construction: split the mass at it evenly
    over = float(np.mean(adj > line))
    push = float(np.mean(adj == line)) if float(line).is_integer() else 0.0
    return over / max(1 - push, 1e-9)


def player_history(pid: str, tid: str, games: list[dict], market: str, line: float) -> tuple[int, int]:
    """(overs, unders) at this line in this season's games he played (for this team or any)."""
    o = u = 0
    for g in games:
        for t, ps in g["players"].items():
            p = ps.get(pid)
            if not p:
                continue
            v = stat_value(p, market)
            if v is None:
                continue
            if v > line:
                o += 1
            elif v < line:
                u += 1
    return o, u


def stat_value(p: dict, market: str):
    f = {"pass_yds": "pass_yds", "completions": "comp", "pass_att": "pass_att", "pass_td": "pass_td", "pass_int": "pass_int",
         "rush_yds": "rush_yds", "rush_att": "car", "rec_yds": "rec_yds", "receptions": "rec"}
    if market == "rush_rec_yds":
        return p.get("rush_yds", 0.0) + p.get("rec_yds", 0.0)
    if market == "anytime_td":
        return p.get("rush_td", 0.0) + p.get("rec_td", 0.0)
    if market in ("pass_yds", "completions", "pass_att", "pass_td", "pass_int"):
        return p.get(f[market]) if p.get("pass_att") else None
    return p.get(f[market], 0.0)


def price_game(event_id: str, n: int = 50000, season: int | None = None, out_names: list[str] | None = None,
               seed: int = 7, alt: list[tuple] | None = None) -> dict:
    """alt: [(player name, market, line)] app or alt lines to price off the DK-anchored shape."""
    """Simulate a game from every earlier game this season, then price each DraftKings prop line."""
    target = game(event_id)
    if season is None:
        season = int(target["date"][:4]) if int(target["date"][5:7]) >= 3 else int(target["date"][:4]) - 1
    wk = int(target["week"]["number"]) if isinstance(target.get("week"), dict) else int(target.get("week") or 18)
    evs = [e for e in season_events(season, wk) if e["status"] == "STATUS_FINAL" and e["date"] < target["date"]]
    history = [g for g in load_games([e["id"] for e in evs]) if g["final"]]
    out_ids = set()
    for name in out_names or []:
        for tid in (target["home"], target["away"]):
            for g in history:
                for pid, p in g["players"].get(tid, {}).items():
                    if p.get("name", "").lower() == name.lower():
                        out_ids.add(pid)
    props = dk_props(event_id)
    listed = collections.defaultdict(dict)
    for pr in props:
        listed[pr["player_id"]][pr["market"]] = pr["line"]
    sim = simulate(target, history, n=n, seed=seed, out_ids=out_ids, listed=dict(listed))
    rows = []
    for pr in props:
        p = sim["players"].get(pr["player_id"])
        if not p or pr["market"] not in p:
            continue
        arr = p[pr["market"]]
        line = pr["line"]
        over, under, push = side_probs(arr, line)
        ho, hu = player_history(pr["player_id"], p["team"], history, pr["market"], line)
        flags = role_flags(p, pr["market"], line, float(np.median(arr)), float(np.mean(arr)))
        sides = (("over", over, ho),) if pr["market"] == "anytime_td" else (("over", over, ho), ("under", under, hu))
        best = None
        for side, pm, ph in sides:
            pm_n = pm / max(1 - push, 1e-9)
            pm_c = calibrated(pm_n, pr["market"])
            dec = ho + hu
            e = final_probability(pm_c, None, (ph / dec) if dec else None, f"nfl:{pr['market']}:{side}", dec)
            conf = "Low" if flags and e.confidence in ("High", "Medium") else e.confidence
            if best is None or e.p > best["p_final"]:
                best = {"side": side, "p_sim": round(pm_n, 4), "p_model": round(pm_c, 4),
                        "p_hist": round(ph / dec, 4) if dec else None,
                        "hist_n": dec, "p_final": e.p, "confidence": conf, "notes": e.notes}
        vol_key = {"rec_yds": "targets", "receptions": "targets", "rush_yds": "rush_att", "rush_att": "rush_att",
                   "rush_rec_yds": "rush_att"}.get(pr["market"], "pass_att")
        vol = p.get(vol_key)
        rows.append({"player_id": pr["player_id"], "player": p["name"], "team": sim["teams"][p["team"]]["abbr"],
                     "market": pr["market"], "line": line, "open": pr.get("open"), "updated": pr.get("updated"),
                     "volume": (vol_key, float(np.mean(vol))) if vol is not None else None,
                     "median": float(np.median(arr)), "mean": float(np.mean(arr)), "flags": flags, **best})
    rows.sort(key=lambda r: -r["p_final"])
    alts = []
    for name, market, line in alt or []:
        cands = [(pid, p) for pid, p in sim["players"].items() if name.lower() in str(p.get("name", "")).lower() and market in p]
        dk = {(r["player_id"], r["market"]): r["line"] for r in rows}
        for pid, p in cands[:1]:
            arr = p[market]
            base = dk.get((pid, market))
            if base is not None and abs(base - line) < 1e-9:   # same as the DK line: the shape adds nothing
                over = next((x["p_model"] if x["side"] == "over" else 1 - x["p_model"]) for x in rows
                            if x["player_id"] == pid and x["market"] == market)
            elif base is not None:
                over = anchored_over(arr, base, line)
            else:
                over = side_probs(arr, line)[0]
            alts.append({"player": p["name"], "market": market, "line": line, "dk_line": base, "p_over": round(over, 4),
                         "p_under": round(1 - over, 4), "anchored": base is not None})
    return {"target": target, "sim": sim, "rows": rows, "history_games": len(history), "history": history, "alts": alts}


# ------------------------------------------------------------------ backtest
def backtest(season: int, weeks: list[int], n: int = 10000) -> dict:
    """Replay finished games week by week (only earlier games + closing line) against DK closing lines."""
    evs = season_events(season, max(weeks))
    final = [e for e in evs if e["status"] == "STATUS_FINAL"]
    games = {g["event_id"]: g for g in load_games([e["id"] for e in final]) if g["final"]}
    props = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for eid, pr in zip([e["id"] for e in final if e["week"] in weeks],
                           ex.map(dk_props, [e["id"] for e in final if e["week"] in weeks])):
            props[eid] = pr
    recs = []
    for e in final:
        if e["week"] not in weeks or e["id"] not in games:
            continue
        tg = games[e["id"]]
        if tg["spread_home"] is None:
            continue
        hist = [g for g in games.values() if g["date"] < tg["date"]]
        # inactives: who actually suited up is known 90 minutes before kickoff; approximate with the
        # final injury report (Out/Doubtful). Players absent from the box score are not removed.
        listed = collections.defaultdict(dict)
        for pr in props.get(e["id"], []):
            listed[pr["player_id"]][pr["market"]] = pr["line"]
        sim = simulate(tg, hist, n=n, seed=int(e["id"]) % 100000, listed=dict(listed))
        for pr in props.get(e["id"], []):
            p = sim["players"].get(pr["player_id"])
            if not p or pr["market"] not in p:
                continue
            actual = None
            for tid, ps in tg["players"].items():
                if pr["player_id"] in ps:
                    actual = stat_value(ps[pr["player_id"]], pr["market"])
            if actual is None:
                continue  # didn't play: books void it
            arr = p[pr["market"]]
            over, under, push = side_probs(arr, pr["line"])
            flags = role_flags(p, pr["market"], pr["line"], float(np.median(arr)), float(np.mean(arr)))
            if p.get("implied"):
                continue
            alts = []
            for step in ALT_STEPS.get(pr["market"], ()):
                al = pr["line"] + step
                if al > 0 and actual != al:
                    alts.append((step, anchored_over(arr, pr["line"], al), 1.0 if actual > al else 0.0))
            recs.append({"flagged": bool(flags), "alts": alts,"event_id": e["id"], "week": e["week"], "player": p["name"], "market": pr["market"],
                         "line": pr["line"], "actual": actual, "p_over": over / max(1 - push, 1e-9),
                         "median": float(np.median(arr)), "mean": float(np.mean(arr)),
                         "pit": float(np.mean(arr < actual) + 0.5 * np.mean(arr == actual))})
    return {"records": recs, "summary": summarize(recs)}


def summarize(recs: list[dict]) -> dict:
    """Score model vs the DraftKings line on the same props."""
    out = {"n": len(recs)}
    dec = [r for r in recs if r["actual"] != r["line"]]
    if not dec:
        return out
    y = np.array([1.0 if r["actual"] > r["line"] else 0.0 for r in dec])
    p = np.clip(np.array([r["p_over"] for r in dec]), 0.01, 0.99)
    out["over_rate"] = float(y.mean())
    out["brier_model"] = float(np.mean((p - y) ** 2))
    out["brier_coinflip"] = float(np.mean((0.5 - y) ** 2))
    # side accuracy when the model leans hard
    for thr in (0.55, 0.60, 0.65):
        m = np.abs(p - 0.5) >= thr - 0.5
        if m.any():
            hit = np.where(p[m] > 0.5, y[m], 1 - y[m])
            out[f"hit_at_{int(thr * 100)}"] = (float(hit.mean()), int(m.sum()))
    # calibration buckets on the side the model favours
    fav = np.where(p >= 0.5, p, 1 - p)
    hit = np.where(p >= 0.5, y, 1 - y)
    buckets = []
    for lo, hi in ((0.5, 0.55), (0.55, 0.6), (0.6, 0.65), (0.65, 0.7), (0.7, 1.01)):
        m = (fav >= lo) & (fav < hi)
        if m.any():
            buckets.append((lo, hi, int(m.sum()), float(fav[m].mean()), float(hit[m].mean())))
    out["calibration"] = buckets
    # point accuracy: model median vs the DK line as a forecast of the actual
    a = np.array([r["actual"] for r in recs])
    med = np.array([r["median"] for r in recs])
    mean = np.array([r["mean"] for r in recs])
    line = np.array([r["line"] for r in recs])
    out["mae_model_median"] = float(np.mean(np.abs(med - a)))
    out["mae_model_mean"] = float(np.mean(np.abs(mean - a)))
    out["mae_dk_line"] = float(np.mean(np.abs(line - a)))
    pit = np.array([r["pit"] for r in recs])
    out["pit_deciles"] = [float(np.mean((pit >= i / 10) & (pit < (i + 1) / 10))) for i in range(10)]
    out["within_10pct_of_actual_mean"] = float(np.mean(np.abs(mean - a) <= np.maximum(0.1 * np.abs(a), 1)))
    by = collections.defaultdict(list)
    for r in dec:
        by[r["market"]].append(r)
    out["by_market"] = {}
    for mk, rs in sorted(by.items()):
        yy = np.array([1.0 if r["actual"] > r["line"] else 0.0 for r in rs])
        pp = np.clip(np.array([r["p_over"] for r in rs]), 0.01, 0.99)
        aa = np.array([r["actual"] for r in rs])
        out["by_market"][mk] = {"n": len(rs), "brier_model": float(np.mean((pp - yy) ** 2)), "over_rate": float(yy.mean()),
                                "mae_median": float(np.mean(np.abs(np.array([r["median"] for r in rs]) - aa))),
                                "mae_line": float(np.mean(np.abs(np.array([r["line"] for r in rs]) - aa)))}
    return out


def fit_shrink(recs: list[dict], prior_n: float = 200.0) -> dict:
    """Per-market weight w on logit(model P(over)) that minimises Brier against results at the DK line
    (w = 0: the line is all there is; w = 1: trust the simulation as is). Small markets are pulled toward
    the pooled weight with prior_n props of strength. Flagged props (role doubts) are left out."""
    lg = lambda p: np.log(p / (1 - p))
    grid = np.linspace(0, 1, 41)

    def best(rs):
        y = np.array([1.0 if r["actual"] > r["line"] else 0.0 for r in rs])
        z = lg(np.clip(np.array([r["p_over"] for r in rs]), 0.02, 0.98))
        return float(min(grid, key=lambda w: np.mean((1 / (1 + np.exp(-w * z)) - y) ** 2)))

    use = [r for r in recs if r["market"] != "anytime_td" and not r.get("flagged") and r["actual"] != r["line"]]
    if not use:
        return {}
    pooled = best(use)
    out = {"_pooled": round(pooled, 3)}
    by = collections.defaultdict(list)
    for r in use:
        by[r["market"]].append(r)
    for mk, rs in by.items():
        out[mk] = round((len(rs) * best(rs) + prior_n * pooled) / (len(rs) + prior_n), 3)
    return out
