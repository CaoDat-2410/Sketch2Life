"""FEAT-066 T-2b: ``POST /v1/story-runs/{id}/assets`` (SRS l.1664) on PostgreSQL.

Runs only against a disposable database whose name contains ``be1_acceptance`` and
``frc08_v3_t2b``. Object storage is the in-memory port by default; when ``T2B_S3_ENDPOINT``,
``T2B_S3_BUCKET``, ``T2B_S3_ACCESS_KEY`` and ``T2B_S3_SECRET_KEY`` are set the module runs against
the local S3Mock target, after the T-2z guard (``check_s3mock_target``: loopback, endpoint and
bucket equal to ``FRC08_ALLOWED_ENDPOINT`` and ``FRC08_ALLOWED_BUCKET``, bucket containing
``frc08`` and ``v3-t2b``, no ambient ``AWS_*`` variable). Only synthetic, in-memory images are
used; no key or bucket is ever deleted by a fixture (the only deletes are the ones under test).
No provider is called: the drawing analyzer is the deterministic fixture.
"""

from __future__ import annotations

import hashlib
import io
import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait as futures_wait
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Barrier, Event, Lock
from typing import Any
from uuid import uuid4

import pytest
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import insert, select, update

from sketch2life.application.ports.core_foundation import LifecycleScope
from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.lesson_documents import (
    MalwareDetected,
    MalwareScanResult,
    scanner_identity_sha256,
)
from sketch2life.application.ports.object_storage import ObjectStorageFailure, StoredObject
from sketch2life.application.ports.parent_story_inputs import (
    DrawingAnalysisResult,
)
from sketch2life.application.ports.parent_story_runs import ParentStoryRunError
from sketch2life.infrastructure.config.settings import get_core_database_settings, get_settings
from sketch2life.infrastructure.documents.local_test_adapters import (
    LocalTestSignatureMediaValidator,
)
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
from sketch2life.infrastructure.persistence.be1_models import AdultIdentityModel
from sketch2life.infrastructure.persistence.core_lifecycle_store import (
    SqlCoreRunAssetPurge,
    build_plan,
)
from sketch2life.infrastructure.persistence.core_models import CoreAssetMetadataModel
from sketch2life.infrastructure.persistence.parent_story_repository import (
    _DRAWING_INPUT_COLUMNS,
    SqlParentStoryRunRepository,
    _next_input_values,
    drawing_attach_fingerprint,
)
from sketch2life.infrastructure.story_inputs.drawing import normalize_drawing
from sketch2life.infrastructure.story_inputs.fixtures import FixtureDrawingAnalyzer
from sketch2life.infrastructure.story_inputs.runner import ParentInputJobRunner
from sketch2life.infrastructure.story_run_lite import tables as story_tables
from sketch2life.infrastructure.uploads.resolvers import parent_scope_ref
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.be1_runtime import get_verified_adult
from tools.local_s3mock_target import check_s3_credentials, check_s3mock_target, ensure_task_bucket
from tools.run_be1_lifecycle_consumer import TargetRefused

ISSUER = "synthetic-t2b-issuer"
TASK_TAG = "v3-t2b"
_S3_VARIABLES = ("T2B_S3_ENDPOINT", "T2B_S3_BUCKET", "T2B_S3_ACCESS_KEY", "T2B_S3_SECRET_KEY")
STORAGE_WORDS = ("bucket", "normalized.png", "parent/", "object_key", "presigned", "s3mock")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_bytes(width: int = 64, height: int = 48, *, seed: int = 0) -> bytes:
    """A synthetic drawing: flat background with a few dots (distinct per ``seed``)."""
    image = Image.new("RGB", (width, height), (245, 245, 235))
    for index in range(1, 6):
        image.putpixel(((index * 7 + seed) % width, (index * 5 + seed * 3) % height), (10, 30, 60))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (80, 40), (200, 120, 60)).save(buffer, format="JPEG")
    return buffer.getvalue()


def webp_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (80, 40), (60, 120, 200)).save(buffer, format="WEBP")
    return buffer.getvalue()


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
    """Delegating storage that records puts and can fail them or the reads on demand."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.puts: list[str] = []
        self.deletes: list[str] = []
        self.fail_put_containing: str | None = None
        self.fail_get_containing: str | None = None
        # (entered, release): the next put signals ``entered`` and waits for ``release``.
        self.put_gate: tuple[Event, Event] | None = None
        self._lock = Lock()

    def put_object(self, key: str, body: Any, **kwargs: Any) -> None:
        if self.fail_put_containing is not None and self.fail_put_containing in key:
            raise ObjectStorageFailure("synthetic put failure")
        gate = self.put_gate
        if gate is not None:
            self.put_gate = None
            gate[0].set()
            assert gate[1].wait(timeout=60)
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
        return MalwareScanResult("t2b-allowlist", "1", "CLEAN")


@dataclass
class InputsApi:
    app: FastAPI
    client: TestClient
    storage: FaultStorage
    scanner: AllowlistScanner
    analyzer: FixtureDrawingAnalyzer
    parent: str
    other_parent: str
    teacher: str
    real_s3: bool = False

    def sessions(self) -> Any:
        return self.app.state.be1_runtime.session_factory


def _s3_storage() -> Any | None:
    if not all(os.environ.get(name) for name in _S3_VARIABLES):
        return None
    endpoint = os.environ["T2B_S3_ENDPOINT"]
    bucket = os.environ["T2B_S3_BUCKET"]
    access_key = os.environ["T2B_S3_ACCESS_KEY"]
    secret_key = os.environ["T2B_S3_SECRET_KEY"]
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
def api(monkeypatch: pytest.MonkeyPatch) -> Iterator[InputsApi]:
    database_url = os.environ.get("BE1_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("set BE1_TEST_DATABASE_URL to a disposable PostgreSQL database")
    database_name = database_url.rsplit("/", 1)[-1]
    if "be1_acceptance" not in database_name or "frc08_v3_t2b" not in database_name:
        pytest.fail("BE1_TEST_DATABASE_URL must be a disposable frc08_v3_t2b*be1_acceptance db")
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
    parent, other_parent = f"synthetic-t2b-parent-{token}", f"synthetic-t2b-parent2-{token}"
    teacher = f"synthetic-t2b-teacher-{token}"
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
    analyzer = FixtureDrawingAnalyzer()
    app.state.lesson_library_storage = storage
    app.state.lesson_document_scanner = scanner
    app.state.upload_media_validator = LocalTestSignatureMediaValidator(env="test")
    app.dependency_overrides[get_verified_adult] = verified
    try:
        with TestClient(app) as client:
            yield InputsApi(
                app,
                client,
                storage,
                scanner,
                analyzer,
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


def new_run(
    api: InputsApi, owner: str, *, state: str = "INPUT_PROCESSING", hold_slot: bool = False
) -> str:
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
                run_state=state,
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
                typed_idea="A friendly dragon learns to share",
                idea_source="TEXT",
                source_profile_revision_ref=str(uuid4()),
                context_revision=1,
                context_snapshot={"synthetic": True},
                context_snapshot_sha256="c" * 64,
                context_confirmed_by=scope_ref,
                context_confirmed_at=now,
                created_at=now,
            )
        )
    return run_id


def create_upload(api: InputsApi, owner: str, run_id: str, data: bytes, media_type: str) -> Any:
    return api.client.post(
        "/v1/upload-sessions",
        json={
            "purpose": "RUN_ARTWORK",
            "target_ref": run_id,
            "media_type": media_type,
            "expected_size_bytes": len(data),
            "expected_sha256": sha(data),
        },
        headers=headers(owner, uuid4().hex),
    )


def upload(
    api: InputsApi, owner: str, run_id: str, data: bytes, media_type: str = "image/png"
) -> str:
    """Create, fill and complete an artwork upload; returns the opaque ``asset_ref``."""
    api.scanner.clean.add(sha(data))
    created = create_upload(api, owner, run_id, data, media_type)
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


def attach(
    api: InputsApi,
    owner: str,
    run_id: str,
    handle: str,
    *,
    key: str | None = None,
    **extra: Any,
) -> Any:
    return api.client.post(
        f"/v1/story-runs/{run_id}/assets",
        json={"asset_ref": handle, **extra},
        headers=headers(owner, key or uuid4().hex),
    )


def code_of(response: Any) -> str:
    return str(response.json()["code"])


def run_row(api: InputsApi, run_id: str) -> Any:
    with api.sessions()() as db:
        return (
            db.execute(
                select(story_tables.story_runs).where(story_tables.story_runs.c.run_id == run_id)
            )
            .mappings()
            .one()
        )


def input_rows(api: InputsApi, run_id: str) -> list[Any]:
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


def understanding_rows(api: InputsApi, run_id: str) -> list[Any]:
    with api.sessions()() as db:
        return list(
            db.execute(
                select(story_tables.understanding_revisions)
                .where(story_tables.understanding_revisions.c.run_id == run_id)
                .order_by(story_tables.understanding_revisions.c.revision_no)
            )
            .mappings()
            .all()
        )


def receipt_rows(api: InputsApi, run_id: str, operation: str = "ATTACH_ASSET") -> list[Any]:
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


def asset_rows(api: InputsApi, run_id: str) -> list[Any]:
    with api.sessions()() as db:
        rows = db.scalars(select(CoreAssetMetadataModel)).all()
        return [row for row in rows if run_id in row.source_refs]


def lineage_rows(api: InputsApi, run_id: str) -> list[Any]:
    lineage = story_tables.asset_lineage
    with api.sessions()() as db:
        return list(
            db.execute(select(lineage).where(lineage.c.source_asset_ref.like(f"parent/{run_id}/%")))
            .mappings()
            .all()
        )


def derived_sha(data: bytes, media_type: str = "image/png") -> str:
    return normalize_drawing(data, declared_media_type=media_type).sha256


def compose_analyzer(api: InputsApi) -> None:
    api.app.state.drawing_analyzer = api.analyzer


def wire(response: Any) -> tuple[int, dict[str, Any]]:
    body = response.json()
    return response.status_code, {
        k: v for k, v in body.items() if k not in {"request_id", "correlation_id"}
    }


def current_candidate(api: InputsApi, owner: str, run_id: str) -> Any:
    with api.sessions()() as db:
        return SqlParentStoryRunRepository(db).get_run(principal=principal_of(owner), run_id=run_id)


# ---------------------------------------------------------------------------- happy path
def test_upload_then_attach_writes_derived_asset_lineage_input_run_and_receipt(
    api: InputsApi,
) -> None:
    run_id = new_run(api, api.parent)
    data = png_bytes(3000, 2000)  # six megapixels: the derived copy is scaled down
    handle = upload(api, api.parent, run_id, data)
    before = run_row(api, run_id)
    response = attach(api, api.parent, run_id, handle, key="attach-1")
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["asset_ref"] == handle
    assert {k: body[k] for k in body if k != "request_id"} == {
        "story_run_id": run_id,
        "asset_ref": handle,
        "asset_kind": "DRAWING",
        "asset_state": "READY",
        "input_revision": 2,
        "run_revision": before["revision"] + 1,
        "run_state": "INPUT_PROCESSING",
        "analysis_state": "QUEUED",
    }
    assert "job" not in body
    assert response.headers["Content-Location"] == f"/v1/story-runs/{run_id}"
    for word in STORAGE_WORDS:
        assert word not in response.text.lower(), word

    run = run_row(api, run_id)
    assert (run["run_state"], run["job_state"], run["retryable"], run["error_code"]) == (
        "INPUT_PROCESSING",
        "QUEUED",
        False,
        None,
    )
    assert run["current_input_revision"] == 2
    assert run["revision"] == before["revision"] + 1 and run["version"] == before["version"] + 1

    inputs = input_rows(api, run_id)
    assert [row["input_revision"] for row in inputs] == [1, 2]
    first, second = inputs
    assert first["original_asset_ref"] is None  # the earlier input is history, untouched
    assert second["original_media_type"] == "image/png" and second["original_size_bytes"] == len(
        data
    )
    assert second["original_sha256"] == sha(data)
    assert second["derived_media_type"] == "image/png"
    assert second["derived_asset_ref"] == second["original_asset_ref"].replace(
        "/original", "/normalized.png"
    )
    for column in (
        "typed_idea",
        "idea_source",
        "source_profile_revision_ref",
        "context_revision",
        "context_snapshot",
        "context_snapshot_sha256",
        "context_confirmed_by",
        "context_confirmed_at",
        "lesson_pin_snapshot",
        "lesson_pin_snapshot_sha256",
    ):
        assert second[column] == first[column], column
    assert run["asset_ref"] == second["original_asset_ref"]
    assert run["derived_asset_ref"] == second["derived_asset_ref"]

    original_bytes = api.storage.read(second["original_asset_ref"])
    derived_bytes = api.storage.read(second["derived_asset_ref"])
    assert original_bytes == data  # the original is never resized or rewritten
    assert derived_bytes is not None and sha(derived_bytes) == second["derived_sha256"]
    assert second["derived_size_bytes"] == len(derived_bytes) <= 5_000_000
    with Image.open(io.BytesIO(derived_bytes)) as image:
        assert image.format == "PNG" and image.mode == "RGB"
        assert image.width * image.height <= 2_000_000

    assets = {row.asset_ref: row for row in asset_rows(api, run_id)}
    assert set(assets) == {second["original_asset_ref"], second["derived_asset_ref"]}
    derived_row = assets[second["derived_asset_ref"]]
    assert derived_row.derived_from_ref == second["original_asset_ref"]
    assert derived_row.owner_scope_kind == "PARENT_ACCOUNT"
    assert derived_row.owner_scope_ref == parent_scope_ref(principal_of(api.parent))
    assert derived_row.source_refs == [run_id] and derived_row.media_type == "image/png"
    (edge,) = lineage_rows(api, run_id)
    assert edge["transform_kind"] == "NORMALIZE_DRAWING_IMAGE"
    assert edge["transform_version"] == "PILLOW_RGB_PNG_V2"
    assert (edge["scanner_name"], edge["scanner_version"]) == ("t2b-allowlist", "1")
    assert edge["scanner_sha256"] == scanner_identity_sha256("t2b-allowlist", "1")
    assert edge["source_sha256"] == sha(data) and edge["derived_sha256"] == sha(derived_bytes)

    (receipt,) = receipt_rows(api, run_id)
    assert receipt["state"] == "FINAL" and receipt["response_status"] == 202
    assert (
        receipt["idempotency_scope_kind"] == "STORY_RUN"
        and receipt["idempotency_scope_ref"] == run_id
    )
    stored = receipt["response_body"]
    assert stored == {
        "input_revision": 2,
        "run_revision": before["revision"] + 1,
        "run_state": "INPUT_PROCESSING",
        "analysis_state": "QUEUED",
    }


def test_jpeg_and_webp_attach(api: InputsApi) -> None:
    for data, media_type in ((jpeg_bytes(), "image/jpeg"), (webp_bytes(), "image/webp")):
        run_id = new_run(api, api.parent)
        handle = upload(api, api.parent, run_id, data, media_type)
        response = attach(api, api.parent, run_id, handle)
        assert response.status_code == 202, response.text
        row = input_rows(api, run_id)[-1]
        assert row["original_media_type"] == media_type and row["derived_media_type"] == "image/png"


def test_without_an_analyzer_the_run_waits_queued(api: InputsApi) -> None:
    assert api.app.state.drawing_analyzer is None
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    assert attach(api, api.parent, run_id, handle).status_code == 202
    run = run_row(api, run_id)
    assert (run["run_state"], run["job_state"]) == ("INPUT_PROCESSING", "QUEUED")
    assert understanding_rows(api, run_id) == []


def test_the_purge_plan_stays_removable_for_both_assets_and_the_lineage(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    assert attach(api, api.parent, run_id, handle).status_code == 202
    original, derived = sorted(row.asset_ref for row in asset_rows(api, run_id))
    scope = LifecycleScope("PARENT_ACCOUNT", parent_scope_ref(principal_of(api.parent)))
    purge = SqlCoreRunAssetPurge(api.sessions(), api.storage)
    plan = build_plan(purge.closure_candidates(scope, run_id), frozenset())
    assert plan.retained == ()
    assert sorted(key.asset_ref for key in plan.removable) == [original, derived]
    purge.purge_objects(plan)
    assert purge.sweep_run_prefix(scope, run_id).swept_count == 0
    assert api.storage.list_keys(f"parent/{run_id}/") == ()
    purge.delete_rows(plan, frozenset())
    assert asset_rows(api, run_id) == [] and lineage_rows(api, run_id) == []


# ------------------------------------------------------------------------------ idempotency
def test_a_replay_returns_the_same_answer_and_writes_nothing(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    first = attach(api, api.parent, run_id, handle, key="replay-1")
    assert first.status_code == 202
    puts = len(api.storage.puts)
    run_before = run_row(api, run_id)
    counts = (
        len(input_rows(api, run_id)),
        len(asset_rows(api, run_id)),
        len(receipt_rows(api, run_id)),
    )
    second = attach(api, api.parent, run_id, handle, key="replay-1")
    assert second.status_code == 202
    assert wire(second) == wire(first)
    assert len(api.storage.puts) == puts
    assert run_row(api, run_id) == run_before
    assert counts == (
        len(input_rows(api, run_id)),
        len(asset_rows(api, run_id)),
        len(receipt_rows(api, run_id)),
    )
    assert len(lineage_rows(api, run_id)) == 1


def test_the_same_key_with_another_body_is_400_invalid_idempotency_key(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    other = upload(api, api.parent, run_id, png_bytes(seed=2))
    assert attach(api, api.parent, run_id, handle, key="mix-1").status_code == 202
    mixed = attach(api, api.parent, run_id, other, key="mix-1")
    assert mixed.status_code == 400 and code_of(mixed) == "INVALID_IDEMPOTENCY_KEY"
    with_revision = attach(api, api.parent, run_id, handle, key="mix-1", expected_run_revision=9)
    assert with_revision.status_code == 400 and code_of(with_revision) == "INVALID_IDEMPOTENCY_KEY"


# ------------------------------------------------------------------------ one drawing and revisions
def test_a_second_drawing_is_409_and_so_is_the_same_asset_again(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    assert attach(api, api.parent, run_id, handle).status_code == 202
    again = attach(api, api.parent, run_id, handle)  # another key, the same asset
    assert again.status_code == 409 and code_of(again) == "INVALID_STATE_TRANSITION"
    other = upload_after_attach_is_refused(api, run_id)
    assert other == 409
    assert len(input_rows(api, run_id)) == 2 and len(lineage_rows(api, run_id)) == 1


def upload_after_attach_is_refused(api: InputsApi, run_id: str) -> int:
    """While the analysis is queued the run accepts no second drawing, not even an upload."""
    data = png_bytes(seed=5)
    api.scanner.clean.add(sha(data))
    return int(create_upload(api, api.parent, run_id, data, "image/png").status_code)


def test_a_stale_run_revision_is_409_with_the_current_version(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    current = run_row(api, run_id)["revision"]
    stale = attach(api, api.parent, run_id, handle, expected_run_revision=current + 5)
    assert stale.status_code == 409
    assert code_of(stale) == "STALE_REVISION"
    assert stale.json()["current_version"] == current
    assert input_rows(api, run_id)[-1]["original_asset_ref"] is None
    fresh = attach(api, api.parent, run_id, handle, expected_run_revision=current)
    assert fresh.status_code == 202, fresh.text
    assert fresh.json()["run_revision"] == current + 1


def test_a_run_outside_the_attach_states_is_409(api: InputsApi) -> None:
    for state in ("PREPARATION_REVIEW", "SCRIPT_REVIEW", "FAILED", "COMPLETED"):
        run_id = new_run(api, api.parent)
        handle = upload(api, api.parent, run_id, png_bytes())
        with api.sessions().begin() as db:
            db.execute(
                update(story_tables.story_runs)
                .where(story_tables.story_runs.c.run_id == run_id)
                .values(run_state=state)
            )
        response = attach(api, api.parent, run_id, handle)
        assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION", (
            state
        )
        assert len(input_rows(api, run_id)) == 1


# --------------------------------------------------------------------------------- analysis
def test_the_analysis_runs_after_the_response_and_the_run_reaches_subject_review(
    api: InputsApi,
) -> None:
    compose_analyzer(api)
    run_id = new_run(api, api.parent)
    data = png_bytes()
    api.analyzer.register(
        derived_sha(data), DrawingAnalysisResult("dragon", ("wings", "tail"), 0.9, 1, True)
    )
    handle = upload(api, api.parent, run_id, data)
    response = attach(api, api.parent, run_id, handle)
    assert response.status_code == 202 and response.json()["analysis_state"] == "QUEUED"
    run = run_row(api, run_id)
    assert (run["run_state"], run["job_state"], run["subject_label"]) == (
        "SUBJECT_REVIEW",
        "SUCCEEDED",
        "dragon",
    )
    assert run["understanding_revision"] == 1
    (understanding,) = understanding_rows(api, run_id)
    assert understanding["run_input_id"] == input_rows(api, run_id)[-1]["run_input_id"]
    assert understanding["result_snapshot"]["result"]["candidate_subject"] == "dragon"
    assert "warnings" not in understanding["result_snapshot"]
    record = current_candidate(api, api.parent, run_id)
    assert record.candidate is not None and record.candidate["candidate_subject"] == "dragon"
    assert len(api.analyzer.calls) == 1 and api.analyzer.calls[0].input_revision == 2


def test_a_topic_mismatch_is_stored_as_a_warning_beside_the_candidate(api: InputsApi) -> None:
    compose_analyzer(api)
    run_id = new_run(api, api.parent)
    data = png_bytes()
    api.analyzer.register(
        derived_sha(data), DrawingAnalysisResult("car", ("wheels",), 0.8, 1, False)
    )
    handle = upload(api, api.parent, run_id, data)
    assert attach(api, api.parent, run_id, handle).status_code == 202
    (understanding,) = understanding_rows(api, run_id)
    assert understanding["result_snapshot"]["warnings"] == [{"code": "TOPIC_MISMATCH"}]
    assert "warnings" not in understanding["result_snapshot"]["result"]


def test_an_unknown_input_is_a_recoverable_failure_not_an_invented_answer(api: InputsApi) -> None:
    compose_analyzer(api)  # the fixture knows no hash
    run_id = new_run(api, api.parent, hold_slot=True)
    handle = upload(api, api.parent, run_id, png_bytes())
    assert attach(api, api.parent, run_id, handle).status_code == 202
    run = run_row(api, run_id)
    # T-2c settle rule (l.394): a recoverable analysis failure is reviewed in INPUT_REVIEW.
    assert (run["run_state"], run["job_state"], run["retryable"], run["error_code"]) == (
        "INPUT_REVIEW",
        "FAILED",
        True,
        "DRAWING_ANALYSIS_UNAVAILABLE",
    )
    assert understanding_rows(api, run_id) == []


def test_multi_child_fails_recoverably_keeps_the_slot_and_allows_one_retake(
    api: InputsApi,
) -> None:
    compose_analyzer(api)
    run_id = new_run(api, api.parent, hold_slot=True)
    first = png_bytes(seed=1)
    second = png_bytes(seed=2)
    third = png_bytes(seed=3)
    api.analyzer.register(
        derived_sha(first), DrawingAnalysisResult("kids", ("hands",), 0.9, child_count=2)
    )
    api.analyzer.register(
        derived_sha(second), DrawingAnalysisResult("kids", ("hands",), 0.9, child_count=3)
    )
    api.analyzer.register(derived_sha(third), DrawingAnalysisResult("kid", ("hands",), 0.9, 1))
    handle_one = upload(api, api.parent, run_id, first)
    assert attach(api, api.parent, run_id, handle_one).status_code == 202
    failed = run_row(api, run_id)
    assert (failed["run_state"], failed["job_state"], failed["retryable"]) == (
        "INPUT_REVIEW",  # T-2c: the recoverable failure moved here from INPUT_PROCESSING (l.394)
        "FAILED",
        True,
    )
    assert failed["error_code"] == "MULTI_CHILD_NOT_SUPPORTED"
    assert failed["active_owner_parent_account_id"] is not None  # the slot is kept (not FAILED)

    handle_two = upload(api, api.parent, run_id, second)  # the upload is accepted for the retake
    retake = attach(api, api.parent, run_id, handle_two)
    assert retake.status_code == 202, retake.text
    assert retake.json()["input_revision"] == 3
    again = run_row(api, run_id)
    assert again["error_code"] == "MULTI_CHILD_NOT_SUPPORTED" and again["job_state"] == "FAILED"
    assert again["run_state"] == "INPUT_REVIEW"
    # The one retake is used: neither an upload session nor an attach is accepted again.
    api.scanner.clean.add(sha(third))
    assert create_upload(api, api.parent, run_id, third, "image/png").status_code == 409
    assert len(input_rows(api, run_id)) == 3


def test_a_retake_after_subject_review_replaces_the_drawing_and_keeps_history(
    api: InputsApi,
) -> None:
    compose_analyzer(api)
    run_id = new_run(api, api.parent, hold_slot=True)
    first, second, third = png_bytes(seed=1), png_bytes(seed=2), png_bytes(seed=3)
    api.analyzer.register(
        derived_sha(first), DrawingAnalysisResult("dog", ("ears",), 0.7, 1, False)
    )
    api.analyzer.register(derived_sha(second), DrawingAnalysisResult("cat", ("whiskers",), 0.9, 1))
    handle_one = upload(api, api.parent, run_id, first)
    assert attach(api, api.parent, run_id, handle_one).status_code == 202
    assert run_row(api, run_id)["run_state"] == "SUBJECT_REVIEW"
    assert current_candidate(api, api.parent, run_id).candidate["candidate_subject"] == "dog"

    # A retake with the analyzer off first: the run returns to INPUT_PROCESSING and no longer
    # reports the replaced drawing's subject; the old input and understanding stay as history.
    api.app.state.drawing_analyzer = None
    handle_two = upload(api, api.parent, run_id, second)
    handle_three = upload(api, api.parent, run_id, third)  # created while a retake is still open
    retake = attach(api, api.parent, run_id, handle_two, key="retake-1")
    assert retake.status_code == 202, retake.text
    assert retake.json()["input_revision"] == 3
    run = run_row(api, run_id)
    assert (run["run_state"], run["job_state"], run["current_input_revision"]) == (
        "INPUT_PROCESSING",
        "QUEUED",
        3,
    )
    assert run["subject_label"] is None and run["understanding_revision"] is None
    assert run["active_owner_parent_account_id"] is not None
    record = current_candidate(api, api.parent, run_id)
    assert record.candidate is None and record.subject_label is None
    inputs = input_rows(api, run_id)
    assert [row["input_revision"] for row in inputs] == [1, 2, 3]
    assert inputs[1]["original_sha256"] == sha(first) and inputs[2]["original_sha256"] == sha(
        second
    )
    assert inputs[2]["typed_idea"] == inputs[0]["typed_idea"]
    assert inputs[2]["context_confirmed_at"] == inputs[0]["context_confirmed_at"]
    assert len(understanding_rows(api, run_id)) == 1  # history kept
    assert len(asset_rows(api, run_id)) == 5 and len(lineage_rows(api, run_id)) == 2
    # The retake is used; a third drawing is refused, by upload and by attach.
    assert create_upload(api, api.parent, run_id, png_bytes(seed=4), "image/png").status_code == 409
    refused = attach(api, api.parent, run_id, handle_three)
    assert refused.status_code == 409 and code_of(refused) == "INVALID_STATE_TRANSITION"
    # Composing the analyzer and replaying the retake changes nothing; a fresh run of the job
    # for the current input answers for the new drawing.
    replay = attach(api, api.parent, run_id, handle_two, key="retake-1")
    assert replay.status_code == 202 and wire(replay) == wire(retake)
    compose_analyzer(api)
    ParentInputJobRunner(api.sessions(), api.analyzer).run(principal_of(api.parent), run_id, 3)
    after = run_row(api, run_id)
    assert (after["run_state"], after["subject_label"], after["understanding_revision"]) == (
        "SUBJECT_REVIEW",
        "cat",
        2,
    )
    record = current_candidate(api, api.parent, run_id)
    assert record.candidate is not None and record.candidate["candidate_subject"] == "cat"


def test_a_stale_analysis_result_is_discarded(api: InputsApi) -> None:
    run_id = new_run(api, api.parent, hold_slot=True)
    first, second = png_bytes(seed=1), png_bytes(seed=2)
    handle_one = upload(api, api.parent, run_id, first)
    assert attach(api, api.parent, run_id, handle_one).status_code == 202
    principal = principal_of(api.parent)
    with api.sessions()() as db:
        repo = SqlParentStoryRunRepository(db)
        assert repo.start_drawing_analysis(
            principal=principal, run_id=run_id, expected_input_revision=2
        )
        assert repo.fail_drawing_analysis_recoverable(
            principal=principal,
            run_id=run_id,
            error_code="DRAWING_ANALYSIS_UNAVAILABLE",
            expected_input_revision=2,
        )
    handle_two = upload(api, api.parent, run_id, second)
    assert attach(api, api.parent, run_id, handle_two).status_code == 202  # retake: input 3
    before = run_row(api, run_id)
    with api.sessions()() as db:
        repo = SqlParentStoryRunRepository(db)
        with pytest.raises(ParentStoryRunError) as raised:
            repo.record_understanding(
                principal=principal,
                run_id=run_id,
                result_snapshot={"result": {"candidate_subject": "old"}},
                candidate_subject="old",
                confidence=0.5,
                expected_input_revision=2,
            )
        assert (raised.value.status_code, raised.value.code) == (409, "PARENT_STORY_INPUT_REPLACED")
        assert not repo.start_drawing_analysis(
            principal=principal, run_id=run_id, expected_input_revision=2
        )
        assert not repo.fail_drawing_analysis_recoverable(
            principal=principal, run_id=run_id, error_code="X", expected_input_revision=2
        )
    assert run_row(api, run_id) == before
    assert understanding_rows(api, run_id) == []
    compose_analyzer(api)
    api.analyzer.register(derived_sha(first), DrawingAnalysisResult("old", ("a",), 0.5, 1))
    ParentInputJobRunner(api.sessions(), api.analyzer).run(principal, run_id, 2)  # stale work
    assert run_row(api, run_id) == before and api.analyzer.calls == []


# ------------------------------------------------------------- uniform 404 and wrong purpose
def test_wrong_role_foreign_run_foreign_asset_and_unknown_asset_look_the_same(
    api: InputsApi,
) -> None:
    run_id = new_run(api, api.parent)
    own_handle = upload(api, api.parent, run_id, png_bytes(seed=1))
    other_run = new_run(api, api.other_parent)
    foreign_handle = upload(api, api.other_parent, other_run, png_bytes(seed=2))
    second_own_run = new_run(api, api.parent)
    other_run_handle = upload(api, api.parent, second_own_run, png_bytes(seed=3))
    unscanned_id = create_upload(api, api.parent, run_id, png_bytes(seed=4), "image/png").json()[
        "upload_id"
    ]  # created, never completed
    unknown_handle = "upl_00000000-0000-4000-8000-000000000000"
    lesson_upload_id = insert_completed_session(api, api.parent, run_id, purpose="LESSON_SOURCE")

    reference = attach(api, api.parent, str(uuid4()), own_handle)  # unknown run
    assert reference.status_code == 404 and code_of(reference) == "RESOURCE_NOT_FOUND"
    cases = {
        "foreign run": attach(api, api.parent, other_run, own_handle),
        "wrong role": attach(api, api.teacher, run_id, own_handle),
        "foreign asset": attach(api, api.parent, run_id, foreign_handle),
        "other run's asset": attach(api, api.parent, run_id, other_run_handle),
        "unknown asset": attach(api, api.parent, run_id, unknown_handle),
        "open session": attach(api, api.parent, run_id, f"upl_{unscanned_id}"),
        "lesson asset": attach(api, api.parent, run_id, f"upl_{lesson_upload_id}"),
    }
    for name, response in cases.items():
        assert wire(response) == wire(reference), name
    # Nothing was attached by any of those.
    assert input_rows(api, run_id)[-1]["original_asset_ref"] is None
    assert attach(api, api.parent, run_id, own_handle).status_code == 202  # the real one works


def insert_completed_session(
    api: InputsApi, owner: str, run_id: str, *, purpose: str, scan_verdict: str = "CLEAN"
) -> str:
    """A COMPLETED, scanned session row of ``purpose`` for the run (no HTTP path creates some)."""
    upload_id = str(uuid4())
    now = datetime.now(UTC)
    with api.sessions().begin() as db:
        db.execute(
            UPLOAD_SESSIONS.insert().values(
                upload_session_id=upload_id,
                organization_id=None,
                owner_scope_kind="PARENT_ACCOUNT",
                owner_scope_ref=parent_scope_ref(principal_of(owner)),
                owner_principal_ref=owner,
                purpose=purpose,
                target_ref=run_id,
                safe_file_name="artwork.bin",
                expected_media_type="audio/wav" if purpose == "RUN_AUDIO" else "image/png",
                expected_size_bytes=100,
                expected_sha256="d" * 64,
                chunk_size_bytes=4194304,
                expected_parts=1,
                state="COMPLETED",
                expires_at=now,
                final_asset_ref=f"parent/{run_id}/{uuid4().hex}/original",
                completed_at=now,
                scan_verdict=scan_verdict,
                scanner_name="t2b-allowlist",
                scanner_version="1",
            )
        )
    return upload_id


def test_a_completed_audio_session_of_the_same_run_answers_415(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    upload_id = insert_completed_session(api, api.parent, run_id, purpose="RUN_AUDIO")
    response = attach(api, api.parent, run_id, f"upl_{upload_id}")
    assert response.status_code == 415 and code_of(response) == "UNSUPPORTED_MEDIA_TYPE"
    # Another Parent's audio session answers the uniform 404, never 415.
    other_run = new_run(api, api.other_parent)
    other_response = attach(api, api.other_parent, other_run, f"upl_{upload_id}")
    assert other_response.status_code == 404
    # An unscanned or infected completed session is not an asset at all: 404.
    infected = insert_completed_session(
        api, api.parent, run_id, purpose="RUN_ARTWORK", scan_verdict="INFECTED"
    )
    assert attach(api, api.parent, run_id, f"upl_{infected}").status_code == 404


# ------------------------------------------------------------------------- image validation
def test_more_than_forty_megapixels_is_422_and_changes_nothing(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    buffer = io.BytesIO()
    Image.new("1", (8001, 5000), 1).save(buffer, format="PNG")
    data = buffer.getvalue()
    handle = upload(api, api.parent, run_id, data)
    before = run_row(api, run_id)
    response = attach(api, api.parent, run_id, handle)
    assert response.status_code == 422 and code_of(response) == "IMAGE_DIMENSIONS_EXCEEDED"
    assert run_row(api, run_id) == before
    assert len(input_rows(api, run_id)) == 1 and lineage_rows(api, run_id) == []
    assert not [key for key in api.storage.list_keys(f"parent/{run_id}/") if key.endswith(".png")]


def test_a_corrupt_image_is_422_content_mismatch(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    data = b"\x89PNG\r\n\x1a\n" + b"garbage-not-a-real-image" * 8
    handle = upload(api, api.parent, run_id, data)
    response = attach(api, api.parent, run_id, handle)
    assert response.status_code == 422 and code_of(response) == "UPLOAD_CONTENT_MISMATCH"
    assert len(input_rows(api, run_id)) == 1


def test_a_missing_or_tampered_stored_original_is_422(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    data = png_bytes()
    handle = upload(api, api.parent, run_id, data)
    key = f"parent/{run_id}/"
    (original,) = [k for k in api.storage.list_keys(key) if k.endswith("/original")]
    api.storage.inner.delete_object(original)
    gone = attach(api, api.parent, run_id, handle)
    assert gone.status_code == 422 and code_of(gone) == "UPLOAD_INCOMPLETE"
    api.storage.inner.put_object(
        original,
        io.BytesIO(png_bytes(seed=9)),
        content_type="image/png",
        content_length=len(png_bytes(seed=9)),
        metadata={},
    )
    tampered = attach(api, api.parent, run_id, handle)
    assert tampered.status_code == 422 and code_of(tampered) == "UPLOAD_CHECKSUM_MISMATCH"
    assert len(input_rows(api, run_id)) == 1


def test_storage_faults_are_503_and_a_retry_succeeds_without_leftovers(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    api.storage.fail_get_containing = "/original"
    read_fault = attach(api, api.parent, run_id, handle, key="fault-key")
    assert read_fault.status_code == 503 and code_of(read_fault) == "STORAGE_UNAVAILABLE"
    assert read_fault.json()["retryable"] is True
    api.storage.fail_get_containing = None
    api.storage.fail_put_containing = "normalized.png"
    write_fault = attach(api, api.parent, run_id, handle, key="fault-key")
    assert write_fault.status_code == 503 and code_of(write_fault) == "STORAGE_UNAVAILABLE"
    assert not [k for k in api.storage.list_keys(f"parent/{run_id}/") if k.endswith(".png")]
    assert receipt_rows(api, run_id) == [] and len(input_rows(api, run_id)) == 1
    api.storage.fail_put_containing = None
    retried = attach(api, api.parent, run_id, handle, key="fault-key")
    assert retried.status_code == 202, retried.text
    assert len(input_rows(api, run_id)) == 2 and len(receipt_rows(api, run_id)) == 1
    assert len(lineage_rows(api, run_id)) == 1


# --------------------------------------------------------------------------- concurrency
def test_two_keys_racing_on_one_asset_give_one_202_one_409_and_a_readable_winner_object(
    api: InputsApi,
) -> None:
    for round_number in range(3):
        run_id = new_run(api, api.parent)
        handle = upload(api, api.parent, run_id, png_bytes(seed=round_number))
        barrier = Barrier(2)

        def call(
            key: str, barrier: Barrier = barrier, run_id: str = run_id, handle: str = handle
        ) -> Any:
            barrier.wait(timeout=30)
            return attach(api, api.parent, run_id, handle, key=key)

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(call, ["race-a", "race-b"]))
        statuses = sorted(result.status_code for result in results)
        assert statuses == [202, 409], [result.text for result in results]
        loser = next(result for result in results if result.status_code == 409)
        assert code_of(loser) == "INVALID_STATE_TRANSITION"
        inputs = input_rows(api, run_id)
        assert len(inputs) == 2 and len(lineage_rows(api, run_id)) == 1
        derived_key = inputs[-1]["derived_asset_ref"]
        stored = api.storage.read(derived_key)
        assert stored is not None and sha(stored) == inputs[-1]["derived_sha256"]
        assert api.storage.puts.count(derived_key) == 1  # the loser never touched storage
        assert derived_key not in api.storage.deletes
        assert len(receipt_rows(api, run_id)) == 1


def test_the_same_key_racing_twice_is_one_attach_and_one_replay(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    barrier = Barrier(2)

    def call(_index: int) -> Any:
        barrier.wait(timeout=30)
        return attach(api, api.parent, run_id, handle, key="same-key")

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(call, [0, 1]))
    assert [result.status_code for result in results] == [202, 202], [r.text for r in results]
    assert wire(results[0]) == wire(results[1])
    assert len(input_rows(api, run_id)) == 2 and len(receipt_rows(api, run_id)) == 1


def test_a_replay_that_arrives_while_the_first_attach_commits_is_the_stored_202(
    api: InputsApi,
) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    entered, release = Event(), Event()
    api.storage.put_gate = (entered, release)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(attach, api, api.parent, run_id, handle, key="held-key")
        assert entered.wait(timeout=30)  # the first attach holds the run lock, before commit
        second = pool.submit(attach, api, api.parent, run_id, handle, key="held-key")
        finished, pending = futures_wait([second], timeout=1.0)
        assert not finished and pending  # the replay waits for the first attach (T2B-R-3)
        release.set()
        results = [first.result(timeout=60), second.result(timeout=60)]
    assert [result.status_code for result in results] == [202, 202], [r.text for r in results]
    assert wire(results[0]) == wire(results[1])
    assert len(input_rows(api, run_id)) == 2 and len(receipt_rows(api, run_id)) == 1


def test_the_pre_check_reads_the_run_under_its_row_lock(api: InputsApi) -> None:
    run_id = new_run(api, api.parent)
    fingerprint = drawing_attach_fingerprint("upl_" + str(uuid4()), None)
    holder = api.sessions()()
    try:
        holder.execute(
            select(story_tables.story_runs.c.run_id)
            .where(story_tables.story_runs.c.run_id == run_id)
            .with_for_update()
        ).one()

        def prepare() -> Any:
            with api.sessions()() as db:
                return SqlParentStoryRunRepository(db).prepare_drawing_attach(
                    principal=principal_of(api.parent),
                    run_id=run_id,
                    idempotency_key="lock-key",
                    fingerprint=fingerprint,
                    expected_run_revision=None,
                )

        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(prepare)
            finished, _ = futures_wait([pending], timeout=1.0)
            assert not finished  # blocked on the row lock held by the other transaction
            holder.rollback()
            assert pending.result(timeout=60) is None
    finally:
        holder.close()


def test_a_second_input_row_without_a_new_drawing_keeps_the_candidate(api: InputsApi) -> None:
    compose_analyzer(api)
    run_id = new_run(api, api.parent, hold_slot=True)
    data = png_bytes(seed=1)
    api.analyzer.register(derived_sha(data), DrawingAnalysisResult("dog", ("ears",), 0.7, 1))
    assert attach(api, api.parent, run_id, upload(api, api.parent, run_id, data)).status_code == 202
    assert run_row(api, run_id)["run_state"] == "SUBJECT_REVIEW"
    # T-2c writes a text-only input revision by copying every column forward (T2B-R-2).
    with api.sessions()() as db:
        previous = (
            db.execute(
                select(story_tables.run_inputs).where(
                    story_tables.run_inputs.c.run_id == run_id,
                    story_tables.run_inputs.c.input_revision == 2,
                )
            )
            .mappings()
            .one()
        )
        overrides = {name: previous[name] for name in _DRAWING_INPUT_COLUMNS}
        overrides.update(run_input_id=str(uuid4()), input_revision=3, created_at=datetime.now(UTC))
        db.execute(
            insert(story_tables.run_inputs).values(**_next_input_values(previous, **overrides))
        )
        db.execute(
            update(story_tables.story_runs)
            .where(story_tables.story_runs.c.run_id == run_id)
            .values(current_input_revision=3)
        )
        db.commit()
    record = current_candidate(api, api.parent, run_id)
    assert record.candidate is not None and record.candidate["candidate_subject"] == "dog"


def test_the_cleanup_waits_for_the_run_lock_and_never_deletes_a_referenced_object(
    api: InputsApi,
) -> None:
    run_id = new_run(api, api.parent)
    handle = upload(api, api.parent, run_id, png_bytes())
    assert attach(api, api.parent, run_id, handle).status_code == 202
    referenced = str(input_rows(api, run_id)[-1]["derived_asset_ref"])
    orphan = f"parent/{run_id}/orphan-token/normalized.png"
    api.storage.inner.put_object(
        orphan, io.BytesIO(b"x"), content_type="image/png", content_length=1, metadata={}
    )

    def discard(key: str) -> None:
        with api.sessions()() as db:
            SqlParentStoryRunRepository(db)._discard_unreferenced_object(api.storage, run_id, key)

    discard(referenced)  # a committed winner's object stays (R1 B2)
    assert api.storage.read(referenced) is not None and referenced not in api.storage.deletes

    holder = api.sessions()()  # another attach holds the run row lock, as between put and commit
    try:
        holder.execute(
            select(story_tables.story_runs.c.run_id)
            .where(story_tables.story_runs.c.run_id == run_id)
            .with_for_update()
        ).one()
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(discard, orphan)
            finished, _ = futures_wait([pending], timeout=1.0)
            assert not finished and orphan not in api.storage.deletes  # T2B-R-1: waits
            holder.rollback()
            pending.result(timeout=60)
    finally:
        holder.close()
    assert orphan in api.storage.deletes and api.storage.read(orphan) is None


# ------------------------------------------------------------------------- purged runs
def cancel_run(api: InputsApi, owner: str, run_id: str) -> Any:
    revision = run_row(api, run_id)["revision"]
    return api.client.post(
        f"/v1/story-runs/{run_id}/cancel",
        json={"expected_revision": revision},
        headers=headers(owner, uuid4().hex),
    )


def test_attach_after_cancel_is_409_and_a_replay_is_the_lifecycle_projection(
    api: InputsApi,
) -> None:
    run_id = new_run(api, api.parent, hold_slot=True)
    handle = upload(api, api.parent, run_id, png_bytes())
    attached = attach(api, api.parent, run_id, handle, key="before-cancel")
    assert attached.status_code == 202
    cancelled = cancel_run(api, api.parent, run_id)
    assert cancelled.status_code == 202, cancelled.text
    assert run_row(api, run_id)["run_state"] == "DELETE_PENDING"

    replay = attach(api, api.parent, run_id, handle, key="before-cancel")
    assert replay.status_code == 202, replay.text
    body = replay.json()
    assert set(body) == {"request_id", "lifecycle"}
    assert (
        body["lifecycle"]["run_id"] == run_id and body["lifecycle"]["run_state"] == "DELETE_PENDING"
    )
    assert "asset_ref" not in body and "input_revision" not in body
    fresh = attach(api, api.parent, run_id, handle, key="after-cancel")
    assert fresh.status_code == 409 and code_of(fresh) == "INVALID_STATE_TRANSITION"
    # Even a replay with another body answers the projection for a purged run (DTR 6.5).
    other_body = attach(
        api, api.parent, run_id, handle, key="before-cancel", expected_run_revision=1
    )
    assert other_body.status_code == 202 and "lifecycle" in other_body.json()
    assert len(input_rows(api, run_id)) == 2


def test_a_run_cancelled_before_the_attach_never_gets_a_derived_object(api: InputsApi) -> None:
    run_id = new_run(api, api.parent, hold_slot=True)
    handle = upload(api, api.parent, run_id, png_bytes())
    cancelled = cancel_run(api, api.parent, run_id)
    assert cancelled.status_code == 202, cancelled.text
    puts = len(api.storage.puts)
    response = attach(api, api.parent, run_id, handle)
    assert response.status_code == 409 and code_of(response) == "INVALID_STATE_TRANSITION"
    assert len(api.storage.puts) == puts
    assert len(input_rows(api, run_id)) == 1
