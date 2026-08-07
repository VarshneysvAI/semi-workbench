export type SkStatus = 'accepted' | 'conflict' | 'refused' | 'review'

export interface SkuRow {
  id: string
  manufacturer: string
  partNumber: string
  attribute: string
  value: string
  unit: string
  sources: number
  confidence: number
  conformal: [number, number]
  auditsPass: number
  status: SkStatus
}

export const SKU_ROWS: SkuRow[] = [
  { id: '1', manufacturer: 'NIBCO', partNumber: 'BV-3001', attribute: 'pressure_rating', value: '150', unit: 'psi', sources: 4, confidence: 0.97, conformal: [145, 155], auditsPass: 5, status: 'accepted' },
  { id: '2', manufacturer: 'NIBCO', partNumber: 'BV-3006', attribute: 'thread_standard', value: 'NPT', unit: '', sources: 3, confidence: 0.94, conformal: [0.87, 0.99], auditsPass: 5, status: 'accepted' },
  { id: '3', manufacturer: 'Watts', partNumber: 'WV-1011', attribute: 'thread_standard', value: 'NPT / BSPT', unit: '', sources: 2, confidence: 0.58, conformal: [0.32, 0.71], auditsPass: 2, status: 'conflict' },
  { id: '4', manufacturer: 'Apollo', partNumber: 'BV-2255', attribute: 'temp_rating', value: '180', unit: '°F', sources: 2, confidence: 0.88, conformal: [171, 192], auditsPass: 4, status: 'accepted' },
  { id: '5', manufacturer: 'Watts', partNumber: 'LFR-2A', attribute: 'material', value: 'Lead-free', unit: '', sources: 3, confidence: 0.96, conformal: [0.9, 1.0], auditsPass: 5, status: 'accepted' },
  { id: '6', manufacturer: 'NIBCO', partNumber: 'WFV-410', attribute: 'flow_coefficient', value: '—', unit: '', sources: 1, confidence: 0.41, conformal: [0.2, 0.62], auditsPass: 1, status: 'refused' },
  { id: '7', manufacturer: 'Apollo', partNumber: 'CV-7001', attribute: 'body_material', value: 'Brass', unit: '', sources: 2, confidence: 0.93, conformal: [0.85, 0.99], auditsPass: 5, status: 'accepted' },
  { id: '8', manufacturer: 'NIBCO', partNumber: 'WBV-50', attribute: 'pressure_rating', value: '400', unit: 'psi', sources: 2, confidence: 0.91, conformal: [388, 416], auditsPass: 5, status: 'accepted' },
  { id: '9', manufacturer: 'Watts', partNumber: 'WV-1042', attribute: 'body_material', value: 'PVC / Brass', unit: '', sources: 2, confidence: 0.62, conformal: [0.4, 0.8], auditsPass: 3, status: 'conflict' },
  { id: '10', manufacturer: 'Apollo', partNumber: 'CTG-200', attribute: 'size', value: '2', unit: 'in', sources: 2, confidence: 0.98, conformal: [1.98, 2.02], auditsPass: 5, status: 'accepted' },
]

export interface SourceRow {
  id: string
  sku: string
  title: string
  kind: 'calibration' | 'spec' | 'manual' | 'page' | 'video'
  authority: number
  verified: boolean
  bytes: string
}

export const SOURCE_ROWS: SourceRow[] = [
  { id: 'S-01', sku: 'BV-3001', title: 'NIBCO ball-valve catalog spec sheet.pdf', kind: 'spec', authority: 1.0, verified: true, bytes: '2.4 MB' },
  { id: 'S-02', sku: 'BV-3001', title: 'install-guide-BV-3001.pdf', kind: 'manual', authority: 0.9, verified: true, bytes: '1.1 MB' },
  { id: 'S-03', sku: 'BV-3001', title: 'nibco.com/en/products/BV-3001', kind: 'page', authority: 0.7, verified: true, bytes: '—' },
  { id: 'S-04', sku: 'WV-1011', title: 'watts.com/wv1011-engineering-note.jpg', kind: 'page', authority: 0.7, verified: true, bytes: '348 KB' },
  { id: 'S-05', sku: 'CV-7001', title: 'install video — Apollo 7000 series.mp4', kind: 'video', authority: 0.5, verified: false, bytes: '42 MB' },
  { id: 'S-06', sku: 'LFR-02', title: 'rejected: www.amazon.com/dp/B0ABC', kind: 'video', authority: 0.0, verified: false, bytes: 'blocked' },
]

export type AuditState = 'pass' | 'fail' | 'run'

export interface AuditCheck {
  label: string
  state: AuditState
  note: string
}

export interface AuditGroup {
  sku: string
  attribute: string
  value: string
  unit: string
  ok: SkStatus
  confidence: number
  conformal: [number, number]
  checks: AuditCheck[]
}

export const AUDIT_GROUPS: AuditGroup[] = [
  {
    sku: 'BV-3001', attribute: 'pressure_rating', value: '150', unit: 'psi', ok: 'accepted', confidence: 0.97, conformal: [145, 155],
    checks: [
      { label: 'Physical constraints', state: 'pass', note: 'Brass ≤ 3000 psi' },
      { label: 'Cross-source consensus', state: 'pass', note: '3 of 4 sources agree' },
      { label: 'Compositional consistency', state: 'pass', note: 'fits family curve' },
      { label: 'Adversarial disproof search', state: 'pass', note: 'no disproof found' },
      { label: 'Conformal coverage 95%', state: 'pass', note: 'CI [145,155]' },
    ],
  },
  {
    sku: 'WV-1011', attribute: 'thread_standard', value: 'NPT vs BSPT', unit: '', ok: 'conflict', confidence: 0.58, conformal: [0.32, 0.71],
    checks: [
      { label: 'Physical constraints', state: 'pass', note: 'both plausible' },
      { label: 'Cross-source consensus', state: 'fail', note: 'spec says NPT, page says BSPT' },
      { label: 'Compositional consistency', state: 'run', note: 'blocked on disproof' },
      { label: 'Adversarial disproof search', state: 'run', note: 'pending' },
      { label: 'Conformal coverage 95%', state: 'fail', note: 'CI crossed 0.7 threshold' },
    ],
  },
  {
    sku: 'WFV-410', attribute: 'flow_coefficient', value: 'refused', unit: '', ok: 'refused', confidence: 0.41, conformal: [0.2, 0.62],
    checks: [
      { label: 'Physical constraints', state: 'fail', note: 'single source only' },
      { label: 'Cross-source consensus', state: 'fail', note: '1 source, no cross-check' },
      { label: 'Compositional consistency', state: 'fail', note: 'breaks size² curve' },
      { label: 'Adversarial disproof search', state: 'run', note: 'skipped' },
      { label: 'Conformal coverage 95%', state: 'fail', note: 'below threshold' },
    ],
  },
]

export interface LedgerEvent {
  at: string
  signature: string
  resolution: string
  changedOutcome: boolean
  sku: string
}

export const LEDGER_EVENTS: LedgerEvent[] = [
  { at: '09:41', signature: 'NPT vs BSPT', resolution: 'NPT · spec authority', changedOutcome: true, sku: 'BV-3006' },
  { at: '09:37', signature: 'PVC vs Brass', resolution: 'Brass · family pattern', changedOutcome: true, sku: 'CV-7001' },
  { at: '09:29', signature: '150 vs 400 psi', resolution: '150 psi · ADJUDICATED', changedOutcome: false, sku: 'BV-3001' },
  { at: '09:12', signature: '2in vs 50mm', resolution: '2 in · conformal CI', changedOutcome: true, sku: 'CTG-200' },
]

export interface PipelineStage {
  label: string
  desc: string
  count: number
  done: boolean
  active?: boolean
}

export const PIPELINE: PipelineStage[] = [
  { label: 'Discovery', desc: 'manufacturer · part_number', count: 42, done: true },
  { label: 'Extraction', desc: 'PDF · web · vision · video', count: 186, done: true, active: true },
  { label: 'Adversarial audit', desc: '5 self-checks per value', count: 418, done: false },
  { label: 'Consensus', desc: 'weights · family · precedent', count: 31, done: false },
  { label: 'Schema output', desc: 'Unilog contract', count: 0, done: false },
]

export const DNA_CHIPS: Array<{ label: string; note: string }> = [
  { label: 'NIBCO threads are listed as NPT', note: '4/4 SKUs' },
  { label: 'Watts splits spec tables per series', note: 'rows 3-7' },
  { label: 'Apollo hides max temp on page 2', note: 'video overlay' },
  { label: 'Pressure always in psi (never bar)', note: '9/10 SKUs' },
]