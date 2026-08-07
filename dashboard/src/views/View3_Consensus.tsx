import { motion } from 'framer-motion'
import { ArrowRight, GitBranch, Zap } from 'lucide-react'
import { LEDGER_EVENTS } from '../data/mock'
import { GlassCard, PanelHeader, SectionTitle, StatusPill } from '../components/ui'
import { cn } from '../lib/cn'

function WeightBar({ label, source, weight, active }: { label: string; source: string; weight: number; active?: boolean }) {
  return (
    <div className={cn('rounded-xl border p-4 transition-all', active ? 'border-emerald-400/30 bg-emerald-400/[0.06] shadow-glow' : 'border-white/[0.06] bg-white/[0.02]')}>
      <div className="flex items-center justify-between">
        <span className="text-[14px] font-bold text-white">{label}</span>
        <span className="font-mono font-num text-[11px] text-slate-500">{source}</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/[0.06]">
        <motion.div
          className={cn('h-full rounded-full', active ? 'bg-gradient-to-r from-emerald-400 to-teal-300' : 'bg-gradient-to-r from-slate-500 to-slate-400')}
          initial={{ width: 0 }}
          animate={{ width: `${weight * 100}%` }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <div className="mt-1.5 font-mono font-num text-[12px] font-semibold text-slate-200">weight {weight.toFixed(2)}</div>
    </div>
  )
}

export default function ConsensusView() {
  return (
    <div className="mx-auto max-w-[1280px] px-6 py-8">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
        <div className="mb-6">
          <h1 className="text-xl font-bold tracking-tight text-white">Consensus · Conflict Resolution through Precedents</h1>
          <p className="mt-0.5 text-[12px] text-slate-500">watts / wv-1011 / thread_standard — unresolved signal resolved by a matched ledger precedent</p>
        </div>

        <div className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <WeightBar label="NPT" source="spec-sheet.pdf · ×1.0" weight={0.84} active />
          <WeightBar label="BSPT" source="product-page · ×0.7" weight={0.54} />
        </div>

        <div className="mb-5 grid gap-4 lg:grid-cols-2">
          <GlassCard delay={0.1}>
            <div className="p-5">
              <div className="mb-3 flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-slate-500" strokeWidth={1.8} />
                <SectionTitle>Counterfactual — without precedent</SectionTitle>
              </div>
              <div className="rounded-xl border border-white/[0.06] bg-white/[0.01] p-4">
                <div className="flex items-center gap-2 text-[12px] text-slate-400">
                  <span className="font-mono font-semibold text-slate-300">0.54</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                  <span className="rounded-md bg-amber-400/10 px-2 py-0.5 font-mono font-bold text-amber-300">REFUSED</span>
                </div>
                <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
                  Below the 0.70 threshold with no family boost — SEMI refuses this value rather than guess.
                </p>
              </div>
            </div>
          </GlassCard>

          <GlassCard delay={0.15} glow>
            <div className="border-emerald-400/20 bg-emerald-400/[0.03] p-5">
              <div className="mb-3 flex items-center gap-2">
                <Zap className="h-4 w-4 text-emerald-300" strokeWidth={1.8} />
                <SectionTitle className="text-emerald-300/80">Counterfactual — with precedent #007</SectionTitle>
              </div>
              <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/[0.05] p-4">
                <div className="flex items-center gap-2 text-[12px]">
                  <span className="font-mono font-semibold text-slate-200">0.54</span>
                  <span className="font-mono font-bold text-emerald-300">+0.30</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                  <span className="rounded-md bg-emerald-400/15 px-2 py-0.5 font-mono font-bold text-emerald-300">ACCEPTED · 0.84</span>
                </div>
                <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
                  Same conflict signature <span className="font-mono text-slate-400">NPT-vs-BSPT</span> resolved as NPT across 3
                  manufacturers. <span className="text-emerald-300 font-semibold">ledger_changed_outcome = true</span> — the system
                  changed its output because it remembered.
                </p>
              </div>
            </div>
          </GlassCard>
        </div>

        <GlassCard delay={0.2}>
          <PanelHeader
            title="Precedent Ledger"
            subtitle="recent resolutions"
            right={<><StatusPill label="auto-apply on" tone="emerald" pulse /></>}
          />
          <div className="divide-y divide-white/[0.04]">
            {LEDGER_EVENTS.map((ev) => (
              <div key={`${ev.at}-${ev.sku}`} className="flex items-center gap-3 px-5 py-3 text-[12px] transition-colors hover:bg-white/[0.02]">
                <span className="font-mono font-num text-[11px] text-slate-600 w-12">{ev.at}</span>
                <span className="w-44 font-mono text-slate-300">{ev.signature}</span>
                <span className="flex-1 text-slate-400">{ev.resolution}</span>
                <span className="font-mono text-[11px] text-slate-500">{ev.sku}</span>
                {ev.changedOutcome ? (
                  <StatusPill label="changed outcome" tone="emerald" />
                ) : (
                  <StatusPill label="confirm" tone="slate" />
                )}
              </div>
            ))}
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}