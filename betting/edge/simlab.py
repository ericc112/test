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

import os

from gamesim import data as gs_data

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
            "spread_home_odds": _num(h.get("spreadOdds")), "spread_away_odds": _num(a.get("spreadOdds")),
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
           "home_color": t["home"]["team"].get("color"), "away_color": t["away"]["team"].get("color"),
           "home_alt": t["home"]["team"].get("alternateColor"), "away_alt": t["away"]["team"].get("alternateColor"),
           "venue": ((c.get("venue") or {}).get("fullName")), **market(summary)}
    out["injuries"] = [{"team": t["team"].get("abbreviation"), "name": i["athlete"]["displayName"], "status": i.get("status"),
                        "detail": " ".join(x for x in ((i.get("details") or {}).get("type"), (i.get("details") or {}).get("detail")) if x and x != "Not Specified")}
                       for t in summary.get("injuries", []) or [] for i in t.get("injuries", []) or []]
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
    # pre-game or live (in progress, halftime, between periods): ESPN's state is "pre" / "in"; "post" is final
    evs = [e for e in evs.values() if (e["competitions"][0]["status"]["type"].get("state") in ("pre", "in"))
           or e["competitions"][0]["status"]["type"]["name"] in ("STATUS_SCHEDULED", "STATUS_IN_PROGRESS", "STATUS_HALFTIME", "STATUS_END_PERIOD")]

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


def us_today() -> dt.date:
    """Today's date in US Eastern time: slates are US dates, and the server clock is UTC (after 8 pm ET it already
    reads tomorrow, which dropped tonight's games from the export)."""
    from zoneinfo import ZoneInfo
    return dt.datetime.now(ZoneInfo("America/New_York")).date()


def export(path: str, nfl_week: int | None = None, backtest_weeks: tuple = (3, 8)) -> dict:
    today = us_today()
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
    data["engines"] = engines(data)
    if backtest_weeks:
        bt = nfl.backtest(season, list(range(backtest_weeks[0], backtest_weeks[1] + 1)), n=10000)
        s = bt["summary"]
        data["backtest"] = {"weeks": list(backtest_weeks), "n": s["n"],
                            "by_market": {k: {kk: _r(vv, 3) for kk, vv in v.items()} for k, v in s["by_market"].items()},
                            "calibration": [[lo, min(hi, 1.0), n, _r(pm, 3), _r(hit, 3)] for lo, hi, n, pm, hit in s["calibration"]]}
    try:                                   # tennis match simulator (ATP + WTA): never sinks the rest of the export
        from . import tennis_watch
        data["tennis"] = tennis_watch.export()
    except Exception as e:
        data["tennis"] = {"matches": [], "note": f"tennis matches not loaded ({type(e).__name__}: {str(e)[:80]})"}
    try:                                   # the Winners tab: projected winners and scores, night by night (after tennis, which saves its projections)
        from . import winners
        data["winners"] = winners.export()
    except Exception as e:
        data["winners"] = {"nights": [], "note": f"winners not loaded ({type(e).__name__}: {str(e)[:80]})"}
    with open(path, "w") as f:
        f.write("window.SIMLAB = " + json.dumps(data, separators=(",", ":"), default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o)) + ";\n")
    return {"path": path, "nfl_week": nfl_week, "games": {lg["key"]: len(lg["games"]) for lg in data["leagues"]},
            "tennis": len(data["tennis"].get("matches") or [])}


# ------------------------------------------------------------------ the gamesim engines, for the browser
def _sub(v, k: int, nd: int | None = None, seed: int = 1) -> list:
    """Subsample an empirical pool to at most k values (seeded) and round it, to keep the data file small."""
    a = np.asarray(v, float)
    if len(a) > k:
        a = np.random.default_rng(seed).choice(a, k, replace=False)
    return [round(float(x), nd) if nd else int(round(float(x))) for x in a]


def _json_or_none(path: str):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _bt_records(name: str) -> list[dict]:
    d = _json_or_none(os.path.join(gs_data.CACHE, f"bt_{name}.json"))
    return (d or {}).get("records", [])


def _bt(name: str, compute):
    """Backtest metrics, cached in .cache/gamesim/bt_<name>.json (recomputed when missing)."""
    path = os.path.join(gs_data.CACHE, f"bt_{name}.json")
    if os.path.exists(path):
        return json.load(open(path))["metrics"]
    bt = compute()
    json.dump(bt, open(path, "w"))
    return bt["metrics"]


def nba_engine(nba_games: list[dict], today: dt.date | None = None) -> dict:
    """NBA possession engine inputs for a list of game cards (league_games): calibrated ratings, each game's sides
    (availability, player ratings), the player layer (rotation with head-to-head, research, DraftKings lines) and
    the backtests. Shared by the Sim Lab export and the PrizePicks NBA pricer (edge/nba_pp.py)."""
    from gamesim import backtest as gbt, nba as gnba, nba_research as gres
    today = today or dt.date.today()
    y = today.year if today.month >= 9 else today.year - 1
    yday = (today - dt.timedelta(days=1)).strftime("%Y%m%d")
    G = gnba.season_games("nba", f"{y}1018", yday)
    cut = gs_data.now_cutoff()               # every game of earlier US days, last night's included (UTC dates lag)
    R = gnba.calibrate(gnba.ratings(G, cut, 48), G, cut, 48, 24)
    span0 = gnba.LAST_SEASON.get(y)                       # player layer prior: each player's own last season
    PT = gnba.season_player_totals("nba", gnba.season_games("nba", *span0)) if span0 else None
    PRt = gnba.PlayerRatings("nba", G, y) if gnba.PLAYER_RATING_W else None   # team strength from player ratings
    RS = gres.Research("nba", G, y)                       # handicapper-style research (game logs, hit rates, head-to-head)
    prf = PRt.fit(cut) if PRt else None
    sides, prof = {}, {}
    for g in nba_games:
        # availability: tonight's Out/Doubtful list (and players gone from the roster) priced into each offense
        inj = [i for i in g.get("injuries", []) if i["team"] in (g["home"], g["away"])]
        gone = lambda team: {i["name"] for i in inj if i["team"] == team and (i["status"] or "").lower() in ("out", "doubtful")}
        absent = {s_: gnba.absent_tonight("nba", G, g[s_], cut, gone(g[s_])) for s_ in ("home", "away")}
        H, A, det = gnba.sides_with_availability(R, G, g, cut, absent)
        # preseason prior: last season's strength moved with the players (fades as this season's games pile up)
        H, A, prior = gnba.with_prior(H, A, R, gnba.prior_context("nba", y) if gnba.PRIOR_K else None, g["home"], g["away"],
                                      {g[s_]: gnba.latest_roster("nba", G, g[s_], cut) for s_ in ("home", "away")})
        # rotation tonight (also the player layer below): projected minutes, Out/Doubtful removed
        opp_of = {"home": g["away"], "away": g["home"]}
        cut_g = gs_data.cutoff(gs_data.us_day(g["start"]))
        h2h = {s_: {pid: RS.rate_factors(pid, opp_of[s_], cut_g, gres.H2H_COEF) for pid, L in RS.logs.items()
                    if L and L[-1]["team"] == g[s_] and L[-1]["date"] < cut_g} for s_ in ("home", "away")}
        prof[g["id"]] = {s_: gnba.player_profiles("nba", G, g[s_], cut_g, gone(g[s_]), prior_tot=PT, rate_mult=h2h[s_])
                         for s_ in ("home", "away")}
        for s_ in ("home", "away"):                       # research card data for every rotation player
            for p in prof[g["id"]][s_]["players"]:
                p["research"] = RS.export(p["id"], opp_of[s_], cut_g)
        pr_det = None
        if PRt and prf["n_games"] >= 100:
            lu = {s_: {p["id"]: p["min"] for p in prof[g["id"]][s_]["players"]} for s_ in ("home", "away")}
            pm = PRt.margin(prf, lu["home"], lu["away"], g.get("neutral", False))
            model_m = gnba.expected_margin(H, A, R)
            H, A, shift = gnba.with_player_ratings(H, A, R, pm["margin"])
            top = lambda s_: sorted(({"name": p["name"], "min": round(p["min"], 1), "rating": round(PRt.rating(prf, p["id"]), 1)}
                                     for p in prof[g["id"]][s_]["players"]), key=lambda r: -r["min"])[:8]
            pr_det = {"players_margin": round(pm["margin"], 2), "model_margin": round(model_m, 2), "w": gnba.PLAYER_RATING_W,
                      "shift": round(shift, 2), "home_edge": round(pm["h"], 2), "games_fitted": prf["n_games"],
                      "lineups": {"home": top("home"), "away": top("away")}}
        H, A, anchor = gnba.anchor_to_market(H, A, R, g.get("spread"), g.get("total"))   # TEAM_MARKET_W (off unless a logic sets it)
        sides[g["id"]] = {"home": {k: round(v, 4) for k, v in H.items()}, "away": {k: round(v, 4) for k, v in A.items()},
                          "player_ratings": pr_det, "market_anchor": anchor,
                          # what each side's opponent allows (for the research card): per game, rank, by position
                          "opp_allowed": {s_: RS.allowed_summary(opp_of[s_], cut_g) for s_ in ("home", "away")},
                          "prior": None if not prior else {t: {"net_last": round(v["net_last"], 2), "roster_delta": round(v["roster_delta"], 2),
                                                                "shift": round(v["shift"], 2), "arrived": [n for n, _ in v["arrived"][:2]],
                                                                "left": [n for n, _ in v["left"][:2]]} for t, v in prior.items()},
                          "games": [R["teams"].get(g["home"], {}).get("games", 0), R["teams"].get(g["away"], {}).get("games", 0)],
                          "availability": {s_: {"points": round(det[s_]["points"], 2), "rows": det[s_]["rows"][:6]} for s_ in ("home", "away")},
                          # dates this season each player out tonight played for the team (the with/without split on the pick card)
                          "out_played": {s_: {r_["name"]: sorted({e["date"][:10] for e in RS.logs.get(r_.get("id"), [])
                                                                  if e["date"] < cut_g and e["team"] == g[s_] and gnba.season_of(e["date"][:10]) == y})
                                              for r_ in det[s_]["rows"] if r_.get("out_tonight")} for s_ in ("home", "away")},
                          "no_availability": {"home": {k: round(v, 4) for k, v in gnba.side(R, g["home"], g["away"], True).items()},
                                              "away": {k: round(v, 4) for k, v in gnba.side(R, g["away"], g["home"], False).items()}}}
    for g in nba_games:                                   # player layer: rotation, per-minute rates, injury report
        inj = [i for i in g.get("injuries", []) if i["team"] in (g["home"], g["away"])]
        pl = {}
        for side in ("home", "away"):
            pr = prof[g["id"]][side]
            pr["players"] = [{k: round(v, 4) if isinstance(v, float) else v for k, v in p.items()} for p in pr["players"]]
            pr["ast_rate"] = round(pr["ast_rate"], 4)
            pl[side] = pr
        pl["injuries"] = inj
        pl["lines"] = gnba.dk_player_lines("nba", g["id"], g["start"])       # DraftKings player lines, once posted
        pl["lines_pulled"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        sides[g["id"]]["players"] = pl
    return {"R": {"pace": R["league"]["pace"], "sd_pace": R["sd_pace"], "sd_p2": R["sd_p2"], "sd_p3": R["sd_p3"], "dur_scale": R["dur_scale"],
                  "and1": R["and1"], "home_scale": R["home_scale"], "comeback": R.get("comeback", 0.0), "reb_credit": round(gnba.reb_credit(G, cut), 4), "ppg": R["ppg_target"], "home_margin": R["home_margin"], "n_games": R["n_games"],
                  "avg": {k: round(v, 4) for k, v in gnba.side(R, "_", "_", False).items()},
                  "avg_home": {k: round(v, 4) for k, v in gnba.side(R, "_", "_", True).items()}},
            "sides": sides, "backtest": _bt("nba", lambda: gnba.backtest(G, 48, 24, n=6000)), "backtest_prior": gbt.prior_metrics("nba"),
            "info": gbt.info_weights(_bt_records("nba") + gbt.prior_records("nba")),
            "anchor": gnba.PROP_ANCHOR,
            "players_bt": _bt("nba_players", lambda: {"metrics": gnba.player_backtest("nba", G, cut, prior_tot=PT)}),
            # calibration of the browser player layer on finished games (written by the audit's pl_check.js run)
            "players_cal": _json_or_none(os.path.join(gs_data.CACHE, "bt_nba_players_cal.json")),
            # fair test of the research factors (written by the audit's research_test.py / research_B.py)
            "research_test": _json_or_none(os.path.join(gs_data.CACHE, "bt_nba_research.json"))}


def engines(data: dict) -> dict:
    """Fitted NFL play-by-play, NBA possession and NHL event engines plus per-game inputs and backtests."""
    from gamesim import backtest as gbt, nfl_pbp, nhl as gnhl, players as gpl
    today = us_today()
    out = {}
    # ---- NFL play by play
    sched = gs_data.schedule()
    nfl_games = next(lg for lg in data["leagues"] if lg["key"] == "nfl")["games"]
    rows = {r["espn"]: r for r in sched if r["espn"]}
    first = min((rows[g["id"]]["gameday"] for g in nfl_games if g["id"] in rows), default=None)
    if first:
        season = int(rows[nfl_games[0]["id"]]["season"])
        P, P0 = gs_data.pbp(season), gs_data.pbp(season - 1)
        wind = {g["game_id"]: (0.0 if g["roof"] in ("dome", "closed") else gs_data.f(g["wind"], 0.0) or 0.0) for g in sched if g["season"] in (str(season), str(season - 1))}
        B = nfl_pbp.build(P, P0, sched, first, wind=wind)
        M, pr = B["M"], B["ratings"]
        pools = M["pools"]
        cm = {"b_call": [round(x, 5) for x in M["b_call"]], "W4": np.round(M["W4"], 5).tolist(), "Wp": np.round(M["Wp"], 5).tolist(),
              "run": {str(k[1]): _sub(v, 1500, 3 if k[1] >= 100 else None) for k, v in pools.items() if k[0] == "run"},
              "comp": {str(k[1]): _sub(v, 1500, 3 if k[1] >= 100 else None) for k, v in pools.items() if k[0] == "comp"},
              "sack": _sub(pools[("sack", 0)], 800), "sack_deep": _sub(nfl_pbp.sack_deep(pools), 400), "int_air": _sub(pools[("int_air", 0)], 600), "int_ret": _sub(pools[("int_ret", 0)], 600),
              "run_off": {str(k): _sub(v, 1200) for k, v in M["run_off"].items()}, "punt": {str(k): _sub(v, 600) for k, v in M["punt"].items()},
              "kick": _sub(M["kick"], 1500), "fum_run": M["fum_run"], "fum_comp": M["fum_comp"], "xp": M["xp"], "two": M["two"],
              "onside": M["onside_rate"], "fg": [float(x) for x in M["fg_beta"]], "yard_sd": M["yard_sd"], "hfa": M["hfa"],
              "home_margin_target": M["home_margin_target"],
              "pen": {"p": M["pen"]["p"], "p_off": M["pen"]["p_off"], "def_first": M["pen"]["def_first"],
                      "off_yds": _sub(M["pen"]["off_yds"], 400), "def_yds": _sub(M["pen"]["def_yds"], 400)},
              "n_plays": M["n_plays"], "n_fourth": M["n_fourth"]}
        games = {}
        for g in nfl_games:
            r = rows.get(g["id"])
            if not r:
                continue
            opts = {}
            for side, team, opp in (("home", r["home_team"], r["away_team"]), ("away", r["away_team"], r["home_team"])):
                q = gpl.starting_qb(season, team)
                opts[side] = []
                for i, name in enumerate(q["depth"][:3]):
                    gs = gpl.gsis_for(season, team, name)
                    si = nfl_pbp.side_inputs(pr, team, opp, gs, M)
                    opts[side].append({"name": name, "projected": i == 0, **{k: round(v, 4) if isinstance(v, float) else v for k, v in si.items()}})
            games[g["id"]] = {"qb": opts, "starter_source": f"ESPN depth chart via nflverse, snapshot {gs_data.depth_chart(season, r['home_team'])[0]}"}
        out["nfl"] = {"M": cm, "games": games,
                      "backtest": _bt("pbp", lambda: gbt.run_pbp(sched, P, P0, str(season), list(range(4, int(rows[nfl_games[0]["id"]]["week"]))), n=10000)),
                      "backtest_prior": gbt.prior_metrics("pbp"), "info": gbt.info_weights(_bt_records("pbp") + gbt.prior_records("pbp"))}
    # ---- NBA possessions
    nba_games = next(lg for lg in data["leagues"] if lg["key"] == "nba")["games"]
    from gamesim import nba as gnba_
    from .nba_pp import SIM_KNOBS, current_sim
    saved = {k: getattr(gnba_, a) for k, a in SIM_KNOBS.items()}
    for k, v in current_sim().items():           # the page runs the published logic's simulation settings
        setattr(gnba_, SIM_KNOBS[k], v)
    try:
        out["nba"] = nba_engine(nba_games, today)
    finally:
        for k, v in saved.items():
            setattr(gnba_, SIM_KNOBS[k], v)
    y = today.year if today.month >= 9 else today.year - 1
    yday = (today - dt.timedelta(days=1)).strftime("%Y%m%d")
    # the "most likely game" backtest (written by the audit's likely_bt.py): accuracy of the most common simulated score
    out["likely_bt"] = {k: (_json_or_none(os.path.join(gs_data.CACHE, f"bt_likely_{k}.json")) or {}).get("summary") for k in ("nba", "nhl", "nfl")}
    # ---- NHL event clock
    nhl_games = next(lg for lg in data["leagues"] if lg["key"] == "nhl")["games"]
    G = gnhl.season_games(f"{y}1005", yday)
    en = gnhl.empty_net_rates(f"{y}1005", yday, max_games=120)
    R = gnhl.calibrate(gnhl.ratings(G, gs_data.now_cutoff()), en)
    sides = {}
    for g in nhl_games:
        gh, ga = R["starters"].get(g["home"], {}), R["starters"].get(g["away"], {})
        sides[g["id"]] = {"home": {k: round(v, 5) for k, v in gnhl.side(R, g["home"], g["away"], True, ga.get("id")).items()},
                          "away": {k: round(v, 5) for k, v in gnhl.side(R, g["away"], g["home"], False, gh.get("id")).items()},
                          "home_lg_goalie": {k: round(v, 5) for k, v in gnhl.side(R, g["home"], g["away"], True).items()},
                          "away_lg_goalie": {k: round(v, 5) for k, v in gnhl.side(R, g["away"], g["home"], False).items()},
                          "goalies": {"home": gh.get("name"), "away": ga.get("name"),
                                      "home_sv": R["goalies"].get(gh.get("id"), {}).get("sv"), "away_sv": R["goalies"].get(ga.get("id"), {}).get("sv")}}
    out["nhl"] = {"R": {"goal_scale": R["goal_scale"], "home_mult": R["home_mult"], "sd_fin": R["sd_fin"], "shg_per_pp": R["league"]["shg_per_pp"],
                        "ot_decided": R["league"]["ot_decided"], "so_home": R["league"]["so_home"], "gpg": R["gpg"], "sv": R["league"]["sv"],
                        "home_prior": R["home_prior"], "lam": R["lam"], "n_games": R["n_games"],
                        "avg": {k: round(v, 5) for k, v in gnhl.side(R, "_", "_", False).items()}},
                  "en": en, "sides": sides, "backtest": _bt("nhl", lambda: gnhl.backtest(G, en, n=6000)), "backtest_prior": gbt.prior_metrics("nhl"),
                  "info": gbt.info_weights(_bt_records("nhl") + gbt.prior_records("nhl"))}
    return out
