import unittest

from jobbot import fields

ALL = {"field": "business"}

BUSINESS = {
    "Financial Analyst": "Finance & Accounting",
    "Staff Accountant": "Finance & Accounting",
    "Investment Banking Summer Analyst": "Finance & Accounting",
    "Account Executive, Mid-Market": "Sales & Business Development",
    "Business Development Representative": "Sales & Business Development",
    "Medical Sales Representative": "Sales & Business Development",
    "Customer Success Manager": "Sales & Business Development",
    "Marketing Operations Manager": "Marketing & Communications",
    "Product Marketing Manager": "Marketing & Communications",
    "Social Media Coordinator": "Marketing & Communications",
    "Talent Acquisition Partner": "HR & People",
    "HR Generalist": "HR & People",
    "Management Consultant": "Consulting & Strategy",
    "Chief of Staff": "Consulting & Strategy",
    "Supply Chain Analyst": "Operations & Supply Chain",
    "Retail Buyer": "Operations & Supply Chain",
    "Product Manager": "Project & Product Management",
    "Management Trainee": "Project & Product Management",
    "Data Analyst": "Business Analytics",
    "Business Manager": "Project & Product Management",
    "Personal Banker - Universal Branch": "Finance & Accounting",
}
NOT_BUSINESS = [
    "Senior Software Engineer", "Sales Engineer", "Solutions Architect", "Data Scientist", "Analytics Engineer",
    "Technical Program Manager", "UX Designer", "Registered Nurse", "Barista - Temporary", "Store Manager",
    "Shift Lead", "Solar Appointment Setter", "Legal Counsel", "Clinical Research Associate", "Security Analyst",
    "IT Support Specialist", "TIG Welder (Starship Components)", "Warehouse Associate", "Customer Service Representative",
    "Data Partner - Finance - Remote", "Personalized Internet Ads Assessor", "Project Manager - Construction",
    "Customer Technology Advisor for Mainframe", "Retail Sales - Stylist - Women's Core", "Beauty Advisor",
    "Retail Sales Associate",
]


class ClassifierTests(unittest.TestCase):
    def test_business_roles(self):
        for title, area in BUSINESS.items():
            self.assertEqual(fields.classify({"title": title}, ALL), (True, area), title)

    def test_other_roles(self):
        for title in NOT_BUSINESS:
            self.assertFalse(fields.classify({"title": title}, ALL)[0], title)

    def test_department_decides_vague_titles(self):
        self.assertEqual(fields.classify({"title": "Associate", "categories": ["Strategic Finance"]}, ALL),
                         (True, "Finance & Accounting"))
        self.assertFalse(fields.classify({"title": "Associate", "categories": ["Engineering"]}, ALL)[0])
        self.assertFalse(fields.classify({"title": "Program Manager", "categories": ["Engineering"]}, ALL)[0])
        self.assertTrue(fields.classify({"title": "Program Manager", "categories": ["Marketing"]}, ALL)[0])

    def test_areas_can_be_narrowed(self):
        only_finance = {"field": "business", "families": ["finance"]}
        self.assertTrue(fields.classify({"title": "Financial Analyst"}, only_finance)[0])
        ok, why = fields.classify({"title": "Brand Manager"}, only_finance)
        self.assertFalse(ok)
        self.assertIn("isn't one of your areas", why)

    def test_job_types(self):
        cases = {"Summer 2027 Finance Intern": "internship", "Investment Banking Summer Analyst": "internship",
                 "Co-op, Supply Chain": "internship", "Internal Audit Associate": "full_time",
                 "International Sales Manager": "full_time", "Part-Time Universal Banker": "part_time",
                 "Seasonal Sales Associate": "temporary", "Financial Analyst": "full_time"}
        for title, kind in cases.items():
            self.assertEqual(fields.job_type({"title": title}), kind, title)
        # Workday/Lever/Ashby employment-type labels count too
        self.assertEqual(fields.job_type({"title": "Corporate Banking Program", "tags": ["Intern (Seasonal) (Trainee)"]}), "internship")
        self.assertEqual(fields.job_type({"title": "Marketing Associate", "tags": ["Intern"]}), "internship")
        # A board's keyword categories don't override a Full Time employment type (Himalayas "Analyst-Intern")
        self.assertEqual(fields.job_type({"title": "Analyst I", "tags": ["Full Time", "Entry-level"],
                                          "categories": ["Finance", "Analyst-Intern", "Junior-Analyst"]}), "full_time")
        self.assertEqual(fields.job_type({"title": "Finance Program", "categories": ["University Internships"]}), "internship")

    def test_mba_internships_skip_undergrads(self):
        undergrad = {"school_year": "Junior", "degree": "Bachelor's"}
        grad = {"school_year": "Graduate student", "degree": "MBA"}
        mba = {"title": "Strategic Finance Intern (MBA)"}
        ug = {"title": "Undergraduate Summer Analyst Intern"}
        self.assertEqual(fields.level_mismatch(mba, undergrad), "For MBA or graduate students")
        self.assertIsNone(fields.level_mismatch(mba, grad))
        self.assertEqual(fields.level_mismatch(ug, grad), "For undergraduates")
        self.assertIsNone(fields.level_mismatch({"title": "Finance Intern"}, undergrad))
        self.assertIsNone(fields.level_mismatch(mba, {}))  # unknown: don't filter
        self.assertIsNone(fields.level_mismatch({"title": "MBA Program Manager"}, undergrad))  # not an internship
        new_grad = {"title": "Finance Graduate Program", "tags": ["Internship"]}  # UK sense: for new graduates
        self.assertIsNone(fields.level_mismatch(new_grad, undergrad))
        self.assertEqual(fields.level_mismatch({"title": "Supply Chain Planning Graduate Internship"}, undergrad),
                         "For MBA or graduate students")
        mba_desc = {"title": "Enterprise Planning Intern", "description": "Currently pursuing an MBA, graduating Spring 2028."}
        self.assertEqual(fields.level_mismatch(mba_desc, undergrad), "For MBA or graduate students")
        both = {"title": "Finance Intern", "description": "Pursuing a bachelor's degree, or enrolled in an MBA program."}
        self.assertIsNone(fields.level_mismatch(both, undergrad))
        skillbridge = {"title": "SkillBridge Intern - Product Manager", "tags": ["Intern"]}
        self.assertEqual(fields.level_mismatch(skillbridge, dict(undergrad, currently_enrolled=True)),
                         "For service members leaving the military (SkillBridge)")

    def test_seasons(self):
        from datetime import date
        self.assertEqual(fields.season_of("2027 Investment Banking Summer Associate"), ("Summer", 2027))
        self.assertEqual(fields.season_of("Finance Intern (Fall 2026)"), ("Fall", 2026))
        self.assertEqual(fields.season_of("Summer '27 Intern"), ("Summer", 2027))
        self.assertIsNone(fields.season_of("Finance Intern"))
        self.assertTrue(fields.season_over("Summer 2026 Intern", date(2026, 10, 16)))
        self.assertFalse(fields.season_over("Fall 2026 Intern", date(2026, 10, 16)))

    def test_business_degree_detection(self):
        self.assertTrue(fields.asks_for_business_degree({"description": "Bachelor's degree in Finance or related field"}))
        self.assertTrue(fields.asks_for_business_degree({"description": "BBA or MBA preferred"}))
        self.assertFalse(fields.asks_for_business_degree({"description": "BS in Computer Science"}))

    def test_source_terms_follow_chosen_areas(self):
        s = {"field": "business", "families": ["finance", "hr"]}
        self.assertEqual(fields.source_terms(s, "muse"), ["Accounting and Finance", "Human Resources and Recruitment"])
        self.assertEqual(fields.source_terms(s, "jobicy"), ["accounting-finance", "hr"])


if __name__ == "__main__":
    unittest.main()
