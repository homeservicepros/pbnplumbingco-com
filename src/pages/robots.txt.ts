import type { APIRoute } from 'astro';
import { absoluteUrl } from '../config/site';

// Same rules as the legacy robots.txt (everything crawlable; common bot traps blocked), new domain sitemaps.
// Search and AI answer-engine crawlers (Googlebot, Bingbot, GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot…)
// are all covered by the wildcard group on purpose: this is a local-lead site that wants to be cited.
export const GET: APIRoute = () => {
  const body = `User-agent: *
Allow: /

# Block common bot traps
Disallow: /cgi-bin/
Disallow: /wp-admin/
Disallow: /admin/
Disallow: /*.php$

Sitemap: ${absoluteUrl('/sitemap-index.xml')}
Sitemap: ${absoluteUrl('/sitemap.xml')}
`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
