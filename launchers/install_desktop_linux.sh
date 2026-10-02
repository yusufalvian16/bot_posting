#!/usr/bin/env bash
# ==============================================================================
# Installer Desktop Shortcut & File Association untuk Linux
# ==============================================================================

set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

DESKTOP_FILE="$APPS_DIR/bot-posting.desktop"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Bot Auto-Posting & CSV Manager
Comment=Multi-Platform Mass Auto-Posting & CSV Progress Controller
Exec=$DIR/launchers/start_gui_linux.sh %f
Icon=utilities-terminal
Terminal=false
Categories=Office;Development;Network;
MimeType=text/csv;application/csv;text/x-csv;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"
chmod +x "$DIR/launchers/start_gui_linux.sh"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi

echo "[BERHASIL] Desktop entry dipasang di: $DESKTOP_FILE"
echo "Sekarang file CSV dapat diklik kanan -> Open With -> Bot Auto-Posting & CSV Manager"
