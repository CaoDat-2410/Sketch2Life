from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import cast
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from test_story_run_lite_postgres import _asset_pair, _create_run, _hash, story_db  # noqa: F401

from sketch2life.application.ports.story_run_lite import (
    CoreAssetAdmissionPort,
    ImageNormalizerPort,
    ImageSafetyScannerPort,
    StoryRunLiteVisionPort,
    ValidatedVisionResult,
    VisionAttemptResult,
)
from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.domain.story_run_lite import (
    OwnerScopeKind,
    canonical_fingerprint,
    validate_idempotency_key,
)
from sketch2life.interfaces.http.story_run_lite_app import create_app


@pytest.mark.parametrize("pending", [False, True])
def test_http_overlap_rechecks_receipt_after_first_lookup_miss(request, monkeypatch, pending):
    _engine, repository = request.getfixturevalue("story_db")
    owner = "synthetic-overlap-" + uuid.uuid4().hex
    run_id = _create_run(repository, owner)
    pair = _asset_pair(run_id, owner, seed=owner)
    original_lookup = repository.replay_attach_command
    missed, committed = threading.Event(), threading.Event()
    first_replay_lookup = True

    def lookup(**values):
        nonlocal first_replay_lookup
        result = original_lookup(**values)
        # TestClient executes sync endpoints on an AnyIO worker, not the caller thread.
        # The main request only starts after this first replay lookup signals `missed`.
        if first_replay_lookup:
            first_replay_lookup = False
            assert result is None
            missed.set()
            assert committed.wait(10)
        return result

    monkeypatch.setattr(repository, "replay_attach_command", lookup)
    admission, vision = Mock(), Mock()
    admission.resolve_story_artwork.return_value = pair

    def analyze(*, run_id, binding, persist_success):
        assert persist_success(
            ValidatedVisionResult(
                {"test": "overlap"}, "Synthetic", 0.5, _hash("canonical"), _hash("raw")
            )
        )
        return VisionAttemptResult("SUCCEEDED", provider_invoked=True, result_committed=True)

    vision.analyze.side_effect = analyze
    service = StoryRunLiteService(
        repository=repository,
        scanner=cast(ImageSafetyScannerPort, object()),
        normalizer=cast(ImageNormalizerPort, object()),
        vision=cast(StoryRunLiteVisionPort, vision),
        story_references=repository,
        asset_admission=cast(CoreAssetAdmissionPort, admission),
        actor_scope_ref=owner,
    )
    app = create_app(service=service)
    key = "overlap-" + uuid.uuid4().hex
    headers = {"Idempotency-Key": key, "If-Match": '"v1"'}
    body = {"asset_ref": pair.original.asset_ref, "expected_revision": 1}

    def replay():
        with TestClient(app) as client:
            return client.post(f"/v1/story-runs/{run_id}/assets", json=body, headers=headers)

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="overlap-replay") as pool:
        future = pool.submit(replay)
        try:
            assert missed.wait(10)
            if pending:
                # An interrupted first dispatcher reserved PENDING, then cancellation made
                # the target check fail. The durable receipt must still give a hold.
                reserved, _job, _claim = repository.attach_asset(
                    actor_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
                    actor_scope_ref=owner,
                    run_id=run_id,
                    pair=pair,
                    expected_revision=1,
                    expected_version=1,
                    key_sha256=validate_idempotency_key(key),
                    fingerprint_sha256=canonical_fingerprint(
                        method="POST",
                        path=f"/v1/story-runs/{run_id}/assets",
                        request=body,
                        expected_version=1,
                    ),
                )
                canceled = repository.cancel_run(
                    actor_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
                    actor_scope_ref=owner,
                    run_id=run_id,
                    expected_revision=int(reserved.body["revision"]),
                    expected_version=int(reserved.body["version"]),
                    key_sha256=_hash("cancel:" + owner),
                    fingerprint_sha256=_hash("cancel-fingerprint:" + owner),
                )
                assert canceled.status_code == 202
            else:
                with TestClient(app) as client:
                    initial = client.post(
                        f"/v1/story-runs/{run_id}/assets", json=body, headers=headers
                    )
                assert initial.status_code == 202
                current = repository.get_run(
                    actor_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
                    actor_scope_ref=owner,
                    run_id=run_id,
                )
                assert current.body["run_state"] == "SUBJECT_REVIEW"
        finally:
            committed.set()
        response = future.result(timeout=10)
    if pending:
        assert response.status_code == 409
        assert response.json()["code"] == "COMMAND_RECOVERY_HOLD"
    else:
        assert (response.status_code, response.json(), response.headers["etag"]) == (
            initial.status_code,
            initial.json(),
            initial.headers["etag"],
        )
    assert vision.analyze.call_count == (0 if pending else 1)
    assert admission.resolve_story_artwork.call_count == (0 if pending else 1)
