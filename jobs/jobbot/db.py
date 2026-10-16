"""SQLite storage. One short-lived connection per call keeps it safe across threads."""
import copy
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from . import config

JSON_FIELDS = ("tags", "score_reasons", "answers")
JOB_FIELDS = (
    "id", "source", "title", "company", "location", "remote", "url", "apply_url",
    "ats", "ats_board", "ats_job_id", "description", "salary_min", "salary_max",
    "salary_text", "tags", "posted_at", "first_seen", "last_seen", "score",
    "score_reasons", "status", "status_note", "answers", "updated_at", "applied_at",
    "dedupe_key",
)

# Statuses a job moves through. "Active" ones are owned by the apply worker.
STATUSES = (
    "new", "skipped", "duplicate", "queued", "preparing", "ready", "needs_input",
    "blocked", "manual", "submitting", "applied", "unconfirmed", "error",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source TEXT, title TEXT, company TEXT, location TEXT, remote INTEGER,
    url TEXT, apply_url TEXT, ats TEXT, ats_board TEXT, ats_job_id TEXT,
    description TEXT, salary_min REAL, salary_max REAL, salary_text TEXT, tags TEXT,
    posted_at TEXT, first_seen TEXT, last_seen TEXT,
    score REAL DEFAULT 0, score_reasons TEXT, status TEXT DEFAULT 'new', status_note TEXT,
    answers TEXT, updated_at TEXT, applied_at TEXT, dedupe_key TEXT
);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS jobs_score ON jobs(score);
CREATE INDEX IF NOT EXISTS jobs_dedupe ON jobs(dedupe_key);
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT, kind TEXT, started_at TEXT, finished_at TEXT, result TEXT,
    url TEXT, fields TEXT, missing TEXT, screenshot TEXT, message TEXT
);
CREATE INDEX IF NOT EXISTS attempts_job ON attempts(job_id);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, message TEXT, job_id TEXT
);
CREATE TABLE IF NOT EXISTS source_runs (
    source TEXT, key TEXT, ts TEXT, ok INTEGER, count INTEGER, error TEXT,
    PRIMARY KEY (source, key)
);
"""

_init_lock = threading.Lock()
_initialized = set()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect():
    path = str(config.DB_PATH)
    with _init_lock:
        if path not in _initialized:
            config.ensure_dirs()
            conn = sqlite3.connect(path)
            conn.executescript(SCHEMA)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.close()
            _initialized.add(path)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _decode(row):
    if row is None:
        return None
    d = dict(row)
    for f in JSON_FIELDS:
        if f in d:
            try:
                d[f] = json.loads(d[f]) if d[f] else ([] if f != "answers" else {})
            except (TypeError, ValueError):
                d[f] = [] if f != "answers" else {}
    if "remote" in d and d["remote"] is not None:
        d["remote"] = bool(d["remote"])
    return d


def _encode(fields):
    out = {}
    for k, v in fields.items():
        if k in JSON_FIELDS and not isinstance(v, str) and v is not None:
            v = json.dumps(v)
        if k == "remote" and v is not None:
            v = int(bool(v))
        out[k] = v
    return out


# ---------------------------------------------------------------- settings

def _merge(default, stored):
    if isinstance(default, dict) and isinstance(stored, dict):
        out = copy.deepcopy(default)
        for k, v in stored.items():
            out[k] = _merge(default.get(k), v) if k in default else v
        return out
    return copy.deepcopy(stored) if stored is not None else copy.deepcopy(default)


def get_setting(key):
    with connect() as c:
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    stored = json.loads(row["value"]) if row else None
    return _merge(config.DEFAULTS.get(key), stored)


def set_setting(key, value):
    with connect() as c:
        c.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value)),
        )


# ---------------------------------------------------------------- jobs

def upsert_job(job):
    """Insert a new job or refresh listing fields of an existing one.

    User-owned fields (status, answers, first_seen) are never overwritten.
    Returns True when the job is new.
    """
    job = dict(job)
    ts = now()
    with connect() as c:
        existing = c.execute("SELECT id, status FROM jobs WHERE id=?", (job["id"],)).fetchone()
        if existing:
            keep = {"status", "status_note", "answers", "first_seen", "applied_at"}
            fields = {k: v for k, v in job.items() if k in JOB_FIELDS and k not in keep and k != "id"}
            fields["last_seen"] = ts
            fields["updated_at"] = ts
            enc = _encode(fields)
            sets = ", ".join(f"{k}=?" for k in enc)
            c.execute(f"UPDATE jobs SET {sets} WHERE id=?", (*enc.values(), job["id"]))
            return False
        job.setdefault("status", "new")
        job["first_seen"] = job["last_seen"] = job["updated_at"] = ts
        enc = _encode({k: v for k, v in job.items() if k in JOB_FIELDS})
        cols = ", ".join(enc)
        marks = ", ".join("?" for _ in enc)
        c.execute(f"INSERT INTO jobs({cols}) VALUES({marks})", tuple(enc.values()))
        return True


def get_job(job_id):
    with connect() as c:
        return _decode(c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())


def update_job(job_id, **fields):
    fields["updated_at"] = now()
    enc = _encode(fields)
    sets = ", ".join(f"{k}=?" for k in enc)
    with connect() as c:
        c.execute(f"UPDATE jobs SET {sets} WHERE id=?", (*enc.values(), job_id))


def find_by_dedupe(key, exclude_id):
    with connect() as c:
        rows = c.execute(
            "SELECT * FROM jobs WHERE dedupe_key=? AND id<>?", (key, exclude_id)
        ).fetchall()
    return [_decode(r) for r in rows]


SORTS = {
    "score": "score DESC, posted_at DESC",
    "newest": "COALESCE(posted_at, first_seen) DESC",
    "updated": "updated_at DESC",
    "company": "company COLLATE NOCASE, title COLLATE NOCASE",
}


def list_jobs(statuses=None, min_score=None, q=None, source=None, ats=None,
              sort="score", limit=200, offset=0, with_description=False):
    where, args = [], []
    if statuses:
        where.append(f"status IN ({','.join('?' for _ in statuses)})")
        args += list(statuses)
    if min_score is not None:
        where.append("score >= ?")
        args.append(min_score)
    if q:
        where.append("(title LIKE ? OR company LIKE ? OR location LIKE ?)")
        args += [f"%{q}%"] * 3
    if source:
        where.append("source = ?")
        args.append(source)
    if ats == "any":
        where.append("ats IS NOT NULL AND ats <> ''")
    elif ats:
        where.append("ats = ?")
        args.append(ats)
    cols = "*" if with_description else ", ".join(f for f in JOB_FIELDS if f != "description")
    sql = f"SELECT {cols} FROM jobs"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {SORTS.get(sort, SORTS['score'])} LIMIT ? OFFSET ?"
    args += [limit, offset]
    with connect() as c:
        rows = c.execute(sql, args).fetchall()
        total = c.execute(
            "SELECT COUNT(*) FROM jobs" + (" WHERE " + " AND ".join(where) if where else ""),
            args[:-2],
        ).fetchone()[0]
    return [_decode(r) for r in rows], total


def all_jobs_for_rescore():
    with connect() as c:
        return [_decode(r) for r in c.execute("SELECT * FROM jobs").fetchall()]


def status_counts():
    with connect() as c:
        rows = c.execute("SELECT status, COUNT(*) n FROM jobs GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}


def applied_since(hours):
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat(timespec="seconds")
    with connect() as c:
        return c.execute(
            "SELECT COUNT(*) FROM jobs WHERE status IN ('applied','unconfirmed') AND applied_at >= ?",
            (since,),
        ).fetchone()[0]


def applied_to_company_since(company, days):
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
    with connect() as c:
        return c.execute(
            "SELECT COUNT(*) FROM jobs WHERE status IN ('applied','unconfirmed','submitting') "
            "AND lower(company)=lower(?) AND COALESCE(applied_at, updated_at) >= ?",
            (company or "", since),
        ).fetchone()[0]


# ---------------------------------------------------------------- attempts

def start_attempt(job_id, kind, url=None):
    with connect() as c:
        cur = c.execute(
            "INSERT INTO attempts(job_id, kind, started_at, url, result) VALUES(?,?,?,?,?)",
            (job_id, kind, now(), url, "running"),
        )
        return cur.lastrowid


def finish_attempt(attempt_id, result, fields=None, missing=None, screenshot=None,
                   message=None, url=None):
    with connect() as c:
        c.execute(
            "UPDATE attempts SET finished_at=?, result=?, fields=?, missing=?, screenshot=?, "
            "message=?, url=COALESCE(?, url) WHERE id=?",
            (now(), result, json.dumps(fields or []), json.dumps(missing or []),
             screenshot, message, url, attempt_id),
        )


def _decode_attempt(row):
    d = dict(row)
    for f in ("fields", "missing"):
        try:
            d[f] = json.loads(d[f]) if d[f] else []
        except ValueError:
            d[f] = []
    return d


def list_attempts(job_id):
    with connect() as c:
        rows = c.execute(
            "SELECT * FROM attempts WHERE job_id=? ORDER BY id DESC", (job_id,)
        ).fetchall()
    return [_decode_attempt(r) for r in rows]


def latest_attempt(job_id, kind=None):
    sql = "SELECT * FROM attempts WHERE job_id=?"
    args = [job_id]
    if kind:
        sql += " AND kind=?"
        args.append(kind)
    with connect() as c:
        row = c.execute(sql + " ORDER BY id DESC LIMIT 1", args).fetchone()
    return _decode_attempt(row) if row else None


# ---------------------------------------------------------------- events

def log(message, level="info", job_id=None):
    with connect() as c:
        c.execute(
            "INSERT INTO events(ts, level, message, job_id) VALUES(?,?,?,?)",
            (now(), level, message, job_id),
        )


def recent_events(limit=100):
    with connect() as c:
        rows = c.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- source runs

def last_source_run(source, key):
    with connect() as c:
        row = c.execute(
            "SELECT * FROM source_runs WHERE source=? AND key=?", (source, key)
        ).fetchone()
    return dict(row) if row else None


def record_source_run(source, key, ok, count=0, error=None):
    with connect() as c:
        c.execute(
            "INSERT INTO source_runs(source, key, ts, ok, count, error) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(source, key) DO UPDATE SET ts=excluded.ts, ok=excluded.ok, "
            "count=excluded.count, error=excluded.error",
            (source, key, now(), int(ok), count, error),
        )


def source_runs():
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT * FROM source_runs ORDER BY ts DESC").fetchall()]
