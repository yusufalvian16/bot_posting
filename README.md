# Multi-Platform Mass Auto-Posting & Keyword Intelligence Bot

Ekosistem bot otomasi modular berbasis **Python** dan **Google Chrome Asli (via CDP / Remote Debugging)** untuk riset kata kunci Google Suggest (Alphabet Soup A-Z + 0-9) dan posting massal otomatis ke:
1. **Carousell Marketplace** (`carousell.com`)
2. **YouTube Studio** (Video reguler & Shorts)
3. **Issuu** (Publikasi Dokumen PDF)

Sistem ini didesain **modular dan mandiri** (setiap platform memiliki script dan file CSV terpisah), aman dari deteksi bot (`navigator.webdriver` bernilai `false`), dan 100% kompatibel di **Windows** dan **Linux**.

---

## 📁 Struktur Direktori

```
Bot-Posting/
├── assets/                          # Folder aset media Anda
│   ├── images/                      # Foto produk Carousell (.jpg / .png)
│   ├── videos/                      # Video YouTube (.mp4)
│   └── docs/                        # Dokumen PDF Issuu (.pdf)
├── data/                            # Folder data CSV
│   ├── keywords_raw/                # Hasil scraping kata kunci Google Suggest
│   ├── carousell_posts.csv          # Antrian posting Carousell
│   ├── youtube_posts.csv            # Antrian upload YouTube
│   └── issuu_posts.csv              # Antrian publikasi Issuu
├── launchers/                       # Script pembuka Chrome Remote Debugging
│   ├── start_chrome_windows.bat     # Untuk pengguna Windows
│   └── start_chrome_linux.sh        # Untuk pengguna Linux
├── modules/                         # Core engine otomasi
│   ├── browser_manager.py           # Konektor CDP ke Google Chrome
│   ├── human_emulator.py            # Simulasi ketikan & jeda manusiawi
│   ├── csv_handler.py               # Pengelola status & atomic CSV write
│   └── logger.py                    # Terminal output berwarna (Rich)
├── config.py                        # Pengaturan delay, port, timeout
├── scraper_keyword.py               # Script Mandiri: Riset kata kunci Google (Alphabet Soup)
├── builder_template.py              # Utility: Konversi kata kunci ke CSV platform
├── poster_carousell.py              # Script Mandiri: Bot posting Carousell
├── poster_youtube.py                # Script Mandiri: Bot upload YouTube
├── poster_issuu.py                  # Script Mandiri: Bot publish Issuu
├── requirements.txt                 # Dependensi Python
└── PRD.md                           # Product Requirement Document lengkap
```

---

## 🚀 Panduan Langkah Demi Langkah

### Langkah 1: Instalasi Dependensi Python

Pastikan Python 3.10+ sudah terpasang. Di terminal / Command Prompt:

```bash
# Buat virtual environment (opsional tapi sangat disarankan)
python -m venv .venv

# Aktifkan virtual environment:
# Di Windows:
.venv\Scripts\activate
# Di Linux:
source .venv/bin/activate

# Install dependensi
pip install -r requirements.txt
```

---

### Langkah 2: Persiapan Profil Google Chrome (Sekali Saja)

Untuk menghindari ban dan mempertahankan sesi login:

#### A. Pengguna Windows:
1. Klik ganda file `launchers\start_chrome_windows.bat`
2. Jendela Google Chrome baru akan terbuka dengan profil khusus di `%USERPROFILE%\ChromeBotProfile`.
3. Di jendela browser tersebut, silakan buka dan login ke:
   - [Carousell](https://www.carousell.com)
   - [YouTube Studio](https://studio.youtube.com)
   - [Issuu](https://issuu.com)
4. Sesi login akan tersimpan otomatis dan permanen. **Biarkan jendela Chrome ini tetap terbuka saat bot dijalankan.**

#### B. Pengguna Linux:
1. Jalankan di terminal:
   ```bash
   ./launchers/start_chrome_linux.sh
   ```
2. Login ke akun-akun target di browser yang terbuka.

---

### Langkah 3: Riset Kata Kunci Otomatis (Alphabet Soup)

Gunakan `scraper_keyword.py` untuk mengambil kata kunci pencarian populer langsung dari dropdown Google Suggest:

```bash
# Cara Interaktif (akan meminta input kata kunci):
python scraper_keyword.py

# Atau dengan parameter langsung:
python scraper_keyword.py --seed "pupuk sawit"
```

- Script akan secara instan mengueri:
  - Kata kunci dasar: `pupuk sawit`
  - Huruf A-Z: `pupuk sawit a`, `pupuk sawit b`, ... `pupuk sawit z`
  - Angka 0-9: `pupuk sawit 0`, ... `pupuk sawit 9`
  - Modifier komersial: `jual pupuk sawit`, `harga pupuk sawit`, dsb.
- Hasil tersimpan di: `data/keywords_raw/keywords_pupuk_sawit.csv` (berisi ratusan kata kunci unik).

---

### Langkah 4: Filter Kata Kunci & Generate CSV Platform

1. Buka file `data/keywords_raw/keywords_[seed].csv` di **Microsoft Excel**, **Google Sheets**, atau **LibreOffice Calc**.
2. Hapus baris kata kunci yang tidak relevan sesuai kebutuhan Anda, lalu simpan file CSV.
3. Jalankan `builder_template.py` untuk membuat template CSV siap posting:

```bash
# Contoh untuk Carousell:
python builder_template.py -p carousell -i data/keywords_raw/keywords_pupuk_sawit.csv -t "Jual {keyword_title} Murah Berkualitas" -m "assets/images/pupuk.jpg" --price "150000"

# Contoh untuk YouTube:
python builder_template.py -p youtube -i data/keywords_raw/keywords_pupuk_sawit.csv -t "Rahasia {keyword_title} Hasil Melimpah" -m "assets/videos/tips_sawit.mp4"

# Contoh untuk Issuu:
python builder_template.py -p issuu -i data/keywords_raw/keywords_pupuk_sawit.csv -t "Katalog Resmi {keyword_title}" -m "assets/docs/katalog.pdf"
```

> Anda juga bisa langsung membuka file CSV hasil (`data/carousell_posts.csv`, dll.) dan mengedit baris per baris secara manual (misal mengganti foto atau harga per produk).

---

### Langkah 5: Menjalankan Bot Posting Otomatis

Setiap bot berjalan secara independen. Pastikan Chrome dari Langkah 2 masih terbuka.

#### 1. Menjalankan Bot Carousell:
```bash
python poster_carousell.py

# Opsi uji coba tanpa menekan tombol 'List Now':
python poster_carousell.py --dry-run

# Opsi membatasi jumlah posting (contoh 5 postingan dulu):
python poster_carousell.py --max-posts 5
```

#### 2. Menjalankan Bot YouTube:
```bash
python poster_youtube.py

# Opsi uji coba:
python poster_youtube.py --dry-run
```

#### 3. Menjalankan Bot Issuu:
```bash
python poster_issuu.py

# Opsi uji coba:
python poster_issuu.py --dry-run
```

---

## 🛡️ Fitur Anti-Ban & Keamanan

1. **CDP Attach Engine**:
   Bot tidak membuka browser tiruan dengan webdriver. Bot menempel langsung ke browser Google Chrome resmi Anda, sehingga `window.navigator.webdriver` bernilai `false` dan bebas dari deteksi Cloudflare / bot detector.
2. **Pengetikan Manusiawi (Human Typing Cadence)**:
   Setiap huruf diketik dengan variasi jeda acak (40ms - 120ms per karakter) disertai micro-pause pada spasi dan tanda baca.
3. **Jeda Antar Postingan (Inter-Post Delays)**:
   Secara default, bot menunggu 60 s/d 180 detik antar postingan. Anda dapat mengubah rentang ini di `config.py`:
   ```python
   MIN_POST_DELAY = 90   # Detik minimal
   MAX_POST_DELAY = 240  # Detik maksimal
   ```
4. **Idempotency & Melanjutkan Otomatis (Resume Capability)**:
   Setiap baris di CSV memiliki kolom `status`. Jika bot berhenti karena koneksi internet putus atau Anda tekan `Ctrl+C`, saat bot dijalankan kembali, baris yang sudah `success` akan otomatis dilewati dan bot melanjutkan baris yang berstatus `pending` atau `failed`.

---

## ❓ Troubleshooting & Tips

- **Error: "Gagal terhubung ke Google Chrome!"**
  - Pastikan Anda sudah menjalankan launcher Chrome (`start_chrome_windows.bat` di Windows atau `start_chrome_linux.sh` di Linux) sebelum menjalankan script Python.
  - Periksa apakah port 9222 aktif dengan membuka `http://localhost:9222/json` di browser.
- **Gambar / Video Tidak Ditemukan**:
  - Pastikan path file di CSV sudah benar. Anda bisa menggunakan path relatif (`assets/images/produk.jpg`) atau path absolut (`C:\Users\Nama\Foto\produk.jpg`).
  - Untuk Carousell, multi-gambar dipisahkan menggunakan titik koma (`;`), contoh: `assets/img1.jpg;assets/img2.jpg`.
- **YouTube Verifikasi Tambahan**:
  - Jika YouTube meminta verifikasi SMS/notifikasi HP saat pertama kali upload, selesaikan verifikasi tersebut langsung di jendela Chrome yang terbuka. Sesi tersebut akan tersimpan untuk upload berikutnya.
