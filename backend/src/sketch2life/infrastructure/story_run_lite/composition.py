"""Create the isolated runtime only for an explicitly named local goal database."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from ipaddress import ip_interface
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url

from sketch2life.application.ports.story_run_lite import (
    StoryRunLiteRepositoryPort,
    StoryRunLiteStoryPort,
    StoryRunLiteVisionPort,
    VisionAttemptResult,
)
from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.domain.story_run_lite import OwnerScopeKind
from sketch2life.infrastructure.ai.modal_function_client import ModalStoryFunctionClient
from sketch2life.infrastructure.story_run_lite.clamav import ClamAvScanner
from sketch2life.infrastructure.story_run_lite.image_worker import WindowsJobObjectImageNormalizer
from sketch2life.infrastructure.story_run_lite.photo_bridge import (
    ModalFunctionPhotoVisionBridge,
    PhotoVisionBridge,
)
from sketch2life.infrastructure.story_run_lite.quarantine import QuarantineStore
from sketch2life.infrastructure.story_run_lite.repository import SqlStoryRunLiteRepository

_LOOPBACK_HOSTS = {"127.0.0.1", "::1"}


class UnavailableLoopbackVision(StoryRunLiteVisionPort):
    """Keep an unconfigured local service fail-closed without attempting a request."""

    def analyze(self, **_values: object) -> VisionAttemptResult:
        return VisionAttemptResult(state="FAILED", error_code="VISION_LOOPBACK_NOT_CONFIGURED")


@dataclass(slots=True)
class StoryRunLiteRuntime:
    engine: Engine
    repository: SqlStoryRunLiteRepository
    service: StoryRunLiteService
    vision: StoryRunLiteVisionPort


def goal_database_url(value: str, *, main_demo: bool = False) -> tuple[str, str]:
    """Reject non-loopback or non-goal databases before SQLAlchemy can connect."""

    try:
        url = make_url(value)
    except Exception:
        raise ValueError("StoryRun-lite database URL is invalid") from None
    if (
        url.get_backend_name() != "postgresql"
        or url.host not in _LOOPBACK_HOSTS
        or not url.database
        or not (
            url.database.startswith("storyrun_lite_")
            or (main_demo and url.database == "sketch2life")
        )
        or (main_demo and (url.host != "127.0.0.1" or url.port != 5433 or bool(url.query)))
        or url.username is None
    ):
        raise ValueError("StoryRun-lite accepts only an owned storyrun_lite_* database on loopback")
    return value, url.database


def verify_goal_database_owner(
    engine: Engine, expected_database: str, *, main_demo: bool = False
) -> str:
    """Read and verify the connected database identity; do not enumerate other databases."""

    with engine.connect() as connection:
        row = (
            connection.execute(
                text(
                    "SELECT current_database() AS database_name, current_user AS current_user, "
                    "pg_get_userbyid(datdba) AS database_owner, "
                    "inet_server_addr()::text AS server_address, "
                    "inet_server_port() AS server_port "
                    "FROM pg_database WHERE datname = current_database()"
                )
            )
            .mappings()
            .one()
        )
    try:
        server_address = str(ip_interface(row["server_address"]).ip)
    except (TypeError, ValueError):
        server_address = None
    if (
        row["database_name"] != expected_database
        or not (
            str(row["database_name"]).startswith("storyrun_lite_")
            or (main_demo and row["database_name"] == "sketch2life")
        )
        or row["current_user"] != row["database_owner"]
        or server_address not in _LOOPBACK_HOSTS
        or (main_demo and (server_address != "127.0.0.1" or row["server_port"] != 5433))
    ):
        raise RuntimeError(
            "StoryRun-lite database is not the explicitly owned loopback goal database"
        )
    return str(row["current_user"])


def _configured_vision(
    engine: Engine, repository: StoryRunLiteRepositoryPort
) -> StoryRunLiteVisionPort:
    mode = os.environ.get("STORYRUN_LITE_VISION_MODE", "loopback")
    loopback = os.environ.get("STORYRUN_LITE_VISION_LOOPBACK_URL")
    modal_url = os.environ.get("STORYRUN_LITE_MODAL_BASE_URL")
    modal_token = os.environ.get("STORYRUN_LITE_MODAL_TOKEN")
    modal_run = os.environ.get("STORYRUN_LITE_MODAL_RUN_ID")
    if mode == "loopback":
        if any(value is not None for value in (modal_url, modal_token, modal_run)):
            raise ValueError("StoryRun-lite Vision mode configuration is ambiguous")
        if loopback:
            return PhotoVisionBridge(engine=engine, repository=repository, base_url=loopback)
        return UnavailableLoopbackVision()
    if mode == "modal_live":
        if loopback is not None or not modal_url or not modal_token or not modal_run:
            raise ValueError("StoryRun-lite Modal live configuration is incomplete or ambiguous")
        return PhotoVisionBridge(
            engine=engine,
            repository=repository,
            base_url=modal_url,
            modal_live_token=modal_token,
            modal_live_run_id=modal_run,
        )
    if mode == "modal_function":
        if (
            loopback is not None
            or modal_url is not None
            or modal_token is not None
            or not modal_run
        ):
            raise ValueError(
                "StoryRun-lite Modal function configuration is incomplete or ambiguous"
            )
        return ModalFunctionPhotoVisionBridge(
            engine=engine,
            repository=repository,
            pinned_run_id=modal_run,
        )
    raise ValueError("StoryRun-lite Vision mode is invalid")


def _configured_story_generator() -> StoryRunLiteStoryPort | None:
    mode = os.environ.get("STORYRUN_LITE_STORY_MODE", "disabled")
    if mode == "disabled":
        return None
    if mode == "modal_function":
        return ModalStoryFunctionClient()
    raise ValueError("StoryRun-lite story generation mode is invalid")


def build_runtime(*, main_demo: bool = False) -> StoryRunLiteRuntime | None:
    value = os.environ.get("STORYRUN_LITE_DATABASE_URL")
    if not value:
        if main_demo:
            raise ValueError("StoryRun-lite main demo database is not configured")
        return None
    safe_url, database_name = goal_database_url(value, main_demo=main_demo)
    if main_demo:
        if any(
            os.environ.get(name)
            for name in (
                "PGHOST",
                "PGHOSTADDR",
                "PGPORT",
                "PGDATABASE",
                "PGSERVICE",
                "PGSERVICEFILE",
                "PGOPTIONS",
            )
        ):
            raise ValueError("StoryRun-lite main demo rejects PostgreSQL target overrides")
        main_value = os.environ.get("SKETCH2LIFE_DATABASE_URL")
        if not main_value:
            raise ValueError("Main backend database is not explicitly configured")
        try:
            goal_database_url(main_value, main_demo=True)
            main_url = make_url(main_value)
            story_url = make_url(safe_url)
            if (main_url.get_backend_name(), main_url.host, main_url.port, main_url.database) != (
                story_url.get_backend_name(),
                story_url.host,
                story_url.port,
                story_url.database,
            ):
                raise ValueError
        except Exception:
            raise ValueError("Main backend and StoryRun-lite database targets differ") from None
    engine = create_engine(safe_url, pool_pre_ping=True, hide_parameters=True)
    try:
        verify_goal_database_owner(engine, database_name, main_demo=main_demo)
        quarantine_root = Path(
            os.environ.get(
                "STORYRUN_LITE_QUARANTINE_ROOT",
                str(Path(tempfile.gettempdir()) / "sketch2life-storyrun-lite"),
            )
        )
        quarantine = QuarantineStore(quarantine_root)
        repository = SqlStoryRunLiteRepository(engine=engine, quarantine=quarantine)
        scanner_host = os.environ.get("STORYRUN_LITE_CLAMAV_HOST")
        if scanner_host not in _LOOPBACK_HOSTS:
            scanner_host = None
        try:
            scanner_port = int(os.environ.get("STORYRUN_LITE_CLAMAV_PORT", "3310"))
        except ValueError:
            scanner_port = 0
        scanner = ClamAvScanner(host=scanner_host, port=scanner_port)
        normalizer = WindowsJobObjectImageNormalizer(temporary_root=quarantine_root / "workers")
        vision = _configured_vision(engine, repository)
        story_generator = _configured_story_generator()
        service = StoryRunLiteService(
            repository=repository,
            scanner=scanner,
            normalizer=normalizer,
            vision=vision,
            story_generator=story_generator,
            story_references=repository,
            asset_admission=repository,
            actor_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
            actor_scope_ref="synthetic-parent-local-v1",
        )
        return StoryRunLiteRuntime(engine, repository, service, vision)
    except Exception:
        engine.dispose()
        raise


@asynccontextmanager
async def runtime_lifespan(app: Any, *, main_demo: bool = False) -> AsyncIterator[None]:
    runtime = build_runtime(main_demo=main_demo)
    if runtime is None:
        app.state.story_run_lite_service = None
        yield
        return
    locked = False
    try:
        runtime.repository.acquire_singleton_lock()
        locked = True
        runtime.repository.recover_after_restart()
        if isinstance(runtime.vision, (PhotoVisionBridge, ModalFunctionPhotoVisionBridge)):
            runtime.vision.reconcile_completed_results()
        app.state.story_run_lite_service = runtime.service
        app.state.story_run_lite_runtime = runtime
        yield
    finally:
        try:
            if locked:
                runtime.repository.release_singleton_lock()
        finally:
            runtime.engine.dispose()


__all__ = [
    "StoryRunLiteRuntime",
    "build_runtime",
    "goal_database_url",
    "runtime_lifespan",
    "verify_goal_database_owner",
]
