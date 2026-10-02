#!/usr/bin/env python3
"""
Comprehensive 4-Tier End-to-End Test Suite for Bot-Posting Ecosystem.

Methodology:
- Opaque-box, requirement-driven tests derived from ORIGINAL_REQUEST.md & PROJECT.md.
- 4 Tiers:
    Tier 1: Feature Coverage (GUI imports, launchers, CLI scraper, template builder, CDP status, video codecs)
    Tier 2: Boundary & Corner Cases (Empty seed, special chars, max 100 char YouTube title truncation, offline CDP, missing media)
    Tier 3: Cross-Feature Combinations (Scrape -> Template -> CSV output, CDP attach & tab routing, atomic updates)
    Tier 4: Real-World Scenarios (Full dry-run pipeline, multi-post atomic CSV status transitions)
- Strict test isolation using temporary directories and non-destructive execution.
"""

import asyncio
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PYTHON_EXEC = sys.executable


# ==============================================================================
# TIER 1: FEATURE COVERAGE (SANITY, CONTRACTS & ASSET VALIDATION)
# ==============================================================================

class TestTier1FeatureCoverage(unittest.TestCase):
    """
    Tier 1 validates that all core modules, CLI interfaces, cross-platform launchers,
    status endpoints, and media assets conform to baseline requirements.
    """

    def test_01_gui_import_and_class_contract(self):
        """
        Verify that app_gui can be imported cleanly, defines AutoPostingGUI,
        and provides all required tab setup and control methods.
        Authoritative source: ORIGINAL_REQUEST.md R1 & PROJECT.md § Architecture.
        """
        import app_gui

        self.assertTrue(
            hasattr(app_gui, "AutoPostingGUI"),
            "app_gui.py must define AutoPostingGUI class"
        )
        cls = app_gui.AutoPostingGUI
        required_methods = [
            "_build_tabs",
            "_setup_scraper_tab",
            "_setup_builder_tab",
            "_setup_poster_tab",
            "_start_posting",
            "_stop_posting",
            "log",
        ]
        for method in required_methods:
            self.assertTrue(
                hasattr(cls, method),
                f"AutoPostingGUI must define method '{method}'"
            )

    def test_02_gui_instantiation_integrity(self):
        """
        Verify that AutoPostingGUI instantiates without Tkinter geometry layout errors.
        Authoritative source: ORIGINAL_REQUEST.md AC (GUI launchability without library error).
        Known defect: DEFECT-GUI-01 (line 462 bad option '-width' in pack).
        """
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            self.skipTest("No graphical display server detected (headless environment)")

        import _tkinter
        import app_gui

        try:
            app = app_gui.AutoPostingGUI()
            app.update_idletasks()
            app.destroy()
        except _tkinter.TclError as e:
            if 'bad option "-width"' in str(e):
                self.fail(
                    f"DEFECT-GUI-01: AutoPostingGUI failed to instantiate due to invalid pack option: {e} "
                    "(Fix required in app_gui.py:462: move width=120 from pack() to CTkButton constructor)"
                )
            raise

    def test_03_launcher_scripts(self):
        """
        Verify that cross-platform launcher scripts exist, have valid permissions,
        and reference .venv and app_gui.py or port 9222.
        Authoritative source: PROJECT.md Feature #10 & ORIGINAL_REQUEST.md AC.
        """
        launchers_dir = PROJECT_ROOT / "launchers"
        self.assertTrue(launchers_dir.is_dir(), "launchers/ directory must exist")

        gui_linux = launchers_dir / "start_gui_linux.sh"
        gui_win = launchers_dir / "start_gui_windows.bat"
        chrome_linux = launchers_dir / "start_chrome_linux.sh"
        chrome_win = launchers_dir / "start_chrome_windows.bat"

        self.assertTrue(gui_linux.exists(), "start_gui_linux.sh must exist")
        self.assertTrue(gui_win.exists(), "start_gui_windows.bat must exist")
        self.assertTrue(chrome_linux.exists(), "start_chrome_linux.sh must exist")
        self.assertTrue(chrome_win.exists(), "start_chrome_windows.bat must exist")

        # Verify executable permissions on Linux scripts
        self.assertTrue(
            os.access(gui_linux, os.X_OK),
            "start_gui_linux.sh must be executable (chmod +x)"
        )
        self.assertTrue(
            os.access(chrome_linux, os.X_OK),
            "start_chrome_linux.sh must be executable (chmod +x)"
        )

        # Inspect script contents
        gui_linux_content = gui_linux.read_text(encoding="utf-8")
        self.assertIn("app_gui.py", gui_linux_content)
        self.assertIn(".venv", gui_linux_content)

        gui_win_content = gui_win.read_text(encoding="utf-8")
        self.assertIn("app_gui.py", gui_win_content)
        self.assertIn(".venv", gui_win_content)

        chrome_linux_content = chrome_linux.read_text(encoding="utf-8")
        self.assertTrue(
            "9222" in chrome_linux_content,
            "start_chrome_linux.sh must configure remote debugging port 9222"
        )

        chrome_win_content = chrome_win.read_text(encoding="utf-8")
        self.assertTrue(
            "9222" in chrome_win_content,
            "start_chrome_windows.bat must configure remote debugging port 9222"
        )

    def test_04_cli_keyword_scraper(self):
        """
        Verify CLI keyword scraper execution and output schema.
        Authoritative source: ORIGINAL_REQUEST.md R1 (Tab 1 Alphabet Soup).
        """
        import scraper_keyword

        # Test fetch function contract
        suggestions = scraper_keyword.fetch_google_suggestions("pupuk sawit", lang="id", country="id")
        self.assertIsInstance(suggestions, list, "fetch_google_suggestions must return a list")
        if suggestions:
            self.assertTrue(all(isinstance(s, str) for s in suggestions))

        # Test CLI execution with output redirection to temp file
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_csv = Path(tmp_dir) / "test_keywords.csv"
            cmd = [
                PYTHON_EXEC,
                str(PROJECT_ROOT / "scraper_keyword.py"),
                "--seed", "pupuk sawit uji",
                "--output", str(out_csv),
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=30,
            )
            self.assertEqual(proc.returncode, 0, f"Scraper CLI failed: {proc.stderr}")
            self.assertTrue(out_csv.exists(), "Output CSV file must be created")

            from modules.csv_handler import read_csv_data
            fieldnames, rows = read_csv_data(out_csv)
            expected_fields = ["keyword", "seed", "category_type", "scraped_at"]
            self.assertEqual(fieldnames, expected_fields)
            self.assertGreater(len(rows), 0, "Scraped CSV must contain data rows")

    def test_05_template_builder(self):
        """
        Verify template title formatting and CSV generation across Carousell, YouTube, Issuu.
        Authoritative source: ORIGINAL_REQUEST.md R1 (Tab 2 Template Builder).
        """
        from builder_template import (
            format_title,
            build_carousell_csv,
            build_youtube_csv,
            build_issuu_csv,
        )
        from modules.csv_handler import write_new_csv, read_csv_data

        # 1. Test format_title placeholder substitution
        t1 = format_title("Jual {keyword_title} Murah Berkualitas", "bibit sawit unggul")
        self.assertEqual(t1, "Jual Bibit Sawit Unggul Murah Berkualitas")
        t2 = format_title("Pesan {keyword} sekarang", "pupuk organik")
        self.assertEqual(t2, "Pesan pupuk organik sekarang")

        # 2. Test platform CSV generation in temp sandbox
        with tempfile.TemporaryDirectory() as tmp_dir:
            in_csv = Path(tmp_dir) / "raw.csv"
            raw_data = [
                {"keyword": "pupuk sawit cair", "seed": "pupuk sawit", "category_type": "root", "scraped_at": "2026-10-02T12:00:00"},
                {"keyword": "bibit sawit unggul", "seed": "pupuk sawit", "category_type": "alphabet_b", "scraped_at": "2026-10-02T12:00:01"},
            ]
            write_new_csv(in_csv, ["keyword", "seed", "category_type", "scraped_at"], raw_data)

            # Carousell
            car_csv = Path(tmp_dir) / "carousell.csv"
            build_carousell_csv(
                in_csv, car_csv,
                title_template="Jual {keyword_title}",
                price="150000",
                condition="Baru",
                desc_template="Deskripsi {keyword}",
                image_paths="assets/images/sample_pupuk.jpg",
                category="Gardening",
            )
            car_fields, car_rows = read_csv_data(car_csv)
            self.assertEqual(
                car_fields,
                ["title", "category", "price", "condition", "description", "image_paths", "status", "post_url", "error_msg", "posted_at"]
            )
            self.assertEqual(len(car_rows), 2)
            self.assertEqual(car_rows[0]["status"], "pending")
            self.assertEqual(car_rows[0]["title"], "Jual Pupuk Sawit Cair")

            # YouTube
            yt_csv = Path(tmp_dir) / "youtube.csv"
            build_youtube_csv(
                in_csv, yt_csv,
                title_template="Video {keyword_title}",
                desc_template="Tonton {keyword}",
                video_path="assets/videos/sample_sawit_15s.mp4",
                tags="sawit, pupuk",
                visibility="Unlisted",
                made_for_kids="false",
            )
            yt_fields, yt_rows = read_csv_data(yt_csv)
            self.assertEqual(
                yt_fields,
                ["title", "video_path", "description", "tags", "visibility", "made_for_kids", "status", "post_url", "error_msg", "posted_at"]
            )
            self.assertEqual(len(yt_rows), 2)
            self.assertEqual(yt_rows[0]["status"], "pending")

            # Issuu
            issuu_csv = Path(tmp_dir) / "issuu.csv"
            build_issuu_csv(
                in_csv, issuu_csv,
                title_template="Katalog {keyword_title}",
                desc_template="Dokumen {keyword}",
                pdf_path="assets/docs/sample_katalog.pdf",
            )
            issuu_fields, issuu_rows = read_csv_data(issuu_csv)
            self.assertEqual(
                issuu_fields,
                ["title", "pdf_path", "description", "status", "post_url", "error_msg", "posted_at"]
            )
            self.assertEqual(len(issuu_rows), 2)
            self.assertEqual(issuu_rows[0]["status"], "pending")

    def test_06_cdp_status_endpoint(self):
        """
        Verify Chrome Remote Debugging configuration and status endpoint.
        Authoritative source: PROJECT.md Feature #8 & ORIGINAL_REQUEST.md R1 (Tab 4).
        """
        import config

        self.assertEqual(config.CDP_PORT, 9222)
        self.assertEqual(config.CDP_URL, "http://localhost:9222")

        # Probe port 9222 endpoint
        url = f"{config.CDP_URL}/json/version"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BotPostingTest/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.assertEqual(resp.status, 200)
                payload = json.loads(resp.read().decode("utf-8"))
                self.assertIn("Browser", payload)
                self.assertIn("webSocketDebuggerUrl", payload)
        except Exception as e:
            self.skipTest(f"Chrome remote debugging endpoint on port 9222 not reachable: {e}")

    def test_07_video_codec_and_media_assets(self):
        """
        Validate duration, codecs, and file integrity of sample media assets.
        Authoritative source: ORIGINAL_REQUEST.md R3.
        """
        video_path = PROJECT_ROOT / "assets" / "videos" / "sample_sawit_15s.mp4"
        image_path = PROJECT_ROOT / "assets" / "images" / "sample_pupuk.jpg"
        doc_path = PROJECT_ROOT / "assets" / "docs" / "sample_katalog.pdf"

        # Check file existence
        self.assertTrue(video_path.exists(), f"Sample video not found at {video_path}")
        self.assertTrue(image_path.exists(), f"Sample image not found at {image_path}")
        self.assertTrue(doc_path.exists(), f"Sample doc not found at {doc_path}")

        # Check image magic bytes (JPEG \xff\xd8\xff)
        with open(image_path, "rb") as f:
            header = f.read(3)
            self.assertEqual(header, b"\xff\xd8\xff", "sample_pupuk.jpg must be a valid JPEG")

        # Check doc magic bytes (PDF %PDF-)
        with open(doc_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-", "sample_katalog.pdf must be a valid PDF document")

        # Check video codec via ffprobe
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_name,codec_type,duration",
            "-of", "json",
            str(video_path)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=10)
        if proc.returncode != 0:
            self.skipTest(f"ffprobe not available or failed: {proc.stderr}")

        data = json.loads(proc.stdout)
        streams = data.get("streams", [])
        self.assertGreaterEqual(len(streams), 2, "Video must contain both video and audio streams")

        # Stream 0: H.264 video
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        self.assertIsNotNone(video_stream, "Video stream must be present")
        self.assertEqual(video_stream.get("codec_name"), "h264")
        dur = float(video_stream.get("duration", 0))
        self.assertGreaterEqual(dur, 14.5, "Duration must be at least 15 seconds")
        self.assertLessEqual(dur, 30.5, "Duration must be within 15-30 seconds requirement")

        # Stream 1: AAC audio
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        self.assertIsNotNone(audio_stream, "Audio stream must be present")
        self.assertEqual(audio_stream.get("codec_name"), "aac")


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (LIMITS, SPECIAL CHARS & FAULT TOLERANCE)
# ==============================================================================

class TestTier2BoundaryCornerCases(unittest.TestCase):
    """
    Tier 2 verifies system boundaries, defensive error handling, format constraints,
    and resilience against invalid or hostile inputs.
    """

    def test_08_empty_seed_handling(self):
        """
        Verify that scraper_keyword.py rejects empty seed strings with non-zero exit code.
        Authoritative source: PRD.md § Error Handling & ORIGINAL_REQUEST.md R1.
        """
        cmd_empty = [
            PYTHON_EXEC,
            str(PROJECT_ROOT / "scraper_keyword.py"),
            "--seed", "",
        ]
        proc = subprocess.run(
            cmd_empty,
            input="\n",
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertNotEqual(proc.returncode, 0, "CLI must reject empty seed with non-zero exit code")
        self.assertIn("Kata kunci tidak boleh kosong", proc.stdout + proc.stderr)

    def test_09_special_characters_and_encoding(self):
        """
        Verify that special characters, ampersands, quotes, and Indonesian accents
        are preserved without corruption across CSV write/read cycles.
        Authoritative source: PROJECT.md Feature #21 (utf-8-sig / Excel compatibility).
        """
        from modules.csv_handler import write_new_csv, read_csv_data

        test_string = "Pupuk & Sawit Super (100% Organik) — \"Pilihan Terbaik\" #1 'Unggulan'"
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "special.csv"
            write_new_csv(csv_path, ["keyword", "notes"], [{"keyword": test_string, "notes": "Tes karakter khusus"}])

            # Read back
            fieldnames, rows = read_csv_data(csv_path)
            self.assertEqual(rows[0]["keyword"], test_string, "String fidelity must be preserved")
            self.assertEqual(rows[0]["notes"], "Tes karakter khusus")

    def test_10_youtube_title_100_char_truncation(self):
        """
        Verify that YouTube video titles exceeding 100 characters are strictly truncated.
        Authoritative source: PROJECT.md Feature #6 / YouTube Studio 100-character constraint.
        """
        from builder_template import build_youtube_csv
        from modules.csv_handler import write_new_csv, read_csv_data

        with tempfile.TemporaryDirectory() as tmp_dir:
            in_csv = Path(tmp_dir) / "long_keyword.csv"
            out_csv = Path(tmp_dir) / "yt_out.csv"

            # Create an excessively long keyword (120 characters)
            long_kw = "pupuk sawit super pemacu buah kelapa sawit usia dewasa di lahan gambut riau sumatera kalimantan indonesia 2026"
            write_new_csv(in_csv, ["keyword"], [{"keyword": long_kw}])

            build_youtube_csv(
                in_csv, out_csv,
                title_template="Rahasia {keyword_title} Hasil Panen Melimpah",
                desc_template="Deskripsi",
                video_path="assets/videos/sample_sawit_15s.mp4",
                tags="sawit",
                visibility="Unlisted",
                made_for_kids="false",
            )

            _, rows = read_csv_data(out_csv)
            title = rows[0]["title"]
            self.assertLessEqual(len(title), 100, f"YouTube title must not exceed 100 characters: got {len(title)}")
            self.assertTrue(title.endswith("..."), "Truncated title must end with ellipsis '...'")

    def test_11_offline_cdp_port_handling(self):
        """
        Verify that connecting to an offline CDP port raises ConnectionError
        instead of terminating the entire process via sys.exit(1).
        Authoritative source: PROJECT.md § Interface Contracts.
        """
        from modules.browser_manager import BrowserManager

        bm = BrowserManager(cdp_url="http://localhost:59999")
        try:
            asyncio.run(bm.connect())
            self.fail("BrowserManager.connect() to offline port must not succeed")
        except ConnectionError:
            # Passes interface contract!
            pass
        except SystemExit as e:
            self.fail(
                f"DEFECT-CDP-02: BrowserManager.connect() called sys.exit({e.code}) on failure. "
                "Interface contract requires raising ConnectionError instead of terminating host process."
            )
        except Exception as e:
            self.assertIn("59999", str(e))

    def test_12_missing_media_file_detection(self):
        """
        Verify that poster processing detects non-existent media files and raises FileNotFoundError.
        Authoritative source: PRD.md § Error Handling.
        """
        from poster_carousell import process_carousell_post

        dummy_row = {
            "title": "Uji Media Hilang",
            "price": "100000",
            "condition": "Baru",
            "description": "Deskripsi",
            "image_paths": "assets/images/non_existent_image_12345.jpg",
            "category": "Gardening",
        }

        mock_page = MagicMock()
        mock_page.url = "https://id.carousell.com/sell"

        async def run_check():
            await process_carousell_post(mock_page, dummy_row, dry_run=True)

        with self.assertRaises(FileNotFoundError):
            asyncio.run(run_check())

    def test_13_csv_pending_filtering(self):
        """
        Verify get_pending_rows filters rows correctly based on status.
        Authoritative source: PROJECT.md Feature #21.
        """
        from modules.csv_handler import get_pending_rows

        rows = [
            {"title": "Item 1", "status": "pending"},
            {"title": "Item 2", "status": "success"},
            {"title": "Item 3", "status": ""},
            {"title": "Item 4", "status": "failed"},
            {"title": "Item 5", "status": "posted"},
            {"title": "Item 6", "status": "done"},
        ]

        pending = get_pending_rows(rows)
        # Should include row 0 (pending), row 2 (""), row 3 (failed)
        pending_indices = [idx for idx, _ in pending]
        self.assertEqual(pending_indices, [0, 2, 3])

        # Test empty list
        self.assertEqual(get_pending_rows([]), [])

        # Test all success list
        all_success = [{"title": "Item", "status": "success"}, {"title": "Item", "status": "posted"}]
        self.assertEqual(get_pending_rows(all_success), [])


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (MULTI-MODULE INTEGRATION & ROUTING)
# ==============================================================================

class TestTier3CrossFeatureCombinations(unittest.TestCase):
    """
    Tier 3 tests verify integrations between modules: Keyword Scraper -> Template Builder,
    BrowserManager domain tab routing, and atomic multi-row status persistence.
    """

    def test_14_pipeline_scrape_to_templates(self):
        """
        Verify cross-feature pipeline: Raw keywords CSV -> Template Builder -> 3 Platform CSVs.
        Authoritative source: ORIGINAL_REQUEST.md AC.
        """
        from builder_template import build_carousell_csv, build_youtube_csv, build_issuu_csv
        from modules.csv_handler import write_new_csv, read_csv_data

        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_csv = Path(tmp_dir) / "keywords_raw.csv"
            raw_keywords = [
                {"keyword": "pupuk sawit buah lebat", "seed": "pupuk sawit", "category_type": "root", "scraped_at": "2026-10-02T12:00:00"},
                {"keyword": "pupuk sawit tanah gambut", "seed": "pupuk sawit", "category_type": "alphabet_t", "scraped_at": "2026-10-02T12:00:01"},
                {"keyword": "pupuk sawit nasa terbaik", "seed": "pupuk sawit", "category_type": "modifier_terbaik", "scraped_at": "2026-10-02T12:00:02"},
            ]
            write_new_csv(raw_csv, ["keyword", "seed", "category_type", "scraped_at"], raw_keywords)

            # Build platform CSVs
            car_csv = Path(tmp_dir) / "carousell_posts.csv"
            yt_csv = Path(tmp_dir) / "youtube_posts.csv"
            issuu_csv = Path(tmp_dir) / "issuu_posts.csv"

            build_carousell_csv(
                raw_csv, car_csv,
                title_template="Jual {keyword_title} Murah",
                price="175000",
                condition="Baru",
                desc_template="Hubungi kami untuk {keyword}",
                image_paths="assets/images/sample_pupuk.jpg",
                category="Gardening",
            )
            build_youtube_csv(
                raw_csv, yt_csv,
                title_template="Panduan {keyword_title}",
                desc_template="Video seputar {keyword}",
                video_path="assets/videos/sample_sawit_15s.mp4",
                tags="sawit, pupuk",
                visibility="Unlisted",
                made_for_kids="false",
            )
            build_issuu_csv(
                raw_csv, issuu_csv,
                title_template="Brosur {keyword_title}",
                desc_template="Unduh brosur {keyword}",
                pdf_path="assets/docs/sample_katalog.pdf",
            )

            # Verify all 3 CSVs exist and contain exactly 3 rows
            _, car_rows = read_csv_data(car_csv)
            _, yt_rows = read_csv_data(yt_csv)
            _, issuu_rows = read_csv_data(issuu_csv)

            self.assertEqual(len(car_rows), 3)
            self.assertEqual(len(yt_rows), 3)
            self.assertEqual(len(issuu_rows), 3)

            # Verify status in all 3 is initialized to 'pending'
            self.assertTrue(all(r["status"] == "pending" for r in car_rows))
            self.assertTrue(all(r["status"] == "pending" for r in yt_rows))
            self.assertTrue(all(r["status"] == "pending" for r in issuu_rows))

    def test_15_browser_manager_tab_routing_contract(self):
        """
        Verify BrowserManager.get_or_create_page domain routing logic.
        Authoritative source: PROJECT.md Feature #12 & Interface Contracts.
        """
        from modules.browser_manager import BrowserManager

        bm = BrowserManager()
        # Mock browser context with existing open pages
        mock_context = MagicMock()
        mock_carousell_page = MagicMock()
        mock_carousell_page.url = "https://id.carousell.com/sell"
        mock_carousell_page.is_closed.return_value = False
        mock_carousell_page.bring_to_front = AsyncMock()

        mock_youtube_page = MagicMock()
        mock_youtube_page.url = "https://studio.youtube.com/channel/123"
        mock_youtube_page.is_closed.return_value = False
        mock_youtube_page.bring_to_front = AsyncMock()

        mock_new_page = MagicMock()
        mock_new_page.url = "about:blank"
        mock_new_page.is_closed.return_value = False
        mock_new_page.bring_to_front = AsyncMock()

        mock_context.pages = [mock_carousell_page, mock_youtube_page]
        mock_context.new_page = AsyncMock(return_value=mock_new_page)
        bm._context = mock_context

        async def test_routing():
            # Domain hint 'carousell' must return mock_carousell_page
            p_car = await bm.get_or_create_page("carousell")
            self.assertEqual(p_car, mock_carousell_page)

            # Domain hint 'youtube' must return mock_youtube_page
            p_yt = await bm.get_or_create_page("youtube")
            self.assertEqual(p_yt, mock_youtube_page)

            # Unknown domain must create a new page
            p_new = await bm.get_or_create_page("issuu")
            self.assertEqual(p_new, mock_new_page)

        asyncio.run(test_routing())

    def test_16_atomic_csv_status_updates(self):
        """
        Verify two-phase atomic write updating status, post_url, error_msg, posted_at.
        Authoritative source: PROJECT.md Feature #21 & ORIGINAL_REQUEST.md AC.
        """
        from modules.csv_handler import write_new_csv, read_csv_data, update_row_status

        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "test_lifecycle.csv"
            initial_rows = [
                {"title": "Post 1", "status": "pending", "post_url": "", "error_msg": "", "posted_at": ""},
                {"title": "Post 2", "status": "pending", "post_url": "", "error_msg": "", "posted_at": ""},
            ]
            fieldnames = ["title", "status", "post_url", "error_msg", "posted_at"]
            write_new_csv(csv_path, fieldnames, initial_rows)

            # Update row 0 to success
            fieldnames, rows = read_csv_data(csv_path)
            update_row_status(
                filepath=csv_path,
                fieldnames=fieldnames,
                rows=rows,
                row_index=0,
                status="success",
                post_url="https://id.carousell.com/p/test-post-1",
            )

            # Verify atomic update
            temp_path = csv_path.with_suffix(".tmp")
            self.assertFalse(temp_path.exists(), "Temporary .tmp file must be replaced and not left on disk")

            # Read back
            _, updated_rows = read_csv_data(csv_path)
            self.assertEqual(updated_rows[0]["status"], "success")
            self.assertEqual(updated_rows[0]["post_url"], "https://id.carousell.com/p/test-post-1")
            self.assertTrue(bool(updated_rows[0]["posted_at"]), "posted_at must be populated with timestamp")

            # Update row 1 to failed
            update_row_status(
                filepath=csv_path,
                fieldnames=fieldnames,
                rows=updated_rows,
                row_index=1,
                status="failed",
                error_msg="Selector timeout: button not found",
            )
            _, final_rows = read_csv_data(csv_path)
            self.assertEqual(final_rows[1]["status"], "failed")
            self.assertEqual(final_rows[1]["error_msg"], "Selector timeout: button not found")
            self.assertEqual(final_rows[0]["status"], "success", "Row 0 status must remain intact")


# ==============================================================================
# TIER 4: REAL-WORLD SCENARIOS (DRY-RUN EXECUTION & QUEUE LIFECYCLE)
# ==============================================================================

class TestTier4RealWorldScenarios(unittest.TestCase):
    """
    Tier 4 tests execute simulated operational workflows, verifying that
    posting bots operate correctly in dry-run mode and persist queue states safely.
    """

    def test_17_poster_cli_interface_contracts(self):
        """
        Verify CLI options (--help, --dry-run, --max-posts, --csv) across all 3 poster runners.
        Authoritative source: ORIGINAL_REQUEST.md R1 & PROJECT.md Architecture.
        """
        posters = ["poster_carousell.py", "poster_youtube.py", "poster_issuu.py"]
        for p in posters:
            script = PROJECT_ROOT / p
            self.assertTrue(script.exists(), f"Poster script {p} must exist")
            cmd = [PYTHON_EXEC, str(script), "--help"]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=10,
            )
            self.assertEqual(proc.returncode, 0, f"{p} --help must return 0")
            self.assertIn("--dry-run", proc.stdout, f"{p} must support --dry-run flag")
            self.assertIn("--max-posts", proc.stdout, f"{p} must support --max-posts parameter")
            self.assertIn("--csv", proc.stdout, f"{p} must support --csv parameter")

    def test_18_dry_run_carousell_execution(self):
        """
        Verify isolated dry-run execution of Carousell poster with sample media.
        Authoritative source: ORIGINAL_REQUEST.md R1/R3 & PRD.md.
        """
        from poster_carousell import process_carousell_post

        # Create mock page simulating Carousell sell form DOM
        mock_page = MagicMock()
        mock_page.url = "https://id.carousell.com/sell"
        mock_page.goto = AsyncMock()
        mock_page.keyboard.press = AsyncMock()

        loc = MagicMock()
        loc.first = loc
        loc.count = AsyncMock(return_value=1)
        loc.is_visible = AsyncMock(return_value=True)
        loc.wait_for = AsyncMock()
        loc.set_input_files = AsyncMock()
        mock_page.locator.return_value = loc

        row = {
            "title": "Jual Pupuk Sawit Uji Kualitas Super",
            "price": "180000",
            "condition": "Baru",
            "description": "Deskripsi produk pupuk sawit berkualitas tinggi.",
            "image_paths": str(PROJECT_ROOT / "assets" / "images" / "sample_pupuk.jpg"),
            "category": "Gardening",
        }

        async def run_dry():
            with patch("poster_carousell.random_delay", new_callable=AsyncMock), \
                 patch("poster_carousell.human_click", new_callable=AsyncMock), \
                 patch("poster_carousell.human_type", new_callable=AsyncMock), \
                 patch("poster_carousell.human_scroll", new_callable=AsyncMock):
                url = await process_carousell_post(mock_page, row, dry_run=True)
                return url

        dry_url = asyncio.run(run_dry())
        self.assertIn("dry-run", dry_url, f"Dry run must return a preview URL, got: {dry_url}")

    def test_19_dry_run_multi_platform_validation(self):
        """
        Verify that YouTube and Issuu posting routines validate assets in dry-run mode.
        Authoritative source: ORIGINAL_REQUEST.md R1/R3 & PRD.md.
        """
        from poster_youtube import upload_youtube_video
        from poster_issuu import publish_issuu_pdf

        # 1. YouTube dry-run with sample video
        yt_row = {
            "title": "Panduan Pemupukan Kelapa Sawit",
            "video_path": str(PROJECT_ROOT / "assets" / "videos" / "sample_sawit_15s.mp4"),
            "description": "Tips pemupukan",
            "tags": "sawit, pupuk",
            "visibility": "Unlisted",
            "made_for_kids": "false",
        }
        mock_yt_page = MagicMock()
        mock_yt_page.url = "https://studio.youtube.com"
        mock_yt_page.goto = AsyncMock()
        mock_yt_page.wait_for_selector = AsyncMock()
        mock_yt_page.keyboard.press = AsyncMock()
        yt_loc = MagicMock()
        yt_loc.first = yt_loc
        yt_loc.count = AsyncMock(return_value=1)
        yt_loc.is_visible = AsyncMock(return_value=True)
        yt_loc.wait_for = AsyncMock()
        yt_loc.set_input_files = AsyncMock()
        yt_loc.click = AsyncMock()
        yt_loc.get_attribute = AsyncMock(return_value="https://youtu.be/sample-test-id")
        mock_yt_page.locator.return_value = yt_loc

        # 2. Issuu dry-run with sample doc
        issuu_row = {
            "title": "Katalog Sawit 2026",
            "pdf_path": str(PROJECT_ROOT / "assets" / "docs" / "sample_katalog.pdf"),
            "description": "Katalog pupuk",
        }
        mock_issuu_page = MagicMock()
        mock_issuu_page.url = "https://issuu.com/home/publisher"
        mock_issuu_page.goto = AsyncMock()
        mock_issuu_page.wait_for_selector = AsyncMock()
        mock_issuu_page.keyboard.press = AsyncMock()
        issuu_loc = MagicMock()
        issuu_loc.first = issuu_loc
        issuu_loc.count = AsyncMock(return_value=1)
        issuu_loc.is_visible = AsyncMock(return_value=True)
        issuu_loc.wait_for = AsyncMock()
        issuu_loc.set_input_files = AsyncMock()
        issuu_loc.click = AsyncMock()
        issuu_loc.get_attribute = AsyncMock(return_value="https://issuu.com/user/docs/sample")
        mock_issuu_page.locator.return_value = issuu_loc

        async def run_dry_platforms():
            with patch("poster_youtube.random_delay", new_callable=AsyncMock), \
                 patch("poster_youtube.human_click", new_callable=AsyncMock), \
                 patch("poster_youtube.human_type", new_callable=AsyncMock), \
                 patch("poster_issuu.random_delay", new_callable=AsyncMock), \
                 patch("poster_issuu.human_click", new_callable=AsyncMock), \
                 patch("poster_issuu.human_type", new_callable=AsyncMock), \
                 patch("poster_issuu.human_scroll", new_callable=AsyncMock):
                yt_res = await upload_youtube_video(mock_yt_page, yt_row, dry_run=True)
                issuu_res = await publish_issuu_pdf(mock_issuu_page, issuu_row, dry_run=True)
                return yt_res, issuu_res

        yt_res, issuu_res = asyncio.run(run_dry_platforms())
        self.assertTrue(yt_res.startswith("https://youtu.be/"))
        self.assertIn("dry-run", issuu_res)

    def test_20_multi_post_atomic_csv_lifecycle(self):
        """
        Simulate full multi-post sequential queue processing lifecycle:
        Pending -> Row 0 Success -> Row 1 Fail (Network) -> Row 2 Success -> Check Pending Queue.
        Authoritative source: ORIGINAL_REQUEST.md AC (atomic status transitions).
        """
        from modules.csv_handler import write_new_csv, read_csv_data, update_row_status, get_pending_rows

        with tempfile.TemporaryDirectory() as tmp_dir:
            queue_csv = Path(tmp_dir) / "queue.csv"
            initial_posts = [
                {"title": "Post 1", "status": "pending", "post_url": "", "error_msg": "", "posted_at": ""},
                {"title": "Post 2", "status": "pending", "post_url": "", "error_msg": "", "posted_at": ""},
                {"title": "Post 3", "status": "pending", "post_url": "", "error_msg": "", "posted_at": ""},
            ]
            fieldnames = ["title", "status", "post_url", "error_msg", "posted_at"]
            write_new_csv(queue_csv, fieldnames, initial_posts)

            # Step 1: Initial state has 3 pending
            _, rows = read_csv_data(queue_csv)
            pending = get_pending_rows(rows)
            self.assertEqual(len(pending), 3)

            # Step 2: Post 1 succeeds
            update_row_status(queue_csv, fieldnames, rows, 0, "success", post_url="https://example.com/1")

            # Step 3: Post 2 fails (e.g. timeout)
            _, rows = read_csv_data(queue_csv)
            update_row_status(queue_csv, fieldnames, rows, 1, "failed", error_msg="Timeout waiting for selector")

            # Step 4: Post 3 succeeds
            _, rows = read_csv_data(queue_csv)
            update_row_status(queue_csv, fieldnames, rows, 2, "success", post_url="https://example.com/3")

            # Step 5: Verify final state
            _, final_rows = read_csv_data(queue_csv)
            self.assertEqual(final_rows[0]["status"], "success")
            self.assertEqual(final_rows[1]["status"], "failed")
            self.assertEqual(final_rows[2]["status"], "success")

            # get_pending_rows should now only return row 1 (the failed one eligible for retry)
            remaining_pending = get_pending_rows(final_rows)
            self.assertEqual(len(remaining_pending), 1)
            self.assertEqual(remaining_pending[0][0], 1)
            self.assertEqual(remaining_pending[0][1]["title"], "Post 2")


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

def run_tests():
    """
    Executes the 4-Tier test suite and prints structured summary.
    """
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestTier1FeatureCoverage))
    suite.addTests(loader.loadTestsFromTestCase(TestTier2BoundaryCornerCases))
    suite.addTests(loader.loadTestsFromTestCase(TestTier3CrossFeatureCombinations))
    suite.addTests(loader.loadTestsFromTestCase(TestTier4RealWorldScenarios))

    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
