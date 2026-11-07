"""Do the tennis reasons carry information beyond the simulation?

Walk-forward set: matches from 2026-09-01 between cached players, predicted from earlier rows only (form measured
on earlier matches). For each match a PrizePicks-like line is set at the simulation's median (x.5), and each reason
is computed from earlier matches only. Logistic regression: result ~ a + b * logit(p_simulation) + c * reason.
c = 0 means the reason adds nothing. Out of sample: fit on the earlier half by date, score on the later half, and
the reverse; Δ log loss < 0 means the reason helped."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from edge import tennis as T

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "tennis_bt")
players = T.cached_players()
print("players", len(players), flush=True)
bt = T.backtest(players, since="2026-09-01", form_mode="measured")
R = bt["records"]
print("matches", len(R), flush=True)

def logit(p): p = np.clip(p, 1e-4, 1 - 1e-4); return np.log(p / (1 - p))

def fit(X, y, iters=50):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        z = X @ w; p = 1 / (1 + np.exp(-z))
        g = X.T @ (y - p); H = (X * (p * (1 - p))[:, None]).T @ X + 1e-6 * np.eye(X.shape[1])
        w += np.linalg.solve(H, g)
    cov = np.linalg.inv(H)
    return w, np.sqrt(np.diag(cov))

def ll(X, y, w):
    p = np.clip(1 / (1 + np.exp(-(X @ w))), 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

rows = {"games": [], "gw": [], "win": []}
for r in R:
    pmf = np.array(r["pmf_games"], float); pmf /= pmf.sum()
    med = int(np.searchsorted(np.cumsum(pmf), 0.5)); L = med + 0.5 if pmf[: med + 1].sum() < 0.5 else med - 0.5
    p_sim = float(pmf[int(L + 0.5):].sum())
    ha, hb = r["hist_a"], r["hist_b"]
    share = lambda h, k, L: (np.mean([x[k] > L for x in h]) if h else np.nan)
    feat = {
        "season/recent record (both players' earlier matches over the line)": np.nanmean([share(ha, 0, L), share(hb, 0, L)]),
        "last 5 (both players)": np.nanmean([share(ha[-5:], 0, L), share(hb[-5:], 0, L)]),
        "head-to-head record": share([x for x in ha if x[3] == r["opp_a"]], 0, L),
        "average total games, earlier matches": np.nanmean([np.mean([x[0] for x in ha]) if ha else np.nan, np.mean([x[0] for x in hb]) if hb else np.nan]) - L,
    }
    rows["games"].append((r["date"], r["games"] > L, p_sim, feat))
    pg = np.array(r["pmf_gw"], float); pg /= pg.sum()
    m2 = int(np.searchsorted(np.cumsum(pg), 0.5)); L2 = m2 + 0.5 if pg[: m2 + 1].sum() < 0.5 else m2 - 0.5
    rows["gw"].append((r["date"], r["gw_a"] > L2, float(pg[int(L2 + 0.5):].sum()), {
        "season/recent record (player's earlier matches over the line)": share(ha, 1, L2),
        "last 5": share(ha[-5:], 1, L2),
        "head-to-head record": share([x for x in ha if x[3] == r["opp_a"]], 1, L2)}))
    wl = lambda h: np.mean([x[2] for x in h]) if h else np.nan
    rows["win"].append((r["date"], bool(r["won_a"]), r["p_win"], {
        "win rate, earlier matches (A minus B)": wl(ha) - wl(hb),
        "last 5 wins (A minus B)": wl(ha[-5:]) - wl(hb[-5:]),
        "head-to-head wins": wl([x for x in ha if x[3] == r["opp_a"]]) - 0.5}))

out = {}
for target, data in rows.items():
    data.sort(key=lambda t: t[0])
    names = list(data[0][3].keys())
    for nm in names:
        D = [(d, y, p, f[nm]) for d, y, p, f in data if np.isfinite(f[nm])]
        if len(D) < 60:
            print(f"{target:5s} | {nm}: only {len(D)} matches with it"); continue
        y = np.array([t[1] for t in D], float); lp = logit(np.array([t[2] for t in D])); x = np.array([t[3] for t in D], float)
        xs = (x - x.mean()) / (x.std() or 1)
        X0 = np.c_[np.ones(len(y)), lp]; X1 = np.c_[X0, xs]
        w1, se = fit(X1, y)
        h = len(y) // 2; dl = []
        for tr, te in ((slice(0, h), slice(h, None)), (slice(h, None), slice(0, h))):
            a0, _ = fit(X0[tr], y[tr]); a1, _ = fit(X1[tr], y[tr])
            dl.append(ll(X1[te], y[te], a1) - ll(X0[te], y[te], a0))
        out[f"{target}: {nm}"] = {"n": len(y), "coef": float(w1[2]), "se": float(se[2]), "dlogloss_out": [float(v) for v in dl]}
        print(f"{target:5s} | {nm:70s} n={len(y):4d}  weight {w1[2]:+.3f} ± {se[2]:.3f}  out-of-sample Δlog loss {dl[0]:+.4f} / {dl[1]:+.4f}", flush=True)
json.dump(out, open(f"{OUT}/tennis_reason_test.json", "w"), indent=1)
