"""Command line: `python -m jobbot` starts the web app; other commands run single steps."""
import argparse
import json
import sys
import threading
import webbrowser

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

    Used by the cloud runner behind the JobBot page: requests come from the page's
    "Apply for me" and "Submit" buttons, and the results go back to it. Each request:
    {"k", "mode": "prepare"|"submit", "title", "company", "url", "source", "answers": {question: answer}}.
    """
    import shutil
    from pathlib import Path

    from .server import extract_text
    from .worker import Worker

    requests = json.load(open(args.requests))
    profile = db.get_setting("profile")
    if args.profile:
        mine = json.load(open(args.profile))
        profile.update({k: v for k, v in mine.items() if k in config.DEFAULT_PROFILE and v not in (None, "")})
    if args.resume:
        src = Path(args.resume)
        config.ensure_dirs()
        shutil.copy(src, config.FILES_DIR / src.name)
        profile["resume_file"], profile["resume_text"] = src.name, extract_text(config.FILES_DIR / src.name)
    db.set_setting("profile", profile)
    worker, results = Worker(), []
    for r in requests:
        mode = "submit" if r.get("mode") == "submit" else "prepare"
        src = (r.get("source") or "page").strip().lower()
        job = {"id": r["k"], "source": SOURCE_NAMES.get(src, src.replace(" ", "")), "title": r.get("title") or "",
               "company": r.get("company") or "", "url": r.get("url"), "apply_url": r.get("url"),
               "dedupe_key": r["k"], "posted_at": None}
        db.upsert_job(job)
        db.update_job(r["k"], answers=r.get("answers") or {}, status="new")
        print(f"{mode}: {job['title']} at {job['company']}", flush=True)
        try:
            worker.process(r["k"], mode)
        except Exception as e:  # one failure shouldn't stop the batch
            db.update_job(r["k"], status="error", status_note=str(e)[:300])
        done, att = db.get_job(r["k"]), db.latest_attempt(r["k"], mode)
        shot = att and att.get("screenshot")
        results.append({
            "k": r["k"], "mode": mode, "status": done["status"], "note": done.get("status_note") or "",
            "fields": [{k: f.get(k) for k in ("label", "answer", "source", "note", "required")} for f in (att or {}).get("fields", [])],
            "missing": [{k: m.get(k) for k in ("label", "kind", "options", "note")} for m in (att or {}).get("missing", [])],
            "screenshot": str(config.SHOTS_DIR / shot) if shot else None,
        })
        print(f"  -> {done['status']}: {done.get('status_note') or ''}", flush=True)
    json.dump(results, open(args.out, "w"), indent=1)
    print(f"wrote {len(results)} result(s) to {args.out}")


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
    s.set_defaults(fn=cmd_apply_batch)
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
