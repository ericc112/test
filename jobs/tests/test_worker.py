"""Which engine applies to a job: the worker's routing. Engines and lookups are faked: no browser, no network."""
import os
import unittest
from unittest import mock

from jobbot import db, finder
from jobbot.apply.engine import Engine, Result
from jobbot.apply.workday import WorkdayEngine
from jobbot.worker import Worker

from .helpers import PROFILE, TempData

WD = "https://acme.wd1.myworkdayjobs.com/Careers/job/Houston/Supply-Chain-Intern_R1"


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for key in ("JOBBOT_WORKDAY_EMAIL", "JOBBOT_WORKDAY_PASSWORD"):
            os.environ.pop(key, None)
        self.used = []

    def tearDown(self):
        self.tmp.close()

    def job(self, url, password="Str0ng!Pass1", **kw):
        db.set_setting("profile", dict(PROFILE, workday_password=password))
        job = {"id": "link:1", "source": "other", "title": kw.get("title", "Job at example.com"), "company": "Acme",
               "url": url, "apply_url": url, "dedupe_key": "link:1", "posted_at": None}
        db.upsert_job(job)
        return job["id"]

    def engine(self, cls, result):
        def run(engine, job, ctx, mode="prepare"):
            self.used.append((cls.__name__, job.get("apply_url")))
            return result(job) if callable(result) else result
        return mock.patch.object(cls, "run", run)

    def test_a_linkedin_job_found_on_workday_goes_to_the_workday_engine(self):
        jid = self.job("https://www.linkedin.com/jobs/view/supply-chain-intern-at-acme-4464168018")
        info = {"title": "Supply Chain Intern", "company": "Acme", "location": "Houston, TX", "website": ""}
        with mock.patch.object(finder, "details", return_value=info), mock.patch.object(finder, "find", return_value=WD), \
                self.engine(WorkdayEngine, Result("ready", "Filled.")):
            Worker().process(jid, "prepare")
        self.assertEqual(self.used, [("WorkdayEngine", WD)])
        self.assertEqual((db.get_job(jid)["status"], db.get_job(jid)["title"]), ("ready", "Supply Chain Intern"))

    def test_apply_leading_to_workday_is_handed_to_its_engine(self):
        jid = self.job("https://careers.acme.com/jobs/1")
        with mock.patch("jobbot.ats.resolve", return_value={"ats": "generic", "apply_url": "https://careers.acme.com/jobs/1"}), \
                self.engine(Engine, Result("moved", "The application is on acme.wd1.myworkdayjobs.com.", url=WD)), \
                self.engine(WorkdayEngine, Result("applied", "Submitted.")):
            Worker().process(jid, "submit")
        self.assertEqual([name for name, _ in self.used], ["Engine", "WorkdayEngine"])
        self.assertEqual(db.get_job(jid)["status"], "applied")

    def test_a_sign_in_site_without_a_password_is_yours_to_apply(self):
        jid = self.job("https://careers-acme.icims.com/jobs/1234/intern/job", password="")
        Worker().process(jid, "prepare")
        job = db.get_job(jid)
        self.assertEqual(job["status"], "manual")
        self.assertIn("JOBBOT_WORKDAY_PASSWORD", job["status_note"])

    def test_a_sign_in_site_with_a_password_goes_to_the_engine(self):
        jid = self.job("https://careers-acme.icims.com/jobs/1234/intern/job")
        with self.engine(Engine, Result("ready", "Filled.")):
            Worker().process(jid, "prepare")
        self.assertEqual(self.used, [("Engine", "https://careers-acme.icims.com/jobs/1234/intern/job")])

    def test_a_job_board_posting_not_found_on_the_employers_site(self):
        jid = self.job("https://www.indeed.com/viewjob?jk=abc", title="Buyer Intern")
        with mock.patch.object(finder, "details", return_value=None), mock.patch.object(finder, "find", return_value=None):
            Worker().process(jid, "prepare")
        job = db.get_job(jid)
        self.assertEqual(job["status"], "manual")
        self.assertIn("Couldn't find this job", job["status_note"])

    def test_a_closed_posting_becomes_a_closed_job(self):
        jid = self.job("https://careers-acme.icims.com/jobs/1234/intern/job")
        with self.engine(Engine, Result("closed", "This posting is no longer up (the employer closed it), so nothing was sent.")):
            Worker().process(jid, "prepare")
        self.assertEqual(db.get_job(jid)["status"], "closed")

    def test_a_job_skipped_while_queued_is_never_processed(self):
        jid = self.job("https://careers-acme.icims.com/jobs/1234/intern/job")
        db.update_job(jid, status="skipped", status_note="Skipped by you")
        with self.engine(Engine, Result("ready", "Filled.")):
            Worker().process(jid, "prepare")
        self.assertEqual(self.used, [])  # removing a queued application cancels it
        self.assertEqual(db.get_job(jid)["status"], "skipped")

    def test_remove_takes_a_job_out_of_the_queue(self):
        jid = self.job("https://careers-acme.icims.com/jobs/1234/intern/job")
        w = Worker()
        self.assertTrue(w.enqueue(jid, "prepare"))
        self.assertEqual(db.get_job(jid)["status"], "queued")
        self.assertEqual(w.remove(jid), 1)
        self.assertEqual(w.snapshot()["pending"], [])
        self.assertEqual(db.get_job(jid)["status"], "new")


if __name__ == "__main__":
    unittest.main()
