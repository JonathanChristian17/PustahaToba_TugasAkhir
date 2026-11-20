# DESIGN.md: Web App Transliterasi Aksara Batak Toba

Dial: ENERGY 3 / RHYTHM 3 / MOTION 3

## 1. Sistem 3 Warna Terpadu (Atas, Tengah, & Bawah Selaras)
- **Primary (`#6B141A` / `#4A0D12`: Marun Ulos Batak):** Menyatukan Navbar aktif, tombol aksi utama, pita showcase penelitian, tirai pembuka, serta Footer agar seluruh halaman memiliki satu identitas marun adat yang selaras.
- **Secondary (`#FAF6EE` & `#FFFFFF` di terang; `#140708` & `#210D10` di gelap):** Permukaan kertas *pustaha* hangat bertekstur titik halus untuk kenyamanan baca teks.
- **Accent (`#C87A19` / `#F2B45A` / `#F8E5C2`: Emas Tenun Ulos):** Digunakan pada sorotan kuas `BrushHighlight`, jahitan tirai Ulos, gelombang interaktif, cincin metrik, dan sorotan karakter.

## 2. Pembaruan Logo, Splash Screen, Kartu, & 3 Halaman Berbeda
- **Logo Terpadu (`BrandMark.jsx`):** Ikon lipatan naskah *Pustaha Laklak* terbuka yang membingkai belah ketupat tenun *Ulos* dan garis pembacaan pusat (tanpa huruf *Ina* tunggal).
- **Splash Screen Tanpa Kotak & Tanpa Tombol (`SplashScreen.jsx`):** Panggung tirai *Ulos* penuh tanpa kotak tengah maupun tombol; menampilkan `BrandMark` tergambar bertahap, teks `PUSTAHA TOBA` muncul per huruf (`Letters` Zip 1), segel teks melingkar berputar (`RingText` Zip 1), serta lapisan 25 aksara bergerak (`AksaraDriftBackdrop`), lalu tirai kiri-kanan membelah terbuka.
- **Penyelarasan Kartu & Halaman:**
  - `Baca Aksara`: Kedua panel sejajar sama tinggi (`align-items: stretch`) dengan header satu baris rapi dan `BrushHighlight` menutupi seluruh tinggi frasa *Kalimat Latin*.
  - `Mode Penelitian`: Band Hero marun gelap dengan 3 cincin metrik SVG animasi (`useTweenNumber`) + panel inspeksi masker/tabel seimbang.
  - `Panduan`: Band Hero marun/kertas dengan **Checklist Persiapan Foto Interaktif** (adaptasi `Busywork` Zip 2) + **Akordeon FAQ** (adaptasi `Agenda/FAQ` Zip 3) + `PipelineHub`.

## 3. Kontras Terverifikasi (WCAG AA via contrast-check.py)
- `#1C1414` pada `#FAF6EE` = **16.80:1** (PASS)
- `#534443` pada `#FFFFFF` = **9.23:1** (PASS)
- `#FAF6EE` pada `#6B141A` = **11.20:1** (PASS)
- `#FAF6EE` pada `#4A0D12` = **14.35:1** (PASS)
- `#F2B45A` pada `#4A0D12` = **8.44:1** (PASS)
- `#1C1414` pada `#F8E5C2` (sorotan `BrushHighlight`) = **14.64:1** (PASS)
