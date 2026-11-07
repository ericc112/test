"""Tennis matches for the Sim Lab's match simulator (ATP and WTA): the next two days on Tennis Explorer, each player's
serve-point probability against that opponent from the opponent-adjusted ratings the tennis pricer uses
(edge/tennis.py, TennisMyLife match database), the tour's measured day-to-day form, Elo, the market's de-vigged winner
price and the serve-point shift that matches it, and any PrizePicks lines on the match. The page plays these point by
point (index.html, tnMatch / tnLiveP).

Only players with stats-covered matches in the last 52 weeks are simulated (Futures, UTR and most ITF players aren't
in the database); the rest are counted, not guessed."""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import re
import unicodedata
from zoneinfo import ZoneInfo

import numpy as np

from .blend import HERE

TE_TZ = ZoneInfo("Europe/Prague")      # Tennis Explorer lists times in Central European time (checked 2026-11-07:
                                       # Rybakina v Noskova 21:00 there, 15:00 EST on PrizePicks)
MIN_MS = 5                             # stats-covered matches in 52 weeks, each player
THIN_MS = 8                            # below this the card says the sample is thin (the pricer keeps such legs off its lists)


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


def _te_name(n: str) -> tuple[str, str]:
    """'Davidovich Fokina A.' -> ('davidovichfokina', 'a')."""
    from .tennis_market import surname_key
    m = re.search(r"\s([A-Za-z])\.(\s*[A-Za-z]\.)*\s*$", n.strip())
    return surname_key(n), (_ascii(m.group(1)) if m else "")


def _index(st: dict, tour: str) -> tuple[dict, dict]:
    """(surname key, first initial) -> [(player id, hand)], and player id -> display name, from the database."""
    full, hand = {}, {}
    for m in st["matches"]:
        if m["tour"] == tour:
            full[m["w"]], hand[m["w"]] = m["w_name"], m["w_hand"]
            full[m["l"]], hand[m["l"]] = m["l_name"], m["l_hand"]
    idx = {}
    for pid, nm in full.items():
        w = _ascii(nm).split()
        if len(w) < 2:
            continue
        for k in (1, 2, 3):
            if len(w) > k:
                idx.setdefault((re.sub(r"[^a-z]", "", "".join(w[-k:])), w[0][0]), []).append((pid, hand.get(pid) or "R"))
    return idx, full


def _surface(st: dict, tour: str, tourn: str, day: dt.date) -> tuple[str, bool, str | None]:
    """(surface, confirmed, event name): this week's matches of the event in the database, then
    data/tennis_events.json; otherwise hard (every tour event in November is on hard courts), marked unconfirmed."""
    key = re.sub(r"\b(challenger|wta|atp|itf|open|cup)\b|[^a-z ]", " ", _ascii(tourn)).split()
    if key:
        cut = int((day - dt.timedelta(days=14)).strftime("%Y%m%d"))
        for m in reversed(st["matches"]):
            if m["tour"] == tour and m["date"] >= cut and all(k in _ascii(m.get("tname") or "") for k in key[:2]):
                return m["surface"], True, m.get("tname")
    ev_path = os.path.join(HERE, "data", "tennis_events.json")
    if os.path.exists(ev_path):
        for e in json.load(open(ev_path)):
            names = {_ascii(e["tourn"]), "masters cup"} if "finals" in e["tourn"].lower() else {_ascii(e["tourn"])}
            if e["tour"] == tour and any(n in _ascii(tourn) for n in names):
                return e["surface"], True, e["tourn"]
    return "Hard", False, None


def _pp_lines(day: dt.date) -> dict:
    """{frozenset of the two surnames: [lines]} from the priced PrizePicks tennis board (data/tennis_boards)."""
    out = {}
    for d in (day, day - dt.timedelta(days=1)):
        p = os.path.join(HERE, "data", "tennis_boards", f"{d.isoformat()}.json.gz")
        if not os.path.exists(p):
            continue
        for r in json.load(gzip.open(p, "rt")):
            g = r.get("game") or ""
            if " vs " not in g:
                continue
            a, b = (x.strip() for x in g.split(" vs ", 1))
            k = frozenset(re.sub(r"[^a-z]", "", _ascii(x.split()[-1])) for x in (a, b))
            out.setdefault(k, []).append({"player": r.get("player"), "stat": r.get("stat"), "line": r.get("line"), "side": r.get("side"),
                                          "p": r.get("p_final"), "conf": r.get("confidence")})
    return out


def _short_wta(st: dict, rows: list[dict], pp: dict) -> list[str]:
    """Full names of WTA players in these schedule rows with fewer than MIN_MS stats-covered matches in 52 weeks in the
    database (or not in it, when the PrizePicks board names them), for the WTA 125 top-up."""
    idx, full = _index(st, "WTA")
    T_ = st["WTA"]; oi, obs, cut = T_["obs"]["idx"], T_["obs"], dt.date.today().toordinal() - 365
    board = {}
    for lines in pp.values():
        for l in lines:
            if l.get("player"):
                w = _ascii(l["player"]).split()
                if len(w) >= 2:
                    board[(re.sub(r"[^a-z]", "", w[-1]), w[0][0])] = l["player"]
    names = []
    for x in rows:
        if not x.get("p2") or re.search(r"\b(itf|utr)\b", _ascii(x.get("tourn") or "")):   # WTA 125s exist only for tour-level players
            continue
        for nm in (x["p1"], x["p2"]):
            key, ini = _te_name(nm)
            cand = idx.get((key, ini)) or []
            best = max((int(((obs["srv"] == oi[pid]) & (obs["day"] >= cut)).sum()) for pid, _ in cand if pid in oi), default=None)
            if best is not None and best >= MIN_MS:
                continue
            full_name = next((full[pid] for pid, _ in cand if pid in full), None) or board.get((key, ini))
            if full_name and full_name not in names:
                names.append(full_name)
    return names


def export(days: int = 2, now: dt.datetime | None = None, log=print) -> dict:
    from . import tennis as T, tennis_hist as TH, tennis_market as TM
    now = now or dt.datetime.now(dt.timezone.utc)
    st = T.tml_state()
    if not st:
        return {"matches": [], "note": "match database not available"}
    dec = json.load(open(T.DECISION)) if os.path.exists(T.DECISION) else {}
    d0 = now.astimezone(TE_TZ).date()
    pp = _pp_lines(d0)
    sched = {}
    for tour in ("ATP", "WTA"):
        for k in range(days):
            d = d0 + dt.timedelta(days=k)
            try:
                sched[(tour, d)] = TM.day(d, tour, T.TE_DIR, max_age=1800, upcoming=True)
            except Exception as e:
                log(f"  tennis watch: {tour} {d} not read ({type(e).__name__})")
    # WTA players short of matches in the tour-level database: add their WTA 125 matches from the WTA's feed, as the
    # tennis pricer does (tennis.tml_state wta_topup); full names from the database or the PrizePicks board
    short = _short_wta(st, [x for (t, _), rows in sched.items() if t == "WTA" for x in rows], pp)
    if short:
        log(f"  tennis watch: WTA 125 top-up for {len(short)} player(s): {', '.join(short[:6])}{'...' if len(short) > 6 else ''}")
        st = T.tml_state(wta_topup=tuple(short)) or st
    out, skipped = [], {"ATP": 0, "WTA": 0}
    for tour in ("ATP", "WTA"):
        T_ = st[tour]
        idx, full = _index(st, tour)
        oi, R = T_["obs"]["idx"], T_["R"]
        obs, cut = T_["obs"], dt.date.today().toordinal() - 365
        E, Es, _ = T_["elo"]
        form = (T_["study"].get("form") or {}).get("B1") or {"sd": 0.05, "rho": -0.8}
        anchor = (dec.get(tour) or {}).get("anchor") == "market"
        for k in range(days):
            d = d0 + dt.timedelta(days=k)
            rows = sched.get((tour, d)) or []
            for x in rows:
                if not x.get("p2") or not re.match(r"^\d\d:\d\d$", x.get("time") or ""):
                    continue
                start = dt.datetime.combine(d, dt.time.fromisoformat(x["time"]), TE_TZ)
                if start < now - dt.timedelta(hours=3):
                    continue
                pl = []
                for nm in (x["p1"], x["p2"]):
                    key, ini = _te_name(nm)
                    cand = idx.get((key, ini)) or []
                    best = None
                    for pid, hand in cand:
                        i = oi.get(pid)
                        if i is None:
                            continue
                        ms = int(((obs["srv"] == i) & (obs["day"] >= cut)).sum())
                        if not best or ms > best[2]:
                            best = (pid, hand, ms, i)
                    pl.append(best)
                if not all(pl) or min(p[2] for p in pl) < MIN_MS:
                    skipped[tour] += 1
                    continue
                (ia, ha, msa, a), (ib, hb, msb, b) = pl
                surf, confirmed, ev = _surface(st, tour, x["tourn"] or "", d)
                s_ = surf if surf in ("Hard", "Clay", "Grass") else "Hard"
                p1, p2 = R.p(a, b, s_, None, ha, hb), R.p(b, a, s_, None, hb, ha)
                bo = 3
                win_model = float(TH.match_win_form(p1, p2, bo, form["sd"], form["rho"])[0])
                fair = TM.fair(x.get("o1"), x.get("o2"))
                shift = float(TH.shift_to(np.array([p1]), np.array([p2]), fair, bo, form["sd"], form["rho"])[0]) if fair else None
                ra = 0.5 * (E.get(ia, 1500) + Es.get((ia, s_), 1500)); rb = 0.5 * (E.get(ib, 1500) + Es.get((ib, s_), 1500))
                na, nb = full.get(ia, x["p1"]), full.get(ib, x["p2"])
                k2 = frozenset(re.sub(r"[^a-z]", "", _ascii(n.split()[-1])) for n in (na, nb))
                out.append({"id": f"{tour}-{d.isoformat()}-{x.get('slug1')}-{x.get('slug2')}", "tour": tour, "tourn": x["tourn"], "event": ev,
                            "surface": surf, "surface_confirmed": confirmed, "best_of": bo, "tb10": False,
                            "start": start.isoformat(), "a": na, "b": nb, "a_te": x["p1"], "b_te": x["p2"],
                            "pa": round(p1, 4), "pb": round(p2, 4), "sd": form["sd"], "rho": form["rho"],
                            "ms_a": msa, "ms_b": msb, "thin": min(msa, msb) < THIN_MS,
                            "odds": [x.get("o1"), x.get("o2")], "market_a": round(fair, 4) if fair else None,
                            "shift": round(shift, 4) if shift is not None else None, "anchor_default": bool(anchor and fair),
                            "win_model": round(win_model, 4), "elo_a": round(1 / (1 + 10 ** ((rb - ra) / 400)), 4),
                            "lines": pp.get(k2, [])})
    out.sort(key=lambda m: (m["start"], m["tour"]))
    note = (f"{len(out)} matches simulated; not simulated (players without enough stats-covered matches in 52 weeks, "
            f"mostly Futures, UTR and ITF): ATP {skipped['ATP']}, WTA {skipped['WTA']}")
    log("  tennis watch: " + note)
    return {"matches": out, "pulled": now.strftime("%Y-%m-%dT%H:%MZ"), "note": note, "skipped": skipped,
            "decision": {t: (dec.get(t) or {}).get("anchor") for t in ("ATP", "WTA")}}
