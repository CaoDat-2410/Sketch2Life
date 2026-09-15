"""Application-owned ports for composing the backend workflow.

The workflow service consumes these protocols only. Concrete JSON/file adapters
live outside the application layer and are assembled by an interface
composition root.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from sketch2life.application.services.media_validation import (
    MediaValidationRequest,
)
from sketch2life.contracts.schemas.activity_semantics import SemanticActivityProfileV1
from sketch2life.contracts.schemas.media_validation import MediaValidationResultV1
from sketch2life.contracts.schemas.p1_experience import (
    ActivityTemplateV1,
    SemanticAnchorSetV1,
    SemanticMatchEvidenceV1,
)
from sketch2life.contracts.schemas.semantic_personalization_v2 import (
    ConfirmedSceneUnderstandingV2,
    SemanticActivityMatchV2,
    SemanticActivityProfileV2,
)
from sketch2life.contracts.schemas.workflow_demo import PixiAssetSelectionV1


class MediaValidationPort(Protocol):
    def validate(self, request: MediaValidationRequest) -> MediaValidationResultV1: ...


class TemplateLibraryPort(Protocol):
    @property
    def templates(self) -> tuple[ActivityTemplateV1, ...]: ...

    @property
    def objective_titles_vi(self) -> Mapping[str, str]: ...


class SemanticCatalogPort(Protocol):
    def profile_for(self, activity_id: str) -> SemanticActivityProfileV1: ...

    def match(
        self,
        anchor_set: SemanticAnchorSetV1,
        profile: SemanticActivityProfileV1,
    ) -> SemanticMatchEvidenceV1 | None: ...


class SemanticCatalogV2Port(Protocol):
    def profile_for(self, activity_id: str) -> SemanticActivityProfileV2: ...

    def match_scene(
        self,
        scene: ConfirmedSceneUnderstandingV2,
        profile: SemanticActivityProfileV2,
    ) -> SemanticActivityMatchV2 | None: ...

    def to_legacy_evidence(self, match: SemanticActivityMatchV2) -> SemanticMatchEvidenceV1: ...


class AssetCatalogPort(Protocol):
    def validate_all_age_bands(self) -> None: ...

    def resolve(self, age_band: str) -> PixiAssetSelectionV1: ...


class ActivityCatalogMetadataPort(Protocol):
    """Read-only authored metadata needed by the workflow handoff."""

    def primary_material_ids(self, activity_id: str) -> tuple[str, ...]: ...

    def duration_spec(self, activity_id: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True, slots=True)
class WorkflowDependencies:
    """Immutable dependency bundle assembled outside the application layer."""

    media_validator: MediaValidationPort
    template_library: TemplateLibraryPort
    semantic_catalog: SemanticCatalogPort
    asset_catalog: AssetCatalogPort
    catalog_metadata: ActivityCatalogMetadataPort
    semantic_catalog_v2: SemanticCatalogV2Port | None = None
