import unittest

from jobbot.answers import Answer, Context, Question, answer, answer_all, missing
from jobbot.config import DEFAULT_ANSWERS
from jobbot.textutil import norm

from .helpers import PROFILE


def q(label, kind="text", options=None, required=True, **kw):
    return Question(key="q", kind=kind, label=label, required=required, options=options or [], **kw)


def ans(question, **ctx_kw):
    ctx = Context(profile=ctx_kw.pop("profile", PROFILE), bank=ctx_kw.pop("bank", DEFAULT_ANSWERS),
                  job={"title": "Engineer", "company": "Acme"}, **ctx_kw)
    return answer(question, ctx)


class RuleTests(unittest.TestCase):
    def test_identity_fields(self):
        self.assertEqual(ans(q("First Name")).value, "Test")
        self.assertEqual(ans(q("Last Name")).value, "Applicant")
        self.assertEqual(ans(q("Full name")).value, "Test Applicant")
        self.assertEqual(ans(q("Legal Name")).value, "Test Applicant")
        self.assertEqual(ans(q("Preferred Name | What would you like us to call you?")).value, "Test")
        self.assertEqual(ans(q("Email")).value, "test@example.com")
        self.assertEqual(ans(q("Phone")).value, "415-555-0134")
        self.assertEqual(ans(q("LinkedIn Profile")).value, "https://www.linkedin.com/in/test")

    def test_name_rule_ignores_other_names(self):
        self.assertNotEqual(ans(q("Company name")).value, "Test Applicant")
        self.assertNotEqual(ans(q("Name of your hiring manager reference")).value, "Test Applicant")

    def test_employer_and_title(self):
        self.assertEqual(ans(q("Who is your current or previous employer?")).value, "Example Corp")
        self.assertEqual(ans(q("What is your current or previous job title?")).value, "Software Engineer")

    def test_work_authorisation_and_sponsorship(self):
        yn = ["Yes", "No"]
        self.assertEqual(ans(q("Are you legally authorized to work in the United States?", "radio", yn)).option, "Yes")
        self.assertEqual(ans(q("Will you now or in the future require sponsorship for a visa?", "radio", yn)).option, "No")
        self.assertEqual(ans(q("Do you currently hold a valid work permit?", "radio", yn)).option, "Yes")

    def test_location_answers(self):
        a = ans(q("Location (City)", "combobox"))
        self.assertEqual(a.value, "San Francisco, California")
        self.assertEqual(a.search, "San Francisco")
        self.assertEqual(ans(q("Please select the country where you currently reside.", "select", ["Canada", "US"])).option, "US")
        self.assertEqual(ans(q("Where do you plan on working from (for payroll tax purposes)?", "combobox")).search, "San Francisco")

    def test_eeo_defaults_to_decline(self):
        a = ans(q("Gender", "select", ["Male", "Female", "Decline To Self Identify"], required=False))
        self.assertEqual(a.option, "Decline To Self Identify")
        a = ans(q("Veteran Status", "select", ["I am a veteran", "I don't wish to answer"], required=False))
        self.assertEqual(a.option, "I don't wish to answer")

    def test_answer_bank_and_overrides(self):
        a = ans(q("Have you ever been employed by Stripe?", "select", ["Yes", "No"]))
        self.assertEqual((a.option, a.source), ("No", "bank"))
        a = ans(q("Have you ever been employed by Stripe?", "select", ["Yes", "No"]),
                overrides={norm("Have you ever been employed by Stripe?"): "Yes"})
        self.assertEqual((a.option, a.source), ("Yes", "user"))

    def test_marketing_opt_in_is_no(self):
        a = ans(q("Do you opt-in to receive WhatsApp messages from Stripe Recruiting?", "select", ["Yes", "No"]))
        self.assertEqual(a.option, "No")

    def test_required_consent_is_acknowledged_optional_is_left(self):
        opts = ["I acknowledge that I have read and understood the Privacy Policy."]
        self.assertEqual(ans(q("Candidate Privacy Policy", "select", opts)).option, opts[0])
        self.assertEqual(ans(q("I agree to the privacy policy", "checkbox")).option, True)
        self.assertEqual(ans(q("I consent to the privacy notice", "checkbox", required=False)).source, "skip")

    def test_years_of_experience(self):
        yn = ["Yes", "No"]
        self.assertEqual(ans(q("Do you have a minimum of 7 years of experience building software?", "buttons", yn)).option, "Yes")
        self.assertEqual(ans(q("Do you have at least 10 years of professional experience?", "buttons", yn)).option, "No")
        self.assertIsNone(ans(q("Do you have a minimum of 5 years of experience with Terraform?", "buttons", yn)).option)
        self.assertEqual(ans(q("How many years of experience do you have?")).value, "8")

    def test_how_heard_falls_back_through_options(self):
        a = ans(q("Please tell us how you heard about this opportunity.", "select", ["LinkedIn", "Job Board (Indeed, Monster, etc.)", "Other"]))
        self.assertEqual(a.option, "Job Board (Indeed, Monster, etc.)")

    def test_school_falls_back_to_other(self):
        a = ans(q("Which university did you attend?", "select", ["MIT", "Stanford", "Other (School Not Listed)"]))
        self.assertEqual(a.option, "Other (School Not Listed)")

    def test_signature_date(self):
        self.assertRegex(ans(q("Date")).value, r"^\d{2}/\d{2}/\d{4}$")

    def test_resume_file(self):
        a = ans(q("Resume/CV", "file"), files={"resume": "/tmp/r.pdf"})
        self.assertEqual((a.value, a.source), ("/tmp/r.pdf", "file"))
        self.assertEqual(ans(q("Autofill from resume", "file", required=False)).source, "skip")


class SafetyTests(unittest.TestCase):
    def test_anti_bot_questions_are_left_to_you(self):
        for label in ["To prove you're not a bot auto-applying, what is 3+4?",
                      "Here's some text encoded in a common format. Figure out the correct secret.",
                      "Enter the security code we emailed you"]:
            self.assertEqual(ans(q(label)).source, "human", label)

    def test_your_own_answer_wins_over_human_only(self):
        a = ans(q("To prove you're not a bot auto-applying, what is 3+4?"), overrides={norm("To prove you're not a bot auto-applying, what is 3+4?"): "7"})
        self.assertEqual((a.value, a.source), ("7", "user"))

    def test_ai_policy_attestation_needs_you(self):
        a = ans(q("Candidate AI Usage Attestation:", "select", ["I agree"]))
        self.assertEqual(a.source, "human")
        bank = DEFAULT_ANSWERS + [{"q": "Candidate AI Usage Attestation", "a": "I agree"}]
        self.assertEqual(ans(q("Candidate AI Usage Attestation:", "select", ["I agree"]), bank=bank).option, "I agree")

    def test_unknown_required_question_is_missing_not_guessed(self):
        question = q("Describe a time you scaled a database.", "textarea")
        ctx = Context(profile=PROFILE, bank=DEFAULT_ANSWERS)
        answers = answer_all([question], ctx)
        self.assertIsNone(answers["q"].value)
        self.assertEqual(missing([question], answers), [question])


class FakeLLM:
    answer_optional = False
    write_cover_letters = False

    def __init__(self):
        self.asked = []

    def answer_questions(self, questions, ctx):
        self.asked += [x.label for x in questions]
        return {x.key: ("I scaled Postgres to 10TB.", "test") for x in questions}


class LLMFallbackTests(unittest.TestCase):
    def test_llm_only_gets_unanswered_required_questions(self):
        qs = [Question("a", "text", "First Name", True), Question("b", "textarea", "Describe a time you scaled a database.", True),
              Question("c", "textarea", "Anything else?", False), Question("d", "text", "Prove you are not a bot", True)]
        llm = FakeLLM()
        out = answer_all(qs, Context(profile=PROFILE, bank=DEFAULT_ANSWERS, llm=llm))
        self.assertEqual(llm.asked, ["Describe a time you scaled a database."])
        self.assertEqual(out["b"].source, "ai")
        self.assertEqual(out["a"].source, "profile")
        self.assertEqual(out["d"].source, "human")


if __name__ == "__main__":
    unittest.main()
