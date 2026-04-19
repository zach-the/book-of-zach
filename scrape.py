#!/usr/bin/env python3
"""
scrape.py — Convert General Conference talks or BYU speeches to LaTeX.

Usage:
    python3 scrape.py URL [URL ...] -o talks.tex   # write to file
    python3 scrape.py URL [URL ...]                 # print to stdout

Then bookletize with:
    ./make_booklet.sh talks.tex

Supported sources:
    https://www.churchofjesuschrist.org/study/general-conference/...
    https://speeches.byu.edu/talks/...
"""

import calendar
import json
import re
import sys
import argparse
import urllib.request
from urllib.parse import urlparse, urlencode

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    sys.exit("Missing dependency: pip3 install beautifulsoup4 lxml")

# ── LaTeX preamble ─────────────────────────────────────────────────────────────

PREAMBLE = r"""%!TEX program = lualatex
\documentclass[letterpaper, 11pt]{report}
\usepackage{fontspec}
\usepackage{fancyhdr}

%%% MARGINS %%%
% use this for normal letter documents
% \usepackage[
%     letterpaper,
%     margin=1in,
%     includehead
% ]{geometry}

%use this for bookletized pdfs
\usepackage[
    paperwidth=6.875in,
    paperheight=10.625in,
    margin=0.75in,     % Now your margins will be exactly what you type
    includehead
]{geometry}

%%% FONT %%%
\setmainfont{Liberation Serif}

%%% SPEAKER \& TALK VARIABLES %%%
\newcommand{\speaker}{}
\newcommand{\talk}{}
\newcommand{\talkdatestr}{}
\newcommand{\setspeaker}[1]{\renewcommand{\speaker}{#1}}
\newcommand{\settalk}[1]{\renewcommand{\talk}{#1}}
\newcommand{\settalkdate}[1]{\renewcommand{\talkdatestr}{#1}}

%%% HEADER \& FOOTER SETUP %%%
\pagestyle{fancy}
\fancyhf{}

\fancyhead[L]{\textbf{\talk}}
\fancyhead[R]{\textbf{\speaker}}

\renewcommand{\headrulewidth}{0.4pt}

%%% CUSTOM HEADER CLASS FOR TALK TITLE %%%
\newcommand{\talkheading}[2]{%
    \vspace{1em}
    \noindent{\huge\bfseries #1}
    \par\nopagebreak\vspace{0.25em}
    \noindent{\normalsize\bfseries #2\ifx\talkdatestr\empty\else,\ \talkdatestr\fi}
    \par\nopagebreak\vspace{0.5em}
}

%%% IN-TALK HEADERS
\newcommand{\intalkheader}[1]{
    \vspace{0.75em}
    \noindent{\normalsize\bfseries #1}
    \par\nopagebreak % Prevents a break immediately after the text
    \vspace{0.25em}
    \nopagebreak     % Prevents a break after the whitespace
}

\begin{document}
"""

# ── LaTeX escaping ─────────────────────────────────────────────────────────────

_SPECIAL = re.compile(r'[\\&%$#_{}~^]')
_ESCAPE_MAP = {
    '\\': r'\textbackslash{}',
    '&':  r'\&',
    '%':  r'\%',
    '$':  r'\$',
    '#':  r'\#',
    '_':  r'\_',
    '{':  r'\{',
    '}':  r'\}',
    '~':  r'\textasciitilde{}',
    '^':  r'\textasciicircum{}',
}

def tex(text: str) -> str:
    """Escape LaTeX special characters; normalize non-breaking spaces."""
    text = text.replace('\xa0', ' ')
    return _SPECIAL.sub(lambda m: _ESCAPE_MAP[m.group()], text)


def clean(el) -> str:
    """Get normalized, LaTeX-escaped plain text from a BeautifulSoup element."""
    raw = el.get_text()
    raw = raw.replace('\xa0', ' ')
    raw = re.sub(r'\s+', ' ', raw).strip()
    return tex(raw)


# ── HTTP fetch ─────────────────────────────────────────────────────────────────

def normalize_url(url: str) -> str:
    url = url.strip().strip('"\'')
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url


def fetch(url: str) -> str:
    url = normalize_url(url)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8', errors='replace')


def fetch_church_api(talk_url: str) -> str:
    """Return the full talk body HTML via the church content API."""
    parsed = urlparse(normalize_url(talk_url))
    lang = 'eng'
    for part in (parsed.query or '').split('&'):
        if part.startswith('lang='):
            lang = part[5:]
    uri = parsed.path.removeprefix('/study')
    api = (f"https://www.churchofjesuschrist.org/study/api/v3/language-pages"
           f"/type/content?lang={lang}&uri={uri}")
    raw = fetch(api)
    data = json.loads(raw)
    return data['content']['body']


def date_from_church_url(url: str) -> str:
    m = re.search(r'/general-conference/(\d{4})/(\d{2})/', url)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        return f"{calendar.month_name[month]} {year}"
    return ""


# ── Church of Jesus Christ scraper ────────────────────────────────────────────

_CHURCH_TITLE_RE = re.compile(
    r'^(President|Elder|Sister|Brother|Bishop|Acting\s+President'
    r'|Hermana|Anciano|Presidente)\s+', re.I
)

def _church_author(soup) -> str:
    p = soup.find('p', class_='author-name')
    if not p:
        byline = soup.find('div', class_='byline')
        raw = byline.get_text() if byline else 'Unknown'
    else:
        raw = p.get_text()
    raw = re.sub(r'\s+', ' ', raw).strip()
    raw = re.sub(r'^By\s+', '', raw)
    raw = _CHURCH_TITLE_RE.sub('', raw)
    return raw.strip()


def _parse_body_block(body) -> list:
    blocks = []
    for el in body.descendants if False else body.children:
        if not isinstance(el, Tag):
            continue
        name = el.name
        classes = el.get('class', [])

        if name == 'p':
            text = clean(el)
            if text:
                blocks.append(text)

        elif name == 'section':
            header = el.find('header')
            if header:
                for hx in header.find_all(['h2', 'h3']):
                    text = clean(hx)
                    if text:
                        blocks.append(f'\\intalkheader{{{text}}}')
            for child in el.children:
                if not isinstance(child, Tag):
                    continue
                if child.name == 'p':
                    text = clean(child)
                    if text:
                        blocks.append(text)
                elif child.name == 'header':
                    pass  # already handled above
                elif child.name == 'div' and 'poetry' in child.get('class', []):
                    blocks.extend(_parse_poetry(child))
                elif child.name == 'section':
                    blocks.extend(_parse_body_block(child))

        elif name == 'div' and 'poetry' in classes:
            blocks.extend(_parse_poetry(el))

    return blocks


def _parse_poetry(el) -> list:
    blocks = []
    stanza = el.find('div', class_='stanza')
    citation = el.find('div', class_='citation-info')
    if stanza:
        lines = [l.strip() for l in stanza.get_text().splitlines() if l.strip()]
        joined = '\\\\\n'.join(tex(l) for l in lines)
        blocks.append(f'\\begin{{verse}}\n{joined}\n\\end{{verse}}')
    if citation:
        blocks.append(clean(citation))
    return blocks


def scrape_church(soup, talk_url: str = None) -> tuple:
    h1 = soup.find('h1', {'data-aid': True}) or soup.find('h1')
    if not h1:
        raise ValueError("Could not find talk title — is this a talk URL?")
    title = h1.get_text(strip=True)
    author = _church_author(soup)

    body = soup.find('div', class_='body-block')
    if not body:
        raise ValueError("Could not find talk body (div.body-block)")

    return title, author, _parse_body_block(body)


# ── BYU speeches scraper ──────────────────────────────────────────────────────

def scrape_byu(soup) -> tuple:
    h1 = soup.find('h1', class_='single-speech__title')
    if not h1:
        raise ValueError("Could not find talk title — is this a BYU Speeches URL?")
    title = h1.get_text(strip=True)

    author_h2 = soup.find('h2', class_='single-speech__speaker')
    author = author_h2.get_text(strip=True) if author_h2 else 'Unknown'

    content = soup.find('div', class_='single-speech__content')
    if not content:
        raise ValueError("Could not find talk content (div.single-speech__content)")

    blocks = []
    for el in content.children:
        if not isinstance(el, Tag):
            continue
        name = el.name

        if name == 'p':
            text = clean(el)
            if text:
                blocks.append(text)

        elif name in ('h2', 'h3'):
            text = clean(el)
            if text:
                blocks.append(f'\\intalkheader{{{text}}}')

        elif name == 'ul':
            for li in el.find_all('li', recursive=False):
                text = clean(li)
                if text:
                    blocks.append(f'- {text}')

        elif name == 'ol':
            for i, li in enumerate(el.find_all('li', recursive=False), 1):
                text = clean(li)
                if text:
                    blocks.append(f'{i}. {text}')

        elif name == 'blockquote':
            text = clean(el)
            if text:
                blocks.append(text)

        # figure, div, audio, video, nav, footer, etc. → skip

    return title, author, blocks


# ── Render one talk ────────────────────────────────────────────────────────────

def render_talk(title: str, author: str, blocks: list, date: str = '') -> str:
    title_tex = tex(title)
    author_tex = tex(author)
    lines = [
        r'\newpage',
        f'\\settalk{{{title_tex}}}',
        f'\\setspeaker{{{author_tex}}}',
        f'\\settalkdate{{{tex(date)}}}',
        f'\\talkheading{{{title_tex}}}{{{author_tex}}}',
        '',
    ]
    for block in blocks:
        lines.append(block)
        lines.append('')
    return '\n'.join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def url_to_talk(url: str) -> tuple:
    url = normalize_url(url)
    print(f'  fetching {url} ...', file=sys.stderr)
    if 'churchofjesuschrist.org' in url:
        body_html = fetch_church_api(url)
        soup = BeautifulSoup(body_html, 'lxml')
        title, author, blocks = scrape_church(soup, url)
        return title, author, blocks, date_from_church_url(url)
    elif 'speeches.byu.edu' in url:
        title, author, blocks = scrape_byu(soup)
        return title, author, blocks, ''
    else:
        raise ValueError(
            f"Unsupported domain. Expected churchofjesuschrist.org or speeches.byu.edu\n"
            f"  Got: {url}"
        )


def main():
    parser = argparse.ArgumentParser(
        description='Scrape LDS talks or BYU speeches into a LaTeX booklet.',
        epilog='Bookletize with: ./make_booklet.sh output.tex',
    )
    parser.add_argument('urls', nargs='+', metavar='URL')
    parser.add_argument('-o', '--output', metavar='FILE',
                        help='Output .tex file (default: stdout)')
    args = parser.parse_args()

    talk_parts = []
    errors = []
    for url in args.urls:
        try:
            title, author, blocks, date = url_to_talk(url)
            talk_parts.append(render_talk(title, author, blocks, date))
            print(f'  OK: {title} — {author}', file=sys.stderr)
        except Exception as e:
            print(f'  ERROR: {url}\n    {e}', file=sys.stderr)
            errors.append(url)

    if not talk_parts:
        sys.exit("No talks were successfully scraped.")

    output = PREAMBLE + '\n'.join(talk_parts) + '\n\\end{document}\n'

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f'\nWrote {len(talk_parts)} talk(s) to {args.output}', file=sys.stderr)
        if errors:
            print(f'{len(errors)} URL(s) failed — see errors above', file=sys.stderr)
    else:
        sys.stdout.write(output)


if __name__ == '__main__':
    main()
