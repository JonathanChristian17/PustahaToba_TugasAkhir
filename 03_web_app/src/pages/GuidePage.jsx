import { Fragment, useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { ANAK_NI_SURAT, INA_NI_SURAT } from '../data/aksaraCatalog.js'
import BrandMark from '../components/BrandMark.jsx'
import { InteractiveScriptCanopy, LetterTiltReveal } from '../components/HeroAnimations.jsx'
import { EASE_OUT, FadeUp, MagneticWrap } from '../components/MotionPrimitives.jsx'

const HANDWRITING_EXAMPLES = [
  {
    id: 'kata',
    tabLabel: 'Kata',
    kicker: 'Contoh 1 · Rangkaian Kata',
    src: '/samples/ID010_P07_N10_010.png',
    syllables: ['hu', 'ta', 'to', 'ba'],
    latin: 'hutatoba',
    note: 'Gabungan huruf dasar dengan tanda vokal /u/ dan /o/',
  },
  {
    id: 'tanda',
    tabLabel: 'Tanda',
    kicker: 'Contoh 2 · Tanda Bunyi',
    src: '/samples/guide_tanda_jabuniinang.png',
    syllables: ['ja', 'bu', 'ni', 'i', 'nang'],
    latin: 'jabuniinang',
    note: 'Memakai tanda /u/, /i/, dan akhiran -ng (Haminsaran)',
  },
  {
    id: 'pangolat',
    tabLabel: 'Pemati',
    kicker: 'Contoh 3 · Pemati Pangolat',
    src: '/samples/guide_pemati_dongan.png',
    syllables: ['do', 'nga', 'n'],
    latin: 'dongan',
    note: 'Garis Pangolat di ujung mematikan vokal /a/ pada Na menjadi -n',
  },
]

const PHOTO_TIPS_STEPS = [
  {
    num: '01',
    title: 'Pencahayaan Merata & Kertas Kontras',
    desc: 'Pastikan tinta tulisan tampak gelap dan tegas di atas kertas terang tanpa bayangan tangan atau pantulan lampu.',
  },
  {
    num: '02',
    title: 'Kamera Tegak Lurus (Gunakan Putar / Potong)',
    desc: 'Posisikan baris tulisan mendatar. Bila foto dari ponsel miring 90 derajat atau berlebih tepi meja, rapikan langsung lewat tombol Putar / Potong sebelum membaca.',
  },
  {
    num: '03',
    title: 'Cakupan Penuh Tanda Kecil (Anak ni Surat)',
    desc: 'Pastikan tanda diakritik di sisi kanan atau pinggir kata masuk ke bingkai karena tanda tersebut mengubah bunyi vokal atau menutup suku kata.',
  },
]

const ALL_CATALOG = [
  ...INA_NI_SURAT.map((g) => ({ ...g, category: 'Ina ni Surat' })),
  ...ANAK_NI_SURAT.map((g) => ({ ...g, category: 'Anak ni Surat' })),
]

/**
 * Halaman Panduan Penggunaan & Kamus Referensi 25 Aksara Batak Toba.
 */
export default function GuidePage({ onGoToReader, onOpenPhotoGuide }) {
  const [catalogFilter, setCatalogFilter] = useState('all')
  const [catalogQuery, setCatalogQuery] = useState('')
  const [selectedGlyph, setSelectedGlyph] = useState(null)
  const [activeSlideIdx, setActiveSlideIdx] = useState(0)
  const [isCarouselPaused, setIsCarouselPaused] = useState(false)
  const reduceMotion = useReducedMotion()

  const activeSlide = HANDWRITING_EXAMPLES[activeSlideIdx]

  useEffect(() => {
    if (reduceMotion || isCarouselPaused) return undefined
    const timer = window.setInterval(() => {
      setActiveSlideIdx((prev) => (prev + 1) % HANDWRITING_EXAMPLES.length)
    }, 3800)
    return () => window.clearInterval(timer)
  }, [reduceMotion, isCarouselPaused])

  const normalizedQuery = catalogQuery.trim().toLowerCase()
  const baseCatalog =
    catalogFilter === 'ina'
      ? ALL_CATALOG.filter((g) => g.category === 'Ina ni Surat')
      : catalogFilter === 'anak'
        ? ALL_CATALOG.filter((g) => g.category === 'Anak ni Surat')
        : ALL_CATALOG

  const filteredCatalog = baseCatalog.filter((item) => {
    if (!normalizedQuery) return true
    return (
      item.name.toLowerCase().includes(normalizedQuery) ||
      item.latin.toLowerCase().includes(normalizedQuery) ||
      item.rawClass.toLowerCase().includes(normalizedQuery)
    )
  })

  useEffect(() => {
    if (!selectedGlyph) return undefined
    const onKey = (e) => {
      if (e.key === 'Escape') setSelectedGlyph(null)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [selectedGlyph])

  const selectedIndex = selectedGlyph
    ? filteredCatalog.findIndex((g) => g.rawClass === selectedGlyph.rawClass)
    : -1

  const stepGlyph = (delta) => {
    if (!filteredCatalog.length) return
    const nextIdx =
      selectedIndex < 0
        ? 0
        : (selectedIndex + delta + filteredCatalog.length) % filteredCatalog.length
    setSelectedGlyph(filteredCatalog[nextIdx])
  }

  const jumpToSection = (sectionId, filterValue = null) => {
    if (filterValue) setCatalogFilter(filterValue)
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="guide-flow">
      <section className="guide-hero-band" aria-labelledby="guide-page-title">
        <InteractiveScriptCanopy />

        <div className="guide-hero-inner">
          <div className="guide-hero-grid">
            <div className="guide-hero-copy">
              <span className="guide-kicker">Panduan Penggunaan · Kamus 25 Aksara</span>
              <h1 id="guide-page-title" className="guide-hero-title">
                <LetterTiltReveal
                  lines={[
                    'Cara Membaca Aksara &',
                    [{ text: 'Kamus ' }, { text: '25 Aksara Batak', accent: true }],
                  ]}
                />
              </h1>
              <p className="guide-hero-lead">
                Tips memotret tulisan tangan Aksara Batak Toba agar mudah terbaca, panduan singkat cara membacanya, serta kamus visual 19 Ina ni Surat dan 6 Anak ni Surat.
              </p>

              <div className="guide-index-list" role="group" aria-label="Sorotan isi halaman panduan">
                <button
                  type="button"
                  className="guide-index-btn"
                  onClick={() => jumpToSection('kamus-aksara', 'ina')}
                >
                  <span className="guide-index-num">19</span>
                  <span className="guide-index-meta">
                    <strong>Ina ni Surat</strong>
                    <span>Huruf dasar utama</span>
                  </span>
                  <span className="guide-index-arrow" aria-hidden="true">&rarr;</span>
                </button>

                <button
                  type="button"
                  className="guide-index-btn"
                  onClick={() => jumpToSection('kamus-aksara', 'anak')}
                >
                  <span className="guide-index-num">6</span>
                  <span className="guide-index-meta">
                    <strong>Anak ni Surat</strong>
                    <span>Tanda pengubah bunyi</span>
                  </span>
                  <span className="guide-index-arrow" aria-hidden="true">&rarr;</span>
                </button>

                <button
                  type="button"
                  className="guide-index-btn"
                  onClick={() => jumpToSection('langkah-foto')}
                >
                  <span className="guide-index-num">3</span>
                  <span className="guide-index-meta">
                    <strong>Langkah Foto</strong>
                    <span>Tips agar mudah dibaca</span>
                  </span>
                  <span className="guide-index-arrow" aria-hidden="true">&rarr;</span>
                </button>
              </div>

              <div className="guide-hero-actions">
                <MagneticWrap>
                  <button type="button" className="btn-curtain btn-primary-read" onClick={onGoToReader}>
                    <span className="btn-curtain-bg" aria-hidden="true" />
                    <span className="btn-curtain-label">Mulai Baca Aksara</span>
                  </button>
                </MagneticWrap>
                <button type="button" className="btn-text-action" onClick={onOpenPhotoGuide}>
                  Ringkasan Tips Foto
                </button>
              </div>
            </div>

            <div
              className="guide-arch-stage"
              onMouseEnter={() => setIsCarouselPaused(true)}
              onMouseLeave={() => setIsCarouselPaused(false)}
              onFocusCapture={() => setIsCarouselPaused(true)}
              onBlurCapture={() => setIsCarouselPaused(false)}
            >
              <div className="guide-book-seal" aria-hidden="true">
                <svg viewBox="0 0 100 100" className="guide-sunburst-ring pt-spin-slow">
                  <g>
                    {Array.from({ length: 24 }, (_, idx) => (
                      <line
                        key={idx}
                        x1="50"
                        y1="6"
                        x2="50"
                        y2="14"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        transform={`rotate(${idx * 15} 50 50)`}
                      />
                    ))}
                  </g>
                </svg>
                <span className="guide-book-core">
                  <BrandMark size={22} />
                </span>
              </div>

              <motion.div
                className="guide-arch-outline"
                aria-hidden="true"
                initial={{ clipPath: 'inset(100% 0% 0% 0%)' }}
                animate={{ clipPath: 'inset(0% 0% 0% 0%)' }}
                transition={{ duration: 1.15, ease: EASE_OUT, delay: 0.15 }}
              />

              <div className="guide-arch-card pt-paper">
                <div className="guide-arch-tabs" role="tablist" aria-label="Pilih contoh tulisan tangan">
                  {HANDWRITING_EXAMPLES.map((slide, idx) => (
                    <button
                      key={slide.id}
                      type="button"
                      role="tab"
                      aria-selected={activeSlideIdx === idx}
                      className={`guide-arch-tab ${activeSlideIdx === idx ? 'is-active' : ''}`}
                      onClick={() => setActiveSlideIdx(idx)}
                    >
                      {slide.tabLabel}
                    </button>
                  ))}
                </div>

                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeSlide.id}
                    className="guide-specimen-stage"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.24, ease: EASE_OUT }}
                  >
                    <div className="guide-sample-photo-box">
                      <img
                        src={activeSlide.src}
                        alt={`Contoh tulisan tangan ${activeSlide.latin}`}
                        className="guide-sample-photo-img"
                      />
                    </div>
                    <span className="guide-specimen-kicker">{activeSlide.kicker}</span>
                    <div className="guide-sample-syllables" aria-label="Pemecahan suku kata">
                      {activeSlide.syllables.map((s, idx) => (
                        <Fragment key={`${s}-${idx}`}>
                          {idx > 0 && (
                            <span className="guide-sample-sep" aria-hidden="true">
                              &middot;
                            </span>
                          )}
                          <span className="guide-sample-syl">{s}</span>
                        </Fragment>
                      ))}
                    </div>
                    <span className="guide-sample-arrow" aria-hidden="true">
                      &darr;
                    </span>
                    <strong className="guide-specimen-name">{activeSlide.latin}</strong>
                    <span className="guide-specimen-sound">{activeSlide.note}</span>
                  </motion.div>
                </AnimatePresence>

                <div className="guide-carousel-dots" aria-label="Indikator putaran otomatis contoh tulisan">
                  {HANDWRITING_EXAMPLES.map((slide, idx) => (
                    <button
                      key={slide.id}
                      type="button"
                      className={`guide-carousel-dot ${activeSlideIdx === idx ? 'is-active' : ''}`}
                      aria-label={`Tampilkan contoh ${slide.latin}`}
                      onClick={() => setActiveSlideIdx(idx)}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="guide-editorial-seam" aria-hidden="true" />
      </section>

      <div className="guide-container">
        {/* Blok 1: 3 Kartu Langkah Persiapan Foto dengan Highlight & Hover */}
        <FadeUp delay={0.04}>
          <section id="langkah-foto" className="guide-steps-band" aria-labelledby="steps-heading">
            <h2 id="steps-heading" className="sr-only">
              Tiga langkah persiapan foto Aksara Batak Toba
            </h2>
            {PHOTO_TIPS_STEPS.map((st) => (
              <article key={st.num} className="guide-step-card pt-paper">
                <span className="guide-step-num">Langkah {st.num}</span>
                <h3 className="guide-step-title">{st.title}</h3>
                <p className="guide-step-desc">{st.desc}</p>
              </article>
            ))}
          </section>
        </FadeUp>

        {/* Blok 2: Kamus Referensi Cepat 25 Aksara dengan Filter Beranimasi & Pop-Up Detail */}
        <FadeUp delay={0.06}>
          <section id="kamus-aksara" className="panel pt-paper guide-catalog-panel" aria-labelledby="catalog-heading">
            <div className="catalog-head">
              <div>
                <span className="panel-kicker">REFERENSI LENGKAP 25 AKSARA BATAK TOBA</span>
                <h2 id="catalog-heading" className="panel-title">
                  Kamus Visual Ina ni Surat (19) &amp; Anak ni Surat (6)
                </h2>
              </div>

              <div className="catalog-controls">
                <div className="toggle-group" role="tablist" aria-label="Filter jenis aksara">
                  {[
                    { id: 'all', label: 'Semua (25)' },
                    { id: 'ina', label: 'Ina ni Surat (19)' },
                    { id: 'anak', label: 'Anak ni Surat (6)' },
                  ].map((tab) => {
                    const isOn = catalogFilter === tab.id
                    return (
                      <button
                        key={tab.id}
                        type="button"
                        role="tab"
                        aria-selected={isOn}
                        className={`chip-toggle chip-toggle-animated ${isOn ? 'is-on' : ''}`}
                        onClick={() => setCatalogFilter(tab.id)}
                      >
                        {isOn && (
                          <motion.span
                            layoutId="catalog-filter-pill"
                            className="chip-active-bg"
                            transition={{ duration: 0.24, ease: EASE_OUT }}
                          />
                        )}
                        <span className="chip-label-text">{tab.label}</span>
                      </button>
                    )
                  })}
                </div>

                <input
                  type="search"
                  value={catalogQuery}
                  onChange={(e) => setCatalogQuery(e.target.value)}
                  placeholder="Cari aksara atau bunyi (mis. ba, u, pangolat)..."
                  aria-label="Cari aksara Batak Toba"
                  className="catalog-search-input"
                />
              </div>
            </div>

            {filteredCatalog.length === 0 ? (
              <p className="empty-desc">
                Tidak ada aksara yang cocok dengan pencarian &ldquo;{catalogQuery}&rdquo;.
              </p>
            ) : (
              <motion.div layout className="catalog-glyph-grid">
                <AnimatePresence mode="popLayout">
                  {filteredCatalog.map((item) => {
                    const isAnak = item.category === 'Anak ni Surat'
                    return (
                      <motion.button
                        key={item.rawClass}
                        type="button"
                        layout
                        initial={{ opacity: 0, scale: 0.94, y: 8 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.94 }}
                        transition={{ duration: 0.22, ease: EASE_OUT }}
                        className="glyph-ref-card is-interactive"
                        aria-label={`Lihat detail aksara ${item.name}`}
                        onClick={() => setSelectedGlyph(item)}
                      >
                        <div className="glyph-ref-top">
                          <span className="glyph-ref-id">{item.id}</span>
                          <span className={`badge-kind ${isAnak ? '' : 'is-ina'}`}>
                            {isAnak ? 'Anak' : 'Ina'}
                          </span>
                        </div>
                        <div className="glyph-ref-img-box">
                          <img
                            src={item.src}
                            alt={`Aksara ${item.name} (${item.latin})`}
                            width="72"
                            height="72"
                            loading="lazy"
                            className="glyph-ref-img"
                          />
                        </div>
                        <div className="glyph-ref-body">
                          <strong className="glyph-ref-name">{item.name}</strong>
                          <span className="glyph-ref-latin">
                            {isAnak ? item.latin : `Bunyi: "${item.latin}"`}
                          </span>
                        </div>
                      </motion.button>
                    )
                  })}
                </AnimatePresence>
              </motion.div>
            )}
          </section>
        </FadeUp>
      </div>

      {/* Pop-Up Detail Aksara saat kartu kamus diklik */}
      <AnimatePresence>
        {selectedGlyph && (
          <motion.div
            className="modal-backdrop"
            role="dialog"
            aria-modal="true"
            aria-labelledby="glyph-detail-title"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => {
              if (e.target === e.currentTarget) setSelectedGlyph(null)
            }}
          >
            <motion.div
              className="modal-card pt-paper glyph-detail-modal"
              initial={{ opacity: 0, y: 14, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.98 }}
              transition={{ duration: 0.22, ease: EASE_OUT }}
            >
              <div className="modal-header">
                <div>
                  <span className="panel-kicker">
                    {selectedGlyph.category.toUpperCase()} · NO. {selectedGlyph.id}
                  </span>
                  <h2 id="glyph-detail-title" className="modal-title">
                    {selectedGlyph.name}
                  </h2>
                </div>
                <button
                  type="button"
                  className="btn-text-action"
                  onClick={() => setSelectedGlyph(null)}
                >
                  Tutup (Esc)
                </button>
              </div>

              <div className="glyph-modal-body">
                <div className="glyph-modal-showcase">
                  <div className="glyph-modal-img-frame">
                    <img
                      src={selectedGlyph.src}
                      alt={`Bentuk aksara ${selectedGlyph.name}`}
                      width="128"
                      height="128"
                      className="glyph-modal-img"
                    />
                  </div>
                  <div className="glyph-modal-info">
                    <span className={`badge-kind ${selectedGlyph.category === 'Anak ni Surat' ? '' : 'is-ina'}`}>
                      {selectedGlyph.category}
                    </span>
                    <p className="glyph-modal-sound">
                      {selectedGlyph.category === 'Anak ni Surat'
                        ? `Fungsi: ${selectedGlyph.latin}`
                        : `Bunyi baca: "${selectedGlyph.latin}"`}
                    </p>
                  </div>
                </div>

                {selectedGlyph.category === 'Anak ni Surat' && selectedGlyph.exampleSrc && (
                  <div className="glyph-modal-example">
                    <div className="glyph-modal-example-text">
                      <span className="panel-kicker">CONTOH PEMAKAIAN SUKU KATA</span>
                      <p>
                        Contoh bergabung dengan huruf dasar: <strong>{selectedGlyph.example}</strong>
                      </p>
                    </div>
                    <img
                      src={selectedGlyph.exampleSrc}
                      alt={`Contoh suku kata ${selectedGlyph.example}`}
                      width="88"
                      height="88"
                      className="glyph-modal-example-img"
                    />
                  </div>
                )}
              </div>

              <div className="glyph-modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={filteredCatalog.length <= 1}
                  onClick={() => stepGlyph(-1)}
                >
                  &larr; Sebelumnya
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  disabled={filteredCatalog.length <= 1}
                  onClick={() => stepGlyph(1)}
                >
                  Berikutnya &rarr;
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
