import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge import nba_pp as N  # noqa: E402


class NbaPrizePicks(unittest.TestCase):
    """The pieces of the NBA PrizePicks pricer that don't need the network."""

    hist = [int(1000 * np.exp(-0.5 * ((k - 20) / 6) ** 2)) for k in range(90)]     # points centred on 20

    def test_sides_at_half_and_whole_lines(self):
        o, u, p = N.sides_at(self.hist, 19.5)
        self.assertAlmostEqual(o + u, 1.0, places=9)
        self.assertEqual(p, 0.0)
        o2, u2, p2 = N.sides_at(self.hist, 20)
        self.assertGreater(p2, 0.0)
        self.assertAlmostEqual(o2 + u2 + p2, 1.0, places=9)

    def test_market_carry_reproduces_the_book_at_its_line(self):
        # DraftKings 21.5 at 55% over; PrizePicks 19.5: slide the simulated shape to match, then read at 19.5
        p, s = N.market_at(self.hist, 21.5, 0.55, 21.5)
        self.assertAlmostEqual(p, 0.55, places=3)
        p2, _ = N.market_at(self.hist, 21.5, 0.55, 19.5)
        self.assertGreater(p2, 0.55)                     # a lower line is more likely to go over
        self.assertGreater(s, 0.0)                       # the book sits above the simulation here

    def test_names_and_team_codes(self):
        ps = [{"name": "Nic Claxton"}, {"name": "Jaren Jackson Jr."}, {"name": "Luka Dončić"}]
        self.assertEqual(N.find_player("Luka Doncic", ps)["name"], "Luka Dončić")
        self.assertEqual(N.find_player("Jaren Jackson", ps)["name"], "Jaren Jackson Jr.")
        self.assertEqual(N.find_player("Nicolas Claxton", ps)["name"], "Nic Claxton")
        self.assertIsNone(N.find_player("Somebody Else", ps))
        self.assertEqual(N.espn_abbr("WAS"), "WSH")
        self.assertEqual(N.espn_abbr("SAS"), "SA")
        self.assertEqual(N.espn_abbr("DET"), "DET")

    def test_us_date_of_evening_tip(self):
        self.assertEqual(N._us_date("2026-11-04T22:30:00-05:00"), "2026-11-04")
        self.assertEqual(N._us_date("2026-11-05T03:30Z"), "2026-11-04")

    def test_pick_order_one_leg_per_game_high_first(self):
        mk = lambda p, c, g, t="standard": {"p_final": p, "confidence": c, "script": g, "odds_type": t}
        rows = [mk(0.62, "Medium", "a"), mk(0.66, "High", "a"), mk(0.70, "Low", "b"), mk(0.64, "Medium", "c"), mk(0.9, "High", "d", "goblin")]
        out = N.pick_order(rows, 5)
        self.assertEqual([r["script"] for r in out], ["a", "c", "b"])
        self.assertEqual(out[0]["confidence"], "High")

    def test_grader_combos(self):
        from edge.grade import NBA_PARTS
        self.assertEqual(NBA_PARTS["pra"], ("pts", "reb", "ast"))
        self.assertEqual(N.PARTS_KEYS["ra"], ("reb", "ast"))


if __name__ == "__main__":
    unittest.main()
