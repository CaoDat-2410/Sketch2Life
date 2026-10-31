"""Generate typed runtime OpenAPI metadata from the FEAT-063 contract catalog."""

from __future__ import annotations

import argparse
import hashlib
import pprint
import re
from pathlib import Path

METHOD_PATH = re.compile(r"`(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)`\s+`([^`]+)`")
HANDLER = re.compile(r"`([^`]+)`\s*$")
RESPONSE_ENTRY = re.compile(r"`(?P<status>\d{3})`\s*(?P<rest>.*?)(?=;\s*`\d{3}`|$)")
RESPONSE_MEDIA = re.compile(
    r":\s*(?P<media>[A-Za-z0-9.+_-]+/[A-Za-z0-9.+_-]+):\s*"
    r"(?P<schema>[A-Za-z][A-Za-z0-9_]*(?:\[[^]]+\])?)"
)
PATH_CONVERTER = re.compile(r":(?:str|int|float|path)}")

TAG_DESCRIPTIONS = {
    "BE1 — Organizations & Classes": "Organization membership, class setup, profiles, assignments, and consents.",
    "BE1 — Sessions & Devices": "Classroom session lifecycle, device joins, rosters, and learning-stage controls.",
    "BE1 — Collaborative Canvas": "Canvas operations, checkpoints, reconnect, and restore workflows.",
    "BE1 — Records & Gallery": "Observations, data requests, portfolio, and classroom gallery records.",
    "BE1 — Session Artifacts": "Upload and retrieve files attached to classroom sessions.",
    "Demo — Capture & Understanding": "Local image/audio capture, preferences, and content-understanding flows.",
    "Demo — Guided Session Workflow": "Local guided learning session and preparation workflows.",
    "Demo — Renderer Assets": "Local renderer source, masks, packages, and Pixi assets.",
    "Demo — Story & Video": "Local story-video and whiteboard-video workflows.",
    "Teacher — Lesson Authoring": "Lesson creation, editing, source documents, versions, and teacher-owned grants.",
    "Teacher & School Manager — Lesson Library": "Staff operations available to teachers and school managers.",
    "School Manager — Sharing & Parent Groups": "School-manager grant decisions, sharing controls, and parent-group administration.",
    "Parent — Invitations & Lesson Library": "Parent invitations, memberships, lesson discovery, and lesson downloads.",
    "Parent & School Manager — Group Membership": "Parent-group membership revocation available to the parent or school manager.",
    "Platform Admin — Moderation": "Platform-level lesson moderation.",
    "Lesson Library — Upload Session Owner": "Continue or manage an upload session as its authenticated owner.",
    "Local Dev — Storage Examples": "Local-only object-storage examples; unavailable outside the enabled local profile.",
    "System — Health": "Service health and readiness endpoints.",
}

_BE1_TAG_BY_HANDLER = {
    "be1_registry.py": "BE1 — Organizations & Classes",
    "be1_sessions.py": "BE1 — Sessions & Devices",
    "be1_canvas.py": "BE1 — Collaborative Canvas",
    "be1_records.py": "BE1 — Records & Gallery",
    "be1_artifacts.py": "BE1 — Session Artifacts",
    "be1_runtime.py": "System — Health",
    "health.py": "System — Health",
}

_TEACHER_LESSON_HANDLERS = {
    "create_lesson",
    "update_lesson",
    "create_upload_session",
    "get_source_document",
    "get_document_revision",
    "create_lesson_version",
    "create_access_grant",
}
_SHARED_STAFF_LESSON_HANDLERS = {
    "list_lessons",
    "get_lesson",
    "archive_lesson",
    "revoke_access_grant",
}
_SCHOOL_MANAGER_HANDLERS = {
    "list_access_grants",
    "decide_access_grant",
    "create_parent_group",
    "list_parent_groups",
    "invite_parent_to_group",
}
_PARENT_HANDLERS = {
    "list_parent_group_invitations",
    "accept_parent_group_invitation",
    "list_lesson_invitations",
    "accept_lesson_invitation",
    "decline_lesson_invitation",
    "list_parent_lessons",
    "get_parent_lesson",
    "download_parent_lesson",
}
_UPLOAD_OWNER_HANDLERS = {
    "get_upload_session",
    "abort_upload_session",
    "upload_part",
    "complete_upload",
}


def _tag_for_operation(entry: dict[str, object]) -> str:
    surface = str(entry["surface"])
    handler_file, handler_name = str(entry["handler"]).split("::", maxsplit=1)
    path = str(entry["path"])
    if surface == "BE1 / classroom":
        try:
            return _BE1_TAG_BY_HANDLER[handler_file]
        except KeyError as error:
            raise ValueError(
                f"No BE1 navigation tag is defined for {handler_file!r}"
            ) from error
    if surface == "Demo / local flow":
        if path.startswith("/v1/renderer/"):
            return "Demo — Renderer Assets"
        if handler_file in {"images.py", "child_preferences.py"}:
            return "Demo — Capture & Understanding"
        if handler_file in {
            "story_video.py",
            "whiteboard_storyboard.py",
            "whiteboard_video.py",
        }:
            return "Demo — Story & Video"
        if handler_file in {"sessions.py", "supervised_flow.py"}:
            return "Demo — Guided Session Workflow"
        raise ValueError(
            f"No Demo navigation tag is defined for {handler_file!r}::{handler_name}"
        )
    if surface == "Lesson Library":
        if handler_name in _TEACHER_LESSON_HANDLERS:
            return "Teacher — Lesson Authoring"
        if handler_name in _SHARED_STAFF_LESSON_HANDLERS:
            return "Teacher & School Manager — Lesson Library"
        if handler_name in _SCHOOL_MANAGER_HANDLERS:
            return "School Manager — Sharing & Parent Groups"
        if handler_name in _PARENT_HANDLERS:
            return "Parent — Invitations & Lesson Library"
        if handler_name == "revoke_parent_group_membership":
            return "Parent & School Manager — Group Membership"
        if handler_name == "moderate_lesson":
            return "Platform Admin — Moderation"
        if handler_name in _UPLOAD_OWNER_HANDLERS:
            return "Lesson Library — Upload Session Owner"
        raise ValueError(f"No Lesson Library role tag is defined for {handler_name!r}")
    if surface == "Local storage example":
        return "Local Dev — Storage Examples"
    raise ValueError(f"Unsupported mounted surface {surface!r}")


def _canonical_path(path: str) -> str:
    return PATH_CONVERTER.sub("}", path)


def _response_entries(success: str, errors: str) -> list[dict[str, str]]:
    combined = "; ".join(value.strip() for value in (success, errors) if value.strip())
    entries: list[dict[str, str]] = []
    for match in RESPONSE_ENTRY.finditer(combined):
        rest = match.group("rest").strip()
        media = RESPONSE_MEDIA.search(rest)
        if media is not None:
            description = rest[: media.start()].rstrip(" :")
            media_type = media.group("media")
            schema_name = media.group("schema")
        elif rest.endswith(": no body"):
            description = rest[: -len(": no body")].rstrip(" :")
            media_type = ""
            schema_name = ""
        else:
            raise ValueError(
                f"Unsupported response contract for HTTP {match.group('status')}: {rest}"
            )
        entries.append(
            {
                "status": match.group("status"),
                "description": description,
                "media_type": media_type,
                "schema_name": schema_name,
            }
        )
    if not entries:
        raise ValueError("Route row is missing success/error response declarations")
    if len({entry["status"] for entry in entries}) != len(entries):
        raise ValueError("Route row contains duplicate response status codes")
    return entries


def _parse_catalog(source: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    mounted: list[dict[str, str]] = []
    unmounted: list[dict[str, str]] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = line.split("|")
        if len(cells) < 10:
            raise ValueError(f"Malformed route row: {line[:120]}")
        method_path = METHOD_PATH.search(cells[3])
        if method_path is None:
            raise ValueError(f"Missing method/path in route row: {cells[1]}")

        surface = cells[2].split(";", maxsplit=1)[0].strip()
        handler = HANDLER.search(cells[8])
        if handler is None:
            raise ValueError(f"Missing source handler in route row: {cells[1]}")
        entry = {
            "method": method_path.group(1).lower(),
            "path": _canonical_path(method_path.group(2)),
            "purpose": cells[4].strip(),
            "request_inputs": cells[5].strip(),
            "surface": surface,
            "handler": handler.group(1),
            "authentication": cells[8].rsplit(";", maxsplit=1)[0].strip(),
            "verification": cells[9].strip(),
            "responses": _response_entries(cells[6], cells[7]),
        }
        if "not mounted" in cells[2].lower():
            unmounted.append(entry)
            continue
        entry["tag"] = _tag_for_operation(entry)
        mounted.append(entry)

    all_keys = [(entry["method"], entry["path"]) for entry in (*mounted, *unmounted)]
    if len(all_keys) != 135:
        raise ValueError(f"Expected 135 Rev37 route rows; found {len(all_keys)}")
    if len(set(all_keys)) != len(all_keys):
        raise ValueError(
            "Rev37 contains duplicate method/path operations after normalization"
        )
    if len(mounted) != 124 or len(unmounted) != 11:
        raise ValueError(
            f"Expected 124 mounted and 11 unmounted rows; found {len(mounted)} and {len(unmounted)}"
        )
    return mounted, unmounted


def _format_module(
    source: Path, mounted: list[dict[str, str]], unmounted: list[dict[str, str]]
) -> str:
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    mounted_map = {
        (entry["method"], entry["path"]): {
            "purpose": entry["purpose"],
            "request_inputs": entry["request_inputs"],
            "surface": entry["surface"],
            "tag": entry["tag"],
            "handler": entry["handler"],
            "authentication": entry["authentication"],
            "verification": entry["verification"],
            "responses": tuple(entry["responses"]),
        }
        for entry in mounted
    }
    candidate_rows = tuple(
        {
            "method": entry["method"],
            "path": entry["path"],
            "purpose": entry["purpose"],
            "request_inputs": entry["request_inputs"],
            "surface": entry["surface"],
            "handler": entry["handler"],
            "authentication": entry["authentication"],
            "verification": entry["verification"],
            "responses": tuple(entry["responses"]),
        }
        for entry in unmounted
    )
    mapping_text = pprint.pformat(
        mounted_map, width=100, sort_dicts=False, compact=False
    )
    candidate_text = pprint.pformat(
        candidate_rows, width=100, sort_dicts=False, compact=False
    )
    tag_descriptions_text = pprint.pformat(
        TAG_DESCRIPTIONS, width=100, sort_dicts=False, compact=False
    )
    return f'''"""Generated from the user-supplied FEAT-063 Rev37 API contract catalog.

Regenerate with ``features/FEAT-063-system-architecture-rearchitecture/scripts/
generate_openapi_contract_metadata.py --contract <catalog.md>``.
"""

# ruff: noqa: E501

from typing import Final, TypedDict

CONTRACT_REVISION: Final = "FEAT-063 Rev37"
SOURCE_FILE_NAME: Final = {source.name!r}
SOURCE_SHA256: Final = {source_hash!r}
DECLARED_OPERATION_COUNT: Final = 135
MOUNTED_OPERATION_COUNT: Final = 124
UNMOUNTED_OPERATION_COUNT: Final = 11
TAG_DESCRIPTIONS: Final[dict[str, str]] = {tag_descriptions_text}


class ResponseMetadata(TypedDict):
    status: str
    description: str
    media_type: str
    schema_name: str


class OperationMetadata(TypedDict):
    purpose: str
    request_inputs: str
    surface: str
    tag: str
    handler: str
    authentication: str
    verification: str
    responses: tuple[ResponseMetadata, ...]


class UnmountedOperationMetadata(TypedDict):
    method: str
    path: str
    purpose: str
    request_inputs: str
    surface: str
    handler: str
    authentication: str
    verification: str
    responses: tuple[ResponseMetadata, ...]


MOUNTED_OPERATIONS: Final[dict[tuple[str, str], OperationMetadata]] = {mapping_text}

UNMOUNTED_OPERATIONS: Final[tuple[UnmountedOperationMetadata, ...]] = {candidate_text}
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        required=True,
        type=Path,
        help="FEAT-063 API catalog Markdown file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("backend/src/sketch2life/interfaces/http/openapi_contract.py"),
        help="Generated Python metadata module path",
    )
    args = parser.parse_args()
    mounted, unmounted = _parse_catalog(args.contract)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        _format_module(args.contract, mounted, unmounted),
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Generated {len(mounted)} mounted and {len(unmounted)} unmounted operations "
        f"from SHA-256 {hashlib.sha256(args.contract.read_bytes()).hexdigest().upper()} at {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
