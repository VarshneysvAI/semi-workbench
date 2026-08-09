import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { INTERVAL_MS, SemiEngine, type Speed } from './engine'
import { COL_KEYS, type Sku, type Stage } from '../data/seed'

export interface Summary {
  rowsTotal: number
  rowsQueued: number
  rowsInFlight: number
  rowsDone: number
  rowsConflict: number
  rowsRefused: number
  cellsWritten: number
  cellsTotal: number
  declinedCells: number
  stageCounts: Partial<Record<Stage, number>>
  donePct: number
}

interface SemiApi {
  engine: SemiEngine
  summary: Summary
  running: boolean
  speed: Speed
  live: 'probe' | 'live' | 'sim'
  setRunning: (v: boolean) => void
  setSpeedBy: (s: Speed) => void
  resolveRow: (skuId: string, choice: 'A' | 'B', note: string) => void
  refuseRow: (skuId: string) => void
  resetEngine: () => void
  select: (skuId: string | null) => void
  selectedId: string | null
  selectedSku: Sku | null
}

const Ctx = createContext<SemiApi | null>(null)

export function useSemi(): SemiApi {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useSemi must be used inside <SemiProvider>')
  return ctx
}

function summarize(rows: Sku[]): Summary {
  const stageCounts: Partial<Record<Stage, number>> = {}
  let cellsWritten = 0
  let declinedCells = 0
  for (const r of rows) {
    stageCounts[r.stage] = (stageCounts[r.stage] ?? 0) + 1
    for (const k in r.cells) {
      const c = r.cells[k]
      if (c.state === 'written') cellsWritten++
      if (c.state === 'refused') declinedCells++
    }
  }
  return {
    rowsTotal: rows.length,
    rowsQueued: stageCounts.queued ?? 0,
    rowsInFlight: (stageCounts.discover ?? 0) + (stageCounts.extract ?? 0) + (stageCounts.audit ?? 0),
    rowsDone: stageCounts.done ?? 0,
    rowsConflict: stageCounts.conflict ?? 0,
    rowsRefused: stageCounts.refused ?? 0,
    stageCounts,
    cellsWritten,
    cellsTotal: rows.length * COL_KEYS.length,
    declinedCells,
    donePct: rows.length ? ((stageCounts.done ?? 0) / rows.length) * 100 : 0,
  }
}

export function SemiProvider({ children }: { children: ReactNode }) {
  const engineRef = useRef<SemiEngine | null>(null)
  if (!engineRef.current) engineRef.current = new SemiEngine()
  const engine = engineRef.current

  const [version, setVersion] = useState(0)
  const bump = () => setVersion((v) => v + 1)

  const [running, setRunningLocal] = useState(true)
  const [speed, setSpeedLocal] = useState<Speed>(1)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [live, setLive] = useState<'probe' | 'live' | 'sim'>('probe')

  useEffect(() => {
    let cancelled = false
    fetch('/api/health')
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        if (!cancelled) setLive(j?.status === 'ok' ? 'live' : 'sim')
      })
      .catch(() => {
        if (!cancelled) setLive('sim')
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!running) return
    const iv = setInterval(() => {
      engine.tick()
      bump()
    }, INTERVAL_MS[speed])
    return () => clearInterval(iv)
  }, [engine, running, speed])

  const api = useMemo<SemiApi>(() => {
    const setRunning = (v: boolean) => {
      engine.setPaused(!v)
      setRunningLocal(v)
    }
    return {
      engine,
      summary: summarize(engine.state.rows),
      running,
      speed,
      live,
      setRunning,
      setSpeedBy: (s) => {
        engine.setSpeed(s)
        setSpeedLocal(s)
      },
      resolveRow: (skuId, choice, note) => {
        engine.resolve(skuId, choice, note)
        bump()
      },
      refuseRow: (skuId) => {
        engine.refuse(skuId)
        bump()
      },
      resetEngine: () => {
        engine.reset()
        setSelectedId(null)
        bump()
      },
      select: (skuId) => setSelectedId(skuId),
      selectedId,
      selectedSku: selectedId ? (engine.state.rows.find((r) => r.id === selectedId) ?? null) : null,
    }
  }, [engine, running, speed, selectedId, live, version])

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>
}