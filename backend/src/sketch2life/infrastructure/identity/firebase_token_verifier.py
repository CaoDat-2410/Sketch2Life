"""Firebase Authentication adapter for verified adult bearer tokens."""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import time

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.infrastructure.config.settings import Settings
from sketch2life.infrastructure.identity.firebase_admin_app import (
    FirebaseAdminUnavailable,
    decode_firebase_admin_json,
    get_firebase_admin_app,
)

# Identity Toolkit can issue a fresh token several seconds ahead of the API host clock.
# Keep a bounded tolerance so immediate post-sign-in role resolution does not fail closed.
FIREBASE_AUTH_CLOCK_SKEW_SECONDS = 30
_LOGGER = logging.getLogger(__name__)


def _safe_token_claim_diagnostics(encoded_token: str, project_id: str) -> dict[str, bool]:
    """Compare untrusted JWT claims without logging claim values or token material."""
    diagnostics = {
        "token_structure_valid": False,
        "token_audience_matches_project": False,
        "token_issuer_matches_project": False,
        "token_subject_present": False,
        "token_expiration_in_future": False,
    }
    try:
        segments = encoded_token.split(".")
        if len(segments) != 3 or not segments[1]:
            return diagnostics
        payload_segment = segments[1]
        payload_segment += "=" * (-len(payload_segment) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_segment.encode("ascii")))
    except (UnicodeEncodeError, binascii.Error, json.JSONDecodeError, ValueError):
        return diagnostics
    if not isinstance(payload, dict):
        return diagnostics

    expiration = payload.get("exp")
    diagnostics.update(
        token_structure_valid=True,
        token_audience_matches_project=payload.get("aud") == project_id,
        token_issuer_matches_project=(
            payload.get("iss") == f"https://securetoken.google.com/{project_id}"
        ),
        token_subject_present=isinstance(payload.get("sub"), str)
        and bool(payload.get("sub")),
        token_expiration_in_future=(
            type(expiration) in {int, float} and expiration > time.time()
        ),
    )
    return diagnostics


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
            # Log only typed diagnostics: provider messages can contain token or identity data.
            claim_diagnostics = _safe_token_claim_diagnostics(
                encoded_token, self._settings.firebase_project_id
            )
            _LOGGER.warning(
                "firebase_id_token_verification_rejected error_type=%s error_module=%s "
                "revocation_check_enabled=%s token_structure_valid=%s "
                "token_audience_matches_project=%s token_issuer_matches_project=%s "
                "token_subject_present=%s token_expiration_in_future=%s",
                type(exc).__name__,
                type(exc).__module__,
                self._settings.firebase_check_revoked_tokens,
                claim_diagnostics["token_structure_valid"],
                claim_diagnostics["token_audience_matches_project"],
                claim_diagnostics["token_issuer_matches_project"],
                claim_diagnostics["token_subject_present"],
                claim_diagnostics["token_expiration_in_future"],
            )
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
