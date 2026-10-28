# Next.js — Pages Router

The Pages Router (`pages/` directory) has no Metadata API. Metadata goes in `next/head`, sitemaps and robots come from `getServerSideProps` routes, API routes, or `next-sitemap`. Pages render on the server (SSR/SSG), so content is crawlable as long as data is fetched in `getStaticProps`/`getServerSideProps` rather than in `useEffect`.

## Contents

1. Detect
2. Where things go
3. Site config
4. SEO component
5. Per-page usage and dynamic routes
6. robots.txt and sitemap.xml
7. Open Graph images
8. Icons and manifest
9. Structured data
10. 404s, redirects, noindex
11. Performance
12. Verify
13. Pitfalls

## 1. Detect

- `pages/` or `src/pages/` with `_app.(t|j)sx`, no `app/layout.*` → Pages Router. Mixed projects: use this for `pages/` routes only.
- `output: 'export'` in `next.config.*` (or `next export` in scripts on old versions) → static; `getServerSideProps` is unavailable.
- Data fetched client-side (`useEffect`, SWR without fallback) means that content is **not** in the HTML — move SEO-relevant data to `getStaticProps` (+ `revalidate` for ISR) or `getServerSideProps`.
- Migration: if the project is on Next 13.4+ and actively developed, mention incremental App Router migration in the playbook; don't migrate as part of the SEO task.

## 2. Where things go

| Concern | File |
|---|---|
| Site config | `lib/site.ts` |
| `<html lang>` | `pages/_document.tsx` (or `i18n` in `next.config` sets it automatically) |
| Default head + SEO component | `components/Seo.tsx`, used in each page; global defaults in `_app.tsx` |
| robots.txt | `public/robots.txt` (static) or `pages/robots.txt.ts` (dynamic) |
| sitemap.xml | `pages/sitemap.xml.ts` via `getServerSideProps`, or `next-sitemap` postbuild |
| OG images | `pages/api/og.tsx` with `@vercel/og`, or static `public/og/*.png` |
| Icons/manifest | `public/` + `<link>`s in `_document.tsx` |
| 404 | `pages/404.tsx`; `return { notFound: true }` from data functions |
| Redirects | `next.config` `redirects()` |

## 3. Site config

```ts
// lib/site.ts
export const siteConfig = {
  name: "Acme",
  url: (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, ""),
  description: "Acme helps small teams ship invoices in minutes.",
  locale: "en_US",
  defaultOgImage: "/og.png",
  twitter: "@acme",
};
export const absoluteUrl = (path = "/") => new URL(path, siteConfig.url).toString();
```

## 4. SEO component

```tsx
// components/Seo.tsx
import Head from "next/head";
import { useRouter } from "next/router";
import { siteConfig, absoluteUrl } from "@/lib/site";

type SeoProps = {
  title?: string;           // page title without brand
  description?: string;
  path?: string;            // canonical path; defaults to current path without query/hash
  image?: string;           // absolute or root-relative
  imageAlt?: string;
  type?: "website" | "article";
  noindex?: boolean;
  publishedTime?: string;
  modifiedTime?: string;
};

export function Seo({ title, description = siteConfig.description, path, image = siteConfig.defaultOgImage, imageAlt, type = "website", noindex, publishedTime, modifiedTime }: SeoProps) {
  const { asPath } = useRouter();
  const canonical = absoluteUrl(path ?? asPath.split(/[?#]/)[0]);
  const fullTitle = title ? `${title} | ${siteConfig.name}` : siteConfig.name;
  const img = absoluteUrl(image);
  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />
      {noindex && <meta name="robots" content="noindex, follow" />}
      <meta property="og:type" content={type} />
      <meta property="og:site_name" content={siteConfig.name} />
      <meta property="og:locale" content={siteConfig.locale} />
      <meta property="og:title" content={title ?? siteConfig.name} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonical} />
      <meta property="og:image" content={img} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:image:alt" content={imageAlt ?? title ?? siteConfig.name} />
      {publishedTime && <meta property="article:published_time" content={publishedTime} />}
      {modifiedTime && <meta property="article:modified_time" content={modifiedTime} />}
      <meta name="twitter:card" content="summary_large_image" />
      {siteConfig.twitter && <meta name="twitter:site" content={siteConfig.twitter} />}
    </Head>
  );
}
```

`next/head` dedupes by tag name for `<title>`/`<meta name>`; give tags a `key` prop if both `_app` and a page set them so the page wins. `asPath` on dynamic SSG pages is correct at build time; prefer passing `path` explicitly for dynamic routes.

Alternative: if the project already uses **`next-seo`**, keep it (`<NextSeo>`, `DefaultSeo` in `_app`, `ArticleJsonLd` etc.) — just make sure canonical and `openGraph.url` are set per page.

## 5. Per-page usage and dynamic routes

```tsx
// pages/blog/[slug].tsx
import type { GetStaticPaths, GetStaticProps, InferGetStaticPropsType } from "next";
import { Seo } from "@/components/Seo";
import { JsonLd } from "@/components/JsonLd";
import { getPost, getAllPosts } from "@/lib/posts";
import { absoluteUrl, siteConfig } from "@/lib/site";

export const getStaticPaths: GetStaticPaths = async () => ({
  paths: (await getAllPosts()).map((p) => ({ params: { slug: p.slug } })),
  fallback: "blocking",
});

export const getStaticProps: GetStaticProps = async ({ params }) => {
  const post = await getPost(String(params?.slug));
  if (!post) return { notFound: true, revalidate: 60 };
  return { props: { post }, revalidate: 3600 };
};

export default function PostPage({ post }: InferGetStaticPropsType<typeof getStaticProps>) {
  const path = `/blog/${post.slug}`;
  return (
    <>
      <Seo title={post.title} description={post.excerpt} path={path} type="article" image={`/api/og?title=${encodeURIComponent(post.title)}`} publishedTime={post.publishedAt} modifiedTime={post.updatedAt} />
      <JsonLd data={{
        "@context": "https://schema.org", "@type": "BlogPosting",
        headline: post.title, description: post.excerpt, url: absoluteUrl(path),
        datePublished: post.publishedAt, dateModified: post.updatedAt ?? post.publishedAt,
        author: { "@type": "Person", name: post.author.name },
        publisher: { "@type": "Organization", name: siteConfig.name, logo: { "@type": "ImageObject", url: absoluteUrl("/logo.png") } },
        image: absoluteUrl(`/api/og?title=${encodeURIComponent(post.title)}`),
      }} />
      <article><h1>{post.title}</h1>{/* ... */}</article>
    </>
  );
}
```

`_document.tsx` sets `lang`:

```tsx
import { Html, Head, Main, NextScript } from "next/document";
export default function Document() {
  return (
    <Html lang="en">
      <Head>{/* icons, manifest, theme-color — NOT <title> */}</Head>
      <body><Main /><NextScript /></body>
    </Html>
  );
}
```

## 6. robots.txt and sitemap.xml

Option A — **`next-sitemap`** (simplest, generates both after build):

```js
// next-sitemap.config.js
/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || "https://www.example.com",
  generateRobotsTxt: true,
  exclude: ["/api/*", "/admin/*", "/thank-you"],
  robotsTxtOptions: { policies: [{ userAgent: "*", allow: "/", disallow: ["/api/", "/admin/"] }] },
  autoLastmod: false, // don't stamp build time on every URL
};
```

Add `"postbuild": "next-sitemap"` to `package.json`. Pages under `getServerSideProps` aren't discovered — add them via `additionalPaths` or a server sitemap (`getServerSideSitemap` from `next-sitemap`).

Option B — **dynamic route** (no dependency, works with SSR data):

```ts
// pages/sitemap.xml.ts
import type { GetServerSideProps } from "next";
import { siteConfig } from "@/lib/site";
import { getAllPosts } from "@/lib/posts";

const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

export const getServerSideProps: GetServerSideProps = async ({ res }) => {
  const posts = await getAllPosts();
  const urls = [
    { loc: "/" }, { loc: "/pricing" }, { loc: "/blog" },
    ...posts.map((p) => ({ loc: `/blog/${p.slug}`, lastmod: p.updatedAt ?? p.publishedAt })),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map((u) => `  <url><loc>${esc(siteConfig.url + u.loc)}</loc>${u.lastmod ? `<lastmod>${u.lastmod}</lastmod>` : ""}</url>`).join("\n")}
</urlset>`;
  res.setHeader("Content-Type", "application/xml; charset=utf-8");
  res.setHeader("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=86400");
  res.write(xml);
  res.end();
  return { props: {} };
};
export default function Sitemap() { return null; }
```

`pages/robots.txt.ts` follows the same pattern, or use `public/robots.txt` with the absolute sitemap URL. With `output: 'export'`, use Option A or generate files in a prebuild script.

## 7. Open Graph images

```tsx
// pages/api/og.tsx
import { ImageResponse } from "@vercel/og"; // in Next 13.4+ "next/og" also works
export const config = { runtime: "edge" };

export default function handler(req: Request) {
  const title = new URL(req.url).searchParams.get("title")?.slice(0, 120) ?? "Acme";
  return new ImageResponse(
    (<div style={{ display: "flex", width: "100%", height: "100%", padding: 72, alignItems: "flex-end", background: "#0a0a0a", color: "#fff", fontSize: 64, fontWeight: 700 }}>{title}</div>),
    { width: 1200, height: 630 },
  );
}
```

Truncate/sanitize the query param; set a long cache header for stable titles. A static `public/og.png` remains the default.

## 8. Icons and manifest

Place `favicon.ico`, `icon.svg`, `apple-touch-icon.png` (180×180), `site.webmanifest` in `public/` and link them in `_document.tsx`:

```tsx
<link rel="icon" href="/favicon.ico" sizes="any" />
<link rel="icon" href="/icon.svg" type="image/svg+xml" />
<link rel="apple-touch-icon" href="/apple-touch-icon.png" />
<link rel="manifest" href="/site.webmanifest" />
<meta name="theme-color" content="#0a0a0a" />
```

## 9. Structured data

```tsx
// components/JsonLd.tsx
import Head from "next/head";
export function JsonLd({ data }: { data: object }) {
  return (
    <Head>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }} />
    </Head>
  );
}
```

Home page: `Organization` + `WebSite` `@graph`. Templates: `assets/jsonld/`. Build from the same props as the visible content.

## 10. 404s, redirects, noindex

- `return { notFound: true }` from `getStaticProps`/`getServerSideProps` → real 404 with `pages/404.tsx`.
- Client-side "not found" states inside a 200 page are soft 404s — avoid.
- Redirects in `next.config` (`permanent: true` → 308) or `return { redirect: { destination, permanent: true } }` from data functions.
- `<Seo noindex />` on search, auth, thank-you pages.

## 11. Performance

- `next/image` with `priority` on the hero/LCP image, `sizes` on responsive images.
- `next/font` in `_app.tsx`.
- `next/script` `strategy="afterInteractive"`/`"lazyOnload"` for third parties; never raw `<script>` in `_document` head for analytics.
- Large `_app` imports ship to every page — lazy-load heavy components with `next/dynamic`.

## 12. Verify

```bash
npm run build && npm run start &
python3 <skill-dir>/scripts/seo_audit.py http://localhost:3000 --crawl 50
python3 <skill-dir>/scripts/validate_jsonld.py http://localhost:3000/
curl -s http://localhost:3000/sitemap.xml | head -30; curl -s http://localhost:3000/robots.txt
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/blog/does-not-exist   # 404
```

Static export: `python3 <skill-dir>/scripts/seo_audit.py out`.

## 13. Pitfalls

- `<title>` inside `_document.tsx` `<Head>` — Next warns; titles belong in page-level `next/head`.
- Multiple `<Head>` blocks setting the same meta without `key` → duplicates.
- `fallback: true` renders a loading shell first; bots usually get the full page, but `fallback: "blocking"` is safer for SEO.
- Canonical built from `asPath` includes query strings unless stripped.
- `next-sitemap` with `autoLastmod: true` (default) stamps every URL with build time.
