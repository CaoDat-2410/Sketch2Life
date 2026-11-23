"""FEAT-066 T-7c-fix unit tests: the keyed profile-create receipt fingerprint (O-1).

SRS l.1697 (keyed commands), l.502 (FR-C-10), l.278-279 (BR-34, BR-35). No database: a fake
session answers the handler's reads. Every name, id and key here is synthetic.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi import HTTPException, Request, Response
from pydantic import SecretStr, ValidationError
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.contracts.schemas.be1_runtime import CreateProfileRequest
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.persistence import be1_receipts
from sketch2life.infrastructure.persistence.be1_models import Be1CommandReceiptModel
from sketch2life.interfaces.http import be1_runtime
from sketch2life.interfaces.http.be1_runtime import Be1Runtime
from sketch2life.interfaces.http.rate_limit import SlidingWindowLimiter
from sketch2life.interfaces.http.routers import be1_registry

ORG = "synthetic-org"
CLASS_ID = "synthetic-class"
KEY = "synthetic-receipt-key-" + "k" * 32
OTHER_KEY = "synthetic-other-key-" + "o" * 32
ROOM_KEY = "synthetic-room-key-" + "r" * 32
PRINCIPAL = VerifiedPrincipal(
    subject="synthetic-teacher", issuer="synthetic-issuer", roles=frozenset(), token_id="t"
)
KEY_ENV = "SKETCH2LIFE_PROFILE_RECEIPT_HMAC_KEY"


def _settings(**values: Any) -> Settings:
    base: dict[str, Any] = {"env": "test"}
    base.update(values)
    return Settings(_env_file=None, **base)  # type: ignore[call-arg]


def _staging(**values: Any) -> Settings:
    base: dict[str, Any] = {
        "env": "staging",
        "auth_provider": "firebase",
        "firebase_project_id": "synthetic-project",
    }
    base.update(values)
    return _settings(**base)


def _production(**values: Any) -> Settings:
    base: dict[str, Any] = {
        "env": "production",
        "auth_provider": "firebase",
        "firebase_project_id": "synthetic-project",
        "ai_provider": "runpod",
        "runpod_endpoint_id": "synthetic-endpoint",
        "runpod_api_key_file": Path("synthetic.key"),
    }
    base.update(values)
    return _settings(**base)


@pytest.fixture(autouse=True)
def _no_key_in_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(KEY_ENV, raising=False)
    monkeypatch.delenv("SKETCH2LIFE_REAL_PROFILE_DATA_ENABLED", raising=False)


# ------------------------------------------------------------------ the setting
@pytest.mark.parametrize("env", ["local", "test"])
def test_local_and_test_generate_a_per_process_key_of_32_bytes_or_more(env: str) -> None:
    first, second = _settings(env=env), _settings(env=env)
    assert first.profile_receipt_hmac_key is not None
    value = first.profile_receipt_hmac_key.get_secret_value()
    assert len(value.encode("utf-8")) >= 32
    assert second.profile_receipt_hmac_key is not None
    assert value != second.profile_receipt_hmac_key.get_secret_value()


@pytest.mark.parametrize("build", [_staging, _production])
def test_staging_and_production_never_generate_a_key(build: Any) -> None:
    assert build().profile_receipt_hmac_key is None


@pytest.mark.parametrize("build", [_staging, _production])
def test_real_profile_data_in_staging_or_production_needs_the_key(build: Any) -> None:
    with pytest.raises(ValidationError) as caught:
        build(real_profile_data_enabled=True)
    assert "profile receipt key" in str(caught.value)
    configured = build(real_profile_data_enabled=True, profile_receipt_hmac_key=KEY)
    assert configured.profile_receipt_hmac_key is not None
    assert configured.real_profile_data_enabled is True


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_a_blank_key_means_unset_and_never_stops_startup(
    blank: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # F-01: the blank `NAME=` line of .env.example and an empty Compose variable are "unset".
    local = _settings(env="local", profile_receipt_hmac_key=blank)
    assert local.profile_receipt_hmac_key is not None
    assert len(local.profile_receipt_hmac_key.get_secret_value()) >= 32
    assert _staging(profile_receipt_hmac_key=blank).profile_receipt_hmac_key is None
    with pytest.raises(ValidationError):
        _staging(real_profile_data_enabled=True, profile_receipt_hmac_key=blank)
    monkeypatch.setenv(KEY_ENV, blank)
    from_environment = _settings(env="local")
    assert from_environment.profile_receipt_hmac_key is not None
    assert len(from_environment.profile_receipt_hmac_key.get_secret_value()) >= 32


@pytest.mark.parametrize("env", ["local", "test"])
def test_a_key_shorter_than_32_bytes_is_refused_in_every_environment(env: str) -> None:
    short = "s" * 31
    with pytest.raises(ValidationError) as caught:
        _settings(env=env, profile_receipt_hmac_key=short)
    assert short not in str(caught.value) and short not in repr(caught.value)
    assert _settings(env=env, profile_receipt_hmac_key="s" * 32) is not None


def test_the_key_never_appears_in_repr_str_or_a_validation_error() -> None:
    configured = _settings(profile_receipt_hmac_key=KEY)
    assert KEY not in repr(configured) and KEY not in str(configured)
    assert KEY not in repr(configured.model_dump()) and KEY not in configured.model_dump_json()
    with pytest.raises(ValidationError) as caught:
        _staging(real_profile_data_enabled=True, profile_receipt_hmac_key="x" * 8)
    assert "x" * 8 not in str(caught.value)


def test_the_key_is_not_the_room_code_key() -> None:
    configured = _settings(room_code_hmac_key=ROOM_KEY, profile_receipt_hmac_key=KEY)
    assert configured.profile_receipt_hmac_key is not None
    assert configured.profile_receipt_hmac_key.get_secret_value() == KEY
    unset = _settings(room_code_hmac_key=ROOM_KEY)
    assert unset.profile_receipt_hmac_key is not None
    assert unset.profile_receipt_hmac_key.get_secret_value() != ROOM_KEY
    # Enforced (review F-01): the same value for both keys is refused, in every environment, and
    # the error never echoes either value.
    for build in (_settings, _staging):
        with pytest.raises(ValidationError) as caught:
            build(room_code_hmac_key=ROOM_KEY, profile_receipt_hmac_key=ROOM_KEY)
        assert "differ from the room-code key" in str(caught.value)
        assert ROOM_KEY not in str(caught.value)


def test_gate_limit_settings_have_the_plan_defaults_and_bounds() -> None:
    configured = _settings()
    assert (
        configured.profile_gate_account_limit,
        configured.profile_gate_ip_limit,
        configured.profile_gate_window_seconds,
    ) == (5, 20, 60)
    for field in ("profile_gate_account_limit", "profile_gate_ip_limit"):
        with pytest.raises(ValidationError):
            _settings(**{field: 0})
    with pytest.raises(ValidationError):
        _settings(profile_gate_window_seconds=0)
    # Upper bounds also cap the limiter's memory (review F-04).
    with pytest.raises(ValidationError):
        _settings(profile_gate_account_limit=201)
    with pytest.raises(ValidationError):
        _settings(profile_gate_ip_limit=1001)
    assert _settings(profile_gate_account_limit=200, profile_gate_ip_limit=1000)


# ------------------------------------------------------------------ the runtime constructor
def test_the_runtime_constructor_refuses_real_data_without_a_key_in_staging_and_production(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # A hand-mutated settings object (the Settings validator would have refused it at load).
    for build in (_staging, _production):
        mutated = build()
        mutated.real_profile_data_enabled = True
        with pytest.raises(RuntimeError) as caught:
            be1_runtime.build_be1_runtime(mutated)
        assert "receipt key" in str(caught.value)
        mutated.profile_receipt_hmac_key = SecretStr("s" * 31)
        with pytest.raises(RuntimeError) as short:
            be1_runtime.build_be1_runtime(mutated)
        assert "s" * 31 not in str(short.value)
        mutated.profile_receipt_hmac_key = SecretStr(KEY)
        be1_runtime._require_receipt_key_for_real_data(mutated)  # no raise
    for env_settings in (_staging(), _production()):  # real data off: no refusal
        be1_runtime._require_receipt_key_for_real_data(env_settings)
    be1_runtime._require_receipt_key_for_real_data(_settings(real_profile_data_enabled=True))
    monkeypatch.setattr(
        be1_runtime, "get_core_database_settings", lambda: SimpleNamespace(database_url=None)
    )
    runtime = be1_runtime.build_be1_runtime(
        _settings(profile_gate_account_limit=2, be1_artifact_root=tmp_path / "artifacts")
    )
    assert runtime.engine is not None or runtime.database_error is not None
    assert isinstance(runtime.profile_gate_limiter, SlidingWindowLimiter)
    assert runtime.profile_gate_limiter.acquire("op", account="a", ip="i") is None
    assert runtime.profile_gate_limiter.acquire("op", account="a", ip="j") is None
    assert runtime.profile_gate_limiter.acquire("op", account="a", ip="k") is not None


# ------------------------------------------------------------------ the fingerprint
def _payload(**overrides: Any) -> CreateProfileRequest:
    values: dict[str, Any] = {"display_name": "Synthetic Learner", "age_months": 60}
    values.update(overrides)
    return CreateProfileRequest(**values)


SCOPE = be1_registry._profile_receipt_scope(ORG, CLASS_ID)


def _fp(**overrides: Any) -> str:
    values: dict[str, Any] = {
        "key": KEY.encode(),
        "principal_ref": "p",
        "scope": SCOPE,
        "payload": _payload(),
        "expected_revision": 1,
    }
    values.update(overrides)
    return be1_registry._profile_fingerprint(**values)


def test_the_fingerprint_is_64_hex_and_stable() -> None:
    value = _fp()
    assert re.fullmatch(r"[0-9a-f]{64}", value)
    assert value == _fp()


def test_the_fingerprint_separates_key_principal_scope_name_age_consent_and_revision() -> None:
    base = _fp()
    changed = {
        _fp(key=OTHER_KEY.encode()),
        _fp(principal_ref="q"),
        _fp(scope=SCOPE + "x"),
        _fp(payload=_payload(display_name="Synthetic Other")),
        _fp(payload=_payload(age_months=61)),
        _fp(payload=_payload(consent_id="c-1")),
        _fp(expected_revision=2),
    }
    assert base not in changed and len(changed) == 7


def test_the_fingerprint_is_not_a_plain_hash_of_the_child_data() -> None:
    value = _fp()
    v1_payload = json.dumps(
        {
            "v": 1,
            "principal": "p",
            "scope": SCOPE,
            "display_name": "Synthetic Learner",
            "age_months": 60,
            "consent_id": None,
            "if_match": 1,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    plain = {
        hashlib.sha256(v1_payload.encode()).hexdigest(),
        hashlib.sha256(b"Synthetic Learner").hexdigest(),
        hashlib.sha256(b"Synthetic Learner60").hexdigest(),
        hashlib.sha256(b"Synthetic Learner:60").hexdigest(),
        hashlib.sha256(
            json.dumps({"display_name": "Synthetic Learner", "age_months": 60}).encode()
        ).hexdigest(),
    }
    assert value not in plain
    assert "Synthetic" not in value


def test_the_fingerprint_is_the_documented_hmac_with_a_domain_inside_the_input() -> None:
    message = json.dumps(
        {
            "domain": "be1.profile.create.receipt",
            "v": 2,
            "principal": "p",
            "scope": SCOPE,
            "display_name": "Synthetic Learner",
            "age_months": 60,
            "consent_id": None,
            "if_match": 1,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    assert _fp() == hmac.new(KEY.encode(), message, hashlib.sha256).hexdigest()


def test_the_key_id_is_short_stable_and_not_the_key() -> None:
    kid = be1_registry._profile_key_id(KEY.encode())
    assert re.fullmatch(r"[0-9a-f]{8}", kid)
    assert kid == be1_registry._profile_key_id(KEY.encode())
    assert kid != be1_registry._profile_key_id(OTHER_KEY.encode())
    assert KEY not in kid


# ------------------------------------------------------------------ the handler
def _request(client: Any = None) -> Request:
    scope: dict[str, Any] = {"type": "http", "headers": [(b"idempotency-key", b"synthetic-key")]}
    if client is not None:
        scope["client"] = client
    return Request(scope)


def _runtime(
    *,
    env: str = "test",
    synthetic: bool = True,
    real: bool = False,
    key: str | None = KEY,
    room_key: str | None = None,
    limiter: SlidingWindowLimiter | None = None,
) -> Be1Runtime:
    return cast(
        Be1Runtime,
        SimpleNamespace(
            settings=SimpleNamespace(
                env=env,
                synthetic_pilot_enabled=synthetic,
                real_profile_data_enabled=real,
                profile_receipt_hmac_key=SecretStr(key) if key is not None else None,
                room_code_hmac_key=SecretStr(room_key) if room_key is not None else None,
            ),
            profile_gate_limiter=limiter or SlidingWindowLimiter(),
        ),
    )


class FakeSession:
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


def _class() -> SimpleNamespace:
    return SimpleNamespace(class_id=CLASS_ID, state="active", revision=1)


@pytest.fixture(autouse=True)
def _teacher_row(monkeypatch: pytest.MonkeyPatch) -> None:
    assignment = SimpleNamespace(class_id=CLASS_ID, role="teacher")
    monkeypatch.setattr(be1_registry, "require_assignment", lambda *_a, **_k: (assignment,))
    monkeypatch.setattr(secrets, "token_hex", lambda _length: "c" * 24)


def _create(
    db: FakeSession,
    *,
    payload: CreateProfileRequest | None = None,
    runtime: Be1Runtime | None = None,
    request: Request | None = None,
) -> dict[str, object]:
    return be1_registry.create_profile(
        ORG,
        CLASS_ID,
        payload or _payload(),
        request or _request(),
        Response(),
        "synthetic-key",
        '"1"',
        PRINCIPAL,
        runtime or _runtime(),
        cast(Session, db),
    )


def _error(db: FakeSession, **kwargs: Any) -> HTTPException:
    with pytest.raises(HTTPException) as caught:
        _create(db, **kwargs)
    return caught.value


def _receipt_of(db: FakeSession) -> Be1CommandReceiptModel:
    return next(row for row in db.added if isinstance(row, Be1CommandReceiptModel))


def test_the_receipt_holds_the_keyed_fingerprint_and_the_key_id_and_no_secret() -> None:
    db = FakeSession([_class(), _class()])
    _create(db)
    receipt = _receipt_of(db)
    expected = be1_registry._profile_fingerprint(
        key=KEY.encode(),
        principal_ref=PRINCIPAL.subject,
        scope=SCOPE,
        payload=_payload(),
        expected_revision=1,
    )
    assert receipt.request_fingerprint == expected
    assert receipt.response_json["fp_v"] == 2
    assert receipt.response_json["fp_kid"] == be1_registry._profile_key_id(KEY.encode())
    stored = json.dumps(receipt.response_json)
    assert KEY not in stored and KEY not in receipt.request_fingerprint
    assert "Synthetic Learner" not in stored + receipt.request_fingerprint


def test_the_room_code_key_never_enters_the_fingerprint() -> None:
    first, second = FakeSession([_class(), _class()]), FakeSession([_class(), _class()])
    _create(first, runtime=_runtime(room_key=ROOM_KEY))
    _create(second, runtime=_runtime(room_key=OTHER_KEY))
    assert _receipt_of(first).request_fingerprint == _receipt_of(second).request_fingerprint


def test_another_receipt_key_makes_the_same_request_a_mismatch() -> None:
    db = FakeSession([_class(), _class()])
    _create(db)
    error = _error(
        FakeSession([_class(), _class()], receipt=_receipt_of(db)),
        runtime=_runtime(key=OTHER_KEY),
    )
    assert error.status_code == 400
    assert cast(dict[str, Any], error.detail)["code"] == "INVALID_IDEMPOTENCY_KEY"


def test_a_v1_receipt_is_non_matching_and_answers_400_never_a_second_profile() -> None:
    # T-7c-fix-DEC-4: a receipt of the plain-SHA-256 format cannot equal a keyed value.
    v1_fingerprint = hashlib.sha256(
        json.dumps(
            {
                "v": 1,
                "principal": PRINCIPAL.subject,
                "scope": SCOPE,
                "display_name": "Synthetic Learner",
                "age_months": 60,
                "consent_id": None,
                "if_match": 1,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    legacy = SimpleNamespace(
        request_fingerprint=v1_fingerprint,
        response_json={
            "child_id": "synthetic-" + "d" * 24,
            "enrollment_id": "e",
            "class_revision": 1,
            "data_origin": "SYNTHETIC_DEV",
        },
    )
    db = FakeSession([_class(), _class()], receipt=legacy)
    error = _error(db)
    assert error.status_code == 400
    assert cast(dict[str, Any], error.detail)["code"] == "INVALID_IDEMPOTENCY_KEY"
    assert db.added == [] and db.commits == 0


def test_a_tampered_non_ascii_fingerprint_is_a_mismatch_not_a_500() -> None:
    db = FakeSession([_class(), _class()])
    _create(db)
    tampered = _receipt_of(db)
    tampered.request_fingerprint = "é" * 64
    error = _error(FakeSession([_class(), _class()], receipt=tampered))
    assert error.status_code == 400


def test_a_receipt_with_the_wrong_format_version_or_key_id_never_matches() -> None:
    db = FakeSession([_class(), _class()])
    _create(db)
    receipt = _receipt_of(db)
    for tampered_json in (
        {**receipt.response_json, "fp_v": 3},
        {**receipt.response_json, "fp_kid": "00000000"},
        {k: v for k, v in receipt.response_json.items() if k != "fp_kid"},
    ):
        receipt.response_json = tampered_json
        assert _error(FakeSession([_class(), _class()], receipt=receipt)).status_code == 400


def test_a_missing_key_is_503_and_writes_nothing() -> None:
    db = FakeSession([_class(), _class()])
    error = _error(db, runtime=_runtime(key=None))
    assert error.status_code == 503
    assert cast(dict[str, Any], error.detail)["code"] == "SERVICE_UNAVAILABLE"
    assert db.added == [] and db.commits == 0 and db.rollbacks >= 1
    short = _error(FakeSession([_class(), _class()]), runtime=_runtime(key="s" * 31))
    assert short.status_code == 503


def test_a_missing_key_with_a_stored_receipt_is_503() -> None:
    db = FakeSession([_class(), _class()])
    _create(db)
    error = _error(
        FakeSession([_class(), _class()], receipt=_receipt_of(db)), runtime=_runtime(key=None)
    )
    assert error.status_code == 503


def test_staging_without_flags_and_without_a_key_keeps_the_409() -> None:
    # F-12: the mode matrix runs before any fingerprint is needed.
    error = _error(
        FakeSession([_class(), _class()]),
        runtime=_runtime(env="staging", synthetic=False, real=False, key=None),
    )
    assert error.status_code == 409
    assert cast(dict[str, Any], error.detail)["code"] == "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE"


def test_the_real_gate_without_a_key_is_503_and_does_not_charge_the_limiter() -> None:
    limiter = SlidingWindowLimiter(account_limit=1, ip_limit=1)
    payload = _payload(consent_id="synthetic-consent")
    error = _error(
        FakeSession([_class(), _class()]),
        payload=payload,
        runtime=_runtime(real=True, key=None, limiter=limiter),
    )
    assert error.status_code == 503
    assert limiter.tracked_keys() == (0, 0)
    assert limiter.acquire("profile_create_real_gate", account=PRINCIPAL.subject, ip="x") is None


def test_the_error_bodies_carry_no_key_or_child_data() -> None:
    error = _error(FakeSession([_class(), _class()]), runtime=_runtime(key=None))
    text = repr(error.detail) + str(error)
    assert KEY not in text and "Synthetic Learner" not in text


# ------------------------------------------------------------------ the purge helper
class _CapturingSession:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def execute(self, statement: Any) -> SimpleNamespace:
        self.statements.append(statement)
        return SimpleNamespace(rowcount=3)


def test_the_purge_helper_deletes_by_organization_and_child_id_in_the_response() -> None:
    session = _CapturingSession()
    deleted = be1_receipts.purge_child_receipts(cast(Any, session), ORG, "synthetic-child")
    assert deleted == 3
    compiled = str(
        session.statements[0].compile(
            dialect=postgresql.dialect(),  # type: ignore[no-untyped-call]
            compile_kwargs={"literal_binds": True},
        )
    )
    assert compiled.startswith("DELETE FROM be1_command_receipts")
    assert "organization_id = 'synthetic-org'" in compiled
    assert "response_json ->> 'child_id') = 'synthetic-child'" in compiled


def test_the_purge_helper_is_not_wired_to_any_route() -> None:
    root = Path(be1_registry.__file__).resolve().parents[3]
    users = [
        path.name
        for path in root.rglob("*.py")
        if path.name != "be1_receipts.py" and "purge_child_receipts" in path.read_text("utf-8")
    ]
    assert users == []  # FR-C-10 deletion path is OPEN (l.502, OD-06, X-19)
