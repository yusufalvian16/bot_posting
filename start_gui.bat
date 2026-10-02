@echo off
REM ==============================================================================
REM Shortcut Launcher: Auto-Posting Bot GUI (Windows Root)
REM ==============================================================================

cd /d "%~dp0"

if exist "launchers\start_gui_windows.bat" (
    call "launchers\start_gui_windows.bat" %*
    exit /b %ERRORLEVEL%
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" app_gui.py %*
) else if exist ".venv\Scripts\python.exe" (
    start "" ".venv\Scripts\python.exe" app_gui.py %*
) else (
    start "" python app_gui.py %*
)
