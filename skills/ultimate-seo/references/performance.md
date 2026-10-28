# Performance & Core Web Vitals Reference

Page experience is a ranking signal (a tie-breaker more than a driver), but speed strongly affects conversions, crawl efficiency, and how much Google renders. Fix the big wins; don't chase a perfect Lighthouse score at the expense of shipping.

## Contents

1. The metrics and thresholds
2. Measuring: field vs lab
3. LCP — Largest Contentful Paint
4. INP — Interaction to Next Paint
5. CLS — Cumulative Layout Shift
6. Images
7. Fonts
8. JavaScript and third parties
9. Caching, compression, delivery
10. bfcache
11. Framework pointers
12. Quick-win checklist

---

## 1. The metrics and thresholds

Assessed on **field data at the 75th percentile** of page loads, split mobile/desktop, per URL group (origin-level if data is sparse).

| Metric | Good | Needs improvement | Poor | Measures |
|---|---|---|---|---|
| **LCP** | ≤ 2.5 s | ≤ 4.0 s | > 4.0 s | Loading — when the largest image/text block renders |
| **INP** | ≤ 200 ms | ≤ 500 ms | > 500 ms | Responsiveness — latency of interactions across the visit (replaced FID in **March 2024**) |
| **CLS** | ≤ 0.1 | ≤ 0.25 | > 0.25 | Visual stability — unexpected layout shifts |

Supporting (diagnostic, not CWV): TTFB (≤ 0.8 s good), FCP (≤ 1.8 s), TBT (lab proxy for INP).

Verify against current docs: https://web.dev/articles/vitals

---

## 2. Measuring: field vs lab

| Tool | Data | Use |
|---|---|---|
| Search Console → Core Web Vitals | Field (CrUX), URL groups | What Google actually uses; trends |
| PageSpeed Insights (pagespeed.web.dev) | Field (CrUX) + Lighthouse lab | Per-URL snapshot |
| CrUX dashboard / CrUX API / BigQuery | Field | Historical, origin-level |
| Lighthouse (DevTools, CLI `npx lighthouse URL`) | Lab | Debugging; throttled mobile emulation |
| Chrome DevTools Performance panel | Lab + live CWV overlay | Find the LCP element, long tasks, shift sources |
| `web-vitals` JS library | Your own RUM | Attribution builds pinpoint the slow element/interaction |
| WebPageTest | Lab, real devices, filmstrips | Deep waterfall analysis |

New sites have no CrUX data — rely on lab plus RUM. Lab scores ≠ field results: INP especially only shows up in field data.

RUM snippet:

```js
import { onLCP, onINP, onCLS } from 'web-vitals/attribution';
const send = (m) => navigator.sendBeacon('/analytics/vitals', JSON.stringify({ name: m.name, value: m.value, rating: m.rating, attribution: m.attribution }));
onLCP(send); onINP(send); onCLS(send);
```

---

## 3. LCP — Largest Contentful Paint

LCP = TTFB + resource load delay + resource load time + render delay. Find the LCP element first (DevTools → Performance → LCP marker, or PSI diagnostics).

Fixes by phase:

**TTFB** — cache HTML at the CDN/edge (SSG/ISR), avoid slow server waterfalls, reduce redirects, use HTTP/2+/3, `103 Early Hints` where supported.

**Load delay** (LCP image discovered late) — the image must be in initial HTML, not a CSS background or JS-inserted:

```html
<img src="/hero-1200.avif"
     srcset="/hero-640.avif 640w, /hero-1200.avif 1200w, /hero-2000.avif 2000w"
     sizes="(max-width: 768px) 100vw, 1200px"
     width="1200" height="630" alt="…"
     fetchpriority="high" decoding="async">
```

- **Never `loading="lazy"` on the LCP image.**
- `fetchpriority="high"` on the LCP image (framework: Next.js `priority`/`preload`, Nuxt `<NuxtImg preload>`, Astro `<Image loading="eager" fetchpriority="high">`).
- If it's a CSS background or discovered late: `<link rel="preload" as="image" href="…" imagesrcset="…" imagesizes="…" fetchpriority="high">`.
- Self-host or `preconnect` the LCP image's origin: `<link rel="preconnect" href="https://cdn.example.com" crossorigin>`.

**Load time** — right-size and compress (AVIF/WebP), serve from CDN, responsive `srcset`.

**Render delay** — remove render-blocking CSS/JS in `<head>`, inline critical CSS for large stylesheets, avoid client-side rendering of the hero, avoid A/B testing scripts that hide the page (anti-flicker snippets add seconds), don't fade-in hero text with JS.

Text LCP: ensure fonts don't block (see §7).

---

## 4. INP — Interaction to Next Paint

INP reports roughly the worst interaction latency (click/tap/key) during a visit: input delay + processing time + presentation delay.

Fixes:
- **Break up long tasks** (> 50 ms). Yield to the main thread between chunks:

```js
async function yieldToMain() {
  if (globalThis.scheduler?.yield) return scheduler.yield();
  return new Promise((r) => setTimeout(r, 0));
}

async function handleClick() {
  updateUIImmediately();      // cheap visual feedback first
  await yieldToMain();
  doExpensiveWork();          // analytics, filtering, state sync
}
```

- Give immediate visual feedback, defer non-visual work (analytics, logging) with `requestIdleCallback` / after yield.
- Reduce hydration cost: less client JS, server components / islands (React Server Components, Astro islands, Qwik), lazy-hydrate below-the-fold widgets.
- React: `useTransition`/`startTransition` for non-urgent updates, `useDeferredValue` for expensive filtered lists, memoize heavy renders, virtualize long lists (`@tanstack/react-virtual`).
- Avoid layout thrashing (read then write DOM, not interleaved). Keep DOM size reasonable (< ~1,500 nodes ideal).
- Debounce input handlers doing heavy work; move heavy computation to Web Workers.
- Audit third-party scripts (chat widgets, tag managers, heatmaps) — frequent INP culprits.
- `content-visibility: auto` on long off-screen sections reduces rendering work (pair with `contain-intrinsic-size` to avoid CLS):

```css
.article-section { content-visibility: auto; contain-intrinsic-size: auto 800px; }
```

---

## 5. CLS — Cumulative Layout Shift

Causes and fixes:
- **Images/video/iframes without dimensions** → always set `width`/`height` attributes (or CSS `aspect-ratio`). Responsive CSS `width:100%; height:auto` keeps the ratio.
- **Ads, embeds, cookie banners, late-injected banners** → reserve space (`min-height`) or overlay (fixed position) instead of pushing content.
- **Web fonts swapping** → metric-matched fallbacks (see §7).
- **Content inserted above existing content** after load (e.g. "Download our app" bar) → insert below, or reserve space, or only on user interaction (shifts within 500 ms of input are excluded).
- **Animations** → animate `transform`/`opacity`, not `top`/`height`/`margin`.
- SPAs: skeletons should match final dimensions.
- bfcache restores avoid shifts on back/forward (§10).

---

## 6. Images

- Formats: **AVIF** (best compression) → **WebP** fallback → JPEG/PNG. Use `<picture>` or an image CDN with `Accept` negotiation.

```html
<picture>
  <source type="image/avif" srcset="/img/a-800.avif 800w, /img/a-1600.avif 1600w" sizes="(max-width: 800px) 100vw, 800px">
  <source type="image/webp" srcset="/img/a-800.webp 800w, /img/a-1600.webp 1600w" sizes="(max-width: 800px) 100vw, 800px">
  <img src="/img/a-800.jpg" width="800" height="450" alt="…" loading="lazy" decoding="async">
</picture>
```

- `loading="lazy"` for below-the-fold images; eager + `fetchpriority="high"` for the LCP image.
- Correct `sizes` so the browser doesn't download desktop images on mobile.
- SVG for logos/icons; inline small critical SVGs.
- Descriptive filenames (`trail-runner-2-black.avif`) and `alt` text help image search.
- Use the framework image component (`next/image`, `astro:assets`, `@nuxt/image`, `@sveltejs/enhanced-img`, Angular `NgOptimizedImage`) — they handle srcset, dimensions and formats.

---

## 7. Fonts

- Self-host (or use the framework font helper: `next/font`, `@nuxt/fonts`, Astro fonts API, Fontsource). Avoids third-party connection cost and improves privacy.
- WOFF2 only; subset to used character sets (`unicode-range`).
- `font-display: swap` (body text) or `optional` (if you'd rather never shift).
- Preload only the 1–2 fonts used above the fold: `<link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>`.
- Prevent CLS from swaps with metric-matched fallbacks:

```css
@font-face {
  font-family: "Inter Fallback";
  src: local("Arial");
  size-adjust: 107%;
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}
body { font-family: "Inter", "Inter Fallback", system-ui, sans-serif; }
```

(`next/font` and Fontaine/`@nuxt/fonts` generate these automatically.)
- Prefer variable fonts over many static weights; limit families to 2.

---

## 8. JavaScript and third parties

- Ship less JS: code-split by route, dynamic `import()` for heavy, below-the-fold or interaction-only components, tree-shake, replace heavy libraries (moment → date-fns/Temporal, lodash → native).
- `defer` or `type="module"` on scripts; never synchronous scripts in `<head>` unless critical.
- Third parties: load after interaction or idle; use **facades** for embeds (YouTube via `lite-youtube-embed`, chat widgets that load on click, maps as static image until clicked).
- Tag managers: audit tags quarterly; server-side tagging moves work off the client.
- Partytown can move some third-party scripts to a Web Worker (test carefully).
- Analyse bundles: `npx vite-bundle-visualizer`, `@next/bundle-analyzer`, `source-map-explorer`.
- `<link rel="preconnect">` for critical third-party origins (max ~3–4), `dns-prefetch` for others.
- Speculation Rules API for near-instant navigations (Chromium):

```html
<script type="speculationrules">
{ "prerender": [{ "where": { "href_matches": "/*" }, "eagerness": "moderate" }] }
</script>
```

---

## 9. Caching, compression, delivery

- CDN in front of everything; HTML cached at edge where possible (SSG, ISR, `stale-while-revalidate`).
- Hashed static assets: `Cache-Control: public, max-age=31536000, immutable`.
- HTML: `Cache-Control: public, max-age=0, must-revalidate` (or `s-maxage=…, stale-while-revalidate=…` for CDN caching).
- Compression: Brotli (fallback gzip) for text; zstd where supported.
- HTTP/2 or HTTP/3; TLS 1.3.
- Avoid redirect chains for the first navigation (e.g. `http → https → www → /en/`).
- `ETag`/`Last-Modified` for conditional requests (also helps crawl budget).

---

## 10. bfcache

Back/forward cache makes back navigations instant (and free for CWV). Blockers:
- `Cache-Control: no-store` on HTML (avoid unless page has sensitive data).
- `unload` event listeners (use `pagehide` instead).
- Open `WebSocket`/`BroadcastChannel`/IndexedDB transactions when navigating away — close on `pagehide`.
- `window.opener` references.

Check: DevTools → Application → Back/forward cache → Test.

---

## 11. Framework pointers

| Stack | Levers |
|---|---|
| Next.js | `next/image` with `priority`/`preload` on LCP, `next/font`, Server Components to cut client JS, `next/script` `strategy="lazyOnload"`, static/ISR rendering, `@next/bundle-analyzer` |
| React SPA (Vite) | Prerender public routes, route-level `lazy()`, `vite-imagetools`, `rollup-plugin-visualizer`, avoid hydrating huge trees |
| Astro | Islands (`client:visible`/`client:idle`), `astro:assets` `<Image>`/`<Picture>`, zero JS by default, prefetch |
| Nuxt | `@nuxt/image`, `@nuxt/fonts`, `@nuxt/scripts` (facades, idle loading), lazy components (`Lazy` prefix), hybrid rendering route rules |
| SvelteKit | Prerender, `@sveltejs/enhanced-img`, `data-sveltekit-preload-data`, small runtime |
| Angular | `NgOptimizedImage` (`priority`), SSR + incremental hydration (`@defer` with hydrate triggers), zoneless change detection |
| Gatsby | `gatsby-plugin-image`, Partytown integration, Head API |
| Remix / React Router | Streaming with `defer`/Suspense, `links` for preloads, `prefetch="intent"` on `Link` |
| WordPress | Caching plugin + CDN, image optimization (AVIF/WebP), remove unused plugins, lightweight theme |
| Static HTML / SSGs | Hand-optimize hero, minify, `<picture>`, CDN hosting |

---

## 12. Quick-win checklist

- [ ] LCP element identified; eager-loaded, `fetchpriority="high"`, right-sized, AVIF/WebP, in initial HTML.
- [ ] No `loading="lazy"` above the fold; lazy below.
- [ ] Every `<img>`, `<video>`, `<iframe>` has width/height or aspect-ratio.
- [ ] Fonts self-hosted, WOFF2, `font-display: swap`, metric-matched fallback, ≤ 2 preloads.
- [ ] No render-blocking third-party scripts in `<head>`; embeds behind facades.
- [ ] Long tasks broken up; heavy handlers yield; analytics deferred.
- [ ] Hashed assets immutable-cached; HTML cached at edge where possible; Brotli on.
- [ ] No `unload` listeners; no `no-store` on public HTML.
- [ ] Field monitoring in place (Search Console CWV report + `web-vitals` RUM).
