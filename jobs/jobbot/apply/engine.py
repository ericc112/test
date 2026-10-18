"""Drive a real browser through an application form.

prepare: open the form, fill everything we can, screenshot, never submit.
submit:  fill again (using the answers you reviewed), press Submit, and check
         for a confirmation, a CAPTCHA, or validation errors.

With headless off you can watch it work. If it gets stuck on a CAPTCHA or a
question only you can answer, it waits for you to finish in that window.
"""
import os
import re
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

from .. import ats, config
from ..answers import AI_POLICY, Question, answer_all, as_dict, missing
from ..textutil import norm, pick_option

EXTRACT_JS = (Path(__file__).with_name("extract.js")).read_text()

SUBMIT_RE = re.compile(r"^(submit|submit application|submit (my|your) application|apply|apply now|send application|send|"
                       r"finish|complete application)$", re.I)
APPLY_LINK_RE = re.compile(r"^(apply|apply now|apply (for|to) this (job|position|role)( online)?|apply online|apply here|"
                           r"apply (on|at) (the )?(company|employer)('s)? (site|website)|i'?m interested|start (my |your )?application|"
                           r"begin (my |your )?application|start applying)$", re.I)
COOKIE_REJECT_RE = re.compile(r"^(reject|reject all|decline|deny|necessary only|only necessary)", re.I)
COOKIE_ACCEPT_RE = re.compile(r"^(accept|accept all|allow all|agree|got it|ok|i understand)", re.I)
# Boxes on a careers page that aren't the application: job search, and job-alert settings
# ("Select how often (in days) to receive an alert:" on SuccessFactors sites).
JOB_SEARCH_BOX = re.compile(r"^search\b|\bsearch (by|for|jobs)\b|^keywords?$|job title or keyword|^(city|location),? (state|zip)|"
                            r"receive an alert|job alerts?\b|alert (frequency|me)", re.I)
NOTICE_ACCEPT_RE = re.compile(r"^(i )?(accept|agree)( and (continue|apply))?$|^(continue|proceed)( to (apply|the application))?$|^ok$",
                              re.I)
# Multi-page forms: the button that moves to the next page.
NEXT_RE = re.compile(r"^(next|continue|save (and|&) continue|save (and|&) next|next (step|page)|proceed|review|"
                     r"review (my |your )?application|continue to (the )?(next step|review|application))$", re.I)
# Offered before the form: skip resume-autofill and LinkedIn imports, and apply as a guest when that's allowed.
MANUAL_ENTRY_RE = re.compile(r"^(apply|continue) as (a )?guest$|^guest$|^apply manually$|^(fill|enter) (it |the form |my details )?"
                             r"(in |out )?manually$|^start from scratch$|^skip( this step)?$", re.I)

RATE_LIMITED = re.compile(r"too many requests|rate limit(ed)?|try again (later|in a few)", re.I)
OWN_ENGINE = re.compile(r"myworkdayjobs\.com/|\.tbe\.taleo\.net/", re.I)
# Careers sites that make you sign in. JobBot signs in, or creates the account, with your email and its one password.
ACCOUNT_JS = """() => {
  const vis = (e) => { const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== "hidden" && s.display !== "none"; };
  const about = (e) => [e.type, e.name, e.id, e.getAttribute("autocomplete"), e.getAttribute("aria-label"), e.placeholder,
    (e.labels && e.labels[0] && e.labels[0].innerText) || ""].join(" ");
  const fields = [...document.querySelectorAll("input, select, textarea")].filter(vis)
    .filter((e) => !["hidden", "submit", "button", "image", "reset", "checkbox", "radio", "file"].includes(e.type));
  const other = fields.filter((e) => e.type !== "password");
  return { passwords: fields.length - other.length, fields: other.length,
           emails: other.filter((e) => /e-?mail|user ?name|login/i.test(about(e))).length,
           names: other.filter((e) => /first|last|given|family|full ?name/i.test(about(e))).length,
           text: (document.body.innerText || "").slice(0, 5000) };
}"""
FINGERPRINT_JS = """() => location.href + "|" + [...document.querySelectorAll("input, select, textarea, h1, h2, h3, legend")]
  .filter((e) => e.offsetParent !== null && e.type !== "hidden").map((e) => e.name || e.id || e.innerText || e.type).join(",")"""
SIGN_IN_TEXT = re.compile(r"\b(sign ?in|log ?in|login|create (an |your )?account|register|returning (user|candidate|applicant)|"
                          r"new (user|candidate)s?)\b", re.I)
NOT_SIGN_IN = re.compile(r"job alert|newsletter|subscribe|talent (community|network)", re.I)
VERIFY_RE = re.compile(r"verify your (email|account)|verification (code|link|email)|check your (email|inbox)|confirm your email|"
                       r"we('ve| have) (just )?(sent|emailed)|one-time (code|passcode|pin)|enter the code", re.I)
EXISTS_RE = re.compile(r"already (exists|registered|in use|have an account)|is (already )?registered|account .{0,30}exists", re.I)
SIGN_IN_GO = re.compile(r"^(sign ?in|log ?in|login|continue|next|submit)$", re.I)
SIGN_IN_LINK = re.compile(r"^(sign ?in|log ?in|login)$|already have an account|returning (user|candidate|applicant)", re.I)
CREATE_LINK = re.compile(r"^(create (an |my |your )?account|register|sign ?up|new (user|candidate)|join( now)?)$|"
                         r"(don'?t|do not) have an account|create (an |my |your )?account", re.I)
CREATE_GO = re.compile(r"^(create (an |my |your )?account|register|sign ?up|create|join|get started|continue|next|submit)$", re.I)
BUTTONS = "button, input[type=submit], input[type=button], [role=button], a"


def password(profile):
    """The one password JobBot uses for your accounts on employers' careers sites (Workday, Taleo and the rest)."""
    return os.environ.get("JOBBOT_WORKDAY_PASSWORD") or profile.get("workday_password") or ""


def account_email(profile):
    return (os.environ.get("JOBBOT_WORKDAY_EMAIL") or profile.get("email") or "").strip()


@dataclass
class Result:
    result: str  # ready | needs_input | blocked | manual | applied | unconfirmed | error | moved (to another engine's site)
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
    MAX_PAGES = 12  # a multi-page form gets this many presses of Next before JobBot gives up

    def _run(self, page, job, ctx, url, mode):
        self.log(f"Opening {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        self._settle(page)
        self._dismiss_cookies(page)
        form = self._form_frame(page)
        data = self._extract(form)
        if data["page"]["botwall"]:
            return Result("manual", "This site shows a bot check, so JobBot stops here. Open the listing and apply yourself.",
                          screenshot=self._shot(page, job, "botcheck"), url=page.url)
        if len(self._form_fields(data)) < 2 and not self._account_state(form):
            page, form, data = self._open_form(page)
            if data["page"]["botwall"]:
                return Result("manual", "The application site shows a bot check, so JobBot stops here. Apply there yourself.",
                              screenshot=self._shot(page, job, "botcheck"), url=page.url)
            if type(self) is Engine and OWN_ENGINE.search(page.url):  # Workday and Taleo have engines of their own
                return Result("moved", f"The application is on {page.url.split('/')[2]}.", url=page.url)
        signed_in = False
        if self._account_state(form):
            stop = self._account(page, job, ctx)
            if stop:
                return stop
            signed_in = True
            form = self._form_frame(page)
            data = self._extract(form)
            if not data["questions"] and self._next_button(form) is None:  # signed in to a dashboard: back to the job
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                self._settle(page)
                page, form, data = self._open_form(page)
        if not data["questions"] and self._next_button(form) is None:
            if RATE_LIMITED.search(form.inner_text("body")[:3000]):
                return Result("error", "The site is turning away requests for now (too many requests). Try again later.",
                              screenshot=self._shot(page, job, "busy"), url=page.url)
            return Result("manual", "Couldn't find an application form on this page.",
                          screenshot=self._shot(page, job, "noform"), url=page.url)

        questions, answers = [], {}
        notes = []
        if ctx.llm is not None and any(AI_POLICY.search(q.get("label") or "") for q in data["questions"]):
            ctx.llm = None
            notes.append("AI answers were turned off because this employer restricts AI use.")
        pages = 1
        while True:
            self._fill_page(form, data, ctx, questions, answers, notes)
            if self._submit_button(form) is not None or pages >= self.MAX_PAGES:
                break
            nxt = self._next_button(form)
            if nxt is None:
                break
            if not self._press_next(page, form, nxt):
                miss = missing(questions, answers)
                errs = self._extract(form)["page"]["errors"]
                return Result("needs_input" if miss or errs else "error",
                              ("Page %d of the form needs: %s" % (pages, "; ".join(errs[:4]))) if errs else
                              f"Page {pages} of the form wouldn't go on to the next one.",
                              [as_dict(q, answers[q.key]) for q in questions],
                              [{"key": q.key, "label": q.label, "kind": q.kind, "options": q.options, "note": answers[q.key].note}
                               for q in miss], self._shot(page, job, "stuck"), page.url)
            pages += 1
            self.log(f"Page {pages} of the application")
            form = self._form_frame(page)
            if self._account_state(form):  # some sites ask you to sign in after the first page
                if signed_in:
                    return Result("error", "The site asked to sign in again partway through the form.",
                                  screenshot=self._shot(page, job, "signin"), url=page.url)
                stop = self._account(page, job, ctx)
                if stop:
                    return stop
                signed_in = True
                form = self._form_frame(page)
            data = self._extract(form, only_new=True)
        if pages > 1:
            notes.append(f"The form had {pages} pages; the site keeps what was entered on the earlier ones.")

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
        before = self._extract(form)["page"]
        if not self._click_submit(form):
            return Result("error", "Couldn't find the Submit button.", fields, [], self._shot(page, job, "nosubmit"), page.url)
        self.log("Submitted; waiting for confirmation")
        outcome = self._await_outcome(page, 30, baseline_success=before["success"], form=form)
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
            errs = self._extract(form)["page"]["errors"]
            return Result("needs_input", "The form reported problems: " + "; ".join(errs[:4]), fields, miss_list, shot, page.url)
        return Result("unconfirmed", "Submit was clicked but no confirmation appeared. Check your email before retrying.",
                      fields, [], shot, page.url)

    @staticmethod
    def _form_fields(data):
        """Fields that could be an application's: not file boxes, and not a job page's search boxes."""
        return [q for q in data["questions"] if q["kind"] != "file" and not JOB_SEARCH_BOX.search(q.get("label") or "")]

    def _fill_page(self, form, data, ctx, questions, answers, notes):
        """Answer and fill one page of the form. Fields that appear as others are answered get up to two more passes."""
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
                        self._probe_options(form, q)  # so the review screen can offer a dropdown
                    continue
                if self._fill(form, q, a):
                    if q.kind == "file" and self.mode == "submit":
                        form.wait_for_timeout(2500)  # let resume parsers autofill before we overwrite
                else:
                    a.failed = True
                    a.note = a.note or "Couldn't enter this answer automatically"
            questions += new_qs
            answers.update(new_answers)
            form.wait_for_timeout(600)
            data = self._extract(form, only_new=True)

    def _open_form(self, page):
        """From a job page, follow Apply (and a guest or fill-in-yourself choice) to the form: (page, form frame, fields)."""
        page = self._click_apply(page)
        self._goto_ats_form(page)
        self._dismiss_cookies(page)
        form = self._form_frame(page)
        if self._press_text(page, form, MANUAL_ENTRY_RE):
            self.log("Chose to fill the form in (not resume autofill or another site's sign-in)")
            form = self._form_frame(page)
        return page, form, self._extract(form)

    # ------------------------------------------------------------ pages, frames, buttons
    COUNT_JS = "() => [...document.querySelectorAll('input:not([type=hidden]), select, textarea')].filter((e) => e.offsetParent !== null).length"

    def _form_frame(self, page):
        """Where the form is: the page itself, or a frame in it with more fields (careers pages often embed their ATS's form)."""
        best = page.main_frame
        try:
            most = best.evaluate(self.COUNT_JS)
        except Exception:
            return best
        for f in page.frames:
            if f is page.main_frame:
                continue
            try:
                n = f.evaluate(self.COUNT_JS)
            except Exception:
                continue
            if n >= 2 and n > most:
                best, most = f, n
        return best

    def _fingerprint(self, form):
        try:
            return form.evaluate(FINGERPRINT_JS)
        except Exception:
            return None  # navigating

    ERRORS_JS = """() => [...document.querySelectorAll("[role=alert], .error, .errors, [class*=error-message], [aria-invalid=true]")]
      .some((e) => e.offsetParent !== null && ((e.innerText || "").trim() || e.getAttribute("aria-invalid") === "true"))"""

    def _wait_change(self, page, before, seconds=12):
        """After a click: wait for the page to change. False if it stayed put (often with errors showing)."""
        start = time.time()
        while time.time() - start < seconds:
            page.wait_for_timeout(600)
            form = self._form_frame(page)
            if self._fingerprint(form) != before:
                self._settle(page, 5000)
                page.wait_for_timeout(500)
                return True
            try:
                if time.time() - start > 3 and form.evaluate(self.ERRORS_JS):
                    return False
            except Exception:
                pass
        return False

    def _press_next(self, page, form, button):
        before = self._fingerprint(form)
        button.scroll_into_view_if_needed(timeout=5000)
        button.click(timeout=10000)
        return self._wait_change(page, before)

    @staticmethod
    def _label(el):
        text = el.inner_text() or el.get_attribute("value") or el.get_attribute("aria-label") or ""
        return re.sub(r"^\W+|\W+$", "", " ".join(text.split()))

    def _find(self, form, rx, links=True, limit=300):
        """The first visible button (then link) whose text matches rx."""
        for sel in ("button, input[type=submit], input[type=button], [role=button]",) + (("a",) if links else ()):
            for el in form.locator(sel).all()[:limit]:
                try:
                    if el.is_visible() and rx.match(self._label(el)) and not el.is_disabled():
                        return el
                except Exception:
                    continue
        return None

    def _press_text(self, page, form, rx, links=True):
        """Click the button or link whose text matches rx and wait for the page to change. False if there's none."""
        el = self._find(form, rx, links)
        if el is None:
            return False
        before = self._fingerprint(form)
        el.scroll_into_view_if_needed(timeout=5000)
        el.click(timeout=10000)
        self._wait_change(page, before)
        return True

    def _next_button(self, form):
        return self._find(form, NEXT_RE)

    # ------------------------------------------------------------ accounts
    def _account_state(self, form, after=False):
        """What a sign-in page wants: "register", "signin", "email" (an email-first sign-in), or "verify" (only after
        JobBot pressed something there: confirm your email). None on anything else, such as the form itself."""
        try:
            s = form.evaluate(ACCOUNT_JS)
        except Exception:
            return None
        if s["fields"] <= 8 and (s["passwords"] >= 2 or (s["passwords"] == 1 and s["names"])):
            return "register"
        if s["passwords"] == 1 and s["fields"] <= 3:
            return "signin"
        if after and s["fields"] <= 2 and VERIFY_RE.search(s["text"]):
            return "verify"
        if 1 <= s["fields"] <= 2 and s["emails"] and SIGN_IN_TEXT.search(s["text"]) and not NOT_SIGN_IN.search(s["text"]):
            return "email"
        return None

    def _account(self, page, job, ctx):
        """Sign in to the employer's careers site with your email and JobBot's one password, or create that account
        when there isn't one. Stops at email confirmations and CAPTCHAs: those are yours to do."""
        company = job.get("company") or "The employer"
        email, pw = account_email(ctx.profile), password(ctx.profile)
        if not email or not pw:
            return Result("manual", f"{company}'s careers site needs an account. Set JOBBOT_WORKDAY_PASSWORD (the one password "
                                    "JobBot uses for employer accounts) and try again, or apply there yourself.",
                          screenshot=self._shot(page, job, "account"), url=page.url)
        tried = set()
        for _ in range(8):
            form = self._form_frame(page)
            state = self._account_state(form, after=bool(tried))
            if state is None:
                self.log(f"Signed in on {company}'s careers site")
                return None
            data = self._extract(form)
            errs = "; ".join(data["page"]["errors"][:3])
            if data["page"]["captcha"] or data["page"]["botwall"]:
                return Result("blocked", f"{company}'s sign-in shows a CAPTCHA or bot check. Sign in there yourself, then try again.",
                              screenshot=self._shot(page, job, "captcha"), url=page.url)
            if state == "verify":
                return Result("blocked", f"{company} sent a confirmation to {email}. Confirm it, then try again: JobBot doesn't "
                                         "read your email.", screenshot=self._shot(page, job, "verify"), url=page.url)
            if state == "email" and "email" not in tried:
                tried.add("email")
                self.log(f"{company}: signing in")
                self._type_email(form, email)
                if not self._press_text(page, form, SIGN_IN_GO, links=False):
                    break
            elif state == "signin" and "signin" not in tried:
                tried.add("signin")
                self.log(f"{company}: signing in")
                self._type_email(form, email)
                box = form.locator("input[type=password]").filter(visible=True).first  # never the hidden bot traps
                box.fill(pw)
                before = self._fingerprint(form)
                if not self._press_text(page, form, SIGN_IN_GO, links=False):
                    box.press("Enter")
                    self._wait_change(page, before)
            elif state == "signin" and "register" not in tried and "create" not in tried and not EXISTS_RE.search(errs):
                tried.add("create")  # no account with that email yet: make one
                if not self._press_text(page, form, CREATE_LINK):
                    return Result("needs_input", f"{company}'s site didn't sign you in{': ' + errs if errs else ''}. If you have an "
                                                 "account there, use its \u201cForgot password\u201d link to set it to JobBot's password.",
                                  screenshot=self._shot(page, job, "signin"), url=page.url)
            elif state == "register" and "register" not in tried:
                tried.add("register")
                self.log(f"{company}: creating your account")
                stop = self._register(page, form, data, job, ctx, email, pw)
                if stop:
                    return stop
            elif state == "register" and EXISTS_RE.search(errs or data["page"]["title"]) and "signin" not in tried:
                self._press_text(page, form, SIGN_IN_LINK)
            else:
                if state == "email":
                    msg = f"{company}'s sign-in didn't go past the email step{': ' + errs if errs else ''}."
                elif state == "signin" or EXISTS_RE.search(errs):
                    msg = (f"You have an account on {company}'s site, but it didn't accept JobBot's password. Use its "
                           "\u201cForgot password\u201d link to set it to that password, then try again.")
                else:
                    msg = f"Couldn't create your account on {company}'s site: {errs or 'it did not accept the form'}."
                return Result("needs_input", msg, screenshot=self._shot(page, job, "account"), url=page.url)
        return Result("error", f"Couldn't get past {company}'s sign-in.", screenshot=self._shot(page, job, "account"), url=page.url)

    EMAIL_BOX = ("input[type=email], input[autocomplete=username], input[autocomplete=email], input[name*=email i], "
                 "input[id*=email i], input[name*=user i], input[id*=user i], input[name*=login i]")

    def _type_email(self, form, email):
        box = form.locator(self.EMAIL_BOX).filter(visible=True).first
        if box.count():
            box.fill(email)

    def _register(self, page, form, data, job, ctx, email, pw):
        """Fill the sign-up form: your details (with the account email), JobBot's password in each password box, the
        required terms box. Then create the account."""
        mine = replace(ctx, profile=dict(ctx.profile, email=email))
        qs = [Question(**q) for q in data["questions"]]
        new = answer_all(qs, mine)
        for q in qs:
            if new[q.key].resolved(q):
                self._fill(form, q, new[q.key])
        for box in form.locator("input[type=password]").filter(visible=True).all():
            box.fill(pw)
        miss = missing(qs, new)
        if miss:
            return Result("needs_input", f"{job.get('company') or 'The'} sign-up asks: " + "; ".join(q.label for q in miss[:4]),
                          [as_dict(q, new[q.key]) for q in qs],
                          [{"key": q.key, "label": q.label, "kind": q.kind, "options": q.options, "note": new[q.key].note} for q in miss],
                          self._shot(page, job, "register"), page.url)
        if not self._press_text(page, form, CREATE_GO, links=False):
            return Result("error", "Couldn't find the button that creates your account.", screenshot=self._shot(page, job, "register"),
                          url=page.url)
        return None

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
            return self._accept_notice(page)
        return page

    def _accept_notice(self, page):
        """Accept a notice shown after Apply (a privacy or data-consent dialog), which may open the form in a new tab."""
        dialog = page.locator("[role=dialog], [aria-modal=true], .modal").filter(visible=True)
        if not dialog.count():
            return page
        button = dialog.first.get_by_role("button", name=NOTICE_ACCEPT_RE)
        if not button.count():
            button = dialog.first.get_by_role("link", name=NOTICE_ACCEPT_RE)
        if not button.count():
            return page
        self.log("Accepting the notice shown before the application")
        try:
            with page.context.expect_page(timeout=4000) as new_tab:
                button.first.click(timeout=5000)
            page = new_tab.value
        except Exception:
            pass
        self._settle(page)
        page.wait_for_timeout(1000)
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

    def _submit_button(self, form):
        """The form's Submit button (the last one when there are several), or None before the last page."""
        candidates = form.locator("button, input[type=submit]")
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
        return best

    def _click_submit(self, form):
        best = self._submit_button(form)
        if best is None:
            return False
        best.scroll_into_view_if_needed()
        best.click()
        return True

    def _await_outcome(self, page, seconds, baseline_success=False, form=None):
        """Watch the page after Submit. A "thank you" that was already on the form page
        (job descriptions often say it) only counts once the form itself is gone.
        With a form in a frame, both the frame and the page around it are watched."""
        docs = [page] if form is None or form is page.main_frame else [form, page]
        deadline = time.time() + seconds
        url0 = page.url
        while time.time() < deadline:
            page.wait_for_timeout(1500)
            seen = []
            for doc in docs:
                try:
                    seen.append((doc, self._extract(doc)["page"]))
                except Exception:
                    continue  # navigating, or the frame went away
            if not seen:
                continue
            if any(d["success"] and (not baseline_success or not d["submit"] or page.url != url0) for _, d in seen):
                return "success"
            if page.url != url0 and re.search(r"/(thanks|thank-you|confirmation|submitted|success)\b", page.url):
                return "success"
            if any(d["captcha"] for _, d in seen):
                return "captcha"
            try:
                body = " ".join(doc.inner_text("body") for doc, _ in seen).lower()  # the code box can be at the very end
            except Exception:
                body = ""
            if "security code" in body or "verification code" in body:
                return "code"
            d = seen[0][1]
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
        if q.input_type == "popup":
            return self._fill_picker(page, q, a)
        return all(self._check(page, self._option_el(page, q, o)) for o in a.option)

    def _fill_picker(self, page, q, a):
        """A "Select All That Apply…" box (Taleo): open its list, tick the choices, press the list's Save."""
        box = self._loc(page, q.key)
        group = box.locator("xpath=ancestor::div[contains(concat(' ', @class, ' '), ' form-group ')][1]")
        group.locator(".input-group-btn button, button.oracletaleocwsv2-multiselect-trigger").first.click()
        popup = group.locator(".oracletaleocwsv2-multiselect-popup").first
        popup.wait_for(state="visible", timeout=5000)
        ok = all(self._tick(self._option_el(page, q, o)) for o in a.option)
        popup.locator("a.oracletaleocwsv2-close-popup-trigger:not(.oracletaleocwsv2-revert-data)").first.click()
        page.wait_for_timeout(400)
        return ok and bool(box.input_value())

    def _tick(self, el):
        """Tick a checkbox the site may hide behind its own styled label: the box, else its label, else its row."""
        if el.is_checked():
            return True
        for target in (el, el.locator("xpath=following-sibling::label[1]"), el.locator("xpath=..")):
            try:
                if target is el:
                    el.check(timeout=1500)
                else:
                    target.click(timeout=1500)
            except Exception:
                continue
            if el.is_checked():
                return True
        el.evaluate("e => { e.checked = true; e.dispatchEvent(new Event('change', {bubbles: true})); }")
        return el.is_checked()

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
        primary = [str(a.option or a.value)]
        fallbacks = [x for x in a.alternatives if x]
        options = self._combo_options(page, loc, timeout=800)
        if options and not q.options:
            q.options = [t for t, _ in options][:80]
        # A short list is the whole menu (Yes/No, consent): any acceptable answer will do.
        # A long one is just the first page of a search box (schools): only an exact hit counts.
        choice = self._choose(options, primary + (fallbacks if len(options) < 40 else []))
        for term in ([] if choice else self._search_terms(a)):
            loc.fill("")
            loc.press_sequentially(term[:40], delay=30)
            options = self._combo_options(page, loc, timeout=5000)
            choice = self._choose(options, primary, fuzzy=True)
            if not choice and a.search and term == a.search and options:
                choice = options[0][0]  # city autocomplete: first suggestion for our search
            if choice:
                break
        for alt in ([] if choice else fallbacks):  # e.g. "Other (school not listed)"
            loc.fill("")
            loc.press_sequentially(alt[:40], delay=30)
            options = self._combo_options(page, loc, timeout=3000)
            choice = self._choose(options, [alt])
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
        full = str(a.value if a.option is None else a.option)
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
            if max(similarity(w, best) for w in wanted) >= 0.85:
                return best
        return None
