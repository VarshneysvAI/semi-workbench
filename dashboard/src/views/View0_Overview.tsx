import { motion } from 'framer-motion'
import { Activity, CheckCircle2, Database, Gauge, TrendingDown, type LucideIcon } from 'lucide-react'
import { PIPELINE, SKU_ROWS, type SkStatus } from '../data/mock'
import { cn } from '../lib/cn'
import { Panel, ProgressRing, SectionTitle, Sparkline, StatusPill, type Tone } from '../components/ui'

const STATUS_UI: Record<SkStatus, { label: string; tone: Tone; pulse?: boolean }> = {
  accepted: { label: 'Accepted', tone: 'emerald' },
  conflict: { label: 'Conflict', tone: 'rose' },
  refused: { label: 'Refused — low evidence', tone: 'amber', pulse: true },
  review: { label: 'Review', tone: 'violet' },
}

const STATS: Array<{ icon: LucideIcon; label: string; value: string; sub: string; data: number[] }> = [
  { icon: Database, label: 'Field extractions', value: '212.4k', sub: '+12% this week', data: [4, 9, 11, 8, 14, 18, 21, 26] },
  { icon: Activity, label: 'Automation rate', value: '94.7%', sub: 'no human in loop', data: [70, 74, 78, 82, 88, 91, 93, 95] },
  { icon: Gauge, label: 'Weighted accuracy', value: '0.989', sub: 'vs 227 verified rows', data: [88, 90, 92, 91, 94, 96, 97, 99] },
  { icon: TrendingDown, label: 'Cost / SKU', value: '$0.0021', sub: 'mature flywheel target $0.0015', data: [82, 60, 48, 40, 30, 24, 19, 15] },
]

function PipelineStrip() {
  return (
    <Panel className="p-5">
      <div className="mb-5 flex items-center justify-between">
        <SectionTitle>Live pipeline — 18.4k SKUs today</SectionTitle>
        <StatusPill label="running" tone="emerald" pulse />
      </div>
      <div className="flex items-stretch gap-2">
        {PIPELINE.map((stage, i) => (
          <div key={stage.label} className="flex flex-1 items-center gap-2">
            <div
              className={cn(
                'relative flex-1 rounded-xl border px-3 py-3',
                stage.active
                  ? 'border-emerald-400/30 bg-emerald-400/[0.06]'
                  : stage.done
                    ? 'border-white/[0.08] bg-white/[0.02]'
                    : 'border-white/[0.05] bg-white/[0.01] opacity-70',
              )}
            >
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-semibold text-slate-100">{stage.label}</span>
                <span className="font-mono text-[11px] text-slate-500">{stage.count}</span>
              </div>
              <div className="mt-1 text-[10px] leading-tight text-slate-500">{stage.desc}</div>
              {stage.active && (
                <span className="mt-2 inline-flex items-center gap-1 text-[10px] font-medium text-emerald-300">
                  <span className="relative flex h-1.5 w-1.5">
                    <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-400" />
                    <span className="relative h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  </span>
                  processing now
                </span>
              )}
            </div>
            {i < PIPELINE.length - 1 && (
              <svg width="18" height="12" viewBox="0 0 18 12" className="shrink-0 text-slate-600">
                <path d="M0 6h14m0 0l-3.5-4M14 6l-3.5 4" stroke="currentColor" strokeWidth="1.2" fill="none" />
              </svg>
            )}
          </div>
        ))}
      </div>
    </Panel>
  )
}

export default function OverviewView() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
          <div className="max-w-2xl">
            <div className="mb-3 flex items-center gap-2">
              <StatusPill label="SEMI v1.0" tone="violet" />
              <StatusPill label="UniHack 2026" tone="slate" />
            </div>
            <h1 className="text-[34px] font-extrabold leading-[1.08] tracking-tight text-white">
              Self-Evolving{' '}
              <span className="bg-gradient-to-r from-emerald-300 via-teal-300 to-violet-400 bg-clip-text text-transparent">
                Manufacturer Intelligence
              </span>
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-400">
              From a bare <span className="font-mono text-slate-200">(manufacturer, part_number)</span> pair, SEMI
              discovers sources, extracts multi-format evidence, adversarially self-audits every value, and emits either a
              certified value — or refuses with <span className="font-mono text-amber-300">INSUFFICIENT_EVIDENCE</span>.
            </p>
          </div>
          <div className="flex items-end gap-6">
            <div className="text-right">
              <SectionTitle>Certification rate</SectionTitle>
              <div className="mt-2 flex items-center gap-4">
                <div>
                  <div className="text-3xl font-extrabold tracking-tight text-white">97.8<span className="text-lg text-slate-400">%</span></div>
                  <div className="text-[11px] text-slate-500">of values pass all 5 audits</div>
                </div>
                <ProgressRing value={0.978} />
              </div>
            </div>
            <div className="text-right">
              <SectionTitle>Refusal honesty</SectionTitle>
              <div className="mt-2 flex items-center gap-4">
                <div>
                  <div className="text-3xl font-extrabold tracking-tight text-amber-300">2.2<span className="text-lg text-slate-400">%</span></div>
                  <div className="text-[11px] text-slate-500">answered "don't know"</div>
                </div>
                <ProgressRing value={0.022} tone="#fbbf24" />
              </div>
            </div>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {STATS.map((s) => (
            <Panel key={s.label} className="p-4">
              <div className="flex items-center justify-between">
                <s.icon className="h-4 w-4 text-slate-500" strokeWidth={1.8} />
                <span className="text-[10px] font-medium text-emerald-400/80">{s.sub}</span>
              </div>
              <div className="mt-3 font-mono font-num text-[22px] font-bold tracking-tight text-white">{s.value}</div>
              <div className="text-[12px] text-slate-500">{s.label}</div>
              <Sparkline data={s.data} className="mt-3" />
            </Panel>
          ))}
        </div>

        <PipelineStrip />

        <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Panel className="lg:col-span-2 p-5">
            <div className="mb-4 flex items-center justify-between">
              <SectionTitle>Live SKU ledger</SectionTitle>
              <StatusPill label="10 of 10 shown" tone="slate" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[12px]">
                <thead>
                  <tr className="border-b border-white/[0.06] text-[10px] uppercase tracking-[0.14em] text-slate-500">
                    <th className="pb-2 pr-3 font-semibold">SKU</th>
                    <th className="pb-2 pr-3 font-semibold">attribute</th>
                    <th className="pb-2 pr-3 font-semibold">value</th>
                    <th className="pb-2 pr-3 text-right font-semibold">conf</th>
                    <th className="pb-2 pr-3 text-right font-semibold">audits</th>
                    <th className="pb-2 text-right font-semibold">status</th>
                  </tr>
                </thead>
                <tbody>
                  {SKU_ROWS.map((row) => {
                    const ui = STATUS_UI[row.status]
                    return (
                      <tr key={row.id} className="group border-b border-white/[0.04] last:border-0">
                        <td className="py-2.5 pr-3">
                          <span className="font-semibold text-slate-200">{row.manufacturer}</span>
                          <span className="ml-1.5 font-mono text-slate-400">{row.partNumber}</span>
                        </td>
                        <td className="py-2.5 pr-3 font-mono text-slate-400">{row.attribute}</td>
                        <td className="py-2.5 pr-3 font-mono text-slate-200">
                          {row.value}
                          {row.unit && <span className="ml-0.5 text-slate-500">{row.unit}</span>}
                        </td>
                        <td className="py-2.5 pr-3 text-right font-mono font-num text-slate-300">{row.confidence.toFixed(2)}</td>
                        <td className="py-2.5 pr-3 text-right">
                          <div className="inline-flex gap-[3px] align-middle">
                            {Array.from({ length: 5 }).map((_, k) => (
                              <span
                                key={k}
                                className={cn('h-1.5 w-1.5 rounded-full', k < row.auditsPass ? 'bg-emerald-400/80' : 'bg-white/[0.08]')}
                              />
                            ))}
                          </div>
                        </td>
                        <td className="py-2.5 text-right">
                          <StatusPill label={ui.label} tone={ui.tone} pulse={ui.pulse} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel className="p-5">
            <div className="mb-4 flex items-center justify-between">
              <SectionTitle>Audit composition</SectionTitle>
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="space-y-4">
              {[
                { label: 'Physical constraints', value: 212, total: 212 },
                { label: 'Cross-source contradiction', value: 205, total: 212 },
                { label: 'Compositional consistency', value: 208, total: 212 },
                { label: 'Adversarial disproof search', value: 174, total: 212 },
                { label: 'Conformal 95% coverage', value: 190, total: 212 },
              ].map((aud) => (
                <div key={aud.label}>
                  <div className="mb-1.5 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">{aud.label}</span>
                    <span className="font-mono font-num text-slate-500">
                      {Math.round((aud.value / aud.total) * 100)}%
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-300"
                      style={{ width: `${(aud.value / aud.total) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-[11px] leading-relaxed text-slate-500">
              Every emitted value carries a <span className="text-emerald-300">formal audit trail</span> + 95% conformal
              interval — a confidence score is never enough.
            </div>
          </Panel>
        </div>
      </motion.div>
    </div>
  )
}