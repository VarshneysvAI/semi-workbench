import { useEffect, useState } from 'react'
import { Pause, Play, RotateCw, Menu } from 'lucide-react'
import { useSemi } from '../engine/SemiContext'
import { StatusDot } from './ui'
import type { Speed } from '../engine/engine'

const SPEEDS: Speed[] = [0.5, 1, 2, 4, 8]

export default function Header({ onToggleNav }: { onToggleNav: () => void }) {
  const { engine, summary, running, speed, setRunning, setSpeedBy, resetEngine } = useSemi()
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const iv = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(iv)
  }, [])

  const active =
    engine.state.rows.find((r) => ['discover', 'extract', 'audit'].includes(r.stage)) ?? null

  const worked = summary.rowsDone + summary.rowsConflict + summary.rowsRefused

  return (
    <header className="flex h-14 shrink-0 items-center gap-4 border-b border-white/[0.08] bg-black/25 px-4 backdrop-blur-md">
      <button
        onClick={onToggleNav}
        className="focus-ring mr-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/[0.12] bg-white/[0.05] text-slate-300 transition-colors hover:border-white/[0.22] hover:text-white"
        title="Toggle navigation"
      >
        <Menu size={15} />
      </button>

      <div className="flex items-center gap-2">
        <StatusDot tone={running ? 'live' : 'idle'} />
        <span className="mono text-[12.5px] font-medium uppercase tracking-[0.14em] text-slate-200">
          {running ? 'Worker streaming' : 'Engine paused'}
        </span>
      </div>

      {active ? (
        <div className="mono hidden min-w-0 items-center gap-2 truncate text-[11px] text-slate-500 md:flex">
          <span className="text-accent-strong">{active.mfr}</span>
          <span className="text-slate-300">{active.pn}</span>
          <span className="rounded border border-line bg-ink-3 px-1.5 py-0.5 text-[9.5px] uppercase tracking-wider text-slate-400">
            {active.stage}
          </span>
          {active.stage === 'extract' ? (
            <span className="caret-live max-w-[220px] truncate text-slate-400">
              writing {activeSkuColLabel(active)}
            </span>
          ) : null}
        </div>
      ) : (
        <span className="mono hidden text-[11px] text-slate-600 md:inline">
          {engine.state.idle ? 'batch complete' : 'engine idle'}
        </span>
      )}

      <div className="flex-1" />

      <div className="mono hidden items-center gap-3 text-[11px] text-slate-500 sm:flex">
        <span className="flex items-center gap-1.5 text-emerald-300">
          <StatusDot tone={running ? 'live' : 'ok'} />
          {worked}/{summary.rowsTotal} rows
        </span>
        <span className="font-num">cells {summary.cellsWritten}</span>
        <span className="hidden font-num lg:inline">{(engine.state.bytes / 1024).toFixed(1)} KB</span>
        <span className="hidden font-num xl:inline">
          {now.toLocaleTimeString('en-GB', { hour12: false })}
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        {SPEEDS.map((s) => (
          <button
            key={s}
            onClick={() => setSpeedBy(s)}
            className={`mono focus-ring rounded-md border px-2 py-1 text-[11.5px] transition-colors ${
              speed === s
                ? 'border-accent bg-accent-10 text-accent-strong'
                : 'border-white/[0.12] text-slate-500 hover:text-slate-200'
            }`}
          >
            {s}×
          </button>
        ))}
        <button onClick={() => setRunning(!running)} className="btn ml-1">
          {running ? <Pause size={12} /> : <Play size={12} />}
          {running ? 'Pause' : 'Run'}
        </button>
        <button onClick={resetEngine} className="btn" title="Re-seed the sheet with a fresh drawing">
          <RotateCw size={12} />
          Reset
        </button>
      </div>
    </header>
  )
}

function activeSkuColLabel(sku: { cells: Record<string, { state: string }> }) {
  for (const k of Object.keys(sku.cells)) {
    if (sku.cells[k].state === 'reading') return k
  }
  return ''
}