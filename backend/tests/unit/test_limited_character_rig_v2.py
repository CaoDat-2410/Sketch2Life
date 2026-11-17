"""Synthetic, no-network rig math/provenance checks, not visual acceptance."""

from __future__ import annotations

import hashlib
import io
import math
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from tools.story_character_motion_proof import prepare_and_render

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.infrastructure.media.limited_character_rig_v2 import (
    DerivedStyleProfile,
    SourceRigPart,
    ease,
    eased_camera_frame,
    inverse_bone_affine,
    lerp,
    planted_step,
    render_rig_pose,
    two_bone_ik,
)


def rig_inputs():
    asset = Image.new("RGBA", (64, 64))
    draw = ImageDraw.Draw(asset)
    draw.polygon(((20, 20), (39, 20), (39, 29), (20, 29)), fill=(34, 95, 185, 255))
    draw.line(((22, 22), (36, 26)), fill=(10, 30, 90, 255), width=1)
    stream = io.BytesIO()
    asset.save(stream, format="PNG")
    body = stream.getvalue()
    part = SourceRigPart("arm", "synthetic-child", "a" * 64,
                         hashlib.sha256(body).hexdigest(), "shoulder", "hand",
                         (20., 24.), (39., 24.))
    return asset, body, part


def test_identity_bone_transform_reconstructs_source_pixels() -> None:
    image, body, part = rig_inputs()
    result, trace = render_rig_pose(
        canvas_size=image.size, object_id=part.object_id, source_sha256=part.source_image_sha256,
        parts=(part,), assets={part.part_id: image}, asset_png_by_id={part.part_id: body},
        joints={"shoulder": part.bind_start, "hand": part.bind_end},
    )
    assert result.tobytes() == image.tobytes()
    assert trace[0]["inverse_affine"] == [1., 0., 0., -0., 1., 0.]


def test_relative_limb_rotation_changes_pixels_not_root_only_translation() -> None:
    image, body, part = rig_inputs()
    result, trace = render_rig_pose(
        canvas_size=image.size, object_id=part.object_id, source_sha256=part.source_image_sha256,
        parts=(part,), assets={part.part_id: image}, asset_png_by_id={part.part_id: body},
        joints={"shoulder": part.bind_start, "hand": (20., 43.)},
    )
    assert result.getchannel("A").getbbox() != image.getchannel("A").getbbox()
    assert abs(trace[0]["inverse_affine"][1]) > .9
    assert image.getchannel("A").getbbox() == (20, 20, 40, 30)


@pytest.mark.parametrize("mode", ["wrong-source", "wrong-object", "bad-png", "missing",
                                 "wrong-decoded-image", "missing-joint"])
def test_source_asset_or_joint_errors_fail_closed(mode: str) -> None:
    image, body, part = rig_inputs()
    assets, bodies = {part.part_id: image}, {part.part_id: body}
    joints = {"shoulder": part.bind_start, "hand": part.bind_end}
    if mode == "wrong-source":
        part = replace(part, source_image_sha256="b" * 64)
    elif mode == "wrong-object":
        part = replace(part, object_id="another-child")
    elif mode == "bad-png":
        bodies[part.part_id] = b"not the reviewed candidate"
    elif mode == "missing":
        assets = {}
    elif mode == "wrong-decoded-image":
        assets[part.part_id] = Image.new("RGBA", image.size)
    elif mode == "missing-joint":
        joints = {}
    with pytest.raises(StoryWorldError) as error:
        render_rig_pose(canvas_size=image.size, object_id="synthetic-child",
                        source_sha256="a" * 64, parts=(part,), assets=assets,
                        asset_png_by_id=bodies, joints=joints)
    assert error.value.code in {"SOURCE_ASSET_MISMATCH", "NEEDS_POSE_REVIEW"}


@pytest.mark.parametrize("bend", [-1, 1])
def test_two_bone_ik_preserves_lengths(bend: int) -> None:
    knee = two_bone_ik((0., 0.), (0., 17.), 10., 10., bend=bend)
    assert math.dist(knee, (0., 0.)) == pytest.approx(10.)
    assert math.dist(knee, (0., 17.)) == pytest.approx(10.)
    assert knee[0] * bend < 0


@pytest.mark.parametrize("target", [(0., 0.), (0., 50.), (float("nan"), 5.)])
def test_unreachable_or_nonfinite_pose_does_not_stretch(target) -> None:
    with pytest.raises(StoryWorldError, match="NEEDS_POSE_REVIEW"):
        two_bone_ik((0., 0.), target, 10., 10.)


def test_stance_is_world_locked_and_swing_lifts_with_smooth_endpoints() -> None:
    args = dict(start_seconds=1., end_seconds=2., start=(10., 30.),
                target=(20., 30.), lift_pixels=5.)
    for t in (0., .3, .9, 1.):
        assert planted_step(t, **args) == ((10., 30.), True)
    for t in (2., 2.2, 3.):
        assert planted_step(t, **args) == ((20., 30.), True)
    mid, planted = planted_step(1.5, **args)
    assert mid == (15., 25.) and not planted
    near, _ = planted_step(1.00001, **args)
    assert math.dist(near, (10., 30.)) < 1e-7


def test_style_candidate_keeps_alpha_source_and_moderate_palette() -> None:
    image, _, _ = rig_inputs()
    before = image.tobytes()
    enhanced = DerivedStyleProfile("a" * 64).apply(image)
    assert image.tobytes() == before
    assert image.getchannel("A").tobytes() == enhanced.getchannel("A").tobytes()
    # Enhanced RGB is intentionally derived, not falsely labelled pixel-exact.
    assert max(abs(a - b) for a, b in zip(enhanced.getpixel((30, 24))[:3],
                                        image.getpixel((30, 24))[:3], strict=True)) <= 3
    assert DerivedStyleProfile("a" * 64, blend=0).apply(image).tobytes() == before


@pytest.mark.parametrize("profile", [DerivedStyleProfile("a" * 64, blend=.5),
                                      DerivedStyleProfile("a" * 64, blur_radius=3)])
def test_style_out_of_scope_fails(profile) -> None:
    with pytest.raises(StoryWorldError, match="STYLE_PROFILE_INVALID"):
        profile.apply(Image.new("RGBA", (10, 10)))


def test_camera_easing_is_bounded_preserves_start_and_source() -> None:
    image, _, _ = rig_inputs()
    before = image.tobytes()
    assert eased_camera_frame(image, elapsed=0, duration=6).tobytes() == before
    assert eased_camera_frame(image, elapsed=6, duration=6).size == image.size
    assert image.tobytes() == before
    assert [ease(v) for v in (-1, 0, .5, 1, 2)] == [0, 0, .5, 1, 1]
    assert lerp((0., 0.), (10., 20.), .5) == (5., 10.)


def test_nonfinite_camera_or_excessive_bone_scale_fails() -> None:
    with pytest.raises(StoryWorldError, match="MOTION_TIMING_INVALID"):
        eased_camera_frame(Image.new("RGB", (10, 10)), elapsed=float("nan"), duration=6)
    with pytest.raises(StoryWorldError, match="NEEDS_POSE_REVIEW"):
        inverse_bone_affine((0., 0.), (10., 0.), (0., 0.), (20., 0.))


def test_proof_requires_explicit_candidate_permission(tmp_path: Path) -> None:
    with pytest.raises(StoryWorldError, match="NEEDS_APPROVAL"):
        prepare_and_render(tmp_path / "missing.json", tmp_path / "rig.json", tmp_path)


def test_proof_refuses_golden_duration_without_reading_private_data(tmp_path: Path) -> None:
    with pytest.raises(StoryWorldError, match="MOTION_RESOURCE_LIMIT"):
        prepare_and_render(tmp_path / "missing.json", tmp_path / "rig.json", tmp_path,
                           duration=55, confirm_local_candidate_only=True)


def test_proof_refuses_repository_media_output(tmp_path: Path) -> None:
    output = Path(__file__).resolve().parents[3] / "unapproved-private-assets"
    with pytest.raises(StoryWorldError, match="PRIVATE_ARTIFACT_REQUIRED"):
        prepare_and_render(tmp_path / "missing.json", tmp_path / "rig.json", output,
                           confirm_local_candidate_only=True)
