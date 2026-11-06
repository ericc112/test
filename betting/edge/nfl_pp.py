"""PrizePicks NFL board, priced by the NFL simulator anchored on DraftKings' lines.

The NFL backtest (README, weeks 3-8, 5,354 DraftKings closing props) says DraftKings' line is the better centre and
the simulation the better shape: alone the simulation shows no edge over the line, but re-centred on the DraftKings
line it prices lines 10-20 yards away well (Brier 0.196, buckets within ~5 pts). A PrizePicks line that differs from
DraftKings' is exactly that case. So each PrizePicks leg gets:

  market   P(side) from the simulated distribution re-centred on DraftKings' line for the same player and stat
           (nfl.anchored_over). The feed has no prices, so DraftKings' line counts as a 50/50 median.
  model    the simulation's own P(side) at the PrizePicks line, shrunk toward 50% by MODEL_SHRINK.
  history  this season's over/under count at the PrizePicks line.

blended by blend.final_probability (same gates and learned corrections as `edge prob`). A leg with no DraftKings line
for that player and stat has no market component and is held at Low: the simulation alone has no edge on a line.
Role flags (back from injury, under 3 games with the team, line far from the model) also hold a leg at Low.
"""
from __future__ import annotations

import collections
import datetime as dt

import numpy as np

from . import nfl

STATS = {"Pass Yards": "pass_yds", "Pass Attempts": "pass_att", "Pass Completions": "completions", "Pass TDs": "pass_td",
         "INT": "pass_int", "Rush Yards": "rush_yds", "Rush Attempts": "rush_att", "Receiving Yards": "rec_yds",
         "Receptions": "receptions", "Rush+Rec Yds": "rush_rec_yds"}
LABEL = {v: k.lower() for k, v in STATS.items()}
ESPN = {"JAC": "JAX", "LA": "LAR", "WAS": "WSH", "LAR": "LAR"}           # PrizePicks abbreviation -> ESPN
BREAK_EVEN = {"standard": 0.577}                                          # 2-pick power; goblin/demon multipliers unknown


DABBLE_STATS = {"rec_yds": ("receiving-yards",), "rush_yds": ("rushing-yards",), "rush_rec_yds": ("receiving-yards", "rushing-yards"),
                "receptions": ("receptions",), "rush_att": ("rushing-attempts",), "pass_yds": ("passing-yards",), "pass_att": ("passing-attempts",),
                "completions": ("passing-completions",), "pass_td": ("passing-touchdowns",), "pass_int": ("interceptions",)}
COUNT_MARKETS = {"receptions", "rush_att", "completions", "pass_att", "pass_td", "pass_int"}
JUICED = {"pass_td", "pass_int"}


def anchored_count(arr: np.ndarray, dk_line: float, line: float) -> float:
    """P(over `line`) for a count stat, from the simulated distribution tilted (exponentially) so that DraftKings'
    line is its median: P(X > dk_line) = 1/2. Unlike a half-unit shift this keeps the integer support, so a push at a
    whole-number PrizePicks line stays a push (Burrow over 2.0 pass TDs wins on 3+, pushes on 2)."""
    k, c = np.unique(np.round(arr).astype(int), return_counts=True)
    pk = c / c.sum()
    z = (k - k.mean()) / max(k.std(), 1e-9)

    def tilt(theta):
        w = pk * np.exp(theta * z)
        return w / w.sum()
    lo, hi = -8.0, 8.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if tilt(mid)[k > dk_line].sum() < 0.5:
            lo = mid
        else:
            hi = mid
    w = tilt((lo + hi) / 2)
    over = float(w[k > line].sum())
    push = float(w[k == line].sum()) if float(line).is_integer() else 0.0
    return over / max(1 - push, 1e-9)


def espn_abbr(a: str | None) -> str:
    return ESPN.get((a or "").upper(), (a or "").upper())


def match_events(props: list[dict], season: int, week: int) -> dict:
    """PrizePicks game (away, home) -> ESPN event for this week."""
    evs = nfl.week_events(season, week)
    by_teams = {}
    for e in evs:
        by_teams[(e["away_abbr"], e["home_abbr"])] = e
    out = {}
    for p in props:
        k = (espn_abbr(p.get("away")), espn_abbr(p.get("home")))
        if k in by_teams:
            out[(p.get("away"), p.get("home"))] = by_teams[k]
    return out


def price_leg(res: dict, name: str, market: str, line: float, over_only: bool = False, side: str | None = None) -> dict | None:
    """One PrizePicks line priced from a priced game (nfl.price_game). `side` forces a side (verify); otherwise the
    better side is chosen. None when the player or stat isn't in the simulation."""
    from .blend import final_probability
    from .nba_pp import find_player
    sim = res["sim"]
    plist = [{"name": p.get("name", ""), "id": pid} for pid, p in sim["players"].items() if market in p]
    hit = find_player(name, plist) if plist else None
    if not hit:
        return None
    pid = hit["id"]
    p = sim["players"][pid]
    arr = p[market]
    dk = next((r for r in res["rows"] if str(r["player_id"]) == str(pid) and r["market"] == market), None)
    dk_line = dk["line"] if dk else None
    so, su, push = nfl.side_probs(arr, line)
    dab = None
    if dk_line is None and market in DABBLE_STATS:   # no DraftKings line: Dabble's line and price (user, 2026-11-06)
        from . import shop
        dab = shop.dabble_market("NFL", name, DABBLE_STATS[market], line)
    if dk_line is None and dab and dab.get("q") is not None:
        if abs(dab["line"] - line) < 1e-9:
            a_over = dab["q"]
        else:                                        # carried along the simulated shape, anchored at Dabble's line
            base = anchored_count(arr, dab["line"], line) if market in COUNT_MARKETS else nfl.anchored_over(arr, dab["line"], line)
            lg = lambda x: float(np.log(np.clip(x, 1e-4, 1 - 1e-4) / (1 - np.clip(x, 1e-4, 1 - 1e-4))))
            a_over = float(1 / (1 + np.exp(-(lg(base) + lg(dab["q"])))))     # shift by Dabble's lean off 50/50 at its line
    elif dk_line is None:
        a_over = None
    elif abs(dk_line - line) < 1e-9:
        a_over = 0.5            # PrizePicks posts DraftKings' line: with no prices in the feed the market says 50/50
    elif market in COUNT_MARKETS:
        a_over = anchored_count(arr, dk_line, line)
    else:
        a_over = nfl.anchored_over(arr, dk_line, line)
    ho, hu = nfl.player_history(pid, p["team"], res["history"], market, line)
    med, mu = float(np.median(arr)), float(np.mean(arr))
    flags = nfl.role_flags(p, market, line, med, mu)
    best = None
    for sd in (["over"] if over_only else ["over", "under"]):
        if side and sd != side:
            continue
        pm = nfl.calibrated((so if sd == "over" else su) / max(1 - push, 1e-9), market)
        pk = None if a_over is None else (a_over if sd == "over" else 1 - a_over)
        dec = ho + hu
        ph = (ho if sd == "over" else hu) / dec if dec else None
        e = final_probability(pm, pk, ph, f"nfl:{market}:{sd}", dec)
        conf = e.confidence
        why = []
        if pk is None and conf in ("High", "Medium"):
            conf, why = "Low", ["no DraftKings or Dabble line for this player and stat: the simulation alone has no edge on a line"]
        if flags and conf in ("High", "Medium"):
            conf = "Low"
        if market in JUICED and conf in ("High", "Medium"):
            conf, why = "Low", why + ["TD and interception lines are often heavily juiced and the feed has no prices: DraftKings' line isn't a 50/50 median here"]
        if best is None or e.p > best["p_final"]:
            best = {"side": sd, "p_model": round(pm, 4), "p_market": None if pk is None else round(pk, 4),
                    "p_hist": None if ph is None else round(ph, 4), "hist_n": dec, "p_final": e.p, "confidence": conf, "why": why}
    vol_key = {"rec_yds": "targets", "receptions": "targets", "rush_yds": "rush_att", "rush_att": "rush_att",
               "rush_rec_yds": "rush_att"}.get(market, "pass_att")
    vol = p.get(vol_key)
    return {"player_id": str(pid), "sim_name": p.get("name"), "team_espn": sim["teams"][p["team"]]["abbr"], "dk_line": dk_line, "dabble": dab,
            "median": med, "mean": mu, "q25": float(np.percentile(arr, 25)), "q75": float(np.percentile(arr, 75)),
            "volume": (vol_key, float(np.mean(vol))) if vol is not None else None, "flags": flags,
            "hist": (ho, hu), **best}


def verdict(r: dict) -> str:
    be = BREAK_EVEN.get(r.get("odds_type"))
    if be is None:
        return "PASS (payout multiplier unknown for this line type)"
    if r["confidence"] == "High" and r["p_final"] >= 0.65 and r["p_final"] >= be + 0.02:
        return f"ENTRY LEG (High, {r['p_final']:.0%} vs break-even {be:.1%})"
    if r["confidence"] in ("High", "Medium"):
        return "LEAN (Medium: show, don't enter)" if r["confidence"] == "Medium" else "LEAN (High but under 65%)"
    return "PASS (below the gate)"


def price_board(props: list[dict], n: int = 50000, season: int = 2026, week: int | None = None, log=print,
                store: dict | None = None) -> list[dict]:
    """Price every supported standard PrizePicks NFL line, one simulation per game. `store` collects each game's
    priced simulation (event id -> nfl.price_game result) for the history and most-likely-game lists."""
    props = [p for p in props if p["stat"] in STATS and p.get("odds_type") == "standard"]
    if week is None:
        week = current_week(season)
    games = match_events(props, season, week)
    rows = []
    for key, ev in sorted(games.items(), key=lambda kv: kv[1]["date"]):
        mine = [p for p in props if (p.get("away"), p.get("home")) == key]
        log(f"  {ev['away_abbr']} @ {ev['home_abbr']}: {len(mine)} lines, simulating...")
        try:
            res = nfl.price_game(ev["id"], n=n, season=season)
        except Exception as e:                          # one game's feed failing never sinks the board
            rows += [{**p, "error": f"{type(e).__name__}: {e}"[:120]} for p in mine]
            continue
        if store is not None:
            store[ev["id"]] = res
        for p in mine:
            m = STATS[p["stat"]]
            x = price_leg(res, p["player"], m, p["line"], p.get("over_only", False))
            if not x:
                rows.append({**p, "error": "player or stat not in the simulation"})
                continue
            opp = ev["home_abbr"] if x["team_espn"] == ev["away_abbr"] else ev["away_abbr"]
            gap = None if x["dk_line"] is None else p["line"] - x["dk_line"]
            note = (f"nfl sim median {x['median']:.1f} (25-75th {x['q25']:.0f}-{x['q75']:.0f})"
                    + (f", {x['volume'][0]} {x['volume'][1]:.1f}" if x["volume"] else "")
                    + (f"; DraftKings line {x['dk_line']} (PrizePicks {gap:+g})" if x["dk_line"] is not None else
                       f"; no DraftKings line; Dabble {x['dabble']['line']:g} at {x['dabble']['over']}/{x['dabble']['under']} (no-vig over {x['dabble']['q']:.0%})"
                       if x.get("dabble") else "; no DraftKings or Dabble line")
                    + (f"; flags: {', '.join(x['flags'])}" if x["flags"] else "") + (f"; {x['why'][0]}" if x["why"] else "")
                    + f"; history {x['hist'][0]} over / {x['hist'][1]} under; pulled {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%MZ}")
            rows.append({**p, **x, "event_id": ev["id"], "team": x["team_espn"], "opp": opp, "market_key": m, "sport": "nfl",
                         "research": research(res, x["player_id"], m, p["line"], opp),
                         "script": f"nfl:{ev['id']}", "game": f"{ev['away_abbr']} @ {ev['home_abbr']}", "start": ev["date"],
                         "proj": x["median"], "opp_proj": None if not x["volume"] else round(x["volume"][1], 1), "notes": note,
                         "gap": gap, "newcomer": bool(x["flags"])})
    return rows


def current_week(season: int) -> int:
    """The first week with a game that hasn't finished."""
    for wk in range(1, 19):
        evs = nfl.week_events(season, wk)
        if any(e["status"] != "STATUS_FINAL" for e in evs):
            return wk
    return 18


def pick_order(rows: list[dict], top: int = 5, per_game: int = 1) -> list[dict]:
    """Best legs by probability, High before Medium, at most `per_game` legs per game (one, unless the day has
    fewer games than picks: see days())."""
    rank = {"High": 0, "Medium": 1, "Low": 2}
    ok = sorted([r for r in rows if "error" not in r], key=lambda r: (rank.get(r["confidence"], 3), -r["p_final"]))
    seen, out = collections.Counter(), []
    for r in ok:
        if seen[r["script"]] >= per_game or any(o["player"] == r["player"] for o in out if o["script"] == r["script"]):
            continue
        seen[r["script"]] += 1
        out.append(r)
        if len(out) == top:
            break
    return out


def write_up(r: dict, verified: str = "", warns: list | None = None) -> str:
    f = lambda v: "-" if v is None else f"{v:.0%}"
    lines = [f"### {r.get('bet_id', '')}{r['player']} ({r['team']}) {r['side'].upper()} {r['line']} {LABEL[r['market_key']]} — {r['game']}",
             f"**{r['p_final']:.1%} {r['confidence']}** · {verdict(r)}" + (f" · back-check: **{verified}**" if verified else ""),
             f"- Sources: DraftKings-anchored {f(r['p_market'])}"
             + (f" (DraftKings line {r['dk_line']}, PrizePicks {r['gap']:+g})" if r["dk_line"] is not None else
                f" (Dabble {r['dabble']['line']:g} at {r['dabble']['over']}/{r['dabble']['under']}; no DraftKings line)" if r.get("dabble") else " (no DraftKings or Dabble line)")
             + f" · simulation {f(r['p_model'])} (shrunk) · this season {r['hist'][0]} over / {r['hist'][1]} under",
             f"- Simulation: median {r['median']:.1f}, 25–75th {r['q25']:.0f}–{r['q75']:.0f}"
             + (f", {r['volume'][1]:.1f} {r['volume'][0].replace('_', ' ')}" if r["volume"] else "")]
    if r.get("ml"):
        sc = ", ".join(f"{k} {v}" for k, v in r["ml"]["score"].items())
        lines.insert(2, f"- Most likely game ({sc}): {r['ml']['value']:.0f} {LABEL[r['market_key']]} ({r['ml']['gap']:+.0f} vs the line)")
    if r["flags"]:
        lines.append("- Role flags: " + "; ".join(r["flags"]))
    if r.get("reasons"):
        mark = {"supports": "✓", "neutral": "–", "against": "✗"}
        lines.append("- Reasons:" if r.get("ml") else "- Context check (shown, not used to drop the leg):")
        lines += [f"  - {mark[x['verdict']]} {x['name']}: {x['text']}" for x in r["reasons"]]
    if warns:
        lines.append("- Back-check warnings: " + "; ".join(warns))
    return "\n".join(lines)


# ------------------------------------------------------------------ research, history list, most likely game
VOLUME = {"rec_yds": ("tgt", "targets"), "receptions": ("tgt", "targets"), "rush_yds": ("car", "rush_att"),
          "rush_att": ("car", "rush_att"), "rush_rec_yds": ("touches", None), "pass_yds": ("pass_att", None),
          "pass_att": ("pass_att", None), "completions": ("pass_att", None), "pass_td": ("pass_att", None), "pass_int": ("pass_att", None)}
FAMILY = {"rec_yds": "rec_yds", "receptions": "receptions", "rush_yds": "rush_yds", "rush_att": "rush_att", "rush_rec_yds": "rush_rec_yds",
          "pass_yds": "pass_yds", "pass_att": "pass_att", "completions": "completions", "pass_td": "pass_td", "pass_int": "pass_int"}


def research(res: dict, pid: str, market: str, line: float, opp: str) -> dict:
    """His games this season at this stat (value, opponent, volume), last 3, meetings with tonight's opponent."""
    log = []
    for g in sorted(res["history"], key=lambda g: g["date"]):
        for tid, ps in g["players"].items():
            p = ps.get(str(pid))
            if not p:
                continue
            v = nfl.stat_value(p, market)
            if v is None:
                continue
            o = next((g["abbr"][t] for t in g["abbr"] if t != tid), "")
            vk = VOLUME[market][0]
            vol = p.get("car", 0.0) + p.get("tgt", 0.0) if vk == "touches" else p.get(vk, 0.0)
            log.append({"date": g["date"][:10], "opp": o, "value": float(v), "vol": float(vol)})
    cnt = lambda L: [sum(x["value"] > line for x in L), sum(x["value"] < line for x in L), len(L)]
    h2h = [x for x in log if x["opp"] == opp]
    avg = lambda L: float(np.mean([x["value"] for x in L])) if L else None
    return {"season": cnt(log), "last3": cnt(log[-3:]), "h2h": cnt(h2h), "season_avg": avg(log), "last3_avg": avg(log[-3:]),
            "h2h_avg": avg(h2h), "last_games": [x["value"] for x in log[-3:]], "vol_avg": float(np.mean([x["vol"] for x in log])) if log else None}


def allowed(res: dict, team: str, market: str) -> dict | None:
    """What `team` (ESPN abbreviation) allowed per game this season in this stat's family (every opposing player
    summed), its rank of 32 (1 = allows the most) and the league average per team-game."""
    fam = FAMILY[market]
    per = {}
    for g in res["history"]:
        for tid in g["abbr"]:
            other = next((t for t in g["abbr"] if t != tid), None)
            if other is None or other not in g["players"]:
                continue
            tot = sum((nfl.stat_value(p, fam) or 0.0) for p in g["players"][other].values())
            per.setdefault(g["abbr"][tid], []).append(tot)
    if team not in per:
        return None
    avg = {t: float(np.mean(v)) for t, v in per.items() if v}
    ranked = sorted(avg.values(), reverse=True)
    league = float(np.mean([x for v in per.values() for x in v]))
    return {"per_game": avg[team], "rank": ranked.index(avg[team]) + 1, "teams": len(ranked), "league": league, "games": len(per[team])}


def history_order(rows: list[dict], store: dict, top: int = 5, min_games: int = 4, per_game: int = 1) -> list[dict]:
    """The hit-rate method, for comparison (LESSONS L27: no information beyond the price in the NBA test): the side each
    line cleared more often this season (4+ games), ranked by that rate, then the last 3, then sample size; one leg
    per game. Each leg carries what the simulation and DraftKings say about that same side."""
    cand = []
    for r in rows:
        if "error" in r or not r.get("research"):
            continue
        o, u, n = r["research"]["season"]
        if n < min_games or o == u:
            continue
        side = "over" if o > u else "under"
        if side == "under" and r.get("over_only"):
            continue
        k = 0 if side == "over" else 1
        rate = lambda t: t[k] / t[2] if t[2] else 0.0
        x = r if side == r["side"] else {**r, **price_leg(store[r["event_id"]], r["player"], r["market_key"], r["line"], side=side)}
        cand.append({**x, "method": "history", "hist_rank": (rate(r["research"]["season"]), rate(r["research"]["last3"]), n)})
    cand.sort(key=lambda r: tuple(-v for v in r["hist_rank"]))
    seen, out = collections.Counter(), []
    for r in cand:
        if seen[r["script"]] >= per_game or any(o["player"] == r["player"] for o in out if o["script"] == r["script"]):
            continue
        seen[r["script"]] += 1
        out.append(r)
        if len(out) == top:
            break
    return out


def most_likely_run(res: dict) -> dict:
    """The game the broadcast plays: the most common final score of the runs, then, among runs with that score, the
    one closest to every player's simulated median (his main stat, in standard deviations)."""
    sim = res["sim"]
    tids = list(sim["teams"])
    a, b = sim["teams"][tids[0]]["points"].astype(int), sim["teams"][tids[1]]["points"].astype(int)
    pairs, counts = np.unique(np.stack([a, b], 1), axis=0, return_counts=True)
    top = pairs[np.argmax(counts)]
    idx = np.where((a == top[0]) & (b == top[1]))[0]
    z = np.zeros(len(idx))
    for p in sim["players"].values():
        for m in ("pass_yds", "rush_yds", "rec_yds"):
            v = p.get(m)
            if v is None or float(np.std(v)) < 1e-9 or float(np.median(v)) < 5:
                continue
            z += ((v[idx] - np.median(v)) / np.std(v)) ** 2
    run = int(idx[int(np.argmin(z))])
    return {"run": run, "score": {sim["teams"][t]["abbr"]: int(sim["teams"][t]["points"][run]) for t in tids}, "share": float(counts.max() / len(a))}


def likely_order(rows: list[dict], store: dict, top: int = 5, drop: list | None = None, per_game: int = 1) -> list[dict]:
    """The most-likely-game list: a line is kept when the player's line in the game's most likely simulated run, the
    simulation's median and this season's record agree on the side, and every reason shown supports that side or
    is neutral (any reason against it drops the leg, recorded in `drop`). Ranked High before Medium, then by
    probability; one leg per game."""
    runs = {e: most_likely_run(res) for e, res in store.items()}
    cand = []
    for r in rows:
        if "error" in r or r["event_id"] not in runs or not r.get("research"):
            continue
        res, L = store[r["event_id"]], runs[r["event_id"]]
        p = res["sim"]["players"].get(str(r["player_id"]))
        if not p or r["market_key"] not in p:
            continue
        val = float(p[r["market_key"]][L["run"]])
        gap = val - r["line"]
        if gap == 0:
            continue
        side = "over" if gap > 0 else "under"
        if side == "under" and r.get("over_only"):
            continue
        if (r["median"] - r["line"]) * gap <= 0:              # the run disagrees with the median: a one-run fluke
            continue
        o, u, n = r["research"]["season"]
        if n < 3 or (o if side == "over" else u) < (u if side == "over" else o):
            continue
        x = r if side == r["side"] else {**r, **price_leg(res, r["player"], r["market_key"], r["line"], side=side)}
        box = {k: float(p[k][L["run"]]) for k in ("pass_yds", "rush_att", "rush_yds", "targets", "receptions", "rec_yds") if k in p}
        cand.append({**x, "method": "likely", "ml": {"score": L["score"], "share": L["share"], "value": val, "gap": gap, "box": box}})
    rank = {"High": 0, "Medium": 1, "Low": 2}
    cand.sort(key=lambda r: (rank.get(r["confidence"], 3), -r["p_final"]))
    seen, out = collections.Counter(), []
    for r in cand:
        if seen[r["script"]] >= per_game or any(o["player"] == r["player"] for o in out if o["script"] == r["script"]):
            continue
        r["reasons"] = reasons(r, store[r["event_id"]])
        against = [x["name"] for x in r["reasons"] if x["verdict"] == "against"]
        if against:
            if drop is not None:
                drop.append({"player": r["player"], "side": r["side"], "line": r["line"], "stat": LABEL[r["market_key"]],
                             "p": round(r["p_final"], 3), "against": against})
            continue
        seen[r["script"]] += 1
        out.append(r)
        if len(out) == top:
            break
    return out


def days(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    """The board split by kickoff day (US Eastern): Thursday, Sunday, Monday. Each day gets its own lists."""
    from zoneinfo import ZoneInfo
    by = collections.defaultdict(list)
    for r in rows:
        if "error" in r or not r.get("start"):
            continue
        t = dt.datetime.fromisoformat(r["start"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
        by[t.strftime("%Y-%m-%d")].append(r)
    out = []
    for d in sorted(by):
        label = dt.date.fromisoformat(d).strftime("%a %b %-d")
        out.append((label, by[d]))
    return out


def per_game_cap(rows: list[dict], top: int) -> int:
    """One leg per game, unless the day has fewer games than picks (Thursday, Monday): then up to 3 per game, each
    flagged as the same game script (never two in one entry)."""
    g = len({r["script"] for r in rows})
    return 1 if g >= top else min(3, -(-top // max(g, 1)))


def _lean(x, ref, band):
    if x is None or not ref:
        return 0
    q = x / ref - 1
    return 1 if q > band else -1 if q < -band else 0


def reasons(r: dict, res: dict) -> list[dict]:
    """Every reason shown for a pick, judged against its side: supports, neutral or against. A reason built from
    several numbers (count and average) is against when any of them points the other way."""
    over = r["side"] == "over"
    sgn = 1 if over else -1
    rs = r.get("research") or {}
    vd = lambda lean: "neutral" if lean == 0 else "supports" if lean == sgn else "against"
    cmp = lambda a, b: (a > b) - (a < b)
    comb = lambda *v: "against" if "against" in v else "supports" if "supports" in v else "neutral"
    out = []
    add = lambda name, verdict, text: out.append({"name": name, "verdict": verdict, "text": text})
    ml = r.get("ml")
    if ml:
        sc = ", ".join(f"{k} {v}" for k, v in ml["score"].items())
        add("most likely game", vd(cmp(ml["value"], r["line"])), f"{ml['value']:.0f} in the most likely game ({sc}) vs a {r['line']} line")
    add("simulation median", vd(cmp(r["median"], r["line"])), f"median {r['median']:.1f} (25-75th {r['q25']:.0f}-{r['q75']:.0f})")
    pk = r.get("p_market")
    if pk is None:
        add("DraftKings", "neutral", "no DraftKings or Dabble line for this player and stat")
    elif r.get("dk_line") is None and r.get("dabble"):
        add("Dabble", "supports" if pk >= 0.52 else "against" if pk <= 0.48 else "neutral",
            f"{pk:.0%} for this side from Dabble's {r['dabble']['line']:g} at {r['dabble']['over']}/{r['dabble']['under']} (no DraftKings line)")
    elif r.get("dk_line") is not None and abs(r["dk_line"] - r["line"]) < 1e-9:
        add("DraftKings", "neutral", f"DraftKings posts the same line ({r['dk_line']}): no prices in the feed, so 50/50")
    else:
        add("DraftKings", "supports" if pk >= 0.52 else "against" if pk <= 0.48 else "neutral",
            f"{pk:.0%} for this side from DraftKings' line {r['dk_line']} (PrizePicks {r['line']})")
    o, u, n = rs.get("season", [0, 0, 0]); avg = rs.get("season_avg")
    add("this season", comb(vd(cmp(o, u)), vd(cmp(avg, r["line"])) if avg is not None else "neutral"),
        f"{o} over / {u} under in {n}" + (f", average {avg:.1f}" if avg is not None else ""))
    lo, lu, ln = rs.get("last3", [0, 0, 0]); la = rs.get("last3_avg")
    add("last 3", comb(vd(cmp(lo, lu)), vd(cmp(la, r["line"])) if la is not None else "neutral"),
        f"{lo} over / {lu} under" + (f" ({', '.join(str(int(v)) for v in rs.get('last_games', []))})" if rs.get("last_games") else ""))
    h = rs.get("h2h", [0, 0, 0])
    if h[2]:
        add("head-to-head", comb(vd(cmp(h[0], h[1])), vd(cmp(rs.get("h2h_avg"), r["line"]))),
            f"{h[0]} over / {h[1]} under vs {r['opp']} this season (average {rs['h2h_avg']:.1f})")
    else:
        add("head-to-head", "neutral", f"no meeting with {r['opp']} this season")
    a = allowed(res, r["opp"], r["market_key"])
    if a and a["games"] >= 3:
        lp = _lean(a["per_game"], a["league"], 0.03)
        word = "more than" if lp > 0 else "less than" if lp < 0 else "about"
        add("matchup", vd(lp), f"{r['opp']} allows {a['per_game']:.1f} {LABEL[r['market_key']]} a game to all opposing players, {word} the league's "
            f"{a['league']:.1f} (rank {a['rank']}/{a['teams']}, 1 = allows the most)")
    else:
        add("matchup", "neutral", "not enough games for the opponent")
    vol, va = r.get("volume"), rs.get("vol_avg")
    vk = VOLUME[r["market_key"]]
    pv = None
    if vk[0] == "touches":
        p = res["sim"]["players"].get(str(r["player_id"])) or {}
        if "rush_att" in p and "targets" in p:
            pv = float(np.mean(p["rush_att"]) + np.mean(p["targets"]))
    elif vol:
        pv = vol[1]
    outs = [x["name"] for t, L in (res["target"].get("out") or {}).items() if t != next((k for k in res["target"]["abbr"] if res["target"]["abbr"][k] == r["opp"]), None)
            for x in L if (x.get("status") or "").lower() in ("out", "doubtful")]
    if pv is not None and va:
        lv = _lean(pv, va, 0.05)
        name = {"tgt": "targets", "car": "carries", "touches": "touches", "pass_att": "pass attempts"}[vk[0]]
        add("usage", vd(lv), f"projected {pv:.1f} {name} vs {va:.1f} a game this season" + (f"; out for his team: {', '.join(outs[:4])}" if outs else ""))
    else:
        add("usage", "neutral", "no volume history")
    if r.get("flags"):
        add("role", "against", "; ".join(r["flags"]))
    return out


def gap_rows(ok: list[dict]) -> list[dict]:
    """PrizePicks lines that differ from DraftKings', biggest gaps first."""
    gaps = sorted([r for r in ok if r.get("gap")], key=lambda r: -abs(r["gap"]))
    return [{"player": r["player"], "stat": LABEL[r["market_key"]], "pp": r["line"], "dk": r["dk_line"], "side": r["side"],
             "p": round(r["p_final"], 4), "conf": r["confidence"], "game": r["game"]} for r in gaps]
