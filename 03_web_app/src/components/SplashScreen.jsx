import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import BrandMark from './BrandMark.jsx'
import AksaraDriftBackdrop from './AksaraDriftBackdrop.jsx'
import { EASE_OUT, RingText } from './MotionPrimitives.jsx'

const SPLASH_TITLE = 'PUSTAHA TOBA'

/**
 * Splash Screen tirai Ulos murni tanpa kotak tengah dan tanpa tombol:
 * menggabungkan animasi huruf Zip 1 (Letters + RingText), tirai Ulos terbelah,
 * gambar jalur SVG BrandMark, dan lapisan 25 aksara berjalan.
 */
export default function SplashScreen({ onComplete }) {
  const [isOpening, setIsOpening] = useState(false)
  const onCompleteRef = useRef(onComplete)
  const finishTimerRef = useRef(null)

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  useEffect(() => {
    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

    if (prefersReduced) {
      onCompleteRef.current()
      return undefined
    }

    const openTimer = setTimeout(() => {
      setIsOpening(true)
      finishTimerRef.current = setTimeout(() => {
        onCompleteRef.current()
      }, 720)
    }, 1550)

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        clearTimeout(openTimer)
        if (finishTimerRef.current) return
        setIsOpening(true)
        finishTimerRef.current = setTimeout(() => {
          onCompleteRef.current()
        }, 520)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      clearTimeout(openTimer)
      if (finishTimerRef.current) clearTimeout(finishTimerRef.current)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  return (
    <div
      className={`curtain-splash-root ${isOpening ? 'is-opening' : ''}`}
      role="status"
      aria-live="polite"
      aria-label="Memuat aplikasi Pustaha Toba"
    >
      {/* Tirai Kiri Ulos */}
      <motion.div
        className="ulos-curtain is-left"
        initial={{ x: '0%' }}
        animate={{ x: isOpening ? '-102%' : '0%' }}
        transition={{ duration: 0.72, ease: EASE_OUT }}
      />

      {/* Tirai Kanan Ulos */}
      <motion.div
        className="ulos-curtain is-right"
        initial={{ x: '0%' }}
        animate={{ x: isOpening ? '102%' : '0%' }}
        transition={{ duration: 0.72, ease: EASE_OUT }}
      />

      {/* Lapisan 25 Aksara Mengalir */}
      <motion.div
        className="curtain-drift-layer"
        animate={{ opacity: isOpening ? 0 : 1 }}
        transition={{ duration: 0.3 }}
      >
        <AksaraDriftBackdrop variant="splash" />
      </motion.div>

      {/* Komposisi Animasi Tengah Tanpa Kotak & Tanpa Tombol */}
      <motion.div
        className="splash-borderless-stage"
        animate={isOpening ? { opacity: 0, scale: 1.06 } : { opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: EASE_OUT }}
      >
        <div className="splash-seal-wrap">
          <RingText
            text="AKSARA BATAK TOBA · TRANSLITERASI LATIN · "
            className="splash-ring-svg"
          />
          <BrandMark size={64} draw={true} className="splash-center-emblem" />
        </div>

        <h1 className="splash-kinetic-title" aria-label="Pustaha Toba">
          {SPLASH_TITLE.split('').map((char, idx) => (
            <span key={idx} className="splash-letter-clip" aria-hidden="true">
              <motion.span
                className="splash-letter-span"
                initial={{ y: '115%', rotate: 6, opacity: 0 }}
                animate={{ y: '0%', rotate: 0, opacity: 1 }}
                transition={{
                  duration: 0.72,
                  ease: EASE_OUT,
                  delay: 0.08 + idx * 0.04,
                }}
              >
                {char === ' ' ? '\u00A0' : char}
              </motion.span>
            </span>
          ))}
        </h1>

        <motion.p
          className="splash-kinetic-sub"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.52, ease: EASE_OUT }}
        >
          Transliterasi Aksara Batak Toba ke Kalimat Huruf Latin
        </motion.p>
      </motion.div>
    </div>
  )
}
