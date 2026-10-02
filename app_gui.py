#!/usr/bin/env python3
"""
Desktop GUI Application for Multi-Platform Mass Auto-Posting & Keyword Intelligence Bot
Built with CustomTkinter for cross-platform compatibility on Windows & Linux.
Features non-blocking background threading for smooth performance.
"""

import asyncio
import json
import os
import queue
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

import customtkinter as ctk

from config import (
    ASSETS_DIR,
    BASE_DIR,
    CAROUSELL_CSV,
    CDP_URL,
    DATA_DIR,
    ISSUU_CSV,
    KEYWORDS_DIR,
    MAX_POST_DELAY,
    MIN_POST_DELAY,
    YOUTUBE_CSV,
)
import webbrowser
from modules.csv_handler import (
    detect_platform_from_fieldnames,
    get_csv_progress_stats,
    get_pending_rows,
    read_csv_data,
    save_csv_data,
    update_row_status,
    write_new_csv,
)
from scraper_keyword import scrape_alphabet_soup
from builder_template import build_carousell_csv, build_issuu_csv, build_youtube_csv

# Inisialisasi tema CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class EditRowDialog(ctk.CTkToplevel):
    def __init__(self, parent, row_dict: dict, fieldnames: List[str], on_save_callback):
        super().__init__(parent)
        self.parent = parent
        self.row_dict = dict(row_dict)
        self.fieldnames = list(fieldnames)
        self.on_save_callback = on_save_callback

        self.title("✏️ Edit Baris Postingan CSV")
        self.geometry("640x700")
        self.minsize(560, 580)
        self.transient(parent)
        self.grab_set()

        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 320
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 350
            self.geometry(f"+{max(50, x)}+{max(50, y)}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title_lbl = ctk.CTkLabel(
            header,
            text="Detail & Konfigurasi Baris Postingan",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            header,
            text="Ubah judul, status antrian, media, atau parameter postingan di bawah ini.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        sub_lbl.pack(anchor="w")

        scroll_frame = ctk.CTkScrollableFrame(self, corner_radius=8)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.entries = {}

        # 1. Judul
        ctk.CTkLabel(scroll_frame, text="Judul Postingan (Title):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.entries["title"] = ctk.CTkEntry(scroll_frame)
        self.entries["title"].insert(0, self.row_dict.get("title", ""))
        self.entries["title"].pack(fill="x", pady=(0, 10))

        # 2. File Media
        media_col = "video_path" if "video_path" in self.fieldnames else ("photos" if "photos" in self.fieldnames else ("file_path" if "file_path" in self.fieldnames else "media_path"))
        ctk.CTkLabel(scroll_frame, text=f"File Media ({media_col}):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        media_box = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        media_box.pack(fill="x", pady=(0, 10))

        self.entries[media_col] = ctk.CTkEntry(media_box)
        self.entries[media_col].insert(0, self.row_dict.get(media_col, ""))
        self.entries[media_col].pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            media_box,
            text="Browse...",
            width=90,
            command=lambda c=media_col: self._browse_media(c),
        )
        browse_btn.pack(side="left")

        # 3. Status Antrian
        ctk.CTkLabel(scroll_frame, text="Status Postingan:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        curr_status = self.row_dict.get("status", "pending").strip().lower()
        if curr_status not in ["pending", "success", "failed", "skipped"]:
            curr_status = "pending"
        self.entries["status"] = ctk.CTkOptionMenu(
            scroll_frame,
            values=["pending", "success", "failed", "skipped"],
            width=200,
        )
        self.entries["status"].set(curr_status)
        self.entries["status"].pack(anchor="w", pady=(0, 10))

        # 4. Visibilitas (Jika YouTube / Issuu)
        if "visibility" in self.fieldnames:
            ctk.CTkLabel(scroll_frame, text="Visibilitas:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
            curr_vis = self.row_dict.get("visibility", "Public").strip()
            if curr_vis not in ["Public", "Unlisted", "Private"]:
                curr_vis = "Public"
            self.entries["visibility"] = ctk.CTkOptionMenu(
                scroll_frame,
                values=["Public", "Unlisted", "Private"],
                width=200,
            )
            self.entries["visibility"].set(curr_vis)
            self.entries["visibility"].pack(anchor="w", pady=(0, 10))

        # 5. Harga (Jika Carousell)
        if "price" in self.fieldnames:
            ctk.CTkLabel(scroll_frame, text="Harga (Rp):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
            self.entries["price"] = ctk.CTkEntry(scroll_frame, width=200)
            self.entries["price"].insert(0, self.row_dict.get("price", "0"))
            self.entries["price"].pack(anchor="w", pady=(0, 10))

        # 6. Tags / Kata Kunci
        if "tags" in self.fieldnames:
            ctk.CTkLabel(scroll_frame, text="Tags / Kata Kunci:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
            self.entries["tags"] = ctk.CTkEntry(scroll_frame)
            self.entries["tags"].insert(0, self.row_dict.get("tags", ""))
            self.entries["tags"].pack(fill="x", pady=(0, 10))

        # 7. Deskripsi (Multiline)
        ctk.CTkLabel(scroll_frame, text="Deskripsi Postingan:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.desc_textbox = ctk.CTkTextbox(scroll_frame, height=110)
        self.desc_textbox.insert("1.0", self.row_dict.get("description", ""))
        self.desc_textbox.pack(fill="x", pady=(0, 10))

        # 8. Post URL (Live Link)
        ctk.CTkLabel(scroll_frame, text="URL Postingan Resmi (Live Link):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.entries["post_url"] = ctk.CTkEntry(scroll_frame)
        self.entries["post_url"].insert(0, self.row_dict.get("post_url", ""))
        self.entries["post_url"].pack(fill="x", pady=(0, 10))

        # 9. Pesan Error (Error Msg)
        ctk.CTkLabel(scroll_frame, text="Pesan Error (jika gagal):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.entries["error_msg"] = ctk.CTkEntry(scroll_frame)
        self.entries["error_msg"].insert(0, self.row_dict.get("error_msg", ""))
        self.entries["error_msg"].pack(fill="x", pady=(0, 10))

        # Bottom Action Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 15))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Simpan Perubahan",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#15803d",
            hover_color="#166534",
            height=36,
            command=self._save_changes,
        )
        save_btn.pack(side="right", padx=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Batal",
            height=36,
            fg_color="gray40",
            hover_color="gray30",
            command=self.destroy,
        )
        cancel_btn.pack(side="right")

    def _browse_media(self, col_name: str):
        filetypes = [
            ("All Supported Media", "*.mp4;*.mov;*.mkv;*.jpg;*.jpeg;*.png;*.pdf"),
            ("Video Files", "*.mp4;*.mov;*.mkv"),
            ("Images", "*.jpg;*.jpeg;*.png"),
            ("PDF Documents", "*.pdf"),
            ("All Files", "*.*"),
        ]
        selected = filedialog.askopenfilename(title="Pilih File Media", filetypes=filetypes)
        if selected:
            self.entries[col_name].delete(0, "end")
            self.entries[col_name].insert(0, selected)

    def _save_changes(self):
        updated = dict(self.row_dict)
        for col, widget in self.entries.items():
            if isinstance(widget, ctk.CTkEntry):
                updated[col] = widget.get().strip()
            elif isinstance(widget, ctk.CTkOptionMenu):
                updated[col] = widget.get().strip()

        if hasattr(self, "desc_textbox"):
            updated["description"] = self.desc_textbox.get("1.0", "end-1c").strip()

        if updated.get("status") == "success" and not updated.get("posted_at"):
            updated["posted_at"] = datetime.now().isoformat()

        self.on_save_callback(updated)
        self.destroy()


class AutoPostingGUI(ctk.CTk):
    def __init__(self, initial_csv: Optional[str] = None):
        super().__init__()

        self.title("Auto-Posting Bot & Keyword Intelligence")
        self.geometry("1060x760")
        self.minsize(920, 680)

        # Thread-safe UI dispatch queue
        self.ui_queue: queue.Queue = queue.Queue()
        self._start_ui_queue_poll()

        # State tracking
        self.is_posting_running = False
        self.stop_requested = False
        self.posting_thread: Optional[threading.Thread] = None

        # Data buffers for CSV Manager (Tab 1)
        self.active_csv_path: Optional[Path] = None
        self.active_csv_fieldnames: List[str] = []
        self.active_csv_rows: List[dict] = []
        self.filtered_csv_rows: List[tuple] = []
        self.custom_poster_csv: Optional[Path] = None

        # Data buffers for Keyword Scraper
        self.all_keywords: List[dict] = []
        self.filtered_keywords: List[dict] = []
        self.last_scraped_csv: Optional[Path] = None

        self._build_header()
        self._build_tabs()
        self._apply_treeview_theme("Dark")
        self._check_chrome_status_async()

        # Auto-load target CSV if provided via Open With, CLI argument, or default
        target_csv = initial_csv
        if not target_csv and len(sys.argv) > 1 and sys.argv[1].endswith(".csv"):
            target_csv = sys.argv[1]

        if target_csv and Path(target_csv).exists():
            self.load_csv_file(Path(target_csv))
            self.tabview.set("📊 CSV Manager & Progres")
        elif YOUTUBE_CSV.exists():
            self.load_csv_file(YOUTUBE_CSV)

    def _start_ui_queue_poll(self):
        """Memproses event queue di main thread secara berkala agar 100% aman."""
        try:
            while not self.ui_queue.empty():
                callback, args, kwargs = self.ui_queue.get_nowait()
                try:
                    callback(*args, **kwargs)
                except Exception as ex:
                    print(f"Error executing queued UI callback: {ex}", file=sys.stderr)
        except Exception:
            pass
        self.after(30, self._start_ui_queue_poll)

    def dispatch_to_main(self, callback, *args, **kwargs):
        """Thread-safe dispatch: antrikan fungsi untuk dieksekusi di main UI thread."""
        self.ui_queue.put((callback, args, kwargs))

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        # Title & Subtitle (Left)
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)

        title_lbl = ctk.CTkLabel(
            title_box,
            text="🚀 AUTO-POSTING BOT & KEYWORD INTELLIGENCE",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            title_box,
            text="Carousell Marketplace • YouTube Studio • Issuu PDF Publisher",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        sub_lbl.pack(anchor="w")

        # Controls Box (Right)
        ctrl_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        ctrl_box.pack(side="right", padx=15, pady=10)

        # 1. Theme Switcher
        theme_box = ctk.CTkFrame(ctrl_box, fg_color="transparent")
        theme_box.pack(side="left", padx=(0, 15))

        ctk.CTkLabel(theme_box, text="Tema:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 6))
        self.theme_menu = ctk.CTkSegmentedButton(
            theme_box,
            values=["Dark", "Light", "System"],
            command=self._change_appearance_mode,
            height=28,
        )
        self.theme_menu.set("Dark")
        self.theme_menu.pack(side="left")

        # 2. Quick Chrome Status Badge
        self.chrome_status_lbl = ctk.CTkLabel(
            ctrl_box,
            text="● Chrome: Memeriksa...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="orange",
        )
        self.chrome_status_lbl.pack(side="left", padx=(0, 10))

        self.launch_chrome_btn = ctk.CTkButton(
            ctrl_box,
            text="Buka Profil Chrome",
            width=140,
            command=self._launch_chrome_profile,
        )
        self.launch_chrome_btn.pack(side="left")

    def _change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)
        self._apply_treeview_theme(new_mode)

    def _apply_treeview_theme(self, mode: str = "Dark"):
        """Sinkronisasi visual warna ttk.Treeview dengan tema CustomTkinter."""
        effective_mode = mode
        if mode == "System":
            try:
                import darkdetect
                effective_mode = "Dark" if darkdetect.isDark() else "Light"
            except Exception:
                effective_mode = "Dark"

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        if effective_mode == "Light":
            bg_color = "#ffffff"
            fg_color = "#111827"
            field_bg = "#ffffff"
            heading_bg = "#e5e7eb"
            heading_fg = "#111827"
            select_bg = "#2563eb"
            row_alt = "#f9fafb"
        else:
            bg_color = "#1f2937"
            fg_color = "#f9fafb"
            field_bg = "#1f2937"
            heading_bg = "#111827"
            heading_fg = "#93c5fd"
            select_bg = "#1d4ed8"
            row_alt = "#111827"

        style.configure(
            "Custom.Treeview",
            background=bg_color,
            foreground=fg_color,
            fieldbackground=field_bg,
            rowheight=26,
            font=("Segoe UI" if sys.platform.startswith("win") else "Ubuntu", 10),
            borderwidth=0,
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=heading_bg,
            foreground=heading_fg,
            font=("Segoe UI" if sys.platform.startswith("win") else "Ubuntu", 10, "bold"),
            relief="flat",
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", select_bg)],
            foreground=[("selected", "#ffffff")],
        )

        if hasattr(self, "keyword_tree"):
            self.keyword_tree.tag_configure("evenrow", background=bg_color)
            self.keyword_tree.tag_configure("oddrow", background=row_alt)
        if hasattr(self, "tabs_tree"):
            self.tabs_tree.tag_configure("evenrow", background=bg_color)
            self.tabs_tree.tag_configure("oddrow", background=row_alt)
        if hasattr(self, "csv_tree"):
            self.csv_tree.tag_configure("evenrow", background=bg_color)
            self.csv_tree.tag_configure("oddrow", background=row_alt)
            self.csv_tree.tag_configure("row_success", foreground="#22c55e")
            self.csv_tree.tag_configure("row_failed", foreground="#ef4444")
            self.csv_tree.tag_configure("row_pending", foreground="#f59e0b")
            self.csv_tree.tag_configure("row_skipped", foreground="#9ca3af")

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tab_csv = self.tabview.add("📊 CSV Manager & Progres")
        self.tab_poster = self.tabview.add("🤖 Bot Auto-Posting")
        self.tab_scraper = self.tabview.add("🔍 Riset Kata Kunci")
        self.tab_builder = self.tabview.add("📝 Template Builder")
        self.tab_browser = self.tabview.add("🌐 Browser Profile Controller")

        self._setup_csv_manager_tab()
        self._setup_poster_tab()
        self._setup_scraper_tab()
        self._setup_builder_tab()
        self._setup_browser_tab()

    # =========================================================================
    # TAB 1: CSV MANAGER, PREVIEW, PROGRESS & EDITOR
    # =========================================================================
    def _setup_csv_manager_tab(self):
        tab = self.tab_csv

        # 1. Header Card (File info & Top Actions)
        top_frame = ctk.CTkFrame(tab)
        top_frame.pack(fill="x", padx=15, pady=(10, 6))

        # File & Platform Information (Left)
        f_info_box = ctk.CTkFrame(top_frame, fg_color="transparent")
        f_info_box.pack(side="left", padx=10, pady=8)

        f_title_row = ctk.CTkFrame(f_info_box, fg_color="transparent")
        f_title_row.pack(anchor="w")

        self.csv_file_lbl = ctk.CTkLabel(
            f_title_row,
            text="File CSV: Memuat...",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.csv_file_lbl.pack(side="left", padx=(0, 10))

        self.csv_platform_badge = ctk.CTkLabel(
            f_title_row,
            text="🎬 YouTube",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1e3a8a",
            text_color="#93c5fd",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        self.csv_platform_badge.pack(side="left")

        self.csv_path_detail_lbl = ctk.CTkLabel(
            f_info_box,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
        )
        self.csv_path_detail_lbl.pack(anchor="w", pady=(2, 0))

        # File Actions (Right)
        f_act_box = ctk.CTkFrame(top_frame, fg_color="transparent")
        f_act_box.pack(side="right", padx=10, pady=8)

        ctk.CTkButton(
            f_act_box,
            text="📂 Buka CSV...",
            width=120,
            command=self._choose_and_load_csv,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            f_act_box,
            text="🔄 Reload",
            width=80,
            command=self._reload_active_csv,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            f_act_box,
            text="💾 Simpan CSV",
            width=110,
            fg_color="#047857",
            hover_color="#065f46",
            command=self._save_active_csv,
        ).pack(side="left", padx=4)

        # 2. Progress & Statistics Card
        prog_card = ctk.CTkFrame(tab)
        prog_card.pack(fill="x", padx=15, pady=(0, 6))

        # Metrics Row
        stat_row = ctk.CTkFrame(prog_card, fg_color="transparent")
        stat_row.pack(fill="x", padx=10, pady=(8, 4))

        self.stat_box_total = self._create_stat_badge(stat_row, "TOTAL BARIS", "0", "#3b82f6")
        self.stat_box_total.pack(side="left", fill="x", expand=True, padx=4)

        self.stat_box_success = self._create_stat_badge(stat_row, "✅ SUKSES", "0", "#22c55e")
        self.stat_box_success.pack(side="left", fill="x", expand=True, padx=4)

        self.stat_box_pending = self._create_stat_badge(stat_row, "⏳ PENDING", "0", "#eab308")
        self.stat_box_pending.pack(side="left", fill="x", expand=True, padx=4)

        self.stat_box_failed = self._create_stat_badge(stat_row, "❌ GAGAL", "0", "#ef4444")
        self.stat_box_failed.pack(side="left", fill="x", expand=True, padx=4)

        self.stat_box_skipped = self._create_stat_badge(stat_row, "⏭️ DILEWATI", "0", "#9ca3af")
        self.stat_box_skipped.pack(side="left", fill="x", expand=True, padx=4)

        # Progress bar
        self.csv_mgr_progress_bar = ctk.CTkProgressBar(prog_card, height=12)
        self.csv_mgr_progress_bar.set(0)
        self.csv_mgr_progress_bar.pack(fill="x", padx=15, pady=(4, 4))

        self.csv_progress_lbl = ctk.CTkLabel(
            prog_card,
            text="Progres antrian sedang dihitung...",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.csv_progress_lbl.pack(anchor="w", padx=15, pady=(0, 8))

        # 3. Action Toolbar (Resume, Edit, Filter, Search)
        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.pack(fill="x", padx=15, pady=(0, 6))

        # Top Action Row
        t_row1 = ctk.CTkFrame(toolbar, fg_color="transparent")
        t_row1.pack(fill="x", pady=(0, 4))

        self.resume_btn = ctk.CTkButton(
            t_row1,
            text="▶ LANJUTKAN POSTING DARI FILE INI",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#15803d",
            hover_color="#166534",
            height=34,
            command=self._resume_posting_from_csv,
        )
        self.resume_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            t_row1,
            text="✏️ Edit Baris",
            width=100,
            height=34,
            command=self._edit_selected_row,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            t_row1,
            text="🔄 Reset Gagal",
            width=110,
            height=34,
            fg_color="#b45309",
            hover_color="#92400e",
            command=self._reset_failed_rows,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            t_row1,
            text="🌐 Buka URL",
            width=100,
            height=34,
            command=self._open_selected_post_url,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            t_row1,
            text="➕ Tambah",
            width=85,
            height=34,
            command=self._add_new_row,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            t_row1,
            text="🗑 Hapus",
            width=85,
            height=34,
            fg_color="#991b1b",
            hover_color="#7f1d1d",
            command=self._delete_selected_row,
        ).pack(side="left", padx=4)

        # Filter & Search Row
        t_row2 = ctk.CTkFrame(toolbar, fg_color="transparent")
        t_row2.pack(fill="x")

        self.csv_search_entry = ctk.CTkEntry(
            t_row2,
            placeholder_text="🔍 Cari kata kunci / judul postingan...",
            width=340,
            height=30,
        )
        self.csv_search_entry.pack(side="left", padx=(0, 8))
        self.csv_search_entry.bind("<KeyRelease>", lambda e: self._filter_csv_table())

        self.csv_filter_opt = ctk.CTkOptionMenu(
            t_row2,
            values=["Semua Status", "Pending", "Success", "Failed", "Skipped"],
            width=135,
            height=30,
            command=lambda _: self._filter_csv_table(),
        )
        self.csv_filter_opt.set("Semua Status")
        self.csv_filter_opt.pack(side="left", padx=(0, 10))

        self.csv_table_count_lbl = ctk.CTkLabel(
            t_row2,
            text="Menampilkan 0 baris",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        self.csv_table_count_lbl.pack(side="right")

        # 4. Preview Table (Treeview with Scrollbars)
        table_container = ctk.CTkFrame(tab)
        table_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        cols = ("no", "status", "title", "media", "info", "url", "posted_at", "error")
        self.csv_tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse",
        )

        self.csv_tree.heading("no", text="#")
        self.csv_tree.heading("status", text="Status")
        self.csv_tree.heading("title", text="Judul Postingan")
        self.csv_tree.heading("media", text="File Media")
        self.csv_tree.heading("info", text="Visibilitas / Info")
        self.csv_tree.heading("url", text="URL Postingan (Live Link)")
        self.csv_tree.heading("posted_at", text="Waktu Posting")
        self.csv_tree.heading("error", text="Pesan Error")

        self.csv_tree.column("no", width=45, anchor="center")
        self.csv_tree.column("status", width=95, anchor="center")
        self.csv_tree.column("title", width=280, anchor="w")
        self.csv_tree.column("media", width=140, anchor="w")
        self.csv_tree.column("info", width=110, anchor="center")
        self.csv_tree.column("url", width=180, anchor="w")
        self.csv_tree.column("posted_at", width=140, anchor="center")
        self.csv_tree.column("error", width=160, anchor="w")

        v_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.csv_tree.yview)
        h_scroll = ttk.Scrollbar(table_container, orient="horizontal", command=self.csv_tree.xview)
        self.csv_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.csv_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.csv_tree.bind("<Double-1>", lambda e: self._edit_selected_row())
        self.csv_tree.bind("<Button-3>", self._show_csv_context_menu)
        if sys.platform == "darwin":
            self.csv_tree.bind("<Button-2>", self._show_csv_context_menu)

    def _create_stat_badge(self, parent, label: str, val: str, color: str):
        box = ctk.CTkFrame(parent, corner_radius=6)
        lbl = ctk.CTkLabel(box, text=label, font=ctk.CTkFont(size=10, weight="bold"), text_color="gray70")
        lbl.pack(pady=(4, 0))
        val_lbl = ctk.CTkLabel(box, text=val, font=ctk.CTkFont(size=16, weight="bold"), text_color=color)
        val_lbl.pack(pady=(0, 4))
        box.val_lbl = val_lbl
        return box

    def load_csv_file(self, filepath: Path):
        """Membaca dan memuat file CSV ke antarmuka CSV Manager."""
        if not filepath.exists():
            messagebox.showerror("Error", f"File {filepath} tidak ditemukan!")
            return

        fieldnames, rows = read_csv_data(filepath)
        self.active_csv_path = filepath
        self.active_csv_fieldnames = fieldnames
        self.active_csv_rows = rows

        # Deteksi Platform
        plat = detect_platform_from_fieldnames(fieldnames)
        badge_colors = {
            "YouTube": ("#1e3a8a", "#93c5fd", "🎬 YouTube"),
            "Carousell": ("#831843", "#fbcfe8", "🛍️ Carousell"),
            "Issuu": ("#14532d", "#bbf7d0", "📄 Issuu"),
        }
        bg_c, fg_c, text_tag = badge_colors.get(plat, ("#374151", "#d1d5db", "📋 Umum"))
        if hasattr(self, "csv_platform_badge"):
            self.csv_platform_badge.configure(text=text_tag, fg_color=bg_c, text_color=fg_c)

        if hasattr(self, "csv_file_lbl"):
            self.csv_file_lbl.configure(text=f"File CSV: {filepath.name}")
        if hasattr(self, "csv_path_detail_lbl"):
            self.csv_path_detail_lbl.configure(text=str(filepath))

        self._update_csv_progress_ui()
        self._filter_csv_table()

    def _choose_and_load_csv(self):
        filetypes = [("CSV Files", "*.csv"), ("All Files", "*.*")]
        chosen = filedialog.askopenfilename(
            title="Pilih File CSV Antrian",
            initialdir=str(DATA_DIR),
            filetypes=filetypes,
        )
        if chosen:
            self.load_csv_file(Path(chosen))

    def _reload_active_csv(self):
        if self.active_csv_path and self.active_csv_path.exists():
            self.load_csv_file(self.active_csv_path)
            messagebox.showinfo("Sukses", f"Data dari {self.active_csv_path.name} berhasil dimuat ulang!")
        else:
            messagebox.showwarning("Peringatan", "Belum ada file CSV yang aktif.")

    def _reload_active_csv_quietly(self):
        """Reload tanpa popup dialog (dipanggil oleh thread bot posting saat live update)."""
        if self.active_csv_path and self.active_csv_path.exists():
            fieldnames, rows = read_csv_data(self.active_csv_path)
            self.active_csv_fieldnames = fieldnames
            self.active_csv_rows = rows
            self._update_csv_progress_ui()
            self._filter_csv_table()

    def _save_active_csv(self):
        if not self.active_csv_path:
            messagebox.showwarning("Peringatan", "Belum ada file CSV yang aktif untuk disimpan.")
            return

        ok = save_csv_data(self.active_csv_path, self.active_csv_fieldnames, self.active_csv_rows)
        if ok:
            messagebox.showinfo("Sukses", f"Perubahan berhasil disimpan ke {self.active_csv_path.name}!")
        else:
            messagebox.showerror("Error", f"Gagal menyimpan ke {self.active_csv_path.name}!")

    def _update_csv_progress_ui(self):
        if not hasattr(self, "stat_box_total"):
            return

        stats = get_csv_progress_stats(self.active_csv_rows)
        self.stat_box_total.val_lbl.configure(text=str(stats["total"]))
        self.stat_box_success.val_lbl.configure(text=str(stats["success"]))
        self.stat_box_pending.val_lbl.configure(text=str(stats["pending"]))
        self.stat_box_failed.val_lbl.configure(text=str(stats["failed"]))
        self.stat_box_skipped.val_lbl.configure(text=str(stats["skipped"]))

        frac = (stats["percentage"] / 100.0) if stats["total"] > 0 else 0.0
        self.csv_mgr_progress_bar.set(frac)

        next_idx_str = f"baris ke-{stats['next_pending_index'] + 1}" if stats["next_pending_index"] is not None else "Semua telah selesai"
        self.csv_progress_lbl.configure(
            text=f"Progres: {stats['success']} / {stats['total']} Selesai ({stats['percentage']}%) • "
                 f"{stats['pending']} Pending • {stats['failed']} Gagal • Siap melanjutkan dari: {next_idx_str}"
        )

    def _filter_csv_table(self):
        if not hasattr(self, "csv_tree"):
            return

        query = self.csv_search_entry.get().strip().lower()
        filter_st = self.csv_filter_opt.get().strip().lower()

        for item in self.csv_tree.get_children():
            self.csv_tree.delete(item)

        matched_count = 0
        self.filtered_csv_rows = []

        for orig_idx, row in enumerate(self.active_csv_rows):
            status = row.get("status", "pending").strip().lower()
            title = row.get("title", "").strip()

            # Status filter
            if filter_st != "semua status":
                if filter_st == "pending" and status not in ["", "pending"]:
                    continue
                elif filter_st == "success" and status not in ["success", "done", "posted"]:
                    continue
                elif filter_st == "failed" and status not in ["failed", "gagal", "error"]:
                    continue
                elif filter_st == "skipped" and status not in ["skip", "skipped", "lewati"]:
                    continue

            # Search query filter
            if query and query not in title.lower() and query not in row.get("tags", "").lower():
                continue

            # Determine media col
            media = row.get("video_path") or row.get("photos") or row.get("file_path") or ""
            media_name = Path(media).name if media else "-"

            # Determine info col
            info = row.get("visibility") or (f"Rp {row.get('price')}" if row.get("price") else "-")

            url = row.get("post_url", "")
            posted_at = row.get("posted_at", "")[:19].replace("T", " ") if row.get("posted_at") else "-"
            err = row.get("error_msg", "")[:60]

            tag = "evenrow" if orig_idx % 2 == 0 else "oddrow"
            status_tag = "row_pending"
            if status in ["success", "done", "posted"]:
                status_tag = "row_success"
            elif status in ["failed", "gagal", "error"]:
                status_tag = "row_failed"
            elif status in ["skip", "skipped", "lewati"]:
                status_tag = "row_skipped"

            self.csv_tree.insert(
                "",
                "end",
                values=(orig_idx + 1, status.upper() or "PENDING", title, media_name, info, url, posted_at, err),
                tags=(tag, status_tag),
            )
            self.filtered_csv_rows.append((orig_idx, row))
            matched_count += 1

        self.csv_table_count_lbl.configure(text=f"Menampilkan {matched_count} dari {len(self.active_csv_rows)} baris")

    def _resume_posting_from_csv(self):
        if not self.active_csv_path or not self.active_csv_path.exists():
            messagebox.showerror("Error", "Belum ada file CSV yang dibuka!")
            return

        pending = get_pending_rows(self.active_csv_rows)
        if not pending:
            messagebox.showinfo(
                "Semua Selesai",
                "Semua postingan di file CSV ini sudah berstatus 'success'!\n"
                "Jika ingin memposting ulang, gunakan tombol 'Edit Baris' atau ubah status ke 'pending'."
            )
            return

        detected_plat = detect_platform_from_fieldnames(self.active_csv_fieldnames)
        self.custom_poster_csv = self.active_csv_path

        # Switch to Bot Runner
        self.tabview.set("🤖 Bot Auto-Posting")
        self.poster_platform_var.set(detected_plat)
        self._on_poster_platform_change(detected_plat)

        first_pending_num = pending[0][0] + 1
        self.log(f"Memuat file CSV: {self.active_csv_path.name}")
        self.log(f"Platform: {detected_plat} | Siap melanjutkan posting dari baris ke-{first_pending_num} (Total pending: {len(pending)}).")

    def _edit_selected_row(self):
        sel = self.csv_tree.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Silakan klik salah satu baris di tabel terlebih dahulu.")
            return

        item = self.csv_tree.item(sel[0])
        row_num = item["values"][0]
        orig_idx = int(row_num) - 1

        if 0 <= orig_idx < len(self.active_csv_rows):
            target_row = self.active_csv_rows[orig_idx]

            def on_save(updated_row):
                self.active_csv_rows[orig_idx] = updated_row
                save_csv_data(self.active_csv_path, self.active_csv_fieldnames, self.active_csv_rows)
                self._update_csv_progress_ui()
                self._filter_csv_table()
                messagebox.showinfo("Sukses", f"Baris ke-{row_num} berhasil diperbarui!")

            EditRowDialog(self, target_row, self.active_csv_fieldnames, on_save)

    def _reset_failed_rows(self):
        if not self.active_csv_rows:
            return

        reset_count = 0
        for r in self.active_csv_rows:
            if r.get("status", "").strip().lower() in ["failed", "gagal", "error"]:
                r["status"] = "pending"
                r["error_msg"] = ""
                reset_count += 1

        if reset_count > 0:
            save_csv_data(self.active_csv_path, self.active_csv_fieldnames, self.active_csv_rows)
            self._update_csv_progress_ui()
            self._filter_csv_table()
            messagebox.showinfo("Reset Berhasil", f"Sebanyak {reset_count} baris berstatus gagal telah direset ke 'pending'!")
        else:
            messagebox.showinfo("Info", "Tidak ada baris yang berstatus gagal pada file CSV ini.")

    def _open_selected_post_url(self):
        sel = self.csv_tree.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih baris postingan terlebih dahulu.")
            return

        item = self.csv_tree.item(sel[0])
        url = str(item["values"][5]).strip()
        if url and url.startswith("http"):
            webbrowser.open(url)
        else:
            messagebox.showinfo("Belum Ada Link", "Baris ini belum memiliki URL postingan resmi (masih pending atau gagal).")

    def _add_new_row(self):
        if not self.active_csv_path:
            messagebox.showwarning("Peringatan", "Buka file CSV terlebih dahulu.")
            return

        new_row = {k: "" for k in self.active_csv_fieldnames}
        new_row["status"] = "pending"
        if "visibility" in self.active_csv_fieldnames:
            new_row["visibility"] = "Public"
        if "made_for_kids" in self.active_csv_fieldnames:
            new_row["made_for_kids"] = "false"

        def on_save(saved_row):
            self.active_csv_rows.append(saved_row)
            save_csv_data(self.active_csv_path, self.active_csv_fieldnames, self.active_csv_rows)
            self._update_csv_progress_ui()
            self._filter_csv_table()
            messagebox.showinfo("Sukses", "Baris baru berhasil ditambahkan!")

        EditRowDialog(self, new_row, self.active_csv_fieldnames, on_save)

    def _delete_selected_row(self):
        sel = self.csv_tree.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih baris yang ingin dihapus.")
            return

        item = self.csv_tree.item(sel[0])
        row_num = item["values"][0]
        orig_idx = int(row_num) - 1

        if 0 <= orig_idx < len(self.active_csv_rows):
            title = self.active_csv_rows[orig_idx].get("title", f"Baris #{row_num}")
            if messagebox.askyesno("Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus baris ke-{row_num}:\n'{title}'?"):
                del self.active_csv_rows[orig_idx]
                save_csv_data(self.active_csv_path, self.active_csv_fieldnames, self.active_csv_rows)
                self._update_csv_progress_ui()
                self._filter_csv_table()

    def _show_csv_context_menu(self, event):
        row_id = self.csv_tree.identify_row(event.y)
        if row_id:
            self.csv_tree.selection_set(row_id)
            import tkinter as tk
            m = tk.Menu(self, tearoff=0)
            m.add_command(label="✏️ Edit Baris Ini", command=self._edit_selected_row)
            m.add_command(label="🌐 Buka URL Postingan", command=self._open_selected_post_url)
            m.add_separator()
            m.add_command(label="🔄 Ubah Status ke Pending", command=lambda: self._quick_set_status(row_id, "pending"))
            m.add_command(label="⏭️ Lewati Baris Ini (Skip)", command=lambda: self._quick_set_status(row_id, "skipped"))
            m.add_separator()
            m.add_command(label="🗑 Hapus Baris", command=self._delete_selected_row)
            try:
                m.tk_popup(event.x_root, event.y_root)
            finally:
                m.grab_release()

    def _quick_set_status(self, row_id, new_status: str):
        item = self.csv_tree.item(row_id)
        row_num = item["values"][0]
        orig_idx = int(row_num) - 1
        if 0 <= orig_idx < len(self.active_csv_rows):
            self.active_csv_rows[orig_idx]["status"] = new_status
            if new_status == "pending":
                self.active_csv_rows[orig_idx]["error_msg"] = ""
            save_csv_data(self.active_csv_path, self.active_csv_fieldnames, self.active_csv_rows)
            self._update_csv_progress_ui()
            self._filter_csv_table()

    # =========================================================================
    # TAB 1: RISET KATA KUNCI (GOOGLE SUGGEST)
    # =========================================================================
    def _setup_scraper_tab(self):
        tab = self.tab_scraper

        # 1. Input Frame
        input_frame = ctk.CTkFrame(tab)
        input_frame.pack(fill="x", padx=15, pady=10)

        lbl = ctk.CTkLabel(input_frame, text="Kata Kunci Utama (Seed Keyword):", font=ctk.CTkFont(weight="bold"))
        lbl.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")

        self.seed_entry = ctk.CTkEntry(input_frame, placeholder_text="Contoh: pupuk sawit", width=380)
        self.seed_entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        self.scrape_btn = ctk.CTkButton(
            input_frame,
            text="⚡ Scrape Google Suggest (Alphabet Soup)",
            font=ctk.CTkFont(weight="bold"),
            command=self._run_keyword_scraper,
        )
        self.scrape_btn.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="w")

        # 2. Status & Filter Toolbar
        filter_bar = ctk.CTkFrame(tab, fg_color="transparent")
        filter_bar.pack(fill="x", padx=15, pady=(0, 6))

        self.scraper_info_lbl = ctk.CTkLabel(
            filter_bar,
            text="Masukkan kata kunci induk lalu klik Scrape untuk mengambil turunan A-Z dan 0-9.",
            text_color="gray70",
        )
        self.scraper_info_lbl.pack(side="left", padx=5)

        # Search & Category Filters (Right)
        filter_ctrls = ctk.CTkFrame(filter_bar, fg_color="transparent")
        filter_ctrls.pack(side="right")

        self.keyword_search_entry = ctk.CTkEntry(filter_ctrls, placeholder_text="🔍 Cari kata kunci...", width=180)
        self.keyword_search_entry.pack(side="left", padx=5)
        self.keyword_search_entry.bind("<KeyRelease>", lambda e: self._apply_keyword_filter())

        self.category_filter_opt = ctk.CTkOptionMenu(
            filter_ctrls,
            values=["Semua Kategori", "Root", "Alphabet (A-Z)", "Angka (0-9)", "Modifier Komersial"],
            width=150,
            command=lambda _: self._apply_keyword_filter(),
        )
        self.category_filter_opt.pack(side="left", padx=5)

        self.reset_filter_btn = ctk.CTkButton(
            filter_ctrls,
            text="Reset",
            width=60,
            fg_color="gray40",
            hover_color="gray30",
            command=self._reset_keyword_filter,
        )
        self.reset_filter_btn.pack(side="left", padx=(0, 5))

        self.table_count_lbl = ctk.CTkLabel(filter_ctrls, text="0 baris", font=ctk.CTkFont(weight="bold"))
        self.table_count_lbl.pack(side="left", padx=5)

        # 3. Visual Table Area (ttk.Treeview inside CTkFrame)
        table_frame = ctk.CTkFrame(tab)
        table_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        columns = ("no", "keyword", "category", "time")
        self.keyword_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Custom.Treeview",
        )
        self.keyword_tree.heading("no", text="#", anchor="center")
        self.keyword_tree.heading("keyword", text="Kata Kunci Google Suggest", anchor="w")
        self.keyword_tree.heading("category", text="Kategori / Tipe", anchor="center")
        self.keyword_tree.heading("time", text="Waktu Scraping", anchor="center")

        self.keyword_tree.column("no", width=55, minwidth=40, anchor="center")
        self.keyword_tree.column("keyword", width=420, minwidth=250, anchor="w")
        self.keyword_tree.column("category", width=160, minwidth=120, anchor="center")
        self.keyword_tree.column("time", width=140, minwidth=100, anchor="center")

        tree_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.keyword_tree.yview)
        self.keyword_tree.configure(yscrollcommand=tree_scrollbar.set)

        self.keyword_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # 4. Action Buttons (Bottom)
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.export_csv_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Ekspor CSV (Auto-Pipe ke Tab 2)",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#15803d",
            hover_color="#166534",
            state="disabled",
            command=self._export_keywords_csv,
        )
        self.export_csv_btn.pack(side="left", padx=5)

        self.open_csv_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Buka Folder Hasil CSV",
            command=lambda: self._open_folder(KEYWORDS_DIR),
            state="disabled",
        )
        self.open_csv_btn.pack(side="left", padx=5)

        self.copy_keywords_btn = ctk.CTkButton(
            btn_frame,
            text="📋 Salin Semua Kata Kunci",
            state="disabled",
            command=self._copy_keywords_to_clipboard,
        )
        self.copy_keywords_btn.pack(side="left", padx=5)

    def _populate_keyword_tree(self, items: List[dict]):
        """Memperbarui isi tabel Treeview dengan styling baris berselang."""
        for row in self.keyword_tree.get_children():
            self.keyword_tree.delete(row)

        for i, item in enumerate(items, 1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            time_str = item.get("scraped_at", "")
            if "T" in time_str:
                time_str = time_str.split("T")[1][:8]

            self.keyword_tree.insert(
                "",
                "end",
                values=(i, item.get("keyword", ""), item.get("category_type", ""), time_str),
                tags=(tag,),
            )
        self.table_count_lbl.configure(text=f"{len(items)} / {len(self.all_keywords)} baris")

    def _apply_keyword_filter(self):
        query = self.keyword_search_entry.get().strip().lower()
        selected_cat = self.category_filter_opt.get()

        filtered = []
        for item in self.all_keywords:
            kw = item.get("keyword", "").lower()
            cat = item.get("category_type", "").lower()

            # Search match
            if query and query not in kw:
                continue

            # Category match
            if selected_cat == "Root" and cat != "root":
                continue
            elif selected_cat == "Alphabet (A-Z)" and not cat.startswith("alphabet"):
                continue
            elif selected_cat == "Angka (0-9)" and not cat.startswith("number"):
                continue
            elif selected_cat == "Modifier Komersial" and not cat.startswith("modifier"):
                continue

            filtered.append(item)

        self.filtered_keywords = filtered
        self._populate_keyword_tree(filtered)

    def _reset_keyword_filter(self):
        self.keyword_search_entry.delete(0, "end")
        self.category_filter_opt.set("Semua Kategori")
        self.filtered_keywords = list(self.all_keywords)
        self._populate_keyword_tree(self.all_keywords)

    def _export_keywords_csv(self):
        data_to_save = self.filtered_keywords if self.filtered_keywords else self.all_keywords
        if not data_to_save:
            messagebox.showwarning("Peringatan", "Belum ada data kata kunci untuk diekspor.")
            return

        seed = self.seed_entry.get().strip() or "hasil"
        seed_slug = seed.lower().replace(" ", "_")
        default_name = f"keywords_{seed_slug}.csv"

        out_file = filedialog.asksaveasfilename(
            initialdir=str(KEYWORDS_DIR),
            initialfile=default_name,
            title="Simpan File CSV Kata Kunci",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not out_file:
            return

        target_path = Path(out_file)
        write_new_csv(target_path, ["keyword", "seed", "category_type", "scraped_at"], data_to_save)

        # Auto-pipe to Tab 2
        self.builder_input_entry.delete(0, "end")
        self.builder_input_entry.insert(0, str(target_path))
        self.last_scraped_csv = target_path

        should_switch = messagebox.askyesno(
            "Ekspor Sukses & Pipa Tab 2",
            f"Berhasil mengekspor {len(data_to_save)} kata kunci ke:\n{target_path.name}\n\n"
            "Path file telah otomatis dimasukkan ke Tab 2 (Template Builder).\n"
            "Apakah Anda ingin beralih ke Tab 2 sekarang?",
        )
        if should_switch:
            self.tabview.set("📝 Template Builder")

    def _copy_keywords_to_clipboard(self):
        data = self.filtered_keywords if self.filtered_keywords else self.all_keywords
        if not data:
            return
        text = "\n".join(item["keyword"] for item in data)
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Tersalin", f"{len(data)} kata kunci berhasil disalin ke clipboard!")

    def _run_keyword_scraper(self):
        seed = self.seed_entry.get().strip()
        if not seed:
            messagebox.showwarning("Peringatan", "Silakan masukkan kata kunci utama terlebih dahulu.")
            return

        self.scrape_btn.configure(state="disabled", text="Sedang Scraping Google...")
        self.scraper_info_lbl.configure(text=f"Sedang mengumpulkan saran kata kunci untuk '{seed}'...")

        def task():
            try:
                results = scrape_alphabet_soup(seed, lang="id", country="id")
                out_slug = seed.lower().replace(" ", "_")
                out_path = KEYWORDS_DIR / f"keywords_{out_slug}.csv"

                write_new_csv(out_path, ["keyword", "seed", "category_type", "scraped_at"], results)

                self.dispatch_to_main(self._on_scraper_success, seed, results, out_path)
            except Exception as e:
                self.dispatch_to_main(self._on_scraper_error, str(e))

        threading.Thread(target=task, daemon=True).start()

    def _on_scraper_success(self, seed: str, results: list, out_path: Path):
        self.scrape_btn.configure(state="normal", text="⚡ Scrape Google Suggest (Alphabet Soup)")
        self.open_csv_btn.configure(state="normal")
        self.export_csv_btn.configure(state="normal")
        self.copy_keywords_btn.configure(state="normal")
        self.last_scraped_csv = out_path

        self.all_keywords = results
        self.filtered_keywords = list(results)
        self._populate_keyword_tree(results)

        self.scraper_info_lbl.configure(
            text=f"✅ Selesai! Ditemukan {len(results)} kata kunci unik. Tersimpan di: {out_path.name}"
        )

        # Auto-fill path in Tab 2
        self.builder_input_entry.delete(0, "end")
        self.builder_input_entry.insert(0, str(out_path))

    def _on_scraper_error(self, err_msg: str):
        self.scrape_btn.configure(state="normal", text="⚡ Scrape Google Suggest (Alphabet Soup)")
        self.scraper_info_lbl.configure(text="❌ Terjadi kesalahan saat scraping.")
        messagebox.showerror("Error", f"Gagal mengambil kata kunci: {err_msg}")

    # =========================================================================
    # TAB 2: TEMPLATE BUILDER
    # =========================================================================
    def _setup_builder_tab(self):
        tab = self.tab_builder

        frame = ctk.CTkScrollableFrame(tab)
        frame.pack(fill="both", expand=True, padx=15, pady=10)

        # 1. Input CSV Kata Kunci
        ctk.CTkLabel(frame, text="1. File CSV Kata Kunci Sumber:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        f_box = ctk.CTkFrame(frame, fg_color="transparent")
        f_box.pack(fill="x", pady=(0, 10))

        self.builder_input_entry = ctk.CTkEntry(f_box, placeholder_text="Pilih file keywords_*.csv")
        self.builder_input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(f_box, text="Pilih File...", width=100, command=self._select_keywords_csv).pack(side="left")

        # 2. Platform Target
        ctk.CTkLabel(frame, text="2. Platform Target:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.builder_platform_var = ctk.StringVar(value="Carousell")
        self.platform_seg = ctk.CTkSegmentedButton(
            frame,
            values=["Carousell", "YouTube", "Issuu"],
            variable=self.builder_platform_var,
            command=self._on_builder_platform_change,
        )
        self.platform_seg.pack(anchor="w", pady=(0, 10))

        # 3. Template Judul
        ctk.CTkLabel(frame, text="3. Template Judul (Gunakan {keyword} atau {keyword_title}):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.builder_title_entry = ctk.CTkEntry(frame, width=600)
        self.builder_title_entry.insert(0, "Jual {keyword_title} Berkualitas Terbaik")
        self.builder_title_entry.pack(anchor="w", fill="x", pady=(0, 10))

        # 4. Template Deskripsi
        ctk.CTkLabel(frame, text="4. Template Deskripsi:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.builder_desc_entry = ctk.CTkEntry(frame, width=600)
        self.builder_desc_entry.insert(0, "Pusat distributor {keyword_title} resmi. Pemesanan hubungi WA: 081234567890")
        self.builder_desc_entry.pack(anchor="w", fill="x", pady=(0, 10))

        # 5. File Media (Gambar / Video / PDF)
        self.builder_media_label = ctk.CTkLabel(frame, text="5. File Gambar Produk (Carousell):", font=ctk.CTkFont(weight="bold"))
        self.builder_media_label.pack(anchor="w", pady=(5, 2))

        m_box = ctk.CTkFrame(frame, fg_color="transparent")
        m_box.pack(fill="x", pady=(0, 10))

        self.builder_media_entry = ctk.CTkEntry(m_box, placeholder_text="Path file media...")
        self.builder_media_entry.insert(0, str(ASSETS_DIR / "images" / "sample_pupuk.jpg"))
        self.builder_media_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(m_box, text="Pilih Media...", width=100, command=self._select_media_file).pack(side="left")

        # 6. Parameter Spesifik Platform (Harga untuk Carousell, dsb)
        self.builder_extra_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.builder_extra_frame.pack(fill="x", pady=(0, 15))

        self.price_label = ctk.CTkLabel(self.builder_extra_frame, text="Harga (Rp):", font=ctk.CTkFont(weight="bold"))
        self.price_label.pack(side="left", padx=(0, 10))

        self.price_entry = ctk.CTkEntry(self.builder_extra_frame, width=120)
        self.price_entry.insert(0, "150000")
        self.price_entry.pack(side="left", padx=(0, 20))

        self.condition_label = ctk.CTkLabel(self.builder_extra_frame, text="Kondisi:", font=ctk.CTkFont(weight="bold"))
        self.condition_label.pack(side="left", padx=(0, 10))

        self.condition_option = ctk.CTkOptionMenu(self.builder_extra_frame, values=["Baru", "Bekas"])
        self.condition_option.pack(side="left")

        # Tombol Eksekusi
        self.generate_csv_btn = ctk.CTkButton(
            tab,
            text="✨ Generate File CSV Siap Posting",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            command=self._generate_platform_csv,
        )
        self.generate_csv_btn.pack(fill="x", padx=15, pady=(5, 10))

    def _on_builder_platform_change(self, value: str):
        if value == "Carousell":
            self.builder_title_entry.delete(0, "end")
            self.builder_title_entry.insert(0, "Jual {keyword_title} Berkualitas Terbaik")
            self.builder_media_label.configure(text="5. File Gambar Produk (Carousell):")
            self.builder_media_entry.delete(0, "end")
            self.builder_media_entry.insert(0, str(ASSETS_DIR / "images" / "sample_pupuk.jpg"))
            self.builder_extra_frame.pack(fill="x", pady=(0, 15))
        elif value == "YouTube":
            self.builder_title_entry.delete(0, "end")
            self.builder_title_entry.insert(0, "Rahasia {keyword_title} Hasil Panen Melimpah")
            self.builder_media_label.configure(text="5. File Video (.mp4):")
            self.builder_media_entry.delete(0, "end")
            self.builder_media_entry.insert(0, str(ASSETS_DIR / "videos" / "sample_sawit_15s.mp4"))
            self.builder_extra_frame.pack_forget()
        elif value == "Issuu":
            self.builder_title_entry.delete(0, "end")
            self.builder_title_entry.insert(0, "Katalog Resmi {keyword_title} 2026")
            self.builder_media_label.configure(text="5. File Dokumen (.pdf):")
            self.builder_media_entry.delete(0, "end")
            self.builder_media_entry.insert(0, str(ASSETS_DIR / "docs" / "sample_katalog.pdf"))
            self.builder_extra_frame.pack_forget()

    def _select_keywords_csv(self):
        f = filedialog.askopenfilename(
            initialdir=str(KEYWORDS_DIR),
            title="Pilih File CSV Kata Kunci",
            filetypes=[("CSV Files", "*.csv")],
        )
        if f:
            self.builder_input_entry.delete(0, "end")
            self.builder_input_entry.insert(0, f)

    def _select_media_file(self):
        plat = self.builder_platform_var.get()
        if plat == "Carousell":
            types = [("Image Files", "*.jpg;*.png;*.jpeg;*.webp")]
        elif plat == "YouTube":
            types = [("Video Files", "*.mp4;*.mov;*.mkv")]
        else:
            types = [("PDF Documents", "*.pdf")]

        f = filedialog.askopenfilename(initialdir=str(ASSETS_DIR), title="Pilih File Media", filetypes=types)
        if f:
            self.builder_media_entry.delete(0, "end")
            self.builder_media_entry.insert(0, f)

    def _generate_platform_csv(self):
        in_file = Path(self.builder_input_entry.get().strip())
        if not in_file.exists():
            messagebox.showerror("Error", f"File kata kunci tidak ditemukan: {in_file}")
            return

        plat = self.builder_platform_var.get().lower()
        title_tmpl = self.builder_title_entry.get().strip()
        desc_tmpl = self.builder_desc_entry.get().strip()
        media_p = self.builder_media_entry.get().strip()

        if plat == "carousell":
            out_p = CAROUSELL_CSV
            build_carousell_csv(
                input_file=in_file,
                output_file=out_p,
                title_template=title_tmpl,
                price=self.price_entry.get().strip(),
                condition=self.condition_option.get(),
                desc_template=desc_tmpl,
                image_paths=media_p,
                category="Gardening",
            )
        elif plat == "youtube":
            out_p = YOUTUBE_CSV
            build_youtube_csv(
                input_file=in_file,
                output_file=out_p,
                title_template=title_tmpl,
                desc_template=desc_tmpl,
                video_path=media_p,
                tags="pupuk sawit, pertanian, perkebunan",
                visibility="Public",
                made_for_kids="false",
            )
        else:
            out_p = ISSUU_CSV
            build_issuu_csv(
                input_file=in_file,
                output_file=out_p,
                title_template=title_tmpl,
                desc_template=desc_tmpl,
                pdf_path=media_p,
            )

        messagebox.showinfo("Sukses", f"Berhasil membuat file antrian posting:\n{out_p}\n\nAnda dapat menjalankannya di Tab Bot Auto-Posting.")
        self.poster_platform_seg.set(self.builder_platform_var.get())
        self._on_poster_platform_change(self.builder_platform_var.get())

    # =========================================================================
    # TAB 3: BOT AUTO-POSTING & LIVE MONITOR
    # =========================================================================
    def _setup_poster_tab(self):
        tab = self.tab_poster

        # Top Control Frame
        ctrl_frame = ctk.CTkFrame(tab)
        ctrl_frame.pack(fill="x", padx=15, pady=10)

        # Platform selector
        ctk.CTkLabel(ctrl_frame, text="Platform:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.poster_platform_var = ctk.StringVar(value="YouTube")
        self.poster_platform_seg = ctk.CTkSegmentedButton(
            ctrl_frame,
            values=["YouTube", "Carousell", "Issuu"],
            variable=self.poster_platform_var,
            command=self._on_poster_platform_change,
        )
        self.poster_platform_seg.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        # Max posts
        ctk.CTkLabel(ctrl_frame, text="Maksimal Postingan:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=10, pady=8, sticky="w")
        self.max_posts_entry = ctk.CTkEntry(ctrl_frame, width=70)
        self.max_posts_entry.insert(0, "3")
        self.max_posts_entry.grid(row=0, column=3, padx=5, pady=8, sticky="w")
        ctk.CTkLabel(ctrl_frame, text="(0 = Semua pending)", text_color="gray70").grid(row=0, column=4, padx=5, pady=8, sticky="w")

        # Delays
        ctk.CTkLabel(ctrl_frame, text="Jeda Acak (detik):", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=8, sticky="w")
        d_box = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        d_box.grid(row=1, column=1, padx=10, pady=8, sticky="w")

        self.min_delay_entry = ctk.CTkEntry(d_box, width=50)
        self.min_delay_entry.insert(0, str(MIN_POST_DELAY))
        self.min_delay_entry.pack(side="left")

        ctk.CTkLabel(d_box, text=" s/d ").pack(side="left", padx=5)

        self.max_delay_entry = ctk.CTkEntry(d_box, width=50)
        self.max_delay_entry.insert(0, str(MAX_POST_DELAY))
        self.max_delay_entry.pack(side="left")

        # Dry Run Checkbox
        self.dry_run_var = ctk.BooleanVar(value=False)
        self.dry_run_check = ctk.CTkCheckBox(ctrl_frame, text="Dry-Run (Hanya uji coba form tanpa terbit final)", variable=self.dry_run_var)
        self.dry_run_check.grid(row=1, column=2, columnspan=2, padx=10, pady=8, sticky="w")

        # CSV Source Indicator Row
        src_box = ctk.CTkFrame(tab, fg_color="transparent")
        src_box.pack(fill="x", padx=15, pady=(2, 6))

        self.poster_source_lbl = ctk.CTkLabel(
            src_box,
            text="File Antrian: Default YouTube (data/youtube_posts.csv)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93c5fd",
        )
        self.poster_source_lbl.pack(side="left")

        ctk.CTkButton(
            src_box,
            text="Ganti File CSV...",
            width=120,
            height=26,
            command=self._choose_poster_csv,
        ).pack(side="right")

        # Action Buttons
        act_box = ctk.CTkFrame(tab, fg_color="transparent")
        act_box.pack(fill="x", padx=15, pady=(0, 5))

        self.start_btn = ctk.CTkButton(
            act_box,
            text="▶ MULAI POSTING OTOMATIS",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#15803d",
            hover_color="#166534",
            height=38,
            command=self._start_posting,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # BUGFIX: width=120 placed directly in constructor, NOT inside pack()
        self.stop_btn = ctk.CTkButton(
            act_box,
            text="⏹ STOP",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#b91c1c",
            hover_color="#991b1b",
            width=120,
            height=38,
            state="disabled",
            command=self._stop_posting,
        )
        self.stop_btn.pack(side="left")

        # Progress bar & status
        p_frame = ctk.CTkFrame(tab, fg_color="transparent")
        p_frame.pack(fill="x", padx=15, pady=(5, 5))

        self.queue_status_lbl = ctk.CTkLabel(p_frame, text="Antrian: Memeriksa file CSV...", font=ctk.CTkFont(weight="bold"))
        self.queue_status_lbl.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(tab)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 8))

        # Live Console Output Box
        self.console_box = ctk.CTkTextbox(tab, wrap="word", font=("Courier", 11))
        self.console_box.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._on_poster_platform_change("YouTube")

    def _choose_poster_csv(self):
        filetypes = [("CSV Files", "*.csv"), ("All Files", "*.*")]
        chosen = filedialog.askopenfilename(
            title="Pilih File CSV Antrian",
            initialdir=str(DATA_DIR),
            filetypes=filetypes,
        )
        if chosen:
            p = Path(chosen)
            self.custom_poster_csv = p
            fieldnames, _ = read_csv_data(p)
            plat = detect_platform_from_fieldnames(fieldnames)
            self.poster_platform_var.set(plat)
            self._on_poster_platform_change(plat)
            self.load_csv_file(p)

    def _on_poster_platform_change(self, value: str):
        if self.custom_poster_csv and self.custom_poster_csv.exists():
            csv_f = self.custom_poster_csv
            source_desc = f"Kustom: {csv_f.name}"
        else:
            if value == "Carousell":
                csv_f = CAROUSELL_CSV
            elif value == "YouTube":
                csv_f = YOUTUBE_CSV
            else:
                csv_f = ISSUU_CSV
            source_desc = f"Default: {csv_f.name}"

        if hasattr(self, "poster_source_lbl"):
            self.poster_source_lbl.configure(text=f"File Antrian: {csv_f.name} ({source_desc})")

        if csv_f.exists():
            _, rows = read_csv_data(csv_f)
            stats = get_csv_progress_stats(rows)
            self.queue_status_lbl.configure(
                text=f"Platform: {value} | {source_desc} | Total: {stats['total']} | Selesai: {stats['success']} | Pending: {stats['pending']} | Gagal: {stats['failed']}"
            )
        else:
            self.queue_status_lbl.configure(text=f"Platform: {value} | {source_desc} (Belum dibuat)")

    def log(self, msg: str):
        """Thread-safe logging to the interactive terminal console."""
        now = datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] {msg}\n"

        def _append():
            self.console_box.insert("end", line)
            self.console_box.see("end")

        self.dispatch_to_main(_append)

    def set_progress(self, fraction: float):
        """Thread-safe progress bar setter."""
        self.dispatch_to_main(lambda: self.progress_bar.set(fraction))

    def _start_posting(self):
        plat = self.poster_platform_var.get()
        if self.custom_poster_csv and self.custom_poster_csv.exists():
            csv_file = self.custom_poster_csv
        else:
            csv_file = CAROUSELL_CSV if plat == "Carousell" else (YOUTUBE_CSV if plat == "YouTube" else ISSUU_CSV)

        if not csv_file.exists():
            messagebox.showerror("Error", f"File antrian {csv_file.name} belum ada! Buat di Tab Template Builder atau pilih file CSV terlebih dahulu.")
            return

        try:
            max_posts = int(self.max_posts_entry.get().strip() or "0")
        except ValueError:
            max_posts = 0

        dry_run = self.dry_run_var.get()

        self.is_posting_running = True
        self.stop_requested = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.log(f"=== MEMULAI SESI POSTING: {plat.upper()} ===")
        self.log(f"Target CSV: {csv_file.name} | Max Posts: {max_posts or 'Semua'} | Dry-Run: {dry_run}")

        def worker():
            asyncio.run(self._async_posting_worker(plat, csv_file, max_posts, dry_run))

        self.posting_thread = threading.Thread(target=worker, daemon=True)
        self.posting_thread.start()

    def _stop_posting(self):
        if self.is_posting_running:
            self.stop_requested = True
            self.log("⚠️ Permintaan STOP diterima. Menyelesaikan postingan yang sedang berjalan...")
            self.stop_btn.configure(state="disabled")

    async def _async_posting_worker(self, platform: str, csv_path: Path, max_posts: int, dry_run: bool):
        from modules.browser_manager import BrowserManager
        bm = BrowserManager()

        try:
            self.log("Menghubungkan ke Google Chrome via Remote Debugging...")
            # Tab isolation with domain hint: preserves existing tabs without overwriting
            domain_hint = platform.lower()
            browser, page = await bm.connect(domain_hint)
            self.log(f"Berhasil menempel ke browser Chrome! Tab terisolasi untuk: {platform}")

            fieldnames, rows = read_csv_data(csv_path)
            pending = get_pending_rows(rows)

            if not pending:
                self.log("Tidak ada postingan yang berstatus pending.")
                return

            if max_posts > 0 and max_posts < len(pending):
                pending = pending[:max_posts]

            total = len(pending)
            self.log(f"Total antrian yang akan diproses: {total} item.")

            for i, (orig_idx, row) in enumerate(pending, 1):
                if self.stop_requested:
                    self.log("Proses dihentikan oleh pengguna.")
                    break

                title = row.get("title", f"Baris {orig_idx + 1}")
                self.log(f"--- [{i}/{total}] Memproses: {title[:50]} ---")
                self.set_progress(i / total)

                try:
                    if platform == "Carousell":
                        from poster_carousell import process_carousell_post
                        url = await process_carousell_post(page, row, dry_run=dry_run)
                    elif platform == "YouTube":
                        from poster_youtube import upload_youtube_video
                        url = await upload_youtube_video(page, row, dry_run=dry_run)
                    else:
                        from poster_issuu import publish_issuu_pdf
                        url = await publish_issuu_pdf(page, row, dry_run=dry_run)

                    update_row_status(csv_path, fieldnames, rows, orig_idx, "success", post_url=url)
                    self.dispatch_to_main(self._reload_active_csv_quietly)
                    self.log(f"✅ Sukses! URL: {url}")
                except Exception as e:
                    err = str(e)
                    update_row_status(csv_path, fieldnames, rows, orig_idx, "failed", error_msg=err)
                    self.dispatch_to_main(self._reload_active_csv_quietly)
                    self.log(f"❌ Gagal: {err}")

                # Jeda acak antar postingan
                if i < total and not self.stop_requested:
                    try:
                        d_min = int(self.min_delay_entry.get().strip() or "60")
                        d_max = int(self.max_delay_entry.get().strip() or "120")
                    except ValueError:
                        d_min, d_max = 60, 120

                    import random
                    wait_sec = random.randint(d_min, d_max) if d_max >= d_min else d_min
                    self.log(f"⏳ Jeda aman anti-spam: menunggu {wait_sec} detik...")
                    for s in range(wait_sec, 0, -1):
                        if self.stop_requested:
                            break
                        if s % 15 == 0 or s <= 5:
                            self.log(f"  Hitung mundur: {s}s tersisa...")
                        await asyncio.sleep(1)

            self.log("=== SESI POSTING SELESAI ===")
            await bm.disconnect()
        except (ConnectionError, RuntimeError, Exception) as e:
            self.log(f"❌ Error pada bot: {e}")
        finally:
            self.is_posting_running = False
            self.dispatch_to_main(self._on_posting_finished)

    def _on_posting_finished(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._on_poster_platform_change(self.poster_platform_var.get())
        self._reload_active_csv_quietly()

    # =========================================================================
    # TAB 4: BROWSER PROFILE CONTROLLER
    # =========================================================================
    def _setup_browser_tab(self):
        tab = self.tab_browser

        scroll_container = ctk.CTkScrollableFrame(tab)
        scroll_container.pack(fill="both", expand=True, padx=15, pady=10)

        # --- CARD 1: STATUS DASHBOARD ---
        status_card = ctk.CTkFrame(scroll_container)
        status_card.pack(fill="x", pady=(0, 12), padx=5)

        c_head = ctk.CTkFrame(status_card, fg_color="transparent")
        c_head.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(c_head, text="Status Koneksi Chrome CDP (Port 9222):", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        self.tab4_badge = ctk.CTkLabel(
            c_head,
            text="○ Memeriksa...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="orange",
        )
        self.tab4_badge.pack(side="left", padx=15)

        # Info details
        info_frame = ctk.CTkFrame(status_card, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.tab4_details_lbl = ctk.CTkLabel(
            info_frame,
            text="Port: 9222 | Endpoint: http://localhost:9222 | Browser: Mendeteksi...",
            font=ctk.CTkFont(family="Courier", size=11),
            text_color="gray80",
            justify="left",
        )
        self.tab4_details_lbl.pack(anchor="w")

        # Action buttons for Card 1
        act_row = ctk.CTkFrame(status_card, fg_color="transparent")
        act_row.pack(fill="x", padx=15, pady=(0, 12))

        self.tab4_launch_btn = ctk.CTkButton(
            act_row,
            text="🚀 Buka Profil Chrome (Remote Debugging)",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#1d4ed8",
            hover_color="#1e40af",
            command=self._launch_chrome_profile,
        )
        self.tab4_launch_btn.pack(side="left", padx=(0, 10))

        self.tab4_refresh_btn = ctk.CTkButton(
            act_row,
            text="🔄 Cek Ulang Koneksi & Tab",
            command=self._refresh_chrome_details_async,
        )
        self.tab4_refresh_btn.pack(side="left", padx=(0, 10))

        self.tab4_open_dir_btn = ctk.CTkButton(
            act_row,
            text="📂 Buka Folder Profil Chrome",
            command=self._open_chrome_profile_dir,
        )
        self.tab4_open_dir_btn.pack(side="left")

        # --- CARD 2: ACTIVE TABS INSPECTOR ---
        tabs_card = ctk.CTkFrame(scroll_container)
        tabs_card.pack(fill="both", expand=True, pady=(0, 12), padx=5)

        t_head = ctk.CTkFrame(tabs_card, fg_color="transparent")
        t_head.pack(fill="x", padx=15, pady=(12, 6))

        ctk.CTkLabel(t_head, text="📑 Tab Browser Aktif (Terdeteksi via Port 9222):", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self.tab4_count_lbl = ctk.CTkLabel(t_head, text="0 tab aktif", text_color="gray70")
        self.tab4_count_lbl.pack(side="left", padx=10)

        # Active Tabs Treeview
        tabs_table_frame = ctk.CTkFrame(tabs_card)
        tabs_table_frame.pack(fill="x", padx=15, pady=(0, 10))

        tab_cols = ("no", "target", "title", "url")
        self.tabs_tree = ttk.Treeview(
            tabs_table_frame,
            columns=tab_cols,
            show="headings",
            height=6,
            style="Custom.Treeview",
        )
        self.tabs_tree.heading("no", text="#", anchor="center")
        self.tabs_tree.heading("target", text="Target Platform", anchor="center")
        self.tabs_tree.heading("title", text="Judul Halaman Tab", anchor="w")
        self.tabs_tree.heading("url", text="URL Tab", anchor="w")

        self.tabs_tree.column("no", width=45, minwidth=35, anchor="center")
        self.tabs_tree.column("target", width=150, minwidth=120, anchor="center")
        self.tabs_tree.column("title", width=340, minwidth=200, anchor="w")
        self.tabs_tree.column("url", width=380, minwidth=250, anchor="w")

        tabs_scroll = ttk.Scrollbar(tabs_table_frame, orient="vertical", command=self.tabs_tree.yview)
        self.tabs_tree.configure(yscrollcommand=tabs_scroll.set)

        self.tabs_tree.pack(side="left", fill="both", expand=True)
        tabs_scroll.pack(side="right", fill="y")

        # Quick Open Target URLs
        quick_bar = ctk.CTkFrame(tabs_card, fg_color="transparent")
        quick_bar.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(quick_bar, text="Pintasan Tab Cepat:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))

        ctk.CTkButton(quick_bar, text="Buka Carousell Sell", width=140, command=lambda: self._open_browser_url("https://id.carousell.com/sell/")).pack(side="left", padx=4)
        ctk.CTkButton(quick_bar, text="Buka YouTube Studio", width=140, command=lambda: self._open_browser_url("https://studio.youtube.com/")).pack(side="left", padx=4)
        ctk.CTkButton(quick_bar, text="Buka Issuu Publisher", width=140, command=lambda: self._open_browser_url("https://issuu.com/home/publisher")).pack(side="left", padx=4)

        # --- CARD 3: PANDUAN PENGGUNAAN & TROUBLESHOOTING ---
        guide_card = ctk.CTkFrame(scroll_container)
        guide_card.pack(fill="x", padx=5)

        g_head = ctk.CTkFrame(guide_card, fg_color="transparent")
        g_head.pack(fill="x", padx=15, pady=(10, 4))
        ctk.CTkLabel(g_head, text="💡 Panduan Anti-Deteksi & Pemecahan Masalah:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left")

        guide_text = (
            "1. Klik 'Buka Profil Chrome' untuk menjalankan Chrome dengan remote debugging port 9222.\n"
            "2. Lakukan login 1x pada Carousell, YouTube, dan Issuu. Profil ini menyimpan cookies & sesi Anda secara permanen.\n"
            "3. JANGAN MENUTUP jendela Chrome saat bot posting berjalan. Bot akan menempel otomatis tanpa memicu deteksi bot Cloudflare/Google.\n"
            "4. Jika port 9222 bentrok/macet, jalankan perintah ini di terminal:\n"
            "   - Linux: fuser -k 9222/tcp\n"
            "   - Windows: netstat -ano | findstr 9222 (lalu taskkill /PID <PID> /F)"
        )
        guide_lbl = ctk.CTkLabel(guide_card, text=guide_text, justify="left", font=ctk.CTkFont(size=12), text_color="gray80")
        guide_lbl.pack(anchor="w", padx=15, pady=(0, 12))

    def _open_chrome_profile_dir(self):
        if sys.platform.startswith("win"):
            profile_dir = Path(os.environ.get("USERPROFILE", Path.home())) / "ChromeBotProfile"
        else:
            profile_dir = Path.home() / ".config" / "chrome_bot_profile"
        self._open_folder(profile_dir)

    def _open_browser_url(self, url: str):
        import webbrowser
        webbrowser.open(url)

    def _refresh_chrome_details_async(self):
        def fetch():
            try:
                req_ver = urllib.request.urlopen("http://localhost:9222/json/version", timeout=1.5)
                ver_data = json.loads(req_ver.read().decode("utf-8"))

                req_list = urllib.request.urlopen("http://localhost:9222/json/list", timeout=1.5)
                list_data = json.loads(req_list.read().decode("utf-8"))
                pages = [d for d in list_data if d.get("type") == "page"]

                self.dispatch_to_main(self._on_chrome_details_success, ver_data, pages)
            except Exception as e:
                self.dispatch_to_main(self._on_chrome_details_offline, str(e))

        threading.Thread(target=fetch, daemon=True).start()

    def _on_chrome_details_success(self, ver_data: dict, pages: list):
        self.chrome_status_lbl.configure(text="● Chrome Online (Port 9222)", text_color="#22c55e")
        if hasattr(self, "tab4_badge"):
            self.tab4_badge.configure(text="● Online (Port 9222 Terhubung)", text_color="#22c55e")

        browser_str = ver_data.get("Browser", "Chrome")
        ua_str = ver_data.get("User-Agent", "")[:85]
        ws_str = ver_data.get("webSocketDebuggerUrl", "")

        if hasattr(self, "tab4_details_lbl"):
            self.tab4_details_lbl.configure(
                text=f"Port: 9222 | Browser: {browser_str}\n"
                     f"User-Agent: {ua_str}...\n"
                     f"WebSocket: {ws_str}"
            )

        if hasattr(self, "tabs_tree"):
            for row in self.tabs_tree.get_children():
                self.tabs_tree.delete(row)

            for i, p in enumerate(pages, 1):
                url = p.get("url", "")
                title = p.get("title", "")
                tag = "evenrow" if i % 2 == 0 else "oddrow"

                target_name = "🌐 Lainnya"
                if "carousell" in url.lower():
                    target_name = "🛍️ Carousell"
                elif "youtube" in url.lower() or "studio.youtube" in url.lower():
                    target_name = "🎬 YouTube Studio"
                elif "issuu" in url.lower():
                    target_name = "📄 Issuu Publisher"

                self.tabs_tree.insert("", "end", values=(i, target_name, title, url), tags=(tag,))

            if hasattr(self, "tab4_count_lbl"):
                self.tab4_count_lbl.configure(text=f"{len(pages)} tab aktif")

    def _on_chrome_details_offline(self, err: str):
        self.chrome_status_lbl.configure(text="○ Chrome Offline", text_color="#ef4444")
        if hasattr(self, "tab4_badge"):
            self.tab4_badge.configure(text="○ Offline (Port 9222 Tidak Terdeteksi)", text_color="#ef4444")
            self.tab4_details_lbl.configure(text="Port 9222 tidak aktif. Silakan klik 'Buka Profil Chrome' di atas.")
        if hasattr(self, "tabs_tree"):
            for row in self.tabs_tree.get_children():
                self.tabs_tree.delete(row)
        if hasattr(self, "tab4_count_lbl"):
            self.tab4_count_lbl.configure(text="0 tab aktif")

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _check_chrome_status_async(self):
        self._refresh_chrome_details_async()
        # Periksa ulang berkala setiap 5 detik
        self.after(5000, self._check_chrome_status_async)

    def _launch_chrome_profile(self):
        launcher_linux = BASE_DIR / "launchers" / "start_chrome_linux.sh"
        launcher_win = BASE_DIR / "launchers" / "start_chrome_windows.bat"

        if sys.platform.startswith("win"):
            subprocess.Popen([str(launcher_win)], shell=True)
        else:
            subprocess.Popen(["bash", str(launcher_linux)])

        self.log("Meluncurkan jendela Chrome Remote Debugging...")

    def _open_folder(self, folder_path: Path):
        folder_path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(folder_path)
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", str(folder_path)])
        else:
            subprocess.Popen(["xdg-open", str(folder_path)])


def main():
    target_csv = None
    if len(sys.argv) > 1 and sys.argv[1].endswith(".csv"):
        target_csv = sys.argv[1]
    app = AutoPostingGUI(initial_csv=target_csv)
    app.mainloop()


if __name__ == "__main__":
    main()
