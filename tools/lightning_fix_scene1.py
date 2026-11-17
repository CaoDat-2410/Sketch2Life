"""Repair only scene 1 using cached FLUX; preserve approved scenes 2-4 byte-for-byte.

Run beside lightning_complete_story.py on Lightning. No download or crop blending.
The new full-scene candidate still requires visual review; this is a silent demo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw

from lightning_complete_story import fit, font, render_video


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_approved(source, output):
    hashes = {}
    for index in (2, 3, 4):
        old = source / f"scene-{index}.png"
        new = output / old.name
        shutil.copy2(old, new)
        if sha(old) != sha(new):
            raise RuntimeError(f"Approved scene {index} changed during copying")
        hashes[str(index)] = sha(new)
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source", type=Path,
                        help="Existing complete-story-demo folder; default is the reviewed 040933 run")
    parser.add_argument("--model", type=Path,
                        default=Path("/teamspace/studios/this_studio/models/FLUX.2-klein-4B"))
    parser.add_argument("--scene1", type=Path,
                        help="Reuse a manually reviewed scene-1 PNG instead of running FLUX again")
    args = parser.parse_args()
    root = args.root.resolve()
    source = (args.source or root / ".runtime/complete-story-demo/20261010-040933").resolve()
    clean = root / ".runtime/flux-scene1-proof/20261010-035033/scene1-candidate.png"
    boy = root / ".runtime/flux-boy-proof/20261010-034707/boy-flux-candidate.png"
    required = [source / f"scene-{i}.png" for i in (1, 2, 3, 4)]
    required += [args.scene1] if args.scene1 else [clean, boy, args.model / "model_index.json"]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"Missing input: {path}")
    # New directory only: never overwrite the reviewed run or source images.
    out = root / ".runtime/scene1-repair" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    out.mkdir(parents=True, exist_ok=False)
    approved_hashes = copy_approved(source, out)
    if args.scene1:
        shutil.copy2(args.scene1, out / "scene-1.png")
        prompt = "Externally supplied replacement; visual review is still required."
    else:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        import torch
        from diffusers import Flux2KleinPipeline

        if not torch.cuda.is_available():
            raise RuntimeError("Run this on the Lightning GPU")
        print(f"Loading cached FLUX: {torch.cuda.get_device_name(0)}", flush=True)
        pipe = Flux2KleinPipeline.from_pretrained(str(args.model), dtype=torch.bfloat16,
                                                local_files_only=True)
        pipe.enable_model_cpu_offload()
        prompt = (
            "Edit image 1 into ONE complete family scene. Image 1 is the clean scene before "
            "crop repairs: preserve its composition, the three characters holding hands, poses, "
            "clothing, tree, flowers, path and pink house. Image 2 is ONLY the approved boy "
            "identity: use his brown-orange hair, two open round dark eyes, warm smile and rosy "
            "cheeks for the boy in image 1. Keep the boy's original small size and pose in the "
            "family. Correct the parents' faces coherently: mother with reddish-brown bob hair, "
            "father with black hair and rectangular eyeglasses. Both parents retain adult facial "
            "proportions and friendly smiles; each has exactly two naturally aligned eyes looking "
            "in one direction. Each face has one continuous cheek and jaw contour, clean eyelids "
            "and natural neck attachment. Preserve the father's glasses. Consistent colored "
            "pencil texture and natural dark outlines on a white background. No duplicated "
            "eyes, ghost contours, pasted patches, halos, additional characters, text or panels. "
            "Keep the family holding hands and all subjects fully inside the landscape canvas."
        )
        print("Repairing scene 1 as a single coherent image (no crop blending)...", flush=True)
        with torch.inference_mode():
            result = pipe(
                image=[fit(Image.open(clean), (1024, 768)), fit(Image.open(boy), (768, 768))],
                prompt=prompt, width=1024, height=768, num_inference_steps=4,
                guidance_scale=1.0,
                generator=torch.Generator(device="cpu").manual_seed(64),
            ).images[0]
        result.save(out / "scene-1.png")
        del pipe
        torch.cuda.empty_cache()
    comparison = Image.new("RGB", (1536, 620), "white")
    for index, (path, label) in enumerate([
        (source / "scene-1.png", "Previous crop repair"),
        (clean if clean.is_file() else source / "scene-1.png", "Clean source scene"),
        (out / "scene-1.png", "New scene 1 - REVIEW REQUIRED"),
    ]):
        comparison.paste(fit(Image.open(path), (512, 550)), (index * 512, 45))
        ImageDraw.Draw(comparison).text((index * 512 + 12, 12), label,
                                       font=font(18), fill="black")
    comparison.save(out / "scene1-comparison.png")
    scenes = [Image.open(out / f"scene-{i}.png").convert("RGB") for i in range(1, 5)]
    render_video(scenes, out)
    # Replace the helper's blanket pending labels with the actual user review state.
    sheet = Image.new("RGB", (1280, 960), "white")
    for index, scene in enumerate(scenes):
        x, y = index % 2 * 640, index // 2 * 480
        sheet.paste(fit(scene, (640, 430)), (x, y))
        status = "REVIEW REQUIRED" if index == 0 else "USER APPROVED - UNCHANGED"
        ImageDraw.Draw(sheet).text((x + 15, y + 442), f"Scene {index + 1}: {status}",
                                  font=font(18), fill="black")
    sheet.save(out / "storyboard-review.png")
    report = {
        "scene_1": "PENDING_HUMAN_REVIEW", "scenes_2_3_4": "USER_APPROVED_UNCHANGED",
        "approved_scene_sha256": approved_hashes, "source_run": str(source),
        "replacement_sha256": sha(out / "scene-1.png"), "prompt": prompt,
        "seed": 64 if not args.scene1 else None, "duration_seconds": 24,
        "audio": "NONE", "reveal": "RASTER_SWEEP_SIMULATION_NOT_SEMANTIC_STROKES",
        "production_approved": False,
        "note": "Full-scene generation can change details. Review faces, hands and identity before approval.",
    }
    (out / "status.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"DONE: {out / 'story-demo.mp4'}")
    print(f"Check scene 1: {out / 'scene1-comparison.png'}")
    print("Scenes 2-4 retained byte-for-byte. Scene 1 and the revised video still require review.")


if __name__ == "__main__":
    main()
