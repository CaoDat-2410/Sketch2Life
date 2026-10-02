"""FastAPI composition root."""

import logging
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from sketch2life.application.ports.activity_ranker import ActivityRankerPort
from sketch2life.application.ports.child_preference_classifier import (
    ChildPreferenceClassifierPort,
)
from sketch2life.application.ports.pixi_motion_cycle import PixiMotionCycleIssue
from sketch2life.application.ports.pixi_show_planner import PixiShowPlannerPort
from sketch2life.application.services.auto_rig import AutoRigService
from sketch2life.application.services.ephemeral_sessions import EphemeralSessionService
from sketch2life.application.services.image_admission import Feat018ImageAdmission
from sketch2life.application.services.live_image_demo import LiveImageDemoService
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.pixi_topic_asset_candidates import load_topic_asset_catalog
from sketch2life.application.services.supervised_flow import SupervisedFlowService
from sketch2life.contracts.schemas.asr import AsrProfileId
from sketch2life.contracts.schemas.mobile_workflow import (
    MobileWorkflowResultV1,
    WorkflowFailureV1,
    WorkflowResultProvenanceV1,
)
from sketch2life.contracts.schemas.scene_exploration import SourceRegionV1
from sketch2life.contracts.schemas.workflow_records import SessionSnapshotV1
from sketch2life.infrastructure.ai.lightning_activity_ranker import LightningActivityRanker
from sketch2life.infrastructure.ai.lightning_child_preference_classifier import (
    LightningChildPreferenceClassifier,
)
from sketch2life.infrastructure.ai.lightning_client import (
    LightningAsrV2Adapter,
    UrllibJsonTransport,
    read_secret_file,
)
from sketch2life.infrastructure.ai.lightning_pixi_show_planner import (
    LightningPixiShowPlanner,
)
from sketch2life.infrastructure.ai.lightning_sam21 import LightningSam21SegmentationAdapter
from sketch2life.infrastructure.ai.lightning_scene_localization import (
    LightningSceneLocalizationAdapter,
)
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.ai.pixi_subject_crop import build_pixi_subject_crop
from sketch2life.infrastructure.catalog.activity_semantics import load_activity_semantic_catalog
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library
from sketch2life.infrastructure.catalog.pixi_show_assets import (
    PixiShowAssetService,
    PixiShowAssetUnavailable,
)
from sketch2life.infrastructure.catalog.workflow_metadata import FileWorkflowCatalogMetadata
from sketch2life.infrastructure.config.settings import Settings, get_settings
from sketch2life.infrastructure.media_validation.av_image_decoder import AvImageDecoder
from sketch2life.infrastructure.storage.in_memory import (
    InMemoryArtifactStore,
    InMemoryIdempotencyStore,
    InMemoryJobStore,
    InMemorySessionRepository,
)
from sketch2life.infrastructure.storage.in_memory_auto_rig_grants import (
    InMemoryRigPackageGrantStore,
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
from sketch2life.interfaces.http.routers.child_preferences import (
    router as child_preferences_router,
)
from sketch2life.interfaces.http.routers.health import router as health_router
from sketch2life.interfaces.http.routers.images import router as images_router
from sketch2life.interfaces.http.routers.sessions import router as sessions_router
from sketch2life.interfaces.http.routers.supervised_flow import (
    renderer_source_router,
)
from sketch2life.interfaces.http.routers.supervised_flow import (
    router as supervised_flow_router,
)

_LOGGER = logging.getLogger("sketch2life.api")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
_SAFE_CONTEXT_PROFILE_FIELDS = frozenset(
    {
        "contract_name",
        "contract_version",
        "age_months",
        "child_profile",
        "profile_declared_by",
        "profile_recorded_at",
        "interests",
        "dislikes",
        "adult_confirmed_progress",
        "activity_id",
        "objective_id",
        "confirmed_at",
        "confirmed_by",
        "readiness_ids",
        "available_material_option_ids",
        "adult_supervision_available",
        "learning_support_ids",
        "candidate_activity_ids",
        "adult_participating",
        "caregiver_participating",
        "supervision_confirmed_activity_ids",
    }
)


def create_app(
    *,
    session_service: EphemeralSessionService | None = None,
    live_image_demo_service: LiveImageDemoService | None = None,
    supervised_flow_service: SupervisedFlowService | None = None,
    auto_rig_service: AutoRigService | None = None,
    child_preference_classifier: ChildPreferenceClassifierPort | None = None,
    activity_ranker: ActivityRankerPort | None = None,
    pixi_show_planner: PixiShowPlannerPort | None = None,
    pixi_show_asset_service: PixiShowAssetService | None = None,
) -> FastAPI:
    """Create the local image-only API composition root with ephemeral adapters."""
    application = FastAPI(
        title="Sketch2Life API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
    )

    @application.exception_handler(RequestValidationError)
    async def handle_request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        is_context_options_route = request.url.path.endswith(
            "/p1/context-options"
        ) or request.url.path.endswith("/p1/context-options/finalize")
        if not is_context_options_route:
            return JSONResponse(status_code=422, content={"detail": "request contract invalid"})

        safe_paths: list[str] = []
        safe_codes: list[str] = []
        for issue in exc.errors():
            location = issue.get("loc", ())
            parts = [str(part) for part in location if str(part) not in {"body", "query"}]
            safe_parts = [
                part
                if part in _SAFE_CONTEXT_PROFILE_FIELDS
                else "item"
                if part.isdigit()
                else "field"
                for part in parts[:8]
            ]
            path = ".".join(safe_parts) or "request"
            code = issue.get("type")
            safe_paths.append(path[:160])
            safe_codes.append(
                str(code)[:64]
                if isinstance(code, str) and re.fullmatch(r"[a-z0-9_.-]+", code)
                else "validation_error"
            )

        request_id = request.headers.get("X-Request-ID", "validation-error")
        if not _SAFE_ID.fullmatch(request_id):
            request_id = "validation-error"
        path_session_id = request.path_params.get("session_id", "unknown-session")
        if not isinstance(path_session_id, str) or not _SAFE_ID.fullmatch(path_session_id):
            path_session_id = "unknown-session"
        raw_expected_version = request.headers.get("X-Expected-Session-Version", "0")
        expected_version = int(raw_expected_version) if raw_expected_version.isdigit() else 0
        expected_version = min(expected_version, 2**31 - 1)

        # Only bounded Pydantic locations and error codes are logged. Submitted values,
        # free text, request bodies, and Pydantic's human-readable messages are excluded.
        _LOGGER.warning(
            "request_validation_failed route=p1_context_options request_id=%s fields=%s codes=%s",
            request_id,
            ",".join(dict.fromkeys(safe_paths)) or "request",
            ",".join(dict.fromkeys(safe_codes)) or "validation_error",
        )
        failure = MobileWorkflowResultV1(
            status="FAILED",
            request_id=request_id,
            session_id=path_session_id,
            expected_session_version=expected_version,
            observed_session_version=expected_version,
            provenance=WorkflowResultProvenanceV1(
                producer="APPLICATION",
                component="request-validation",
                component_version="1.0",
                source_contracts=(
                    (
                        "P1ContextOptionsRequestV2"
                        if request.url.path.endswith("/p1/context-options/finalize")
                        else "P1ContextOptionsQueryV1"
                        if request.method == "GET"
                        else "P1ContextOptionsRequestV1"
                    ),
                ),
            ),
            failure=WorkflowFailureV1(
                domain="TRANSPORT",
                code="REQUEST_VALIDATION_FAILED",
                retryable=False,
                safe_message=(
                    "Một số thông tin hồ sơ chưa hợp lệ. Hãy kiểm tra lựa chọn rồi thử lại."
                ),
            ),
        )
        return JSONResponse(status_code=422, content=failure.model_dump(mode="json"))

    application.add_middleware(BoundedImageUploadMiddleware)
    scene_localizer = None
    pixi_show_planner_required = False
    if session_service is None:
        artifacts = InMemoryArtifactStore()
        idempotency = InMemoryIdempotencyStore()
        renderer_source_grants = InMemoryRendererSourceGrantStore()
        settings = get_settings()
        pixi_show_planner_required = settings.pixi_show_planner_enabled
        if child_preference_classifier is None:
            child_preference_classifier = _configured_lightning_preference_classifier(settings)
        if activity_ranker is None:
            activity_ranker = _configured_lightning_activity_ranker(settings)
        if pixi_show_planner is None:
            pixi_show_planner = _configured_lightning_pixi_show_planner(settings)
        if auto_rig_service is None:
            auto_rig_service = AutoRigService(
                artifacts=artifacts,
                grants=InMemoryRigPackageGrantStore(),
                jobs=InMemoryJobStore(),
                segmenter=_configured_lightning_sam21(settings, artifacts),
            )
        session_service = EphemeralSessionService(
            sessions=InMemorySessionRepository[SessionSnapshotV1](),
            idempotency=idempotency,
            artifacts=artifacts,
            workflow_data=InMemoryDemoWorkflowStore(),
            idle_ttl_seconds=get_settings().session_idle_ttl_seconds,
        )
        if live_image_demo_service is None:
            vision = _configured_lightning_vision(settings, artifacts)
            asr = _configured_lightning_asr(settings, artifacts)
            # Geometry localization is intentionally disabled in the normal demo path.  The
            # owner requested the fast topic-direction flow; Pixi keeps its whole-drawing
            # fallback until a separate localization slice is approved again.
            scene_localizer = None
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
                scene_localizer=scene_localizer,
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
            feature_root = asset_catalog_path.resolve().parents[2]
            if pixi_show_asset_service is None:
                pixi_show_asset_service = PixiShowAssetService(
                    feature_root=feature_root,
                    assets=topic_assets,
                    motion_cycle_manifest_path=(
                        asset_catalog_path.parent / "motion-cycle-review-manifest.rev1.json"
                    ),
                    motion_cycle_dev_preview_catalog_path=(
                        feature_root
                        / "assets"
                        / "applied"
                        / "motion-cycle-local-preview-catalog.v1.json"
                    ),
                    allow_dev_preview=settings.pixi_sprite_cycle_dev_preview_allowed,
                )

            def load_pixi_subject_crop(
                session_id: str,
                source_ref: str,
                source_sha256: str,
                mask_ref: str,
                mask_sha256: str,
            ) -> tuple[bytes, str, SourceRegionV1]:
                source_item = artifacts.get(source_ref)
                mask_item = artifacts.get(mask_ref)
                if (
                    source_item is None
                    or mask_item is None
                    or source_item[0].session_id != session_id
                    or mask_item[0].session_id != session_id
                    or source_item[0].sha256 != source_sha256
                    or mask_item[0].sha256 != mask_sha256
                    or source_item[0].content_type not in {"image/png", "image/jpeg"}
                    or mask_item[0].content_type != "image/png"
                ):
                    from sketch2life.infrastructure.ai.pixi_subject_crop import (
                        PixiSubjectCropUnavailable,
                    )

                    raise PixiSubjectCropUnavailable from None
                return build_pixi_subject_crop(source_item[1], mask_item[1])

            def issue_pixi_motion_cycle(
                cycle_id: str,
                *,
                start_seconds: float,
                end_seconds: float,
                x: float,
                y: float,
            ) -> PixiMotionCycleIssue:
                if pixi_show_asset_service is None:
                    return PixiMotionCycleIssue(None, "ASSET_UNAVAILABLE")
                try:
                    cycle = pixi_show_asset_service.issue_motion_cycle_read(
                        cycle_id,
                        start_seconds=start_seconds,
                        end_seconds=end_seconds,
                        x=x,
                        y=y,
                    )
                    return PixiMotionCycleIssue(cycle)
                except PixiShowAssetUnavailable as error:
                    return PixiMotionCycleIssue(None, error.reason_code)

            supervised_flow_service = SupervisedFlowService(
                sessions=session_service,
                idempotency=idempotency,
                p1_compiler=p1_compiler,
                topic_assets=topic_assets,
                semantic_catalog=semantic_catalog,
                semantic_catalog_v2=semantic_catalog_v2,
                catalog_metadata=catalog_metadata,
                scene_localizer=scene_localizer,
                renderer_source_capability_issuer=(
                    live_image_demo_service.issue_renderer_source_capability
                    if live_image_demo_service is not None
                    else None
                ),
                auto_rig_service=auto_rig_service,
                activity_ranker=activity_ranker,
                pixi_show_planner=pixi_show_planner,
                pixi_show_planner_required=pixi_show_planner_required,
                pixi_show_crop_provider=load_pixi_subject_crop,
                pixi_show_asset_issuer=pixi_show_asset_service.issue_reads,
                pixi_motion_cycle_issuer=issue_pixi_motion_cycle,
            )
    application.state.session_service = session_service
    application.state.live_image_demo_service = live_image_demo_service
    application.state.supervised_flow_service = supervised_flow_service
    application.state.auto_rig_service = auto_rig_service
    application.state.child_preference_classifier = child_preference_classifier
    application.state.activity_ranker = activity_ranker
    application.state.pixi_show_planner = pixi_show_planner
    application.state.pixi_show_asset_service = pixi_show_asset_service
    application.include_router(health_router)
    application.include_router(child_preferences_router)
    application.include_router(sessions_router)
    application.include_router(images_router)
    application.include_router(supervised_flow_router)
    application.include_router(renderer_source_router)
    renderer_dist = Path(__file__).resolve().parents[5] / "packages" / "art-renderer" / "dist-demo"
    if renderer_dist.is_dir():
        application.mount(
            "/renderer",
            StaticFiles(directory=renderer_dist, html=True),
            name="pixi-renderer",
        )
    return application


def _configured_lightning_preference_classifier(
    settings: Settings,
) -> LightningChildPreferenceClassifier | None:
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
    return LightningChildPreferenceClassifier(transport=transport)


def _configured_lightning_activity_ranker(
    settings: Settings,
) -> LightningActivityRanker | None:
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
            request_timeout_seconds=min(settings.ai_request_timeout_seconds, 30.0),
        )
    except (OSError, ValueError):
        return None
    return LightningActivityRanker(transport=transport)


def _configured_lightning_pixi_show_planner(
    settings: Settings,
) -> LightningPixiShowPlanner | None:
    if (
        not settings.pixi_show_planner_enabled
        or settings.env == "test"
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
            request_timeout_seconds=min(settings.ai_request_timeout_seconds, 60.0),
        )
    except (OSError, ValueError):
        return None
    return LightningPixiShowPlanner(
        transport=transport,
        endpoint_path=settings.lightning_pixi_show_path,
    )


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


def _configured_lightning_sam21(
    settings: Settings, artifacts: InMemoryArtifactStore
) -> LightningSam21SegmentationAdapter | None:
    if (
        not settings.lightning_sam21_enabled
        or settings.env == "test"
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

    def write_artifact(session_id: str, content_type: str, body: bytes) -> object:
        return artifacts.put(session_id=session_id, content_type=content_type, body=body)

    return LightningSam21SegmentationAdapter(
        transport=transport,
        artifact_loader=load_artifact,
        artifact_writer=write_artifact,
        endpoint_path=settings.lightning_sam21_path,
    )


def _configured_lightning_scene_localizer(
    settings: Settings, artifacts: InMemoryArtifactStore
) -> LightningSceneLocalizationAdapter | None:
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

    return LightningSceneLocalizationAdapter(
        transport=transport,
        artifact_loader=load_artifact,
    )
