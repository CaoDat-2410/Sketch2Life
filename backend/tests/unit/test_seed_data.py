"""Pure checks of the S1 seed data (FEAT-066 SEED-1, package §4 test 6). No database."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.lesson_library import LessonContentInputV1
from sketch2life.contracts.schemas.parent_story_runs import ParentRunContextSnapshotV1
from sketch2life.domain.lesson_library.model import canonical_content_hash, validate_content
from sketch2life.infrastructure.persistence.parent_story_repository import (
    _principal_scope_ref,
    _sha256_json,
)
from tools.seed import data

ALL_ROWS = {
    "be1_organizations": data.organization_rows,
    "be1_adult_identities": data.adult_rows,
    "be1_organization_assignments": data.assignment_rows,
    "be1_classrooms": data.classroom_rows,
    "be1_managed_profiles": data.managed_profile_rows,
    "be1_enrollments": data.enrollment_rows,
    "be1_parent_groups": data.parent_group_rows,
    "be1_parent_group_members": data.parent_group_member_rows,
    "parent.child_profiles": data.child_profile_rows,
    "parent.profile_revisions": data.profile_revision_rows,
    "lesson.library_items": data.library_item_rows,
    "lesson.library_versions": data.library_version_rows,
    "lesson.version_activities": data.version_activity_rows,
    "lesson.access_grants": data.access_grant_rows,
    "story.runs": data.story_run_rows,
    "story.run_inputs": data.run_input_rows,
}
TEXT_ID_COLUMNS = {
    "be1_organizations": "organization_id",
    "be1_adult_identities": "subject",
    "be1_classrooms": "class_id",
    "be1_managed_profiles": "child_id",
    "be1_parent_groups": "parent_group_id",
    "be1_parent_group_members": "membership_id",
    "lesson.library_items": "lesson_id",
    "lesson.library_versions": "version_id",
    "lesson.version_activities": "activity_id",
    "lesson.access_grants": "access_grant_id",
}
UUID_ID_COLUMNS = {
    "be1_organization_assignments": "assignment_id",
    "be1_enrollments": "enrollment_id",
    "parent.child_profiles": "parent_profile_id",
    "parent.profile_revisions": "profile_revision_id",
    "story.runs": "run_id",
    "story.run_inputs": "run_input_id",
}


def test_counts_match_expected() -> None:
    assert data.expected_counts() == data.EXPECTED_COUNTS
    assert {name: len(rows()) for name, rows in ALL_ROWS.items()} == data.EXPECTED_COUNTS


@pytest.mark.parametrize("table", sorted(TEXT_ID_COLUMNS))
def test_text_ids_are_marked_and_short(table: str) -> None:
    ids = [row[TEXT_ID_COLUMNS[table]] for row in ALL_ROWS[table]()]
    assert len(ids) == len(set(ids))
    for value in ids:
        assert value.startswith("seed-")
        assert len(value) <= 36


@pytest.mark.parametrize("table", sorted(UUID_ID_COLUMNS))
def test_uuid_ids_are_uuidv5_and_unique(table: str) -> None:
    ids = [str(row[UUID_ID_COLUMNS[table]]) for row in ALL_ROWS[table]()]
    assert len(ids) == len(set(ids))
    for value in ids:
        assert uuid.UUID(value).version == 5


def test_account_ids_are_uuidv5_and_unique() -> None:
    ids = [row["account_id"] for row in data.adult_rows()]
    assert len(ids) == len(set(ids))
    assert all(uuid.UUID(value).version == 5 for value in ids)


def test_rows_are_deterministic() -> None:
    for rows in ALL_ROWS.values():
        assert rows() == rows()
    assert data.seed_uuid("x") == uuid.uuid5(data.SEED_NAMESPACE, "x")


def test_display_names_are_marked() -> None:
    for rows in (
        data.organization_rows,
        data.classroom_rows,
        data.managed_profile_rows,
        data.parent_group_rows,
        data.profile_revision_rows,
    ):
        for row in rows():
            assert row["display_name"].startswith("[SEED]")
    for row in data.library_version_rows():
        assert row["content_json"]["title"].startswith("[SEED]")


def test_adult_roles() -> None:
    roles = [row["account_role"] for row in data.adult_rows()]
    assert set(roles) == {"platform_admin", "school_manager", "teacher", "parent"}
    assert all(row["role_revision"] == 1 for row in data.adult_rows())
    assert len({row["subject"] for row in data.adult_rows()}) == len(roles)


def test_class_profiles_are_synthetic() -> None:
    for row in data.managed_profile_rows():
        assert 36 <= row["age_months"] <= 120
        assert row["data_origin"] == "SYNTHETIC_DEV"
        assert row["consent_id"] is None and row["consent_purpose_ref"] is None
        assert row["age_source"] == "SYNTHETIC_FIXTURE"


def test_foreign_references_resolve() -> None:
    orgs = {row["organization_id"] for row in data.organization_rows()}
    subjects = {row["subject"] for row in data.adult_rows()}
    classes = {row["class_id"]: row["organization_id"] for row in data.classroom_rows()}
    for row in data.assignment_rows():
        assert row["organization_id"] in orgs and row["subject"] in subjects
        assert row["class_id"] is None or classes[row["class_id"]] == row["organization_id"]
    for row in data.managed_profile_rows():
        assert classes[row["class_id"]] == row["organization_id"]
    for row in data.parent_group_member_rows():
        assert row["parent_principal_ref"] in subjects
        assert row["invited_by"] in subjects
    versions = {row["version_id"]: row["lesson_id"] for row in data.library_version_rows()}
    for row in data.access_grant_rows():
        assert versions[row["version_id"]] == row["lesson_id"]
        if row["audience_kind"] == "PUBLIC":
            assert row["audience_ref"] is None
        else:
            assert row["audience_ref"] is not None
        if row["audience_kind"] == "PRINCIPAL":
            assert row["audience_ref"] in subjects
    for row in data.library_item_rows():
        assert versions[row["current_version_id"]] == row["lesson_id"]


def test_org_a_teacher_shapes() -> None:
    org_a = [row for row in data.assignment_rows() if row["organization_id"] == "seed-org-a"]
    taught = {row["class_id"] for row in org_a if row["role"] == "teacher" and row["class_id"]}
    assert data.class_id("a", 4) not in taught
    assert any(row["role"] == "teacher" and row["class_id"] is None for row in org_a)
    no_org = [
        row for row in data.assignment_rows() if row["subject"] == data.NO_ORG_TEACHER_SUBJECT
    ]
    assert no_org == []


def test_parent_profiles_and_revisions() -> None:
    revisions = data.profile_revision_rows()
    for profile in data.child_profile_rows():
        own = [row for row in revisions if row["parent_profile_id"] == profile["parent_profile_id"]]
        assert max(row["revision_no"] for row in own) == profile["current_revision_no"]
        assert profile["data_origin"] == "SYNTHETIC_DEV"
    for row in revisions:
        assert 36 <= row["age_months"] <= 120
        assert row["age_band_ref"] is None and row["age_band_version"] is None
        assert len(row["revision_hash"]) == 64


@pytest.mark.parametrize("spec", data.LESSON_SPECS, ids=lambda spec: spec[0])
def test_lesson_content_is_valid(spec: tuple[Any, ...]) -> None:
    for _number, _state, content in spec[3]:
        validate_content(content)
        LessonContentInputV1.model_validate(content)


def test_lesson_versions_store_like_the_product() -> None:
    activities = data.version_activity_rows()
    for key, _internal, _revision, versions in data.LESSON_SPECS:
        for number, _state, content in versions:
            row = next(
                item
                for item in data.library_version_rows()
                if item["version_id"] == data.version_id(key, number)
            )
            assert "activities" not in row["content_json"]
            assert row["structured_content_hash"] == canonical_content_hash(content)
            own = [item for item in activities if item["version_id"] == row["version_id"]]
            assert [item["activity_order"] for item in own] == list(
                range(1, len(content["activities"]) + 1)
            )
            assert [item["activity_json"] for item in own] == content["activities"]


def test_public_grant_binds_a_pending_version() -> None:
    states = {row["version_id"]: row["review_state"] for row in data.library_version_rows()}
    for grant in data.access_grant_rows():
        if grant["audience_kind"] == "PUBLIC":
            assert states[grant["version_id"]] == "PENDING_REVIEW"


def test_expected_visibility() -> None:
    items = {row["lesson_id"]: row["visibility"] for row in data.library_item_rows()}
    assert items == {data.lesson_id(key): value for key, value in data.EXPECTED_VISIBILITY.items()}
    assert data.EXPECTED_VISIBILITY == {"l1": "SCHOOL", "l2": "PRIVATE", "l3": "SCHOOL"}


@pytest.mark.parametrize(
    ("kinds", "internal", "expected"),
    [
        ((), "PRIVATE", "PRIVATE"),
        ((), "SCHOOL", "SCHOOL"),
        (("ORGANIZATION",), "PRIVATE", "SCHOOL"),
        (("PARENT_GROUP", "ORGANIZATION"), "PRIVATE", "SELECTED_AUDIENCE"),
        (("PRINCIPAL",), "SCHOOL", "SELECTED_AUDIENCE"),
        (("PUBLIC", "PRINCIPAL"), "PRIVATE", "PUBLIC"),
    ],
)
def test_visibility_rule(kinds: tuple[str, ...], internal: str, expected: str) -> None:
    grants = [{"audience_kind": kind, "state": "ACTIVE", "expires_at": None} for kind in kinds]
    assert data.derive_visibility(internal, grants, data.SEED_TIME) == expected


def test_visibility_ignores_inactive_and_expired_grants() -> None:
    grants = [
        {"audience_kind": "PUBLIC", "state": "REVOKED", "expires_at": None},
        {"audience_kind": "ORGANIZATION", "state": "ACTIVE", "expires_at": data.SEED_TIME},
    ]
    assert data.derive_visibility("PRIVATE", grants, data.SEED_TIME) == "PRIVATE"


def test_one_active_run_per_parent_account() -> None:
    active = [
        row["active_owner_parent_account_id"]
        for row in data.story_run_rows()
        if row["active_owner_parent_account_id"] is not None
    ]
    assert len(active) == len(set(active))
    accounts = {row["account_id"] for row in data.adult_rows() if row["account_role"] == "parent"}
    assert set(active) <= accounts
    for row in data.story_run_rows():
        is_active = row["run_state"] in {"INPUT_PROCESSING", "PREPARATION_REVIEW"}
        assert (row["active_owner_parent_account_id"] is not None) == is_active


def test_every_run_has_its_current_input() -> None:
    inputs = {(row["run_id"], row["input_revision"]) for row in data.run_input_rows()}
    for row in data.story_run_rows():
        assert row["current_input_revision"] == 1
        assert (row["run_id"], row["current_input_revision"]) in inputs
        assert row["revision"] == 1 and row["version"] == 1 and row["retryable"] is False
        if row["run_state"] == "FAILED":
            assert row["job_state"] == "FAILED" and row["error_code"]
        else:
            assert row["job_state"] is None and row["error_code"] is None


def test_runs_point_at_parent_profiles() -> None:
    profiles = {str(row["parent_profile_id"]) for row in data.child_profile_rows()}
    for row in data.story_run_rows():
        assert row["profile_ref"] in profiles
        assert 36 <= row["child_age_months"] <= 120


@pytest.mark.parametrize("parent_key", sorted(data.PARENT_SUBJECTS))
def test_scope_ref_parity(parent_key: str) -> None:
    subject = data.PARENT_SUBJECTS[parent_key]
    principal = VerifiedPrincipal(
        subject=subject, issuer=data.SEED_ISSUER, roles=frozenset({"parent"})
    )
    assert data.principal_scope_ref(data.SEED_ISSUER, subject) == _principal_scope_ref(principal)


def test_context_snapshots() -> None:
    for row in data.run_input_rows():
        snapshot = row["context_snapshot"]
        ParentRunContextSnapshotV1.model_validate(snapshot)
        assert row["context_snapshot_sha256"] == _sha256_json(snapshot)
        assert data.sha256_json(snapshot) == _sha256_json(snapshot)
        assert row["source_profile_revision_ref"] == snapshot["profile_revision_ref"]
        if row["typed_idea"] is None:
            assert row["idea_source"] is None and snapshot["adult_confirmed_idea"] == ""
        else:
            assert row["idea_source"] == "TEXT"
            assert row["typed_idea"] == snapshot["adult_confirmed_idea"] != ""
        assert "lesson_pin_snapshot" not in row


# --- SEED-7a additions (package Draft 3 test T1) ----------------------------------------


def test_p4_and_p5_profiles_are_synthetic_and_in_range() -> None:
    specs = {spec[0]: spec for spec in data.PARENT_PROFILE_SPECS}
    for profile_key, parent_key, age in (("k4", "p4", 72), ("k5", "p5", 96)):
        _key, owner, state, revisions = specs[profile_key]
        assert owner == parent_key
        assert state == "ACTIVE"
        assert len(revisions) == 1
        name, months, _interests = revisions[0]
        assert name.startswith("[SEED]")
        assert months == age
        assert 36 <= months <= 120
    assert len(data.child_profile_rows()) == 5


def test_p4_and_p5_have_no_s1_run() -> None:
    owners = {spec[1] for spec in data.STORY_RUN_SPECS}
    assert "p4" not in owners and "p5" not in owners


def test_counts_include_p4_and_p5() -> None:
    assert data.EXPECTED_COUNTS["be1_adult_identities"] == 25
    assert data.EXPECTED_COUNTS["parent.child_profiles"] == 5
    assert data.EXPECTED_COUNTS["parent.profile_revisions"] == 7
    assert data.expected_counts() == data.EXPECTED_COUNTS


def test_s7a_specs_and_keys() -> None:
    assert [spec[0] for spec in data.S7A_RUN_SPECS] == ["p4", "p5"]
    for parent_key, profile_key, topic, idea in data.S7A_RUN_SPECS:
        assert parent_key in data.PARENT_SUBJECTS
        assert profile_key in {spec[0] for spec in data.PARENT_PROFILE_SPECS}
        assert 0 < len(topic) <= 120 and topic.strip()
        assert 0 < len(idea) <= 500
        assert data.s7a_create_key(parent_key) != data.s7a_confirm_key(parent_key)
    assert data.EXPECTED_S7A_COUNTS == {
        "story.runs": 2,
        "story.run_inputs": 2,
        "story.command_receipts": 4,
    }
