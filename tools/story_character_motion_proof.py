"""Explicit CPU/local candidate motion proof, independent of V1/HTTP/Golden jobs.

All anatomy/poses are supplied in a private manual definition, not hardcoded
identities in the engine. Candidates may be used only for this review proof.
Original image and master masks are read-only. No TTS/AI/network call exists.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import time
from itertools import pairwise
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageChops, ImageDraw
from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.infrastructure.media.limited_character_rig_v2 import (
    DerivedStyleProfile,
    SourceRigPart,
    ease,
    eased_camera_frame,
    lerp,
    planted_step,
    render_rig_pose,
    two_bone_ik,
)


def _digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _png(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def _local_path(value: str) -> Path:
    if "://" in value:
        raise StoryWorldError("LOCAL_ONLY", "remote asset path forbidden")
    return Path(value).resolve(strict=True)


def candidate_joints(definition: dict, elapsed: float) -> tuple[dict, dict]:
    """One explicit proof timeline: release/standing preparation then 3 bounded steps."""
    bind = {name: tuple(point) for name, point in definition["joints"].items()}
    release = ease((elapsed - .3) / 1.3)
    travel = definition["root_travel_pixels"] * ease((elapsed - 2.) / 3.2)
    root = (travel, 3. * release)
    joints = {name: (point[0] + root[0], point[1] + root[1])
              for name, point in bind.items()}
    planted = {}
    for side, resting, bend in (("left", (196., definition["ground_ankle_y"]), 1),
                               ("right", (216., definition["ground_ankle_y"]), -1)):
        wrist = bind[f"{side}_wrist"]
        shoulder = joints[f"{side}_shoulder"]
        rest_wrist = ((180., 244.) if side == "left" else (233., 236.))
        target = lerp(wrist, rest_wrist, release)
        swing = 1.2 * math.sin(max(0., elapsed - 2.) * math.pi) * release
        target = (target[0] + root[0] + swing, target[1] + root[1])
        upper = math.dist(bind[f"{side}_shoulder"], bind[f"{side}_elbow"])
        lower = math.dist(bind[f"{side}_elbow"], wrist)
        # At exact original pose retain annotated knee/elbow, avoiding reflection
        # ambiguity. During release the explicit candidate IK chain is followed.
        elbow = two_bone_ik(shoulder, target, upper, lower, bend=bend)
        joints[f"{side}_elbow"], joints[f"{side}_wrist"] = elbow, target
        ankle = lerp(bind[f"{side}_ankle"], resting, release)
        foot_planted = False
        if elapsed >= 2.:
            if side == "left":
                ankle, foot_planted = planted_step(
                    elapsed, start_seconds=2.3, end_seconds=3.1,
                    start=resting, target=(resting[0] + 12, resting[1]), lift_pixels=5.,
                )
                if elapsed > 4.2:
                    ankle, foot_planted = planted_step(
                        elapsed, start_seconds=4.3, end_seconds=5.1,
                        start=(resting[0] + 12, resting[1]),
                        target=(resting[0] + 20, resting[1]), lift_pixels=4.,
                    )
            else:
                ankle, foot_planted = planted_step(
                    elapsed, start_seconds=3.3, end_seconds=4.1,
                    start=resting, target=(resting[0] + 20, resting[1]), lift_pixels=6.,
                )
        hip = joints[f"{side}_hip"]
        upper = math.dist(bind[f"{side}_hip"], bind[f"{side}_knee"])
        lower = math.dist(bind[f"{side}_knee"], bind[f"{side}_ankle"])
        joints[f"{side}_knee"] = two_bone_ik(hip, ankle, upper, lower, bend=bend)
        joints[f"{side}_ankle"] = ankle
        # Whole shoe has unchanged orientation during stance. Its endpoint is
        # world-locked, not added to root translation a second time.
        delta = (ankle[0] - bind[f"{side}_ankle"][0],
                 ankle[1] - bind[f"{side}_ankle"][1])
        joints[f"{side}_toe"] = (bind[f"{side}_toe"][0] + delta[0],
                                    bind[f"{side}_toe"][1] + delta[1])
        planted[side] = foot_planted
    if elapsed <= .3:
        joints = bind
    return joints, {"root_offset": root, "release_fraction": release, "planted": planted}


def prepare_and_render(
    manifest_path: Path, definition_path: Path, output: Path, *, duration: float = 6.,
    fps: int = 24, confirm_local_candidate_only: bool = False,
) -> dict:
    if not confirm_local_candidate_only:
        raise StoryWorldError("NEEDS_APPROVAL", "explicit conditional proof authorization required")
    if not 5 <= duration <= 8 or not 12 <= fps <= 30 or duration * fps > 240:
        raise StoryWorldError("MOTION_RESOURCE_LIMIT", "proof must be 5–8s and at most 240 frames")
    repo = Path(__file__).resolve().parents[1]
    if output.resolve().is_relative_to(repo):
        raise StoryWorldError("PRIVATE_ARTIFACT_REQUIRED", "real motion candidates stay outside Git")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    source_body = _local_path(manifest["source_ref"]).read_bytes()
    source_hash = _digest(source_body)
    if source_hash != manifest["source_image_sha256"] or source_hash != definition[
        "source_image_sha256"
    ]:
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "source/rig definition hash mismatch")
    source = Image.open(io.BytesIO(source_body)).convert("RGBA")
    if max(source.size) > 2048 or source.width * source.height > 1920 * 1080:
        raise StoryWorldError("MOTION_RESOURCE_LIMIT", "source canvas too large")
    output.mkdir(parents=True, exist_ok=True)
    if (output / "motion-proof.mp4").exists() or (output / "candidate-asset-manifest.json").exists():
        raise StoryWorldError("ARTIFACT_EXISTS", "refusing to overwrite previous proof")
    started = time.monotonic()
    object_specs = {obj["object_id"]: obj for obj in manifest["objects"]}
    if definition["object_id"] not in object_specs:
        raise StoryWorldError("NEEDS_MASK_REVIEW", "unknown source character identity")
    mask_checks = []
    for obj in manifest["objects"]:
        body = _local_path(obj["mask_ref"]).read_bytes()
        if _digest(body) != obj["mask_sha256"]:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "master mask changed")
        mask_image = Image.open(io.BytesIO(body)).convert("L")
        if mask_image.size != source.size:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "master mask coordinates mismatch")
        mask_checks.append({"object_id": obj["object_id"], "sha256": _digest(body)})
    parent = object_specs[definition["object_id"]]
    parent_mask = Image.open(_local_path(parent["mask_ref"])).convert("L")
    style = DerivedStyleProfile(source_hash, **definition["style"])
    enhanced = style.apply(source)
    source.save(output / "source-decoded.png")
    enhanced.save(output / "enhanced-source-candidate.png")
    bind = {name: tuple(point) for name, point in definition["joints"].items()}
    union = Image.new("L", source.size, 0)
    parts = []
    assets = {}
    pngs = {}
    part_specs = []
    mask_overlay = enhanced.copy()
    overlay = ImageDraw.Draw(mask_overlay)
    (output / "parts").mkdir(exist_ok=True)
    for index, item in enumerate(definition["parts"]):
        region = Image.new("L", source.size, 0)
        ImageDraw.Draw(region).polygon([tuple(p) for p in item["polygon"]], fill=255)
        # Polygon selects anatomy from a true master silhouette. It is not a bbox
        # segmentation replacement; actual pixels/alpha remain master-mask bound.
        mask = ImageChops.multiply(region, parent_mask)
        if not mask.getbbox():
            raise StoryWorldError("NEEDS_MASK_REVIEW", "candidate part has no source pixels")
        union = ImageChops.lighter(union, mask)
        asset = enhanced.copy()
        asset.putalpha(mask)
        original_part = source.copy()
        original_part.putalpha(mask)
        original_part.save(output / "parts" / f"{item['part_id']}.source.png")
        mask.save(output / "parts" / f"{item['part_id']}.mask.png")
        body = _png(asset)
        (output / "parts" / f"{item['part_id']}.enhanced.png").write_bytes(body)
        part = SourceRigPart(
            part_id=item["part_id"], object_id=definition["object_id"],
            source_image_sha256=source_hash, asset_sha256=_digest(body),
            start_joint=item["start_joint"], end_joint=item["end_joint"],
            bind_start=bind[item["start_joint"]], bind_end=bind[item["end_joint"]],
            z_index=item["z_index"], provenance="SOURCE_MASKED_ENHANCED_RESAMPLED_CANDIDATE",
        )
        parts.append(part)
        assets[part.part_id], pngs[part.part_id] = asset, body
        part_specs.append({**part.__dict__, "asset_ref": str(output / "parts" /
                          f"{part.part_id}.enhanced.png"), "mask_sha256": _digest(_png(mask)),
                           "review_status": "NEEDS_VISUAL_REVIEW"})
        color = (40 + index * 19, 190 - index * 8, 40 + index * 13, 255)
        overlay.line([tuple(p) for p in item["polygon"]] + [tuple(item["polygon"][0])],
                     fill=color, width=1)
        overlay.text(tuple(item["polygon"][0]), item["part_id"], fill=color)
    body_mask = ImageChops.subtract(parent_mask, union)
    body_asset = enhanced.copy()
    body_asset.putalpha(body_mask)
    body_png = _png(body_asset)
    body_part = SourceRigPart("body-head", definition["object_id"], source_hash,
                               _digest(body_png), "body_top", "body_bottom",
                               bind["body_top"], bind["body_bottom"], 5,
                               "SOURCE_HEAD_TORSO_ENHANCED_RIGID_TRANSLATION_ONLY")
    parts.append(body_part)
    assets[body_part.part_id], pngs[body_part.part_id] = body_asset, body_png
    (output / "parts" / "body-head.enhanced.png").write_bytes(body_png)
    body_mask.save(output / "parts" / "body-head.mask.png")
    body_source = source.copy()
    body_source.putalpha(body_mask)
    body_source.save(output / "parts" / "body-head.source.png")
    part_specs.append({**body_part.__dict__, "review_status": "NEEDS_VISUAL_REVIEW"})
    for name, point in bind.items():
        overlay.ellipse((point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2),
                        fill="red")
        overlay.text((point[0] + 3, point[1] - 4), name, fill="black")
    mask_overlay.save(output / "rig-source-overlay.png")

    # Inpainting is NOT claimed. New background pixels are explicitly copied
    # from a reviewed-later unobstructed source patch, with a full donor map.
    box = definition["background_sample_box"]
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= source.width and 0 <= y0 < y1 <= source.height):
        raise StoryWorldError("NEEDS_MASK_REVIEW", "background donor outside source")
    py, px = np.indices((source.height, source.width))
    donor_x = x0 + px % (x1 - x0)
    donor_y = y0 + py % (y1 - y0)
    donor = np.asarray(enhanced)[donor_y, donor_x]
    patch = Image.fromarray(donor, "RGBA")
    background = enhanced.copy()
    background.paste(patch, (0, 0), parent_mask)
    background.save(output / "occluded-background-candidate.png")
    parent_mask.save(output / "derived-background-region-mask.png")
    np.savez_compressed(output / "background-donor-map.npz", source_x=donor_x,
                        source_y=donor_y, applied_mask=np.asarray(parent_mask))
    background_spec = {
        "provenance": "SOURCE_CLONED_PIXELS_NEW_LOCATION_ENHANCED_DERIVED_BACKGROUND",
        "donor_box": box, "donor_map_ref": str(output / "background-donor-map.npz"),
        "pixel_identity": "NOT_ORIGINAL_HIDDEN_BACKGROUND_NOT_GENERATED_AI",
        "review_status": "NEEDS_VISUAL_REVIEW", "applied_only_to_parent_mask": True,
    }
    for obj in manifest["objects"]:
        if obj["object_id"] == definition["object_id"]:
            continue
        other = Image.open(_local_path(obj["mask_ref"])).convert("L")
        if ImageChops.multiply(parent_mask, other).getbbox():
            raise StoryWorldError("NEEDS_MASK_REVIEW", "parent overlaps another master identity")
    raw_diff = ImageChops.difference(source.convert("RGB"), enhanced.convert("RGB"))
    comparison = Image.new("RGB", (source.width * 3, source.height + 30), "white")
    labels = ImageDraw.Draw(comparison)
    for i, (label, art) in enumerate((('ORIGINAL', source), ('ENHANCED CANDIDATE', enhanced),
                                    ('DIFFERENCE x12', raw_diff.point(lambda p: min(255, p * 12))))):
        comparison.paste(art.convert("RGB"), (i * source.width, 30))
        labels.text((i * source.width + 5, 5), label, fill="black")
    comparison.save(output / "original-enhanced-style-comparison.png")
    bound_pose, _ = render_rig_pose(canvas_size=source.size, object_id=definition["object_id"],
                                   source_sha256=source_hash, parts=tuple(parts), assets=assets,
                                   asset_png_by_id=pngs, joints=bind)
    expected_pose = enhanced.copy()
    expected_pose.putalpha(parent_mask)
    bind_diff = ImageChops.difference(bound_pose, expected_pose)
    if bind_diff.getbbox():
        raise StoryWorldError("NEEDS_POSE_REVIEW", "bind pose fails source-part reconstruction")
    records = []
    # Preflight every frame before encoding, failing one bounded attempt if pose
    # targets cannot be reached; never increase stretch/resource limits silently.
    count = round(duration * fps)
    for index in range(count):
        elapsed = duration * index / (count - 1)
        joints, info = candidate_joints(definition, elapsed)
        records.append({"frame": index, "seconds": elapsed, "joints": joints, **info})
    pose_times = (0., 1.6, 2.7, 3.7, 4.7, 6.)
    contact = Image.new("RGB", (source.width * 3, (source.height + 25) * 2), "white")
    contact_draw = ImageDraw.Draw(contact)
    cropped_poses = []
    for i, elapsed in enumerate(pose_times):
        joints, _ = candidate_joints(definition, elapsed)
        pose, _ = render_rig_pose(canvas_size=source.size, object_id=definition["object_id"],
                                  source_sha256=source_hash, parts=tuple(parts), assets=assets,
                                  asset_png_by_id=pngs, joints=joints)
        board = Image.alpha_composite(background, pose).convert("RGB")
        board.save(output / f"pose-{elapsed:04.1f}s-native.png")
        x, y = (i % 3) * source.width, (i // 3) * (source.height + 25)
        contact.paste(board, (x, y + 25))
        contact_draw.text((x + 5, y + 5), f"{elapsed:.1f}s CANDIDATE", fill="black")
        cropped_poses.append(board.crop((138, 155, 286, 314)).resize((296, 318)))
    contact.save(output / "pose-contact-sheet.png")
    detail_sheet = Image.new("RGB", (296 * 3, 343 * 2), "white")
    labels = ImageDraw.Draw(detail_sheet)
    for i, frame in enumerate(cropped_poses):
        x, y = i % 3 * 296, i // 3 * 343
        detail_sheet.paste(frame, (x, y + 25))
        labels.text((x + 5, y + 5), f"{pose_times[i]:.1f}s CANDIDATE", fill="black")
    detail_sheet.save(output / "child-pose-detail-sheet.png")
    video = output / "motion-proof.mp4"
    debug_video = output / "motion-proof-joints-debug.mp4"
    writers = [imageio.get_writer(str(path), fps=fps, codec="libx264", quality=9,
                                 pixelformat="yuv420p", macro_block_size=1)
               for path in (video, debug_video)]
    try:
        for record in records:
            if time.monotonic() - started > 120:
                raise StoryWorldError("MOTION_RESOURCE_LIMIT", "proof exceeded 120s CPU deadline")
            pose, transforms = render_rig_pose(
                canvas_size=source.size, object_id=definition["object_id"],
                source_sha256=source_hash, parts=tuple(parts), assets=assets,
                asset_png_by_id=pngs, joints=record["joints"],
            )
            record["transforms"] = transforms
            board = Image.alpha_composite(background, pose).convert("RGB")
            if record["frame"] in (0, count - 1):
                board.save(output / f'frame-{record["frame"]:03}-raw.png')
            clean = eased_camera_frame(board, elapsed=record["seconds"], duration=duration,
                                       end_zoom=1.035, center=(.48, .58))
            debug = board.copy()
            draw = ImageDraw.Draw(debug)
            for part in parts:
                draw.line((record["joints"][part.start_joint], record["joints"][part.end_joint]),
                          fill="red", width=1)
            for point in record["joints"].values():
                draw.ellipse((point[0] - 2, point[1] - 2, point[0] + 2, point[1] + 2),
                             fill="yellow", outline="red")
            debug = eased_camera_frame(debug, elapsed=record["seconds"], duration=duration,
                                       end_zoom=1.035, center=(.48, .58))
            for writer, frame in zip(writers, (clean, debug), strict=True):
                writer.append_data(np.asarray(frame.resize((source.width * 2, source.height * 2),
                                                           Image.Resampling.LANCZOS)))
    finally:
        for writer in writers:
            writer.close()
    decode = []
    for path in (video, debug_video):
        reader = imageio.get_reader(str(path), format="ffmpeg")
        frames = 0
        try:
            meta = reader.get_meta_data()
            for frame in reader:
                if frames in (0, 24, 48, 72, 96, 120, 143) and path == video:
                    Image.fromarray(frame).save(output / f"decoded-frame-{frames:03}.png")
                frames += 1
        finally:
            reader.close()
        decode.append({"path": str(path), "frames": frames, "fps": meta["fps"],
                       "duration": meta["duration"], "size": list(meta["size"])})
        if frames != count or abs(meta["duration"] - duration) > .05:
            raise StoryWorldError("MOTION_TIMING_INVALID", "encoded proof timing mismatch")
    slide = []
    for a, b in pairwise(records):
        for side in ('left', 'right'):
            if a["planted"][side] and b["planted"][side]:
                slide.append(math.dist(a['joints'][f'{side}_ankle'],
                                       b['joints'][f'{side}_ankle']))
    source_now = _digest(_local_path(manifest["source_ref"]).read_bytes())
    if source_now != source_hash:
        raise StoryWorldError("SOURCE_ASSET_MISMATCH", "source changed during proof")
    metrics = {
        "status": "MOTION_PROOF_NOT_PASSED_AWAITING_OWNER_VIDEO_REVIEW",
        "source_image_sha256": source_hash, "master_mask_hash_checks": mask_checks,
        "duration": duration, "fps": fps, "frame_count": count, "decode": decode,
        "bind_reconstruction": "EXACT_ENHANCED_SOURCE_INSIDE_MASTER_MASK",
        "foot_stance_endpoint_max_delta_world_px": max(slide, default=0.),
        "foot_metric_limit": "Endpoints only, not sole-shape/skin appearance or owner QA",
        "style_rgb_mae": float(np.abs(np.asarray(source.convert('RGB'), dtype=np.int16) -
                                      np.asarray(enhanced.convert('RGB'), dtype=np.int16)).mean()),
        "wall_seconds": time.monotonic() - started,
        "parents_motion": "NOT_IMPLEMENTED_IN_THIS_PROOF", "butterfly": "NOT_CREATED",
        "audio": "NOT_CALLED_OR_CREATED", "inference_calls": 0,
        "candidate_assets_approved_for_golden": False, "server_gate_a_b": "NOT_VERIFIED",
    }
    for name, data in (("joint-transform-timeline.json", records),
                       ("candidate-asset-manifest.json", {"source_sha256": source_hash,
                        "style_profile": style.__dict__, "object_id": definition["object_id"],
                        "parts": part_specs, "background": background_spec,
                        "review_status": "NEEDS_VISUAL_REVIEW", "original_masks_unchanged": True}),
                       ("motion-metrics.json", metrics)):
        (output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--rig-definition", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--confirm-local-candidate-only", action="store_true")
    args = parser.parse_args()
    result = prepare_and_render(args.source_manifest, args.rig_definition, args.output_dir,
                                confirm_local_candidate_only=args.confirm_local_candidate_only)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
