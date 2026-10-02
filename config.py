"""
Central configuration for Auto-Posting and Keyword Intelligence Bot.
Values can be overridden using environment variables or edited directly here.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
KEYWORDS_DIR = DATA_DIR / "keywords_raw"

# Ensure essential directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
KEYWORDS_DIR.mkdir(parents=True, exist_ok=True)

# CDP (Chrome DevTools Protocol) Configuration
CDP_PORT = int(os.getenv("CDP_PORT", "9222"))
CDP_HOST = os.getenv("CDP_HOST", "localhost")
CDP_URL = f"http://{CDP_HOST}:{CDP_PORT}"

# Delay & Human Cadence Configuration (in seconds)
# Jeda antar baris postingan (untuk mencegah rate-limit / spam detection)
MIN_POST_DELAY = int(os.getenv("MIN_POST_DELAY", "60"))
MAX_POST_DELAY = int(os.getenv("MAX_POST_DELAY", "180"))

# Jeda mengetik per karakter (detik)
MIN_TYPING_DELAY = float(os.getenv("MIN_TYPING_DELAY", "0.03"))
MAX_TYPING_DELAY = float(os.getenv("MAX_TYPING_DELAY", "0.12"))

# Jeda acak antar aksi klik tombol / navigasi (detik)
MIN_ACTION_DELAY = float(os.getenv("MIN_ACTION_DELAY", "1.5"))
MAX_ACTION_DELAY = float(os.getenv("MAX_ACTION_DELAY", "3.5"))

# Timeout Pengaturan Playwright (milidetik)
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "45000"))
NAVIGATION_TIMEOUT_MS = int(os.getenv("NAVIGATION_TIMEOUT_MS", "60000"))

# Default CSV file locations
CAROUSELL_CSV = DATA_DIR / "carousell_posts.csv"
YOUTUBE_CSV = DATA_DIR / "youtube_posts.csv"
ISSUU_CSV = DATA_DIR / "issuu_posts.csv"
