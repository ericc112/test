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

    if args.host not in ("127.0.0.1", "localhost"):
        print("Warning: JobBot has no login. Anyone who can reach this address sees your profile "
              "and can submit applications as you.", file=sys.stderr)
    url = f"http://{'localhost' if args.host in ('0.0.0.0', '127.0.0.1') else args.host}:{args.port}"
    print(f"JobBot running at {url}  (data in {config.DATA_DIR})")
    if not args.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    extra = [] if args.host in ("127.0.0.1", "localhost", "0.0.0.0") else [args.host]
    uvicorn.run(create_app(extra_hosts=extra), host=args.host, port=args.port, log_level="warning")


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
    s = sub.add_parser("settings", help="show or set a settings block as JSON")
    s.add_argument("key", choices=["profile", "answers", "search", "automation", "llm"])
    s.add_argument("value", nargs="?")
    s.set_defaults(fn=cmd_settings)
    args = p.parse_args(argv)
    if not args.cmd:
        args = p.parse_args(["serve", *(argv or sys.argv[1:])])
    args.fn(args)


if __name__ == "__main__":
    main()
