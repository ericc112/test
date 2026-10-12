"""CLI: python -m edge <command>   (run from the betting/ directory)

  report                       calibration, CLV, ROI, segment table, untagged misses
  grade                        settle pending bets from stat feeds, then report
  learn                        refit blend + segment bias from graded bets, append lessons
  prob  --model .6 --market .55 --hist .7 --hist-n 12 --segment mlb:pitcher_outs:over
  breakeven                    per-leg break-even for pick'em payout tables
  squad --means 245 283 207 --sds 70 78 65 --milestones 807 977 1044 --pair-corr 0 1 0.3
  add   key=value ...          append a bet (fields: see data/bets.csv header)
  tag   ID "reason"            record why a high-confidence pick missed
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

from . import grade as G
from . import learn as L
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
    t = sub.add_parser("tag")
    t.add_argument("id")
    t.add_argument("reason")
    args = ap.parse_args(argv)

    if args.cmd == "report":
        print(L.report(L.read_bets()))
    elif args.cmd == "grade":
        rows = L.read_bets()
        print(G.grade_rows(rows))
        L.write_bets(rows)
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
    elif args.cmd == "tag":
        rows = L.read_bets()
        for r in rows:
            if r["id"] == args.id:
                r["miss_reason"] = args.reason
        L.write_bets(rows)
        print("tagged", args.id)


if __name__ == "__main__":
    sys.exit(main())
