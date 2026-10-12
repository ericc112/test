"""Fixed-payout entries: break-evens, correlated entry odds, best-entry search, Squad Ride milestones."""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np

# Multipliers by number of correct legs. Verify in-app: payouts vary by state and by line (goblins/demons).
PAYOUTS = {
    "pp_power_2": {2: 3.0},
    "pp_power_3": {3: 5.0},
    "pp_power_4": {4: 10.0},
    "pp_power_5": {5: 20.0},
    "pp_power_6": {6: 37.5},
    "pp_flex_3": {3: 2.25, 2: 1.25},
    "pp_flex_4": {4: 5.0, 3: 1.5},
    "pp_flex_5": {5: 10.0, 4: 2.0, 3: 0.4},
    "pp_flex_6": {6: 25.0, 5: 2.0, 4: 0.4},
    "boom_pickem_2": {2: 3.2},
}


def entry_ev_independent(p: float, n: int, payout: dict[int, float]) -> float:
    """EV per $1 when every leg has the same independent probability p."""
    return sum(m * math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k, m in payout.items()) - 1


def breakeven(payout: dict[int, float], n: int | None = None) -> float:
    """Per-leg win rate at which the entry breaks even (independent, equal legs)."""
    n = n or max(payout)
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if entry_ev_independent(mid, n, payout) < 0 else (lo, mid)
    return round((lo + hi) / 2, 4)


def _norm_ppf(p: np.ndarray) -> np.ndarray:
    # Acklam's rational approximation (no scipy dependency).
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02, 1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02, 6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00, -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00]
    p = np.clip(np.asarray(p, float), 1e-12, 1 - 1e-12)
    out = np.empty_like(p)
    lo, hi = p < 0.02425, p > 1 - 0.02425
    mid = ~(lo | hi)
    q = np.sqrt(-2 * np.log(p[lo]))
    out[lo] = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p[mid] - 0.5
    r = q * q
    out[mid] = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = np.sqrt(-2 * np.log(1 - p[hi]))
    out[hi] = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    return out


def simulate_hits(probs: list[float], corr: np.ndarray | None = None, n_sims: int = 200_000, seed: int = 7) -> np.ndarray:
    """Simulate leg outcomes (n_sims x legs, bool) with a Gaussian copula.

    corr[i, j] > 0 means legs i and j tend to win together (e.g. two unders that both need a short game).
    """
    k = len(probs)
    corr = np.eye(k) if corr is None else np.asarray(corr, float)
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n_sims, k)) @ np.linalg.cholesky(corr + 1e-9 * np.eye(k)).T
    thresholds = _norm_ppf(np.asarray(probs, float))
    return z < thresholds


def entry_summary(probs: list[float], payout: dict[int, float], corr: np.ndarray | None = None) -> dict:
    hits = simulate_hits(probs, corr).sum(axis=1)
    n = len(probs)
    dist = {k: float((hits == k).mean()) for k in range(n + 1)}
    ev = sum(payout.get(k, 0.0) * pk for k, pk in dist.items()) - 1
    return {"p_all": dist[n], "dist": dist, "ev": ev}


@dataclass
class Leg:
    label: str
    p: float
    team: str = ""
    game: str = ""
    group: str = ""          # legs sharing a group are positively correlated (same-direction game script)
    group_sign: int = 1      # -1 if this leg wins in the opposite script from the rest of its group
    meta: dict = field(default_factory=dict)


def corr_matrix(legs: list[Leg], rho_group: float = 0.25, rho_game: float = 0.05) -> np.ndarray:
    k = len(legs)
    c = np.eye(k)
    for i, j in itertools.combinations(range(k), 2):
        rho = 0.0
        if legs[i].group and legs[i].group == legs[j].group:
            rho = rho_group * legs[i].group_sign * legs[j].group_sign
        elif legs[i].game and legs[i].game == legs[j].game:
            rho = rho_game
        c[i, j] = c[j, i] = rho
    return c


def best_entries(legs: list[Leg], size: int, payout: dict[int, float], min_teams: int = 1,
                 objective: str = "p_all", top: int = 5, max_candidates: int = 16) -> list[dict]:
    """Search leg combinations; objective 'p_all' (hit rate) or 'ev'. Only legs above 0.5 are considered."""
    pool = sorted([l for l in legs if l.p > 0.5], key=lambda l: -l.p)[:max_candidates]
    out = []
    for combo in itertools.combinations(pool, size):
        if len({l.team for l in combo if l.team}) < min_teams:
            continue
        s = entry_summary([l.p for l in combo], payout, corr_matrix(list(combo)))
        out.append({"legs": [l.label for l in combo], **s})
    return sorted(out, key=lambda r: -r[objective])[:top]


def squad_ride(means: list[float], sds: list[float], milestones: tuple[float, float, float],
               corr: np.ndarray | None = None, payouts: tuple[float, float, float] = (2, 5, 20),
               n_sims: int = 600_000, seed: int = 9) -> dict:
    """Probability of each Squad Ride milestone (ties count) with right-skewed (lognormal) player totals."""
    k = len(means)
    corr = np.eye(k) if corr is None else np.asarray(corr, float)
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n_sims, k)) @ np.linalg.cholesky(corr + 1e-9 * np.eye(k)).T
    m, s = np.asarray(means, float), np.asarray(sds, float)
    sig = np.sqrt(np.log1p((s / m) ** 2))
    total = np.exp(np.log(m) - sig ** 2 / 2 + sig * z).sum(axis=1)
    p = [float((total >= t).mean()) for t in milestones]
    ev = payouts[0] * (p[0] - p[1]) + payouts[1] * (p[1] - p[2]) + payouts[2] * p[2] - 1
    return {"p_m1": p[0], "p_m2": p[1], "p_m3": p[2], "p_nothing": 1 - p[0], "ev": ev,
            "median_total": float(np.median(total)), "mean_total": float(total.mean())}
