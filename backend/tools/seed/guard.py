"""Target-database guard for the S1 synthetic seed (FEAT-066 SEED-1, package §3.1).

The guard reads exactly one variable, ``S2L_SEED_DATABASE_URL``. Every check that does
not need settings runs before anything reads settings. No refusal ever prints any part
of the URL: each refusal raises :class:`SeedGuardError` with a fixed message and
``from None``, so parser and driver errors cannot echo it.
"""

from __future__ import annotations

import os
import sys
import tempfile
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import unquote, urlsplit

from sqlalchemy import Engine, text

SEED_URL_VARIABLE = "S2L_SEED_DATABASE_URL"
_ALLOWED_SCHEMES = frozenset({"postgresql", "postgresql+psycopg"})
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_FORBIDDEN_PORTS = frozenset({5432, 5433})
_FORBIDDEN_NAME_PARTS = ("be1_acceptance", "m2_s1a")
_LIBPQ_VARIABLES = (
    "PGHOST",
    "PGHOSTADDR",
    "PGPORT",
    "PGDATABASE",
    "PGSERVICE",
    "PGSERVICEFILE",
    "PGOPTIONS",
)
_OTHER_URL_VARIABLES = ("S1A_P_ALEMBIC_DATABASE_URL", "STORYRUN_LITE_DATABASE_URL")
_ALLOWED_ENVS = frozenset({"local", "test"})


class SeedGuardError(RuntimeError):
    """A guard refusal. The message is fixed and never contains the URL."""


@dataclass(frozen=True, slots=True)
class GuardedTarget:
    """The checked seed target. ``url`` must never be printed or logged."""

    url: str
    database: str
    host: str
    port: int

    def __repr__(self) -> str:  # never expose the URL in a traceback or log
        return "GuardedTarget(<redacted>)"


def _refuse(reason: str) -> SeedGuardError:
    return SeedGuardError(f"seed guard refused: {reason}")


def check_target(environ: dict[str, str] | None = None) -> GuardedTarget:
    """Run the checks of package §3.1 (a) to (c); read no settings."""

    env = os.environ if environ is None else environ
    raw = env.get(SEED_URL_VARIABLE)
    if not raw:
        raise _refuse(f"{SEED_URL_VARIABLE} is not set")
    try:
        parts = urlsplit(raw)
        scheme = parts.scheme
        host = parts.hostname
        port = parts.port
        database = unquote(parts.path.lstrip("/"))
        query = parts.query
        fragment = parts.fragment
    except Exception:
        raise _refuse("the seed URL cannot be parsed") from None
    if scheme not in _ALLOWED_SCHEMES:
        raise _refuse("the seed URL must use the PostgreSQL psycopg scheme")
    if not database or "/" in database:
        raise _refuse("the seed URL must name exactly one database")
    lowered = database.lower()
    if "seed" not in lowered:
        raise _refuse("the database name must contain 'seed'")
    if any(part in lowered for part in _FORBIDDEN_NAME_PARTS):
        raise _refuse("the database name is reserved for another task")
    if not host:
        raise _refuse("the seed URL must name an explicit host")
    if host.lower() not in _LOOPBACK_HOSTS:
        raise _refuse("the seed host must be a loopback address")
    if port is None:
        raise _refuse("the seed URL must name an explicit port")
    if port in _FORBIDDEN_PORTS:
        raise _refuse("ports 5432 and 5433 are not allowed for the seed")
    if query or fragment:
        raise _refuse("the seed URL must not carry a query string")
    if any(env.get(name) for name in _LIBPQ_VARIABLES):
        raise _refuse("libpq connection variables must not be set")
    for name in _OTHER_URL_VARIABLES:
        other = env.get(name)
        if other and other != raw:
            raise _refuse("another database URL variable points elsewhere")
    return GuardedTarget(url=raw, database=database, host=host.lower(), port=port)


def prepare_runtime(target: GuardedTarget) -> None:
    """Point this process at the guarded URL, then check the resolved settings."""

    os.environ["SKETCH2LIFE_DATABASE_URL"] = target.url
    from sketch2life.infrastructure.config.settings import (
        get_core_database_settings,
        get_settings,
    )

    get_settings.cache_clear()
    get_core_database_settings.cache_clear()
    try:
        resolved_env = get_settings().env
    except Exception:
        raise _refuse("settings cannot be resolved") from None
    if resolved_env not in _ALLOWED_ENVS:
        raise _refuse("settings.env must be local or test")


def create_guarded_engine(target: GuardedTarget) -> Engine:
    """Create the engine with the explicit URL and compare it with the target."""

    from sqlalchemy.engine import make_url

    from sketch2life.infrastructure.persistence.database import create_core_engine

    try:
        engine = create_core_engine(target.url)
        url = make_url(target.url)
    except Exception:
        raise _refuse("the seed engine cannot be created") from None
    if (
        engine.url.database != target.database
        or (engine.url.host or "").lower() != target.host
        or engine.url.port != target.port
        or url.database != target.database
    ):
        engine.dispose()
        raise _refuse("the engine does not match the guarded target")
    return engine


def verify_live_target(engine: Engine, target: GuardedTarget) -> None:
    """Check the server side before any write (package §3.1 as amended by D-066-78).

    Only the database name and its owner are checked on the server. A seed database in a
    container reports its own in-container port and interface address through port
    mapping, so the loopback host and the port are enforced on the client side instead.
    """

    query = text(
        "SELECT current_database() AS database_name, "
        "current_user = pg_get_userbyid(d.datdba) AS is_owner "
        "FROM pg_database AS d WHERE d.datname = current_database()"
    )
    try:
        with engine.connect() as connection:
            row = connection.execute(query).mappings().one()
    except Exception:
        raise _refuse("the live target check failed") from None
    if row["database_name"] != target.database:
        raise _refuse("the server database does not match the guarded name")
    if row["is_owner"] is not True:
        raise _refuse("the connected user does not own the seed database")


def guarded_engine(environ: dict[str, str] | None = None) -> tuple[Engine, GuardedTarget]:
    """Run every guard step and return a checked engine for the seed."""

    target = check_target(environ)
    prepare_runtime(target)
    engine = create_guarded_engine(target)
    try:
        verify_live_target(engine, target)
    except SeedGuardError:
        engine.dispose()
        raise
    return engine, target


# --- SEED-7a guards (package Draft 3 section 3.1) --------------------------------------

_S7A_MUST_BE_UNSET = (
    "STORYRUN_LITE_DATABASE_URL",
    "STORYRUN_LITE_MODAL_BASE_URL",
    "STORYRUN_LITE_MODAL_TOKEN",
    "STORYRUN_LITE_MODAL_RUN_ID",
)
_MODAL_CONFIG_VARIABLE = "MODAL_CONFIG_PATH"
_S7A_SCRATCH_PARTS = ("tmp", "seed7a")


def _s7a_scratch_root() -> Path:
    # backend/tools/seed/guard.py -> the repository (or worktree) root is three levels up.
    return Path(__file__).resolve().parents[3].joinpath(*_S7A_SCRATCH_PARTS)


def check_s7a_environment(
    environ: MutableMapping[str, str] | None = None,
    *,
    scratch_root: Path | None = None,
    modules: MutableMapping[str, ModuleType] | None = None,
) -> None:
    """Refuse a process environment that could reach a provider (design rules 3 and 10).

    It runs before any settings are read. It reads only the process environment, and it
    then points ``MODAL_CONFIG_PATH`` at a file that does not exist, so a Modal client
    could not find a credential even if one were imported. Every refusal has a fixed
    message and never contains a value.
    """

    env = os.environ if environ is None else environ
    loaded = sys.modules if modules is None else modules
    for name in _S7A_MUST_BE_UNSET:
        if env.get(name):
            raise _refuse("a provider or runtime variable must be unset for S7a")
    if env.get("STORYRUN_LITE_VISION_MODE") not in (None, "", "loopback"):
        raise _refuse("the vision mode must be unset or loopback for S7a")
    if env.get("STORYRUN_LITE_STORY_MODE") not in (None, "", "disabled"):
        raise _refuse("the story mode must be unset or disabled for S7a")
    loopback_url = env.get("STORYRUN_LITE_VISION_LOOPBACK_URL")
    if loopback_url:
        try:
            loopback_host = (urlsplit(loopback_url).hostname or "").lower()
        except Exception:
            raise _refuse("the vision loopback URL cannot be parsed") from None
        if loopback_host not in _LOOPBACK_HOSTS:
            raise _refuse("the vision loopback URL must be a loopback address")
    if any(name.startswith("MODAL_") and name != _MODAL_CONFIG_VARIABLE for name in env):
        raise _refuse("a Modal variable is set")
    if "modal" in loaded:
        raise _refuse("the Modal client is already imported")
    root = _s7a_scratch_root() if scratch_root is None else scratch_root
    try:
        root.mkdir(parents=True, exist_ok=True)
        missing = Path(tempfile.mkdtemp(dir=root)) / "modal-config-absent.toml"
    except OSError:
        raise _refuse("the scratch folder cannot be created") from None
    if missing.exists():
        raise _refuse("the Modal config path is not absent")
    env[_MODAL_CONFIG_VARIABLE] = str(missing)


def check_no_provider(settings: Any = None) -> None:
    """Check the resolved settings after ``prepare_runtime``: no provider is configured."""

    if settings is None:
        from sketch2life.infrastructure.config.settings import get_settings

        try:
            settings = get_settings()
        except Exception:
            raise _refuse("settings cannot be resolved") from None
    if settings.ai_provider != "disabled" or settings.auth_provider != "development":
        raise _refuse("a provider is enabled in the settings")
    secret_value = settings.firebase_admin_json_base64
    if (
        settings.firebase_project_id
        or settings.firebase_credentials_file
        or (secret_value is not None and secret_value.get_secret_value())
        or settings.lightning_ai_base_url
        or settings.lightning_ai_token_file
        or settings.runpod_endpoint_id
        or settings.runpod_api_key_file
    ):
        raise _refuse("a provider setting is not empty")
    clamav = settings.clamav_host
    if clamav and clamav.lower() not in _LOOPBACK_HOSTS:
        raise _refuse("the malware scanner host must be a loopback address")
