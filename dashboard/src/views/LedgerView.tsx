import { useMemo } from 'react'
import { useSemi } from '../engine/SemiContext'
import { Badge, SectionTitle, StatusDot } from '../components/ui'
import { LiveLedger } from '../components/live'

export default function LedgerView() {
  const { engine, live } = useSemi()

  const ledgerEvents = useMemo(
    () => engine.state.events.filter((e) => e.origin === 'ledger').slice(0, 14),
    [engine.state.events],
  )

  return (
    <div className="mx-auto max-w-[1100px] space-y-5 p-5">
      <div>
        <h1 className="text-[23px] font-semibold tracking-tight text-slate-100">Resolution ledger</h1>
        <p className="mt-1 text-[13.5px] text-slate-400">
          the flywheel — every human decision is a trainable precedent
        </p>
      </div>

      {live === 'live' ? (
        <LiveLedger />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <LedgerStat label="ledger rows" value={engine.state.ledger.length} />
            <LedgerStat label="outcome flips" value={engine.state.changedOutcomes} tone="emerald" />
            <LedgerStat label="retrains" value={engine.state.retrains} />
            <LedgerStat label="resolved conflicts" value={engine.state.conflictsResolved} tone="violet" />
          </div>

          <div className="panel p-4">
            <SectionTitle
              right={
                <span className="mono flex items-center gap-2 text-[10px] text-slate-500">
                  <StatusDot tone="live" /> streaming
                </span>
              }
            >
              Ledger rows
            </SectionTitle>
            <div className="mono overflow-x-auto">
              <table className="w-full border-collapse text-left text-[12px]">
                <thead>
                  <tr className="border-b border-white/[0.09] text-[11.5px] uppercase tracking-wider text-slate-400">
                    <th className="py-2 pr-3 font-medium">t</th>
                    <th className="py-2 pr-3 font-medium">sku</th>
                    <th className="py-2 pr-3 font-medium">signature</th>
                    <th className="py-2 pr-3 font-medium">resolution</th>
                    <th className="py-2 pr-3 font-medium">outcome changed</th>
                    <th className="py-2 font-medium">source_url</th>
                  </tr>
                </thead>
                <tbody>
                  {engine.state.ledger.length ? (
                    engine.state.ledger.map((r, i) => (
                      <tr key={`${r.at}-${i}`} className="border-b border-white/[0.06] text-slate-300">
                        <td className="py-2 pr-3 font-num text-slate-500">{i + 1}</td>
                        <td className="py-2 pr-3 text-slate-50">{r.sku}</td>
                        <td className="py-2 pr-3 text-amber-200/90">{r.sig}</td>
                        <td className="py-2 pr-3 text-emerald-300">{r.resolution}</td>
                        <td className="py-2 pr-3">
                          {r.changedOutcome ? <Badge tone="amber">TRUE</Badge> : <Badge tone="slate">false</Badge>}
                        </td>
                        <td className="mono max-w-[280px] truncate py-2 text-slate-500">{r.sourceUrl}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="py-8 text-center text-[12px] text-slate-500">
                        ledger empty — wait for the first conflict
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel p-4">
            <SectionTitle right={null}>Recent ledger events</SectionTitle>
            <div className="space-y-1">
              {ledgerEvents.length ? (
                ledgerEvents.map((e) => (
                  <div key={e.id} className="mono flex items-center gap-2 text-[11.5px] text-slate-500">
                    <StatusDot tone="ok" />
                    <span className="min-w-0 flex-1 truncate">{e.label}</span>
                    <span className="text-slate-600">{e.sku}</span>
                  </div>
                ))
              ) : (
                <div className="text-[11px] text-slate-600">no ledger events yet</div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function LedgerStat({
  label,
  value,
  tone = 'slate',
}: {
  label: string
  value: number
  tone?: 'slate' | 'emerald' | 'violet'
}) {
  const tones = { slate: 'text-slate-200', emerald: 'text-emerald-300', violet: 'text-violet-300' }
  return (
    <div className="panel px-4 py-3">
      <div className="label-caps">{label}</div>
      <div className={`mono mt-1 font-num text-[20px] font-semibold ${tones[tone]}`}>{value}</div>
    </div>
  )
}