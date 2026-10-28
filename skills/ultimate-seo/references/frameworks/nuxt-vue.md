# Nuxt (3/4) and Vue

Nuxt renders on the server (or prerenders) by default, so crawlers get full HTML. The work is mostly: one site config, `useSeoMeta` per page, and the `@nuxtjs/seo` module family for sitemap/robots/OG images/schema. A plain Vue SPA (Vite + `vue-router`, no Nuxt) is a client-rendered SPA — follow `react-spa.md` (the prerendering advice applies equally; `vite-ssg` is the Vue equivalent of prerendering) and use `@unhead/vue` for head tags.

## Contents
- Detect
- Where things go
- Site config
- Global head
- Per-page metadata
- Sitemap, robots, OG images, schema (`@nuxtjs/seo`)
- Without the module (hand-rolled)
- Rendering and prerendering
- Structured data
- Plain Vue SPA
- Verify
- Pitfalls

## Detect

- `nuxt` in `package.json` dependencies. `nuxt@^3` vs `nuxt@^4` — v4 defaults to the `app/` source directory (`app/pages`, `app/app.vue`); v3 uses root `pages/`. Check which exists.
- Rendering: `ssr: false` in `nuxt.config.ts` means SPA mode (bad for SEO — fix it or prerender). `nuxi generate` / `nitro.prerender` / `routeRules: { '/**': { prerender: true } }` means static.
- Existing modules: look for `@nuxtjs/seo`, `@nuxtjs/sitemap`, `@nuxtjs/robots`, `nuxt-og-image`, `nuxt-schema-org`, `nuxt-site-config`, `@nuxt/content` in `modules`.
- Plain Vue: `vue` + `vite` + `vue-router` without `nuxt` → SPA.

## Where things go

| Concern | Nuxt location |
|---|---|
| Site config (url, name, locale) | `nuxt.config.ts` → `site: {}` (from `nuxt-site-config`, bundled in `@nuxtjs/seo`) + `NUXT_PUBLIC_SITE_URL` env |
| Global defaults (lang, title template) | `app.vue` via `useHead` / `useSeoMeta`, or `nuxt.config.ts` → `app.head` |
| Per-page title/description/OG | `useSeoMeta()` in each `pages/**.vue` |
| Canonical | `useHead({ link: [{ rel: 'canonical', href }] })` or automatic via `@nuxtjs/seo` |
| robots.txt | `@nuxtjs/robots` (generated) or `public/robots.txt` |
| sitemap.xml | `@nuxtjs/sitemap` or `server/routes/sitemap.xml.ts` |
| OG images | `nuxt-og-image` (`defineOgImageComponent`) or static `public/og-default.png` |
| JSON-LD | `nuxt-schema-org` (`useSchemaOrg`) or `useHead({ script: [{ type: 'application/ld+json', ... }] })` |
| Icons/manifest | `public/` + `app.head.link` |
| llms.txt | `public/llms.txt` |
| 404 | `error.vue` + `throw createError({ statusCode: 404, fatal: true })` |

## Site config

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/seo'],
  site: {
    url: 'https://www.example.com', // overridden by NUXT_PUBLIC_SITE_URL / NUXT_SITE_URL
    name: 'Example',
    description: 'One-line value proposition, ~150 chars.',
    defaultLocale: 'en',
    indexable: true, // auto-false on non-production envs when using the module's env detection
  },
  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      charset: 'utf-8',
      viewport: 'width=device-width, initial-scale=1',
      link: [
        { rel: 'icon', href: '/favicon.ico', sizes: '48x48' },
        { rel: 'icon', href: '/icon.svg', type: 'image/svg+xml' },
        { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' },
        { rel: 'manifest', href: '/site.webmanifest' },
      ],
      meta: [{ name: 'theme-color', content: '#0f172a' }],
    },
  },
})
```

`@nuxtjs/seo` reads `site.url` everywhere (canonicals, sitemap, robots, OG image URLs, schema). Set `NUXT_PUBLIC_SITE_URL` in production env. Install with `npx nuxi module add @nuxtjs/seo`.

## Global head

```vue
<!-- app.vue (app/app.vue in Nuxt 4) -->
<script setup lang="ts">
useHead({
  titleTemplate: (title) => (title ? `${title} · Example` : 'Example — One-line value proposition'),
})
useSeoMeta({
  ogSiteName: 'Example',
  ogType: 'website',
  twitterCard: 'summary_large_image',
  twitterSite: '@example', // only if it exists
})
</script>

<template>
  <NuxtLayout><NuxtPage /></NuxtLayout>
</template>
```

With `@nuxtjs/seo`, the title template and `og:site_name` can come from `site.name` automatically (its `seo` module sets sensible defaults); don't duplicate if they're already emitted — check rendered HTML.

## Per-page metadata

```vue
<!-- pages/blog/[slug].vue -->
<script setup lang="ts">
const route = useRoute()
const { data: post } = await useFetch(`/api/posts/${route.params.slug}`)
if (!post.value) throw createError({ statusCode: 404, statusMessage: 'Post not found', fatal: true })

useSeoMeta({
  title: post.value.title,
  description: post.value.excerpt,
  ogTitle: post.value.title,
  ogDescription: post.value.excerpt,
  ogType: 'article',
  articlePublishedTime: post.value.publishedAt,
  articleModifiedTime: post.value.updatedAt,
})
// Without @nuxtjs/seo, add the canonical yourself:
// const siteUrl = useRuntimeConfig().public.siteUrl
// useHead({ link: [{ rel: 'canonical', href: new URL(route.path, siteUrl).href }] })
</script>
```

- `useSeoMeta` is typed (catches typos like `ogImageAlt`); prefer it over raw `meta` arrays.
- Always fetch with `useFetch`/`useAsyncData` (server-side) so metadata is in the SSR HTML, not set after hydration.
- `@nuxt/content`: page frontmatter `title`/`description` can be passed straight to `useSeoMeta`; `useContentHead` exists in older Content versions — check the installed major.

## Sitemap, robots, OG images, schema (`@nuxtjs/seo`)

`@nuxtjs/seo` bundles: `@nuxtjs/sitemap`, `@nuxtjs/robots`, `nuxt-og-image`, `nuxt-schema-org`, `nuxt-link-checker`, `nuxt-seo-utils`, `nuxt-site-config`. Use individual modules if the user wants a lighter footprint.

**Sitemap** — static routes are discovered automatically. Dynamic routes need a source:

```ts
// nuxt.config.ts
sitemap: {
  sources: ['/api/__sitemap__/urls'],
  exclude: ['/admin/**', '/account/**', '/search'],
},
```

```ts
// server/api/__sitemap__/urls.ts
import { defineSitemapEventHandler } from '#imports'
export default defineSitemapEventHandler(async () => {
  const posts = await $fetch<{ slug: string; updatedAt: string }[]>('/api/posts')
  return posts.map((p) => ({ loc: `/blog/${p.slug}`, lastmod: p.updatedAt }))
})
```

**Robots** — module generates `/robots.txt`, auto-disallows on non-production, and adds the sitemap line. Configure:

```ts
robots: {
  disallow: ['/admin', '/api', '/account', '/search'],
  groups: [
    // explicit AI policy — see references/ai-search.md
    { userAgent: ['GPTBot', 'ClaudeBot', 'Google-Extended', 'CCBot'], allow: ['/'] },
  ],
},
```

Per-page noindex: `defineRouteRules({ robots: false })` in a page, or `routeRules: { '/thank-you': { robots: false } }`. Delete any hand-written `public/robots.txt` — it conflicts.

**OG images** — `nuxt-og-image` renders Vue components to PNG with Satori:

```vue
<script setup lang="ts">
defineOgImageComponent('NuxtSeo', { title: post.value.title, description: post.value.excerpt })
</script>
```

Custom templates live in `components/OgImage/*.vue`. For fully static hosting, OG images are prerendered at `nuxi generate`. If the module is too heavy, ship `public/og-default.png` (1200×630) and set `ogImage` with absolute URL + `ogImageWidth/Height/Alt`.

## Without the module (hand-rolled)

```ts
// server/routes/sitemap.xml.ts
export default defineEventHandler(async (event) => {
  const site = useRuntimeConfig().public.siteUrl
  const posts = await $fetch<{ slug: string; updatedAt: string }[]>('/api/posts')
  const urls = [
    { loc: '/' },
    ...posts.map((p) => ({ loc: `/blog/${p.slug}`, lastmod: p.updatedAt })),
  ]
  setHeader(event, 'content-type', 'application/xml; charset=utf-8')
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((u) => `  <url><loc>${new URL(u.loc, site).href}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ''}</url>`).join('\n')}
</urlset>`
})
```

`server/routes/robots.txt.ts` similarly returns text with `Sitemap: ${site}/sitemap.xml`. Add `runtimeConfig: { public: { siteUrl: '' } }` and set `NUXT_PUBLIC_SITE_URL`. For `nuxi generate`, add both to `nitro.prerender.routes`.

## Rendering and prerendering

```ts
routeRules: {
  '/': { prerender: true },
  '/blog/**': { isr: 3600 },   // or swr on non-Vercel/Netlify
  '/admin/**': { ssr: false, robots: false },
},
```

- Never `ssr: false` globally on a public site. Client-only sections: wrap in `<ClientOnly>` but keep content and links server-rendered.
- 404s: `createError({ statusCode: 404, fatal: true })` sets a real 404 status during SSR. Check catch-all `[...slug].vue` pages — they're the common source of soft 404s.
- Trailing slashes: pick one; with the module set `site.trailingSlash` and keep `<NuxtLink>` consistent.

## Structured data

With `nuxt-schema-org` (in `@nuxtjs/seo`), define the identity once and add page nodes:

```ts
// nuxt.config.ts
schemaOrg: {
  identity: {
    type: 'Organization',
    name: 'Example',
    logo: '/logo.png',
    sameAs: ['https://github.com/example'], // only real profiles
  },
},
```

```vue
<script setup lang="ts">
useSchemaOrg([
  defineArticle({
    headline: post.value.title,
    image: post.value.cover,
    datePublished: post.value.publishedAt,
    dateModified: post.value.updatedAt,
    author: { name: post.value.author.name, url: post.value.author.url },
  }),
])
</script>
```

The module emits a linked `@graph` with `WebSite`, `WebPage`, and breadcrumbs automatically. Without it:

```ts
useHead({
  script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(jsonLd) }],
})
```

(Older Unhead used `children`; `innerHTML` is current. Check the rendered output.)

## Plain Vue SPA

- Use `@unhead/vue` (`createHead()` + `useSeoMeta`) for per-route tags.
- Social scrapers and most AI crawlers don't run JS: prerender public routes with `vite-ssg` or move to Nuxt. See `react-spa.md` for the full SPA strategy, hosting rewrites, and soft-404 handling.
- Static `public/robots.txt`, a generated sitemap (`vite-plugin-sitemap` or `scripts/generate_sitemap.py` on the prerendered `dist/`).

## Verify

```bash
npx nuxi build && node .output/server/index.mjs &   # or: npx nuxi generate && npx serve .output/public
python3 <skill-dir>/scripts/seo_audit.py http://localhost:3000 --crawl 50
python3 <skill-dir>/scripts/validate_jsonld.py http://localhost:3000/
curl -s http://localhost:3000/robots.txt; curl -s http://localhost:3000/sitemap.xml | head -20
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/definitely-not-a-page   # expect 404
```

The `@nuxtjs/seo` devtools tab also shows per-page meta, OG preview, and schema.

## Pitfalls

- Hand-written `public/robots.txt` or `public/sitemap.xml` shadowing the module's generated ones.
- `site.url` unset → module falls back to localhost or relative URLs in canonicals/OG. Verify absolute production URLs in the built HTML.
- Metadata set inside `onMounted` or after a client-side fetch — invisible to crawlers.
- `useSeoMeta` called with refs that are undefined during SSR (fetch not awaited).
- Duplicate `og:*` tags from both `app.head` and the module — inspect rendered HTML, keep one source.
- i18n (`@nuxtjs/i18n`): use its `useLocaleHead()` for hreflang/canonical; see `references/international.md`.
