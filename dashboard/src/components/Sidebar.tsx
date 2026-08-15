import { NavLink } from 'react-router-dom'
import { motion, AnimatePresence, type Variants } from 'framer-motion'
import {
  LayoutDashboard,
  Table2,
  Radar,
  ShieldCheck,
  GitMerge,
  FileSearch,
  BookOpen,
  ChevronsLeft,
  ChevronsRight,
  Settings,
  Info,
  HelpCircle,
  type LucideIcon,
} from 'lucide-react'

const NAV: Array<{ to: string; label: string; icon: LucideIcon }> = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/sheet', label: 'Enrichment Sheet', icon: Table2 },
  { to: '/discovery', label: 'Discovery', icon: Radar },
  { to: '/audit', label: 'Audit Engine', icon: ShieldCheck },
  { to: '/conflicts', label: 'Review Queue', icon: GitMerge },
  { to: '/evidence', label: 'Evidence', icon: FileSearch },
  { to: '/ledger', label: 'Ledger', icon: BookOpen },
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/about', label: 'About Us', icon: Info },
  { to: '/help', label: 'Help', icon: HelpCircle },
]

const listVariants: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04, delayChildren: 0.08 } },
}

const itemVariants: Variants = {
  hidden: { opacity: 0, x: -12 },
  show: { opacity: 1, x: 0, transition: { duration: 0.3, ease: [0.23, 1, 0.32, 1] } },
}

export default function Sidebar({
  conflicts,
  live,
  width,
  collapsed,
  overlayOpen,
  dragging,
  onClose,
  onStartResize,
  onToggleCollapse,
}: {
  conflicts: number
  live: boolean
  width: number
  collapsed: boolean
  overlayOpen: boolean
  dragging: boolean
  onClose: () => void
  onStartResize: (e: React.PointerEvent) => void
  onToggleCollapse: () => void
}) {
  const sideVisible = !collapsed

  const NavItems = (
    <motion.nav
      variants={listVariants}
      initial="hidden"
      animate="show"
      className="mt-2 flex-1 space-y-0.5 overflow-y-auto px-2"
    >
      {NAV.map((item) => (
        <motion.div key={item.to} variants={itemVariants}>
          <NavLink
            to={item.to}
            onClick={onClose}
            title={collapsed ? item.label : undefined}
            className={({ isActive }) =>
              `group flex items-center rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors ${
                collapsed ? 'justify-center px-2' : 'gap-2.5'
              } ${
                isActive
                  ? 'bg-white/[0.09] text-accent-strong'
                  : 'text-slate-400 hover:bg-white/[0.06] hover:text-slate-100'
              }`
            }
          >
            <item.icon
              size={15}
              strokeWidth={1.75}
              className="shrink-0 transition-transform duration-200 group-hover:translate-x-[2px]"
            />
            {sideVisible && (
              <>
                <span className="flex-1 truncate">{item.label}</span>
                {item.to === '/conflicts' && conflicts > 0 && (
                  <span className="mono rounded bg-amber-400/15 px-1.5 py-0.5 text-[10px] font-semibold text-amber-300">
                    {conflicts}
                  </span>
                )}
              </>
            )}
          </NavLink>
        </motion.div>
      ))}
    </motion.nav>
  )

  const ShowMain = (
    <>
      <header className="flex h-14 shrink-0 items-center justify-center gap-2.5 px-4 md:justify-start">
        {sideVisible ? (
          <img src="/logo.png" alt="SEMI workbench" className="h-8 w-auto max-w-[200px] object-contain" />
        ) : (
          <img src="/logo.png" alt="SEMI workbench" className="h-7 w-7 object-contain" />
        )}
      </header>

      {NavItems}

      <footer className="flex items-center justify-between border-t border-white/[0.07] px-2">
        <div className={`mono min-w-0 px-2 py-3 text-[10.5px] leading-relaxed text-slate-400 ${sideVisible ? '' : 'hidden'}`}>
          <span
            className={`mr-1.5 inline-block h-1.5 w-1.5 rounded-full ${
              live ? 'bg-cyan-400 dot-live' : 'bg-slate-600'
            }`}
          />
          {live ? 'SIM ENGINE · streaming' : 'engine paused'}
        </div>
        <button
          onClick={onToggleCollapse}
          className="focus-ring hidden rounded-md p-1.5 text-slate-500 transition-colors hover:bg-white/[0.05] hover:text-slate-200 md:block"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronsRight size={14} /> : <ChevronsLeft size={14} />}
        </button>
      </footer>
    </>
  )

  return (
    <div className="relative z-10 flex-none">
      {/* Desktop rail — resizable split */}
      <motion.aside
        initial={{ x: -24, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 280, damping: 30 }}
        className="hidden h-screen shrink-0 flex-col border-r border-white/[0.1] bg-white/[0.05] backdrop-blur-2xl md:flex"
        style={{
          width: collapsed ? 72 : width,
          transition: dragging ? 'none' : 'width 280ms var(--ease)',
        }}
      >
        {ShowMain}

        {!collapsed && (
          <button
            onPointerDown={onStartResize}
            title="Drag to resize"
            className="splitter group absolute inset-y-0 -right-[4px] z-20 w-[8px]"
            aria-label="Resize sidebar"
          >
            <span className="absolute inset-y-4 left-1/2 w-px -translate-x-1/2 bg-white/[0.08] transition-opacity duration-150 group-hover:opacity-0 group-hover:bg-accent-strong group-active:opacity-0 group-active:bg-accent-strong" />
          </button>
        )}
      </motion.aside>

      {/* Mobile overlay drawer */}
      <AnimatePresence>
        {overlayOpen && (
          <>
            <motion.div
              key="scrim"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={onClose}
              className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm md:hidden"
            />
            <motion.aside
              key="drawer"
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 32 }}
              className="fixed inset-y-0 left-0 z-40 flex w-[288px] flex-col border-r border-white/[0.1] bg-black/85 backdrop-blur-md md:hidden"
            >
              {ShowMain}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}