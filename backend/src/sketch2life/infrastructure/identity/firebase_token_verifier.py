"""Firebase Authentication adapter for verified adult bearer tokens."""

from __future__ import annotations

import asyncio

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.identity.firebase_admin_app import (
    FirebaseAdminUnavailable,
    decode_firebase_admin_json,
    get_firebase_admin_app,
)

FIREBASE_AUTH_CLOCK_SKEW_SECONDS = 10


class IdentityVerificationUnavailable(RuntimeError):
    """The configured identity provider cannot verify a token safely."""


class FirebaseTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def verify(self, encoded_token: str) -> VerifiedPrincipal:
        return await asyncio.to_thread(self._verify_sync, encoded_token)

    def _verify_sync(self, encoded_token: str) -> VerifiedPrincipal:
        try:
            from firebase_admin import auth

            app = get_firebase_admin_app(self._settings)
            claims = auth.verify_id_token(
                encoded_token,
                app=app,
                check_revoked=self._settings.firebase_check_revoked_tokens,
                clock_skew_seconds=FIREBASE_AUTH_CLOCK_SKEW_SECONDS,
            )
        except FirebaseAdminUnavailable as exc:
            raise IdentityVerificationUnavailable(str(exc)) from exc
        except ImportError as exc:
            raise IdentityVerificationUnavailable(
                "Firebase Admin SDK is required for adult token verification"
            ) from exc
        except Exception as exc:
            # Avoid leaking provider errors or token material into an API response.
            raise IdentityVerificationUnavailable("Firebase identity token was rejected") from exc

        subject = claims.get("uid")
        issuer = claims.get("iss")
        expected_issuer = f"https://securetoken.google.com/{self._settings.firebase_project_id}"
        if not isinstance(subject, str) or not subject or issuer != expected_issuer:
            raise IdentityVerificationUnavailable("Firebase identity claims are invalid")
        token_id = claims.get("jti")
        email = claims.get("email")
        display_name = claims.get("name")
        return VerifiedPrincipal(
            subject=subject,
            issuer=issuer,
            roles=frozenset(),
            token_id=token_id if isinstance(token_id, str) else None,
            email=email.strip().lower() if isinstance(email, str) and email.strip() else None,
            display_name=(
                display_name.strip()
                if isinstance(display_name, str) and display_name.strip()
                else None
            ),
            email_verified=claims.get("email_verified") is True,
        )


# Kept as an import-compatible name for existing focused config tests.
_decode_firebase_admin_json = decode_firebase_admin_json


__all__ = ["FirebaseTokenVerifier", "IdentityVerificationUnavailable"]
