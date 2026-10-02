#!/usr/bin/env python3
"""
Template & Data Builder Utility
Converts filtered raw keyword CSV files into platform-specific ready-to-post CSV files
(Carousell, YouTube, Issuu) with custom title patterns, descriptions, and media paths.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict

from config import DATA_DIR, CAROUSELL_CSV, YOUTUBE_CSV, ISSUU_CSV
from modules.csv_handler import read_csv_data, write_new_csv
from modules.logger import log_error, log_header, log_info, log_success, log_warn


def format_title(template: str, keyword: str) -> str:
    """
    Mengisi placeholder {keyword} atau {keyword_title} pada template judul.
    """
    clean_kw = keyword.strip()
    title_kw = clean_kw.title()
    formatted = template.replace("{keyword_title}", title_kw).replace("{keyword}", clean_kw)
    return formatted.strip()


def build_carousell_csv(
    input_file: Path,
    output_file: Path,
    title_template: str,
    price: str,
    condition: str,
    desc_template: str,
    image_paths: str,
    category: str,
):
    _, raw_rows = read_csv_data(input_file)
    if not raw_rows:
        log_error(f"Tidak ada data di {input_file}")
        return

    fieldnames = [
        "title",
        "category",
        "price",
        "condition",
        "description",
        "image_paths",
        "status",
        "post_url",
        "error_msg",
        "posted_at",
    ]
    posts = []

    for r in raw_rows:
        kw = r.get("keyword", "").strip()
        if not kw:
            continue
        title = format_title(title_template, kw)
        desc = format_title(desc_template, kw)

        posts.append({
            "title": title,
            "category": category,
            "price": price,
            "condition": condition,
            "description": desc,
            "image_paths": image_paths,
            "status": "pending",
            "post_url": "",
            "error_msg": "",
            "posted_at": "",
        })

    write_new_csv(output_file, fieldnames, posts)
    log_success(f"Berhasil membuat {len(posts)} baris untuk Carousell di: {output_file}")


def build_youtube_csv(
    input_file: Path,
    output_file: Path,
    title_template: str,
    desc_template: str,
    video_path: str,
    tags: str,
    visibility: str,
    made_for_kids: str,
):
    _, raw_rows = read_csv_data(input_file)
    if not raw_rows:
        log_error(f"Tidak ada data di {input_file}")
        return

    fieldnames = [
        "title",
        "video_path",
        "description",
        "tags",
        "visibility",
        "made_for_kids",
        "status",
        "post_url",
        "error_msg",
        "posted_at",
    ]
    posts = []

    for r in raw_rows:
        kw = r.get("keyword", "").strip()
        if not kw:
            continue
        title = format_title(title_template, kw)
        # Batasi judul YouTube maksimal 100 karakter
        if len(title) > 100:
            title = title[:97] + "..."

        desc = format_title(desc_template, kw)

        posts.append({
            "title": title,
            "video_path": video_path,
            "description": desc,
            "tags": tags,
            "visibility": visibility,
            "made_for_kids": made_for_kids,
            "status": "pending",
            "post_url": "",
            "error_msg": "",
            "posted_at": "",
        })

    write_new_csv(output_file, fieldnames, posts)
    log_success(f"Berhasil membuat {len(posts)} baris untuk YouTube di: {output_file}")


def build_issuu_csv(
    input_file: Path,
    output_file: Path,
    title_template: str,
    desc_template: str,
    pdf_path: str,
):
    _, raw_rows = read_csv_data(input_file)
    if not raw_rows:
        log_error(f"Tidak ada data di {input_file}")
        return

    fieldnames = [
        "title",
        "pdf_path",
        "description",
        "status",
        "post_url",
        "error_msg",
        "posted_at",
    ]
    posts = []

    for r in raw_rows:
        kw = r.get("keyword", "").strip()
        if not kw:
            continue
        title = format_title(title_template, kw)
        desc = format_title(desc_template, kw)

        posts.append({
            "title": title,
            "pdf_path": pdf_path,
            "description": desc,
            "status": "pending",
            "post_url": "",
            "error_msg": "",
            "posted_at": "",
        })

    write_new_csv(output_file, fieldnames, posts)
    log_success(f"Berhasil membuat {len(posts)} baris untuk Issuu di: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Template & Data Builder: Ubah kata kunci mentah menjadi file CSV siap posting platform."
    )
    parser.add_argument(
        "--platform",
        "-p",
        choices=["carousell", "youtube", "issuu"],
        help="Target platform postingan",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        help="Path file CSV kata kunci (misal: data/keywords_raw/keywords_pupuk_sawit.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Path file output CSV (default: sesuai platform di folder data/)",
    )
    parser.add_argument(
        "--title-template",
        "-t",
        type=str,
        default="Jual {keyword_title} Murah Berkualitas",
        help="Pola judul. Gunakan {keyword} atau {keyword_title}. Contoh: 'Jual {keyword_title}'",
    )
    parser.add_argument(
        "--desc-template",
        "-d",
        type=str,
        default="Informasi dan pemesanan {keyword_title} hubungi kontak kami.",
        help="Pola deskripsi teks.",
    )
    parser.add_argument(
        "--media",
        "-m",
        type=str,
        default="",
        help="Path file media (gambar / video / pdf)",
    )
    parser.add_argument(
        "--price",
        type=str,
        default="150000",
        help="Harga produk (khusus Carousell)",
    )
    parser.add_argument(
        "--condition",
        type=str,
        default="Baru",
        help="Kondisi barang (khusus Carousell)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="",
        help="Kategori (khusus Carousell)",
    )
    parser.add_argument(
        "--visibility",
        type=str,
        default="Public",
        choices=["Public", "Unlisted", "Draft"],
        help="Visibilitas video (khusus YouTube)",
    )

    args = parser.parse_args()

    # Mode interaktif jika tanpa argumen lengkap
    platform = args.platform
    input_file = args.input

    if not platform or not input_file:
        log_header("Template Builder Interaktif")
        if not input_file:
            # Cari file kata kunci yang ada
            kw_files = list(Path("data/keywords_raw").glob("*.csv"))
            if kw_files:
                print("\nFile kata kunci ditemukan:")
                for i, kf in enumerate(kw_files, 1):
                    print(f" [{i}] {kf.name}")
                choice = input("\nPilih nomor file atau ketik path file: ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(kw_files):
                    input_file = str(kw_files[int(choice) - 1])
                else:
                    input_file = choice
            else:
                input_file = input("Masukkan path file CSV kata kunci: ").strip()

        if not platform:
            print("\nPilih Platform Target:")
            print(" [1] Carousell (carousell_posts.csv)")
            print(" [2] YouTube (youtube_posts.csv)")
            print(" [3] Issuu (issuu_posts.csv)")
            p_choice = input("Pilihan (1/2/3): ").strip()
            if p_choice == "1":
                platform = "carousell"
            elif p_choice == "2":
                platform = "youtube"
            elif p_choice == "3":
                platform = "issuu"
            else:
                log_error("Pilihan platform tidak valid.")
                sys.exit(1)

    in_path = Path(input_file)
    if not in_path.exists():
        log_error(f"File {in_path} tidak ditemukan!")
        sys.exit(1)

    # Eksekusi sesuai platform
    if platform == "carousell":
        out_path = Path(args.output) if args.output else CAROUSELL_CSV
        build_carousell_csv(
            input_file=in_path,
            output_file=out_path,
            title_template=args.title_template,
            price=args.price,
            condition=args.condition,
            desc_template=args.desc_template,
            image_paths=args.media or "assets/images/sample.jpg",
            category=args.category,
        )
    elif platform == "youtube":
        out_path = Path(args.output) if args.output else YOUTUBE_CSV
        build_youtube_csv(
            input_file=in_path,
            output_file=out_path,
            title_template=args.title_template,
            desc_template=args.desc_template,
            video_path=args.media or "assets/videos/sample.mp4",
            tags="pupuk sawit, pertanian, perkebunan",
            visibility=args.visibility,
            made_for_kids="false",
        )
    elif platform == "issuu":
        out_path = Path(args.output) if args.output else ISSUU_CSV
        build_issuu_csv(
            input_file=in_path,
            output_file=out_path,
            title_template=args.title_template,
            desc_template=args.desc_template,
            pdf_path=args.media or "assets/docs/sample.pdf",
        )


if __name__ == "__main__":
    main()
