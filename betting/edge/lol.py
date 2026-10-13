"""LoL 'maps 1-3 kills' props from gol.gg (player games) and bo3.gg (series odds). No keys.

Each simulated game: the winner is drawn from the series market (per-game p inverted for Bo3/Bo5),
and the player's kills are bootstrapped from his recent games with the same result. In a Bo5,
games 1-3 are always played; in a Bo3, game 3 only when it is 1-1.
History is counted per SERIES in the current season (sum of the first three games of series that
reached game 3), never per game (LESSONS L23).
"""
from __future__ import annotations

import collections
import html
import re

import numpy as np

from .grade import _get

GOL = "https://gol.gg/players/player-matchlist/{pid}/season-{season}/split-ALL/tournament-ALL/"
BO3 = "https://api.bo3.gg/api/v1"


_PAGES: dict = {}


def _page(url: str, tries: int = 4) -> str:
    """gol.gg drops connections under load: retry with backoff, and fetch each page once per run."""
    import time
    import urllib.request
    from .grade import _CTX
    if url in _PAGES:
        return _PAGES[url]
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=_CTX, timeout=40) as r:
                _PAGES[url] = r.read().decode("utf-8", "ignore")
                return _PAGES[url]
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))


def player_games(gol_id: str, seasons=("S16",)) -> list[dict]:
    """This season's games on the player's gol.gg match list: win, kills, date, series title, game id.
    One definition everywhere: history and the model both use the current season only."""
    out = []
    for s in seasons:
        h = _page(GOL.format(pid=gol_id, season=s))
        for row in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            m = re.search(r"game/stats/(\d+)/", row)
            kda = next((c for c in cells if re.fullmatch(r"\d+/\d+/\d+", c)), None)
            if not (m and kda and len(cells) >= 10):
                continue
            out.append({"win": cells[1] == "Victory", "k": int(kda.split("/")[0]), "date": cells[8], "title": cells[9], "game": int(m.group(1))})
    seen, uniq = set(), []
    for g in sorted(out, key=lambda g: (g["date"], g["game"]), reverse=True):
        if g["game"] not in seen:
            seen.add(g["game"])
            uniq.append(g)
    return uniq


def series_totals(games: list[dict], n_games: int = 3) -> list[int]:
    """Sum of kills over the first n games of each series that reached game n."""
    by = collections.defaultdict(list)
    for g in games:
        by[(g["date"], g["title"])].append(g)
    return [sum(x["k"] for x in sorted(v, key=lambda g: g["game"])[:n_games]) for v in by.values() if len(v) >= n_games]


def history(games: list[dict], line: float) -> tuple[int, int, int]:
    s = series_totals(games)
    return sum(x > line for x in s), sum(x < line for x in s), len(s)


def per_game_p(p_series: float, bo: int) -> float:
    f = (lambda p: p ** 3 * (1 + 3 * (1 - p) + 6 * (1 - p) ** 2)) if bo == 5 else (lambda p: p * p * (3 - 2 * p))
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < p_series else (lo, mid)
    return (lo + hi) / 2


def find_match(match_id: int) -> dict | None:
    for st in ("upcoming", "current"):
        d = _get(f"{BO3}/matches?page%5Blimit%5D=100&sort=start_date&filter%5Bmatches.status%5D%5Bin%5D={st}"
                 f"&filter%5Bmatches.discipline_id%5D%5Beq%5D=3&with=teams")
        for m in d.get("results", []):
            if m.get("id") == int(match_id):
                return m
    return None


def team_series_p(match: dict, games: list[dict]) -> tuple[float, str]:
    """Series win probability for the player's team: the bo3 team whose name appears in his recent series titles."""
    bu = match.get("bet_updates") or {}
    t1, t2 = bu.get("team_1") or {}, bu.get("team_2") or {}
    i1, i2 = 1 / t1["coeff"], 1 / t2["coeff"]
    p1 = i1 / (i1 + i2)
    titles = " ".join(g["title"].lower() for g in games[:15])
    words = lambda n: [w for w in re.findall(r"[a-z0-9]+", (n or "").lower()) if len(w) > 2]
    s1 = sum(titles.count(w) for w in words(t1.get("name")))
    s2 = sum(titles.count(w) for w in words(t2.get("name")))
    return (p1, t1.get("name")) if s1 >= s2 else (1 - p1, t2.get("name"))


def price(games: list[dict], p_game: float, bo: int, line: float, n: int = 200_000, seed: int = 11) -> dict:
    rng = np.random.default_rng(seed)
    recent = games[:40]
    kw = np.array([g["k"] for g in recent if g["win"]] or [0])
    kl = np.array([g["k"] for g in recent if not g["win"]] or [0])
    win = rng.random((n, 3)) < p_game
    k = np.where(win, rng.choice(kw, (n, 3)), rng.choice(kl, (n, 3)))
    tot = k.sum(1) if bo == 5 else k[:, 0] + k[:, 1] + np.where(win[:, 0] != win[:, 1], k[:, 2], 0)
    return {"p_over": float((tot > line).mean()), "p_under": float((tot < line).mean()), "p_push": float((tot == line).mean()),
            "median": float(np.median(tot)), "kpg_w": float(kw.mean()), "kpg_l": float(kl.mean())}
