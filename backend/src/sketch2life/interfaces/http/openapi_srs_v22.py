"""FE-facing OpenAPI projection for the owner-selected SRS v2.2 scope."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SRS_V22_INCLUDED_OPERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("post", "/v1/parent/profiles"),
        ("get", "/v1/parent/profiles/{profile_id}"),
        ("patch", "/v1/parent/profiles/{profile_id}"),
        ("post", "/v1/story-runs"),
        ("get", "/v1/story-runs/{run_id}"),
        ("get", "/v1/story-runs/active/current"),
        ("post", "/v1/story-runs/{run_id}/context-confirmation"),
        ("post", "/v1/story-runs/{run_id}/subject-confirmation"),
        ("post", "/v1/story-runs/{run_id}/script-confirmation"),
        ("get", "/api/be1/v1/organizations/{organization_id}"),
        ("get", "/api/be1/v1/organizations/{organization_id}/me"),
        ("post", "/api/be1/v1/classes/{class_id}/assignments"),
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
        "description": "Create, read, and revise synthetic Parent-owned profiles.",
    },
    {
        "name": "Parent StoryRuns",
        "description": "Proposed Parent StoryRun create, read, and confirmation slice.",
    },
]

SRS_V22_OPENAPI_DESCRIPTION = "\n\n".join(
    (
        "Implemented FE APIs include accepted Parent profiles and a proposed Parent StoryRun "
        "slice alongside organization, class, consent, and Teacher lesson preparation.",
        "Bearer authentication and role/resource access are checked per operation.",
        "Not available yet: Parent activity catalog; Teacher occurrence, Sketch Deck, "
        "sample video; job/playback; quota/payment; notifications.",
        "Parent context, subject, and script confirmation operation details remain proposals.",
        "This projection documents current backend paths and does not indicate final SRS approval.",
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
            if key not in SRS_V22_INCLUDED_OPERATIONS:
                continue
            operation["tags"] = [SRS_V22_OPERATION_TAGS[key]]
            retained[method] = operation
        if retained:
            published[path] = retained
    spec["paths"] = published
    spec["info"]["title"] = "Sketch2Life FE API"
    spec["info"]["description"] = SRS_V22_OPENAPI_DESCRIPTION
    spec["tags"] = deepcopy(SRS_V22_TAGS)
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
