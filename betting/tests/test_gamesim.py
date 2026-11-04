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

    def test_safeties_and_kneels_near_the_own_goal_line(self):
        # audit M5: own-20 losses replayed at the own 3 gave 0.19 safeties a game (real 2025: 0.044)
        saf, kneel_deep = 0, 0
        for g in self.sim["trace"]:
            for p in g:
                if p["act"] == "kneel" and p["yl"] > 98:
                    kneel_deep += 1
                if p["act"] in ("run", "pass", "kneel") and not p["pen"] and not p["turnover"]:
                    if p["yl"] - (-1.0 if p["act"] == "kneel" else p["gain"]) >= 100:
                        saf += 1
        self.assertEqual(kneel_deep, 0)
        # 0.19 before the fix, ~0.12 after; real is 0.044 (the rest needs a "backed up" term in the call and sack
        # models: a proposal in the audit report, not applied)
        self.assertLess(saf / len(self.sim["trace"]), 0.15)

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

    def test_trailing_team_fouls_when_shot_clock_is_off(self):
        # audit C1: down 1-2 with the shot clock off, the trailing team never got the ball back (leader won 100%)
        from gamesim import nba
        avg = nba.side(self.R, "_", "_", False)
        s = nba.simulate(avg, dict(avg), self.R, 48, n=4000, seed=4, trace=4000)
        checked = 0
        for g in s["trace"]:
            for p in g:
                own, opp = (p["score"][0], p["score"][1]) if p["off"] == 0 else (p["score"][1], p["score"][0])
                lead_before = own - p["pts"] - opp
                if 2 < p["clock"] <= 24 and 1 <= lead_before <= 2:
                    checked += 1
                    self.assertTrue(p["foul"], p)
                    self.assertFalse(p["hold"], p)
        self.assertGreater(checked, 20)

    def test_late_fouling_happens(self):
        from gamesim import nba
        avg = nba.side(self.R, "_", "_", False)
        s = nba.simulate(avg, dict(avg), self.R, 48, n=3000, seed=3, trace=300)
        fouls = sum(p["foul"] for g in s["trace"] for p in g)
        self.assertGreater(fouls, 0)
        self.assertTrue(all(p["clock"] <= 60 for g in s["trace"] for p in g if p["foul"]))


class BasketballPlayers(unittest.TestCase):
    """Player layer: rotation and per-minute rates from box scores, with no look-ahead."""

    @staticmethod
    def _summary(gid, rows):
        lab = ["MIN", "PTS", "FG", "3PT", "FT", "OREB", "DREB", "AST", "TO"]
        ath = [{"athlete": {"id": str(i), "displayName": n, "position": {"abbreviation": "G"}}, "starter": i < 5,
                "didNotPlay": m == 0, "reason": "" if m else r, "stats": [] if m == 0 else [str(m), str(p), "%d-%d" % (fgm, fga), "%d-%d" % (tpm, tpa), "%d-%d" % (ftm, fta), "1", "3", str(a), "1"]}
               for i, (n, m, p, fgm, fga, tpm, tpa, ftm, fta, a, r) in enumerate(rows)]
        return {"boxscore": {"players": [{"team": {"abbreviation": "AAA"}, "statistics": [{"labels": lab, "athletes": ath}]}]}}

    def setUp(self):
        import json
        import tempfile
        from gamesim import nba
        self.nba, self.tmp, self.old = nba, tempfile.TemporaryDirectory(), data.CACHE
        data.CACHE = self.tmp.name
        star = ("Star", 36, 30, 10, 20, 4, 9, 6, 7, 6, "")
        bench = [("P%d" % k, 24, 10, 4, 9, 1, 3, 1, 2, 2, "") for k in range(1, 9)]
        hurt = ("P8", 0, 0, 0, 0, 0, 0, 0, 0, 0, "LEFT ANKLE SPRAIN")
        self.games = []
        for d, rows in (("2026-10-20", [star] + bench), ("2026-10-22", [star] + bench), ("2026-10-24", [star] + bench[:7] + [hurt]),
                        ("2026-10-26", [("Star", 40, 60, 25, 30, 6, 8, 4, 4, 9, "")] + bench)):   # the future game must not leak
            gid = d.replace("-", "")
            self.games.append({"id": gid, "date": d, "final": True, "home": "AAA", "away": "BBB"})
            with open(os.path.join(self.tmp.name, f"nba_sum_{gid}.json"), "w") as f:
                json.dump(self._summary(gid, rows), f)

    def tearDown(self):
        data.CACHE = self.old
        self.tmp.cleanup()

    def test_minutes_sum_and_no_lookahead(self):
        pr = self.nba.player_profiles("nba", self.games, "AAA", "2026-10-25")
        self.assertEqual(pr["games"], 3)
        self.assertAlmostEqual(sum(p["min"] for p in pr["players"]), 240.0, delta=0.5)
        star = next(p for p in pr["players"] if p["name"] == "Star")
        made = 2 * star["fga2"] * star["p2"] + 3 * star["fga3"] * star["p3"] + star["fta"] * star["ftp"]
        self.assertLess(made * 36, 34)                     # 30 a game before; the 60-point game comes later
        self.assertTrue(0.3 < star["p2"] < 0.7)

    def test_out_players_removed_and_shrinkage(self):
        pr = self.nba.player_profiles("nba", self.games, "AAA", "2026-10-25", {"Star"})
        self.assertNotIn("Star", [p["name"] for p in pr["players"]])
        self.assertAlmostEqual(sum(p["min"] for p in pr["players"]), 240.0, delta=0.5)
        full = self.nba.player_profiles("nba", self.games, "AAA", "2026-10-25")
        star = next(p for p in full["players"] if p["name"] == "Star")
        raw3 = 12 / 27                                     # 3PT% in his own games, shrunk toward the team's
        self.assertLess(abs(star["p3"] - 0.33), abs(raw3 - 0.33) + 1e-9)

    def test_injured_last_game_is_returning(self):
        pr = self.nba.player_profiles("nba", self.games, "AAA", "2026-10-25")
        names = {p["name"]: p for p in pr["players"]}
        self.assertTrue(names["P8"]["returning"])          # sat the last game injured, not listed Out now
        self.assertGreater(names["P8"]["min"], 15)

    def test_rebound_credit(self):
        g = [{"final": True, "date": "2026-10-20", "box": {"home": {"fga": 90, "fgm": 42, "orb": 10, "drb": 34}, "away": {"fga": 88, "fgm": 40, "orb": 11, "drb": 33}}}]
        self.assertAlmostEqual(self.nba.reb_credit(g, "2026-10-21"), 88 / 96)
        self.assertEqual(self.nba.reb_credit(g, "2026-10-20"), 0.93)


class Availability(unittest.TestCase):
    """Who is out tonight, priced against who played in the rating sample (no double counting)."""

    def test_shift_is_relative_to_games_already_missed(self):
        from gamesim import nba
        vals = {"players": {"a": {"name": "Star", "value": 6.0, "missed_share": 0.0}, "b": {"name": "Hurt", "value": 4.0, "missed_share": 0.5},
                            "c": {"name": "Back", "value": 3.0, "missed_share": 0.8}}}
        self.assertAlmostEqual(nba.availability_shift(vals, set())["lost"], -0.5 * 4 - 0.8 * 3)       # all play: better than rated
        self.assertAlmostEqual(nba.availability_shift(vals, {"a"})["lost"], 6 - 2 - 2.4)               # the star sits
        self.assertAlmostEqual(nba.availability_shift(vals, {"b"})["lost"], 0.5 * 4 - 2.4)             # half priced in already

    def test_offense_shift_moves_points_by_the_requested_amount(self):
        from gamesim import nba
        R = dict(Basketball.R, league=dict(Basketball.R["league"]), teams={}, and1=0.08)
        s0 = nba.side(R, "_", "_", False)
        s1 = nba.shift_offense(s0, R, -3.0)
        pace = R["league"]["pace"]
        self.assertAlmostEqual((nba.ppp_expected(s1, 0.08) - nba.ppp_expected(s0, 0.08)) * pace, -3.0, delta=0.15)
        self.assertLess(s1["p2"], s0["p2"])
        self.assertLess(s1["p3"], s0["p3"])


class TeamFromPlayers(unittest.TestCase):
    """Team strength from player ratings: the ridge recovers who is good, refits incrementally, and the blend moves
    the margin by w x (players - model) without moving the total."""

    @staticmethod
    def league(n_games=400, seed=4):
        rng = np.random.default_rng(seed)
        true = {f"p{i}": v for i, v in enumerate(rng.normal(0, 4, 24))}
        pids = sorted(true)
        games = []
        for j in range(n_games):
            pick = rng.permutation(pids)[:16]
            rows, y = [], 2.0
            for side, sg in ((pick[:8], 1.0), (pick[8:], -1.0)):
                mins = rng.uniform(5, 40, 8); mins *= 240 / mins.sum()
                for p, m in zip(side, mins):
                    rows.append((p, sg * 5 * m / 240, float(m), 10.0 * m / 36))   # equal Game Score rates: prior 0
                    y += sg * 5 * m / 240 * true[p]
            games.append({"id": str(j), "date": f"2025-{11 + j // 200:02d}-{1 + (j % 200) // 8:02d}T23:00Z", "season": 2025,
                          "h": 1.0, "y": y + rng.normal(0, 3), "rows": rows})
        return true, games

    def test_recovers_player_effects_and_home_edge(self):
        from gamesim import nba
        true, games = self.league()
        PR = nba.PlayerRatings("nba", [], 2025, lam=2.0, prepared=games)
        f = PR.fit("2099-01-01")
        est = np.array([PR.rating(f, p) for p in sorted(true)]); tru = np.array([true[p] for p in sorted(true)])
        self.assertGreater(np.corrcoef(est, tru)[0, 1], 0.95)
        self.assertAlmostEqual(f["h"], 2.0, delta=0.6)

    def test_incremental_fit_equals_fresh_fit(self):
        from gamesim import nba
        _, games = self.league()
        a = nba.PlayerRatings("nba", [], 2025, prepared=games)
        a.fit("2025-11-15"); fa = a.fit("2025-12-10")
        fb = nba.PlayerRatings("nba", [], 2025, prepared=games).fit("2025-12-10")
        self.assertEqual(fa["n_games"], fb["n_games"])
        self.assertTrue(np.allclose(fa["r"], fb["r"]))
        self.assertLess(nba.PlayerRatings("nba", [], 2025, prepared=games).fit("2025-11-02")["n_games"], 100)   # no lookahead

    def test_blend_moves_margin_not_total(self):
        from gamesim import nba
        R = dict(Basketball.R, league=dict(Basketball.R["league"]), teams={}, and1=0.08)
        H0, A0 = nba.side(R, "_", "_", True), nba.side(R, "_", "_", False)
        m0 = nba.expected_margin(H0, A0, R)
        H1, A1, d = nba.with_player_ratings(H0, A0, R, m0 + 10.0, w=0.6)
        self.assertAlmostEqual(d, 6.0, places=6)
        self.assertAlmostEqual(nba.expected_margin(H1, A1, R) - m0, 6.0, delta=0.4)
        pace = R["league"]["pace"]
        tot = lambda H, A: pace * (nba.ppp_expected(H, 0.08) + nba.ppp_expected(A, 0.08))
        self.assertAlmostEqual(tot(H1, A1), tot(H0, A0), delta=0.4)
        self.assertEqual(nba.with_player_ratings(H0, A0, R, None, w=0.6)[2], 0.0)


class SeasonPrior(unittest.TestCase):
    def test_prior_moves_margin_not_total(self):
        from gamesim import nba
        R = dict(Basketball.R, league=dict(Basketball.R["league"]), teams={"AAA": {"games": 4}, "BBB": {"games": 4}}, and1=0.08)
        prior = {"AAA": {"net_last": 6.0, "roster_delta": -2.0}, "BBB": {"net_last": -4.0, "roster_delta": 1.0}}
        sh, sa = nba.prior_shifts(R, prior, "AAA", "BBB", k=4, rho=0.5)
        self.assertAlmostEqual(sh, 0.5 * 0.5 * 4.0, places=6)          # w = 4/(4+4), target 0.5 x (6 - 2), current 0
        self.assertAlmostEqual(sa, 0.5 * 0.5 * -3.0, places=6)
        H0 = nba.side(R, "_", "_", True); A0 = nba.side(R, "_", "_", False)
        H1, A1 = nba.apply_prior(H0, A0, R, sh, sa)
        pace = R["league"]["pace"]
        dm = pace * ((nba.ppp_expected(H1, .08) - nba.ppp_expected(A1, .08)) - (nba.ppp_expected(H0, .08) - nba.ppp_expected(A0, .08)))
        dt = pace * ((nba.ppp_expected(H1, .08) + nba.ppp_expected(A1, .08)) - (nba.ppp_expected(H0, .08) + nba.ppp_expected(A0, .08)))
        self.assertAlmostEqual(dm, sh - sa, delta=0.1)
        self.assertAlmostEqual(dt, 0.0, delta=0.1)

    def test_roster_delta_counts_arrivals_and_departures(self):
        from gamesim import nba
        lv = {"1": {"name": "Star", "value": 8.0, "gp": 82, "teams": {"AAA": 1.0}}, "2": {"name": "Wing", "value": 4.0, "gp": 41, "teams": {"BBB": 0.5}}}
        R0 = {"league": dict(Basketball.R["league"]), "teams": {}, "and1": 0.07}
        p = nba.preseason_prior(R0, lv, "BBB", {"1"})                     # the star moved from AAA to BBB, the wing left
        self.assertAlmostEqual(p["roster_delta"], nba.INJURY_BETA * (8.0 - 4.0 * 0.5))


class Cutoffs(unittest.TestCase):
    """Audit M1/M2: ratings for a US day use every game of earlier US days and nothing from that day."""

    def test_us_day_and_cutoff(self):
        self.assertEqual(data.us_day("2026-11-03T00:30Z"), "2026-11-02")      # 7:30 pm ET on Nov 2
        self.assertEqual(data.us_day("2026-11-03T06:30Z"), "2026-11-02")      # 10:30 pm PT on Nov 2
        self.assertEqual(data.us_day("2026-11-03T17:00Z"), "2026-11-03")      # noon ET on Nov 3
        cut = data.cutoff("2026-11-03")
        self.assertTrue("2026-11-03T03:00Z" < cut)                             # last night's late game is in
        self.assertFalse("2026-11-03T23:30Z" < cut)                            # tonight's early game is out

    def test_pooled_rms(self):
        a = {"win": {"n": 100, "rms_vs_market": 0.10}}
        b = {"win": {"n": 300, "rms_vs_market": 0.14}, "total": {"n": 300, "rms_vs_market": 0.09}}
        r = backtest.pooled_rms(a, b, None)
        self.assertAlmostEqual(r["win"], ((100 * 0.01 + 300 * 0.0196) / 400) ** 0.5)
        self.assertAlmostEqual(r["total"], 0.09)


class Hockey(unittest.TestCase):
    R = {"league": {"shots": 26.0, "fin": 0.095, "ppo": 3.0, "ppc": 0.2, "sv": 0.89, "shg_per_pp": 0.027, "ot_decided": 0.6, "so_home": 0.5},
         "teams": {}, "goalies": {}, "sd_fin": 0.05, "goal_scale": 1.25, "home_mult": 1.03}
    EN = {"for_per_min": 0.14, "against_per_min": 0.34}

    def test_goals_overtime_and_shootout(self):
        from gamesim import nhl
        avg = nhl.side(self.R, "_", "_", False)
        s = nhl.simulate(avg, dict(avg), self.R, self.EN, n=20000, seed=1)
        self.assertTrue(2.6 <= (s["home"].mean() + s["away"].mean()) / 2 <= 3.8)
        self.assertFalse(np.any(s["home"] == s["away"]))                       # OT, then a shootout, always decides it
        self.assertTrue(0.12 <= s["ot"].mean() <= 0.3)

    def test_empty_net_makes_three_goal_margins_common(self):
        from gamesim import nhl
        avg = nhl.side(self.R, "_", "_", False)
        s = nhl.simulate(avg, dict(avg), self.R, self.EN, n=20000, seed=2)
        m = np.abs(s["home"] - s["away"])
        self.assertGreater(float((m == 3).mean()), float((m == 2).mean()) * 0.9)   # real NHL: 3-goal margins outnumber 2-goal ones

    def test_hot_goalie_lowers_goals_against(self):
        from gamesim import nhl
        R = {**self.R, "goalies": {"g1": {"sv": 0.93}}}
        good = nhl.side(R, "_", "_", True, "g1")       # home attack facing a .930 goalie
        s = nhl.simulate(good, nhl.side(R, "_", "_", False), R, self.EN, n=20000, seed=3)
        self.assertLess(s["home"].mean(), s["away"].mean())


if __name__ == "__main__":
    unittest.main()
