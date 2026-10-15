"""The user's takes: props tapped "Take" on the Eight-Plus Board (db `takes/<id>`). From 10/15 these are what the
reports track; every other prop is still logged quietly for calibration.

python -m edge takes DIR --out RES.json
DIR holds the takes/*.json documents read from the board's database. Each take is linked to its row in bets.csv (the
scan logs most board props), marked as the user's entry (`take-<id>`), or logged through `edge inject` when no row
exists. RES maps each take to the fields written back: bets_id, status (pending / won / lost / push / void), result,
rating and chance.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re

from . import learn as L
from .blend import rating


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _market(lg: str, stat: str) -> str | None:
    from .tier import canon_stat, market_key
    if re.search(r"match ?winner|^ml", stat or "", re.I):
        return "ml"
    return market_key(lg, stat) or market_key(lg, canon_stat(lg, stat) or "")


def match_row(rows: list[dict], t: dict) -> dict | None:
    """The bets.csv row for a take: same sport, player, market, line and side, on the take's slate."""
    from .tier import name_match, slate_day
    if t.get("bets_id"):
        return next((r for r in rows if r["id"] == str(t["bets_id"])), None)
    lg = (t.get("lg") or "").upper()
    mk = _market(lg, t.get("stat", ""))
    side = "over" if re.match(r"(?i)more|over|to win", t.get("side") or "") else "under"
    day = slate_day(t.get("start")) if t.get("start") else (t.get("created") or "")[:10]
    best = None
    for r in rows:
        if r.get("sport") != lg.lower() or not name_match(t.get("player", ""), r.get("player", "")):
            continue
        if mk == "ml":
            if not r.get("market", "").startswith("ml"):
                continue
        elif r.get("market") != mk or _f(r.get("line")) != _f(t.get("line")) or r.get("side") != side:
            continue
        m = re.search(r"start (\S+)", r.get("notes", ""))
        rday = slate_day(m.group(1)) if m else r.get("date", "")
        if day and rday and rday != day:
            continue
        if best is None or int(r["id"]) < int(best["id"]):            # the first logged row is the record
            best = r
    return best


def process(docs: list[dict]) -> dict:
    """{take id: fields to write back}. Links or logs every take, then reads its status from bets.csv."""
    from . import inject
    rows = L.read_bets()
    out, to_inject = {}, []
    for t in docs:
        r = match_row(rows, t)
        if r is None:
            to_inject.append(t)
            continue
        if r.get("action") != "user_entry" or not r.get("entry_id"):
            r["action"], r["entry_id"] = "user_entry", r.get("entry_id") or f"take-{t['id']}"
        out[t["id"]] = r["id"]
    L.write_bets(rows)
    for t in to_inject:                                             # not on the log yet: price and log it like a slip leg
        res = inject.process({"id": t["id"], "kind": "slip", "app": "PrizePicks", "props": [{
            "player": t.get("player"), "sport": t.get("lg"), "stat": t.get("stat"), "line": t.get("line"), "side": t.get("side"),
            "odds_type": t.get("ty") or "standard", "team": t.get("tm"), "opponent": t.get("op")}]}, entry_prefix="take")
        got = next((x for x in res["results"] if x.get("id")), None)
        if got:
            out[t["id"]] = got["id"]
        else:
            out[t["id"]] = None
            out.setdefault("_errors", {})[t["id"]] = next((x.get("why") for x in res["results"]), "not priced")
    by = {r["id"]: r for r in L.read_bets()}
    from . import review as R
    pms = R.read_pm()
    res = {}
    for tid, bid in out.items():
        if tid == "_errors":
            continue
        b = by.get(bid) if bid else None
        if not b:
            res[tid] = {"status": "unlogged", "why": out.get("_errors", {}).get(tid, "not found")}
            continue
        p, pm = _f(b.get("p_final")), _f(b.get("p_market"))
        res[tid] = {"bets_id": b["id"], "status": b.get("status", "pending"), "result": _f(b.get("result_value")),
                    "rating": rating(p, b.get("confidence"), pm) if p is not None else None, "p": p,
                    "checked": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        if b.get("status") == "lost":                                # the post-mortem rides along: what happened, why, what changes
            pmr = pms.get(b["id"], {})
            res[tid].update({"tag": b.get("miss_reason") or pmr.get("auto_tag") or "", "lesson": pmr.get("lesson", ""),
                             "detail": (pmr.get("detail") or "")[:400]})
    return res


def record(rows: list[dict] | None = None) -> dict:
    """The user's takes, graded: hits, decided, by rating band."""
    rows = L.read_bets() if rows is None else rows
    t = [r for r in rows if str(r.get("entry_id", "")).startswith("take-") and r.get("status") in ("won", "lost")]
    bands = {}
    for r in t:
        p, pm = _f(r.get("p_final")), _f(r.get("p_market"))
        rt = rating(p, r.get("confidence"), pm) if p is not None else 0
        k = "8-10" if rt >= 8 else "5-7" if rt >= 5 else "1-4"
        b = bands.setdefault(k, [0, 0])
        b[0] += r["status"] == "won"
        b[1] += 1
    return {"hits": sum(r["status"] == "won" for r in t), "n": len(t), "bands": {k: {"hits": h, "n": n} for k, (h, n) in bands.items()}}


def cli(folder: str, out: str | None = None) -> dict:
    docs = []
    for f in sorted(glob.glob(os.path.join(folder, "**", "*.json"), recursive=True)):
        with open(f) as fh:
            d = json.load(fh)
        d = d.get("data", d)
        if isinstance(d, dict) and d.get("player"):
            d.setdefault("id", os.path.basename(f)[:-5])
            docs.append(d)
    res = process(docs)
    if out:
        with open(out, "w") as fh:
            json.dump(res, fh)
    return res
