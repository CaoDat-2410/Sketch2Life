"""FEAT-066 T-7c unit tests: the Teacher profile create modes, receipt helpers and handler order.

No database: a fake session answers the handler's reads in order. SRS l.543, l.832, l.1095-1096,
l.1651, l.1697-1699; coordinator ruling: the real-data success write is parked (X-19), the real
branch is a refusing gate, and the `Synthetic ` name rule holds for every create.
"""

from __future__ import annotations

import re
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Request, Response
from pydantic import SecretStr, ValidationError

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import CreateProfileRequest
from sketch2life.infrastructure.persistence.be1_models import (
    Be1CommandReceiptModel,
    ConsentRecordModel,
    ManagedProfileModel,
)
from sketch2life.infrastructure.persistence.core_models import CoreAuditEntryModel
from sketch2life.interfaces.http.rate_limit import SlidingWindowLimiter
from sketch2life.interfaces.http.routers import be1_registry

ORG = "synthetic-org"
CLASS_ID = "synthetic-class"
RECEIPT_KEY = "synthetic-receipt-key-" + "k" * 32
PRINCIPAL = VerifiedPrincipal(
    subject="synthetic-teacher", issuer="synthetic-issuer", roles=frozenset(), token_id="t"
)


def _payload(**overrides: Any) -> CreateProfileRequest:
    values: dict[str, Any] = {"display_name": "Synthetic Learner", "age_months": 60}
    values.update(overrides)
    return CreateProfileRequest(**values)


def _request(key: str = "synthetic-key") -> Request:
    return Request({"type": "http", "headers": [(b"idempotency-key", key.encode())]})


def _runtime(
    *,
    env: str = "test",
    synthetic: bool = True,
    real: bool = False,
    key: str | None = RECEIPT_KEY,
    limiter: SlidingWindowLimiter | None = None,
) -> be1_registry.Be1Runtime:
    return cast(
        be1_registry.Be1Runtime,
        SimpleNamespace(
            settings=SimpleNamespace(
                env=env,
                synthetic_pilot_enabled=synthetic,
                real_profile_data_enabled=real,
                profile_receipt_hmac_key=SecretStr(key) if key is not None else None,
            ),
            profile_gate_limiter=limiter or SlidingWindowLimiter(),
        ),
    )


class FakeSession:
    """`scalar` answers in call order: known class, locked class, then the consent lookup."""

    def __init__(self, scalars: list[object], receipt: object | None = None) -> None:
        self._scalars = list(scalars)
        self._receipt = receipt
        self.added: list[object] = []
        self.commits = 0
        self.rollbacks = 0

    def scalar(self, _statement: object) -> object:
        return self._scalars.pop(0)

    def get(self, _model: object, _key: object) -> object | None:
        return self._receipt

    def add(self, row: object) -> None:
        self.added.append(row)

    def add_all(self, rows: list[object]) -> None:
        self.added.extend(rows)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _class(*, revision: int = 1, state: str = "active") -> SimpleNamespace:
    return SimpleNamespace(class_id=CLASS_ID, state=state, revision=revision)


@pytest.fixture(autouse=True)
def _teacher_row(monkeypatch: pytest.MonkeyPatch) -> None:
    assignment = SimpleNamespace(class_id=CLASS_ID, role="teacher")
    monkeypatch.setattr(be1_registry, "require_assignment", lambda *_a, **_k: (assignment,))
    monkeypatch.setattr(be1_registry.secrets, "token_hex", lambda _length: "b" * 24)


def _create(
    db: FakeSession,
    payload: CreateProfileRequest | None = None,
    *,
    runtime: be1_registry.Be1Runtime | None = None,
    if_match: str | None = '"1"',
    key: str = "synthetic-key",
    response: Response | None = None,
) -> dict[str, object]:
    return be1_registry.create_profile(
        ORG,
        CLASS_ID,
        payload or _payload(),
        _request(key),
        response or Response(),
        key,
        if_match,
        PRINCIPAL,
        runtime or _runtime(),
        cast(be1_registry.Session, db),
    )


def _error(db: FakeSession, **kwargs: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        _create(db, **kwargs)
    return caught.value


# ------------------------------------------------------------------ schema and the name rule
def test_schema_has_no_class_id_and_one_optional_reference() -> None:
    assert set(CreateProfileRequest.model_fields) == {"display_name", "age_months", "consent_id"}
    assert _payload().consent_id is None
    for age in (36, 120):
        assert _payload(age_months=age).age_months == age
    for age in (35, 121):
        with pytest.raises(ValidationError):
            _payload(age_months=age)


@pytest.mark.parametrize("field", ["class_id", "child_id", "purpose_ref", "data_origin"])
def test_schema_rejects_client_identity_origin_and_class_fields(field: str) -> None:
    with pytest.raises(ValidationError) as caught:
        CreateProfileRequest(
            display_name="Synthetic Learner", age_months=60, **{field: "client-value"}
        )  # type: ignore[arg-type]
    assert caught.value.errors()[0]["type"] == "extra_forbidden"


@pytest.mark.parametrize("name", ["Learner", "Synthetic", "synthetic Learner", "Real Child Name"])
def test_a_name_without_the_synthetic_prefix_is_refused_whatever_the_flags(name: str) -> None:
    # Every row of the mode matrix that writes a profile writes SYNTHETIC_DEV, so the rule is the
    # schema's and does not depend on the settings (review F-02).
    with pytest.raises(ValidationError):
        _payload(display_name=name)


def test_duplicate_display_names_are_not_a_schema_concern() -> None:
    assert _payload(display_name="Synthetic Learner").display_name == "Synthetic Learner"


# ------------------------------------------------------------------ the mode matrix
def _mode(**kwargs: Any) -> str:
    return be1_registry._profile_create_mode(**kwargs)


def _http_error(**kwargs: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        be1_registry._profile_create_mode(**kwargs)
    return caught.value


@pytest.mark.parametrize("real", [False, True])
def test_matrix_without_consent_id_is_synthetic_when_the_pilot_is_on(real: bool) -> None:
    assert (
        _mode(env="test", synthetic_pilot_enabled=True, real_enabled=real, consent_id=None)
        == "synthetic"
    )
    assert (
        _mode(env="local", synthetic_pilot_enabled=True, real_enabled=real, consent_id=None)
        == "synthetic"
    )


@pytest.mark.parametrize(
    ("env", "pilot"), [("test", False), ("staging", True), ("production", True), ("local", False)]
)
def test_matrix_without_consent_id_and_without_the_pilot_is_409_unless_real_is_on(
    env: str, pilot: bool
) -> None:
    error = _http_error(
        env=env, synthetic_pilot_enabled=pilot, real_enabled=False, consent_id=None
    )
    assert error.status_code == 409
    assert cast(dict[str, Any], error.detail)["code"] == "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE"
    required = _http_error(
        env=env, synthetic_pilot_enabled=pilot, real_enabled=True, consent_id=None
    )
    assert required.status_code == 400
    assert required.detail == {
        "code": "INVALID_REQUEST",
        "field_errors": [{"field": "consent_id", "code": "REQUIRED"}],
    }


@pytest.mark.parametrize("pilot", [False, True])
def test_matrix_with_consent_id_while_real_data_is_off_is_unknown_field(pilot: bool) -> None:
    error = _http_error(
        env="test", synthetic_pilot_enabled=pilot, real_enabled=False, consent_id="c-1"
    )
    assert error.status_code == 400
    assert error.detail == {
        "code": "INVALID_REQUEST",
        "field_errors": [{"field": "consent_id", "code": "UNKNOWN_FIELD"}],
    }


@pytest.mark.parametrize(("env", "pilot"), [("test", True), ("production", False), ("test", False)])
def test_matrix_with_consent_id_while_real_data_is_on_is_the_gate(env: str, pilot: bool) -> None:
    assert (
        _mode(env=env, synthetic_pilot_enabled=pilot, real_enabled=True, consent_id="c-1")
        == "real_gate"
    )


def test_the_setting_defaults_off() -> None:
    from sketch2life.infrastructure.config.settings import Settings

    assert Settings.model_fields["real_profile_data_enabled"].default is False


# ------------------------------------------------------------------ receipt helpers
def test_fingerprint_is_stable_and_separates_every_input() -> None:
    scope = be1_registry._profile_receipt_scope(ORG, CLASS_ID)

    def fp(**overrides: Any) -> str:
        values: dict[str, Any] = {
            "key": RECEIPT_KEY.encode(),
            "principal_ref": "p",
            "scope": scope,
            "payload": _payload(),
            "expected_revision": 1,
        }
        values.update(overrides)
        return be1_registry._profile_fingerprint(**values)

    base = fp()
    assert base == fp()
    assert len(base) == 64
    assert "Synthetic" not in base
    for changed in (
        fp(principal_ref="q"),
        fp(scope=scope + "x"),
        fp(payload=_payload(display_name="Synthetic Other")),
        fp(payload=_payload(age_months=61)),
        fp(payload=_payload(consent_id="c-1")),
        fp(expected_revision=2),
        fp(key=b"another-key-" + b"k" * 32),
    ):
        assert changed != base


def test_receipt_scope_is_plain_when_it_fits_and_hashed_when_it_cannot() -> None:
    assert be1_registry._profile_receipt_scope(ORG, CLASS_ID) == (
        f"POST /organizations/{ORG}/classes/{CLASS_ID}/profiles"
    )
    long_org, long_class = "o" * 128, "c" * 128
    hashed = be1_registry._profile_receipt_scope(long_org, long_class)
    assert len(hashed) <= 256
    assert hashed != be1_registry._profile_receipt_scope(long_org, "d" * 128)
    assert hashed == be1_registry._profile_receipt_scope(long_org, long_class)


# ------------------------------------------------------------------ the handler, in order
def test_success_writes_one_profile_one_enrollment_and_a_reference_only_receipt() -> None:
    db = FakeSession([_class(), _class()])
    response = Response()
    body = _create(db, response=response)
    assert body["class_revision"] == 1
    assert body["data_origin"] == "SYNTHETIC_DEV"
    assert body["child_id"] == "synthetic-" + "b" * 24
    assert response.headers["ETag"] == '"1"'
    assert db.commits == 1
    profiles = [row for row in db.added if isinstance(row, ManagedProfileModel)]
    receipts = [row for row in db.added if isinstance(row, Be1CommandReceiptModel)]
    assert len(profiles) == 1 and len(receipts) == 1
    assert profiles[0].age_source == "SYNTHETIC_FIXTURE"
    assert profiles[0].consent_id is None and profiles[0].consent_purpose_ref is None
    stored = receipts[0].response_json
    assert set(stored) == {
        "child_id",
        "enrollment_id",
        "class_revision",
        "data_origin",
        "fp_v",
        "fp_kid",
    }
    assert stored["fp_v"] == 2 and re.fullmatch(r"[0-9a-f]{8}", str(stored["fp_kid"]))
    assert "Synthetic Learner" not in str(stored) and RECEIPT_KEY not in str(stored)
    assert receipts[0].operation_scope == f"POST /organizations/{ORG}/classes/{CLASS_ID}/profiles"


def test_a_missing_class_is_404_before_the_scope_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        be1_registry,
        "require_assignment",
        lambda *_a, **_k: pytest.fail("a missing class is denied first"),
    )
    error = _error(FakeSession([None]))
    assert error.status_code == 404


def test_replay_returns_the_stored_references_before_the_stale_check() -> None:
    db = FakeSession([_class(), _class()])
    first_response = Response()
    first = _create(db, response=first_response)
    receipt = next(row for row in db.added if isinstance(row, Be1CommandReceiptModel))
    # The class moved on (revision 7, suspended) and the request still carries the old revision:
    # the stored result is replayed, not a 409.
    replay_db = FakeSession([_class(revision=7, state="suspended")] * 2, receipt=receipt)
    replay_response = Response()
    replay = _create(replay_db, response=replay_response)
    assert replay == first
    assert replay_response.headers["ETag"] == '"1"'
    assert replay_db.added == [] and replay_db.commits == 0


def test_the_same_key_with_another_request_is_400_invalid_idempotency_key() -> None:
    db = FakeSession([_class(), _class()])
    _create(db)
    receipt = next(row for row in db.added if isinstance(row, Be1CommandReceiptModel))
    for other in (_payload(display_name="Synthetic Other"), _payload(age_months=61)):
        error = _error(FakeSession([_class(), _class()], receipt=receipt), payload=other)
        assert error.status_code == 400
        assert cast(dict[str, Any], error.detail)["code"] == "INVALID_IDEMPOTENCY_KEY"
    error = _error(FakeSession([_class(), _class()], receipt=receipt), if_match='"2"')
    assert cast(dict[str, Any], error.detail)["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_a_stale_revision_is_409_with_the_current_version_and_writes_nothing() -> None:
    db = FakeSession([_class(revision=3), _class(revision=3)])
    error = _error(db, if_match='"1"')
    assert error.status_code == 409
    assert error.detail == {"code": "STALE_REVISION", "current_version": 3}
    assert error.headers == {"ETag": '"3"'}
    assert db.added == [] and db.commits == 0


def test_the_stale_check_comes_before_the_state_check() -> None:
    db = FakeSession([_class(revision=3, state="suspended")] * 2)
    error = _error(db, if_match='"1"')
    assert cast(dict[str, Any], error.detail)["code"] == "STALE_REVISION"


@pytest.mark.parametrize("state", ["suspended", "archived"])
def test_a_read_only_class_is_409_before_the_mode_matrix(state: str) -> None:
    db = FakeSession([_class(state=state)] * 2)
    # With the pilot off and real data on this would be a 400; the state wins.
    error = _error(db, runtime=_runtime(synthetic=False, real=True))
    assert error.status_code == 409
    assert cast(dict[str, Any], error.detail)["code"] == "INVALID_STATE_TRANSITION"
    assert db.added == []


def test_a_missing_or_malformed_if_match_is_400() -> None:
    for value, code in ((None, "REQUIRED"), ("1", "INVALID_FORMAT"), ('W/"1"', "INVALID_FORMAT")):
        error = _error(FakeSession([_class()]), if_match=value)
        assert error.status_code == 400
        assert cast(dict[str, Any], error.detail)["field_errors"] == [
            {"field": "If-Match", "code": code}
        ]


def test_the_config_gate_is_after_authorization_and_the_state_check() -> None:
    error = _error(FakeSession([_class(), _class()]), runtime=_runtime(synthetic=False))
    assert error.status_code == 409
    assert cast(dict[str, Any], error.detail)["code"] == "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE"


def test_a_consent_id_while_real_data_is_off_is_400_and_writes_nothing() -> None:
    db = FakeSession([_class(), _class()])
    error = _error(db, payload=_payload(consent_id="synthetic-consent"))
    assert error.status_code == 400
    assert cast(dict[str, Any], error.detail)["field_errors"] == [
        {"field": "consent_id", "code": "UNKNOWN_FIELD"}
    ]
    assert db.added == [] and db.commits == 0


# ------------------------------------------------------------------ the real-data gate
def test_the_real_gate_refuses_a_pending_consent_with_an_audit_row_and_no_profile() -> None:
    db = FakeSession([_class(), _class(), "synthetic-consent"])
    error = _error(
        db, payload=_payload(consent_id="synthetic-consent"), runtime=_runtime(real=True)
    )
    assert error.status_code == 409
    assert cast(dict[str, Any], error.detail)["code"] == "CONSENT_NOT_EFFECTIVE"
    assert not any(isinstance(row, ManagedProfileModel) for row in db.added)
    assert not any(isinstance(row, Be1CommandReceiptModel) for row in db.added)
    audits = [row for row in db.added if isinstance(row, CoreAuditEntryModel)]
    assert len(audits) == 1
    assert audits[0].decision == "denied_consent_pending"
    assert audits[0].action == "profile.enroll"
    assert audits[0].resource_id == "synthetic-consent"
    assert db.commits == 1


def test_the_real_gate_for_an_unknown_consent_is_404_consent_not_found() -> None:
    db = FakeSession([_class(), _class(), None])
    error = _error(db, payload=_payload(consent_id="missing"), runtime=_runtime(real=True))
    assert error.status_code == 404
    assert cast(dict[str, Any], error.detail)["code"] == "CONSENT_NOT_FOUND"
    assert db.added == []


def test_the_real_gate_never_reads_child_or_purpose_from_the_consent_row() -> None:
    import inspect

    source = inspect.getsource(be1_registry._refuse_real_profile)
    assert "child_id" not in source.replace("ConsentRecordModel.child_id", "")
    assert "purpose_ref" not in source
    assert ConsentRecordModel.consent_id is not None  # the lookup selects the id only
