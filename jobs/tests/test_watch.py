import io
import unittest
import urllib.error
from datetime import datetime, timezone
from unittest import mock

from jobbot import db, pipeline, sources
from jobbot.sources import http, make_job, workday

from .helpers import PROFILE, TempData


class Resp(io.BytesIO):
    def __init__(self, body, etag=None, url="https://x"):
        super().__init__(body)
        self.headers = {"ETag": etag} if etag else {}
        self._url = url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class ConditionalRequestTests(unittest.TestCase):
    def tearDown(self):
        http.forget_etags()

    def test_etag_round_trip(self):
        seen_headers = []

        def urlopen(req, timeout=None):
            seen_headers.append(dict(req.header_items()))
            if len(seen_headers) == 1:
                return Resp(b'{"jobs": []}', etag='W/"abc"')
            raise urllib.error.HTTPError(req.full_url, 304, "Not Modified", {}, None)

        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            self.assertEqual(http.get_json("https://b/jobs", conditional=True), {"jobs": []})
            with self.assertRaises(http.NotModified):
                http.get_json("https://b/jobs", conditional=True)
        self.assertNotIn("If-none-match", seen_headers[0])
        self.assertEqual(seen_headers[1]["If-none-match"], 'W/"abc"')


def wd_page(ids, posted="Posted Today"):
    return {"total": 500, "jobPostings": [
        {"title": t, "externalPath": f"/job/NYC/{i}", "locationsText": "New York, NY", "postedOn": posted, "bulletFields": [i]}
        for i, t in ids]}


class WorkdayTests(unittest.TestCase):
    KEY = "acme|wd5|Careers"
    SEARCH = {"field": "business"}

    def setUp(self):
        workday._looked_at.clear()

    def test_posted_text(self):
        now = datetime(2026, 10, 16, 15, tzinfo=timezone.utc)
        self.assertTrue(workday.posted_from_text("Posted Today", now).startswith("2026-10-16"))
        self.assertTrue(workday.posted_from_text("Posted Yesterday", now).startswith("2026-10-15"))
        self.assertTrue(workday.posted_from_text("Posted 3 Days Ago", now).startswith("2026-10-13"))
        self.assertTrue(workday.posted_from_text("Posted 30+ Days Ago", now).startswith("2026-09-16"))
        self.assertEqual(workday.key_from_url("https://citi.wd5.myworkdayjobs.com/en-US/2/job/x"), "citi|wd5|2")

    def test_fetch_new_business_jobs_with_details(self):
        page = wd_page([("R1", "Financial Analyst"), ("R2", "Software Engineer")])
        page["jobPostings"] += page["jobPostings"][:1] * 0
        detail = {"jobPostingInfo": {"jobDescription": "<p>Excel</p>", "startDate": "2026-10-16",
                                     "location": "New York, NY", "externalUrl": "https://acme.wd5.myworkdayjobs.com/Careers/job/NYC/R1"}}
        with mock.patch.object(http, "post_json", return_value=page) as post, \
             mock.patch.object(http, "get_json", return_value=detail) as get:
            jobs = workday.fetch(self.KEY, self.SEARCH)
        self.assertEqual([j["title"] for j in jobs], ["Financial Analyst"])
        j = jobs[0]
        self.assertEqual((j["id"], j["ats"], j["description"]), ("workday:acme:R1", "manual", "Excel"))
        self.assertEqual(get.call_count, 1)  # the engineer never got a detail request
        self.assertEqual(post.call_count, 1)  # short page: no more pages

    def test_paging_stops_once_caught_up(self):
        full = wd_page([(f"R{i}", "Financial Analyst") for i in range(20)])
        known = {f"workday:acme:R{i}" for i in range(20)}
        with mock.patch.object(http, "post_json", return_value=full) as post, \
             mock.patch.object(http, "get_json", return_value={"jobPostingInfo": {}}):
            self.assertEqual(workday.fetch(self.KEY, self.SEARCH, known=known), [])
        self.assertEqual(post.call_count, 1)


class WatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        db.set_setting("profile", PROFILE)
        s = db.get_setting("search")
        s.update(sources={n: n == "greenhouse" for n in sources.REGISTRY}, locations=["Remote"],
                 companies={"greenhouse": ["acme"], "lever": [], "ashby": [], "workday": []})
        db.set_setting("search", s)
        db.set_setting("automation", dict(db.get_setting("automation"), watch_minutes=5, prepare_min_score=10))
        self.queued = []
        self.watcher = pipeline.Watcher(lambda job_id, action: self.queued.append((job_id, action)))
        pipeline._filtered_out.clear()

    def tearDown(self):
        self.tmp.close()

    def job(self, n, title="Financial Analyst"):
        return make_job("greenhouse", f"acme:{n}", title, "Acme", f"https://acme/{n}", ats="greenhouse",
                        ats_board="acme", ats_job_id=str(n), remote=True, location="Remote",
                        posted_at=db.now(), description="Excel modeling", categories=["Finance"])

    def tick(self, result):
        self.watcher.last_poll.clear()  # make every board due
        gh = sources.REGISTRY["greenhouse"]
        kw = {"side_effect": result} if isinstance(result, Exception) else {"return_value": result}
        with mock.patch.object(gh, "fetch", **kw) as fetch:
            fresh = self.watcher.tick()
        return fresh, fetch

    def test_first_look_is_backfill_then_new_postings_are_fresh(self):
        fresh, _ = self.tick([self.job(1)])
        self.assertEqual(fresh, [])
        self.assertEqual(db.get_job("greenhouse:acme:1")["fresh"], 0)
        self.assertEqual(self.queued, [])

        fresh, fetch = self.tick([self.job(2), self.job(3, "Software Engineer")])
        self.assertEqual([j["id"] for j in fresh], ["greenhouse:acme:2"])
        self.assertEqual(db.get_job("greenhouse:acme:2")["fresh"], 1)
        self.assertIn("greenhouse:acme:1", fetch.call_args.kwargs["known"])
        self.assertEqual(self.queued, [("greenhouse:acme:2", "prepare")])  # filled right away
        events = [e["message"] for e in db.recent_events()]
        self.assertTrue(any(m.startswith("Just posted at Acme: Financial Analyst") for m in events))
        self.assertEqual(db.fresh_jobs()[1], 1)

    def test_unchanged_board_costs_nothing(self):
        self.tick([self.job(1)])
        fresh, _ = self.tick(http.NotModified("u"))
        self.assertEqual(fresh, [])
        self.assertTrue(db.last_source_run("greenhouse", "acme")["ok"])

    def test_boards_are_not_polled_again_before_interval(self):
        self.tick([self.job(1)])
        with mock.patch.object(sources.REGISTRY["greenhouse"], "fetch", return_value=[]) as fetch:
            self.watcher.tick()
        fetch.assert_not_called()

    def test_failures_are_logged_once(self):
        self.tick(http.FetchError("HTTP 500"))
        self.tick(http.FetchError("HTTP 500"))
        warnings = [e for e in db.recent_events() if "Watching greenhouse" in e["message"]]
        self.assertEqual(len(warnings), 1)

    def test_changing_the_search_re_evaluates_filtered_jobs(self):
        self.tick([self.job(1)])
        self.tick([self.job(2, "Software Engineer")])  # filtered out, remembered
        self.assertIn("greenhouse:acme:2", pipeline._filtered_out)
        pipeline.search_changed()
        self.assertNotIn("greenhouse:acme:2", pipeline._filtered_out)
        self.assertEqual(db.last_source_run("greenhouse", "acme")["count"], 1)  # board total, not just new ones

    def test_watch_can_be_turned_off(self):
        db.set_setting("automation", dict(db.get_setting("automation"), watch_enabled=False))
        _, fetch = self.tick([self.job(1)])
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
