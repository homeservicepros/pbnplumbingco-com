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

Then add `buffaloplumbingpros.com` under **Custom domains**. The old-domain → new-domain redirect is configured in Cloudflare
(Redirect Rules); this repo does not do it.

URLs are identical to the legacy site because `build.format: 'preserve'` emits `services/<slug>.html` (served by Cloudflare Pages at
the extensionless `/services/<slug>`) and `blog/index.html` (served at `/blog/`). The four legacy image URLs under `/images/` are kept
in `public/images/` so any image-search results still resolve.

## What lives where

```
src/
  config/site.ts          Business facts (name, phone, e-mail, address, hours, GA id, domain). Change here → changes everywhere.
  content/                ALL page copy, as JSON, extracted verbatim from the legacy HTML (see "Content" below)
    services/ areas/ blog/   one JSON file per page, validated by schemas in src/content.config.ts
    pages/home.json, blog-index.json, nav.json
  pages/                  index, services/[slug], service-area/[slug], blog/index, blog/[slug], 404,
                          sitemap.xml, sitemap-index.xml, robots.txt, llms.txt
  layouts/Base.astro      <head> (canonical, OG/Twitter, JSON-LD, GA4), skip link, header, footer, mobile call bar
  components/             Header (mega menus), Footer, InnerHero, Prose, FaqList, Process, MapSection, ServiceCard, …
  lib/schema.ts           JSON-LD builders (Plumber, WebSite, WebPage, Service, FAQPage, BreadcrumbList, BlogPosting, Place)
  lib/media.ts            photo registry, accurate alt text, which photo suits which service page
  lib/prose.ts            adds heading ids + table wrappers to legacy body HTML (never changes wording)
  assets/photos|brand/    optimised sources (Astro builds AVIF/WebP + srcset at build time)
  styles/global.css       design tokens (navy / signal blue / amber), typography, prose styles
public/                   favicons, OG image, _headers, site.webmanifest, legacy /images
scripts/                  extract_legacy_content.py · prepare_media.py · verify_parity.py
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

## Verifying a build against the legacy site

```
git archive main | tar -x -C /tmp/legacy
npm run build
npm run verify -- /tmp/legacy dist        # python3 -I scripts/verify_parity.py /tmp/legacy dist
```

Checks: identical URL set (+ sitemap lists all 45) · identical `<title>` and meta description on every page · every text node of
every legacy page's content present verbatim · every internal link/asset resolves · one `<h1>`, canonical on the new domain,
valid JSON-LD, alt text and og:image on every page.

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

* Contact e-mail is still `contact@pbmplumbingco.com` (old domain) — set `SITE.email` in `src/config/site.ts`.
* The homepage "States We Serve" grid links to `*.pbmplumbingco.com` sub-domains (old domain).
* Google Analytics ID `G-9YE9WNCF35` is the legacy property.
* Claims that need evidence/consistency: "15+" vs "20+" years (and "since 2005"), "A+ BBB rating", "5.0 Rating", "98% satisfaction",
  "500+ projects", response times (30 / 30–60 / 60 min), "licensed in all 50 states", published prices, and hours (24/7 vs Mon–Fri/Sat).
* Title tags run up to 145 characters (search results truncate near 60) and many are keyword-stacked.
* Blog bylines use named "Master Plumbers"; structured data attributes posts to the business, not to a person.
