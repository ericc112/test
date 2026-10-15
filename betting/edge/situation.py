"""Circumstances a game log can't see (L31), read before a prop is rated: tonight's injury and rest report, a teammate's
absence, the player's latest Rotowire note, the spread and total, the weather, the probable goalie, a back-to-back.

check(...) returns the flags for one prop. A flag only ever lowers a label or withdraws a prop, never raises one:
  OUT   not playable tonight (listed out, on IR/IL, not the probable goalie)          -> withdraw
  HOLD  the role tonight isn't the role in his log (sits/limited for an over,           -> Low
        a new starting role for an under, doubtful)
  CAP   real doubt the numbers can't price (questionable, a star teammate newly out,   -> Medium at most
        blowout spread, wind or rain, a goalie's second night)
  INFO  context worth reading next to the number (total, opponent resting, weather)
Sources: ESPN's game summary (injuries, odds, gameInfo.weather, goalies, leaders) and the athlete overview's Rotowire note.
"""
from __future__ import annotations

import datetime as dt
import functools
import re
from dataclasses import dataclass, field

from .grade import _get

SPORT = {"NBA": "basketball/nba", "NFL": "football/nfl", "MLB": "baseball/mlb", "NHL": "hockey/nhl"}
OUT_STATUS = ("out", "injured reserve", "il", "suspension", "suspended")
RANK = {"OUT": 3, "HOLD": 2, "CAP": 1, "INFO": 0}

# Rotowire phrases, read in the player's latest note
SIT = r"remains to be seen|won't play|will not play|not expected to play|sit out|sitting out|will rest|rest(ed|ing)? (on|for|tonight|thursday|friday|saturday|sunday|monday|tuesday|wednesday)|load management|game-time decision|questionable|doubtful|minutes (restriction|limit)|limited minutes|on a minutes|pitch count|innings limit|bulk reliever|(as|serve as) (an |the )?opener"
ROLE_UP = r"will start|expected to start|in line to start|starting (role|lineup|spot)|moves? into the starting|promoted|lead back|top line|first line|top-six|first-unit|first unit|bigger role|expanded role|featured"
ROLE_DOWN = r"come off the bench|coming off the bench|demoted|second unit|healthy scratch|reduced role|out of the rotation|benched|fourth line"
# stats whose overs a blowout, wind or rain hit hardest
PASS_KICK = {"pass_yds", "pass_tds", "pass_cmp", "pass_att", "rec_yds", "receptions", "longest_rec", "fg_made", "kicking_pts", "pass_rush_yds"}
PITCH_LONG = {"pitcher_strikeouts", "pitcher_outs"}


@dataclass
class Situation:
    flags: list = field(default_factory=list)                   # (level, text)

    def add(self, level: str, text: str):
        self.flags.append((level, text))

    @property
    def worst(self) -> str:
        return max((lv for lv, _ in self.flags), key=RANK.get, default="INFO")

    def apply(self, confidence: str) -> str:
        """The label after the circumstances: OUT and HOLD -> Low, CAP -> Medium at most."""
        w = self.worst
        if w in ("OUT", "HOLD") and confidence in ("High", "Medium"):
            return "Low"
        if w == "CAP" and confidence == "High":
            return "Medium"
        return confidence

    def notes(self) -> list[str]:
        return [f"circumstances ({lv.lower()}): {t}" for lv, t in sorted(self.flags, key=lambda f: -RANK[f[0]])]


def _key(name: str) -> tuple[str, str]:
    from .tier import name_key
    return name_key(name)


@functools.lru_cache(maxsize=None)
def summary(league: str, event_id: str) -> dict:
    try:
        return _get(f"https://site.api.espn.com/apis/site/v2/sports/{SPORT[league]}/summary?event={event_id}")
    except Exception:
        return {}


@functools.lru_cache(maxsize=None)
def rotowire(league: str, espn_id: str) -> str:
    """The player's latest Rotowire headline and story (ESPN athlete overview), or ''."""
    if not espn_id:
        return ""
    try:
        o = _get(f"https://site.web.api.espn.com/apis/common/v3/sports/{SPORT[league]}/athletes/{espn_id}/overview")
    except Exception:
        return ""
    rw = o.get("rotowire") or {}
    return " ".join(x for x in (rw.get("headline"), rw.get("story")) if x)


def _team_abbr(t: dict) -> str:
    return ((t.get("team") or {}).get("abbreviation") or "").upper()


def _recent(date: str | None, days: int = 10) -> bool:
    try:
        d = dt.datetime.fromisoformat((date or "").replace("Z", "+00:00"))
    except ValueError:
        return True                                             # undated: treat as news
    return (dt.datetime.now(dt.timezone.utc) - d).days <= days


def _leaders(s: dict, team: str) -> set[tuple[str, str]]:
    out = set()
    for t in s.get("leaders") or []:
        if _team_abbr(t) != team:
            continue
        for cat in t.get("leaders") or []:
            for a in (cat.get("leaders") or [])[:1]:
                nm = (a.get("athlete") or {}).get("displayName")
                if nm:
                    out.add(_key(nm))
    return out


def check(league: str, event_id: str, team: str, player: str, espn_id: str | None, market: str, side: str,
          game_day: str | None = None, read_news: bool = True) -> Situation:
    """Flags for one prop. `team` is the player's team as ESPN abbreviates it; `side` is 'over' or 'under'."""
    from .tier import espn_team
    sit = Situation()
    s = summary(league, str(event_id)) if event_id else {}
    team = espn_team(league, (team or "").upper())
    over = side == "over"
    me = _key(player)

    # 1. tonight's injury and rest report: him, his teammates, the other side
    opp_rest = []
    for t in s.get("injuries") or []:
        mine = _team_abbr(t) == team
        for i in t.get("injuries") or []:
            a = i.get("athlete") or {}
            status = (i.get("status") or "").strip()
            st = status.lower()
            kind = ((i.get("details") or {}).get("type") or i.get("type") or "")
            kind = kind if isinstance(kind, str) else (kind.get("description") or "")
            is_me = (espn_id and str(a.get("id")) == str(espn_id)) or (_key(a.get("displayName", "")) == me and me[1])
            resting = kind.lower() in ("rest", "not injury related")
            if is_me:
                if any(st.startswith(o) or o in st for o in OUT_STATUS) and not st.startswith("day"):
                    sit.add("OUT", f"listed {status} ({kind}) tonight")
                elif "doubtful" in st:
                    sit.add("HOLD", f"listed doubtful ({kind})")
                elif resting and over:
                    sit.add("HOLD", f"listed {status}, {kind.lower()}: he may sit or play limited minutes")
                elif resting:
                    sit.add("INFO", f"listed {status}, {kind.lower()}: if he sits, PrizePicks voids it; if he plays, limited minutes help the under")
                elif "questionable" in st or "day-to-day" in st or "game-time" in st:
                    sit.add("CAP", f"listed {status} ({kind}): confirm he plays")
            elif mine and (st.startswith("out") or "doubtful" in st or resting) and _recent(i.get("date")):
                lead = _key(a.get("displayName", "")) in _leaders(s, team)
                if lead and not over and league in ("NBA", "NFL"):
                    sit.add("CAP", f"teammate {a.get('displayName')} ({kind or status}) is out: more usage for the rest, unders lose their cushion")
                elif lead:
                    sit.add("INFO", f"teammate {a.get('displayName')} ({kind or status}) is out: more usage for the rest")
            elif not mine and (resting or st.startswith("out")) and _recent(i.get("date")) and league in ("NBA", "NHL"):
                opp_rest.append(a.get("displayName"))
    if opp_rest:
        sit.add("INFO", f"opponent without {', '.join(n for n in opp_rest[:5] if n)}")

    # 2. spread and total: blowouts cut starters' minutes; the total sets the scoring environment
    odds = next(iter(s.get("pickcenter") or s.get("odds") or []), {}) or {}
    spread, total = odds.get("spread"), odds.get("overUnder")
    if league == "NBA" and spread is not None and abs(float(spread)) >= 12 and over:
        sit.add("CAP", f"spread {odds.get('details')}: a blowout can sit starters for the fourth quarter")
    if total is not None:
        sit.add("INFO", f"game total {total} ({odds.get('details') or 'no line'})")

    # 3. weather, outdoors
    w = (s.get("gameInfo") or {}).get("weather") or {}
    gust, rain, temp = w.get("gust") or 0, w.get("precipitation") or 0, w.get("temperature")
    if w:
        if league == "NFL" and over and market in PASS_KICK and (gust >= 20 or rain >= 70):
            sit.add("CAP", f"weather: gusts {gust} mph, {rain}% rain: passing and kicking overs suffer")
        elif league == "MLB" and over and market in PITCH_LONG and rain >= 60:
            sit.add("CAP", f"weather: {rain}% rain: a delay can end the starter's night")
        sit.add("INFO", f"weather {temp}°F, gusts {gust} mph, {rain}% rain")

    # 4. NHL goalies: saves need the probable starter; a second night means the backup more often
    if league == "NHL" and market == "goalie_saves":
        names = [_key(a.get("displayName", "")) for side_ in (s.get("goalies") or {}).values() if isinstance(side_, dict)
                 for a in side_.get("athletes") or []]
        if names and me not in names:
            sit.add("OUT", "not tonight's probable goalie")
        elif not names:
            sit.add("CAP", "starting goalie not confirmed yet")

    # 5. the second night of a back-to-back
    if game_day:
        from .tier import slate_day
        prev = (dt.date.fromisoformat(game_day) - dt.timedelta(days=1)).isoformat()
        days = {slate_day(e.get("gameDate")) for t in s.get("lastFiveGames") or [] if _team_abbr(t) == team
                for e in t.get("events") or [] if e.get("gameDate")}
        if prev in days:
            if league == "NHL" and market == "goalie_saves":
                sit.add("CAP", "second night of a back-to-back: backup goalies start more often")
            elif league in ("NBA", "NHL"):
                sit.add("INFO", "second night of a back-to-back: rest and minutes risk")

    # 6. the player's latest note: a word from the beat writer the numbers never see
    if read_news and espn_id and league in ("NBA", "NFL", "NHL", "MLB"):
        note = rotowire(league, str(espn_id))
        low = note.lower()
        quote = lambda m: note[max(0, m.start() - 60): m.end() + 80].strip()
        m = re.search(SIT, low)
        if m:
            sit.add("HOLD" if over else "INFO", f"Rotowire: \"...{quote(m)}...\"" + ("" if over else " (sitting voids it; limited minutes help an under)"))
        m = re.search(ROLE_UP, low)
        if m and not over and market not in PITCH_LONG and market != "goalie_saves":   # a starter who 'will start' isn't news
            sit.add("HOLD", f"Rotowire, a bigger role than his log: \"...{quote(m)}...\" (L5)")
        m = re.search(ROLE_DOWN, low)
        if m and over:
            sit.add("HOLD", f"Rotowire, a smaller role than his log: \"...{quote(m)}...\" (L5)")
    return sit
