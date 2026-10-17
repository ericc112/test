import io
import unittest
import urllib.error
from datetime import datetime, timezone
from unittest import mock

from jobbot import db, pipeline, sources
from jobbot.sources import amazon, http, jibe, make_job, oracle, phenom, successfactors, workday

from .helpers import PROFILE, TempData


class Resp(io.BytesIO):
    def __init__(self, body, etag=None, url="https://x"):
        super().__init__(body)
        self.headers = {"ETag": etag} if etag else {}
        self._url = url

    def geturl(self):
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class ConditionalRequestTests(unittest.TestCase):
    def tearDown(self):
        http.forget_etags()

    def test_etag_round_trip(self):
        seen_headers = []

        def urlopen(req, timeout=None):
            seen_headers.append(dict(req.header_items()))
            if len(seen_headers) == 1:
                return Resp(b'{"jobs": []}', etag='W/"abc"')
            raise urllib.error.HTTPError(req.full_url, 304, "Not Modified", {}, None)

        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            self.assertEqual(http.get_json("https://b/jobs", conditional=True), {"jobs": []})
            with self.assertRaises(http.NotModified):
                http.get_json("https://b/jobs", conditional=True)
        self.assertNotIn("If-none-match", seen_headers[0])
        self.assertEqual(seen_headers[1]["If-none-match"], 'W/"abc"')


def wd_page(ids, posted="Posted Today"):
    return {"total": 500, "jobPostings": [
        {"title": t, "externalPath": f"/job/NYC/{i}", "locationsText": "New York, NY", "postedOn": posted, "bulletFields": [i]}
        for i, t in ids]}


class WorkdayTests(unittest.TestCase):
    KEY = "acme|wd5|Careers"
    SEARCH = {"field": "business", "job_types": ["full_time"]}

    def setUp(self):
        workday._looked_at.clear()

    def test_posted_text(self):
        now = datetime(2026, 10, 16, 15, tzinfo=timezone.utc)
        self.assertTrue(workday.posted_from_text("Posted Today", now).startswith("2026-10-16"))
        self.assertTrue(workday.posted_from_text("Posted Yesterday", now).startswith("2026-10-15"))
        self.assertTrue(workday.posted_from_text("Posted 3 Days Ago", now).startswith("2026-10-13"))
        self.assertTrue(workday.posted_from_text("Posted 30+ Days Ago", now).startswith("2026-09-16"))
        self.assertEqual(workday.key_from_url("https://citi.wd5.myworkdayjobs.com/en-US/2/job/x"), "citi|wd5|2")

    def test_fetch_new_business_jobs_with_details(self):
        page = wd_page([("R1", "Financial Analyst"), ("R2", "Software Engineer")])
        page["jobPostings"] += page["jobPostings"][:1] * 0
        detail = {"jobPostingInfo": {"jobDescription": "<p>Excel</p>", "startDate": "2026-10-16",
                                     "location": "New York, NY", "externalUrl": "https://acme.wd5.myworkdayjobs.com/Careers/job/NYC/R1"}}
        with mock.patch.object(http, "post_json", return_value=page) as post, \
             mock.patch.object(http, "get_json", return_value=detail) as get:
            jobs = workday.fetch(self.KEY, self.SEARCH)
        self.assertEqual([j["title"] for j in jobs], ["Financial Analyst"])
        j = jobs[0]
        self.assertEqual((j["id"], j["ats"], j["description"]), ("workday:acme:R1", "manual", "Excel"))
        self.assertEqual(get.call_count, 1)  # the engineer never got a detail request
        self.assertEqual(post.call_count, 1)  # short page: no more pages

    def test_keys_per_job_type(self):
        s = {"companies": {"workday": ["acme|wd5|Careers"]}}
        self.assertEqual(workday.keys(dict(s, job_types=["internship"])), ["acme|wd5|Careers#intern"])
        self.assertEqual(workday.keys(dict(s, job_types=["internship", "full_time"])),
                         ["acme|wd5|Careers", "acme|wd5|Careers#intern"])
        self.assertEqual(workday.id_prefix("acme|wd5|Careers#intern"), "workday:acme:")

    def test_intern_feed_uses_the_sites_intern_filter(self):
        workday._intern_facets.clear()
        facets = {"facets": [
            {"facetParameter": "locations", "values": [{"id": "L1", "descriptor": "Summerville, SC"}]},
            {"facetParameter": "jobFamilyGroup", "values": [{"id": "F1", "descriptor": "Internal Audit"}]},
            {"facetParameter": "workerSubType", "values": [{"id": "W1", "descriptor": "Intern (Fixed Term)"},
                                                            {"id": "W2", "descriptor": "Regular"}]}],
            "jobPostings": []}
        interns = wd_page([("R7", "Corporate Banking Summer Program")])
        bodies = []

        def post(url, body, **kw):
            bodies.append(body)
            return facets if body["limit"] == 1 else interns

        with mock.patch.object(http, "post_json", side_effect=post), \
             mock.patch.object(http, "get_json", return_value={"jobPostingInfo": {}}):
            jobs = workday.fetch("acme|wd5|Careers#intern", {"field": "business", "job_types": ["internship"]})
        self.assertEqual(bodies[1]["appliedFacets"], {"workerSubType": ["W1"]})
        self.assertEqual([j["title"] for j in jobs], ["Corporate Banking Summer Program"])
        self.assertIn("Internship", jobs[0]["tags"])

    def test_intern_feed_without_an_intern_filter_searches_for_interns(self):
        workday._intern_facets.clear()
        bodies = []

        def post(url, body, **kw):
            bodies.append(body)
            return {"facets": [], "jobPostings": []} if body["limit"] == 1 else wd_page([("R9", "Finance Intern")])

        with mock.patch.object(http, "post_json", side_effect=post), \
             mock.patch.object(http, "get_json", return_value={"jobPostingInfo": {}}):
            jobs = workday.fetch("acme|wd5|Careers#intern", {"field": "business", "job_types": ["internship"]})
        self.assertEqual(bodies[1]["searchText"], "intern")
        self.assertEqual([j["title"] for j in jobs], ["Finance Intern"])

    def test_paging_stops_once_caught_up(self):
        full = wd_page([(f"R{i}", "Financial Analyst") for i in range(20)])
        known = {f"workday:acme:R{i}" for i in range(20)}
        with mock.patch.object(http, "post_json", return_value=full) as post, \
             mock.patch.object(http, "get_json", return_value={"jobPostingInfo": {}}):
            self.assertEqual(workday.fetch(self.KEY, self.SEARCH, known=known), [])
        self.assertEqual(post.call_count, 1)


def orc_page(rows, total=3674):
    return {"items": [{"TotalJobsCount": total, "requisitionList": [
        {"Id": i, "Title": t, "PostedDate": "2026-10-01", "PrimaryLocation": loc, "WorkplaceType": "",
         "ShortDescriptionStr": "Short", "secondaryLocations": []} for i, t, loc in rows]}]}


class OracleTests(unittest.TestCase):
    KEY = "jpmc.fa.oraclecloud.com|CX_1001"

    def setUp(self):
        oracle._looked_at.clear()

    def test_keys_and_urls(self):
        s = {"companies": {"oracle": [self.KEY]}}
        self.assertEqual(oracle.keys(dict(s, job_types=["internship"])), [self.KEY + "#intern"])
        self.assertEqual(oracle.id_prefix(self.KEY + "#intern"), "oracle:jpmc:")
        self.assertEqual(oracle.key_from_url("https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs"), self.KEY)

    def test_intern_feed_searches_by_relevance_and_keeps_business_internships(self):
        page = orc_page([("1", "2027 Global Finance & Business Management - Summer Analyst", "New York, NY, United States"),
                         ("2", "Software Engineer Intern", "Plano, TX, United States"),
                         ("3", "Credit Trading - Analyst", "New York, NY, United States")])
        detail = {"items": [{"ExternalDescriptionStr": "<p>Pay: $50 per hour</p>"}]}
        calls = []

        def get_json(url, params=None, **kw):
            calls.append((url, params))
            return detail if "Details" in url else page

        with mock.patch.object(http, "get_json", side_effect=get_json):
            jobs = oracle.fetch(self.KEY + "#intern", {"field": "business", "job_types": ["internship"]})
        self.assertEqual([j["title"] for j in jobs], ["2027 Global Finance & Business Management - Summer Analyst"])
        j = jobs[0]
        self.assertEqual(j["id"], "oracle:jpmc:1")
        self.assertEqual(j["url"], "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/1")
        self.assertIn("Pay: $50 per hour", j["description"])
        self.assertIn('keyword="intern"', calls[0][1]["finder"])
        self.assertIn("sortBy=RELEVANCY", calls[0][1]["finder"])


class AmazonTests(unittest.TestCase):
    def test_us_business_internships_from_amazon_jobs(self):
        page = {"hits": 3, "jobs": [
            {"id_icims": "1", "title": "Supply Chain Manager Intern - Summer 2027", "job_path": "/en/jobs/1/x",
             "normalized_location": "Seattle, Washington, USA", "posted_date": "October  9, 2026", "is_intern": True,
             "description": "Plan inventory.", "job_category": "Supply Chain/Transportation Management"},
            {"id_icims": "2", "title": "2027 Applied Science Internship - United States, PhD Student Science Recruiting",
             "job_path": "/en/jobs/2/y", "normalized_location": "Seattle, Washington, USA", "posted_date": "October 9, 2026",
             "is_intern": True, "job_category": "Research Science", "business_category": "studentprograms"},
            {"id_icims": "3", "title": "Sourcing Recruiter Intern – Summer 2027", "job_path": "/en/jobs/3/z",
             "normalized_location": "Seattle, Washington, USA", "posted_date": "October 9, 2026", "is_intern": True}]}
        seen = []
        with mock.patch.object(http, "get_json", side_effect=lambda url, params=None, **kw: seen.append(params) or page):
            jobs = amazon.fetch("amazon#intern", {"field": "business", "job_types": ["internship"],
                                                  "locations": ["Remote", "United States"]})
        self.assertEqual([j["title"] for j in jobs], ["Supply Chain Manager Intern - Summer 2027", "Sourcing Recruiter Intern – Summer 2027"])
        self.assertEqual((jobs[0]["id"], jobs[0]["url"]), ("amazon:1", "https://www.amazon.jobs/en/jobs/1/x"))
        self.assertTrue(jobs[0]["posted_at"].startswith("2026-10-09"))
        self.assertEqual((seen[0]["base_query"], seen[0]["country"]), ("intern", "USA"))
        self.assertEqual(amazon.keys({"companies": {"amazon": ["amazon"]}, "job_types": ["internship"]}), ["amazon#intern"])


SEARCH = {"field": "business", "job_types": ["internship"]}


class JibeTests(unittest.TestCase):
    def test_reads_the_api_and_keeps_business_internships(self):
        def post(slug, title, kind="INTERN"):
            return {"data": {"slug": slug, "req_id": slug, "language": "en-us", "title": title, "description": "Paid: $22 per hour.",
                             "full_location": "Bloomington, Illinois", "country": "United States", "employment_type": kind,
                             "posted_date": "2026-10-15T14:00:00+0000", "hiring_organization": "State Farm",
                             "meta_data": {"canonical_url": f"https://jobs.statefarm.com/jobs/{slug}?lang=en-us"}}}
        page = {"totalCount": 2, "jobs": [post("46413", "Summer 2027 Intern - Marketing"), post("1", "Software Engineer Intern")]}
        seen = []
        with mock.patch.object(http, "get_json", side_effect=lambda url, params=None, **kw: seen.append((url, params)) or page):
            jobs = jibe.fetch("jobs.statefarm.com#intern", SEARCH)
        self.assertEqual([j["title"] for j in jobs], ["Summer 2027 Intern - Marketing"])
        j = jobs[0]
        self.assertEqual((j["id"], j["company"]), ("jibe:jobs.statefarm.com:46413", "State Farm"))
        self.assertEqual(j["url"], "https://jobs.statefarm.com/jobs/46413?lang=en-us")
        self.assertEqual(j["location"], "Bloomington, Illinois, United States")
        self.assertTrue(j["posted_at"].startswith("2026-10-15T14:00"))
        self.assertEqual(seen[0][0], "https://jobs.statefarm.com/api/jobs")
        self.assertEqual((seen[0][1]["keywords"], seen[0][1]["sortBy"]), ("intern", "posted_date"))
        self.assertEqual(jibe.keys({"companies": {"jibe": ["jobs.statefarm.com", "not a host"]}, "job_types": ["internship"]}),
                         ["jobs.statefarm.com#intern"])


def sf_table(rows, total):
    body = "".join(f"""<tr class="data-row"><td class="colTitle"><span class="jobTitle hidden-phone">
        <a href="{path}" class="jobTitle-link">{title}</a></span></td>
        <td class="colLocation"><span class="jobLocation"> {loc} </span></td>
        <td class="colDate"><span class="jobDate">Oct 16, 2026
        </span></td></tr>""" for path, title, loc in rows)
    return f'<span class="paginationLabel">Results <b>1 – {len(rows)}</b> of <b>{total}</b></span><table><tbody>{body}</tbody></table>'


class SuccessFactorsTests(unittest.TestCase):
    def test_table_layout_with_a_path_prefix(self):
        rows, total = successfactors.parse_results(sf_table(
            [("/eightfold/job/Moline-2027-Intern-Finance-IL-61265/1431021000/", "2027 Intern - Finance &amp; Accounting", "Moline, IL, US, 61265")], 14))
        self.assertEqual(total, 14)
        self.assertEqual(rows, [{"path": "/eightfold/job/Moline-2027-Intern-Finance-IL-61265/1431021000/",
                                 "title": "2027 Intern - Finance & Accounting", "location": "Moline, IL, US, 61265",
                                 "posted_at": "2026-10-16T00:00:00+00:00"}])

    def test_tile_layout(self):
        tile = """<li class="job-tile job-id-1389579300" data-url="/job/Denver-Marketing-Intern-CO-80203/1389579300/">
            <a class="jobTitle-link fontcolor7222" data-focus-tile=".job-id-1389579300" href="/job/Denver-Marketing-Intern-CO-80203/1389579300/"> Marketing Intern </a>
            <div id="job-1389579300-desktop-section-location-value">Denver, CO, US, 80203</div>
            <ul><li>nested</li></ul>
            <div id="job-1389579300-desktop-section-date-value">Oct 16, 2026</div></li>"""
        rows, total = successfactors.parse_results("<ul>" + tile * 2 + "</ul>")
        self.assertIsNone(total)  # tile pages don't print a count
        self.assertEqual(len(rows), 2)
        self.assertEqual((rows[0]["title"], rows[0]["location"], rows[0]["posted_at"]),
                         ("Marketing Intern", "Denver, CO, US, 80203", "2026-10-16T00:00:00+00:00"))

    def test_no_results_page_is_empty_not_the_newest_jobs(self):
        page = '<div id="noresults">There are currently no open positions.</div>' + sf_table([("/job/x/1/", "Mining Technician", "Bagdad, AZ, US")], 10)
        with mock.patch.object(http, "get", return_value=("u", page)):
            self.assertEqual(successfactors._search("jobs.example.com", True), ([], 0))

    def test_fetch_opens_matching_postings_only(self):
        listing = sf_table([("/job/Inver-Grove-Heights-Supply-Chain-Intern-MN/1431172000/", "Supply Chain Intern", "Inver Grove Heights, MN, US"),
                            ("/job/Grand-Forks-Agronomy-Intern-ND/1420999400/", "Crop Science Research Intern", "Grand Forks, ND, US")], 2)
        detail = ('<meta itemprop="datePosted" content="Fri Oct 16 07:00:00 UTC 2026">'
                  '<span itemprop="description"><span class="jobdescription"><p>Plan freight. $21 per hour.</p></span></span>')
        urls = []

        def get(url, params=None, **kw):
            urls.append(url)
            return url, detail if "/job/" in url else listing

        with mock.patch.object(http, "get", side_effect=get):
            jobs = successfactors.fetch("careers.chsinc.com#intern", SEARCH)
        self.assertEqual([j["title"] for j in jobs], ["Supply Chain Intern"])
        j = jobs[0]
        self.assertEqual(j["id"], "successfactors:careers.chsinc.com:1431172000")
        self.assertIn("$21 per hour", j["description"])
        self.assertEqual(j["posted_at"], "2026-10-16T07:00:00+00:00")
        self.assertEqual(sum("/job/" in u for u in urls), 1)  # the research posting was never opened


class PhenomTests(unittest.TestCase):
    KEY = "careers.molsoncoors.com/us/en"

    def test_reads_the_search_service(self):
        hits = {"refineSearch": {"status": 200, "totalHits": 2, "data": {"jobs": [
            {"jobId": "40096", "title": "Finance Intern", "type": "Student/Intern", "cityStateCountry": "Milwaukee, US-WI, United States",
             "postedDate": "2026-10-16T16:42:36.451+0000", "descriptionTeaser": "Support our FP&A team.", "multi_category": ["Finance"]},
            {"jobId": "39744", "title": "Brewery Operations Intern - Packaging", "type": "Student/Intern",
             "cityStateCountry": "Fort Worth, US-TX, United States", "postedDate": "2026-10-16T16:42:36.451+0000"}]}}}
        job_page = 'phApp.ddo = {"jobDetail": {"data": {"job": {"description": "<p>Pay: $24 per hour</p>"}}}}; phApp.x = 1;'
        sent = []
        with mock.patch.object(http, "post_json", side_effect=lambda url, payload, **kw: sent.append((url, payload)) or hits), \
             mock.patch.object(http, "get", return_value=("u", job_page)):
            jobs = phenom.fetch(self.KEY + "#intern", SEARCH)
        titles = [j["title"] for j in jobs]
        self.assertIn("Finance Intern", titles)
        j = jobs[titles.index("Finance Intern")]
        self.assertEqual((j["id"], j["url"]), ("phenom:careers.molsoncoors.com:40096", "https://careers.molsoncoors.com/us/en/job/40096"))
        self.assertIn("$24 per hour", j["description"])
        self.assertEqual(sent[0][0], "https://careers.molsoncoors.com/widgets")
        self.assertEqual((sent[0][1]["keywords"], sent[0][1]["lang"], sent[0][1]["country"]), ("intern", "en_us", "us"))
        self.assertEqual(phenom.keys({"companies": {"phenom": [self.KEY, "careers.example.com"]}, "job_types": ["internship"]}),
                         [self.KEY + "#intern"])


class CompanyNameTests(unittest.TestCase):
    def test_first_listed_name_wins_for_a_shared_tenant(self):
        from jobbot import config
        with mock.patch.object(config, "SUGGESTED_COMPANIES", [("Morgan Stanley", "workday", "ms|wd5|External"),
                                                                ("Moody's", "workday", "ms|wd5|private")]):
            names = sources.suggested_names("workday", lambda slug: slug.split("|")[0])
        self.assertEqual(names, {"ms": "Morgan Stanley"})


class WatcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TempData()
        db.set_setting("profile", PROFILE)
        s = db.get_setting("search")
        s.update(sources={n: n == "greenhouse" for n in sources.REGISTRY}, locations=["Remote"], job_types=["full_time"],
                 companies={"greenhouse": ["acme"], "lever": [], "ashby": [], "workday": []})
        db.set_setting("search", s)
        db.set_setting("automation", dict(db.get_setting("automation"), watch_minutes=5, prepare_min_score=10))
        self.queued = []
        self.watcher = pipeline.Watcher(lambda job_id, action: self.queued.append((job_id, action)))
        pipeline._filtered_out.clear()

    def tearDown(self):
        self.tmp.close()

    def job(self, n, title="Financial Analyst"):
        return make_job("greenhouse", f"acme:{n}", title, "Acme", f"https://acme/{n}", ats="greenhouse",
                        ats_board="acme", ats_job_id=str(n), remote=True, location="Remote",
                        posted_at=db.now(), description="Excel modeling", categories=["Finance"])

    def tick(self, result):
        self.watcher.last_poll.clear()  # make every board due
        gh = sources.REGISTRY["greenhouse"]
        kw = {"side_effect": result} if isinstance(result, Exception) else {"return_value": result}
        with mock.patch.object(gh, "fetch", **kw) as fetch:
            fresh = self.watcher.tick()
        return fresh, fetch

    def test_first_look_is_backfill_then_new_postings_are_fresh(self):
        fresh, _ = self.tick([self.job(1)])
        self.assertEqual(fresh, [])
        self.assertEqual(db.get_job("greenhouse:acme:1")["fresh"], 0)
        self.assertEqual(self.queued, [])

        fresh, fetch = self.tick([self.job(2), self.job(3, "Software Engineer")])
        self.assertEqual([j["id"] for j in fresh], ["greenhouse:acme:2"])
        self.assertEqual(db.get_job("greenhouse:acme:2")["fresh"], 1)
        self.assertIn("greenhouse:acme:1", fetch.call_args.kwargs["known"])
        self.assertEqual(self.queued, [("greenhouse:acme:2", "prepare")])  # filled right away
        events = [e["message"] for e in db.recent_events()]
        self.assertTrue(any(m.startswith("Just posted at Acme: Financial Analyst") for m in events))
        self.assertEqual(db.fresh_jobs()[1], 1)

    def test_unchanged_board_costs_nothing(self):
        self.tick([self.job(1)])
        fresh, _ = self.tick(http.NotModified("u"))
        self.assertEqual(fresh, [])
        self.assertTrue(db.last_source_run("greenhouse", "acme")["ok"])

    def test_boards_are_not_polled_again_before_interval(self):
        self.tick([self.job(1)])
        with mock.patch.object(sources.REGISTRY["greenhouse"], "fetch", return_value=[]) as fetch:
            self.watcher.tick()
        fetch.assert_not_called()

    def test_failures_are_logged_once(self):
        self.tick(http.FetchError("HTTP 500"))
        self.tick(http.FetchError("HTTP 500"))
        warnings = [e for e in db.recent_events() if "Watching greenhouse" in e["message"]]
        self.assertEqual(len(warnings), 1)

    def test_changing_the_search_re_evaluates_filtered_jobs(self):
        self.tick([self.job(1)])
        self.tick([self.job(2, "Software Engineer")])  # filtered out, remembered
        self.assertIn("greenhouse:acme:2", pipeline._filtered_out)
        pipeline.search_changed()
        self.assertNotIn("greenhouse:acme:2", pipeline._filtered_out)
        self.assertEqual(db.last_source_run("greenhouse", "acme")["count"], 1)  # board total, not just new ones

    def test_big_watch_lists_are_spread_over_the_interval(self):
        s = db.get_setting("search")
        s["companies"]["greenhouse"] = [f"co{i}" for i in range(450)]
        db.set_setting("search", s)
        polled = []
        with mock.patch.object(pipeline, "poll_feed", side_effect=lambda n, k, *a: polled.append(k) or {"jobs": [], "fresh": []}):
            self.watcher.tick()
        self.assertEqual(len(polled), 30)  # 450 boards every 5 min: 30 per 20 s tick
        self.assertEqual(self.watcher.status["interval_min"], 5.0)

    def test_watch_can_be_turned_off(self):
        db.set_setting("automation", dict(db.get_setting("automation"), watch_enabled=False))
        _, fetch = self.tick([self.job(1)])
        fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
