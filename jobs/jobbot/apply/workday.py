"""Applying on Workday career sites (about 200 of the Fortune 500).

Workday wants an account with each employer. JobBot signs in with the email in the
JOBBOT_WORKDAY_EMAIL environment variable (or your profile's email) and the password in
JOBBOT_WORKDAY_PASSWORD (or Profile → Workday password), creating the account with the
same email and password the first time. It then fills My Information, My
Experience (your resume), Application Questions and Voluntary Disclosures, pressing
"Save and Continue" after each, and stops at Review: the draft is saved in your account
there and nothing has gone to the employer. Submitting signs in again, reopens the saved
application and presses Submit on the Review step.

It stops for you, without working around them, at CAPTCHAs, email verification and
anything it can't answer, and it never touches Workday's hidden bot-trap field.
"""
import os
import re
from datetime import date
from pathlib import Path

from ..answers import Question, answer_all, as_dict, missing
from ..textutil import norm, pick_option
from .engine import Engine, Result

WD_JS = Path(__file__).with_name("wd_extract.js").read_text()
NEXT = '[data-automation-id="bottom-navigation-next-button"], [data-automation-id="pageFooterNextButton"]'
# Options of the list that's open. Not the items already chosen in other fields: those sit in a
# "selectedItemList" listbox and use the same option markup.
OPTION = ('[role="listbox"]:not([data-automation-id="selectedItemList"]) [role="option"], '
          '[data-automation-id="activeListContainer"] [data-automation-id="promptOption"], '
          '[data-automation-id="activeListContainer"] [data-automation-id="menuItem"]')
# Workday's own error page asks for a refresh.
WENT_WRONG = r"something went wrong[\s\S]{0,300}refresh the page"
# Some sites (Tyson Foods) first ask how to sign in: Apple, Google, LinkedIn or email.
EMAIL_CHOICE = r"^\s*(sign in|continue|log in) with email\s*$"
READY_JS = f"""(sel) => !!document.querySelector(sel) || /{WENT_WRONG}/i.test(document.body ? document.body.innerText : "")
  || [...document.querySelectorAll("button")].some((b) => /{EMAIL_CHOICE}/i.test(b.innerText))"""
SKILLS = re.compile(r"^(type to )?add (your )?skills|^(your )?skills$")
SOON = re.compile(r"immediately|as soon as|\basap\b|right away", re.I)
NO_ITEMS = re.compile(r"^no items\b", re.I)
PASSWORD_RULES = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def password(profile):
    return os.environ.get("JOBBOT_WORKDAY_PASSWORD") or profile.get("workday_password") or ""


def account_email(profile):
    return (os.environ.get("JOBBOT_WORKDAY_EMAIL") or profile.get("email") or "").strip()


def is_workday(job):
    return job.get("source") == "workday" or "myworkdayjobs.com" in (job.get("url") or job.get("apply_url") or "")


class WorkdayEngine(Engine):
    MAX_STEPS = 10

    def _run(self, page, job, ctx, url, mode):
        email, pw = account_email(ctx.profile), password(ctx.profile)
        if not email or not pw:
            return Result("needs_input", "Add your email and a Workday password first: Workday needs an account with each employer.")
        if not PASSWORD_RULES.match(pw):
            return Result("needs_input", "Your Workday password needs 8+ characters with upper and lower case letters, a number and a symbol.")
        company = job.get("company") or "the employer"
        self.log(f"Opening {job.get('url')}")
        page.goto(job.get("url"), wait_until="domcontentloaded", timeout=45000)
        self._settle(page)
        desc = page.locator('[data-automation-id="jobPostingDescription"]')
        if desc.count() and isinstance(ctx.job, dict):  # read before applying: skills are matched to it
            ctx.job["description"] = desc.first.inner_text()[:20000]
        if not self._open_application(page):
            return Result("error", "Couldn't find the Apply button on this Workday posting.",
                          screenshot=self._shot(page, job, "noapply"), url=page.url)
        self._where = {}
        stop = self._account(page, job, email, pw, company)
        if stop:
            return stop
        # Applications with an assessment test (Workday lists it as a step, e.g. "Take Assessment") are skipped
        # before anything is filled in: that test is yours to take, not JobBot's.
        bar = page.locator('[data-automation-id="progressBar"]')
        if bar.count() and re.search(r"assessment", bar.first.inner_text(), re.I):
            return Result("manual", f"{company}'s application includes an assessment test, so JobBot skipped it. Nothing was sent.",
                          screenshot=self._shot(page, job, "assessment"), url=page.url)

        questions, answers, seen, retried = [], {}, set(), {}
        info = self._info(page)
        for step_no in range(self.MAX_STEPS):
            if info["captcha"]:
                return Result("blocked", f"{company}'s site showed a CAPTCHA. Open the posting and finish it yourself.",
                              [as_dict(q, answers[q.key]) for q in questions], [], self._shot(page, job, "captcha"), page.url)
            if "review" in info["step"].lower() or info["next"].lower() == "submit":
                break
            step = info["step"]
            qs = []
            for raw in info["questions"]:
                q = Question(key=f"{step_no}:{raw['key']}", kind=raw["kind"], label=raw["label"] or raw["auto"], required=raw["required"],
                             options=raw["options"], input_type=raw.get("input_type") or "", value=raw.get("value"),
                             section=raw.get("section") or "")
                self._where[q.key] = (raw["auto"], raw["nth"])
                if q.input_type == "wd_listbox":
                    q.options = self._listbox_options(page, q)
                elif q.input_type == "wd_prompt" and q.value in (None, ""):
                    q.options = self._prompt_options(page, q)
                qs.append(q)
            # "From" and "To (Actual or Expected)" next to your school are your education's dates, even where
            # Workday doesn't mark the block as education.
            dates = [q for q in qs if not q.section and re.match(r"(from|to)\b", norm(q.label))]
            if any(re.search(r"school|university|degree", q.label, re.I) for q in qs) and len(dates) <= 2 \
                    and not any(q.section == "employment" for q in qs):  # a single From/To pair: no doubt whose it is
                for q in dates:
                    q.section = "education"
            new = answer_all(qs, ctx)
            for q in qs:  # a search box (schools, skills) lists nothing until you type: the answer is what to search for
                a = new[q.key]
                if q.input_type == "wd_prompt" and a.value not in (None, "", []) and a.option in (None, ""):
                    a.option, a.note = a.value, ""  # not in the first list (or the list is longer than we read): search
            for q in qs:
                a = new[q.key]
                if q.kind == "file":
                    if a.value and self._attached(page, q, a.value):
                        a.note = "Already attached to your draft"
                    elif a.value and self._upload(page, q, a.value):
                        a.note = "Uploaded to your draft (not sent until you submit)"
                    continue
                if a.source == "blank":
                    if q.value not in (None, "") and not self._clear(page, q):  # e.g. a phone number left in "Phone Extension"
                        a.failed, a.note = True, "Couldn't clear this field"
                    continue
                have = q.value[0] if isinstance(q.value, list) and len(q.value) == 1 else q.value
                # Your answer beats what's there (a wrong pick saved in the draft by an earlier run, a misread resume).
                fix = q.kind in ("select", "radio", "buttons", "combobox", "text", "textarea") and a.resolved(q) \
                    and a.source in ("profile", "bank", "user") and norm(str(have)) != norm(str(a.option or a.value)) \
                    and not SKILLS.search(norm(q.label))  # skills already there stay: pressing one again removes it
                if q.value not in (None, "", False, []) and norm(q.label) not in ctx.overrides and not fix:
                    a.value, a.option, a.source, a.note = q.value, q.value, a.source or "site", "Already filled in"
                    continue  # Workday kept it from your account or resume
                if a.resolved(q) and not self._wd_fill(page, q, a):
                    a.failed = True
                    a.note = a.note or "Couldn't enter this answer automatically"
            for q in qs:
                uid = (step, norm(q.label))
                if uid not in seen:
                    seen.add(uid)
                    questions.append(q)
                    answers[q.key] = new[q.key]
            self.log(f"{company}: {step or 'step'} filled, saving")
            after = self._next(page, step)
            if after["step"] == step and "review" not in step.lower() and retried.get(step, 0) < 1 \
                    and not [q for q in qs if q.required and not new[q.key].resolved(q) and self._shown(page, q)]:
                # Every answer was in, yet Workday kept the step: one it dropped. Fill the step again, once.
                retried[step] = 1
                self.log(f"{company}: “{step}” lost an answer, filling it again")
                info = after
                continue
            if after["step"] == step and "review" not in step.lower():
                # Still on the same step: Workday says what's missing.
                miss = [q for q in qs if q.required and not new[q.key].resolved(q) and self._shown(page, q)] or \
                       [q for q in qs if any(norm(q.label)[:30] in norm(e) for e in after["errors"])]
                fields = [as_dict(q, answers[q.key]) for q in questions]
                miss_list = [{"key": q.key, "label": q.label, "kind": q.kind, "options": q.options,
                              "note": new[q.key].note} for q in miss]
                msg = (f"{company}'s “{step}” step needs: " + "; ".join(after["errors"][:4])) if after["errors"] else \
                    f"{company}'s “{step}” step wouldn't continue."
                status = "needs_input" if miss_list else "error"
                return Result(status, msg + " Your answers so far are saved in your draft.", fields, miss_list,
                              self._shot(page, job, "stuck"), page.url)
            info = after

        fields = [as_dict(q, answers[q.key]) for q in questions]
        if mode == "prepare":
            return Result("ready", f"Filled in and saved as a draft in your {company} account; nothing has been sent. "
                                   "Review it and tap Submit.", fields, [], self._shot(page, job, "review"), page.url)
        self.log(f"{company}: submitting")
        if not self._click(page, NEXT):
            return Result("error", "Couldn't find the Submit button on the Review step.", fields, [],
                          self._shot(page, job, "nosubmit"), page.url)
        for _ in range(20):
            page.wait_for_timeout(1500)
            done = self._info(page)
            if done["submitted"]:
                return Result("applied", f"Submitted to {company} and confirmed.", fields, [], self._shot(page, job, "submitted"), page.url)
            if done["captcha"]:
                return Result("blocked", f"{company}'s site showed a CAPTCHA at Submit. Open your draft there and submit it yourself.",
                              fields, [], self._shot(page, job, "captcha"), page.url)
        return Result("unconfirmed", "Submit was pressed but no confirmation appeared. Check your email (and your "
                                     f"{company} account) before trying again.", fields, [], self._shot(page, job, "unconfirmed"), page.url)

    # ------------------------------------------------------------ steps
    _where = None

    def _box(self, page, q):
        """A question's block, found by Workday's own name (our markers vanish when the page re-renders)."""
        auto, nth = (self._where or {}).get(q.key, (None, 0))
        if auto:
            return page.locator(f'[data-automation-id="{auto}"]').nth(nth)
        return page.locator(f'[data-jobbot="{q.key}"]').first

    def _info(self, page):
        try:
            return page.evaluate(WD_JS)
        except Exception:
            page.wait_for_timeout(1500)
            return page.evaluate(WD_JS)

    def _click(self, page, selector):
        loc = page.locator(selector).first
        if not loc.count():
            return False
        try:
            loc.click(timeout=5000)
        except Exception:
            # Workday lays an invisible "click_filter" over its buttons.
            loc.evaluate("b => { const f = b.parentElement && b.parentElement.querySelector('[data-automation-id=click_filter]'); (f || b).click(); }")
        return True

    def _open_application(self, page):
        apply, app = '[data-automation-id="adventureButton"]', '[data-automation-id="progressBar"], [data-automation-id="email"]'
        start = '[data-automation-id="continueButton"], [data-automation-id="applyManually"]'
        try:
            page.wait_for_selector(f"{apply}, {app}", timeout=15000)
        except Exception:
            pass
        # A press of Apply before the page's scripts load does nothing: press again if nothing opened.
        for _ in range(3):
            if not self._click(page, apply):
                break
            try:
                page.wait_for_selector(f"{start}, {app}", timeout=5000)
                break
            except Exception:
                pass
        # A saved draft opens with "Continue Application"; a new one asks how to start.
        for sel in ('[data-automation-id="continueButton"]', '[data-automation-id="applyManually"]'):
            if page.locator(sel).count():
                self._click(page, sel)
                break
        try:
            page.wait_for_selector(app, timeout=30000)
        except Exception:
            return False
        self._wait_step(page)  # the progress bar shows a few seconds before the sign-in form or the step itself
        choice = page.get_by_role("button", name=re.compile(EMAIL_CHOICE, re.I))
        if choice.count():  # "Sign in with email" rather than Apple, Google or LinkedIn
            self._press(page, choice.first)
            self._wait_step(page)
        return True

    def _next(self, page, step):
        """Save and Continue, then wait for Workday to save: a new step or its error list (saving can take a while)."""
        after = None
        for _ in range(2):
            self._click(page, NEXT)
            for _ in range(10):
                page.wait_for_timeout(2000)
                after = self._info(page)
                if after["step"] != step or after["errors"] or after["captcha"] or after["submitted"]:
                    break
            if after["step"] != step or after["errors"]:
                break
            self.log(f"“{step}” didn't move on: pressing Save and Continue again")
        self._settle(page, 6000)
        self._wait_step(page)
        return self._info(page)

    def _wait_step(self, page, timeout=30000):
        """Wait out Workday's loading: until a sign-in form or a step's Next button shows, then until its fields stop changing.
        Workday's "Something went wrong. Please refresh the page" gets the refresh it asks for (twice at most)."""
        for attempt in range(3):
            try:
                page.wait_for_function(READY_JS, arg=f'[data-automation-id="email"], {NEXT}', timeout=timeout)
            except Exception:
                return  # a CAPTCHA, an email check or an error page: the caller looks at what's there
            if not re.search(WENT_WRONG, page.inner_text("body"), re.I) or attempt == 2:
                break
            self.log("Workday said “Something went wrong”: refreshing the page")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
        last = None
        for _ in range(10):
            page.wait_for_timeout(1500)
            n = page.locator("input, textarea, button").count()
            if n == last:
                return
            last = n

    def _account(self, page, job, email, pw, company):
        info = self._info(page)
        if not (info["signIn"] or info["createAccount"]):
            return None  # already signed in
        if info["createAccount"] and page.locator('[data-automation-id="signInLink"]').count():
            self._click(page, '[data-automation-id="signInLink"]')  # an account may exist from an earlier application
            page.wait_for_timeout(1500)
        self._type(page, '[data-automation-id="email"]', email)
        self._type(page, '[data-automation-id="password"]', pw)
        self._click(page, '[data-automation-id="signInSubmitButton"]')
        page.wait_for_timeout(3000)
        self._settle(page, 6000)
        self._wait_step(page)
        info = self._info(page)
        if info["signIn"] or info["createAccount"]:
            self.log(f"No {company} account yet: creating one for {email}")
            if not info["createAccount"]:
                self._click(page, '[data-automation-id="createAccountLink"]')
                page.wait_for_timeout(1500)
            self._type(page, '[data-automation-id="email"]', email)
            self._type(page, '[data-automation-id="password"]', pw)
            self._type(page, '[data-automation-id="verifyPassword"]', pw)
            box = page.locator('[data-automation-id="createAccountCheckbox"]')
            if box.count() and not box.first.is_checked():
                self._check(page, box.first)
            self._click(page, '[data-automation-id="createAccountSubmitButton"]')
            page.wait_for_timeout(3500)
            self._settle(page, 8000)
            self._wait_step(page)
            info = self._info(page)
        if info["captcha"]:
            return Result("blocked", f"{company}'s sign-in showed a CAPTCHA. Open the posting and sign in yourself once.",
                          screenshot=self._shot(page, job, "captcha"), url=page.url)
        if info["verify"]:
            return Result("blocked", f"{company} emailed a verification link to {email}. Open it to verify your account, "
                                     "then tap Try again.", screenshot=self._shot(page, job, "verify"), url=page.url)
        if info["signIn"] or info["createAccount"]:
            why = "; ".join(info["errors"][:3]) or "the site didn't accept the sign-in"
            return Result("needs_input", f"Couldn't sign in to {company}'s careers site: {why}.",
                          screenshot=self._shot(page, job, "signin"), url=page.url)
        return None

    def _type(self, page, selector, text):
        loc = page.locator(selector).first
        loc.click()
        loc.fill(text)

    # ------------------------------------------------------------ Workday widgets
    def _listbox_options(self, page, q):
        btn = self._box(page, q).locator('button[aria-haspopup="listbox"]').first
        try:
            self._close_lists(page)
            self._press(page, btn)
            page.wait_for_selector(OPTION, timeout=3000)
            opts = [t for t in self._options(page) if t]
            page.keyboard.press("Escape")
            return opts[:1000]  # some degree lists run to hundreds, medical degrees first
        except Exception:
            return []

    def _prompt_options(self, page, q):
        """A search prompt's first level ("Job Board", "Company Website"…), read by opening it."""
        try:
            inp = self._box(page, q).locator("input").first
            self._close_lists(page)
            self._press(page, inp)
            inp.press("Enter")
            page.wait_for_selector(OPTION, timeout=3000)
            opts = [t for t in self._options(page) if t and not NO_ITEMS.match(t)]  # a search box shows "No Items." until you type
            page.keyboard.press("Escape")
            return opts[:150]
        except Exception:
            return []

    def _wd_fill(self, page, q, a):
        box = self._box(page, q)
        want = [str(x) for x in ([a.option] if not isinstance(a.option, list) else a.option) + [a.value] + list(a.alternatives) if x]
        try:
            if q.input_type in ("wd_listbox", "wd_prompt"):
                self._close_lists(page)
            if q.input_type == "wd_listbox":
                self._press(page, box.locator('button[aria-haspopup="listbox"]').first)
                return self._pick(page, want)
            if q.input_type == "wd_prompt":
                inp = box.locator("input").first
                if SKILLS.search(norm(q.label)):
                    have = box.locator('[data-automation-id="selectedItem"]').all_inner_texts()
                    added = self._add_all(page, inp, [str(x) for x in [a.value, *a.alternatives] if x][:10], have)
                    if added:
                        a.value = a.option = added
                    return bool(added)
                for _ in range(5):  # replacing what's there: remove it first
                    if not box.locator('[data-automation-id="DELETE_charm"]').count():
                        break
                    self._press(page, box.locator('[data-automation-id="DELETE_charm"]').first)
                    page.wait_for_timeout(500)
                self._press(page, inp)
                inp.press("Enter")  # lists the first level
                page.wait_for_timeout(800)
                if not self._pick(page, want):
                    # A search pick is final. Workday may open the next field's list right after it, and
                    # picking from that would answer the wrong question.
                    found = self._search(page, inp, want, a)
                    page.keyboard.press("Escape")
                    return bool(found)
                page.wait_for_timeout(800)
                if self._opts(page).count():  # a second level ("Job Board" → "LinkedIn"…)
                    picked = self._pick(page, want + ["Other", "Company Website", "Careers Website"], any_ok=True)
                    if picked and picked not in want:
                        a.note = f"Chose “{picked}” in the second list"
                page.keyboard.press("Escape")
                return True
            if q.input_type in ("wd_date", "month", "wd_year") and SOON.search(str(a.value)):
                a.value = date.today().isoformat() if q.input_type == "wd_date" else date.today().strftime("%Y-%m")  # "Immediately"
            if q.input_type == "wd_date":  # month / day / year boxes: each one clicked and typed, as a person would
                m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(a.value))
                if not m:
                    return False
                for part, v in (("Month", m.group(2)), ("Day", m.group(3)), ("Year", m.group(1))):
                    el = box.locator(f'[data-automation-id="dateSection{part}-input"]').first
                    try:
                        el.click(timeout=3000)
                    except Exception:
                        el.focus()  # Workday lays its date picker over the boxes
                    page.keyboard.type(v, delay=60)
                return True
            if q.input_type in ("month", "wd_year"):
                m = re.match(r"(\d{4})-(\d{2})", str(a.value)) or re.match(r"(\d{1,2})/(\d{4})", str(a.value))
                year = re.search(r"\d{4}", str(a.value))
                if q.input_type == "month" and m:
                    mm, yy = (m.group(2), m.group(1)) if len(m.group(1)) == 4 else (m.group(1), m.group(2))
                    box.locator('[data-automation-id="dateSectionMonth-input"]').first.fill(mm.zfill(2))
                    box.locator('[data-automation-id="dateSectionYear-input"]').first.fill(yy)
                    return True
                if year:
                    box.locator('[data-automation-id="dateSectionYear-input"]').first.fill(year.group(0))
                    return True
                return False
            if q.kind == "checkboxes":  # "check all that apply"
                picks = a.option if isinstance(a.option, list) else [a.option]
                return all(self._check(page, box.get_by_label(str(o), exact=True).first) for o in picks if o)
            if q.kind == "radio":
                label = box.locator("label", has_text=re.compile(rf"^\s*{re.escape(str(a.option))}\s*$", re.I)).first
                label.click()
                return True
            if q.kind == "checkbox":
                if a.option or a.value in (True, "Yes", "yes"):
                    self._check(page, box.locator('input[type=checkbox]').first)
                return True
            if q.kind in ("text", "textarea"):
                el = box.locator("textarea, input").first
                el.fill(str(a.value))
                return True
        except Exception as e:
            self.log(f"Couldn't fill “{q.label[:60]}”: {str(e).splitlines()[0][:160]}")
        return False

    def _close_lists(self, page):
        """Close any list still open, so the next one's options aren't mixed up with it."""
        for _ in range(3):
            if not self._opts(page).count():
                return
            page.keyboard.press("Escape")
            page.evaluate("() => document.activeElement && document.activeElement.blur && document.activeElement.blur()")
            page.wait_for_timeout(500)

    def _opts(self, page):
        """The options showing now: a list Workday closed can linger hidden in the page."""
        return page.locator(OPTION).filter(visible=True)

    def _options(self, page):
        """The open list's options, once they've loaded past Workday's "Select One" placeholder."""
        texts = []
        for _ in range(10):
            texts = [t.strip() for t in self._opts(page).all_inner_texts()]
            if any(t and norm(t) != "select one" and not NO_ITEMS.match(t) for t in texts):
                break
            page.wait_for_timeout(500)
        return texts

    def _press(self, page, loc):
        """Click, even when Workday lays an invisible "click_filter", or a list left open, over it."""
        try:
            loc.click(timeout=5000)
        except Exception:
            page.keyboard.press("Escape")
            loc.evaluate("b => { const f = b.parentElement && b.parentElement.querySelector('[data-automation-id=click_filter]'); (f || b).click(); }")

    def _search(self, page, inp, want, a):
        """A search box: type the answer and pick it from what it finds. Schools that aren't listed are
        under "Other" ("Other - I do not see my school"), as Workday's own hint says."""
        terms = [a.search or str(a.value)] + list(a.alternatives)[:3] + [w for w in want if norm(w) == "other"]
        for term in dict.fromkeys(t for t in terms if t and t != "None"):
            page.keyboard.press("Escape")
            inp.fill(term)
            inp.press("Enter")
            page.wait_for_timeout(2000)
            hit = self._pick(page, want)
            if hit:
                a.note = a.note or (f"Chose “{hit}”" if norm(hit) != norm(str(a.value)) else "")
                return hit
        return False

    def _add_all(self, page, inp, terms, have=()):
        """A search box that takes many (skills): search each term and add its match, once each. Ones already
        chosen are left alone: pressing one again would remove it."""
        added, have = [], {norm(h) for h in have}
        for term in terms:
            page.keyboard.press("Escape")
            inp.fill(term)
            inp.press("Enter")
            page.wait_for_timeout(2000)
            try:
                page.wait_for_selector(OPTION, timeout=3000)
            except Exception:
                continue
            texts = self._options(page)
            hit = self._best_skill(term, [t for t in texts if not NO_ITEMS.match(t)])
            if hit and hit not in added and norm(hit) not in have:
                self._opts(page).nth(texts.index(hit)).click()
                added.append(hit)
                page.wait_for_timeout(600)
        page.keyboard.press("Escape")
        return added

    @staticmethod
    def _best_skill(term, opts):
        """"Excel" is "Excel" or "Microsoft Excel": only the skill itself, never a near miss ("Excel-DNA",
        "Lean Supply Chain Management" for "Supply Chain Management", "DP Operations" for "Operations")."""
        t = norm(term)
        return next((o for o in opts if norm(o) in (t, f"microsoft {t}", f"google {t}")), None)

    def _shown(self, page, q):
        """A required field Workday has hidden (the end date once "I currently work here" is ticked) isn't missing."""
        try:
            return self._box(page, q).is_visible()
        except Exception:
            return True

    def _clear(self, page, q):
        try:
            self._box(page, q).locator("textarea, input").first.fill("")
            return True
        except Exception:
            return False

    def _pick(self, page, want, any_ok=False):
        try:
            page.wait_for_selector(OPTION, timeout=3000)
        except Exception:
            return False
        opts, texts = self._opts(page), self._options(page)
        hit = next((pick_option(w, texts) for w in want if pick_option(w, texts)), None)
        if not hit and any_ok and texts:
            hit = texts[0]
        if not hit:
            page.keyboard.press("Escape")
            return False
        opts.nth(texts.index(hit)).click()
        page.wait_for_timeout(400)
        return hit

    def _attached(self, page, q, path):
        """Your resume is already in the draft (from an earlier run). Extra copies get removed."""
        box, name = self._box(page, q), Path(str(path)).name
        try:
            copies = box.inner_text().count(name)
            dels = box.locator('[data-automation-id="delete-file"]')
            while copies > 1 and dels.count() == copies:
                self._press(page, dels.last)
                page.wait_for_timeout(1500)
                copies = box.inner_text().count(name)
            return copies >= 1
        except Exception:
            return False

    def _upload(self, page, q, path):
        if not Path(str(path)).exists():
            return False
        self._box(page, q).locator("input[type=file]").first.set_input_files(str(path))
        page.wait_for_timeout(4000)  # Workday reads the resume and may fill in experience
        return True
