import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import ImagePrepEditor from '../components/ImagePrepEditor.jsx'
import { MODEL_IDENTITY } from '../data/samples.js'
import {
  buildTransliterationJson,
  buildTransliterationTxt,
  describeSpacingStatus,
  instanceColor,
  renderOverlayViaApi,
  displayReading,
  unresolvedReadingUnits,
} from '../utils/transliterationAdapter.js'
import {
  EASE_OUT,
  FadeUp,
  MetricArc,
  RiseLines,
  useTweenNumber,
} from '../components/MotionPrimitives.jsx'
import {
  IconAlertNotice,
  IconDownloadFile,
  IconPlayRead,
  IconReadingText,
} from '../components/Icons.jsx'

function escapeCsvField(value) {
  const str = String(value ?? '')
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`
  }
  return str
}

const BACKBONE_PROFILES = {
  r50: {
    id: 'r50',
    badge: 'Backbone Terpilih',
    name: 'ResNet-50-FPN (Epoch 28 / 30)',
    summary:
      'Dipilih berdasarkan validasi tertinggi (AP50:95 68,34%) untuk menjaga presisi masker segmentasi huruf pokok maupun diakritik kecil.',
    breakdown: [
      { label: 'Prediksi Benar (Matched)', value: '898 / 941 instansi', tone: 'good' },
      { label: 'Salah Kelas (Misclassified)', value: '27 instansi', tone: 'warn' },
      { label: 'Acuan Terlewat (Missed)', value: '16 instansi', tone: 'warn' },
      { label: 'Prediksi Tambahan (Extra)', value: '66 instansi', tone: 'neutral' },
    ],
  },
  r101: {
    id: 'r101',
    badge: 'Backbone Pembanding',
    name: 'ResNet-101-FPN (Epoch 25 / 30)',
    summary:
      'Dilatih pada protokol 30 epoch dan dataset identik; validasi berhenti pada AP50:95 68,19%, lebih rendah dari ResNet-50 epoch 28.',
    breakdown: [
      { label: 'Protokol Pelatihan', value: '30 epoch penuh (terbaik epoch 25)', tone: 'neutral' },
      { label: 'Mask AP50:95 Validasi', value: '68,19% (147 citra validasi)', tone: 'neutral' },
      { label: 'Status Integrasi', value: 'Pembanding eksperimental (non-aktif)', tone: 'neutral' },
      { label: 'Keputusan Model', value: 'R50 Epoch 28 tetap model utama', tone: 'good' },
    ],
  },
}

const PIPELINE_STAGES = [
  {
    step: '01',
    layer: 'Input & ResNet-50-FPN Backbone',
    detail:
      'Citra masukan PNG/JPG/WEBP diproses melalui piramida fitur FPN P2-P5 untuk menangkap kontur huruf Ina ni Surat sekaligus goresan kecil Anak ni Surat.',
  },
  {
    step: '02',
    layer: 'Region Proposal Network (RPN)',
    detail:
      'Membangkitkan kandidat kotak wilayah tulisan yang berpotensi memuat karakter individual pada baris tulisan tangan.',
  },
  {
    step: '03',
    layer: 'RoIAlign + 25-Class Box & Mask Head',
    detail:
      'Mengklasifikasikan 25 kelas aksara (19 Ina + 6 Anak), menyaring skor confidence >= 0,50, dan membentuk poligon segmentasi per instansi.',
  },
  {
    step: '04',
    layer: 'Spatial Grouping & Latin Decoder',
    detail:
      'Mengurutkan posisi karakter kiri-ke-kanan, memasangkan Anak ni Surat ke Ina ni Surat terdekat, serta menghasilkan bacaan Latin literal dan usulan spasi.',
  },
]

const DATASET_SPLITS = [
  {
    split: 'Latih (Train)',
    images: '1.257 citra',
    instances: '2.229 instansi',
    share: 82,
    note: 'Gabungan 1.140 citra publik + primer penulis P02, P03, P05, P06',
  },
  {
    split: 'Validasi (Val)',
    images: '147 citra',
    instances: '918 instansi',
    share: 10,
    note: 'Penulis P01, P04, P09, P11, P12 untuk pemilihan epoch terbaik',
  },
  {
    split: 'Uji (Test)',
    images: '131 citra',
    instances: '941 instansi',
    share: 8,
    note: 'Penulis P07, P08, P10, P13, P14 sebagai himpunan evaluasi akhir',
  },
]

const ERROR_GROUPS = [
  { label: 'Citra Bersih Seluruhnya', count: 80, total: 131, desc: 'Seluruh unit karakter cocok dengan acuan.' },
  { label: 'Mengandung Salah Kelas', count: 22, total: 131, desc: 'Kemiripan bentuk huruf dasar memicu ketertukaran label.' },
  { label: 'Mengandung Objek Terlewat', count: 15, total: 131, desc: 'Umumnya tanda diakritik kecil di dekat tepi huruf.' },
  { label: 'Mengandung Prediksi Tambahan', count: 44, total: 131, desc: 'Tumpang tindih kandidat pada satu goresan sebelum penyaringan selokasi.' },
]

export default function ResearchPage({
  samples,
  currentItem,
  sessionHistory = [],
  isScanning,
  backendStatus,
  modelIdentity,
  apiError,
  onDismissError,
  onSelectSample,
  onSelectHistoryItem,
  onUploadFile,
  onUpdateCurrentImage,
  onResetOriginalImage,
  onRunReadScript,
  onBackToPublic,
}) {
  const [researchTab, setResearchTab] = useState('studio')
  const [activeCharId, setActiveCharId] = useState(null)
  const [vizMode, setVizMode] = useState('mask_bbox')
  const [showLabels, setShowLabels] = useState(true)
  const [maskOpacity, setMaskOpacity] = useState(0.65)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isPanning, setIsPanning] = useState(false)
  const [showPrepDrawer, setShowPrepDrawer] = useState(false)
  const [detectronRenderUrl, setDetectronRenderUrl] = useState('')
  const [isRenderingOverlay, setIsRenderingOverlay] = useState(false)
  const [showLightbox, setShowLightbox] = useState(false)

  const [selectedBackbone, setSelectedBackbone] = useState('r50')
  const [activeStage, setActiveStage] = useState('01')

  const imgRef = useRef(null)
  const fileQuickRef = useRef(null)
  const panStartRef = useRef(null)

  const tweenCa = useTweenNumber(95.43, 850)
  const tweenAp = useTweenNumber(60.38, 850)
  const tweenIou = useTweenNumber(80.9, 850)

  useEffect(() => {
    setActiveCharId(null)
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setShowPrepDrawer(false)
    setDetectronRenderUrl('')
    setShowLightbox(false)
  }, [currentItem?.id])

  useEffect(() => {
    if (!showLightbox) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') setShowLightbox(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [showLightbox])

  const activeDetections = currentItem?.detections || []

  const activeDetection = activeDetections.find((d) => (d.instance_id ?? d.id) === activeCharId)

  // Render overlay Detectron2 (visual.render_pair) langsung dari server agar warna unik tiap instansi & opasitas khusus mask
  useEffect(() => {
    const cacheKey = currentItem?.cacheKey || currentItem?.id
    if (!currentItem || !cacheKey || activeDetections.length === 0) {
      setDetectronRenderUrl('')
      return undefined
    }
    let cancelled = false
    const apiModeMap = {
      mask_bbox: 'Mask + Bbox',
      mask_only: 'Mask',
      bbox_only: 'Bbox',
      raw_image: 'raw_image',
    }
    const focusNum = activeDetection?.display_number ?? null
    const timer = setTimeout(() => {
      setIsRenderingOverlay(true)
      renderOverlayViaApi({
        cacheKey,
        mode: apiModeMap[vizMode] || 'Mask + Bbox',
        opacity: maskOpacity,
        focus: focusNum,
      })
        .then((dataUrl) => {
          if (!cancelled) setDetectronRenderUrl(dataUrl)
        })
        .catch(() => {
          if (!cancelled) setDetectronRenderUrl('')
        })
        .finally(() => {
          if (!cancelled) setIsRenderingOverlay(false)
        })
    }, 90)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [
    currentItem?.cacheKey,
    currentItem?.id,
    vizMode,
    maskOpacity,
    activeDetection?.display_number,
    activeDetections.length,
  ])
  const inaCount = activeDetections.filter((d) => d.kind === 'Ina').length
  const anakCount = activeDetections.filter((d) => d.kind !== 'Ina').length

  const showMask = vizMode === 'mask_bbox' || vizMode === 'mask_only'
  const showBoxes = vizMode === 'mask_bbox' || vizMode === 'bbox_only'

  const adjustZoom = (delta) => {
    setZoom((prev) => {
      const next = Math.min(3.5, Math.max(1, Number((prev + delta).toFixed(2))))
      if (next === 1) setPan({ x: 0, y: 0 })
      return next
    })
  }

  const resetView = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  const handlePointerDown = (e) => {
    if (zoom <= 1) return
    if (e.target.closest('[data-det-hit="true"]')) return
    e.currentTarget.setPointerCapture?.(e.pointerId)
    setIsPanning(true)
    panStartRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y }
  }

  const handlePointerMove = (e) => {
    if (!isPanning || !panStartRef.current) return
    const nextX = e.clientX - panStartRef.current.x
    const nextY = e.clientY - panStartRef.current.y
    const limit = Math.max(40, (zoom - 1) * 180)
    setPan({
      x: Math.max(-limit, Math.min(limit, nextX)),
      y: Math.max(-limit, Math.min(limit, nextY)),
    })
  }

  const handlePointerUp = (e) => {
    if (!isPanning) return
    e.currentTarget.releasePointerCapture?.(e.pointerId)
    setIsPanning(false)
    panStartRef.current = null
  }

  const triggerDownload = (filename, content, mimeType) => {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  const handleDownloadJsonPredictions = () => {
    if (!currentItem) return
    if (currentItem.researchExports?.predictions_json_text) {
      triggerDownload(
        `${currentItem.id}_predictions.json`,
        currentItem.researchExports.predictions_json_text,
        'application/json;charset=utf-8',
      )
      return
    }
    const payload = {
      source_name: currentItem.sourceName || currentItem.label,
      source_sha256: currentItem.sourceSha256 || null,
      model_identity: modelIdentity,
      display_threshold: MODEL_IDENTITY.scoreThreshold,
      predictions: activeDetections,
    }
    triggerDownload(
      `${currentItem.id}_predictions.json`,
      JSON.stringify(payload, null, 2),
      'application/json;charset=utf-8',
    )
  }

  const handleDownloadCsv = () => {
    if (!currentItem) return
    if (currentItem.researchExports?.karakter_csv_text) {
      triggerDownload(
        `${currentItem.id}_karakter.csv`,
        currentItem.researchExports.karakter_csv_text,
        'text/csv;charset=utf-8',
      )
      return
    }
    const header = 'nomor,instance_id,category_id,class_label,jenis,confidence,x_pct,y_pct,w_pct,h_pct'
    const rows = activeDetections.map((d) =>
      [
        d.display_number ?? d.id,
        d.instance_id ?? d.id,
        d.category_id ?? '',
        d.rawClass || d.cls,
        d.kind,
        d.score.toFixed(4),
        ...d.box,
      ]
        .map(escapeCsvField)
        .join(','),
    )
    triggerDownload(
      `${currentItem.id}_karakter.csv`,
      [header, ...rows].join('\n'),
      'text/csv;charset=utf-8',
    )
  }

  const handleDownloadOverlayPng = () => {
    if (!currentItem) return
    if (detectronRenderUrl) {
      const link = document.createElement('a')
      link.href = detectronRenderUrl
      link.download = `${currentItem.id}_overlay_segmentasi.png`
      document.body.appendChild(link)
      link.click()
      link.remove()
      return
    }
    if (currentItem.researchExports?.overlay_png_b64 && vizMode === 'mask_bbox' && showLabels) {
      const link = document.createElement('a')
      link.href = `data:image/png;base64,${currentItem.researchExports.overlay_png_b64}`
      link.download = `${currentItem.id}_overlay_segmentasi.png`
      document.body.appendChild(link)
      link.click()
      link.remove()
      return
    }

    const imgEl = imgRef.current
    if (!imgEl) return
    const width = imgEl.naturalWidth || 640
    const height = imgEl.naturalHeight || 240
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.drawImage(imgEl, 0, 0, width, height)

    activeDetections.forEach((det) => {
      const [xPct, yPct, wPct, hPct] = det.box
      const x = (xPct / 100) * width
      const y = (yPct / 100) * height
      const w = (wPct / 100) * width
      const h = (hPct / 100) * height
      const isIna = det.kind === 'Ina'
      const color = isIna ? '#6B141A' : '#C87A19'

      if (showMask) {
        ctx.save()
        ctx.globalAlpha = maskOpacity
        ctx.fillStyle = instanceColor(det.display_number ?? det.id)
        if (det.polygons?.length > 0) {
          det.polygons.forEach((poly) => {
            ctx.beginPath()
            poly.forEach((pt, idx) => {
              const px = (pt[0] / 100) * width
              const py = (pt[1] / 100) * height
              if (idx === 0) ctx.moveTo(px, py)
              else ctx.lineTo(px, py)
            })
            ctx.closePath()
            ctx.fill()
          })
        } else {
          ctx.beginPath()
          ctx.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, 0, 0, Math.PI * 2)
          ctx.fill()
        }
        ctx.restore()
      }

      if (showBoxes) {
        ctx.save()
        ctx.strokeStyle = '#AF3131'
        ctx.lineWidth = 2
        ctx.strokeRect(x, y, w, h)
        ctx.restore()
      }

      if (showLabels) {
        ctx.save()
        ctx.font = 'bold 13px sans-serif'
        ctx.fillStyle = '#0F172A'
        ctx.fillText(`#${det.display_number ?? det.id} ${det.rawClass || det.cls}`, x, Math.max(14, y - 4))
        ctx.restore()
      }
    })

    const pngUrl = canvas.toDataURL('image/png')
    const link = document.createElement('a')
    link.href = pngUrl
    link.download = `${currentItem.id}_overlay_segmentasi.png`
    document.body.appendChild(link)
    link.click()
    link.remove()
  }

  const profile = BACKBONE_PROFILES[selectedBackbone]
  const currentStage = PIPELINE_STAGES.find((s) => s.step === activeStage) || PIPELINE_STAGES[0]
  const spacingMeta = describeSpacingStatus(currentItem?.wordSpacing)
  const epochLabel = modelIdentity?.epoch ? `Epoch ${modelIdentity.epoch}` : 'Epoch 28'

  return (
    <div className="research-flow">
      <section className="research-hero-band">
        <div className="research-ulos-bg" aria-hidden="true" />

        <div className="research-hero-inner">
          <div className="lab-hero-top">
            <div className="lab-hero-copy">
              <span className="hero-kicker lab-kicker-light">
                DEEP LEARNING VISION LAB · {modelIdentity?.architecture || MODEL_IDENTITY.architecture} ({epochLabel})
              </span>
              <h1 className="hero-display-title night-hero-title">
                <RiseLines lines={['Inspeksi Segmentasi &', 'Evaluasi Model 25 Kelas']} />
              </h1>
              <p className="research-hero-lead">
                Studio pemeriksaan masker RLE, kotak batas (bbox), kandidat bertumpuk, dan jejak transliterasi modul ({backendStatus?.moduleVersion || '0.4.3'}) serta ringkasan evaluasi 131 citra uji dataset penelitian.
              </p>
            </div>

            <div className="lab-hero-switcher">
              <div className="lab-mode-tabs" role="tablist" aria-label="Pilih tampilan hasil penelitian">
                <button
                  type="button"
                  role="tab"
                  aria-selected={researchTab === 'studio'}
                  className={`lab-mode-tab ${researchTab === 'studio' ? 'is-active' : ''}`}
                  onClick={() => setResearchTab('studio')}
                >
                  Studio Segmentasi
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={researchTab === 'evaluation'}
                  className={`lab-mode-tab ${researchTab === 'evaluation' ? 'is-active' : ''}`}
                  onClick={() => setResearchTab('evaluation')}
                >
                  Hasil Evaluasi &amp; Arsitektur
                </button>
              </div>
              <button type="button" className="btn-night-outline" onClick={onBackToPublic}>
                <IconReadingText size={15} />
                <span>Kembali ke Baca Aksara</span>
              </button>
            </div>
          </div>

          <div className="research-metrics-banner">
            <div className="research-metric-card">
              <MetricArc percent={95.43} label="Character Accuracy 95,43%" />
              <div>
                <span className="metric-kicker-light">CHARACTER ACCURACY (UJI 131)</span>
                <strong className="metric-value-light">{tweenCa.toFixed(2)}%</strong>
                <span className="metric-sub-light">898 / 941 instansi benar (bukan uji unggahan)</span>
              </div>
            </div>
            <div className="research-metric-card">
              <MetricArc percent={60.38} label="Mask AP50:95 60,38%" />
              <div>
                <span className="metric-kicker-light">MASK AP50:95 (COCO)</span>
                <strong className="metric-value-light">{tweenAp.toFixed(2)}%</strong>
                <span className="metric-sub-light">R50 {epochLabel} · Validasi 68,34%</span>
              </div>
            </div>
            <div className="research-metric-card">
              <MetricArc percent={80.9} label="Mean Mask IoU 80,90%" />
              <div>
                <span className="metric-kicker-light">MEAN MASK IOU (ACUAN)</span>
                <strong className="metric-value-light">{tweenIou.toFixed(2)}%</strong>
                <span className="metric-sub-light">Ketepatan kontur 25 kelas surat</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="studio-workspace-wrap">
        {apiError && (
          <div className="error-banner" role="alert" style={{ marginBottom: 16 }}>
            <span>{apiError}</span>
            <button type="button" className="btn-dismiss" onClick={onDismissError}>
              Tutup
            </button>
          </div>
        )}

        <AnimatePresence mode="wait">
          {researchTab === 'studio' ? (
            <motion.div
              key="tab-studio"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.22, ease: EASE_OUT }}
              className="studio-container-stack"
            >
              <FadeUp>
                <section className="panel pt-paper lab-source-dock" aria-label="Pilih citra masukan dan kondisi uji">
                  <div className="lab-dock-top">
                    <div className="lab-dock-samples">
                      <span className="panel-kicker">SUMBER MASUKAN CITRA &amp; RIWAYAT SESI</span>
                      <div className="studio-sample-pills" role="list">
                        {samples.map((item) => {
                          const isAct = currentItem?.id === item.id
                          return (
                            <button
                              key={item.id}
                              type="button"
                              role="listitem"
                              className={`studio-sample-pill ${isAct ? 'is-active' : ''}`}
                              title={item.label}
                              onClick={() => onSelectSample(item)}
                            >
                              <img src={item.src} alt="" width="36" height="24" />
                              <span>{item.label}</span>
                            </button>
                          )
                        })}
                        {sessionHistory
                          .filter((h) => !samples.some((s) => s.id === h.id))
                          .map((item) => {
                            const isAct = currentItem?.id === item.id
                            return (
                              <button
                                key={item.id}
                                type="button"
                                role="listitem"
                                className={`studio-sample-pill ${isAct ? 'is-active' : ''}`}
                                title={item.label}
                                onClick={() => onSelectHistoryItem?.(item)}
                              >
                                <img src={item.src} alt="" width="36" height="24" />
                                <span>{item.label}</span>
                              </button>
                            )
                          })}
                      </div>
                    </div>

                    <div className="lab-dock-actions">
                      <input
                        ref={fileQuickRef}
                        type="file"
                        accept="image/png,image/jpeg,image/webp"
                        hidden
                        onChange={(e) => {
                          const file = e.target.files?.[0]
                          if (file) onUploadFile(file)
                          e.target.value = ''
                        }}
                      />
                      <button
                        type="button"
                        className="btn-upload-accent"
                        onClick={() => fileQuickRef.current?.click()}
                      >
                        Unggah Citra
                      </button>
                      {currentItem && (
                        <button
                          type="button"
                          className={`btn-prep-toggle ${showPrepDrawer ? 'is-active' : ''}`}
                          onClick={() => setShowPrepDrawer((v) => !v)}
                        >
                          {showPrepDrawer ? 'Tutup Putar/Potong' : 'Putar / Potong'}
                        </button>
                      )}
                      {currentItem && (
                        <button
                          type="button"
                          className="btn-curtain btn-primary-read"
                          disabled={isScanning}
                          onClick={onRunReadScript}
                        >
                          <span className="btn-curtain-bg" aria-hidden="true" />
                          <span className="btn-curtain-label">
                            <IconPlayRead size={15} />
                            <span>
                              {isScanning
                                ? 'Memproses...'
                                : currentItem.transliteration
                                  ? 'Segmen Ulang'
                                  : 'Baca & Segmen Citra'}
                            </span>
                          </span>
                        </button>
                      )}
                    </div>
                  </div>

                  <AnimatePresence>
                    {showPrepDrawer && currentItem && (
                      <ImagePrepEditor
                        src={currentItem.originalSrc || currentItem.src}
                        label={currentItem.label}
                        hasModified={Boolean(currentItem.originalSrc && currentItem.src !== currentItem.originalSrc)}
                        onClose={() => setShowPrepDrawer(false)}
                        onResetOriginal={() => {
                          onResetOriginalImage?.()
                          setShowPrepDrawer(false)
                        }}
                        onApply={(dataUrl, summaryNote) => {
                          onUpdateCurrentImage?.(dataUrl, summaryNote)
                          setShowPrepDrawer(false)
                        }}
                      />
                    )}
                  </AnimatePresence>
                </section>
              </FadeUp>

              <div className="studio-enlarged-stack">
                <FadeUp className="studio-stage-col">
                  <section className="panel pt-paper studio-enlarged-stage" aria-labelledby="studio-canvas-heading">
                    <div className="panel-header panel-header-inline">
                      <div>
                        <span className="panel-kicker">01 · MASUKAN CITRA &amp; OVERLAY DETECTRON2 (MASK RLE)</span>
                        <h2 id="studio-canvas-heading" className="panel-title">
                          Inspeksi Overlay {currentItem ? `· ${currentItem.label}` : ''}
                        </h2>
                      </div>
                      <div className="legend-row">
                        <span className="mono">
                          {detectronRenderUrl
                            ? 'Overlay Bitmap Detectron2 Aktif (warna unik per instansi pada mask)'
                            : 'Mode Masker Vektor Multi-Warna'}
                        </span>
                      </div>
                    </div>

                    {!currentItem ? (
                      <div className="empty-state">
                        <p className="empty-title">Belum ada citra terpilih</p>
                        <p className="empty-desc">
                          Pilih salah satu sampel di atas atau unggah berkas citra Aksara Batak Toba.
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="research-controls">
                          <div className="toggle-group" role="group" aria-label="Mode lapisan segmentasi">
                            {[
                              { id: 'mask_bbox', label: 'Mask + Bbox' },
                              { id: 'raw_image', label: 'Citra Murni' },
                              { id: 'mask_only', label: 'Mask' },
                              { id: 'bbox_only', label: 'Bbox' },
                            ].map((opt) => (
                              <button
                                key={opt.id}
                                type="button"
                                className={`chip-toggle ${vizMode === opt.id ? 'is-on' : ''}`}
                                onClick={() => setVizMode(opt.id)}
                              >
                                {opt.label}
                              </button>
                            ))}
                            {!detectronRenderUrl && (
                              <button
                                type="button"
                                className={`chip-toggle ${showLabels ? 'is-on' : ''}`}
                                onClick={() => setShowLabels((v) => !v)}
                              >
                                Label
                              </button>
                            )}
                          </div>

                          <div className="studio-zoom-group">
                            <label className="opacity-slider-mini">
                              <span>Opasitas Mask {Math.round(maskOpacity * 100)}%</span>
                              <input
                                type="range"
                                min="0.1"
                                max="0.9"
                                step="0.05"
                                value={maskOpacity}
                                onChange={(e) => setMaskOpacity(Number(e.target.value))}
                              />
                            </label>
                            <div className="zoom-stepper" role="group" aria-label="Kontrol perbesaran kanvas">
                              <button
                                type="button"
                                className="zoom-btn"
                                disabled={zoom <= 1}
                                aria-label="Perkecil"
                                onClick={() => adjustZoom(-0.5)}
                              >
                                -
                              </button>
                              <span className="zoom-readout">{Math.round(zoom * 100)}%</span>
                              <button
                                type="button"
                                className="zoom-btn"
                                disabled={zoom >= 3.5}
                                aria-label="Perbesar"
                                onClick={() => adjustZoom(0.5)}
                              >
                                +
                              </button>
                              {zoom > 1 && (
                                <button type="button" className="zoom-btn is-reset" onClick={resetView}>
                                  Reset
                                </button>
                              )}
                            </div>
                            <button
                              type="button"
                              className="btn-prep-toggle"
                              onClick={() => setShowLightbox(true)}
                            >
                              Perbesar Layar Penuh
                            </button>
                          </div>
                        </div>

                        <div className="canvas-stage">
                          <div className="canvas-toolbar">
                            <span>
                              {zoom > 1
                                ? `Zoom ${Math.round(zoom * 100)}% · Seret kanvas untuk memeriksa detail Anak ni Surat`
                                : 'Klik gambar atau tombol "Perbesar Layar Penuh" untuk inspeksi maksimal'}
                            </span>
                            <span className="mono">
                              {isRenderingOverlay ? 'Merender mask...' : `${activeDetections.length} instansi`}
                            </span>
                          </div>

                          <div
                            className={`research-zoom-viewport is-enlarged ${zoom > 1 ? (isPanning ? 'is-grabbing' : 'is-grab') : ''}`}
                            onPointerDown={handlePointerDown}
                            onPointerMove={handlePointerMove}
                            onPointerUp={handlePointerUp}
                            onPointerCancel={handlePointerUp}
                            onClick={() => {
                              if (zoom === 1 && !isPanning) setShowLightbox(true)
                            }}
                          >
                            {isScanning && (
                              <div className="scan-overlay" role="status" aria-live="polite">
                                <div className="scan-beam" />
                                <span className="scan-pill">Memperbarui segmentasi &amp; transliterasi...</span>
                              </div>
                            )}

                            <div
                              className="research-zoom-transform"
                              style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
                            >
                              <div className="canvas-figure">
                                <img
                                  ref={imgRef}
                                  src={detectronRenderUrl || currentItem.src}
                                  alt={`Masukan citra dan segmentasi ${currentItem.label}`}
                                  width="1100"
                                  height="440"
                                  draggable={false}
                                  className="canvas-img is-large-canvas"
                                />

                                {!detectronRenderUrl && vizMode !== 'raw_image' && activeDetections.length > 0 && (
                                  <svg
                                    className="canvas-svg"
                                    viewBox="0 0 100 100"
                                    preserveAspectRatio="none"
                                  >
                                    {activeDetections.map((det) => {
                                      const detKey = det.instance_id ?? det.id
                                      const [x, y, w, h] = det.box
                                      const isSelected = activeCharId === detKey
                                      const maskColor = instanceColor(det.display_number ?? det.id)

                                      return (
                                        <g
                                          key={detKey}
                                          data-det-hit="true"
                                          className="svg-det-group"
                                          onClick={(ev) => {
                                            ev.stopPropagation()
                                            setActiveCharId((prev) => (prev === detKey ? null : detKey))
                                          }}
                                        >
                                          {showMask &&
                                            (det.polygons?.length > 0 ? (
                                              det.polygons.map((poly, pi) => (
                                                <polygon
                                                  key={pi}
                                                  points={poly.map((pt) => `${pt[0]},${pt[1]}`).join(' ')}
                                                  fill={maskColor}
                                                  fillOpacity={
                                                    isSelected ? Math.min(0.85, maskOpacity + 0.18) : maskOpacity
                                                  }
                                                />
                                              ))
                                            ) : (
                                              <ellipse
                                                cx={x + w / 2}
                                                cy={y + h / 2}
                                                rx={w / 2}
                                                ry={h / 2}
                                                fill={maskColor}
                                                fillOpacity={
                                                  isSelected ? Math.min(0.85, maskOpacity + 0.18) : maskOpacity
                                                }
                                              />
                                            ))}
                                          {showBoxes && (
                                            <rect
                                              x={x}
                                              y={y}
                                              width={w}
                                              height={h}
                                              rx="0.6"
                                              fill="transparent"
                                              stroke={isSelected ? maskColor : '#AF3131'}
                                              strokeWidth={isSelected ? '1.3' : '0.68'}
                                            />
                                          )}
                                          {showLabels && (
                                            <text
                                              x={x}
                                              y={Math.max(4, y - 1.5)}
                                              fill="#0F172A"
                                              fontSize="3.1"
                                              fontWeight="700"
                                            >
                                              #{det.display_number ?? det.id}
                                            </text>
                                          )}
                                        </g>
                                      )
                                    })}
                                  </svg>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </section>
                </FadeUp>

                <FadeUp delay={0.07} className="studio-inspector-col">
                  <section className="panel pt-paper studio-inspector-panel" aria-labelledby="telemetry-heading">
                    <div className="panel-header">
                      <span className="panel-kicker">02 · TELEMETRI DETEKSI, TRANSLITERASI, &amp; EKSPOR</span>
                      <h2 id="telemetry-heading" className="panel-title">
                        Keluaran Unit &amp; Prediksi Asli
                      </h2>
                    </div>

                    {!currentItem ? (
                      <p className="empty-desc">Pilih citra untuk menampilkan rincian instansi.</p>
                    ) : currentItem.readingStatus === 'NO_PREDICTIONS' ? (
                      <div className="state-notice is-warn">
                        <div className="state-notice-head">
                          <IconAlertNotice size={16} />
                          <span>0 Deteksi Lolos Threshold 0,50</span>
                        </div>
                        <p className="state-notice-desc">
                          Model tidak mendeteksi karakter yang memenuhi ambang keyakinan. Status transliterasi: NO_PREDICTIONS.
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="lab-kpi-grid">
                          <div className="lab-kpi-card">
                            <span className="lab-kpi-label">Total Unit</span>
                            <strong className="lab-kpi-val">{activeDetections.length}</strong>
                          </div>
                          <div className="lab-kpi-card">
                            <span className="lab-kpi-label">Ina ni Surat</span>
                            <strong className="lab-kpi-val">{inaCount}</strong>
                          </div>
                          <div className="lab-kpi-card">
                            <span className="lab-kpi-label">Anak ni Surat</span>
                            <strong className="lab-kpi-val">{anakCount}</strong>
                          </div>
                        </div>

                        <div className="spacing-split-box">
                          <div className="spacing-row">
                            <span className="spacing-key">Transliterasi otomatis:</span>
                            <strong className="spacing-val is-selectable">
                              {displayReading(currentItem.rawLatinText) || '(kosong)'}
                            </strong>
                          </div>
                          <div className="spacing-row">
                            <span className="spacing-key">Usulan spasi ({spacingMeta.code}):</span>
                            <strong className="spacing-val is-selectable">
                              {displayReading(currentItem.wordSpacing?.suggested_text || currentItem.rawLatinText || '-')}
                            </strong>
                          </div>
                          <div className="spacing-row">
                            <span className="spacing-key">Bacaan literal:</span>
                            <code className="spacing-val mono is-selectable">
                              {displayReading(currentItem.literalText) || '-'}
                            </code>
                          </div>
                        </div>

                        {unresolvedReadingUnits(currentItem).length > 0 && (
                          <div className="detail-focus-box" role="note">
                            <strong>Bagian yang belum terbaca:</strong>
                            <ul>{unresolvedReadingUnits(currentItem).map((u) => (
                              <li key={`${u.line_number}-${u.unit_number}`}>
                                Baris {u.line_number}, unit {u.unit_number}, ID {(u.source_instance_ids || []).join(', ')}: {(u.reasons || []).join(' ')}
                              </li>
                            ))}</ul>
                          </div>
                        )}
                        {activeDetection && (
                          <div className="detail-focus-box">
                            <span className="lab-detail-kicker">UNIT TERPILIH PADA KANVAS / TABEL</span>
                            <p className="detail-focus-text">
                              <strong>
                                No.{activeDetection.display_number ?? activeDetection.id} (ID {activeDetection.instance_id ?? activeDetection.id}) · {activeDetection.rawClass || activeDetection.cls}
                              </strong>{' '}
                              · Jenis {activeDetection.kind} · Confidence{' '}
                              <strong>{(activeDetection.score * 100).toFixed(1)}%</strong>
                            </p>
                          </div>
                        )}

                        {currentItem.overlappingCandidates?.length > 0 && (
                          <div className="overlap-box">
                            <span className="overlap-title">Kandidat Pembacaan</span>
                            {currentItem.overlappingCandidates.map((grp) => (
                              <div key={grp.groupId} className="overlap-item">
                                <strong>
                                  {grp.groupId} ({grp.selectionStatus}):
                                </strong>{' '}
                                {grp.chosen
                                  ? `dipilih ${grp.chosen.cls} (${Math.round(grp.chosen.score * 100)}%)`
                                  : 'skor seri'}
                                {' · '}
                                {grp.alternatives
                                  .map((a) => `${a.cls} (${Math.round(a.score * 100)}%)`)
                                  .join(', ')}
                              </div>
                            ))}
                          </div>
                        )}

                        {activeDetections.length > 0 && (
                          <div className="table-wrap studio-table-wrap">
                            <table className="char-table">
                              <thead>
                                <tr>
                                  <th>No.</th>
                                  <th>Kelas</th>
                                  <th>Jenis</th>
                                  <th>Conf.</th>
                                </tr>
                              </thead>
                              <tbody>
                                {activeDetections.map((det) => {
                                  const detKey = det.instance_id ?? det.id
                                  const isSel = activeCharId === detKey
                                  return (
                                    <tr
                                      key={detKey}
                                      className={isSel ? 'is-highlighted' : ''}
                                      onClick={() =>
                                        setActiveCharId((prev) => (prev === detKey ? null : detKey))
                                      }
                                    >
                                      <td className="mono">#{det.display_number ?? det.id}</td>
                                      <td>
                                        <strong>{det.rawClass || det.cls}</strong>{' '}
                                        <span className="mono">(ID {det.instance_id ?? det.id})</span>
                                      </td>
                                      <td>
                                        <span
                                          className={`badge-kind ${det.kind === 'Ina' ? 'is-ina' : ''}`}
                                        >
                                          {det.kind}
                                        </span>
                                      </td>
                                      <td className="mono">{(det.score * 100).toFixed(1)}%</td>
                                    </tr>
                                  )
                                })}
                              </tbody>
                            </table>
                          </div>
                        )}

                        <div className="studio-export-bar">
                          <span className="lab-detail-kicker">EKSPOR PENELITIAN &amp; TRANSLITERASI</span>
                          <div className="export-group">
                            <button type="button" className="btn-secondary" onClick={handleDownloadOverlayPng}>
                              <IconDownloadFile size={15} />
                              <span>Overlay PNG</span>
                            </button>
                            <button type="button" className="btn-secondary" onClick={handleDownloadJsonPredictions}>
                              <IconDownloadFile size={15} />
                              <span>Prediksi JSON</span>
                            </button>
                            <button type="button" className="btn-secondary" onClick={handleDownloadCsv}>
                              <IconDownloadFile size={15} />
                              <span>Karakter CSV</span>
                            </button>
                            <button
                              type="button"
                              className="btn-secondary"
                              disabled={!currentItem.transliteration}
                              onClick={() =>
                                triggerDownload(
                                  `${currentItem.id}_transliterasi.txt`,
                                  buildTransliterationTxt(currentItem),
                                  'text/plain;charset=utf-8',
                                )
                              }
                            >
                              <IconDownloadFile size={15} />
                              <span>Transliterasi TXT</span>
                            </button>
                            <button
                              type="button"
                              className="btn-secondary"
                              disabled={!currentItem.transliteration}
                              onClick={() =>
                                triggerDownload(
                                  `${currentItem.id}_transliterasi.json`,
                                  buildTransliterationJson(currentItem),
                                  'application/json;charset=utf-8',
                                )
                              }
                            >
                              <IconDownloadFile size={15} />
                              <span>Transliterasi JSON</span>
                            </button>
                          </div>
                        </div>
                      </>
                    )}
                  </section>
                </FadeUp>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="tab-evaluation"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.22, ease: EASE_OUT }}
              className="studio-container-stack"
            >
              <section className="panel pt-paper eval-section-card" aria-labelledby="backbone-comp-title">
                <div className="panel-header panel-header-inline">
                  <div>
                    <span className="panel-kicker">01 · KOMPARASI BACKBONE &amp; RINCIAN PENGUJIAN</span>
                    <h2 id="backbone-comp-title" className="panel-title">
                      Evaluasi ResNet-50 vs ResNet-101 pada Protokol 30 Epoch
                    </h2>
                  </div>
                  <div className="toggle-group" role="tablist" aria-label="Pilih arsitektur backbone">
                    <button
                      type="button"
                      role="tab"
                      aria-selected={selectedBackbone === 'r50'}
                      className={`chip-toggle ${selectedBackbone === 'r50' ? 'is-on' : ''}`}
                      onClick={() => setSelectedBackbone('r50')}
                    >
                      ResNet-50 (Aktif)
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={selectedBackbone === 'r101'}
                      className={`chip-toggle ${selectedBackbone === 'r101' ? 'is-on' : ''}`}
                      onClick={() => setSelectedBackbone('r101')}
                    >
                      ResNet-101 (Pembanding)
                    </button>
                  </div>
                </div>

                <div className="eval-backbone-grid">
                  <div className="eval-backbone-summary">
                    <span className="eval-chip">{profile.badge}</span>
                    <h3>{profile.name}</h3>
                    <p>{profile.summary}</p>
                    <div className="eval-bar-compare">
                      <div className="eval-bar-row">
                        <span>Validasi AP50:95 R50 Ep.28</span>
                        <div className="eval-bar-track">
                          <div className="eval-bar-fill is-primary" style={{ width: '68.34%' }} />
                        </div>
                        <strong>68,34%</strong>
                      </div>
                      <div className="eval-bar-row">
                        <span>Validasi AP50:95 R101 Ep.25</span>
                        <div className="eval-bar-track">
                          <div className="eval-bar-fill is-accent" style={{ width: '68.19%' }} />
                        </div>
                        <strong>68,19%</strong>
                      </div>
                    </div>
                  </div>

                  <div className="eval-breakdown-grid">
                    {profile.breakdown.map((row) => (
                      <div key={row.label} className={`eval-stat-tile is-${row.tone}`}>
                        <span className="eval-stat-label">{row.label}</span>
                        <strong className="eval-stat-val">{row.value}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              <section className="panel pt-paper eval-section-card" aria-labelledby="dl-pipeline-title">
                <div className="panel-header">
                  <span className="panel-kicker">02 · ARSITEKTUR PIPELINE MODEL</span>
                  <h2 id="dl-pipeline-title" className="panel-title">
                    Alur Mask R-CNN &amp; Decoder Spasial Aksara Batak Toba
                  </h2>
                </div>

                <div className="eval-stage-tabs" role="tablist">
                  {PIPELINE_STAGES.map((st) => {
                    const isAct = st.step === activeStage
                    return (
                      <button
                        key={st.step}
                        type="button"
                        role="tab"
                        aria-selected={isAct}
                        className={`eval-stage-btn ${isAct ? 'is-active' : ''}`}
                        onClick={() => setActiveStage(st.step)}
                      >
                        <span className="eval-stage-num">{st.step}</span>
                        <span className="eval-stage-name">{st.layer}</span>
                      </button>
                    )
                  })}
                </div>

                <div className="eval-stage-detail">
                  <span className="eval-chip">Tahap {currentStage.step}</span>
                  <h3>{currentStage.layer}</h3>
                  <p>{currentStage.detail}</p>
                </div>
              </section>

              <div className="eval-two-col">
                <section className="panel pt-paper panel-stretch" aria-labelledby="split-dist-title">
                  <div className="panel-header">
                    <span className="panel-kicker">03 · KOMPOSISI DATASET (1.535 CITRA / 4.088 INSTANSI)</span>
                    <h2 id="split-dist-title" className="panel-title">
                      Pembagian Data Latih, Validasi, dan Uji
                    </h2>
                  </div>
                  <div className="eval-split-list">
                    {DATASET_SPLITS.map((item) => (
                      <div key={item.split} className="eval-split-row">
                        <div className="eval-split-top">
                          <strong>{item.split}</strong>
                          <span>{item.images} · {item.instances}</span>
                        </div>
                        <div className="eval-bar-track">
                          <div className="eval-bar-fill is-primary" style={{ width: `${item.share}%` }} />
                        </div>
                        <p className="eval-split-note">{item.note}</p>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="panel pt-paper panel-stretch" aria-labelledby="err-profile-title">
                  <div className="panel-header">
                    <span className="panel-kicker">04 · PROFIL UJI 131 CITRA</span>
                    <h2 id="err-profile-title" className="panel-title">
                      Distribusi Kelompok Kasus pada Himpunan Uji
                    </h2>
                  </div>
                  <div className="eval-split-list">
                    {ERROR_GROUPS.map((grp) => (
                      <div key={grp.label} className="eval-split-row">
                        <div className="eval-split-top">
                          <strong>{grp.label}</strong>
                          <span>{grp.count} / {grp.total} citra</span>
                        </div>
                        <div className="eval-bar-track">
                          <div
                            className="eval-bar-fill is-accent"
                            style={{ width: `${Math.round((grp.count / grp.total) * 100)}%` }}
                          />
                        </div>
                        <p className="eval-split-note">{grp.desc}</p>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Modal Perbesar Layar Penuh (Lightbox) */}
      <AnimatePresence>
        {showLightbox && currentItem && (
          <motion.div
            className="lightbox-backdrop"
            role="dialog"
            aria-modal="true"
            aria-label="Tampilan perbesar overlay segmentasi"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowLightbox(false)}
          >
            <button
              type="button"
              className="lightbox-close-btn"
              onClick={() => setShowLightbox(false)}
            >
              Tutup (ESC)
            </button>
            <img
              src={detectronRenderUrl || currentItem.src}
              alt={`Perbesar overlay ${currentItem.label}`}
              className="lightbox-img"
              onClick={(e) => e.stopPropagation()}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
