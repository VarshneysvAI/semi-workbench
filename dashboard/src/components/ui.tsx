import { type ReactNode } from 'react'
import { cn } from '../lib/cn'

export function Panel({ className = '', children }: { className?: string; children: ReactNode }) {
  return (
    <div
      className={cn(
        'rounded-2xl border border-white/[0.07] bg-white/[0.02] shadow-panel backdrop-blur-sm',
        className,
      )}
    >
      {children}
    </div>
  )
}

export function SectionTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500', className)}>
      {children}
    </div>
  )
}

export type Tone = 'emerald' | 'violet' | 'amber' | 'rose' | 'slate' | 'cyan'

const TONE_MAPS: Record<Tone, { text: string; dot: string; border?: string }> = {
  emerald: { text: 'text-emerald-300', dot: 'bg-emerald-400' },
  violet: { text: 'text-violet-300', dot: 'bg-violet-400' },
  amber: { text: 'text-amber-300', dot: 'bg-amber-400' },
  rose: { text: 'text-rose-300', dot: 'bg-rose-400' },
  slate: { text: 'text-slate-300', dot: 'bg-slate-400' },
  cyan: { text: 'text-cyan-300', dot: 'bg-cyan-400' },
}

export function StatusPill({
  label,
  tone = 'slate',
  pulse = false,
  className = '',
}: {
  label: string
  tone?: Tone
  pulse?: boolean
  className?: string
}) {
  const t = TONE_MAPS[tone]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] px-2.5 py-1 text-[11px] font-medium tracking-wide',
        t.text,
        className,
      )}
    >
      <span className="relative flex h-1.5 w-1.5">
        {pulse && <span className={cn('absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping', t.dot)} />}
        <span className={cn('relative inline-flex h-1.5 w-1.5 rounded-full', t.dot)} />
      </span>
      {label}
    </span>
  )
}

export function Sparkline({ data, className = '' }: { data: number[]; className?: string }) {
  const w = 120
  const h = 32
  const max = Math.max(...data)
  const min = Math.min(...data)
  const span = max - min || 1
  const pts = data
    .map((d, i) => {
      const x = (i / (data.length - 1 || 1)) * w
      const y = h - 3 - ((h - 6) * (d - min)) / span
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
  const id = `sp-${data.join('')}`
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={cn('h-8 w-full', className)} preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(45,212,191,0.35)" />
          <stop offset="100%" stopColor="rgba(45,212,191,0)" />
        </linearGradient>
      </defs>
      <polygon points={`0,${h} ${pts} ${w},${h}`} fill={`url(#${id})`} />
      <polyline
        points={pts}
        fill="none"
        stroke="rgba(45,212,191,0.9)"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function ProgressRing({ value, size = 68, tone = '#2dd4bf' }: { value: number; size?: number; tone?: string }) {
  const r = (size - 8) / 2
  const c = 2 * Math.PI * r
  const offset = c * (1 - Math.min(Math.max(value, 0), 1))
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="5" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={tone}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 900ms cubic-bezier(.4,0,.2,1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-mono font-num text-sm font-semibold text-slate-100">
        {Math.round(value * 100)}%
      </div>
    </div>
  )
}

export function Bars({ data, tone = '#2dd4bf' }: { data: number[]; tone?: string }) {
  const max = Math.max(...data) || 1
  return (
    <div className="flex h-12 items-end gap-1">
      {data.map((v, i) => (
        <div
          key={i}
          className="w-2 rounded-t-sm"
          style={{ height: `${(v / max) * 100}%`, background: tone, opacity: 0.35 + (i / data.length) * 0.65 }}
        />
      ))}
    </div>
  )
}