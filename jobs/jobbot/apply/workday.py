"""Applying on Workday career sites (about 200 of the Fortune 500).

Workday wants an account with each employer. JobBot signs in with your email and the
password in the JOBBOT_WORKDAY_PASSWORD environment variable (or Profile → Workday
password), creating the account the first time. It then fills My Information, My
Experience (your resume), Application Questions and Voluntary Disclosures, pressing
"Save and Continue" after each, and stops at Review: the draft is saved in your account
there and nothing has gone to the employer. Submitting signs in again, reopens the saved
application and presses Submit on the Review step.

It stops for you, without working around them, at CAPTCHAs, email verification and
anything it can't answer, and it never touches Workday's hidden bot-trap field.
"""
import os
import re
from pathlib import Path

from ..answers import Question, answer_all, as_dict, missing
from ..textutil import norm, pick_option
from .engine import Engine, Result

WD_JS = Path(__file__).with_name("wd_extract.js").read_text()
NEXT = '[data-automation-id="bottom-navigation-next-button"], [data-automation-id="pageFooterNextButton"]'
OPTION = '[role="listbox"] [role="option"], [data-automation-id="promptOption"], [data-automation-id="menuItem"]'
PASSWORD_RULES = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def password(profile):
    return os.environ.get("JOBBOT_WORKDAY_PASSWORD") or profile.get("workday_password") or ""


def is_workday(job):
    return job.get("source") == "workday" or "myworkdayjobs.com" in (job.get("url") or job.get("apply_url") or "")


class WorkdayEngine(Engine):
    MAX_STEPS = 10

    def _run(self, page, job, ctx, url, mode):
        email, pw = (ctx.profile.get("email") or "").strip(), password(ctx.profile)
        if not email or not pw:
            return Result("needs_input", "Add your email and a Workday password first: Workday needs an account with each employer.")
        if not PASSWORD_RULES.match(pw):
            return Result("needs_input", "Your Workday password needs 8+ characters with upper and lower case letters, a number and a symbol.")
        company = job.get("company") or "the employer"
        self.log(f"Opening {job.get('url')}")
        page.goto(job.get("url"), wait_until="domcontentloaded", timeout=45000)
        self._settle(page)
        if not self._open_application(page):
            return Result("error", "Couldn't find the Apply button on this Workday posting.",
                          screenshot=self._shot(page, job, "noapply"), url=page.url)
        self._where = {}
        stop = self._account(page, job, email, pw, company)
        if stop:
            return stop

        questions, answers, seen = [], {}, set()
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
            new = answer_all(qs, ctx)
            for q in qs:
                a = new[q.key]
                if q.kind == "file":
                    if a.value and self._upload(page, q, a.value):
                        a.note = "Uploaded to your draft (not sent until you submit)"
                    continue
                if q.value not in (None, "", False) and norm(q.label) not in ctx.overrides:
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
            self._click(page, NEXT)
            page.wait_for_timeout(2500)
            self._settle(page, 6000)
            after = self._info(page)
            if after["step"] == step and "review" not in step.lower():
                # Still on the same step: Workday says what's missing.
                miss = [q for q in qs if q.required and not new[q.key].resolved(q)] or \
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
        if self._click(page, '[data-automation-id="adventureButton"]'):
            page.wait_for_timeout(2000)
        # A saved draft opens with "Continue Application"; a new one asks how to start.
        for sel in ('[data-automation-id="continueButton"]', '[data-automation-id="applyManually"]'):
            if page.locator(sel).count():
                self._click(page, sel)
                break
        try:
            page.wait_for_selector('[data-automation-id="progressBar"], [data-automation-id="email"]', timeout=30000)
        except Exception:
            return False
        page.wait_for_timeout(1500)
        return True

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
            btn.click(timeout=4000)
            page.wait_for_selector(OPTION, timeout=3000)
            opts = [t.strip() for t in page.locator(OPTION).all_inner_texts() if t.strip()]
            page.keyboard.press("Escape")
            return opts[:150]
        except Exception:
            return []

    def _prompt_options(self, page, q):
        """A search prompt's first level ("Job Board", "Company Website"…), read by opening it."""
        try:
            inp = self._box(page, q).locator("input").first
            inp.click(timeout=4000)
            inp.press("Enter")
            page.wait_for_selector(OPTION, timeout=3000)
            opts = [t.strip() for t in page.locator(OPTION).all_inner_texts() if t.strip()]
            page.keyboard.press("Escape")
            return opts[:150]
        except Exception:
            return []

    def _wd_fill(self, page, q, a):
        box = self._box(page, q)
        want = [str(x) for x in ([a.option] if not isinstance(a.option, list) else a.option) + [a.value] + list(a.alternatives) if x]
        try:
            if q.input_type == "wd_listbox":
                box.locator('button[aria-haspopup="listbox"]').first.click()
                return self._pick(page, want)
            if q.input_type == "wd_prompt":
                inp = box.locator("input").first
                inp.click()
                inp.press("Enter")  # lists the first level
                page.wait_for_timeout(800)
                if not self._pick(page, want):
                    return False
                page.wait_for_timeout(800)
                if page.locator(OPTION).count():  # a second level ("Job Board" → "LinkedIn"…)
                    picked = self._pick(page, want + ["Other", "Company Website", "Careers Website"], any_ok=True)
                    if picked and picked not in want:
                        a.note = f"Chose “{picked}” in the second list"
                page.keyboard.press("Escape")
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

    def _pick(self, page, want, any_ok=False):
        try:
            page.wait_for_selector(OPTION, timeout=3000)
        except Exception:
            return False
        opts = page.locator(OPTION)
        texts = [t.strip() for t in opts.all_inner_texts()]
        hit = next((pick_option(w, texts) for w in want if pick_option(w, texts)), None)
        if not hit and any_ok and texts:
            hit = texts[0]
        if not hit:
            page.keyboard.press("Escape")
            return False
        opts.nth(texts.index(hit)).click()
        page.wait_for_timeout(400)
        return hit

    def _upload(self, page, q, path):
        if not Path(str(path)).exists():
            return False
        self._box(page, q).locator("input[type=file]").first.set_input_files(str(path))
        page.wait_for_timeout(4000)  # Workday reads the resume and may fill in experience
        return True
