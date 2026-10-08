"""A story job must use this approved session's admitted source image."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sketch2life.application.services.story_video_job import (
    StoryVideoInputError,
    StoryVideoJobService,
)
from sketch2life.contracts.schemas.story_video import (
    ApprovedStoryPackageV1,
    StoryScriptSegmentV1,
    stable_model_hash,
    story_script_segments_hash,
)
from sketch2life.infrastructure.storage.in_memory import InMemoryArtifactStore


def _package(source_ref: str, source_hash: str) -> ApprovedStoryPackageV1:
    digest = "a" * 64
    package = ApprovedStoryPackageV1(
        package_id="pkg-test",
        session_id="session-test",
        session_version=3,
        source_image_ref=source_ref,
        source_image_sha256=source_hash,
        confirmed_understanding_ref="understanding:test",
        confirmed_understanding_sha256=digest,
        experience_spec_ref="experience:test",
        experience_spec_sha256=digest,
        story_script_ref="script:test",
        story_script_revision=1,
        story_script_sha256=story_script_segments_hash(_segments()),
        audience_profile_ref="audience:test",
        audience_profile_sha256=digest,
        evidence_set_ref="evidence:test",
        evidence_set_sha256=digest,
        locale="vi-VN",
        narration_profile_ref="voice:test",
        narration_profile_sha256=digest,
        approval_ref="approval:test",
        approval_sha256=digest,
        content_validator_version="test-v1",
        content_validator_result="PASSED",
        created_at="2026-10-08T00:00:00Z",
        package_hash=digest,
    )
    return _rehash(package)


def _rehash(package: ApprovedStoryPackageV1) -> ApprovedStoryPackageV1:
    return package.model_copy(
        update={"package_hash": stable_model_hash(package, exclude={"package_hash"})}
    )


def _segments() -> tuple[StoryScriptSegmentV1, ...]:
    return tuple(
        StoryScriptSegmentV1(
            segment_id=f"segment-{index}",
            text=f"Đoạn kể đã duyệt {index}.",
            approved_fact_ids=(f"fact-{index}",),
            confirmed_anchor_ids=("anchor-1",),
            scene_purpose=purpose,
        )
        for index, purpose in enumerate(("INTRO", "EXPLAIN", "RECAP"), 1)
    )


def _service(store: InMemoryArtifactStore, *, state: str = "EXPERIENCE_READY", version=3):
    return StoryVideoJobService(
        session_snapshot=lambda _session_id: SimpleNamespace(
            state=state, status="ACTIVE", version=version
        ),
        source_artifacts=store,
    )


def test_story_job_accepts_only_session_bound_source() -> None:
    store = InMemoryArtifactStore()
    source = store.put(session_id="session-test", content_type="image/png", body=b"image")
    job, replayed = _service(store).create_or_replay(
        session_id="session-test",
        idempotency_key="request-1",
        package=_package(source.artifact_ref, source.sha256),
        segments=_segments(),
    )
    assert not replayed
    assert job.state == "QUEUED"


def test_story_job_rejects_other_session_source() -> None:
    store = InMemoryArtifactStore()
    source = store.put(session_id="another-session", content_type="image/png", body=b"image")
    with pytest.raises(StoryVideoInputError, match="STORY_SOURCE_MISMATCH"):
        _service(store).create_or_replay(
            session_id="session-test",
            idempotency_key="request-1",
            package=_package(source.artifact_ref, source.sha256),
            segments=_segments(),
        )


def test_story_job_rejects_stale_session_and_mismatched_source_hash() -> None:
    store = InMemoryArtifactStore()
    source = store.put(session_id="session-test", content_type="image/png", body=b"image")
    with pytest.raises(StoryVideoInputError, match="STORY_SESSION_NOT_APPROVED"):
        _service(store, state="GATE_B_PENDING").create_or_replay(
            session_id="session-test",
            idempotency_key="request-1",
            package=_package(source.artifact_ref, source.sha256),
            segments=_segments(),
        )
    with pytest.raises(StoryVideoInputError, match="STORY_SESSION_VERSION_MISMATCH"):
        _service(store, version=4).create_or_replay(
            session_id="session-test",
            idempotency_key="request-1",
            package=_package(source.artifact_ref, source.sha256),
            segments=_segments(),
        )
    with pytest.raises(StoryVideoInputError, match="STORY_SOURCE_MISMATCH"):
        _service(store).create_or_replay(
            session_id="session-test",
            idempotency_key="request-1",
            package=_rehash(
                _package(source.artifact_ref, source.sha256).model_copy(
                    update={"source_image_sha256": "b" * 64}
                )
            ),
            segments=_segments(),
        )


def test_story_job_rejects_mutated_script_and_package_hash() -> None:
    store = InMemoryArtifactStore()
    source = store.put(session_id="session-test", content_type="image/png", body=b"image")
    package = _package(source.artifact_ref, source.sha256)
    changed = list(_segments())
    changed[0] = changed[0].model_copy(update={"text": "Nội dung bị đổi sau duyệt."})
    with pytest.raises(StoryVideoInputError, match="STORY_SCRIPT_HASH_MISMATCH"):
        _service(store).create_or_replay(
            session_id="session-test",
            idempotency_key="request-1",
            package=package,
            segments=tuple(changed),
        )
    with pytest.raises(StoryVideoInputError, match="STORY_PACKAGE_HASH_MISMATCH"):
        _service(store).create_or_replay(
            session_id="session-test",
            idempotency_key="request-1",
            package=package.model_copy(update={"approval_ref": "approval:changed"}),
            segments=_segments(),
        )


def test_expired_session_cannot_keep_a_ready_story_job() -> None:
    store = InMemoryArtifactStore()
    source = store.put(session_id="session-test", content_type="image/png", body=b"image")
    active = True

    def snapshot(_session_id: str):
        if not active:
            raise KeyError("session expired")
        return SimpleNamespace(state="EXPERIENCE_READY", status="ACTIVE", version=3)

    service = StoryVideoJobService(session_snapshot=snapshot, source_artifacts=store)
    job, _ = service.create_or_replay(
        session_id="session-test",
        idempotency_key="request-1",
        package=_package(source.artifact_ref, source.sha256),
        segments=_segments(),
    )
    active = False

    assert service.get(job.job_id).state == "EXPIRED"
    service.run_safely(job.job_id)
    assert service.get(job.job_id).state == "EXPIRED"
