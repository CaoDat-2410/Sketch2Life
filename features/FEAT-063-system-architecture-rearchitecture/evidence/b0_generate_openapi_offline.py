"""Export offline FEAT-063 OpenAPI snapshots; no requests or provider access."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "backend" / "src"))


def deny_network(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("Network disabled for offline OpenAPI export")


def main() -> None:
    # Do not read project .env or inherit provider-specific process settings.
    for name in list(os.environ):
        if name.upper().startswith(("SKETCH2LIFE_", "AWS_")):
            os.environ.pop(name, None)

    with (
        patch.object(socket.socket, "connect", deny_network),
        patch.object(socket.socket, "connect_ex", deny_network),
        patch.object(socket, "create_connection", deny_network),
    ):
        from sketch2life.infrastructure.config.settings import Settings
        from sketch2life.interfaces.http import app as app_module

        for enabled in (False, True):
            config = Settings.model_construct(
                env="local",
                ai_provider="disabled",
                auth_provider="development",
                storage_example_enabled=enabled,
            )
            # Stub only construction of runtime and storage clients; no startup,
            # requests, DB engines, credentials chain, or provider calls.
            with (
                patch.object(app_module, "get_settings", return_value=config),
                patch.object(app_module, "build_be1_runtime", return_value=None),
                patch.object(app_module, "Boto3S3CompatibleObjectStorage", return_value=object()),
            ):
                schema = app_module.create_app(_composition_profile="combined").openapi()

            label = "storage-on" if enabled else "storage-off"
            dest = HERE / f"B0_openapi_combined_{label}_20261030.json"
            if dest.exists():
                raise FileExistsError(f"Refusing to overwrite {dest.name}")
            raw = (json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
            dest.write_bytes(raw)
            paths = schema["paths"]
            verbs = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
            operations = sum(verb in verbs for item in paths.values() for verb in item)
            print(f"{dest.name}: {operations} operations, {len(paths)} paths, sha256={hashlib.sha256(raw).hexdigest()}")


if __name__ == "__main__":
    main()
