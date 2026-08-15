import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { type Speed } from './engine'
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
  engine: any
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
  const [running, setRunningLocal] = useState(true)
  const [speed, setSpeedLocal] = useState<Speed>(1)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const live = 'live'
  const [backendState, setBackendState] = useState<any>({ 
    rows: [], logs: [], events: [], ledger: [], changedOutcomes: 0, bytes: 0, tickCount: 0, idle: true, retrains: 0 
  })
  const [isProcessing, setIsProcessing] = useState(false)

  // 1. Fetch UI State continuously
  useEffect(() => {
    let cancelled = false
    const iv = setInterval(() => {
      fetch('http://127.0.0.1:8000/api/ui_state')
        .then((r) => r.json())
        .then((data) => {
          if (!cancelled) setBackendState(data)
        })
        .catch(() => {})
    }, 1000)
    return () => {
      cancelled = true
      clearInterval(iv)
    }
  }, [])

  // 2. Autonomous Processing Loop: Process one queued SKU at a time
  useEffect(() => {
    if (!running || isProcessing || backendState.rows.length === 0) return

    const nextQueued = backendState.rows.find((r) => r.stage === 'queued')
    if (nextQueued) {
      setIsProcessing(true)
      fetch(`http://127.0.0.1:8000/api/discover/${nextQueued.id.split('-').slice(1).join('-')}`, {
        method: 'POST'
      })
        .finally(() => {
          setIsProcessing(false)
        })
    }
  }, [backendState.rows, running, isProcessing])

  const engine = useMemo<any>(() => {
    return {
      state: backendState,
      setPaused: () => {},
      setSpeed: () => {},
      resolve: async (skuId: string, choice: 'A' | 'B', note: string) => {
        const row = backendState.rows.find((r) => r.id === skuId)
        if (!row || !row.conflict) return
        await fetch('http://127.0.0.1:8000/api/resolve', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sku: row.pn,
            attribute: row.conflict.col,
            human_resolution: choice === 'A' ? row.conflict.a.value : row.conflict.b.value,
            reason_tags: [note]
          })
        })
      },
      refuse: () => {},
      reset: () => {}
    }
  }, [backendState])

  const api = useMemo<SemiApi>(() => {
    const setRunning = (v: boolean) => setRunningLocal(v)
    return {
      engine,
      summary: summarize(engine.state.rows),
      running,
      speed,
      live,
      setRunning,
      setSpeedBy: (s) => setSpeedLocal(s),
      resolveRow: (skuId, choice, note) => engine.resolve(skuId, choice, note),
      refuseRow: () => {},
      resetEngine: () => { setSelectedId(null) },
      select: (skuId) => setSelectedId(skuId),
      selectedId,
      selectedSku: selectedId ? (engine.state.rows.find((r: Sku) => r.id === selectedId) ?? null) : null,
    }
  }, [engine, running, speed, selectedId, live])

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>
}