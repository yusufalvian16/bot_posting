@echo off
REM ==============================================================================
REM Registrasi Menu Konteks "Open With" Windows untuk File CSV
REM Menambahkan opsi klik kanan: "Buka dengan Bot Auto-Posting"
REM Berjalan pada HKCU (Tidak memerlukan hak Administrator)
REM ==============================================================================

cd /d "%~dp0"
set "APP_BAT=%~dp0start_gui_windows.bat"

echo ==============================================================================
echo   REGISTRASI "OPEN WITH" BOT AUTO-POSTING UNTUK WINDOWS
echo ==============================================================================
echo Menghubungkan file .CSV dengan: %APP_BAT%
echo.

REM 1. Tambahkan ke SystemFileAssociations .csv
reg add "HKCU\Software\Classes\SystemFileAssociations\.csv\shell\BotPosting" /ve /d "Buka dengan Bot Auto-Posting" /f >nul 2>&1
reg add "HKCU\Software\Classes\SystemFileAssociations\.csv\shell\BotPosting" /v "Icon" /d "imageres.dll,-68" /f >nul 2>&1
reg add "HKCU\Software\Classes\SystemFileAssociations\.csv\shell\BotPosting\command" /ve /d "\"%APP_BAT%\" \"%%1\"" /f >nul 2>&1

REM 2. Tambahkan ke OpenWithList
reg add "HKCU\Software\Classes\Applications\start_gui_windows.bat\shell\open\command" /ve /d "\"%APP_BAT%\" \"%%1\"" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.csv\OpenWithList" /v "a" /d "start_gui_windows.bat" /f >nul 2>&1

echo [BERHASIL] Menu klik kanan berhasil dipasang!
echo Sekarang Anda dapat mengklik kanan pada file .CSV apa saja dan memilih:
echo   --^> "Buka dengan Bot Auto-Posting"
echo.
pause
