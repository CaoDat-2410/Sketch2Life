"""Put the measured clips next to each other with their names and seconds (local ffmpeg, no GPU).

    python side_by_side.py <directory with report.json and the clips>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FONT = "C\\:/Windows/Fonts/arialbd.ttf"
ORDER = ("base", "natten", "conv_vae", "small", "fps16")


def main(directory: Path) -> None:
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    records = {
        record["name"]: record for key in ("base_image", "new_image") for record in report.get(key, {}).get("variants", [])
    }
    names = [name for name in ORDER if (directory / f"{name}-2.mp4").is_file()]
    inputs: list[str] = []
    filters: list[str] = []
    for index, name in enumerate(names):
        inputs += ["-i", str(directory / f"{name}-2.mp4")]
        seconds = records[name]["renders"][-1]["render_s"]
        label = f"{index + 1}. {name}  {seconds:.0f}s"
        filters.append(
            f"[{index}:v]scale=640:360,drawtext=fontfile='{FONT}':text='{label}':x=12:y=10:fontsize=24:"
            f"fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=6[v{index}]"
        )
    positions = [f"{(i % 2) * 640}_{(i // 2) * 360}" for i in range(len(names))]
    filters.append(
        "".join(f"[v{i}]" for i in range(len(names)))
        + f"xstack=inputs={len(names)}:layout={'|'.join(positions)}:fill=white[out]"
    )
    target = directory / "side-by-side.mp4"
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
         "-map", "[out]", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         str(target)],
        check=True,
    )
    print(target)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
