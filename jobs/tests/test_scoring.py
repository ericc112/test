import unittest
from datetime import datetime, timedelta, timezone

from jobbot import scoring

SEARCH = {"job_types": ["full_time"], "keywords": ["software engineer", "backend engineer"], "exclude": ["intern", "manager"],
          "locations": ["Remote", "United States"], "remote": "any", "min_salary": 120000, "max_age_days": 30}
PROFILE = {"skills": "python, go, aws, kubernetes"}


def job(**kw):
    base = {"title": "Senior Software Engineer", "description": "We use Python and AWS.", "location": "Remote",
            "remote": True, "posted_at": datetime.now(timezone.utc).isoformat()}
    base.update(kw)
    return base


class ScoringTests(unittest.TestCase):
    def test_title_match(self):
        self.assertEqual(scoring.title_match("Senior Software Engineer", ["software engineer"])[0], 40)
        self.assertEqual(scoring.title_match("Software Engineering Lead", ["software engineer"])[0], 32)
        self.assertLess(scoring.title_match("Data Analyst", ["software engineer"])[0], 32)

    def test_relevant(self):
        self.assertTrue(scoring.relevant(job(), SEARCH))
        self.assertFalse(scoring.relevant(job(title="Account Executive"), SEARCH))

    def test_exclusions(self):
        self.assertIn("intern", scoring.exclusion(job(title="Software Engineer Intern"), SEARCH).lower())
        old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        self.assertIn("days ago", scoring.exclusion(job(posted_at=old), SEARCH))
        self.assertIn("below", scoring.exclusion(job(salary_max=90000), SEARCH))
        self.assertIsNone(scoring.exclusion(job(salary_max=150000), SEARCH))
        self.assertEqual(scoring.exclusion(job(remote=False, location="NYC"), dict(SEARCH, remote="remote_only")), "Not remote")

    def test_good_remote_match_scores_high(self):
        s, reasons, excluded = scoring.score(job(), SEARCH, PROFILE)
        self.assertIsNone(excluded)
        self.assertGreaterEqual(s, 75)
        self.assertTrue(any("skills" in r for r in reasons))

    def test_business_field_scoring(self):
        biz = dict(SEARCH, field="business", keywords=[])
        s, reasons, excluded = scoring.score(job(title="Financial Analyst", description="Bachelor's degree in Finance. Excel."),
                                             biz, {"skills": "Excel"})
        self.assertIsNone(excluded)
        self.assertIn("Finance & Accounting role", reasons)
        self.assertIn("Asks for a business degree", reasons)
        direct, _, _ = scoring.score(job(title="Financial Analyst", ats="greenhouse"), biz, {"skills": "Excel"})
        plain, _, _ = scoring.score(job(title="Financial Analyst"), biz, {"skills": "Excel"})
        self.assertEqual(direct - plain, 5)
        self.assertEqual(scoring.score(job(title="Software Engineer"), biz, PROFILE)[2], "Not a business role")

    def test_us_cities_count_as_united_states(self):
        for loc in ["Bethesda, MD", "NC - Charlotte (28210)", "Austin, Texas", "New York, NY 10001", "McLean, VA",
                    "Remote - USA", "Chicago, Illinois, United States"]:
            self.assertTrue(scoring.looks_us(loc), loc)
        for loc in ["London, UK", "Toronto, ON", "Amsterdam", "Bengaluru, India", "Paris, France"]:
            self.assertFalse(scoring.looks_us(loc), loc)
        pts, reason = scoring.location_fit(job(remote=False, location="Bethesda, MD"), SEARCH)
        self.assertEqual((pts, reason), (20, "In United States"))

    def test_unstated_location_is_neutral(self):
        self.assertEqual(scoring.location_fit(job(remote=False, location="Hybrid"), SEARCH), (5, "Location not stated"))

    def test_internship_mode(self):
        interns = {"job_types": ["internship"], "field": "business", "locations": ["United States"]}
        today_title = "Summer 2027 Finance Intern"
        s, reasons, excluded = scoring.score(job(title=today_title, location="New York, NY", remote=False), interns,
                                             {"internship_terms": "Summer 2027"})
        self.assertIsNone(excluded)
        self.assertIn("Internship", reasons)
        self.assertIn("Summer 2027, the term you want", reasons)
        self.assertEqual(scoring.exclusion(job(title="Financial Analyst"), interns), "Not an internship")
        self.assertIn("has already passed", scoring.exclusion(job(title="Summer 2025 Finance Intern"), interns))
        other, reasons2, _ = scoring.score(job(title="Spring 2027 Finance Intern", location="New York, NY", remote=False),
                                           interns, {"internship_terms": "Summer 2027"})
        self.assertLess(other, s)
        self.assertIn("Spring 2027 (you want Summer 2027)", reasons2)
        both = dict(interns, job_types=["internship", "full_time"])
        self.assertIsNone(scoring.exclusion(job(title="Financial Analyst"), both))
        self.assertEqual(scoring.exclusion(job(title="Part-Time Financial Analyst"), both), "Part-time or temporary")

    def test_location_mismatch_is_penalised(self):
        here, _, _ = scoring.score(job(remote=False, location="Austin, TX, USA"), SEARCH, PROFILE)
        abroad, _, _ = scoring.score(job(remote=False, location="Amsterdam"), SEARCH, PROFILE)
        locked, reasons, _ = scoring.score(job(location="Poland, Portugal, UK"), SEARCH, PROFILE)
        self.assertGreater(here, abroad + 30)
        self.assertGreater(here, locked + 30)
        self.assertTrue(any("only for" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
