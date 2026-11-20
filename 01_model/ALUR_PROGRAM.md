# Alur menjalankan program Aksarabataktoba

Root Windows: D:/SKRIPSIJONATHAN/PROGRAM/02_AKSARABATAKTOBA_TERBARU.

Klik MULAI_DISINI.cmd untuk memilih tahap. Peluncur memakai environment Ubuntu WSL penelitian yang sudah tersedia. Pilihan training pada menu akan memulai pelatihan baru; gunakan hanya ketika memang ingin mengulang eksperimen. Untuk rekaman uji program, cukup status, pratinjau, kode, aplikasi dan bukti.

| Pilihan | Tahap | Perilaku |
|---|---|---|
| 1 | Status | Menampilkan kedua run selesai 30 epoch dan checkpoint terpilih. |
| 2 | Audit | Memeriksa data, konfigurasi dan bobot pralatih; tidak melatih. |
| 3 | Praproses | Menyimpan satu contoh citra latih: asli, resize, nilai normalisasi dan augmentasi. |
| 4 | Training R50 baru | 30 epoch, responden repeat 3, folder keluaran baru. |
| 5 | Training R101 baru | 30 epoch, responden repeat 3, folder keluaran baru. |
| 6 | Evaluasi R50 tersimpan | Menghitung ulang hasil model yang sudah selesai ke folder baru. |
| 7 | Evaluasi R101 tersimpan | Menghitung ulang hasil model yang sudah selesai ke folder baru. |
| 8 | Aplikasi | Menjalankan UI R50 pada localhost:8502. Terminal tetap terbuka. |
| 9 | Bukti | Membuka halaman anotasi/prediksi serta evaluasi untuk presentasi. |
| 10 | Kode | Membuka folder dan enam berkas presentasi di VS Code jika perintah code tersedia. |
| 0 | Keluar | Menutup menu. |

## Alur singkat untuk rekaman

1. Pilih 1 untuk menunjukkan kedua model selesai 30 epoch.
2. Pilih 3 bila ingin menampilkan proses resize/normalisasi/augmentasi. Folder hasil dicetak pada terminal, di hasil_tahapan/praproses.
3. Pilih 10 untuk membuka enam berkas kode. Perhitungan normalisasi dan resize UI menggunakan model/kode, yang identik dengan salinan eksperimen.
4. Pilih 9 untuk membuka bukti validasi.
5. Pilih 8 untuk menjalankan aplikasi. Buka http://localhost:8502. Setelah aplikasi berjalan, terminal ini perlu dibiarkan terbuka. Gunakan jendela terminal lain bila ingin menjalankan menu/perintah tambahan.
6. Pilih citra asli dari D:/SKRIPSIJONATHAN/SEMHAS/UJI_PROGRAM_EKSPERIMEN_2/01_CITRA_UNTUK_DIUNGGAH. Pedoman ucapan berada pada NASKAH_LENGKAP_TAMPILAN_DAN_UCAPAN.md dalam folder uji program tersebut.

Rekaman tidak memerlukan training atau evaluasi ulang seluruh data. Hasil penelitian sudah tersedia dan tetap dipertahankan.

## Perintah Ubuntu, satu per satu

```bash
cd /mnt/d/SKRIPSIJONATHAN/PROGRAM/02_AKSARABATAKTOBA_TERBARU
```

Panggil menu:

```bash
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py
```

Atau pilih tahap langsung:

```bash
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py status
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py audit
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py praproses
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py kode
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py bukti
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py ui
```

Setiap baris adalah perintah terpisah. UI memanggil environment .venv-web secara otomatis. Hasil pratinjau bukan dataset training baru. Normalisasi numerik disimpan dalam NPZ; PNG yang dikembalikan ke RGB wajar tampak sama dengan hasil resize. Saat training, resize/augmentasi dan normalisasi tetap diterapkan dinamis oleh kode asli, bukan membaca gambar pratinjau ini.

## Mengulang eksperimen dari awal, jika diperlukan

Jalankan R50 dahulu, tunggu selesai, kemudian R101 pada GPU yang sama:

```bash
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py train-r50
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py train-r101
```

Kedua perintah membuat folder bertanggal baru di hasil_tahapan/train_R50 atau train_R101. Durasi selalu 30 epoch, jadwal LR tetap epoch 20 dan 27, faktor pengulangan responden 3. Folder keluaran ditampilkan sebelum training. Catat lokasi itu untuk resume/evaluasi. Model UI tidak diganti otomatis oleh hasil eksperimen baru.

Menguji perintah tanpa training:

```bash
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py train-r50 --dry-run
```

Jika run baru terputus, gunakan --resume dan --output yang menunjuk folder run yang sama persis. Contoh berikut mengganti NILAI_FOLDER_RUN dengan lokasi nyata yang dicetak terminal:

```bash
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py train-r50 --resume --output NILAI_FOLDER_RUN
```

Tanpa --output, --resume memeriksa run penelitian yang sudah ada di eksperimen/hasil_train_R50 atau R101. Karena keduanya selesai 30 epoch, peluncur menginformasikan selesai tanpa memulai training tambahan. Pemeriksaan kontrak saja dapat memakai --resume --check-resume.

Peluncur lama sudah diperbarui dan dapat dipakai:

```bash
bash eksperimen/jalankan_R50.sh --dry-run
bash eksperimen/jalankan_R101.sh --dry-run
```

Hapus --dry-run hanya ketika ingin memulai training baru. Keduanya meneruskan ke alur.py, bukan trainer mentah. Jangan menjalankan train_Aksarabataktoba.py secara langsung karena sumbernya mempertahankan jalur historis untuk integritas kontrak; peluncur paket mengarahkan dependensi lokal yang benar.

## Evaluasi

Model penelitian yang sudah selesai:

```bash
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py eval-r50
/home/jonatomic/skripsi-batak-toba/.venv/bin/python -B alur.py eval-r101
```

Folder hasil baru dibuat di hasil_tahapan/evaluasi_R50 atau evaluasi_R101. Untuk mengevaluasi training baru, tambahkan --run NILAI_FOLDER_RUN. Evaluator memilih model_best dari run tersebut dan memeriksa kesesuaiannya terhadap riwayat validasi. Tidak menimpa hasil penelitian tersimpan.

## Yang tetap dipertahankan

30 adalah durasi pelatihan. 25 tetap jumlah kelas. Checkpoint terbaik R101 tetap epoch 25 dan R50 epoch 28; keduanya berasal dari training yang selesai epoch 30. Angka hasil, dataset, checkpoint, riwayat, kode trainer/evaluator/transformasi dan Word tidak diubah. Mode smoke pada trainer merupakan diagnosis singkat, bukan pelatihan penelitian; menu ini tidak menyediakan mode tersebut.

Dokumentasi README_ASLI_EKSPERIMEN.md merupakan catatan historis. Ikuti panduan ini untuk eksekusi saat ini. Cadangan peluncur sebelumnya berada di ARSIP_PENELITIAN/SEBELUM_PELUNCUR_30_EPOCH_15NOV2026.
