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
TOP_CAP_ZONE = 60  # the first page: no more than TOP_PER_COMPANY cards from one company there
TOP_PER_COMPANY = 3
RECENCY_BOOST = ((1, 8), (3, 5), (7, 2))  # (posted within N days, points added for ordering only)
_F500 = None


def fortune500():
    """{company key: Fortune 500 entry} from fortune500.json."""
    global _F500
    if _F500 is None:
        with open(os.path.join(os.path.dirname(__file__), "fortune500.json")) as f:
            _F500 = {sources.company_key(c["name"]): c for c in json.load(f)}
    return _F500


def domain_of(url):
    m = re.match(r"^(?:https?://)?(?:www\.)?([^/:?#]+)", url or "")
    return m.group(1).lower() if m else ""


def initials(name):
    words = [w for w in re.split(r"[^A-Za-z0-9&]+", name or "") if w and w.lower() not in ("the", "of", "and", "inc", "co")]
    return "".join(w[0] for w in words[:2]).upper() or "?"


def company_info(name):
    """Logo and profile fields for a card, only from data JobBot already has (fortune500.json)."""
    entry = fortune500().get(sources.company_key(name))
    out = {"ini": initials(name), "f500": bool(entry)}
    if entry:
        dom = domain_of(entry.get("website"))
        out.update(rank=entry["rank"], web=entry.get("website") or "", car=entry.get("careers") or "")
        if dom:
            out.update(dom=dom, logo=f"https://www.google.com/s2/favicons?domain={dom}&sz=64")
    return out


def group_key(it):
    return f"{sources.company_key(it['c'])}|{sources.norm(it['t'])}"


def group(items):
    """One card per company + title: the best-scoring posting leads, the others become its extra locations."""
    groups = {}
    for it in items:  # already in best-first order
        lead = groups.get(group_key(it))
        if lead is None:
            groups[group_key(it)] = it
            it["n"] = 1
            continue
        lead["n"] += 1
        lead.setdefault("more", []).append({"k": it["k"], "u": it["u"], "loc": it["loc"], "st": it["st"]})
        lead["st"] = sorted(set(lead["st"]) | set(it["st"]))
        lead["rm"] = lead["rm"] or it["rm"]
        lead["x"] = lead["x"] and it["x"]
        if it["f"] > lead["f"]:
            lead["f"] = it["f"]  # a new location counts as new
    return list(groups.values())


def _boost(it, now):
    posted = _when(it["p"])
    if not posted:
        return 0
    age = (now - posted).total_seconds() / 86400
    return next((pts for days, pts in RECENCY_BOOST if age < days), 0)


def spread(items, zone=TOP_CAP_ZONE, cap=TOP_PER_COMPANY):
    """Near the top no company gets more than `cap` cards; the rest move down, still in order."""
    top, later, per = [], [], Counter()
    for it in items:
        key = sources.company_key(it["c"])
        if len(top) < zone and per[key] < cap:
            top.append(it)
            per[key] += 1
        else:
            later.append(it)
    return top + later


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
    out.update(company_info(out["c"]))
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


def build(jobs, search, first_seen=None, now=None, min_score=0):
    """(pages, meta) for the page from stored jobs: duplicates, listings MAX_AGE_DAYS or more days old and listings
    scoring under min_score left out."""
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat(timespec="seconds")
    first_seen = first_seen or {}
    cutoff = now - timedelta(days=MAX_AGE_DAYS)
    items, dropped, low = [], 0, 0
    for job in jobs:
        if job.get("status") in ("duplicate", "skipped"):
            continue
        if (job.get("score") or 0) < min_score:
            low += 1
            continue
        seen = first_seen.get(job["id"]) or stamp
        posted = _when(job.get("posted_at")) or _when(seen)
        if posted and posted <= cutoff:
            dropped += 1
            continue
        items.append(item(job, search, seen))
    items.sort(key=lambda i: (-i["s"], -(_when(i["p"]) or now).timestamp(), i["k"]))
    postings = len(items)
    items = group(items)
    for it in items:
        it["new"] = it["f"] == stamp  # first appeared in this run; the page can also compare "f" with your last visit
        it["b"] = it["s"] + _boost(it, now)  # "Best match" order: score plus a recency boost
    items.sort(key=lambda i: (-i["b"], -(_when(i["p"]) or now).timestamp(), i["k"]))
    items = spread(items)
    pages = [{"n": n, "items": items[i:i + PAGE_ITEMS]} for n, i in enumerate(range(0, len(items), PAGE_ITEMS))]
    feeds, employers = watched(search)
    meta = {"updated_at": stamp, "total": len(items), "in_reach": sum(not i["x"] for i in items),
            "with_pay": sum("pay" in i for i in items), "pages": len(pages), "paid_only": bool(search.get("paid_only", True)),
            "by_source": dict(Counter(i["src"] for i in items)), "feeds_watched": feeds, "employers_watched": employers,
            "dropped_old": dropped, "max_age_days": MAX_AGE_DAYS, "min_score": min_score, "below_min_score": low,
            "postings": postings, "grouped": postings - len(items), "new_this_run": sum(i["new"] for i in items),
            "posted_last_day": sum(_boost(i, now) == RECENCY_BOOST[0][1] for i in items),
            "non_f500": sorted({i["c"] for i in items if not i["f500"]})}
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


def run(out_dir, previous=None, search_first=False, profile_file=None, min_score=0):
    summary = None
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
    elif profile_file:
        pipeline.rescore()  # scores use your skills and terms
    pages, meta = build(db.all_jobs_for_rescore(), db.get_setting("search"), previous_first_seen(previous) if previous else None,
                        min_score=min_score)
    if summary is not None:
        meta["feed_errors"] = summary.get("errors", [])[:100]  # which feeds failed this run
        meta["feeds_failed"] = len(summary.get("errors", []))
    write(out_dir, pages, meta)
    return meta
