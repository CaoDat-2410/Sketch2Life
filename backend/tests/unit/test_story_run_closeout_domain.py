"""FEAT-066 T-1d1: the pure closeout rules over every state (SRS l.394-395, l.503 FR-C-11)."""

from __future__ import annotations

import ast
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from sketch2life.application.ports.story_run_lifecycle import (
    DELETE_ELIGIBLE_STATES,
    PUBLIC_RUN_STATES,
    PURGE_STATES,
)
from sketch2life.domain import story_run_closeout
from sketch2life.domain.story_run_closeout import (
    ABANDONING_WAIT_STATES,
    ACTIVE_JOB_STATES,
    ADULT_WAIT_STATES,
    CLOSEOUT_TRANSITIONS,
    COMPLETING_WAIT_STATES,
    GENERATION_DEADLINE,
    IDLE_CLOSEOUT,
    generation_deadline_at,
    generation_deadline_due,
    idle_closeout_due,
    idle_since,
    idle_target,
)
from sketch2life.domain.story_video import model as story_video_model
from sketch2life.domain.story_video.model import VIDEO_RUN_STATES

NOW = datetime(2026, 11, 19, 12, 0, tzinfo=UTC)
JOB_STATES = (
    None,
    "QUEUED",
    "RUNNING",
    "RETRY_WAIT",
    "SUCCEEDED",
    "FAILED",
    "AWAITING_RECONCILIATION",
)

# SRS l.394: the states that wait for the adult, and l.503: how each ends.
EXPECTED = {
    "DRAFT": "ABANDONED",
    "INPUT_REVIEW": "ABANDONED",
    "SUBJECT_REVIEW": "ABANDONED",
    "PREPARATION_REVIEW": "ABANDONED",
    "SCRIPT_REVIEW": "ABANDONED",
    "SAFETY_BLOCKED": "ABANDONED",
    "VIDEO_READY": "COMPLETED",
}


def test_the_constants_follow_the_srs() -> None:
    assert timedelta(hours=168) == IDLE_CLOSEOUT
    assert timedelta(hours=6) == GENERATION_DEADLINE
    assert {"VIDEO_READY"} == COMPLETING_WAIT_STATES
    assert set(EXPECTED) == COMPLETING_WAIT_STATES | ABANDONING_WAIT_STATES
    assert CLOSEOUT_TRANSITIONS["INPUT_PROCESSING"] == "ABANDONED"
    assert set(EXPECTED) | {"INPUT_PROCESSING"} == ADULT_WAIT_STATES
    # SRS l.394: no idle closeout while QUEUED, RUNNING, RETRY_WAIT or AWAITING_RECONCILIATION
    assert {"QUEUED", "RUNNING", "RETRY_WAIT", "AWAITING_RECONCILIATION"} == ACTIVE_JOB_STATES


@pytest.mark.parametrize("state", PUBLIC_RUN_STATES)
@pytest.mark.parametrize("job_state", JOB_STATES)
def test_idle_target_over_every_state_and_job_state(state: str, job_state: str | None) -> None:
    target = idle_target(state, job_state)
    if state in EXPECTED and job_state not in ACTIVE_JOB_STATES:
        assert target == EXPECTED[state]
    elif state == "INPUT_PROCESSING" and job_state is None:
        assert target == "ABANDONED"  # nothing attached yet: the draft of the SRS
    else:
        assert target is None


@pytest.mark.parametrize("state", PUBLIC_RUN_STATES)
def test_system_work_and_closed_states_are_never_closed(state: str) -> None:
    if state in ADULT_WAIT_STATES:
        return
    # in-flight AI work, admission pending, and every closed or purged state
    assert idle_target(state, None) is None
    assert idle_target(state, "SUCCEEDED") is None
    assert state in (
        {
            "STORY_GENERATING",
            "SCRIPT_GENERATING",
            "SCRIPT_GENERATION_UNKNOWN",
            "VIDEO_ADMISSION_PENDING",
            "VIDEO_QUEUED",
            "VIDEO_GENERATING",
            "VIDEO_SAFETY_VALIDATING",
        }
        | DELETE_ELIGIBLE_STATES
        | PURGE_STATES
    )


def test_admission_pending_never_arms_the_timer() -> None:
    assert idle_target("VIDEO_ADMISSION_PENDING", None) is None
    assert "VIDEO_ADMISSION_PENDING" not in ADULT_WAIT_STATES


def test_video_states_are_split_between_wait_and_system_work() -> None:
    waiting = {state for state in VIDEO_RUN_STATES if state in ADULT_WAIT_STATES}
    assert waiting == {"VIDEO_READY", "SAFETY_BLOCKED"}


def test_input_processing_with_a_job_or_a_pending_transcript_is_ai_work() -> None:
    assert idle_target("INPUT_PROCESSING", None) == "ABANDONED"
    assert idle_target("INPUT_PROCESSING", None, transcript_pending=True) is None
    for job_state in (
        "QUEUED",
        "RUNNING",
        "RETRY_WAIT",
        "AWAITING_RECONCILIATION",
        "SUCCEEDED",
        "FAILED",
    ):
        assert idle_target("INPUT_PROCESSING", job_state) is None


def test_a_pending_transcript_does_not_hold_back_a_review_state() -> None:
    assert idle_target("SCRIPT_REVIEW", "SUCCEEDED", transcript_pending=True) == "ABANDONED"


def test_idle_since_is_the_latest_marker_and_ignores_missing_ones() -> None:
    earlier = NOW - timedelta(days=9)
    middle = NOW - timedelta(days=5)
    assert idle_since(earlier, None, None) == earlier
    assert idle_since(earlier, middle, None) == middle
    assert idle_since(earlier, None, middle) == middle
    assert idle_since(middle, earlier, earlier) == middle
    assert idle_since(earlier, middle, NOW) == NOW


def test_the_closeout_is_due_at_exactly_168_hours() -> None:
    since = NOW
    assert not idle_closeout_due(since, since + timedelta(hours=168) - timedelta(seconds=1))
    assert idle_closeout_due(since, since + timedelta(hours=168))
    assert idle_closeout_due(since, since + timedelta(hours=169))


def test_the_generation_deadline_runs_from_accepted_at() -> None:
    accepted = NOW
    assert generation_deadline_at(accepted) == accepted + timedelta(hours=6)
    assert not generation_deadline_due(accepted, accepted + timedelta(hours=6, seconds=-1))
    assert generation_deadline_due(accepted, accepted + timedelta(hours=6))


def test_the_deadline_code_is_defined_once() -> None:
    assert story_run_closeout.VIDEO_DEADLINE_EXCEEDED is story_video_model.VIDEO_DEADLINE_EXCEEDED
    assert story_run_closeout.VIDEO_DEADLINE_EXCEEDED in story_video_model.PUBLIC_FAILURE_CODES


def test_retry_wait_is_ai_work_in_every_wait_state() -> None:
    for state in sorted(ABANDONING_WAIT_STATES | COMPLETING_WAIT_STATES):
        assert idle_target(state, "RETRY_WAIT") is None, state


# ---------------------------------------------------------------- every writer of ``story.runs``
SRC = Path(__file__).resolve().parents[2] / "src" / "sketch2life"
# The modules that write ``story.runs`` and how many ``update(story_runs)`` sites each holds (T-1d1
# listed one module; T-1d1-fix scans all of them). A new writer or a new site fails this pin until
# someone has read it: a run write that does not move ``updated_at`` lets the closeout come early.
WRITER_SITES = {
    "infrastructure/persistence/parent_story_repository.py": 22,
    # FEAT-066 goal v4 T-2e-a: the implicit first-story start moves the run to SCRIPT_GENERATING.
    "infrastructure/persistence/story_first_start.py": 1,
    "infrastructure/story_run_lite/repository.py": 12,
    "infrastructure/story_video/repository.py": 5,
    "infrastructure/persistence/story_task_reaper_store.py": 3,
    "infrastructure/persistence/story_lifecycle_store.py": 3,
    "infrastructure/story_video/closeout_store.py": 1,
}
# (module, function) writes that need not set ``updated_at``, each with the audit that licenses it.
EXEMPT_WRITES = {
    # only recomputes ``run_state``; every caller (l.1469, 1542, 2766, 3212, 3515, 3668 at the
    # T-1d1-fix commit) runs it in the transaction of a writer that set ``updated_at``
    ("infrastructure/persistence/parent_story_repository.py", "_apply_settle"),
    # the purge writes: the run is already in a purge state, which is never closable
    ("infrastructure/persistence/story_lifecycle_store.py", "purge_story_content"),
    ("infrastructure/persistence/story_lifecycle_store.py", "_delete_children"),
}


def _run_table_names(tree: ast.AST) -> set[str]:
    names = {"story_runs"}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and ast.unparse(node.value).endswith("story_runs")
        ):
            names.add(node.targets[0].id)
        if isinstance(node, ast.ImportFrom):
            names.update(
                alias.asname or alias.name for alias in node.names if alias.name == "story_runs"
            )
    return names


def _run_update_sites(path: Path) -> list[tuple[ast.Call, ast.Call | None, str, str]]:
    """Each ``update(<runs table>)``: the call, its ``.values(...)`` call, the function name and
    the function source."""

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    names = _run_table_names(tree)
    sites: list[tuple[ast.Call, ast.Call | None, str, str]] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "update"
            and node.args
            and ast.unparse(node.args[0]).split(".")[-1] in names
        ):
            continue
        values: ast.Call | None = None
        current: ast.AST = node
        while current in parents:
            parent = parents[current]
            if (
                isinstance(parent, ast.Attribute)
                and parent.attr == "values"
                and isinstance(parents.get(parent), ast.Call)
            ):
                values = parents[parent]  # type: ignore[assignment]
                break
            current = parent
        function: ast.AST = node
        while function in parents and not isinstance(
            function, ast.FunctionDef | ast.AsyncFunctionDef
        ):
            function = parents[function]
        sites.append(
            (
                node,
                values,
                getattr(function, "name", ""),
                ast.get_source_segment(source, function) or "",
            )
        )
    return sites


def test_the_writers_of_story_runs_are_the_pinned_seven_modules() -> None:
    found = {
        path.relative_to(SRC).as_posix(): len(sites)
        for path in sorted(SRC.rglob("*.py"))
        if (sites := _run_update_sites(path))
    }
    assert found == WRITER_SITES


def test_every_run_write_in_every_module_bumps_updated_at() -> None:
    """The idle clock of the Parent steps is ``updated_at`` (T-1d1-DEC-2): every writer must move it
    by keyword, or through a ``**spread`` whose function holds the ``"updated_at"`` key."""

    for relative in WRITER_SITES:
        for node, values, function, function_source in _run_update_sites(SRC / relative):
            where = f"{relative}:{node.lineno}"
            assert values is not None, f"{where}: update(story_runs) without values"
            names = {keyword.arg for keyword in values.keywords if keyword.arg is not None}
            if "updated_at" in names or (relative, function) in EXEMPT_WRITES:
                continue
            spread = any(keyword.arg is None for keyword in values.keywords)
            assert spread and '"updated_at"' in function_source, (
                f"{where}: a run write that does not set updated_at"
            )
