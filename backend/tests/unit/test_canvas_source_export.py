from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest
from pydantic import ValidationError


def _schema_types():
    from sketch2life.contracts.schemas.be1_runtime import (
        CanvasSourceExportV1,
        CanvasSourceOperationV1,
    )

    return CanvasSourceExportV1, CanvasSourceOperationV1


def _sha256(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _operations() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for revision, operation_id, color in (
        (2, "synthetic-op-1", "#FFD21F"),
        (3, "synthetic-op-2", "#1685F8"),
    ):
        payload = {
            "kind": "stroke",
            "points": [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
            "color": color,
            "size": 5,
            "canvas_operation_profile_id": "canvas-operation-profile-v1",
        }
        result.append(
            {
                "operation_id": operation_id,
                "participant_id": "synthetic-child-1",
                "document_epoch": 1,
                "resulting_revision": revision,
                "operation_payload": payload,
                "payload_sha256": _sha256(payload),
            }
        )
    return result


def _valid_export(**overrides: Any) -> dict[str, Any]:
    CanvasSourceExportV1, CanvasSourceOperationV1 = _schema_types()
    operations = [CanvasSourceOperationV1.model_validate(item) for item in _operations()]
    return CanvasSourceExportV1.from_operations(
        organization_id=overrides.get("organization_id", "synthetic-org-1"),
        session_id=overrides.get("session_id", "synthetic-session-1"),
        canvas_id=overrides.get("canvas_id", "synthetic-canvas-1"),
        document_epoch=overrides.get("document_epoch", 1),
        document_revision=overrides.get("document_revision", 3),
        operations=overrides.get("operations", operations),
    ).model_dump(mode="json")


def test_canvas_source_export_requires_complete_ordered_matching_manifest() -> None:
    CanvasSourceExportV1, _ = _schema_types()

    valid = CanvasSourceExportV1.model_validate(_valid_export())
    assert [item.resulting_revision for item in valid.operations] == [2, 3]
    assert [item.operation_id for item in valid.operations] == [
        item.operation_id for item in valid.operation_manifest
    ]

    missing_manifest = _valid_export()
    missing_manifest["operation_manifest"] = missing_manifest["operation_manifest"][:1]
    with pytest.raises(ValidationError):
        CanvasSourceExportV1.model_validate(missing_manifest)

    revision_gap = _valid_export()
    revision_gap["operations"][1]["resulting_revision"] = 4
    revision_gap["operation_manifest"][1]["resulting_revision"] = 4
    with pytest.raises(ValidationError):
        CanvasSourceExportV1.model_validate(revision_gap)


def test_canvas_source_export_rejects_extra_fields_and_unbound_payload_changes() -> None:
    CanvasSourceExportV1, _ = _schema_types()

    extra_field = _valid_export()
    extra_field["untrusted_client_document"] = {"kind": "stroke"}
    with pytest.raises(ValidationError):
        CanvasSourceExportV1.model_validate(extra_field)

    changed_payload = _valid_export()
    changed_payload["operations"][0]["operation_payload"]["color"] = "#FF596C"
    with pytest.raises(ValidationError):
        CanvasSourceExportV1.model_validate(changed_payload)


def test_canvas_source_export_rejects_uppercase_sha256() -> None:
    CanvasSourceExportV1, _ = _schema_types()
    invalid = _valid_export()
    invalid["source_sha256"] = "D" * 64

    with pytest.raises(ValidationError):
        CanvasSourceExportV1.model_validate(invalid)


def test_canvas_source_export_digests_are_stable_and_bind_scope_and_order() -> None:
    CanvasSourceExportV1, CanvasSourceOperationV1 = _schema_types()
    base = _valid_export()
    stable = CanvasSourceExportV1.model_validate(_valid_export())
    assert base == stable.model_dump(mode="json")

    other_session = CanvasSourceExportV1.model_validate(
        _valid_export(session_id="synthetic-session-2")
    )
    assert other_session.canonical_document_sha256 == stable.canonical_document_sha256
    assert other_session.source_sha256 != stable.source_sha256

    first, second = _operations()
    swapped_order = [
        {
            **first,
            "operation_id": second["operation_id"],
            "operation_payload": second["operation_payload"],
            "payload_sha256": second["payload_sha256"],
        },
        {
            **second,
            "operation_id": first["operation_id"],
            "operation_payload": first["operation_payload"],
            "payload_sha256": first["payload_sha256"],
        },
    ]
    reordered = [CanvasSourceOperationV1.model_validate(item) for item in swapped_order]
    alternate = CanvasSourceExportV1.from_operations(
        organization_id="synthetic-org-1",
        session_id="synthetic-session-1",
        canvas_id="synthetic-canvas-1",
        document_epoch=1,
        document_revision=3,
        operations=reordered,
    )
    assert alternate.canonical_document_sha256 != stable.canonical_document_sha256
    assert alternate.operation_manifest_sha256 != stable.operation_manifest_sha256
    assert alternate.source_sha256 != stable.source_sha256
