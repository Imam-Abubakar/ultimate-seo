# Server-Rendered Backends: Django, Flask, Rails, Laravel, Express, Go, ASP.NET, PHP

Classic server-rendered apps send complete HTML, so crawlers are happy by default. The work is structural: a base template with overridable SEO blocks, a context/helper that supplies defaults, real HTTP status codes, a sitemap generated from the database, and host/redirect canonicalization in the app or proxy. If the backend only serves an API to a SPA frontend, SEO lives in the frontend — see the relevant framework file instead.

## Contents
- Detect
- Universal pattern
- Django
- Flask / Jinja
- Rails
- Laravel
- Express (EJS/Pug/Handlebars)
- Go (html/template)
- ASP.NET Core (Razor)
- Plain PHP
- Structured data (all)
- Verify (all)
- Pitfalls (all)

## Detect

| Stack | Signals |
|---|---|
| Django | `manage.py`, `settings.py`, `django` in requirements/pyproject |
| Flask | `flask` in requirements, `app.py`/`create_app`, `templates/` |
| Rails | `Gemfile` with `rails`, `config/routes.rb`, `app/views/layouts/application.html.erb` |
| Laravel | `artisan`, `composer.json` with `laravel/framework`, `resources/views/` |
| Express | `express` in package.json + `views/` with `.ejs`/`.pug`/`.hbs` |
| Go | `go.mod`, `html/template` imports, `templates/` |
| ASP.NET Core | `*.csproj` with `Microsoft.NET.Sdk.Web`, `Pages/`/`Views/` with `.cshtml` |
| PHP | `*.php` at web root, `index.php`, no framework |

## Universal pattern

1. **Settings**: `SITE_URL` (env), `SITE_NAME`, default description, default OG image.
2. **Base layout** renders the full head from variables with defaults; each view/template overrides `title`, `description`, `canonical`, `og_image`, `robots`, `json_ld`.
3. **Canonical** built from `SITE_URL + request.path` (not `request.host` — that lets any Host header or staging domain leak into canonicals).
4. **robots.txt** and **sitemap.xml** as routes, generated from models with real `updated_at`.
5. **Status codes**: missing records → 404 (not a 200 "not found" template), moved → 301, gone → 410.
6. **Host canonicalization**: one 301 from apex/http to the canonical origin, in the proxy (Nginx/Caddy/CDN) or middleware.
7. Escape JSON-LD: serialize with the platform's JSON encoder and escape `<`, `>`, `&` (`json_script`-style).

## Django

`settings.py`:

```python
SITE_URL = os.environ.get("SITE_URL", "https://www.example.com").rstrip("/")
SITE_NAME = "Example"
SEO_DEFAULT_DESCRIPTION = "Default description, ~150 chars."
INSTALLED_APPS += ["django.contrib.sitemaps"]
# optional: SECURE_SSL_REDIRECT = True; PREPEND_WWW = True (if www is canonical)
```

Context processor (`core/context_processors.py`), registered in `TEMPLATES[...]["OPTIONS"]["context_processors"]`:

```python
from django.conf import settings

def seo(request):
    return {
        "SITE_URL": settings.SITE_URL,
        "SITE_NAME": settings.SITE_NAME,
        "canonical_url": settings.SITE_URL + request.path,
        "default_description": settings.SEO_DEFAULT_DESCRIPTION,
    }
```

`templates/base.html`:

```django
<!doctype html>
<html lang="{{ LANGUAGE_CODE|default:'en' }}">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}{{ SITE_NAME }}{% endblock %}</title>
  <meta name="description" content="{% block description %}{{ default_description }}{% endblock %}">
  <link rel="canonical" href="{% block canonical %}{{ canonical_url }}{% endblock %}">
  {% block robots %}{% endblock %}
  <meta property="og:title" content="{% block og_title %}{{ SITE_NAME }}{% endblock %}">
  <meta property="og:description" content="{% block og_description %}{{ default_description }}{% endblock %}">
  <meta property="og:url" content="{{ canonical_url }}">
  <meta property="og:image" content="{% block og_image %}{{ SITE_URL }}/static/og-default.png{% endblock %}">
  <meta property="og:type" content="{% block og_type %}website{% endblock %}">
  <meta name="twitter:card" content="summary_large_image">
  {% block json_ld %}{% endblock %}
</head>
```

Page template:

```django
{% extends "base.html" %}
{% block title %}{{ post.title }} · {{ SITE_NAME }}{% endblock %}
{% block description %}{{ post.excerpt|truncatechars:160 }}{% endblock %}
{% block og_type %}article{% endblock %}
{% block json_ld %}{{ post_schema|json_script:"post-schema" }}{% endblock %}
```

Note `json_script` outputs `<script id="post-schema" type="application/json">`, which is **not** JSON-LD. Use a small filter instead:

```python
# core/templatetags/seo.py
import json
from django import template
from django.utils.safestring import mark_safe
register = template.Library()

@register.filter
def jsonld(value):
    data = json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{data}</script>')
```

`{% load seo %}{{ post_schema|jsonld }}`.

Views: `get_object_or_404(Post, slug=slug, published=True)` gives real 404s.

Sitemaps (`core/sitemaps.py`):

```python
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import Post

class StaticSitemap(Sitemap):
    def items(self): return ["home", "about", "pricing"]
    def location(self, item): return reverse(item)

class PostSitemap(Sitemap):
    def items(self): return Post.objects.filter(published=True)
    def lastmod(self, obj): return obj.updated_at
```

`urls.py`:

```python
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
urlpatterns += [
    path("sitemap.xml", sitemap, {"sitemaps": {"static": StaticSitemap, "posts": PostSitemap}}, name="sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("llms.txt", TemplateView.as_view(template_name="llms.txt", content_type="text/plain")),
]
```

Django's sitemap uses the `django.contrib.sites` domain (or the request host if `sites` isn't installed) — set the `Site` object's domain to the production host, or set `protocol = "https"` on sitemap classes. `templates/robots.txt` ends with `Sitemap: {{ SITE_URL }}/sitemap.xml` (needs the context processor; `TemplateView` uses `RequestContext`, so it works). Wagtail: use `wagtail.contrib.sitemaps` and page `seo_title`/`search_description` fields.

## Flask / Jinja

```python
@app.context_processor
def inject_seo():
    site = app.config["SITE_URL"].rstrip("/")
    return {"SITE_URL": site, "SITE_NAME": app.config["SITE_NAME"], "canonical_url": site + request.path}

@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nDisallow: /admin\n\nSitemap: {app.config['SITE_URL']}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    posts = Post.query.filter_by(published=True).all()
    xml = render_template("sitemap.xml", posts=posts)
    return Response(xml, mimetype="application/xml")

@app.route("/blog/<slug>")
def post(slug):
    post = Post.query.filter_by(slug=slug, published=True).first_or_404()
    return render_template("post.html", post=post)
```

`base.html` uses `{% block title %}`/`{% block description %}` like Django. JSON-LD: `<script type="application/ld+json">{{ schema | tojson }}</script>` — Jinja's `tojson` escapes `<`, `>`, `&`, `'` for safe embedding. FastAPI + Jinja2Templates: same templates, routes with `PlainTextResponse`/`Response(media_type="application/xml")`.

## Rails

Layout `app/views/layouts/application.html.erb`:

```erb
<title><%= content_for?(:title) ? "#{yield(:title)} · #{Rails.configuration.x.site_name}" : Rails.configuration.x.site_name %></title>
<meta name="description" content="<%= content_for?(:description) ? yield(:description) : t('seo.default_description') %>">
<link rel="canonical" href="<%= Rails.configuration.x.site_url + request.path %>">
<%= yield(:robots) %>
<meta property="og:title" content="<%= content_for?(:title) ? yield(:title) : Rails.configuration.x.site_name %>">
<meta property="og:image" content="<%= content_for?(:og_image) ? yield(:og_image) : image_url('og-default.png') %>">
<meta name="twitter:card" content="summary_large_image">
<%= yield(:json_ld) %>
```

`config/application.rb`: `config.x.site_url = ENV.fetch("SITE_URL", "https://www.example.com")`, `config.x.site_name = "Example"`. Set `config.action_controller.asset_host`/`default_url_options[:host]` so `image_url` is absolute and correct.

View:

```erb
<% content_for :title, @post.title %>
<% content_for :description, truncate(strip_tags(@post.excerpt), length: 160) %>
<% content_for :json_ld do %>
  <script type="application/ld+json"><%= raw json_escape(@post.schema.to_json) %></script>
<% end %>
```

(`json_escape` escapes `<`, `>`, `&` for safe embedding.) The `meta-tags` gem (`set_meta_tags` / `display_meta_tags`) is a well-established alternative if the project prefers a helper.

Controllers: `Post.published.find_by!(slug: params[:slug])` → `ActiveRecord::RecordNotFound` → 404 in production.

Sitemap: `sitemap_generator` gem — `config/sitemap.rb`:

```ruby
SitemapGenerator::Sitemap.default_host = ENV.fetch("SITE_URL")
SitemapGenerator::Sitemap.create do
  add about_path
  Post.published.find_each { |p| add post_path(p), lastmod: p.updated_at }
end
```

Run `rake sitemap:refresh:no_ping` on deploy/cron (search engines retired sitemap ping endpoints; submit in Search Console instead). Writes to `public/sitemap.xml.gz` by default — make sure `robots.txt` points at the real file name, or serve a dynamic `sitemap.xml` route with a builder view for small sites. `public/robots.txt` is static; for env-dependent rules, route `get "/robots.txt" => "seo#robots"` and delete the static file.

## Laravel

Layout `resources/views/layouts/app.blade.php`:

```blade
<title>@hasSection('title')@yield('title') · {{ config('app.name') }}@else{{ config('app.name') }}@endif</title>
<meta name="description" content="@yield('description', config('seo.description'))">
<link rel="canonical" href="@yield('canonical', url()->current())">
@stack('robots')
<meta property="og:title" content="@yield('og_title', config('app.name'))">
<meta property="og:image" content="@yield('og_image', asset('og-default.png'))">
<meta name="twitter:card" content="summary_large_image">
@stack('jsonld')
```

`url()->current()` uses `APP_URL`-based generation only when `URL::forceRootUrl(config('app.url'))` is set in a service provider — do that (plus `URL::forceScheme('https')` in production) so canonicals use the production host. View:

```blade
@section('title', $post->title)
@section('description', Str::limit(strip_tags($post->excerpt), 160))
@push('jsonld')
<script type="application/ld+json">{!! json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP) !!}</script>
@endpush
```

Routes: `Post::where('slug', $slug)->published()->firstOrFail()` → 404. Sitemap: `spatie/laravel-sitemap`:

```php
use Spatie\Sitemap\Sitemap;
use Spatie\Sitemap\Tags\Url;

Sitemap::create()
    ->add(Url::create('/'))
    ->add(Post::published()->get()->map(fn ($p) => Url::create(route('posts.show', $p))->setLastModificationDate($p->updated_at)))
    ->writeToFile(public_path('sitemap.xml'));
```

Run from an Artisan command scheduled daily. `artesaos/seotools` is an alternative helper package.

## Express (EJS/Pug/Handlebars)

```js
app.use((req, res, next) => {
  res.locals.site = { url: process.env.SITE_URL, name: 'Example', description: 'Default…' };
  res.locals.seo = { canonical: process.env.SITE_URL + req.path };
  next();
});

app.get('/robots.txt', (req, res) =>
  res.type('text/plain').send(`User-agent: *\nAllow: /\n\nSitemap: ${process.env.SITE_URL}/sitemap.xml\n`));

app.get('/blog/:slug', async (req, res, next) => {
  const post = await Post.findPublished(req.params.slug);
  if (!post) return res.status(404).render('404');
  res.render('post', { post, seo: { ...res.locals.seo, title: post.title, description: post.excerpt } });
});
```

EJS head: `<title><%= seo.title ? seo.title + ' · ' + site.name : site.name %></title>`; JSON-LD with `<%- JSON.stringify(schema).replace(/</g, '\\u003c') %>`. A 404 catch-all `app.use((req, res) => res.status(404).render('404'))` after all routes. Sitemap: build XML in a route (or the `sitemap` npm package's `SitemapStream`).

## Go (html/template)

`html/template` is context-aware: inside `<script type="application/ld+json">` it JSON-escapes values, so pass a struct/map rather than a pre-marshaled string.

```go
type SEO struct {
    Title, Description, Canonical, OGImage string
    NoIndex bool
    JSONLD  any
}
```

```gotemplate
<title>{{.SEO.Title}}</title>
<meta name="description" content="{{.SEO.Description}}">
<link rel="canonical" href="{{.SEO.Canonical}}">
{{if .SEO.NoIndex}}<meta name="robots" content="noindex, follow">{{end}}
{{with .SEO.JSONLD}}<script type="application/ld+json">{{.}}</script>{{end}}
```

Handlers: `http.NotFound` / `w.WriteHeader(http.StatusNotFound)` before rendering the 404 template. Sitemap: `encoding/xml` with a `urlset` struct, or `text/template`.

## ASP.NET Core (Razor)

`_Layout.cshtml`:

```cshtml
<title>@(ViewData["Title"] is string t ? $"{t} · Example" : "Example")</title>
<meta name="description" content="@(ViewData["Description"] ?? "Default description")" />
<link rel="canonical" href="@($"{Configuration["SiteUrl"]}{Context.Request.Path}")" />
@await RenderSectionAsync("Head", required: false)
```

Page: `ViewData["Title"] = Model.Post.Title;` and `@section Head { <script type="application/ld+json">@Html.Raw(JsonSerializer.Serialize(Model.Schema))</script> }` — `System.Text.Json`'s default encoder escapes `<`/`>`/`&` as `<` etc., so the raw output is safe. Return `NotFound()` for missing entities; `app.UseStatusCodePagesWithReExecute("/Error/{0}")` keeps the 404 status. Sitemap via a controller action returning `Content(xml, "application/xml")`. Host canonicalization: `app.UseRewriter(new RewriteOptions().AddRedirectToHttpsPermanent().AddRedirectToWwwPermanent())` (or non-www variant).

## Plain PHP

`includes/head.php` reading `$seo` array with defaults (`$seo['title'] ?? SITE_NAME`), `htmlspecialchars()` every value, JSON-LD with `json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP)`. 404s: `http_response_code(404); include '404.php'; exit;`. `sitemap.php` + rewrite `RewriteRule ^sitemap\.xml$ sitemap.php [L]` in `.htaccess`, `header('Content-Type: application/xml; charset=utf-8')`.

## Structured data (all)

Build schema objects as native dicts/hashes/arrays in the view-model, serialize with the platform JSON encoder plus `<`/`>`/`&` escaping, and render in the head block. Home: `Organization` + `WebSite`; detail pages: the matching type + `BreadcrumbList`. Templates: `assets/jsonld/`.

## Verify (all)

```bash
# start the app locally (examples)
python manage.py runserver 8000 | bin/rails s -p 3000 | php artisan serve | node server.js | go run . | dotnet run
python3 <skill-dir>/scripts/seo_audit.py http://localhost:8000 --crawl 50
python3 <skill-dir>/scripts/validate_jsonld.py http://localhost:8000/
curl -s http://localhost:8000/robots.txt; curl -s http://localhost:8000/sitemap.xml | head
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8000/blog/does-not-exist   # 404
```

Also run the project's test suite — adding a context processor or layout block can break existing view tests.

## Pitfalls (all)

- Canonicals built from `request.host` / `request.build_absolute_uri()` behind a proxy → `http://` or internal hostnames. Use the configured `SITE_URL`.
- Debug/staging environments indexable: add `X-Robots-Tag: noindex` header (middleware) on non-production, never rely on robots.txt alone.
- "Not found" pages rendered with 200 — soft 404s. Test with curl.
- Search/filter result pages (`?q=`, `?sort=`) crawlable and canonicalized to themselves → infinite URL space. Noindex or canonicalize to the base listing.
- Sitemaps listing unpublished/draft records — filter by the same predicate as the public view.
- Sitemap ping endpoints (`google.com/ping?sitemap=`) are retired; old gems/scripts that call them just fail — disable pinging.
