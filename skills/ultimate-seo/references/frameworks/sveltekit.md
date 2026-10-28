# SvelteKit

SvelteKit server-renders by default and can prerender any route, so it is SEO-friendly out of the box. The work: a site config module, an `<Seo>` component using `<svelte:head>`, endpoints for `robots.txt`/`sitemap.xml`, prerendering for content routes, and correct 404 handling. Svelte 5 (runes) is current; examples use runes syntax with notes for Svelte 4.

## Contents
- Detect
- Where things go
- Site config
- Seo component
- Page data → metadata
- robots.txt and sitemap.xml endpoints
- OG images
- Prerendering, adapters, errors
- Structured data
- Verify
- Pitfalls

## Detect

- `@sveltejs/kit` in `package.json`; `svelte` version (5 → runes `$props()`; 4 → `export let`).
- `svelte.config.js` → adapter (`adapter-static`, `adapter-vercel`, `adapter-node`, `adapter-cloudflare`, `adapter-netlify`).
- `export const ssr = false` in `src/routes/+layout.(js|ts)` = SPA mode (bad for SEO). `export const prerender = true` = static.
- `trailingSlash` export in root layout.

## Where things go

| Concern | Location |
|---|---|
| Site config | `src/lib/site.ts` + `PUBLIC_SITE_URL` in `.env` (`$env/static/public`) |
| Global head defaults, `lang` | `src/app.html` (`<html lang="en">`, charset, viewport, icons) |
| Per-page tags | `src/lib/components/Seo.svelte` used in each `+page.svelte` |
| Data for metadata | `+page.ts`/`+page.server.ts` `load` |
| robots.txt | `src/routes/robots.txt/+server.ts` (or `static/robots.txt`) |
| sitemap.xml | `src/routes/sitemap.xml/+server.ts` |
| OG image | `static/og-default.png` or `src/routes/og/[slug].png/+server.ts` |
| llms.txt, icons, manifest | `static/` |
| 404 page | `src/routes/+error.svelte` + `error(404)` in loads |

## Site config

```ts
// src/lib/site.ts
import { PUBLIC_SITE_URL } from '$env/static/public'

export const site = {
  url: (PUBLIC_SITE_URL || 'https://www.example.com').replace(/\/$/, ''),
  name: 'Example',
  titleDefault: 'Example — One-line value proposition',
  description: 'Default description, ~150 chars, a reason to click.',
  locale: 'en_US',
  ogImage: '/og-default.png',
  twitter: '@example', // only if real
}
export const absolute = (path: string) => new URL(path, site.url + '/').href
```

`src/app.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" href="%sveltekit.assets%/favicon.ico" sizes="48x48" />
    <link rel="icon" href="%sveltekit.assets%/icon.svg" type="image/svg+xml" />
    <link rel="apple-touch-icon" href="%sveltekit.assets%/apple-touch-icon.png" />
    <link rel="manifest" href="%sveltekit.assets%/site.webmanifest" />
    <meta name="theme-color" content="#0f172a" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

## Seo component

```svelte
<!-- src/lib/components/Seo.svelte -->
<script lang="ts">
  import { page } from '$app/state'; // SvelteKit ≥2.12; older: import { page } from '$app/stores' and use $page
  import { site, absolute } from '$lib/site';

  let {
    title = undefined,
    description = site.description,
    image = site.ogImage,
    imageAlt = site.name,
    type = 'website',
    noindex = false,
    jsonLd = undefined,
  }: {
    title?: string; description?: string; image?: string; imageAlt?: string;
    type?: 'website' | 'article'; noindex?: boolean; jsonLd?: Record<string, unknown> | Record<string, unknown>[];
  } = $props();

  const fullTitle = $derived(title ? `${title} · ${site.name}` : site.titleDefault);
  const canonical = $derived(absolute(page.url.pathname));
  const imageUrl = $derived(absolute(image));
</script>

<svelte:head>
  <title>{fullTitle}</title>
  <meta name="description" content={description} />
  <link rel="canonical" href={canonical} />
  {#if noindex}<meta name="robots" content="noindex, follow" />{/if}
  <meta property="og:type" content={type} />
  <meta property="og:site_name" content={site.name} />
  <meta property="og:locale" content={site.locale} />
  <meta property="og:title" content={title ?? site.titleDefault} />
  <meta property="og:description" content={description} />
  <meta property="og:url" content={canonical} />
  <meta property="og:image" content={imageUrl} />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta property="og:image:alt" content={imageAlt} />
  <meta name="twitter:card" content="summary_large_image" />
  {#if site.twitter}<meta name="twitter:site" content={site.twitter} />{/if}
  {#if jsonLd}
    {@html `<script type="application/ld+json">${JSON.stringify(jsonLd).replace(/</g, '\\u003c')}</script>`}
  {/if}
</svelte:head>
```

The `\u003c` escape prevents a `</script>` inside data from breaking out — always keep it when using `{@html}`. Canonical uses `pathname` only (drops query strings); adjust if query params define distinct indexable content.

## Page data → metadata

```ts
// src/routes/blog/[slug]/+page.server.ts
import { error } from '@sveltejs/kit';
import { getPost } from '$lib/server/posts';

export async function load({ params }) {
  const post = await getPost(params.slug);
  if (!post) error(404, 'Not found'); // SvelteKit 2: no `throw` needed
  return { post };
}
```

```svelte
<!-- src/routes/blog/[slug]/+page.svelte -->
<script lang="ts">
  import Seo from '$lib/components/Seo.svelte';
  import { absolute } from '$lib/site';
  let { data } = $props();
  const p = data.post;
</script>

<Seo
  title={p.title}
  description={p.excerpt}
  image={p.cover}
  type="article"
  jsonLd={{
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: p.title,
    image: absolute(p.cover),
    datePublished: p.publishedAt,
    dateModified: p.updatedAt,
    author: { '@type': 'Person', name: p.author.name, url: p.author.url },
    mainEntityOfPage: absolute(`/blog/${p.slug}`),
  }}
/>

<article><h1>{p.title}</h1>…</article>
```

Alternative pattern: return a `seo` object from `load` and render one `<Seo {...page.data.seo} />` in `+layout.svelte`. Pick one — never both, or tags duplicate.

## robots.txt and sitemap.xml endpoints

```ts
// src/routes/robots.txt/+server.ts
import { site } from '$lib/site';
export const prerender = true;

export function GET() {
  const body = [
    'User-agent: *',
    'Allow: /',
    'Disallow: /admin',
    'Disallow: /api/',
    '',
    `Sitemap: ${site.url}/sitemap.xml`,
  ].join('\n');
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
```

Add the explicit AI-crawler groups from `assets/robots.txt` / `references/ai-search.md`.

```ts
// src/routes/sitemap.xml/+server.ts
import { site } from '$lib/site';
import { getAllPosts } from '$lib/server/posts';
export const prerender = true; // remove if content changes without a rebuild

const xmlEscape = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

export async function GET() {
  const staticPaths = ['/', '/about', '/pricing', '/blog'];
  const posts = await getAllPosts();
  const urls = [
    ...staticPaths.map((p) => ({ loc: site.url + p })),
    ...posts.map((p) => ({ loc: `${site.url}/blog/${p.slug}`, lastmod: p.updatedAt })),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((u) => `  <url><loc>${xmlEscape(u.loc)}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ''}</url>`).join('\n')}
</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
```

Static routes can be discovered with `import.meta.glob('/src/routes/**/+page.svelte')` and filtered (drop `[param]`, `(group)` segments handled, private routes). The `super-sitemap` package does this with param values and is a reasonable dependency for large sites.

## OG images

- Default: `static/og-default.png` (1200×630).
- Dynamic: an endpoint `src/routes/og/[slug].png/+server.ts` using `satori` + `@resvg/resvg-js` (Node adapters) or `@vercel/og`-compatible libraries on edge adapters. Prerender it when the content is static. Pass `image={`/og/${slug}.png`}` to `<Seo>`.

## Prerendering, adapters, errors

- Content/marketing routes: `export const prerender = true` in their `+page.ts` or a group `+layout.ts`. The crawler follows links from `/` and prerenders entries; add unlinked routes via `config.kit.prerender.entries` or an `entries()` export.
- Never `ssr = false` on public routes.
- `+error.svelte` renders on `error(404)` with a real 404 status in SSR. With `adapter-static` + a SPA `fallback` page, unknown URLs on the host may return 200 — configure the host's 404 (`404.html` fallback on Netlify/Vercel/GitHub Pages) so missing pages are real 404s.
- `trailingSlash`: default `'never'`. For `adapter-static` on hosts that serve `/about/index.html`, `'always'` avoids redirects. Keep sitemap/canonicals consistent with the choice.

## Structured data

Home page: `Organization` + `WebSite` (from `assets/jsonld/`); nested pages: `BreadcrumbList` built from `page.url.pathname` segments + titles; per template as in `references/structured-data.md`. Pass via the `jsonLd` prop (accepts an array → render a `@graph` or multiple scripts).

## Verify

```bash
npm run build && npm run preview -- --port 4173 &
python3 <skill-dir>/scripts/seo_audit.py http://localhost:4173 --crawl 50
# adapter-static output:
python3 <skill-dir>/scripts/seo_audit.py build
python3 <skill-dir>/scripts/validate_jsonld.py http://localhost:4173/
curl -s http://localhost:4173/robots.txt; curl -s http://localhost:4173/sitemap.xml | head
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:4173/nope   # expect 404
npx svelte-check
```

## Pitfalls

- Both `static/robots.txt` and `routes/robots.txt/+server.ts` — the static file wins silently. Keep one.
- `<svelte:head>` in both layout and page emitting the same tag → duplicates (title is fine — last wins — but `meta description`/`og:*` duplicate). Defaults in one place only.
- Using `$app/state` on SvelteKit < 2.12 — fall back to `$app/stores`.
- Unescaped JSON-LD via `{@html}` — XSS and broken markup.
- Prerendered sitemap with dynamic CMS content goes stale — rebuild on publish (webhook) or drop `prerender` from the endpoint.
- Links rendered only after client-side fetch in `onMount` — crawlers miss them; load data in `load`.
