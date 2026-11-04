"""Player research the way prop handicappers write it up, computed from box scores: a game log against tonight's line,
hit rates (season, last 5, last 10), head-to-head against tonight's opponent (any season), per-36 rates, games on low
minutes, and what the opponent allows (to every player and to the player's position).

`Research` holds the box scores of this season and the two before it. `card()` builds one player's write-up for one
stat and line; `rate_factors()` gives the multiplicative factors the fair test (reports/AUDIT_2026-11-03_after.md)
measured, so only the ones that predicted out of sample are used to adjust the simulation."""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from . import nba

STATS = ("pts", "reb", "ast", "tpm")
POS = ("G", "F", "C")

# Head-to-head multiplier on a player's per-minute rates: exp(coef x log of his shrunk rate ratio in the last 5
# meetings). The only research factor that improved the projection on every stat in both held-out tests (2025-26
# Feb-Apr and 2026-27; fitted on 2025-26). Recent form, what the opponent allows and what it allows to his position did
# not (the team-level matchup is already in the engine). The gain is small: ~0.1% of the average miss.
H2H_COEF = {"pts": {"h2h": 0.059}, "reb": {"h2h": 0.068}, "ast": {"h2h": 0.102}, "tpm": {"h2h": 0.066}}


def _val(r: dict, st: str) -> float:
    return float(r["oreb"] + r["dreb"]) if st == "reb" else float(r[st])


class Research:
    def __init__(self, lg: str, games: list[dict], year: int):
        G = {g["id"]: g for g in games}
        for yy in (year, year - 1):
            span = nba.LAST_SEASON.get(yy) if lg == "nba" else None
            if span:
                for g in nba.season_games(lg, *span):
                    G.setdefault(g["id"], g)
        self.lg, self.year = lg, year
        self.logs = defaultdict(list)            # pid -> appearances, by date
        self.allowed = defaultdict(list)         # team -> per game: what its opponents' players produced
        self.dnp = defaultdict(list)             # pid -> dates he was on a box but didn't play
        for g in sorted(G.values(), key=lambda g: g["date"]):
            if not g["final"] or nba.season_of(g["date"]) > year:
                continue
            box = nba._box_cached(lg, g["id"])
            if g["home"] not in box or g["away"] not in box:
                continue
            season = nba.season_of(g["date"])
            for s_, o_ in (("home", "away"), ("away", "home")):
                team, opp = g[s_], g[o_]
                al = {"date": g["date"], "season": season, "min": 0.0, **{st: 0.0 for st in STATS},
                      "pos": {p: {"min": 0.0, **{st: 0.0 for st in STATS}} for p in POS}}
                for r in box[g[o_]]:
                    if r["dnp"] or r["min"] <= 0:
                        continue
                    al["min"] += r["min"]
                    pb = al["pos"].get(r["pos"])
                    for st in STATS:
                        al[st] += _val(r, st)
                        if pb is not None:
                            pb[st] += _val(r, st)
                    if pb is not None:
                        pb["min"] += r["min"]
                self.allowed[team].append(al)
                for r in box[team]:
                    if r["dnp"] or r["min"] <= 0:
                        self.dnp[r["id"]].append(g["date"])
                        continue
                    self.logs[r["id"]].append({"date": g["date"], "gid": g["id"], "season": season, "team": team, "opp": opp,
                                               "home": s_ == "home", "min": float(r["min"]), "pos": r["pos"], "name": r["name"],
                                               "starter": r["starter"], **{st: _val(r, st) for st in STATS}})

        # cumulative allowed per (team, season), for fast "before this date" sums
        self._cum = {}
        for team, rows in self.allowed.items():
            for season in {a["season"] for a in rows}:
                R = [a for a in rows if a["season"] == season]
                arr = lambda f: np.cumsum([0.0] + [f(a) for a in R])
                self._cum[(team, season)] = {"dates": [a["date"] for a in R],
                                             None: {"min": arr(lambda a: a["min"]), **{st: arr(lambda a, st=st: a[st]) for st in STATS}},
                                             **{p: {"min": arr(lambda a, p=p: a["pos"][p]["min"]),
                                                    **{st: arr(lambda a, p=p, st=st: a["pos"][p][st]) for st in STATS}} for p in POS}}
        self._memo = {}

    # ---------------------------------------------------------------- pieces
    def before(self, pid: str, before: str) -> list[dict]:
        return [e for e in self.logs.get(pid, []) if e["date"] < before]

    def opp_allowed(self, opp: str, st: str, before: str, pos: str | None = None) -> dict:
        """What `opp` allowed this season before `before`, per game and per opposing player-minute, against the league;
        with `pos`, to that position only. Rank 1 = allows the most per game."""
        key = (opp, st, before, pos)
        if key in self._memo:
            return self._memo[key]
        import bisect
        season = nba.season_of(before[:10])
        def agg(team):
            c = self._cum.get((team, season))
            if not c:
                return {"games": 0, "per_game": None, "per_min": None, "min": 0.0, "sum": 0.0}
            i = bisect.bisect_left(c["dates"], before)
            s, m = float(c[pos][st][i]), float(c[pos]["min"][i])
            return {"games": i, "per_game": s / i if i else None, "per_min": s / m if m else None, "min": m, "sum": s}
        me = agg(opp)
        allt = {t: agg(t) for t, ss in self._cum if ss == season}
        lg_s = sum(v["sum"] for v in allt.values()); lg_m = sum(v["min"] for v in allt.values())
        lg_g = sum(v["games"] for v in allt.values())
        ranked = sorted((v["per_game"] for v in allt.values() if v["per_game"] is not None), reverse=True)
        out = {**me, "league_per_game": lg_s / lg_g if lg_g else None, "league_per_min": lg_s / lg_m if lg_m else None,
               "rank": (ranked.index(me["per_game"]) + 1) if me["per_game"] is not None else None, "teams": len(ranked)}
        self._memo[key] = out
        return out

    # ---------------------------------------------------------------- the write-up
    def card(self, pid: str, opp: str, st: str, line: float | None, before: str) -> dict:
        """One player's research for one stat. Hit = cleared `line` (or, with no line, his season average rounded to
        .5). Everything is from games strictly before `before`."""
        season = nba.season_of(before[:10])
        past = self.before(pid, before)
        cur = [e for e in past if e["season"] == season]
        if not past:
            return {"games": 0}
        ln = line if line is not None else (round(2 * np.mean([e[st] for e in cur])) / 2 + 0.5 if cur else None)
        hit = lambda L: {"n": len(L), "over": sum(e[st] > ln for e in L) if ln is not None else None,
                         "avg": float(np.mean([e[st] for e in L])) if L else None, "min": float(np.mean([e["min"] for e in L])) if L else None}
        h2h = [e for e in past if e["opp"] == opp][-5:]
        low = [e for e in cur if e["min"] < 20]
        tot_min = sum(e["min"] for e in cur)
        pos = past[-1]["pos"] if past[-1]["pos"] in POS else None
        return {"games": len(cur), "line": ln, "line_source": "DraftKings" if line is not None else "season average",
                "log": [{"date": e["date"][:10], "opp": ("vs " if e["home"] else "@ ") + e["opp"], "min": e["min"], "value": e[st],
                         "over": (e[st] > ln) if ln is not None else None} for e in cur[-10:]][::-1],
                "season": hit(cur), "last5": hit(cur[-5:]), "last10": hit(cur[-10:]),
                "h2h": {**hit(h2h), "games_list": [{"date": e["date"][:10], "min": e["min"], "value": e[st]} for e in h2h][::-1]},
                "low_minutes": hit(low), "per36": 36 * sum(e[st] for e in cur) / tot_min if tot_min else None,
                "opp_allowed": self.opp_allowed(opp, st, before), "opp_allowed_pos": self.opp_allowed(opp, st, before, pos) if pos else None,
                "pos": pos}

    def base_rate(self, past: list[dict], cur: list[dict], st: str, before: str, pos: str | None) -> float:
        """Per-minute rate this season, shrunk to his own last season by 100 minutes (else to the league's rate at his
        position by 60): the baseline the head-to-head ratio is measured against (as in the fair test)."""
        s = sum(e[st] for e in cur); m = sum(e["min"] for e in cur)
        last = [e for e in past if e["season"] == nba.season_of(before[:10]) - 1]
        lm = sum(e["min"] for e in last)
        if lm >= 100:
            return (s + 100 * sum(e[st] for e in last) / lm) / (m + 100)
        lp = (self.opp_allowed(next(iter(self.allowed)), st, before, pos)["league_per_min"] if pos and self.allowed else None) or 0.01
        return (s + 60 * lp) / (m + 60)

    def export(self, pid: str, opp: str, before: str) -> dict | None:
        """Compact research data for the page: this season's games [date, opponent, home, minutes, pts, reb, ast, 3PM]
        and the last 5 meetings with tonight's opponent (any season) [date, minutes, pts, reb, ast, 3PM]."""
        past = self.before(pid, before)
        if not past:
            return None
        season = nba.season_of(before[:10])
        row = lambda e: [e["date"][:10], e["opp"], int(e["home"]), e["min"]] + [e[st] for st in STATS]
        return {"log": [row(e) for e in past if e["season"] == season],
                "h2h": [[e["date"][:10], e["min"]] + [e[st] for st in STATS] for e in past if e["opp"] == opp][-5:],
                "pos": past[-1]["pos"] if past[-1]["pos"] in POS else None}

    def allowed_summary(self, team: str, before: str) -> dict:
        """What `team` allows per game this season, by stat, to every opposing player and to each position, with rank."""
        out = {}
        for st in STATS:
            a = self.opp_allowed(team, st, before)
            out[st] = {"per_game": a["per_game"], "league": a["league_per_game"], "rank": a["rank"], "teams": a["teams"], "games": a["games"],
                       "pos": {p: {k: self.opp_allowed(team, st, before, p)[k] for k in ("per_game", "league_per_game", "rank")} for p in POS}}
        return out

    # ---------------------------------------------------------------- factors for the simulation
    def rate_factors(self, pid: str, opp: str, before: str, coef: dict, k_min: float = 60.0) -> dict:
        """Multiplier per stat on a player's per-minute rate from the factors that passed the fair test:
        exp(sum of coef[stat][factor] x log-ratio). Factors: 'h2h' (his rate in the last 5 meetings vs his rate),
        'recent' (last 5 games), 'opp' (what the opponent allows per player-minute vs the league), 'opp_pos' (to his
        position). Each ratio is shrunk toward 1 by k_min minutes (opponent ratios by 5 games' worth)."""
        past = self.before(pid, before)
        season = nba.season_of(before[:10])
        cur = [e for e in past if e["season"] == season]
        if not cur:
            return {st: 1.0 for st in STATS}
        out = {}
        pos = past[-1]["pos"] if past[-1]["pos"] in POS else None
        for st in STATS:
            c = coef.get(st) or {}
            r0 = self.base_rate(past, cur, st, before, pos)
            if not c or r0 <= 0:
                out[st] = 1.0
                continue
            f = factor_logs(past, cur, opp, st, r0, k_min, self.opp_allowed(opp, st, before), self.opp_allowed(opp, st, before, pos) if pos else None)
            out[st] = float(np.exp(sum(c.get(k, 0.0) * v for k, v in f.items())))
        return out


def factor_logs(past: list[dict], cur: list[dict], opp: str, st: str, r0: float, k_min: float, oa: dict, oap: dict | None) -> dict:
    """The log-ratio features (shared by the fair test and rate_factors)."""
    def ratio(L):
        s = sum(e[st] for e in L); m = sum(e["min"] for e in L)
        return float(np.log((s + k_min * r0) / ((m + k_min) * r0))) if r0 > 0 else 0.0
    def oratio(a):
        if not a or not a.get("league_per_min") or not a.get("min"):
            return 0.0
        k = 5 * a["min"] / max(a["games"], 1)          # five games' worth of minutes
        return float(np.log((a["sum"] + k * a["league_per_min"]) / ((a["min"] + k) * a["league_per_min"])))
    return {"h2h": ratio([e for e in past if e["opp"] == opp][-5:]), "recent": ratio(cur[-5:]), "opp": oratio(oa), "opp_pos": oratio(oap)}
