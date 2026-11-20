# Rencana pengembangan aplikasi pembacaan aksara Batak Toba

## Keputusan dan ruang lingkup

Rancangan ini menindaklanjuti arahan bimbingan yang disampaikan pengguna pada 17 November 2026. Paket dasar adalah `PROGRAM/02_AKSARABATAKTOBA_TERBARU`. Model UI yang tersedia merupakan Mask R-CNN ResNet-50-FPN, checkpoint terbaik epoch 28 dari pelatihan 30 epoch. Identitas ini dipertahankan sesuai `model/identitas.json`, dengan SHA-256 `5d964b6e0f56f14901351933272f0ffb2ee6d6b085213fadd3f8406ffa4221c2`.

Pengembangan menambahkan pengolahan setelah inferensi. Arsitektur, bobot, praproses inferensi, 25 kelas, threshold confidence 0,50, NMS dan hasil evaluasi lama tetap. Word belum direvisi. Publikasi aplikasi ke internet adalah pekerjaan tersendiri; aplikasi lokal yang dapat digunakan melalui browser belum otomatis menjadi layanan publik.

## Temuan dari acuan

### Paket kata/frasa V6

PDF terdiri dari 36 halaman. Halaman 1-2 merencanakan 449 item untuk P01-P15, terdiri dari 419 item kata/frasa dan 30 latihan suku kata. Ekstraksi tabel halaman 3-32 menghasilkan 449 baris, dengan 39 teks Latin unik, sesuai rekap dokumen. Daftar tersimpan dalam `00_ACUAN/ITEM_RESPONDEN_V6.csv` dan `DAFTAR_TEKS_UNIK_V6.csv`.

Angka tersebut merupakan rencana stimulus. Angka itu tidak menggantikan jumlah dataset aktual, jumlah penulis aktual, atau 131 citra testing Eksperimen 2. Paket berisi kata, frasa, dan latihan; tidak seluruhnya kalimat lengkap. Latihan `nya` dan `nyi` dipisahkan dari kosakata/frasa alami. Halaman 35 menyebut revisi belum merupakan validasi ahli bahasa/aksara.

PDF menjadi acuan penelusuran nomor stimulus, ejaan target dan cakupan kombinasi. Penautan ke citra aktual masih perlu diperiksa dari nama file, metadata dan tulisan pada citra. Isi tulisan aktual harus sesuai sebelum Latin pada PDF diterima sebagai ground truth transliterasi. Jangan menautkan nomor secara otomatis hanya karena nama file mirip.

Teks aksara hasil ekstraksi PDF mengandung karakter NUL pada beberapa susunan. Karena itu glyph hasil ekstraksi tidak diperlakukan sebagai urutan Unicode kanonik. Pratinjau halaman asli sudah diperiksa untuk konteks visual; penyusunan referensi aksara memerlukan pemeriksaan sumber atau glyph aslinya.

### Skripsi Bobby Adithya Manik, 201402034

PDF terdiri dari 74 halaman. Bab 3 bagian 3.2, khususnya halaman cetak 31-34 / PDF 44-47, menjelaskan alur memilih citra dan menampilkan hasil Latin. Bab 4 bagian 4.3.2-4.3.3 / PDF 53-55 menunjukkan penerapannya. Ini menjadi pedoman agar hasil pembacaan tampak sebagai fungsi utama aplikasi.

Cakupan model yang dilaporkan senior adalah 19 Ina ni Surat, sebagaimana bagian 3.1.6 / PDF 41 dan kesimpulan / PDF 69. Dalam bagian relevan yang diperiksa, tidak ditemukan spesifikasi algoritma rinci untuk menghubungkan enam kelas Anak ni Surat pada penelitian kita. Karena itu skripsi senior digunakan sebagai acuan alur aplikasi, bukan bukti bahwa pemasangan diakritik kita sudah terpecahkan. Platform Android dan YOLOv8 senior juga tidak perlu diadopsi untuk aplikasi Streamlit/Mask R-CNN yang sudah ada.

### Sumber aturan tambahan

- [Unicode Standard 16, bagian 17.6 Batak](https://unicode.org/versions/Unicode16.0.0/core-spec/chapter-17/): struktur aksara, vokal inheren, pangolat dan perbedaan urutan logis dengan susunan visual.
- [Pelajaran Anak ni Surat](https://aksara-batak.com/lessons/toba-6/): fungsi tanda vokal dan Haminsaran. Nama lokal tanda pada sumber dapat berbeda; ID dan nama kelas dataset tidak diganti.
- [Pelajaran Ya dan Wa](https://aksara-batak.com/lessons/pelajaran-6/): variasi penyambung vokal seperti dua/duwa dan tio/tiyo.
- [Informasi Transtoba](https://siboro.org/transtoba/informasi.html): konteks varian aksara dan batas representasi. Program tersebut berjalan dari Latin ke aksara; pembalikan ke Latin tidak dianggap selalu unik.

## Alur yang diusulkan

```text
Citra unggahan
    -> inferensi Mask R-CNN yang sudah ada
    -> salinan hasil instansi: ID, kelas, confidence, bbox dan mask
    -> pengelompokan baris dan urutan Ina dari kiri ke kanan
    -> pencarian hubungan Anak-Ina dan susunan suku kata
    -> aturan pembacaan vokal, ng dan pangolat
    -> teks Latin + penanda bagian ambigu + jejak sumber instansi
    -> tampilan hasil, salin/unduh, pemeriksaan mask dan koreksi pengguna
```

Daftar keluaran model sekarang diurutkan berdasarkan confidence (`list_order` pada backend), sehingga bukan urutan baca. Nomor instansi asli tetap tersedia pada tabel dan overlay. Urutan baca dibuat dalam atribut baru; penomoran model tidak ditimpa.

Pemasangan diakritik menggunakan hubungan geometri yang sesuai jenis tanda, ukuran karakter, kedekatan mask/bbox dan baris. Tanda Haborotan dapat bersentuhan dengan Ina. Satu Ina juga dapat menerima tanda vokal bersama Haminsaran. Perlu kandidat lebih luas daripada satu pasangan terdekat.

Urutan visual tidak selalu sama dengan urutan bunyi pada suku kata tertutup. Kasus pangolat memerlukan analisis kelompok suku kata; tanda vokal yang tampak dekat konsonan akhir dapat memengaruhi konsonan sebelumnya. Ini menjadi kasus wajib sebelum modul dinyatakan bekerja.

Prediksi bertumpuk dengan kelas berbeda tetap disimpan. Pada tahap pembacaan, kandidat yang tidak dapat dipilih secara meyakinkan menghasilkan alternatif/penanda ambigu. Tidak ada suppression lintas kelas dan tidak ada pengubahan prediksi agar sesuai kata yang diharapkan.

## Susunan kode yang direncanakan

Nama berikut merupakan rencana, belum merupakan berkas yang sudah diimplementasikan.

```text
03_PENGEMBANGAN_TRANSLITERASI/
  00_ACUAN/                      sumber, daftar stimulus dan jejak asal
  01_ATURAN/
    peta_aksara.json              25 kelas, nilai dasar dan fungsi tanda
    aturan_ortografi.json         kombinasi dan kebijakan ejaan berversi
  02_MODUL_TRANSLITERASI/
    transliterasi.py              urutan baca, pasangan, suku kata, hasil Latin
  03_INTEGRASI_WEB/
    app.py                       salinan UI pengembangan
    penghubung_model.py           pemanggilan backend paket 02 yang terverifikasi
  04_PENGUJIAN/
    acuan_teks.csv                pemetaan citra aktual ke teks referensi
    uji_aturan.py                 pemeriksaan aturan terpisah dari model
    uji_integrasi.py              regresi prediksi dan hasil teks
  05_HASIL/                      hasil dan bukti baru setelah eksekusi diizinkan
```

Fungsi satu modul transliterasi dipisahkan secara logis; jumlah berkas dapat bertambah hanya bila kompleksitas membutuhkannya. Dependensi UI/visual asli digunakan kembali secara terkontrol. Penghubung model harus memakai import yang mengikat ke paket 02 secara eksplisit agar modul generik `backend`/`visual` tidak tertukar. Tidak mengedit salinan kode model yang dilindungi hash. Perubahan pada penghubung, UI dan transliterasi dicatat terpisah.

## Tahapan pelaksanaan

| Tahap | Pekerjaan | Bukti penyelesaian |
|---|---|---|
| 1 | Tetapkan tabel kelas dan kebijakan ejaan | Aturan dengan sumber, contoh dan bagian ambigu yang jelas |
| 2 | Susun pengurutan dan hubungan tanda dari hasil tersimpan | Urutan baca serta pasangan dapat ditelusuri kembali ke ID prediksi |
| 3 | Terapkan transliterasi dan kasus suku kata tertutup | Kasus aturan sederhana dan kompleks lolos pemeriksaan |
| 4 | Integrasikan pada salinan UI | Hasil Latin tampil, dapat disalin, rincian mask tetap tersedia |
| 5 | Uji dengan citra dan referensi yang sudah ditetapkan | Ketepatan teks dan kegagalan dilaporkan terpisah dari CA model |

Parameter geometri ditetapkan dengan data pengembangan/validasi. Sampel testing tetap untuk pemeriksaan hasil akhir, bukan untuk berulang kali mengatur parameter sampai cocok. Penggunaan testing secara eksploratif yang telah terjadi tidak dihapus dari riwayat.

## Bentuk UI

Pertahankan unggah, tombol proses, citra asli, overlay mask/bbox dan tabel prediksi. Tambahkan area utama `Hasil transliterasi Latin`, tombol salin dan unduh TXT. Tampilkan bagian yang perlu diperiksa bila ada tanda tidak berpasangan atau prediksi ganda. Rincian teknis berada di bagian yang dapat dibuka pengguna.

Koreksi manual dapat disediakan dengan dua keluaran terpisah: hasil otomatis dan versi suntingan pengguna. Tindakan tersebut tidak mengubah label, skor atau mask model. Hasil suntingan tidak dihitung sebagai keberhasilan otomatis. Confidence per karakter tidak dijadikan persentase akurasi kalimat.

## Hal yang perlu disepakati sebelum implementasi

1. Mulai dari satu baris kata/frasa dengan jarak tulisan yang jelas; dukungan banyak baris ditambahkan setelah aturan satu baris teruji.
2. Hasil utama awal mengikuti pembacaan aksara yang dapat ditelusuri. Kebijakan normalisasi Ya/Wa dan ejaan akhir seperti `aek` ditetapkan eksplisit, karena hubungan glyph ke ejaan Latin tidak selalu satu-ke-satu.
3. Spasi diusulkan dari celah visual jika memang tampak. Naskah tanpa jarak kata menghasilkan teks bersambung atau batas kata yang ditandai perlu diperiksa. Kamus stimulus tidak dipakai untuk menebak jawaban pengujian.
4. Paket V6 menjadi acuan materi, tidak menjadi daftar jawaban tersembunyi dalam aplikasi. Kesalahan model tetap terlihat dalam hasil pembacaan.
5. Tahap berikutnya adalah mengimplementasikan aturan dan modul pada folder ini setelah pengguna meninjau rancangan. Belum ada penerapan ke aplikasi aktif.
