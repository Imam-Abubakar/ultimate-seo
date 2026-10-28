# Content Strategy, On-Page & Link Earning

Technical SEO makes a site eligible to rank; content and links decide whether it does. Use this file to build the "Next 30/90 days" roadmap in ULTIMATE-SEO.md — every recommendation there should name real pages, topics, and page types for *this* site.

## Contents

1. Search intent
2. Keyword research workflow
3. Topic clusters and pillar pages
4. Page-type playbooks by site type
5. On-page structure
6. E-E-A-T signals
7. Google's content policies (helpful content, scaled content abuse, site reputation abuse)
8. Internal linking rules
9. Content refresh and pruning
10. Programmatic SEO done safely
11. Link earning
12. RSS/Atom feeds
13. Playbook items for ULTIMATE-SEO.md

---

## 1. Search intent

Every target query has an intent, and the ranking page type must match it. Check by searching the query and looking at what currently ranks — the SERP is the spec.

| Intent | Example | Page type that ranks |
|---|---|---|
| Informational | "what is schema markup" | Guide, explainer, glossary entry |
| Commercial investigation | "best CRM for startups", "X vs Y", "X alternatives" | Comparison, listicle, review |
| Transactional | "buy running shoes", "notion pricing" | Product, category, pricing, signup page |
| Navigational | "stripe dashboard login" | Brand/home/login page |
| Local | "plumber near me", "dentist austin" | Local landing page + Google Business Profile |

Mismatch is the most common reason good content doesn't rank: a product page won't rank for "how to choose X", and a blog post won't rank for "buy X".

## 2. Keyword research workflow

1. **Seed list** from the business: products, features, problems solved, audiences, competitors, integrations, locations. Pull from the repo: nav labels, feature names, docs headings, FAQs, support tickets if available.
2. **Expand** with tools:
   - Free: Google Search Console (queries you already get impressions for — the best data source once live), Google autocomplete & "People also ask", Google Keyword Planner (ranges), Bing Webmaster Tools keyword research, Google Trends, AnswerThePublic (limited free), Reddit/forums/Stack Overflow for real phrasing.
   - Paid: Ahrefs, Semrush, Moz, SE Ranking, Mangools/KWFinder — volume, difficulty, competitor gap, SERP features.
3. **Qualify** each keyword: intent, business value (would a searcher become a customer?), difficulty vs. your site's authority, current SERP (who ranks — giant brands or small sites?).
4. **Map** keywords to pages: one primary topic per URL; group synonyms and close variants onto the same page. Two pages chasing the same intent = cannibalization.
5. **Prioritize**: high business value × achievable difficulty first. New sites should target long-tail, specific, low-competition queries before head terms.

Deliverable for the playbook: a keyword → URL map (table), noting which pages exist, need improving, or need creating.

## 3. Topic clusters and pillar pages

- **Pillar page**: broad, comprehensive page on a core topic (e.g. "Email Marketing Guide").
- **Cluster pages**: focused pages on subtopics ("email subject lines", "email deliverability", "cold email templates").
- Every cluster page links to the pillar; the pillar links to every cluster page; related clusters interlink with descriptive anchors.
- Clusters build **topical authority** — covering a topic thoroughly beats scattered one-off posts.
- Start with 2–3 clusters aligned with what you sell. Don't write clusters unrelated to the business just for traffic; it dilutes topical focus and rarely converts.

## 4. Page-type playbooks by site type

### SaaS / software product
Highest-value pages, in rough priority order:
1. **Home** — clear category ("project management software for agencies"), not just a slogan.
2. **Feature pages** — one per major feature, targeting "[feature] software/tool".
3. **Use-case / solution pages** — by job-to-be-done ("client onboarding") and by industry/role ("for agencies", "for HR teams").
4. **Comparison pages** — "Product vs Competitor": honest, specific tables; acknowledge where competitor wins. These convert extremely well.
5. **Alternatives pages** — "Competitor alternatives": list several including yourself, with real criteria.
6. **Integration pages** — one per integration ("Slack integration"); partner may link back.
7. **Pricing page** — indexable, crawlable plan details (not only in JS/images).
8. **Templates / free tools** — linkable assets that attract links and top-of-funnel traffic.
9. **Docs & changelog** — rank for long-tail "how to X in Product" and build trust.
10. **Blog** — problem-focused content for your ICP, linking to features/use cases.

### E-commerce
1. **Category/collection pages** usually drive the most organic revenue: unique intro copy (above or below grid), useful filters, FAQs, buying advice, internal links to subcategories.
2. **Product pages**: unique descriptions (never manufacturer copy-paste alone), specs, real reviews, Q&A, sizing, shipping/returns info, high-quality images.
3. **Buying guides** ("how to choose a road bike") linking to categories.
4. **Comparison / "best X for Y"** pages for commercial queries.
5. Brand pages if you stock multiple brands. See `ecommerce.md`.

### Local business
1. **One page per core service** (not one page listing everything).
2. **Location pages** only for real locations or genuinely served areas with unique content (local team, photos, testimonials from that area, local specifics, directions). City-swap pages with identical copy are doorway pages.
3. Strong contact/about page with NAP. See `local-seo.md`.

### Publisher / blog / media
1. Topic hubs/category pages that are curated, not just paginated archives.
2. Author pages with credentials.
3. Evergreen guides updated regularly + timely news if relevant.
4. Original research, data, and first-hand testing — what differentiates from AI-generated summaries.
5. Article schema with author, `datePublished`, `dateModified`; RSS feed; Google News/Discover hygiene (large high-quality images ≥1200px wide, `max-image-preview:large`).

### Documentation sites
1. Task-oriented page titles ("Authenticate with OAuth" not "Auth").
2. One concept per page, stable URLs, versioning strategy (canonical to latest; noindex or canonicalize old versions).
3. Search-friendly error message pages (people paste errors into Google).
4. Breadcrumbs + BreadcrumbList schema, sidebar navigation as real links.
5. `llms.txt` and clean markdown copies are especially valuable here (see `ai-search.md`).
6. Information architecture by job: *Getting started* (install, quickstart), *Guides* (task pages: "Add dark mode to WidgetKit"), *Reference* (one page per component/endpoint/CLI command, generated from source where possible), *Concepts* (why/how it works), *Troubleshooting* (one page per common error, title = the error text).
7. Every reference page needs real prose above the API table: what it is, when to use it, a minimal working example. Bare property tables rank poorly and get cited rarely.
8. Integration and "X with Y" pages ("WidgetKit with React", "…with Vue", "…with Astro") capture framework-specific searches and earn links from those ecosystems.
9. Comparison/migration pages ("Migrating from Shoelace to WidgetKit") for libraries with alternatives.
10. Off-site: keep the GitHub README, npm/PyPI description and docs homepage consistent (same one-line description) — they reinforce the entity for search and AI. Link docs from the package registry and repo `homepage` field.
11. Measure with Search Console queries containing error strings, "how to", and component names; turn high-impression/low-CTR queries into better titles, and unanswered queries into new pages.

### Portfolio / personal site
1. Home that states name + role + specialty ("Jane Doe — Product Designer for fintech").
2. One page per case study with problem/process/outcome, not just images.
3. About page; `Person` schema with `sameAs` to profiles; `ProfilePage` on about.
4. Writing/talks section to earn links and topical relevance.

### Marketplace / directory / community
1. Category and location hub pages with unique, useful intros.
2. Listing pages: noindex thin or empty listings; index only those with substantive content.
3. User-generated content: moderate, `rel="ugc"` on user links, noindex low-quality profiles.

## 5. On-page structure

For every important page:

- **Title**: primary topic first, specific, ≤ ~60 chars, brand last. Unique sitewide.
- **Meta description**: ≤ ~155 chars; what the page gives + why click. Google rewrites often; still write it.
- **H1**: one, matches intent, close to title (need not be identical).
- **Intro**: answer or value proposition in the first 2–3 sentences (good for users, featured snippets, and AI answers).
- **Headings**: H2/H3 as a scannable outline; phrase some as the questions people ask.
- **Body**: covers the topic completely, with specifics — numbers, examples, screenshots, steps, original data. Depth means completeness, not word count.
- **Media**: images with descriptive filenames and `alt`; video with transcript; diagrams.
- **Internal links**: to pillar/parent, to related pages, to the next step in the funnel.
- **Freshness**: visible "Updated" date on content that changes; actually update it.
- **URL**: short, lowercase, hyphenated, descriptive, no dates for evergreen content, no stop-word stuffing.

## 6. E-E-A-T signals

Experience, Expertise, Authoritativeness, Trust. Not a ranking factor by itself but a framework for what Google's systems reward, especially for YMYL topics (health, finance, legal, safety).

Concrete implementations:
- **Author bylines** linking to **author pages** with real bio, credentials, photo, links to profiles (`Person` schema with `sameAs`, `jobTitle`, `knowsAbout`).
- **About page**: who runs the site, history, team, mission; **Contact page** with real contact methods.
- **First-hand experience**: original photos, screenshots, test results, "we tried X for 30 days" details.
- **Sourcing**: cite primary sources; link out to authoritative references.
- **Editorial policy / review process** pages for publishers; "Medically reviewed by" for health.
- **Trust basics**: HTTPS, privacy policy, terms, clear pricing, refund/return policy, real business details.

## 7. Google's content policies

Verify against current docs: https://developers.google.com/search/docs/essentials/spam-policies and https://developers.google.com/search/docs/fundamentals/creating-helpful-content

- **Helpful content** (now part of core ranking systems since March 2024): content made for people, demonstrating first-hand expertise, leaving readers satisfied. Red flags: content written mainly to rank, summarizing others without adding value, covering trends outside your expertise, promising answers that don't exist.
- **Scaled content abuse**: generating many pages primarily to manipulate rankings — whether via AI, templates, scraping, or humans — with little value. AI use itself isn't penalized; low-value scale is.
- **Site reputation abuse** ("parasite SEO"): third-party content hosted on a reputable site to exploit its ranking signals (e.g. coupon sections run by others). Avoid hosting it.
- **Expired domain abuse**: buying expired domains to host unrelated low-value content.
- **Doorway pages**: many near-identical pages targeting variants (city names) that funnel to one destination.

AI-assisted writing guidance for the playbook: use AI for outlines, drafts, and editing, but add human expertise, original examples, accurate facts, and a real author. Fact-check everything.

## 8. Internal linking rules

1. Every indexable page should be reachable via crawlable `<a href>` links from at least one other page — ideally within 3 clicks from home.
2. **Descriptive anchor text** ("compare CRM pricing plans") — not "click here". Vary naturally.
3. Link from high-authority pages (home, popular posts) to pages you want to rank.
4. Use hub pages (pillars, categories) to distribute links.
5. Add contextual links in body copy, not only nav/footer.
6. Breadcrumbs on nested sites (with BreadcrumbList schema).
7. Fix orphan pages (in sitemap but no internal links) — find them by comparing sitemap URLs to crawled link graph.
8. Avoid linking to redirects or 404s internally; update links after URL changes.
9. "Related posts" blocks should be relevance-based, not random.
10. Don't `nofollow` internal links (PageRank sculpting doesn't work and hurts discovery).

## 9. Content refresh and pruning

- Quarterly: export GSC pages with declining clicks or with high impressions but low CTR (positions 4–15 are the best targets).
- Refresh: update facts, stats, screenshots, examples; expand sections that match new "People also ask" questions; improve title/description for CTR; update `dateModified` only when content materially changes.
- Prune: pages with no traffic, no links, and no business value → improve, merge (301 to the better page), or remove (410/404). Don't delete pages that have backlinks without redirecting.
- Consolidate cannibalizing pages: pick the strongest URL, merge content, 301 the others.

## 10. Programmatic SEO done safely

Programmatic pages (templated pages generated from data: integrations, locations, comparisons, glossary) are legitimate when each page has **unique, useful data** a searcher wants.

Do:
- Start from a proprietary or well-structured dataset that varies meaningfully per page (prices, stats, specs, availability, reviews, local details).
- Make each page answer the query fully on its own, with unique copy blocks driven by the data, not just swapped names.
- Launch in batches (e.g. 50–200 pages), monitor indexing and engagement in GSC, then expand.
- `noindex` or skip pages whose data is thin/empty; set a minimum-content threshold in code.
- Link them through hub pages; include them in the sitemap.

Don't:
- Generate thousands of pages that differ only by a keyword (city name, "best X for Y" with the same list).
- Publish unreviewed AI text at scale.

## 11. Link earning

Links remain a major ranking signal. Earn them; don't buy them.

High-ROI tactics:
- **Linkable assets**: original research/data reports, free tools/calculators, templates, comprehensive guides, industry benchmarks, open-source projects, visual assets/infographics with embed codes.
- **Digital PR**: pitch data-driven stories to journalists; respond to journalist requests (Qwoted, Featured.com, Help a B2B Writer, Source of Sources); newsjacking with expert commentary.
- **Partner & integration links**: integration directories/marketplaces (Zapier, Slack, Shopify app stores), partners, customers' "powered by"/case studies, suppliers/vendors listing you.
- **Community**: genuinely helpful participation (Reddit, Stack Overflow, GitHub, industry forums) — links are usually nofollow but drive traffic and brand mentions.
- **Podcasts & guest expertise**: guest appearances, expert roundups, conference talks (event pages link to speakers).
- **Unlinked brand mentions**: find mentions without links and ask for a link.
- **Broken link building**: find dead resources on relevant sites and offer your equivalent.
- **Directories**: only genuine, relevant ones (industry associations, chambers of commerce, G2/Capterra for SaaS, Product Hunt at launch).

Avoid: buying links, link exchanges at scale, PBNs, paid guest posts without `rel="sponsored"`, low-quality directory blasts, keyword-rich anchor manipulation. These violate Google's link spam policy.

Mark paid/affiliate links `rel="sponsored"`, user-generated links `rel="ugc"`.

## 12. RSS/Atom feeds

For blogs, news, changelogs, podcasts:
- Provide an RSS 2.0 or Atom feed with full or summary content, absolute URLs, `pubDate`/`updated`.
- Advertise it: `<link rel="alternate" type="application/rss+xml" title="Site Blog" href="https://example.com/rss.xml">`.
- Feeds help discovery by aggregators, readers, and some AI systems; Google can also use RSS/Atom as sitemaps for fresh URLs.

## 13. Playbook items for ULTIMATE-SEO.md

Make each item specific to the site:

- [ ] Keyword → URL map for the top 20–50 target queries (existing / improve / create).
- [ ] Page types to create first for this site type (from section 4), with proposed URLs and titles.
- [ ] 2–3 topic clusters with pillar + 5–10 cluster topics each.
- [ ] Author pages and bylines (publishers, blogs, YMYL).
- [ ] About/contact/trust pages complete.
- [ ] Internal linking pass: pillars ↔ clusters, orphan check, breadcrumbs.
- [ ] One linkable asset idea for the next 90 days and 5 link targets (partners, directories, journalists).
- [ ] Quarterly refresh routine using GSC (CTR and declining pages).
- [ ] Content template/checklist for new posts (title, description, H1, intro answer, internal links, image alt, schema, author, dates).
