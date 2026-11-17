"""Deterministically validate and compile untrusted AI show intent."""

from __future__ import annotations

import logging
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
    PixiShowIntentV2,
    PixiShowPlanV2,
    PixiShowPlanV3,
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
_LOGGER = logging.getLogger("sketch2life.pixi_show_compiler")
_STATIC_SUPPLEMENT_ACTIONS = frozenset(
    {
        PixiShowActionV1.NOTICE,
        PixiShowActionV1.APPROACH,
        PixiShowActionV1.INTERACT,
        PixiShowActionV1.SETTLE,
    }
)


def supported_source_actions_for_rig(
    rig_tier: str,
    part_roles: tuple[str, ...],
) -> tuple[PixiShowActionV1, ...]:
    """Return source actions already supported by the verified rig package."""
    normalized_roles = {role.casefold().replace("_", "-") for role in part_roles}
    if rig_tier == "FULL_AUTO_RIG":
        actions = [
            PixiShowActionV1.NOTICE,
            PixiShowActionV1.APPROACH,
            PixiShowActionV1.INTERACT,
            PixiShowActionV1.SETTLE,
        ]
        actions.extend(
            action
            for action, required_roles in _REQUIRED_PART_ROLES.items()
            if normalized_roles & required_roles
        )
        return tuple(actions)
    if rig_tier == "CUTOUT_MICRO_MOTION":
        return (
            PixiShowActionV1.NOTICE,
            PixiShowActionV1.APPROACH,
            PixiShowActionV1.INTERACT,
            PixiShowActionV1.SETTLE,
        )
    return (PixiShowActionV1.NOTICE, PixiShowActionV1.SETTLE)


def supported_render_strategies_for_rig(
    rig_tier: str,
    *,
    has_environment_candidate: bool,
) -> tuple[str, ...]:
    """Return strategies accepted by the existing adaptive compiler for this tier."""
    if rig_tier == "FULL_AUTO_RIG":
        return ("FULL_AUTO_RIG",)
    if rig_tier == "CUTOUT_MICRO_MOTION":
        strategies = ["CUTOUT_MICRO_MOTION", "STATIC_SOURCE"]
        if has_environment_candidate:
            strategies.insert(0, "CUTOUT_TOPIC_SCENE")
        return tuple(strategies)
    return ("STATIC_SOURCE",)


def supported_source_actions_for_strategy(
    rig_tier: str,
    part_roles: tuple[str, ...],
    render_strategy: str,
) -> tuple[PixiShowActionV1, ...]:
    """Narrow rig-supported actions further for the selected rendering strategy."""
    if render_strategy == "STATIC_SOURCE":
        return (PixiShowActionV1.NOTICE, PixiShowActionV1.SETTLE)
    if render_strategy == "FULL_AUTO_RIG" and rig_tier == "FULL_AUTO_RIG":
        return supported_source_actions_for_rig(rig_tier, part_roles)
    if render_strategy in {"CUTOUT_TOPIC_SCENE", "CUTOUT_MICRO_MOTION"} and (
        rig_tier == "CUTOUT_MICRO_MOTION"
    ):
        return supported_source_actions_for_rig(rig_tier, part_roles)
    return ()


def _reject_capability(reason: str) -> None:
    """Log only a closed, non-user-derived reason before returning the same safe error."""
    _LOGGER.warning("pixi_show_capability_rejected reason=%s", reason)
    raise PixiShowPlannerUnavailable("BEHAVIOR_CAPABILITY_UNSUPPORTED")


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
    supported_actions = set(
        supported_source_actions_for_rig(request.rig_tier, request.part_roles)
    )
    for beat in intent.beats:
        if beat.target_role == "SUPPLEMENTAL_ASSET":
            if beat.asset_id not in selected_ids:
                raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
            if beat.action not in _STATIC_SUPPLEMENT_ACTIONS:
                # Catalog entries are currently static poses, never walk/flight cycles.
                _reject_capability("supplemental_motion_not_supported")
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
            _reject_capability("action_behavior_mismatch")
        required_roles = _REQUIRED_PART_ROLES.get(beat.action)
        if beat.action not in supported_actions:
            if required_roles is not None and request.rig_tier != "FULL_AUTO_RIG":
                _reject_capability("articulated_action_requires_full_rig")
            if required_roles is not None:
                _reject_capability("required_part_role_missing")
            _reject_capability("source_action_not_supported_by_rig_tier")

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


def compile_adaptive_pixi_show_plan(
    *,
    request: PixiShowPlanningRequest,
    intent: PixiShowIntentV2,
    plan_id: str | None = None,
) -> PixiShowPlanV3:
    """Validate the selected strategy and exact environment candidate before delivery."""
    if not request.chosen_topic_labels:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
    if request.rig_tier == "FULL_AUTO_RIG":
        if intent.render_strategy != "FULL_AUTO_RIG" or intent.scene_theme_asset_id is not None:
            _reject_capability("full_rig_strategy_mismatch")
        if not any(beat.action in _BEHAVIOR_FOR_ACTION for beat in intent.beats):
            _reject_capability("full_rig_missing_part_motion")
    elif intent.render_strategy == "FULL_AUTO_RIG":
        _reject_capability("unverified_full_rig_strategy")
    elif intent.render_strategy == "CUTOUT_TOPIC_SCENE":
        if request.rig_tier != "CUTOUT_MICRO_MOTION":
            _reject_capability("topic_scene_requires_verified_cutout")
    elif intent.render_strategy == "CUTOUT_MICRO_MOTION":
        if request.rig_tier != "CUTOUT_MICRO_MOTION" or intent.scene_theme_asset_id is not None:
            _reject_capability("cutout_motion_requires_verified_cutout")
    elif intent.scene_theme_asset_id is not None:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")

    if intent.scene_theme_asset_id is not None:
        candidate = next(
            (
                item
                for item in request.candidate_assets
                if item.asset_id == intent.scene_theme_asset_id
            ),
            None,
        )
        if candidate is None or candidate.role != "ENVIRONMENT":
            raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
    elif intent.render_strategy == "CUTOUT_TOPIC_SCENE":
        raise PixiShowPlannerUnavailable("NO_COMPATIBLE_ASSET")

    selected_candidates = {
        item.asset_id: item for item in request.candidate_assets
    }
    if any(
        selected_candidates.get(asset_id) is None
        or selected_candidates[asset_id].role not in {"PROP", "EFFECT"}
        for asset_id in intent.selected_asset_ids
    ):
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
    allowed_strategy_actions = set(
        supported_source_actions_for_strategy(
            request.rig_tier,
            request.part_roles,
            intent.render_strategy,
        )
    )
    if any(
        beat.target_role == "SOURCE_SUBJECT" and beat.action not in allowed_strategy_actions
        for beat in intent.beats
    ):
        _reject_capability("source_action_not_supported_by_render_strategy")
    if intent.scene_theme_asset_id in set(intent.selected_asset_ids):
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")
    chosen_topic_label = request.chosen_topic_labels[0].strip()
    if not chosen_topic_label:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT")

    try:
        base_intent = PixiShowIntentV1.model_validate(
            intent.model_dump(
                mode="python",
                by_alias=True,
                exclude={"render_strategy", "scene_theme_asset_id"},
            )
        )
    except ValidationError:
        raise PixiShowPlannerUnavailable("PLANNER_INVALID_RESULT") from None
    base_plan = compile_pixi_show_plan(request=request, intent=base_intent, plan_id=plan_id)
    try:
        selected_total = len(base_plan.selected_asset_ids) + (
            1 if intent.scene_theme_asset_id is not None else 0
        )
        if selected_total > 3:
            raise PixiShowPlannerUnavailable("NO_COMPATIBLE_ASSET")
        return PixiShowPlanV3.model_validate(
            {
                **base_plan.model_dump(mode="python", by_alias=True),
                "contractName": "PixiShowPlanV3",
                "contractVersion": "3.0",
                "renderStrategy": intent.render_strategy,
                "chosenTopicLabel": chosen_topic_label,
                "sceneThemeAssetId": intent.scene_theme_asset_id,
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


__all__ = [
    "compile_adaptive_pixi_show_plan",
    "compile_pixi_show_plan",
    "supported_render_strategies_for_rig",
    "supported_source_actions_for_rig",
    "supported_source_actions_for_strategy",
]
