import { motion } from 'framer-motion'
import { ServerCog, GitMerge, FileSearch, ShieldCheck } from 'lucide-react'

export default function AboutView() {
  return (
    <div className="mx-auto max-w-[900px] space-y-12 p-6 pb-20 lg:p-12">
      {/* Header */}
      <div className="text-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-accent/30 to-blue-500/30 p-4 shadow-[0_0_40px_rgba(52,211,153,0.15)] ring-1 ring-white/10"
        >
          <ServerCog className="h-10 w-10 text-accent-strong" />
        </motion.div>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Meet <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent to-blue-400">SEMI</span>
        </h1>
        <p className="mt-4 text-lg text-slate-400">
          Self-Evolving Manufacturer Intelligence.
        </p>
      </div>

      {/* Manifesto */}
      <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-p:text-slate-300">
        <p className="text-[15px]">
          Industrial distribution catalogs are notoriously fragmented. Suppliers push spreadsheets full of gaps, contradictions, and non-standard units. Traditional deterministic parsers break the moment a column header changes. Relying purely on generative AI leads to dangerous hallucinations in critical engineering specs.
        </p>
        <p className="text-[15px]">
          <strong>SEMI solves this with a deterministic orchestration framework wrapping highly-scoped LLM extractors.</strong> We don't ask the LLM to do math or make assumptions. We ask the LLM to read a single PDF bounding box or website chunk, extract the literal string, and cite the evidence.
        </p>
      </div>

      {/* Architecture Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 shadow-xl transition-all hover:bg-white/[0.04]">
          <div className="mb-4 inline-flex rounded-lg bg-blue-500/20 p-2 text-blue-400">
            <FileSearch size={24} />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-white">Parallel Extraction</h3>
          <p className="text-[13px] leading-relaxed text-slate-400">
            Deep HTML crawls, OCR-powered PDF parsing, and YouTube transcript extraction run concurrently to gather maximum evidence points.
          </p>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 shadow-xl transition-all hover:bg-white/[0.04]">
          <div className="mb-4 inline-flex rounded-lg bg-purple-500/20 p-2 text-purple-400">
            <GitMerge size={24} />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-white">Two-Pass Normalization</h3>
          <p className="text-[13px] leading-relaxed text-slate-400">
            A context-aware semantic pass maps varied labels (e.g. "OAL" vs "Overall Length") to canonical keys, followed by deterministic unit conversion.
          </p>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 shadow-xl transition-all hover:bg-white/[0.04]">
          <div className="mb-4 inline-flex rounded-lg bg-amber-500/20 p-2 text-amber-500">
            <ShieldCheck size={24} />
          </div>
          <h3 className="mb-2 text-lg font-semibold text-white">Adversarial Audit</h3>
          <p className="text-[13px] leading-relaxed text-slate-400">
            Every canonical truth is subjected to physical rule checks, contradiction detection, and conformal calibration before emission.
          </p>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center pt-8 border-t border-white/[0.08]">
        <div className="font-mono text-[10px] uppercase tracking-widest text-slate-500">Built for UniHack 2026</div>
        <div className="mt-2 text-sm text-slate-400">Team Varshney</div>
      </div>
    </div>
  )
}
