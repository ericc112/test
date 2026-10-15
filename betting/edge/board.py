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
               home: bool | None = None, date: str = "") -> dict:
    """The prop card: last games (opponent, home/away, value), averages, head-to-head, venue split, matchup rank."""
    from . import tier
    from . import context as CX
    from . import lowline as LW
    games = tier.card_games(lg, stat, team, player, aid)
    vals = [g["v"] for g in games]
    norm = lambda a: tier.NHL_API.get(tier.espn_team(lg, a or ""), tier.espn_team(lg, a or ""))
    h2h = [g["v"] for g in games if opp and norm(g["o"]) == norm(opp)]
    hm, aw = [g["v"] for g in games if g["h"] is True], [g["v"] for g in games if g["h"] is False]
    pid = aid
    if lg == "MLB":
        try:
            pid = LW.mlb_player(team, player)
        except Exception:
            pid = None
    return {"pl": player, "pos": position, "tm": team, "op": opp, "st": stat,
            "g": [{"d": g["d"][5:], "o": g["o"], "h": g["h"], "v": g["v"]} for g in games[:15]],
            "a5": _avg(vals[:5]), "a10": _avg(vals[:10]), "aN": _avg(vals), "n": len(vals),
            "h2h": {"avg": _avg(h2h), "n": len(h2h)}, "home": {"avg": _avg(hm), "n": len(hm)}, "away": {"avg": _avg(aw), "n": len(aw)},
            "tonight": "home" if home is True else "away" if home is False else "",
            "mu": CX.matchup(lg, stat, opp, pid, team, date)}


def pick_doc(r: dict, rows: list[dict], verify_it: bool) -> dict:
    notes = r.get("notes", "")
    m = re.search(r"DK (\d+)\+ ([+-]\d+)", notes)
    st = re.search(r"start (\d{4}-\d\d-\d\dT[\d:.]+[+-]\d\d:\d\d)", notes)
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
    if doc["proj"] is None and doc["status"] == "pending":       # rows logged before projections: price the matchup now
        from . import context as CX
        cx = CX.price(doc["sport"], stat, doc["opp"], r.get("player_id"), doc["line"], int(r["date"][:4])) if stat else None
        if cx:
            doc["proj"], doc["context"] = round(cx[2], 1), doc["context"] or cx[1]
    if stat and doc["status"] == "pending":
        try:
            doc["card"] = build_card(doc["sport"], stat, doc["team"], doc["opp"], r["player"],
                                     r.get("player_id") if doc["sport"] in ("NBA", "NFL") else None, date=r["date"])
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
    bands = {"8-10": [0, 0, 0.0], "5-7": [0, 0, 0.0], "1-4": [0, 0, 0.0]}
    for r in rows:
        if r.get("status") not in ("won", "lost"):
            continue
        rt = _rating(r)
        if rt is None:
            continue
        b = bands["8-10" if rt >= 8 else "5-7" if rt >= 5 else "1-4"]
        b[0] += r["status"] == "won"
        b[1] += 1
        b[2] += _f(r["p_final"])
    return {"updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "regular": {"hits": sum(r["status"] == "won" for r in reg), "n": len(reg), "min": REG_MIN,
                        "predicted": round(sum(_f(r["p_final"]) for r in reg) / len(reg), 3) if reg else None},
            "bands": [{"band": k, "hits": h, "n": n, "predicted": round(p / n, 3) if n else None} for k, (h, n, p) in bands.items()]}


def _row(r: dict, source: str) -> dict:
    """One compact row for the page's props explorer."""
    return {"pl": r["player"], "tm": r.get("team", ""), "op": r.get("opp", ""), "st": r["stat"], "ln": r["line"],
            "sd": ("More" if r["side"] == "over" else "Less") if source == "pp" else ("Over" if r["side"] == "over" else "Under"),
            "ty": r.get("odds_type", "") if source == "pp" else r.get("book", ""), "pr": r.get("price"),
            "p": round(r["p_final"], 4), "pm": round(r["p_market"], 4),
            "ph": None if r.get("p_hist") is None else round(r["p_hist"], 3), "n": r.get("hist_n", 0),
            "r": r["rating"], "t": r.get("start", ""), "cx": r.get("context") or [],
            "pj": r.get("proj"), "pjs": r.get("proj_src", ""), "a10": r.get("avg10"),
            "ck": card_key(r["league"], r["player"], r["stat"], r.get("team", "")),
            "pmod": None if r.get("p_model") is None else round(r["p_model"], 3)}


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
            d["why"] = "sources disagree"
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


def export_props(out: str, leagues=("NHL", "MLB", "NBA"), date: dt.date | None = None, days: int = 2) -> list[tuple[str, str, str]]:
    """boards/pp-<LG> (every PrizePicks line we could price) and boards/book-<LG> (sportsbook lines), each rated."""
    from . import tier
    written, base = [], Path(out) / "boards"
    base.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pp = [r for r in tier.scan(leagues, date, days=days) if "error" not in r and r.get("odds_type") != "demon"]
    book = tier.book_scan(leagues, date, days=days)
    p = Path(out) / "meta" / "regular.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(regular(pp, now), separators=(",", ":")))
    written.append(("meta", "regular", str(p)))
    import concurrent.futures as cf
    cards = {}
    for source, rows in (("pp", pp), ("book", book)):
        for lg in leagues:
            sel = sorted((r for r in rows if r["league"] == lg), key=lambda r: (-r["rating"], -r["p_final"]))[:700]
            doc = {"source": source, "league": lg, "updated": now, "rows": [_row(r, source) for r in sel]}
            p = base / f"{source}-{lg}.json"
            p.write_text(json.dumps(doc, separators=(",", ":")))
            written.append(("boards", f"{source}-{lg}", str(p)))
            for r in sel:
                k = card_key(lg, r["player"], r["stat"], r.get("team", ""))
                if k not in cards:
                    home = (r.get("home") == r.get("team")) if r.get("home") else None
                    cards[k] = (lg, r["stat"], r.get("team", ""), r.get("opp", ""), r["player"],
                                r.get("player_id") if lg in ("NBA", "NFL") else None, r.get("position", ""), home,
                                (r.get("start") or "")[:10])

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
