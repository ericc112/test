import os
import random
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edge import cs2, grade, learn, pp, review, soccer, verify  # noqa: E402
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
        self.assertTrue(std[0]["over_only"])           # More-only standard line
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


if __name__ == "__main__":
    unittest.main()
