"""Drive a real browser through an application form.

prepare: open the form, fill everything we can, screenshot, never submit.
submit:  fill again (using the answers you reviewed), press Submit, and check
         for a confirmation, a CAPTCHA, or validation errors.

With headless off you can watch it work. If it gets stuck on a CAPTCHA or a
question only you can answer, it waits for you to finish in that window.
"""
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .. import ats, config
from ..answers import AI_POLICY, Question, answer_all, as_dict, missing
from ..textutil import norm, pick_option

EXTRACT_JS = (Path(__file__).with_name("extract.js")).read_text()

SUBMIT_RE = re.compile(r"^(submit|submit application|submit your application|apply|apply now|send application|send)$", re.I)
APPLY_LINK_RE = re.compile(r"^(apply|apply now|apply for this (job|position|role)|i'?m interested|start application)$", re.I)
COOKIE_REJECT_RE = re.compile(r"^(reject|reject all|decline|deny|necessary only|only necessary)", re.I)
COOKIE_ACCEPT_RE = re.compile(r"^(accept|accept all|allow all|agree|got it|ok|i understand)", re.I)


@dataclass
class Result:
    result: str  # ready | needs_input | blocked | manual | applied | unconfirmed | error
    message: str = ""
    fields: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    screenshot: str = None
    url: str = None


class Engine:
    def __init__(self, headless=True, assist_timeout_min=10, slow_mo=0, log=None):
        self.headless = headless
        self.assist_timeout = max(1, int(assist_timeout_min)) * 60
        self.slow_mo = slow_mo
        self.log = log or (lambda msg: None)
        self.found_ats = None  # set when an Apply link led to a Greenhouse/Lever/Ashby form

    # ------------------------------------------------------------ public API
    def run(self, job, ctx, mode="prepare"):
        self.mode = mode
        from playwright.sync_api import Error as PWError
        from playwright.sync_api import sync_playwright

        url = job.get("apply_url") or job.get("url")
        if not url:
            return Result("manual", "No application link for this job.")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless, slow_mo=self.slow_mo)
            try:
                context = browser.new_context(
                    user_agent=config.USER_AGENT, viewport={"width": 1280, "height": 1000}, locale="en-US",
                )
                page = context.new_page()
                page.set_default_timeout(15000)
                try:
                    return self._run(page, job, ctx, url, mode)
                except PWError as e:
                    shot = self._shot(page, job, "error")
                    return Result("error", f"Browser error: {str(e).splitlines()[0][:300]}", screenshot=shot, url=page.url)
            finally:
                browser.close()

    # ------------------------------------------------------------ steps
    def _run(self, page, job, ctx, url, mode):
        self.log(f"Opening {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        self._settle(page)
        self._dismiss_cookies(page)
        data = self._extract(page)
        if data["page"]["botwall"]:
            return Result("manual", "This site shows a bot check, so JobBot stops here. Open the listing and apply yourself.",
                          screenshot=self._shot(page, job, "botcheck"), url=page.url)
        if len([q for q in data["questions"] if q["kind"] != "file"]) < 2:
            page = self._click_apply(page)
            self._goto_ats_form(page)
            self._dismiss_cookies(page)
            data = self._extract(page)
            if data["page"]["botwall"]:
                return Result("manual", "The application site shows a bot check, so JobBot stops here. Apply there yourself.",
                              screenshot=self._shot(page, job, "botcheck"), url=page.url)
        if data["page"]["login"] and len(data["questions"]) < 4:
            return Result("manual", "This site wants you to sign in first. Apply on the site directly.",
                          screenshot=self._shot(page, job, "login"), url=page.url)
        if not data["questions"]:
            return Result("manual", "Couldn't find an application form on this page.",
                          screenshot=self._shot(page, job, "noform"), url=page.url)

        questions, answers = [], {}
        notes = []
        if ctx.llm is not None and any(AI_POLICY.search(q.get("label") or "") for q in data["questions"]):
            ctx.llm = None
            notes.append("AI answers were turned off because this employer restricts AI use.")
        for pass_no in range(3):
            new_qs = [Question(**q) for q in data["questions"] if q["key"] not in answers]
            if not new_qs:
                break
            try:
                new_answers = answer_all(new_qs, ctx)
            except Exception as e:  # AI failures shouldn't sink the whole application
                notes.append(str(e))
                ctx_llm, ctx.llm = ctx.llm, None
                new_answers = answer_all(new_qs, ctx)
                ctx.llm = ctx_llm
            # Files first: resume parsers on Lever/Ashby autofill fields we then overwrite.
            ordered = sorted(new_qs, key=lambda q: q.kind != "file")
            for q in ordered:
                a = new_answers[q.key]
                if not a.resolved(q):
                    if q.kind == "combobox" and q.required:
                        self._probe_options(page, q)  # so the review screen can offer a dropdown
                    continue
                if self._fill(page, q, a):
                    if q.kind == "file" and self.mode == "submit":
                        page.wait_for_timeout(2500)  # let resume parsers autofill before we overwrite
                else:
                    a.failed = True
                    a.note = a.note or "Couldn't enter this answer automatically"
            questions += new_qs
            answers.update(new_answers)
            page.wait_for_timeout(600)
            data = self._extract(page, only_new=True)

        miss = missing(questions, answers)
        fields = [as_dict(q, answers[q.key]) for q in questions]
        miss_list = [{"key": q.key, "label": q.label, "kind": q.kind, "options": q.options,
                      "note": answers[q.key].note} for q in miss]
        human = [q for q in miss if answers[q.key].source == "human"]

        if mode == "prepare":
            shot = self._shot(page, job, "prepared")
            extra = (" " + " ".join(notes)) if notes else ""
            if miss:
                msg = f"{len(miss)} required question(s) need your answer"
                if human:
                    msg += " (the employer asks you to answer some personally)"
                return Result("needs_input", msg + "." + extra, fields, miss_list, shot, page.url)
            return Result("ready", "Form filled; nothing has been sent." + extra, fields, [], shot, page.url)

        # ---- submit mode
        if miss:
            if not self.headless:
                return self._assist(page, job, fields, miss_list,
                                    f"{len(miss)} question(s) need you. Finish them in the browser window and press Submit.")
            return Result("needs_input", f"{len(miss)} required question(s) still unanswered; not submitted.",
                          fields, miss_list, self._shot(page, job, "unanswered"), page.url)
        before = self._extract(page)["page"]
        if not self._click_submit(page):
            return Result("error", "Couldn't find the Submit button.", fields, [], self._shot(page, job, "nosubmit"), page.url)
        self.log("Submitted; waiting for confirmation")
        outcome = self._await_outcome(page, 30, baseline_success=before["success"])
        shot = self._shot(page, job, "submitted")
        if outcome == "success":
            return Result("applied", "Application submitted and confirmed.", fields, [], shot, page.url)
        if outcome in ("captcha", "code"):
            what = "a CAPTCHA" if outcome == "captcha" else "an email security code"
            if not self.headless:
                return self._assist(page, job, fields, [], f"The site asked for {what}. Complete it in the browser window.")
            return Result("blocked", f"The site asked for {what}. Turn off headless mode in Settings and submit again to finish it yourself.",
                          fields, [], shot, page.url)
        if outcome == "errors":
            errs = self._extract(page)["page"]["errors"]
            return Result("needs_input", "The form reported problems: " + "; ".join(errs[:4]), fields, miss_list, shot, page.url)
        return Result("unconfirmed", "Submit was clicked but no confirmation appeared. Check your email before retrying.",
                      fields, [], shot, page.url)

    # ------------------------------------------------------------ helpers
    def _settle(self, page, ms=8000):
        try:
            page.wait_for_load_state("networkidle", timeout=ms)
        except Exception:
            pass

    def _extract(self, page, only_new=False):
        return page.evaluate(EXTRACT_JS, {"onlyNew": only_new})

    def _dismiss_cookies(self, page):
        try:
            banners = page.locator("[id*=cookie i], [class*=cookie i], [id*=consent i], [class*=consent i], [class*=cc-window], [id*=onetrust i]")
            if not banners.count():
                return
            for rx in (COOKIE_REJECT_RE, COOKIE_ACCEPT_RE):
                btn = banners.get_by_role("button", name=rx)
                if btn.count():
                    btn.first.click(timeout=3000)
                    page.wait_for_timeout(300)
                    return
        except Exception:
            pass

    def _click_apply(self, page):
        """Follow a job page's Apply link/button. Returns the page holding the form."""
        for role in ("link", "button"):
            loc = page.get_by_role(role, name=APPLY_LINK_RE)
            if not loc.count():
                continue
            try:
                with page.context.expect_page(timeout=4000) as new_tab:
                    loc.first.click(timeout=5000)
                page = new_tab.value  # opened in a new tab
            except Exception:
                pass  # navigated (or revealed the form) in place
            self._settle(page)
            page.wait_for_timeout(1000)
            return page
        return page

    def _goto_ats_form(self, page):
        """If we landed on a Greenhouse/Lever/Ashby job page, open its application form."""
        kind, board, job_id, host = ats.detect(page.url)
        target = ats.form_url(kind, board, job_id, host) if kind else None
        if target and page.url.split("#")[0] != target:
            self.log(f"Found a {kind.capitalize()} form: {target}")
            page.goto(target, wait_until="domcontentloaded", timeout=45000)
            self._settle(page)
        if kind:
            self.found_ats = {"ats": kind, "ats_board": board, "ats_job_id": job_id, "apply_url": target}

    def _click_submit(self, page):
        candidates = page.locator("button, input[type=submit]")
        best = None
        for i in range(candidates.count()):
            el = candidates.nth(i)
            try:
                if not el.is_visible():
                    continue
                label = (el.inner_text() or el.get_attribute("value") or "").strip()
            except Exception:
                continue
            if SUBMIT_RE.match(label) and not el.get_attribute("data-jobbot"):
                best = el
        if best is None:
            return False
        best.scroll_into_view_if_needed()
        best.click()
        return True

    def _await_outcome(self, page, seconds, baseline_success=False):
        """Watch the page after Submit. A "thank you" that was already on the form page
        (job descriptions often say it) only counts once the form itself is gone."""
        deadline = time.time() + seconds
        url0 = page.url
        while time.time() < deadline:
            page.wait_for_timeout(1500)
            try:
                d = self._extract(page)["page"]
            except Exception:
                continue  # page navigating
            if d["success"] and (not baseline_success or not d["submit"] or page.url != url0):
                return "success"
            if page.url != url0 and re.search(r"/(thanks|thank-you|confirmation|submitted|success)\b", page.url):
                return "success"
            if d["captcha"]:
                return "captcha"
            body = page.inner_text("body")[:5000].lower()
            if "security code" in body or "verification code" in body:
                return "code"
            if (d["errors"] or d["invalid"]) and page.url == url0 and time.time() > deadline - seconds + 5:
                return "errors"
        return "unknown"

    def _assist(self, page, job, fields, miss_list, message):
        """Visible-browser mode: wait for the human to finish and submit."""
        self.log(message)
        before = self._extract(page)["page"]
        outcome = self._await_outcome(page, self.assist_timeout, baseline_success=before["success"])
        shot = self._shot(page, job, "assisted")
        if outcome == "success":
            return Result("applied", "Submitted with your help in the browser window.", fields, [], shot, page.url)
        return Result("needs_input", message + " (timed out waiting)", fields, miss_list, shot, page.url)

    def _shot(self, page, job, tag):
        try:
            config.ensure_dirs()
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", job.get("id", "job"))[:80]
            name = f"{safe}-{tag}-{int(time.time())}.png"
            page.screenshot(path=str(config.SHOTS_DIR / name), full_page=True)
            return name
        except Exception:
            return None

    # ------------------------------------------------------------ filling
    def _fill(self, page, q, a):
        if a is None or not a.resolved(q):
            return False
        try:
            fn = getattr(self, f"_fill_{q.kind}")
            return bool(fn(page, q, a))
        except Exception as e:
            self.log(f"Couldn't fill “{q.label[:60]}”: {str(e).splitlines()[0][:160]}")
            return False

    def _loc(self, page, key):
        return page.locator(f'[data-jobbot="{key}"]').first

    SUGGESTIONS = ("[role=option], [class*=dropdown-location], [class*=suggestion], .pac-item, "
                   "[class*=autocomplete] li, [class*=autocomplete-item]")

    def _autocomplete(self, page, loc, a):
        """Type into a free-text box that pops up suggestions (e.g. Lever's location)."""
        loc.fill("")
        loc.press_sequentially(a.search[:40], delay=30)
        scope = loc.locator("xpath=../..")
        deadline = time.time() + 3
        found = []
        while time.time() < deadline and not found:
            page.wait_for_timeout(300)
            items = scope.locator(self.SUGGESTIONS)
            found = [(" ".join((items.nth(i).inner_text() or "").split()), items.nth(i))
                     for i in range(min(items.count(), 20)) if items.nth(i).is_visible()]
            found = [(t, el) for t, el in found if t]
        if not found:
            return False
        choice = self._choose(found, [str(a.value), *a.alternatives], fuzzy=True) or found[0][0]
        next(el for t, el in found if t == choice).click()
        page.wait_for_timeout(300)
        a.option = choice
        return bool(loc.input_value())

    def _fill_text(self, page, q, a):
        loc = self._loc(page, q.key)
        value = str(a.value)
        loc.scroll_into_view_if_needed(timeout=5000)
        if a.search and q.kind == "text" and self._autocomplete(page, loc, a):
            return True
        loc.fill(value)
        if q.input_type == "tel" and not loc.input_value():
            loc.press_sequentially(value, delay=20)
        loc.dispatch_event("blur")
        return bool(loc.input_value())

    _fill_textarea = _fill_text

    def _fill_select(self, page, q, a):
        loc = self._loc(page, q.key)
        if q.multi and isinstance(a.option, list):
            loc.select_option(label=a.option)
        else:
            loc.select_option(label=a.option)
        return True

    def _check(self, page, el):
        try:
            el.check(timeout=3000)
        except Exception:
            el.evaluate("e => (e.labels && e.labels[0] ? e.labels[0] : (e.closest('label') || e)).click()")
        return el.is_checked()

    def _option_el(self, page, q, option):
        i = q.options.index(option)
        return page.locator(f'[data-jobbot="{q.key}:{i}"]').first

    def _fill_radio(self, page, q, a):
        return self._check(page, self._option_el(page, q, a.option))

    def _fill_checkboxes(self, page, q, a):
        return all(self._check(page, self._option_el(page, q, o)) for o in a.option)

    def _fill_checkbox(self, page, q, a):
        el = self._loc(page, q.key)
        if a.option:
            return self._check(page, el)
        return True

    def _fill_buttons(self, page, q, a):
        btn = self._option_el(page, q, a.option)
        btn.scroll_into_view_if_needed(timeout=5000)
        btn.click()
        page.wait_for_timeout(150)
        pressed = btn.get_attribute("aria-pressed") or btn.get_attribute("aria-checked")
        return pressed in (None, "true")

    def _fill_file(self, page, q, a):
        path = Path(str(a.value))
        if not path.exists():
            return False
        if self.mode == "prepare":
            # Many forms upload an attachment the moment it's chosen. Fill keeps
            # your resume on your machine; it's attached when you submit.
            a.note = f"{path.name} is attached when you submit"
            return True
        self._loc(page, q.key).set_input_files(str(path))
        return True

    def _fill_combobox(self, page, q, a):
        loc = self._loc(page, q.key)
        loc.scroll_into_view_if_needed(timeout=5000)
        loc.click()
        wanted = [str(a.option or a.value), *[x for x in a.alternatives if x]]
        options = self._combo_options(page, loc, timeout=800)
        if options and not q.options:
            q.options = [t for t, _ in options][:80]
        choice = self._choose(options, wanted)
        for term in ([] if choice else self._search_terms(a)):
            loc.fill("")
            loc.press_sequentially(term[:40], delay=30)
            options = self._combo_options(page, loc, timeout=5000)
            choice = self._choose(options, wanted, fuzzy=True)
            if not choice and a.search and term == a.search and options:
                choice = options[0][0]  # city autocomplete: first suggestion for our search
            if choice:
                break
        if not choice:
            loc.fill("")
            loc.press("Escape")
            return False
        for text, el in options:
            if text == choice:
                el.click()
                break
        page.wait_for_timeout(250)
        a.option = choice
        return True

    def _probe_options(self, page, q):
        try:
            loc = self._loc(page, q.key)
            loc.scroll_into_view_if_needed(timeout=5000)
            loc.click()
            opts = self._combo_options(page, loc, timeout=1200)
            q.options = [t for t, _ in opts][:80]
            loc.press("Escape")
        except Exception:
            pass

    def _combo_options(self, page, loc, timeout):
        listbox_id = loc.get_attribute("aria-controls") or loc.get_attribute("aria-owns")
        scope = page.locator(f'[id="{listbox_id}"]') if listbox_id else page
        opts = scope.locator("[role=option]")
        deadline = time.time() + timeout / 1000
        while True:
            visible = [opts.nth(i) for i in range(min(opts.count(), 100))]
            visible = [o for o in visible if o.is_visible()]
            if visible or time.time() > deadline:
                break
            page.wait_for_timeout(200)
        out = []
        for o in visible:
            t = " ".join((o.inner_text() or "").split())
            if t and not re.match(r"^(no options|no results|loading)", t, re.I):
                out.append((t, o))
        return out

    @staticmethod
    def _search_terms(a):
        """What to type into a search-as-you-type box, most specific first."""
        full = str(a.option or a.value)
        terms = [a.search] if a.search else []
        terms.append(full)
        parts = [p.strip() for p in re.split(r",| - | \(", full) if p.strip()]
        if len(parts) > 1:
            terms += [parts[-1], parts[0]]
        seen, out = set(), []
        for t in terms:
            if t and t.lower() not in seen:
                seen.add(t.lower())
                out.append(t)
        return out[:4]

    def _choose(self, options, wanted, fuzzy=False):
        texts = [t for t, _ in options]
        for w in wanted:
            hit = pick_option(w, texts)
            if hit:
                return hit
        if fuzzy and texts:
            from ..textutil import similarity
            best = max(texts, key=lambda t: max(similarity(w, t) for w in wanted))
            if max(similarity(w, best) for w in wanted) >= 0.6:
                return best
        return None
