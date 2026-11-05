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
import json
import os
import re
from dataclasses import dataclass, field

from .blend import final_probability, load_adjustments

TOL_P = 0.005      # recompute must match the logged number
TOL_HIST = 0.05    # recount within 5 pts of the logged history
TOL_MODEL = 0.04   # re-run model within 4 pts, else re-price before publishing
TOL_ENTRY = 0.02   # Fix 7: an ENTRY leg (action "bet") must reprice and recount within 2 pts
DRIFT_N, DRIFT_MAX = 50, 0.05   # trailing published NBA legs: predicted vs realized gap past 5 pts = WARN on new legs
STALE_MIN = 60     # market data older than this inside the last hour before tip FAILS (re-price first)


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
        head = f"#{r['id']} {r['player']} {r['market']} {r['side']} {r['line']} | p {r.get('p_final')} {r.get('confidence')} -> {self.verdict}"
        return "\n".join([head] + [f"   {s:4s} {n:11s} {d}" for s, n, d in self.checks])


# ------------------------------------------------------------------ individual checks
def check_recompute(rep: Report, adj: dict):
    r = rep.row
    pm, pk, ph = _f(r.get("p_model")), _f(r.get("p_market")), _f(r.get("p_hist"))
    if pm is None and pk is None and ph is None:
        rep.add("FAIL", "recompute", "no model, market or history stored: nothing to check the number against")
        return
    e = final_probability(pm, pk, ph, r.get("segment", ""), int(_f(r.get("hist_n")) or 0), adj)
    if r.get("sport") == "nba":                  # NBA legs: rebuild under the logic version that priced them
        from . import nba_model, nba_pp
        mv = re.search(r"logic v(\d+)", r.get("notes") or "")
        lg_ = nba_model.params_for(int(mv.group(1)) if mv else 1)
        p_, c_ = nba_pp.recompute(pm, pk, ph, int(_f(r.get("hist_n")) or 0), r.get("segment", ""), lg_)
        if "role unconfirmed" in (r.get("notes") or ""):
            c_ = "Low"
        e = type(e)(p=p_, confidence=c_, agreement=e.agreement, spread=e.spread, components=e.components, notes=e.notes)
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
    if sport == "mlb" and mk in ("pitcher_outs", "pitcher_pitches") and side == "over" and r.get("date", "")[5:7] in ("10", "11"):
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
        if row.get("sport") in ("nfl", "cfb"):
            lg = "college-football" if row["sport"] == "cfb" else "nfl"
            s = _get(f"https://site.api.espn.com/apis/site/v2/sports/football/{lg}/summary?event={row['event_id']}")
            return s["header"]["competitions"][0]["status"]["type"]["name"] != "STATUS_SCHEDULED"
        if row.get("sport") == "mlb":
            g = _get(f"https://statsapi.mlb.com/api/v1/schedule?gamePk={row['event_id']}")["dates"][0]["games"][0]
            return g["status"]["abstractGameState"] != "Preview"
        if row.get("sport") == "nba":
            s = _get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={row['event_id']}")
            return s["header"]["competitions"][0]["status"]["type"]["name"] != "STATUS_SCHEDULED"
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
        lg = {"cs2": "CS2", "lol": "LoL", "mlb": "MLB", "nhl": "NHL", "nfl": "NFL", "soccer": "UCL", "nba": "NBA"}.get(r.get("sport"))
        try:
            board = pp.board(lg, ("standard", "goblin", "demon")) if lg else []
        except Exception as e:
            rep.add("WARN", "offered", f"couldn't load the PrizePicks board ({type(e).__name__}): confirm the line on screen")
            return
        from .cs2 import same_name
        hits = [p for p in board if same_name(p["player"], r["player"]) and abs(p["line"] - float(r["line"])) < 1e-9]
        if not hits:
            rep.add("FAIL", "offered", f"no {r['player']} line at {r['line']} on the PrizePicks board now (moved or pulled)")
        elif r.get("side") == "under" and all(p["over_only"] for p in hits):
            rep.add("FAIL", "offered", "line is MORE-ONLY on PrizePicks: the under can't be played")
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


def check_nfl(rep: Report, adj: dict):
    """Re-run the simulator (same seed, fresh lines and injury report), recount history at this line, and
    confirm DraftKings still posts this line (the NFL feed has lines but no prices)."""
    from . import nfl
    r = rep.row
    if getattr(rep, "locked", False):
        rep.add("WARN", "offered", "game under way or over: pick is locked; audit only (never rewritten)")
    res = nfl.price_game(str(r["event_id"]), n=50000)
    hit = [x for x in res["rows"] if str(x["player_id"]) == str(r["player_id"]) and x["market"] == r["market"]]
    if not hit:
        rep.add("FAIL", "offered", f"DraftKings no longer posts {r['player']} {r['market']}: pulled (injury/role?)")
        return
    x = hit[0]
    if abs(x["line"] - float(r["line"])) > 1e-9:
        rep.add("WARN" if getattr(rep, "locked", False) else "FAIL", "offered", f"DraftKings line moved {r['line']} -> {x['line']}")
    else:
        rep.add("PASS", "offered", f"DraftKings still at {x['line']} (no price in the feed: confirm the odds on screen)")
    line = float(r["line"])
    o, u = nfl.player_history(str(r["player_id"]), None, res["history"], r["market"], line)
    ph = (o if r["side"] == "over" else u) / max(o + u, 1) if o + u else None
    logged = _f(r.get("p_hist"))
    if ph is None and logged is None:
        rep.add("PASS", "recount", "no history component used")
    else:
        bad = ph is None or logged is None or abs(ph - logged) > TOL_HIST
        rep.add("FAIL" if bad else "PASS", "recount", f"2026 games recount to {ph if ph is None else round(ph, 2)} over {o + u} (logged {logged})")
    pm = x["p_model"] if x["side"] == r["side"] else nfl.calibrated(1 - x["p_sim"], r["market"])
    lm = _f(r.get("p_model"))
    off = lm is None or abs(pm - lm) > TOL_MODEL
    rep.add("WARN" if off and getattr(rep, "locked", False) else "FAIL" if off else "PASS", "reprice",
            f"simulator now {pm:.3f} (calibrated), logged {lm}")
    if x["flags"]:
        rep.add("WARN", "role", "; ".join(x["flags"]))


def last_priced(notes: str):
    """When a leg was last priced: the latest of the pricer's "pulled" stamp and any "fresh" stamp a verify --fix
    re-price added (UTC), or None."""
    stamps = re.findall(r"(?:pulled|fresh) (\d{4}-\d\d-\d\d)[T ](\d\d:\d\d)Z", notes)
    return max(dt.datetime.fromisoformat(f"{d}T{t}+00:00") for d, t in stamps) if stamps else None


def check_nba(rep: Report, adj: dict):
    """Recount this season's games at the line from the box scores, re-run the simulation (50,000 runs, fresh injury
    report and DraftKings lines) and rebuild the label from fresh components."""
    from . import nba_pp
    from gamesim import nba as gnba, nba_research as gres
    r = rep.row
    line, stat, side = float(r["line"]), r["market"], r["side"]
    entry = r.get("action") == "bet"
    tol_m, tol_h = (TOL_ENTRY, TOL_ENTRY) if entry else (TOL_MODEL, TOL_HIST)
    ctx = nba_pp.build(gids={str(r["event_id"])})
    g = ctx["games"].get(str(r["event_id"]))
    if not g or str(r["event_id"]) not in ctx["sims"]:
        rep.add("WARN" if getattr(rep, "locked", False) else "FAIL", "reprice", "game not on ESPN's schedule now (started, postponed?): can't re-run")
        return
    y = gnba.season_of(g["start"][:10])
    key = ("nba_research", y)
    if key not in nba_pp._MEMO:
        nba_pp._MEMO[key] = gres.Research("nba", gnba.season_games("nba", f"{y}1018", dt.date.today().strftime("%Y%m%d")), y)
    RS = nba_pp._MEMO[key]
    cut = g["start"]
    cur = [e for e in RS.before(str(r["player_id"]), cut) if e["season"] == y]
    vals = [sum(e[k] for k in nba_pp.PARTS_KEYS[stat]) for e in cur]
    o, u = sum(v > line for v in vals), sum(v < line for v in vals)
    ph = (o if side == "over" else u) / max(o + u, 1) if o + u else None
    logged, ln = _f(r.get("p_hist")), int(_f(r.get("hist_n")) or 0)
    if ph is None and logged is None:
        rep.add("PASS", "recount", "no games this season: no history component")
    else:
        bad = ph is None or logged is None or abs(ph - logged) > tol_h or abs((o + u) - ln) > 1
        rep.add("FAIL" if bad else "PASS", "recount", f"box scores recount to {o} over / {u} under at {line} in {len(vals)} games (logged {logged} over {ln})"
                + (f"; ENTRY tolerance {tol_h:.0%}" if entry else ""))
    sim = ctx["sims"][str(r["event_id"])]["players"].get(str(r["player_id"]))
    if not sim:
        rep.add("WARN" if getattr(rep, "locked", False) else "FAIL", "reprice", f"{r['player']} is out of tonight's projected rotation now (injury report?)")
        return
    po, pu, pp_ = nba_pp.sides_at(sim["hist"][stat], line)
    m = re.search(r"model de-biased ([+-]\d+\.\d+) logit", r.get("notes") or "")
    if m and 0 < po < 1 - pp_:                 # the same per-scan bias fix the pricer applied (L7)
        q = nba_pp._sg(nba_pp._lg(po / (1 - pp_)) + float(m.group(1))) * (1 - pp_)
        po, pu = q, 1 - pp_ - q                # (not `o`: o and u are the season's over/under counts used below)
    pm = (po if side == "over" else pu) / max(1 - pp_, 1e-9)
    lm = _f(r.get("p_model"))
    off = lm is None or abs(pm - lm) > tol_m
    rep.add("WARN" if off and getattr(rep, "locked", False) else "FAIL" if off else "PASS", "reprice",
            f"simulation now {pm:.3f} (50,000 runs, current injury report), logged {lm}" + (f"; ENTRY tolerance {tol_m:.0%}" if entry else ""))
    # Fix 7: tilt monitor and stale market data
    mt = re.search(r"raw tilt ([+-]\d+\.\d+)", r.get("notes") or "")
    causes = json.load(open(nba_pp.TILT_CAUSES)) if os.path.exists(nba_pp.TILT_CAUSES) else {}
    if mt and abs(float(mt.group(1))) > nba_pp.TILT_MAX and stat not in causes:
        rep.add("FAIL" if entry else "WARN", "tilt", f"tonight's raw simulation-vs-DraftKings tilt on {stat} is {mt.group(1)} logit (limit "
                f"{nba_pp.TILT_MAX}) with no cause logged in data/nba_tilt_causes.json" + (": no ENTRY leg in this stat" if entry else ""))
    last = last_priced(r.get("notes") or "")
    if last and g.get("start") and not getattr(rep, "locked", False):
        now = dt.datetime.now(dt.timezone.utc)
        tip = dt.datetime.fromisoformat(g["start"].replace("Z", "+00:00"))
        age = (now - last).total_seconds() / 60
        if (tip - now).total_seconds() / 60 <= 60 and age > STALE_MIN:
            rep.add("FAIL", "freshness", f"market and injury data pulled {age:.0f} min ago, inside the last hour before tip: re-price (edge verify --fix)")
    dk = ((ctx["eng"]["sides"][str(r["event_id"])]["players"].get("lines") or {}).get(str(r["player_id"])) or {}).get(stat)
    pk = None
    if dk and dk.get("over") and dk.get("under"):
        qo, qu = nba_pp._imp(dk["over"]), nba_pp._imp(dk["under"])
        q = qo / (qo + qu)
        q = q if abs(dk["line"] - line) < 1e-9 else nba_pp.market_at(sim["hist"][stat], dk["line"], q, line)[0]
        pk = q if side == "over" else 1 - q
    lk = _f(r.get("p_market"))
    if (pk is None) != (lk is None) or (pk is not None and abs(pk - lk) > TOL_MODEL):
        rep.add("WARN", "market", f"DraftKings now {'none' if pk is None else f'{pk:.3f}'} (logged {lk}): the line or price moved, re-price before publishing")
    e = final_probability(pm, pk, ph, r.get("segment", ""), o + u, adj)
    rep.fresh = {"p_model": round(pm, 3), "p_market": "" if pk is None else round(pk, 3), "p_hist": "" if ph is None else round(ph, 3),
                 "hist_n": o + u, "p_final": round(e.p, 4), "confidence": e.confidence,
                 "side_note": f"fresh {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}: simulation re-run, {o + u} games of history"}
    conf = r.get("confidence")
    if "role unconfirmed" in (r.get("notes") or "") and conf == "Low":
        rep.add("PASS", "fresh label", f"rebuilt {e.p:.3f} {e.confidence}; stays Low (role or minutes unconfirmed, L5)")
    else:
        rep.add("PASS" if e.confidence == conf else "FAIL", "fresh label", f"rebuilt from fresh data: {e.p:.3f} {e.confidence}" + ("" if e.confidence == conf else f" (logged {conf})"))


def check_drift(rep: Report, rows: list[dict]):
    """Fix 7: calibration drift on the trailing DRIFT_N published, graded legs of the same sport."""
    r = rep.row
    pub = [x for x in rows if x.get("sport") == r.get("sport") and x.get("action") in ("bet", "lean") and x.get("status") in ("won", "lost")
           and _f(x.get("p_final")) is not None]
    pub.sort(key=lambda x: (x.get("date", ""), int(x["id"]) if str(x.get("id", "")).isdigit() else 0))
    tail = pub[-DRIFT_N:]
    if len(tail) < DRIFT_N:
        rep.add("PASS", "drift", f"{len(tail)} graded published {r.get('sport')} legs so far (drift check starts at {DRIFT_N})")
        return
    pred = sum(_f(x["p_final"]) for x in tail) / len(tail); real = sum(x["status"] == "won" for x in tail) / len(tail)
    rep.add("WARN" if abs(pred - real) > DRIFT_MAX else "PASS", "drift",
            f"last {DRIFT_N} published legs: predicted {pred:.1%}, realized {real:.1%}" + (" (calibration drift past 5 pts)" if abs(pred - real) > DRIFT_MAX else ""))


def check_mlb_history(rep: Report):
    from .grade import MLB_STATS, _get
    r = rep.row
    if _f(r.get("p_hist")) is None:
        rep.add("PASS", "recount", "no history component used")
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
    if row.get("sport") == "nba":
        check_drift(rep, rows)
    if fetch:
        sport = row.get("sport")
        try:
            if sport == "lol":
                check_lol(rep, adj)
            elif sport == "cs2":
                check_cs2(rep, adj)
            elif sport == "mlb":
                check_mlb_history(rep)
            elif sport == "nfl":
                check_nfl(rep, adj)
            elif sport == "nba":
                check_nba(rep, adj)
            else:
                rep.add("WARN", "recount", f"no automatic recount for {sport} yet: recount history by hand before publishing")
        except Exception as e:
            rep.add("FAIL", "recount", f"back-check crashed ({type(e).__name__}: {str(e)[:60]}): not verified")
        if sport != "nfl":   # check_nfl reads the DraftKings board itself
            check_offered(rep)
    repriced = any(n == "reprice" and st == "PASS" for st, n, _ in rep.checks)
    if row.get("date") and row["date"] < dt.date.today().isoformat() and not repriced:
        rep.add("WARN", "freshness", f"priced on {row['date']} and not re-run today: odds, lineups and lines may have moved")
    return rep
