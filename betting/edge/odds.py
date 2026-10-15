"""Odds conversion, de-vig, EV and Kelly sizing."""
from __future__ import annotations

import math


def american_to_decimal(american: float) -> float:
    a = float(american)
    return 1 + a / 100 if a > 0 else 1 + 100 / -a


def implied(american: float) -> float:
    """Implied probability including vig."""
    a = float(american)
    return 100 / (a + 100) if a > 0 else -a / (-a + 100)


DEVIG_METHODS = ("multiplicative", "additive", "power", "shin")


def devig(over: float, under: float, method: str = "multiplicative") -> tuple[float, float]:
    """No-vig probabilities for a two-way market priced in American odds.

    multiplicative: scale both sides by the overround. additive: take half the overround off each side.
    power: po**k + pu**k = 1 (shades longshots more). shin: Shin's insider-trading model, which also loads the margin
    on the longshot. worst: the lowest fair probability any method gives each side (the conservative read).
    """
    po, pu = implied(over), implied(under)
    if method == "worst":
        fair = [devig(over, under, m) for m in DEVIG_METHODS]
        return min(f[0] for f in fair), min(f[1] for f in fair)
    if method == "additive":
        cut = (po + pu - 1) / 2
        a, b = min(max(po - cut, 1e-6), 1 - 1e-6), min(max(pu - cut, 1e-6), 1 - 1e-6)
        return a / (a + b), b / (a + b)
    if method == "shin":
        s = po + pu

        def fair(z):
            return [(math.sqrt(z * z + 4 * (1 - z) * q * q / s) - z) / (2 * (1 - z)) for q in (po, pu)]
        lo, hi = 0.0, 0.5
        for _ in range(60):
            z = (lo + hi) / 2
            lo, hi = (z, hi) if sum(fair(z)) > 1 else (lo, z)
        a, b = fair((lo + hi) / 2)
        return a / (a + b), b / (a + b)
    if method == "multiplicative":
        s = po + pu
        return po / s, pu / s
    if method == "power":  # find k with po**k + pu**k = 1 (shades longshots more)
        lo, hi = 0.5, 2.5
        for _ in range(60):
            k = (lo + hi) / 2
            lo, hi = (k, hi) if po ** k + pu ** k > 1 else (lo, k)
        return po ** k, pu ** k
    raise ValueError(method)


def fair_american(p: float) -> int:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return round(-100 * p / (1 - p)) if p >= 0.5 else round(100 * (1 - p) / p)


def ev_per_dollar(p: float, american: float) -> float:
    return p * american_to_decimal(american) - 1


def kelly_fraction(p: float, american: float) -> float:
    b = american_to_decimal(american) - 1
    return max((b * p - (1 - p)) / b, 0.0)


def stake(p: float, american: float, bankroll: float, frac: float = 0.25, cap: float = 0.02) -> float:
    """Quarter-Kelly stake capped at `cap` of bankroll."""
    return round(bankroll * min(frac * kelly_fraction(p, american), cap), 2)


def logit(p: float) -> float:
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def sigmoid(z: float) -> float:
    return 1 / (1 + math.exp(-z))
