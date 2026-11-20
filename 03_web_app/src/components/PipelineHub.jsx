import { useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { EASE_OUT } from './MotionPrimitives.jsx'

const PIPELINE_STEPS = [
  {
    id: 'citra',
    code: '01',
    title: 'Foto Tulisan Aksara',
    summary: 'Foto Aksara Batak Toba diterima pada kanvas.',
    detail:
      'Aplikasi memeriksa foto (PNG, JPG, WEBP) dan memberi ruang untuk memutar atau memotong tepi gambar sebelum dibaca.',
  },
  {
    id: 'deteksi',
    code: '02',
    title: 'Pengenalan 25 Aksara',
    summary: 'Mengenali 19 Ina ni Surat dan 6 Anak ni Surat.',
    detail:
      'Setiap goresan huruf utama (Ina ni Surat) dan tanda pengubah bunyi (Anak ni Surat) dikenali posisinya langsung dari gambar.',
  },
  {
    id: 'susun',
    code: '03',
    title: 'Pasangan Ina & Anak',
    summary: 'Menentukan urutan baca baris dan suku kata.',
    detail:
      'Setiap tanda Anak ni Surat dipasangkan dengan huruf Ina ni Surat di dekatnya sesuai kaidah baca Batak Toba dari kiri ke kanan.',
  },
  {
    id: 'latin',
    code: '04',
    title: 'Kalimat Huruf Latin',
    summary: 'Hasil bacaan utama yang siap disalin dan dipelajari.',
    detail:
      'Menampilkan bacaan Latin secara jelas beserta pemecahan suku kata interaktif dan perkiraan spasi kata yang dapat diunduh sebagai berkas teks (TXT).',
  },
]

/**
 * Pita gelap interaktif alur transliterasi (menggabungkan pola Hub & pita gelap Zip 2).
 */
export default function PipelineHub({ onOpenGuide }) {
  const [activeId, setActiveId] = useState('citra')
  const current = PIPELINE_STEPS.find((s) => s.id === activeId) || PIPELINE_STEPS[0]

  return (
    <section className="pipeline-editorial-band" aria-labelledby="pipeline-hub-title">
      <div className="pipeline-surface-card pt-paper">
        <div className="pipeline-header">
          <div>
            <span className="pipeline-eyebrow">ALUR PEMBACAAN PUSTAHA TOBA</span>
            <h2 id="pipeline-hub-title" className="pipeline-title">
              Bagaimana Citra Aksara Menjadi Kalimat Latin
            </h2>
          </div>
          <div className="pipeline-cta-group">
            <button type="button" className="btn-secondary" onClick={onOpenGuide}>
              Lihat Panduan Lengkap
            </button>
          </div>
        </div>

        <div className="hub-grid">
          <div className="hub-nodes" role="group" aria-label="Pilih tahapan pembacaan">
            {PIPELINE_STEPS.map((step) => {
              const isActive = step.id === activeId
              return (
                <button
                  key={step.id}
                  type="button"
                  aria-pressed={isActive}
                  className={`hub-node-btn ${isActive ? 'is-active' : ''}`}
                  onClick={() => setActiveId(step.id)}
                >
                  <span className="hub-node-code">{step.code}</span>
                  <span className="hub-node-body">
                    <span className="hub-node-title">{step.title}</span>
                    <span className="hub-node-summary">{step.summary}</span>
                  </span>
                </button>
              )
            })}
          </div>

          <div className="hub-detail-stage">
            <AnimatePresence mode="wait">
              <motion.div
                key={current.id}
                className="hub-detail-card"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.24, ease: EASE_OUT }}
              >
                <span className="hub-detail-code">Tahap {current.code}</span>
                <h3 className="hub-detail-title">{current.title}</h3>
                <p className="hub-detail-text">{current.detail}</p>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </section>
  )
}
