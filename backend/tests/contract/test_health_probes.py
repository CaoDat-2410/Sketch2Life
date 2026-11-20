"""FEAT-066 T0.3: `/health/live`, `/health/ready` and `/metrics` (SRS l.814, TD-03).

Offline: the database URL points at a closed port or a silent loopback listener. The probe
credential is generated at runtime (never a literal in the source).
"""

from __future__ import annotations

import re
import secrets
import socket
import time
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import anyio
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from sketch2life.infrastructure.config.settings import (
    CoreDatabaseSettings,
    Settings,
    get_core_database_settings,
    get_settings,
)
from sketch2life.interfaces.http.app import create_app
from sketch2life.interfaces.http.metrics import HttpMetricsMiddleware, MetricsRegistry
from sketch2life.interfaces.http.probe_access import is_direct_loopback_request
from sketch2life.interfaces.http.routers import health as health_module
from sketch2life.interfaces.http.routers.health import router as health_router

LOOPBACK = ("127.0.0.1", 50000)
LOOPBACK_URL = "http://127.0.0.1"
CLOSED_URL = "postgresql+psycopg://synthetic_user:synthetic_pw@localhost:9/t03_closed"
ENVELOPE_FIELDS = {
    "code",
    "message",
    "correlation_id",
    "retryable",
    "retry_after_seconds",
    "field_errors",
    "request_id",
}


@pytest.fixture(autouse=True)
def _offline_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setitem(CoreDatabaseSettings.model_config, "env_file", None)
    monkeypatch.setenv("SKETCH2LIFE_ENV", "test")
    monkeypatch.setenv("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0")
    monkeypatch.setenv("SKETCH2LIFE_DATABASE_URL", CLOSED_URL)
    monkeypatch.delenv("SKETCH2LIFE_OPS_PROBE_TOKEN", raising=False)
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    yield
    get_settings.cache_clear()
    get_core_database_settings.cache_clear()


def _app(monkeypatch: pytest.MonkeyPatch, *, credential: str | None = None) -> FastAPI:
    if credential is not None:
        monkeypatch.setenv("SKETCH2LIFE_OPS_PROBE_TOKEN", credential)
    get_settings.cache_clear()
    return create_app()


def _loopback_client(application: FastAPI) -> TestClient:
    return TestClient(
        application, base_url=LOOPBACK_URL, client=LOOPBACK, raise_server_exceptions=False
    )


def _remote_client(application: FastAPI) -> TestClient:
    return TestClient(
        application,
        base_url="http://api.example.test",
        client=("203.0.113.9", 4000),
        raise_server_exceptions=False,
    )


def _series(text: str) -> list[str]:
    return [line for line in text.splitlines() if line and not line.startswith("#")]


def _mini_app(settings: Settings, *, engine: object | None = None) -> FastAPI:
    """Only the probe router, the metrics middleware and a runtime stub (any profile)."""
    application = FastAPI()
    registry = MetricsRegistry()
    application.state.metrics_registry = registry
    application.state.be1_runtime = SimpleNamespace(
        settings=settings, engine=engine, database_error=None if engine else "not configured"
    )
    application.include_router(health_router)
    application.add_middleware(HttpMetricsMiddleware, registry=registry)
    return application


def _settings(env: str, probe_credential: str | None = None) -> Settings:
    common: dict[str, object] = {"_env_file": None, "ops_probe_token": probe_credential}
    if env == "staging":
        return Settings(
            env="staging", auth_provider="firebase", firebase_project_id="synthetic-project",
            **common,  # type: ignore[arg-type]
        )
    if env == "production":
        return Settings(
            env="production", auth_provider="firebase", firebase_project_id="synthetic-project",
            ai_provider="runpod", runpod_endpoint_id="synthetic-endpoint",
            runpod_api_key_file=Path("synthetic-key-file"),
            **common,  # type: ignore[arg-type]
        )
    return Settings(env=env, **common)  # type: ignore[arg-type]


# --- live, /health, schema ---------------------------------------------------------------


def test_live_is_public_and_detail_free(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _remote_client(_app(monkeypatch))
    response = client.get("/health/live", headers={"Authorization": "Bearer anything"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_health_body_is_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _remote_client(_app(monkeypatch)).get("/health")

    assert response.json() == {"status": "ok", "service": "sketch2life-api"}


def test_live_is_in_swagger_and_operator_probes_are_not(monkeypatch: pytest.MonkeyPatch) -> None:
    application = _app(monkeypatch)
    paths = set(application.openapi(fe_projected=False)["paths"])  # type: ignore[call-arg]

    assert "/health/live" in paths
    assert "/health/ready" not in paths and "/metrics" not in paths
    # the FE projection is an explicit allow-list; none of the new probes is in it
    assert not {"/health/live", "/health/ready", "/metrics"} & set(application.openapi()["paths"])
    # they are mounted (reachable from loopback), only absent from the schema
    client = _loopback_client(application)
    assert client.get("/metrics").status_code == 200
    assert client.get("/health/ready").status_code in {200, 503}


def test_metrics_middleware_is_the_outermost_user_middleware(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _app(monkeypatch).user_middleware[0].cls == HttpMetricsMiddleware  # type: ignore[comparison-overlap]


# --- access matrix -----------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/health/ready", "/metrics"])
def test_loopback_without_credential_is_allowed_in_test_env(
    monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    response = _loopback_client(_app(monkeypatch)).get(path)

    assert response.status_code in {200, 503}  # allowed; readiness is 503 with a closed database
    assert response.headers["Cache-Control"] == "no-store"


def test_direct_loopback_helper_covers_ipv6_and_proxy_headers() -> None:
    def request(client: str, server: str, host: str, extra: list[tuple[bytes, bytes]]) -> Request:
        return Request(
            {
                "type": "http",
                "client": (client, 50000),
                "server": (server, 8000),
                "headers": [(b"host", host.encode()), *extra],
            }
        )

    assert is_direct_loopback_request(request("::1", "::1", "[::1]:8000", []))
    assert is_direct_loopback_request(request("127.0.0.1", "127.0.0.1", "localhost:8000", []))
    forwarded = [(b"forwarded", b"x")]
    assert not is_direct_loopback_request(request("::1", "::1", "[::1]:8000", forwarded))
    assert not is_direct_loopback_request(request("::1", "::1", "evil.example", []))
    assert not is_direct_loopback_request(request("10.0.0.5", "127.0.0.1", "127.0.0.1", []))
    assert not is_direct_loopback_request(Request({"type": "http", "headers": []}))


@pytest.mark.parametrize("path", ["/health/ready", "/metrics"])
@pytest.mark.parametrize("header", ["Forwarded", "X-Forwarded-For", "X-Real-IP"])
def test_forwarding_header_denies_loopback(
    monkeypatch: pytest.MonkeyPatch, path: str, header: str
) -> None:
    response = _loopback_client(_app(monkeypatch)).get(path, headers={header: "198.51.100.1"})

    assert response.status_code == 404


@pytest.mark.parametrize("path", ["/health/ready", "/metrics"])
def test_non_loopback_client_or_host_is_denied(
    monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    application = _app(monkeypatch)

    assert _remote_client(application).get(path).status_code == 404
    spoofed_host = TestClient(
        application, base_url="http://api.example.test", client=LOOPBACK
    )
    assert spoofed_host.get(path).status_code == 404
    local_host_remote_client = TestClient(
        application, base_url=LOOPBACK_URL, client=("203.0.113.9", 4000)
    )
    assert local_host_remote_client.get(path).status_code == 404


@pytest.mark.parametrize(
    ("path", "unknown"), [("/health/ready", "/health/ready-x"), ("/metrics", "/metricz")]
)
def test_404_denial_is_byte_identical_to_an_unknown_path(
    monkeypatch: pytest.MonkeyPatch, path: str, unknown: str
) -> None:
    client = _remote_client(_app(monkeypatch))
    denied = client.get(path)
    missing = client.get(unknown)

    assert denied.status_code == missing.status_code == 404
    assert denied.content == missing.content
    assert denied.headers["content-type"] == missing.headers["content-type"]
    assert denied.json() == {"detail": "Not Found"}


@pytest.mark.parametrize("path", ["/health/ready", "/metrics"])
@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE"])
def test_other_methods_on_hidden_paths_answer_like_an_unknown_path(
    monkeypatch: pytest.MonkeyPatch, path: str, method: str
) -> None:
    client = _remote_client(_app(monkeypatch))
    hidden = client.request(method, path)
    unknown = client.request(method, "/no-such-probe")

    assert hidden.status_code == unknown.status_code
    assert hidden.content == unknown.content
    assert "allow" not in hidden.headers


@pytest.mark.parametrize("path", ["/health/ready", "/metrics"])
def test_credential_allows_from_any_client_and_denies_otherwise(
    monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    probe_credential = secrets.token_urlsafe(32)
    wrong_credential = secrets.token_urlsafe(32)
    application = _app(monkeypatch, credential=probe_credential)
    remote = _remote_client(application)

    allowed = remote.get(path, headers={"Authorization": f"Bearer {probe_credential}"})
    assert allowed.status_code in {200, 503}
    lower_scheme = remote.get(path, headers={"Authorization": f"bearer {probe_credential}"})
    assert lower_scheme.status_code in {200, 503}

    denials = [
        remote.get(path),
        remote.get(path, headers={"Authorization": f"Bearer {wrong_credential}"}),
        remote.get(path, headers={"Authorization": probe_credential}),
        remote.get(path, headers={"Authorization": f"Basic {probe_credential}"}),
        # a configured credential disables the loopback bypass
        _loopback_client(application).get(path),
        remote.get(
            path,
            headers=[
                ("Authorization", f"Bearer {probe_credential}"),
                ("Authorization", f"Bearer {probe_credential}"),
            ],
        ),
    ]
    for denied in denials:
        assert denied.status_code == 401
        body = denied.json()
        assert set(body) == ENVELOPE_FIELDS
        assert body["code"] == "AUTH_REQUIRED"
        assert body["request_id"] == body["correlation_id"] == denied.headers["X-Request-ID"]
        assert denied.headers["WWW-Authenticate"] == "Bearer"
        assert wrong_credential not in denied.text and probe_credential not in denied.text


def test_presented_value_is_never_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    probe_credential = secrets.token_urlsafe(32)
    wrong_credential = secrets.token_urlsafe(32)
    client = _remote_client(_app(monkeypatch, credential=probe_credential))
    with caplog.at_level("DEBUG"):
        client.get("/metrics", headers={"Authorization": f"Bearer {wrong_credential}"})

    assert wrong_credential not in caplog.text and probe_credential not in caplog.text


@pytest.mark.parametrize("env", ["staging", "production"])
@pytest.mark.parametrize("path", ["/health/ready", "/metrics"])
def test_staging_and_production_ignore_loopback_and_hide_without_credential(
    env: str, path: str
) -> None:
    application = _mini_app(_settings(env))

    # no credential configured: nothing can ever match, even from loopback with a bearer
    assert _loopback_client(application).get(path).status_code == 404
    remote = _remote_client(application)
    assert remote.get(path, headers={"Authorization": "Bearer x" * 20}).status_code == 404
    assert remote.get(path).content == remote.get("/no-such-probe").content


@pytest.mark.parametrize("env", ["staging", "production"])
def test_staging_and_production_accept_only_the_credential(env: str) -> None:
    probe_credential = secrets.token_urlsafe(32)
    application = _mini_app(_settings(env, probe_credential))
    remote = _remote_client(application)

    assert remote.get("/metrics").status_code == 401
    assert _loopback_client(application).get("/metrics").status_code == 401
    ok = remote.get("/metrics", headers={"Authorization": f"Bearer {probe_credential}"})
    assert ok.status_code == 200
    assert ok.headers["content-type"].startswith("text/plain; version=0.0.4")
    ready = remote.get("/health/ready", headers={"Authorization": f"Bearer {probe_credential}"})
    assert ready.status_code == 503  # no database engine in this stub


# --- the setting ---------------------------------------------------------------------------


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_blank_credential_is_unset_and_does_not_fail_startup(
    monkeypatch: pytest.MonkeyPatch, blank: str
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_OPS_PROBE_TOKEN", blank)
    get_settings.cache_clear()

    assert get_settings().ops_probe_token is None
    assert create_app() is not None


@pytest.mark.parametrize("bad", ["short", "x" * 31, "a" * 31 + " ", ("é" * 40)])
def test_short_or_non_ascii_credential_fails_without_echoing_it(
    monkeypatch: pytest.MonkeyPatch, bad: str
) -> None:
    monkeypatch.setenv("SKETCH2LIFE_OPS_PROBE_TOKEN", bad)
    get_settings.cache_clear()

    with pytest.raises(ValueError) as error:
        get_settings()
    assert bad.strip() not in str(error.value) or not bad.strip()
    assert "operator probe credential" in str(error.value)


def test_minimum_length_credential_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKETCH2LIFE_OPS_PROBE_TOKEN", secrets.token_urlsafe(24)[:32])
    get_settings.cache_clear()

    assert get_settings().ops_probe_token is not None


def test_production_without_a_credential_is_allowed() -> None:
    assert _settings("production").ops_probe_token is None


# --- readiness -----------------------------------------------------------------------------

_LEAK_WORDS = (
    "postgres", "password", "synthetic_user", "synthetic_pw", "localhost", "t03_closed",
    "psycopg", "sqlalchemy", "Traceback", "Error", "refused",
)


def test_ready_is_503_with_a_closed_database_and_leaks_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _loopback_client(_app(monkeypatch))
    started = time.monotonic()
    response = client.get("/health/ready")

    assert time.monotonic() - started < 4.5
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "down"}}
    assert response.headers["Cache-Control"] == "no-store"
    assert not any(word.lower() in response.text.lower() for word in _LEAK_WORDS)


def test_ready_is_503_without_a_database_configuration() -> None:
    application = _mini_app(_settings("test"))

    response = _loopback_client(application).get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "down"}}


class _SilentListener:
    """Accepts TCP connections in the kernel backlog and never answers (a black hole)."""

    def __enter__(self) -> int:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(16)
        return int(self._socket.getsockname()[1])

    def __exit__(self, *_exc: object) -> None:
        self._socket.close()


def _wait_for_no_probe_threads(limit_seconds: float = 8.0) -> None:
    deadline = time.monotonic() + limit_seconds
    while health_module._probe_threads and time.monotonic() < deadline:
        time.sleep(0.05)
    assert health_module._probe_threads == 0


def test_ready_bound_holds_against_a_silent_server_and_threads_do_not_accumulate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_module, "_PROBE_CONNECT_TIMEOUT_SECONDS", 1)
    with _SilentListener() as port:
        monkeypatch.setenv(
            "SKETCH2LIFE_DATABASE_URL",
            f"postgresql+psycopg://synthetic_user:synthetic_pw@127.0.0.1:{port}/t03_silent",
        )
        client = _loopback_client(_app(monkeypatch))
        for _ in range(3):
            started = time.monotonic()
            response = client.get("/health/ready")
            elapsed = time.monotonic() - started
            assert response.status_code == 503
            assert elapsed < health_module._PROBE_OUTER_BOUND_SECONDS + 0.5
            assert response.json()["checks"] == {"database": "down"}
        _wait_for_no_probe_threads()


def test_ready_answers_down_without_a_thread_when_the_probe_cap_is_reached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(health_module, "_MAX_PROBE_THREADS", 0)
    client = _loopback_client(_app(monkeypatch))
    started = time.monotonic()
    response = client.get("/health/ready")

    assert time.monotonic() - started < 1.0
    assert response.status_code == 503
    assert health_module._probe_threads == 0


def test_cancelled_probe_releases_its_slot() -> None:
    runtime = SimpleNamespace(
        engine=SimpleNamespace(url=make_url(CLOSED_URL)), database_error=None
    )
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(be1_runtime=runtime)))

    async def cancelled_probe() -> None:
        with anyio.CancelScope() as scope:
            scope.cancel()
            await health_module._database_is_up(request)  # type: ignore[arg-type]

    for _ in range(3):  # more than the cap: a leak would make later probes answer without a thread
        anyio.run(cancelled_probe)
    assert health_module._probe_threads == 0


def test_probe_slot_is_released_after_a_failed_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _loopback_client(_app(monkeypatch))
    for _ in range(4):
        assert client.get("/health/ready").status_code == 503
    _wait_for_no_probe_threads()


# --- metrics -------------------------------------------------------------------------------


def _scrape(client: TestClient) -> str:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    return response.text


def test_metrics_exposition_has_the_expected_families(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _loopback_client(_app(monkeypatch))
    client.get("/health/live")
    text = _scrape(client)

    assert 'sketch2life_build_info{service="sketch2life-api"} 1' in text
    assert "sketch2life_process_start_time_seconds " in text
    assert 'sketch2life_http_requests_total{method="GET",status_class="2xx"} ' in text
    assert "sketch2life_http_request_duration_seconds_bucket" in text
    assert "sketch2life_http_requests_in_flight 1" in text  # the scrape itself
    assert text.endswith("\n")


def test_metrics_series_do_not_grow_with_unmatched_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _loopback_client(_app(monkeypatch))
    client.get("/unmatched-warmup")
    _scrape(client)  # the scrape itself becomes a series only after its first completion
    before = _series(_scrape(client))
    for index in range(50):
        client.get(f"/unmatched-{index}-{secrets.token_hex(8)}")
    after = _series(_scrape(client))

    assert len(after) == len(before)


def test_metrics_carry_no_path_identifier_or_route_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _loopback_client(_app(monkeypatch))
    run_id = "01234567-89ab-4def-8123-456789abcdef"
    client.get(f"/v1/story-runs/{run_id}")
    client.get("/api/be1/v1/organizations/synthetic-org/classes")
    client.request("PURGE", "/anything")
    text = _scrape(client)

    assert run_id not in text and "/v1/" not in text and "synthetic-org" not in text
    assert not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}", text)
    assert 'method="OTHER"' in text and "PURGE" not in text
    labels = set(re.findall(r"(\w+)=\"", "\n".join(_series(text))))
    assert labels <= {"service", "method", "status_class", "le"}


def test_metrics_histogram_is_cumulative_and_counters_are_monotonic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _loopback_client(_app(monkeypatch))
    for _ in range(5):
        client.get("/health/live")

    def parse(text: str) -> tuple[list[int], int, float, int]:
        buckets = [
            int(line.rsplit(" ", 1)[1])
            for line in text.splitlines()
            if line.startswith("sketch2life_http_request_duration_seconds_bucket")
        ]
        count = int(re.search(r"duration_seconds_count (\d+)", text).group(1))  # type: ignore[union-attr]
        total = float(re.search(r"duration_seconds_sum ([0-9.]+)", text).group(1))  # type: ignore[union-attr]
        requests = sum(
            int(line.rsplit(" ", 1)[1])
            for line in text.splitlines()
            if line.startswith("sketch2life_http_requests_total{")
        )
        return buckets, count, total, requests

    first = parse(_scrape(client))
    second = parse(_scrape(client))

    for buckets, count, _total, requests in (first, second):
        assert buckets == sorted(buckets)
        assert buckets[-1] == count == requests
    assert second[1] == first[1] + 1 and second[2] >= first[2]


def test_scraping_does_not_touch_the_database() -> None:
    touched: list[str] = []

    class _Runtime:
        settings = _settings("test")

        def __getattr__(self, name: str) -> object:
            touched.append(name)
            raise AttributeError(name)

    application = _mini_app(_settings("test"))
    application.state.be1_runtime = _Runtime()

    assert _loopback_client(application).get("/metrics").status_code == 200
    assert touched == []


def test_an_unhandled_exception_is_counted_as_5xx_and_re_raised() -> None:
    application = _mini_app(_settings("test"))

    @application.get("/boom")
    def boom() -> None:
        raise RuntimeError("synthetic failure")

    client = _loopback_client(application)
    assert client.get("/boom").status_code == 500
    text = _scrape(client)

    assert 'sketch2life_http_requests_total{method="GET",status_class="5xx"} 1' in text
    assert "synthetic failure" not in text


def test_in_flight_returns_to_zero_after_a_request() -> None:
    application = _mini_app(_settings("test"))
    client = _loopback_client(application)
    client.get("/health/live")
    registry = application.state.metrics_registry

    assert "sketch2life_http_requests_in_flight 0" in registry.render()
