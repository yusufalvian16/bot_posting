# Original User Request

## 2026-10-02T05:10:33Z

Membangun aplikasi Desktop GUI (Cross-Platform Windows & Linux menggunakan CustomTkinter) untuk ekosistem Bot Auto-Posting & Keyword Intelligence, serta menjalankan pengujian 2-3 postingan nyata dengan video sampel 15-30 detik pada Carousell, YouTube Studio, dan Issuu.

Working directory: /home/yusuf/Projects/Bot-Posting
Integrity mode: development

## Requirements

### R1. Desktop GUI Application (CustomTkinter)
Aplikasi desktop modern dengan Dark/Light theme yang bekerja identik di Windows dan Linux:
- **Tab 1 - Keyword Scraper**: Input kata kunci induk, tombol "Scrape Google Suggest", tabel visual hasil Alphabet Soup (A-Z, 0-9), filter kata kunci, dan ekspor CSV.
- **Tab 2 - Template Builder**: Konfigurasi pola judul (`Jual {keyword_title}`), deskripsi, pemilih file media (gambar/video/PDF), dan tombol generate CSV platform.
- **Tab 3 - Auto-Posting Runner & Monitor**: Pemilihan platform (Carousell, YouTube, Issuu), pengaturan jeda acak (min/max detik), opsi Dry-Run, tombol Start/Stop, live progress bar, dan terminal log interaktif.
- **Tab 4 - Browser Profile Controller**: Status indikator koneksi Chrome port 9222 (Hijau=Online, Merah=Offline) dan tombol peluncur profil Chrome otomatis.

### R2. Threaded Non-Blocking Execution
- Semua proses scraping dan browser automation dijalankan di background thread (worker thread) terpisah agar antarmuka GUI tetap responsif, tidak mengalami "Not Responding" / freeze saat bot sedang mengetik atau menunggu jeda waktu.

### R3. Multi-Post Testing (2-3 Sampel per Platform)
- Menghasilkan aset video sampel berdurasi 15-30 detik (`assets/videos/sample_sawit_15s.mp4`) dengan audio/visual yang valid.
- Menjalankan pengujian 2-3 postingan nyata untuk memverifikasi reliabilitas selektor, upload media, penanganan jeda waktu, dan pencatatan status sukses/gagal di CSV.

## Acceptance Criteria

### GUI Usability & Cross-Platform
- [ ] GUI dapat diluncurkan dengan `python app_gui.py` atau shortcut `.bat` (Windows) dan `.sh` (Linux) tanpa error library.
- [ ] Pengguna dapat mengoperasikan seluruh alur kerja (Scrape -> Filter -> Buat Template -> Mulai Posting) langsung dari GUI tanpa command line.
- [ ] Live log pada GUI menampilkan detail baris yang sedang diproses beserta countdown jeda aman anti-spam.

### Automation & Testing
- [ ] File video sampel 15-30 detik terbuat dan lolos validasi codec MP4.
- [ ] Pengujian 2-3 listing Carousell terisi lengkap (foto, judul, harga, kategori Gardening, kondisi, deskripsi) dan terverifikasi.
- [ ] Pengujian upload YouTube Studio berhasil memproses video dengan opsi penonton dan visibilitas.
- [ ] Pengujian Issuu berhasil mengunggah dokumen PDF dan mempublikasikan.
- [ ] Seluruh status postingan tercatat atomik di masing-masing file CSV (`status`, `post_url`, `posted_at`).
