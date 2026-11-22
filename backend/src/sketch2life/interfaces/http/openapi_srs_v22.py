"""FE-facing OpenAPI projection for the owner-selected SRS v2.2 scope."""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from sketch2life.interfaces.http.admin_contract import ADMIN_OPERATIONS

SRS_V22_INCLUDED_OPERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("post", "/v1/parent/profiles"),
        ("get", "/v1/parent/profiles"),
        ("get", "/v1/parent/profiles/{profile_id}"),
        ("patch", "/v1/parent/profiles/{profile_id}"),
        ("delete", "/v1/parent/profiles/{profile_id}"),
        ("post", "/v1/story-runs"),
        # FEAT-081 C3b: the Parent run-history list (projected for the mobile client).
        ("get", "/v1/story-runs"),
        ("get", "/v1/story-runs/{run_id}"),
        ("get", "/v1/story-runs/active/current"),
        ("post", "/v1/story-runs/{run_id}/context-confirmation"),
        ("post", "/v1/story-runs/{run_id}/subject-confirmation"),
        ("post", "/v1/story-runs/{run_id}/script-confirmation"),
        # FEAT-066 T-2b (SRS l.1664): attach the drawing asset to a Parent run.
        ("post", "/v1/story-runs/{run_id}/assets"),
        # FEAT-066 T-2c (SRS l.1665, l.1713): the idea, the transcript read and its confirmation.
        ("post", "/v1/story-runs/{run_id}/idea"),
        ("get", "/v1/story-runs/{run_id}/transcript"),
        ("post", "/v1/story-runs/{run_id}/transcript-confirmation"),
        # FEAT-066 T-2d (SRS l.1668, FR-P-07): one more story revision, at most three rewrites.
        ("post", "/v1/story-runs/{run_id}/story-rewrites"),
        # FEAT-066 goal v4 T-2e-a (SRS l.514, l.1412, l.1667): the Parent main activity.
        ("get", "/v1/activities"),
        ("post", "/v1/story-runs/{run_id}/activity-selection"),
        # FEAT-066 T-1a (SRS l.1670): the Parent video request.
        ("post", "/v1/story-runs/{run_id}/video-generations"),
        # FEAT-066 T-1b (SRS l.1671-1672): the adult's decisions on a ready video.
        ("post", "/v1/story-runs/{run_id}/video-unsuitable"),
        ("post", "/v1/story-runs/{run_id}/complete"),
        # FEAT-066 T-1c (SRS l.1676, l.1691): the playback grant and the header-borne stream.
        ("post", "/v1/story-runs/{run_id}/playback-token"),
        ("get", "/v1/story-runs/{run_id}/playback"),
        # FEAT-066 T-2a (SRS l.1654-1658): generic upload sessions.
        ("post", "/v1/upload-sessions"),
        ("get", "/v1/upload-sessions/{upload_id}"),
        ("put", "/v1/upload-sessions/{upload_id}/parts/{part_no}"),
        ("post", "/v1/upload-sessions/{upload_id}/complete"),
        ("delete", "/v1/upload-sessions/{upload_id}"),
        # FEAT-066 T-3a (SRS l.1652): Teacher lesson occurrences.
        ("post", "/v1/lesson-occurrences"),
        ("get", "/v1/lesson-occurrences"),
        ("get", "/v1/lesson-occurrences/{occurrence_id}"),
        # FEAT-066 T-4b1 (SRS l.341-352, l.1441, AC-56): the Teacher random-child selection.
        ("post", "/v1/lesson-occurrences/{occurrence_id}/child-selections"),
        ("get", "/v1/lesson-occurrences/{occurrence_id}/child-selections/{selection_id}"),
        (
            "post",
            "/v1/lesson-occurrences/{occurrence_id}/child-selections/{selection_id}/confirmation",
        ),
        # FEAT-066 T-5a (SRS l.1661-1662, l.777): the class projection of the sample video.
        ("post", "/v1/lesson-occurrences/{occurrence_id}/projection-confirmation"),
        ("post", "/v1/lesson-occurrences/{occurrence_id}/projection-playback-token"),
        # FEAT-066 T-8a (SRS l.1681, l.812): the notification inbox and mark-read.
        ("get", "/v1/notifications"),
        ("post", "/v1/notifications/{inbox_item_id}/read"),
        ("post", "/v1/notifications/read-all"),
        ("get", "/api/be1/v1/organizations/{organization_id}"),
        ("get", "/api/be1/v1/organizations/{organization_id}/me"),
        ("get", "/api/be1/v1/billing/video-quota/payment-settings"),
        ("get", "/api/be1/v1/billing/video-quota/products"),
        ("get", "/api/be1/v1/billing/video-quota"),
        ("get", "/api/be1/v1/billing/video-quota/invoices"),
        ("post", "/api/be1/v1/billing/video-quota/checkout"),
        ("get", "/api/be1/v1/organizations/{organization_id}/video-quota"),
        ("get", "/api/be1/v1/organizations/{organization_id}/video-quota/products"),
        ("get", "/api/be1/v1/organizations/{organization_id}/video-quota/payment-settings"),
        ("get", "/api/be1/v1/organizations/{organization_id}/video-quota/teachers"),
        ("get", "/api/be1/v1/organizations/{organization_id}/video-quota/invoices"),
        (
            "post",
            "/api/be1/v1/organizations/{organization_id}/video-quota/invoices/{invoice_id}/reconcile",
        ),
        ("post", "/api/be1/v1/organizations/{organization_id}/video-quota/checkout"),
        ("get", "/api/be1/v1/organizations/{organization_id}/video-quota/allocations"),
        ("post", "/api/be1/v1/organizations/{organization_id}/video-quota/allocations"),
        ("post", "/api/be1/v1/organizations/{organization_id}/video-quota/allocations/reclaim"),
        ("get", "/api/be1/v1/organizations/{organization_id}/video-quota/me"),
        ("post", "/api/be1/v1/classes/{class_id}/assignments"),
        # FEAT-066 T-7b (SRS l.1709): School Manager class archive and manual suspend.
        ("post", "/api/be1/v1/classes/{class_id}/suspend"),
        ("post", "/api/be1/v1/classes/{class_id}/archive"),
        # FEAT-066 T-7d (SRS l.544, l.1651): the Teacher enrollment move between two classes.
        ("post", "/api/be1/v1/classes/{class_id}/profiles/{child_id}/move"),
        ("get", "/api/be1/v1/organizations/{organization_id}/classes"),
        ("post", "/api/be1/v1/organizations/{organization_id}/classes"),
        (
            "get",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
        ),
        (
            "post",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
        ),
        (
            "get",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents",
        ),
        (
            "post",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents",
        ),
        (
            "post",
            "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke",
        ),
        (
            "post",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons",
        ),
        (
            "patch",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}",
        ),
        (
            "post",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions",
        ),
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}",
        ),
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/source-documents/{source_document_id}/revisions/{revision_id}",
        ),
        (
            "post",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions",
        ),
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons",
        ),
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}",
        ),
        (
            "delete",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}",
        ),
        ("get", "/api/lesson-library/v1/upload-sessions/{upload_session_id}"),
        ("delete", "/api/lesson-library/v1/upload-sessions/{upload_session_id}"),
        (
            "put",
            "/api/lesson-library/v1/upload-sessions/{upload_session_id}/parts/{part_number}",
        ),
        (
            "post",
            "/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete",
        ),
    }
)

SRS_V22_OPERATION_TAGS: dict[tuple[str, str], str] = {
    key: "Organization & Class Management"
    for key in SRS_V22_INCLUDED_OPERATIONS
    if key[1].startswith("/api/be1/v1/")
}
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Video Quota & Billing"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if "/video-quota" in key[1]
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Parent Profiles"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/v1/parent/profiles")
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Parent StoryRuns"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/v1/story-runs")
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Parent StoryRuns"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/v1/activities")
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Upload Sessions"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/v1/upload-sessions")
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Lesson Occurrences"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/v1/lesson-occurrences")
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Notifications"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/v1/notifications")
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Teacher — Lesson Preparation"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/api/lesson-library/v1/organizations/")
        and key[0] in {"post", "patch", "get"}
        and any(
            part in key[1]
            for part in (
                "/lessons",
                "/source-documents/",
                "/versions",
                "/upload-sessions",
            )
        )
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons",
        ): "Teacher & School Manager — Lesson Library",
        (
            "get",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}",
        ): "Teacher & School Manager — Lesson Library",
        (
            "delete",
            "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}",
        ): "Teacher & School Manager — Lesson Library",
    }
)
SRS_V22_OPERATION_TAGS.update(
    {
        key: "Lesson Document Upload"
        for key in SRS_V22_INCLUDED_OPERATIONS
        if key[1].startswith("/api/lesson-library/v1/upload-sessions/")
    }
)

SRS_V22_TAGS: list[dict[str, str]] = [
    {
        "name": "Organization & Class Management",
        "description": "Manage organization assignments, classes, profiles, and consent.",
    },
    {
        "name": "Teacher — Lesson Preparation",
        "description": "Create and review lessons and source documents.",
    },
    {
        "name": "Teacher & School Manager — Lesson Library",
        "description": "Browse and archive organization lessons.",
    },
    {
        "name": "Lesson Document Upload",
        "description": "Upload source documents and track upload sessions.",
    },
    {
        "name": "Parent Profiles",
        "description": "Parent profiles: create, list, read, revise, request deletion.",
    },
    {
        "name": "Parent StoryRuns",
        "description": "Proposed Parent StoryRun create, read, and confirmation slice.",
    },
    {
        "name": "Upload Sessions",
        "description": "Resumable uploads for Parent artwork and Teacher documents.",
    },
    {
        "name": "Lesson Occurrences",
        "description": "Teacher lesson occurrences: create, read and list per class.",
    },
    {
        "name": "Notifications",
        "description": "Own notification inbox: cursor page and mark-read.",
    },
    {
        "name": "Video Quota & Billing",
        "description": "Scoped Parent/School quota summaries, checkout, invoices, and Teacher allocations. Real checkout availability is controlled by server configuration.",
    },
]

SRS_V22_OPENAPI_DESCRIPTION = "\n\n".join(
    (
        "Implemented FE APIs cover Parent profiles, a proposed Parent StoryRun slice, "
        "organization/class management, consent, Teacher lesson preparation, and scoped video quota commerce.",
        "Authentication and role/resource access are checked per operation.",
        "Parent activity catalog, Teacher occurrence, Sketch Deck, sample video, jobs/playback, "
        "quota/payment, and notification push endpoints are unavailable.",
        "Proposed Parent confirmations and draft SRS status remain subject to approval.",
    )
)


def project_srs_v22_openapi(runtime_spec: dict[str, Any]) -> dict[str, Any]:
    """Return only the explicit SRS v2.2-related implemented operations."""
    spec = deepcopy(runtime_spec)
    published: dict[str, dict[str, Any]] = {}
    for path, path_item in spec.get("paths", {}).items():
        retained: dict[str, Any] = {}
        for method, operation in path_item.items():
            key = (method.lower(), path)
            if key not in SRS_V22_INCLUDED_OPERATIONS and key not in ADMIN_OPERATIONS:
                continue
            operation["tags"] = ["Admin" if key in ADMIN_OPERATIONS else SRS_V22_OPERATION_TAGS[key]]
            retained[method] = operation
        if retained:
            published[path] = retained
    spec["paths"] = published
    spec["info"]["title"] = "Sketch2Life FE API"
    spec["info"]["description"] = SRS_V22_OPENAPI_DESCRIPTION
    spec["tags"] = deepcopy(SRS_V22_TAGS)
    spec["tags"].append({"name": "Admin", "description": "Administration, identity and school-scoped feedback."})
    schemas = spec.get("components", {}).get("schemas", {})
    if isinstance(schemas, dict) and "Be1Error" in schemas:
        schemas["ApiError"] = schemas.pop("Be1Error")
    spec = publicize_openapi_terms(spec)
    _prune_unused_schemas(spec)
    _prune_unused_security_schemes(spec)
    return spec


def publicize_openapi_terms(value: Any) -> Any:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                value[key] = child.replace(
                    "#/components/schemas/Be1Error",
                    "#/components/schemas/ApiError",
                )
            else:
                value[key] = publicize_openapi_terms(child)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            value[index] = publicize_openapi_terms(child)
    elif isinstance(value, str):
        return value.replace("Be1Error", "ApiError").replace("BE1", "API")
    return value


def _component_refs(value: Any, component_type: str) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        prefix = f"#/components/{component_type}/"
        if isinstance(ref, str) and ref.startswith(prefix):
            refs.add(ref[len(prefix) :])
        for child in value.values():
            refs.update(_component_refs(child, component_type))
    elif isinstance(value, list):
        for child in value:
            refs.update(_component_refs(child, component_type))
    return refs


def _prune_unused_schemas(spec: dict[str, Any]) -> None:
    schemas = spec.get("components", {}).get("schemas")
    if not isinstance(schemas, dict):
        return
    retained = _component_refs(spec.get("paths", {}), "schemas")
    pending = list(retained)
    while pending:
        name = pending.pop()
        schema = schemas.get(name)
        if not isinstance(schema, dict):
            continue
        for dependency in _component_refs(schema, "schemas") - retained:
            retained.add(dependency)
            pending.append(dependency)
    spec["components"]["schemas"] = {
        name: schema for name, schema in schemas.items() if name in retained
    }


def _prune_unused_security_schemes(spec: dict[str, Any]) -> None:
    schemes = spec.get("components", {}).get("securitySchemes")
    if not isinstance(schemes, dict):
        return
    names: set[str] = set()
    root_security = spec.get("security", [])
    if isinstance(root_security, list):
        for requirement in root_security:
            if isinstance(requirement, dict):
                names.update(requirement)
    for operation in _operations(spec):
        security = operation.get("security", [])
        if isinstance(security, list):
            for requirement in security:
                if isinstance(requirement, dict):
                    names.update(requirement)
    spec["components"]["securitySchemes"] = {
        name: scheme for name, scheme in schemes.items() if name in names
    }


def _operations(spec: dict[str, Any]):
    for path_item in spec.get("paths", {}).values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
            } and isinstance(operation, dict):
                yield operation
