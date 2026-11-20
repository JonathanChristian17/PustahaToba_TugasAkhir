# Rancangan pengembangan transliterasi

## Versi aktif0.5.0 — 18 November 2026

Pengelompokan lintasInaAnak, kandidatfragmen dan ambiguitaslokal telah diperbaiki. Poda/ulos/suku kata porlak pada kasus yang diperiksa kembali terbaca. Hasil takpasti pada5citra tetap disajikan sebagai⟦belum terbaca⟧besertaalasan sesuai pilihan pengguna; JSON menyimpan diagnostik asli, bukan huruf tebakan. Salahkelas dan tanda hilang tetap dapat menghasilkan kesalahan.130tesPython,tesJS131hasil,regresi131citra/655variasi dan buildweb lulus. API04sudahdimuat ulang0.5.0;4sampelbawaan diperbarui darihasilmodeltersimpan. Tidak ada training/inferensi baru atau perubahan paket02/Word. Laporan `05_HASIL/TAHAP_14_KONFLIK_PERAN/LAPORAN.md` menjelaskan perubahan dan keterbatasan; angkaCERlama tetaparsipversilama.

## Pembaruan tanda bersaing — 18 November 2026

Mesin terbaru0.4.5 memilih kandidat tanda tertinggi ketika beberapa tanda yang telah dipasangkan ke satu Ina bersaing pada peran logis sama. Semua alternatif/prediksi tetap. P14_N24 danP10_N29 kini aeknatio; tidak menggunakan jawabanPDF.121tes lulus;131citra/655variasi diperiksa tanpa regresi bacaan yang sebelumnya cocokPDF. Masih10citra berpenandaambigu, bukan janji bahwa semua bacaan benar. Laporan: `05_HASIL/TAHAP_12_KANDIDAT_ANAK/LAPORAN.md`.

Web04 mengimpor mesin03, tetapi proses yang sudah hidup perlu restartbackend dan prosesulang untuk memakai0.4.5. Tidak ada kodeweb/02/model/data/prediksi/metrik/Word yang diubah pada tahap12. CER diagnostik terbaru dibedakan dari angka arsip tahap10/11; semua masih perbandingan pengembangan terhadap acuan yang belum seluruhnya disahkan.

## Pembaruan kandidat mask — 18 November 2026

Mesin susun terbaru0.4.4 memakai bukti tambahan mask RLE untuk kandidat Ina ketika bbox belum cukup. P14_N17 terbaca nyi; satu kasus Pa ganda juga membaik.113tes lulus,131citra/655variasi diperiksa dan1579mask dibanding decoder resmi. Tidak ada jaminan semua citra baru bebas ambigu. Pemasangan Anak tetap memakai bbox; prediksi model tetap utuh. Laporan `05_HASIL/TAHAP_11_KELOMPOK_MASK/LAPORAN.md` menggantikan kesimpulan sebelumnya bahwa tidak ditemukan masalah tambahan dalam cakupan pemeriksaan lama.

Penghubung aplikasi React pada paket04 telah tersedia; tesnya memakai modul03. Proses API yang sudah hidup perlu restart untuk mengambil perubahan modul; browser langsung belum diverifikasi dalam tahap11. Tidak ada kode web atau paket02 yang diubah. Hasil CER tahap10 adalah versi0.4.3; diagnostik versi0.4.4 dicatat terpisah pada laporan tahap11, bukan penggantian metrik lama.

## Status terbaru — 18 November 2026

Pemeriksaan minor selesai: 92 tes lulus, 131 keluaran identik tahap08 dan 655 pemeriksaan perubahan urutan/skala/translasi bbox tanpa kegagalan. Tiga kasus jabuob, aek ni hata dan porlak ni na nang tetap memerlukan tinjauan; tidak diganti hurufnya untuk mencocokkan PDF. Kebijakan h/k sudah diterapkan, buhu tidak otomatis menjadi buku. Koreksi P10_N23 sudah diuji pada salinan terpisah dan belum diaktifkan sebagai data utama. Pernyataan lama di bawah bahwa koreksi belum dieksekusi merupakan riwayat sebelum pekerjaan tersebut.

Usulan spasi v2 tetap opsional dan memerlukan pemeriksaan bahasa. Web belum diubah. Laporan terbaru: `05_HASIL/TAHAP_09_PENUTUPAN_MINOR/LAPORAN.md`; rincian spasi: `05_HASIL/TAHAP_08_SPASI_KONSERVATIF/LAPORAN.md`. Tidak ada perubahan mesin modul, model, data, metrik atau Word pada tahap09; perubahan terbatas pada tes regresi dan dokumentasi.

## Status aktif — 17 November 2026

Audit terbaru enam perbedaan GT/PDF menemukan **penghapusan goresan Ja pada P10_N23 saat cleanup** (3.996 piksel), disertai label snapshot Ja versus label testing aktif Da pada poligon identik. Kasus ini perlu koreksi sumber pada salinan versi baru dan pemeriksaan ulang terkait; belum dieksekusi. Lima kasus lain mempunyai perbedaan yang sudah tampak pada sumber Enhance atau memerlukan konfirmasi identitas bentuk. Modul tetap 0.4.3; tidak ada perubahan model/data/hasil/UI. Baca `05_HASIL/AUDIT_ENAM_GT_PDF_20261117/LAPORAN.md` atau `TINJAU_ENAM_KASUS.html` pada folder yang sama. Pemeriksaan ini memperinci penyebab perbedaan yang sebelumnya hanya dicatat sebagai GT–PDF.

Pembaruan terbaru **0.4.3**: kandidat Ina berkotak hampir saling mencakup kini dapat dikelompokkan untuk memilih confidence tertinggi pada jalur Latin. P07_N02 berubah **daina → ina**; ng yang tidak terdeteksi tetap tidak ditambahkan. Semua 131 citra diuji; empat bacaan berubah, 127 tetap; tidak ada regresi kesesuaian acuan atau kelompok yang menyatukan dua GT berbeda menurut matching tersimpan. **70 uji perangkat lunak lulus** Windows/WSL. Semua prediksi asli tetap disimpan; tidak ada perubahan model/NMS/threshold/UI. Laporan: `05_HASIL/TAHAP_05_KANDIDAT_SELOKASI/LAPORAN.md`. Hasil terkini: `05_HASIL/TESTING_131_20261117T111615166527Z/AUDIT_KANDIDAT_SELOKASI/TINJAU_PERUBAHAN.html`. Hitungan pengembangan bukan akurasi model baru; keterbatasan tahap sebelumnya tetap berlaku.

### Tahap sebelumnya

Versi susun **0.4.2**, peta aturan **0.1.2**. Pemasangan tanda pada Ina mendatar, pengelompokan baris miring, tanda vokal/ng/pangolat yang berurutan, suku kata tertutup dan normalisasi penyambung Ya/Wa telah diperbaiki. Bacaan harfiah tetap tersimpan. **63 uji perangkat lunak lulus** di Windows dan WSL; empat JSON validation lama tetap konsisten. Model, prediksi sumber, dataset, evaluasi dan UI tidak diubah.

Pada 80 citra tanpa kesalahan matching GT, kesesuaian dengan PDF tanpa spasi/kapital berubah dari 53 menjadi 74. Empat sisanya berbeda antara GT dan acuan; dua terkait buku/buhu. Pada diagnosis terpisah kelas+bbox GT seluruh 131 citra, 119 sesuai acuan, enam berbeda antara GT/acuan dan enam terkait ejaan h/k. Diagnosis GT bukan prediksi model. Testing sudah ditinjau dan dipakai dalam pengembangan; hitungan ini **bukan akurasi pengujian independen**. Spasi otomatis, keputusan ejaan h/k, pengesahan ahli dan integrasi UI belum selesai.

Mulai dari `TAHAP_04_PANDUAN.md`. Laporan: `05_HASIL/TAHAP_04_ATURAN_DAN_GEOMETRI/LAPORAN.md`. Hasil akhir tahap: `05_HASIL/TESTING_131_20261117T110305251381Z/AUDIT_BACAAN_DAN_GT/TINJAU_BACAAN.html`. Hasil antara yang lebih awal dipertahankan sebagai jejak pengembangan.

## Riwayat tahap sebelumnya

Batch testing tersimpan sudah dijalankan atas permintaan pengguna: 131 citra diproses, 0 error; 68 DRAFT_READING dan 63 NEEDS_REVIEW. Status bukan akurasi teks. Galeri/CSV/JSON/laporan pada `05_HASIL/TESTING_131_20261117T102933620328Z`. Aturan tidak diubah setelah melihat batch; tidak ada inferensi baru. Belum ada acuan Latin terverifikasi per citra, sehingga akurasi teks/CER belum dihitung.

Versi terbaru 0.3.0: pemilihan kandidat dilakukan sebelum pemasangan tanda; suku kata tertutup dan Ha berpangolat sebagai k akhir diterapkan. 51 uji perangkat lunak lulus; regresi JSON validation tersimpan menghasilkan aek, jabu, huta sesuai acuan, sedangkan amang tetap ama akibat tanda ng di bawah threshold model. Tidak ada inferensi baru atau perubahan UI. Baca `05_HASIL/TAHAP_03_SUKU_TERTUTUP/LAPORAN.md`. Catatan versi lebih lama di bawah bersifat historis.

Versi terbaru 0.2.2: atas instruksi pengguna, teks utama memilih kandidat Ina ber-confidence tertinggi dalam kelompok overlap; seluruh alternatif tetap disimpan. Skor seri tetap ambigu, tanda Anak yang belum berpasangan tetap perlu diperiksa. 45 uji perangkat lunak lulus di WSL. Lihat `05_HASIL/TAHAP_02_CONFIDENCE/CATATAN.md`. Versi terdahulu dan hasil citra pengguna tidak ditimpa.

Pembaruan 0.2.1: tampilan alternatif Ina bertumpuk menjadi satu kelompok tanpa suppression atau pemilihan kelas. Semua ID/skor dipertahankan. Total 42 uji perangkat lunak lulus; lihat `05_HASIL/TAHAP_02_ALTERNATIF/CATATAN.md`. Pemeriksaan citra aktual tetap dijalankan pengguna.

Status 17 November 2026: mesin aturan dan pengurutan/pemasangan berbasis bbox awal sudah dibuat atas arahan pengguna. Total 37 uji perangkat lunak lulus pada WSL. Pemasangan belum dikalibrasi atau diverifikasi pada citra nyata; belum ada integrasi UI. Tidak ada training, inferensi baru, perubahan dataset atau perubahan Word pada tahap ini.

Arahan bimbingan yang dilaporkan pengguna: gunakan kandidat Eksperimen 2; pertahankan model; kembangkan manfaat aplikasi melalui hasil teks Latin. Penjelasan sampel pengujian pada draf dikerjakan kemudian. RUN400 tetap disimpan sebagai arsip.

Mulai membaca `TAHAP_02_PANDUAN.md` untuk pengurutan dan pasangan tanda, lalu `TAHAP_01_PANDUAN.md` untuk mesin aturan. `RENCANA_PENGEMBANGAN.md`, `01_ATURAN/KEPUTUSAN_ATURAN.md` dan `04_PENGUJIAN/RENCANA_UJI.md` menyimpan rancangan keseluruhan; bagian yang menyatakan belum implementasi menggambarkan saat rancangan awal disusun.

Referensi tambahan dari pengguna, 17 November 2026: 25 halaman SuratBatak.id telah dibaca materi teksnya. Catatan cakupan, keterbatasan interaksi dan perbedaan yang perlu diperiksa tersedia pada `00_ACUAN/CATATAN_SURATBATAK_ID.md`; metadata akses pada `SURATBATAK_HALAMAN_DIBACA.json`. Belum ada perubahan aplikasi.

| Folder | Isi saat ini | Peran berikutnya |
|---|---|---|
| 00_ACUAN | Manifest sumber, ekstraksi teks PDF, pratinjau halaman, daftar 449 item dan 39 teks unik | Penelusuran acuan; tidak menjadi masukan jawaban untuk mesin transliterasi |
| 01_ATURAN | Peta 25 kelas dan catatan keputusan | Penyelesaian kebijakan ortografi |
| 02_MODUL_TRANSLITERASI | Mesin aturan dan usulan pengurutan/pasangan bbox | Verifikasi geometri pada citra dan penanganan batas kata |
| 03_INTEGRASI_WEB | Rancangan integrasi | Salinan UI pengembangan yang mengakses model Eksperimen 2 |
| 04_PENGUJIAN | Rencana dan 37 uji perangkat lunak | Acuan teks terverifikasi dan regresi prediksi |
| 05_HASIL | Bukti uji tahap 1-2, bukan evaluasi citra | Bukti pengembangan berikutnya, terpisah dari eksperimen asli |

Tidak ada berkas Python kosong. Status tiap tahap dibedakan pada panduan. Checkpoint tidak disalin; integrasi direncanakan menunjuk ke checkpoint asli yang diverifikasi hash-nya.
