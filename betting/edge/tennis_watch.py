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


def _scout(scout, ia, na, ib, nb, surface=None, event=None):
    """Both players' scouting cards (the core lines every player shows, the stand-out notes, form, schedule and record),
    the head-to-head and the matchup notes (edge/tennis_scout.py), or None."""
    if not scout:
        return None
    from . import tennis_scout as TS
    try:
        ca, cb = scout.card(ia, na, surface, event), scout.card(ib, nb, surface, event)
        hh = TS.h2h(scout.byp, ia, ib, surface)
        for x in hh["meetings"]:
            x["winner"] = "a" if x["winner"] == ia else "b"
        return {"a": TS.compact(ca), "b": TS.compact(cb), "matchup": TS.matchup(ca, cb), "h2h": hh}
    except Exception as e:
        print(f"  tennis watch: scouting card failed for {na} v {nb} ({type(e).__name__}: {e})")
        return None


SHADOW_DIR = os.path.join(HERE, "data", "tennis_shadow")


def _shadow(st, out, queue, log=print) -> None:
    """The winner model in testing (user, 2026-11-11): the ratings plus the factors that passed the walk-forward test
    (data/tennis_bt/winner_factors.json, "shadow" per tour). Shown on the page as "in testing", never used for a pick,
    and logged to data/tennis_shadow/<date>.json so `python -m edge.tennis_winner_factors report` grades it against the
    ratings and the market. Promotion needs 200+ graded matches or 14 days, better on log loss and calibration."""
    from . import tennis_winner_factors as TW
    try:
        res = json.load(open(TW.OUT))
    except (OSError, ValueError):
        return
    by_tour = {}
    for item in queue:
        by_tour.setdefault(item[1], []).append(item)
    now = dt.datetime.now(dt.timezone.utc)
    logs = {}
    for tour, items in by_tour.items():
        model = (res.get(tour) or {}).get("shadow")
        if not model:
            continue
        F = TW.features(st["matches"], tour, [(i, ia, ib, s_, ev, ha, hb, day) for i, (_m, _t, ia, ib, s_, ev, ha, hb, day) in enumerate(items)])
        for i, item in enumerate(items):
            m, f = item[0], F.get(i)
            if not f:
                continue
            p = TW.shadow_p(model, m["win_model"], f["a"], f["b"], f["elo"])
            m["shadow"] = {"p_a": round(p, 4), "name": model.get("name", "ratings + factors")}
            day = dt.datetime.fromisoformat(m["start"]).astimezone(TE_TZ).date().isoformat()
            logs.setdefault(day, {})[m["id"]] = {"tour": tour, "a": m["a"], "b": m["b"], "a_te": m.get("a_te"), "b_te": m.get("b_te"),
                                                 "slugs": m.get("slugs"), "start": m["start"], "p_ratings": m["win_model"],
                                                 "p_market": m.get("market_a"), "p_shadow": round(p, 4), "logged": now.strftime("%Y-%m-%dT%H:%MZ")}
    os.makedirs(SHADOW_DIR, exist_ok=True)
    for day, recs in logs.items():
        path = os.path.join(SHADOW_DIR, f"{day}.json")
        cur = json.load(open(path)) if os.path.exists(path) else {}
        for k, v in recs.items():
            if k not in cur or dt.datetime.fromisoformat(v["start"]) > now:     # keep the last pre-match number
                cur[k] = v
        json.dump(cur, open(path, "w"), indent=0)
    n = sum(len(v) for v in logs.values())
    if n:
        log(f"  tennis watch: shadow winner model scored {n} matches (in testing, not published)")


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
    out, skipped, shadow_q = [], {"ATP": 0, "WTA": 0}, []
    from . import tennis_scout as TS
    try:
        TS.download()                       # the Match Charting Project files (weekly)
    except Exception as e:
        log(f"  tennis watch: charting files not refreshed ({type(e).__name__})")
    for tour in ("ATP", "WTA"):
        T_ = st[tour]
        try:
            scout = TS.Scout(st, tour)
        except Exception as e:
            scout = None
            log(f"  tennis watch: {tour} scouting not built ({type(e).__name__}: {str(e)[:60]})")
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
                            "slugs": [x.get("slug1"), x.get("slug2")], "odds": [x.get("o1"), x.get("o2")], "market_a": round(fair, 4) if fair else None,
                            "shift": round(shift, 4) if shift is not None else None, "anchor_default": bool(anchor and fair),
                            "win_model": round(win_model, 4), "elo_a": round(1 / (1 + 10 ** ((rb - ra) / 400)), 4),
                            "lines": pp.get(k2, []), "scout": _scout(scout, ia, na, ib, nb, surf, ev),
                            "likely": {"ratings": likely_match(p1, p2, bo, win_model, form["sd"], form["rho"]),
                                       **({"market": likely_match(p1 + shift, p2 - shift, bo, fair, form["sd"], form["rho"])} if shift is not None else {})}})
                shadow_q.append((out[-1], tour, ia, ib, s_, ev or x["tourn"] or "", ha, hb, d.toordinal()))
    _shadow(st, out, shadow_q, log)
    out.sort(key=lambda m: (m["start"], m["tour"]))
    try:
        save_winners(out)
    except Exception as e:
        log(f"  tennis watch: winners not saved ({type(e).__name__})")
    note = (f"{len(out)} matches simulated; not simulated (players without enough stats-covered matches in 52 weeks, "
            f"mostly Futures, UTR and ITF): ATP {skipped['ATP']}, WTA {skipped['WTA']}")
    log("  tennis watch: " + note)
    return {"matches": out, "pulled": now.strftime("%Y-%m-%dT%H:%MZ"), "note": note, "skipped": skipped,
            "decision": {t: (dec.get(t) or {}).get("anchor") for t in ("ATP", "WTA")}}

# ------------------------------------------------------------------ projected scoreline (the Winners tab)
def _hold(p: float) -> float:
    d = p * p / (p * p + (1 - p) * (1 - p))
    return p ** 4 * (1 + 4 * (1 - p) + 10 * (1 - p) ** 2) + 20 * p ** 3 * (1 - p) ** 3 * d


def _tiebreak(pa: float, pb: float, first: int) -> float:
    """A's chance to win a 7-point tiebreak, `first` (0 = A) serving the first point, then two each."""
    from functools import lru_cache
    @lru_cache(None)
    def f(x, y):
        if (x >= 7 or y >= 7) and abs(x - y) >= 2:
            return 1.0 if x > y else 0.0
        if x >= 6 and y >= 6 and x == y:
            a, b = pa * (1 - pb), (1 - pa) * pb
            return a / (a + b)
        k = x + y
        s = first if ((k + 1) // 2) % 2 == 0 else 1 - first
        w = pa if s == 0 else 1 - pb
        return w * f(x + 1, y) + (1 - w) * f(x, y + 1)
    return f(0, 0)


def _sets(pa: float, pb: float, first: int) -> dict:
    """{(games A, games B, who serves the next set's first game): probability} for one set."""
    hA, hB = _hold(pa), _hold(pb)
    out, frontier = {}, {(0, 0, first): 1.0}
    while frontier:
        nxt = {}
        for (a, b, srv), pr in frontier.items():
            if a == 6 and b == 6:
                t = _tiebreak(pa, pb, srv)
                for key, q in (((7, 6, 1 - srv), t), ((6, 7, 1 - srv), 1 - t)):
                    out[key] = out.get(key, 0) + pr * q
                continue
            aw = hA if srv == 0 else 1 - hB
            for (na, nb), q in (((a + 1, b), aw), ((a, b + 1), 1 - aw)):
                done = (na >= 6 or nb >= 6) and abs(na - nb) >= 2 or na == 7 or nb == 7
                key = (na, nb, 1 - srv)
                (out if done else nxt)[key] = (out if done else nxt).get(key, 0) + pr * q
        frontier = nxt
    return out


def scoreline(pa: float, pb: float, best_of: int = 3) -> dict:
    """Exact distribution of final scorelines at fixed serve-point rates (coin toss for the first server): the most
    likely scoreline overall and for each player as the winner, the chance each wins, and expected games."""
    need = best_of // 2 + 1
    lines = {}
    def go(sa, sb, srv, score, pr):
        if sa == need or sb == need:
            lines[tuple(score)] = lines.get(tuple(score), 0) + pr
            return
        for (a, b, nxt), q in _sets(pa, pb, srv).items():
            go(sa + (a > b), sb + (b > a), nxt, score + [(a, b)], pr * q)
    for first in (0, 1):
        go(0, 0, first, [], 0.5)
    win_a = sum(p for sc, p in lines.items() if sum(a > b for a, b in sc) == need)
    best = lambda cond: max(((sc, p) for sc, p in lines.items() if cond(sc)), key=lambda x: x[1], default=(None, 0))
    a_line, a_p = best(lambda sc: sum(a > b for a, b in sc) == need)
    b_line, b_p = best(lambda sc: sum(b > a for a, b in sc) == need)
    games = (sum(p * sum(a for a, _ in sc) for sc, p in lines.items()), sum(p * sum(b for _, b in sc) for sc, p in lines.items()))
    sets = {}
    for sc, p in lines.items():
        k = f"{sum(a > b for a, b in sc)}-{sum(b > a for a, b in sc)}"
        sets[k] = sets.get(k, 0) + p
    fmt = lambda sc, flip=False: ", ".join(f"{b}-{a}" if flip else f"{a}-{b}" for a, b in sc) if sc else None
    return {"p_a": win_a, "line_a": fmt(a_line), "line_a_p": a_p, "line_b": fmt(b_line), "line_b_p": b_p,
            "line_b_w": fmt(b_line, True), "sets": {k: round(v, 4) for k, v in sorted(sets.items(), reverse=True)},
            "games": [round(games[0], 1), round(games[1], 1)],
            "line_a_sets": [list(x) for x in a_line or []], "line_b_sets": [list(x) for x in b_line or []]}


def _lines(pa: float, pb: float, best_of: int = 3) -> dict:
    """{scoreline (tuple of (A games, B games) per set): probability} at fixed serve-point rates, coin toss to serve."""
    need = best_of // 2 + 1
    S = (_sets(pa, pb, 0), _sets(pa, pb, 1))
    out = {}

    def go(sa, sb, srv, score, pr):
        if sa == need or sb == need:
            out[score] = out.get(score, 0) + pr
            return
        for (a, b, nxt), q in S[srv].items():
            go(sa + (a > b), sb + (b > a), nxt, score + ((a, b),), pr * q)
    for first in (0, 1):
        go(0, 0, first, (), 0.5)
    return out


def _lines_form(pa: float, pb: float, best_of: int = 3, sd: float = 0.0, rho: float = 0.0) -> dict:
    """The scoreline distribution with each match's serve rates drawn for day-to-day form, as the simulator's runs draw
    them (sd, correlation rho; 7 x 7 Gauss-Hermite as tennis_hist.match_win_form). Without the form draws the exact
    distribution makes every match longer and closer than the runs and real matches are."""
    if not sd:
        return _lines(pa, pb, best_of)
    from .tennis_hist import _GH
    x, wq = _GH
    wq = wq / wq.sum()
    r2 = (1 - rho * rho) ** 0.5
    out = {}
    for x1, w1 in zip(x, wq):
        for x2, w2 in zip(x, wq):
            qa = min(max(pa + sd * x1, 0.3), 0.95)
            qb = min(max(pb + sd * (rho * x1 + r2 * x2), 0.3), 0.95)
            for sc, p in _lines(qa, qb, best_of).items():
                out[sc] = out.get(sc, 0) + w1 * w2 * p
    return out


def _quantile(pairs, f):
    c, tot = 0.0, sum(p for _, p in pairs)
    for v, p in sorted(pairs):
        c += p
        if c >= f * tot - 1e-12:
            return v


def match_picture(pa: float, pb: float, best_of: int = 3, sd: float = 0.0, rho: float = 0.0, win_a: float | None = None,
                  top: int = 3) -> dict:
    """What the simulation says about how a match goes (user, 2026-11-11: "all the simulated scores are 6-4, 6-4").
    One exact score is a thin slice: 6-4 6-4 is also the commonest score in 22,038 real best-of-3 matches since 2025,
    at 4.1%, so naming only the single most likely score shows the same thing for most matches. What differs between
    matches is who wins and how: each player's chance in straight sets and in a decider, the length in games, and the
    few commonest scores with their chances. `line` is the projected winner's commonest score (winner's games first),
    `sets` the same score A-first for the page to replay. Day-to-day form is included, as in the runs."""
    L = _lines_form(pa, pb, best_of, sd, rho)
    need = best_of // 2 + 1
    a_won = lambda sc: sum(a > b for a, b in sc) == need
    p_a = sum(p for sc, p in L.items() if a_won(sc))
    win_a = p_a if win_a is None else win_a
    A = win_a >= 0.5
    split = {"a_straight": 0.0, "a_long": 0.0, "b_straight": 0.0, "b_long": 0.0}
    for sc, p in L.items():
        split[("a" if a_won(sc) else "b") + ("_straight" if len(sc) == need else "_long")] += p
    tot = [(sum(a + b for a, b in sc), p) for sc, p in L.items()]
    fmt = lambda sc, a_first: ", ".join(f"{a}-{b}" if a_first else f"{b}-{a}" for a, b in sc)
    ranked = sorted(L.items(), key=lambda x: -x[1])
    best = next(x for x in ranked if a_won(x[0]) == A)
    return {"w": 0 if A else 1, "p_win": round(win_a if A else 1 - win_a, 3), "p_a_exact": round(p_a, 4),
            "line": fmt(best[0], A), "line_p": round(best[1], 4), "sets": [list(x) for x in best[0]],
            "straight": round(split["a_straight" if A else "b_straight"], 3),
            "split": {k: round(v, 3) for k, v in split.items()},
            "length": [_quantile(tot, 0.25), _quantile(tot, 0.5), _quantile(tot, 0.75)],
            "top": [{"w": 0 if a_won(sc) else 1, "line": fmt(sc, a_won(sc)), "p": round(p, 4)} for sc, p in ranked[:top]],
            "form": bool(sd)}


def likely_match(pa: float, pb: float, best_of: int, win_a: float, sd: float = 0.0, rho: float = 0.0) -> dict:
    """The Tennis tab's match picture for the rates shown (ratings, or matched to the market's price): the projected
    winner (by the win chance the page shows), the commonest score for him with day-to-day form included (the score
    "Watch the most likely score" replays), how he wins (straight sets or a decider), the length, and the commonest
    scores with their chances (match_picture)."""
    return match_picture(pa, pb, best_of, sd, rho, win_a)


def save_winners(matches: list[dict], now=None) -> None:
    """Each upcoming match's projected winner and scoreline for the Winners tab (data/winners/tennis/<date>.json, by
    the match's Central European date), at the rates the simulator shows by default (matched to the market where the
    pricer does that: ATP)."""
    import datetime as _dt
    from .winners import WIN_DIR
    now = now or _dt.datetime.now(_dt.timezone.utc)       # `now`: the time the projection was made (only later starts kept)
    by_day = {}
    for m in matches:
        start = _dt.datetime.fromisoformat(m["start"])
        if start <= now:
            continue
        d = m["shift"] if (m.get("anchor_default") and m.get("shift") is not None) else 0.0
        sl = scoreline(m["pa"] + d, m["pb"] - d, m.get("best_of", 3))
        win = m["win_model"] if not d else (m.get("market_a") or sl["p_a"])
        a_wins = win > 0.5
        mp = match_picture(m["pa"] + d, m["pb"] - d, m.get("best_of", 3), m.get("sd") or 0.0, m.get("rho") or 0.0, win)
        by_day.setdefault(start.astimezone(TE_TZ).date().isoformat(), {})[m["id"]] = {
            "gid": m["id"], "sport": "tennis", "tour": m["tour"], "event": m.get("event") or m.get("tourn"), "away": m["a"], "home": m["b"],
            "a_te": m.get("a_te"), "b_te": m.get("b_te"), "start": m["start"], "pulled": now.strftime("%Y-%m-%dT%H:%MZ"),
            "slugs": m.get("slugs"), "best_of": m.get("best_of", 3), "surface": m.get("surface"),
            "p_a": round(float(win), 4), "p_a_ratings": m.get("win_model"), "market_a": m.get("market_a"), "winner": "a" if a_wins else "b",
            "line": mp["line"], "line_p": round(mp["line_p"], 3),       # the projected winner's commonest score (form included), winner's games first
            "sets": sl["sets"], "games": sl["games"], "split": mp["split"], "length": mp["length"], "top": mp["top"],
            "rates": "market" if d else "ratings"}
    for day, recs in by_day.items():
        dd = os.path.join(WIN_DIR, "tennis"); os.makedirs(dd, exist_ok=True)
        path = os.path.join(dd, f"{day}.json")
        cur = json.load(open(path)) if os.path.exists(path) else {}
        cur.update(recs); json.dump(cur, open(path, "w"))
