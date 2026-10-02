#!/usr/bin/env python3
"""
Generate 10 distinct sample MP4 videos for Bot-Posting testing.
Each video has unique background colors, titles, and 10s duration.
"""

import subprocess
import sys
from pathlib import Path

SAMPLE_DATA = [
    ("video_1.mp4", "0x0f172a", "Video 1: Rahasia Pupuk Sawit Unggul"),
    ("video_2.mp4", "0x064e3b", "Video 2: Cara Pemupukan Sawit Baru Tanam"),
    ("video_3.mp4", "0x1e1b4b", "Video 3: Dosis Pupuk Sawit Umur 3 Tahun"),
    ("video_4.mp4", "0x450a0a", "Video 4: Pupuk Sawit Agar Buah Lebat"),
    ("video_5.mp4", "0x134e4a", "Video 5: Perawatan Sawit di Lahan Gambut"),
    ("video_6.mp4", "0x3b0764", "Video 6: Pupuk NPK Terbaik Untuk Sawit"),
    ("video_7.mp4", "0x1c1917", "Video 7: Jadwal Pemupukan Sawit Rutin"),
    ("video_8.mp4", "0x1e3a8a", "Video 8: Solusi Daun Sawit Sehat Hijau"),
    ("video_9.mp4", "0x365314", "Video 9: Meningkatkan Bobot Buah Sawit"),
    ("video_10.mp4", "0x4c0519", "Video 10: Distributor Pupuk Sawit Resmi"),
]


def create_sample_videos():
    base_dir = Path(__file__).resolve().parent.parent
    target_dir = base_dir / "assets" / "videos" / "samples_10"
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎬 Membuat 10 video sampel di: {target_dir}")

    for idx, (filename, color, title) in enumerate(SAMPLE_DATA, 1):
        out_path = target_dir / filename
        duration = 10  # 10 detik

        # Escape single quotes and colons for ffmpeg drawtext filter
        safe_title = title.replace(":", "\\:").replace("'", "")
        vf_filter = (
            f"drawtext=text='{safe_title}':fontsize=42:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-30,"
            f"drawtext=text='Sample Video Bot-Posting • 10 Detik':fontsize=24:fontcolor=0xcccccc:x=(w-text_w)/2:y=(h-text_h)/2+40"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s=1280x720:d={duration}",
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
            "-vf", vf_filter,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "64k",
            "-t", str(duration),
            "-shortest",
            str(out_path.resolve()),
        ]

        print(f"[{idx}/10] Menghasilkan {filename} ({title})...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"❌ Error pada {filename}:\n{res.stderr}", file=sys.stderr)
            sys.exit(res.returncode)

        size_kb = round(out_path.stat().st_size / 1024, 1)
        print(f"    ✅ Selesai: {out_path.name} ({size_kb} KB)")

    print(f"\n🎉 Seluruh 10 video sampel berhasil dibuat di:\n{target_dir.resolve()}\n")


if __name__ == "__main__":
    create_sample_videos()
