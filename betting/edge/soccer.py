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
                            "passes": (st.get("accuratePasses") or 0) + (st.get("inaccuratePasses") or 0), "team_passes": m["passes"]}
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
    share = sum(g["passes"] for g in starts) / sum(g["team_passes"] * g["minutes"] / 90 for g in starts)
    t_poss, o_poss = float(np.mean([m["poss"] for m in tm])), float(np.mean([m["poss"] for m in om]))
    t_dom, o_dom = tm[0]["domestic"], om[0]["domestic"]
    pos = possession(t_poss, o_poss, ctx["home"], ctx["wdl"], same_league=t_dom == o_dom)
    if poss is not None:
        pos["possession"] = poss
    team_ppp = float(np.mean([m["passes"] / (m["poss"] * 100) for m in tm]))
    opp_allowed = float(np.mean([m["opp_passes"] / ((1 - m["poss"]) * 100) for m in om]))
    press = opp_allowed / league_ppp(o_dom) if o_dom else 1.0
    if t_dom != o_dom:  # measured against the opponent's own league, whose sides differ in quality: half weight
        press = 1 + 0.5 * (press - 1)
    press = min(max(press, PRESS_CLIP[0]), PRESS_CLIP[1])
    proj = project(pos["possession"], team_ppp * press, share, [g["minutes"] for g in starts], ctx["wdl"], line)
    out = {**ctx, "starts": starts, "share": share, "team_poss": t_poss, "opp_poss": o_poss, **pos,
           "team_ppp": team_ppp, "opp_allowed_ppp": opp_allowed, "press_factor": press, **proj}
    if line is not None:
        hist = starts
        if hist_n > n:  # history reaches further back than the rate sample
            with cf.ThreadPoolExecutor(8) as ex:
                hist = [g for g in ex.map(lambda m: player_match(m, team_id, player_id), team_matches(team_id, hist_n)) if g]
            hist = [g for g in hist if g["starter"] and g["minutes"] >= 45]
        vals = [g["passes"] for g in hist]
        out["hist_over"], out["hist_n"] = sum(h > line for h in vals) / len(vals), len(vals)
        out["hist_vals"] = vals
    out["days_rest"] = (dt.date.today() - dt.date.fromisoformat(max(m["date"] for m in tm))).days
    return out
