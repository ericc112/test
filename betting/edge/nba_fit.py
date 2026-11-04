"""Fixes 1-3 and 5 on a backtest corpus, walk-forward by day (every number for day d is fitted on days before d only).
  python -m edge.nba_fit TAG

  residual bias   per stat x (projected top five / bench), shrunk toward the stat-wide value by n / (n + 50)
  blends          old (flat same-night bias, weights .45/.41/.07, intercept +.046, history regressed n/(n+10));
                  market only; market-dominant priors with model weight .2 / .3 / .45 (history in or out, raw or
                  minutes-aware); a walk-forward logistic fit with bootstrap intervals
  selected side   the higher side of each leg, Platt-recalibrated on earlier days' selected legs
  labels          realized vs predicted per label under the old gates and under re-derived gates
Writes data/nba_bt/fit_TAG.json."""
from __future__ import annotations

import gzip
import json
import os
import sys

import numpy as np

from .blend import HERE

OLD = {"intercept": 0.0461, "w_model": 0.4496, "w_market": 0.4135, "w_hist": 0.0705}
STATS = ("pts", "reb", "ast", "tpm", "pra", "pr", "pa", "ra")
K_SHRINK = 50.0
MIN_TRAIN = 300


def lg(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def sg(z):
    return 1 / (1 + np.exp(-np.asarray(z, float)))


def ll(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier(p, y):
    return float(np.mean((p - y) ** 2))


def load_legs(tag: str) -> list[dict]:
    c = json.load(gzip.open(os.path.join(HERE, "data", "nba_bt", f"corpus_{tag}.json.gz"), "rt"))
    L = []
    for l in c["legs"]:
        if l["q"] is None or not (0 < l["p_over"] < 1 - l["p_push"]) or l["y"] == l["line"]:
            continue
        l = dict(l)
        l["m_raw"] = l["p_over"] / (1 - l["p_push"])
        l["yo"] = 1.0 if l["y"] > l["line"] else 0.0
        l["seg"] = (l["stat"], "top5" if l["top5"] else "bench")
        L.append(l)
    return L


# ------------------------------------------------------------------ residual bias (Fix 1, segment-aware)
def fit_bias(train: list[dict]) -> dict:
    """Mean logit gap (simulation - DraftKings) per stat, and per stat x segment shrunk toward it by n/(n+K)."""
    out = {}
    for st in STATS:
        S = [l for l in train if l["stat"] == st]
        if not S:
            continue
        base = float(np.mean(lg([l["m_raw"] for l in S]) - lg([l["q"] for l in S])))
        out[st] = base
        for sgm in ("top5", "bench"):
            T = [l for l in S if l["seg"][1] == sgm]
            if T:
                g = float(np.mean(lg([l["m_raw"] for l in T]) - lg([l["q"] for l in T])))
                w = len(T) / (len(T) + K_SHRINK)
                out[(st, sgm)] = w * g + (1 - w) * base
    return out


def debias(l: dict, bias: dict) -> float:
    b = bias.get(l["seg"], bias.get(l["stat"], 0.0))
    return float(sg(lg(l["m_raw"]) - b))


def fit_bias_outcome(train: list[dict]) -> dict:
    """The same table, fitted to what happened instead of to DraftKings: per stat x segment, the logit shift that
    makes the simulation's average over probability match the realized over rate (one Newton step from 0), shrunk
    toward the stat-wide value by n/(n+K)."""
    def shift(S):
        z = lg([l["m_raw"] for l in S]); y = np.array([l["yo"] for l in S]); b = 0.0
        for _ in range(20):
            p = sg(z - b); b -= np.sum(y - p) / max(np.sum(p * (1 - p)), 1e-9)
        return float(b)
    out = {}
    for st in STATS:
        S = [l for l in train if l["stat"] == st]
        if len(S) < 20:
            continue
        base = shift(S); out[st] = base
        for sgm in ("top5", "bench"):
            T = [l for l in S if l["seg"][1] == sgm]
            if len(T) >= 10:
                w = len(T) / (len(T) + K_SHRINK)
                out[(st, sgm)] = w * shift(T) + (1 - w) * base
    return out


# ------------------------------------------------------------------ blends
def hist_p(l, aware: bool):
    o, u = (l["hist_wo"], l["hist_wu"]) if aware else (l["hist_o"], l["hist_u"])
    n = o + u
    return (o / n, n) if n > 0 else (None, 0)


def blend(m, q, h, n, w_model, w_market, w_hist, intercept=0.0):
    comps = {"model": m, "market": q}
    if h is not None and w_hist > 0:
        w = n / (n + 10)
        comps["hist"] = w * h + (1 - w) * q
    W = {"model": w_model, "market": w_market, "hist": w_hist}
    tot = sum(W.values()); pres = sum(W[k] for k in comps)
    z = intercept + sum(W[k] * tot / pres * lg(v) for k, v in comps.items())
    return float(sg(z))


def logistic(X, y, l2=1.0, iters=50):
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = sg(X @ b); W = p * (1 - p)
        H = X.T @ (X * W[:, None]) + l2 * np.eye(X.shape[1]); H[0, 0] -= l2 - 1e-6
        b += np.linalg.solve(H, X.T @ (y - p) - l2 * np.r_[0, b[1:]])
    p = sg(X @ b)
    cov = np.linalg.inv(X.T @ (X * (p * (1 - p))[:, None]) + 1e-6 * np.eye(X.shape[1]))
    return b, cov


# ------------------------------------------------------------------ the walk-forward run
def run(tag: str) -> dict:
    L = load_legs(tag)
    days = sorted({l["day"] for l in L})
    rows = []
    fits = []
    for d in days:
        train = [l for l in L if l["day"] < d]
        test = [l for l in L if l["day"] == d]
        if len(train) < MIN_TRAIN or not test:
            continue
        bias = fit_bias(train)
        bias_o = fit_bias_outcome(train)
        night = {}                        # the old pipeline: flat per-stat bias measured on the same night's board
        for st in STATS:
            S = [l for l in test if l["stat"] == st]
            if len(S) >= 10:
                night[st] = float(np.mean(lg([l["m_raw"] for l in S]) - lg([l["q"] for l in S])))
        # walk-forward logistic: y ~ logit(market) + (logit(model) - logit(market)) [+ (logit(hist) - logit(market))]
        Xtr = np.array([[1.0, lg(l["q"]), lg(debias(l, bias)) - lg(l["q"])] for l in train]); ytr = np.array([l["yo"] for l in train])
        bfit, cov = logistic(Xtr, ytr)
        fits.append({"day": d, "n_train": len(train), "b": bfit.tolist(), "se": np.sqrt(np.diag(cov)).tolist()})
        for l in test:
            m = debias(l, bias)
            mo = debias(l, bias_o)
            m_old = float(sg(lg(l["m_raw"]) - night.get(l["stat"], 0.0)))
            h, n = hist_p(l, False); hw, nw = hist_p(l, True)
            r = {"day": d, "stat": l["stat"], "seg": l["seg"][1], "y": l["yo"], "q": l["q"], "m_raw": l["m_raw"], "m": m,
                 "old": blend(m_old, l["q"], h, n, OLD["w_model"], OLD["w_market"], OLD["w_hist"], OLD["intercept"]),
                 "market": l["q"], "model": m, "hist": h, "hist_n": n,
                 "lr": float(sg(np.array([1.0, lg(l["q"]), lg(m) - lg(l["q"])]) @ bfit)),
                 "lr_se_logit": float(np.sqrt(np.array([1.0, lg(l["q"]), lg(m) - lg(l["q"])]) @ cov @ np.array([1.0, lg(l["q"]), lg(m) - lg(l["q"])])))}
            r["model_o"] = mo
            r["model_raw"] = l["m_raw"]
            r["top5"] = l["top5"]
            r["hist_aware"], r["hist_aware_n"] = hw, nw
            for wm in (0.2, 0.3, 0.45):
                r[f"o{wm}"] = blend(mo, l["q"], None, 0, wm, 1 - wm, 0.0)
                r[f"o{wm}_h"] = blend(mo, l["q"], h, n, wm, 1 - wm - 0.05, 0.05)
                r[f"o{wm}_hw"] = blend(mo, l["q"], hw, nw, wm, 1 - wm - 0.05, 0.05)
                r[f"w{wm}"] = blend(m, l["q"], None, 0, wm, 1 - wm, 0.0)
                r[f"w{wm}_h"] = blend(m, l["q"], h, n, wm, 1 - wm - 0.05, 0.05)
                r[f"w{wm}_hw"] = blend(m, l["q"], hw, nw, wm, 1 - wm - 0.05, 0.05)
            rows.append(r)
    return {"rows": rows, "fits": fits, "days": days}


def score(rows: list[dict], key: str) -> dict:
    p = np.array([r[key] for r in rows]); y = np.array([r["y"] for r in rows])
    return {"n": len(rows), "logloss": ll(p, y), "brier": brier(p, y)}


def boot_diff(rows, a, b, B=2000, seed=3):
    """Paired bootstrap of log loss(a) - log loss(b), resampling days' legs."""
    rng = np.random.default_rng(seed)
    y = np.array([r["y"] for r in rows]); pa = np.clip([r[a] for r in rows], 1e-4, 1 - 1e-4); pb = np.clip([r[b] for r in rows], 1e-4, 1 - 1e-4)
    la = -(y * np.log(pa) + (1 - y) * np.log(1 - pa)); lb = -(y * np.log(pb) + (1 - y) * np.log(1 - pb))
    d = la - lb
    idx = rng.integers(0, len(d), (B, len(d)))
    m = d[idx].mean(1)
    return {"mean": float(d.mean()), "ci95": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]}


def selected(rows: list[dict], key: str) -> list[dict]:
    """Each leg at its higher side: p_sel = max(p, 1 - p), y_sel = the result for that side."""
    out = []
    for r in rows:
        p = r[key]
        side = "over" if p >= 0.5 else "under"
        out.append({**r, "side": side, "p_sel": max(p, 1 - p), "y_sel": r["y"] if side == "over" else 1 - r["y"]})
    return out


def platt_walk(sel: list[dict], min_train: int = 300) -> list[dict]:
    """Platt recalibration of the selected side, fitted on earlier days' selected legs only."""
    days = sorted({r["day"] for r in sel})
    out = []
    for d in days:
        tr = [r for r in sel if r["day"] < d]; te = [r for r in sel if r["day"] == d]
        if len(tr) < min_train:
            continue
        X = np.array([[1.0, lg(r["p_sel"])] for r in tr]); y = np.array([r["y_sel"] for r in tr])
        b, cov = logistic(X, y, l2=0.0)
        for r in te:
            x = np.array([1.0, lg(r["p_sel"])])
            out.append({**r, "p_cal": float(sg(x @ b)), "cal_se_logit": float(np.sqrt(x @ cov @ x)), "platt": b.tolist()})
    return out


def buckets(sel: list[dict], key: str, edges=((0.5, 0.55), (0.55, 0.6), (0.6, 0.65), (0.65, 0.7), (0.7, 1.01))) -> list[dict]:
    out = []
    for lo, hi in edges:
        S = [r for r in sel if lo <= r[key] < hi]
        if S:
            out.append({"bucket": f"{lo:.2f}-{min(hi, 1):.2f}", "n": len(S), "pred": float(np.mean([r[key] for r in S])),
                        "real": float(np.mean([r["y_sel"] for r in S]))})
    return out


def market_cal(rows: list[dict]) -> None:
    """Market-only, Platt-recalibrated on earlier days (a stronger baseline: DraftKings' overs run high)."""
    days = sorted({r["day"] for r in rows})
    for d in days:
        tr = [r for r in rows if r["day"] < d]; te = [r for r in rows if r["day"] == d]
        if len(tr) < MIN_TRAIN:
            for r in te:
                r["market_cal"] = r["market"]
            continue
        b, _ = logistic(np.array([[1.0, lg(r["market"])] for r in tr]), np.array([r["y"] for r in tr]), l2=0.0)
        for r in te:
            r["market_cal"] = float(sg(b[0] + b[1] * lg(r["market"])))


def label_table(sel: list[dict], pkey: str, gates: dict, high_thin: dict | None = None) -> dict:
    """Assign High / Medium / Low with the blend's gate logic on each selected leg (model, market, history at the
    selected side), then realized vs predicted per label."""
    out = {}
    for r in sel:
        flip = (lambda v: v) if r["side"] == "over" else (lambda v: None if v is None else 1 - v)
        comps = {"model": flip(r["model_o"]), "market": flip(r["market"])}
        if r.get("hist") is not None:
            w = r["hist_n"] / (r["hist_n"] + 10)
            comps["hist"] = w * flip(r["hist"]) + (1 - w) * comps["market"]
        vals = list(comps.values()); lean = [v for v in vals if abs(v - 0.5) >= 0.01]
        agree = bool(lean) and (all(v > 0.5 for v in lean) or all(v < 0.5 for v in lean))
        spread = max(vals) - min(vals); p = r[pkey]; n = r["hist_n"]
        high = p >= gates["high"] and agree and spread <= gates["max_spread_high"] and n >= gates["min_hist_n_high"]
        if not high and high_thin and p >= gates["high"] and agree and n < gates["min_hist_n_high"]:
            high = abs(comps["model"] - comps["market"]) <= high_thin["max_spread"]
        lab = "High" if high else "Medium" if (p >= gates["medium"] and agree) else "Low"
        o = out.setdefault(lab, {"n": 0, "pred": 0.0, "real": 0.0})
        o["n"] += 1; o["pred"] += p; o["real"] += r["y_sel"]
    for v in out.values():
        v["pred"] /= v["n"]; v["real"] /= v["n"]; v["gap"] = v["real"] - v["pred"]
    return out


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "base"
    res = run(tag)
    rows = res["rows"]
    market_cal(rows)
    keys = ["market", "market_cal", "model", "model_o", "old", "lr"] + [f"{b}{w}{h}" for b in ("w", "o") for w in (0.2, 0.3, 0.45) for h in ("", "_h", "_hw")]
    keys = [k for k in keys if k in rows[0]]
    sc = {k: score(rows, k) for k in keys}
    print(f"held-out legs {len(rows)} over {len({r['day'] for r in rows})} days (walk-forward, fit on earlier days only)")
    for k in keys:
        print(f"  {k:11s} log loss {sc[k]['logloss']:.4f}  Brier {sc[k]['brier']:.4f}")
    best = min((k for k in keys if k[0] in "wo" and k[1].isdigit()), key=lambda k: sc[k]["logloss"])
    print("best new blend:", best, "| vs market:", boot_diff(rows, best, "market"), "| vs market_cal:", boot_diff(rows, best, "market_cal"),
          "| vs old:", boot_diff(rows, best, "old"))
    json.dump({"scores": sc, "best": best, "fits": res["fits"]}, open(os.path.join(HERE, "data", "nba_bt", f"fit_{tag}.json"), "w"), indent=1)
