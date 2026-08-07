import { useEffect, useState } from 'react'
import { BookOpenCheck, Search } from 'lucide-react'
import { useLocation } from 'react-router-dom'

const PAGE_TITLES: Record<string, string> = {
  '/': 'Overview',
  '/discovery': 'Discovery',
  '/audit': 'Adversarial Audit',
  '/consensus': 'Consensus',
  '/output': 'Schema Output',
}

function useClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  const t = now.toLocaleTimeString('en-GB', { hour12: false })
  const d = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  return { t, d }
}

export default function TopBar() {
  const { pathname } = useLocation()
  const { t, d } = useClock()
  const title = PAGE_TITLES[pathname] ?? 'Workspace'

  return (
    <header className="flex flex-none items-center justify-between gap-4 border-b border-white/[0.06] bg-ink/40 px-6 py-3 backdrop-blur-md">
      <div className="flex min-w-0 items-center gap-3">
        <div className="truncate text-[13px] text-slate-400">
          <span className="text-slate-600">Manufacturing /</span> {title}
        </div>
        <span className="hidden items-center gap-1.5 rounded-md border border-amber-400/20 bg-amber-400/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300/90 md:inline-flex">
          UI preview · sample data
        </span>
      </div>

      <div className="flex flex-none items-center gap-4">
        <div className="hidden items-center gap-2 rounded-xl border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-[12px] text-slate-500 lg:flex">
          <Search className="h-3.5 w-3.5" strokeWidth={2} />
          <span className="pr-8">Filter by manufacturer, SKU…</span>
          <kbd className="rounded border border-white/10 bg-white/5 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">⌘K</kbd>
        </div>

        <div className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/[0.07] px-3 py-1.5">
          <BookOpenCheck className="h-4 w-4 text-emerald-300" strokeWidth={1.8} />
          <div className="leading-none">
            <div className="font-mono text-[12px] font-semibold text-emerald-300">7</div>
            <div className="text-[9px] uppercase tracking-wider text-emerald-400/70">precedents</div>
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] px-3 py-1.5 text-right leading-none">
          <div className="font-mono font-num text-[12px] font-semibold text-slate-100">{t}</div>
          <div className="mt-0.5 text-[9px] uppercase tracking-wider text-slate-500">{d}</div>
        </div>
      </div>
    </header>
  )
}