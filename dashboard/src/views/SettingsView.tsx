import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Cpu, Key, Database, Sliders, Save, CheckCircle2, ShieldAlert } from 'lucide-react'

export default function SettingsView() {
  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="mx-auto max-w-[1200px] space-y-6 p-6 lg:p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Engine Configuration</h1>
        <p className="mt-1 text-sm text-slate-400">Manage LLM parameters, extractor routing, and calibration limits.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* LLM Routing */}
          <section className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 shadow-xl backdrop-blur-md">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-accent/20 p-2 text-accent-strong">
                <Cpu size={20} />
              </div>
              <h2 className="text-lg font-medium">LLM Intelligence Routing</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-slate-500">Primary Model</label>
                <select className="w-full rounded-lg border border-white/[0.06] bg-black/40 p-2.5 text-sm outline-none transition-colors focus:border-accent">
                  <option>gemini-2.5-pro</option>
                  <option>gemini-2.5-flash</option>
                  <option>gemma-2-9b-it (Local via vLLM)</option>
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-slate-500">Temperature</label>
                  <input type="range" min="0" max="1" step="0.1" defaultValue="0" className="w-full accent-accent" />
                  <div className="mt-1 text-right font-mono text-[10px] text-slate-400">0.0 (Strict Determinism)</div>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-slate-500">Max Tokens</label>
                  <input type="number" defaultValue="4096" className="w-full rounded-lg border border-white/[0.06] bg-black/40 p-2.5 font-mono text-sm outline-none transition-colors focus:border-accent" />
                </div>
              </div>
            </div>
          </section>

          {/* Audit Calibration */}
          <section className="rounded-xl border border-amber-500/[0.15] bg-amber-500/[0.02] p-6 shadow-xl backdrop-blur-md">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-amber-500/20 p-2 text-amber-500">
                <Sliders size={20} />
              </div>
              <h2 className="text-lg font-medium text-amber-500">Audit & Consensus Calibration</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 flex items-center justify-between text-xs font-medium uppercase tracking-wider text-amber-500/70">
                  <span>Conformal Emission Threshold</span>
                  <span className="font-mono text-amber-500">0.85</span>
                </label>
                <input type="range" min="0" max="1" step="0.05" defaultValue="0.85" className="w-full accent-amber-500" />
                <p className="mt-2 text-[11px] leading-relaxed text-amber-500/50">
                  Values below this confidence interval will be sent to the Review Queue (Gate 2).
                </p>
              </div>
            </div>
          </section>
        </div>

        <div className="space-y-6">
          {/* API Keys */}
          <section className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-6 shadow-xl backdrop-blur-md">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-cyan-400/20 p-2 text-cyan-400">
                <Key size={20} />
              </div>
              <h2 className="text-lg font-medium">Service Credentials</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-slate-500">Google AI Studio API Key</label>
                <input type="password" defaultValue="AIzaSyXXXXXXXXXXXXXXXX" className="w-full rounded-lg border border-white/[0.06] bg-black/40 p-2.5 font-mono text-sm text-slate-300 outline-none transition-colors focus:border-cyan-400" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-slate-500">Firecrawl API Key</label>
                <input type="password" defaultValue="fc-xxxxxxxxxxxxxxxxxxxx" className="w-full rounded-lg border border-white/[0.06] bg-black/40 p-2.5 font-mono text-sm text-slate-300 outline-none transition-colors focus:border-cyan-400" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-slate-500">Exa Search API Key</label>
                <input type="password" defaultValue="exa_xxxxxxxxxxxxxxxxxx" className="w-full rounded-lg border border-white/[0.06] bg-black/40 p-2.5 font-mono text-sm text-slate-300 outline-none transition-colors focus:border-cyan-400" />
              </div>
            </div>
          </section>

          {/* Database */}
          <section className="rounded-xl border border-rose-500/[0.15] bg-rose-500/[0.02] p-6 shadow-xl backdrop-blur-md">
            <div className="mb-4 flex items-center gap-3">
              <div className="rounded-lg bg-rose-500/20 p-2 text-rose-500">
                <Database size={20} />
              </div>
              <h2 className="text-lg font-medium text-rose-500">Data Management</h2>
            </div>
            <button className="w-full flex items-center justify-center gap-2 rounded-lg bg-rose-500/10 px-4 py-2.5 text-sm font-medium text-rose-500 transition-colors hover:bg-rose-500/20">
              <ShieldAlert size={16} />
              Purge Local SQLite State
            </button>
            <p className="mt-3 text-center text-[10.5px] text-rose-500/50">This will permanently delete all run data, ledgers, and extraction graphs.</p>
          </section>
        </div>
      </div>

      <div className="flex items-center justify-end gap-4 pt-4 border-t border-white/[0.08]">
        <AnimatePresence>
          {saved && (
            <motion.div
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 text-sm text-accent-strong"
            >
              <CheckCircle2 size={16} />
              Settings saved
            </motion.div>
          )}
        </AnimatePresence>
        <button
          onClick={handleSave}
          className="flex items-center gap-2 rounded-lg bg-accent px-6 py-2.5 text-sm font-semibold text-slate-900 transition-all hover:bg-accent-strong hover:shadow-[0_0_20px_rgba(52,211,153,0.3)] active:scale-95"
        >
          <Save size={16} />
          Save Configuration
        </button>
      </div>
    </div>
  )
}
