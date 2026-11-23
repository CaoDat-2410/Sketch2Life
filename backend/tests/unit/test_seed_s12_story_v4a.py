"""Pure fixture, idempotency, and guard checks for the S12 Story v4a seed stage."""

from __future__ import annotations

import re
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from sketch2life.domain.story_video.model import (
    QUALITY_REASON_CODES,
    is_playable,
    public_failure_code,
)
from tools.seed import data, s12_story_v4a
from tools.seed import s12_story_v4a_data as fixtures
from tools.seed.guard import SeedGuardError
from tools.seed.stage_common import StageError, StageResult, check_database_prefix


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("parent_subjects", [spec.subject for spec in fixtures.PARENT_SPECS]),
        ("run_ids", list(fixtures.RUN_IDS)),
        ("expected_keys", list(fixtures.EXPECTED.keys())),
    ],
)
def test_fixture_identifiers_are_distinct_and_syntactically_valid(
    field: str, value: list[str]
) -> None:
    assert len(value) == len(set(value)), field
    if field == "expected_keys":
        assert all(re.fullmatch(r"[A-Za-z0-9_]+", name) for name in value)


def test_static_bundle_encodes_required_phase_a_shapes_and_synthetic_vietnamese() -> None:
    bundle = fixtures.build_static_fixture_bundle()
    runs_by_id = {row["run_id"]: row for row in bundle["runs"]}

    assert runs_by_id[fixtures.RUN_STARTED_ID]["run_state"] == "PREPARATION_REVIEW"
    assert runs_by_id[fixtures.RUN_STARTED_ID]["active_owner_parent_account_id"] is not None
    assert runs_by_id[fixtures.RUN_SAFETY_BLOCKED_ID]["run_state"] == "SCRIPT_REVIEW"
    assert runs_by_id[fixtures.RUN_SAFETY_BLOCKED_ID]["error_code"] == "SAFETY_BLOCKED"
    assert public_failure_code("SAFETY_BLOCKED") == "VIDEO_SAFETY_BLOCKED"

    completed = runs_by_id[fixtures.RUN_COMPLETED_ID]
    assert completed["run_state"] == "COMPLETED"
    assert completed["active_owner_parent_account_id"] is None
    assert completed["actor_scope_ref"] == data.principal_scope_ref(
        data.SEED_ISSUER, data.PARENT_SUBJECTS[fixtures.REUSED_PARENT_KEY]
    )

    reviews_completed = [
        row
        for row in bundle["story_revision_reviews"]
        if row["run_id"] == fixtures.RUN_COMPLETED_ID
    ]
    assert [row["review_epoch"] for row in reviews_completed] == [1, 2]
    assert len({row["story_revision_id"] for row in reviews_completed}) == 1

    gens_completed = [
        row
        for row in bundle["video_generations"]
        if row["story_run_id"] == fixtures.RUN_COMPLETED_ID
    ]
    assert [(row["generation_no"], row["state"]) for row in gens_completed] == [
        (1, "FAILED"),
        (2, "READY"),
    ]
    ready_gen = gens_completed[1]
    assert ready_gen["quality_reason_code"] in QUALITY_REASON_CODES
    assert is_playable(
        run_state=completed["run_state"],
        generation_state=ready_gen["state"],
        technical=ready_gen["technical_validation_state"],
        consistency=ready_gen["consistency_validation_state"],
        safety=ready_gen["safety_validation_state"],
        has_output=bool(ready_gen["output_asset_ref"]),
        allow_completed=True,
    )


def test_lesson_and_profiles_match_age_band_and_outdoor_rules() -> None:
    profiles, profile_revs = fixtures.parent_profile_rows()
    assert len(profiles) == 2
    assert len(profile_revs) == 2
    for rev in profile_revs:
        assert 36 <= rev["age_months"] <= 71
        assert rev["age_band_ref"] == fixtures.OUTDOOR_AGE_BAND_REF
    assert fixtures.LESSON_CONTENT["locale"] == "vi-VN"
    assert fixtures.LESSON_CONTENT["target_age_band_ref"] == fixtures.OUTDOOR_AGE_BAND_REF
    assert [act["activity_kind"] for act in fixtures.LESSON_ACTIVITIES] == ["outdoor", "outdoor"]


@pytest.mark.parametrize(
    ("second_run", "expected_ok"),
    [
        (False, True),
        (True, True),
    ],
)
def test_run_s12_returns_expected_counts_and_is_idempotent(
    monkeypatch: pytest.MonkeyPatch, second_run: bool, expected_ok: bool
) -> None:
    counts_seq = [
        {key: 0 for key in fixtures.EXPECTED} if not second_run else dict(fixtures.EXPECTED),
        dict(fixtures.EXPECTED),
    ]
    events: list[tuple[str, int]] = []

    class _FakeSelectService:
        def select_activity(
            self,
            *,
            principal: object,
            run_id: str,
            expected_revision: int,
            activity_ref: dict[str, object],
            idempotency_key: str,
        ) -> SimpleNamespace:
            events.append((idempotency_key, expected_revision))
            return SimpleNamespace(
                run_revision=expected_revision + 1,
                context_revision=1,
                context_snapshot_sha256="a" * 64,
            )

    class _FakeRunRepo:
        def get_run(self, *, principal: object, run_id: str) -> SimpleNamespace:
            return SimpleNamespace(
                run_revision=1,
                context_revision=1,
                context_snapshot_sha256="a" * 64,
            )

        def confirm_context(
            self,
            *,
            principal: object,
            run_id: str,
            expected_context_revision: int,
            expected_context_snapshot_sha256: str,
            idempotency_key: str,
        ) -> SimpleNamespace:
            events.append((idempotency_key, expected_context_revision))
            return SimpleNamespace(run_revision=4)

    class _FakeSession:
        def __enter__(self) -> _FakeSession:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(s12_story_v4a, "_require_prerequisites", lambda _conn: None)
    monkeypatch.setattr(s12_story_v4a, "count_s12_rows", lambda _conn: counts_seq.pop(0))
    monkeypatch.setattr(s12_story_v4a, "_seed_static_rows", lambda _engine: None)
    monkeypatch.setattr(
        s12_story_v4a, "create_core_session_factory", lambda _engine: lambda: _FakeSession()
    )

    fake_engine = MagicMock()
    result = s12_story_v4a.run_s12(
        fake_engine,
        selection_factory=lambda _sess: _FakeSelectService(),  # type: ignore[arg-type, return-value]
        run_repo_factory=lambda _sess: _FakeRunRepo(),  # type: ignore[arg-type, return-value]
    )

    assert isinstance(result, StageResult)
    assert result.ok is expected_ok
    assert result.after == fixtures.EXPECTED
    assert events == [
        (fixtures.SELECT_STARTED_KEY_1, 1),
        (fixtures.SELECT_STARTED_KEY_2, 2),
        (fixtures.CONFIRM_CONTEXT_STARTED_KEY, 1),
    ]


@pytest.mark.parametrize(
    ("env_url", "expected_message"),
    [
        ("postgresql+psycopg://postgres:pass@127.0.0.1:5432/sketch2life_m2_s1a", "contain 'seed'"),
        ("postgresql+psycopg://postgres:pass@127.0.0.1:5435/seed_other", "frc08_"),
        ("", "S2L_SEED_DATABASE_URL is not set"),
    ],
)
def test_database_prefix_and_guard_refuse_wrong_target(
    env_url: str, expected_message: str
) -> None:
    environ = {"S2L_SEED_DATABASE_URL": env_url} if env_url else {}
    with pytest.raises(SeedGuardError) as exc_info:
        check_database_prefix(environ)
    assert expected_message in str(exc_info.value)


def test_main_prints_counts_only_and_returns_nonzero_on_mismatch(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    bad_result = StageResult(
        name="s12_story_v4a",
        before={key: 0 for key in fixtures.EXPECTED},
        after={key: 0 for key in fixtures.EXPECTED},
        expected=dict(fixtures.EXPECTED),
    )
    monkeypatch.setattr(s12_story_v4a, "run_s12", lambda _engine: bad_result)
    fake_engine = MagicMock()
    monkeypatch.setattr("tools.seed.stage_common.open_guarded_engine", lambda: fake_engine)

    exit_code = s12_story_v4a.main()
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "story_activity_selections" in captured.out
    assert "postgresql" not in captured.out.lower()
    fake_engine.dispose.assert_called_once()


def test_run_s12_raises_stage_error_when_prerequisites_missing() -> None:
    conn = MagicMock()
    conn.scalar.return_value = None
    fake_engine = MagicMock()
    fake_engine.connect.return_value.__enter__.return_value = conn

    with pytest.raises(StageError) as exc_info:
        s12_story_v4a.run_s12(fake_engine)
    assert exc_info.value.code == "S12_PREREQUISITES_MISSING"
