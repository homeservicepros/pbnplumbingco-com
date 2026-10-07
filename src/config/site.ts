/**
 * GA4 Measurement ID fallback (G-XXXXXXXXXX). Leave empty and set PUBLIC_GA_MEASUREMENT_ID in
 * Cloudflare Pages instead (Settings → Environment variables → Production, then redeploy), or paste the
 * new ID here. While no ID is set, no analytics script is emitted at all.
 */
const GA_MEASUREMENT_ID = '';

/**
 * Single source of truth for business facts (NAP), domain, analytics and maps.
 * Change a value here and it changes everywhere (visible text, tel:/mailto: links, JSON-LD, sitemap).
 */
export const SITE = {
  name: 'Buffalo Plumbing PROS',
  /** Production origin. Canonical URLs, sitemap, JSON-LD and the state sub-domain links are built from this. */
  url: 'https://buffaloplumbingpros.com',
  tagline: 'Expert Residential Plumbing Services Solutions',
  /** PRIMARY number: used by every call-to-action button, the header, the mobile call bar and the main JSON-LD telephone. */
  phone: '(716) 663-0186',
  /** E.164 form for tel: links. */
  phoneE164: '+17166630186',
  /** SECOND live line (the number on the vans, signs and badges). Shown as an "alternate line" in contact blocks and the footer. */
  phoneAlt: '(716) 610-1160',
  phoneAltE164: '+17166101160',
  email: 'info@buffaloplumbingpros.com',
  address: {
    street: '140 Irwin Pl',
    city: 'Buffalo',
    region: 'NY',
    postalCode: '14228',
    country: 'US',
  },
  /** Visible hours (homepage #contact section). */
  hours: ['Mon-Fri: 8AM-6PM', 'Sat: 8AM-4PM', '24/7 Emergency'],
  /** Same values for structured data. */
  openingHours: [
    { days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], opens: '08:00', closes: '18:00' },
    { days: ['Saturday'], opens: '08:00', closes: '16:00' },
  ],
  /** GA4 Measurement ID — see GA_MEASUREMENT_ID above. Only a well-formed `G-…` ID is ever emitted. */
  googleAnalyticsId: ((import.meta.env.PUBLIC_GA_MEASUREMENT_ID as string | undefined)?.trim() || GA_MEASUREMENT_ID).trim(),
  foundingYear: 2005,
  /** Publish date of the rebuilt site — sitemap <lastmod> and page-level dateModified. Keep it on or before today. */
  lastModified: '2026-10-05',
} as const;

export const telHref = `tel:${SITE.phoneE164}`;
export const telAltHref = `tel:${SITE.phoneAltE164}`;
export const mailHref = `mailto:${SITE.email}`;
export const absoluteUrl = (path = '/') => new URL(path, SITE.url).toString();

/** "140 Irwin Pl, Buffalo, NY 14228" */
export const fullAddress = `${SITE.address.street}, ${SITE.address.city}, ${SITE.address.region} ${SITE.address.postalCode}`;

/**
 * Google Maps embeds.
 * `embedUrl(query, zoom)` builds the same keyless embed URL the legacy site used
 * (https://maps.google.com/maps?q=…&output=embed), so every <iframe> works without an API key.
 * To use Google's own "Share → Embed a map" iframe for the business pin instead, paste just its
 * src="…" URL into `businessEmbedSrc`; it is then used for every business-location map.
 */
export const MAPS = {
  businessEmbedSrc: '',
  businessQuery: fullAddress,
};

export const embedUrl = (query: string, zoom = 13) =>
  `https://maps.google.com/maps?q=${encodeURIComponent(query)}&t=&z=${zoom}&ie=UTF8&iwloc=&output=embed`;

export const businessMapSrc = (zoom = 14) => MAPS.businessEmbedSrc || embedUrl(MAPS.businessQuery, zoom);
/** City-wide service-area map (legacy: q=Buffalo, NY, United States, z=13). */
export const buffaloMapSrc = embedUrl('Buffalo, NY, United States', 13);
export const usaMapSrc = embedUrl('United States', 4);
export const googleMapsLink = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}`;
