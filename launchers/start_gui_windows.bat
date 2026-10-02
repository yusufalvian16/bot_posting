@echo off
REM ==============================================================================
REM Launcher Aplikasi Desktop GUI Auto-Posting Bot untuk Windows
REM ==============================================================================

cd /d "%~dp0.."

set PYTHON_BIN=

REM Prefer pythonw.exe inside .venv for clean detached GUI (no ghost cmd window)
if exist ".venv\Scripts\pythonw.exe" (
    set "PYTHON_BIN=.venv\Scripts\pythonw.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_BIN=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\pythonw.exe" (
    set "PYTHON_BIN=venv\Scripts\pythonw.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_BIN=venv\Scripts\python.exe"
) else (
    where pythonw >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_BIN=pythonw"
    ) else (
        where python >nul 2>&1
        if %ERRORLEVEL% equ 0 (
            set "PYTHON_BIN=python"
        )
    )
)

if "%PYTHON_BIN%"=="" (
    echo [ERROR] Python tidak ditemukan di sistem Windows Anda!
    echo Silakan install Python 3.10+ atau buat .venv: python -m venv .venv
    pause
    exit /b 1
)

start "" "%PYTHON_BIN%" app_gui.py %*
exit /b 0
