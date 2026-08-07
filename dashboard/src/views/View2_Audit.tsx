import { motion } from 'framer-motion'
import { ShieldCheck } from 'lucide-react'
import { AUDIT_GROUPS, type AuditGroup, type AuditState } from '../data/mock'
import { GlassCard, StatusPill } from '../components/ui'
import { cn } from '../lib/cn'

const VERDICT_UI: Record<string, { label: string; tone: 'emerald' | 'violet' | 'amber' | 'rose' }> = {
  accepted: { label: 'ACCEPTED', tone: 'emerald' },
  conflict: { label: 'CONFLICT → review', tone: 'rose' },
  refused: { label: 'REFUSED', tone: 'amber' },
  review: { label: 'REVIEW', tone: 'violet' },
}

const CHECK_UI: Record<AuditState, { label: string; tone: 'emerald' | 'rose' | 'cyan' }> = {
  pass: { label: 'PASS', tone: 'emerald' },
  fail: { label: 'FAIL', tone: 'rose' },
  run: { label: 'RUNNING', tone: 'cyan' },
}

function AuditCard({ group }: { group: AuditGroup }) {
  const v = VERDICT_UI[group.ok]
  const pct = group.confidence * 100
  return (
    <GlassCard delay={0.1}>
      <div className="p-5">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <div className="text-[12px] text-slate-500">
              <span className="font-semibold text-slate-300">{group.sku}</span>
              <span className="mx-1.5 text-slate-600">/</span>
              <span className="font-mono">{group.attribute}</span>
            </div>
            <div className="mt-1.5 text-lg font-bold tracking-tight text-white">
              {group.value}
              {group.unit && <span className="ml-1 text-sm font-medium text-slate-500">{group.unit}</span>}
            </div>
          </div>
          <div className="text-right">
            <StatusPill label={v.label} tone={v.tone} pulse={group.ok === 'conflict'} />
            <div className="mt-2 font-mono font-num text-[13px] font-semibold text-slate-100">
              {group.confidence.toFixed(2)}
              <span className="text-[10px] text-slate-500"> CI [{group.conformal[0]}, {group.conformal[1]}]</span>
            </div>
          </div>
        </div>

        <div className="space-y-1.5">
          {group.checks.map((check) => {
            const chk = CHECK_UI[check.state]
            return (
              <div
                key={check.label}
                className={cn(
                  'flex items-center justify-between gap-3 rounded-lg border px-3 py-2 transition-colors',
                  check.state === 'run'
                    ? 'border-cyan-400/20 bg-cyan-400/[0.04]'
                    : 'border-white/[0.05] bg-white/[0.015]',
                )}
              >
                <span className={cn('text-[12px]', check.state === 'run' ? 'text-slate-200' : 'text-slate-400')}>
                  {check.label}
                </span>
                <span className="flex items-center gap-2">
                  <span className="hidden text-[11px] text-slate-500 sm:inline">{check.note}</span>
                  <StatusPill label={chk.label} tone={chk.tone} pulse={check.state === 'run'} />
                </span>
              </div>
            )
          })}
        </div>

        <div className="mt-4">
          <div className="mb-1 flex justify-between text-[10px] text-slate-500">
            <span>weighted score</span>
            <span className="font-mono font-num">{pct.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.06]">
            <motion.div
              className={cn(
                'h-full rounded-full',
                pct >= 70 ? 'bg-gradient-to-r from-emerald-400 to-teal-300' : 'bg-gradient-to-r from-amber-400 to-rose-400',
              )}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
          <div className="mt-1.5 text-[10px] text-slate-600">threshold 0.70 · family boost applies in consensus</div>
        </div>
      </div>
    </GlassCard>
  )
}

export default function AuditView() {
  return (
    <div className="mx-auto max-w-[1280px] px-6 py-8">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/10">
              <ShieldCheck className="h-5 w-5 text-emerald-300" strokeWidth={1.8} />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">Adversarial Self-Audit</h1>
              <p className="text-[12px] text-slate-500">Five independent audits per candidate — only survivors reach consensus</p>
            </div>
          </div>
          <StatusPill label="audit engine online" tone="emerald" pulse />
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {AUDIT_GROUPS.map((group) => (
            <AuditCard key={`${group.sku}-${group.attribute}`} group={group} />
          ))}
        </div>

        <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-5">
          {[
            { n: 'Physical', hint: 'PVC ≤ 150 psi' },
            { n: 'Contradiction', hint: 'BGE-M3 cosine' },
            { n: 'Compositional', hint: 'constraint graph' },
            { n: 'Adversarial', hint: 'auto disproof' },
            { n: 'Conformal', hint: '95% coverage' },
          ].map((a) => (
            <GlassCard key={a.n} delay={0.2}>
              <div className="p-3 text-center">
                <div className="flex items-center justify-center gap-1.5 text-[12px] font-semibold text-slate-200">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-50" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                  </span>
                  {a.n}
                </div>
                <div className="mt-1 font-mono text-[10px] text-slate-500">{a.hint}</div>
              </div>
            </GlassCard>
          ))}
        </div>
      </motion.div>
    </div>
  )
}