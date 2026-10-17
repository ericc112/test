import unittest

from jobbot import places


def where(loc, remote=False):
    d = places.describe({"location": loc, "remote": remote})
    return d["text"], d["states"]


class PlacesTests(unittest.TestCase):
    def test_formats_boards_use(self):
        self.assertEqual(where("CT - Hartford"), ("Hartford, CT", ["CT"]))  # Workday
        self.assertEqual(where("California - San Francisco"), ("San Francisco, CA", ["CA"]))
        self.assertEqual(where("1000 Nicollet Mall, Minneapolis,MN 55403-2542"), ("Minneapolis, MN", ["MN"]))
        self.assertEqual(where("Lake Buena Vista, FL, USA"), ("Lake Buena Vista, FL", ["FL"]))
        self.assertEqual(where("Boston, Massachusetts"), ("Boston, MA", ["MA"]))
        self.assertEqual(where("Washington, DC"), ("Washington, DC", ["DC"]))

    def test_remote_and_hybrid(self):
        self.assertEqual(where("United States", remote=True), ("Remote (US)", []))
        self.assertEqual(where("Hybrid - New York, NY"), ("New York, NY · Hybrid", ["NY"]))
        self.assertEqual(where("Hybrid"), ("Hybrid", []))
        self.assertEqual(where("Athens, Greece; Flexible / Remote", remote=True), ("Remote · Athens, Greece", []))

    def test_other_countries_are_not_us_states(self):
        self.assertEqual(where("Toronto · CA-Toronto")[1], [])  # CA here is Canada
        self.assertEqual(where("London, UK"), ("London, UK", []))
        self.assertFalse(places.describe({"location": "Sao Paulo Sao Paulo Brazil"})["us"])

    def test_several_offices(self):
        text, states = where("New York, Seattle, South San Francisco HQ")
        self.assertEqual(states, ["CA", "NY", "WA"])
        self.assertTrue(text.endswith("+1 more"))


if __name__ == "__main__":
    unittest.main()
