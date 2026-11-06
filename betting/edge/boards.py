"""Every priced PrizePicks leg of the day, per sport, for the Sim Lab's label filter (edge boards --page boards.js).

Reads the full priced boards each pricer saves (data/{sport}_boards/DATE.json.gz), joins the ledger (a leg logged in
bets.csv gets its id) and the day's published lists (data/picks/DATE-{sport}.json: the back-check result of each
listed leg). Goblin lines are left out (user, 2026-11-06). A leg that was never back-checked is shown as such: it is a price, not a pick, until `edge verify` passes
it (CLAUDE.md)."""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import os

from .blend import HERE

SPORTS = ("nba", "nfl", "nhl", "tennis")
BE_STANDARD = 0.577          # PrizePicks 2-pick power, per leg; goblin and demon payouts aren't published


def _label(sport: str, r: dict) -> str:
    if r.get("stat"):
        return r["stat"]
    if sport == "nba":
        from .nba_pp import LABEL
        return LABEL.get(r.get("market_key") or r.get("stat_key"), r.get("market_key"))
    return r.get("market_key") or ""


def _verified(date: str) -> dict:
    """{bet id: back-check result} for every leg on the day's published lists."""
    out = {}
    for sp in SPORTS:
        path = os.path.join(HERE, "data", "picks", f"{date}-{sp}.json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        lists = [d.get(k) or [] for k in ("model", "history", "likely")]
        for day in d.get("days") or []:
            lists += [day.get(k) or [] for k in ("model", "history", "likely")]
        for L in lists:
            for c in L:
                if c.get("id") and c.get("verified"):
                    out[str(c["id"])] = (c["verified"], c.get("warns") or [])
    return out


def export(date: str | None = None) -> dict:
    date = date or dt.date.today().isoformat()
    bets = list(csv.DictReader(open(os.path.join(HERE, "data", "bets.csv"))))
    key = lambda e, p, l, s: (str(e), str(p).lower(), round(float(l), 2), s)
    logged = {}
    for b in bets:
        try:
            logged.setdefault(key(b["event_id"], b["player"], b["line"], b["side"]), b)
        except (TypeError, ValueError):
            continue
    ver = _verified(date)
    out = {"date": date, "be_standard": BE_STANDARD, "sports": {}}
    for sp in SPORTS:
        path = os.path.join(HERE, "data", f"{sp}_boards", f"{date}.json.gz")
        if not os.path.exists(path):
            continue
        rows = []
        for r in json.load(gzip.open(path, "rt")):
            if r.get("p_final") is None or not r.get("side") or r.get("odds_type") == "goblin":   # user: no goblin lines
                continue
            b = logged.get(key(r.get("event_id"), r.get("player"), r.get("line"), r.get("side")))
            v = ver.get(b["id"]) if b else None
            t = r.get("odds_type") or "standard"
            rows.append({"player": r.get("player"), "team": r.get("team"), "game": r.get("game"), "stat": _label(sp, r), "side": r["side"],
                         "line": r.get("line"), "type": t, "p": round(float(r["p_final"]), 4), "conf": r.get("confidence"),
                         "model": None if r.get("p_model") is None else round(float(r["p_model"]), 3),
                         "market": None if r.get("p_market") is None else round(float(r["p_market"]), 3),
                         "be": BE_STANDARD if t == "standard" else None, "start": r.get("start"),
                         "id": b["id"] if b else None, "verified": v[0] if v else None, "warns": v[1] if v else []})
        out["sports"][sp] = rows
    return out
