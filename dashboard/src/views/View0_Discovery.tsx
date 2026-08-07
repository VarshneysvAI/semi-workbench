import { Radar } from 'lucide-react'

export default function View0_Discovery() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 p-8 text-center">
      <Radar className="h-16 w-16 text-indigo-400" strokeWidth={1.2} />
      <h2 className="text-2xl font-semibold text-slate-100">Autonomous Discovery</h2>
      <p className="max-w-md text-sm text-slate-400">
        (manufacturer, part_number) → targeted site search → spec PDF, manual PDF, product
        page and video candidates ranked by authority. Forbidden marketplaces filtered out.
      </p>
    </div>
  )
}