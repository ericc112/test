import os
import random
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge import cs2, grade, learn, lol, pp, review, soccer, verify  # noqa: E402
from edge.blend import DEFAULT_ADJ, final_probability  # noqa: E402
from edge.odds import devig, fair_american, kelly_fraction, stake  # noqa: E402
from edge.pickem import PAYOUTS, Leg, best_entries, breakeven, entry_summary, squad_ride  # noqa: E402


class Odds(unittest.TestCase):
    def test_devig_sums_to_one_and_orders(self):
        o, u = devig(-130, 102)
        self.assertAlmostEqual(o + u, 1, places=9)
        self.assertAlmostEqual(o, 0.533, places=3)
        po, pu = devig(-130, 102, "power")
        self.assertAlmostEqual(po + pu, 1, places=6)

    def test_fair_and_kelly(self):
        self.assertEqual(fair_american(0.5), -100)
        self.assertEqual(fair_american(0.25), 300)
        self.assertEqual(kelly_fraction(0.4, 100), 0.0)
        self.assertAlmostEqual(kelly_fraction(0.502, 102), 0.0138, places=3)
        self.assertEqual(stake(0.9, 100, 1000), 20.0)  # capped at 2%


class Pickem(unittest.TestCase):
    def test_breakevens_match_known_values(self):
        self.assertAlmostEqual(breakeven(PAYOUTS["pp_power_2"]), 0.577, places=3)
        self.assertAlmostEqual(breakeven(PAYOUTS["pp_flex_6"]), 0.542, places=2)
        self.assertAlmostEqual(breakeven(PAYOUTS["boom_pickem_2"]), 0.559, places=3)

    def test_positive_correlation_raises_joint_hit(self):
        ind = entry_summary([0.6, 0.6], PAYOUTS["pp_power_2"])["p_all"]
        cor = entry_summary([0.6, 0.6], PAYOUTS["pp_power_2"], np.array([[1, 0.4], [0.4, 1]]))["p_all"]
        self.assertAlmostEqual(ind, 0.36, delta=0.01)
        self.assertGreater(cor, ind + 0.03)

    def test_best_entries_respects_min_teams(self):
        legs = [Leg("a", 0.7, team="X"), Leg("b", 0.68, team="X"), Leg("c", 0.6, team="Y")]
        top = best_entries(legs, 2, PAYOUTS["pp_power_2"], min_teams=2)
        self.assertTrue(all(set(e["legs"]) != {"a", "b"} for e in top))

    def test_squad_ride_monotone(self):
        r = squad_ride([245, 283, 207], [70, 78, 65], (807, 977, 1044))
        self.assertTrue(r["p_m1"] > r["p_m2"] > r["p_m3"] > 0)
        self.assertAlmostEqual(r["p_m1"], 0.26, delta=0.04)


class Blend(unittest.TestCase):
    def test_rating_keeps_the_gates(self):
        """1-10 score: the label sets the band, so a big number that misses a gate can't score like a High."""
        from edge.blend import rating
        self.assertEqual([rating(p, "High", 0.85, floor=0.80) for p in (0.80, 0.85, 0.90)], [8, 9, 10])
        self.assertEqual(rating(0.79, "High", 0.85, floor=0.80), 7)     # under the 80% floor
        self.assertEqual(rating(0.88, "High", None, floor_no_market=0.80), 9)   # no book price: held to its own floor, not capped
        self.assertEqual(rating(0.88, "High", None, floor_no_market=0.89), 7)   # ... which learn raises on unpriced results
        self.assertEqual(rating(0.86, "High", 0.70, floor=0.80), 7)     # the market itself under 75%
        self.assertEqual([rating(p, "Medium") for p in (0.58, 0.63, 0.90)], [5, 6, 7])     # 90% that failed a gate is a 7 at most
        self.assertEqual([rating(p, "Low") for p in (0.45, 0.52, 0.56, 0.95)], [1, 2, 3, 4])
        self.assertEqual(rating(0.9, "Avoid"), 1)
        thin = final_probability(0.80, None, 0.85, "cs2:cs_kills_m12:under", hist_n=8, adj=DEFAULT_ADJ)  # no market, thin history
        self.assertLessEqual(thin.rating, 7)

    def test_missing_components_and_agreement(self):
        e = final_probability(0.71, 0.66, 0.74, "mlb:pitcher_outs:over", hist_n=20, adj=DEFAULT_ADJ)
        self.assertTrue(0.65 < e.p < 0.75)
        self.assertTrue(e.agreement)
        self.assertEqual(e.confidence, "High")
        d = final_probability(0.6, 0.45, None, "x:y:z", adj=DEFAULT_ADJ)
        self.assertFalse(d.agreement)
        self.assertEqual(d.confidence, "Low")
        s = final_probability(0.7, None, None, "x:y:z", adj=DEFAULT_ADJ)
        self.assertEqual(s.confidence, "Low")  # single source

    def test_avoid_list(self):
        adj = {**DEFAULT_ADJ, "avoid_segments": ["nhl:skater_sog"]}
        self.assertEqual(final_probability(0.7, 0.65, None, "nhl:skater_sog:over", adj=adj).confidence, "Avoid")


def _synthetic(n, seed=1):
    """Market is informative, model is noise -> learning should shift weight from model to market."""
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        true = rng.uniform(0.35, 0.75)
        market = min(max(true + rng.gauss(0, 0.03), 0.05), 0.95)
        model = min(max(rng.uniform(0.35, 0.75), 0.05), 0.95)
        y = rng.random() < true
        seg = "mlb:pitcher_outs:over" if i % 2 else "nhl:skater_sog:under"
        if seg == "nhl:skater_sog:under" and rng.random() < 0.25:
            y = False  # this segment underperforms
        p = final_probability(model, market, None, seg, adj=DEFAULT_ADJ).p
        rows.append({"id": str(i), "segment": seg, "p_model": model, "p_market": market, "p_hist": "", "hist_n": 0,
                     "p_final": p, "status": "won" if y else "lost", "player": "p", "market": "m", "side": "over",
                     "line": 1, "result_value": 0, "price": -110, "stake": 1, "entry_id": "", "closing_price": "", "miss_reason": ""})
    return rows


class Learning(unittest.TestCase):
    def test_fit_shifts_weight_to_informative_source(self):
        rows = _synthetic(600)
        fit = learn.fit_blend(rows, {**DEFAULT_ADJ})
        self.assertGreater(fit["w_market"], DEFAULT_ADJ["blend"]["w_market"])
        self.assertLess(fit["w_model"], DEFAULT_ADJ["blend"]["w_model"])

    def test_small_sample_keeps_prior(self):
        self.assertEqual(learn.fit_blend(_synthetic(5), {**DEFAULT_ADJ})["w_model"], DEFAULT_ADJ["blend"]["w_model"])

    def test_one_game_script_counts_once(self):
        leg = lambda i, ev: {"id": str(i), "segment": "lol:kills_m123:under", "event_id": ev, "status": "lost",
                             "p_model": "0.66", "p_hist": "0.66", "hist_n": "20"}
        same = [leg(i, "S1") for i in range(7)]                    # seven unders on one series
        self.assertEqual(learn.learn_segment_bias(same, {**DEFAULT_ADJ}), {})
        apart = [leg(i, f"S{i}") for i in range(7)]                # seven series
        self.assertLess(learn.learn_segment_bias(apart, {**DEFAULT_ADJ})["lol:kills_m123:under"], 0)

    def test_segment_bias_and_avoid(self):
        rows = _synthetic(600)
        bias = learn.learn_segment_bias(rows, {**DEFAULT_ADJ})
        self.assertLess(bias["nhl:skater_sog:under"], -0.1)
        self.assertIn("nhl:skater_sog:under", learn.find_avoid_segments(rows))

    def test_update_writes_adjustments_and_lessons(self):
        with tempfile.TemporaryDirectory() as d:
            adj_p, les_p = os.path.join(d, "adj.json"), os.path.join(d, "L.md")
            out = learn.update(_synthetic(600), adj_p, les_p, today="2026-10-13")
            self.assertTrue(os.path.exists(adj_p))
            self.assertTrue(out["lessons_added"])
            with open(les_p) as f:
                self.assertIn("Auto-learned 2026-10-13", f.read())
            again = learn.update(_synthetic(600), adj_p, les_p, today="2026-10-14")
            self.assertEqual(again["adjustments"]["blend"], out["adjustments"]["blend"])  # refit from prior, no double counting

    def test_report_runs(self):
        txt = learn.report(_synthetic(80))
        self.assertIn("Calibration", txt)

    def test_calibration_pulls_overconfident_model_only_picks_down(self):
        from edge.blend import DEFAULT_ADJ, final_probability
        rows = [{"id": str(i), "status": "won" if i % 10 < 6 else "lost", "p_model": "0.80", "p_market": "", "p_hist": "",
                 "hist_n": "0", "segment": f"s{i % 7}:m:over", "event_id": str(i)} for i in range(200)]   # "80%" hitting 60%
        cal = learn.fit_calibration(rows, dict(DEFAULT_ADJ))
        self.assertIn("no_market", cal)
        adj = {**DEFAULT_ADJ, "calibration": cal}
        self.assertLess(final_probability(0.80, None, None, "x:y:over", 0, adj).p, 0.75)
        self.assertNotIn("market", cal)                    # no priced rows: priced picks stay uncalibrated

    def test_rating_floor_tightens_until_tier_hits_80(self):
        rows = [{"id": str(i), "status": "won" if i % 10 < 7 else "lost", "p_final": "0.85", "p_market": "0.86",
                 "confidence": "High", "segment": "x:y:over"} for i in range(30)]     # 70% < 80%
        fl, _ = learn.tune_rating_floor(rows, {"rating_floor": 0.80})
        self.assertGreater(fl, 0.80)
        fl, _ = learn.tune_rating_floor(rows[:10], {"rating_floor": 0.80})          # too few to move it
        self.assertEqual(fl, 0.80)

    def test_report_has_rating_scorecard(self):
        self.assertIn("Scorecard by rating", learn.report(_synthetic(80)))

    def test_report_skips_unpriced_rows(self):
        rows = _synthetic(80)
        rows.append({**rows[0], "id": "999", "p_final": "", "status": "won"})   # a user's leg nobody priced
        self.assertIn("Calibration", learn.report(rows))


class HitRateDiscipline(unittest.TestCase):
    def test_no_market_needs_deep_history_for_high(self):
        thin = final_probability(0.72, None, 0.75, "lol:kills_m123:under", hist_n=12, adj=DEFAULT_ADJ)
        deep = final_probability(0.72, None, 0.74, "lol:kills_m123:under", hist_n=40, adj=DEFAULT_ADJ)
        self.assertNotEqual(thin.confidence, "High")
        self.assertEqual(deep.confidence, "High")

    def test_postseason_history_shrink(self):
        adj = {**DEFAULT_ADJ, "hist_weight_scale": {"mlb:pitcher_outs": 0.5}}
        full = final_probability(None, 0.63, 0.90, "mlb:pitcher_outs:over", hist_n=29, adj=DEFAULT_ADJ)
        half = final_probability(None, 0.63, 0.90, "mlb:pitcher_outs:over", hist_n=29, adj=adj)
        self.assertLess(half.p, full.p)

    def test_best_legs_one_per_script(self):
        from edge import card
        base = {"status": "pending", "date": "d", "p_market": 0.68, "hist_n": 30, "segment": "x:y:over", "sport": "mlb"}
        rows = [{**base, "player": "A", "event_id": "1", "p_model": 0.75, "p_hist": 0.74},
                {**base, "player": "B", "event_id": "1", "p_model": 0.73, "p_hist": 0.72},
                {**base, "player": "C", "event_id": "2", "p_model": 0.74, "p_hist": 0.73}]
        legs = card.best_legs(rows, min_p=0.6)
        self.assertEqual(sorted(r["player"] for r in legs), ["A", "C"])
        self.assertAlmostEqual(card.best_entry(legs, 2)["p_all"], legs[0]["p_now"] * legs[1]["p_now"], delta=0.01)


def _loss(i, event, pid, market, side, line, result, **kw):
    return {"id": str(i), "date": "d", "sport": "mlb", "event_id": event, "player": f"p{pid}", "player_id": str(pid),
            "market": market, "side": side, "line": str(line), "result_value": str(result), "status": "lost",
            "p_final": "0.6", "action": "lean", "group": "", "segment": f"mlb:{market}:{side}", **kw}


class LossReview(unittest.TestCase):
    """Every loss gets a post-mortem; legs that rode one script point to a single root cause."""
    def setUp(self):
        self.rows = [
            _loss(1, "9", 100, "pitcher_outs", "over", 17.5, 8, p_market="0.63", p_hist="0.9"),
            _loss(2, "9", 100, "pitcher_pitches", "over", 93.5, 75, p_model="0.6"),
            _loss(3, "9", 200, "batter_hrr", "under", 1.5, 4),
            _loss(4, "9", 300, "batter_hrr", "under", 1.5, 5),
            _loss(5, "7", 400, "pitcher_walks", "under", 1.5, 2, p_model="0.6", p_market="0.54"),
            _loss(6, "8", 500, "pitcher_strikeouts", "under", 5.5, 7, p_model="0.6", p_market="0.45"),
        ]
        pit = {"role": "pitcher", "outs": 8, "bf": 14, "pitches": 75, "p_per_pa": 5.4}
        self.details = {"1": {**pit, "opportunity": 8}, "2": {**pit, "opportunity": 14},
                        "3": {"role": "batter", "pa": 5, "opp_starter_id": 100, "opp_starter_outs": 8, "opp_starter_er": 3, "hrr_total": 4, "hrr_vs_starter": 3},
                        "4": {"role": "batter", "pa": 4, "opp_starter_id": 100, "opp_starter_outs": 8, "opp_starter_er": 3, "hrr_total": 5, "hrr_vs_starter": 2},
                        "5": {"role": "pitcher", "outs": 12, "bf": 18, "pitches": 64}, "6": {"role": "pitcher", "outs": 18}}

    def test_every_loss_reviewed_and_script_linked(self):
        pms = {p["id"]: p for p in review.review(self.rows, details=self.details, fetch=False)}
        self.assertEqual(set(pms), {"1", "2", "3", "4", "5", "6"})
        self.assertEqual(pms["1"]["auto_tag"], "opportunity")       # starter pulled early: the root leg
        self.assertEqual(pms["2"]["auto_tag"], "correlated")        # his pitches over rode the same script
        self.assertEqual(pms["3"]["auto_tag"], "correlated")        # hitter under lost on damage off that starter
        self.assertEqual(pms["4"]["auto_tag"], "variance")          # bullpen damage alone beat the line
        self.assertTrue(pms["5"]["near_miss"])
        self.assertEqual(pms["6"]["auto_tag"], "model bias")        # sided with the model against the market

    def test_caps_and_rule_flags(self):
        rows = [dict(r, miss_reason="opportunity", segment="mlb:pitcher_outs:over", p_final="0.66") for r in self.rows[:4]]
        rows.append(dict(self.rows[0], id="9", status="won", segment="mlb:pitcher_outs:over", p_final="0.66"))
        caps = learn.find_caps(rows)
        self.assertIn("mlb:pitcher_outs:over", caps)
        adj = {**DEFAULT_ADJ, "cap_medium_segments": caps}
        e = final_probability(0.71, 0.66, 0.74, "mlb:pitcher_outs:over", hist_n=20, adj=adj)
        self.assertEqual(e.confidence, "Medium")
        with tempfile.TemporaryDirectory() as d:
            a, l = os.path.join(d, "a.json"), os.path.join(d, "L.md")
            first = learn.update(rows, a, l, today="x")
            self.assertTrue(any("share the cause" in n for n in first["lessons_added"]))
            again = learn.update(rows, a, l, today="y")
            self.assertFalse(any("share the cause" in n for n in again["lessons_added"]))  # flagged once

    def test_l19_no_high_without_market_when_model_known_off(self):
        adj = {**DEFAULT_ADJ, "model_bias_logit": {"mlb:batter_hrr:under": -0.31}}
        e = final_probability(0.76, None, 0.647, "mlb:batter_hrr:under", hist_n=116, adj=adj)
        self.assertEqual(e.confidence, "Medium")
        ok = final_probability(0.72, None, 0.73, "lol:kills_m123:under", hist_n=40, adj=DEFAULT_ADJ)
        self.assertEqual(ok.confidence, "High")  # no correction needed in that market: rule doesn't fire


class SoccerPasses(unittest.TestCase):
    def test_possession_stats_market_blend(self):
        self.assertAlmostEqual(soccer.log5(0.6, 0.6), 0.5)          # two 60% teams split the ball
        self.assertGreater(soccer.log5(0.6, 0.4), 0.6)
        even = soccer.possession(0.5, 0.5, home=None, wdl=(0.35, 0.3, 0.35))
        self.assertAlmostEqual(even["possession"], 0.5, places=3)
        fav = soccer.possession(0.5, 0.5, home=None, wdl=(0.7, 0.2, 0.1))
        self.assertAlmostEqual(fav["market"], 0.5 + 0.21 * 0.6, places=3)   # market says the favourite has the ball
        self.assertGreater(fav["possession"], 0.55)
        cross = soccer.possession(0.51, 0.62, home=None, same_league=False)
        self.assertGreater(cross["possession"], cross["stats"])    # no market: cross-league gap shrunk

    def test_projection_press_and_script(self):
        base = soccer.project(0.5, 9.0, 0.11, [90.0], line=49.5)
        self.assertAlmostEqual(base["mean"], 0.5 * 100 * 9.0 * 0.11, delta=1.0)
        pressed = soccer.project(0.5, 9.0 * 0.85, 0.11, [90.0], line=49.5)   # a pressing opponent cuts passes
        self.assertLess(pressed["p_over"], base["p_over"] - 0.1)
        fav = soccer.project(0.5, 9.0, 0.11, [90.0], wdl=(0.8, 0.15, 0.05), line=49.5)
        self.assertLess(fav["mean"], base["mean"])                            # expected to lead -> cedes some ball
        subbed = soccer.project(0.5, 9.0, 0.11, [60.0], line=49.5)
        self.assertLess(subbed["p_over"], 0.2)

    def test_soccer_grader(self):
        orig_get, orig_stats = grade._get, grade.soccer_player_stats
        grade._get = lambda url: {"header": {"league": {"slug": "fra.1"}, "competitions": [{"status": {"type": {"completed": True}}}]},
                                  "rosters": [{"team": {"id": "175"}, "roster": [{"athlete": {"id": "9"}, "starter": True},
                                                                               {"athlete": {"id": "8"}, "starter": False}]}]}
        grade.soccer_player_stats = lambda *a: {"accuratePasses": 50, "inaccuratePasses": 4, "saves": 3}
        try:
            self.assertEqual(grade.soccer_value("1", "9", "passes_att", {}), ("final", 54))
            self.assertEqual(grade.soccer_value("1", "8", "passes_att", {}), ("void", None))   # unused sub: voided
        finally:
            grade._get, grade.soccer_player_stats = orig_get, orig_stats


def _maps(nick, team, games, win, kills, hs, rounds=21, date="2026-09-01"):
    return [{"date": date, "match": g // 2, "bo": 3, "game": g, "num": 1 + g % 2, "rounds": rounds, "team_id": team,
             "nick": nick, "kills": kills, "hs": hs, "win": win} for g in games]


class SoccerFeedIntegrity(unittest.TestCase):
    def test_empty_stats_split_is_missing_not_zero(self):
        m = {"date": "2026-10-10", "league": "eng.1", "event_id": "1", "passes": 500.0,
             "summary": {"rosters": [{"team": {"id": "7"}, "roster": [{"athlete": {"id": "9"}, "starter": True}]}]}}
        orig = soccer.soccer_player_stats
        try:
            soccer.soccer_player_stats = lambda *a: {}
            self.assertIsNone(soccer.player_match(m, "7", "9"))            # feed hiccup: skip the match
            soccer.soccer_player_stats = lambda *a: {"minutes": 90, "accuratePasses": 40, "inaccuratePasses": 5}
            self.assertEqual(soccer.player_match(m, "7", "9")["passes"], 45)
        finally:
            soccer.soccer_player_stats = orig


class KeeperPasses(unittest.TestCase):
    def test_keeper_priced_from_same_competition(self):
        cup = [{"starter": True, "minutes": 90, "passes": v, "league": "uefa.champions", "position": "G"} for v in (35, 40, 38, 42, 36)]
        dom = [{"starter": True, "minutes": 90, "passes": v, "league": "nor.1", "position": "G"} for v in (20, 22, 19, 24, 21, 23)]
        it = iter(cup + dom)
        orig = soccer.team_matches, soccer.player_match, soccer.summary
        try:
            soccer.team_matches = lambda team, n=10: list(range(11))
            soccer.player_match = lambda m, t, p: next(it)
            soccer.summary = lambda eid: {"header": {"league": {"slug": "uefa.champions"}}}
            m = soccer.keeper_passes("1", "2", {"home": True, "opp_id": "3", "wdl": None, "opp_name": None}, "9", 27.5)
        finally:
            soccer.team_matches, soccer.player_match, soccer.summary = orig
        self.assertEqual(m["sample"], "European cup")
        self.assertGreater(m["p_over"], 0.85)       # his cup rate, not his domestic one
        self.assertEqual(m["hist_n"], 5)


class SoccerBackCheck(unittest.TestCase):
    """L26: the back-check fails a keeper priced the outfield way, and recounts history in tonight's competition."""
    def _run(self, notes, p_hist):
        cup = [{"starter": True, "minutes": 90, "passes": v, "league": "uefa.champions", "position": "G"} for v in (35, 40, 38, 42, 36, 30)]
        dom = [{"starter": True, "minutes": 90, "passes": v, "league": "nor.1", "position": "G"} for v in (20, 22, 19, 24, 21, 23)]
        it = iter(cup + dom)
        summ = {"header": {"league": {"slug": "uefa.champions"}, "competitions": [{"competitors": []}]},
                "rosters": [{"team": {"id": "2"}, "roster": [{"athlete": {"id": "1"}, "position": {"abbreviation": "G"}}]}]}
        orig = soccer.summary, soccer.team_matches, soccer.player_match
        try:
            soccer.summary = lambda eid: summ
            soccer.team_matches = lambda team, n=10: list(range(12))
            soccer.player_match = lambda m, t, p: next(it)
            rep = verify.Report({"id": "9", "sport": "soccer", "market": "passes_att", "event_id": "5", "player_id": "1", "player": "K",
                                 "line": "27.5", "side": "over", "p_hist": str(p_hist), "notes": notes})
            verify.check_soccer(rep)
        finally:
            soccer.summary, soccer.team_matches, soccer.player_match = orig
        return {(name, st) for st, name, _ in rep.checks}

    def test_outfield_priced_keeper_fails(self):
        got = self._run("median 21, possession 52%", 0.154)        # how Haikin was first priced
        self.assertIn(("rule L26", "FAIL"), got)
        self.assertIn(("recount", "FAIL"), got)                     # cup history 6/6 over vs logged 15%

    def test_possession_regime_recount(self):
        """L27: a centre-back's history at 70% possession says nothing about a 48% night."""
        big = [{"starter": True, "minutes": 90, "passes": v, "league": "eng.1", "position": "CD-R", "poss": 0.72} for v in (110, 120, 105, 98, 115, 102)]
        tight = [{"starter": True, "minutes": 90, "passes": v, "league": "eng.1", "position": "CD-R", "poss": 0.48} for v in (45, 50, 38, 61, 47, 52)]
        it = iter(big + tight)
        summ = {"header": {"league": {"slug": "eng.1"}, "competitions": [{"competitors": []}]},
                "rosters": [{"team": {"id": "2"}, "roster": [{"athlete": {"id": "1"}, "position": {"abbreviation": "CD-R"}}]}]}
        orig = soccer.summary, soccer.team_matches, soccer.player_match
        try:
            soccer.summary = lambda eid: summ
            soccer.team_matches = lambda team, n=10: list(range(12))
            soccer.player_match = lambda m, t, p: next(it)
            rep = verify.Report({"id": "9", "sport": "soccer", "market": "passes_att", "event_id": "5", "player_id": "1", "player": "D",
                                 "line": "62.5", "side": "under", "p_hist": "0.5", "notes": "median 65, possession 48%"})
            verify.check_soccer(rep)
        finally:
            soccer.summary, soccer.team_matches, soccer.player_match = orig
        self.assertIn(("rule L27", "FAIL"), {(name, st) for st, name, _ in rep.checks})   # 6/6 under at 48% vs logged 50%

    def test_bench_player_over_fails(self):
        """L29: an over on a player named on the bench is withdrawn; before the XI is out it is a WARN."""
        def run(roster):
            summ = {"header": {"league": {"slug": "uefa.champions"}, "competitions": [{"competitors": []}]}, "rosters": roster}
            rep = verify.Report({"id": "9", "sport": "soccer", "market": "shots", "event_id": "5", "player_id": "1", "side": "over"})
            orig = soccer.summary
            try:
                soccer.summary = lambda eid: summ
                verify.check_soccer(rep)
            finally:
                soccer.summary = orig
            return {(name, st) for st, name, _ in rep.checks}
        xi = lambda me: [{"team": {"id": "2"}, "roster": [{"athlete": {"id": "7"}, "starter": True}, {"athlete": {"id": "1"}, "starter": me}]}]
        self.assertIn(("lineup", "FAIL"), run(xi(False)))
        self.assertIn(("lineup", "PASS"), run(xi(True)))
        self.assertIn(("lineup", "WARN"), run([]))

    def test_keeper_model_passes(self):
        got = self._run("KEEPER: priced from his own European cup starts", 1.0)
        self.assertNotIn(("rule L26", "FAIL"), got)
        self.assertIn(("recount", "PASS"), got)


class CS2Model(unittest.TestCase):
    def test_names_and_series_inversion(self):
        self.assertTrue(cs2.same_name("dev1ce", "device"))
        self.assertTrue(cs2.same_name("EliGE", "EliGe"))
        self.assertFalse(cs2.same_name("JT", "NAF"))
        self.assertAlmostEqual(cs2.map_p_from_series(0.5), 0.5, places=4)
        p = cs2.map_p_from_series(0.683)
        self.assertAlmostEqual(p * p * (3 - 2 * p), 0.683, places=4)

    def test_current_era_keeps_four_of_five(self):
        five = ["a", "b", "c", "d", "e"]
        rows = []
        for n in five:
            rows += _maps(n, 1, [10, 11], True, 20, 10, date="2026-10-01")          # today's roster
        for n in ["a", "b", "c", "d", "x"]:
            rows += _maps(n, 1, [8, 9], True, 20, 10, date="2026-09-20")           # stand-in game: 4 of 5
        for n in ["a", "b", "c", "y", "z"]:
            rows += _maps(n, 1, [6, 7], True, 20, 10, date="2026-08-01")           # old roster: 3 of 5
        got, era = cs2.current_era(rows, 1)
        self.assertEqual(got, set(five))
        self.assertEqual({r["game"] for r in era}, {8, 9, 10, 11})

    def test_map_winner_effect(self):
        me = _maps("p", 1, range(0, 20), True, 22, 11) + _maps("p", 1, range(20, 40), False, 13, 6)
        rw, rl = np.array([21]), np.array([21])
        fav = cs2.price(me, me, 0.8, rw, rl, "kills", 30.5)
        dog = cs2.price(me, me, 0.2, rw, rl, "kills", 30.5)
        self.assertGreater(fav["mean"], dog["mean"] + 8)
        self.assertGreater(fav["p_over"], dog["p_over"])


class PrizePicksBoard(unittest.TestCase):
    FIXTURE = {"data": [
        {"attributes": {"description": "BBL MAPS 1-2", "stat_type": "MAPS 1-2 Kills", "line_score": 32, "odds_type": "standard",
                        "allowed_wager_types": "over", "start_time": "2026-10-13T06:00:00-04:00"},
         "relationships": {"new_player": {"data": {"id": "1"}}, "game": {"data": {"id": "g"}}}},
        {"attributes": {"description": "BBL MAPS 1-2", "stat_type": "MAPS 1-2 Kills", "line_score": 40.5, "odds_type": "demon",
                        "start_time": "2026-10-13T06:00:00-04:00"},
         "relationships": {"new_player": {"data": {"id": "1"}}, "game": {"data": {"id": "g"}}}}],
        "included": [{"type": "new_player", "id": "1", "attributes": {"display_name": "malbsMd", "team": "Liquid"}},
                     {"type": "game", "id": "g", "attributes": {"metadata": {"game_info": {"teams": {"home": {"abbreviation": "Liquid"}, "away": {"abbreviation": "BBL"}}}}}}]}

    def test_board_parsing(self):
        orig_get, orig_leagues = pp.pp_get, pp.leagues
        pp.pp_get, pp.leagues = (lambda url, max_age=120: self.FIXTURE), (lambda: {"CS2": "265"})
        try:
            std = pp.board("CS2")
            both = pp.board("CS2", ("standard", "demon"))
        finally:
            pp.pp_get, pp.leagues = orig_get, orig_leagues
        self.assertEqual(len(std), 1)
        self.assertEqual(len(both), 2)
        self.assertEqual(std[0]["opp"], "BBL")
        self.assertFalse(std[0]["over_only"])          # the feed says "over" but the app shows Less on standard lines
        self.assertTrue(std[0]["feed_over_only"])
        self.assertTrue(both[1]["over_only"])          # demons are always over-only

    def test_ladder_fit_and_over_only_side(self):
        import math
        sf = lambda lam, k: 1 - sum(math.exp(-lam) * lam ** j / math.factorial(j) for j in range(k))
        to_am = lambda p: -100 * p / (1 - p) if p >= 0.5 else 100 * (1 - p) / p
        ladder = {k: to_am(min(sf(2.0, k) / pp.MILESTONE_HOLD, 0.99)) for k in (1, 2, 3, 4)}
        self.assertAlmostEqual(pp.ladder_lambda(ladder), 2.0, delta=0.1)
        o, u, push = pp.poisson_sides(2.0, 2)
        self.assertAlmostEqual(push, 2 * math.exp(-2), places=6)
        self.assertAlmostEqual(o + u + push, 1, places=6)
        leg = {"over_only": True}
        row = pp._finish(leg, "cs_kills_m12", "cs2", 0.3, 0.7, 0.0, 2, 8)
        self.assertEqual(row["side"], "over")          # can't take the under even though it's likelier


class PrePublishVerify(unittest.TestCase):
    """Every pick is back-checked before it is published; these are the offline checks."""
    def _row(self, **kw):
        e = final_probability(0.72, 0.68, None, "nhl:skater_sog:under", 0, DEFAULT_ADJ)
        base = {"id": "1", "date": "2026-10-13", "sport": "nhl", "event_id": "9", "player": "P", "market": "skater_sog", "line": "2.5",
                "side": "under", "p_model": "0.72", "p_market": "0.68", "p_hist": "", "hist_n": "0", "p_final": str(e.p),
                "confidence": e.confidence, "action": "lean", "segment": "nhl:skater_sog:under", "group": "g", "status": "pending", "notes": ""}
        return {**base, **kw}

    def test_consistent_pick_passes_offline(self):
        r = self._row()
        rep = verify.verify(r, [r], DEFAULT_ADJ, fetch=False)
        self.assertNotEqual(rep.verdict, "NOT VERIFIED")

    def test_mistyped_number_fails(self):
        r = self._row(p_final="0.78")          # the 0.78-vs-0.728 kind of slip
        self.assertEqual(verify.verify(r, [r], DEFAULT_ADJ, fetch=False).verdict, "NOT VERIFIED")

    def test_rules_block(self):
        new = self._row(notes="NEW TO TEAM: priced from previous team")
        self.assertEqual(verify.verify(new, [new], DEFAULT_ADJ, fetch=False).verdict, "NOT VERIFIED")      # L5
        e = final_probability(0.7, 0.66, None, "mlb:pitcher_outs:over", 0, DEFAULT_ADJ)
        outs = self._row(sport="mlb", market="pitcher_outs", side="over", segment="mlb:pitcher_outs:over",
                         p_model="0.7", p_market="0.66", p_final=str(e.p), confidence=e.confidence)
        self.assertEqual(verify.verify(outs, [outs], DEFAULT_ADJ, fetch=False).verdict, "NOT VERIFIED")   # L17

    def test_same_script_warns(self):
        a, b = self._row(id="1"), self._row(id="2", player="Q")
        rep = verify.verify(a, [a, b], DEFAULT_ADJ, fetch=False)
        self.assertTrue(any(st == "WARN" and n == "correlation" for st, n, _ in rep.checks))


class GameTotalBackCheck(unittest.TestCase):
    """A playoff total is recounted in both teams' playoff games (L26), not their regular season."""
    def test_postseason_recount(self):
        from edge import grade
        def game(pk, gt, a, h, tid=None):
            return {"gamePk": pk, "gameType": gt, "status": {"codedGameState": "F"},
                    "teams": {"away": {"score": a, "team": {"id": 1}}, "home": {"score": h, "team": {"id": 2}}}}
        tonight = {"dates": [{"games": [{**game(99, "L", 0, 0), "status": {"codedGameState": "S"}}]}]}
        season = {"dates": [{"games": [game(i, "R", 6, 6) for i in range(20)] + [game(100 + i, "L", 2, 2) for i in range(6)]}]}
        orig = grade._get
        try:
            grade._get = lambda url: tonight if "gamePk=99" in url else season
            rep = verify.Report({"id": "1", "sport": "mlb", "market": "game_total", "event_id": "99", "line": "9.5", "side": "under",
                                 "p_hist": "1.0", "date": "2026-10-14"})
            verify.check_mlb_history(rep)
        finally:
            grade._get = orig
        st, name, detail = rep.checks[-1]
        self.assertEqual(st, "PASS")                      # 6/6 playoff games under, not 0/20 regular-season
        self.assertIn("postseason", detail)


class MlbLineupCheck(unittest.TestCase):
    """An 80% call on a hitter who sits is worthless: verify FAILs a batter prop missing from the posted lineup."""
    def _run(self, lineups, pid="7"):
        from edge import grade
        sched = {"dates": [{"games": [{"lineups": lineups, "teams": {"away": {"probablePitcher": {"id": 1}}, "home": {"probablePitcher": {"id": 2}}}}]}]}
        orig = grade._get
        try:
            grade._get = lambda url: sched
            rep = verify.Report({"id": "1", "sport": "mlb", "market": "batter_hits", "event_id": "9", "player_id": pid, "line": "0.5", "side": "over"})
            verify.check_mlb_lineup(rep)
        finally:
            grade._get = orig
        return rep.checks[-1][0]

    def test_lineup_states(self):
        self.assertEqual(self._run({}), "WARN")                                            # not posted yet
        self.assertEqual(self._run({"awayPlayers": [{"id": 7}], "homePlayers": []}), "PASS")
        self.assertEqual(self._run({"awayPlayers": [{"id": 8}], "homePlayers": []}), "FAIL")


class DevigMethods(unittest.TestCase):
    def test_methods_agree_on_even_lines_and_order_on_favourites(self):
        from edge import odds
        for m in odds.DEVIG_METHODS + ("worst",):
            a, b = odds.devig(-110, -110, m)
            self.assertAlmostEqual(a, 0.5, places=4)
            self.assertAlmostEqual(a + b, 1.0, places=4) if m != "worst" else None
        fav = {m: odds.devig(-500, 350, m)[0] for m in odds.DEVIG_METHODS}
        # multiplicative leaves the most margin on the favourite; power and Shin move it to the longshot
        self.assertLess(fav["multiplicative"], fav["power"])
        self.assertLess(fav["multiplicative"], fav["shin"])
        self.assertLessEqual(odds.devig(-500, 350, "worst")[0], min(fav.values()) + 1e-9)


class Projection(unittest.TestCase):
    def test_ladder_line_is_the_market_fifty_fifty_point(self):
        from edge import tier
        rungs = {2: -400, 3: -200, 4: 100, 5: 250, 6: 450}       # P(X>=3) ~ .63, P(X>=4) ~ .47
        m = tier.ladder_line(rungs)
        self.assertGreater(m, 2.5)
        self.assertLess(m, 3.5)
        self.assertIsNone(tier.ladder_line({1: -900, 2: -500}))   # never crosses one half: no market line

    def test_projection_prefers_matchup_then_market_then_average(self):
        from edge import tier
        self.assertEqual(tier.projection((0.6, ["x"], 7.04), {2: -400, 3: 100}, 5.5, 6.2), (7.0, "matchup model"))
        self.assertEqual(tier.projection(None, None, 5.5, 6.2), (5.5, "books' main line"))
        self.assertEqual(tier.projection(None, None, None, 6.24), (6.2, "last 10 average"))
        self.assertEqual(tier.projection(None, None, None, None), (None, ""))


class ContextModel(unittest.TestCase):
    def test_nb_over_matches_poisson_limit_and_handles_push(self):
        import math
        from edge import context as CX
        lam = 2.0
        pois_over_1_5 = 1 - math.exp(-lam) * (1 + lam)
        self.assertAlmostEqual(CX.nb_over(lam, 1.5, 0.01), pois_over_1_5, places=3)   # tiny CV -> Poisson
        self.assertLess(CX.nb_over(lam, 1.5, 0.5), pois_over_1_5)                     # overdispersion fattens the 0-1 side
        p0, p1 = math.exp(-lam), math.exp(-lam) * lam
        self.assertAlmostEqual(CX.nb_over(lam, 1.0, 0.01), (1 - p0 - p1) / (1 - p1), places=3)  # whole line: push removed

    def test_no_context_for_unsupported_props(self):
        from edge import context as CX
        self.assertIsNone(CX.price("NBA", "Points", "BOS", "1", 20.5, 2026))
        self.assertIsNone(CX.price("NHL", "Shots On Goal", None, "1", 2.5, 2026))


class OddsApi(unittest.TestCase):
    ODDS = {"id": "e1", "home_team": "Boston Celtics", "away_team": "Detroit Pistons", "commence_time": "2026-10-20T23:00:00Z",
            "bookmakers": [
                {"key": "pinnacle", "markets": [{"key": "player_points", "outcomes": [
                    {"name": "Over", "description": "Jayson Tatum", "price": -400, "point": 19.5},
                    {"name": "Under", "description": "Jayson Tatum", "price": 300, "point": 19.5}]}]},
                {"key": "draftkings", "markets": [{"key": "player_points_alternate", "outcomes": [
                    {"name": "Over", "description": "Jayson Tatum", "price": -500, "point": 19.5},
                    {"name": "Over", "description": "Jayson Tatum", "price": -200, "point": 24.5}]}]},
                {"key": "fanduel", "markets": [{"key": "player_points", "outcomes": [
                    {"name": "Over", "description": "Jaylen Brown", "price": -110, "point": 22.5},
                    {"name": "Under", "description": "Jaylen Brown", "price": -110, "point": 22.5}]}]}]}

    def test_book_prices_two_way_and_ladder(self):
        from edge import oddsapi as OA, tier
        p = OA.book_prices(self.ODDS, "player_points", "Jayson Tatum", 19.5)
        self.assertEqual(set(p), {"pinnacle", "draftkings"})
        self.assertAlmostEqual(p["pinnacle"], 0.8 / (0.8 + 0.25), places=4)              # two-way, multiplicative
        self.assertAlmostEqual(p["draftkings"], tier.devig_one_way(500 / 600), places=4)  # one-way rung
        self.assertEqual(OA.book_prices(self.ODDS, "player_points", "Jayson Tatum", 20.5), {})
        self.assertEqual(OA.book_prices(self.ODDS, "player_points", "Jayson Tatum", 20.0), {})  # whole line, no push price

    def test_consensus_weights_sharp_and_flags_disagreement(self):
        from edge import oddsapi as OA
        c = OA.consensus({"pinnacle": 0.76, "draftkings": 0.82})
        self.assertLess(c["p_over"], 0.79)                         # Pinnacle 3x pulls toward .76
        self.assertEqual(c["sharp"], ["pinnacle"])
        self.assertFalse(c["disagree"])
        self.assertTrue(OA.consensus({"pinnacle": 0.70, "fanduel": 0.85})["disagree"])
        self.assertIsNone(OA.consensus({}))
        self.assertIn("2 books incl. pinnacle", OA.describe(c))

    def test_match_event_by_team_and_time(self):
        from edge import oddsapi as OA
        evs = [self.ODDS, {**self.ODDS, "id": "e2", "commence_time": "2026-10-22T23:00:00Z"}]
        self.assertEqual(OA.match_event(evs, "Celtics", "2026-10-20T19:10:00.000-04:00")["id"], "e1")
        self.assertEqual(OA.match_event(evs, "Celtics", "2026-10-22T19:00:00.000-04:00")["id"], "e2")
        self.assertIsNone(OA.match_event(evs, "Knicks", "2026-10-20T19:00:00.000-04:00"))

    def test_market_keys_cover_extra_stats(self):
        from edge import tier
        self.assertEqual(tier.market_key("MLB", "Pitching Outs"), "pitcher_outs")
        self.assertEqual(tier.market_key("NHL", "Shots On Goal"), "skater_sog")
        self.assertEqual(tier.market_key("NFL", "Receiving Yards"), "rec_yds")
        self.assertIsNone(tier.market_key("NFL", "Fantasy Score"))


class TierScan(unittest.TestCase):
    def test_devig_and_rungs(self):
        from edge import tier
        self.assertAlmostEqual(tier.devig_one_way(0.5), 0.465, places=3)        # mid prices: ~7% hold
        self.assertGreater(tier.devig_one_way(0.95), 0.92)                      # heavy favourites: ~3%
        self.assertLess(tier.devig_one_way(0.95), 0.95)

    def test_whole_line_removes_push(self):
        from edge import tier
        lad = {2: -190, 3: 150}                                                  # Rantanen SOG, PrizePicks 2.0
        half, _ = tier.market_over(lad, 2.5)
        whole, note = tier.market_over(lad, 2.0)
        self.assertAlmostEqual(half, tier.devig_one_way(0.4), places=4)          # 2.5 reads the 3+ rung as is
        self.assertGreater(whole, 0.45)                                          # 0-1 vs 3+: near a coin flip,
        self.assertLess(whole, 0.52)                                             # not the 63% under that 1 - P(3+) gave
        self.assertIn("push", note)
        self.assertIsNone(tier.market_over({3: 150}, 2.0)[0])                    # can't price the push without the 2+ rung


class Grading(unittest.TestCase):
    def test_settle(self):
        self.assertEqual(grade.settle(3, 3.5, "under"), "won")
        self.assertEqual(grade.settle(16, 16, "under"), "push")
        self.assertEqual(grade.settle(18, 17.5, "over"), "won")

    def test_mlb_from_cache(self):
        cache = {("mlb", "1"): {"final": True, "box": {"teams": {"home": {"players": {"ID9": {"stats": {"pitching": {"outs": 15, "strikeOuts": 4}}}}}, "away": {"players": {}}}}}}
        self.assertEqual(grade.mlb_value("1", "9", "pitcher_outs", cache), ("final", 15))
        self.assertEqual(grade.mlb_value("1", "8", "pitcher_outs", cache), ("void", None))

    def test_cs2_unparsed_stats_stay_pending(self):
        orig = grade._get
        grade._get = lambda url: [] if "players_stats" in url else {"results": [{"id": 1, "number": 1, "status": "finished"}, {"id": 2, "number": 2, "status": "finished"}]}
        try:
            self.assertEqual(grade.cs2_value("9", "divine", "cs_kills_m12", {}), ("pending", None))
        finally:
            grade._get = orig

    def test_lol_maps_1_3_from_gol(self):
        g = lambda gid, date, title, k, w=True: {"game": gid, "date": date, "title": title, "k": k, "win": w}
        games = [g(7, "2026-10-13", "WE vs FQ", 5, False), g(5, "2026-10-13", "WE vs FQ", 7), g(6, "2026-10-13", "WE vs FQ", 4, False),
                 g(8, "2026-10-13", "WE vs FQ", 12), g(1, "2026-10-06", "FQ vs SR", 9)]
        orig = lol.match_by_id, lol.player_games
        try:
            lol.player_games = lambda pid: games
            lol.match_by_id = lambda i: {"status": "finished", "team1_score": 3, "team2_score": 1, "start_date": "2026-10-13T06:00:00Z"}
            self.assertEqual(grade.lol_value("1", "2", "kills_m123", {}), ("final", 16))   # games 1-3 in game-id order
            lol.match_by_id = lambda i: {"status": "finished", "team1_score": 2, "team2_score": 0, "start_date": "2026-10-13T06:00:00Z"}
            self.assertEqual(grade.lol_value("1", "2", "kills_m123", {}), ("void", None))   # a 2-0 Bo3 never plays map 3
            lol.match_by_id = lambda i: {"status": "finished", "team1_score": 3, "team2_score": 0, "start_date": "2026-10-20T06:00:00Z"}
            self.assertEqual(grade.lol_value("1", "2", "kills_m123", {}), ("pending", None))  # not on gol.gg yet
            lol.match_by_id = lambda i: {"status": "current", "team1_score": 1, "team2_score": 1, "start_date": "2026-10-13T06:00:00Z"}
            self.assertEqual(grade.lol_value("1", "2", "kills_m123", {}), ("pending", None))
        finally:
            lol.match_by_id, lol.player_games = orig

    def test_grade_rows_updates_status(self):
        rows = [{"status": "pending", "sport": "nhl", "event_id": "5", "player_id": "7", "market": "skater_sog", "line": "3.5", "side": "under", "notes": ""}]
        orig = grade.GRADERS["nhl"]
        grade.GRADERS["nhl"] = lambda *a: ("final", 2)
        try:
            grade.grade_rows(rows)
        finally:
            grade.GRADERS["nhl"] = orig
        self.assertEqual(rows[0]["status"], "won")
        self.assertEqual(rows[0]["result_value"], 2)


class Tennis(unittest.TestCase):
    """The live chain against textbook values, the serve solver, score parsing and the no-look-ahead feature walk."""
    def test_chain_known_values(self):
        from edge import tennis as T
        self.assertAlmostEqual(T.p_game(0.6), 0.7357, places=4)                 # hold at 60% of serve points
        self.assertAlmostEqual(T.p_tiebreak(0.65, 0.65, "A"), 0.5, places=9)
        self.assertAlmostEqual(T.p_prematch(0.62, 0.62), 0.5, places=9)
        self.assertGreater(T.p_prematch(0.66, 0.62, 5), T.p_prematch(0.66, 0.62, 3))   # best of 5 favours the better player
        self.assertGreater(T.p_match(0.64, 0.64, 3, 1, 0, 5, 4, "A", (3, 0)), 0.99)  # serving for it at 40-0
        self.assertLess(T.p_match(0.64, 0.64, 3, 0, 1, 0, 5, "B", (3, 0)), 0.01)

    def test_serve_solver_inverts_the_chain(self):
        from edge import tennis as T
        pa, pb = T.solve_serve(0.7, 1.28)
        self.assertAlmostEqual(pa + pb, 1.28, places=6)
        self.assertAlmostEqual(T.p_prematch(pa, pb), 0.7, places=3)

    def test_momentum_lifts_the_set_leader(self):
        from edge import tennis as T
        self.assertGreater(T.p_match(0.62, 0.62, 3, 1, 0, srv="A", form=0.015), T.p_match(0.62, 0.62, 3, 1, 0, srv="A"))

    def test_score_and_points(self):
        from edge import tennis as T
        self.assertEqual(T.parse_score("4-6 1-0"), ((0, 1), (1, 0)))
        self.assertEqual(T.parse_score("7-6(5) 3-6 2-2"), ((1, 1), (2, 2)))
        self.assertEqual(T.parse_points("40-AD", False), (3, 4))
        self.assertEqual(T.parse_points("5-6", True), (5, 6))
        self.assertEqual(T.surface("Roland Garros", "Paris, France", "2025-06-01"), "clay")
        self.assertEqual(T.surface("Rolex Paris Masters", "Paris, France", "2025-11-01"), "hard")
        self.assertEqual(T.surface("Lexus Birmingham Open", "Birmingham", "2025-05-30"), "grass")

    def test_features_never_see_the_match(self):
        from edge import tennis as T
        rows = [{"date": f"2025-01-{d:02d}", "tour": "atp", "comp_id": str(d), "event_id": "e", "event": "X", "round": "R1",
                 "city": "", "surface": "hard", "bo": "3", "w_id": "1", "w_name": "A", "l_id": "2", "l_name": "B",
                 "w_games": "6,6", "l_games": "3,4", "tb": "0", "retired": "0"} for d in range(1, 6)]
        R, out = T.walk(rows)
        self.assertAlmostEqual(out[0][3]["p_elo"], 0.5)                          # first meeting: no information yet
        self.assertGreater(R.p_elo("1", "2", "hard"), 0.6)                       # after five wins


class NoMarketGrading(unittest.TestCase):
    def test_log_model(self):
        from edge.context import log_model
        p, why, m = log_model([102, 45, 88, 130, 61, 95, 77, 110, 40, 99, 120, 85], 91.5)
        self.assertTrue(0.3 < p < 0.5 and 80 < m < 95)
        self.assertIsNone(log_model([1, 2, 3], 1.5))                                   # under 5 games: no model
        self.assertEqual(log_model([0, 0, 0, 0, 0, 0], 0.5)[0], 0.02)                  # never 0 or 1
        hi, lo = log_model([2, 1, 3, 2, 1, 2, 0, 1], 0.5)[0], log_model([2, 1, 3, 2, 1, 2, 0, 1], 2.5)[0]
        self.assertGreater(hi, lo)

    def test_nfl_cells(self):
        from edge.tier import nfl_num, canon_stat
        self.assertEqual([nfl_num(v) for v in ("3-4", "1,204", "-3", "0/0", "--")], [3, 1204, -3, 0, 0])
        self.assertEqual(canon_stat("NFL", "Anytime TDs"), "Rush+Rec TDs")
        self.assertEqual(canon_stat("NFL", "Rush+Rec Yds"), "Rush+Rec Yds")
        self.assertEqual(canon_stat("NFL", "Rec Yards"), "Receiving Yards")
        self.assertEqual(canon_stat("NFL", "Recs"), "Receptions")
        self.assertEqual(canon_stat("NFL", "FG Made"), "FG Made")
        self.assertEqual(canon_stat("NFL", "Receiving"), "Receiving Yards")             # a tout's '70+ Receiving'
        self.assertEqual(canon_stat("NFL", "Yards Rushing"), "Rush Yards")
        self.assertEqual(canon_stat("NFL", "Rushing Attempts"), "Rush Attempts")
        self.assertEqual(canon_stat("NFL", "Passing TDs"), "Pass TDs")

    def test_unpriced_floor_learns_apart(self):
        rows = [{"id": str(i), "status": "lost" if i < 8 else "won", "p_final": "0.85", "confidence": "High", "p_market": "",
                 "sport": "nfl", "market": "rec_yds", "side": "over", "action": "lean"} for i in range(20)]
        rows += [{"id": f"m{i}", "status": "won", "p_final": "0.85", "confidence": "High", "p_market": "0.86", "sport": "mlb",
                  "market": "pitcher_strikeouts", "side": "over", "action": "lean"} for i in range(20)]
        priced, _ = learn.tune_rating_floor(rows, {"rating_floor": 0.80})
        unpriced, _ = learn.tune_rating_floor(rows, {"rating_floor_no_market": 0.80}, priced=False)
        self.assertEqual((priced, unpriced), (0.80, 0.83))                              # only the unpriced floor moves


class ComboLadder(unittest.TestCase):
    def test_parts_combine(self):
        from edge.tier import combo_over, ladder_pmf
        pts = {8: -4400, 10: -1580, 12: -730, 15: -288, 18: -134, 20: 119, 25: 354, 30: 1100, 35: 2900}
        ast = {3: -2400, 4: -750, 5: -315, 6: -153, 7: 121, 8: 220, 9: 402, 10: 730, 11: 1220, 12: 2600}
        reb = {3: -111, 4: 223, 5: 518, 6: 1060}
        self.assertAlmostEqual(sum(ladder_pmf(pts)), 1.0, places=6)
        over = combo_over([pts, reb, ast], 28.5)                      # Shai, preseason 10/15: the book's ~28 PRA
        self.assertTrue(0.40 < over < 0.52)
        self.assertGreater(combo_over([pts, reb, ast], 20.5), over)
        self.assertGreater(combo_over([pts, ast], 20.5), combo_over([pts, ast], 25.5))


class Preseason(unittest.TestCase):
    def test_minutes_model(self):
        from unittest import mock
        from edge import tier
        g = lambda d, mn, pts, reb, ast, team="OKC": {"date": d, "team": team, "s": {"MIN": str(mn), "PTS": str(pts), "REB": str(reb), "AST": str(ast)}}
        pre = [g("2026-10-14", 23, 15, 0, 6), g("2026-10-08", 18, 17, 3, 5), g("2025-10-18", 18, 12, 4, 5), g("2025-10-15", 19, 23, 2, 6),
               g("2025-10-10", 20, 16, 1, 5)]
        reg = [g("2026-04-10", 34, 32, 5, 6)] * 20
        with mock.patch.object(tier, "nba_log", lambda aid, kind="Regular Season": pre if kind == "Preseason" else reg):
            fresh = tier.preseason_model("1", "OKC", "pra", 28.5, "2026-10-20")
            b2b = tier.preseason_model("1", "OKC", "pra", 28.5, "2026-10-15")
        self.assertLess(fresh[0], 0.30)                                  # ~20 minutes: 28.5 PRA is a long way off
        self.assertLess(b2b[2], fresh[2])                                # second night of a back-to-back: fewer minutes
        self.assertIn("back-to-back", b2b[1][0])

    def test_preseason_book_counts_half(self):
        from edge.tier import preseason_adj
        from edge.blend import load_adjustments
        a, b = load_adjustments()["blend"], preseason_adj()["blend"]
        self.assertAlmostEqual(sum(a[k] for k in ("w_model", "w_market", "w_hist")), sum(b[k] for k in ("w_model", "w_market", "w_hist")), places=6)
        self.assertLess(b["w_market"] / b["w_model"], a["w_market"] / a["w_model"])


class Circumstances(unittest.TestCase):
    """L31: what a game log can't see, read from tonight's feed and the player's latest note."""
    def feed(self, injuries=(), spread=None, total=None, weather=None, goalies=None, last=()):
        return {"injuries": [{"team": {"abbreviation": t}, "injuries": [{"athlete": {"id": i, "displayName": n}, "status": st,
                                                                            "details": {"type": k}, "date": "2099-01-01T00:00Z"}
                                                                           for i, n, st, k in v]} for t, v in injuries],
                "pickcenter": [{"spread": spread, "overUnder": total, "details": f"X {spread}"}] if spread is not None or total else [],
                "gameInfo": {"weather": weather} if weather else {}, "goalies": goalies or {},
                "lastFiveGames": [{"team": {"abbreviation": "OKC"}, "events": [{"gameDate": d} for d in last]}],
                "leaders": [{"team": {"abbreviation": "OKC"}, "leaders": [{"leaders": [{"athlete": {"displayName": "Shai Gilgeous-Alexander"}}]}]}]}

    def chk(self, feed, note="", **kw):
        from unittest import mock
        from edge import situation as SI
        args = dict(league="NBA", event_id="1", team="OKC", player="Jalen Williams", espn_id="9", market="pra", side="under",
                    game_day="2026-10-15")
        args.update(kw)
        with mock.patch.object(SI, "summary", lambda lg, ev: feed), mock.patch.object(SI, "rotowire", lambda lg, i: note):
            return SI.check(**args)

    def test_out_and_doubtful(self):
        f = self.feed(injuries=[("OKC", [("9", "Jalen Williams", "Out", "Wrist")])])
        self.assertEqual(self.chk(f).worst, "OUT")
        f = self.feed(injuries=[("OKC", [("9", "Jalen Williams", "Doubtful", "Wrist")])])
        self.assertEqual(self.chk(f).apply("High"), "Low")

    def test_rest_and_notes_by_side(self):
        f = self.feed(injuries=[("OKC", [("9", "Jalen Williams", "Day-To-Day", "Rest")])])
        self.assertEqual(self.chk(f, side="over").worst, "HOLD")             # resting: an over is a bet on minutes he may not get
        self.assertEqual(self.chk(f, side="under").worst, "INFO")            # sitting voids, limited minutes help
        note = "It remains to be seen if he'll get one final tune-up Thursday in Houston."
        self.assertEqual(self.chk(self.feed(), note, side="over").worst, "HOLD")
        self.assertEqual(self.chk(self.feed(), "He is expected to start Thursday with Holmgren out.", side="under").worst, "HOLD")
        self.assertEqual(self.chk(self.feed(), "Glasnow will start Game 4.", market="pitcher_strikeouts", side="under",
                                  league="MLB").worst, "INFO")             # a starter who will start isn't news

    def test_star_teammate_out_caps_unders(self):
        f = self.feed(injuries=[("OKC", [("1", "Shai Gilgeous-Alexander", "Out", "Rest")])])
        self.assertEqual(self.chk(f).apply("High"), "Medium")

    def test_blowout_weather_goalie_b2b(self):
        self.assertEqual(self.chk(self.feed(spread=14.5), side="over").apply("High"), "Medium")
        wind = self.feed(weather={"gust": 25, "precipitation": 10, "temperature": 40})
        self.assertEqual(self.chk(wind, league="NFL", market="pass_yds", side="over").apply("High"), "Medium")
        g = {"home": {"athletes": [{"displayName": "Sergei Bobrovsky"}]}}
        self.assertEqual(self.chk(self.feed(goalies=g), league="NHL", market="goalie_saves", player="Spencer Knight", side="over").worst, "OUT")
        b2b = self.feed(goalies={"home": {"athletes": [{"displayName": "Jalen Williams"}]}}, last=["2026-10-14T23:30Z"])
        self.assertEqual(self.chk(b2b, league="NHL", market="goalie_saves", side="over").apply("High"), "Medium")


class DefenseVsPosition(unittest.TestCase):
    def test_rank_tier_and_side(self):
        from edge import dvp
        allowed = {"DEN": 117.8, "SEA": 150.0, "MIA": 190.0, "NYJ": 140.0, "KC": 130.0}
        c = dvp._card("Defense vs Position", "x", "Def vs WRs", "DEN", allowed, False, "less", "allowed a game")
        self.assertEqual((c["rank"], c["of"], c["tier"]), (1, 5, "Strong"))           # allows the fewest: strongest
        w = dvp._card("Defense vs Position", "x", "Def vs WRs", "MIA", allowed, False, "less", "allowed a game")
        self.assertEqual((w["rank"], w["tier"]), (5, "Weak"))
        lineup = {"LAD": 0.257, "MIL": 0.221, "NYY": 0.250}                            # a hitting lineup: high = strong
        self.assertEqual(dvp._card("Lineup vs Pitchers", "x", "g", "LAD", lineup, True, "more", "")["rank"], 1)

    def test_table_from_box_scores(self):
        from unittest import mock
        from edge import dvp
        games = {"1": {"DEN": {"WR": {"rec_yds": 100}}, "SEA": {"WR": {"rec_yds": 200}}},
                 "2": {"DEN": {"WR": {"rec_yds": 140}}, "SEA": {"WR": {"rec_yds": 180}}}}
        dvp.table.cache_clear()
        with mock.patch.object(dvp, "_load", lambda lg: {"games": games}):
            t = dvp.table("NFL", "WR", ("rec_yds",))
        dvp.table.cache_clear()
        self.assertEqual(t, {"DEN": 120.0, "SEA": 190.0})


class LineGap(unittest.TestCase):
    def test_standard_line_is_the_median(self):
        from edge.tier import line_gate
        notes = []
        self.assertEqual(line_gate("Medium", notes, "standard", 0.937, 58.5, 33.8, "under"), "Low")   # Lloyd: the line knows
        self.assertIn("line gap", notes[0])
        self.assertEqual(line_gate("High", [], "goblin", 0.88, 0.5, 2.7, "over"), "High")        # goblins sit off the median
        self.assertEqual(line_gate("Medium", [], "standard", 0.66, 47.5, 62.7, "over"), "Medium")  # a normal disagreement


class Inject(unittest.TestCase):
    def test_stat_names_from_screens(self):
        from edge.tier import canon_stat
        self.assertEqual(canon_stat("MLB", "H+R+RBI"), "Hits+Runs+RBIs")
        self.assertEqual(canon_stat("MLB", "Hits + Runs + RBIs"), "Hits+Runs+RBIs")
        self.assertEqual(canon_stat("MLB", "Hits Allowed"), "Hits Allowed")                  # not batter Hits
        self.assertEqual(canon_stat("MLB", "Pitcher Strikeouts"), "Pitcher Strikeouts")
        self.assertEqual(canon_stat("NHL", "SOG"), "Shots On Goal")
        self.assertEqual(canon_stat("NBA", "Pts+Rebs+Asts"), "Pts+Rebs+Asts")
        self.assertEqual(canon_stat("NBA", "3PT Made"), "3-PT Made")
        self.assertIsNone(canon_stat("NBA", "Fantasy Score"))

    def test_abbreviated_names(self):
        from edge.tier import name_key
        self.assertEqual(name_key("S. Gilgeous-Alexander"), name_key("Shai Gilgeous-Alexander"))
        self.assertEqual(name_key("K. Walker"), name_key("Kenneth Walker III"))
        self.assertNotEqual(name_key("J. Williams"), name_key("Jalen Brooks"))

    def test_slate_day_reads_utc_in_new_york(self):
        from edge.tier import slate_day
        self.assertEqual(slate_day("2026-10-16T00:00Z"), "2026-10-15")                       # 8 PM ET game on the 15th
        self.assertEqual(slate_day("2026-10-15T20:00:00.000-04:00"), "2026-10-15")
        self.assertEqual(slate_day("2026-10-15T17:00Z"), "2026-10-15")

    def test_process_logs_dedupes_and_reports(self):
        from unittest import mock
        from edge import inject, tier
        head = {k: "" for k in learn.FIELDS}
        old = {**head, "id": "7", "event_id": "849810", "player": "Tyler Glasnow", "market": "pitcher_strikeouts", "line": "3.5",
               "side": "over", "status": "pending", "action": "lean", "entry_id": "", "p_final": "0.8558", "confidence": "High",
               "p_market": "0.8475"}
        store = {"rows": [old]}
        priced = {"Tyler Glasnow": dict(player="Tyler Glasnow", stat="Pitcher Strikeouts", market_key="pitcher_strikeouts",
                                        side="over", p_market=0.85, p_hist=0.93, hist_n=14, p_model=None, p_final=0.86,
                                        confidence="High", rating=9, player_id="607192", proj=7.0, notes="DK", event_id="401908033",
                                        team="LAD", opp="MIL", start="2026-10-16T00:00Z"),
                  "Shohei Ohtani": dict(player="Shohei Ohtani", stat="Hits+Runs+RBIs", market_key="batter_hrr", side="under",
                                        p_market=0.69, p_hist=0.8, hist_n=30, p_model=None, p_final=0.71, confidence="Medium",
                                        rating=7, player_id="660271", proj=1.4, notes="DK", event_id="401908033", team="LAD",
                                        opp="MIL", start="2026-10-16T00:00Z")}
        rep = mock.Mock(verdict="VERIFIED", checks=[("WARN", "lineup", "not posted")])
        doc = {"id": "t1", "kind": "slip", "app": "PrizePicks", "props": [
            {"player": "Tyler Glasnow", "sport": "MLB", "stat": "Strikeouts", "line": 3.5, "side": "More", "odds_type": "goblin"},
            {"player": "Shohei Ohtani", "sport": "MLB", "stat": "H+R+RBI", "line": "2.5", "side": "Less"},
            {"player": "Someone", "sport": "CS2", "stat": "Kills", "line": 30.5, "side": "More"}]}
        with mock.patch.object(learn, "read_bets", lambda *a: [dict(r) for r in store["rows"]]), \
                mock.patch.object(learn, "write_bets", lambda rows, *a: store.update(rows=rows)), \
                mock.patch.object(tier, "price_prop", lambda lg, pl, *a, **k: priced[pl]), \
                mock.patch.object(tier, "grade_id", lambda r: "849810"), \
                mock.patch("edge.verify.verify", lambda b, rows: rep):
            res = inject.process(doc)
        r0, r1, r2 = res["results"]
        self.assertEqual((r0["id"], r0["rating"], r0["verdict"]), ("7", 9, "VERIFIED"))         # existing row, not a duplicate
        self.assertEqual(store["rows"][0]["action"], "user_entry")                               # the user played it
        self.assertEqual(store["rows"][0]["entry_id"], "inject-t1")
        self.assertEqual(r1["id"], "8")
        self.assertEqual(res["new_ids"], ["8"])
        new = store["rows"][1]
        self.assertEqual((new["market"], new["side"], new["line"], new["action"]), ("batter_hrr", "under", 2.5, "user_entry"))
        self.assertEqual(r1["warns"], ["lineup: not posted"])
        self.assertEqual(r2["status"], "not priced")


if __name__ == "__main__":
    unittest.main()
