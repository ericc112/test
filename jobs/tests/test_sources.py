import unittest
from unittest import mock

from jobbot import ats, sources
from jobbot.sources import http

GH_JOB = {
        "id": 101, "title": "Financial Analyst", "company_name": "Acme", "absolute_url": "https://acme.com/jobs?gh_jid=101",
        "location": {"name": "Remote - US"}, "content": "&lt;p&gt;Python &amp;amp; Go&lt;/p&gt;",
        "first_published": "2026-10-10T10:00:00-04:00", "departments": [{"name": "Finance"}]}
GH_LIST = {"jobs": [{k: v for k, v in GH_JOB.items() if k not in ("content", "departments")},
                    {"id": 102, "title": "Senior Software Engineer", "company_name": "Acme", "absolute_url": "u",
                     "location": {"name": "Remote"}, "first_published": "2026-10-10T10:00:00-04:00"}]}
SAMPLES = {
    "boards-api.greenhouse.io/v1/boards/acme/jobs/101": GH_JOB,
    "boards-api.greenhouse.io": GH_LIST,
    "api.lever.co": [{
        "id": "6ed76ce8-4156-4b60-b120-403538bd66cd", "text": "Software Engineer", "categories": {"location": "New York, NY", "team": "Eng"},
        "workplaceType": "hybrid", "hostedUrl": "https://jobs.lever.co/acme/6ed76ce8-4156-4b60-b120-403538bd66cd",
        "applyUrl": "https://jobs.lever.co/acme/6ed76ce8-4156-4b60-b120-403538bd66cd/apply", "descriptionPlain": "Build things",
        "lists": [{"text": "You have", "content": "<li>Python</li>"}], "createdAt": 1786469891368,
        "salaryRange": {"min": 150000, "max": 200000, "currency": "USD", "interval": "per-year-salary"}}],
    "api.ashbyhq.com": {"jobs": [{
        "id": "34413f8d-26bf-4bbc-8ade-eb309a0e2245", "title": " Security Engineer ", "location": "New York, NY",
        "isRemote": True, "jobUrl": "https://jobs.ashbyhq.com/acme/34413f8d-26bf-4bbc-8ade-eb309a0e2245",
        "applyUrl": "https://jobs.ashbyhq.com/acme/34413f8d-26bf-4bbc-8ade-eb309a0e2245/application",
        "descriptionPlain": "Secure things", "publishedAt": "2026-04-07T17:12:35.753+00:00", "isListed": True,
        "compensation": {"scrapeableCompensationSalarySummary": "$211.4K - $290.6K"}}]},
    "remotive.com": {"jobs": [{"id": 5, "url": "https://remotive.com/remote-jobs/x-5", "title": "Python Developer",
                               "company_name": "Beta", "candidate_required_location": "USA", "salary": "$170k - $200k",
                               "description": "<p>Hi</p>", "publication_date": "2026-10-14T20:33:44", "tags": ["python"]}]},
    "remoteok.com": [{"legal": "terms"}, {"id": "9", "position": "Go Engineer", "company": "Gamma", "url": "https://remoteok.com/remote-jobs/9",
                      "apply_url": "https://remoteok.com/l/9", "description": "Go", "date": "2026-10-15T08:00:17+00:00",
                      "salary_min": 100000, "salary_max": 140000, "tags": ["go"]}],
}


def fake_get_json(url, params=None, **kw):
    for host, data in SAMPLES.items():
        if host in url:
            return data
    raise http.FetchError("no sample")


class SourceParserTests(unittest.TestCase):
    def setUp(self):
        self.patch = mock.patch.object(http, "get_json", side_effect=fake_get_json)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_greenhouse(self):
        [j] = sources.REGISTRY["greenhouse"].fetch("acme", {"field": "business", "job_types": ["full_time"]})
        self.assertEqual(j["id"], "greenhouse:acme:101")
        self.assertEqual(j["ats"], "greenhouse")
        self.assertEqual(j["apply_url"], "https://job-boards.greenhouse.io/embed/job_app?for=acme&token=101")
        self.assertEqual(j["description"], "Python & Go")
        self.assertEqual(j["categories"], ["Finance"])
        self.assertTrue(j["remote"])
        self.assertTrue(j["posted_at"].startswith("2026-10-10T14:00"))

    def test_greenhouse_vague_location_uses_offices(self):
        from jobbot.sources import greenhouse
        j = greenhouse._job("acme", {"id": 1, "title": "BDR", "location": {"name": "Hybrid"}, "content": "",
                                     "offices": [{"name": "Dubai, United Arab Emirates"}]})
        self.assertEqual(j["location"], "Hybrid · Dubai, United Arab Emirates")
        same = greenhouse._job("acme", {"id": 2, "title": "BDR", "location": {"name": "United States"}, "content": "",
                                        "offices": [{"name": "United States"}]})
        self.assertEqual(same["location"], "United States")

    def test_greenhouse_only_fetches_details_for_new_matching_jobs(self):
        gh = sources.REGISTRY["greenhouse"]
        self.assertEqual(gh.fetch("acme", {"field": "business", "job_types": ["full_time"]}, known={"greenhouse:acme:101"}), [])
        urls = [c.args[0] for c in http.get_json.call_args_list]
        self.assertNotIn("https://boards-api.greenhouse.io/v1/boards/acme/jobs/102", urls)  # engineer: never detailed

    def test_lever(self):
        [j] = sources.REGISTRY["lever"].fetch("acme", {})
        self.assertEqual((j["company"], j["ats"], j["salary_min"]), ("Acme", "lever", 150000))
        self.assertIn("Python", j["description"])
        self.assertTrue(j["apply_url"].endswith("/apply"))

    def test_ashby(self):
        [j] = sources.REGISTRY["ashby"].fetch("acme", {})
        self.assertEqual(j["title"], "Security Engineer")
        self.assertEqual((j["salary_min"], j["salary_max"]), (211400, 290600))

    def test_remotive(self):
        [j] = sources.REGISTRY["remotive"].fetch("python", {})
        self.assertEqual((j["id"], j["remote"], j["salary_min"], j["salary_max"]), ("remotive:5", True, 170000, 200000))

    def test_remoteok_skips_legal_row(self):
        jobs = sources.REGISTRY["remoteok"].fetch("latest", {})
        self.assertEqual([j["title"] for j in jobs], ["Go Engineer"])
        self.assertEqual(jobs[0]["apply_url"], "https://remoteok.com/l/9")

    def test_dedupe_key_ignores_company_suffixes(self):
        a = sources.make_job("x", 1, "Backend Engineer", "Acme, Inc.", "u")
        b = sources.make_job("y", 2, "Backend  Engineer", "ACME", "v")
        self.assertEqual(a["dedupe_key"], b["dedupe_key"])


class FieldAwareKeysTests(unittest.TestCase):
    BUSINESS = {"field": "business", "families": ["finance", "marketing"], "keywords": [], "locations": ["Remote"],
                "job_types": ["full_time"]}

    def test_keyword_boards_use_business_areas(self):
        self.assertEqual(sources.REGISTRY["jobicy"].keys(self.BUSINESS), ["industry:accounting-finance", "industry:marketing"])
        self.assertEqual(sources.REGISTRY["himalayas"].keys(self.BUSINESS), ["financial analyst", "accountant", "marketing"])
        self.assertEqual(sources.REGISTRY["remotive"].keys(self.BUSINESS), ["latest"])

    def test_titles_you_list_win(self):
        s = dict(self.BUSINESS, keywords=["Brand Manager"])
        self.assertEqual(sources.REGISTRY["jobicy"].keys(s), ["tag:Brand Manager"])
        self.assertEqual(sources.REGISTRY["himalayas"].keys(s), ["Brand Manager"])

    def test_internship_mode_queries(self):
        s = dict(self.BUSINESS, job_types=["internship"])
        self.assertEqual(sources.REGISTRY["jobicy"].keys(s), ["tag:internship"])
        self.assertEqual(sources.REGISTRY["himalayas"].keys(s), ["finance intern", "accounting intern", "marketing intern"])
        with mock.patch.object(http, "get_json", return_value={"results": [], "page_count": 1}) as get:
            sources.REGISTRY["themuse"].fetch("Flexible / Remote", s)
        self.assertEqual(get.call_args.args[1]["level"], "Internship")
        both = dict(s, job_types=["internship", "full_time"])
        self.assertEqual(sources.REGISTRY["jobicy"].keys(both), ["tag:internship", "industry:accounting-finance", "industry:marketing"])

    def test_muse_sends_business_categories(self):
        with mock.patch.object(http, "get_json", return_value={"results": [], "page_count": 1}) as get:
            sources.REGISTRY["themuse"].fetch("Flexible / Remote", self.BUSINESS)
        self.assertEqual(get.call_args.args[1]["category"], ["Accounting and Finance", "Advertising and Marketing"])


class AtsTests(unittest.TestCase):
    def test_detect_and_form_urls(self):
        cases = {
            "https://boards.greenhouse.io/airbnb/jobs/123": ("greenhouse", "airbnb", "123"),
            "https://job-boards.greenhouse.io/embed/job_app?for=stripe&token=8172510": ("greenhouse", "stripe", "8172510"),
            "https://jobs.lever.co/palantir/a237973c-cb29-41fe-9c80-416e6f42e087/apply": ("lever", "palantir", "a237973c-cb29-41fe-9c80-416e6f42e087"),
            "https://jobs.ashbyhq.com/ramp/34413f8d-26bf-4bbc-8ade-eb309a0e2245": ("ashby", "ramp", "34413f8d-26bf-4bbc-8ade-eb309a0e2245"),
        }
        for url, want in cases.items():
            self.assertEqual(ats.detect(url)[:3], want)
        self.assertEqual(ats.detect("https://example.com/careers")[0], None)
        self.assertEqual(ats.form_url("lever", "acme", "abc"), "https://jobs.lever.co/acme/abc/apply")
        self.assertEqual(ats.form_url("ashby", "acme", "abc"), "https://jobs.ashbyhq.com/acme/abc/application")

    def test_resolve_from_listing_page(self):
        page = '<a href="https://jobs.lever.co/acme/6ed76ce8-4156-4b60-b120-403538bd66cd">Apply for this job</a>'
        with mock.patch.object(http, "get_html", return_value=("https://board.example/job/1", page)):
            out = ats.resolve({"url": "https://board.example/job/1"})
        self.assertEqual(out["ats"], "lever")
        self.assertTrue(out["apply_url"].endswith("/apply"))

    def test_resolve_job_board_link_to_the_employers_posting(self):
        from jobbot import finder
        info = {"title": "Supply Chain Intern", "company": "Acme", "location": "Houston, TX", "website": ""}
        wd = "https://acme.wd1.myworkdayjobs.com/Careers/job/Houston/Supply-Chain-Intern_R1"
        with mock.patch.object(finder, "details", return_value=info), mock.patch.object(finder, "find", return_value=wd):
            out = ats.resolve({"url": "https://www.linkedin.com/jobs/view/4464168018", "title": "Job at linkedin.com"})
        self.assertEqual((out["ats"], out["apply_url"], out["title"], out["company"]), ("account", wd, "Supply Chain Intern", "Acme"))
        with mock.patch.object(finder, "details", return_value=info), mock.patch.object(finder, "find", return_value=None):
            out = ats.resolve({"url": "https://www.indeed.com/viewjob?jk=abc", "title": "Supply Chain Intern"})
        self.assertEqual(out["ats"], "manual")
        self.assertNotIn("title", out)  # a job that already has its name keeps it

    def test_resolve_finds_the_icims_posting_behind_a_careers_page(self):
        page = '<button>Apply</button><script>var u = "https://careers-acme.icims.com/jobs/login?loginOnly=1";' \
               'var a = "https://careers-acme.icims.com/jobs/54808/login";</script>'
        with mock.patch.object(http, "get_html", return_value=("https://jobs.acme.com/external/jobs/54808", page)):
            out = ats.resolve({"url": "https://jobs.acme.com/external/jobs/54808"})
        self.assertEqual(out, {"ats": "account", "apply_url": "https://careers-acme.icims.com/jobs/54808/login"})

    def test_resolve_sign_in_sites(self):
        for url in ("https://careers-acme.icims.com/jobs/1234/intern/job", "https://career4.successfactors.com/career?company=acme",
                    "https://acme.wd5.myworkdayjobs.com/External/job/X_R1"):
            self.assertEqual(ats.resolve({"url": url})["ats"], "account", url)


if __name__ == "__main__":
    unittest.main()
