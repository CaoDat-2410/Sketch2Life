"""``list_keys`` over ListObjectsV2: all pages, fail closed (port design Draft 6 §5.3, §12)."""

from __future__ import annotations

from typing import Any

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from sketch2life.application.ports.object_storage import ObjectStorageFailure
from sketch2life.infrastructure.storage.s3_compatible import Boto3S3CompatibleObjectStorage

PREFIX = "parent/22222222-2222-4222-8222-222222222222/"


class _Client:
    def __init__(self, pages: list[dict[str, Any]] | None = None, error: Exception | None = None):
        self.pages = list(pages or [])
        self.error = error
        self.requests: list[dict[str, Any]] = []

    def list_objects_v2(self, **request: Any) -> dict[str, Any]:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.pages.pop(0)


def _storage(client: _Client) -> Boto3S3CompatibleObjectStorage:
    storage = Boto3S3CompatibleObjectStorage(
        bucket="frc08-bucket",
        endpoint_url="http://127.0.0.1:9000",
        region_name="us-east-1",
        access_key="throwaway",
        secret_key="throwaway",  # noqa: S106 - synthetic, never a real credential
    )
    storage._client = client  # type: ignore[attr-defined]
    return storage


def _client_error(code: str, status: int) -> ClientError:
    return ClientError(
        {
            "Error": {"Code": code, "Message": PREFIX + "object-key"},
            "ResponseMetadata": {"HTTPStatusCode": status},
        },
        "ListObjectsV2",
    )


def test_every_page_is_read_and_keys_are_sorted() -> None:
    client = _Client(
        [
            {
                "Contents": [{"Key": PREFIX + "b"}],
                "IsTruncated": True,
                "NextContinuationToken": "t1",
            },
            {"Contents": [{"Key": PREFIX + "a"}], "IsTruncated": False},
        ]
    )
    assert _storage(client).list_keys(PREFIX) == (PREFIX + "a", PREFIX + "b")
    assert client.requests[0] == {"Bucket": "frc08-bucket", "Prefix": PREFIX}
    assert client.requests[1]["ContinuationToken"] == "t1"


def test_an_empty_prefix_listing_returns_nothing() -> None:
    assert _storage(_Client([{"IsTruncated": False}])).list_keys(PREFIX) == ()


@pytest.mark.parametrize(
    "error",
    (
        _client_error("AccessDenied", 403),
        _client_error("NoSuchBucket", 404),
        _client_error("InternalError", 500),
        _client_error("SlowDown", 503),
        EndpointConnectionError(endpoint_url="http://127.0.0.1:9000"),
    ),
)
def test_storage_errors_fail_closed_without_leaking_a_key(error: Exception) -> None:
    with pytest.raises(ObjectStorageFailure) as failed:
        _storage(_Client(error=error)).list_keys(PREFIX)
    assert "parent/" not in str(failed.value)


@pytest.mark.parametrize(
    "pages",
    (
        [{"Contents": [{"Key": "lesson-library/x"}], "IsTruncated": False}],
        [{"Contents": [{"Key": 7}], "IsTruncated": False}],
        [{"Contents": [], "IsTruncated": True}],
        [{"Contents": [], "IsTruncated": True, "NextContinuationToken": ""}],
    ),
)
def test_an_unexpected_listing_is_never_read_as_absence(pages: list[dict[str, Any]]) -> None:
    with pytest.raises(ObjectStorageFailure):
        _storage(_Client(pages)).list_keys(PREFIX)


def test_an_empty_prefix_is_refused() -> None:
    with pytest.raises(ObjectStorageFailure):
        _storage(_Client([])).list_keys("")


def test_an_unexpected_adapter_error_is_wrapped() -> None:
    with pytest.raises(ObjectStorageFailure):
        _storage(_Client(error=RuntimeError("boom"))).list_keys(PREFIX)
