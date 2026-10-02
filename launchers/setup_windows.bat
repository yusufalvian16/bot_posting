@echo off
setlocal enabledelayedexpansion
REM ==============================================================================
REM  AUTOMATED WINDOWS INSTALLER - BOT AUTO-POSTING & KEYWORD INTELLIGENCE
REM ==============================================================================

title Bot Auto-Posting - Installer Windows
cd /d "%~dp0"

echo ==============================================================================
echo       SELAMAT DATANG DI INSTALLER BOT AUTO-POSTING ^& CSV MANAGER
echo ==============================================================================
echo.

REM 1. Cek Python di Sistem
echo [1/5] Memeriksa instalasi Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Python tidak ditemukan di sistem Windows Anda!
    echo Silakan unduh dan install Python 3.10+ dari:
    echo   https://www.python.org/downloads/
    echo.
    echo PENTING: Saat instalasi Python di Windows, PASTIKAN Anda mencentang:
    echo   [X] "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set "PY_VER=%%i"
echo   --^> Terdeteksi: %PY_VER%
echo.

REM 2. Buat Virtual Environment (.venv)
echo [2/5] Menyiapkan Virtual Environment (.venv)...
if not exist ".venv\Scripts\activate.bat" (
    echo   --^> Membuat .venv baru...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Gagal membuat virtual environment!
        pause
        exit /b 1
    )
    echo   --^> Virtual environment berhasil dibuat.
) else (
    echo   --^> Virtual environment (.venv) sudah ada.
)
echo.

REM 3. Install Dependensi (pip install -r requirements.txt)
echo [3/5] Menginstall library Python yang dibutuhkan...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Gagal menginstall library dari requirements.txt!
    pause
    exit /b 1
)
echo   --^> Seluruh library Python berhasil diinstall.
echo.

REM 4. Install Playwright Chromium Driver
echo [4/5] Menginisialisasi komponen Playwright Chromium...
playwright install chromium
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Playwright install chromium selesai dengan catatan.
)
echo.

REM 5. Registrasi Menu Konteks "Open With" untuk File CSV
echo [5/5] Mendaftarkan menu klik kanan "Open With" file CSV di Windows...
if exist "launchers\register_open_with_windows.bat" (
    call "launchers\register_open_with_windows.bat"
) else (
    echo   --^> launchers\register_open_with_windows.bat tidak ditemukan, dilewati.
)

echo.
echo ==============================================================================
echo                      INSTALASI WINDOWS SELESAI!
echo ==============================================================================
echo.
echo Cara Menjalankan Aplikasi:
echo   1. Klik dua kali file: start_gui.bat
echo   2. Atau klik kanan file .csv mana saja --^> "Buka dengan Bot Auto-Posting"
echo.
echo Catatan untuk Google Chrome:
echo   Pastikan Google Chrome resmi sudah terpasang.
echo   Sebelum memposting, Anda dapat mengklik tombol "Buka Profil Chrome" di aplikasi
echo   untuk login akun YouTube Studio / Carousell / Issuu Anda sekali saja.
echo.
echo Tekan sembarang tombol untuk langsung membuka aplikasi sekarang...
pause >nul

start "" start_gui.bat
exit /b 0
