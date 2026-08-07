import { type LucideIcon, Activity, Cpu, FileOutput, Radar, Scale, ScrollText, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import { cn } from '../lib/cn'

const NAV: Array<{ to: string; label: string; icon: LucideIcon }> = [
  { to: '/', label: 'Command Center', icon: Cpu },
  { to: '/discovery', label: 'Discovery', icon: Radar },
  { to: '/audit', label: 'Adversarial Audit', icon: ShieldCheck },
  { to: '/consensus', label: 'Consensus', icon: Scale },
  { to: '/output', label: 'Schema Output', icon: FileOutput },
  { to: '/evidence', label: 'Evidence', icon: ScrollText },
]

function useClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return {
    time: now.toLocaleTimeString('en-GB', { hour12: false }),
    date: now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }),
  }
}

export default function Sidebar() {
  const { time, date } = useClock()

  return (
    <aside className="flex w-[232px] flex-none flex-col border-r border-white/[0.06]">
      <div className="flex items-center gap-3 px-4 py-5">
        <div className="relative">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-violet-500 shadow-glow">
            <span className="font-mono text-sm font-extrabold text-ink">S</span>
          </div>
          <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-ink bg-emerald-400" />
        </div>
        <div className="min-w-0">
          <div className="truncate text-[15px] font-bold tracking-tight text-white">SEMI</div>
          <div className="truncate text-[10px] font-medium uppercase tracking-[0.2em] text-slate-500">Manufacturer Intelligence</div>
        </div>
      </div>

      <div className="px-4 pb-2 pt-2">
        <div className="text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-600">Workspace</div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-all duration-200',
                isActive
                  ? 'bg-gradient-to-r from-cyan-400/10 via-cyan-400/5 to-transparent text-white shadow-panel'
                  : 'text-slate-400 hover:bg-white/[0.03] hover:text-slate-200',
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-r-full bg-cyan-400 shadow-glow" />
                )}
                <item.icon
                  className={cn(
                    'h-4 w-4 shrink-0 transition-colors',
                    isActive ? 'text-cyan-300' : 'text-slate-500 group-hover:text-slate-300',
                  )}
                  strokeWidth={1.8}
                />
                <span className="truncate">{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/[0.06] px-4 py-4">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span className="text-[11px] font-medium text-emerald-300/90">All systems operational</span>
        </div>
        <div className="mt-3 flex items-center justify-between rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 py-2">
          <Activity className="h-3.5 w-3.5 text-cyan-300" />
          <div className="text-right">
            <div className="font-mono font-num text-[11px] font-bold text-slate-100">{time}</div>
            <div className="text-[9px] uppercase tracking-wider text-slate-500">{date}</div>
          </div>
        </div>
      </div>
    </aside>
  )
}