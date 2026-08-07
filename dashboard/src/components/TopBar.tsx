import { BookOpenCheck, Database, Search } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { StatusPill } from './ui'

const TITLES: Record<string, string> = {
  '/': 'Command Center — manufacturing intelligence at scale',
  '/discovery': 'Discovery — autonomous multi-source sourcing',
  '/audit': 'Adversarial Audit — 5 self-checks per candidate',
  '/consensus': 'Consensus — precedent-driven resolution',
  '/output': 'Schema Output — Unilog contract',
  '/evidence': 'Evidence — full provenance chain',
}

export default function TopBar() {
  const { pathname } = useLocation()
  return (
    <header className="flex flex-none items-center justify-between gap-4 border-b border-white/[0.06] bg-ink/40 px-6 py-3 backdrop-blur-xl">
      <div className="flex min-w-0 items-center gap-3">
        <h2 className="truncate text-[13px] font-medium text-slate-300">{TITLES[pathname] ?? 'Workspace'}</h2>
        <StatusPill label="v1.0 · sample data" tone="amber" />
      </div>

      <div className="flex flex-none items-center gap-3">
        <div className="hidden items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-[12px] text-slate-500 lg:flex">
          <Search className="h-3.5 w-3.5" strokeWidth={2} />
          <span className="pr-6">Filter manufacturers, SKUs…</span>
          <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">⌘K</kbd>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/[0.06] px-3 py-1.5">
          <Database className="h-3.5 w-3.5 text-cyan-300" strokeWidth={1.8} />
          <div className="leading-none">
            <div className="font-mono text-[12px] font-bold text-cyan-300">7</div>
            <div className="text-[8px] uppercase tracking-wider text-cyan-400/70">precedents</div>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/[0.06] px-3 py-1.5">
          <BookOpenCheck className="h-3.5 w-3.5 text-emerald-300" strokeWidth={1.8} />
          <div className="leading-none">
            <div className="font-mono text-[12px] font-bold text-emerald-300">97.8<span className="text-[10px]">%</span></div>
            <div className="text-[8px] uppercase tracking-wider text-emerald-400/70">certified</div>
          </div>
        </div>
      </div>
    </header>
  )
}