"""FEAT-066 T-2d: the shared story output, the rewrite request rules and the rewrite reservation.

Offline: no database. The repository is driven with a statement-recording session (the same style as
``test_parent_story_run_cancel_repository``); behaviour on PostgreSQL lives in
``tests/integration/test_parent_story_rewrites_postgres.py``.
"""

from __future__ import annotations

import ast
import contextlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

import sketch2life.infrastructure.story_inputs.story_generation as generation_module
import sketch2life.interfaces.http.routers.parent_ai as parent_ai_module
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_inputs import (
    STORY_GENERATION_UNAVAILABLE,
    StoryGenerationFailure,
    StoryGenerationResult,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryLifecycleRecord,
    ParentStoryRevisionReservation,
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.application.services.story_output import (
    EDUCATIONAL_FACT_CHECK_FAILED,
    STORY_OUTPUT_INVALID,
    StoryOutputInvalid,
    complete_generated_story,
    normalize_story_output,
)
from sketch2life.contracts.schemas.parent_story_inputs import (
    ParentStoryRewriteAcceptedV1,
    RewriteStoryRequestV1,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.story_inputs.fixtures import (
    FixtureStoryGenerator,
    worker_input_sha256,
)
from sketch2life.infrastructure.story_inputs.story_generation import (
    REWRITE_NEUTRAL_INSTRUCTION_V1,
    REWRITE_NEUTRAL_INSTRUCTION_VERSION,
    STORY_REWRITE_PROMPT_VERSION,
)

PRINCIPAL = VerifiedPrincipal("parent-1", "issuer-1", frozenset({"parent"}))
RUN_ID = "22222222-2222-4222-8222-222222222222"
HASH = "a" * 64
HINT = "HINT-SENTENCE make the dragon braver"


def valid_story(*, subject_text: str = "con rồng nhỏ") -> dict[str, Any]:
    """A draft that passes ``StoryRevisionDraftV1`` (five contiguous scenes, 40 s)."""
    scenes = [
        {
            "scene_index": index,
            "title": f"Cảnh {index}",
            "action": f"{subject_text} làm việc {index}",
            "visual_prompt": f"visual {index}",
            "narration": f"lời kể {index}",
            "start_ms": (index - 1) * 8_000,
            "duration_ms": 8_000,
            "character_anchors": ["đôi cánh nhỏ"],
        }
        for index in range(1, 6)
    ]
    return {
        "schema_version": "sketch2life.story-revision.v1",
        "language": "vi",
        "title": "Rồng nhỏ biết chia sẻ",
        "story": {"opening": "Mở đầu", "middle": "Giữa truyện", "ending": "Kết thúc"},
        "duration_ms": 40_000,
        "scenes": scenes,
    }


# ------------------------------------------------------------------------- story_output
def test_a_valid_draft_is_normalized_and_hashed() -> None:
    story, digest = normalize_story_output(valid_story(), confirmed_subject="rồng")
    assert story["language"] == "vi" and len(story["scenes"]) == 5
    assert len(digest) == 64
    again = normalize_story_output(valid_story(), confirmed_subject="rồng")
    assert again == (story, digest)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda story: story.pop("title"),
        lambda story: story.update(language="en"),
        lambda story: story.update(extra="x"),
        lambda story: story.update(duration_ms=39_000),
        lambda story: story["scenes"].pop(),
    ],
)
def test_an_invalid_draft_is_story_output_invalid(mutate: Any) -> None:
    story = valid_story()
    mutate(story)
    with pytest.raises(StoryOutputInvalid) as refused:
        normalize_story_output(story, confirmed_subject="rồng")
    assert refused.value.code == STORY_OUTPUT_INVALID


def test_a_butterfly_draft_that_breaks_the_life_cycle_is_a_fact_check_failure() -> None:
    story = valid_story(subject_text="bướm")
    story["story"] = {
        "opening": "Một chú bướm tìm kiếm một cái tổ",
        "middle": "Trứng nở ra bướm",
        "ending": "Hết",
    }
    with pytest.raises(StoryOutputInvalid) as refused:
        normalize_story_output(story, confirmed_subject="con bướm")
    assert refused.value.code == EDUCATIONAL_FACT_CHECK_FAILED


class _Repository:
    def __init__(self, *, record: Any = None, complete_error: Exception | None = None) -> None:
        self.record = record
        self.complete_error = complete_error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def fail_story_revision(self, **kwargs: Any) -> None:
        self.calls.append(("fail", kwargs))

    def complete_story_revision(self, **kwargs: Any) -> Any:
        self.calls.append(("complete", kwargs))
        if self.complete_error is not None:
            raise self.complete_error
        return self.record


def _reservation(receipt_id: str | None = None) -> ParentStoryRevisionReservation:
    return ParentStoryRevisionReservation(
        run_id=RUN_ID,
        story_revision_id="rev-2",
        revision_no=2,
        understanding_revision=1,
        context_revision=1,
        source_asset_sha256=HASH,
        worker_input={"confirmed_subject": "rồng"},
        request_sha256=HASH,
        receipt_id=receipt_id,
    )


def _record() -> ParentStoryRunRecord:
    return SimpleNamespace()  # type: ignore[return-value]


def test_a_valid_draft_is_stored_with_its_hash_and_provenance() -> None:
    repository = _Repository(record=_record())
    result = complete_generated_story(
        repository,  # type: ignore[arg-type]
        principal=PRINCIPAL,
        reservation=_reservation(),
        raw_story=valid_story(),
        provider_call_id="call-1",
        model_id="m",
        model_revision="r",
    )
    assert result is repository.record
    (name, kwargs) = repository.calls[0]
    assert name == "complete"
    assert (
        kwargs["story_sha256"] == normalize_story_output(valid_story(), confirmed_subject="rồng")[1]
    )
    assert (kwargs["provider_call_id"], kwargs["model_id"], kwargs["model_revision"]) == (
        "call-1",
        "m",
        "r",
    )


def test_an_invalid_draft_records_the_failure_and_raises() -> None:
    repository = _Repository()
    broken = valid_story()
    broken.pop("title")
    with pytest.raises(StoryOutputInvalid):
        complete_generated_story(
            repository,  # type: ignore[arg-type]
            principal=PRINCIPAL,
            reservation=_reservation(),
            raw_story=broken,
            provider_call_id="call-1",
            model_id="m",
            model_revision="r",
        )
    assert [name for name, _ in repository.calls] == ["fail"]
    failure = repository.calls[0][1]
    assert failure["error_code"] == STORY_OUTPUT_INVALID and failure["outcome_unknown"] is False


def test_a_purged_run_during_the_fail_write_surfaces_as_the_repository_error() -> None:
    class Purged(_Repository):
        def fail_story_revision(self, **kwargs: Any) -> None:
            raise ParentStoryRunError(409, "INVALID_STATE_TRANSITION")

    broken = valid_story()
    broken.pop("title")
    with pytest.raises(ParentStoryRunError) as refused:
        complete_generated_story(
            Purged(),  # type: ignore[arg-type]
            principal=PRINCIPAL,
            reservation=_reservation(),
            raw_story=broken,
            provider_call_id="c",
            model_id="m",
            model_revision="r",
        )
    assert refused.value.code == "INVALID_STATE_TRANSITION"


def test_a_lifecycle_projection_from_the_store_is_never_served() -> None:
    projection = ParentStoryLifecycleRecord(RUN_ID, "DELETE_PENDING", 3, 3, "req", "PENDING")
    with pytest.raises(ParentStoryRunError) as refused:
        complete_generated_story(
            _Repository(record=projection),  # type: ignore[arg-type]
            principal=PRINCIPAL,
            reservation=_reservation(),
            raw_story=valid_story(),
            provider_call_id="c",
            model_id="m",
            model_revision="r",
        )
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")


def test_the_legacy_route_and_the_service_share_one_implementation() -> None:
    source = Path(str(parent_ai_module.__file__)).read_text(encoding="utf-8")
    assert "complete_generated_story" in source
    assert "validate_butterfly_lifecycle_v1" not in source
    assert "StoryRevisionDraftV1" not in source


# ------------------------------------------------------------------------- the request rules
def test_the_rewrite_request_accepts_the_four_revisions_and_trims_the_hint() -> None:
    for revision in (1, 2, 3, 4):
        assert RewriteStoryRequestV1(expected_story_revision=revision).hint is None
    request = RewriteStoryRequestV1(expected_story_revision=2, hint=f"  {HINT}  ")
    assert request.hint == HINT


@pytest.mark.parametrize(
    "values",
    [
        {"expected_story_revision": 0},
        {"expected_story_revision": 5},
        {"expected_story_revision": 1, "hint": ""},
        {"expected_story_revision": 1, "hint": "  "},
        {"expected_story_revision": 1, "hint": "x" * 401},
        {"expected_story_revision": 1, "hint": "a\u0000b"},
        {"expected_story_revision": 1, "hint": "a\u0085b"},
        {"expected_story_revision": 1, "hint": "a\nb"},
        {"expected_story_revision": 1, "expected_story_sha256": "A" * 64},
        {"expected_story_revision": 1, "extra": 1},
    ],
)
def test_the_rewrite_request_refuses_what_the_contract_refuses(values: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        RewriteStoryRequestV1(**values)


def test_the_rewrite_answer_is_bounded() -> None:
    body = {
        "request_id": "11111111-1111-4111-8111-111111111111",
        "story_run_id": RUN_ID,
        "story_revision_no": 4,
        "run_revision": 3,
        "run_state": "SCRIPT_GENERATING",
    }
    assert ParentStoryRewriteAcceptedV1.model_validate(body).story_revision_no == 4
    with pytest.raises(ValidationError):
        ParentStoryRewriteAcceptedV1.model_validate({**body, "run_state": "SCRIPT_REVIEW"})
    with pytest.raises(ValidationError):
        ParentStoryRewriteAcceptedV1.model_validate({**body, "job": {"id": "x"}})


def test_the_neutral_instruction_is_a_versioned_constant() -> None:
    assert REWRITE_NEUTRAL_INSTRUCTION_VERSION == "rewrite-neutral.v1"
    assert REWRITE_NEUTRAL_INSTRUCTION_V1 == (
        "Hãy viết lại câu chuyện theo một cách khác, giữ nguyên chủ thể và ý tưởng của người lớn."
    )
    assert STORY_REWRITE_PROMPT_VERSION == "parent-story-rewrite.v1"


# ------------------------------------------------------------------------- fixture generator
def test_the_fixture_generator_answers_only_for_a_registered_input_hash() -> None:
    worker_input = {"confirmed_subject": "rồng", "adult_confirmed_idea": "một ý tưởng"}
    result = StoryGenerationResult(valid_story(), "call-1", "fixture-model", "1")
    generator = FixtureStoryGenerator({worker_input_sha256(worker_input): result})
    assert generator.generate(worker_input) is result
    with pytest.raises(StoryGenerationFailure) as refused:
        generator.generate({**worker_input, "adult_rewrite_hint": "other"})
    assert refused.value.code == STORY_GENERATION_UNAVAILABLE
    assert len(generator.calls) == 2


def test_the_story_generation_module_has_no_provider_import() -> None:
    tree = ast.parse(Path(generation_module.__file__).read_text(encoding="utf-8"))
    imported = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not [name for name in imported if "modal" in name.lower() or name.startswith("boto")]


# ------------------------------------------------------------------------- bounded strings
class _RunnerRepository:
    """Stands for ``SqlParentStoryRunRepository`` inside the runner; records the writes."""

    calls: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, session: Any) -> None:
        pass

    def start_story_generation(self, **kwargs: Any) -> bool:
        return True

    def fail_story_revision(self, **kwargs: Any) -> None:
        self.calls.append(("fail", kwargs))

    def complete_story_revision(self, **kwargs: Any) -> Any:
        self.calls.append(("complete", kwargs))
        return SimpleNamespace()


class _Generator:
    def __init__(self, *, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error

    def generate(self, worker_input: Any) -> Any:
        if self.error is not None:
            raise self.error
        return self.result


def _run_runner(monkeypatch: pytest.MonkeyPatch, generator: Any) -> list[tuple[str, Any]]:
    _RunnerRepository.calls = []
    monkeypatch.setattr(generation_module, "SqlParentStoryRunRepository", _RunnerRepository)
    runner = generation_module.ParentStoryRewriteRunner(
        lambda: SimpleNamespace(close=lambda: None),  # type: ignore[arg-type, return-value]
        generator,
    )
    runner.run(PRINCIPAL, _reservation())
    return _RunnerRepository.calls


@pytest.mark.parametrize(
    ("code", "stored"),
    [
        ("STORY_GENERATION_UNAVAILABLE", "STORY_GENERATION_UNAVAILABLE"),
        ("PROVIDER_QUOTA", "PROVIDER_QUOTA"),
        ("X" * 64, "X" * 64),
        ("X" * 65, STORY_GENERATION_UNAVAILABLE),
        ("lower_case", STORY_GENERATION_UNAVAILABLE),
        ("HAS SPACE", STORY_GENERATION_UNAVAILABLE),
        ("", STORY_GENERATION_UNAVAILABLE),
        ("1_STARTS_WITH_DIGIT", STORY_GENERATION_UNAVAILABLE),
    ],
)
def test_a_generator_failure_code_is_validated_before_the_store_write(
    monkeypatch: pytest.MonkeyPatch, code: str, stored: str
) -> None:
    calls = _run_runner(monkeypatch, _Generator(error=StoryGenerationFailure(code)))
    assert [name for name, _ in calls] == ["fail"]
    assert calls[0][1]["error_code"] == stored and len(stored) <= 64
    assert calls[0][1]["outcome_unknown"] is False


def test_over_long_generator_provenance_is_truncated_before_the_store_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = StoryGenerationResult(valid_story(), "c" * 500, "m" * 900, "r" * 300)
    calls = _run_runner(monkeypatch, _Generator(result=result))
    assert [name for name, _ in calls] == ["complete"]
    kwargs = calls[0][1]
    assert kwargs["provider_call_id"] == "c" * 128
    assert kwargs["model_id"] == "m" * 256
    assert kwargs["model_revision"] == "r" * 128


def test_blank_generator_provenance_falls_back_to_the_unassigned_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = StoryGenerationResult(valid_story(), "  ", "", " ")
    calls = _run_runner(monkeypatch, _Generator(result=result))
    kwargs = calls[0][1]
    assert kwargs["provider_call_id"] == "unassigned"
    assert kwargs["model_id"] == generation_module.STORY_REWRITE_MODEL_ID
    assert kwargs["model_revision"] == generation_module.STORY_REWRITE_MODEL_REVISION


# ------------------------------------------------------------------------- the reservation
class _Rows:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def mappings(self) -> _Rows:
        return self

    def all(self) -> list[Any]:
        return self._rows


class _Session:
    def __init__(self, revisions: list[dict[str, Any]], rowcount: int = 1) -> None:
        self.revisions = revisions
        self.rowcount = rowcount
        self.statements: list[Any] = []
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> Any:
        self.statements.append(statement)
        table = getattr(getattr(statement, "table", None), "name", "")
        if table:
            return SimpleNamespace(rowcount=self.rowcount)
        return _Rows(self.revisions)

    def scalar(self, *_args: Any, **_kwargs: Any) -> Any:
        return "rev-2"

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def writes_to(self, table: str) -> list[Any]:
        return [
            statement
            for statement in self.statements
            if getattr(getattr(statement, "table", None), "name", "") == table
        ]


def _params(statement: Any) -> dict[str, Any]:
    dialect: Any = postgresql.dialect
    return dict(statement.compile(dialect=dialect()).params)


def _revision(number: int, status: str = "DRAFT") -> dict[str, Any]:
    return {
        "story_revision_id": f"rev-{number}",
        "revision_no": number,
        "status": status,
        "story_sha256": HASH if status in {"DRAFT", "SUPERSEDED"} else None,
    }


def _repository(
    monkeypatch: pytest.MonkeyPatch,
    *,
    revisions: list[dict[str, Any]],
    run_state: str = "SCRIPT_REVIEW",
    receipt: Any = None,
    basis_error: ParentStoryRunError | None = None,
    attempts: int = 0,
    rowcount: int = 1,
) -> tuple[SqlParentStoryRunRepository, _Session, dict[str, Any]]:
    session = _Session(revisions, rowcount)
    repository = SqlParentStoryRunRepository(session)  # type: ignore[arg-type]
    stored: dict[str, Any] = {}
    run = {
        "run_id": RUN_ID,
        "run_state": run_state,
        "revision": 7,
        "version": 9,
        "understanding_revision": 1,
        "subject_label": "rồng",
        "active_owner_parent_account_id": "parent-account-1",
        "actor_scope_ref": "scope-1",
    }
    monkeypatch.setattr(repository, "_owned_run", lambda *_args, **_kwargs: dict(run))
    # T-2d-fix D2: the accepted attempts of the slot come from the stored receipts
    monkeypatch.setattr(repository, "_rewrite_attempts_used", lambda *_args, **_kwargs: attempts)
    monkeypatch.setattr(repository, "_lock_idempotency", lambda **_kwargs: None)
    monkeypatch.setattr(repository, "_find_idempotency_receipt", lambda **_kwargs: receipt)
    monkeypatch.setattr(
        repository, "_store_idempotency_receipt", lambda **kwargs: stored.update(kwargs) or "r-1"
    )

    def basis(**_kwargs: Any) -> Any:
        if basis_error is not None:
            raise basis_error
        input_row = {
            "original_sha256": HASH,
            "context_revision": 1,
            "context_snapshot": {"age_months": 60},
        }
        return {}, input_row, "một ý tưởng", ["đôi cánh"]

    monkeypatch.setattr(repository, "_story_generation_basis", basis)
    return repository, session, stored


def _reserve(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    values: dict[str, Any] = {
        "principal": PRINCIPAL,
        "run_id": RUN_ID,
        "idempotency_key": "rewrite-1",
        "expected_story_revision": 1,
        "expected_story_sha256": None,
        "hint": None,
        "story_revision_id": "rev-new",
        "model_id": "story-generator-port",
        "model_revision": "unassigned",
        "prompt_version": STORY_REWRITE_PROMPT_VERSION,
        "instruction_version": REWRITE_NEUTRAL_INSTRUCTION_VERSION,
        "instruction": REWRITE_NEUTRAL_INSTRUCTION_V1,
    }
    values.update(overrides)
    return repository.reserve_story_rewrite(**values)


def test_a_fresh_rewrite_stores_a_final_202_receipt_and_no_pending_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, stored = _repository(monkeypatch, revisions=[_revision(1)])
    outcome = _reserve(repository, hint=HINT)
    assert (outcome.story_revision_no, outcome.run_revision, outcome.run_state) == (
        2,
        8,
        "SCRIPT_GENERATING",
    )
    assert outcome.replayed is False and outcome.lifecycle is None
    # the receipt is final in the reservation transaction: status 202 and the accepted body
    assert stored["operation"] == "GENERATE_STORY_REVISION" and stored["response_status"] == 202
    assert stored["response_body"] == {
        "story_revision_no": 2,
        "story_revision_id": "rev-new",
        "run_revision": 8,
        "run_state": "SCRIPT_GENERATING",
    }
    assert stored["scope_kind"] == "STORY_RUN" and stored["scope_ref"] == RUN_ID
    reservation = outcome.reservation
    assert reservation.receipt_id is None  # complete and fail touch no receipt
    # the hint is data in its own field; the instruction is the server constant
    worker_input = reservation.worker_input
    assert worker_input["adult_rewrite_hint"] == HINT
    assert worker_input["rewrite_instruction"] == REWRITE_NEUTRAL_INSTRUCTION_V1
    assert worker_input["rewrite_instruction_version"] == "rewrite-neutral.v1"
    assert HINT not in worker_input["rewrite_instruction"]
    assert worker_input["schema_version"] == "sketch2life.story-rewrite-input.v1"
    assert worker_input["confirmed_subject"] == "rồng"
    assert worker_input["adult_confirmed_idea"] == "một ý tưởng"
    # T-2d-fix D3: the previous draft is left alone until the new one completes; the new one
    # generates and the run is queued
    revisions = session.writes_to("story_revisions")
    assert [statement.__class__.__name__ for statement in revisions] == ["Insert"]
    inserted = _params(revisions[0])
    assert (inserted["revision_no"], inserted["status"]) == (2, "GENERATING")
    run_update = _params(session.writes_to("runs")[0])
    assert (run_update["run_state"], run_update["job_state"], run_update["revision"]) == (
        "SCRIPT_GENERATING",
        "QUEUED",
        8,
    )
    assert session.commits == 1 and session.writes_to("command_receipts") == []


def test_without_a_hint_the_worker_gets_no_hint_and_the_same_constant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _repository(monkeypatch, revisions=[_revision(1)])
    worker_input = _reserve(repository).reservation.worker_input
    assert worker_input["adult_rewrite_hint"] is None
    assert worker_input["rewrite_instruction"] == REWRITE_NEUTRAL_INSTRUCTION_V1


def test_the_fingerprint_binds_the_hint_the_revision_and_the_instruction_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []
    repository, _session, _stored = _repository(monkeypatch, revisions=[_revision(1)])

    def record(**kwargs: Any) -> None:
        seen.append(kwargs["fingerprint"])

    monkeypatch.setattr(repository, "_find_idempotency_receipt", record)
    for overrides in (
        {},
        {},
        {"hint": "other"},
        {"expected_story_revision": 2},  # stale here, which is raised after the fingerprint
        {"expected_story_sha256": HASH},
        {"instruction_version": "rewrite-neutral.v2"},
    ):
        with contextlib.suppress(ParentStoryRunError):
            _reserve(repository, **overrides)
    assert seen[0] == seen[1]
    assert len(set(seen)) == 5 and all(len(value) == 64 for value in seen)


def test_the_limit_is_checked_before_the_stale_comparison(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revisions = [
        _revision(4),
        _revision(3, "SUPERSEDED"),
        _revision(2, "SUPERSEDED"),
        _revision(1, "SUPERSEDED"),
    ]
    repository, _session, _stored = _repository(monkeypatch, revisions=revisions)
    for expected in (4, 1):  # the current revision and a stale one both learn the real reason
        with pytest.raises(ParentStoryRunError) as refused:
            _reserve(repository, expected_story_revision=expected)
        assert (refused.value.status_code, refused.value.code) == (
            409,
            "STORY_REWRITE_LIMIT_REACHED",
        )


@pytest.mark.parametrize(("attempts", "accepted"), [(0, True), (2, True), (3, False), (7, False)])
def test_a_failed_attempt_gives_its_slot_back_up_to_three_attempts(
    monkeypatch: pytest.MonkeyPatch, attempts: int, accepted: bool
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(1)], attempts=attempts
    )
    if accepted:
        assert _reserve(repository).reservation.revision_no == 2
        return
    with pytest.raises(ParentStoryRunError) as refused:
        _reserve(repository)
    assert (refused.value.status_code, refused.value.code) == (409, "STORY_REWRITE_LIMIT_REACHED")
    assert session.writes_to("story_revisions") == [] and session.writes_to("runs") == []


def test_a_stale_revision_or_hash_carries_the_latest_revision_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _repository(
        monkeypatch,
        revisions=[_revision(3), _revision(2, "SUPERSEDED"), _revision(1, "SUPERSEDED")],
    )
    with pytest.raises(ParentStoryRunError) as stale:
        _reserve(repository, expected_story_revision=2)
    assert (stale.value.status_code, stale.value.code, stale.value.current_version) == (
        409,
        "STALE_REVISION",
        3,
    )
    with pytest.raises(ParentStoryRunError) as wrong_hash:
        _reserve(repository, expected_story_revision=3, expected_story_sha256="b" * 64)
    assert (wrong_hash.value.code, wrong_hash.value.current_version) == ("STALE_REVISION", 3)
    assert _reserve(repository, expected_story_revision=3, expected_story_sha256=HASH)


@pytest.mark.parametrize(
    "state", ["PREPARATION_REVIEW", "SCRIPT_GENERATING", "SUBJECT_REVIEW", "FAILED"]
)
def test_only_a_run_in_script_review_can_be_rewritten(
    monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(1)], run_state=state
    )
    with pytest.raises(ParentStoryRunError) as refused:
        _reserve(repository)
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert session.statements == []


def test_a_run_without_a_first_story_cannot_be_rewritten(monkeypatch: pytest.MonkeyPatch) -> None:
    repository, _session, _stored = _repository(monkeypatch, revisions=[])
    with pytest.raises(ParentStoryRunError) as refused:
        _reserve(repository)
    assert refused.value.code == "INVALID_STATE_TRANSITION"


def test_the_gate_errors_of_the_first_story_surface_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for error in (
        ParentStoryRunError(422, "SUBJECT_NOT_CONFIRMED"),
        ParentStoryRunError(422, "PROFILE_CONTEXT_NOT_CONFIRMED"),
        ParentStoryRunError(422, "TRANSCRIPT_NOT_CONFIRMED"),
    ):
        repository, session, _stored = _repository(
            monkeypatch, revisions=[_revision(1)], basis_error=error
        )
        with pytest.raises(ParentStoryRunError) as refused:
            _reserve(repository)
        assert (refused.value.status_code, refused.value.code) == (422, error.code)
        assert session.writes_to("story_revisions") == [] and session.writes_to("runs") == []


def test_the_replay_returns_the_stored_202_without_a_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = {
        "state": "FINAL",
        "response_status": 202,
        "response_body": {
            "story_revision_no": 2,
            "story_revision_id": "rev-new",
            "run_revision": 8,
            "run_state": "SCRIPT_GENERATING",
        },
    }
    # the run is still generating (the lost-202 retry) and later it is in review: same answer
    for state in ("SCRIPT_GENERATING", "SCRIPT_REVIEW"):
        repository, session, stored = _repository(
            monkeypatch, revisions=[_revision(2)], run_state=state, receipt=receipt
        )
        outcome = _reserve(repository)
        assert outcome.replayed is True and outcome.reservation is None
        assert (outcome.story_revision_no, outcome.run_revision, outcome.run_state) == (
            2,
            8,
            "SCRIPT_GENERATING",
        )
        assert stored == {} and session.statements == []


def test_a_pending_receipt_is_never_replayed_as_an_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    repository, _session, _stored = _repository(
        monkeypatch,
        revisions=[_revision(1)],
        receipt={"state": "PENDING", "response_status": None, "response_body": None},
    )
    with pytest.raises(ParentStoryRunError) as refused:
        _reserve(repository)
    assert refused.value.status_code == 503


def test_a_replay_of_a_purged_run_is_the_projection_and_a_fresh_command_is_a_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _repository(
        monkeypatch,
        revisions=[_revision(1)],
        run_state="DELETE_PENDING",
        receipt={"state": "FINAL", "response_status": 202, "response_body": {}},
    )
    monkeypatch.setattr(
        "sketch2life.infrastructure.persistence.parent_story_repository._projection",
        lambda run: ParentStoryLifecycleRecord(
            RUN_ID, str(run["run_state"]), 7, 9, "req", "PENDING"
        ),
    )
    outcome = _reserve(repository)
    assert outcome.replayed is True and outcome.lifecycle is not None
    assert outcome.lifecycle.run_state == "DELETE_PENDING"
    fresh, _s, _st = _repository(monkeypatch, revisions=[_revision(1)], run_state="DELETED")
    with pytest.raises(ParentStoryRunError) as refused:
        _reserve(fresh)
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")


def test_completing_and_failing_a_rewrite_touch_no_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(2, "GENERATING")], run_state="SCRIPT_GENERATING"
    )
    monkeypatch.setattr(repository, "get_run", lambda **_kwargs: _record())
    normalized, digest = normalize_story_output(valid_story(), confirmed_subject="rồng")
    repository.complete_story_revision(
        reservation=_reservation(None),
        principal=PRINCIPAL,
        story=normalized,
        story_sha256=digest,
        provider_call_id="call-1",
        model_id="m",
        model_revision="r",
    )
    repository.fail_story_revision(
        principal=PRINCIPAL,
        reservation=_reservation(None),
        error_code="STORY_GENERATION_UNAVAILABLE",
        outcome_unknown=False,
    )
    assert session.writes_to("command_receipts") == []
    assert session.commits == 2
    # the previous draft is superseded by a compare-and-set when the rewrite completes (D3)
    completion = session.writes_to("story_revisions")
    assert [statement.__class__.__name__ for statement in completion] == [
        "Update",
        "Update",
        "Delete",
    ]
    assert _params(completion[0])["status"] == "DRAFT"
    assert _params(completion[1])["status"] == "SUPERSEDED"
    # T-2d-fix D1: a known failure of a rewrite deletes its own row (the previous story is the
    # last one left), returns the run to review with a safe code, and leaves one audit row
    run_failure = _params(session.writes_to("runs")[-1])
    assert (run_failure["run_state"], run_failure["job_state"]) == ("SCRIPT_REVIEW", "FAILED")
    assert run_failure["retryable"] is True
    assert run_failure["error_code"] == "STORY_GENERATION_UNAVAILABLE"
    audit = _params(session.writes_to("core_audit_entries")[-1])
    assert audit["action"] == "STORY_REWRITE_ATTEMPT_FAILED"
    assert audit["decision"] == "STORY_GENERATION_UNAVAILABLE" and audit["resource_id"] == RUN_ID
    assert audit["owner_scope_kind"] == "PARENT_ACCOUNT" and audit["organization_id"] is None
    # a pending receipt of the legacy route is still finalized
    legacy, legacy_session, _s = _repository(
        monkeypatch, revisions=[_revision(2, "GENERATING")], run_state="SCRIPT_GENERATING"
    )
    monkeypatch.setattr(legacy, "get_run", lambda **_kwargs: _record())
    legacy.complete_story_revision(
        reservation=_reservation("receipt-1"),
        principal=PRINCIPAL,
        story=normalized,
        story_sha256=digest,
        provider_call_id="call-1",
        model_id="m",
        model_revision="r",
    )
    assert len(legacy_session.writes_to("command_receipts")) == 1


def _fail(
    repository: SqlParentStoryRunRepository, *, unknown: bool = False, legacy: bool = False
) -> Any:
    return repository.fail_story_revision(
        principal=PRINCIPAL,
        reservation=_reservation("receipt-1" if legacy else None),
        error_code="STORY_GENERATION_UNAVAILABLE",
        outcome_unknown=unknown,
    )


@pytest.mark.parametrize("run_state", ["SCRIPT_REVIEW", "FAILED", "SCRIPT_GENERATION_UNKNOWN"])
@pytest.mark.parametrize("unknown", [False, True])
def test_a_late_failure_after_the_run_left_script_generating_changes_nothing(
    monkeypatch: pytest.MonkeyPatch, run_state: str, unknown: bool
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(2, "GENERATING")], run_state=run_state
    )
    with pytest.raises(ParentStoryRunError) as refused:
        _fail(repository, unknown=unknown)
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert session.statements == [] and session.commits == 0 and session.rollbacks == 1


@pytest.mark.parametrize(
    ("unknown", "legacy"), [(False, False), (True, False), (False, True), (True, True)]
)
def test_a_failure_whose_revision_row_is_gone_rolls_back_and_changes_nothing(
    monkeypatch: pytest.MonkeyPatch, unknown: bool, legacy: bool
) -> None:
    repository, session, _stored = _repository(
        monkeypatch,
        revisions=[_revision(2, "GENERATING")],
        run_state="SCRIPT_GENERATING",
        rowcount=0,
    )
    with pytest.raises(ParentStoryRunError) as refused:
        _fail(repository, unknown=unknown, legacy=legacy)
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert session.commits == 0 and session.rollbacks == 1


def test_a_known_failure_of_a_first_story_or_the_legacy_route_still_ends_the_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(2, "GENERATING")], run_state="SCRIPT_GENERATING"
    )
    _fail(repository, legacy=True)
    revision = _params(session.writes_to("story_revisions")[-1])
    assert revision["status"] == "FAILED"
    run_update = _params(session.writes_to("runs")[-1])
    assert (run_update["run_state"], run_update["job_state"]) == ("FAILED", "FAILED")
    assert run_update["retryable"] is False and run_update["active_owner_parent_account_id"] is None
    assert run_update["finished_at"] is not None and run_update["adult_wait_started_at"] is None
    assert len(session.writes_to("command_receipts")) == 1 and session.commits == 1


def test_an_unknown_outcome_keeps_the_attempt_for_reconciliation_and_the_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(2, "GENERATING")], run_state="SCRIPT_GENERATING"
    )
    _fail(repository, unknown=True)
    assert _params(session.writes_to("story_revisions")[-1])["status"] == "AWAITING_RECONCILIATION"
    run_update = _params(session.writes_to("runs")[-1])
    assert run_update["run_state"] == "SCRIPT_GENERATION_UNKNOWN"
    assert run_update["active_owner_parent_account_id"] == "parent-account-1"
    assert "finished_at" not in run_update and session.writes_to("core_audit_entries") == []


@pytest.mark.parametrize("run_state", ["SCRIPT_REVIEW", "FAILED", "SCRIPT_GENERATION_UNKNOWN"])
def test_a_late_completion_after_the_run_left_script_generating_changes_nothing(
    monkeypatch: pytest.MonkeyPatch, run_state: str
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(2, "GENERATING")], run_state=run_state
    )
    normalized, digest = normalize_story_output(valid_story(), confirmed_subject="rồng")
    with pytest.raises(ParentStoryRunError) as refused:
        repository.complete_story_revision(
            reservation=_reservation(None),
            principal=PRINCIPAL,
            story=normalized,
            story_sha256=digest,
            provider_call_id="call-1",
            model_id="m",
            model_revision="r",
        )
    assert refused.value.code == "INVALID_STATE_TRANSITION"
    assert session.statements == [] and session.commits == 0


def test_the_previous_story_must_still_be_reviewable_when_a_rewrite_completes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, _stored = _repository(
        monkeypatch, revisions=[_revision(2, "GENERATING")], run_state="SCRIPT_GENERATING"
    )
    normalized, digest = normalize_story_output(valid_story(), confirmed_subject="rồng")
    # every compare-and-set after the first reports a miss: the supersede of revision 1
    results = iter([1, 0])
    original = session.execute

    def execute(statement: Any, *args: Any, **kwargs: Any) -> Any:
        result = original(statement, *args, **kwargs)
        if getattr(getattr(statement, "table", None), "name", "") == "story_revisions":
            return SimpleNamespace(rowcount=next(results, 1))
        return result

    session.execute = execute  # type: ignore[method-assign]
    with pytest.raises(ParentStoryRunError) as refused:
        repository.complete_story_revision(
            reservation=_reservation(None),
            principal=PRINCIPAL,
            story=normalized,
            story_sha256=digest,
            provider_call_id="call-1",
            model_id="m",
            model_revision="r",
        )
    assert refused.value.code == "INVALID_STATE_TRANSITION"
    assert session.commits == 0 and session.rollbacks >= 1


# ------------------------------------------------------------------------- subject confirmation
def _subject_repository(
    monkeypatch: pytest.MonkeyPatch,
    *,
    run_state: str = "SUBJECT_REVIEW",
    receipt: Any = None,
    suggested: str = "rồng",
    latest_revision: int = 1,
) -> tuple[SqlParentStoryRunRepository, _Session, dict[str, Any]]:
    repository, session, stored = _repository(
        monkeypatch, revisions=[], run_state=run_state, receipt=receipt
    )
    monkeypatch.setattr(
        repository,
        "_latest_understanding",
        lambda _run_id: {
            "revision_no": latest_revision,
            "run_input_id": "input-1",
            "confidence": 0.9,
            "raw_body_sha256": None,
            "result_snapshot": {
                "result": {"candidate_subject": suggested, "visible_features": ["a"]}
            },
        },
    )
    return repository, session, stored


def _confirm(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    values: dict[str, Any] = {
        "principal": PRINCIPAL,
        "run_id": RUN_ID,
        "expected_understanding_revision": 1,
        "confirmed_subject": "rồng",
        "idempotency_key": "subject-1",
    }
    values.update(overrides)
    return repository.confirm_subject(**values)


def test_a_plain_confirmation_stores_a_202_receipt_with_the_run_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, stored = _subject_repository(monkeypatch)
    outcome = _confirm(repository, rerun_on_edit=True)
    assert (outcome.decision, outcome.understanding_revision, outcome.run_revision) == (
        "CONFIRMED",
        1,
        8,
    )
    assert outcome.input_revision is None and outcome.replayed is False
    assert stored["response_status"] == 202
    assert stored["response_body"] == {
        "decision": "CONFIRMED",
        "understanding_revision": 1,
        "run_revision": 8,
    }
    run_update = _params(session.writes_to("runs")[0])
    assert (
        run_update["run_state"] == "PREPARATION_REVIEW" and run_update["job_state"] == "SUCCEEDED"
    )
    assert len(session.writes_to("review_decisions")) == 1


def test_an_edit_with_the_rerun_queues_the_vlm_and_writes_no_decision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, stored = _subject_repository(monkeypatch)
    outcome = _confirm_with_input(repository, confirmed_subject="chú rồng lửa", rerun_on_edit=True)
    assert (outcome.decision, outcome.understanding_revision, outcome.run_revision) == (
        "RERUN_REQUESTED",
        1,
        8,
    )
    assert outcome.input_revision == 3
    assert stored["response_status"] == 202
    assert stored["response_body"] == {
        "decision": "RERUN_REQUESTED",
        "understanding_revision": 1,
        "run_revision": 8,
        "subject_hint": "chú rồng lửa",
    }
    run_update = _params(session.writes_to("runs")[0])
    assert (run_update["run_state"], run_update["job_state"], run_update["revision"]) == (
        "INPUT_PROCESSING",
        "QUEUED",
        8,
    )
    assert session.writes_to("review_decisions") == []
    assert session.writes_to("understanding_revisions") == []


def _confirm_with_input(repository: SqlParentStoryRunRepository, **overrides: Any) -> Any:
    original = repository._owned_run
    repository._owned_run = lambda *a, **k: {**original(*a, **k), "current_input_revision": 3}  # type: ignore[method-assign]
    return _confirm(repository, **overrides)


def test_an_edit_without_the_rerun_is_recorded_and_confirmed_at_once_dev_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, session, stored = _subject_repository(monkeypatch)
    outcome = _confirm(repository, confirmed_subject="chú rồng lửa", rerun_on_edit=False)
    assert (outcome.decision, outcome.understanding_revision, outcome.run_revision) == (
        "CONFIRMED",
        2,
        8,
    )
    assert stored["response_body"]["understanding_revision"] == 2
    revision = _params(session.writes_to("understanding_revisions")[0])
    assert revision["revision_no"] == 2 and revision["subject_label"] == "chú rồng lửa"
    assert len(session.writes_to("review_decisions")) == 1
    assert _params(session.writes_to("runs")[0])["run_state"] == "PREPARATION_REVIEW"


def test_a_stale_understanding_revision_carries_the_latest_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _session, _stored = _subject_repository(monkeypatch, latest_revision=3)
    with pytest.raises(ParentStoryRunError) as stale:
        _confirm(repository, expected_understanding_revision=2)
    assert (stale.value.status_code, stale.value.code, stale.value.current_version) == (
        409,
        "STALE_REVISION",
        3,
    )


@pytest.mark.parametrize("state", ["INPUT_PROCESSING", "INPUT_REVIEW", "PREPARATION_REVIEW"])
def test_only_a_run_in_subject_review_can_confirm_the_subject(
    monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    repository, session, _stored = _subject_repository(monkeypatch, run_state=state)
    with pytest.raises(ParentStoryRunError) as refused:
        _confirm(repository)
    assert (refused.value.status_code, refused.value.code) == (409, "INVALID_STATE_TRANSITION")
    assert session.statements == []


def test_the_replay_answers_the_stored_decision_and_run_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = {
        "response_body": {
            "decision": "RERUN_REQUESTED",
            "understanding_revision": 1,
            "run_revision": 8,
            "subject_hint": "chú rồng lửa",
        }
    }
    repository, session, stored = _subject_repository(
        monkeypatch, run_state="INPUT_PROCESSING", receipt=receipt
    )
    outcome = _confirm(repository, confirmed_subject="chú rồng lửa")
    assert (outcome.decision, outcome.understanding_revision, outcome.run_revision) == (
        "RERUN_REQUESTED",
        1,
        8,
    )
    assert outcome.replayed is True and outcome.input_revision is None
    assert stored == {} and session.statements == []


def test_a_receipt_written_before_t_2d_replays_with_the_current_run_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = {"response_body": {"decision": "CONFIRMED", "understanding_revision": 2}}
    repository, _session, _stored = _subject_repository(
        monkeypatch, run_state="PREPARATION_REVIEW", receipt=receipt
    )
    outcome = _confirm(repository)
    assert (outcome.decision, outcome.understanding_revision, outcome.run_revision) == (
        "CONFIRMED",
        2,
        7,
    )
    assert outcome.replayed is True
