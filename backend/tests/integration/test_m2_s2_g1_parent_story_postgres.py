"""Owner-run PostgreSQL gate G1 (reduced) for M2-AT-08 and M2-AT-10, FEAT-063.

Runs only from an approved gate card against a dedicated, migrated, empty PostgreSQL 17
container. Without the gate variables every test skips with a stated reason; the gate card
requires zero skipped tests. The API under test is the real application served by
``m2_s2_g1_launcher.py`` in a child process, reached over loopback HTTP.

Recorded deviations DV-1 to DV-18 apply (see the gate's Task Approval): Parent only,
synthetic token verifier, SQL-seeded identities and profiles, late-result guards at
repository level, restart as a persistence check.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.parent_story_runs import (
    ParentStoryRevisionReservation,
    ParentStoryRunError,
)
from sketch2life.infrastructure.persistence.database import (
    create_core_engine,
    create_core_session_factory,
)
from sketch2life.infrastructure.persistence.parent_story_repository import (
    SqlParentStoryRunRepository,
    _principal_scope_ref,
)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_WORKTREE_ROOT = _BACKEND_ROOT.parent
_LAUNCHER_PATH = Path(__file__).resolve().with_name("m2_s2_g1_launcher.py")

_GATE_VARIABLES = (
    "SKETCH2LIFE_DATABASE_URL",
    "PGPASSFILE",
    "M2_S2_G1_EXPECTED_DATABASE",
    "M2_S2_G1_EXPECTED_PORT",
    "M2_S2_G1_RUN_MARKER",
    "M2_S2_G1_API_PORT",
    "M2_S2_G1_OUTPUT_ROOT",
)
_FORBIDDEN_VARIABLES = (
    "S1A_P_ALEMBIC_DATABASE_URL",
    "S1A_P_TEST_DATABASE_URL",
    "BE1_TEST_DATABASE_URL",
    "STORYRUN_LITE_DATABASE_URL",
    "PGHOST",
    "PGHOSTADDR",
    "PGPORT",
    "PGDATABASE",
    "PGUSER",
    "PGPASSWORD",
    "PGSERVICE",
    "PGSERVICEFILE",
    "PGOPTIONS",
)
_ALLOWED_DATABASES = frozenset({"sketch2life_m2_s2_gate", "sketch2life_m2_s2_rehearsal"})
_ALLOWED_DATABASE_PORTS = frozenset({55440, 55441})
_EXPECTED_ROLE = "s2l_m2_gate"
_EXPECTED_MAJOR = 17
_EXPECTED_VERSION_ROWS = frozenset(
    {
        "20261017_lc_0001",
        "20261018_ap_0009",
        "20261018_kv_0001",
        "20261018_vr_0001",
        "20261019_ae_0001",
        "20261019_pa_0001",
        "20261019_vf_0001",
        # FEAT-066 goal v4 T-12a: the DDL-D context-entry revision follows the Parent profile
        # revision and replaces its row (this gate test runs only on the fixed gate databases).
        # FEAT-066 goal v4 T-12c: the DDL-D Parent support-needs revision follows it and
        # replaces its row.
        "20261121_psn_0001",
        # FEAT-066 C5: the BE1 command-receipt revision follows ar_0001 and replaces its row.
        # FEAT-066 T-2a: the DDL-F upload-scope revision follows ar_0002 and replaces its row.
        # FEAT-066 T-3a: the DDL-A occurrence revision follows uf_0001 and replaces its row.
        # FEAT-066 T-7b: the DDL-H class-revision revision follows oc_0001 and replaces its row.
        # FEAT-066 T-7d: the DDL-H enrollment-index revision follows cls_0001 and replaces its row.
        # FEAT-066 T-8a/T-8b/T-NTF1: DDL-C inbox, endpoint and delivery revisions share this chain;
        # nt_0003 replaces the current row.
        # FEAT-066 T-4b1: the DDL-A child-selection revision follows nt_0001 and replaces its row.
        "20261125_nt_0003",
        # FR-C-08: the lifecycle revision depends on the Story head and replaces its row.
        # FEAT-066 T-2c: the DDL-B1 voice-idea revision follows the lifecycle revision and
        # replaces its row (this gate test runs only on the fixed gate databases).
        # FEAT-066 T-1a: the DDL-B1 video-generation revision follows the voice-idea revision and
        # replaces its row.
        # FEAT-066 T-4b2: the DDL-B2 Teacher-lock revision follows the video-generation revision
        # and replaces its row.
        # FEAT-066 goal v4 T-2e-a: the DDL-B3 activity-selection revision follows the Teacher-lock
        # revision and replaces its row.
        # FEAT-066 goal v4 T-1b-fix: the DDL-B1c review-epoch revision follows the DDL-B3 revision
        # and replaces its row.
        # FEAT-066 goal v4 T-12b: the DDL-D profile-revision revision follows the DDL-B1c revision
        # and replaces its row.
        # FEAT-066 goal v4 T-12c: the DDL-D BE1 support-needs revision follows it and
        # replaces its row.
        # FEAT-066 goal v4 T-12b-fix: the DDL-D purge revision follows it and replaces its row.
        "20261123_ppg_0001",
    }
)
_MUST_START_EMPTY = (
    "be1_adult_identities",
    "core_asset_metadata",
    "core_asset_lineage",
    "core_outbox_events",
    "ai_jobs.job",
    "ai_jobs.outbox",
    "parent.child_profiles",
    "parent.profile_revisions",
    "story.runs",
    "story.run_inputs",
    "story.understanding_revisions",
    "story.review_decisions",
    "story.command_receipts",
    "story.story_revisions",
)
_SIDE_EFFECT_TABLES = ("ai_jobs.job", "ai_jobs.outbox", "core_outbox_events")
_CONCURRENCY_REPETITIONS = 10
_LOCK_WAIT_SECONDS = 20.0
_HTTP_TIMEOUT_SECONDS = 60.0
_STARTUP_SECONDS = 120.0
_ZERO_HASH = "0" * 64


def _load_launcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location("m2_s2_g1_launcher", _LAUNCHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("gate G1 launcher module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_LAUNCHER = _load_launcher()
_LOOPBACK: str = _LAUNCHER.LOOPBACK_ADDRESS
_ISSUER: str = _LAUNCHER.SYNTHETIC_ISSUER
_BEARER_PREFIX: str = _LAUNCHER.BEARER_PREFIX
_PID_FILE_NAME: str = _LAUNCHER.PID_FILE_NAME


@dataclass(frozen=True, slots=True)
class _Gate:
    engine: Engine
    session_factory: sessionmaker[Session]
    output_root: Path
    api_port: int


@dataclass(frozen=True, slots=True)
class _Account:
    subject: str
    account_id: str
    profile_id: str
    profile_revision_id: str
    age_months: int

    @property
    def principal(self) -> VerifiedPrincipal:
        return VerifiedPrincipal(self.subject, _ISSUER, frozenset())

    @property
    def scope_ref(self) -> str:
        return _principal_scope_ref(self.principal)

    def headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {_BEARER_PREFIX}{self.subject}"}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        return headers


def _pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        listing = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        ).stdout
        return f'"{pid}"' in listing
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _port_refuses(port: int) -> bool:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.settimeout(2.0)
    try:
        probe.connect((_LOOPBACK, port))
    except OSError:
        return True
    finally:
        probe.close()
    return False


class _Api:
    """Owns the launcher child process and the HTTP client that talks to it."""

    def __init__(self, gate: _Gate) -> None:
        self._gate = gate
        self._process: subprocess.Popen[bytes] | None = None
        self._client: httpx.Client | None = None
        self._starts = 0
        self.reported_pid = 0

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("gate G1 API is not running")
        return self._client

    @property
    def running(self) -> bool:
        return self._process is not None

    @property
    def spawned_pid(self) -> int:
        if self._process is None:
            raise RuntimeError("gate G1 API is not running")
        return self._process.pid

    def start(self) -> None:
        if self._process is not None:
            raise RuntimeError("gate G1 API is already running")
        if not _port_refuses(self._gate.api_port):
            pytest.fail("gate G1 API port is already in use before start")
        pid_file = self._gate.output_root / _PID_FILE_NAME
        pid_file.unlink(missing_ok=True)
        self._starts += 1
        log_path = self._gate.output_root / f"launcher-{self._starts}.log"
        with log_path.open("wb") as log:
            self._process = subprocess.Popen(
                [sys.executable, "-B", str(_LAUNCHER_PATH)],
                cwd=str(self._gate.output_root),
                env=dict(os.environ),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        client = httpx.Client(
            base_url=f"http://{_LOOPBACK}:{self._gate.api_port}",
            timeout=_HTTP_TIMEOUT_SECONDS,
            trust_env=False,
        )
        deadline = time.monotonic() + _STARTUP_SECONDS
        while True:
            if self._process.poll() is not None:
                client.close()
                pytest.fail(f"gate G1 launcher exited early; see {log_path.name}")
            try:
                if client.get("/v1/story-runs/active/current").status_code == 401:
                    break
            except httpx.TransportError:
                pass
            if time.monotonic() > deadline:
                client.close()
                self.stop_abruptly()
                pytest.fail("gate G1 launcher did not become ready in time")
            time.sleep(0.5)
        facts = json.loads(pid_file.read_text(encoding="utf-8"))
        package_path = Path(str(facts["package_path"])).resolve()
        if _BACKEND_ROOT / "src" not in package_path.parents:
            client.close()
            self.stop_abruptly()
            pytest.fail("gate G1 launcher imported the package from another checkout")
        self.reported_pid = int(facts["pid"])
        self._client = client

    def stop_abruptly(self) -> tuple[int, int]:
        """Terminate the launcher at operating-system level; return (spawned, reported) pids."""
        if self._process is None:
            raise RuntimeError("gate G1 API is not running")
        spawned, reported = self._process.pid, self.reported_pid
        if self._client is not None:
            self._client.close()
            self._client = None
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(spawned)],
                capture_output=True,
                check=False,
                timeout=60,
            )
            # The tree kill already covers an interpreter started by a redirector. The
            # reported identifier is never killed separately: once freed, Windows may give
            # it to an unrelated process.
        else:
            self._process.kill()
        self._process.wait(timeout=60)
        self._process = None
        self.reported_pid = 0
        return spawned, reported


def _required_environment() -> dict[str, str] | None:
    values = {name: os.environ.get(name, "") for name in _GATE_VARIABLES}
    if not all(values.values()):
        return None
    return values


def _scalar(engine: Engine, statement: str, **parameters: object) -> Any:
    with engine.connect() as connection:
        value = connection.execute(text(statement), parameters).scalar()
        connection.rollback()
    return value


def _rows(engine: Engine, statement: str, **parameters: object) -> list[str]:
    """Return matching rows as canonical JSON strings, for content comparison."""
    with engine.connect() as connection:
        result = connection.execute(text(statement), parameters).mappings().all()
        connection.rollback()
    return sorted(json.dumps(dict(row), sort_keys=True, default=str) for row in result)


def _count(engine: Engine, table: str) -> int:
    schema, _, name = table.rpartition(".")
    qualified = f'"{schema}"."{name}"' if schema else f'"{name}"'
    return int(_scalar(engine, f"SELECT count(*) FROM {qualified}"))


def _all_table_counts(engine: Engine) -> dict[str, int]:
    with engine.connect() as connection:
        tables = connection.execute(
            text(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' "
                "AND table_schema NOT IN ('pg_catalog', 'information_schema') "
                "ORDER BY table_schema, table_name"
            )
        ).all()
        counts = {
            f"{schema}.{name}": int(
                connection.execute(text(f'SELECT count(*) FROM "{schema}"."{name}"')).scalar()
                or 0
            )
            for schema, name in tables
        }
        connection.rollback()
    return counts


def _assert_no_side_effects(engine: Engine) -> None:
    for table in _SIDE_EFFECT_TABLES:
        if table == "core_outbox_events":
            # FR-C-08 (DTR Draft 6 §6.1): cancel writes one lifecycle event by design; any
            # other Core outbox row is still a side effect.
            assert (
                _scalar(
                    engine,
                    "SELECT count(*) FROM core_outbox_events WHERE event_type NOT IN "
                    "('StoryRunCancellationRequestedV1', 'StoryRunDeletedV1')",
                )
                == 0
            ), "core_outbox_events must hold no event other than lifecycle events"
            continue
        assert _count(engine, table) == 0, f"{table} must stay empty"


def _run_row(engine: Engine, run_id: str) -> list[str]:
    return _rows(engine, "SELECT * FROM story.runs WHERE run_id = :run_id", run_id=run_id)


def _run_value(engine: Engine, run_id: str, column: str) -> Any:
    allowed = {"revision", "version", "run_state", "active_owner_parent_account_id"}
    assert column in allowed
    return _scalar(engine, f"SELECT {column} FROM story.runs WHERE run_id = :run_id", run_id=run_id)


def _account_counts(engine: Engine, account: _Account) -> dict[str, int]:
    scope = account.scope_ref
    return {
        "runs": int(
            _scalar(
                engine,
                "SELECT count(*) FROM story.runs WHERE actor_scope_ref = :scope",
                scope=scope,
            )
        ),
        "inputs": int(
            _scalar(
                engine,
                "SELECT count(*) FROM story.run_inputs i JOIN story.runs r "
                "ON r.run_id = i.run_id WHERE r.actor_scope_ref = :scope",
                scope=scope,
            )
        ),
        "create_receipts": int(
            _scalar(
                engine,
                "SELECT count(*) FROM story.command_receipts "
                "WHERE actor_scope_ref = :scope AND operation = 'CREATE_RUN'",
                scope=scope,
            )
        ),
        "cancel_receipts": int(
            _scalar(
                engine,
                "SELECT count(*) FROM story.command_receipts "
                "WHERE actor_scope_ref = :scope AND operation = 'CANCEL_RUN'",
                scope=scope,
            )
        ),
    }


def _account_rows(engine: Engine, account: _Account) -> dict[str, list[str]]:
    scope = account.scope_ref
    return {
        "runs": _rows(
            engine, "SELECT * FROM story.runs WHERE actor_scope_ref = :scope", scope=scope
        ),
        "inputs": _rows(
            engine,
            "SELECT i.* FROM story.run_inputs i JOIN story.runs r ON r.run_id = i.run_id "
            "WHERE r.actor_scope_ref = :scope",
            scope=scope,
        ),
        "receipts": _rows(
            engine,
            "SELECT * FROM story.command_receipts WHERE actor_scope_ref = :scope",
            scope=scope,
        ),
    }


def _seed_identity(engine: Engine, subject: str, account_id: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO be1_adult_identities "
                "(subject, account_id, issuer, state, account_role, role_revision) "
                "VALUES (:subject, :account_id, :issuer, 'active', 'parent', 1)"
            ),
            {"subject": subject, "account_id": account_id, "issuer": _ISSUER},
        )


def _insert_profile(
    engine: Engine, *, subject: str, profile_id: str, revision_id: str, age_months: int
) -> None:
    revision_hash = hashlib.sha256(f"{profile_id}:{age_months}".encode("ascii")).hexdigest()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO parent.child_profiles "
                "(parent_profile_id, owner_issuer, owner_subject, state, "
                "current_revision_no, data_origin) "
                "VALUES (CAST(:profile_id AS uuid), :issuer, :subject, 'ACTIVE', 1, "
                "'SYNTHETIC_DEV')"
            ),
            {"profile_id": profile_id, "issuer": _ISSUER, "subject": subject},
        )
        connection.execute(
            text(
                "INSERT INTO parent.profile_revisions "
                "(profile_revision_id, parent_profile_id, revision_no, age_months, "
                "display_name, interests_summary, authored_by_issuer, authored_by_subject, "
                "revision_hash) "
                "VALUES (CAST(:revision_id AS uuid), CAST(:profile_id AS uuid), 1, "
                ":age_months, 'Gate G1 synthetic', 'synthetic interests', :issuer, :subject, "
                ":revision_hash)"
            ),
            {
                "revision_id": revision_id,
                "profile_id": profile_id,
                "age_months": age_months,
                "issuer": _ISSUER,
                "subject": subject,
                "revision_hash": revision_hash,
            },
        )


def _new_account(engine: Engine, age_months: int = 60) -> _Account:
    """Seed one fresh Parent identity with one synthetic child profile (DV-9, DV-10)."""
    account = _Account(
        subject=f"m2-s2-g1-{uuid4().hex}",
        account_id=str(uuid4()),
        profile_id=str(uuid4()),
        profile_revision_id=str(uuid4()),
        age_months=age_months,
    )
    _seed_identity(engine, account.subject, account.account_id)
    _insert_profile(
        engine,
        subject=account.subject,
        profile_id=account.profile_id,
        revision_id=account.profile_revision_id,
        age_months=age_months,
    )
    return account


def _constraint_name(error: IntegrityError) -> str | None:
    diagnostics = getattr(error.orig, "diag", None)
    name = getattr(diagnostics, "constraint_name", None)
    return name if isinstance(name, str) else None


def _create(api: _Api, account: _Account, key: str) -> httpx.Response:
    return api.client.post(
        "/v1/story-runs",
        json={"parent_profile_id": account.profile_id, "topic": "gate", "adult_confirmed_idea": ""},
        headers=account.headers(key),
    )


def _created_run_id(api: _Api, account: _Account) -> str:
    response = _create(api, account, f"create-{uuid4().hex}")
    assert response.status_code == 201, response.text
    return str(response.json()["story_run"]["run_id"])


def _cancel(
    api: _Api, account: _Account, run_id: str, key: str, expected_revision: int | None
) -> httpx.Response:
    body: dict[str, int] = {}
    if expected_revision is not None:
        body["expected_revision"] = expected_revision
    return api.client.post(
        f"/v1/story-runs/{run_id}/cancel", json=body, headers=account.headers(key)
    )


def _get(api: _Api, account: _Account, run_id: str) -> httpx.Response:
    return api.client.get(f"/v1/story-runs/{run_id}", headers=account.headers())


def _active(api: _Api, account: _Account) -> httpx.Response:
    return api.client.get("/v1/story-runs/active/current", headers=account.headers())


def _assert_error(response: httpx.Response, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status, response.text
    body: dict[str, Any] = response.json()
    assert body["code"] == code, body
    return body


def _with_repository[ResultT](
    gate: _Gate, action: Callable[[SqlParentStoryRunRepository], ResultT]
) -> ResultT:
    """Call a product repository method on a session from the product's own factory."""
    with gate.session_factory() as session:
        try:
            return action(SqlParentStoryRunRepository(session))
        finally:
            session.rollback()


def _fail_run(gate: _Gate, account: _Account, run_id: str, error_code: str) -> None:
    _with_repository(
        gate,
        lambda repository: repository.fail_drawing_analysis(
            principal=account.principal,
            run_id=run_id,
            error_code=error_code,
            outcome_unknown=False,
        ),
    )


@pytest.fixture(scope="session")
def gate() -> Iterator[_Gate]:
    environment = _required_environment()
    if environment is None:
        pytest.skip("gate G1 variables are not set; this file runs only from the gate card")
    present = [name for name in _FORBIDDEN_VARIABLES if os.environ.get(name)]
    assert not present, f"variables that must be cleared are set: {present}"
    assert os.environ.get("SKETCH2LIFE_ENV") == "test"
    assert os.environ.get("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0") == "0"
    assert not (_WORKTREE_ROOT / ".env").exists(), "a .env file exists at the worktree root"

    import sketch2life

    package_path = Path(sketch2life.__file__).resolve().parent
    assert _BACKEND_ROOT / "src" in package_path.parents, "package imported from another checkout"

    url = make_url(environment["SKETCH2LIFE_DATABASE_URL"])
    expected_port = int(environment["M2_S2_G1_EXPECTED_PORT"])
    expected_database = environment["M2_S2_G1_EXPECTED_DATABASE"]
    assert url.host == _LOOPBACK
    assert url.password is None, "the database URL must not carry a password"
    assert url.username == _EXPECTED_ROLE
    assert expected_port in _ALLOWED_DATABASE_PORTS and url.port == expected_port
    assert expected_database in _ALLOWED_DATABASES and url.database == expected_database
    output_root = Path(environment["M2_S2_G1_OUTPUT_ROOT"]).resolve()
    assert output_root.is_dir(), "the output root must exist"
    api_port = int(environment["M2_S2_G1_API_PORT"])
    assert api_port in {55450, 55451}

    _LAUNCHER.install_socket_guard()
    engine = create_core_engine(environment["SKETCH2LIFE_DATABASE_URL"])
    try:
        with engine.connect() as connection:
            identity = connection.execute(
                text(
                    "SELECT current_database(), current_user, "
                    "current_setting('server_version_num')::integer / 10000, "
                    "(SELECT rolsuper FROM pg_roles WHERE rolname = current_user), "
                    "current_setting('m2_s2_g1.run_marker', true)"
                )
            ).one()
            raw_versions: list[Any] = list(
                connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
            )
            version_rows = frozenset(str(value) for value in raw_versions)
            connection.rollback()
        assert identity[0] == expected_database
        assert identity[1] == _EXPECTED_ROLE
        assert identity[2] == _EXPECTED_MAJOR
        assert identity[3] is False, "the gate role must not be a superuser"
        assert identity[4] == environment["M2_S2_G1_RUN_MARKER"], "run marker mismatch"
        assert version_rows == _EXPECTED_VERSION_ROWS, sorted(version_rows)
        for table in _MUST_START_EMPTY:
            assert _count(engine, table) == 0, f"{table} is not empty before the run"
        before = _all_table_counts(engine)
        yield _Gate(engine, create_core_session_factory(engine), output_root, api_port)
        after = _all_table_counts(engine)
        (output_root / "table-counts.json").write_text(
            json.dumps({"before": before, "after": after}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def api(gate: _Gate) -> Iterator[_Api]:
    runner = _Api(gate)
    runner.start()
    try:
        yield runner
    finally:
        if runner.running:
            runner.stop_abruptly()


def _blocked_by(engine: Engine, holder_pid: int) -> int:
    return int(
        _scalar(
            engine,
            "SELECT count(*) FROM pg_stat_activity WHERE :holder = ANY(pg_blocking_pids(pid))",
            holder=holder_pid,
        )
    )


def test_08_01a_unique_index_path_is_deterministic(gate: _Gate, api: _Api) -> None:
    """One request against a held, uncommitted active run of the same account (DV-14)."""
    for _ in range(_CONCURRENCY_REPETITIONS):
        account = _new_account(gate.engine)
        holder = gate.engine.connect()
        transaction = holder.begin()
        released = False
        try:
            holder_pid = int(holder.execute(text("SELECT pg_backend_pid()")).scalar_one())
            holder.execute(
                text(
                    "INSERT INTO story.runs (run_id, actor_scope_kind, actor_scope_ref, "
                    "profile_ref, run_state, revision, version, active_owner_parent_account_id) "
                    "VALUES (:run_id, 'PARENT_ACCOUNT', :scope, :profile, 'INPUT_PROCESSING', "
                    "1, 1, :account_id)"
                ),
                {
                    "run_id": str(uuid4()),
                    "scope": account.scope_ref,
                    "profile": account.profile_id,
                    "account_id": account.account_id,
                },
            )
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending: Future[httpx.Response] = pool.submit(
                    _create, api, account, f"held-{uuid4().hex}"
                )
                deadline = time.monotonic() + _LOCK_WAIT_SECONDS
                try:
                    while _blocked_by(gate.engine, holder_pid) == 0:
                        assert not pending.done(), "the create returned before the lock wait"
                        assert time.monotonic() < deadline, "no session waited on the holder"
                        time.sleep(0.05)
                except BaseException:
                    # Release the holder before the pool waits for the blocked request.
                    transaction.rollback()
                    released = True
                    raise
                transaction.commit()
                released = True
                response = pending.result(timeout=_HTTP_TIMEOUT_SECONDS)
        finally:
            if not released:
                transaction.rollback()
            holder.close()
        _assert_error(response, 409, "ACTIVE_RUN_EXISTS")
        # The held run has no input row: this account is never read again.
        assert _account_counts(gate.engine, account) == {
            "runs": 1,
            "inputs": 0,
            "create_receipts": 0,
            "cancel_receipts": 0,
        }
    _assert_no_side_effects(gate.engine)


def test_08_01b_concurrent_creates_leave_one_active_run(gate: _Gate, api: _Api) -> None:
    for _ in range(_CONCURRENCY_REPETITIONS):
        account = _new_account(gate.engine)
        barrier = threading.Barrier(2)

        def submit(
            key: str, *, owner: _Account = account, start: threading.Barrier = barrier
        ) -> httpx.Response:
            start.wait(timeout=30)
            return _create(api, owner, key)

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit, f"race-{uuid4().hex}") for _ in range(2)]
            responses = [future.result(timeout=_HTTP_TIMEOUT_SECONDS) for future in futures]
        assert sorted(response.status_code for response in responses) == [201, 409]
        loser = next(response for response in responses if response.status_code == 409)
        _assert_error(loser, 409, "ACTIVE_RUN_EXISTS")
        assert _account_counts(gate.engine, account) == {
            "runs": 1,
            "inputs": 1,
            "create_receipts": 1,
            "cancel_receipts": 0,
        }
    _assert_no_side_effects(gate.engine)


def test_08_02_create_replay_returns_the_same_run_without_writes(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    key = f"replay-{uuid4().hex}"
    first = _create(api, account, key)
    assert first.status_code == 201, first.text
    run_id = first.json()["story_run"]["run_id"]
    before = _account_rows(gate.engine, account)
    replay = _create(api, account, key)
    assert replay.status_code == 201, replay.text
    assert replay.json()["story_run"]["run_id"] == run_id
    assert _account_rows(gate.engine, account) == before
    _assert_no_side_effects(gate.engine)


def test_08_03_cancel_marks_delete_pending_and_releases_the_owner(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    response = _cancel(api, account, run_id, f"cancel-{uuid4().hex}", 1)
    assert response.status_code == 202, response.text
    body = response.json()["lifecycle"]  # FR-C-08 lifecycle envelope (D-218 A-3)
    assert body["purge_state"] == "PENDING"
    assert body["run_state"] == "DELETE_PENDING"
    assert body["revision"] == 2
    assert _run_value(gate.engine, run_id, "run_state") == "DELETE_PENDING"
    assert _run_value(gate.engine, run_id, "active_owner_parent_account_id") is None
    receipt = _scalar(
        gate.engine,
        "SELECT response_body ->> 'purge_state' FROM story.command_receipts "
        "WHERE resource_ref = :run_id AND operation = 'CANCEL_RUN' AND state = 'FINAL' "
        "AND response_status = 202",
        run_id=run_id,
    )
    assert receipt == "PENDING"
    _assert_no_side_effects(gate.engine)


def test_08_04_cancel_replay_returns_the_recorded_response(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    key = f"cancel-{uuid4().hex}"
    first = _cancel(api, account, run_id, key, 1)
    assert first.status_code == 202, first.text
    assert _run_value(gate.engine, run_id, "revision") == 2
    before = _account_rows(gate.engine, account)
    replay = _cancel(api, account, run_id, key, 1)
    assert replay.status_code == 202, replay.text
    assert replay.json() == first.json()
    assert _account_rows(gate.engine, account) == before


def test_08_05_same_key_with_a_different_request_is_refused(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    key = f"cancel-{uuid4().hex}"
    assert _cancel(api, account, run_id, key, 1).status_code == 202
    before = _account_rows(gate.engine, account)
    _assert_error(_cancel(api, account, run_id, key, 2), 400, "INVALID_IDEMPOTENCY_KEY")
    assert _account_rows(gate.engine, account) == before


def test_08_06_run_revision_tracks_committed_state_changes(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    create_key = f"create-{uuid4().hex}"
    created = _create(api, account, create_key)
    assert created.status_code == 201, created.text
    run_id = created.json()["story_run"]["run_id"]
    assert created.json()["story_run"]["run_revision"] == 1
    assert _run_value(gate.engine, run_id, "revision") == 1
    assert _get(api, account, run_id).json()["story_run"]["run_revision"] == 1
    assert _create(api, account, create_key).json()["story_run"]["run_revision"] == 1
    assert _run_value(gate.engine, run_id, "revision") == 1
    cancel_key = f"cancel-{uuid4().hex}"
    assert _cancel(api, account, run_id, cancel_key, 1).json()["lifecycle"]["revision"] == 2
    assert _cancel(api, account, run_id, cancel_key, 1).status_code == 202
    assert _get(api, account, run_id).json()["lifecycle"]["revision"] == 2
    assert _run_value(gate.engine, run_id, "revision") == 2


def test_08_07_stale_expected_revision_is_refused_without_a_write(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    before = _account_rows(gate.engine, account)
    body = _assert_error(
        _cancel(api, account, run_id, f"cancel-{uuid4().hex}", 5), 409, "STALE_REVISION"
    )
    assert body["current_version"] == 1
    assert _account_rows(gate.engine, account) == before


def test_08_08_missing_expected_revision_is_a_request_error(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    before = _account_rows(gate.engine, account)
    body = _assert_error(
        _cancel(api, account, run_id, f"cancel-{uuid4().hex}", None), 400, "INVALID_REQUEST"
    )
    fields = [entry["field"] for entry in body["field_errors"] or []]
    assert "expected_revision" in fields
    assert _account_rows(gate.engine, account) == before


def test_08_09_cancel_key_reused_on_another_run_is_refused(gate: _Gate, api: _Api) -> None:
    account = _new_account(gate.engine)
    key = f"cancel-{uuid4().hex}"
    first_run = _created_run_id(api, account)
    assert _cancel(api, account, first_run, key, 1).status_code == 202
    second_run = _created_run_id(api, account)
    before = _run_row(gate.engine, second_run)
    _assert_error(_cancel(api, account, second_run, key, 1), 400, "INVALID_IDEMPOTENCY_KEY")
    assert _run_row(gate.engine, second_run) == before


def test_08_14_cancel_in_a_terminal_state_is_refused(gate: _Gate, api: _Api) -> None:
    """Asserts status and code, which is stronger than the approved case (DV-15)."""
    failed_owner = _new_account(gate.engine)
    failed_run = _created_run_id(api, failed_owner)
    _fail_run(gate, failed_owner, failed_run, "SYNTHETIC_ANALYSIS_FAILED")

    completed_owner = _new_account(gate.engine)
    completed_run = _created_run_id(api, completed_owner)
    with gate.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE story.runs SET run_state = 'COMPLETED', "
                "active_owner_parent_account_id = NULL, revision = revision + 1, "
                "version = version + 1 WHERE run_id = :run_id"
            ),
            {"run_id": completed_run},
        )

    pending_owner = _new_account(gate.engine)
    pending_run = _created_run_id(api, pending_owner)
    assert _cancel(api, pending_owner, pending_run, f"cancel-{uuid4().hex}", 1).status_code == 202

    cases = (
        (failed_owner, failed_run, "FAILED"),
        (completed_owner, completed_run, "COMPLETED"),
        (pending_owner, pending_run, "DELETE_PENDING"),
    )
    for owner, run_id, state in cases:
        assert _run_value(gate.engine, run_id, "run_state") == state
        assert _run_value(gate.engine, run_id, "active_owner_parent_account_id") is None
        revision = int(_run_value(gate.engine, run_id, "revision"))
        before = _account_rows(gate.engine, owner)
        _assert_error(
            _cancel(api, owner, run_id, f"cancel-{uuid4().hex}", revision),
            409,
            "INVALID_STATE_TRANSITION",
        )
        assert _account_rows(gate.engine, owner) == before


def test_08_15_ownership_and_lock_release(gate: _Gate, api: _Api) -> None:
    owner = _new_account(gate.engine)
    other = _new_account(gate.engine)
    run_id = _created_run_id(api, owner)
    before = _run_row(gate.engine, run_id)
    _assert_error(_get(api, other, run_id), 404, "RESOURCE_NOT_FOUND")
    _assert_error(
        _cancel(api, other, run_id, f"cancel-{uuid4().hex}", 1), 404, "RESOURCE_NOT_FOUND"
    )
    assert _run_row(gate.engine, run_id) == before
    assert _active(api, owner).json()["story_run"]["run_id"] == run_id
    assert _cancel(api, owner, run_id, f"cancel-{uuid4().hex}", 1).status_code == 202
    assert _active(api, owner).json()["story_run"] is None
    second_run = _created_run_id(api, owner)
    assert second_run != run_id
    assert _active(api, owner).json()["story_run"]["run_id"] == second_run


def test_08_16_job_status_is_readable_by_the_owner_only(gate: _Gate, api: _Api) -> None:
    owner = _new_account(gate.engine)
    other = _new_account(gate.engine)
    run_id = _created_run_id(api, owner)
    active = _active(api, owner).json()["story_run"]
    assert (active["run_state"], active["job_state"], active["retryable"]) == (
        "INPUT_PROCESSING",
        None,
        False,
    )
    assert active["error_code"] is None
    _fail_run(gate, owner, run_id, "SYNTHETIC_ANALYSIS_FAILED")
    seen = _get(api, owner, run_id)
    assert seen.status_code == 200, seen.text
    story_run = seen.json()["story_run"]
    assert story_run["run_state"] == "FAILED"
    assert story_run["job_state"] == "FAILED"
    assert story_run["retryable"] is False
    assert story_run["error_code"] == "SYNTHETIC_ANALYSIS_FAILED"
    _assert_error(_get(api, other, run_id), 404, "RESOURCE_NOT_FOUND")


def _retention_rows(
    engine: Engine, run_id: str, original_ref: str, derived_ref: str
) -> dict[str, list[str]]:
    return {
        "run_inputs": _rows(
            engine, "SELECT * FROM story.run_inputs WHERE run_id = :run_id", run_id=run_id
        ),
        "understanding_revisions": _rows(
            engine,
            "SELECT * FROM story.understanding_revisions WHERE run_id = :run_id",
            run_id=run_id,
        ),
        "review_decisions": _rows(
            engine, "SELECT * FROM story.review_decisions WHERE run_id = :run_id", run_id=run_id
        ),
        "earlier_receipts": _rows(
            engine,
            "SELECT * FROM story.command_receipts WHERE resource_ref = :run_id "
            "AND operation <> 'CANCEL_RUN'",
            run_id=run_id,
        ),
        "asset_metadata": _rows(
            engine,
            "SELECT * FROM core_asset_metadata WHERE asset_ref IN (:original, :derived)",
            original=original_ref,
            derived=derived_ref,
        ),
        "asset_lineage": _rows(
            engine,
            "SELECT * FROM core_asset_lineage WHERE source_asset_ref = :original",
            original=original_ref,
        ),
    }


def test_08_03p_cancel_from_preparation_review_keeps_inputs_and_assets(
    gate: _Gate, api: _Api
) -> None:
    """D-127 retention. The state is built with product repository methods (DV-6)."""
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    original_ref = f"parent/{run_id}/{uuid4().hex}/original"
    derived_ref = f"parent/{run_id}/{uuid4().hex}/normalized.png"
    try:
        _with_repository(
            gate,
            lambda repository: repository.attach_artwork(
                principal=account.principal,
                run_id=run_id,
                original_asset_ref=original_ref,
                original_sha256=hashlib.sha256(b"gate-g1-original").hexdigest(),
                original_media_type="image/png",
                original_size_bytes=2048,
                derived_asset_ref=derived_ref,
                derived_sha256=hashlib.sha256(b"gate-g1-derived").hexdigest(),
                derived_size_bytes=1024,
                scanner_name="synthetic-scanner",
                scanner_version="1",
            ),
        )
    except ParentStoryRunError as error:
        pytest.fail(
            "STOP (review finding G2): attach_artwork failed under the product session "
            f"factory with {error.status_code} {error.code}; report as a product defect"
        )
    candidate = {
        "candidate_subject": "con meo",
        "visible_features": ["tai nhon"],
        "confidence": 0.9,
        "adult_confirmation_required": True,
        "decision": "REVIEW_REQUIRED",
    }
    understanding = _with_repository(
        gate,
        lambda repository: repository.record_understanding(
            principal=account.principal,
            run_id=run_id,
            result_snapshot={"result": candidate},
            candidate_subject="con meo",
            confidence=0.9,
        ),
    )
    _with_repository(
        gate,
        lambda repository: repository.confirm_subject(
            principal=account.principal,
            run_id=run_id,
            expected_understanding_revision=understanding,
            confirmed_subject="con meo",
            idempotency_key=f"subject-{uuid4().hex}",
        ),
    )
    seen = _get(api, account, run_id)
    assert seen.status_code == 200, seen.text
    assert seen.json()["story_run"]["run_state"] == "PREPARATION_REVIEW"
    revision = int(seen.json()["story_run"]["run_revision"])

    before = _retention_rows(gate.engine, run_id, original_ref, derived_ref)
    assert {name: len(rows) for name, rows in before.items()} == {
        "run_inputs": 2,
        "understanding_revisions": 1,
        "review_decisions": 1,
        "earlier_receipts": 2,
        "asset_metadata": 2,
        "asset_lineage": 1,
    }
    response = _cancel(api, account, run_id, f"cancel-{uuid4().hex}", revision)
    assert response.status_code == 202, response.text
    assert response.json()["lifecycle"]["purge_state"] == "PENDING"
    assert response.json()["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert _run_value(gate.engine, run_id, "active_owner_parent_account_id") is None
    assert (
        _scalar(
            gate.engine,
            "SELECT response_body ->> 'purge_state' FROM story.command_receipts "
            "WHERE resource_ref = :run_id AND operation = 'CANCEL_RUN' AND state = 'FINAL' "
            "AND response_status = 202",
            run_id=run_id,
        )
        == "PENDING"
    )
    assert _retention_rows(gate.engine, run_id, original_ref, derived_ref) == before
    assert _get(api, account, run_id).json()["lifecycle"]["run_state"] == "DELETE_PENDING"
    _assert_no_side_effects(gate.engine)


def test_level_r_late_results_are_refused_after_cancel(gate: _Gate, api: _Api) -> None:
    """Repository-level guards on PostgreSQL; not route evidence (DV-2, DV-3)."""
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    assert _cancel(api, account, run_id, f"cancel-{uuid4().hex}", 1).status_code == 202
    reservation = ParentStoryRevisionReservation(
        run_id=run_id,
        story_revision_id=str(uuid4()),
        revision_no=1,
        understanding_revision=1,
        context_revision=1,
        source_asset_sha256=_ZERO_HASH,
        worker_input={},
        request_sha256=_ZERO_HASH,
        receipt_id=str(uuid4()),
    )
    principal = account.principal
    attempts: tuple[tuple[str, Callable[[SqlParentStoryRunRepository], object]], ...] = (
        (
            "PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING",
            lambda repository: repository.record_understanding(
                principal=principal,
                run_id=run_id,
                result_snapshot={"result": {}},
                candidate_subject="late",
                confidence=0.5,
            ),
        ),
        (
            "INVALID_STATE_TRANSITION",
            lambda repository: repository.fail_drawing_analysis(
                principal=principal, run_id=run_id, error_code="LATE", outcome_unknown=False
            ),
        ),
        (
            "INVALID_STATE_TRANSITION",
            lambda repository: repository.fail_drawing_analysis(
                principal=principal, run_id=run_id, error_code="LATE", outcome_unknown=True
            ),
        ),
        (
            "INVALID_STATE_TRANSITION",
            lambda repository: repository.complete_story_revision(
                reservation=reservation,
                principal=principal,
                story={},
                story_sha256=_ZERO_HASH,
                provider_call_id="late",
                model_id="late",
                model_revision="late",
            ),
        ),
        (
            "INVALID_STATE_TRANSITION",
            lambda repository: repository.fail_story_revision(
                principal=principal,
                reservation=reservation,
                error_code="LATE",
                outcome_unknown=False,
            ),
        ),
        (
            "INVALID_STATE_TRANSITION",
            lambda repository: repository.fail_story_revision(
                principal=principal,
                reservation=reservation,
                error_code="LATE",
                outcome_unknown=True,
            ),
        ),
    )
    before = _account_rows(gate.engine, account)
    revisions_before = _count(gate.engine, "story.story_revisions")
    for expected_code, attempt in attempts:
        with pytest.raises(ParentStoryRunError) as raised:
            _with_repository(gate, attempt)
        assert raised.value.status_code == 409
        assert raised.value.code == expected_code
        assert _account_rows(gate.engine, account) == before
        assert _count(gate.engine, "story.story_revisions") == revisions_before
    assert _run_value(gate.engine, run_id, "run_state") == "DELETE_PENDING"


@pytest.mark.parametrize("age_months", [36, 120])
def test_10_01_02_run_is_created_at_both_age_bounds(
    gate: _Gate, api: _Api, age_months: int
) -> None:
    """Compares the create response with the seeded profile revision (DV-8, DV-17)."""
    account = _new_account(gate.engine, age_months)
    response = _create(api, account, f"create-{uuid4().hex}")
    assert response.status_code == 201, response.text
    story_run = response.json()["story_run"]
    assert story_run["run_state"] == "INPUT_PROCESSING"
    assert story_run["parent_profile_id"] == account.profile_id
    assert story_run["profile_revision_ref"] == account.profile_revision_id
    assert story_run["context_snapshot"]["profile_revision_ref"] == account.profile_revision_id
    assert story_run["context_snapshot"]["age_months"] == age_months
    assert _account_counts(gate.engine, account) == {
        "runs": 1,
        "inputs": 1,
        "create_receipts": 1,
        "cancel_receipts": 0,
    }
    _assert_no_side_effects(gate.engine)


@pytest.mark.parametrize("age_months", [121, 155])
def test_10_03_04_database_refuses_out_of_range_ages(gate: _Gate, age_months: int) -> None:
    """The database refuses to store these ages (DV-7); no run creation reaches the service."""
    subject = f"m2-s2-g1-{uuid4().hex}"
    profile_id, revision_id = str(uuid4()), str(uuid4())
    with pytest.raises(IntegrityError) as refused_profile:
        _insert_profile(
            gate.engine,
            subject=subject,
            profile_id=profile_id,
            revision_id=revision_id,
            age_months=age_months,
        )
    assert (
        _constraint_name(refused_profile.value)
        == "ck_parent_profile_revisions_age_months_36_120"
    )
    assert (
        _scalar(
            gate.engine,
            "SELECT count(*) FROM parent.child_profiles "
            "WHERE parent_profile_id = CAST(:profile_id AS uuid)",
            profile_id=profile_id,
        )
        == 0
    )
    run_id = str(uuid4())
    with pytest.raises(IntegrityError) as refused_run, gate.engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO story.runs (run_id, actor_scope_kind, actor_scope_ref, "
                "profile_ref, child_age_months, run_state, revision, version) "
                "VALUES (:run_id, 'PARENT_ACCOUNT', :scope, :profile, :age_months, "
                "'INPUT_PROCESSING', 1, 1)"
            ),
            {
                "run_id": run_id,
                "scope": hashlib.sha256(subject.encode("ascii")).hexdigest(),
                "profile": profile_id,
                "age_months": age_months,
            },
        )
    assert _constraint_name(refused_run.value) == "ck_story_run_child_age_months"
    assert _run_row(gate.engine, run_id) == []


def test_restart_keeps_committed_state(gate: _Gate, api: _Api) -> None:
    """Real process stop and start. Shows persistence, not recovery (DV-1, DV-2).

    Defined last in the file because it replaces the API process.
    """
    account = _new_account(gate.engine)
    run_id = _created_run_id(api, account)
    cancel_key = f"cancel-{uuid4().hex}"
    cancelled = _cancel(api, account, run_id, cancel_key, 1)
    assert cancelled.status_code == 202, cancelled.text

    before = _account_rows(gate.engine, account)
    old_spawned, old_reported = api.stop_abruptly()
    assert not _pid_alive(old_spawned), "the spawned launcher process survived"
    assert not _pid_alive(old_reported), "the launcher interpreter process survived"
    assert _port_refuses(gate.api_port), "the API port still accepts connections"
    assert _account_rows(gate.engine, account) == before

    api.start()
    assert api.reported_pid not in {old_spawned, old_reported}
    assert _account_rows(gate.engine, account) == before
    (gate.output_root / "restart-process-ids.json").write_text(
        json.dumps(
            {
                "old_spawned_pid": old_spawned,
                "old_reported_pid": old_reported,
                "new_spawned_pid": api.spawned_pid,
                "new_reported_pid": api.reported_pid,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    seen = _get(api, account, run_id)
    assert seen.status_code == 200, seen.text
    assert seen.json()["lifecycle"]["run_state"] == "DELETE_PENDING"
    assert seen.json()["lifecycle"]["revision"] == 2
    assert _active(api, account).json()["story_run"] is None
    replay = _cancel(api, account, run_id, cancel_key, 1)
    assert replay.status_code == 202, replay.text
    assert replay.json() == cancelled.json()
    assert _account_rows(gate.engine, account) == before

    new_run = _created_run_id(api, account)
    assert new_run != run_id
    counts = _account_counts(gate.engine, account)
    assert (counts["runs"], counts["create_receipts"]) == (2, 2)
    _assert_no_side_effects(gate.engine)
