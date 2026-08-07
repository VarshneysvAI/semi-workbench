import { motion } from 'framer-motion'
import { Boxes, Check, Clipboard, Download } from 'lucide-react'
import { GlassCard, PanelHeader, StatusPill } from '../components/ui'

const OUTPUT_FIELDS: Array<{ key: string; value: string; unit: string; ok: boolean; verdict: string }> = [
  { key: 'thread_connection', value: 'NPT', unit: '', ok: true, verdict: '3 sources · CI [0.87, 0.99]' },
  { key: 'body_material', value: 'Brass', unit: '', ok: true, verdict: 'physical ✓ compositional ✓' },
  { key: 'pressure_rating', value: '150', unit: 'psi', ok: true, verdict: 'CI [145, 155] · 5/5 audits' },
  { key: 'temp_rating', value: '180', unit: '°F', ok: true, verdict: 'cross-source ✓ disproof: none' },
  { key: 'size', value: '50.8', unit: 'mm', ok: true, verdict: 'auto-converted 2 in → 50.8 mm' },
  { key: 'flow_coefficient', value: 'INSUFFICIENT_EVIDENCE', unit: '', ok: false, verdict: 'refused — only 1 low-authority source' },
  { key: 'media_type', value: 'INSUFFICIENT_EVIDENCE', unit: '', ok: false, verdict: 'disproved · nameplate contradicts' },
]

const JSON_SNIPPET = `{
  "manufacturer": "NIBCO",
  "part_number": "BV-3001",
  "source_urls": [
    "https://www.nibco.com/product/spec-bv-3001.pdf",
    "https://www.nibco.com/en/bv-3001"
  ],
  "attributes": {
    "thread_connection": {
      "value": "NPT",
      "unit": "",
      "conformal_ci": [0.87, 0.99],
      "audit_report": {
        "physical_constraints": "PASS",
        "cross_source_consensus": "PASS (3 sources)",
        "compositional_consistency": "PASS",
        "adversarial_disproof": "PASS (not found)",
        "conformal_coverage": 0.95
      },
      "evidence_chain": [
        {"source": "spec-sheet.pdf", "page": 3, "value": "NPT", "authority": 1.0},
        {"source": "product-page", "value": "NPT", "authority": 0.7}
      ]
    },
    "flow_coefficient": "INSUFFICIENT_EVIDENCE"
  },
  "enrichment_status": "PARTIAL"
}`

export default function OutputView() {
  return (
    <div className="mx-auto max-w-[1280px] px-6 py-8">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
        <div className="mb-6">
          <h1 className="text-xl font-bold tracking-tight text-white">Schema-Bound Output</h1>
          <p className="mt-0.5 text-[12px] text-slate-500">every field maps to the Unilog contract · certified or refused</p>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <GlassCard glow delay={0.1}>
            <PanelHeader
              title="Shadow Attributes — NIBCO BV-3001"
              subtitle="certified vs refused"
              right={<StatusPill label="5 certified · 2 refused" tone="emerald" />}
            />
            <div className="space-y-2 p-4">
              {OUTPUT_FIELDS.map((f) => (
                <div key={f.key} className="flex items-center gap-3 rounded-xl border border-white/[0.05] bg-white/[0.015] px-3 py-2.5 transition-colors hover:bg-white/[0.03]">
                  <span className={f.ok ? 'text-emerald-400' : 'text-amber-300'}>
                    {f.ok ? <Check className="h-4 w-4" strokeWidth={2.4} /> : <Boxes className="h-4 w-4" strokeWidth={1.8} />}
                  </span>
                  <span className="w-40 font-mono text-[12px] text-slate-400">{f.key}</span>
                  <span className="min-w-0 flex-1 truncate font-mono text-[13px] font-semibold text-white">
                    {f.value}
                    {f.unit && <span className="ml-1 text-[11px] font-medium text-slate-500">{f.unit}</span>}
                  </span>
                  <span className="hidden text-right text-[10px] leading-tight text-slate-500 sm:block max-w-[180px]">{f.verdict}</span>
                </div>
              ))}
            </div>
            <div className="border-t border-white/[0.06] p-4">
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-4 py-2.5 text-[12px] font-semibold text-cyan-200 shadow-glow transition-all hover:bg-cyan-400/20"
              >
                <Download className="h-3.5 w-3.5" /> Export evidence package
              </button>
            </div>
          </GlassCard>

          <GlassCard delay={0.15}>
            <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-2.5">
              <StatusPill label="output.json" tone="slate" />
              <button type="button" className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-[11px] text-slate-400 transition-colors hover:text-slate-200">
                <Clipboard className="h-3 w-3" /> copy
              </button>
            </div>
            <pre className="overflow-x-auto p-4 font-mono text-[11.5px] leading-relaxed">
              {JSON_SNIPPET.split('\n').map((line, i) => {
                let cls = 'text-slate-400'
                if (line.includes('"manufacturer"') || line.includes('"part_number"') || line.includes('"value"') || line.includes('"conformal_ci"')) cls = 'text-slate-200'
                if (line.includes('PASS') || line.includes('"PASS"')) cls = 'text-emerald-300'
                if (line.includes('INSUFFICIENT')) cls = 'text-amber-300'
                if (line.includes('"enrichment_status"')) cls = 'text-rose-300'
                return (
                  <div key={i} className={cls}>
                    {line || '\u00A0'}
                  </div>
                )
              })}
            </pre>
          </GlassCard>
        </div>
      </motion.div>
    </div>
  )
}