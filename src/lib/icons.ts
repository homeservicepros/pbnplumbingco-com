/** Lucide icon per service (names verified against @iconify-json/lucide). */
export const SERVICE_ICON: Record<string, string> = {
  'plumbing-repair-buffalo-ny': 'wrench',
  'drain-repair-buffalo-ny': 'waves',
  'toilet-repair-buffalo-ny': 'toilet',
  'shower-repair-buffalo-ny': 'shower-head',
  'faucet-repair-buffalo-ny': 'faucet',
  'water-heater-repair-buffalo-ny': 'flame',
  'sewer-repair-buffalo-ny': 'construction',
  'water-pipe-repair-buffalo-ny': 'droplets',
  'water-heater-installation-buffalo-ny': 'flame',
  'toilet-installation-buffalo-ny': 'toilet',
  'sink-installation-buffalo-ny': 'glass-water',
  'bathtub-installation-buffalo-ny': 'bath',
  'shower-installation-buffalo-ny': 'shower-head',
  'faucet-installation-buffalo-ny': 'faucet',
  'drain-installation-buffalo-ny': 'waves',
  'sewer-installation-buffalo-ny': 'construction',
  'plumbing-installation-or-replacement-buffalo-ny': 'hammer',
  'water-purification-system-installation-buffalo-ny': 'filter',
};
export const serviceIcon = (slug: string) => SERVICE_ICON[slug] ?? 'wrench';
