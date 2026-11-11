"""Walk-forward re-run of a past slate's tennis winners, for nights before the Winners tab saved its projections.

The ratings are refitted without any match played from the slate's start onward. TennisMyLife dates every match by its
event's start, so a cut by date alone would leak results from events still running: matches are removed instead by
the player pairs on Tennis Explorer's results pages from the slate on. The settings are the ones the simulator uses
(study's chosen half-life and prior, the tour's day-to-day form, ATP matched to the price by default). Two limits:
prices are Tennis Explorer's closing odds, not the price at the time, and the database may hold a few pre-slate
matches it had not added yet on the night. It is a rebuild, not a saved record, and is labelled as one."""
from __future__ import annotations

import datetime as dt
import json
import os
import re

import numpy as np

from .blend import HERE

OUT_DIR = os.path.join(HERE, "data", "tennis_bt")


def rebuild(slate: str, now: dt.datetime | None = None, log=print) -> dict:
    from . import tennis as T, tennis_hist as TH, tennis_market as TM
    from .tennis_watch import TE_TZ, MIN_MS, _index, _short_wta, _surface, _te_name, scoreline
    from .winners import _set_games
    now = now or dt.datetime.now(dt.timezone.utc)
    D = dt.date.fromisoformat(slate)
    w0 = dt.datetime.combine(D, dt.time(10), dt.timezone.utc)          # the US slate: UTC-10h, as everywhere in the kit
    w1 = w0 + dt.timedelta(days=1)
    today_cet = now.astimezone(TE_TZ).date()
    rows = []
    for tour in ("ATP", "WTA"):
        d = w0.astimezone(TE_TZ).date()
        while d <= today_cet:
            for x in TM.day(d, tour, T.TE_DIR, max_age=1800):
                if x.get("p2") and re.match(r"^\d\d:\d\d$", x.get("time") or ""):
                    x["_start"] = dt.datetime.combine(d, dt.time.fromisoformat(x["time"]), TE_TZ)
                    if x["_start"] >= w0:
                        rows.append(x)
            d += dt.timedelta(days=1)
    st = T.tml_state(refresh=False)
    short = _short_wta(st, [x for x in rows if x["tour"] == "WTA" and x["_start"] < w1], {})
    if short:
        st = T.tml_state(refresh=False, wta_topup=tuple(short)) or st
    dec = json.load(open(T.DECISION)) if os.path.exists(T.DECISION) else {}
    # every match from the slate on, as player-id pairs (all candidates for each Tennis Explorer name)
    excl = set()
    for tour in ("ATP", "WTA"):
        idx, _ = _index(st, tour)
        for x in rows:
            if x["tour"] != tour:
                continue
            ca = [p for p, _ in idx.get(_te_name(x["p1"]), [])]
            cb = [p for p, _ in idx.get(_te_name(x["p2"]), [])]
            excl |= {frozenset((a, b)) for a in ca for b in cb}
    recent = D.toordinal() - 28
    M = [m for m in st["matches"] if not (m["day"] >= recent and frozenset((m["w"], m["l"])) in excl)]
    removed = len(st["matches"]) - len(M)
    stf = {"matches": M}
    games, skipped, rets = [], {"ATP": 0, "WTA": 0}, 0
    for tour in ("ATP", "WTA"):
        study = st[tour]["study"]
        ch = study.get("chosen") or {"H": 730, "lam": 400, "indoor": False, "hand": False}
        form = (study.get("form") or {}).get("B1") or {"sd": 0.05, "rho": -0.8}
        obs = TH.observations(M, tour)
        R = TH.Ratings(H=ch["H"], lam=ch["lam"], indoor=ch.get("indoor", False), hand=ch.get("hand", False)).fit(obs, D.toordinal() + 1)
        oi, cut = obs["idx"], D.toordinal() - 365
        idx, full = _index(stf, tour)
        anchor = (dec.get(tour) or {}).get("anchor") == "market"
        for x in rows:
            if x["tour"] != tour or x["_start"] >= w1:
                continue
            try:
                s1, s2 = int(x.get("s1") or 0), int(x.get("s2") or 0)
                g1, g2 = [_set_games(v) for v in x.get("g1") or []], [_set_games(v) for v in x.get("g2") or []]
            except ValueError:
                continue
            if max(s1, s2) < 2:                         # retirement or walkover: no clean winner to grade
                rets += 1
                continue
            pl = []
            for nm in (x["p1"], x["p2"]):
                best = None
                for pid, hand in idx.get(_te_name(nm)) or []:
                    i = oi.get(pid)
                    if i is None:
                        continue
                    ms = int(((obs["srv"] == i) & (obs["day"] >= cut) & (obs["day"] <= D.toordinal())).sum())
                    if not best or ms > best[2]:
                        best = (pid, hand, ms, i)
                pl.append(best)
            if not all(pl) or min(p[2] for p in pl) < MIN_MS:
                skipped[tour] += 1
                continue
            (ia, ha, _, a), (ib, hb, _, b) = pl          # a = the winner (listed first on a results page)
            surf, _, ev = _surface(st, tour, x["tourn"] or "", D)
            s_ = surf if surf in ("Hard", "Clay", "Grass") else "Hard"
            p1, p2 = R.p(a, b, s_, None, ha, hb), R.p(b, a, s_, None, hb, ha)
            win = float(TH.match_win_form(p1, p2, 3, form["sd"], form["rho"])[0])
            fair = TM.fair(x.get("o1"), x.get("o2"))
            d = float(TH.shift_to(np.array([p1]), np.array([p2]), fair, 3, form["sd"], form["rho"])[0]) if (anchor and fair) else 0.0
            default = fair if (anchor and fair) else win
            sl = scoreline(p1 + d, p2 - d, 3)
            pick_w = default > 0.5
            line = sl["line_a"] if pick_w else sl["line_b_w"]
            actual = ", ".join(f"{u}-{v}" for u, v in zip(g1, g2))
            games.append({"tour": tour, "event": ev or x["tourn"], "start": x["_start"].isoformat(),
                          "winner": full.get(ia, x["p1"]), "loser": full.get(ib, x["p2"]),
                          "p_winner_ratings": round(win, 3), "p_winner_default": round(default, 3),
                          "p_winner_market": None if fair is None else round(fair, 3), "rates": "market" if d else "ratings",
                          "proj_line": line, "proj_line_p": round(sl["line_a_p"] if pick_w else sl["line_b_p"], 3),
                          "actual": actual, "exact": pick_w and line == actual,
                          "straight_proj": round(sl["sets"]["2-0"] if pick_w else sl["sets"]["0-2"], 3), "straight_actual": s2 == 0})
    games.sort(key=lambda g: g["start"])

    def rec(k, rows_=None):
        G = [g for g in (rows_ if rows_ is not None else games) if g[k] is not None and g[k] != 0.5]
        return [sum(g[k] > 0.5 for g in G), sum(g[k] < 0.5 for g in G)]

    out = {"slate": slate, "built": now.strftime("%Y-%m-%dT%H:%MZ"), "kind": "walk-forward rebuild (not a saved record)",
           "removed_rows": removed, "skipped": skipped, "retirements": rets, "games": games, "record": {}}
    for tour in ("ATP", "WTA", "all"):
        G = [g for g in games if tour == "all" or g["tour"] == tour]
        Gm = [g for g in G if g["p_winner_market"]]                  # log loss on the priced matches only, for both
        ll = lambda k, X: round(float(np.mean([-np.log(g[k]) for g in X])), 3) if X else None
        dis = [g for g in G if g["p_winner_market"] is not None and (g["p_winner_ratings"] > 0.5) != (g["p_winner_market"] > 0.5)]
        out["record"][tour] = {"n": len(G), "ratings": rec("p_winner_ratings", G), "default": rec("p_winner_default", G),
                               "market": rec("p_winner_market", G), "exact": sum(g["exact"] for g in G),
                               "disagree": {"n": len(dis), "ratings_right": sum(g["p_winner_ratings"] > 0.5 for g in dis)},
                               "priced": len(Gm), "ll_ratings": ll("p_winner_ratings", Gm), "ll_market": ll("p_winner_market", Gm)}
    os.makedirs(OUT_DIR, exist_ok=True)
    json.dump(out, open(os.path.join(OUT_DIR, f"recon_{slate}.json"), "w"), indent=1)
    return out
