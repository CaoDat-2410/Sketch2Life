"""Parent service gating and repository boundary tests."""

from __future__ import annotations

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_profiles import ParentCommandResult
from sketch2life.application.services.parent_profiles import ParentProfileService
from sketch2life.domain.parent_profiles import ParentProfileError, ProfileSnapshot


class RecordingRepository:
    def __init__(self) -> None:
        self.create_calls = 0

    def create_profile(self, **kwargs: object) -> ParentCommandResult:
        self.create_calls += 1
        return ParentCommandResult(201, {"profile_id": "generated"})

    def get_profile(self, **kwargs: object) -> dict[str, object]:
        return {"profile_id": "generated"}

    def patch_profile(self, **kwargs: object) -> ParentCommandResult:
        return ParentCommandResult(200, {"profile_id": "generated"})


def test_disabled_synthetic_creation_fails_before_repository_write() -> None:
    repository = RecordingRepository()
    service = ParentProfileService(repository, synthetic_enabled=False)

    try:
        service.create_profile(
            principal=VerifiedPrincipal("parent-1", "issuer-1", frozenset()),
            snapshot=ProfileSnapshot("Mina", 72, None),
            idempotency_key="synthetic-key",
            request_id="request-1",
        )
    except ParentProfileError as error:
        assert error.status_code == 409
        assert error.code == "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE"
    else:
        raise AssertionError("disabled synthetic creation unexpectedly succeeded")

    assert repository.create_calls == 0


def test_enabled_synthetic_creation_validates_then_delegates_once() -> None:
    repository = RecordingRepository()
    service = ParentProfileService(repository, synthetic_enabled=True)

    result = service.create_profile(
        principal=VerifiedPrincipal("parent-1", "issuer-1", frozenset()),
        snapshot=ProfileSnapshot("Mina", 72, None),
        idempotency_key="synthetic-key",
        request_id="request-1",
    )

    assert result.status_code == 201
    assert repository.create_calls == 1
