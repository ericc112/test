import unittest
from unittest import mock

from jobbot import db, pipeline, sources
from jobbot.sources import make_job

from .helpers import PROFILE, TempData


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        db.set_setting("profile", PROFILE)
        search = db.get_setting("search")
        search.update(field="business", job_types=["full_time"], keywords=[], locations=["Remote"],
                      sources={n: False for n in sources.REGISTRY})
        search["sources"]["greenhouse"] = search["sources"]["remotive"] = True
        search["companies"]["greenhouse"] = ["acme"]
        db.set_setting("search", search)

    def tearDown(self):
        self.tmp.close()

    def fake_fetch(self, source):
        def fetch(key, search, known=None):
            if source == "greenhouse":
                return [make_job("greenhouse", "acme:1", "Financial Analyst", "Acme", "https://acme.com/1",
                                 ats="greenhouse", ats_board="acme", ats_job_id="1", remote=True, location="Remote",
                                 description="Bachelor's degree in finance or accounting. Excel.", categories=["Finance"]),
                        make_job("greenhouse", "acme:2", "Senior Software Engineer", "Acme", "https://acme.com/2",
                                 remote=True, location="Remote", categories=["Engineering"])]
            return [make_job("remotive", "77", "Financial Analyst", "Acme Inc", "https://remotive.com/77", remote=True,
                             location="Remote", description="excel")]
        return fetch

    def run_search(self):
        with mock.patch.object(sources.REGISTRY["greenhouse"], "fetch", self.fake_fetch("greenhouse")), \
             mock.patch.object(sources.REGISTRY["remotive"], "fetch", self.fake_fetch("remotive")):
            return pipeline.run_search()

    def test_search_filters_scores_and_dedupes(self):
        summary = self.run_search()
        self.assertEqual(summary["new"], 2)
        gh = db.get_job("greenhouse:acme:1")
        rm = db.get_job("remotive:77")
        self.assertIsNone(db.get_job("greenhouse:acme:2"))  # not a business role: not stored
        self.assertGreater(gh["score"], 50)
        self.assertIn("Finance & Accounting role", gh["score_reasons"])
        self.assertIn("Asks for a business degree", gh["score_reasons"])
        self.assertEqual(gh["categories"], ["Finance"])
        # Same job on two boards: keep the one we can apply to directly.
        self.assertEqual({gh["status"], rm["status"]}, {"new", "duplicate"})
        self.assertEqual(gh["status"], "new")

    def test_search_stores_pay_stated_in_the_posting(self):
        def gh_fetch(key, search, known=None):
            return [make_job("greenhouse", "acme:9", "Financial Analyst", "Acme", "https://acme.com/9",
                             ats="greenhouse", ats_board="acme", ats_job_id="9", remote=True, location="Remote",
                             description="Bachelor's degree in finance. The pay range for this role is "
                                         "$28.00 - $33.00 per hour.",
                             categories=["Finance"])]
        with mock.patch.object(sources.REGISTRY["greenhouse"], "fetch", gh_fetch), \
             mock.patch.object(sources.REGISTRY["remotive"], "fetch", lambda key, search, known=None: []):
            pipeline.run_search()
        job = db.get_job("greenhouse:acme:9")
        self.assertEqual((job["pay_text"], job["pay_min"], job["pay_max"]),
                         ("$28.00 - $33.00 per hour", 28.0, 33.0))

    def test_same_title_on_one_board_is_not_a_duplicate(self):
        for n in (1, 2):
            job = make_job("lever", f"acme:{n}", "Account Executive", "Acme", "u")
            db.upsert_job(job)
            pipeline._dedupe(job)
        self.assertEqual({db.get_job(f"lever:acme:{n}")["status"] for n in (1, 2)}, {"new"})

    def test_rate_limit_skips_recent_feeds(self):
        self.run_search()
        summary = self.run_search()
        self.assertEqual(summary["fetched"], [])
        self.assertEqual({s["source"] for s in summary["skipped"]}, {"greenhouse", "remotive"})

    def test_upsert_keeps_user_fields(self):
        self.run_search()
        db.update_job("greenhouse:acme:1", status="skipped", answers={"Why us?": "Because"})
        db.upsert_job(make_job("greenhouse", "acme:1", "Financial Analyst II", "Acme", "u"))
        j = db.get_job("greenhouse:acme:1")
        self.assertEqual((j["title"], j["status"], j["answers"]), ("Financial Analyst II", "skipped", {"Why us?": "Because"}))

    def test_rescore_hides_newly_excluded_and_restores(self):
        self.run_search()
        s = db.get_setting("search")
        s["exclude"] = ["financial"]
        db.set_setting("search", s)
        pipeline.rescore()
        self.assertEqual(db.get_job("greenhouse:acme:1")["status"], "skipped")
        s["exclude"] = []
        db.set_setting("search", s)
        pipeline.rescore()
        self.assertEqual(db.get_job("greenhouse:acme:1")["status"], "new")

    def test_auto_submit_policy(self):
        self.run_search()
        job = db.get_job("greenhouse:acme:1")
        job["score"] = 90
        auto = dict(db.get_setting("automation"), auto_submit=True, submit_min_score=75, daily_limit=1, company_limit_30d=5)
        ok, _ = pipeline.can_auto_submit(job, {"fields": [{"source": "profile"}]}, auto)
        self.assertTrue(ok)
        ok, why = pipeline.can_auto_submit(job, {"fields": [{"source": "ai"}]}, auto)
        self.assertFalse(ok)
        self.assertIn("AI", why)
        ok, why = pipeline.can_auto_submit(dict(job, ats="generic"), {"fields": []}, auto)
        self.assertFalse(ok)
        # Workday and Taleo have engines of their own that confirm what they send.
        wd = dict(job, ats="account", apply_url="https://acme.wd5.myworkdayjobs.com/Careers/job/Dallas/Intern_R1")
        self.assertEqual(pipeline.can_auto_submit(wd, {"fields": []}, auto), (True, ""))
        db.update_job("remotive:77", status="applied", applied_at=db.now())
        ok, why = pipeline.can_auto_submit(job, {"fields": []}, auto)
        self.assertEqual((ok, why), (False, "daily limit reached"))
        ok, why = pipeline.can_auto_submit(job, {"fields": []}, dict(auto, auto_submit=False))
        self.assertFalse(ok)

    def test_switching_field_off_allows_any_role(self):
        s = db.get_setting("search")
        s["field"] = ""
        db.set_setting("search", s)
        self.run_search()
        self.assertIsNotNone(db.get_job("greenhouse:acme:2"))

    def test_rescore_hides_old_non_business_jobs(self):
        db.upsert_job(make_job("lever", "x:1", "Software Engineer", "Zed", "u", status="new"))
        pipeline.rescore()
        j = db.get_job("lever:x:1")
        self.assertEqual((j["status"], j["status_note"]), ("skipped", "auto: Not a business role"))

    def test_rescore_ages_out_a_job_that_vanished_from_its_feed(self):
        from datetime import datetime, timedelta, timezone
        db.upsert_job(make_job("remotive", "gone:1", "Financial Analyst", "Acme", "u", remote=True,
                               location="Remote", description="excel"))
        old = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat(timespec="seconds")
        db.update_job("remotive:gone:1", last_seen=old)  # the feed stopped returning it weeks ago
        pipeline.rescore()
        j = db.get_job("remotive:gone:1")
        self.assertEqual(j["status"], "skipped")
        self.assertIn("No longer listed", j["status_note"])

    def test_highest_pay_sort_counts_extracted_pay(self):
        # Greenhouse/Workday jobs only ever get pay_* (extracted); the sort used to ignore it.
        db.upsert_job(make_job("lever", "p:1", "Analyst", "A Co", "u1", salary_min=10.0, salary_max=10.0))
        db.upsert_job(make_job("greenhouse", "p:2", "Analyst", "B Co", "u2",
                               pay_min=20.0, pay_max=25.0, pay_text="$20-25/hr"))
        db.upsert_job(make_job("greenhouse", "p:3", "Analyst", "C Co", "u3"))
        jobs, _ = db.list_jobs(sort="pay")
        self.assertEqual([j["id"] for j in jobs], ["greenhouse:p:2", "lever:p:1", "greenhouse:p:3"])

    def test_applied_counts_split_confirmed_from_unconfirmed(self):
        db.upsert_job(make_job("lever", "a:1", "Analyst", "A Co", "u", status="applied", applied_at=db.now()))
        db.upsert_job(make_job("lever", "a:2", "Analyst", "B Co", "u", status="unconfirmed", applied_at=db.now()))
        self.assertEqual(db.applied_since(24), 1)  # confirmed only: unconfirmed no longer inflates it
        self.assertEqual(db.unconfirmed_since(24), 1)

    def test_switching_to_internships_hides_full_time_and_back(self):
        self.run_search()
        s = db.get_setting("search")
        s["job_types"] = ["internship"]
        db.set_setting("search", s)
        pipeline.rescore()
        self.assertEqual(db.get_job("greenhouse:acme:1")["status_note"], "auto: Not an internship")
        s["job_types"] = ["internship", "full_time"]
        db.set_setting("search", s)
        pipeline.rescore()
        self.assertEqual(db.get_job("greenhouse:acme:1")["status"], "new")

    def test_settings_merge_new_defaults(self):
        db.set_setting("automation", {"enabled": True})
        a = db.get_setting("automation")
        self.assertTrue(a["enabled"])
        self.assertEqual(a["daily_limit"], 15)


if __name__ == "__main__":
    unittest.main()


class WatchListUpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()

    def tearDown(self):
        self.tmp.close()

    def test_saved_searches_pick_up_new_default_employers_once(self):
        from jobbot import config
        with mock.patch.dict(config.DEFAULT_SEARCH["companies"], {"oracle": ["jpmc.fa.oraclecloud.com|CX_1001"],
                                                                 "workday": ["acme|wd5|Careers", "new|wd1|Jobs"]}), \
             mock.patch.object(config, "WATCHLIST_VERSION", 2):
            db.set_setting("search", {"companies": {"workday": ["acme|wd5|Careers", "mine|wd3|X"]}})  # saved before the upgrade
            s = db.get_setting("search")
            self.assertEqual(s["companies"]["workday"], ["acme|wd5|Careers", "mine|wd3|X", "new|wd1|Jobs"])
            self.assertEqual(s["companies"]["oracle"], ["jpmc.fa.oraclecloud.com|CX_1001"])
            s["companies"]["workday"].remove("new|wd1|Jobs")  # you remove one afterwards: it stays removed
            db.set_setting("search", s)
            self.assertNotIn("new|wd1|Jobs", db.get_setting("search")["companies"]["workday"])

    def test_upgrade_drops_feeds_that_belong_to_other_companies(self):
        from jobbot import config
        with mock.patch.object(config, "RETIRED_FEEDS", {"workday": ["cc|wd3|ChanelCareers"]}), \
             mock.patch.object(config, "WATCHLIST_VERSION", 3):
            db.set_setting("search", {"watchlist_version": 2,
                                      "companies": {"workday": ["cc|wd3|ChanelCareers", "mine|wd3|X"]}})
            s = db.get_setting("search")
            self.assertNotIn("cc|wd3|ChanelCareers", s["companies"]["workday"])
            self.assertIn("mine|wd3|X", s["companies"]["workday"])
            self.assertEqual(s["watchlist_version"], 3)


class ExtraCompaniesTests(unittest.TestCase):
    def test_verified_extra_employers_are_watched_by_default(self):
        from jobbot import config
        suggested = {(kind, slug) for _, kind, slug in config.SUGGESTED_COMPANIES}
        self.assertIn(("greenhouse", "flyzipline"), suggested)  # Zipline
        self.assertIn(("greenhouse", "uberfreight"), suggested)  # Uber Freight
        self.assertIn(("workday", "uline|wd1|Uline_Careers"), suggested)  # Uline
        companies = config.DEFAULT_SEARCH["companies"]
        self.assertIn("flyzipline", companies["greenhouse"])
        self.assertIn("uberfreight", companies["greenhouse"])

    def test_every_verified_extra_feed_is_wired_in(self):
        from jobbot import config
        suggested = {(kind, slug) for _, kind, slug in config.SUGGESTED_COMPANIES}
        missing = [(c["company"], c["ats"], c["feedId"]) for c in config.EXTRA_COMPANIES
                   if c.get("feedVerified") and (c["ats"], c["feedId"]) not in suggested]
        self.assertEqual(missing, [])
