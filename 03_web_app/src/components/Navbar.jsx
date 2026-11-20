import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from 'motion/react'
import BrandMark from './BrandMark.jsx'
import { IconLayersInspect, IconSettingsGear, IconTrashClear } from './Icons.jsx'
import { EASE_OUT } from './MotionPrimitives.jsx'

const PUBLIC_NAV_ITEMS = [
  { id: 'public', label: 'Baca Aksara', hint: 'Pembaca Utama' },
  { id: 'history', label: 'Riwayat', hint: 'Riwayat Bacaan Sesi' },
  { id: 'guide', label: 'Panduan', hint: 'Cara & 25 Aksara' },
]

const RESEARCH_NAV_ITEM = {
  id: 'research',
  label: 'Hasil Penelitian',
  hint: 'Studio segmentasi mask, tabel prediksi, & evaluasi model',
}

export default function Navbar({
  activePage,
  onNavigate,
  onOpenPhotoGuide,
  theme,
  onSetTheme,
  historyCount = 0,
  onRequestClearHistory,
  onReplaySplash,
  detectionCount = 0,
}) {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const settingsWrapRef = useRef(null)
  const settingsBtnRef = useRef(null)
  const { scrollY } = useScroll()

  useMotionValueEvent(scrollY, 'change', (latest) => {
    setScrolled(latest > 24)
  })

  useEffect(() => {
    setMobileOpen(false)
    setSettingsOpen(false)
  }, [activePage])

  useEffect(() => {
    if (!mobileOpen && !settingsOpen) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') {
        if (settingsOpen) {
          setSettingsOpen(false)
          settingsBtnRef.current?.focus()
        }
        if (mobileOpen) setMobileOpen(false)
      }
    }
    const onPointerDown = (e) => {
      if (settingsOpen && settingsWrapRef.current && !settingsWrapRef.current.contains(e.target)) {
        setSettingsOpen(false)
      }
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('pointerdown', onPointerDown)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('pointerdown', onPointerDown)
    }
  }, [mobileOpen, settingsOpen])

  const handleToggleSettings = () => {
    setSettingsOpen((prev) => {
      const next = !prev
      if (next) setMobileOpen(false)
      return next
    })
  }

  const handleToggleMobile = () => {
    setMobileOpen((prev) => {
      const next = !prev
      if (next) setSettingsOpen(false)
      return next
    })
  }

  return (
    <header className="floating-header-wrap">
      <div className={`floating-nav ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="brand">
          <button
            type="button"
            className="brand-mark-btn"
            title="Putar ulang tirai pembuka Pustaha Toba"
            aria-label="Putar ulang tirai pembuka Pustaha Toba"
            onClick={onReplaySplash}
          >
            <BrandMark size={20} />
          </button>
          <div>
            <span className="brand-title">Pustaha Toba</span>
            <p className="brand-sub">Transliterasi Aksara Batak Toba</p>
          </div>
        </div>

        {/* Navigasi Editorial Terbuka */}
        <nav className="desktop-nav" aria-label="Navigasi utama aplikasi">
          {PUBLIC_NAV_ITEMS.map((item) => {
            const isActive = activePage === item.id
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-link-btn ${isActive ? 'is-active' : ''}`}
                aria-current={isActive ? 'page' : undefined}
                onClick={() => onNavigate(item.id)}
              >
                <span className="nav-link-text">
                  {item.label}
                  {item.id === 'history' && historyCount > 0 && (
                    <span className="nav-count-dot" aria-label={`${historyCount} riwayat`}>
                      {historyCount}
                    </span>
                  )}
                </span>
                {isActive && (
                  <motion.span
                    layoutId="nav-active-bar"
                    className="nav-active-bar"
                    transition={{ duration: 0.26, ease: EASE_OUT }}
                  />
                )}
              </button>
            )
          })}
        </nav>

        <div className="header-actions">
          <span className="nav-util-divider" aria-hidden="true" />

          <button
            type="button"
            className="nav-guide-btn"
            onClick={onOpenPhotoGuide}
          >
            Tips Foto
          </button>

          <div className="nav-settings-wrap" ref={settingsWrapRef}>
            <button
              ref={settingsBtnRef}
              type="button"
              className={`nav-settings-btn ${settingsOpen ? 'is-open' : ''}`}
              aria-haspopup="dialog"
              aria-expanded={settingsOpen}
              aria-controls="nav-settings-popover"
              aria-label="Pengaturan tampilan dan opsi penelitian"
              onClick={handleToggleSettings}
            >
              <IconSettingsGear size={17} className="settings-gear-icon" />
              <span className="settings-btn-label">Pengaturan</span>
              {activePage === 'research' && (
                <span className="settings-active-dot" aria-hidden="true" />
              )}
            </button>

            <AnimatePresence>
              {settingsOpen && (
                <motion.div
                  id="nav-settings-popover"
                  role="dialog"
                  aria-label="Pengaturan aplikasi"
                  className="nav-settings-popover"
                  initial={{ opacity: 0, y: 8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 6, scale: 0.98 }}
                  transition={{ duration: 0.18, ease: EASE_OUT }}
                >
                  <div className="settings-popover-head">
                    <span className="settings-popover-title">Pengaturan</span>
                  </div>

                  <div className="settings-control-group">
                    <span className="settings-group-label" id="settings-theme-label">
                      Tema tampilan
                    </span>
                    <div
                      className="settings-seg-group"
                      role="group"
                      aria-labelledby="settings-theme-label"
                    >
                      <button
                        type="button"
                        className={`settings-seg-btn ${theme === 'light' ? 'is-active' : ''}`}
                        aria-pressed={theme === 'light'}
                        onClick={() => onSetTheme?.('light')}
                      >
                        Terang
                      </button>
                      <button
                        type="button"
                        className={`settings-seg-btn ${theme === 'dark' ? 'is-active' : ''}`}
                        aria-pressed={theme === 'dark'}
                        onClick={() => onSetTheme?.('dark')}
                      >
                        Gelap
                      </button>
                    </div>
                  </div>

                  <div className="settings-session-section">
                    <button
                      type="button"
                      className="settings-clear-btn"
                      disabled={historyCount === 0}
                      onClick={() => {
                        setSettingsOpen(false)
                        onRequestClearHistory?.()
                      }}
                    >
                      <IconTrashClear size={15} />
                      <span>
                        {historyCount > 0
                          ? `Bersihkan riwayat sesi (${historyCount})`
                          : 'Riwayat sesi kosong'}
                      </span>
                    </button>
                  </div>

                  <div className="settings-research-section">
                    <button
                      type="button"
                      className={`settings-research-link ${activePage === RESEARCH_NAV_ITEM.id ? 'is-active' : ''}`}
                      aria-current={activePage === RESEARCH_NAV_ITEM.id ? 'page' : undefined}
                      onClick={() => {
                        setSettingsOpen(false)
                        onNavigate(RESEARCH_NAV_ITEM.id)
                      }}
                    >
                      <span className="settings-research-icon">
                        <IconLayersInspect size={16} />
                      </span>
                      <span className="settings-research-body">
                        <span className="settings-research-title-row">
                          <strong>{RESEARCH_NAV_ITEM.label}</strong>
                          {detectionCount > 0 && (
                            <span className="settings-research-badge">{detectionCount}</span>
                          )}
                        </span>
                        <span className="settings-research-sub">{RESEARCH_NAV_ITEM.hint}</span>
                      </span>
                      <span className="settings-research-arrow" aria-hidden="true">
                        &rarr;
                      </span>
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <button
            type="button"
            className="mobile-menu-btn"
            aria-expanded={mobileOpen}
            aria-controls="mobile-nav-drawer"
            onClick={handleToggleMobile}
          >
            {mobileOpen ? 'Tutup' : 'Menu'}
          </button>
        </div>
      </div>

      {/* Menu Lipat Mobile */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.nav
            id="mobile-nav-drawer"
            className="mobile-nav-drawer"
            aria-label="Navigasi seluler"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: EASE_OUT }}
          >
            <div className="mobile-nav-inner">
              {PUBLIC_NAV_ITEMS.map((item) => {
                const isActive = activePage === item.id
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`mobile-nav-item ${isActive ? 'is-active' : ''}`}
                    aria-current={isActive ? 'page' : undefined}
                    onClick={() => {
                      onNavigate(item.id)
                      setMobileOpen(false)
                    }}
                  >
                    <span className="mobile-nav-title">
                      {item.label}
                      {item.id === 'history' && historyCount > 0 ? ` (${historyCount})` : ''}
                    </span>
                    <span className="mobile-nav-hint">{item.hint}</span>
                  </button>
                )
              })}

              <div className="mobile-nav-divider" aria-hidden="true" />

              <button
                type="button"
                className={`mobile-nav-item is-optional ${activePage === RESEARCH_NAV_ITEM.id ? 'is-active' : ''}`}
                aria-current={activePage === RESEARCH_NAV_ITEM.id ? 'page' : undefined}
                onClick={() => {
                  onNavigate(RESEARCH_NAV_ITEM.id)
                  setMobileOpen(false)
                }}
              >
                <span className="mobile-nav-title">
                  {RESEARCH_NAV_ITEM.label}
                  {detectionCount > 0 ? ` (${detectionCount})` : ''}
                </span>
                <span className="mobile-nav-hint">Opsi peneliti</span>
              </button>

              <button
                type="button"
                className="mobile-nav-item"
                onClick={() => {
                  setMobileOpen(false)
                  onOpenPhotoGuide()
                }}
              >
                <span className="mobile-nav-title">Tips Foto Aksara</span>
                <span className="mobile-nav-hint">Panduan pemotretan</span>
              </button>
            </div>
          </motion.nav>
        )}
      </AnimatePresence>
    </header>
  )
}
