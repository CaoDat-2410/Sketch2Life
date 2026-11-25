from types import SimpleNamespace

import pytest

from sketch2life.application.ports.story_video import (
    QuotaStatus,
    VideoRequestScope,
)
from sketch2life.infrastructure.billing.quota_commerce import QuotaCommerceService
from sketch2life.infrastructure.story_video.billing_quota_admission import (
    BillingVideoQuotaAdmission,
)


class FakeSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


@pytest.mark.parametrize(
    ("scope", "expected_owner_scope"),
    [
        (
            VideoRequestScope("PARENT_ACCOUNT", "parent-account-1"),
            ("PARENT_ACCOUNT", "parent-account-1"),
        ),
        (
            VideoRequestScope("ORGANIZATION", "organization-1"),
            ("ORGANIZATION", "organization-1"),
        ),
    ],
)
def test_adapter_passes_parent_and_teacher_owner_scopes_to_billing(
    monkeypatch: pytest.MonkeyPatch,
    scope: VideoRequestScope,
    expected_owner_scope: tuple[str, str],
) -> None:
    calls: list[dict] = []

    def consume(self, **kwargs):
        calls.append(kwargs)
        return {
            "status": "ACCEPTED",
            "usage_ref": "usage-1",
            "grant_ref": "grant-1",
        }

    monkeypatch.setattr(QuotaCommerceService, "consume_video_quota", consume)
    adapter = BillingVideoQuotaAdmission(FakeSession, SimpleNamespace())  # type: ignore[arg-type]

    result = adapter.admit_video_request(
        scope=scope,
        request_ref="generation-1",
        idempotency_key="key-1",
        fingerprint="fingerprint-1",
        contract_version="video-quota-port-v1",
    )

    assert result.status is QuotaStatus.ACCEPTED
    assert result.usage_ref == "usage-1"
    assert result.grant_ref == "grant-1"
    assert calls == [
        {
            "owner_scope": expected_owner_scope,
            "request_ref": "generation-1",
            "idempotency_key": "key-1",
            "fingerprint": "fingerprint-1",
            "contract_version": "video-quota-port-v1",
        }
    ]


@pytest.mark.parametrize(
    ("billing_status", "port_status"),
    [
        ("QUOTA_EXCEEDED", QuotaStatus.QUOTA_EXCEEDED),
        ("SUBSCRIPTION_RESTRICTED", QuotaStatus.SUBSCRIPTION_RESTRICTED),
        ("IDEMPOTENCY_MISMATCH", QuotaStatus.IDEMPOTENCY_MISMATCH),
        ("UNAVAILABLE", QuotaStatus.UNAVAILABLE),
    ],
)
def test_adapter_maps_each_billing_status_to_one_story_status(
    monkeypatch: pytest.MonkeyPatch,
    billing_status: str,
    port_status: QuotaStatus,
) -> None:
    monkeypatch.setattr(
        QuotaCommerceService,
        "consume_video_quota",
        lambda self, **kwargs: {"status": billing_status},
    )
    adapter = BillingVideoQuotaAdmission(FakeSession, SimpleNamespace())  # type: ignore[arg-type]

    result = adapter.admit_video_request(
        scope=VideoRequestScope("PARENT_ACCOUNT", "parent-account-1"),
        request_ref="generation-1",
        idempotency_key="key-1",
        fingerprint="fingerprint-1",
        contract_version="video-quota-port-v1",
    )

    assert result.status is port_status
    assert result.usage_ref is None
    assert result.grant_ref is None


def test_adapter_fails_closed_on_storage_errors_unknown_status_or_missing_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = BillingVideoQuotaAdmission(FakeSession, SimpleNamespace())  # type: ignore[arg-type]
    request = {
        "scope": VideoRequestScope("ORGANIZATION", "organization-1"),
        "request_ref": "generation-1",
        "idempotency_key": "key-1",
        "fingerprint": "fingerprint-1",
        "contract_version": "video-quota-port-v1",
    }

    monkeypatch.setattr(
        QuotaCommerceService,
        "consume_video_quota",
        lambda self, **kwargs: {"status": "UNKNOWN"},
    )
    assert adapter.admit_video_request(**request).status is QuotaStatus.UNAVAILABLE

    monkeypatch.setattr(
        QuotaCommerceService,
        "consume_video_quota",
        lambda self, **kwargs: {"status": "ACCEPTED", "grant_ref": "grant-1"},
    )
    assert adapter.admit_video_request(**request).status is QuotaStatus.UNAVAILABLE

    def fail(self, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(QuotaCommerceService, "consume_video_quota", fail)
    assert adapter.admit_video_request(**request).status is QuotaStatus.UNAVAILABLE
