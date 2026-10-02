#!/usr/bin/env python3
"""
Google Suggest / Autocomplete Keyword Scraper (Alphabet Soup Method)
Scrapes Google Autocomplete recommendations using high-speed API (miliseconds per request).
Generates clean CSV output for keyword research and auto-posting titles.
"""

import argparse
import json
import re
import string
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Set
import requests

from config import KEYWORDS_DIR
from modules.csv_handler import write_new_csv
from modules.logger import log_error, log_header, log_info, log_success, log_warn

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def fetch_google_suggestions(query: str, lang: str = "id", country: str = "id") -> List[str]:
    """
    Mengambil data rekomendasi dropdown pencarian Google Suggest API.
    """
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "chrome",
        "hl": lang,
        "gl": country,
        "q": query,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and isinstance(data[1], list):
                return [str(item).strip() for item in data[1] if item]
    except Exception as e:
        log_warn(f"Gagal mengambil saran untuk query '{query}': {e}")
    return []


def scrape_alphabet_soup(seed_keyword: str, lang: str = "id", country: str = "id") -> List[dict]:
    """
    Melakukan scraping mendalam dengan metode Alphabet Soup:
    1. Query murni (root)
    2. Query + spasi + 'a' sampai 'z'
    3. Query + spasi + '0' sampai '9'
    4. Pertanyaan / Pre-modifier umum (cara, jual, harga, terbaik)
    """
    seed_clean = seed_keyword.strip().lower()
    results = []
    seen_keywords: Set[str] = set()

    def add_keyword(kw: str, category_type: str):
        kw_clean = kw.strip().lower()
        if kw_clean and kw_clean not in seen_keywords:
            seen_keywords.add(kw_clean)
            results.append({
                "keyword": kw_clean,
                "seed": seed_clean,
                "category_type": category_type,
                "scraped_at": datetime.now().isoformat(),
            })

    log_header(f"Mencari Kata Kunci: '{seed_clean}'")

    # 1. Root Query
    log_info("1. Mengambil rekomendasi kata kunci dasar (Root)...")
    for item in fetch_google_suggestions(seed_clean, lang, country):
        add_keyword(item, "root")
    time.sleep(0.2)

    # 2. Alphabet Soup (A - Z)
    log_info("2. Mengambil Alphabet Soup (A - Z)...")
    for letter in string.ascii_lowercase:
        query = f"{seed_clean} {letter}"
        items = fetch_google_suggestions(query, lang, country)
        for item in items:
            add_keyword(item, f"alphabet_{letter}")
        time.sleep(0.15)  # Delay halus agar tetap sopan

    # 3. Number Soup (0 - 9)
    log_info("3. Mengambil Angka Rekomendasi (0 - 9)...")
    for digit in string.digits:
        query = f"{seed_clean} {digit}"
        items = fetch_google_suggestions(query, lang, country)
        for item in items:
            add_keyword(item, f"number_{digit}")
        time.sleep(0.15)

    # 4. Modifiers Komersial & Populer (jual, harga, cara, terbaik, rekomendasi, murah)
    log_info("4. Mengambil kata kunci modifier komersial...")
    modifiers = ["jual", "harga", "cara", "terbaik", "murah", "distributor", "grosir", "review"]
    for mod in modifiers:
        query = f"{mod} {seed_clean}"
        items = fetch_google_suggestions(query, lang, country)
        for item in items:
            add_keyword(item, f"modifier_{mod}")
        time.sleep(0.15)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Google Suggest / Autocomplete Keyword Scraper (Alphabet Soup)"
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=str,
        help="Kata kunci awal / induk (contoh: 'pupuk sawit')",
    )
    parser.add_argument(
        "--lang",
        "-l",
        type=str,
        default="id",
        help="Bahasa pencarian (default: 'id' untuk Indonesia)",
    )
    parser.add_argument(
        "--country",
        "-c",
        type=str,
        default="id",
        help="Negara pencarian (default: 'id' untuk Indonesia)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Nama file output CSV kustom (opsional)",
    )

    args = parser.parse_args()

    # Jika seed diberikan sebagai string kosong lewat CLI, langsung tolak
    if args.seed is not None:
        seed = args.seed.strip()
        if not seed:
            log_error("Kata kunci tidak boleh kosong.")
            sys.exit(1)
    else:
        # Jika argumen --seed tidak disertakan sama sekali
        if not sys.stdin.isatty():
            log_error("Kata kunci tidak boleh kosong. Gunakan --seed <kata_kunci>.")
            sys.exit(1)

        print("\n========================================================")
        print("   Google Autocomplete / Alphabet Soup Keyword Scraper   ")
        print("========================================================\n")
        try:
            seed = input("Masukkan kata kunci utama (contoh: pupuk sawit): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nDibatalkan.")
            sys.exit(0)

        if not seed:
            log_error("Kata kunci tidak boleh kosong.")
            sys.exit(1)

    # Tentukan nama file output
    if args.output:
        out_file = Path(args.output)
    else:
        slug = re.sub(r"[^\w\-_]", "_", seed.lower()).strip("_")
        out_file = KEYWORDS_DIR / f"keywords_{slug}.csv"

    # Jalankan scraping
    keywords = scrape_alphabet_soup(seed, lang=args.lang, country=args.country)

    if not keywords:
        log_warn("Tidak ditemukan kata kunci.")
        sys.exit(0)

    # Simpan ke CSV
    fieldnames = ["keyword", "seed", "category_type", "scraped_at"]
    write_new_csv(out_file, fieldnames, keywords)

    log_success(f"Selesai! Ditemukan total {len(keywords)} kata kunci unik.")
    log_info(f"File tersimpan di: {out_file}")
    log_info("Tip: Anda sekarang dapat membuka file CSV tersebut di Excel / Google Sheets untuk menyaring kata kunci yang diinginkan.")


if __name__ == "__main__":
    main()
