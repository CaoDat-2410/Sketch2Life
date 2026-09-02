"""Generate synthetic MP4 fixtures for FFmpeg integration tests."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def generate_video(output: Path, duration_sec: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x176:r=8",
            "-t",
            str(duration_sec),
            "-pix_fmt",
            "yuv420p",
            str(output),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    generate_video(args.output_dir / "valid.mp4", 8)
    generate_video(args.output_dir / "short.mp4", 3)
    generate_video(args.output_dir / "long.mp4", 11)
    (args.output_dir / "corrupt.mp4").write_bytes(b"synthetic invalid mp4 fixture")
    print(f"Generated video fixtures in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
