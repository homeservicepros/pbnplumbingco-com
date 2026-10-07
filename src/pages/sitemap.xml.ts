import type { APIRoute } from 'astro';
import { SITE, absoluteUrl } from '../config/site';
import { getServices, getAreas, getPosts, serviceHref, areaHref, postHref } from '../lib/content';

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

export const GET: APIRoute = async () => {
  const [services, areas, posts] = await Promise.all([getServices(), getAreas(), getPosts()]);

  // Exactly the 45 URLs the legacy sitemap listed (home, blog index, 18 services, 15 areas, 10 posts),
  // now on the new domain.
  const entries: { path: string; lastmod: string }[] = [
    { path: '/', lastmod: SITE.lastModified },
    { path: '/blog/', lastmod: SITE.lastModified },
    ...services.map((s) => ({ path: serviceHref(s.id), lastmod: SITE.lastModified })),
    ...areas.map((a) => ({ path: areaHref(a.id), lastmod: SITE.lastModified })),
    ...posts.map((p) => ({ path: postHref(p.id), lastmod: SITE.lastModified })),
  ];

  const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries.map((e) => `  <url><loc>${esc(absoluteUrl(e.path))}</loc><lastmod>${e.lastmod}</lastmod></url>`).join('\n')}
</urlset>
`;
  return new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
