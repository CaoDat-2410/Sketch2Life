"""Non-child, no-network Level-1 fixture and contact sheet for story world V2."""

from __future__ import annotations

import argparse
import hashlib
import io
from pathlib import Path

from PIL import Image, ImageDraw
from sketch2life.application.services.story_video_pipeline import StoryVideoPipeline
from sketch2life.application.services.story_world_model import ManualSourceObject
from sketch2life.contracts.schemas.story_video import (
    ApprovedStoryPackageV1,
    StoryScriptSegmentV1,
    stable_model_hash,
    story_script_segments_hash,
)
from sketch2life.contracts.schemas.story_world_v2 import (
    NarrationObjectV2,
    ReviewedEventV2,
)
from sketch2life.infrastructure.media.scene_state_composer import SceneStateComposer


def fixture_inputs():
    """All art, masks, review references and approved text here are synthetic."""
    image = Image.new("RGB", (600, 360), "white")
    masks: dict[str, Image.Image] = {}
    definitions = (
        ("mother", "person", (45, 155, 105, 290), "#eb626c"),
        ("child", "person", (115, 195, 165, 275), "#5989e9"),
        ("father", "person", (175, 145, 240, 285), "#e9a840"),
        ("house", "house", (305, 55, 485, 230), "#efb4b5"),
        ("tree", "tree", (230, 30, 290, 170), "#60b661"),
        ("flowers", "garden", (330, 255, 530, 320), "#bc64ad"),
    )
    for object_id, _, box, color in definitions:
        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        if object_id == "tree":
            draw.ellipse(box, fill=255)
        else:
            draw.rectangle(box, fill=255)
        image.paste(color, mask=mask)
        masks[object_id] = mask
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    source = buffer.getvalue()
    sha = hashlib.sha256(source).hexdigest()
    texts = (
        "Gia đình đứng trước nhà.",
        "Gia đình đi dạo trước nhà.",
        "Em bé nhìn thấy một con bướm trong vườn hoa.",
        "Cả nhà quay về nhà.",
    )
    segments = tuple(
        StoryScriptSegmentV1(
            segment_id=f"segment-{index}", text=text,
            approved_fact_ids=(f"fact-{index}",),
            confirmed_anchor_ids=(f"anchor-{index}",),
            scene_purpose=("INTRO", "EXPLAIN", "DEMONSTRATE", "RECAP")[index - 1],
        )
        for index, text in enumerate(texts, 1)
    )
    digest = "a" * 64
    package = ApprovedStoryPackageV1(
        package_id="pkg-world-fixture", session_id="synthetic-session", session_version=1,
        source_image_ref="fixture:family.png", source_image_sha256=sha,
        confirmed_understanding_ref="fixture:understanding", confirmed_understanding_sha256=digest,
        experience_spec_ref="fixture:experience", experience_spec_sha256=digest,
        story_script_ref="fixture:reviewed-script", story_script_revision=1,
        story_script_sha256=story_script_segments_hash(segments),
        audience_profile_ref="fixture:audience", audience_profile_sha256=digest,
        evidence_set_ref="fixture:evidence", evidence_set_sha256=digest,
        locale="vi-VN", narration_profile_ref="fixture:voice",
        narration_profile_sha256=digest, approval_ref="fixture:approval",
        approval_sha256=digest, content_validator_version="fixture-only",
        content_validator_result="PASSED", created_at="2026-10-09T00:00:00Z",
        package_hash=digest,
    )
    package = package.model_copy(update={
        "package_hash": stable_model_hash(package, exclude={"package_hash"})
    })
    specs = []
    for object_id, object_type, _, _ in definitions:
        output = io.BytesIO()
        masks[object_id].save(output, format="PNG")
        specs.append(ManualSourceObject(
            object_id=object_id, object_type=object_type, mask_png=output.getvalue(),
            identity_review_ref="fixture:mask-review-v1",
            reviewed_mask_sha256=hashlib.sha256(output.getvalue()).hexdigest(),
            approved_fact_ids=("fact-1",), confirmed_anchor_ids=("anchor-1",),
        ))
    butterfly = NarrationObjectV2(
        object_id="butterfly", object_type="butterfly", segment_id="segment-3",
        approved_fact_ids=("fact-3",), requested_appearance="small colorful butterfly",
        requested_action="appears above the garden", asset_status="PENDING",
    )
    event_data = (
        ("family-start", 1, ("mother", "father", "child", "house", "tree", "flowers"),
         "STATIC", {}),
        ("walk", 2, ("mother", "father", "child"), "TRANSLATE",
         {"mother": (.18, .62), "father": (.37, .59), "child": (.28, .65)}),
        ("butterfly", 3, ("child", "butterfly", "flowers"), "ADD_OBJECT", {}),
        ("return", 4, ("mother", "father", "child", "house"), "TRANSLATE",
         {"mother": (.12, .62), "father": (.34, .59), "child": (.23, .65)}),
    )
    events = tuple(
        ReviewedEventV2(
            event_id=f"event-{name}", segment_id=f"segment-{index}",
            approved_fact_ids=(f"fact-{index}",),
            confirmed_anchor_ids=(f"anchor-{index}",),
            source_quote=texts[index - 1], mapping_rule="EXPLICIT_REVIEWED_EVENT",
            approval_status="APPROVED", review_ref="fixture:adult-review-v1",
            object_ids=objects, action=action, target_positions=positions,
            camera_intent="PAN" if index == 2 else "HOLD",
        )
        for name, index, objects, action, positions in event_data
    )
    return package, segments, source, tuple(specs), (butterfly,), events


class _NoProvider:
    def render(self, *_args, **_kwargs):
        raise AssertionError("V2 prototype must not call a paid provider")

    def assemble(self, *_args, **_kwargs):
        raise AssertionError("V2 prototype must not assemble an MP4")


def make_prototype():
    package, segments, source, specs, additions, events = fixture_inputs()
    pipeline = StoryVideoPipeline(
        narration=_NoProvider(), illustrations=_NoProvider(),
        motion=_NoProvider(), assembler=_NoProvider(), story_render_v2_enabled=True,
    )
    return pipeline.run_v2_prototype(
        package, segments, source_image_bytes=source, source_objects=specs,
        narration_objects=additions, events=events,
        measured_segment_durations=(10.0, 10.0, 10.0, 10.0),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Create synthetic V2 continuity contact sheet")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = make_prototype()
    composer = SceneStateComposer()
    images = [composer.render_scene(result.registry, scene) for scene in result.scene_plan.scenes[:2]]
    sheet = Image.new("RGB", (1200, 390), "white")
    for index, image in enumerate(images):
        sheet.paste(image, (600 * index, 30))
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 5), "Scene 1: source identities", fill="black")
    draw.text((610, 5), "Scene 2: same source assets, translated", fill="black")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, format="PNG")
    print(args.output)


if __name__ == "__main__":
    main()
