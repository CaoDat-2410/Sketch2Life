"""FEAT-066 T-1a: the local/test admission adapters, their settings flag and the scope rule.

OD-03 and the owner scope rule: the local pair is accept-all and in-memory; it holds no counter,
unit, balance, grant or price logic; it is refused in staging and production by its constructor and
by ``Settings``; ``unconfigured`` starts everywhere and composes nothing.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sketch2life.application.ports.story_video import (
    AckStatus,
    QuotaStatus,
    ReservationStatus,
    VideoRequestScope,
)
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.story_video.billing_quota_admission import (
    BillingVideoQuotaAdmission,
)
from sketch2life.infrastructure.story_video.composition import build_story_video_adapters
from sketch2life.infrastructure.story_video.local_adapters import (
    LocalAdapterRefused,
    LocalVideoComputeReservation,
    LocalVideoQuotaAdmission,
    VideoAdmissionScript,
    build_local_video_adapters,
)

_SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"
_STORY_VIDEO_FILES = (
    _SRC / "application" / "ports" / "story_video.py",
    _SRC / "application" / "services" / "story_run_video.py",
    _SRC / "domain" / "story_video" / "model.py",
    *sorted((_SRC / "infrastructure" / "story_video").glob("*.py")),
    _SRC / "interfaces" / "http" / "routers" / "story_run_video.py",
    _SRC / "contracts" / "schemas" / "story_run_video.py",
)
_SCOPE = VideoRequestScope("PARENT_ACCOUNT", "a" * 64)
_REFUSAL = "local test video adapters are available only in local/test"


def _quota(env: str = "test", script: VideoAdmissionScript | None = None) -> Any:
    return LocalVideoQuotaAdmission(env=env, script=script)


def _admit(adapter: Any, request_ref: str, key: str = "k1", fingerprint: str = "f1") -> Any:
    return adapter.admit_video_request(
        scope=_SCOPE,
        request_ref=request_ref,
        idempotency_key=key,
        fingerprint=fingerprint,
        contract_version="video-quota-port-v1",
    )


def _reserve(adapter: Any, request_ref: str, key: str = "k1") -> Any:
    return adapter.reserve(
        scope=_SCOPE, request_ref=request_ref, idempotency_key=key, fingerprint="f1"
    )


# ------------------------------------------------------------------------------- refusal
@pytest.mark.parametrize("env", ["staging", "production"])
def test_the_constructors_refuse_staging_and_production(env: str) -> None:
    with pytest.raises(LocalAdapterRefused):
        LocalVideoComputeReservation(env=env)
    with pytest.raises(LocalAdapterRefused):
        LocalVideoQuotaAdmission(env=env)
    with pytest.raises(LocalAdapterRefused):
        build_local_video_adapters(env=env)


@pytest.mark.parametrize("env", ["local", "test"])
def test_the_constructors_accept_local_and_test(env: str) -> None:
    adapters = build_local_video_adapters(env=env)
    assert adapters.reservation is not None and adapters.quota is not None


# ------------------------------------------------------------------------------- settings
def test_the_flag_defaults_to_unconfigured_and_composes_nothing() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.story_video_adapters == "unconfigured"
    assert build_story_video_adapters(settings) is None


@pytest.mark.parametrize("env", ["local", "test"])
def test_local_test_is_accepted_and_composes_the_pair_in_local_and_test(env: Any) -> None:
    settings = Settings(_env_file=None, env=env, story_video_adapters="local_test")  # type: ignore[call-arg]
    adapters = build_story_video_adapters(settings)
    assert isinstance(adapters.reservation, LocalVideoComputeReservation)  # type: ignore[union-attr]
    assert isinstance(adapters.quota, LocalVideoQuotaAdmission)  # type: ignore[union-attr]


def test_billing_mode_composes_billing_quota_with_the_local_test_reservation() -> None:
    settings = Settings(
        _env_file=None, env="test", story_video_adapters="billing"
    )  # type: ignore[call-arg]
    adapters = build_story_video_adapters(
        settings, session_factory=lambda: None
    )  # type: ignore[arg-type]
    assert isinstance(
        adapters.reservation, LocalVideoComputeReservation
    )  # type: ignore[union-attr]
    assert isinstance(adapters.quota, BillingVideoQuotaAdmission)  # type: ignore[union-attr]


def test_billing_mode_stays_fail_closed_in_production_until_compute_reservation_is_supplied(
) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        env="production",
        auth_provider="firebase",
        firebase_project_id="fixture-project",
        ai_provider="runpod",
        runpod_endpoint_id="fixture-endpoint",
        runpod_api_key_file=Path("/runtime/secrets/runpod-key"),
        story_video_adapters="billing",
    )
    def sessions() -> None:
        return None

    assert build_story_video_adapters(
        settings, session_factory=sessions
    ) is None  # type: ignore[arg-type]

    reservation = object()
    adapters = build_story_video_adapters(
        settings,
        session_factory=sessions,  # type: ignore[arg-type]
        reservation=reservation,  # type: ignore[arg-type]
    )
    assert adapters.reservation is reservation  # type: ignore[union-attr]
    assert isinstance(adapters.quota, BillingVideoQuotaAdmission)  # type: ignore[union-attr]


def test_staging_refuses_local_test_before_any_other_policy_reason() -> None:
    # No Firebase configuration either: the video reason must be the one reported.
    with pytest.raises(ValidationError, match=_REFUSAL):
        Settings(_env_file=None, env="staging", story_video_adapters="local_test")  # type: ignore[call-arg]


def test_production_refuses_local_test_even_with_valid_firebase_and_runpod() -> None:
    with pytest.raises(ValidationError, match=_REFUSAL):
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            env="production",
            auth_provider="firebase",
            firebase_project_id="fixture-project",
            ai_provider="runpod",
            runpod_endpoint_id="fixture-endpoint",
            runpod_api_key_file=Path("/runtime/secrets/runpod-key"),
            story_video_adapters="local_test",
        )


@pytest.mark.parametrize("env", ["staging", "production"])
def test_unconfigured_starts_in_staging_and_production_and_composes_nothing(env: Any) -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        env=env,
        auth_provider="firebase",
        firebase_project_id="fixture-project",
        ai_provider="runpod" if env == "production" else "disabled",
        runpod_endpoint_id="fixture-endpoint" if env == "production" else "",
        runpod_api_key_file=Path("/runtime/secrets/runpod-key") if env == "production" else None,
        story_video_adapters="unconfigured",
    )
    assert settings.story_video_adapters == "unconfigured"
    assert build_story_video_adapters(settings) is None


@pytest.mark.parametrize("env", ["staging", "production"])
def test_the_process_does_not_start_with_the_local_pair_outside_local_and_test(
    monkeypatch: pytest.MonkeyPatch, env: str
) -> None:
    from sketch2life.infrastructure.config.settings import get_settings
    from sketch2life.interfaces.http.app import create_app

    monkeypatch.setenv("SKETCH2LIFE_ENV", env)
    monkeypatch.setenv("SKETCH2LIFE_STORY_VIDEO_ADAPTERS", "local_test")
    get_settings.cache_clear()
    try:
        with pytest.raises(ValidationError, match="local test video adapters"):
            create_app()
    finally:
        get_settings.cache_clear()


def test_the_default_port_timeout_is_bounded() -> None:
    assert Settings(_env_file=None).story_video_port_timeout_seconds == 5.0  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Settings(_env_file=None, story_video_port_timeout_seconds=0)  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Settings(_env_file=None, story_video_port_timeout_seconds=31)  # type: ignore[call-arg]


# ------------------------------------------------------------------------- accept-all behaviour
def test_the_reservation_is_accept_all_and_idempotent_per_key() -> None:
    adapter = LocalVideoComputeReservation(env="test")
    first = _reserve(adapter, "gen-1")
    again = _reserve(adapter, "gen-1")
    other = _reserve(adapter, "gen-2", key="k2")
    assert first.status is ReservationStatus.RESERVED
    assert first.reservation_ref == again.reservation_ref
    assert other.reservation_ref != first.reservation_ref
    assert adapter.release(scope=_SCOPE, reservation_ref="r", idempotency_key="k") is AckStatus.DONE
    settled = adapter.settle(
        scope=_SCOPE, reservation_ref="r", outcome="COMPLETED", idempotency_key="k"
    )
    assert settled is AckStatus.DONE


def test_the_quota_admission_is_accept_all_idempotent_and_detects_a_changed_payload() -> None:
    adapter = _quota()
    first = _admit(adapter, "gen-1")
    again = _admit(adapter, "gen-1")
    assert first.status is QuotaStatus.ACCEPTED and first.usage_ref == again.usage_ref
    assert _admit(adapter, "gen-1", fingerprint="other").status is QuotaStatus.IDEMPOTENCY_MISMATCH
    # accept-all: no count, no month, no scope ever refuses
    results = [_admit(adapter, f"gen-{index}", key=f"k{index}") for index in range(2, 60)]
    assert all(result.status is QuotaStatus.ACCEPTED for result in results)


def test_the_script_returns_fixed_outcomes_one_per_call_and_counts_nothing() -> None:
    script = VideoAdmissionScript()
    script.quotas.extend([QuotaStatus.QUOTA_EXCEEDED, QuotaStatus.UNAVAILABLE])
    script.reservations.append(ReservationStatus.COST_LIMIT_REACHED)
    script.releases.append(AckStatus.UNAVAILABLE)
    adapters = build_local_video_adapters(env="test", script=script)
    assert _reserve(adapters.reservation, "g1").status is ReservationStatus.COST_LIMIT_REACHED
    assert _admit(adapters.quota, "g1").status is QuotaStatus.QUOTA_EXCEEDED
    assert _admit(adapters.quota, "g2", key="k2").status is QuotaStatus.UNAVAILABLE
    # the queue is empty: back to accept-all, whatever the scope or the number of earlier calls
    assert _admit(adapters.quota, "g3", key="k3").status is QuotaStatus.ACCEPTED
    first = adapters.reservation.release(scope=_SCOPE, reservation_ref="r", idempotency_key="k")
    second = adapters.reservation.release(scope=_SCOPE, reservation_ref="r", idempotency_key="k")
    assert (first, second) == (AckStatus.UNAVAILABLE, AckStatus.DONE)


def test_a_reserved_key_keeps_its_reference_whatever_the_script_says_next() -> None:
    script = VideoAdmissionScript()
    adapter = LocalVideoComputeReservation(env="test", script=script)
    reference = _reserve(adapter, "g1").reservation_ref
    script.reservations.append(ReservationStatus.COST_LIMIT_REACHED)
    # the stored receipt answers, not the script
    assert _reserve(adapter, "g1").reservation_ref == reference
    assert script.reservations  # untouched


# --------------------------------------------------------------------------- scope rule (owner)
_FORBIDDEN_NAMES = re.compile(
    r"(balance|top_?up|price|prices|pricing|grant_?ledger|read_balance|monthly_|payment|"
    r"checkout|invoice|stripe|billing_plan|per_month|quota_remaining|units_left)",
    re.IGNORECASE,
)


def test_no_story_video_code_holds_quota_balance_price_or_payment_logic() -> None:
    offenders: list[str] = []
    for path in _STORY_VIDEO_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            name: str | None = None
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                name = node.name
            elif isinstance(node, ast.Name):
                name = node.id
            elif isinstance(node, ast.Attribute):
                name = node.attr
            elif isinstance(node, ast.arg):
                name = node.arg
            if name is not None and _FORBIDDEN_NAMES.search(name):
                offenders.append(f"{path.name}:{name}")
    assert offenders == []


def test_no_path_reads_the_organization_scope() -> None:
    """``ORGANIZATION`` stays a bare literal value of ``ScopeKind`` (the Teacher seam)."""

    for path in _STORY_VIDEO_FILES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "ORGANIZATION":
                assert path.name == "story_video.py" and "ports" in str(path), path
            if isinstance(node, ast.Compare):
                text = ast.unparse(node)
                assert "ORGANIZATION" not in text, (path.name, text)


def test_the_local_adapters_never_branch_on_the_scope_kind() -> None:
    source = (_SRC / "infrastructure" / "story_video" / "local_adapters.py").read_text(
        encoding="utf-8"
    )
    assert ".kind" not in source and "scope.kind" not in source
