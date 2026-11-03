import os
import sys
import unittest
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gamesim import backtest, data, engine, ratings, report  # noqa: E402
from gamesim.drives import DOWNS, FG, PUNT, SAFETY, TD, TO  # noqa: E402


def toy_model():
    """A small, fixed drive model so engine tests run offline."""
    p = np.array([0.25, 0.20, 0.36, 0.12, 0.066, 0.004])
    W = np.zeros((6, 11))
    W[:, 0] = np.log(p)
    W[TD, 3], W[TD, 4] = 4.0, 3.0           # better offense / worse defense -> more touchdowns
    W[PUNT, 3], W[PUNT, 4] = -2.0, -1.5
    dur = {}
    for c, s in ((TD, 240.0), (FG, 260.0), (PUNT, 140.0), (TO, 130.0), (DOWNS, 200.0), (SAFETY, 40.0)):
        for t in ("norm", "two", "lead", "trail"):
            dur[(c, t)] = np.array([s * (0.3 if t == "two" else 1.0)])
    nxt = {(c, b): np.array([v]) for c, v in ((PUNT, 70.0), (TO, 55.0), (DOWNS, 50.0), (FG, 68.0)) for b in range(10)}
    nxt[(SAFETY, 0)] = np.array([60.0])
    return {"W": W, "sigma_game": 0.12, "pace_sd": 0.1, "fg_beta": np.array([2.16, -0.98]), "fg_dist": {b: np.array([40.0]) for b in range(10)},
            "xp": 0.95, "two": 0.48, "p_def_td": 0.09, "dur": dur, "next": nxt, "kick": np.array([70.0]),
            "fg_wind": {"coef_per_10mph": 0.0, "mean_wind": 0.0, "n_with_wind": 0}}


AVG = {"off_epa": 0.0, "off_sr": 0.0, "def_epa": 0.0, "def_sr": 0.0, "pace_ratio": 1.0}


class Engine(unittest.TestCase):
    def test_monte_carlo_error_at_50k(self):
        s = engine.summary(engine.simulate({"home": dict(AVG), "away": dict(AVG)}, toy_model(), n=50000, seed=1, hfa=False))
        self.assertAlmostEqual(s["home_win"][1], 0.0022, delta=0.0002)     # ~ +-0.22% at 50,000 runs

    def test_fixed_seed_reproduces(self):
        a = engine.simulate({"home": dict(AVG), "away": dict(AVG)}, toy_model(), n=2000, seed=7)
        b = engine.simulate({"home": dict(AVG), "away": dict(AVG)}, toy_model(), n=2000, seed=7)
        self.assertTrue(np.array_equal(a["home"], b["home"]) and np.array_equal(a["away"], b["away"]))

    def test_equal_teams_are_a_coin_flip_without_home_field(self):
        s = engine.summary(engine.simulate({"home": dict(AVG), "away": dict(AVG)}, toy_model(), n=40000, seed=2, hfa=False))
        self.assertLess(abs(s["home_win"][0] - s["away_win"][0]), 0.02)
        self.assertLess(s["tie"][0], 0.03)

    def test_better_offense_wins_more_and_scores_more(self):
        s = engine.summary(engine.simulate({"home": {**AVG, "off_epa": 0.15}, "away": dict(AVG)}, toy_model(), n=20000, seed=3, hfa=False))
        self.assertGreater(s["home_win"][0], 0.6)
        self.assertGreater(s["home_mean"] - s["away_mean"], 2.0)

    def test_scoring_is_lumpy_on_3_and_7(self):
        sim = engine.simulate({"home": dict(AVG), "away": dict(AVG)}, toy_model(), n=30000, seed=4, hfa=False)
        self.assertFalse(np.any(sim["home"] == 1) or np.any(sim["away"] == 1))   # 1 point is unreachable
        m = Counter(np.abs(sim["home"] - sim["away"]).tolist())
        top = [k for k, _ in m.most_common(4) if k != 0]
        self.assertIn(3, top)
        self.assertIn(7, top)

    def test_whole_game_is_played(self):
        sim = engine.simulate({"home": dict(AVG), "away": dict(AVG)}, toy_model(), n=5000, seed=5)
        self.assertGreater(sim["drives"].mean(), 16)       # both halves, not just the first


class NoLeakage(unittest.TestCase):
    def _play(self, gid, date, off, de, epa, week="1"):
        return {"game_id": gid, "season": "2026", "week": week, "posteam": off, "defteam": de, "home_team": off, "away_team": de,
                "play_type": "pass", "epa": str(epa), "success": "1" if epa > 0 else "0", "qb_dropback": "1", "passer_player_id": off + "qb",
                "passer_player_name": off + " QB", "wp": "0.5", "qb_kneel": "0", "qb_spike": "0", "game_date": date}

    def test_ratings_ignore_games_on_or_after_the_date(self):
        past = [self._play("g1", "2026-10-01", "AAA", "BBB", 0.3) for _ in range(50)] + [self._play("g1", "2026-10-01", "BBB", "AAA", -0.2) for _ in range(50)]
        future = [self._play("g2", "2026-11-05", "AAA", "BBB", -2.0) for _ in range(500)]
        r1 = ratings.team_ratings(ratings.rating_plays(past, before="2026-11-05"))
        r2 = ratings.team_ratings(ratings.rating_plays(past + future, before="2026-11-05"))
        self.assertEqual(r1["n_plays"], r2["n_plays"])
        self.assertAlmostEqual(r1["teams"]["AAA"]["off_epa"], r2["teams"]["AAA"]["off_epa"])
        self.assertGreater(r1["teams"]["AAA"]["off_epa"], r1["teams"]["BBB"]["off_epa"])


class MarketAndRules(unittest.TestCase):
    def test_no_vig(self):
        self.assertAlmostEqual(backtest.no_vig(-110, -110), 0.5)
        self.assertAlmostEqual(backtest.no_vig(-200, 170), (2 / 3) / (2 / 3 + 100 / 270))

    def test_decision_rule(self):
        self.assertEqual(report.decision(0.55, 0.52, 0.01)["verdict"], "PLAY")     # 3 pts edge, 3 - 1.5 > 0
        self.assertEqual(report.decision(0.55, 0.52, 0.03)["verdict"], "PASS")     # 3 - 4.5 < 0
        self.assertEqual(report.decision(0.53, 0.52, 0.001)["verdict"], "PASS")    # edge under 2 pts
        self.assertAlmostEqual(report.total_error(0.003, 0.04), np.sqrt(0.003 ** 2 + 0.04 ** 2))

    def test_fair_odds(self):
        self.assertEqual(backtest.fair_american(0.5), "+100")
        self.assertEqual(backtest.fair_american(0.75), "-300")


@unittest.skipUnless(os.path.exists(os.path.join(data.CACHE, "pbp_2026.slim2.json")), "needs cached 2026 play-by-play")
class ReproducesRatings(unittest.TestCase):
    def test_simulated_season_scoring_tracks_ratings(self):
        """Each team vs a league-average opponent: simulated points should line up with what its ratings imply and
        with its actual points per game, and the league average should match the real one."""
        from gamesim import drives
        P25, P26 = data.pbp(2025), data.pbp(2026)
        allp = P25 + P26
        D = drives.build_drives(allp)
        M = drives.fit(allp, D, before="2026-11-03")
        R = ratings.team_ratings(ratings.rating_plays(P26, before="2026-11-03"))
        sched = [g for g in data.schedule() if g["season"] == "2026" and g["result"] and g["gameday"] < "2026-11-03"]
        ppg = {}
        for g in sched:
            for t, pts in ((g["home_team"], g["home_score"]), (g["away_team"], g["away_score"])):
                ppg.setdefault(t, []).append(float(pts))
        sim_pts, act = [], []
        for t, r in R["teams"].items():
            s = engine.simulate({"home": {**AVG, "off_epa": r["off_epa"], "off_sr": r["off_sr"]}, "away": dict(AVG)}, M, n=3000, seed=9, hfa=False)
            sim_pts.append(float(s["home"].mean()))
            act.append(np.mean(ppg[t]))
        self.assertGreater(np.corrcoef(sim_pts, act)[0, 1], 0.6)
        allpts = [float(x) for g in sched for x in (g["home_score"], g["away_score"])]
        avg = engine.simulate({"home": dict(AVG), "away": dict(AVG)}, M, n=20000, seed=10, hfa=False)
        self.assertLess(abs((avg["home"].mean() + avg["away"].mean()) / 2 - np.mean(allpts)), 2.0)


@unittest.skipUnless(os.path.exists(os.path.join(data.CACHE, "pbp_2026.slim2.json")), "needs cached play-by-play")
class PlayByPlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gamesim import drives, nfl_pbp
        P25, P26 = data.pbp(2025), data.pbp(2026)
        allp = P25 + P26
        DM = drives.fit(allp, drives.build_drives(allp), before="2026-11-03")
        cls.M = nfl_pbp.fit(allp, "2026-11-03", fg_beta=DM["fg_beta"], fg_wind=DM["fg_wind"])
        cls.N = {"comp": 0.0, "sack": 0.0, "int": 0.0, "ypc_mult": 1.0, "ypr_mult": 1.0, "pass_offset": 0.0}
        cls.sim = nfl_pbp.simulate({"home": dict(cls.N), "away": dict(cls.N)}, cls.M, n=4000, seed=1, trace=300)

    def test_snaps_and_scoring_look_like_the_nfl(self):
        self.assertTrue(140 <= self.sim["plays"].mean() <= 156)                       # real 2026: 147 snaps a game
        ppg = (self.sim["home"].mean() + self.sim["away"].mean()) / 2
        self.assertTrue(19 <= ppg <= 26)                                              # real 2025-26: 23.0

    def test_gains_are_whole_yards_and_goal_line_scores(self):
        gains = [p["gain"] for g in self.sim["trace"] for p in g if p["act"] in ("run", "pass")]
        self.assertTrue(all(float(x).is_integer() for x in gains))
        gl = [p["td"] for g in self.sim["trace"] for p in g if p["act"] in ("run", "pass") and not p["pen"] and p["yl"] <= 2]
        self.assertTrue(0.35 <= np.mean(gl) <= 0.65)                                 # real: ~51% of snaps inside the 2

    def test_better_passing_offense_wins_more(self):
        from gamesim import nfl_pbp
        s = nfl_pbp.simulate({"home": {**self.N, "comp": 0.3, "ypc_mult": 1.15}, "away": dict(self.N)}, self.M, n=4000, seed=2)
        self.assertGreater(float((s["home"] > s["away"]).mean()), 0.6)


class Basketball(unittest.TestCase):
    R = {"league": {"to": 0.15, "three": 0.42, "p2": 0.54, "p3": 0.35, "ft_rate": 0.12, "ftp": 0.78, "orb": 0.27, "pace": 100.0},
         "teams": {}, "sd_p2": 0.01, "sd_p3": 0.01, "sd_pace": 4.0, "and1": 0.08, "dur_scale": 0.96}

    def test_possessions_and_scoring(self):
        from gamesim import nba
        avg = nba.side(self.R, "_", "_", False)
        s = nba.simulate(avg, dict(avg), self.R, 48, n=20000, seed=1)
        self.assertTrue(190 <= s["possessions"].mean() <= 215)            # ~100 a team
        self.assertTrue(95 <= s["home"].mean() <= 125)
        self.assertFalse(np.any(s["home"] == s["away"]))                   # overtime until someone wins
        self.assertLess(abs(float((s["home"] > s["away"]).mean()) - 0.5), 0.02)

    def test_better_shooting_wins(self):
        from gamesim import nba
        avg = nba.side(self.R, "_", "_", False)
        s = nba.simulate({**avg, "p3": 0.40, "p2": 0.57}, dict(avg), self.R, 48, n=20000, seed=2)
        self.assertGreater(float((s["home"] > s["away"]).mean()), 0.65)

    def test_late_fouling_happens(self):
        from gamesim import nba
        avg = nba.side(self.R, "_", "_", False)
        s = nba.simulate(avg, dict(avg), self.R, 48, n=3000, seed=3, trace=300)
        fouls = sum(p["foul"] for g in s["trace"] for p in g)
        self.assertGreater(fouls, 0)
        self.assertTrue(all(p["clock"] <= 60 for g in s["trace"] for p in g if p["foul"]))


if __name__ == "__main__":
    unittest.main()
