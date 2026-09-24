"""FastAPI composition root."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from sketch2life.application.services.ephemeral_sessions import EphemeralSessionService
from sketch2life.application.services.image_admission import Feat018ImageAdmission
from sketch2life.application.services.live_image_demo import LiveImageDemoService
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.pixi_topic_asset_candidates import load_topic_asset_catalog
from sketch2life.application.services.supervised_flow import SupervisedFlowService
from sketch2life.application.services.whiteboard_video_job import (
    UnconfiguredWhiteboardVideoPipeline,
    WhiteboardVideoJobService,
)
from sketch2life.application.services.whiteboard_video_pipeline import WhiteboardVideoPipeline
from sketch2life.contracts.schemas.asr import AsrProfileId
from sketch2life.contracts.schemas.workflow_records import SessionSnapshotV1
from sketch2life.infrastructure.ai.lightning_client import (
    LightningAsrV2Adapter,
    UrllibJsonTransport,
    read_secret_file,
)
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.catalog.activity_semantics import load_activity_semantic_catalog
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library
from sketch2life.infrastructure.catalog.workflow_metadata import FileWorkflowCatalogMetadata
from sketch2life.infrastructure.config.settings import Settings, get_settings
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder
from sketch2life.infrastructure.storage.in_memory import (
    InMemoryArtifactStore,
    InMemoryIdempotencyStore,
    InMemorySessionRepository,
)
from sketch2life.infrastructure.storage.in_memory_demo_workflow import (
    InMemoryDemoWorkflowStore,
)
from sketch2life.infrastructure.storage.in_memory_renderer_source_grants import (
    InMemoryRendererSourceGrantStore,
)
from sketch2life.interfaces.http.middleware.bounded_image_upload import (
    BoundedImageUploadMiddleware,
)
from sketch2life.interfaces.http.routers.health import router as health_router
from sketch2life.interfaces.http.routers.images import router as images_router
from sketch2life.interfaces.http.routers.sessions import router as sessions_router
from sketch2life.interfaces.http.routers.supervised_flow import (
    renderer_source_router,
)
from sketch2life.interfaces.http.routers.whiteboard_video import router as whiteboard_video_router
from sketch2life.interfaces.http.routers.supervised_flow import (
    router as supervised_flow_router,
)

_LOGGER = logging.getLogger("sketch2life.api")


def create_app(
    *,
    session_service: EphemeralSessionService | None = None,
    live_image_demo_service: LiveImageDemoService | None = None,
    supervised_flow_service: SupervisedFlowService | None = None,
    whiteboard_video_job_service: WhiteboardVideoJobService | None = None,
    whiteboard_video_pipeline: WhiteboardVideoPipeline | None = None,
) -> FastAPI:
    """Create the local image-only API composition root with ephemeral adapters."""
    application = FastAPI(
        title="Sketch2Life API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )
    application.add_middleware(BoundedImageUploadMiddleware)
    if session_service is None:
        artifacts = InMemoryArtifactStore()
        idempotency = InMemoryIdempotencyStore()
        renderer_source_grants = InMemoryRendererSourceGrantStore()
        session_service = EphemeralSessionService(
            sessions=InMemorySessionRepository[SessionSnapshotV1](),
            idempotency=idempotency,
            artifacts=artifacts,
            workflow_data=InMemoryDemoWorkflowStore(),
            idle_ttl_seconds=get_settings().session_idle_ttl_seconds,
        )
        if live_image_demo_service is None:
            settings = get_settings()
            vision = _configured_lightning_vision(settings, artifacts)
            asr = _configured_lightning_asr(settings, artifacts)
            _LOGGER.info(
                "ai_adapters_configured provider=%s base_url_configured=%s "
                "token_file_configured=%s "
                "vision=%s asr=%s vision_profile=%s asr_profile=%s vision_path=%s asr_path=%s",
                settings.ai_provider,
                bool(settings.lightning_ai_base_url),
                settings.lightning_ai_token_file is not None,
                vision is not None,
                asr is not None,
                settings.lightning_model_profile,
                settings.lightning_asr_profile,
                settings.lightning_vision_v2_path,
                settings.lightning_asr_path,
            )
            live_image_demo_service = LiveImageDemoService(
                sessions=session_service,
                artifacts=artifacts,
                idempotency=idempotency,
                admission=Feat018ImageAdmission(AvImageDecoder()),
                vision=vision,
                renderer_source_grants=renderer_source_grants,
                asr=asr,
                asr_profile_id=AsrProfileId(settings.lightning_asr_profile),
            )
        if supervised_flow_service is None:
            repo_root = Path(__file__).resolve().parents[5]
            p1_library = load_p1_template_library(
                repo_root, include_mvp=True, include_expansion=True
            )
            semantic_catalog = load_activity_semantic_catalog(repo_root)
            semantic_catalog_v2 = load_activity_semantic_catalog_v2(
                repo_root, include_expansion=True
            )
            catalog_metadata = FileWorkflowCatalogMetadata(repo_root)
            p1_compiler = P1ExperienceCompiler(
                p1_library.templates,
                p1_library.objective_titles_vi,
            )
            asset_catalog_path = (
                repo_root
                / "features"
                / "FEAT-028-pixi-topic-asset-library"
                / "assets"
                / "generated"
                / "asset-catalog.v2.json"
            )
            topic_assets = load_topic_asset_catalog(asset_catalog_path)
            supervised_flow_service = SupervisedFlowService(
                sessions=session_service,
                idempotency=idempotency,
                p1_compiler=p1_compiler,
                topic_assets=topic_assets,
                semantic_catalog=semantic_catalog,
                semantic_catalog_v2=semantic_catalog_v2,
                catalog_metadata=catalog_metadata,
                renderer_source_capability_issuer=(
                    live_image_demo_service.issue_renderer_source_capability
                    if live_image_demo_service is not None
                    else None
                ),
            )
    application.state.session_service = session_service
    application.state.live_image_demo_service = live_image_demo_service
    application.state.supervised_flow_service = supervised_flow_service
    if whiteboard_video_job_service is None:
        whiteboard_video_job_service = WhiteboardVideoJobService(
            pipeline=whiteboard_video_pipeline or UnconfiguredWhiteboardVideoPipeline()
        )
    application.state.whiteboard_video_job_service = whiteboard_video_job_service
    application.include_router(health_router)
    application.include_router(sessions_router)
    application.include_router(images_router)
    application.include_router(supervised_flow_router)
    application.include_router(renderer_source_router)
    application.include_router(whiteboard_video_router)
    renderer_dist = Path(__file__).resolve().parents[5] / "packages" / "art-renderer" / "dist-demo"
    if renderer_dist.is_dir():
        application.mount(
            "/renderer",
            StaticFiles(directory=renderer_dist, html=True),
            name="pixi-renderer",
        )
    return application


def _configured_lightning_vision(
    settings: Settings, artifacts: InMemoryArtifactStore
) -> LightningVisionV2Adapter | None:
    if (
        settings.env == "test"
        or settings.ai_provider != "lightning_dev"
        or not settings.lightning_ai_base_url
        or settings.lightning_ai_token_file is None
    ):
        return None
    try:
        token = read_secret_file(settings.lightning_ai_token_file)
        transport = UrllibJsonTransport(
            base_url=settings.lightning_ai_base_url,
            token=token,
            request_timeout_seconds=settings.ai_request_timeout_seconds,
        )
    except (OSError, ValueError):
        return None

    def load_artifact(artifact_ref: str) -> bytes:
        stored = artifacts.get(artifact_ref)
        if stored is None:
            raise KeyError("image artifact is unavailable")
        return stored[1]

    return LightningVisionV2Adapter(
        transport=transport,
        artifact_loader=load_artifact,
        endpoint_path=settings.lightning_vision_v2_path,
    )


def _configured_lightning_asr(
    settings: Settings, artifacts: InMemoryArtifactStore
) -> LightningAsrV2Adapter | None:
    if (
        settings.env == "test"
        or settings.ai_provider != "lightning_dev"
        or not settings.lightning_ai_base_url
        or settings.lightning_ai_token_file is None
    ):
        return None
    try:
        token = read_secret_file(settings.lightning_ai_token_file)
        transport = UrllibJsonTransport(
            base_url=settings.lightning_ai_base_url,
            token=token,
            request_timeout_seconds=settings.ai_request_timeout_seconds,
        )
    except (OSError, ValueError):
        return None

    def load_artifact(artifact_ref: str) -> bytes:
        stored = artifacts.get(artifact_ref)
        if stored is None:
            raise KeyError("audio artifact is unavailable")
        return stored[1]

    return LightningAsrV2Adapter(
        transport=transport,
        artifact_loader=load_artifact,
        endpoint_path=settings.lightning_asr_path,
    )
