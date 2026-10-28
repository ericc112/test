"""Optional Claude integration: answer the questions JobBot's rules can't, and write cover letters.

Claude sees your profile, saved answers, resume text and the job posting, and gives the answer you
would give: the best one your information supports, so the application can go without asking you.
It never invents experience, grades, numbers or legal status. Every AI answer is labelled in the
review screen, and auto-submit holds AI-answered forms for you unless you allow it.
"""
import json
import os
import re

from .textutil import norm

SYSTEM = """You fill in job applications for the candidate whose profile, saved answers and resume follow, writing as them, in the first person. JobBot sends the application without asking them first, so give the answer they would give: the best one their information supports.

How to answer:
- Facts about the candidate (contact details, education, dates, work history, skills, location, citizenship and work authorization): take them from the profile and resume, together with what follows directly from them. Someone living in Texas is not a California resident; a U.S. citizen needs no visa sponsorship; years of experience add up from the resume's dates; a school is in the country where it is located.
- Saved answers are ones the candidate gave for other applications. Follow them for questions that ask the same thing in other words.
- Preferences and availability (start and end dates, cohort, term, office, location, team, shift, hours, travel, relocation): choose what fits both the candidate and this posting and keeps them eligible for it. Follow the posting's program dates and location, and pick the option nearest the candidate when several would work.
- Motivation and experience questions ("Why this company?", "Describe a project you led"): write a specific answer that connects the candidate's real experience and coursework to this job, usually 3-5 sentences, drawing only on what the resume says.
- Acknowledgements, consents and certifications (read and agree, consent to be contacted, certify that the information is accurate): agree.
- Conflicts of interest the material doesn't mention (relatives at the company, a non-compete, earlier employment there, government service): answer that none apply.
- Sensitive questions the material doesn't settle (criminal history, disability, veteran status, race, gender, sexual orientation): choose the option that declines to answer when there is one.

Mark a question not answerable only when the honest answer needs a fact that is not in the material and no option avoids stating it (a reference's contact details, a license number, a past salary). Never invent employers, titles, dates, degrees, grades, certifications, numbers or results, and never claim a legal or visa status the profile doesn't give. Never answer a question meant to prove the applicant is a human.

For a multiple-choice question, copy exactly one option from its list (or several, separated by " | ", where the question allows more than one). Write plain text: no markdown, no placeholders."""

# Credentials never leave this machine: the profile is serialised into an API call, so
# anything that looks like a password, secret, token or API key is dropped first.
_SECRET_KEY = re.compile(r"password|secret|token|api_key", re.I)

ANSWERS_SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "answerable": {"type": "boolean"},
                    "answer": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["key", "answerable", "answer", "note"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["answers"],
    "additionalProperties": False,
}

MAX_JOB_CHARS = 15000


class LLMError(Exception):
    pass


class Claude:
    def __init__(self, cfg):
        self.cfg = cfg
        self.key = (cfg.get("api_key") or os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        self.model = cfg.get("model") or "claude-opus-5-5"
        self.answer_enabled = bool(cfg.get("answer_questions", True))
        self.answer_optional = bool(cfg.get("answer_optional", False))
        self.write_cover_letters = bool(cfg.get("cover_letters", True))
        self._client = None

    @classmethod
    def from_settings(cls, cfg):
        """Return a client when AI is enabled and the SDK is installed, else None."""
        if not cfg.get("enabled"):
            return None
        try:
            import anthropic  # noqa: F401
        except ImportError:
            return None
        return cls(cfg)

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.key) if self.key else anthropic.Anthropic()
        return self._client

    def _system(self, ctx):
        p = ctx.profile
        profile = {k: v for k, v in p.items() if k not in ("resume_text", "cover_letter", "resume_file", "cover_letter_file") and not _SECRET_KEY.search(k) and v not in ("", None)}
        resume = p.get("resume_text") or "(no resume text available)"
        saved = "\n".join(f"- {e['q']}: {e['a']}" for e in list(ctx.bank or []) + list(ctx.learned or [])[:80]
                          if e.get("q") and e.get("a") not in (None, "", []))
        return [
            {"type": "text", "text": SYSTEM},
            {
                "type": "text",
                "text": f"<candidate_profile>\n{json.dumps(profile, indent=1)}\n</candidate_profile>\n\n"
                        f"<saved_answers>\nEach line: words or a pattern from a question, then the candidate's answer.\n"
                        f"{saved or '(none)'}\n</saved_answers>\n\n<resume>\n{resume}\n</resume>",
                "cache_control": {"type": "ephemeral"},
            },
        ]

    def _job(self, ctx):
        j = ctx.job
        desc = j.get("description") or ""
        if len(desc) > MAX_JOB_CHARS:
            desc = desc[:MAX_JOB_CHARS] + "\n[description truncated]"
        return f"<job>\nTitle: {j.get('title')}\nCompany: {j.get('company')}\nLocation: {j.get('location')}\n\n{desc}\n</job>"

    def _create(self, **kw):
        import anthropic
        try:
            resp = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                **kw,
            )
        except anthropic.AuthenticationError as e:
            raise LLMError("Anthropic API key was rejected. Check Settings → AI.") from e
        except anthropic.PermissionDeniedError as e:
            raise LLMError("This API key can't use the selected model.") from e
        except anthropic.NotFoundError as e:
            raise LLMError(f"Model {self.model!r} was not found.") from e
        except anthropic.RateLimitError as e:
            raise LLMError("Anthropic rate limit hit; try again in a minute.") from e
        except anthropic.APIStatusError as e:
            raise LLMError(f"Anthropic API error {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise LLMError("Couldn't reach the Anthropic API.") from e
        if resp.stop_reason == "refusal":
            return None
        return next((b.text for b in resp.content if b.type == "text"), None)

    def answer_questions(self, questions, ctx):
        """Return {question key: (answer, note)} for the questions Claude could answer."""
        if not self.answer_enabled or not questions:
            return {}
        items = []
        for q in questions:
            item = {"key": q.key, "question": q.label, "type": q.kind}
            if q.options:
                item["options"] = q.options
            if q.section:
                item["section"] = q.section  # e.g. "Start date year" of a past job, not availability
            if q.kind == "checkboxes":
                item["note"] = "Several options may apply; separate them with ' | '."
            items.append(item)
        text = self._create(
            system=self._system(ctx),
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": ANSWERS_SCHEMA}},
            messages=[{
                "role": "user",
                "content": f"{self._job(ctx)}\n\nAnswer these application questions:\n{json.dumps(items, indent=1)}",
            }],
        )
        if not text:
            return {}
        try:
            data = json.loads(text)
        except ValueError:
            return {}
        keys = {q.key: q for q in questions}
        out = {}
        for a in data.get("answers", []):
            q = keys.get(a.get("key"))
            if not q or not a.get("answerable") or not norm(a.get("answer", "")):
                continue
            value = a["answer"].strip()
            if q.kind == "checkboxes":
                value = [v.strip() for v in value.split("|") if v.strip()]
            out[q.key] = (value, a.get("note") or "Written by Claude")
        return out

    def cover_letter(self, ctx):
        text = self._create(
            system=self._system(ctx),
            output_config={"effort": "medium"},
            messages=[{
                "role": "user",
                "content": f"{self._job(ctx)}\n\nWrite a cover letter for this job: under 250 words, "
                           "three short paragraphs, specific to the role, grounded only in the resume. "
                           "Sign it with the candidate's name. Return only the letter text.",
            }],
        )
        return text.strip() if text else None
