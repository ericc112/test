"""Soccer passes attempted, the concise way (ESPN data, no keys).

    player passes = team passes x player share x minutes / 90
    team passes   = possession x match passes (both teams)
    possession    = log5(team possession, opponent possession) +/- home edge,
                    shrunk halfway to 50% when the teams come from different leagues

The count is gamma-Poisson: Poisson noise plus ~17% game-to-game variation in share and tempo
(measured on regular starters, Oct 2026: 14.5% with team passes known, 16-20% without).
Minutes are drawn from his own recent starts.
"""
from __future__ import annotations

import concurrent.futures as cf

import numpy as np

from .grade import _get, soccer_player_stats

SITE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
HOME_EDGE = 0.02      # home sides average ~2 pts more possession
EXTRA_CV = 0.17       # game-to-game variation beyond Poisson (share + tempo)
CUPS = ("uefa.champions", "uefa.europa", "uefa.europa.conf")


# ------------------------------------------------------------------ pure model
def log5(a: float, b: float) -> float:
    """Possession share for a team that averages `a` vs an opponent that averages `b`."""
    return a * (1 - b) / (a * (1 - b) + b * (1 - a))


def possession(team_poss: float, opp_poss: float, home: bool | None, same_league: bool = True) -> float:
    p = log5(team_poss, opp_poss)
    if not same_league:  # possession is inflated for teams that dominate weaker leagues
        p = 0.5 + 0.5 * (p - 0.5)
    if home is not None:
        p += HOME_EDGE if home else -HOME_EDGE
    return float(min(max(p, 0.2), 0.8))


def project(team_passes: float, share: float, minutes: list[float] | None = None, line: float | None = None,
            n: int = 200_000, seed: int = 7) -> dict:
    """Distribution of a player's passes attempted. `share` is per 90 minutes of his team's passes."""
    rng = np.random.default_rng(seed)
    mins = rng.choice(np.array(minutes or [90.0]), n) / 90
    mu = team_passes * share * mins
    k = 1 / EXTRA_CV ** 2
    x = rng.poisson(mu * rng.gamma(k, 1 / k, n))
    out = {"mean": float(x.mean()), "median": float(np.median(x)), "p10": float(np.percentile(x, 10)), "p90": float(np.percentile(x, 90))}
    if line is not None:
        out.update(p_over=float((x > line).mean()), p_under=float((x < line).mean()), p_push=float((x == line).mean()))
    return out


# ------------------------------------------------------------------ ESPN data
def summary(event_id: str) -> dict:
    return _get(f"{SITE}/all/summary?event={event_id}")


def team_matches(team_id: str, n: int = 10, seasons=("2026", "2025")) -> list[dict]:
    """Last n completed matches (domestic league + European cups): possession and passes for both sides."""
    dom = (_get(f"{SITE}/all/teams/{team_id}").get("team") or {}).get("defaultLeague", {}).get("slug")
    evs = set()
    for lg in [x for x in (dom, *CUPS) if x]:
        for s in seasons:
            try:
                for e in _get(f"{SITE}/{lg}/teams/{team_id}/schedule?season={s}").get("events", []):
                    if e["competitions"][0]["status"]["type"].get("completed"):
                        evs.add((e["date"], lg, e["id"]))
            except Exception:
                continue
    recent = sorted(evs, reverse=True)[:n]

    def one(ev):
        date, lg, eid = ev
        s = summary(eid)
        teams = {str(t["team"]["id"]): {x["name"]: x.get("displayValue") for x in t.get("statistics", [])}
                 for t in (s.get("boxscore") or {}).get("teams", [])}
        comp = s["header"]["competitions"][0]
        home = next((c["homeAway"] == "home" for c in comp["competitors"] if str(c["team"]["id"]) == str(team_id)), None)
        me = teams.get(str(team_id), {})
        opp = next((v for k, v in teams.items() if k != str(team_id)), {})
        try:
            return {"date": date[:10], "league": lg, "event_id": eid, "home": home, "summary": s,
                    "poss": float(me["possessionPct"]) / 100, "passes": float(me["totalPasses"]),
                    "match_passes": float(me["totalPasses"]) + float(opp["totalPasses"])}
        except (KeyError, TypeError, ValueError):
            return None

    with cf.ThreadPoolExecutor(8) as ex:
        return [m for m in ex.map(one, recent) if m]


def player_match(m: dict, team_id: str, player_id: str) -> dict | None:
    """Minutes and passes attempted for one player in one match (None if he didn't play)."""
    played = False
    for r in m["summary"].get("rosters", []):
        if str(r["team"]["id"]) == str(team_id):
            for p in r.get("roster", []):
                if str(p["athlete"]["id"]) == str(player_id):
                    played = bool(p.get("starter") or p.get("subbedIn"))
                    starter = bool(p.get("starter"))
    if not played:
        return None
    st = soccer_player_stats(m["league"], m["event_id"], team_id, player_id)
    passes = (st.get("accuratePasses") or 0) + (st.get("inaccuratePasses") or 0)
    return {"date": m["date"], "starter": starter, "minutes": st.get("minutes") or 0, "passes": passes, "team_passes": m["passes"]}


def passes_model(player_id: str, team_id: str, opp_id: str, line: float | None = None, home: bool | None = None,
                 n: int = 10, poss: float | None = None) -> dict:
    tm, om = team_matches(team_id, n), team_matches(opp_id, n)
    with cf.ThreadPoolExecutor(8) as ex:
        games = [g for g in ex.map(lambda m: player_match(m, team_id, player_id), tm) if g]
    starts = [g for g in games if g["starter"] and g["minutes"] >= 45]
    if not starts:
        raise ValueError("no recent starts with passing data for this player")
    share = sum(g["passes"] for g in starts) / sum(g["team_passes"] * g["minutes"] / 90 for g in starts)
    t_poss, o_poss = np.mean([m["poss"] for m in tm]), np.mean([m["poss"] for m in om])
    same = _dom(tm) == _dom(om)
    p = poss if poss is not None else possession(t_poss, o_poss, home, same)
    match_passes = (np.mean([m["match_passes"] for m in tm]) + np.mean([m["match_passes"] for m in om])) / 2
    team_passes = p * match_passes
    proj = project(team_passes, share, [g["minutes"] for g in starts], line)
    hist = [g["passes"] for g in starts]
    out = {"starts": starts, "share": share, "team_poss": t_poss, "opp_poss": o_poss, "same_league": same, "possession": p,
           "match_passes": match_passes, "team_passes": team_passes, **proj}
    if line is not None:
        out["hist_over"], out["hist_n"] = sum(h > line for h in hist) / len(hist), len(hist)
    return out


def _dom(matches: list[dict]) -> str | None:
    lgs = [m["league"] for m in matches if m["league"] not in CUPS]
    return max(set(lgs), key=lgs.count) if lgs else None
