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
        "start": st.group(1) if st else "", "status": r.get("status") or "pending",
        "result": _f(r.get("result_value")), "verdict": "", "warns": [], "lesson": "",
    }
    if verify_it and doc["status"] == "pending":
        from .verify import verify
        rep = verify(r, rows)
        doc["verdict"] = rep.verdict
        doc["warns"] = [f"{name}: {d}" for s, name, d in rep.checks if s in ("WARN", "FAIL")]
    return doc


def summary(rows: list[dict]) -> dict:
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
            "bands": [{"band": k, "hits": h, "n": n, "predicted": round(p / n, 3) if n else None} for k, (h, n, p) in bands.items()]}


def _row(r: dict, source: str) -> dict:
    """One compact row for the page's props explorer."""
    return {"pl": r["player"], "tm": r.get("team", ""), "op": r.get("opp", ""), "st": r["stat"], "ln": r["line"],
            "sd": ("More" if r["side"] == "over" else "Less") if source == "pp" else ("Over" if r["side"] == "over" else "Under"),
            "ty": r.get("odds_type", "") if source == "pp" else r.get("book", ""), "pr": r.get("price"),
            "p": round(r["p_final"], 4), "pm": round(r["p_market"], 4),
            "ph": None if r.get("p_hist") is None else round(r["p_hist"], 3), "n": r.get("hist_n", 0),
            "r": r["rating"], "t": r.get("start", "")}


def export_props(out: str, leagues=("NHL", "MLB", "NBA"), date: dt.date | None = None, days: int = 2) -> list[tuple[str, str, str]]:
    """boards/pp-<LG> (every PrizePicks line we could price) and boards/book-<LG> (sportsbook lines), each rated."""
    from . import tier
    written, base = [], Path(out) / "boards"
    base.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pp = [r for r in tier.scan(leagues, date, days=days) if "error" not in r and r.get("odds_type") != "demon"]
    book = tier.book_scan(leagues, date, days=days)
    for source, rows in (("pp", pp), ("book", book)):
        for lg in leagues:
            sel = sorted((r for r in rows if r["league"] == lg), key=lambda r: (-r["rating"], -r["p_final"]))[:700]
            doc = {"source": source, "league": lg, "updated": now, "rows": [_row(r, source) for r in sel]}
            p = base / f"{source}-{lg}.json"
            p.write_text(json.dumps(doc, separators=(",", ":")))
            written.append(("boards", f"{source}-{lg}", str(p)))
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
