"""Importing a Muse board export into the local database: statuses, pay, dedupe."""
import contextlib
import io
import json
import unittest
from pathlib import Path

from jobbot import db
from jobbot.__main__ import main

from .helpers import TempData

EXPORT = {
    "jobs": [
        {"id": 1, "title": "Supply Chain Intern", "company": "Zipline",
         "locations": ["South San Francisco, CA"], "url": "https://example.com/jobs/1",
         "status": "review", "payText": "$37/hr", "payMin": 37, "payMax": 37,
         "term": "Summer 2027", "note": None, "needsNote": None, "appliedAt": None,
         "postedAt": "2026-10-19T00:00:00+00:00"},
        {"id": 2, "title": "Procurement Intern", "company": "Acme", "locations": ["Houston, TX"],
         "url": None, "status": "applied", "payText": None, "payMin": None, "payMax": None,
         "term": None, "note": "Req 123", "needsNote": None, "appliedAt": "2026-10-08",
         "postedAt": None},
        {"id": 3, "title": "Operations Intern", "company": "Beta", "locations": [],
         "url": "https://example.com/jobs/3", "status": "applying", "payText": None,
         "payMin": None, "payMax": None, "term": None, "note": None,
         "needsNote": "Create your account first", "appliedAt": None, "postedAt": None},
        {"id": 4, "title": "Logistics Intern", "company": "Gamma", "locations": [],
         "url": "https://example.com/jobs/4", "status": "applying", "payText": None,
         "payMin": None, "payMax": None, "term": None, "note": None, "needsNote": None,
         "appliedAt": None, "postedAt": None},
        {"id": 5, "title": "Warehouse Intern", "company": "Delta", "locations": [],
         "url": "https://example.com/jobs/5", "status": "removed", "payText": None,
         "payMin": None, "payMax": None, "term": None, "note": None, "needsNote": None,
         "appliedAt": None, "postedAt": None},
    ],
    "profile": {"fullName": "Test Applicant"},
}


class ImportBoardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        self.file = Path(self.tmp.dir) / "board.json"
        self.file.write_text(json.dumps(EXPORT))

    def tearDown(self):
        self.tmp.close()

    def run_import(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["import-board", str(self.file)])
        return buf.getvalue()

    def test_statuses_pay_and_notes_survive(self):
        out = self.run_import()
        self.assertIn("Imported 5", out)
        j1 = db.get_job("board:1")
        self.assertEqual(j1["status"], "new")  # review -> new
        self.assertEqual((j1["pay_text"], j1["pay_min"], j1["pay_max"]), ("$37/hr", 37.0, 37.0))
        self.assertEqual(j1["location"], "South San Francisco, CA")
        self.assertIn("Summer 2027", j1["status_note"])
        j2 = db.get_job("board:2")
        self.assertEqual(j2["status"], "applied")
        self.assertEqual(j2["applied_at"], "2026-10-08")
        self.assertIn("verified submission", j2["status_note"])
        self.assertIn("Req 123", j2["status_note"])
        self.assertEqual(db.get_job("board:3")["status"], "needs_input")  # applying + needsNote
        self.assertIn("Create your account first", db.get_job("board:3")["status_note"])
        self.assertEqual(db.get_job("board:4")["status"], "queued")  # applying, nothing blocking
        self.assertEqual(db.get_job("board:5")["status"], "skipped")  # removed (local equivalent)

    def test_second_import_inserts_nothing(self):
        self.run_import()
        out = self.run_import()
        self.assertIn("Imported 0", out)
        self.assertIn("5 already in JobBot", out)


if __name__ == "__main__":
    unittest.main()
