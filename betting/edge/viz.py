"""Compact shapes for the Sim Lab's visual pick cards: a simulated distribution trimmed to its 1st-99th percentile
(at most 40 bins) and a game log as rows of [date, opponent, home, extra, value]."""
from __future__ import annotations

import numpy as np


def dist_from_counts(h) -> dict | None:
    """Counts by whole value (index = value) -> {lo, w, p}: probability per bin from lo in steps of w."""
    a = np.asarray(h, float)
    if a.size == 0 or a.sum() <= 0:
        return None
    c = np.cumsum(a) / a.sum()
    lo, hi = int(np.searchsorted(c, 0.01)), int(np.searchsorted(c, 0.99))
    w = max(1, int(np.ceil((hi - lo + 1) / 40)))
    p = [float(a[i:i + w].sum() / a.sum()) for i in range(lo, hi + 1, w)]
    return {"lo": lo, "w": w, "p": [round(x, 4) for x in p]}


def dist_from_samples(arr) -> dict | None:
    """Simulated values -> {lo, w, p}; whole-number stats keep unit bins until the range needs more than 40."""
    x = np.asarray(arr, float)
    if x.size == 0:
        return None
    lo, hi = np.percentile(x, 1), np.percentile(x, 99)
    if np.allclose(x, np.round(x)):
        lo, hi = int(np.floor(lo)), int(np.ceil(hi))
        w = max(1, int(np.ceil((hi - lo + 1) / 40)))
    else:
        w = max((hi - lo) / 40, 1e-9)
    n = int(np.floor((hi - lo) / w)) + 1
    idx = np.clip(np.floor((x - lo) / w).astype(int), 0, n - 1)
    keep = (x >= lo) & (x < lo + n * w + 1e-9)
    p = np.bincount(idx[keep], minlength=n)[:n] / x.size
    return {"lo": round(float(lo), 3), "w": round(float(w), 3), "p": [round(float(v), 4) for v in p]}
