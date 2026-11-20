/**
 * Adapter tunggal untuk memetakan keluaran modul transliterasi (Paket 03)
 * dan backend Mask R-CNN (Paket 02) ke antarmuka React tanpa menghitung ulang aturan di UI.
 */

export const STATUS_READING_ID = {
  DRAFT_READING: 'Draf bacaan otomatis (tanpa spasi antarkata)',
  NEEDS_REVIEW: 'Perlu ditinjau (terdapat isu pasangan, kandidat bertumpuk, atau tanda terlepas)',
  NO_PREDICTIONS: 'Tidak ada prediksi aksara yang lolos ambang confidence 0,50',
}

export const STATUS_SPACING_ID = {
  SUGGESTED: {
    title: 'Usulan spasi tersedia (perlu ditinjau)',
    note: 'Pemisahan kata berasal dari pencocokan tunggal kosakata pengembangan kosakata_toba_v2; bukan jaminan kebenaran kalimat.',
  },
  UNCHANGED: {
    title: 'Tidak ada pemisahan tambahan (perlu ditinjau)',
    note: 'Teks dasar dipertahankan tanpa penyisipan spasi baru oleh pencocokan kosakata.',
  },
  NEEDS_REVIEW: {
    title: 'Perlu ditinjau (usulan ditahan / bagian belum tunggal)',
    note: 'Usulan pemisahan kata ditahan atau terdapat bagian ambigu/belum dikenal maupun isu pembacaan.',
  },
}

export const ISSUE_LABELS_ID = {
  OVERLAPPING_INA: 'Dua huruf Ina ni Surat saling bertumpuk; bagian belum terbaca',
  SIGN_UNPAIRED: 'Tanda Anak ni Surat tidak menemukan pasangan Ina ni Surat',
  SIGN_AMBIGUOUS: 'Posisi tanda Anak ni Surat ambigu di antara kandidat Ina ni Surat',
  READING_CANDIDATE_GROUP: 'Kandidat Ina selokasi bertumpuk; modul memilih confidence tertinggi dan menyimpan alternatif',
  READING_SIGN_CANDIDATES: 'Kandidat Anak pada peran tanda yang sama bertumpuk; modul memilih confidence tertinggi dan menyimpan alternatif',
  READING_ROLE_CANDIDATES: 'Kandidat Ina dan Anak berbagi goresan; pilihan bacaan mengikuti confidence tertinggi, alternatif tetap tersedia',
  AMBIGUOUS: 'Unit baca tidak dapat dipastikan oleh aturan geometri atau skor seri',
  UNSUPPORTED: 'Kombinasi aksara atau tanda tidak didukung aturan modul',
}

export function describeReadingStatus(code) {
  return STATUS_READING_ID[code] || code || 'Perlu ditinjau'
}

export function describeSpacingStatus(wordSpacing) {
  const code = wordSpacing?.status || 'NEEDS_REVIEW'
  const meta = STATUS_SPACING_ID[code] || {
    title: code,
    note: 'Status usulan pemisahan kata dari modul transliterasi.',
  }
  return { code, ...meta }
}

export function describeIssueReason(reason) {
  return ISSUE_LABELS_ID[reason] || reason
}

export function displayReading(text) {
  return String(text ?? '').replaceAll('[?]', '⟦belum terbaca⟧')
}

export function unresolvedReadingUnits(item) {
  const tr = item?.transliteration || {}
  if (tr.presentation?.unresolved_units) return tr.presentation.unresolved_units
  return (tr.lines || []).flatMap((line) => (line.units || [])
    .map((unit, idx) => ({unit, idx}))
    .filter(({unit}) => unit.reading?.status === 'AMBIGUOUS')
    .map(({unit, idx}) => ({line_number: line.line_number, unit_number: idx + 1,
      source_instance_ids: unit.source_instance_ids || [],
      reasons: unit.reading.warnings || ['Hubungan huruf dan tanda belum dapat dipastikan.']})))
}

/**
 * Mengubah kode kelas internal (mis. "ina_nya", "anak_hauluan")
 * menjadi nama Aksara Batak Toba yang mudah dibaca masyarakat umum.
 */
export function formatAksaraLabel(rawClass) {
  if (!rawClass || typeof rawClass !== 'string') return ''
  const stripped = rawClass.replace(/^(ina|anak)_/i, '')
  return stripped
    .split('_')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Deskripsi status pembacaan yang ramah pengguna awam tanpa istilah teknis/kode.
 */
export function describePublicReadingNote(code) {
  if (code === 'NO_PREDICTIONS') {
    return 'Belum ditemukan aksara yang terbaca jelas. Pastikan pencahayaan merata dan coba unggah foto yang lebih fokus.'
  }
  if (code === 'NEEDS_REVIEW') {
    return 'Sebagian huruf atau tanda baca tampak berdekatan sehingga susunan kata mungkin perlu diperiksa kembali.'
  }
  return 'Bacaan disusun otomatis dari huruf ke huruf tanpa spasi antarkata, sesuai kaidah penulisan tradisional Batak Toba.'
}

export function adaptApiPayloadToUiItem(payload, extraMeta = {}) {
  const tr = payload.transliteration || {}
  const detections = Array.isArray(payload.detections) ? payload.detections : []
  const byId = new Map(detections.map((d) => [d.instance_id ?? d.id, d]))

  const rawText = tr.text_automatic ?? ''
  const ws = tr.word_spacing || null
  const suggestedText = ws?.suggested_text ?? rawText

  const units = []
  for (const line of tr.lines || []) {
    const lineNo = line.line_number || 1
    ;(line.units || []).forEach((u, idx) => {
      const reading = u.reading || {}
      const sourceIds = Array.isArray(u.source_instance_ids) ? u.source_instance_ids : []
      const overlayNumbers = sourceIds
        .map((iid) => byId.get(iid)?.display_number)
        .filter((n) => n !== undefined && n !== null)
      const rules = [...(reading.rules || [])]
      if (reading.orthographic_rule) {
        rules.push(reading.orthographic_rule)
      }
      const displayUnitText = reading.orthographic_text ?? reading.text ?? ''
      const literalUnitText = reading.text ?? ''
      const sourceLabels = reading.source_labels || []

      units.push({
        id: `line-${lineNo}-unit-${idx + 1}`,
        lineNo,
        unitOrder: idx + 1,
        text: displayUnitText,
        literalText: literalUnitText,
        formula: sourceLabels.length
          ? `${sourceLabels.join(' + ')} -> ${displayUnitText}`
          : `${u.kind || 'Unit'} -> ${displayUnitText}`,
        sourceLabels,
        charIds: sourceIds,
        overlayNumbers,
        inaId: u.ina_id,
        geometryRule: u.geometry_rule || '-',
        rules,
        orthographicRule: reading.orthographic_rule || null,
        alternatives: reading.alternatives || null,
        selectionStatus: reading.selection_status || null,
      })
    })
  }

  const rawAssignments = Array.isArray(tr.assignments) ? tr.assignments : []
  const unpairedAssignments = rawAssignments
    .filter((a) => a.status !== 'PROPOSED')
    .map((a) => {
      const det = byId.get(a.anak_id)
      return {
        anakId: a.anak_id,
        displayNumber: det?.display_number ?? null,
        classLabel: det?.rawClass || det?.cls || '-',
        score: det?.score ?? null,
        status: a.status,
        geometryBasis: a.geometry_basis,
      }
    })

  const rawIssues = Array.isArray(tr.issues) ? tr.issues : []
  const warnings = rawIssues.map(
    (iss) =>
      `[${iss.reason}] ${describeIssueReason(iss.reason)} (ID instansi: ${(iss.instance_ids || []).join(', ')})`,
  )

  const mapCandidateGroup = (g, prefix, idx, ids) => {
    const alts = g.alternatives || []
    const isTied = g.selection_status === 'TIED_CONFIDENCE' || g.selected_instance_id == null
    const winner = isTied
      ? null
      : alts.find((a) => a.instance_id === g.selected_instance_id) || null
    return {
      groupId: `${prefix}-${idx + 1}`,
      locationLabel: `Kelompok ID [${ids.join(', ')}]`,
      selectionStatus: g.selection_status,
      selectedInstanceId: g.selected_instance_id,
      chosen: winner
        ? {
            instanceId: winner.instance_id,
            cls: winner.class_label,
            latin: winner.base_latin || formatAksaraLabel(winner.class_label),
            score: winner.score,
          }
        : null,
      alternatives: alts.map((a) => ({
        instanceId: a.instance_id,
        cls: a.class_label,
        latin: a.base_latin || formatAksaraLabel(a.class_label),
        score: a.score,
      })),
    }
  }

  const overlappingCandidates = [
    ...(tr.role_candidate_groups || [])
      .filter((g) => (g.instance_ids || []).length > 1)
      .map((g, idx) => mapCandidateGroup(g, 'P', idx, g.instance_ids || [])),
    ...(tr.reading_candidate_groups || [])
      .filter((g) => (g.ina_ids || []).length > 1)
      .map((g, idx) => mapCandidateGroup(g, 'K', idx, g.ina_ids || [])),
    ...(tr.sign_candidate_groups || [])
      .filter((g) => (g.sign_ids || []).length > 1)
      .map((g, idx) => mapCandidateGroup(g, 'T', idx, g.sign_ids || [])),
  ]

  return {
    id: extraMeta.id || payload.id || `CITRA_${Date.now()}`,
    label: extraMeta.label || payload.label || payload.source_name || 'Citra Aksara',
    publicLabel:
      extraMeta.publicLabel ||
      payload.publicLabel ||
      extraMeta.label ||
      payload.label ||
      payload.source_name ||
      'Foto Aksara',
    subtitle:
      extraMeta.subtitle ||
      (tr.text_status === 'NO_PREDICTIONS'
        ? '0 deteksi lolos ambang 0,50'
        : `${detections.length} instansi · Status: ${tr.text_status || '-'}`),
    publicSubtitle:
      extraMeta.publicSubtitle ||
      (tr.text_status === 'NO_PREDICTIONS'
        ? 'Belum ada aksara terbaca'
        : `${detections.length} aksara terbaca`),
    src: extraMeta.src || payload.src,
    originalSrc: extraMeta.originalSrc || payload.originalSrc || extraMeta.src || payload.src,
    sourceName: payload.source_name,
    sourceSha256: payload.source_sha256,
    inputHw: payload.input_hw,
    rawLatinText: rawText,
    latinText: suggestedText,
    literalText: tr.text_literal ?? '',
    readingStatus: tr.text_status || 'NEEDS_REVIEW',
    spacingStatus: describeSpacingStatus(ws).title,
    spacingStatusCode: ws?.status || 'NEEDS_REVIEW',
    wordSpacing: ws,
    syllables: units,
    detections,
    rawPredictionsSource: payload.raw_predictions_source || [],
    issues: rawIssues,
    warnings,
    overlappingCandidates,
    unpairedAssignments,
    transliteration: tr,
    modelIdentity: payload.model_identity || null,
    lexicon: payload.lexicon || null,
    researchExports: payload.research_exports || null,
    cacheKey: payload.cache_key || extraMeta.id || payload.id || payload.source_sha256 || null,
    inferenceSeconds: payload.inference_seconds ?? null,
    isLiveInference: Boolean(extraMeta.isLiveInference),
  }
}

/**
 * Warna unik golden-ratio per instansi mengikuti visual.instance_color di Paket 02.
 */
export function instanceColor(displayNumber) {
  const n = Math.max(1, Number(displayNumber) || 1)
  const hue = (0.56 + (n - 1) * 0.38196601125) % 1
  const h = Math.round(hue * 360)
  return `hsl(${h}, 78%, 48%)`
}

export function buildTransliterationTxt(item, editedText = '') {
  if (!item) return ''
  const tr = item.transliteration || {}
  const ws = item.wordSpacing || {}
  const spacingMeta = describeSpacingStatus(ws)
  const model = item.modelIdentity || {}
  const textAuto = item.rawLatinText || '(tidak ada bacaan lolos threshold 0,50)'
  const autoFormatted = displayReading(textAuto)
  const suggested = ws?.suggested_text || textAuto
  const literal = item.literalText || '(kosong)'
  const cleanEdited = typeof editedText === 'string' ? editedText.trim() : ''

  const lines = [
    `Sumber citra: ${item.sourceName || item.label || '-'}`,
    `Model: ${model.architecture || 'Mask R-CNN ResNet-50-FPN'} (Epoch ${model.epoch ?? 28})`,
    `Checkpoint SHA256: ${model.checkpoint_sha256 || tr.checkpoint_sha256 || '-'}`,
    `Versi modul / aturan: ${tr.version || '-'} / ${tr.rules_version || '-'}`,
    '',
    `Hasil transliterasi otomatis: ${autoFormatted}`,
  ]
  if (cleanEdited && cleanEdited !== autoFormatted) {
    lines.push(`Suntingan pengguna: ${cleanEdited}`)
  }
  lines.push(
    `Usulan pemisahan kata: ${displayReading(suggested)}`,
    `Status usulan spasi: ${ws?.status || '-'} (${spacingMeta.title})`,
    `Keterangan spasi: ${spacingMeta.note}`,
    `Perlu tinjauan (review_required): ${String(ws?.review_required ?? true)}`,
    `Alasan tinjauan: ${(ws?.review_reasons || []).join(', ') || '-'}`,
    `Bacaan literal (sebelum normalisasi Ya/Wa): ${displayReading(literal)}`,
    `Status bacaan modul: ${item.readingStatus} (${describeReadingStatus(item.readingStatus)})`,
  )

  unresolvedReadingUnits(item).forEach((u) => lines.push(
    `Belum terbaca: baris ${u.line_number}, unit ${u.unit_number}, ID ${(u.source_instance_ids || []).join(', ')}: ${(u.reasons || []).join(' ')}`,
  ))
  if (item.warnings?.length) {
    lines.push('', `Peringatan & catatan (${item.warnings.length}):`)
    item.warnings.forEach((w, idx) => lines.push(`  ${idx + 1}. ${w}`))
  }

  return lines.join('\n') + '\n'
}

export function buildTransliterationJson(item) {
  if (!item) return '{}'
  const tr = item.transliteration || {}
  const overlayMap = {}
  for (const d of item.detections || []) {
    if (d.display_number != null) {
      overlayMap[String(d.instance_id ?? d.id)] = d.display_number
    }
  }
  const doc = {
    source_name: item.sourceName || item.label,
    source_sha256: item.sourceSha256 || tr.source_sha256 || null,
    display_threshold: tr.display_threshold ?? 0.5,
    model_identity: item.modelIdentity || {
      architecture: 'Mask R-CNN ResNet-50-FPN',
      backbone_depth: 50,
      epoch: 28,
      checkpoint_sha256: tr.checkpoint_sha256 || null,
    },
    modul_version: tr.version || null,
    rules_version: tr.rules_version || null,
    prediksi_sumber_tampil: (item.detections || []).map((d) => ({
      instance_id: d.instance_id ?? d.id,
      display_number: d.display_number,
      category_id: d.category_id,
      class_label: d.rawClass,
      score: d.score,
      bbox_xyxy: d.bbox_xyxy,
    })),
    peta_id_ke_nomor_overlay: overlayMap,
    hasil_modul: tr,
  }
  return JSON.stringify(doc, null, 2)
}

const API_BASE = (import.meta.env?.VITE_API_BASE || '').replace(/\/+$/, '')

export async function fetchApiHealth() {
  const res = await fetch(`${API_BASE}/api/health`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function fileOrDataUrlToBase64(src) {
  if (typeof src === 'string' && src.startsWith('data:')) {
    return src
  }
  const resp = await fetch(src)
  const blob = await resp.blob()
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('Gagal membaca berkas citra'))
    reader.readAsDataURL(blob)
  })
}

export async function predictImageViaApi({ filename, imageSrc }) {
  const imageBase64 = await fileOrDataUrlToBase64(imageSrc)
  const res = await fetch(`${API_BASE}/api/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, image_base64: imageBase64 }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.error || `Gagal menghubungi server inferensi (HTTP ${res.status})`)
  }
  return data
}

export async function renderOverlayViaApi({ cacheKey, mode = 'Mask + Bbox', opacity = 0.65, focus = null }) {
  const res = await fetch(`${API_BASE}/api/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      cache_key: cacheKey,
      mode,
      opacity,
      focus,
    }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.error || `Render overlay gagal (HTTP ${res.status})`)
  }
  return `data:image/png;base64,${data.overlay_png_b64}`
}

export async function predictSampleViaApi(sampleId) {
  const res = await fetch(`${API_BASE}/api/sample`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sample_id: sampleId }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.error || `Gagal menjalankan modul pada sampel (HTTP ${res.status})`)
  }
  return data
}
