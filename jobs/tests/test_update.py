import io
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from jobbot import config, update


def archive(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(f"test-abc123/{name}", data)
    return buf.getvalue()


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="jobbot-update-"))
        (self.root / "jobbot").mkdir()
        (self.root / "data").mkdir()
        (self.root / "data" / "jobbot.db").write_text("yours")
        (self.root / "jobbot" / "gone.py").write_text("old")
        (self.root / "Start-JobBot.bat").write_text("old launcher")
        (self.root / "requirements.txt").write_text("a\n")
        (self.root / ".jobbot-files").write_text(json.dumps(["jobbot/gone.py", "requirements.txt", "Start-JobBot.bat"]))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_only_the_program_changes(self):
        changed, new_requirements = update.apply(archive({
            "jobs/jobbot/new.py": "new", "jobs/requirements.txt": "a\nb\n", "jobs/Start-JobBot.bat": "new launcher",
            "jobs/data/jobbot.db": "someone else's", "jobs/../../evil.txt": "x", "betting/other.py": "not ours"}), "sha1", self.root)
        self.assertEqual((self.root / "jobbot" / "new.py").read_text(), "new")
        self.assertFalse((self.root / "jobbot" / "gone.py").exists())  # removed upstream
        self.assertEqual((self.root / "data" / "jobbot.db").read_text(), "yours")  # your data is never touched
        self.assertEqual((self.root / "Start-JobBot.bat").read_text(), "old launcher")  # running: replaced on next start
        self.assertEqual((self.root / "Start-JobBot.new.bat").read_text(), "new launcher")
        self.assertFalse((self.root.parent / "evil.txt").exists())
        self.assertFalse((self.root / "other.py").exists())
        self.assertEqual((self.root / ".jobbot-version").read_text(), "sha1")
        self.assertTrue(new_requirements)
        self.assertEqual(changed, 3)

    def test_offline_starts_the_version_you_have(self):
        with mock.patch.object(update, "latest", side_effect=OSError("offline")), mock.patch.object(update, "apply") as apply:
            self.assertEqual(update.main(), 0)
        apply.assert_not_called()


class DataFolderTests(unittest.TestCase):
    """Your data lives in your user folder; the first start brings over what an earlier copy kept in jobs/data."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix="jobbot-downloads-"))
        self.saved = (config.ROOT, config.DATA_DIR, os.environ.pop("JOBBOT_DATA", None))

    def tearDown(self):
        config.ROOT, config.DATA_DIR, env = self.saved
        if env is not None:
            os.environ["JOBBOT_DATA"] = env
        shutil.rmtree(self.base, ignore_errors=True)

    def copy(self, name, with_data=False):
        jobs = self.base / name / "jobs"
        (jobs / "jobbot").mkdir(parents=True)
        if with_data:
            (jobs / "data" / "files").mkdir(parents=True)
            (jobs / "data" / "jobbot.db").write_text(f"db from {name}")
            (jobs / "data" / "files" / "resume.pdf").write_text("pdf")
        return jobs

    def test_a_new_download_picks_up_the_old_copys_data(self):
        self.copy("jobbot-ready", with_data=True)
        config.ROOT, config.DATA_DIR = self.copy("test-main"), self.base / "user" / "JobBot"
        came = config.adopt_old_data()
        self.assertEqual(came, self.base / "jobbot-ready" / "jobs" / "data")
        self.assertEqual((config.DATA_DIR / "jobbot.db").read_text(), "db from jobbot-ready")
        self.assertTrue((config.DATA_DIR / "files" / "resume.pdf").exists())
        self.assertIsNone(config.adopt_old_data())  # once only: after that, your user folder is the one

    def test_nothing_to_bring(self):
        config.ROOT, config.DATA_DIR = self.copy("test-main"), self.base / "user" / "JobBot"
        self.assertIsNone(config.adopt_old_data())


if __name__ == "__main__":
    unittest.main()
