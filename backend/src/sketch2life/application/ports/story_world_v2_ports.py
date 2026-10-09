"""Milestone-2 *interfaces only*. No adapter, engine, API or authorization here.

These contracts describe future server-owned approval and durable media boundaries.
Passing a caller-created snapshot is NOT proof of approval: an adapter must read it
from trusted server storage and compare the live session/package/script/source/masks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from sketch2life.contracts.schemas.story_strokes_v2 import SourceObjectStrokesV2
from sketch2life.contracts.schemas.story_world_v2 import ScenePlanV2

if TYPE_CHECKING:
    from sketch2life.application.services.story_world_model import SourceAssetRegistry


@dataclass(frozen=True, slots=True)
class ServerApprovalSnapshotV2:
    """Future immutable, server-fetched adult review record; not an input DTO."""

    record_id: str
    record_sha256: str
    session_id: str
    session_version: int
    package_hash: str
    story_script_sha256: str
    source_image_sha256: str
    approved_event_ids: frozenset[str]
    reviewed_mask_sha256_by_object: tuple[tuple[str, str], ...]
    reviewer_identity_ref: str
    approved_at: str


class ServerApprovalVerificationPort(Protocol):
    """Must fetch trusted Gate A/B and exact adult-review records server-side."""

    def verify_for_render(
        self, *, session_id: str, session_version: int, package_hash: str,
        story_script_sha256: str, source_image_sha256: str,
        event_ids: tuple[str, ...], mask_sha256_by_object: tuple[tuple[str, str], ...],
    ) -> ServerApprovalSnapshotV2: ...


@dataclass(frozen=True, slots=True)
class SourceMaskProposalV2:
    object_id: str
    mask_ref: str
    mask_sha256: str
    source_image_sha256: str
    review_status: Literal["NEEDS_MASK_REVIEW"] = "NEEDS_MASK_REVIEW"


class SourceObjectSegmentationPort(Protocol):
    """Propose masks for human review; proposals alone cannot enter registry."""

    def propose_masks(
        self, *, source_image_ref: str, source_image_sha256: str,
        object_hints: tuple[str, ...],
    ) -> tuple[SourceMaskProposalV2, ...]: ...


class DurableAssetStoragePort(Protocol):
    """Persist byte-verified assets with session-scoped, restart-safe refs."""

    def put(
        self, *, session_id: str, package_hash: str, object_id: str,
        media_type: str, content: bytes, sha256: str,
    ) -> str: ...

    def get_verified(self, *, session_id: str, asset_ref: str, sha256: str) -> bytes: ...


class ObjectAwareStrokePort(Protocol):
    """Extract source-bound per-object strokes; does not authorize a job."""

    def extract_object(
        self, registry: SourceAssetRegistry, object_id: str,
    ) -> SourceObjectStrokesV2: ...


class SceneMotionTransitionPort(Protocol):
    """Future action/pose/transition execution; must reject unsupported actions."""

    def render_motion(
        self, *, scene: ScenePlanV2, stroke_artifact_ref: str,
        previous_scene_state_sha256: str | None,
    ) -> str: ...


class ApprovedNewAssetGenerationPort(Protocol):
    """Future generation after exact adult approval; result requires separate review."""

    def generate_candidate(
        self, *, package_hash: str, object_id: str, approved_event_id: str,
        approval_record_id: str, appearance_request: str,
    ) -> str: ...
