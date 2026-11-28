from __future__ import annotations

from sketch2life.interfaces.http.app import create_app


def test_additive_display_label_fields_are_published_in_openapi() -> None:
    app = create_app()
    app.openapi()
    document = app.state.runtime_openapi_schema
    schemas = document["components"]["schemas"]

    summary = schemas["LessonFeedbackSummaryV1"]["properties"]
    message = schemas["LessonFeedbackMessageV1"]["properties"]
    thread = schemas["LessonFeedbackThreadV1"]["properties"]
    grant = schemas["LessonAccessGrantV1"]["properties"]
    teacher = schemas["SchoolQuotaTeacherV1"]["properties"]
    allocation = schemas["SchoolQuotaAllocationV1"]["properties"]

    assert {"lesson_title", "version_no"} <= set(summary)
    assert {"author_role", "author_display_name"} <= set(message)
    assert {"lesson_title", "version_no"} <= set(thread)
    assert {"lesson_title", "version_no"} <= set(grant)
    assert {"display_name", "email_masked"} <= set(teacher)
    assert {"display_name", "email_masked"} <= set(allocation)

    assert "lesson_title" not in schemas["LessonFeedbackSummaryV1"]["required"]
    assert "author_display_name" not in schemas["LessonFeedbackMessageV1"]["required"]
    assert "lesson_title" not in schemas["LessonAccessGrantV1"]["required"]

    paths = document["paths"]

    def response_ref(path: str) -> str:
        return paths[path]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]

    for path in (
        "/api/lesson-library/v1/organizations/{organization_id}/feedback",
        "/api/platform-admin/v1/organizations/{organization_id}/feedback",
    ):
        assert response_ref(path) == "#/components/schemas/LessonFeedbackPageV1"
    for path in (
        "/api/lesson-library/v1/organizations/{organization_id}/feedback/{thread_id}",
        "/api/platform-admin/v1/organizations/{organization_id}/feedback/{thread_id}",
    ):
        assert response_ref(path) == "#/components/schemas/LessonFeedbackThreadV1"
    assert response_ref(
        "/api/lesson-library/v1/organizations/{organization_id}/access-grants"
    ) == "#/components/schemas/LessonAccessGrantPageV1"
    quota = "/api/be1/v1/organizations/{organization_id}/video-quota"
    assert response_ref(f"{quota}/teachers") == "#/components/schemas/SchoolQuotaTeacherPageV1"
    assert response_ref(f"{quota}/allocations") == "#/components/schemas/SchoolQuotaAllocationPageV1"

