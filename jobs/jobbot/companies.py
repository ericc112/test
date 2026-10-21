"""The Fortune 500 list JobBot ships (config.FORTUNE500, from fortune500.json): who a company is,
for job cards and company profiles.

The file carries what the list itself publishes — rank, name, the company's website and careers page,
and the job systems it was found on. It has no industry, headquarters or headcount, so profiles show
only what's here rather than inventing the rest. Logos come from the company's own domain through a
free logo service (with a favicon service as the fallback) — no key, and a card simply shows no logo
when the company isn't in the file.
"""
from functools import lru_cache
from urllib.parse import urlparse

from . import config
from .sources import company_key

LOGO = "https://logo.clearbit.com/{domain}"
FAVICON = "https://www.google.com/s2/favicons?domain={domain}&sz=128"


def domain_of(website):
    host = urlparse(website or "").netloc or (website or "").split("/")[0]
    return host[4:] if host.startswith("www.") else host


@lru_cache(maxsize=1)
def _index():
    out = {}
    for row in config.FORTUNE500:
        key = company_key(row.get("name") or "")
        if key and key not in out:
            domain = domain_of(row.get("website"))
            out[key] = {"name": row.get("name"), "rank": row.get("rank"), "website": row.get("website"),
                        "careers": row.get("careers"), "systems": row.get("systems") or [],
                        "domain": domain or None,
                        "logo": LOGO.format(domain=domain) if domain else None,
                        "favicon": FAVICON.format(domain=domain) if domain else None}
    return out


def for_company(name):
    """The Fortune 500 entry for a company name as a job spells it ("Amazon.com Inc" → Amazon), or None."""
    return _index().get(company_key(name or ""))


def all_companies():
    return _index()
