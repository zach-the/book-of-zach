#!/usr/bin/env python3
"""
list_talks.py — Print talk URLs from a General Conference session page.

Usage:
    python3 list_talks.py https://www.churchofjesuschrist.org/study/general-conference/2026/04?lang=eng
"""

import re
import sys
import urllib.request
from urllib.parse import urlparse

# Matches the talk path anywhere in raw HTML/JSON, e.g. /study/general-conference/2026/04/13kearon
# or letter-slug talks like /study/general-conference/2004/04/gods-gift-to-his-children
TALK_PATH_RE = re.compile(r'/study/general-conference/(\d{4})/(\d{2})/([\w][\w-]*)')


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', errors='replace')


def list_talks(session_url: str) -> list[str]:
    parsed = urlparse(session_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    lang = "eng"
    if "lang=" in session_url:
        lang = session_url.split("lang=")[-1].split("&")[0]

    html = fetch(session_url)

    seen = set()
    urls = []
    for m in TALK_PATH_RE.finditer(html):
        path = m.group(0)
        if path not in seen:
            seen.add(path)
            urls.append(f"{base}{path}?lang={lang}")

    return urls


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        sys.exit(0 if sys.argv[1:] else 1)

    for url in list_talks(sys.argv[1]):
        print(url)


if __name__ == '__main__':
    main()
