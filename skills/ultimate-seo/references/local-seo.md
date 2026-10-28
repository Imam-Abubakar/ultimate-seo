# Local SEO

Use this for any business with a physical location customers visit (store, clinic, restaurant, office) or that serves customers within a geographic area (plumber, cleaner, mobile service). Local rankings ("map pack" and "near me" results) are driven mostly by **relevance, distance, and prominence** — and much of that lives outside the website, in Google Business Profile.

## Contents

1. How local ranking works
2. Google Business Profile (GBP)
3. NAP consistency
4. Citations
5. Reviews strategy (ethical)
6. LocalBusiness structured data
7. Website: location and service pages
8. Multi-location businesses
9. Service-area businesses
10. Local links and prominence
11. Apple Business Connect, Bing Places, and other platforms
12. Playbook items for ULTIMATE-SEO.md

---

## 1. How local ranking works

Google's stated factors (verify against current docs: https://support.google.com/business/answer/7091):
- **Relevance**: how well the profile matches the search (categories, services, description, website content).
- **Distance**: proximity of the business to the searcher or the location in the query. You can't optimize this beyond accurate address/service area.
- **Prominence**: how well-known the business is — reviews (count, rating), links, citations, mentions, organic ranking strength.

The website matters for organic local results and as a prominence/relevance signal for the map pack.

## 2. Google Business Profile (GBP)

This is a human task (requires the owner's Google account and verification). Put it high in the launch checklist.

Setup:
1. Claim/create at https://business.google.com. Verify (video, phone, email, or postcard — Google chooses).
2. **Business name**: exactly the real-world name. Adding keywords/cities ("Joe's Plumbing – Best Plumber Austin") violates guidelines and risks suspension.
3. **Primary category**: the single most specific category that describes the core business (most impactful field). Add relevant secondary categories.
4. **Address** (storefront) or **service area** (SAB, address hidden) — see section 9.
5. **Hours**: regular + special/holiday hours; keep accurate.
6. **Phone**: a local number (call tracking numbers OK as primary if the main number is listed as additional).
7. **Website**: link to the home page or the specific location page (multi-location). Optionally add UTM parameters to track GBP traffic in analytics (`?utm_source=google&utm_medium=organic&utm_campaign=gbp`).
8. **Services/products**: list all with descriptions and prices where possible.
9. **Description**: 750 chars, what you do, who for, where; no links or promos.
10. **Attributes**: accessibility, amenities, identity attributes as applicable.
11. **Photos**: real exterior, interior, team, work examples; add regularly. Logo + cover.
12. **Posts/updates**: offers, events, news — weekly or biweekly keeps the profile active.
13. **Q&A**: seed genuinely common questions and answer them (feature availability varies; verify current GBP UI).
14. **Messaging/booking** links if relevant.

Ongoing: respond to every review, update hours for holidays, add photos monthly, monitor suggested edits from Google/users (competitors and users can propose changes).

## 3. NAP consistency

NAP = Name, Address, Phone. It must be identical (character-level consistency helps) across the website, GBP, schema, and citations.

- Choose a canonical format once: "Suite 200" vs "Ste 200", "St" vs "Street", phone format `+1 512-555-0100` vs `(512) 555-0100`. Document it in ULTIMATE-SEO.md.
- Put NAP in the site footer (or contact page) as real text, not an image.
- Use the same NAP in `LocalBusiness` schema.
- When moving or rebranding: update GBP first, then website, then top citations, then the long tail.

## 4. Citations

Citations = mentions of NAP on other sites (directories, data aggregators, industry sites).

Priority order:
1. **Core platforms**: Google Business Profile, Apple Business Connect, Bing Places, Facebook, Yelp (US), relevant country leaders (e.g. Yell UK, Gelbe Seiten DE, PagesJaunes FR).
2. **Data aggregators** (US): Data Axle, Foursquare, Neustar Localeze — they feed many downstream directories.
3. **Industry-specific**: Healthgrades/Zocdoc (medical), Avvo/Justia (legal), TripAdvisor (hospitality), Houzz/Angi (home services), Clutch (agencies).
4. **Local**: chamber of commerce, local business associations, city directories, local news business listings.

Quality > quantity: 30–50 accurate, relevant citations beat 300 low-quality ones. Tools that help: BrightLocal, Whitespark, Yext, Moz Local, Semrush Listing Management.

## 5. Reviews strategy (ethical)

Reviews (quantity, velocity, rating, recency, and content) are a major prominence signal and a conversion driver.

Do:
- Ask every customer, right after a good experience, with a direct review link (GBP → "Ask for reviews" share link).
- Make it easy: email/SMS follow-up, QR code at checkout/on receipts, link in invoices.
- Respond to every review — thank positive ones specifically, respond to negative ones calmly with resolution steps. Responses are public trust signals.
- Spread across platforms relevant to your industry, but prioritize Google.

Don't (policy violations; can cause review removal or profile suspension, and FTC fines in the US under the 2024 rule banning fake reviews):
- Buy reviews, write fake reviews, or have staff/family review.
- **Review gating** (only asking happy customers / filtering unhappy ones to private feedback before asking for public reviews).
- Offer incentives (discounts, entries) in exchange for reviews on Google.
- Copy third-party reviews into your own `AggregateRating` schema on `LocalBusiness`/`Organization` — Google doesn't show self-serving review stars for these types, and fabricated ratings are a manual-action risk.

## 6. LocalBusiness structured data

Use the most specific subtype of `LocalBusiness` (`Dentist`, `Restaurant`, `Plumber`, `AutoRepair`, `LegalService`, `MedicalClinic`, `HairSalon`, `RealEstateAgent`, etc. — see https://schema.org/LocalBusiness#subtypes). Place on the home page (single location) or each location page (multi-location).

```json
{
  "@context": "https://schema.org",
  "@type": "Plumber",
  "@id": "https://example.com/#business",
  "name": "Example Plumbing Co.",
  "url": "https://example.com/",
  "logo": "https://example.com/logo.png",
  "image": ["https://example.com/images/storefront.jpg"],
  "telephone": "+1-512-555-0100",
  "email": "hello@example.com",
  "priceRange": "$$",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St, Suite 200",
    "addressLocality": "Austin",
    "addressRegion": "TX",
    "postalCode": "78701",
    "addressCountry": "US"
  },
  "geo": { "@type": "GeoCoordinates", "latitude": 30.2672, "longitude": -97.7431 },
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "08:00",
      "closes": "18:00"
    },
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": "Saturday",
      "opens": "09:00",
      "closes": "13:00"
    }
  ],
  "areaServed": [
    { "@type": "City", "name": "Austin" },
    { "@type": "City", "name": "Round Rock" }
  ],
  "sameAs": [
    "https://www.facebook.com/exampleplumbing",
    "https://www.yelp.com/biz/example-plumbing-austin"
  ]
}
```

Notes:
- **Every value must be real.** Use placeholders in config and list them in ULTIMATE-SEO.md if unknown — never invent addresses, phone numbers, coordinates or hours.
- Opening hours: 24-hour `HH:MM`; closed days are simply omitted; open 24h → `"opens": "00:00", "closes": "23:59"`. Seasonal/holiday hours: add a spec with `validFrom`/`validThrough` (closed = `opens` and `closes` both `"00:00"`).
- `geo`: at least 5 decimal places for precision.
- Restaurants: `servesCuisine`, `menu` (URL), `acceptsReservations`.
- Bakeries, cafés, bars: use the specific type (`Bakery`, `CafeOrCoffeeShop`, `BarOrPub` — all `FoodEstablishment` subtypes) with `hasMenu` pointing to the menu page URL; only mark up prices that are printed on the page.
- Service-area businesses: omit street address if hidden on GBP; use `areaServed`.
- Multi-location: one `LocalBusiness` per location page with unique `@id`, and `parentOrganization` pointing to the brand `Organization` `@id`.
- No `aggregateRating`/`review` unless they are genuine first-party reviews collected and displayed on that page (and even then, Google won't show stars for self-serving LocalBusiness/Organization reviews).

Reference: https://developers.google.com/search/docs/appearance/structured-data/local-business (verify against current docs).

## 7. Website: location and service pages

- **Home page**: say what you do and where in the title/H1 ("Emergency Plumber in Austin, TX | Example Plumbing").
- **One page per core service**: `/services/water-heater-repair` with real details — process, pricing guidance, FAQs, photos of actual jobs, testimonials about that service.
- **Contact page**: NAP, embedded map, hours, directions/parking, contact form, click-to-call `tel:` link.
- **Local proof**: photos of the team and location, local projects/case studies, community involvement, local awards, certifications/licenses.
- **Mobile-first**: most local searches are on phones — sticky call button, fast load, tap-to-call, tap-to-navigate.
- Embed the Google Map for the GBP listing on contact/location pages (helps users; minor/no ranking effect — lazy-load the iframe for performance).

## 8. Multi-location businesses

- One **dedicated URL per location**: `/locations/austin-downtown`. Linked from a `/locations` hub (with a store locator that also renders crawlable links — not a JS-only map).
- Each page must be genuinely unique: local NAP, hours, manager/team, photos of that location, local reviews/testimonials, directions, nearby landmarks, location-specific services/inventory/events.
- Each GBP listing links to its own location page.
- Each page has its own `LocalBusiness` schema with `parentOrganization`.
- Avoid template pages where only the city name changes — these are doorway pages.

## 9. Service-area businesses (SABs)

- If customers don't visit your address, hide the address in GBP and set a service area (cities/postcodes; Google recommends staying within ~2 hours' drive).
- You can't rank a map-pack listing everywhere you serve; distance from the verified address still matters.
- Create service-area pages only for major areas where you can add unique value (local projects, area-specific info, testimonials from customers there). A handful of strong pages beats dozens of thin ones.

## 10. Local links and prominence

- Local sponsorships (sports teams, charities, events) — usually come with a link.
- Local press: newsworthy stories, expert commentary to local journalists.
- Chamber of commerce, business associations, BBB (US), local networking groups.
- Partner businesses (supplier/vendor/referral partners) linking to each other where natural.
- Hosting/speaking at local events and meetups.
- Local resource content (e.g. "Austin water hardness guide") that local sites cite.

## 11. Apple Business Connect, Bing Places, and other platforms

- **Apple Business Connect** (https://businessconnect.apple.com): controls Apple Maps, Siri, and Spotlight results — important given iPhone share. Claim, verify, add photos/hours, "Showcases" for promos.
- **Bing Places** (https://www.bingplaces.com): import from GBP in a few clicks. Bing data also powers some AI assistants and other surfaces.
- **Facebook page**, **Yelp**, **Nextdoor** (neighborhood services), and industry platforms.
- AI assistants increasingly answer "best X near me" using map data, review platforms, and the web — consistent NAP and strong reviews across platforms help here too.

## 12. Playbook items for ULTIMATE-SEO.md

- [ ] Claim + verify Google Business Profile; set primary category; complete every field (owner action).
- [ ] Claim Apple Business Connect and Bing Places (import from GBP).
- [ ] Document the canonical NAP format; ensure website footer, contact page, schema, and GBP match exactly.
- [ ] Confirm the `LocalBusiness` schema values (placeholders listed in "Configuration you must fill in").
- [ ] Build/verify citations on the top 10–20 platforms for this industry and country.
- [ ] Set up a review request flow (email/SMS/QR) with the GBP review link; respond to all reviews within 48h.
- [ ] One page per core service; location pages only for real locations with unique content.
- [ ] Add GBP UTM link to track GBP traffic in analytics.
- [ ] Monthly: add GBP photos and posts, check for suggested edits, review GBP Performance (calls, directions, website clicks).
- [ ] Quarterly: audit citations for NAP drift; pursue 2–3 local link opportunities.
