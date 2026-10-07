import type { APIRoute } from 'astro';
import { SITE, absoluteUrl, fullAddress } from '../config/site';
import { statesAlphabetical, stateUrl } from '../config/states';
import { home, getServices, getAreas, getPosts, serviceHref, areaHref, postHref } from '../lib/content';

/**
 * /llms.txt — a plain-Markdown map of the site for LLM crawlers and answer engines (llmstxt.org).
 * Built entirely from the site's own content collections, so it can never drift from the pages.
 */
export const GET: APIRoute = async () => {
  const [services, areas, posts] = await Promise.all([getServices(), getAreas(), getPosts()]);

  const lines: string[] = [
    `# ${SITE.name}`,
    '',
    `> ${home.description}`,
    '',
    `${SITE.name} is a residential plumbing company based in Buffalo, NY, serving Buffalo neighborhoods and surrounding areas with 24/7 emergency plumbing.`,
    '',
    '## Business details',
    `- Phone: ${SITE.phone}`,
    `- Alternate phone: ${SITE.phoneAlt}`,
    `- Email: ${SITE.email}`,
    `- Address: ${fullAddress}`,
    `- Hours: ${SITE.hours.join(' · ')}`,
    `- Website: ${SITE.url}/`,
    '',
    '## Plumbing services',
    ...services.map((s) => `- [${s.data.name}](${absoluteUrl(serviceHref(s.id))}): ${s.data.description}`),
    '',
    '## Buffalo service areas',
    ...areas.map((s) => `- [${s.data.name} (${s.data.zip})](${absoluteUrl(areaHref(s.id))}): ${s.data.description}`),
    '',
    '## State sites (nationwide coverage)',
    ...statesAlphabetical().map((s) => `- [${s.name}](${stateUrl(s.code)}): ${SITE.name} in ${s.name}`),
    '',
    '## Plumbing guides (blog)',
    `- [Blog index](${absoluteUrl('/blog/')}): Professional advice and tips from ${SITE.name}.`,
    ...posts.map((p) => `- [${p.data.h1}](${absoluteUrl(postHref(p.id))}): ${p.data.description}`),
    '',
  ];
  return new Response(lines.join('\n'), { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
