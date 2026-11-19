"""Guard refusals for the S1 seed (FEAT-066 SEED-1, package §3.1).

No test here opens a database or reads the worktree ``.env``: settings lookups are
replaced with stubs, and the live check uses a fake engine.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from tools.seed import guard
from tools.seed.guard import GuardedTarget, SeedGuardError

PLACEHOLDER_USER = "fixtureuser"
PLACEHOLDER_PASS = "fixturepass"
DATABASE = "s2l_seed_fixture"
PORT = 5435
GOOD_URL = f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/{DATABASE}"
URL_FRAGMENTS = (PLACEHOLDER_USER, PLACEHOLDER_PASS, DATABASE, str(PORT), "127.0.0.1")


def _env(url: str | None = GOOD_URL, **extra: str) -> dict[str, str]:
    env = dict(extra)
    if url is not None:
        env[guard.SEED_URL_VARIABLE] = url
    return env


def _assert_refused(
    capsys: pytest.CaptureFixture[str], call: Any, *fragments: str
) -> SeedGuardError:
    with pytest.raises(SeedGuardError) as info:
        call()
    error = info.value
    message = str(error)
    for fragment in (*URL_FRAGMENTS, *fragments):
        assert fragment not in message
    assert error.__cause__ is None
    assert error.__suppress_context__ or error.__context__ is None
    captured = capsys.readouterr()
    for fragment in (*URL_FRAGMENTS, *fragments):
        assert fragment not in captured.out
        assert fragment not in captured.err
    return error


def test_good_target_passes() -> None:
    target = guard.check_target(_env())
    assert (target.database, target.host, target.port) == (DATABASE, "127.0.0.1", PORT)
    assert PLACEHOLDER_PASS not in repr(target)


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        f"mysql://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/a/b_seed",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/s2l_fixture",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/be1_acceptance_seed",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/sketch2life_m2_s1a_seed",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@:{PORT}/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@10.0.0.5:{PORT}/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@db.example:{PORT}/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:5432/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:5433/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@localhost:5433/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:99999/{DATABASE}",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/{DATABASE}?host=10.0.0.5",
        f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@127.0.0.1:{PORT}/{DATABASE}#x",
    ],
)
def test_url_refusals(capsys: pytest.CaptureFixture[str], url: str | None) -> None:
    _assert_refused(capsys, lambda: guard.check_target(_env(url)), "10.0.0.5", "db.example")


@pytest.mark.parametrize(
    "name",
    ["PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS"],
)
def test_libpq_variable_refusal(capsys: pytest.CaptureFixture[str], name: str) -> None:
    _assert_refused(capsys, lambda: guard.check_target(_env(**{name: "elsewhere-value"})))


@pytest.mark.parametrize("name", ["S1A_P_ALEMBIC_DATABASE_URL", "STORYRUN_LITE_DATABASE_URL"])
def test_other_url_variable_refusal(capsys: pytest.CaptureFixture[str], name: str) -> None:
    other = f"postgresql+psycopg://other:otherpass@127.0.0.1:{PORT}/other_seed"
    _assert_refused(
        capsys, lambda: guard.check_target(_env(**{name: other})), "otherpass", "other_seed"
    )


@pytest.mark.parametrize("name", ["S1A_P_ALEMBIC_DATABASE_URL", "STORYRUN_LITE_DATABASE_URL"])
def test_other_url_variable_equal_to_seed_is_accepted(name: str) -> None:
    assert guard.check_target(_env(**{name: GOOD_URL})).port == PORT


def test_check_target_reads_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (guard.SEED_URL_VARIABLE, *guard._LIBPQ_VARIABLES, *guard._OTHER_URL_VARIABLES):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(SeedGuardError):
        guard.check_target()
    monkeypatch.setenv(guard.SEED_URL_VARIABLE, GOOD_URL)
    assert guard.check_target().database == DATABASE


class _CachedStub:
    def __init__(self, value: Any) -> None:
        self.value = value
        self.cleared = 0

    def __call__(self) -> Any:
        if isinstance(self.value, Exception):
            raise self.value
        return self.value

    def cache_clear(self) -> None:
        self.cleared += 1


@pytest.fixture
def stub_settings(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Replace both settings lookups so the worktree ``.env`` is never read."""

    from sketch2life.infrastructure.config import settings as settings_module

    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", "placeholder")

    def install(value: Any) -> tuple[_CachedStub, _CachedStub]:
        settings_stub = _CachedStub(value)
        core_stub = _CachedStub(None)
        monkeypatch.setattr(settings_module, "get_settings", settings_stub)
        monkeypatch.setattr(settings_module, "get_core_database_settings", core_stub)
        return settings_stub, core_stub

    return install


@pytest.mark.parametrize("env", ["local", "test"])
def test_prepare_runtime_accepts_local_and_test(stub_settings: Any, env: str) -> None:
    import os

    settings_stub, core_stub = stub_settings(SimpleNamespace(env=env))
    guard.prepare_runtime(guard.check_target(_env()))
    assert os.environ["SKETCH2LIFE_DATABASE_URL"] == GOOD_URL
    assert settings_stub.cleared == 1 and core_stub.cleared == 1


@pytest.mark.parametrize("env", ["staging", "production"])
def test_prepare_runtime_refuses_other_envs(
    capsys: pytest.CaptureFixture[str], stub_settings: Any, env: str
) -> None:
    stub_settings(SimpleNamespace(env=env))
    target = guard.check_target(_env())
    _assert_refused(capsys, lambda: guard.prepare_runtime(target))


def test_prepare_runtime_hides_settings_errors(
    capsys: pytest.CaptureFixture[str], stub_settings: Any
) -> None:
    stub_settings(ValueError(f"bad settings for {GOOD_URL}"))
    target = guard.check_target(_env())
    _assert_refused(capsys, lambda: guard.prepare_runtime(target))


class _FakeResult:
    def __init__(self, row: dict[str, Any]) -> None:
        self._row = row

    def mappings(self) -> _FakeResult:
        return self

    def one(self) -> dict[str, Any]:
        return self._row


class _FakeEngine:
    def __init__(self, row: dict[str, Any] | Exception) -> None:
        self._row = row

    @contextmanager
    def connect(self) -> Any:
        if isinstance(self._row, Exception):
            raise self._row
        row = self._row
        yield SimpleNamespace(execute=lambda _query: _FakeResult(row))


def _live_row(**changes: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"database_name": DATABASE, "is_owner": True}
    row.update(changes)
    return row


def _target() -> GuardedTarget:
    return guard.check_target(_env())


def test_live_target_passes() -> None:
    guard.verify_live_target(_FakeEngine(_live_row()), _target())  # type: ignore[arg-type]


def test_live_check_reads_name_and_owner_only() -> None:
    """D-066-78: through Docker port mapping the server reports its in-container port and
    interface address, so the live check must not compare them."""

    seen: list[str] = []

    class _RecordingEngine(_FakeEngine):
        @contextmanager
        def connect(self) -> Any:
            def execute(query: Any) -> _FakeResult:
                seen.append(str(query))
                return _FakeResult(_live_row())

            yield SimpleNamespace(execute=execute)

    guard.verify_live_target(_RecordingEngine(_live_row()), _target())  # type: ignore[arg-type]
    assert len(seen) == 1
    assert "current_database()" in seen[0] and "datdba" in seen[0]
    assert "inet_server_port" not in seen[0] and "inet_server_addr" not in seen[0]


@pytest.mark.parametrize(
    "row",
    [
        _live_row(database_name="other_seed"),
        _live_row(database_name=None),
        _live_row(is_owner=False),
        _live_row(is_owner=None),
        RuntimeError(f"connection failed for {GOOD_URL}"),
    ],
)
def test_live_target_refusals(capsys: pytest.CaptureFixture[str], row: Any) -> None:
    target = _target()
    _assert_refused(
        capsys,
        lambda: guard.verify_live_target(_FakeEngine(row), target),  # type: ignore[arg-type]
        "10.0.0.5",
    )


def test_engine_creation_failure_is_hidden(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from sketch2life.infrastructure.persistence import database

    def broken(url: str) -> Any:
        raise ValueError(f"cannot create engine for {url}")

    monkeypatch.setattr(database, "create_core_engine", broken)
    target = _target()
    _assert_refused(capsys, lambda: guard.create_guarded_engine(target))


@pytest.mark.parametrize(
    ("host", "expected"), [("[::1]", "::1"), ("localhost", "localhost"), ("LOCALHOST", "localhost")]
)
def test_other_loopback_hosts_are_accepted(host: str, expected: str) -> None:
    url = f"postgresql+psycopg://{PLACEHOLDER_USER}:{PLACEHOLDER_PASS}@{host}:{PORT}/{DATABASE}"
    assert guard.check_target(_env(url)).host == expected


@pytest.mark.parametrize(
    "other",
    [
        f"postgresql+psycopg://u:p@127.0.0.1:{PORT}/other_seed",
        f"postgresql+psycopg://u:p@127.0.0.2:{PORT}/{DATABASE}",
        f"postgresql+psycopg://u:p@127.0.0.1:5436/{DATABASE}",
    ],
)
def test_engine_mismatch_is_refused(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, other: str
) -> None:
    from sqlalchemy import create_engine

    from sketch2life.infrastructure.persistence import database

    monkeypatch.setattr(database, "create_core_engine", lambda _url: create_engine(other))
    target = _target()
    _assert_refused(capsys, lambda: guard.create_guarded_engine(target), "other_seed")


def test_s1_main_exits_2_on_refused_target(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from tools.seed import s1_core

    monkeypatch.setenv(guard.SEED_URL_VARIABLE, GOOD_URL.replace(str(PORT), "5432"))
    for name in (*guard._LIBPQ_VARIABLES, *guard._OTHER_URL_VARIABLES):
        monkeypatch.delenv(name, raising=False)
    assert s1_core.main() == 2
    captured = capsys.readouterr()
    assert "seed guard refused" in captured.err
    for fragment in (PLACEHOLDER_USER, PLACEHOLDER_PASS, DATABASE, "5432"):
        assert fragment not in captured.out + captured.err.replace("5432 and 5433", "")


# --- SEED-7a guards (package Draft 3 test T2) -------------------------------------------


@pytest.mark.parametrize(
    "extra",
    [
        {"STORYRUN_LITE_DATABASE_URL": "placeholder-value"},
        {"STORYRUN_LITE_MODAL_BASE_URL": "https://placeholder.invalid"},
        {"STORYRUN_LITE_MODAL_TOKEN": "placeholder-value"},
        {"STORYRUN_LITE_MODAL_RUN_ID": "placeholder-value"},
        {"STORYRUN_LITE_VISION_MODE": "modal"},
        {"STORYRUN_LITE_STORY_MODE": "modal"},
        {"STORYRUN_LITE_VISION_LOOPBACK_URL": "http://placeholder.invalid:9"},
        {"MODAL_PLACEHOLDER_SETTING": "placeholder-value"},
    ],
)
def test_s7a_environment_refusals(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, extra: dict[str, str]
) -> None:
    env = dict(extra)
    _assert_refused(
        capsys,
        lambda: guard.check_s7a_environment(env, scratch_root=tmp_path, modules={}),
        *extra.values(),
    )
    assert "MODAL_CONFIG_PATH" not in env


def test_s7a_environment_refuses_an_imported_modal_client(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    env: dict[str, str] = {}
    _assert_refused(
        capsys,
        lambda: guard.check_s7a_environment(
            env, scratch_root=tmp_path, modules={"modal": sys.modules[__name__]}
        ),
    )


def test_s7a_environment_accepts_loopback_values_and_points_modal_at_a_missing_file(
    tmp_path: Path,
) -> None:
    env = {
        "STORYRUN_LITE_VISION_MODE": "loopback",
        "STORYRUN_LITE_STORY_MODE": "disabled",
        "STORYRUN_LITE_VISION_LOOPBACK_URL": "http://127.0.0.1:9",
        "MODAL_CONFIG_PATH": "placeholder-previous-value",
    }
    guard.check_s7a_environment(env, scratch_root=tmp_path, modules={})
    path = Path(env["MODAL_CONFIG_PATH"])
    assert not path.exists()
    assert path.parent.parent == tmp_path


def test_modal_config_path_is_honoured_by_the_installed_client(tmp_path: Path) -> None:
    if importlib.util.find_spec("modal") is None:
        pytest.skip("the Modal client is not installed")
    env: dict[str, str] = {}
    guard.check_s7a_environment(env, scratch_root=tmp_path, modules={})
    code = (
        "import modal.config as c, os, sys; "
        "sys.exit(0 if str(c.user_config_path) == os.environ['MODAL_CONFIG_PATH'] else 1)"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        env={**os.environ, **env},
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0


def _provider_settings(**overrides: Any) -> Any:
    values: dict[str, Any] = {
        "ai_provider": "disabled",
        "auth_provider": "development",
        "firebase_project_id": "",
        "firebase_credentials_file": None,
        "firebase_admin_json_base64": None,
        "lightning_ai_base_url": "",
        "lightning_ai_token_file": None,
        "runpod_endpoint_id": "",
        "runpod_api_key_file": None,
        "clamav_host": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_no_provider_accepts_the_disabled_defaults() -> None:
    guard.check_no_provider(_provider_settings())
    guard.check_no_provider(_provider_settings(clamav_host="localhost"))


@pytest.mark.parametrize(
    "overrides",
    [
        {"ai_provider": "modal_dev"},
        {"auth_provider": "firebase"},
        {"firebase_project_id": "placeholder-project"},
        {"firebase_credentials_file": "placeholder-file"},
        {"firebase_admin_json_base64": SimpleNamespace(get_secret_value=lambda: "placeholder")},
        {"lightning_ai_base_url": "https://placeholder.invalid"},
        {"lightning_ai_token_file": "placeholder-file"},
        {"runpod_endpoint_id": "placeholder-endpoint"},
        {"runpod_api_key_file": "placeholder-file"},
        {"clamav_host": "scanner.placeholder.invalid"},
    ],
)
def test_no_provider_refusals(
    capsys: pytest.CaptureFixture[str], overrides: dict[str, Any]
) -> None:
    _assert_refused(
        capsys,
        lambda: guard.check_no_provider(_provider_settings(**overrides)),
        "placeholder",
    )
