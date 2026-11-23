"""Shared fixtures and helpers of the T-4b3a PostgreSQL modules (Teacher StoryRun input steps).

Not a test module. It builds on the T-4b2 fixtures (``api``, ``flow``, ``post_create``: a synthetic
organization, classes, Teachers, one confirmed child and a Teacher run) and adds what the input
steps need: in-memory object storage, a scanner that knows the synthetic uploads, the deterministic
drawing analyzer, speech transcriber and story generator, and ``seed_first_story``.

**First story (V4-A OPEN-A D1).** The Teacher first story starts by itself when the last of the
subject and context confirmations is given (``FirstStoryStarter``), and the composed
``RecordingGenerator`` answers after the response, so ``to_script_review`` needs no seeding. The
SQL helper ``seed_first_story`` stays for the tests that need a story over a run that never met the
gates (it mirrors the rows ``complete_story_revision`` writes); every later step (the rewrites) is
exercised through the real routes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import insert, select, update
from test_teacher_run_create_postgres import (  # type: ignore[import-not-found]
    Api,
    api,  # noqa: F401 - re-exported fixture
    body_for,
    flow,
    headers,
    post_create,
    run_rows,
)

from sketch2life.application.ports.parent_story_inputs import (
    DrawingAnalysisResult,
    StoryGenerationResult,
)
from sketch2life.application.services.story_output import normalize_story_output
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalTestSignatureMediaValidator,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.story_inputs.drawing import normalize_drawing
from sketch2life.infrastructure.story_inputs.fixtures import (
    FixtureDrawingAnalyzer,
    FixtureSpeechTranscriber,
)
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from tests.integration.test_parent_story_idea_postgres import wav_audio
from tests.integration.test_parent_story_inputs_postgres import (
    AllowlistScanner,
    FaultStorage,
    InMemoryStorage,
    png_bytes,
    sha,
)
from tests.unit.test_story_output import valid_story

__all__ = ["Api", "api", "body_for", "flow", "headers", "post_create", "run_rows"]

SUBJECT = "dragon"
FEATURES = ("green scales", "small wings")
SPEECH = "Con rồng nhỏ chia kẹo cho bạn"
RUNS = story_tables.story_runs
_MASK = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class RecordingGenerator:
    """Answers every worker input with a valid draft and records what it was given.

    ``before`` runs inside ``generate`` (a hook for the late-result tests); ``fail`` makes the next
    calls raise ``StoryGenerationFailure``-style errors through ``error``.
    """

    def __init__(self) -> None:
        self.inputs: list[dict[str, Any]] = []
        self.before: Any = None
        self.error: BaseException | None = None

    def generate(self, worker_input: Any) -> StoryGenerationResult:
        self.inputs.append(dict(worker_input))
        if self.before is not None:
            self.before()
        if self.error is not None:
            raise self.error
        story = valid_story()
        story["title"] = f"Rồng nhỏ lần {len(self.inputs)}"
        return StoryGenerationResult(story, f"call-{len(self.inputs)}", "fixture-model", "1")


@dataclass
class Env:
    api: Api
    storage: FaultStorage
    scanner: AllowlistScanner
    analyzer: FixtureDrawingAnalyzer
    transcriber: FixtureSpeechTranscriber
    generator: RecordingGenerator
    runs: dict[str, str] = field(default_factory=dict)

    def sessions(self) -> Any:
        return self.api.sessions()

    @property
    def d(self) -> Api:
        return self.api


@pytest.fixture
def env(api: Api) -> Env:  # noqa: F811 - the re-exported T-4b2 fixture
    storage = FaultStorage(InMemoryStorage())
    scanner = AllowlistScanner()
    analyzer = FixtureDrawingAnalyzer()
    transcriber = FixtureSpeechTranscriber()
    generator = RecordingGenerator()
    application = api.app
    application.state.lesson_library_storage = storage
    application.state.lesson_document_scanner = scanner
    application.state.upload_media_validator = LocalTestSignatureMediaValidator(env="test")
    application.state.drawing_analyzer = analyzer
    application.state.speech_transcriber = transcriber
    application.state.story_generator = generator
    return Env(api, storage, scanner, analyzer, transcriber, generator)


# ----------------------------------------------------------------------------- wire helpers
def mask(text_body: str) -> str:
    return _MASK.sub("<uuid>", text_body)


def wire(response: Any) -> tuple[int, Any]:
    """Status and body with every id masked: the shape the uniform 404 must share."""
    body = response.json() if response.content else None
    if isinstance(body, dict):
        body = {k: v for k, v in body.items() if k not in {"request_id", "correlation_id"}}
    return response.status_code, body


def who_headers(e: Env, who: str, key: str | None = None, **extra: str) -> dict[str, str]:
    return dict(headers(e.d.subjects[who], key, **extra))


# ----------------------------------------------------------------------------- the flow steps
def new_run(e: Env, who: str = "t1") -> str:
    """A Teacher run created through the real T-4b2 route (child, plan, confirmed selection)."""
    _occ, _offer, body = flow(e.d, who=who)
    response = post_create(e.d, who, body)
    assert response.status_code == 201, response.text
    run_id = str(response.json()["story_run"]["run_id"])
    e.runs[run_id] = who
    return run_id


def upload(
    e: Env, who: str, run_id: str, data: bytes, *, purpose: str = "RUN_ARTWORK", media_type: str
) -> Any:
    e.scanner.clean.add(sha(data))
    return e.d.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": purpose,
            "target_ref": run_id,
            "media_type": media_type,
            "expected_size_bytes": len(data),
            "expected_sha256": sha(data),
        },
        headers=who_headers(e, who, uuid4().hex),
    )


def complete_upload(
    e: Env, who: str, run_id: str, data: bytes, *, purpose: str, media_type: str
) -> str:
    created = upload(e, who, run_id, data, purpose=purpose, media_type=media_type)
    assert created.status_code == 201, created.text
    upload_id = created.json()["upload_id"]
    part = e.d.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/1",
        content=data,
        headers={
            **who_headers(e, who),
            "X-Part-SHA256": sha(data),
            "Content-Type": "application/octet-stream",
        },
    )
    assert part.status_code == 200, part.text
    done = e.d.client.post(
        f"/v1/upload-sessions/{upload_id}/complete",
        json={"expected_size_bytes": len(data), "expected_sha256": sha(data)},
        headers=who_headers(e, who, uuid4().hex),
    )
    assert done.status_code == 202, done.text
    return str(done.json()["asset_ref"])


def drawing_handle(e: Env, who: str, run_id: str, *, seed: int = 0) -> tuple[str, bytes]:
    data = png_bytes(seed=seed)
    handle = complete_upload(e, who, run_id, data, purpose="RUN_ARTWORK", media_type="image/png")
    return handle, data


def register_analysis(
    e: Env,
    data: bytes,
    *,
    subject: str = SUBJECT,
    hint: str | None = None,
    child_count: int = 1,
) -> None:
    derived = normalize_drawing(data, declared_media_type="image/png").sha256
    e.analyzer.register(
        derived,
        DrawingAnalysisResult(
            subject=subject,
            visible_features=FEATURES,
            confidence=0.9,
            child_count=child_count,
        ),
        subject_hint=hint,
    )


def attach(
    e: Env, who: str, run_id: str, handle: str, *, key: str | None = None, **extra: Any
) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/assets",
        json={"asset_ref": handle, **extra},
        headers=who_headers(e, who, key or uuid4().hex),
    )


def idea(
    e: Env,
    who: str,
    run_id: str,
    *,
    revision: int | None = None,
    key: str | None = None,
    **body: Any,
) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/idea",
        json={
            "expected_run_revision": revision if revision is not None else run_revision(e, run_id),
            **body,
        },
        headers=who_headers(e, who, key or uuid4().hex),
    )


def read_transcript(e: Env, who: str, run_id: str) -> Any:
    return e.d.client.get(f"/v1/story-runs/{run_id}/transcript", headers=who_headers(e, who))


def confirm_transcript(
    e: Env, who: str, run_id: str, revision: int, digest: str, *, key: str | None = None
) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/transcript-confirmation",
        json={
            "expected_transcript_revision": revision,
            "transcript_sha256": digest,
            "confirmed": True,
        },
        headers=who_headers(e, who, key or uuid4().hex),
    )


def confirm_context(e: Env, who: str, run_id: str) -> Any:
    snapshot = e.d.client.get(f"/v1/story-runs/{run_id}", headers=who_headers(e, who)).json()[
        "story_run"
    ]
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/context-confirmation",
        json={
            "expected_context_revision": snapshot["context_revision"],
            "context_snapshot_sha256": snapshot["context_snapshot_sha256"],
            "confirmed": True,
        },
        headers=who_headers(e, who, uuid4().hex),
    )


def confirm_subject(
    e: Env,
    who: str,
    run_id: str,
    *,
    subject: str = SUBJECT,
    revision: int = 1,
    key: str | None = None,
) -> Any:
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/subject-confirmation",
        json={"expected_understanding_revision": revision, "confirmed_subject": subject},
        headers=who_headers(e, who, key or uuid4().hex),
    )


def rewrite(
    e: Env,
    who: str,
    run_id: str,
    *,
    revision: int | None = None,
    key: str | None = None,
    **body: Any,
) -> Any:
    if revision is None:
        revision = int(story_rows(e, run_id)[-1]["revision_no"])
    return e.d.client.post(
        f"/v1/story-runs/{run_id}/story-rewrites",
        json={"expected_story_revision": revision, **body},
        headers=who_headers(e, who, key or uuid4().hex),
    )


# ----------------------------------------------------------------------------- readers
def run_row(e: Env, run_id: str) -> Any:
    with e.sessions()() as db:
        return db.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()


def run_revision(e: Env, run_id: str) -> int:
    return int(run_row(e, run_id)["revision"])


def states(e: Env, run_id: str) -> tuple[str, str | None]:
    row = run_row(e, run_id)
    return str(row["run_state"]), row["job_state"]


def input_rows(e: Env, run_id: str) -> list[Any]:
    table = story_tables.run_inputs
    with e.sessions()() as db:
        return list(
            db.execute(
                select(table).where(table.c.run_id == run_id).order_by(table.c.input_revision)
            )
            .mappings()
            .all()
        )


def understanding_rows(e: Env, run_id: str) -> list[Any]:
    table = story_tables.understanding_revisions
    with e.sessions()() as db:
        return list(
            db.execute(select(table).where(table.c.run_id == run_id).order_by(table.c.revision_no))
            .mappings()
            .all()
        )


def transcript_rows(e: Env, run_id: str) -> list[Any]:
    table = story_tables.transcript_revisions
    with e.sessions()() as db:
        return list(
            db.execute(select(table).where(table.c.run_id == run_id).order_by(table.c.revision_no))
            .mappings()
            .all()
        )


def story_rows(e: Env, run_id: str) -> list[Any]:
    table = story_tables.story_revisions
    with e.sessions()() as db:
        return list(
            db.execute(select(table).where(table.c.run_id == run_id).order_by(table.c.revision_no))
            .mappings()
            .all()
        )


def receipt_rows(e: Env, run_id: str) -> list[Any]:
    table = story_tables.story_command_receipts
    with e.sessions()() as db:
        return list(
            db.execute(
                select(table).where(table.c.resource_ref == run_id).order_by(table.c.created_at)
            )
            .mappings()
            .all()
        )


def decision_rows(e: Env, run_id: str) -> list[Any]:
    table = story_tables.review_decisions
    with e.sessions()() as db:
        return list(db.execute(select(table).where(table.c.run_id == run_id)).mappings().all())


def asset_rows(e: Env, run_id: str) -> list[Any]:
    with e.sessions()() as db:
        return list(
            db.execute(
                select(CoreAssetMetadataModel)
                .where(CoreAssetMetadataModel.source_refs.contains([run_id]))
                .order_by(CoreAssetMetadataModel.asset_ref)
            )
            .scalars()
            .all()
        )


def upload_session_rows(e: Env, run_id: str) -> list[Any]:
    from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS

    with e.sessions()() as db:
        return list(
            db.execute(select(UPLOAD_SESSIONS).where(UPLOAD_SESSIONS.c.target_ref == run_id))
            .mappings()
            .all()
        )


# ----------------------------------------------------------------------------- composed steps
def to_subject_review(e: Env, who: str = "t1", *, run_id: str | None = None) -> str:
    """Create a run, attach its drawing and let the (fixture) analyzer understand it."""
    run_id = run_id or new_run(e, who)
    handle, data = drawing_handle(e, who, run_id)
    register_analysis(e, data)
    response = attach(e, who, run_id, handle)
    assert response.status_code == 202, response.text
    assert states(e, run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    return run_id


def seed_first_story(e: Env, run_id: str) -> str:
    """Insert the first story revision and its scenes by SQL and set the run to
    ``SCRIPT_REVIEW`` (mirrors ``complete_story_revision``; see the module docstring). Returns
    the story hash."""
    story, digest = normalize_story_output(valid_story(), confirmed_subject=SUBJECT)
    now = datetime.now(UTC)
    revision_id = str(uuid4())
    with e.sessions().begin() as db:
        run = db.execute(select(RUNS).where(RUNS.c.run_id == run_id)).mappings().one()
        current = story_tables.run_inputs
        input_row = (
            db.execute(
                select(current)
                .where(current.c.run_id == run_id)
                .order_by(current.c.input_revision.desc())
                .limit(1)
            )
            .mappings()
            .one()
        )
        db.execute(
            insert(story_tables.story_revisions).values(
                story_revision_id=revision_id,
                run_id=run_id,
                revision_no=1,
                status="DRAFT",
                source_asset_sha256=str(input_row["original_sha256"]),
                understanding_revision=int(run["understanding_revision"]),
                context_revision=int(input_row["context_revision"]),
                story_sha256=digest,
                language=story["language"],
                title=story["title"],
                duration_ms=story["duration_ms"],
                story_content=story["story"],
                schema_version="sketch2life.story-revision.v1",
                prompt_version="synthetic-prompt",
                model_id="synthetic-model",
                model_revision="1",
                request_sha256="e" * 64,
                provider_call_id="seed-call",
                created_at=now,
            )
        )
        for scene in story["scenes"]:
            db.execute(
                insert(story_tables.story_scenes).values(
                    scene_id=str(uuid4()),
                    story_revision_id=revision_id,
                    scene_index=scene["scene_index"],
                    title=scene["title"],
                    action=scene["action"],
                    visual_prompt=scene["visual_prompt"],
                    narration=scene["narration"],
                    start_ms=scene["start_ms"],
                    duration_ms=scene["duration_ms"],
                    character_anchors=scene["character_anchors"],
                )
            )
        db.execute(
            update(RUNS)
            .where(RUNS.c.run_id == run_id)
            .values(
                run_state="SCRIPT_REVIEW",
                job_state="SUCCEEDED",
                retryable=False,
                error_code=None,
                result_sha256=digest,
                version=int(run["version"]) + 1,
                revision=int(run["revision"]) + 1,
                updated_at=now,
            )
        )
    return digest


def to_script_review(e: Env, who: str = "t1") -> str:
    """Drawing, understanding, context and subject confirmed: the last confirmation starts the
    first story by itself (V4-A OPEN-A D1) and the composed generator answers after the response."""
    run_id = to_subject_review(e, who)
    assert confirm_context(e, who, run_id).status_code == 200
    assert states(e, run_id)[0] == "SUBJECT_REVIEW"
    assert confirm_subject(e, who, run_id).status_code == 202
    assert states(e, run_id) == ("SCRIPT_REVIEW", "SUCCEEDED")
    assert [row["revision_no"] for row in story_rows(e, run_id)] == [1]
    return run_id


def wav_bytes(milliseconds: int = 2000, *, seed: int = 0) -> bytes:
    return wav_audio(milliseconds, seed=seed)
