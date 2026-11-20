import { useState } from 'react'
import { motion } from 'motion/react'
import { InteractiveGlyphField } from '../components/HeroAnimations.jsx'
import {
  EASE_OUT,
  FadeUp,
  InteractiveWaveLine,
  MagneticWrap,
  RingText,
  useTweenNumber,
  WordReveal,
} from '../components/MotionPrimitives.jsx'
import { displayReading } from '../utils/transliterationAdapter.js'
import { IconLayersInspect, IconReadingText } from '../components/Icons.jsx'

/**
 * Halaman Riwayat Bacaan:
 * Menampilkan tulisan yang telah dibaca beserta ringkasan statistik dan pencarian.
 */
export default function HistoryPage({
  sessionHistory = [],
  currentItem,
  onSelectForReader,
  onSelectForResearch,
  onClearHistory,
  onGoToReader,
}) {
  const [filterText, setFilterText] = useState('')
  const q = filterText.trim().toLowerCase()

  const filtered = sessionHistory.filter((item) => {
    if (!q) return true
    return (
      (item.publicLabel || item.label || '').toLowerCase().includes(q) ||
      (item.rawLatinText || '').toLowerCase().includes(q) ||
      (item.latinText || '').toLowerCase().includes(q)
    )
  })

  const totalCharacters = sessionHistory.reduce(
    (acc, it) => acc + (it.detections?.length || 0),
    0,
  )

  const tweenSaved = useTweenNumber(sessionHistory.length, 550)
  const tweenChars = useTweenNumber(totalCharacters, 680)

  return (
    <div className="history-flow">
      <section className="history-hero-band" aria-labelledby="history-page-title">
        <InteractiveGlyphField />

        <div className="history-hero-inner">
          <div className="history-hero-top">
            <div className="history-hero-copy">
              <span className="history-kicker">Arsip Bacaan Pengguna</span>
              <div className="history-title-wrap">
                <h1 id="history-page-title" className="history-hero-title">
                  <WordReveal as="span" text="Riwayat Pembacaan Aksara" />
                </h1>
                <motion.span
                  className="history-title-rule"
                  aria-hidden="true"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: 0.7, ease: EASE_OUT, delay: 0.25 }}
                />
              </div>
              <p className="history-hero-lead">
                Kumpulan tulisan Aksara Batak Toba yang baru saja Anda baca. Pilih salah satu kartu di bawah untuk melihat kembali hasil bacaannya.
              </p>
            </div>

            <div className="history-hero-aside">
              <div className="history-metric-pillars" role="group" aria-label="Ringkasan statistik riwayat">
                <div className="history-metric-pillar">
                  <strong className="hero-stat-value">{Math.round(tweenSaved)}</strong>
                  <span className="history-metric-label">Tulisan tersimpan</span>
                </div>
                <div className="history-metric-pillar">
                  <strong className="hero-stat-value">{Math.round(tweenChars)}</strong>
                  <span className="history-metric-label">Total aksara terbaca</span>
                </div>
              </div>

              <div className="history-seal-badge" aria-hidden="true">
                <RingText
                  text="ARSIP BACAAN · PUSTAHA TOBA · RIWAYAT · "
                  className="history-seal-ring"
                />
                <span className="history-seal-icon">
                  <IconReadingText size={18} />
                </span>
              </div>
            </div>
          </div>
        </div>

        <InteractiveWaveLine darkBg={true} fillBottom={true} />
      </section>

      <div className="history-container">
        <div className="history-dock-bar pt-paper" role="region" aria-label="Pencarian dan aksi riwayat">
          <div className="history-dock-search">
            <label htmlFor="history-search-input" className="sr-only">
              Cari riwayat bacaan
            </label>
            <input
              id="history-search-input"
              type="search"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Cari judul atau hasil bacaan Latin..."
              className="catalog-search-input hero-search-input"
            />
            {q && (
              <span className="hero-search-count">
                Menampilkan {filtered.length} dari {sessionHistory.length} bacaan
              </span>
            )}
          </div>

          <div className="history-dock-actions">
            <MagneticWrap>
              <button type="button" className="btn-curtain btn-primary-read" onClick={onGoToReader}>
                <span className="btn-curtain-bg" aria-hidden="true" />
                <span className="btn-curtain-label">
                  <IconReadingText size={15} />
                  <span>Unggah Foto Baru</span>
                </span>
              </button>
            </MagneticWrap>
            {sessionHistory.length > 0 && (
              <button type="button" className="btn-secondary" onClick={onClearHistory}>
                Bersihkan Riwayat
              </button>
            )}
          </div>
        </div>

        {filtered.length === 0 ? (
          <section className="panel pt-paper">
            <div className="empty-state">
              <p className="empty-title">Belum ada entri riwayat yang cocok</p>
              <p className="empty-desc">
                Pilih sampel atau unggah foto tulisan Aksara Batak Toba dari halaman Baca Aksara.
              </p>
              <button type="button" className="btn-curtain btn-primary-read" onClick={onGoToReader}>
                <span className="btn-curtain-bg" aria-hidden="true" />
                <span className="btn-curtain-label">Ke Halaman Baca Aksara</span>
              </button>
            </div>
          </section>
        ) : (
          <div className="history-cards-grid">
            {filtered.map((item) => {
              const isCurr = currentItem?.id === item.id
              const hasModule = Boolean(item.transliteration)
              return (
                <article
                  key={`${item.id}-${item.viewedAt || 'init'}`}
                  className={`panel pt-paper history-full-card ${isCurr ? 'is-current' : ''}`}
                >
                  <div className="history-card-top">
                    <div className="history-card-head">
                      <span className="panel-kicker">
                        {isCurr ? 'SEDANG AKTIF · ' : ''}
                        {item.viewedAt ? `Dilihat ${item.viewedAt}` : 'Sesi Aktif'}
                      </span>
                      <h2 className="history-card-title" title={item.publicLabel || item.label}>
                        {item.publicLabel || item.label}
                      </h2>
                    </div>
                    <span className="mono history-card-count">
                      {item.detections?.length || 0} aksara
                    </span>
                  </div>

                  <div className="history-card-thumb-wrap">
                    <img
                      src={item.src}
                      alt={`Pratinjau ${item.publicLabel || item.label}`}
                      className="history-card-img"
                    />
                  </div>

                  <div className="history-card-meta">
                    <div className="spacing-row">
                      <span className="spacing-key">Bacaan Latin:</span>
                      <strong className="spacing-val is-selectable">
                        {displayReading(item.rawLatinText) || '(belum dibaca)'}
                      </strong>
                    </div>
                    {hasModule &&
                      item.wordSpacing?.suggested_text &&
                      item.wordSpacing.suggested_text !== item.rawLatinText && (
                        <div className="spacing-row">
                          <span className="spacing-key">Perkiraan Spasi:</span>
                          <span className="spacing-val is-selectable">
                            {displayReading(item.wordSpacing.suggested_text)}
                          </span>
                        </div>
                      )}
                    {!hasModule && item.subtitle && (
                      <p className="spacing-review-note">{item.subtitle}</p>
                    )}
                  </div>

                  <div className="history-card-actions">
                    <button
                      type="button"
                      className="btn-curtain btn-primary-read"
                      onClick={() => onSelectForReader(item)}
                    >
                      <span className="btn-curtain-bg" aria-hidden="true" />
                      <span className="btn-curtain-label">
                        <IconReadingText size={15} />
                        <span>Buka di Baca Aksara</span>
                      </span>
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => onSelectForResearch(item)}
                    >
                      <IconLayersInspect size={15} />
                      <span>Lihat Hasil Penelitian</span>
                    </button>
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
