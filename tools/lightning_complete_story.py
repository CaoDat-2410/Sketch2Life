"""Offline FLUX handoff. Candidate artwork + silent illustrated demo, not production QA.

Run from the Lightning Sketch2Life root. No installs, downloads or source edits.
The sweep reveal is a preview effect, NOT recovered semantic drawing strokes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

CAPTIONS = [
    "Trước ngôi nhà mái đỏ, em ở bên bố mẹ.",
    "Em bước theo con đường nhỏ vào vườn hoa.",
    "Em cúi xuống, nhẹ nhàng hái một bông hoa.",
    "Bỗng em nhìn thấy một chú bướm cam xanh!",
]
GOLD_BOXES = [(.025, .080, .480, .435), (.515, .080, .975, .435),
              (.025, .565, .480, .925), (.515, .565, .975, .925)]


def box(image, bounds):
    w, h = image.size
    return tuple(round(v * (w if i % 2 == 0 else h)) for i, v in enumerate(bounds))


def fit(image, size):
    return ImageOps.pad(image.convert("RGB"), size, color="white",
                        method=Image.Resampling.LANCZOS)


def font(size):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "C:/Windows/Fonts/arial.ttf"):
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    raise RuntimeError("Missing Unicode font: install/configure a font before rendering Vietnamese captions.")


def render_video(scenes, out, seconds=6.0, fps=24, size=(1280, 720)):
    import imageio_ffmpeg
    w, h = size
    writer = imageio_ffmpeg.write_frames(
        str(out / "story-demo.mp4"), size, fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=1,
        output_params=["-crf", "20", "-preset", "fast", "-movflags", "+faststart"],
    )
    writer.send(None)
    text_font = font(round(w * .025))
    tag_font = font(round(w * .014))
    frames_per_scene = round(seconds * fps)
    if frames_per_scene < 2:
        raise ValueError("Scene duration too short")
    try:
        for index, scene in enumerate(scenes):
            artwork = fit(scene, (w, h - round(h * .15)))
            canvas = Image.new("RGB", size, "white")
            canvas.paste(artwork, (0, 0))
            base = np.asarray(canvas)
            ah = artwork.height
            # Continuous serpentine marker sweep, deliberately labelled a simulation.
            ys, xs = np.mgrid[:h, :w]
            rows = 18
            band = np.minimum(ys * rows // ah, rows - 1)
            direction_x = np.where(band % 2 == 0, xs / w, 1 - xs / w)
            reveal_time = (band + direction_x) / rows
            for frame in range(frames_per_scene):
                progress = min(1.0, frame / max(1, round(frames_per_scene * .65)))
                visible = (reveal_time <= progress) & (ys < ah)
                rgb = np.where(visible[..., None], base, 255).astype(np.uint8)
                result = Image.fromarray(rgb)
                draw = ImageDraw.Draw(result)
                draw.text((w // 2, h - round(h * .065)), CAPTIONS[index],
                          font=text_font, fill="#202020", anchor="mm")
                draw.text((16, 10), f"{index + 1}/4 | DEMO - PENDING REVIEW",
                          font=tag_font, fill="#555555")
                writer.send(np.asarray(result))
            print(f"Encoded scene {index + 1}/{len(scenes)}", flush=True)
    finally:
        writer.close()
    sheet = Image.new("RGB", (1280, 960), "white")
    for i, image in enumerate(scenes):
        tile = fit(image, (640, 430))
        x, y = (i % 2) * 640, (i // 2) * 480
        sheet.paste(tile, (x, y))
        ImageDraw.Draw(sheet).text((x + 15, y + 442), f"Scene {i+1} - REVIEW PENDING",
                                  font=font(20), fill="black")
    sheet.save(out / "storyboard-review.png")
    def stamp(seconds_value):
        millis = round(seconds_value * 1000)
        return f"{millis//3600000:02}:{millis//60000%60:02}:{millis//1000%60:02},{millis%1000:03}"
    (out / "captions.srt").write_text("\n\n".join(
        f"{i+1}\n{stamp(i*seconds)} --> {stamp((i+1)*seconds)}\n{caption}"
        for i, caption in enumerate(CAPTIONS[:len(scenes)])) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--model", type=Path,
                        default=Path("/teamspace/studios/this_studio/models/FLUX.2-klein-4B"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--render-only", action="store_true",
                        help="Reuse the four existing scene-N.png files; does not load FLUX")
    args = parser.parse_args()
    root = args.root.resolve()
    out = (args.output or root / ".runtime" / "complete-story-demo" /
           datetime.now().strftime("%Y%m%d-%H%M%S")).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if not args.render_only:
        boy_path = root / ".runtime/flux-boy-proof/20261010-034707/boy-flux-candidate.png"
        scene_path = root / ".runtime/flux-scene1-proof/20261010-035033/scene1-candidate.png"
        head_path = root / ".runtime/flux-face-fix/20261010-035400/head-correction-candidate.png"
        gold_path = root / "upload/gold-reference.png"
        inputs = [boy_path, scene_path, head_path, gold_path]
        for path in inputs:
            if not path.is_file():
                raise FileNotFoundError(f"Required pinned input missing: {path}")
        if not (args.model / "model_index.json").is_file():
            raise FileNotFoundError(f"Cached Diffusers model missing: {args.model}")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        import torch
        from diffusers import Flux2KleinPipeline
        if not torch.cuda.is_available():
            raise RuntimeError("Run generation on Lightning GPU, not the Windows machine")
        print(f"Loading cached FLUX on {torch.cuda.get_device_name(0)}", flush=True)
        pipe = Flux2KleinPipeline.from_pretrained(str(args.model), dtype=torch.bfloat16,
                                                local_files_only=True)
        pipe.enable_model_cpu_offload()
        boy = Image.open(boy_path).convert("RGB")
        scene = Image.open(scene_path).convert("RGB")
        gold = Image.open(gold_path).convert("RGB")
        prompts = {}

        def generate(images, prompt, seed, size):
            prompts[str(seed)] = prompt
            with torch.inference_mode():
                return pipe(image=images, prompt=prompt, width=size[0], height=size[1],
                            num_inference_steps=4, guidance_scale=1.0,
                            generator=torch.Generator(device="cpu").manual_seed(seed)).images[0]

        # Manual crop-local edit masks, NOT detected faces or object segmentation.
        # Pixels outside each crop are retained exactly. All composites require review.
        repairs = [("boy", (.395, .40, .57, .64)),
                   ("mother", (.19, .27, .395, .485)),
                   ("father", (.55, .17, .735, .385))]
        for i, (name, bounds) in enumerate(repairs):
            bbox = box(scene, bounds)
            current = scene.crop(bbox)
            current.save(out / f"{name}-before.png")
            if name == "boy":
                corrected = Image.open(head_path).convert("RGB")
            else:
                identity = ("adult mother, reddish brown bob hair, no glasses" if name == "mother"
                            else "adult father, black hair, rectangular eyeglasses")
                corrected = generate([fit(current, (512, 512))],
                    f"Edit this close-up of an {identity}. Correct only the eyes: two naturally "
                    "aligned eyes looking in the same direction, clean coherent pupils and eyelids. "
                    "Retain adult facial proportions, smile, head angle, hair, glasses if present, "
                    "neck, clothing, crop layout and colored pencil style. No extra facial features, "
                    "no text. Keep the face at the same position and scale.", 40 + i, (512, 512))
            corrected.save(out / f"{name}-correction.png")
            corrected = corrected.resize(current.size, Image.Resampling.LANCZOS)
            cw, ch = current.size
            mask = Image.new("L", current.size)
            points = [(cw*.12, ch*.35), (cw*.30, ch*.18), (cw*.73, ch*.18),
                      (cw*.90, ch*.38), (cw*.86, ch*.69), (cw*.64, ch*.88),
                      (cw*.37, ch*.88), (cw*.13, ch*.68)]
            ImageDraw.Draw(mask).polygon(points, fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(max(1, cw * .025)))
            mask.save(out / f"{name}-manual-edit-mask.png")
            scene.paste(corrected, bbox[:2], mask)
        scene.save(out / "scene-1.png")
        actions = [
            "The boy walks alone along the garden path between colorful flowers. The family house "
            "is small in the background. No parents in this scene.",
            "The boy bends down and gently picks ONE pink flower by its stem in the garden. "
            "His face is clearly visible in a natural three-quarter view, not hidden. No parents.",
            "The boy stands in the garden holding the same ONE pink flower, looking happily at "
            "ONE butterfly with orange and cyan wings flying nearby. No parents.",
        ]
        for i, action in enumerate(actions, start=2):
            print(f"Generating scene {i}/4", flush=True)
            ref = gold.crop(box(gold, GOLD_BOXES[i-1]))
            ref.save(out / f"scene-{i}-gold-reference.png")
            result = generate([fit(boy, (768, 768)), fit(ref, (1024, 768))],
                "Create ONE landscape colored whiteboard story illustration. Image 1 is the "
                "approved boy identity: preserve his exact face, brown-orange hair, round dark "
                "eyes, blue shirt with orange pocket, purple shorts and green shoes. Image 2 gives "
                "ONLY composition and action; do not copy its boy face. " + action +
                " Clean white background, natural dark hand-drawn outlines, bright colored pencil "
                "fills matching image 1. Complete limbs and natural hands. No frame, panels, text, "
                "captions, labels or watermark. Preserve facial identity rather than inventing "
                "another child. Keep all important subjects inside the canvas.", 50 + i, (1024, 768))
            result.save(out / f"scene-{i}.png")
        del pipe
        torch.cuda.empty_cache()
        (out / "generation.json").write_text(json.dumps({
            "model": str(args.model), "steps": 4, "prompts": prompts,
            "inputs": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
            "approval": "PENDING_HUMAN_REVIEW", "face_masks": "MANUAL_APPROXIMATE_CROP_LOCAL",
            "warning": "Crops and composites may need adjustment; no automatic face-quality guarantee.",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    scenes = [Image.open(out / f"scene-{i}.png").convert("RGB") for i in range(1, 5)]
    render_video(scenes, out)
    (out / "status.json").write_text(json.dumps({
        "duration_seconds": 24, "audio": "NONE", "visual_qa": "PENDING_HUMAN_REVIEW",
        "reveal": "RASTER_SERPENTINE_PREVIEW_NOT_SEMANTIC_STROKES",
        "production_approved": False,
    }, indent=2), encoding="utf-8")
    print(f"DONE (silent demo, review required): {out / 'story-demo.mp4'}")
    print(f"Review all four faces/actions: {out / 'storyboard-review.png'}")


if __name__ == "__main__":
    main()
