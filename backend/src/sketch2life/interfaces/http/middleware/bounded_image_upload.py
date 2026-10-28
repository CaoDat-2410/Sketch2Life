"""Hard request-body caps for FEAT-018 image and narration uploads."""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_MAX_MULTIPART_BODY_BYTES = 20_100_000
_UPLOAD_PATH_MARKER = "/media/image"
_AUDIO_UPLOAD_PATH_MARKER = "/media/audio"
_MAX_AUDIO_MULTIPART_BODY_BYTES = 20_100_000
_STORAGE_EXAMPLE_PATH_MARKER = "/api/dev/v1/storage-examples/lesson-source-documents"
_DEFAULT_STORAGE_EXAMPLE_BODY_BYTES = 10 * 1024 * 1024 + 64 * 1024
_LESSON_LIBRARY_PART_PATH_MARKER = "/api/lesson-library/v1/upload-sessions/"
_MAX_LESSON_LIBRARY_PART_BYTES = 4 * 1024 * 1024


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
                    await _send_too_large(send, error_message)
                    return
            except ValueError:
                await _send_too_large(send, error_message)
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
            await _send_too_large(send, error_message)


async def _send_too_large(send: Send, safe_message: str) -> None:
    body = json.dumps(
        {"code": "REQUEST_TOO_LARGE", "message": safe_message, "request_id": "request-body-limit"},
        separators=(",", ":"),
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": body})


__all__ = ["BoundedImageUploadMiddleware"]
