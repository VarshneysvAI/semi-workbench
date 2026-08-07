import { ShieldCheck } from 'lucide-react'

export default function View1_Audit() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <ShieldCheck className="h-16 w-16 text-emerald-400" strokeWidth={1.2} />
      <h2 className="text-2xl font-semibold text-slate-100">Adversarial Audit</h2>
      <p className="max-w-md text-sm text-slate-400">
        Five audits per candidate value: physical constraints, cross-source contradiction,
        compositional consistency, adversarial disproof search, and conformal prediction
        with a 95% coverage interval. Only survivors reach consensus.
      </p>
    </div>
  )
}