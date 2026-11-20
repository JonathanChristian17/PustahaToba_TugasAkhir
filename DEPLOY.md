# Panduan Deploy Pustaha Toba (Backend HF Spaces + Frontend Vercel)

Repositori ini sudah dikonfigurasi untuk dipisahkan antara **Backend API (Mask R-CNN + Modul Transliterasi 0.5.1)** di Hugging Face Spaces (Docker gratis 16 GB RAM, mode CPU otomatis `PUSTAHA_DEVICE=cpu`) dan **Frontend Web (React + Vite)** di Vercel.

---

## Langkah 1 — Deploy Backend ke Hugging Face Spaces

1. Buka [https://huggingface.co/new-space](https://huggingface.co/new-space).
2. Isi konfigurasi:
   - **Space name**: `pustaha-toba-api`
   - **SDK**: pilih **Docker** (template **Blank**)
   - **Space hardware**: **CPU basic (2 vCPU · 16 GB RAM · FREE)**
3. Clone Space kosong tersebut atau hubungkan remote Hugging Face, lalu push isi repositori ini (termasuk `Dockerfile` dan `model_best.pth` via Git LFS):
   ```bash
   git remote add hf https://huggingface.co/spaces/<username-hf>/pustaha-toba-api
   git push hf main
   ```
   *(Atau unggah berkas `Dockerfile`, `01_model/`, `02_transliteration/`, `03_web_app/` beserta `01_model/eksperimen/hasil_train_R50/model_best.pth` lewat tab **Files** di Hugging Face Space.)*
4. Tunggu proses build Docker selesai (~5–15 menit), lalu pastikan status Space **Running** dan buka:
   `https://<username-hf>-pustaha-toba-api.hf.space/api/health`

---

## Langkah 2 — Deploy Frontend ke Vercel

1. Buka [https://vercel.com/new](https://vercel.com/new) dan **Import** repositori GitHub `JonathanChristian17/PustahaToba_TugasAkhir`.
2. Atur konfigurasi proyek:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `03_web_app`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Tambahkan **Environment Variable**:
   - Name: `VITE_API_BASE`
   - Value: `https://<username-hf>-pustaha-toba-api.hf.space` *(tanpa garis miring di akhir)*
4. Klik **Deploy** (~1–2 menit). Setelah selesai, buka URL Vercel dan uji unggah citra dari `03_web_app/demo_citra/`.
