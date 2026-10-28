# Launch, Monitoring & Migrations

Everything after the code ships: getting the site discovered, measuring it, keeping it healthy, and moving it safely. Most items here are human steps — they belong in the "Launch checklist" and "Monitoring" sections of ULTIMATE-SEO.md, made specific to the project.

## Contents

1. Pre-launch checklist
2. Google Search Console
3. Bing Webmaster Tools and IndexNow
4. Analytics
5. Rank tracking and visibility tools
6. Uptime, errors and performance monitoring
7. Monitoring cadence (weekly / monthly / quarterly)
8. Site migration and redesign runbook
9. What to expect: timelines
10. KPIs
11. Playbook items for ULTIMATE-SEO.md

---

## 1. Pre-launch checklist

Run before any production launch or major release:

- [ ] Production does **not** send `noindex` (meta robots or `X-Robots-Tag`) and robots.txt does not `Disallow: /`. Staging/preview **does** (or is behind auth). This is the #1 launch disaster — check both environments.
- [ ] One canonical host: `http→https` and `www↔apex` 301 redirects in place; HSTS enabled.
- [ ] Canonical tags use the production origin (not localhost, staging, or preview URLs). Check env var `SITE_URL`/equivalent is set in production.
- [ ] `/robots.txt`, `/sitemap.xml` (or index), `/llms.txt`, manifest, favicons return 200 with correct content types.
- [ ] Sitemap only contains canonical 200 URLs; sitemap URLs use the production origin.
- [ ] 404 page returns status 404; unknown routes don't return 200 (soft 404). Check SPA catch-all routes.
- [ ] Redirects from any old URLs (see §8).
- [ ] Unique titles/descriptions on key templates; OG images render (test with a social debugger).
- [ ] Structured data validates (`validate_jsonld.py`, Rich Results Test https://search.google.com/test/rich-results, Schema Markup Validator https://validator.schema.org).
- [ ] Core Web Vitals in lab (Lighthouse/PageSpeed Insights) within targets on mobile for home + key templates.
- [ ] Analytics installed and consent banner (if required) doesn't block content rendering.
- [ ] Final `seo_audit.py` run against production URL.

## 2. Google Search Console

https://search.google.com/search-console

**Setup (owner action):**
1. Add a **Domain property** (covers all protocols and subdomains) — verified via a DNS TXT record at the domain registrar/DNS host. Add URL-prefix properties too if teams need scoped access.
2. Add team members with appropriate permissions (Owner/Full/Restricted).
3. **Submit the sitemap** (Sitemaps → enter `sitemap.xml` or the index URL). Confirm status "Success" and discovered URL count.
4. Link GSC to GA4 (GA4 Admin → Product links → Search Console).

**Key reports and how to use them:**
- **Performance**: clicks, impressions, CTR, position by query/page/country/device. Primary SEO KPI source. Compare date ranges; filter by page to diagnose drops.
- **URL Inspection**: see Google's indexed version, render screenshot, canonical chosen by Google vs. user-declared; "Request indexing" for important new/changed pages (rate-limited — don't spam).
- **Pages (Indexing)**: why URLs aren't indexed. Key statuses:
  - *Discovered – currently not indexed*: Google knows the URL but hasn't crawled — often crawl budget or low perceived value/internal links.
  - *Crawled – currently not indexed*: crawled but judged not worth indexing — usually quality/duplication. Improve content or consolidate.
  - *Duplicate, Google chose different canonical than user*: canonical signals conflict.
  - *Excluded by 'noindex'*, *Blocked by robots.txt*, *Soft 404*, *Not found (404)*, *Page with redirect*: verify these are intentional.
- **Core Web Vitals**: field data (CrUX) grouped by URL pattern; mobile and desktop. Needs enough traffic to populate.
- **HTTPS**, **Enhancements** (rich result types detected and their errors: Breadcrumbs, Products, Review snippets, etc.), **Manual actions**, **Security issues**, **Links** (top linked pages, linking sites, anchor text), **Crawl stats** (Settings → Crawl stats: response codes, host issues, crawl requests).
- **Removals**: temporary emergency removal of URLs (6 months) — not a substitute for noindex/404.

Data lag ~2–3 days; Performance data retained 16 months — export monthly to keep history (or use the BigQuery bulk export).

## 3. Bing Webmaster Tools and IndexNow

https://www.bing.com/webmasters

- **Import sites from Google Search Console** for one-click verification and sitemap import.
- Bing powers Bing, DuckDuckGo (partially), Yahoo, Ecosia and feeds into some AI assistants (e.g. Copilot; ChatGPT search has used Bing among other sources) — worth the 5 minutes. Verify current partnerships against current docs.
- Reports: Search performance, URL inspection, Site Explorer, SEO reports, backlinks, keyword research.

**IndexNow** (https://www.indexnow.org): a protocol to instantly notify participating search engines (Bing, Yandex, Seznam, Naver and others; Google does **not** participate as of this writing — verify against current docs) when URLs are added, updated, or deleted.
1. Generate a key; host it at `https://example.com/{key}.txt` containing the key.
2. On publish/update/delete, POST URLs:
   ```bash
   curl -X POST "https://api.indexnow.org/indexnow" \
     -H "Content-Type: application/json; charset=utf-8" \
     -d '{"host":"example.com","key":"YOUR_KEY","keyLocation":"https://example.com/YOUR_KEY.txt","urlList":["https://example.com/new-page"]}'
   ```
3. Many platforms have built-in support or plugins: Cloudflare (Crawler Hints), WordPress (Yoast, Rank Math, IndexNow plugin), Wix, Duda. For custom sites, add a deploy hook or CMS webhook that submits changed URLs.

Add IndexNow when content changes frequently (news, e-commerce inventory, marketplaces); low value for a 10-page site.

## 4. Analytics

Pick one primary analytics tool and set it up properly:
- **Google Analytics 4**: free, deep integration with GSC and Ads; heavier script; consent requirements in EU/UK (Consent Mode v2).
- **Privacy-friendly alternatives**: Plausible, Fathom, Simple Analytics, Umami (self-host), Matomo (self-host or cloud), Pirsch. Lightweight, often cookieless.
- **Vercel/Netlify/Cloudflare Web Analytics**: zero-config for sites on those platforms.

Must-haves:
- Organic search segment (channel = Organic Search) and landing-page report.
- **Conversions/key events** defined: signups, purchases, leads, contact form submissions, calls (click-to-call), demo bookings. SEO value = organic conversions, not just sessions.
- Load scripts async/deferred; avoid tag-manager bloat hurting INP/LCP.
- Annotate (or keep a changelog of) major site changes and Google core updates to explain trend shifts.

## 5. Rank tracking and visibility tools

- **Free**: GSC Performance (average position per query — the ground truth for your own site), Bing WMT.
- **Paid rank trackers**: Ahrefs, Semrush, SE Ranking, AccuRanker, Wincher, Nightwatch — daily rankings by location/device, competitor tracking, SERP features.
- **Local rank grids**: BrightLocal, Local Falcon, Places Scout — map-pack position across a geographic grid.
- **AI visibility**: emerging tools track brand mentions/citations in ChatGPT, Perplexity, Google AI Overviews/AI Mode, Copilot (e.g. Semrush AI toolkit, Ahrefs Brand Radar, Profound, Peec AI, Otterly). Also check referrals from `chatgpt.com`, `perplexity.ai`, `copilot.microsoft.com`, `gemini.google.com` in analytics. See `ai-search.md`.
- Site crawlers for technical audits: Screaming Frog (free ≤500 URLs), Sitebulb, Ahrefs/Semrush site audit, and this skill's `seo_audit.py --crawl`.

Track 20–100 priority keywords mapped to target pages — not thousands of vanity terms.

## 6. Uptime, errors and performance monitoring

- **Uptime**: UptimeRobot, Better Stack, Pingdom, Checkly — alert on downtime and on robots.txt/sitemap returning non-200. Extended 5xx errors cause Google to slow crawling and eventually drop URLs.
- **Errors**: Sentry or equivalent for client/server errors (broken rendering = broken SEO).
- **Real-user performance**: CrUX (via PageSpeed Insights / GSC CWV report / CrUX dashboard), `web-vitals` library sending to analytics, Vercel Speed Insights, Cloudflare Web Analytics, DebugBear, SpeedCurve.
- **Change detection for SEO-critical files**: alert if `robots.txt` changes or a `noindex` appears on key pages (ContentKing/Conductor Monitoring, Little Warden, or a simple CI/cron check: `curl -s https://example.com/robots.txt | grep -q "Disallow: /$" && alert`).
- Consider adding `seo_audit.py` to CI against a preview deployment to block regressions (missing titles, canonicals, noindex).

## 7. Monitoring cadence

**Weekly (15 min)**
- GSC Performance: clicks/impressions vs previous period; any sudden drops by page.
- GSC Pages report: new spikes in not-indexed/errors; manual actions/security issues (email alerts on).
- Uptime and 5xx alerts reviewed.
- New content published → submitted/linked internally; IndexNow pinged if used.

**Monthly (1–2 h)**
- Top landing pages and conversions from organic (analytics).
- Queries in positions 4–15 with high impressions → optimization targets (titles, content, internal links).
- Core Web Vitals report (field data) for regressions.
- Enhancements/rich result errors.
- New backlinks and lost backlinks (GSC Links, Ahrefs/Semrush).
- Local: GBP performance, reviews responded to, photos/posts added.
- Export GSC data for long-term history.

**Quarterly (half day)**
- Full crawl (`seo_audit.py --crawl` / Screaming Frog): broken links, redirect chains, orphan pages, duplicate titles, canonical issues.
- Content refresh/prune cycle (see `content-strategy.md` §9).
- Competitor review: who gained, which content types they're winning with.
- Revisit keyword map and roadmap; update ULTIMATE-SEO.md.
- Review robots.txt AI-crawler policy against new bots/policies.
- Check Google Search Central blog for core updates and policy changes: https://developers.google.com/search/blog and Google Search Status Dashboard https://status.search.google.com

## 8. Site migration and redesign runbook

Migrations (domain change, platform change, URL restructure, HTTPS, merging sites, redesign) are where sites lose the most traffic. Treat as a project.

**Before**
1. **Inventory all URLs** with value: crawl the current site, export GSC top pages (16 months), analytics landing pages, backlink tools' top linked pages, sitemap URLs.
2. **Benchmark**: traffic, rankings for priority keywords, indexed pages count, CWV, conversions. Save full crawl output (titles, descriptions, canonicals, H1s, structured data, internal links).
3. **Redirect map**: every old URL → most relevant new URL (1:1 where possible) with **301/308**. No mass redirects to home. Spreadsheet: old URL, new URL, status, notes.
4. **Parity check on staging**: titles, descriptions, H1s, body content, internal links, structured data, canonicals, hreflang, image alt, page speed — compare old vs new for top templates and top 100 pages. Content removed in a redesign = rankings lost.
5. Staging blocked from indexing (auth preferred over robots/noindex so you don't accidentally ship them).
6. Plan launch at a low-traffic time; avoid peak season for e-commerce.

**Launch day**
1. Deploy; remove staging noindex/robots blocks from production config.
2. Test redirects in bulk (script the redirect map: expect 301 + correct Location, no chains/loops).
3. Verify robots.txt, sitemap (new URLs only), canonicals use new domain, hreflang updated, structured data URLs updated.
4. Domain change: use GSC **Change of Address** tool (old property → new) after redirects are live. Verify both properties.
5. Submit new sitemap; keep the old sitemap (with old URLs) available temporarily to encourage crawling of redirects.
6. Update internal links to point directly to new URLs (no internal redirects), plus GBP, social profiles, ad campaigns, email templates, top backlinks (outreach for most valuable ones).

**After**
- Daily for 2 weeks: GSC Pages/crawl errors, 404s in server logs, traffic by landing page vs benchmark.
- Keep redirects **at least 1 year, ideally permanently**.
- Expect temporary fluctuation 2–8 weeks for URL changes; domain moves can take months to fully settle.
- Investigate any page that lost traffic: missing redirect, lost content, changed title, lost internal links.

## 9. What to expect: timelines

Set realistic expectations in the playbook (varies widely by competition and authority):
- **Technical fixes** (indexing, canonical, noindex removed): visible in days to a few weeks after recrawl.
- **New site** with no links: often 3–6 months to meaningful non-brand traffic; long-tail first.
- **New content on an established site**: indexing in days; rankings settle over 1–3 months.
- **Link building / authority**: compounding over 6–12+ months.
- **Rich results**: after recrawl when markup is valid; eligibility is never guaranteed.
- **Core updates**: roll out over ~2 weeks; recovery usually requires sustained quality improvements and often the next core update.

## 10. KPIs

Pick a few, tied to the business:
- **Organic conversions / revenue** (primary).
- Organic clicks and **non-brand** clicks (GSC; filter out brand queries with a regex).
- Impressions and average position for the priority keyword set.
- Indexed pages vs. intended indexable pages (coverage ratio).
- CTR for top pages (title/description effectiveness).
- Core Web Vitals pass rate (field).
- Referring domains (quality, relevant).
- Local: GBP calls, direction requests, website clicks; review count and rating.
- AI visibility: referrals from AI assistants; brand citations in tracked prompts.

## 11. Playbook items for ULTIMATE-SEO.md

- [ ] Pre-launch checklist run against production (owner + dev).
- [ ] GSC Domain property verified via DNS; sitemap submitted; GA4 linked (owner action).
- [ ] Bing Webmaster Tools imported from GSC (owner action).
- [ ] IndexNow key + submit-on-publish hook (only if content changes frequently).
- [ ] Analytics with organic segment and key events defined.
- [ ] Uptime monitor on home, robots.txt, sitemap; alerts for noindex/robots changes.
- [ ] Priority keyword list (20–100) in a rank tracker or tracked via GSC.
- [ ] Weekly/monthly/quarterly cadence assigned to a named owner.
- [ ] If migrating: redirect map file location, parity check results, Change of Address done.
- [ ] Baseline KPIs recorded (date-stamped) so progress is measurable.
