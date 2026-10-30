"""Bring this copy of JobBot up to date from GitHub, before it starts (Start-JobBot.bat runs `py -m jobbot.update`).

Only the program changes: your data lives in your user folder (see config.DATA_DIR), never in the jobs folder. Uses
nothing but Python itself, so it works before the first install of JobBot's packages. Offline, it just says so and
the copy you have starts.
"""
import io
import json
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO, BRANCH, FOLDER = "ericc112/test", "main", "jobs"
ROOT = Path(__file__).resolve().parent.parent
VERSION, MANIFEST = ".jobbot-version", ".jobbot-files"
KEEP = {"data", ".jobbot-setup-done", VERSION, MANIFEST}
LAUNCHER = "Start-JobBot.bat"  # running while we update: its new version waits as Start-JobBot.new.bat


def _get(url, accept="application/vnd.github+json", timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "JobBot-updater", "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def latest():
    return _get(f"https://api.github.com/repos/{REPO}/commits/{BRANCH}", accept="application/vnd.github.sha").decode().strip()


def download(sha):
    return _get(f"https://codeload.github.com/{REPO}/zip/{sha}", accept="application/zip", timeout=120)


def apply(archive, sha, root=ROOT):
    """Write the jobs folder from a GitHub zip into root: changed files only, files gone from it removed."""
    z = zipfile.ZipFile(io.BytesIO(archive))
    top = z.namelist()[0].split("/")[0]
    prefix = f"{top}/{FOLDER}/"
    root = Path(root).resolve()
    req_before = (root / "requirements.txt").read_bytes() if (root / "requirements.txt").exists() else b""
    written, changed = [], 0
    for info in z.infolist():
        if info.is_dir() or not info.filename.startswith(prefix):
            continue
        rel = info.filename[len(prefix):]
        if not rel or rel.split("/")[0] in KEEP:
            continue
        target = (root / rel).resolve()
        if root not in target.parents:
            continue  # never outside the jobs folder
        data = z.read(info)
        written.append(rel)
        if target.exists() and target.read_bytes() == data:
            continue
        if rel == LAUNCHER and target.exists():
            target = root / "Start-JobBot.new.bat"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        changed += 1
    try:
        before = json.loads((root / MANIFEST).read_text())
    except (OSError, ValueError):
        before = []
    for rel in set(before) - set(written):
        gone = (root / rel).resolve()
        if root in gone.parents and gone.is_file():
            gone.unlink()
    (root / MANIFEST).write_text(json.dumps(sorted(written)))
    (root / VERSION).write_text(sha)
    return changed, (root / "requirements.txt").read_bytes() != req_before


def main():
    try:
        sha = latest()
    except Exception:
        print("Couldn't check for a newer JobBot (offline?). Starting the version you have.")
        return 0
    have = (ROOT / VERSION).read_text().strip() if (ROOT / VERSION).exists() else ""
    if have == sha:
        print("JobBot is up to date.")
        return 0
    print("Updating JobBot to the latest version...")
    try:
        changed, new_requirements = apply(download(sha), sha)
    except Exception as e:
        print(f"Couldn't update JobBot ({e}). Starting the version you have.")
        return 0
    if new_requirements and (ROOT / ".jobbot-setup-done").exists():
        subprocess.call([sys.executable, "-m", "pip", "install", "-q", "-r", str(ROOT / "requirements.txt")])
    print(f"Updated ({changed} file(s) changed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
