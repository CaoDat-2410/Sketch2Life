"""Create the private MinIO bucket used by the local Docker Compose example."""

from __future__ import annotations

import time

from botocore.exceptions import BotoCoreError, ClientError
from pydantic import SecretStr

from sketch2life.infrastructure.config.settings import get_settings
from sketch2life.infrastructure.storage.s3_compatible import build_s3_client


def ensure_bucket(*, attempts: int = 60, retry_seconds: float = 1.0) -> None:
    settings = get_settings()
    endpoint = (settings.s3_endpoint or "").rstrip("/")
    if settings.env != "local" or endpoint != "http://minio:9000":
        raise RuntimeError("Local bucket initialization only accepts the Compose MinIO endpoint")
    if not settings.s3_bucket:
        raise RuntimeError("A local object-storage bucket name is required")

    access_key = _secret_value(settings.s3_access_key)
    secret_key = _secret_value(settings.s3_secret_key)
    client = build_s3_client(
        endpoint_url=endpoint,
        region_name=settings.s3_region,
        access_key=access_key,
        secret_key=secret_key,
    )

    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            client.head_bucket(Bucket=settings.s3_bucket)
            return
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchBucket", "NotFound"}:
                try:
                    client.create_bucket(Bucket=settings.s3_bucket)
                    return
                except ClientError as create_error:
                    create_code = str(
                        create_error.response.get("Error", {}).get("Code", "")
                    )
                    if create_code in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                        return
                    raise
            if code not in {"500", "502", "503", "504", "SlowDown"}:
                raise
            last_error = exc
        except BotoCoreError as exc:
            last_error = exc
        time.sleep(retry_seconds)

    raise RuntimeError("MinIO did not become ready for local bucket initialization") from last_error


def _secret_value(secret: SecretStr | None) -> str | None:
    if secret is None:
        return None
    value = secret.get_secret_value()
    return value or None


if __name__ == "__main__":
    ensure_bucket()
