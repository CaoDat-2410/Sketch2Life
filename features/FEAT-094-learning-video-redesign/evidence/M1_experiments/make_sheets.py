"""Contact sheets of the experiment videos: six frames per video, one labelled row each.

Uses the ffmpeg of the local video-worker container (the host has none). Usage:
    python make_sheets.py <video directory> <output.png> <name> [<name> ...]
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

CONTAINER = "sketch2life-video-worker-1"
SIZE = (320, 180)
POSITIONS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)


def frames_of(video: Path, count: int = 240) -> list[Image.Image]:
    wanted = "+".join(f"eq(n\\,{min(round(p * (count - 1)), count - 1)})" for p in POSITIONS)
    command = [
        "docker", "exec", "-i", CONTAINER, "sh", "-c",
        "cat > /tmp/sheet.mp4 && ffmpeg -loglevel error -i /tmp/sheet.mp4 "
        f"-vf \"select='{wanted}',scale={SIZE[0]}:{SIZE[1]},tile={len(POSITIONS)}x1\" "
        "-frames:v 1 -f image2pipe -vcodec png - ; rm -f /tmp/sheet.mp4",
    ]
    completed = subprocess.run(command, input=video.read_bytes(), capture_output=True, check=True, timeout=120)
    return [Image.open(io.BytesIO(completed.stdout)).convert("RGB")]


def main(directory: str, output: str, *names: str) -> None:
    rows = []
    for name in names:
        strip = frames_of(Path(directory) / f"{name}.mp4")[0]
        row = Image.new("RGB", (strip.width, strip.height + 22), "white")
        ImageDraw.Draw(row).text((6, 4), name, fill="black")
        row.paste(strip, (0, 22))
        rows.append(row)
    sheet = Image.new("RGB", (rows[0].width, sum(row.height + 4 for row in rows)), (90, 90, 90))
    top = 0
    for row in rows:
        sheet.paste(row, (0, top))
        top += row.height + 4
    sheet.save(output)
    print(output, sheet.size)


if __name__ == "__main__":
    main(*sys.argv[1:])
