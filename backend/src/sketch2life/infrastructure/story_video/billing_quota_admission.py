"""Billing-owned video quota admission for the Story video port."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping

from sqlalchemy.orm import Session

from sketch2life.application.ports.story_video import (
    QuotaResult,
    QuotaStatus,
    VideoRequestScope,
)
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.config.settings import Settings

_LOG = logging.getLogger(__name__)


class BillingVideoQuotaAdmission:
    """Call Billing in its own session and translate its receipt to the Story port contract."""

    def __init__(self, session_factory: Callable[[], Session], settings: Settings) -> None:
        self._session_factory = session_factory
        self._settings = settings

    def admit_video_request(
        self,
        *,
        scope: VideoRequestScope,
        request_ref: str,
        idempotency_key: str,
        fingerprint: str,
        contract_version: str,
    ) -> QuotaResult:
        try:
            with self._session_factory() as session:
                commerce = QuotaCommerceService(
                    session,
                    actor="story-video-admission",
                    settings=self._settings,
                )
                result = commerce.consume_video_quota(
                    owner_scope=(scope.kind, scope.ref),
                    request_ref=request_ref,
                    idempotency_key=idempotency_key,
                    fingerprint=fingerprint,
                    contract_version=contract_version,
                )
        except Exception:
            _LOG.warning("story_video_billing_quota_unavailable")
            return QuotaResult(QuotaStatus.UNAVAILABLE)

        status_value = result.get("status") if isinstance(result, Mapping) else None
        if not isinstance(status_value, str):
            return QuotaResult(QuotaStatus.UNAVAILABLE)
        try:
            status = QuotaStatus(status_value)
        except ValueError:
            return QuotaResult(QuotaStatus.UNAVAILABLE)

        usage_ref = result.get("usage_ref")
        grant_ref = result.get("grant_ref")
        if status is QuotaStatus.ACCEPTED and not isinstance(usage_ref, str):
            return QuotaResult(QuotaStatus.UNAVAILABLE)
        return QuotaResult(
            status=status,
            usage_ref=usage_ref if isinstance(usage_ref, str) else None,
            grant_ref=grant_ref if isinstance(grant_ref, str) else None,
        )


__all__ = ["BillingVideoQuotaAdmission"]
