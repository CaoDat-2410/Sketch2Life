"""BE2-07 exact knowledge export adapter for the BE2-08 source port.

This adapter composes the existing candidate application contracts. It does not
create a job, call a provider, or claim a durable cross-feature transaction.
"""

from __future__ import annotations

from sketch2life.application.ports.ai_jobs import Principal
from sketch2life.application.ports.knowledge_video_media import (
    RenderAttempt,
    VideoSourceMaterial,
)
from sketch2life.application.services.knowledge_bundle import KnowledgeBundleService
from sketch2life.domain.knowledge_video.model import ExactRef, VideoError
from sketch2life.infrastructure.knowledge_bundle.coordination import (
    KnowledgeCommitCoordinator,
)


class KnowledgeScriptVideoSourceResolver:
    """Resolve BE2-08's pinned source through the real BE2-07 service.

    ``principal`` is a trusted server-side principal supplied by composition.
    The process-local coordinator orders a read against BE2-07 fixture
    publications while this resolver reads and validates the exact export.
    """

    def __init__(
        self,
        service: KnowledgeBundleService,
        principal: Principal,
        coordinator: KnowledgeCommitCoordinator,
    ) -> None:
        self._service = service
        self._principal = principal
        self._coordinator = coordinator

    def load(self, attempt: RenderAttempt) -> VideoSourceMaterial:
        pin = attempt.run.pin
        if self._principal.organization_id != pin.organization_id:
            raise VideoError("VIDEO_SOURCE_UNAVAILABLE")

        with self._coordinator.read():
            resolution = self._service.resolve_exact(
                self._principal,
                pin.bundle.ref,
                pin.bundle.version,
                pin.bundle.hash,
            )
            export = resolution.export
            if not resolution.ready or export is None:
                raise VideoError("VIDEO_SOURCE_UNAVAILABLE")
            if (
                export.organization_id != pin.organization_id
                or export.session_id != pin.session_id
                or export.bundle_id != pin.bundle.ref
                or export.bundle_version != pin.bundle.version
                or export.bundle_hash != pin.bundle.hash
                or export.editorial_revision != pin.editorial_revision
                or export.context_revision != pin.context_revision
                or export.audience_revision != pin.audience_revision
            ):
                raise VideoError("VIDEO_SOURCE_MISMATCH")

            source_refs = tuple(
                sorted(
                    (
                        ExactRef(
                            item.ref.source_id,
                            item.ref.revision,
                            item.ref.sha256,
                        )
                        for item in export.source_records
                    ),
                    key=lambda ref: (ref.ref, ref.version, ref.hash),
                )
            )
            pinned_refs = tuple(
                sorted(pin.sources, key=lambda ref: (ref.ref, ref.version, ref.hash))
            )
            if source_refs != pinned_refs or not export.script_text.strip():
                raise VideoError("VIDEO_SOURCE_MISMATCH")

            return VideoSourceMaterial(pin.bundle, pin.digest(), export.script_text)

    def assert_current(self, attempt: RenderAttempt) -> None:
        """Re-resolve the exact bundle at each BE2-08 source boundary."""

        self.load(attempt)
