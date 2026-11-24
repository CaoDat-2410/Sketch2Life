from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

from sketch2life.application.ports.parent_video_candidates import (
    ParentVideoCandidateError,
    SilentStoryWorkerOutput,
)
from sketch2life.application.services.parent_video_candidate_service import (
    _MODEL_CODE_COMMIT,
    _MODEL_ID,
    _MODEL_REVISION,
    _VIDEO_PROFILE,
    ParentVideoCandidateService,
    _validate_worker_output,
)


def _worker_output(
    *,
    model_revision: str = _MODEL_REVISION,
    code_commit: str = _MODEL_CODE_COMMIT,
    omit_media_metadata: bool = False,
) -> tuple[SilentStoryWorkerOutput, SimpleNamespace]:
    video_bytes = b"synthetic-mp4-bytes"
    video_sha256 = hashlib.sha256(video_bytes).hexdigest()
    record = SimpleNamespace(
        job_id="job-safe-01",
        generation_id="generation-safe-01",
        attempt_id="attempt-safe-01",
        story_revision_id="00000000-0000-4000-8000-000000000001",
        story_sha256="a" * 64,
        source_asset_sha256="b" * 64,
    )
    manifest = {
        "schema_version": "sketch2life.modal.silent-story-video-output.v2",
        "workload": "video.story.generate",
        "status": "CANDIDATE_READY",
        "product_playable": False,
        "safety_validation": "NOT_RUN",
        "audio_streams": 0,
        "job_id": record.job_id,
        "generation_id": record.generation_id,
        "attempt_id": record.attempt_id,
        "story_revision_id": record.story_revision_id,
        "story_sha256": record.story_sha256,
        "source_drawing_sha256": record.source_asset_sha256,
        "storyboard_sha256": "c" * 64,
        "render_plan_sha256": "d" * 64,
        "scene_visual_plan_sha256": "e" * 64,
        "scene_count": 5,
        "output_ref": "output/video.mp4",
        "output_sha256": video_sha256,
        "output_size_bytes": len(video_bytes),
        "duration_seconds": 30.0,
        "width": 1280,
        "height": 720,
        "fps": 24.0,
        "video_codec": "h264",
        "model": {
            "id": _MODEL_ID,
            "revision": model_revision,
            "code_commit": code_commit,
            "dependency_lock_sha256": "f" * 64,
            "checkpoint_manifest_sha256": "1" * 64,
            "model_profile": _VIDEO_PROFILE,
        },
    }
    manifest_bytes = json.dumps(
        manifest, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    result = {
        **{key: value for key, value in manifest.items() if key != "model"},
        "model_profile": _VIDEO_PROFILE,
        "output_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    }
    if omit_media_metadata:
        for key in ("width", "height", "fps", "video_codec"):
            result.pop(key)
    return (
        SilentStoryWorkerOutput(
            result=result,
            output_manifest_bytes=manifest_bytes,
            video_bytes=video_bytes,
        ),
        record,
    )


def test_candidate_output_requires_pinned_model_revision_and_code() -> None:
    output, record = _worker_output()

    metadata = _validate_worker_output(output, record)

    assert metadata["model_id"] == _MODEL_ID
    assert metadata["model_revision"] == _MODEL_REVISION
    assert metadata["safety_validation"] == "NOT_RUN"
    assert metadata["product_playable"] is False


def test_candidate_output_rejects_different_checkpoint_revision() -> None:
    output, record = _worker_output(model_revision="unapproved-revision")

    with pytest.raises(ParentVideoCandidateError, match="VIDEO_WORKER_OUTPUT_INVALID"):
        _validate_worker_output(output, record)


def test_candidate_output_rejects_different_ltx_code_revision() -> None:
    output, record = _worker_output(code_commit="unapproved-code")

    with pytest.raises(ParentVideoCandidateError, match="VIDEO_WORKER_OUTPUT_INVALID"):
        _validate_worker_output(output, record)


def test_candidate_output_accepts_manifest_bound_media_metadata_when_result_omits_it() -> None:
    output, record = _worker_output(omit_media_metadata=True)

    metadata = _validate_worker_output(output, record)

    assert metadata["width"] == 1280
    assert metadata["height"] == 720
    assert metadata["fps"] == 24.0
    assert metadata["video_codec"] == "h264"


def test_candidate_output_rejects_conflicting_duplicate_media_metadata() -> None:
    output, record = _worker_output()
    output.result["width"] = 640

    with pytest.raises(ParentVideoCandidateError, match="VIDEO_WORKER_OUTPUT_INVALID"):
        _validate_worker_output(output, record)


def test_failed_output_contract_recovery_reuses_the_existing_modal_call_once() -> None:
    output, validation_record = _worker_output(omit_media_metadata=True)
    failed_record = SimpleNamespace(
        **vars(validation_record),
        video_candidate_id="candidate-01",
        run_id="run-01",
        state="FAILED",
        safe_failure_code="VIDEO_WORKER_OUTPUT_INVALID",
        modal_call_id="fc-existing-output",
        attempt_prefix="sketch2life/dev/run-01/candidate-01/",
        output_metadata=None,
    )
    recovering_record = SimpleNamespace(
        **{
            **vars(failed_record),
            "state": "AWAITING_RECONCILIATION",
            "safe_failure_code": None,
            "output_metadata": {
                "recovery": {
                    "kind": "same_modal_output_contract_revalidation_v1",
                    "source_failure_code": "VIDEO_WORKER_OUTPUT_INVALID",
                    "attempt_count": 1,
                }
            },
        }
    )

    class Repository:
        def __init__(self) -> None:
            self.recovery_claims = 0
            self.ready_record = None

        def begin_output_contract_recovery(self, **_kwargs):
            self.recovery_claims += 1
            return recovering_record

        def mark_candidate_ready(self, **kwargs):
            self.ready_record = SimpleNamespace(
                **{
                    **vars(recovering_record),
                    "state": "CANDIDATE_READY",
                    "output_asset_ref": kwargs["output_asset_ref"],
                    "output_sha256": kwargs["output_sha256"],
                    "output_size_bytes": kwargs["output_size_bytes"],
                    "output_manifest_sha256": kwargs["output_manifest_sha256"],
                    "output_metadata": kwargs["output_metadata"],
                }
            )
            return self.ready_record

    class Worker:
        def __init__(self) -> None:
            self.calls = []

        def collect_if_ready(self, **kwargs):
            self.calls.append(kwargs)
            return output

    class Storage:
        def __init__(self) -> None:
            self.objects = {}

        def put_object(self, key, body, **kwargs):
            self.objects[key] = body.read()

    repository = Repository()
    worker = Worker()
    storage = Storage()
    service = ParentVideoCandidateService(
        settings=SimpleNamespace(
            env="local",
            parent_video_dev_candidate_enabled=True,
            ai_provider="modal_dev",
            synthetic_pilot_enabled=True,
        ),
        story_repository=None,
        profile_lookup=None,
        candidate_repository=repository,
        storage=storage,
        worker=worker,
    )

    recovered = service._reconcile(
        principal=SimpleNamespace(issuer="synthetic", subject="owner"),
        run_id="run-01",
        record=failed_record,
    )

    assert recovered is repository.ready_record
    assert recovered.state == "CANDIDATE_READY"
    assert recovered.output_metadata["recovery"]["attempt_count"] == 1
    assert repository.recovery_claims == 1
    assert len(worker.calls) == 1
    assert worker.calls[0]["modal_call_id"] == "fc-existing-output"
    assert storage.objects[recovered.output_asset_ref] == output.video_bytes


def test_output_contract_recovery_marker_prevents_another_recovery() -> None:
    _output, validation_record = _worker_output(omit_media_metadata=True)
    failed_record = SimpleNamespace(
        **vars(validation_record),
        video_candidate_id="candidate-02",
        run_id="run-02",
        state="FAILED",
        safe_failure_code="VIDEO_WORKER_OUTPUT_INVALID",
        modal_call_id="fc-existing-output",
        attempt_prefix="sketch2life/dev/run-02/candidate-02/",
        output_metadata={
            "recovery": {
                "kind": "same_modal_output_contract_revalidation_v1",
                "source_failure_code": "VIDEO_WORKER_OUTPUT_INVALID",
                "attempt_count": 1,
            }
        },
    )
    service = ParentVideoCandidateService(
        settings=SimpleNamespace(
            env="local",
            parent_video_dev_candidate_enabled=True,
            ai_provider="modal_dev",
            synthetic_pilot_enabled=True,
        ),
        story_repository=None,
        profile_lookup=None,
        candidate_repository=None,
        storage=None,
        worker=None,
    )

    result = service._reconcile(
        principal=SimpleNamespace(issuer="synthetic", subject="owner"),
        run_id="run-02",
        record=failed_record,
    )

    assert result is failed_record


def test_candidate_service_fails_closed_when_dev_route_is_disabled() -> None:
    service = ParentVideoCandidateService(
        settings=SimpleNamespace(
            env="local",
            parent_video_dev_candidate_enabled=False,
            ai_provider="modal_dev",
            synthetic_pilot_enabled=True,
        ),
        story_repository=None,
        profile_lookup=None,
        candidate_repository=None,
        storage=None,
        worker=None,
    )

    with pytest.raises(ParentVideoCandidateError) as error:
        service._require_candidate_configuration()

    assert error.value.status_code == 503
    assert error.value.code == "PARENT_VIDEO_CANDIDATE_DISABLED"

