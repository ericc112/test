"""Slips, boards and tout posts injected on the Eight-Plus Board: price each prop, log it, back-check it.

python -m edge inject FILE.json [--out RESULTS.json]

FILE is one `inbox` document read from the board's database: {id, kind, app, entry, props: [{player, sport, stat,
line, side, odds_type, price}]}. Each MLB, NHL or NBA prop is priced like a scan row (`tier.price_prop`), logged to
bets.csv (a slip's legs as the user's entry, anything else as a pass) so it is graded like every other prop, and run
through `edge verify`. RESULTS is what goes back into the document: status, and per prop the bets.csv id, rating,
chance, label and verdict, or the reason it could not be priced.
"""
from __future__ import annotations

import datetime as dt
import json

from . import learn as L
from . import tier
from .blend import rating


def process(doc: dict) -> dict:
    rows = L.read_bets()
    seen = {(b["event_id"], b["player"].lower(), b["market"], str(float(b["line"])) if b.get("line") else "", b["side"]): b["id"]
            for b in rows}
    nid = max(int(b["id"]) for b in rows if b["id"].isdigit()) + 1
    slip = doc.get("kind") == "slip"
    results, new_ids = [], []
    for i, p in enumerate(doc.get("props") or []):
        lg = (p.get("sport") or "").upper()
        try:
            line = float(p["line"]) if p.get("line") not in (None, "") else None
        except (TypeError, ValueError):
            line = None
        if lg not in tier.STATS:
            why = ("tennis match winner: priced at check-in with `edge tennis pre` (needs both prices)" if lg in ("TENNIS", "ATP", "WTA")
                   else f"{lg or 'unknown sport'}: no automatic pricer for this sport yet")
            results.append({"i": i, "status": "not priced", "why": why})
            continue
        r = tier.price_prop(lg, p.get("player", ""), p.get("stat", ""), line, p.get("side"), (p.get("odds_type") or "standard").lower())
        if "error" in r:
            results.append({"i": i, "status": "not priced", "why": r["error"]})
            continue
        gid = tier.grade_id({"league": lg, "team": r["team"], "start": r["start"], "event_id": r["event_id"]})
        key = (gid, r["player"].lower(), r["market_key"], str(float(line)), r["side"])
        if key in seen:
            bid = seen[key]
            old = next(b for b in rows if b["id"] == bid)
            if slip and old.get("status") == "pending" and old.get("action") != "user_entry":
                old["action"] = "user_entry"                        # the user played it: grade it as their entry
                old["entry_id"] = old.get("entry_id") or f"inject-{doc.get('id', '')}"
        else:
            bid = str(nid)
            nid += 1
            rows.append({"id": bid, "date": dt.date.today().isoformat(), "sport": lg.lower(), "event": f"{r['team']} vs {r['opp']}",
                         "event_id": gid, "player": r["player"], "player_id": r.get("player_id") or "", "market": r["market_key"],
                         "line": line, "side": r["side"], "book": f"{doc.get('app') or 'app'} {p.get('odds_type') or ''}".strip(),
                         "price": "", "entry_id": f"inject-{doc.get('id', '')}" if slip else "",
                         "p_model": "" if r["p_model"] is None else round(r["p_model"], 4),
                         "p_market": "" if r["p_market"] is None else round(r["p_market"], 4),
                         "p_hist": "" if r["p_hist"] is None else round(r["p_hist"], 4), "hist_n": r["hist_n"],
                         "p_final": round(r["p_final"], 4), "confidence": r["confidence"],
                         "action": "user_entry" if slip else ("lean" if r["rating"] >= 8 else "pass"),
                         "segment": f"{lg.lower()}:{r['market_key']}:{r['side']}", "group": f"{lg.lower()}:{r['event_id']}",
                         "status": "pending", "proj": "" if r.get("proj") is None else r["proj"],
                         "notes": f"inject {doc.get('id', '')} ({doc.get('kind') or 'post'}, {doc.get('app') or 'app'}: "
                                  f"{p.get('player')} {p.get('side')} {p.get('line')} {p.get('stat')}); {r['notes']}; start {r['start']}"})
            seen[key] = bid
            new_ids.append(bid)
        results.append({"i": i, "status": "logged", "id": bid, "player": r["player"], "stat": r["stat"], "line": line,
                        "side": r["side"], "rating": r["rating"], "p": round(r["p_final"], 4), "confidence": r["confidence"],
                        "p_market": None if r["p_market"] is None else round(r["p_market"], 4), "proj": r.get("proj")})
    L.write_bets(rows)
    from .verify import verify
    rows = L.read_bets()
    by = {b["id"]: b for b in rows}
    for res in results:
        if res.get("id") in by:
            b = by[res["id"]]                                       # report the logged numbers, the ones verify checked
            pm = float(b["p_market"]) if b.get("p_market") else None
            res.update(p=float(b["p_final"]), confidence=b["confidence"], p_market=pm,
                       rating=rating(float(b["p_final"]), b["confidence"], pm))
            rep = verify(b, rows)
            res["verdict"] = rep.verdict
            res["warns"] = [f"{n}: {d}" for s, n, d in rep.checks if s in ("WARN", "FAIL")]
    return {"id": doc.get("id"), "status": "logged", "processed": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "results": results, "new_ids": new_ids}


def cli(path: str, out: str | None = None) -> dict:
    with open(path) as f:
        doc = json.load(f)
    doc = doc.get("data", doc)                                      # an ArtifactData read wraps the body in {id, data}
    res = process(doc)
    if out:
        with open(out, "w") as f:
            json.dump(res, f)
    return res
