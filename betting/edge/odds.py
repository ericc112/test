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


def devig(over: float, under: float, method: str = "multiplicative") -> tuple[float, float]:
    """No-vig probabilities for a two-way market priced in American odds."""
    po, pu = implied(over), implied(under)
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
