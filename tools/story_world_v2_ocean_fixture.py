"""Independent synthetic ocean fixture for the same manual-mask V2 prototype."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from PIL import Image, ImageDraw
from sketch2life.application.services.story_video_pipeline import StoryVideoPipeline
from sketch2life.application.services.story_world_model import ManualSourceObject
from sketch2life.contracts.schemas.story_video import (
    StoryScriptSegmentV1,
    stable_model_hash,
    story_script_segments_hash,
)
from sketch2life.contracts.schemas.story_world_v2 import ReviewedEventV2
from sketch2life.infrastructure.media.scene_state_composer import SceneStateComposer

from tools.story_world_v2_fixture import _NoProvider
from tools.story_world_v2_fixture import fixture_inputs as family_inputs


def fixture_inputs(*, image_format: str = "PNG"):
    """Return source, masks and reviewed fixture events; no model or network call."""
    if image_format not in {"PNG", "JPEG"}:
        raise ValueError("ocean fixture supports PNG or JPEG")
    image = Image.new("RGB", (480, 320), "#eaf8fd")
    draw = ImageDraw.Draw(image)
    draw.line([(0, 270), (480, 270)], fill="#79c9d9", width=3)
    masks: dict[str, Image.Image] = {}
    definitions = (
        ("fish-blue", "fish", (35, 75, 125, 145), "#347ccd", "fish"),
        ("fish-orange", "fish", (160, 100, 230, 150), "#ee8a31", "fish"),
        ("turtle", "turtle", (280, 120, 400, 220), "#58ae70", "turtle"),
        ("kelp-left", "seaweed", (52, 210, 102, 295), "#278c63", "polygon"),
        ("coral", "coral", (325, 230, 435, 300), "#d567a0", "polygon"),
    )
    for object_id, _, box, color, shape in definitions:
        mask = Image.new("L", image.size, 0)
        painter = ImageDraw.Draw(mask)
        left, top, right, bottom = box
        if shape == "fish":
            span = right - left
            painter.ellipse((left + span // 4, top + 8, right, bottom - 8), fill=255)
            painter.polygon(
                [(left + span // 3, (top + bottom) // 2), (left, top + 6),
                 (left, bottom - 6)], fill=255,
            )
        elif shape == "turtle":
            painter.ellipse((left + 20, top + 22, right - 26, bottom - 25), fill=255)
            painter.ellipse((right - 37, top + 34, right, bottom - 43), fill=255)
            painter.ellipse((left + 27, top + 5, left + 54, top + 45), fill=255)
            painter.ellipse((left + 32, bottom - 48, left + 63, bottom - 4), fill=255)
            painter.ellipse((right - 69, top + 5, right - 39, top + 43), fill=255)
            painter.ellipse((right - 70, bottom - 47, right - 41, bottom - 4), fill=255)
        else:
            painter.polygon(
                [(left, bottom), (left + 8, top), (left + 20, top + 35),
                 (right - 10, top + 8), (right, bottom)], fill=255,
            )
        image.paste(color, mask=mask)
        if shape == "fish":
            draw.ellipse((right - 18, top + 21, right - 13, top + 26), fill="#153b52")
            draw.arc((left + (right - left) // 4, top + 8, right, bottom - 8),
                     start=15, end=340, fill="#17445d", width=2)
        elif shape == "turtle":
            draw.ellipse((right - 18, top + 43, right - 13, top + 48), fill="#174d3e")
            draw.arc((left + 21, top + 22, right - 26, bottom - 25),
                     start=0, end=359, fill="#287454", width=3)
        masks[object_id] = mask
    source_io = io.BytesIO()
    image.save(source_io, format=image_format, quality=92)
    source = source_io.getvalue()
    texts = (
        "Hai chú cá bơi gần rùa biển.",
        "Cá xanh bơi đến gần rong biển.",
        "Rùa biển nhìn rặng san hô.",
        "Các bạn trở về vùng nước yên bình.",
    )
    segments = tuple(
        StoryScriptSegmentV1(
            segment_id=f"segment-{index}", text=text,
            approved_fact_ids=(f"ocean-fact-{index}",),
            confirmed_anchor_ids=(f"ocean-anchor-{index}",),
            scene_purpose=("INTRO", "EXPLAIN", "DEMONSTRATE", "RECAP")[index - 1],
        )
        for index, text in enumerate(texts, 1)
    )
    family_package, *_ = family_inputs()
    package = family_package.model_copy(update={
        "package_id": f"pkg-ocean-{image_format.lower()}",
        "source_image_ref": f"fixture:ocean.{image_format.lower()}",
        "source_image_sha256": hashlib.sha256(source).hexdigest(),
        "story_script_sha256": story_script_segments_hash(segments),
        "package_hash": "0" * 64,
    })
    package = package.model_copy(update={
        "package_hash": stable_model_hash(package, exclude={"package_hash"}),
    })
    specs = []
    for object_id, object_type, *_ in definitions:
        mask_io = io.BytesIO()
        masks[object_id].save(mask_io, format="PNG")
        specs.append(ManualSourceObject(
            object_id=object_id, object_type=object_type, mask_png=mask_io.getvalue(),
            identity_review_ref="fixture:ocean-manual-mask-review",
            reviewed_mask_sha256=hashlib.sha256(mask_io.getvalue()).hexdigest(),
            approved_fact_ids=("ocean-fact-1",),
            confirmed_anchor_ids=("ocean-anchor-1",),
        ))
    event_data: tuple[
        tuple[str, tuple[str, ...], str, dict[str, tuple[float, float]]], ...
    ] = (
        ("ocean-start", ("fish-blue", "fish-orange", "turtle", "kelp-left", "coral"),
         "STATIC", {}),
        ("fish-swim", ("fish-blue",), "TRANSLATE", {"fish-blue": (.30, .32)}),
        ("turtle-sees-coral", ("turtle", "coral"), "STATIC", {}),
        ("ocean-return", ("fish-blue", "fish-orange"), "TRANSLATE",
         {"fish-blue": (.17, .34), "fish-orange": (.40, .39)}),
    )
    events = tuple(
        ReviewedEventV2(
            event_id=f"event-{name}", segment_id=f"segment-{index}",
            approved_fact_ids=(f"ocean-fact-{index}",),
            confirmed_anchor_ids=(f"ocean-anchor-{index}",),
            source_quote=texts[index - 1], mapping_rule="EXPLICIT_REVIEWED_EVENT",
            approval_status="APPROVED", review_ref="fixture:ocean-review-only",
            object_ids=object_ids, action=action, target_positions=positions,
        )
        for index, (name, object_ids, action, positions) in enumerate(event_data, 1)
    )
    return package, segments, source, tuple(specs), (), events


def make_prototype(*, image_format: str = "PNG"):
    package, segments, source, specs, additions, events = fixture_inputs(
        image_format=image_format,
    )
    pipeline = StoryVideoPipeline(
        narration=_NoProvider(), illustrations=_NoProvider(),
        motion=_NoProvider(), assembler=_NoProvider(), story_render_v2_enabled=True,
    )
    return pipeline.run_v2_prototype(
        package, segments, source_image_bytes=source, source_objects=specs,
        narration_objects=additions, events=events,
        measured_segment_durations=(10.0,) * 4,
    )


def write_contact_sheet(output: Path, *, image_format: str = "PNG") -> Path:
    result = make_prototype(image_format=image_format)
    composer = SceneStateComposer()
    sheet = Image.new("RGB", (960, 350), "white")
    draw = ImageDraw.Draw(sheet)
    for index, scene in enumerate(result.scene_plan.scenes[:2]):
        sheet.paste(composer.render_scene(result.registry, scene), (index * 480, 30))
        draw.text((index * 480 + 10, 6), f"Ocean {image_format}: scene {index + 1}", fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG")
    return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image-format", choices=("PNG", "JPEG"), default="PNG")
    args = parser.parse_args()
    print(write_contact_sheet(args.output, image_format=args.image_format))
