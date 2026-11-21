"""FEAT-066 T-2c: ``POST /v1/story-runs/{id}/idea`` and the transcript routes on PostgreSQL.

SRS l.1665 (idea), l.512 and l.1413 (voice idea, editing creates a revision), l.1713 and TD-04
(exact confirmation), l.982 (2 minutes, 20,000,000 bytes), l.394 (``INPUT_REVIEW``), BR-23 and
l.1472 (kept until the run is deleted). Runs only against a disposable database whose name
contains ``be1_acceptance`` and ``frc08_v3_t2c``. Object storage is the in-memory port by default;
when ``T2C_S3_ENDPOINT``, ``T2C_S3_BUCKET``, ``T2C_S3_ACCESS_KEY`` and ``T2C_S3_SECRET_KEY`` are
set the module runs against the local S3Mock target after the T-2z guard (``check_s3mock_target``:
loopback, endpoint and bucket equal to ``FRC08_ALLOWED_ENDPOINT`` and ``FRC08_ALLOWED_BUCKET``,
bucket containing ``frc08`` and ``v3-t2c``, no ambient ``AWS_*`` variable). Only synthetic,
in-memory audio and images are used; no key or bucket is ever deleted by a fixture. No provider is
called: the drawing analyzer and the speech transcriber are deterministic fixtures keyed by
SHA-256.
"""

from __future__ import annotations

import hashlib
import io
import os
import struct
import wave
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Barrier, Lock
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import insert, null, select, text, update
from sqlalchemy.exc import DataError, IntegrityError

from sketch2life.application.ports.core_foundation import LifecycleScope
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import MalwareDetected, MalwareScanResult
from sketch2life.application.ports.object_storage import ObjectStorageFailure, StoredObject
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAnalysisResult,
    SpeechTranscriptionResult,
)
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRunError,
    ParentStoryRunRecord,
)
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalTestSignatureMediaValidator,
)
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    SqlCoreRunAssetPurge,
    build_plan,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
)
from sketch2life.infrastructure.persistence.story_lifecycle_store import (
    SqlStoryLifecycleStore,
)
from sketch2life.infrastructure.story_inputs.drawing import normalize_drawing
from sketch2life.infrastructure.story_inputs.fixtures import (
    FixtureDrawingAnalyzer,
    FixtureSpeechTranscriber,
)
from sketch2life.infrastructure.story_inputs.runner import ParentInputJobRunner
from sketch2life.infrastructure.story_inputs.speech import ParentSpeechJobRunner
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tools.local_s3mock_target import check_s3_credentials, check_s3mock_target, ensure_task_bucket
from tools.run_be1_lifecycle_consumer import TargetRefused

ISSUER = "synthetic-t2c-issuer"
TASK_TAG = "v3-t2c"
_S3_VARIABLES = ("T2C_S3_ENDPOINT", "T2C_S3_BUCKET", "T2C_S3_ACCESS_KEY", "T2C_S3_SECRET_KEY")
STORAGE_WORDS = ("bucket", "normalized.png", "parent/", "object_key", "presigned", "s3mock")
SPEECH = "Con rồng nhỏ biết chia sẻ kẹo"
TYPED = "A friendly dragon learns to share"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def png_bytes(*, seed: int = 0) -> bytes:
    image = Image.new("RGB", (64, 48), (245, 245, 235))
    for index in range(1, 6):
        image.putpixel(((index * 7 + seed) % 64, (index * 5 + seed * 3) % 48), (10, 30, 60))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def wav_audio(milliseconds: int = 2000, *, seed: int = 0, rate: int = 1000) -> bytes:
    """A synthetic mono 8-bit PCM WAV of ``milliseconds`` (distinct bytes per ``seed``)."""
    frames = milliseconds * rate // 1000
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(1)
        writer.setframerate(rate)
        writer.writeframes(bytes((seed + index) % 251 for index in range(frames)))
    return buffer.getvalue()


def _box(kind: bytes, body: bytes = b"") -> bytes:
    return struct.pack(">I", 8 + len(body)) + kind + body


def mp4_audio(milliseconds: int = 2000, *, seed: int = 0, with_moov: bool = True) -> bytes:
    ftyp = _box(b"ftyp", b"M4A \x00\x00\x00\x00M4A mp42isom")
    mvhd = _box(
        b"mvhd",
        b"\x00\x00\x00\x00" + struct.pack(">IIII", 0, 0, 1000, milliseconds) + b"\x00" * 80,
    )
    mdat = _box(b"mdat", bytes((seed + index) % 251 for index in range(512)))
    return ftyp + mdat + (_box(b"moov", mvhd) if with_moov else b"")


class InMemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, tuple[bytes, str]] = {}

    def put_object(
        self, key: str, body: Any, *, content_type: str, content_length: int, metadata: Any
    ) -> None:
        content = body.read()
        assert len(content) == content_length
        self.objects[key] = (content, content_type)

    def get_object(self, key: str) -> StoredObject | None:
        item = self.objects.get(key)
        if item is None:
            return None
        content, content_type = item
        return StoredObject(io.BytesIO(content), len(content), content_type, {})

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(sorted(key for key in self.objects if key.startswith(prefix)))


class FaultStorage:
    """Delegating storage that records puts and can fail the reads on demand."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.puts: list[str] = []
        self.deletes: list[str] = []
        self.fail_get_containing: str | None = None
        self._lock = Lock()

    def put_object(self, key: str, body: Any, **kwargs: Any) -> None:
        with self._lock:
            self.puts.append(key)
        self.inner.put_object(key, body, **kwargs)

    def get_object(self, key: str) -> Any:
        if self.fail_get_containing is not None and self.fail_get_containing in key:
            raise ObjectStorageFailure("synthetic get failure")
        return self.inner.get_object(key)

    def delete_object(self, key: str) -> None:
        with self._lock:
            self.deletes.append(key)
        self.inner.delete_object(key)

    def list_keys(self, prefix: str) -> tuple[str, ...]:
        return tuple(self.inner.list_keys(prefix))

    def read(self, key: str) -> bytes | None:
        stored = self.inner.get_object(key)
        return None if stored is None else stored.body.read()


class AllowlistScanner:
    """CLEAN for registered SHA-256 digests, MalwareDetected for any other."""

    def __init__(self) -> None:
        self.clean: set[str] = set()

    def scan(self, file_obj: Any) -> MalwareScanResult:
        file_obj.seek(0)
        digest = hashlib.sha256(file_obj.read()).hexdigest()
        file_obj.seek(0)
        if digest not in self.clean:
            raise MalwareDetected("synthetic")
        return MalwareScanResult("t2c-allowlist", "1", "CLEAN")


@dataclass
class IdeaApi:
    app: FastAPI
    client: TestClient
    storage: FaultStorage
    scanner: AllowlistScanner
    analyzer: FixtureDrawingAnalyzer
    transcriber: FixtureSpeechTranscriber
    parent: str
    other_parent: str
    teacher: str
    real_s3: bool = False

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory


def _s3_storage() -> Any | None:
    if not all(os.environ.get(name) for name in _S3_VARIABLES):
        return None
    endpoint = os.environ["T2C_S3_ENDPOINT"]
    bucket = os.environ["T2C_S3_BUCKET"]
    access_key = os.environ["T2C_S3_ACCESS_KEY"]
    secret_key = os.environ["T2C_S3_SECRET_KEY"]
    try:
        check_s3mock_target(endpoint, bucket, task_tag=TASK_TAG, environ=os.environ)
        check_s3_credentials(access_key, secret_key, os.environ)
    except TargetRefused as refused:
        pytest.fail(f"REFUSED code={refused.code}", pytrace=False)
    from sketch2life.infrastructure.storage.s3_compatible import (
        Boto3S3CompatibleObjectStorage,
        build_s3_client,
    )

    client = build_s3_client(
        endpoint_url=endpoint, region_name="us-east-1", access_key=access_key, secret_key=secret_key
    )
    ensure_task_bucket(client, bucket)
    return Boto3S3CompatibleObjectStorage(
        bucket=bucket,
        endpoint_url=endpoint,
        region_name="us-east-1",
        access_key=access_key,
        secret_key=secret_key,
    )


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[IdeaApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t2c" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t2c*be1_acceptance db")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", database_url)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("SKETCH2LIFE_AUTH_PROVIDER", "development")
    monkeypatch.setenv("SKETCH2LIFE_AI_PROVIDER", "disabled")
    monkeypatch.delenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    app = create_app()
    runtime = app.state.be1_runtime
    if runtime.engine is None or runtime.session_factory is None:
        pytest.fail("PostgreSQL runtime did not initialize")
    token = uuid4().hex[:8]
    parent, other_parent = f"synthetic-t2c-parent-{token}", f"synthetic-t2c-parent2-{token}"
    teacher = f"synthetic-t2c-teacher-{token}"
    with runtime.session_factory.begin() as db:
        for subject, role in ((parent, "parent"), (other_parent, "parent"), (teacher, "teacher")):
            db.add(
                AdultIdentityModel(
                    subject=subject, issuer=ISSUER, state="active", account_role=role
                )
            )

    async def verified(
        x_test_principal: str = Header(alias="X-Test-Principal"),
    ) -> VerifiedPrincipal:
        return VerifiedPrincipal(subject=x_test_principal, issuer=ISSUER, roles=frozenset())

    s3 = _s3_storage()
    storage = FaultStorage(s3 if s3 is not None else InMemoryStorage())
    scanner = AllowlistScanner()
    app.state.lesson_library_storage = storage
    app.state.lesson_document_scanner = scanner
    app.state.upload_media_validator = LocalTestSignatureMediaValidator(env="test")
    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield IdeaApi(
                app,
                client,
                storage,
                scanner,
                FixtureDrawingAnalyzer(),
                FixtureSpeechTranscriber(),
                parent,
                other_parent,
                teacher,
                real_s3=s3 is not None,
            )
    finally:
        app.dependency_overrides.clear()
        runtime.engine.dispose()
        get_settings.cache_clear()
        get_core_database_settings.cache_clear()


# ----------------------------------------------------------------------------- helpers
def principal_of(subject: str) -> VerifiedPrincipal:
    return VerifiedPrincipal(subject=subject, issuer=ISSUER, roles=frozenset())


def headers(subject: str, key: str | None = None) -> dict[str, str]:
    result = {"X-Test-Principal": subject}
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def new_run(api: IdeaApi, owner: str, *, hold_slot: bool = True) -> str:
    """A run with its first input (typed idea, confirmed Parent context, no drawing yet)."""
    run_id = str(uuid4())
    now = datetime.now(UTC)
    scope_ref = parent_scope_ref(principal_of(owner))
    with api.sessions().begin() as db:
        account_id = db.scalar(
            select(AdultIdentityModel.account_id).where(AdultIdentityModel.subject == owner)
        )
        db.execute(
            story_tables.story_runs.insert().values(
                run_id=run_id,
                actor_scope_kind="PARENT_ACCOUNT",
                actor_scope_ref=scope_ref,
                profile_ref=str(uuid4()),
                run_state="INPUT_PROCESSING",
                revision=2,
                version=2,
                current_input_revision=1,
                active_owner_parent_account_id=str(account_id) if hold_slot else None,
                created_at=now,
                updated_at=now,
            )
        )
        db.execute(
            story_tables.run_inputs.insert().values(
                run_input_id=str(uuid4()),
                run_id=run_id,
                input_revision=1,
                typed_idea=TYPED,
                idea_source="TEXT",
                source_profile_revision_ref=str(uuid4()),
                context_revision=1,
                context_snapshot={
                    "schema_version": "sketch2life.parent-context.v1",
                    "profile_revision_ref": str(uuid4()),
                    "age_months": 60,
                    "interests_summary": "",
                    "topic": "synthetic",
                    "adult_confirmed_idea": TYPED,
                },
                context_snapshot_sha256="c" * 64,
                context_confirmed_by=scope_ref,
                context_confirmed_at=now,
                created_at=now,
            )
        )
    return run_id


def upload(
    api: IdeaApi,
    owner: str,
    run_id: str,
    data: bytes,
    media_type: str = "image/png",
    purpose: str = "RUN_ARTWORK",
) -> str:
    """Create, fill and complete an upload; returns the opaque ``asset_ref``."""
    api.scanner.clean.add(sha(data))
    created = api.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": purpose,
            "target_ref": run_id,
            "media_type": media_type,
            "expected_size_bytes": len(data),
            "expected_sha256": sha(data),
        },
        headers=headers(owner, uuid4().hex),
    )
    assert created.status_code == 201, created.text
    upload_id = created.json()["upload_id"]
    part = api.client.put(
        f"/v1/upload-sessions/{upload_id}/parts/1",
        content=data,
        headers={
            **headers(owner),
            "X-Part-SHA256": sha(data),
            "Content-Type": "application/octet-stream",
        },
    )
    assert part.status_code == 200, part.text
    done = api.client.post(
        f"/v1/upload-sessions/{upload_id}/complete",
        json={"expected_size_bytes": len(data), "expected_sha256": sha(data)},
        headers=headers(owner, uuid4().hex),
    )
    assert done.status_code == 202, done.text
    handle = done.json()["asset_ref"]
    assert handle == f"upl_{upload_id}"
    return str(handle)


def upload_audio(
    api: IdeaApi, owner: str, run_id: str, data: bytes, media_type: str = "audio/wav"
) -> str:
    return upload(api, owner, run_id, data, media_type, "RUN_AUDIO")


def run_row(api: IdeaApi, run_id: str) -> Any:
    with api.sessions()() as db:
        return (
            db.execute(
                select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )


def revision_of(api: IdeaApi, run_id: str) -> int:
    return int(run_row(api, run_id)["revision"])


def input_rows(api: IdeaApi, run_id: str) -> list[Any]:
    with api.sessions()() as db:
        return list(
            db.execute(
                select(story_tables.run_inputs)
                .where(story_tables.run_inputs.c.run_id == run_id)
                .order_by(story_tables.run_inputs.c.input_revision)
            )
            .mappings()
            .all()
        )


def transcript_rows(api: IdeaApi, run_id: str) -> list[Any]:
    table = story_tables.transcript_revisions
    with api.sessions()() as db:
        return list(
            db.execute(select(table).where(table.c.run_id == run_id).order_by(table.c.revision_no))
            .mappings()
            .all()
        )


def live_transcripts(api: IdeaApi, run_id: str) -> list[Any]:
    return [row for row in transcript_rows(api, run_id) if row["state"] != "SUPERSEDED"]


def receipt_rows(api: IdeaApi, run_id: str, operation: str) -> list[Any]:
    with api.sessions()() as db:
        return list(
            db.execute(
                select(story_tables.story_command_receipts).where(
                    story_tables.story_command_receipts.c.resource_ref == run_id,
                    story_tables.story_command_receipts.c.operation == operation,
                )
            )
            .mappings()
            .all()
        )


def asset_rows(api: IdeaApi, run_id: str) -> list[Any]:
    with api.sessions()() as db:
        rows = db.scalars(select(CoreAssetMetadataModel)).all()
        return [row for row in rows if run_id in row.source_refs]


def code_of(response: Any) -> str:
    return str(response.json()["code"])


def wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {
        k: v for k, v in body.items() if k not in {"request_id", "correlation_id"}
    }


def idea(
    api: IdeaApi,
    owner: str,
    run_id: str,
    *,
    key: str | None = None,
    revision: int | None = None,
    **body: Any,
) -> Any:
    payload = {
        "expected_run_revision": revision if revision is not None else revision_of(api, run_id),
        **body,
    }
    return api.client.post(
        f"/v1/story-runs/{run_id}/idea", json=payload, headers=headers(owner, key or uuid4().hex)
    )


def read_transcript(api: IdeaApi, owner: str, run_id: str) -> Any:
    return api.client.get(f"/v1/story-runs/{run_id}/transcript", headers=headers(owner))


def confirm(
    api: IdeaApi, owner: str, run_id: str, *, key: str | None = None, **override: Any
) -> Any:
    view = read_transcript(api, owner, run_id).json()
    body = {
        "expected_transcript_revision": view["transcript_revision"],
        "transcript_sha256": view["transcript_sha256"],
        "confirmed": True,
        **override,
    }
    return api.client.post(
        f"/v1/story-runs/{run_id}/transcript-confirmation",
        json=body,
        headers=headers(owner, key or uuid4().hex),
    )


def compose_analyzer(api: IdeaApi) -> None:
    api.app.state.drawing_analyzer = api.analyzer


def compose_transcriber(api: IdeaApi) -> None:
    api.app.state.speech_transcriber = api.transcriber


def derived_sha(data: bytes) -> str:
    return normalize_drawing(data, declared_media_type="image/png").sha256


def attach_drawing(api: IdeaApi, owner: str, run_id: str, seed: int, *, understood: bool) -> str:
    """Upload and attach a drawing; with ``understood`` the analyzer answers for it."""
    data = png_bytes(seed=seed)
    if understood:
        api.analyzer.register(
            derived_sha(data), DrawingAnalysisResult("dragon", ("wings", "tail"), 0.9, 1, True)
        )
    handle = upload(api, owner, run_id, data)
    response = api.client.post(
        f"/v1/story-runs/{run_id}/assets",
        json={"asset_ref": handle},
        headers=headers(owner, uuid4().hex),
    )
    assert response.status_code == 202, response.text
    return handle


def states(api: IdeaApi, run_id: str) -> tuple[str, str | None]:
    row = run_row(api, run_id)
    return str(row["run_state"]), row["job_state"]


@dataclass
class Prepared:
    run_id: str
    audio: bytes
    audio_ref: str


def run_in_input_review(
    api: IdeaApi,
    owner: str | None = None,
    *,
    speech: str | SpeechTranscriptionResult = SPEECH,
    seed: int | None = None,
    hold_slot: bool = True,
) -> Prepared:
    """A run with an understood drawing and a voice idea whose transcript needs confirmation."""
    owner = owner or api.parent
    seed = seed if seed is not None else int(uuid4().int % 200) + 1
    compose_analyzer(api)
    compose_transcriber(api)
    run_id = new_run(api, owner, hold_slot=hold_slot)
    attach_drawing(api, owner, run_id, seed, understood=True)
    assert states(api, run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    audio = wav_audio(2000, seed=seed)
    api.transcriber.register(sha(audio), speech)
    audio_ref = upload_audio(api, owner, run_id, audio)
    response = idea(api, owner, run_id, audio_ref=audio_ref)
    assert response.status_code == 202, response.text
    return Prepared(run_id, audio, audio_ref)


def reserve(api: IdeaApi, owner: str, run_id: str, key: str | None = None) -> Any:
    with api.sessions()() as db:
        return SqlParentStoryRunRepository(db).reserve_story_revision(
            principal=principal_of(owner),
            run_id=run_id,
            expected_understanding_revision=understanding_of(api, run_id),
            rewrite_instruction=None,
            idempotency_key=key or uuid4().hex,
            story_revision_id=str(uuid4()),
            model_id="synthetic-model",
            model_revision="1",
            prompt_version="synthetic-prompt",
        )


def understanding_of(api: IdeaApi, run_id: str) -> int:
    return int(run_row(api, run_id)["understanding_revision"] or 1)


def confirm_subject_route(api: IdeaApi, owner: str, run_id: str) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run_id}/subject-confirmation",
        json={
            "expected_understanding_revision": understanding_of(api, run_id),
            "confirmed_subject": "dragon",
        },
        headers=headers(owner, uuid4().hex),
    )


# ---------------------------------------------------------------------------- full path
def test_audio_idea_asr_correction_confirmation_and_the_story_gate(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    # the idea answered 202 with the voice input revision and the pending transcript
    assert states(api, run_id) == ("INPUT_REVIEW", "SUCCEEDED")
    (row,) = live_transcripts(api, run_id)
    assert (row["origin"], row["state"], row["raw_transcript"]) == (
        "ASR",
        "NEEDS_CONFIRMATION",
        SPEECH,
    )
    assert row["transcript_sha256"] == text_sha(SPEECH) and row["revision_no"] == 1
    assert (row["language"], row["model_revision"]) == ("vi", "fixture-1")
    inputs = input_rows(api, run_id)
    voice = inputs[-1]
    assert [item["input_revision"] for item in inputs] == [1, 2, 3]
    assert voice["idea_source"] == "TEXT_AND_VOICE" and voice["typed_idea"] == TYPED
    assert voice["voice_asset_ref"].endswith("/original") and voice["voice_duration_ms"] == 2000
    # the drawing, the context and its confirmation are copied forward
    assert voice["derived_sha256"] == inputs[1]["derived_sha256"]
    assert voice["context_confirmed_by"] == inputs[0]["context_confirmed_by"]

    # the adult reads it: owner only, not cached
    read = read_transcript(api, api.parent, run_id)
    assert read.status_code == 200 and read.headers["Cache-Control"] == "private, no-store"
    assert wire(read)[1] == {
        "story_run_id": run_id,
        "transcript_revision": 1,
        "state": "NEEDS_CONFIRMATION",
        "origin": "ASR",
        "text": SPEECH,
        "transcript_sha256": text_sha(SPEECH),
        "language": "vi",
        "error_code": None,
        "run_revision": revision_of(api, run_id),
    }
    # the run state hides the review: the subject cannot be confirmed yet
    assert confirm_subject_route(api, api.parent, run_id).status_code == 409
    # the gate: the story worker would not get an unconfirmed text
    assert states(api, run_id)[0] == "INPUT_REVIEW"

    # the adult corrects the text: a new revision, the old row is superseded
    corrected = "Con rồng nhỏ chia kẹo cho bạn"
    response = idea(
        api,
        api.parent,
        run_id,
        transcript_correction={"base_revision": 1, "text": corrected},
    )
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["transcript"] == {"transcript_revision": 2, "state": "NEEDS_CONFIRMATION"}
    assert body["input_revision"] == 3 and body["run_state"] == "INPUT_REVIEW"
    rows = transcript_rows(api, run_id)
    assert [(item["revision_no"], item["state"]) for item in rows] == [
        (1, "SUPERSEDED"),
        (2, "NEEDS_CONFIRMATION"),
    ]
    assert rows[1]["origin"] == "ADULT_CORRECTION" and rows[1]["adult_corrected_text"] == corrected
    assert rows[1]["raw_transcript"] == SPEECH and rows[1]["transcript_sha256"] == text_sha(
        corrected
    )
    assert len(input_rows(api, run_id)) == 3  # a correction writes no input revision

    # the old revision and hash no longer confirm
    stale = api.client.post(
        f"/v1/story-runs/{run_id}/transcript-confirmation",
        json={
            "expected_transcript_revision": 1,
            "transcript_sha256": text_sha(SPEECH),
            "confirmed": True,
        },
        headers=headers(api.parent, uuid4().hex),
    )
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == 2
    wrong_hash = confirm(api, api.parent, run_id, transcript_sha256="0" * 64)
    assert wrong_hash.status_code == 409 and wrong_hash.json()["current_version"] == 2

    confirmed = confirm(api, api.parent, run_id, key="confirm-1")
    assert confirmed.status_code == 200, confirmed.text
    cbody = confirmed.json()
    assert (cbody["transcript_revision"], cbody["state"], cbody["run_state"]) == (
        2,
        "CONFIRMED",
        "SUBJECT_REVIEW",
    )
    (live,) = live_transcripts(api, run_id)
    assert live["state"] == "CONFIRMED" and live["reviewed_by"] == parent_scope_ref(
        principal_of(api.parent)
    )
    assert live["reviewed_at"] is not None

    # the story gate reads the confirmed text, typed idea first
    assert confirm_subject_route(api, api.parent, run_id).status_code == 202
    reservation = reserve(api, api.parent, run_id)
    assert reservation.worker_input["adult_confirmed_idea"] == f"{TYPED} {corrected}"
    assert len(reservation.worker_input["adult_confirmed_idea"]) <= 500
    assert states(api, run_id)[0] == "SCRIPT_GENERATING"


def test_a_voice_only_idea_sends_only_the_confirmed_text(api: IdeaApi) -> None:
    compose_analyzer(api)
    compose_transcriber(api)
    run_id = new_run(api, api.parent)
    with api.sessions().begin() as db:  # a run created without a typed idea
        db.execute(
            update(story_tables.run_inputs)
            .where(story_tables.run_inputs.c.run_id == run_id)
            .values(typed_idea=None, idea_source=None)
        )
    attach_drawing(api, api.parent, run_id, 11, understood=True)
    audio = wav_audio(1500, seed=11)
    api.transcriber.register(sha(audio), SPEECH)
    handle = upload_audio(api, api.parent, run_id, audio)
    response = idea(api, api.parent, run_id, audio_ref=handle)
    assert response.status_code == 202 and response.json()["idea_source"] == "VOICE"
    assert input_rows(api, run_id)[-1]["typed_idea"] is None
    assert confirm(api, api.parent, run_id).status_code == 200
    assert confirm_subject_route(api, api.parent, run_id).status_code == 202
    assert reserve(api, api.parent, run_id).worker_input["adult_confirmed_idea"] == SPEECH


def test_mp4_audio_is_accepted_and_measured_from_the_header(api: IdeaApi) -> None:
    compose_transcriber(api)
    run_id = new_run(api, api.parent)
    audio = mp4_audio(7500, seed=3)
    api.transcriber.register(sha(audio), SPEECH)
    handle = upload_audio(api, api.parent, run_id, audio, "audio/mp4")
    response = idea(api, api.parent, run_id, audio_ref=handle)
    assert response.status_code == 202, response.text
    assert input_rows(api, run_id)[-1]["voice_duration_ms"] == 7500
    assert api.transcriber.calls[-1].media_type == "audio/mp4"
    assert api.transcriber.calls[-1].duration_ms == 7500


# --------------------------------------------------------------- ordering of the two jobs
def test_asr_finishes_before_the_drawing_analysis(api: IdeaApi) -> None:  # (B)
    compose_transcriber(api)
    run_id = new_run(api, api.parent)
    drawing = png_bytes(seed=21)
    api.analyzer.register(derived_sha(drawing), DrawingAnalysisResult("dragon", ("wings",), 0.9))
    handle = upload(api, api.parent, run_id, drawing)
    attached = api.client.post(
        f"/v1/story-runs/{run_id}/assets",
        json={"asset_ref": handle},
        headers=headers(api.parent, uuid4().hex),
    )
    assert attached.status_code == 202 and states(api, run_id) == ("INPUT_PROCESSING", "QUEUED")
    audio = wav_audio(1000, seed=21)
    api.transcriber.register(sha(audio), SPEECH)
    assert (
        idea(
            api, api.parent, run_id, audio_ref=upload_audio(api, api.parent, run_id, audio)
        ).status_code
        == 202
    )
    (row,) = live_transcripts(api, run_id)
    assert row["state"] == "NEEDS_CONFIRMATION"
    assert states(api, run_id) == ("INPUT_PROCESSING", "QUEUED")  # the VLM is still outstanding
    # the adult may already confirm the text; the run waits for the drawing
    assert confirm(api, api.parent, run_id).status_code == 200
    assert states(api, run_id) == ("INPUT_PROCESSING", "QUEUED")
    # the drawing analysis, started for input revision 2, finishes after revision 3 was written:
    # the drawing is the same, so the result counts
    ParentInputJobRunner(api.sessions(), api.analyzer).run(principal_of(api.parent), run_id, 2)
    assert states(api, run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")


def test_the_drawing_analysis_finishes_before_asr(api: IdeaApi) -> None:  # (C)
    compose_analyzer(api)
    run_id = new_run(api, api.parent)
    attach_drawing(api, api.parent, run_id, 22, understood=True)
    assert states(api, run_id) == ("SUBJECT_REVIEW", "SUCCEEDED")
    audio = wav_audio(1000, seed=22)
    api.transcriber.register(sha(audio), SPEECH)
    handle = upload_audio(api, api.parent, run_id, audio)
    assert api.app.state.speech_transcriber is None
    response = idea(api, api.parent, run_id, audio_ref=handle)
    assert response.status_code == 202 and response.json()["run_state"] == "INPUT_PROCESSING"
    (pending,) = live_transcripts(api, run_id)
    assert pending["state"] == "PENDING"
    assert read_transcript(api, api.parent, run_id).json()["state"] == "PENDING"
    assert read_transcript(api, api.parent, run_id).json()["text"] is None
    # no transcriber composed: the run waits, the subject cannot be confirmed, the adult can cancel
    assert confirm_subject_route(api, api.parent, run_id).status_code == 409
    ParentSpeechJobRunner(api.sessions(), api.transcriber).run(
        principal_of(api.parent), run_id, pending["transcript_revision_id"]
    )
    assert states(api, run_id)[0] == "INPUT_REVIEW"
    assert confirm(api, api.parent, run_id).status_code == 200
    assert states(api, run_id)[0] == "SUBJECT_REVIEW"


def test_a_failed_asr_is_reviewed_and_the_adult_types_the_text(api: IdeaApi) -> None:  # (D)
    compose_analyzer(api)
    compose_transcriber(api)
    run_id = new_run(api, api.parent)
    attach_drawing(api, api.parent, run_id, 23, understood=True)
    audio = wav_audio(1000, seed=23)  # the fixture transcriber knows no hash for it
    handle = upload_audio(api, api.parent, run_id, audio)
    assert idea(api, api.parent, run_id, audio_ref=handle).status_code == 202
    (row,) = live_transcripts(api, run_id)
    assert (row["state"], row["error_code"], row["raw_transcript"]) == (
        "FAILED",
        "ASR_UNAVAILABLE",
        None,
    )
    assert states(api, run_id)[0] == "INPUT_REVIEW"
    view = read_transcript(api, api.parent, run_id).json()
    assert (view["state"], view["error_code"], view["text"]) == ("FAILED", "ASR_UNAVAILABLE", None)
    # a confirmation of a failed row is refused
    refused = confirm(api, api.parent, run_id, transcript_sha256="0" * 64)
    assert refused.status_code == 409
    typed = "Con rồng nhỏ biết chia sẻ"
    corrected = idea(
        api, api.parent, run_id, transcript_correction={"base_revision": 1, "text": typed}
    )
    assert corrected.status_code == 202, corrected.text
    assert corrected.json()["transcript"] == {
        "transcript_revision": 2,
        "state": "NEEDS_CONFIRMATION",
    }
    assert confirm(api, api.parent, run_id).status_code == 200
    assert states(api, run_id)[0] == "SUBJECT_REVIEW"
    assert [row["state"] for row in transcript_rows(api, run_id)] == ["SUPERSEDED", "CONFIRMED"]


def test_a_text_only_idea_in_subject_review_keeps_the_state_and_the_candidate(
    api: IdeaApi,
) -> None:  # (E)
    compose_analyzer(api)
    run_id = new_run(api, api.parent)
    attach_drawing(api, api.parent, run_id, 24, understood=True)
    before = run_row(api, run_id)
    assert before["run_state"] == "SUBJECT_REVIEW"
    response = idea(api, api.parent, run_id, text="  a dragon who loves clouds  ")
    assert response.status_code == 202, response.text
    body = response.json()
    assert (body["run_state"], body["idea_source"], body["transcript"]) == (
        "SUBJECT_REVIEW",
        "TEXT",
        None,
    )
    assert body["input_revision"] == 3 and body["run_revision"] == before["revision"] + 1
    after = run_row(api, run_id)
    assert after["version"] == before["version"] + 1 and after["current_input_revision"] == 3
    latest = input_rows(api, run_id)[-1]
    assert latest["typed_idea"] == "a dragon who loves clouds" and latest["idea_source"] == "TEXT"
    assert latest["derived_sha256"] == input_rows(api, run_id)[1]["derived_sha256"]
    record = SqlParentStoryRunRepository(api.sessions()()).get_run(
        principal=principal_of(api.parent), run_id=run_id
    )
    # R-2: the drawing, not the input row, owns the candidate
    assert isinstance(record, ParentStoryRunRecord) and record.candidate is not None
    assert confirm_subject_route(api, api.parent, run_id).status_code == 202


def test_audio_in_subject_review_returns_the_run_to_input_processing(api: IdeaApi) -> None:  # (F)
    compose_analyzer(api)
    run_id = new_run(api, api.parent)
    attach_drawing(api, api.parent, run_id, 25, understood=True)
    audio = wav_audio(1000, seed=25)
    handle = upload_audio(api, api.parent, run_id, audio)
    response = idea(api, api.parent, run_id, audio_ref=handle)  # no transcriber composed
    assert response.status_code == 202
    assert response.json()["transcript"] == {"transcript_revision": 1, "state": "PENDING"}
    assert states(api, run_id)[0] == "INPUT_PROCESSING"
    # cancelling works while the transcript is pending
    cancel = api.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": revision_of(api, run_id)},
        headers=headers(api.parent, uuid4().hex),
    )
    assert cancel.status_code in {200, 202}, cancel.text
    assert states(api, run_id)[0] == "DELETE_PENDING"


def test_correcting_a_confirmed_transcript_returns_the_run_to_input_review(
    api: IdeaApi,
) -> None:  # (G)
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    assert confirm(api, api.parent, run_id).status_code == 200
    assert states(api, run_id)[0] == "SUBJECT_REVIEW"
    confirmed_row = live_transcripts(api, run_id)[0]
    response = idea(
        api,
        api.parent,
        run_id,
        transcript_correction={"base_revision": 1, "text": "đã sửa lại câu chuyện"},
    )
    assert response.status_code == 202, response.text
    assert response.json()["run_state"] == "INPUT_REVIEW"
    rows = transcript_rows(api, run_id)
    assert [(row["revision_no"], row["state"]) for row in rows] == [
        (1, "SUPERSEDED"),
        (2, "NEEDS_CONFIRMATION"),
    ]
    assert rows[0]["transcript_revision_id"] == confirmed_row["transcript_revision_id"]
    assert confirm_subject_route(api, api.parent, run_id).status_code == 409
    assert confirm(api, api.parent, run_id).status_code == 200  # the new revision is confirmed
    assert states(api, run_id)[0] == "SUBJECT_REVIEW"


# ---------------------------------------------------- the retake keeps the voice (C1, H)
def test_a_retake_after_confirmed_audio_keeps_the_voice_and_the_gate_holds(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    assert confirm(api, api.parent, run_id).status_code == 200
    before = input_rows(api, run_id)[-1]
    assert before["voice_asset_ref"] is not None
    # the retake from SUBJECT_REVIEW (T-2b): a new drawing, analyzed as well
    attach_drawing(api, api.parent, run_id, 99, understood=True)
    after = input_rows(api, run_id)[-1]
    assert after["input_revision"] == before["input_revision"] + 1
    for column in (
        "voice_asset_ref",
        "voice_asset_version",
        "voice_duration_ms",
        "typed_idea",
        "idea_source",
        "context_confirmed_by",
    ):
        assert after[column] == before[column], column
    assert after["derived_sha256"] != before["derived_sha256"]
    # the confirmed transcript is found by (run, asset), not by the input row
    (live,) = live_transcripts(api, run_id)
    assert live["state"] == "CONFIRMED"
    assert read_transcript(api, api.parent, run_id).json()["state"] == "CONFIRMED"
    assert states(api, run_id)[0] == "SUBJECT_REVIEW"
    assert confirm_subject_route(api, api.parent, run_id).status_code == 202
    reservation = reserve(api, api.parent, run_id)
    assert reservation.worker_input["adult_confirmed_idea"] == f"{TYPED} {SPEECH}"


def test_a_failed_analysis_beside_a_pending_transcript_still_allows_the_one_retake(
    api: IdeaApi,
) -> None:
    compose_analyzer(api)  # the fixture knows no hash for the first drawing
    run_id = new_run(api, api.parent)
    attach_drawing(api, api.parent, run_id, 70, understood=False)
    assert states(api, run_id) == ("INPUT_REVIEW", "FAILED")  # T-2b's failure now reviews
    audio = wav_audio(1000, seed=70)
    handle = upload_audio(api, api.parent, run_id, audio)
    response = idea(api, api.parent, run_id, audio_ref=handle)  # no transcriber: PENDING
    assert response.status_code == 202 and response.json()["run_state"] == "INPUT_PROCESSING"
    assert states(api, run_id) == ("INPUT_PROCESSING", "FAILED")
    attach_drawing(api, api.parent, run_id, 71, understood=True)  # the one retake
    assert states(api, run_id)[0] == "INPUT_PROCESSING"
    assert input_rows(api, run_id)[-1]["voice_asset_ref"] is not None
    assert live_transcripts(api, run_id)[0]["state"] == "PENDING"
    # the retake is used up
    data = png_bytes(seed=72)
    api.scanner.clean.add(sha(data))
    refused = api.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": "RUN_ARTWORK",
            "target_ref": run_id,
            "media_type": "image/png",
            "expected_size_bytes": len(data),
            "expected_sha256": sha(data),
        },
        headers=headers(api.parent, uuid4().hex),
    )
    assert refused.status_code == 409


def test_a_retake_while_the_transcript_waits_cannot_skip_the_confirmation(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    attach_drawing(api, api.parent, run_id, 98, understood=True)  # retake from INPUT_REVIEW
    assert input_rows(api, run_id)[-1]["voice_asset_ref"] is not None
    assert states(api, run_id)[0] == "INPUT_REVIEW"  # not SUBJECT_REVIEW: the text is unconfirmed
    assert confirm_subject_route(api, api.parent, run_id).status_code == 409
    assert confirm(api, api.parent, run_id).status_code == 200
    assert states(api, run_id)[0] == "SUBJECT_REVIEW"


def test_the_repository_gate_refuses_an_unconfirmed_transcript_even_in_a_later_state(
    api: IdeaApi,
) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    assert confirm(api, api.parent, run_id).status_code == 200
    assert confirm_subject_route(api, api.parent, run_id).status_code == 202
    assert states(api, run_id)[0] == "PREPARATION_REVIEW"
    table = story_tables.transcript_revisions
    with api.sessions().begin() as db:  # simulate any defect that left the text unconfirmed
        db.execute(
            update(table)
            .where(table.c.run_id == run_id)
            .values(state="NEEDS_CONFIRMATION", reviewed_by=None, reviewed_at=None)
        )
    with pytest.raises(ParentStoryRunError) as raised:
        reserve(api, api.parent, run_id)
    assert (raised.value.status_code, raised.value.code) == (422, "TRANSCRIPT_NOT_CONFIRMED")
    assert states(api, run_id)[0] == "PREPARATION_REVIEW"
    assert [row["state"] for row in transcript_rows(api, run_id)] == ["NEEDS_CONFIRMATION"]
    with api.sessions().begin() as db:
        db.execute(
            update(table).where(table.c.run_id == run_id).values(state="FAILED", error_code="X")
        )
    with pytest.raises(ParentStoryRunError) as failed:
        reserve(api, api.parent, run_id)
    assert failed.value.code == "TRANSCRIPT_NOT_CONFIRMED"


# ---------------------------------------------------------------------- authorization
def test_other_actors_and_wrong_assets_get_one_404(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    view = read_transcript(api, api.parent, run_id).json()
    unknown_run = str(uuid4())
    other_run = new_run(api, api.other_parent)
    foreign_audio = upload_audio(api, api.other_parent, other_run, wav_audio(1000, seed=7))
    image_handle = upload(api, api.parent, run_id, png_bytes(seed=7))  # an artwork upload
    other_audio_same_parent = upload_audio(
        api, api.parent, run_id, wav_audio(1000, seed=8)
    )  # fine: used below only to prove the positive control
    reference = wire(idea(api, api.parent, unknown_run, text="x", revision=1))
    assert reference[0] == 404 and reference[1]["code"] == "RESOURCE_NOT_FOUND"
    attempts = {
        "other parent text": idea(api, api.other_parent, run_id, text="x", revision=1),
        "teacher text": idea(api, api.teacher, run_id, text="x", revision=1),
        "other parent correction": idea(
            api,
            api.other_parent,
            run_id,
            revision=1,
            transcript_correction={"base_revision": 1, "text": "x"},
        ),
        "foreign audio": idea(api, api.parent, run_id, audio_ref=foreign_audio),
        "image as audio": idea(api, api.parent, run_id, audio_ref=image_handle),
        "unknown handle": idea(api, api.parent, run_id, audio_ref=f"upl_{uuid4()}"),
        "other parent read": read_transcript(api, api.other_parent, run_id),
        "teacher read": read_transcript(api, api.teacher, run_id),
        "unknown run read": read_transcript(api, api.parent, unknown_run),
        "other parent confirm": api.client.post(
            f"/v1/story-runs/{run_id}/transcript-confirmation",
            json={
                "expected_transcript_revision": view["transcript_revision"],
                "transcript_sha256": view["transcript_sha256"],
                "confirmed": True,
            },
            headers=headers(api.other_parent, uuid4().hex),
        ),
        "teacher confirm": api.client.post(
            f"/v1/story-runs/{run_id}/transcript-confirmation",
            json={
                "expected_transcript_revision": 1,
                "transcript_sha256": "a" * 64,
                "confirmed": True,
            },
            headers=headers(api.teacher, uuid4().hex),
        ),
    }
    for name, response in attempts.items():
        assert wire(response) == reference, name
    assert SPEECH not in "".join(response.text for response in attempts.values())
    # nothing changed and the positive control still works
    assert len(live_transcripts(api, run_id)) == 1
    assert idea(api, api.parent, run_id, audio_ref=other_audio_same_parent).status_code == 202
    assert idea(api, api.parent, other_run, text="x", revision=1).status_code == 404


def test_audio_of_another_run_of_the_same_parent_is_a_404(api: IdeaApi) -> None:
    run_a = new_run(api, api.parent, hold_slot=False)
    run_b = new_run(api, api.parent, hold_slot=False)
    handle = upload_audio(api, api.parent, run_a, wav_audio(1000, seed=31))
    response = idea(api, api.parent, run_b, audio_ref=handle)
    assert response.status_code == 404 and code_of(response) == "RESOURCE_NOT_FOUND"
    assert transcript_rows(api, run_b) == []


def test_a_same_run_audio_session_offered_to_the_drawing_route_is_415(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload_audio(api, api.parent, run_id, wav_audio(1000, seed=32))
    response = api.client.post(
        f"/v1/story-runs/{run_id}/assets",
        json={"asset_ref": handle},
        headers=headers(api.parent, uuid4().hex),
    )
    assert response.status_code == 415 and code_of(response) == "UNSUPPORTED_MEDIA_TYPE"
    assert len(input_rows(api, run_id)) == 1


# ------------------------------------------------------------------------- audio admission
def test_audio_over_two_minutes_is_413_and_two_minutes_is_accepted(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    too_long = upload_audio(api, api.parent, run_id, wav_audio(120_001, seed=41))
    response = idea(api, api.parent, run_id, audio_ref=too_long)
    assert response.status_code == 413 and code_of(response) == "AUDIO_TOO_LARGE"
    assert response.json()["message"] and len(input_rows(api, run_id)) == 1
    assert transcript_rows(api, run_id) == []
    exact = upload_audio(api, api.parent, run_id, wav_audio(120_000, seed=42))
    accepted = idea(api, api.parent, run_id, audio_ref=exact)
    assert accepted.status_code == 202, accepted.text
    assert input_rows(api, run_id)[-1]["voice_duration_ms"] == 120_000
    run_b = new_run(api, api.parent, hold_slot=False)
    long_mp4 = upload_audio(api, api.parent, run_b, mp4_audio(120_500, seed=3), "audio/mp4")
    refused = idea(api, api.parent, run_b, audio_ref=long_mp4)
    assert refused.status_code == 413 and code_of(refused) == "AUDIO_TOO_LARGE"


def test_the_upload_session_refuses_more_than_20_million_bytes(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)

    def create(size: int, media_type: str = "audio/wav") -> Any:
        return api.client.post(
            "/v1/upload-sessions",
            json={
                "purpose": "RUN_AUDIO",
                "target_ref": run_id,
                "media_type": media_type,
                "expected_size_bytes": size,
                "expected_sha256": "a" * 64,
            },
            headers=headers(api.parent, uuid4().hex),
        )

    over = create(20_000_001)
    assert over.status_code == 413 and code_of(over) == "AUDIO_TOO_LARGE"
    assert create(20_000_000).status_code == 201
    unsupported = create(1000, "audio/ogg")
    assert unsupported.status_code == 415 and code_of(unsupported) == "UNSUPPORTED_MEDIA_TYPE"
    assert create(1000, "audio/mp4").status_code == 201


def test_an_unreadable_audio_is_a_422_content_mismatch(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    # passes the RIFF/WAVE signature check but is not a readable PCM file
    fake_wav = b"RIFF\x00\x00\x00\x00WAVE" + b"junk" * 64
    handle = upload_audio(api, api.parent, run_id, fake_wav)
    response = idea(api, api.parent, run_id, audio_ref=handle)
    assert response.status_code == 422 and code_of(response) == "UPLOAD_CONTENT_MISMATCH"
    no_moov = upload_audio(
        api, api.parent, run_id, mp4_audio(1000, seed=9, with_moov=False), "audio/mp4"
    )
    refused = idea(api, api.parent, run_id, audio_ref=no_moov)
    assert refused.status_code == 422 and code_of(refused) == "UPLOAD_CONTENT_MISMATCH"
    assert len(input_rows(api, run_id)) == 1 and transcript_rows(api, run_id) == []
    assert run_row(api, run_id)["revision"] == 2


def test_a_missing_or_tampered_original_and_a_storage_fault(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    audio = wav_audio(1000, seed=43)
    handle = upload_audio(api, api.parent, run_id, audio)
    key = f"parent/{run_id}/"
    (stored_key,) = [item for item in api.storage.list_keys(key) if item.endswith("/original")]
    original = api.storage.read(stored_key)
    assert original == audio
    api.storage.fail_get_containing = "original"
    fault = idea(api, api.parent, run_id, audio_ref=handle)
    assert fault.status_code == 503 and code_of(fault) == "STORAGE_UNAVAILABLE"
    api.storage.fail_get_containing = None
    api.storage.inner.put_object(
        stored_key,
        io.BytesIO(audio[:-1] + b"\x07"),
        content_type="audio/wav",
        content_length=len(audio),
        metadata={},
    )
    tampered = idea(api, api.parent, run_id, audio_ref=handle)
    assert tampered.status_code == 422 and code_of(tampered) == "UPLOAD_CHECKSUM_MISMATCH"
    api.storage.inner.delete_object(stored_key)
    missing = idea(api, api.parent, run_id, audio_ref=handle)
    assert missing.status_code == 422 and code_of(missing) == "UPLOAD_INCOMPLETE"
    api.storage.inner.put_object(
        stored_key,
        io.BytesIO(audio),
        content_type="audio/wav",
        content_length=len(audio),
        metadata={},
    )
    retried = idea(api, api.parent, run_id, audio_ref=handle)
    assert retried.status_code == 202, retried.text
    assert len(receipt_rows(api, run_id, "SUBMIT_IDEA")) == 1
    assert len(input_rows(api, run_id)) == 2


def test_the_same_audio_again_and_a_run_outside_the_window_are_409(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    audio = wav_audio(1000, seed=44)
    handle = upload_audio(api, api.parent, run_id, audio)
    assert idea(api, api.parent, run_id, audio_ref=handle).status_code == 202
    again = idea(api, api.parent, run_id, audio_ref=handle)  # another key, the same asset
    assert again.status_code == 409 and code_of(again) == "INVALID_STATE_TRANSITION"
    assert len(input_rows(api, run_id)) == 2 and len(transcript_rows(api, run_id)) == 1
    for state in (
        "PREPARATION_REVIEW",
        "SCRIPT_GENERATING",
        "SCRIPT_REVIEW",
        "FAILED",
        "COMPLETED",
    ):
        other = new_run(api, api.parent, hold_slot=False)
        with api.sessions().begin() as db:
            db.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == other)
                .values(run_state=state)
            )
        for response in (
            idea(api, api.parent, other, text="x"),
            idea(api, api.parent, other, transcript_correction={"base_revision": 1, "text": "x"}),
        ):
            assert response.status_code == 409, state
            assert code_of(response) == "INVALID_STATE_TRANSITION", state
        assert len(input_rows(api, other)) == 1
        assert read_transcript(api, api.parent, other).json()["state"] == "NONE"


# ------------------------------------------------------------------ idempotency and revisions
def test_a_replay_returns_the_same_answer_and_writes_nothing(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    first = idea(api, api.parent, run_id, key="replay-1", text="first idea")
    assert first.status_code == 202
    before = (
        run_row(api, run_id),
        input_rows(api, run_id),
        len(receipt_rows(api, run_id, "SUBMIT_IDEA")),
    )
    second = idea(api, api.parent, run_id, key="replay-1", text="first idea", revision=2)
    assert second.status_code == 202 and wire(second) == wire(first)
    assert (
        run_row(api, run_id),
        input_rows(api, run_id),
        len(receipt_rows(api, run_id, "SUBMIT_IDEA")),
    ) == before
    (receipt,) = receipt_rows(api, run_id, "SUBMIT_IDEA")
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 202
    assert receipt["response_body"] == {
        "input_revision": 2,
        "run_revision": 3,
        "run_state": "INPUT_PROCESSING",
        "idea_source": "TEXT",
        "transcript_revision": None,
        "transcript_state": None,
    }
    mixed = idea(api, api.parent, run_id, key="replay-1", text="another idea", revision=2)
    assert mixed.status_code == 400 and code_of(mixed) == "INVALID_IDEMPOTENCY_KEY"


def test_an_audio_replay_does_not_start_a_second_transcription(api: IdeaApi) -> None:
    compose_transcriber(api)
    run_id = new_run(api, api.parent)
    audio = wav_audio(1000, seed=45)
    api.transcriber.register(sha(audio), SPEECH)
    handle = upload_audio(api, api.parent, run_id, audio)
    first = idea(api, api.parent, run_id, key="audio-replay", audio_ref=handle)
    assert first.status_code == 202 and len(api.transcriber.calls) == 1
    second = idea(api, api.parent, run_id, key="audio-replay", audio_ref=handle, revision=2)
    assert (
        second.status_code == 202 and wire(second)[1]["transcript"] == wire(first)[1]["transcript"]
    )
    assert len(api.transcriber.calls) == 1 and len(transcript_rows(api, run_id)) == 1
    assert len(receipt_rows(api, run_id, "SUBMIT_IDEA")) == 1


def test_a_stale_run_revision_is_409_with_the_current_version(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    current = revision_of(api, run_id)
    stale = idea(api, api.parent, run_id, text="x", revision=current + 4)
    assert stale.status_code == 409 and code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == current
    assert len(input_rows(api, run_id)) == 1
    fresh = idea(api, api.parent, run_id, text="x", revision=current)
    assert fresh.status_code == 202 and fresh.json()["run_revision"] == current + 1
    stale_again = idea(api, api.parent, run_id, text="y", revision=current)
    assert stale_again.status_code == 409 and stale_again.json()["current_version"] == current + 1


def test_a_purged_run_refuses_a_fresh_command_and_replays_the_projection(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    first = idea(api, api.parent, run_id, key="before-delete", text="one more idea")
    assert first.status_code == 202
    cancel = api.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": revision_of(api, run_id)},
        headers=headers(api.parent, uuid4().hex),
    )
    assert cancel.status_code in {200, 202}, cancel.text
    assert states(api, run_id)[0] == "DELETE_PENDING"
    fresh = idea(api, api.parent, run_id, text="x", revision=1)
    assert fresh.status_code == 409 and code_of(fresh) == "INVALID_STATE_TRANSITION"
    replay = idea(api, api.parent, run_id, key="before-delete", text="one more idea", revision=1)
    assert replay.status_code == 202 and set(replay.json()) == {"request_id", "lifecycle"}
    assert replay.json()["lifecycle"]["run_state"] == "DELETE_PENDING"
    different = idea(api, api.parent, run_id, key="before-delete", text="other text", revision=1)
    assert different.status_code == 202 and "lifecycle" in different.json()
    assert read_transcript(api, api.parent, run_id).status_code == 409
    stale_confirm = api.client.post(
        f"/v1/story-runs/{run_id}/transcript-confirmation",
        json={"expected_transcript_revision": 1, "transcript_sha256": "a" * 64, "confirmed": True},
        headers=headers(api.parent, "after-delete"),
    )
    assert stale_confirm.status_code == 409 and code_of(stale_confirm) == "INVALID_STATE_TRANSITION"
    assert "transcript" not in replay.text.lower().replace("lifecycle", "")


# --------------------------------------------------------------- the confirmation rules
def test_confirmation_rules_pending_noop_and_length(api: IdeaApi) -> None:
    compose_analyzer(api)
    run_id = new_run(api, api.parent)
    attach_drawing(api, api.parent, run_id, 51, understood=True)
    audio = wav_audio(1000, seed=51)
    handle = upload_audio(api, api.parent, run_id, audio)
    assert idea(api, api.parent, run_id, audio_ref=handle).status_code == 202  # PENDING
    pending = api.client.post(
        f"/v1/story-runs/{run_id}/transcript-confirmation",
        json={"expected_transcript_revision": 1, "transcript_sha256": "a" * 64, "confirmed": True},
        headers=headers(api.parent, uuid4().hex),
    )
    assert pending.status_code == 409 and code_of(pending) == "INVALID_STATE_TRANSITION"
    nothing = api.client.post(
        f"/v1/story-runs/{run_id}/transcript-confirmation",
        json={"expected_transcript_revision": 7, "transcript_sha256": "a" * 64, "confirmed": True},
        headers=headers(api.parent, uuid4().hex),
    )
    assert nothing.status_code == 409 and nothing.json()["current_version"] == 1
    # a correction on a pending row waits for the ASR (nothing to correct yet)
    early = idea(api, api.parent, run_id, transcript_correction={"base_revision": 1, "text": "x"})
    assert early.status_code == 409 and code_of(early) == "INVALID_STATE_TRANSITION"
    # the ASR text is long: 300 characters, with the 34-character typed idea
    long_text = ("lời " * 75).strip()  # 299 characters
    compose_transcriber(api)
    api.transcriber.register(sha(audio), long_text)
    (row,) = live_transcripts(api, run_id)
    ParentSpeechJobRunner(api.sessions(), api.transcriber).run(
        principal_of(api.parent), run_id, row["transcript_revision_id"]
    )
    assert len(long_text) + 1 + len(TYPED) <= 500
    confirmed = confirm(api, api.parent, run_id, key="noop-key")
    assert confirmed.status_code == 200
    before = (run_row(api, run_id), transcript_rows(api, run_id))
    # the same revision and hash again with another key: the same answer, nothing written
    again = confirm(api, api.parent, run_id, key="other-key")
    assert again.status_code == 200
    assert wire(again)[1] == wire(confirmed)[1]
    assert (run_row(api, run_id), transcript_rows(api, run_id)) == before
    assert len(receipt_rows(api, run_id, "CONFIRM_TRANSCRIPT")) == 2
    # a replay of the first key
    replay = confirm(api, api.parent, run_id, key="noop-key")
    assert wire(replay) == wire(confirmed)
    # the same revision, already confirmed, with another hash: an old request, not a state error
    wrong_hash = confirm(api, api.parent, run_id, transcript_sha256="b" * 64)
    assert wrong_hash.status_code == 409 and code_of(wrong_hash) == "STALE_REVISION"
    assert wrong_hash.json()["current_version"] == 1
    assert (run_row(api, run_id), transcript_rows(api, run_id)) == before


def test_an_overlong_asr_config_hash_is_bounded_and_the_transcript_completes(
    api: IdeaApi,
) -> None:
    result = SpeechTranscriptionResult(
        text=SPEECH, model_revision="fixture-1", config_hash="f" * 100, language="vi"
    )
    prepared = run_in_input_review(api, speech=result)
    (row,) = live_transcripts(api, prepared.run_id)
    assert row["state"] == "NEEDS_CONFIRMATION"
    assert row["config_hash"] == "f" * 64


def test_the_500_character_rule_is_a_400_with_field_errors(api: IdeaApi) -> None:
    prepared = run_in_input_review(api, speech="câu " * 130)  # 519 characters of ASR text
    run_id = prepared.run_id
    too_long = confirm(api, api.parent, run_id)
    assert too_long.status_code == 400
    body = too_long.json()
    assert body["code"] == "INVALID_REQUEST"
    assert body["field_errors"] == [
        {"field": "transcript", "code": "TOO_LONG", "message": "Giá trị trường không hợp lệ."}
    ]
    assert "câu câu" not in too_long.text  # the text is never echoed
    assert [row["state"] for row in live_transcripts(api, run_id)] == ["NEEDS_CONFIRMATION"]
    assert receipt_rows(api, run_id, "CONFIRM_TRANSCRIPT") == []
    # the adult shortens it; the typed idea and the text must fit together (34 + 1 + n <= 500)
    fits = "x" * (500 - len(TYPED) - 1)
    ok = idea(api, api.parent, run_id, transcript_correction={"base_revision": 1, "text": fits})
    assert ok.status_code == 202
    assert confirm(api, api.parent, run_id).status_code == 200
    # a longer typed idea after the confirmation would no longer fit: refused with a field error
    refused = idea(api, api.parent, run_id, text="y" * 50)
    assert refused.status_code == 400
    assert refused.json()["field_errors"][0]["field"] == "text"
    assert refused.json()["field_errors"][0]["code"] == "TOO_LONG"
    assert len(input_rows(api, run_id)) == 3
    assert len(reserve_text(api, run_id)) == 500


def reserve_text(api: IdeaApi, run_id: str) -> str:
    assert confirm_subject_route(api, api.parent, run_id).status_code == 202
    return str(reserve(api, api.parent, run_id).worker_input["adult_confirmed_idea"])


# -------------------------------------------------------------------------- concurrency
def race_confirmation_and_correction(
    api: IdeaApi, run_id: str, payload: dict[str, Any], corrected_text: str
) -> tuple[Any, Any]:
    """Send the confirmation and a correction of the same revision at the same moment."""
    barrier = Barrier(2)

    def do_confirm() -> Any:
        barrier.wait(timeout=30)
        return api.client.post(
            f"/v1/story-runs/{run_id}/transcript-confirmation",
            json=payload,
            headers=headers(api.parent, uuid4().hex),
        )

    def do_correct() -> Any:
        barrier.wait(timeout=30)
        return idea(
            api,
            api.parent,
            run_id,
            transcript_correction={"base_revision": 1, "text": corrected_text},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        confirm_future = pool.submit(do_confirm)
        correct_future = pool.submit(do_correct)
        return confirm_future.result(), correct_future.result()


def test_a_correction_and_a_confirmation_racing_leave_one_consistent_live_row(
    api: IdeaApi,
) -> None:
    for round_number in range(3):
        prepared = run_in_input_review(api, hold_slot=False)
        run_id = prepared.run_id
        view = read_transcript(api, api.parent, run_id).json()
        payload = {
            "expected_transcript_revision": view["transcript_revision"],
            "transcript_sha256": view["transcript_sha256"],
            "confirmed": True,
        }
        confirmed, corrected = race_confirmation_and_correction(
            api, run_id, payload, f"sửa lần {round_number}"
        )
        assert confirmed.status_code in {200, 409}, confirmed.text
        assert corrected.status_code in {202, 409}, corrected.text
        live = live_transcripts(api, run_id)
        assert len(live) == 1  # one live row, always
        revisions = [row["revision_no"] for row in transcript_rows(api, run_id)]
        assert revisions == sorted(set(revisions))
        if corrected.status_code == 202:
            # the correction won or came after the confirmation: the live row is the new one and
            # is not confirmed, so the gate stays closed until it is confirmed
            assert (
                live[0]["origin"] == "ADULT_CORRECTION" and live[0]["state"] == "NEEDS_CONFIRMATION"
            )
            assert states(api, run_id)[0] == "INPUT_REVIEW"
        else:
            assert live[0]["state"] == "CONFIRMED" and live[0]["revision_no"] == 1
            assert states(api, run_id)[0] == "SUBJECT_REVIEW"
        # whatever happened, the reserved text is the live confirmed row, never the superseded one
        status = read_transcript(api, api.parent, run_id).json()
        assert status["state"] == live[0]["state"]


# ---------------------------------------------------- database checks and supersede order
def test_the_partial_unique_indexes_and_checks_hold_at_the_database(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    assert confirm(api, api.parent, run_id).status_code == 200
    (live,) = live_transcripts(api, run_id)
    table = story_tables.transcript_revisions

    def attempt(**values: Any) -> str | None:
        base = {
            "transcript_revision_id": str(uuid4()),
            "run_id": run_id,
            "run_input_id": live["run_input_id"],
            "source_asset_ref": live["source_asset_ref"],
            "revision_no": 50 + len(str(values)),
            "origin": "ASR",
            "state": "PENDING",
        }
        base.update(values)
        try:
            with api.sessions().begin() as db:
                db.execute(insert(table).values(**base))
        except IntegrityError as exc:
            return str(getattr(getattr(exc.orig, "diag", None), "constraint_name", None))
        return None

    confirmed_row = {
        "state": "CONFIRMED",
        "raw_transcript": "x",
        "transcript_sha256": "a" * 64,
        "reviewed_by": "r",
        "reviewed_at": datetime.now(UTC),
    }
    assert attempt(revision_no=60, **confirmed_row) == "uq_story_transcript_confirmed"
    assert attempt(revision_no=61, state="PENDING") is None  # a PENDING row beside CONFIRMED
    assert attempt(revision_no=62, state="PENDING") == "uq_story_transcript_open"
    assert attempt(revision_no=live["revision_no"]) == "uq_story_transcript_revision"
    assert attempt(revision_no=63, source_asset_ref="parent/other/asset", state="PENDING") is None
    assert (
        attempt(revision_no=64, state="CONFIRMED", raw_transcript="x", transcript_sha256="a" * 64)
        == "ck_story_transcript_confirmed"
    )
    assert attempt(revision_no=65, state="NEEDS_CONFIRMATION") == "ck_story_transcript_hash"
    assert attempt(revision_no=66, state="FAILED") == "ck_story_transcript_failed"
    assert (
        attempt(revision_no=67, origin="ADULT_CORRECTION", state="FAILED", error_code="E")
        == "ck_story_transcript_correction"
    )
    assert attempt(revision_no=68, origin="HUMAN") == "ck_story_transcript_origin"
    assert attempt(revision_no=69, state="DONE") == "ck_story_transcript_state"
    assert attempt(revision_no=70, raw_transcript="x" * 20_001) == "ck_story_transcript_text_bound"
    assert attempt(revision_no=71, adult_corrected_text="") == "ck_story_transcript_text_bound"
    assert attempt(revision_no=0) == "ck_story_transcript_revision_no"
    assert attempt(revision_no=72, transcript_sha256="G" * 64) == "ck_story_transcript_hash"
    assert (
        attempt(revision_no=73, run_input_id=str(uuid4()), source_asset_ref="parent/none/asset")
        == "fk_story_transcript_run_input"
    )


def test_the_run_input_checks_at_the_database(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    latest = input_rows(api, run_id)[-1]
    inputs = story_tables.run_inputs

    def attempt(**values: Any) -> str | None:
        row = {
            key: (null() if value is None and key == "lesson_pin_snapshot" else value)
            for key, value in dict(latest).items()
            if key not in {"run_input_id", "input_revision"}
        }
        row.update(values)
        row["run_input_id"] = str(uuid4())
        row["input_revision"] = 80 + len(str(values))
        try:
            with api.sessions().begin() as db:
                db.execute(insert(inputs).values(**row))
        except IntegrityError as exc:
            return str(exc.orig.diag.constraint_name)  # type: ignore[union-attr]
        return None

    voice = {
        "voice_asset_ref": f"parent/{run_id}/x/original",
        "voice_asset_version": 1,
        "voice_duration_ms": 1000,
    }
    assert attempt(**voice, idea_source="TEXT_AND_VOICE") is None
    assert attempt(**voice, idea_source="TEXT") == "ck_story_run_input_idea"
    assert attempt(**voice, idea_source="VOICE", typed_idea=None) is None
    assert attempt(**voice, idea_source="VOICE") == "ck_story_run_input_idea"  # typed idea set
    assert attempt(idea_source="TEXT_AND_VOICE") == "ck_story_run_input_idea"  # no voice
    assert attempt(typed_idea=None, idea_source="TEXT") == "ck_story_run_input_idea"
    with pytest.raises(DataError):  # the column is a VARCHAR(500): refused before the CHECK
        attempt(typed_idea="x" * 501)
    assert attempt(**{**voice, "voice_duration_ms": 120_001}, idea_source="TEXT_AND_VOICE") == (
        "ck_story_run_input_voice"
    )
    assert attempt(**{**voice, "voice_duration_ms": 0}, idea_source="TEXT_AND_VOICE") == (
        "ck_story_run_input_voice"
    )
    assert attempt(**{**voice, "voice_asset_version": 0}, idea_source="TEXT_AND_VOICE") == (
        "ck_story_run_input_voice"
    )
    assert attempt(voice_duration_ms=1000) == "ck_story_run_input_voice"  # a lone duration
    assert attempt(**{**voice, "voice_duration_ms": None}, idea_source="TEXT_AND_VOICE") == (
        "ck_story_run_input_voice"
    )
    with api.sessions().begin() as db, pytest.raises(IntegrityError):
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == run_id)
            .values(run_state="REVIEWING")
        )
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == run_id)
            .values(run_state="INPUT_REVIEW")
        )


# ---------------------------------------------------- privacy, lifecycle and purge
def test_no_transcript_text_reaches_the_logs_or_the_audit(
    api: IdeaApi, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    caplog.set_level(logging.DEBUG)
    prepared = run_in_input_review(api, speech="một câu bí mật của em bé")
    run_id = prepared.run_id
    assert read_transcript(api, api.parent, run_id).status_code == 200
    assert confirm(api, api.parent, run_id).status_code == 200
    refused = idea(api, api.parent, run_id, text="x", revision=1)
    assert refused.status_code == 409
    assert "bí mật" not in caplog.text and "bí mật" not in refused.text
    with api.sessions()() as db:
        dump = " ".join(
            str(value)
            for row in db.execute(text("select * from core_audit_entries")).all()
            for value in row
        )
    assert "bí mật" not in dump
    # the run read never carries the transcript (l.780, l.1164)
    run_read = api.client.get(f"/v1/story-runs/{run_id}", headers=headers(api.parent))
    assert run_read.status_code == 200 and "bí mật" not in run_read.text
    assert "transcript" not in run_read.text.lower()


def test_cancel_during_asr_then_the_stale_job_changes_nothing_and_the_purge_removes_all(
    api: IdeaApi,
) -> None:
    compose_analyzer(api)
    run_id = new_run(api, api.parent)
    attach_drawing(api, api.parent, run_id, 61, understood=True)
    audio = wav_audio(1000, seed=61)
    api.transcriber.register(sha(audio), SPEECH)
    handle = upload_audio(api, api.parent, run_id, audio)
    assert idea(api, api.parent, run_id, audio_ref=handle).status_code == 202
    (pending,) = live_transcripts(api, run_id)
    voice_key = input_rows(api, run_id)[-1]["voice_asset_ref"]
    assert api.storage.read(voice_key) == audio
    cancel = api.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": revision_of(api, run_id)},
        headers=headers(api.parent, uuid4().hex),
    )
    assert cancel.status_code in {200, 202}, cancel.text
    assert states(api, run_id)[0] == "DELETE_PENDING"
    # the ASR job that was queued before the cancel finishes now: nothing changes
    before = (run_row(api, run_id), transcript_rows(api, run_id))
    ParentSpeechJobRunner(api.sessions(), api.transcriber).run(
        principal_of(api.parent), run_id, pending["transcript_revision_id"]
    )
    assert (run_row(api, run_id), transcript_rows(api, run_id)) == before
    assert api.transcriber.calls == []

    # the purge: the object and the asset row of the audio go, then the transcript and the inputs
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.parent)))
    purge = SqlCoreRunAssetPurge(api.sessions(), api.storage)
    plan = build_plan(purge.closure_candidates(scope, run_id), frozenset())
    refs = sorted(key.asset_ref for key in plan.removable)
    assert voice_key in refs and len(refs) == 3  # the drawing, its derived copy and the audio
    purge.purge_objects(plan)
    assert purge.sweep_run_prefix(scope, run_id).swept_count == 0
    assert api.storage.list_keys(f"parent/{run_id}/") == ()
    purge.delete_rows(plan, frozenset())
    store = SqlStoryLifecycleStore(api.sessions())
    story_plan = store.plan_story_purge(run_id)
    kinds = {item.split(":")[0] for item in story_plan.ids}
    assert {"transcript_revisions", "run_inputs"} <= kinds
    store.purge_story_content(story_plan)
    assert transcript_rows(api, run_id) == [] and input_rows(api, run_id) == []
    assert asset_rows(api, run_id) == []
    assert store.plan_story_purge(run_id).ids == ()


def test_a_voice_asset_referenced_by_another_run_is_retained(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    voice_key = input_rows(api, prepared.run_id)[-1]["voice_asset_ref"]
    other = new_run(api, api.other_parent)
    store = SqlStoryLifecycleStore(api.sessions())
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.parent)))
    assert store.assets_referenced_by_other_runs(
        scope, prepared.run_id, frozenset({voice_key})
    ) == (frozenset())
    with api.sessions().begin() as db:
        db.execute(
            update(story_tables.run_inputs)
            .where(story_tables.run_inputs.c.run_id == other)
            .values(
                voice_asset_ref=voice_key,
                voice_asset_version=1,
                voice_duration_ms=1000,
                idea_source="TEXT_AND_VOICE",
            )
        )
    assert store.assets_referenced_by_other_runs(
        scope, prepared.run_id, frozenset({voice_key})
    ) == (frozenset({voice_key}))


def test_the_run_response_and_history_do_not_expose_the_voice(api: IdeaApi) -> None:
    prepared = run_in_input_review(api)
    run_id = prepared.run_id
    response = api.client.get(f"/v1/story-runs/{run_id}", headers=headers(api.parent))
    assert response.status_code == 200
    lowered = response.text.lower()
    for word in STORAGE_WORDS + ("voice", "audio", "upl_"):
        assert word not in lowered, word
    assert response.json()["story_run"]["run_state"] == "INPUT_REVIEW"
    listing = api.client.get("/v1/story-runs", headers=headers(api.parent))
    assert listing.status_code == 200 and "voice" not in listing.text.lower()


def test_the_concurrent_same_key_idea_is_one_command_and_one_replay(api: IdeaApi) -> None:
    run_id = new_run(api, api.parent)
    revision = revision_of(api, run_id)
    barrier = Barrier(2)

    def send() -> Any:
        barrier.wait(timeout=30)
        return idea(api, api.parent, run_id, key="race-key", text="same idea", revision=revision)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _i: send(), range(2)))
    assert sorted(response.status_code for response in results) == [202, 202]
    assert len(input_rows(api, run_id)) == 2 and len(receipt_rows(api, run_id, "SUBMIT_IDEA")) == 1
    assert wire(results[0]) == wire(results[1])
    assert SPEECH not in " ".join(response.text for response in results)
