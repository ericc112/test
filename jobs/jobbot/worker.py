"""Background apply worker: one browser task at a time, in its own thread."""
import queue
import threading

from . import ats, config, db, pipeline
from .answers import Context
from .apply.engine import Engine
from .apply.taleo import TaleoEngine, is_taleo
from .apply.workday import WorkdayEngine, is_workday, password
from .llm import Claude
from .textutil import norm

ACTIVE = ("queued", "preparing", "submitting")


def build_context(job, mode):
    profile = db.get_setting("profile")
    files = {}
    for key, field_name in (("resume", "resume_file"), ("cover_letter", "cover_letter_file")):
        name = profile.get(field_name)
        if name and (config.FILES_DIR / name).exists():
            files[key] = str(config.FILES_DIR / name)
    planned = {}
    if mode == "submit":
        last = db.latest_attempt(job["id"], "prepare")
        for f in (last or {}).get("fields", []):
            # Reuse the AI text you reviewed; profile answers are recomputed (autocompletes need re-picking).
            if f.get("source") == "ai" and f.get("answer") not in (None, "", []):
                planned[norm(f["label"])] = (f["answer"], f["source"])
    return Context(
        profile=profile,
        bank=db.get_setting("answers"),
        job=job,
        overrides={norm(k): v for k, v in (job.get("answers") or {}).items()},
        planned=planned,
        files=files,
        llm=Claude.from_settings(db.get_setting("llm")),
    )


class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="jobbot-worker")
        self.q = queue.Queue()
        self.pending = []  # (job_id, action) in order, for the UI
        self.current = None
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

    # ------------------------------------------------------------ queueing
    def enqueue(self, job_id, action):
        with self.lock:
            if (job_id, action) in self.pending or self.current == (job_id, action):
                return False
            self.pending.append((job_id, action))
        job = db.get_job(job_id)
        if job and action == "prepare":
            db.update_job(job_id, status="queued", status_note=None)
        self.q.put((job_id, action))
        return True

    def snapshot(self):
        with self.lock:
            return {"current": self.current, "pending": list(self.pending)}

    def clear(self):
        with self.lock:
            dropped = list(self.pending)
            self.pending.clear()
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break
        for job_id, _ in dropped:
            job = db.get_job(job_id)
            if job and job["status"] == "queued":
                db.update_job(job_id, status="new")
        return len(dropped)

    def stop(self):
        self.stop_event.set()
        self.q.put(None)

    # ------------------------------------------------------------ main loop
    def run(self):
        # Anything left mid-flight by a previous run goes back to a sane state.
        for status, back in (("queued", "new"), ("preparing", "new"), ("submitting", "unconfirmed")):
            for job in db.list_jobs(statuses=[status], limit=1000)[0]:
                db.update_job(job["id"], status=back,
                              status_note="Interrupted by a restart" if back == "unconfirmed" else None)
        while not self.stop_event.is_set():
            item = self.q.get()
            if item is None:
                break
            job_id, action = item
            with self.lock:
                if item not in self.pending:
                    continue  # cleared
                self.pending.remove(item)
                self.current = item
            try:
                self.process(job_id, action)
            except Exception as e:
                db.update_job(job_id, status="error", status_note=str(e)[:300])
                db.log(f"{action} failed: {e}", "error", job_id)
            finally:
                with self.lock:
                    self.current = None

    def process(self, job_id, action):
        job = db.get_job(job_id)
        if not job:
            return
        if job["status"] in ("applied",) and action == "submit":
            return
        automation = db.get_setting("automation")
        label = f"{job['title']} at {job['company']}"
        workday = is_workday(job) and bool(password(db.get_setting("profile")))  # sign in and apply there
        taleo = is_taleo(job) and bool(password(db.get_setting("profile")))  # register or sign in, then apply

        if not workday and not taleo and not job.get("ats"):
            db.log(f"Finding the application form for {label}", job_id=job_id)
            found = ats.resolve(job)
            db.update_job(job_id, **found)
            job.update(found)
        if not workday and not taleo and job.get("ats") == "manual":
            note = ("Workday needs an account with each employer, and no Workday password is set. Set "
                    "JOBBOT_WORKDAY_PASSWORD (in your cloud environment's settings, or before starting JobBot) "
                    "and try again: JobBot creates the account and applies." if is_workday(job) else
                    "The employer's careers site asks you to create an account with them, so apply there."
                    if job.get("source") in ("oracle", "amazon") else "Needs an account on another site, so apply there directly.")
            db.update_job(job_id, status="manual", status_note=note)
            db.log(f"{label}: apply manually", job_id=job_id)
            return

        db.update_job(job_id, status="preparing" if action == "prepare" else "submitting")
        engine = (WorkdayEngine if workday else TaleoEngine if taleo else Engine)(
            headless=automation.get("headless", True),
            assist_timeout_min=automation.get("assist_timeout_min", 10),
            log=lambda m: db.log(m, job_id=job_id),
        )
        ctx = build_context(job, action)
        attempt = db.start_attempt(job_id, action, job.get("apply_url"))
        db.log(f"{'Filling' if action == 'prepare' else 'Submitting'} application: {label}", job_id=job_id)
        res = engine.run(job, ctx, mode=action)
        if engine.found_ats and job.get("ats") not in ats.SUPPORTED:
            db.update_job(job_id, **engine.found_ats)  # next time, go straight to the real form
        db.finish_attempt(attempt, res.result, res.fields, res.missing, res.screenshot, res.message, res.url)

        fields = {"status": res.result, "status_note": res.message}
        if res.result in ("applied", "unconfirmed"):
            fields["applied_at"] = db.now()
        db.update_job(job_id, **fields)
        level = "info" if res.result in ("ready", "applied") else "warn"
        db.log(f"{label}: {res.result} - {res.message}", level, job_id)

        if action == "prepare" and res.result == "ready":
            ok, why = pipeline.can_auto_submit(db.get_job(job_id), db.latest_attempt(job_id, "prepare"), automation)
            if ok:
                db.log(f"Auto-submitting {label}", job_id=job_id)
                self.enqueue(job_id, "submit")
            elif automation.get("auto_submit"):
                db.log(f"Holding {label} for review: {why}", job_id=job_id)
