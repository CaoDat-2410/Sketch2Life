"""Owner-operated media-only smoke test for a LOCAL Lightning provider.

This is NOT the approved session/story job. Use only a synthetic drawing and
non-child story text. It runs provider TTS, image, stroke scene and MP4 assembly
without fabricating Gate B or claiming product acceptance.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def _preview_contact_sheet(
    source: Path, scenes: tuple[dict[str, Any], ...], illustrations: list[dict[str, Any]]
) -> Path:
    """Put the source and all generated scenes side by side for visual review."""

    from PIL import Image, ImageDraw, ImageOps

    tiles = [("SOURCE", source, ())] + [
        (f"SCENE {index}", Path(str(item["asset_ref"])), scene.get("draw_cues", ()))
        for index, (scene, item) in enumerate(zip(scenes, illustrations, strict=True), 1)
    ]
    tile_width, tile_height = 420, 290
    image_height = 250
    columns = 3
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), "white")
    draw = ImageDraw.Draw(sheet)
    for tile_index, (label, path, cues) in enumerate(tiles):
        origin_x = (tile_index % columns) * tile_width
        origin_y = (tile_index // columns) * tile_height
        with Image.open(path) as opened:
            if opened.width * opened.height > 20_000_000:
                raise ValueError(f"{label} image exceeds preview pixel limit")
            fitted = ImageOps.contain(ImageOps.exif_transpose(opened).convert("RGB"),
                                      (tile_width - 20, image_height))
        x = origin_x + (tile_width - fitted.width) // 2
        y = origin_y + 28 + (image_height - fitted.height) // 2
        sheet.paste(fitted, (x, y))
        draw.text((origin_x + 10, origin_y + 8), label, fill=(20, 20, 20))
        for cue_index, cue in enumerate(cues, 1):
            left, top, right, bottom = cue["focus_box"]
            draw.rectangle(
                (x + left * fitted.width, y + top * fitted.height,
                 x + right * fitted.width, y + bottom * fitted.height),
                outline=(230, 70, 25), width=2,
            )
            draw.text((x + left * fitted.width + 2, y + top * fitted.height + 2),
                      str(cue_index), fill=(230, 70, 25))
    output_dir = Path(tempfile.mkdtemp(prefix="sketch2life-scene-preview-"))
    output = output_dir / "contact-sheet.png"
    sheet.save(output)
    return output


def _caption_chunks(text: str) -> tuple[str, ...]:
    chunks: list[str] = []
    current: list[str] = []
    for word in text.split():
        if len(word) > 62:
            raise ValueError("a caption word exceeds 62 characters")
        if current and len(" ".join((*current, word))) > 62:
            chunks.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        chunks.append(" ".join(current))
    if not 1 <= len(chunks) <= 4:
        raise ValueError("each scene needs one to four short caption chunks")
    return tuple(chunks)


def load_fixture(path: Path) -> tuple[Path, str, tuple[dict[str, Any], ...]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"source_image", "locale", "scenes"}:
        raise ValueError("fixture needs only source_image, locale and scenes")
    source_value = raw["source_image"]
    locale = raw["locale"]
    scenes = raw["scenes"]
    if not isinstance(source_value, str) or not source_value:
        raise ValueError("source_image must be a local image path")
    source = (path.parent / source_value).resolve()
    if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("source_image must be PNG, JPEG or WebP")
    if not source.is_file() or not 0 < source.stat().st_size <= 10 * 1024 * 1024:
        raise ValueError("source_image must exist and be at most 10 MiB")
    try:
        from PIL import Image

        with Image.open(source) as image:
            image.verify()
    except (ImportError, OSError, ValueError) as error:
        raise ValueError("source_image cannot be decoded as an image") from error
    if not isinstance(locale, str) or not 2 <= len(locale) <= 20:
        raise ValueError("locale must be 2-20 characters")
    if not isinstance(scenes, list) or not 3 <= len(scenes) <= 6:
        raise ValueError("fixture needs three to six scenes")
    parsed: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or not {"text", "visual_prompt"}.issubset(scene) or (
            set(scene) - {"text", "visual_prompt", "focus_box", "draw_cues"}
        ):
            raise ValueError(f"scene {index} needs text, visual_prompt and optional visual cues")
        text = scene["text"]
        prompt = scene["visual_prompt"]
        if not isinstance(text, str) or not text.strip() or len(text) > 1600:
            raise ValueError(f"scene {index} text is invalid")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000:
            raise ValueError(f"scene {index} visual_prompt is invalid")
        _caption_chunks(text)
        parsed_scene: dict[str, Any] = {"text": text.strip(), "visual_prompt": prompt.strip()}
        if "focus_box" in scene:
            box = scene["focus_box"]
            if (
                not isinstance(box, list)
                or len(box) != 4
                or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in box)
            ):
                raise ValueError(f"scene {index} focus_box must have four numbers")
            left, top, right, bottom = (float(value) for value in box)
            if not (
                0 <= left < right <= 1
                and 0 <= top < bottom <= 1
                and right - left >= 0.1
                and bottom - top >= 0.1
            ):
                raise ValueError(f"scene {index} focus_box is outside the source image")
            parsed_scene["focus_box"] = [left, top, right, bottom]
        if "draw_cues" in scene:
            cues = scene["draw_cues"]
            if not isinstance(cues, list) or not 1 <= len(cues) <= 4:
                raise ValueError(f"scene {index} draw_cues must contain one to four elements")
            seen_ids: set[str] = set()
            parsed_cues = []
            for cue in cues:
                if not isinstance(cue, dict) or set(cue) != {"element_id", "label", "focus_box"}:
                    raise ValueError(f"scene {index} draw cue fields are invalid")
                element_id, label, box = cue["element_id"], cue["label"], cue["focus_box"]
                if not isinstance(element_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", element_id):
                    raise ValueError(f"scene {index} draw cue ID is invalid")
                if element_id in seen_ids or not isinstance(label, str) or not 1 <= len(label) <= 100:
                    raise ValueError(f"scene {index} draw cue label or ID is invalid")
                if not isinstance(box, list) or len(box) != 4 or any(
                    isinstance(value, bool) or not isinstance(value, (int, float)) for value in box
                ):
                    raise ValueError(f"scene {index} draw cue box is invalid")
                left, top, right, bottom = (float(value) for value in box)
                if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
                    raise ValueError(f"scene {index} draw cue box is invalid")
                seen_ids.add(element_id)
                parsed_cues.append({"element_id": element_id, "label": label,
                                    "focus_box": [left, top, right, bottom]})
            parsed_scene["draw_cues"] = parsed_cues
        parsed.append(parsed_scene)
    return source, locale, tuple(parsed)


def _require_ready(stage: str, result: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") != "READY":
        raise RuntimeError(f"{stage} stopped: {result.get('error_code', 'UNKNOWN')}")
    return result


def _subtitle_cues(
    scenes: tuple[dict[str, Any], ...], durations: list[float]
) -> list[dict[str, str | float]]:
    cues: list[dict[str, str | float]] = []
    cursor = 0.0
    for scene, duration in zip(scenes, durations, strict=True):
        chunks = _caption_chunks(scene["text"])
        weights = [len(chunk.split()) for chunk in chunks]
        total = sum(weights)
        elapsed = 0.0
        for index, (chunk, weight) in enumerate(zip(chunks, weights, strict=True)):
            start = round(cursor + elapsed, 3)
            elapsed += duration * weight / total
            end = round(cursor + duration if index == len(chunks) - 1 else cursor + elapsed, 3)
            if end <= start:
                raise ValueError("TTS segment is too short for a caption")
            cues.append({"text": chunk, "start_seconds": start, "end_seconds": end})
        cursor += duration
    return cues


def _scene_draw_beats(scene: dict[str, Any], scene_index: int, duration: float) -> list[dict]:
    cues = scene.get("draw_cues", [])
    return [
        {**cue, "segment_id": f"segment-{scene_index}",
         "start_seconds": round(duration * beat_index / len(cues), 3),
         "end_seconds": round(duration * (beat_index + 1) / len(cues), 3)}
        for beat_index, cue in enumerate(cues)
    ]


def run_media_smoke(
    source: Path,
    locale: str,
    scenes: tuple[dict[str, Any], ...],
    *,
    get: Callable[[str], dict[str, Any]],
    post: Callable[[str, dict[str, Any]], dict[str, Any]],
    preflight_only: bool = False,
    preview_images: bool = False,
    progress: Callable[[str], None] = lambda _message: None,
) -> dict[str, Any]:
    report = get("/v1/story-video/preflight")
    if not report.get("ready"):
        failed = [name for name, item in report.get("checks", {}).items() if not item.get("ready")]
        raise RuntimeError(f"provider preflight failed: {', '.join(failed) or 'UNKNOWN'}")
    if preflight_only:
        return {"preflight": "READY", "checks": report.get("checks", {})}
    if not preview_images and report.get("story_segmenter") == "sam2" and any(
        not scene.get("draw_cues") for scene in scenes
    ):
        raise ValueError("SAM2 media smoke needs draw_cues in every scene before TTS or images")

    source_bytes = source.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    canonical = json.dumps(
        {"source_sha256": source_hash, "locale": locale,
         "scenes": [{key: value for key, value in scene.items() if key != "draw_cues"}
                    for scene in scenes]},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    package_hash = hashlib.sha256(canonical).hexdigest()
    package_id = f"media-smoke-{package_hash[:12]}"
    cue_hash = hashlib.sha256(json.dumps(
        [scene.get("draw_cues", []) for scene in scenes],
        sort_keys=True, ensure_ascii=False, separators=(",", ":"),
    ).encode()).hexdigest()
    encoded = base64.b64encode(source_bytes).decode("ascii")

    def render_illustrations() -> list[dict[str, Any]]:
        illustrations = []
        for index, scene in enumerate(scenes, 1):
            scene_id = f"scene-{index}"
            progress(f"{scene_id}: image")
            illustration = _require_ready(
                scene_id + " illustration",
                post(
                    "/v1/story-video/illustration",
                    {
                        "request": {
                            "package_id": package_id,
                            "package_hash": package_hash,
                            "scene_id": scene_id,
                            "source_image_ref": "synthetic-media-smoke:source",
                            "source_image_sha256": source_hash,
                            "visual_prompt": scene["visual_prompt"],
                            **({"focus_box": scene["focus_box"]} if "focus_box" in scene else {}),
                        },
                        "source_image": {"sha256": source_hash, "content_base64": encoded},
                    },
                ),
            )
            image_path = Path(str(illustration.get("asset_ref", "")))
            if not image_path.is_file() or _sha256(image_path) != illustration.get("asset_sha256"):
                raise RuntimeError(f"{scene_id} illustration is missing or changed")
            illustrations.append(illustration)
        return illustrations

    if preview_images:
        illustrations = render_illustrations()
        sheet = _preview_contact_sheet(source, scenes, illustrations)
        return {
            "preflight": "READY",
            "package_hash": package_hash,
            "cue_sha256": cue_hash,
            "contact_sheet_ref": str(sheet),
            "contact_sheet_sha256": _sha256(sheet),
            "illustrations": [
                {"scene_id": f"scene-{index}", "asset_ref": item["asset_ref"],
                 "asset_sha256": item["asset_sha256"]}
                for index, item in enumerate(illustrations, 1)
            ],
            "note": "Images only; no TTS, scene MP4 or approved story job.",
        }

    texts = [scene["text"] for scene in scenes]
    progress("TTS narration")
    narration = _require_ready(
        "narration",
        post(
            "/v1/story-video/narration",
            {
                "request": {
                    "package_id": package_id,
                    "package_hash": package_hash,
                    "locale": locale,
                },
                "texts": texts,
            },
        ),
    )
    durations = narration.get("segment_timing_seconds")
    if not isinstance(durations, list) or len(durations) != len(scenes):
        raise RuntimeError("TTS returned an invalid segment count")
    durations = [float(value) for value in durations]
    total = sum(durations)
    if not 40 <= total <= 60 or any(not 5 <= duration <= 20 for duration in durations):
        raise RuntimeError("TTS is outside the 40-60 s total or 5-20 s scene window")
    if abs(float(narration.get("duration_seconds", 0)) - total) > 0.25:
        raise RuntimeError("TTS segment timings differ from combined audio duration")
    audio = Path(str(narration.get("audio_ref", "")))
    if not audio.is_file() or _sha256(audio) != narration.get("audio_sha256"):
        raise RuntimeError("TTS audio is missing or changed")
    cues = _subtitle_cues(scenes, durations)

    clips: list[dict[str, Any]] = []
    illustrations = render_illustrations()
    for index, (scene, duration, illustration) in enumerate(
        zip(scenes, durations, illustrations, strict=True), 1
    ):
        scene_id = f"scene-{index}"
        progress(f"{scene_id}: stroke render")
        draw_beats = _scene_draw_beats(scene, index, duration)
        clip = _require_ready(
            scene_id + " stroke render",
            post(
                "/v1/story-video/scene",
                {
                    "request": {
                        "package_id": package_id,
                        "package_hash": package_hash,
                        "scene_id": scene_id,
                        "illustration_ref": illustration["asset_ref"],
                        "illustration_sha256": illustration["asset_sha256"],
                        "duration_seconds": duration,
                        "model_profile_ref": "whiteboard-stroke-v1",
                        **({"draw_beats": draw_beats} if draw_beats else {}),
                    }
                },
            ),
        )
        if abs(float(clip.get("duration_seconds", 0)) - duration) > 0.5:
            raise RuntimeError(f"{scene_id} clip duration differs from narration")
        clips.append(clip)

    progress("MP4 assembly")
    video = _require_ready(
        "assembly",
        post(
            "/v1/story-video/assembly",
            {
                "request": {
                    "package_id": package_id,
                    "package_hash": package_hash,
                    "scene_ids": [f"scene-{index}" for index in range(1, len(scenes) + 1)],
                    "scene_artifact_refs": [clip["silent_clip_ref"] for clip in clips],
                    "scene_artifact_sha256": [clip["silent_clip_sha256"] for clip in clips],
                    "narration_ref": str(audio),
                    "narration_sha256": narration["audio_sha256"],
                    "subtitle_cues": cues,
                }
            },
        ),
    )
    output = Path(str(video.get("video_ref", "")))
    if not output.is_file() or _sha256(output) != video.get("video_sha256"):
        raise RuntimeError("assembled MP4 is missing or changed")
    if not 40 <= float(video.get("duration_seconds", 0)) <= 60:
        raise RuntimeError("assembled MP4 is outside the 40-60 s duration window")
    return {
        "preflight": "READY",
        "package_hash": package_hash,
        "cue_sha256": cue_hash,
        "scene_durations_seconds": durations,
        "video_ref": str(output),
        "video_sha256": video["video_sha256"],
        "duration_seconds": video.get("duration_seconds"),
        "note": "Media-only smoke test; not an approved story job or visual acceptance.",
    }


def _local_base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ValueError("media smoke test only accepts a local HTTP provider")
    if parsed.username or parsed.password or not parsed.port or parsed.path not in {"", "/"}:
        raise ValueError("provider URL must be a local origin such as http://127.0.0.1:8001")
    return value.rstrip("/")


def _request_json(base_url: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload else None
    request = Request(
        base_url + path,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    try:
        with urlopen(request, timeout=3600 if data else 30) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"provider HTTP {error.code} at {path}") from error
    except URLError as error:
        raise RuntimeError(f"cannot reach local provider at {path}") from error
    if not isinstance(result, dict):
        raise TypeError(f"provider returned non-object JSON at {path}")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Synthetic media fixture JSON")
    parser.add_argument("--provider", default="http://127.0.0.1:8001")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--preview-images", action="store_true")
    parser.add_argument("--confirm-synthetic-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.preflight_only and not args.confirm_synthetic_only:
        parser.error("rendering requires --confirm-synthetic-only (no real child media)")
    base_url = _local_base_url(args.provider)
    source, locale, scenes = load_fixture(args.input)
    result = run_media_smoke(
        source,
        locale,
        scenes,
        get=lambda path: _request_json(base_url, path),
        post=lambda path, payload: _request_json(base_url, path, payload),
        preflight_only=args.preflight_only,
        preview_images=args.preview_images,
        progress=lambda message: print(message, file=sys.stderr, flush=True),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
