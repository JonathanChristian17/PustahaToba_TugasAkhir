import { Fragment, useEffect, useRef } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { ANAK_NI_SURAT, INA_NI_SURAT } from '../data/aksaraCatalog.js'
import { EASE_OUT } from './MotionPrimitives.jsx'

const ALL_25_GLYPH_SRCS = [...INA_NI_SURAT, ...ANAK_NI_SURAT].map((g) => g.src)
let cachedGlyphImagesPromise = null

function loadAll25GlyphImages() {
  if (cachedGlyphImagesPromise) return cachedGlyphImagesPromise
  cachedGlyphImagesPromise = Promise.allSettled(
    ALL_25_GLYPH_SRCS.map(
      (src) =>
        new Promise((resolve, reject) => {
          const img = new Image()
          img.crossOrigin = 'anonymous'
          img.onload = () => {
            if (img.naturalWidth > 0 && img.naturalHeight > 0) resolve(img)
            else reject(new Error('empty image'))
          }
          img.onerror = () => reject(new Error(`failed ${src}`))
          img.src = src
        }),
    ),
  ).then((results) =>
    results.filter((r) => r.status === 'fulfilled' && r.value).map((r) => r.value),
  )
  return cachedGlyphImagesPromise
}

/**
 * Mengubah PNG aksara (latar putih, tinta hitam) menjadi sprite kanvas kuning #F2B45A
 * berlatar belakang transparan penuh, dengan bounding-box crop proporsional.
 */
function makeYellowGlyphSprite(img, cell, dpr) {
  const iw = img.naturalWidth
  const ih = img.naturalHeight
  if (!iw || !ih) return null

  const tmp = document.createElement('canvas')
  tmp.width = iw
  tmp.height = ih
  const tctx = tmp.getContext('2d')
  if (!tctx) return null
  tctx.drawImage(img, 0, 0)

  let imgData
  try {
    imgData = tctx.getImageData(0, 0, iw, ih)
  } catch {
    return null
  }

  const d = imgData.data
  let minX = iw
  let minY = ih
  let maxX = -1
  let maxY = -1

  for (let y = 0; y < ih; y += 1) {
    for (let x = 0; x < iw; x += 1) {
      const idx = (y * iw + x) * 4
      const lum = 0.299 * d[idx] + 0.587 * d[idx + 1] + 0.114 * d[idx + 2]
      if (lum >= 225) {
        d[idx + 3] = 0
      } else {
        const strength = Math.max(0, Math.min(1, (225 - lum) / 150))
        d[idx] = 242
        d[idx + 1] = 180
        d[idx + 2] = 90
        d[idx + 3] = Math.round(strength * 255)
        if (x < minX) minX = x
        if (x > maxX) maxX = x
        if (y < minY) minY = y
        if (y > maxY) maxY = y
      }
    }
  }

  if (maxX < minX || maxY < minY) return null
  tctx.putImageData(imgData, 0, 0)

  const bw = maxX - minX + 1
  const bh = maxY - minY + 1
  const px = Math.ceil(cell * dpr * 2)
  const out = document.createElement('canvas')
  out.width = px
  out.height = px
  const octx = out.getContext('2d')
  if (!octx) return null

  const innerSpan = px * 0.44
  const baseScale = innerSpan / Math.max(iw, ih)
  const cropScale = Math.min(innerSpan / Math.max(bw, bh), baseScale * 1.45)
  const dw = bw * cropScale
  const dh = bh * cropScale
  octx.drawImage(tmp, minX, minY, bw, bh, (px - dw) / 2, (px - dh) / 2, dw, dh)
  return out
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v))
}

function mulberry32(seed) {
  let a = seed >>> 0
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function shortestAngle(a) {
  let x = a
  while (x > Math.PI) x -= Math.PI * 2
  while (x < -Math.PI) x += Math.PI * 2
  return x
}

/**
 * Kisi 25 Aksara Batak Toba interaktif berwarna kuning transparan untuk header Halaman Riwayat.
 * Berputar dan membesar mengikuti kursor serta memancarkan riak konsentris saat diklik.
 */
export function InteractiveGlyphField({ className = '' }) {
  const wrapRef = useRef(null)
  const canvasRef = useRef(null)
  const reduce = useReducedMotion()

  useEffect(() => {
    const wrap = wrapRef.current
    const cv = canvasRef.current
    const host = wrap?.parentElement
    if (!wrap || !cv || !host) return undefined
    const ctx = cv.getContext('2d')
    if (!ctx) return undefined

    let mounted = true
    const cell = 44
    const half = cell / 2
    let W = 0
    let H = 0
    let dpr = 1
    let n = 0
    let xs = new Float32Array(0)
    let ys = new Float32Array(0)
    let wGold = new Float32Array(0)
    let kinds = new Uint8Array(0)
    let grain = new Float32Array(0)
    let ang = new Float32Array(0)
    let scl = new Float32Array(0)
    let loadedImgs = []
    let glyphSprites = []
    const ptr = { x: 0, y: 0, on: false }
    const ripples = []
    let visible = true
    let raf = 0

    const fieldWeight = (nx, ny) => {
      // Kurangi kepadatan di area kolom teks kiri agar kontras baca judul putih tetap tinggi
      const dxText = (nx - 0.34) / 0.36
      const dyText = (ny - 0.48) / 0.38
      const dText = Math.sqrt(dxText * dxText + dyText * dyText)
      const part = clamp((dText - 0.56) / 0.72, 0.12, 1)
      const edgeBoost = 0.28 + 0.64 * clamp((nx - 0.38) / 0.62, 0, 1)
      const vEdge = 1 - 0.34 * Math.pow(Math.abs(ny - 0.5) * 2, 2.2)
      return clamp(part * edgeBoost * vEdge * 0.58, 0.08, 0.65)
    }

    const buildSprites = () => {
      if (!loadedImgs.length) return
      glyphSprites = loadedImgs
        .map((img) => makeYellowGlyphSprite(img, cell, dpr))
        .filter(Boolean)
    }

    const layout = () => {
      const r = wrap.getBoundingClientRect()
      W = Math.max(1, r.width)
      H = Math.max(1, r.height)
      dpr = Math.min(2, window.devicePixelRatio || 1)
      cv.width = Math.round(W * dpr)
      cv.height = Math.round(H * dpr)
      cv.style.width = `${W}px`
      cv.style.height = `${H}px`

      const cols = Math.max(1, Math.floor((W - 32) / cell))
      const rows = Math.max(1, Math.floor((H - 28) / cell))
      n = cols * rows
      xs = new Float32Array(n)
      ys = new Float32Array(n)
      wGold = new Float32Array(n)
      kinds = new Uint8Array(n)
      grain = new Float32Array(n)
      ang = new Float32Array(n)
      scl = new Float32Array(n).fill(1)

      const ox = (W - (cols - 1) * cell) / 2
      const oy = (H - (rows - 1) * cell) / 2
      const rand = mulberry32(cols * 977 + rows)
      const spriteCount = Math.max(1, glyphSprites.length || ALL_25_GLYPH_SRCS.length)
      for (let j = 0, k = 0; j < rows; j += 1) {
        for (let i = 0; i < cols; i += 1, k += 1) {
          const x = ox + i * cell
          const y = oy + j * cell
          xs[k] = x
          ys[k] = y
          wGold[k] = fieldWeight(x / W, y / H)
          kinds[k] = (i * 7 + j * 11 + Math.floor(rand() * 5)) % spriteCount
          grain[k] = 0.6 + 0.4 * rand()
        }
      }
      buildSprites()
    }

    const drawFrame = (t) => {
      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.clearRect(0, 0, cv.width, cv.height)
      if (!glyphSprites.length) return

      const radius = 155
      const r2 = radius * radius
      const count = glyphSprites.length

      for (let q = ripples.length - 1; q >= 0; q -= 1) {
        if (t - ripples[q].t0 > 1500) ripples.splice(q, 1)
      }

      for (let i = 0; i < n; i += 1) {
        const g0 = wGold[i]
        if (g0 < 0.02) continue

        const x = xs[i]
        const y = ys[i]
        let tA = 0
        let tS = 1
        let boost = 0

        if (!reduce) {
          if (ptr.on) {
            const dx = x - ptr.x
            const dy = y - ptr.y
            const d2 = dx * dx + dy * dy
            if (d2 < r2) {
              let w = 1 - Math.sqrt(d2) / radius
              w = w * w * (3 - 2 * w)
              tA = shortestAngle(Math.atan2(dy, dx) + Math.PI / 4) * w * 0.30
              tS = 1 + 0.34 * w
              boost = 0.52 * w
            }
          }
          for (let q = 0; q < ripples.length; q += 1) {
            const rp = ripples[q]
            const age = t - rp.t0
            const dx = x - rp.x
            const dy = y - rp.y
            const dd = Math.abs(Math.sqrt(dx * dx + dy * dy) - age * 0.52)
            if (dd < 58) {
              const k = (1 - dd / 58) * (1 - age / 1500)
              tS += 0.38 * k
              boost += 0.48 * k
              tA += shortestAngle(Math.atan2(dy, dx) + Math.PI / 4) * k * 0.30
            }
          }
          ang[i] += (tA - ang[i]) * 0.14
          scl[i] += (tS - scl[i]) * 0.16
        }

        const shimmer = reduce ? 1 : 0.78 + 0.22 * Math.sin((x + y * 0.8) * 0.011 - t * 0.0011)
        const gr = grain[i] * shimmer
        const alGold = clamp(g0 * gr + boost, 0, 0.90)

        const a = ang[i]
        const s = scl[i]
        if (Math.abs(a) < 0.003 && Math.abs(s - 1) < 0.003) {
          ctx.setTransform(dpr, 0, 0, dpr, dpr * x, dpr * y)
        } else {
          const c = Math.cos(a) * s * dpr
          const sn = Math.sin(a) * s * dpr
          ctx.setTransform(c, sn, -sn, c, dpr * x, dpr * y)
        }

        const sprite = glyphSprites[kinds[i] % count]
        if (alGold > 0.015 && sprite) {
          ctx.globalAlpha = alGold
          ctx.drawImage(sprite, -half, -half, cell, cell)
        }
      }
      ctx.globalAlpha = 1
    }

    const loop = (t) => {
      raf = 0
      drawFrame(t)
      if (visible && !reduce) {
        raf = requestAnimationFrame(loop)
      }
    }

    const start = () => {
      if (!raf && visible && !reduce && glyphSprites.length) {
        raf = requestAnimationFrame(loop)
      }
    }

    const onPointerMove = (e) => {
      const r = wrap.getBoundingClientRect()
      ptr.x = e.clientX - r.left
      ptr.y = e.clientY - r.top
      ptr.on = true
    }

    const onPointerLeave = () => {
      ptr.on = false
    }

    const onPointerDown = (e) => {
      if (reduce) return
      if (e.target.closest('button, a, input, label')) return
      const r = wrap.getBoundingClientRect()
      ripples.push({ x: e.clientX - r.left, y: e.clientY - r.top, t0: performance.now() })
    }

    layout()
    loadAll25GlyphImages().then((imgs) => {
      if (!mounted) return
      loadedImgs = imgs
      buildSprites()
      drawFrame(performance.now())
      start()
    })

    const ro = typeof ResizeObserver !== 'undefined'
      ? new ResizeObserver(() => {
          layout()
          drawFrame(performance.now())
        })
      : null
    ro?.observe(wrap)

    const io = typeof IntersectionObserver !== 'undefined'
      ? new IntersectionObserver((entries) => {
          visible = entries[0]?.isIntersecting ?? true
          if (visible) {
            drawFrame(performance.now())
            start()
          } else if (raf) {
            cancelAnimationFrame(raf)
            raf = 0
          }
        })
      : null
    io?.observe(host)

    host.addEventListener('pointermove', onPointerMove)
    host.addEventListener('pointerleave', onPointerLeave)
    host.addEventListener('pointerdown', onPointerDown)

    return () => {
      mounted = false
      if (raf) cancelAnimationFrame(raf)
      ro?.disconnect()
      io?.disconnect()
      host.removeEventListener('pointermove', onPointerMove)
      host.removeEventListener('pointerleave', onPointerLeave)
      host.removeEventListener('pointerdown', onPointerDown)
    }
  }, [reduce])

  return (
    <div ref={wrapRef} className={`hero-canvas-layer ${className}`} aria-hidden="true">
      <canvas ref={canvasRef} />
    </div>
  )
}

/**
 * Kanopi serpihan goresan & daun Pustaha melayang dengan angin kursor (pola Canopy Zip 2).
 * Mengikuti tema Terang/Gelap secara otomatis via MutationObserver dan melepaskan serpihan saat klik.
 */
export function InteractiveScriptCanopy({ className = '' }) {
  const wrapRef = useRef(null)
  const canvasRef = useRef(null)
  const reduce = useReducedMotion()

  useEffect(() => {
    const wrap = wrapRef.current
    const cv = canvasRef.current
    const host = wrap?.parentElement
    if (!wrap || !cv || !host) return undefined
    const ctx = cv.getContext('2d')
    if (!ctx) return undefined

    let W = 0
    let H = 0
    let dpr = 1
    let visible = true
    let raf = 0
    let last = performance.now()
    let time = 0
    const ptr = { x: -1e4, y: -1e4, vx: 0, vy: 0, t: 0 }

    const readPalette = () => {
      const dark = document.documentElement.getAttribute('data-theme') === 'dark'
      return dark
        ? ['#F2B45A', '#D96B73', '#DFCFC8']
        : ['#6B141A', '#C87A19', '#8E5B3A']
    }

    const makePetalSprite = (color, variant) => {
      const c = document.createElement('canvas')
      c.width = 40
      c.height = 40
      const g = c.getContext('2d')
      if (!g) return c
      g.translate(20, 20)
      g.fillStyle = color
      g.beginPath()
      if (variant === 0) {
        // Serpihan daun/kelopak naskah
        g.moveTo(0, -13)
        g.bezierCurveTo(9, -6, 9, 7, 0, 13)
        g.bezierCurveTo(-9, 7, -9, -6, 0, -13)
      } else if (variant === 1) {
        // Wajik tipis ragam Ulos
        g.moveTo(0, -11)
        g.lineTo(7, 0)
        g.lineTo(0, 11)
        g.lineTo(-7, 0)
        g.closePath()
      } else {
        // Goresan kuas lengkung
        g.ellipse(0, 0, 4.5, 12, 0.25, 0, Math.PI * 2)
      }
      g.fill()
      return c
    }

    let sprites = readPalette().map((col, idx) => makePetalSprite(col, idx))
    const rebuildSprites = () => {
      sprites = readPalette().map((col, idx) => makePetalSprite(col, idx))
    }

    const mo = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.attributeName === 'data-theme') {
          rebuildSprites()
          if (reduce) drawReduced()
          break
        }
      }
    })
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })

    const resize = () => {
      const r = wrap.getBoundingClientRect()
      W = Math.max(1, r.width)
      H = Math.max(1, r.height)
      dpr = Math.min(1.75, window.devicePixelRatio || 1)
      cv.width = Math.round(W * dpr)
      cv.height = Math.round(H * dpr)
      cv.style.width = `${W}px`
      cv.style.height = `${H}px`
    }

    const rng = mulberry32(202607)
    const spawn = (p, x, y, extra = false) => {
      const q = p || {}
      q.x = x
      q.y = y
      q.vx = extra ? (rng() - 0.5) * 42 : 7 + rng() * 14
      q.vy = extra ? 10 + rng() * 24 : 13 + rng() * 18
      q.z = 0.55 + rng() * 0.8
      q.rot = rng() * Math.PI * 2
      q.spin = (rng() - 0.5) * 1.9
      q.flip = rng() * Math.PI * 2
      q.flipV = 1.1 + rng() * 2.1
      q.ph = rng() * 10
      q.f = 0.6 + rng() * 0.9
      q.sprite = Math.floor(rng() * 3)
      q.alpha = 0.18 + rng() * 0.24
      return q
    }

    resize()
    const targetCount = () => clamp(Math.round((W * H) / 28000), 18, 32)
    const particles = []
    for (let i = 0; i < targetCount(); i += 1) {
      particles.push(spawn(null, rng() * W, rng() * H))
    }

    function drawReduced() {
      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.clearRect(0, 0, cv.width, cv.height)
      const r = mulberry32(411)
      for (let i = 0; i < 14; i += 1) {
        const px = (0.08 + r() * 0.84) * W * dpr
        const py = (0.1 + r() * 0.8) * H * dpr
        const z = (0.55 + r() * 0.65) * dpr * 0.58
        ctx.setTransform(1, 0, 0, 1, px, py)
        ctx.rotate(r() * Math.PI * 2)
        ctx.scale(z, z)
        ctx.globalAlpha = 0.24
        ctx.drawImage(sprites[i % sprites.length], -20, -20, 40, 40)
      }
      ctx.globalAlpha = 1
    }

    if (reduce) {
      drawReduced()
      const ro = typeof ResizeObserver !== 'undefined'
        ? new ResizeObserver(() => {
            resize()
            drawReduced()
          })
        : null
      ro?.observe(wrap)
      return () => {
        ro?.disconnect()
        mo.disconnect()
      }
    }

    const tick = (now) => {
      raf = 0
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      time += dt

      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.clearRect(0, 0, cv.width, cv.height)

      const windRadius = 145
      for (let i = 0; i < particles.length; i += 1) {
        const p = particles[i]
        const dx = p.x - ptr.x
        const dy = p.y - ptr.y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < windRadius && dist > 1) {
          const push = (1 - dist / windRadius) * 0.9
          p.vx += (ptr.vx * 0.045 + (dx / dist) * 18) * push * dt
          p.vy += (ptr.vy * 0.045 + (dy / dist) * 12) * push * dt
          p.spin += push * 0.14
        }

        const sway = Math.sin(time * 1.15 * p.f + p.ph) * 11
        p.x += (p.vx + sway) * p.z * dt
        p.y += p.vy * p.z * dt
        p.vx *= 0.992
        p.vy = p.vy * 0.992 + (14 + 6 * p.z) * 0.008
        p.rot += p.spin * dt
        p.flip += p.flipV * dt

        if (p.y > H + 26 || p.x > W + 40 || p.x < -40) {
          spawn(p, rng() * W, -16)
        }

        const scaleZ = p.z * dpr * 0.56
        const flipScale = 0.35 + 0.65 * Math.abs(Math.cos(p.flip))
        ctx.setTransform(1, 0, 0, 1, p.x * dpr, p.y * dpr)
        ctx.rotate(p.rot)
        ctx.scale(scaleZ * flipScale, scaleZ)
        ctx.globalAlpha = p.alpha
        ctx.drawImage(sprites[p.sprite], -20, -20, 40, 40)
      }
      ctx.globalAlpha = 1

      if (visible) raf = requestAnimationFrame(tick)
    }

    const start = () => {
      if (!raf && visible) {
        last = performance.now()
        raf = requestAnimationFrame(tick)
      }
    }

    const onPointerMove = (e) => {
      const r = wrap.getBoundingClientRect()
      const x = e.clientX - r.left
      const y = e.clientY - r.top
      const now = performance.now()
      const dt = Math.max(8, now - ptr.t) / 1000
      if (ptr.t && now - ptr.t < 140) {
        ptr.vx = clamp((x - ptr.x) / dt, -1400, 1400)
        ptr.vy = clamp((y - ptr.y) / dt, -1400, 1400)
      }
      ptr.x = x
      ptr.y = y
      ptr.t = now
    }

    const onPointerLeave = () => {
      ptr.x = -1e4
      ptr.y = -1e4
      ptr.vx = 0
      ptr.vy = 0
    }

    const onPointerDown = (e) => {
      if (e.target.closest('button, a, input, label')) return
      const r = wrap.getBoundingClientRect()
      const cx = e.clientX - r.left
      const cy = e.clientY - r.top
      for (let i = 0; i < 7; i += 1) {
        if (particles.length < 44) {
          particles.push(spawn(null, cx + (rng() - 0.5) * 28, cy + (rng() - 0.5) * 18, true))
        }
      }
    }

    start()

    const ro = typeof ResizeObserver !== 'undefined'
      ? new ResizeObserver(() => resize())
      : null
    ro?.observe(wrap)

    const io = typeof IntersectionObserver !== 'undefined'
      ? new IntersectionObserver((entries) => {
          visible = entries[0]?.isIntersecting ?? true
          if (visible) start()
          else if (raf) {
            cancelAnimationFrame(raf)
            raf = 0
          }
        })
      : null
    io?.observe(host)

    host.addEventListener('pointermove', onPointerMove)
    host.addEventListener('pointerleave', onPointerLeave)
    host.addEventListener('pointerdown', onPointerDown)

    return () => {
      if (raf) cancelAnimationFrame(raf)
      ro?.disconnect()
      io?.disconnect()
      mo.disconnect()
      host.removeEventListener('pointermove', onPointerMove)
      host.removeEventListener('pointerleave', onPointerLeave)
      host.removeEventListener('pointerdown', onPointerDown)
    }
  }, [reduce])

  return (
    <div ref={wrapRef} className={`hero-canvas-layer ${className}`} aria-hidden="true">
      <canvas ref={canvasRef} />
    </div>
  )
}

/**
 * Animasi judul huruf-per-huruf bangkit miring dengan penarikan garis bawah (pola Letters Zip 1).
 * Menerima array baris berupa string atau array segmen { text, accent }.
 */
export function LetterTiltReveal({ lines, className = '', delay = 0.06 }) {
  const reduce = useReducedMotion()

  const normalizedLines = lines.map((line) => {
    if (typeof line === 'string') return [{ text: line, accent: false }]
    if (Array.isArray(line)) return line
    return [{ text: line?.text || '', accent: Boolean(line?.accent) }]
  })

  if (reduce) {
    return (
      <span className={className}>
        {normalizedLines.map((segments, lineIdx) => (
          <span key={lineIdx} className="letter-tilt-line">
            {segments.map((seg, segIdx) =>
              seg.accent ? (
                <span key={segIdx} className="guide-title-accent">
                  {seg.text}
                  <span className="guide-underline-draw" aria-hidden="true" />
                </span>
              ) : (
                <Fragment key={segIdx}>{seg.text}</Fragment>
              ),
            )}
          </span>
        ))}
      </span>
    )
  }

  let runningChar = 0

  const renderAnimatedWords = (text, lineBaseDelay) => {
    const tokens = String(text || '').split(/(\s+)/)
    return tokens.map((tok, tIdx) => {
      if (!tok) return null
      if (/^\s+$/.test(tok)) {
        return <Fragment key={`sp-${tIdx}`}>{' '}</Fragment>
      }
      const chars = Array.from(tok)
      return (
        <span key={`w-${tIdx}`} className="letter-tilt-word">
          {chars.map((ch, cIdx) => {
            const idxOrder = runningChar
            runningChar += 1
            return (
              <motion.span
                key={`c-${cIdx}`}
                className="letter-tilt-char"
                initial={{ y: '112%', rotate: 5.5, opacity: 0 }}
                animate={{ y: '0%', rotate: 0, opacity: 1 }}
                transition={{
                  duration: 0.72,
                  ease: EASE_OUT,
                  delay: lineBaseDelay + Math.min(idxOrder * 0.022, 0.55),
                }}
              >
                {ch}
              </motion.span>
            )
          })}
        </span>
      )
    })
  }

  return (
    <span className={className}>
      {normalizedLines.map((segments, lineIdx) => {
        const lineDelay = delay + lineIdx * 0.08
        return (
          <span key={lineIdx} className="letter-tilt-line">
            {segments.map((seg, segIdx) =>
              seg.accent ? (
                <span key={segIdx} className="guide-title-accent">
                  {renderAnimatedWords(seg.text, lineDelay)}
                  <motion.span
                    aria-hidden="true"
                    className="guide-underline-draw"
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ duration: 0.65, ease: EASE_OUT, delay: 0.42 }}
                  />
                </span>
              ) : (
                <Fragment key={segIdx}>{renderAnimatedWords(seg.text, lineDelay)}</Fragment>
              ),
            )}
          </span>
        )
      })}
    </span>
  )
}
