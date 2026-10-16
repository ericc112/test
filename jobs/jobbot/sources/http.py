"""Tiny HTTP client: JSON GETs with a browser User-Agent, timeouts and polite retries."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .. import config


class FetchError(Exception):
    pass


def get(url, params=None, timeout=25, retries=2, accept="application/json"):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
    headers = {"User-Agent": config.USER_AGENT, "Accept": accept}
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.geturl(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                time.sleep(min(float(retry_after), 30) if retry_after and retry_after.isdigit() else delay)
                delay *= 2
                continue
            raise FetchError(f"HTTP {e.code} for {url}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise FetchError(f"{type(e).__name__}: {e} for {url}") from e
    raise FetchError(f"giving up on {url}")


def get_json(url, params=None, timeout=25, retries=2):
    _, body = get(url, params, timeout, retries)
    try:
        return json.loads(body)
    except ValueError as e:
        raise FetchError(f"invalid JSON from {url}") from e


def get_html(url, timeout=25):
    return get(url, timeout=timeout, retries=1, accept="text/html,application/xhtml+xml")
