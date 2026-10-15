"""Export the 8+ picks and the scorecard as JSON documents for the Eight-Plus Board page.

python -m edge board --out DIR [--days 7]

Writes DIR/picks/<id>.json (one per 8+ pick from the last few days, pending and graded) and DIR/meta/summary.json.
Each pending pick carries its `edge verify` verdict and warnings; every pick carries the raw game-by-game numbers
behind its history component, newest first, so the page shows the evidence and not just the rating.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from .blend import rating
from . import learn as L

SIDE = {"over": "More", "under": "Less"}
REG_MIN = 0.60   # a regular (standard) line is a play at 60%+: above every PrizePicks break-even (2-pick power 57.7%, 3-pick flex 59.8%)
STAT = {"pitcher_strikeouts": "Strikeouts", "skater_sog": "Shots on goal", "skater_points": "Points", "skater_assists": "Assists",
        "skater_goals": "Goals", "skater_ppp": "Power-play points", "batter_hits": "Hits", "batter_total_bases": "Total bases",
        "batter_hrr": "Hits + runs + RBIs", "batter_strikeouts": "Hitter strikeouts", "batter_walks": "Walks",
        "batter_singles": "Singles", "batter_runs": "Runs", "batter_rbi": "RBIs", "goalie_saves": "Saves", "batter_fs_pp": "Fantasy score",
        "points": "Points", "rebounds": "Rebounds", "assists": "Assists", "pra": "Pts + Rebs + Asts", "pts_asts": "Pts + Asts",
        "pts_rebs": "Pts + Rebs", "threes": "3-pointers made", "steals": "Steals", "blocks": "Blocks"}


def _f(x):
    try:
        return float(x) if x not in ("", None) else None
    except ValueError:
        return None


def _rating(r: dict) -> int | None:
    p = _f(r.get("p_final"))
    return None if p is None else rating(p, r.get("confidence"), _f(r.get("p_market")))


def games(r: dict) -> list[float]:
    """The game log behind the pick's history number, newest first (up to 15)."""
    from . import tier
    from . import lowline as LW
    sport, mk, pid = r["sport"].upper(), r["market"], r.get("player_id")
    if not pid:
        return []
    try:
        if sport in ("NHL", "NBA"):
            vals = tier.recount_values(sport, mk, (r.get("event") or "").split(" vs ")[0].strip(), pid) or []
        elif mk == "pitcher_strikeouts":
            vals = [float(g["x"].get("strikeOuts") or 0) for g in tier.mlb_pitch_log(pid)]
        elif sport == "MLB":
            stat = next((s for s, (_, k) in tier.STATS["MLB"].items() if k == mk), None)
            gl = [g for g in LW.mlb_log(pid) if (g["vol"] or 0) >= 3]
            vals = [v for v in (LW.value("MLB", stat, g) for g in gl) if v is not None] if stat else []
        else:
            vals = []
    except Exception:
        vals = []
    return [round(v, 1) for v in vals[:15]]


def _avg(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 2) if xs else None


def card_key(lg: str, player: str, stat: str, team: str) -> str:
    return f"{lg}|{player}|{stat}|{team}"


def build_card(lg: str, stat: str, team: str, opp: str, player: str, aid: str | None, position: str = "",
               home: bool | None = None, date: str = "", rungs: dict | None = None, competition: str = "regular") -> dict:
    """The prop card: his last 40 games (date, opponent, home/away, value), every game against tonight's opponent the
    logs hold, the DraftKings ladder (to price other lines), averages, venue split and matchup rank."""
    from . import tier
    from . import context as CX
    from . import lowline as LW
    every = tier.card_games(lg, stat, team, player, aid, limit=None, competition=competition)
    games = every[:40]
    vals = [g["v"] for g in games[:30]]
    norm = lambda a: tier.NHL_API.get(tier.espn_team(lg, a or ""), tier.espn_team(lg, a or ""))
    h2h_g = [g for g in every if opp and norm(g["o"]) == norm(opp)]
    h2h = [g["v"] for g in h2h_g]
    hm, aw = [g["v"] for g in games[:30] if g["h"] is True], [g["v"] for g in games[:30] if g["h"] is False]
    pid = aid
    if lg == "MLB":
        try:
            pid = LW.mlb_player(team, player)
        except Exception:
            pid = None
    slim = lambda g: {"d": g["d"], "o": g["o"], "h": g["h"], "v": g["v"]}
    extra = {}
    if lg == "MLB" and pid and opp and date:
        try:
            if stat in ("Pitcher Strikeouts", "Pitching Outs", "Hits Allowed", "Earned Runs Allowed", "Walks Allowed"):
                extra["pvl"] = CX.pitcher_vs_lineup(pid, opp)
            else:
                extra["bvp"] = CX.batter_vs_staff(pid, opp, date)
        except Exception:
            pass
    return {**extra, "pl": player, "pos": position, "tm": team, "op": opp, "st": stat,
            "g": [slim(g) for g in games], "hh": [slim(g) for g in h2h_g],
            "lad": {str(k): v for k, v in (rungs or {}).items()},
            "a5": _avg(vals[:5]), "a10": _avg(vals[:10]), "aN": _avg(vals), "n": len(vals),
            "h2h": {"avg": _avg(h2h), "n": len(h2h)}, "home": {"avg": _avg(hm), "n": len(hm)}, "away": {"avg": _avg(aw), "n": len(aw)},
            "tonight": "home" if home is True else "away" if home is False else "",
            "mu": CX.matchup(lg, stat, opp, pid, team, date),
            "dvp": _dvp(lg, stat, opp, position, aid, pid, team, date)}


def _dvp(lg: str, stat: str, opp: str, position: str, aid, pid, team: str, date: str) -> dict | None:
    """The Defense vs Position card: tonight's opponent against this position for this stat, ranked."""
    from . import dvp as DV
    from . import tier
    try:
        return DV.card(lg, tier.market_key(lg, stat), stat, opp, position or DV.position_of(lg, team, aid), pid, team, date)
    except Exception:
        return None


def _ladder_for(r: dict, stat: str) -> dict:
    """DraftKings 'k+' rungs for a logged pick, so its card can price other lines (empty when ESPN has none)."""
    from . import tier
    try:
        lg = r["sport"].upper()
        eid = (r.get("group") or "").split(":")[-1]
        team, _, opp = (r.get("event") or "").partition(" vs ")
        names = {}
        for ab in (tier.espn_team(lg, team.strip()), tier.espn_team(lg, opp.strip())):
            names.update(tier.roster(lg, ab))
        from . import lowline as LW
        aid = names.get(LW._fold(r["player"]))
        return tier.ladders(lg, eid).get((tier.STATS[lg][stat][0], aid or ""), {}) if aid and stat in tier.STATS.get(lg, {}) else {}
    except Exception:
        return {}


def pick_doc(r: dict, rows: list[dict], verify_it: bool) -> dict:
    notes = r.get("notes", "")
    m = re.search(r"DK (\d+)\+ ([+-]\d+)", notes)
    st = re.search(r"start (\d{4}-\d\d-\d\dT[\d:.]+(?:Z|[+-]\d\d:\d\d))", notes)      # PrizePicks "-04:00" or ESPN "Z"
    team, _, opp = (r.get("event") or "").partition(" vs ")
    hist, n = _f(r.get("p_hist")), int(_f(r.get("hist_n")) or 0)
    doc = {
        "id": r["id"], "slate": r["date"], "sport": r["sport"].upper(), "player": r["player"], "team": team.strip(), "opp": opp.strip(),
        "stat": STAT.get(r["market"], r["market"]), "line": _f(r["line"]), "side": SIDE.get(r["side"], r["side"]),
        "odds_type": (r.get("book") or "").replace("PrizePicks ", ""), "rating": _rating(r), "p": _f(r.get("p_final")),
        "market_p": _f(r.get("p_market")), "market_text": f"DraftKings {m.group(1)}+ at {m.group(2)}" if m else "",
        "hist_hits": round(hist * n) if hist is not None else None, "hist_n": n,
        "games": games(r) if (r.get("status") or "pending") == "pending" else [],      # a graded pick's log now holds its own result
        "start": st.group(1) if st else "", "status": r.get("status") or "pending", "proj": _f(r.get("proj")),
        "result": _f(r.get("result_value")), "verdict": "", "warns": [], "lesson": "",
        "context": (re.search(r"context: (.*?)(?:; start |$)", notes).group(1).split(" / ") if "context: " in notes else []),
    }
    from . import tier
    stat = next((s for lg_ in (tier.STATS, tier.EXTRA) for s, v in lg_.get(doc["sport"], {}).items()
                 if (v[1] if isinstance(v, tuple) else v) == r["market"]), None)
    if r["sport"] == "tennis":                                  # match winner: "Swiatek to win", no line, no game log
        who = (r.get("event") or "").split(" (")[0]
        a_, _, b_ = who.partition(" vs ")
        doc.update(side="To win", line=None, stat="Match winner", team="", opp=(b_ if a_.strip() == r["player"] else a_).strip(),
                   hist_hits=None, hist_n=0, odds_type="")
        if verify_it and doc["status"] == "pending":
            from .verify import verify
            rep = verify(r, rows)
            doc["verdict"] = rep.verdict
            doc["warns"] = [f"{name}: {d}" for s, name, d in rep.checks if s in ("WARN", "FAIL")]
        return doc
    if doc["proj"] is None and doc["status"] == "pending":       # rows logged before projections: price the matchup now
        from . import context as CX
        cx = CX.price(doc["sport"], stat, doc["opp"], r.get("player_id"), doc["line"], int(r["date"][:4])) if stat else None
        if cx:
            doc["proj"], doc["context"] = round(cx[2], 1), doc["context"] or cx[1]
    if stat and doc["status"] == "pending":
        try:
            doc["card"] = build_card(doc["sport"], stat, doc["team"], doc["opp"], r["player"],
                                     r.get("player_id") if doc["sport"] in ("NBA", "NFL") else None, date=r["date"],
                                     rungs=_ladder_for(r, stat),
                                     competition="preseason" if "preseason: history from" in r.get("notes", "") else "regular")
        except Exception:
            pass
    if verify_it and doc["status"] == "pending":
        from .verify import verify
        rep = verify(r, rows)
        doc["verdict"] = rep.verdict
        doc["warns"] = [f"{name}: {d}" for s, name, d in rep.checks if s in ("WARN", "FAIL")]
    return doc


def is_regular_play(r: dict) -> bool:
    p = _f(r.get("p_final"))
    return "standard" in (r.get("book") or "").lower() and p is not None and p >= REG_MIN and r.get("confidence") in ("Medium", "High")


def summary(rows: list[dict]) -> dict:
    reg = [r for r in rows if r.get("status") in ("won", "lost") and is_regular_play(r)]
    bands = {"8-10": [0, 0, 0.0], "8-10 no book": [0, 0, 0.0], "5-7": [0, 0, 0.0], "1-4": [0, 0, 0.0]}
    for r in rows:
        if r.get("status") not in ("won", "lost"):
            continue
        rt = _rating(r)
        if rt is None:
            continue
        b = bands[("8-10" if _f(r.get("p_market")) is not None else "8-10 no book") if rt >= 8 else "5-7" if rt >= 5 else "1-4"]
        b[0] += r["status"] == "won"
        b[1] += 1
        b[2] += _f(r["p_final"])
    return {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "regular": {"hits": sum(r["status"] == "won" for r in reg), "n": len(reg), "min": REG_MIN,
                        "predicted": round(sum(_f(r["p_final"]) for r in reg) / len(reg), 3) if reg else None},
            "bands": [{"band": k, "hits": h, "n": n, "predicted": round(p / n, 3) if n else None} for k, (h, n, p) in bands.items()]}


def hold_reason(r: dict) -> str | None:
    """Why a priced prop sits below 8, as a short code the page spells out with the row's own numbers:
    gap, role, out, sit, cap (L5/L31 holds), avoid, split (sources on different sides), one (single source), book (a book
    under 75%), floor (under the 80% bar), thin (too few games), far (sources too far apart), short (history the blend
    shrinks toward 50% ends up too far from the model), learned (a learned cap), low (under 58%), mid (a lean)."""
    if (r.get("rating") or 0) >= 8:
        return None
    n = r.get("notes") or ""
    for key, code in (("circumstances (out)", "out"), ("circumstances (hold)", "sit"), ("line gap:", "gap"), ("role unconfirmed", "role"),
                      ("role change:", "role"), ("avoid list", "avoid"), ("circumstances (cap)", "cap"),
                      ("disagree on the side", "split"), ("single-source", "one"), ("capped at Medium", "learned")):
        if key in n:
            return code
    from .blend import TIER_MARKET_MIN, load_adjustments
    p, pm, conf = r.get("p_final") or 0, r.get("p_market"), r.get("confidence")
    hn = int(r.get("hist_n") or 0)
    comps = [v for v in (r.get("p_model"), pm, r.get("p_hist")) if v is not None]
    spread = max(comps) - min(comps) if len(comps) > 1 else 0
    g = load_adjustments()["gates"]
    if conf == "High":
        return "book" if pm is not None and pm < TIER_MARKET_MIN else "floor"
    if p < g["medium"]:
        return "low"
    if p < g["high"]:
        return "mid"
    if hn < g["min_hist_n_high"] or (pm is None and hn < g.get("no_market_min_hist_n", 20)):
        return "thin"
    limit = g["max_spread_high"] if pm is not None else g.get("no_market_max_spread", 0.10)
    if spread > limit:
        return "far"
    if shrunk_spread(r.get("p_model"), pm, r.get("p_hist"), hn) > limit:
        return "short"                                              # the blend shrinks short history toward the book (or 50%)
    return "mid"


def shrunk_spread(p_model, p_market, p_hist, hist_n: int) -> float:
    """Spread between the sources as the blend sees them: history regressed toward the book, or 50% with no book."""
    comps = [v for v in (p_model, p_market) if v is not None]
    if p_hist is not None:
        w = hist_n / (hist_n + 10) if hist_n else 0.5
        comps.append(w * p_hist + (1 - w) * (p_market if p_market is not None else 0.5))
    return max(comps) - min(comps) if len(comps) > 1 else 0.0


HOLD_TEXT = {"gap": "line gap: the standard line is far from his log, so the line likely knows something (role, injury)",
             "role": "role change: his workload over the last 5 games is 25%+ off his average (L5)",
             "out": "listed out tonight", "sit": "tonight's report or news says he may sit or play a smaller role",
             "cap": "tonight's report (questionable, a blowout spread, weather) caps it", "avoid": "this market is on the avoid list",
             "split": "the sources point to different sides", "one": "only one source: no book price and no usable history",
             "book": "the sportsbook makes it under 75%", "floor": "under the 80% bar for an 8",
             "thin": "too few games to trust", "far": "the sources are too far apart",
             "short": "short history is discounted toward 50% with no book price, which leaves it too far from the model", "learned": "capped by graded results in this market",
             "low": "under 58%: not a play", "mid": "a lean, not an 8"}


def _row(r: dict, source: str) -> dict:
    """One compact row for the page's props explorer."""
    return {"pl": r["player"], "tm": r.get("team", ""), "op": r.get("opp", ""), "st": r["stat"], "ln": r["line"],
            "sd": ("More" if r["side"] == "over" else "Less") if source == "pp" else ("Over" if r["side"] == "over" else "Under"),
            "ty": r.get("odds_type", "") if source == "pp" else r.get("book", ""), "pr": r.get("price"),
            "p": round(r["p_final"], 4), "pm": None if r.get("p_market") is None else round(r["p_market"], 4),
            "ph": None if r.get("p_hist") is None else round(r["p_hist"], 3), "n": r.get("hist_n", 0),
            "r": r["rating"], "t": r.get("start", ""), "cx": r.get("context") or [],
            "pj": r.get("proj"), "pjs": r.get("proj_src", ""), "a10": r.get("avg10"),
            "ck": card_key(r["league"], r["player"], r["stat"], r.get("team", "")),
            "pmod": None if r.get("p_model") is None else round(r["p_model"], 3), "lo": hold_reason(r)}


def regular(pp_rows: list[dict], now: str, top: int = 10) -> dict:
    """The best regular (standard) PrizePicks lines on the board. A line is a play only at 60%+, not Low, logged and
    back-checked this run; the rest are shown with the reason they are not."""
    from .verify import verify
    bets = L.read_bets()
    by_key = {(b["player"].lower(), b["market"], str(_f(b["line"])), b["side"]): b for b in bets
              if b.get("status") == "pending" and "standard" in (b.get("book") or "").lower()}
    st = sorted((r for r in pp_rows if r.get("odds_type") == "standard"), key=lambda r: -r["p_final"])[:top]
    rows = []
    for r in st:
        d = {**_row(r, "pp"), "lg": r["league"], "play": False, "why": ""}
        if r["p_final"] < REG_MIN:
            d["why"] = f"under {REG_MIN:.0%}: below the break-even"
        elif r["confidence"] == "Low":
            d["why"] = HOLD_TEXT.get(hold_reason(r) or "", "held at Low")
        else:
            b = by_key.get((r["player"].lower(), r["market_key"], str(float(r["line"])), r["side"]))
            if not b:
                d["why"] = "not logged yet: run edge tier --log"
            else:
                rep = verify(b, bets)
                d["play"] = not rep.verdict.startswith("NOT")
                d["why"] = "back-check: " + rep.verdict.lower()
                d["warns"] = [f"{n}: {x}" for s_, n, x in rep.checks if s_ in ("WARN", "FAIL")]
        rows.append(d)
    return {"updated": now, "min": REG_MIN, "rows": rows}


PP_EXTRA = ("CS2", "LOL", "VAL", "SOCCER")


STATE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "board_state"


def save_state(lg: str, compact: list[dict], tried: list | None = None) -> None:
    """Every PrizePicks line priced for a league (the board documents keep the best ~2,500), so `edge refresh` can tell
    a new prop from one that was priced and trimmed. Kept in .cache: a fresh container starts from the board itself."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / f"pp-{lg}.json").write_text(json.dumps({"updated": dt.datetime.now(dt.timezone.utc).isoformat(), "rows": compact,
                                                         "tried": tried or []}, separators=(",", ":")))


def load_state(lg: str) -> list[dict] | None:
    p = STATE_DIR / f"pp-{lg}.json"
    try:
        return json.loads(p.read_text())["rows"]
    except (OSError, ValueError, KeyError):
        return None


def load_tried(lg: str) -> set:
    """Props a refresh already tried and couldn't price (no data, not found): (player, stat, type, line) keys."""
    p = STATE_DIR / f"pp-{lg}.json"
    try:
        return {tuple(k) for k in json.loads(p.read_text()).get("tried", [])}
    except (OSError, ValueError):
        return set()


def _tried(errors: list[dict]) -> list:
    """(player, stat, type, line) keys of props a scan couldn't price, so the hourly refresh doesn't retry them."""
    from .refresh import pkey
    out = []
    for p in errors:
        try:
            out.append(list(pkey(p)))
        except (KeyError, TypeError, ValueError):
            continue
    return out


PART_BYTES = 245_000      # one db document holds 256 KB
MAX_PARTS = 6
CARD_ROWS = 700           # tier leagues build cards over the network: the best-rated rows get them


def board_docs(source: str, lg: str, compact: list[dict], now: str) -> list[tuple[str, dict]]:
    """A league's board as one or more documents, best-rated rows first: <source>-<LG> holds the top rows and the part
    count, the rest go to <source>-<LG>~2, ~3, ... The page reads a part only when its `updated` matches the main
    document's, so a part left over from a bigger board is ignored."""
    head = {"source": source, "league": lg, "updated": now}
    parts, cur, size = [], [], 200
    for r in compact:
        s = len(json.dumps(r, separators=(",", ":"))) + 1
        if cur and size + s > PART_BYTES:
            parts.append(cur)
            cur, size = [], 200
            if len(parts) == MAX_PARTS:
                break
        cur.append(r)
        size += s
    if cur and len(parts) < MAX_PARTS:
        parts.append(cur)
    parts = parts or [[]]
    docs = [(f"{source}-{lg}", {**head, "parts": len(parts), "rows": parts[0]})]
    docs += [(f"{source}-{lg}~{i}", {**head, "part": i, "rows": rows}) for i, rows in enumerate(parts[1:], start=2)]
    return docs


def read_board(live: str, source: str, lg: str) -> dict:
    """A league's board as ArtifactData listed it (LIVE/boards/<id>.json), parts merged; {"rows": []} when there is none."""
    def load(doc_id):
        f = Path(live, "boards", f"{doc_id}.json")
        if not f.exists():
            return None
        d = json.loads(f.read_text())
        return d.get("data", d)
    main = load(f"{source}-{lg}")
    if not main:
        return {"rows": []}
    rows = list(main.get("rows", []))
    for i in range(2, (main.get("parts") or 1) + 1):
        part = load(f"{source}-{lg}~{i}")
        if part and part.get("updated") == main.get("updated"):
            rows += part.get("rows", [])
    return {**main, "rows": rows}


def write_board_docs(base: Path, docs: list[tuple[str, dict]]) -> list[tuple[str, str, str]]:
    base.mkdir(parents=True, exist_ok=True)
    out = []
    for doc_id, d in docs:
        p = base / f"{doc_id}.json"
        p.write_text(json.dumps(d, separators=(",", ":")))
        out.append(("boards", doc_id, str(p)))
    return out


def _write_board(base: Path, source: str, lg: str, rows: list[dict], now: str,
                 errors: list[dict] | None = None) -> tuple[list[dict], list[tuple[str, str, str]]]:
    """The league's board documents (board_docs), best-rated rows first. Returns the rows kept and the writes."""
    sel = sorted(rows, key=lambda r: (-r["rating"], -r["p_final"]))
    compact = [_row(r, source) for r in sel]
    if source == "pp":
        save_state(lg, compact, _tried(errors or []))
    docs = board_docs(source, lg, compact, now)
    sel = sel[:sum(len(d["rows"]) for _, d in docs)]
    return sel, write_board_docs(base, docs)


def _write_cards(out: str, lg: str, built: dict) -> list[tuple[str, str, str]]:
    """Pack a league's cards into documents under ~180 KB each (the store's limit is 256 KB)."""
    cdir = Path(out) / "cards"
    cdir.mkdir(parents=True, exist_ok=True)
    written, chunk, size, i = [], {}, 0, 0
    for k, c in ((k, c) for k, c in built.items() if k.startswith(lg + "|")):
        s = len(json.dumps(c, separators=(",", ":")))
        if chunk and size + s > 180_000:
            p = cdir / f"{lg}-{i}.json"
            p.write_text(json.dumps({"league": lg, "cards": chunk}, separators=(",", ":")))
            written.append(("cards", f"{lg}-{i}", str(p)))
            chunk, size, i = {}, 0, i + 1
        chunk[k], size = c, size + s
    if chunk:
        p = cdir / f"{lg}-{i}.json"
        p.write_text(json.dumps({"league": lg, "cards": chunk}, separators=(",", ":")))
        written.append(("cards", f"{lg}-{i}", str(p)))
    return written


def history_card(r: dict, lg: str) -> dict:
    """A prop card from the pricer's own game-by-game history (esports series totals, soccer matches)."""
    games = (r.get("games") or [])[:40]
    vals = [g["v"] for g in games[:30]]
    opp = str(r.get("opp") or "")
    from .cs2 import same_name
    hh = [g for g in games if opp and g.get("o") and (same_name(g["o"], opp) or opp.lower() in str(g["o"]).lower())]
    hm, aw = [g["v"] for g in games[:30] if g.get("h") is True], [g["v"] for g in games[:30] if g.get("h") is False]
    return {"pl": r["player"], "pos": r.get("position") or "", "tm": r.get("team", ""), "op": opp, "st": r["stat"],
            "g": games, "hh": hh, "lad": {}, "a5": _avg(vals[:5]), "a10": _avg(vals[:10]), "aN": _avg(vals), "n": len(vals),
            "h2h": {"avg": _avg([g["v"] for g in hh]), "n": len(hh)}, "home": {"avg": _avg(hm), "n": len(hm)},
            "away": {"avg": _avg(aw), "n": len(aw)}, "tonight": "", "mu": None, "dvp": None}


def extra_row(r: dict, lg: str) -> dict:
    """An edge pp row (esports, soccer) with what the board needs: league, rating, context, projection source, L10 average."""
    vals = [g["v"] for g in (r.get("games") or [])[:10]]
    src = "model median" if lg != "SOCCER" else "DraftKings" if r.get("p_market") is not None else "game log"
    return {**r, "league": lg, "rating": rating(r["p_final"], r["confidence"], r.get("p_market")),
            "context": [r["notes"]] if r.get("notes") else [], "proj_src": src, "avg10": _avg(vals)}


def export_pp_extra(out: str, leagues=PP_EXTRA, log: bool = True) -> list[tuple[str, str, str]]:
    """boards/pp-<LG> and cards for PrizePicks boards edge pp prices (CS2, LoL, Valorant, soccer): standard and goblin
    lines for games that haven't started, each rated like every other prop and logged to bets.csv (so an 8+ becomes a pick
    after its back-check)."""
    from . import pp as PPM
    written, base = [], Path(out) / "boards"
    base.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_now = dt.datetime.now(dt.timezone.utc)
    for lg in leagues:
        try:
            props = PPM.soccer_board() if lg == "SOCCER" else PPM.board(lg, ("standard", "goblin"))
        except Exception:
            continue
        props = [p for p in props if p.get("start") and dt.datetime.fromisoformat(p["start"]) > t_now]
        priced = PPM.price_board(props)
        ok = [r for r in priced if "error" not in r]
        if log and ok:
            PPM.log_rows(ok)
        rows = [extra_row(r, lg) for r in ok]
        sel, w = _write_board(base, "pp", lg, rows, now, [r for r in priced if "error" in r])
        written += w
        built = {}
        for r in sel:
            k = card_key(lg, r["player"], r["stat"], r.get("team", ""))
            if k not in built and r.get("games"):
                built[k] = history_card(r, lg)
        written += _write_cards(out, lg, built)
    return written


def export_props(out: str, leagues=("NHL", "MLB", "NBA"), date: dt.date | None = None, days: int = 2,
                 log: bool = True) -> list[tuple[str, str, str]]:
    """boards/pp-<LG> (every PrizePicks line we could price) and boards/book-<LG> (sportsbook lines), each rated."""
    from . import tier
    written, base = [], Path(out) / "boards"
    base.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    scanned = tier.scan(leagues, date, days=days)
    pp = [r for r in scanned if "error" not in r and r.get("odds_type") != "demon"]
    errs = [r for r in scanned if "error" in r]
    if log:
        tier.log_rows(pp)                                           # every evaluated prop is logged (skips logged ones)
    book = tier.book_scan(leagues, date, days=days)
    p = Path(out) / "meta" / "regular.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(regular(pp, now), separators=(",", ":")))
    written.append(("meta", "regular", str(p)))
    import concurrent.futures as cf
    cards = {}
    for source, rows in (("pp", pp), ("book", book)):
        for lg in leagues:
            sel, w = _write_board(base, source, lg, [r for r in rows if r["league"] == lg], now,
                                  [r for r in errs if r.get("league") == lg] if source == "pp" else None)
            written += w
            for r in sel[:CARD_ROWS]:
                k = card_key(lg, r["player"], r["stat"], r.get("team", ""))
                if k not in cards:
                    home = (r.get("home") == r.get("team")) if r.get("home") else None
                    cards[k] = (lg, r["stat"], r.get("team", ""), r.get("opp", ""), r["player"],
                                (r.get("player_id") or r.get("aid")) if lg in ("NBA", "NFL") else None,
                                r.get("position", ""), home, tier.slate_day(r.get("start")) if r.get("start") else "", r.get("rungs") or {},
                                r.get("competition", "regular"))

    def make(item):
        k, args = item
        try:
            return k, build_card(*args)
        except Exception:
            return k, None
    with cf.ThreadPoolExecutor(6) as ex:
        built = {k: c for k, c in ex.map(make, cards.items()) if c}
    # pack the cards into documents under ~180 KB each (the store's limit is 256 KB)
    cdir = Path(out) / "cards"
    cdir.mkdir(parents=True, exist_ok=True)
    for lg in leagues:
        chunk, size, i = {}, 0, 0
        items = [(k, c) for k, c in built.items() if k.startswith(lg + "|")]
        for n, (k, c) in enumerate(items):
            s = len(json.dumps(c, separators=(",", ":")))
            if chunk and size + s > 180_000:
                p = cdir / f"{lg}-{i}.json"
                p.write_text(json.dumps({"league": lg, "cards": chunk}, separators=(",", ":")))
                written.append(("cards", f"{lg}-{i}", str(p)))
                chunk, size, i = {}, 0, i + 1
            chunk[k], size = c, size + s
        if chunk:
            p = cdir / f"{lg}-{i}.json"
            p.write_text(json.dumps({"league": lg, "cards": chunk}, separators=(",", ":")))
            written.append(("cards", f"{lg}-{i}", str(p)))
    return written


def export(out: str, days: int = 7, verify_it: bool = True) -> list[tuple[str, str, str]]:
    rows = L.read_bets()
    since = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    picks = [r for r in rows if r.get("date", "") >= since and r.get("status") != "void" and (_rating(r) or 0) >= 8]
    base = Path(out)
    written = []
    for r in picks:
        p = base / "picks" / f"{r['id']}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(pick_doc(r, rows, verify_it)))
        written.append(("picks", r["id"], str(p)))
    p = base / "meta" / "summary.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary(rows)))
    written.append(("meta", "summary", str(p)))
    return written
