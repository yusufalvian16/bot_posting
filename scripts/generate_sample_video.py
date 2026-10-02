#!/usr/bin/env python3
"""
Reproducible Sample Video Generator for Bot-Posting
Generates 15s and 30s compliant H.264/AAC MP4 videos from sample_pupuk.jpg
"""
import subprocess
import sys
from pathlib import Path


def generate_sample_video(image_path: Path, output_path: Path, duration_seconds: int = 15):
    if not image_path.exists():
        raise FileNotFoundError(f"Source image not found: {image_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(image_path.resolve()),
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=mono:sample_rate=44100",
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "64k",
        "-t", str(duration_seconds),
        "-shortest",
        str(output_path.resolve()),
    ]

    print(f"Generating {duration_seconds}s sample video -> {output_path}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"Successfully generated: {output_path} ({output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    img = base_dir / "assets" / "images" / "sample_pupuk.jpg"
    out_15 = base_dir / "assets" / "videos" / "sample_sawit_15s.mp4"
    out_30 = base_dir / "assets" / "videos" / "sample_sawit_30s.mp4"

    generate_sample_video(img, out_15, duration_seconds=15)
    generate_sample_video(img, out_30, duration_seconds=30)
