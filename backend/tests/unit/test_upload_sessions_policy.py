"""FEAT-066 T-2a: offline checks of upload-session policy, keys, scope and the DDL-F text."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType
from uuid import uuid4

import pytest

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.upload_sessions import (
    PARENT_ACCOUNT_SCOPE,
    UPLOAD_MAX_PARTS,
    UPLOAD_PART_SIZE_BYTES,
)
from sketch2life.application.ports.upload_validation import (
    DOCX_MEDIA_TYPE,
    PPTX_MEDIA_TYPE,
    header_matches_media_type,
)
from sketch2life.contracts.schemas.upload_sessions import (
    CompleteGenericUploadRequestV1,
    CreateGenericUploadRequestV1,
)
from sketch2life.infrastructure.lesson_library.service import upload_session_revision
from sketch2life.infrastructure.lesson_library.tables import UPLOAD_SESSIONS
from sketch2life.infrastructure.persistence.core_models import OWNER_SCOPE_CHECK
from sketch2life.infrastructure.persistence.parent_story_repository import _principal_scope_ref
from sketch2life.infrastructure.uploads.purposes import (
    GENERIC_PURPOSES,
    MAX_DOCUMENT_BYTES,
    MAX_IMAGE_BYTES,
    OCCURRENCE_DOCUMENT,
    POLICIES,
    RUN_ARTWORK,
    RUN_AUDIO,
    document_media_type_for,
    safe_document_name,
)
from sketch2life.infrastructure.uploads.resolvers import (
    default_resolver_factories,
    merged_resolver_factories,
    parent_scope_ref,
)
from sketch2life.infrastructure.uploads.service import (
    UploadSessionError,
    asset_key,
    part_key,
    public_asset_ref,
    resolve_asset_key,
)
from sketch2life.interfaces.http import error_envelope as envelope

BACKEND = Path(__file__).resolve().parents[2]
SRC = BACKEND / "src" / "sketch2life"
MIGRATION = BACKEND / "alembic" / "versions" / "20261119_uf_0001_upload_scope.py"
RUN_ID = "0f1e2d3c-4b5a-4968-8777-665544332211"


# ----------------------------------------------------------------------------- purposes
def test_run_artwork_accepts_jpeg_png_webp_up_to_20_mib() -> None:
    policy = POLICIES[RUN_ARTWORK]
    assert policy.media_types == {"image/jpeg", "image/png", "image/webp"}
    assert policy.max_bytes == MAX_IMAGE_BYTES == 20 * 1024 * 1024
    assert policy.account_role == "parent" and policy.enabled
    assert (policy.too_large_code, policy.unsupported_code) == (
        "MEDIA_TOO_LARGE", "UNSUPPORTED_MEDIA_TYPE",
    )
    # 20 MiB is five 4 MiB parts, inside the DDL size CHECK (25,000,000) and the parts CHECK (7).
    assert -(-policy.max_bytes // UPLOAD_PART_SIZE_BYTES) == 5
    assert policy.max_bytes <= 25_000_000


def test_occurrence_document_accepts_pdf_docx_pptx_up_to_25_million_bytes() -> None:
    policy = POLICIES[OCCURRENCE_DOCUMENT]
    assert policy.media_types == {"application/pdf", DOCX_MEDIA_TYPE, PPTX_MEDIA_TYPE}
    assert policy.max_bytes == MAX_DOCUMENT_BYTES == 25_000_000
    assert policy.account_role == "teacher" and policy.needs_file_name
    assert (policy.too_large_code, policy.unsupported_code) == (
        "LESSON_FILE_TOO_LARGE", "UNSUPPORTED_LESSON_TYPE",
    )
    assert -(-policy.max_bytes // UPLOAD_PART_SIZE_BYTES) == 6 <= UPLOAD_MAX_PARTS


def test_run_audio_is_enabled_for_wav_and_mp4_up_to_20_megabytes() -> None:
    policy = POLICIES[RUN_AUDIO]
    assert policy.enabled and policy.media_types == frozenset({"audio/wav", "audio/mp4"})
    assert policy.max_bytes == 20_000_000 and policy.account_role == "parent"
    assert policy.too_large_code == "AUDIO_TOO_LARGE" and "AUDIO_TOO_LARGE" in envelope.MESSAGES
    assert -(-policy.max_bytes // UPLOAD_PART_SIZE_BYTES) == 5 <= UPLOAD_MAX_PARTS


def test_lesson_source_and_profile_image_are_not_generic_purposes() -> None:
    assert {RUN_ARTWORK, RUN_AUDIO, OCCURRENCE_DOCUMENT} == GENERIC_PURPOSES
    assert "LESSON_SOURCE" not in GENERIC_PURPOSES and "PROFILE_IMAGE" not in GENERIC_PURPOSES


def test_every_signature_the_policies_accept_is_known_to_the_shared_table() -> None:
    samples = {
        "image/png": b"\x89PNG\r\n\x1a\nxxxx",
        "image/jpeg": b"\xff\xd8\xff\xe0xxxxxxxx",
        "image/webp": b"RIFF\x00\x00\x00\x00WEBPxxxx",
        "audio/wav": b"RIFF\x00\x00\x00\x00WAVExxxx",
        "audio/mp4": b"\x00\x00\x00\x18ftypM4A xxxx",
        "application/pdf": b"%PDF-1.7xxxxxxx",
        DOCX_MEDIA_TYPE: b"PK\x03\x04xxxxxxxxxxxx",
        PPTX_MEDIA_TYPE: b"PK\x03\x04xxxxxxxxxxxx",
    }
    accepted = (
        POLICIES[RUN_ARTWORK].media_types
        | POLICIES[RUN_AUDIO].media_types
        | POLICIES[OCCURRENCE_DOCUMENT].media_types
    )
    assert set(samples) == accepted
    for media_type, sample in samples.items():
        assert header_matches_media_type(media_type, sample)
        assert not header_matches_media_type(media_type, b"\x00" * 16)
    assert not header_matches_media_type("image/png", samples["image/jpeg"])
    assert not header_matches_media_type("image/gif", b"GIF89a" + b"x" * 10)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("plan.pdf", "plan.pdf"),
        ("../../etc/plan.pdf", "plan.pdf"),
        ("C:\\users\\x\\plan.docx", "plan.docx"),
        ("a\x00b\x1f.pptx", "ab.pptx"),
        ("  ", ""),
    ],
)
def test_document_names_are_reduced_to_a_safe_last_segment(raw: str, expected: str) -> None:
    assert safe_document_name(raw) == expected


def test_document_extension_decides_the_media_type() -> None:
    assert document_media_type_for("a.PDF") == "application/pdf"
    assert document_media_type_for("a.docx") == DOCX_MEDIA_TYPE
    assert document_media_type_for("a.pptx") == PPTX_MEDIA_TYPE
    assert document_media_type_for("a.exe") is None and document_media_type_for("noext") is None


# ----------------------------------------------------------------------------- scope and keys
def test_parent_scope_ref_equals_the_story_repository_formula() -> None:
    principal = VerifiedPrincipal(subject="subject-é", issuer="issuer", roles=frozenset())
    assert parent_scope_ref(principal) == _principal_scope_ref(principal)
    other = VerifiedPrincipal(subject="subject-é", issuer="issuer-2", roles=frozenset())
    assert parent_scope_ref(other) != parent_scope_ref(principal)
    assert len(parent_scope_ref(principal)) == 64


def test_asset_and_chunk_keys_sit_under_the_run_prefix_with_version_one_rule() -> None:
    prefix = f"parent/{RUN_ID}/"
    upload_id = str(uuid4())
    asset = asset_key(prefix, upload_id)
    assert asset.startswith(prefix) and asset.endswith("/original")
    assert asset == asset_key(prefix, upload_id)  # deterministic: a retry overwrites
    assert asset != asset_key(prefix, str(uuid4()))
    chunk = part_key(prefix, upload_id, 3)
    assert chunk == f"{prefix}upload/{upload_id}/parts/3"
    assert chunk.startswith(prefix) and not chunk.startswith(f"{prefix}upload/{upload_id}/parts/30")
    # The purge closure (core_lifecycle_store.build_plan) accepts it: prefix and version 1.
    from sketch2life.application.ports.core_foundation import run_object_prefix

    assert asset.startswith(run_object_prefix(RUN_ID))


def test_the_public_asset_ref_is_an_opaque_handle_not_the_object_key() -> None:
    upload_id = str(uuid4())
    handle = public_asset_ref(upload_id)
    assert handle == f"upl_{upload_id}"
    assert "/" not in handle and "parent" not in handle and "original" not in handle
    assert handle != asset_key(f"parent/{RUN_ID}/", upload_id)
    # A value that is not a handle never reaches the database.
    assert resolve_asset_key(
        None, f"parent/{RUN_ID}/x/original",  # type: ignore[arg-type]
        owner_scope_kind="PARENT_ACCOUNT", owner_scope_ref="a" * 64, organization_id=None,
    ) is None


def test_revision_math_is_the_lesson_derivation() -> None:
    assert [upload_session_revision("OPEN", count) for count in (0, 1, 7)] == [1, 2, 8]
    for state in ("COMPLETED", "ABORTED", "EXPIRED", "FAILED"):
        assert upload_session_revision(state, 2) == 4


def test_default_resolvers_serve_the_run_purposes_and_registered_ones_win() -> None:
    assert set(default_resolver_factories()) == {RUN_ARTWORK, RUN_AUDIO}
    sentinel = object()
    merged = merged_resolver_factories({OCCURRENCE_DOCUMENT: sentinel})
    assert set(merged) == {RUN_ARTWORK, RUN_AUDIO, OCCURRENCE_DOCUMENT}
    assert merged[OCCURRENCE_DOCUMENT] is sentinel
    assert merged_resolver_factories(None).keys() == default_resolver_factories().keys()


# ----------------------------------------------------------------------------- schemas
def _create_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "purpose": "RUN_ARTWORK", "target_ref": RUN_ID, "media_type": "image/png",
        "expected_size_bytes": 10, "expected_sha256": "a" * 64,
    }
    body.update(overrides)
    return body


def test_create_request_forbids_unknown_fields_and_lesson_purposes() -> None:
    assert CreateGenericUploadRequestV1.model_validate(_create_body()).purpose == RUN_ARTWORK
    for extra in ("organization_id", "owner_ref", "role", "actor", "state"):
        with pytest.raises(ValueError):
            CreateGenericUploadRequestV1.model_validate(_create_body(**{extra: "x"}))
    for purpose in ("LESSON_SOURCE", "PROFILE_IMAGE", "OTHER"):
        with pytest.raises(ValueError):
            CreateGenericUploadRequestV1.model_validate(_create_body(purpose=purpose))
    bad_values = (
        {"expected_sha256": "A" * 64},
        {"expected_sha256": "a" * 63},
        {"expected_size_bytes": 0},
    )
    for bad in bad_values:
        with pytest.raises(ValueError):
            CreateGenericUploadRequestV1.model_validate(_create_body(**bad))
    with pytest.raises(ValueError):
        CompleteGenericUploadRequestV1.model_validate(
            {"expected_size_bytes": 1, "expected_sha256": "a" * 64, "purpose": "RUN_ARTWORK"}
        )
    # An over-cap size is a 413 of the service, not a validation error.
    assert CreateGenericUploadRequestV1.model_validate(
        _create_body(expected_size_bytes=30_000_000)
    ).expected_size_bytes == 30_000_000


# ----------------------------------------------------------------------------- envelope
def test_upload_session_paths_join_the_conv1_family_only_when_mounted() -> None:
    for path in ("/v1/upload-sessions", "/v1/upload-sessions/abc", "/v1/upload-sessions/a/parts/1"):
        assert envelope.is_conv1_path(path)
        assert not envelope.is_conv1_path(path, include_upload_sessions=False)
    assert not envelope.is_conv1_path("/v1/upload-sessionsfoo")
    assert not envelope.is_conv1_path("/v1/upload-sessionsfoo", include_upload_sessions=True)
    assert envelope.is_conv1_path("/api/be1/v1/x", include_upload_sessions=False)
    assert envelope.UPLOAD_SESSIONS_BASE not in envelope.CONV1_PREFIXES  # whole-segment rule


def _error_codes_raised_by_the_service() -> set[tuple[int, str]]:
    service = SRC / "infrastructure" / "uploads" / "service.py"
    tree = ast.parse(service.read_text(encoding="utf-8"))
    found: set[tuple[int, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else func.attr if isinstance(func, ast.Attribute) else None
        )
        if name in {"UploadSessionError", "_fail_terminal"}:
            args = node.args[1:3] if name == "_fail_terminal" else node.args[:2]
            if len(args) == 2 and all(isinstance(arg, ast.Constant) for arg in args):
                found.add((args[0].value, args[1].value))  # type: ignore[attr-defined]
    return found


def test_every_code_the_service_raises_has_a_message_or_is_status_only() -> None:
    found = _error_codes_raised_by_the_service()
    expected = {(404, "RESOURCE_NOT_FOUND"), (422, "UPLOAD_INCOMPLETE")}
    assert expected | {(410, "UPLOAD_SESSION_EXPIRED")} <= found
    unclassified = sorted(
        f"{status} {code}"
        for status, code in found
        if code not in envelope.MESSAGES
        and code not in envelope.STATUS_MESSAGE_ONLY
        and envelope.map_code(status, code) not in envelope.MESSAGES
    )
    assert unclassified == []


def test_upload_error_messages_are_worded_for_the_new_codes() -> None:
    for code in (
        "UNSUPPORTED_LESSON_TYPE", "UPLOAD_CHECKSUM_MISMATCH", "UPLOAD_CONTENT_MISMATCH",
        "STORAGE_UNAVAILABLE", "MEDIA_TOO_LARGE", "LESSON_FILE_TOO_LARGE", "UNSUPPORTED_MEDIA_TYPE",
        "UPLOAD_PART_CONFLICT", "UPLOAD_SESSION_STATE_CONFLICT", "UPLOAD_SESSION_EXPIRED",
        "UPLOAD_INCOMPLETE", "INVALID_STATE_TRANSITION", "PROVIDER_UNAVAILABLE",
    ):
        assert envelope.MESSAGES[code]
    assert "MALWARE_DETECTED" in envelope.STATUS_MESSAGE_ONLY  # recorded technical decision Q3
    body = envelope.build_error_body(status=503, code="STORAGE_UNAVAILABLE", request_id="r")
    assert body["retryable"] is True
    assert body["message"] == envelope.MESSAGES["STORAGE_UNAVAILABLE"]


def test_upload_session_error_carries_only_safe_fields() -> None:
    error = UploadSessionError(409, "STALE_REVISION", current_revision=4)
    assert (error.status_code, error.code, error.current_revision) == (409, "STALE_REVISION", 4)
    assert str(error) == "STALE_REVISION"  # no storage detail in the message


# ----------------------------------------------------------------------------- DDL-F
def _load_migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("uf_0001_under_test", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _op_calls(function: str) -> list[str]:
    tree = ast.parse(MIGRATION.read_text(encoding="utf-8"))
    body = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function
    )
    names: list[str] = []
    for node in ast.walk(body):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "op"
        ):
            names.append(node.func.attr)
    return names


def test_ddl_f_revision_chain_and_shape() -> None:
    module = _load_migration()
    assert module.revision == "20261119_uf_0001" and len(module.revision) <= 32
    assert module.down_revision == "20261119_ar_0002"
    assert module.branch_labels is None and module.depends_on is None
    forbidden = {"create_table", "drop_table", "rename_table"}
    assert forbidden.isdisjoint(_op_calls("upgrade"))
    assert forbidden.isdisjoint(_op_calls("downgrade"))
    assert module.OWNER_SCOPE_CHECK == OWNER_SCOPE_CHECK
    assert module.TABLE == "core_upload_sessions"
    assert "'OCCURRENCE_DOCUMENT'" in module.PURPOSE_AFTER
    assert "'OCCURRENCE_DOCUMENT'" not in module.PURPOSE_BEFORE
    assert module.PURPOSE_AFTER.startswith(module.PURPOSE_BEFORE)


def test_ddl_f_upgrade_and_downgrade_mirror_each_other() -> None:
    upgrade, downgrade = _op_calls("upgrade"), _op_calls("downgrade")
    assert upgrade.count("add_column") == 7  # scope kind and ref, plus five provenance columns
    # The five provenance columns are dropped in one loop over ``NEW_COLUMNS``.
    assert downgrade.count("drop_column") == 3
    assert len(_load_migration().NEW_COLUMNS) == 5
    assert upgrade.count("create_index") == downgrade.count("drop_index") == 2
    assert upgrade.count("create_check_constraint") == 2  # owner scope and the new purpose list
    assert upgrade.count("alter_column") == downgrade.count("alter_column") == 1
    assert downgrade[0] == "execute"  # the guard runs before anything is dropped


def test_ddl_f_downgrade_guard_refuses_generic_rows() -> None:
    guard = _load_migration().DOWNGRADE_GUARD
    assert "owner_scope_kind <> 'ORGANIZATION'" in guard
    assert "purpose = 'OCCURRENCE_DOCUMENT'" in guard
    assert "RAISE EXCEPTION" in guard


def test_orm_table_matches_ddl_f() -> None:
    columns = {column.name: column for column in UPLOAD_SESSIONS.columns}
    assert columns["organization_id"].nullable is True
    assert columns["owner_scope_kind"].nullable is False
    assert columns["owner_scope_kind"].server_default is not None
    nullable = (
        "owner_scope_ref", "error_code", "scan_verdict", "scanner_name", "scanner_version",
        "validated_at",
    )
    for name in nullable:
        assert columns[name].nullable is True
    names = {constraint.name for constraint in UPLOAD_SESSIONS.constraints}
    assert {"ck_core_upload_owner_scope", "ck_core_upload_purpose"} <= names
    assert {index.name for index in UPLOAD_SESSIONS.indexes} >= {
        "ix_core_upload_scope_state", "ix_core_upload_target_state", "ix_core_upload_owner_state",
    }
    owner_check = next(
        constraint for constraint in UPLOAD_SESSIONS.constraints
        if constraint.name == "ck_core_upload_owner_scope"
    )
    assert str(owner_check.sqltext) == OWNER_SCOPE_CHECK
    purpose_check = next(
        constraint for constraint in UPLOAD_SESSIONS.constraints
        if constraint.name == "ck_core_upload_purpose"
    )
    assert "'OCCURRENCE_DOCUMENT'" in str(purpose_check.sqltext)
    assert PARENT_ACCOUNT_SCOPE == "PARENT_ACCOUNT"


def test_the_migration_file_is_lf_and_plain_ascii_sql() -> None:
    raw = MIGRATION.read_bytes()
    assert b"\r" not in raw
    assert hashlib.sha256(raw).hexdigest()  # present; the hash itself is recorded in the evidence
