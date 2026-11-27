"""Nightly simulation audit (NBA): where the simulation went wrong, game by game and player by player, against the
box score, and which known fix each repeated miss points at.

Reads each game's last pre-tip prediction (data/nba_pretip/DATE.json, written by nba_pp.save_pretip on every
published-logic run) and the final box scores. For nights before that file existed it falls back to the saved
priced boards (win chance and the projected rotation only).

  team       the simulation's winner, margin and total against DraftKings' line and the result
  minutes    late scratches (projected 10+ minutes, didn't play), surprise minutes (15+ minutes, projected under 8),
             the biggest misses, and the error when two or more starters were out
  rates      production per minute (points, rebounds, assists) against the simulation's, by role
Each night is saved to data/sim_audit/DATE.json; `findings()` reads every audited night and names the patterns that
repeat, each tied to a switch that is tested walk-forward and then run in shadow before it touches a published number
(the user's rule: beat the current logic on 200+ legs or 14 days, on log loss and label calibration).

  python -m edge sim-audit [--date YYYY-MM-DD]"""
from __future__ import annotations

import datetime as dt
import glob
import gzip
import json
import math
import os

import numpy as np

from .blend import HERE

AUDIT_DIR = os.path.join(HERE, "data", "sim_audit")
PRETIP_DIR = os.path.join(HERE, "data", "nba_pretip")


def _imp(a):
    if a is None:
        return None
    a = float(a)
    return 100 / (a + 100) if a > 0 else -a / (-a + 100)


def _games(date: str) -> dict:
    from gamesim import data as gs_data, nba as gnba
    d = dt.date.fromisoformat(date)
    G = gnba.season_games("nba", d.strftime("%Y%m%d"), (d + dt.timedelta(days=1)).strftime("%Y%m%d"))
    return {g["id"]: g for g in G if g["final"] and gs_data.us_day(g["date"]) == date}


def _pretip(date: str, boards: list[str] | None = None) -> tuple[dict, str]:
    p = os.path.join(PRETIP_DIR, f"{date}.json")
    if os.path.exists(p):
        return json.load(open(p)), "pre-tip predictions"
    # fallback: the priced boards (last run before each tip): win chance and the projected rotation
    out = {}
    for path in boards or [os.path.join(HERE, "data", "nba_boards", f"{date}.json.gz")]:
        if not os.path.exists(path):
            continue
        for r in json.load(gzip.open(path, "rt")):
            gid, pulled = str(r.get("event_id")), r.get("pulled") or ""
            if not r.get("start") or not pulled or pulled > dt.datetime.fromisoformat(r["start"]).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"):
                continue
            rec = out.setdefault(gid, {"gid": gid, "players": {}, "pulled": ""})
            if pulled >= rec["pulled"]:
                rec.update(pulled=pulled, p_home=r.get("p_home"))
                side = "home" if r.get("team") == r.get("home") else "away"
                for x in r.get("rotation") or []:
                    rec["players"][x["name"]] = {"name": x["name"], "side": side, "min_proj": x["min"], "season_min": x["season"], "starter_last": x.get("starter")}
                rec.setdefault("outs", {})[side] = [o["name"] for o in (r.get("outs") or [])]
    return out, "priced boards (win chance and rotation only)"


def audit(date: str, boards: list[str] | None = None, save: bool = True) -> dict:
    from gamesim import nba as gnba
    P, source = _pretip(date, boards)
    G = _games(date)
    rows_t, rows_m, rows_r, notes = [], [], [], []
    for gid, rec in P.items():
        g = G.get(gid)
        if not g:
            continue
        hs, as_ = g["score"]["home"], g["score"]["away"]
        ln = g.get("line") or {}
        mk_home = None
        if ln.get("ml_home") is not None and ln.get("ml_away") is not None:
            a, b = _imp(ln["ml_home"]), _imp(ln["ml_away"]); mk_home = a / (a + b)
        t = {"game": f"{g['away']} @ {g['home']}", "p_home": rec.get("p_home"), "mk_home": mk_home, "home_won": hs > as_,
             "margin": hs - as_, "total": hs + as_, "spread": ln.get("spread_home"), "mk_total": ln.get("total")}
        if rec.get("mean_home") is not None:
            t["sim_margin"] = rec["mean_home"] - rec["mean_away"]; t["sim_total"] = rec["mean_home"] + rec["mean_away"]
        rows_t.append(t)
        # players
        box = gnba._box_cached("nba", gid)
        actual = {}
        for team, side in ((g["home"], "home"), (g["away"], "away")):
            for r in box.get(team) or []:
                actual[r["name"]] = {"side": side, "min": 0.0 if r["dnp"] else float(r["min"]), "pts": r["pts"], "reb": r["oreb"] + r["dreb"], "ast": r["ast"],
                                     "starter": r["starter"], "dnp": r["dnp"], "reason": r.get("reason") or ""}
        proj = {p["name"]: p for p in rec.get("players", {}).values()}
        for name, p in proj.items():
            a = actual.get(name)
            am = a["min"] if a else 0.0
            pm = float(p.get("min_proj") or 0)
            kind = "late scratch" if pm >= 10 and am == 0 else ("surprise minutes" if am >= 15 and pm < 8 else "")
            rows_m.append({"game": t["game"], "name": name, "side": p["side"], "proj": pm, "act": am, "kind": kind,
                           "outs_on_team": len((rec.get("outs") or {}).get(p["side"], []))})
            if a and am >= 15 and pm >= 15 and p.get("pts") is not None and p.get("min"):
                for k in ("pts", "reb", "ast"):
                    rows_r.append({"name": name, "stat": k, "top": pm >= 26, "proj36": 36 * p[k] / max(p["min"], 1), "act36": 36 * a[k] / am})
        for name, a in actual.items():                          # played big minutes the simulation didn't have at all
            if name not in proj and a["min"] >= 15:
                rows_m.append({"game": t["game"], "name": name, "side": a["side"], "proj": 0.0, "act": a["min"], "kind": "surprise minutes",
                               "outs_on_team": len((rec.get("outs") or {}).get(a["side"], []))})
    rep = summarize(date, rows_t, rows_m, rows_r, source)
    if save and rows_t:
        os.makedirs(AUDIT_DIR, exist_ok=True)
        json.dump({**rep, "rows": {"team": rows_t, "minutes": rows_m, "rates": rows_r}}, open(os.path.join(AUDIT_DIR, f"{date}.json"), "w"), default=float)
    return rep


def summarize(date, T, M, Rr, source) -> dict:
    rep = {"date": date, "source": source, "games": len(T)}
    if T:
        sim_right = sum((t["p_home"] > 0.5) == t["home_won"] for t in T if t["p_home"] is not None)
        mk_right = sum((t["mk_home"] > 0.5) == t["home_won"] for t in T if t["mk_home"] is not None)
        br = lambda k: float(np.mean([(t[k] - t["home_won"]) ** 2 for t in T if t[k] is not None]))
        rep["team"] = {"sim_winners": sim_right, "market_winners": mk_right, "brier_sim": round(br("p_home"), 3), "brier_market": round(br("mk_home"), 3),
                       "disagreements": [{"game": t["game"], "sim_home": round(t["p_home"], 3), "market_home": round(t["mk_home"], 3),
                                          "home_won": t["home_won"], "margin": t["margin"]} for t in T
                                         if t["p_home"] is not None and t["mk_home"] is not None and (t["p_home"] > .5) != (t["mk_home"] > .5)]}
        sm = [t for t in T if t.get("sim_margin") is not None and t.get("spread") is not None]
        if sm:
            rep["team"]["margin_rmse_sim"] = round(math.sqrt(np.mean([(t["sim_margin"] - t["margin"]) ** 2 for t in sm])), 2)
            rep["team"]["margin_rmse_market"] = round(math.sqrt(np.mean([(-t["spread"] - t["margin"]) ** 2 for t in sm])), 2)
            rep["team"]["total_rmse_sim"] = round(math.sqrt(np.mean([(t["sim_total"] - t["total"]) ** 2 for t in sm if t.get("mk_total")])), 2)
            rep["team"]["total_rmse_market"] = round(math.sqrt(np.mean([(t["mk_total"] - t["total"]) ** 2 for t in sm if t.get("mk_total")])), 2)
    if M:
        normal = [m for m in M if not m["kind"]]
        rep["minutes"] = {"mae": round(float(np.mean([abs(m["proj"] - m["act"]) for m in normal])), 2) if normal else None,
                          "mae_2plus_out": round(float(np.mean([abs(m["proj"] - m["act"]) for m in normal if m["outs_on_team"] >= 2])), 2) if any(m["outs_on_team"] >= 2 for m in normal) else None,
                          "late_scratches": [f"{m['name']} ({m['game']}, projected {m['proj']:.0f})" for m in M if m["kind"] == "late scratch"],
                          "surprise_minutes": [f"{m['name']} ({m['game']}, {m['act']:.0f} min, projected {m['proj']:.0f})" for m in M if m["kind"] == "surprise minutes"],
                          "biggest_misses": [f"{m['name']} ({m['game']}): projected {m['proj']:.0f}, played {m['act']:.0f}" for m in sorted(normal, key=lambda m: -abs(m['proj'] - m['act']))[:5]]}
    if Rr:
        out = {}
        for k in ("pts", "reb", "ast"):
            for role, f in (("top", True), ("bench", False)):
                x = [r["act36"] - r["proj36"] for r in Rr if r["stat"] == k and r["top"] == f]
                if len(x) >= 5:
                    out[f"{k}_{role}"] = {"n": len(x), "bias_per36": round(float(np.mean(x)), 2), "se": round(float(np.std(x) / math.sqrt(len(x))), 2)}
        rep["rates"] = out
    return rep


def findings(min_games: int = 30) -> list[dict]:
    """Patterns across every audited night, each tied to the switch that addresses it."""
    T, M, Rr = [], [], []
    for p in sorted(glob.glob(os.path.join(AUDIT_DIR, "*.json"))):
        d = json.load(open(p)).get("rows") or {}
        T += d.get("team", []); M += d.get("minutes", []); Rr += d.get("rates", [])
    out = []
    sm = [t for t in T if t.get("sim_margin") is not None and t.get("spread") is not None]
    if len(sm) >= min_games:
        es = math.sqrt(np.mean([(t["sim_margin"] - t["margin"]) ** 2 for t in sm])); em = math.sqrt(np.mean([(-t["spread"] - t["margin"]) ** 2 for t in sm]))
        if es > em:
            out.append({"pattern": f"team margins: simulation {es:.2f} vs market {em:.2f} points (RMSE, {len(sm)} games)",
                        "switch": "TEAM_MARKET_W (team-level market anchor)", "status": "candidate"})
    normal = [m for m in M if not m["kind"]]
    two = [abs(m["proj"] - m["act"]) for m in normal if m["outs_on_team"] >= 2]; rest = [abs(m["proj"] - m["act"]) for m in normal if m["outs_on_team"] < 2]
    if len(two) >= 40 and np.mean(two) > np.mean(rest) + 0.5:
        out.append({"pattern": f"minutes miss by {np.mean(two):.1f} with 2+ teammates out vs {np.mean(rest):.1f} otherwise ({len(two)} player-games)",
                    "switch": "MINUTES_SHARE = headroom", "status": "in shadow v3"})
    surprise = [m for m in M if m["kind"] == "surprise minutes"]
    if len(surprise) >= 10:
        out.append({"pattern": f"{len(surprise)} surprise-minutes players across audited nights (a coach's call the box scores didn't show)",
                    "switch": "lineup lock: re-price on announced starters", "status": "needs announced lineups (data source)"})
    for k in ("pts", "reb", "ast"):
        for role, f in (("top", True), ("bench", False)):
            x = [r["act36"] - r["proj36"] for r in Rr if r["stat"] == k and r["top"] == f]
            if len(x) >= 60:
                b, se = float(np.mean(x)), float(np.std(x) / math.sqrt(len(x)))
                if abs(b) > 2.5 * se:
                    out.append({"pattern": f"{k} per 36, {'starters' if f else 'bench'}: actual {b:+.2f} vs simulated ({len(x)} player-games, SE {se:.2f})",
                                "switch": "per-minute rate bias (nba_model bias table / AST_FIX)", "status": "candidate"})
    return out


def markdown(rep: dict, fnd: list[dict] | None = None) -> str:
    L = [f"## Simulation audit: {rep['date']} ({rep['games']} games, from {rep['source']})"]
    t = rep.get("team")
    if t:
        L.append(f"- **Winners:** simulation {t['sim_winners']} of {rep['games']}, DraftKings favorite {t['market_winners']} of {rep['games']}; "
                 f"Brier {t['brier_sim']} vs {t['brier_market']}.")
        for d in t["disagreements"]:
            L.append(f"  - {d['game']}: simulation home {d['sim_home']:.0%}, market {d['market_home']:.0%}; home {'won' if d['home_won'] else 'lost'} ({d['margin']:+.0f}).")
        if "margin_rmse_sim" in t:
            L.append(f"- **Margins / totals (RMSE):** simulation {t['margin_rmse_sim']} / {t['total_rmse_sim']}, market {t['margin_rmse_market']} / {t['total_rmse_market']}.")
    m = rep.get("minutes")
    if m:
        L.append(f"- **Minutes:** average miss {m['mae']} ({m['mae_2plus_out']} with 2+ teammates out). Late scratches: {', '.join(m['late_scratches']) or 'none'}. "
                 f"Surprise minutes: {', '.join(m['surprise_minutes']) or 'none'}.")
        if m["biggest_misses"]:
            L.append("  - Biggest misses: " + "; ".join(m["biggest_misses"]) + ".")
    r = rep.get("rates")
    if r:
        L.append("- **Per-minute production (actual minus simulated, per 36):** " + ", ".join(f"{k} {v['bias_per36']:+.1f} (±{v['se']:.1f}, n {v['n']})" for k, v in r.items()) + ".")
    if fnd:
        L.append("- **Patterns across audited nights:**")
        L += [f"  - {f['pattern']} → {f['switch']} ({f['status']})" for f in fnd]
    return "\n".join(L)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    from gamesim.data import slate_today
    d = a.date or (dt.date.fromisoformat(slate_today()) - dt.timedelta(days=1)).isoformat()
    print(markdown(audit(d), findings()))
