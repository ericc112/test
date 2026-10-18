import json
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


if __name__ == "__main__":
    unittest.main()
