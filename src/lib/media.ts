import type { ImageMetadata } from 'astro';

const photoModules = import.meta.glob<{ default: ImageMetadata }>('/src/assets/photos/*.webp', { eager: true });
const brandModules = import.meta.glob<{ default: ImageMetadata }>('/src/assets/brand/*.png', { eager: true });

export type PhotoName =
  | 'business-exterior' | 'owner-portrait' | 'team-composite' | 'workspace-interior'
  | 'bg-header' | 'bg-footer'
  | 'before-after-1' | 'before-after-2' | 'before-after-3' | 'before-after-4'
  | 'technician-greeting' | 'van-1' | 'van-2' | 'technician-unloading'
  | 'residential-1' | 'residential-2' | 'residential-3' | 'residential-4'
  | 'commercial-1' | 'commercial-2' | 'commercial-3' | 'commercial-4';

export type BrandName =
  | 'logo-full' | 'logo-full-white' | 'logo-mark' | 'logo-mark-white' | 'badge-shield' | 'badge-emergency';

export function photo(name: PhotoName): ImageMetadata {
  const mod = photoModules[`/src/assets/photos/${name}.webp`];
  if (!mod) throw new Error(`Missing photo asset: ${name}`);
  return mod.default;
}

export function brand(name: BrandName): ImageMetadata {
  const mod = brandModules[`/src/assets/brand/${name}.png`];
  if (!mod) throw new Error(`Missing brand asset: ${name}`);
  return mod.default;
}

/** Accurate, descriptive alt text for every photo (what is actually visible in the image). */
export const PHOTO_ALT: Record<PhotoName, string> = {
  'business-exterior': 'Buffalo Plumbing PROS branded service van parked outside the shop with a technician loading equipment',
  'owner-portrait': 'Buffalo Plumbing PROS plumber in a navy company jacket standing in the workshop beside the service van',
  'team-composite': 'Four Buffalo Plumbing PROS plumbers talking together in the workshop',
  'workspace-interior': 'Buffalo Plumbing PROS technician working at a parts bench next to a Buffalo Plumbing PROS sign',
  'bg-header': '',
  'bg-footer': '',
  'before-after-1': 'Before and after: a burst pipe spraying water in a brick utility room, replaced with new copper piping and a shut-off valve',
  'before-after-2': 'Before and after: a corroded outdoor hose bib and wet wall replaced with a new brass hose connection',
  'before-after-3': 'Before and after: a rusted exterior pipe and flooded drain cover beside a building, replaced with new white piping and a flush drain cap',
  'before-after-4': 'Before and after: a basement utility room with rusted leaking pipes, updated with new copper and PEX piping and a clean utility sink',
  'technician-greeting': 'A Buffalo Plumbing PROS technician in a blue uniform shaking hands with a smiling homeowner at her front door',
  'van-1': 'White Buffalo Plumbing PROS service van with the company phone number parked in a residential driveway',
  'van-2': 'Blue and white Buffalo Plumbing PROS emergency plumbing van on a Buffalo neighborhood street',
  'technician-unloading': 'Buffalo Plumbing PROS technician carrying a toolbox and pipe from the service van',
  'residential-1': 'Plumber kneeling at an outdoor water line beside a suburban Buffalo home',
  'residential-2': 'Gloved hands using pliers on a kitchen sink supply line next to a garbage disposal',
  'residential-3': 'Plumber carrying coiled pipe and tools through a utility room with a water heater',
  'residential-4': 'Plumber standing with arms crossed in a bathroom, assessing the vanity plumbing',
  'commercial-1': 'Crew of plumbers installing large water main pipe and a gate valve at a building site',
  'commercial-2': 'Plumber feeding a sewer inspection camera into a pipe with a live monitor showing the pipe interior',
  'commercial-3': 'Plumber working on a large outdoor pipe manifold beside a building',
  'commercial-4': 'Three plumbers in hard hats reviewing building plans inside an unfinished building with exposed pipework',
};

/** Which header photo suits which service page. Chosen by what the picture actually shows. */
export const SERVICE_PHOTO: Record<string, PhotoName> = {
  'plumbing-repair-buffalo-ny': 'residential-1',
  'drain-repair-buffalo-ny': 'commercial-2',
  'toilet-repair-buffalo-ny': 'residential-4',
  'shower-repair-buffalo-ny': 'residential-4',
  'faucet-repair-buffalo-ny': 'residential-2',
  'water-heater-repair-buffalo-ny': 'residential-3',
  'sewer-repair-buffalo-ny': 'commercial-3',
  'water-pipe-repair-buffalo-ny': 'commercial-1',
  'water-heater-installation-buffalo-ny': 'residential-3',
  'toilet-installation-buffalo-ny': 'residential-4',
  'sink-installation-buffalo-ny': 'residential-2',
  'bathtub-installation-buffalo-ny': 'residential-4',
  'shower-installation-buffalo-ny': 'residential-4',
  'faucet-installation-buffalo-ny': 'residential-2',
  'drain-installation-buffalo-ny': 'commercial-2',
  'sewer-installation-buffalo-ny': 'commercial-3',
  'plumbing-installation-or-replacement-buffalo-ny': 'commercial-4',
  'water-purification-system-installation-buffalo-ny': 'commercial-1',
};

/** Neighbourhood pages rotate through the field/branding photos (deterministic by slug). */
const AREA_ROTATION: PhotoName[] = ['van-1', 'technician-unloading', 'van-2', 'business-exterior', 'technician-greeting'];
export function areaPhoto(slug: string): PhotoName {
  let h = 0;
  for (const ch of slug) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return AREA_ROTATION[h % AREA_ROTATION.length]!;
}

/** Decorative thumbnails for the blog (alt is intentionally empty on these). */
const BLOG_ROTATION: PhotoName[] = ['residential-2', 'van-2', 'residential-3', 'workspace-interior', 'commercial-2', 'residential-1', 'technician-unloading', 'team-composite', 'residential-4', 'van-1'];
export function blogPhoto(index: number): PhotoName {
  return BLOG_ROTATION[index % BLOG_ROTATION.length]!;
}
