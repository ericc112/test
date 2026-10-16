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
}
NOT_BUSINESS = [
    "Senior Software Engineer", "Sales Engineer", "Solutions Architect", "Data Scientist", "Analytics Engineer",
    "Technical Program Manager", "UX Designer", "Registered Nurse", "Barista - Temporary", "Store Manager",
    "Shift Lead", "Solar Appointment Setter", "Legal Counsel", "Clinical Research Associate", "Security Analyst",
    "IT Support Specialist", "TIG Welder (Starship Components)", "Warehouse Associate", "Customer Service Representative",
    "Data Partner - Finance - Remote", "Personalized Internet Ads Assessor", "Project Manager - Construction",
    "Customer Technology Advisor for Mainframe",
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
