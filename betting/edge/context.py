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
                  for k, f in (("sa", "shotsAgainstPerGame"), ("sf", "shotsForPerGame"))}
    lg = {k: sum(v[k] for v in out.values()) / len(out) for k in ("sa", "sf")}
    return {"teams": out, "league": lg}


def _nhl_opp(opp: str) -> str:
    from .tier import NHL_API
    return NHL_API.get(opp, opp)


def nhl_sog(pid: str, opp: str, line: float) -> tuple[float, list[str]] | None:
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
    return nb_over(mean, line, 0.30), why


def nhl_saves(pid: str, opp: str, line: float) -> tuple[float, list[str]] | None:
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
    return nb_over(mean, line, 0.18), why


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


def mlb_pitcher_k(pid: str, opp: str, line: float, season: int) -> tuple[float, list[str]] | None:
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
    return nb_over(mean, line, 0.22), why


def price(league: str, stat: str, opp: str | None, pid: str | None, line: float, season: int) -> tuple[float, list[str]] | None:
    """Model P(over) at the line with its reasons, or None when there is no context model for this prop."""
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
