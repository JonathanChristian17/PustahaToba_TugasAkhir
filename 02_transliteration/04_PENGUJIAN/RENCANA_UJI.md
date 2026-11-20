# Rencana pengujian pengembangan

Status: rencana; tidak ada hasil pengujian transliterasi pada tahap ini.

## 1. Acuan teks

Peta citra aktual ke responden, subset, nomor stimulus, halaman V6 dan teks Latin setelah pemeriksaan isi gambar. Kolom minimum yang direncanakan untuk `acuan_teks.csv`: image_id, nama_file, sha256_citra, subset, responden, nomor_stimulus, halaman_pdf, jenis_stimulus, teks_referensi, versi_ejaan, status_pemeriksaan dan catatan.

449 item/39 teks unik dari V6 adalah daftar rencana stimulus, bukan jumlah citra uji. Gunakan data aktual Eksperimen 2 saat menyusun populasi pengujian. P13/P14 tetap testing. Jangan menambah salinan atau memindahkan subset untuk menguji fitur ini.

## 2. Pengujian aturan terpisah

Periksa urutan baca, masing-masing tanda vokal, Haminsaran bersama vokal, pangolat, suku kata tertutup, Ya/Wa, tanda terlepas dan kelas tumpang tindih. Fixture buatan boleh digunakan untuk uji perangkat lunak dengan label jelas `fixture_unit`; tidak boleh ditampilkan sebagai hasil penelitian pada citra asli.

Pengujian dengan anotasi GT bertujuan mengisolasi kebenaran aturan. Pengujian hasil akhir menggunakan prediksi model dan dilaporkan terpisah; keberhasilan pada GT tidak dianggap keberhasilan model.

## 3. Pengujian hasil prediksi tersimpan

Gunakan kelas, confidence, bbox dan RLE mask dari hasil yang sudah ada terlebih dahulu. Backend UI dan evaluator memiliki format keluaran yang perlu dipetakan tanpa mengubah nilainya. Aturan menerima prediksi; teks Latin referensi hanya tersedia bagi evaluator, bukan mesin pembaca.

Parameter pemasangan/spasi ditetapkan pada sampel pengembangan/validasi. Bekukan versi sebelum testing. Karena riwayat eksplorasi testing telah ada, klaim independensi pengujian tetap mengikuti keterbatasan penelitian sebelumnya.

## 4. Regresi integrasi

- Checkpoint dan hash tetap sesuai paket 02.
- Untuk citra yang sama, seluruh prediksi asli, termasuk confidence, bbox dan mask, tidak berubah akibat penambahan modul.
- Mode mask/bbox dan penyuntingan teks tidak memengaruhi hasil inferensi.
- Nomor asli pada tabel dan overlay tetap konsisten; urutan baca disimpan terpisah.
- Ketika masukan baru diunggah, hasil teks dan koreksi citra sebelumnya dibersihkan agar tidak tercampur.
- Semua prediksi bertumpuk masih dapat diperiksa, meskipun hasil pembacaan ditandai ambigu.

## 5. Evaluasi teks baru yang diusulkan

CA instansi, AP dan IoU yang sudah dilaporkan tetap merupakan hasil model. Untuk fitur baru, usulkan ketepatan teks persis dan Character Error Rate (CER), dihitung terhadap referensi teks terverifikasi. Penambahan metrik ini memerlukan penjelasan teori/prosedur pada penulisan berikutnya; belum ada nilainya.

CER = (substitusi + penghapusan + penyisipan) / jumlah karakter teks referensi. Nyatakan normalisasi huruf besar/kecil, spasi dan variasi ejaan sebelum menghitung. Laporkan hasil otomatis; hasil setelah suntingan pengguna dipisahkan. CER dapat melebihi 100% ketika penyisipan sangat banyak.

Kesalahan dikelompokkan menurut pengenalan karakter, hubungan diakritik, urutan baca, pemisahan kata, dan kebijakan ejaan. Ini membantu menentukan sumber kegagalan tanpa menganggap seluruh kesalahan transliterasi berasal dari model segmentasi.
