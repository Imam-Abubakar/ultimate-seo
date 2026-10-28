# React Router v7 (framework mode) and Remix v2

Remix v2 merged into React Router v7 "framework mode": route modules with `loader`, `meta`, `links`, server rendering by default, optional build-time prerendering. Both render real HTML, so the job is mostly correct `meta` exports, resource routes for `sitemap.xml`/`robots.txt`, and real 404 status codes.

## Contents

1. Detect
2. Where things go
3. Site config
4. Root document
5. The `meta` export (and its merge trap)
6. Dynamic routes, loaders, 404s
7. sitemap.xml and robots.txt resource routes
8. Prerendering (SSG / SPA mode)
9. Open Graph images
10. Structured data
11. Performance
12. Verify
13. Pitfalls

## 1. Detect

- **RR7 framework mode:** `react-router.config.ts`, `app/routes.ts`, `app/root.tsx`, `@react-router/dev` in devDependencies, scripts `react-router dev/build`. Types via `./+types/<route>` imports.
- **Remix v2:** `@remix-run/*` packages, `remix vite:build`, `vite.config` with `vitePlugin as remix`. Same concepts; imports come from `@remix-run/react` / `@remix-run/node`. Recommend the (largely codemod-able) RR7 upgrade in the playbook, not as part of SEO work.
- Rendering: `ssr: true` (default) → SSR. `ssr: false` → SPA mode; with `prerender` → static HTML per listed route.
- React Router **library mode** (`createBrowserRouter` in a Vite SPA) → use `react-spa.md`.

## 2. Where things go

| Concern | File |
|---|---|
| Site config | `app/lib/site.ts` |
| `<html lang>`, `<Meta />`, `<Links />` | `app/root.tsx` `Layout` |
| Per-route metadata | `meta` export in each route module |
| sitemap.xml | `app/routes/sitemap[.]xml.ts` (flat routes) or `route("sitemap.xml", "routes/sitemap.ts")` in `app/routes.ts` |
| robots.txt | `public/robots.txt` or resource route `robots[.]txt.ts` |
| llms.txt, icons, manifest | `public/` |
| 404 | throw 404 from loaders + `ErrorBoundary` / catch-all `*` route |
| Redirects | `redirect("/new", 301)` in loaders or at the host |

## 3. Site config

```ts
// app/lib/site.ts
export const siteConfig = {
  name: "Acme",
  url: (process.env.SITE_URL ?? "http://localhost:5173").replace(/\/$/, ""),
  description: "Acme helps small teams ship invoices in minutes.",
  locale: "en_US",
  ogImage: "/og.png",
  twitter: "@acme",
};
export const absoluteUrl = (path = "/") => new URL(path, siteConfig.url).toString();
```

`process.env` is server-only; `meta` runs on server and client. Return `siteUrl` from the root loader (or a route loader) and read it in `meta` via `matches`, or inline the origin at build with Vite `define`. Simplest robust option: compute absolute URLs in the loader and pass them as data.

## 4. Root document

```tsx
// app/root.tsx
import { Links, Meta, Outlet, Scripts, ScrollRestoration } from "react-router";
import type { Route } from "./+types/root";

export const links: Route.LinksFunction = () => [
  { rel: "icon", href: "/favicon.ico", sizes: "any" },
  { rel: "icon", href: "/icon.svg", type: "image/svg+xml" },
  { rel: "apple-touch-icon", href: "/apple-touch-icon.png" },
  { rel: "manifest", href: "/manifest.webmanifest" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0a0a0a" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() { return <Outlet />; }
```

## 5. The `meta` export

```ts
// app/lib/seo.ts
import { siteConfig } from "./site";

export function seo({ title, description = siteConfig.description, url, image = `${siteConfig.url}${siteConfig.ogImage}`, type = "website", noindex = false }: {
  title?: string; description?: string; url: string; image?: string; type?: string; noindex?: boolean;
}) {
  const fullTitle = title ? `${title} | ${siteConfig.name}` : siteConfig.name;
  return [
    { title: fullTitle },
    { name: "description", content: description },
    { tagName: "link", rel: "canonical", href: url },
    ...(noindex ? [{ name: "robots", content: "noindex, follow" }] : []),
    { property: "og:type", content: type },
    { property: "og:site_name", content: siteConfig.name },
    { property: "og:title", content: title ?? siteConfig.name },
    { property: "og:description", content: description },
    { property: "og:url", content: url },
    { property: "og:image", content: image },
    { property: "og:image:width", content: "1200" },
    { property: "og:image:height", content: "630" },
    { name: "twitter:card", content: "summary_large_image" },
  ];
}
```

```ts
// app/routes/pricing.tsx
import type { Route } from "./+types/pricing";
import { seo } from "~/lib/seo";
import { absoluteUrl } from "~/lib/site";

export const meta: Route.MetaFunction = () =>
  seo({ title: "Pricing", description: "Simple plans from $0 ...", url: absoluteUrl("/pricing") });
```

**Merge trap:** the deepest matching route's `meta` *replaces* all parent meta — nothing is inherited. That's why `seo()` always emits the full set. To include parent values, read `matches` (`matches.flatMap(m => m.meta ?? [])`) and filter duplicates — but the helper approach is simpler.

**Alternative (React 19):** render `<title>`/`<meta>`/`<link>` directly in route components; React hoists them. Don't mix both approaches on the same route or you'll get duplicates.

## 6. Dynamic routes, loaders, 404s

```tsx
// app/routes/blog.$slug.tsx
import { data } from "react-router";
import type { Route } from "./+types/blog.$slug";
import { getPost } from "~/lib/posts.server";
import { seo } from "~/lib/seo";
import { absoluteUrl, siteConfig } from "~/lib/site";

export async function loader({ params }: Route.LoaderArgs) {
  const post = await getPost(params.slug);
  if (!post) throw data(null, { status: 404 }); // Remix v2: throw new Response("Not Found", { status: 404 })
  return { post, url: absoluteUrl(`/blog/${post.slug}`) };
}

export const meta: Route.MetaFunction = ({ data }) => {
  // RR7 also exposes `loaderData`; `data` is the older name (Remix v2) — use whichever your version types provide.
  if (!data) return [{ title: `Not found | ${siteConfig.name}` }, { name: "robots", content: "noindex" }];
  const { post, url } = data;
  return [
    ...seo({ title: post.title, description: post.excerpt, url, type: "article", image: absoluteUrl(`/og/blog/${post.slug}.png`) }),
    { property: "article:published_time", content: post.publishedAt },
    {
      "script:ld+json": {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        headline: post.title,
        datePublished: post.publishedAt,
        dateModified: post.updatedAt ?? post.publishedAt,
        author: { "@type": "Person", name: post.author.name },
        url,
      },
    },
  ];
};

export default function Post({ loaderData }: Route.ComponentProps) {
  return <article><h1>{loaderData.post.title}</h1></article>;
}
```

- Catch-all `app/routes/$.tsx` with a loader that throws 404 ensures unknown URLs return 404 instead of a 200 empty page.
- `ErrorBoundary` renders the 404 UI; the status code comes from the thrown response.
- Old URLs: `throw redirect("/new-path", 301)` in the loader.

## 7. sitemap.xml and robots.txt resource routes

A route module with only a `loader` (no default export) is a resource route:

```ts
// app/routes/sitemap[.]xml.ts
import { siteConfig } from "~/lib/site";
import { getAllPosts } from "~/lib/posts.server";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

export async function loader() {
  const posts = await getAllPosts();
  const urls = [
    { loc: "/" }, { loc: "/pricing" }, { loc: "/blog" },
    ...posts.map((p) => ({ loc: `/blog/${p.slug}`, lastmod: p.updatedAt ?? p.publishedAt })),
  ];
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((u) => `  <url><loc>${esc(siteConfig.url + u.loc)}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ""}</url>`).join("\n")}
</urlset>`;
  return new Response(body, {
    headers: { "Content-Type": "application/xml; charset=utf-8", "Cache-Control": "public, max-age=3600" },
  });
}
```

If the project uses `app/routes.ts` config instead of flat routes: `route("sitemap.xml", "routes/sitemap.ts")`. `robots.txt` the same way (`Content-Type: text/plain`), or simply `public/robots.txt`. Resource routes can be prerendered too (list `/sitemap.xml` in `prerender`).

## 8. Prerendering

```ts
// react-router.config.ts
import type { Config } from "@react-router/dev/config";
import { getAllPosts } from "./app/lib/posts.server";

export default {
  ssr: true, // keep SSR for dynamic routes; set false for a fully static site
  async prerender({ getStaticPaths }) {
    const posts = await getAllPosts();
    return [...getStaticPaths(), "/sitemap.xml", ...posts.map((p) => `/blog/${p.slug}`)];
  },
} satisfies Config;
```

`getStaticPaths()` returns routes without dynamic params. With `ssr: false`, every non-prerendered URL falls back to the SPA shell — configure the host to return 404 for unknown paths (see `react-spa.md` §8).

## 9. Open Graph images

Options: static images in `public/og/`, generated at build by a script with `satori` + `@resvg/resvg-js`, or a resource route `app/routes/og.$slug[.]png.ts` that renders with `satori` and returns `image/png` with long cache headers. Keep 1200×630, absolute URLs in `og:image`.

## 10. Structured data

Use `"script:ld+json"` meta descriptors (rendered as `<script type="application/ld+json">` by `<Meta />`) or a `<JsonLd>` component in the route. Home route: `Organization` + `WebSite` `@graph`. Templates: `assets/jsonld/`.

## 11. Performance

- `links` export to `preload` the LCP image and critical font (`{ rel: "preload", as: "image", href, fetchPriority: "high" }`).
- Set `Cache-Control` headers via `headers` export for HTML that can be cached at the CDN.
- Avoid waterfalls: load data in parallel in loaders; stream non-critical data with promises + `<Await>`.
- Lazy-load heavy client-only widgets.

## 12. Verify

```bash
npm run build && npm run start &     # react-router-serve ./build/server/index.js (port 3000)
python3 <skill-dir>/scripts/seo_audit.py http://localhost:3000 --crawl 50
python3 <skill-dir>/scripts/validate_jsonld.py http://localhost:3000/
curl -s http://localhost:3000/sitemap.xml | head -20
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/does-not-exist   # 404
# Prerendered build: python3 <skill-dir>/scripts/seo_audit.py build/client
```

## 13. Pitfalls

- Parent `meta` silently disappearing on child routes (§5).
- `meta` that reads `data.post` without a null check crashes the error boundary on 404s.
- Using `process.env` inside `meta` on the client → `undefined` origin.
- Catch-all routes returning 200 for everything.
- `json()`/`defer()` helpers are deprecated in RR7 — return plain objects.
