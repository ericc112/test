"""Point JobBot at a throwaway data directory for each test."""
import shutil
import tempfile
from pathlib import Path

from jobbot import config, db

FIXTURES = Path(__file__).with_name("fixtures")

PROFILE = dict(
    config.DEFAULT_PROFILE,
    first_name="Test", last_name="Applicant", email="test@example.com", phone="415-555-0134",
    city="San Francisco", state="California", country="United States",
    linkedin="https://www.linkedin.com/in/test", github="https://github.com/test", website="https://example.com",
    current_company="Example Corp", current_title="Software Engineer", years_experience="8",
    school="University of California, Berkeley", degree="Bachelor's", discipline="Computer Science",
    graduation_year="2016", skills="python, go, aws", summary="I build backend systems.",
)


class TempData:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="jobbot-test-"))
        self._saved = {k: getattr(config, k) for k in ("DATA_DIR", "DB_PATH", "FILES_DIR", "SHOTS_DIR")}
        config.DATA_DIR = self.dir
        config.DB_PATH = self.dir / "jobbot.db"
        config.FILES_DIR = self.dir / "files"
        config.SHOTS_DIR = self.dir / "screenshots"
        config.ensure_dirs()

    def close(self):
        for k, v in self._saved.items():
            setattr(config, k, v)
        db._initialized.discard(str(self.dir / "jobbot.db"))
        shutil.rmtree(self.dir, ignore_errors=True)


def browser_available():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False
