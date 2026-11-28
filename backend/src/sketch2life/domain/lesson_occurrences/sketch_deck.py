"""Framework-free rules for immutable Teacher Sketch Deck revisions."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

SKETCH_DECK_STATES: Final = ("GENERATING", "READY", "FAILED", "STALE", "SUPERSEDED")
SKETCH_DECK_TRANSITIONS: Final = frozenset(
    {
        ("GENERATING", "READY"),
        ("GENERATING", "FAILED"),
        ("READY", "STALE"),
        ("READY", "SUPERSEDED"),
    }
)
MIN_GUIDE_STEPS: Final = 4
MAX_GUIDE_STEPS: Final = 8
MAX_LAYOUT_HINT_BYTES: Final = 16_384
MAX_SUBJECT_KNOWLEDGE_CHARACTERS: Final = 10_000
MAX_SUBJECT_KNOWLEDGE_NOTE_CHARACTERS: Final = 240


class SketchDeckRuleError(ValueError):
    """A deterministic invalid-state or output-contract refusal."""

    def __init__(self, code: str, field: str | None = None) -> None:
        self.code = code
        self.field = field
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SketchDeckStep:
    plan_activity_id: str | None
    instruction_group_key: str
    step_index: int
    step_kind: str
    subject_key: str
    short_title: str
    child_facing_prompt: str
    teacher_explanation: str
    bounded_layout_hints: Mapping[str, Any]
    line_sketch_asset_ref: str | None = None
    line_sketch_asset_version: int | None = None
    source_job_ref: str | None = None


@dataclass(frozen=True, slots=True)
class DrawingStepInput:
    action: str
    placement: str


@dataclass(frozen=True, slots=True)
class SketchDeckDrawingInputs:
    review_confirmed: bool
    topic: str
    drawing_steps: tuple[DrawingStepInput, ...]
    subject_knowledge: tuple[str, ...]
    teacher_confirmed_age_band_ref: str | None = None


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def drawing_inputs_payload(value: SketchDeckDrawingInputs) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "review_confirmed": value.review_confirmed,
        "topic": value.topic,
        "drawing_steps": [
            {"action": step.action, "placement": step.placement}
            for step in value.drawing_steps
        ],
        "subject_knowledge": list(value.subject_knowledge),
    }
    if value.teacher_confirmed_age_band_ref is not None:
        payload["teacher_confirmed_age_band_ref"] = value.teacher_confirmed_age_band_ref
    return payload


def revision_content_hash(
    value: SketchDeckDrawingInputs, steps: Sequence[SketchDeckStep]
) -> str:
    return content_hash(
        {
            "review_inputs": drawing_inputs_payload(value),
            "steps_content_hash": steps_content_hash(steps),
        }
    )


def can_transition(old: str, new: str) -> bool:
    return (old, new) in SKETCH_DECK_TRANSITIONS


def validate_drawing_inputs(value: SketchDeckDrawingInputs) -> SketchDeckDrawingInputs:
    if value.review_confirmed is not True:
        raise SketchDeckRuleError("INVALID_REQUEST", "review_confirmed")
    if not MIN_GUIDE_STEPS <= len(value.drawing_steps) <= MAX_GUIDE_STEPS:
        raise SketchDeckRuleError("INVALID_REQUEST", "drawing_steps")
    if (
        not isinstance(value.topic, str)
        or not value.topic.strip()
        or len(value.topic) > 120
        or "\x00" in value.topic
    ):
        raise SketchDeckRuleError("INVALID_REQUEST", "topic")
    if not 1 <= len(value.subject_knowledge) <= 8:
        raise SketchDeckRuleError("INVALID_REQUEST", "subject_knowledge")
    for index, step in enumerate(value.drawing_steps):
        if (
            not isinstance(step.action, str)
            or not step.action.strip()
            or len(step.action) > 240
            or not isinstance(step.placement, str)
            or not step.placement.strip()
            or len(step.placement) > 240
            or "\x00" in step.action
            or "\x00" in step.placement
        ):
            raise SketchDeckRuleError("INVALID_REQUEST", f"drawing_steps[{index}]")
    if any(
        not isinstance(note, str)
        or not note.strip()
        or len(note) > MAX_SUBJECT_KNOWLEDGE_NOTE_CHARACTERS
        or "\x00" in note
        for note in value.subject_knowledge
    ) or sum(len(note) for note in value.subject_knowledge) > MAX_SUBJECT_KNOWLEDGE_CHARACTERS:
        raise SketchDeckRuleError("INVALID_REQUEST", "subject_knowledge")
    return value


def validate_ready_steps(
    plan_activity_ids: Sequence[str], steps: Sequence[SketchDeckStep]
) -> tuple[SketchDeckStep, ...]:
    """Require activity coverage and 4–8 contiguous, bounded steps in each instruction group."""

    if not plan_activity_ids:
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "activities")
    if not steps:
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "steps")

    expected = set(plan_activity_ids)
    covered: set[str] = set()
    groups: dict[str, list[SketchDeckStep]] = defaultdict(list)
    for step in steps:
        if step.plan_activity_id is not None:
            if step.plan_activity_id not in expected:
                raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "plan_activity_id")
            covered.add(step.plan_activity_id)
        groups[step.instruction_group_key].append(step)
        _validate_step(step)

    if covered != expected:
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "activity_coverage")

    for group_key, group_steps in groups.items():
        ordered = sorted(group_steps, key=lambda step: step.step_index)
        if not MIN_GUIDE_STEPS <= len(ordered) <= MAX_GUIDE_STEPS:
            raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "instruction_group")
        if [step.step_index for step in ordered] != list(range(1, len(ordered) + 1)):
            raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "step_index")
        if len({step.plan_activity_id for step in ordered}) != 1:
            raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "instruction_group")
        if any(step.instruction_group_key != group_key for step in ordered):
            raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "instruction_group_key")

    return tuple(
        sorted(steps, key=lambda step: (step.instruction_group_key, step.step_index))
    )


def steps_content_hash(steps: Sequence[SketchDeckStep]) -> str:
    return content_hash(
        [
            {
                "plan_activity_id": step.plan_activity_id,
                "instruction_group_key": step.instruction_group_key,
                "step_index": step.step_index,
                "step_kind": step.step_kind,
                "subject_key": step.subject_key,
                "short_title": step.short_title,
                "child_facing_prompt": step.child_facing_prompt,
                "teacher_explanation": step.teacher_explanation,
                "bounded_layout_hints": dict(step.bounded_layout_hints),
                "line_sketch_asset_ref": step.line_sketch_asset_ref,
                "line_sketch_asset_version": step.line_sketch_asset_version,
                "source_job_ref": step.source_job_ref,
            }
            for step in steps
        ]
    )


def _validate_step(step: SketchDeckStep) -> None:
    bounded_text = (
        ("instruction_group_key", step.instruction_group_key, 80),
        ("step_kind", step.step_kind, 32),
        ("subject_key", step.subject_key, 80),
        ("short_title", step.short_title, 160),
        ("child_facing_prompt", step.child_facing_prompt, 600),
        ("teacher_explanation", step.teacher_explanation, 2000),
    )
    for field, value, maximum in bounded_text:
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", field)
        if "\x00" in value:
            raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", field)
    if step.plan_activity_id is not None and not 0 < len(step.plan_activity_id) <= 36:
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "plan_activity_id")
    if type(step.step_index) is not int or step.step_index < 1:
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "step_index")
    if not isinstance(step.bounded_layout_hints, Mapping):
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "bounded_layout_hints")
    try:
        layout_bytes = canonical_json(dict(step.bounded_layout_hints))
    except (TypeError, ValueError, UnicodeError):
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "bounded_layout_hints") from None
    if len(layout_bytes) > MAX_LAYOUT_HINT_BYTES:
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "bounded_layout_hints")
    if (step.line_sketch_asset_ref is None) != (step.line_sketch_asset_version is None):
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "line_sketch_asset_ref")
    if step.line_sketch_asset_version is not None and step.line_sketch_asset_version < 1:
        raise SketchDeckRuleError("MODAL_OUTPUT_CONTRACT_INVALID", "line_sketch_asset_version")


__all__ = [
    "MAX_GUIDE_STEPS",
    "MAX_LAYOUT_HINT_BYTES",
    "MAX_SUBJECT_KNOWLEDGE_CHARACTERS",
    "MIN_GUIDE_STEPS",
    "SKETCH_DECK_STATES",
    "SKETCH_DECK_TRANSITIONS",
    "DrawingStepInput",
    "SketchDeckDrawingInputs",
    "SketchDeckRuleError",
    "SketchDeckStep",
    "can_transition",
    "content_hash",
    "drawing_inputs_payload",
    "revision_content_hash",
    "steps_content_hash",
    "validate_drawing_inputs",
    "validate_ready_steps",
]
