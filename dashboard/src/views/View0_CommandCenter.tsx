import { motion } from 'framer-motion'
import { Activity, AlertTriangle, CheckCircle2, Database, Gauge, ShieldCheck, TrendingDown, Zap } from 'lucide-react'
import IntelligenceGraph from '../components/IntelligenceGraph'
import { BarList, CountUp, GlassCard, PanelHeader, RingGauge, SectionTitle, Sparkline, StatusPill } from '../components/ui'
import { SKU_ROWS, type SkStatus } from '../data/mock'
import { cn } from '../lib/cn'

const STATUS_UI: Record<SkStatus, { label: string; tone: 'emerald' | 'violet' | 'amber' | 'rose'; pulse?: boolean }> = {
  accepted: { label: 'Accepted', tone: 'emerald' },
  conflict: { label: 'Conflict', tone: 'rose', pulse: true },
  refused: { label: 'Refused', tone: 'amber', pulse: true },
  review: { label: 'Review', tone: 'violet' },
}

const STATS: Array<{ icon: typeof Database; label: string; value: number; decimals?: number; suffix: string; sub: string; data: number[]; color?: string }> = [
  { icon: Database, label: 'Field extractions', value: 212.4, suffix: 'k', decimals: 1, sub: '+12% this week', data: [4, 9, 11, 8, 14, 18, 21, 26, 31, 38] },
  { icon: Activity, label: 'Automation rate', value: 94.7, suffix: '%', decimals: 1, sub: 'no human in the loop', data: [70, 74, 78, 82, 88, 91, 93, 94.2, 94.5, 94.7] },
  { icon: Gauge, label: 'Weighted accuracy', value: 0.989, suffix: '', decimals: 3, sub: 'vs 227 verified rows', data: [88, 90, 92, 91, 94, 96, 97, 98.2, 98.7, 98.9], color: '#a78bfa' },
  { icon: TrendingDown, label: 'Cost / SKU', value: 0.0021, suffix: '', decimals: 4, sub: 'mature target $0.0015', data: [82, 60, 48, 40, 30, 24, 19, 15, 12, 10], color: '#fbbf24' },
]

export default function CommandCenterView() {
  return (
    <div className="mx-auto max-w-[1280px] px-6 py-8">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
        <div className="mb-8 flex flex-wrap items-end justify-between gap-6">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <StatusPill label="SEMI v1.0" tone="cyan" />
              <StatusPill label="UniHack 2026" tone="violet" />
              <StatusPill label="local · Apache 2.0" tone="slate" />
            </div>
            <h1 className="text-[32px] font-extrabold leading-[1.08] tracking-tight">
              Self-Evolving{' '}
              <span className="text-gradient">Manufacturer Intelligence</span>
            </h1>
            <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-slate-400">
              From a bare <span className="font-mono text-cyan-300">(manufacturer, part_number)</span> pair, SEMI
              discovers sources, extracts multi-format evidence, adversarially self-checks every value, and emits either a
              certified value — or refuses with <span className="font-mono text-amber-300">INSUFFICIENT_EVIDENCE</span>.
            </p>
          </div>
          <div className="flex items-end gap-5">
            <div className="text-right">
              <SectionTitle>Certification rate</SectionTitle>
              <div className="mt-2 flex items-center gap-4">
                <RingGauge value={0.978} color="#34d399" label="certified" />
              </div>
            </div>
            <div className="text-right">
              <SectionTitle>Refusal honesty</SectionTitle>
              <div className="mt-2 flex items-center gap-4">
                <RingGauge value={0.022} color="#fbbf24" label="refused" />
              </div>
            </div>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {STATS.map((s, i) => (
            <GlassCard key={s.label} delay={i * 0.06}>
              <div className="p-4">
                <div className="flex items-center justify-between">
                  <s.icon className="h-4 w-4 text-slate-500" strokeWidth={1.8} />
                  <span className="text-[10px] font-semibold text-emerald-400/80">{s.sub}</span>
                </div>
                <div className="mt-3 font-mono text-[26px] font-bold tracking-tight text-white">
                  <CountUp target={s.value} decimals={s.decimals ?? 0} suffix={s.suffix} />
                </div>
                <div className="text-[11px] text-slate-500">{s.label}</div>
                <Sparkline data={s.data} className="mt-3" color={s.color} />
              </div>
            </GlassCard>
          ))}
        </div>

        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <GlassCard className="lg:col-span-2" glow delay={0.25}>
            <PanelHeader
              title="Live Intelligence Graph"
              subtitle="NIBCO BV-3001 — sources → extraction → 5 audits → certification"
              right={<StatusPill label="processing now" tone="cyan" pulse />}
            />
            <div className="h-[320px]">
              <IntelligenceGraph />
            </div>
          </GlassCard>

          <GlassCard delay={0.3}>
            <PanelHeader
              title="Audit Composition"
              subtitle="values passing each gate"
              right={<ShieldCheck className="h-4 w-4 text-emerald-400" />}
            />
            <div className="p-5">
              <BarList
                items={[
                  { label: 'Physical constraints', value: 212, tone: 'emerald' },
                  { label: 'Cross-source consensus', value: 205, tone: 'teal' },
                  { label: 'Compositional consistency', value: 208, tone: 'cyan' },
                  { label: 'Adversarial disproof search', value: 174, tone: 'violet' },
                  { label: 'Conformal 95% coverage', value: 190, tone: 'amber' },
                ]}
              />
              <div className="mt-5 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-[11px] leading-relaxed text-slate-500">
                Every emitted value carries a <span className="text-emerald-300">formal audit trail</span> + 95% conformal
                interval — a confidence score is never enough.
              </div>
            </div>
          </GlassCard>
        </div>

        <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <GlassCard className="lg:col-span-2" delay={0.35}>
            <PanelHeader title="Live SKU Ledger" subtitle="18.4k SKUs today" right={<StatusPill label="10 of 10 shown" tone="slate" />} />
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[12px]">
                <thead>
                  <tr className="border-b border-white/[0.06] text-[10px] uppercase tracking-[0.16em] text-slate-500">
                    <th className="px-4 pb-2.5 font-semibold">SKU</th>
                    <th className="pb-2.5 font-semibold">Attribute</th>
                    <th className="pb-2.5 font-semibold">Value</th>
                    <th className="pb-2.5 text-right font-semibold">Conf</th>
                    <th className="pb-2.5 text-center font-semibold">Audits</th>
                    <th className="pr-4 pb-2.5 text-right font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {SKU_ROWS.map((row) => {
                    const ui = STATUS_UI[row.status]
                    return (
                      <tr key={row.id} className="group border-b border-white/[0.04] transition-colors hover:bg-white/[0.015]">
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-200">{row.manufacturer}</div>
                          <div className="font-mono text-[11px] text-slate-500">{row.partNumber}</div>
                        </td>
                        <td className="py-3 font-mono text-[11px] text-slate-400">{row.attribute}</td>
                        <td className="py-3 font-mono text-[13px] font-semibold text-white">
                          {row.value}
                          {row.unit && <span className="ml-0.5 text-[11px] font-medium text-slate-500">{row.unit}</span>}
                        </td>
                        <td className="py-3 text-right font-mono font-num text-slate-300">{row.confidence.toFixed(2)}</td>
                        <td className="py-3">
                          <div className="flex justify-center gap-[3px]">
                            {Array.from({ length: 5 }).map((_, k) => (
                              <span
                                key={k}
                                className={cn(
                                  'h-[5px] w-[5px] rounded-full',
                                  k < row.auditsPass ? 'bg-emerald-400 shadow-[0_0_6px_-1px_#34d399]' : 'bg-white/[0.08]',
                                )}
                              />
                            ))}
                          </div>
                        </td>
                        <td className="py-3 pr-4 text-right">
                          <StatusPill label={ui.label} tone={ui.tone} pulse={ui.pulse} />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </GlassCard>

          <GlassCard delay={0.4}>
            <PanelHeader title="Pipeline Stages" subtitle="5-layer architecture" right={<Zap className="h-4 w-4 text-amber-400" />} />
            <div className="p-5">
              <div className="space-y-3">
                {[
                  { n: 'Discovery', c: 'bg-cyan-400', active: true },
                  { n: 'Extraction', c: 'bg-violet-400', active: true },
                  { n: 'Adversarial Audit', c: 'bg-amber-400', active: false },
                  { n: 'Consensus', c: 'bg-teal-400', active: false },
                  { n: 'Schema Output', c: 'bg-emerald-400', active: false },
                ].map((s) => (
                  <div key={s.n} className="flex items-center gap-3">
                    <span className={cn('h-2.5 w-2.5 rounded-full', s.c, s.active && 'shadow-glow')} />
                    <span className={cn('text-[12px]', s.active ? 'font-semibold text-white' : 'text-slate-400')}>{s.n}</span>
                    {s.active && <StatusPill label="active" tone="cyan" pulse className="ml-auto" />}
                  </div>
                ))}
              </div>
              <div className="mt-5 grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-center">
                  <div className="font-mono text-lg font-bold text-cyan-300">42</div>
                  <div className="text-[9px] uppercase tracking-wider text-slate-500">sources found</div>
                </div>
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-center">
                  <div className="font-mono text-lg font-bold text-violet-300">186</div>
                  <div className="text-[9px] uppercase tracking-wider text-slate-500">extractions</div>
                </div>
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-center">
                  <div className="font-mono text-lg font-bold text-amber-300">418</div>
                  <div className="text-[9px] uppercase tracking-wider text-slate-500">audit checks</div>
                </div>
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 text-center">
                  <div className="font-mono text-lg font-bold text-emerald-300">31</div>
                  <div className="text-[9px] uppercase tracking-wider text-slate-500">certified</div>
                </div>
              </div>
            </div>
          </GlassCard>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <GlassCard delay={0.45}>
            <PanelHeader title="Conflict Alerts" subtitle="requiring resolution" right={<AlertTriangle className="h-4 w-4 text-rose-400" />} />
            <div className="divide-y divide-white/[0.05] p-4">
              {SKU_ROWS.filter((r) => r.status === 'conflict').map((row) => (
                <div key={row.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                  <StatusPill label={row.partNumber} tone="rose" />
                  <div className="min-w-0 flex-1">
                    <div className="text-[12px] text-slate-200">{row.attribute}</div>
                    <div className="text-[11px] text-slate-500">{row.value} · {row.sources} sources disagree</div>
                  </div>
                  <span className="font-mono text-[11px] text-rose-300">{row.confidence.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </GlassCard>
          <GlassCard delay={0.5}>
            <PanelHeader title="Recent Certifications" subtitle="just verified" right={<CheckCircle2 className="h-4 w-4 text-emerald-400" />} />
            <div className="divide-y divide-white/[0.05] p-4">
              {SKU_ROWS.filter((r) => r.status === 'accepted').slice(0, 5).map((row) => (
                <div key={row.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                  <StatusPill label={row.partNumber} tone="emerald" />
                  <div className="min-w-0 flex-1">
                    <div className="text-[12px] text-slate-200">{row.attribute}</div>
                    <div className="font-mono text-[11px] text-slate-500">{row.value} {row.unit}</div>
                  </div>
                  <span className="font-mono text-[11px] text-emerald-300">{row.confidence.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </motion.div>
    </div>
  )
}