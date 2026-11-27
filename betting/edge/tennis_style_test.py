"""Does how they play add anything the ratings don't already know? Walk-forward test of style matchups.

For every match with serve counts, the share of serve points the server won is compared with the opponent-adjusted
ratings' prediction (tennis_hist.Ratings, the settings the pricer uses), fitted only on matches before a cut date.
Style profiles (edge/tennis_scout.py, from the 52 weeks before the cut) give interaction terms: does a big server do
worse than the ratings say against a strong first-serve returner, a weak second serve worse against a second-serve
attacker, and so on. The terms are fitted on one window (ratings cut 2026-01-01, matches Jan-Aug 2026) and scored on
the next (cut 2026-09-01, matches from September): weighted squared error of the serve-point share and the
point-level log likelihood, with a bootstrap over matches.
  python -m edge.tennis_style_test            -> data/tennis_bt/style_test.json"""
from __future__ import annotations

import datetime as dt
import json
import os

import numpy as np

from .blend import HERE

TERMS = {
    # name: (server feature, returner feature): interaction of the two, each centred on the field's mean
    "ace_x_return1": ("ace_pct", "r1_won"),         # big server vs strong first-serve returner
    "second_x_return2": ("second_won", "r2_won"),   # second serve vs second-serve attacker
    "firstin_x_return2": ("first_in", "r2_won"),    # misses first serves vs punishes second serves
    "df_x_return2": ("df_pct", "r2_won"),           # double-fault prone vs pressure on second serve
}
CHARTED = {
    "shortwin_x_shortwin": ("won_le3", "ret_inplay"),   # first-strike server vs returner who makes them play
    "long_x_long": ("long_won", "long_won"),           # who wins the long rallies, server vs returner
}


def _profiles(st: dict, tour: str, cut: dt.date) -> dict:
    from . import tennis_scout as TS
    db = TS.from_matches(st["matches"], tour, cut)
    ch = TS.charted(tour, (cut - dt.timedelta(days=730)).strftime("%Y%m%d"))
    out = {}
    for pid, d in db.items():
        f = TS.features(d, ch.get(TS._norm(d.get("name") or "")))
        if f:
            out[pid] = f
    return out


def _rows(st: dict, tour: str, cut: dt.date, end: dt.date, study: dict) -> tuple:
    from . import tennis_hist as TH
    T_ = st[tour]; obs = T_["obs"]
    ch = (study.get(tour) or {}).get("chosen") or {"H": 730, "lam": 400}
    R = TH.Ratings(H=ch["H"], lam=ch["lam"]).fit(obs, cut.toordinal())
    prof = _profiles(st, tour, cut)
    lo, hi = int(cut.strftime("%Y%m%d")), int(end.strftime("%Y%m%d"))
    X, y, w, ids, base = [], [], [], [], []
    keys = list(TERMS) + list(CHARTED)
    mean = {}
    for k, (fs, fr) in {**TERMS, **CHARTED}.items():
        for f in (fs, fr):
            vals = [p[f] for p in prof.values() if p.get(f) is not None]
            mean[f] = float(np.mean(vals)) if vals else 0.0
    for m in st["matches"]:
        if m["tour"] != tour or not (lo <= m["date"] < hi) or not m.get("w_n") or not m.get("l_n"):
            continue
        for srv, ret, n, k in ((m["w"], m["l"], m["w_n"], m["w_k"]), (m["l"], m["w"], m["l_n"], m["l_k"])):
            i, j = obs["idx"].get(srv), obs["idx"].get(ret)
            if i is None or j is None or i >= R.P or j >= R.P or R.pts_s[i] < 300 or R.pts_r[j] < 300:
                continue
            ps, pr = prof.get(srv), prof.get(ret)
            if not ps or not pr:
                continue
            p = R.p(i, j, m["surface"] if m["surface"] in ("Hard", "Clay", "Grass") else "Hard", None)
            row = []
            for kk in keys:
                fs, fr = {**TERMS, **CHARTED}[kk]
                a, b = ps.get(fs), pr.get(fr)
                row.append((a - mean[fs]) * (b - mean[fr]) if a is not None and b is not None else np.nan)
            X.append(row); y.append(k / n); w.append(n); base.append(p); ids.append(m["ev"] + m["w"] + m["l"])
    return np.array(X, float), np.array(y), np.array(w, float), np.array(base), np.array(ids), keys


def _fit(X, r, w, lam=1.0):
    """Weighted ridge on standardized columns (NaN -> 0 after centring). Returns coefficients and the scaler."""
    Z = np.nan_to_num(X)
    sd = np.sqrt(np.average(Z ** 2, axis=0, weights=w)) + 1e-12
    Zs = Z / sd
    A = (Zs * w[:, None]).T @ Zs + lam * w.sum() * 1e-4 * np.eye(Z.shape[1])
    beta = np.linalg.solve(A, (Zs * w[:, None]).T @ r)
    return beta, sd


def _ll(p, y, n):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return n * (y * np.log(p) + (1 - y) * np.log(1 - p))


def run(out: str | None = None) -> dict:
    from . import tennis as T
    st = T.tml_state()
    study = json.load(open(T.STUDY)) if os.path.exists(T.STUDY) else {}
    res = {}
    rng = np.random.default_rng(7)
    for tour in ("ATP", "WTA"):
        Xa, ya, wa, ba, _, keys = _rows(st, tour, dt.date(2026, 1, 1), dt.date(2026, 9, 1), study)
        Xb, yb, wb, bb, idb, _ = _rows(st, tour, dt.date(2026, 9, 1), dt.date(2026, 12, 31), study)
        out_t = {"tune_rows": int(len(ya)), "test_rows": int(len(yb)), "terms": {}}
        for subset, cols in (("match stats (everyone)", [keys.index(k) for k in TERMS]),
                             ("plus charted (top players)", list(range(len(keys))))):
            beta, sd = _fit(Xa[:, cols], ya - ba, wa)
            pred = bb + (np.nan_to_num(Xb[:, cols]) / sd) @ beta
            d_ll = _ll(pred, yb, wb) - _ll(bb, yb, wb)            # per row, positive = style helps
            d_se = wb * ((yb - bb) ** 2 - (yb - pred) ** 2)
            # bootstrap over matches
            u, inv = np.unique(idb, return_inverse=True)
            tot_ll = np.bincount(inv, d_ll, len(u)); tot_w = np.bincount(inv, wb, len(u))
            bs = [tot_ll[s].sum() / tot_w[s].sum() for s in (rng.integers(0, len(u), len(u)) for _ in range(1000))]
            covered = int((~np.isnan(Xb[:, cols])).all(axis=1).sum())
            out_t["terms"][subset] = {
                "coef_per_sd": {keys[c]: round(float(b), 5) for c, b in zip(cols, beta)},
                "test_ll_per_point": round(float(d_ll.sum() / wb.sum()), 6), "ci95": [round(float(np.percentile(bs, 2.5)), 6), round(float(np.percentile(bs, 97.5)), 6)],
                "test_se_gain": round(float(d_se.sum() / wb.sum()), 7), "rows_fully_covered": covered}
        res[tour] = out_t
    res["_note"] = ("Positive test_ll_per_point = style terms improved the point-level fit beyond the ratings on matches the terms weren't fitted on. "
                    "A term is worth adopting only if the 95% interval excludes zero.")
    path = out or os.path.join(HERE, "data", "tennis_bt", "style_test.json")
    json.dump(res, open(path, "w"), indent=1)
    return res


if __name__ == "__main__":
    print(json.dumps(run(), indent=1))
