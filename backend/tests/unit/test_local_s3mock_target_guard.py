"""T-2z: target guard for local S3Mock runs and the task-bucket helper."""

from __future__ import annotations

from typing import Any

import pytest

from tools.local_s3mock_target import (
    check_s3_credentials,
    check_s3mock_target,
    ensure_task_bucket,
)
from tools.run_be1_lifecycle_consumer import TargetRefused

ENDPOINT = "http://127.0.0.1:59458"
BUCKET = "frc08-v3-t2z-s3mock"
TAG = "v3-t2z"
ALLOWED = {"FRC08_ALLOWED_ENDPOINT": ENDPOINT, "FRC08_ALLOWED_BUCKET": BUCKET}


def _refused(
    endpoint: str, bucket: str, environ: dict[str, str] | None = None, tag: str = TAG
) -> str:
    env = ALLOWED if environ is None else environ
    with pytest.raises(TargetRefused) as caught:
        check_s3mock_target(endpoint, bucket, task_tag=tag, environ=env)
    return caught.value.code


def test_the_expected_target_is_accepted() -> None:
    check_s3mock_target(ENDPOINT, BUCKET, task_tag=TAG, environ=ALLOWED)


@pytest.mark.parametrize(
    ("endpoint", "code"),
    [
        ("http://10.0.0.5:59458", "STORAGE_ENDPOINT_NOT_LOOPBACK"),
        ("http://example.com:59458", "STORAGE_ENDPOINT_NOT_LOOPBACK"),
        ("https://127.0.0.1:59458", "STORAGE_ENDPOINT_REFUSED"),
        ("http://127.0.0.1:59458/bucket", "STORAGE_ENDPOINT_REFUSED"),
        ("http://127.0.0.1:59458?x=1", "STORAGE_ENDPOINT_REFUSED"),
        ("http://user:pw@127.0.0.1:59458", "STORAGE_ENDPOINT_REFUSED"),
        ("http://127.0.0.1", "STORAGE_PORT_REFUSED"),
        ("http://127.0.0.1:5432", "STORAGE_PORT_REFUSED"),
        ("http://127.0.0.1:5433", "STORAGE_PORT_REFUSED"),
        ("http://127.0.0.1:9000", "STORAGE_PORT_REFUSED"),
        ("http://127.0.0.1:99999", "STORAGE_PORT_INVALID"),
    ],
)
def test_bad_endpoints_are_refused(endpoint: str, code: str) -> None:
    # Allow-list the endpoint itself so only the structural rule under test can refuse it.
    environ = {**ALLOWED, "FRC08_ALLOWED_ENDPOINT": endpoint}

    assert _refused(endpoint, BUCKET, environ) == code


def test_an_endpoint_that_is_not_the_allow_listed_one_is_refused() -> None:
    assert _refused("http://127.0.0.1:59459", BUCKET) == "STORAGE_ENDPOINT_NOT_ALLOW_LISTED"
    assert _refused(ENDPOINT, BUCKET, {}) == "STORAGE_ENDPOINT_NOT_ALLOW_LISTED"


@pytest.mark.parametrize(
    "bucket",
    [
        "sketch2life-private",
        "frc08-other-task",
        "v3-t2z-without-marker",
        "FRC08-V3-T2Z",
        "frc08_v3_t2z",
        "-frc08-v3-t2z",
        "fr",
        "frc08-v3-t2z-" + "x" * 60,
        "",
    ],
)
def test_buckets_without_the_marker_the_tag_or_a_valid_name_are_refused(bucket: str) -> None:
    environ = {**ALLOWED, "FRC08_ALLOWED_BUCKET": bucket}

    assert _refused(ENDPOINT, bucket, environ) == "STORAGE_BUCKET_REFUSED"


def test_a_bucket_that_is_not_the_allow_listed_one_is_refused() -> None:
    assert _refused(ENDPOINT, "frc08-v3-t2z-other") == "STORAGE_BUCKET_REFUSED"


@pytest.mark.parametrize("tag", ["", "T2Z", "v3 t2z", "../t2z", "x" * 40])
def test_an_invalid_task_tag_is_refused(tag: str) -> None:
    assert _refused(ENDPOINT, BUCKET, tag=tag) == "STORAGE_TASK_TAG_INVALID"


def test_credentials_need_both_keys_and_no_ambient_aws_environment() -> None:
    check_s3_credentials("access", "secret", {"PATH": "x"})
    for access, secret in [(None, "s"), ("a", None), ("", "s"), ("a", ""), (None, None)]:
        with pytest.raises(TargetRefused) as caught:
            check_s3_credentials(access, secret, {})
        assert caught.value.code == "STORAGE_CREDENTIALS_MISSING"
    for name in ["AWS_ACCESS_KEY_ID", "AWS_PROFILE", "aws_session_token"]:
        with pytest.raises(TargetRefused) as caught:
            check_s3_credentials("a", "s", {name: "x"})
        assert caught.value.code == "STORAGE_AMBIENT_CREDENTIALS_REFUSED"


class _ClientError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.response = {"Error": {"Code": code}}


class _FakeClient:
    """Records calls; ``list_buckets`` and ``delete_bucket`` must never be touched."""

    def __init__(self, head: Exception | None = None, create: Exception | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self._head = head
        self._create = create

    def head_bucket(self, *, Bucket: str) -> dict[str, Any]:  # noqa: N803
        self.calls.append(("head_bucket", Bucket))
        if self._head is not None:
            raise self._head
        return {}

    def create_bucket(self, *, Bucket: str) -> dict[str, Any]:  # noqa: N803
        self.calls.append(("create_bucket", Bucket))
        if self._create is not None:
            raise self._create
        return {}

    def list_buckets(self) -> None:
        raise AssertionError("list_buckets must never be called")

    def delete_bucket(self, **_: object) -> None:
        raise AssertionError("delete_bucket must never be called")


def test_existing_bucket_is_only_probed() -> None:
    client = _FakeClient()

    assert ensure_task_bucket(client, BUCKET) is False
    assert client.calls == [("head_bucket", BUCKET)]


@pytest.mark.parametrize("code", ["404", "NoSuchBucket", "NotFound"])
def test_missing_bucket_is_created_and_only_that_one(code: str) -> None:
    client = _FakeClient(head=_ClientError(code))

    assert ensure_task_bucket(client, BUCKET) is True
    assert client.calls == [("head_bucket", BUCKET), ("create_bucket", BUCKET)]


@pytest.mark.parametrize("code", ["403", "AccessDenied", "500", "Forbidden", ""])
def test_any_other_head_answer_raises_and_creates_nothing(code: str) -> None:
    client = _FakeClient(head=_ClientError(code))

    with pytest.raises(_ClientError):
        ensure_task_bucket(client, BUCKET)
    assert client.calls == [("head_bucket", BUCKET)]


def test_a_non_client_error_on_head_is_not_swallowed() -> None:
    client = _FakeClient(head=ConnectionError("down"))

    with pytest.raises(ConnectionError):
        ensure_task_bucket(client, BUCKET)
    assert client.calls == [("head_bucket", BUCKET)]


@pytest.mark.parametrize("code", ["BucketAlreadyOwnedByYou", "BucketAlreadyExists"])
def test_create_race_answers_are_accepted(code: str) -> None:
    client = _FakeClient(head=_ClientError("404"), create=_ClientError(code))

    assert ensure_task_bucket(client, BUCKET) is False
    assert client.calls == [("head_bucket", BUCKET), ("create_bucket", BUCKET)]


def test_other_create_errors_are_raised() -> None:
    client = _FakeClient(head=_ClientError("404"), create=_ClientError("AccessDenied"))

    with pytest.raises(_ClientError):
        ensure_task_bucket(client, BUCKET)
