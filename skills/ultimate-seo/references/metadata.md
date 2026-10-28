# Metadata Reference

Stack-agnostic rules for everything that lives in `<head>` (or the equivalent HTTP headers). Framework files show *where* to put it; this file says *what* to put.

## Contents

1. Baseline head checklist
2. Titles
3. Meta descriptions
4. Canonical URLs
5. Robots meta and X-Robots-Tag
6. Open Graph
7. Twitter / X cards
8. Social image specs
9. Icons, manifest, theme-color
10. Verification tags
11. Pagination and alternates
12. What not to add

---

## 1. Baseline head checklist

Order matters a little: `charset` must be in the first 1024 bytes; put `viewport` next, then `<title>`.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Invoice Software for Freelancers | Acme</title>
  <meta name="description" content="Send professional invoices in 60 seconds, get paid by card or bank transfer, and chase late payments automatically. Free for up to 5 clients.">
  <link rel="canonical" href="https://www.acme.com/invoicing">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Acme">
  <meta property="og:title" content="Invoice Software for Freelancers">
  <meta property="og:description" content="Send professional invoices in 60 seconds and get paid faster.">
  <meta property="og:url" content="https://www.acme.com/invoicing">
  <meta property="og:image" content="https://www.acme.com/og/invoicing.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Acme invoice editor showing a paid invoice">
  <meta property="og:locale" content="en_US">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="@acme">

  <link rel="icon" href="/favicon.ico" sizes="32x32">
  <link rel="icon" href="/icon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="manifest" href="/manifest.webmanifest">
  <meta name="theme-color" content="#0f172a">

  <script type="application/ld+json">{ ... }</script>
</head>
```

Every URL in metadata (canonical, og:url, og:image, hreflang, JSON-LD) must be **absolute** with the production origin. Relative `og:image` silently breaks most scrapers.

---

## 2. Titles

Google rewrites ~60% of titles when they're poor; good titles survive.

**Rules**
- Unique per indexable URL. Duplicate titles across pages are a top audit finding.
- Primary topic/keyword first, brand last via a template: `%s | Brand` or `%s – Brand`.
- ≈50–60 characters (Google truncates by pixel width ~580px). Shorter is fine; never pad.
- Describe the page, not the site. Home page may be `Brand – value proposition`.
- Match the `<h1>` intent (not necessarily identical text). Mismatch is the #1 reason Google rewrites titles.
- No keyword lists, no ALL CAPS, no repeated brand (`Acme | Pricing | Acme`).
- Dynamic pages: build from data (`{product.name} – {category} | Brand`). Paginated: append `– Page 2`.

| Bad | Why | Good |
|---|---|---|
| `Home` | Says nothing | `Acme – Invoicing for Freelancers` |
| `Acme \| Acme Invoicing \| Invoices, Invoice App, Free Invoice` | Stuffed, repetitive | `Free Invoice App for Freelancers \| Acme` |
| `Blog Post` (on 400 posts) | Duplicate | `How to Write a Late Payment Email (Templates) \| Acme` |
| `Welcome to the official website of Acme Corporation Ltd, the leading…` | Too long, no topic | `Acme – Industrial Valves & Fittings` |

---

## 3. Meta descriptions

Not a ranking factor, but drives click-through and is often reused by social/AI previews.

- ≈140–160 characters (mobile shows ~120). Front-load the value.
- Unique per page; for templated pages, generate from real data (price, specs, excerpt) rather than one shared string.
- Write it as a pitch: what the page gives + a reason to click. Include the primary term naturally (Google bolds matches).
- No quotes unescaped (`"` ends the attribute), no emoji spam.
- If you can't write a good one for a long-tail page type, omitting it is better than a duplicated generic one — Google will generate from content.

Bad: `This is the pricing page of Acme.`
Good: `Acme pricing: free for up to 5 clients, $12/month for unlimited invoices, recurring billing and automatic reminders. No card needed to start.`

---

## 4. Canonical URLs

`<link rel="canonical">` tells search engines which URL is the representative one among duplicates. It is a strong hint, not a directive.

- Every indexable page: **self-referencing, absolute** canonical on the preferred host, protocol and trailing-slash form.
- Strip tracking params (`utm_*`, `gclid`, `fbclid`, `ref`) and session IDs from the canonical.
- Sorting/filter variants canonicalize to the unfiltered listing **only** if content is substantially the same; filters that create genuinely distinct pages you want indexed (e.g. `/shoes/red`) get their own self-canonical and clean paths.
- Paginated pages: page 2 canonicalizes to **page 2**, not page 1.
- Never canonicalize to a URL that redirects, 404s, or is `noindex`.
- Never combine `noindex` and a canonical pointing elsewhere (conflicting signals).
- One canonical per page. Frameworks plus plugins often emit two — check rendered HTML.
- Cross-domain canonical is valid for syndicated content (point to the original).
- HTTP header form for non-HTML (PDFs): `Link: <https://example.com/doc.pdf>; rel="canonical"`.

---

## 5. Robots meta and X-Robots-Tag

Default (no tag) = `index, follow`. Only add the tag when you need to change behaviour or opt in to richer previews.

```html
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
```

| Directive | Effect |
|---|---|
| `noindex` | Drop from index. Page must be crawlable for this to be seen. |
| `nofollow` | Don't follow links on page (rarely what you want; prefer per-link `rel`). |
| `none` | `noindex, nofollow` |
| `noarchive` | Legacy cache directive; Google removed the cache link in 2024. Unnecessary. |
| `nosnippet` | No text snippet; also excludes content from AI Overviews/AI Mode snippets. Heavy-handed. |
| `max-snippet:N` | Cap snippet length; `-1` = no limit. `0` = nosnippet. |
| `max-image-preview:none\|standard\|large` | `large` is recommended — enables big images in Discover and results. |
| `max-video-preview:N` | Seconds; `-1` = no limit. |
| `notranslate` | No translation offer in results. |
| `noimageindex` | Don't index images on page. |
| `unavailable_after: 2026-12-31` | Drop after date (events, promos). |
| `indexifembedded` | With `noindex`, allow indexing when embedded via iframe. |

`data-nosnippet` attribute on an element excludes just that element from snippets.

Bot-specific: `<meta name="googlebot" content="noindex">`, `<meta name="bingbot" ...>`.

**X-Robots-Tag** — same directives as an HTTP header; required for non-HTML (PDF, images) and convenient for whole environments:

```
X-Robots-Tag: noindex, nofollow
```

Use it on staging/preview deployments (set by env at the edge/server level), on `/api/*` JSON, and on downloadable files you don't want indexed.

**Pages that typically get `noindex`:** internal search results, cart/checkout/account, auth pages, thank-you/confirmation, thin tag/archive pages, print views, A/B variant URLs, staging. Keep them out of the sitemap too.

---

## 6. Open Graph

Used by Facebook, LinkedIn, Slack, Discord, iMessage, WhatsApp, Teams, Telegram, Pinterest, and many AI chat link previews. Scrapers do **not** run JavaScript — tags must be in server/prerendered HTML.

| Property | Required | Notes |
|---|---|---|
| `og:title` | yes | Can omit brand suffix; ≤ ~70 chars |
| `og:description` | recommended | ≤ ~200 chars |
| `og:url` | yes | Absolute canonical URL |
| `og:image` | yes | Absolute URL, https |
| `og:image:width` / `og:image:height` | recommended | Lets scrapers render on first share |
| `og:image:alt` | recommended | Accessibility |
| `og:image:type` | optional | `image/png`, `image/jpeg`, `image/webp` |
| `og:type` | yes | `website` (default), `article`, `profile`, `product` (non-standard but used), `video.other`, `music.song`, `book` |
| `og:site_name` | recommended | Brand |
| `og:locale` | recommended | `en_US` format (underscore). Alternates: `og:locale:alternate` |

Article extras: `article:published_time`, `article:modified_time` (ISO 8601), `article:author` (URL), `article:section`, `article:tag`.

Facebook-specific `fb:app_id` is optional (only for Facebook Insights). LinkedIn caches aggressively — use the Post Inspector to refresh.

---

## 7. Twitter / X cards

X falls back to OG tags for title/description/image, so the minimum is:

```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@brand">     <!-- only if a real handle exists -->
<meta name="twitter:creator" content="@author"> <!-- articles, optional -->
```

Card types: `summary` (square thumbnail), `summary_large_image` (wide), `player`, `app`. Add `twitter:title`/`twitter:description`/`twitter:image` only when they should differ from OG. Note: Twitter tags use `name=`, OG tags use `property=`.

---

## 8. Social image specs

| Use | Size | Ratio | Notes |
|---|---|---|---|
| OG / summary_large_image | **1200×630** | 1.91:1 | Universal default. Keep key content in the centre ~1000×500 (some crops are square). |
| summary (square) | 1200×1200 min 144×144 | 1:1 | |
| Pinterest | 1000×1500 | 2:3 | Optional extra |

- Format: PNG or JPEG (WebP supported by most, not all, scrapers — use PNG/JPEG for safety). Keep < 5 MB, ideally < 300 KB.
- Text large enough to read at thumbnail size (≥ 48px at 1200 width), high contrast, brand mark present.
- Per-page dynamic images (title + brand) beat one generic image; generate at build or via an edge function (Satori/`@vercel/og`, `next/og`, Astro/Nuxt OG modules, Cloudinary/imgix text overlays).
- Cache-bust by changing URL (`?v=2` or hashed filename) — scrapers cache by URL.

Debuggers: Facebook Sharing Debugger (developers.facebook.com/tools/debug), LinkedIn Post Inspector (linkedin.com/post-inspector), opengraph.xyz.

---

## 9. Icons, manifest, theme-color

Minimal modern set (covers browsers, Google results favicon, iOS, Android, PWA):

| File | Size | Tag |
|---|---|---|
| `/favicon.ico` | 32×32 (can contain 16 & 32) | `<link rel="icon" href="/favicon.ico" sizes="32x32">` — also fetched at root by default |
| `/icon.svg` | vector | `<link rel="icon" href="/icon.svg" type="image/svg+xml">` (can include a `prefers-color-scheme` media query) |
| `/apple-touch-icon.png` | 180×180, opaque background | `<link rel="apple-touch-icon" href="/apple-touch-icon.png">` |
| `/icon-192.png`, `/icon-512.png` | 192, 512 | In manifest; add a `maskable` variant with safe-zone padding |
| `/manifest.webmanifest` | — | `<link rel="manifest" href="/manifest.webmanifest">` |

Google Search favicon: must be a multiple of 48×48 px (48, 96, 144…) or SVG, crawlable, stable URL, on the home page. Verify against current docs: https://developers.google.com/search/docs/appearance/favicon-in-search

```json
{
  "name": "Acme Invoicing",
  "short_name": "Acme",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0f172a",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

`theme-color` supports media queries:

```html
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0b1120" media="(prefers-color-scheme: dark)">
```

Site name in Google results comes from `WebSite` structured data (`name`, `alternateName`) plus `og:site_name` and title — see `structured-data.md`.

---

## 10. Verification tags

Prefer DNS verification (survives redesigns, covers all subdomains/protocols with a Domain property). If HTML tags are used, read the value from env/config and only render when set:

```html
<meta name="google-site-verification" content="...">
<meta name="msvalidate.01" content="...">          <!-- Bing -->
<meta name="yandex-verification" content="...">
<meta name="p:domain_verify" content="...">        <!-- Pinterest -->
<meta name="facebook-domain-verification" content="...">
```

Never commit someone else's token or invent one; leave a placeholder in config and list it in `ULTIMATE-SEO.md`.

---

## 11. Pagination and alternates

- `rel="prev"/"next"` is **not** used by Google for indexing (since 2019) but harmless and used by some other engines/accessibility tools. Don't spend effort on it.
- Paginated pages: self-canonical, unique title (`– Page 3`), crawlable `<a href>` links to other pages. Don't `noindex` page 2+ if it's the only path to deep items.
- `rel="alternate" hreflang` for language/region variants — see `international.md`.
- `rel="alternate" type="application/rss+xml"` for feeds on blogs.
- `rel="alternate" media="only screen and (max-width: 640px)"` only for legacy separate-mobile (m.) sites.

---

## 12. What not to add

| Tag | Why skip |
|---|---|
| `<meta name="keywords">` | Ignored by Google since 2009; Bing treats stuffing as spam signal. |
| `<meta name="revisit-after">` | Never supported. |
| `<meta name="rating">` / `distribution` / `copyright` | No search effect (except `rating: adult` for SafeSearch, which is legitimate for adult sites). |
| `<meta name="robots" content="index, follow">` alone | It's the default; noise. |
| `<meta http-equiv="refresh">` redirects | Use server 301s. |
| `<meta name="author">` as SEO | Fine for humans; authorship signals come from visible bylines + `Article.author` schema. |
| Duplicate tags from framework + plugin | Pick one source. Audit rendered HTML. |
| `noarchive` | Cache feature removed; no effect. |
