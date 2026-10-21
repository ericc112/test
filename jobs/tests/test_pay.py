import unittest

from jobbot import pay, scoring


def hr(description="", **fields):
    h = pay.hourly(dict(fields, description=description))
    return h and h["text"]


class PayTests(unittest.TestCase):
    def test_hourly_ranges_as_written(self):
        self.assertEqual(hr("The typical base salary range for this position is $29 - $33 per hour."), "$29–33/hr")
        self.assertEqual(hr("Pay: $18 - 26.00/hr depending on location"), "$18–26/hr")
        self.assertEqual(hr("Compensation: $23.50-$29.25/hour"), "$23.50–29.25/hr")
        self.assertEqual(hr("Salary Range $25.00 - $26.00  Target Openings 2"), "$25–26/hr")
        self.assertEqual(hr("Hourly Range: $50 — $50 USD"), "$50/hr")
        self.assertEqual(hr("The pay is $20 per hour and is expected to work 15-20 hours per week"), "$20/hr")

    def test_yearly_and_monthly_pay_is_converted_and_marked(self):
        self.assertEqual(hr("Base Salary: $39,100.00 – $126,500.00. Salaries may vary."), "≈$19–61/hr")
        self.assertEqual(hr("Compensation: $1,500 USD Monthly Base + 15% Commission"), "≈$9/hr")
        self.assertEqual(pay.hourly({"description": "Salary: $45,000 - $60,000 annually"})["basis"], "year")

    def test_dollar_figures_that_are_not_pay(self):
        for text in ["We provide $6 billion in annual community benefits.",
                     "Raised $4.1M in Seed Funding to streamline vendor payments",
                     "We manage $60 billion in assets under management.",
                     "ProSidian will pay up to $5k for all referrals employed for 90 days",
                     "Brilliant will reimburse you $250 each month for using your personal cell phone",
                     "Monthly scholarship of $500",
                     "Pay range: $0.00 - $0.00"]:
            self.assertIsNone(hr(text), text)
        # The stipend in one sentence doesn't hide the wage in the next.
        self.assertEqual(hr("Interns receive a housing stipend between $1,000 and $3,000. "
                            "The hourly rate is $17.00 to $24.00 per hour."), "$17–24/hr")
        # An earlier sentence about "awards" doesn't either.
        self.assertEqual(hr("Employees are eligible for cash incentive awards.  Salary Range $25.00 - $26.00"), "$25–26/hr")

    def test_rates_by_degree_level_show_the_undergraduate_one(self):
        text = ("If the selected candidate is pursuing an Associate-level degree: $16.00 per hour  "
                "If the selected candidate is pursuing an Undergraduate-level degree: $22.00 per hour  "
                "If the selected candidate is pursuing a Graduate-level degree: $32.50 per hour")
        self.assertEqual(hr(text), "$22/hr")
        self.assertEqual(hr("$32.70/hr for undergraduate students in Denver and $42.07/hr for undergraduate students in New York."),
                         "$32.70–42.07/hr")

    def test_salary_fields(self):
        self.assertEqual(hr(salary_text="USD 21-21 hourly"), "$21/hr")
        self.assertEqual(hr(salary_text="USD 19-21"), "$19–21/hr")  # size says hourly
        self.assertEqual(hr(salary_text="USD 37752-56650", salary_min=37752, salary_max=56650), "≈$18–27/hr")
        self.assertIsNone(hr(salary_text="INR 15000-15000"))
        self.assertIsNone(hr(salary_text="EUR 51000-51000", salary_min=51000, salary_max=51000))
        # A rate stated per hour in the description wins over a guessed one.
        self.assertEqual(hr("Pay: $24.00 per hour", salary_text="USD 37752-56650", salary_min=37752, salary_max=56650), "$24/hr")

    def test_score_reason_shows_hourly_pay(self):
        job = {"title": "Finance Intern", "description": "Pay: $25.00 per hour", "location": "New York, NY",
               "salary_text": "USD 25-25"}
        _, reasons, _ = scoring.score(job, {"field": "business", "job_types": ["internship"]}, {"skills": ""})
        self.assertIn("Pay: $25/hr", reasons)


class StoredPayTests(unittest.TestCase):
    """pay.extract / pay.for_job: the stored pay fields (the export's payText/payMin/payMax).

    Only pay stated per hour gets hourly numbers; any other period is stored as the
    written text with hourly fields None — never converted, never guessed from the web.
    """

    def test_hourly_formats(self):
        self.assertEqual(pay.extract("The typical base salary range for this position is $28.00 - $33.00 per hour."),
                         ("$28.00 - $33.00 per hour", 28.0, 33.0))
        self.assertEqual(pay.extract("Pay: $28–$33/hr"), ("$28–$33/hr", 28.0, 33.0))
        self.assertEqual(pay.extract("This role pays $25/hr."), ("$25/hr", 25.0, 25.0))
        self.assertEqual(pay.extract("Compensation: $23.50-$29.25/hour"), ("$23.50-$29.25/hour", 23.5, 29.25))
        self.assertEqual(pay.extract("Pay range: USD $28 - $33 per hour"), ("USD $28 - $33 per hour", 28.0, 33.0))
        self.assertEqual(pay.extract("The hourly rate is $22.50."), ("$22.50", 22.5, 22.5))
        self.assertEqual(pay.extract("Pay range is $29 - $33 depending on location"), ("$29 - $33", 29.0, 33.0))

    def test_up_to_gives_a_max_and_no_min(self):
        self.assertEqual(pay.extract("Earn up to $30 per hour"), ("up to $30 per hour", None, 30.0))

    def test_other_periods_stay_as_written_text(self):
        self.assertEqual(pay.extract("Salary: $40,000 - $55,000 a year."), ("$40,000 - $55,000 a year", None, None))
        self.assertEqual(pay.extract("Pay is $1,798 - $2,914 bi-weekly."), ("$1,798 - $2,914 bi-weekly", None, None))

    def test_stipend_is_not_pay_and_not_the_max(self):
        # The stipend figure must not become pay_max, and must not hide the wage next to it.
        self.assertEqual(pay.extract("The pay is $32.50/hr + a $2,500 housing stipend."),
                         ("$32.50/hr", 32.5, 32.5))
        self.assertIsNone(pay.extract("Interns receive a $2,500 housing stipend."))
        self.assertIsNone(pay.extract("Monthly scholarship of $500"))

    def test_figures_that_are_not_pay(self):
        for text in ["We provide $6 billion in annual community benefits.",
                     "We manage $60 billion in assets under management.",
                     "The company raised $4.1M in seed funding.",
                     "Join our team! Great culture, mentorship and free snacks.",
                     ""]:
            self.assertIsNone(pay.extract(text), text)

    def test_a_pay_labeled_figure_wins(self):
        self.assertEqual(pay.extract("$18 per hour. The salary range for this role is $24 - $28 per hour."),
                         ("$24 - $28 per hour", 24.0, 28.0))

    def test_for_job_uses_the_boards_salary_fields(self):
        self.assertEqual(pay.for_job({"salary_text": "USD 21-21 hourly"}), ("USD 21-21 hourly", 21.0, 21.0))
        # Annual fields stay as written text (hourly() converts them for display; storage does not).
        annual = {"salary_text": "USD 37752-56650", "salary_min": 37752, "salary_max": 56650}
        self.assertEqual(pay.for_job(annual), ("USD 37752-56650", None, None))
        # A rate stated in the description wins over the fields.
        self.assertEqual(pay.for_job(dict(annual, description="Pay: $25.00 per hour")),
                         ("$25.00 per hour", 25.0, 25.0))
        self.assertIsNone(pay.for_job({"title": "Finance Intern", "description": "Great team, learn a lot."}))


class PaidOnlyTests(unittest.TestCase):
    INTERNS = {"field": "business", "job_types": ["internship"]}

    def intern(self, description, source="himalayas", title="Marketing Intern"):
        return {"title": title, "description": description, "source": source, "location": "Remote", "remote": True}

    def test_stated_unpaid_work_is_hidden_everywhere(self):
        for text in ["Compensation: Unpaid, designed for educational purposes only.",
                     "Please note that this is an unpaid internship.",
                     "Compensation: This is not a paid internship.",
                     "All roles are pro-bono (unpaid) positions.",
                     "This internship is for academic credit only.",
                     "Compensation is commission-only."]:
            self.assertEqual(pay.status(self.intern(text)), "unpaid", text)
            self.assertEqual(scoring.exclusion(self.intern(text, source="workday"), self.INTERNS), "Unpaid", text)
        self.assertEqual(pay.status(self.intern("", title="Executive Marketing Intern/Volunteer")), "unpaid")

    def test_benefits_wording_is_not_unpaid(self):
        for text in ["Volunteer time off and employee resource groups.", "Up to 12 weeks of unpaid leave.",
                     "Opportunities to join volunteer activities."]:
            self.assertNotEqual(pay.status(self.intern(text)), "unpaid", text)

    def test_job_boards_must_say_it_is_paid(self):
        self.assertEqual(scoring.exclusion(self.intern("Great team, learn a lot."), self.INTERNS), "Pay not stated")
        self.assertIsNone(scoring.exclusion(self.intern("This is a paid internship."), self.INTERNS))
        self.assertIsNone(scoring.exclusion(self.intern("Pay: $20 per hour"), self.INTERNS))
        # An employer's own careers site: large employers pay their interns.
        self.assertIsNone(scoring.exclusion(self.intern("Great team.", source="workday"), self.INTERNS))
        # Your choice: switch it off to see everything except stated-unpaid roles... and those too.
        self.assertIsNone(scoring.exclusion(self.intern("Great team."), dict(self.INTERNS, paid_only=False)))


if __name__ == "__main__":
    unittest.main()
