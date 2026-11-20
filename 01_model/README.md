# Kandidat Aksarabataktoba terbaru

Mulai dari **MULAI_DISINI.cmd**. Menu menyediakan status, audit, pratinjau praproses, training R50/R101 30 epoch, evaluasi, aplikasi, bukti dan kode.

Baca ALUR_PROGRAM.md untuk perintah lengkap. Untuk rekaman uji program, pilih status/praproses/kode/bukti/aplikasi; training ulang tidak diperlukan. Antarmuka tetap dapat dijalankan melalui JALANKAN_UI.cmd pada http://localhost:8502.

Training R50 dan R101 penelitian sudah selesai 30 epoch. Model terbaik dipilih dari validasi: R50 epoch 28, R101 epoch 25. UI menggunakan R50 epoch 28. Training baru menyimpan hasil pada folder baru dan tidak mengganti checkpoint UI otomatis.

Pilih citra asli, tekan Proses citra, lalu periksa mask, bounding box, label dan tabel. PNG, CSV dan JSON disimpan otomatis ke hasil_demo. UI tidak menghitung akurasi tanpa ground truth dan tidak melatih model.

eksperimen/ menyimpan dataset, sumber training/evaluasi dan hasil; model/kode diperlukan UI; pendukung/ berisi dependensi aktif. draf/ berisi salinan Word kandidat. Bobot dan hasil penelitian dipertahankan. Runtime memakai environment WSL penelitian yang sudah tersedia; terminal aplikasi tetap terbuka selama digunakan.
