import { FileOutput } from 'lucide-react'

export default function View3_Output() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <FileOutput className="h-16 w-16 text-cyan-400" strokeWidth={1.2} />
      <h2 className="text-2xl font-semibold text-slate-100">Schema-Bound Output</h2>
      <p className="max-w-md text-sm text-slate-400">
        Every accepted field maps to the Unilog output schema with an audit report,
        conformal interval and evidence chain. True unknowns are marked
        INSUFFICIENT_EVIDENCE rather than guessed.
      </p>
    </div>
  )
}