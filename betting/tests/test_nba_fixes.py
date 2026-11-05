import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge import learn as LN  # noqa: E402
from edge import nba_fit as F  # noqa: E402
from edge import nba_model as NM  # noqa: E402
from edge import nba_pp as N  # noqa: E402


class ShadowMode(unittest.TestCase):
    """New logic is scored in shadow and promoted only with evidence; promotions are logged and reversible."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.saved = (NM.PATH, NM.CHANGELOG, NM.SHADOW_DIR)
        NM.PATH, NM.CHANGELOG, NM.SHADOW_DIR = (os.path.join(self.tmp, "m.json"), os.path.join(self.tmp, "CL.md"), os.path.join(self.tmp, "sh"))

    def tearDown(self):
        NM.PATH, NM.CHANGELOG, NM.SHADOW_DIR = self.saved

    def test_promote_needs_evidence_then_rollback(self):
        NM.set_shadow({"entry": "se1"}, "v2 test")
        with self.assertRaises(SystemExit):           # no graded shadow legs yet
            NM.promote()
        cur = NM.promote(force="test only")
        self.assertEqual(cur["version"], 2)
        self.assertIn("FORCED", open(NM.CHANGELOG).read())
        self.assertEqual(NM.params("current")["entry"], "se1")
        back = NM.rollback()
        self.assertEqual(back["version"], 1)
        self.assertEqual(NM.params("current")["entry"], "flat2")
        self.assertIn("ROLLBACK", open(NM.CHANGELOG).read())

    def test_summarize_requires_both_criteria(self):
        legs = [{"day": f"2026-11-{1 + i % 14:02d}", "cur": {"p": 0.6, "conf": "Medium", "y": float(i % 2)},
                 "sh": {"p": 0.5, "conf": "Low", "y": float(i % 2)}} for i in range(220)]
        s = NM.summarize(legs)
        self.assertTrue(s["eligible"])
        self.assertTrue(s["shadow_wins"])              # 0.5 on a coin flip beats a 0.6 that hits half the time


class LearnDiscipline(unittest.TestCase):
    def test_holdout_weekday(self):
        self.assertTrue(LN.is_holdout({"date": "2026-11-04"}))      # a Wednesday
        self.assertFalse(LN.is_holdout({"date": "2026-11-05"}))

    def test_caps_skip_the_holdout(self):
        legs = [{"date": "2026-11-04", "segment": "nba:pts:over", "p_final": "0.65", "status": "lost", "miss_reason": "model bias"}
                for _ in range(6)]                                       # a Wednesday: never fitted on
        self.assertEqual(LN.find_caps(legs), {})
        thu = [{**r, "date": "2026-11-05"} for r in legs]
        self.assertIn("nba:pts:over", LN.find_caps(thu))

    def test_avoid_needs_50_legs_in_both_windows(self):
        def legs(n, start_hit, end_hit):
            out = []
            for i in range(n):
                hit = start_hit if i < n // 2 else end_hit
                out.append({"date": f"2026-10-{1 + i // 4:02d}", "segment": "nba:pts:over", "p_final": "0.65",
                            "status": "won" if (i % 10) < hit * 10 else "lost"})
            return out
        self.assertEqual(LN.find_avoid_segments(legs(40, 0.3, 0.3)), [])            # too few legs
        bad = [r for r in legs(80, 0.3, 0.3) if not LN.is_holdout(r)]
        self.assertEqual(LN.find_avoid_segments(bad), ["nba:pts:over"])
        one_window = [r for r in legs(80, 0.1, 0.75) if not LN.is_holdout(r)]
        self.assertEqual(LN.find_avoid_segments(one_window), [])                    # second half fine: not persistent


class PricingCorrectness(unittest.TestCase):
    hist = [int(1000 * np.exp(-0.5 * ((k - 20) / 6) ** 2)) for k in range(90)]

    def test_market_push_excluded_on_whole_lines(self):
        p, _ = N.market_sides(self.hist, 21.5, 0.5, 21.0)
        o, u, push = N.sides_at(self.hist, 21.0)
        self.assertGreater(push, 0)
        self.assertTrue(0.5 < p < 0.62)                 # a whole line just under the even line, push removed

    def test_verdict_rules(self):
        base = {"confidence": "High", "p_final": 0.66, "newcomer": False, "stat_key": "pts", "entry_rule": "se1", "se_p": 0.03}
        self.assertTrue(N.verdict({**base, "break_even": 0.577}).startswith("ENTRY"))
        self.assertIn("payout multiplier unknown", N.verdict({**base, "break_even": None}))
        self.assertIn("tilt", N.verdict({**base, "break_even": 0.577, "tilt_block": True, "tilt_raw": -0.4}))
        self.assertTrue(N.verdict({**base, "break_even": 0.577, "se_p": 0.10}).startswith("LEAN"))   # inside 1 SE
        self.assertTrue(N.verdict({**base, "confidence": "Medium", "break_even": 0.577}).startswith("LEAN"))

    def test_recompute_under_logic(self):
        logic = {**NM.V1, "blend": {"intercept": 0.0, "w_model": 0.2, "w_market": 0.8, "w_hist": 0.0}, "missing_market": "neutral",
                 "cap": 0.70, "gates": {"high": 0.62, "medium": 0.54, "max_spread_high": 0.16, "min_hist_n_high": 0, "no_market_min_hist_n": 99999}}
        p, c = N.recompute(0.80, None, None, 0, "nba:pts:over", logic)
        self.assertLess(p, 0.6)                          # no market: the model alone can't push it far
        self.assertNotEqual(c, "High")
        p2, c2 = N.recompute(0.75, 0.66, None, 0, "nba:pts:over", logic)
        self.assertGreater(p2, 0.66)
        self.assertEqual(c2, "High")


class Reasons(unittest.TestCase):
    """Every reason on a most-likely-game card must support the pick or be neutral."""

    def leg(self, **kw):
        pa = lambda per, lg, rank: {"per_game": per, "league_per_game": lg, "rank": rank, "all": 110.0, "league": 113.0}
        r = {"side": "over", "line": 9.5, "proj": 14, "q25": 10, "q75": 19, "p_market": None, "dk": None, "stat_key": "pra",
             "opp_espn": "TOR", "pos": "F", "ml": {"value": 12, "gap": 2.5},
             "research": {"season": [5, 1, 6], "season_avg": 15.0, "last5": [4, 1, 5], "last_games": [26, 7, 19, 10, 12],
                          "h2h": [0, 0, 0], "per36": 24.5, "h2h_per36": None},
             "pos_allows": {"pts": pa(38.1, 43.1, 25), "reb": pa(15.4, 18.9, 26), "ast": pa(5.9, 8.1, 29)},
             "usage": {"tonight": 0.07, "season": 0.067, "min_tonight": 22.0, "min_season": 22.0, "out": []}}
        r.update(kw)
        return r

    def verdicts(self, r):
        return {x["name"]: x["verdict"] for x in N.likely_reasons(r)}

    def test_tough_matchup_is_against_an_over(self):
        v = self.verdicts(self.leg())
        self.assertEqual(v["matchup"], "against")       # allows ~15% less than average to forwards
        self.assertEqual(v["this season"], "supports")
        self.assertEqual(v["head-to-head"], "neutral")  # no meetings: nothing to read

    def test_average_matchup_is_neutral_and_mixed_h2h_is_against(self):
        pa = {"pts": {"per_game": 43.0, "league_per_game": 43.1, "rank": 13, "all": 112.0, "league": 113.0}}
        r = self.leg(pos_allows=pa, research={**self.leg()["research"], "h2h": [2, 3, 5], "h2h_per36": 26.0})
        v = self.verdicts(r)
        self.assertEqual(v["matchup"], "neutral")
        self.assertEqual(v["head-to-head"], "against")  # 2 over / 3 under: the count leans under even with a higher per 36

    def test_market_and_usage_against(self):
        v = self.verdicts(self.leg(p_market=0.44, usage={"tonight": 0.07, "season": 0.07, "min_tonight": 18.0, "min_season": 22.0, "out": []}))
        self.assertEqual(v["DraftKings"], "against")
        self.assertEqual(v["usage"], "against")         # fewer minutes at the same usage: less volume for an over
        self.assertEqual(self.verdicts(self.leg(side="under", line=20.5, proj=16, ml={"value": 14, "gap": -6.5}))["matchup"], "supports")


class VerifyFreshness(unittest.TestCase):
    def test_latest_stamp_wins(self):
        from edge import verify as V
        n = "edge pp; pulled 2026-11-04T21:00Z | corrected by verify: 0.76 Medium -> 0.75 Medium; fresh 2026-11-05 00:04Z: simulation re-run"
        self.assertEqual(V.last_priced(n).strftime("%Y-%m-%d %H:%M"), "2026-11-05 00:04")
        self.assertEqual(V.last_priced("edge pp; pulled 2026-11-04T21:00Z").strftime("%H:%M"), "21:00")
        self.assertIsNone(V.last_priced("no stamp"))


class SideNumbers(unittest.TestCase):
    """A re-sided leg (history and most-likely lists) is priced by the same recompute verify runs."""

    def test_v2_ignores_history_and_neutral_market(self):
        logic = {**NM.V1, "blend": {"intercept": 0.0, "w_model": 0.2, "w_market": 0.8, "w_hist": 0.0}, "history": "off",
                 "missing_market": "neutral", "cap": 0.70, "gates": {"high": 0.62, "medium": 0.54, "max_spread_high": 0.16,
                 "min_hist_n_high": 0, "no_market_min_hist_n": 99999}}
        r = {"side": "over", "p_model": 0.60, "p_market": None, "stat_key": "reb", "research": {"season": [6, 1, 7]}}
        x = N.side_numbers(r, "over", logic)
        self.assertIsNone(x["p_hist"]); self.assertEqual(x["hist_n"], 0)
        self.assertEqual((x["p_final"], x["confidence"]), N.recompute(0.60, None, None, 0, "nba:reb:over", logic))
        y = N.side_numbers(r, "under", logic)
        self.assertAlmostEqual(y["p_model"], 0.40)


class NflAnchoring(unittest.TestCase):
    def test_count_tilt_keeps_pushes(self):
        from edge import nfl_pp
        rng = np.random.default_rng(1)
        arr = rng.poisson(1.9, 200000).astype(float)
        self.assertAlmostEqual(nfl_pp.anchored_count(arr, 2.5, 2.5), 0.5, places=2)       # DK's line is the median
        o = nfl_pp.anchored_count(arr, 2.5, 2.0)                                          # over 2.0: 3+ wins, 2 pushes
        k = np.arange(0, 15)
        self.assertTrue(0.5 < o < 0.75)
        self.assertLess(nfl_pp.anchored_count(arr, 1.5, 2.0), 0.5)                         # DK at 1.5: 3+ is less likely than not


class MinutesGap(unittest.TestCase):
    def test_l28(self):
        from edge import verify as V
        self.assertIn("needs minutes", V.minutes_gap("over", 25.2, [20, 18, 22, 19, 21]))        # Keldon Johnson, Nov 4
        self.assertIn("fewer minutes", V.minutes_gap("under", 25.0, [33, 31, 34, 30]))           # Derrick White, Nov 4
        self.assertIsNone(V.minutes_gap("over", 22.0, [20, 21, 23]))
        self.assertIsNone(V.minutes_gap("over", 30.0, [20, 20]))                                  # too few games


class FitPieces(unittest.TestCase):
    def test_bias_table_shrinks_small_segments(self):
        legs = [{"stat": "pts", "seg": ("pts", "top5"), "m_raw": 0.40, "q": 0.50} for _ in range(400)] + \
               [{"stat": "pts", "seg": ("pts", "bench"), "m_raw": 0.60, "q": 0.50} for _ in range(10)]
        b = F.fit_bias(legs)
        self.assertLess(b[("pts", "top5")], 0)
        self.assertLess(b[("pts", "bench")], F.lg(0.60) - F.lg(0.5))   # pulled toward the stat-wide value

    def test_selected_side(self):
        s = F.selected([{"x": 0.3, "y": 0.0, "day": "d"}], "x")[0]
        self.assertEqual(s["side"], "under")
        self.assertAlmostEqual(s["p_sel"], 0.7)
        self.assertEqual(s["y_sel"], 1.0)


if __name__ == "__main__":
    unittest.main()


class LineShop(unittest.TestCase):
    def test_implied_and_shift(self):
        from edge import shop
        q = shop.implied_over(1.91, 2.10)
        self.assertAlmostEqual(q, 0.5237, places=3)
        self.assertAlmostEqual(shop.prob_at(q, 19.5, 19.5, ("points",)), q, places=3)          # same line: Dabble's own number
        self.assertGreater(shop.prob_at(q, 19.5, 17.5, ("points",)), q)                        # a lower line helps the over
        self.assertLess(shop.prob_at(q, 19.5, 21.5, ("points",)), q)

    def test_small_counts_use_poisson_with_push(self):
        from edge import shop
        q = shop.implied_over(1.46, 3.18)                     # Herbert 0.5+ pass TDs at ~68.5%
        under_1 = 1 - shop.prob_at(q, 0.5, 1.0, ("passing-touchdowns",))
        self.assertTrue(0.40 < under_1 < 0.55)               # wins only on 0 TDs, pushes on 1
