/**
 * Light, build-time post-processing of the legacy body HTML. It never changes wording —
 * it only adds structure that helps readers and crawlers:
 *   - stable `id`s on h2/h3 (deep links, table of contents, "jump to" sitelinks)
 *   - table wrappers so wide pricing tables scroll instead of breaking the layout
 *   - safe `rel` on off-site links
 */
export interface TocItem {
  id: string;
  text: string;
  level: 2 | 3;
}

const slugify = (s: string) =>
  s
    .toLowerCase()
    .replace(/&amp;/g, 'and')
    .replace(/<[^>]+>/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 70);

const textOf = (html: string) =>
  html
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&')
    .replace(/&nbsp;/g, ' ')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, ' ')
    .trim();

export function enhanceProse(html: string): { html: string; toc: TocItem[] } {
  const toc: TocItem[] = [];
  const used = new Set<string>();

  let out = html.replace(/<h([23])([^>]*)>([\s\S]*?)<\/h\1>/gi, (_m, lvl: string, attrs: string, inner: string) => {
    const text = textOf(inner);
    let id = slugify(text) || `section-${toc.length + 1}`;
    if (/^[0-9]/.test(id)) id = `s-${id}`; // ids that start with a digit are legal HTML5 but awkward in CSS selectors
    let n = 2;
    const base = id;
    while (used.has(id)) id = `${base}-${n++}`;
    used.add(id);
    toc.push({ id, text, level: Number(lvl) as 2 | 3 });
    return `<h${lvl}${attrs} id="${id}">${inner}</h${lvl}>`;
  });

  out = out.replace(/<table/gi, '<div class="table-wrap"><table').replace(/<\/table>/gi, '</table></div>');

  out = out.replace(/<a\s+([^>]*href="https?:\/\/[^"]+"[^>]*)>/gi, (m, attrs: string) => {
    if (/rel=/i.test(attrs) || attrs.includes('buffaloplumbingpros.com')) return m;
    return `<a ${attrs} rel="noopener">`;
  });

  return { html: out, toc };
}
