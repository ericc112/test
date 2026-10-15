"""Keep the Eight-Plus Board in step with PrizePicks between full scans: python -m edge refresh LIVE --out OUT

LIVE holds the page's documents as ArtifactData listed them (LIVE/boards/pp-<LG>.json, and LIVE/cards/*.json for the
cards already built). For each league the current PrizePicks board is read and compared prop by prop:
  same line                         kept as priced
  standard line moved               re-priced at the new line
  new prop (or a new goblin line)   priced
  pulled, or the game has started   dropped
Re-priced and new props are logged like scan rows (every evaluated prop is logged). The documents that changed are written
to OUT (boards/pp-<LG>.json, cards/<LG>-r.json for the new props' cards) with OUT/summary.json: counts per league and the
new or moved 8+ props, which need `edge verify` and a picks refresh before they show as picks. A fresh slate (more than
MAX_NEW new props in a league) is left to the full scan (`edge board --props`), which also rebuilds cards and regular lines.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import unicodedata
from pathlib import Path

TIER = ("NHL", "MLB", "NBA", "NFL")
EXTRA = ("CS2", "LOL", "VAL", "SOCCER")
MAX_NEW = 150


def _fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def _ty(t: str) -> str:
    return "goblin" if "goblin" in (t or "").lower() else "demon" if "demon" in (t or "").lower() else "standard"


def diff(rows: list[dict], props: list[dict]) -> dict:
    """rows: the board's compact rows (pl, st, ty, ln). props: today's PrizePicks props (player, stat, odds_type, line),
    already limited to games that haven't started. Returns {keep: rows, moved: props, new: props, gone: rows}.
    A standard line is one number per player and stat, so a different number is a move; goblin lines are separate props."""
    exact = {(_fold(r["pl"]), str(r["st"]).lower(), _ty(r.get("ty")), float(r["ln"])): r for r in rows}
    std = {k[:3]: r for k, r in exact.items() if k[2] == "standard"}
    keep, moved, new, seen = [], [], [], set()
    for p in props:
        k = (_fold(p["player"]), str(p["stat"]).lower(), _ty(p.get("odds_type")), float(p["line"]))
        if k in seen:
            continue
        seen.add(k)
        if k in exact:
            keep.append(exact[k])
        elif k[2] == "standard" and k[:3] in std:
            moved.append({**p, "old_line": std[k[:3]]["ln"]})
        else:
            new.append(p)
    kept = {id(r) for r in keep}
    moved_keys = {(_fold(p["player"]), str(p["stat"]).lower(), "standard") for p in moved}
    gone = [r for r in rows if id(r) not in kept and not (_ty(r.get("ty")) == "standard"
                                                            and (_fold(r["pl"]), str(r["st"]).lower(), "standard") in moved_keys)]
    return {"keep": keep, "moved": moved, "new": new, "gone": gone}


def board_props(lg: str, now: dt.datetime) -> list[dict]:
    """Today's standard and goblin props for a league, games not started; tier leagues only where we have a market."""
    from . import pp
    from . import tier
    boards = (lg, "NBAP") if lg == "NBA" else (lg,)
    out = []
    for b in boards:
        try:
            out += [{**p, "league": lg} for p in pp.board(b, ("standard", "goblin"))]
        except Exception:
            continue
    out = [p for p in out if p.get("start") and dt.datetime.fromisoformat(p["start"]) > now]
    if lg in TIER:
        out = [p for p in out if tier.market_key(lg, p["stat"])]
    return out


def price(lg: str, props: list[dict]) -> list[dict]:
    """Full rows (as the scans make them) for the props to (re)price."""
    if not props:
        return []
    if lg in EXTRA:
        from . import pp
        from .board import extra_row
        return [extra_row(r, lg) for r in pp.price_board(props) if "error" not in r]
    from . import tier
    rows = []
    for p in props:
        side = None if _ty(p.get("odds_type")) == "standard" else "over"        # goblins are More-only
        try:
            day = dt.datetime.fromisoformat(p["start"]).date()
            r = tier.price_prop(lg, p["player"], p["stat"], p["line"], side, _ty(p.get("odds_type")), day)
        except Exception as e:
            r = {"error": f"{type(e).__name__}"}
        if "error" not in r:
            rows.append({**r, "stat": p["stat"], "start": r.get("start") or p.get("start"), "team": p.get("team") or r.get("team"),
                         "opp": p.get("opp") or r.get("opp")})
    return rows


def log_rows(lg: str, rows: list[dict]) -> list[str]:
    from . import pp, tier
    if lg in EXTRA:
        return pp.log_rows(rows)
    return tier.log_rows(rows)


def run(live: str, out: str, leagues=TIER + EXTRA, log: bool = True) -> dict:
    from . import board as B
    from . import tier
    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    have_cards = set()
    for f in glob.glob(os.path.join(live, "cards", "*.json")):
        try:
            d = json.load(open(f))
        except ValueError:
            continue
        have_cards |= set((d.get("data", d).get("cards") or {}).keys())
    summary = {"updated": stamp, "leagues": {}, "eight_plus": [], "full_scan": []}
    Path(out, "boards").mkdir(parents=True, exist_ok=True)
    for lg in leagues:
        f = os.path.join(live, "boards", f"pp-{lg}.json")
        doc = json.load(open(f)) if os.path.exists(f) else {"rows": []}
        doc = doc.get("data", doc)
        known = B.load_state(lg)                                     # every line the last scan priced, trimmed ones too
        live_rows = [r for r in doc.get("rows", []) if not r.get("t") or dt.datetime.fromisoformat(r["t"]) > now]
        rows = [r for r in (known if known is not None else doc.get("rows", []))
                if not r.get("t") or dt.datetime.fromisoformat(r["t"]) > now]
        props = board_props(lg, now)
        if not props and not doc.get("rows"):
            continue
        d = diff(rows, props)
        if len(d["new"]) > MAX_NEW:
            summary["full_scan"].append(lg)
            summary["leagues"][lg] = {k: len(v) for k, v in d.items()}
            continue
        fresh = price(lg, d["moved"] + d["new"])
        if log and fresh:
            log_rows(lg, fresh)
        compact = [B._row(r, "pp") for r in fresh]
        merged = sorted(d["keep"] + compact, key=lambda r: (-(r.get("r") or 0), -(r.get("p") or 0)))
        B.save_state(lg, merged)
        merged = merged[:700]
        changed = bool(fresh or d["gone"] or len(live_rows) != len(doc.get("rows", [])))
        summary["leagues"][lg] = {"kept": len(d["keep"]), "moved": len(d["moved"]), "new": len(d["new"]),
                                  "priced": len(fresh), "dropped": len(d["gone"]), "state": known is not None}
        summary["eight_plus"] += [{"lg": lg, "player": r["player"], "stat": r["stat"], "line": r["line"], "side": r["side"],
                                   "odds_type": r.get("odds_type"), "rating": r["rating"], "p": r["p_final"]}
                                  for r in fresh if r.get("rating", 0) >= 8]
        if not changed:
            continue
        new_doc = {"source": "pp", "league": lg, "updated": stamp, "rows": merged}
        while len(json.dumps(new_doc, separators=(",", ":")).encode()) > 250_000:
            new_doc["rows"] = new_doc["rows"][:-25]
        Path(out, "boards", f"pp-{lg}.json").write_text(json.dumps(new_doc, separators=(",", ":")))
        # cards for new props that have none yet, merged with the refresh cards already on the page
        rf = os.path.join(live, "cards", f"{lg}-r.json")
        old = json.load(open(rf)) if os.path.exists(rf) else {}
        cards = dict((old.get("data", old).get("cards") or {}))
        on_board = {r.get("ck") for r in new_doc["rows"]}
        cards = {k: v for k, v in cards.items() if k in on_board}
        for r in fresh:
            k = B.card_key(lg, r["player"], r["stat"], r.get("team", ""))
            if k in have_cards and k not in cards:
                continue
            try:
                if lg in EXTRA:
                    c = B.history_card(r, lg) if r.get("games") else None
                else:
                    home = (r.get("home") == r.get("team")) if r.get("home") else None
                    c = B.build_card(lg, r["stat"], r.get("team", ""), r.get("opp", ""), r["player"],
                                     (r.get("player_id") or r.get("aid")) if lg in ("NBA", "NFL") else None, r.get("position", ""),
                                     home, tier.slate_day(r["start"]) if r.get("start") else "", {}, r.get("competition", "regular"))
            except Exception:
                c = None
            if c:
                cards[k] = c
        if cards:
            Path(out, "cards").mkdir(parents=True, exist_ok=True)
            body = {"league": lg, "cards": cards}
            while len(json.dumps(body, separators=(",", ":")).encode()) > 240_000 and body["cards"]:
                body["cards"].pop(next(iter(body["cards"])))
            Path(out, "cards", f"{lg}-r.json").write_text(json.dumps(body, separators=(",", ":")))
    Path(out, "summary.json").write_text(json.dumps(summary, indent=1))
    return summary
