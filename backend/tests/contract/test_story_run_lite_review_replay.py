from __future__ import annotations

from typing import cast
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from sketch2life.application.ports.story_run_lite import (
    CommandResult,
    CoreAssetAdmissionPort,
    ImageNormalizerPort,
    ImageSafetyScannerPort,
    StoryRunLiteRepositoryPort,
    StoryRunLiteVisionPort,
    StoryRunReferencePort,
)
from sketch2life.application.services.story_run_lite import StoryRunLiteService
from sketch2life.domain.story_run_lite import (
    OwnerScopeKind,
    StoryRunLiteError,
    canonical_fingerprint,
    validate_idempotency_key,
)
from sketch2life.interfaces.http.story_run_lite_app import create_app

_RUN = "8ef31e64-a750-4cf4-bd84-958db52ad720"
_OWNER = "synthetic-review-parent"
_KEY = "review-attach-command"
_PAYLOAD = {"asset_ref": "synthetic-asset", "expected_revision": 1}


def _service(
    repository: Mock,
    references: Mock,
    admission: Mock,
    vision: Mock,
) -> StoryRunLiteService:
    return StoryRunLiteService(
        repository=cast(StoryRunLiteRepositoryPort, repository),
        scanner=cast(ImageSafetyScannerPort, object()),
        normalizer=cast(ImageNormalizerPort, object()),
        vision=cast(StoryRunLiteVisionPort, vision),
        story_references=cast(StoryRunReferencePort, references),
        asset_admission=cast(CoreAssetAdmissionPort, admission),
        actor_scope_ref=_OWNER,
    )


@pytest.mark.parametrize(
    "current_state", ["SUBJECT_REVIEW", "PREPARATION_REVIEW", "DELETE_PENDING"]
)
def test_http_attach_replays_original_snapshot_before_new_command_state_checks(
    current_state: str,
) -> None:
    repository, references, admission, vision = Mock(), Mock(), Mock(), Mock()
    snapshot = {"run_ref": _RUN, "run_state": "INPUT_PROCESSING", "version": 2, "revision": 2}
    repository.replay_attach_command.return_value = CommandResult(202, snapshot, 2, True)
    # Every post-attach state makes the original authorize_upload_target reject the request.
    references.authorize_upload_target.return_value = current_state == "INPUT_PROCESSING"
    with TestClient(
        create_app(service=_service(repository, references, admission, vision))
    ) as client:
        response = client.post(
            f"/v1/story-runs/{_RUN}/assets",
            headers={"Idempotency-Key": _KEY, "If-Match": '"1"'},
            json=_PAYLOAD,
        )
    assert response.status_code == 202
    assert response.json() == snapshot
    assert response.headers["etag"] == '"v2"'
    assert response.headers["location"] == f"/v1/story-runs/{_RUN}"
    repository.replay_attach_command.assert_called_once_with(
        actor_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
        actor_scope_ref=_OWNER,
        run_id=_RUN,
        key_sha256=validate_idempotency_key(_KEY),
        fingerprint_sha256=canonical_fingerprint(
            method="POST",
            path=f"/v1/story-runs/{_RUN}/assets",
            request=_PAYLOAD,
            expected_version=1,
        ),
    )
    references.authorize_upload_target.assert_not_called()
    admission.resolve_story_artwork.assert_not_called()
    repository.attach_asset.assert_not_called()
    vision.analyze.assert_not_called()


@pytest.mark.parametrize("status,code", [(400, "INVALID_IDEMPOTENCY_KEY"), (404, "NOT_FOUND")])
def test_http_attach_propagates_scoped_receipt_rejection_without_dispatch(
    status: int,
    code: str,
) -> None:
    repository, references, admission, vision = Mock(), Mock(), Mock(), Mock()
    repository.replay_attach_command.side_effect = StoryRunLiteError(
        status, code, "The scoped receipt does not authorize this replay."
    )
    with TestClient(
        create_app(service=_service(repository, references, admission, vision))
    ) as client:
        response = client.post(
            f"/v1/story-runs/{_RUN}/assets",
            headers={"Idempotency-Key": _KEY, "If-Match": '"1"'},
            json=_PAYLOAD,
        )
    assert response.status_code == status
    assert response.json()["code"] == code
    references.authorize_upload_target.assert_not_called()
    admission.resolve_story_artwork.assert_not_called()
    repository.attach_asset.assert_not_called()
    vision.analyze.assert_not_called()


def test_http_new_attach_still_requires_current_owned_input_processing_run() -> None:
    repository, references, admission, vision = Mock(), Mock(), Mock(), Mock()
    repository.replay_attach_command.return_value = None
    references.authorize_upload_target.return_value = False
    with TestClient(
        create_app(service=_service(repository, references, admission, vision))
    ) as client:
        response = client.post(
            f"/v1/story-runs/{_RUN}/assets",
            headers={"Idempotency-Key": _KEY, "If-Match": '"1"'},
            json=_PAYLOAD,
        )
    assert response.status_code == 404
    admission.resolve_story_artwork.assert_not_called()
    repository.attach_asset.assert_not_called()
    vision.analyze.assert_not_called()


@pytest.mark.parametrize("failure", ["target", "admission"])
def test_http_attach_rechecks_locked_receipt_after_mutable_check_race(failure: str) -> None:
    repository, references, admission, vision = Mock(), Mock(), Mock(), Mock()
    snapshot = {"run_ref": _RUN, "run_state": "INPUT_PROCESSING", "version": 2, "revision": 2}
    repository.replay_attach_command.side_effect = [None, CommandResult(202, snapshot, 2, True)]
    references.authorize_upload_target.return_value = failure != "target"
    admission.resolve_story_artwork.side_effect = StoryRunLiteError(
        409, "ASSET_SCOPE_MISMATCH", "Admission changed while the first command completed."
    )
    with TestClient(
        create_app(service=_service(repository, references, admission, vision))
    ) as client:
        response = client.post(
            f"/v1/story-runs/{_RUN}/assets",
            headers={"Idempotency-Key": _KEY, "If-Match": '"v1"'},
            json=_PAYLOAD,
        )
    assert response.status_code == 202 and response.json() == snapshot
    assert response.headers["etag"] == '"v2"'
    assert repository.replay_attach_command.call_count == 2
    repository.attach_asset.assert_not_called()
    vision.analyze.assert_not_called()


def test_http_attach_pending_receipt_race_holds_without_dispatch() -> None:
    repository, references, admission, vision = Mock(), Mock(), Mock(), Mock()
    repository.replay_attach_command.side_effect = [
        None,
        StoryRunLiteError(409, "COMMAND_RECOVERY_HOLD", "Pending command.", retryable=False),
    ]
    references.authorize_upload_target.return_value = False
    with TestClient(
        create_app(service=_service(repository, references, admission, vision))
    ) as client:
        response = client.post(
            f"/v1/story-runs/{_RUN}/assets",
            headers={"Idempotency-Key": _KEY, "If-Match": '"v1"'},
            json=_PAYLOAD,
        )
    assert response.status_code == 409 and response.json()["code"] == "COMMAND_RECOVERY_HOLD"
    assert response.json()["retryable"] is False
    assert repository.replay_attach_command.call_count == 2
    repository.attach_asset.assert_not_called()
    vision.analyze.assert_not_called()
