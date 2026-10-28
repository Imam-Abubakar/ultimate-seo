#!/usr/bin/env python3
"""Generate sitemap.xml for a static site from its built HTML files.

Use this for plain-HTML sites or generators without sitemap tooling. Framework
projects should prefer their native sitemap support (see the framework
references), because it knows about dynamic routes.

Examples:
  generate_sitemap.py public --base-url https://example.com
  generate_sitemap.py dist --base-url https://example.com --lastmod git --no-trailing-slash
  generate_sitemap.py _site --base-url https://example.com --stdout

Pages are skipped when they are noindexed, canonicalize to another URL, or are
error pages (404.html etc.). lastmod is omitted by default: a lastmod that
changes on every build is worse than none, because search engines learn to
ignore it. Use --lastmod git when the HTML files are committed sources.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.parse
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_lib import file_to_url_path, iter_html_files, parse_html, site_uses_html_extension, url_key  # noqa: E402

MAX_URLS = 50_000
ERROR_PAGES = {"404.html", "500.html", "50x.html", "offline.html"}


def git_lastmod(path: str) -> Optional[str]:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cI", "--", os.path.basename(path)],
                             cwd=os.path.dirname(path) or ".", capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def collect_urls(root: str, base_url: str, trailing_slash: bool, lastmod: str,
                 keep_extension: Optional[bool] = None) -> Tuple[List[Tuple[str, Optional[str]]], List[str]]:
    base = base_url.rstrip("/")
    if keep_extension is None:
        keep_extension = site_uses_html_extension(root)
    base_host = urllib.parse.urlsplit(base).netloc.lower()
    urls: List[Tuple[str, Optional[str]]] = []
    skipped: List[str] = []
    for path in iter_html_files(root):
        rel = os.path.relpath(path, root)
        if os.path.basename(path) in ERROR_PAGES:
            skipped.append(f"{rel} (error page)")
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            page = parse_html(fh.read(), "")
        url = base + file_to_url_path(root, path, trailing_slash, keep_extension)
        if page.is_noindex:
            skipped.append(f"{rel} (noindex)")
            continue
        canon = page.canonicals[0] if page.canonicals else None
        if canon and canon.startswith(("http://", "https://")):
            if url_key(canon) != url_key(url):
                skipped.append(f"{rel} (canonical → {canon})")
                continue
            if urllib.parse.urlsplit(canon).netloc.lower() == base_host:
                url = canon  # the page's own canonical is the authoritative URL form
            else:
                print(f"warning: {rel} canonical host differs from --base-url: {canon}", file=sys.stderr)
        if any(m.lower().startswith("0;") or "url=" in m.lower() for m in page.meta.get("refresh", [])):
            skipped.append(f"{rel} (meta refresh redirect)")
            continue
        mod = None
        if lastmod == "git":
            mod = git_lastmod(path)
        elif lastmod == "mtime":
            from datetime import datetime, timezone
            mod = datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        urls.append((url, mod))
    urls.sort(key=lambda u: (u[0].count("/"), u[0]))
    return urls, skipped


def render_urlset(urls: List[Tuple[str, Optional[str]]]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod in urls:
        lines.append(f"  <url><loc>{escape(loc)}</loc>" + (f"<lastmod>{mod}</lastmod>" if mod else "") + "</url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def render_index(locs: List[str]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += [f"  <sitemap><loc>{escape(l)}</loc></sitemap>" for l in locs]
    lines.append("</sitemapindex>")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", help="directory containing the built HTML")
    ap.add_argument("--base-url", required=True, help="production origin, e.g. https://www.example.com")
    ap.add_argument("--no-trailing-slash", action="store_true", help="emit /about instead of /about/")
    ap.add_argument("--lastmod", choices=["none", "git", "mtime"], default="none")
    ap.add_argument("--html-extension", choices=["auto", "keep", "strip"], default="auto",
                    help="emit /page.html (keep) or /page (strip); auto follows the site's own links and canonicals")
    ap.add_argument("--stdout", action="store_true", help="print instead of writing sitemap.xml")
    args = ap.parse_args(argv)

    if not args.base_url.startswith(("http://", "https://")):
        ap.error("--base-url must be absolute, e.g. https://www.example.com")
    if not os.path.isdir(args.root):
        ap.error(f"{args.root} is not a directory")

    keep = {"auto": None, "keep": True, "strip": False}[args.html_extension]
    urls, skipped = collect_urls(args.root, args.base_url, not args.no_trailing_slash, args.lastmod, keep)
    if args.stdout:
        sys.stdout.write(render_urlset(urls[:MAX_URLS]))
    elif len(urls) <= MAX_URLS:
        with open(os.path.join(args.root, "sitemap.xml"), "w", encoding="utf-8") as fh:
            fh.write(render_urlset(urls))
    else:
        locs = []
        for n, start in enumerate(range(0, len(urls), MAX_URLS)):
            name = f"sitemap-{n}.xml"
            with open(os.path.join(args.root, name), "w", encoding="utf-8") as fh:
                fh.write(render_urlset(urls[start:start + MAX_URLS]))
            locs.append(f"{args.base_url.rstrip('/')}/{name}")
        with open(os.path.join(args.root, "sitemap.xml"), "w", encoding="utf-8") as fh:
            fh.write(render_index(locs))
    print(f"{len(urls)} URL(s) in sitemap; skipped {len(skipped)}", file=sys.stderr)
    for s in skipped:
        print(f"  skipped {s}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
