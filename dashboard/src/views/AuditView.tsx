import { useMemo } from 'react'
import { useSemi } from '../engine/SemiContext'
import { Badge, SectionTitle } from '../components/ui'

export default function AuditView() {
  const { engine } = useSemi()

  const auditEvents = useMemo(
    () => engine.state.events.filter((e: any) => e.origin === 'audit').slice(0, 40),
    [engine.state.events],
  )

  const active = engine.state.rows.find((r: any) => r.stage === 'audit')
  const totalChecks = engine.state.rows.reduce((a: number, r: any) => a + (r.audits?.length ?? 0), 0)
  const passChecks = engine.state.rows.reduce(
    (a: number, r: any) => a + (r.audits ?? []).filter((x: any) => x.state === 'pass').length, 0,
  )
  const failChecks = engine.state.rows.reduce(
    (a: number, r: any) => a + (r.audits ?? []).filter((x: any) => x.state === 'fail').length, 0,
  )
  const failRate = totalChecks ? Math.round((failChecks / totalChecks) * 100) : 0

  return (
    <div className="mx-auto max-w-[1200px] space-y-5 p-5">
      <div>
        <h1 className="text-[23px] font-semibold tracking-tight text-slate-100">Adversarial audit engine</h1>
        <p className="mt-1 text-[13.5px] text-slate-500">
          5 self-checks per value · nothing ships without a PASS row
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <MiniStat label="checks executed" value={totalChecks} tone="slate" />
        <MiniStat label="passed" value={passChecks} tone="emerald" />
        <MiniStat label="failed" value={failChecks} tone={failChecks ? 'rose' : 'slate'} />
        <MiniStat label="fail rate" value={`${failRate}%`} tone={failRate > 12 ? 'amber' : 'slate'} />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="panel p-4">
          <SectionTitle right={active ? <Badge tone="cyan">{active.pn}</Badge> : null}>
            {active ? `Auditing ${active.pn}` : 'No audit in flight'}
          </SectionTitle>
          {active ? (
            <div className="space-y-1.5">
              {(active.audits ?? []).map((a: any, i: number) => (
                <div
                  key={a.label}
                  className={`flex items-center justify-between rounded-md border px-2.5 py-2 ${
                    a.state === 'pass'
                      ? 'border-emerald-400/20 bg-emerald-400/[0.05]'
                      : a.state === 'fail'
                        ? 'border-rose-400/20 bg-rose-400/[0.05]'
                        : 'border-white/[0.1] bg-white/[0.03]'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="text-[12.5px] text-slate-200">
                      <span className="mono mr-2 text-[11px] text-slate-600">{i + 1}</span>
                      {a.label}
                    </div>
                    {a.note ? <div className="mono mt-0.5 truncate text-[10.5px] text-slate-600">{a.note}</div> : null}
                  </div>
                  <span className="mono shrink-0 text-[11px]">
                    {a.state === 'run' ? (
                      <span className="caret-live text-accent-strong">running…</span>
                    ) : a.state === 'pass' ? (
                      <span className="text-emerald-400">PASS</span>
                    ) : (
                      <span className="text-rose-400">FAIL</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-[13px] text-slate-600">
              audits resume when a row reaches the audit stage
            </div>
          )}
        </div>

        <div className="panel p-4">
          <SectionTitle right={<span className="mono text-[11px] text-slate-600">{auditEvents.length} recent</span>}>
            Audit transcript
          </SectionTitle>
          <div className="max-h-[420px] space-y-1 overflow-y-auto">
            {auditEvents.length ? (
              auditEvents.map((e: any) => (
                <div key={e.id} className="mono flex gap-2 text-[11px] leading-relaxed text-slate-500">
                  <span className="shrink-0 text-amber-400">[audit]</span>
                  <span className="min-w-0 flex-1 truncate">{e.label}</span>
                  <span className="max-w-[240px] truncate text-slate-600">{e.detail}</span>
                  <Badge tone="slate">{e.sku}</Badge>
                </div>
              ))
            ) : (
              <div className="text-[11px] text-slate-600">waiting for audit events…</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function MiniStat({ label, value, tone }: { label: string; value: string | number; tone: 'slate' | 'emerald' | 'rose' | 'amber' }) {
  const tones = {
    slate: 'text-slate-200',
    emerald: 'text-emerald-300',
    rose: 'text-rose-300',
    amber: 'text-amber-300',
  }
  return (
    <div className="panel px-4 py-3">
      <div className="label-caps">{label}</div>
      <div className={`mono mt-1 font-num text-[20px] font-semibold ${tones[tone]}`}>{value}</div>
    </div>
  )
}