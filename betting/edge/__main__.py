"""CLI: python -m edge <command>   (run from the betting/ directory)

  report                       calibration, CLV, ROI, segment table, untagged misses
  grade                        settle pending bets from stat feeds, then report
  learn                        refit blend + segment bias from graded bets, append lessons
  prob  --model .6 --market .55 --hist .7 --hist-n 12 --segment mlb:pitcher_outs:over
  breakeven                    per-leg break-even for pick'em payout tables
  squad --means 245 283 207 --sds 70 78 65 --milestones 807 977 1044 --pair-corr 0 1 0.3
  add   key=value ...          append a bet (fields: see data/bets.csv header)
  tag   ID "tag" [--lesson ".."] confirm the root cause of a loss (every loss) and what to change
  verify ID [ID ...] | --open  back-check picks before publishing (recompute, recount, reprice, offered, rules)
  review [--all] [--accept]    post-mortem on every graded loss: feed detail, linked legs, suggested tag
  best  [--date D] [--min-p .65] [--legs 2]   top-tier legs, one per game script, best entry
  card  [--date D]               exposure check: legs riding on the same game script
  pp    --league CS2 [--match Liquid] [--player X] [--types standard,goblin] [--log]   price a PrizePicks board
  passes --player ID --team ID (--event ID | --opp ID [--home|--away]) --line 50.5   soccer passes attempted
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import sys

import numpy as np

from . import card as C
from . import grade as G
from . import learn as L
from . import review as R
from . import pp as P
from . import soccer as S
from . import verify as V
from .blend import final_probability, rating, segment_key
from .odds import fair_american
from .pickem import PAYOUTS, breakeven, squad_ride


def main(argv=None):
    ap = argparse.ArgumentParser(prog="edge", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report")
    sub.add_parser("grade")
    sub.add_parser("learn")
    p = sub.add_parser("prob")
    p.add_argument("--model", type=float)
    p.add_argument("--market", type=float)
    p.add_argument("--hist", type=float)
    p.add_argument("--hist-n", type=int, default=0)
    p.add_argument("--segment", default="")
    sub.add_parser("breakeven")
    s = sub.add_parser("squad")
    s.add_argument("--means", type=float, nargs="+", required=True)
    s.add_argument("--sds", type=float, nargs="+", required=True)
    s.add_argument("--milestones", type=float, nargs=3, required=True)
    s.add_argument("--pair-corr", type=float, nargs=3, action="append", default=[], metavar=("I", "J", "RHO"))
    a = sub.add_parser("add")
    a.add_argument("pairs", nargs="+")
    b = sub.add_parser("best")
    b.add_argument("--date")
    b.add_argument("--min-p", type=float, default=0.65)
    b.add_argument("--legs", type=int, default=2)
    c = sub.add_parser("card")
    c.add_argument("--date")
    c.add_argument("--breakeven", type=float, default=0.577, help="per-leg break-even of the entry (2-pick power 0.577)")
    ps = sub.add_parser("passes")
    ps.add_argument("--player", required=True)
    ps.add_argument("--team", required=True)
    ps.add_argument("--opp")
    ps.add_argument("--event", help="ESPN event id: home/away, opponent and the 3-way line come from it")
    ps.add_argument("--line", type=float)
    ha = ps.add_mutually_exclusive_group()
    ha.add_argument("--home", dest="home", action="store_true", default=None)
    ha.add_argument("--away", dest="home", action="store_false")
    ps.add_argument("--n", type=int, default=10, help="recent matches per team")
    ps.add_argument("--poss", type=float, help="override projected possession (0-1)")
    pb = sub.add_parser("pp")
    pb.add_argument("--league", required=True, help="PrizePicks league name: CS2, UCL, EPL, ...")
    pb.add_argument("--match", help="only props whose team or opponent contains this text")
    pb.add_argument("--player")
    pb.add_argument("--types", default="standard", help="odds types to include: standard,goblin,demon")
    pb.add_argument("--log", action="store_true", help="log every priced prop to bets.csv (skips ones already logged)")
    oa = sub.add_parser("odds", help="The Odds API ($ODDS_API_KEY): check the key and quota")
    oa.add_argument("--league", default="NBA")
    bd = sub.add_parser("board", help="export 8+ picks and the scorecard as JSON for the Eight-Plus Board page")
    bd.add_argument("--out", required=True)
    bd.add_argument("--days", type=int, default=7)
    bd.add_argument("--no-verify", action="store_true")
    bd.add_argument("--props", action="store_true", help="also export every rated PrizePicks and sportsbook prop (runs the scans)")
    bd.add_argument("--league", default="NHL,MLB,NBA")
    bd.add_argument("--date", help="first slate date for --props (default today)")
    tr = sub.add_parser("tier", help="PrizePicks props with a DraftKings price behind them (NHL, MLB, NBA), rated; 8+ = the 80% tier")
    tr.add_argument("--league", default="NHL,MLB,NBA")
    tr.add_argument("--date", help="first slate date YYYY-MM-DD (default today)")
    tr.add_argument("--days", type=int, default=2, help="slate days to scan from --date")
    tr.add_argument("--min-rating", type=int, default=8)
    tr.add_argument("--log", action="store_true", help="log every priced non-demon prop")
    lw = sub.add_parser("lowline", help="standard PrizePicks lines at 0.5-1.5 where Less is offered, unders priced from game logs")
    lw.add_argument("--league", default="NHL,MLB,NFL")
    lw.add_argument("--max-line", type=float, default=1.5)
    lw.add_argument("--min-rating", type=int, default=1)
    lw.add_argument("--log", action="store_true")
    tn = sub.add_parser("tennis", help="match winner, pre-match and live (ESPN scores; your book's odds)")
    tn.add_argument("action", choices=["refresh", "backtest", "list", "pre", "live"])
    tn.add_argument("player", nargs="?", help="the player you're pricing (A)")
    tn.add_argument("opponent", nargs="?", help="pre-match only")
    tn.add_argument("--tour", choices=["atp", "wta"])
    tn.add_argument("--surface", choices=["hard", "clay", "grass"])
    tn.add_argument("--bo", type=int, choices=[3, 5])
    tn.add_argument("--event", default="")
    tn.add_argument("--odds", nargs=2, type=float, metavar=("A", "B"), help="American odds, A first (live price for `live`)")
    tn.add_argument("--pre-odds", nargs=2, type=float, metavar=("A", "B"), help="pre-match odds: anchor the live model")
    tn.add_argument("--score", help="from A's side, e.g. '4-6 1-0' (overrides ESPN)")
    tn.add_argument("--points", default="0-0", help="current game A-B: 0/15/30/40/AD, or tiebreak points")
    tn.add_argument("--server", choices=["A", "B"])
    tn.add_argument("--srv-a", help="A's serve points won/played so far, e.g. 31/45")
    tn.add_argument("--srv-b", help="B's serve points won/played so far")
    tn.add_argument("--book", default="")
    tn.add_argument("--log", action="store_true")
    ij = sub.add_parser("inject", help="price, log and back-check the props in an inbox doc from the Eight-Plus Board")
    ij.add_argument("file", help="the inbox document as JSON (ArtifactData read output or its data)")
    ij.add_argument("--out", help="write the results here, for the batch update of the inbox doc")
    t = sub.add_parser("tag")
    t.add_argument("id")
    t.add_argument("reason")
    t.add_argument("--lesson", default="")
    vf = sub.add_parser("verify")
    vf.add_argument("ids", nargs="*")
    vf.add_argument("--open", action="store_true", help="every pending pick that is High/Medium or played (bet, lean, user_entry)")
    vf.add_argument("--offline", action="store_true", help="skip the network checks (recompute and rules only)")
    vf.add_argument("--refresh", action="store_true", help="first re-score pending, not-started picks with today's weights")
    vf.add_argument("--fix", action="store_true", help="write the freshly recounted/re-priced numbers onto not-started picks that failed")
    v = sub.add_parser("review")
    v.add_argument("--all", action="store_true", help="re-diagnose every loss, not only new ones")
    v.add_argument("--accept", action="store_true", help="record the suggested tag on losses that have none")
    args = ap.parse_args(argv)

    if args.cmd == "report":
        print(L.report(L.read_bets()))
    elif args.cmd == "grade":
        rows = L.read_bets()
        before = {r["id"]: r.get("status") for r in rows}
        print(G.grade_rows(rows))
        L.write_bets(rows)
        new_losses = [r["id"] for r in rows if r.get("status") == "lost" and before.get(r["id"]) != "lost"]
        if new_losses:  # every loss gets a post-mortem straight away
            print(f"\nPost-mortems for {len(new_losses)} new loss(es):")
            _review(rows, new_losses, accept=False)
        print(L.report(rows))
    elif args.cmd == "learn":
        out = L.update()
        adj = out["adjustments"]
        print("Blend:", adj["blend"], adj.get("blend_fit", {}))
        print("Outcome bias:", adj["outcome_bias_logit"] or "none yet")
        print("Avoid:", adj["avoid_segments"] or "none")
        for n in out["lessons_added"]:
            print("LESSON:", n)
        print(L.report(L.read_bets()))
    elif args.cmd == "prob":
        e = final_probability(args.model, args.market, args.hist, args.segment.lower(), args.hist_n)
        print(f"p={e.p:.3f} (fair {fair_american(e.p):+d}) rating={e.rating}/10 confidence={e.confidence} agreement={e.agreement} spread={e.spread:.3f}")
        print("components:", e.components)
        for n in e.notes:
            print("note:", n)
    elif args.cmd == "breakeven":
        for name, pay in PAYOUTS.items():
            print(f"{name:14s} {pay}  per-leg break-even {breakeven(pay):.1%}")
    elif args.cmd == "squad":
        k = len(args.means)
        corr = np.eye(k)
        for i, j, rho in args.pair_corr:
            corr[int(i), int(j)] = corr[int(j), int(i)] = rho
        r = squad_ride(args.means, args.sds, tuple(args.milestones), corr)
        print(f"median total {r['median_total']:.0f} | P(2x+) {r['p_m1']:.1%} | P(5x+) {r['p_m2']:.1%} | P(20x) {r['p_m3']:.2%} | "
              f"P(nothing) {r['p_nothing']:.1%} | EV per $1 {r['ev'] + 1:.2f}")
    elif args.cmd == "add":
        rows = L.read_bets()
        new = dict(kv.split("=", 1) for kv in args.pairs)
        new.setdefault("id", str(max([int(r["id"]) for r in rows if r["id"].isdigit()] or [0]) + 1))
        new.setdefault("status", "pending")
        if not new.get("segment") and new.get("sport") and new.get("market") and new.get("side"):
            new["segment"] = segment_key(new["sport"], new["market"], new["side"])
        rows.append(new)
        L.write_bets(rows)
        print("added bet", new["id"])
    elif args.cmd == "best":
        legs = C.best_legs(L.read_bets(), args.min_p, date=args.date)
        if not legs:
            print(f"No pending legs pass the gate (High, >= {args.min_p:.0%}). Better to sit out than force a play.")
        for r in legs:
            print(f"{r['p_now']:.1%}  {r['player']:22s} {r['side']:5s} {r['line']:>5} {r['market']:22s} {r['event'][:34]:34s} [{C.script_key(r)}]")
        e = C.best_entry(legs, args.legs)
        if e:
            print(f"\nBest {args.legs}-leg entry (one leg per script): P(all hit) = {e['p_all']:.1%}")
    elif args.cmd == "card":
        rows = [r for r in L.read_bets() if r.get("status") in ("pending", "") and (not args.date or r.get("date") == args.date)]
        priced = {r["id"]: r for r in C.rescore([r for r in rows if any(r.get(k) for k in ("p_model", "p_market", "p_hist"))])}
        weak = 0
        for k, legs in sorted(C.exposure(rows).items(), key=lambda kv: -len(kv[1])):
            flag = "  <-- same script: these win or lose together" if len(legs) > 1 else ""
            print(f"{k:34s} {len(legs)} leg(s){flag}")
            for r in legs:
                p = priced.get(r["id"])
                tag = "UNPRICED: run it through `edge prob` first" if not p else (
                    f"{p['p_now']:.0%} {p['conf_now']}" + ("  <-- below break-even: take it out (L20)" if p["p_now"] < args.breakeven else ""))
                weak += (not p) or p["p_now"] < args.breakeven
                print(f"    {r['player']:22s} {r['side']:5s} {r['line']:>5} {r['market']:22s} {tag}")
        if weak:
            print(f"\n{weak} leg(s) are unpriced or under the {args.breakeven:.1%} break-even. Fix them before submitting.")
    elif args.cmd == "verify":
        rows = L.read_bets()
        if args.refresh:
            ch = V.refresh(rows)
            L.write_bets(rows)
            print(f"Re-scored {len(ch)} pending pick(s) with today's weights:")
            for c in ch:
                print(f"   #{c[0]} {c[1]}: {c[2]} {c[3]} -> {c[4]} {c[5]}")
            print()
        pick = [r for r in rows if r["id"] in args.ids] if args.ids else [
            r for r in rows if r.get("status") in ("pending", "") and (r.get("confidence") in ("High", "Medium") or r.get("action") in ("bet", "lean", "user_entry"))] if args.open else []
        if not pick:
            print("Give pick ids or --open.")
            return
        bad = 0
        for r in pick:
            rep = V.verify(r, rows, fetch=not args.offline)
            if args.fix and rep.verdict == "NOT VERIFIED" and getattr(rep, "fresh", None) and not rep.locked and not rep.start_unknown:
                f = rep.fresh
                r["notes"] = (r.get("notes", "") + f" | corrected by verify: {r.get('p_final')} {r.get('confidence')} -> {f['p_final']} {f['confidence']}; {f['side_note']}").strip(" |")
                r.update({k: f[k] for k in ("p_model", "p_hist", "hist_n", "p_final", "confidence")})
                if f["confidence"] not in ("High",) and r.get("action") in ("bet", "lean"):
                    r["action"] = "pass"
                L.write_bets(rows)
                rep = V.verify(r, rows, fetch=not args.offline)
                print("   (corrected from fresh data, re-verified below)")
            print(rep.text() + "\n")
            bad += rep.verdict == "NOT VERIFIED"
        print(f"{len(pick) - bad} of {len(pick)} verified. Anything NOT VERIFIED is not published; fix it or withdraw it.")
    elif args.cmd == "review":
        rows = L.read_bets()
        done = R.read_pm()
        ids = None if args.all else [r["id"] for r in R.losses(rows) if r["id"] not in done]
        if ids == []:
            print("Every loss already has a post-mortem (use --all to re-diagnose).")
        else:
            _review(rows, ids, accept=args.accept)
    elif args.cmd == "passes":
        m = S.passes_model(args.player, args.team, args.opp, args.line, args.home, args.event, args.n, args.poss)
        st = m["starts"]
        print(f"history ({len(st)} recent starts): " + " ".join(str(int(g['passes'])) for g in st)
              + f" | avg {np.mean([g['passes'] for g in st]):.1f} | share {m['share']:.1%} of team passes per 90")
        mk = f", market {m['market']:.1%}" if m["market"] is not None else " (no 3-way line: stats only)"
        print(f"possession: {m['team_poss']:.0%} vs opp {m['opp_poss']:.0%} -> stats {m['stats']:.1%}{mk} -> {m['possession']:.1%}"
              + ("" if m["home"] is None else " (home)" if m["home"] else " (away)"))
        print(f"tempo: team {m['team_ppp']:.2f} passes per possession pt x opponent press factor {m['press_factor']:.2f}"
              f" ({'presses / compact' if m['press_factor'] < 0.97 else 'lets teams pass' if m['press_factor'] > 1.03 else 'neutral'})")
        if m["wdl"]:
            print(f"game script: win/draw/loss {m['wdl'][0]:.0%}/{m['wdl'][1]:.0%}/{m['wdl'][2]:.0%} (winners keep ~3 pts less of the ball)")
        print(f"team passes ~{m['team_passes']:.0f} -> projection mean {m['mean']:.1f}, median {m['median']:.0f}, 80% range {m['p10']:.0f}-{m['p90']:.0f}")
        if m["days_rest"] is not None and m["days_rest"] <= 3:
            print(f"rotation flag: team played {m['days_rest']} day(s) ago")
        if args.line is not None:
            print(f"P(over {args.line}) {m['p_over']:.1%} | P(under) {m['p_under']:.1%}"
                  + (f" | P(push) {m['p_push']:.1%}" if m["p_push"] else "")
                  + f" | history over {m['hist_over']:.0%} of {m['hist_n']}")
            print(f"next: python -m edge prob --model {m['p_over']:.3f} --hist {m['hist_over']:.3f} --hist-n {m['hist_n']} "
                  f"--segment soccer:passes_att:over   (confirm the lineup ~1 hour before kickoff)")
    elif args.cmd == "pp":
        props = P.board(args.league, tuple(args.types.split(",")))
        if args.match:
            props = [p for p in props if args.match.lower() in f"{p['team']} {p['team_name']} {p['opp']}".lower()]
        if args.player:
            props = [p for p in props if args.player.lower() in str(p["player"]).lower()]
        if not props:
            print("No props on the board match that filter.")
            return
        print(f"Pricing {len(props)} prop(s)...")
        rows = P.price_board(props)
        ok = sorted([r for r in rows if "error" not in r], key=lambda r: -r["p_final"])
        bad = [r for r in rows if "error" in r]
        f = lambda v: "  - " if v is None else f"{v:.2f}"
        print(f"\n{'rate':>4} {'p':>5} {'conf':6s} {'player':16s} {'team':12s} {'stat':18s} {'side':5s} {'line':>5} {'type':8s} model mrkt hist(n)  notes")
        for r in ok:
            print(f"{rating(r['p_final'], r['confidence'], r.get('p_market')):>2}/10 {r['p_final']:.3f} {r['confidence']:6s} {str(r['player'])[:16]:16s} {str(r['team'])[:12]:12s} {r['stat'][:18]:18s} {r['side']:5s} "
                  f"{r['line']:>5} {r['odds_type'][:8]:8s} {f(r['p_model'])} {f(r['p_market'])} {f(r['p_hist'])}({r['hist_n']})  "
                  + ("MORE-ONLY; " if r["over_only"] else "") + (f"push {r['push']:.0%}; " if r['push'] > 0.005 else "") + r["notes"])
        if bad:
            why = collections.Counter(r["error"] for r in bad)
            print(f"\nNot priced: {len(bad)} (" + "; ".join(f"{k} x{v}" for k, v in why.most_common()) + ")")
        high = [r for r in ok if r["confidence"] == "High" and r["p_final"] >= 0.65 and not r.get("newcomer")]
        best = {}
        for r in high:
            best.setdefault(r["script"], r)
        legs = list(best.values())[:2]
        if len(legs) == 2:
            print(f"\nBest 2-leg entry (High legs, different matches): {legs[0]['player']} {legs[0]['side']} {legs[0]['line']} + "
                  f"{legs[1]['player']} {legs[1]['side']} {legs[1]['line']} -> P(both) {legs[0]['p_final'] * legs[1]['p_final']:.1%}")
        else:
            print("\nNo 2-leg entry clears the High gate (>= 65%, one leg per match). Sitting out beats forcing it.")
        if any(r["over_only"] for r in ok):
            print("MORE-ONLY lines can't be played under on PrizePicks; goblins/demons also pay differently, so check the payout.")
        if args.log:
            bets = L.read_bets()
            seen = {(b["event_id"], str(b["player"]).lower(), b["market"], str(float(b["line"])) if b["line"] else "", b["side"]) for b in bets}
            nid = max(int(b["id"]) for b in bets if b["id"].isdigit()) + 1
            added = 0
            for r in ok:
                k = (str(r["event_id"]), str(r["player"]).lower(), r["market_key"], str(float(r["line"])), r["side"])
                if k in seen:
                    continue
                bets.append({"id": str(nid), "date": dt.date.today().isoformat(), "sport": r["sport"], "event": f"{r['team']} vs {r['opp']}",
                             "event_id": r["event_id"], "player": r["player"], "player_id": r["player_id"], "market": r["market_key"],
                             "line": r["line"], "side": r["side"], "book": f"PrizePicks {r['odds_type']}", "p_model": "" if r["p_model"] is None else round(r["p_model"], 3),
                             "p_market": "" if r["p_market"] is None else round(r["p_market"], 3), "p_hist": "" if r["p_hist"] is None else round(r["p_hist"], 3),
                             "hist_n": r["hist_n"], "p_final": r["p_final"], "confidence": r["confidence"],
                             "action": "lean" if r["confidence"] in ("High", "Medium") and not r.get("newcomer") else "pass",
                             "segment": f"{r['sport']}:{r['market_key']}:{r['side']}", "group": r["script"], "status": "pending",
                             "proj": "" if r.get("proj") is None else round(r["proj"], 1), "notes": f"edge pp; {r['notes']}"})
                nid += 1
                added += 1
            L.write_bets(bets)
            print(f"Logged {added} new prop(s) to bets.csv.")
    elif args.cmd == "odds":
        from . import oddsapi as OA
        print(OA.check(args.league.upper()))
    elif args.cmd == "inject":
        from . import inject as IJ
        res = IJ.cli(args.file, args.out)
        for x in res["results"]:
            if x["status"] == "logged":
                print(f"#{x['id']:>5}  {' '.join(str(v) for v in (x['player'], x['side'], x['line'], x['stat']) if v is not None)}: {x['rating']}/10, "
                      f"{x['p']:.3f} {x['confidence']}  {x.get('verdict', '')}")
                for w in x.get("warns", []):
                    print(f"         {w}")
            else:
                print(f"  prop {x['i'] + 1}: not priced ({x['why']})")
        print(f"{len(res['new_ids'])} new row(s) in bets.csv")
    elif args.cmd == "board":
        from . import board as B
        out = B.export(args.out, args.days, not args.no_verify)
        if args.props:
            out += B.export_props(args.out, tuple(x.strip().upper() for x in args.league.split(",")),
                                  dt.date.fromisoformat(args.date) if args.date else None)
        for coll, doc_id, path in out:
            print(coll, doc_id, path)
    elif args.cmd == "tier":
        from . import tier as TR
        res = TR.scan(tuple(x.strip().upper() for x in args.league.split(",")),
                      dt.date.fromisoformat(args.date) if args.date else None, days=args.days)
        ok = sorted([r for r in res if "error" not in r], key=lambda r: -r["p_final"])
        shown = [r for r in ok if r["rating"] >= args.min_rating]
        print(f"\n{len(ok)} priced; {len(shown)} rated {args.min_rating}+ (8+ = High, blended 80%+, and 75%+ at the book when a book prices it)")
        for r in shown:
            ph = "-" if r["p_hist"] is None else f"{r['p_hist']:.2f}"
            print(f"{r['rating']:>2}/10 {r['p_final']:.3f} {r['league']} {r['player'][:22]:22s} {r['team']:4s} {r['stat'][:18]:18s} {'More' if r['side'] == 'over' else 'Less'} "
                  f"{r['line']:<5} {r['odds_type']:8s} market {'none' if r['p_market'] is None else format(r['p_market'], '.2f')} "
                  f"hist {ph}({r['hist_n']}) {r['notes'][:24]}")
        if args.log:
            bets = L.read_bets()
            seen = {(b["event_id"], b["player"].lower(), b["market"], str(float(b["line"])) if b["line"] else "", b["side"]) for b in bets}
            nid = max(int(b["id"]) for b in bets if b["id"].isdigit()) + 1
            added = 0
            for r in ok:
                k = (str(r["event_id"]), r["player"].lower(), r["market_key"], str(float(r["line"])), r["side"])
                if r["odds_type"] == "demon" or k in seen:
                    continue
                bets.append({"id": str(nid), "date": dt.date.today().isoformat(), "sport": r["league"].lower(),
                             "event": f"{r['team']} vs {r['opp']}", "event_id": TR.grade_id(r),
                             "player": r["player"], "player_id": r["player_id"] or "", "market": r["market_key"], "line": r["line"],
                             "side": r["side"], "book": f"PrizePicks {r['odds_type']}", "p_model": "" if r.get("p_model") is None else round(r["p_model"], 4),
                             "p_market": "" if r["p_market"] is None else round(r["p_market"], 4),
                             "p_hist": "" if r["p_hist"] is None else round(r["p_hist"], 4), "hist_n": r["hist_n"], "p_final": round(r["p_final"], 4),
                             "confidence": r["confidence"], "action": "lean" if r["rating"] >= 8 else "pass",
                             "segment": f"{r['league'].lower()}:{r['market_key']}:{r['side']}", "group": f"{r['league'].lower()}:{r['event_id']}",
                             "status": "pending", "proj": "" if r.get("proj") is None else r["proj"],
                             "notes": f"edge tier; {r['notes']}; start {r.get('start')}"})
                nid += 1
                added += 1
            L.write_bets(bets)
            print(f"Logged {added} new prop(s) to bets.csv.")
    elif args.cmd == "lowline":
        from . import lowline as LW
        res = LW.scan(tuple(x.strip().upper() for x in args.league.split(",")), args.max_line)
        ok = sorted([r for r in res if "error" not in r], key=lambda r: -r["p_final"])
        print(f"\n{'rate':>4} {'p':>5} {'conf':6s} {'lg':3s} {'player':20s} {'team':4s} {'stat':14s} {'line':>5} model hist(n)   mean  notes")
        for r in ok:
            if r["rating"] < args.min_rating:
                continue
            print(f"{r['rating']:>2}/10 {r['p_final']:.3f} {r['confidence']:6s} {r['league']:3s} {r['player'][:20]:20s} {r['team'] or '':4s} {r['stat'][:14]:14s} "
                  f"U{r['line']:<4} {r['p_model']:.2f}  {r['p_hist']:.2f}({r['hist_n']:>2}) {r['mean']:5.2f}  "
                  + (f"ROLE CHANGE: workload x{r['scale']:.2f} lately, capped at Low (L5); " if r["role_shift"] else "") + f"last {r['last']}")
        bad = [r for r in res if "error" in r]
        if bad:
            print(f"\nNot priced: {len(bad)} (" + "; ".join(f"{k} x{v}" for k, v in collections.Counter(r['error'] for r in bad).most_common()) + ")")
        if args.log:
            bets = L.read_bets()
            seen = {(b["player"].lower(), b["market"], str(float(b["line"])) if b["line"] else "", b["side"], b["date"]) for b in bets}
            nid = max(int(b["id"]) for b in bets if b["id"].isdigit()) + 1
            added = 0
            for r in ok:
                k = (r["player"].lower(), r["market"], str(float(r["line"])), "under", dt.date.today().isoformat())
                if k in seen:
                    continue
                bets.append({"id": str(nid), "date": dt.date.today().isoformat(), "sport": r["league"].lower(),
                             "event": f"{r['team']} vs {r['opp']}", "event_id": "", "player": r["player"], "player_id": r["player_id"],
                             "market": r["market"], "line": r["line"], "side": "under", "book": "PrizePicks standard",
                             "p_model": round(r["p_model"], 4), "p_hist": round(r["p_hist"], 4), "hist_n": r["hist_n"],
                             "p_final": round(r["p_final"], 4), "confidence": r["confidence"],
                             "action": "lean" if r["confidence"] == "High" else "pass", "segment": r["segment"],
                             "group": f"{r['league'].lower()}:{r['team']}-{r['opp']}", "status": "pending", "proj": round(r["mean"], 2),
                             "notes": f"edge lowline; per game {r['per_game']:.2f}, workload x{r['scale']:.2f}" + ("; ROLE CHANGE (L5)" if r["role_shift"] else "")
                                      + f"; last {r['last']}; start {r.get('start')}"})
                nid += 1
                added += 1
            L.write_bets(bets)
            print(f"Logged {added} new prop(s) to bets.csv.")
    elif args.cmd == "tennis":
        from . import tennis
        tennis.cli(args)
    elif args.cmd == "tag":
        if L.base_tag(args.reason) not in R.TAGS:
            print(f"note: '{args.reason}' is not a standard tag ({', '.join(R.TAGS)}); recorded anyway")
        rows = L.read_bets()
        for r in rows:
            if r["id"] == args.id:
                r["miss_reason"] = args.reason
        L.write_bets(rows)
        pms = R.read_pm()
        if args.lesson and args.id in pms:
            pms[args.id]["lesson"] = args.lesson
            R.write_pm(pms)
        R.render_md(pms, rows)
        print("tagged", args.id)


def _review(rows, ids, accept):
    pms = R.review(rows, ids)
    print(R.summary(pms))
    merged = R.merge(pms, R.read_pm())
    if accept:
        for pm in pms:
            for r in rows:
                if r["id"] == pm["id"] and not r.get("miss_reason"):
                    r["miss_reason"] = pm["auto_tag"]
        L.write_bets(rows)
    R.write_pm(merged)
    R.render_md(merged, rows)
    print(f"\nWrote {len(pms)} post-mortem(s) to data/postmortems.csv and POSTMORTEMS.md."
          + ("" if accept else " Confirm each cause: python -m edge tag <id> \"tag\" --lesson \"...\""))


if __name__ == "__main__":
    sys.exit(main())
