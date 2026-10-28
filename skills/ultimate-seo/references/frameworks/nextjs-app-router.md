# Next.js — App Router

The App Router has first-class SEO primitives: the Metadata API, file-based `sitemap`/`robots`/`manifest`/`opengraph-image`, and Server Components that render everything to HTML. Use them instead of hand-written `<head>` tags or third-party SEO packages (`next-seo` is for the Pages Router).

## Contents

1. Detect
2. Where things go
3. Site config
4. Root layout metadata
5. Per-page and dynamic metadata
6. robots.ts
7. sitemap.ts (and large sitemaps)
8. Open Graph images
9. Icons and manifest
10. Structured data
11. 404s, redirects, noindex
12. Performance
13. Verify
14. Pitfalls

## 1. Detect

- `app/` or `src/app/` with `layout.tsx|jsx` → App Router. If `pages/` exists too, it's mixed; apply this file to `app/` routes and `nextjs-pages-router.md` to `pages/` routes.
- Version: `next` in `package.json`. **15+**: `params`/`searchParams` are Promises (await them). **14**: they're plain objects. **16**: same as 15, `middleware.ts` renamed to `proxy.ts`, Turbopack default.
- Rendering: Server Components render on the server by default. `output: 'export'` in `next.config.*` means fully static — file-based metadata routes still work but must be static (no request-time data); `generateStaticParams` is required for dynamic segments.
- A `"use client"` page cannot export `metadata`/`generateMetadata`. Move the metadata to a server `page.tsx` that renders the client component, or to a `layout.tsx`.

## 2. Where things go

| Concern | File |
|---|---|
| Site config | `lib/site.ts` (or `src/config/site.ts` — follow repo) |
| Global defaults, `metadataBase`, title template | `app/layout.tsx` → `export const metadata` |
| Per-page metadata | `app/**/page.tsx` → `metadata` or `generateMetadata` |
| robots.txt | `app/robots.ts` |
| sitemap.xml | `app/sitemap.ts` (or `app/<segment>/sitemap.ts` + `generateSitemaps`) |
| OG / Twitter images | `app/opengraph-image.tsx`, `app/**/opengraph-image.tsx`, `twitter-image.*` |
| Favicon/icons | `app/favicon.ico`, `app/icon.(png\|svg)`, `app/apple-icon.png` |
| Manifest | `app/manifest.ts` |
| JSON-LD | `components/json-ld.tsx`, rendered in page/layout |
| llms.txt | `public/llms.txt` or `app/llms.txt/route.ts` for dynamic |
| 404 | `app/not-found.tsx` |
| Redirects | `next.config.*` `redirects()`; host canonicalization at the platform (Vercel domain settings) |

## 3. Site config

```ts
// lib/site.ts
export const siteConfig = {
  name: "Acme",
  url: (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, ""),
  description: "Acme helps small teams ship invoices in minutes.",
  locale: "en_US",
  ogImage: "/og.png", // fallback if no opengraph-image file exists
  twitter: "@acme", // leave undefined if unknown — don't invent
  sameAs: [] as string[], // real social profile URLs only
} as const;

export const absoluteUrl = (path = "/") => new URL(path, siteConfig.url).toString();
```

On Vercel, `VERCEL_PROJECT_PRODUCTION_URL` (no protocol) is available at build time; a common fallback is `process.env.NEXT_PUBLIC_SITE_URL ?? (process.env.VERCEL_PROJECT_PRODUCTION_URL ? \`https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}\` : "http://localhost:3000")`. Never use preview URLs (`VERCEL_URL`) as canonical.

## 4. Root layout metadata

```tsx
// app/layout.tsx
import type { Metadata, Viewport } from "next";
import { siteConfig } from "@/lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: { default: `${siteConfig.name} — Invoicing for small teams`, template: `%s | ${siteConfig.name}` },
  description: siteConfig.description,
  applicationName: siteConfig.name,
  // No alternates.canonical or openGraph.url here: children inherit them (see the trap below).
  // Set both on every page instead; the home page sets canonical "/" in app/page.tsx.
  openGraph: {
    type: "website",
    siteName: siteConfig.name,
    locale: siteConfig.locale,
  },
  twitter: { card: "summary_large_image", site: siteConfig.twitter },
  robots: { index: true, follow: true, googleBot: { "max-image-preview": "large", "max-snippet": -1, "max-video-preview": -1 } },
  // verification: { google: "...", other: { "msvalidate.01": "..." } }, // only with real tokens
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

Notes:
- `metadataBase` makes every relative URL in metadata (canonical, OG url/image) absolute. Without it, Next warns and falls back to localhost in some cases.
- `viewport`/`themeColor` belong in the `viewport` export (Next 14+); putting them in `metadata` is deprecated.
- `charset` and `viewport` meta are added automatically.
- **Canonical inheritance trap:** `alternates.canonical: "/"` in the root layout is inherited by every child that doesn't set its own — every page would canonicalize to the home page. That's why the example above omits it: set `alternates.canonical` and `openGraph.url` on every page instead.
- Nested `openGraph` objects are **shallow-merged per key**: if a page defines `openGraph`, it replaces the layout's whole `openGraph` object. Spread a shared base (`...baseOpenGraph`) in pages.

## 5. Per-page and dynamic metadata

Static page:

```tsx
// app/pricing/page.tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing", // → "Pricing | Acme"
  description: "Simple plans from $0. Unlimited invoices, Stripe payouts, and team seats on every paid plan.",
  alternates: { canonical: "/pricing" },
  openGraph: { title: "Pricing — Acme", url: "/pricing" },
};
```

Dynamic route (Next 15+ signature; on 14 drop the `Promise`/`await`):

```tsx
// app/blog/[slug]/page.tsx
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getPost, getAllPosts } from "@/lib/posts";

type Props = { params: Promise<{ slug: string }> };

export async function generateStaticParams() {
  return (await getAllPosts()).map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) return {};
  const url = `/blog/${post.slug}`;
  return {
    title: post.seoTitle ?? post.title,
    description: post.excerpt,
    alternates: { canonical: url },
    authors: [{ name: post.author.name, url: post.author.url }],
    openGraph: {
      type: "article",
      url,
      title: post.title,
      description: post.excerpt,
      publishedTime: post.publishedAt,
      modifiedTime: post.updatedAt,
      authors: [post.author.name],
      // images come from app/blog/[slug]/opengraph-image.tsx automatically
    },
  };
}

export default async function Page({ params }: Props) {
  const { slug } = await params;
  const post = await getPost(slug);
  if (!post) notFound();
  return <article>{/* <h1>{post.title}</h1> ... */}</article>;
}
```

`fetch`/data calls in `generateMetadata` and the page are deduped (React `cache` for non-fetch data: wrap `getPost` in `cache()` from `react`).

Use `title: { absolute: "..." }` to bypass the template (e.g. the home page).

## 6. robots.ts

```ts
// app/robots.ts
import type { MetadataRoute } from "next";
import { siteConfig } from "@/lib/site";

export default function robots(): MetadataRoute.Robots {
  const isProd = process.env.VERCEL_ENV ? process.env.VERCEL_ENV === "production" : process.env.NODE_ENV === "production";
  if (!isProd) return { rules: [{ userAgent: "*", disallow: "/" }] }; // previews only
  return {
    rules: [
      { userAgent: "*", allow: "/", disallow: ["/api/", "/admin/", "/search"] },
      // explicit AI policy — see references/ai-search.md. A named group REPLACES the "*" group
      // for that bot, so repeat the disallows.
      { userAgent: ["GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot"], allow: "/", disallow: ["/api/", "/admin/"] },
    ],
    sitemap: `${siteConfig.url}/sitemap.xml`,
    host: siteConfig.url,
  };
}
```

Better than disallowing previews in robots: also send `X-Robots-Tag: noindex` on non-production deployments (Vercel does this automatically for preview URLs). Don't disallow `/_next/` — Google needs the JS/CSS.

## 7. sitemap.ts

```ts
// app/sitemap.ts
import type { MetadataRoute } from "next";
import { siteConfig } from "@/lib/site";
import { getAllPosts } from "@/lib/posts";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes = ["", "/pricing", "/about", "/blog"].map((path) => ({
    url: `${siteConfig.url}${path}`,
  }));
  const posts = (await getAllPosts()).map((p) => ({
    url: `${siteConfig.url}/blog/${p.slug}`,
    lastModified: new Date(p.updatedAt ?? p.publishedAt),
  }));
  return [...staticRoutes, ...posts];
}
```

- Omit `lastModified` where you have no real date (don't use `new Date()`). `changeFrequency`/`priority` are ignored by Google; skip them.
- Localized alternates: `alternates: { languages: { es: \`${siteConfig.url}/es/...\` } }` per entry.
- Images/videos: entries accept `images: string[]` and `videos: [...]` (Next 15+).
- **> 50,000 URLs**: export `generateSitemaps()` returning `[{ id: 0 }, { id: 1 }, ...]` from e.g. `app/products/sitemap.ts`; Next serves `/products/sitemap/0.xml`, etc. The `sitemap({ id })` signature receives the id (in Next 16 it is passed as a Promise — `const id = await props.id` — check your version's docs). Next does not auto-generate a sitemap index for these; create `app/sitemap.xml/route.ts` (or a static sitemap index) that lists them, and reference it in robots.
- Sitemaps are cached/static by default. For frequently changing data add `export const revalidate = 3600`.

## 8. Open Graph images

```tsx
// app/blog/[slug]/opengraph-image.tsx
import { ImageResponse } from "next/og";
import { getPost } from "@/lib/posts";

export const alt = "Acme blog post";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = await getPost(slug);
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 72, background: "#0a0a0a", color: "#fff" }}>
        <div style={{ fontSize: 32, opacity: 0.7 }}>Acme</div>
        <div style={{ fontSize: 64, fontWeight: 700, lineHeight: 1.1 }}>{post?.title ?? "Acme"}</div>
      </div>
    ),
    size,
  );
}
```

- File-based images automatically emit `og:image`, `og:image:width/height/type/alt`, with absolute URLs via `metadataBase`. Add `twitter-image.tsx` or re-export: `export { default, alt, size, contentType } from "./opengraph-image";`.
- Satori supports flexbox and a CSS subset only; every multi-child `div` needs `display: "flex"`. Load custom fonts with `fetch(new URL("./Inter-Bold.ttf", import.meta.url)).then(r => r.arrayBuffer())` (edge) or `readFile` (node) and pass `fonts: [...]`.
- Root `app/opengraph-image.png` (static file) is the simplest default for every page.

## 9. Icons and manifest

Drop files in `app/`: `favicon.ico`, `icon.svg` (or `icon.png`), `apple-icon.png` (180×180). Next emits the `<link>` tags.

```ts
// app/manifest.ts
import type { MetadataRoute } from "next";
import { siteConfig } from "@/lib/site";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: siteConfig.name,
    short_name: siteConfig.name,
    description: siteConfig.description,
    start_url: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#0a0a0a",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  };
}
```

## 10. Structured data

```tsx
// components/json-ld.tsx
export function JsonLd({ data }: { data: Record<string, unknown> | Record<string, unknown>[] }) {
  return (
    <script
      type="application/ld+json"
      // escape "<" so content can't close the script tag (XSS)
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}
```

Home page (`app/page.tsx`): an `@graph` with `Organization` + `WebSite` (templates in `assets/jsonld/`). Blog post page: `BlogPosting` + `BreadcrumbList` built from the same `post` object used for metadata, so they never disagree. Render `<JsonLd>` inside the page component (Server Component) — it lands in the HTML. Use `schema-dts` types (`WithContext<BlogPosting>`) if the project likes strict typing.

## 11. 404s, redirects, noindex

- Call `notFound()` for missing data → real 404 + `app/not-found.tsx`. Never render "not found" UI with a 200.
- Permanent redirects: `next.config` `async redirects() { return [{ source: "/old", destination: "/new", permanent: true }] }` (308). For thousands, use a proxy/middleware lookup.
- Utility pages: `export const metadata = { robots: { index: false, follow: true } }` (search, thank-you, auth). `app/(auth)/layout.tsx` can set it once for a route group.
- Trailing slash: choose with `trailingSlash` in config (default false) and keep sitemap/canonicals consistent.
- Draft/preview: ensure `draftMode` pages aren't linked publicly.

## 12. Performance

- `next/image` for every content image; on the LCP image (hero) set `priority` (Next ≤15). In Next 16 `priority` is deprecated in favour of `preload` (and `fetchPriority="high"` is passed through) — use whatever the installed version supports without warnings. Always give `sizes` for responsive images.
- `next/font` (`next/font/google` or `next/font/local`) — self-hosts, zero layout shift, `display: "swap"` by default.
- Third-party scripts: `next/script` with `strategy="afterInteractive"` (analytics) or `"lazyOnload"` (chat widgets). Use `@next/third-parties` for GA/GTM/YouTube where available.
- Keep pages Server Components; push `"use client"` down to leaf components to cut JS (helps INP).
- Prefer static/ISR (`export const revalidate = N`) for marketing pages; avoid `cookies()`/`headers()` in layouts — it makes every page dynamic.

## 13. Verify

```bash
npm run build                       # metadata errors and missing metadataBase warnings appear here
npm run start &                     # or: npx next start -p 3000
python3 <skill-dir>/scripts/seo_audit.py http://localhost:3000 --crawl 50
python3 <skill-dir>/scripts/validate_jsonld.py http://localhost:3000/
curl -s http://localhost:3000/robots.txt; curl -s http://localhost:3000/sitemap.xml | head -40
curl -sI http://localhost:3000/opengraph-image | head -5
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/definitely-missing   # expect 404
```

For `output: 'export'`, audit the `out/` directory instead. Set `NEXT_PUBLIC_SITE_URL` to the production origin when building for the audit so canonicals are realistic.

## 14. Pitfalls

- Metadata exported from a `"use client"` file is silently ignored (build error in newer versions). Keep it in server files.
- Root-layout `alternates.canonical` inherited by every page (see §4).
- Shallow merge of `openGraph`/`twitter` objects drops the layout's `siteName`/`images` when a page sets its own.
- `generateMetadata` that throws turns the page into a 500 — return `{}` on missing data and let the page call `notFound()`.
- Streaming metadata (Next 15.2+): for bots Next blocks to put metadata in `<head>`; for browsers it may stream metadata into `<body>`. This is expected; HTML-limited bots are detected via `htmlLimitedBots`. Don't "fix" it.
- `searchParams`-driven pages (filters, sort) should canonicalize to the clean path.
- Don't add `next-seo` to an App Router project — it targets the Pages Router.
