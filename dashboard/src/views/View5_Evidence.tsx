import { motion } from 'framer-motion'
import { ExternalLink, ScanSearch } from 'lucide-react'
import { SOURCE_ROWS } from '../data/mock'
import { Panel, SectionTitle, StatusPill, type Tone } from '../components/ui'

const KIND_META: Record<string, { label: string; tone: Tone }> = {
  spec: { label: 'spec', tone: 'emerald' },
  manual: { label: 'manual', tone: 'violet' },
  page: { label: 'web', tone: 'cyan' },
  video: { label: 'video', tone: 'amber' },
}

const EXTRACTS: Array<{ field: string; value: string; sourceId: string; page: string; bbox: string; extractor: string; confidence: string }> = [
  { field: 'thread_connection', value: 'NPT', sourceId: 'S-01', page: 'p.3', bbox: '[84, 210, 96, 218]', extractor: 'regex', confidence: '0.99' },
  { field: 'thread_connection', value: 'NPT', sourceId: 'S-03', page: '—', bbox: '—', extractor: 'llm · gemma-4-12b', confidence: '0.94' },
  { field: 'pressure_rating', value: '150 psi', sourceId: 'S-02', page: 'p.12', bbox: '[30, 55, 118, 61]', extractor: 'regex', confidence: '0.97' },
  { field: 'pressure_rating', value: '150 psi', sourceId: 'S-01', page: 'p.3', bbox: '[44, 190, 60, 196]', extractor: 'regex', confidence: '0.98' },
  { field: 'size', value: '2 in', sourceId: 'S-03', page: '—', bbox: '—', extractor: 'llm · gemma-4-12b', confidence: '0.96' },
  { field: 'body_material', value: 'Brass', sourceId: 'S-04', page: 'img 1/3', bbox: '[12, 88, 55, 96]', extractor: 'ocr · easyocr', confidence: '0.91' },
]

export default function EvidenceView() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03]">
            <ScanSearch className="h-5 w-5 text-emerald-300" strokeWidth={1.8} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">Evidence Chain</h1>
            <p className="text-[12px] text-slate-500">every value links to the exact source, page and pixel that produced it</p>
          </div>
        </div>

        <Panel className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <SectionTitle>Extraction traces — BV-3001</SectionTitle>
            <StatusPill label="all URLs sourced" tone="emerald" />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[12px]">
              <thead>
                <tr className="border-b border-white/[0.06] text-[10px] uppercase tracking-[0.14em] text-slate-500">
                  <th className="pb-2 pr-3 font-semibold">attribute</th>
                  <th className="pb-2 pr-3 font-semibold">extracted value</th>
                  <th className="pb-2 pr-3 font-semibold">source</th>
                  <th className="pb-2 pr-3 font-semibold">loc</th>
                  <th className="pb-2 pr-3 font-semibold">bbox</th>
                  <th className="pb-2 pr-3 font-semibold">extractor</th>
                  <th className="pb-2 text-right font-semibold">conf</th>
                </tr>
              </thead>
              <tbody>
                {EXTRACTS.map((ex, i) => {
                  const src = SOURCE_ROWS.find((s) => s.id === ex.sourceId)
                  const kind = src ? KIND_META[src.kind] : null
                  return (
                    <tr key={i} className="border-b border-white/[0.04] last:border-0">
                      <td className="py-2.5 pr-3 font-mono text-slate-300">{ex.field}</td>
                      <td className="py-2.5 pr-3 font-mono font-semibold text-white">{ex.value}</td>
                      <td className="max-w-[220px] py-2.5 pr-3">
                        <div className="flex items-center gap-1.5">
                          <span className="truncate font-mono text-[11px] text-slate-400">{src?.title ?? ex.sourceId}</span>
                          <ExternalLink className="h-3 w-3 flex-none text-slate-600" />
                        </div>
                        {kind && <StatusPill label={kind.label} tone={kind.tone} className="mt-1" />}
                      </td>
                      <td className="py-2.5 pr-3 font-mono text-[11px] text-slate-500">{ex.page}</td>
                      <td className="py-2.5 pr-3 font-mono text-[10px] text-slate-600">{ex.bbox}</td>
                      <td className="py-2.5 pr-3 font-mono text-[11px] text-slate-400">{ex.extractor}</td>
                      <td className="py-2.5 text-right font-mono font-num text-slate-300">{ex.confidence}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-[11px] text-slate-500">
            deterministic-first: regex → 60-70% of fields at zero marginal cost; the local Gemma 4 12B fills only the gaps.
          </p>
        </Panel>
      </motion.div>
    </div>
  )
}