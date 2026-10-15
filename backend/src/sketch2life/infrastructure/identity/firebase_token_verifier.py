"""Firebase Authentication adapter for verified adult bearer tokens."""

from __future__ import annotations

import asyncio
from functools import lru_cache
from threading import Lock

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import Settings


class IdentityVerificationUnavailable(RuntimeError):
    """The configured identity provider cannot verify a token safely."""


class FirebaseTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def verify(self, encoded_token: str) -> VerifiedPrincipal:
        return await asyncio.to_thread(self._verify_sync, encoded_token)

    def _verify_sync(self, encoded_token: str) -> VerifiedPrincipal:
        if self._settings.auth_provider != "firebase" or not self._settings.firebase_project_id:
            raise IdentityVerificationUnavailable("Firebase Authentication is not configured")
        try:
            from firebase_admin import auth, credentials, get_app, initialize_app
        except ImportError as exc:
            raise IdentityVerificationUnavailable(
                "Firebase Admin SDK is required for adult token verification"
            ) from exc

        try:
            app = _firebase_app(
                self._settings.firebase_project_id,
                str(self._settings.firebase_credentials_file)
                if self._settings.firebase_credentials_file
                else None,
                credentials,
                get_app,
                initialize_app,
            )
            claims = auth.verify_id_token(
                encoded_token,
                app=app,
                check_revoked=self._settings.firebase_check_revoked_tokens,
            )
        except Exception as exc:
            # Avoid leaking provider errors or token material into an API response.
            raise IdentityVerificationUnavailable("Firebase identity token was rejected") from exc

        subject = claims.get("uid")
        issuer = claims.get("iss")
        expected_issuer = f"https://securetoken.google.com/{self._settings.firebase_project_id}"
        if not isinstance(subject, str) or not subject or issuer != expected_issuer:
            raise IdentityVerificationUnavailable("Firebase identity claims are invalid")
        token_id = claims.get("jti")
        return VerifiedPrincipal(
            subject=subject,
            issuer=issuer,
            roles=frozenset(),
            token_id=token_id if isinstance(token_id, str) else None,
        )


_APP_LOCK = Lock()


@lru_cache(maxsize=4)
def _firebase_app(project_id, credential_path, credentials_module, get_app, initialize_app):
    """Initialize one SDK app per configured project without serializing credentials."""
    with _APP_LOCK:
        try:
            return get_app(project_id)
        except ValueError:
            credential = (
                credentials_module.Certificate(credential_path)
                if credential_path
                else credentials_module.ApplicationDefault()
            )
            return initialize_app(credential, options={"projectId": project_id}, name=project_id)


__all__ = ["FirebaseTokenVerifier", "IdentityVerificationUnavailable"]
