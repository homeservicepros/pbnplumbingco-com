import { SITE } from './site';

/**
 * Every U.S. state (+ D.C. and Puerto Rico, which the legacy site already linked) with the tile-grid
 * position used by the map on the homepage. Each state has its own sub-domain: ny.buffaloplumbingpros.com …
 */
export interface UsState {
  code: string; // USPS code → sub-domain
  name: string;
  /** 0-based column / row in the 11 × 8 tile grid */
  col: number;
  row: number;
  territory?: boolean;
}

export const GRID = { cols: 11, rows: 8 } as const;

const s = (code: string, name: string, col: number, row: number, territory = false): UsState => ({ code, name, col, row, territory });

export const STATES: UsState[] = [
  // row 0
  s('AK', 'Alaska', 0, 0),
  s('ME', 'Maine', 10, 0),
  // row 1
  s('WI', 'Wisconsin', 5, 1),
  s('VT', 'Vermont', 9, 1),
  s('NH', 'New Hampshire', 10, 1),
  // row 2
  s('WA', 'Washington', 0, 2),
  s('ID', 'Idaho', 1, 2),
  s('MT', 'Montana', 2, 2),
  s('ND', 'North Dakota', 3, 2),
  s('MN', 'Minnesota', 4, 2),
  s('IL', 'Illinois', 5, 2),
  s('MI', 'Michigan', 6, 2),
  s('NY', 'New York', 8, 2),
  s('MA', 'Massachusetts', 9, 2),
  // row 3
  s('OR', 'Oregon', 0, 3),
  s('NV', 'Nevada', 1, 3),
  s('WY', 'Wyoming', 2, 3),
  s('SD', 'South Dakota', 3, 3),
  s('IA', 'Iowa', 4, 3),
  s('IN', 'Indiana', 5, 3),
  s('OH', 'Ohio', 6, 3),
  s('PA', 'Pennsylvania', 7, 3),
  s('NJ', 'New Jersey', 8, 3),
  s('CT', 'Connecticut', 9, 3),
  s('RI', 'Rhode Island', 10, 3),
  // row 4
  s('CA', 'California', 0, 4),
  s('UT', 'Utah', 1, 4),
  s('CO', 'Colorado', 2, 4),
  s('NE', 'Nebraska', 3, 4),
  s('MO', 'Missouri', 4, 4),
  s('KY', 'Kentucky', 5, 4),
  s('WV', 'West Virginia', 6, 4),
  s('VA', 'Virginia', 7, 4),
  s('MD', 'Maryland', 8, 4),
  s('DE', 'Delaware', 9, 4),
  // row 5
  s('AZ', 'Arizona', 1, 5),
  s('NM', 'New Mexico', 2, 5),
  s('KS', 'Kansas', 3, 5),
  s('AR', 'Arkansas', 4, 5),
  s('TN', 'Tennessee', 5, 5),
  s('NC', 'North Carolina', 6, 5),
  s('SC', 'South Carolina', 7, 5),
  s('DC', 'District of Columbia', 8, 5),
  // row 6
  s('OK', 'Oklahoma', 3, 6),
  s('LA', 'Louisiana', 4, 6),
  s('MS', 'Mississippi', 5, 6),
  s('AL', 'Alabama', 6, 6),
  s('GA', 'Georgia', 7, 6),
  // row 7
  s('HI', 'Hawaii', 0, 7),
  s('TX', 'Texas', 3, 7),
  s('FL', 'Florida', 8, 7),
  s('PR', 'Puerto Rico', 10, 7, true),
];

/** Headquarters state — highlighted on the map. */
export const HQ_STATE = 'NY';

const rootHost = new URL(SITE.url).host.replace(/^www\./, '');

/** https://ny.buffaloplumbingpros.com/ */
export const stateUrl = (code: string) => `https://${code.toLowerCase()}.${rootHost}/`;
export const stateSitemapUrl = (code: string) => `https://${code.toLowerCase()}.${rootHost}/sitemap.xml`;

export const statesAlphabetical = () => [...STATES].sort((a, b) => a.name.localeCompare(b.name));
