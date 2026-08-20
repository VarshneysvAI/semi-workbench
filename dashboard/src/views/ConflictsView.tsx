import { useMemo } from 'react'
import { useSemi } from '../engine/SemiContext'
import { Badge, StatusDot } from '../components/ui'
import type { Sku } from '../data/seed'

export default function ConflictsView() {
  const { engine, resolveRow, select, selectedId, summary } = useSemi()

  const conflicts = useMemo(
    () => engine.state.rows.filter((r: any) => r.stage === 'conflict'),
    [engine.state.rows],
  )

  return (
    <div className="mx-auto max-w-[1200px] space-y-5 p-5">
      <div>
        <h1 className="text-[23px] font-semibold tracking-tight text-slate-100">Review queue</h1>
        <p className="mt-1 text-[13.5px] text-slate-400">
          Human-gated — every resolution writes a ledger row and feeds the classifier
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Badge tone="amber">
          <StatusDot tone="warn" /> {summary.rowsConflict} open
        </Badge>
        <Badge tone="violet">{engine.state.ledger.length} ledger rows</Badge>
        <Badge tone="slate">retrained × {engine.state.retrains}</Badge>
      </div>

      {conflicts.length ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {conflicts.map((sku: Sku) => (
            <ConflictCard
              key={sku.id}
              sku={sku}
              selected={selectedId === sku.id}
              onSelect={select}
              onResolve={resolveRow}
            />
          ))}
        </div>
      ) : (
        <div className="panel flex flex-col items-center py-14 text-center">
          <StatusDot tone="ok" />
          <p className="mt-3 text-[14px] text-slate-300">Queue clear</p>
          <p className="mono mt-1 text-[11.5px] text-slate-500">
            incoming conflicts stream here from the sheet
          </p>
        </div>
      )}
    </div>
  )
}

function ConflictCard({
  sku,
  selected,
  onSelect,
  onResolve,
}: {
  sku: Sku
  selected: boolean
  onSelect: (id: string) => void
  onResolve: (id: string, choice: 'A' | 'B', note: string) => void
}) {
  if (!sku.conflict) return null
  const c = sku.conflict
  return (
    <div
      className={`panel cursor-pointer p-4 transition-colors ${selected ? 'border-accent bg-accent-05' : ''}`}
      onClick={() => onSelect(sku.id)}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="mono text-[14.5px] font-semibold text-slate-50">{sku.pn}</span>
          <Badge tone="cyan">{sku.mfr}</Badge>
        </div>
        <Badge tone="amber">{c.col}</Badge>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <SideBox
          letter="A"
          value={c.a.value}
          from={c.a.from}
          sourceUrl={c.a.sourceUrl}
          authority={c.a.authority}
          accent={false}
          onPick={() => onResolve(sku.id, 'A', 'spec_sheet_authority')}
        />
        <SideBox
          letter="B"
          value={c.b.value}
          from={c.b.from}
          sourceUrl={c.b.sourceUrl}
          authority={c.b.authority}
          accent
          onPick={() => onResolve(sku.id, 'B', 'admin override')}
        />
      </div>

      <div className="mono mt-3 flex items-center justify-between text-[10.5px] text-slate-600">
        <span>written to ledger with source_url</span>
        <span className="text-slate-500">pick a side to close</span>
      </div>
    </div>
  )
}

function SideBox({
  letter,
  value,
  from,
  sourceUrl,
  authority,
  accent,
  onPick,
}: {
  letter: 'A' | 'B'
  value: string
  from: string
  sourceUrl?: string
  authority: number
  accent: boolean
  onPick: () => void
}) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        accent ? 'border-violet-400/25 bg-violet-400/[0.04]' : 'border-white/[0.1] bg-white/[0.03]'
      }`}
    >
      <div className="mb-1 flex items-center justify-between">
        <span className="mono text-[11px] font-bold text-slate-400">{letter}</span>
        <span className="mono font-num text-[11px] text-slate-500">{authority.toFixed(2)}</span>
      </div>
      <div className="mono text-[17px] font-semibold text-slate-100">{value}</div>
      <div className="mono mt-1 truncate text-[10.5px] text-slate-400">{from}</div>
      {sourceUrl ? (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="mono mt-1 block truncate text-[9.5px] text-cyan-400 hover:underline"
        >
          🔗 {sourceUrl}
        </a>
      ) : null}
      <button onClick={onPick} className="btn mt-2.5 w-full justify-center">
        {accent ? 'Adopt B' : 'Adopt A'}
      </button>
    </div>
  )
}