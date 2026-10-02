@echo off
REM ==============================================================================
REM Script untuk Membuka Google Chrome dengan Remote Debugging di Windows
REM Digunakan oleh Bot Auto-Posting agar aman dari deteksi bot & mempertahankan sesi login.
REM ==============================================================================

setlocal enabledelayedexpansion

set PROFILE_DIR=%USERPROFILE%\ChromeBotProfile
set PORT=9222

echo ==========================================================
echo   Menyiapkan Profil Google Chrome (Remote Debugging: %PORT%)
echo   Direktori Profil: %PROFILE_DIR%
echo ==========================================================

REM Cek apakah port 9222 sudah listening
netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Chrome Remote Debugging di port %PORT% sudah aktif dan siap digunakan.
    pause
    exit /b 0
)

REM Cari executable Google Chrome, Brave, atau Edge di lokasi standar Windows
set CHROME_BIN=

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    set "CHROME_BIN=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    set "CHROME_BIN=C:\Program Files\Microsoft\Edge\Application\msedge.exe"
) else if exist "%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe" (
    set "CHROME_BIN=%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"
)

if "%CHROME_BIN%"=="" (
    echo [ERROR] Google Chrome atau browser Chromium tidak ditemukan di folder standar!
    echo Pastikan Google Chrome atau Microsoft Edge sudah terinstall di komputer Anda.
    pause
    exit /b 1
)

echo [INFO] Menemukan browser: "%CHROME_BIN%"
echo [INFO] Membuka browser... Silakan login ke YouTube, Carousell, dan Issuu di jendela ini.
echo.

start "" "%CHROME_BIN%" --remote-debugging-port=%PORT% --user-data-dir="%PROFILE_DIR%" --no-first-run --no-default-browser-check --disable-background-timer-throttling --disable-renderer-backgrounding --disable-backgrounding-occluded-windows %*

echo [SUCCESS] Chrome telah diluncurkan!
echo JANGAN TUTUP jendela Chrome ini selama bot posting sedang berjalan.
echo Anda sekarang bisa menjalankan aplikasi Desktop GUI Bot.
pause
