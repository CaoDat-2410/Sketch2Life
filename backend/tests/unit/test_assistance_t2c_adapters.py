from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import pytest
from sketch2life.contracts.schemas.be1_runtime import CanvasSourceExportV1, CanvasSourceOperationV1
from sketch2life.domain.assistance import CheckpointRef
from sketch2life.domain.vision_analysis import SourceVerdict, verify_source
from sketch2life.infrastructure.canvas_render.renderer import (
    CanvasAdmissionReceiptV1,
    render_canvas_source,
)
from sqlalchemy import Connection


@dataclass
class _Result:
    rows: list[dict[str, object]]

    def mappings(self) -> _Result:
        return self

    def all(self) -> list[dict[str, object]]:
        return self.rows


class _Connection:
    def __init__(self, batches: list[list[dict[str, object]]]) -> None:
        self.batches = batches

    def execute(self, statement: object) -> _Result:
        return _Result(self.batches.pop(0))


def source_fixture() -> CanvasSourceExportV1:
    payload = {
        "canvas_operation_profile_id": "canvas-operation-profile-v1",
        "kind": "stroke",
        "points": [{"x": 0.2, "y": 0.2}, {"x": 0.8, "y": 0.8}],
        "color": "#FFD21F",
        "size": 5,
    }
    operation = CanvasSourceOperationV1(
        operation_id="synthetic-stroke",
        participant_id="synthetic-child",
        document_epoch=1,
        resulting_revision=2,
        operation_payload=payload,
        payload_sha256=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    )
    return CanvasSourceExportV1.from_operations(
        organization_id="synthetic-org",
        session_id="synthetic-session",
        canvas_id="synthetic-canvas",
        document_epoch=1,
        document_revision=2,
        operations=[operation],
    )


def source_adapter_fixture() -> tuple[Any, CanvasSourceExportV1, dict[str, bytes], list[Any]]:
    from sketch2life.infrastructure.assistance.be1_canvas_source_adapter import (
        PostgresCanvasSourceAdapter,
    )

    source = source_fixture()
    rendered = render_canvas_source(source)
    receipt = CanvasAdmissionReceiptV1.create(
        derivation=rendered.derivation,
        render_artifact_ref="synthetic-render",
        admitted_content_sha256=rendered.derivation.render_sha256,
        decoder_container="png_pipe",
        decoder_codec="png",
        decoder_pixel_format="rgb24",
        decoded_width=1024,
        decoded_height=1024,
        admitted_at=datetime(2026, 11, 2, tzinfo=UTC),
    )
    artifacts = {
        "synthetic-render": rendered.png_bytes,
        "synthetic-receipt": receipt.to_json_bytes(),
    }
    lineage = [
        "be1-session:synthetic-session",
        "be1-canvas:synthetic-canvas",
        f"be1-canvas-source:{source.source_sha256}",
        "be1-child:synthetic-child",
    ]
    batches = [
        [
            {
                "asset_ref": "synthetic-render",
                "asset_version": 1,
                "organization_id": source.organization_id,
                "content_sha256": receipt.render_sha256,
                "media_type": "image/png",
                "source_refs": lineage.copy(),
                "derived_from_ref": source.source_ref,
            }
        ],
        [
            {
                "asset_ref": "synthetic-receipt",
                "asset_version": 1,
                "organization_id": source.organization_id,
                "content_sha256": hashlib.sha256(artifacts["synthetic-receipt"]).hexdigest(),
                "media_type": "application/vnd.sketch2life.canvas-admission-receipt+json",
                "source_refs": lineage.copy(),
                "derived_from_ref": "synthetic-render",
            }
        ],
    ]
    adapter = PostgresCanvasSourceAdapter(
        cast(Connection, _Connection(batches)),
        session_id=source.session_id,
        export_source=lambda org, canvas: source,
        load_artifact=artifacts.get,
        environment="test",
        pilot_enabled=True,
    )
    return adapter, source, artifacts, batches


def _ref(source: CanvasSourceExportV1, **changes: Any) -> CheckpointRef:
    return CheckpointRef(
        **{
            "checkpoint_id": source.source_ref,
            "document_epoch": source.document_epoch,
            "server_sequence": source.document_revision,
            "hash": source.source_sha256,
            **changes,
        }
    )


def test_t4_export_and_t5_receipt_produce_exact_admitted_source() -> None:
    adapter, source, _, _ = source_adapter_fixture()
    resolved = adapter.resolve(source.organization_id, source.canvas_id, _ref(source))
    assert resolved is not None
    assert resolved.snapshot.checkpoint.checksum_sha256 == source.source_sha256
    assert resolved.snapshot.checkpoint.checkpoint_id == source.source_ref
    assert resolved.server_sequence == source.document_revision
    assert (
        verify_source(
            resolved.snapshot,
            resolved.admission,
            organization_id=source.organization_id,
            canvas_id=source.canvas_id,
        )
        is SourceVerdict.PROCEED
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("checkpoint_id", "teacher-checkpoint"),
        ("hash", "0" * 64),
        ("document_epoch", 2),
        ("server_sequence", 3),
    ],
)
def test_stale_or_teacher_checkpoint_binding_is_refused(field: str, value: object) -> None:
    adapter, source, _, _ = source_adapter_fixture()
    assert (
        adapter.resolve(source.organization_id, source.canvas_id, _ref(source, **{field: value}))
        is None
    )


@pytest.mark.parametrize(
    "batch,field,value",
    [
        (0, "organization_id", "another-org"),
        (1, "organization_id", "another-org"),
        (0, "source_refs", []),
        (1, "source_refs", []),
        (0, "derived_from_ref", "teacher-checkpoint"),
        (1, "derived_from_ref", "another-render"),
        (0, "content_sha256", "0" * 64),
        (1, "content_sha256", "0" * 64),
        (0, "media_type", "image/jpeg"),
        (1, "media_type", "application/json"),
    ],
)
def test_metadata_scope_lineage_and_hash_mismatch_refuses(
    batch: int, field: str, value: object
) -> None:
    adapter, source, _, batches = source_adapter_fixture()
    batches[batch][0][field] = value
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


@pytest.mark.parametrize("artifact", ["synthetic-render", "synthetic-receipt"])
def test_missing_artifact_refuses(artifact: str) -> None:
    adapter, source, artifacts, _ = source_adapter_fixture()
    del artifacts[artifact]
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


def test_exporter_runtime_error_fails_closed() -> None:
    adapter, source, _, _ = source_adapter_fixture()

    def fail_export(_organization_id: str, _canvas_id: str) -> CanvasSourceExportV1:
        raise RuntimeError("synthetic exporter failure")

    adapter._export_source = fail_export
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


def test_artifact_loader_runtime_error_fails_closed() -> None:
    adapter, source, _, _ = source_adapter_fixture()

    def fail_load(_artifact_ref: str) -> bytes:
        raise RuntimeError("synthetic artifact loader failure")

    adapter._load_artifact = fail_load
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


def test_malformed_export_field_accessor_runtime_error_fails_closed() -> None:
    adapter, source, _, _ = source_adapter_fixture()

    class MalformedExport:
        @property
        def model_dump(self) -> object:
            raise RuntimeError("synthetic malformed export field failure")

    adapter._export_source = lambda _organization_id, _canvas_id: MalformedExport()  # type: ignore[assignment]
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


@pytest.mark.parametrize("batch", [0, 1])
def test_ambiguous_persisted_versions_refuse(batch: int) -> None:
    adapter, source, _, batches = source_adapter_fixture()
    batches[batch].append(batches[batch][0].copy())
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


def test_noncanonical_receipt_refuses_even_with_matching_metadata_hash() -> None:
    adapter, source, artifacts, batches = source_adapter_fixture()
    artifacts["synthetic-receipt"] += b"\n"
    batches[1][0]["content_sha256"] = hashlib.sha256(artifacts["synthetic-receipt"]).hexdigest()
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


@pytest.mark.parametrize("artifact", ["synthetic-render", "synthetic-receipt"])
def test_changed_artifact_bytes_refuse(artifact: str) -> None:
    adapter, source, artifacts, _ = source_adapter_fixture()
    artifacts[artifact] += b"corrupt"
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None


def test_receipt_render_source_binding_is_checked_separately() -> None:
    adapter, source, artifacts, batches = source_adapter_fixture()
    payload = json.loads(artifacts["synthetic-receipt"])
    payload["render_source_binding_sha256"] = "0" * 64
    del payload["receipt_binding_sha256"]

    def canonical(value: object) -> bytes:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

    payload["receipt_binding_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    artifacts["synthetic-receipt"] = canonical(payload)
    batches[1][0]["content_sha256"] = hashlib.sha256(artifacts["synthetic-receipt"]).hexdigest()
    assert adapter.resolve(source.organization_id, source.canvas_id, _ref(source)) is None
