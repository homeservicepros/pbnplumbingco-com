import type { APIRoute } from 'astro';
import { SITE, absoluteUrl } from '../config/site';

/**
 * The legacy site exposed /sitemap-index.xml (it also listed per-state sub-domain sitemaps of the old
 * domain). The URL is kept so existing references keep resolving; it points at this site's sitemap.
 */
export const GET: APIRoute = () => {
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>${absoluteUrl('/sitemap.xml')}</loc><lastmod>${SITE.lastModified}</lastmod></sitemap>
</sitemapindex>
`;
  return new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
