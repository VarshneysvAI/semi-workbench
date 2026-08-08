import { useMemo } from 'react'
import { useSemi } from '../engine/SemiContext'
import { Badge, SectionTitle, StatusDot } from '../components/ui'
import { MANUFACTURERS } from '../data/seed'

const AUTHORITY_BARS = [
  { kind: 'spec', label: 'spec', auth: '1.00' },
  { kind: 'manual', label: 'manual', auth: '0.90' },
  { kind: 'page', label: 'page', auth: '0.70' },
  { kind: 'nameplate', label: 'plate', auth: '0.60' },
]

export default function DiscoveryView() {
  const { engine } = useSemi()

  const discoverEvents = useMemo(
    () => engine.state.events.filter((e) => e.origin === 'discover').slice(0, 30),
    [engine.state.events],
  )
  const blockedEvents = useMemo(
    () => engine.state.events.filter((e) => e.origin === 'validator').slice(0, 20),
    [engine.state.events],
  )
  void AUTHORITY_BARS

  return (
    <div className="mx-auto max-w-[1200px] space-y-5 p-5">
      <div>
        <h1 className="text-[23px] font-semibold tracking-tight text-slate-100">Discovery</h1>
        <p className="mt-1 text-[13.5px] text-slate-500">
          Authoritative sources only · spec &gt; manual &gt; page &gt; nameplate
        </p>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="panel p-4">
          <SectionTitle right={null}>Source funnel by manufacturer</SectionTitle>
          <div className="space-y-3">
            {MANUFACTURERS.map((m) => {
              const rows = engine.state.rows.filter((r) => r.mfr === m)
              const kinds = rows.reduce(
                (acc, r) => {
                  r.sources.forEach((s) => (acc[s.kind] = (acc[s.kind] ?? 0) + 1))
                  return acc
                },
                {} as Record<string, number>,
              )
              return (
                <div key={m} className="rounded-lg border border-white/[0.1] bg-white/[0.03] p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="mono text-[12px] font-semibold text-slate-200">{m}</span>
                    <span className="mono font-num text-[12px] text-slate-500">
                      {rows.reduce((a, r) => a + r.sources.length, 0)} sources
                    </span>
                  </div>
                  <div className="flex gap-4">
                    {AUTHORITY_BARS.map((ab) => (
                      <div key={ab.kind} className="flex-1">
                        <div className="mb-1 flex items-center justify-between">
                          <span className="text-[10.5px] text-slate-500">{ab.label} · {ab.auth}</span>
                          <span className="mono font-num text-[9px] text-slate-600">{kinds[ab.kind] ?? 0}</span>
                        </div>
                        <div className="h-1 rounded-full bg-white/[0.05]">
                          <div
                            className="h-1 rounded-full bg-accent-strong"
                            style={{ width: `${Math.min(100, ((kinds[ab.kind] ?? 0) / Math.max(1, rows.length)) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="panel p-4">
          <SectionTitle
            right={<span className="mono text-[12px] text-slate-600">{blockedEvents.length} blocked</span>}
          >
            <span className="flex items-center gap-2">
              Source validator
              <StatusDot tone="danger" />
            </span>
          </SectionTitle>
          <div className="max-h-[300px] space-y-1 overflow-y-auto">
            {blockedEvents.length ? (
              blockedEvents.map((e) => (
                <div key={e.id} className="mono rounded-md border border-rose-400/15 bg-rose-400/[0.05] px-2 py-1.5 text-[12px]">
                  <span className="text-rose-300">✕</span>{' '}
                  <span className="text-slate-400">{e.label}</span>
                  <span className="ml-2 text-slate-600">{e.detail}</span>
                </div>
              ))
            ) : (
              <div className="text-[12px] text-slate-600">no blocked sources yet</div>
            )}
          </div>
        </div>
      </div>

      <div className="panel p-4">
        <SectionTitle
          right={<span className="mono text-[12px] text-slate-600">{discoverEvents.length} live</span>}
        >
          Discovery transcript
        </SectionTitle>
        <div className="max-h-[320px] space-y-1 overflow-y-auto">
          {discoverEvents.length ? (
            discoverEvents.map((e) => (
              <div key={e.id} className="mono flex gap-2 text-[12px] leading-relaxed text-slate-500">
                <span className="shrink-0 text-emerald-400">[discover]</span>
                <span className="min-w-0 flex-1 truncate">{e.label}</span>
                {e.detail ? <span className="hidden max-w-[260px] truncate text-slate-600 xl:inline">{e.detail}</span> : null}
                <Badge tone="cyan" >{e.sku}</Badge>
              </div>
            ))
          ) : (
            <div className="text-[12px] text-slate-600">waiting for discovery events…</div>
          )}
        </div>
      </div>
    </div>
  )
}