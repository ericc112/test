"""CLI: python -m edge <command>   (run from the betting/ directory)

  report                       calibration, CLV, ROI, segment table, untagged misses
  grade                        settle pending bets from stat feeds, then report
  learn                        refit blend + segment bias from graded bets, append lessons
  prob  --model .6 --market .55 --hist .7 --hist-n 12 --segment mlb:pitcher_outs:over
  breakeven                    per-leg break-even for pick'em payout tables
  squad --means 245 283 207 --sds 70 78 65 --milestones 807 977 1044 --pair-corr 0 1 0.3
  add   key=value ...          append a bet (fields: see data/bets.csv header)
  tag   ID "tag" [--lesson ".."] confirm the root cause of a loss (every loss) and what to change
  review [--all] [--accept]    post-mortem on every graded loss: feed detail, linked legs, suggested tag
  best  [--date D] [--min-p .65] [--legs 2]   top-tier legs, one per game script, best entry
  card  [--date D]               exposure check: legs riding on the same game script
  passes --player ID --team ID (--event ID | --opp ID [--home|--away]) --line 50.5   soccer passes attempted
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

from . import card as C
from . import grade as G
from . import learn as L
from . import review as R
from . import soccer as S
from .blend import final_probability, segment_key
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
    t = sub.add_parser("tag")
    t.add_argument("id")
    t.add_argument("reason")
    t.add_argument("--lesson", default="")
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
        print(f"p={e.p:.3f} (fair {fair_american(e.p):+d}) confidence={e.confidence} agreement={e.agreement} spread={e.spread:.3f}")
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
