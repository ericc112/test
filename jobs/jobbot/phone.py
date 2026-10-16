"""Phone access: let other devices on your network open JobBot with a private link.

`python -m jobbot --phone` listens on your network as well as on localhost. Your
computer stays trusted as before; any other device must first open the private link
(it carries a random key), which leaves a cookie so the phone stays signed in. The
key lives in data/phone_key; resetting it signs every phone out.
"""
import hmac
import os
import secrets
import socket

from . import config

COOKIE = "jobbot_key"
LOOPBACK = {"127.0.0.1", "::1", "localhost"}
ADDRESS = None  # --phone-address: e.g. the computer's Tailscale name, for use away from home Wi-Fi


def _path():
    return config.DATA_DIR / "phone_key"


def key():
    p = _path()
    if p.exists():
        k = p.read_text().strip()
        if len(k) >= 20:
            return k
    return reset()


def reset():
    config.ensure_dirs()
    k = secrets.token_urlsafe(24)
    p = _path()
    p.write_text(k)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return k


def check(candidate):
    return bool(candidate) and hmac.compare_digest(str(candidate), key())


def lan_ip():
    """This computer's address on the local network (what your phone connects to)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # picks the outgoing interface; nothing is sent
        return s.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "localhost"  # no network: only this computer can connect anyway
    finally:
        s.close()


def link(port, host=None):
    return f"http://{host or ADDRESS or lan_ip()}:{port}/?key={key()}"


def qr_svg(text):
    """The link as an inline SVG QR code, or None if segno isn't installed."""
    try:
        import segno
    except ImportError:
        return None
    return segno.make(text, error="m").svg_inline(scale=5, dark="#111", light="#fff")


def qr_terminal(text):
    try:
        import segno
    except ImportError:
        return False
    segno.make(text, error="m").terminal(compact=True)
    return True
