"""Tennis (ATP + WTA): a point-by-point match simulator on real serve and return statistics.

Data (all real, nothing estimated): Tennis Abstract (tennisabstract.com, Jeff Sackmann's match-statistics site).
  - jsfrags/<Player>.js, for ATP and WTA players: the "last 52 weeks" splits by surface, computed from match
    counts (serve points won SPW, return points won RPW, ace rate A%, double-fault rate DF%, matches with stats MS),
    and the recent results with each match's serve numbers.
  - The walk-forward backtest uses the same recent-results rows (each match's 1stIn, 1st%, 2nd%, DR), so each
    prediction sees only matches played before it.
The site rate-limits, so every request is spaced out and cached.

Model:
  - each player's SPW, RPW, A% and DF% on the match surface from the last-52-weeks table; a thin surface sample is
    blended with the player's other surfaces by matches-with-stats, then with the tour average (MIN_MS matches of
    prior); tour averages come from per-match rows, both players counted (so they aren't tilted toward the players
    fetched).
  - Barnett & Clarke (2005): A's chance of winning a point on serve vs B = tour SPW + (A's SPW - tour SPW) -
    (B's RPW - tour RPW), on the surface and tour.
  - every service game and tiebreak is played point by point (tiebreak at 6-6; a 10-point tiebreak at 6-6 in a
    Grand Slam's deciding set; best of 5 only in ATP Grand Slams), N_SIMS runs. Aces, double faults and break
    points are not priced: the 2026 WTA counts needed to grade and test them aren't available.
"""
from __future__ import annotations

import collections
import datetime as dt
import html
import json
import os
import re
import subprocess
import time
import unicodedata

import numpy as np

from .blend import HERE

TA = "https://www.tennisabstract.com"
CACHE = os.path.join(HERE, ".cache", "tennis")
THROTTLE = 4.0                 # seconds between Tennis Abstract requests (it answers bursts with HTTP 429)
N_SIMS = 20000
MIN_MS = 8.0                   # matches of tour-average prior blended into a player's rates
SURF_K = 10.0                  # matches of the player's other surfaces blended into a thin surface sample
SLAMS = ("australian open", "roland garros", "french open", "wimbledon", "us open")
_last = [0.0]


# ------------------------------------------------------------------ fetching
def _get(url: str, name: str, max_age: float = 12 * 3600) -> str:
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9_.-]+", "_", name))
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age:
        return open(path, encoding="utf-8", errors="replace").read()
    for attempt in range(3):
        wait = THROTTLE - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        r = subprocess.run(["curl", "-sS", "-m", "40", "-A", "Mozilla/5.0 (edge tennis research)", "-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
        _last[0] = time.time()
        body, _, code = r.stdout.rpartition("\n")
        if code == "200":
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)
            return body
        if code == "429":
            time.sleep(60 * (attempt + 1))
            continue
        break
    if os.path.exists(path):                      # a stale copy beats nothing; the caller sees its date in the data
        return open(path, encoding="utf-8", errors="replace").read()
    raise RuntimeError(f"Tennis Abstract {url}: HTTP {code}")


def slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z]", "", s)


def _pct(x: str) -> float | None:
    x = (x or "").strip().rstrip("%")
    try:
        return float(x) / 100.0
    except ValueError:
        return None


def _table(s: str, tid: str) -> tuple[list[str], list[list[str]]]:
    i = s.find(f'id="{tid}"')
    if i < 0:
        return [], []
    t = s[i:s.find("</table>", i)]
    hdr = [html.unescape(re.sub(r"<.*?>", "", c)).strip() for c in re.findall(r"<th[^>]*>(.*?)</th>", t, re.S)]
    rows = [[html.unescape(re.sub(r"<.*?>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
            for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)]
    return hdr, [r for r in rows if r]


def player_by_slug(sl: str, max_age: float = 12 * 3600) -> dict | None:
    return player(sl, max_age=max_age)


def player(name: str, max_age: float = 12 * 3600) -> dict | None:
    """A player's Tennis Abstract record: tour, last-52-weeks surface splits and recent matches."""
    s = _get(f"{TA}/jsfrags/{slug(name)}.js", f"frag_{slug(name)}.js", max_age)
    if "recent-results" not in s:
        return None
    tour = "WTA" if "wplayer.cgi?p=" in s else "ATP"
    hdr, rows = _table(s, "last52-splits")
    splits = {}
    for r in rows:
        d = dict(zip(hdr, r))
        ms = d.get("MS") or next((v for k, v in d.items() if k.startswith("<span") or k.startswith("MS")), "0")
        try:
            ms = float(ms)
        except ValueError:
            ms = 0.0
        splits[r[0]] = {"ms": ms, "spw": _pct(d.get("SPW")), "rpw": _pct(d.get("RPW")), "ace": _pct(d.get("A%")),
                        "df": _pct(d.get("DF%")), "hold": _pct(d.get("Hld%")), "brk": _pct(d.get("Brk%")), "m": float(d.get("M") or 0)}
    rec = []
    i = s.find('id="recent-results"')
    body = s[i:s.find("</table>", i)]
    for r in re.findall(r"<tr><td>(.*?)</tr>", body, re.S):
        c = re.findall(r"<td[^>]*>(.*?)</td>", "<td>" + r, re.S)
        if len(c) < 16:
            continue
        txt = [html.unescape(re.sub(r"<.*?>", "", x)).strip() for x in c]
        m = re.search(r"p=([A-Za-z]+)\">([^<]+)</a", c[6])
        won = "</b> d." in c[6] or re.search(r"<b>[^<]*</b>\s*d\.", c[6]) is not None
        try:
            date = dt.datetime.strptime(txt[0], "%d-%b-%Y").date().isoformat()
        except ValueError:
            continue
        first, f1, f2, dr = _pct(txt[11]), _pct(txt[12]), _pct(txt[13]), (float(txt[8]) if re.match(r"^\d", txt[8] or "") else None)
        spw = first * f1 + (1 - first) * f2 if None not in (first, f1, f2) else None
        rpw = dr * (1 - spw) if dr is not None and spw is not None else None
        rec.append({"date": date, "tourn": txt[1], "surface": txt[2], "round": txt[3], "won": won, "opp": m.group(2) if m else "",
                    "opp_slug": m.group(1) if m else "", "score": txt[7], "spw": spw, "rpw": rpw, "ace": _pct(txt[9]), "df": _pct(txt[10])})
    fn = re.search(r"var fullname = '([^']+)'", s)
    return {"name": fn.group(1) if fn else name, "slug": slug(name), "tour": tour, "splits": splits, "recent": rec}


# ------------------------------------------------------------------ scores
def parse_score(score: str) -> dict | None:
    """Games, sets and tiebreaks from a score string like '6-7(7) 7-6(2) 6-3'. None for retirements / walkovers."""
    if not score or any(w in score.upper() for w in ("RET", "W/O", "DEF", "ABD", "UNP")):
        return None
    sets = re.findall(r"(\d+)-(\d+)(?:\((\d+)\))?", score)
    if not sets:
        return None
    g = [(int(a), int(b)) for a, b, _ in sets]
    return {"sets": len(g), "games": sum(a + b for a, b in g), "tiebreaks": sum(1 for a, b in g if {a, b} == {7, 6}),
            "first_set": g[0][0] + g[0][1], "games_w": sum(a for a, b in g), "games_l": sum(b for a, b in g)}


# ------------------------------------------------------------------ rates
def tour_average(players: list[dict], tour: str, surface: str) -> dict:
    """Tour SPW and ace rate on a surface from per-match rows, both players counted: a player's own SPW and the
    opponent's (1 - the player's RPW). Falls back to all surfaces when the surface has under 50 matches."""
    def collect(surf):
        spw, ace = [], []
        seen = set()
        for p in players:
            if p["tour"] != tour:
                continue
            for r in p["recent"]:
                if r["spw"] is None or r["rpw"] is None or (surf and r["surface"] != surf):
                    continue
                key = (r["date"], r["tourn"], tuple(sorted((p["slug"], r["opp_slug"]))))
                if key in seen:
                    continue
                seen.add(key)
                spw += [r["spw"], 1 - r["rpw"]]
                if r["ace"] is not None:
                    ace.append(r["ace"])
        return spw, ace
    spw, ace = collect(surface)
    if len(spw) < 100:
        spw, ace = collect(None)
    return {"spw": float(np.mean(spw)) if spw else (0.63 if tour == "ATP" else 0.56), "ace": float(np.mean(ace)) if ace else None,
            "n": len(spw) // 2, "surface": surface if len(spw) >= 100 else "all"}


def rates(p: dict, surface: str, avg: dict) -> dict:
    """A player's SPW, RPW, ace and double-fault rates on the surface: the surface row, blended with the other
    surfaces when thin (SURF_K matches), then with the tour average (MIN_MS matches)."""
    S = p["splits"]
    surf_rows = [S[k] for k in ("Hard", "Clay", "Grass", "Carpet") if k in S and S[k]["ms"] > 0 and S[k]["spw"] is not None]
    tot = sum(r["ms"] for r in surf_rows)

    def agg(key):
        rows = [r for r in surf_rows if r.get(key) is not None]
        n = sum(r["ms"] for r in rows)
        return (sum(r[key] * r["ms"] for r in rows) / n) if n else None
    out = {}
    tour_vals = {"spw": avg["spw"], "rpw": 1 - avg["spw"], "ace": avg.get("ace"), "df": None}
    row = S.get(surface)
    for k in ("spw", "rpw", "ace", "df"):
        allv = agg(k)
        sv, sms = (row[k], row["ms"]) if row and row.get(k) is not None else (None, 0.0)
        v = allv if sv is None else (sv if allv is None else (sms * sv + SURF_K * allv) / (sms + SURF_K))
        prior = tour_vals.get(k)
        if v is not None and prior is not None:
            v = (tot * v + MIN_MS * prior) / (tot + MIN_MS)
        out[k] = v
    out["ms"], out["surface_ms"] = tot, (row["ms"] if row else 0.0)
    return out


def matchup(ra: dict, rb: dict, avg: dict) -> tuple[float, float]:
    """Barnett-Clarke: each player's chance of winning a point on their serve against this opponent."""
    t = avg["spw"]
    pa = t + (ra["spw"] - t) - (rb["rpw"] - (1 - t))
    pb = t + (rb["spw"] - t) - (ra["rpw"] - (1 - t))
    return float(np.clip(pa, 0.35, 0.90)), float(np.clip(pb, 0.35, 0.90))


# ------------------------------------------------------------------ simulation
def simulate(pa: float, pb: float, best_of: int = 3, n: int = N_SIMS, seed: int = 7, final_tb10: bool = False,
             ace=(None, None), df=(None, None), form: dict | None = None, est=(0.0, 0.0)) -> dict:
    """Play n matches point by point. Returns per-run arrays: total games, games won by A and B, sets, tiebreaks,
    first-set games, breaks by A and B, serve points by A and B, aces and double faults, and the winner.

    form = {"sd", "rho"} (from form_variation): each run draws the day's serve-point rates around pa / pb, the two
    players' deviations correlated (a player who is on serves better and returns better, so the opponent serves
    worse). est = (variance of the estimate of pa, of pb): the uncertainty in the rates themselves, drawn per run too."""
    rng = np.random.default_rng(seed)
    p0a, p0b = pa, pb
    if form or any(est):
        sd, rho = (form["sd"], form["rho"]) if form else (0.0, 0.0)
        z1, z2 = rng.standard_normal(n), rng.standard_normal(n)
        ea = sd * z1
        eb = sd * (rho * z1 + np.sqrt(1 - rho * rho) * z2)
        ea = ea + np.sqrt(est[0]) * rng.standard_normal(n)
        eb = eb + np.sqrt(est[1]) * rng.standard_normal(n)
        pa, pb = np.clip(pa + ea, 0.30, 0.95), np.clip(pb + eb, 0.30, 0.95)
    need = best_of // 2 + 1
    sa = np.zeros(n, int); sb = np.zeros(n, int)                 # sets
    ga = np.zeros(n, int); gb = np.zeros(n, int)                 # games in the current set
    GA = np.zeros(n, int); GB = np.zeros(n, int)                 # games in the match
    tb = np.zeros(n, int); brA = np.zeros(n, int); brB = np.zeros(n, int)
    spA = np.zeros(n, int); spB = np.zeros(n, int)
    first_set = np.zeros(n, int)
    server_a = rng.random(n) < 0.5                                # coin toss
    done = np.zeros(n, bool)
    for _ in range(80 * best_of):
        act = ~done
        if not act.any():
            break
        deciding = (sa == need - 1) & (sb == need - 1)
        is_tb = act & (ga == 6) & (gb == 6)
        # ---- regular service games
        rg = act & ~is_tb
        if rg.any():
            p = np.where(server_a, pa, pb)
            x = np.zeros(n, int); y = np.zeros(n, int); live = rg.copy()
            for _k in range(60):
                if not live.any():
                    break
                w = rng.random(n) < p
                x += live & w; y += live & ~w
                live &= ~(((x >= 4) | (y >= 4)) & (np.abs(x - y) >= 2))
            srv_won = x > y
            pts = x + y
            spA += np.where(rg & server_a, pts, 0); spB += np.where(rg & ~server_a, pts, 0)
            a_won = np.where(server_a, srv_won, ~srv_won)
            ga += rg & a_won; gb += rg & ~a_won
            brA += rg & ~server_a & a_won; brB += rg & server_a & ~a_won
        # ---- tiebreaks (first to 7, or 10 in a Slam's deciding set; win by 2)
        if is_tb.any():
            target = np.where(final_tb10 & deciding, 10, 7)
            x = np.zeros(n, int); y = np.zeros(n, int); live = is_tb.copy(); k = 0
            for _k in range(80):
                if not live.any():
                    break
                # point k: first point by the player due to serve, then two each
                cur_a = np.where(((k + 1) // 2) % 2 == 0, server_a, ~server_a)
                w = rng.random(n) < np.where(cur_a, pa, pb)
                a_pt = np.where(cur_a, w, ~w)
                spA += live & cur_a; spB += live & ~cur_a
                x += live & a_pt; y += live & ~a_pt
                live &= ~(((x >= target) | (y >= target)) & (np.abs(x - y) >= 2))
                k += 1
            a_won = x > y
            ga += is_tb & a_won; gb += is_tb & ~a_won
            tb += is_tb
        # ---- the next game's server alternates (a tiebreak counts as a game served by its first server)
        server_a = np.where(act, ~server_a, server_a)
        # ---- set over?
        set_over = act & (((ga >= 6) | (gb >= 6)) & (np.abs(ga - gb) >= 2) | is_tb)
        if set_over.any():
            first = set_over & (sa + sb == 0)
            first_set += np.where(first, ga + gb, 0)
            GA += np.where(set_over, ga, 0); GB += np.where(set_over, gb, 0)
            a_set = ga > gb
            sa += set_over & a_set; sb += set_over & ~a_set
            ga = np.where(set_over, 0, ga); gb = np.where(set_over, 0, gb)
            done |= (sa == need) | (sb == need)
    out = {"games": GA + GB, "games_a": GA, "games_b": GB, "sets": sa + sb, "tiebreaks": tb, "first_set": first_set,
           "breaks_a": brA, "breaks_b": brB, "sp_a": spA, "sp_b": spB, "a_wins": sa > sb, "pa": p0a, "pb": p0b}
    for who, sp, a_, d_ in (("a", spA, ace[0], df[0]), ("b", spB, ace[1], df[1])):
        out[f"aces_{who}"] = rng.binomial(sp, a_) if a_ is not None else None
        out[f"dfs_{who}"] = rng.binomial(sp, d_) if d_ is not None else None
    return out


# ------------------------------------------------------------------ match-to-match variation (measured)
def _pts_per_game(p: float) -> float:
    """Expected points in a service game with point-win probability p (closed form, deuce included)."""
    q = 1 - p
    e4, e5, e6 = p ** 4 + q ** 4, 4 * (p ** 4 * q + q ** 4 * p), 10 * (p ** 4 * q * q + q ** 4 * p * p)
    return 4 * e4 + 5 * e5 + 6 * e6 + 20 * p ** 3 * q ** 3 * (6 + 2 / (p * p + q * q))


_FORM = {}


def form_variation(players: list[dict], tour: str, until: str | None = None) -> dict | None:
    """How much a matchup's serve-point rates move from match to match, from real Tennis Abstract rows (matches
    dated before `until`). For each match between two players with 5+ other matches, each side's SPW minus the
    Barnett-Clarke expectation from both players' other matches; the residual variance minus the binomial noise
    (serve points from the score) and the leave-one-out estimation error is the day-to-day variance; the covariance
    of the two sides' residuals gives the correlation. Also returns the per-match variance of a rate (v_match), for
    the estimation error of a player's average."""
    key = (tour, until, len(players), sum(len(p["recent"]) for p in players))
    if key in _FORM:
        return _FORM[key]
    rows = {}
    for p in players:
        if p["tour"] != tour:
            continue
        ok = [r for r in p["recent"] if r["spw"] is not None and r["rpw"] is not None and (until is None or r["date"] < until)]
        if ok:
            rows[p["slug"]] = ok
    allr = [r for v in rows.values() for r in v]
    if len(allr) < 100:
        _FORM[key] = None
        return None
    t = float(np.mean([r["spw"] for r in allr] + [1 - r["rpw"] for r in allr]))
    ra_, rb_, binom, est, seen = [], [], [], [], set()
    for a, A in rows.items():
        for r in A:
            b = r["opp_slug"]
            k = (r["date"], r["tourn"], tuple(sorted((a, b))))
            if b not in rows or k in seen:
                continue
            seen.add(k)
            sc = parse_score(r["score"])
            if not sc:
                continue
            oa = [x for x in A if x is not r]
            ob = [x for x in rows[b] if not (x["opp_slug"] == a and x["date"] == r["date"] and x["tourn"] == r["tourn"])]
            if len(oa) < 5 or len(ob) < 5:
                continue
            sa, rA = np.mean([x["spw"] for x in oa]), np.mean([x["rpw"] for x in oa])
            sb, rB = np.mean([x["spw"] for x in ob]), np.mean([x["rpw"] for x in ob])
            xa, xb = r["spw"], 1 - r["rpw"]
            ra_.append(xa - (sa - (rB - (1 - t))))
            rb_.append(xb - (sb - (rA - (1 - t))))
            g = sc["games"] / 2
            binom.append((xa * (1 - xa) / (g * _pts_per_game(xa)) + xb * (1 - xb) / (g * _pts_per_game(xb))) / 2)
            est.append((np.var([x["spw"] for x in oa]) / len(oa) + np.var([x["rpw"] for x in ob]) / len(ob)
                        + np.var([x["spw"] for x in ob]) / len(ob) + np.var([x["rpw"] for x in oa]) / len(oa)) / 2)
    if len(ra_) < 50:
        _FORM[key] = None
        return None
    ra_, rb_ = np.array(ra_), np.array(rb_)
    V = float((np.var(ra_) + np.var(rb_)) / 2)
    var = max(V - float(np.mean(binom)) - float(np.mean(est)), 0.0)
    rho = float(np.clip(np.cov(ra_, rb_)[0, 1] / var, -0.95, 0.0)) if var > 0 else 0.0
    v_match = float(np.mean([np.var([r["spw"] for r in v]) for v in rows.values() if len(v) >= 5]))
    out = {"sd": var ** 0.5, "rho": rho, "v_match": v_match, "matches": len(ra_), "until": until}
    _FORM[key] = out
    return out


def est_var(form: dict | None, n_a_spw: float, n_b_rpw: float) -> float:
    """Variance of the estimate of A's serve-point rate vs B: A's SPW average and B's RPW average, each a mean over
    its matches (plus the tour-average prior's MIN_MS pseudo-matches)."""
    if not form:
        return 0.0
    return form["v_match"] * (1 / (n_a_spw + MIN_MS) + 1 / (n_b_rpw + MIN_MS))


# ------------------------------------------------------------------ walk-forward backtest
def _rates_from_rows(rows: list[dict], surface: str, avg_spw: float) -> dict | None:
    """The backtest's version of rates(): match-level SPW / RPW from Tennis Abstract's recent results (only rows
    before the match), the surface blended with other surfaces (SURF_K) and the tour average (MIN_MS)."""
    ok = [r for r in rows if r["spw"] is not None and r["rpw"] is not None]
    if len(ok) < 3:
        return None
    out = {}
    for k in ("spw", "rpw"):
        allv = float(np.mean([r[k] for r in ok]))
        same = [r[k] for r in ok if r["surface"] == surface]
        v = allv if not same else (len(same) * float(np.mean(same)) + SURF_K * allv) / (len(same) + SURF_K)
        prior = avg_spw if k == "spw" else 1 - avg_spw
        out[k] = (len(ok) * v + MIN_MS * prior) / (len(ok) + MIN_MS)
    out["n"] = len(ok)
    return out


def backtest(players: list[dict], since: str = "2026-09-01", n: int = 4000, form_mode: str = "measured") -> dict:
    """Walk-forward on real results: every match (since `since`) between two fetched players, predicted only from
    rows dated before it, scored against the final score. Baselines use the same earlier rows: the empirical
    distribution of total games for that tour and format, and a coin flip for the winner.
    form_mode "measured": the day-to-day variation comes from form_variation() on matches before `since` only, so
    the test matches never inform it; "none": fixed rates (the plain iid model), for comparison."""
    by_slug = {p["slug"]: p for p in players}
    forms = {t: (form_variation(players, t, until=since) if form_mode == "measured" else None) for t in ("ATP", "WTA")}
    rows_all = [(p, r) for p in players for r in p["recent"]]
    seen, recs = set(), []
    for p, r in sorted(rows_all, key=lambda x: x[1]["date"]):
        o = by_slug.get(r["opp_slug"])
        if not o or r["date"] < since:
            continue
        key = (r["date"], r["tourn"], tuple(sorted((p["slug"], o["slug"]))))
        if key in seen:
            continue
        seen.add(key)
        sc = parse_score(r["score"])
        if not sc:
            continue
        d, surf, tour = r["date"], r["surface"], p["tour"]
        prior = [x for q in players if q["tour"] == tour for x in q["recent"] if x["date"] < d and x["spw"] is not None and x["rpw"] is not None]
        if len(prior) < 60:
            continue
        avg_spw = float(np.mean([x["spw"] for x in prior] + [1 - x["rpw"] for x in prior]))
        ra = _rates_from_rows([x for x in p["recent"] if x["date"] < d], surf, avg_spw)
        rb = _rates_from_rows([x for x in o["recent"] if x["date"] < d], surf, avg_spw)
        if not ra or not rb:
            continue
        bo = 5 if tour == "ATP" and any(s in r["tourn"].lower() for s in SLAMS) else 3
        pa, pb = matchup(ra, rb, {"spw": avg_spw})
        fm = forms[tour]
        s = simulate(pa, pb, bo, n=n, seed=len(recs) + 1, final_tb10=bo == 5 or any(x in r["tourn"].lower() for x in SLAMS),
                     form=fm, est=(est_var(fm, ra["n"], rb["n"]), est_var(fm, rb["n"], ra["n"])))
        base_sc = [parse_score(x["score"]) for q in players if q["tour"] == tour for x in q["recent"]
                   if x["date"] < d and (5 if tour == "ATP" and any(z in x["tourn"].lower() for z in SLAMS) else 3) == bo]
        base_sc = [b for b in base_sc if b]
        base = [b["games"] for b in base_sc]
        if len(base) < 40:
            continue
        pmf = np.bincount(s["games"], minlength=80)[:80] + 0.5
        pmf = pmf / pmf.sum()
        bpmf = np.bincount(base, minlength=80)[:80] + 0.5
        bpmf = bpmf / bpmf.sum()
        g = min(sc["games"], 79)
        won = r["won"]
        prior_a = [x for x in sorted(p["recent"], key=lambda x: x["date"]) if x["date"] < d and parse_score(x["score"])]
        prior_b = [x for x in sorted(o["recent"], key=lambda x: x["date"]) if x["date"] < d and parse_score(x["score"])]
        hist = lambda rows: [(parse_score(x["score"])["games"], _stat(parse_score(x["score"]), "games_won", x["won"]), x["won"], x["opp_slug"]) for x in rows]
        detail = {"pmf_games": np.bincount(s["games"], minlength=80)[:80].tolist(), "pmf_gw": np.bincount(s["games_a"], minlength=40)[:40].tolist(),
                  "hist_a": hist(prior_a), "hist_b": hist(prior_b), "opp_a": o["slug"], "won_a": won, "gw_a": sc["games_w"] if won else sc["games_l"]}
        recs.append({"date": d, "tour": tour, "bo": bo, "surface": surf, "games": sc["games"], "sets": sc["sets"], **detail,
                     "model_mean": float(s["games"].mean()), "base_mean": float(np.mean(base)),
                     "logp_model": float(np.log(pmf[g])), "logp_base": float(np.log(bpmf[g])),
                     "p_win": float(s["a_wins"].mean()), "won": won,
                     "p_3": float((s["sets"] == 3).mean()) if bo == 3 else None,
                     "base_3": float(np.mean([b["sets"] == 3 for b in base_sc])) if bo == 3 else None,
                     "over": {L: (float((s["games"] > L).mean()), float(np.mean(np.array(base) > L)), sc["games"] > L) for L in (19.5, 20.5, 21.5, 22.5, 23.5)}})
    return {"records": recs, "summary": summarize(recs), "form": forms, "since": since, "form_mode": form_mode}


def summarize(recs: list[dict]) -> dict:
    out = {}
    for tour in ("ATP", "WTA", "all"):
        R = [r for r in recs if tour == "all" or r["tour"] == tour]
        if not R:
            continue
        ll = lambda p, y: -np.log(np.clip(p if y else 1 - p, 1e-6, 1))
        o = {"matches": len(R),
             "games_mae_model": float(np.mean([abs(r["model_mean"] - r["games"]) for r in R])),
             "games_mae_base": float(np.mean([abs(r["base_mean"] - r["games"]) for r in R])),
             "log_score_model": float(np.mean([r["logp_model"] for r in R])), "log_score_base": float(np.mean([r["logp_base"] for r in R])),
             "winner_logloss": float(np.mean([ll(r["p_win"], r["won"]) for r in R])), "winner_acc": float(np.mean([(r["p_win"] > 0.5) == r["won"] for r in R]))}
        R3 = [r for r in R if r["p_3"] is not None]
        if R3:
            o["three_set_brier_model"] = float(np.mean([(r["p_3"] - (r["sets"] == 3)) ** 2 for r in R3]))
            o["three_set_brier_base"] = float(np.mean([(r["base_3"] - (r["sets"] == 3)) ** 2 for r in R3]))
        lines = {}
        for L in (19.5, 20.5, 21.5, 22.5, 23.5):
            pts = [r["over"][L] for r in R if r["bo"] == 3]
            if pts:
                lines[L] = {"logloss_model": float(np.mean([ll(m, y) for m, b, y in pts])), "logloss_base": float(np.mean([ll(b, y) for m, b, y in pts])),
                            "over_rate": float(np.mean([y for m, b, y in pts]))}
        o["lines"] = lines
        out[tour] = o
    return out


# ------------------------------------------------------------------ PrizePicks board
STATS = {"Total Games": "games", "Total Games Won": "games_won", "Total Sets": "sets", "Total Tie Breaks": "tiebreaks",
         "1st Set Total Games": "first_set"}
LABEL = {"games": "total games", "games_won": "games won", "sets": "total sets", "tiebreaks": "tiebreaks", "first_set": "1st set games"}
DABBLE = {"games": ("total-games",)}
BLEND = {"intercept": 0.0, "w_model": 0.2, "w_market": 0.8, "w_hist": 0.0}   # the kit's learned NBA/NHL weights; no tennis-specific fit yet
BREAK_EVEN = {"standard": 0.577}


EVENTS = os.path.join(HERE, "data", "tennis_events.json")


def _events() -> list[dict]:
    """Events checked by hand against a cited source (data/tennis_events.json): used when the players have no
    match at the event yet (e.g. the first round-robin day of a tour final)."""
    try:
        return json.load(open(EVENTS))
    except (OSError, ValueError):
        return []


def _context(pa: dict, pb: dict, start: str) -> dict:
    """The match's tournament, surface and format. Known only when both players' latest matches (at an event
    dated up to 13 days before the start, 16 for a Slam) are at the same tournament, i.e. both are in that draw, or when a sourced entry in
    data/tennis_events.json lists both players for these dates. Otherwise unknown, and no surface is assumed."""
    from .shop import _norm
    d0 = dt.date.fromisoformat(start[:10])

    def latest(p):   # Tennis Abstract dates a match by its event's start: 12-day Masters events and two-week Slams
        rows = [r for r in p["recent"] if 0 <= (d0 - dt.date.fromisoformat(r["date"])).days
                <= (16 if any(s in r["tourn"].lower() for s in SLAMS) else 13)]
        return max(rows, key=lambda r: r["date"]) if rows else None
    ca, cb = latest(pa), latest(pb)
    if ca and cb and ca["tourn"] == cb["tourn"] and ca["date"] == cb["date"]:
        slam = any(s in ca["tourn"].lower() for s in SLAMS)
        return {"tourn": ca["tourn"], "surface": ca["surface"], "best_of": 5 if slam and pa["tour"] == "ATP" else 3, "slam": slam,
                "known": True, "source": "both players' matches at this event (Tennis Abstract)"}
    for e in _events():
        names = {_norm(x) for x in e.get("players", [])}
        if e.get("tour") == pa["tour"] and e["start"] <= start[:10] <= e["end"] and {_norm(pa["name"]), _norm(pb["name"])} <= names:
            return {"tourn": e["tourn"], "surface": e["surface"], "best_of": e["best_of"], "slam": e.get("slam", False), "known": True,
                    "source": e["source"]}
    return {"tourn": None, "surface": None, "best_of": 3, "known": False}


def _player_row(p: dict, opp_slug: str, start: str):
    """The player's Tennis Abstract row for this match. Tennis Abstract dates every match with its tournament's
    start date, so the row is dated 0-16 days before the match (a two-week Slam) or a day after (time zones). None
    when there is no such row yet, or when two rows fit (the same opponent twice in one event, e.g. a round robin
    and the final): that one is graded by hand."""
    d0 = dt.date.fromisoformat(start[:10])
    rows = [r for r in p["recent"] if r["opp_slug"] == opp_slug and -16 <= (dt.date.fromisoformat(r["date"]) - d0).days <= 1]
    return rows[0] if len(rows) == 1 else None


def _dabble_board() -> dict:
    """{(player key, stats): (line, over price, under price)} for Dabble's open tennis props."""
    from .shop import _get as dget, _norm
    out = {}
    for c in dget("/competitions").get("data", []):
        if "tennis" not in (c.get("name") or "").lower():
            continue
        for fx in dget(f"/competitions/{c['id']}/sport-fixtures").get("data", []):
            d = dget(f"/sportfixtures/details/{fx['id']}?filter=dfs-enabled").get("data") or {}
            price = {x["selectionId"]: x.get("price") for x in d.get("prices", [])}
            for x in d.get("playerProps", []):
                k = (_norm(x["playerName"]), tuple(sorted(x.get("stats") or [])))
                v = out.setdefault(k, {"line": float(x["value"])})
                v[x["lineType"]] = price.get(x["selectionId"])
    return out


def _tilt_over(arr: np.ndarray, d_line: float, q: float, line: float) -> float:
    from .nfl_pp import anchored_count
    return anchored_count(arr.astype(float), d_line, line) if abs(d_line - line) > 1e-9 else q


def price_leg(G: dict, name: str, stat: str, line: float, over_only: bool = False, side: str | None = None) -> dict | None:
    from .blend import final_probability, load_adjustments
    from .nba_pp import find_player
    from .shop import _norm
    who = find_player(name, [{"name": G["a"]["name"]}, {"name": G["b"]["name"]}])
    if not who:
        return None
    a_side = who["name"] == G["a"]["name"]
    s = G["sim"]
    arr = {"games": s["games"], "sets": s["sets"], "tiebreaks": s["tiebreaks"], "first_set": s["first_set"],
           "games_won": s["games_a"] if a_side else s["games_b"]}[stat]
    over = float(np.mean(arr > line)); push = float(np.mean(arr == line)) if float(line).is_integer() else 0.0
    pmk, dk = None, None
    if stat in DABBLE:
        dk = G["dabble"].get((_norm(name), DABBLE[stat])) or G["dabble"].get((_norm(G["b"]["name"] if a_side else G["a"]["name"]), DABBLE[stat]))
        if dk and dk.get("over") and dk.get("under"):
            q = (1 / dk["over"]) / (1 / dk["over"] + 1 / dk["under"])
            pmk = _tilt_over(arr, dk["line"], q, line)
    adj = load_adjustments()
    adj["blend_by_sport"] = {**(adj.get("blend_by_sport") or {}), "tennis": BLEND}
    flags = []
    if not G["ctx"]["known"]:
        flags.append("tournament and surface not found in either player's recent matches: all-surface rates, no surface assumed")
    for p, r in ((G["a"], G["ra"]), (G["b"], G["rb"])):
        if r["ms"] < 8:
            flags.append(f"THIN SAMPLE: {p['name']} has {r['ms']:.0f} matches with stats in the last 52 weeks")
    best = None
    for sd in (["over"] if over_only else ["over", "under"]):
        if side and sd != side:
            continue
        pm = (over if sd == "over" else 1 - over - push) / max(1 - push, 1e-9)
        pk = None if pmk is None else (pmk if sd == "over" else 1 - pmk)
        e = final_probability(pm, pk, None, f"tennis:{stat}:{sd}", 0, adj)
        conf, why = e.confidence, []
        if pk is None and conf in ("High", "Medium"):
            conf, why = "Low", ["no market price for this line: the simulation alone can't carry a leg"]
        if flags and conf in ("High", "Medium"):
            conf = "Low"
        if best is None or e.p > best["p_final"]:
            best = {"side": sd, "p_model": round(pm, 4), "p_market": None if pk is None else round(pk, 4), "p_hist": None, "hist_n": 0,
                    "p_final": e.p, "confidence": conf, "why": why}
    return {"a_side": a_side, "median": float(np.median(arr)), "mean": float(np.mean(arr)), "q25": float(np.percentile(arr, 25)),
            "q75": float(np.percentile(arr, 75)), "flags": flags, "dabble": dk, **best}


_PARSED = {}


def cached_players() -> list[dict]:
    """Every Tennis Abstract record in the cache (the set the tour averages come from, so pricing and edge verify
    use the same averages)."""
    out = []
    if not os.path.isdir(CACHE):
        return out
    for f in sorted(os.listdir(CACHE)):
        if not f.startswith("frag_"):
            continue
        path = os.path.join(CACHE, f)
        key = (f, os.path.getmtime(path))
        if key not in _PARSED:
            try:
                _PARSED[key] = player(f[len("frag_"):-3], max_age=10 ** 9)
            except Exception:
                _PARSED[key] = None
        if _PARSED[key]:
            out.append(_PARSED[key])
    return out


class NoStats(ValueError):
    pass


def game(pa: dict, pb: dict, start: str, players: list[dict] | None, dab: dict, n: int = N_SIMS) -> dict:
    ctx = _context(pa, pb, start)
    avg = tour_average(cached_players() or players or [pa, pb], pa["tour"], ctx["surface"])
    ra, rb = rates(pa, ctx["surface"], avg), rates(pb, ctx["surface"], avg)
    for p, r in ((pa, ra), (pb, rb)):
        if r["spw"] is None or r["rpw"] is None:   # no stats-covered match in 52 weeks: nothing real to simulate from
            raise NoStats(f"{p['name']} has no matches with serve/return stats in the last 52 weeks on Tennis Abstract")
    p1, p2 = matchup(ra, rb, avg)
    fm = form_variation(cached_players() or players or [pa, pb], pa["tour"])
    sim = simulate(p1, p2, ctx["best_of"], n=n, final_tb10=bool(ctx.get("slam")), form=fm,
                   est=(est_var(fm, ra["ms"], rb["ms"]), est_var(fm, rb["ms"], ra["ms"])))
    return {"a": pa, "b": pb, "ctx": ctx, "avg": avg, "ra": ra, "rb": rb, "sim": sim, "dabble": dab, "start": start, "form": fm}


def price_board(props: list[dict], n: int = N_SIMS, log=print, store: dict | None = None) -> list[dict]:
    props = [p for p in props if p["stat"] in STATS and p.get("odds_type") == "standard" and "/" not in (p["player"] or "")]
    if not props:
        return []
    cache = {}
    def get(nm):
        if nm not in cache:
            try:
                cache[nm] = player(nm)
            except Exception:
                cache[nm] = None
        return cache[nm]
    pairs = {}
    for p in props:
        opp = (p.get("opp") or "").replace(" 1st Set", "").strip()
        pairs.setdefault(tuple(sorted((p["player"], opp))), []).append(p)
    dab = _dabble_board()
    everyone = [x for nm in {n for k in pairs for n in k} for x in [get(nm)] if x]
    rows = []
    for (a, b), mine in sorted(pairs.items(), key=lambda kv: kv[1][0]["start"]):
        pa, pb = get(a), get(b)
        if not pa or not pb:
            rows += [{**p, "error": f"no Tennis Abstract record for {a if not pa else b}"} for p in mine]
            continue
        if pa["tour"] != pb["tour"]:
            rows += [{**p, "error": "players on different tours (name match?)"} for p in mine]
            continue
        log(f"  {a} vs {b} ({pa['tour']}): {len(mine)} lines, simulating...")
        try:
            G = game(pa, pb, mine[0]["start"], everyone, dab, n)
        except NoStats as e:
            log(f"    not priced: {e}")
            rows += [{**p, "error": str(e)} for p in mine]
            continue
        eid = f"{pa['slug']}-{pb['slug']}-{mine[0]['start'][:10]}"
        if store is not None:
            store[eid] = G
        for p in mine:
            st = STATS[p["stat"]]
            x = price_leg(G, p["player"], st, p["line"], p.get("over_only", False))
            if not x:
                rows.append({**p, "error": "player not matched"})
                continue
            me, op = (pa, pb) if x["a_side"] else (pb, pa)
            note = (f"tennis sim median {x['median']:.1f} (25-75th {x['q25']:.0f}-{x['q75']:.0f}); serve points won vs this opponent "
                    f"{G['sim']['pa'] if x['a_side'] else G['sim']['pb']:.3f}, opponent {G['sim']['pb'] if x['a_side'] else G['sim']['pa']:.3f}; "
                    + (f"{G['ctx']['tourn']} ({G['ctx']['surface']}, best of {G['ctx']['best_of']})" if G["ctx"]["known"] else "event unknown")
                    + (f"; Dabble {x['dabble']['line']:g} at {x['dabble'].get('over')}/{x['dabble'].get('under')}" if x["dabble"] else "; no market price")
                    + (f"; flags: {', '.join(x['flags'])}" if x["flags"] else "") + (f"; {x['why'][0]}" if x["why"] else "")
                    + f"; pulled {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%MZ}")
            rows.append({**p, **x, "event_id": eid, "player_id": me["slug"], "team": me["tour"], "opp": op["name"], "opp_slug": op["slug"],
                         "market_key": f"tennis_{st}", "stat_key": st, "sport": "tennis", "script": f"tennis:{eid}",
                         "game": f"{pa['name']} vs {pb['name']}",
                         "event": (f"{G['ctx']['tourn']} ({G['ctx']['surface']}, best of {G['ctx']['best_of']})" if G["ctx"]["known"] else "event not confirmed: all-surface rates"),
                         "proj": x["median"], "opp_proj": None, "notes": note,
                         "newcomer": bool(x["flags"]), "dk_line": None, "dk_lambda": None, "hist": hist_counts(me, st, p["line"]),
                         "research": research(me, op, st, p["line"])})
    return rows


def _stat(sc: dict, st: str, won: bool) -> float:
    if st == "games_won":
        return sc["games_w"] if won else sc["games_l"]
    return {"games": sc["games"], "sets": sc["sets"], "tiebreaks": sc["tiebreaks"], "first_set": sc["first_set"]}[st]


def hist_counts(p: dict, st: str, line: float) -> tuple[int, int]:
    vals = [_stat(sc, st, r["won"]) for r in p["recent"] for sc in [parse_score(r["score"])] if sc]
    return sum(v > line for v in vals), sum(v < line for v in vals)


def research(p: dict, o: dict, st: str, line: float) -> dict:
    rows = sorted([r for r in p["recent"] if parse_score(r["score"])], key=lambda r: r["date"])
    vals = [(r, _stat(parse_score(r["score"]), st, r["won"])) for r in rows]
    cnt = lambda L: [sum(v > line for _, v in L), sum(v < line for _, v in L), len(L)]
    h2h = [(r, v) for r, v in vals if r["opp_slug"] == o["slug"]]
    avg = lambda L: float(np.mean([v for _, v in L])) if L else None
    return {"season": cnt(vals), "last5": cnt(vals[-5:]), "h2h": cnt(h2h), "season_avg": avg(vals), "last5_avg": avg(vals[-5:]),
            "h2h_avg": avg(h2h), "last_games": [v for _, v in vals[-5:]]}


# ------------------------------------------------------------------ lists (same shape as nfl_pp / nhl_pp, for edge tennis-picks)
def days(rows: list[dict]):
    from zoneinfo import ZoneInfo
    by = collections.defaultdict(list)
    for r in rows:
        if "error" in r or not r.get("start"):
            continue
        t = dt.datetime.fromisoformat(r["start"].replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York"))
        by[t.strftime("%Y-%m-%d")].append(r)
    return [(dt.date.fromisoformat(d).strftime("%a %b %-d"), by[d]) for d in sorted(by)]


def per_game_cap(rows: list[dict], top: int) -> int:
    g = len({r["script"] for r in rows})
    return 1 if g >= top else min(3, -(-top // max(g, 1)))


RANK = {"High": 0, "Medium": 1, "Low": 2}


def _take(cand, top, per_game, accept=None):
    seen, out = collections.Counter(), []
    for r in cand:
        if seen[r["script"]] >= per_game or any(o["player"] == r["player"] and o["stat_key"] == r["stat_key"] for o in out if o["script"] == r["script"]):
            continue
        if accept and not accept(r):
            continue
        seen[r["script"]] += 1
        out.append(r)
        if top and len(out) == top:
            break
    return out


def _rankable(r) -> bool:
    """Lists rank only legs the data supports: both players with 8+ stats-covered matches and a confirmed event.
    A thin sample (often lower-level 125 / Challenger / ITF opposition, which the rates don't adjust for) or an
    unknown surface stays on the full board, unranked."""
    return "error" not in r and not r.get("newcomer")


def pick_order(rows, top=5, per_game=1):
    return _take(sorted([r for r in rows if _rankable(r)], key=lambda r: (RANK.get(r["confidence"], 3), -r["p_final"])), top, per_game)


def most_likely_run(G: dict) -> dict:
    """The most common final scoreline in games (A's games, B's games, sets), then the run with it."""
    s = G["sim"]
    keys = np.stack([s["games_a"], s["games_b"], s["sets"]], 1)
    u, c = np.unique(keys, axis=0, return_counts=True)
    top = u[np.argmax(c)]
    run = int(np.where((keys == top).all(1))[0][0])
    return {"run": run, "score": {G["a"]["name"]: int(top[0]), G["b"]["name"]: int(top[1])}, "sets": int(top[2]), "share": float(c.max() / len(keys))}


def likely_order(rows, store, top=None, drop=None, per_game=99):
    runs = {e: most_likely_run(G) for e, G in store.items()}
    cand = []
    for r in rows:
        if not _rankable(r) or r["event_id"] not in runs or not r.get("research"):
            continue
        G, L = store[r["event_id"]], runs[r["event_id"]]
        s = G["sim"]
        arr = {"games": s["games"], "sets": s["sets"], "tiebreaks": s["tiebreaks"], "first_set": s["first_set"],
               "games_won": s["games_a"] if r["a_side"] else s["games_b"]}[r["stat_key"]]
        val = float(arr[L["run"]])
        gap = val - r["line"]
        if gap == 0:
            continue
        side = "over" if gap > 0 else "under"
        if (side == "under" and r.get("over_only")) or (r["median"] - r["line"]) * gap <= 0:
            continue
        x = r if side == r["side"] else {**r, **price_leg(G, r["player"], r["stat_key"], r["line"], side=side)}
        if x["p_final"] < 0.5:
            continue
        cand.append({**x, "method": "likely", "ml": {"score": L["score"], "sets": L["sets"], "value": val, "gap": gap, "box": {}}})
    cand.sort(key=lambda r: (RANK.get(r["confidence"], 3), -r["p_final"]))

    def accept(r):
        r["reasons"] = reasons(r, store[r["event_id"]])
        against = [x["name"] for x in r["reasons"] if x["verdict"] == "against"]
        if against and drop is not None:
            drop.append({"player": r["player"], "side": r["side"], "line": r["line"], "stat": LABEL[r["stat_key"]],
                         "p": round(r["p_final"], 3), "against": against})
        return not against
    return _take(cand, top, per_game, accept)


def _hold(p: float) -> float:
    q = 1 - p
    return p ** 4 * (1 + 4 * q + 10 * q * q) + 20 * p ** 3 * q ** 3 * p * p / (1 - 2 * p * q)


def reasons(r: dict, G: dict) -> list[dict]:
    """The reasons that make a difference: the most likely match, the simulation (its median, with the projected holds
    or win chance that drive it), Dabble's price, and the sample flag. Recent record, last 5, head-to-head and average
    games in earlier matches are not reasons: on 742 walk-forward matches none added information beyond the
    simulation (LESSONS L30)."""
    sgn = 1 if r["side"] == "over" else -1
    vd = lambda lean: "neutral" if lean == 0 else "supports" if lean == sgn else "against"
    cmp = lambda a, b: (a > b) - (a < b)
    out = []
    add = lambda name, verdict, text: out.append({"name": name, "verdict": verdict, "text": text})
    ml = r.get("ml")
    if ml:
        sc = ", ".join(f"{k} {v}" for k, v in ml["score"].items())
        add("most likely match", vd(cmp(ml["value"], r["line"])), f"{ml['value']:g} in the most likely match ({sc} games, {ml['sets']} sets) vs a {r['line']} line")
    s = G["sim"]
    if r["stat_key"] == "games_won":
        pw = float(s["a_wins"].mean()) if r["a_side"] else 1 - float(s["a_wins"].mean())
        why = f"projected to win {pw:.0%} of the time"
    else:
        why = f"projected holds {_hold(s['pa']):.0%} and {_hold(s['pb']):.0%} vs a tour average of {_hold(G['avg']['spw']):.0%}"
        if G["ctx"]["best_of"] == 3 and r["stat_key"] != "first_set":
            why += f", three sets {float((s['sets'] == 3).mean()):.0%}"
    add("simulation", vd(cmp(r["median"], r["line"])), f"median {r['median']:g} (25-75th {r['q25']:.0f}-{r['q75']:.0f}); {why}")
    pk = r.get("p_market")
    if pk is None:
        add("market", "neutral", "no Dabble price for this line")
    else:
        add("market", "supports" if pk >= 0.52 else "against" if pk <= 0.48 else "neutral", f"Dabble {pk:.0%} for this side at this line")
    if r.get("flags"):
        add("sample", "against", "; ".join(r["flags"]))
    return out


def gap_rows(ok):
    rs = sorted([r for r in ok if r.get("p_market") is not None], key=lambda r: -abs(r["p_market"] - 0.5))
    return [{"player": r["player"], "stat": LABEL[r["stat_key"]], "pp": r["line"], "dk": f"Dabble {r['dabble']['line']:g}", "side": r["side"],
             "p": round(r["p_final"], 4), "conf": r["confidence"], "game": r["game"]} for r in rs]


def verdict(r: dict) -> str:
    be = BREAK_EVEN.get(r.get("odds_type"))
    if be is None:
        return "PASS (payout multiplier unknown for this line type)"
    if r["confidence"] == "High" and r["p_final"] >= 0.65 and r["p_final"] >= be + 0.02:
        return f"ENTRY LEG (High, {r['p_final']:.0%} vs break-even {be:.1%})"
    if r["confidence"] in ("High", "Medium"):
        return "LEAN (Medium: show, don't enter)" if r["confidence"] == "Medium" else "LEAN (High but under 65%)"
    return "PASS (below the gate)"


def write_up(r: dict, verified: str = "", warns: list | None = None) -> str:
    f = lambda v: "-" if v is None else f"{v:.0%}"
    lines = [f"### {r.get('bet_id', '')}{r['player']} ({r['team']}) {r['side'].upper()} {r['line']} {LABEL[r['stat_key']]} — {r['game']}",
             f"**{r['p_final']:.1%} {r['confidence']}** · {verdict(r)}" + (f" · back-check: **{verified}**" if verified else ""),
             f"- Sources: simulation {f(r['p_model'])} · Dabble {f(r['p_market'])}",
             f"- Simulation: median {r['median']:g}, 25–75th {r['q25']:.0f}–{r['q75']:.0f}"]
    if r.get("ml"):
        sc = ", ".join(f"{k} {v}" for k, v in r["ml"]["score"].items())
        lines.insert(2, f"- Most likely match ({sc} games, {r['ml']['sets']} sets): {r['ml']['value']:g} ({r['ml']['gap']:+.1f} vs the line)")
    if r["flags"]:
        lines.append("- Flags: " + "; ".join(r["flags"]))
    if r.get("reasons"):
        mark = {"supports": "✓", "neutral": "–", "against": "✗"}
        lines.append("- Reasons:" if r.get("ml") else "- Reasons (shown, not used to drop the leg):")
        lines += [f"  - {mark[x['verdict']]} {x['name']}: {x['text']}" for x in r["reasons"]]
    if warns:
        lines.append("- Back-check warnings: " + "; ".join(warns))
    return "\n".join(lines)
