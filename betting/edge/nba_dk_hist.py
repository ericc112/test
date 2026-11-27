"""DraftKings NBA player-prop history from ESPN's propBets feed (works for finished games): every item for the
eight stats the simulation scores, their "N+" milestone ladders, open and current targets and prices, and when each
was last updated. Saved to data/nba_dk_hist/SEASON.json.gz, keyed by ESPN event id.
  python -m edge.nba_dk_hist 20261018 20261103"""
from __future__ import annotations

import concurrent.futures as cf
import gzip
import json
import os
import sys
import urllib.request

from .blend import HERE

TOTALS = {"Total Points": "pts", "Total Assists": "ast", "Total Rebounds": "reb", "Total 3-Point Field Goals": "tpm",
          "Total Points, Rebounds, and Assists": "pra", "Total Points and Rebounds": "pr", "Total Points and Assists": "pa",
          "Total Assists and Rebounds": "ra"}
MILESTONES = {"Points Milestones": "pts", "Assists Milestones": "ast", "Rebounds Milestones": "reb", "3-Point Field Goals Milestones": "tpm",
              "Points + Assists + Rebounds Milestones": "pra", "Points + Rebounds Milestones": "pr", "Points + Assists Milestones": "pa",
              "Rebounds + Assists Milestones": "ra"}
PATH = os.path.join(HERE, "data", "nba_dk_hist")


def fetch(gid: str) -> list[dict]:
    items, page = [], 1
    while True:
        u = f"https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events/{gid}/competitions/{gid}/odds/100/propBets?limit=1000&page={page}"
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40))
        except Exception:
            return items
        for i in d.get("items", []):
            nm = i["type"]["name"]
            if not i.get("athlete") or (nm not in TOTALS and nm not in MILESTONES):
                continue
            pid = i["athlete"]["$ref"].split("/athletes/")[1].split("?")[0]
            g = lambda k: (i.get(k) or {})
            items.append({"pid": pid, "kind": "total" if nm in TOTALS else "ms", "stat": TOTALS.get(nm) or MILESTONES[nm],
                          "cur": (g("current").get("target") or {}).get("value"), "open": (g("open").get("target") or {}).get("value"),
                          "price": (g("odds").get("american") or {}).get("value"), "price_open": (g("odds").get("american") or {}).get("open"),
                          "updated": i.get("lastUpdated")})
        if page >= d.get("pageCount", 1):
            return items
        page += 1


def main(start: str, end: str):
    sys.path.insert(0, HERE)
    from gamesim import nba
    G = [g for g in nba.season_games("nba", start, end) if g["final"]]
    season = start[:4]
    os.makedirs(PATH, exist_ok=True)
    path = os.path.join(PATH, f"{season}.json.gz")
    have = json.load(gzip.open(path, "rt")) if os.path.exists(path) else {}
    todo = [g for g in G if g["id"] not in have]
    with cf.ThreadPoolExecutor(6) as ex:
        for g, items in zip(todo, ex.map(lambda g: fetch(g["id"]), todo)):
            have[g["id"]] = {"date": g["date"], "home": g["home"], "away": g["away"], "items": items}
    json.dump(have, gzip.open(path, "wt"))
    print(f"{len(have)} games, {sum(len(v['items']) for v in have.values())} items -> {path}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
