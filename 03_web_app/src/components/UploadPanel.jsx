import { useEffect, useRef, useState } from 'react'
import { AnimatePresence } from 'motion/react'
import { IconManuscriptUpload, IconPlayRead } from './Icons.jsx'
import { MagneticWrap } from './MotionPrimitives.jsx'
import ImagePrepEditor from './ImagePrepEditor.jsx'

export default function UploadPanel({
  samples,
  activeId,
  currentItem,
  isScanning,
  simulationMode = 'normal',
  showSimulationControls = false,
  onChangeSimulationMode,
  onSelectSample,
  onUploadFile,
  onUpdateCurrentImage,
  onResetOriginalImage,
  onRunReadScript,
  onClearSelection,
}) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [showPrepEditor, setShowPrepEditor] = useState(false)

  useEffect(() => {
    setShowPrepEditor(false)
  }, [currentItem?.id])

  const validateAndSend = (files) => {
    const file = files?.[0]
    if (!file) return

    const validTypes = ['image/png', 'image/jpeg', 'image/webp']
    if (!validTypes.includes(file.type)) {
      setErrorMsg('Format berkas belum didukung. Pilih citra PNG, JPG, atau WEBP.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('Ukuran berkas melebihi batas 10 MB. Gunakan citra yang lebih ringkas.')
      return
    }

    setErrorMsg('')
    onUploadFile(file)
  }

  return (
    <section className="panel pt-paper panel-stretch" aria-labelledby="upload-panel-title">
      <div className="panel-header panel-header-inline">
        <div>
          <span className="panel-kicker">01 · MASUKAN CITRA</span>
          <h2 id="upload-panel-title" className="panel-title">
            Unggah atau Pilih Sampel
          </h2>
        </div>
        {currentItem && (
          <button
            type="button"
            className="btn-text-action"
            onClick={() => {
              setErrorMsg('')
              onClearSelection()
            }}
          >
            Kosongkan
          </button>
        )}
      </div>

      <div
        className={`dropzone ${isDragging ? 'is-dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setIsDragging(false)
          validateAndSend(e.dataTransfer.files)
        }}
      >
        <div className="dropzone-aksara-bg" aria-hidden="true">
          <img src="/imageweb/01_ina_a.png" alt="" />
          <img src="/imageweb/02_ina_ha.png" alt="" />
          <img src="/imageweb/06_ina_ba.png" alt="" />
          <img src="/imageweb/05_ina_ta.png" alt="" />
        </div>

        <input
          id="batak-file-input"
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          hidden
          onChange={(e) => {
            validateAndSend(e.target.files)
            e.target.value = ''
          }}
        />
        <div className="dropzone-content">
          <div className="dropzone-icon">
            <IconManuscriptUpload size={22} />
          </div>
          <p className="dropzone-title">
            {isDragging ? 'Lepaskan berkas citra di sini' : 'Unggah foto tulisan Aksara Batak Toba'}
          </p>
          <p className="dropzone-hint">
            Seret berkas ke area ini atau pilih dari perangkat (PNG, JPG, WEBP maks. 10 MB)
          </p>
          <button
            type="button"
            className="btn-secondary-upload"
            onClick={() => inputRef.current?.click()}
          >
            {currentItem ? 'Ganti Berkas Citra' : 'Pilih Berkas Citra'}
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="error-banner" role="alert">
          <span>{errorMsg}</span>
          <button
            type="button"
            className="btn-dismiss"
            onClick={() => setErrorMsg('')}
          >
            Tutup
          </button>
        </div>
      )}

      {currentItem && (
        <div className="file-ready-wrap">
          <div className="file-ready-box">
            <div className="file-ready-meta">
              <img
                src={currentItem.src}
                alt={`Pratinjau berkas ${currentItem.publicLabel || currentItem.label}`}
                width="60"
                height="44"
                className="file-ready-thumb"
              />
              <div className="file-ready-text">
                <span className="file-ready-name" title={currentItem.publicLabel || currentItem.label}>
                  {currentItem.publicLabel || currentItem.label}
                </span>
                <span className="file-ready-sub">{currentItem.publicSubtitle || currentItem.subtitle}</span>
              </div>
            </div>

            <div className="file-ready-actions">
              <button
                type="button"
                className={`btn-prep-toggle ${showPrepEditor ? 'is-active' : ''}`}
                onClick={() => setShowPrepEditor((v) => !v)}
              >
                {showPrepEditor ? 'Tutup Edit' : 'Putar / Potong'}
              </button>
              <MagneticWrap>
                <button
                  type="button"
                  className="btn-curtain btn-primary-read"
                  disabled={isScanning}
                  onClick={onRunReadScript}
                >
                  <span className="btn-curtain-bg" aria-hidden="true" />
                  <span className="btn-curtain-label">
                    <IconPlayRead size={16} />
                    <span>{isScanning ? 'Membaca...' : 'Baca Aksara'}</span>
                  </span>
                </button>
              </MagneticWrap>
            </div>
          </div>

          <AnimatePresence>
            {showPrepEditor && (
              <ImagePrepEditor
                src={currentItem.originalSrc || currentItem.src}
                label={currentItem.label}
                hasModified={Boolean(currentItem.originalSrc && currentItem.src !== currentItem.originalSrc)}
                onClose={() => setShowPrepEditor(false)}
                onResetOriginal={() => {
                  onResetOriginalImage?.()
                  setShowPrepEditor(false)
                }}
                onApply={(dataUrl, summaryNote) => {
                  onUpdateCurrentImage?.(dataUrl, summaryNote)
                  setShowPrepEditor(false)
                }}
              />
            )}
          </AnimatePresence>
        </div>
      )}

      <div className="samples-section">
        <div className="samples-header">
          <span className="samples-label">Atau coba langsung menggunakan contoh tulisan:</span>
        </div>
        <div className="samples-grid-balanced">
          {samples.map((item) => {
            const isActive = item.id === activeId
            return (
              <button
                key={item.id}
                type="button"
                className={`sample-btn ${isActive ? 'is-active' : ''}`}
                aria-pressed={isActive}
                onClick={() => {
                  setErrorMsg('')
                  onSelectSample(item)
                }}
              >
                <img
                  src={item.src}
                  alt={`Pratinjau ${item.publicLabel || item.label}`}
                  width="56"
                  height="40"
                  loading="lazy"
                  className="sample-thumb"
                />
                <span className="sample-meta">
                  <span className="sample-name">{item.publicLabel || item.label}</span>
                  <span className="sample-sub">{item.publicSubtitle || item.subtitle}</span>
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {showSimulationControls && (
        <div className="sim-mode-box">
          <label htmlFor="sim-mode-select" className="sim-mode-label">
            Simulasi kondisi keluaran modul (khusus uji antarmuka penelitian):
          </label>
          <select
            id="sim-mode-select"
            className="sim-mode-select"
            value={simulationMode}
            onChange={(e) => onChangeSimulationMode?.(e.target.value)}
          >
            <option value="normal">Normal: Bacaan & pasangan karakter tersedia</option>
            <option value="no_prediction">Kondisi 0 prediksi lolos threshold (0,50)</option>
            <option value="process_error">Kondisi proses inferensi gagal</option>
          </select>
        </div>
      )}
    </section>
  )
}
