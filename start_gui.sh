#!/usr/bin/env bash
# ==============================================================================
# Shortcut Launcher: Auto-Posting Bot GUI (Linux Root)
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ -f "launchers/start_gui_linux.sh" ]; then
    exec bash "launchers/start_gui_linux.sh" "$@"
fi

if [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    PYTHON_BIN="python"
fi

exec "$PYTHON_BIN" app_gui.py "$@"
