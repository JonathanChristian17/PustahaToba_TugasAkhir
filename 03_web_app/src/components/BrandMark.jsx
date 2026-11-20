import { motion } from 'motion/react'
import { EASE_OUT } from './MotionPrimitives.jsx'

/**
 * Logo terpadu Pustaha Toba: siluet lipatan naskah pustaha laklak yang terbuka,
 * bingkai belah ketupat motif tenun ulos di tengah, serta garis pembacaan Latin.
 */
export default function BrandMark({ size = 24, draw = false, className = '' }) {
  if (draw) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        className={className}
        aria-hidden="true"
      >
        {/* Sampul naskah pustaha terbuka */}
        <motion.path
          d="M8 17C16 14 25 15 32 20C39 15 48 14 56 17V49C48 46 39 47 32 52C25 47 16 46 8 49V17Z"
          stroke="currentColor"
          strokeWidth="2.8"
          strokeLinejoin="round"
          initial={{ pathLength: 0, opacity: 0.4 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.85, ease: EASE_OUT }}
        />
        {/* Tulang tengah naskah */}
        <motion.path
          d="M32 20V52"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.45, delay: 0.25, ease: EASE_OUT }}
        />
        {/* Belah ketupat motif ulos & garis baca */}
        <motion.path
          d="M32 25L41 34L32 43L23 34Z"
          stroke="#F2B45A"
          strokeWidth="2.6"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.65, delay: 0.35, ease: EASE_OUT }}
        />
        <motion.path
          d="M14 28H20M14 35H19M44 28H50M45 35H50"
          stroke="#F2B45A"
          strokeWidth="2.2"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 0.5, delay: 0.5, ease: EASE_OUT }}
        />
      </svg>
    )
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M8 17C16 14 25 15 32 20C39 15 48 14 56 17V49C48 46 39 47 32 52C25 47 16 46 8 49V17Z"
        stroke="currentColor"
        strokeWidth="3.2"
        strokeLinejoin="round"
      />
      <path d="M32 20V52" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M32 25L41 34L32 43L23 34Z" stroke="var(--accent)" strokeWidth="2.8" strokeLinejoin="round" />
      <path d="M14 29H20M44 29H50" stroke="var(--accent)" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  )
}
