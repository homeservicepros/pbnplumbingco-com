import { SITE, absoluteUrl } from '../config/site';
import { home } from './content';

/** Build JSON-LD (schema.org) nodes. Everything here is derived from visible page content or site config. */

export const ids = {
  business: `${SITE.url}/#business`,
  website: `${SITE.url}/#website`,
};

type Json = Record<string, unknown>;

export interface AreaRef {
  name: string;
  zip: string;
  href: string;
}
export interface ServiceRef {
  name: string;
  href: string;
}

const dayUrl = (d: string) => `https://schema.org/${d}`;

export function areaPlace(a: AreaRef): Json {
  return {
    '@type': 'Place',
    name: `${a.name}, Buffalo, NY`,
    url: absoluteUrl(a.href),
    address: {
      '@type': 'PostalAddress',
      addressLocality: 'Buffalo',
      addressRegion: SITE.address.region,
      postalCode: a.zip,
      addressCountry: SITE.address.country,
    },
  };
}

/** The business entity (Plumber → LocalBusiness). Included on every page so each URL is self-describing. */
export function businessNode(opts: { areas: AreaRef[]; services: ServiceRef[]; withCatalog?: boolean }): Json {
  const node: Json = {
    '@type': 'Plumber',
    '@id': ids.business,
    name: SITE.name,
    url: `${SITE.url}/`,
    description: home.description,
    telephone: SITE.phoneE164,
    email: SITE.email,
    priceRange: '$$',
    foundingDate: String(SITE.foundingYear),
    logo: { '@type': 'ImageObject', url: absoluteUrl('/icon-512.png'), width: 512, height: 512 },
    image: absoluteUrl('/og-default.jpg'),
    address: {
      '@type': 'PostalAddress',
      streetAddress: SITE.address.street,
      addressLocality: SITE.address.city,
      addressRegion: SITE.address.region,
      postalCode: SITE.address.postalCode,
      addressCountry: SITE.address.country,
    },
    openingHoursSpecification: SITE.openingHours.map((h) => ({
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: h.days.map(dayUrl),
      opens: h.opens,
      closes: h.closes,
    })),
    areaServed: [
      { '@type': 'City', name: 'Buffalo', containedInPlace: { '@type': 'State', name: 'New York' } },
      ...opts.areas.map(areaPlace),
    ],
    contactPoint: {
      '@type': 'ContactPoint',
      telephone: SITE.phoneE164,
      contactType: 'emergency plumbing service',
      areaServed: 'US-NY',
      availableLanguage: 'English',
      hoursAvailable: {
        '@type': 'OpeningHoursSpecification',
        dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map(dayUrl),
        opens: '00:00',
        closes: '23:59',
      },
    },
  };
  if (opts.withCatalog) {
    node.hasOfferCatalog = {
      '@type': 'OfferCatalog',
      name: 'Residential Plumbing Services',
      itemListElement: opts.services.map((s) => ({
        '@type': 'Offer',
        itemOffered: { '@type': 'Service', name: s.name, url: absoluteUrl(s.href), provider: { '@id': ids.business } },
      })),
    };
  }
  return node;
}

export function websiteNode(): Json {
  return {
    '@type': 'WebSite',
    '@id': ids.website,
    url: `${SITE.url}/`,
    name: SITE.name,
    inLanguage: 'en-US',
    publisher: { '@id': ids.business },
  };
}

export function breadcrumbNode(pageUrl: string, items: { name: string; path: string }[]): Json {
  return {
    '@type': 'BreadcrumbList',
    '@id': `${pageUrl}#breadcrumb`,
    itemListElement: items.map((it, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: it.name,
      item: absoluteUrl(it.path),
    })),
  };
}

export function webPageNode(opts: { url: string; name: string; description: string; type?: string; about?: string; image?: string; dateModified?: string }): Json {
  const node: Json = {
    '@type': opts.type ?? 'WebPage',
    '@id': `${opts.url}#webpage`,
    url: opts.url,
    name: opts.name,
    description: opts.description,
    inLanguage: 'en-US',
    isPartOf: { '@id': ids.website },
    breadcrumb: { '@id': `${opts.url}#breadcrumb` },
    primaryImageOfPage: { '@type': 'ImageObject', url: opts.image ?? absoluteUrl('/og-default.jpg') },
    dateModified: opts.dateModified ?? SITE.lastModified,
  };
  if (opts.about) node.about = { '@id': opts.about };
  return node;
}

/** The homepage is the entity's main page: it is *about* and *mainEntity of* the business. */
export function homePageNode(opts: { name: string; description: string }): Json {
  return {
    '@type': 'WebPage',
    '@id': `${SITE.url}/#webpage`,
    url: `${SITE.url}/`,
    name: opts.name,
    description: opts.description,
    inLanguage: 'en-US',
    isPartOf: { '@id': ids.website },
    about: { '@id': ids.business },
    mainEntity: { '@id': ids.business },
    primaryImageOfPage: { '@type': 'ImageObject', url: absoluteUrl('/og-default.jpg') },
    dateModified: SITE.lastModified,
  };
}

export function serviceNode(opts: { url: string; name: string; serviceType: string; description: string; image?: string }): Json {
  return {
    '@type': 'Service',
    '@id': `${opts.url}#service`,
    name: opts.name,
    serviceType: opts.serviceType,
    category: 'Residential Plumbing Services',
    description: opts.description,
    url: opts.url,
    image: opts.image ?? absoluteUrl('/og-default.jpg'),
    provider: { '@id': ids.business },
    areaServed: { '@type': 'City', name: 'Buffalo', containedInPlace: { '@type': 'State', name: 'New York' } },
  };
}

export function faqNode(url: string, faqs: { q: string; a: string }[]): Json {
  return {
    '@type': 'FAQPage',
    '@id': `${url}#faq`,
    mainEntity: faqs.map((f) => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  };
}

export function blogPostingNode(opts: { url: string; headline: string; description: string; datePublished: string; dateModified: string; image?: string }): Json {
  return {
    '@type': 'BlogPosting',
    '@id': `${opts.url}#article`,
    headline: opts.headline,
    description: opts.description,
    datePublished: opts.datePublished,
    dateModified: opts.dateModified,
    inLanguage: 'en-US',
    mainEntityOfPage: { '@id': `${opts.url}#webpage` },
    image: opts.image ?? absoluteUrl('/og-default.jpg'),
    author: { '@id': ids.business },
    publisher: { '@id': ids.business },
  };
}

export const graph = (nodes: Json[]): Json => ({ '@context': 'https://schema.org', '@graph': nodes });
