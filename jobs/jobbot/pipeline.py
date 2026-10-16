"""Search all enabled sources, score what comes back, and decide what to apply to."""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from . import ats, db, scoring, sources

_search_lock = threading.Lock()


def _age_seconds(ts):
    try:
        then = datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None
    return (datetime.now(timezone.utc) - then).total_seconds()


def plan_fetches(search, force=False, only=None):
    """List (source, key) pairs to fetch now, plus the ones skipped for rate limits."""
    todo, skipped = [], []
    for name, mod in sources.REGISTRY.items():
        if not search.get("sources", {}).get(name):
            continue
        if only and name not in only:
            continue
        interval = mod.FORCE_MIN_INTERVAL if force else mod.MIN_INTERVAL
        for key in mod.keys(search):
            last = db.last_source_run(name, key)
            age = _age_seconds(last["ts"]) if last else None
            if last and last["ok"] and age is not None and age < interval:
                skipped.append({"source": name, "key": key, "wait_min": round((interval - age) / 60)})
            else:
                todo.append((name, key))
    return todo, skipped


def _dedupe(job):
    """Hide the same job listed on several boards, keeping the one we can apply to directly."""
    others = db.find_by_dedupe(job["dedupe_key"], job["id"])
    if not others:
        return
    mine_direct = job.get("ats") in ats.SUPPORTED
    for o in others:
        theirs_direct = o.get("ats") in ats.SUPPORTED
        if mine_direct and not theirs_direct and o["status"] == "new":
            db.update_job(o["id"], status="duplicate", status_note=f"Same as {job['id']}")
        elif o["status"] != "duplicate":
            db.update_job(job["id"], status="duplicate", status_note=f"Same as {o['id']}")
            return


def run_search(force=False, only=None):
    """Fetch, filter, score and store jobs. Returns a summary dict."""
    if not _search_lock.acquire(blocking=False):
        return {"busy": True}
    try:
        search = db.get_setting("search")
        profile = db.get_setting("profile")
        todo, skipped = plan_fetches(search, force, only)
        summary = {"fetched": [], "skipped": skipped, "errors": [], "new": 0, "kept": 0}
        db.log(f"Search started: {len(todo)} feeds" + (f", {len(skipped)} rate-limited" if skipped else ""))
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(sources.REGISTRY[n].fetch, k, search): (n, k) for n, k in todo}
            for fut in as_completed(futures):
                name, key = futures[fut]
                try:
                    jobs = fut.result()
                except Exception as e:  # one bad feed shouldn't stop the others
                    db.record_source_run(name, key, False, 0, str(e)[:300])
                    summary["errors"].append({"source": name, "key": key, "error": str(e)[:300]})
                    db.log(f"{name} ({key}) failed: {e}", "warn")
                    continue
                kept = new = 0
                for job in jobs:
                    if not job.get("title") or not scoring.relevant(job, search):
                        continue
                    s, reasons, excluded = scoring.score(job, search, profile)
                    if excluded:
                        continue
                    job["score"], job["score_reasons"] = s, reasons
                    if db.upsert_job(job):
                        new += 1
                        _dedupe(job)
                    kept += 1
                db.record_source_run(name, key, True, kept)
                summary["fetched"].append({"source": name, "key": key, "total": len(jobs), "kept": kept, "new": new})
                summary["new"] += new
                summary["kept"] += kept
        db.log(f"Search finished: {summary['new']} new, {summary['kept']} matching"
               + (f", {len(summary['errors'])} feed errors" if summary["errors"] else ""))
        return summary
    finally:
        _search_lock.release()


def rescore():
    """Recompute scores after you change your search or skills."""
    search = db.get_setting("search")
    profile = db.get_setting("profile")
    changed = 0
    for job in db.all_jobs_for_rescore():
        s, reasons, excluded = scoring.score(job, search, profile)
        fields = {"score": s, "score_reasons": reasons}
        note = job.get("status_note") or ""
        if excluded and job["status"] == "new":
            fields.update(status="skipped", status_note=f"auto: {excluded}")
        elif not excluded and job["status"] == "skipped" and note.startswith("auto:"):
            fields.update(status="new", status_note=None)
        db.update_job(job["id"], **fields)
        changed += 1
    return changed


# ------------------------------------------------------------------ automation policy

def can_auto_submit(job, attempt, automation):
    """Return (ok, reason). Auto-submit is deliberately conservative."""
    if not automation.get("auto_submit"):
        return False, "auto-submit is off"
    if job.get("ats") not in ats.SUPPORTED:
        return False, "only Greenhouse, Lever and Ashby forms are auto-submitted"
    if (job.get("score") or 0) < automation.get("submit_min_score", 75):
        return False, "score below auto-submit threshold"
    fields = (attempt or {}).get("fields") or []
    if any(f.get("source") == "ai" for f in fields) and not automation.get("auto_submit_ai_answers"):
        return False, "contains AI-written answers for you to review"
    if db.applied_since(24) >= automation.get("daily_limit", 15):
        return False, "daily limit reached"
    if db.applied_to_company_since(job.get("company"), 30) >= automation.get("company_limit_30d", 3):
        return False, f"already applied to {job.get('company')} recently"
    return True, ""


def auto_queue(enqueue, max_jobs=25):
    """Queue high-scoring new jobs for preparation (filling without submitting)."""
    automation = db.get_setting("automation")
    if not automation.get("auto_prepare"):
        return 0
    jobs, _ = db.list_jobs(
        statuses=["new"], min_score=automation.get("prepare_min_score", 60), sort="score", limit=max_jobs
    )
    for job in jobs:
        enqueue(job["id"], "prepare")
    if jobs:
        db.log(f"Queued {len(jobs)} matches to prepare")
    return len(jobs)


class Scheduler(threading.Thread):
    """Runs search + auto-queue every N hours while automation is enabled."""

    def __init__(self, enqueue):
        super().__init__(daemon=True, name="jobbot-scheduler")
        self.enqueue = enqueue
        self.stop_event = threading.Event()
        self.wake = threading.Event()
        self.next_run = None

    def run(self):
        while not self.stop_event.is_set():
            automation = db.get_setting("automation")
            if automation.get("enabled"):
                last = db.get_setting("last_auto_run")
                age = _age_seconds(last) if isinstance(last, str) else None
                interval = max(1.0, float(automation.get("interval_hours") or 6)) * 3600
                if age is None or age >= interval:
                    db.set_setting("last_auto_run", db.now())
                    try:
                        run_search()
                        auto_queue(self.enqueue)
                    except Exception as e:
                        db.log(f"Automatic run failed: {e}", "error")
                    age = 0
                self.next_run = interval - (age or 0)
            else:
                self.next_run = None
            self.wake.wait(timeout=60)
            self.wake.clear()

    def stop(self):
        self.stop_event.set()
        self.wake.set()
