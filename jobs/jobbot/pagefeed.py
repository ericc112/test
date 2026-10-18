"""The internship list on the JobBot page, built from JobBot's search results.

`python3 -m jobbot page-feed --out DIR` writes the page's documents: DIR/meta.json (the `meta/feed` document: when
the list was made and its counts) and DIR/pages/p0.json … (the `jobs/p0` … documents, PAGE_ITEMS listings each).
Listings posted MAX_AGE_DAYS or more days ago are left out. With `--previous DIR` (the current `jobs` documents),
each listing keeps the time it first appeared. `--search` runs a fresh search of every watched feed first.
"""
import glob
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import config, db, fields, pay, places, scoring, sources

MAX_AGE_DAYS = 30
PAGE_ITEMS = 60  # listings per document: about 45 KB
SOURCE_LABELS = {
    "workday": "Workday", "greenhouse": "Greenhouse", "lever": "Lever", "ashby": "Ashby", "successfactors": "SuccessFactors",
    "oracle": "Oracle", "phenom": "Phenom", "jibe": "Jibe", "amazon": "Amazon", "themuse": "The Muse", "himalayas": "Himalayas",
    "jobicy": "Jobicy", "remotive": "Remotive", "remoteok": "Remote OK", "arbeitnow": "Arbeitnow",
}
# Shown elsewhere on the card (area, pay, Apply), or true of every listing.
HIDDEN_REASON = re.compile(r"^(Internship|Pay: |JobBot can apply directly)|\brole$")


def _when(ts):
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def item(job, search, first_seen):
    """One listing as the page reads it."""
    where = places.describe(job)
    hourly = pay.hourly(job)
    in_field, area = fields.classify(job, search)
    season = fields.season_of(job.get("title"))
    out = {
        "k": job["id"], "t": job.get("title") or "", "c": job.get("company") or "", "u": job.get("url") or job.get("apply_url") or "",
        "src": SOURCE_LABELS.get(job.get("source"), job.get("source") or ""), "emp": job.get("source") in sources.EMPLOYER,
        "l": job.get("location") or "", "loc": where["text"], "st": where["states"], "rm": where["remote"],
        # Outside the US: "USA - New Jersey - Rahway" counts as US too, and a listing without a location isn't called away.
        "x": bool(job.get("location")) and not (where["us"] or scoring.looks_us(job.get("location"))),
        "a": area if in_field else "", "se": f"{season[0]} {season[1]}" if season else "",
        "s": job.get("score") or 0, "r": [r for r in job.get("score_reasons") or [] if not HIDDEN_REASON.search(r)],
        "p": job.get("posted_at") or first_seen, "f": first_seen,
        "paid": "listed" if hourly else "stated" if pay.status(job) == "paid" else "employer",
    }
    if hourly:
        out.update(pay=hourly["text"], hr=round(hourly["lo"]), est=hourly["basis"] != "hour")
    return out


def previous_first_seen(folder):
    """{listing key: first seen} from the current `jobs` documents saved in a folder (as ArtifactData saves them)."""
    seen = {}
    for path in glob.glob(os.path.join(folder, "**", "*.json"), recursive=True):
        try:
            with open(path) as f:
                doc = json.load(f)
        except (OSError, ValueError):
            continue
        for it in (doc.get("data", doc) if isinstance(doc, dict) else {}).get("items") or []:
            if it.get("k") and it.get("f"):
                seen[it["k"]] = it["f"]
    return seen


def watched(search):
    """(feeds, employers) JobBot reads for this search."""
    names = {(kind, slug.split("#")[0]): name for name, kind, slug in config.SUGGESTED_COMPANIES}
    feeds, employers = 0, set()
    for name, mod in sources.REGISTRY.items():
        if not search.get("sources", {}).get(name) or not getattr(mod, "EMPLOYER", False):
            continue
        for key in mod.keys(search):
            feeds += 1
            employers.add(sources.company_key(names.get((name, key.split("#")[0]), key.split("|")[0])))
    return feeds, len(employers)


def build(jobs, search, first_seen=None, now=None):
    """(pages, meta) for the page from stored jobs: duplicates and listings MAX_AGE_DAYS or more days old left out."""
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat(timespec="seconds")
    first_seen = first_seen or {}
    cutoff = now - timedelta(days=MAX_AGE_DAYS)
    items, dropped = [], 0
    for job in jobs:
        if job.get("status") == "duplicate":
            continue
        seen = first_seen.get(job["id"]) or stamp
        posted = _when(job.get("posted_at")) or _when(seen)
        if posted and posted <= cutoff:
            dropped += 1
            continue
        items.append(item(job, search, seen))
    items.sort(key=lambda i: (-i["s"], -(_when(i["p"]) or now).timestamp(), i["k"]))
    pages = [{"n": n, "items": items[i:i + PAGE_ITEMS]} for n, i in enumerate(range(0, len(items), PAGE_ITEMS))]
    feeds, employers = watched(search)
    meta = {"updated_at": stamp, "total": len(items), "in_reach": sum(not i["x"] for i in items),
            "with_pay": sum("pay" in i for i in items), "pages": len(pages), "paid_only": bool(search.get("paid_only", True)),
            "by_source": dict(Counter(i["src"] for i in items)), "feeds_watched": feeds, "employers_watched": employers,
            "dropped_old": dropped, "max_age_days": MAX_AGE_DAYS}
    return pages, meta


def write(out_dir, pages, meta):
    os.makedirs(os.path.join(out_dir, "pages"), exist_ok=True)
    for old in glob.glob(os.path.join(out_dir, "pages", "p*.json")):
        os.remove(old)
    for page in pages:
        with open(os.path.join(out_dir, "pages", f"p{page['n']}.json"), "w") as f:
            json.dump(page, f, separators=(",", ":"))
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)


def run(out_dir, previous=None, search_first=False, profile_file=None):
    """The page-feed command: optionally search, then build and write the list. Returns the meta document."""
    from . import pipeline
    if profile_file:
        profile = db.get_setting("profile")
        with open(profile_file) as f:
            mine = json.load(f)
        profile.update({k: v for k, v in mine.items() if k in config.DEFAULT_PROFILE and v not in (None, "")})
        db.set_setting("profile", profile)
    if search_first:
        summary = pipeline.run_search(force=True)
        print(f"searched {len(summary.get('fetched', []))} feeds: {summary.get('kept', 0)} matching, "
              f"{len(summary.get('errors', []))} errors", flush=True)
    pages, meta = build(db.all_jobs_for_rescore(), db.get_setting("search"), previous_first_seen(previous) if previous else None)
    write(out_dir, pages, meta)
    return meta
