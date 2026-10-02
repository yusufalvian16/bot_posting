#!/usr/bin/env python3
"""
YouTube Studio Mass Auto-Uploader Bot (Video & Shorts)
Reads data/youtube_posts.csv, attaches to Chrome via CDP, opens YouTube Studio,
uploads video files, fills title, description, tags, handles COPPA & visibility settings,
publishes video, and saves YouTube video URL to CSV.
"""

import argparse
import asyncio
import os
import random
import sys
from pathlib import Path

from config import (
    YOUTUBE_CSV,
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
    human_type,
    random_delay,
)
from modules.logger import log_error, log_header, log_info, log_success, log_warn

STUDIO_URL = "https://studio.youtube.com"


async def upload_youtube_video(page, row: dict, dry_run: bool = False, test_mode: bool = False) -> str:
    """
    Menjalankan alur upload video YouTube Studio untuk 1 video.
    Mengembalikan URL video setelah diunggah.
    Jika test_mode=True, visibilitas dipaksa ke 'Private' (Pribadi) agar aman saat testing.
    """
    title = row.get("title", "").strip()
    video_path_raw = row.get("video_path", "").strip()
    description = row.get("description", "").strip()
    vis_raw = row.get("visibility", "Public").strip().lower()

    if test_mode:
        visibility = "Private"
        log_info("🧪 [MODE TEST AKTIF] Visibilitas video dipaksa ke 'Private' (Pribadi) untuk pengujian aman.")
    elif vis_raw in ["unlisted", "tidak publik", "tidak_publik"]:
        visibility = "Unlisted"
    elif vis_raw in ["private", "pribadi"]:
        visibility = "Private"
    else:
        visibility = "Public"
    made_for_kids = row.get("made_for_kids", "false").strip().lower() == "true"

    if not title:
        raise ValueError("Judul video tidak boleh kosong.")

    # Validasi file video
    vid_path = Path(video_path_raw)
    if not vid_path.is_absolute():
        vid_path = Path.cwd() / vid_path

    if not vid_path.exists():
        raise FileNotFoundError(f"File video tidak ditemukan: {video_path_raw}")

    if "studio.youtube" not in page.url or "/video/" in page.url or "/edit" in page.url:
        log_info(f"Membuka YouTube Studio: {STUDIO_URL}...")
        await page.goto(STUDIO_URL, wait_until="domcontentloaded")
        await random_delay(2.5, 4.0, "Menunggu antarmuka Studio siap")
    else:
        log_info("Menggunakan antarmuka YouTube Studio yang aktif...")

    # Tutup modal konfirmasi yang mungkin masih terbuka dari upload sebelumnya
    stale_close = page.locator("#close-button, ytcp-button#close-button, button:has-text('Tutup'), button:has-text('Close')").first
    try:
        if await stale_close.is_visible(timeout=2000):
            await human_click(stale_close)
            await random_delay(1.0, 2.0)
    except Exception:
        pass

    # 1. Buka Modal Upload Video
    log_info("Membuka tombol Buat / Upload Video...")
    file_input = page.locator("input[type='file']").first
    if await file_input.count() == 0:
        create_btn = page.locator("button:has-text('Buat'), button[aria-label='Buat'], #create-icon, button:has-text('Create')").first
        await create_btn.wait_for(state="visible", timeout=20000)
        await create_btn.click()
        await page.wait_for_timeout(1000)

        upload_menu_item = page.locator(
            "yt-formatted-string:has-text('Upload video'), tp-yt-paper-item:has-text('Upload video'), yt-formatted-string:has-text('Upload videos'), tp-yt-paper-item:has-text('Upload videos'), [role='menuitem']:has-text('Upload')"
        ).first
        await upload_menu_item.wait_for(state="visible", timeout=10000)
        await upload_menu_item.click()
        await random_delay(1.5, 2.5)

    # 2. Upload File Video
    log_info(f"Mengunggah file video: {vid_path.name}...")
    file_input = page.locator("input[type='file']").first
    await file_input.wait_for(state="attached", timeout=25000)
    await file_input.set_input_files(str(vid_path.resolve()))

    # Tunggu dialog detail form muncul
    log_info("Menunggu form detail video diproses YouTube...")
    title_box = page.locator("#title-textarea #textbox").first
    await title_box.wait_for(state="visible", timeout=45000)
    await random_delay(2.0, 3.5)

    # 3. Judul Video
    log_info(f"Mengisi judul video: '{title[:60]}'...")
    if await title_box.count() > 0:
        await human_click(title_box)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await human_type(title_box, title[:100])  # Maksimal 100 karakter
        await random_delay(1.0, 2.0)

    # 4. Deskripsi Video
    if description:
        log_info("Mengisi deskripsi video...")
        desc_box = page.locator("#description-textarea #textbox").first
        if await desc_box.count() > 0:
            await human_click(desc_box)
            await human_type(desc_box, description)
            await random_delay(1.5, 2.5)

    # Catatan: Thumbnail dibiarkan otomatis oleh YouTube dari cuplikan video sesuai preferensi user
    log_info("Thumbnail: dibiarkan otomatis oleh YouTube (tanpa upload custom thumbnail)...")

    # 5. Opsi Audiens (COPPA - Not made for kids)
    log_info("Mengatur opsi penonton (Not made for kids)...")
    if made_for_kids:
        kids_radio = page.locator("[name='VIDEO_MADE_FOR_KIDS_MFK'], tp-yt-paper-radio-button:has-text('dibuat untuk anak-anak')").first
    else:
        kids_radio = page.locator(
            "[name='VIDEO_MADE_FOR_KIDS_NOT_MFK'], tp-yt-paper-radio-button:has-text('tidak dibuat untuk anak-anak'), tp-yt-paper-radio-button:has-text('not made for kids')"
        ).first

    if await kids_radio.count() > 0:
        await human_click(kids_radio)
        await random_delay(1.0, 2.0)

    # 6. Navigasi Melalui Tab (Next / Berikutnya) hingga mencapai Visibilitas
    log_info("Menavigasi langkah-langkah wizard menuju Visibilitas...")
    for step in range(5):
        # Cek apakah tab visibilitas sudah tercapai
        vis_ready = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], tp-yt-paper-radio-button[name='UNLISTED']").first
        if await vis_ready.count() > 0 and await vis_ready.is_visible():
            log_info("Langkah Visibilitas berhasil tercapai.")
            break
        next_btn = page.locator("#next-button:visible, button:has-text('Next'), button:has-text('Berikutnya')").first
        if await next_btn.count() > 0 and await next_btn.is_visible():
            await next_btn.click()
            await random_delay(1.5, 2.5)
        else:
            await page.wait_for_timeout(1000)

    # 7. Pengaturan Visibilitas (Visibility) - Default: Public
    log_info(f"Mengatur visibilitas video ke: {visibility}...")
    if visibility == "Public":
        vis_radio = page.locator("tp-yt-paper-radio-button[name='PUBLIC'], #public-radio-button, tp-yt-paper-radio-button:has-text('Publik'), tp-yt-paper-radio-button:has-text('Public')").first
    elif visibility == "Unlisted":
        vis_radio = page.locator("tp-yt-paper-radio-button[name='UNLISTED'], #unlisted-radio-button, tp-yt-paper-radio-button:has-text('Tidak publik'), tp-yt-paper-radio-button:has-text('Unlisted')").first
    else:
        vis_radio = page.locator("tp-yt-paper-radio-button[name='PRIVATE'], #private-radio-button, tp-yt-paper-radio-button:has-text('Pribadi'), tp-yt-paper-radio-button:has-text('Private')").first

    await vis_radio.wait_for(state="visible", timeout=15000)
    await vis_radio.click()
    await random_delay(1.5, 2.5)

    # Ambil tautan video jika sudah ada di preview dialog
    video_url = ""
    link_elem = page.locator("a.ytcp-video-info, a[href*='youtu.be']").first
    if await link_elem.count() > 0:
        video_url = await link_elem.get_attribute("href") or ""
        log_info(f"Link video terdeteksi di preview: {video_url}")

    if dry_run:
        log_warn("[DRY RUN] Mode uji coba aktif: Tombol Simpan/Publikasikan tidak diklik.")
        return video_url or "https://youtu.be/sample-dry-run"

    # 8. Klik Tombol Publikasikan / Simpan
    log_info("Menyimpan dan mempublikasikan video ke Publik...")
    done_btn = page.locator("#done-button:visible, button:has-text('Publikasikan'):visible, button:has-text('Publish'):visible, button:has-text('Simpan'):visible").first
    await done_btn.wait_for(state="visible", timeout=15000)
    await done_btn.click()
    log_info("Menunggu konfirmasi penerbitan video...")
    await page.wait_for_timeout(4000)

    # 9. Tutup modal dialog konfirmasi upload ("Video dipublikasikan" / Share dialog)
    log_info("Memeriksa modal konfirmasi publikasi...")
    share_dialog = page.locator("ytcp-video-share-dialog, ytcp-confirmation-dialog").first
    try:
        await share_dialog.wait_for(state="attached", timeout=8000)
        share_link = share_dialog.locator("a[href*='youtu.be']").first
        if await share_link.count() > 0:
            official_url = await share_link.get_attribute("href")
            if official_url:
                video_url = official_url
        log_info(f"Video YouTube resmi terpublikasi aktif: {video_url}")

        close_btn = page.locator("ytcp-video-share-dialog #close-button, #dialog-close-button, #close-button, ytcp-button#close-button, button:has-text('Tutup'), button:has-text('Close')").first
        if await close_btn.count() > 0 and await close_btn.is_visible():
            await close_btn.click()
            log_info("Modal dialog konfirmasi berhasil ditutup.")
            await random_delay(1.0, 2.0)
    except Exception as e:
        log_warn(f"Modal konfirmasi tidak terdeteksi atau sudah tertutup: {e}")

    log_success(f"Video YouTube berhasil diproses dan tayang Publik! URL: {video_url}")
    return video_url or "Berhasil Dipublikasikan"


async def main():
    parser = argparse.ArgumentParser(description="YouTube Studio Mass Auto-Uploader Bot")
    parser.add_argument(
        "--csv",
        "-c",
        type=str,
        default=str(YOUTUBE_CSV),
        help="Path file CSV YouTube (default: data/youtube_posts.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Jalankan hingga pengisian detail tanpa mengklik tombol Publish/Done",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Jalankan upload lengkap namun paksa visibilitas ke 'Private' (Pribadi) untuk pengujian aman",
    )
    parser.add_argument(
        "--max-posts",
        "-m",
        type=int,
        default=0,
        help="Maksimal video yang diunggah per sesi eksekusi",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        log_error(f"File {csv_path} tidak ditemukan!")
        log_info("Gunakan builder_template.py untuk membuat file CSV YouTube terlebih dahulu.")
        sys.exit(1)

    fieldnames, rows = read_csv_data(csv_path)
    pending_items = get_pending_rows(rows)

    if not pending_items:
        log_success(f"Semua video di {csv_path.name} sudah selesai diposting.")
        sys.exit(0)

    if args.max_posts > 0 and args.max_posts < len(pending_items):
        pending_items = pending_items[: args.max_posts]
        log_info(f"Membatasi eksekusi hingga {args.max_posts} video.")

    log_header(f"YouTube Bot: {len(pending_items)} Video Antri")
    if args.test_mode:
        log_warn("🧪 MODE TEST DIAKTIFKAN: Semua video akan disetel ke Private (Pribadi).")

    # Inisialisasi Browser CDP
    bm = BrowserManager()
    browser, page = await bm.connect("youtube")

    success_count = 0
    fail_count = 0

    try:
        for i, (orig_idx, row) in enumerate(pending_items, 1):
            title = row.get("title", f"Baris {orig_idx + 1}")
            log_header(f"[{i}/{len(pending_items)}] Mengunggah: {title[:50]}...")

            try:
                post_url = await upload_youtube_video(page, row, dry_run=args.dry_run, test_mode=args.test_mode)
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
                log_error(f"Gagal mengunggah baris {orig_idx + 1}: {err_msg}")
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
                await countdown_delay(delay_sec, message="Jeda aman upload YouTube berikutnya")

    finally:
        await bm.disconnect()

    log_header("Ringkasan Selesai")
    log_info(f"Total Video Berhasil: {success_count} | Gagal: {fail_count}")


if __name__ == "__main__":
    asyncio.run(main())
