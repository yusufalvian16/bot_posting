#!/usr/bin/env bash
# ==============================================================================
# Shortcut Launcher: Chrome Remote Debugging (Linux Root)
# ==============================================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

if [ -f "launchers/start_chrome_linux.sh" ]; then
    exec bash "launchers/start_chrome_linux.sh" "$@"
fi
