import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import UploadPanel from '../components/UploadPanel.jsx'
import AksaraDriftBackdrop from '../components/AksaraDriftBackdrop.jsx'
import PipelineHub from '../components/PipelineHub.jsx'
import {
  buildTransliterationTxt,
  describePublicReadingNote,
  formatAksaraLabel,
  displayReading,
  unresolvedReadingUnits,
} from '../utils/transliterationAdapter.js'
import {
  BrushHighlight,
  EASE_OUT,
  FadeUp,
  InteractiveWaveLine,
  MagneticWrap,
  RiseLines,
  WordReveal,
} from '../components/MotionPrimitives.jsx'
import {
  IconCheckMark,
  IconCopySheet,
  IconDownloadFile,
  IconEditPen,
  IconExpandZoom,
} from '../components/Icons.jsx'

export default function PublicReaderPage({
  samples,
  currentItem,
  isScanning,
  apiError,
  onDismissError,
  onSelectSample,
  onUploadFile,
  onUpdateCurrentImage,
  onResetOriginalImage,
  onRunReadScript,
  onClearSelection,
  onOpenGuide,
  onOpenPhotoGuide,
  onNotify,
}) {
  const [copiedType, setCopiedType] = useState('')
  const [largeReading, setLargeReading] = useState(false)
  const [selectedSyllableId, setSelectedSyllableId] = useState(null)
  const [isEditingReading, setIsEditingReading] = useState(false)
  const [editedReading, setEditedReading] = useState('')
  const [showImageModal, setShowImageModal] = useState(false)

  const copyTimerRef = useRef(null)

  useEffect(() => {
    setSelectedSyllableId(null)
    setCopiedType('')
    setIsEditingReading(false)
    setEditedReading('')
    setShowImageModal(false)
    if (copyTimerRef.current) {
      clearTimeout(copyTimerRef.current)
      copyTimerRef.current = null
    }
  }, [currentItem?.id, currentItem?.rawLatinText])

  useEffect(() => {
    return () => {
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current)
    }
  }, [])

  useEffect(() => {
    if (!showImageModal) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') setShowImageModal(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [showImageModal])

  const selectedSyllable = currentItem?.syllables?.find((s) => s.id === selectedSyllableId)
  const highlightedCharIds = new Set(selectedSyllable ? selectedSyllable.charIds : [])

  const detToSyllableId = new Map()
  for (const syl of currentItem?.syllables || []) {
    for (const cid of syl.charIds || []) {
      detToSyllableId.set(cid, syl.id)
    }
  }

  const handleCopyText = async (textToCopy, typeKey, toastMessage = 'Teks bacaan tersalin') => {
    try {
      await navigator.clipboard.writeText(textToCopy || '')
      setCopiedType(typeKey)
      onNotify?.(toastMessage)
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current)
      copyTimerRef.current = setTimeout(() => {
        setCopiedType('')
        copyTimerRef.current = null
      }, 2000)
    } catch {
      setCopiedType('')
    }
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

  const handleDownloadTxt = (customEdit = '') => {
    if (!currentItem) return
    const suffix = customEdit ? '_suntingan.txt' : '_transliterasi.txt'
    triggerDownload(
      `${currentItem.id}${suffix}`,
      buildTransliterationTxt(currentItem, customEdit),
      'text/plain;charset=utf-8',
    )
    onNotify?.(customEdit ? 'Berkas TXT suntingan diunduh' : 'Berkas TXT bacaan diunduh')
  }

  const isNoPredictions = currentItem?.readingStatus === 'NO_PREDICTIONS'
  const hasModuleOutput = Boolean(currentItem?.transliteration)
  const autoDisplayText = displayReading(currentItem?.rawLatinText || '')
  const suggestedText = displayReading(currentItem?.wordSpacing?.suggested_text || '')
  const hasDistinctSpacing = Boolean(suggestedText) && suggestedText !== autoDisplayText
  const hasUserEdit = Boolean(editedReading.trim()) && editedReading.trim() !== autoDisplayText.trim()

  const handleOpenEdit = () => {
    setIsEditingReading((prev) => {
      const next = !prev
      if (next && !editedReading) {
        setEditedReading(hasDistinctSpacing ? suggestedText : autoDisplayText)
      }
      return next
    })
  }

  const getCanvasStatusHint = () => {
    if (isScanning) return 'Sedang membaca tulisan aksara...'
    if (!hasModuleOutput) return 'Tekan tombol "Baca Aksara" di panel kiri untuk memproses gambar'
    if (highlightedCharIds.size > 0 && selectedSyllable) {
      return `Menyorot suku kata "${displayReading(selectedSyllable.text)}" pada gambar`
    }
    if (currentItem?.syllables?.length > 0) {
      return 'Klik gambar aksara atau tombol suku kata di bawah untuk menyorot letaknya'
    }
    return 'Belum ada aksara yang terdeteksi pada gambar ini'
  }

  const renderInteractiveFigure = (isModal = false) => {
    const hasInteractiveOverlay = hasModuleOutput && (currentItem?.detections?.length || 0) > 0
    return (
      <div className={`canvas-figure ${isModal ? 'is-modal-figure' : ''}`}>
        <img
          ref={(el) => {
            if (el && !isModal) el.setAttribute('fetchpriority', 'high')
          }}
          src={currentItem.src}
          alt={`Citra aksara ${currentItem.publicLabel || currentItem.label}`}
          width="640"
          height="240"
          className={`canvas-img ${isModal ? 'is-modal-img' : ''}`}
        />

        {hasInteractiveOverlay && (
          <svg
            className={`canvas-svg ${highlightedCharIds.size > 0 ? 'has-highlight' : ''}`}
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-label="Area interaktif aksara pada gambar"
          >
            {currentItem.detections.map((det) => {
              const detId = det.instance_id ?? det.id
              const linkedSylId = detToSyllableId.get(detId) || null
              const isHighlighted = highlightedCharIds.has(detId)
              const [x, y, w, h] = det.box || [0, 0, 0, 0]

              const onToggleDet = () => {
                if (!linkedSylId) return
                setSelectedSyllableId((prev) => (prev === linkedSylId ? null : linkedSylId))
              }

              if (det.polygons?.length > 0) {
                return det.polygons.map((poly, pi) => (
                  <polygon
                    key={`${detId}-${pi}`}
                    points={poly.map((pt) => `${pt[0]},${pt[1]}`).join(' ')}
                    className={`canvas-hit-region ${linkedSylId ? 'is-clickable' : ''} ${isHighlighted ? 'is-highlighted' : ''}`}
                    fill={isHighlighted ? 'var(--primary)' : 'transparent'}
                    fillOpacity={isHighlighted ? '0.28' : '0'}
                    stroke={isHighlighted ? 'var(--primary)' : 'transparent'}
                    strokeWidth={isHighlighted ? '1.2' : '0.8'}
                    onClick={onToggleDet}
                  />
                ))
              }
              return (
                <rect
                  key={detId}
                  x={x}
                  y={y}
                  width={w}
                  height={h}
                  rx="1.2"
                  className={`canvas-hit-region ${linkedSylId ? 'is-clickable' : ''} ${isHighlighted ? 'is-highlighted' : ''}`}
                  fill={isHighlighted ? 'var(--primary)' : 'transparent'}
                  fillOpacity={isHighlighted ? '0.24' : '0'}
                  stroke={isHighlighted ? 'var(--primary)' : 'transparent'}
                  strokeWidth={isHighlighted ? '1.2' : '0.8'}
                  onClick={onToggleDet}
                />
              )
            })}
          </svg>
        )}
      </div>
    )
  }

  return (
    <div className="public-flow">
      <section className="hero-band">
        <div className="hero-gorga-bg" aria-hidden="true" />
        <AksaraDriftBackdrop variant="hero" />

        <div className="hero-band-inner">
          <div className="hero-text-col">
            <span className="hero-kicker">PUSTAKA DIGITAL AKSARA BATAK TOBA</span>
            <h1 className="hero-display-title">
              <RiseLines
                lines={[
                  'Baca Aksara Batak Toba',
                  <span key="brush-line">
                    dalam <BrushHighlight>Kalimat Latin</BrushHighlight>
                  </span>,
                ]}
              />
            </h1>
            <p className="hero-lead">
              Baca tulisan tangan Aksara Batak Toba dalam huruf Latin. Unggah foto tulisan Anda, lalu lihat hasil bacaan, susunan suku kata, dan salin teksnya dengan mudah.
            </p>
            <div className="hero-actions">
              <MagneticWrap>
                <a href="#area-baca-aksara" className="btn-curtain btn-primary-read">
                  <span className="btn-curtain-bg" aria-hidden="true" />
                  <span className="btn-curtain-label">Mulai Baca Aksara</span>
                </a>
              </MagneticWrap>
              <button type="button" className="btn-text-action" onClick={onOpenPhotoGuide}>
                Tips Foto yang Jelas
              </button>
            </div>
          </div>
        </div>

        <InteractiveWaveLine />
      </section>

      <div id="area-baca-aksara" className="workspace-section">
        {apiError && (
          <div className="error-banner" role="alert" style={{ marginBottom: 16 }}>
            <span>{apiError}</span>
            <button type="button" className="btn-dismiss" onClick={onDismissError}>
              Tutup
            </button>
          </div>
        )}

        <div className="workspace-grid">
          <FadeUp className="grid-col-stretch">
            <UploadPanel
              samples={samples}
              activeId={currentItem?.id || ''}
              currentItem={currentItem}
              isScanning={isScanning}
              showSimulationControls={false}
              onSelectSample={onSelectSample}
              onUploadFile={onUploadFile}
              onUpdateCurrentImage={onUpdateCurrentImage}
              onResetOriginalImage={onResetOriginalImage}
              onRunReadScript={onRunReadScript}
              onClearSelection={onClearSelection}
            />
          </FadeUp>

          <FadeUp delay={0.08} className="grid-col-stretch">
            <section className="panel pt-paper panel-stretch" aria-labelledby="public-result-title">
              <div className="panel-header panel-header-inline">
                <div>
                  <span className="panel-kicker">02 · HASIL PEMBACAAN AKSARA</span>
                  <h2 id="public-result-title" className="panel-title">
                    Hasil Bacaan Huruf Latin
                  </h2>
                </div>
              </div>

              {!currentItem ? (
                <div className="empty-state">
                  <p className="empty-title">Belum ada citra aksara yang dipilih</p>
                  <p className="empty-desc">
                    Unggah foto tulisan Aksara Batak Toba di sebelah kiri atau muat contoh citra pertama.
                  </p>
                  <button
                    type="button"
                    className="btn-curtain btn-primary-read"
                    onClick={() => onSelectSample(samples[0])}
                  >
                    <span className="btn-curtain-bg" aria-hidden="true" />
                    <span className="btn-curtain-label">Muat Contoh Citra Pertama</span>
                  </button>
                </div>
              ) : (
                <>
                  <div className="canvas-stage">
                    <div className="canvas-toolbar">
                      <span className="canvas-name-tag">
                        Citra: <strong>{currentItem.publicLabel || currentItem.label}</strong>
                      </span>
                      <div className="canvas-toolbar-right">
                        <span className="canvas-status-hint">{getCanvasStatusHint()}</span>
                        {highlightedCharIds.size > 0 && (
                          <button
                            type="button"
                            className="btn-inline-copy"
                            onClick={() => setSelectedSyllableId(null)}
                          >
                            Hapus sorotan
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn-inline-copy btn-zoom-trigger"
                          onClick={() => setShowImageModal(true)}
                        >
                          <IconExpandZoom size={14} />
                          <span>Perbesar</span>
                        </button>
                      </div>
                    </div>

                    <div className="canvas-inner">
                      {isScanning && (
                        <div className="scan-overlay" role="status" aria-live="polite">
                          <div className="scan-beam" />
                          <span className="scan-pill">Membaca aksara Batak Toba...</span>
                        </div>
                      )}

                      {renderInteractiveFigure(false)}
                    </div>
                  </div>

                  <div key={currentItem.id} className="reading-card reading-spotlight-card">
                    <div className="accent-rule" aria-hidden="true" />
                    <div className="reading-body">
                      <div className="reading-spotlight-stage">
                        <div className="reading-top">
                          <div className="reading-title-group">
                            <span className="reading-spotlight-eyebrow">
                              Hasil Transliterasi Huruf Latin
                            </span>
                          </div>

                          <div className="reading-actions">
                            <button
                              type="button"
                              className={`btn-size-toggle ${largeReading ? 'is-on' : ''}`}
                              aria-pressed={largeReading}
                              onClick={() => setLargeReading((v) => !v)}
                            >
                              {largeReading ? 'Huruf Normal' : 'Perbesar Huruf'}
                            </button>
                            <button
                              type="button"
                              className={`btn-size-toggle ${isEditingReading ? 'is-on' : ''}`}
                              disabled={!hasModuleOutput || isNoPredictions}
                              aria-pressed={isEditingReading}
                              onClick={handleOpenEdit}
                            >
                              <IconEditPen size={14} />
                              <span>{isEditingReading ? 'Tutup Sunting' : 'Sunting Bacaan'}</span>
                            </button>
                            <button
                              type="button"
                              className={`btn-copy ${copiedType === 'auto' ? 'is-copied' : ''}`}
                              disabled={!currentItem.rawLatinText}
                              onClick={() =>
                                handleCopyText(autoDisplayText, 'auto', 'Hasil bacaan otomatis tersalin')
                              }
                            >
                              {copiedType === 'auto' ? <IconCheckMark size={16} /> : <IconCopySheet size={16} />}
                              <span>{copiedType === 'auto' ? 'Tersalin' : 'Salin Teks'}</span>
                            </button>
                            <button
                              type="button"
                              className="btn-secondary"
                              disabled={!hasModuleOutput}
                              onClick={() => handleDownloadTxt('')}
                            >
                              <IconDownloadFile size={15} />
                              <span>Unduh TXT</span>
                            </button>
                          </div>
                        </div>

                        {!hasModuleOutput ? (
                          <div className="reading-heroic-output is-waiting">
                            <p className="empty-desc">
                              Citra siap dibaca. Tekan tombol <strong>Baca Aksara</strong> pada panel di sebelah kiri untuk menampilkan hasil transliterasinya.
                            </p>
                          </div>
                        ) : isNoPredictions ? (
                          <div className="reading-heroic-output">
                            <p className="reading-sentence is-empty-read">
                              {describePublicReadingNote('NO_PREDICTIONS')}
                            </p>
                          </div>
                        ) : (
                          <div className="reading-heroic-output selectable-reading-wrap">
                            <WordReveal
                              key={`${currentItem.id}-${isScanning ? 'scan' : 'ready'}`}
                              text={autoDisplayText}
                              className={`reading-sentence is-heroic is-selectable ${largeReading ? 'is-large' : ''}`}
                            />
                          </div>
                        )}
                      </div>

                      {hasModuleOutput && !isNoPredictions && (isEditingReading || hasUserEdit) && (
                        <div className="reading-edit-card" role="region" aria-label="Sunting dan bandingkan bacaan">
                          <div className="reading-edit-head">
                            <span className="reading-spotlight-eyebrow">
                              Sunting &amp; Bandingkan Bacaan
                            </span>
                            {hasUserEdit && !isEditingReading && (
                              <button
                                type="button"
                                className="btn-inline-copy"
                                onClick={() => setIsEditingReading(true)}
                              >
                                Ubah Suntingan
                              </button>
                            )}
                          </div>

                          <div className="reading-compare-grid">
                            <div className="reading-compare-row">
                              <span className="reading-compare-label">Hasil otomatis</span>
                              <span className="reading-compare-auto is-selectable">{autoDisplayText}</span>
                            </div>

                            <div className="reading-compare-row">
                              <label htmlFor="reading-edit-input" className="reading-compare-label">
                                Suntingan pengguna
                              </label>
                              {isEditingReading ? (
                                <textarea
                                  id="reading-edit-input"
                                  className="reading-edit-textarea"
                                  rows={2}
                                  value={editedReading}
                                  onChange={(e) => setEditedReading(e.target.value)}
                                  placeholder="Tulis pembetulan kata atau pemisahan spasi..."
                                />
                              ) : (
                                <strong className="reading-compare-edited is-selectable">
                                  {editedReading}
                                </strong>
                              )}
                            </div>
                          </div>

                          <div className="reading-edit-actions">
                            <button
                              type="button"
                              className={`btn-copy ${copiedType === 'edited' ? 'is-copied' : ''}`}
                              disabled={!editedReading.trim()}
                              onClick={() =>
                                handleCopyText(
                                  editedReading.trim(),
                                  'edited',
                                  `Suntingan "${editedReading.trim()}" tersalin`,
                                )
                              }
                            >
                              {copiedType === 'edited' ? <IconCheckMark size={16} /> : <IconCopySheet size={16} />}
                              <span>{copiedType === 'edited' ? 'Tersalin' : 'Salin Suntingan'}</span>
                            </button>
                            <button
                              type="button"
                              className="btn-secondary"
                              disabled={!editedReading.trim()}
                              onClick={() => handleDownloadTxt(editedReading.trim())}
                            >
                              <IconDownloadFile size={15} />
                              <span>Unduh TXT Suntingan</span>
                            </button>
                            <button
                              type="button"
                              className="btn-inline-copy"
                              onClick={() => setEditedReading(autoDisplayText)}
                            >
                              Reset
                            </button>
                            {isEditingReading && (
                              <button
                                type="button"
                                className="btn-inline-copy"
                                onClick={() => setIsEditingReading(false)}
                              >
                                Selesai
                              </button>
                            )}
                          </div>
                        </div>
                      )}

                      {hasModuleOutput && !isNoPredictions && currentItem.wordSpacing && hasDistinctSpacing && (
                        <div className="spacing-spotlight-box">
                          <div className="spacing-spotlight-head">
                            <span className="spacing-spotlight-label">
                              Perkiraan Pemisahan Kata
                            </span>
                            <button
                              type="button"
                              className="btn-inline-copy"
                              onClick={() =>
                                handleCopyText(suggestedText, 'spaced', 'Perkiraan pemisahan kata tersalin')
                              }
                            >
                              {copiedType === 'spaced' ? 'Tersalin' : 'Salin Pemisahan'}
                            </button>
                          </div>
                          <p className="spacing-spotlight-value is-selectable">
                            {suggestedText}
                          </p>
                          <p className="spacing-spotlight-hint">
                            Tulisan tradisional Batak Toba dirangkai tanpa spasi. Anda dapat membetulkan huruf atau spasi lewat tombol Sunting Bacaan di atas sambil tetap melihat hasil otomatisnya.
                          </p>
                        </div>
                      )}

                      {currentItem.syllables?.length > 0 && (
                        <div className="syllable-bar" aria-label="Urutan suku kata pembentuk bacaan">
                          <span className="syllable-bar-label">
                            Suku kata (klik untuk sorot pada gambar):
                          </span>
                          {currentItem.syllables.map((syl) => {
                            const isSelected = selectedSyllableId === syl.id
                            const friendlyParts = (syl.sourceLabels || [])
                              .map(formatAksaraLabel)
                              .filter(Boolean)
                            return (
                              <button
                                key={syl.id}
                                type="button"
                                className={`syllable-chip ${isSelected ? 'is-selected' : ''}`}
                                aria-pressed={isSelected}
                                onClick={() =>
                                  setSelectedSyllableId((prev) => (prev === syl.id ? null : syl.id))
                                }
                              >
                                <span>{displayReading(syl.text)}</span>
                                <span className="syllable-part">
                                  ({friendlyParts.join(' + ') || 'aksara'})
                                </span>
                              </button>
                            )
                          })}
                        </div>
                      )}

                      {unresolvedReadingUnits(currentItem).length > 0 && (
                        <div className="public-caution-note" role="note">
                          <div>
                            <strong>Bacaan belum lengkap pada bagian berikut:</strong>
                            <ul>{unresolvedReadingUnits(currentItem).map((u) => (
                              <li key={`${u.line_number}-${u.unit_number}`}>
                                Baris {u.line_number}, unit {u.unit_number}: {(u.reasons || []).join(' ')}
                              </li>
                            ))}</ul>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </section>
          </FadeUp>
        </div>
      </div>

      <PipelineHub onOpenGuide={onOpenGuide} />

      <AnimatePresence>
        {showImageModal && currentItem && (
          <motion.div
            className="modal-backdrop"
            role="dialog"
            aria-modal="true"
            aria-labelledby="zoom-preview-title"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => {
              if (e.target === e.currentTarget) setShowImageModal(false)
            }}
          >
            <motion.div
              className="modal-card pt-paper zoom-preview-modal"
              initial={{ opacity: 0, y: 14, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.98 }}
              transition={{ duration: 0.24, ease: EASE_OUT }}
            >
              <div className="modal-header">
                <div>
                  <span className="panel-kicker">PRATINJAU GAMBAR DIPERBESAR</span>
                  <h2 id="zoom-preview-title" className="modal-title">
                    {currentItem.publicLabel || currentItem.label}
                  </h2>
                </div>
                <button
                  type="button"
                  className="btn-text-action"
                  onClick={() => setShowImageModal(false)}
                >
                  Tutup (Esc)
                </button>
              </div>

              <p className="zoom-preview-hint">{getCanvasStatusHint()}</p>

              <div className="zoom-preview-stage">
                {renderInteractiveFigure(true)}
              </div>

              {currentItem.syllables?.length > 0 && (
                <div className="syllable-bar" style={{ marginTop: 12 }}>
                  <span className="syllable-bar-label">Pilih suku kata:</span>
                  {currentItem.syllables.map((syl) => {
                    const isSelected = selectedSyllableId === syl.id
                    return (
                      <button
                        key={syl.id}
                        type="button"
                        className={`syllable-chip ${isSelected ? 'is-selected' : ''}`}
                        aria-pressed={isSelected}
                        onClick={() =>
                          setSelectedSyllableId((prev) => (prev === syl.id ? null : syl.id))
                        }
                      >
                        <span>{displayReading(syl.text)}</span>
                      </button>
                    )
                  })}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
