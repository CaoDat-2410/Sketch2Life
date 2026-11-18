"""Test-only API launcher for the FEAT-063 M2 PostgreSQL gate G1.

It serves the real application on the loopback address with a synthetic token verifier.
It is started only by ``test_m2_s2_g1_parent_story_postgres.py`` from an owner-run gate card;
it is not a test module and is never collected.
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path
from typing import Any

LOOPBACK_ADDRESS = "127.0.0.1"
SYNTHETIC_ISSUER = "m2-s2-g1-synthetic-issuer"
BEARER_PREFIX = "m2g1:"
PID_FILE_NAME = "launcher-process.json"
_ALLOWED_NAMES = frozenset({LOOPBACK_ADDRESS, "localhost"})


class NonLoopbackConnectionRefused(OSError):
    """Raised when this process tries to reach anything but the loopback address."""


def _host_of(address: object) -> str | None:
    if isinstance(address, tuple) and address and isinstance(address[0], str):
        return address[0]
    return None


def install_socket_guard() -> None:
    """Refuse blocking-socket connects and name lookups that are not loopback.

    The guard covers ``socket.connect``, ``connect_ex`` and ``getaddrinfo`` only. It does not
    see overlapped connects made by an asynchronous client on Windows, datagram sends, or
    connections opened in native code such as the database driver's; the database is
    constrained by the literal-address URL instead.
    """

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_getaddrinfo = socket.getaddrinfo

    def guarded_connect(self: socket.socket, address: Any) -> None:
        if _host_of(address) != LOOPBACK_ADDRESS:
            raise NonLoopbackConnectionRefused("gate G1 allows loopback connections only")
        original_connect(self, address)

    def guarded_connect_ex(self: socket.socket, address: Any) -> int:
        if _host_of(address) != LOOPBACK_ADDRESS:
            raise NonLoopbackConnectionRefused("gate G1 allows loopback connections only")
        return original_connect_ex(self, address)

    def guarded_getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
        if name is not None and name not in _ALLOWED_NAMES:
            raise NonLoopbackConnectionRefused("gate G1 allows loopback name lookups only")
        return original_getaddrinfo(host, *args, **kwargs)

    socket.socket.connect = guarded_connect  # type: ignore[method-assign, assignment]
    socket.socket.connect_ex = guarded_connect_ex  # type: ignore[method-assign, assignment]
    socket.getaddrinfo = guarded_getaddrinfo


def _required(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise SystemExit(f"gate G1 launcher: {name} is not set")
    return value


def main() -> None:
    api_port = int(_required("M2_S2_G1_API_PORT"))
    output_root = Path(_required("M2_S2_G1_OUTPUT_ROOT"))
    if os.environ.get("SKETCH2LIFE_ENV") != "test":
        raise SystemExit("gate G1 launcher: SKETCH2LIFE_ENV must be test")
    if os.environ.get("STORYRUN_LITE_MAIN_DEMO_ENABLED", "0") != "0":
        raise SystemExit("gate G1 launcher: the StoryRun-lite demo flag must be off")

    install_socket_guard()

    import uvicorn

    import sketch2life
    from sketch2life.application.ports.identity import VerifiedPrincipal
    from sketch2life.infrastructure.config.settings import Settings
    from sketch2life.infrastructure.identity.firebase_token_verifier import (
        FirebaseTokenVerifier,
        IdentityVerificationUnavailable,
    )
    from sketch2life.interfaces.http.app import create_app

    class SyntheticTokenVerifier(FirebaseTokenVerifier):
        """Maps ``m2g1:<subject>`` bearer values to synthetic principals; nothing else."""

        def __init__(self, settings: Settings) -> None:
            super().__init__(settings)

        async def verify(self, encoded_token: str) -> VerifiedPrincipal:
            subject = encoded_token.removeprefix(BEARER_PREFIX)
            if not encoded_token.startswith(BEARER_PREFIX) or not subject or len(subject) > 200:
                raise IdentityVerificationUnavailable("gate G1 bearer value was not recognized")
            return VerifiedPrincipal(subject, SYNTHETIC_ISSUER, frozenset())

    application = create_app()
    runtime = application.state.be1_runtime
    if runtime.session_factory is None:
        raise SystemExit("gate G1 launcher: the database is not configured")
    runtime.identity_verifier = SyntheticTokenVerifier(runtime.settings)

    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / PID_FILE_NAME).write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "api_port": api_port,
                "package_path": str(Path(sketch2life.__file__).resolve().parent),
                "executable": sys.executable,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    uvicorn.run(
        application,
        host=LOOPBACK_ADDRESS,
        port=api_port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
