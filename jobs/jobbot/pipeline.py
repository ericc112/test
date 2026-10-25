"""Search all enabled sources, score what comes back, and decide what to apply to."""
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from . import ats, db, pay, scoring, sources
from .sources import http

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


def _is_direct(job):
    """Straight from the employer's own job system (vs. an aggregator's copy)."""
    return job.get("ats") in ats.SUPPORTED or job.get("source") in sources.EMPLOYER


def _dedupe(job):
    """Hide the same job listed on several boards, keeping the employer's own listing.

    Same-title postings on one board are separate openings (other teams or cities), so
    only copies from a different source count as duplicates.
    """
    others = [o for o in db.find_by_dedupe(job["dedupe_key"], job["id"]) if o["source"] != job["source"]]
    if not others:
        return
    mine_direct = _is_direct(job)
    for o in others:
        if mine_direct and not _is_direct(o) and o["status"] == "new":
            db.update_job(o["id"], status="duplicate", status_note=f"Same as {job['id']}")
        elif o["status"] != "duplicate":
            db.update_job(job["id"], status="duplicate", status_note=f"Same as {o['id']}")
            return


_feed_locks = {}
_feed_locks_guard = threading.Lock()
_filtered_out = set()  # fetched with details but didn't match: don't fetch details again this session


def search_changed():
    """Your search or profile changed: look at every board's jobs afresh on the next check."""
    _filtered_out.clear()
    http.forget_etags()
    sources.REGISTRY["workday"]._looked_at.clear()


def _feed_lock(name, key):
    with _feed_locks_guard:
        return _feed_locks.setdefault((name, key), threading.Lock())


def poll_feed(name, key, search, profile):
    """Fetch one feed, store what matches, and report what's new.

    Jobs that appear on an employer board after JobBot's first look at it are
    marked fresh: they were just published.
    """
    mod = sources.REGISTRY[name]
    result = {"source": name, "key": key, "total": 0, "kept": 0, "new": 0, "fresh": [], "not_modified": False}
    lock = _feed_lock(name, key)
    if not lock.acquire(blocking=False):
        result["busy"] = True
        return result
    try:
        last = db.last_source_run(name, key)
        first_look = not (last and last["ok"])
        kwargs = {}
        if getattr(mod, "INCREMENTAL", False):
            kwargs["known"] = db.known_ids(sources.id_prefix(name, key)) | _filtered_out
        try:
            jobs = mod.fetch(key, search, **kwargs)
        except http.NotModified:
            db.record_source_run(name, key, True, last["count"] if last else 0)
            result["not_modified"] = True
            return result
        except Exception as e:
            db.record_source_run(name, key, False, 0, str(e)[:300])
            raise
        result["total"] = len(jobs)
        for job in jobs:
            if not job.get("title") or not scoring.relevant(job, search):
                _filtered_out.add(job.get("id"))
                continue
            s, reasons, excluded = scoring.score(job, search, profile)
            if excluded:
                _filtered_out.add(job.get("id"))
                continue
            job["score"], job["score_reasons"] = s, reasons
            found_pay = pay.for_job(job)  # pay stated in the posting, stored mechanically (no AI)
            if found_pay:
                job["pay_text"], job["pay_min"], job["pay_max"] = found_pay
            job["fresh"] = 0 if first_look or not getattr(mod, "EMPLOYER", False) else 1
            if db.upsert_job(job):
                result["new"] += 1
                _dedupe(job)
                if job["fresh"]:
                    result["fresh"].append(job)
            result["kept"] += 1
        if getattr(mod, "INCREMENTAL", False):  # these return only new jobs; report the board's total
            count = len(db.known_ids(sources.id_prefix(name, key)))
        else:
            count = result["kept"]
        db.record_source_run(name, key, True, count)
        return result
    finally:
        lock.release()


def run_search(force=False, only=None, skip=()):
    """Fetch, filter, score and store jobs from every enabled feed. Returns a summary dict."""
    if not _search_lock.acquire(blocking=False):
        return {"busy": True}
    try:
        search = db.get_setting("search")
        profile = db.get_setting("profile")
        todo, skipped = plan_fetches(search, force, only)
        todo = [(n, k) for n, k in todo if n not in skip]
        summary = {"fetched": [], "skipped": skipped, "errors": [], "new": 0, "kept": 0}
        db.log(f"Search started: {len(todo)} feeds" + (f", {len(skipped)} rate-limited" if skipped else ""))
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(poll_feed, n, k, search, profile): (n, k) for n, k in todo}
            for fut in as_completed(futures):
                name, key = futures[fut]
                try:
                    r = fut.result()
                except Exception as e:  # one bad feed shouldn't stop the others
                    summary["errors"].append({"source": name, "key": key, "error": str(e)[:300]})
                    db.log(f"{name} ({key}) failed: {e}", "warn")
                    continue
                summary["fetched"].append({k: r[k] for k in ("source", "key", "total", "kept", "new", "not_modified")})
                summary["new"] += r["new"]
                summary["kept"] += r["kept"]
                _announce(r["fresh"])
        db.log(f"Search finished: {summary['new']} new, {summary['kept']} matching"
               + (f", {len(summary['errors'])} feed errors" if summary["errors"] else ""))
        return summary
    finally:
        _search_lock.release()


def _ago(ts):
    age = _age_seconds(ts)
    if age is None:
        return ""
    if age < 3600:
        return f"{max(1, round(age / 60))} min ago"
    if age < 86400:
        return f"{round(age / 3600)} h ago"
    return f"{round(age / 86400)} d ago"


def _announce(fresh):
    for job in fresh:
        when = f", posted {_ago(job['posted_at'])}" if job.get("posted_at") and job.get("source") != "workday" else ""
        db.log(f"Just posted at {job['company']}: {job['title']}{when}", job_id=job["id"])


def rescore():
    """Recompute scores after you change your search or skills. The scheduler also runs this
    on every automatic run, so postings that vanish from a feed age out through the same
    exclusion rules instead of lingering as "new" forever. Nothing is deleted: a job only
    moves new -> skipped (and back to new if it qualifies again)."""
    search = db.get_setting("search")
    profile = db.get_setting("profile")
    incremental = {n for n, m in sources.REGISTRY.items() if getattr(m, "INCREMENTAL", False)}
    changed = 0
    for job in db.all_jobs_for_rescore():
        # Feeds that only report new postings can't say whether an old one is still up, so
        # the not-seen-for-weeks rule in scoring.exclusion doesn't apply to their jobs.
        job["feed_incremental"] = job.get("source") in incremental
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
    link = " ".join(job.get(k) or "" for k in ("apply_url", "url"))
    if job.get("ats") not in ats.SUPPORTED and job.get("source") != "workday" and not ats.OWN_ENGINE_SITES.search(link):
        return False, "only Greenhouse, Lever, Ashby, Workday and Taleo forms are auto-submitted"
    if (job.get("score") or 0) < automation.get("submit_min_score", 75):
        return False, "score below auto-submit threshold"
    fields = (attempt or {}).get("fields") or []
    if any(f.get("source") == "ai" for f in fields) and not automation.get("auto_submit_ai_answers"):
        return False, "contains AI-written answers for you to review"
    if db.applied_since(24) + db.unconfirmed_since(24) >= automation.get("daily_limit", 15):
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
                    # The watcher already covers employer boards minute by minute.
                    skip = sources.EMPLOYER if automation.get("watch_enabled", True) else ()
                    try:
                        run_search(skip=skip)
                        auto_queue(self.enqueue)
                        rescore()  # periodic: postings that vanished age out instead of lingering as new
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


class Watcher(threading.Thread):
    """Checks employer job boards every few minutes and acts on new postings right away.

    Aggregators (Indeed, LinkedIn and the boards above) re-list jobs hours or days after
    the employer publishes them. Greenhouse, Lever, Ashby, Workday and Oracle *are* the employers'
    own job systems, so a posting is visible there the moment a recruiter publishes it.
    Unchanged boards answer with an empty 304, so frequent checks stay cheap.
    """

    TICK = 20  # seconds between looking for due boards
    PER_TICK = 8  # boards polled per tick, so checks are spread out...
    MAX_PER_TICK = 30  # ...growing with the watch list (500 employers: about every 6 minutes)

    def __init__(self, enqueue):
        super().__init__(daemon=True, name="jobbot-watcher")
        self.enqueue = enqueue
        self.stop_event = threading.Event()
        self.last_poll = {}
        self.last_error = {}
        self.status = {"enabled": False, "feeds": 0, "interval_min": None, "last_check": None, "found": 0}

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception as e:  # never let one bad tick kill the watcher
                db.log(f"Watcher error: {e}", "error")
            self.stop_event.wait(self.TICK)

    def stop(self):
        self.stop_event.set()

    def feeds(self, search):
        return [(n, k) for n in sources.EMPLOYER if search.get("sources", {}).get(n)
                for k in sources.REGISTRY[n].keys(search)]

    def tick(self):
        auto = db.get_setting("automation")
        self.status["enabled"] = bool(auto.get("watch_enabled", True))
        if not self.status["enabled"]:
            return []
        search, profile = db.get_setting("search"), db.get_setting("profile")
        interval = max(1.0, float(auto.get("watch_minutes") or 5)) * 60
        feeds = self.feeds(search)
        per_tick = max(self.PER_TICK, min(self.MAX_PER_TICK, math.ceil(len(feeds) * self.TICK / interval)))
        cycle = max(interval, math.ceil(len(feeds) / per_tick) * self.TICK)  # what the list really allows
        self.status.update(feeds=len(feeds), interval_min=round(cycle / 60, 1))
        now = time.time()
        due = sorted((f for f in feeds if now - self.last_poll.get(f, 0) >= interval),
                     key=lambda f: self.last_poll.get(f, 0))[:per_tick]
        if not due:
            return []
        fresh = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(poll_feed, n, k, search, profile): (n, k) for n, k in due}
            for fut in as_completed(futures):
                feed = futures[fut]
                self.last_poll[feed] = time.time()
                try:
                    r = fut.result()
                except Exception as e:
                    msg = str(e)[:200]
                    if self.last_error.get(feed) != msg:  # say it once, not every few minutes
                        db.log(f"Watching {feed[0]} ({feed[1]}) failed: {msg}", "warn")
                    self.last_error[feed] = msg
                    continue
                self.last_error.pop(feed, None)
                fresh += r["fresh"]
        self.status["last_check"] = db.now()
        if fresh:
            self.status["found"] += len(fresh)
            _announce(fresh)
            self.act_on(fresh, auto)
        return fresh

    def act_on(self, fresh, auto):
        """Fill strong new matches immediately: early applicants get read first."""
        if not auto.get("auto_prepare", True):
            return
        for job in sorted(fresh, key=lambda j: -(j.get("score") or 0)):
            if (job.get("score") or 0) >= auto.get("prepare_min_score", 60) and job.get("ats") != "manual":
                self.enqueue(job["id"], "prepare")
