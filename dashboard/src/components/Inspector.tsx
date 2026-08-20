import { X } from 'lucide-react'
import { useSemi } from '../engine/SemiContext'
import { Badge, StatusDot, SectionTitle } from './ui'
import { STAGE_LABELS, type Sku } from '../data/seed'

const CELL_KEYS = ['pressure', 'temp', 'material', 'thread', 'size', 'flow'] as const

export default function Inspector({ showCloser = true }: { showCloser?: boolean }) {
  const { selectedSku, select, engine, resolveRow, refuseRow } = useSemi()

  if (!selectedSku) {
    return (
      <aside className="hidden w-[330px] shrink-0 flex-col border-l border-line bg-ink-2/50 p-4 lg:flex">
        <div className="flex flex-1 items-center justify-center">
          <div className="max-w-[220px] text-center">
            <div className="mono mx-auto mb-3 flex h-9 w-9 items-center justify-center rounded-lg border border-dashed border-white/15 text-[11px] text-slate-600">
              detail
            </div>
            <p className="text-[12px] leading-relaxed text-slate-500">
              Select a row in the sheet to inspect its live evidence chain, transcript and audits.
            </p>
          </div>
        </div>
      </aside>
    )
  }

  const sku = selectedSku
  const cellKeys = Object.keys(sku.cells || {})
  const displayKeys = cellKeys.length > 0 ? cellKeys : ['Mfg_Part_Num', 'Part_Desc', 'Unilog_Brand', 'Part_Manuf', 'Material', 'Voltage']
  const log = engine.state.events.filter((e) => e.sku === sku.pn || e.pid === sku.id || (e.label && e.label.includes(sku.pn))).slice(0, 14)

  return (
    <aside className="hidden w-[340px] shrink-0 flex-col border-l border-line bg-ink-2/60 lg:flex">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="mono text-[13px] font-semibold text-slate-100">{sku.pn}</span>
          <Badge tone="cyan">{sku.mfr}</Badge>
        </div>
        {showCloser ? (
          <button onClick={() => select(null)} className="focus-ring rounded p-1 text-slate-500 hover:text-slate-200">
            <X size={14} />
          </button>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        <div className="mb-3 flex items-center gap-2">
          <StatusDot tone={stageTone(sku)} />
          <span className="mono text-[12px] font-medium text-slate-200">{STAGE_LABELS[sku.stage]}</span>
          {sku.stage === 'conflict' ? <Badge tone="amber">needs review</Badge> : null}
          {sku.stage === 'refused' ? <Badge tone="rose">flagged</Badge> : null}
        </div>

        <SectionTitle right={null}>Attributes written</SectionTitle>
        <div className="mb-4 space-y-1">
          {displayKeys.map((k) => (
            <CellRowDetail key={k} sku={sku} col={k} />
          ))}
        </div>


        <SectionTitle right={null}>Sources</SectionTitle>
        <div className="mb-4 space-y-1">
          {(sku.sources || []).map((s) => (
            <div key={s.key || s.ref} className="flex items-center justify-between rounded-md border border-line bg-ink-3 px-2 py-1.5">
              <div className="min-w-0">
                <div className="mono truncate text-[10.5px] text-slate-300">{s.ref}</div>
                <div className="mono truncate text-[9.5px] text-slate-600">{s.sourceUrl}</div>
              </div>
              <span className="mono shrink-0 text-[10px] text-slate-500">{(s.authority || 0.85).toFixed(2)}</span>
            </div>
          ))}
        </div>

        <SectionTitle right={null}>Audits</SectionTitle>
        <div className="mb-4 space-y-1">
          {(sku.audits || []).length ? (
            (sku.audits || []).map((a) => (
              <div key={a.label} className="flex items-center justify-between rounded-md border border-line bg-ink-3 px-2 py-1.5">
                <div className="min-w-0">
                  <div className="text-[11px] text-slate-300">{a.label}</div>
                  {a.note ? <div className="mono truncate text-[9.5px] text-slate-600">{a.note}</div> : null}
                </div>
                <span className="mono shrink-0 text-[10px]">
                  {a.state === 'run' ? <span className="text-slate-500">…</span> : a.state === 'pass' ? <span className="text-emerald-400">PASS</span> : <span className="text-rose-400">FAIL</span>}
                </span>
              </div>
            ))
          ) : (
            <div className="text-[11px] text-slate-600">no audits yet — queued</div>
          )}
        </div>

        <SectionTitle right={null}>Transcript</SectionTitle>
        <div className="mb-4 space-y-1 rounded-md border border-line bg-ink-3/60 p-2">
          {log.length ? (
            log.map((e) => (
              <div key={e.id} className="mono flex gap-2 text-[9.5px] leading-relaxed text-slate-500">
                <span className="shrink-0 text-slate-700">t{e.tick}</span>
                <span className="shrink-0" style={{ color: originColor(e.origin) }}>
                  [{e.origin}]
                </span>
                <span className="min-w-0 flex-1 truncate">{e.label}</span>
              </div>
            ))
          ) : (
            <div className="text-[10.5px] text-slate-600">no transcript yet</div>
          )}
        </div>

        <ConflictGate sku={sku} resolveRow={resolveRow} refuseRow={refuseRow} />
      </div>
    </aside>
  )
}

function CellRowDetail({ sku, col }: { sku: Sku; col: string }) {
  const cell = sku.cells?.[col]
  const val = cell?.display || cell?.value || ''
  const isBlank = !cell || cell.state === 'blank' || !val || val === '—' || val === '0.00'

  return (
    <div className="flex items-center justify-between rounded-md border border-line bg-ink-3 px-2 py-1.5">
      <div className="min-w-0">
        <div className="label-caps mb-0.5">{col}</div>
        <div className="mono truncate text-[11.5px] font-medium text-slate-200">
          {isBlank ? <span className="text-slate-600">—</span> : val}
        </div>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-0.5">
        {isBlank ? (
          <span className="mono text-[9.5px] text-slate-600">pending write</span>
        ) : (
          <>
            <span className="mono font-num text-[10px]" style={{ color: confColor(cell?.conf || 0.95) }}>
              {(cell?.conf || 0.95).toFixed(2)}
            </span>
            <span className="mono font-num text-[9px] text-slate-500">
              [{(cell?.ci?.[0] || 0.88).toFixed(2)} – {(cell?.ci?.[1] || 0.99).toFixed(2)}]
            </span>
          </>
        )}
      </div>
    </div>
  )
}




function ConflictGate({
  sku,
  resolveRow,
  refuseRow,
}: {
  sku: Sku
  resolveRow: (id: string, choice: 'A' | 'B', note: string) => void
  refuseRow: (id: string) => void
}) {
  if (sku.stage !== 'conflict' || !sku.conflict) return null
  const c = sku.conflict
  return (
    <div className="rounded-lg border border-amber-400/25 bg-amber-400/[0.06] p-3">
      <div className="mb-2 text-[11px] font-semibold text-amber-200">
        Conflict · {c.col} — resolve to write ledger row
      </div>
      <div className="space-y-1.5">
        <ConflictSideCard
          label="A"
          value={c.a.value}
          from={c.a.from}
          authority={c.a.authority}
          action="Adopt →"
          onAction={() => resolveRow(sku.id, 'A', 'spec_sheet_authority')}
        />
        <ConflictSideCard
          label="B"
          value={c.b.value}
          from={c.b.from}
          authority={c.b.authority}
          action="Adopt →"
          onAction={() => resolveRow(sku.id, 'B', 'admin override')}
        />
      </div>
      <button onClick={() => refuseRow(sku.id)} className="mono mt-2 w-full rounded-md border border-line bg-ink-3 py-1.5 text-[10.5px] text-slate-400 hover:text-slate-200">
        REFUSE — INSUFFICIENT EVIDENCE
      </button>
      <div className="mono mt-2 text-[9px] leading-relaxed text-slate-600">
        ledger_changed_outcome flips to true when the non-default side wins.
      </div>
    </div>
  )
}

function ConflictSideCard({
  label,
  value,
  from,
  authority,
  action,
  onAction,
}: {
  label: 'A' | 'B'
  value: string
  from: string
  authority: number
  action: string
  onAction: () => void
}) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-md border border-line bg-ink-3 px-2 py-1.5">
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="mono text-[10px] font-bold text-cyan-300">{label}</span>
          <span className="mono text-[11px] text-slate-100">{value}</span>
        </div>
        <div className="mono truncate text-[9px] text-slate-600">{from} · auth {authority.toFixed(2)}</div>
      </div>
      <button onClick={onAction} className="focus-ring shrink-0 rounded border-accent bg-accent-10 px-2 py-1 text-[10px] text-accent-strong hover:bg-accent-05">
        {action}
      </button>
    </div>
  )
}

function stageTone(sku: Sku) {
  return sku.stage === 'done' ? 'ok' : sku.stage === 'conflict' ? 'warn' : sku.stage === 'refused' ? 'danger' : 'live'
}

function confColor(conf: number) {
  return conf >= 0.91 ? '#34d399' : conf >= 0.79 ? '#fbbf24' : '#fb7185'
}

function originColor(origin: string) {
  const c: Record<string, string> = {
    discover: '#34d399',
    extract: '#93c5fd',
    audit: '#fbbf24',
    sheet: '#22d3ee',
    ledger: '#a78bfa',
    validator: '#fb7185',
  }
  return c[origin] ?? '#64748b'
}