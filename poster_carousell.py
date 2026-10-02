#!/usr/bin/env python3
"""
Carousell Marketplace Auto-Posting Bot
Reads data/carousell_posts.csv, attaches to Chrome via CDP, uploads product photos,
selects category, fills product title, price, condition, description, and publishes listing.
Updates status and listing URLs in CSV safely.
"""

import argparse
import asyncio
import os
import random
import sys
from pathlib import Path

from config import (
    CAROUSELL_CSV,
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

SELL_URL = "https://id.carousell.com/sell"


async def process_carousell_post(page, row: dict, dry_run: bool = False) -> str:
    """
    Menjalankan alur pengisian form Carousell untuk 1 listing.
    Mengembalikan URL listing jika berhasil.
    """
    title = row.get("title", "").strip()
    price = str(row.get("price", "0")).strip()
    condition = row.get("condition", "Baru").strip()
    description = row.get("description", "").strip()
    image_paths_raw = row.get("image_paths", "").strip()
    category = row.get("category", "Gardening").strip() or "Gardening"

    if not title:
        raise ValueError("Judul listing tidak boleh kosong.")

    # Validasi path gambar
    valid_images = []
    if image_paths_raw:
        for p in image_paths_raw.split(";"):
            clean_p = p.strip()
            if clean_p:
                img_path = Path(clean_p)
                if not img_path.is_absolute():
                    img_path = Path.cwd() / img_path
                if img_path.exists():
                    valid_images.append(str(img_path.resolve()))
                else:
                    log_warn(f"File gambar tidak ditemukan: {clean_p}")

    if not valid_images:
        raise FileNotFoundError("Minimal 1 file gambar yang valid harus disertakan untuk Carousell.")

    # Gunakan halaman yang sudah ada jika sudah di carousell, atau goto
    if "carousell" not in page.url or "sell" not in page.url:
        log_info(f"Membuka halaman jual Carousell: {SELL_URL}...")
        await page.goto(SELL_URL, wait_until="domcontentloaded")
    else:
        log_info("Menggunakan halaman jual Carousell yang sudah aktif...")

    await random_delay(2.0, 3.5)

    # 1. Upload Gambar Produk
    log_info(f"Mengunggah {len(valid_images)} foto produk...")
    file_input = page.locator("input[type='file']").first
    await file_input.wait_for(state="attached", timeout=15000)
    await file_input.set_input_files(valid_images)
    await random_delay(3.5, 5.0, "Menunggu preview foto terunggah")

    # 2. Pemilihan Kategori dengan Fallback Bertingkat ke 'Gardening'
    log_info(f"Memeriksa status pemilihan kategori (target: {category})...")

    # 2a. Periksa apakah kategori target atau 'Gardening' sudah terpilih secara otomatis
    already_selected = False
    current_cat_elem = page.locator(f"p:text-is('{category}'), p:text-is('Gardening'), span:text-is('{category}'), span:text-is('Gardening')").first
    try:
        if await current_cat_elem.count() > 0 and await current_cat_elem.is_visible():
            log_info(f"Kategori '{category}' sudah terpilih secara otomatis.")
            already_selected = True
    except Exception:
        pass

    if not already_selected:
        # 2b. Periksa apakah ada chip rekomendasi kategori yang dapat diklik langsung
        suggested_chip = page.locator(
            f"button:has-text('{category}'), div[role='button']:has-text('{category}'), button:has-text('Gardening')"
        ).first
        if await suggested_chip.count() > 0 and await suggested_chip.is_visible():
            log_info(f"Memilih chip rekomendasi kategori '{category}'...")
            await human_click(suggested_chip)
            await random_delay(1.5, 2.5)
        else:
            # 2c. Buka picker kategori (dukungan bilingual: Inggris / Indonesia)
            cat_trigger = page.locator(
                "p:has-text('Select a category'), button:has-text('Select a category'), "
                "p:has-text('Pilih kategori'), button:has-text('Pilih kategori'), "
                "[data-testid*='category']"
            ).first
            if await cat_trigger.count() > 0 and await cat_trigger.is_visible():
                log_info("Membuka dialog pemilihan kategori...")
                await human_click(cat_trigger)
                await random_delay(1.5, 2.5)

                # Coba cari kotak input pencarian kategori jika ada
                cat_search = page.locator("input[placeholder*='Search'], input[placeholder*='Cari']").first
                if await cat_search.count() > 0 and await cat_search.is_visible():
                    await human_type(cat_search, category)
                    await random_delay(1.0, 2.0)

                # Klik kategori target atau fallback ke Gardening
                target_cat = page.locator(f"p:has-text('{category}'), div:has-text('{category}'), button:has-text('{category}')").first
                if await target_cat.count() > 0 and await target_cat.is_visible():
                    await human_click(target_cat)
                else:
                    log_warn(f"Kategori '{category}' tidak ditemukan langsung, menggunakan fallback ke 'Gardening' / 'Everything Else'...")
                    fallback_cat = page.locator(
                        "p:has-text('Gardening'), div:has-text('Gardening'), "
                        "p:has-text('Everything Else'), p:has-text('Lainnya')"
                    ).first
                    if await fallback_cat.count() > 0 and await fallback_cat.is_visible():
                        await human_click(fallback_cat)
                await random_delay(1.5, 2.5)

    # 3. Isi Judul Produk
    log_info(f"Mengisi judul: '{title}'...")
    title_input = page.locator("input[name='field_title'], input[placeholder*='Name your listing']").first
    if await title_input.count() > 0:
        await human_click(title_input)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await human_type(title_input, title)
    else:
        text_inputs = page.locator("form input[type='text']")
        if await text_inputs.count() > 0:
            await human_type(text_inputs.first, title)

    await random_delay(1.5, 2.5)

    # 4. Kondisi Barang (Brand new / Like new / Baru)
    log_info(f"Memilih kondisi barang: {condition}...")
    cond_target = "Brand new" if "baru" in condition.lower() or "new" in condition.lower() else "Like new"
    cond_elem = page.locator(
        f"button:has-text('{cond_target}'), div[role='button']:has-text('{cond_target}'), p:has-text('{cond_target}')"
    ).first
    if await cond_elem.count() > 0:
        await human_click(cond_elem)
        await random_delay(1.0, 2.0)

    # 5. Harga Produk
    log_info(f"Mengisi harga: Rp {price}...")
    price_input = page.locator("input[name='field_price'], input[placeholder*='Price']").first
    if await price_input.count() > 0:
        await human_click(price_input)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await human_type(price_input, price)
        await random_delay(1.0, 2.0)

    # 6. Deskripsi Produk
    if description:
        log_info("Mengisi deskripsi produk...")
        desc_input = page.locator("textarea[name='field_description'], textarea").first
        if await desc_input.count() > 0:
            await human_click(desc_input)
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await human_type(desc_input, description)
            await random_delay(1.5, 2.5)

    await human_scroll(page, steps=2, min_dist=150, max_dist=300)

    # 7. Publikasi (List now)
    if dry_run:
        log_warn("[DRY RUN] Mode uji coba aktif: Tombol 'List Now' tidak diklik.")
        return "https://id.carousell.com/p/preview-dry-run"

    log_info("Mempublikasikan listing ke Carousell...")
    publish_btn = page.locator("button:has-text('List now'), button[type='submit']:has-text('List')").first

    if await publish_btn.count() == 0:
        publish_btn = page.locator("form button[type='submit']").last

    await human_click(publish_btn)
    log_info("Menunggu konfirmasi penerbitan listing...")
    await page.wait_for_timeout(6000)

    current_url = page.url
    log_success(f"Listing berhasil dipublikasikan! URL: {current_url}")
    return current_url


async def main():
    parser = argparse.ArgumentParser(description="Carousell Mass Auto-Posting Bot")
    parser.add_argument(
        "--csv",
        "-c",
        type=str,
        default=str(CAROUSELL_CSV),
        help="Path file CSV Carousell (default: data/carousell_posts.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Jalankan hingga pengisian form tanpa mengklik tombol submit publikasi",
    )
    parser.add_argument(
        "--max-posts",
        "-m",
        type=int,
        default=0,
        help="Maksimal jumlah postingan dalam satu sesi eksekusi (0 = semua pending)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        log_error(f"File {csv_path} tidak ditemukan!")
        log_info("Gunakan builder_template.py untuk membuat file CSV Carousell terlebih dahulu.")
        sys.exit(1)

    fieldnames, rows = read_csv_data(csv_path)
    pending_items = get_pending_rows(rows)

    if not pending_items:
        log_success(f"Semua baris di {csv_path.name} sudah selesai diposting (status success).")
        sys.exit(0)

    total_to_process = len(pending_items)
    if args.max_posts > 0 and args.max_posts < total_to_process:
        pending_items = pending_items[: args.max_posts]
        log_info(f"Membatasi eksekusi hingga {args.max_posts} postingan.")

    log_header(f"Carousell Bot: {len(pending_items)} Postingan Antri")

    # Inisialisasi Browser CDP
    bm = BrowserManager()
    browser, page = await bm.connect("carousell")

    success_count = 0
    fail_count = 0

    try:
        for i, (orig_idx, row) in enumerate(pending_items, 1):
            title = row.get("title", f"Baris {orig_idx + 1}")
            log_header(f"[{i}/{len(pending_items)}] Memproses: {title[:50]}...")

            try:
                post_url = await process_carousell_post(page, row, dry_run=args.dry_run)
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
                log_error(f"Gagal memposting baris {orig_idx + 1}: {err_msg}")
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
                await countdown_delay(delay_sec, message="Jeda aman anti-spam sebelum posting berikutnya")

    finally:
        await bm.disconnect()

    log_header("Ringkasan Selesai")
    log_info(f"Total Berhasil: {success_count} | Gagal: {fail_count}")


if __name__ == "__main__":
    asyncio.run(main())
