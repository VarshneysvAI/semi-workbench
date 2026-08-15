import { motion } from 'framer-motion'
import { Book, HelpCircle, MessageCircleQuestion, TerminalSquare, AlertTriangle } from 'lucide-react'

export default function HelpView() {
  return (
    <div className="mx-auto max-w-[800px] space-y-8 p-6 pt-12 lg:p-8 lg:pt-14">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Help & Documentation</h1>
        <p className="mt-1 text-sm text-slate-400">Learn how to operate the SEMI autonomous pipeline.</p>
      </div>

      <div className="grid gap-6">
        {/* Quick Start */}
        <div className="rounded-xl border border-white/[0.08] bg-gradient-to-br from-white/[0.04] to-transparent p-6 shadow-xl backdrop-blur-md">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-lg bg-accent/20 p-2 text-accent-strong">
              <TerminalSquare size={20} />
            </div>
            <h2 className="text-lg font-medium text-white">Quick Start</h2>
          </div>
          <div className="space-y-4 text-sm text-slate-300">
            <p>
              SEMI is designed to run autonomously. To begin an enrichment run:
            </p>
            <ol className="ml-4 list-decimal space-y-2 text-slate-400">
              <li>Upload a manufacturer workbook (.xlsx) via the backend ingestion API.</li>
              <li>SEMI will infer the ontology and map the columns to its internal 252-column schema.</li>
              <li>Navigate to the <strong>Overview</strong> dashboard and click "Run Engine".</li>
              <li>Monitor the live stream. If contradictory evidence is found, the SKU will be routed to the <strong>Review Queue</strong>.</li>
            </ol>
          </div>
        </div>

        {/* Review Queue Explanation */}
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 shadow-xl backdrop-blur-md">
          <div className="mb-4 flex items-center gap-3">
            <div className="rounded-lg bg-amber-500/20 p-2 text-amber-500">
              <AlertTriangle size={20} />
            </div>
            <h2 className="text-lg font-medium text-white">Understanding the Review Queue</h2>
          </div>
          <div className="space-y-4 text-sm text-slate-400 leading-relaxed">
            <p>
              SEMI will <strong>never guess</strong> when it encounters conflicting facts. 
              For example, if a manufacturer's PDF manual states the voltage is 120V, but a distributor's website states 240V, the Audit Engine will flag a <strong>Cross-Source Contradiction</strong>.
            </p>
            <p>
              Administrators must visit the <strong>Review Queue</strong> to view the highlighted source documents side-by-side and select the correct canonical value. This resolution is then permanently stored in the <strong>Ledger</strong> to autonomously resolve future conflicts.
            </p>
          </div>
        </div>

        {/* FAQ */}
        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 shadow-xl backdrop-blur-md">
          <div className="mb-6 flex items-center gap-3">
            <div className="rounded-lg bg-blue-500/20 p-2 text-blue-400">
              <MessageCircleQuestion size={20} />
            </div>
            <h2 className="text-lg font-medium text-white">Frequently Asked Questions</h2>
          </div>
          
          <div className="space-y-6">
            <div>
              <h4 className="font-medium text-slate-200">How do I export the final 252-column sheet?</h4>
              <p className="mt-1 text-[13px] text-slate-400">Once rows reach the "Done" stage, they are automatically synchronized to the local `unilog_output.xlsx` file in the root directory by the backend assembler.</p>
            </div>
            <div>
              <h4 className="font-medium text-slate-200">Can I force SEMI to re-crawl a page?</h4>
              <p className="mt-1 text-[13px] text-slate-400">Yes. Navigate to the <strong>Evidence</strong> tab, locate the specific URL, and click the refresh icon. This will bypass the local cache and trigger a fresh Firecrawl scrape.</p>
            </div>
            <div>
              <h4 className="font-medium text-slate-200">Why are some SKUs stuck in "Refused"?</h4>
              <p className="mt-1 text-[13px] text-slate-400">A "Refused" status indicates that SEMI could not find sufficient authoritative evidence on the web to populate the required schema fields safely. This is a deliberate safety mechanism to prevent hallucinated data.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
