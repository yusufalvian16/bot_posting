"""
Safe and atomic CSV reader and writer module.
Handles UTF-8 BOM (Windows Excel compatibility), row status updates, and progress persistence.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from modules.logger import log_error, log_info, log_warn


def read_csv_data(filepath: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Membaca file CSV dengan aman, mendukung UTF-8 dan UTF-8-SIG (format Excel Windows).
    Mengembalikan (fieldnames, rows).
    """
    if not filepath.exists():
        log_warn(f"File CSV {filepath} belum ada.")
        return [], []

    try:
        with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            rows = [dict(row) for row in reader]
            return list(fieldnames), rows
    except Exception as e:
        log_error(f"Gagal membaca CSV {filepath}: {e}")
        return [], []


def get_pending_rows(rows: List[Dict[str, str]]) -> List[Tuple[int, Dict[str, str]]]:
    """
    Mengambil baris yang belum selesai diposting:
    status kosong (''), 'pending', atau 'failed'.
    Mengembalikan list tuple (index_baris_asli, row_dict).
    """
    pending = []
    for idx, row in enumerate(rows):
        status = row.get("status", "").strip().lower()
        if status not in ["success", "done", "posted"]:
            pending.append((idx, row))
    return pending


def update_row_status(
    filepath: Path,
    fieldnames: List[str],
    rows: List[Dict[str, str]],
    row_index: int,
    status: str,
    post_url: str = "",
    error_msg: str = "",
):
    """
    Memperbarui status baris tertentu secara atomik di file CSV.
    """
    # Pastikan kolom status, post_url, error_msg, posted_at ada di header
    required_cols = ["status", "post_url", "error_msg", "posted_at"]
    for col in required_cols:
        if col not in fieldnames:
            fieldnames.append(col)

    if 0 <= row_index < len(rows):
        rows[row_index]["status"] = status
        if post_url:
            rows[row_index]["post_url"] = post_url
        if error_msg:
            rows[row_index]["error_msg"] = error_msg
        rows[row_index]["posted_at"] = datetime.now().isoformat()

    # Tulis ulang file CSV secara aman
    temp_path = filepath.with_suffix(".tmp")
    try:
        with open(temp_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                # Pastikan semua field ada
                clean_r = {k: r.get(k, "") for k in fieldnames}
                writer.writerow(clean_r)
        temp_path.replace(filepath)
    except Exception as e:
        log_error(f"Gagal memperbarui file CSV {filepath}: {e}")
        if temp_path.exists():
            temp_path.unlink()


def write_new_csv(filepath: Path, fieldnames: List[str], rows: List[Dict[str, str]]):
    """
    Membuat file CSV baru lengkap dengan header.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log_info(f"Berhasil menyimpan {len(rows)} baris ke {filepath}")


def save_csv_data(filepath: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> bool:
    """
    Menyimpan seluruh baris ke file CSV dengan atomic temporary file replacement dan UTF-8 BOM untuk Excel Windows.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    temp_path = filepath.with_suffix(".tmp")
    try:
        with open(temp_path, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                clean_r = {k: r.get(k, "") for k in fieldnames}
                writer.writerow(clean_r)
        temp_path.replace(filepath)
        log_info(f"Berhasil menyimpan {len(rows)} baris ke {filepath.name}")
        return True
    except Exception as e:
        log_error(f"Gagal menyimpan CSV {filepath}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        return False


def detect_platform_from_fieldnames(fieldnames: List[str]) -> str:
    """
    Mendeteksi jenis platform bot otomatis berdasarkan kolom header CSV.
    """
    cols = [c.lower().strip() for c in fieldnames]
    if any(k in cols for k in ["video_path", "made_for_kids"]):
        return "YouTube"
    elif any(k in cols for k in ["price", "condition", "photos", "photo_path"]):
        return "Carousell"
    elif any(k in cols for k in ["file_path", "preview_page", "issuu"]):
        return "Issuu"
    return "YouTube"


def get_csv_progress_stats(rows: List[Dict[str, str]]) -> Dict[str, any]:
    """
    Menganalisis status antrian CSV secara mendalam:
    Total, Sukses, Pending, Gagal, Dilewati, Persentase, dan baris pending berikutnya.
    """
    total = len(rows)
    success = 0
    pending = 0
    failed = 0
    skipped = 0
    next_pending_idx = None

    for idx, r in enumerate(rows):
        st = r.get("status", "").strip().lower()
        if st in ["success", "done", "posted"]:
            success += 1
        elif st in ["failed", "gagal", "error"]:
            failed += 1
        elif st in ["skip", "skipped", "lewati"]:
            skipped += 1
        else:
            pending += 1
            if next_pending_idx is None:
                next_pending_idx = idx

    pct = (success / total * 100) if total > 0 else 0.0
    return {
        "total": total,
        "success": success,
        "pending": pending,
        "failed": failed,
        "skipped": skipped,
        "percentage": round(pct, 1),
        "next_pending_index": next_pending_idx,
    }


def natural_sort_key(s: any) -> list:
    """
    Key untuk pengurutan alami (natural sort).
    Misal: 'video 2.mp4' akan berada sebelum 'video 10.mp4'.
    """
    import re
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]


def scan_media_files_in_dir(folder_path: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Memindai file media dalam sebuah folder dan mengurutkannya secara alami.
    Default ekstensi: .mp4, .mov, .mkv, .webm, .avi, .m4v.
    """
    if not extensions:
        extensions = [".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"]
    exts = {e.lower() if e.startswith(".") else f".{e.lower()}" for e in extensions}

    p = Path(folder_path)
    if not p.is_dir():
        return []

    found = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in exts]
    found.sort(key=lambda x: natural_sort_key(x.name))
    return found


def write_canva_csv(filepath: Path, keywords: List[str]):
    """
    Membuat file CSV 1-kolom khusus untuk fitur 'Bulk Create' (Buat Banyak) Canva.
    Format:
    Kata Kunci
    keyword 1
    keyword 2
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Kata Kunci"])
        for kw in keywords:
            clean = str(kw).strip()
            if clean:
                writer.writerow([clean])
    log_info(f"Berhasil mengekspor {len(keywords)} kata kunci untuk Canva di: {filepath}")


