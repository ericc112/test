"""Data for the browser simulator (Sim Lab): python -m edge simlab --out data.js

The browser page runs every simulation itself (50,000 per game), so this only has to hand it inputs:
  NFL       the full player-level model inputs from nfl.game_inputs (same numbers `edge nfl` uses),
            DraftKings prop lines with this season's over/under counts, injury report, backtest scores
  CFB       spread/total for the drive model (game level)
  NBA/NCAAB spread/total for the margin/total model
  NHL       both moneylines + total + over/under prices for the Poisson goal model
  Soccer    three-way moneyline + total + over/under prices for the Poisson goal model
Lines come from each game's ESPN summary (DraftKings), with the opening line where ESPN carries it.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import re

import numpy as np

from . import nfl
from .blend import load_adjustments
from .grade import _get

SITE = "https://site.api.espn.com/apis/site/v2/sports"

# key, label, ESPN path, model, dates (YYYYMMDD, relative days from today), model params
LEAGUES = [
    ("cfb", "College football", "football/college-football", "football", range(0, 6), {"drives": 12.0, "fg_per_td": 0.45, "minutes": 60, "ot": "cfb"}),
    ("nba", "NBA", "basketball/nba", "basketball", range(0, 3), {"minutes": 48, "sd_margin": 12.5, "sd_total": 18.0}),
    ("ncaab", "College basketball", "basketball/mens-college-basketball", "basketball", range(0, 2), {"minutes": 40, "sd_margin": 10.5, "sd_total": 15.0}),
    ("nhl", "NHL", "hockey/nhl", "hockey", range(0, 2), {"minutes": 60}),
    ("ucl", "Champions League", "soccer/uefa.champions", "soccer", range(0, 3), {"minutes": 90}),
    ("epl", "Premier League", "soccer/eng.1", "soccer", range(0, 7), {"minutes": 90}),
]


def _num(x):
    try:
        return float(str(x).replace("+", "").replace("o", "").replace("u", ""))
    except (TypeError, ValueError):
        return None


def market(summary: dict) -> dict:
    """DraftKings lines from an ESPN summary's pickcenter: home spread, total, moneylines, O/U prices, opens."""
    pc = (summary.get("pickcenter") or [{}])[0]
    h, a, d = pc.get("homeTeamOdds") or {}, pc.get("awayTeamOdds") or {}, pc.get("drawOdds") or {}
    sp = pc.get("spread")
    if sp is not None and h.get("favorite") is True and sp > 0 or sp is not None and h.get("favorite") is False and sp < 0:
        sp = -sp
    ps, tot, ml = pc.get("pointSpread") or {}, pc.get("total") or {}, pc.get("moneyline") or {}
    return {"spread": sp, "total": pc.get("overUnder"), "ml_home": _num(h.get("moneyLine")), "ml_away": _num(a.get("moneyLine")),
            "ml_draw": _num(d.get("moneyLine")), "over": _num(pc.get("overOdds")), "under": _num(pc.get("underOdds")),
            "open_spread": _num(((ps.get("home") or {}).get("open") or {}).get("line")),
            "open_total": _num(((tot.get("over") or {}).get("open") or {}).get("line")),
            "open_ml_home": _num(((ml.get("home") or {}).get("open") or {}).get("odds")),
            "open_ml_away": _num(((ml.get("away") or {}).get("open") or {}).get("odds")),
            "details": pc.get("details")}


def _game_card(ev: dict, summary: dict) -> dict:
    c = ev["competitions"][0]
    t = {x["homeAway"]: x for x in c["competitors"]}
    out = {"id": ev["id"], "start": ev["date"], "status": c["status"]["type"]["name"].replace("STATUS_", "").lower(),
           "home": t["home"]["team"].get("abbreviation", "HOME"), "away": t["away"]["team"].get("abbreviation", "AWAY"),
           "home_name": t["home"]["team"].get("displayName"), "away_name": t["away"]["team"].get("displayName"),
           "venue": ((c.get("venue") or {}).get("fullName")), **market(summary)}
    w = (summary.get("gameInfo") or {}).get("weather") or {}
    if w.get("temperature") is not None:
        out["weather"] = f"{w['temperature']}°F" + (f", {w['displayValue']}" if w.get("displayValue") else "")
    return out


def league_games(path: str, days, today: dt.date) -> list[dict]:
    evs = {}
    for d in days:
        day = (today + dt.timedelta(days=d)).strftime("%Y%m%d")
        try:
            for e in _get(f"{SITE}/{path}/scoreboard?dates={day}").get("events", []):
                evs[e["id"]] = e
        except Exception:
            continue
    evs = [e for e in evs.values() if e["competitions"][0]["status"]["type"]["name"] in ("STATUS_SCHEDULED", "STATUS_IN_PROGRESS")]

    def one(e):
        try:
            return _game_card(e, _get(f"{SITE}/{path}/summary?event={e['id']}"))
        except Exception:
            return None
    with cf.ThreadPoolExecutor(8) as ex:
        games = [g for g in ex.map(one, evs) if g]
    return sorted(games, key=lambda g: g["start"])


def _r(x, k=4):
    return None if x is None else round(float(x), k)


def nfl_game(target: dict, history: list[dict], L: dict) -> dict:
    """Player-level inputs for one NFL game, in the shape the browser simulator reads."""
    props = nfl.dk_props(target["event_id"])
    listed = {}
    for pr in props:
        listed.setdefault(pr["player_id"], {})[pr["market"]] = pr["line"]
    gi = nfl.game_inputs(target, history, L=L, listed=listed)
    teams = {}
    for side, tid in (("home", target["home"]), ("away", target["away"])):
        ti, tp = gi["teams"][tid], gi["T"][tid]
        P = ti["P"]
        meta = lambda pid: {"id": pid, "name": P[pid]["name"], "thin": bool(P[pid]["thin"]),
                            "returning": bool(P[pid].get("returning")), "implied": bool(P[pid].get("implied")), "games": P[pid]["games"]}
        teams[side] = {
            "tid": tid, "abbr": target["abbr"][tid], "implied": _r(gi["implied"][tid], 2), "p_td": _r(ti["p_td"]), "p_fg": _r(ti["p_fg"]),
            "plays_mu": _r(ti["plays_mu"], 2), "db_rate": _r(tp["db_rate"]), "sack_rate": _r(ti["sack_rate"]), "pass_adj": _r(ti["pass_adj"]),
            "rush_adj": _r(ti["rush_adj"]), "int_rate": _r(ti["int_rate"]), "rush_td_share": _r(tp["rush_td_share"]), "qb": ti["qb"],
            "tshare": [_r(x) for x in ti["tshare"]], "cshare": [_r(x) for x in ti["cshare"]],
            "rec": [{**meta(p), "catch": _r(P[p]["catch"]), "ypr": _r(P[p]["ypr"], 2), "td": _r(P[p]["rec_td_share"]),
                     "share": _r(P[p]["tgt_share"])} for p in ti["rec_ids"]],
            "rush": [{**meta(p), "ypc": _r(P[p]["ypc"], 2), "td": _r(P[p]["rush_td_share"]), "share": _r(P[p]["car_share"])} for p in ti["rush_ids"]],
            "qb_name": P[ti["qb"]]["name"] if ti["qb"] else None, "qb_games": P[ti["qb"]]["games"] if ti["qb"] else 0,
        }
    out_names, questionable = [], []
    for tid, lst in (target.get("out") or {}).items():
        for i in lst:
            st = (i.get("status") or "").lower()
            row = f"{target['abbr'][tid]} {i['name']} ({i.get('status')})"
            (questionable if st == "questionable" else out_names if i["id"] in gi["out_ids"] else []).append(row)
    pl = []
    for pr in props:
        o, u = nfl.player_history(pr["player_id"], None, history, pr["market"], pr["line"])
        pl.append({"pid": pr["player_id"], "market": pr["market"], "line": pr["line"], "open": pr.get("open"), "ho": o, "hu": u})
    Lx = {k: _r(L[k]) for k in ("plays", "beta_plays", "beta_db", "plays_resid_sd", "db_resid_sd", "catch", "ypr", "ypc", "untargeted")}
    return {"d_mu": _r(gi["d_mu"], 3), "L": Lx, "teams": teams, "props": pl, "out": out_names, "questionable": questionable,
            "history_games": len(history)}


def export(path: str, nfl_week: int | None = None, backtest_weeks: tuple = (3, 8)) -> dict:
    today = dt.date.today()
    season = today.year if today.month >= 3 else today.year - 1
    adj = load_adjustments()
    data = {"pulled": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "leagues": [],
            "blend": adj["blend"], "gates": adj["gates"],
            "outcome_bias": {k: v for k, v in adj["outcome_bias_logit"].items() if k.startswith("nfl")},
            "shrink": nfl.MODEL_SHRINK,
            "consts": {k: getattr(nfl, k) for k in ("SHARE_ALPHA", "CATCH_SHAPE", "CARRY_SD", "CARRY_SHIFT", "PASS_SHOCK_SD",
                                                     "RUSH_SHOCK_SD", "SHOCK_RHO", "PLAYS_SD_MULT", "FRINGE_T", "FRINGE_C")},
            "role_gap": nfl.ROLE_GAP}
    # NFL: the week that has games still to play
    evs = nfl.season_events(season, 18)
    if nfl_week is None:
        nfl_week = min((e["week"] for e in evs if e["status"] in ("STATUS_SCHEDULED", "STATUS_IN_PROGRESS")), default=18)
    final = [e for e in evs if e["status"] == "STATUS_FINAL"]
    history = [g for g in nfl.load_games([e["id"] for e in final]) if g["final"]]
    L = nfl.league_params(history)
    games = []
    for e in [e for e in evs if e["week"] == nfl_week and e["status"] != "STATUS_FINAL"]:
        tg = nfl.game(e["id"])
        if tg.get("spread_home") is None:
            continue
        summ = _get(f"{SITE}/football/nfl/summary?event={e['id']}")
        card = _game_card({"id": e["id"], "date": e["date"], "competitions": summ["header"]["competitions"]}, summ)
        card["nfl"] = nfl_game(tg, [g for g in history if g["date"] < tg["date"]], L)
        games.append(card)
    data["leagues"].append({"key": "nfl", "label": f"NFL week {nfl_week}", "model": "nfl",
                            "params": {"minutes": 60, "drives": float(L.get("drives", 10.2)), "ot": "nfl"}, "games": games})
    for key, label, p, model, days, params in LEAGUES:
        data["leagues"].append({"key": key, "label": label, "model": model, "params": params, "games": league_games(p, days, today)})
    if backtest_weeks:
        bt = nfl.backtest(season, list(range(backtest_weeks[0], backtest_weeks[1] + 1)), n=10000)
        s = bt["summary"]
        data["backtest"] = {"weeks": list(backtest_weeks), "n": s["n"],
                            "by_market": {k: {kk: _r(vv, 3) for kk, vv in v.items()} for k, v in s["by_market"].items()},
                            "calibration": [[lo, min(hi, 1.0), n, _r(pm, 3), _r(hit, 3)] for lo, hi, n, pm, hit in s["calibration"]]}
    with open(path, "w") as f:
        f.write("window.SIMLAB = " + json.dumps(data, separators=(",", ":"), default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o)) + ";\n")
    return {"path": path, "nfl_week": nfl_week, "games": {lg["key"]: len(lg["games"]) for lg in data["leagues"]}}
