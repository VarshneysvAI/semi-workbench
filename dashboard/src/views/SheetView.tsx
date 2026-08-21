import { memo, useMemo, useState } from 'react'
import { Search } from 'lucide-react'
import { useSemi } from '../engine/SemiContext'
import Inspector from '../components/Inspector'
import { Badge, ProgressBar } from '../components/ui'
import { STAGE_LABELS, type Sku, type Stage } from '../data/seed'

type StageFilter = 'all' | Stage

export default function SheetView() {
  const { engine, summary, select, selectedId } = useSemi()
  const [q, setQ] = useState('')
  const [mfr, setMfr] = useState<'all' | string>('all')
  const [stageFilter, setStageFilter] = useState<StageFilter>('all')

  const rows = useMemo(() => {
    const term = q.trim().toLowerCase()
    return engine.state.rows.filter((r: Sku) => {
      if (mfr !== 'all' && r.mfr !== mfr) return false
      if (stageFilter !== 'all' && r.stage !== stageFilter) return false
      if (term && !r.pn.toLowerCase().includes(term) && !r.id.toLowerCase().includes(term)) return false
      return true
    })
  }, [engine.state.rows, q, mfr, stageFilter])

  const mfrList = useMemo(() => {
    const set = new Set<string>()
    engine.state.rows.forEach((r: Sku) => set.add(r.mfr))
    return Array.from(set).sort()
  }, [engine.state.rows])

  const colKeys = useMemo(() => {
    const set = new Set<string>()
    engine.state.rows.forEach((r: Sku) => {
      Object.keys(r.cells).forEach(k => set.add(k))
    })
    return Array.from(set)
  }, [engine.state.rows])

  const active = engine.state.rows.find((r: Sku) => ['discover', 'extract', 'audit'].includes(r.stage))

  return (
    <div className="flex h-full min-h-0">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center gap-2 border-b border-white/[0.08] px-4 py-2.5">
          <h1 className="mono mr-auto text-[14.5px] font-semibold text-slate-100">
            unilog_output.xlsx
            <span className="ml-2 normal-case text-[11px] font-normal text-slate-500">live enrichment sheet</span>
          </h1>

          <div className="flex items-center gap-1.5 rounded-lg border border-white/[0.12] bg-white/[0.04] px-2.5 py-1">
            <Search size={13} className="text-slate-400" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="filter SKU / part no…"
              aria-label="Filter by SKU or part number"
              className="mono w-48 bg-transparent text-[12px] text-slate-100 placeholder:text-slate-500 focus:outline-none"
            />
          </div>

          <select
            value={mfr}
            onChange={(e) => setMfr(e.target.value)}
            aria-label="Filter by manufacturer"
            className="mono focus-ring rounded-md border border-white/[0.12] bg-white/[0.04] px-2 py-1.5 text-[12px] text-slate-200"
          >
            <option value="all">all manufacturers</option>
            {mfrList.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          <div className="flex items-center gap-1">
            {(['all', 'queued', 'discover', 'extract', 'audit', 'done', 'conflict', 'refused'] as StageFilter[]).map((s) => (
              <button
                key={s}
                onClick={() => setStageFilter(s)}
                className={`mono focus-ring rounded-md border px-2 py-1.5 text-[11px] transition-colors ${
                  stageFilter === s
                    ? 'border-accent bg-accent-10 text-accent-strong'
                    : 'border-white/[0.12] text-slate-400 hover:text-slate-100'
                }`}
              >
                {s === 'all' ? 'ALL' : STAGE_LABELS[s as Stage]}
              </button>
            ))}
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-auto overscroll-contain">
          <div className="grid min-w-[1300px]" style={{ gridTemplateColumns: `44px 118px 92px repeat(${colKeys.length}, minmax(88px, 1fr)) 120px` }}>
            <HeaderRow colKeys={colKeys} />
            {rows.map((r: Sku, i: number) => (
              <RowMemo
                key={r.id}
                sku={r}
                index={i}
                active={active?.id === r.id}
                selected={selectedId === r.id}
                onSelect={select}
                colKeys={colKeys}
              />
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4 border-t border-white/[0.08] px-4 py-2.5">
          <div className="mono text-[12px] text-slate-400">
            {rows.length} rows visible · {summary.rowsDone + summary.rowsConflict + summary.rowsRefused} worked of {summary.rowsTotal}
          </div>
          <div className="flex flex-1 items-center gap-3">
            <ProgressBar
              pct={summary.donePct}
              className="h-1 w-40"
            />
            <span className="mono font-num text-[11px] text-slate-500">{summary.donePct.toFixed(1)}% accepted</span>
          </div>
          <div className="mono flex items-center gap-3 text-[11.5px]">
            <Legend color="#22d3ee" label="writing" />
            <Legend color="#34d399" label="accepted" />
            <Legend color="#fbbf24" label="conflict" />
            <Legend color="#fb7185" label="refused" />
          </div>
        </div>
      </div>

      <Inspector />
    </div>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1 text-slate-500">
      <span className="h-1.5 w-1.5 rounded-sm" style={{ background: color }} />
      {label}
    </span>
  )
}

const RowMemo = memo(
  Row,
  (prev, next) =>
    prev.index === next.index &&
    prev.sku === next.sku &&
    prev.active === next.active &&
    prev.selected === next.selected,
)

function HeaderRow({ colKeys }: { colKeys: string[] }) {
  return (
    <>
      <div className="sticky top-0 z-10 border-b border-white/[0.09] bg-[#0a0a0d]/95 px-2 py-1.5 text-right font-mono text-[10px] text-slate-500">
        #
      </div>
      <div className="sticky top-0 z-10 border-b border-white/[0.09] bg-[#0a0a0d]/95 px-2 py-1.5 font-mono text-[10.5px] font-medium overflow-hidden whitespace-nowrap text-slate-300">
        {colLetter(0)} · SKU
      </div>
      <div className="sticky top-0 z-10 border-b border-white/[0.09] bg-[#0a0a0d]/95 px-2 py-1.5 font-mono text-[10.5px] font-medium text-slate-300">
        {colLetter(1)} · MFR
      </div>
      {colKeys.map((k, i) => (
        <div key={k} className="sticky top-0 z-10 border-b border-white/[0.09] bg-[#0a0a0d]/95 px-2 py-1.5">
          <div className="font-mono text-[10.5px] font-semibold overflow-hidden whitespace-nowrap text-slate-200">
            {colLetter(i + 2)} · {k}
          </div>
          <div className="font-mono text-[8.5px] text-slate-500">—</div>
        </div>
      ))}
      <div className="sticky top-0 z-10 border-b border-white/[0.09] bg-[#0a0a0d]/95 px-2 py-1.5 font-mono text-[10.5px] font-medium text-slate-300">
        STATUS
      </div>
    </>
  )
}

function colLetter(i: number) {
  return i < 26 ? String.fromCharCode(65 + i) : ''
}

function Row({
  sku,
  index,
  active,
  selected,
  onSelect,
  colKeys,
}: {
  sku: Sku
  index: number
  active: boolean
  selected: boolean
  onSelect: (id: string) => void
  colKeys: string[]
}) {
  const bg = selected
    ? 'bg-accent-05'
    : active
      ? 'bg-accent-05'
      : index % 2 === 1
        ? 'bg-white/[0.012]'
        : ''

  return (
    <div
      className={`grid cursor-pointer items-center border-b border-white/[0.06] transition-colors hover:bg-white/[0.04] ${bg}`}
      style={{ gridColumn: '1 / -1', gridTemplateColumns: 'inherit' }}
      onClick={() => onSelect(sku.id)}
    >
      <div className="px-2 text-right font-mono text-[10px] text-slate-500">{index + 1}</div>
      <SkuCell sku={sku} />
      <div className="mono truncate px-2 text-[11.5px] overflow-hidden whitespace-nowrap text-slate-300">{sku.mfr}</div>
      {colKeys.map((k) => (
        <ValueCell key={k} sku={sku} col={k} />
      ))}
      <div className="px-2">
        <StageBadge stage={sku.stage} />
      </div>
    </div>
  )
}

function SkuCell({ sku }: { sku: Sku }) {
  return (
    <div className="mono flex items-center gap-1.5 px-2">
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${stageDot(sku.stage)}`} />
      <span className="truncate text-[12.5px] overflow-hidden whitespace-nowrap font-medium text-slate-100">{sku.pn}</span>
    </div>
  )
}

function ValueCell({ sku, col }: { sku: Sku; col: string }) {
  const cell = sku.cells[col]

  if (!cell) {
    return (
      <div className={`flex h-full items-center justify-end gap-1.5 border-r border-white/[0.05] px-2 py-1 font-mono`}>
        <span className="text-[11.5px] text-slate-600">—</span>
      </div>
    )
  }

  return (
    <div className={`flex h-full items-center justify-end gap-1.5 border-r border-white/[0.05] px-2 py-1 font-mono min-w-0 overflow-hidden`}>
      {cell.state === 'blank' ? (
        <span className="text-[11.5px] text-slate-600">—</span>
      ) : cell.state === 'reading' ? (
        <span key={`r:${col}`} className={`scan-line flex items-center text-[11.5px] text-accent-strong`}>
          <span className="caret-live">scn·{col}</span>
        </span>
      ) : cell.state === 'written' ? (
        <div key={`w:${cell.display}:${cell.conf}`} className="flex items-center gap-1.5 min-w-0 w-full justify-end">
          <span className="cell-write rounded px-1 text-[12px] text-slate-50 truncate text-right block" title={cell.display}>{cell.display}</span>
          <span className="mono font-num text-[9.5px]" style={{ color: confColor(cell.conf) }}>
            {cell.conf.toFixed(2)}
          </span>
        </div>
      ) : cell.state === 'conflict' ? (
        <span key={`c:${col}`} className="rounded bg-amber-400/15 px-1.5 py-0.5 text-[10.5px] text-amber-200">CONFLICT</span>
      ) : (
        <span key={`r:${col}`} className="rounded bg-rose-400/15 px-1.5 py-0.5 text-[10.5px] text-rose-300">REFUSED</span>
      )}
    </div>
  )
}

function StageBadge({ stage }: { stage: Stage }) {
  const tone = { queued: 'slate', discover: 'cyan', extract: 'cyan', audit: 'amber', done: 'emerald', conflict: 'amber', refused: 'rose' } as const
  return <Badge tone={tone[stage]}>{STAGE_LABELS[stage]}</Badge>
}

function stageDot(stage: Stage) {
  return stage === 'done'
    ? 'bg-emerald-400'
    : stage === 'conflict'
      ? 'bg-amber-400'
      : stage === 'refused'
        ? 'bg-rose-400'
        : stage === 'queued'
          ? 'bg-slate-600'
          : 'bg-cyan-400 dot-live'
}

function confColor(conf: number) {
  return conf >= 0.91 ? '#34d399' : conf >= 0.79 ? '#fbbf24' : '#fb7185'
}