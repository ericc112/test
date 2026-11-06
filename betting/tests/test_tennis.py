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


class DeeperHistory(unittest.TestCase):
    def test_exact_win_probability(self):
        from edge import tennis_hist as H
        self.assertAlmostEqual(float(H.match_win(np.array([0.62]), np.array([0.62]), 3)[0]), 0.5, places=6)
        a = float(H.match_win(np.array([0.66]), np.array([0.60]), 3)[0])
        s = T.simulate(0.66, 0.60, 3, n=40000, seed=9)
        self.assertAlmostEqual(a, float(s["a_wins"].mean()), delta=0.01)
        d = H.shift_to(np.array([0.64]), np.array([0.62]), np.array([0.40]), 3, 0.05, -0.8)
        self.assertAlmostEqual(float(H.match_win_form(0.64 + d, 0.62 - d, 3, 0.05, -0.8)[0]), 0.40, places=3)

    def test_ratings_adjust_for_opponents(self):
        from edge import tennis_hist as H
        # A and B each win 70% of serve points: A against a weak returner (W), B against a strong one (S).
        rows = []
        for i in range(30):
            rows.append({"tour": "ATP", "day": 1000 + i, "surface": "Hard", "indoor": 0, "w": "A", "l": "W", "w_hand": "R", "l_hand": "R",
                         "w_n": 80, "w_k": 56, "l_n": 80, "l_k": 40})
            rows.append({"tour": "ATP", "day": 1000 + i, "surface": "Hard", "indoor": 0, "w": "B", "l": "S", "w_hand": "R", "l_hand": "R",
                         "w_n": 80, "w_k": 56, "l_n": 80, "l_k": 52})
            rows.append({"tour": "ATP", "day": 1000 + i, "surface": "Hard", "indoor": 0, "w": "S", "l": "W", "w_hand": "R", "l_hand": "R",
                         "w_n": 80, "w_k": 60, "l_n": 80, "l_k": 40})
        obs = H.observations(rows, "ATP")
        R = H.Ratings(H=365, lam=400).fit(obs, 1100)
        i = obs["idx"]
        self.assertGreater(R.a[i["B"]], R.a[i["A"]])          # the same 70% against the better returner is worth more
        P = H.Ratings(H=365, lam=400, opponent=False).fit(obs, 1100)
        self.assertAlmostEqual(P.a[i["B"]], P.a[i["A"]], places=6)   # plain averages can't tell them apart

    def test_odds_parser_both_layouts(self):
        from edge import tennis_market as M
        res = ('<table class="result"><tr><td>Shanghai</td><td>S</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>H</td><td>A</td></tr>'
               '<tr><td>12:10</td><td><a href="/player/zverev-6f768/">Zverev A. (1)</a></td><td>2</td><td>6</td><td>6</td><td></td><td></td><td></td>'
               '<td>1.48</td><td>2.64</td><td></td><td>info</td></tr>'
               '<tr><td><a href="/player/de-minaur/">De Minaur A. (9)</a></td><td>0</td><td>4</td><td>4</td><td></td><td></td><td></td></tr></table>')
        x = M.parse(res, "2026-10-15", "ATP")[0]
        self.assertEqual((x["p1"], x["p2"], x["o1"], x["o2"]), ("Zverev A.", "De Minaur A.", 1.48, 2.64))
        up = ('<table class="result"><tr><td>Paris</td><td>S</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>H</td><td>A</td></tr>'
              '<tr><td>20:05Live streams</td><td><a href="/player/fritz-2b0f6/">Fritz T. (11)</a></td><td></td><td></td><td></td><td></td><td></td>'
              '<td>TV Sky</td><td>1-7</td><td>3.37</td><td>1.32</td></tr>'
              '<tr><td><a href="/player/alcaraz/">Alcaraz C. (2)</a></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>')
        y = M.parse(up, "2026-11-06", "ATP")[0]
        self.assertEqual((y["o1"], y["o2"]), (3.37, 1.32))
        self.assertAlmostEqual(M.fair(3.37, 1.32), (1 / 3.37) / (1 / 3.37 + 1 / 1.32))
        self.assertEqual(M.surname_key("Davidovich Fokina A."), "davidovichfokina")


if __name__ == "__main__":
    unittest.main()
