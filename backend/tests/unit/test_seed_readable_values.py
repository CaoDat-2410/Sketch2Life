"""Keep seed values shown to families and educators natural and free of fixture markers."""

from __future__ import annotations

import re
from dataclasses import fields, is_dataclass
from typing import Any

from tools.seed import (
    data,
    s7b_story_states_data,
    s8_lessons_data,
    s9_classes_data,
    s10_inbox_data,
    s11_org_run_shares_data,
    s12_story_v4a_data,
    s13_system_demo_data,
)

_READABLE_FIELDS = frozenset(
    {
        "action",
        "adult_confirmed_idea",
        "alt_text",
        "body",
        "child_name",
        "description",
        "description_vi",
        "consent_text",
        "decision_text",
        "display_name",
        "drawing_steps_text",
        "drawing_subject",
        "ending",
        "error_message",
        "feedback_text",
        "file_name",
        "idea",
        "interests_summary",
        "instructions_text",
        "materials_text",
        "match_reason",
        "message",
        "middle",
        "name",
        "narration",
        "objectives",
        "opening",
        "observation_notes",
        "preparation_text",
        "reason",
        "reason_text",
        "reply_text",
        "safe_file_name",
        "safe_title",
        "safety_notes",
        "short_text",
        "source_address",
        "source_label",
        "source_title",
        "story_content",
        "subject_label",
        "subject_learning_notes",
        "text",
        "teacher_direction",
        "title",
        "title_vi",
        "topic",
        "typed_idea",
        "visual",
        "visual_prompt",
        "visible_features",
    }
)
_READABLE_CONTAINERS = frozenset(
    {"activities", "character_anchors", "scenes", "story", "story_content", "visible_features"}
)
_BANNED_WORD = re.compile(r"\b(?:seed|test|demo|placeholder|agy|synthetic|lorem)\b", re.I)
_RAW_ID = re.compile(
    r"\bseed-[a-z0-9][a-z0-9-]*\b|"
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.I,
)


def _strings(value: Any, path: str = "", *, all_children: bool = False):
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            child_path = f"{path}.{field.name}" if path else field.name
            yield from _strings(
                getattr(value, field.name),
                child_path,
                all_children=field.name in _READABLE_CONTAINERS,
            )
    elif isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from _strings(
                child,
                child_path,
                all_children=key in _READABLE_CONTAINERS,
            )
    elif isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            yield from _strings(child, f"{path}[{index}]", all_children=all_children)
    elif isinstance(value, str) and (all_children or path.rsplit(".", 1)[-1] in _READABLE_FIELDS):
        yield path, value


def _fixture_values() -> list[tuple[str, str]]:
    roots = [
        ("s1", data.LESSON_SPECS),
        ("s1", data.STORY_RUN_SPECS),
        ("s1", data.organization_rows()),
        ("s1", data.classroom_rows()),
        ("s1", data.managed_profile_rows()),
        ("s1", data.parent_group_rows()),
        ("s7b", vars(s7b_story_states_data)),
        (
            "s7b",
            {
                "subject_label": [
                    result.subject
                    for result in s7b_story_states_data.DRAWING_RESULTS.values()
                ],
                "visible_features": [
                    feature
                    for result in s7b_story_states_data.DRAWING_RESULTS.values()
                    for feature in result.visible_features
                ],
            },
        ),
        ("s8", vars(s8_lessons_data)),
        ("s9", s9_classes_data.lifecycle_profile_rows()),
        ("s9", s9_classes_data.keyed_profile_rows()),
        ("s10", vars(s10_inbox_data)),
        ("s11", vars(s11_org_run_shares_data)),
        ("s12", vars(s12_story_v4a_data)),
        (
            "s12",
            {"reason": s12_story_v4a_data.PARENT_ACTIVITY_MATCH_REASON},
        ),
        (
            "s13",
            {
                "consent_text": s13_system_demo_data.CONSENT_POLICY_TEXT,
                "short_text": s13_system_demo_data.PARENT_CONTEXT_ENTRY_TEXT,
                "feedback_text": s13_system_demo_data.PARENT_FEEDBACK_TEXT,
                "offers": s13_system_demo_data.QUOTA_PRODUCTS,
            },
        ),
    ]
    return [
        (f"{stage}.{path}", value)
        for stage, root in roots
        for path, value in _strings(root)
    ]


def test_readable_seed_values_have_no_fixture_markers_or_raw_ids() -> None:
    values = _fixture_values()
    assert values
    problems = [
        f"{path}: {value}"
        for path, value in values
        if _BANNED_WORD.search(value) or _RAW_ID.search(value)
    ]
    assert not problems, "Readable seed values must be natural Vietnamese: " + "; ".join(problems)


def test_library_lesson_hash_covers_ordered_activities() -> None:
    versions = {row["version_id"]: row for row in data.library_version_rows()}
    activities = data.version_activity_rows()
    for _lesson_key, _visibility, _revision, lesson_versions in data.LESSON_SPECS:
        for version_no, _state, content in lesson_versions:
            row = versions[data.version_id(_lesson_key, version_no)]
            ordered = sorted(
                (
                    activity
                    for activity in activities
                    if activity["version_id"] == row["version_id"]
                ),
                key=lambda activity: activity["activity_order"],
            )
            assert row["structured_content_hash"] == data.canonical_content_hash(content)
            assert [item["activity_json"] for item in ordered] == content["activities"]
