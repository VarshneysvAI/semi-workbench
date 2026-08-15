/**
 * SEMI — TypeScript type definitions for real backend data.
 * 
 * No mock data, no demo generators, no fake values.
 * All data comes from the backend /api/ui_state endpoint.
 */

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

// Dynamic column keys derived from backend data (no hardcoded list)
export const COL_KEYS: string[] = []

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