"""The JobBot page's internship list: what goes in, what's left out, and the counts."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jobbot import config, pagefeed

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def job(i, days_ago=1, **kw):
    out = {"id": f"workday:acme:R{i}", "source": "workday", "title": f"Supply Chain Intern {i} - Summer 2027", "company": "Acme",
           "location": "Houston, TX", "url": f"https://acme.wd1.myworkdayjobs.com/Careers/job/R{i}", "score": 70,
           "score_reasons": ["Internship", "Operations & Supply Chain role", "In United States", "Posted 1d ago"],
           "posted_at": (NOW - timedelta(days=days_ago)).isoformat() if days_ago is not None else None, "status": "new",
           "description": "The pay is $25 per hour."}
    out.update(kw)
    return out


class PageFeedTests(unittest.TestCase):
    def test_listings_30_days_or_older_are_left_out(self):
        jobs = [job(1, 29), job(2, 30), job(3, 45), job(4, 2, status="duplicate")]
        pages, meta = pagefeed.build(jobs, config.DEFAULT_SEARCH, now=NOW)
        self.assertEqual([i["k"] for p in pages for i in p["items"]], ["workday:acme:R1"])
        self.assertEqual((meta["total"], meta["dropped_old"]), (1, 2))

    def test_listings_under_the_minimum_score_are_left_out(self):
        jobs = [job(1, score=85), job(2, score=80), job(3, score=79), job(4, score=90, status="skipped")]
        pages, meta = pagefeed.build(jobs, config.DEFAULT_SEARCH, now=NOW, min_score=80)
        self.assertEqual([i["k"] for i in pages[0]["items"]], ["workday:acme:R1", "workday:acme:R2"])
        self.assertEqual((meta["min_score"], meta["below_min_score"]), (80, 1))

    def test_a_listing_without_a_date_ages_from_when_it_first_appeared(self):
        old = (NOW - timedelta(days=31)).isoformat()
        recent = (NOW - timedelta(days=3)).isoformat()
        jobs = [job(1, None), job(2, None)]
        pages, meta = pagefeed.build(jobs, config.DEFAULT_SEARCH, {"workday:acme:R1": old, "workday:acme:R2": recent}, now=NOW)
        items = pages[0]["items"]
        self.assertEqual([(i["k"], i["f"], i["p"]) for i in items], [("workday:acme:R2", recent, recent)])

    def test_a_listing_as_the_page_reads_it(self):
        pages, meta = pagefeed.build([job(1)], config.DEFAULT_SEARCH, now=NOW)
        it = pages[0]["items"][0]
        self.assertEqual({k: it[k] for k in ("src", "emp", "loc", "st", "x", "rm", "a", "se", "pay", "hr", "est", "paid", "f")},
                         {"src": "Workday", "emp": True, "loc": "Houston, TX", "st": ["TX"], "x": False, "rm": False,
                          "a": "Operations & Supply Chain", "se": "Summer 2027", "pay": "$25/hr", "hr": 25, "est": False,
                          "paid": "listed", "f": NOW.isoformat(timespec="seconds")})
        self.assertEqual(it["r"], ["In United States", "Posted 1d ago"])
        for where, away in (("USA - New Jersey - Rahway", False), ("Auburn Hills - Michigan - USA", False), ("London, United Kingdom", True)):
            self.assertEqual(pagefeed.build([job(1, location=where)], config.DEFAULT_SEARCH, now=NOW)[0][0]["items"][0]["x"], away, where)  # area, pay and "Internship" show on the card itself
        self.assertEqual(meta["updated_at"], "2026-10-18T12:00:00+00:00")

    def test_pages_and_counts(self):
        jobs = [job(i, 1, score=i, location="London, United Kingdom" if i % 2 else "Austin, TX") for i in range(130)]
        pages, meta = pagefeed.build(jobs, config.DEFAULT_SEARCH, now=NOW)
        self.assertEqual([len(p["items"]) for p in pages], [60, 60, 10])
        self.assertEqual([p["n"] for p in pages], [0, 1, 2])
        self.assertEqual(pages[0]["items"][0]["s"], 129)  # (one company: the top-of-list cap only reorders)  # best match first
        self.assertEqual((meta["total"], meta["in_reach"], meta["with_pay"], meta["pages"]), (130, 65, 130, 3))
        self.assertEqual(meta["by_source"], {"Workday": 130})

    def test_first_seen_times_come_from_the_current_list(self):
        with tempfile.TemporaryDirectory() as d:
            saved = Path(d) / "jobs"
            saved.mkdir()
            # As ArtifactData saves documents, and as page-feed writes them.
            (saved / "p0.json").write_text(json.dumps({"id": "p0", "data": {"n": 0, "items": [{"k": "a", "f": "2026-10-01T00:00:00+00:00"}]}}))
            (saved / "p1.json").write_text(json.dumps({"n": 1, "items": [{"k": "b", "f": "2026-10-02T00:00:00+00:00"}]}))
            self.assertEqual(pagefeed.previous_first_seen(d), {"a": "2026-10-01T00:00:00+00:00", "b": "2026-10-02T00:00:00+00:00"})

    def test_write_replaces_the_old_pages(self):
        with tempfile.TemporaryDirectory() as d:
            pagefeed.write(d, [{"n": 0, "items": []}, {"n": 1, "items": []}], {"total": 0})
            pagefeed.write(d, [{"n": 0, "items": []}], {"total": 0})
            self.assertEqual(sorted(p.name for p in (Path(d) / "pages").iterdir()), ["p0.json"])
            self.assertEqual(json.loads((Path(d) / "meta.json").read_text()), {"total": 0})


if __name__ == "__main__":
    unittest.main()


class CardTests(unittest.TestCase):
    """Fewer repeats: one card per company + title, a mix of companies at the top, newer postings first."""

    def test_same_title_in_several_locations_is_one_card(self):
        jobs = [job(i, title="Sales Intern", company="CHS", location=loc, score=80 - i)
                for i, loc in enumerate(["Houston, TX", "Austin, TX", "Remote"])]
        pages, meta = pagefeed.build(jobs, config.DEFAULT_SEARCH, now=NOW)
        items = pages[0]["items"]
        self.assertEqual(len(items), 1)
        card = items[0]
        self.assertEqual((card["k"], card["n"]), ("workday:acme:R0", 3))
        self.assertEqual([m["k"] for m in card["more"]], ["workday:acme:R1", "workday:acme:R2"])
        self.assertTrue(card["rm"])
        self.assertEqual((meta["postings"], meta["grouped"], meta["total"]), (3, 2, 1))

    def test_one_company_cannot_fill_the_top(self):
        jobs = [job(i, score=99) for i in range(5)] + [job(10 + i, company=f"Other{i}", score=90) for i in range(3)]
        items = pagefeed.build(jobs, config.DEFAULT_SEARCH, now=NOW)[0][0]["items"]
        self.assertEqual([i["c"] for i in items[:6]], ["Acme"] * 3 + ["Other0", "Other1", "Other2"])
        self.assertEqual([i["c"] for i in items[6:]], ["Acme", "Acme"])

    def test_newer_postings_get_a_boost(self):
        jobs = [job(1, days_ago=20, score=80), job(2, days_ago=0, score=75, company="Fresh")]
        items = pagefeed.build(jobs, config.DEFAULT_SEARCH, now=NOW)[0][0]["items"]
        self.assertEqual([i["c"] for i in items], ["Fresh", "Acme"])
        self.assertEqual(items[0]["s"], 75)  # the score shown is unchanged

    def test_new_since_the_last_list(self):
        seen = {"workday:acme:R1": (NOW - timedelta(days=2)).isoformat()}
        pages, meta = pagefeed.build([job(1), job(2)], config.DEFAULT_SEARCH, seen, now=NOW)
        new = {i["k"]: i["new"] for i in pages[0]["items"]}
        self.assertEqual(new, {"workday:acme:R1": False, "workday:acme:R2": True})
        self.assertEqual(meta["new_this_run"], 1)

    def test_logo_profile_and_fortune_500_flag(self):
        pages, meta = pagefeed.build([job(1, company="Amazon"), job(2, company="Gusto")], config.DEFAULT_SEARCH, now=NOW)
        cards = {i["c"]: i for i in pages[0]["items"]}
        amazon, gusto = cards["Amazon"], cards["Gusto"]
        self.assertEqual((amazon["f500"], amazon["rank"], amazon["dom"], amazon["ini"]), (True, 1, "amazon.com", "A"))
        self.assertIn("domain=amazon.com", amazon["logo"])
        self.assertEqual(amazon["car"], "https://amazon.jobs/en/")
        self.assertFalse(gusto["f500"])
        self.assertNotIn("logo", gusto)  # the page shows the initials instead
        self.assertNotIn("rank", gusto)
        self.assertEqual(meta["non_f500"], ["Gusto"])

    def test_initials(self):
        self.assertEqual(pagefeed.initials("C.H. Robinson Worldwide"), "CH")
        self.assertEqual(pagefeed.initials("The Home Depot"), "HD")
        self.assertEqual(pagefeed.initials(""), "?")
