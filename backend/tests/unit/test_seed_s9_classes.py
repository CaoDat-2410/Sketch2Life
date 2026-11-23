"""Pure fixture and orchestration checks for the S9 class stage."""

from __future__ import annotations

import re

import pytest

from sketch2life.contracts.schemas.be1_runtime import CreateProfileRequest, MoveProfileRequest
from tools.seed import data, s9_classes
from tools.seed import s9_classes_data as fixtures
from tools.seed.guard import SeedGuardError
from tools.seed.stage_common import check_database_prefix


def test_class_lifecycle_and_profile_fixtures_are_stable_and_synthetic() -> None:
    assert [(row.class_number, row.target_state, row.command) for row in fixtures.CLASS_STATES] == [
        (5, "archived", "archive"),
        (6, "suspended", "suspend"),
    ]
    assert [data.class_display_name("a", row.class_number) for row in fixtures.CLASS_STATES] == [
        "Lớp Mầm 2",
        "Lớp Chồi 2",
    ]
    profiles = fixtures.lifecycle_profile_rows() + fixtures.keyed_profile_rows()
    s1_profiles = data.managed_profile_rows()
    assert len(profiles) == 7
    assert len({row["child_id"] for row in profiles}) == len(profiles)
    assert len({row["display_name"] for row in s1_profiles + profiles}) == len(
        s1_profiles + profiles
    )
    for row in profiles:
        low, high = data.CLASS_PROFILE_AGE_RANGES[
            data.class_age_group("a", int(str(row["class_id"]).rsplit("-", 1)[1]))
        ]
        assert low <= row["age_months"] <= high
        assert row["age_source"] == "SYNTHETIC_FIXTURE"
        assert row["data_origin"] == "SYNTHETIC_DEV"
        assert row["consent_id"] is None and row["consent_purpose_ref"] is None
    for child_id in fixtures.PROFILE_CREATE_CHILD_IDS:
        assert child_id.startswith("seed-ch-a-1-") and len(child_id) <= 36
    assert fixtures.PROFILE_CREATE_CHILD_IDS[0] == fixtures.MOVED_CHILD_ID
    assert fixtures.MOVE_FROM_CLASS_NUMBER == 1 and fixtures.MOVE_TO_CLASS_NUMBER == 3
    keyed = fixtures.keyed_profile_rows()
    assert all(row["display_name"].startswith("Synthetic ") for row in keyed)
    assert [row["child_id"] for row in keyed] == list(fixtures.PROFILE_CREATE_CHILD_IDS)


def test_expected_counts_and_route_idempotency_keys_are_valid() -> None:
    assert fixtures.EXPECTED == {
        "be1_classrooms": 4,
        "be1_organization_assignments": 1,
        "be1_managed_profiles": 7,
        "be1_enrollments": 8,
        "be1_command_receipts": 7,
        "core_audit_entries": 7,
        "core_aggregate_revisions": 6,
        "core_outbox_events": 7,
    }
    assert all(re.fullmatch(r"[A-Za-z0-9_]+", name) for name in fixtures.EXPECTED)
    keys = [fixtures.class_state_key(row) for row in fixtures.CLASS_STATES]
    keys += [
        fixtures.profile_create_key(child_id) for child_id in fixtures.PROFILE_CREATE_CHILD_IDS
    ]
    keys.append(fixtures.move_key())
    assert len(keys) == len(set(keys))
    assert all(re.fullmatch(r"[A-Za-z0-9:_-]+", key) for key in keys)
    assert fixtures.stage_enrollment_id(fixtures.MOVED_CHILD_ID) != fixtures.move_enrollment_id()


def test_route_fingerprints_are_deterministic_and_bind_revisions() -> None:
    assert s9_classes._class_state_expected_revision(fixtures.CLASS_STATES[0]) == 1
    assert s9_classes._class_state_expected_revision(fixtures.CLASS_STATES[1]) == 2
    assert s9_classes._state_fingerprint("archive", 1) == s9_classes._state_fingerprint(
        "archive", 1
    )
    assert s9_classes._state_fingerprint("archive", 1) != s9_classes._state_fingerprint(
        "suspend", 1
    )
    assert s9_classes._state_fingerprint("suspend", 1) != s9_classes._state_fingerprint(
        "suspend", 2
    )
    profile = CreateProfileRequest(display_name="Synthetic Mai An", age_months=40, consent_id=None)
    fingerprint = s9_classes._profile_fingerprint(
        key=b"x" * 32,
        subject=data.ORG_A_TEACHERS[0],
        scope=fixtures.profile_create_scope(),
        payload=profile,
        expected_revision=1,
    )
    assert fingerprint == s9_classes._profile_fingerprint(
        key=b"x" * 32,
        subject=data.ORG_A_TEACHERS[0],
        scope=fixtures.profile_create_scope(),
        payload=profile,
        expected_revision=1,
    )
    assert len(fingerprint) == 64
    assert fingerprint != s9_classes._profile_fingerprint(
        key=b"y" * 32,
        subject=data.ORG_A_TEACHERS[0],
        scope=fixtures.profile_create_scope(),
        payload=profile,
        expected_revision=1,
    )
    move = MoveProfileRequest(target_class_id=data.class_id("a", 3), target_class_revision=1)
    assert (
        len(
            s9_classes._move_fingerprint(
                class_id=data.class_id("a", 1),
                child_id=fixtures.MOVED_CHILD_ID,
                payload=move,
                expected_revision=1,
            )
        )
        == 64
    )


def test_run_s9_orchestrates_each_direct_write_set_once_with_a_fake_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []

    class FakeEngine:
        def connect(self) -> FakeEngine:
            return self

        def __enter__(self) -> FakeEngine:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    counts = iter([{}, dict(fixtures.EXPECTED)])
    monkeypatch.setattr(s9_classes, "count_s9_rows", lambda _connection: next(counts))
    monkeypatch.setattr(s9_classes, "create_core_session_factory", lambda _engine: object())
    monkeypatch.setattr(
        s9_classes,
        "_ensure_class_row",
        lambda _factory, spec: calls.append(("class", spec.class_number)),
    )
    monkeypatch.setattr(
        s9_classes,
        "_ensure_class_assignment",
        lambda _factory, spec: calls.append(("assignment", spec.class_number)),
    )
    monkeypatch.setattr(
        s9_classes,
        "_ensure_lifecycle_profiles",
        lambda _factory: calls.append(("lifecycle_profiles",)),
    )
    monkeypatch.setattr(
        s9_classes,
        "_ensure_class_state",
        lambda _factory, spec: calls.append(("state", spec.class_number)),
    )
    monkeypatch.setattr(s9_classes, "_profile_receipt_key", lambda: b"x" * 32)
    monkeypatch.setattr(
        s9_classes,
        "_ensure_profile_create",
        lambda _factory, profile, _key: calls.append(("profile", profile["child_id"])),
    )
    monkeypatch.setattr(s9_classes, "_ensure_move", lambda _factory: calls.append(("move",)))

    result = s9_classes.run_s9(FakeEngine())  # type: ignore[arg-type]

    assert result.ok
    assert result.before == {}
    assert result.after == fixtures.EXPECTED
    assert [call for call in calls if call[0] == "class"] == [("class", 5), ("class", 6)]
    assert [call for call in calls if call[0] == "assignment"] == [("assignment", 6)]
    assert [call for call in calls if call[0] == "lifecycle_profiles"] == [("lifecycle_profiles",)]
    assert [call for call in calls if call[0] == "state"] == [("state", 5), ("state", 6)]
    assert len([call for call in calls if call[0] == "profile"]) == 3
    assert [call for call in calls if call[0] == "move"] == [("move",)]


def test_stage_guard_refuses_seed_database_without_frc08_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "tools.seed.stage_common.check_target",
        lambda _environ=None: type("Target", (), {"database": "seed_fixture"})(),
    )
    with pytest.raises(SeedGuardError, match="frc08_"):
        check_database_prefix({})

    monkeypatch.setattr(
        "tools.seed.stage_common.check_target",
        lambda _environ=None: type("Target", (), {"database": "frc08_seed_fixture"})(),
    )
    check_database_prefix({})
