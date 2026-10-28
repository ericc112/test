import unittest

from jobbot import resume
from jobbot.answers import Context, Question, answer_all
from jobbot.config import DEFAULT_ANSWERS

from .helpers import PROFILE

# How pypdf reads a two-column resume PDF: one word per line.
WORDY = "\n\n".join("""Jordan Sample Houston, TX EDUCATION State University Bachelor of Business Administration MAY 2027
EXPERIENCE Northwind Traders | Supply Chain Analyst Intern | Houston, TX August 2024 - Present
● Negotiated prices with 8+ vendors, improving on-time delivery by 22% ● Kept SAP inventory data accurate across 3 locations
Contoso | Operations Intern | Las Vegas, NV May 2026 – August 2026 ● Led a dashboard for 90+ associates using Power BI
● Cut trailer dwell time by 27% Fabrikam Freight | Logistics Manager | Logan, WV August 2019 – August 2023
● Built an Excel inventory tracker, cutting manual work by 10 hours a week LEADERSHIP & ACTIVITIES
Business Student Association | Mentor | Houston, TX May 2026 – Present ● Ran workshops for 20 members every semester""".split())

LINES = """Jordan Sample
WORK EXPERIENCE
Supply Chain Analyst Intern, Northwind Traders, Houston, TX
Aug 2024 – Present
• Negotiated prices with 8+ vendors, improving on-time delivery by 22%
Contoso — Operations Intern
05/2026 - 08/2026
• Led a dashboard for 90+ associates using Power BI
EDUCATION
State University, Bachelor of Business Administration
Aug 2023 – May 2027"""


class ResumeTests(unittest.TestCase):
    def test_a_word_per_line_pdf(self):
        jobs = resume.ordered(WORDY)
        self.assertEqual([(j["company"], j["title"], j["kind"]) for j in jobs], [
            ("Northwind Traders", "Supply Chain Analyst Intern", "work"), ("Contoso", "Operations Intern", "work"),
            ("Fabrikam Freight", "Logistics Manager", "work"), ("Business Student Association", "Mentor", "activity")])
        self.assertEqual((jobs[0]["start"], jobs[0]["current"]), ((2024, 8), True))
        self.assertEqual((jobs[1]["start"], jobs[1]["end"], jobs[1]["location"]), ((2026, 5), (2026, 8), "Las Vegas, NV"))
        self.assertEqual(jobs[1]["description"], "Led a dashboard for 90+ associates using Power BI\nCut trailer dwell time by 27%")
        self.assertNotIn("LEADERSHIP", jobs[2]["description"])

    def test_a_resume_with_lines_and_other_layouts(self):
        jobs = resume.ordered(LINES)
        self.assertEqual([(j["company"], j["title"], j["start"], j["end"]) for j in jobs], [
            ("Northwind Traders", "Supply Chain Analyst Intern", (2024, 8), None), ("Contoso", "Operations Intern", (2026, 5), (2026, 8))])


class WorkExperienceBlockTests(unittest.TestCase):
    """Workday's "My Experience": every block gets its own job from the resume, never the current job's details."""

    def fill(self, shown):
        qs = []
        for block, company, title in shown:
            for label, kind, it, value in [("Job Title", "text", "", title), ("Company", "text", "", company),
                                           ("I currently work here", "checkbox", "", False), ("From", "text", "month", None),
                                           ("To", "text", "month", None), ("Role Description", "textarea", "", None)]:
                qs.append(Question(f"{block}:{label}", kind, label, label in ("From", "To"), input_type=it, value=value,
                                   section="employment", block=block))
        ctx = Context(profile=dict(PROFILE, resume_text=WORDY, current_company="Northwind Traders", current_job_start="August 2024"),
                      bank=DEFAULT_ANSWERS)
        got = answer_all(qs, ctx)
        out = {}
        for q in qs:
            a = got[q.key]
            out[(q.block, q.label)] = a.option if a.option not in (None, []) else a.value
        return out

    def test_each_block_is_its_own_job(self):
        out = self.fill([("Work Experience 1", "Northwind Traders", None), ("Work Experience 2", "Contoso, Inc.", None),
                         ("Work Experience 3", None, "Logistics Manager"), ("Work Experience 4", None, None)])
        self.assertEqual(out[("Work Experience 1", "From")], "2024-08")
        self.assertIsNone(out[("Work Experience 1", "To")])  # current: no end date
        self.assertEqual(out[("Work Experience 1", "I currently work here")], True)
        self.assertEqual(out[("Work Experience 2", "Company")], "Contoso, Inc.")  # the form's own wording stays
        self.assertEqual((out[("Work Experience 2", "From")], out[("Work Experience 2", "To")]), ("2026-05", "2026-08"))
        self.assertEqual(out[("Work Experience 2", "Job Title")], "Operations Intern")
        self.assertEqual((out[("Work Experience 3", "Company")], out[("Work Experience 3", "To")]), ("Fabrikam Freight", "2023-08"))
        self.assertEqual(out[("Work Experience 4", "Company")], "Business Student Association")
        self.assertTrue(out[("Work Experience 2", "Role Description")].startswith("Led a dashboard"))

    def test_a_job_the_resume_lacks_is_left_alone(self):
        out = self.fill([("Work Experience 1", "Northwind Traders", None), ("Work Experience 2", "Tailspin Toys", None)])
        self.assertIsNone(out[("Work Experience 2", "From")])
        self.assertIsNone(out[("Work Experience 2", "Job Title")])  # not the current job's title either


if __name__ == "__main__":
    unittest.main()
