#!/usr/bin/env python3
"""Audit the SEO health of built HTML, a directory of pages, or a live URL.

Examples:
  seo_audit.py dist                              # audit a static build
  seo_audit.py http://localhost:3000 --crawl 50  # crawl a running dev server
  seo_audit.py https://example.com --json        # machine-readable output
  seo_audit.py out --base-url https://example.com --fail-under 85   # CI gate

The audit reads raw HTML and never executes JavaScript. That is deliberate:
it is what social-card scrapers and most AI crawlers see, so a client-only SPA
shows up as an empty page here, exactly as it does for them.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_lib import (  # noqa: E402
    Page, fetch, file_to_url_path, is_absolute_http, is_url, iter_html_files,
    load_json_lenient, normalize_url, parse_html, same_origin, site_uses_html_extension,
)

SEVERITY_WEIGHT = {"error": 12, "warning": 5, "info": 1}
SITE_WEIGHT = {"error": 8, "warning": 3, "info": 0}
ASSET_EXT = re.compile(r"\.(png|jpe?g|gif|webp|avif|svg|ico|css|js|mjs|json|xml|txt|pdf|zip|mp4|webm|mp3|woff2?|ttf|eot|map)$", re.I)
HREFLANG_RE = re.compile(r"^(x-default|[a-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|\d{3}))?)$")

FIX_HINTS = {
    "title-missing": "Give every page a unique <title> (≈50–60 chars, topic first, brand last).",
    "title-multiple": "Render exactly one <title>; duplicate head managers usually cause this.",
    "title-length": "Keep titles ≈15–65 characters so they aren't truncated or vague.",
    "title-duplicate": "Titles must be unique per URL; generate them from page data.",
    "description-missing": "Add a meta description (≈140–160 chars) that gives a reason to click.",
    "description-length": "Aim for ≈70–170 characters.",
    "description-duplicate": "Write unique descriptions per page, or generate them from page data.",
    "canonical-missing": "Add a self-referencing absolute <link rel=\"canonical\">.",
    "canonical-relative": "Canonical URLs must be absolute (https://…), built from one site-origin config.",
    "canonical-multiple": "Emit exactly one canonical link per page.",
    "canonical-cross-origin": "Canonical points to a different origin; check the site URL config/env var.",
    "canonical-noindex-conflict": "Don't combine noindex with a canonical to another URL; pick one signal.",
    "lang-missing": "Set <html lang=\"…\"> to the page's language.",
    "viewport-missing": "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">.",
    "charset-missing": "Add <meta charset=\"utf-8\"> as the first element in <head>.",
    "h1-missing": "Give each page one descriptive <h1>.",
    "h1-multiple": "Prefer a single <h1> that states the page topic.",
    "heading-skip": "Don't skip heading levels (e.g. h2 → h4); keep the outline logical.",
    "og-missing": "Add Open Graph tags so links unfurl well on social/chat apps.",
    "og-image-relative": "og:image must be an absolute URL, or scrapers can't fetch it.",
    "twitter-card-missing": "Add <meta name=\"twitter:card\" content=\"summary_large_image\">.",
    "img-alt-missing": "Add alt text to meaningful images (alt=\"\" for decorative ones).",
    "img-dimensions-missing": "Set width/height on images to prevent layout shift (CLS).",
    "jsonld-invalid": "Fix the JSON-LD syntax; invalid blocks are ignored entirely.",
    "jsonld-missing": "Add JSON-LD structured data appropriate to the page type.",
    "noindex": "Page is noindexed. Fine for utility pages; a bug on pages meant to rank.",
    "spa-shell": "Content is rendered client-side only. Prerender/SSR public routes so crawlers and scrapers see it.",
    "thin-content": "Very little text; make sure the page is useful on its own or noindex it.",
    "links-not-crawlable": "Use real <a href=\"/path\"> links; crawlers don't click buttons or follow javascript: links.",
    "mixed-content": "Load all resources over https on an https page.",
    "meta-keywords": "meta keywords is ignored by Google; remove it.",
    "render-blocking-script": "Add defer/async to head scripts (or move them) to speed up rendering.",
    "hreflang-invalid": "Use valid language(-region) codes like en, en-GB, pt-BR, or x-default.",
    "hreflang-no-self": "Each hreflang set must include the page itself.",
    "hreflang-no-x-default": "Add an x-default hreflang for unmatched languages.",
    "hreflang-not-reciprocal": "hreflang links must be reciprocal: if A points to B, B must point back to A.",
    "http-error": "URL returns an error status; fix it or remove links to it.",
    "broken-internal-link": "Internal link points to a page that doesn't exist.",
    "broken-image": "Image file isn't in the build output; fix the path (relative paths break on nested URLs) or add the file.",
    "robots-missing": "Add /robots.txt that allows crawling and references your sitemap.",
    "robots-blocks-all": "robots.txt blocks the whole site for all crawlers. Remove `Disallow: /` before launch.",
    "robots-no-sitemap": "Reference the sitemap in robots.txt: `Sitemap: https://…/sitemap.xml`.",
    "robots-blocks-assets": "Don't block CSS/JS; Google needs them to render pages.",
    "sitemap-missing": "Publish an XML sitemap of canonical, indexable URLs.",
    "sitemap-invalid": "The sitemap isn't valid XML or contains relative URLs.",
    "sitemap-noindex-url": "Sitemap lists URLs that are noindexed or non-200; keep it to indexable pages.",
    "llms-txt-missing": "Optional: add /llms.txt to summarize the site for AI tools.",
    "favicon-missing": "Add a favicon (and apple-touch-icon) — shown in Google results and tabs.",
    "manifest-missing": "Optional: add a web app manifest with name, icons and theme_color.",
    "page-blocked-by-robots": "This page is disallowed by robots.txt, so it can't be crawled.",
}


@dataclass
class Issue:
    id: str
    severity: str
    message: str
    url: str = ""

    @property
    def hint(self) -> str:
        return FIX_HINTS.get(self.id, "")


@dataclass
class PageReport:
    url: str
    status: int
    score: int
    issues: List[Issue] = field(default_factory=list)


@dataclass
class AuditReport:
    target: str
    mode: str
    score: int
    grade: str
    pages: List[PageReport]
    site_issues: List[Issue]
    stats: Dict[str, object]


# ---------------------------------------------------------------- page checks

def check_page(page: Page, origin: Optional[str], is_home: bool) -> List[Issue]:
    issues: List[Issue] = []

    def add(id_: str, sev: str, msg: str):
        issues.append(Issue(id_, sev, msg, page.url))

    if page.status >= 400 or page.status == 0:
        add("http-error", "error", f"HTTP status {page.status or 'unreachable'}")
        return issues

    titles = [t for t in page.titles if t is not None]
    if not titles or not titles[0].strip():
        add("title-missing", "error", "No <title>")
    else:
        if len(titles) > 1:
            add("title-multiple", "warning", f"{len(titles)} <title> elements")
        n = len(titles[0])
        if n < 15 or n > 65:
            add("title-length", "warning", f"Title is {n} chars: {titles[0][:80]!r}")

    desc = page.meta_first("description")
    if not desc or not desc.strip():
        add("description-missing", "error", "No meta description")
    elif not 70 <= len(desc) <= 170:
        add("description-length", "warning", f"Description is {len(desc)} chars")

    canon = page.canonicals
    if not canon:
        add("canonical-missing", "warning", "No canonical link")
    else:
        if len(set(canon)) > 1:
            add("canonical-multiple", "error", f"{len(canon)} canonical links: {canon}")
        if not is_absolute_http(canon[0]):
            add("canonical-relative", "error", f"Canonical is not absolute: {canon[0]!r}")
        elif origin and is_url(page.url) and not same_origin(canon[0], origin):
            add("canonical-cross-origin", "info", f"Canonical {canon[0]} is on another origin than {origin}")
        if page.is_noindex and is_absolute_http(canon[0]) and is_url(page.url) \
                and normalize_url(canon[0]) != normalize_url(page.url):
            add("canonical-noindex-conflict", "warning", "noindex combined with a canonical to another URL")

    if not page.html_lang:
        add("lang-missing", "warning", "<html> has no lang attribute")
    if not page.meta_first("viewport"):
        add("viewport-missing", "error", "No viewport meta tag")
    if not page.has_charset:
        add("charset-missing", "warning", "No charset declaration")

    # SPA shell: almost no server-rendered text, a JS mount point, and scripts.
    text_len = len(page.body_text)
    mount = {m.lower() for m in page.mount_ids} & {"root", "app", "__next", "__nuxt", "svelte", "q-app", "main"}
    if text_len < 150 and page.script_count > 0 and (mount or not page.headings):
        add("spa-shell", "error", f"Only {text_len} chars of text in raw HTML; content appears to be client-rendered")
    elif text_len < 250 and not page.is_noindex:
        add("thin-content", "info", f"Only {text_len} chars of visible text")

    h1s = [h for lvl, h in page.headings if lvl == 1]
    if not h1s and "spa-shell" not in {i.id for i in issues}:
        add("h1-missing", "warning", "No <h1>")
    elif len(h1s) > 1:
        add("h1-multiple", "info", f"{len(h1s)} <h1> elements")
    prev = 0
    for lvl, text in page.headings:
        if prev and lvl > prev + 1:
            add("heading-skip", "info", f"Heading jumps from h{prev} to h{lvl} ({text[:40]!r})")
            break
        prev = lvl

    og_missing = [k for k in ("og:title", "og:description", "og:image", "og:url", "og:type") if not page.meta_first(k)]
    if og_missing:
        add("og-missing", "warning", "Missing " + ", ".join(og_missing))
    og_image = page.meta_first("og:image")
    if og_image and not is_absolute_http(og_image):
        add("og-image-relative", "error", f"og:image is not absolute: {og_image!r}")
    if not page.meta_first("twitter:card"):
        add("twitter-card-missing", "info", "No twitter:card")

    no_alt = [i.src for i in page.images if i.alt is None]
    if no_alt:
        add("img-alt-missing", "warning", f"{len(no_alt)} image(s) without alt, e.g. {no_alt[0][:80]!r}")
    no_dims = [i.src for i in page.images if not (i.width and i.height) and not i.src.endswith(".svg")]
    if no_dims:
        add("img-dimensions-missing", "info", f"{len(no_dims)} image(s) without width/height")

    if not page.jsonld:
        add("jsonld-missing", "info" if not is_home else "warning", "No JSON-LD structured data")
    for block in page.jsonld:
        try:
            load_json_lenient(block)
        except ValueError as e:
            add("jsonld-invalid", "error", f"Invalid JSON-LD: {e}")

    if page.is_noindex:
        add("noindex", "warning", "Page is noindex")

    bad_links = [a for a in page.anchors
                 if (a.href is None and a.has_onclick) or (a.href or "").strip().lower().startswith("javascript:")]
    if bad_links:
        add("links-not-crawlable", "warning", f"{len(bad_links)} link(s) without a crawlable href")

    if page.url.startswith("https://"):
        insecure = [u for u in page.resource_urls if u.startswith("http://")]
        if insecure:
            add("mixed-content", "warning", f"{len(insecure)} http:// resource(s), e.g. {insecure[0][:80]}")

    if "keywords" in page.meta:
        add("meta-keywords", "info", "meta keywords present")

    blocking = [s.get("src", "") for s in page.head_scripts
                if "async" not in s and "defer" not in s and s.get("type", "").lower() != "module"]
    if blocking:
        add("render-blocking-script", "info", f"{len(blocking)} render-blocking script(s) in <head>")

    alternates = [l for l in page.links_with_rel("alternate") if l.get("hreflang")]
    if alternates:
        codes = [l["hreflang"] for l in alternates]
        bad = [c for c in codes if not HREFLANG_RE.match(c)]
        if bad:
            add("hreflang-invalid", "error", f"Invalid hreflang code(s): {bad}")
        own = {normalize_url(c) for c in page.canonicals if is_absolute_http(c)}
        if is_url(page.url):
            own.add(normalize_url(page.url))
        if own and not any(normalize_url(l.get("href", "")) in own for l in alternates if is_absolute_http(l.get("href", ""))):
            add("hreflang-no-self", "warning", "hreflang set doesn't include this page")
        if "x-default" not in [c.lower() for c in codes]:
            add("hreflang-no-x-default", "info", "No x-default hreflang")

    if is_home:
        if not (page.links_with_rel("icon") or page.links_with_rel("shortcut")):
            add("favicon-missing", "info", "No <link rel=\"icon\"> on the home page")
        if not page.links_with_rel("manifest"):
            add("manifest-missing", "info", "No web app manifest linked")
    return issues


def page_score(issues: List[Issue]) -> int:
    # Count each issue id once per page so one noisy check can't zero a page.
    seen: Dict[str, str] = {}
    for i in issues:
        seen.setdefault(i.id, i.severity)
    return max(0, 100 - sum(SEVERITY_WEIGHT[s] for s in seen.values()))


# ---------------------------------------------------------------- robots & sitemap

def parse_robots(text: str) -> Dict[str, List[Tuple[str, str]]]:
    groups: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    agents: List[str] = []
    last_was_agent = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (s.strip() for s in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if not last_was_agent:
                agents = []
            agents.append(value.lower())
            last_was_agent = True
            continue
        last_was_agent = False
        if key in ("allow", "disallow"):
            for agent in agents:
                groups[agent].append((key, value))
        elif key == "sitemap":
            groups["__sitemaps__"].append(("sitemap", value))
    return groups


def robots_disallows(groups, path: str, agent: str = "*") -> bool:
    rules = groups.get(agent.lower()) or groups.get("*") or []
    best: Tuple[int, str] = (-1, "allow")
    for kind, pattern in rules:
        if not pattern:
            continue
        regex = "^" + re.escape(pattern).replace(r"\*", ".*")
        if regex.endswith(r"\$"):
            regex = regex[:-2] + "$"
        if re.match(regex, path) and len(pattern) >= best[0]:
            # On equal length, allow wins (Google's documented tie-break).
            if len(pattern) > best[0] or kind == "allow":
                best = (len(pattern), kind)
    return best[1] == "disallow"


def check_robots(text: Optional[str], source: str) -> Tuple[List[Issue], Dict]:
    if text is None:
        return [Issue("robots-missing", "warning", "No robots.txt found", source)], {}
    groups = parse_robots(text)
    issues = []
    star = groups.get("*", [])
    if any(k == "disallow" and v == "/" for k, v in star) and not any(k == "allow" and v == "/" for k, v in star):
        issues.append(Issue("robots-blocks-all", "error", "`User-agent: *` + `Disallow: /`", source))
    if not groups.get("__sitemaps__"):
        issues.append(Issue("robots-no-sitemap", "warning", "No Sitemap: line", source))
    if any(k == "disallow" and re.search(r"\.(css|js)\b|/_next/|/assets/?$|/static/?$", v) for k, v in star):
        issues.append(Issue("robots-blocks-assets", "warning", "robots.txt appears to block CSS/JS assets", source))
    return issues, groups


def parse_sitemap_urls(xml_text: str) -> Tuple[List[str], bool]:
    """Return (locs, is_index). Raises ValueError for invalid XML."""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text)
    tag = root.tag.split("}")[-1]
    locs = [el.text.strip() for el in root.iter() if el.tag.split("}")[-1] == "loc" and el.text]
    return locs, tag == "sitemapindex"


# ---------------------------------------------------------------- collectors

def collect_from_dir(root: str, base_url: Optional[str]) -> Tuple[List[Page], Dict[str, Optional[str]]]:
    pages = []
    keep_ext = site_uses_html_extension(root)
    for path in iter_html_files(root):
        url_path = file_to_url_path(root, path, keep_extension=keep_ext)
        url = (base_url.rstrip("/") + url_path) if base_url else url_path
        with open(path, encoding="utf-8", errors="replace") as fh:
            page = parse_html(fh.read(), url)
        page.file = path  # type: ignore[attr-defined]
        if os.path.basename(path) in ("404.html", "500.html"):
            page.status = 404 if path.endswith("404.html") else 500
            page.is_error_page = True  # type: ignore[attr-defined]
        pages.append(page)
    extras = {}
    for name in ("robots.txt", "sitemap.xml", "sitemap-index.xml", "sitemap_index.xml", "sitemap-0.xml", "llms.txt"):
        p = os.path.join(root, name)
        extras[name] = open(p, encoding="utf-8", errors="replace").read() if os.path.isfile(p) else None
    return pages, extras


def collect_from_url(start: str, crawl: int, timeout: float) -> Tuple[List[Page], Dict[str, Optional[str]]]:
    pages: List[Page] = []
    seen = set()
    queue = deque([start])
    while queue and len(pages) < max(1, crawl):
        url = queue.popleft()
        key = normalize_url(url)
        if key in seen:
            continue
        seen.add(key)
        res = fetch(url, timeout)
        if res.status and "html" not in res.content_type.lower() and res.status < 400:
            continue
        page = parse_html(res.body, res.final_url or url, res.status, res.headers.get("x-robots-tag", ""))
        pages.append(page)
        if res.error:
            page.status = 0
        for a in page.anchors:
            if not a.href or a.href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            nxt = urllib.parse.urljoin(page.url, a.href).split("#")[0]
            if same_origin(nxt, start) and not ASSET_EXT.search(urllib.parse.urlsplit(nxt).path) \
                    and normalize_url(nxt) not in seen and "nofollow" not in a.rel.lower():
                queue.append(nxt)
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(start))
    extras: Dict[str, Optional[str]] = {}
    for name in ("robots.txt", "sitemap.xml", "llms.txt"):
        res = fetch(f"{origin}/{name}", timeout)
        extras[name] = res.body if res.status == 200 else None
    if extras.get("sitemap.xml") is None and extras.get("robots.txt"):
        for kind, value in parse_robots(extras["robots.txt"] or "").get("__sitemaps__", []):
            res = fetch(value, timeout)
            if res.status == 200:
                extras["sitemap.xml"] = res.body
                break
    return pages, extras


# ---------------------------------------------------------------- site checks

def site_checks(pages: List[Page], extras: Dict[str, Optional[str]], mode: str, source: str,
                root: Optional[str]) -> Tuple[List[Issue], List[Issue]]:
    """Return (site-level issues, extra per-page issues)."""
    site: List[Issue] = []
    per_page: List[Issue] = []
    indexable = [p for p in pages if p.status < 400 and not p.is_noindex and not getattr(p, "is_error_page", False)]

    titles = Counter(p.titles[0] for p in indexable if p.titles and p.titles[0])
    for title, count in titles.items():
        if count > 1:
            urls = [p.url for p in indexable if p.titles and p.titles[0] == title]
            for u in urls:
                per_page.append(Issue("title-duplicate", "warning", f"Title shared by {count} pages: {title[:60]!r}", u))
    descs = Counter(p.meta_first("description") for p in indexable if p.meta_first("description"))
    for desc, count in descs.items():
        if count > 1:
            for p in indexable:
                if p.meta_first("description") == desc:
                    per_page.append(Issue("description-duplicate", "warning", f"Description shared by {count} pages", p.url))

    robots_issues, groups = check_robots(extras.get("robots.txt"), source)
    site.extend(robots_issues)
    if groups:
        for p in indexable:
            path = urllib.parse.urlsplit(p.url).path or "/"
            if robots_disallows(groups, path):
                per_page.append(Issue("page-blocked-by-robots", "error", f"robots.txt disallows {path}", p.url))

    sitemap_text = next((extras.get(n) for n in ("sitemap.xml", "sitemap-index.xml", "sitemap_index.xml", "sitemap-0.xml") if extras.get(n)), None)
    sitemap_count = 0
    if sitemap_text is None:
        site.append(Issue("sitemap-missing", "warning", "No sitemap.xml found", source))
    else:
        try:
            locs, is_index = parse_sitemap_urls(sitemap_text)
            sitemap_count = len(locs)
            rel = [l for l in locs if not is_absolute_http(l)]
            if rel:
                site.append(Issue("sitemap-invalid", "error", f"{len(rel)} relative <loc> URL(s), e.g. {rel[0]}", source))
            if not is_index:
                noindexed = {urllib.parse.urlsplit(p.url).path for p in pages if p.is_noindex or p.status >= 400}
                bad = [l for l in locs if urllib.parse.urlsplit(l).path in noindexed]
                if bad:
                    site.append(Issue("sitemap-noindex-url", "warning", f"{len(bad)} sitemap URL(s) are noindex/error pages, e.g. {bad[0]}", source))
        except Exception as e:  # ParseError and friends
            site.append(Issue("sitemap-invalid", "error", f"Sitemap is not valid XML: {e}", source))

    if extras.get("llms.txt") is None:
        site.append(Issue("llms-txt-missing", "info", "No /llms.txt", source))

    # hreflang reciprocity, only among pages we actually saw.
    by_url = {normalize_url(p.url): p for p in pages if is_absolute_http(p.url)}
    for p in pages:
        for l in p.links_with_rel("alternate"):
            href = l.get("href", "")
            if not l.get("hreflang") or not is_absolute_http(href) or l["hreflang"].lower() == "x-default":
                continue
            target = by_url.get(normalize_url(href))
            if target is None or target is p:
                continue
            back = {normalize_url(x.get("href", "")) for x in target.links_with_rel("alternate") if x.get("hreflang")}
            if normalize_url(p.url) not in back:
                per_page.append(Issue("hreflang-not-reciprocal", "warning", f"{href} doesn't link back", p.url))

    if mode == "dir" and root:
        known = {file_to_url_path(root, getattr(p, "file")) for p in pages if hasattr(p, "file")}
        known |= {k.rstrip("/") for k in known}
        files_on_disk = set()
        for dirpath, _, filenames in os.walk(root):
            for f in filenames:
                files_on_disk.add("/" + os.path.relpath(os.path.join(dirpath, f), root).replace(os.sep, "/"))
        for p in pages:
            if not hasattr(p, "file"):
                continue
            broken = set()
            for a in p.anchors:
                href = (a.href or "").strip()
                if not href or re.match(r"^([a-z]+:|//|#)", href, re.I):
                    continue
                cur = file_to_url_path(root, p.file)  # type: ignore[attr-defined]
                if not cur.endswith("/") and not cur.endswith(".html"):
                    cur = cur.rsplit("/", 1)[0] + "/"
                target = urllib.parse.urljoin(cur, href).split("#")[0].split("?")[0]
                target = urllib.parse.unquote(target)
                if target in known or target.rstrip("/") in known or target in files_on_disk \
                        or (target.rstrip("/") + "/index.html") in files_on_disk or (target + ".html") in files_on_disk:
                    continue
                broken.add(target)
            if broken:
                per_page.append(Issue("broken-internal-link", "warning",
                                      f"{len(broken)} broken internal link(s), e.g. {sorted(broken)[0]}", p.url))
            # Images resolve against the URL the page is served at, so a relative
            # src that works for /index.html breaks on /docs/page/.
            missing = set()
            page_url = file_to_url_path(root, p.file)  # type: ignore[attr-defined]
            if not page_url.endswith("/") and not page_url.endswith((".html", ".htm")):
                page_url += "/"  # directory-style URL: the browser resolves relative to it
            for img in p.images:
                src = (img.src or "").strip()
                if not src or re.match(r"^([a-z]+:|//)", src, re.I):
                    continue
                target = urllib.parse.unquote(urllib.parse.urljoin(page_url, src).split("?")[0].split("#")[0])
                if target not in files_on_disk:
                    missing.add(target)
            if missing:
                per_page.append(Issue("broken-image", "warning",
                                      f"{len(missing)} image(s) not found in the output, e.g. {sorted(missing)[0]}", p.url))
    return site, per_page


# ---------------------------------------------------------------- orchestration

def grade(score: int) -> str:
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 55 else "F"


def audit(target: str, crawl: int = 25, base_url: Optional[str] = None, timeout: float = 15.0) -> AuditReport:
    if is_url(target):
        mode = "url"
        pages, extras = collect_from_url(target, crawl, timeout)
        origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(target))
        home_url = normalize_url(origin + "/")
        root = None
    elif os.path.isdir(target):
        mode = "dir"
        root = target
        pages, extras = collect_from_dir(target, base_url)
        origin = base_url
        home_url = normalize_url(base_url.rstrip("/") + "/") if base_url else "/"
    elif os.path.isfile(target):
        mode = "file"
        root = None
        with open(target, encoding="utf-8", errors="replace") as fh:
            pages = [parse_html(fh.read(), base_url or target)]
        extras = {"robots.txt": "", "sitemap.xml": "", "llms.txt": ""}  # not applicable for one file
        origin, home_url = base_url, None
    else:
        raise SystemExit(f"error: {target!r} is not a URL, directory, or file")

    if not pages:
        raise SystemExit(f"error: no HTML pages found at {target!r}")

    def is_home(p: Page) -> bool:
        if mode == "file":
            return True
        u = p.url if mode == "url" else p.url
        return normalize_url(u) == home_url if is_absolute_http(u) else u == "/"

    extra_issues: List[Issue] = []
    site_issues: List[Issue] = []
    if mode != "file":
        site_issues, extra_issues = site_checks(pages, extras, mode, target, root)

    reports = []
    for p in pages:
        if getattr(p, "is_error_page", False):
            continue
        issues = check_page(p, origin, is_home(p)) + [i for i in extra_issues if i.url == p.url]
        reports.append(PageReport(p.url, p.status, page_score(issues), issues))

    avg = sum(r.score for r in reports) / len(reports) if reports else 0
    penalty = sum(SITE_WEIGHT[i.severity] for i in site_issues)
    score = int(round(max(0, avg - penalty)))
    counts = Counter(i.severity for r in reports for i in r.issues) + Counter(i.severity for i in site_issues)
    stats = {"pages": len(reports), "errors": counts.get("error", 0), "warnings": counts.get("warning", 0),
             "info": counts.get("info", 0), "average_page_score": round(avg, 1), "site_penalty": penalty}
    return AuditReport(target, mode, score, grade(score), reports, site_issues, stats)


def render_markdown(report: AuditReport, max_pages: int = 30) -> str:
    out = [f"# SEO audit: {report.target}", "",
           f"**Score: {report.score}/100 (grade {report.grade})** · {report.stats['pages']} page(s) · "
           f"{report.stats['errors']} errors · {report.stats['warnings']} warnings · {report.stats['info']} notices", ""]
    if report.site_issues:
        out += ["## Site-wide", ""]
        for i in sorted(report.site_issues, key=lambda i: list(SEVERITY_WEIGHT).index(i.severity)):
            out.append(f"- **{i.severity.upper()}** `{i.id}` — {i.message}. {i.hint}")
        out.append("")

    agg: Dict[str, List[Issue]] = defaultdict(list)
    for r in report.pages:
        for i in r.issues:
            agg[i.id].append(i)
    if agg:
        out += ["## Top issues", "", "| Severity | Issue | Pages | Fix |", "|---|---|---|---|"]
        order = sorted(agg.items(), key=lambda kv: (list(SEVERITY_WEIGHT).index(kv[1][0].severity), -len(kv[1])))
        for id_, items in order:
            out.append(f"| {items[0].severity} | `{id_}` | {len({i.url for i in items})} | {items[0].hint} |")
        out.append("")

    out += ["## Pages", ""]
    for r in sorted(report.pages, key=lambda r: r.score)[:max_pages]:
        out.append(f"### {r.url} — {r.score}/100")
        if not r.issues:
            out.append("- ✓ No issues")
        for i in r.issues:
            out.append(f"- {i.severity}: `{i.id}` — {i.message}")
        out.append("")
    if len(report.pages) > max_pages:
        out.append(f"_…{len(report.pages) - max_pages} more page(s) omitted; use --json for everything._")
    return "\n".join(out)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="URL, build directory, or single HTML file")
    ap.add_argument("--crawl", type=int, default=25, help="max pages to crawl in URL mode (default 25)")
    ap.add_argument("--base-url", help="production origin for directory/file mode, e.g. https://example.com")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    ap.add_argument("--max-pages", type=int, default=30, help="pages to list in the Markdown report")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--fail-under", type=int, help="exit 1 if the score is below this (for CI)")
    args = ap.parse_args(argv)

    report = audit(args.target, args.crawl, args.base_url, args.timeout)
    if args.json:
        data = asdict(report)
        for r in data["pages"]:
            for i in r["issues"]:
                i["hint"] = FIX_HINTS.get(i["id"], "")
        print(json.dumps(data, indent=2))
    else:
        print(render_markdown(report, args.max_pages))
    if args.fail_under is not None and report.score < args.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
