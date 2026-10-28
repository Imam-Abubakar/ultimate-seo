"""Shared helpers for the ultimate-seo scripts.

Standard library only (Python 3.9+), so the scripts run anywhere Claude can
run Python, with nothing to install.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, Iterator, List, Optional, Tuple

USER_AGENT = "Mozilla/5.0 (compatible; ultimate-seo-audit/1.0)"
VOID_TEXT_TAGS = {"script", "style", "noscript", "template", "svg"}
HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
SKIP_DIRS = {
    "node_modules", ".git", ".next", ".nuxt", ".svelte-kit", ".astro", ".cache",
    "__pycache__", ".venv", "venv", ".turbo", "coverage", "vendor", ".idea", ".vscode",
}


@dataclass
class Image:
    src: str
    alt: Optional[str]
    width: Optional[str]
    height: Optional[str]
    loading: Optional[str]


@dataclass
class Anchor:
    href: Optional[str]
    text: str
    rel: str = ""
    has_onclick: bool = False


@dataclass
class Page:
    """Everything the audit needs from one HTML document."""

    url: str
    status: int = 200
    html_lang: Optional[str] = None
    titles: List[str] = field(default_factory=list)
    meta: Dict[str, List[str]] = field(default_factory=dict)
    links: List[Dict[str, str]] = field(default_factory=list)
    headings: List[Tuple[int, str]] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    anchors: List[Anchor] = field(default_factory=list)
    jsonld: List[str] = field(default_factory=list)
    head_scripts: List[Dict[str, str]] = field(default_factory=list)
    script_count: int = 0
    body_text: str = ""
    has_charset: bool = False
    mount_ids: List[str] = field(default_factory=list)
    resource_urls: List[str] = field(default_factory=list)
    x_robots_tag: str = ""

    def meta_first(self, key: str) -> Optional[str]:
        values = self.meta.get(key.lower())
        return values[0] if values else None

    def links_with_rel(self, rel: str) -> List[Dict[str, str]]:
        rel = rel.lower()
        return [l for l in self.links if rel in l.get("rel", "").lower().split()]

    @property
    def canonicals(self) -> List[str]:
        return [l.get("href", "") for l in self.links_with_rel("canonical")]

    @property
    def robots_directives(self) -> List[str]:
        values = (self.meta.get("robots", []) + self.meta.get("googlebot", []) + [self.x_robots_tag])
        out: List[str] = []
        for v in values:
            out.extend(d.strip().lower() for d in v.split(",") if d.strip())
        return out

    @property
    def is_noindex(self) -> bool:
        return any(d in ("noindex", "none") for d in self.robots_directives)


class _PageParser(HTMLParser):
    def __init__(self, page: Page):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.stack: List[str] = []
        self.in_head = False
        self.in_body = False
        self._title_buf: Optional[List[str]] = None
        self._heading: Optional[Tuple[int, List[str]]] = None
        self._anchor: Optional[Tuple[Anchor, List[str]]] = None
        self._script: Optional[Tuple[str, List[str]]] = None
        self._suppress = 0
        self._text: List[str] = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        p = self.page
        if tag == "html":
            p.html_lang = a.get("lang") or None
        elif tag == "head":
            self.in_head = True
        elif tag == "body":
            self.in_head = False
            self.in_body = True
        elif tag == "title" and not self.stack_has("svg"):
            self._title_buf = []
        elif tag == "meta":
            if "charset" in a or a.get("http-equiv", "").lower() == "content-type":
                p.has_charset = True
            key = (a.get("name") or a.get("property") or a.get("itemprop") or "").lower()
            if key:
                p.meta.setdefault(key, []).append(a.get("content", ""))
        elif tag == "link":
            p.links.append(a)
            if "stylesheet" in a.get("rel", "").lower():
                p.resource_urls.append(a.get("href", ""))
        elif tag in HEADING_TAGS:
            self._heading = (int(tag[1]), [])
        elif tag == "img":
            p.images.append(Image(a.get("src") or a.get("data-src") or "", a.get("alt"),
                                  a.get("width"), a.get("height"), a.get("loading")))
            p.resource_urls.append(a.get("src", ""))
        elif tag == "a":
            self._anchor = (Anchor(a.get("href"), "", a.get("rel", ""), "onclick" in a), [])
        elif tag == "script":
            p.script_count += 1
            stype = a.get("type", "").lower()
            if stype == "application/ld+json":
                self._script = ("jsonld", [])
            elif self.in_head and "src" in a:
                p.head_scripts.append(a)
            if "src" in a:
                p.resource_urls.append(a.get("src", ""))
        elif tag in ("div", "main", "section") and a.get("id"):
            p.mount_ids.append(a["id"])
        if tag in VOID_TEXT_TAGS:
            self._suppress += 1
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source", "area", "base", "col", "embed", "wbr", "track", "param"):
            self.stack.append(tag)

    def stack_has(self, tag: str) -> bool:
        return tag in self.stack

    def handle_endtag(self, tag):
        p = self.page
        if tag == "head":
            self.in_head = False
        elif tag == "title" and self._title_buf is not None:
            p.titles.append(" ".join("".join(self._title_buf).split()))
            self._title_buf = None
        elif tag in HEADING_TAGS and self._heading:
            p.headings.append((self._heading[0], " ".join("".join(self._heading[1]).split())))
            self._heading = None
        elif tag == "a" and self._anchor:
            anchor, buf = self._anchor
            anchor.text = " ".join("".join(buf).split())
            p.anchors.append(anchor)
            self._anchor = None
        elif tag == "script" and self._script:
            p.jsonld.append("".join(self._script[1]))
            self._script = None
        if tag in VOID_TEXT_TAGS and self._suppress:
            self._suppress -= 1
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in self.stack and self.stack[-1] == tag:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self._script is not None:
            self._script[1].append(data)
            return
        if self._title_buf is not None:
            self._title_buf.append(data)
            return
        if self._suppress:
            return
        if self._heading:
            self._heading[1].append(data)
        if self._anchor:
            self._anchor[1].append(data)
        if self.in_body or not self.in_head:
            self._text.append(data)

    def close(self):
        super().close()
        self.page.body_text = " ".join(" ".join(self._text).split())


def parse_html(html: str, url: str, status: int = 200, x_robots_tag: str = "") -> Page:
    page = Page(url=url, status=status, x_robots_tag=x_robots_tag)
    parser = _PageParser(page)
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # malformed HTML should degrade, never crash an audit
        page.body_text = page.body_text or ""
    return page


@dataclass
class FetchResult:
    url: str
    final_url: str
    status: int
    content_type: str
    body: str
    headers: Dict[str, str]
    error: Optional[str] = None


def fetch(url: str, timeout: float = 15.0) -> FetchResult:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(5_000_000)
            charset = resp.headers.get_content_charset() or "utf-8"
            return FetchResult(url, resp.geturl(), resp.status, resp.headers.get("Content-Type", ""),
                               raw.decode(charset, errors="replace"),
                               {k.lower(): v for k, v in resp.headers.items()})
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return FetchResult(url, url, e.code, e.headers.get("Content-Type", "") if e.headers else "", body,
                           {k.lower(): v for k, v in (e.headers.items() if e.headers else [])})
    except Exception as e:  # network errors, timeouts, bad TLS
        return FetchResult(url, url, 0, "", "", {}, error=str(e))


def is_url(target: str) -> bool:
    return target.startswith("http://") or target.startswith("https://")


def is_absolute_http(url: str) -> bool:
    return bool(re.match(r"^https?://[^/\s]+", url or ""))


def iter_html_files(root: str) -> Iterator[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.endswith((".html", ".htm")):
                yield os.path.join(dirpath, name)


def file_to_url_path(root: str, path: str, trailing_slash: bool = True, keep_extension: bool = False) -> str:
    """Map a built file to the URL path a static host would serve it at.

    keep_extension=True is for sites that link to /menu.html rather than /menu.
    """
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        base = "/" + rel[: -len("index.html")]
        return base if trailing_slash else base.rstrip("/")
    if rel.endswith(".html") and not keep_extension:
        return "/" + rel[: -len(".html")]
    return "/" + rel


def site_uses_html_extension(root: str) -> bool:
    """Guess whether a static site's URLs keep ".html" (/menu.html) or are clean (/menu).

    Hand-written sites usually link to page.html, and changing that would need
    redirects, so we follow whatever the site's own links and canonicals do.
    """
    with_ext = without = 0
    for path in iter_html_files(root):
        with open(path, encoding="utf-8", errors="replace") as fh:
            page = parse_html(fh.read(), "")
        for href in [a.href for a in page.anchors if a.href] + page.canonicals:
            parts = urllib.parse.urlsplit(href)
            if parts.scheme not in ("", "http", "https") or (parts.netloc and not page.canonicals.count(href)):
                continue
            last = parts.path.rsplit("/", 1)[-1]
            if last.endswith((".html", ".htm")) and last not in ("index.html", "index.htm"):
                with_ext += 1
            elif last and "." not in last:
                without += 1
    return with_ext > without


def url_key(url: str) -> str:
    """Path identity for comparing URL variants: /a, /a/, /a.html and /a/index.html are one page."""
    path = urllib.parse.urlsplit(url).path or "/"
    for suffix in ("index.html", "index.htm"):
        if path.endswith("/" + suffix):
            path = path[: -len(suffix)]
    if path.endswith((".html", ".htm")):
        path = path.rsplit(".", 1)[0]
    return path.rstrip("/") or "/"


def extract_jsonld_blocks(html: str) -> List[str]:
    return parse_html(html, "").jsonld


def load_json_lenient(text: str):
    """json.loads that tolerates HTML comment wrappers and CDATA some CMSs emit."""
    cleaned = text.strip()
    for prefix, suffix in (("<!--", "-->"), ("//<![CDATA[", "//]]>"), ("<![CDATA[", "]]>")):
        if cleaned.startswith(prefix) and cleaned.endswith(suffix):
            cleaned = cleaned[len(prefix): -len(suffix)].strip()
    return json.loads(cleaned)


def same_origin(a: str, b: str) -> bool:
    pa, pb = urllib.parse.urlsplit(a), urllib.parse.urlsplit(b)
    return (pa.scheme, pa.netloc.lower()) == (pb.scheme, pb.netloc.lower())


def normalize_url(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", parts.query, ""))
