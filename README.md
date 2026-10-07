# Buffalo Plumbing PROS — Astro site

Static [Astro](https://astro.build) rebuild of the legacy `pbmplumbingco.com` site for **buffaloplumbingpros.com**.
Same 45 URLs, same copy, new design. Deployed on Cloudflare Pages.

```
npm install
npm run dev        # http://localhost:4321
npm run build      # → dist/   (46 pages: 45 legacy URLs + 404)
npm run preview
npm run check      # astro check (types)
```

## Deploy (Cloudflare Pages)

| Setting | Value |
| --- | --- |
| Production branch | the branch holding this code (e.g. `astro-version`) |
| Framework preset | Astro |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Node | 22 (`.nvmrc` / `.node-version`; or set env `NODE_VERSION=22`) |
| Env var (optional) | `PUBLIC_GA_MEASUREMENT_ID` = your GA4 ID (see *Analytics*) |

Then add `buffaloplumbingpros.com` under **Custom domains**. The old-domain → new-domain redirect is configured in Cloudflare
(Redirect Rules); this repo does not do it.

URLs are identical to the legacy site because `build.format: 'preserve'` emits `services/<slug>.html` (served by Cloudflare Pages at
the extensionless `/services/<slug>`) and `blog/index.html` (served at `/blog/`). The four legacy image URLs under `/images/` are kept
in `public/images/` so any image-search results still resolve.

## What lives where

```
src/
  config/site.ts          Business facts (name, phone, e-mail, address, hours, domain, GA id, map helpers). Change here → changes everywhere.
  config/states.ts        All 50 states + D.C. + Puerto Rico → <code>.buffaloplumbingpros.com links, map tile positions
  content/                ALL page copy, as JSON, extracted verbatim from the legacy HTML (see "Content" below)
    services/ areas/ blog/   one JSON file per page, validated by schemas in src/content.config.ts
    pages/home.json, blog-index.json, nav.json
  pages/                  index, services/[slug], service-area/[slug], blog/index, blog/[slug], 404,
                          sitemap.xml, sitemap-index.xml, robots.txt, llms.txt
  layouts/Base.astro      <head> (canonical, OG/Twitter, JSON-LD, GA4), skip link, header, footer, mobile call bar
  components/             Header (mega menus), Footer, StatesSection (tile map + A–Z), InnerHero, Prose, FaqList, Process, MapSection/MapEmbed, ServiceCard, …
  lib/schema.ts           JSON-LD builders (Plumber, WebSite, WebPage, Service, FAQPage, BreadcrumbList, BlogPosting, Place)
  lib/media.ts            photo registry, accurate alt text, which photo suits which service page
  lib/prose.ts            adds heading ids + table wrappers to legacy body HTML (never changes wording)
  assets/photos|brand/    optimised sources (Astro builds AVIF/WebP + srcset at build time)
  styles/global.css       design tokens (navy / signal blue / amber), typography, prose styles
public/                   favicons, OG image, _headers, site.webmanifest, legacy /images
scripts/                  extract_legacy_content.py · prepare_media.py · swap_photo.py · verify_parity.py
```

### Content

Copy is data, not markup. To edit a page's wording, edit its JSON in `src/content/…` (`bodyHtml` holds the body HTML).
`scripts/extract_legacy_content.py` was the one-time extraction from the legacy `main` branch; it is kept for auditability and
needs the legacy files (`git archive main | tar -x -C /tmp/legacy`). It is **not** part of the build.

### Media

`scripts/prepare_media.py <unzipped webp pack>` re-encodes the "Buffalo Plumbing PROS media pack" photos, builds transparent
logo variants (navy for light backgrounds, white for dark), cuts the trust badges out of their white backdrops, and generates the
favicons and `og-default.jpg`. The GBP-optimised (EXIF) JPG pack is for Google Business Profile uploads and is intentionally not used
on the site. `Conversion Graphics/Overlay 2` (a mock "5-star verified customer" review card) is not used.

### Phone number

The business number lives in `SITE.phone` / `SITE.phoneE164` (`src/config/site.ts`) and in the page copy (extracted JSON). It is currently
**(716) 663-0186**. The media pack was generated with the previous number printed on it, so `scripts/phone_retouch.py` redraws the new
number on the six images that carried it — `van-1`, `van-2`, `technician-unloading`, `business-exterior` and both trust badges (the
social-share image is built from the retouched `van-1`). These are stop-gaps; regenerate or photograph those images with the right
number and drop them in with `npm run photo`. (The two vans also show a mistyped e-mail, `…plumbingpres.com`, from the AI generation.)
If you change the number again, update the config and the extractor's `REPLACEMENTS`, re-run `prepare_media.py`, and `npm run verify`
will fail the build if the old number survives anywhere.

## Analytics (Google Analytics 4)

No analytics script is emitted until you add an ID — the old site's ID was removed on purpose. When you have the new GA4
property: **Cloudflare Pages → Settings → Environment variables → Production → `PUBLIC_GA_MEASUREMENT_ID` = `G-XXXXXXXXXX`**,
then redeploy. To change it later, edit that one variable. (Alternatively paste it into `GA_MEASUREMENT_ID` at the top of
`src/config/site.ts`.) The tag is only added to production builds, never to `npm run dev`.

## States We Serve (internal linking)

`src/config/states.ts` lists all 50 states, D.C. and Puerto Rico (the legacy site already linked both). Each links to
`https://<code>.buffaloplumbingpros.com/` (e.g. `https://ny.buffaloplumbingpros.com/`). They appear:

* on the homepage — a tile-grid U.S. map (New York highlighted as HQ) plus an A–Z index (the only view on phones);
* in the footer of **every** page — a sitewide "States We Serve" link block;
* in `sitemap-index.xml` (each state's `/sitemap.xml`, like the legacy index), `llms.txt`, and as an `ItemList` in the homepage JSON-LD.

The state sites themselves are separate projects; each must serve `/sitemap.xml` and be verified in Search Console for Google to
accept the cross-host sitemap references.

## Maps

All maps are Google Maps `<iframe>` embeds, lazy-loaded, built by `src/components/MapEmbed.astro` (35 across the site):
homepage business-address map (140 Irwin Pl) and U.S. map, every service page (Buffalo service area) and every neighbourhood page
(centred on that neighbourhood + ZIP). They use the same keyless embed URL as the legacy site. To use Google's own
*Share → Embed a map* iframe for the business pin, paste its `src` URL into `MAPS.businessEmbedSrc` in `src/config/site.ts`.

## Replacing the placeholder photos

All photography lives in `src/assets/photos/` (one file per slot). When you have real photos:

```
npm run photo -- --list                         # every slot, its size, and where it is used
npm run photo -- van-1 ~/Downloads/real-van.jpg # resizes → WebP and replaces the slot
```

Then update that photo's description in `PHOTO_ALT` (`src/lib/media.ts`) so the alt text matches, and rebuild. Which photo each
service/neighbourhood page uses is also set in `src/lib/media.ts`.

## Dates

The rebuilt site is treated as freshly published, so every date is between **2026-09-01 and 2026-10-05** (none later than today).

* Blog posts: `datePublished` / `dateModified` in `src/content/blog/<slug>.json` (ISO `YYYY-MM-DD`). The visible `m/d/yyyy` on posts and on
  the blog index, the `<time>` tags, `article:published_time` and the `BlogPosting` JSON-LD are all derived from it. The ten posts have
  ten distinct dates, newest first in the blog-index order (`POST_DATES` in `scripts/extract_legacy_content.py` records how they were set).
* Everything else (sitemap `<lastmod>`, page-level `dateModified`): `SITE.lastModified` in `src/config/site.ts` — keep it on or before today.
* "(2024)" in one post title became "(2026)". The business-history claims "since 2005" / "since 2010" are not publish dates and were left.
* `npm run verify` check 7 fails the run if any date, `<time>`, `<lastmod>`, or stray visible year falls outside the window
  (`EARLIEST`/`LATEST` at the top of `scripts/verify_parity.py`; move `LATEST` forward when you publish new posts).

## Verifying a build against the legacy site

```
git archive main | tar -x -C /tmp/legacy
npm run build
npm run verify -- /tmp/legacy dist        # python3 -I scripts/verify_parity.py /tmp/legacy dist
```

Checks: identical URL set (+ sitemap lists all 45) · identical `<title>` and meta description on every page · every text node of
every legacy page's content present verbatim · every internal link/asset resolves · one `<h1>`, canonical on the new domain,
valid JSON-LD, alt text and og:image on every page · no trace of the old domain or old phone number · every tel: link and JSON-LD telephone is the new number · all 52 state links on every page · every date inside the window above.

The only intentional differences from the legacy copy (applied by the extractor and mirrored in the verifier):
`contact@pbmplumbingco.com` → `info@buffaloplumbingpros.com`, `pbmplumbingco.com` → `buffaloplumbingpros.com`, and the business ZIP
`14086` → `14228` (new address: 140 Irwin Pl, Buffalo, NY 14228) in titles, descriptions and body copy, the new phone number, and the new publish dates described above.

## SEO / AI-search foundations included

* Canonical URLs on the new domain; `robots.txt`; `sitemap.xml` (45 URLs); `sitemap-index.xml` kept for URL continuity.
* One JSON-LD `@graph` per page: `Plumber` (NAP, hours, 15 neighbourhood `Place`s with ZIPs, 18-service `OfferCatalog`), `WebSite`,
  `WebPage`, `BreadcrumbList`; plus `Service` + `FAQPage` on service pages, `Place` on area pages, `BlogPosting` on posts.
* `/llms.txt` — Markdown map of services, areas and guides for LLM crawlers, generated from the same content.
* Internal-link mesh: every service ↔ every area ↔ blog; "related services", the original hand-picked "nearby areas", footer + mega-menus.
* Semantic landmarks, descriptive alt text, in-article table of contents with deep-link ids, zero axe-core violations (WCAG 2.1 AA).
* Static HTML, ~2 kB JS, self-hosted fonts, AVIF/WebP images, CLS ≈ 0.

## Legacy copy preserved on purpose (decide in a later content pass)

The brief was "no content changes", so these were carried over exactly. They are flagged here so they get a conscious decision:

* Claims that need evidence/consistency: "15+" vs "20+" years (and "since 2005"), "A+ BBB rating", "5.0 Rating", "98% satisfaction",
  "500+ projects", response times (30 / 30–60 / 60 min), "licensed in all 50 states", published prices, and hours (24/7 vs Mon–Fri/Sat).
* Title tags run up to 145 characters (search results truncate near 60) and many are keyword-stacked.
* Blog bylines use named "Master Plumbers"; structured data attributes posts to the business, not to a person.
