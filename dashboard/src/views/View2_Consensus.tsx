import { Scale } from 'lucide-react'

export default function View2_Consensus() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <Scale className="h-16 w-16 text-amber-400" strokeWidth={1.2} />
      <h2 className="text-2xl font-semibold text-slate-100">Consensus &amp; Precedents</h2>
      <p className="max-w-md text-sm text-slate-400">
        Source authority weighting plus family boost; a matched ledger precedent can
        change the outcome. Winners above threshold are ACCEPTED, otherwise the system
        refuses with INSUFFICIENT_EVIDENCE.
      </p>
    </div>
  )
}