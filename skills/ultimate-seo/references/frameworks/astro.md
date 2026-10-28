# Astro

Astro renders to static HTML by default (zero JS unless islands opt in), which makes it one of the best SEO foundations. The work is: set `site`, build a `BaseHead` component used by every layout, add `@astrojs/sitemap`, a robots endpoint, OG images, and JSON-LD from content collections.

## Contents

1. Detect
2. Where things go
3. Site config
4. BaseHead component
5. Layouts and pages
6. Content collections → metadata
7. Sitemap and robots.txt
8. Open Graph images
9. Structured data
10. RSS, 404, redirects
11. Performance
12. Verify
13. Pitfalls

## 1. Detect

- `astro.config.(mjs|ts)`, `astro` in dependencies, `src/pages/`.
- `output`: `"static"` (default) → SSG; `"server"` → SSR (needs adapter); in Astro 5, static is default and individual pages opt into SSR with `export const prerender = false`.
- Content collections: Astro 5+ uses `src/content.config.ts` with loaders (`glob`, `file`) and `render(entry)`; Astro 2–4 used `src/content/config.ts` and `entry.render()`. Check which exists.

## 2. Where things go

| Concern | File |
|---|---|
| Canonical origin | `astro.config.*` → `site` |
| Site config | `src/consts.ts` (Astro's blog template convention) or `src/config/site.ts` |
| Head tags | `src/components/BaseHead.astro` |
| Layout | `src/layouts/BaseLayout.astro` (renders `<html lang>` + `BaseHead`) |
| Sitemap | `@astrojs/sitemap` integration |
| robots.txt | `src/pages/robots.txt.ts` (endpoint) or `public/robots.txt` |
| OG images | `src/pages/og/[...slug].png.ts` (satori) or `public/og.png` |
| llms.txt, icons, manifest | `public/` (or `src/pages/llms.txt.ts` generated from collections) |
| 404 | `src/pages/404.astro` |
| Redirects | `redirects` in `astro.config` |

## 3. Site config

```js
// astro.config.mjs
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: process.env.SITE_URL ?? "https://www.example.com",
  trailingSlash: "ignore", // pick "always" or "never" and keep canonicals consistent
  integrations: [
    sitemap({
      filter: (page) => !page.includes("/thank-you") && !page.includes("/search"),
    }),
  ],
});
```

```ts
// src/consts.ts
export const SITE_TITLE = "Acme";
export const SITE_DESCRIPTION = "Acme helps small teams ship invoices in minutes.";
export const DEFAULT_OG_IMAGE = "/og.png";
export const TWITTER = "@acme";
export const SAME_AS: string[] = []; // real profile URLs only
```

`Astro.site` (a `URL`) is available in every component/page once `site` is set — use it for every absolute URL.

## 4. BaseHead component

```astro
---
// src/components/BaseHead.astro
import { SITE_TITLE, SITE_DESCRIPTION, DEFAULT_OG_IMAGE, TWITTER } from "../consts";

interface Props {
  title?: string;
  description?: string;
  image?: string;        // path or absolute URL
  imageAlt?: string;
  type?: "website" | "article";
  noindex?: boolean;
  publishedTime?: Date;
  modifiedTime?: Date;
}

const { title, description = SITE_DESCRIPTION, image = DEFAULT_OG_IMAGE, imageAlt, type = "website", noindex = false, publishedTime, modifiedTime } = Astro.props;
const canonical = new URL(Astro.url.pathname, Astro.site);
const ogImage = new URL(image, Astro.site);
const fullTitle = title ? `${title} | ${SITE_TITLE}` : SITE_TITLE;
---
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{fullTitle}</title>
<meta name="description" content={description} />
<link rel="canonical" href={canonical} />
{noindex && <meta name="robots" content="noindex, follow" />}
<link rel="icon" href="/favicon.ico" sizes="any" />
<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="manifest" href="/manifest.webmanifest" />
<link rel="sitemap" href="/sitemap-index.xml" />
<meta name="theme-color" content="#0a0a0a" />
<meta name="generator" content={Astro.generator} />

<meta property="og:type" content={type} />
<meta property="og:site_name" content={SITE_TITLE} />
<meta property="og:title" content={title ?? SITE_TITLE} />
<meta property="og:description" content={description} />
<meta property="og:url" content={canonical} />
<meta property="og:image" content={ogImage} />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content={imageAlt ?? title ?? SITE_TITLE} />
{publishedTime && <meta property="article:published_time" content={publishedTime.toISOString()} />}
{modifiedTime && <meta property="article:modified_time" content={modifiedTime.toISOString()} />}
<meta name="twitter:card" content="summary_large_image" />
{TWITTER && <meta name="twitter:site" content={TWITTER} />}
<slot />
```

`Astro.url.pathname` excludes query strings, so faceted/tracking params don't leak into canonicals.

## 5. Layouts and pages

```astro
---
// src/layouts/BaseLayout.astro
import BaseHead from "../components/BaseHead.astro";
const { lang = "en", ...seo } = Astro.props;
---
<html lang={lang}>
  <head>
    <BaseHead {...seo}><slot name="head" /></BaseHead>
  </head>
  <body>
    <header><!-- nav with real <a href> links --></header>
    <main><slot /></main>
    <footer></footer>
  </body>
</html>
```

```astro
---
// src/pages/pricing.astro
import BaseLayout from "../layouts/BaseLayout.astro";
---
<BaseLayout title="Pricing" description="Simple plans from $0. Unlimited invoices on every paid plan.">
  <h1>Pricing</h1>
</BaseLayout>
```

## 6. Content collections → metadata

```ts
// src/content.config.ts (Astro 5+)
import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const blog = defineCollection({
  loader: glob({ base: "./src/content/blog", pattern: "**/*.{md,mdx}" }),
  schema: ({ image }) => z.object({
    title: z.string().max(70),
    description: z.string().min(50).max(160), // enforce good meta descriptions at build time
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    heroImage: image().optional(),
    author: z.string(),
    noindex: z.boolean().default(false),
  }),
});
export const collections = { blog };
```

Schema validation turning bad titles/descriptions into **build errors** is a uniquely strong Astro pattern — use it.

```astro
---
// src/pages/blog/[...slug].astro
import { getCollection, render } from "astro:content";
import BaseLayout from "../../layouts/BaseLayout.astro";

export async function getStaticPaths() {
  const posts = await getCollection("blog");
  return posts.map((post) => ({ params: { slug: post.id }, props: { post } }));
}
const { post } = Astro.props;
const { Content } = await render(post); // Astro ≤4: await post.render()
const url = new URL(Astro.url.pathname, Astro.site);
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  headline: post.data.title,
  description: post.data.description,
  datePublished: post.data.pubDate.toISOString(),
  dateModified: (post.data.updatedDate ?? post.data.pubDate).toISOString(),
  author: { "@type": "Person", name: post.data.author },
  image: new URL(`/og/${post.id}.png`, Astro.site).toString(),
  url: url.toString(),
};
---
<BaseLayout title={post.data.title} description={post.data.description} type="article"
  image={`/og/${post.id}.png`} publishedTime={post.data.pubDate} modifiedTime={post.data.updatedDate}
  noindex={post.data.noindex}>
  <script type="application/ld+json" slot="head" set:html={JSON.stringify(jsonLd).replace(/</g, "\\u003c")} />
  <article><h1>{post.data.title}</h1><Content /></article>
</BaseLayout>
```

(Astro ≤4 uses `post.slug` instead of `post.id` for the URL.)

## 7. Sitemap and robots.txt

`@astrojs/sitemap` (install with `npx astro add sitemap`) writes `sitemap-index.xml` + `sitemap-0.xml` at build and requires `site`. Options: `filter`, `customPages` (SSR routes it can't discover), `i18n` (adds hreflang alternates), `serialize(item)` to set `lastmod` from your content (don't use build time).

```ts
// src/pages/robots.txt.ts
import type { APIRoute } from "astro";

const body = (sitemap: URL) => `User-agent: *
Allow: /
Disallow: /api/

Sitemap: ${sitemap.href}
`;

export const GET: APIRoute = ({ site }) =>
  new Response(body(new URL("sitemap-index.xml", site)), { headers: { "Content-Type": "text/plain; charset=utf-8" } });
```

Add the AI-crawler section from `assets/robots.txt`. Delete any `public/robots.txt` so the two don't conflict.

## 8. Open Graph images

Build-time PNGs with `satori` + `@resvg/resvg-js` (no runtime cost):

```ts
// src/pages/og/[...slug].png.ts
import type { APIRoute, GetStaticPaths } from "astro";
import { getCollection, type CollectionEntry } from "astro:content";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import { readFile } from "node:fs/promises";

export const getStaticPaths: GetStaticPaths = async () =>
  (await getCollection("blog")).map((post) => ({ params: { slug: post.id }, props: { post } }));

export const GET: APIRoute = async ({ props }) => {
  const { post } = props as { post: CollectionEntry<"blog"> };
  const font = await readFile("./src/assets/fonts/Inter-Bold.ttf"); // satori needs TTF/OTF/WOFF (not WOFF2)
  const svg = await satori(
    { type: "div", props: { style: { display: "flex", width: "100%", height: "100%", padding: 72, alignItems: "flex-end", background: "#0a0a0a", color: "#fff", fontSize: 64, fontFamily: "Inter" }, children: post.data.title } },
    { width: 1200, height: 630, fonts: [{ name: "Inter", data: font, weight: 700, style: "normal" }] },
  );
  const png = new Resvg(svg).render().asPng();
  return new Response(png, { headers: { "Content-Type": "image/png" } });
};
```

Community wrappers (`astro-og-canvas`, `astro-opengraph-images`) do the same with less code; fine to use if preferred.

## 9. Structured data

Home page: `Organization` + `WebSite` `@graph` in `src/pages/index.astro` via `<script type="application/ld+json" set:html={...} />`. Always `set:html` with `JSON.stringify` (escaping `<`), never interpolate into a template string. Templates: `assets/jsonld/`.

## 10. RSS, 404, redirects

- `@astrojs/rss`: `src/pages/rss.xml.js` from the blog collection; add `<link rel="alternate" type="application/rss+xml" href="/rss.xml">` in `BaseHead`.
- `src/pages/404.astro` → `404.html`; static hosts serve it with status 404. Pass `noindex`.
- `redirects: { "/old": "/new" }` in config — static builds emit meta-refresh HTML pages; for real 301s configure the host (`_redirects`, `vercel.json`) or use an adapter that supports redirects.

## 11. Performance

- `<Image>` / `<Picture>` from `astro:assets` (auto width/height, WebP/AVIF). For the LCP image set `loading="eager"` and `fetchpriority="high"` (Astro 5.10+ also offers a `priority` shorthand on `<Image>` — use it if available).
- Keep islands minimal; prefer `client:visible`/`client:idle` over `client:load`.
- Fonts: Astro's experimental/built-in Fonts API (5.x) or `@fontsource/*`; preload the primary weight.
- Inline small stylesheets is default; avoid heavy CSS frameworks shipping unused CSS.

## 12. Verify

```bash
SITE_URL=https://www.example.com npx astro build
python3 <skill-dir>/scripts/seo_audit.py dist
python3 <skill-dir>/scripts/validate_jsonld.py dist
ls dist/sitemap-index.xml dist/robots.txt dist/og/
npx astro preview &   # :4321
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:4321/nope   # 404
```

## 13. Pitfalls

- Missing `site` → `Astro.site` undefined, sitemap integration fails, canonicals break.
- Canonical/sitemap trailing-slash mismatch with `trailingSlash` and the host's behavior.
- Putting `<title>` in both layout and page slot → duplicates.
- Satori fails silently on WOFF2 fonts or multi-child elements without `display: flex`.
