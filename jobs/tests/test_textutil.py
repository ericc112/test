import unittest

from jobbot.textutil import contains_phrase, html_to_text, norm, pick_option, split_list


class TextUtilTests(unittest.TestCase):
    def test_html_to_text_handles_double_escaping(self):
        self.assertEqual(html_to_text("&lt;p&gt;Hello &amp;amp; welcome&lt;/p&gt;&lt;p&gt;Two&lt;/p&gt;"), "Hello & welcome\n\nTwo")

    def test_norm_drops_required_markers_and_separators(self):
        self.assertEqual(norm("First Name*"), "first name")
        self.assertEqual(norm("University of California - Berkeley"), "university of california berkeley")

    def test_contains_phrase_is_whole_word(self):
        self.assertTrue(contains_phrase("Senior Java Engineer", "java"))
        self.assertFalse(contains_phrase("JavaScript Engineer", "java"))

    def test_split_list(self):
        self.assertEqual(split_list("a, b\nc;;"), ["a", "b", "c"])
        self.assertEqual(split_list(["x", " ", "y"]), ["x", "y"])

    def test_yes_and_no_in_other_words(self):
        self.assertEqual(pick_option("No", ["Select One", "Yes", "Not to my knowledge"]), "Not to my knowledge")
        self.assertEqual(pick_option("No", ["I have never been employed by the U.S. Federal Government.",
                                            "I am currently employed by the U.S. Federal Government."]),
                         "I have never been employed by the U.S. Federal Government.")
        self.assertEqual(pick_option("No", ["I consent to receive emails", "I do not consent to receive emails"]),
                         "I do not consent to receive emails")
        self.assertEqual(pick_option("Yes", ["I am able to meet the onsite requirements", "I am not able to"]),
                         "I am able to meet the onsite requirements")
        self.assertEqual(pick_option("Yes", ["By checking this box, I consent to the use of AI", "I opt out"]),
                         "By checking this box, I consent to the use of AI")
        self.assertIsNone(pick_option("No", ["Yes", "Maybe"]))

    def test_numbers_pick_their_range(self):
        self.assertEqual(pick_option("65000", ["$40,000-$50,000", "$60,000-$70,000"]), "$60,000-$70,000")
        self.assertEqual(pick_option("$65,000", ["0 - 30,000", "60,000 - 70,000"]), "60,000 - 70,000")
        self.assertEqual(pick_option("0", ["Less than 1 year", "More than 1 year, less than 3 years"]), "Less than 1 year")
        self.assertEqual(pick_option("2", ["0-1 Year", "1-3 Years", "5+ Years"]), "1-3 Years")
        self.assertEqual(pick_option("6", ["0-1 Year", "1-3 Years", "5+ Years"]), "5+ Years")
        self.assertEqual(pick_option("0", ["No previous relevant work experience", "Up to 2 years"]), "No previous relevant work experience")
        self.assertEqual(pick_option("0.3", ["0 - 6 months", "6 - 11 months", "1 - 2 years"]), "0 - 6 months")
        self.assertEqual(pick_option("2", ["0", "1", "2", "3"]), "2")

    def test_pick_option_yes_no_prefix(self):
        opts = ["Yes, I intend to work remotely.", "No, I intend to work from an office location."]
        self.assertEqual(pick_option("Yes", opts), opts[0])
        self.assertEqual(pick_option("No", opts), opts[1])
        self.assertIsNone(pick_option("Yes", ["Maybe"]))

    def test_pick_option_decline(self):
        opts = ["Male", "Female", "I don't wish to answer"]
        self.assertEqual(pick_option("decline", opts), "I don't wish to answer")
        self.assertEqual(pick_option("decline", ["Decline To Self Identify", "Yes"]), "Decline To Self Identify")

    def test_pick_option_aliases(self):
        self.assertEqual(pick_option("United States", ["UK", "US", "Canada"]), "US")
        self.assertEqual(pick_option("Bachelor's", ["Associate's Degree", "Bachelor's Degree", "Master's Degree"]), "Bachelor's Degree")

    def test_pick_option_fuzzy_school(self):
        opts = ["Berkeley College", "University of California - Berkeley", "University of California - Davis"]
        self.assertEqual(pick_option("University of California, Berkeley", opts), opts[1])

    def test_pick_option_does_not_confuse_schools(self):
        self.assertIsNone(pick_option("New York University", ["Andrews University", "Arizona State University"]))
        self.assertEqual(pick_option("New York University", ["Andrews University", "New York University Abu Dhabi", "New York University"]),
                         "New York University")
        self.assertEqual(pick_option("Univ. of Michigan", ["University of Michigan", "Michigan State University"]), None)
        self.assertEqual(pick_option("Michigan State", ["University of Michigan", "Michigan State University"]), "Michigan State University")

    def test_pick_option_prefers_closest_containing(self):
        opts = ["San Francisco, California, United States", "South San Francisco, California, United States"]
        self.assertEqual(pick_option("San Francisco, California", opts), opts[0])


if __name__ == "__main__":
    unittest.main()
