# Client-rendered SPAs (React/Vite, CRA, Vue, Svelte, Solid)

A client-only SPA ships one `index.html` with an empty `<div id="root">` and builds the page in JavaScript. Googlebot renders JS (with delay and a render budget), but **social scrapers (Facebook, LinkedIn, X, Slack, Discord, iMessage), Bing at scale, and most AI crawlers (GPTBot, ClaudeBot, PerplexityBot) do not execute JavaScript**. They see a blank page with whatever is hard-coded in `index.html`. So for SPAs the single biggest SEO lever is getting real HTML for public routes. Metadata libraries alone don't fix this.

## Contents

1. Detect
2. Decide the rendering strategy
3. Where things go
4. Site config
5. Metadata (React 19 native, react-helmet-async)
6. Prerendering options
7. robots.txt, sitemap, llms.txt
8. 404s and the SPA fallback problem
9. Social previews without prerendering (edge injection)
10. Structured data
11. Performance
12. Vue, Svelte and Solid SPAs
13. Verify
14. Pitfalls

## 1. Detect

- `vite.config.*` with `@vitejs/plugin-react` and `index.html` containing `<div id="root">` → Vite React SPA. `react-scripts` → CRA (deprecated since 2025; recommend Vite migration in the playbook).
- Router: `react-router-dom`/`react-router` (library mode: `createBrowserRouter`/`<BrowserRouter>`), `@tanstack/react-router`, `wouter`. If `react-router.config.ts` exists, it's framework mode — use `react-router-remix.md` instead.
- React version decides metadata approach: **19+** supports `<title>`, `<meta>`, `<link>` anywhere in the tree (hoisted to `<head>`). **≤18** needs `react-helmet-async`.
- Hash routing (`/#/about`) → search engines treat it as one URL. Switch to history routing for any public site.

## 2. Decide the rendering strategy

Pick the highest option the project can absorb; write the rest into `ULTIMATE-SEO.md`.

| Option | When | Effort |
|---|---|---|
| **A. Build-time prerender (SSG)** of public routes | Marketing pages, blogs, docs, product pages known at build | Low–medium |
| **B. Move to a framework** (React Router v7 framework mode, Next.js, Astro for content, TanStack Start) | Large dynamic catalogs, user-generated pages | High — recommend, don't do unasked |
| **C. Edge meta injection** | Dynamic routes, can't prerender; mainly fixes social cards | Medium |
| **D. Strong `index.html` defaults only** | App behind login (dashboard) where only the landing page matters | Minimal — always do this anyway |

Apps whose public surface is a single landing page: do D plus prerender the landing page; noindex the app routes.

## 3. Where things go

| Concern | File |
|---|---|
| Site config | `src/config/site.ts` |
| Fallback metadata for every route | `index.html` `<head>` |
| Per-route metadata | `src/components/Seo.tsx` used in route components |
| robots.txt / llms.txt / icons / manifest | `public/` |
| sitemap.xml | generated at build: `scripts/generate-sitemap.mjs` (or `vite-plugin-sitemap`) |
| 404 | `NotFound` route component + host config (`404.html`, `_redirects`, `vercel.json`) |

## 4. Site config

```ts
// src/config/site.ts
export const siteConfig = {
  name: "Acme",
  url: (import.meta.env.VITE_SITE_URL ?? "https://www.example.com").replace(/\/$/, ""),
  description: "Acme helps small teams ship invoices in minutes.",
  locale: "en_US",
  ogImage: "/og.png",
  twitter: "@acme",
};
export const absoluteUrl = (path = "/") => new URL(path, siteConfig.url).toString();
```

Mirror the defaults in `index.html` (Vite replaces `%VITE_SITE_URL%` placeholders in `index.html` at build time):

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Acme — Invoicing for small teams</title>
    <meta name="description" content="Acme helps small teams ship invoices in minutes." />
    <link rel="canonical" href="%VITE_SITE_URL%/" />
    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="Acme" />
    <meta property="og:title" content="Acme — Invoicing for small teams" />
    <meta property="og:description" content="Acme helps small teams ship invoices in minutes." />
    <meta property="og:url" content="%VITE_SITE_URL%/" />
    <meta property="og:image" content="%VITE_SITE_URL%/og.png" />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="icon" href="/favicon.ico" sizes="any" />
    <link rel="icon" href="/icon.svg" type="image/svg+xml" />
    <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
    <link rel="manifest" href="/manifest.webmanifest" />
    <meta name="theme-color" content="#0a0a0a" />
  </head>
  <body>
    <div id="root"></div>
    <noscript>Acme helps small teams ship invoices in minutes. <a href="/pricing">Pricing</a></noscript>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Caveat: the hard-coded canonical points every unprerendered route at `/` until JS replaces it. Once per-route metadata exists, the route's `<link rel="canonical">` must replace it (React 19 dedupes nothing — remove the one from `index.html` if routes render their own, or prerender so each HTML file has its own).

## 5. Metadata

**React 19+ (no library):**

```tsx
// src/components/Seo.tsx
import { siteConfig, absoluteUrl } from "@/config/site";

type Props = { title?: string; description?: string; path: string; image?: string; noindex?: boolean; type?: "website" | "article" };

export function Seo({ title, description = siteConfig.description, path, image = siteConfig.ogImage, noindex, type = "website" }: Props) {
  const fullTitle = title ? `${title} | ${siteConfig.name}` : siteConfig.name;
  const url = absoluteUrl(path);
  return (
    <>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={url} />
      {noindex && <meta name="robots" content="noindex, follow" />}
      <meta property="og:type" content={type} />
      <meta property="og:title" content={title ?? siteConfig.name} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content={absoluteUrl(image)} />
      <meta name="twitter:card" content="summary_large_image" />
    </>
  );
}
```

React 19 hoists these into `<head>` but does **not** dedupe `<meta>`; tags from `index.html` stay. Remove the per-route duplicates from `index.html` (keep only charset, viewport, icons, manifest, theme-color) once every route renders `<Seo>`, or the head will contain two descriptions.

**React ≤18:** `react-helmet-async` — wrap the app in `<HelmetProvider>`, render `<Helmet>` with the same tags. Helmet replaces tags it manages (use `data-rh` or keep `index.html` tags minimal). Unmaintained `react-helmet` (non-async) should be replaced.

## 6. Prerendering options

**React Router v7 (recommended path for RR users):** adopting framework mode gives `prerender` in `react-router.config.ts` with `ssr: false` — static HTML per route, no server needed. See `react-router-remix.md`. It's a real migration (route modules, `meta` exports); budget it.

**`vite-react-ssg`** (React Router data routes, minimal change):

```tsx
// src/main.tsx
import { ViteReactSSG } from "vite-react-ssg";
import { routes } from "./routes"; // RouteRecord[] (createBrowserRouter-style objects)
export const createRoot = ViteReactSSG({ routes });
```

```json
// package.json scripts
"build": "vite-react-ssg build"
```

Dynamic routes list their paths via `getStaticPaths` on the route record. Use its `<Head>` component (or React 19 tags) for metadata. Code that touches `window`/`document` at module scope must be guarded — SSG runs in Node.

**TanStack Router:** use TanStack Start's static prerendering, or move to it.

**Generic headless prerender** (`@prerenderer/rollup-plugin`/Puppeteer-based) works with any SPA but is slower and flakier; prefer the options above.

**SaaS prerender services** (Prerender.io etc., serving cached HTML to bot user-agents): acceptable as a stopgap (Google calls this dynamic rendering a workaround, not a recommendation). Content must match what users see.

## 7. robots.txt, sitemap, llms.txt

Put `robots.txt` and `llms.txt` in `public/` (templates in `assets/`). Generate the sitemap at build from the route list and data:

```js
// scripts/generate-sitemap.mjs  — run after vite build: "build": "vite build && node scripts/generate-sitemap.mjs"
import { writeFileSync } from "node:fs";
const SITE = (process.env.VITE_SITE_URL || "https://www.example.com").replace(/\/$/, "");
const routes = ["/", "/pricing", "/about", "/blog"]; // import from your routes/data if possible
// const posts = JSON.parse(readFileSync("src/content/posts.json", "utf8")); routes.push(...posts.map(p => `/blog/${p.slug}`));
const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${routes.map((r) => `  <url><loc>${SITE}${r}</loc></url>`).join("\n")}
</urlset>\n`;
writeFileSync("dist/sitemap.xml", xml);
```

Or run the skill's `generate_sitemap.py dist --base-url $VITE_SITE_URL` after prerendering, which reads the actual HTML files.

## 8. 404s and the SPA fallback problem

SPA hosting rewrites every path to `index.html` with **status 200**, so `/anything-at-all` is a soft 404 and duplicates the home page. Mitigate:

- Prerender, and configure the host to serve real files and a `404.html` with status 404 for unknown paths (Netlify/Cloudflare Pages/GitHub Pages do this automatically for `404.html` if no catch-all rewrite exists; on Vercel, avoid a blanket `rewrites` to `/index.html` once routes are prerendered).
- If a catch-all rewrite must stay, the `NotFound` route renders `<meta name="robots" content="noindex" />` so Google drops it.
- Never redirect unknown routes to `/`.

## 9. Social previews without prerendering

When dynamic routes can't be prerendered, inject route-specific `<title>`/OG tags at the edge before serving `index.html`: Cloudflare Workers/Pages Functions with `HTMLRewriter`, Netlify Edge Functions, Vercel Edge Middleware/Functions. Look up the entity by path, rewrite the head tags, return the same HTML to everyone (no user-agent cloaking). This fixes share cards and gives every crawler correct metadata even though the body is still client-rendered.

## 10. Structured data

```tsx
export function JsonLd({ data }: { data: object }) {
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }} />;
}
```

In a client-only SPA, Google can read JSON-LD injected by JS, but other consumers can't. Put site-wide `Organization` + `WebSite` JSON-LD statically in `index.html` (or the prerendered home page). Templates: `assets/jsonld/`.

## 11. Performance

SPAs usually struggle with LCP (JS must load before content) and INP (big bundles):
- Route-level code splitting (`React.lazy`, router `lazy`).
- Preload the LCP image in `index.html` (`<link rel="preload" as="image" href="/hero.webp" fetchpriority="high">`) and give it `width`/`height`.
- Self-host fonts with `font-display: swap`; preload the main weight.
- Load analytics/chat with `defer`/after `load`.
- Check bundle size: `npx vite-bundle-visualizer`.

## 12. Vue, Svelte and Solid SPAs

- **Vue (Vite, no Nuxt):** `@unhead/vue` → `useHead`/`useSeoMeta` in components; prerender with `vite-ssg`. For anything content-heavy, recommend Nuxt (`nuxt-vue.md`).
- **Svelte (Vite, no SvelteKit):** `<svelte:head>` for tags; for prerendering, migrate to SvelteKit with `adapter-static` (`sveltekit.md`) — it's the supported path.
- **Solid:** `@solidjs/meta` (`<Title>`, `<Meta>`, `<Link>` inside `<MetaProvider>`); prerender with SolidStart.
- The same `index.html` defaults, robots/sitemap/404 guidance above apply to all of them.

## 13. Verify

```bash
npm run build && npx vite preview --port 4173 &
# Raw HTML is what scrapers see — this is the important check for SPAs:
curl -s http://localhost:4173/pricing | grep -iE "<title>|og:title|canonical|<h1"
python3 <skill-dir>/scripts/seo_audit.py dist                 # prerendered files
python3 <skill-dir>/scripts/seo_audit.py http://localhost:4173 --crawl 30
python3 <skill-dir>/scripts/validate_jsonld.py dist
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:4173/nope   # vite preview returns 200 (SPA fallback) — check host config separately
```

The audit's "client-rendered shell" warning is expected before prerendering; it should disappear for prerendered routes.

## 14. Pitfalls

- Treating `react-helmet` as "SEO done" — the HTML is still empty for non-JS crawlers.
- Duplicate `<meta name="description">` from `index.html` + React 19 tags.
- Links built with `onClick={() => navigate(...)}` on `<div>`s — crawlers only follow `<a href>`. Use `<Link>`.
- Content fetched after mount with no loading skeleton dimensions → CLS.
- `VITE_SITE_URL` unset in CI → canonicals and sitemap point at the fallback/localhost.
