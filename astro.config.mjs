// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// The legacy site is served from extensionless URLs (/services/plumbing-repair-buffalo-ny) and the
// blog index at /blog/. `build.format: 'preserve'` emits files exactly as authored:
//   services/[slug].astro  -> services/plumbing-repair-buffalo-ny.html  (Cloudflare Pages serves it at the
//                              extensionless URL, exactly like the legacy site)
//   blog/index.astro       -> blog/index.html                            (served at /blog/)
// so every URL stays identical to the legacy site.
export default defineConfig({
  site: 'https://buffaloplumbingpros.com',
  output: 'static',
  trailingSlash: 'ignore',
  build: {
    format: 'preserve',
    inlineStylesheets: 'auto',
  },
  compressHTML: true,
  prefetch: { prefetchAll: false },
  vite: {
    plugins: [tailwindcss()],
  },
});
