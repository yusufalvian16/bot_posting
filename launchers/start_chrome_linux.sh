#!/usr/bin/env bash
# ==============================================================================
# Script untuk Membuka Google Chrome / Chromium dengan Remote Debugging di Linux
# Digunakan oleh Bot Auto-Posting agar aman dari deteksi bot & mempertahankan sesi login.
# ==============================================================================

PROFILE_DIR="$HOME/.config/chrome_bot_profile"
PORT="9222"

echo "=========================================================="
echo "  Menyiapkan Profil Browser (Remote Debugging Port: $PORT)"
echo "  Direktori Profil: $PROFILE_DIR"
echo "=========================================================="

mkdir -p "$PROFILE_DIR"

# Cek apakah Chrome CDP di port 9222 sudah berjalan
if curl -s "http://localhost:$PORT/json/version" >/dev/null 2>&1; then
    echo "[INFO] Chrome Remote Debugging di port $PORT sudah aktif dan siap digunakan."
    exit 0
fi

# Cari executable Chrome / Chromium / Brave / Edge
BROWSER_BIN=""
for candidate in google-chrome-stable google-chrome chromium-browser chromium brave-browser microsoft-edge-stable microsoft-edge; do
    if command -v "$candidate" >/dev/null 2>&1; then
        BROWSER_BIN="$(command -v "$candidate")"
        break
    fi
done

if [ -z "$BROWSER_BIN" ]; then
    echo "[ERROR] Google Chrome atau Chromium tidak ditemukan di sistem Anda!"
    echo "Silakan install Google Chrome: sudo apt install google-chrome-stable atau sudo pacman -S chromium"
    exit 1
fi

echo "[INFO] Menggunakan browser: $BROWSER_BIN"
echo "[INFO] Membuka browser... Silakan login ke YouTube, Carousell, dan Issuu di jendela ini."
echo ""

"$BROWSER_BIN" \
    --remote-debugging-port=$PORT \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --disable-background-timer-throttling \
    --disable-renderer-backgrounding \
    --disable-backgrounding-occluded-windows \
    "$@" &

echo "[SUCCESS] Browser telah dijalankan di background (PID: $!)"
echo "JANGAN TUTUP jendela browser ini selama bot posting sedang bekerja."
