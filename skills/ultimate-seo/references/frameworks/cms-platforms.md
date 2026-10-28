# CMS & Hosted Platforms: WordPress, Shopify, Webflow, Ghost, Wix/Squarespace, Headless CMS

On CMS platforms, much of the SEO baseline is configuration rather than code, and the platform or an SEO plugin already emits sitemaps, canonicals and some schema. Your job is to (1) avoid fighting or duplicating what the platform does, (2) fix theme-level gaps in code where the repo contains the theme, and (3) move everything that needs the admin UI into `ULTIMATE-SEO.md` as precise click-paths. For a headless CMS, the work is designing SEO fields in the content model and wiring them into the frontend framework.

## Contents
- Detect
- Where things go
- WordPress
- Shopify
- Webflow
- Ghost
- Wix and Squarespace
- Headless CMS (Sanity, Contentful, Strapi, others)
- Structured data (all)
- Verify (all)
- Pitfalls (all)

## Detect

| Platform | Signals in repo |
|---|---|
| WordPress theme/plugin | `style.css` with `Theme Name:`, `functions.php`, `theme.json` (block theme), `wp-content/`, `wp-config.php` |
| Shopify theme | `layout/theme.liquid`, `sections/`, `snippets/`, `config/settings_schema.json`, `.shopify/` or `shopify.theme.toml` |
| Webflow | usually no repo; exported `*.html` with `data-wf-site` attributes |
| Ghost theme | `package.json` with `"engines": {"ghost": ...}`, `default.hbs`, `post.hbs` |
| Headless | `sanity.config.ts`, `schemas/`, `contentful` SDK, `@strapi/strapi`, Storyblok/Prismic/Payload/Hygraph SDKs alongside a frontend framework |

Live site only: view source for `generator` meta, `/wp-json/`, `cdn.shopify.com`, `webflow.com` asset URLs, `static.parastorage.com` (Wix), `squarespace` assets.

## Where things go

| Concern | WordPress | Shopify | Headless |
|---|---|---|---|
| Titles/descriptions | SEO plugin fields per post | Product/collection/page "Search engine listing" + `theme.liquid` | `seo` object in CMS schema → frontend metadata |
| Canonical | plugin / core `rel_canonical` | `{{ canonical_url }}` in `theme.liquid` | frontend |
| Sitemap | core `/wp-sitemap.xml` or plugin `/sitemap_index.xml` | auto `/sitemap.xml` | frontend generates from CMS API |
| robots.txt | virtual (plugin editor) or physical file | `templates/robots.txt.liquid` | frontend |
| JSON-LD | plugin + theme additions | `sections`/`snippets` | frontend |
| OG images | plugin social fields, featured image | `page_image`, `settings.share_image` | `seo.ogImage` field |

## WordPress

**Pick one SEO plugin** (Yoast SEO, Rank Math, SEOPress, or The SEO Framework). If one is installed, use it; never install a second. The plugin handles titles, descriptions, canonicals, OG/Twitter, the sitemap index, breadcrumbs and a schema graph. Your theme must not duplicate those tags.

Theme hygiene (classic theme `functions.php`):

```php
add_action('after_setup_theme', function () {
    add_theme_support('title-tag');           // WP/plugin generates <title>; remove hard-coded <title> from header.php
    add_theme_support('post-thumbnails');     // featured image = default OG image
    add_theme_support('html5', ['search-form', 'gallery', 'caption', 'script', 'style']);
});
```

`header.php` must call `wp_head()` before `</head>` and `<html <?php language_attributes(); ?>>`; `footer.php` must call `wp_footer()`. Block themes (`theme.json`, `templates/*.html`) get these automatically.

Without an SEO plugin (rare; prefer recommending one), minimal additions:

```php
add_action('wp_head', function () {
    if (is_singular()) {
        $desc = has_excerpt() ? get_the_excerpt() : wp_trim_words(wp_strip_all_tags(get_the_content()), 30);
        printf('<meta name="description" content="%s">' . "\n", esc_attr($desc));
        $img = get_the_post_thumbnail_url(null, 'large');
        if ($img) printf('<meta property="og:image" content="%s">' . "\n", esc_url($img));
    }
}, 1);
```

(WordPress core already outputs `rel=canonical` on singular pages and the `/wp-sitemap.xml` sitemap since 5.5; SEO plugins replace both.)

Custom JSON-LD on top of a plugin: extend the plugin's graph rather than printing a second disconnected block — Yoast: `wpseo_schema_graph_pieces` / `wpseo_schema_<type>` filters; Rank Math: `rank_math/json_ld` filter. Example (Rank Math):

```php
add_filter('rank_math/json_ld', function ($data, $jsonld) {
    if (is_singular('event')) {
        $data['Event'] = [
            '@type' => 'Event',
            'name' => get_the_title(),
            'startDate' => get_post_meta(get_the_ID(), 'start_date', true),
            'location' => ['@type' => 'Place', 'name' => get_post_meta(get_the_ID(), 'venue', true)],
        ];
    }
    return $data;
}, 10, 2);
```

robots.txt: WordPress serves a virtual one; edit via the plugin's file editor or a physical `robots.txt` in the web root (wins over virtual). Admin-only checks for the playbook:
- Settings → Reading → "Discourage search engines" **unchecked** in production (it adds noindex everywhere).
- Settings → Permalinks → "Post name" (not `?p=123`).
- Plugin: noindex tag/date/author archives if thin; disable attachment pages (Yoast does by default).
- Media: upload WebP/AVIF, set alt text; consider a performance plugin (caching + image optimization) — one, not three.

## Shopify

Online Store 2.0 themes (Dawn and descendants). Core head in `layout/theme.liquid`:

```liquid
<title>{{ page_title }}{% if current_tags %} &ndash; tagged "{{ current_tags | join: ', ' }}"{% endif %}{% if current_page != 1 %} &ndash; Page {{ current_page }}{% endif %}{% unless page_title contains shop.name %} &ndash; {{ shop.name }}{% endunless %}</title>
{% if page_description %}<meta name="description" content="{{ page_description | escape }}">{% endif %}
<link rel="canonical" href="{{ canonical_url }}">
{% render 'meta-tags' %}
```

Dawn's `snippets/meta-tags.liquid` outputs `og:*` and `twitter:*` from `page_image`, `settings.share_image`, and product data. Fix there rather than adding new tags.

Structured data: Dawn includes product JSON-LD via `{{ product | structured_data }}` in `sections/main-product.liquid` (and `{{ shop | structured_data }}` elsewhere in newer versions). Older themes hand-write it. Check what exists and fill gaps:
- `Product` with `offers` per variant (`price`, `priceCurrency`, `availability`, `url` with `?variant=`), `brand`, `sku`/`gtin` (from barcode), `image`.
- `MerchantReturnPolicy` and `OfferShippingDetails` are now best configured in Merchant Center; on-page markup is optional.
- `Organization` with logo + `sameAs` in `theme.liquid` on the home page (`{% if request.page_type == 'index' %}`).
- `BreadcrumbList` in product/collection templates.
- Only include `aggregateRating` if a reviews app provides real reviews (most apps inject their own markup — avoid duplicating).

robots.txt: Shopify generates it; customize via `templates/robots.txt.liquid`, keeping the default groups:

```liquid
{% for group in robots.default_groups %}
  {{- group.user_agent }}
  {%- for rule in group.rules %}
{{ rule }}
  {%- endfor %}
  {%- if group.user_agent.value == '*' %}
{{ 'Disallow: /*?q=*' }}
  {%- endif %}
  {%- if group.sitemap != blank %}
{{ group.sitemap }}
  {%- endif %}
{% endfor %}
```

Sitemap: automatic at `/sitemap.xml` (not editable). Admin steps for the playbook: per-product "Search engine listing" title/description, alt text on product images, Online Store → Preferences (home title/description, social sharing image), remove the storefront password before launch, connect Google & YouTube channel / Merchant Center. Duplicate URLs (`/collections/x/products/y` vs `/products/y`) are canonicalized by Shopify; make internal product links use `{{ product.url }}` without the collection prefix where the theme allows (`within: collection` creates the nested form).

## Webflow

Mostly UI configuration — put click-paths in the playbook:
- Site settings → SEO: auto-generate sitemap on, robots.txt content, canonical tag URL (set to `https://www.example.com`), redirects (301 table).
- Site settings → Publishing: default domain set to the canonical host (other hosts redirect).
- Page settings: SEO title/description, Open Graph image; CMS collection templates bind them to fields (`{{Name}} · Brand`).
- Custom code → Head: JSON-LD for Organization/WebSite; CMS template pages can embed JSON-LD with field bindings in page-level custom code.
- Alt text in Asset manager; use Webflow's responsive images and lazy loading (default).
- Staging `*.webflow.io` subdomain: disable indexing in Site settings → SEO.

## Ghost

Ghost core emits title, meta description, canonical, OG/Twitter, JSON-LD (`Article`, `Person`, `Organization`), `sitemap.xml` and `robots.txt` via `{{ghost_head}}`. Theme must call `{{ghost_head}}` in `<head>` and `{{ghost_foot}}` before `</body>`, and must not hand-write duplicate meta. Per-post SEO, social cards, canonical override and code injection are in the post settings. Custom `robots.txt`: add a `robots.txt` file at the theme root. Membership/paywalled content: keep a public preview above the paywall so pages aren't thin.

## Wix and Squarespace

No code access in the repo — produce a configuration checklist instead:
- **Wix**: SEO Settings (SEO patterns per page type, sitemap, robots.txt editor, structured data markup per page), SEO Setup Checklist, connect Search Console from the dashboard, 301 redirect manager.
- **Squarespace**: Settings → SEO (site title/description formats), per-page SEO tab, Social image, Code Injection (header) for JSON-LD, URL mappings (301s). Sitemap at `/sitemap.xml` automatic; robots.txt not editable (limited AI-crawler toggle in settings).

## Headless CMS (Sanity, Contentful, Strapi, others)

Add a reusable SEO object to every routable document type, then wire it into the frontend's metadata (see the frontend framework file).

Sanity (`schemas/seo.ts`):

```ts
import { defineType, defineField } from 'sanity'

export const seo = defineType({
  name: 'seo',
  title: 'SEO',
  type: 'object',
  fields: [
    defineField({ name: 'title', type: 'string', validation: (r) => r.max(60).warning('Keep under ~60 characters') }),
    defineField({ name: 'description', type: 'text', rows: 3, validation: (r) => r.max(160).warning('Keep under ~160 characters') }),
    defineField({ name: 'ogImage', type: 'image', options: { hotspot: true }, description: '1200×630' }),
    defineField({ name: 'noindex', type: 'boolean', initialValue: false }),
    defineField({ name: 'canonical', type: 'url', description: 'Only if this content lives primarily elsewhere' }),
  ],
})
// in post/page schemas: defineField({ name: 'seo', type: 'seo' })
```

Contentful: an "SEO" content type with the same fields, referenced from Page/Post (single reference). Strapi: the official SEO plugin or a `shared.seo` component added to collection types. Every CMS: also ensure `slug` (unique, validated), `updatedAt` exposure for sitemap `lastmod`, image `alt` fields required.

Frontend wiring: `seo.title ?? doc.title`, `seo.description ?? excerpt`, `seo.ogImage ?? doc.mainImage ?? site default`; sitemap from a CMS query of all published, non-noindexed slugs; rebuild/revalidate on publish via the CMS webhook (Next.js `revalidateTag`/`revalidatePath`, Netlify/Vercel build hooks). Preview/draft routes must be noindexed and excluded from sitemaps.

## Structured data (all)

- Use the plugin/platform graph as the base; extend it, don't duplicate it. Two `Organization` nodes with different names/logos confuse entity understanding.
- Test with Google's Rich Results Test on a live URL after changes (templates can't be tested pre-deploy on hosted platforms — say so in the playbook).

## Verify (all)

```bash
python3 <skill-dir>/scripts/seo_audit.py https://www.example.com --crawl 50
python3 <skill-dir>/scripts/validate_jsonld.py https://www.example.com/
curl -s https://www.example.com/robots.txt
curl -s https://www.example.com/sitemap.xml | head        # WP core: /wp-sitemap.xml ; Yoast/Rank Math: /sitemap_index.xml
curl -s https://www.example.com/ | grep -c 'og:title'     # expect 1
```

Shopify theme dev: `shopify theme dev` then audit `http://127.0.0.1:9292`. WordPress local (wp-env/LocalWP): audit the local URL.

## Pitfalls (all)

- Two SEO plugins, or a theme + plugin both printing OG/canonical tags → duplicate/conflicting tags.
- WordPress "Discourage search engines" left on after launch; Shopify storefront password left on; Webflow staging domain indexed.
- Thin auto-generated archives (WordPress tag/date/author archives, Shopify tag-filtered collection URLs) indexed at scale.
- Review apps injecting `AggregateRating` alongside the theme's own → duplicate/conflicting product markup.
- Changing permalink structure or product handles without 301 redirects.
- Page builders producing multiple `<h1>`s and enormous DOMs (INP/LCP problems) — note in the playbook.
