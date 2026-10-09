#!/usr/bin/env python3
"""Tell IndexNow search engines (Bing, Yandex, Seznam, Naver, ...) that
cyberdeck.tools pages changed, so they re-crawl in minutes instead of days.

Run it AFTER the change is pushed and GitHub Pages has deployed — a ping
before that just gets the old page re-crawled. Tool bump scripts print the
exact command when a release is ready.

Usage:
    python indexnow.py                     # every URL in sitemap.xml
    python indexnow.py eidolon-ui          # one tool + its language pages (folder name ...)
    python indexnow.py https://cyberdeck.tools/eidolon-ui/   # ... or full URL

The key file (<KEY>.txt, next to this script) must be deployed at the site
root — that's how the engines verify the ping comes from the site owner.
One POST to api.indexnow.org is shared with every participating engine.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "cyberdeck.tools"
KEY = "618928754bdb4e2cc19267e1df0c74d8"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", xml)


def to_urls(arg, listed):
    """A tool folder or URL expands to every sitemap URL under it (its
    language pages too); the hub root stays just the hub root."""
    base = arg if arg.startswith("http") else f"https://{HOST}/{arg.strip('/')}/"
    if base == f"https://{HOST}/":
        return [base]
    return [u for u in listed if u.startswith(base)] or [base]


def main():
    listed = sitemap_urls()
    urls = [u for a in sys.argv[1:] for u in to_urls(a, listed)] or listed
    bad = [u for u in urls if not u.startswith(f"https://{HOST}/")]
    if bad:
        sys.exit(f"not on {HOST}: {', '.join(bad)}")

    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": urls}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except urllib.error.URLError as e:
        sys.exit(f"IndexNow not reached ({e.reason}) — nothing sent; try again when online")

    # 200 = accepted, 202 = accepted, key check pending; anything else is a problem
    meaning = {200: "accepted", 202: "accepted (key validation pending)",
               400: "bad request", 403: "key not valid — is the key file deployed?",
               422: "URLs don't match the host/key", 429: "too many requests — slow down"}
    print(f"IndexNow {status}: {meaning.get(status, 'unexpected response')}")
    for u in urls:
        print(f"  {u}")
    if status not in (200, 202):
        sys.exit(1)


if __name__ == "__main__":
    main()
