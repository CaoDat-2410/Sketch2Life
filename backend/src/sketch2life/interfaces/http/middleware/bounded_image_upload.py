"""Hard request-body cap for the single-image multipart upload route."""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_MAX_MULTIPART_BODY_BYTES = 5_100_000
_UPLOAD_PATH_MARKER = "/media/image"


class _RequestBodyTooLarge(Exception):
    pass


class BoundedImageUploadMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int = _MAX_MULTIPART_BODY_BYTES) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or _UPLOAD_PATH_MARKER not in str(scope.get("path", ""))
        ):
            await self.app(scope, receive, send)
            return

        content_length = next(
            (value for key, value in scope.get("headers", ()) if key.lower() == b"content-length"),
            None,
        )
        if content_length is not None:
            try:
                if int(content_length) > self.max_body_bytes:
                    await _send_too_large(send)
                    return
            except ValueError:
                await _send_too_large(send)
                return

        received = 0

        async def bounded_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    raise _RequestBodyTooLarge
            return message

        try:
            await self.app(scope, bounded_receive, send)
        except _RequestBodyTooLarge:
            await _send_too_large(send)


async def _send_too_large(send: Send) -> None:
    body = json.dumps(
        {
            "status": "FAILED",
            "failure": {
                "domain": "MEDIA",
                "code": "UPLOAD_TOO_LARGE",
                "retryable": False,
                "safe_message": "Image upload exceeded the demo request size limit.",
            },
        },
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
