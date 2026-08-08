import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useSemi } from '../engine/SemiContext'
import { Kpi, ProgressBar, Ring, StatusDot, SectionTitle } from '../components/ui'

export default function Overview() {
  const { engine, summary } = useSemi()
  const worked = summary.rowsDone + summary.rowsConflict + summary.rowsRefused
  const events = engine.state.events.slice(0, 26)
  const active = engine.state.rows.find((r) => ['discover', 'extract', 'audit'].includes(r.stage))

  const mfrStats = useMemo(
    () =>
      ['NIBCO', 'WATTS', 'APOLLO'].map((m) => {
        const rows = engine.state.rows.filter((r) => r.mfr === m)
        const done = rows.filter((r) => r.stage === 'done').length
        const srcs = rows.reduce((a, r) => a + r.sources.length, 0)
        return { m, done, total: rows.length, srcs }
      }),
    [engine.state.rows],
  )

  const segments = [
    { w: (summary.rowsDone / summary.rowsTotal) * 100, color: '#34d399', label: 'accept' },
    { w: (summary.rowsConflict / summary.rowsTotal) * 100, color: '#fbbf24', label: 'conflict' },
    { w: (summary.rowsRefused / summary.rowsTotal) * 100, color: '#fb7185', label: 'refuse' },
  ].filter((s) => s.w > 0)

  return (
    <div className="mx-auto max-w-[1400px] space-y-5 p-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-[23px] font-semibold tracking-tight text-slate-100">
            Enrichment overview
          </h1>
          <p className="mt-1 text-[13.5px] text-slate-500">
            Manufacturer intelligence pipeline · workbook in → verified attributes out
          </p>
        </div>
        <Link to="/sheet" className="btn btn-primary">
          Open sheet
        </Link>
      </div>

      <div className="panel p-4">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <div className="label-caps">Signal orbit</div>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-[12px] text-slate-300">
              <span>orbital sweep of manufacturer feeds</span>
              <span className="mono flex items-center gap-1 text-[11.5px] text-slate-500">
                <StatusDot tone={engine.state.idle ? 'idle' : 'live'} />
                {active ? `tracking ${active.pn}` : 'idle'}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {['discover', 'extract', 'audit', 'sheet', 'ledger', 'validator'].map((o) => (
                <span
                  key={o}
                  className="mono inline-flex items-center gap-1 rounded border border-white/[0.08] bg-white/[0.03] px-1.5 py-0.5 text-[9.5px] text-slate-500"
                >
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: originColor(o) }} />
                  {o}
                </span>
              ))}
            </div>
          </div>
          <SimOrbit />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-6">
        <Kpi
          label="Rows worked"
          value={
            <span className="mono">
              {worked}
              <span className="text-[14px] text-slate-500">/{summary.rowsTotal}</span>
            </span>
          }
          sub={<Ring pct={worked / summary.rowsTotal} />}
          tone="accent"
        />
        <Kpi
          label="Cells written"
          value={<span className="mono">{summary.cellsWritten}</span>}
          sub={`of ${summary.cellsTotal} cells`}
          tone="ok"
        />
        <Kpi
          label="Open conflicts"
          value={<span className="mono">{summary.rowsConflict}</span>}
          sub="review queue"
          tone={summary.rowsConflict ? 'warn' : 'default'}
        />
        <Kpi
          label="Refused"
          value={<span className="mono">{summary.rowsRefused}</span>}
          sub="insufficient evidence"
          tone={summary.rowsRefused ? 'danger' : 'default'}
        />
        <Kpi
          label="Ledger writes"
          value={<span className="mono">{engine.state.ledger.length}</span>}
          sub={`${engine.state.changedOutcomes} outcome flips`}
          tone="accent"
        />
        <Kpi
          label="Sheet size"
          value={<span className="mono">{(engine.state.bytes / 1024).toFixed(1)}</span>}
          sub="KB written"
          tone="default"
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <div className="panel p-4">
            <SectionTitle
              right={
                <span className="mono text-[11.5px] text-slate-500">
                  {summary.rowsInFlight} in flight · {summary.rowsQueued} queued
                </span>
              }
            >
              <span className="flex items-center gap-2">
                Pipeline progress
                <StatusDot tone={engine.state.idle ? 'ok' : 'live'} />
              </span>
            </SectionTitle>
            <div className="mb-2 flex flex-wrap gap-1.5">
              {segments.map((s) => (
                <span key={s.label} className="mono flex items-center gap-1 text-[11.5px] text-slate-500">
                  <span className="h-2 w-2 rounded-sm" style={{ background: s.color }} />
                  {s.label} {s.w.toFixed(0)}%
                </span>
              ))}
            </div>
            <ProgressBar segments={segments} className="h-2" />
          </div>

          <div className="panel p-4">
            <SectionTitle right={null}>Manufacturer throughput</SectionTitle>
            <div className="grid gap-3 md:grid-cols-3">
              {mfrStats.map((m) => {
                return (
                  <div key={m.m} className="rounded-lg border border-line bg-ink-3 p-3">
                    <div className="mono text-[12px] font-semibold text-slate-200">{m.m}</div>
                    <div className="mono mt-1 font-num text-[12px] text-slate-400">
                      {m.done}/{m.total}
                    </div>
                    <div className="mono mt-0.5 font-num text-[11.5px] text-slate-600">{m.srcs} sources catalogued</div>
                    <ProgressBar pct={m.total ? (m.done / m.total) * 100 : 0} className="mt-2 h-1" />
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          <div className="panel p-4">
            <SectionTitle
              right={<span className="mono text-[11.5px] text-slate-600">tick {engine.state.tickCount}</span>}
            >
              Worker transcript
            </SectionTitle>
            <div className="space-y-1">
              {events.length ? (
                events.map((e) => (
                  <div key={e.id} className="mono flex gap-2 text-[11.5px] leading-relaxed text-slate-500">
                    <span className="shrink-0" style={{ color: originColor(e.origin) }}>
                      [{e.origin}]
                    </span>
                    <span className="min-w-0 flex-1 truncate">{e.label}</span>
                    <span className="shrink-0 text-slate-600">{e.sku}</span>
                  </div>
                ))
              ) : (
                <div className="text-[12px] text-slate-600">engine idle — press Run</div>
              )}
            </div>
          </div>

          <div className="panel p-4">
            <SectionTitle>Sheet transparency</SectionTitle>
            <div className="mono space-y-2 text-[12px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">cell writes</span>
                <span className="font-num text-slate-200">{summary.cellsWritten}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">ledger rows</span>
                <span className="font-num text-slate-200">{engine.state.ledger.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">retrains</span>
                <span className="font-num text-slate-200">{engine.state.retrains}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">blocked sources</span>
                <span className="font-num text-slate-200">{engine.state.events.filter((e) => e.origin === 'validator').length}</span>
              </div>
              {active ? (
                <div className="rounded-md border-accent bg-accent-10 px-2 py-1.5 text-[11.5px] text-accent-strong">
                  <span className="caret-live">writing {active.pn}</span> · {active.stage}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
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

function SimOrbit() {
  const ringPath =
    'M 18 48 C 18 26, 58 14, 110 14 C 162 14, 202 26, 202 48 C 202 70, 162 82, 110 82 C 58 82, 18 70, 18 48 Z'
  return (
    <svg
      viewBox="0 0 220 96"
      className="h-24 w-full max-w-[420px] shrink-0 lg:w-[380px]"
      aria-hidden
    >
      <defs>
        <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" style={{ stopColor: 'var(--accent)', stopOpacity: 0.9 }} />
          <stop offset="100%" style={{ stopColor: 'var(--accent)', stopOpacity: 0 }} />
        </linearGradient>
      </defs>

      <line x1="0" y1="48" x2="220" y2="48" stroke="rgba(148,163,184,0.10)" strokeWidth="1" />
      <ellipse cx="110" cy="48" rx="90" ry="34" fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth="1" />

      <path
        d={ringPath}
        fill="none"
        stroke="url(#sweep)"
        strokeWidth="1.5"
        strokeLinecap="round"
        pathLength={2000}
        strokeDasharray="140 1860"
        className="orbit-sweep"
      />

      <circle cx="110" cy="14" r="2.5" className="orbit-dot" style={{ fill: 'var(--accent)' }} />
      <circle cx="110" cy="14" r="1.4" fill="#e0f2fe" />
      <circle cx="14" cy="48" r="1.6" fill="#34d399" opacity="0.9" />
      <circle cx="206" cy="48" r="1.6" fill="#a78bfa" opacity="0.9" />

      {[10, 18, 26, 34, 42].map((x) => (
        <circle key={x} cx={x} cy="48" r="1" fill="rgba(148,163,184,0.4)" />
      ))}
      {[178, 186, 194, 202, 210].map((x) => (
        <circle key={x} cx={x} cy="48" r="1" fill="rgba(148,163,184,0.4)" />
      ))}
    </svg>
  )
}