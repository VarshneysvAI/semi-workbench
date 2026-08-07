import { type LucideIcon, Cpu, FileOutput, Radar, Scale, ScrollText, ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '../lib/cn'

const NAV: Array<{ to: string; label: string; tag: string; icon: LucideIcon }> = [
  { to: '/', label: 'Overview', tag: '00', icon: Cpu },
  { to: '/discovery', label: 'Discovery', tag: '01', icon: Radar },
  { to: '/audit', label: 'Adversarial Audit', tag: '02', icon: ShieldCheck },
  { to: '/consensus', label: 'Consensus', tag: '03', icon: Scale },
  { to: '/output', label: 'Schema Output', tag: '04', icon: FileOutput },
  { to: '/evidence', label: 'Evidence', tag: '05', icon: ScrollText },
]

export default function Sidebar() {
  return (
    <aside className="flex w-60 flex-none flex-col border-r border-white/[0.06] bg-ink-2/80">
      <div className="flex items-center gap-3 px-4 py-5">
        <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400/80 to-violet-500/80 shadow-sm">
          <span className="font-mono text-base font-bold text-ink">S</span>
          <span className="absolute inset-0 rounded-xl ring-1 ring-inset ring-white/20" />
        </div>
        <div>
          <div className="text-[15px] font-bold tracking-tight text-white">SEMI</div>
          <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-slate-500">Intelligence console</div>
        </div>
      </div>

      <div className="px-4 pb-2 pt-3">
        <div className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-600">Workspace</div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-colors',
                isActive ? 'text-white' : 'text-slate-400 hover:text-slate-200',
              )
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-emerald-500/[0.16] to-violet-500/[0.07] ring-1 ring-inset ring-white/[0.07]" />
                )}
                <item.icon className="relative h-4 w-4 shrink-0" strokeWidth={1.8} />
                <span className="relative flex-1">{item.label}</span>
                <span className={cn('relative font-mono text-[10px]', isActive ? 'text-emerald-300/80' : 'text-slate-600')}>
                  {item.tag}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/[0.06] px-4 py-4">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
            <span className="relative h-2 w-2 rounded-full bg-emerald-400" />
          </span>
          <span className="text-[11px] font-medium text-emerald-300/90">7 systems operational</span>
        </div>
        <div className="mt-1 text-[10px] text-slate-600">Gemma 4 12B · BGE-M3 · local stack</div>
      </div>
    </aside>
  )
}