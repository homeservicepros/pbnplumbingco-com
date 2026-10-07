import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// Content is extracted verbatim from the legacy site by scripts/extract_legacy_content.py.
// The schemas make a template/content mismatch a build error instead of a silent blank section.

const cta = z.object({ heading: z.string(), text: z.string(), button: z.string() });
const idFromFile = ({ entry }: { entry: string }) => entry.replace(/\.json$/, '');

const services = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/services', generateId: idFromFile }),
  schema: z.object({
    name: z.string(),
    title: z.string(),
    description: z.string(),
    h1: z.string(),
    heroText: z.string(),
    heroButton: z.string(),
    bodyHtml: z.string(),
    benefitsHeading: z.string(),
    benefits: z.array(z.string()).min(1),
    processHeading: z.string(),
    process: z.array(z.string()).min(1),
    sidebarCta: cta,
    faqHeading: z.string(),
    faqs: z.array(z.object({ q: z.string(), a: z.string() })).min(1),
    faqFooter: z.object({ text: z.string(), button: z.string() }),
    areasHeading: z.string(),
    areasSubheading: z.string(),
    cardText: z.string(),
  }),
});

const areas = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/areas', generateId: idFromFile }),
  schema: z.object({
    name: z.string(),
    zip: z.string(),
    title: z.string(),
    description: z.string(),
    h1: z.string(),
    heroText: z.string(),
    heroButton: z.string(),
    bodyHtml: z.string(),
    whyHeading: z.string(),
    whyItems: z.array(z.object({ title: z.string(), text: z.string() })).min(1),
    coverage: z.object({ heading: z.string(), text: z.string() }),
    sidebarCta: cta,
    infoHeading: z.string(),
    infoRows: z.array(z.object({ label: z.string(), value: z.string() })).min(1),
    servicesHeading: z.string(),
    mapHeading: z.string(),
    mapSubheading: z.string(),
    mapContact: z.object({
      heading: z.string(),
      businessName: z.string(),
      serving: z.string(),
      zipLine: z.string(),
      hoursLabel: z.string(),
      hoursValue: z.string(),
    }),
    nearby: z.object({
      heading: z.string(),
      links: z.array(z.object({ slug: z.string(), name: z.string() })).min(1),
      viewAll: z.object({ label: z.string(), href: z.string() }),
    }),
  }),
});

const blog = defineCollection({
  loader: glob({ pattern: '*.json', base: './src/content/blog', generateId: idFromFile }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    keywords: z.string().nullable(),
    h1: z.string(),
    author: z.string(),
    dateText: z.string(),
    datePublished: z.string(),
    dateModified: z.string(),
    summary: z.string(),
    bodyHtml: z.string(),
    cta,
  }),
});

export const collections = { services, areas, blog };
