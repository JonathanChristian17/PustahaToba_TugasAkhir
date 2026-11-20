# Kontrak modul yang diusulkan

## Konflik peran, ambiguitas lokal dan penyajian, 18 November 2026

Versi0.5.0 menyelesaikan kandidat berbagi mask lintas Ina–Anak sebelum mengurutkan Ina dan memasangkan tanda. Bukti maskIoU>=0,50 dan bboxIoU>=0,25 diperiksa complete-link. Pemenang ditentukan confidence; skor seri tetap tidak dipastikan. Semua alternatif berada pada `role_candidate_groups`; tidak ada penggantian kelas ke GT. Kandidat Ina berupa fragmen satu kolom juga dapat memakai bukti maskIoU>=0,50 dengan overlap horizontal>=0,90 dan jarak pusat horizontal<=0,15lebarterbesar, tanpa harus memenuhi bboxIoUminimum; ini hipotesis fragmentasi, bukan jaminan identitas fisik.

Ambiguitas pasangan tanda dicatat per tanda/calonIna melalui `pending_sign_ids`, tanpa memasukkan semua tetangga ke blocked global. Pasangan tanda lain yang unik tetap diproses; unit dengan tanda relevan yang masih ambigu tetap ditandai. Skor seri kandidat dan konflik Ina lain tetap dapat memblokir unit. Analisis suku tertutup memakai kandidat yang tersisa setelah resolusi peran, sehingga tanda yang merupakan alternatif role Ina tidak lagi otomatis mengisi onset sebagai Anak.

`source_instance_ids` pada unit dan assignment tanpa pasangan mencakup semua ID alternatif peran. Konservasi ID harus memakai sumber assignment tersebut, bukan hanya satu `anak_id`. `visible_instance_ids` dan semua prediksi asli tidak diubah.

Atas pilihan pengguna, field baru `presentation` menyajikan `[?]` sebagai `⟦belum terbaca⟧`, menyimpan daftar unit/ID/alasan, dan daftar tanda tanpa pasangan. `text_automatic`, `text_literal` dan `word_spacing` tetap keluaran diagnostik asli: tidak dihapus atau diisi dari PDF. `has_unresolved_units=false` bukan jaminan teks lengkap/benar karena karakter yang tidak terdeteksi atau salah kelas dapat tidak diketahui oleh modul.

Web04 memakai format penyajian yang sama pada halaman baca, hasil penelitian, riwayat, salin teks dan TXT. JSON mempertahankan teks diagnostik dan jejak asli. Tidak boleh menghitung CER dari string `⟦belum terbaca⟧`; evaluator menggunakan teks diagnostik asli dengan protokol yang dijelaskan. Pengesahan bahasa dan spasi masih belum dijamin.

## Kandidat tanda dalam peran logis yang sama, 18 November 2026

Versi susun0.4.5 menambahkan pemilihan bacaan ketika beberapa tanda telah dipasangkan secara geometri ke Ina yang sama dan saling menempati satu peran logis: satu vokal dari kelas19–22, satu final ng, atau satu pangolat. Ini bukan pernyataan bahwa semua kandidat berasal dari objek fisik yang sama. Kandidat confidence tertinggi dipakai untuk bacaan; skor seri tetap ambigu. Vokal dan ng adalah peran berbeda dan boleh dipakai bersama. Konflik vokal+pangolat tetap memerlukan analisis suku tertutup/penanda ambigu, tidak diselesaikan dengan membuang salah satunya.

`sign_candidate_groups` tersedia pada hasil dan unit terkait, memuat peran, Ina asal, semua kandidat ID/kelas/score serta ID pilihan. `assignments` tetap mencatat pasangan geometri seluruh tanda, dengan tambahan `reading_selected`/`reading_role` pada tanda yang bersaing. `source_instance_ids` tetap mencakup alternatif yang tidak dipilih dan semua tanda pada konsonan penutup yang dikonsumsi. Tidak ada perubahan atau penghapusan prediksi mentah.

Catatan `READING_SIGN_CANDIDATES` membuat hasil tetap perlu tinjauan walaupun teks dapat dibentuk. Tanda yang confidence tertingginya salah tetap dapat menghasilkan huruf salah. Tidak ada pemaksaan semua teks bebas `[?]`; skor seri, tanda tanpa pasangan, atau kombinasi lain yang tidak dapat dipastikan tetap ditandai. Mesin aturan `transliterasi.py` tidak dilonggarkan untuk menerima kombinasi tidak sah. Angka CER versi sebelumnya tetap arsip versi tersebut.

## Kandidat Ina berbasis mask, 18 November 2026

Versi susun0.4.4 menambahkan bukti selokasi dari mask RLE: bbox IoU minimal0,25 dan mask IoU minimal0,50. Bukti ini menjadi alternatif terhadap geometri bbox sebelumnya, bukan perubahan NMS. Hanya kandidat Ina yang dikelompokkan; mask Anak tetap menjadi hasil prediksi asli dan pemasangannya mengikuti geometri modul. Semua pasangan dalam kelompok harus memenuhi bukti selokasi (complete-link), bukan penggabungan rantai transitif.

Pemenang confidence dipilih sebelum memasangkan Anak; skor seri tetap ambigu. Semua ID, kelas, score dan mask asli tetap tersedia. Keluaran kelompok mencatat `SHARED_FOREGROUND_MASK`, bboxIoU, maskIoU, luas mask dan intersection. Tidak ada nama kelas tertentu atau nama citra dalam keputusan. RLE compressed/uncompressed dibaca melalui interval foreground tanpa mengubah mask dan tanpa dependensi runtime baru. Bila mask tidak tersedia, tidak valid, kosong atau dimensi berbeda, bukti tambahan mask tidak digunakan; aturan bbox lama tetap berlaku.

Penggunaan mask menggantikan deskripsi lama BBOX_ONLY: pemasangan tanda masih berdasarkan bbox, sedangkan bukti tambahan kandidat Ina memakai mask. Pengelompokan merupakan hipotesis geometri/segmentasi, bukan verifikasi identitas objek yang dijamin pada setiap citra baru. Angka CER tahap10 berasal dari versi0.4.3; jangan menganggapnya otomatis mewakili keluaran versi0.4.4.

## Pengetatan usulan spasi, 17 November 2026

Setiap `word_spacing` kini memuat `review_required=true` dan `review_reasons`. Pembagian tunggal menurut kosakata tetap berupa usulan, bukan validasi bahasa. Jika bacaan memiliki `issues`, teks usulan keseluruhan ditahan sama dengan `text_automatic` dan status menjadi `NEEDS_REVIEW`; kandidat tiap bagian tetap tersedia untuk ditinjau. Kebijakan ini juga dapat menahan usulan yang sebenarnya benar. Tidak ada ambang confidence baru atau aturan khusus nama citra.

Kosakata v2 tersedia secara terpisah sebagai `kosakata_toba_v2.json`: token yang seluruh kemunculannya berupa huruf kapital penuh dikeluarkan dari korpus. Filter ini tidak dapat menjamin semua token yang tersisa benar atau semua token yang dikeluarkan salah. Kosakata v1 dipertahankan. Pengguna CLI harus memilih v2 secara eksplisit; tidak ada pengaktifan otomatis di web.

## Tambahan implementasi: usulan spasi opsional, 17 November 2026

`arrange(document, lexicon=None)` mempertahankan keluaran lama bila kosakata tidak diberikan. CLI menerima `--lexicon` berupa JSON berisi `language=batak_toba`, `source`, `license`, `revision` dan `words`. Tidak ada kamus yang dibaca otomatis dari PDF, nama citra atau dataset penelitian.

Jika kosakata diberikan, keluaran tambahan `word_spacing` memuat `original_text`, `suggested_text`, status, bagian yang diperiksa, sumber kosakata dan hash dokumen kosakata yang diserialisasi secara kanonik. `text_automatic`, `text_literal`, unit, pasangan dan prediksi asli tetap. `word_boundaries=NOT_INFERRED` pada keluaran lama tetap merujuk pada bacaan dasar; usulan berbasis kosakata berada di field terpisah.

Spasi hanya disisipkan pada batas unit baca yang sudah terbentuk dan hanya untuk pembagian tunggal sesuai kosakata. Pencarian menghitung paling banyak dua jalur; daftar kandidat bukan peringkat atau seluruh kemungkinan. Bagian ambigu, tidak dikenal atau mengandung penanda/pungtuasi yang tidak didukung tetap disimpan apa adanya. Whitespace yang sudah ada dipertahankan. Tidak ada penggantian huruf, kapitalisasi, normalisasi h/k tambahan, pengisian karakter hilang atau confidence kalimat. Pembagian tunggal menurut kosakata belum menjamin benar secara bahasa.

Status bagian: UNIQUE, AMBIGUOUS, UNKNOWN, UNSUPPORTED_OR_AMBIGUOUS_INPUT. Status keseluruhan: SUGGESTED, UNCHANGED, NEEDS_REVIEW. Status tersebut bukan metrik akurasi.

Kosakata pengembangan saat ini diturunkan dari korpus eksternal terbuka pada `01_ATURAN/KOSAKATA_EKSTERNAL/`, bukan kamus ahli yang sudah disahkan. Fitur diaktifkan secara eksplisit; tidak ada perubahan pada model atau web app.

## Spesifikasi awal

Status: spesifikasi sebelum implementasi.

Masukan berasal dari keluaran backend Eksperimen 2 yang sudah ada: `input_hw`, `checkpoint_sha256`, `display_threshold`, dan daftar prediksi dengan `instance_id`, `display_number`, `category_id`, `class_label`, `score`, `bbox_xyxy`, `segmentation`, serta `displayed`.

Modul hanya membaca salinan instansi yang lolos confidence 0,50 untuk pembacaan utama. Semua prediksi mentah tetap tersimpan. Prediksi tidak diurutkan ulang secara in-place dan tidak ditulis kembali ke dataset.

Keluaran baru yang diusulkan:

| Atribut | Isi |
|---|---|
| versi_aturan | Versi peta dan kebijakan transliterasi |
| teks_otomatis | Teks hasil pembacaan otomatis, termasuk penanda ambigu |
| baris | Pengelompokan dan urutan baca |
| unit_baca | Ina, Anak terkait, nilai Latin dan ID sumber masing-masing |
| ambigu | Tanda lepas, pasangan bersaing, prediksi ganda atau batas kata tidak pasti |
| jejak_aturan | Aturan yang diterapkan per unit |
| teks_suntingan | Opsional, disimpan terpisah setelah tindakan pengguna |

Batas modul:

- Tidak membaca Latin referensi, daftar stimulus, nama responden atau nama file untuk menentukan hasil teks.
- Tidak menambahkan prediksi karakter yang hilang agar sesuai kata yang dikenal.
- Tidak mengubah threshold/NMS atau menyembunyikan prediksi bertumpang tindih.
- Tidak menghasilkan akurasi atau confidence kalimat dari rata-rata confidence karakter.
- Tidak memanggil LLM untuk melengkapi kata atau kalimat.

Perhitungan ketepatan teks dilakukan modul pengujian terpisah terhadap referensi yang sudah diperiksa. Ketika algoritma memilih alternatif untuk pembacaan, keputusan dan semua kandidat asal tetap dicatat; label dan skor asli model tidak berubah.
