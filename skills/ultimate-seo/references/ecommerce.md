# E-commerce SEO

Use this for online stores of any size and platform (custom, Shopify, WooCommerce, BigCommerce, Magento/Adobe Commerce, Salesforce Commerce, headless). E-commerce SEO is mostly about **category pages that rank, product pages that convert and earn rich results, and crawl control so faceted navigation doesn't drown the site in duplicates.**

## Contents

1. Site architecture
2. Category (PLP) page anatomy
3. Product (PDP) page anatomy
4. Product structured data
5. Google Merchant Center and free listings
6. Variants: URLs and canonicalization
7. Faceted navigation and crawl control
8. Pagination on category pages
9. Out-of-stock, discontinued and seasonal products
10. Image SEO
11. Internal site search
12. Platform quirks (Shopify, WooCommerce, others)
13. Playbook items for ULTIMATE-SEO.md

---

## 1. Site architecture

- Shallow hierarchy: Home → Category → Subcategory → Product (products reachable within ~3–4 clicks).
- Category URLs that mirror how people search: `/womens-running-shoes/`, `/mens/jackets/rain-jackets/`.
- Product URLs: short, stable, no category path required (`/products/nimbus-26`) — avoids duplicate URLs when a product lives in several categories. If the platform uses category paths in product URLs, ensure one canonical.
- Breadcrumbs on every category and product page (`BreadcrumbList` schema).
- Mega-menus must output real `<a href>` links in the HTML.

## 2. Category (PLP) page anatomy

Category pages target the highest-volume commercial queries ("running shoes", "linen bedding") and are usually the biggest organic revenue drivers.

- **Title**: `{Category} – {qualifier} | {Brand}` e.g. "Women's Running Shoes – Free Returns | Example".
- **H1**: the category name as searched.
- **Intro copy**: 1–3 sentences above the grid (don't push products below the fold); longer, genuinely useful copy below the grid — buying considerations, FAQs, links to subcategories and guides. Avoid keyword-stuffed SEO blocks.
- **Product grid**: products rendered in server HTML with links (not lazy-loaded only via JS on scroll/infinite scroll without paginated URLs).
- **Subcategory links** and popular filtered views as links (only the ones worth indexing, see §7).
- **Structured data**: `BreadcrumbList`; optionally `ItemList` for products. Don't put `Product` markup for many products on a category page expecting rich results — Google expects Product rich results on product pages.
- **Unique content**: each category page should be meaningfully different, not template text with the name swapped.

## 3. Product (PDP) page anatomy

- **Title**: `{Product name} {key attribute} – {Brand}`; include model numbers/SKUs people search.
- **Unique description**: written for the store; manufacturer copy is duplicated across every retailer. At minimum, add your own intro, use cases, comparisons, and FAQs.
- **Specs** as an HTML table/list (materials, dimensions, compatibility).
- **Price, availability, shipping and returns** visible near the buy button.
- **Reviews and Q&A** rendered in HTML (not only an iframe/JS widget that crawlers can't see); paginate or show top reviews.
- **Images**: multiple angles, zoomable, in-use photos, video if possible.
- **Related products / complete-the-look**: crawlable links.
- **Breadcrumbs**.
- **Canonical**: self (see §6 for variants).

## 4. Product structured data

Google has two product experiences: **product snippets** (review stars/price in organic results) and **merchant listings** (Shopping tab, product knowledge panels, free listings) — merchant listings require offer details. Reference: https://developers.google.com/search/docs/appearance/structured-data/product (verify against current docs).

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "@id": "https://example.com/products/nimbus-26#product",
  "name": "Nimbus 26 Women's Running Shoe",
  "description": "Neutral cushioned road running shoe with ...",
  "sku": "NIM26-W-BLK",
  "gtin13": "0123456789012",
  "mpn": "1012B601",
  "brand": { "@type": "Brand", "name": "Example Brand" },
  "image": [
    "https://example.com/img/nimbus-26-1x1.jpg",
    "https://example.com/img/nimbus-26-4x3.jpg",
    "https://example.com/img/nimbus-26-16x9.jpg"
  ],
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/products/nimbus-26",
    "priceCurrency": "USD",
    "price": "159.99",
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
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.6",
    "reviewCount": "128"
  }
}
```

Rules:
- **Values must be generated from real product data at render time** (price, currency, availability, ratings). Never hardcode or invent them. If the store has no reviews, omit `aggregateRating`/`review` entirely — fake ratings are a manual-action risk.
- Ratings must reflect reviews visible on the page and collected from customers (not copied from other sites).
- `price` as a number string without currency symbols; `priceCurrency` ISO 4217.
- `availability` must match what the page shows and what Merchant Center feeds say.
- Use GTIN/MPN/brand when they exist — they strengthen product matching.
- Store-wide shipping and return policies can also be declared once at the organization level (`Organization` → `hasMerchantReturnPolicy`, and shipping policy support in Organization markup) and/or in Merchant Center; page-level markup overrides. Verify current support: https://developers.google.com/search/docs/appearance/structured-data/merchant-listing
- Variants: Google supports `ProductGroup` with `hasVariant` and `variesBy` (size, color...) — use it when variants share a page. Reference: https://developers.google.com/search/docs/appearance/structured-data/product-variants
- Sale prices: use `priceSpecification` with `UnitPriceSpecification` and `priceType` `https://schema.org/StrikethroughPrice` for the original price (verify current docs).
- Validate with `validate_jsonld.py` and Google's Rich Results Test.

## 5. Google Merchant Center and free listings

Human tasks for the playbook:
1. Create a Merchant Center account (https://merchants.google.com), verify and claim the website.
2. Add products via feed (Shopify/WooCommerce apps, or a scheduled feed file/API) — or let Google build from structured data where supported (verify current options).
3. Enable **free listings** (Shopping tab, Images, Search).
4. Configure shipping and return policies in Merchant Center.
5. Fix item disapprovals and price/availability mismatches (page, schema, and feed must agree).
6. Add store ratings/product ratings programs if eligible.
7. Link to Google Analytics and Search Console.

Bing equivalent: Microsoft Merchant Center (import from Google).

## 6. Variants: URLs and canonicalization

Options:
- **One URL per product, variants via selector (no URL change or `?variant=` param)** — simplest. Canonical = base product URL. Use `ProductGroup` schema.
- **Distinct URLs per variant** (`/products/shirt-blue`, `/products/shirt?color=blue`) — use when variants are searched separately (e.g. "iphone 16 pro 256gb blue") and have unique content. Each variant URL is self-canonical, with `ProductGroup` + `Product` per variant (`isVariantOf`) and the page reflecting the selected variant's price/availability/image.
- **Never** canonicalize variant URLs to the base while showing different content and wanting them indexed — pick one strategy.
- Sort/view parameters (`?sort=price`, `?view=grid`) → canonical to the clean URL.
- Products in multiple categories → one canonical product URL.

## 7. Faceted navigation and crawl control

Filters (size, color, brand, price, rating) can create millions of URL combinations. Strategy:

1. **Decide which facet pages deserve to be indexable**: those with real search demand and enough products (e.g. "red dresses", "nike running shoes"). Make them clean, static-looking URLs (`/dresses/red/`) with unique title/H1/intro, self-canonical, in the sitemap, and linked from the category page.
2. **All other filter combinations** (multi-select, price ranges, sorting, in-stock toggles):
   - Prefer not generating crawlable links to them (use buttons/JS for low-value filters, or `rel="nofollow"` on those links) so Googlebot doesn't discover them.
   - Canonical to the parent category, or `noindex, follow` — but note Google may still crawl them.
   - Block crawling of parameter patterns in `robots.txt` when crawl volume is a problem (e.g. `Disallow: /*?*sort=`, `Disallow: /*?*price=`). Don't combine robots.txt blocking with expecting `noindex` to be seen.
3. Keep consistent parameter ordering and lowercase values to avoid duplicates (`?color=red&size=m` vs `?size=m&color=red`).
4. Google's guidance (verify against current docs): https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation

## 8. Pagination on category pages

- Use real paginated URLs (`?page=2` or `/page/2/`) with crawlable `<a href>` links. Infinite scroll/"load more" must also update the URL and have paginated fallbacks.
- Each page is **self-canonical** — don't canonicalize page 2+ to page 1 (products on deeper pages would lose their discovery path).
- `rel="next"/"prev"` are no longer used by Google as indexing signals; harmless to keep.
- Unique titles: "Women's Running Shoes – Page 2 | Example".
- Optionally noindex very deep pages on huge catalogs only if products are discoverable through other links (subcategories, sitemaps).
- Consider "view all" only when it loads fast.

## 9. Out-of-stock, discontinued and seasonal products

| Situation | Action |
|---|---|
| Temporarily out of stock | Keep the page live (200), show "out of stock" + restock date/notify-me, update `availability` to `OutOfStock` or `BackOrder`/`PreOrder`, show alternatives |
| Permanently discontinued, has a clear replacement | 301 to the replacement product (or closest category) |
| Discontinued, valuable traffic/links, no replacement | Keep page with "discontinued" notice, specs, and links to alternatives (good for support/reviews); `availability: Discontinued` |
| Discontinued, no traffic/links/value | 410 (or 404); remove from sitemap and internal links |
| Seasonal (Black Friday, holiday collections) | Keep a **permanent evergreen URL** (`/black-friday`) and update it each year rather than creating `/black-friday-2026` |

Don't mass-redirect discontinued products to the home page (treated as soft 404).

## 10. Image SEO

- Descriptive filenames (`nimbus-26-womens-black-side.jpg`), not `IMG_1234.jpg`.
- `alt` describing the product and variant ("Nimbus 26 women's running shoe in black, side view").
- Serve modern formats (AVIF/WebP) with fallbacks, responsive `srcset`, explicit width/height; lazy-load below-the-fold images but **not** the main product image (it's usually the LCP element — give it `fetchpriority="high"`).
- Product images on a white/clean background for Merchant Center; lifestyle images on the page too.
- Images large enough for Google Images/Discover (≥1200px wide for primary image; provide 1:1, 4:3, 16:9 in schema).
- Use a CDN; keep image URLs stable (changing CDN URLs constantly forces re-discovery).
- Image sitemap optional; useful if images are loaded via JS.

## 11. Internal site search

- Internal search result pages (`/search?q=`) should be `noindex` (and ideally disallowed in robots.txt if they're being crawled heavily) — infinite low-quality URLs.
- Mine internal search queries (analytics) for keyword research: frequent searches with no matching category → create a category/landing page.
- Optional `WebSite` + `SearchAction` schema (sitelinks search box was retired by Google in late 2024 — markup is harmless but provides no rich result; verify against current docs).

## 12. Platform quirks (Shopify, WooCommerce, others)

Details in `frameworks/cms-platforms.md`. Common issues:
- **Shopify**: products accessible at both `/products/x` and `/collections/y/products/x` — make sure theme links use the canonical `/products/x` (`{{ product.url }}` without `within: collection`). Fixed `/products/`, `/collections/` prefixes. robots.txt editable via `robots.txt.liquid`. Tag pages (`/collections/x/tag`) create thin duplicates — noindex or avoid linking. Apps can inject duplicate JSON-LD — audit for multiple `Product` blocks.
- **WooCommerce**: use Yoast/Rank Math (+ WooCommerce SEO add-on) for product schema; noindex product tags and thin attribute archives; watch `?add-to-cart=` and `?orderby=` parameter URLs.
- **Magento/Adobe Commerce**: layered navigation parameters, category path in product URLs (config: "Use Categories Path for Product URLs" → No), canonical meta tag settings.
- **Headless**: ensure SSR/SSG of category and product pages; generate sitemaps from the product API; don't render prices only client-side.

## 13. Playbook items for ULTIMATE-SEO.md

- [ ] Product JSON-LD generated from live data on every PDP (price, availability, GTIN, brand, images, shipping, returns); ratings only if real reviews exist.
- [ ] BreadcrumbList on categories and products.
- [ ] Facet strategy documented: which facet pages are indexable; everything else non-crawlable/canonicalized.
- [ ] Pagination: crawlable, self-canonical.
- [ ] Out-of-stock and discontinued rules implemented (who decides 301 vs keep vs 410).
- [ ] Category copy for the top 10 categories by revenue/search demand.
- [ ] Rewrite manufacturer descriptions for top 50 products.
- [ ] Merchant Center: set up, free listings enabled, shipping/returns configured, zero mismatches (owner action).
- [ ] Review collection program (post-purchase email) with reviews rendered in HTML.
- [ ] Image audit: filenames, alt, LCP image priority, formats.
- [ ] Internal search: noindex; monthly review of top no-result queries.
- [ ] Seasonal evergreen landing pages created ahead of season (≥6–8 weeks before).
