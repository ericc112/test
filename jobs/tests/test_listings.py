"""Job listings read from screenshots, screen recordings and copied text. Nothing touches the network:
looking a job up on the employer's site is faked. The OCR tests run only where the reader is installed
(pip install -r requirements-ocr.txt) and draw their screenshots with the test browser."""
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jobbot import listings
from jobbot.listings import Line
from tests.helpers import TempData, browser_available

FIXTURES = Path(__file__).parent / "fixtures"
HAVE_OCR = importlib.util.find_spec("rapidocr_onnxruntime") is not None


def table_screen():
    """What the reader saw on a dark job-board table (title and company · city, then date and score to the right)."""
    rows = [("ROLE", 38, 42, 30), ("DATE", 1159, 42, 30), ("MATCH SCORE", 1300, 44, 30), ("SAVE", 1553, 42, 30)]
    jobs = [("Supply Chain Analyst Intern - Summer 2027", "PepsiCo · Plano,TX", "2h ago", "96%"),
            ("Operations Management Intern", "Tesla · Austin, TX", "5h ago", "93%"),
            ("Software Engineering Intern", "Stripe · Remote", "1d ago", "95%"),
            ("Procurement Intern, Summer 2027", "Caterpillar ·Irving, TX", "1d ago", "91%"),
            ("Marketing Analytics Intern", "Dell Technologies · Round Rock, TX", "2d ago", "88%")]
    lines = [Line(t, x, y, h) for t, x, y, h in rows]
    for i, (title, sub, date, score) in enumerate(jobs):
        top = 124 + 130 * i
        lines += [Line(title, 40, top, 34), Line(date, 1158, top + 13, 28), Line(score, 1341, top + 13, 28),
                  Line(sub, 41, top + 38, 28)]
    return lines


def cards_screen():
    """A phone app's cards: company above the title, then city · type · pay, then the match."""
    cards = [("Amazon", "Supply Chain Intern", "Seattle, WA :Internship : $28/hr", "97% match"),
             ("Toyota", "Production Control Intern", "Plano, TX · Internship", "94% match"),
             ("Google", "Software Engineering Intern", "Mountain View, CA", "96% match")]
    lines = []
    for i, (company, title, sub, score) in enumerate(cards):
        top = 100 + 400 * i
        lines += [Line(company, 60, top, 40), Line(title, 60, top + 60, 52), Line(sub, 60, top + 135, 32),
                  Line(score, 60, top + 205, 34)]
    return lines


def phone_board_screen():
    """A phone job-board app (LinkedIn's look): the search text, filter chips, then cards with the company's logo left
    of the text, titles that wrap onto two lines, company, city, perks and how long ago, and the app's tab bar."""
    rows = [("intern posted in the past 24 hours", 298, 226, 36), ("Jobs", 166, 349, 49), ("Past 24 hours", 438, 352, 42),
            ("Easy Apply", 898, 346, 54),
            ("Supply Chain Intern - Engineering", 214, 495, 54), ("ACME", 40, 548, 30), ("and Business Majors", 216, 548, 30),
            ("Acme Foods", 215, 622, 40), ("Fresno, TX", 215, 680, 40), ("401(k) benefit", 218, 743, 36),
            ("15 hours ago : Be an early applicant", 215, 895, 38),
            ("2027 Summer Internship -", 215, 989, 52), ("Purchasing", 215, 1050, 53), ("Perry Homes", 217, 1118, 37),
            ("Houston, TX (Hybrid)", 215, 1175, 39), ("Actively reviewing applicants", 299, 1256, 37),
            ("18 hours ago : Be an early applicant :", 215, 1336, 32), ("in", 874, 1336, 32),
            ("HOUSTON - Land Development,", 215, 1276 + 300, 47), ("BGE", 41, 1310 + 300, 61), ("Internship", 215, 1314 + 300, 53),
            ("BGE, Inc.", 216, 1403 + 300, 40), ("Houston, TX (On-site)", 214, 1461 + 300, 39),
            ("Assurance Intern - Winter 2028", 218, 2165, 39), ("IBDO", 50, 2198, 50), ("(Houston) ①", 218, 2194, 57),
            ("BDO USA", 217, 2287, 37), ("Houston, TX (Hybrid)", 214, 2343, 43),
            ("This job search alert is on", 53, 2483, 39), ("On", 906, 2481, 45),
            ("Home", 66, 2675, 34), ("Video", 307, 2675, 40), ("My Network", 499, 2677, 36), ("Jobs", 1041, 2677, 36)]
    return [Line(listings._clean(t), x, y, h) for t, x, y, h in rows]


class SplitTests(unittest.TestCase):
    def test_reads_each_row_of_a_table(self):
        got = listings.split(table_screen())
        self.assertEqual([(l["title"], l["company"], l["location"], l["posted"], l["score"]) for l in got], [
            ("Supply Chain Analyst Intern - Summer 2027", "PepsiCo", "Plano, TX", "2h ago", 96),
            ("Operations Management Intern", "Tesla", "Austin, TX", "5h ago", 93),
            ("Software Engineering Intern", "Stripe", "Remote", "1d ago", 95),
            ("Procurement Intern, Summer 2027", "Caterpillar", "Irving, TX", "1d ago", 91),
            ("Marketing Analytics Intern", "Dell Technologies", "Round Rock, TX", "2d ago", 88)])

    def test_reads_cards_with_the_company_above_the_title(self):
        got = listings.split(cards_screen())
        self.assertEqual([(l["title"], l["company"], l["location"], l["score"]) for l in got], [
            ("Supply Chain Intern", "Amazon", "Seattle, WA", 97),
            ("Production Control Intern", "Toyota", "Plano, TX", 94),
            ("Software Engineering Intern", "Google", "Mountain View, CA", 96)])

    def test_reads_copied_text(self):
        text = """Jobs for you
Supply Chain Intern
Lockheed Martin
Fort Worth, TX (On-site)
Promoted · Easy Apply
Financial Analyst Intern - Summer 2027
Charles Schwab
Westlake, TX (Hybrid)
Posted 3 days ago
92% match
"""
        got = listings.split(listings.text_lines(text))
        self.assertEqual([(l["title"], l["company"], l["location"], l["posted"], l["score"]) for l in got], [
            ("Supply Chain Intern", "Lockheed Martin", "Fort Worth, TX (On-site)", "", None),
            ("Financial Analyst Intern - Summer 2027", "Charles Schwab", "Westlake, TX (Hybrid)", "Posted 3 days ago", 92)])

    def test_reads_a_phone_board_with_logos_and_wrapped_titles(self):
        got = listings.split(phone_board_screen())
        self.assertEqual([(l["title"], l["company"], l["location"], l["posted"]) for l in got], [
            ("Supply Chain Intern - Engineering and Business Majors", "Acme Foods", "Fresno, TX", "15 hours ago"),
            ("2027 Summer Internship - Purchasing", "Perry Homes", "Houston, TX (Hybrid)", "18 hours ago"),
            ("HOUSTON - Land Development, Internship", "BGE, Inc.", "Houston, TX (On-site)", ""),
            ("Assurance Intern - Winter 2028 (Houston)", "BDO USA", "Houston, TX (Hybrid)", "")])

    def test_wrapped_titles(self):
        self.assertTrue(listings._continues("2027 Summer Internship -", "Purchasing"))
        self.assertTrue(listings._continues("Supply Chain Intern - Engineering", "and Business Majors"))
        self.assertTrue(listings._continues("HOUSTON - Land Development,", "Internship"))
        self.assertFalse(listings._continues("Learning and Development Intern (", "Olin"))  # cut off, not wrapped
        self.assertFalse(listings._continues("Buyer Intern", "Acme"))
        self.assertFalse(listings._continues("Buyer Intern -", "Houston, TX"))
        self.assertEqual(listings._clean_title("Energy & Utilities Analyst, 1898 &"), "Energy & Utilities Analyst, 1898")

    def test_a_location_line_isnt_a_title(self):
        self.assertEqual(listings.split(listings.text_lines("Plano, TX · Internship\nInternship · Remote")), [])

    def test_a_title_with_a_comma_isnt_a_place(self):
        self.assertEqual(listings._piece("Procurement Intern, Summer 2027")[0], "other")
        self.assertEqual(listings._piece("Dell Technologies, Inc")[0], "other")
        self.assertEqual(listings._piece("Austin, Texas"), ("location", "Austin, Texas"))

    def test_the_same_job_in_several_stills_is_one_listing(self):
        first = listings.split(table_screen())
        cut_off = [{"title": "Operations Management Intern", "company": "", "location": "", "posted": "", "score": None}]
        merged = listings.merge(first + cut_off + listings.split(table_screen()))
        self.assertEqual(len(merged), 5)


class PickTests(unittest.TestCase):
    def test_keeps_business_roles_the_board_scored_90_or_more(self):
        kept, dropped = listings.pick(listings.split(table_screen()))
        self.assertEqual([l["title"] for l in kept], ["Supply Chain Analyst Intern - Summer 2027", "Operations Management Intern",
                                                      "Procurement Intern, Summer 2027"])
        self.assertEqual({l["title"]: l["why"] for l in dropped}, {
            "Software Engineering Intern": "Not a business role",
            "Marketing Analytics Intern": "Board score 88, under 90"})
        self.assertEqual(kept[0]["area"], "Operations & Supply Chain")

    def test_a_listing_without_a_score_or_company(self):
        kept, dropped = listings.pick([
            {"title": "Buyer Intern", "company": "Acme", "location": "", "posted": "", "score": None},
            {"title": "Buyer Intern", "company": "", "location": "", "posted": "", "score": 95}], min_score=90)
        self.assertEqual([l["company"] for l in kept], ["Acme"])
        self.assertEqual(dropped[0]["why"], "Company not read")

    def test_a_vague_title_counts_when_the_board_scored_it(self):
        job = {"title": "Production Control Intern", "company": "Toyota", "location": "", "posted": "", "score": 94}
        kept, _ = listings.pick([job])
        self.assertEqual(kept[0]["area"], "Business (the title doesn't say which area)")
        kept, dropped = listings.pick([{**job, "score": None}])  # a board with no score doesn't vouch for it
        self.assertEqual((kept, dropped[0]["why"]), ([], "Not clearly a business role"))


class LocateTests(unittest.TestCase):
    def test_finds_each_job_on_the_employers_site(self):
        hits = {"Supply Chain Intern": "https://amazon.jobs/en/jobs/1"}
        with mock.patch.object(listings.finder, "find", side_effect=lambda t, c, l, budget: hits.get(t)):
            got = listings.locate([{"title": "Supply Chain Intern", "company": "Amazon", "location": "Seattle, WA"},
                                   {"title": "Buyer Intern", "company": "Acme", "location": ""}])
        self.assertEqual([(l["url"], l["found"]) for l in got], [("https://amazon.jobs/en/jobs/1", True), ("", False)])
        self.assertEqual(got[1]["why"], "Not found on the employer's site")

    def test_a_copied_link_is_used(self):
        rows = listings._with_links([{"title": "Buyer Intern", "company": "Acme", "location": ""}],
                                    [{"t": "Buyer Intern", "u": "https://boards.greenhouse.io/acme/jobs/1"}])
        with mock.patch.object(listings.finder, "find") as find:
            got = listings.locate(rows)
        find.assert_not_called()
        self.assertEqual(got[0]["url"], "https://boards.greenhouse.io/acme/jobs/1")

    def test_a_lookup_that_fails_keeps_the_others(self):
        def find(title, company, location, budget):
            if title == "Bad":
                raise RuntimeError("site down")
            return "https://example.com/job"
        with mock.patch.object(listings.finder, "find", side_effect=find):
            got = listings.locate([{"title": "Bad", "company": "A", "location": ""}, {"title": "Good", "company": "B", "location": ""}])
        self.assertEqual([l["found"] for l in got], [False, True])


class FileTests(unittest.TestCase):
    def test_a_file_it_cant_read(self):
        with self.assertRaises(listings.ReadError):
            listings.read("listings.docx")

    def test_a_saved_page_brings_its_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "board.html")
            Path(path).write_text('<div><a href="https://jobs.lever.co/acme/1">Buyer Intern</a></div><div>Acme</div>'
                                  '<div>Austin, TX</div><div>93%</div>')
            result = listings.run([path], find=False)
        self.assertEqual([(l["title"], l["company"], l["score"], l["url"]) for l in result["kept"]],
                         [("Buyer Intern", "Acme", 93, "https://jobs.lever.co/acme/1")])

    def test_errors_are_reported_per_file(self):
        result = listings.run(["notes.docx"], text="Buyer Intern\nAcme\n95%", find=False)
        self.assertEqual([e["file"] for e in result["errors"]], ["notes.docx"])
        self.assertIn("can't read .docx files", result["errors"][0]["why"])
        self.assertEqual(len(result["kept"]), 1)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.data = TempData()

    def tearDown(self):
        self.data.close()

    def test_read_listings_writes_the_page_shape(self):
        from jobbot.__main__ import main
        with tempfile.TemporaryDirectory() as tmp:
            text, out = os.path.join(tmp, "copied.txt"), os.path.join(tmp, "out.json")
            Path(text).write_text("Supply Chain Intern\nAmazon\nSeattle, WA\n97% match\nData Engineer Intern\nAcme\n99%\n")
            with mock.patch("sys.stdout"):
                main(["read-listings", "--text", text, "--no-find", "--out", out])
            got = json.loads(Path(out).read_text())
        self.assertEqual(got["read"], 2)
        self.assertEqual(got["kept"], [{"t": "Supply Chain Intern", "c": "Amazon", "l": "Seattle, WA", "p": "", "s": 97, "u": "",
                                        "a": "Operations & Supply Chain", "why": ""}])
        self.assertEqual(got["dropped"][0]["t"], "Data Engineer Intern")


@unittest.skipUnless(HAVE_OCR and browser_available(), "needs the OCR reader (requirements-ocr.txt) and the test browser")
class OcrTests(unittest.TestCase):
    """The real reader on screenshots the test browser draws."""

    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.tmp = tempfile.mkdtemp()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1100, "height": 600}, device_scale_factor=2)
            page.goto((FIXTURES / "board_table.html").as_uri())
            page.screenshot(path=os.path.join(cls.tmp, "table.png"))
            page = browser.new_page(viewport={"width": 390, "height": 700}, device_scale_factor=3)
            page.goto((FIXTURES / "board_cards.html").as_uri())
            for i, y in enumerate([0, 350, 700, 1100]):
                page.evaluate(f"window.scrollTo(0, {y})")
                page.screenshot(path=os.path.join(cls.tmp, f"still{i}.png"))
            browser.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_reads_a_screenshot(self):
        result = listings.run([os.path.join(self.tmp, "table.png")], find=False)
        self.assertEqual(result["read"], 6)
        self.assertEqual([(l["title"], l["company"], l["location"], l["score"]) for l in result["kept"]], [
            ("Supply Chain Analyst Intern - Summer 2027", "PepsiCo", "Plano, TX", 96),
            ("Operations Management Intern", "Tesla", "Austin, TX", 93),
            ("Procurement Intern, Summer 2027", "Caterpillar", "Irving, TX", 91),
            ("Logistics Coordinator Intern", "H-E-B", "San Antonio, TX", 92)])

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
    def test_reads_a_screen_recording(self):
        video = os.path.join(self.tmp, "scroll.mp4")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "0.5", "-i", os.path.join(self.tmp, "still%d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "scale=1170:-2", video], check=True)
        result = listings.run([video], find=False)
        self.assertEqual(result["read"], 10)
        kept = {l["title"]: (l["company"], l["location"], l["score"]) for l in result["kept"]}
        self.assertEqual(kept, {
            "Supply Chain Intern": ("Amazon", "Seattle, WA", 97),
            "Production Control Intern": ("Toyota", "Plano, TX", 94),
            "Summer Analyst - Operations": ("Goldman Sachs", "New York, NY", 90),
            "Purchasing Intern": ("Ford", "Dearborn, MI", 92),
            "Merchandising Intern": ("Walmart", "Bentonville, AR", 91),
            "Sales Intern": ("PepsiCo", "Purchase, NY", 93),
            "Sourcing Intern": ("Nike", "Beaverton, OR", 95)})


if __name__ == "__main__":
    unittest.main()
