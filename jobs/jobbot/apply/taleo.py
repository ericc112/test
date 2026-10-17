"""Applying on Taleo Business Edition career sites (...tbe.taleo.net), such as Olin's.

The application is one form shown a step at a time. The first step registers your account with
the email in JOBBOT_WORKDAY_EMAIL (or your profile's) and the password in JOBBOT_WORKDAY_PASSWORD,
the same pair JobBot uses on Workday. If that account already exists, JobBot signs in on the
site's login page and starts the application again. The other steps are filled like any form,
pressing Next after each; the last one has Submit. JobBot stops at CAPTCHAs and email checks, as
everywhere else.
"""
import re

from ..answers import Question, answer_all, as_dict, missing
from .engine import Engine, Result
from .workday import account_email, password

TBE = re.compile(r"\.tbe\.taleo\.net/", re.I)
NEXT = 'a[aria-label="next"], button[aria-label="next"]'
SUBMIT = re.compile(r"^\s*(submit|submit application|send application)\s*$", re.I)
ALREADY = re.compile(r"you('ve| have) (already|previously) (applied|submitted an application)|already applied (to|for) this (job|position|requisition)", re.I)
EXISTS = re.compile(r"already (exists|registered|in use|been registered)|is (already )?registered|account .{0,30}exists", re.I)


def is_taleo(job):
    return bool(TBE.search(job.get("url") or job.get("apply_url") or ""))


class TaleoEngine(Engine):
    MAX_STEPS = 8

    def _run(self, page, job, ctx, url, mode):
        email, pw = account_email(ctx.profile), password(ctx.profile)
        if not email or not pw:
            return Result("needs_input", "Add your email and a password first: Taleo needs an account with each employer.")
        company = job.get("company") or "the employer"
        apply_url = url.replace("viewRequisition", "applyRequisition")
        self.log(f"Opening {apply_url}")
        page.goto(apply_url, wait_until="domcontentloaded", timeout=45000)
        self._settle(page)
        self._dismiss_cookies(page)
        stop = self._account(page, job, email, pw, company, apply_url)
        if stop:
            return stop
        if ALREADY.search(page.inner_text("body")[:3000]):
            return Result("applied", f"{company}'s site says you have already applied to this job.",
                          screenshot=self._shot(page, job, "already"), url=page.url)
        if "/myjobs" in page.url.lower() and not self._on_form_step(page):
            # Taleo sends you to My Jobs instead of a form it won't reopen: one already sent, or a closed opening.
            return Result("unconfirmed", f"{company}'s site opens My Jobs instead of the application, so it was probably sent "
                                         "already (or the opening closed). Check your email for their confirmation.",
                          screenshot=self._shot(page, job, "myjobs"), url=page.url)

        questions, answers, first = [], {}, True
        for _ in range(self.MAX_STEPS):
            data = self._extract(page, only_new=not first)
            first = False
            if data["page"]["captcha"] or data["page"]["botwall"]:
                return Result("blocked", f"{company}'s site showed a CAPTCHA or bot check. Open the posting and finish it yourself.",
                              [as_dict(q, answers[q.key]) for q in questions], [], self._shot(page, job, "captcha"), page.url)
            qs = [Question(**q) for q in data["questions"] if q["key"] not in answers]
            new = answer_all(qs, ctx)
            for q in sorted(qs, key=lambda q: q.kind != "file"):  # the resume first: some sites read it into the form
                a = new[q.key]
                if a.resolved(q) and not self._fill(page, q, a):
                    a.failed = True
                    a.note = a.note or "Couldn't enter this answer automatically"
            questions += qs
            answers.update(new)
            self._close_popups(page)
            if self._submit_button(page) is not None:
                break
            step = self._step(page)
            self._press(page)
            if self._step(page) == step:
                miss = missing(questions, answers)
                errs = self._extract(page)["page"]["errors"]
                msg = (f"{company}'s step {step} needs: " + "; ".join(errs[:4])) if errs else f"{company}'s step {step} wouldn't continue."
                return Result("needs_input" if miss else "error", msg,
                              [as_dict(q, answers[q.key]) for q in questions],
                              [{"key": q.key, "label": q.label, "kind": q.kind, "options": q.options, "note": answers[q.key].note} for q in miss],
                              self._shot(page, job, "stuck"), page.url)

        fields = [as_dict(q, answers[q.key]) for q in questions]
        miss = missing(questions, answers)
        if miss:
            return Result("needs_input", f"{len(miss)} required question(s) need your answer.", fields,
                          [{"key": q.key, "label": q.label, "kind": q.kind, "options": q.options, "note": answers[q.key].note} for q in miss],
                          self._shot(page, job, "unanswered"), page.url)
        if mode == "prepare":
            return Result("ready", f"Filled in on {company}'s Taleo site, up to Submit; nothing has been sent. Review it and tap Submit.",
                          fields, [], self._shot(page, job, "review"), page.url)
        button = self._submit_button(page)
        if button is None:
            return Result("error", "Couldn't find the Submit button on the last step.", fields, [], self._shot(page, job, "nosubmit"), page.url)
        self.log(f"{company}: submitting")
        for _ in range(3):  # Submit can lead to a voluntary page (gender, race, veteran) with a Submit of its own
            button.scroll_into_view_if_needed()
            button.click()
            outcome = self._await_outcome(page, 20)
            if outcome != "unknown":
                break
            qs = [Question(**q) for q in self._extract(page)["questions"] if q["key"] not in answers]  # the wait above tags them
            button = self._submit_button(page)
            if not qs or button is None:
                break
            self.log(f"{company}: answering the voluntary questions after Submit")
            new = answer_all(qs, ctx)
            for q in qs:
                if new[q.key].resolved(q):
                    self._fill(page, q, new[q.key])
            self._close_popups(page)
            answers.update(new)
            fields += [as_dict(q, new[q.key]) for q in qs]
        shot = self._shot(page, job, "submitted")
        if outcome == "success":
            return Result("applied", f"Submitted to {company} and confirmed.", fields, [], shot, page.url)
        if outcome in ("captcha", "code"):
            what = "a CAPTCHA" if outcome == "captcha" else "an email security code"
            return Result("blocked", f"{company}'s site asked for {what} at Submit. Finish it there yourself.", fields, [], shot, page.url)
        if outcome == "errors":
            errs = self._extract(page)["page"]["errors"]
            return Result("needs_input", "The form reported problems: " + "; ".join(errs[:4]), fields, [], shot, page.url)
        return Result("unconfirmed", "Submit was pressed but no confirmation appeared. Check your email before trying again.",
                      fields, [], shot, page.url)

    # ------------------------------------------------------------ steps
    def _account(self, page, job, email, pw, company, apply_url):
        """Step 1: register with your email and password, or sign in when that account already exists."""
        if not page.locator("input[name=cwsPassword]").count():
            return None  # already signed in: the application starts at its first form step
        self._type(page, "input[name=email]", email)
        self._type(page, "input[name=cwsPassword]", pw)
        if page.locator("input[name=cwsPassword_2]").count():
            self._type(page, "input[name=cwsPassword_2]", pw)
        self._press(page)
        if self._on_form_step(page):
            self.log(f"Registered on {company}'s Taleo site")
            return None
        if not EXISTS.search(page.inner_text("body")):
            errs = self._extract(page)["page"]["errors"] or ["the site didn't accept the email and password"]
            return Result("needs_input", f"Couldn't register on {company}'s Taleo site: {'; '.join(errs[:3])}.",
                          screenshot=self._shot(page, job, "register"), url=page.url)
        # The account exists: Taleo shows its sign-in form ("Previous Applicants"), or links to its login page.
        self.log(f"{company}: you have an account there already, signing in")
        if not page.locator("input[type=password]").filter(visible=True).count():
            login = page.locator("a[href*=candidateLogin]").first
            if not login.count():
                return Result("needs_input", f"You already have an account on {company}'s Taleo site, and its sign-in page wasn't found.",
                              screenshot=self._shot(page, job, "signin"), url=page.url)
            page.goto(login.get_attribute("href"), wait_until="domcontentloaded", timeout=45000)
            self._settle(page)
        box = page.locator("input[type=email], input[name*=email i], input[name*=user i]").filter(visible=True).first
        if box.count() and not box.input_value().strip():
            box.fill(email)
        self._type(page, "input[type=password]", pw)
        login_button = page.locator("button, input[type=submit], a").filter(visible=True)
        login_button.filter(has_text=re.compile(r"^\s*(log ?in|sign ?in)\s*$", re.I)).first.click(timeout=10000)
        page.wait_for_timeout(3000)
        self._settle(page)
        if page.locator("input[type=password]").filter(visible=True).count() and not self._on_form_step(page):
            return Result("needs_input", f"You have an account on {company}'s Taleo site, but it didn't accept your JobBot password. "
                                         "Use its \u201cForgot password?\u201d link to set it to the password JobBot uses, then tap Try again.",
                          screenshot=self._shot(page, job, "signin"), url=page.url)
        if not self._on_form_step(page):
            page.goto(apply_url, wait_until="domcontentloaded", timeout=45000)
            self._settle(page)
        if page.locator("input[name=cwsPassword]").is_visible():
            return Result("needs_input", f"Signed in to {company}'s Taleo site, but it asked to register again.",
                          screenshot=self._shot(page, job, "signin"), url=page.url)
        return None

    def _on_form_step(self, page):
        """On the application's form, past the account step."""
        cur = page.locator(".oracletaleocwsv2-current-step")
        try:
            return cur.count() > 0 and cur.first.inner_text().strip() not in ("", "1") \
                or (page.locator(".oracletaleocwsv2-step.oracletaleocwsv2-active").count() > 0
                    and not page.locator("input[name=cwsPassword]").is_visible())
        except Exception:
            return False

    def _type(self, page, selector, text):
        el = page.locator(selector).filter(visible=True).first  # the sign-in page also holds hidden password boxes
        el.click()
        el.fill(text)

    def _step(self, page):
        el = page.locator(".oracletaleocwsv2-current-step").first
        try:
            return el.inner_text().strip() if el.count() else page.url
        except Exception:
            return page.url

    def _press(self, page):
        """Next, then wait for the next step (or the step's errors)."""
        step = self._step(page)
        page.locator(NEXT).first.click(timeout=10000)
        for _ in range(10):
            page.wait_for_timeout(1000)
            if self._step(page) != step or self._extract(page)["page"]["errors"]:
                break
        self._settle(page, 4000)

    def _close_popups(self, page):
        """Close a date picker left open by the last answer: it can cover Next and Submit."""
        try:
            page.keyboard.press("Escape")
            page.evaluate("document.activeElement && document.activeElement.blur()")
            page.wait_for_timeout(300)
        except Exception:
            pass

    def _submit_button(self, page):
        for el in page.locator("button, input[type=submit], a").all():
            try:
                if el.is_visible() and SUBMIT.match(el.inner_text() or el.get_attribute("value") or ""):
                    return el
            except Exception:
                continue
        return None
