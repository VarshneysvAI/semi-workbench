import { useEffect, useState } from 'react'
import { Upload, Download, Menu } from 'lucide-react'
import { useSemi } from '../engine/SemiContext'
import { StatusDot } from './ui'

import { getApiUrl } from '../config'

export default function Header({ onToggleNav }: { onToggleNav: () => void }) {
  const { engine, summary, running, live, startJob } = useSemi()
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const iv = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(iv)
  }, [])

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const concurrencyStr = prompt("Concurrency (1 for Free Tier, 2-5 for Pro):", "1")
    const concurrency = parseInt(concurrencyStr || "1", 10) || 1
    startJob(file, concurrency)
  }

  const handleExport = () => {
    if (engine.state.jobId) {
      window.location.href = getApiUrl(`/api/jobs/${engine.state.jobId}/files/Unihack_Delivery_Format_Output.csv`)
    } else {
      window.location.href = getApiUrl('/api/export_unilog')
    }
  }



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
        {live !== 'sim' ? (
          <span
            className={`flex items-center gap-1.5 ${
              live === 'live' ? 'text-emerald-300' : 'text-slate-400'
            }`}
          >
            <StatusDot tone={live === 'live' ? 'ok' : 'idle'} />
            backend {live === 'live' ? 'live' : 'probe…'}
          </span>
        ) : null}
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
        <label className="btn cursor-pointer">
          <Upload size={12} />
          Upload Catalog
          <input type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={handleUpload} />
        </label>
        <button onClick={handleExport} className="btn ml-1" title="Download Results">
          <Download size={12} />
          Export CSV
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