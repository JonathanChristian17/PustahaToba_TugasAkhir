# Rancangan aturan pembacaan

Pembaruan 17 November 2026, aturan 0.1.2 / geometri 0.4.2: bacaan literal dan ejaan penyambung Ya/Wa kini dipisahkan. Ya setelah i/e dan Wa setelah u yang diikuti vokal dapat dinormalisasi dengan jejak aturan; Ha onset tetap h, Ha penutup berpangolat tetap k. Tidak ada kamus atau jawaban PDF di dalam mesin. Enam citra diagnostik GT masih berbeda karena ejaan buku/buhu; enam lainnya karena perbedaan GT/acuan. Baca `05_HASIL/TAHAP_04_ATURAN_DAN_GEOMETRI/LAPORAN.md`. Catatan berikut merupakan riwayat rancangan dan keputusan terdahulu, bukan status aktif.

Pembaruan 17 November 2026, aturan 0.1.1: Ha sebagai penutup berpangolat kini dibaca k berdasarkan Pelajaran 5 aksara-batak.com; Ha awal suku kata tetap h. Aturan h/k yang pada rancangan awal di bawah masih ditandai terbuka sudah diterapkan dalam lingkup ini. Ya/Wa dan batas kata belum dinormalisasi. Laporan implementasi dan batas verifikasi: `05_HASIL/TAHAP_03_SUKU_TERTUTUP/LAPORAN.md`.

Status: aturan awal untuk ditinjau; belum merupakan implementasi yang diuji atau pengesahan ahli.

## Peta kelas yang dipertahankan

Sumber ID dan label adalah `PROGRAM/02_AKSARABATAKTOBA_TERBARU/model/class_map.json`.

| ID | Kelas | Nilai dasar / fungsi awal |
|---|---|---|
| 0 | ina_a | a, vokal mandiri |
| 1 | ina_ha | ha |
| 2 | ina_ma | ma |
| 3 | ina_na | na |
| 4 | ina_ra | ra |
| 5 | ina_ta | ta |
| 6 | ina_ba | ba |
| 7 | ina_pa | pa |
| 8 | ina_wa | wa |
| 9 | ina_ga | ga |
| 10 | ina_ja | ja |
| 11 | ina_da | da |
| 12 | ina_nga | nga |
| 13 | ina_la | la |
| 14 | ina_sa | sa |
| 15 | ina_ya | ya |
| 16 | ina_nya | nya |
| 17 | ina_i | i, vokal mandiri |
| 18 | ina_u | u, vokal mandiri |
| 19 | anak_hatadingan | vokal e |
| 20 | anak_hauluan | vokal i |
| 21 | anak_sihora | vokal o |
| 22 | anak_haborotan | vokal u |
| 23 | anak_haminsaran | ng penutup suku kata |
| 24 | anak_pangolat | mematikan vokal inheren a pada konsonan |

Nilai tanda diverifikasi terhadap glyph pada tabel V6 halaman PDF 33-34 dan fungsi pada sumber bahasa/Unicode. Penamaan lokal pada referensi dapat berbeda. Tabel tidak mengganti label kelas atau menyamakan Ina Nga dengan tanda penutup ng.

## Aturan dasar yang akan diuji

- Ina berkonsonan umumnya membawa vokal a. Ina A, I, U diperlakukan sebagai vokal mandiri; jangan menghapus karakter terakhir label secara seragam untuk semua kelas.
- Tanda vokal mengubah vokal pada unit yang sesuai. Haminsaran menambahkan ng akhir dan dapat menyertai tanda vokal.
- Pangolat mematikan vokal konsonan. Pada suku kata tertutup, susunan visual dapat memindahkan tanda vokal ke dekat konsonan akhir. Perlu analisis kelompok, bukan sekadar mengubah Ina yang paling dekat.
- Anak yang tidak memiliki pasangan, kombinasi tidak sah, dua calon Ina yang sama kuat, atau dua kelas untuk lokasi yang sama diberi status ambigu. Jangan menebak supaya sesuai daftar kata.

## Contoh dari materi V6

| Kelompok | Contoh sumber | Hal yang perlu diuji |
|---|---|---|
| Vokal dasar | saba | dua Ina tanpa Anak |
| Vokal u | jabu, huta | pasangan Haborotan dan Ina, termasuk tanda yang menyentuh |
| Vokal i/o | piso, roha | tanda setelah Ina dan urutan baca |
| Akhir ng | amang, inang | Haminsaran sebagai ng, berbeda dari Ina Nga |
| Susunan tertutup | ulos, dongan, porlak | pangolat, konsonan akhir, dan perpindahan tampilan tanda vokal |
| Varian ejaan | sia, dua, aek na tio | Ya/Wa penyambung; hasil harfiah dapat berbeda dari ejaan Latin pada PDF |
| Ejaan akhir | aek, porlak | kebijakan h/k akhir perlu rujukan dan keputusan eksplisit sebelum target disahkan |
| Frasa | huta Toba, jabu ni inang | jarak kata, urutan kiri ke kanan dan kapitalisasi |
| Latihan | nya, nyi | latihan suku kata; tidak diklaim sebagai kata/frasa alami |

Contoh di atas merupakan target pembahasan dari PDF. Belum ada klaim aplikasi telah menghasilkan kata-kata tersebut dengan benar.

## Sumber aturan

- Unicode 16, bab 17, bagian 17.6 Batak: https://unicode.org/versions/Unicode16.0.0/core-spec/chapter-17/
- Anak ni Surat: https://aksara-batak.com/lessons/toba-6/
- Ya dan Wa: https://aksara-batak.com/lessons/pelajaran-6/
- Konteks Transtoba: https://siboro.org/transtoba/informasi.html

Keputusan normalisasi harus memiliki sumber dan nomor versi. Penggunaan Latin PDF sebagai target tidak dengan sendirinya memvalidasi aturan yang menghasilkannya.
