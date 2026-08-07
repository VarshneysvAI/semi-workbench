import { motion } from 'framer-motion'

export default function Aurora() {
  return (
    <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div className="grain absolute inset-0 opacity-[0.035]" />
      <motion.div
        className="absolute -left-32 -top-32 h-[520px] w-[520px] rounded-full opacity-50 blur-[120px]"
        style={{ background: 'radial-gradient(circle, #22d3ee 0%, transparent 70%)' }}
        animate={{ x: [0, 60, 0], y: [0, 40, 0], scale: [1, 1.08, 1] }}
        transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute -right-40 top-1/3 h-[520px] w-[520px] rounded-full opacity-40 blur-[130px]"
        style={{ background: 'radial-gradient(circle, #a78bfa 0%, transparent 70%)' }}
        animate={{ x: [0, -50, 0], y: [0, 60, 0], scale: [1, 1.1, 1] }}
        transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="absolute -bottom-40 left-1/3 h-[460px] w-[460px] rounded-full opacity-30 blur-[120px]"
        style={{ background: 'radial-gradient(circle, #34d399 0%, transparent 70%)' }}
        animate={{ x: [0, 40, 0], y: [0, -40, 0] }}
        transition={{ duration: 26, repeat: Infinity, ease: 'easeInOut' }}
      />
      <div className="absolute inset-0 bg-[linear-gradient(to_bottom,transparent_0%,rgba(4,6,10,0.5)_92%,#04060a_100%)]" />
    </div>
  )
}