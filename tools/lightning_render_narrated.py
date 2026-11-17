"""Local outline-tracing + color-brush preview synchronized to sentence TTS.

Raster-derived strokes, not original artist strokes or word-level semantic alignment.
No model inference or dependency installs; images and audio are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from lightning_complete_story import font


def thin(binary):
    """Zhang-Suen skeleton; array padding avoids wrapping at image borders."""
    a = np.pad(binary.astype(bool), 1)
    for _ in range(160):
        changed = False
        for step in (0, 1):
            p = [a[:-2, 1:-1], a[:-2, 2:], a[1:-1, 2:], a[2:, 2:],
                 a[2:, 1:-1], a[2:, :-2], a[1:-1, :-2], a[:-2, :-2]]
            neighbors = sum(item.astype(np.uint8) for item in p)
            transitions = sum((~p[i] & p[(i + 1) % 8]).astype(np.uint8) for i in range(8))
            if step == 0:
                guard = ~(p[0] & p[2] & p[4]) & ~(p[2] & p[4] & p[6])
            else:
                guard = ~(p[0] & p[2] & p[6]) & ~(p[0] & p[4] & p[6])
            delete = a[1:-1, 1:-1] & (neighbors >= 2) & (neighbors <= 6) & (transitions == 1) & guard
            changed |= bool(delete.any())
            a[1:-1, 1:-1][delete] = False
        if not changed:
            break
    return a[1:-1, 1:-1]


def trace_paths(binary):
    pixels = {(int(x), int(y)) for y, x in np.argwhere(thin(binary))}
    offsets = [(x, y) for y in (-1, 0, 1) for x in (-1, 0, 1) if x or y]
    adjacency = {p: [(p[0]+x, p[1]+y) for x, y in offsets if (p[0]+x, p[1]+y) in pixels]
                 for p in pixels}
    edges = set()
    paths = []
    starts = sorted(pixels, key=lambda p: (len(adjacency[p]) == 2, p[1], p[0]))
    def edge(a, b):
        return (a, b) if a < b else (b, a)
    for start in starts:
        for neighbor in adjacency[start]:
            if edge(start, neighbor) in edges:
                continue
            path = [start, neighbor]
            edges.add(edge(start, neighbor))
            current = neighbor
            while len(adjacency[current]) == 2:
                available = [p for p in adjacency[current] if edge(current, p) not in edges]
                if not available:
                    break
                nxt = available[0]
                edges.add(edge(current, nxt))
                path.append(nxt)
                current = nxt
            if len(path) > 2:
                paths.append(path)
    # Longer contours first; tiny pencil texture isn't animated as hundreds of dots.
    return sorted((p for p in paths if len(p) >= 5), key=len, reverse=True)


def color_paths(rgb):
    """Brush tracks local to color regions, not a whole-canvas horizontal wipe."""
    hi = rgb.max(axis=2).astype(float)
    lo = rgb.min(axis=2).astype(float)
    foreground = lo < 247
    chromatic = hi - lo > 35
    # Dominant hue categories only; these are NOT detected semantic objects.
    categories = rgb.argmax(axis=2) + 1
    categories[~chromatic] = 0
    paths = []
    spacing = 8
    for category in (0, 1, 2, 3):
        region = foreground & (categories == category)
        groups = []
        for y in range(0, rgb.shape[0], spacing):
            active = np.flatnonzero(region[max(0, y-4):y+5].any(axis=0))
            if not len(active):
                continue
            breaks = np.flatnonzero(np.diff(active) > 12) + 1
            for run in np.split(active, breaks):
                x1, x2 = int(run[0]), int(run[-1])
                path = [(x1, y), (x2, y)] if (y // spacing) % 2 == 0 else [(x2, y), (x1, y)]
                groups.append(path)
        paths.extend(groups)
    return paths


def commands(paths):
    return [(a, b, math.dist(a, b)) for path in paths for a, b in zip(path, path[1:])
            if a != b]


class Brush:
    def __init__(self, paths, size, width):
        self.parts = commands(paths)
        self.length = sum(item[2] for item in self.parts)
        self.index = 0
        self.done = 0.0
        self.mask = Image.new("L", size)
        self.draw = ImageDraw.Draw(self.mask)
        self.width = width

    def advance(self, progress):
        budget = min(1, max(0, progress)) * self.length
        while self.index < len(self.parts):
            a, b, distance = self.parts[self.index]
            if self.done + distance <= budget:
                self.draw.line([a, b], fill=255, width=self.width)
                self.index += 1
                self.done += distance
            else:
                fraction = max(0, (budget - self.done) / distance)
                point = (a[0]+(b[0]-a[0])*fraction, a[1]+(b[1]-a[1])*fraction)
                if fraction > 0:
                    self.draw.line([a, point], fill=255, width=self.width)
                break
        return np.asarray(self.mask) > 0


def wrap(text, draw, face, max_width):
    lines = []
    line = ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if line and draw.textlength(candidate, font=face) > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def render(scenes_dir, tts_dir, root, fps=24, size=(1280, 720)):
    import imageio_ffmpeg
    data = json.loads((tts_dir / "timeline.json").read_text(encoding="utf-8"))
    rows = data["scenes"]
    if not rows or len(rows) > 64 or [r["scene"] for r in rows] != list(range(1, len(rows)+1)):
        raise ValueError("Expected 1-64 consecutively numbered storyboard beats")
    cursor = 0.0
    for row in rows:
        if abs(row["start_seconds"] - cursor) > .02:
            raise ValueError("Storyboard audio timeline must be continuous")
        if not row["start_seconds"] < row["speech_end_seconds"] <= row["scene_end_seconds"]:
            raise ValueError("Invalid beat duration")
        cursor = row["scene_end_seconds"]
    audio_path = tts_dir / "narration.wav"
    import wave
    with wave.open(str(audio_path), "rb") as reader:
        audio_duration = reader.getnframes() / reader.getframerate()
    if abs(audio_duration - rows[-1]["scene_end_seconds"]) > .02:
        raise ValueError("Audio and timeline duration disagree")
    out = root / ".runtime/narrated-whiteboard" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    w, h = size
    small_size = (640, 300)
    silent = out / "drawing-silent.mp4"
    writer = imageio_ffmpeg.write_frames(str(silent), size, fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=1,
        output_params=["-crf", "19", "-preset", "fast"])
    writer.send(None)
    evidence = []
    frame_cursor = 0
    previous_art = None
    try:
        for row in rows:
            index = row["scene"]
            path = scenes_dir / f"scene-{index}.png"
            image = ImageOps.pad(Image.open(path).convert("RGB"), small_size,
                                 color="white", method=Image.Resampling.LANCZOS)
            rgb = np.asarray(image)
            wide_rgb = rgb.astype(np.int16)
            ink = (wide_rgb.max(axis=2) < 150) & (wide_rgb.max(axis=2)-wide_rgb.min(axis=2) < 65)
            strokes = trace_paths(ink)
            if not strokes:
                raise ValueError(f"No usable outlines recovered for scene {index}")
            line_brush = Brush(strokes, small_size, 5)
            paint_brush = Brush(color_paths(rgb), small_size, 19)
            # Final fidelity gate: brush coverage must reconstruct all visible artwork;
            # never hide incomplete coverage with a sudden final-image replacement.
            covered = paint_brush.advance(1)
            foreground = rgb.min(axis=2) < 247
            coverage = float(covered[foreground].mean()) if foreground.any() else 1
            if coverage < .999:
                raise ValueError(f"Insufficient color brush coverage {coverage:.3f} in scene {index}")
            paint_brush = Brush(color_paths(rgb), small_size, 19)
            face = font(round(w * .020))
            tag = font(round(w * .013))
            start = row["start_seconds"]
            speech_length = row["speech_end_seconds"] - start
            line_end = max(.2, speech_length * .43)
            color_end = max(line_end + .2, speech_length * .96)
            scene_end_frame = round(row["scene_end_seconds"] * fps)
            print(f"Scene {index}: {len(strokes)} outline paths; brush coverage {coverage:.3f}", flush=True)
            while frame_cursor < scene_end_frame:
                t = max(0, frame_cursor/fps - start)
                lines = line_brush.advance(t / line_end)
                colors = paint_brush.advance((t - line_end) / (color_end - line_end))
                gray = np.mean(rgb, axis=2).astype(np.uint8)
                result = np.full_like(rgb, 255)
                line_visible = lines & ink
                result[line_visible] = np.repeat(gray[..., None], 3, axis=2)[line_visible]
                result[colors] = rgb[colors]
                canvas = Image.new("RGB", size, "white")
                art = Image.fromarray(result).resize((w, h-120), Image.Resampling.LANCZOS)
                if previous_art is not None and t < .28:
                    phase = min(1, t / .28)
                    eased = phase * phase * (3 - 2 * phase)
                    offset = round(w * eased)
                    canvas.paste(previous_art, (-offset, 0))
                    canvas.paste(art, (w-offset, 0))
                else:
                    canvas.paste(art, (0, 0))
                draw = ImageDraw.Draw(canvas)
                draw.text((12, 10), f"{index}/{len(rows)} | OUTLINE + COLOR PREVIEW", font=tag, fill="#555555")
                for j, text in enumerate(wrap(row["text"], draw, face, w-80)):
                    draw.text((w//2, h-103+j*29), text, anchor="mt", font=face, fill="#222222")
                writer.send(np.asarray(canvas))
                frame_cursor += 1
            previous_art = image.resize((w, h-120), Image.Resampling.LANCZOS)
            evidence.append({"scene": index, "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                             "outline_paths": len(strokes), "color_coverage": coverage})
    finally:
        writer.close()
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
               "-i", str(silent), "-i", str(audio_path), "-map", "0:v:0", "-map", "1:a:0",
               "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
               "-movflags", "+faststart", str(out / "story-narrated.mp4")]
    subprocess.run(command, check=True)
    (out / "report.json").write_text(json.dumps({
        "duration_seconds": audio_duration, "target_35_40_met": 35 <= audio_duration <= 40,
        "scene_sources": str(scenes_dir), "tts_sources": str(tts_dir), "scenes": evidence,
        "timing": "SENTENCE_LEVEL_NOT_WORD_LEVEL", "renderer": "RASTER_DERIVED_OUTLINES_AND_BRUSH_COLOR",
        "visual_qa": "PENDING_HUMAN_REVIEW", "audio_qa": "PENDING_LISTENING_REVIEW",
        "original_artist_strokes": False, "automatic_semantic_object_alignment": False,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE: {out / 'story-narrated.mp4'}", flush=True)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenes", required=True, type=Path, help="Folder with sequential scene-N.png beat images")
    parser.add_argument("--tts", required=True, type=Path, help="Folder with narration.wav and timeline.json")
    args = parser.parse_args()
    render(args.scenes.resolve(), args.tts.resolve(), Path.cwd())


if __name__ == "__main__":
    main()
