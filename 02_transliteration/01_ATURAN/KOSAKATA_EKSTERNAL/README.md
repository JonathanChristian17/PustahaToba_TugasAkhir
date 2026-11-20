# Kosakata pengembangan Batak Toba

Pembaruan v2: `kosakata_toba_v2.json` berisi 6.157 token. Dari 6.241 token v1, 84 token yang seluruh kemunculannya berhuruf kapital penuh dikeluarkan. Pemeriksaan dilakukan pada token sebelum diubah menjadi huruf kecil, setelah tanda baca tepi dibuang; setidaknya satu kemunculan harus tidak memenuhi `str.isupper()`. Bukti token dan dokumen asal tersedia pada `05_HASIL/TAHAP_08_SPASI_KONSERVATIF/TOKEN_KAPITAL_SAJA.json`. Contoh `ob` hanya ditemukan sebagai `OB`; ini alasan penyaringan kapital, bukan kesimpulan bahwa kata tersebut mustahil dalam bahasa Toba. Nama diri atau singkatan lain masih mungkin lolos, dan kata sah berhuruf kapital dapat ikut terbuang. V1 tetap disimpan untuk reproduksi.

Sumber: **Feliks Victor Parningotan Samosir, Korpus Bahasa Batak Toba**, Universitas Pelita Harapan. Repositori: https://github.com/FeliksMakarios/batak-toba-korpus

Revisi yang dipertahankan: `23cfc304920a7b0ba41a8142724a8d7e968fdcae`. Lisensi rilis data **CC BY 4.0**; salinan LICENSE dan CITATION.cff disertakan. Dokumen pernyataan data menjelaskan batas hak sumber asli dan sifat awal korpus. Tanggal akses: 17 November 2026.

`kosakata_toba.json` berisi **6.241 token unik** dari seluruh **104 dokumen** `data/btb_multigenre.csv`, hanya kolom `text_bt`. Kolom terjemahan Indonesia tidak dipakai. Token dipisah dengan whitespace, tanda baca tepi dibuang, huruf dikecilkan, lalu hanya token utuh yang cocok `[a-z]+` diterima. Token dengan tanda hubung/apostrof internal atau karakter lain tidak dipecah menjadi kata baru; token tersebut dikeluarkan. Hasil dideduplikasi dan diurutkan. Tidak ada tambahan atau penyaringan kata berdasarkan PDF, daftar stimulus, nama citra atau jawaban testing.

Ini **kosakata turunan korpus, bukan kamus baku**. Nama diri, kata serapan, token pendek, salah ketik atau variasi ejaan mungkin ikut terbawa; kata yang sah juga mungkin belum tercakup. Metode pembagian tunggal tetap memerlukan tinjauan bahasa. Token/frekuensi tidak dipakai untuk memilih tebakan paling cocok dengan penelitian.

Sumber asli disalin dengan prefiks `data__`/`docs__`; sumber tidak dieksekusi sebagai kode. Hash CSV, aturan ekstraksi, jumlah dokumen, lisensi dan revisi tersedia pada JSON. Keluaran aplikasi tidak perlu mengirim teks ke layanan daring.

Contoh penggunaan dari Ubuntu, pada folder PROGRAM/03_PENGEMBANGAN_TRANSLITERASI:

```bash
python 02_MODUL_TRANSLITERASI/susun_prediksi.py \
  --predictions 05_HASIL/KOREKSI_P10_N23_V1/inferensi_koreksi/predictions.json \
  --lexicon 01_ATURAN/KOSAKATA_EKSTERNAL/kosakata_toba_v2.json \
  --output 05_HASIL/P10_N23_USULAN_SPASI_BARU.json
```

Pilih nama keluaran baru jika berkas sudah ada. Tanpa `--lexicon`, keluaran lama tetap tanpa usulan spasi. Perintah tersebut membaca prediksi yang sudah tersedia; tidak menjalankan model.
