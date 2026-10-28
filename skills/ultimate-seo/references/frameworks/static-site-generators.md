# Static Site Generators: Hugo, Jekyll, Eleventy, Docusaurus, VitePress, MkDocs

SSGs output plain HTML, so crawlability is solved. The work is configuring the base URL correctly, using each tool's built-in sitemap/SEO features instead of reinventing them, and making per-page metadata flow from frontmatter. Find the section for the detected tool; the head checklist in `static-html.md` is the target output for all of them.

## Contents
- Detect (all)
- Shared approach: frontmatter → metadata
- Hugo
- Jekyll
- Eleventy (11ty)
- Docusaurus
- VitePress
- MkDocs (Material)
- Structured data (all)
- Verify (all)
- Pitfalls (all)

## Detect (all)

| Tool | Signals | Output dir |
|---|---|---|
| Hugo | `hugo.toml`/`hugo.yaml`/`config.toml`, `layouts/`, `content/` | `public/` |
| Jekyll | `_config.yml`, `Gemfile` with `jekyll`, `_layouts/`, `_posts/` | `_site/` |
| Eleventy | `@11ty/eleventy` in package.json, `eleventy.config.js`/`.eleventy.js` | `_site/` |
| Docusaurus | `@docusaurus/core`, `docusaurus.config.(js|ts)` | `build/` |
| VitePress | `vitepress` dep, `.vitepress/config.(ts|mts|js)` | `.vitepress/dist/` |
| MkDocs | `mkdocs.yml` (+ `mkdocs-material` in requirements) | `site/` |

## Shared approach: frontmatter → metadata

Every content file should support `title`, `description`, optional `image`, `noindex`, `canonical` (rare override), and for posts `date`/`lastmod`/`author`. Layouts read them with site-level defaults as fallback. Write the expected frontmatter fields into the per-page checklist of `ULTIMATE-SEO.md`.

## Hugo

**Site config** (`hugo.toml`):

```toml
baseURL = "https://www.example.com/"
languageCode = "en-us"
title = "Example"
enableRobotsTXT = true

[params]
  description = "Default description, ~150 chars."
  images = ["og-default.png"]        # used by the internal opengraph template
  [params.social]
    twitter = "example"               # only if real

[sitemap]
  changeFreq = ""
  priority = -1
  filename = "sitemap.xml"

[taxonomies]
  tag = "tags"
  category = "categories"
```

Hugo ≥0.120 also accepts `[params.social]`; older themes used `[social]`. Check the version: `hugo version`.

**Head partial** (`layouts/partials/head-seo.html`, include from `baseof.html`):

```go-html-template
{{ $title := cond .IsHome site.Title (printf "%s · %s" .Title site.Title) }}
{{ $desc := .Description | default .Summary | default site.Params.description | plainify | truncate 160 }}
<title>{{ $title }}</title>
<meta name="description" content="{{ $desc }}">
<link rel="canonical" href="{{ .Permalink }}">
{{ if or .Params.noindex (eq .Kind "taxonomy") }}<meta name="robots" content="noindex, follow">{{ end }}
{{ partial "opengraph.html" . }}      {{/* newer Hugo; older: template "_internal/opengraph.html" . */}}
{{ partial "twitter_cards.html" . }}
{{ partial "schema.html" . }}
{{ range .AllTranslations }}<link rel="alternate" hreflang="{{ .Language.LanguageCode }}" href="{{ .Permalink }}">{{ end }}
```

The embedded templates `opengraph.html`, `twitter_cards.html`, `schema.html` read `images`, `description`, `date`, `lastmod`. Newer Hugo (the v0.146+ template system) calls them as `{{ partial "opengraph.html" . }}`; older versions use `{{ template "_internal/opengraph.html" . }}` (still supported for a while). Run `hugo version` and verify which form builds without warnings. The internal `schema.html` emits microdata `<meta itemprop>` — prefer adding your own JSON-LD partial (below) for rich results.

**robots.txt**: with `enableRobotsTXT = true`, override `layouts/robots.txt`:

```go-html-template
User-agent: *
Allow: /
Sitemap: {{ "sitemap.xml" | absURL }}
```

**Sitemap**: built-in at `/sitemap.xml` (or a sitemap index per language). Exclude pages with frontmatter `sitemap: { disable: true }` (Hugo ≥0.125) or override `layouts/_default/sitemap.xml`. `lastmod` comes from frontmatter or `enableGitInfo = true` (recommended — real dates from git).

**OG images**: per-page `images: ["/img/post.png"]` in frontmatter; site default from `params.images`.

## Jekyll

```yaml
# _config.yml
url: "https://www.example.com"   # no trailing slash
baseurl: ""                       # subpath if on github.io/project
title: Example
description: Default description, ~150 chars.
lang: en_US
logo: /assets/logo.png
image: /assets/og-default.png
twitter:
  username: example
  card: summary_large_image
social:
  name: Example
  links:
    - https://github.com/example
plugins:
  - jekyll-seo-tag
  - jekyll-sitemap
  - jekyll-feed
```

`Gemfile`: add `gem "jekyll-seo-tag"`, `gem "jekyll-sitemap"`, `gem "jekyll-feed"` in the `:jekyll_plugins` group. GitHub Pages supports all three natively.

Layout `<head>`: `{% seo %}` (outputs title, description, canonical, OG, Twitter, JSON-LD for `WebSite`/`BlogPosting`/`Organization`). Remove any hand-written `<title>`/OG tags it would duplicate. Per page: `title`, `description`, `image`, `author`, `last_modified_at`. Exclude from sitemap with `sitemap: false`.

`robots.txt` at the root with frontmatter so Liquid runs:

```
---
layout: null
sitemap: false
---
User-agent: *
Allow: /
Sitemap: {{ "/sitemap.xml" | absolute_url }}
```

`jekyll-seo-tag` puts `Organization` with `logo` only when `logo` is set; `social.links` becomes `sameAs`.

## Eleventy (11ty)

v3 is ESM (`eleventy.config.js` with `export default`). Site data in `_data/site.js`:

```js
// _data/site.js
export default {
  url: process.env.SITE_URL || 'https://www.example.com',
  name: 'Example',
  description: 'Default description, ~150 chars.',
  ogImage: '/og-default.png',
  locale: 'en_US',
};
```

`eleventy.config.js`:

```js
export default function (eleventyConfig) {
  eleventyConfig.addFilter('absoluteUrl', (path, base) => new URL(path, base).href);
  eleventyConfig.addPassthroughCopy({ 'src/static': '/' }); // robots, llms.txt, icons
}
```

(`@11ty/eleventy-plugin-rss` also ships an `absoluteUrl` filter.) Head in `_includes/layouts/base.njk`:

```njk
{% set pageTitle = (title + ' · ' + site.name) if title else site.name %}
<title>{{ pageTitle }}</title>
<meta name="description" content="{{ description or site.description }}">
<link rel="canonical" href="{{ page.url | absoluteUrl(site.url) }}">
{% if noindex %}<meta name="robots" content="noindex, follow">{% endif %}
<meta property="og:title" content="{{ title or site.name }}">
<meta property="og:description" content="{{ description or site.description }}">
<meta property="og:url" content="{{ page.url | absoluteUrl(site.url) }}">
<meta property="og:image" content="{{ (image or site.ogImage) | absoluteUrl(site.url) }}">
<meta name="twitter:card" content="summary_large_image">
```

Sitemap template `src/sitemap.njk`:

```njk
---
permalink: /sitemap.xml
eleventyExcludeFromCollections: true
---
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{%- for p in collections.all %}{% if not p.data.noindex and not p.data.eleventyExcludeFromCollections %}
  <url><loc>{{ p.url | absoluteUrl(site.url) }}</loc><lastmod>{{ p.date.toISOString().slice(0,10) }}</lastmod></url>
{%- endif %}{% endfor %}
</urlset>
```

Use `date: git Last Modified` in frontmatter/directory data so `p.date` is meaningful (otherwise it's file creation time). Also `robots.njk` with `permalink: /robots.txt`. Put shared defaults in directory data files (`posts/posts.11tydata.js` → `layout`, `type: 'article'`).

## Docusaurus

```ts
// docusaurus.config.ts
const config = {
  url: 'https://docs.example.com',
  baseUrl: '/',
  title: 'Example Docs',
  tagline: 'One-line description',
  trailingSlash: false,             // set explicitly; match host behavior
  favicon: 'img/favicon.ico',
  presets: [['classic', {
    sitemap: { lastmod: 'date', changefreq: null, priority: null, ignorePatterns: ['/tags/**'] },
    docs: { showLastUpdateTime: true },
    blog: { showReadingTime: true },
  }]],
  themeConfig: {
    image: 'img/og-default.png',     // default og:image / twitter:image
    metadata: [{ name: 'twitter:card', content: 'summary_large_image' }],
  },
  headTags: [
    { tagName: 'script', attributes: { type: 'application/ld+json' },
      innerHTML: JSON.stringify({ '@context': 'https://schema.org', '@type': 'Organization', name: 'Example', url: 'https://example.com', logo: 'https://docs.example.com/img/logo.png' }) },
  ],
};
export default config;
```

Sitemap plugin is in `preset-classic`; `lastmod: 'date'` needs `showLastUpdateTime` (git history; in CI use `fetch-depth: 0`). Per-doc frontmatter: `title`, `description`, `image`, `keywords` (used only by Algolia, harmless), `slug`. Per-page extra tags: `<head>` in MDX. `headTags` requires Docusaurus ≥3.0. `static/robots.txt` and `static/llms.txt` are copied to root (community plugin `docusaurus-plugin-llms` can generate llms.txt from docs).

## VitePress

```ts
// .vitepress/config.mts
import { defineConfig } from 'vitepress'
const SITE = 'https://docs.example.com'

export default defineConfig({
  lang: 'en-US',
  title: 'Example',
  titleTemplate: ':title · Example',
  description: 'Default description, ~150 chars.',
  cleanUrls: true,
  lastUpdated: true,
  sitemap: { hostname: SITE },
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['meta', { property: 'og:site_name', content: 'Example' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
  ],
  transformPageData(pageData) {
    const path = pageData.relativePath.replace(/(index)?\.md$/, '').replace(/\.md$/, '')
    const url = `${SITE}/${path}`
    pageData.frontmatter.head ??= []
    pageData.frontmatter.head.push(
      ['link', { rel: 'canonical', href: url }],
      ['meta', { property: 'og:url', content: url }],
      ['meta', { property: 'og:title', content: pageData.frontmatter.title || pageData.title }],
      ['meta', { property: 'og:description', content: pageData.frontmatter.description || pageData.description }],
      ['meta', { property: 'og:image', content: `${SITE}${pageData.frontmatter.image || '/og-default.png'}` }],
    )
  },
})
```

`transformHead` is the alternative hook (runs at build per page, returns extra head entries). Static files (`robots.txt`, `llms.txt`) go in `docs/public/`. With `cleanUrls: true`, ensure the host serves extensionless URLs (Netlify/Vercel do).

## MkDocs (Material)

```yaml
# mkdocs.yml
site_name: Example Docs
site_url: https://docs.example.com/     # required for sitemap + canonical
site_description: Default description, ~150 chars.
theme:
  name: material
  features: [navigation.instant]        # keeps real <a> links; content is still static HTML
plugins:
  - search
  - social                               # Material: generates OG cards (needs Cairo deps)
  - git-revision-date-localized:
      enable_creation_date: true
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/example
```

MkDocs builds `sitemap.xml` automatically when `site_url` is set, and Material emits canonical links. Per page: frontmatter `title`, `description`. Custom head/JSON-LD: override `main.html` in `overrides/` (`theme.custom_dir: overrides`) and extend `{% block extrahead %}`. `docs/robots.txt` copies to root.

## Structured data (all)

- Home: `Organization` + `WebSite` (assets/jsonld).
- Posts: `BlogPosting` with `datePublished`/`dateModified`/`author` from frontmatter.
- Docs: `TechArticle` or `Article` is optional; `BreadcrumbList` from the sidebar hierarchy is more useful.
- Emit via a head partial/include fed by frontmatter; escape `<` in JSON strings (Hugo: `jsonify` handles it; Nunjucks: `| dump | safe`; Liquid: `| jsonify`).

## Verify (all)

```bash
hugo --minify && python3 <skill-dir>/scripts/seo_audit.py public
bundle exec jekyll build && python3 <skill-dir>/scripts/seo_audit.py _site
npx @11ty/eleventy && python3 <skill-dir>/scripts/seo_audit.py _site
npm run build && python3 <skill-dir>/scripts/seo_audit.py build                 # Docusaurus
npx vitepress build docs && python3 <skill-dir>/scripts/seo_audit.py docs/.vitepress/dist
mkdocs build && python3 <skill-dir>/scripts/seo_audit.py site
python3 <skill-dir>/scripts/validate_jsonld.py <output-dir>
grep -c '<loc>' <output-dir>/sitemap.xml
```

## Pitfalls (all)

- `baseURL`/`url`/`site_url` left as `localhost` or `example.org` — every canonical and sitemap URL is wrong. Check the built output.
- Shallow CI clones (`fetch-depth: 1`) make git-based `lastmod` equal to the build date for every page.
- Tag/category archives with one or two posts indexed — thin pages; noindex or exclude them.
- Themes that already emit OG/Twitter tags + your partial → duplicates. Grep the built HTML for `og:title` counts.
- Project sites on `user.github.io/project/` need `baseurl`/`baseUrl` set or every asset and canonical breaks.
