@echo off
REM ==============================================================================
REM Shortcut Launcher: Chrome Remote Debugging (Windows Root)
REM ==============================================================================

cd /d "%~dp0"

if exist "launchers\start_chrome_windows.bat" (
    call "launchers\start_chrome_windows.bat" %*
    exit /b %ERRORLEVEL%
)
