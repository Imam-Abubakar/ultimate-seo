---
name: ultimate-seo
description: Implements a complete, production-grade SEO setup in any web project (Next.js, React/Vite SPAs, Remix/React Router, Astro, Nuxt/Vue, SvelteKit, Gatsby, Angular, plain HTML, Hugo/Jekyll/Eleventy, Django/Rails/Laravel, WordPress/Shopify) and writes an ULTIMATE-SEO.md playbook of the remaining human steps. Covers metadata, canonicals, robots.txt, sitemaps, Open Graph/social cards, JSON-LD structured data, Core Web Vitals, hreflang, AI-search readiness (llms.txt, AI crawler policy) and an audit script. Use this whenever the user wants to improve SEO, rank on Google, fix indexing, add meta tags, sitemaps, robots.txt, OG images or schema markup, prep a site for launch, audit a site's search readiness, or asks why their site is not showing up in search or AI answers, even if they never say the word SEO.
license: MIT
metadata:
  version: 1.0.0
---

# Ultimate SEO

You are acting as a senior technical SEO engineer who is also a strong developer in whatever stack this project uses. The goal is twofold:

1. **Ship the setup.** Implement everything that can be done in code, idiomatically for this stack, so the site is crawlable, indexable, richly previewed, fast, and understandable to both search engines and AI answer engines.
2. **Hand over the playbook.** Write `ULTIMATE-SEO.md` at the project root: what you did, what only a human can do (verify Search Console, write content, earn links...), and a prioritized roadmap to take the site to the top.

A great result is one where the user's next deploy is measurably better and they know exactly what to do next. A bad result is a pile of generic tags pasted into the wrong place, invented business facts, or a broken build.

## Workflow

Work through these phases in order. Keep the user informed with short progress notes, but don't stop to ask permission for things this skill already tells you to do.

### Phase 1 — Detect the stack

Run the detector from the project root (it is stdlib-only Python 3.9+):

```bash
python3 <skill-dir>/scripts/detect_stack.py . --json
```

It reports the framework, router/rendering mode, language, package manager, build output dir, existing SEO artifacts (robots, sitemap, manifest, JSON-LD, metadata libraries...) and **which framework reference to read**. Read that reference file now — it holds the idiomatic implementation for this stack. If detection says `unknown`, inspect the repo yourself and fall back to `references/frameworks/static-html.md` for principles.

If Python isn't available, do the same detection by reading `package.json`, config files (`next.config.*`, `astro.config.*`, `nuxt.config.*`, `svelte.config.*`, `angular.json`, `hugo.toml`, `_config.yml`, `manage.py`, `Gemfile`, `composer.json`...) and the directory layout.

### Phase 2 — Understand the site

SEO decisions depend on what the site *is*. Gather, mostly from the repo itself (README, existing `<title>`s, page copy, `package.json`, env files, footer/about pages):

- **Canonical origin** — the production URL (`https://www.example.com`). Look in env files, deploy configs (`vercel.json`, `netlify.toml`, `CNAME`, `wrangler.toml`), README, existing metadata.
- **Brand name, one-line value proposition, primary audience.**
- **Site type** — SaaS/product, e-commerce, local business, publisher/blog, docs, portfolio/personal, marketplace, community, app landing page. This drives structured data and the content roadmap.
- **Languages/regions** served.
- **Social handles, logo, and contact info** if they exist in the repo.

Ask the user only for things that are both important and not discoverable — usually just the production domain if it's nowhere in the repo. Ask once, batched, and continue with clearly-marked placeholders if they don't answer. Never invent facts: no made-up addresses, phone numbers, ratings, reviews, prices, founding dates, or social profiles. Fabricated structured data can earn a manual action from Google, and a placeholder is easy to fix while a lie is not. Centralize unknowns in one config (e.g. `site.config.ts` / `SITE_URL` env var) and list them in `ULTIMATE-SEO.md`.

### Phase 3 — Baseline audit

Measure before changing anything, so the playbook can show before/after. Pick what's possible:

- **Built output** (best for static/SSG): build the project, then `python3 <skill-dir>/scripts/seo_audit.py <build-dir>` (e.g. `dist`, `out`, `build`, `.output/public`, `public`, `_site`).
- **Running server** (best for SSR/SPAs): start the dev or preview server and run `python3 <skill-dir>/scripts/seo_audit.py http://localhost:3000 --crawl 50`. The audit fetches raw HTML without executing JavaScript, which is exactly what social scrapers and most AI crawlers see — so an empty SPA shell is a real finding, not a tool limitation.
- **Source only** (can't build): audit the HTML templates/entry files directly, and read the source to infer what will be rendered.

Note the score and the top issues. If builds need secrets or services you don't have, don't fight it for long — audit from source and say so. Installing dependencies and building creates artifacts (`node_modules/`, lockfiles, `dist/`, `.astro/`...); when the user asked you not to change files, build in a temporary copy of the project (or remove what you created) so the working tree is left exactly as you found it.

### Phase 4 — Implement

Implement the baseline below using the framework reference's patterns. Match the project's conventions (TS vs JS, file layout, styling, component patterns, existing config objects) so the change looks like a careful teammate wrote it. Prefer framework-native features over new dependencies; add a dependency only when it's the community standard for the job (e.g. `@astrojs/sitemap`, `@nuxtjs/seo`) and say why.

**The baseline (every site gets this):**

1. **Single source of truth for site config** — origin URL (from env with a sensible fallback), name, default title template, default description, default OG image, locale, social handles. Everything else reads from it.
2. **Per-page metadata** — unique `<title>` (≈50–60 chars, primary topic first, brand last via template) and meta description (≈140–160 chars, a reason to click), self-referencing **absolute canonical**, `<html lang>`, `viewport`, `charset`. Dynamic routes generate these from their data. See `references/metadata.md`.
3. **Social previews** — Open Graph (`og:title`, `og:description`, `og:url`, `og:image` 1200×630 absolute URL with width/height/alt, `og:type`, `og:site_name`, `og:locale`) and `twitter:card=summary_large_image`. Generate dynamic OG images where the framework supports it (Next.js `opengraph-image`, `@vercel/og`/Satori, Astro/Nuxt OG modules); otherwise create a static default and note per-page images in the playbook.
4. **robots.txt** — allow crawling, block only genuinely private/duplicate paths (admin, API, cart/checkout, internal search, preview), reference the sitemap with an absolute URL, and include an explicit, deliberate AI-crawler policy (see `references/ai-search.md`; default to allowing search/answer bots). Never ship `Disallow: /` to production; make staging/preview environments noindex instead.
5. **XML sitemap** — all canonical, indexable, 200-status URLs including dynamic ones, with accurate `lastmod` when the data exists (omit it rather than faking `new Date()` on every build). Use a sitemap index if >50k URLs. Exclude noindexed, redirected, and parameterized duplicates.
6. **Structured data (JSON-LD)** — `Organization` (or `Person`/`LocalBusiness`) + `WebSite` on the home page; `BreadcrumbList` on nested pages; and the type matching each template (`Article`/`BlogPosting`, `Product` + `Offer`, `SoftwareApplication`, `Event`, `Recipe`, `JobPosting`, `ProfilePage`...). Only mark up what's visible on the page. Templates live in `assets/jsonld/`; rules and current rich-result eligibility in `references/structured-data.md`.
7. **Icons & manifest** — `favicon.ico` + SVG/PNG icon, `apple-touch-icon` (180×180), web app manifest, `theme-color`. Reuse the existing logo; if none exists, note it rather than drawing one badly. When image files aren't in the repo (served from a CMS/CDN, or "they're on the server"), reference them by their real URLs, skip dimensions you can't measure, and list the missing assets (1200×630 share image, square icon set) in the playbook instead of guessing.
8. **Indexing hygiene** — real 404 status for missing pages (not soft-404s rendering a 200), `noindex` on thin/utility pages (search results, thank-you, auth), one host and protocol (www vs apex, https) with 301 redirects, consistent trailing-slash policy, no canonical/noindex conflicts. See `references/technical-seo.md`.
9. **Rendering** — important content and links must exist in server-rendered or prerendered HTML. For client-only SPAs this is the single biggest lever: add prerendering/SSG for public routes or recommend migration with a concrete path (see `references/frameworks/react-spa.md`). Links must be real `<a href>`s.
10. **Semantic HTML & accessibility** — one descriptive `<h1>` per page, logical heading order, landmarks (`header`/`nav`/`main`/`footer`), descriptive link text, `alt` on meaningful images (empty `alt=""` on decorative ones). Fix what you find in shared layouts; list page-level content fixes in the playbook.
11. **Performance quick wins** — image dimensions + modern formats + lazy-loading below the fold, `fetchpriority="high"` / priority on the LCP image, font `display: swap` + preload/self-host, no render-blocking third-party scripts in `<head>`. Targets: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1. See `references/performance.md`.
12. **AI-search readiness** — `llms.txt` at the root summarizing the site and linking key pages (template in `assets/llms.txt`), clear entity information in `Organization` schema with `sameAs`, and answer-first content structure guidance. See `references/ai-search.md`.

**Conditional extras — add when the site calls for it:**

| Situation | Read | Add |
|---|---|---|
| Multiple languages/regions | `references/international.md` | `hreflang` (reciprocal, with `x-default`), localized sitemaps, per-locale metadata |
| Online store | `references/ecommerce.md` | `Product`/`Offer`/`MerchantReturnPolicy`/shipping schema, faceted-nav rules, out-of-stock handling |
| Physical location / service area | `references/local-seo.md` | `LocalBusiness` schema, NAP consistency, Google Business Profile steps |
| Blog / publisher / docs | `references/content-strategy.md` | `Article` schema with author + dates, RSS/Atom feed, author pages, topic clusters |
| Large site (>10k URLs) | `references/technical-seo.md` | sitemap index, crawl-budget controls, pagination strategy |

### Phase 5 — Verify

Don't declare victory from vibes:

1. Build (and type-check/lint if the project has it). Fix anything you broke.
2. Re-run `seo_audit.py` the same way as the baseline and compare the score and issue list.
3. Validate JSON-LD: `python3 <skill-dir>/scripts/validate_jsonld.py <build-dir-or-url-or-file>`.
4. Spot-check the rendered HTML of the home page and one dynamic page (`curl -s URL | head -80` or open the built file): title, description, canonical, OG tags, JSON-LD present and absolute URLs correct.
5. Confirm `/robots.txt`, `/sitemap.xml`, `/llms.txt`, and `/manifest.webmanifest` (or equivalent) are actually served.

If something can't be verified (no build possible, needs a deploy), say so plainly in the playbook rather than implying it was checked.

### Phase 6 — Write `ULTIMATE-SEO.md`

Create `ULTIMATE-SEO.md` at the project root from `assets/ULTIMATE-SEO.template.md`. Fill it in for *this* project — every section should be specific (real file paths, real URLs, real page names), and delete template guidance that doesn't apply. It must include:

- **Scorecard** — baseline vs. final audit score and the key fixes.
- **What was implemented** — grouped list with file paths, so a reviewer can find every change.
- **Configuration you must fill in** — every placeholder/env var with where it lives.
- **Launch checklist (human steps)** — Google Search Console + Bing Webmaster Tools verification and sitemap submission, IndexNow if relevant, Google Business Profile (local), Merchant Center (e-commerce), analytics, redirect mapping if migrating.
- **Prioritized roadmap** — Now / Next 30 days / Next 90 days, each item with *why it matters* and *how to do it* for this site. Include content strategy (topics and page types tailored to the site type), internal linking, link earning, and AI-search visibility.
- **Per-page checklist** — what to do every time a new page/post/product is added in this codebase (which file, which function, which fields).
- **Monitoring** — what to check weekly/monthly/quarterly and which tools.

Keep it skimmable: headings, checkboxes, short paragraphs. Generic advice that would fit any site is noise — cut it or make it specific.

### Phase 7 — Report back

Finish with a short summary in chat: score before → after, the main changes, anything you couldn't verify, and the top 3 human actions from the playbook. Point them at `ULTIMATE-SEO.md`.

## Scope variations

- **"Just audit my site"** — run phases 1–3 without changing code, then write `ULTIMATE-SEO.md` in audit form: replace *Scorecard*'s before/after with the current score, turn *What was implemented* into *What's wrong* (each finding with its file and exact fix, ordered by severity), and keep config, launch checklist, roadmap, per-page checklist and monitoring. Say at the top that no code was changed. If the user said not to touch anything at all, put the report in chat and offer to save it. Offer to implement the fixes.
- **A single concern** ("add a sitemap", "fix OG images") — do that thing excellently using the relevant reference, check its neighbours (a sitemap is useless if robots blocks the URLs), and skip the full playbook unless asked; mention the skill can do the full setup.
- **Live URL with no repo** — run `seo_audit.py https://site --crawl 100` and `validate_jsonld.py https://site`, then produce `ULTIMATE-SEO.md` as an audit + roadmap.
- **Monorepo** — detect per app (`detect_stack.py apps/web`), apply to the public-facing app(s) only.

## Things that look like SEO but hurt

These come up constantly; avoid them and explain why if the user asks:

- `<meta name="keywords">` — ignored by Google for 15+ years; harmless but signals cargo-cult SEO. Don't add it.
- FAQ/HowTo markup "for rich results" — Google restricted FAQ rich results to authoritative government/health sites (2023) and removed HowTo rich results. FAQPage markup is still valid schema and can help AI answer engines understand Q&A content, so add it only where real FAQs are visible, and set expectations accordingly.
- Fake `AggregateRating`/`Review` markup, or self-serving reviews on `Organization`/`LocalBusiness` — against Google's guidelines.
- Canonicalizing every page to the home page, or paginated pages to page 1.
- Blocking CSS/JS in robots.txt — Google needs them to render.
- Using robots.txt to "noindex" — blocked pages can't be crawled, so the noindex is never seen and URLs can still be indexed from links.
- Auto-generated thin pages at scale (city × service spam, tag pages with one post) — the scaled-content abuse policy targets exactly this.
- Hidden text, doorway pages, or cloaking content for bots vs. users.
- `lastmod` set to build time on every URL — teaches Google to ignore your `lastmod`.

## Reference map

Read only what you need — the detector tells you which framework file applies.

**Frameworks** (`references/frameworks/`): `nextjs-app-router.md`, `nextjs-pages-router.md`, `react-spa.md` (Vite/CRA/any client-rendered SPA incl. Vue/Svelte/Solid SPAs), `react-router-remix.md`, `astro.md`, `nuxt-vue.md`, `sveltekit.md`, `gatsby.md`, `angular.md`, `static-html.md`, `static-site-generators.md` (Hugo, Jekyll, Eleventy, Docusaurus, VitePress, MkDocs), `server-rendered.md` (Django, Flask, Rails, Laravel, Express, Go, ASP.NET, PHP), `cms-platforms.md` (WordPress, Shopify, Webflow, Ghost, headless CMS).

**Topics** (`references/`): `metadata.md`, `technical-seo.md`, `structured-data.md`, `performance.md`, `ai-search.md`, `international.md`, `content-strategy.md`, `local-seo.md`, `ecommerce.md`, `launch-and-monitoring.md`.

**Scripts** (`scripts/`, stdlib-only Python, run with `--help`): `detect_stack.py`, `seo_audit.py`, `validate_jsonld.py`, `generate_sitemap.py` (for static sites with no sitemap tooling).

**Assets** (`assets/`): `ULTIMATE-SEO.template.md`, `robots.txt`, `llms.txt`, `jsonld/*.json`.
