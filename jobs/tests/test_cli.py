import json
import time
import unittest
from types import SimpleNamespace
from unittest import mock

from jobbot import __main__ as cli, db
from jobbot.worker import Worker

from .helpers import TempData


class ApplyBatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        self.requests = self.tmp.dir / "requests.json"
        self.out = self.tmp.dir / "results.json"
        self.requests.write_text(json.dumps([
            {"k": "greenhouse:acme:1", "mode": "submit", "title": "Finance Intern", "company": "Acme",
             "url": "https://boards.greenhouse.io/acme/jobs/1", "source": "Greenhouse"},
            {"k": "greenhouse:acme:2", "mode": "submit", "title": "Marketing Intern", "company": "Acme",
             "url": "https://boards.greenhouse.io/acme/jobs/2", "source": "Greenhouse"},
        ]))

    def tearDown(self):
        self.tmp.close()

    def test_results_are_saved_after_each_application(self):
        # The cloud runner's command can be cut off by a time limit: what finished must already be on disk.
        def process(self_, job_id, mode):
            if job_id.endswith(":2"):
                raise KeyboardInterrupt  # the command was killed here
            db.update_job(job_id, status="applied", status_note="Submitted.")

        args = SimpleNamespace(requests=str(self.requests), profile=None, resume=None, out=str(self.out))
        with mock.patch.object(Worker, "process", process), self.assertRaises(KeyboardInterrupt):
            cli.cmd_apply_batch(args)
        results = json.loads(self.out.read_text())
        self.assertEqual([(r["k"], r["mode"], r["status"]) for r in results], [("greenhouse:acme:1", "submit", "applied")])

    def test_the_answer_bank_in_your_profile_is_used(self):
        profile = self.tmp.dir / "profile.json"
        profile.write_text(json.dumps({"first_name": "Test", "answer_bank": [
            {"q": "valid driver's license", "a": "Yes"}, {"q": "debar", "a": "No", "regex": True}, {"bad": 1}]}))
        args = SimpleNamespace(requests=str(self.requests), profile=str(profile), resume=None, out=str(self.out))
        with mock.patch.object(Worker, "process", lambda self_, job_id, mode: None):
            cli.cmd_apply_batch(args)
        bank = db.get_setting("answers")
        self.assertEqual(bank[:2], [{"q": "valid driver's license", "a": "Yes"}, {"q": "debar", "a": "No", "regex": True}])
        self.assertEqual(sum(b["q"] == "debar" for b in bank), 1)  # yours replaces a default with the same question


    def test_time_limit_leaves_the_rest_for_the_next_run(self):
        done = []
        args = SimpleNamespace(requests=str(self.requests), profile=None, resume=None, out=str(self.out),
                               data=None, time_limit=0.001)

        def process(self_, job_id, mode):
            done.append(job_id)
            time.sleep(0.01)
            db.update_job(job_id, status="applied")

        with mock.patch.object(Worker, "process", process):
            cli.cmd_apply_batch(args)
        results = json.loads(self.out.read_text())
        self.assertEqual(done, ["greenhouse:acme:1"])
        self.assertEqual([r["status"] for r in results], ["applied", "not_started"])

    def test_data_option_picks_the_data_folder(self):
        from jobbot import config
        other = self.tmp.dir / "other"
        args = SimpleNamespace(requests=str(self.requests), profile=None, resume=None, out=str(self.out),
                               data=str(other), time_limit=0)
        try:
            with mock.patch.object(Worker, "process", lambda self_, job_id, mode: db.update_job(job_id, status="ready")):
                cli.cmd_apply_batch(args)
            self.assertTrue((other / "jobbot.db").exists())
        finally:
            config.use_data_dir(self.tmp.dir)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()

    def tearDown(self):
        self.tmp.close()

    def test_coverage_reports_the_wall_and_names_failing_feeds(self):
        import io
        from contextlib import redirect_stdout
        from jobbot import config
        watched = next(r for r in config.FORTUNE500 if r.get("status") == "watched" and r.get("feeds"))
        kind, slug = watched["feeds"][0]
        db.record_source_run(kind, slug, ok=False, count=0, error="HTTP 404")
        out = self.tmp.dir / "coverage.json"
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli.cmd_coverage(SimpleNamespace(out=str(out)))
        report = json.loads(out.read_text())
        self.assertEqual(report["companies"], len(config.FORTUNE500))
        self.assertEqual(report["watched"] + report["unsupported"] + report["no_public_feed"], report["companies"])
        self.assertEqual(report["feeds_failing"], [{"company": watched["name"], "feed": f"{kind}:{slug}",
                                                    "error": "HTTP 404", "when": report["feeds_failing"][0]["when"]}])
        self.assertIn(watched["name"], buf.getvalue())


if __name__ == "__main__":
    unittest.main()
