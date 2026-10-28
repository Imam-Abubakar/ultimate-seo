# International & Multilingual SEO

Use this when a site serves more than one language or region. The goal: each user (and each search engine market) lands on the right version, and versions don't compete with each other as duplicates.

## Contents

1. Decide: language vs. region targeting
2. URL structure options
3. hreflang fundamentals
4. Implementing hreflang (HTML, HTTP headers, sitemap)
5. Language and region codes
6. Canonical + hreflang interaction
7. Locale detection without hurting crawlers
8. Translated slugs, content and metadata
9. Per-locale sitemaps
10. Common errors and how to detect them
11. Playbook items for ULTIMATE-SEO.md

---

## 1. Decide: language vs. region targeting

Ask two questions before touching code:

- **Does content differ by language only?** (`en`, `fr`, `es`) → target languages. Most SaaS, docs, blogs.
- **Does content differ by country even within one language?** (prices, currency, shipping, legal, spelling, availability: `en-us` vs `en-gb`) → target language-region pairs. Most e-commerce, regulated industries.

Don't create region variants that are identical copies — near-duplicate `en-us`/`en-gb`/`en-au` pages with no real differences add crawl cost and are often folded together by Google anyway. Only split when something meaningful changes (currency, availability, legal text, spelling).

Machine translation is acceptable if reviewed for quality; raw, unreviewed auto-translation at scale can fall under Google's scaled-content-abuse policy. Prefer fewer, high-quality locales over many weak ones.

## 2. URL structure options

| Structure | Example | Pros | Cons | Use when |
|---|---|---|---|---|
| ccTLD | `example.de` | Strongest geo signal, local trust | Separate domains = separate authority, costly, ops overhead | Large brands with local entities/teams per country |
| Subdirectory | `example.com/de/` | Consolidates authority, cheap, simple ops | Weaker geo signal (fine in practice) | **Default for almost everyone** |
| Subdomain | `de.example.com` | Separate hosting/infra possible | Authority partly split, more setup | Infra genuinely differs per locale |
| URL parameter | `example.com?lang=de` | — | Not recommended by Google; easy to break | Never for new builds |
| Cookie/Accept-Language only (same URL) | `example.com` | — | Crawlers see one version only; other locales are invisible | Never |

Rules:
- **Every language/region version needs its own URL.** Content that only changes via cookie or JS is not indexable per locale.
- Pick whether the default locale gets a prefix (`/en/`) or lives at root (`/`). Either works; be consistent and make `x-default` point at the right place.
- Keep the locale segment first: `/de/produkte/...`, not `/produkte/de/...`.
- Google Search Console's International Targeting report was retired; geo-targeting comes from ccTLD, hreflang, local content signals (currency, address, language), and links. Verify against current docs: https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites

## 3. hreflang fundamentals

hreflang tells Google "these URLs are equivalent pages for different languages/regions". It is a *signal*, not a directive, and is used by Google and Yandex (Bing primarily uses `content-language` and other signals, but hreflang doesn't hurt).

The four rules that break most implementations:

1. **Self-reference.** Each page lists itself in its own hreflang set.
2. **Reciprocity (return links).** If A points to B, B must point back to A. Missing return links → Google ignores the pair.
3. **Absolute, canonical URLs only.** Every hreflang URL must be the canonical, indexable, 200-status version (no redirects, no noindex, no parameters unless they're canonical).
4. **x-default.** Add `hreflang="x-default"` for the fallback page (language selector or default locale) for users who match none of the listed locales.

A complete set for one page in three locales:

```html
<link rel="alternate" hreflang="en" href="https://example.com/en/pricing" />
<link rel="alternate" hreflang="de" href="https://example.com/de/preise" />
<link rel="alternate" hreflang="fr" href="https://example.com/fr/tarifs" />
<link rel="alternate" hreflang="x-default" href="https://example.com/en/pricing" />
```

This exact block appears on all three pages.

Only link pages that are true equivalents. If `/de/blog/post-x` doesn't exist, don't point the English post's German hreflang to the German blog home.

## 4. Implementing hreflang

Pick **one** method per URL set; mixing methods invites contradictions.

### HTML `<link>` in `<head>`
Best for most sites. Generate it from a single locale map in code, never by hand. Pseudocode:

```ts
// alternates for the current route, built from one source of truth
const alternates = locales
  .filter((l) => routeExistsIn(route, l))
  .map((l) => ({ hreflang: l.code, href: absoluteUrl(localizedPath(route, l)) }));
alternates.push({ hreflang: 'x-default', href: absoluteUrl(localizedPath(route, defaultLocale)) });
```

Framework specifics: Next.js `metadata.alternates.languages` (App Router) — see `frameworks/nextjs-app-router.md`; Nuxt `@nuxtjs/i18n` `useLocaleHead()`; Astro i18n routing + manual `<link>`s; SvelteKit/Remix generate in the layout.

### HTTP `Link` header
For non-HTML files (PDFs) or when you can't edit the head:

```
Link: <https://example.com/en/guide.pdf>; rel="alternate"; hreflang="en",
      <https://example.com/de/guide.pdf>; rel="alternate"; hreflang="de"
```

### XML sitemap
Best for very large sites (keeps HTML lean) or when templates are hard to change. Each `<url>` lists all alternates including itself:

```xml
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>https://example.com/en/pricing</loc>
    <xhtml:link rel="alternate" hreflang="en" href="https://example.com/en/pricing"/>
    <xhtml:link rel="alternate" hreflang="de" href="https://example.com/de/preise"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://example.com/en/pricing"/>
  </url>
  <url>
    <loc>https://example.com/de/preise</loc>
    <xhtml:link rel="alternate" hreflang="en" href="https://example.com/en/pricing"/>
    <xhtml:link rel="alternate" hreflang="de" href="https://example.com/de/preise"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="https://example.com/en/pricing"/>
  </url>
</urlset>
```

Reference: https://developers.google.com/search/docs/specialty/international/localized-versions (verify against current docs).

## 5. Language and region codes

- Language: **ISO 639-1** two-letter code (`en`, `de`, `pt`, `zh`).
- Optional region: **ISO 3166-1 Alpha-2** (`en-GB`, `pt-BR`, `es-MX`). Case-insensitive, but be consistent.
- Region alone is invalid: `hreflang="uk"` means Ukrainian language, not United Kingdom. UK English is `en-GB`.
- `en-UK` is invalid (use `en-GB`). `es-LA` / `es-419` (Latin America) is not supported by Google — list countries individually or use plain `es`.
- Scripts: use `zh-Hans` / `zh-Hant` (or `zh-CN` / `zh-TW`) — pick one scheme and be consistent.
- If you serve `en-US` and `en-GB`, also consider a plain `en` (or `x-default`) to catch `en-IN`, `en-AU`, etc.
- Mirror the locale in `<html lang="de-DE">` and `og:locale="de_DE"` (OG uses underscore) and `og:locale:alternate` for the others.

## 6. Canonical + hreflang interaction

- Each locale page's canonical points to **itself**, never to the default-language version. Canonicalizing `/de/preise` to `/en/pricing` tells Google the German page is a duplicate and it will drop out of German results.
- hreflang targets must be the canonical URLs. A hreflang pointing at a URL whose canonical is elsewhere is ignored.
- Paginated or filtered variants: hreflang between equivalent page 2s is fine; don't point page 2 in one locale to page 1 in another.
- For region variants that are near-identical (e.g. `en-US` vs `en-CA` with only currency changed), self-canonical + hreflang is correct; Google may still fold them, which is acceptable.

## 7. Locale detection without hurting crawlers

Googlebot crawls mostly from US IPs, usually without an `Accept-Language` header. If you force-redirect based on IP or language, Googlebot may only ever see one locale.

Do:
- Serve every locale at its own URL with a **200** to any client, including bots.
- Use detection only to **suggest** (a dismissible banner: "View this page in Deutsch?") or to redirect the *root* `/` once for first-time human visitors, with the choice stored in a cookie.
- If you redirect `/` by language, use a 302 and keep `x-default` pointing at `/` (or a language-picker page) so crawlers have a stable entry.
- Always provide a visible language switcher with real `<a href>` links to the equivalent page in each locale (crawlable, and helps users).

Don't:
- Auto-redirect deep URLs (`/en/pricing` → `/de/preise`) based on IP/Accept-Language.
- Hide locales behind JS-only toggles or forms.
- Return different content at the same URL depending on IP (that's effectively cloaking toward Googlebot's US IPs).

## 8. Translated slugs, content and metadata

- **Translate slugs** for real localization (`/de/preise`, not `/de/pricing`) when you have the tooling to map equivalents; it helps CTR and relevance. Keep a route map (`pricing` ↔ `preise` ↔ `tarifs`) as the single source of truth used by the switcher, hreflang, and sitemap.
- Use UTF-8 slugs carefully: non-ASCII slugs work but appear percent-encoded when shared; transliteration is a valid choice. Be consistent.
- Localize everything on the page: title, meta description, headings, alt text, OG image text, structured data (`inLanguage`, prices/currency in `Offer`), dates and number formats, units.
- Localize keyword research — direct translation of keywords misses how people actually search (e.g. "mobile phone" vs "cell phone" vs "Handy").
- Avoid mixing languages on one page (navigation in English, body in German) — confuses language detection.
- Don't translate brand names or product names that users search in their original form.

## 9. Per-locale sitemaps

- Use a sitemap index referencing one sitemap per locale (`/sitemap-en.xml`, `/sitemap-de.xml`), or one sitemap with `xhtml:link` alternates (section 4).
- List only canonical, indexable, 200 URLs for each locale.
- Reference the index from `robots.txt` (absolute URL). Submit it in Search Console; for ccTLDs/subdomains, each property needs its own submission.

## 10. Common errors and how to detect them

| Error | Symptom | Fix |
|---|---|---|
| Missing return links | GSC/third-party tools report "no return tags"; wrong locale ranks | Generate hreflang from one shared map so every page emits the full set |
| hreflang to redirected/404/noindex URLs | Pairs ignored | Point only at canonical 200 URLs; regenerate after slug changes |
| Relative URLs in hreflang | Ignored | Always absolute with protocol + host |
| Invalid codes (`en-UK`, `uk` for UK, `es-LA`) | Ignored silently | Validate against ISO lists |
| Canonical to default language | Locales vanish from index | Self-referencing canonicals |
| IP-based forced redirects | Only one locale indexed | Banner/suggestion instead |
| hreflang in `<body>` or after invalid head elements | Ignored | Keep in `<head>`; invalid elements (e.g. `<img>`, `<iframe>`) in `<head>` close it early |
| Mixed methods (HTML + sitemap disagree) | Conflicting signals | One method per URL set |
| Untranslated duplicates labeled as other languages | Thin/duplicate content | Only launch locales with real translations |

Detection: `seo_audit.py` with `--crawl` reports hreflang reciprocity and invalid codes across crawled pages; Screaming Frog / Sitebulb have hreflang reports; Search Console shows indexed pages per locale (filter by URL prefix).

## 11. Playbook items for ULTIMATE-SEO.md

Tailor these for the project:

- [ ] Confirm the locale list and default locale; document the route map file path.
- [ ] Every locale page: self-canonical, full hreflang set incl. `x-default`, `<html lang>`, `og:locale` + alternates.
- [ ] Language switcher uses real links to equivalent pages.
- [ ] No IP/Accept-Language forced redirects on deep URLs.
- [ ] Per-locale sitemap(s) submitted in Search Console (one property per ccTLD/subdomain).
- [ ] Localized keyword research for the top 10 pages per locale before translating.
- [ ] Native-speaker review of machine translations for top pages.
- [ ] Localized structured data (currency, `inLanguage`, local address/phone where relevant).
- [ ] Monitor: GSC Performance filtered by country and by URL prefix; check impressions per locale monthly.
- [ ] Earn local links per market (local press, partners, directories in that language).
