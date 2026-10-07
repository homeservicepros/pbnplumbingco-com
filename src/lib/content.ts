import { getCollection, type CollectionEntry } from 'astro:content';
import nav from '../content/pages/nav.json';
import home from '../content/pages/home.json';
import blogIndex from '../content/pages/blog-index.json';

export { nav, home, blogIndex };

export type ServiceEntry = CollectionEntry<'services'>;
export type AreaEntry = CollectionEntry<'areas'>;
export type PostEntry = CollectionEntry<'blog'>;

export type ServiceGroup = 'repair' | 'installation';

export interface ServiceLink {
  slug: string;
  name: string;
  group: ServiceGroup;
  href: string;
}
export interface AreaLink {
  slug: string;
  name: string;
  zip: string;
  href: string;
}

/** "Plumbing Repair Buffalo NY" -> repair; "Water Heater Installation Buffalo NY" -> installation. */
export const serviceGroup = (name: string): ServiceGroup => (/repair/i.test(name) ? 'repair' : 'installation');

export const GROUP_LABEL: Record<ServiceGroup, string> = {
  repair: 'Plumbing Repair',
  installation: 'Installation & Replacement',
};

export const serviceHref = (slug: string) => `/services/${slug}`;
export const areaHref = (slug: string) => `/service-area/${slug}`;
export const postHref = (slug: string) => `/blog/${slug}`;

/** Menu/card order is the order the legacy site used. */
export const serviceLinks: ServiceLink[] = nav.services.map((s) => ({
  slug: s.slug,
  name: s.name,
  group: serviceGroup(s.name),
  href: serviceHref(s.slug),
}));

/** Zip codes come from the area JSON (needed for nav labels); resolved lazily in getAreaLinks. */
export async function getAreaLinks(): Promise<AreaLink[]> {
  const areas = await getCollection('areas');
  const byId = new Map(areas.map((a) => [a.id, a]));
  return nav.areas.map((a) => ({
    slug: a.slug,
    name: a.name,
    zip: byId.get(a.slug)!.data.zip,
    href: areaHref(a.slug),
  }));
}

export async function getServices(): Promise<ServiceEntry[]> {
  const all = await getCollection('services');
  const byId = new Map(all.map((s) => [s.id, s]));
  return nav.services.map((s) => byId.get(s.slug)!);
}

export async function getAreas(): Promise<AreaEntry[]> {
  const all = await getCollection('areas');
  const byId = new Map(all.map((a) => [a.id, a]));
  return nav.areas.map((a) => byId.get(a.slug)!);
}

/** Newest first. */
export async function getPosts(): Promise<PostEntry[]> {
  const all = await getCollection('blog');
  return all.sort((a, b) => b.data.datePublished.localeCompare(a.data.datePublished) || a.id.localeCompare(b.id));
}

/** Blog index order exactly as on the legacy /blog/ page. */
export async function getPostsInLegacyOrder(): Promise<PostEntry[]> {
  const all = await getCollection('blog');
  const byId = new Map(all.map((p) => [p.id, p]));
  return blogIndex.items.map((i) => byId.get(i.slug)!);
}

export const stripLocation = (name: string) => name.replace(/\s+Buffalo NY$/i, '');
