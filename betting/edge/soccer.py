"""Soccer passes attempted (ESPN data, no keys).

    player passes = team passes x his share per 90 x minutes / 90
    team passes   = possession x 100 x team passes per possession point x opponent press factor

  possession     half stats (log5 of both teams' averages, +/-2 pts home) and half market
                 (0.5 + 0.21 x (P(win) - P(loss)) - 0.02 home, from the DraftKings 3-way line)
  press factor   passes the opponent lets teams make per point of possession, vs its league
                 (a high press or compact block shows up as fewer passes per point of the ball)
  game script    the result is drawn from the 3-way line; winners end with ~2.9 pts less
                 possession than forecast, losers ~2.9 pts more
  spread         team passes +/-19% (forecast error) x share +/-14.5% x Poisson; minutes drawn
                 from his own recent starts

Backtest, 250 matches in the top four leagues (Aug-Oct 2026), each team's numbers from its other
matches: team-pass error 70.6 vs 74.2 for possession x tempo and 81.1 for the team average;
possession error 6.8 pts vs 7.2 stats-only and 9.5 for 50/50. On 190 starter-matches the player
distribution was calibrated (PIT sd 0.284 vs 0.289 ideal; the old 17% spread was overconfident).
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import functools
import json
import os

import numpy as np

from .blend import HERE
from .grade import _get, soccer_player_stats

SITE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
CUPS = ("uefa.champions", "uefa.europa", "uefa.europa.conf")
HOME_EDGE = 0.02
MKT = {"slope": 0.21, "home": -0.02, "w_stats": 0.5}       # fitted league-out on the backtest
GAME_STATE = 0.029                                          # possession shift by final result
CV_TEAM, CV_SHARE = 0.19, 0.145
LEAGUE_PPP = {"eng.1": 8.69, "esp.1": 9.13, "fra.1": 9.61, "ita.1": 9.24}   # passes per possession point
BASE_PATH = os.path.join(HERE, "data", "soccer_baselines.json")
MIN_TEAM_PASSES = 150          # below this a box score is partial
PRESS_CLIP = (0.75, 1.25)      # outside this the opponent sample is broken, not the press
POSS_BAND, MIN_COMPARABLE = 0.07, 4   # L27: compare like with like (team possession within 7 points)
SHARE_SHRINK = 4                        # comparable-start share gets weight n / (n + 4)
COMPARABLE_REACH = 40                  # team matches searched for comparable-possession starts
KEEPER_CV = 0.12               # match-to-match noise on a keeper's per-90 rate, on top of his own spread


# ------------------------------------------------------------------ pure model
def log5(a: float, b: float) -> float:
    """Possession share for a team that averages `a` against an opponent that averages `b`."""
    return a * (1 - b) / (a * (1 - b) + b * (1 - a))


def market_possession(p_win: float, p_loss: float, home: bool | None) -> float:
    return 0.5 + MKT["slope"] * (p_win - p_loss) + (MKT["home"] * (1 if home else -1) if home is not None else 0)


def possession(team_poss: float, opp_poss: float, home: bool | None, wdl: tuple | None = None,
               same_league: bool = True) -> dict:
    stats = log5(team_poss, opp_poss) + (HOME_EDGE if home else -HOME_EDGE if home is not None else 0)
    if wdl:
        mkt = market_possession(wdl[0], wdl[2], home)
        p = MKT["w_stats"] * stats + (1 - MKT["w_stats"]) * mkt
    else:
        mkt = None
        p = stats if same_league else 0.5 + 0.5 * (stats - 0.5)  # no market: shrink cross-league gaps
    return {"stats": stats, "market": mkt, "possession": float(min(max(p, 0.2), 0.8))}


def project(poss: float, rate: float, share: float, minutes=None, wdl=None, line=None, n=200_000, seed=7) -> dict:
    """rate = team passes per possession point after the press factor; share = his passes per 90 / team passes."""
    rng = np.random.default_rng(seed)
    p = np.full(n, poss)
    if wdl:  # game script from the 3-way market
        res = rng.choice(3, n, p=np.array(wdl) / sum(wdl))
        p = p + np.select([res == 0, res == 2], [-GAME_STATE, GAME_STATE], 0.0)
    kt, ks = 1 / CV_TEAM ** 2, 1 / CV_SHARE ** 2
    team = np.clip(p, 0.15, 0.85) * 100 * rate * rng.gamma(kt, 1 / kt, n)
    mins = rng.choice(np.array(minutes or [90.0]), n) / 90
    x = rng.poisson(team * share * rng.gamma(ks, 1 / ks, n) * mins)
    out = {"team_passes": float(np.median(team)), "mean": float(x.mean()), "median": float(np.median(x)),
           "p10": float(np.percentile(x, 10)), "p90": float(np.percentile(x, 90))}
    if line is not None:
        out.update(p_over=float((x > line).mean()), p_under=float((x < line).mean()), p_push=float((x == line).mean()))
    return out


# ------------------------------------------------------------------ ESPN data
@functools.lru_cache(maxsize=512)
def summary(event_id: str) -> dict:
    return _get(f"{SITE}/all/summary?event={event_id}")


def _implied(ml):
    try:
        ml = float(ml)
    except (TypeError, ValueError):
        return None
    return 100 / (ml + 100) if ml > 0 else -ml / (-ml + 100)


def match_context(event_id: str, team_id: str) -> dict:
    """Home/away, opponent and the de-vigged win/draw/loss line for an upcoming match."""
    s = summary(event_id)
    comp = s["header"]["competitions"][0]
    me = next(c for c in comp["competitors"] if str(c["team"]["id"]) == str(team_id))
    opp = next(c for c in comp["competitors"] if str(c["team"]["id"]) != str(team_id))
    pc = (s.get("pickcenter") or [{}])[0]
    side = "homeTeamOdds" if me["homeAway"] == "home" else "awayTeamOdds"
    oside = "awayTeamOdds" if side == "homeTeamOdds" else "homeTeamOdds"
    w, d, l = (_implied((pc.get(k) or {}).get("moneyLine")) for k in (side, "drawOdds", oside))
    wdl = None if None in (w, d, l) else tuple(v / (w + d + l) for v in (w, d, l))
    return {"home": me["homeAway"] == "home", "opp_id": str(opp["team"]["id"]), "opp_name": opp["team"].get("displayName"), "wdl": wdl}


@functools.lru_cache(maxsize=64)   # one fetch per team per run, however many of its players are on the board
def team_matches(team_id: str, n: int = 10, seasons=("2026", "2025")) -> list[dict]:
    """Last n completed matches (domestic league + European cups), with both sides' passes and possession."""
    dom = (_get(f"{SITE}/all/teams/{team_id}").get("team") or {}).get("defaultLeague", {}).get("slug")
    evs = set()
    for lg in [x for x in (dom, *CUPS) if x]:
        for s in seasons:
            try:
                for e in _get(f"{SITE}/{lg}/teams/{team_id}/schedule?season={s}").get("events", []):
                    if e["competitions"][0]["status"]["type"].get("completed"):
                        evs.add((e["date"], lg, e["id"]))
            except Exception:
                continue

    def one(ev):
        date, lg, eid = ev
        s = summary(eid)
        teams = {str(t["team"]["id"]): {x["name"]: x.get("displayValue") for x in t.get("statistics", [])}
                 for t in (s.get("boxscore") or {}).get("teams", [])}
        me = teams.get(str(team_id), {})
        opp = next((v for k, v in teams.items() if k != str(team_id)), {})
        try:
            row = {"date": date[:10], "league": lg, "domestic": dom, "event_id": eid, "summary": s,
                   "poss": float(me["possessionPct"]) / 100, "passes": float(me["totalPasses"]), "opp_passes": float(opp["totalPasses"])}
        except (KeyError, TypeError, ValueError):
            return None
        # partial feeds come back as zeros or a few dozen passes: a top-flight side never has fewer than MIN_TEAM_PASSES
        ok = row["passes"] >= MIN_TEAM_PASSES and row["opp_passes"] >= MIN_TEAM_PASSES and 0.15 <= row["poss"] <= 0.85
        return row if ok else None

    with cf.ThreadPoolExecutor(8) as ex:
        return [m for m in ex.map(one, sorted(evs, reverse=True)[:n]) if m]


SUMMARY_CACHE = os.path.join(HERE, ".cache", "espn_soccer")


def summary_cached(event_id: str) -> dict:
    """ESPN's match summary; finished matches are kept on disk (they never change)."""
    p = os.path.join(SUMMARY_CACHE, f"{event_id}.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    s = summary(event_id)
    if ((s.get("header") or {}).get("competitions") or [{}])[0].get("status", {}).get("type", {}).get("completed"):
        os.makedirs(SUMMARY_CACHE, exist_ok=True)
        with open(p, "w") as f:
            json.dump({k: s.get(k) for k in ("header", "rosters", "boxscore")}, f)
    return s


def team_history(team_id: str, comps=(), n: int = 25, seasons=("2026", "2025")) -> list[dict]:
    """His team's last n finished matches in any competition we can see (domestic league, the cups, and tonight's
    competition), newest first: {date, event_id, opp, home, summary}. Unlike team_matches it keeps matches whose feed has
    no passing numbers, so shots, saves and fouls can be counted in every league ESPN covers."""
    dom = (_get(f"{SITE}/all/teams/{team_id}").get("team") or {}).get("defaultLeague", {}).get("slug")
    evs = {}
    for lg in dict.fromkeys(x for x in (dom, *comps, *CUPS) if x):
        for se in seasons:
            try:
                for e in _get(f"{SITE}/{lg}/teams/{team_id}/schedule?season={se}").get("events", []):
                    if e["competitions"][0]["status"]["type"].get("completed"):
                        evs[e["id"]] = e["date"]
            except Exception:
                continue

    def one(item):
        eid, date = item
        try:
            s = summary_cached(eid)
        except Exception:
            return None
        cs = ((s.get("header") or {}).get("competitions") or [{}])[0].get("competitors") or []
        me = next((c for c in cs if str(c.get("id") or (c.get("team") or {}).get("id")) == str(team_id)), None)
        op = next((c for c in cs if c is not me), None)
        return {"date": date[:10], "event_id": eid, "summary": s, "home": (me or {}).get("homeAway") == "home",
                "opp": ((op or {}).get("team") or {}).get("abbreviation") or ((op or {}).get("team") or {}).get("displayName") or ""}

    with cf.ThreadPoolExecutor(8) as ex:
        return [m for m in ex.map(one, sorted(evs.items(), key=lambda kv: kv[1], reverse=True)[:n]) if m]


def league_ppp(league: str) -> float:
    """League-average passes per possession point (cached; computed from up to 60 recent league matches)."""
    if league in LEAGUE_PPP:
        return LEAGUE_PPP[league]
    cache = json.load(open(BASE_PATH)) if os.path.exists(BASE_PATH) else {}
    hit = cache.get(league)
    if hit and (dt.date.today() - dt.date.fromisoformat(hit["date"])).days <= 14:
        return hit["ppp"]
    teams = _get(f"{SITE}/{league}/teams")["sports"][0]["leagues"][0]["teams"]
    evs = set()
    for t in teams:
        try:
            for e in _get(f"{SITE}/{league}/teams/{t['team']['id']}/schedule?season=2026").get("events", []):
                if e["competitions"][0]["status"]["type"].get("completed"):
                    evs.add(e["id"])
        except Exception:
            continue

    def one(eid):
        try:
            ts = summary(eid)["boxscore"]["teams"]
            return sum(float({x["name"]: x.get("displayValue") for x in t["statistics"]}["totalPasses"]) for t in ts) / 100
        except Exception:
            return None

    with cf.ThreadPoolExecutor(10) as ex:
        vals = [v for v in ex.map(one, sorted(evs)[-60:]) if v]
    ppp = float(np.mean(vals)) if vals else float(np.mean(list(LEAGUE_PPP.values())))
    cache[league] = {"ppp": round(ppp, 3), "date": dt.date.today().isoformat(), "n": len(vals)}
    with open(BASE_PATH, "w") as f:
        json.dump(cache, f, indent=2)
    return ppp


def player_match(m: dict, team_id: str, player_id: str) -> dict | None:
    """Minutes and passes attempted for one player in one match (None if he didn't play)."""
    for r in m["summary"].get("rosters", []):
        if str(r["team"]["id"]) == str(team_id):
            for p in r.get("roster", []):
                if str(p["athlete"]["id"]) == str(player_id) and (p.get("starter") or p.get("subbedIn")):
                    st = soccer_player_stats(m["league"], m["event_id"], team_id, player_id)
                    if st.get("accuratePasses") is None and st.get("inaccuratePasses") is None or not st.get("minutes"):
                        return None  # the stats feed sometimes returns an empty split: missing, never zero passes
                    return {"date": m["date"], "starter": bool(p.get("starter")), "minutes": st.get("minutes") or 0,
                            "passes": (st.get("accuratePasses") or 0) + (st.get("inaccuratePasses") or 0), "team_passes": m["passes"],
                            "league": m["league"], "event_id": m["event_id"], "position": (p.get("position") or {}).get("abbreviation"), "poss": m.get("poss")}
    return None


def passes_model(player_id: str, team_id: str, opp_id: str | None = None, line: float | None = None, home: bool | None = None,
                 event_id: str | None = None, n: int = 10, poss: float | None = None, hist_n: int = 25) -> dict:
    ctx = match_context(event_id, team_id) if event_id else {"home": home, "opp_id": opp_id, "wdl": None, "opp_name": None}
    if ctx["opp_id"] is None:
        raise ValueError("give --opp or --event")
    tm, om = team_matches(team_id, n), team_matches(ctx["opp_id"], n)
    with cf.ThreadPoolExecutor(8) as ex:
        games = [g for g in ex.map(lambda m: player_match(m, team_id, player_id), tm) if g]
    starts = [g for g in games if g["starter"] and g["minutes"] >= 45]
    if not starts:
        raise ValueError("no recent starts with passing data for this player")
    if any(g.get("position") == "G" for g in starts):
        return keeper_passes(player_id, team_id, ctx, event_id, line, hist_n)
    share = sum(g["passes"] for g in starts) / sum(g["team_passes"] * g["minutes"] / 90 for g in starts)
    t_poss, o_poss = float(np.mean([m["poss"] for m in tm])), float(np.mean([m["poss"] for m in om]))
    t_dom, o_dom = tm[0]["domestic"], om[0]["domestic"]
    if t_dom != o_dom:
        # L28: a cross-league tie can't use season possession: Bodø's 63% comes from dominating Norwegian sides. Use each
        # team's possession in European-cup matches (the same level as tonight) when both have 3+ of them.
        tc = [m["poss"] for m in team_matches(team_id, COMPARABLE_REACH) if m["league"] in CUPS]
        oc = [m["poss"] for m in team_matches(ctx["opp_id"], COMPARABLE_REACH) if m["league"] in CUPS]
        if len(tc) >= 3 and len(oc) >= 3:
            t_poss, o_poss = float(np.mean(tc)), float(np.mean(oc))
    pos = possession(t_poss, o_poss, ctx["home"], ctx["wdl"], same_league=t_dom == o_dom)
    if poss is not None:
        pos["possession"] = poss
    team_ppp = float(np.mean([m["passes"] / (m["poss"] * 100) for m in tm]))
    opp_allowed = float(np.mean([m["opp_passes"] / ((1 - m["poss"]) * 100) for m in om]))
    press = opp_allowed / league_ppp(o_dom) if o_dom else 1.0
    if t_dom != o_dom:  # measured against the opponent's own league, whose sides differ in quality: half weight
        press = 1 + 0.5 * (press - 1)
    press = min(max(press, PRESS_CLIP[0]), PRESS_CLIP[1])
    # L27: a player's share of team passes and his history both depend on how much of the ball his team has. A
    # centre-back's 100-pass games come at 70% possession; at 45-50% (big games) he makes half that. Measure share
    # and history in starts at a possession close to tonight's forecast whenever there are enough of them.
    pool = starts
    if hist_n > n:  # history reaches further back than the rate sample
        with cf.ThreadPoolExecutor(8) as ex:
            wide = [g for g in ex.map(lambda m: player_match(m, team_id, player_id), team_matches(team_id, COMPARABLE_REACH)) if g]
        wide = [g for g in wide if g["starter"] and g["minutes"] >= 45]
        pool = sorted(wide, key=lambda g: g["date"], reverse=True)
        recent = {m["event_id"] for m in team_matches(team_id, hist_n)}
    else:
        recent = None
    target = pos["possession"]
    comp = [g for g in pool if g.get("poss") is not None and abs(g["poss"] - target) <= POSS_BAND]
    if recent is not None:  # the plain-history fallback keeps its usual window
        pool = [g for g in pool if g.get("event_id") in recent] or pool
    basis = f"all {len(pool)} recent starts"
    if comp:  # shrink toward the all-starts share instead of an all-or-nothing cutoff
        w = len(comp) / (len(comp) + SHARE_SHRINK)
        share_c = sum(g["passes"] for g in comp) / sum(g["team_passes"] * g["minutes"] / 90 for g in comp)
        share = w * share_c + (1 - w) * share
        basis = f"{len(comp)} starts at {target - POSS_BAND:.0%}-{target + POSS_BAND:.0%} possession (weight {w:.0%})"
    proj = project(pos["possession"], team_ppp * press, share, [g["minutes"] for g in starts], ctx["wdl"], line)
    out = {**ctx, "starts": starts, "share": share, "team_poss": t_poss, "opp_poss": o_poss, **pos,
           "team_ppp": team_ppp, "opp_allowed_ppp": opp_allowed, "press_factor": press, "basis": basis, **proj}
    if line is not None:
        hist = comp if len(comp) >= MIN_COMPARABLE else pool
        vals = [g["passes"] for g in hist]
        out["hist_over"], out["hist_n"] = sum(h > line for h in vals) / len(vals), len(vals)
        out["hist_vals"] = vals
    out["days_rest"] = (dt.date.today() - dt.date.fromisoformat(max(m["date"] for m in tm))).days
    return out


def keeper_passes(player_id: str, team_id: str, ctx: dict, event_id: str | None, line: float | None, hist_n: int = 25,
                  n: int = 200_000, seed: int = 7) -> dict:
    """Goalkeepers don't follow the outfield model: their passes go UP when the team has less of the ball (goal kicks,
    back-passes under a press). Haikin: 19-27 in Norway at 55-78% possession, 29-44 in the Champions League at 29-48%.
    So price a keeper from his own per-90 rate in the same kind of competition (European cup vs domestic), not from
    team possession x share."""
    rng = np.random.default_rng(seed)
    cup = bool(event_id) and (summary(event_id).get("header", {}).get("league", {}).get("slug") in CUPS)
    with cf.ThreadPoolExecutor(8) as ex:
        rows = [g for g in ex.map(lambda m: player_match(m, team_id, player_id), team_matches(team_id, max(hist_n, 40))) if g]
    rows = [g for g in rows if g["starter"] and g["minutes"] >= 60]
    same = [g for g in rows if (g["league"] in CUPS) == cup]
    sample = same if len(same) >= 5 else rows
    if not sample:
        raise ValueError("no recent keeper starts with passing data")
    rates = np.array([g["passes"] * 90 / g["minutes"] for g in sample])
    x = rng.poisson(rng.choice(rates, n) * rng.gamma(1 / KEEPER_CV ** 2, KEEPER_CV ** 2, n))
    out = {**ctx, "keeper": True, "sample": ("European cup" if cup else "domestic") if sample is same else "all competitions",
           "starts": sample, "share": None, "possession": float("nan"), "press_factor": float("nan"), "team_passes": None,
           "mean": float(x.mean()), "median": float(np.median(x)), "p10": float(np.percentile(x, 10)), "p90": float(np.percentile(x, 90))}
    if line is not None:
        vals = [g["passes"] for g in sample]
        out.update(p_over=float((x > line).mean()), p_under=float((x < line).mean()), p_push=float((x == line).mean()),
                   hist_over=sum(v > line for v in vals) / len(vals), hist_n=len(vals), hist_vals=vals)
    out["days_rest"] = None
    return out

