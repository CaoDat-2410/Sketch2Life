"""T-2z: local S3Mock storage and the allowlist scanner against PostgreSQL (TD-29).

Coordinator-run only. Each half skips (NOT_RUN, never PASS) when its variables are unset and
fails with ``REFUSED code=...`` when a target is set but outside the allow-list:

* PostgreSQL: ``BE1_TEST_DATABASE_URL`` is checked with ``check_database_url`` (loopback, port not
  5432/5433, name contains ``frc08`` and ``frc08_v3_t2z``, equal to ``FRC08_ALLOWED_DATABASE`` and
  ``FRC08_ALLOWED_PORT``).
* S3Mock: ``T2Z_S3_ENDPOINT``, ``T2Z_S3_BUCKET``, ``T2Z_S3_ACCESS_KEY``, ``T2Z_S3_SECRET_KEY`` are
  checked with ``check_s3mock_target`` (endpoint equal to ``FRC08_ALLOWED_ENDPOINT``, bucket
  equal to ``FRC08_ALLOWED_BUCKET`` and containing ``frc08`` and ``v3-t2z``), both keys must be
  set and no ambient ``AWS_*`` variable may exist. The guard runs before any client is built.

Only synthetic bytes are used. The test creates only its own keys under a unique per-run prefix
and has no teardown; the only delete is the in-body ``delete_object`` call that is the behaviour
under test. It never lists buckets and never deletes a bucket or a database.
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator
from dataclasses import dataclass
from io import BytesIO
from typing import Any
from uuid import uuid4

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    scanner_identity_sha256,
)
from sketch2life.infrastructure.documents.local_test_adapters import LocalTestAllowlistScanner
from sketch2life.infrastructure.storage.s3_compatible import (
    Boto3S3CompatibleObjectStorage,
    build_s3_client,
)
from tests.synthetic_upload_fixtures import synthetic_pdf, synthetic_png
from tools.local_s3mock_target import (
    check_s3_credentials,
    check_s3mock_target,
    ensure_task_bucket,
)
from tools.run_be1_lifecycle_consumer import TargetRefused, check_database_url

TASK_TAG = "v3-t2z"
DATABASE_MARKER = "frc08_v3_t2z"
PNG = synthetic_png()
PDF = synthetic_pdf()

_S3_VARIABLES = ("T2Z_S3_ENDPOINT", "T2Z_S3_BUCKET", "T2Z_S3_ACCESS_KEY", "T2Z_S3_SECRET_KEY")


def _refuse(code: str) -> None:
    pytest.fail(f"REFUSED code={code}", pytrace=False)


@dataclass
class S3Target:
    storage: Boto3S3CompatibleObjectStorage


@pytest.fixture(scope="module")
def s3_target() -> Iterator[S3Target]:
    if not all(os.environ.get(name) for name in _S3_VARIABLES):
        pytest.skip("NOT_RUN: set T2Z_S3_ENDPOINT, T2Z_S3_BUCKET and both T2Z_S3 key variables")
    endpoint = os.environ["T2Z_S3_ENDPOINT"]
    bucket = os.environ["T2Z_S3_BUCKET"]
    access_key = os.environ["T2Z_S3_ACCESS_KEY"]
    secret_key = os.environ["T2Z_S3_SECRET_KEY"]
    try:
        check_s3mock_target(endpoint, bucket, task_tag=TASK_TAG, environ=os.environ)
        check_s3_credentials(access_key, secret_key, os.environ)
    except TargetRefused as refused:
        _refuse(refused.code)
    client = build_s3_client(
        endpoint_url=endpoint, region_name="us-east-1", access_key=access_key, secret_key=secret_key
    )
    ensure_task_bucket(client, bucket)
    storage = Boto3S3CompatibleObjectStorage(
        bucket=bucket,
        endpoint_url=endpoint,
        region_name="us-east-1",
        access_key=access_key,
        secret_key=secret_key,
    )
    # No teardown: keys sit under a unique per-run prefix and are left in place; the only delete is
    # the in-body one that is the behaviour under test.
    yield S3Target(storage)


def _put(target: S3Target, key: str, data: bytes, content_type: str) -> None:
    target.storage.put_object(
        key,
        BytesIO(data),
        content_type=content_type,
        content_length=len(data),
        metadata={"origin": "t2z-synthetic"},
    )


def test_put_get_list_and_delete_round_trip_through_the_real_adapter(s3_target: S3Target) -> None:
    prefix = f"t2z-{uuid4().hex}/"
    png_key, pdf_key = f"{prefix}artwork.png", f"{prefix}lesson.pdf"
    _put(s3_target, png_key, PNG, "image/png")
    _put(s3_target, pdf_key, PDF, "application/pdf")

    stored = s3_target.storage.get_object(png_key)
    assert stored is not None
    assert stored.body.read() == PNG
    assert stored.content_length == len(PNG)
    assert stored.content_type == "image/png"
    assert s3_target.storage.list_keys(prefix) == (png_key, pdf_key)

    s3_target.storage.delete_object(png_key)
    assert s3_target.storage.get_object(png_key) is None
    assert s3_target.storage.list_keys(prefix) == (pdf_key,)
    s3_target.storage.delete_object(pdf_key)
    assert s3_target.storage.list_keys(prefix) == ()


def test_a_missing_key_reads_as_none(s3_target: S3Target) -> None:
    assert s3_target.storage.get_object(f"t2z-{uuid4().hex}/never-written") is None


def test_the_task_bucket_is_already_present_after_ensure(s3_target: S3Target) -> None:
    client = build_s3_client(
        endpoint_url=os.environ["T2Z_S3_ENDPOINT"],
        region_name="us-east-1",
        access_key=os.environ["T2Z_S3_ACCESS_KEY"],
        secret_key=os.environ["T2Z_S3_SECRET_KEY"],
    )

    assert ensure_task_bucket(client, os.environ["T2Z_S3_BUCKET"]) is False


# --- PostgreSQL: scanner identity reaches core_asset_lineage ------------------------------


@dataclass
class DatabaseTarget:
    engine: Any
    sessions: Any
    database_name: str


@pytest.fixture(scope="module")
def database_target() -> Iterator[DatabaseTarget]:
    url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not url:
        pytest.skip("NOT_RUN: set BE1_TEST_DATABASE_URL to a disposable frc08_v3_t2z database")
    allowed = {
        "FRC08_ALLOWED_DATABASE": os.environ.get("FRC08_ALLOWED_DATABASE", ""),
        "FRC08_ALLOWED_PORT": os.environ.get("FRC08_ALLOWED_PORT", ""),
    }
    try:
        name, _port = check_database_url(url, allowed)
        if DATABASE_MARKER not in name:
            raise TargetRefused("DATABASE_NAME_REFUSED")
    except TargetRefused as refused:
        _refuse(refused.code)
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import NullPool

    engine = create_engine(url, poolclass=NullPool, hide_parameters=True)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT current_database()")).scalar_one() == name
    try:
        sessions = sessionmaker(engine, expire_on_commit=False, autoflush=False)
        yield DatabaseTarget(engine, sessions, name)
    finally:
        engine.dispose()


def _attach_with_scan(
    target: DatabaseTarget, scanner: LocalTestAllowlistScanner, *, scan_name: str | None = None
) -> tuple[str, str, str]:
    """Create a Parent run, scan the synthetic PNG, attach it; return (derived, name, version)."""
    from sketch2life.application.ports.parent_story_profile_lookup import (
        ParentStoryProfileReference,
    )
    from sketch2life.infrastructure.persistence.parent_story_repository import (
        SqlParentStoryRunRepository,
    )

    principal = VerifiedPrincipal(f"t2z-parent-{uuid4().hex}", "t2z-issuer", frozenset({"parent"}))
    profile = ParentStoryProfileReference(
        profile_id=uuid4(),
        profile_revision_id=uuid4(),
        state="ACTIVE",
        data_origin="SYNTHETIC_DEV",
        age_months=72,
        interests_summary=None,
    )
    run_id = str(uuid4())
    SqlParentStoryRunRepository(target.sessions()).create_run(
        principal=principal,
        account_id=f"account-{uuid4().hex}",
        profile=profile,
        idempotency_key=f"create-{uuid4().hex}",
        run_id=run_id,
        topic="t2z",
        adult_confirmed_idea="synthetic",
    )
    result = scanner.scan(BytesIO(PNG))
    name = scan_name or result.scanner_name
    original = f"parent/{run_id}/{uuid4().hex}/original"
    derived = f"parent/{run_id}/{uuid4().hex}/normalized.png"
    SqlParentStoryRunRepository(target.sessions()).attach_artwork(
        principal=principal,
        run_id=run_id,
        original_asset_ref=original,
        original_sha256="a" * 64,
        original_media_type="image/png",
        original_size_bytes=len(PNG),
        derived_asset_ref=derived,
        derived_sha256="b" * 64,
        derived_size_bytes=len(PNG),
        scanner_name=name,
        scanner_version=result.scanner_version,
    )
    return derived, name, result.scanner_version


def _png_scanner() -> LocalTestAllowlistScanner:
    return LocalTestAllowlistScanner(env="test", allowed_sha256=[hashlib.sha256(PNG).hexdigest()])


def _lineage(target: DatabaseTarget, derived_ref: str) -> tuple[str, str, str]:
    from sqlalchemy import text

    with target.engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT scanner_name, scanner_version, scanner_sha256 FROM core_asset_lineage "
                "WHERE derived_asset_ref = :ref"
            ),
            {"ref": derived_ref},
        ).one()
    return str(row[0]), str(row[1]), str(row[2])


def test_allowlist_scan_identity_is_recorded_in_core_asset_lineage(
    database_target: DatabaseTarget,
) -> None:
    scanner = _png_scanner()

    derived, name, version = _attach_with_scan(database_target, scanner)
    stored_name, stored_version, stored_hash = _lineage(database_target, derived)

    assert (stored_name, stored_version) == ("local-test-allowlist", scanner.scanner_version)
    assert stored_version == version
    assert len(stored_hash) == 64
    # The Parent formula sha256(name NUL version): the identity digest (F-1 stays with T-2a).
    assert stored_hash == scanner_identity_sha256(name, version)


def test_lineage_scanner_hash_depends_on_the_scanner_name_the_caller_passes(
    database_target: DatabaseTarget,
) -> None:
    """Repository-level check only: the stored hash follows the name, not a ClamAV verdict."""
    scanner = _png_scanner()

    local_ref, _, _ = _attach_with_scan(database_target, scanner)
    clamav_ref, _, _ = _attach_with_scan(
        database_target, scanner, scan_name="clamav-clamd-instream"
    )

    local = _lineage(database_target, local_ref)
    clamav = _lineage(database_target, clamav_ref)
    assert local[0] == "local-test-allowlist"
    assert clamav[0] == "clamav-clamd-instream"
    assert local[2] != clamav[2]


def test_scanner_level_unlisted_file_stops_before_attach_artwork_is_called(
    database_target: DatabaseTarget,
) -> None:
    """Scanner-level check: the scan raises first, so no lineage row is ever attempted."""
    from sqlalchemy import text

    scanner = LocalTestAllowlistScanner(env="test", allowed_sha256=["c" * 64])
    with database_target.engine.connect() as connection:
        before = connection.execute(text("SELECT count(*) FROM core_asset_lineage")).scalar_one()

    with pytest.raises(MalwareDetected):
        _attach_with_scan(database_target, scanner)

    with database_target.engine.connect() as connection:
        after = connection.execute(text("SELECT count(*) FROM core_asset_lineage")).scalar_one()
    assert after == before
