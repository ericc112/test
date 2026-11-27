"""NBA pricing logic, versioned: the CURRENT logic is published; the SHADOW logic scores the same board every night
and is logged but never published. A shadow logic is promoted only when it beats the current one on held-out
graded legs (>= 200 legs or 14 days) on log loss AND label calibration; every promotion is written to
data/MODEL_CHANGELOG.md and can be rolled back.

  python -m edge.nba_model status | report | promote [--force "reason"] | rollback

Logic parameters (all optional; missing = the v1 behaviour):
  bias      "night_flat" (v1: tonight's per-stat simulation-vs-DraftKings gap, flat) | "table" (a fitted per stat x
            top5/bench table in bias_table) | "none"
  blend     {"intercept", "w_model", "w_market", "w_hist"} for NBA (v1: the global blend in adjustments.json)
  history   "raw" (v1) | "aware" (minutes-weighted, early exits dropped) | "off"
  recal     {"a", "b", "cov"}: Platt map on the selected side's logit (v1: none)
  gates     overrides of adjustments.json gates (v1: none)
  high_thin {"max_spread", ...}: High allowed with thin history when model and market agree tightly (v1: off)
  entry     "flat2" (v1: final >= break-even + 2 pts) | "se1" (recalibrated p - break-even > 1 standard error)
  push      "half" (v1: market at a whole line counts half the push as over) | "exclusive" (push removed, as the model)
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import sys

import numpy as np

from .blend import HERE

PATH = os.path.join(HERE, "data", "nba_model.json")
CHANGELOG = os.path.join(HERE, "data", "MODEL_CHANGELOG.md")
SHADOW_DIR = os.path.join(HERE, "data", "nba_shadow")
MIN_LEGS, MIN_DAYS = 200, 14
V1 = {"bias": "night_flat", "blend": None, "history": "raw", "recal": None, "gates": None, "high_thin": None, "entry": "flat2", "push": "half"}


def load() -> dict:
    if os.path.exists(PATH):
        with open(PATH) as f:
            return json.load(f)
    return {"current": {"version": 1, "name": "v1 (2026-11-04)", "params": dict(V1), "since": "2026-11-04"}, "shadow": None, "history": []}


def save(m: dict):
    with open(PATH, "w") as f:
        json.dump(m, f, indent=1, default=float)


def params(which: str = "current") -> dict:
    m = load()
    x = m.get(which)
    return {**V1, **(x or {}).get("params", {})} if x else None


def params_for(version: int | None) -> dict:
    """The parameters of a logic version (current, shadow or retired); None or unknown = current."""
    m = load()
    for x in [m.get("current"), m.get("shadow")] + m.get("history", []) + m.get("rolled_back", []):
        if x and version is not None and x.get("version") == version:
            return {**V1, **x.get("params", {})}
    return params("current")


def set_shadow(params: dict, name: str, evidence: dict | None = None):
    m = load()
    v = max([m["current"]["version"]] + [h["version"] for h in m.get("history", [])] + ([m["shadow"]["version"]] if m.get("shadow") else [])) + 1
    m["shadow"] = {"version": v, "name": name, "params": params, "since": dt.date.today().isoformat(), "backtest_evidence": evidence}
    save(m)
    return m["shadow"]


# ------------------------------------------------------------------ the shadow log and its scoring
def log_shadow(rows_cur: list[dict], rows_sh: list[dict], day: str | None = None):
    """Both logics' verdicts on tonight's standard legs, keyed by leg, for grading later."""
    os.makedirs(SHADOW_DIR, exist_ok=True)
    key = lambda r: f"{r['event_id']}|{r['player_id']}|{r['stat_key']}|{r['line']}"
    cur = {key(r): r for r in rows_cur if "error" not in r and r.get("odds_type") == "standard"}
    out = []
    for r in rows_sh:
        if "error" in r or r.get("odds_type") != "standard" or key(r) not in cur:
            continue
        c = cur[key(r)]
        out.append({"key": key(r), "event_id": r["event_id"], "player_id": r["player_id"], "stat": r["stat_key"], "line": r["line"],
                    "cur": {"side": c["side"], "p": c["p_final"], "conf": c["confidence"], "verdict": c.get("verdict_v")},
                    "sh": {"side": r["side"], "p": r["p_final"], "conf": r["confidence"], "verdict": r.get("verdict_v"),
                           "p_raw": r.get("p_uncal")}})
    m = load()
    path = os.path.join(SHADOW_DIR, f"{day or dt.date.today().isoformat()}.json.gz")
    json.dump({"current": m["current"]["version"], "shadow": (m.get("shadow") or {}).get("version"), "legs": out}, gzip.open(path, "wt"))
    return path


def _outcome(event_id: str, player_id: str, stat: str, cache: dict):
    from .grade import nba_value
    try:
        state, v = nba_value(str(event_id), str(player_id), stat, cache)
    except Exception:
        return None
    return v if state == "final" else None


def score_shadow() -> dict:
    """Grade every logged shadow night: log loss, Brier and label calibration for current vs shadow, same legs."""
    cache, legs = {}, []
    days = sorted(f[:10] for f in os.listdir(SHADOW_DIR)) if os.path.isdir(SHADOW_DIR) else []
    for d in days:
        S = json.load(gzip.open(os.path.join(SHADOW_DIR, f"{d}.json.gz"), "rt"))
        for l in S["legs"]:
            v = _outcome(l["event_id"], l["player_id"], l["stat"], cache)
            if v is None or v == l["line"]:
                continue
            for k in ("cur", "sh"):
                l[k]["y"] = 1.0 if (v > l["line"]) == (l[k]["side"] == "over") else 0.0
            legs.append({**l, "day": d})
    return summarize(legs)


def summarize(legs: list[dict]) -> dict:
    out = {"legs": len(legs), "days": len({l["day"] for l in legs})}
    for k in ("cur", "sh"):
        if not legs:
            break
        p = np.clip([l[k]["p"] for l in legs], 1e-4, 1 - 1e-4); y = np.array([l[k]["y"] for l in legs])
        lab = {}
        for c in ("High", "Medium", "Low"):
            S = [l for l in legs if l[k]["conf"] == c]
            if S:
                lab[c] = {"n": len(S), "pred": float(np.mean([l[k]["p"] for l in S])), "real": float(np.mean([l[k]["y"] for l in S]))}
        out[k] = {"logloss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))), "brier": float(np.mean((p - y) ** 2)),
                  "labels": lab, "label_gap": float(np.mean([abs(v["real"] - v["pred"]) for v in lab.values()])) if lab else None}
    if legs:
        out["eligible"] = out["legs"] >= MIN_LEGS or out["days"] >= MIN_DAYS
        out["shadow_wins"] = out["sh"]["logloss"] < out["cur"]["logloss"] and (out["sh"]["label_gap"] or 0) <= (out["cur"]["label_gap"] or 0)
    return out


def promote(force: str | None = None) -> dict:
    m = load()
    if not m.get("shadow"):
        raise SystemExit("no shadow logic to promote")
    ev = score_shadow()
    ok = ev.get("eligible") and ev.get("shadow_wins")
    if not ok and not force:
        raise SystemExit(f"not promoted: shadow has {ev.get('legs', 0)} graded legs over {ev.get('days', 0)} days "
                         f"(needs {MIN_LEGS} legs or {MIN_DAYS} days) and must beat current on log loss and label calibration: {json.dumps(ev)[:400]}")
    old = m["current"]
    m.setdefault("history", []).append({**old, "retired": dt.date.today().isoformat()})
    m["current"] = {**m["shadow"], "since": dt.date.today().isoformat(), "live_evidence": ev}
    m["shadow"] = None
    save(m)
    with open(CHANGELOG, "a") as f:
        f.write(f"\n## {dt.date.today().isoformat()}: v{old['version']} -> v{m['current']['version']} ({m['current']['name']})\n"
                f"- Live shadow evidence: {ev.get('legs')} graded legs over {ev.get('days')} days; log loss current "
                f"{ev.get('cur', {}).get('logloss')} vs new {ev.get('sh', {}).get('logloss')}; label gap {ev.get('cur', {}).get('label_gap')} -> {ev.get('sh', {}).get('label_gap')}\n"
                + (f"- Backtest evidence: {json.dumps(m['current'].get('backtest_evidence'))[:600]}\n" if m['current'].get('backtest_evidence') else "")
                + (f"- FORCED: {force}\n" if force and not ok else "")
                + f"- Rollback: `python -m edge.nba_model rollback` restores v{old['version']}.\n")
    return m["current"]


def rollback() -> dict:
    m = load()
    if not m.get("history"):
        raise SystemExit("nothing to roll back to")
    prev = m["history"].pop()
    bad = m["current"]
    m["current"] = {k: v for k, v in prev.items() if k != "retired"}
    m["current"]["since"] = dt.date.today().isoformat()
    m.setdefault("rolled_back", []).append({**bad, "rolled_back": dt.date.today().isoformat()})
    save(m)
    with open(CHANGELOG, "a") as f:
        f.write(f"\n## {dt.date.today().isoformat()}: ROLLBACK v{bad['version']} -> v{m['current']['version']}\n")
    return m["current"]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "status":
        m = load()
        print(json.dumps({"current": m["current"]["name"], "shadow": (m.get("shadow") or {}).get("name"), "history": [h["name"] for h in m.get("history", [])]}, indent=1))
    elif cmd == "report":
        print(json.dumps(score_shadow(), indent=1))
    elif cmd == "promote":
        force = sys.argv[sys.argv.index("--force") + 1] if "--force" in sys.argv else None
        print(promote(force))
    elif cmd == "rollback":
        print(rollback())
