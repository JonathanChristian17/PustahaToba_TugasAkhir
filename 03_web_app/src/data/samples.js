import realSamples from './realSamples.json'
import { adaptApiPayloadToUiItem } from '../utils/transliterationAdapter.js'

export const MODEL_IDENTITY = {
  architecture: 'Mask R-CNN ResNet-50 FPN',
  backboneDepth: 50,
  epoch: 28,
  totalEpochs: 30,
  checkpoint: 'R50 Epoch 28 (dari pelatihan 30 epoch)',
  numClasses: 25,
  scoreThreshold: 0.5,
  evaluationNote:
    'Evaluasi dataset penelitian (131 citra uji): CA 95,43%, Mask AP50:95 60,38%. Angka ini adalah metrik pengujian penelitian, bukan klaim akurasi pada unggahan baru.',
}

export const SAMPLE_IMAGES = realSamples.map((raw, idx) =>
  adaptApiPayloadToUiItem(raw, {
    id: raw.id,
    label: raw.label,
    publicLabel: `Contoh Tulisan ${idx + 1}`,
    src: raw.src,
    originalSrc: raw.src,
  }),
)
