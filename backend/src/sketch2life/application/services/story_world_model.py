"""Build a fail-closed V2 world from reviewed metadata and real manual mask pixels."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageStat

from sketch2life.application.services.story_world_errors import StoryWorldError
from sketch2life.contracts.schemas.story_video import ApprovedStoryPackageV1, StoryScriptSegmentV1
from sketch2life.contracts.schemas.story_world_v2 import (
    NarrationObjectV2,
    ObjectStateV2,
    ReviewedEventV2,
    SourceObjectV2,
    WorldModelV2,
)


@dataclass(frozen=True)
class ManualSourceObject:
    object_id: str
    object_type: str
    mask_png: bytes | None
    identity_review_ref: str | None = None
    reviewed_mask_sha256: str | None = None
    relationship_ids: tuple[str, ...] = ()
    approved_fact_ids: tuple[str, ...] = ()
    confirmed_anchor_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceAssetRegistry:
    world: WorldModelV2
    # Process-local prototype. An asset's bytes are its source pixels + mask, never diffusion.
    asset_png_by_id: dict[str, bytes]
    mask_png_by_id: dict[str, bytes]


def _sha(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def build_source_asset_registry(
    *,
    package: ApprovedStoryPackageV1,
    segments: tuple[StoryScriptSegmentV1, ...],
    source_image_bytes: bytes,
    source_objects: tuple[ManualSourceObject, ...],
    narration_objects: tuple[NarrationObjectV2, ...],
    events: tuple[ReviewedEventV2, ...],
) -> SourceAssetRegistry:
    """Manual/fixture masks are authoritative; missing or dubious masks block V2.

    The returned PNGs are lossless RGBA cutouts of decoded source pixels.
    This function never guesses an object from a box and never invokes SAM/GPU.
    """
    if _sha(source_image_bytes) != package.source_image_sha256:
        raise StoryWorldError("SOURCE_HASH_MISMATCH", "original image differs from package")
    if not source_objects:
        raise StoryWorldError("NEEDS_MASK_REVIEW", "no source objects or masks")
    try:
        source = Image.open(io.BytesIO(source_image_bytes)).convert("RGBA")
    except (OSError, ValueError) as error:
        raise StoryWorldError("SOURCE_IMAGE_INVALID", "cannot decode original image") from error

    segment_by_id = {segment.segment_id: segment for segment in segments}
    if len(segment_by_id) != len(segments):
        raise StoryWorldError("NEEDS_APPROVAL", "duplicate script segment ID")
    source_ids = [item.object_id for item in source_objects]
    added_ids = [item.object_id for item in narration_objects]
    if len(set(source_ids)) != len(source_ids) or set(source_ids) & set(added_ids):
        raise StoryWorldError("NEEDS_MASK_REVIEW", "object identity is ambiguous")
    if len(set(added_ids)) != len(added_ids):
        raise StoryWorldError("NEEDS_APPROVAL", "duplicate added-object identity")
    if any(not set(item.relationship_ids).issubset(source_ids) for item in source_objects):
        raise StoryWorldError("NEEDS_MASK_REVIEW", "relationship references unknown identity")
    known_facts = set().union(*(set(segment.approved_fact_ids) for segment in segments))
    known_anchors = set().union(*(set(segment.confirmed_anchor_ids) for segment in segments))
    if any(not set(item.approved_fact_ids).issubset(known_facts) or not set(
        item.confirmed_anchor_ids
    ).issubset(known_anchors) for item in source_objects):
        raise StoryWorldError("NEEDS_APPROVAL", "source object evidence is not in approved script")

    for added in narration_objects:
        segment = segment_by_id.get(added.segment_id)
        if segment is None or not set(added.approved_fact_ids).issubset(segment.approved_fact_ids):
            raise StoryWorldError("NEEDS_APPROVAL", "added object is not bound to approved facts")
        if added.asset_status != "PENDING":
            raise StoryWorldError("NEEDS_APPROVAL", "new assets need a separate approval flow")

    for event in events:
        segment = segment_by_id.get(event.segment_id)
        if segment is None:
            raise StoryWorldError("NEEDS_APPROVAL", "event has no approved segment")
        if event.source_quote not in segment.text:
            raise StoryWorldError("NEEDS_APPROVAL", "event quote is absent from approved text")
        if not set(event.approved_fact_ids).issubset(segment.approved_fact_ids) or not set(
            event.confirmed_anchor_ids
        ).issubset(segment.confirmed_anchor_ids):
            raise StoryWorldError("NEEDS_APPROVAL", "event provenance is not approved")
        if event.approval_status != "APPROVED":
            raise StoryWorldError("NEEDS_APPROVAL", f"event {event.event_id} needs review")
        if not set(event.object_ids).issubset(set(source_ids) | set(added_ids)):
            raise StoryWorldError("NEEDS_APPROVAL", "event references an unknown object")
        referenced_additions = (
            obj for obj in narration_objects if obj.object_id in event.object_ids
        )
        if any(
            not set(event.approved_fact_ids).intersection(obj.approved_fact_ids)
            or obj.segment_id != event.segment_id
            for obj in referenced_additions
        ):
            raise StoryWorldError("NEEDS_APPROVAL", "new object has no matching approved fact")

    masks: dict[str, Image.Image] = {}
    mask_bytes: dict[str, bytes] = {}
    for source_item in source_objects:
        if (
            not source_item.object_id or not source_item.object_type
            or source_item.mask_png is None or not source_item.identity_review_ref
            or source_item.reviewed_mask_sha256 is None
        ):
            raise StoryWorldError("NEEDS_MASK_REVIEW", "missing mask or reviewed object identity")
        if _sha(source_item.mask_png) != source_item.reviewed_mask_sha256:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "mask differs from reviewed object binding")
        try:
            mask = Image.open(io.BytesIO(source_item.mask_png)).convert("L")
        except (OSError, ValueError) as error:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "cannot decode manual mask") from error
        if mask.size != source.size or mask.getbbox() is None:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "mask dimensions or coverage are invalid")
        histogram = mask.histogram()
        if sum(histogram[1:255]) != 0 or histogram[255] < 4:
            raise StoryWorldError("NEEDS_MASK_REVIEW", "mask must be a real binary object region")
        masks[source_item.object_id] = mask
        mask_bytes[source_item.object_id] = source_item.mask_png
    for index, left_id in enumerate(source_ids):
        for right_id in source_ids[index + 1:]:
            overlap = ImageChops.multiply(masks[left_id], masks[right_id]).histogram()[255]
            smaller = min(masks[left_id].histogram()[255], masks[right_id].histogram()[255])
            if overlap / smaller > 0.05:
                raise StoryWorldError("NEEDS_MASK_REVIEW", "source masks overlap unusually")

    width, height = source.size
    objects: list[SourceObjectV2] = []
    initial: list[ObjectStateV2] = []
    assets: dict[str, bytes] = {}
    for z_index, source_item in enumerate(source_objects):
        mask = masks[source_item.object_id]
        bounds = mask.getbbox()
        assert bounds is not None  # checked above
        cutout = source.crop(bounds)
        cutout.putalpha(ImageChops.multiply(cutout.getchannel("A"), mask.crop(bounds)))
        stream = io.BytesIO()
        cutout.save(stream, format="PNG")
        assets[source_item.object_id] = stream.getvalue()
        red, green, blue = (
            round(channel) for channel in ImageStat.Stat(source, mask).mean[:3]
        )
        objects.append(SourceObjectV2(
            object_id=source_item.object_id,
            object_type=source_item.object_type,
            source_image_ref=package.source_image_ref,
            source_image_sha256=package.source_image_sha256,
            source_mask_ref=f"memory:mask:{_sha(mask_bytes[source_item.object_id])}",
            source_mask_sha256=_sha(mask_bytes[source_item.object_id]),
            asset_ref=f"memory:source-asset:{_sha(assets[source_item.object_id])}",
            asset_sha256=_sha(assets[source_item.object_id]),
            bbox=(bounds[0] / width, bounds[1] / height,
                  bounds[2] / width, bounds[3] / height),
            appearance_colors=(f"#{red:02x}{green:02x}{blue:02x}",),
            relationship_ids=source_item.relationship_ids,
            approved_fact_ids=source_item.approved_fact_ids,
            confirmed_anchor_ids=source_item.confirmed_anchor_ids,
        ))
        initial.append(ObjectStateV2(
            object_id=source_item.object_id,
            x=(bounds[0] + bounds[2]) / (2 * width),
            y=(bounds[1] + bounds[3]) / (2 * height),
            z_index=z_index,
        ))
    world = WorldModelV2(
        package_hash=package.package_hash,
        source_image_ref=package.source_image_ref,
        source_image_sha256=package.source_image_sha256,
        source_width=width,
        source_height=height,
        source_objects=tuple(objects),
        narration_objects=narration_objects,
        events=events,
        initial_states=tuple(initial),
    )
    return SourceAssetRegistry(world=world, asset_png_by_id=assets, mask_png_by_id=mask_bytes)
