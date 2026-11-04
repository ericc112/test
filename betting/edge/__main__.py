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
  nba-picks [--top 5] [--match DAL] [--no-log] [--no-verify]   tonight's best NBA PrizePicks legs with the write-up
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
from .blend import final_probability, segment_key
from .odds import fair_american
from .pickem import PAYOUTS, breakeven, squad_ride



def log_pp(rows: list[dict], action: dict | None = None, refresh: bool = False) -> list[tuple]:
    """Log priced PrizePicks props to bets.csv (skips ones already logged). `action` maps id(row) to an action
    ("lean", "pass", ...) to override the default. With `refresh`, a leg already logged and still pending is re-priced
    in place (the board still lists it, so it hasn't started: the not-started rule of `verify --fix`).
    Returns [(bet id, newly added)] in row order."""
    bets = L.read_bets()
    seen = {(b["event_id"], str(b["player"]).lower(), b["market"], str(float(b["line"])) if b["line"] else "", b["side"]): b["id"] for b in bets}
    by_id = {b["id"]: b for b in bets}
    nid = max(int(b["id"]) for b in bets if b["id"].isdigit()) + 1
    out = []
    rnd = lambda v: "" if v is None else round(v, 3)
    for r in rows:
        k = (str(r["event_id"]), str(r["player"]).lower(), r["market_key"], str(float(r["line"])), r["side"])
        if k in seen:
            b = by_id[seen[k]]
            if refresh and b.get("status") == "pending" and (abs(float(b["p_final"] or 0) - r["p_final"]) > 1e-4 or b.get("confidence") != r["confidence"]):
                b["notes"] = f"edge pp; {r['notes']} | re-priced {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ} (was {b.get('p_final')} {b.get('confidence')})"
                b.update({"p_model": rnd(r["p_model"]), "p_market": rnd(r["p_market"]), "p_hist": rnd(r["p_hist"]), "hist_n": r["hist_n"],
                          "p_final": r["p_final"], "confidence": r["confidence"], "proj": "" if r.get("proj") is None else round(r["proj"], 1),
                          "opp_proj": "" if r.get("opp_proj") is None else r["opp_proj"]})
                if action and action.get(id(r)):
                    b["action"] = action[id(r)]
            out.append((seen[k], False))
            continue
        bets.append({"id": str(nid), "date": dt.date.today().isoformat(), "sport": r["sport"], "event": f"{r['team']} vs {r['opp']}",
                     "event_id": r["event_id"], "player": r["player"], "player_id": r["player_id"], "market": r["market_key"],
                     "line": r["line"], "side": r["side"], "book": f"PrizePicks {r['odds_type']}", "p_model": "" if r["p_model"] is None else round(r["p_model"], 3),
                     "p_market": "" if r["p_market"] is None else round(r["p_market"], 3), "p_hist": "" if r["p_hist"] is None else round(r["p_hist"], 3),
                     "hist_n": r["hist_n"], "p_final": r["p_final"], "confidence": r["confidence"],
                     "action": (action or {}).get(id(r)) or ("lean" if r["confidence"] in ("High", "Medium") and not r.get("newcomer") else "pass"),
                     "segment": f"{r['sport']}:{r['market_key']}:{r['side']}", "group": r["script"], "status": "pending",
                     "proj": "" if r.get("proj") is None else round(r["proj"], 1),
                     "opp_proj": "" if r.get("opp_proj") is None else r["opp_proj"], "notes": f"edge pp; {r['notes']}"})
        seen[k] = str(nid)
        out.append((str(nid), True))
        nid += 1
    L.write_bets(bets)
    return out

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
    npk = sub.add_parser("nba-picks", help="today's best NBA PrizePicks legs, back-checked, with the research write-up")
    npk.add_argument("--top", type=int, default=5)
    npk.add_argument("--n", type=int, default=50000, help="simulations per game")
    npk.add_argument("--match", help="only games whose teams contain this text")
    npk.add_argument("--no-log", action="store_true", help="don't log to bets.csv (default: log the picks, every Medium+ leg and each game's best leg)")
    npk.add_argument("--no-verify", action="store_true")
    npk.add_argument("--out", help="write the report here (default data/picks/DATE-nba.md)")
    nf = sub.add_parser("nfl", help="NFL game simulator (ESPN box scores + DraftKings lines)")
    nf.add_argument("--event", help="ESPN event id (see --week)")
    nf.add_argument("--week", type=int, help="list a week's games with event ids and DraftKings lines")
    nf.add_argument("--season", type=int)
    nf.add_argument("--n", type=int, default=50000, help="simulations (default 50,000)")
    nf.add_argument("--out", nargs="*", default=[], help="extra inactive players by name (the injury report is read automatically)")
    nf.add_argument("--alt", nargs="*", default=[], help='app or alt lines to price, e.g. "Swift:rush_yds:52.5"')
    nf.add_argument("--player", help="only props for players whose name contains this")
    nf.add_argument("--all", action="store_true", help="show every prop, not just the top 30")
    nf.add_argument("--log", action="store_true", help="log every priced prop to bets.csv (skips ones already logged)")
    nf.add_argument("--backtest", help="replay finished weeks against DraftKings closing lines, e.g. 3-8")
    sl = sub.add_parser("simlab", help="write the data file for the browser simulator (Sim Lab)")
    sl.add_argument("--out", default="simlab_data.js")
    sl.add_argument("--week", type=int, help="NFL week (default: the next one with games to play)")
    sl.add_argument("--no-backtest", action="store_true", help="skip the ~40 s NFL backtest summary")
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
                r.update({k: f[k] for k in ("p_model", "p_market", "p_hist", "hist_n", "p_final", "confidence") if k in f})
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
        print(f"\n{'p':>5} {'conf':6s} {'player':16s} {'team':12s} {'stat':18s} {'side':5s} {'line':>5} {'type':8s} model mrkt hist(n)  notes")
        for r in ok:
            print(f"{r['p_final']:.3f} {r['confidence']:6s} {str(r['player'])[:16]:16s} {str(r['team'])[:12]:12s} {r['stat'][:18]:18s} {r['side']:5s} "
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
            added = len([1 for _, new in log_pp(ok) if new])
            print(f"Logged {added} new prop(s) to bets.csv.")
    elif args.cmd == "nba-picks":
        _nba_picks(args)
    elif args.cmd == "nfl":
        _nfl(args)
    elif args.cmd == "simlab":
        from . import simlab
        print(simlab.export(args.out, nfl_week=args.week, backtest_weeks=None if args.no_backtest else (3, 8)))
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


def _nba_picks(args):
    """Price tonight's NBA PrizePicks board, keep the best legs (one per game), back-check each, write the report."""
    import gzip
    import json
    import os
    from . import nba_pp as N
    from . import pp as P
    from . import verify as V
    from .blend import HERE, load_adjustments
    props = [p for p in P.board("NBA", ("standard", "goblin", "demon")) if p["stat"] in N.STATS]
    if args.match:
        props = [p for p in props if args.match.lower() in f"{p['team']} {p['opp']} {p['home']} {p['away']}".lower()]
    if not props:
        print("No NBA props on the PrizePicks board for the stats the simulation scores.")
        return
    print(f"Pricing {len(props)} NBA prop(s) ({sum(p['odds_type'] == 'standard' for p in props)} standard) with {args.n:,} runs per game...")
    rows = N.price_nba(props, n=args.n)
    ok = [r for r in rows if "error" not in r]
    today = dt.date.today().isoformat()
    os.makedirs(os.path.join(HERE, "data", "nba_boards"), exist_ok=True)
    with gzip.open(os.path.join(HERE, "data", "nba_boards", f"{today}.json.gz"), "wt") as f:     # the full priced board
        json.dump([{k: v for k, v in r.items() if k not in ("research", "dk")} for r in ok], f, default=float)
    picks = N.pick_order(ok, args.top)
    ids = {}
    if not args.no_log:
        best_game = {}
        for r in sorted([r for r in ok if r["odds_type"] == "standard"], key=lambda r: -r["p_final"]):
            best_game.setdefault(r["script"], r)
        keep = {id(r) for r in picks} | {id(r) for r in best_game.values()} | {id(r) for r in ok if r["odds_type"] == "standard" and r["confidence"] in ("High", "Medium")}
        logrows = [r for r in ok if id(r) in keep]
        pick_ids = {id(r) for r in picks}
        act = {id(r): (("lean" if r["confidence"] in ("High", "Medium") and not r.get("newcomer") else "pass") if id(r) in pick_ids else "pass")
               for r in logrows}          # only the published picks are leans; the rest are logged for calibration
        for r, (bid, _) in zip(logrows, log_pp(logrows, act, refresh=True)):
            ids[id(r)] = bid
        print(f"Logged {len(logrows)} leg(s) to bets.csv (picks, every Medium+ leg, each game's best leg); full board in data/nba_boards/{today}.json.gz")
    adj = load_adjustments()
    bets = L.read_bets()
    blocks = []
    for r in picks:
        ver, warns = "not checked", []
        if not args.no_verify and id(r) in ids:
            row = next(b for b in bets if b["id"] == ids[id(r)])
            rep = V.verify(row, bets, adj)
            ver = rep.verdict
            warns = [f"{n}: {d}" for st, n, d in rep.checks if st != "PASS"]
            print(rep.text())
        if id(r) in ids:
            r["bet_id"] = f"#{ids[id(r)]} "
        blocks.append(N.write_up(r, ver, warns))
    bias = N.model_market_bias(ok)
    n_std = sum(r["odds_type"] == "standard" for r in ok)
    head = [f"# NBA PrizePicks: best {len(picks)} legs, {today}",
            f"Board pulled {rows[0].get('pulled', '') if rows else ''} · {len(ok)} props priced ({n_std} standard) across {len({r['script'] for r in ok})} games · "
            f"{args.n:,} simulations per game · not priced: {len(rows) - len(ok)}",
            "",
            "Ranked by calibrated probability (model + DraftKings + this season, blended as `edge prob`), High before Medium, "
            "standard lines only, one leg per game. Entry rule (ANALYST_PROMPT): only High legs at 65%+ go in entries, two legs max; "
            "PrizePicks break-evens per leg: 2-pick power 57.7%, 3-pick power 58.5%, 5/6-pick flex 54.2%. These are model numbers, "
            "not locks: the NBA player model has not beaten DraftKings' prices out of sample (projection error 4.72 vs the line's 4.72 on Nov 2).",
            ""]
    if bias:
        head.append("Simulation vs DraftKings tonight, main lines (mean logit gap, taken out of the model before blending, L7): "
                    + ", ".join(f"{N.LABEL[k]} {v['bias_logit']:+.2f} (n {v['n']})" for k, v in sorted(bias.items())))
        head.append("")
    high = [r for r in picks if N.verdict(r).startswith("ENTRY")]
    if len(high) >= 2:
        head.append(f"**Best 2-leg entry:** {high[0]['player']} {high[0]['side']} {high[0]['line']} + {high[1]['player']} {high[1]['side']} {high[1]['line']} "
                    f"-> P(both) {high[0]['p_final'] * high[1]['p_final']:.1%} (2-pick power pays 3x; break-even 33.3%)")
    else:
        head.append("**No 2-leg entry clears the High gate tonight (65%+, one leg per game). Sitting out beats forcing it.**")
    head.append("")
    rest = [r for r in N.pick_order(ok, args.top + 10)[args.top:]]
    tail = ["", "## Next best", "| p | conf | player | stat | side | line | model | DK | history |", "|---|---|---|---|---|---|---|---|---|"]
    fm = lambda v: "-" if v is None else f"{v:.0%}"
    tail += [f"| {r['p_final']:.1%} | {r['confidence']} | {r['player']} ({r['team']}) | {N.LABEL[r['stat_key']]} | {r['side']} | {r['line']} | {fm(r['p_model'])} | {fm(r['p_market'])} | {fm(r['p_hist'])} ({r['hist_n']}) |" for r in rest]
    report = "\n".join(head) + "\n" + "\n\n".join(blocks) + "\n" + "\n".join(tail) + "\n"
    out = args.out or os.path.join(HERE, "data", "picks", f"{today}-nba.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(report)
    print("\n" + report)
    print(f"Report: {out}")


def _nfl(args):
    from . import nfl as N
    season = args.season or (dt.date.today().year if dt.date.today().month >= 3 else dt.date.today().year - 1)
    if args.week:
        for e in N.week_events(season, args.week):
            g = N.game(e["id"])
            line = f"{g['abbr'][g['home']]} {g['spread_home']:+g}, total {g['total']}" if g["spread_home"] is not None else "no line yet"
            print(f"{e['id']}  {e['date'][:16]}  {e['away_abbr']} @ {e['home_abbr']}  {e['status'].replace('STATUS_', '').lower():10s} {line}")
        return
    if args.backtest:
        a, _, b = args.backtest.partition("-")
        weeks = list(range(int(a), int(b or a) + 1))
        bt = N.backtest(season, weeks, n=min(args.n, 10000))
        s = bt["summary"]
        print(f"Backtest {season} weeks {weeks[0]}-{weeks[-1]}: {s['n']} DraftKings closing props (only earlier games used)")
        print(f"{'market':13s} {'n':>5s} {'avg miss: sim':>14s} {'DK line':>8s} {'Brier sim':>10s} (0.250 = line as a coin flip)")
        for mk, v in s["by_market"].items():
            dk = "       -" if mk == "anytime_td" else f"{v['mae_line']:8.2f}"   # a TD 'line' of 0.5 isn't a forecast
            print(f"{mk:13s} {v['n']:5d} {v['mae_median']:14.2f} {dk} {v['brier_model']:10.3f}")
        print("Calibration of the raw simulation at the DK line (side it favours: predicted -> actual):")
        for lo, hi, n, pm, hit in s["calibration"]:
            print(f"  {lo:.2f}-{min(hi, 1):.2f}  n={n:5d}  {pm:.1%} -> {hit:.1%}")
        print("Suggested MODEL_SHRINK (paste into edge/nfl.py only after a full-season look):", N.fit_shrink(bt["records"]))
        return
    if not args.event:
        print("Give --event ID (find it with --week N) or --backtest 3-8.")
        return
    alt = []
    for a in args.alt:
        name, mk, ln = a.rsplit(":", 2)
        alt.append((name, mk, float(ln)))
    r = N.price_game(args.event, n=args.n, season=args.season, out_names=args.out, alt=alt)
    g, sim = r["target"], r["sim"]
    print(f"{g['abbr'][g['away']]} @ {g['abbr'][g['home']]}  DraftKings {g['abbr'][g['home']]} {g['spread_home']:+g}, total {g['total']}"
          f"  | {args.n:,} simulations from {r['history_games']} earlier games")
    for tid, t in sim["teams"].items():
        print(f"  {t['abbr']}: implied {sim['meta']['implied'][tid]:.1f}, sim {t['points'].mean():.1f} pts, win {np.mean(t['margin'] > 0):.1%}, "
              f"opening drive scores {np.mean(t['first_drive_score']):.1%}, {t['plays'].mean():.0f} plays, {t['pass_att'].mean():.1f} att / {t['car'].mean():.1f} car")
    if sim["meta"]["out_ids"]:
        print(f"  inactive (injury report Out/Doubtful, or --out): {len(sim['meta']['out_ids'])} player(s) removed, volume redistributed")
    rows = [x for x in r["rows"] if not args.player or args.player.lower() in x["player"].lower()]
    shown = rows if args.all else rows[:30]
    print(f"\n{'p':>5} {'conf':6s} {'player':20s} {'tm':3s} {'market':12s} {'side':5s} {'line':>6} {'median':>7} {'sim':>5} {'cal':>5} {'hist(n)':>8}  flags")
    for x in shown:
        h = "  - " if x["p_hist"] is None else f"{x['p_hist']:.2f}"
        print(f"{x['p_final']:.3f} {x['confidence']:6s} {x['player'][:20]:20s} {x['team']:3s} {x['market']:12s} {x['side']:5s} {x['line']:6g} "
              f"{x['median']:7.1f} {x['p_sim']:.2f} {x['p_model']:.2f} {h}({x['hist_n']})  {'; '.join(x['flags'])}")
    if len(rows) > len(shown):
        print(f"... {len(rows) - len(shown)} more (--all)")
    for a in r["alts"]:
        src = f"centred on DK {a['dk_line']}" if a["anchored"] else "no DK line: raw simulation"
        print(f"ALT {a['player']} {a['market']} {a['line']}: over {a['p_over']:.1%} / under {a['p_under']:.1%} ({src})")
    print("\nsim = raw simulated P; cal = shrunk toward the line by the backtest weight (what goes into the blend).")
    print("The NFL feed carries DraftKings lines but no prices, so there is no market component: no label above Medium,")
    print("and every pick still needs `python -m edge verify ID` before it is named.")
    if args.log:
        bets = L.read_bets()
        seen = {(b["event_id"], str(b["player_id"]), b["market"], str(float(b["line"])) if b["line"] else "", b["side"]) for b in bets}
        nid = max(int(b["id"]) for b in bets if b["id"].isdigit()) + 1
        added = 0
        ev = f"{g['abbr'][g['away']]} @ {g['abbr'][g['home']]}"
        for x in r["rows"]:
            k = (str(g["event_id"]), str(x["player_id"]), x["market"], str(float(x["line"])), x["side"])
            if k in seen or "not priced" in " ".join(x["flags"]):
                continue
            vol = x.get("volume")
            bets.append({"id": str(nid), "date": dt.date.today().isoformat(), "sport": "nfl", "event": ev, "event_id": g["event_id"],
                         "player": x["player"], "player_id": x["player_id"], "market": x["market"], "line": x["line"], "side": x["side"],
                         "book": "DraftKings line (no price)", "p_model": x["p_model"], "p_market": "",
                         "p_hist": "" if x["p_hist"] is None else x["p_hist"], "hist_n": x["hist_n"], "p_final": x["p_final"],
                         "confidence": x["confidence"], "action": "lean" if x["confidence"] in ("High", "Medium") else "pass",
                         "segment": f"nfl:{x['market']}:{x['side']}", "group": f"nfl-{g['event_id']}", "status": "pending",
                         "proj": round(x["median"], 1), "opp_proj": "" if vol is None else round(vol[1], 1),
                         "notes": f"edge nfl ({args.n} sims); raw sim {x['p_sim']}; DK line {x['line']} (open {x.get('open')})"
                                  + (f"; {'; '.join(x['flags'])}" if x["flags"] else "")})
            nid += 1
            added += 1
        L.write_bets(bets)
        print(f"Logged {added} new prop(s) to bets.csv.")


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
