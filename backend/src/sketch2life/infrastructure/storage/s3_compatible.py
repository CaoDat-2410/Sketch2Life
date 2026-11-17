"""Boto3 adapter for MinIO and AWS S3-compatible object storage."""

from __future__ import annotations

from typing import Any, BinaryIO, Mapping, cast

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from sketch2life.application.ports.object_storage import (
    ObjectStorageFailure,
    ObjectStoragePort,
    ReadableObjectBody,
    StoredObject,
)


def build_s3_client(
    *,
    endpoint_url: str | None,
    region_name: str,
    access_key: str | None,
    secret_key: str | None,
) -> Any:
    """Build an S3 client; absent credentials use Boto3's default chain/IAM role."""
    kwargs: dict[str, object] = {
        "region_name": region_name,
        "endpoint_url": endpoint_url or None,
        "config": Config(
            signature_version="s3v4",
            s3={"addressing_style": "path" if endpoint_url else "auto"},
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    }
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key
    return cast(Any, boto3.client("s3", **kwargs))


class Boto3S3CompatibleObjectStorage(ObjectStoragePort):
    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None,
        region_name: str,
        access_key: str | None,
        secret_key: str | None,
    ) -> None:
        self._bucket = bucket
        self._client = build_s3_client(
            endpoint_url=endpoint_url,
            region_name=region_name,
            access_key=access_key,
            secret_key=secret_key,
        )

    def put_object(
        self,
        key: str,
        body: BinaryIO,
        *,
        content_type: str,
        content_length: int,
        metadata: Mapping[str, str],
    ) -> None:
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body,
                ContentLength=content_length,
                ContentType=content_type,
                Metadata=dict(metadata),
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageFailure("Object storage could not save the object") from exc

    def get_object(self, key: str) -> StoredObject | None:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"NoSuchKey", "NoSuchBucket", "404", "NotFound"}:
                return None
            raise ObjectStorageFailure("Object storage could not read the object") from exc
        except BotoCoreError as exc:
            raise ObjectStorageFailure("Object storage could not read the object") from exc

        body = cast(ReadableObjectBody, response["Body"])
        return StoredObject(
            body=body,
            content_length=int(response.get("ContentLength", 0)),
            content_type=str(response.get("ContentType", "application/octet-stream")),
            metadata={str(key): str(value) for key, value in response.get("Metadata", {}).items()},
        )

    def delete_object(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageFailure("Object storage could not delete the object") from exc


__all__ = ["Boto3S3CompatibleObjectStorage", "build_s3_client"]
