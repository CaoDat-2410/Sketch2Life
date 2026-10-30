"""Hard request-body caps for FEAT-018 image and narration uploads."""

from __future__ import annotations

import json
import re

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_MAX_MULTIPART_BODY_BYTES = 20_100_000
_UPLOAD_PATH_MARKER = "/media/image"
_AUDIO_UPLOAD_PATH_MARKER = "/media/audio"
_MAX_AUDIO_MULTIPART_BODY_BYTES = 20_100_000
_STORAGE_EXAMPLE_PATH_MARKER = "/api/dev/v1/storage-examples/lesson-source-documents"
_DEFAULT_STORAGE_EXAMPLE_BODY_BYTES = 10 * 1024 * 1024 + 64 * 1024
_LESSON_LIBRARY_PART_PATH_MARKER = "/api/lesson-library/v1/upload-sessions/"
_MAX_LESSON_LIBRARY_PART_BYTES = 4 * 1024 * 1024
_SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")


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
            await self.app(scope, receive, send)
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


async def _send_too_large(send: Send, safe_message: str, *, scope: Scope) -> None:
    path = str(scope.get("path", ""))
    if _is_demo_media_upload(path):
        body, request_id = _mobile_workflow_upload_failure(scope, safe_message)
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
        expected_version = int(version_text) if version_text.isdecimal() and len(version_text) <= 20 else 0
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


__all__ = ["BoundedImageUploadMiddleware"]
