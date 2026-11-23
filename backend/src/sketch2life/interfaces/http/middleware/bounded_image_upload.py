"""Hard request-body caps for FEAT-018 image and narration uploads and the FEAT-066 JSON routes."""

from __future__ import annotations

import contextlib
import json
import re
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from sketch2life.interfaces.http.error_envelope import build_error_body

_MAX_MULTIPART_BODY_BYTES = 20_100_000
_UPLOAD_PATH_MARKER = "/media/image"
_AUDIO_UPLOAD_PATH_MARKER = "/media/audio"
_MAX_AUDIO_MULTIPART_BODY_BYTES = 20_100_000
_STORAGE_EXAMPLE_PATH_MARKER = "/api/dev/v1/storage-examples/lesson-source-documents"
_DEFAULT_STORAGE_EXAMPLE_BODY_BYTES = 10 * 1024 * 1024 + 64 * 1024
_LESSON_LIBRARY_PART_PATH_MARKER = "/api/lesson-library/v1/upload-sessions/"
_MAX_LESSON_LIBRARY_PART_BYTES = 4 * 1024 * 1024
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")

# FEAT-066 T-3c (plan review R1 F-01): the Teacher's text edit carries up to 2 MiB of UTF-8 text in
# a JSON string. JSON escaping inflates a character up to 6 bytes (a control character becomes a
# six-byte u00XX escape), so a valid 2 MiB text is at most 12 MiB on the wire; with the small
# envelope the body cap is 13 MiB. The guard runs before FastAPI reads, parses or validates the
# body and before any authorisation or database access.
MAX_REVISION_EDIT_BODY_BYTES = 13 * 1024 * 1024
_REVISION_EDIT_PATH = re.compile(r"^/v1/lesson-occurrences/[^/]+/documents/[^/]+/revisions/?$")

# FEAT-066 T-3d (T-3c review debt P3-4): the plan routes join the same guard through one table of
# bounded JSON routes. A plan revision is at most 12 objectives of 1,000 characters, a direction and
# notes of 2,000, and 24 activities of up to 4,160 characters plus ids: about 120,000 characters,
# which is at most 6 bytes each once JSON-escaped, so 1 MiB is a safe cap. A confirm carries at most
# 24 checklist entries of 64 items (about 150 KB), so 256 KiB is the cap.
MAX_PLAN_CREATE_BODY_BYTES = 1024 * 1024
MAX_PLAN_CONFIRM_BODY_BYTES = 256 * 1024
_PLAN_CREATE_PATH = re.compile(r"^/v1/lesson-occurrences/[^/]+/plan-revisions/?$")
_PLAN_CONFIRM_PATH = re.compile(r"^/v1/lesson-occurrences/[^/]+/plan-revisions/[^/]+/confirm/?$")

# (method, anchored path, limit in bytes, safe message): every entry is bounded by Content-Length
# and by the streamed byte count before FastAPI reads, parses or validates the body.
_BOUNDED_JSON_ROUTES: tuple[tuple[str, re.Pattern[str], int, str], ...] = (
    (
        "POST",
        _REVISION_EDIT_PATH,
        MAX_REVISION_EDIT_BODY_BYTES,
        "The text edit exceeds the request size limit.",
    ),
    (
        "POST",
        _PLAN_CREATE_PATH,
        MAX_PLAN_CREATE_BODY_BYTES,
        "The plan revision exceeds the request size limit.",
    ),
    (
        "POST",
        _PLAN_CONFIRM_PATH,
        MAX_PLAN_CONFIRM_BODY_BYTES,
        "The plan confirmation exceeds the request size limit.",
    ),
)


class _RequestBodyTooLarge(Exception):
    pass


class BoundedImageUploadMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        max_body_bytes: int = _MAX_MULTIPART_BODY_BYTES,
        max_storage_example_body_bytes: int = _DEFAULT_STORAGE_EXAMPLE_BODY_BYTES,
    ) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.max_storage_example_body_bytes = max_storage_example_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = str(scope.get("path", ""))
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        method = scope.get("method")
        if method == "POST" and _UPLOAD_PATH_MARKER in path:
            body_limit = self.max_body_bytes
            error_message = "Image upload exceeded the 20 MB source-plus-derivative limit."
        elif method == "POST" and _AUDIO_UPLOAD_PATH_MARKER in path:
            body_limit = _MAX_AUDIO_MULTIPART_BODY_BYTES
            error_message = "Narration upload exceeded the demo request size limit."
        elif method == "POST" and _STORAGE_EXAMPLE_PATH_MARKER in path:
            body_limit = self.max_storage_example_body_bytes
            error_message = "Lesson source upload exceeded the configured request size limit."
        elif (
            method == "PUT"
            and _LESSON_LIBRARY_PART_PATH_MARKER in path
            and "/parts/" in path
        ):
            body_limit = _MAX_LESSON_LIBRARY_PART_BYTES
            error_message = "Lesson upload part exceeds the 4 MiB request limit."
        else:
            bounded = next(
                (
                    (limit, message)
                    for route_method, pattern, limit, message in _BOUNDED_JSON_ROUTES
                    if method == route_method and pattern.match(path)
                ),
                None,
            )
            if bounded is None:
                await self.app(scope, receive, send)
                return
            await self._call_bounded_json(scope, receive, send, *bounded)
            return

        content_length = next(
            (value for key, value in scope.get("headers", ()) if key.lower() == b"content-length"),
            None,
        )
        if content_length is not None:
            try:
                if int(content_length) > body_limit:
                    await _send_too_large(send, error_message, scope=scope)
                    return
            except ValueError:
                await _send_too_large(send, error_message, scope=scope)
                return

        received = 0

        async def bounded_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > body_limit:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, bounded_receive, send)
        except _RequestBodyTooLarge:
            await _send_too_large(send, error_message, scope=scope)

    async def _call_bounded_json(
        self, scope: Scope, receive: Receive, send: Send, limit: int, message: str
    ) -> None:
        """Bound a JSON route by ``Content-Length`` and by the streamed byte count.

        FastAPI turns an exception raised while it reads the body into its own 400, so the
        streamed case records the breach, swallows whatever the application then answers and sends
        the 413 envelope itself.
        """
        content_length = next(
            (value for key, value in scope.get("headers", ()) if key.lower() == b"content-length"),
            None,
        )
        if content_length is not None:
            try:
                declared = int(content_length)
            except ValueError:
                declared = limit + 1
            if declared > limit:
                await _send_too_large(send, message, scope=scope)
                return

        received = 0
        exceeded = False
        started = False

        async def bounded_receive() -> Message:
            nonlocal received, exceeded
            incoming = await receive()
            if incoming["type"] == "http.request":
                received += len(incoming.get("body", b""))
                if received > limit:
                    exceeded = True
                    raise _RequestBodyTooLarge
            return incoming

        async def guarded_send(outgoing: Message) -> None:
            nonlocal started
            if exceeded:
                return
            if outgoing["type"] == "http.response.start":
                started = True
            await send(outgoing)

        with contextlib.suppress(_RequestBodyTooLarge):
            await self.app(scope, bounded_receive, guarded_send)
        if exceeded and not started:
            await _send_too_large(send, message, scope=scope)


async def _send_too_large(send: Send, safe_message: str, *, scope: Scope) -> None:
    path = str(scope.get("path", ""))
    if _is_demo_media_upload(path):
        body, request_id = _mobile_workflow_upload_failure(scope, safe_message)
        response_headers = [
            (b"content-type", b"application/json"),
            (b"x-request-id", request_id.encode("ascii")),
        ]
    elif path.startswith(("/api/lesson-library/v1/", "/v1/lesson-occurrences/")):
        # CONV-1 §3.2 item 5: the Lesson Library 413 uses the shared envelope and carries an
        # X-Request-ID; FEAT-066 C4 gives it the SRS §9.8 code LESSON_FILE_TOO_LARGE. The T-3c text
        # edit is a JSON request, not a file, so its 413 is the generic MEDIA_TOO_LARGE.
        request_id = _supplied_request_id(scope) or str(uuid4())
        too_large_code = (
            "MEDIA_TOO_LARGE"
            if path.startswith("/v1/lesson-occurrences/")
            else "LESSON_FILE_TOO_LARGE"
        )
        body = json.dumps(
            build_error_body(status=413, code=too_large_code, request_id=request_id),
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        response_headers = [
            (b"content-type", b"application/json"),
            (b"x-request-id", request_id.encode("ascii")),
        ]
    else:
        body = json.dumps(
            {
                "code": "REQUEST_TOO_LARGE",
                "message": safe_message,
                "request_id": "request-body-limit",
            },
            separators=(",", ":"),
        ).encode("utf-8")
        response_headers = [(b"content-type", b"application/json")]
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": response_headers,
        }
    )
    await send({"type": "http.response.body", "body": body})


def _supplied_request_id(scope: Scope) -> str | None:
    for name, value in scope.get("headers", ()):
        if name.lower() == b"x-request-id":
            try:
                candidate = value.decode("ascii")
            except UnicodeDecodeError:
                return None
            return candidate if _SAFE_ID.fullmatch(candidate) else None
    return None


def _is_demo_media_upload(path: str) -> bool:
    parts = path.strip("/").split("/")
    return (
        len(parts) == 5
        and parts[0] == "v1"
        and parts[1] == "sessions"
        and parts[2] != ""
        and parts[3] == "media"
        and parts[4] in {"image", "audio"}
    )


def _mobile_workflow_upload_failure(scope: Scope, safe_message: str) -> tuple[bytes, str]:
    headers = {
        name.lower(): value
        for name, value in scope.get("headers", ())
        if name.lower() in {b"x-request-id", b"x-expected-session-version"}
    }
    supplied_request_id = headers.get(b"x-request-id", b"")
    try:
        request_id = supplied_request_id.decode("ascii")
    except UnicodeDecodeError:
        request_id = ""
    if not _SAFE_ID.fullmatch(request_id):
        request_id = "request-body-limit"

    path_parts = str(scope.get("path", "")).strip("/").split("/")
    session_id = path_parts[2] if len(path_parts) >= 5 and path_parts[1] == "sessions" else ""
    if not _SAFE_ID.fullmatch(session_id):
        session_id = "unknown-session"

    raw_version = headers.get(b"x-expected-session-version", b"")
    try:
        version_text = raw_version.decode("ascii")
        if version_text.isdecimal() and len(version_text) <= 20:
            expected_version = int(version_text)
        else:
            expected_version = 0
    except (UnicodeDecodeError, ValueError):
        expected_version = 0
    expected_version = min(expected_version, 2**31 - 1)

    body = json.dumps(
        {
            "contract_name": "MobileWorkflowResultV1",
            "contract_version": "1.0",
            "status": "FAILED",
            "request_id": request_id,
            "session_id": session_id,
            "expected_session_version": expected_version,
            "observed_session_version": expected_version,
            "provenance": {
                "contract_name": "WorkflowResultProvenanceV1",
                "contract_version": "1.0",
                "producer": "APPLICATION",
                "component": "bounded-image-upload-middleware",
                "component_version": "1.0",
                "source_contracts": ["MobileWorkflowResultV1"],
            },
            "failure": {
                "contract_name": "WorkflowFailureV1",
                "contract_version": "1.0",
                "domain": "MEDIA",
                "code": "UPLOAD_TOO_LARGE",
                "retryable": False,
                "safe_message": safe_message[:240],
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return body, request_id


__all__ = [
    "MAX_PLAN_CONFIRM_BODY_BYTES",
    "MAX_PLAN_CREATE_BODY_BYTES",
    "MAX_REVISION_EDIT_BODY_BYTES",
    "BoundedImageUploadMiddleware",
]
