import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, MotionConfig, motion } from 'motion/react'
import { MODEL_IDENTITY, SAMPLE_IMAGES } from './data/samples.js'
import {
  adaptApiPayloadToUiItem,
  fetchApiHealth,
  predictImageViaApi,
  predictSampleViaApi,
} from './utils/transliterationAdapter.js'
import SplashScreen from './components/SplashScreen.jsx'
import Navbar from './components/Navbar.jsx'
import PhotoGuideModal from './components/PhotoGuideModal.jsx'
import PublicReaderPage from './pages/PublicReaderPage.jsx'
import ResearchPage from './pages/ResearchPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import GuidePage from './pages/GuidePage.jsx'
import { EASE_OUT, RiseLines } from './components/MotionPrimitives.jsx'

const HISTORY_STORAGE_KEY = 'pt_session_history_v2'
const MAX_HISTORY_ITEMS = 8

function loadInitialHistory() {
  try {
    const raw = sessionStorage.getItem(HISTORY_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) return parsed
  } catch {
    // Abaikan jika sessionStorage tidak tersedia
  }
  return []
}

export default function App() {
  const [theme, setTheme] = useState('light')
  const [showSplash, setShowSplash] = useState(true)
  const [showPhotoGuide, setShowPhotoGuide] = useState(false)
  const [confirmClearOpen, setConfirmClearOpen] = useState(false)
  const [activePage, setActivePage] = useState('public')
  const [currentItem, setCurrentItem] = useState(null)
  const [sessionHistory, setSessionHistory] = useState(loadInitialHistory)
  const [isScanning, setIsScanning] = useState(false)
  const [backendStatus, setBackendStatus] = useState({
    connected: false,
    modelIdentity: null,
    moduleVersion: null,
    rulesVersion: null,
    lexiconFile: 'kosakata_toba_v2.json',
  })
  const [apiError, setApiError] = useState('')
  const [toastMsg, setToastMsg] = useState('')

  const scanTimerRef = useRef(null)
  const toastTimerRef = useRef(null)
  const objectUrlsRef = useRef(new Set())

  const showToast = (msg) => {
    if (!msg) return
    setToastMsg(msg)
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
    toastTimerRef.current = setTimeout(() => {
      setToastMsg('')
      toastTimerRef.current = null
    }, 2400)
  }

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => {
    if (!confirmClearOpen) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') setConfirmClearOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [confirmClearOpen])

  useEffect(() => {
    let active = true
    fetchApiHealth()
      .then((info) => {
        if (!active || !info?.ok) return
        setBackendStatus({
          connected: true,
          modelIdentity: info.model_identity || null,
          moduleVersion: info.module_version || null,
          rulesVersion: info.rules_version || null,
          lexiconFile: info.lexicon_file || 'kosakata_toba_v2.json',
        })
      })
      .catch(() => {
        // Mode offline tetap berjalan untuk inspeksi 4 sampel uji bawaan
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    return () => {
      if (scanTimerRef.current) clearTimeout(scanTimerRef.current)
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current)
      objectUrlsRef.current.forEach((url) => URL.revokeObjectURL(url))
      objectUrlsRef.current.clear()
    }
  }, [])

  const pushSessionHistory = (item) => {
    if (!item) return
    const entry = {
      ...item,
      viewedAt: new Date().toLocaleTimeString('id-ID', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    }
    setSessionHistory((prev) => {
      const filtered = prev.filter((p) => p.id !== entry.id)
      const next = [entry, ...filtered].slice(0, MAX_HISTORY_ITEMS)
      try {
        const serializable = next.filter(
          (x) => typeof x.src === 'string' && !x.src.startsWith('blob:') && x.src.length < 350000,
        )
        sessionStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(serializable))
      } catch {
        // Abaikan batas kuota sessionStorage
      }
      return next
    })
  }

  const triggerScanTransition = (nextItem, recordHistory = true) => {
    if (scanTimerRef.current) clearTimeout(scanTimerRef.current)
    setIsScanning(true)
    if (nextItem !== undefined) {
      setCurrentItem(nextItem)
      if (recordHistory && nextItem) {
        pushSessionHistory(nextItem)
      }
    }
    scanTimerRef.current = setTimeout(() => {
      setIsScanning(false)
      scanTimerRef.current = null
    }, 420)
  }

  const runLivePrediction = async (baseItem, extraMeta = {}) => {
    if (!baseItem?.src) return
    if (scanTimerRef.current) clearTimeout(scanTimerRef.current)
    setApiError('')
    setIsScanning(true)
    try {
      const apiPayload = await predictImageViaApi({
        filename: baseItem.sourceName || baseItem.label || 'unggahan.png',
        imageSrc: baseItem.src,
      })
      setBackendStatus((prev) => ({
        ...prev,
        connected: true,
        modelIdentity: apiPayload.model_identity || prev.modelIdentity,
        moduleVersion: apiPayload.transliteration?.version || prev.moduleVersion,
        rulesVersion: apiPayload.transliteration?.rules_version || prev.rulesVersion,
      }))
      const updated = adaptApiPayloadToUiItem(apiPayload, {
        id: extraMeta.id || baseItem.id,
        label: extraMeta.label || baseItem.label,
        publicLabel: extraMeta.publicLabel || baseItem.publicLabel,
        subtitle: extraMeta.subtitle,
        src: baseItem.src,
        originalSrc: baseItem.originalSrc || baseItem.src,
        isLiveInference: true,
      })
      setCurrentItem(updated)
      pushSessionHistory(updated)
    } catch (err) {
      const msg = err?.message || 'Gagal terhubung ke server inferensi Python.'
      setApiError(
        `${msg} Pastikan API backend berjalan di WSL (.venv-web) melalui JALANKAN_API_BACKEND.cmd atau python jalankan_api.py pada port 8503.`,
      )
    } finally {
      setIsScanning(false)
    }
  }

  const handleSelectSample = async (sample) => {
    setApiError('')
    triggerScanTransition(sample, true)
    try {
      const apiPayload = await predictSampleViaApi(sample.id)
      const fresh = adaptApiPayloadToUiItem(apiPayload, {
        id: sample.id,
        label: sample.label,
        publicLabel: sample.publicLabel,
        src: sample.src,
        originalSrc: sample.originalSrc || sample.src,
        isLiveInference: true,
      })
      setBackendStatus((prev) => ({
        ...prev,
        connected: true,
        modelIdentity: apiPayload.model_identity || prev.modelIdentity,
        moduleVersion: apiPayload.transliteration?.version || prev.moduleVersion,
        rulesVersion: apiPayload.transliteration?.rules_version || prev.rulesVersion,
      }))
      setCurrentItem(fresh)
      pushSessionHistory(fresh)
    } catch {
      // Tetap gunakan sampel 0.4.4 lokal jika server API belum berjalan
    }
  }

  const handleSelectHistoryItem = (historyItem) => {
    setApiError('')
    triggerScanTransition(historyItem, true)
  }

  const handleRequestClearHistory = () => {
    if (sessionHistory.length > 0) setConfirmClearOpen(true)
  }

  const handleConfirmClearHistory = () => {
    setSessionHistory([])
    try {
      sessionStorage.removeItem(HISTORY_STORAGE_KEY)
    } catch {
      // Abaikan
    }
    setConfirmClearOpen(false)
    showToast('Riwayat bacaan dibersihkan')
  }

  const handleUploadFile = (file) => {
    const objectUrl = URL.createObjectURL(file)
    objectUrlsRef.current.add(objectUrl)
    setApiError('')

    const customItem = {
      id: `UNGGAHAN_${Date.now()}`,
      label: file.name,
      publicLabel: file.name,
      sourceName: file.name,
      subtitle: 'Pratinjau siap - klik Baca Aksara untuk memproses',
      publicSubtitle: 'Siap dibaca - klik Baca Aksara',
      src: objectUrl,
      originalSrc: objectUrl,
      rawLatinText: '',
      latinText: '',
      literalText: '',
      spacingStatus: 'Menunggu tombol Baca Aksara',
      spacingStatusCode: 'NEEDS_REVIEW',
      wordSpacing: null,
      readingStatus: 'READY',
      warnings: [],
      issues: [],
      overlappingCandidates: [],
      unpairedAssignments: [],
      syllables: [],
      detections: [],
      transliteration: null,
      modelIdentity: backendStatus.modelIdentity || null,
      isLiveInference: false,
    }
    setCurrentItem(customItem)
  }

  const handleUpdateCurrentImage = (dataUrl, summaryNote) => {
    if (!currentItem) return
    const updatedItem = {
      ...currentItem,
      originalSrc: currentItem.originalSrc || currentItem.src,
      src: dataUrl,
      subtitle: `${summaryNote || 'Citra disesuaikan'} - klik Baca Aksara untuk memproses`,
      rawLatinText: '',
      latinText: '',
      literalText: '',
      wordSpacing: null,
      syllables: [],
      detections: [],
      transliteration: null,
      warnings: [],
      issues: [],
      overlappingCandidates: [],
      unpairedAssignments: [],
      cacheKey: null,
      isLiveInference: false,
    }
    setCurrentItem(updatedItem)
  }

  const handleResetOriginalImage = () => {
    if (!currentItem || !currentItem.originalSrc) return
    const origSample = SAMPLE_IMAGES.find((s) => s.id === currentItem.id)
    if (origSample) {
      handleSelectSample(origSample)
      return
    }
    const restored = {
      ...currentItem,
      src: currentItem.originalSrc,
      subtitle: 'Citra asli dipulihkan - klik Baca Aksara untuk memproses',
      detections: [],
      transliteration: null,
      rawLatinText: '',
      latinText: '',
      literalText: '',
      wordSpacing: null,
      syllables: [],
      cacheKey: null,
    }
    setCurrentItem(restored)
  }

  const handleRunReadScript = async () => {
    if (!currentItem) return
    await runLivePrediction(currentItem)
  }

  const handleClearSelection = () => {
    if (scanTimerRef.current) clearTimeout(scanTimerRef.current)
    setApiError('')
    setIsScanning(false)
    setCurrentItem(null)
  }

  const handleNavigate = (pageId) => {
    setActivePage(pageId)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const effectiveModelIdentity = currentItem?.modelIdentity || backendStatus.modelIdentity || {
    architecture: MODEL_IDENTITY.architecture,
    backbone_depth: MODEL_IDENTITY.backboneDepth,
    epoch: MODEL_IDENTITY.epoch,
  }

  return (
    <MotionConfig reducedMotion="user">
      <div className="app-shell">
        <AnimatePresence>
          {showSplash && <SplashScreen onComplete={() => setShowSplash(false)} />}
        </AnimatePresence>

        <AnimatePresence>
          {showPhotoGuide && <PhotoGuideModal onClose={() => setShowPhotoGuide(false)} />}
        </AnimatePresence>

        <a href="#ruang-kerja" className="skip-link">
          Langsung ke konten utama
        </a>
        <div className="accent-rule" aria-hidden="true" />

        <Navbar
          activePage={activePage}
          onNavigate={handleNavigate}
          onOpenPhotoGuide={() => setShowPhotoGuide(true)}
          theme={theme}
          onSetTheme={setTheme}
          historyCount={sessionHistory.length}
          onRequestClearHistory={handleRequestClearHistory}
          onReplaySplash={() => setShowSplash(true)}
          detectionCount={currentItem?.detections?.length || 0}
        />

        <main id="ruang-kerja" className="main-content">
          <AnimatePresence mode="wait">
            {activePage === 'public' && (
              <motion.div
                key="page-public"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: EASE_OUT }}
              >
                <PublicReaderPage
                  samples={SAMPLE_IMAGES}
                  currentItem={currentItem}
                  isScanning={isScanning}
                  apiError={apiError}
                  onDismissError={() => setApiError('')}
                  onSelectSample={handleSelectSample}
                  onUploadFile={handleUploadFile}
                  onUpdateCurrentImage={handleUpdateCurrentImage}
                  onResetOriginalImage={handleResetOriginalImage}
                  onRunReadScript={handleRunReadScript}
                  onClearSelection={handleClearSelection}
                  onOpenGuide={() => handleNavigate('guide')}
                  onOpenPhotoGuide={() => setShowPhotoGuide(true)}
                  onNotify={showToast}
                />
              </motion.div>
            )}

            {activePage === 'history' && (
              <motion.div
                key="page-history"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: EASE_OUT }}
              >
                <HistoryPage
                  sessionHistory={sessionHistory}
                  currentItem={currentItem}
                  onClearHistory={handleRequestClearHistory}
                  onGoToReader={() => handleNavigate('public')}
                  onSelectForReader={(item) => {
                    handleSelectHistoryItem(item)
                    handleNavigate('public')
                  }}
                  onSelectForResearch={(item) => {
                    handleSelectHistoryItem(item)
                    handleNavigate('research')
                  }}
                />
              </motion.div>
            )}

            {activePage === 'research' && (
              <motion.div
                key="page-research"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: EASE_OUT }}
              >
                <ResearchPage
                  samples={SAMPLE_IMAGES}
                  currentItem={currentItem}
                  sessionHistory={sessionHistory}
                  isScanning={isScanning}
                  backendStatus={backendStatus}
                  modelIdentity={effectiveModelIdentity}
                  apiError={apiError}
                  onDismissError={() => setApiError('')}
                  onSelectSample={handleSelectSample}
                  onSelectHistoryItem={handleSelectHistoryItem}
                  onUploadFile={handleUploadFile}
                  onUpdateCurrentImage={handleUpdateCurrentImage}
                  onResetOriginalImage={handleResetOriginalImage}
                  onRunReadScript={handleRunReadScript}
                  onBackToPublic={() => handleNavigate('public')}
                />
              </motion.div>
            )}

            {activePage === 'guide' && (
              <motion.div
                key="page-guide"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: EASE_OUT }}
              >
                <GuidePage
                  onGoToReader={() => handleNavigate('public')}
                  onOpenPhotoGuide={() => setShowPhotoGuide(true)}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        <AnimatePresence>
          {confirmClearOpen && (
            <motion.div
              className="modal-backdrop"
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="confirm-clear-title"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
              onClick={(e) => {
                if (e.target === e.currentTarget) setConfirmClearOpen(false)
              }}
            >
              <motion.div
                className="modal-card pt-paper confirm-modal"
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={{ duration: 0.2, ease: EASE_OUT }}
              >
                <span className="panel-kicker">KONFIRMASI PENGHAPUSAN</span>
                <h2 id="confirm-clear-title" className="modal-title confirm-modal-title">
                  Bersihkan Riwayat Bacaan?
                </h2>
                <p className="confirm-modal-desc">
                  Sebanyak {sessionHistory.length} entri riwayat bacaan akan dihapus dari daftar. Gambar yang sedang terbuka di halaman Baca Aksara tidak akan ikut terhapus.
                </p>
                <div className="confirm-modal-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setConfirmClearOpen(false)}
                  >
                    Batal
                  </button>
                  <button
                    type="button"
                    className="btn-curtain btn-primary-read"
                    onClick={handleConfirmClearHistory}
                  >
                    <span className="btn-curtain-bg" aria-hidden="true" />
                    <span className="btn-curtain-label">Ya, Bersihkan Riwayat</span>
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {toastMsg && (
            <motion.div
              className="app-toast"
              role="status"
              aria-live="polite"
              initial={{ opacity: 0, y: 14, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.96 }}
              transition={{ duration: 0.2, ease: EASE_OUT }}
            >
              {toastMsg}
            </motion.div>
          )}
        </AnimatePresence>

        <footer className="site-footer">
          <div className="footer-gorga-bg" aria-hidden="true" />
          <div className="footer-inner">
            <p className="footer-wordmark">
              <RiseLines lines={['Pustaha Toba']} />
            </p>
            <p className="footer-meta">
              Designed &amp; Developed by Jonathan C. Amadeo Sembiring
            </p>
          </div>
        </footer>
      </div>
    </MotionConfig>
  )
}
