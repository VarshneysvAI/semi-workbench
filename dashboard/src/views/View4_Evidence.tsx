import { ScrollText } from 'lucide-react'

export default function View4_Evidence() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <ScrollText className="h-16 w-16 text-violet-400" strokeWidth={1.2} />
      <h2 className="text-2xl font-semibold text-slate-100">Evidence Viewer</h2>
      <p className="max-w-md text-sm text-slate-400">
        For each emitted value: source URL, page, bounding box, raw extract and
        extractor. Every ledger row keeps its source link for transparency.
      </p>
    </div>
  )
}