# Structured Data Reference (JSON-LD)

How to describe pages to search engines and AI systems with schema.org JSON-LD — what to add, what's eligible for rich results, and what gets sites penalized.

Ready-to-fill templates live in `assets/jsonld/*.json`. This file explains how to use them correctly.

## Contents

1. Core rules
2. The @graph and @id pattern
3. Site-wide: Organization, WebSite
4. BreadcrumbList
5. Article / BlogPosting / NewsArticle
6. Product, Offer, return policy, shipping
7. SoftwareApplication
8. LocalBusiness
9. Event
10. FAQPage (restricted rich results)
11. Person / ProfilePage
12. VideoObject
13. Recipe
14. JobPosting
15. Course
16. Reviews and ratings policy
17. Google rich-result eligibility table
18. Validation and monitoring

---

## 1. Core rules

- **Format**: JSON-LD in `<script type="application/ld+json">`. Google also supports Microdata/RDFa, but JSON-LD is recommended and easiest to maintain.
- **Server-rendered**: include it in initial HTML. Google can read JS-injected JSON-LD, but other consumers (Bing, AI crawlers) often can't.
- **Visible content only**: every marked-up fact must be visible to users on that page (price, rating, author, FAQ answers, dates). Hidden-only markup violates Google's guidelines.
- **Truthful**: never invent ratings, reviews, prices, addresses, founding dates, or awards. Use placeholders and list them in `ULTIMATE-SEO.md`.
- **Absolute URLs** for `url`, `@id`, `image`, `logo`, `sameAs`, `item`.
- **Specific types**: `BlogPosting` over `CreativeWork`, `Dentist` over `LocalBusiness` when accurate.
- **Dates**: ISO 8601 with timezone: `2026-09-14T09:30:00+01:00`.
- **One coherent graph per page** (see §2) rather than many disconnected blobs. Multiple `<script>` blocks are valid, but a single `@graph` is cleaner and avoids contradictions.
- **Escape safely** when serializing from data: replace `<` with `<` to prevent `</script>` injection (XSS). E.g. `JSON.stringify(data).replace(/</g, '\\u003c')`.
- **Required vs recommended**: missing required properties = not eligible; missing recommended = eligible but weaker. Fill recommended properties when the data genuinely exists.
- Structured data does **not** directly boost rankings; it enables rich results, improves entity understanding (Knowledge Graph, AI answers), and can lift CTR.

---

## 2. The @graph and @id pattern

Give each entity a stable `@id` (URL + fragment) and reference it instead of repeating it.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://www.example.com/#organization",
      "name": "Acme",
      "url": "https://www.example.com/",
      "logo": { "@type": "ImageObject", "url": "https://www.example.com/logo-512.png", "width": 512, "height": 512 }
    },
    {
      "@type": "WebSite",
      "@id": "https://www.example.com/#website",
      "url": "https://www.example.com/",
      "name": "Acme",
      "publisher": { "@id": "https://www.example.com/#organization" }
    },
    {
      "@type": "WebPage",
      "@id": "https://www.example.com/pricing#webpage",
      "url": "https://www.example.com/pricing",
      "name": "Pricing | Acme",
      "isPartOf": { "@id": "https://www.example.com/#website" },
      "breadcrumb": { "@id": "https://www.example.com/pricing#breadcrumb" }
    }
  ]
}
```

Conventions: `/#organization`, `/#website`, `/#person`, `{pageUrl}#webpage`, `{pageUrl}#breadcrumb`, `{pageUrl}#article`, `{pageUrl}#product`. Keep `@id`s identical on every page.

---

## 3. Site-wide: Organization, WebSite

**Organization** — on the home page (and optionally sitewide via `@id` reference). Feeds logo in results, Knowledge Panel, and entity disambiguation for AI.

```json
{
  "@type": "Organization",
  "@id": "https://www.example.com/#organization",
  "name": "Acme",
  "legalName": "Acme Software Ltd",
  "url": "https://www.example.com/",
  "logo": "https://www.example.com/logo-512.png",
  "description": "Invoicing software for freelancers and small agencies.",
  "sameAs": [
    "https://www.linkedin.com/company/acme",
    "https://github.com/acme",
    "https://x.com/acme",
    "https://www.wikidata.org/wiki/Q000000"
  ],
  "contactPoint": { "@type": "ContactPoint", "contactType": "customer support", "email": "support@example.com" }
}
```

- Logo: ≥112×112 px, crawlable, on a background that works on white.
- `sameAs`: only real, official profiles. Wikidata/Wikipedia entries are the strongest entity signals when they exist.
- Optional when known: `foundingDate`, `founder`, `address`, `numberOfEmployees`, `vatID`, `iso6523Code`, `duns`.
- For a personal site use `Person` instead (see §11).
- Online stores can use `OnlineStore` (subtype of Organization) with `hasMerchantReturnPolicy`.

**WebSite** — on the home page; controls the **site name** shown in Google results.

```json
{
  "@type": "WebSite",
  "@id": "https://www.example.com/#website",
  "url": "https://www.example.com/",
  "name": "Acme",
  "alternateName": ["Acme Invoicing", "acme.com"],
  "publisher": { "@id": "https://www.example.com/#organization" },
  "inLanguage": "en-US"
}
```

Sitelinks search box (`potentialAction` SearchAction) rich result was **retired by Google in late 2024**; the markup is harmless but no longer produces a feature. Don't add it expecting a result.

---

## 4. BreadcrumbList

On every page below the home page. Must mirror a visible breadcrumb trail (or the logical hierarchy).

```json
{
  "@type": "BreadcrumbList",
  "@id": "https://www.example.com/blog/late-payment-email#breadcrumb",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.example.com/" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://www.example.com/blog" },
    { "@type": "ListItem", "position": 3, "name": "How to Write a Late Payment Email" }
  ]
}
```

The last item may omit `item` (it's the current page). Note: Google stopped *displaying* breadcrumbs in mobile result URLs (2025) but still uses the markup; keep it.

---

## 5. Article / BlogPosting / NewsArticle

```json
{
  "@type": "BlogPosting",
  "@id": "https://www.example.com/blog/late-payment-email#article",
  "mainEntityOfPage": "https://www.example.com/blog/late-payment-email",
  "headline": "How to Write a Late Payment Email (With 7 Templates)",
  "description": "Polite, firm and final-notice templates for chasing unpaid invoices.",
  "image": [
    "https://www.example.com/og/late-payment-email-16x9.png",
    "https://www.example.com/og/late-payment-email-4x3.png",
    "https://www.example.com/og/late-payment-email-1x1.png"
  ],
  "datePublished": "2026-03-02T08:00:00+00:00",
  "dateModified": "2026-09-14T10:15:00+00:00",
  "author": [{ "@type": "Person", "name": "Jane Doe", "url": "https://www.example.com/authors/jane-doe" }],
  "publisher": { "@id": "https://www.example.com/#organization" },
  "inLanguage": "en-US",
  "wordCount": 1850
}
```

- Use `NewsArticle` for news, `BlogPosting` for blogs, `Article` otherwise; `TechArticle` for docs is valid schema.
- `headline` should match the visible H1 (no hard length limit now, but keep concise).
- Images: ≥1200 px wide recommended; multiple aspect ratios (16:9, 4:3, 1:1) maximize eligibility.
- `author`: Person (or Organization) with `url` to an author page — supports E-E-A-T. Don't put the job title in `name`.
- `dateModified` only changes when content meaningfully changes. Show dates visibly.

---

## 6. Product, Offer, return policy, shipping

Product snippets (price, availability, ratings in results) and merchant listings (Shopping tab, free listings).

```json
{
  "@type": "Product",
  "@id": "https://shop.example.com/p/trail-runner-2#product",
  "name": "Trail Runner 2 – Men's Running Shoe",
  "image": ["https://shop.example.com/img/trail-runner-2-1.jpg"],
  "description": "Lightweight trail shoe with 6mm drop and Vibram outsole.",
  "sku": "TR2-M-BLK-42",
  "gtin13": "0123456789012",
  "brand": { "@type": "Brand", "name": "Acme" },
  "offers": {
    "@type": "Offer",
    "url": "https://shop.example.com/p/trail-runner-2",
    "priceCurrency": "USD",
    "price": "129.00",
    "priceValidUntil": "2026-12-31",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition",
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "shippingRate": { "@type": "MonetaryAmount", "value": "0", "currency": "USD" },
      "shippingDestination": { "@type": "DefinedRegion", "addressCountry": "US" },
      "deliveryTime": {
        "@type": "ShippingDeliveryTime",
        "handlingTime": { "@type": "QuantitativeValue", "minValue": 0, "maxValue": 1, "unitCode": "DAY" },
        "transitTime": { "@type": "QuantitativeValue", "minValue": 2, "maxValue": 5, "unitCode": "DAY" }
      }
    },
    "hasMerchantReturnPolicy": {
      "@type": "MerchantReturnPolicy",
      "applicableCountry": "US",
      "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
      "merchantReturnDays": 30,
      "returnMethod": "https://schema.org/ReturnByMail",
      "returnFees": "https://schema.org/FreeReturn"
    }
  }
}
```

- Variants: `ProductGroup` with `hasVariant` and `variesBy` (size, color), each variant a `Product` with its own `sku`/`offers`; `productGroupID`.
- Price ranges: `AggregateOffer` with `lowPrice`/`highPrice`/`offerCount`.
- Sale prices: `priceSpecification` with `UnitPriceSpecification` and `priceType: https://schema.org/StrikethroughPrice` for the original price.
- Shipping and return policy can be defined once at the Organization level (`hasMerchantReturnPolicy`, `shippingDetails` via `OfferShippingDetails` on Organization — supported since 2024/2025) instead of per offer, or configured in Merchant Center. Verify against current docs: https://developers.google.com/search/docs/appearance/structured-data/merchant-listing
- `aggregateRating`/`review` only when genuine reviews are displayed on the page.
- Identifiers (`gtin`, `mpn`, `brand`) strongly help merchant listings.

---

## 7. SoftwareApplication

For apps and SaaS products (also `WebApplication`, `MobileApplication`, `VideoGame`).

```json
{
  "@type": "SoftwareApplication",
  "name": "Acme Invoicing",
  "applicationCategory": "BusinessApplication",
  "operatingSystem": "Web, iOS, Android",
  "offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
  "url": "https://www.example.com/"
}
```

Google's software app rich result requires `name`, `offers.price` and **either** `aggregateRating` or `review` — so without genuine reviews it won't show stars. Still valuable for entity understanding; never fake ratings to unlock it.

---

## 8. LocalBusiness

Use the most specific subtype (`Restaurant`, `Dentist`, `LegalService`, `HomeAndConstructionBusiness`, `AutoRepair`…). One entity per physical location, on that location's page.

```json
{
  "@type": "Dentist",
  "@id": "https://www.example.com/locations/leeds#localbusiness",
  "name": "Bright Smile Dental Leeds",
  "image": "https://www.example.com/img/leeds-clinic.jpg",
  "url": "https://www.example.com/locations/leeds",
  "telephone": "+44 113 000 0000",
  "priceRange": "££",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "1 Example Street",
    "addressLocality": "Leeds",
    "postalCode": "LS1 1AA",
    "addressCountry": "GB"
  },
  "geo": { "@type": "GeoCoordinates", "latitude": 53.7997, "longitude": -1.5492 },
  "openingHoursSpecification": [
    { "@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"], "opens": "08:30", "closes": "17:30" }
  ],
  "parentOrganization": { "@id": "https://www.example.com/#organization" }
}
```

NAP (name, address, phone) must match the Google Business Profile exactly. Service-area businesses without a public address: use `areaServed` and omit `address`/`geo` street details. See `local-seo.md`.

---

## 9. Event

```json
{
  "@type": "Event",
  "name": "Freelance Finance Live 2026",
  "startDate": "2026-11-20T18:00:00+00:00",
  "endDate": "2026-11-20T21:00:00+00:00",
  "eventStatus": "https://schema.org/EventScheduled",
  "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
  "location": {
    "@type": "Place",
    "name": "Example Hall",
    "address": { "@type": "PostalAddress", "streetAddress": "10 Example Rd", "addressLocality": "London", "postalCode": "E1 6AN", "addressCountry": "GB" }
  },
  "image": ["https://www.example.com/img/event.jpg"],
  "description": "An evening of talks on pricing, invoicing and tax for freelancers.",
  "organizer": { "@type": "Organization", "name": "Acme", "url": "https://www.example.com/" },
  "offers": { "@type": "Offer", "url": "https://www.example.com/events/ffl-2026", "price": "15.00", "priceCurrency": "GBP", "availability": "https://schema.org/InStock", "validFrom": "2026-09-01T00:00:00+00:00" }
}
```

Online events: `eventAttendanceMode: OnlineEventAttendanceMode`, `location: { "@type": "VirtualLocation", "url": "…" }`. Update `eventStatus` for cancelled/postponed/rescheduled (`previousStartDate`). Not for coupons, multi-day "sales", or courses.

---

## 10. FAQPage (restricted rich results)

Since August 2023, FAQ rich results are shown **only for well-known, authoritative government and health websites**. For everyone else, FAQPage markup produces no rich result.

Still reasonable to add when the page has a genuine, visible FAQ section because it is valid schema, it makes Q&A structure explicit for Bing and AI answer engines, and it costs little. Never add FAQs that aren't on the page, never use it for advertising, and set expectations: "no Google rich result expected".

```json
{
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Is Acme free?",
      "acceptedAnswer": { "@type": "Answer", "text": "Yes. Acme is free for up to 5 clients. Paid plans start at $12/month." }
    }
  ]
}
```

User-generated single-question pages (forums, Q&A sites) use `QAPage` instead. **HowTo** rich results were removed entirely in 2023; don't add HowTo markup expecting a result.

---

## 11. Person / ProfilePage

Personal sites, portfolios, author pages, creator profiles.

```json
{
  "@type": "ProfilePage",
  "dateCreated": "2024-01-10T00:00:00+00:00",
  "dateModified": "2026-09-01T00:00:00+00:00",
  "mainEntity": {
    "@type": "Person",
    "@id": "https://www.example.com/#person",
    "name": "Jane Doe",
    "alternateName": "janedoe",
    "jobTitle": "Product Designer",
    "description": "Product designer specialising in fintech onboarding.",
    "image": "https://www.example.com/jane.jpg",
    "url": "https://www.example.com/",
    "sameAs": ["https://www.linkedin.com/in/janedoe", "https://github.com/janedoe"],
    "worksFor": { "@type": "Organization", "name": "Acme" }
  }
}
```

`ProfilePage` rich results target forums/social/creator platforms with interaction stats, but the markup is a good fit for author and about pages generally.

---

## 12. VideoObject

For pages where a video is the main content (or prominent).

```json
{
  "@type": "VideoObject",
  "name": "How to send your first invoice",
  "description": "A 3-minute walkthrough of creating and sending an invoice in Acme.",
  "thumbnailUrl": ["https://www.example.com/video/first-invoice.jpg"],
  "uploadDate": "2026-05-01T09:00:00+00:00",
  "duration": "PT3M12S",
  "contentUrl": "https://cdn.example.com/video/first-invoice.mp4",
  "embedUrl": "https://www.youtube.com/embed/XXXXXXXX"
}
```

Key moments: `hasPart` with `Clip` items (or `SeekToAction`). Videos must be the page's main focus to get video indexing in Google (2023 change). A video sitemap helps discovery.

---

## 13. Recipe

```json
{
  "@type": "Recipe",
  "name": "Classic Jollof Rice",
  "image": ["https://www.example.com/img/jollof-16x9.jpg"],
  "author": { "@type": "Person", "name": "Jane Doe" },
  "datePublished": "2026-02-01",
  "description": "Smoky party-style jollof rice.",
  "prepTime": "PT20M",
  "cookTime": "PT50M",
  "totalTime": "PT1H10M",
  "recipeYield": "6 servings",
  "recipeCategory": "Main course",
  "recipeCuisine": "West African",
  "nutrition": { "@type": "NutritionInformation", "calories": "420 calories" },
  "recipeIngredient": ["3 cups long-grain parboiled rice", "6 plum tomatoes"],
  "recipeInstructions": [
    { "@type": "HowToStep", "name": "Blend", "text": "Blend tomatoes, peppers and onion until smooth." }
  ]
}
```

---

## 14. JobPosting

Eligible for Google for Jobs and the Indexing API.

Required: `title`, `description` (HTML allowed, full job description), `datePosted`, `hiringOrganization`, `jobLocation` (or `jobLocationType: "TELECOMMUTE"` + `applicantLocationRequirements`). Recommended: `validThrough`, `employmentType`, `baseSalary` (`MonetaryAmount` with `QuantitativeValue`), `identifier`, `directApply`. Remove the page or set `validThrough` in the past when filled — expired jobs with markup are a policy violation.

---

## 15. Course

Google retired the **Course info** rich result in 2025; the **Course list** (carousel) feature for course providers may still apply. `Course` with `name`, `description`, `provider` remains valid schema and useful for entity understanding. Verify current status before promising anything: https://developers.google.com/search/docs/appearance/structured-data/course

---

## 16. Reviews and ratings policy

- `Review`/`AggregateRating` only for content where users can see the reviews on that page, collected genuinely.
- **Self-serving reviews are ineligible**: a business marking up reviews about itself on its own site (`Organization` or `LocalBusiness` with `aggregateRating`) won't show stars (since 2019).
- Product reviews on product pages, critic reviews of books/movies/products are fine.
- Never copy reviews from third-party sites (Google, Trustpilot) into your markup.
- `Review snippet` requires `author`, `reviewRating`, `itemReviewed`; `ratingValue` within `bestRating`/`worstRating` (default 5/1).
- Pros/cons markup (`positiveNotes`/`negativeNotes`) for editorial product reviews.

---

## 17. Google rich-result eligibility table

> Status as of late 2026 — Google changes these often. **Verify at developers.google.com/search/docs/appearance/structured-data/search-gallery** before promising a rich result.

| Type | Rich result status | Notes |
|---|---|---|
| Organization (logo) | Supported | Logo, Knowledge Panel signals |
| WebSite (site name) | Supported | Sitelinks search box retired (Nov 2024) |
| BreadcrumbList | Supported | Desktop display; mobile shows domain only |
| Article / NewsArticle / BlogPosting | Supported | Top stories eligibility via content policies, not markup alone |
| Product (snippets + merchant listings) | Supported | Shopping/free listings |
| Review snippet / AggregateRating | Supported (with policy limits) | No self-serving reviews |
| Recipe | Supported | |
| Event | Supported | |
| JobPosting | Supported | Plus Indexing API |
| VideoObject | Supported | Main-content videos only |
| LocalBusiness | Supported | Mostly via Google Business Profile |
| SoftwareApplication | Supported | Needs genuine rating/review |
| ProfilePage, DiscussionForumPosting, QAPage | Supported | Forums/social/creator sites |
| Dataset | Supported (Dataset Search) | |
| Carousel (ItemList) | Limited | Specific types only |
| Image metadata (license) | Supported | |
| Math solver, Education Q&A | Supported | Education sites |
| Vacation rental, Paywalled content, Subscription | Supported | Specialized |
| FAQPage | **Restricted** (Aug 2023) | Only authoritative gov/health sites |
| HowTo | **Removed** (Sep 2023) | No rich result |
| Sitelinks search box | **Removed** (Nov 2024) | |
| Book Actions | **Retired** (2025) | |
| Course info | **Retired** (2025) | Course list carousel may persist — verify |
| ClaimReview (fact check) | **Retired** (2025) | |
| Estimated Salary | **Retired** (2025) | |
| Learning Video | **Retired** (2025) | |
| Special Announcement | **Retired** (2025) | |
| Vehicle Listing | **Retired** (2025) | |

Retired ≠ invalid: the schema is still valid and may still help other engines and AI systems understand the page; it just won't produce a Google feature. Don't add retired types purely for Google.

---

## 18. Validation and monitoring

- `python3 <skill-dir>/scripts/validate_jsonld.py <file|dir|url>` — parses every JSON-LD block, checks `@context`/`@type`, absolute URLs and key required properties.
- **Rich Results Test** (search.google.com/test/rich-results) — Google eligibility, renders JS.
- **Schema Markup Validator** (validator.schema.org) — full schema.org validity, all types.
- **Search Console → Enhancements** — per-type errors/warnings across the site after indexing.
- Bing Webmaster Tools → URL Inspection shows Bing's markup parse.
- Re-validate after template changes; add a CI check on built output if possible.
