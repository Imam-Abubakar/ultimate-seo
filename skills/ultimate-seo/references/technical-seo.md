# Technical SEO Reference

How search engines crawl, render, and index — and the server/URL decisions that make or break it.

## Contents

1. Crawl → render → index model
2. HTTP status codes
3. Redirects
4. URL normalization (host, protocol, trailing slash, case)
5. robots.txt
6. XML sitemaps
7. Canonicalization and duplicate content
8. Faceted navigation and URL parameters
9. Pagination and infinite scroll
10. JavaScript rendering and SPAs
11. Soft 404s and error pages
12. Staging and preview environments
13. Site migrations checklist
14. Crawl budget (large sites)
15. Log file analysis
16. IndexNow

---

## 1. Crawl → render → index model

1. **Discover** URLs via links (`<a href>`), sitemaps, redirects, and external links. Links in `onclick`, `<button>`, or JS router calls without `href` are not discovered.
2. **Crawl**: fetch raw HTML; obey robots.txt. Googlebot crawls mobile-first (smartphone UA) for nearly all sites.
3. **Render** (Google, Bing): queued headless Chromium executes JS. Can lag crawl. Most other crawlers (social scrapers, most AI crawlers, many SEO tools) do **not** render.
4. **Index**: pick a canonical among duplicates, evaluate quality, store. "Crawled – currently not indexed" in Search Console usually means quality/duplication, not a technical block.
5. **Serve/rank**.

Implication: put titles, meta, canonical, main content, internal links and JSON-LD in the initial HTML response.

---

## 2. HTTP status codes

| Code | Meaning to search engines | Use for |
|---|---|---|
| 200 | Indexable | Real content |
| 301 / 308 | Permanent move; passes signals; target becomes canonical | Changed URLs, host/protocol normalization |
| 302 / 307 | Temporary; original URL kept in index (long-lived 302s get treated as 301) | Geo/AB tests, maintenance |
| 304 | Not modified (conditional GET) | Saves crawl budget — support `ETag`/`Last-Modified` |
| 404 | Not found; dropped after recrawls | Missing content |
| 410 | Gone; dropped slightly faster | Intentionally removed content |
| 429 / 503 | Slow down / temporarily unavailable; Google retries; prolonged → deindexing | Rate limiting, maintenance (add `Retry-After`) |
| 5xx | Server error; repeated → crawl rate reduced, eventually dropped | Never intentionally |

Never serve a 200 "not found" page (soft 404) or a 200 maintenance page site-wide.

---

## 3. Redirects

- Server-side (`301`/`308`) only. Avoid JS redirects and `<meta refresh>` (followed by Google but slower, lossy elsewhere).
- 301 vs 308: equivalent for SEO; 308 preserves method (POST). Frameworks often default to 307/308 — fine.
- **One hop**: `http://example.com/a` → `https://www.example.com/a` directly, not via two hops. Chains > 5 hops are abandoned by Googlebot.
- Update internal links to the final URL; don't rely on redirects internally.
- Redirect to the closest relevant page, not the home page (mass home redirects = soft 404s).
- Keep migration redirects at least 1 year, ideally forever.

---

## 4. URL normalization

Pick one form for each and 301 everything else to it:

| Dimension | Decision | Notes |
|---|---|---|
| Protocol | `https` | HSTS header after confident: `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| Host | `www` **or** apex | Either is fine; be consistent everywhere (canonical, sitemap, OG, schema, internal links) |
| Trailing slash | with **or** without | Match framework default (Next.js: without; Astro/Hugo/Gatsby/Jekyll: usually with) — and configure the server to 301 the other |
| Case | lowercase | Many servers are case-sensitive → duplicates |
| Index files | `/blog/` not `/blog/index.html` | 301 `index.html` variants |
| Parameters | stable order, no empty params | Strip tracking params in canonical |

URL design: short, lowercase, hyphen-separated words, meaningful hierarchy (`/blog/late-payment-email`), no IDs-only slugs when avoidable, no dates in evergreen content URLs, ASCII or properly UTF-8 percent-encoded.

---

## 5. robots.txt

Served at `/robots.txt` on each host (and protocol/port), UTF-8, < 500 KiB, status 200. A 404 = everything allowed; a 5xx = Google treats as full disallow temporarily.

```txt
User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/
Disallow: /cart
Disallow: /checkout
Disallow: /search
Disallow: /*?*sessionid=

Sitemap: https://www.example.com/sitemap.xml
```

Syntax rules:
- Groups start with one or more `User-agent` lines; a crawler obeys **only the most specific matching group** (not `*` plus its own). If you add a `User-agent: GPTBot` group, repeat any rules from `*` you want applied to it.
- Most specific (longest) path match wins between `Allow` and `Disallow`; on a tie, `Allow` wins (Google/Bing).
- Wildcards: `*` any sequence, `$` end of URL. Paths are case-sensitive.
- `Sitemap:` lines are global, absolute URLs, any number.
- `Crawl-delay` is ignored by Google; respected by Bing/Yandex.
- `Noindex:` in robots.txt is unsupported (since 2019).

Rules:
- robots.txt controls **crawling, not indexing**. A disallowed URL can still be indexed (URL only) from external links. To remove from index: allow crawl + `noindex`.
- Don't block CSS, JS, images, or fonts needed to render.
- Don't disallow URLs that are canonical targets or that hold `noindex` you need seen.
- Staging: don't rely on robots.txt; use auth or `X-Robots-Tag: noindex`.

Test: Search Console robots.txt report; `curl -A Googlebot https://site/robots.txt`.

---

## 6. XML sitemaps

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.example.com/blog/late-payment-email</loc>
    <lastmod>2026-09-14</lastmod>
  </url>
</urlset>
```

- Limits: **50,000 URLs or 50 MB uncompressed** per file. Larger → sitemap index (`<sitemapindex>` with `<sitemap><loc>`), up to 50,000 sitemaps. gzip allowed.
- Include only canonical, indexable, 200-status URLs on the same host. No redirects, 404s, noindex, parameter duplicates, or blocked URLs. Sitemap/canonical disagreement weakens both.
- `lastmod`: W3C datetime; **must reflect real content change** (DB `updatedAt`, git commit date, frontmatter). Google uses it only if it proves consistently accurate. Never stamp build time on every URL.
- `changefreq` and `priority`: ignored by Google. Omit.
- Segment by type for diagnostics: `sitemap-pages.xml`, `sitemap-posts.xml`, `sitemap-products.xml` under an index; Search Console reports indexing per sitemap.
- Reference from robots.txt and submit in Search Console + Bing Webmaster Tools.
- Extensions (separate namespaces):
  - **Image**: `xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"`, `<image:image><image:loc>…</image:loc></image:image>` — useful when images are lazy-loaded via JS or on CDN hosts.
  - **Video**: `xmlns:video="http://www.google.com/schemas/sitemap-video/1.1"`, requires `thumbnail_loc`, `title`, `description`, `content_loc` or `player_loc`.
  - **News**: `xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"`; only articles from last 2 days, ≤1000 URLs; publisher name + language + publication_date + title.
  - **hreflang**: `xmlns:xhtml="http://www.w3.org/1999/xhtml"` with `<xhtml:link rel="alternate" hreflang="…" href="…"/>` — see `international.md`.

Verify against current docs: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

---

## 7. Canonicalization and duplicate content

Common duplicate sources: host/protocol variants, trailing slash, `index.html`, tracking params, sort/filter params, session IDs, print pages, printer/AMP versions, HTTP vs HTTPS, staging leaks, case variants, product in multiple categories (`/men/shoes/x` and `/sale/x`), syndicated copies.

Signals Google combines to pick a canonical (strongest first): redirects > `rel=canonical` > sitemap inclusion > internal links > HTTPS > shorter/cleaner URL. Make them all agree.

Fixes:
- Products in multiple categories: one canonical product URL (`/products/x`) linked from all categories.
- Near-duplicate locations/variants: consolidate or differentiate content substantially.
- Duplicate content is not a "penalty" — it splits signals and wastes crawl. Scraped/spun duplicates at scale are a spam issue.

---

## 8. Faceted navigation and URL parameters

Faceted filters (color × size × brand × price × sort) can generate millions of URLs.

Strategy:
1. Decide which facet combinations have **search demand** (e.g. `/shoes/red`, `/shoes/nike`). Give them clean static paths, unique titles/H1/copy, self-canonical, sitemap inclusion.
2. All other combinations: keep functional for users but make them non-indexable and ideally uncrawlable:
   - Prefer: don't render them as crawlable links (use `<button>`/form controls or `rel="nofollow"` links) **and** canonical to the base listing or `noindex`.
   - Large sites with crawl waste: `Disallow` param patterns in robots.txt (`Disallow: /*?*sort=`) — but then canonical/noindex on those URLs won't be seen; acceptable for pure crawl-trap params.
3. Sort order, view mode, page size, session params: never indexable.
4. Consistent parameter order and no empty params.

Google retired the Search Console URL Parameters tool (2022) — control must be on-site.

---

## 9. Pagination and infinite scroll

- Each page has its own URL (`?page=2` or `/page/2/`), self-canonical, crawlable `<a href>` links between pages.
- Infinite scroll / "load more": back it with paginated URLs, update URL via History API as the user scrolls, ensure `<a href="?page=2">` exists in HTML for crawlers.
- "View all" page: canonicalize components to it only if it loads fast; otherwise standard pagination.
- Deep pagination is a weak discovery path for important items — also link them via categories, related items, and sitemaps.

---

## 10. JavaScript rendering and SPAs

Google renders JS, but with costs: delay, render budget, failures on blocked resources, timeouts, and no user interaction (no clicks, scrolls, or permission prompts). Bing renders less reliably; social scrapers and most AI crawlers not at all.

Rendering options, best to worst for SEO: **SSG/prerender** ≈ **SSR** > hybrid (SSR shell + client hydration) > dynamic rendering (serving bots a prerendered copy — deprecated workaround, Google calls it a workaround not a solution) > pure CSR.

CSR pitfalls checklist:
- Empty `<div id="root">` in raw HTML → nothing for non-rendering crawlers. Check with `curl -s URL | grep -c '<h1'`.
- Client-side routing that returns 200 + `index.html` for every path → every bad URL is a soft 404. Need server-side 404 for unknown routes (prerender a route manifest, or edge function).
- Metadata set only after JS (e.g. `document.title`, react-helmet without SSR) → scrapers see the default.
- Links as `onClick` handlers without `href`.
- Hash routing (`/#/about`) → fragments are ignored; all routes are one URL. Use History API routing.
- Content behind interaction (tabs fetched on click, "load more" without URL).
- Lazy-loading via scroll events (Googlebot doesn't scroll; it uses a tall viewport). Use `loading="lazy"` or IntersectionObserver.
- Blocked API endpoints in robots.txt that the page needs to render content.
- `noindex` in initial HTML removed by JS — Google may not render; the initial noindex wins.

Test: Search Console URL Inspection → "View crawled page"; Rich Results Test (renders); compare `curl` vs browser DOM.

---

## 11. Soft 404s and error pages

A soft 404 is a page returning 200 that looks empty/error-like ("No products found", "Page not found" template, redirects to home).

- Unknown routes must return a real 404 (or 410). Custom 404 page content is fine — status must be 404.
- Empty category/search pages: `noindex` or 404 when permanently empty.
- Out-of-stock products: keep 200 with availability `OutOfStock` if returning; 301 to replacement or 404/410 if discontinued permanently.
- SPAs: see §10.

---

## 12. Staging and preview environments

Leaked staging sites cause duplicate content and can outrank production.

- Best: HTTP auth / IP allowlist / Vercel/Netlify protected previews.
- Plus: `X-Robots-Tag: noindex, nofollow` header on all non-production hosts (gated by env var like `VERCEL_ENV !== 'production'` or `CONTEXT !== 'production'`).
- Canonical URLs everywhere should use the production origin env var — so even if a preview is crawled, signals point to prod.
- Never ship a robots.txt `Disallow: /` that could be deployed to production; generate robots.txt from env.

---

## 13. Site migrations checklist

Domain change, URL restructure, platform/framework rewrite, HTTPS move.

Before:
- [ ] Crawl old site; export all URLs with traffic/links (Search Console, analytics, backlink tool, server logs).
- [ ] Build 1:1 redirect map old → closest new URL. Avoid mass redirects to home.
- [ ] Benchmark rankings, traffic, indexed pages, Core Web Vitals.
- [ ] Preserve titles, content, internal links, structured data for top pages.

Launch:
- [ ] Deploy 301s (one hop), test the full map with a script (`curl -sI` each, expect 301 → 200).
- [ ] New sitemap submitted; keep old sitemap (with old URLs) submitted briefly so Google recrawls redirects.
- [ ] Domain change: Search Console Change of Address tool; verify both properties.
- [ ] Update canonicals, hreflang, OG, schema, internal links to new URLs.
- [ ] Remove staging noindex/auth from production (most common migration disaster).

After:
- [ ] Monitor 404s, crawl errors, index coverage daily for 2 weeks, weekly for 3 months.
- [ ] Update external links you control (social profiles, directories, GBP).
- [ ] Expect fluctuation for weeks; keep redirects ≥ 1 year.

---

## 14. Crawl budget (large sites)

Only matters for roughly >10k frequently changing URLs or >1M URLs, or when Search Console shows "Discovered – currently not indexed" at scale.

- Eliminate crawl traps (facets, calendars, session IDs, infinite param combos).
- Fast responses (server time < 200 ms for HTML) — Google raises crawl rate for fast, healthy hosts.
- Support conditional requests (304).
- Remove/redirect soft 404s and long redirect chains.
- Keep sitemaps clean and `lastmod` accurate.
- Strong internal linking to important pages (link depth ≤ 3 from home).
- Monitor Search Console → Settings → Crawl stats.

---

## 15. Log file analysis

Server/CDN logs show what bots actually fetch.

- Verify Googlebot by reverse DNS (`googlebot.com`/`google.com`) or Google's published IP ranges; user agents are spoofed constantly. Same for Bingbot and AI crawlers (OpenAI, Anthropic, Perplexity publish IP ranges).
- Questions to answer: % of crawl on non-canonical/parameter URLs; important pages never crawled; 4xx/5xx served to bots; response times for bots; AI crawler volume.
- Tools: Screaming Frog Log File Analyser, CDN analytics (Cloudflare AI Crawl Control/bot analytics), BigQuery on raw logs.

---

## 16. IndexNow

Protocol to notify Bing, Yandex, Seznam, Naver and others (not Google) instantly when URLs change.

1. Generate a key (8–128 hex chars), host it at `https://example.com/{key}.txt` containing the key.
2. On publish/update/delete, POST:

```http
POST https://api.indexnow.org/indexnow
Content-Type: application/json

{"host":"www.example.com","key":"<key>","keyLocation":"https://www.example.com/<key>.txt","urlList":["https://www.example.com/blog/new-post"]}
```

- Worth it for frequently updated sites (news, e-commerce, listings). Many CDNs/CMSs have one-click support (Cloudflare Crawler Hints, Yoast, Rank Math).
- Google does not use IndexNow; rely on sitemaps + `lastmod` for Google. The Indexing API is officially limited to JobPosting and livestream BroadcastEvent pages.

Verify against current docs: https://www.indexnow.org/documentation
