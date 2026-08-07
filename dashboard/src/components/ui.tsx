import { type ReactNode, useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../lib/cn'

export function GlassCard({
  children,
  className = '',
  glow = false,
  delay = 0,
}: {
  children: ReactNode
  className?: string
  glow?: boolean
  delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        'glass relative overflow-hidden',
        glow && 'shadow-glow',
        className,
      )}
    >
      <div className="absolute inset-x-0 top-px h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      {children}
    </motion.div>
  )
}

export function SectionTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500', className)}>
      {children}
    </div>
  )
}

export type Tone = 'emerald' | 'violet' | 'amber' | 'rose' | 'slate' | 'cyan' | 'teal'

const TONE_MAPS: Record<Tone, { text: string; dot: string; bg: string; border: string }> = {
  emerald: { text: 'text-emerald-300', dot: 'bg-emerald-400', bg: 'bg-emerald-400/10', border: 'border-emerald-400/20' },
  teal: { text: 'text-teal-300', dot: 'bg-teal-400', bg: 'bg-teal-400/10', border: 'border-teal-400/20' },
  violet: { text: 'text-violet-300', dot: 'bg-violet-400', bg: 'bg-violet-400/10', border: 'border-violet-400/20' },
  amber: { text: 'text-amber-300', dot: 'bg-amber-400', bg: 'bg-amber-400/10', border: 'border-amber-400/20' },
  rose: { text: 'text-rose-300', dot: 'bg-rose-400', bg: 'bg-rose-400/10', border: 'border-rose-400/20' },
  slate: { text: 'text-slate-300', dot: 'bg-slate-400', bg: 'bg-slate-400/10', border: 'border-slate-400/20' },
  cyan: { text: 'text-cyan-300', dot: 'bg-cyan-400', bg: 'bg-cyan-400/10', border: 'border-cyan-400/20' },
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
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide',
        t.text,
        t.bg,
        t.border,
        className,
      )}
    >
      <span className="relative flex h-1.5 w-1.5">
        {pulse && <span className={cn('absolute inline-flex h-full w-full animate-ping rounded-full opacity-75', t.dot)} />}
        <span className={cn('relative inline-flex h-1.5 w-1.5 rounded-full', t.dot)} />
      </span>
      {label}
    </span>
  )
}

export function CountUp({ target, decimals = 0, suffix = '' }: { target: number; decimals?: number; suffix?: string }) {
  const [val, setVal] = useState(0)
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return
        const start = performance.now()
        const dur = 1400
        const from = 0
        const step = (now: number) => {
          const t = Math.min(1, (now - start) / dur)
          const ease = 1 - Math.pow(1 - t, 3)
          setVal(from + (target - from) * ease)
          if (t < 1) requestAnimationFrame(step)
        }
        requestAnimationFrame(step)
        io.disconnect()
      },
      { threshold: 0.3 },
    )
    if (ref.current) io.observe(ref.current)
    return () => io.disconnect()
  }, [target])

  return (
    <span ref={ref} className="font-num">
      {val.toFixed(decimals)}
      {suffix}
    </span>
  )
}

export function RingGauge({ value, size = 72, color = '#22d3ee', label }: { value: number; size?: number; color?: string; label?: string }) {
  const r = (size - 8) / 2
  const c = 2 * Math.PI * r
  const offset = c * (1 - Math.min(Math.max(value, 0), 1))
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-sm font-bold text-slate-100 font-num">{Math.round(value * 100)}</span>
        {label && <span className="text-[8px] uppercase tracking-wider text-slate-500">{label}</span>}
      </div>
    </div>
  )
}

export function Sparkline({ data, className = '', color = '#22d3ee' }: { data: number[]; className?: string; color?: string }) {
  const w = 160
  const h = 40
  const max = Math.max(...data)
  const min = Math.min(...data)
  const span = max - min || 1
  const pts = data.map((d, i) => `${(i / (data.length - 1)) * w},${h - 3 - ((h - 6) * (d - min)) / span}`).join(' ')
  const id = `sp-${data.join('').replace(/[^0-9]/g, '')}`
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={cn('h-10 w-full', className)} preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.polygon
        points={`0,${h} ${pts} ${w},${h}`}
        fill={`url(#${id})`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
      />
      <motion.polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1, ease: 'easeInOut' }}
      />
    </svg>
  )
}

export function BarList({ items }: { items: Array<{ label: string; value: number; tone?: Tone }> }) {
  const max = Math.max(...items.map((i) => i.value)) || 1
  return (
    <div className="space-y-3">
      {items.map((it) => {
        const tone = TONE_MAPS[it.tone ?? 'teal']
        return (
          <div key={it.label}>
            <div className="mb-1.5 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">{it.label}</span>
              <span className="font-mono font-num font-semibold text-slate-300">{it.value}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.05]">
              <motion.div
                className={cn('h-full rounded-full', tone.bg)}
                initial={{ width: 0 }}
                animate={{ width: `${(it.value / max) * 100}%` }}
                transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
                style={{ boxShadow: `0 0 12px -2px ${tone.dot.includes('emerald') ? '#34d399' : tone.dot.includes('violet') ? '#a78bfa' : '#22d3ee'}` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function PanelHeader({ title, subtitle, right }: { title: string; subtitle?: string; right?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-white/[0.06] px-5 py-4">
      <div>
        <h3 className="text-[14px] font-semibold text-slate-100">{title}</h3>
        {subtitle && <p className="mt-0.5 text-[11px] text-slate-500">{subtitle}</p>}
      </div>
      {right}
    </div>
  )
}