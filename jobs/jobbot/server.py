"""FastAPI app: the JSON API plus the single-page UI in ./static."""
import re
import threading
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import __version__, ats, config, db, fields, phone, pipeline, sources
from .textutil import norm, split_list
from .worker import Worker

STATIC = Path(__file__).with_name("static")
SETTING_KEYS = ("profile", "answers", "search", "automation", "llm")
ALLOWED_UPLOADS = {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"}


class State:
    worker = None
    scheduler = None
    watcher = None
    search_running = False
    last_search = None


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]", "testserver"}

SIGNED_OUT = """<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1">
<title>JobBot</title><body style="font:16px system-ui;margin:40px 20px;max-width:30em;color:#222">
<h2>JobBot</h2><p>This device isn't signed in.</p>
<p>On your computer, open JobBot and go to <b>Automation &amp; AI &rarr; Phone</b>, then scan the QR code
or open its link here.</p></body>"""


def _is_local(request):
    return (request.client.host if request.client else "") in phone.LOOPBACK


def create_app(start_background=True, extra_hosts=(), phone_access=False):
    allowed_hosts = LOCAL_HOSTS | set(extra_hosts)

    @asynccontextmanager
    async def lifespan(app):
        if start_background:
            State.worker = Worker()
            State.worker.start()
            State.scheduler = pipeline.Scheduler(State.worker.enqueue)
            State.scheduler.start()
            State.watcher = pipeline.Watcher(State.worker.enqueue)
            State.watcher.start()
        yield
        if State.watcher:
            State.watcher.stop()
        if State.scheduler:
            State.scheduler.stop()
        if State.worker:
            State.worker.stop()

    app = FastAPI(title="JobBot", version=__version__, lifespan=lifespan)
    config.ensure_dirs()

    @app.middleware("http")
    async def local_only(request, call_next):
        if phone_access and not _is_local(request):
            # Another device (your phone): it must have opened the private link once.
            k = request.query_params.get("key")
            if k and request.method == "GET" and phone.check(k):
                resp = RedirectResponse(request.url.path, status_code=303)  # drop the key from the address bar
                resp.set_cookie(phone.COOKIE, k, max_age=180 * 86400, httponly=True, samesite="lax")
                return resp
            if not phone.check(request.cookies.get(phone.COOKIE)):
                if request.url.path.startswith("/api/"):
                    return JSONResponse({"detail": "Open the phone link from your computer first"}, status_code=401)
                return HTMLResponse(SIGNED_OUT, status_code=401)
        else:
            # Host check blocks DNS-rebinding; the custom header on writes forces a CORS
            # preflight, so other websites open in your browser can't post to JobBot.
            host = request.headers.get("host", "")
            host = host[1:host.find("]")] if host.startswith("[") else host.rsplit(":", 1)[0]
            if host not in allowed_hosts:
                return JSONResponse({"detail": "Unknown host"}, status_code=403)
        if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get("x-jobbot") != "1":
            return JSONResponse({"detail": "Missing X-JobBot header"}, status_code=403)
        return await call_next(request)

    def worker():
        if State.worker is None:
            raise HTTPException(503, "Worker not running")
        return State.worker

    # ---------------------------------------------------------------- overview
    @app.get("/api/state")
    def state():
        automation = db.get_setting("automation")
        profile = db.get_setting("profile")
        search = db.get_setting("search")
        companies = sum(len(v) for v in search.get("companies", {}).values())
        llm = db.get_setting("llm")
        fresh, fresh_total = db.fresh_jobs(hours=48, limit=8, min_score=automation.get("alert_min_score", 50))
        lags = db.detection_lags(days=7)
        return {
            "version": __version__,
            "counts": db.status_counts(),
            "applied_24h": db.applied_since(24),
            "applied_7d": db.applied_since(24 * 7),
            "daily_limit": automation.get("daily_limit"),
            "automation": automation,
            "next_run_sec": State.scheduler.next_run if State.scheduler else None,
            "queue": State.worker.snapshot() if State.worker else {"current": None, "pending": []},
            "search_running": State.search_running,
            "watch": dict(State.watcher.status) if State.watcher else {"enabled": False, "feeds": 0},
            "fresh": {
                "total_48h": fresh_total,
                "latest": fresh,
                "lag_median_min": round(lags[len(lags) // 2], 1) if lags else None,
                "lag_samples": len(lags),
            },
            "last_search": State.last_search,
            "setup": {
                "profile": bool(profile.get("first_name") and profile.get("email")),
                "resume": bool(profile.get("resume_file")),
                "keywords": bool(search.get("field") or split_list(search.get("keywords"))),
                "companies": companies > 0,
                "automation": bool(automation.get("enabled")),
                "ai": bool(llm.get("enabled")),
            },
        }

    @app.get("/api/phone")
    def phone_info(request: Request):
        if not phone_access:
            return {"enabled": False}
        if not _is_local(request):
            return {"enabled": True, "on_phone": True}
        link = phone.link(request.url.port or 8765)
        return {"enabled": True, "on_phone": False, "link": link, "qr": phone.qr_svg(link)}

    @app.post("/api/phone/reset")
    def phone_reset(request: Request):
        if not phone_access or not _is_local(request):
            raise HTTPException(403, "Only from the computer running JobBot")
        phone.reset()
        return phone_info(request)

    @app.get("/api/sources")
    def list_sources():
        runs = {}
        for r in db.source_runs():
            runs.setdefault(r["source"], []).append(r)
        return [
            {"name": n, "label": getattr(m, "LABEL", n), "direct_apply": n in ats.SUPPORTED,
             "employer": n in sources.EMPLOYER, "runs": runs.get(n, [])}
            for n, m in sources.REGISTRY.items()
        ]

    @app.get("/api/fields")
    def list_fields():
        return {
            name: {"label": f["label"], "areas": [{"key": k, "label": fields.FAMILIES[k]["label"]} for k in f["families"]]}
            for name, f in fields.FIELDS.items()
        }

    @app.get("/api/company-names")
    def company_names():
        names = {}
        for name, kind, slug in config.SUGGESTED_COMPANIES:
            names.setdefault(kind, {})[slug] = name
        return names

    @app.get("/api/suggestions")
    def suggestions():
        have = db.get_setting("search").get("companies", {})
        return [{"name": n, "ats": a, "slug": s} for n, a, s in config.SUGGESTED_COMPANIES if s not in have.get(a, [])]

    @app.get("/api/events")
    def events(limit: int = 150):
        return db.recent_events(limit)

    # ---------------------------------------------------------------- jobs
    @app.get("/api/jobs")
    def jobs(status: str = "", q: str = "", min_score: float = None, source: str = "", ats_filter: str = "",
             sort: str = "score", limit: int = 100, offset: int = 0, posted_hours: int = 0):
        statuses = [s for s in status.split(",") if s] or None
        rows, total = db.list_jobs(statuses, min_score, q or None, source or None, ats_filter or None,
                                   sort, min(limit, 500), offset, posted_hours=posted_hours or None)
        return {"jobs": rows, "total": total}

    @app.get("/api/jobs/{job_id:path}/detail")
    def job_detail(job_id: str):
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(404, "No such job")
        job["attempts"] = db.list_attempts(job_id)[:10]
        q = State.worker.snapshot() if State.worker else {"current": None, "pending": []}
        job["in_queue"] = any(p[0] == job_id for p in q["pending"]) or (q["current"] or [None])[0] == job_id
        return job

    @app.post("/api/jobs/{job_id:path}/action")
    def job_action(job_id: str, body: dict = Body(...)):
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(404, "No such job")
        action = body.get("action")
        if action in ("prepare", "submit"):
            if job["status"] == "applied" and not body.get("force"):
                raise HTTPException(409, "Already applied to this job")
            if action == "submit" and job["status"] in ("submitting",):
                raise HTTPException(409, "Already submitting")
            worker().enqueue(job_id, action)
            return {"ok": True, "queued": action}
        if action == "skip":
            db.update_job(job_id, status="skipped", status_note="Skipped by you")
        elif action == "restore":
            db.update_job(job_id, status="new", status_note=None)
        elif action == "mark_applied":
            db.update_job(job_id, status="applied", status_note="Marked as applied by you", applied_at=db.now())
        elif action == "manual":
            db.update_job(job_id, status="manual", status_note="You'll apply on the company site")
        else:
            raise HTTPException(400, f"Unknown action {action!r}")
        return {"ok": True}

    @app.post("/api/jobs/{job_id:path}/answers")
    def save_answers(job_id: str, body: dict = Body(...)):
        """Save your answers for this job's open questions; optionally remember them everywhere."""
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(404, "No such job")
        given = {k: v for k, v in (body.get("answers") or {}).items() if v not in (None, "", [])}
        merged = dict(job.get("answers") or {})
        merged.update(given)
        db.update_job(job_id, answers=merged)
        if body.get("remember"):
            bank = db.get_setting("answers")
            known = {norm(e.get("q", "")) for e in bank}
            for label, value in given.items():
                if norm(label) not in known and isinstance(value, str):
                    bank.append({"q": label, "a": value})
            db.set_setting("answers", bank)
        if body.get("refill", True):
            worker().enqueue(job_id, "prepare")
        return {"ok": True}

    @app.post("/api/bulk")
    def bulk(body: dict = Body(...)):
        ids, action = body.get("ids") or [], body.get("action")
        for job_id in ids:
            if action in ("prepare", "submit"):
                worker().enqueue(job_id, action)
            elif action == "skip":
                db.update_job(job_id, status="skipped", status_note="Skipped by you")
        return {"ok": True, "count": len(ids)}

    @app.post("/api/queue/clear")
    def clear_queue():
        return {"cleared": worker().clear()}

    # ---------------------------------------------------------------- search
    @app.post("/api/search")
    def search_now(body: dict = Body(default={})):
        if State.search_running:
            return {"started": False, "reason": "A search is already running"}

        def run():
            State.search_running = True
            try:
                State.last_search = pipeline.run_search(force=bool(body.get("force", True)))
                State.last_search["finished"] = db.now()
                if body.get("queue") and State.worker:
                    pipeline.auto_queue(State.worker.enqueue)
            except Exception as e:
                db.log(f"Search failed: {e}", "error")
            finally:
                State.search_running = False

        threading.Thread(target=run, daemon=True).start()
        return {"started": True}

    @app.post("/api/rescore")
    def rescore():
        return {"rescored": pipeline.rescore()}

    @app.post("/api/companies/detect")
    def detect_company(body: dict = Body(...)):
        """Find a company's Greenhouse/Lever/Ashby board from its name or careers URL."""
        raw = (body.get("name") or "").strip()
        if not raw:
            raise HTTPException(400, "Enter a company name or job board URL")
        hit = ats.detect(raw)
        workday_key = sources.REGISTRY["workday"].key_from_url(raw)
        found = []
        if hit[0]:
            found.append({"ats": hit[0], "slug": hit[1]})
        elif workday_key:
            if not sources.REGISTRY["workday"].probe(workday_key):
                raise HTTPException(400, "That Workday careers site didn't answer. Copy the link from the company's job search page.")
            found.append({"ats": "workday", "slug": workday_key})
        else:
            base = re.sub(r"https?://|www\.|\.(com|io|ai|co|org|net)\b.*$", "", raw.lower()).strip("/ ")
            words_ = re.findall(r"[a-z0-9]+", base)
            slugs = list(dict.fromkeys(["".join(words_), "-".join(words_), raw.strip()]))
            checks = [(name, slug) for slug in slugs if slug for name in ats.SUPPORTED]
            with ThreadPoolExecutor(max_workers=9) as pool:
                results = pool.map(lambda c: (c, sources.REGISTRY[c[0]].probe(c[1])), checks)
                for (name, slug), ok in results:
                    if ok and not any(f["ats"] == name for f in found):
                        found.append({"ats": name, "slug": slug})
        if body.get("add") and found:
            search = db.get_setting("search")
            for f in found:
                lst = search["companies"].setdefault(f["ats"], [])
                if f["slug"] not in lst:
                    lst.append(f["slug"])
            db.set_setting("search", search)
        return {"found": found}

    # ---------------------------------------------------------------- settings
    @app.get("/api/settings/{key}")
    def get_settings(key: str):
        if key not in SETTING_KEYS:
            raise HTTPException(404)
        value = db.get_setting(key)
        if key == "llm":
            import os
            value = dict(value, has_key=bool(value.get("api_key")), env_key=bool(os.environ.get("ANTHROPIC_API_KEY")),
                         api_key="")
        return value

    @app.put("/api/settings/{key}")
    def put_settings(key: str, body=Body(...)):
        if key not in SETTING_KEYS:
            raise HTTPException(404)
        if key == "llm":
            old = db.get_setting("llm")
            body = {k: v for k, v in body.items() if k not in ("has_key", "env_key")}
            if not body.get("api_key"):
                body["api_key"] = "" if body.get("clear_key") else old.get("api_key", "")
            body.pop("clear_key", None)
        if key == "profile":
            old = db.get_setting("profile")
            for f in ("resume_file", "resume_text", "cover_letter_file"):
                body.setdefault(f, old.get(f, ""))
        db.set_setting(key, body)
        if key in ("search", "profile"):
            pipeline.search_changed()
            pipeline.rescore()
        return {"ok": True}

    @app.post("/api/upload/{kind}")
    async def upload(kind: str, file: UploadFile = File(...)):
        if kind not in ("resume", "cover_letter"):
            raise HTTPException(404)
        name = Path(file.filename or "upload").name
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED_UPLOADS:
            raise HTTPException(400, f"Use one of: {', '.join(sorted(ALLOWED_UPLOADS))}")
        safe = re.sub(r"[^A-Za-z0-9._ -]+", "_", name)[:120]
        data = await file.read()
        if len(data) > 10 * 1024 * 1024:
            raise HTTPException(400, "File is larger than 10 MB")
        (config.FILES_DIR / safe).write_bytes(data)
        profile = db.get_setting("profile")
        profile[f"{kind}_file"] = safe
        if kind == "resume":
            profile["resume_text"] = extract_text(config.FILES_DIR / safe)
        db.set_setting("profile", profile)
        return {"ok": True, "file": safe, "text_chars": len(profile.get("resume_text") or "")}

    @app.get("/shots/{name}")
    def screenshot(name: str):
        path = (config.SHOTS_DIR / Path(name).name).resolve()
        if not path.is_file() or config.SHOTS_DIR.resolve() not in path.parents:
            raise HTTPException(404)
        return FileResponse(path)

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


def extract_text(path):
    path = Path(path)
    try:
        if path.suffix.lower() == ".pdf":
            from pypdf import PdfReader
            return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages).strip()
        if path.suffix.lower() in (".txt", ".md"):
            return path.read_text(errors="replace").strip()
    except Exception:
        return ""
    return ""
