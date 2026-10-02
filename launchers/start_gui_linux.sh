#!/usr/bin/env bash
# ==============================================================================
# Launcher Aplikasi Desktop GUI Auto-Posting Bot untuk Linux
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

# Deteksi virtual environment Python
PYTHON_BIN=""
if [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -x "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "[ERROR] Python tidak ditemukan di sistem Anda!"
    echo "Silakan install Python 3.10+ atau buat virtualenv: python -m venv .venv"
    exit 1
fi

echo "[INFO] Menjalankan Bot Auto-Posting GUI..."
echo "[INFO] Python binary: $PYTHON_BIN"
echo "[INFO] Direktori kerja: $DIR"

"$PYTHON_BIN" app_gui.py "$@" &

echo "[SUCCESS] GUI telah diluncurkan di background (PID: $!)."
