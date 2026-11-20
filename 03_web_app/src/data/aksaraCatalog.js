export const CULTURAL_MEDIA = {
  gorga: {
    src: '/imageweb/gorgabatak.webp',
    alt: 'Ukiran tradisional Gorga Batak Toba',
    caption: 'Motif ukiran Gorga Batak Toba',
  },
  ulos: {
    src: '/imageweb/motifulos.jpg',
    alt: 'Pola tenun tradisional Ulos Batak Toba',
    caption: 'Pola tenun Ulos Batak Toba',
  },
}

export const INA_NI_SURAT = [
  { id: '01', rawClass: 'ina_a', name: 'A', latin: 'a', src: '/imageweb/01_ina_a.png' },
  { id: '02', rawClass: 'ina_ha', name: 'Ha', latin: 'ha / ka', src: '/imageweb/02_ina_ha.png' },
  { id: '03', rawClass: 'ina_na', name: 'Na', latin: 'na', src: '/imageweb/03_ina_na.png' },
  { id: '04', rawClass: 'ina_ra', name: 'Ra', latin: 'ra', src: '/imageweb/04_ina_ra.png' },
  { id: '05', rawClass: 'ina_ta', name: 'Ta', latin: 'ta', src: '/imageweb/05_ina_ta.png' },
  { id: '06', rawClass: 'ina_ba', name: 'Ba', latin: 'ba', src: '/imageweb/06_ina_ba.png' },
  { id: '07', rawClass: 'ina_wa', name: 'Wa', latin: 'wa', src: '/imageweb/07_ina_wa.png' },
  { id: '08', rawClass: 'ina_ma', name: 'Ma', latin: 'ma', src: '/imageweb/08_ina_ma.png' },
  { id: '09', rawClass: 'ina_nga', name: 'Nga', latin: 'nga', src: '/imageweb/09_ina_nga.png' },
  { id: '10', rawClass: 'ina_la', name: 'La', latin: 'la', src: '/imageweb/10_ina_la.png' },
  { id: '11', rawClass: 'ina_pa', name: 'Pa', latin: 'pa', src: '/imageweb/11_ina_pa.png' },
  { id: '12', rawClass: 'ina_sa', name: 'Sa', latin: 'sa', src: '/imageweb/12_ina_sa.png' },
  { id: '13', rawClass: 'ina_da', name: 'Da', latin: 'da', src: '/imageweb/13_ina_da.png' },
  { id: '14', rawClass: 'ina_ga', name: 'Ga', latin: 'ga', src: '/imageweb/14_ina_ga.png' },
  { id: '15', rawClass: 'ina_ja', name: 'Ja', latin: 'ja', src: '/imageweb/15_ina_ja.png' },
  { id: '16', rawClass: 'ina_ya', name: 'Ya', latin: 'ya', src: '/imageweb/16_ina_ya.png' },
  { id: '17', rawClass: 'ina_nya', name: 'Nya', latin: 'nya', src: '/imageweb/17_ina_nya.png' },
  { id: '18', rawClass: 'ina_i', name: 'I', latin: 'i', src: '/imageweb/18_ina_i.png' },
  { id: '19', rawClass: 'ina_u', name: 'U', latin: 'u', src: '/imageweb/19_ina_u.png' },
]

export const ANAK_NI_SURAT = [
  {
    id: '20',
    rawClass: 'anak_hatadingan',
    name: 'Hatadingan',
    latin: 'mengubah vokal menjadi /e/',
    example: 'te',
    src: '/imageweb/20_anak_hatadingan.png',
    exampleSrc: '/imageweb/20_anak_hatadingan_te.png',
  },
  {
    id: '21',
    rawClass: 'anak_hauluan',
    name: 'Hauluan',
    latin: 'mengubah vokal menjadi /i/',
    example: 'ti',
    src: '/imageweb/21_anak_hauluan.png',
    exampleSrc: '/imageweb/21_anak_hauluan_ti.png',
  },
  {
    id: '22',
    rawClass: 'anak_siala',
    name: 'Siala',
    latin: 'mengubah vokal menjadi /o/',
    example: 'to',
    src: '/imageweb/22_anak_siala.png',
    exampleSrc: '/imageweb/22_anak_siala_to.png',
  },
  {
    id: '23',
    rawClass: 'anak_haborotan',
    name: 'Haborotan',
    latin: 'mengubah vokal menjadi /u/',
    example: 'tu',
    src: '/imageweb/23_anak_haborotan.png',
    exampleSrc: '/imageweb/23_anak_haborotan_tu.png',
  },
  {
    id: '24',
    rawClass: 'anak_haminsaran',
    name: 'Haminsaran',
    latin: 'menambah bunyi sengau /-ng/',
    example: 'tang',
    src: '/imageweb/24_anak_haminsaran.png',
    exampleSrc: '/imageweb/24_anak_haminsaran_tang.png',
  },
  {
    id: '25',
    rawClass: 'anak_pangolat',
    name: 'Pangolat',
    latin: 'menghilangkan vokal /a/ (konsonan mati)',
    example: 't',
    src: '/imageweb/25_anak_pangolat.png',
    exampleSrc: '/imageweb/25_anak_pangolat_t.png',
  },
]

const ALL_CLASSES = [...INA_NI_SURAT, ...ANAK_NI_SURAT]

export function getGlyphAssetByRawClass(rawClass) {
  return ALL_CLASSES.find((item) => item.rawClass === rawClass) || null
}
