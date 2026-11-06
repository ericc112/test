import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge import tennis as T  # noqa: E402


class Score(unittest.TestCase):
    def test_parse(self):
        sc = T.parse_score("7-6(4) 3-6 6-2")
        self.assertEqual((sc["sets"], sc["games"], sc["tiebreaks"], sc["first_set"]), (3, 30, 1, 13))
        self.assertEqual((sc["games_w"], sc["games_l"]), (16, 14))

    def test_unparseable(self):
        self.assertIsNone(T.parse_score("W/O"))


class Simulator(unittest.TestCase):
    def test_hold_rate_matches_closed_form(self):
        s = T.simulate(0.62, 0.62, 3, n=20000, seed=3)
        # breaks happen only in regular service games; holds = service games - breaks (tiebreaks excluded)
        games = s["games"] - s["tiebreaks"]
        held = 1 - (s["breaks_a"] + s["breaks_b"]).sum() / games.sum()
        self.assertAlmostEqual(held, T._hold(0.62), delta=0.006)

    def test_structure_best_of_3(self):
        s = T.simulate(0.65, 0.6, 3, n=5000, seed=1)
        self.assertTrue(((s["sets"] >= 2) & (s["sets"] <= 3)).all())
        self.assertTrue((s["games"] == s["games_a"] + s["games_b"]).all())
        self.assertTrue(((s["first_set"] >= 6) & (s["first_set"] <= 13)).all())
        self.assertTrue((s["tiebreaks"] <= s["sets"]).all())
        self.assertTrue((s["games"] >= 12).all() and (s["games"] <= 39).all())

    def test_structure_best_of_5(self):
        s = T.simulate(0.66, 0.66, 5, n=3000, seed=2, final_tb10=True)
        self.assertTrue(((s["sets"] >= 3) & (s["sets"] <= 5)).all())
        self.assertTrue((s["games"] <= 65).all())

    def test_stronger_server_wins_more(self):
        s = T.simulate(0.68, 0.60, 3, n=5000, seed=4)
        self.assertGreater(s["a_wins"].mean(), 0.7)

    def test_matchup_is_neutral_for_average_players(self):
        avg = {"spw": 0.62}
        r = {"spw": 0.62, "rpw": 0.38}
        self.assertEqual(T.matchup(r, r, avg), (0.62, 0.62))
        pa, pb = T.matchup({"spw": 0.66, "rpw": 0.38}, {"spw": 0.62, "rpw": 0.40}, avg)
        self.assertAlmostEqual(pa, 0.64)   # A serves 4 pts above average, B returns 2 above
        self.assertAlmostEqual(pb, 0.62)


class Rates(unittest.TestCase):
    def test_thin_surface_shrinks_to_other_surfaces_then_tour(self):
        p = {"splits": {"Hard": {"ms": 30, "spw": 0.66, "rpw": 0.40, "ace": 0.08, "df": 0.03},
                        "Grass": {"ms": 2, "spw": 0.76, "rpw": 0.36, "ace": 0.15, "df": 0.03}}}
        r = T.rates(p, "Grass", {"spw": 0.63, "ace": 0.07})
        self.assertLess(r["spw"], 0.70)      # 2 grass matches don't carry the rate
        self.assertGreater(r["spw"], 0.66)
        r0 = T.rates(p, None, {"spw": 0.63, "ace": 0.07})
        self.assertAlmostEqual(r0["spw"], (32 * ((30 * 0.66 + 2 * 0.76) / 32) + T.MIN_MS * 0.63) / (32 + T.MIN_MS))


class Grading(unittest.TestCase):
    def test_row_dated_by_tournament_start(self):
        p = {"recent": [{"opp_slug": "TaylorFritz", "date": "2026-11-02", "score": "6-4 6-4", "won": True}]}
        self.assertIsNotNone(T._player_row(p, "TaylorFritz", "2026-11-06T13:00:00-05:00"))   # QF, four days after the event's date
        self.assertIsNone(T._player_row(p, "TaylorFritz", "2026-11-30T13:00:00-05:00"))

    def test_same_opponent_twice_is_ambiguous(self):
        p = {"recent": [{"opp_slug": "X", "date": "2026-11-08", "score": "6-4 6-4", "won": True},
                        {"opp_slug": "X", "date": "2026-11-08", "score": "3-6 6-4 6-1", "won": False}]}
        self.assertIsNone(T._player_row(p, "X", "2026-11-15T13:00:00-05:00"))

    def test_retirement_voids(self):
        self.assertIsNone(T.parse_score("6-3 2-1 RET"))


class Form(unittest.TestCase):
    def test_form_makes_matches_more_lopsided(self):
        a = T.simulate(0.56, 0.56, 3, n=20000, seed=5)
        b = T.simulate(0.56, 0.56, 3, n=20000, seed=5, form={"sd": 0.055, "rho": -0.8})
        self.assertLess((b["sets"] == 3).mean(), (a["sets"] == 3).mean() - 0.05)
        self.assertLess(b["games"].mean(), a["games"].mean())

    def test_form_pulls_big_favourites_toward_even(self):
        a = T.simulate(0.66, 0.52, 3, n=20000, seed=6)
        b = T.simulate(0.66, 0.52, 3, n=20000, seed=6, form={"sd": 0.055, "rho": -0.8}, est=(0.0005, 0.0005))
        self.assertLess(b["a_wins"].mean(), a["a_wins"].mean())
        self.assertEqual((b["pa"], b["pb"]), (0.66, 0.52))     # the base rates are reported, not a draw

    def test_points_per_game(self):
        self.assertAlmostEqual(T._pts_per_game(0.5), 6.75, places=6)   # known value for p = 0.5


if __name__ == "__main__":
    unittest.main()
