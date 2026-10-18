"""Drive the real browser against local fixture forms. Nothing touches the network."""
import os
import unittest
from unittest import mock

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

    def test_emailed_code_at_the_bottom_of_a_long_form_is_blocked(self):
        res = self.run_form("email_code.html", mode="submit")
        self.assertEqual(res.result, "blocked", res.message)
        self.assertIn("email security code", res.message)

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


@unittest.skipUnless(HAS_BROWSER, "Chromium for Playwright isn't installed (python -m playwright install chromium)")
class WorkdayFlowTests(unittest.TestCase):
    """The Workday flow against a local stand-in for a Workday careers site."""

    def setUp(self):
        self.tmp = TempData()

    def tearDown(self):
        self.tmp.close()

    def run_wd(self, mode="prepare", query="", overrides=None, password="Str0ng!Pass"):
        from jobbot.apply.workday import WorkdayEngine
        job = {"id": "test:wd", "title": "Finance Intern", "company": "Acme", "source": "workday",
               "url": (FIXTURES / "workday_like.html").as_uri() + query}
        ctx = Context(profile=dict(PROFILE, workday_password=password, state="New York"), bank=DEFAULT_ANSWERS, job=job,
                      overrides={norm(k): v for k, v in (overrides or {}).items()}, files={"resume": str(FIXTURES / "resume.txt")})
        # The machine's own Workday password (if one is set) must not stand in for the test's.
        env = {k: v for k, v in os.environ.items() if k != "JOBBOT_WORKDAY_PASSWORD"}
        with mock.patch.dict(os.environ, env, clear=True):
            return WorkdayEngine(headless=True).run(job, ctx, mode)

    def answer(self, res, label_part):
        return next(f["answer"] for f in res.fields if label_part.lower() in f["label"].lower())

    def test_creates_the_account_fills_every_step_and_stops_at_review(self):
        res = self.run_wd(overrides={"Which Acme office would you prefer?": "New York"})
        self.assertEqual(res.result, "ready", res.message)
        self.assertIn("nothing has been sent", res.message)
        self.assertEqual(self.answer(res, "hear about"), "Company Website")  # found on the employer's own site
        self.assertEqual(self.answer(res, "state"), "New York")
        self.assertEqual(self.answer(res, "sponsorship"), "No")
        self.assertEqual(self.answer(res, "gender"), "I do not wish to answer")
        # The stand-in rejects sign-ups whose hidden "beecatcher" bot trap was filled, so getting here proves it wasn't.

    def test_a_question_only_you_can_answer_comes_back_with_its_options(self):
        res = self.run_wd()
        self.assertEqual(res.result, "needs_input")
        self.assertEqual(res.missing[0]["label"], "Which Acme office would you prefer?")
        self.assertEqual(res.missing[0]["options"], ["Minneapolis", "New York"])
        self.assertIn("saved in your draft", res.message)

    def test_submit_signs_in_and_is_confirmed(self):
        res = self.run_wd("submit", "?account=1", overrides={"Which Acme office would you prefer?": "New York"})
        self.assertEqual(res.result, "applied", res.message)

    def test_needs_a_strong_password(self):
        self.assertIn("password", self.run_wd(password="").message.lower())
        self.assertIn("8+ characters", self.run_wd(password="short").message)
