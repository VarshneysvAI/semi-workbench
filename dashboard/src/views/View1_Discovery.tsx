import { motion } from 'framer-motion'
import { Ban, BrainCircuit, FileText, Loader2, Router } from 'lucide-react'
import { DNA_CHIPS, SOURCE_ROWS } from '../data/mock'
import { cn } from '../lib/cn'
import { Panel, SectionTitle, StatusPill } from '../components/ui'

const KIND_META: Record<string, { label: string; tone: 'emerald' | 'violet' | 'cyan' | 'amber' }> = {
  spec: { label: 'spec sheet', tone: 'emerald' },
  manual: { label: 'manual', tone: 'violet' },
  page: { label: 'product page', tone: 'cyan' },
  video: { label: 'video', tone: 'amber' },
}

export default function DiscoveryView() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03]">
            <Router className="h-5 w-5 text-emerald-300" strokeWidth={1.8} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">Autonomous Discovery</h1>
            <p className="text-[12px] text-slate-500">Stage 01 — manufacturing site search → ranked, validated sources</p>
          </div>
        </div>

        <div className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Panel className="p-5 lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <SectionTitle>Discovered sources — NIBCO BV-3001</SectionTitle>
              <StatusPill label="4 validated" tone="emerald" pulse />
            </div>
            <div className="space-y-2">
              {SOURCE_ROWS.map((src) => {
                const kind = KIND_META[src.kind]
                const blocked = src.id === 'S-06'
                return (
                  <div
                    key={src.id}
                    className={cn(
                      'flex items-center gap-3 rounded-xl border px-3 py-2.5',
                      blocked ? 'border-rose-400/20 bg-rose-400/[0.04]' : 'border-white/[0.06] bg-white/[0.02]',
                    )}
                  >
                    <div
                      className={cn(
                        'flex h-8 w-8 flex-none items-center justify-center rounded-lg',
                        blocked ? 'bg-rose-400/10' : 'bg-gradient-to-br from-emerald-400/15 to-violet-500/15',
                      )}
                    >
                      {blocked ? (
                        <Ban className="h-4 w-4 text-rose-300" strokeWidth={1.8} />
                      ) : (
                        <FileText className="h-4 w-4 text-emerald-300" strokeWidth={1.8} />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-mono text-[12px] text-slate-200">{src.title}</div>
                      <div className="text-[10px] text-slate-500">
                        {src.sku} · {src.bytes}
                      </div>
                    </div>
                    {!blocked && (
                      <span className="font-mono font-num text-[11px] text-slate-400">
                        <span className="text-emerald-300/90">×</span> {src.authority.toFixed(1)}
                      </span>
                    )}
                    <div className="w-28 text-right">
                      {blocked ? (
                        <StatusPill label="blocked · amazon" tone="rose" />
                      ) : (
                        <StatusPill label={kind.label} tone={kind.tone} />
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
            <p className="mt-4 text-[11px] leading-relaxed text-slate-500">
              Authority: <span className="font-mono">spec 1.0 · manual 0.9 · page 0.7 · video 0.5</span>. Marketplace
              listing URLs are rejected before they ever reach the extractor.
            </p>
          </Panel>

          <Panel className="p-5">
            <SectionTitle className="mb-4">Manufacturer Extraction DNA</SectionTitle>
            <div className="space-y-3">
              {DNA_CHIPS.map((dna) => (
                <div key={dna.label} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                  <div className="flex items-start gap-2.5">
                    <BrainCircuit className="mt-0.5 h-4 w-4 flex-none text-violet-300" strokeWidth={1.8} />
                    <div>
                      <div className="text-[12px] font-medium leading-snug text-slate-200">{dna.label}</div>
                      <div className="mt-0.5 text-[10px] text-slate-500">{dna.note}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-4 flex items-center gap-1.5 text-[11px] text-slate-500">
              <Loader2 className="h-3 w-3 animate-spin text-emerald-300" />
              patterns compound on every SKU...
            </p>
          </Panel>
        </div>
      </motion.div>
    </div>
  )
}