import { useCallback, useEffect, useState } from 'react'
import { Badge, SectionTitle, StatusDot } from './ui'

const POLL_MS = 3000

export interface LiveConflict {
  sku: string
  manufacturer: string
  attribute: string
  status: string
  a: { value: string; source_url: string; authority: number }
  b: { value: string; source_url: string; authority: number }
}

export interface LiveLedgerRow {
  sku: string
  manufacturer: string
  signature: string
  resolution: string
  note: string
  source_url: string
  changed_outcome: boolean
  at: number
}

export interface LiveGraph {
  sku: string
  manufacturer: string
  sources: number
  candidates: number
}

export interface LiveVerdict {
  attribute: string
  status: string
  value: string
  confidence: number
  interval: [number, number] | null
  calibrated: boolean
  reason: string
  findings: string[]
}

export interface LiveAudit {
  sku: string
  manufacturer: string
  calibrated: boolean
  findings: Array<{ attribute: string; kind: string; rule: string; detail: string; severity: string }>
  contradictions: Array<{ attribute: string; detail: string }>
  verdicts: LiveVerdict[]
  conflict: LiveConflict | null
}

function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null)
  const [failed, setFailed] = useState(false)
  const [tick, setTick] = useState(0)

  const refetch = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    if (!path) return
    let cancelled = false
    const load = () =>
      fetch(path)
        .then((r) => (r.ok ? r.json() : null))
        .then((j) => {
          if (!cancelled) {
            setData(j as T)
            setFailed(false)
          }
        })
        .catch(() => {
          if (!cancelled) setFailed(true)
        })
    load()
    const iv = setInterval(load, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(iv)
    }
  }, [path, tick])

  return { data, failed, refetch }
}

function SideTile({
  letter,
  value,
  sourceUrl,
  authority,
  accent,
  busy,
  onPick,
}: {
  letter: 'A' | 'B'
  value: string
  sourceUrl: string
  authority: number
  accent: boolean
  busy: boolean
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
      <div className="mono mt-1 truncate text-[10.5px] text-slate-600">{sourceUrl}</div>
      <button onClick={onPick} disabled={busy} className="btn mt-2.5 w-full justify-center">
        {busy ? 'resolving…' : accent ? 'Adopt B' : 'Adopt A'}
      </button>
    </div>
  )
}

export function LiveConflicts() {
  const { data, refetch } = useApi<{ count: number; conflicts: LiveConflict[] }>('/api/conflicts')
  const [busySku, setBusySku] = useState<string | null>(null)

  const resolve = async (c: LiveConflict, choice: 'A' | 'B') => {
    setBusySku(c.sku)
    try {
      await fetch('/api/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sku: c.sku,
          human_resolution: choice === 'A' ? c.a.value : c.b.value,
          reason_tags: [choice === 'A' ? 'spec_sheet_authority' : 'admin override'],
        }),
      })
    } finally {
      setBusySku(null)
      refetch()
    }
  }

  const conflicts = data?.conflicts ?? []
  const resolved = (data?.count ?? 0) - conflicts.length

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Badge tone="amber">
          <StatusDot tone="warn" /> {conflicts.length} open
        </Badge>
        <Badge tone="emerald">{Math.max(0, resolved)} resolved</Badge>
        <span className="mono text-[11px] text-slate-600">live backend queue · polls {POLL_MS / 1000}s</span>
      </div>

      {conflicts.length ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {conflicts.map((c) => (
            <div key={c.sku} className="panel p-4">
              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="mono text-[14.5px] font-semibold text-slate-50">{c.sku}</span>
                  <Badge tone="cyan">{c.manufacturer}</Badge>
                </div>
                <Badge tone="amber">{c.attribute}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <SideTile
                  letter="A"
                  value={c.a.value}
                  sourceUrl={c.a.source_url}
                  authority={c.a.authority}
                  accent={false}
                  busy={busySku === c.sku}
                  onPick={() => resolve(c, 'A')}
                />
                <SideTile
                  letter="B"
                  value={c.b.value}
                  sourceUrl={c.b.source_url}
                  authority={c.b.authority}
                  accent
                  busy={busySku === c.sku}
                  onPick={() => resolve(c, 'B')}
                />
              </div>
              <div className="mono mt-3 flex items-center justify-between text-[10.5px] text-slate-600">
                <span>resolution writes a ledger row + broadcasts</span>
                <span className="text-slate-500">pick a side to close</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="panel flex flex-col items-center py-14 text-center">
          <StatusDot tone="ok" />
          <p className="mt-3 text-[14px] text-slate-300">Queue clear</p>
          <p className="mono mt-1 text-[11.5px] text-slate-500">
            resolved conflicts land in the ledger — the flywheel feeds on them
          </p>
        </div>
      )}
    </div>
  )
}

export function LiveLedger() {
  const { data } = useApi<{ count: number; rows: LiveLedgerRow[] }>('/api/ledger')
  const rows = data?.rows ?? []
  const flips = rows.filter((r) => r.changed_outcome).length

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <div className="panel px-4 py-3">
          <div className="label-caps">ledger rows</div>
          <div className="mono mt-1 font-num text-[20px] font-semibold text-slate-200">{rows.length}</div>
        </div>
        <div className="panel px-4 py-3">
          <div className="label-caps">outcome flips</div>
          <div className="mono mt-1 font-num text-[20px] font-semibold text-emerald-300">{flips}</div>
        </div>
        <div className="panel px-4 py-3">
          <div className="label-caps">signatures</div>
          <div className="mono mt-1 font-num text-[20px] font-semibold text-slate-200">
            {new Set(rows.map((r) => r.signature)).size}
          </div>
        </div>
        <div className="panel px-4 py-3">
          <div className="label-caps">flywheel feed</div>
          <div className="mono mt-1 font-num text-[20px] font-semibold text-violet-300">
            {rows.length >= 30 ? 'calibrated' : `${Math.max(0, 30 - rows.length)} to cal`}
          </div>
        </div>
      </div>

      <div className="panel p-4">
        <SectionTitle
          right={
            <span className="mono flex items-center gap-2 text-[10px] text-slate-500">
              <StatusDot tone="live" /> live rows
            </span>
          }
        >
          Ledger rows
        </SectionTitle>
        <div className="mono overflow-x-auto">
          <table className="w-full border-collapse text-left text-[12px]">
            <thead>
              <tr className="border-b border-white/[0.09] text-[11.5px] uppercase tracking-wider text-slate-400">
                <th className="py-2 pr-3 font-medium">sku</th>
                <th className="py-2 pr-3 font-medium">signature</th>
                <th className="py-2 pr-3 font-medium">resolution</th>
                <th className="py-2 pr-3 font-medium">reason</th>
                <th className="py-2 pr-3 font-medium">outcome changed</th>
                <th className="py-2 font-medium">source_url</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((r) => (
                  <tr key={`${r.at}-${r.sku}`} className="border-b border-white/[0.06] text-slate-300">
                    <td className="py-2 pr-3 text-slate-50">{r.sku}</td>
                    <td className="py-2 pr-3 text-amber-200/90">{r.signature}</td>
                    <td className="py-2 pr-3 text-emerald-300">{r.resolution}</td>
                    <td className="mono max-w-[220px] truncate py-2 pr-3 text-slate-500">{r.note}</td>
                    <td className="py-2 pr-3">
                      {r.changed_outcome ? <Badge tone="amber">TRUE</Badge> : <Badge tone="slate">false</Badge>}
                    </td>
                    <td className="mono max-w-[240px] truncate py-2 text-slate-500">{r.source_url}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-[12px] text-slate-500">
                    ledger empty — resolve a conflict to write the first row
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export function LiveAudit() {
  const { data: graphs } = useApi<{ count: number; graphs: LiveGraph[] }>('/api/graphs')
  const [sku, setSku] = useState<string | null>(null)

  const graphsList = graphs?.graphs ?? []
  const activeSku = sku ?? graphsList[0]?.sku ?? null
  const { data } = useApi<LiveAudit>(activeSku ? `/api/audit/${activeSku}` : null)

  const report = data
  const verdicts = report?.verdicts ?? []
  const acc = verdicts.filter((v) => v.status === 'ACCEPT').length
  const ref = verdicts.filter((v) => v.status.startsWith('REFUSE')).length

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="label-caps">sku</label>
          <select
            value={activeSku ?? ''}
            onChange={(e) => setSku(e.target.value || null)}
            className="mono rounded-md border border-white/[0.12] bg-black/30 px-2 py-1 text-[12px] text-slate-200"
          >
            {graphsList.map((g) => (
              <option key={g.sku} value={g.sku}>
                {g.sku}
              </option>
            ))}
          </select>
        </div>
        <Badge tone={report?.calibrated ? 'emerald' : 'slate'}>
          {report?.calibrated ? 'split-conformal CI active' : 'uncalibrated (needs ≥30 ledger rows)'}
        </Badge>
        <Badge tone="emerald">{acc} accept</Badge>
        <Badge tone={ref ? 'rose' : 'slate'}>{ref} refuse</Badge>
        <Badge tone="slate">{report?.contradictions.length ?? 0} contradictions</Badge>
      </div>

      <div className="panel p-4">
        <SectionTitle right={<span className="mono text-[11px] text-slate-600">refusal gate is the default</span>}>
          Verdicts — {report?.sku ?? '…'}
        </SectionTitle>
        <div className="grid gap-3 lg:grid-cols-2">
          {verdicts.length ? (
            verdicts.map((v) => (
              <div
                key={v.attribute}
                className={`rounded-lg border p-3 ${
                  v.status === 'ACCEPT'
                    ? 'border-emerald-400/20 bg-emerald-400/[0.05]'
                    : 'border-rose-400/20 bg-rose-400/[0.05]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[12.5px] font-medium text-slate-200">{v.attribute}</span>
                  <span className="mono text-[11px]">
                    {v.status === 'ACCEPT' ? (
                      <span className="text-emerald-400">ACCEPT</span>
                    ) : (
                      <span className="text-rose-400">{v.status}</span>
                    )}
                  </span>
                </div>
                <div className="mono mt-1 text-[15px] font-semibold text-slate-100">
                  {v.value || <span className="text-slate-600">no value ships — cell stays empty</span>}
                </div>
                <div className="mono mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10.5px] text-slate-500">
                  <span>conf {v.confidence.toFixed(3)}</span>
                  {v.interval && v.status === 'ACCEPT' ? (
                    <span className={v.calibrated ? 'text-cyan-300' : 'text-slate-500'}>
                      CI [{v.interval[0].toFixed(2)}, {v.interval[1].toFixed(2)}]
                      {v.calibrated ? '· calibrated' : '· uncalibrated'}
                    </span>
                  ) : null}
                  <span className="min-w-0 flex-1 truncate">{v.reason}</span>
                </div>
                {v.findings.length ? (
                  <div className="mono mt-1.5 space-y-0.5">
                    {v.findings.map((f) => (
                      <div key={f} className="truncate text-[10.5px] text-rose-400/80">
                        ⚠ {f}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ))
          ) : (
            <div className="py-8 text-center text-[13px] text-slate-600">
              {graphsList.length ? 'audit returned no verdicts yet' : 'no state graphs registered — ingest a workbook first'}
            </div>
          )}
        </div>
      </div>

      {report?.conflict ? (
        <div className="panel border-amber-400/25 p-4">
          <SectionTitle right={<Badge tone="amber">{report.conflict.attribute}</Badge>}>
            <span className="flex items-center gap-2">
              Open conflict <StatusDot tone="warn" />
            </span>
          </SectionTitle>
          <div className="mono flex flex-wrap items-center justify-between gap-3 text-[12px] text-slate-300">
            <span>
              A · <span className="text-slate-100">{report.conflict.a.value}</span>
              <span className="ml-2 text-slate-600">{report.conflict.a.source_url}</span>
            </span>
            <span className="text-slate-600">vs</span>
            <span>
              B · <span className="text-slate-100">{report.conflict.b.value}</span>
              <span className="ml-2 text-slate-600">{report.conflict.b.source_url}</span>
            </span>
            <span className="text-slate-500">resolve in the review queue</span>
          </div>
        </div>
      ) : null}
    </div>
  )
}

export function LiveDiscovery() {
  const { data, refetch } = useApi<{ count: number; graphs: LiveGraph[] }>('/api/graphs')
  const [busySku, setBusySku] = useState<string | null>(null)

  const run = async (sku: string) => {
    setBusySku(sku)
    try {
      await fetch(`/api/discover/${sku}?top_k=5&fetch=false&extract=false`)
    } finally {
      setBusySku(null)
      refetch()
    }
  }

  const graphs = data?.graphs ?? []
  const sources = graphs.reduce((a, g) => a + g.sources, 0)
  const candidates = graphs.reduce((a, g) => a + g.candidates, 0)

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Badge tone="cyan">{graphs.length} graphs</Badge>
        <Badge tone="slate">{sources} sources</Badge>
        <Badge tone="violet">{candidates} extracted candidates</Badge>
        <span className="mono text-[11px] text-slate-600">
          run discovery = live web search → validation → ranking (query-only mode)
        </span>
      </div>

      <div className="panel p-4">
        <SectionTitle right={null}>Registered state graphs</SectionTitle>
        <div className="mono overflow-x-auto">
          <table className="w-full border-collapse text-left text-[12px]">
            <thead>
              <tr className="border-b border-white/[0.09] text-[11.5px] uppercase tracking-wider text-slate-400">
                <th className="py-2 pr-3 font-medium">sku</th>
                <th className="py-2 pr-3 font-medium">manufacturer</th>
                <th className="py-2 pr-3 font-medium">sources</th>
                <th className="py-2 pr-3 font-medium">candidates</th>
                <th className="py-2 font-medium">action</th>
              </tr>
            </thead>
            <tbody>
              {graphs.length ? (
                graphs.map((g) => (
                  <tr key={g.sku} className="border-b border-white/[0.06] text-slate-300">
                    <td className="py-2 pr-3 text-slate-50">{g.sku}</td>
                    <td className="py-2 pr-3">{g.manufacturer}</td>
                    <td className="py-2 pr-3 font-num">{g.sources}</td>
                    <td className="py-2 pr-3 font-num">{g.candidates}</td>
                    <td className="py-2">
                      <button
                        onClick={() => run(g.sku)}
                        disabled={busySku === g.sku}
                        className="btn px-2.5 py-1 text-[11px]"
                      >
                        {busySku === g.sku ? 'searching…' : 'Run discovery'}
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-[12px] text-slate-500">
                    no graphs — POST /api/ingest with an Unilog .xlsx to register state graphs
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}