"""Named constructors for the local, in-memory demo adapters."""

from dataclasses import dataclass

from sketch2life.application.services.ephemeral_sessions import EphemeralSessionService
from sketch2life.contracts.schemas.workflow_records import SessionSnapshotV1
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.storage.in_memory import (
    InMemoryArtifactStore,
    InMemoryIdempotencyStore,
    InMemorySessionRepository,
)
from sketch2life.infrastructure.storage.in_memory_demo_workflow import InMemoryDemoWorkflowStore
from sketch2life.infrastructure.storage.in_memory_renderer_source_grants import (
    InMemoryRendererSourceGrantStore,
)


@dataclass(frozen=True)
class DemoStores:
    artifacts: InMemoryArtifactStore
    idempotency: InMemoryIdempotencyStore
    renderer_source_grants: InMemoryRendererSourceGrantStore
    workflow_data: InMemoryDemoWorkflowStore


def build_demo_stores() -> DemoStores:
    """Create the isolated in-memory stores shared by local demo services."""
    return DemoStores(
        artifacts=InMemoryArtifactStore(),
        idempotency=InMemoryIdempotencyStore(),
        renderer_source_grants=InMemoryRendererSourceGrantStore(),
        workflow_data=InMemoryDemoWorkflowStore(),
    )


def build_ephemeral_session_service(
    *, stores: DemoStores, settings: Settings
) -> EphemeralSessionService:
    """Build the demo session service from its explicit local adapters."""
    return EphemeralSessionService(
        sessions=InMemorySessionRepository[SessionSnapshotV1](),
        idempotency=stores.idempotency,
        artifacts=stores.artifacts,
        workflow_data=stores.workflow_data,
        idle_ttl_seconds=settings.session_idle_ttl_seconds,
    )
