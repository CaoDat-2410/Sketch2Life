"""Synthetic PostgreSQL boundary fixtures for the approved GA1 canvas limits."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException
from sketch2life.infrastructure.persistence.core_models import (
    CoreAggregateRevisionModel,
    CoreCanvasOperationModel,
)
from sqlalchemy import select
from test_be1_synthetic_pilot_postgres import (
    PilotHarness,
    _JsonResponse,
    _session_path,
    _synthetic_id,
    _t4_append_two_strokes,
)
from test_be1_synthetic_pilot_postgres import (
    block_non_loopback_sockets as block_non_loopback_sockets,
)
from test_be1_synthetic_pilot_postgres import (
    pilot_harness as pilot_harness,
)


def _seed_capacity(
    harness: PilotHarness, strokes: int, points_per_stroke: int
) -> tuple[str, str, str, str, str]:
    session_id, _child, canvas_id, grant, device_key, _ids = _t4_append_two_strokes(harness)
    with harness.session_factory.begin() as db:
        original = db.scalars(
            select(CoreCanvasOperationModel).where(
                CoreCanvasOperationModel.organization_id == harness.organization_id,
                CoreCanvasOperationModel.canvas_id == canvas_id,
            )
        ).all()
        template = original[0]
        for row in original:
            row.operation_payload = {
                **row.operation_payload,
                "points": [{"x": 0.2, "y": 0.3}] * points_per_stroke,
            }
        for revision in range(4, strokes + 2):
            db.add(
                CoreCanvasOperationModel(
                    operation_id=_synthetic_id(),
                    organization_id=harness.organization_id,
                    canvas_id=canvas_id,
                    session_id=session_id,
                    turn_id=template.turn_id,
                    participant_id=template.participant_id,
                    document_epoch=1,
                    resulting_revision=revision,
                    request_fingerprint="0" * 64,
                    operation_payload={
                        **template.operation_payload,
                        "points": [{"x": 0.2, "y": 0.3}] * points_per_stroke,
                    },
                )
            )
        aggregate = db.get(CoreAggregateRevisionModel, canvas_id)
        assert aggregate is not None
        aggregate.revision = strokes + 1
        turn_id = template.turn_id
    return session_id, canvas_id, grant, device_key, turn_id


def _command(turn_id: str, revision: int, points: int = 2) -> dict[str, Any]:
    return {
        "operation_id": _synthetic_id(),
        "turn_id": turn_id,
        "document_epoch": 1,
        "expected_revision": revision,
        "profile_version": "CanvasOperationProfileV1",
        "operation_payload": {
            "kind": "stroke",
            "points": [{"x": 0.2, "y": 0.3}] * points,
            "color": "#FFD21F",
            "size": 5,
        },
    }


def _post(
    harness: PilotHarness, scope: tuple[str, str, str, str, str], body: dict[str, Any]
) -> _JsonResponse:
    session, _canvas, grant, key, _turn = scope
    return harness.client.post(
        _session_path(harness, session, "/canvas/operations"),
        headers={
            "X-Be1-Grant": grant,
            "X-Be1-Device-Key": key,
            "Idempotency-Key": body["operation_id"],
        },
        json=body,
    )


def test_stroke_limit_boundary_replay_and_stale_precede_capacity(
    pilot_harness: PilotHarness,
) -> None:
    scope = _seed_capacity(pilot_harness, 499, 2)
    body = _command(scope[-1], 500)
    accepted = _post(pilot_harness, scope, body)
    assert accepted.status_code == 200, accepted.text
    replay = _post(pilot_harness, scope, body)
    assert replay.status_code == 200, replay.text
    assert replay.json()["status"] == "replayed"
    assert replay.json()["resulting_revision"] == 501
    stale = _post(pilot_harness, scope, _command(scope[-1], 500))
    assert stale.status_code == 409 and stale.json()["code"] == "STALE_AGGREGATE"
    over = _post(pilot_harness, scope, _command(scope[-1], 501))
    assert over.status_code == 409 and over.json()["code"] == "CANVAS_CAPACITY_REACHED"


def test_point_limit_exact_boundary_and_next_stroke_rejected(pilot_harness: PilotHarness) -> None:
    scope = _seed_capacity(pilot_harness, 119, 504)  # 59,976 accepted points.
    accepted = _post(pilot_harness, scope, _command(scope[-1], 120, 24))
    assert accepted.status_code == 200, accepted.text
    over = _post(pilot_harness, scope, _command(scope[-1], 121))
    assert over.status_code == 409 and over.json()["code"] == "CANVAS_CAPACITY_REACHED"


@pytest.mark.parametrize(("strokes", "points"), [(501, 2), (119, 512)])
def test_export_legacy_oversize_source_fails_closed(
    pilot_harness: PilotHarness, strokes: int, points: int
) -> None:
    from sketch2life.interfaces.http.routers.be1_canvas import build_canvas_source_export

    session, canvas, _grant, _key, _turn = _seed_capacity(pilot_harness, strokes, points)
    with pilot_harness.session_factory() as db, pytest.raises(HTTPException) as denied:
        build_canvas_source_export(
            db,
            organization_id=pilot_harness.organization_id,
            session_id=session,
            canvas_id=canvas,
            document_epoch=1,
        )
    assert denied.value.status_code == 409
    assert isinstance(denied.value.detail, dict)
    assert denied.value.detail["code"] == "CANVAS_SOURCE_TOO_LARGE"


def test_handoff_deadline_includes_source_export(
    pilot_harness: PilotHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sketch2life.infrastructure.canvas_render import limits
    from sketch2life.interfaces.http.be1_runtime import get_verified_device
    from sketch2life.interfaces.http.routers import be1_artifacts, be1_canvas

    harness = pilot_harness
    session, _child, _canvas, grant, key, _ops = _t4_append_two_strokes(harness)
    clock = [100.0]
    monkeypatch.setattr(limits, "monotonic", lambda: clock[0])
    original_export = be1_canvas.build_canvas_source_export

    def slow_export(*args: Any, **kwargs: Any) -> Any:
        result = original_export(*args, **kwargs)
        clock[0] += 7.0
        return result

    monkeypatch.setattr(be1_canvas, "build_canvas_source_export", slow_export)
    with harness.session_factory() as db:
        device = get_verified_device(
            grant_id=grant,
            device_key=key,
            db=db,
            runtime=harness.runtime,
        )
        with pytest.raises(HTTPException) as denied:
            be1_artifacts.create_canvas_render_handoff(db, harness.runtime, device)
    assert denied.value.status_code == 503
    assert isinstance(denied.value.detail, dict)
    assert denied.value.detail["code"] == "CANVAS_RENDER_DEADLINE_EXCEEDED"
