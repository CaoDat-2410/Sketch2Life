"""Explicit CPU-only import of the public Openclipart corpus into Modal Volume v2."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from typing import Any

import modal

from openclipart_catalog import (
    CATALOG_ACTIVE_FILE,
    CATALOG_DATABASE_FILE,
    CATALOG_MANIFEST_FILE,
    CATALOG_ROOT_NAME,
    CATALOG_SCHEMA,
    initialize_catalog_database,
    index_source_record,
)


APP_NAME = "sketch2life-openclipart-catalog-import-dev"
VOLUME_NAME = "sketch2life-openclipart-catalog-dev"
VOLUME_MOUNT = "/catalog-volume"
DATASET_ID = "kawwaaa/openclipart"
MAX_JSONL_ROW_BYTES = 16 * 1024 * 1024
_SHA = re.compile(r"\A[0-9a-f]{40,64}\Z")
_SHARD = re.compile(r"\Aopenclipart_\d{2}\.jsonl\.zst\Z")
_MODULE_DIR = Path(__file__).resolve().parent
_CATALOG_MODULE = _MODULE_DIR / "openclipart_catalog.py"

app = modal.App(APP_NAME)
catalog_volume = modal.Volume.from_name(
    VOLUME_NAME,
    environment_name="dev",
    create_if_missing=True,
    version=2,
)
import_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("httpx==0.28.1", "zstandard==0.23.0")
    .add_local_file(str(_CATALOG_MODULE), "/root/openclipart_catalog.py", copy=True)
)


@app.function(
    name="ingest-openclipart-svg-catalog",
    image=import_image,
    cpu=4.0,
    memory=16_384,
    volumes={VOLUME_MOUNT: catalog_volume},
    timeout=43_200,
    retries=0,
    max_containers=1,
)
def ingest_openclipart_catalog(dataset_revision: str = "main") -> dict[str, Any]:
    """Resolve and ingest one immutable Openclipart dataset revision on Modal."""
    import httpx
    import zstandard

    requested_revision = dataset_revision.strip()
    if not requested_revision or len(requested_revision) > 128:
        raise ValueError("OPENCLIPART_REVISION_INVALID")

    api_base = f"https://huggingface.co/api/datasets/{DATASET_ID}"
    # The public HF CDN can pause between chunks for large shards. Bound
    # connection setup tightly but allow a longer read-idle interval.
    with httpx.Client(
        timeout=httpx.Timeout(600.0, connect=30.0, write=30.0, pool=30.0),
        follow_redirects=True,
    ) as client:
        revision_response = client.get(f"{api_base}/revision/{requested_revision}")
        revision_response.raise_for_status()
        revision_payload = revision_response.json()
        resolved_revision = revision_payload.get("sha")
        if not isinstance(resolved_revision, str) or _SHA.fullmatch(resolved_revision) is None:
            raise RuntimeError("OPENCLIPART_REVISION_RESOLUTION_FAILED")
        tree_response = client.get(
            f"{api_base}/tree/{resolved_revision}",
            params={"recursive": "true", "expand": "false"},
        )
        tree_response.raise_for_status()
        tree_payload = tree_response.json()
        shards = sorted(
            (
                item
                for item in tree_payload
                if isinstance(item, dict)
                and isinstance(item.get("path"), str)
                and _SHARD.fullmatch(item["path"])
            ),
            key=lambda item: item["path"],
        )
        if not shards:
            raise RuntimeError("OPENCLIPART_SHARDS_NOT_FOUND")
        print(
            f"CATALOG_IMPORT_RESOLVED revision={resolved_revision} shards={len(shards)}",
            flush=True,
        )

        volume_root = Path(VOLUME_MOUNT) / CATALOG_ROOT_NAME
        revision_root = volume_root / resolved_revision
        revision_root.mkdir(parents=True, exist_ok=True)
        state_path = revision_root / CATALOG_MANIFEST_FILE
        database_path = revision_root / CATALOG_DATABASE_FILE
        if state_path.exists():
            state = _read_json(state_path)
            if state.get("dataset_revision") != resolved_revision or state.get("dataset_id") != DATASET_ID:
                raise RuntimeError("OPENCLIPART_CATALOG_REVISION_CONFLICT")
            if state.get("status") == "READY":
                expected_shards = {item["path"] for item in shards}
                if set(state.get("completed_shards", [])) != expected_shards:
                    raise RuntimeError("OPENCLIPART_READY_SHARD_SET_INVALID")
                for shard_name in expected_shards:
                    stored_shard = revision_root / "source_shards" / shard_name
                    if not stored_shard.is_file() or _sha256_file(stored_shard) != state.get("shard_sha256", {}).get(shard_name):
                        raise RuntimeError("OPENCLIPART_SOURCE_CORPUS_INCOMPLETE")
                import sqlite3

                if not database_path.is_file():
                    raise RuntimeError("OPENCLIPART_INDEX_DATABASE_MISSING")
                with sqlite3.connect(
                    f"file:{database_path.as_posix()}?mode=ro&immutable=1", uri=True
                ) as connection:
                    indexed_rows = connection.execute("SELECT COUNT(*) FROM source_assets").fetchone()[0]
                    eligible_rows = connection.execute(
                        "SELECT COUNT(*) FROM source_assets WHERE eligible = 1"
                    ).fetchone()[0]
                if (
                    indexed_rows != state.get("stored_cc0_rows")
                    or eligible_rows != state.get("guide_eligible")
                ):
                    raise RuntimeError("OPENCLIPART_INDEX_COUNTS_MISMATCH")
                _write_json_atomic(
                    volume_root / CATALOG_ACTIVE_FILE,
                    {
                        "schema_version": CATALOG_SCHEMA,
                        "dataset_id": DATASET_ID,
                        "dataset_revision": resolved_revision,
                        "manifest_sha256": _sha256_file(state_path),
                    },
                )
                catalog_volume.commit()
                return {
                    "status": "ALREADY_READY",
                    "dataset_id": DATASET_ID,
                    "dataset_revision": resolved_revision,
                    "source_rows": state.get("source_rows", 0),
                    "guide_eligible": state.get("guide_eligible", 0),
                }
        else:
            state = {
                "schema_version": CATALOG_SCHEMA,
                "status": "IMPORTING",
                "dataset_id": DATASET_ID,
                "dataset_revision": resolved_revision,
                "requested_revision": requested_revision,
                "license_policy": "CC0-1.0-only",
                "source_row_count": None,
                "source_rows": 0,
                "stored_cc0_rows": 0,
                "guide_eligible": 0,
                "rejected_rows": 0,
                "rejection_reasons": {},
                "completed_shards": [],
                "shard_sha256": {},
                "started_at_utc": _utc_now(),
            }
            _write_json_atomic(state_path, state)
            connection = _open_database(database_path)
            connection.close()
            catalog_volume.commit()

        completed = set(state.get("completed_shards", []))
        shard_hashes = dict(state.get("shard_sha256", {}))
        rejection_reasons = dict(state.get("rejection_reasons", {}))
        source_rows = int(state.get("source_rows", 0))
        stored_cc0_rows = int(state.get("stored_cc0_rows", 0))
        guide_eligible = int(state.get("guide_eligible", 0))
        rejected_rows = int(state.get("rejected_rows", 0))

        for shard in shards:
            shard_name = shard["path"]
            if shard_name in completed:
                continue
            temp_name = None
            download_started = time.monotonic()
            downloaded_bytes = 0
            try:
                expected_size = shard.get("size")
                print(
                    f"CATALOG_SHARD_START name={shard_name} expected_bytes={expected_size}",
                    flush=True,
                )
                with tempfile.NamedTemporaryFile(prefix="openclipart-", suffix=".jsonl.zst", delete=False) as temp_file:
                    temp_name = temp_file.name
                    url = f"https://huggingface.co/datasets/{DATASET_ID}/resolve/{resolved_revision}/{shard_name}?download=true"
                    with client.stream("GET", url) as response:
                        response.raise_for_status()
                        digest = hashlib.sha256()
                        next_progress_bytes = 256 * 1024 * 1024
                        for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                            if chunk:
                                digest.update(chunk)
                                temp_file.write(chunk)
                                downloaded_bytes += len(chunk)
                                if downloaded_bytes >= next_progress_bytes:
                                    print(
                                        f"CATALOG_SHARD_PROGRESS name={shard_name} downloaded_bytes={downloaded_bytes}",
                                        flush=True,
                                    )
                                    next_progress_bytes += 256 * 1024 * 1024
                    shard_hash = digest.hexdigest()
                print(
                    f"CATALOG_SHARD_DOWNLOADED name={shard_name} bytes={downloaded_bytes} elapsed_seconds={time.monotonic() - download_started:.1f}",
                    flush=True,
                )
                if isinstance(expected_size, int) and os.path.getsize(temp_name) != expected_size:
                    raise RuntimeError("OPENCLIPART_SHARD_SIZE_MISMATCH")

                # Preserve the original compressed shard as the lossless corpus.
                # Durable data stays on the dedicated Modal Volume, never Docker/local.
                shard_directory = revision_root / "source_shards"
                shard_directory.mkdir(parents=True, exist_ok=True)
                stored_shard = shard_directory / shard_name
                if stored_shard.exists() and _sha256_file(stored_shard) != shard_hash:
                    raise RuntimeError("OPENCLIPART_STORED_SHARD_HASH_MISMATCH")
                if not stored_shard.exists():
                    temporary_shard = stored_shard.with_name(f".{shard_name}.{os.getpid()}.tmp")
                    shutil.copyfile(temp_name, temporary_shard)
                    if _sha256_file(temporary_shard) != shard_hash:
                        temporary_shard.unlink(missing_ok=True)
                        raise RuntimeError("OPENCLIPART_STORED_SHARD_HASH_MISMATCH")
                    os.replace(temporary_shard, stored_shard)

                connection = _open_database(database_path)
                row_count = cc0_count = eligible_count = rejected_count = 0
                connection.execute("BEGIN")
                try:
                    with open(temp_name, "rb") as compressed:
                        with zstandard.ZstdDecompressor().stream_reader(compressed) as reader:
                            with io.BufferedReader(reader) as buffered:
                                while True:
                                    raw_line = buffered.readline(MAX_JSONL_ROW_BYTES + 1)
                                    if not raw_line:
                                        break
                                    row_count += 1
                                    if len(raw_line) > MAX_JSONL_ROW_BYTES:
                                        while raw_line and not raw_line.endswith(b"\n"):
                                            raw_line = buffered.readline(MAX_JSONL_ROW_BYTES + 1)
                                        rejected_count += 1
                                        rejection_reasons["JSONL_ROW_SIZE_REJECTED"] = (
                                            rejection_reasons.get("JSONL_ROW_SIZE_REJECTED", 0) + 1
                                        )
                                        continue
                                    if not raw_line.strip():
                                        continue
                                    try:
                                        record = json.loads(raw_line)
                                    except (UnicodeDecodeError, json.JSONDecodeError):
                                        rejected_count += 1
                                        rejection_reasons["JSONL_ROW_INVALID"] = rejection_reasons.get("JSONL_ROW_INVALID", 0) + 1
                                        continue
                                    if not isinstance(record, dict):
                                        rejected_count += 1
                                        rejection_reasons["JSONL_ROW_INVALID"] = rejection_reasons.get("JSONL_ROW_INVALID", 0) + 1
                                        continue
                                    stored, eligible, reason = index_source_record(
                                        connection,
                                        record=record,
                                        shard_name=shard_name,
                                        catalog_root=revision_root,
                                    )
                                    if stored:
                                        cc0_count += 1
                                        if eligible:
                                            eligible_count += 1
                                        else:
                                            rejected_count += 1
                                            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                                    else:
                                        rejected_count += 1
                                        rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
                finally:
                    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    connection.close()

                source_rows += row_count
                stored_cc0_rows += cc0_count
                guide_eligible += eligible_count
                rejected_rows += rejected_count
                completed.add(shard_name)
                shard_hashes[shard_name] = shard_hash
                state.update(
                    {
                        "source_rows": source_rows,
                        "stored_cc0_rows": stored_cc0_rows,
                        "guide_eligible": guide_eligible,
                        "rejected_rows": rejected_rows,
                        "rejection_reasons": rejection_reasons,
                        "completed_shards": sorted(completed),
                        "shard_sha256": shard_hashes,
                        "source_shard_paths": {
                            name: f"source_shards/{name}" for name in sorted(completed)
                        },
                        "updated_at_utc": _utc_now(),
                    }
                )
                _write_json_atomic(state_path, state)
                catalog_volume.commit()
                print(
                    f"CATALOG_SHARD_COMMITTED name={shard_name} source_rows={source_rows} stored_cc0_rows={stored_cc0_rows} guide_eligible={guide_eligible} elapsed_seconds={time.monotonic() - download_started:.1f}",
                    flush=True,
                )
            except Exception as exc:
                print(
                    f"CATALOG_SHARD_FAILED name={shard_name} downloaded_bytes={downloaded_bytes} error_type={type(exc).__name__}",
                    flush=True,
                )
                raise
            finally:
                if temp_name and os.path.exists(temp_name):
                    os.unlink(temp_name)

    expected_shards = {shard["path"] for shard in shards}
    if completed != expected_shards:
        raise RuntimeError("OPENCLIPART_IMPORT_INCOMPLETE")
    for shard_name in expected_shards:
        stored_shard = revision_root / "source_shards" / shard_name
        if not stored_shard.is_file() or _sha256_file(stored_shard) != shard_hashes.get(shard_name):
            raise RuntimeError("OPENCLIPART_SOURCE_CORPUS_INCOMPLETE")
    connection = _open_database(database_path)
    indexed_rows = connection.execute("SELECT COUNT(*) FROM source_assets").fetchone()[0]
    eligible_rows = connection.execute("SELECT COUNT(*) FROM source_assets WHERE eligible = 1").fetchone()[0]
    connection.close()
    source_shard_bytes = sum(
        (revision_root / "source_shards" / name).stat().st_size for name in expected_shards
    )
    stored_svg_bytes = sum(
        path.stat().st_size for path in (revision_root / "assets").rglob("*.svg")
    )
    database_bytes = database_path.stat().st_size

    state.update(
        {
            "status": "READY",
            "source_row_count": source_rows,
            "stored_cc0_rows": indexed_rows,
            "guide_eligible": eligible_rows,
            "completed_shards": sorted(completed),
            "shard_count": len(shards),
            "shard_sha256": shard_hashes,
            "source_shard_paths": {
                name: f"source_shards/{name}" for name in sorted(completed)
            },
            "source_shard_bytes": source_shard_bytes,
            "stored_svg_bytes": stored_svg_bytes,
            "catalog_database_bytes": database_bytes,
            "stored_total_bytes": source_shard_bytes + stored_svg_bytes + database_bytes,
            "finished_at_utc": _utc_now(),
        }
    )
    _write_json_atomic(state_path, state)
    _write_json_atomic(
        volume_root / CATALOG_ACTIVE_FILE,
        {
            "schema_version": CATALOG_SCHEMA,
            "dataset_id": DATASET_ID,
            "dataset_revision": resolved_revision,
            "manifest_sha256": _sha256_file(state_path),
        },
    )
    catalog_volume.commit()
    return {
        "status": "READY",
        "dataset_id": DATASET_ID,
        "dataset_revision": resolved_revision,
        "shard_count": len(shards),
        "source_rows": source_rows,
        "stored_cc0_rows": indexed_rows,
        "guide_eligible": eligible_rows,
        "rejected_rows": rejected_rows,
        "source_shard_bytes": source_shard_bytes,
        "stored_svg_bytes": stored_svg_bytes,
        "catalog_database_bytes": database_bytes,
        "stored_total_bytes": source_shard_bytes + stored_svg_bytes + database_bytes,
        "volume_name": VOLUME_NAME,
        "volume_version": 2,
    }


def _open_database(database_path: Path):
    import sqlite3

    connection = sqlite3.connect(database_path, timeout=60)
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.execute("PRAGMA cache_size=-65536")
    initialize_catalog_database(connection)
    return connection


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("OPENCLIPART_MANIFEST_INVALID")
    return value


def _write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


@app.local_entrypoint()
def main(dataset_revision: str = "main") -> None:
    """Explicit operator command: `modal run ...openclipart_catalog_app.py`."""
    result = ingest_openclipart_catalog.remote(dataset_revision)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
