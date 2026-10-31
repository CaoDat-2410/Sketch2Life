"""Pure contract tests for the versioned BE1 canvas stroke profile."""

from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from types import SimpleNamespace

import pytest
from sketch2life.contracts.schemas.be1_runtime import CanvasOperationRequest
from sketch2life.domain.core_foundation import (
    CANVAS_OPERATION_PROFILE_V1_ID,
    CANVAS_OPERATION_PROFILE_V1_VERSION,
    CoreErrorCode,
    CoreRuleViolation,
    bind_canvas_operation_profile_v1_payload,
    canvas_operation_profile_v1_configuration,
    validate_canvas_operation_profile_v1,
)


def _stroke(
    *,
    points: object | None = None,
    color: object = "#FFD21F",
    size: object = 5,
    kind: object = "stroke",
) -> dict[str, object]:
    return {
        "kind": kind,
        "points": points if points is not None else [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
        "color": color,
        "size": size,
    }


def _assert_invalid(payload: Mapping[str, object]) -> None:
    with pytest.raises(CoreRuleViolation) as caught:
        validate_canvas_operation_profile_v1(payload)
    assert caught.value.code == CoreErrorCode.CANVAS_PROFILE_INVALID


def test_profile_v1_configuration_pins_canvas_palette_and_width_ratios() -> None:
    assert CANVAS_OPERATION_PROFILE_V1_ID == "canvas-operation-profile-v1"
    assert CANVAS_OPERATION_PROFILE_V1_VERSION == "CanvasOperationProfileV1"
    assert canvas_operation_profile_v1_configuration() == {
        "profile_id": "canvas-operation-profile-v1",
        "version": "CanvasOperationProfileV1",
        "aspect_ratio": {"width": 1, "height": 1},
        "logical_canvas": {"width": 400, "height": 400},
        "background": "#FFFFFF",
        "operation_mode": "strokes-only",
        "history_mode": "append-only",
        "palette": ["#FFD21F", "#FF596C", "#1685F8", "#31C978", "#9250E8"],
        "stroke_widths": [
            {"token": 5, "ratio": 0.0125},
            {"token": 9, "ratio": 0.0225},
            {"token": 14, "ratio": 0.035},
        ],
        "minimum_points": 2,
        "maximum_points": 512,
        "coordinate_precision_places": 6,
    }


@pytest.mark.parametrize("color", ["#FFD21F", "#FF596C", "#1685F8", "#31C978", "#9250E8"])
@pytest.mark.parametrize("size", [5, 9, 14])
def test_profile_v1_accepts_supported_strokes(color: str, size: int) -> None:
    payload = _stroke(color=color, size=size)
    assert validate_canvas_operation_profile_v1(payload) == payload


@pytest.mark.parametrize(
    "payload",
    [
        _stroke(points=[]),
        _stroke(points=[{"x": 0.5, "y": 0.5}]),
        _stroke(points=[{"x": 0, "y": 0}] * 513),
        _stroke(points=[{"x": -0.01, "y": 0.5}, {"x": 0.5, "y": 0.5}]),
        _stroke(points=[{"x": 1.01, "y": 0.5}, {"x": 0.5, "y": 0.5}]),
        _stroke(points=[{"x": True, "y": 0.5}, {"x": 0.5, "y": 0.5}]),
        _stroke(points=[{"x": float("nan"), "y": 0.5}, {"x": 0.5, "y": 0.5}]),
        _stroke(points=[{"x": float("inf"), "y": 0.5}, {"x": 0.5, "y": 0.5}]),
        _stroke(points=[{"x": 0.1234567, "y": 0.5}, {"x": 0.5, "y": 0.5}]),
        _stroke(points=[{"x": 0.5, "y": 0.5, "pressure": 0.5}, {"x": 0.6, "y": 0.6}]),
        _stroke(color="#000000"),
        _stroke(size=7),
        _stroke(kind="erase"),
        {**_stroke(), "client_profile_id": "canvas-operation-profile-v1"},
    ],
)
def test_profile_v1_rejects_values_outside_the_frozen_contract(
    payload: dict[str, object],
) -> None:
    _assert_invalid(payload)


def test_profile_v1_rejects_non_object_points() -> None:
    _assert_invalid(_stroke(points=[None, {"x": 0.5, "y": 0.5}]))


def test_profile_v1_rejects_missing_coordinates() -> None:
    _assert_invalid(_stroke(points=[{"x": 0.1}, {"x": 0.2, "y": 0.3}]))


def test_unprofiled_historical_session_keeps_legacy_payload_interpretation() -> None:
    legacy_payload = {"legacy_operation": "opaque"}
    assert (
        bind_canvas_operation_profile_v1_payload(
            session_configuration={}, profile_version=None, operation_payload=legacy_payload
        )
        == legacy_payload
    )


def test_client_cannot_opt_a_historical_session_into_profile_v1() -> None:
    with pytest.raises(CoreRuleViolation) as caught:
        bind_canvas_operation_profile_v1_payload(
            session_configuration={},
            profile_version=CANVAS_OPERATION_PROFILE_V1_VERSION,
            operation_payload=_stroke(),
        )
    assert caught.value.code == CoreErrorCode.CANVAS_PROFILE_MISMATCH


def test_profiled_session_requires_exact_echo_and_persists_server_id() -> None:
    accepted = bind_canvas_operation_profile_v1_payload(
        session_configuration={
            "canvas_operation_profile": canvas_operation_profile_v1_configuration()
        },
        profile_version=CANVAS_OPERATION_PROFILE_V1_VERSION,
        operation_payload=_stroke(),
    )
    assert accepted["canvas_operation_profile_id"] == CANVAS_OPERATION_PROFILE_V1_ID


@pytest.mark.parametrize(
    ("configuration", "profile_version", "payload"),
    [
        (
            {"canvas_operation_profile": canvas_operation_profile_v1_configuration()},
            None,
            _stroke(),
        ),
        (
            {"canvas_operation_profile": canvas_operation_profile_v1_configuration()},
            "CanvasOperationProfileV0",
            _stroke(),
        ),
        (
            {},
            None,
            {**_stroke(), "canvas_operation_profile_id": CANVAS_OPERATION_PROFILE_V1_ID},
        ),
        (
            {"canvas_operation_profile": {"profile_id": "changed"}},
            CANVAS_OPERATION_PROFILE_V1_VERSION,
            _stroke(),
        ),
    ],
)
def test_profile_binding_rejects_mismatch_or_client_asserted_provenance(
    configuration: dict[str, object],
    profile_version: str | None,
    payload: dict[str, object],
) -> None:
    with pytest.raises(CoreRuleViolation) as caught:
        bind_canvas_operation_profile_v1_payload(
            session_configuration=configuration,
            profile_version=profile_version,
            operation_payload=payload,
        )
    assert caught.value.code == CoreErrorCode.CANVAS_PROFILE_MISMATCH


@pytest.mark.parametrize(
    "color",
    [["#FFD21F"], {"a": 1}, None, 1, True, "", "#ffd21f"],
)
def test_untrusted_color_values_are_rejected_as_typed_profile_errors(color: object) -> None:
    _assert_invalid(_stroke(color=color))


@pytest.mark.parametrize("size", [[], {}, None, True, "5", 10**100])
def test_untrusted_width_values_are_rejected_as_typed_profile_errors(size: object) -> None:
    _assert_invalid(_stroke(size=size))


@pytest.mark.parametrize("points", [None, {}, "points", 7, [None, {"x": 0.5, "y": 0.5}]])
def test_untrusted_point_values_are_rejected_as_typed_profile_errors(points: object) -> None:
    payload = _stroke()
    payload["points"] = points
    _assert_invalid(payload)


@pytest.mark.parametrize("coordinate", [[], {}, None, True, "0.1", 10**100, float("inf")])
def test_untrusted_coordinate_values_are_rejected_as_typed_profile_errors(
    coordinate: object,
) -> None:
    _assert_invalid(_stroke(points=[{"x": coordinate, "y": 0.2}, {"x": 0.3, "y": 0.4}]))


def test_legacy_canvas_fingerprint_matches_pre_g1_payload_and_profile_changes_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sketch2life.interfaces.http.routers import be1_canvas

    captured: list[str] = []
    session_configuration: dict[str, object] = {}

    def apply_canvas_operation(**kwargs: object) -> SimpleNamespace:
        captured.append(str(kwargs["request_fingerprint"]))
        return SimpleNamespace(status=SimpleNamespace(value="accepted"), resulting_revision=2)

    monkeypatch.setattr(be1_canvas, "_require_device_path", lambda *_args: None)
    monkeypatch.setattr(
        be1_canvas,
        "_require_group_eligibility",
        lambda *_args, **_kwargs: SimpleNamespace(configuration=session_configuration),
    )
    monkeypatch.setattr(
        be1_canvas,
        "_store",
        lambda _runtime: SimpleNamespace(
            get_receipt=lambda **_kwargs: None,
            current_revision=lambda *_args, **_kwargs: 1,
        ),
    )
    monkeypatch.setattr(
        be1_canvas.CoreFoundationApplication,
        "apply_canvas_operation",
        apply_canvas_operation,
    )
    device = SimpleNamespace(
        grant=SimpleNamespace(organization_id="synthetic-org", grant_id="synthetic-grant"),
        session=SimpleNamespace(session_id="synthetic-session"),
        membership=SimpleNamespace(group_id="synthetic-group", child_id="synthetic-child"),
        turn=SimpleNamespace(canvas_id="synthetic-group", document_epoch=1),
        principal=object(),
        scope=object(),
    )

    def send(configuration: dict[str, object], payload: CanvasOperationRequest) -> None:
        session_configuration.clear()
        session_configuration.update(configuration)
        be1_canvas.append_canvas_operation(
            "synthetic-org",
            "synthetic-session",
            payload,
            idempotency_key="synthetic-idempotency-key",
            device=device,
            runtime=SimpleNamespace(settings=object()),
            db=SimpleNamespace(scalar=lambda _statement: 0),
        )

    legacy_payload = {"legacy_operation": "opaque"}
    legacy_request = CanvasOperationRequest.model_validate(
        {
            "operation_id": "synthetic-operation",
            "turn_id": "synthetic-turn",
            "document_epoch": 1,
            "expected_revision": 1,
            "operation_payload": legacy_payload,
        }
    )
    # Read-only HEAD inspection confirms the pre-G1 fingerprint had these five JSON keys.
    legacy_fingerprint_payload = {
        "operation_id": "synthetic-operation",
        "turn_id": "synthetic-turn",
        "document_epoch": 1,
        "expected_revision": 1,
        "operation_payload": legacy_payload,
    }
    expected_legacy = sha256(
        json.dumps(
            legacy_fingerprint_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    send({}, legacy_request)
    assert captured[-1] == expected_legacy

    profiled_request = CanvasOperationRequest.model_validate(
        {
            "operation_id": "synthetic-operation",
            "turn_id": "synthetic-turn",
            "document_epoch": 1,
            "expected_revision": 1,
            "profile_version": CANVAS_OPERATION_PROFILE_V1_VERSION,
            "operation_payload": _stroke(),
        }
    )
    send(
        {"canvas_operation_profile": canvas_operation_profile_v1_configuration()},
        profiled_request,
    )
    assert captured[-1] != expected_legacy
