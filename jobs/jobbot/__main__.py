"""Command line: `python -m jobbot` starts the web app; other commands run single steps."""
import argparse
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path

from . import config, db, pipeline


def cmd_serve(args):
    import uvicorn

    from .server import create_app

    if args.phone_address:
        from . import phone
        phone.ADDRESS, args.phone = args.phone_address, True
    if args.phone:
        args.host = "0.0.0.0"
    elif args.host not in ("127.0.0.1", "localhost"):
        print("Warning: JobBot has no login. Anyone who can reach this address sees your profile "
              "and can submit applications as you. Use --phone for a private link instead.", file=sys.stderr)
    url = f"http://{'localhost' if args.host in ('0.0.0.0', '127.0.0.1') else args.host}:{args.port}"
    print(f"JobBot running at {url}  (data in {config.DATA_DIR})")
    if args.phone:
        from . import phone
        link = phone.link(args.port)
        where = "" if args.phone_address else " (same Wi-Fi)"
        print(f"\nPhone access is on. On your phone{where}, scan this or open the link:\n")
        phone.qr_terminal(link)
        print(f"\n  {link}\n\nKeep it private: it signs a device in. The same QR is in Automation & AI on this computer.")
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    extra = [] if args.host in ("127.0.0.1", "localhost", "0.0.0.0") else [args.host]
    uvicorn.run(create_app(extra_hosts=extra, phone_access=args.phone), host=args.host, port=args.port, log_level="warning")


def cmd_search(args):
    summary = pipeline.run_search(force=args.force)
    for f in sorted(summary.get("fetched", []), key=lambda x: x["source"]):
        print(f"  {f['source']:<11} {f['key'][:30]:<30} {f['kept']:>4} matching, {f['new']:>4} new")
    for s in summary.get("skipped", []):
        print(f"  {s['source']:<11} {s['key'][:30]:<30} skipped (rate limit, {s['wait_min']} min left)")
    for e in summary.get("errors", []):
        print(f"  {e['source']:<11} {e['key'][:30]:<30} ERROR {e['error']}")
    print(f"{summary.get('new', 0)} new jobs, {summary.get('kept', 0)} matching")


def cmd_list(args):
    jobs, total = db.list_jobs(statuses=args.status.split(",") if args.status else None, limit=args.limit)
    for j in jobs:
        print(f"{int(j['score'] or 0):>3}  {j['status']:<11} {(j['ats'] or '-'):<10} {j['title'][:48]:<48} {j['company'][:22]:<22} {j['id']}")
    print(f"{total} total")


def _run_one(job_id, mode):
    from .worker import Worker
    w = Worker()
    w.process(job_id, mode)
    job = db.get_job(job_id)
    att = db.latest_attempt(job_id)
    print(f"{job['status']}: {job.get('status_note') or ''}")
    if att:
        for m in att["missing"]:
            print(f"  needs answer: {m['label']}")
        if att.get("screenshot"):
            print(f"  screenshot: {config.SHOTS_DIR / att['screenshot']}")


def cmd_prepare(args):
    _run_one(args.job_id, "prepare")


def cmd_submit(args):
    _run_one(args.job_id, "submit")


SOURCE_NAMES = {"the muse": "themuse", "remote ok": "remoteok"}


def cmd_apply_batch(args):
    """Fill (or submit) a list of applications and write the results as JSON.

    Used by the cloud runner behind the JobBot page: requests come from the page's Apply
    button, and the results go back to it. Results are saved after each request. Each request:
    {"k", "mode": "prepare"|"submit", "title", "company", "url", "source", "location", "answers": {question: answer},
     "ai_answers": {question: answer}}. "ai_answers" are ones Claude wrote (the cloud runner answers what JobBot
    couldn't, as llm.SYSTEM says); they're used like "answers", which win over them, and are labelled AI.
    """
    import shutil
    import time
    from pathlib import Path

    from .server import extract_text
    from .textutil import norm
    from .worker import Worker

    started = time.monotonic()
    if getattr(args, "data", None):
        config.use_data_dir(args.data)
    requests = json.load(open(args.requests))
    profile = db.get_setting("profile")
    if args.profile:
        mine = json.load(open(args.profile))
        profile.update({k: v for k, v in mine.items() if k in config.DEFAULT_PROFILE and v not in (None, "")})
        # Your answer bank, kept with your profile on the page: it goes first, so it wins over JobBot's defaults.
        bank = [b for b in mine.get("answer_bank") or [] if isinstance(b, dict) and b.get("q") and "a" in b]
        if bank:
            ours = {b["q"] for b in bank}
            db.set_setting("answers", bank + [b for b in db.get_setting("answers") if b["q"] not in ours])
    if args.resume:
        src = Path(args.resume)
        config.ensure_dirs()
        shutil.copy(src, config.FILES_DIR / src.name)
        profile["resume_file"], profile["resume_text"] = src.name, extract_text(config.FILES_DIR / src.name)
    db.set_setting("profile", profile)
    worker, results = Worker(), []
    limit = getattr(args, "time_limit", 0) or 0
    for r in requests:
        mode = "submit" if r.get("mode") == "submit" else "prepare"
        if limit and results and time.monotonic() - started > limit:
            # Out of time: leave it for the next run rather than get cut off halfway through a form.
            results.append({"k": r["k"], "mode": mode, "status": "not_started", "note": "", "fields": [], "missing": [],
                            "screenshot": None})
            _write_json(args.out, results)
            continue
        src = (r.get("source") or "page").strip().lower()
        job = {"id": r["k"], "source": SOURCE_NAMES.get(src, src.replace(" ", "")), "title": r.get("title") or "",
               "company": r.get("company") or "", "url": r.get("url"), "apply_url": r.get("url"), "location": r.get("location") or "",
               "dedupe_key": r["k"], "posted_at": None}
        db.upsert_job(job)
        ai = {norm(q) for q in r.get("ai_answers") or {}} - {norm(q) for q in r.get("answers") or {}}
        db.update_job(r["k"], answers=dict(r.get("ai_answers") or {}, **(r.get("answers") or {})), status="new")
        print(f"{mode}: {job['title']} at {job['company']}", flush=True)
        try:
            worker.process(r["k"], mode)
        except Exception as e:  # one failure shouldn't stop the batch
            db.update_job(r["k"], status="error", status_note=str(e)[:300])
        done, att = db.get_job(r["k"]), db.latest_attempt(r["k"], mode)
        shot = att and att.get("screenshot")
        fields = [{k: f.get(k) for k in ("label", "answer", "source", "note", "required", "site_value")} for f in (att or {}).get("fields", [])]
        for f in fields:
            if f["source"] == "user" and norm(f["label"] or "") in ai:
                f["source"] = "ai"
        results.append({
            "k": r["k"], "mode": mode, "status": done["status"], "note": done.get("status_note") or "",
            "title": done.get("title") or "", "company": done.get("company") or "", "apply_url": done.get("apply_url") or "",
            "fields": fields,
            "missing": [{k: m.get(k) for k in ("label", "kind", "options", "note")} for m in (att or {}).get("missing", [])],
            "screenshot": str(config.SHOTS_DIR / shot) if shot else None,
        })
        print(f"  -> {done['status']}: {done.get('status_note') or ''}", flush=True)
        _write_json(args.out, results)  # after each one: a run cut off midway keeps what it finished
    _write_json(args.out, results)
    print(f"wrote {len(results)} result(s) to {args.out}")


def _write_json(path, data):
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


def cmd_page_feed(args):
    from . import pagefeed
    meta = pagefeed.run(args.out, args.previous, args.search, args.profile, args.min_score)
    print(f"{meta['total']} internships ({meta['in_reach']} in the US or remote) in {meta['pages']} pages; "
          f"{meta['dropped_old']} older than {meta['max_age_days']} days and {meta['below_min_score']} scoring under "
          f"{meta['min_score']} left out. Written to {args.out}")


def cmd_coverage(args):
    """The Fortune 500, honestly: how many companies JobBot reads, why the rest aren't read, and
    which watched feeds failed on their last run (per company, from the recorded source runs)."""
    from collections import Counter
    rows = config.FORTUNE500
    runs = {(r["source"], r["key"]): r for r in db.source_runs()}
    watched = [r for r in rows if r.get("status") == "watched"]
    unsupported = [r for r in rows if r.get("status") == "unsupported"]
    missing = [r for r in rows if r.get("status") not in ("watched", "unsupported")]
    failed = [{"company": r["name"], "feed": f"{kind}:{slug}", "error": (runs[(kind, slug)]["error"] or "")[:200],
               "when": runs[(kind, slug)]["ts"]}
              for r in watched for kind, slug in r.get("feeds", []) if (kind, slug) in runs and not runs[(kind, slug)]["ok"]]
    report = {"companies": len(rows), "watched": len(watched), "unsupported": len(unsupported),
              "unsupported_systems": dict(Counter(s for r in unsupported for s in r.get("systems", []) if s)),
              "no_public_feed": len(missing), "feeds_failing": failed}
    print(f"{report['companies']} Fortune 500 companies: {report['watched']} watched, "
          f"{report['unsupported']} on job systems JobBot can't read yet "
          f"({', '.join(f'{k} {v}' for k, v in sorted(report['unsupported_systems'].items()))}), "
          f"{report['no_public_feed']} with no public feed found")
    for f in failed:
        print(f"  failing feed: {f['company']} ({f['feed']}) — {f['error']}")
    if not failed:
        print("  no failing feeds in the last recorded search")
    if args.out:
        _write_json(args.out, report)


def _board_status(row):
    """Map a Claude-board status onto a local JobBot status. The local app has no "removed"
    status: its equivalent is "skipped" (dismissed by you, restorable back to new)."""
    status = row.get("status")
    if status == "applied":
        return "applied"
    if status == "removed":
        return "skipped"
    if status == "applying":
        return "needs_input" if row.get("needsNote") else "queued"
    return "new"


def cmd_import_board(args):
    """Import jobs from a Muse board export (the hosted page's JSON: {"jobs": [...], "profile": {...}}).

    Dedupes by URL, then by company+title when a job has no URL. Nothing is fetched and
    nothing is applied to — this only fills the local database from the board's records."""
    from .sources import company_key, make_job
    from .textutil import norm

    data = json.loads(Path(args.file).read_text())
    rows = data.get("jobs") or []
    seen_urls, seen_keys = set(), set()
    for j in db.all_jobs_for_rescore():
        if j.get("url"):
            seen_urls.add(j["url"])
        seen_keys.add((company_key(j.get("company") or ""), norm(j.get("title") or "")))
    inserted, skipped, by_status = 0, 0, {}
    for row in rows:
        url = row.get("url") or None
        key = (company_key(row.get("company") or ""), norm(row.get("title") or ""))
        if (url and url in seen_urls) or key in seen_keys:
            skipped += 1
            continue
        status = _board_status(row)
        notes = []
        if row.get("term"):
            notes.append(f"Term: {row['term']}")
        if row.get("note"):
            notes.append(str(row["note"]))
        if row.get("needsNote"):
            notes.append(str(row["needsNote"]))
        if status == "applied" and row.get("appliedAt"):
            notes.append("Imported from Claude board — verified submission")
        if row.get("status") == "removed":
            notes.append("Removed on the Claude board")
        job = make_job("board", str(row.get("id")), row.get("title") or "", row.get("company") or "", url,
                       location=", ".join(row.get("locations") or []),
                       pay_text=row.get("payText"), pay_min=row.get("payMin"), pay_max=row.get("payMax"),
                       posted_at=row.get("postedAt"), status=status,
                       status_note="; ".join(notes) or None,
                       applied_at=row.get("appliedAt") if status == "applied" else None)
        if db.upsert_job(job):
            inserted += 1
            by_status[status] = by_status.get(status, 0) + 1
            if url:
                seen_urls.add(url)
            seen_keys.add(key)
        else:
            skipped += 1
    breakdown = ", ".join(f"{n} {s}" for s, n in sorted(by_status.items())) or "none"
    print(f"Imported {inserted} jobs ({breakdown}); {skipped} already in JobBot, skipped")


def cmd_pay(args):
    """Fill the stored pay fields (pay_text/pay_min/pay_max — the export's payText/payMin/payMax)
    for jobs that have none, extracting what the posting itself states. Code only, no AI:
    per-hour pay gets hourly numbers, any other period stays as the written text."""
    from . import pay
    jobs = db.all_jobs_for_rescore()
    have = sum(1 for j in jobs if j.get("pay_text"))
    filled = 0
    for job in jobs:
        if job.get("pay_text"):
            continue
        found = pay.for_job(job)
        if not found:
            continue
        db.update_job(job["id"], pay_text=found[0], pay_min=found[1], pay_max=found[2])
        filled += 1
    print(f"{filled} jobs got pay ({have} already had it, {len(jobs) - have - filled} still list none)")


def cmd_read_listings(args):
    from . import listings
    text = Path(args.text).read_text(encoding="utf-8") if args.text else None
    links = json.loads(Path(args.links).read_text()) if args.links else None
    result = listings.run(args.files, text, links, args.min_score, db.get_setting("search") or None, find=not args.no_find)
    page = lambda l: {"t": l["title"], "c": l["company"], "l": l["location"], "p": l["posted"], "s": l["score"],  # noqa: E731
                      "u": l.get("url") or "", "a": l.get("area") or "", "why": l.get("why") or ""}
    out = {"read": result["read"], "kept": [page(l) for l in result["kept"]],
           "dropped": [page(l) for l in result["dropped"]], "errors": result["errors"]}
    for l in out["kept"]:
        where = l["u"] or l["why"]
        print(f"keep {str(l['s'] if l['s'] is not None else '-'):>3}  {l['t'][:44]:<44} {l['c'][:22]:<22} {where[:70]}")
    for l in out["dropped"]:
        print(f"drop {str(l['s'] if l['s'] is not None else '-'):>3}  {l['t'][:44]:<44} {l['c'][:22]:<22} {l['why']}")
    for e in out["errors"]:
        print(f"error {e['file']}: {e['why']}")
    print(f"{out['read']} listings read, {len(out['kept'])} kept"
          + (f", {sum(1 for l in out['kept'] if l['u'])} found on the employer's site" if not args.no_find else ""))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=1)


def cmd_settings(args):
    if args.value is None:
        print(json.dumps(db.get_setting(args.key), indent=2))
    else:
        db.set_setting(args.key, json.loads(args.value))
        print("saved")


def main(argv=None):
    p = argparse.ArgumentParser(prog="jobbot", description="Search job boards and apply for you.")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("serve", help="start the web app (default)")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--no-browser", action="store_true")
    s.add_argument("--phone", action="store_true", help="also open JobBot on your phone (same Wi-Fi) with a private link")
    s.add_argument("--phone-address", metavar="ADDRESS",
                   help="address your phone uses to reach this computer, e.g. its Tailscale name (implies --phone)")
    s.set_defaults(fn=cmd_serve)
    s = sub.add_parser("search", help="fetch jobs from all enabled sources once")
    s.add_argument("--force", action="store_true", help="ignore the normal refresh interval")
    s.set_defaults(fn=cmd_search)
    s = sub.add_parser("list", help="list stored jobs")
    s.add_argument("--status", default="")
    s.add_argument("--limit", type=int, default=40)
    s.set_defaults(fn=cmd_list)
    s = sub.add_parser("prepare", help="fill a job's application without submitting")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_prepare)
    s = sub.add_parser("submit", help="fill and submit a job's application")
    s.add_argument("job_id")
    s.set_defaults(fn=cmd_submit)
    s = sub.add_parser("apply-batch", help="fill or submit a list of applications (JSON in, JSON out)")
    s.add_argument("requests")
    s.add_argument("--profile", help="your profile as JSON (JobBot profile fields)")
    s.add_argument("--resume", help="your resume file")
    s.add_argument("--out", default="results.json")
    s.add_argument("--data", help="data folder for this run (instead of JOBBOT_DATA)")
    s.add_argument("--time-limit", type=float, default=0,
                   help="seconds; don't start another application after this (the rest come back not_started)")
    s.set_defaults(fn=cmd_apply_batch)
    s = sub.add_parser("page-feed", help="build the JobBot page's internship list (meta.json and pages/p*.json)")
    s.add_argument("--out", required=True, help="folder for meta.json and pages/")
    s.add_argument("--previous", help="folder holding the page's current jobs documents (keeps first-seen times)")
    s.add_argument("--search", action="store_true", help="search every watched feed first")
    s.add_argument("--profile", help="your profile as JSON (scores use your skills and terms)")
    s.add_argument("--min-score", type=int, default=0, help="leave out listings scoring under this (0-100)")
    s.set_defaults(fn=cmd_page_feed)
    s = sub.add_parser("coverage", help="which Fortune 500 companies JobBot can read, and which feeds are failing")
    s.add_argument("--out", help="also write the report as JSON here")
    s.set_defaults(fn=cmd_coverage)
    s = sub.add_parser("pay", help="fill stored pay for jobs that list none, from what the posting states (no AI)")
    s.set_defaults(fn=cmd_pay)
    s = sub.add_parser("import-board", help="import jobs from a Muse board export (JSON)")
    s.add_argument("file", help="the board export file ({\"jobs\": [...], \"profile\": {...}})")
    s.set_defaults(fn=cmd_import_board)
    s = sub.add_parser("read-listings", help="read job listings from screenshots, a screen recording, a PDF or text")
    s.add_argument("files", nargs="*", help="screenshots (PNG, JPG), recordings (MP4, MOV), PDFs, saved pages or text files")
    s.add_argument("--text", help="a text file of listings copied from a job board")
    s.add_argument("--links", help='JSON list of {"t": link text, "u": url} copied with the text')
    s.add_argument("--min-score", type=int, default=90, help="leave out listings the board scored under this (default 90)")
    s.add_argument("--no-find", action="store_true", help="don't look for each job on the employer's site")
    s.add_argument("--out", help="write the listings as JSON here")
    s.set_defaults(fn=cmd_read_listings)
    s = sub.add_parser("settings", help="show or set a settings block as JSON")
    s.add_argument("key", choices=["profile", "answers", "search", "automation", "llm"])
    s.add_argument("value", nargs="?")
    s.set_defaults(fn=cmd_settings)
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0].startswith("-") and argv[0] not in ("-h", "--help"):
        argv = ["serve", *argv]  # `python -m jobbot --phone` means `serve --phone`
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
