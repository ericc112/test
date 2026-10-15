"""Defense vs Position: how tonight's opponent treats this player's position for this stat, ranked against the league.

Each card describes the opponent's unit as it is (rank 1 = the strongest defense, or the strongest lineup/offense on
pitcher and goalie props) and says which side a strong opponent helps: a strong defense helps a Less; a strong lineup
helps the More on a pitcher's hits, runs or walks allowed.
  NFL  box scores this season, by the position that produced the stat (QB, RB, WR, TE, K; positions from rosters)
  NBA  box scores by position (G, F, C): this season's regular season, or the last six weeks of last season until
       teams have played 10 games
  NHL  team rates: shots and goals allowed, shots taken (goalie saves)
  MLB  team rates: a batter faces the opponent's pitching, a pitcher faces the opponent's lineup
Box scores are cached in data/dvp/<league>.json and only new games are fetched.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import functools
import json
import os

from .grade import _get

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(HERE, "data", "dvp")
ESPN = "https://site.api.espn.com/apis/site/v2/sports"
TIERS = ((0.2, "Strong"), (0.4, "Above Average"), (0.6, "Average"), (0.8, "Below Average"), (1.01, "Weak"))

# market key -> (position-group stat terms summed, plain words)
NFL_STATS = {"pass_yds": (("pass_yds",), "passing yards"), "pass_tds": (("pass_td",), "passing TDs"),
             "pass_att": (("pass_att",), "pass attempts"), "pass_cmp": (("pass_cmp",), "completions"),
             "pass_int": (("pass_int",), "interceptions"), "rush_yds": (("rush_yds",), "rushing yards"),
             "rush_att": (("rush_att",), "carries"), "rec_yds": (("rec_yds",), "receiving yards"),
             "receptions": (("rec",), "receptions"), "rush_rec_yds": (("rush_yds", "rec_yds"), "rush + rec yards"),
             "pass_rush_yds": (("pass_yds", "rush_yds"), "pass + rush yards"), "anytime_td": (("rush_td", "rec_td"), "touchdowns"),
             "longest_rec": (("long_rec",), "longest catch"), "fg_made": (("fg",), "field goals"), "kicking_pts": (("k_pts",), "kicking points")}
NBA_STATS = {"points": ("PTS",), "rebounds": ("REB",), "assists": ("AST",), "threes": ("3PM",), "steals": ("STL",), "blocks": ("BLK",),
             "turnovers": ("TO",), "pra": ("PTS", "REB", "AST"), "pts_rebs": ("PTS", "REB"), "pts_asts": ("PTS", "AST"),
             "rebs_asts": ("REB", "AST"), "blks_stls": ("BLK", "STL")}
NBA_WORDS = {"PTS": "points", "REB": "rebounds", "AST": "assists", "3PM": "threes", "STL": "steals", "BLK": "blocks", "TO": "turnovers"}
GROUP_WORD = {"QB": "QBs", "RB": "RBs", "WR": "WRs", "TE": "TEs", "K": "kickers", "G": "guards", "F": "forwards", "C": "centers"}


def tier(strength_rank: int, of: int) -> str:
    x = (strength_rank - 1) / max(1, of - 1)
    return next(w for cut, w in TIERS if x < cut)


def _rank(table: dict[str, float], team: str, high_is_strong: bool) -> tuple[int, int] | None:
    """Strength rank (1 = strongest) of `team` among the teams in `table`."""
    if team not in table:
        return None
    order = sorted(table, key=lambda k: table[k], reverse=high_is_strong)
    return order.index(team) + 1, len(order)


def _card(title: str, sub: str, group: str, team: str, table: dict[str, float], high_is_strong: bool, strong_helps: str,
          unit: str, digits: int = 1) -> dict | None:
    r = _rank(table, team, high_is_strong)
    if not r:
        return None
    lg = sum(table.values()) / len(table)
    return {"title": title, "sub": sub, "group": group, "team": team, "rank": r[0], "of": r[1], "tier": tier(*r),
            "strong_helps": strong_helps,
            "value": f"{table[team]:.{digits}f}{(unit if unit.startswith('%') else ' ' + unit) if unit else ''} (league {lg:.{digits}f})"}


# ------------------------------------------------------------------ box-score cache (NFL, NBA)
def _load(league: str) -> dict:
    p = os.path.join(CACHE, f"{league.lower()}.json")
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"games": {}}


def _save(league: str, d: dict):
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, f"{league.lower()}.json"), "w") as f:
        json.dump(d, f, separators=(",", ":"))


@functools.lru_cache(maxsize=None)
def nfl_positions(team: str) -> dict[str, str]:
    r = _get(f"{ESPN}/football/nfl/teams/{team.lower()}/roster")
    out = {}
    for g in r.get("athletes", []):
        for a in g.get("items", []):
            pos = (a.get("position") or {}).get("abbreviation", "")
            out[str(a["id"])] = {"FB": "RB", "HB": "RB", "PK": "K"}.get(pos, pos)
    return out


def _num(v) -> float:
    try:
        return float(str(v).replace(",", "").split("/")[0].split("-")[0] or 0)
    except ValueError:
        return 0.0


def _nfl_game(eid: str) -> dict | None:
    """{defense: {group: {stat: total}}} for one final NFL game."""
    s = _get(f"{ESPN}/football/nfl/summary?event={eid}")
    teams = s.get("boxscore", {}).get("players", [])
    if len(teams) != 2:
        return None
    out = {}
    for i, t in enumerate(teams):
        off, dfn = t["team"]["abbreviation"], teams[1 - i]["team"]["abbreviation"]
        pos = nfl_positions(off)
        acc = out.setdefault(dfn, {})
        for cat in t.get("statistics", []):
            labels = cat.get("labels") or []
            for a in cat.get("athletes", []):
                g = pos.get(str(a["athlete"]["id"]))
                if g not in ("QB", "RB", "WR", "TE", "K"):
                    continue
                st = dict(zip(labels, a.get("stats", [])))
                b = acc.setdefault(g, {})
                add = lambda k, v: b.__setitem__(k, b.get(k, 0) + v)
                name = cat.get("name")
                if name == "passing":
                    c_a = str(st.get("C/ATT", "0/0")).split("/")
                    add("pass_cmp", _num(c_a[0])); add("pass_att", _num(c_a[1]) if len(c_a) > 1 else 0)
                    add("pass_yds", _num(st.get("YDS"))); add("pass_td", _num(st.get("TD"))); add("pass_int", _num(st.get("INT")))
                elif name == "rushing":
                    add("rush_att", _num(st.get("CAR"))); add("rush_yds", _num(st.get("YDS"))); add("rush_td", _num(st.get("TD")))
                elif name == "receiving":
                    add("rec", _num(st.get("REC"))); add("rec_yds", _num(st.get("YDS"))); add("rec_td", _num(st.get("TD")))
                    b["long_rec"] = max(b.get("long_rec", 0), _num(st.get("LONG")))
                elif name == "kicking":
                    add("fg", _num(st.get("FG"))); add("k_pts", _num(st.get("PTS")))
    return out


def _nba_game(eid: str) -> dict | None:
    s = _get(f"{ESPN}/basketball/nba/summary?event={eid}")
    teams = s.get("boxscore", {}).get("players", [])
    if len(teams) != 2:
        return None
    out = {}
    for i, t in enumerate(teams):
        dfn = teams[1 - i]["team"]["abbreviation"]
        acc = out.setdefault(dfn, {})
        cat = (t.get("statistics") or [{}])[0]
        labels = cat.get("labels") or cat.get("names") or []
        for a in cat.get("athletes", []):
            st = dict(zip(labels, a.get("stats", [])))
            if not st or str(st.get("MIN", "0")) in ("0", "", "--"):
                continue
            p = ((a["athlete"].get("position") or {}).get("abbreviation") or "F")[0]
            b = acc.setdefault(p if p in "GFC" else "F", {})
            for k in ("PTS", "REB", "AST", "STL", "BLK", "TO"):
                b[k] = b.get(k, 0) + _num(st.get(k))
            b["3PM"] = b.get("3PM", 0) + _num(str(st.get("3PT", "0-0")).split("-")[0])
    return out


def _final_events(league: str) -> list[str]:
    today = dt.date.today()
    ids = []
    if league == "NFL":
        for wk in range(1, 19):
            evs = _get(f"{ESPN}/football/nfl/scoreboard?seasontype=2&week={wk}&dates={today.year if today.month >= 3 else today.year - 1}").get("events", [])
            done = [e["id"] for e in evs if e["competitions"][0]["status"]["type"]["state"] == "post"]
            ids += done
            if evs and not done:
                break
    elif league == "NBA":
        start = dt.date(today.year if today.month >= 8 else today.year - 1, 10, 15)
        days = [start + dt.timedelta(days=i) for i in range((today - start).days)]
        if len(days) < 20:                                      # early season: the last six weeks of last regular season
            end = dt.date(start.year, 4, 12)
            days = [end - dt.timedelta(days=i) for i in range(42)] + days
        def one(d):
            try:
                evs = _get(f"{ESPN}/basketball/nba/scoreboard?dates={d:%Y%m%d}").get("events", [])
            except Exception:
                return []
            return [e["id"] for e in evs if e["competitions"][0]["status"]["type"]["state"] == "post"
                    and (e.get("season") or {}).get("type") == 2]
        with cf.ThreadPoolExecutor(6) as ex:
            for got in ex.map(one, days):
                ids += got
    return ids


def update(league: str, log=print) -> dict:
    """Fetch box scores for final games not in the cache yet."""
    d = _load(league)
    new = [e for e in _final_events(league) if e not in d["games"]]
    reader = _nfl_game if league == "NFL" else _nba_game
    def safe(e):
        try:
            return e, reader(e)
        except Exception:
            return e, None
    with cf.ThreadPoolExecutor(6) as ex:
        for e, g in ex.map(safe, new):
            if g:
                d["games"][e] = g
    d["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    _save(league, d)
    log(f"{league} defense vs position: {len(d['games'])} games ({len(new)} new)")
    table.cache_clear()
    return d


@functools.lru_cache(maxsize=None)
def table(league: str, group: str, terms: tuple[str, ...]) -> dict[str, float]:
    """{defense: per-game total allowed to this position group for these terms}."""
    tot, n = {}, {}
    for g in _load(league)["games"].values():
        for dfn, groups in g.items():
            v = groups.get(group)
            if v is None and league == "NFL" and group in ("TE", "K"):
                v = {}
            if v is None:
                continue
            tot[dfn] = tot.get(dfn, 0) + sum(v.get(t, 0) for t in terms)
            n[dfn] = n.get(dfn, 0) + 1
    return {k: tot[k] / n[k] for k in tot if n[k] >= 2}


@functools.lru_cache(maxsize=None)
def _nba_positions(team: str) -> dict[str, str]:
    r = _get(f"{ESPN}/basketball/nba/teams/{team.lower()}/roster")
    return {str(a["id"]): (a.get("position") or {}).get("abbreviation", "") for a in r.get("athletes", [])}


def position_of(league: str, team: str, aid: str | None) -> str:
    """The player's position from his ESPN roster, for rows that don't carry it."""
    if not aid or not team:
        return ""
    try:
        from .tier import espn_team
        t = espn_team(league, team)
        return (nfl_positions(t) if league == "NFL" else _nba_positions(t) if league == "NBA" else {}).get(str(aid), "")
    except Exception:
        return ""


# ------------------------------------------------------------------ the card for one prop
def card(league: str, market: str, stat: str, opp: str, position: str = "", pid: str | None = None, team: str = "",
         date: str = "") -> dict | None:
    """The Defense vs Position card for one prop, or None when there's nothing to rank."""
    if not opp:
        return None
    try:
        if league == "NFL":
            spec = NFL_STATS.get(market)
            g = {"FB": "RB", "HB": "RB", "PK": "K"}.get(position, position)
            if not spec or g not in ("QB", "RB", "WR", "TE", "K"):
                return None
            t = table("NFL", g, spec[0])
            o = {"WAS": "WSH"}.get(opp, opp)
            return _card("Defense vs Position", f"{o} defense vs {g} {spec[1]}", f"Def vs {GROUP_WORD[g]}", o, t, False, "less",
                         "allowed a game", 1 if max(t.values() or [0]) >= 10 else 2)
        if league == "NBA":
            terms = NBA_STATS.get(market)
            g = (position or "F")[0]
            g = g if g in "GFC" else "F"
            if not terms:
                return None
            t = table("NBA", g, terms)
            from .tier import espn_team
            o = espn_team("NBA", opp)
            words = " + ".join(NBA_WORDS[x] for x in terms)
            return _card("Defense vs Position", f"{o} defense vs {GROUP_WORD[g]}' {words}", f"Def vs {GROUP_WORD[g]}", o, t, False, "less",
                         "allowed a game")
        if league == "NHL":
            from .context import nhl_teams, _nhl_opp
            t = nhl_teams()["teams"]
            o = _nhl_opp(opp)
            if market == "goalie_saves":                        # few shots taken = strong against saves
                return _card("Offense vs Goalies", f"{o} shots taken a game", "Offense vs goalies", o, {k: v["sf"] for k, v in t.items()},
                             True, "more", "shots a game")
            key, words = ("sa", "shots allowed") if market in ("skater_sog", "skater_blocks") else ("ga", "goals allowed")
            return _card("Defense vs Skaters", f"{o} {words} a game", "Def vs skaters", o, {k: v[key] for k, v in t.items()}, False, "less", "a game")
        if league == "MLB":
            return mlb_card(market, opp, pid, date)
    except Exception:
        return None
    return None


# MLB: market -> (team field, a high value means a strong unit?, which side a strong unit helps, words, digits)
MLB_BAT = {"batter_hits": ("avg", False, "less", "batting average allowed", 3), "batter_singles": ("avg", False, "less", "batting average allowed", 3),
           "batter_total_bases": ("slg", False, "less", "slugging allowed", 3), "batter_doubles": ("slg", False, "less", "slugging allowed", 3),
           "batter_home_runs": ("homeRunsPer9", False, "less", "home runs allowed per 9", 2),
           "batter_hrr": ("runsScoredPer9", False, "less", "runs allowed per 9", 2), "batter_runs": ("runsScoredPer9", False, "less", "runs allowed per 9", 2),
           "batter_rbi": ("runsScoredPer9", False, "less", "runs allowed per 9", 2), "batter_walks": ("walksPer9Inn", False, "less", "walks per 9", 2),
           "batter_strikeouts": ("strikeoutsPer9Inn", True, "more", "strikeouts per 9", 2),      # a strikeout staff gives a hitter's Ks
           "batter_sb": ("stolenBases", False, "less", "stolen bases allowed", 0)}
MLB_PITCH = {"pitcher_hits_allowed": ("avg", True, "more", "batting average", 3), "pitcher_earned_runs": ("runs", True, "more", "runs scored", 0),
             "pitcher_walks": ("baseOnBalls", True, "more", "walks drawn", 0), "pitcher_outs": ("obp", True, "less", "on-base percentage", 3)}


@functools.lru_cache(maxsize=None)
def _mlb_team_table(group: str, field: str, season: int) -> dict[str, float]:
    d = _get(f"https://statsapi.mlb.com/api/v1/teams/stats?season={season}&group={group}&stats=season&sportIds=1")
    from .context import _mlb_team_ids
    ids = {v: k for k, v in _mlb_team_ids().items()}
    out = {}
    for sp in d["stats"][0]["splits"]:
        ab = ids.get(sp["team"]["id"])
        try:
            out[ab] = float(sp["stat"][field])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def mlb_card(market: str, opp: str, pid: str | None, date: str) -> dict | None:
    season = int(date[:4]) if date else dt.date.today().year
    from .context import _mlb_team_ids
    ids = _mlb_team_ids()
    o = opp
    if market in MLB_BAT:
        field, high_strong, helps, words, digits = MLB_BAT[market]
        t = _mlb_team_table("pitching", field, season)
        o = o if o in t else next((k for k in t if ids.get(k) == ids.get(opp)), o)
        return _card("Pitching vs Batters", f"{o} pitching: {words}", "Pitching vs hitters", o, t, high_strong, helps, "", digits)
    if market == "pitcher_strikeouts" and pid:
        from .context import mlb_k_table, pitch_hand
        hand = pitch_hand(pid)
        t = mlb_k_table(hand, season)
        o = o if o in t else next((k for k in t if ids.get(k) == ids.get(opp)), o)
        # a lineup that rarely strikes out is strong against a pitcher's Ks
        return _card("Lineup vs Pitchers", f"{o} strikeout rate vs {'lefties' if hand == 'L' else 'righties'}", "Lineup vs Ks", o,
                     {k: v * 100 for k, v in t.items()}, False, "less", "% strikeouts")
    spec = MLB_PITCH.get(market)
    if spec:
        field, high_strong, helps, words, digits = spec
        t = _mlb_team_table("hitting", field, season)
        o = o if o in t else next((k for k in t if ids.get(k) == ids.get(opp)), o)
        return _card("Lineup vs Pitchers", f"{o} lineup: {words}", "Lineup vs pitchers", o, t, high_strong, helps, "", digits)
    return None
