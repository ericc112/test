"""Job sources. Each module exposes NAME, MIN_INTERVAL, keys(search) and fetch(key, search)."""
import re
from datetime import datetime, timezone

from ..textutil import norm

REGISTRY = {}


def register(module):
    REGISTRY[module.NAME] = module
    return module


def iso(value):
    """Normalise epoch seconds/ms or ISO strings to an ISO-8601 UTC string."""
    if value in (None, "", 0):
        return None
    if isinstance(value, (int, float)):
        if value > 1e12:
            value /= 1000
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat(timespec="seconds")
    s = str(value).strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except ValueError:
        return None


def company_key(name):
    s = norm(name)
    s = re.sub(r"\b(inc|llc|ltd|gmbh|corp|corporation|co|company|technologies|labs)\b\.?", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def make_job(source, external_id, title, company, url, **kw):
    title = " ".join((title or "").split())
    company = " ".join((company or "").split())
    job = {
        "id": f"{source}:{external_id}",
        "source": source,
        "title": title,
        "company": company,
        "url": url,
        "apply_url": kw.pop("apply_url", None) or url,
        "dedupe_key": f"{company_key(company)}|{norm(title)}",
    }
    job.update(kw)
    return job


def display_name(slug):
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", slug or "") if w)


from . import (  # noqa: E402  (modules register themselves)
    arbeitnow, ashby, greenhouse, himalayas, jobicy, lever, remoteok, remotive, themuse, workday,
)

# Employer-run job systems (not aggregators): watched every few minutes for new postings.
EMPLOYER = [n for n, m in REGISTRY.items() if getattr(m, "EMPLOYER", False)]


def id_prefix(name, key):
    mod = REGISTRY[name]
    return mod.id_prefix(key) if hasattr(mod, "id_prefix") else f"{name}:{key}:"
