"""Bind an authoritative BE1 operation export to its persisted T5 render and receipt."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping

from sqlalchemy import Connection, select

from sketch2life.application.ports.assistance import ResolvedSource
from sketch2life.contracts.schemas.be1_runtime import CanvasSourceExportV1
from sketch2life.domain.assistance import CheckpointRef
from sketch2life.domain.vision_analysis import (
    AdmissionReceipt,
    CheckpointBinding,
    RenderBinding,
    SourceSnapshot,
    SourceVerdict,
    verify_source,
)
from sketch2life.infrastructure.canvas_render.renderer import (
    CANVAS_EXPORT_SPEC_VERSION,
    CANVAS_RENDERER_VERSION,
    CanvasAdmissionReceiptV1,
    RenderDerivationV1,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel

ExportSource = Callable[[str, str], CanvasSourceExportV1 | None]
ArtifactLoader = Callable[[str], bytes | None]
RECEIPT_MEDIA_TYPE = "application/vnd.sketch2life.canvas-admission-receipt+json"


class PostgresCanvasSourceAdapter:
    """Read metadata on the caller's connection; never open/commit a transaction.

    ``export_source`` must be the trusted scoped T4 operation exporter, injected by the
    caller. No Teacher checkpoint snapshot or arbitrary upload is a source for this port.
    Duplicate stored render/receipt candidates are unavailable rather than picked by order.
    """

    def __init__(
        self,
        connection: Connection,
        *,
        session_id: str,
        export_source: ExportSource,
        load_artifact: ArtifactLoader,
        environment: str,
        pilot_enabled: bool,
    ) -> None:
        self._connection = connection
        self._session_id = session_id
        self._export_source = export_source
        self._load_artifact = load_artifact
        self._enabled = environment in {"local", "test"} and pilot_enabled is True

    def resolve(
        self, organization_id: str, canvas_id: str, ref: CheckpointRef
    ) -> ResolvedSource | None:
        if not self._enabled:
            return None
        try:
            source = self._export_source(organization_id, canvas_id)
            if source is None:
                return None
            # Revalidate even an instance made with model_construct/model_copy by a caller.
            source = CanvasSourceExportV1.model_validate(source.model_dump(mode="json"))
            if (
                source.organization_id != organization_id
                or source.canvas_id != canvas_id
                or source.session_id != self._session_id
                or ref.checkpoint_id != source.source_ref
                or ref.hash != source.source_sha256
                or ref.document_epoch != source.document_epoch
                or ref.server_sequence != source.document_revision
            ):
                return None
            lineage = [
                f"be1-session:{source.session_id}",
                f"be1-canvas:{source.canvas_id}",
                f"be1-canvas-source:{source.source_sha256}",
                *(
                    f"be1-child:{child}"
                    for child in sorted(
                        {operation.participant_id for operation in source.operations}
                    )
                ),
            ]
            render = self._metadata(organization_id, source.source_ref, "image/png", lineage)
            if render is None:
                return None
            render_ref = str(render["asset_ref"])
            receipt_meta = self._metadata(organization_id, render_ref, RECEIPT_MEDIA_TYPE, lineage)
            if receipt_meta is None:
                return None
            render_bytes = self._load_artifact(render_ref)
            receipt_ref = str(receipt_meta["asset_ref"])
            receipt_bytes = self._load_artifact(receipt_ref)
            if (
                not render_bytes
                or not receipt_bytes
                or hashlib.sha256(render_bytes).hexdigest() != render["content_sha256"]
                or hashlib.sha256(receipt_bytes).hexdigest() != receipt_meta["content_sha256"]
            ):
                return None
            receipt = CanvasAdmissionReceiptV1(**json.loads(receipt_bytes))
            if (
                receipt.to_json_bytes() != receipt_bytes
                or receipt.source_ref != source.source_ref
                or receipt.source_sha256 != source.source_sha256
                or receipt.render_artifact_ref != render_ref
                or receipt.render_sha256 != render["content_sha256"]
                or receipt.export_spec_version != CANVAS_EXPORT_SPEC_VERSION
                or receipt.renderer_version != CANVAS_RENDERER_VERSION
            ):
                return None
            # The receipt's own binding is distinct from the versioned render/source binding.
            RenderDerivationV1(
                contract="CanvasRenderDerivationV1",
                source_ref=receipt.source_ref,
                source_sha256=receipt.source_sha256,
                export_spec_version=receipt.export_spec_version,
                renderer_version=receipt.renderer_version,
                pillow_version=receipt.pillow_version,
                width=receipt.width,
                height=receipt.height,
                mode=receipt.mode,
                background=receipt.background,
                media_type=receipt.media_type,
                render_sha256=receipt.render_sha256,
                render_source_binding_sha256=receipt.render_source_binding_sha256,
            )
            snapshot = SourceSnapshot(
                snapshot_ref=source.source_ref,
                organization_id=organization_id,
                checkpoint=CheckpointBinding(
                    source.source_ref,
                    canvas_id,
                    source.document_epoch,
                    source.document_revision,
                    source.source_sha256,
                ),
                render=RenderBinding(
                    render_ref,
                    receipt.render_sha256,
                    receipt.media_type,
                    source.source_ref,
                    source.source_sha256,
                    receipt.renderer_version,
                ),
            )
            admission = AdmissionReceipt(
                receipt_ref,
                str(receipt_meta["content_sha256"]),
                render_ref,
                receipt.render_sha256,
                "PASS",
                receipt.admission_policy_version,
            )
            if (
                verify_source(
                    snapshot, admission, organization_id=organization_id, canvas_id=canvas_id
                )
                is not SourceVerdict.PROCEED
            ):
                return None
            return ResolvedSource(snapshot, source.document_revision, admission)
        except Exception:
            # Corrupt/missing metadata and malformed artifacts never imply admitted content.
            return None

    def _metadata(
        self, organization_id: str, parent_ref: str, media_type: str, lineage: list[str]
    ) -> Mapping[str, object] | None:
        table = CoreAssetMetadataModel.__table__
        rows = (
            self._connection.execute(
                select(table).where(
                    table.c.organization_id == organization_id,
                    table.c.derived_from_ref == parent_ref,
                    table.c.media_type == media_type,
                )
            )
            .mappings()
            .all()
        )
        if len(rows) != 1:
            return None
        row = rows[0]
        if (
            row["organization_id"] != organization_id
            or row["derived_from_ref"] != parent_ref
            or row["media_type"] != media_type
            or row["source_refs"] != lineage
            or row["asset_version"] != 1
        ):
            return None
        return {str(key): value for key, value in row.items()}


__all__ = ["ArtifactLoader", "ExportSource", "PostgresCanvasSourceAdapter"]
