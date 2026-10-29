import json
from pathlib import Path

from sketch2life.interfaces.http.app import (
    create_app,
    create_classroom_app,
    create_demo_app,
)


def test_compatibility_app_preserves_baseline_route_surface() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    baseline_path = (
        repository_root
        / "features"
        / "FEAT-059-code-structure-cleanup"
        / "evidence"
        / "metrics"
        / "baseline_routes.json"
    )
    expected_entries = json.loads(baseline_path.read_text(encoding="utf-8"))
    expected = {
        entry["path"]: sorted(entry["methods"])
        for entry in expected_entries
    }
    openapi = create_app().openapi()
    actual = {
        path: sorted(method.upper() for method in operations)
        for path, operations in openapi["paths"].items()
    }
    # Frozen method/path pairs from the FEAT-063 Rev32 API purpose catalog.
    library = "/api/lesson-library/v1"
    organization = f"{library}/organizations/{{organization_id}}"
    lesson = f"{organization}/lessons/{{lesson_id}}"
    upload = f"{library}/upload-sessions/{{upload_session_id}}"
    lesson_library_methods = {
        f"{library}/me/lesson-invitations": ["GET"],
        f"{library}/me/lesson-invitations/{{access_grant_id}}/accept": ["POST"],
        f"{library}/me/lesson-invitations/{{access_grant_id}}/decline": ["POST"],
        f"{library}/me/lessons": ["GET"],
        f"{library}/me/lessons/{{lesson_id}}": ["GET"],
        f"{library}/me/lessons/{{lesson_id}}/download": ["GET"],
        f"{library}/me/parent-group-invitations": ["GET"],
        f"{library}/me/parent-group-invitations/{{membership_id}}/accept": ["POST"],
        f"{organization}/access-grants": ["GET"],
        f"{organization}/access-grants/{{access_grant_id}}/decision": ["POST"],
        f"{organization}/lessons": ["GET", "POST"],
        lesson: ["DELETE", "GET", "PATCH"],
        f"{lesson}/access-grants": ["POST"],
        f"{lesson}/access-grants/{{access_grant_id}}": ["DELETE"],
        f"{lesson}/source-documents/{{source_document_id}}": ["GET"],
        f"{lesson}/source-documents/{{source_document_id}}/revisions/{{revision_id}}": ["GET"],
        f"{lesson}/upload-sessions": ["POST"],
        f"{lesson}/versions": ["POST"],
        f"{organization}/parent-groups": ["GET", "POST"],
        f"{organization}/parent-groups/{{parent_group_id}}/invitations": ["POST"],
        f"{organization}/parent-groups/{{parent_group_id}}/members/{{membership_id}}": ["DELETE"],
        f"{library}/platform/lessons/{{lesson_id}}/moderation": ["PATCH"],
        upload: ["DELETE", "GET"],
        f"{upload}/complete": ["POST"],
        f"{upload}/parts/{{part_number}}": ["PUT"],
    }

    # Preserve the full pre-integration route surface while allowing only the
    # reviewed FEAT-060 classroom and FEAT-063 Lesson Library contracts.
    assert expected.items() <= actual.items()
    assert set(actual) - set(expected) == {
        "/api/be1/v1/device-grants/{grant_id}/join-status",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/completion",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster",
        "/api/be1/v1/room-code/join",
    } | set(lesson_library_methods)
    assert {path: actual[path] for path in lesson_library_methods} == lesson_library_methods


def test_compatibility_app_keeps_be1_and_demo_services_on_app_state() -> None:
    application = create_app()

    assert application.state.be1_runtime is not None
    assert application.state.session_service is not None
    assert application.state.live_image_demo_service is not None
    assert application.state.supervised_flow_service is not None


def test_classroom_profile_excludes_process_local_demo_routes() -> None:
    application = create_classroom_app()
    paths = set(application.openapi()["paths"])

    assert "/health" in paths
    assert "/api/be1/v1/health" in paths
    assert "/v1/sessions" not in paths
    assert "/v1/profile/preferences/classify" not in paths
    assert application.state.session_service is None
    assert application.state.live_image_demo_service is None


def test_demo_profile_excludes_durable_classroom_routes() -> None:
    application = create_demo_app()
    paths = set(application.openapi()["paths"])

    assert "/v1/sessions" in paths
    assert "/api/be1/v1/health" not in paths
    assert application.state.session_service is not None
    assert application.state.live_image_demo_service is not None
