import { INA_NI_SURAT, ANAK_NI_SURAT } from '../data/aksaraCatalog.js'

const ROW_ONE = INA_NI_SURAT.slice(0, 10)
const ROW_TWO = [...INA_NI_SURAT.slice(10), ...ANAK_NI_SURAT.slice(0, 3)]
const ROW_THREE = [...ANAK_NI_SURAT, ...INA_NI_SURAT.slice(0, 7)]

function DriftTrack({ items, reverse = false, duration = '38s' }) {
  const doubled = [...items, ...items]
  return (
    <div
      className={`aksara-drift-track ${reverse ? 'is-reverse' : ''}`}
      style={{ '--dur': duration }}
    >
      {doubled.map((item, idx) => (
        <span key={`${item.id}-${idx}`} className="aksara-drift-glyph">
          <img
            src={item.src}
            alt=""
            width="54"
            height="54"
            loading="eager"
            draggable={false}
          />
        </span>
      ))}
    </div>
  )
}

/**
 * Lapisan latar bergerak yang memadukan seluruh 25 karakter PNG aksara Batak Toba
 * (diadaptasi dari pola animasi .at-drift Zip 1, menyatu transparan ke latar tanpa kartu lampiran).
 */
export default function AksaraDriftBackdrop({ variant = 'hero' }) {
  return (
    <div className={`aksara-drift-backdrop is-${variant}`} aria-hidden="true">
      <DriftTrack items={ROW_ONE} duration="44s" />
      <DriftTrack items={ROW_TWO} reverse={true} duration="52s" />
      <DriftTrack items={ROW_THREE} duration="40s" />
    </div>
  )
}
