import { motion } from 'framer-motion'

interface Node {
  id: string
  label: string
  x: number
  y: number
  r: number
  color: string
  pulse?: boolean
}

interface Edge {
  from: string
  to: string
  color?: string
  flow?: boolean
}

const NODES: Node[] = [
  { id: 'pn', label: 'NIBCO · BV-3001', x: 50, y: 50, r: 14, color: '#22d3ee', pulse: true },
  { id: 's1', label: 'spec-sheet.pdf', x: 18, y: 22, r: 9, color: '#5eead4' },
  { id: 's2', label: 'install manual', x: 16, y: 80, r: 9, color: '#5eead4' },
  { id: 's3', label: 'product page', x: 84, y: 20, r: 9, color: '#5eead4' },
  { id: 's4', label: 'nameplate img', x: 86, y: 82, r: 9, color: '#5eead4' },
  { id: 'e1', label: 'pressure', x: 30, y: 36, r: 7, color: '#a78bfa' },
  { id: 'e2', label: 'thread', x: 30, y: 64, r: 7, color: '#a78bfa' },
  { id: 'e3', label: 'material', x: 70, y: 36, r: 7, color: '#a78bfa' },
  { id: 'e4', label: 'temp', x: 70, y: 64, r: 7, color: '#a78bfa' },
  { id: 'a1', label: 'physical', x: 36, y: 50, r: 6, color: '#fbbf24' },
  { id: 'a2', label: 'cross-src', x: 50, y: 30, r: 6, color: '#fbbf24' },
  { id: 'a3', label: 'disproof', x: 64, y: 50, r: 6, color: '#fbbf24' },
  { id: 'a4', label: 'conformal', x: 50, y: 70, r: 6, color: '#fbbf24' },
  { id: 'out', label: 'CERTIFIED', x: 85, y: 50, r: 11, color: '#34d399', pulse: true },
]

const EDGES: Edge[] = [
  { from: 's1', to: 'e1' },
  { from: 's1', to: 'e2' },
  { from: 's2', to: 'e2' },
  { from: 's2', to: 'e3' },
  { from: 's3', to: 'e3' },
  { from: 's4', to: 'e4' },
  { from: 's3', to: 'e4' },
  { from: 'e1', to: 'pn', color: 'rgba(34,211,238,0.5)' },
  { from: 'e2', to: 'pn', color: 'rgba(34,211,238,0.5)' },
  { from: 'e3', to: 'pn', color: 'rgba(34,211,238,0.5)' },
  { from: 'e4', to: 'pn', color: 'rgba(34,211,238,0.5)' },
  { from: 'e1', to: 'a1' },
  { from: 'e2', to: 'a1' },
  { from: 'e2', to: 'a2' },
  { from: 'e3', to: 'a3' },
  { from: 'e4', to: 'a4' },
  { from: 'a1', to: 'a2', color: 'rgba(251,191,36,0.5)' },
  { from: 'a1', to: 'a3', color: 'rgba(251,191,36,0.5)' },
  { from: 'a2', to: 'a4', color: 'rgba(251,191,36,0.5)' },
  { from: 'a3', to: 'a4', color: 'rgba(251,191,36,0.5)' },
  { from: 'a4', to: 'out', flow: true, color: 'rgba(52,211,153,0.7)' },
  { from: 'pn', to: 'out', color: 'rgba(34,211,238,0.35)' },
]

function getNode(id: string): Node | undefined {
  return NODES.find((n) => n.id === id)
}

function buildPath(a: Node, b: Node): string {
  const dx = b.x - a.x
  const dy = b.y - a.y
  const cx = (a.x + b.x) / 2 - dy * 0.18
  const cy = (a.y + b.y) / 2 + dx * 0.18
  return `M ${a.x} ${a.y} Q ${cx} ${cy} ${b.x} ${b.y}`
}

export default function IntelligenceGraph() {

  return (
    <div className="relative h-full w-full">
      <svg viewBox="0 0 100 100" className="h-full w-full" preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="0.6" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="pnGrad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.5" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
          </radialGradient>
        </defs>

        {EDGES.map((edge, i) => {
          const a = getNode(edge.from)
          const b = getNode(edge.to)
          if (!a || !b) return null
          const d = buildPath(a, b)
          return (
            <g key={`e-${i}`}>
              <path
                d={d}
                fill="none"
                stroke={edge.color ?? 'rgba(148,163,184,0.14)'}
                strokeWidth={0.35}
              />
              {edge.flow && (
                <circle r="1.1" filter="url(#glow)">
                  <animateMotion dur="3.2s" repeatCount="indefinite" path={d} />
                  <animate attributeName="fill" values="#22d3ee;#a78bfa;#34d399" dur="3.2s" repeatCount="indefinite" />
                </circle>
              )}
            </g>
          )
        })}

        {NODES.map((n) => (
          <g key={n.id} filter="url(#glow)">
            {n.pulse && (
              <motion.circle
                cx={n.x}
                cy={n.y}
                r={n.r * 2.4}
                fill={n.color}
                opacity={0.12}
                animate={{ r: [n.r * 2, n.r * 3.2, n.r * 2], opacity: [0.16, 0, 0.16] }}
                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              />
            )}
            <circle cx={n.x} cy={n.y} r={n.r} fill={n.color} opacity={0.92} />
            <circle cx={n.x} cy={n.y} r={n.r} fill="none" stroke={n.color} strokeWidth={0.3} opacity={0.5} />
            <text
              x={n.x}
              y={n.y + n.r + 3.4}
              textAnchor="middle"
              fill="rgba(226,232,240,0.78)"
              fontSize={n.id === 'pn' || n.id === 'out' ? 2.4 : 1.7}
              fontFamily="JetBrains Mono, monospace"
              fontWeight={n.id === 'pn' ? 700 : 500}
            >
              {n.label}
            </text>
          </g>
        ))}

        <circle r="2.2" filter="url(#glow)">
          <animateMotion dur="18s" repeatCount="indefinite" path="M 30 36 Q 40 30 50 50 Q 60 70 70 64" />
          <animate attributeName="fill" values="#22d3ee;#a78bfa;#34d399;#22d3ee" dur="18s" repeatCount="indefinite" />
        </circle>
      </svg>

      <div className="pointer-events-none absolute right-3 top-3 flex items-center gap-2 rounded-full border border-white/[0.08] bg-ink/70 px-3 py-1 backdrop-blur-md">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
        </span>
        <span className="font-mono text-[10px] tracking-wide text-slate-300">LIVE GRAPH</span>
      </div>
    </div>
  )
}