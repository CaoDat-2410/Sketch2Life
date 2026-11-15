"""FE-facing OpenAPI projection for mounted workflow APIs and legacy BE1 contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SRS_V22_INCLUDED_OPERATIONS: frozenset[tuple[str, str]] = frozenset(
    {
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
]

SRS_V22_OPENAPI_DESCRIPTION = "\n\n".join(
    (
        "Current API operations mounted by this backend build, with request and response "
        "schemas generated from the registered handlers.",
        "Bearer authentication and role/resource access are enforced per operation where "
        "required. This document describes the implemented API surface; it is not the "
        "canonical product SRS.",
        "Video-generation operations are excluded from this non-video workflow contract.",
    )
)

_ACTIVE_WORKFLOW_PREFIXES: tuple[str, ...] = (
    "/api/auth/v1/",
    "/api/parent/v1/",
    "/api/teacher/v1/",
    "/api/billing/v1/",
    "/api/lesson-library/v1/",
    "/api/svg-catalog/v1/",
)
_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})

ACTIVE_WORKFLOW_TAGS: list[dict[str, str]] = [
    {"name": "Authentication", "description": "Resolve and register authenticated accounts."},
    {"name": "Parent — Profiles & Consent", "description": "Manage owned child profiles and data authorization."},
    {"name": "Parent — AI", "description": "Generate optional sketch guides and Parent learning drafts."},
    {"name": "Parent — StoryRuns", "description": "Create, review, resume, and list Parent learning runs."},
    {"name": "Parent — Quota", "description": "Read the Parent's available video quota."},
    {"name": "Teacher — AI", "description": "Generate lesson-plan, sketch-deck, and visual drafts from reviewed Teacher input."},
    {"name": "Lesson Library", "description": "Manage, discover, and share versioned lessons."},
    {"name": "SVG Illustration & Stroke Guides", "description": "Manage provenance-tracked SVG references, progressive drawing guides, educator reviews, and platform curation."},
]


def _workflow_tag(path: str) -> str:
    if path.startswith("/api/auth/v1/"):
        return "Authentication"
    if path.startswith("/api/parent/v1/ai/"):
        return "Parent — AI"
    if "/story-runs" in path:
        return "Parent — StoryRuns"
    if path.startswith("/api/parent/v1/"):
        return "Parent — Profiles & Consent"
    if path.startswith("/api/billing/v1/"):
        return "Parent — Quota"
    if path.startswith("/api/teacher/v1/"):
        return "Teacher — AI"
    if path.startswith("/api/svg-catalog/v1/"):
        return "SVG Illustration & Stroke Guides"
    return "Lesson Library"


def _is_video_generation_operation(path: str, operation: Any) -> bool:
    if path.startswith("/api/billing/v1/") and "quota" in path.casefold():
        return False
    path_text = path.casefold()
    operation_text = " ".join(
        str(operation.get(key, "")) for key in ("summary", "operationId")
    ).casefold()
    return "video" in path_text or any(
        term in operation_text
        for term in ("generate video", "video generation", "story video", "whiteboard video")
    )


def project_srs_v22_openapi(runtime_spec: dict[str, Any]) -> dict[str, Any]:
    """Project active workflow routes plus the existing explicit BE1 contract surface."""
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
    for path, path_item in spec.get("paths", {}).items():
        if not path.startswith(_ACTIVE_WORKFLOW_PREFIXES) or not isinstance(path_item, dict):
            continue
        retained = published.setdefault(path, {})
        for method, operation in path_item.items():
            if method.lower() not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            if _is_video_generation_operation(path, operation):
                continue
            operation["tags"] = [_workflow_tag(path)]
            retained[method] = operation
        if not retained:
            published.pop(path, None)
    spec["paths"] = published
    spec["info"]["title"] = "Sketch2Life FE API"
    spec["info"]["description"] = SRS_V22_OPENAPI_DESCRIPTION
    spec["tags"] = deepcopy(SRS_V22_TAGS + ACTIVE_WORKFLOW_TAGS)
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
