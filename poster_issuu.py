#!/usr/bin/env python3
"""
Issuu Document / PDF Mass Auto-Publisher Bot
Reads data/issuu_posts.csv, attaches to Chrome via CDP, navigates to Issuu upload,
uploads PDF documents, fills publication title and description, and publishes documents.
Updates status and publication URLs in CSV.
"""

import argparse
import asyncio
import os
import random
import sys
from pathlib import Path

from config import (
    ISSUU_CSV,
    MIN_POST_DELAY,
    MAX_POST_DELAY,
    MIN_ACTION_DELAY,
    MAX_ACTION_DELAY,
)
from modules.browser_manager import BrowserManager
from modules.csv_handler import get_pending_rows, read_csv_data, update_row_status
from modules.human_emulator import (
    countdown_delay,
    human_click,
    human_scroll,
    human_type,
    random_delay,
)
from modules.logger import log_error, log_header, log_info, log_success, log_warn

ISSUU_UPLOAD_URL = "https://issuu.com/home/publisher"


async def publish_issuu_pdf(page, row: dict, dry_run: bool = False) -> str:
    """
    Menjalankan alur upload PDF Issuu untuk 1 dokumen.
    Mengembalikan URL dokumen setelah berhasil dipublikasikan.
    """
    title = row.get("title", "").strip()
    pdf_path_raw = row.get("pdf_path", "").strip()
    description = row.get("description", "").strip()

    if not title:
        raise ValueError("Judul dokumen tidak boleh kosong.")

    pdf_path = Path(pdf_path_raw)
    if not pdf_path.is_absolute():
        pdf_path = Path.cwd() / pdf_path

    if not pdf_path.exists():
        raise FileNotFoundError(f"File PDF tidak ditemukan: {pdf_path_raw}")

    if "publisher" not in page.url and await page.locator("input[type='file']").count() == 0:
        log_info(f"Membuka halaman upload Issuu: {ISSUU_UPLOAD_URL}...")
        try:
            await page.goto(ISSUU_UPLOAD_URL, wait_until="domcontentloaded", timeout=25000)
        except Exception:
            up_btn = page.locator("button:has-text('Upload'), a:has-text('Upload')").first
            if await up_btn.count() > 0:
                await human_click(up_btn)
    else:
        log_info("Menggunakan antarmuka upload Issuu yang sudah aktif...")

    await random_delay(2.5, 4.0, "Menunggu antarmuka Issuu siap")

    # 0. Tutup dialog Cookiebot jika muncul
    cookiebot_btn = page.locator(
        "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll, button:has-text('Allow all'), button:has-text('Allow All')"
    ).first
    try:
        if await cookiebot_btn.is_visible(timeout=3000):
            log_info("Menutup dialog persetujuan Cookiebot Issuu...")
            await cookiebot_btn.click()
            await random_delay(0.5, 1.5)
    except Exception:
        pass

    # 1. Upload File PDF
    log_info(f"Mengunggah file PDF: {pdf_path.name}...")
    file_input = page.locator("input[type='file']").first
    await file_input.wait_for(state="attached", timeout=25000)
    await file_input.set_input_files(str(pdf_path.resolve()))

    # Tunggu proses konversi dokumen awal di Issuu
    log_info("Menunggu Issuu memproses dokumen PDF...")
    await page.wait_for_selector("input[name='title'], input[placeholder*='Title'], input[id*='title']", timeout=60000)
    await random_delay(2.0, 4.0)

    # 2. Judul Dokumen
    log_info(f"Mengisi judul dokumen: '{title[:60]}'...")
    title_input = page.locator("input[name='title'], input[placeholder*='Title'], input[id*='title']").first
    if await title_input.count() > 0:
        await human_click(title_input)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await human_type(title_input, title)
        await random_delay(1.0, 2.0)

    # 3. Deskripsi Dokumen
    if description:
        log_info("Mengisi deskripsi dokumen...")
        desc_input = page.locator("textarea[name='description'], textarea[placeholder*='Description'], textarea").first
        if await desc_input.count() > 0:
            await human_click(desc_input)
            await human_type(desc_input, description)
            await random_delay(1.5, 2.5)

    await human_scroll(page, steps=2, min_dist=150, max_dist=300)

    if dry_run:
        log_warn("[DRY RUN] Mode uji coba aktif: Tombol Publish tidak diklik.")
        return "https://issuu.com/sample-dry-run"

    # 4. Klik Tombol Publikasikan (Publish Now)
    log_info("Mempublikasikan dokumen ke Issuu...")
    publish_btn = page.locator(
        "button:has-text('Publish now'), button:has-text('Publish'), button[type='submit']:has-text('Publish')"
    ).first
    if await publish_btn.count() > 0:
        await human_click(publish_btn)
        log_info("Menunggu konfirmasi terbit...")
        await page.wait_for_timeout(6000)

    current_url = page.url
    log_success(f"Dokumen PDF berhasil dipublikasikan! URL: {current_url}")
    return current_url


async def main():
    parser = argparse.ArgumentParser(description="Issuu Document / PDF Mass Auto-Publisher Bot")
    parser.add_argument(
        "--csv",
        "-c",
        type=str,
        default=str(ISSUU_CSV),
        help="Path file CSV Issuu (default: data/issuu_posts.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Jalankan hingga pengisian detail tanpa mengklik tombol Publish",
    )
    parser.add_argument(
        "--max-posts",
        "-m",
        type=int,
        default=0,
        help="Maksimal dokumen yang dipublikasikan per sesi",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        log_error(f"File {csv_path} tidak ditemukan!")
        log_info("Gunakan builder_template.py untuk membuat file CSV Issuu terlebih dahulu.")
        sys.exit(1)

    fieldnames, rows = read_csv_data(csv_path)
    pending_items = get_pending_rows(rows)

    if not pending_items:
        log_success(f"Semua dokumen di {csv_path.name} sudah selesai diposting.")
        sys.exit(0)

    if args.max_posts > 0 and args.max_posts < len(pending_items):
        pending_items = pending_items[: args.max_posts]
        log_info(f"Membatasi eksekusi hingga {args.max_posts} dokumen.")

    log_header(f"Issuu Bot: {len(pending_items)} Dokumen Antri")

    # Inisialisasi Browser CDP
    bm = BrowserManager()
    browser, page = await bm.connect("issuu")

    success_count = 0
    fail_count = 0

    try:
        for i, (orig_idx, row) in enumerate(pending_items, 1):
            title = row.get("title", f"Baris {orig_idx + 1}")
            log_header(f"[{i}/{len(pending_items)}] Menerbitkan: {title[:50]}...")

            try:
                post_url = await publish_issuu_pdf(page, row, dry_run=args.dry_run)
                update_row_status(
                    filepath=csv_path,
                    fieldnames=fieldnames,
                    rows=rows,
                    row_index=orig_idx,
                    status="success",
                    post_url=post_url,
                )
                success_count += 1
                log_success(f"Status baris {orig_idx + 1} diperbarui menjadi 'success'.")
            except Exception as e:
                fail_count += 1
                err_msg = str(e)
                log_error(f"Gagal menerbitkan baris {orig_idx + 1}: {err_msg}")
                update_row_status(
                    filepath=csv_path,
                    fieldnames=fieldnames,
                    rows=rows,
                    row_index=orig_idx,
                    status="failed",
                    error_msg=err_msg,
                )

            # Jeda acak antar postingan (kecuali baris terakhir)
            if i < len(pending_items):
                delay_sec = random.randint(MIN_POST_DELAY, MAX_POST_DELAY)
                await countdown_delay(delay_sec, message="Jeda aman publikasi Issuu berikutnya")

    finally:
        await bm.disconnect()

    log_header("Ringkasan Selesai")
    log_info(f"Total Dokumen Berhasil: {success_count} | Gagal: {fail_count}")


if __name__ == "__main__":
    asyncio.run(main())
