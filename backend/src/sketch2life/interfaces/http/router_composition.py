"""HTTP router groups for classroom runtime and local/demo capabilities."""

from fastapi import APIRouter, FastAPI

from sketch2life.infrastructure.lesson_occurrences.upload_target import (
    OccurrenceUploadTargetResolver,
)
from sketch2life.infrastructure.uploads.purposes import OCCURRENCE_DOCUMENT
from sketch2life.interfaces.http.routers.auth_registration import (
    router as auth_registration_router,
)
from sketch2life.interfaces.http.routers.be1_runtime import router as be1_runtime_router
from sketch2life.interfaces.http.routers.child_preferences import (
    router as child_preferences_router,
)
from sketch2life.interfaces.http.routers.health import router as health_router
from sketch2life.interfaces.http.routers.images import router as images_router
from sketch2life.interfaces.http.routers.jobs import router as jobs_router
from sketch2life.interfaces.http.routers.lesson_library import router as lesson_library_router
from sketch2life.interfaces.http.routers.lesson_occurrences import (
    router as lesson_occurrences_router,
)
from sketch2life.interfaces.http.routers.notifications import router as notifications_router
from sketch2life.interfaces.http.routers.parent_ai import router as parent_ai_router
from sketch2life.interfaces.http.routers.parent_profiles import router as parent_profiles_router
from sketch2life.interfaces.http.routers.parent_story_activities import (
    activities_router as parent_activities_router,
)
from sketch2life.interfaces.http.routers.parent_story_activities import (
    router as parent_story_activities_router,
)
from sketch2life.interfaces.http.routers.parent_story_inputs import (
    router as parent_story_inputs_router,
)
from sketch2life.interfaces.http.routers.parent_story_runs import router as parent_story_runs_router
from sketch2life.interfaces.http.routers.pilot_assistance import router as pilot_assistance_router
from sketch2life.interfaces.http.routers.platform_admin_accounts import (
    router as platform_admin_accounts_router,
)
from sketch2life.interfaces.http.routers.platform_admin import router as platform_admin_router
from sketch2life.interfaces.http.routers.password_recovery import router as password_recovery_router
from sketch2life.interfaces.http.routers.lesson_feedback import router as lesson_feedback_router
from sketch2life.interfaces.http.routers.sessions import router as sessions_router
from sketch2life.interfaces.http.routers.story_run_video import router as story_run_video_router
from sketch2life.interfaces.http.routers.story_video import router as story_video_router
from sketch2life.interfaces.http.routers.supervised_flow import renderer_source_router
from sketch2life.interfaces.http.routers.supervised_flow import (
    router as supervised_flow_router,
)
from sketch2life.interfaces.http.routers.teacher_ai import router as teacher_ai_router
from sketch2life.interfaces.http.routers.upload_sessions import router as upload_sessions_router
from sketch2life.interfaces.http.routers.whiteboard_storyboard import (
    router as whiteboard_storyboard_router,
)
from sketch2life.interfaces.http.routers.whiteboard_video import router as whiteboard_video_router


def story_demo_replaced_routers() -> tuple[APIRouter, ...]:
    """Real routers that stay unmounted while the StoryRun-lite main demo is on.

    The demo router owns `/v1/story-runs*` and `/v1/upload-sessions*`; the startup guard
    (`story_demo_guard`) reads these route tables. A task that mounts another real router
    on one of those paths only when the demo is off adds it here. T-2a: the generic upload
    sessions (`/v1/upload-sessions*`) are mounted only while the demo is off. T-2b: the Parent run
    input routes (`POST /v1/story-runs/{run_id}/assets`, later T-2c and T-2d routes) mount and
    unmount together with the Parent StoryRun router. T-1a: the video request route
    (`POST /v1/story-runs/{run_id}/video-generations`) does the same.
    """
    return (
        parent_story_runs_router,
        parent_story_inputs_router,
        parent_story_activities_router,
        story_run_video_router,
        upload_sessions_router,
    )


def mount_classroom_routers(
    application: FastAPI, *, include_pilot_assistance: bool = True
) -> None:
    """Mount durable identity, classroom health, and BE1 runtime route groups."""
    application.include_router(auth_registration_router)
    application.include_router(platform_admin_accounts_router)
    application.include_router(platform_admin_router)
    application.include_router(password_recovery_router)
    application.include_router(health_router)
    application.include_router(be1_runtime_router)
    application.include_router(parent_profiles_router)
    # FEAT-066 T0.4: mounted here once; mount_all_routers reaches it through this function.
    application.include_router(jobs_router)
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
    application: FastAPI,
    *,
    include_parent_story_runs: bool = True,
    include_upload_sessions: bool = True,
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
    application.include_router(lesson_feedback_router)
    application.include_router(parent_ai_router)
    if include_parent_story_runs:
        application.include_router(parent_story_runs_router)
        application.include_router(parent_story_inputs_router)
        # FEAT-066 goal v4 T-2e-a: the main-activity routes (selection under /v1/story-runs, so it
        # mounts and unmounts with the Parent router; the list has no demo twin).
        application.include_router(parent_story_activities_router)
        application.include_router(parent_activities_router)
        application.include_router(story_run_video_router)
    # FEAT-066 T-2a: the demo router answers the same literal paths with another contract, so
    # the generic upload sessions are mounted only while the demo is off (T-2a-DEC-1).
    if include_upload_sessions:
        application.include_router(upload_sessions_router)
    application.include_router(teacher_ai_router)
    # FEAT-066 T-3a: /v1/lesson-occurrences has no demo collision, so it mounts unconditionally.
    application.include_router(lesson_occurrences_router)
    # FEAT-066 T-8a: /v1/notifications (the inbox) has no demo collision: mounted unconditionally.
    application.include_router(notifications_router)
    # T-2a left OCCURRENCE_DOCUMENT without a resolver (it answers 404); T-3a registers it. A
    # factory a caller put on app.state first (a test double) is kept.
    factories = dict(getattr(application.state, "upload_target_resolver_factories", None) or {})
    factories.setdefault(OCCURRENCE_DOCUMENT, OccurrenceUploadTargetResolver)
    application.state.upload_target_resolver_factories = factories
