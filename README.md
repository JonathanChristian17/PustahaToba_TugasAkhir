# Pustaha Toba — Pengenalan & Transliterasi Aksara Batak Toba

Repositori dokumentasi kode penelitian skripsi oleh **Jonathan C. Amadeo Sembiring** (`231402111`) untuk deteksi, segmentasi instansi, dan transliterasi Aksara Batak Toba ke huruf Latin.

## Struktur Repositori

- `01_model/` — Skrip pelatihan, evaluasi, konfigurasi, serta backend inferensi **Mask R-CNN ResNet-50-FPN** (25 kelas: 19 *Ina ni Surat* + 6 *Anak ni Surat*, Epoch 28 / 30).
- `02_transliteration/` — Modul transliterasi berbasis geometri mask & kaidah ortografi Batak Toba (`v0.5.1-composite-ina-and-mask-sign-conflicts`), peta aturan 25 kelas, kosakata eksternal (`kosakata_toba_v2.json`), skrip pengujian (`132` unit test Python + uji penyajian JS), dan laporan audit (`TAHAP_15_AUDIT_TRANSLITERASI_051`).
- `03_web_app/` — Aplikasi web interaktif React + Vite, server API lokal (`server/api_server.py`), dan contoh citra uji ringkas (`demo_citra/`).

## Bobot Model (Checkpoint)

Berkas bobot model `model_best.pth` (`168,5 MB` untuk ResNet-50-FPN Epoch 28) melebihi batas ukuran berkas `100 MB` di GitHub, sehingga disediakan melalui halaman **GitHub Releases** pada repositori ini.

Setelah mengunduh, letakkan berkas bobot sesuai konfigurasi `01_model/model/identitas.json` sebelum menjalankan inferensi backend.

## Cara Menjalankan Lokal

### 1. Backend API (Python / Detectron2)
```bash
cd 03_web_app
python jalankan_api.py
# Aktif di http://127.0.0.1:8503 (env PUSTAHA_API_HOST & PUSTAHA_API_PORT tersedia)
```

### 2. Frontend Web (React + Vite)
```bash
cd 03_web_app
npm install
npm run dev
# Buka http://localhost:5173
```

Jika frontend di-deploy terpisah (mis. Vercel), atur environment variable `VITE_API_BASE` mengarah ke URL backend publik.

### 3. Pengujian Modul Transliterasi
```bash
cd 02_transliteration
python -m unittest discover -s 04_PENGUJIAN -p "uji_*.py"
```
