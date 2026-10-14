"""Back-check a pick before it is published: python -m edge verify ID [ID ...] | --open

A pick is VERIFIED only if every check passes. Any FAIL means it is not published (or is
withdrawn); any WARN must be stated next to the pick. The checks exist because each one caught,
or would have caught, a real mistake on 2026-10-12/13:

  recompute     final probability and label rebuilt from the stored components with today's gates
                (a mistyped model number 0.78 vs 0.728; labels left stale after gates changed)
  recount       history re-fetched from the raw source and recounted at the prop's own unit
                (Cuzz "80% of 40" was 13 of 20 by series: L23)
  reprice       the model re-run on current data and odds (series price moved 72% -> 66%)
  offered       the line and side exist on the app right now (malbsMd U32 was MORE-ONLY)
  rules         lesson rules: L5 new/thin roles, L17 playoff leash, L18 hits-allowed, L21 CS2
                stomps, L22 H+R+RBI unders
  correlation   other open legs on the same game script
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from .blend import final_probability, load_adjustments

TOL_P = 0.005      # recompute must match the logged number
TOL_HIST = 0.05    # recount within 5 pts of the logged history
TOL_MODEL = 0.04   # re-run model within 4 pts, else re-price before publishing


def _f(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


@dataclass
class Report:
    row: dict
    checks: list = field(default_factory=list)   # (status, name, detail): status in PASS / WARN / FAIL

    def add(self, status, name, detail):
        self.checks.append((status, name, detail))

    @property
    def verdict(self) -> str:
        if any(s == "FAIL" for s, _, _ in self.checks):
            return "NOT VERIFIED"
        return "VERIFIED" + (" with warnings" if any(s == "WARN" for s, _, _ in self.checks) else "")

    def text(self) -> str:
        r = self.row
        from .blend import rating
        head = (f"#{r['id']} {r['player']} {r['market']} {r['side']} {r['line']} | {rating(_f(r.get('p_final')), r.get('confidence'), _f(r.get('p_market')))}/10 "
                f"p {r.get('p_final')} {r.get('confidence')} -> {self.verdict}")
        return "\n".join([head] + [f"   {s:4s} {n:11s} {d}" for s, n, d in self.checks])


# ------------------------------------------------------------------ individual checks
def check_recompute(rep: Report, adj: dict):
    r = rep.row
    pm, pk, ph = _f(r.get("p_model")), _f(r.get("p_market")), _f(r.get("p_hist"))
    if pm is None and pk is None and ph is None:
        rep.add("FAIL", "recompute", "no model, market or history stored: nothing to check the number against")
        return
    e = final_probability(pm, pk, ph, r.get("segment", ""), int(_f(r.get("hist_n")) or 0), adj)
    logged, conf = _f(r.get("p_final")), r.get("confidence")
    if (logged is None or abs(e.p - logged) > TOL_P or e.confidence != conf) and getattr(rep, "locked", False):
        rep.add("WARN", "recompute", f"today's weights give {e.p:.3f} {e.confidence}; logged {logged} {conf} (event under way: logged number stands)")
    elif logged is None or abs(e.p - logged) > TOL_P or e.confidence != conf:
        rep.add("FAIL", "recompute", f"components give {e.p:.3f} {e.confidence}; logged {logged} {conf}")
    else:
        rep.add("PASS", "recompute", f"{e.p:.3f} {e.confidence} from model {pm} / market {pk} / hist {ph} (n {r.get('hist_n')})")
    rep.recomputed = e


def check_rules(rep: Report):
    r = rep.row
    sport, mk, side, conf = r.get("sport"), r.get("market"), r.get("side"), r.get("confidence")
    notes = r.get("notes", "")
    strong = conf in ("High", "Medium") or r.get("action") in ("bet", "lean")
    if ("NEW TO TEAM" in notes or "THIN SAMPLE" in notes) and strong:
        rep.add("FAIL", "rule L5", "player new to the team or thin sample: role unconfirmed")
    if sport == "mlb" and mk in ("pitcher_outs", "pitcher_pitches", "pitcher_bf") and side == "over" and r.get("date", "")[5:7] in ("10", "11"):
        rep.add("FAIL", "rule L17", "postseason starter-length over: no playoff leash bets in hit-rate mode")
    if sport == "mlb" and mk == "pitcher_hits_allowed" and side == "under" and conf == "High":
        rep.add("FAIL", "rule L18", "hits-allowed unders are capped at Medium")
    if sport == "mlb" and mk == "batter_hrr" and side == "under" and conf == "High":
        rep.add("FAIL", "rule L22", "H+R+RBI unders are capped at Medium (bullpen damage)")
    m = re.search(r"per-map win (\d+)%", notes)
    if sport == "cs2" and mk == "cs_kills_m12" and side == "under" and m and int(m.group(1)) >= 65 and conf == "High":
        rep.add("FAIL", "rule L21", f"kill under on a {m.group(1)}% per-map favourite: stomps beat it, capped at Medium")
    if not any(n.startswith("rule") for _, n, _ in rep.checks):
        rep.add("PASS", "rules", "no lesson rule blocks this pick")


def check_correlation(rep: Report, rows: list[dict]):
    r = rep.row
    same = [x for x in rows if x is not r and x.get("status") in ("pending", "") and x.get("action") in ("bet", "lean", "user_entry")
            and ((r.get("group") and x.get("group") == r.get("group")) or x.get("event_id") == r.get("event_id"))]
    if same:
        rep.add("WARN", "correlation", "same game script as open legs: " + ", ".join(f"#{x['id']} {x['player']} {x['side']} {x['line']}" for x in same[:6])
                + " -> one leg per script")
    else:
        rep.add("PASS", "correlation", "no other open legs on this game script")


def started(row: dict) -> bool | None:
    """True once the event is under way or over (lines are pulled then, so 'offered' can't be checked)."""
    from .grade import _get
    try:
        if row.get("sport") == "lol":   # LoL matches aren't returned by the id filter: look among upcoming/current
            from . import lol
            m = lol.find_match(int(row["event_id"]))
            return None if m is None else m.get("status") in ("current", "finished")
        if row.get("sport") == "cs2":
            m = _get(f"https://api.bo3.gg/api/v1/matches?filter%5Bmatches.id%5D%5Beq%5D={row['event_id']}")["results"]
            return bool(m) and m[0].get("status") in ("current", "finished")
        if row.get("sport") == "mlb":
            g = _get(f"https://statsapi.mlb.com/api/v1/schedule?gamePk={row['event_id']}")["dates"][0]["games"][0]
            return g["status"]["abstractGameState"] != "Preview"
    except Exception:
        return None
    return None


def check_offered(rep: Report):
    r = rep.row
    if getattr(rep, "locked", False):
        rep.add("WARN", "offered", "event already under way: pick is locked, line can't be re-checked")
        return
    book = (r.get("book") or "").lower()
    if "prizepicks" in book:
        from . import pp
        lg = {"cs2": "CS2", "lol": "LoL", "mlb": "MLB", "nhl": "NHL", "nfl": "NFL", "soccer": "UCL"}.get(r.get("sport"))
        try:
            board = pp.board(lg, ("standard", "goblin", "demon")) if lg else []
        except Exception as e:
            rep.add("WARN", "offered", f"couldn't load the PrizePicks board ({type(e).__name__}): confirm the line on screen")
            return
        from .cs2 import same_name
        mine = [p for p in board if same_name(p["player"], r["player"])]
        hits = [p for p in mine if abs(p["line"] - float(r["line"])) < 1e-9]
        if not mine:
            # the partner feed lags the app and drops lines the app still shows: absence is not proof the line was pulled
            rep.add("WARN", "offered", f"{r['player']} is not in the PrizePicks partner feed now: confirm {r['line']} {r['side']} is on your screen")
        elif not hits:
            rep.add("FAIL", "offered", f"no {r['player']} line at {r['line']} on the PrizePicks board now (now {sorted({p['line'] for p in mine})})")
        elif r.get("side") == "under" and all(p["over_only"] for p in hits):
            rep.add("FAIL", "offered", "only a goblin/demon line at this number: More-only, the under can't be played")
        elif r.get("side") == "under" and all(p.get("feed_over_only") for p in hits):
            rep.add("WARN", "offered", f"on the board at {r['line']}; the feed marks it More-only but the app usually shows Less: confirm Less on screen")
        else:
            rep.add("PASS", "offered", f"on the PrizePicks board at {r['line']}" + (" (under available)" if r.get("side") == "under" else ""))
    else:
        rep.add("WARN", "offered", f"can't read {r.get('book') or 'this app'} automatically: confirm line {r['line']} and the {r['side']} side on screen")


def check_lol(rep: Report, adj: dict):
    from . import lol
    r = rep.row
    games = lol.player_games(r["player_id"])
    o, u, n = lol.history(games, float(r["line"]))
    ph = (o if r["side"] == "over" else u) / max(o + u, 1)
    logged, ln = _f(r.get("p_hist")), int(_f(r.get("hist_n")) or 0)
    if logged is None or abs(ph - logged) > TOL_HIST or abs((o + u) - ln) > 2:
        rep.add("FAIL", "recount", f"series history recounts to {ph:.2f} over {o + u} series; logged {logged} over {ln}")
    else:
        rep.add("PASS", "recount", f"series history {ph:.2f} ({o + u} series that reached game 3)")
    m = lol.find_match(int(r["event_id"]))
    if not m:
        rep.add("WARN", "reprice", "match not found among upcoming/current on bo3.gg: can't re-run the model")
        return
    ps, team = lol.team_series_p(m, games)
    pg = lol.per_game_p(ps, m.get("bo_type") or 5)
    pr = lol.price(games, pg, m.get("bo_type") or 5, float(r["line"]))
    pm = (pr["p_over"] if r["side"] == "over" else pr["p_under"]) / max(1 - pr["p_push"], 1e-9)
    lm = _f(r.get("p_model"))
    if (lm is None or abs(pm - lm) > TOL_MODEL) and getattr(rep, "locked", False):
        rep.add("WARN", "reprice", f"event under way: live odds give {pm:.2f} (logged {lm}); pre-game number stands for grading")
    elif lm is None or abs(pm - lm) > TOL_MODEL:
        rep.add("FAIL", "reprice", f"model now {pm:.2f} ({team} series {ps:.0%}); logged {lm}: re-price before publishing")
    else:
        rep.add("PASS", "reprice", f"model {pm:.2f} on current odds ({team} series {ps:.0%}, per game {pg:.0%})")
    e = final_probability(pm, None, ph, r.get("segment", ""), o + u, adj)
    rep.fresh = {"p_model": round(pm, 3), "p_hist": round(ph, 3), "hist_n": o + u, "p_final": round(e.p, 4), "confidence": e.confidence,
                 "side_note": f"fresh {dt.date.today()}: series {ps:.0%} ({team}), per game {pg:.0%}, {o + u} series of history"}
    rep.add("PASS" if e.confidence == r.get("confidence") else "FAIL", "fresh label",
            f"rebuilt from fresh data: {e.p:.3f} {e.confidence}" + ("" if e.confidence == r.get("confidence") else f" (logged {r.get('confidence')})"))


def check_cs2(rep: Report, adj: dict):
    from . import cs2
    r = rep.row
    teams = [t.strip() for t in re.split(r"\s+vs\.?\s+", re.sub(r"\s*\(.*$", "", r.get("event", "")))]
    if len(teams) != 2:
        rep.add("WARN", "recount", "can't parse the two teams from the event name: check by hand")
        return
    stat = "kills" if r["market"] == "cs_kills_m12" else "hs"
    for t in teams:
        res = cs2.price_match(t, teams[1] if t == teams[0] else teams[0], [{"player": r["player"], "team": t, "stat": stat, "line": float(r["line"])}])[0]
        if "error" not in res and res.get("maps"):
            break
    if "error" in res:
        rep.add("WARN", "recount", f"couldn't re-price from bo3.gg ({res['error']}): check by hand")
        return
    o, u = res["hist_over"], res["hist_under"]
    ph = (o if r["side"] == "over" else u) / max(o + u, 1)
    logged, ln = _f(r.get("p_hist")), int(_f(r.get("hist_n")) or 0)
    rep.add("FAIL" if logged is None or abs(ph - logged) > TOL_HIST else "PASS", "recount",
            f"maps 1-2 history {ph:.2f} over {o + u} series (logged {logged} over {ln})")
    pm = (res["p_over"] if r["side"] == "over" else res["p_under"]) / max(1 - res["p_push"], 1e-9)
    lm = _f(r.get("p_model"))
    off = lm is None or abs(pm - lm) > TOL_MODEL
    rep.add("WARN" if off and getattr(rep, "locked", False) else "FAIL" if off else "PASS", "reprice",
            f"model now {pm:.2f}, logged {lm}" + (" (event under way: live data, pre-game number stands)" if off and getattr(rep, "locked", False) else ""))


def check_mlb_history(rep: Report):
    from .grade import MLB_STATS, _get
    r = rep.row
    if _f(r.get("p_hist")) is None:
        rep.add("PASS", "recount", "no history component used")
        return
    if r["market"] == "game_total":
        check_mlb_game_total(rep)
        return
    if r["market"] not in MLB_STATS:
        rep.add("WARN", "recount", f"no automatic recount for mlb {r['market']}: recount by hand before publishing")
        return
    group, fn = MLB_STATS[r["market"]]
    vals = []
    for gt in ("R", "P"):
        try:
            d = _get(f"https://statsapi.mlb.com/api/v1/people/{r['player_id']}/stats?stats=gameLog&group={group}&season={r['date'][:4]}&gameType={gt}")
            vals += [fn(s["stat"]) for s in d["stats"][0]["splits"] if fn(s["stat"]) is not None]
        except Exception:
            continue
    line = float(r["line"])
    o, u = sum(v > line for v in vals), sum(v < line for v in vals)
    ph = (o if r["side"] == "over" else u) / max(o + u, 1)
    logged = _f(r.get("p_hist"))
    rep.add("FAIL" if abs(ph - logged) > TOL_HIST else "PASS", "recount", f"this season's game log gives {ph:.2f} over {o + u} games (logged {logged})")


def check_mlb_game_total(rep: Report):
    """Game totals: recount both teams' finished games this season of the same kind as tonight's (L26: a playoff game
    is recounted in playoff games once there are 6+, else in all games)."""
    from .grade import _get
    r = rep.row
    api = "https://statsapi.mlb.com/api/v1"
    gm = _get(f"{api}/schedule?sportId=1&gamePk={r['event_id']}")["dates"][0]["games"][0]
    post = gm.get("gameType") not in ("R", "S", "E")
    tot = {}
    for side in ("away", "home"):
        sc = _get(f"{api}/schedule?sportId=1&teamId={gm['teams'][side]['team']['id']}&season={r['date'][:4]}&gameType=R,F,D,L,W")
        for d in sc["dates"]:
            for g in d["games"]:
                if g["status"].get("codedGameState") == "F" and g["gamePk"] != gm["gamePk"]:
                    tot[g["gamePk"]] = (g.get("gameType") != "R", (g["teams"]["away"].get("score") or 0) + (g["teams"]["home"].get("score") or 0))
    same = [t for p, t in tot.values() if p == post]
    vals = same if (post and len(same) >= 6) or not post else [t for _, t in tot.values()]
    line = float(r["line"])
    o, u = sum(v > line for v in vals), sum(v < line for v in vals)
    ph = (o if r["side"] == "over" else u) / max(o + u, 1)
    logged = _f(r.get("p_hist"))
    kind = "postseason" if post and vals is same else "season"
    rep.add("FAIL" if logged is None or abs(ph - logged) > TOL_HIST else "PASS", "recount",
            f"both teams' {kind} games give {ph:.2f} over {o + u} (logged {logged})")


def check_mlb_lineup(rep: Report):
    """A hitter prop needs him in the posted lineup and a pitcher prop needs him as the listed starter: an 80% call
    on a player who sits is a void at best. Lineups post ~3 hours before first pitch; until then it's a WARN."""
    from .grade import _get
    r = rep.row
    mk = r.get("market", "")
    if not (mk.startswith("batter_") or mk.startswith("pitcher_")) or not r.get("player_id"):
        return
    try:
        gm = _get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&gamePk={r['event_id']}&hydrate=lineups,probablePitcher")["dates"][0]["games"][0]
    except Exception:
        rep.add("WARN", "lineup", "couldn't read the MLB lineup: confirm he plays before publishing")
        return
    pid = str(r["player_id"])
    if mk.startswith("pitcher_"):
        probs = {str((gm["teams"][s].get("probablePitcher") or {}).get("id")) for s in ("away", "home")}
        rep.add("PASS" if pid in probs else "FAIL", "starter",
                "listed as tonight's probable starter" if pid in probs else "not the listed probable starter: withdraw")
        return
    lu = gm.get("lineups") or {}
    names = [str(p.get("id")) for k in ("awayPlayers", "homePlayers") for p in lu.get(k, [])]
    if not names:
        rep.add("WARN", "lineup", "lineups not posted yet (about 3 hours before first pitch): confirm he starts")
    elif pid in names:
        rep.add("PASS", "lineup", "in the posted lineup")
    else:
        rep.add("FAIL", "lineup", "not in the posted lineup: withdraw (a pinch-hit appearance doesn't play the prop)")


def check_lineup(rep: Report, s: dict):
    """L29: soccer props are priced for a full start. Nine overs lost on 10/13 to players who got 10-38 minutes."""
    r = rep.row
    ros = s.get("rosters") or []
    if not any(p.get("starter") for ro in ros for p in ro.get("roster", [])):
        rep.add("WARN", "lineup", "starting XI not out yet: confirm he starts before publishing (L29)")
        return
    me = next((p for ro in ros for p in ro.get("roster", []) if str(p["athlete"]["id"]) == str(r.get("player_id"))), None)
    if me is not None and me.get("starter"):
        rep.add("PASS", "lineup", "named in the starting XI")
        return
    where = "not in the matchday squad" if me is None else "on the bench"
    over = r.get("side") == "over"
    rep.add("FAIL" if over else "WARN", "lineup",
            f"{where}: " + ("an over needs a full start, withdraw it (L29)" if over else "a sub's minutes are a guess, re-price or withdraw (L29)"))


def check_soccer(rep: Report):
    """Soccer passes (L26): a keeper must be priced with the keeper model, and history is recounted in the SAME kind of
    competition as tonight's match (European cup vs domestic): a keeper or a possession side can look completely
    different in Europe than at home."""
    from . import soccer
    r = rep.row
    s = soccer.summary(r["event_id"])
    check_lineup(rep, s)
    if r.get("market") != "passes_att":
        rep.add("WARN", "recount", f"no automatic recount for soccer {r.get('market')} yet: recount history by hand before publishing")
        return
    team_id, pos = None, None
    for ro in s.get("rosters", []):
        for p in ro.get("roster", []):
            if str(p["athlete"]["id"]) == str(r["player_id"]):
                team_id, pos = str(ro["team"]["id"]), (p.get("position") or {}).get("abbreviation")
    if team_id is None:  # rosters not out yet: find his team from recent matches
        for c in s["header"]["competitions"][0]["competitors"]:
            if any(g for g in [soccer.player_match(m, c["team"]["id"], r["player_id"]) for m in soccer.team_matches(str(c["team"]["id"]), 6)] if g):
                team_id = str(c["team"]["id"])
                break
    if team_id is None:
        rep.add("FAIL", "recount", "player not found on either team's recent matches: can't back-check")
        return
    rows = [g for g in (soccer.player_match(m, team_id, r["player_id"]) for m in soccer.team_matches(team_id, 40)) if g]
    starts = [g for g in rows if g["starter"] and g["minutes"] >= 60]
    keeper = pos == "G" or any(g.get("position") == "G" for g in starts)
    if keeper and "keeper" not in (r.get("notes") or "").lower():
        rep.add("FAIL", "rule L26", "goalkeeper priced with the outfield passes model: re-price with soccer.keeper_passes")
    cup = s.get("header", {}).get("league", {}).get("slug") in soccer.CUPS
    same = [g for g in starts if (g["league"] in soccer.CUPS) == cup]
    line, side = float(r["line"]), r.get("side", "over")
    rate = lambda gs: (sum((g["passes"] > line) if side == "over" else (g["passes"] < line) for g in gs) / len(gs)) if gs else None
    p_same, p_all, logged = rate(same), rate(starts), _f(r.get("p_hist"))
    kind = "European-cup" if cup else "domestic"
    msg = f"{kind} starts {p_same if p_same is None else round(p_same, 2)} over {len(same)}; all starts {p_all if p_all is None else round(p_all, 2)} over {len(starts)} (logged {logged})"
    # L27: also recount in starts at a team possession close to tonight's forecast (logged in the notes)
    import re as _re
    mp = _re.search(r"possession (\d+)%", r.get("notes") or "")
    if mp and not keeper:
        target = int(mp.group(1)) / 100
        comp = [g for g in starts if g.get("poss") is not None and abs(g["poss"] - target) <= soccer.POSS_BAND]
        p_comp = rate(comp)
        if p_comp is not None and len(comp) >= soccer.MIN_COMPARABLE and logged is not None and abs(p_comp - logged) > 0.20:
            rep.add("FAIL", "rule L27", f"in {len(comp)} starts at {target:.0%}+/-7 possession the {side} hit {p_comp:.0%} vs logged {logged:.0%}: re-price on comparable games")
        elif p_comp is not None:
            rep.add("PASS", "rule L27", f"comparable-possession starts ({target:.0%}+/-7): {side} {p_comp:.0%} over {len(comp)}")
    if p_same is not None and len(same) >= 6 and logged is not None and abs(p_same - logged) > 0.20:
        rep.add("FAIL", "recount", f"{msg}: this competition tells a different story (L26)")
    elif p_same is not None and len(same) >= 3 and logged is not None and abs(p_same - logged) > 0.20:
        rep.add("WARN", "recount", f"{msg}: few {kind} starts, but they disagree with the logged history")
    else:
        rep.add("PASS", "recount", msg)


def refresh(rows: list[dict], adj: dict | None = None) -> list[tuple]:
    """Re-score pending, not-yet-started picks with today's weights and gates (after `edge learn` changes them)."""
    adj = adj or load_adjustments()
    changed = []
    for r in rows:
        if r.get("status") not in ("pending", "") or started(r):
            continue
        pm, pk, ph = _f(r.get("p_model")), _f(r.get("p_market")), _f(r.get("p_hist"))
        if pm is None and pk is None and ph is None:
            continue
        e = final_probability(pm, pk, ph, r.get("segment", ""), int(_f(r.get("hist_n")) or 0), adj)
        if _f(r.get("p_final")) is None or abs(e.p - _f(r["p_final"])) > TOL_P or e.confidence != r.get("confidence"):
            changed.append((r["id"], r["player"], r.get("p_final"), r.get("confidence"), round(e.p, 4), e.confidence))
            r["notes"] = (r.get("notes", "") + f" | re-scored {dt.date.today()}: {r.get('p_final')} {r.get('confidence')} -> {e.p:.4f} {e.confidence}").strip(" |")
            r["p_final"], r["confidence"] = round(e.p, 4), e.confidence
    return changed


def verify(row: dict, rows: list[dict], adj: dict | None = None, fetch: bool = True) -> Report:
    adj = adj or load_adjustments()
    rep = Report(row)
    st = started(row) if fetch else False
    rep.locked = bool(st)
    rep.start_unknown = st is None and fetch
    check_recompute(rep, adj)
    check_rules(rep)
    check_correlation(rep, rows)
    if fetch:
        sport = row.get("sport")
        try:
            if sport == "lol":
                check_lol(rep, adj)
            elif sport == "cs2":
                check_cs2(rep, adj)
            elif sport == "mlb":
                check_mlb_history(rep)
                check_mlb_lineup(rep)
            elif sport == "soccer":
                check_soccer(rep)
            else:
                rep.add("WARN", "recount", f"no automatic recount for {sport} yet: recount history by hand before publishing")
        except Exception as e:
            rep.add("FAIL", "recount", f"back-check crashed ({type(e).__name__}: {str(e)[:60]}): not verified")
        check_offered(rep)
    repriced = any(n == "reprice" and st == "PASS" for st, n, _ in rep.checks)
    if row.get("date") and row["date"] < dt.date.today().isoformat() and not repriced:
        rep.add("WARN", "freshness", f"priced on {row['date']} and not re-run today: odds, lineups and lines may have moved")
    return rep
