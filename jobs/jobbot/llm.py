"""Optional Claude integration: answer leftover questions and write cover letters.

Claude only sees your profile, resume text and the job posting, and is told to
say "not answerable" rather than invent anything. Every AI answer is labelled
in the review screen, and auto-submit skips AI-answered forms unless you allow it.
"""
import json
import os

from .textutil import norm

SYSTEM = """You help a job seeker fill in job applications. You write on their behalf, in the first person.

Rules:
- Use only facts found in the candidate profile and resume below. Never invent employers, titles, dates, degrees, certifications, numbers, skills, legal or visa status, or personal details.
- If a question cannot be answered truthfully from that material, mark it not answerable. Leaving a question for the candidate is always better than guessing.
- For multiple-choice questions, answer with one option copied exactly from the list.
- Keep free-text answers specific and concise (2-5 sentences unless the question asks for more). Plain text, no markdown, no placeholders.
- Never answer questions that ask the applicant to prove they are human or to solve a puzzle meant for people."""

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
        profile = {k: v for k, v in p.items() if k not in ("resume_text", "cover_letter", "resume_file", "cover_letter_file") and v not in ("", None)}
        resume = p.get("resume_text") or "(no resume text available)"
        return [
            {"type": "text", "text": SYSTEM},
            {
                "type": "text",
                "text": f"<candidate_profile>\n{json.dumps(profile, indent=1)}\n</candidate_profile>\n\n<resume>\n{resume}\n</resume>",
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
