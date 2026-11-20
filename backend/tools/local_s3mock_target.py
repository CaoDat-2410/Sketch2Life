"""Target guard for local S3Mock runs of the upload pipeline (T-2z, TD-29).

Pure functions, no network at import. They extend the FR-C-08 storage allow-list
(``tools.run_be1_lifecycle_consumer.check_storage_target``) instead of adding a naming scheme:

* the endpoint must equal ``FRC08_ALLOWED_ENDPOINT`` exactly, be ``http`` on a loopback host with an
  explicit port, and never use port 5432, 5433 or 9000;
* the bucket must equal ``FRC08_ALLOWED_BUCKET``, match ``^[a-z0-9][a-z0-9-]{2,62}$`` and contain
  both ``frc08`` and the task tag;
* both S3 keys must be set and no ambient ``AWS_*`` variable may exist, so boto3 can never fall back
  to its default credential chain.

``ensure_task_bucket`` touches only the named bucket (``head_bucket``, then ``create_bucket`` on a
missing bucket). It never lists buckets and never deletes anything.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

from tools.run_be1_lifecycle_consumer import REQUIRED_MARKER, TargetRefused, check_storage_target

FORBIDDEN_S3_PORTS = frozenset({5432, 5433, 9000})
_BUCKET_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{2,62}$")
_TASK_TAG = re.compile(r"^[a-z0-9][a-z0-9-]{0,20}$")
_MISSING_BUCKET_CODES = frozenset({"404", "NoSuchBucket", "NotFound"})
_ACCEPTED_CREATE_CODES = frozenset({"BucketAlreadyOwnedByYou", "BucketAlreadyExists"})


def check_s3mock_target(
    endpoint: str, bucket: str, *, task_tag: str, environ: Mapping[str, str]
) -> None:
    """Raise ``TargetRefused`` unless endpoint and bucket are the allowed local S3Mock target."""

    if not _TASK_TAG.fullmatch(task_tag):
        raise TargetRefused("STORAGE_TASK_TAG_INVALID")
    check_storage_target(endpoint, bucket, environ)
    parts = urlsplit(endpoint)
    try:
        port = parts.port
    except ValueError:
        raise TargetRefused("STORAGE_PORT_INVALID") from None
    if port is None or port in FORBIDDEN_S3_PORTS:
        raise TargetRefused("STORAGE_PORT_REFUSED")
    if parts.scheme != "http":
        raise TargetRefused("STORAGE_ENDPOINT_REFUSED")
    if (
        not _BUCKET_NAME.fullmatch(bucket)
        or REQUIRED_MARKER not in bucket
        or task_tag not in bucket
    ):
        raise TargetRefused("STORAGE_BUCKET_REFUSED")


def check_s3_credentials(
    access_key: str | None, secret_key: str | None, environ: Mapping[str, str]
) -> None:
    """Both keys are required and the ambient AWS environment must be empty (no default chain)."""

    if not access_key or not secret_key:
        raise TargetRefused("STORAGE_CREDENTIALS_MISSING")
    if any(name.upper().startswith("AWS_") for name in environ):
        raise TargetRefused("STORAGE_AMBIENT_CREDENTIALS_REFUSED")


def _error_code(error: Exception) -> str:
    response = getattr(error, "response", None)
    if isinstance(response, dict):
        return str(response.get("Error", {}).get("Code", ""))
    return ""


def ensure_task_bucket(client: Any, bucket: str) -> bool:
    """Create the named bucket when it is missing; return True when it was created.

    Any answer other than "missing" to ``head_bucket`` (for example 403) is re-raised and nothing is
    created. A race that reports the bucket as already owned or existing is accepted.
    """

    try:
        client.head_bucket(Bucket=bucket)
        return False
    except Exception as error:
        if _error_code(error) not in _MISSING_BUCKET_CODES:
            raise
    try:
        client.create_bucket(Bucket=bucket)
    except Exception as error:
        if _error_code(error) in _ACCEPTED_CREATE_CODES:
            return False
        raise
    return True


__all__ = [
    "FORBIDDEN_S3_PORTS",
    "TargetRefused",
    "check_s3_credentials",
    "check_s3mock_target",
    "ensure_task_bucket",
]
