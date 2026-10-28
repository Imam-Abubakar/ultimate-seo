#!/usr/bin/env python3
"""Detect a project's web stack and existing SEO setup.

Examples:
  detect_stack.py .            # human-readable summary
  detect_stack.py . --json     # machine-readable
  detect_stack.py apps/web     # one app inside a monorepo

Reports the framework, rendering mode, language, package manager, build
output, existing SEO artifacts, likely production URL, and which reference
file in this skill to read next.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from seo_lib import SKIP_DIRS  # noqa: E402

REF = "references/frameworks/"

SEO_LIBRARIES = [
    "next-seo", "next-sitemap", "react-helmet", "react-helmet-async", "@unhead/vue", "@unhead/react", "@vueuse/head",
    "vue-meta", "@nuxtjs/seo", "@nuxtjs/sitemap", "@nuxtjs/robots", "nuxt-og-image", "nuxt-schema-org", "nuxt-seo-kit",
    "@astrojs/sitemap", "astro-seo", "astro-og-canvas", "svelte-meta-tags", "super-sitemap", "gatsby-plugin-sitemap",
    "gatsby-plugin-robots-txt", "gatsby-plugin-react-helmet", "@vercel/og", "satori", "schema-dts", "next-intl",
    "next-i18next", "@nuxtjs/i18n", "react-i18next", "i18next", "react-intl", "vue-i18n", "@angular/localize",
    "@docusaurus/plugin-sitemap", "vite-plugin-sitemap", "vite-react-ssg", "vite-ssg", "react-snap", "@prerenderer/rollup-plugin",
]
I18N_LIBS = {"next-intl", "next-i18next", "@nuxtjs/i18n", "react-i18next", "i18next", "react-intl", "vue-i18n", "@angular/localize", "@inlang/paraglide-js", "@lingui/core"}
URL_ENV_KEYS = re.compile(r"^\s*(?:export\s+)?((?:NEXT_PUBLIC_|PUBLIC_|VITE_|NUXT_PUBLIC_|REACT_APP_|GATSBY_)?(?:SITE_URL|BASE_URL|APP_URL|PUBLIC_URL|URL|SITE|ORIGIN|CANONICAL_URL|WEBSITE_URL|HOST_URL))\s*=\s*[\"']?(https?://[^\s\"'#]+)", re.M)


def read(path: str, limit: int = 400_000) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def exists(root: str, *patterns: str) -> List[str]:
    found: List[str] = []
    for pat in patterns:
        for p in glob.glob(os.path.join(root, pat), recursive=True):
            rel = os.path.relpath(p, root)
            if not any(part in SKIP_DIRS for part in rel.split(os.sep)):
                found.append(rel)
    return sorted(set(found))


def walk_files(root: str, max_files: int = 20_000):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d not in ("dist", "build", "out", "public/build", "_site", ".output")]
        for f in filenames:
            count += 1
            if count > max_files:
                return
            yield os.path.join(dirpath, f)


def load_package(root: str) -> Dict[str, Any]:
    try:
        return json.loads(read(os.path.join(root, "package.json")) or "{}")
    except ValueError:
        return {}


def package_manager(root: str) -> Optional[str]:
    for lock, pm in (("bun.lockb", "bun"), ("bun.lock", "bun"), ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"),
                     ("package-lock.json", "npm"), ("poetry.lock", "poetry"), ("uv.lock", "uv"), ("Pipfile.lock", "pipenv"),
                     ("requirements.txt", "pip"), ("Gemfile.lock", "bundler"), ("composer.lock", "composer"), ("go.sum", "go")):
        if os.path.exists(os.path.join(root, lock)):
            return pm
    return "npm" if os.path.exists(os.path.join(root, "package.json")) else None


def version_of(deps: Dict[str, str], name: str) -> Optional[str]:
    v = deps.get(name)
    if not v:
        return None
    m = re.search(r"\d+(\.\d+)*", v)
    return m.group(0) if m else v


def detect_framework(root: str, deps: Dict[str, str]) -> Dict[str, Any]:
    """Ordered from most to least specific: meta-frameworks before the libraries they wrap."""
    has = lambda *names: any(n in deps for n in names)  # noqa: E731
    cfg = lambda *pats: exists(root, *pats)  # noqa: E731

    if has("next"):
        app_dir = cfg("app/**/page.*", "src/app/**/page.*", "app/layout.*", "src/app/layout.*")
        pages_dir = cfg("pages/*.js", "pages/*.jsx", "pages/*.ts", "pages/*.tsx", "src/pages/*.js", "src/pages/*.jsx", "src/pages/*.ts", "src/pages/*.tsx")
        next_cfg = " ".join(read(os.path.join(root, p)) for p in cfg("next.config.*"))
        static_export = bool(re.search(r"output\s*:\s*['\"]export['\"]", next_cfg))
        router = "app" if app_dir and not pages_dir else "pages" if pages_dir and not app_dir else "app+pages" if app_dir else "app"
        return {"framework": "nextjs", "router": router, "version": version_of(deps, "next"),
                "rendering": "static-export" if static_export else "ssr/ssg (hybrid)",
                "reference": REF + ("nextjs-pages-router.md" if router == "pages" else "nextjs-app-router.md"),
                "build_output": "out" if static_export else ".next (audit a running server instead)"}
    if has("gatsby"):
        return {"framework": "gatsby", "version": version_of(deps, "gatsby"), "rendering": "ssg",
                "reference": REF + "gatsby.md", "build_output": "public"}
    if has("@remix-run/react", "@remix-run/node", "@remix-run/dev"):
        return {"framework": "remix", "version": version_of(deps, "@remix-run/react"), "rendering": "ssr",
                "reference": REF + "react-router-remix.md", "build_output": "build"}
    if has("@react-router/dev") or cfg("react-router.config.*"):
        rr_cfg = " ".join(read(os.path.join(root, p)) for p in cfg("react-router.config.*"))
        spa = bool(re.search(r"ssr\s*:\s*false", rr_cfg))
        return {"framework": "react-router-framework", "version": version_of(deps, "react-router"),
                "rendering": "spa (ssr:false)" if spa else "ssr", "reference": REF + "react-router-remix.md",
                "build_output": "build/client"}
    if has("@tanstack/react-start", "@tanstack/start", "@tanstack/solid-start"):
        return {"framework": "tanstack-start", "version": version_of(deps, "@tanstack/react-start"), "rendering": "ssr",
                "reference": REF + "react-spa.md", "build_output": ".output/public",
                "note": "SSR-capable: set metadata via each route's head() option; react-spa.md covers the head-tag patterns."}
    if has("astro"):
        astro_cfg = " ".join(read(os.path.join(root, p)) for p in cfg("astro.config.*"))
        ssr = bool(re.search(r"output\s*:\s*['\"](server|hybrid)['\"]", astro_cfg))
        result = {"framework": "astro", "version": version_of(deps, "astro"), "rendering": "ssr" if ssr else "ssg",
                  "reference": REF + "astro.md", "build_output": "dist"}
        if not re.search(r"\bsite\s*:", astro_cfg):
            result["note"] = "astro.config has no `site`: canonicals, sitemap and OG URLs can't be absolute until it's set."
        return result
    if has("nuxt", "nuxt3"):
        return {"framework": "nuxt", "version": version_of(deps, "nuxt") or version_of(deps, "nuxt3"), "rendering": "ssr (universal)",
                "reference": REF + "nuxt-vue.md", "build_output": ".output/public (after nuxt generate)"}
    if has("@sveltejs/kit"):
        adapter = next((d for d in deps if d.startswith("@sveltejs/adapter-")), None)
        return {"framework": "sveltekit", "version": version_of(deps, "@sveltejs/kit"),
                "rendering": "ssg" if adapter == "@sveltejs/adapter-static" else "ssr", "adapter": adapter,
                "reference": REF + "sveltekit.md", "build_output": "build"}
    if has("@angular/core"):
        ssr = has("@angular/ssr", "@nguniversal/express-engine")
        return {"framework": "angular", "version": version_of(deps, "@angular/core"), "rendering": "ssr" if ssr else "spa",
                "reference": REF + "angular.md", "build_output": "dist/<project>/browser"}
    if has("@docusaurus/core"):
        return {"framework": "docusaurus", "version": version_of(deps, "@docusaurus/core"), "rendering": "ssg",
                "reference": REF + "static-site-generators.md", "build_output": "build"}
    if has("vitepress"):
        return {"framework": "vitepress", "version": version_of(deps, "vitepress"), "rendering": "ssg",
                "reference": REF + "static-site-generators.md", "build_output": "docs/.vitepress/dist or .vitepress/dist"}
    if has("@11ty/eleventy"):
        return {"framework": "eleventy", "version": version_of(deps, "@11ty/eleventy"), "rendering": "ssg",
                "reference": REF + "static-site-generators.md", "build_output": "_site"}
    if has("@solidjs/start", "@builder.io/qwik-city", "@analogjs/platform"):
        name = "solidstart" if has("@solidjs/start") else "qwik-city" if has("@builder.io/qwik-city") else "analog"
        return {"framework": name, "rendering": "ssr", "reference": REF + "static-html.md",
                "build_output": "dist or .output/public",
                "note": "No dedicated reference yet: apply static-html.md principles with the framework's head API."}
    if has("vite-react-ssg", "vite-ssg", "react-snap"):
        return {"framework": "vite-prerendered-spa", "rendering": "ssg (prerendered)", "reference": REF + "react-spa.md",
                "build_output": "dist"}
    if has("react", "react-dom") and has("vite", "react-scripts", "@rsbuild/core", "parcel", "webpack"):
        cra = has("react-scripts")
        return {"framework": "react-spa", "bundler": "create-react-app" if cra else "vite" if has("vite") else "other",
                "version": version_of(deps, "react"), "rendering": "spa (client-side only)",
                "reference": REF + "react-spa.md", "build_output": "build" if cra else "dist"}
    if has("vue"):
        return {"framework": "vue-spa", "version": version_of(deps, "vue"), "rendering": "spa (client-side only)",
                "reference": REF + "react-spa.md", "build_output": "dist",
                "note": "Plain Vue SPA. react-spa.md covers SPA prerendering; consider Nuxt for SSR (nuxt-vue.md)."}
    if has("svelte", "solid-js", "preact", "lit"):
        return {"framework": "spa", "rendering": "spa (client-side only)", "reference": REF + "react-spa.md", "build_output": "dist"}

    # Non-JavaScript stacks
    if cfg("hugo.toml", "hugo.yaml", "hugo.json") or (cfg("config.toml") and cfg("archetypes", "layouts")):
        return {"framework": "hugo", "rendering": "ssg", "reference": REF + "static-site-generators.md", "build_output": "public"}
    gemfile = read(os.path.join(root, "Gemfile"))
    if cfg("_config.yml") and ("jekyll" in gemfile or "github-pages" in gemfile or not gemfile):
        return {"framework": "jekyll", "rendering": "ssg", "reference": REF + "static-site-generators.md", "build_output": "_site"}
    if cfg("mkdocs.yml", "mkdocs.yaml"):
        return {"framework": "mkdocs", "rendering": "ssg", "reference": REF + "static-site-generators.md", "build_output": "site"}
    if cfg("wp-config.php", "wp-content", "style.css") and (cfg("wp-config.php", "wp-content") or "Theme Name:" in read(os.path.join(root, "style.css"))):
        return {"framework": "wordpress", "rendering": "ssr (php)", "reference": REF + "cms-platforms.md", "build_output": None}
    if cfg("layout/theme.liquid") or cfg("config/settings_schema.json") and cfg("sections"):
        return {"framework": "shopify-theme", "rendering": "ssr (liquid)", "reference": REF + "cms-platforms.md", "build_output": None}
    if cfg("manage.py") or "django" in read(os.path.join(root, "requirements.txt")).lower() or "django" in read(os.path.join(root, "pyproject.toml")).lower():
        return {"framework": "django", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    if "rails" in gemfile:
        return {"framework": "rails", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    composer = read(os.path.join(root, "composer.json"))
    if "laravel/framework" in composer:
        return {"framework": "laravel", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    py = (read(os.path.join(root, "requirements.txt")) + read(os.path.join(root, "pyproject.toml"))).lower()
    if "flask" in py or "fastapi" in py:
        return {"framework": "flask" if "flask" in py else "fastapi", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    if cfg("go.mod"):
        return {"framework": "go", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    if cfg("*.csproj", "*.sln"):
        return {"framework": "aspnet", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    if has("express", "fastify", "koa", "hono", "@nestjs/core"):
        return {"framework": "node-server", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    if composer or cfg("index.php"):
        return {"framework": "php", "rendering": "ssr", "reference": REF + "server-rendered.md", "build_output": None}
    if cfg("index.html", "public/index.html", "src/index.html", "*.html"):
        return {"framework": "static-html", "rendering": "static", "reference": REF + "static-html.md", "build_output": "."}
    return {"framework": "unknown", "rendering": "unknown", "reference": REF + "static-html.md", "build_output": None,
            "note": "Couldn't identify the stack; inspect the repo and apply static-html.md principles."}


def find_artifacts(root: str) -> Dict[str, List[str]]:
    patterns = {
        "robots": r"(^|/)robots\.(txt|ts|js|mjs|txt\.liquid|txt\.ts)$|(^|/)robots\.txt/\+server\.(ts|js)$",
        "sitemap": r"(^|/)sitemap[^/]*\.(xml|ts|js|mjs|xml\.ts|xml\.js)$|(^|/)sitemap\.xml/\+server\.(ts|js)$|(^|/)sitemap[^/]*\.(xml|njk|liquid|html)$",
        "llms_txt": r"(^|/)llms(-full)?\.txt$",
        "manifest": r"(^|/)(manifest\.(webmanifest|json|ts|js)|site\.webmanifest)$",
        "favicon": r"(^|/)(favicon\.(ico|svg|png)|icon\.(png|svg|ico|tsx|jsx|ts|js)|apple-touch-icon[^/]*\.png|apple-icon\.(png|tsx|jsx))$",
        "og_image": r"(^|/)(opengraph-image|twitter-image)\.(png|jpe?g|tsx|jsx|ts|js)$|(^|/)og[-_]?(image)?[^/]*\.(png|jpe?g|webp)$",
    }
    compiled = {k: re.compile(v, re.I) for k, v in patterns.items()}
    found: Dict[str, List[str]] = {k: [] for k in patterns}
    found.update({"jsonld_in_source": [], "meta_description_in_source": [], "open_graph_in_source": []})
    text_ext = (".html", ".htm", ".tsx", ".jsx", ".ts", ".js", ".mjs", ".vue", ".svelte", ".astro", ".liquid",
                ".php", ".erb", ".njk", ".hbs", ".jinja", ".j2", ".twig", ".cshtml", ".md", ".mdx")
    for path in walk_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        for k, rx in compiled.items():
            if rx.search(rel) and len(found[k]) < 20:
                found[k].append(rel)
        if rel.endswith(text_ext) and os.path.getsize(path) < 300_000 and "/test" not in rel and not rel.endswith(".md"):
            text = read(path)
            if "application/ld+json" in text and len(found["jsonld_in_source"]) < 20:
                found["jsonld_in_source"].append(rel)
            if re.search(r"""name=["']description["']|description\s*:|useSeoMeta|generateMetadata|<SEO|Helmet""", text) \
                    and len(found["meta_description_in_source"]) < 20:
                found["meta_description_in_source"].append(rel)
            if re.search(r"og:title|openGraph|ogTitle", text) and len(found["open_graph_in_source"]) < 20:
                found["open_graph_in_source"].append(rel)
    return found


def find_site_urls(root: str, pkg: Dict[str, Any]) -> List[Dict[str, str]]:
    """Candidate production origins, with where each came from. Only URL-shaped values are read from env files."""
    out: List[Dict[str, str]] = []

    def add(url: str, source: str):
        url = url.rstrip("/")
        if "localhost" in url or "127.0.0.1" in url or "${" in url:
            return
        if not any(o["url"] == url for o in out):
            out.append({"url": url, "source": source})

    for env in sorted(glob.glob(os.path.join(root, ".env*"))):
        for m in URL_ENV_KEYS.finditer(read(env)):
            add(m.group(2), f"{os.path.basename(env)}:{m.group(1)}")
    cname = read(os.path.join(root, "CNAME")).strip() or read(os.path.join(root, "public", "CNAME")).strip()
    if cname and "." in cname and " " not in cname:
        add("https://" + cname.splitlines()[0], "CNAME")
    if isinstance(pkg.get("homepage"), str) and pkg["homepage"].startswith("http"):
        add(pkg["homepage"], "package.json homepage")
    config_patterns = [
        ("astro.config.*", r"site\s*:\s*['\"](https?://[^'\"]+)"),
        ("nuxt.config.*", r"url\s*:\s*['\"](https?://[^'\"]+)"),
        ("docusaurus.config.*", r"url\s*:\s*['\"](https?://[^'\"]+)"),
        ("svelte.config.*", r"origin\s*:\s*['\"](https?://[^'\"]+)"),
        ("next-sitemap.config.*", r"siteUrl\s*:\s*['\"](https?://[^'\"]+)"),
        ("gatsby-config.*", r"siteUrl\s*:\s*['\"](https?://[^'\"]+)"),
        ("hugo.toml", r"baseURL\s*=\s*['\"](https?://[^'\"]+)"),
        ("config.toml", r"baseURL\s*=\s*['\"](https?://[^'\"]+)"),
        ("_config.yml", r"^url\s*:\s*['\"]?(https?://[^'\"\s]+)"),
        ("mkdocs.yml", r"^site_url\s*:\s*['\"]?(https?://[^'\"\s]+)"),
        ("vercel.json", r"\"(https?://[a-z0-9.-]+\.[a-z]{2,})"),
        ("netlify.toml", r"(https?://[a-z0-9.-]+\.[a-z]{2,})"),
        ("wrangler.toml", r"pattern\s*=\s*['\"]([a-z0-9.-]+\.[a-z]{2,})"),
        ("src/**/site*.{ts,js}", r"(https?://[a-z0-9.-]+\.[a-z]{2,})"),
    ]
    for pattern, rx in config_patterns:
        for rel in exists(root, pattern):
            for m in re.finditer(rx, read(os.path.join(root, rel)), re.M | re.I):
                url = m.group(1)
                add(url if url.startswith("http") else "https://" + url, rel)
    return out[:8]


def detect(root: str) -> Dict[str, Any]:
    root = os.path.abspath(root)
    pkg = load_package(root)
    deps: Dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update(pkg.get(key) or {})
    result: Dict[str, Any] = {"root": root}
    result.update(detect_framework(root, deps))
    result["language"] = "typescript" if exists(root, "tsconfig.json") else ("javascript" if pkg else None)
    result["package_manager"] = package_manager(root)
    scripts = pkg.get("scripts") or {}
    result["scripts"] = {k: v for k, v in scripts.items() if k in ("dev", "start", "build", "preview", "generate", "export", "serve", "lint", "typecheck", "test")}
    result["seo_libraries"] = [l for l in SEO_LIBRARIES if l in deps]
    result["i18n"] = sorted(set(deps) & I18N_LIBS) or (["locale directories"] if exists(root, "locales", "src/locales", "i18n", "messages", "src/i18n") else [])
    result["existing_seo"] = find_artifacts(root)
    result["site_url_candidates"] = find_site_urls(root, pkg)

    workspaces = pkg.get("workspaces")
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages")
    ws_globs = list(workspaces or [])
    pnpm = read(os.path.join(root, "pnpm-workspace.yaml"))
    ws_globs += re.findall(r"^\s*-\s*['\"]?([^'\"\n]+)", pnpm, re.M)
    if ws_globs or exists(root, "turbo.json", "nx.json", "lerna.json"):
        apps = []
        for g in ws_globs or ["apps/*", "packages/*"]:
            for d in sorted(glob.glob(os.path.join(root, g))):
                if os.path.isfile(os.path.join(d, "package.json")):
                    sub = load_package(d)
                    sub_deps = {**(sub.get("dependencies") or {}), **(sub.get("devDependencies") or {})}
                    fw = detect_framework(d, sub_deps)
                    if fw["framework"] not in ("unknown", "static-html"):
                        apps.append({"path": os.path.relpath(d, root), "framework": fw["framework"], "reference": fw["reference"]})
        if apps:
            result["monorepo_apps"] = apps
            if result["framework"] in ("unknown", "static-html"):
                result.update(framework="monorepo", rendering="per app", reference=apps[0]["reference"])
            result["note"] = "Monorepo: run detect_stack.py on each public-facing app and apply the skill there."
    return result


def render_text(r: Dict[str, Any]) -> str:
    lines = [f"Framework:        {r['framework']}" + (f" {r['version']}" if r.get("version") else "")
             + (f" ({r['router']} router)" if r.get("router") else ""),
             f"Rendering:        {r.get('rendering')}",
             f"Language:         {r.get('language') or '-'}",
             f"Package manager:  {r.get('package_manager') or '-'}",
             f"Build output:     {r.get('build_output') or '-'}",
             f"Read next:        {r['reference']}"]
    if r.get("note"):
        lines.append(f"Note:             {r['note']}")
    if r.get("scripts"):
        lines.append("Scripts:          " + ", ".join(f"{k}={v!r}" for k, v in r["scripts"].items()))
    if r.get("seo_libraries"):
        lines.append("SEO libraries:    " + ", ".join(r["seo_libraries"]))
    if r.get("i18n"):
        lines.append("i18n:             " + ", ".join(r["i18n"]))
    lines.append("Site URL:         " + (", ".join(f"{c['url']} ({c['source']})" for c in r["site_url_candidates"]) or "not found — ask the user or use a SITE_URL placeholder"))
    lines.append("Existing SEO:")
    for k, v in r["existing_seo"].items():
        lines.append(f"  {k:28} {', '.join(v[:4]) + (' …' if len(v) > 4 else '') if v else '—'}")
    for app in r.get("monorepo_apps", []):
        lines.append(f"  app {app['path']}: {app['framework']} → {app['reference']}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", help="project directory (default: .)")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)
    if not os.path.isdir(args.root):
        ap.error(f"{args.root} is not a directory")
    result = detect(args.root)
    print(json.dumps(result, indent=2) if args.json else render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
