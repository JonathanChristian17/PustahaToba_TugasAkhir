import { useEffect, useRef, useState } from 'react'
import { EASE_OUT } from './MotionPrimitives.jsx'
import { motion } from 'motion/react'

/**
 * Editor praproses ringan di sisi peramban:
 * memutar citra kelipatan 90 derajat dan memotong area tepi berlebih via Canvas
 * sebelum citra dibaca oleh model.
 */
export default function ImagePrepEditor({ src, label, onApply, onResetOriginal, hasModified, onClose }) {
  const [rotation, setRotation] = useState(0)
  const [cropLeft, setCropLeft] = useState(0)
  const [cropRight, setCropRight] = useState(0)
  const [cropTop, setCropTop] = useState(0)
  const [cropBottom, setCropBottom] = useState(0)
  const [dims, setDims] = useState({ w: 0, h: 0 })
  const [isApplying, setIsApplying] = useState(false)

  const imgObjRef = useRef(null)
  const previewCanvasRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      if (cancelled) return
      imgObjRef.current = img
      const isQuarter = Math.abs(rotation % 180) === 90
      const rotW = isQuarter ? img.naturalHeight : img.naturalWidth
      const rotH = isQuarter ? img.naturalWidth : img.naturalHeight
      setDims({ w: rotW, h: rotH })
      drawPreview(img, rotation, { cropLeft, cropRight, cropTop, cropBottom })
    }
    img.src = src
    return () => {
      cancelled = true
    }
  }, [src])

  const drawPreview = (img, rot, crop) => {
    const canvas = previewCanvasRef.current
    if (!canvas || !img) return

    const isQuarter = Math.abs(rot % 180) === 90
    const rotW = isQuarter ? img.naturalHeight : img.naturalWidth
    const rotH = isQuarter ? img.naturalWidth : img.naturalHeight
    setDims({ w: rotW, h: rotH })

    const maxPreviewW = 460
    const scale = Math.min(1, maxPreviewW / Math.max(1, rotW))
    canvas.width = Math.max(1, Math.round(rotW * scale))
    canvas.height = Math.max(1, Math.round(rotH * scale))

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.save()
    ctx.translate(canvas.width / 2, canvas.height / 2)
    ctx.rotate((rot * Math.PI) / 180)
    const drawW = img.naturalWidth * scale
    const drawH = img.naturalHeight * scale
    ctx.drawImage(img, -drawW / 2, -drawH / 2, drawW, drawH)
    ctx.restore()

    // Arsir area di luar kotak potong
    const lx = (crop.cropLeft / 100) * canvas.width
    const rx = canvas.width - (crop.cropRight / 100) * canvas.width
    const ty = (crop.cropTop / 100) * canvas.height
    const by = canvas.height - (crop.cropBottom / 100) * canvas.height
    const cw = Math.max(8, rx - lx)
    const ch = Math.max(8, by - ty)

    ctx.save()
    ctx.fillStyle = 'rgba(28, 12, 14, 0.54)'
    ctx.fillRect(0, 0, canvas.width, ty)
    ctx.fillRect(0, ty + ch, canvas.width, canvas.height - (ty + ch))
    ctx.fillRect(0, ty, lx, ch)
    ctx.fillRect(lx + cw, ty, canvas.width - (lx + cw), ch)

    ctx.strokeStyle = '#F2B45A'
    ctx.lineWidth = 2
    ctx.strokeRect(lx, ty, cw, ch)
    ctx.restore()
  }

  useEffect(() => {
    if (!imgObjRef.current) return
    drawPreview(imgObjRef.current, rotation, { cropLeft, cropRight, cropTop, cropBottom })
  }, [rotation, cropLeft, cropRight, cropTop, cropBottom])

  const updateCrop = (edge, value) => {
    const val = Math.max(0, Math.min(40, Number(value) || 0))
    if (edge === 'left') setCropLeft(Math.min(val, 80 - cropRight))
    if (edge === 'right') setCropRight(Math.min(val, 80 - cropLeft))
    if (edge === 'top') setCropTop(Math.min(val, 80 - cropBottom))
    if (edge === 'bottom') setCropBottom(Math.min(val, 80 - cropTop))
  }

  const applyPreset = (preset) => {
    if (preset === 'full') {
      setCropLeft(0)
      setCropRight(0)
      setCropTop(0)
      setCropBottom(0)
    } else if (preset === 'trim10') {
      setCropLeft(8)
      setCropRight(8)
      setCropTop(10)
      setCropBottom(10)
    } else if (preset === 'strip') {
      setCropLeft(4)
      setCropRight(4)
      setCropTop(22)
      setCropBottom(22)
    }
  }

  const outW = Math.max(1, Math.round((dims.w * (100 - cropLeft - cropRight)) / 100))
  const outH = Math.max(1, Math.round((dims.h * (100 - cropTop - cropBottom)) / 100))

  const handleApply = () => {
    const img = imgObjRef.current
    if (!img) return
    setIsApplying(true)

    const isQuarter = Math.abs(rotation % 180) === 90
    const rotW = isQuarter ? img.naturalHeight : img.naturalWidth
    const rotH = isQuarter ? img.naturalWidth : img.naturalHeight

    const rotCanvas = document.createElement('canvas')
    rotCanvas.width = rotW
    rotCanvas.height = rotH
    const rctx = rotCanvas.getContext('2d')
    if (!rctx) {
      setIsApplying(false)
      return
    }
    rctx.translate(rotW / 2, rotH / 2)
    rctx.rotate((rotation * Math.PI) / 180)
    rctx.drawImage(img, -img.naturalWidth / 2, -img.naturalHeight / 2)

    const sx = Math.round((cropLeft / 100) * rotW)
    const sy = Math.round((cropTop / 100) * rotH)
    const sw = Math.max(16, Math.round(((100 - cropLeft - cropRight) / 100) * rotW))
    const sh = Math.max(16, Math.round(((100 - cropTop - cropBottom) / 100) * rotH))

    const outCanvas = document.createElement('canvas')
    outCanvas.width = sw
    outCanvas.height = sh
    const octx = outCanvas.getContext('2d')
    if (!octx) {
      setIsApplying(false)
      return
    }
    octx.drawImage(rotCanvas, sx, sy, sw, sh, 0, 0, sw, sh)

    const dataUrl = outCanvas.toDataURL('image/png')
    const parts = []
    if (rotation !== 0) parts.push(`Putar ${rotation}°`)
    if (cropLeft || cropRight || cropTop || cropBottom) parts.push(`Potong ${sw}x${sh} px`)
    const summaryNote = parts.length > 0 ? parts.join(' · ') : 'Salinan disesuaikan'
    setIsApplying(false)
    onApply(dataUrl, summaryNote)
  }

  return (
    <motion.div
      className="prep-editor-box"
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.24, ease: EASE_OUT }}
    >
      <div className="prep-editor-head">
        <div>
          <span className="panel-kicker">PRAPROSES CITRA RINGAN</span>
          <p className="prep-editor-title">Putar 90° &amp; Potong Tepi: {label}</p>
        </div>
        <button type="button" className="btn-dismiss" onClick={onClose}>
          Tutup
        </button>
      </div>

      <div className="prep-canvas-stage">
        <canvas ref={previewCanvasRef} className="prep-preview-canvas" />
        <span className="prep-dim-badge">
          Keluaran: {outW} x {outH} px {rotation !== 0 ? `(${rotation}°)` : ''}
        </span>
      </div>

      <div className="prep-toolbar-row">
        <div className="prep-btn-group" role="group" aria-label="Rotasi citra 90 derajat">
          <button
            type="button"
            className="btn-prep-mini"
            onClick={() => setRotation((r) => (r - 90 + 360) % 360)}
          >
            ↺ Putar -90°
          </button>
          <button
            type="button"
            className="btn-prep-mini"
            onClick={() => setRotation((r) => (r + 90) % 360)}
          >
            ↻ Putar +90°
          </button>
        </div>

        <div className="prep-btn-group" role="group" aria-label="Preset area potong">
          <button type="button" className="btn-prep-mini" onClick={() => applyPreset('full')}>
            Penuh
          </button>
          <button type="button" className="btn-prep-mini" onClick={() => applyPreset('trim10')}>
            Rapikan Tepi
          </button>
          <button type="button" className="btn-prep-mini" onClick={() => applyPreset('strip')}>
            Fokus Baris
          </button>
        </div>
      </div>

      <div className="prep-sliders-grid">
        <label className="prep-slider-item">
          <span>Batas Kiri ({cropLeft}%)</span>
          <input
            type="range"
            min="0"
            max="40"
            value={cropLeft}
            onChange={(e) => updateCrop('left', e.target.value)}
          />
        </label>
        <label className="prep-slider-item">
          <span>Batas Kanan ({cropRight}%)</span>
          <input
            type="range"
            min="0"
            max="40"
            value={cropRight}
            onChange={(e) => updateCrop('right', e.target.value)}
          />
        </label>
        <label className="prep-slider-item">
          <span>Batas Atas ({cropTop}%)</span>
          <input
            type="range"
            min="0"
            max="40"
            value={cropTop}
            onChange={(e) => updateCrop('top', e.target.value)}
          />
        </label>
        <label className="prep-slider-item">
          <span>Batas Bawah ({cropBottom}%)</span>
          <input
            type="range"
            min="0"
            max="40"
            value={cropBottom}
            onChange={(e) => updateCrop('bottom', e.target.value)}
          />
        </label>
      </div>

      <div className="prep-footer-actions">
        {hasModified && (
          <button type="button" className="btn-text-action" onClick={onResetOriginal}>
            Kembalikan Citra Asli
          </button>
        )}
        <button
          type="button"
          className="btn-curtain btn-primary-read"
          disabled={isApplying}
          onClick={handleApply}
        >
          <span className="btn-curtain-bg" aria-hidden="true" />
          <span className="btn-curtain-label">
            {isApplying ? 'Menerapkan...' : 'Terapkan ke Kanvas'}
          </span>
        </button>
      </div>
    </motion.div>
  )
}
