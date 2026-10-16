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


if __name__ == "__main__":
    unittest.main()
