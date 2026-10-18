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


def without_account_env(test):
    """Use the test's own email and password, not the JOBBOT_WORKDAY_* account set in this environment."""
    env = mock.patch.dict(os.environ)
    env.start()
    test.addCleanup(env.stop)
    for key in ("JOBBOT_WORKDAY_EMAIL", "JOBBOT_WORKDAY_PASSWORD"):
        os.environ.pop(key, None)


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

    def test_a_job_pages_search_boxes_are_not_the_form(self):
        res = self.run_form("search_job.html")
        self.assertEqual(res.result, "ready", res.missing)
        self.assertTrue(res.url.endswith("greenhouse_like.html"))

    def test_a_notice_shown_after_apply_is_accepted(self):
        res = self.run_form("consent_job.html")
        self.assertEqual(res.result, "ready", res.missing)
        self.assertTrue(res.url.endswith("greenhouse_like.html"))

    def test_apply_link_in_new_tab_is_followed(self):
        res = self.run_form("jobpage.html")
        self.assertEqual(res.result, "ready", res.missing)
        self.assertTrue(res.url.endswith("lever_like.html"))


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HAS_BROWSER, "Chromium for Playwright isn't installed (python -m playwright install chromium)")
class TaleoFlowTests(unittest.TestCase):
    """The Taleo Business Edition flow against a local stand-in: register, fill each step, submit."""

    def setUp(self):
        self.tmp = TempData()
        without_account_env(self)

    def tearDown(self):
        self.tmp.close()

    def run_taleo(self, mode, password="Str0ng!Passw0rd", query=""):
        from jobbot.apply.taleo import TaleoEngine
        job = {"id": "test:taleo", "title": "Procurement Intern", "company": "Acme", "source": "other",
               "url": (FIXTURES / "taleo_like.html").as_uri() + query}
        ctx = Context(profile=dict(PROFILE, workday_password=password, work_authorized=True), bank=DEFAULT_ANSWERS, job=job,
                      files={"resume": str(FIXTURES / "resume.txt")})
        return TaleoEngine(headless=True).run(job, ctx, mode)

    def test_registers_fills_each_step_and_submits(self):
        res = self.run_taleo("submit")
        self.assertEqual(res.result, "applied", res.message)

    def test_the_voluntary_page_after_submit_is_answered_and_sent(self):
        res = self.run_taleo("submit", query="?eeo=1")
        self.assertEqual(res.result, "applied", res.message)
        self.assertIn("Gender", [f["label"] for f in res.fields])

    def test_prepare_stops_before_submit(self):
        res = self.run_taleo("prepare")
        self.assertEqual(res.result, "ready", res.message)
        self.assertIn("nothing has been sent", res.message)

    def test_a_password_the_site_rejects_is_reported(self):
        res = self.run_taleo("submit", password="Sh0rt!pass1")  # 11 characters: the site wants 12
        self.assertEqual(res.result, "needs_input", res.message)
        self.assertIn("twelve (12) characters", res.message)


class WorkdaySkillTests(unittest.TestCase):
    def test_the_exact_skill_wins_over_look_alikes(self):
        from jobbot.apply.workday import WorkdayEngine
        pick = WorkdayEngine._best_skill
        self.assertEqual(pick("Excel", ["Excel-DNA", "Microsoft Excel", "Excel Macros"]), "Microsoft Excel")
        self.assertEqual(pick("SQL", ["MySQL", "SQL Server", "SQL"]), "SQL")
        self.assertIsNone(pick("Supply Chain Management", ["Lean Supply Chain Management"]))
        self.assertIsNone(pick("Operations", ["DP Operations", "Operations Research"]))


@unittest.skipUnless(HAS_BROWSER, "Chromium for Playwright isn't installed (python -m playwright install chromium)")
class WorkdayFlowTests(unittest.TestCase):
    """The Workday flow against a local stand-in for a Workday careers site."""

    def setUp(self):
        self.tmp = TempData()
        without_account_env(self)

    def tearDown(self):
        self.tmp.close()

    def run_wd(self, mode="prepare", query="", overrides=None, password="Str0ng!Pass"):
        from jobbot.apply.workday import WorkdayEngine
        job = {"id": "test:wd", "title": "Finance Intern", "company": "Acme", "source": "workday",
               "url": (FIXTURES / "workday_like.html").as_uri() + query}
        ctx = Context(profile=dict(PROFILE, workday_password=password, state="New York"), bank=DEFAULT_ANSWERS, job=job,
                      overrides={norm(k): v for k, v in (overrides or {}).items()}, files={"resume": str(FIXTURES / "resume.txt")})
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

    def test_waits_for_a_slow_site(self):
        # Apply pressed before the page is ready, and a progress bar that comes before the sign-in form.
        # Also a draft from an earlier run with a phone number left in Phone Extension, which has to be cleared.
        res = self.run_wd(query="?slow=1&ext=4155550134", overrides={"Which Acme office would you prefer?": "New York"})
        self.assertEqual(res.result, "ready", res.message)

    def test_an_application_with_an_assessment_is_skipped(self):
        res = self.run_wd("submit", "?account=1&assess=1")
        self.assertEqual(res.result, "manual", res.message)
        self.assertIn("assessment", res.message)

    def test_submit_signs_in_and_is_confirmed(self):
        res = self.run_wd("submit", "?account=1", overrides={"Which Acme office would you prefer?": "New York"})
        self.assertEqual(res.result, "applied", res.message)

    def test_needs_a_strong_password(self):
        self.assertIn("password", self.run_wd(password="").message.lower())
        self.assertIn("8+ characters", self.run_wd(password="short").message)


@unittest.skipUnless(HAS_BROWSER, "Chromium for Playwright isn't installed (python -m playwright install chromium)")
class AnySiteTests(unittest.TestCase):
    """Careers sites JobBot has no code of its own for: sign in or create the account, go through each page, submit."""

    def setUp(self):
        self.tmp = TempData()
        without_account_env(self)

    def tearDown(self):
        self.tmp.close()

    def run_site(self, fixture, mode="prepare", query="", password="Str0ng!Pass1"):
        job = {"id": "test:any", "title": "Procurement Intern", "company": "Acme",
               "url": (FIXTURES / fixture).as_uri() + query}
        me = dict(PROFILE, workday_password=password, work_authorized=True, needs_sponsorship=False, state="Texas", city="Austin")
        ctx = Context(profile=me, bank=DEFAULT_ANSWERS, job=job, files={"resume": str(FIXTURES / "resume.txt")})
        return Engine(headless=True).run(job, ctx, mode)

    def test_creates_the_account_goes_through_each_page_and_submits(self):
        res = self.run_site("account_site.html", "submit")
        self.assertEqual(res.result, "applied", res.message)

    def test_prepare_stops_at_submit(self):
        res = self.run_site("account_site.html")
        self.assertEqual(res.result, "ready", res.message)
        self.assertIn("3 pages", res.message)
        self.assertEqual(next(f["answer"] for f in res.fields if "sponsorship" in f["label"]), "No")

    def test_signs_in_to_an_existing_account(self):
        res = self.run_site("account_site.html", "submit", "?account=1")
        self.assertEqual(res.result, "applied", res.message)

    def test_an_account_with_another_password_is_handed_to_you(self):
        res = self.run_site("account_site.html", "submit", "?wrong=1")
        self.assertEqual(res.result, "needs_input", res.message)
        self.assertIn("Forgot password", res.message)

    def test_a_password_the_sign_up_rejects_is_reported(self):
        res = self.run_site("account_site.html", "submit", password="weakpassword")
        self.assertEqual(res.result, "needs_input", res.message)
        self.assertIn("Couldn't create your account", res.message)
        self.assertIn("8+ characters", res.message)

    def test_stops_when_the_site_asks_you_to_confirm_your_email(self):
        res = self.run_site("account_site.html", "submit", "?verify=1")
        self.assertEqual(res.result, "blocked", res.message)
        self.assertIn("Confirm it", res.message)

    def test_applies_as_a_guest_when_offered(self):
        res = self.run_site("account_site.html", "submit", "?guest=1")
        self.assertEqual(res.result, "applied", res.message)

    def test_a_job_alert_box_is_not_a_sign_in(self):
        res = self.run_site("account_site.html", "submit", "?alerts=1&account=1")
        self.assertEqual(res.result, "applied", res.message)

    def test_without_a_password_you_apply_there(self):
        res = self.run_site("account_site.html", password="")
        self.assertEqual(res.result, "manual", res.message)
        self.assertIn("JOBBOT_WORKDAY_PASSWORD", res.message)

    def test_a_form_inside_a_frame(self):
        res = self.run_site("embedded_form.html", "submit")
        self.assertEqual(res.result, "applied", res.message)
