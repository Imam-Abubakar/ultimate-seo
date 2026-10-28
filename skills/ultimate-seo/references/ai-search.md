# AI Search Readiness Reference (GEO / AEO)

How AI answer engines discover, read, and cite websites — and what a site can do to be included and cited accurately. Classic SEO is still the foundation: most AI answers are grounded in a traditional search index.

> This area moves fast. Crawler names, policies and products change several times a year. Every table here should be treated as "verify against current docs" — links are given per vendor.

## Contents

1. How AI answer engines source content
2. AI crawler user-agent table
3. Choosing a robots.txt policy
4. Controls beyond robots.txt
5. llms.txt
6. Rendering: why server HTML matters even more
7. Content patterns that get cited
8. Entity clarity
9. Measuring AI visibility and referrals
10. Checklist

---

## 1. How AI answer engines source content

| Engine | Where answers come from | Implication |
|---|---|---|
| **Google AI Overviews / AI Mode** | Google's search index (Googlebot); query fan-out to many sub-queries | Rank and be indexable in Google; no separate opt-in. Control snippet use with `nosnippet`/`max-snippet`/`data-nosnippet`. |
| **ChatGPT search** | OpenAI's index (OAI-SearchBot) + Bing and partner data; live fetches by ChatGPT-User | Allow OAI-SearchBot; be indexed in Bing. |
| **Microsoft Copilot** | Bing index (Bingbot) | Bing Webmaster Tools verification, IndexNow, Bing indexing. |
| **Perplexity** | Own index (PerplexityBot) + live fetches (Perplexity-User) + search APIs | Allow PerplexityBot. |
| **Claude (web search)** | Search provider results + Anthropic crawlers (Claude-SearchBot) + live fetches (Claude-User) | Allow Claude-SearchBot / Claude-User. |
| **Gemini app** | Google index/grounding | Google-Extended governs training/grounding use for Gemini, not Search. |
| **Apple Intelligence / Siri** | Applebot | Applebot-Extended governs training use. |

Common thread: answers are assembled from pages that (a) are in an index, (b) are fetchable without JS, (c) contain a passage that directly answers a sub-question, and (d) come from sources the system trusts for that topic.

---

## 2. AI crawler user-agent table

Purpose categories: **Training** (collect data to train models), **Search** (build an index used to cite/link in answers), **User** (fetch triggered by a user's request in real time).

| User-agent token | Operator | Purpose | Respects robots.txt? | Docs |
|---|---|---|---|---|
| `GPTBot` | OpenAI | Training | Yes | platform.openai.com/docs/bots |
| `OAI-SearchBot` | OpenAI | Search (ChatGPT search results) | Yes | platform.openai.com/docs/bots |
| `ChatGPT-User` | OpenAI | User-triggered fetches | Treated as user action; OpenAI has said robots.txt may not apply — verify | platform.openai.com/docs/bots |
| `ClaudeBot` | Anthropic | Training | Yes | support.claude.com (search "crawler") |
| `Claude-SearchBot` | Anthropic | Search | Yes | same |
| `Claude-User` | Anthropic | User-triggered fetches | Yes | same |
| `PerplexityBot` | Perplexity | Search index (not training, per Perplexity) | Yes | docs.perplexity.ai/guides/bots |
| `Perplexity-User` | Perplexity | User-triggered fetches | Generally ignores robots.txt (user-initiated) | docs.perplexity.ai/guides/bots |
| `Google-Extended` | Google | **Robots token only, not a crawler.** Controls use of content crawled by Googlebot for Gemini training and grounding. Does **not** affect Google Search or AI Overviews. | n/a | developers.google.com/search/docs/crawling-indexing/google-common-crawlers |
| `Applebot` | Apple | Search (Siri, Spotlight) | Yes | support.apple.com/en-us/119829 |
| `Applebot-Extended` | Apple | Token: opt out of Apple model training | n/a (token) | same |
| `CCBot` | Common Crawl | Open web corpus (heavily used for training) | Yes | commoncrawl.org/ccbot |
| `Bytespider` | ByteDance | Training | Reported to be inconsistent | — |
| `meta-externalagent` | Meta | Training / AI products | Yes | developers.facebook.com/docs/sharing/webmasters/web-crawlers |
| `meta-externalfetcher` | Meta | User-triggered fetches | May bypass | same |
| `Amazonbot` | Amazon | Alexa/AI answers, may be used for training | Yes | developer.amazon.com/amazonbot |
| `DuckAssistBot` | DuckDuckGo | User-triggered answer fetches | Yes | duckduckgo.com/duckduckgo-help-pages |
| `MistralAI-User` | Mistral | User-triggered | — | docs.mistral.ai |
| `Bingbot` | Microsoft | Search + Copilot | Yes | bing.com/webmasters |
| `Googlebot` | Google | Search + AI Overviews/AI Mode | Yes | developers.google.com/search |

User agents can be spoofed; vendors publish IP ranges (OpenAI, Anthropic, Perplexity, Google, Bing) for verification. Cloudflare and other CDNs offer managed AI-crawler controls (and some block AI training bots by default on new zones — check the CDN dashboard if crawlers report 403s).

---

## 3. Choosing a robots.txt policy

Make the policy **deliberate and documented** in `ULTIMATE-SEO.md`. Remember: a crawler obeys only its most specific `User-agent` group, so any rules from `*` that should also apply to a named bot must be repeated in that bot's group.

**Policy A — Allow all (default recommendation for most businesses, SaaS, local, e-commerce)**
Maximizes the chance of being cited and linked in AI answers. Training inclusion also helps models "know" the brand.

```txt
User-agent: *
Allow: /
Disallow: /api/
Disallow: /admin/

Sitemap: https://www.example.com/sitemap.xml
```

**Policy B — Allow search/answer bots, block training (publishers, original-content creators, premium content)**
Keeps citations and referral traffic while opting out of model training.

```txt
User-agent: *
Allow: /
Disallow: /api/

# AI training crawlers — opt out
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: CCBot
User-agent: Bytespider
User-agent: meta-externalagent
User-agent: Google-Extended
User-agent: Applebot-Extended
Disallow: /

# AI search / answer crawlers — explicitly allowed
User-agent: OAI-SearchBot
User-agent: ChatGPT-User
User-agent: Claude-SearchBot
User-agent: Claude-User
User-agent: PerplexityBot
User-agent: Perplexity-User
Allow: /
Disallow: /api/

Sitemap: https://www.example.com/sitemap.xml
```

Trade-off: blocking `Google-Extended` may reduce use of your content in Gemini grounding; it does not affect Google Search. Blocking training bots means models may know less about your brand over time.

**Policy C — Block all AI (rarely right for a business site)**
Use only for strong legal/licensing reasons. Note you **cannot** opt out of Google AI Overviews without also limiting regular snippets (`nosnippet`/`max-snippet`) or leaving Google Search.

---

## 4. Controls beyond robots.txt

- **Google**: `nosnippet`, `max-snippet:N`, and `data-nosnippet` apply to AI Overviews/AI Mode as well as classic snippets. `noindex` removes the page entirely.
- **Bing/Copilot**: `<meta name="robots" content="nocache">` limits Copilot to titles/URLs/snippets; `noarchive` excludes content from Copilot answers. Verify against current docs: https://blogs.bing.com/webmaster
- **Paywalled content**: use `isAccessibleForFree: false` + `hasPart` with `cssSelector` structured data so it isn't treated as cloaking.
- Emerging standards (IETF AI Preferences / "aipref" vocabulary, Content Signals in robots.txt, TDM-Rep) let sites express training vs search preferences in a machine-readable way. Adoption by AI vendors is partial — use as a supplement, not a replacement, for user-agent rules.

---

## 5. llms.txt

**What it is**: a proposal (llmstxt.org, Jeremy Howard, 2024) for a Markdown file at `/llms.txt` that gives LLMs a concise, curated map of a site: name, summary, and links to the most useful pages (ideally to clean Markdown versions).

**Honest status (late 2026)**: it is a community proposal, not a standard. Major AI search engines have **not** confirmed using it as a ranking or retrieval signal, and Google has said it doesn't use it. It is widely adopted by developer-tool and docs sites, used by some coding agents and IDE integrations, and is cheap to add. Treat it as low-cost, low-certainty upside — never as a substitute for crawlable HTML.

**Format**:

```markdown
# Acme

> Acme is invoicing software for freelancers and small agencies: create invoices, accept card and bank payments, and automate late-payment reminders.

Key facts: founded 2021, based in London, free plan for up to 5 clients, paid plans from $12/month.

## Product
- [Features](https://www.example.com/features): Invoicing, recurring billing, reminders, multi-currency
- [Pricing](https://www.example.com/pricing): Plans and limits

## Docs
- [Getting started](https://www.example.com/docs/getting-started.md): Create your first invoice in 5 minutes
- [API reference](https://www.example.com/docs/api.md): REST API for invoices and clients

## Optional
- [Blog](https://www.example.com/blog): Guides on freelancing finances
```

Rules: H1 with the name (required), blockquote summary, optional prose, H2 sections of link lists (`- [title](url): note`), an `## Optional` section for lower-priority links. Keep it accurate and short; generate from the same source as the sitemap when possible. `llms-full.txt` (full concatenated content) is an optional companion for docs sites. Template: `assets/llms.txt`.

Docs sites: serving `.md` versions of pages (e.g. `/docs/page.md`) is the most useful part of the proposal for agents.

---

## 6. Rendering: why server HTML matters even more

Most AI crawlers (GPTBot, ClaudeBot, PerplexityBot, CCBot, and user-triggered fetchers) **do not execute JavaScript**. A client-rendered SPA shows them an empty `<div id="root">`. Googlebot renders JS, but AI products relying on other crawlers will not see your content.

- SSR/SSG/prerender all public content.
- Main content, headings, and key facts in HTML — not in images, canvases, or tabs loaded on click.
- Test: `curl -A "GPTBot" -s https://site/page | sed 's/<[^>]*>//g' | grep -c "your key phrase"`.
- Don't block AI crawlers by accident with bot-protection/WAF rules or CDN defaults if Policy A/B is chosen.
- Fast responses: user-triggered fetchers have short timeouts.

---

## 7. Content patterns that get cited

AI systems extract **passages**, not pages. Make each section independently quotable.

- **Answer first**: put a direct 1–3 sentence answer immediately under each question-style heading, then elaborate. ("How long does X take? — Typically 3–5 business days…")
- **Question-shaped headings** that mirror real queries (`How much does a website audit cost?`).
- **Definitions**: "X is a …" sentences for core concepts and your product category.
- **Specific, sourced facts**: numbers, dates, prices, limits, comparisons — with citations to primary sources. Original data (surveys, benchmarks) is heavily cited.
- **Structured formats**: comparison tables, step lists, pros/cons, spec tables — easy to extract.
- **Freshness**: visible "Updated" dates and genuinely updated content; AI search favours recent sources for time-sensitive queries.
- **Clear authorship and expertise**: bylines, author pages with credentials, first-hand experience (E-E-A-T applies doubly).
- **Comprehensive coverage of sub-questions** (query fan-out): cover the follow-up questions a user would ask on the same page or tightly linked pages.
- **Consistent facts everywhere**: pricing, features, and company facts identical across your site, docs, profiles, and third-party listings — models reconcile conflicting sources poorly.
- **Third-party presence**: AI answers lean on reviews, comparisons, Reddit/forums, Wikipedia, and industry publications. Earned mentions matter as much as on-site work.
- Avoid: fluff intros, keyword-stuffed text, content hidden behind interaction, mass-produced AI text without original value.

---

## 8. Entity clarity

Help models know *who you are* unambiguously:
- `Organization`/`Person` JSON-LD with `name`, `url`, `logo`, `description`, `sameAs` to all official profiles (LinkedIn, GitHub, Crunchbase, Wikidata, Wikipedia, app stores).
- A thorough **About** page: what you do, who for, founders, location, history, key facts.
- Consistent brand name spelling and one-line description across the web.
- A Wikidata entry when notability allows (factual, sourced — not promotional).
- Product/category pages that state plainly what the product is and how it compares.

---

## 9. Measuring AI visibility and referrals

- **Referral traffic**: in analytics, segment referrers such as `chatgpt.com`, `perplexity.ai`, `claude.ai`, `gemini.google.com`, `copilot.microsoft.com`, `bing.com/chat`. ChatGPT appends `utm_source=chatgpt.com` to many links.
- **Google AI Overviews/AI Mode**: counted inside Search Console Performance (Web search type); no separate filter as of late 2026 — verify against current docs.
- **Bing Webmaster Tools**: Copilot/AI performance reporting (verify current availability).
- **Server logs / CDN bot analytics**: crawl volume by AI user agent, pages fetched, status codes (catch accidental 403s).
- **Prompt tracking**: periodically ask target questions in ChatGPT, Perplexity, Gemini, Claude, Copilot; record whether you're cited and what's said. Dedicated tools (e.g. Profound, Peec AI, Semrush/Ahrefs AI visibility features) automate this.
- Track brand-mention accuracy: wrong facts in AI answers usually trace back to outdated or inconsistent sources — fix the source.

---

## 10. Checklist

- [ ] Deliberate AI crawler policy in robots.txt (Policy A/B/C) and documented in `ULTIMATE-SEO.md`.
- [ ] CDN/WAF not blocking allowed AI crawlers.
- [ ] Public content server-rendered or prerendered; key facts in HTML text.
- [ ] `/llms.txt` with accurate summary and key links (low-cost extra).
- [ ] Organization/Person JSON-LD with `sameAs`; strong About page.
- [ ] Answer-first, question-headed sections on key pages; tables and specifics.
- [ ] Visible updated dates; stale facts refreshed.
- [ ] Bing Webmaster Tools verified and sitemap submitted (powers Copilot and feeds ChatGPT).
- [ ] AI referrers segmented in analytics; quarterly prompt checks.
