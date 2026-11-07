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


class TennisReasons(unittest.TestCase):
    """Tennis reasons are only the tested ones (LESSONS L30)."""

    def test_tennis_reasons(self):
        from edge import tennis as T
        s = T.simulate(0.64, 0.62, 3, n=2000, seed=1)
        G = {"sim": s, "avg": {"spw": 0.63}, "ctx": {"best_of": 3}}
        r = {"side": "under", "line": 22.5, "median": 22.0, "q25": 19, "q75": 27, "p_market": None, "stat_key": "games", "a_side": True, "flags": []}
        v = {x["name"]: x["verdict"] for x in T.reasons(r, G)}
        self.assertEqual(v, {"simulation": "supports", "market": "neutral"})


if __name__ == "__main__":
    unittest.main()


class MatchSimulator(unittest.TestCase):
    """The Sim Lab's tennis match simulator (edge/tennis_watch.py data, index.html worker engine)."""

    def test_tennis_explorer_names(self):
        from edge.tennis_watch import _te_name
        self.assertEqual(_te_name("Davidovich Fokina A."), ("davidovichfokina", "a"))
        self.assertEqual(_te_name("Rybakina E."), ("rybakina", "e"))
        self.assertEqual(_te_name("Montes-De La Torre I."), ("montesdelatorre", "i"))

    def test_surface_falls_back_to_hard_unconfirmed(self):
        import datetime as dt
        from edge.tennis_watch import _surface
        st = {"matches": [{"tour": "ATP", "date": 20261105, "tname": "Montevideo", "surface": "Clay"}]}
        self.assertEqual(_surface(st, "ATP", "Montevideo challenger", dt.date(2026, 11, 7))[:2], ("Clay", True))
        self.assertEqual(_surface(st, "ATP", "Nowhere Open", dt.date(2026, 11, 7))[:2], ("Hard", False))

    def test_engine_matches_exact_odds_and_flags(self):
        import shutil, subprocess, json as js, os
        if not shutil.which("node"):
            self.skipTest("node not installed")
        html = os.path.join(os.path.dirname(__file__), "..", "simlab", "index.html")
        code = r"""
const fs=require('fs'),vm=require('vm');const h=fs.readFileSync(process.argv[1],'utf8');
const src=h.match(/<script type="text\/plain" id="workerSrc">([\s\S]*?)<\/script>/)[1];
const c={postMessage:()=>{},setTimeout:(f)=>f(),console,Math,Float64Array,Int32Array,Uint32Array,Uint8Array,Array,Object,JSON,Date,Map};vm.createContext(c);
vm.runInContext(src+';this.__x={tnSolver,tnMatch,seed};',c);const W=c.__x;
const L=W.tnSolver(0.66,0.62,3,false),pre=0.5*(L({sa:0,sb:0,ga:0,gb:0,srv:0,tb:false,x:0,y:0})+L({sa:0,sb:0,ga:0,gb:0,srv:1,tb:false,x:0,y:0}));
W.seed(3);let aw=0,n=60000,bad=0,badSet=0,lastLp=[];for(let i=0;i<n;i++){const log=i<400?[]:null;const r=W.tnMatch([0.66,0.62],3,false,log,i<400?L:null);if(r.w===0)aw++;
 for(const [a,b] of r.sets){if(!((a===7&&(b===5||b===6))||(b===7&&(a===5||a===6))||(a===6&&b<=4)||(b===6&&a<=4)))badSet++;}
 if(log){const pts=log.filter(e=>e.k==='pt'||e.k==='tb');lastLp.push(Math.abs(pts[pts.length-1].lp-(r.w===0?1:0)));
  for(let k=0;k<log.length;k++){const e=log[k];if(e.flag!=='match point')continue;const conv=(e.a?0:1)===e.fp;const end=log.slice(k+1).find(x=>x.k==='pt'||x.k==='tb'||x.k==='end');if(conv!==(end&&end.k==='end'))bad++;}}}
console.log(JSON.stringify({pre,sim:aw/n,badSet,bad,lastLp:Math.max(...lastLp)}));"""
        out = js.loads(subprocess.run(["node", "-e", code, html], capture_output=True, text=True, check=True).stdout)
        self.assertAlmostEqual(out["pre"], out["sim"], delta=0.006)        # exact chance vs 60,000 simulated matches
        self.assertEqual(out["badSet"], 0)                                   # every set score is a real one
        self.assertEqual(out["bad"], 0)                                      # match point "converted" only when the match ends
        self.assertLess(out["lastLp"], 1e-9)                                 # the live line ends at 100% / 0%

    def test_wta_topup_names_short_tour_players_not_itf(self):
        import numpy as np
        from edge.tennis_watch import _short_wta
        st = {"matches": [{"tour": "WTA", "w": "1", "l": "2", "w_name": "Alexandra Shubladze", "l_name": "Claire Liu", "w_hand": "R", "l_hand": "R"}],
              "WTA": {"obs": {"idx": {"1": 0, "2": 1}, "srv": np.array([0] * 3 + [1] * 14), "day": np.array([10 ** 7] * 17)}}}
        rows = [{"p1": "Shubladze A.", "p2": "Liu C.", "tourn": "Hong Kong WTA"},
                {"p1": "Combs E.", "p2": "Liu K.", "tourn": "Hilton Head Island ITF"}]
        pp = {frozenset({"combs", "liu"}): [{"player": "Ellie Combs"}]}
        self.assertEqual(_short_wta(st, rows, pp), ["Alexandra Shubladze"])      # 3 matches: topped up; Liu has 14; ITF skipped
