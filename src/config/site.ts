/**
 * Single source of truth for business facts (NAP), domain and analytics.
 * Every value here was taken from the legacy site; change it here and it changes everywhere
 * (visible text, tel:/mailto: links, JSON-LD).
 */
export const SITE = {
  name: 'Buffalo Plumbing PROS',
  /** Production origin. Canonical URLs, sitemap and JSON-LD are built from this. */
  url: 'https://buffaloplumbingpros.com',
  tagline: 'Expert Residential Plumbing Services Solutions',
  phone: '(716) 610-1160',
  /** E.164 form for tel: links. */
  phoneE164: '+17166101160',
  email: 'contact@pbmplumbingco.com',
  address: {
    street: '140 Irwin Pl',
    city: 'Buffalo',
    region: 'NY',
    postalCode: '14086',
    country: 'US',
  },
  /** Visible hours (homepage #contact section). */
  hours: ['Mon-Fri: 8AM-6PM', 'Sat: 8AM-4PM', '24/7 Emergency'],
  /** Same values for structured data. */
  openingHours: [
    { days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], opens: '08:00', closes: '18:00' },
    { days: ['Saturday'], opens: '08:00', closes: '16:00' },
  ],
  googleAnalyticsId: 'G-9YE9WNCF35',
  foundingYear: 2005,
  /** Redesign date — used as sitemap <lastmod> for the migrated pages. */
  lastModified: '2026-10-07',
  /** Google Maps embeds exactly as on the legacy site. */
  maps: {
    buffalo: 'https://maps.google.com/maps?q=Buffalo%2C%20NY%2C%20United%20States&t=&z=13&ie=UTF8&iwloc=&output=embed',
    usa: 'https://maps.google.com/maps?q=United%20States&t=&z=4&ie=UTF8&iwloc=&output=embed',
  },
} as const;

export const telHref = `tel:${SITE.phoneE164}`;
export const mailHref = `mailto:${SITE.email}`;
export const absoluteUrl = (path = '/') => new URL(path, SITE.url).toString();
