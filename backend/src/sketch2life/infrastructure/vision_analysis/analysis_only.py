"""Analysis-only assistance and T4/T5 source binding for the synthetic pilot."""

from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import replace

from sketch2life.application.ports.assistance import ResolvedSource
from sketch2life.application.ports.vision_analysis import (
    AdmissionPort,
    AnalysisSourcePort,
)
from sketch2life.application.services.assistance import AssistanceDependencies, AssistanceService
from sketch2life.domain.vision_analysis import AdmissionReceipt, SourceSnapshot

ResolvedCanvasSource = Callable[[str, str], ResolvedSource | None]


def build_analysis_only_assistance(dependencies: AssistanceDependencies) -> AssistanceService:
    """Build the existing service with only its downstream Sketch effects disabled."""

    return AssistanceService(replace(dependencies, analysis_only=True))


class A2AnalysisSourceAdmissionPort(AnalysisSourcePort, AdmissionPort):
    """Expose only the verified source and receipt returned by the A2 canvas adapter.

    ``resolve_canvas_source`` must load the persisted request and use its stored
    ``CheckpointRef`` with ``PostgresCanvasSourceAdapter``. The callback must not accept a
    client-supplied checkpoint. The short-lived context binding prevents an admission lookup
    from substituting a receipt belonging to another source or organization.
    """

    def __init__(self, resolve_canvas_source: ResolvedCanvasSource) -> None:
        self._resolve_canvas_source = resolve_canvas_source
        self._admission: ContextVar[tuple[str, str, AdmissionReceipt] | None] = ContextVar(
            f"a2-analysis-admission-{id(self)}", default=None
        )

    def resolve(self, snapshot_ref: str, *, organization_id: str) -> SourceSnapshot | None:
        self._admission.set(None)
        try:
            resolved = self._resolve_canvas_source(organization_id, snapshot_ref)
        except Exception:
            return None
        if (
            resolved is None
            or resolved.snapshot.snapshot_ref != snapshot_ref
            or resolved.snapshot.organization_id != organization_id
            or resolved.admission is None
        ):
            return None
        self._admission.set((organization_id, snapshot_ref, resolved.admission))
        return resolved.snapshot

    def receipt_for(
        self,
        render_ref: str,
        render_sha256: str,
        *,
        organization_id: str,
    ) -> AdmissionReceipt | None:
        binding = self._admission.get()
        self._admission.set(None)
        if binding is None or binding[0] != organization_id:
            return None
        receipt = binding[2]
        if receipt.render_ref != render_ref or receipt.render_sha256 != render_sha256:
            return None
        return receipt


__all__ = [
    "A2AnalysisSourceAdmissionPort",
    "ResolvedCanvasSource",
    "build_analysis_only_assistance",
]
