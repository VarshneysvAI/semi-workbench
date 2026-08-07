import { Hash } from 'lucide-react'
import { NavLink, Route, Routes } from 'react-router-dom'
import View0_Discovery from './views/View0_Discovery'
import View1_Audit from './views/View1_Audit'
import View2_Consensus from './views/View2_Consensus'
import View3_Output from './views/View3_Output'
import View4_Evidence from './views/View4_Evidence'

const NAV_ITEMS = [
  { to: '/', label: 'Discovery', view: 'View 0' },
  { to: '/audit', label: 'Adversarial Audit', view: 'View 1' },
  { to: '/consensus', label: 'Consensus / Precedents', view: 'View 2' },
  { to: '/output', label: 'Schema-Bound Output', view: 'View 3' },
  { to: '/evidence', label: 'Evidence', view: 'View 4' },
]

const apiUrl = import.meta.env.VITE_API_URL ?? '/api'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="flex w-64 flex-none flex-col border-r border-slate-800 bg-slate-900/60">
        <div className="border-b border-slate-800 px-5 py-4">
          <div className="text-sm font-semibold tracking-wide text-indigo-300">SEMI</div>
          <div className="text-xs text-slate-500">Self-Evolving Manufacturer Intelligence</div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-indigo-500/15 text-indigo-200'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`
              }
            >
              <span className="mr-2 inline-block w-14 text-xs text-slate-600">{item.view}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-800 px-5 py-3 text-xs text-slate-600">
          API: {apiUrl}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-none items-center justify-between border-b border-slate-800 bg-slate-950/50 px-6 py-3">
          <span className="text-sm font-medium text-slate-300">Manufacturer Intelligence Console</span>
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">
            <Hash className="h-3.5 w-3.5" />
            ledger events: <span className="font-mono font-semibold">0</span>
          </div>
        </header>
        <main className="min-h-0 flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<View0_Discovery />} />
            <Route path="/audit" element={<View1_Audit />} />
            <Route path="/consensus" element={<View2_Consensus />} />
            <Route path="/output" element={<View3_Output />} />
            <Route path="/evidence" element={<View4_Evidence />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}