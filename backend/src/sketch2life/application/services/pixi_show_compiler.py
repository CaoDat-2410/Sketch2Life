"""Deterministically validate and compile untrusted AI show intent."""

from __future__ import annotations

import unicodedata
from uuid import uuid4

from pydantic import ValidationError

from sketch2life.application.ports.pixi_show_planner import (
    PixiShowPlannerUnavailable,
    PixiShowPlanningRequest,
)
from sketch2life.contracts.schemas.pixi_show import (
    PixiBehaviorClassV1,
    PixiShowActionV1,
    PixiShowIntentV1,
    PixiShowPlanV2,
    PixiSubjectHintV1,
)

_BEHAVIOR_BY_HINT: dict[PixiSubjectHintV1, frozenset[PixiBehaviorClassV1]] = {
    PixiSubjectHintV1.BIRD: frozenset({PixiBehaviorClassV1.FLYER, PixiBehaviorClassV1.WALKER}),
    PixiSubjectHintV1.INSECT: frozenset({PixiBehaviorClassV1.FLYER, PixiBehaviorClassV1.CRAWLER}),
    PixiSubjectHintV1.FISH: frozenset({PixiBehaviorClassV1.SWIMMER}),
    PixiSubjectHintV1.QUADRUPED: frozenset({PixiBehaviorClassV1.WALKER}),
    PixiSubjectHintV1.BIPED: frozenset({PixiBehaviorClassV1.WALKER}),
    PixiSubjectHintV1.PLANT: frozenset({PixiBehaviorClassV1.STATIONARY}),
    PixiSubjectHintV1.VEHICLE: frozenset(
        {PixiBehaviorClassV1.ROLLER, PixiBehaviorClassV1.STATIONARY}
    ),
    PixiSubjectHintV1.OBJECT: frozenset(
        {PixiBehaviorClassV1.STATIONARY, PixiBehaviorClassV1.ROLLER}
    ),
    PixiSubjectHintV1.UNKNOWN: frozenset({PixiBehaviorClassV1.STATIONARY}),
}

_REQUIRED_PART_ROLES: dict[PixiShowActionV1, frozenset[str]] = {
    PixiShowActionV1.WALK_STEP: frozenset(
        {"leg", "legs", "left-leg", "right-leg", "fore-leg", "hind-leg"}
    ),
    PixiShowActionV1.FLAP: frozenset({"wing", "left-wing", "right-wing"}),
    PixiShowActionV1.GLIDE: frozenset({"wing", "left-wing", "right-wing"}),
    PixiShowActionV1.SWIM: frozenset({"tail", "fin", "left-fin", "right-fin"}),
    PixiShowActionV1.SLITHER: frozenset({"body", "tail"}),
    PixiShowActionV1.ROLL: frozenset({"wheel", "left-wheel", "right-wheel"}),
}
_BEHAVIOR_FOR_ACTION: dict[PixiShowActionV1, PixiBehaviorClassV1] = {
    PixiShowActionV1.WALK_STEP: PixiBehaviorClassV1.WALKER,
    PixiShowActionV1.FLAP: PixiBehaviorClassV1.FLYER,
    PixiShowActionV1.GLIDE: PixiBehaviorClassV1.FLYER,
    PixiShowActionV1.SWIM: PixiBehaviorClassV1.SWIMMER,
    PixiShowActionV1.SLITHER: PixiBehaviorClassV1.CRAWLER,
    PixiShowActionV1.ROLL: PixiBehaviorClassV1.ROLLER,
}
_STATIC_SUPPLEMENT_ACTIONS = frozenset(
    {
        PixiShowActionV1.NOTICE,
        PixiShowActionV1.APPROACH,
        PixiShowActionV1.INTERACT,
        PixiShowActionV1.SETTLE,
    }
)


def compile_pixi_show_plan(
    *,
    request: PixiShowPlanningRequest,
    intent: PixiShowIntentV1,
    plan_id: str | None = None,
) -> PixiShowPlanV2:
    """Reject Gate-A drift, unsupported motion, and any model-invented asset ID."""
    expected_hint = _confirmed_subject_hint(request.confirmed_subject_label, request.subject_tags)
    if intent.visual_subject_hint_id not in {expected_hint, PixiSubjectHintV1.UNKNOWN}:
        raise PixiShowPlannerUnavailable("SUBJECT_RECONFIRMATION_REQUIRED")
    if expected_hint is PixiSubjectHintV1.UNKNOWN and (
        intent.visual_subject_hint_id is not PixiSubjectHintV1.UNKNOWN
    ):
        raise PixiShowPlannerUnavailable("SUBJECT_RECONFIRMATION_REQUIRED")
    if intent.behavior_class not in _BEHAVIOR_BY_HINT[expected_hint]:
        raise PixiShowPlannerUnavailable("BEHAVIOR_CAPABILITY_UNSUPPORTED")
    if intent.duration_seconds != request.renderer_duration_seconds:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")

    candidate_ids = {asset.asset_id for asset in request.candidate_assets}
    selected_ids = set(intent.selected_asset_ids)
    if not selected_ids <= candidate_ids:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
    if request.subject_region is None:
        raise PixiShowPlannerUnavailable("SUBJECT_CROP_UNAVAILABLE")

    referenced_assets: set[str] = set()
    rig_roles = {role.casefold().replace("_", "-") for role in request.part_roles}
    for beat in intent.beats:
        if beat.target_role == "SUPPLEMENTAL_ASSET":
            if beat.asset_id not in selected_ids:
                raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
            if beat.action not in _STATIC_SUPPLEMENT_ACTIONS:
                # Catalog entries are currently static poses, never walk/flight cycles.
                raise PixiShowPlannerUnavailable("BEHAVIOR_CAPABILITY_UNSUPPORTED")
            region = request.subject_region
            if not 0.12 <= beat.x <= 0.88 or not 0.12 <= beat.y <= 0.88:
                raise PixiShowPlannerUnavailable("NO_COMPATIBLE_ASSET")
            if (
                region.x - 0.14 <= beat.x <= region.x + region.width + 0.14
                and region.y - 0.14 <= beat.y <= region.y + region.height + 0.14
            ):
                # Static companions stay outside a padded bound around the child's subject.
                raise PixiShowPlannerUnavailable("NO_COMPATIBLE_ASSET")
            referenced_assets.add(beat.asset_id)
            continue

        required_behavior = _BEHAVIOR_FOR_ACTION.get(beat.action)
        if required_behavior is not None and required_behavior is not intent.behavior_class:
            raise PixiShowPlannerUnavailable("BEHAVIOR_CAPABILITY_UNSUPPORTED")
        required_roles = _REQUIRED_PART_ROLES.get(beat.action)
        if required_roles is not None and not (rig_roles & required_roles):
            raise PixiShowPlannerUnavailable("BEHAVIOR_CAPABILITY_UNSUPPORTED")
        if required_roles is not None and request.rig_tier != "FULL_AUTO_RIG":
            raise PixiShowPlannerUnavailable("BEHAVIOR_CAPABILITY_UNSUPPORTED")

    if referenced_assets != selected_ids:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
    try:
        return PixiShowPlanV2.model_validate(
            {
                "contractName": "PixiShowPlanV2",
                "contractVersion": "2.0",
                "planId": plan_id or f"show-{uuid4().hex}",
                "sessionId": request.session_id,
                "packageId": request.package_id,
                "sourceSha256": request.source_sha256,
                "sourceSubjectRegion": request.subject_region,
                "experienceSpecRef": {
                    "id": request.experience_spec_id,
                    "version": request.experience_spec_version,
                },
                "confirmedSubjectId": request.confirmed_subject_id,
                "visualSubjectHintId": intent.visual_subject_hint_id,
                "behaviorClass": intent.behavior_class,
                "durationSeconds": intent.duration_seconds,
                "selectedAssetIds": intent.selected_asset_ids,
                "beats": intent.beats,
                "endingStill": intent.ending_still,
            }
        )
    except ValidationError:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT") from None


def _confirmed_subject_hint(label: str, tags: tuple[str, ...]) -> PixiSubjectHintV1:
    normalized = _normalize(" ".join((label, *tags)))
    aliases: tuple[tuple[PixiSubjectHintV1, tuple[str, ...]], ...] = (
        (
            PixiSubjectHintV1.BIRD,
            ("bird", "chim", "avian", "chicken", "hen", "rooster", "con ga", "ga"),
        ),
        (
            PixiSubjectHintV1.INSECT,
            ("insect", "butterfly", "buom", "butterflies", "bee", "ong", "caterpillar"),
        ),
        (PixiSubjectHintV1.FISH, ("fish", "ca", "fishes", "ca chep", "ca vang")),
        (
            PixiSubjectHintV1.QUADRUPED,
            (
                "quadruped", "dog", "cho", "cat", "meo", "deer", "huou", "horse", "ngua",
                "cow", "bo", "elephant", "voi",
            ),
        ),
        (
            PixiSubjectHintV1.BIPED,
            ("biped", "person", "people", "be", "girl", "boy", "nguoi", "child", "tre em"),
        ),
        (
            PixiSubjectHintV1.PLANT,
            (
                "plant", "flower", "hoa", "tree", "cay", "leaf", "la", "carrot", "ca rot",
                "rau cu",
            ),
        ),
        (PixiSubjectHintV1.VEHICLE, ("vehicle", "car", "truck", "xe", "o to", "oto")),
        (PixiSubjectHintV1.OBJECT, ("object", "fossil", "hoa thach", "do vat", "vat the")),
    )
    matches = [
        (len(phrase.split()), hint)
        for hint, words in aliases
        for phrase in words
        if _contains_token_phrase(normalized, phrase)
    ]
    if not matches:
        return PixiSubjectHintV1.UNKNOWN

    # Prefer the most specific whole-token phrase: "cà rốt" must not be
    # classified as fish merely because both normalize to the token "ca".
    longest = max(length for length, _hint in matches)
    most_specific = {hint for length, hint in matches if length == longest}
    return next(iter(most_specific)) if len(most_specific) == 1 else PixiSubjectHintV1.UNKNOWN


def _normalize(value: str) -> str:
    lowered = value.casefold().replace("đ", "d")
    decomposed = unicodedata.normalize("NFKD", lowered)
    unaccented = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(unaccented.split())


def _contains_token_phrase(value: str, phrase: str) -> bool:
    return f" {phrase} " in f" {value} "


__all__ = ["compile_pixi_show_plan"]
