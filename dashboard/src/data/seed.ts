export type Stage =
  | 'queued'
  | 'discover'
  | 'extract'
  | 'audit'
  | 'done'
  | 'conflict'
  | 'refused'

export type CellState = 'blank' | 'reading' | 'written' | 'conflict' | 'refused'

export type Origin = 'discover' | 'extract' | 'audit' | 'sheet' | 'ledger' | 'validator'

export interface Cell {
  col: string
  state: CellState
  value: string
  display: string
  conf: number
  ci: [number, number]
}

export interface SourceRef {
  key: string
  kind: 'spec' | 'manual' | 'page' | 'video' | 'nameplate'
  ref: string
  authority: number
  verified: boolean
  sourceUrl: string
}

export interface AuditCheck {
  label: string
  state: 'run' | 'pass' | 'fail'
  note: string
}

export interface ConflictSide {
  value: string
  from: string
  authority: number
  sourceUrl: string
}

export interface PlanConflict {
  col: string
  a: ConflictSide
  b: ConflictSide
}

export interface Sku {
  id: string
  mfr: string
  pn: string
  stage: Stage
  discStep: number
  sourceMax: number
  cells: Record<string, Cell>
  sources: SourceRef[]
  audits: AuditCheck[]
  conflict: PlanConflict | null
  resolution: 'A' | 'B' | 'refused' | null
}

export interface LedgerRow {
  at: number
  sig: string
  resolution: string
  note: string
  sku: string
  changedOutcome: boolean
  sourceUrl: string
}

export interface LogEvent {
  at: number
  pid: string | null
  sku: string
  mfr: string
  origin: Origin
  label: string
  detail?: string
  bytes?: number
}

export const MANUFACTURERS = ['NIBCO', 'WATTS', 'APOLLO'] as const
export type Mfr = (typeof MANUFACTURERS)[number]

export const COLUMNS = [
  { key: 'pressure', label: 'PRESSURE', unit: 'psi', w: 116 },
  { key: 'temp', label: 'TEMP', unit: '°F', w: 114 },
  { key: 'material', label: 'BODY MATERIAL', unit: '', w: 150 },
  { key: 'thread', label: 'THREAD', unit: '', w: 128 },
  { key: 'size', label: 'SIZE', unit: 'in', w: 102 },
  { key: 'flow', label: 'CV', unit: '', w: 92 },
  { key: 'voltage', label: 'VOLTAGE', unit: 'V', w: 92 },
  { key: 'power', label: 'POWER', unit: 'W', w: 92 },
  { key: 'weight', label: 'WEIGHT', unit: 'lbs', w: 92 },
  { key: 'certification', label: 'CERTIFICATION', unit: '', w: 140 },
] as const

export type ColKey = (typeof COLUMNS)[number]['key']
export const COL_KEYS = COLUMNS.map((c) => c.key)

export const TOTAL_SKUS = 120
export const COUNTER_THRESHOLD = 0.85

type Rng = () => number

export function mulberry32(seed: number): Rng {
  let a = seed >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const PN_POOL: Record<Mfr, string[]> = {
  NIBCO: ['BV-100', 'BV-150', 'WB-200', 'WB-200L', 'CW-90', 'S58-138', 'S58-432', 'CH90-142'],
  WATTS: ['WV-1011', 'WV-1042', 'LF30-5', 'LF30-6', 'B6001-04', 'B6260-06', 'LFR-2A', 'W7410-2'],
  APOLLO: ['CV-700', 'CV-7010', 'LFB-101', 'LFB-301', 'T100-1', 'T100-5', 'CTG-200', 'CT-300'],
}

const VALUE_POOL: Record<ColKey, string[]> = {
  pressure: ['150', '200', '300', '400', '600'],
  temp: ['17–180', '0–200', '−40–250', '32–180', '−10–220'],
  material: ['Brass', '316 SS', 'Lead-free Brass', 'PVC', 'Ductile Iron', 'CPVC'],
  thread: ['NPT', 'BSPT', 'NPT / BSPP', 'BSPP'],
  size: ['1/2', '3/4', '1', '1 1/2', '2'],
  flow: ['4.1', '9.8', '14.5', '23.3', '38.2', '46.0'],
  voltage: ['120', '240', '24'],
  power: ['50', '100', '200'],
  weight: ['1.2', '2.5', '5.0'],
  certification: ['UL Listed', 'CSA', 'NSF/ANSI 61'],
}

const CONFLICT_TABLE: PlanConflict[] = [
  {
    col: 'thread',
    a: { value: 'NPT', from: 'spec-sheet-WV-1011.pdf · p.2', authority: 1.0, sourceUrl: 'https://www.watts.com/spec/wv1011' },
    b: { value: 'BSPT', from: 'nameplate-WV-1011.jpg · crop 140,220', authority: 0.62, sourceUrl: 'https://www.watts.com/img/wv1011-nameplate' },
  },
  {
    col: 'pressure',
    a: { value: '400', from: 'spec-sheet-WB-200.pdf · tab.2', authority: 1.0, sourceUrl: 'https://www.nibco.com/spec/wb200' },
    b: { value: '200', from: 'product page · spec block', authority: 0.7, sourceUrl: 'https://www.nibco.com/products/wb200' },
  },
  {
    col: 'material',
    a: { value: '316 SS', from: 'apollo-CTG-200-catalog.pdf · p.11', authority: 0.95, sourceUrl: 'https://www.apollovalves.com/catalog/ctg200' },
    b: { value: 'Brass', from: 'nameplate CTG-200.jpg', authority: 0.6, sourceUrl: 'https://www.apollovalves.com/img/ctg200' },
  },
  {
    col: 'size',
    a: { value: '3/4', from: 'watts-B6260-06-spec.pdf · p.2', authority: 1.0, sourceUrl: 'https://www.watts.com/spec/b6260-06' },
    b: { value: '1/2', from: 'install-guide header', authority: 0.9, sourceUrl: 'https://www.watts.com/manual/b6260-06' },
  },
  {
    col: 'temp',
    a: { value: '0–200', from: 'nibco-CH90-142-spec.pdf · table D', authority: 1.0, sourceUrl: 'https://www.nibco.com/spec/ch90142' },
    b: { value: '−40–250', from: 'video transcript · 01:42', authority: 0.5, sourceUrl: 'https://www.nibco.com/media/ch90142' },
  },
  {
    col: 'thread',
    a: { value: 'NPT', from: 'apollo-T100-1-spec.pdf · p.1', authority: 1.0, sourceUrl: 'https://www.apollovalves.com/spec/t100-1' },
    b: { value: 'BSPP', from: 'apollo catalog 2026 · index table', authority: 0.8, sourceUrl: 'https://www.apollovalves.com/catalog/t100-1' },
  },
]

export interface SkuSpec {
  mfr: Mfr
  pn: string
  conflict: PlanConflict | null
  refused: boolean
}

export function genPlans(seed: number): SkuSpec[] {
  const rng = mulberry32(seed)
  return Array.from({ length: TOTAL_SKUS }, (_, i) => {
    const mfr = MANUFACTURERS[i % 3]
    return {
      mfr,
      pn: PN_POOL[mfr][i % PN_POOL[mfr].length],
      conflict: rng() < 0.06 ? CONFLICT_TABLE[(i * 7) % CONFLICT_TABLE.length] : null,
      refused: rng() < 0.03,
    }
  })
}

export function buildSku(spec: SkuSpec, idx: number, rng: Rng): Sku {
  const cells: Record<string, Cell> = {}
  COL_KEYS.forEach((col, ci) => {
    const pool = VALUE_POOL[col]
    const value = pool[(idx * 3 + ci * 5 + 1) % pool.length]
    cells[col] = {
      col,
      state: 'blank',
      value,
      display: col === 'size' ? `${value}"` : col === 'temp' ? `${value} °F` : value,
      conf: 0,
      ci: [0, 0],
    }
  })

  const sources = buildSources(spec.mfr, spec.pn, rng)

  return {
    id: `${spec.mfr.slice(0, 2).toLowerCase()}-${idx + 1}`,
    mfr: spec.mfr,
    pn: spec.pn,
    stage: 'queued',
    discStep: 0,
    sourceMax: sources.length,
    cells,
    sources,
    audits: [],
    conflict: spec.conflict,
    resolution: null,
  }
}

function buildSources(mfr: Mfr, pn: string, rng: Rng): SourceRef[] {
  const AUTH: Record<SourceRef['kind'], number> = { spec: 1.0, manual: 0.9, page: 0.7, video: 0.5, nameplate: 0.6 }
  const kinds: SourceRef['kind'][] = ['spec', 'manual', 'page']
  const list: SourceRef[] = kinds.map((kind, i) => {
    const authority = AUTH[kind]
    const base = {
      key: `src-${i + 1}`,
      kind,
      authority,
      verified: true,
    }
    if (mfr === 'NIBCO')
      return { ...base, ref: `spec-sheet-${pn}.pdf`, sourceUrl: `https://www.nibco.com/en-us/product/${pn.toLowerCase()}` }
    if (mfr === 'WATTS')
      return { ...base, ref: `watts-${pn}-${kind}.pdf`, sourceUrl: `https://www.watts.com/product/${pn.toLowerCase()}` }
    return { ...base, ref: `apollo-${pn}-catalog.pdf`, sourceUrl: `https://www.apollovalves.com/${pn.toLowerCase()}` }
  })
  if (rng() > 0.5)
    list.push({
      key: 'src-4',
      kind: 'nameplate',
      ref: `nameplate-${pn}.jpg`,
      authority: 0.6,
      verified: true,
      sourceUrl: `https://www.${mfr.toLowerCase()}.com/img/${pn.toLowerCase()}-nameplate`,
    })
  return list
}

export const STAGE_LABELS: Record<Stage, string> = {
  queued: 'Queued',
  discover: 'Discovery',
  extract: 'Extraction',
  audit: 'Audit',
  done: 'Accepted',
  conflict: 'Conflict',
  refused: 'Refused',
}

export const AUDIT_LABELS = [
  { label: 'Physical constraints', pass: 'within material limits' },
  { label: 'Cross-source contradiction', pass: 'N sources agree after normalisation' },
  { label: 'Compositional consistency', pass: 'fits family physics curve' },
  { label: 'Adversarial disproof search', pass: 'no disproof found on site' },
  { label: 'Conformal coverage 95%', pass: 'CI above 0.7 emit threshold' },
]