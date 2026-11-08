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
        self.assertEqual(v["history"], "supports")          # one history line (season, last 5, h2h count once)
        self.assertNotIn("head-to-head", v)

    def test_average_matchup_is_neutral_and_mixed_h2h_is_against(self):
        pa = {"pts": {"per_game": 43.0, "league_per_game": 43.1, "rank": 13, "all": 112.0, "league": 113.0}}
        r = self.leg(pos_allows=pa, research={**self.leg()["research"], "h2h": [2, 3, 5], "h2h_per36": 26.0})
        v = self.verdicts(r)
        self.assertEqual(v["matchup"], "neutral")
        self.assertEqual(v["history"], "supports")

    def test_matchup_reads_per_100_possessions(self):
        # a fast team allows more per game (43.5 vs 43.1) but less per 100 possessions (38.5 vs 41.5): pace taken out, it's tougher
        pa = {"pts": {"per_game": 43.5, "league_per_game": 43.1, "rank": 12, "per_100": 38.5, "league_per_100": 41.5, "rank_100": 21,
                      "all": 117.0, "league": 113.0, "all_100": 108.0, "league_all_100": 110.0}}
        r = self.leg(stat_key="pts", pos_allows=pa)
        m = next(x for x in N.likely_reasons(r) if x["name"] == "matchup")
        self.assertEqual(m["verdict"], "against")
        self.assertIn("38.5 pts per 100 possessions to Fs", m["text"])
        self.assertIn("ranks pts 21/30", m["text"])
        self.assertIn("43.5 a game", m["text"])

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

    def test_refresh_uses_each_legs_own_logic(self):
        """edge verify --refresh must rebuild a leg the way verify checks it (an NBA v2 leg under v2), so a consistent
        leg is left alone (it once re-scored v2 legs with the generic blend and broke every back-check)."""
        from edge import nba_model, nba_pp, verify as V
        from edge.blend import load_adjustments
        lg = nba_model.params_for(2)
        p, c = nba_pp.recompute(0.70, 0.55, None, 0, "nba:pts:under", lg)
        c, _ = nba_pp.gate_label(c, 0.70, 0.55, "edge pp; logic v2", "pts")      # as the pricer logs it (High = agreement)
        row = {"id": "1", "player": "X", "sport": "nba", "status": "pending", "segment": "nba:pts:under", "p_model": "0.70",
               "p_market": "0.55", "p_hist": "", "hist_n": "0", "p_final": f"{p:.4f}", "confidence": c,
               "notes": "edge pp; logic v2", "event_id": "", "market": "pts"}
        real = V.started
        V.started = lambda r: False
        try:
            self.assertEqual(V.refresh([row], load_adjustments()), [])
        finally:
            V.started = real
        e = V.expected(row, load_adjustments())
        self.assertAlmostEqual(e.p, p, places=4)


class MarketFallback(unittest.TestCase):
    """DraftKings first; with no DraftKings price, Dabble's line nearest the PrizePicks line (user, 2026-11-06)."""

    def test_draftkings_first_then_dabble(self):
        import time
        from edge import nba_pp
        nba_pp._DABBLE.update(t=time.time() + 1e6, map={("derikqueen", "ra"): [{"line": 9.5, "over": 2.06, "under": 1.95},
                                                                               {"line": 12.5, "over": 3.1, "under": 1.4}]})
        try:
            dk = {"p1": {"ra": {"line": 10.5, "over": "-110", "under": "-110"}}}
            m, _ = nba_pp.market_for(dk, "p1", "Derik Queen", "ra", 10.0)
            self.assertEqual((m["book"], m["line"]), ("DraftKings", 10.5))
            self.assertAlmostEqual(m["q"], 0.5)
            m, _ = nba_pp.market_for({}, "p1", "Derik Queen", "ra", 10.0)
            self.assertEqual((m["book"], m["line"]), ("Dabble", 9.5))          # the nearest Dabble line
            self.assertAlmostEqual(m["q"], (1 / 2.06) / (1 / 2.06 + 1 / 1.95))
            self.assertEqual(nba_pp.market_for({}, "p1", "Nobody Here", "ra", 10.0)[0], None)
        finally:
            nba_pp._DABBLE.clear()

    def test_unpriced_draftkings_line_falls_back(self):
        import time
        from edge import nba_pp
        nba_pp._DABBLE.update(t=time.time() + 1e6, map={("derikqueen", "reb"): [{"line": 6.5, "over": 1.83, "under": 2.2}]})
        try:
            m, raw = nba_pp.market_for({"p1": {"reb": {"line": 7.0}}}, "p1", "Derik Queen", "reb", 7.0)
            self.assertEqual(m["book"], "Dabble")
            self.assertEqual(raw["line"], 7.0)
        finally:
            nba_pp._DABBLE.clear()


class HistoryLine(unittest.TestCase):
    """User audit 2026-11-06: one history line, trend next to the count, head-to-head only on comparable minutes."""

    def test_cmb_under(self):
        r = {"side": "under", "line": 14.5, "opp_espn": "MIL", "role": {"min": 22.0},
             "research": {"season": [2, 6, 8], "season_avg": 9.6, "last5": [2, 3, 5], "last_games": [10, 15, 4, 18, 13],
                          "per36": 15.7, "h2h_games": [["2026-01-01", 6, 15], ["2026-02-01", 8, 17], ["2026-03-01", 9, 20]]}}
        v, text = N.history_line(r)
        self.assertEqual(v, "supports")
        self.assertIn("last 5: 3/5 under, avg 12.0, up from 9.6", text)
        self.assertIn("not counted", text)                 # 17 min a game vs 22 projected
        self.assertIn("6/8 under this season", text)


class SecondBookGate(unittest.TestCase):
    def test_disagreeing_second_book_holds_high(self):
        c, held = N.gate_label("High", 0.66, 0.64, "DraftKings 8.5 ...; second book disagrees: Dabble 49% for the over at 10.5", "pts")
        self.assertEqual(c, "Medium")
        self.assertIn("the second book prices the other side", held)


class WithWithout(unittest.TestCase):
    def test_split_by_teammate_played(self):
        log = [["2026-10-22", "X", 1, 24, 10, 5, 2, 1], ["2026-10-24", "X", 1, 22, 8, 4, 1, 0], ["2026-10-26", "X", 0, 31, 16, 7, 3, 2]]
        w = N.with_without({"research": {"log": log}}, "pr", {"Kawhi Leonard": ["2026-10-22", "2026-10-24"], "Bench Guy": []},
                           [{"name": "Bench Guy", "value": 0.4}, {"name": "Kawhi Leonard", "value": 3.1}])
        self.assertEqual(w[0]["name"], "Kawhi Leonard")                     # most valuable first
        self.assertEqual(w[0]["with"], {"n": 2, "min": 23.0, "avg": 13.5})
        self.assertEqual(w[0]["without"], {"n": 1, "min": 31.0, "avg": 23.0})
        self.assertEqual(w[1]["with"]["n"], 0)                              # never played: every game is "without"
        self.assertEqual(N.with_without({"research": {"log": log}}, "pr", None, []), [])


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


class DabbleValue(unittest.TestCase):
    def test_whole_reference_line_push(self):
        from edge import shop
        # DraftKings 51% over 3 threes (push excluded): over 3.5 needs 4+, well under 51%
        self.assertTrue(0.35 < shop.prob_at(0.51, 3.0, 3.5, ("three-made",)) < 0.45)
        self.assertAlmostEqual(shop.prob_at(0.6, 19.5, 19.5, ("points",)), 0.6, places=3)


class SlateDate(unittest.TestCase):
    """After 7 pm ET the UTC clock reads tomorrow; files and ledger dates must stay on the US slate."""

    def test_evening_and_late_west_coast_stay_on_the_slate(self):
        from unittest import mock
        import datetime as dt
        from gamesim import data as D
        for utc, want in (("2026-11-07T00:31", "2026-11-06"), ("2026-11-07T06:30", "2026-11-06"), ("2026-11-06T17:00", "2026-11-06")):
            class Fake(dt.datetime):
                @classmethod
                def now(cls, tz=None, _t=utc):
                    return dt.datetime.strptime(_t, "%Y-%m-%dT%H:%M").replace(tzinfo=dt.timezone.utc)
            with mock.patch.object(D.dt, "datetime", Fake):
                self.assertEqual(D.slate_today(), want, utc)


class SimStudy(unittest.TestCase):
    """2026-11-07 simulation study: headroom minutes sharing and the assist-share fix."""

    def test_headroom_fills_rotation_before_stars(self):
        from gamesim import nba as G
        raw = [36.0, 34.0, 30.0, 18.0, 15.0, 12.0, 10.0, 8.0]          # 163 minutes: a starter's 77 are free
        ceil = [40.0, 39.0, 37.0, 34.0, 32.0, 28.0, 24.0, 20.0]   # room for the 77
        x = G.allocate_headroom(raw, ceil)
        self.assertAlmostEqual(sum(x), 240.0, places=6)
        self.assertTrue(all(v <= c + 1e-9 for v, c in zip(x, ceil)))
        self.assertLess(x[0] - raw[0], x[3] - raw[3])                 # the star gains less than the rotation player
        alpha = G.allocate_minutes(raw, alpha=1.0)
        self.assertLess(x[0], alpha[0])                               # proportional scaling pushes the star higher
        self.assertEqual(G.allocate_headroom([50.0] * 5 + [10.0], [52.0] * 6), G.allocate_minutes([50.0] * 5 + [10.0]))  # surplus: unchanged rule

    def test_assist_fix_restores_the_high_usage_share(self):
        import shutil, subprocess, json as js, os
        if not shutil.which("node"):
            self.skipTest("node not installed")
        html = os.path.join(os.path.dirname(__file__), "..", "simlab", "index.html")
        code = r"""
const fs=require('fs'),vm=require('vm');const h=fs.readFileSync(process.argv[1],'utf8');
const src=h.match(/<script type="text\/plain" id="workerSrc">([\s\S]*?)<\/script>/)[1];
const c={postMessage:()=>{},setTimeout:(f)=>f(),console,Math,Float64Array,Int32Array,Uint32Array,Uint8Array,Array,Object,JSON};vm.createContext(c);
vm.runInContext(src+';this.__f=nbAstFix;',c);
const z=(a)=>Float64Array.from(a);const t={n:3,w2m:z([4,3,3]),w3m:z([0,0,0]),wa:z([5,3,2]),am:z([0,0,0]),at:z([0,0,0]),ax:z([0,0,0]),ae:z([0,0,0])};
c.__f(t);const A=[...t.wa],S=A.reduce((a,b)=>a+b,0),ms=[0.4,0.3,0.3];
const e=A.map((x,i)=>ms.reduce((s,m,j)=>j===i?s:s+m*x/(S-A[j]),0));console.log(JSON.stringify({e,tgt:[0.5,0.3,0.2],w:A}));"""
        out = js.loads(subprocess.run(["node", "-e", code, html], capture_output=True, text=True, check=True).stdout)
        for e, t in zip(out["e"], out["tgt"]):
            self.assertAlmostEqual(e, t, places=3)                   # expected assist shares now match the rates
        self.assertGreater(out["w"][0] / sum(out["w"]), 0.5)          # the main shooter's weight is raised above his 50% rate share


class TeamMarketAnchor(unittest.TestCase):
    """OKC @ MEM 2026-11-06: eight games of results had Memphis by 7; the market had OKC by 4.5."""

    def test_anchor_moves_margin_and_total_to_the_line(self):
        from gamesim import nba as G
        R = {"league": {"pace": 99.0}, "and1": 0.02}
        side = lambda p2, p3: {"three": 0.4, "p2": p2, "p3": p3, "to": 0.13, "ft_rate": 0.12, "ftp": 0.78, "orb": 0.25, "pace_off": 0.0}
        H, A = side(0.56, 0.38), side(0.52, 0.35)
        h0, a0 = G.expected_points(H, A, R)
        self.assertGreater(h0 - a0, 3)                                 # the ratings like the home side
        H2, A2, det = G.anchor_to_market(H, A, R, spread_home=4.5, total=224.5, w=1.0)
        h1, a1 = G.expected_points(H2, A2, R)
        self.assertAlmostEqual(h1 - a1, -4.5, delta=0.2)
        self.assertAlmostEqual(h1 + a1, 224.5, delta=0.3)
        self.assertEqual(G.anchor_to_market(H, A, R, None, 224.5, 1.0)[0], H)   # no line: unchanged
        self.assertEqual(G.anchor_to_market(H, A, R, 4.5, 224.5, None)[0], H) if G.TEAM_MARKET_W is None else None


class SimAudit(unittest.TestCase):
    def test_summary_counts_and_flags(self):
        from edge import sim_audit as SA
        T = [{"game": "OKC @ MEM", "p_home": 0.61, "mk_home": 0.39, "home_won": False, "margin": -31, "total": 225, "spread": 4.5, "mk_total": 224.5, "sim_margin": 4.0, "sim_total": 223},
             {"game": "WSH @ ATL", "p_home": 0.75, "mk_home": 0.73, "home_won": True, "margin": 7, "total": 271, "spread": -8.5, "mk_total": 228.5, "sim_margin": 7.0, "sim_total": 230}]
        M = [{"game": "TOR @ MIL", "name": "Alijah Martin", "side": "away", "proj": 9.7, "act": 31.0, "kind": "", "outs_on_team": 3},
             {"game": "PHI @ CLE", "name": "Jarrett Allen", "side": "home", "proj": 21.0, "act": 0.0, "kind": "late scratch", "outs_on_team": 1}]
        rep = SA.summarize("2026-11-06", T, M, [], "test")
        self.assertEqual(rep["team"]["sim_winners"], 1); self.assertEqual(rep["team"]["market_winners"], 2)
        self.assertEqual([d["game"] for d in rep["team"]["disagreements"]], ["OKC @ MEM"])
        self.assertIn("Jarrett Allen", rep["minutes"]["late_scratches"][0])
        self.assertIn("Alijah Martin", rep["minutes"]["biggest_misses"][0])
        self.assertIn("Winners:** simulation 1 of 2", SA.markdown(rep))


class AppBookRouting(unittest.TestCase):
    """An NFL leg on a pick'em app (PrizePicks or Underdog) is re-priced off DraftKings' line by the app pricer, not
    read as a DraftKings line (an Underdog line of 39.5 against DraftKings' 26.5 is not 'the line moved')."""

    def test_app_books(self):
        from edge import verify as V
        self.assertTrue(V._app_book({"book": "PrizePicks goblin"}))
        self.assertTrue(V._app_book({"book": "Underdog"}))
        self.assertFalse(V._app_book({"book": "DraftKings"}))
        self.assertFalse(V._app_book({}))

    def test_underdog_offered_is_a_warning(self):
        from edge import verify as V
        rep = V.Report({"book": "Underdog", "player": "X", "line": 39.5, "side": "under", "start": "2099-01-01T00:00Z"})
        rep.locked = False
        V.check_offered(rep)
        st, name, detail = rep.checks[-1]
        self.assertEqual((st, name), ("WARN", "offered"))
        self.assertIn("confirm line 39.5", detail)
