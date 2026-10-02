# 🪟 Panduan Lengkap Instalasi & Pemakaian di Windows

Panduan resmi langkah demi langkah untuk memasang dan menjalankan **Bot Auto-Posting & CSV Manager** pada sistem operasi **Windows 10 / Windows 11**.

---

## 📋 1. Persyaratan Sistem (Prerequisites)

Sebelum memulai, pastikan komputer Windows Anda memiliki:
1. **Python 3.10 atau versi yang lebih baru**:
   - Unduh dari: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - ⚠️ **PENTING SAAT MENGINSTALL PYTHON**:
     Pada layar pertama installer Python, **WAJIB CENTANG**:
     `[X] Add Python to PATH` (atau `Add python.exe to PATH`).
2. **Google Chrome**:
   - Pastikan Google Chrome resmi sudah terpasang di lokasi standar (`C:\Program Files\Google\Chrome\Application\chrome.exe` atau `%LocalAppData%\Google\Chrome\Application\chrome.exe`).

---

## ⚡ 2. Instalasi Otomatis (1-Click Installer)

Kami telah menyediakan script installer otomatis yang akan menyiapkan seluruh lingkungan aplikasi tanpa perlu mengetik perintah manual:

1. Buka folder proyek `Bot-Posting`.
2. **Klik dua kali file:**
   ```
   setup_windows.bat
   ```
3. Installer akan secara otomatis melakukan:
   - ✅ Memeriksa ketersediaan Python di PATH Windows.
   - ✅ Membuat lingkungan virtual terisolasi (`.venv`).
   - ✅ Menginstall seluruh pustaka Python (`playwright`, `customtkinter`, `rich`, `requests`, `darkdetect`, dll).
   - ✅ Mengunduh driver browser Playwright Chromium.
   - ✅ Mendaftarkan menu klik kanan **"Buka dengan Bot Auto-Posting"** pada semua file `.csv` di Windows Explorer.
4. Setelah instalasi selesai, tekan sembarang tombol untuk langsung membuka aplikasi.

---

## 🚀 3. Cara Menjalankan Aplikasi di Windows

Anda memiliki 3 cara mudah untuk menjalankan aplikasi:

### Cara 1: Menggunakan Shortcut Utama (Rekomendasi)
- Cukup **klik dua kali** file:
  ```
  start_gui.bat
  ```
  Aplikasi Desktop GUI modern CustomTkinter akan langsung terbuka tanpa jendela terminal hitam yang mengganggu.

### Cara 2: Klik Kanan pada File CSV ("Open With")
- Cari file antrian `.csv` Anda (misalnya di folder `data\youtube_posts.csv`).
- **Klik kanan file `.csv`** -> Pilih:
  ```
  "Buka dengan Bot Auto-Posting"
  ```
- Aplikasi akan terbuka seketika dan langsung memuat seluruh data ke tab **📊 CSV Manager & Progres**, lengkap dengan statistik progres, tabel interaktif, dan tombol pelanjutan posting.

### Cara 3: Drag & Drop
- Tarik (drag) file `.csv` apa saja lalu lepaskan (drop) tepat di atas file `start_gui.bat`.

---

## 🔐 4. Langkah Awal: Login Akun Sekali Saja (Profil Chrome Terisolasi)

Bot menggunakan browser Chrome asli Anda melalui protokol Remote Debugging port 9222 sehingga Anda terhindar dari deteksi bot atau pemblokiran login Google:

1. Buka aplikasi GUI (`start_gui.bat`).
2. Di pojok kanan atas, klik tombol **"Buka Profil Chrome"**.
3. Jendela Google Chrome khusus bot akan terbuka.
4. Buka situs yang ingin Anda gunakan dan login akun Anda:
   - **YouTube Studio**: [https://studio.youtube.com](https://studio.youtube.com)
   - **Carousell Marketplace**: [https://www.carousell.co.id](https://www.carousell.co.id)
   - **Issuu Publisher**: [https://issuu.com](https://issuu.com)
5. Sesi login, cookies, dan akun Anda akan **tersimpan secara permanen** di profil lokal (`%USERPROFILE%\ChromeBotProfile`). Anda tidak perlu login ulang di kemudian hari!

---

## 🔄 5. Alur Kerja Harian: Melanjutkan Progres (Resume Session)

Sistem dirancang agar Anda bisa memposting bertahap kapan saja tanpa menduplikasi data:

1. **Buka file CSV antrian Anda** (misal `data\youtube_posts.csv`).
2. Tab **📊 CSV Manager & Progres** langsung menampilkan:
   - Berapa video yang sudah sukses (misal: 3 video bertanda hijau ✅).
   - Berapa video yang masih antri / pending (misal: 454 video).
   - Persentase penyelesaian dan informasi: *"Siap melanjutkan dari baris ke-4"*.
3. **Ingin memposting 3 video hari ini?**
   - Klik tombol hijau besar: **`▶ LANJUTKAN POSTING DARI FILE INI`**.
   - Di tab Bot Auto-Posting, atur **Maksimal Postingan = 3**.
   - Klik **Mulai Auto-Posting**.
   - Bot akan memposting baris ke-4, ke-5, dan ke-6.
4. **Besok saat dibuka lagi**:
   - Progres otomatis terupdate menjadi 6/457 selesai, dan siap lanjut dari baris ke-7!

---

## ✏️ 6. Menyunting Data Langsung dari Aplikasi
- **Edit Baris**: Klik ganda baris mana saja di tabel untuk membuka form editor (ubah judul, ganti file video/gambar, ubah status, atau visibilitas Publik/Unlisted).
- **Reset Gagal**: Jika ada baris yang gagal karena internet putus, klik tombol **"🔄 Reset Gagal"** untuk mengembalikan statusnya ke `pending`.
- **Buka URL**: Klik tombol **"🌐 Buka URL"** untuk membuka langsung link video YouTube yang sudah berhasil terbit di browser default Anda.

---

## 🛠️ 7. Penyelesaian Masalah (Troubleshooting)

| Masalah | Solusi |
|---|---|
| `'python' is not recognized as an internal or external command` | Install ulang Python dari python.org dan pastikan mencentang kotak **"Add Python to PATH"**. Restart komputer setelahnya. |
| Chrome status di aplikasi menunjukkan `Offline` | Klik tombol **"Buka Profil Chrome"** di aplikasi, atau pastikan tidak ada proses Chrome lain yang mengunci port 9222. |
| Menu klik kanan "Open With" tidak muncul | Jalankan file `launchers\register_open_with_windows.bat` secara manual. |
| Ingin menghapus menu klik kanan | Jalankan file `launchers\unregister_open_with_windows.bat`. |
