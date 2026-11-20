# Audit Pembaruan Transliterasi v0.5.1 (Ina Komposit, Konflik Mask Tanda, & Anak Terkandung)

Tanggal: 20 November 2026. Versi susun: `0.5.1-composite-ina-and-mask-sign-conflicts`.
Perubahan dilakukan pada modul transliterasi (`susun_prediksi.py`), unit test (`uji_kandidat_anak.py`, `uji_konflik_peran.py`, `uji_penyajian_web.mjs`), dan penyegaran sampel & antarmuka web (`04_WEB_APP_BATAK_TOBA`) tanpa mengubah `02_AKSARABATAKTOBA_TERBARU`, checkpoint, dataset, prediksi tersimpan, metrik evaluasi asli, atau berkas Word.

## Rencana dan perubahan algoritma (`susun_prediksi.py` v0.5.1)

1. **Resolusi Anak terkandung penuh di dalam mask Ina berskor lebih tinggi (`CONTAINED_ANAK_IN_INA_MASK`)**:
   - Sub-langkah kedua pada `select_role_candidates` memeriksa kandidat Anak berskor **lebih rendah** daripada Ina yang tidak sedang seri, dengan luas mask `anak_area <= ina_area`, `mask_containment >= 0,90`, dan `bbox_containment >= 0,90`.
   - Tidak memaksa menekan Anak ber-confidence lebih tinggi; semua ID dan daftar `role_candidate_groups` dipertahankan untuk audit.
2. **Penyerapan kandidat Ina komposit/membentang (`COMPOSITE_SPANNING_INA_MASK`)**:
   - `select_reading_anchors` menjalankan `composite_mask_coverage` atas kandidat terpilih yang tidak seri. Jika `>= 2` Ina terpilih dengan skor lebih tinggi masing-masing menyumbang irisan `>= 0,30` (terhadap area terkecil) dan `>= 0,15` (terhadap area kandidat) serta union mask-nya menutupi `>= 0,80` area kandidat, kandidat komposit diserap ke Ina host tumpang tindih terbesar sambil menyimpan alternatif dan bukti di `reading_candidate_groups`.
3. **Resolusi konflik tanda Anak berbagi mask pada Ina yang sama (`SHARED_MASK`)**:
   - Sebelum pemilahan peran logis (`VOWEL`, `FINAL_NG`, `KILLER`) per Ina di `arrange`, tanda-tanda yang menempel pada Ina yang sama dikelompokkan berbasis `bbox_iou >= 0,25` dan `mask_iou >= 0,50`. Skor tertinggi menang (skor seri tetap menahan `pending_signs` agar unit berstatus `AMBIGUOUS`), alternatif dan bukti disimpan pada `sign_candidate_groups` dengan `role="SHARED_MASK"`.
4. **Penjaga vokal mandiri pada pengurutan suku kata tertutup (`DRAFT_CLOSED_SYLLABLE_REORDER`)**:
   - `base["category_id"] not in (17, 18)` memastikan `ina_i` dan `ina_u` tidak mengambil tanda vokal dari konsonan penutup berpangolat di kanannya, selaras dengan `transliterasi.py`.

## Hasil yang dibuktikan (131 citra uji tersimpan, tanpa inferensi/training baru)

| ID | Citra | Sebelum (0.5.0) | Sesudah (0.5.1) | Keterangan |
|---|---|---|---|---|
| 4 | `P07_N04_004.png` | `[?]la[?][?]` | `unglos` | Komposit `ina_sa` (`9`) diserap ke `3`, konflik mask `haminsaran` (`7`) vs `hatadingan` (`8`) dimenangkan `7`. |
| 43 | `P10_N12_012.png` | `dongen` | `dongan` | Ekstra `anak_hatadingan` (`5`, `0,890`) terkandung di dalam mask `ina_na` (`4`, `0,988`). |
| 70 | `P08_C009_F02_25-27.png` | `rohanadenggen` / `[?]nianggi` / `podanadagan` | `rohanadenggan` / `u[?]nianggi` / `podanadagan` | Baris 1 membaik ke `rohanadenggan`; baris 2 menyelamatkan vokal mandiri `ina_u`. |

- Kasus `ID 60`: `pred#11` (`anak_hatadingan` tambahan, `mcont=0,972` di dalam `ina_ya` `pred#9`) kini diselesaikan pada tahap `role_candidate_groups`; `text_automatic` tetap `aeknatio` dan semua 11 ID tampil terkonservasi.
- Kasus `ID 58`: tetap `buhunianggi` tanpa regresi.
- Sisa unit belum pasti (`[?]` / `⟦belum terbaca⟧`): **4 citra** (`ID 30, 68, 70, 124`), turun dari 5 citra pada `0.5.0` — seluruhnya disebabkan oleh keterbatasan prediksi model pada citra asli (`u+e`, salah kelas menjadi `haminsaran`+`pangolat`, `sihora > ina_sa` pada `la`, serta `sihora+pangolat` asli pada `ID 124`), bukan karena gagal membaca pasangan yang sah.

## Verifikasi perangkat lunak

- **132 tes Python lulus** di WSL (`UJI_WSL.txt`): seluruh tes lama plus kasus nyata `ID 4, 43, 58, 60, 70` dan uji negatif sintetis v0.5.1.
- **Audit `audit.py` lulus**: `distinct_matched_gt_group_conflicts == []`, `reference_regressions == []`, `655/655` uji invariansi urutan/skala/translasi lulus (`invariance_failures == []`), seluruh visible ID terkonservasi, dan nol tanda `?` pada `presentation`.
- **Tes JS `uji_penyajian_web.mjs` lulus** (`UJI_WEB.txt`): `images: 131, unresolved_images: 4`.
- **CER diagnostik ekspos-PDF tanpa spasi** (bukan metrik model atau evaluasi independen): turun dari `81/1063` (`7,6199%`, `96` cocok utuh) menjadi `70/1063` (`6,5851%`, `97` cocok utuh).
