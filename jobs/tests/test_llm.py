import json
import unittest
from types import SimpleNamespace
from unittest import mock

from jobbot.answers import Context, Question
from jobbot.llm import Claude

from .helpers import PROFILE


def response(text, stop="end_turn"):
    return SimpleNamespace(stop_reason=stop, content=[SimpleNamespace(type="text", text=text)])


class ClaudeTests(unittest.TestCase):
    def setUp(self):
        self.claude = Claude({"enabled": True, "api_key": "sk-test", "model": "claude-opus-5-5"})
        self.create = mock.MagicMock()
        self.claude._client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=self.create)))
        self.ctx = Context(profile=dict(PROFILE, resume_text="8 years of Python."),
                           job={"title": "Backend Engineer", "company": "Acme", "description": "Build APIs"})

    def test_batch_request_shape_and_parsing(self):
        self.create.return_value = response(json.dumps({"answers": [
            {"key": "q1", "answerable": True, "answer": "I built Python APIs for 8 years.", "note": "From resume"},
            {"key": "q2", "answerable": False, "answer": "", "note": "Not in resume"},
            {"key": "q3", "answerable": True, "answer": "Python | Go", "note": ""},
        ]}))
        qs = [Question("q1", "textarea", "Describe your API experience", True),
              Question("q2", "text", "What is your clearance level?", True),
              Question("q3", "checkboxes", "Languages you use", True, options=["Python", "Go", "Rust"])]
        out = self.claude.answer_questions(qs, self.ctx)
        self.assertEqual(out["q1"][0], "I built Python APIs for 8 years.")
        self.assertNotIn("q2", out)
        self.assertEqual(out["q3"][0], ["Python", "Go"])
        kw = self.create.call_args.kwargs
        self.assertEqual(kw["model"], "claude-opus-5-5")
        self.assertEqual(kw["fallbacks"], "default")
        self.assertEqual(kw["betas"], ["server-side-fallback-2026-07-01"])
        self.assertEqual(kw["output_config"]["format"]["type"], "json_schema")
        self.assertIn("8 years of Python.", kw["system"][1]["text"])
        self.assertIn("Describe your API experience", kw["messages"][0]["content"])

    def test_profile_secrets_never_reach_the_api(self):
        profile = dict(self.ctx.profile, workday_password="<redacted>", api_key="<redacted>",
                       client_secret="<redacted>", auth_token="<redacted>")
        ctx = Context(profile=profile, job=self.ctx.job)
        self.create.return_value = response(json.dumps({"answers": []}))
        self.claude.answer_questions([Question("q1", "text", "Why us?", True)], ctx)
        sent = self.create.call_args.kwargs["system"][1]["text"]
        for secret in ("hunter2-wd", "sk-secret-123", "shh-value", "tok-abc"):
            self.assertNotIn(secret, sent)
        for key in ("workday_password", "api_key", "client_secret", "auth_token"):
            self.assertNotIn(key, sent)
        self.assertIn("Test", sent)  # ordinary profile fields still go

    def test_refusal_returns_nothing(self):
        self.create.return_value = response("", stop="refusal")
        self.assertEqual(self.claude.answer_questions([Question("q1", "text", "Why us?", True)], self.ctx), {})

    def test_cover_letter(self):
        self.create.return_value = response("  Dear Acme team,\n\nHello.  ")
        self.assertEqual(self.claude.cover_letter(self.ctx), "Dear Acme team,\n\nHello.")

    def test_disabled_returns_none(self):
        self.assertIsNone(Claude.from_settings({"enabled": False}))


if __name__ == "__main__":
    unittest.main()
