import type { ReactNode } from 'react'

export function Kpi({
  label,
  value,
  sub,
  tone = 'default',
}: {
  label: string
  value: ReactNode
  sub?: ReactNode
  tone?: 'default' | 'accent' | 'ok' | 'warn' | 'danger'
}) {
  const tones = {
    default: 'text-slate-100',
    accent: 'text-cyan-300',
    ok: 'text-emerald-300',
    warn: 'text-amber-300',
    danger: 'text-rose-300',
  }
  const accentLine: Record<string, string> = {
    default: 'rgba(255,255,255,0.22)',
    accent: 'var(--accent, #22d3ee)',
    ok: '#34d399',
    warn: '#fbbf24',
    danger: '#fb7185',
  }
  return (
    <div className="panel relative overflow-hidden px-4 py-3">
      <span
        className="pointer-events-none absolute inset-x-0 top-0 h-[2px]"
        style={{
          background: `linear-gradient(90deg, ${accentLine[tone]}, transparent 85%)`,
          opacity: tone === 'default' ? 0.55 : 0.95,
        }}
      />
      <div className="label-caps">{label}</div>
      <div className={`mt-1.5 flex items-center justify-between gap-2 text-[15px] ${tones[tone]}`}>{value}</div>
      {sub ? <div className="mt-1.5 text-[11.5px] text-slate-400">{sub}</div> : null}
    </div>
  )
}

export function ProgressBar({
  pct,
  segments,
  className = '',
}: {
  pct?: number
  segments?: Array<{ w: number; color: string }>
  className?: string
}) {
  return (
    <div className={`h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06] ${className}`}>
      {pct != null ? (
        <div className="h-full rounded-full bg-accent-strong transition-all duration-500" style={{ width: `${pct}%` }} />
      ) : (
        <div className="flex h-full">
          {segments?.map((s, i) => (
            <div key={i} className="h-full" style={{ width: `${s.w}%`, background: s.color }} />
          ))}
        </div>
      )}
    </div>
  )
}

export function Ring({ pct, size = 32, color }: { pct: number; size?: number; color?: string }) {
  const r = (size - 6) / 2
  const c = 2 * Math.PI * r
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="shrink-0 -rotate-90">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={3.5} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color ?? 'var(--accent, #22d3ee)'}
        strokeWidth={3.5}
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - Math.min(1, Math.max(0, pct)))}
        style={{ transition: 'stroke-dashoffset 500ms ease' }}
      />
    </svg>
  )
}

export function Badge({
  children,
  tone = 'slate',
}: {
  children: ReactNode
  tone?: 'slate' | 'cyan' | 'emerald' | 'amber' | 'rose' | 'violet'
}) {
  const tones = {
    slate: 'border-white/10 bg-white/[0.04] text-slate-400',
    cyan: 'border-cyan-400/30 bg-cyan-400/10 text-cyan-300',
    emerald: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300',
    amber: 'border-amber-400/30 bg-amber-400/10 text-amber-300',
    rose: 'border-rose-400/30 bg-rose-400/10 text-rose-300',
    violet: 'border-violet-400/30 bg-violet-400/10 text-violet-300',
  }
  return (
    <span
      className={`mono inline-flex items-center gap-1 rounded border px-1.5 py-0.5 font-medium ${tones[tone]}`}
      style={{ fontSize: 11.5 }}
    >
      {children}
    </span>
  )
}

export function StatusDot({
  tone,
}: {
  tone: 'ok' | 'warn' | 'danger' | 'idle' | 'live' | 'accent'
}) {
  const map = {
    ok: 'bg-emerald-400',
    warn: 'bg-amber-400',
    danger: 'bg-rose-400',
    idle: 'bg-slate-500',
    live: 'bg-cyan-400 dot-live',
    accent: 'bg-cyan-400',
  }
  return <span className={`inline-block h-1.5 w-1.5 rounded-full ${map[tone]}`} />
}

export function SectionTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <h2 className="flex items-center gap-2 text-[13.5px] font-semibold tracking-wide text-slate-100">
        {children}
      </h2>
      {right}
    </div>
  )
}