import unittest
from unittest import mock

from fastapi.testclient import TestClient

from jobbot import db, sources
from jobbot.server import create_app
from jobbot.sources import make_job

from .helpers import FIXTURES, TempData


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        self.client = TestClient(create_app(start_background=False), headers={"X-JobBot": "1"})
        db.upsert_job(make_job("greenhouse", "acme:1", "Backend Engineer", "Acme", "https://acme.com/1", ats="greenhouse"))
        self.jid = "greenhouse%3Aacme%3A1"

    def tearDown(self):
        self.tmp.close()

    def test_index_and_state(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        st = self.client.get("/api/state").json()
        self.assertEqual(st["counts"], {"new": 1})
        self.assertFalse(st["setup"]["resume"])

    def test_state_reports_source_health(self):
        db.record_source_run("greenhouse", "acme", True, 3)
        db.record_source_run("lever", "acme", False, 0, "HTTP 503 from api.lever.co")
        st = self.client.get("/api/state").json()
        health = st["source_health"]
        self.assertFalse(health["greenhouse"]["failing"])
        self.assertIsNotNone(health["greenhouse"]["last_success"])
        self.assertTrue(health["lever"]["failing"])
        self.assertIn("503", health["lever"]["last_error"])
        self.assertEqual(st["failing_sources"], ["lever"])
        self.assertIn("unconfirmed_24h", st)

    def test_profile_round_trip_keeps_resume(self):
        r = self.client.post("/api/upload/resume", files={"file": ("my resume.txt", (FIXTURES / "resume.txt").read_bytes(), "text/plain")})
        self.assertEqual(r.status_code, 200)
        self.assertGreater(r.json()["text_chars"], 20)
        p = self.client.get("/api/settings/profile").json()
        p["first_name"] = "Ada"
        p.pop("resume_file")
        self.assertEqual(self.client.put("/api/settings/profile", json=p).status_code, 200)
        p = self.client.get("/api/settings/profile").json()
        self.assertEqual((p["first_name"], p["resume_file"]), ("Ada", "my resume.txt"))

    def test_workday_password_round_trip(self):
        p = self.client.get("/api/settings/profile").json()
        p["workday_password"] = "hunter2-example"
        self.assertEqual(self.client.put("/api/settings/profile", json=p).status_code, 200)
        p = self.client.get("/api/settings/profile").json()
        self.assertEqual(p["workday_password"], "hunter2-example")
        # A later save that never mentions the password must not wipe it.
        p.pop("workday_password")
        p["first_name"] = "Ada"
        self.assertEqual(self.client.put("/api/settings/profile", json=p).status_code, 200)
        p = self.client.get("/api/settings/profile").json()
        self.assertEqual((p["first_name"], p["workday_password"]), ("Ada", "hunter2-example"))

    def test_upload_rejects_other_types(self):
        r = self.client.post("/api/upload/resume", files={"file": ("x.exe", b"MZ", "application/octet-stream")})
        self.assertEqual(r.status_code, 400)

    def test_api_key_is_never_returned(self):
        self.client.put("/api/settings/llm", json={"enabled": True, "api_key": "sk-ant-secret", "model": "claude-opus-5-5"})
        got = self.client.get("/api/settings/llm").json()
        self.assertEqual((got["api_key"], got["has_key"]), ("", True))
        # Saving again without a key keeps the stored one.
        self.client.put("/api/settings/llm", json={"enabled": True, "api_key": ""})
        self.assertEqual(db.get_setting("llm")["api_key"], "sk-ant-secret")
        self.client.put("/api/settings/llm", json={"enabled": False, "api_key": "", "clear_key": True})
        self.assertEqual(db.get_setting("llm")["api_key"], "")

    def test_job_actions(self):
        for action, status in (("skip", "skipped"), ("restore", "new"), ("mark_applied", "applied")):
            r = self.client.post(f"/api/jobs/{self.jid}/action", json={"action": action})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(self.client.get(f"/api/jobs/{self.jid}/detail").json()["status"], status)
        self.assertEqual(self.client.post(f"/api/jobs/{self.jid}/action", json={"action": "submit"}).status_code, 409)

    def test_companies_and_logos(self):
        db.upsert_job(make_job("workday", "amazon:1", "Supply Chain Intern", "Amazon", "https://amazon.com/1", ats="workday"))
        companies = self.client.get("/api/companies").json()
        self.assertEqual(companies["Amazon"]["rank"], 1)
        self.assertIn("amazon.com", companies["Amazon"]["logo"])
        row = next(j for j in self.client.get("/api/jobs").json()["jobs"] if j["company"] == "Amazon")
        self.assertEqual(row["company_info"]["rank"], 1)
        other = next(j for j in self.client.get("/api/jobs").json()["jobs"] if j["company"] == "Acme")
        self.assertIsNone(other["company_info"])  # not a Fortune 500 company: no logo, no rank, nothing invented

    def test_a_closed_job_cannot_be_filled_and_can_be_restored(self):
        db.update_job("greenhouse:acme:1", status="closed", status_note="This posting is no longer up")
        r = self.client.post(f"/api/jobs/{self.jid}/action", json={"action": "prepare"})
        self.assertEqual(r.status_code, 409)
        self.assertIn("closed", r.json()["detail"])
        r = self.client.post(f"/api/jobs/{self.jid}/action", json={"action": "restore"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(db.get_job("greenhouse:acme:1")["status"], "new")

    def test_skipping_a_queued_job_cancels_it(self):
        from jobbot import server
        from jobbot.worker import Worker
        w = Worker()
        server.State.worker = w
        try:
            self.assertTrue(w.enqueue("greenhouse:acme:1", "prepare"))
            r = self.client.post(f"/api/jobs/{self.jid}/action", json={"action": "skip"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(w.snapshot()["pending"], [])
            self.assertEqual(db.get_job("greenhouse:acme:1")["status"], "skipped")
        finally:
            server.State.worker = None

    def test_answers_saved_and_remembered(self):
        r = self.client.post(f"/api/jobs/{self.jid}/answers",
                             json={"answers": {"Why Acme?": "Great team"}, "remember": True, "refill": False})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(db.get_job("greenhouse:acme:1")["answers"], {"Why Acme?": "Great team"})
        self.assertIn({"q": "Why Acme?", "a": "Great team"}, db.get_setting("answers"))

    def test_cross_site_writes_and_foreign_hosts_are_refused(self):
        bare = TestClient(create_app(start_background=False))
        r = bare.post("/api/upload/resume", files={"file": ("evil.txt", b"x", "text/plain")})
        self.assertEqual(r.status_code, 403)
        r = self.client.get("/api/state", headers={"Host": "attacker.example"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(bare.get("/api/state").status_code, 200)

    def test_fields_and_suggestions(self):
        f = self.client.get("/api/fields").json()
        self.assertEqual(len(f["business"]["areas"]), 8)
        self.assertEqual(self.client.get("/api/suggestions").json(), [])  # all watched by default
        s = db.get_setting("search")
        s["companies"] = {"greenhouse": [], "lever": [], "ashby": [], "workday": []}
        db.set_setting("search", s)
        before = self.client.get("/api/suggestions").json()
        self.assertTrue(any(c["slug"] == "stripe" for c in before))
        s = db.get_setting("search")
        s["companies"]["greenhouse"] = ["stripe"]
        db.set_setting("search", s)
        after = self.client.get("/api/suggestions").json()
        self.assertFalse(any(c["slug"] == "stripe" for c in after))
        self.assertEqual(len(after), len(before) - 1)

    def test_screenshot_path_is_contained(self):
        self.assertEqual(self.client.get("/shots/..%2F..%2Fetc%2Fpasswd").status_code, 404)
        (self.tmp.dir / "screenshots" / "a.png").write_bytes(b"\x89PNG")
        self.assertEqual(self.client.get("/shots/a.png").status_code, 200)

    def test_company_detection_adds_boards(self):
        s = db.get_setting("search")
        s["companies"] = {"greenhouse": [], "lever": [], "ashby": [], "workday": []}
        db.set_setting("search", s)
        with mock.patch.object(sources.REGISTRY["greenhouse"], "probe", side_effect=lambda s: s == "acmecorp"), \
             mock.patch.object(sources.REGISTRY["lever"], "probe", return_value=False), \
             mock.patch.object(sources.REGISTRY["ashby"], "probe", side_effect=lambda s: s == "acme-corp"):
            r = self.client.post("/api/companies/detect", json={"name": "Acme Corp", "add": True}).json()
        self.assertEqual(sorted((f["ats"], f["slug"]) for f in r["found"]), [("ashby", "acme-corp"), ("greenhouse", "acmecorp")])
        companies = db.get_setting("search")["companies"]
        self.assertEqual((companies["greenhouse"], companies["ashby"]), (["acmecorp"], ["acme-corp"]))
        r = self.client.post("/api/companies/detect", json={"name": "https://jobs.lever.co/zeta/6ed76ce8-4156-4b60-b120-403538bd66cd"}).json()
        self.assertEqual(r["found"], [{"ats": "lever", "slug": "zeta"}])
        with mock.patch.object(sources.REGISTRY["workday"], "probe", return_value=True):
            r = self.client.post("/api/companies/detect", json={
                "name": "https://acme.wd5.myworkdayjobs.com/en-US/AcmeCareers/job/NYC/Analyst_R1", "add": True}).json()
        self.assertEqual(r["found"], [{"ats": "workday", "slug": "acme|wd5|AcmeCareers"}])
        self.assertIn("acme|wd5|AcmeCareers", db.get_setting("search")["companies"]["workday"])

    def test_state_reports_watcher_and_fresh_jobs(self):
        db.update_job("greenhouse:acme:1", first_seen="2026-01-01T00:00:00+00:00")
        db.upsert_job(make_job("lever", "acme:9", "Financial Analyst", "Acme", "u", fresh=1,
                               posted_at=db.now(), score=80))
        db.upsert_job(make_job("lever", "acme:10", "Financial Analyst", "Acme", "u", fresh=1,
                               posted_at=db.now(), score=20, location="Manila"))  # below the alert threshold
        st = self.client.get("/api/state").json()
        self.assertEqual(st["fresh"]["total_48h"], 1)
        self.assertEqual(st["fresh"]["latest"][0]["title"], "Financial Analyst")
        self.assertEqual(st["fresh"]["lag_samples"], 2)  # speed counts every new posting
        r = self.client.get("/api/jobs?sort=found&posted_hours=24").json()
        self.assertEqual(r["jobs"][0]["id"], "lever:acme:9")


class PhoneAccessTests(unittest.TestCase):
    """`--phone`: this computer is trusted; other devices need the private link once."""

    def setUp(self):
        self.tmp = TempData()
        app = create_app(start_background=False, phone_access=True)
        self.computer = TestClient(app, headers={"X-JobBot": "1"}, client=("127.0.0.1", 5000))
        self.phone = TestClient(app, headers={"X-JobBot": "1"}, client=("192.168.1.20", 5000))

    def tearDown(self):
        self.tmp.close()

    def link_key(self):
        info = self.computer.get("/api/phone").json()
        self.assertTrue(info["enabled"])
        self.assertTrue(info["qr"] is None or info["qr"].startswith("<svg"))
        return info["link"].split("?key=")[1]

    def test_phone_needs_the_link_once(self):
        self.assertEqual(self.phone.get("/").status_code, 401)
        self.assertEqual(self.phone.get("/api/state").status_code, 401)
        self.assertEqual(self.phone.get("/?key=wrong").status_code, 401)
        r = self.phone.get(f"/?key={self.link_key()}", follow_redirects=False)
        self.assertEqual((r.status_code, r.headers["location"]), (303, "/"))  # key leaves the address bar
        self.assertIn("httponly", r.headers["set-cookie"].lower())
        self.assertEqual(self.phone.get("/api/state").status_code, 200)
        self.assertEqual(self.phone.get("/api/state", headers={"Host": "laptop.tailnet.ts.net"}).status_code, 200)
        self.assertEqual(self.phone.get("/api/phone").json(), {"enabled": True, "on_phone": True})  # no key shown

    def test_writes_still_need_the_header_and_reset_is_computer_only(self):
        self.phone.get(f"/?key={self.link_key()}")
        self.assertEqual(self.phone.post("/api/rescore", headers={"X-JobBot": ""}).status_code, 403)
        self.assertEqual(self.phone.post("/api/phone/reset").status_code, 403)
        old = self.link_key()
        self.assertNotEqual(self.computer.post("/api/phone/reset").json()["link"].split("?key=")[1], old)
        self.assertEqual(self.phone.get("/api/state").status_code, 401)  # signed out

    def test_computer_keeps_the_host_check(self):
        self.assertEqual(self.computer.get("/api/state").status_code, 200)
        self.assertEqual(self.computer.get("/api/state", headers={"Host": "evil.example"}).status_code, 403)

    def test_off_by_default(self):
        app = create_app(start_background=False)
        self.assertEqual(TestClient(app, client=("127.0.0.1", 1)).get("/api/phone").json(), {"enabled": False})


if __name__ == "__main__":
    unittest.main()
