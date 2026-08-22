import { useEffect, useRef, useState } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { AnimatePresence, MotionConfig, motion } from 'framer-motion'
import { SemiProvider, useSemi } from './engine/SemiContext'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Overview from './views/Overview'
import SheetView from './views/SheetView'
import DiscoveryView from './views/DiscoveryView'
import AuditView from './views/AuditView'
import ConflictsView from './views/ConflictsView'
import EvidenceView from './views/EvidenceView'
import LedgerView from './views/LedgerView'
import HistoryView from './views/HistoryView'
import SettingsView from './views/SettingsView'

import AboutView from './views/AboutView'
import HelpView from './views/HelpView'

const EASE = [0.23, 1, 0.32, 1] as const
const MIN_W = 208
const MAX_W = 560

function Boot() {
  const [done, setDone] = useState(() => sessionStorage.getItem('semi-booted') === '1')
  const timer = useRef<number | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [duration, setDuration] = useState<number>(12)
  const [reduced] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )

  const dismiss = () => {
    if (timer.current) window.clearTimeout(timer.current)
    sessionStorage.setItem('semi-booted', '1')
    setDone(true)
  }

  const handleLoadedMetadata = () => {
    const v = videoRef.current
    if (v && v.duration && !isNaN(v.duration) && v.duration > 0) {
      setDuration(v.duration)
      if (timer.current) window.clearTimeout(timer.current)
      const cap = (v.duration + 3) * 1000
      timer.current = window.setTimeout(() => {
        dismiss()
      }, cap)
    }
  }

  useEffect(() => {
    if (done) return
    if (sessionStorage.getItem('semi-booted') === '1') {
      setDone(true)
      return
    }
    const v = videoRef.current
    if (v && !reduced) {
      v.play().catch(() => dismiss())
    } else {
      dismiss()
    }
    const cap = reduced ? 800 : 15000
    timer.current = window.setTimeout(() => {
      dismiss()
    }, cap)
    return () => {
      if (timer.current) window.clearTimeout(timer.current)
    }
  }, [done, reduced])

  return (
    <AnimatePresence>
      {!done && (
        <motion.div
          key="boot"
          initial={{ opacity: 1 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          onClick={dismiss}
          className="fixed inset-0 z-[60] flex cursor-pointer items-center justify-center overflow-hidden bg-[var(--app-bg)]"
        >
          {reduced ? (
            <div className="absolute inset-0 bg-[var(--app-bg)]" />
          ) : (
            <video
              ref={videoRef}
              src="/boot.mp4"
              autoPlay
              muted
              playsInline
              onLoadedMetadata={handleLoadedMetadata}
              onEnded={dismiss}
              onError={dismiss}
              className="absolute inset-0 h-full w-full object-cover opacity-70"
            />
          )}

          <div className="pointer-events-none absolute inset-0 bg-black/30" />

          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.25, ease: EASE }}
            className="relative z-10 flex w-full flex-col items-center px-8"
          >
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.4 }}
              className="mt-8 h-px w-56 overflow-hidden bg-white/[0.12]"
            >
              <motion.div
                initial={{ width: '0%' }}
                animate={{ width: '100%' }}
                transition={{ duration: reduced ? 1.6 : duration, ease: 'linear' }}
                className="h-full bg-white/50"
              />
            </motion.div>
            <div className="mono mt-4 text-[9.5px] tracking-[0.22em] text-slate-400/70">
              click anywhere to skip
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function Shell() {
  const { summary, running } = useSemi()
  const [overlay, setOverlay] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const [width, setWidth] = useState(272)
  const [dragging, setDragging] = useState(false)
  const dragRef = useRef<{ startX: number; startW: number } | null>(null)
  const location = useLocation()

  useEffect(() => {
    if (!dragging) return
    const move = (e: PointerEvent) => {
      const d = dragRef.current
      if (!d) return
      setWidth(Math.min(MAX_W, Math.max(MIN_W, d.startW + (e.clientX - d.startX))))
    }
    const up = () => {
      dragRef.current = null
      setDragging(false)
    }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
    return () => {
      window.removeEventListener('pointermove', move)
      window.removeEventListener('pointerup', up)
    }
  }, [dragging])

  const startResize = (e: React.PointerEvent) => {
    dragRef.current = { startX: e.clientX, startW: width }
    setDragging(true)
  }

  const toggleSidebar = () => {
    if (window.innerWidth < 768) setOverlay((v) => !v)
    else setCollapsed((c) => !c)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--app-bg)] text-slate-100">
      <div className="canvas-orbs" aria-hidden>
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="orb orb-c" />
      </div>
      <div className="canvas-grid" aria-hidden />
      <div className="canvas-noise" aria-hidden />

      <div className="relative z-10 flex h-full w-full">
        <Sidebar
          conflicts={summary.rowsConflict}
          live={running}
          width={width}
          collapsed={collapsed}
          overlayOpen={overlay}
          dragging={dragging}
          onClose={() => setOverlay(false)}
          onStartResize={startResize}
          onToggleCollapse={() => setCollapsed((c) => !c)}
        />
        <div className="relative flex min-w-0 flex-1 flex-col">
          <Header onToggleNav={toggleSidebar} />
          <main className="min-h-0 flex-1 overflow-y-auto">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={location.pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22, ease: EASE }}
              >
                <Routes location={location}>
                  <Route path="/" element={<Overview />} />
                  <Route path="/sheet" element={<SheetView />} />
                  <Route path="/discovery" element={<DiscoveryView />} />
                  <Route path="/audit" element={<AuditView />} />
                  <Route path="/conflicts" element={<ConflictsView />} />
                  <Route path="/evidence" element={<EvidenceView />} />
                  <Route path="/ledger" element={<LedgerView />} />
                  <Route path="/history" element={<HistoryView />} />
                  <Route path="/settings" element={<SettingsView />} />
                  <Route path="/about" element={<AboutView />} />
                  <Route path="/help" element={<HelpView />} />


                </Routes>
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <SemiProvider>
        <Boot />
        <Shell />
      </SemiProvider>
    </MotionConfig>
  )
}