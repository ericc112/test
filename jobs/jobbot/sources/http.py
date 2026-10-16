"""Tiny HTTP client: JSON requests with a browser User-Agent, timeouts and polite retries.

Conditional requests: pass conditional=True and the response's ETag is remembered;
the next request for the same URL sends If-None-Match, and an unchanged feed answers
304 with no body, raised here as NotModified. That makes checking an employer's job
board every few minutes nearly free for both sides.
"""
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from .. import config


class FetchError(Exception):
    pass


class NotModified(Exception):
    """The feed hasn't changed since the last conditional request."""


_etags = {}
_etag_lock = threading.Lock()


def forget_etags():
    with _etag_lock:
        _etags.clear()


def get(url, params=None, timeout=25, retries=2, accept="application/json", conditional=False,
        data=None, content_type=None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
    headers = {"User-Agent": config.USER_AGENT, "Accept": accept}
    if content_type:
        headers["Content-Type"] = content_type
    if conditional:
        with _etag_lock:
            etag = _etags.get(url)
        if etag:
            headers["If-None-Match"] = etag
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers, data=data, method="POST" if data is not None else "GET")
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                if conditional and r.headers.get("ETag"):
                    with _etag_lock:
                        _etags[url] = r.headers["ETag"]
                return r.geturl(), body
        except urllib.error.HTTPError as e:
            if e.code == 304 and conditional:
                raise NotModified(url) from None
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


def _parse(url, body):
    try:
        return json.loads(body)
    except ValueError as e:
        raise FetchError(f"invalid JSON from {url}") from e


def get_json(url, params=None, timeout=25, retries=2, conditional=False):
    _, body = get(url, params, timeout, retries, conditional=conditional)
    return _parse(url, body)


def post_json(url, payload, timeout=25, retries=2):
    _, body = get(url, timeout=timeout, retries=retries, data=json.dumps(payload).encode(),
                  content_type="application/json")
    return _parse(url, body)


def get_html(url, timeout=25):
    return get(url, timeout=timeout, retries=1, accept="text/html,application/xhtml+xml")
