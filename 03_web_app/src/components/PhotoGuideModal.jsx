import { useEffect } from 'react'
import { motion } from 'motion/react'
import { EASE_OUT } from './MotionPrimitives.jsx'

/**
 * Modal panduan foto yang baik (diadaptasi dari pola DemoModal Zip 2).
 */
export default function PhotoGuideModal({ onClose }) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <motion.div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="photo-guide-title"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <motion.div
        className="modal-card pt-paper"
        initial={{ opacity: 0, y: 14, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 10, scale: 0.98 }}
        transition={{ duration: 0.24, ease: EASE_OUT }}
      >
        <div className="modal-header">
          <h2 id="photo-guide-title" className="modal-title">
            Tips Mengambil Foto Aksara yang Jelas
          </h2>
          <button
            type="button"
            className="btn-text-action"
            onClick={onClose}
          >
            Tutup (Esc)
          </button>
        </div>

        <div className="modal-grid">
          <div className="modal-tip-card is-good">
            <span className="modal-badge is-good">Disarankan</span>
            <ul className="modal-list">
              <li>Foto tegak lurus dari atas kertas agar bentuk huruf tidak miring tajam.</li>
              <li>Gunakan kertas polos terang dengan tinta hitam atau gelap yang kontras.</li>
              <li>Pastikan seluruh tanda kecil (Anak ni Surat) masuk penuh di dalam bingkai.</li>
            </ul>
          </div>
          <div className="modal-tip-card is-avoid">
            <span className="modal-badge is-avoid">Hindari</span>
            <ul className="modal-list">
              <li>Bayangan tangan atau kilau lampu menutupi sebagian aksara.</li>
              <li>Foto buram, terlalu jauh, atau terpotong di tepi baris tulisan.</li>
              <li>Kertas bergaris tebal yang menabrak goresan tanda diakritik.</li>
            </ul>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
