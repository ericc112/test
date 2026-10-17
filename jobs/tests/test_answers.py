import unittest
from datetime import date

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

    def test_how_heard_takes_any_choice_when_none_of_the_usual_ones_is_there(self):
        # Target's Workday list: no website, job board or "Other" choice.
        opts = ["Select One", "Events", "Personal Connection", "Radio/Newspaper", "Signage"]
        self.assertEqual(ans(q("How Did You Hear About Us?", "select", opts)).option, "Events")

    def test_phone_extension_and_address_line_2_are_left_blank(self):
        me = dict(PROFILE, address="1 Main St")
        self.assertEqual(ans(q("Phone Extension", required=False), profile=me).source, "blank")
        self.assertEqual(ans(q("Address Line 2", required=False), profile=me).source, "blank")
        self.assertEqual(ans(q("Address Line 2", required=False), profile=dict(me, address_line2="Apt 4")).value, "Apt 4")
        self.assertEqual(ans(q("Address Line 1"), profile=me).value, "1 Main St")

    def test_a_bare_upload_field_gets_the_resume(self):
        ctx = Context(profile=PROFILE, bank=DEFAULT_ANSWERS, job={}, files={"resume": "/r.pdf"})
        self.assertEqual(answer(q("Upload a file (5MB max)", "file"), ctx).value, "/r.pdf")
        self.assertEqual(answer(q("Upload a transcript", "file", required=False), ctx).source, "skip")

    def test_skills_come_from_the_profile_or_the_resume(self):
        self.assertEqual(ans(q("Type to Add Skills"), profile=dict(PROFILE, skills="SQL, Tableau")).value, "SQL")
        a = ans(q("Type to Add Skills"), profile=dict(PROFILE, skills="", resume_text="Built Excel models and SQL reports"))
        self.assertEqual([a.value] + a.alternatives, ["Excel", "SQL"])
        self.assertIsNone(ans(q("Describe your leadership skills", "textarea"), profile=dict(PROFILE, resume_text="Excel")).value)
        # The posting's skills first, and only skills the resume shows.
        ctx = Context(profile=dict(PROFILE, skills="", resume_text="Excel, SQL and Tableau dashboards"), bank=DEFAULT_ANSWERS,
                      job={"description": "You will build Tableau reports. Python a plus."})
        a = answer(q("Type to Add Skills"), ctx)
        self.assertEqual([a.value] + a.alternatives, ["Tableau", "Excel", "SQL"])

    def test_sponsorship_isnt_mistaken_for_work_authorization(self):
        me, yn = dict(PROFILE, work_authorized=True, needs_sponsorship=False), ["Select One", "Yes", "No"]
        for label in ("Will you now or in the future require employer sponsorship for work authorization (e.g., H-1B)?",
                      "Is your current work authorization through STEM OPT or will you need employer sponsorship in the future?"):
            self.assertEqual(ans(q(label, "select", yn), profile=me).option, "No", label)
        self.assertEqual(ans(q("Are you legally authorized to work in the United States?", "select", yn), profile=me).option, "Yes")
        target = ["Select One", "Yes, I am legally authorized for employment in the United States.",
                  "No, I am not legally authorized for employment in the United States."]
        self.assertEqual(ans(q("Are you legally authorized for employment in the United States?", "select", target), profile=me).option,
                         target[1])

    def test_role_type_and_education_dates(self):
        ctx = Context(profile=dict(PROFILE, expected_graduation="May 2027", graduation_year="", education_start="August 2023"), bank=DEFAULT_ANSWERS,
                      job={"title": "Inventory Analyst Intern"})
        self.assertEqual(answer(q("Which type of role are you applying for?", "select", ["Internship", "Full Time"]), ctx).option,
                         "Internship")
        self.assertEqual(answer(q("From", input_type="month", section="education"), ctx).value, "2023-08")
        self.assertEqual(answer(q("To (Actual or Expected)", input_type="month", section="education"), ctx).value, "2027-05")

    def test_phone_device_type_and_a_full_graduation_date(self):
        self.assertEqual(ans(q("Phone Device Type", "select", ["Landline", "Mobile"])).option, "Mobile")
        me = dict(PROFILE, expected_graduation="May 2027", graduation_year="")
        self.assertEqual(ans(q("Please input your anticipated graduation date", input_type="wd_date"), profile=me).value, "2027-05-01")

    def test_a_required_agreement_is_accepted(self):
        self.assertEqual(ans(q("You must AGREE to proceed.", "checkbox")).option, True)

    def test_current_job_fills_a_work_experience_block(self):
        me = dict(PROFILE, current_company="Best Cheer Stone", current_title="Supply Chain Analyst Intern",
                  current_job_start="August 2024", current_job_location="Houston, TX", current_job_description="Sourcing.")
        job = lambda label, **kw: ans(q(label, section="employment", **kw), profile=me)
        self.assertEqual(job("Job Title").value, "Supply Chain Analyst Intern")
        self.assertEqual(job("Company").value, "Best Cheer Stone")
        self.assertEqual(job("Location").value, "Houston, TX")
        self.assertEqual(job("I currently work here", kind="checkbox", required=False).option, True)
        self.assertEqual(job("From", input_type="month").value, "2024-08")
        self.assertEqual(job("Role Description", kind="textarea").value, "Sourcing.")

    def test_not_a_veteran_never_says_veteran(self):
        me = dict(PROFILE, eeo_veteran="I am not a protected veteran")
        travelers = ["I identify as one or more of the classifications of protected veteran",
                     "I am a veteran, but I am not a protected veteran", "I am not a veteran", "I don't wish to answer"]
        self.assertEqual(ans(q("Veteran Status:", "select", travelers), profile=me).option, "I am not a veteran")
        pnc = ["I am not a protected veteran", "I identify as one or more of the classifications of protected veteran"]
        self.assertEqual(ans(q("Please confirm your veteran status:", "select", pnc), profile=me).option, pnc[0])

    def test_the_exact_degree_comes_before_the_first_bachelors(self):
        me = dict(PROFILE, degree="Bachelor's", degree_type="BBA")
        self.assertEqual(ans(q("Degree", "select", ["BA", "BS", "BBA", "MBA"]), profile=me).option, "BBA")
        self.assertEqual(ans(q("Degree type", "select", ["Bachelor of Arts", "Bachelor of Business Administration"]), profile=me).option,
                         "Bachelor of Business Administration")
        self.assertEqual(ans(q("Highest level of education", "select", ["Master's Degree", "Bachelor's Degree"]), profile=me).option,
                         "Bachelor's Degree")

    def test_graduation_date_and_degree_type_come_before_degree_and_enrollment(self):
        me = dict(PROFILE, degree="Bachelor's", degree_type="BBA", expected_graduation="May 2027", graduation_year="")
        tyson = ("Expected Graduation / Graduation Date? If you are continuing education further than your current degree "
                 "program, enter your expected graduation date for that future program")
        self.assertEqual(ans(q(tyson, input_type="wd_date"), profile=me).value, "2027-05-01")
        merck = ["Bachelors", "Masters", "MBA", "Ph.D./Doctorate", "I am not currently pursing a degree"]
        self.assertEqual(ans(q("Please select the degree type you are currently pursuing", "select", merck), profile=me).option,
                         "Bachelors")

    def test_no_sponsorship_never_claims_a_temporary_visa(self):
        me = dict(PROFILE, needs_sponsorship=False)
        merck = ["Yes", "No – I hold a temporary visa status that provides work authorization through OPT or CPT",
                 "No – I am a U.S. citizen, national, permanent resident, refugee or asylee"]
        label = "Will you require our Company to provide immigration sponsorship now or in the future?"
        self.assertEqual(ans(q(label, "select", merck), profile=me).option, merck[2])
        self.assertEqual(ans(q(label, "select", ["Yes", "No"]), profile=me).option, "No")

    def test_the_disability_form(self):
        me = dict(PROFILE, eeo_disability="No, I don't have a disability")
        opts = ["Yes, I have a disability, or have had one in the past",
                "No, I do not have a disability and have not had one in the past", "I do not want to answer"]
        self.assertEqual(ans(q("Please check one of the boxes below:", "checkboxes", opts), profile=me).option, [opts[1]])
        self.assertEqual(ans(q("Date", input_type="wd_date")).value, date.today().isoformat())

    def test_school_falls_back_to_other(self):
        a = ans(q("Which university did you attend?", "select", ["MIT", "Stanford", "Other (School Not Listed)"]))
        self.assertEqual(a.option, "Other (School Not Listed)")

    def test_signature_date(self):
        self.assertRegex(ans(q("Date")).value, r"^\d{2}/\d{2}/\d{4}$")

    def test_resume_file(self):
        a = ans(q("Resume/CV", "file"), files={"resume": "/tmp/r.pdf"})
        self.assertEqual((a.value, a.source), ("/tmp/r.pdf", "file"))
        self.assertEqual(ans(q("Autofill from resume", "file", required=False)).source, "skip")


STUDENT = dict(PROFILE, gpa="3.62", expected_graduation="May 2028", graduation_year="", school_year="Junior",
               currently_enrolled=True, internship_terms="Summer 2027", minor="Economics")


class StudentTests(unittest.TestCase):
    def a(self, *args, **kw):
        r = ans(q(*args, **kw), profile=STUDENT)
        return r.option if r.option not in (None, []) else r.value

    def test_gpa(self):
        self.assertEqual(self.a("What is your cumulative GPA?"), "3.62")
        self.assertEqual(self.a("GPA", "select", ["Below 3.0", "3.0 - 3.49", "3.5 - 4.0"]), "3.5 - 4.0")
        self.assertEqual(self.a("GPA", "select", ["3.75+", "3.5-3.74", "Under 3.5"]), "3.5-3.74")

    def test_graduation_in_any_format(self):
        self.assertEqual(self.a("Expected graduation date", input_type="date"), "2028-05-01")
        self.assertEqual(self.a("Expected Graduation Date"), "May 2028")
        self.assertEqual(self.a("Graduation Year"), "2028")
        self.assertEqual(self.a("Anticipated graduation", "select", ["Spring 2028", "Fall 2028"]), "Spring 2028")
        self.assertEqual(self.a("Class year", "select", ["Class of 2027", "Class of 2028"]), "Class of 2028")
        self.assertEqual(self.a("Graduation year", "select", ["2027", "2028", "2029"]), "2028")

    def test_enrollment_year_and_term(self):
        yn = ["Yes", "No"]
        self.assertEqual(self.a("What is your current year in school?", "select", ["Freshman", "Sophomore", "Junior", "Senior"]), "Junior")
        self.assertEqual(self.a("Current academic standing", "select", ["1st year", "2nd year", "3rd year", "4th year"]), "3rd year")
        self.assertEqual(self.a("Are you currently enrolled in a degree program?", "radio", yn), "Yes")
        self.assertEqual(self.a("Will you be returning to school after the internship?", "radio", yn), "Yes")
        self.assertEqual(self.a("Which internship term are you applying for?", "select", ["Spring 2027", "Summer 2027"]), "Summer 2027")
        self.assertEqual(self.a("Are you available for the Summer 2027 internship?", "radio", yn), "Yes")
        self.assertEqual(self.a("Are you available for the Fall 2027 internship?", "radio", yn), "No")
        self.assertEqual(self.a("Minor"), "Economics")
        self.assertEqual(self.a("Are you available to work full-time (40 hours/week) during the internship?", "radio", yn), "Yes")

    def test_questions_from_a_live_internship_form(self):
        yn = ["Yes", "No"]
        self.assertEqual(self.a("Have you ever, or are you currently working at Gusto in any capacity?", "select", yn), "No")
        self.assertEqual(self.a("I identify as a first-generation professional (please select one):", "select",
                                ["Yes", "No", "I don't wish to answer"]), "I don't wish to answer")
        self.assertIsNone(ans(q("Are you a first-generation college student? Tell us more."), profile=STUDENT).value)

    def test_employment_and_education_blocks(self):
        months = [m.capitalize() for m in ("january", "february", "march", "april", "may", "june")]
        job = lambda label, kind="text", **kw: ans(q(label, kind, section="employment", **kw), profile=STUDENT)
        edu = lambda label, kind="text", **kw: ans(q(label, kind, section="education", **kw), profile=STUDENT)
        # A past job's dates are never "Two weeks after an offer" or your graduation date.
        self.assertIsNone(job("Start date month", "combobox").value)
        self.assertIsNone(job("Start date year").value)
        self.assertIsNone(job("End date year").value)
        self.assertIsNone(ans(q("Start date year"), profile=STUDENT).value)  # no block info: still not availability
        self.assertEqual(job("Company name").value, "Example Corp")
        self.assertEqual(job("Title").value, "Software Engineer")
        # The end of your degree is your graduation.
        self.assertEqual(edu("End date year").value, "2028")
        self.assertEqual(edu("End date month", "select", options=months).option, "May")
        self.assertIsNone(edu("Start date year").value)

    def test_how_heard_names_the_company_site_for_employer_postings(self):
        opts = ["LinkedIn", "Glassdoor", "Indeed", "Gusto Blog", "Gusto Employee", "Gusto Website"]
        question = q("How did you hear about this opportunity?", "checkboxes", opts)
        ctx = dict(profile=STUDENT, bank=DEFAULT_ANSWERS)
        on_site = Context(job={"source": "greenhouse", "company": "Gusto, Inc.", "title": "Finance Intern"}, **ctx)
        self.assertEqual(answer(question, on_site).option, ["Gusto Website"])
        via_board = Context(job={"source": "himalayas", "company": "Gusto, Inc.", "title": "Finance Intern"}, **ctx)
        self.assertFalse(answer(question, via_board).resolved(question))  # found on a job board: don't claim the company site


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
