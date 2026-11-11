"""HTTP router groups for classroom runtime and local/demo capabilities."""

from fastapi import FastAPI

from sketch2life.interfaces.http.routers.auth_registration import (
    router as auth_registration_router,
)
from sketch2life.interfaces.http.routers.be1_runtime import router as be1_runtime_router
from sketch2life.interfaces.http.routers.parent_ai import router as parent_ai_router
from sketch2life.interfaces.http.routers.parent_profiles import router as parent_profiles_router
from sketch2life.interfaces.http.routers.parent_story_runs import router as parent_story_runs_router
from sketch2life.interfaces.http.routers.platform_admin_accounts import (
    router as platform_admin_accounts_router,
)
from sketch2life.interfaces.http.routers.teacher_ai import router as teacher_ai_router
from sketch2life.interfaces.http.routers.child_preferences import (
    router as child_preferences_router,
)
from sketch2life.interfaces.http.routers.health import router as health_router
from sketch2life.interfaces.http.routers.images import router as images_router
from sketch2life.interfaces.http.routers.lesson_library import router as lesson_library_router
from sketch2life.interfaces.http.routers.parent_profiles import router as parent_profiles_router
from sketch2life.interfaces.http.routers.pilot_assistance import router as pilot_assistance_router
from sketch2life.interfaces.http.routers.sessions import router as sessions_router
from sketch2life.interfaces.http.routers.story_video import router as story_video_router
from sketch2life.interfaces.http.routers.supervised_flow import renderer_source_router
from sketch2life.interfaces.http.routers.supervised_flow import (
    router as supervised_flow_router,
)
from sketch2life.interfaces.http.routers.whiteboard_storyboard import (
    router as whiteboard_storyboard_router,
)
from sketch2life.interfaces.http.routers.whiteboard_video import router as whiteboard_video_router


def mount_classroom_routers(
    application: FastAPI, *, include_pilot_assistance: bool = True
) -> None:
    """Mount durable identity, classroom health, and BE1 runtime route groups."""
    application.include_router(auth_registration_router)
    application.include_router(platform_admin_accounts_router)
    application.include_router(health_router)
    application.include_router(be1_runtime_router)
    application.include_router(parent_profiles_router)
    if include_pilot_assistance:
        application.include_router(pilot_assistance_router)


def mount_demo_routers(application: FastAPI) -> None:
    """Mount the existing local/ephemeral demo route group in its stable order."""
    application.include_router(child_preferences_router)
    application.include_router(sessions_router)
    application.include_router(images_router)
    application.include_router(supervised_flow_router)
    application.include_router(renderer_source_router)
    application.include_router(whiteboard_video_router)
    application.include_router(whiteboard_storyboard_router)
    application.include_router(story_video_router)


def mount_all_routers(
    application: FastAPI, *, include_parent_story_runs: bool = True
) -> None:
    """Preserve the original compatibility app's router registration order."""
    settings = application.state.be1_runtime.settings
    include_pilot_assistance = settings.env == "test" or (
        settings.env == "local" and settings.synthetic_pilot_enabled is True
    )
    mount_classroom_routers(
        application,
        include_pilot_assistance=include_pilot_assistance,
    )
    mount_demo_routers(application)
    application.include_router(lesson_library_router)
    application.include_router(parent_ai_router)
    application.include_router(parent_profiles_router)
    if include_parent_story_runs:
        application.include_router(parent_story_runs_router)
    application.include_router(teacher_ai_router)
