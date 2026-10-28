# Angular

Without SSR, an Angular app is a client-rendered SPA (`<app-root></app-root>` and nothing else in the HTML) — all of `react-spa.md`'s crawler caveats apply. The fix is Angular's own SSR/prerendering (`@angular/ssr`), plus the `Title`/`Meta` services and a small SEO service for canonical and JSON-LD.

## Contents

1. Detect
2. Where things go
3. Site config
4. Enable SSR / prerendering
5. SEO service (title, meta, canonical, JSON-LD)
6. Route-level titles and data
7. 404 status
8. robots.txt, sitemap, llms.txt, icons
9. Structured data
10. Performance
11. Verify
12. Pitfalls

## 1. Detect

- `angular.json`, `@angular/core` in dependencies. Version decides APIs: **17+** standalone + application builder; **19+** server routing (`app.routes.server.ts`, `RenderMode`), `outputMode`; **≤16** NgModules, `@nguniversal/express-engine`.
- SSR present if `@angular/ssr` is installed and `server.ts` / `src/main.server.ts` exist; `angular.json` build options contain `"server"`, `"ssr"`, `"prerender"` or `"outputMode"`.
- Hash routing (`withHashLocation()` / `useHash: true`) must go for any indexable site.

## 2. Where things go

| Concern | File |
|---|---|
| Site config | `src/environments/environment*.ts` or `src/app/site.config.ts` |
| SEO service | `src/app/core/seo.service.ts` |
| Default tags, `lang` | `src/index.html` |
| Route titles/meta | `app.routes.ts` `title` + `data`, custom `TitleStrategy` |
| SSR/prerender config | `angular.json`, `app.routes.server.ts` (19+), `server.ts` |
| robots.txt, llms.txt, icons, manifest | `public/` (17+; `src/assets` / `src/` in older apps — check `angular.json` `assets`) |
| Sitemap | build script → `dist/<app>/browser/sitemap.xml`, or an Express route in `server.ts` |

## 3. Site config

```ts
// src/app/site.config.ts
export const SITE = {
  name: "Acme",
  url: "https://www.example.com", // replaced per environment via fileReplacements, or read from environment.ts
  description: "Acme helps small teams ship invoices in minutes.",
  ogImage: "/og.png",
  twitter: "@acme",
  locale: "en_US",
} as const;
```

## 4. Enable SSR / prerendering

```bash
ng add @angular/ssr
```

**Angular 19+** — choose per route in `src/app/app.routes.server.ts`:

```ts
import { RenderMode, ServerRoute } from "@angular/ssr";
import { inject } from "@angular/core";
import { PostService } from "./blog/post.service";

export const serverRoutes: ServerRoute[] = [
  { path: "", renderMode: RenderMode.Prerender },
  { path: "pricing", renderMode: RenderMode.Prerender },
  {
    path: "blog/:slug",
    renderMode: RenderMode.Prerender,
    async getPrerenderParams() {
      const posts = await inject(PostService).listSlugs();
      return posts.map((slug) => ({ slug }));
    },
  },
  { path: "app/**", renderMode: RenderMode.Client }, // logged-in area, noindex
  { path: "**", renderMode: RenderMode.Server, status: 404 },
];
```

With `"outputMode": "static"` in `angular.json` the build emits only static HTML (no Node server); `"server"` keeps a Node server for `RenderMode.Server` routes.

**Angular 17–18** — `angular.json` `"prerender": { "routesFile": "routes.txt" }` (one path per line) or `"prerender": true` for discovered static routes; SSR via `server.ts`.

**≤16** — `@nguniversal/express-engine`; recommend upgrading (Universal is EOL).

## 5. SEO service

```ts
// src/app/core/seo.service.ts
import { Injectable, inject, DOCUMENT } from "@angular/core"; // Angular <20: import { DOCUMENT } from "@angular/common"
import { Meta, Title } from "@angular/platform-browser";
import { SITE } from "../site.config";

export interface PageSeo { title?: string; description?: string; path: string; image?: string; type?: "website" | "article"; noindex?: boolean; jsonLd?: object | object[]; }

@Injectable({ providedIn: "root" })
export class SeoService {
  private title = inject(Title);
  private meta = inject(Meta);
  private doc = inject(DOCUMENT);

  set(p: PageSeo) {
    const url = new URL(p.path, SITE.url).toString();
    const image = new URL(p.image ?? SITE.ogImage, SITE.url).toString();
    const description = p.description ?? SITE.description;
    this.title.setTitle(p.title ? `${p.title} | ${SITE.name}` : SITE.name);
    const tags: Array<[string, string, string]> = [
      ["name", "description", description],
      ["name", "robots", p.noindex ? "noindex, follow" : "index, follow"],
      ["property", "og:type", p.type ?? "website"],
      ["property", "og:site_name", SITE.name],
      ["property", "og:title", p.title ?? SITE.name],
      ["property", "og:description", description],
      ["property", "og:url", url],
      ["property", "og:image", image],
      ["name", "twitter:card", "summary_large_image"],
    ];
    for (const [attr, key, content] of tags) this.meta.updateTag({ [attr]: key, content }, `${attr}="${key}"`);
    this.setCanonical(url);
    this.setJsonLd(p.jsonLd);
  }

  private setCanonical(url: string) {
    let link = this.doc.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (!link) { link = this.doc.createElement("link"); link.rel = "canonical"; this.doc.head.appendChild(link); }
    link.href = url;
  }

  private setJsonLd(data?: object | object[]) {
    this.doc.head.querySelectorAll('script[data-seo="jsonld"]').forEach((el) => el.remove());
    if (!data) return;
    const s = this.doc.createElement("script");
    s.type = "application/ld+json";
    s.setAttribute("data-seo", "jsonld");
    s.textContent = JSON.stringify(data).replace(/</g, "\\u003c");
    this.doc.head.appendChild(s);
  }
}
```

`DOCUMENT` is exported from `@angular/core` since v20 (still re-exported from `@angular/common`). Using `DOCUMENT` (not `document`) keeps this working during SSR, so the tags land in the server HTML.

Use it in a component (from resolved data, so it runs before render completes on the server):

```ts
export class PostPage {
  private seo = inject(SeoService);
  post = input.required<Post>(); // via withComponentInputBinding() + resolver
  constructor() {
    effect(() => {
      const p = this.post();
      this.seo.set({ title: p.title, description: p.excerpt, path: `/blog/${p.slug}`, type: "article",
        jsonLd: { "@context": "https://schema.org", "@type": "BlogPosting", headline: p.title, datePublished: p.publishedAt } });
    });
  }
}
```

## 6. Route-level titles

```ts
// app.routes.ts
export const routes: Routes = [
  { path: "", component: HomePage, title: "Invoicing for small teams" },
  { path: "pricing", component: PricingPage, title: "Pricing", data: { description: "Simple plans from $0..." } },
  { path: "blog/:slug", component: PostPage, resolve: { post: postResolver } },
  { path: "**", component: NotFoundPage, title: "Page not found" },
];
```

A custom `TitleStrategy` (`provide: TitleStrategy, useClass: SeoTitleStrategy`) can call `SeoService.set()` for every navigation using `title` + `data.description` + the router URL, so static pages need no per-component code.

## 7. 404 status

- Angular 19+: `status: 404` on the `**` server route (above), or inject `RESPONSE_INIT` in `NotFoundPage` and set `status = 404` when rendering on the server.
- Older SSR: inject the Express `RESPONSE` token provided in `server.ts` and call `res.status(404)`.
- Prerender-only/static hosting: emit a `404.html` and configure the host; add `noindex` meta in `NotFoundPage`.

## 8. robots.txt, sitemap, llms.txt, icons

- `public/robots.txt`, `public/llms.txt`, icons and `manifest.webmanifest` (templates in `assets/`). Ensure `angular.json` `assets` includes them (default `public/**` in 17+).
- Sitemap: after `ng build`, run `python3 <skill-dir>/scripts/generate_sitemap.py dist/<app>/browser --base-url https://www.example.com` for prerendered output, or add a postbuild Node script that reads the same slug source used by `getPrerenderParams`. For SSR-only dynamic content, add an Express route in `server.ts` before the Angular handler: `app.get("/sitemap.xml", async (req, res) => { res.type("application/xml").send(await buildSitemap()); })`.

## 9. Structured data

Via `SeoService.set({ jsonLd })`. Site-wide `Organization` + `WebSite` can live statically in `src/index.html`. Templates: `assets/jsonld/`.

## 10. Performance

- `NgOptimizedImage` (`<img ngSrc>`) with `priority` on the LCP image; `width`/`height` required (prevents CLS).
- Hydration: `provideClientHydration(withEventReplay())` (default in new SSR apps) avoids re-render flash; incremental hydration (`@defer (hydrate on viewport)`) in 19+ cuts JS on long pages.
- `@defer` blocks for below-the-fold widgets.
- Inline critical CSS is on by default with SSR builds; keep global styles lean.

## 11. Verify

```bash
ng build
ls dist/*/browser/**/index.html | head          # prerendered pages exist
python3 <skill-dir>/scripts/seo_audit.py dist/<app>/browser
npm run serve:ssr:<app> &                      # SSR server, usually :4000
python3 <skill-dir>/scripts/seo_audit.py http://localhost:4000 --crawl 50
curl -s http://localhost:4000/pricing | grep -iE "<title>|canonical|og:title"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:4000/nope   # 404
```

## 12. Pitfalls

- Setting tags in `ngAfterViewInit` or after an async call that isn't awaited by SSR → missing from server HTML.
- `Meta.addTag` on every navigation → duplicates; use `updateTag` with a selector.
- Using the global `document`/`window` in services breaks SSR.
- Prerendered app with a catch-all `**` client route on a host that serves `index.html` for everything → soft 404s.
