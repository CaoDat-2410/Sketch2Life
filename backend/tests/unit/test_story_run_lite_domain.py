from __future__ import annotations

import hashlib
import uuid

import pytest

from sketch2life.domain.story_run_lite import (
    MAX_PART_BYTES,
    MAX_PARTS,
    MAX_UPLOAD_BYTES,
    StoryRunLiteError,
    canonical_fingerprint,
    etag,
    parse_etag_version,
    validate_idempotency_key,
    validate_part_number,
    validate_upload_bounds,
)
from sketch2life.infrastructure.story_run_lite.quarantine import (
    QuarantineError,
    QuarantineStore,
)


def test_idempotency_identity_and_canonical_fingerprint_are_stable() -> None:
    digest = validate_idempotency_key("synthetic-request-01")
    assert len(digest) == 64
    assert digest != "synthetic-request-01"

    first = canonical_fingerprint(
        method="post",
        path="/v1/story-runs",
        request={"profile_ref": "synthetic-parent-demo"},
    )
    same = canonical_fingerprint(
        method="POST",
        path="/v1/story-runs",
        request={"profile_ref": "synthetic-parent-demo"},
    )
    changed_version = canonical_fingerprint(
        method="POST",
        path="/v1/story-runs",
        request={"profile_ref": "synthetic-parent-demo"},
        expected_version=2,
    )
    assert first == same
    assert first != changed_version


@pytest.mark.parametrize("value", ["", "contains\ncontrol", "x" * 201])
def test_invalid_idempotency_keys_fail_closed(value: str) -> None:
    with pytest.raises(StoryRunLiteError) as error:
        validate_idempotency_key(value)
    assert error.value.code == "INVALID_IDEMPOTENCY_KEY"


def test_strong_etag_and_upload_bounds() -> None:
    assert etag(7) == '"v7"'
    assert parse_etag_version('"v7"') == 7
    assert parse_etag_version('"7"') == 7
    with pytest.raises(StoryRunLiteError, match="strong ETag"):
        parse_etag_version('W/"v7"')
    with pytest.raises(StoryRunLiteError) as missing:
        parse_etag_version(None)
    assert missing.value.status_code == 428

    validate_upload_bounds(MAX_UPLOAD_BYTES)
    with pytest.raises(StoryRunLiteError) as too_large:
        validate_upload_bounds(MAX_UPLOAD_BYTES + 1)
    assert too_large.value.status_code == 413
    assert MAX_PART_BYTES == 4_194_304
    assert MAX_PARTS == 5
    assert MAX_UPLOAD_BYTES == 20_971_520
    with pytest.raises(StoryRunLiteError) as exact_overflow:
        validate_upload_bounds(20_971_521)
    assert exact_overflow.value.code == "IMAGE_TOO_LARGE"


@pytest.mark.parametrize("part_count", [1, 2, 5])
def test_quarantine_assembles_exactly_one_two_or_five_contiguous_parts(
    tmp_path, part_count: int
) -> None:
    store = QuarantineStore(tmp_path / "quarantine")
    upload_id = str(uuid.uuid4())
    parts = [f"synthetic-part-{part_number}".encode() for part_number in range(1, part_count + 1)]
    part_rows = []
    for part_number, payload in enumerate(parts, start=1):
        digest, size = store.write_part(upload_id, part_number, payload)
        part_rows.append({"part_number": part_number, "sha256": digest, "byte_size": size})
    snapshot = b"".join(parts)
    _, assembled = store.assemble_snapshot(
        upload_id,
        part_rows,
        expected_size=len(snapshot),
        expected_sha256=hashlib.sha256(snapshot).hexdigest(),
    )
    assert assembled == snapshot


def test_quarantine_rejects_gaps_and_snapshot_digest_mismatch(tmp_path) -> None:
    store = QuarantineStore(tmp_path / "quarantine")
    upload_id = str(uuid.uuid4())
    first = b"synthetic-first-part"
    third = b"synthetic-third-part"
    first_sha, first_size = store.write_part(upload_id, 1, first)
    third_sha, third_size = store.write_part(upload_id, 3, third)
    rows = [
        {"part_number": 1, "sha256": first_sha, "byte_size": first_size},
        {"part_number": 3, "sha256": third_sha, "byte_size": third_size},
    ]
    with pytest.raises(QuarantineError, match="contiguous"):
        store.assemble_snapshot(
            upload_id,
            rows,
            expected_size=first_size + third_size,
            expected_sha256=hashlib.sha256(first + third).hexdigest(),
        )

    with pytest.raises(QuarantineError, match="size or SHA-256"):
        store.assemble_snapshot(
            upload_id,
            [rows[0]],
            expected_size=first_size,
            expected_sha256="0" * 64,
        )


@pytest.mark.parametrize("part_number", [0, 6])
def test_part_number_is_bounded(part_number: int) -> None:
    with pytest.raises(StoryRunLiteError):
        validate_part_number(part_number)
