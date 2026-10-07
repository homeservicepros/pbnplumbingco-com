import type { APIRoute } from 'astro';
import { SITE, absoluteUrl } from '../config/site';
import { STATES, stateSitemapUrl } from '../config/states';

/**
 * Like the legacy /sitemap-index.xml: this site's sitemap plus the sitemap of every state sub-domain
 * (ny.buffaloplumbingpros.com …). The state sites must serve /sitemap.xml and be verified in
 * Search Console for Google to accept the cross-host references.
 */
export const GET: APIRoute = () => {
  const body = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

  <!-- Main Site -->
  <sitemap><loc>${absoluteUrl('/sitemap.xml')}</loc><lastmod>${SITE.lastModified}</lastmod></sitemap>

  <!-- State Subdomains -->
${STATES.map((s) => `  <sitemap><loc>${stateSitemapUrl(s.code)}</loc><lastmod>${SITE.lastModified}</lastmod></sitemap>`).join('\n')}
</sitemapindex>
`;
  return new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
