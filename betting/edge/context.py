"""Context layer: what a sharp bettor checks beyond the price and the raw game log, priced as a model probability
with the reasons spelled out.

  NHL shots on goal   shot rate per minute x projected ice time (recent games weigh more) x the opponent's shots
                      allowed per game against the league (early-season numbers lean on last season)
  NHL goalie saves    the opponent's shots per game x the goalie's save rate over his last 30 starts
  MLB pitcher Ks      strikeouts per batter faced (shrunk to league) combined with the opponent's strikeout rate
                      against his throwing hand (odds-ratio method) x batters he usually faces (last 5 starts)

The result is the `model` component of the blend. It is used for regular (standard) lines, where the price alone
sits near 50/50; goblins keep the validated market + history recipe. Every context call is logged with its
reasons, so `edge learn` can measure whether it earns its weight.
"""
from __future__ import annotations

import functools
import math

from .grade import _get
from . import lowline as LW

NHL_SEASONS = ("20262027", "20252026")
PRIOR_GAMES = 10          # early-season team rates lean on last season as if it were 10 games
OPP_SHRINK = 0.6          # opponent effects are partly noise and pace: keep 60% of the measured gap
LEAGUE_K = 0.222


def nb_over(mean: float, line: float, cv: float) -> float:
    """P(X > line) for a gamma-Poisson count with this mean and game-to-game CV; whole lines exclude the push."""
    k = 1 / cv ** 2
    p = k / (k + mean)
    cdf, m = 0.0, int(math.floor(line))
    pm = None
    for x in range(m + 1):
        pmf = math.exp(math.lgamma(x + k) - math.lgamma(k) - math.lgamma(x + 1) + k * math.log(p) + x * math.log(1 - p))
        cdf += pmf
        pm = pmf
    over = 1 - cdf
    if line == int(line):
        return over / max(1e-9, 1 - pm)
    return over


# ------------------------------------------------------------------ NHL
@functools.lru_cache(maxsize=None)
def nhl_teams() -> dict:
    """{triCode: {'sa': shots against/game, 'sf': shots for/game}} blended with last season, plus league averages."""
    tri = {t["id"]: t["triCode"] for t in _get("https://api.nhle.com/stats/rest/en/team")["data"]}
    seasons = []
    for s in NHL_SEASONS:
        d = _get(f"https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId={s}%20and%20gameTypeId=2")["data"]
        seasons.append({tri.get(x["teamId"]): x for x in d})
    cur, last = seasons
    out = {}
    for t, x in cur.items():
        gp, prev = x.get("gamesPlayed") or 0, last.get(t) or x
        out[t] = {k: ((x[f] or 0) * gp + (prev[f] or 0) * PRIOR_GAMES) / (gp + PRIOR_GAMES)
                  for k, f in (("sa", "shotsAgainstPerGame"), ("sf", "shotsForPerGame"), ("ga", "goalsAgainstPerGame"))}
    lg = {k: sum(v[k] for v in out.values()) / len(out) for k in ("sa", "sf", "ga")}
    return {"teams": out, "league": lg}


def _nhl_opp(opp: str) -> str:
    from .tier import NHL_API
    return NHL_API.get(opp, opp)


def nhl_sog(pid: str, opp: str, line: float) -> tuple[float, list[str], float] | None:
    log = LW.nhl_log(pid)[:30]
    if len(log) < 8:
        return None
    cur = log[0]["season"]
    w = [2.0 if g["season"] == cur else 1.0 for g in log]
    mins = sum(wi * g["vol"] for wi, g in zip(w, log))
    if mins <= 0:
        return None
    rate = sum(wi * float(g["x"].get("shots") or 0) for wi, g in zip(w, log)) / mins
    toi_all = mins / sum(w)
    toi5 = sum(g["vol"] for g in log[:5]) / min(5, len(log))
    toi = 0.6 * toi5 + 0.4 * toi_all
    why = [f"{rate * 60:.1f} shots per 60 min, about {toi:.0f} min a night"]
    if abs(toi5 - toi_all) >= 1.5:
        why.append(f"ice time {'up' if toi5 > toi_all else 'down'}: {toi5:.1f} min over his last 5 vs {toi_all:.1f}")
    f = 1.0
    t = nhl_teams()
    o = t["teams"].get(_nhl_opp(opp))
    if o:
        raw = o["sa"] / t["league"]["sa"]
        f = 1 + OPP_SHRINK * (raw - 1)
        why.append(f"{_nhl_opp(opp)} allows {o['sa']:.1f} shots a game (league {t['league']['sa']:.1f}): {(f - 1) * 100:+.0f}%")
    mean = rate * toi * f
    why.append(f"projects {mean:.2f} shots")
    return nb_over(mean, line, 0.30), why, mean


def nhl_saves(pid: str, opp: str, line: float) -> tuple[float, list[str], float] | None:
    starts = [g for g in LW.nhl_log(pid) if g["x"].get("gamesStarted")][:30]
    if len(starts) < 8:
        return None
    sa = sum(float(g["x"].get("shotsAgainst") or 0) for g in starts)
    ga = sum(float(g["x"].get("goalsAgainst") or 0) for g in starts)
    sv = (sa - ga + 0.900 * 300) / (sa + 300)                       # save rate shrunk toward .900 with 300 shots
    t = nhl_teams()
    o = t["teams"].get(_nhl_opp(opp))
    shots = (t["league"]["sf"] + OPP_SHRINK * (o["sf"] - t["league"]["sf"])) if o else sa / len(starts)
    mean = shots * sv
    why = [f"save rate {sv:.3f} over his last {len(starts)} starts"]
    if o:
        why.append(f"{_nhl_opp(opp)} takes {o['sf']:.1f} shots a game (league {t['league']['sf']:.1f})")
    why.append(f"projects {mean:.1f} saves")
    return nb_over(mean, line, 0.18), why, mean


# ------------------------------------------------------------------ MLB
@functools.lru_cache(maxsize=None)
def _mlb_team_ids() -> dict:
    ids = {t["abbreviation"]: t["id"] for t in _get("https://statsapi.mlb.com/api/v1/teams?sportId=1")["teams"]}
    for a, b in (("AZ", "ARI"), ("CWS", "CHW"), ("WSN", "WSH"), ("LA", "LAD")):
        if b in ids:
            ids.setdefault(a, ids[b])
        elif a in ids:
            ids.setdefault(b, ids[a])
    return ids


@functools.lru_cache(maxsize=None)
def opp_k_rate(team: str, hand: str, season: int) -> tuple[float, int] | None:
    tid = _mlb_team_ids().get(team)
    if not tid:
        return None
    code = "vl" if hand == "L" else "vr"
    for gt in ("R",):
        r = _get(f"https://statsapi.mlb.com/api/v1/teams/{tid}/stats?stats=statSplits&group=hitting&season={season}&sitCodes={code}&gameType={gt}")
        for s in r["stats"][0]["splits"]:
            if s["split"]["code"] == code and s["stat"].get("plateAppearances"):
                return s["stat"]["strikeOuts"] / s["stat"]["plateAppearances"], s["stat"]["plateAppearances"]
    return None


@functools.lru_cache(maxsize=None)
def pitch_hand(pid: str) -> str:
    return _get(f"https://statsapi.mlb.com/api/v1/people/{pid}")["people"][0].get("pitchHand", {}).get("code", "R")


def mlb_pitcher_k(pid: str, opp: str, line: float, season: int) -> tuple[float, list[str], float] | None:
    from .tier import mlb_pitch_log
    log = mlb_pitch_log(pid)
    if len(log) < 5:
        return None
    k = sum(float(g["x"].get("strikeOuts") or 0) for g in log)
    bf_all = [float(g["x"].get("battersFaced") or 0) for g in log]
    kp = (k + LEAGUE_K * 100) / (sum(bf_all) + 100)
    bf = 0.6 * (sum(bf_all[:5]) / min(5, len(bf_all))) + 0.4 * (sum(bf_all) / len(bf_all))
    hand = pitch_hand(pid)
    why = [f"strikes out {kp * 100:.1f}% of batters (league {LEAGUE_K * 100:.1f}%), faces about {bf:.0f} a start"]
    p = kp
    o = opp_k_rate(opp, hand, season)
    if o:
        ok = LEAGUE_K + OPP_SHRINK * (o[0] - LEAGUE_K)
        num = kp * ok / LEAGUE_K
        p = num / (num + (1 - kp) * (1 - ok) / (1 - LEAGUE_K))
        why.append(f"{opp} strikes out {o[0] * 100:.1f}% vs {'lefties' if hand == 'L' else 'righties'}")
    mean = bf * p
    why.append(f"projects {mean:.1f} strikeouts")
    return nb_over(mean, line, 0.22), why, mean


def price(league: str, stat: str, opp: str | None, pid: str | None, line: float, season: int) -> tuple[float, list[str], float] | None:
    """(model P(over) at the line, its reasons, projected mean), or None when there is no context model for this prop."""
    if not pid or not opp:
        return None
    try:
        if league == "NHL" and stat == "Shots On Goal":
            return nhl_sog(pid, opp, line)
        if league == "NHL" and stat == "Goalie Saves":
            return nhl_saves(pid, opp, line)
        if league == "MLB" and stat == "Pitcher Strikeouts":
            return mlb_pitcher_k(pid, opp, line, season)
    except Exception:
        return None
    return None


# ------------------------------------------------------------------ game-log model: the second source when no book prices a prop
LOG_HALF_LIFE = 8           # games: last week's game counts twice as much as the one eight games back


def log_model(vals: list[float], line: float) -> tuple[float, list[str], float] | None:
    """(P(over), reasons, projected mean) from his own games alone, newest first: a recency-weighted mean and spread
    fitted as a gamma-Poisson count, so a line that sits between his outcomes gets a smooth chance rather than a raw
    tally. Used only when no sportsbook prices the prop; None under 5 games."""
    v = [max(0.0, float(x)) for x in vals[:30]]
    if len(v) < 5:
        return None
    w = [0.5 ** (i / LOG_HALF_LIFE) for i in range(len(v))]
    sw = sum(w)
    m = sum(a * b for a, b in zip(w, v)) / sw
    sd = math.sqrt(sum(a * (b - m) ** 2 for a, b in zip(w, v)) / sw)
    if m <= 0:
        p = 0.0
    else:
        cv = math.sqrt(max(sd * sd - m, 0.0025 * m * m)) / m        # at least Poisson spread, never tighter than CV 0.05
        p = nb_over(m, line, cv)
    p = min(0.98, max(0.02, p))
    return p, [f"game-log model: recency-weighted average {m:.1f} over his last {len(v)} games (spread {sd:.1f})"], m


# ------------------------------------------------------------------ matchup strength for the prop card
@functools.lru_cache(maxsize=None)
def mlb_k_table(hand: str, season: int) -> dict:
    """{team: strikeout rate vs this throwing hand} for every MLB team."""
    out, seen = {}, set()
    for abbr, tid in _mlb_team_ids().items():                      # aliases (AZ/ARI, CWS/CHW...) share an id: count each team once
        if tid in seen:
            continue
        seen.add(tid)
        r = opp_k_rate(abbr, hand, season)
        if r:
            out[abbr] = r[0]
    return out


@functools.lru_cache(maxsize=None)
def probable_starter(team: str, date: str) -> dict | None:
    """The starter `team` faces on `date`: name, hand, season ERA and strikeout rate."""
    tid = _mlb_team_ids().get(team)
    s = _get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=probablePitcher")
    for d in s.get("dates", []):
        for g in d["games"]:
            sides = g["teams"]
            for me, them in (("home", "away"), ("away", "home")):
                if sides[me]["team"]["id"] == tid and sides[them].get("probablePitcher"):
                    pp = sides[them]["probablePitcher"]
                    st = _get(f"https://statsapi.mlb.com/api/v1/people/{pp['id']}/stats?stats=season&group=pitching&season={date[:4]}")
                    x = (st["stats"][0]["splits"] or [{}])[-1].get("stat", {}) if st.get("stats") else {}
                    bf = x.get("battersFaced") or 0
                    return {"name": pp["fullName"], "id": str(pp["id"]), "hand": pitch_hand(str(pp["id"])), "era": x.get("era"),
                            "k": (x.get("strikeOuts") or 0) / bf if bf else None}
    return None


# ------------------------------------------------------------------ MLB matchups: batter vs pitcher, pitcher vs lineup
def _line(st: dict) -> dict:
    pa = st.get("plateAppearances") or 0
    return {"pa": pa, "ab": st.get("atBats") or 0, "h": st.get("hits") or 0, "hr": st.get("homeRuns") or 0,
            "k": st.get("strikeOuts") or 0, "bb": st.get("baseOnBalls") or 0, "rbi": st.get("rbi") or 0,
            "avg": st.get("avg") or "", "ops": st.get("ops") or ""}


@functools.lru_cache(maxsize=None)
def bvp(batter_id: str, pitcher_id: str) -> dict | None:
    """Career regular-season line of a batter against one pitcher (statsapi vsPlayerTotal); None if they never met."""
    r = _get(f"https://statsapi.mlb.com/api/v1/people/{batter_id}/stats?stats=vsPlayer&opposingPlayerId={pitcher_id}&group=hitting")
    for st in r.get("stats", []):
        if st["type"]["displayName"] == "vsPlayerTotal" and st["splits"]:
            out = _line(st["splits"][0]["stat"])
            return out if out["pa"] else None
    return None


@functools.lru_cache(maxsize=None)
def active_roster(team: str) -> tuple:
    """((name, id, position), ...) on the team's active roster."""
    tid = _mlb_team_ids().get(team)
    if not tid:
        return ()
    ro = _get(f"https://statsapi.mlb.com/api/v1/teams/{tid}/roster?rosterType=active")
    return tuple((p["person"]["fullName"], str(p["person"]["id"]), p["position"]["abbreviation"]) for p in ro.get("roster", []))


def batter_vs_staff(batter_id: str, opp: str, date: str) -> dict | None:
    """The hitter's career line against tonight's starter and every arm in the opponent's active bullpen he has faced."""
    sp = probable_starter_for_opp(opp, date)
    arms = [(n, i) for n, i, pos in active_roster(opp) if pos in ("P", "TWP")]
    rows = []
    for n, i in arms:
        x = bvp(batter_id, i)
        if x:
            rows.append({"name": n, "id": i, "role": "SP" if sp and sp.get("id") == i else "RP", "hand": pitch_hand(i), **x})
    if sp and not any(r["id"] == sp["id"] for r in rows):
        x = bvp(batter_id, sp["id"])
        rows.append({"name": sp["name"], "id": sp["id"], "role": "SP", "hand": sp["hand"], **(x or {"pa": 0})})
    rows.sort(key=lambda r: (r["role"] != "SP", -r.get("pa", 0)))
    return {"starter": sp["name"] if sp else None, "rows": rows} if rows else None


@functools.lru_cache(maxsize=None)
def probable_starter_for_opp(opp: str, date: str) -> dict | None:
    """The starter `opp` sends out on `date` (the pitcher a hitter facing `opp` will see)."""
    tid = _mlb_team_ids().get(opp)
    s = _get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=probablePitcher")
    for d in s.get("dates", []):
        for g in d["games"]:
            for side in ("home", "away"):
                if g["teams"][side]["team"]["id"] == tid and g["teams"][side].get("probablePitcher"):
                    pp = g["teams"][side]["probablePitcher"]
                    return {"name": pp["fullName"], "id": str(pp["id"]), "hand": pitch_hand(str(pp["id"]))}
    return None


def pitcher_vs_lineup(pitcher_id: str, opp: str) -> dict | None:
    """Tonight's opposing hitters (active roster) against this pitcher, career regular season, plus their total."""
    tid = _mlb_team_ids().get(opp)
    if not tid:
        return None
    r = _get(f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats?stats=vsTeam&opposingTeamId={tid}&group=pitching")
    hitters = {i: n for n, i, pos in active_roster(opp) if pos != "P"}
    agg = {}
    for st in r.get("stats", []):
        if st["type"]["displayName"] != "vsTeam":
            continue
        for s in st["splits"]:
            b = s.get("batter") or {}
            bid = str(b.get("id", ""))
            if bid not in hitters:
                continue
            x = _line(s["stat"])
            a = agg.setdefault(bid, {"name": hitters[bid], "pa": 0, "ab": 0, "h": 0, "hr": 0, "k": 0, "bb": 0, "rbi": 0})
            for k in ("pa", "ab", "h", "hr", "k", "bb", "rbi"):
                a[k] += x[k]
    rows = sorted((a for a in agg.values() if a["pa"]), key=lambda a: -a["pa"])
    for a in rows:
        a["avg"] = f"{a['h'] / a['ab']:.3f}".lstrip("0") if a["ab"] else ""
    if not rows:
        return None
    tot = {k: sum(a[k] for a in rows) for k in ("pa", "ab", "h", "hr", "k", "bb", "rbi")}
    tot["avg"] = f"{tot['h'] / tot['ab']:.3f}".lstrip("0") if tot["ab"] else ""
    tot["kpct"] = round(tot["k"] / tot["pa"], 3) if tot["pa"] else None
    return {"rows": rows, "total": tot}


def matchup(league: str, stat: str, opp: str | None, pid: str | None, team: str = "", date: str = "") -> dict | None:
    """How tonight's opponent stacks up for this stat: label, value, rank (1 = most), out of, and which side it helps."""
    if not opp:
        return None
    try:
        if league == "NHL":
            t = nhl_teams()
            o = _nhl_opp(opp)
            key, label, helps = {"Goalie Saves": ("sf", "shots taken per game", "over")}.get(
                stat, ("sa", "shots allowed per game", "over") if stat == "Shots On Goal" else ("ga", "goals allowed per game", "over"))
            if o not in t["teams"]:
                return None
            order = sorted(t["teams"], key=lambda k: -t["teams"][k][key])
            return {"label": f"{o} {label}", "value": f"{t['teams'][o][key]:.1f} (league {t['league'][key]:.1f})",
                    "rank": order.index(o) + 1, "of": len(order), "high_helps": helps}
        if league == "MLB" and stat == "Pitcher Strikeouts" and pid:
            hand = pitch_hand(pid)
            tab = mlb_k_table(hand, int(date[:4]) if date else 2026)
            ids = _mlb_team_ids()
            me = next((k for k in tab if ids.get(k) == ids.get(opp)), None)
            if me is None:
                return None
            order = sorted(tab, key=lambda k: -tab[k])
            return {"label": f"{opp} strikeout rate vs {'lefties' if hand == 'L' else 'righties'}", "value": f"{tab[me] * 100:.1f}%",
                    "rank": order.index(me) + 1, "of": len(order), "high_helps": "over"}
        if league == "MLB" and team and date:
            sp = probable_starter(team, date)
            if sp:
                bits = [f"{sp['hand']}HP"] + ([f"{sp['era']} ERA"] if sp.get("era") else []) + ([f"{sp['k'] * 100:.0f}% K rate"] if sp.get("k") else [])
                return {"label": f"Faces {sp['name']}", "value": ", ".join(bits), "rank": None, "of": None, "high_helps": None}
    except Exception:
        return None
    return None
