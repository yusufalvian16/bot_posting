@echo off
REM ==============================================================================
REM Hapus Registrasi Menu Konteks "Open With" Windows untuk File CSV
REM ==============================================================================

echo Menghapus menu konteks "Buka dengan Bot Auto-Posting"...
reg delete "HKCU\Software\Classes\SystemFileAssociations\.csv\shell\BotPosting" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Applications\start_gui_windows.bat" /f >nul 2>&1

echo [BERHASIL] Menu konteks berhasil dihapus dari sistem.
pause
