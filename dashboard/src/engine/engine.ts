import {
  AUDIT_LABELS,
  buildSku,
  genPlans,
  mulberry32,
  COL_KEYS,
  type ColKey,
  type LedgerRow,
  type LogEvent,
  type Sku,
  type SkuSpec,
} from '../data/seed'

export const INTERVAL_MS: Record<Speed, number> = { 0.5: 1900, 1: 950, 2: 480, 4: 240, 8: 120 }

export type Speed = 0.5 | 1 | 2 | 4 | 8

export interface LiveEvent extends LogEvent {
  id: number
  tick: number
}

export interface EngineState {
  rows: Sku[]
  events: LiveEvent[]
  ledger: LedgerRow[]
  paused: boolean
  speed: Speed
  tickCount: number
  bytes: number
  cellsWritten: number
  refusedCount: number
  conflictsOpen: number
  conflictsResolved: number
  changedOutcomes: number
  retrains: number
  idle: boolean
}

const ROW_END_BYTES = 96
const BLOCKED_URLS: Array<{ url: string; why: string }> = [
  { url: 'https://www.amazon.com/dp/B0ABC123XYZ', why: 'forbidden e-commerce domain' },
  { url: 'https://www.ebay.com/itm/314159265358', why: 'forbidden e-commerce domain' },
  { url: 'https://www.target.com/p/nibco-bv100', why: 'forbidden e-commerce domain' },
  { url: 'https://www.walmart.com/ip/xxxxxx', why: 'forbidden e-commerce domain' },
]

const KIND_LABEL = {
  spec: 'spec sheet',
  manual: 'manual',
  page: 'product page',
  nameplate: 'nameplate',
  video: 'video',
} as const

const ACTIVE_STAGES: Sku['stage'][] = ['queued', 'discover', 'extract', 'audit']

export class SemiEngine {
  private spec: SkuSpec[]
  private rng: () => number
  private eventId = 0
  private touchedId: string | null = null
  state: EngineState

  constructor(seed = 20260816) {
    this.rng = mulberry32(seed)
    this.spec = genPlans(seed)
    const rows: Sku[] = this.spec.map((s, i) => {
      const sku = buildSku(s, i, mulberry32(seed + i + 7))
      sku.id = `sku-${i + 1}`
      return sku
    })
    this.state = {
      rows,
      events: [],
      ledger: [],
      paused: false,
      speed: 1,
      tickCount: 0,
      bytes: 0,
      cellsWritten: 0,
      refusedCount: 0,
      conflictsOpen: 0,
      conflictsResolved: 0,
      changedOutcomes: 0,
      retrains: 0,
      idle: false,
    }
  }

  private push(
    origin: LogEvent['origin'],
    sku: Sku | null,
    label: string,
    detail?: string,
    bytes?: number,
  ) {
    this.state.events.unshift({
      id: this.eventId++,
      tick: this.state.tickCount,
      at: Date.now(),
      pid: sku?.id ?? null,
      sku: sku?.pn ?? 'SYS',
      mfr: sku?.mfr ?? 'SYS',
      origin,
      label,
      detail,
      bytes,
    })
    if (this.state.events.length > 320) this.state.events.length = 320
  }

  private activeSku(): Sku | null {
    return this.state.rows.find((r) => ACTIVE_STAGES.includes(r.stage)) ?? null
  }

  tick() {
    if (this.state.paused) return
    this.state.tickCount++

    if (this.state.tickCount % 31 === 0) this.blockedUrlEvent()
    if (this.state.tickCount % 59 === 0) this.sheetSyncEvent()

    const sku = this.activeSku()
    this.state.idle = !sku
    if (sku) {
      this.touchedId = sku.id
      this.stepSku(sku)
      this.commitTouched()
    }
  }

  private commitTouched() {
    const id = this.touchedId
    this.touchedId = null
    if (!id) return
    const rows = this.state.rows
    const i = rows.findIndex((r) => r.id === id)
    if (i === -1) return
    const copy = rows.slice()
    copy[i] = { ...copy[i] }
    this.state.rows = copy
  }

  private blockedUrlEvent() {
    const pick = BLOCKED_URLS[Math.floor(this.rng() * BLOCKED_URLS.length)]
    this.push('validator', null, `Validator · blocked ${pick.url.replace('https://www.', '')}`, pick.why)
  }

  private sheetSyncEvent() {
    const done = this.state.rows.filter((r) => r.stage === 'done').length
    const conflicts = this.state.rows.filter((r) => r.stage === 'conflict').length
    this.push(
      'sheet',
      null,
      'Sheet SYNC · unilog_output.xlsx',
      `${done} rows · ${this.state.cellsWritten} cells · ${(this.state.bytes / 1024).toFixed(1)} KB — conflicts ${conflicts}, refused ${this.state.refusedCount}`,
    )
  }

  private stepSku(sku: Sku) {
    switch (sku.stage) {
      case 'queued':
        sku.stage = 'discover'
        this.push('discover', sku, `Discovery · ${sku.pn}`, `manufacturer ${sku.mfr} · entering`)
        return
      case 'discover':
        if (sku.discStep < sku.sourceMax) {
          const src = sku.sources[sku.discStep++]
          this.push('discover', sku, `Found ${KIND_LABEL[src.kind]}`, `${src.ref} · authority ${src.authority.toFixed(2)}`)
        } else {
          sku.stage = 'extract'
          this.push('discover', sku, 'Discovery complete', `${sku.sources.length} sources kept`)
        }
        return
      case 'extract': {
        const col = this.nextCellKey(sku)
        if (!col) {
          sku.stage = 'audit'
          sku.audits = AUDIT_LABELS.map((a) => ({ label: a.label, state: 'run' as const, note: '' }))
          this.push('audit', sku, `Auditing ${sku.pn}`, `${sku.sources.length} sources · 5 checks`)
          return
        }
        const cell = sku.cells[col]
        if (cell.state === 'blank') {
          cell.state = 'reading'
          this.push('extract', sku, `Reading ${col}`, `${sku.sources[0].ref.split('/')[0]} · page 1`)
        } else {
          const { conf, ci } = this.confFor(col)
          cell.state = 'written'
          cell.conf = conf
          cell.ci = ci
          this.state.cellsWritten++
          this.state.bytes += 24 + cell.display.length
          this.push('sheet', sku, `Sheet write · ${col}`, `${cell.display} · conf ${conf.toFixed(2)}`, 12 + cell.display.length)
        }
        return
      }
      case 'audit': {
        const pending = sku.audits.find((a) => a.state === 'run')
        if (!pending) {
          this.finishAudit(sku)
          return
        }
        const idx = sku.audits.indexOf(pending)
        const fail = this.isAuditFailing(sku, idx)
        pending.state = fail ? 'fail' : 'pass'
        pending.note = fail ? this.failNote(sku, idx) : this.passNote(sku, idx)
        this.push('audit', sku, `${pending.label} → ${fail ? 'FAIL' : 'PASS'}`, pending.note)
        return
      }
      default:
        return
    }
  }

  private nextCellKey(sku: Sku): ColKey | null {
    for (const col of COL_KEYS) {
      const c = sku.cells[col]
      if (c.state === 'blank' || c.state === 'reading') return col
    }
    return null
  }

  private confFor(_col: ColKey): { conf: number; ci: [number, number] } {
    const conf = Math.min(0.99, Math.max(0.74, 0.84 + this.rng() * 0.15))
    return { conf, ci: [Math.max(0.2, conf - 0.09), Math.min(1, conf + 0.05)] }
  }

  private passNote(sku: Sku, idx: number): string {
    if (idx === 1) return `${Math.max(2, sku.sources.length)} sources agree after normalisation`
    if (idx === 2) return 'fits family physics curve'
    if (idx === 4) return 'CI above 0.7 emit threshold'
    return 'within limits'
  }

  private failNote(sku: Sku, idx: number): string {
    if (sku.conflict && idx === 1) return `contradiction: ${sku.conflict.a.value} vs ${sku.conflict.b.value}`
    if (idx === 4) return 'CI crosses 0.7 emit threshold'
    if (idx === 2) return 'single source, no cross-check'
    return 'insufficient evidence'
  }

  private isAuditFailing(sku: Sku, idx: number): boolean {
    if (idx === 1 && sku.conflict) return true
    if (idx === 2 && sku.sources.length < 2) return true
    if (idx === 4 && this.refusedCol(sku) !== null) return true
    return false
  }

  private refusedCol(sku: Sku): ColKey | null {
    const spec = this.spec.find((s) => s.pn === sku.pn && s.mfr === sku.mfr)
    return spec?.refused ? 'flow' : null
  }

  private finishAudit(sku: Sku) {
    if (sku.conflict) {
      sku.stage = 'conflict'
      this.state.conflictsOpen++
      const cell = sku.cells[sku.conflict.col]
      cell.state = 'conflict'
      this.push(
        'audit',
        sku,
        'Conflicting values flagged',
        `${sku.conflict.a.value} (${sku.conflict.a.authority.toFixed(2)}) vs ${sku.conflict.b.value} (${sku.conflict.b.authority.toFixed(2)})`,
      )
      return
    }
    const refusedCol = this.refusedCol(sku)
    if (refusedCol) {
      sku.stage = 'refused'
      this.state.refusedCount++
      const cell = sku.cells[refusedCol]
      cell.state = 'refused'
      cell.display = 'INSUFFICIENT EVIDENCE'
      this.push('sheet', sku, `Refused · ${refusedCol}`, 'INSUFFICIENT EVIDENCE — refusing to guess')
      return
    }
    sku.stage = 'done'
    this.state.bytes += ROW_END_BYTES
    this.push('sheet', sku, 'Accepted → written to sheet', `${COL_KEYS.length} cells · row complete`, ROW_END_BYTES)
  }

  resolve(skuId: string, choice: 'A' | 'B', note: string) {
    const sku = this.state.rows.find((r) => r.id === skuId)
    if (!sku || !sku.conflict || sku.stage !== 'conflict') return
    const c = sku.conflict
    const side = choice === 'A' ? c.a : c.b
    const cell = sku.cells[c.col]
    cell.state = 'written'
    cell.value = side.value
    cell.display = side.value
    cell.conf = Math.min(0.98, side.authority + 0.03)
    sku.stage = 'done'
    this.state.conflictsOpen--
    this.state.conflictsResolved++
    const changed = choice === 'B'
    if (changed) this.state.changedOutcomes++
    this.state.ledger.unshift({
      at: Date.now(),
      sig: `${c.a.value} vs ${c.b.value}`,
      resolution: side.value,
      note: note || 'admin override',
      sku: sku.pn,
      changedOutcome: changed,
      sourceUrl: side.sourceUrl,
    })
    this.state.retrains = Math.floor(this.state.ledger.length / 5)
    this.push('ledger', sku, `Ledger write · ${sku.pn}`, `${side.value} · outcome_changed=${changed}`)
    this.touchedId = skuId
    this.commitTouched()
  }

  refuse(skuId: string) {
    const sku = this.state.rows.find((r) => r.id === skuId)
    if (!sku || !sku.conflict || sku.stage !== 'conflict') return
    const c = sku.conflict
    const cell = sku.cells[c.col]
    cell.state = 'refused'
    cell.display = 'INSUFFICIENT EVIDENCE'
    sku.stage = 'refused'
    this.state.conflictsOpen--
    this.state.refusedCount++
    this.push('sheet', sku, 'Refused after review', `INSUFFICIENT EVIDENCE — ${c.a.value} / ${c.b.value} both plausible`)
    this.touchedId = skuId
    this.commitTouched()
  }

  setSpeed(speed: Speed) {
    this.state.speed = speed
  }

  setPaused(paused: boolean) {
    this.state.paused = paused
  }

  reset() {
    this.state.rows = this.spec.map((s, i) => {
      const sku = buildSku(s, i, mulberry32(Date.now() % 1000000007 + i + 7))
      sku.id = `sku-${i + 1}`
      return sku
    })
    this.state.events = []
    this.state.ledger = []
    this.state.tickCount = 0
    this.state.bytes = 0
    this.state.cellsWritten = 0
    this.state.refusedCount = 0
    this.state.conflictsOpen = 0
    this.state.conflictsResolved = 0
    this.state.changedOutcomes = 0
    this.state.retrains = 0
  }
}
