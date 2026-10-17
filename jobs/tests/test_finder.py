"""Finding a job-board posting on the employer's own site. HTTP is faked: nothing touches the network."""
import unittest
from unittest import mock

from jobbot import finder
from jobbot.sources import http

LINKEDIN = """<section><h2 class="top-card-layout__title font-sans">Procurement Intern - Summer 2027</h2>
<a class="topcard__org-name-link topcard__flavor--black-link" href="https://www.linkedin.com/company/olin">
  Olin </a><span class="topcard__flavor topcard__flavor--bullet"> Houston, TX </span></section>"""
HOME = """<a href="/about">About</a><a href="https://phe.tbe.taleo.net/phe02/ats/careers/v2/jobSearch?org=OLIN&amp;cws=47">Search Jobs</a>
<link href="https://staticphe.tbe.taleo.net/phe02/ats/x.css">"""
RSS = """<rss><channel><item><title>Procurement Co-Op - Fall 2027</title>
<link>https://phe.tbe.taleo.net/phe02/ats/careers/requisition.jsp?org=OLIN&amp;cws=47&amp;rid=15350</link></item>
<item><title>Procurement Intern - Summer 2027</title>
<link>https://phe.tbe.taleo.net/phe02/ats/careers/requisition.jsp?org=OLIN&amp;cws=47&amp;rid=15721</link></item></channel></rss>"""


class FinderTests(unittest.TestCase):
    def fake_html(self, pages):
        def get_html(url, timeout=25):
            for prefix, body in pages.items():
                if url.startswith(prefix):
                    return url, body
            raise http.FetchError(f"404 {url}")
        return mock.patch.object(http, "get_html", side_effect=get_html)

    def test_reads_a_linkedin_posting(self):
        with self.fake_html({"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/4464168018": LINKEDIN}):
            info = finder.details("https://www.linkedin.com/jobs/view/procurement-intern-summer-2027-at-olin-4464168018?trk=x")
        self.assertEqual(info, {"title": "Procurement Intern - Summer 2027", "company": "Olin", "location": "Houston, TX",
                                "website": ""})

    def test_reads_a_job_board_posting_from_its_structured_data(self):
        page = """<script type="application/ld+json">{"@type": "JobPosting", "title": "Buyer Intern",
          "hiringOrganization": {"name": "Acme", "sameAs": "https://www.acme.com"},
          "jobLocation": {"address": {"addressLocality": "Austin", "addressRegion": "TX"}}}</script>"""
        with self.fake_html({"https://www.ziprecruiter.com/": page}):
            info = finder.details("https://www.ziprecruiter.com/c/Acme/Job/Buyer-Intern/-in-Austin,TX?jid=1")
        self.assertEqual(info, {"title": "Buyer Intern", "company": "Acme", "location": "Austin, TX", "website": "https://www.acme.com"})

    def test_finds_the_job_through_the_careers_site_and_taleo_feed(self):
        pages = {"https://www.olin.com": HOME, "https://phe.tbe.taleo.net/phe02/ats/careers/v2/jobSearch": "<p>Search</p>",
                 "https://phe.tbe.taleo.net/phe02/ats/servlet/Rss?org=OLIN&cws=47": RSS}
        with self.fake_html(pages), mock.patch.object(http, "get_json", side_effect=http.FetchError("404")):
            url = finder.find("Procurement Intern - Summer 2027", "Olin", "Houston, TX")
        self.assertEqual(url, "https://phe.tbe.taleo.net/phe02/ats/careers/v2/viewRequisition?org=OLIN&cws=47&rid=15721")

    def test_the_directory_comes_first(self):
        with mock.patch.object(finder, "_careers_pages", return_value=[]):
            first = next(finder.boards("Stripe"))
        self.assertEqual(first, ("greenhouse", "stripe"))

    def test_matching_titles(self):
        hits = [("Procurement Co-Op - Fall 2027", "u1", ""), ("2027 Summer Internship - Purchasing - Houston, TX", "u2", "Houston"),
                ("2027 Summer Internship - Purchasing - Dallas, TX", "u3", "Dallas")]
        self.assertEqual(finder._best(hits, "2027 Summer Internship - Purchasing", "Houston, TX"), "u2")
        self.assertIsNone(finder._best(hits, "Procurement Intern - Summer 2027"))  # a co-op is a different job
        self.assertIsNone(finder._best([("Senior Buyer", "u4", "")], "Buyer Intern"))


if __name__ == "__main__":
    unittest.main()
