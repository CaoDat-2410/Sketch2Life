"""Firebase Authentication adapter for verified adult bearer tokens."""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import os
import time

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.identity.firebase_admin_app import (
    FirebaseAdminUnavailable,
    decode_firebase_admin_json,
    get_firebase_admin_app,
)

FIREBASE_AUTH_CLOCK_SKEW_SECONDS = 10
_LOGGER = logging.getLogger(__name__)


def _safe_token_claim_diagnostics(encoded_token: str, project_id: str) -> dict[str, bool]:
    """Inspect untrusted token claims while returning boolean diagnostics only."""
    diagnostics = {
        "token_payload_decodable": False,
        "token_audience_matches_project": False,
        "token_issuer_matches_project": False,
        "token_subject_present": False,
        "token_expiration_in_future": False,
    }
    if not isinstance(encoded_token, str):
        return diagnostics
    try:
        segments = encoded_token.split(".")
        if len(segments) != 3 or not segments[1]:
            return diagnostics
        payload_segment = segments[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        payload_bytes = base64.b64decode(
            payload_segment.encode("ascii"), altchars=b"-_", validate=True
        )
        payload = json.loads(payload_bytes)
    except (binascii.Error, UnicodeEncodeError, ValueError):
        return diagnostics
    if not isinstance(payload, dict):
        return diagnostics

    expiration = payload.get("exp")
    diagnostics.update(
        token_payload_decodable=True,
        token_audience_matches_project=payload.get("aud") == project_id,
        token_issuer_matches_project=(
            payload.get("iss") == f"https://securetoken.google.com/{project_id}"
        ),
        token_subject_present=isinstance(payload.get("sub"), str) and bool(payload.get("sub")),
        token_expiration_in_future=(
            isinstance(expiration, int | float)
            and not isinstance(expiration, bool)
            and expiration > time.time()
        ),
    )
    return diagnostics


def _log_verification_failure(
    error: Exception,
    encoded_token: str,
    project_id: str,
    *,
    stage: str = "verify",
) -> None:
    diagnostics = _safe_token_claim_diagnostics(encoded_token, project_id)
    _LOGGER.warning(
        "firebase_token_verification_failed stage=%s error_type=%s error_module=%s "
        "token_payload_decodable=%s token_audience_matches_project=%s "
        "token_issuer_matches_project=%s token_subject_present=%s "
        "token_expiration_in_future=%s",
        stage,
        type(error).__name__,
        type(error).__module__,
        diagnostics["token_payload_decodable"],
        diagnostics["token_audience_matches_project"],
        diagnostics["token_issuer_matches_project"],
        diagnostics["token_subject_present"],
        diagnostics["token_expiration_in_future"],
    )


class IdentityVerificationUnavailable(RuntimeError):
    """The configured identity provider cannot verify a token safely."""


class FirebaseTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        if os.environ.get("FIREBASE_AUTH_EMULATOR_HOST") and getattr(settings, "env", None) not in {
            "local",
            "test",
        }:
            raise ValueError(
                "FIREBASE_AUTH_EMULATOR_HOST is permitted only when "
                "SKETCH2LIFE_ENV is local or test"
            )
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
            _log_verification_failure(exc, encoded_token, self._settings.firebase_project_id)
            raise IdentityVerificationUnavailable(str(exc)) from exc
        except ImportError as exc:
            _log_verification_failure(exc, encoded_token, self._settings.firebase_project_id)
            raise IdentityVerificationUnavailable(
                "Firebase Admin SDK is required for adult token verification"
            ) from exc
        except Exception as exc:
            # Avoid leaking provider errors or token material into an API response.
            _log_verification_failure(exc, encoded_token, self._settings.firebase_project_id)
            raise IdentityVerificationUnavailable("Firebase identity token was rejected") from exc

        subject = claims.get("uid")
        issuer = claims.get("iss")
        expected_issuer = f"https://securetoken.google.com/{self._settings.firebase_project_id}"
        if not isinstance(subject, str) or not subject or issuer != expected_issuer:
            error = IdentityVerificationUnavailable("Firebase identity claims are invalid")
            _log_verification_failure(
                error,
                encoded_token,
                self._settings.firebase_project_id,
                stage="claim_validation",
            )
            raise error
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
