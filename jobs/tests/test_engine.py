"""Drive the real browser against local fixture forms. Nothing touches the network."""
import unittest

from jobbot.answers import Context
from jobbot.apply.engine import Engine
from jobbot.config import DEFAULT_ANSWERS
from jobbot.textutil import norm

from .helpers import FIXTURES, PROFILE, TempData, browser_available

HAS_BROWSER = browser_available()


@unittest.skipUnless(HAS_BROWSER, "Chromium for Playwright isn't installed (python -m playwright install chromium)")
class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        self.engine = Engine(headless=True)

    def tearDown(self):
        self.tmp.close()

    def run_form(self, fixture, mode="prepare", overrides=None, resume=True):
        job = {"id": f"test:{fixture}", "title": "Backend Engineer", "company": "Acme",
               "apply_url": (FIXTURES / fixture).as_uri()}
        ctx = Context(profile=PROFILE, bank=DEFAULT_ANSWERS, job=job, overrides=overrides or {},
                      files={"resume": str(FIXTURES / "resume.txt")} if resume else {})
        return self.engine.run(job, ctx, mode)

    def field(self, res, label_part):
        return next(f for f in res.fields if label_part.lower() in f["label"].lower())

    def test_greenhouse_like_prepare_fills_everything_without_submitting(self):
        res = self.run_form("greenhouse_like.html")
        self.assertEqual(res.result, "ready", res.missing)
        self.assertEqual(self.field(res, "first name")["answer"], "Test")
        self.assertEqual(self.field(res, "authorized")["answer"], "Yes")
        self.assertEqual(self.field(res, "sponsorship")["answer"], "No")
        self.assertEqual(self.field(res, "countries")["answer"], ["US"])
        self.assertEqual(self.field(res, "resume")["source"], "file")
        self.assertIn("attached when you submit", self.field(res, "resume")["note"])
        self.assertEqual(self.field(res, "gender")["answer"], "Decline To Self Identify")
        self.assertTrue((self.tmp.dir / "screenshots" / res.screenshot).exists())

    def test_greenhouse_like_submit_is_confirmed(self):
        res = self.run_form("greenhouse_like.html", mode="submit")
        self.assertEqual(res.result, "applied", res.message)

    def test_missing_resume_blocks_submit(self):
        res = self.run_form("greenhouse_like.html", mode="submit", resume=False)
        self.assertEqual(res.result, "needs_input")
        self.assertEqual([m["label"] for m in res.missing], ["Resume/CV"])

    def test_lever_like_cards_location_autocomplete_and_submit(self):
        res = self.run_form("lever_like.html", mode="submit")
        self.assertEqual(res.result, "applied", f"{res.message} {res.missing}")
        self.assertEqual(self.field(res, "current location")["answer"], "San Francisco, CA, USA")
        self.assertEqual(self.field(res, "heard about")["answer"], "Job Board (Indeed, Monster, etc.)")
        self.assertEqual(self.field(res, "veteran")["label"], "Veteran status")

    def test_ashby_like_human_question_then_your_answer(self):
        res = self.run_form("ashby_like.html")
        self.assertEqual(res.result, "needs_input")
        self.assertEqual(self.field(res, "minimum of 5 years")["answer"], "Yes")
        self.assertEqual(self.field(res, "not a bot")["source"], "human")
        label = self.field(res, "not a bot")["label"]
        res = self.run_form("ashby_like.html", mode="submit", overrides={norm(label): "7"})
        self.assertEqual(res.result, "applied", res.message)

    def test_captcha_after_submit_is_blocked(self):
        res = self.run_form("captcha.html", mode="submit")
        self.assertEqual(res.result, "blocked")
        self.assertIn("CAPTCHA", res.message)

    def test_validation_errors_are_reported(self):
        res = self.run_form("errors.html", mode="submit")
        self.assertEqual(res.result, "needs_input")
        self.assertIn("couldn't verify your email", res.message)

    def test_bot_wall_hands_job_to_you(self):
        res = self.run_form("botwall.html")
        self.assertEqual(res.result, "manual")

    def test_apply_link_in_new_tab_is_followed(self):
        res = self.run_form("jobpage.html")
        self.assertEqual(res.result, "ready", res.missing)
        self.assertTrue(res.url.endswith("lever_like.html"))


if __name__ == "__main__":
    unittest.main()
