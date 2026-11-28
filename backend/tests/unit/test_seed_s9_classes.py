"""Pure fixture and orchestration checks for the S9 class stage."""

from __future__ import annotations

import hashlib
import hmac
import json
import re

import pytest

from sketch2life.contracts.schemas.be1_runtime import CreateProfileRequest, MoveProfileRequest
from tools.seed import data, s9_classes
from tools.seed import s9_classes_data as fixtures
from tools.seed.guard import SeedGuardError
from tools.seed.stage_common import check_database_prefix


def test_class_lifecycle_and_profile_fixtures_are_stable_and_realistic() -> None:
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
    assert all(not row["display_name"].startswith("Synthetic ") for row in keyed)
    assert [row["display_name"] for row in keyed] == [
        "Lê Bảo Hiếu",
        "Phạm Khánh Ngân",
        "Phạm Đức Tín",
    ]
    assert [row["child_id"] for row in keyed] == list(fixtures.PROFILE_CREATE_CHILD_IDS)


def test_expected_counts_and_route_idempotency_keys_are_valid() -> None:
    assert fixtures.EXPECTED == {
        "be1_classrooms": 4,
        "be1_organization_assignments": 1,
        "be1_managed_profiles": 7,
        "be1_profile_revisions": 7,
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
    profile = fixtures.keyed_profile_rows()[0]
    fingerprint_args = {
        "subject": data.ORG_A_TEACHERS[0],
        "scope": fixtures.profile_create_scope(),
        "display_name": str(profile["display_name"]),
        "age_months": int(profile["age_months"]),
        "consent_id": None,
        "expected_revision": 1,
    }
    fingerprint = s9_classes._profile_fingerprint(key=b"x" * 32, **fingerprint_args)
    assert fingerprint == s9_classes._profile_fingerprint(
        key=b"x" * 32, **fingerprint_args
    )
    assert len(fingerprint) == 64
    assert fingerprint != s9_classes._profile_fingerprint(
        key=b"y" * 32, **fingerprint_args
    )
    route_payload = CreateProfileRequest(
        display_name="Synthetic Mai An", age_months=40, consent_id=None
    )
    route_fingerprint = s9_classes._profile_fingerprint(
        key=b"x" * 32,
        subject=data.ORG_A_TEACHERS[0],
        scope=fixtures.profile_create_scope(),
        display_name=route_payload.display_name,
        age_months=route_payload.age_months,
        consent_id=route_payload.consent_id,
        expected_revision=1,
    )
    route_message = json.dumps(
        {
            "domain": s9_classes.PROFILE_RECEIPT_DOMAIN,
            "v": s9_classes.PROFILE_RECEIPT_VERSION,
            "principal": data.ORG_A_TEACHERS[0],
            "scope": fixtures.profile_create_scope(),
            "display_name": route_payload.display_name,
            "age_months": route_payload.age_months,
            "consent_id": route_payload.consent_id,
            "if_match": 1,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert route_fingerprint == hmac.new(b"x" * 32, route_message, hashlib.sha256).hexdigest()
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


def test_keyed_profile_create_uses_persistence_path_without_http_name_schema() -> None:
    profile = fixtures.keyed_profile_rows()[0]

    class FakeFreshProfileSession:
        def __init__(self) -> None:
            self.executed_tables: list[str] = []
            self.added: list[object] = []
            self.closed = False

        def begin(self) -> FakeFreshProfileSession:
            return self

        def __enter__(self) -> FakeFreshProfileSession:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def get(self, model: object, key: object) -> object:
            if getattr(model, "__name__", None) == "Be1CommandReceiptModel":
                return None
            if getattr(model, "__name__", None) == "ClassroomModel":
                return type("Classroom", (), {"state": "active", "revision": 1})()
            return None

        def scalar(self, _statement: object) -> str:
            return "seed-assignment"

        def execute(self, statement: object) -> None:
            self.executed_tables.append(str(statement.table.name))  # type: ignore[attr-defined]

        def add(self, row: object) -> None:
            self.added.append(row)

        def close(self) -> None:
            self.closed = True

    session = FakeFreshProfileSession()
    s9_classes._ensure_profile_create(lambda: session, profile, b"x" * 32)  # type: ignore[arg-type]

    assert session.closed
    assert session.executed_tables == [
        s9_classes.ManagedProfileModel.__tablename__,
        s9_classes.ProfileRevisionModel.__tablename__,
        s9_classes.EnrollmentModel.__tablename__,
        s9_classes.CoreAuditEntryModel.__tablename__,
        s9_classes.CoreAggregateRevisionModel.__tablename__,
        s9_classes.CoreOutboxEventModel.__tablename__,
    ]
    assert len(session.added) == 1
    receipt = session.added[0]
    assert isinstance(receipt, s9_classes.Be1CommandReceiptModel)
    assert receipt.idempotency_key == fixtures.profile_create_key(str(profile["child_id"]))
    assert receipt.request_fingerprint == s9_classes._profile_fingerprint(
        key=b"x" * 32,
        subject=data.ORG_A_TEACHERS[0],
        scope=fixtures.profile_create_scope(),
        display_name=str(profile["display_name"]),
        age_months=int(profile["age_months"]),
        consent_id=None,
        expected_revision=1,
    )
    assert receipt.response_json["enrollment_id"] == fixtures.stage_enrollment_id(
        str(profile["child_id"])
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
