"""Shared Firebase Admin app initialization for Authentication adapters."""

from __future__ import annotations

import base64
import binascii
import json
from threading import Lock
from typing import Any

from sketch2life.infrastructure.config.settings import Settings


class FirebaseAdminUnavailable(RuntimeError):
    """Firebase Admin could not be initialized from the configured server settings."""


_APP_LOCK = Lock()


def decode_firebase_admin_json(encoded: str, project_id: str) -> dict[str, Any]:
    """Decode a Base64 service-account value without logging its contents."""
    try:
        decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
        payload = json.loads(decoded)
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Firebase Admin credential is not valid Base64 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("Firebase Admin credential must be a JSON object")
    if payload.get("project_id") != project_id:
        raise ValueError("Firebase Admin credential project does not match configured project")
    return payload


def get_firebase_admin_app(settings: Settings):
    """Return the single named Firebase Admin app for the configured project."""
    if settings.auth_provider != "firebase" or not settings.firebase_project_id:
        raise FirebaseAdminUnavailable("Firebase Authentication is not configured")
    try:
        from firebase_admin import credentials, get_app, initialize_app
    except ImportError as exc:
        raise FirebaseAdminUnavailable("Firebase Admin SDK is required") from exc

    admin_json_base64 = settings.firebase_admin_json_base64
    encoded = (
        admin_json_base64.get_secret_value().strip()
        if admin_json_base64 and admin_json_base64.get_secret_value().strip()
        else None
    )
    credential_path = (
        str(settings.firebase_credentials_file) if settings.firebase_credentials_file else None
    )

    with _APP_LOCK:
        try:
            return get_app(settings.firebase_project_id)
        except ValueError:
            try:
                if encoded:
                    credential_info = decode_firebase_admin_json(
                        encoded, settings.firebase_project_id
                    )
                    credential = credentials.Certificate(credential_info)
                elif credential_path:
                    credential = credentials.Certificate(credential_path)
                else:
                    credential = credentials.ApplicationDefault()
                return initialize_app(
                    credential,
                    options={"projectId": settings.firebase_project_id},
                    name=settings.firebase_project_id,
                )
            except Exception as exc:
                # Suppress SDK details: they can include credential paths or provider payloads.
                raise FirebaseAdminUnavailable(
                    "Firebase Admin app could not be initialized"
                ) from exc


__all__ = [
    "FirebaseAdminUnavailable",
    "decode_firebase_admin_json",
    "get_firebase_admin_app",
]
