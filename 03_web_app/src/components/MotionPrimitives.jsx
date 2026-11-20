import { useEffect, useId, useRef, useState } from 'react'
import { motion, useMotionValue, useReducedMotion, useSpring } from 'motion/react'

export const EASE_OUT = [0.16, 1, 0.3, 1]

/**
 * Animasi judul bertahap dari balik batas kotak (pola RiseLines Zip 1).
 */
export function RiseLines({ lines, className = '', delay = 0 }) {
  const reduce = useReducedMotion()

  if (reduce) {
    return (
      <span className={className}>
        {lines.map((line, i) => (
          <span key={i} className="rise-line-block">
            {line}
          </span>
        ))}
      </span>
    )
  }

  return (
    <span className={className}>
      {lines.map((line, index) => (
        <span key={index} className="rise-line-clip">
          <motion.span
            className="rise-line-block"
            initial={{ y: '105%', rotate: 1.5, opacity: 0 }}
            animate={{ y: '0%', rotate: 0, opacity: 1 }}
            transition={{
              duration: 0.78,
              ease: EASE_OUT,
              delay: delay + index * 0.09,
            }}
          >
            {line}
          </motion.span>
        </span>
      ))}
    </span>
  )
}

/**
 * Sapuan kuas penuh di belakang frasa kunci agar menutupi seluruh tinggi huruf.
 */
export function BrushHighlight({ children, delay = 0.25 }) {
  const reduce = useReducedMotion()
  return (
    <span className="brush-wrap">
      <motion.span
        aria-hidden="true"
        className="brush-stroke"
        initial={reduce ? { scaleX: 1 } : { scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.85, ease: EASE_OUT, delay }}
      />
      <span className="brush-text">{children}</span>
    </span>
  )
}

/**
 * Teks segel melingkar berputar halus (diadaptasi dari RingText Zip 1 Hero.tsx).
 */
export function RingText({ text, className = '' }) {
  const ringId = useId()
  return (
    <svg viewBox="0 0 120 120" className={className} aria-hidden="true">
      <defs>
        <path id={ringId} d="M60 60 m-46 0 a46 46 0 1 1 92 0 a46 46 0 1 1 -92 0" />
      </defs>
      <g className="pt-spin-slow">
        <text fontSize="8.8" letterSpacing="0.9" fill="currentColor" fontFamily="DM Mono, monospace">
          <textPath href={`#${ringId}`} textLength="282" lengthAdjust="spacing">
            {text}
          </textPath>
        </text>
      </g>
    </svg>
  )
}

/**
 * Cincin metrik animasi SVG untuk Mode Penelitian (kombinasi Zip 1 Day.tsx + Zip 2 StatCell).
 */
export function MetricArc({ percent, label }) {
  const reduce = useReducedMotion()
  const r = 24
  const circumference = 2 * Math.PI * r
  const offset = circumference * (1 - Math.min(100, Math.max(0, percent)) / 100)

  return (
    <svg viewBox="0 0 64 64" className="metric-arc-svg" aria-label={label}>
      <circle
        cx="32"
        cy="32"
        r={r}
        fill="none"
        stroke="currentColor"
        strokeOpacity="0.18"
        strokeWidth="4.5"
      />
      <motion.circle
        cx="32"
        cy="32"
        r={r}
        fill="none"
        stroke="#F2B45A"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeDasharray={circumference}
        initial={reduce ? { strokeDashoffset: offset } : { strokeDashoffset: circumference }}
        animate={{ strokeDashoffset: offset }}
        transition={{ duration: 0.9, ease: EASE_OUT }}
        transform="rotate(-90 32 32)"
      />
    </svg>
  )
}

/**
 * Kemunculan kartu saat memasuki viewport (pola FadeUp Zip 1).
 */
export function FadeUp({ children, delay = 0, className = '' }) {
  const reduce = useReducedMotion()
  if (reduce) {
    return <div className={className}>{children}</div>
  }
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: 0.65, ease: EASE_OUT, delay }}
    >
      {children}
    </motion.div>
  )
}

/**
 * Tarikan spring halus mengikuti kursor (pola Magnetic Zip 1).
 */
export function MagneticWrap({ children, strength = 0.24, className = '' }) {
  const reduce = useReducedMotion()
  const springCfg = { stiffness: 220, damping: 18, mass: 0.5 }
  const x = useSpring(useMotionValue(0), springCfg)
  const y = useSpring(useMotionValue(0), springCfg)

  const handleMove = (e) => {
    if (reduce || e.pointerType !== 'mouse') return
    const rect = e.currentTarget.getBoundingClientRect()
    x.set((e.clientX - rect.left - rect.width / 2) * strength)
    y.set((e.clientY - rect.top - rect.height / 2) * strength)
  }

  const handleLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      className={`magnetic-wrap ${className}`}
      style={reduce ? undefined : { x, y }}
      onPointerMove={handleMove}
      onPointerLeave={handleLeave}
    >
      {children}
    </motion.div>
  )
}

/**
 * Memunculkan kalimat Latin kata demi kata dari blur ke tajam (pola ows-rise-in Zip 3).
 */
export function WordReveal({ text, className = '', as = 'p' }) {
  const reduce = useReducedMotion()
  const words = String(text || '').split(/\s+/).filter(Boolean)
  const Tag = as

  if (reduce || words.length === 0) {
    return <Tag className={className}>{text}</Tag>
  }

  return (
    <Tag className={className} aria-label={text}>
      {words.map((word, idx) => (
        <motion.span
          key={`${word}-${idx}`}
          className="word-reveal-item"
          initial={{ opacity: 0, y: 8, filter: 'blur(5px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{
            duration: 0.4,
            ease: EASE_OUT,
            delay: Math.min(idx * 0.06, 0.45),
          }}
        >
          {word}
          {idx < words.length - 1 ? '\u00A0' : ''}
        </motion.span>
      ))}
    </Tag>
  )
}

/**
 * Hook animasi hitungan angka halus (pola useTween Zip 2).
 */
export function useTweenNumber(target, duration = 750) {
  const reduce = useReducedMotion()
  const [val, setVal] = useState(reduce ? target : 0)

  useEffect(() => {
    if (reduce) {
      setVal(target)
      return undefined
    }
    let raf = 0
    const start = performance.now()
    const step = (now) => {
      const t = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - t, 3)
      setVal(target * eased)
      if (t < 1) {
        raf = requestAnimationFrame(step)
      }
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target, duration, reduce])

  return val
}

/**
 * Gelombang garis SVG interaktif di bawah Hero (diadaptasi dari TideLine Zip 1).
 */
export function InteractiveWaveLine({ darkBg = false, fillBottom = false }) {
  const svgRef = useRef(null)
  const frontRef = useRef(null)
  const backRef = useRef(null)
  const fillRef = useRef(null)
  const reduce = useReducedMotion()

  useEffect(() => {
    const svg = svgRef.current
    const section = svg?.parentElement
    if (!svg || !section) return undefined

    let width = Math.max(600, section.clientWidth || 1000)
    let time = 0
    let cursorX = width * 0.5
    let targetX = cursorX
    let energy = 0
    let targetEnergy = 0
    let raf = 0
    let last = performance.now()

    const onResize = () => {
      width = Math.max(600, section.clientWidth || 1000)
      svg.setAttribute('viewBox', `0 0 ${width} 76`)
    }
    onResize()

    const onMove = (e) => {
      if (reduce) return
      const rect = section.getBoundingClientRect()
      targetX = e.clientX - rect.left
      targetEnergy = 1
    }
    const onLeave = () => {
      targetEnergy = 0
    }

    const buildPath = (phase, amp, baseY) => {
      const step = 18
      let d = ''
      for (let x = 0; x <= width + step; x += step) {
        const dist = Math.abs(x - cursorX)
        const bump = energy * Math.exp(-(dist * dist) / (2 * 110 * 110)) * 12
        const y = baseY + Math.sin(x * 0.014 + time * 1.4 + phase) * amp - bump
        d += `${x === 0 ? 'M' : 'L'}${x} ${y.toFixed(1)}`
      }
      return d
    }

    const tick = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      if (!reduce) time += dt
      cursorX += (targetX - cursorX) * 0.09
      energy += (targetEnergy - energy) * 0.06
      targetEnergy *= 0.985

      const frontD = buildPath(0, 5.5, 48)
      frontRef.current?.setAttribute('d', frontD)
      if (fillBottom && fillRef.current) {
        fillRef.current.setAttribute('d', `${frontD} L${width + 20} 82 L0 82 Z`)
      }
      backRef.current?.setAttribute('d', buildPath(1.9, 4, 34))

      if (!reduce) {
        raf = requestAnimationFrame(tick)
      }
    }

    tick(performance.now())
    window.addEventListener('resize', onResize)
    section.addEventListener('pointermove', onMove)
    section.addEventListener('pointerleave', onLeave)
    return () => {
      if (raf) cancelAnimationFrame(raf)
      window.removeEventListener('resize', onResize)
      section.removeEventListener('pointermove', onMove)
      section.removeEventListener('pointerleave', onLeave)
    }
  }, [reduce, fillBottom])

  return (
    <svg ref={svgRef} className="hero-wave-svg" preserveAspectRatio="none" aria-hidden="true">
      {fillBottom && <path ref={fillRef} className="hero-wave-fill" fill="var(--bg-page)" />}
      <path
        ref={backRef}
        fill="none"
        stroke={darkBg ? '#FAF6EE' : 'var(--primary)'}
        strokeOpacity={darkBg ? '0.28' : '0.25'}
        strokeWidth="1.4"
      />
      <path
        ref={frontRef}
        fill="none"
        stroke={darkBg ? '#F2B45A' : 'var(--accent)'}
        strokeOpacity="0.88"
        strokeWidth="1.9"
      />
    </svg>
  )
}
