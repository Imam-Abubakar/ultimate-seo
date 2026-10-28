# Gatsby

Gatsby prerenders every page to static HTML at build time, so content is crawlable by default. SEO work is the Gatsby Head API (v4.19+), `siteMetadata` as the config source, and the standard plugins for sitemap, robots and manifest. Gatsby has been in maintenance mode since 2023–24; mention a migration path (Astro for content sites, Next.js for apps) in the playbook only if the user is planning a rewrite anyway.

## Contents

1. Detect
2. Where things go
3. Site config (`siteMetadata`)
4. SEO component + Head API
5. `<html lang>`
6. Sitemap, robots, manifest
7. Open Graph images
8. Structured data
9. 404s and redirects
10. Performance
11. Verify
12. Pitfalls

## 1. Detect

- `gatsby-config.(js|ts|mjs)`, `gatsby` in dependencies, `src/pages/`, scripts `gatsby build`.
- Version: Head API needs **4.19+**. Older projects use `react-helmet` + `gatsby-plugin-react-helmet` — migrate those pages to `export const Head` (the plugin is deprecated in v5).
- Rendering per page: default SSG; `export async function getServerData` → SSR; `export const config = { defer: true }` → DSG (built on first request). All produce real HTML.

## 2. Where things go

| Concern | File |
|---|---|
| Site config | `gatsby-config` → `siteMetadata` |
| SEO component | `src/components/seo.tsx` + `src/hooks/use-site-metadata.ts` |
| Per-page metadata | `export const Head` in each page/template |
| `<html lang>` | `gatsby-ssr.js` `onRenderBody` → `setHtmlAttributes` |
| Sitemap | `gatsby-plugin-sitemap` |
| robots.txt | `gatsby-plugin-robots-txt` or `static/robots.txt` |
| Manifest/icons | `gatsby-plugin-manifest` |
| llms.txt, static OG image | `static/` |
| 404 | `src/pages/404.tsx` |

## 3. Site config

```js
// gatsby-config.js
module.exports = {
  siteMetadata: {
    title: "Acme",
    titleTemplate: "%s | Acme",
    description: "Acme helps small teams ship invoices in minutes.",
    siteUrl: (process.env.SITE_URL || "https://www.example.com").replace(/\/$/, ""),
    image: "/og.png",
    twitterUsername: "@acme",
  },
  plugins: [
    "gatsby-plugin-image",
    "gatsby-plugin-sharp",
    "gatsby-transformer-sharp",
    {
      resolve: "gatsby-plugin-sitemap",
      options: { excludes: ["/thank-you/", "/search/"] },
    },
    {
      resolve: "gatsby-plugin-robots-txt",
      options: {
        resolveEnv: () => process.env.CONTEXT || process.env.NODE_ENV, // Netlify sets CONTEXT
        env: {
          production: { policy: [{ userAgent: "*", allow: "/" }] },
          "deploy-preview": { policy: [{ userAgent: "*", disallow: ["/"] }], sitemap: null, host: null },
          "branch-deploy": { policy: [{ userAgent: "*", disallow: ["/"] }], sitemap: null, host: null },
        },
      },
    },
    {
      resolve: "gatsby-plugin-manifest",
      options: {
        name: "Acme", short_name: "Acme", start_url: "/",
        background_color: "#ffffff", theme_color: "#0a0a0a", display: "standalone",
        icon: "src/images/icon.png", // ≥512×512 source; generates favicons + apple-touch-icon
      },
    },
  ],
};
```

`gatsby-plugin-sitemap` reads `siteMetadata.siteUrl` (or a `resolveSiteUrl` option) and writes `sitemap-index.xml` + `sitemap-0.xml`. Point robots at `/sitemap-index.xml`. For `lastmod`, use the plugin's `query` + `resolvePages` + `serialize` options to pull dates from your content nodes.

```ts
// src/hooks/use-site-metadata.ts
import { graphql, useStaticQuery } from "gatsby";
export const useSiteMetadata = () =>
  useStaticQuery(graphql`
    query SiteMeta { site { siteMetadata { title titleTemplate description siteUrl image twitterUsername } } }
  `).site.siteMetadata;
```

## 4. SEO component + Head API

```tsx
// src/components/seo.tsx
import * as React from "react";
import { useSiteMetadata } from "../hooks/use-site-metadata";

type Props = { title?: string; description?: string; pathname?: string; image?: string; article?: boolean; noindex?: boolean; children?: React.ReactNode };

export const Seo = ({ title, description, pathname = "/", image, article, noindex, children }: Props) => {
  const m = useSiteMetadata();
  const url = `${m.siteUrl}${pathname}`;
  const img = `${m.siteUrl}${image ?? m.image}`;
  const fullTitle = title ? m.titleTemplate.replace("%s", title) : m.title;
  const desc = description ?? m.description;
  return (
    <>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <link rel="canonical" href={url} />
      {noindex && <meta name="robots" content="noindex, follow" />}
      <meta property="og:type" content={article ? "article" : "website"} />
      <meta property="og:site_name" content={m.title} />
      <meta property="og:title" content={title ?? m.title} />
      <meta property="og:description" content={desc} />
      <meta property="og:url" content={url} />
      <meta property="og:image" content={img} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta name="twitter:card" content="summary_large_image" />
      {m.twitterUsername && <meta name="twitter:site" content={m.twitterUsername} />}
      {children}
    </>
  );
};
```

```tsx
// src/templates/blog-post.tsx
import { graphql, type HeadProps } from "gatsby";
import { Seo } from "../components/seo";

export const Head = ({ data, location }: HeadProps<Queries.BlogPostQuery>) => {
  const post = data.markdownRemark!;
  return (
    <Seo title={post.frontmatter!.title!} description={post.excerpt!} pathname={location.pathname} article>
      <script type="application/ld+json">{JSON.stringify({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        headline: post.frontmatter!.title,
        datePublished: post.frontmatter!.date,
        author: { "@type": "Person", name: post.frontmatter!.author },
      })}</script>
    </Seo>
  );
};

export const query = graphql`
  query BlogPost($id: String!) {
    markdownRemark(id: { eq: $id }) { excerpt(pruneLength: 155) frontmatter { title date author } }
  }
`;
```

- `Head` receives `location`, `params`, `data`, `pageContext` — **not** React context; hooks using `useStaticQuery` work, but context providers from `wrapRootElement` are not available.
- `location.pathname` includes the trailing slash per your `trailingSlash` config (Gatsby 5 default `"always"`); keep canonicals and sitemap consistent with it.
- Only valid head elements (`title`, `meta`, `link`, `style`, `script`, `noscript`, `base`) are allowed in `Head`.

## 5. `<html lang>`

```js
// gatsby-ssr.js
exports.onRenderBody = ({ setHtmlAttributes }) => { setHtmlAttributes({ lang: "en" }); };
```

## 6. Sitemap, robots, manifest

Configured in §3. Also add `static/llms.txt` (template `assets/llms.txt`). If the site isn't on Netlify, change `resolveEnv` to whatever distinguishes production (e.g. `process.env.VERCEL_ENV`).

## 7. Open Graph images

Default: `static/og.png` (1200×630). Per-post: generate at build in `gatsby-node` `onPostBuild` / `createPages` with `satori` + `@resvg/resvg-js`, write to `public/og/<slug>.png`, and pass `image="/og/<slug>.png"` to `<Seo>`. Or use a frontmatter `image` processed by `gatsby-plugin-image`/`getSrc` (needs absolute URL: prefix `siteUrl`).

## 8. Structured data

JSON-LD inside `Head` as children of `<Seo>` (above). Home page (`src/pages/index.tsx` `Head`): `Organization` + `WebSite` `@graph` built from `siteMetadata`. Templates: `assets/jsonld/`.

## 9. 404s and redirects

- `src/pages/404.tsx` is served with status 404 by Gatsby-aware hosts (Netlify, Gatsby Cloud successors, most static hosts serving `404.html`). Add `<Seo title="Page not found" noindex />` in its `Head`.
- `createRedirect({ fromPath, toPath, isPermanent: true })` in `gatsby-node` — needs a host adapter/plugin to take effect (`gatsby-adapter-netlify`, or `_redirects` file on Netlify).

## 10. Performance

- `gatsby-plugin-image` (`StaticImage`/`GatsbyImage`) with `loading="eager"` on the LCP image; others lazy by default.
- Self-host fonts (`@fontsource/*`) instead of Google Fonts `<link>`.
- `gatsby-plugin-google-gtag` loads async; use Partytown (`<Script strategy="off-main-thread">` from `gatsby`) for heavy third parties.
- Check `public/` for oversized page-data JSON (huge GraphQL queries bloat every page).

## 11. Verify

```bash
SITE_URL=https://www.example.com npx gatsby build
python3 <skill-dir>/scripts/seo_audit.py public
python3 <skill-dir>/scripts/validate_jsonld.py public
ls public/sitemap-index.xml public/robots.txt public/manifest.webmanifest
npx gatsby serve &   # :9000
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:9000/nope   # 404
```

## 12. Pitfalls

- Leftover `react-helmet` + `Head` API on the same page → duplicate tags.
- `siteUrl` with a trailing slash → `//` in canonicals.
- Robots plugin defaulting to `disallow` on production because `resolveEnv` doesn't match the host's env var.
- `serialize` in the sitemap plugin stamping `new Date()` on every URL.
