from __future__ import annotations

import hashlib
import io
import json
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sketch2life.application.ports.story_run_lite import AssetBinding
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.domain.story_run_lite import OwnerScopeKind
from sketch2life.infrastructure.ai.modal_function_client import (
    MODEL_ID,
    MODEL_REVISION,
    ModalDrawingFunctionClient,
    ModalFunctionOutcomeUnknown,
    ModalFunctionResult,
    prepare_drawing_input,
)
from sketch2life.infrastructure.story_run_lite import photo_bridge as photo_bridge_module
from sketch2life.infrastructure.story_run_lite.composition import (
    UnavailableLoopbackVision,
    _configured_vision,
)
from sketch2life.infrastructure.story_run_lite.photo_bridge import (
    ModalFunctionPhotoVisionBridge,
    PhotoVisionBridge,
)

_LIVE_URL = "https://synthetic-example--vision.modal.run"
_TEST_CREDENTIAL = "synthetic-modal-test-token"
_RUN_ID = "a0000000-0000-4000-8000-000000000001"
_OTHER_RUN_ID = "b0000000-0000-4000-8000-000000000002"
_CONFIG_KEYS = (
    "STORYRUN_LITE_VISION_MODE",
    "STORYRUN_LITE_VISION_LOOPBACK_URL",
    "STORYRUN_LITE_MODAL_BASE_URL",
    "STORYRUN_LITE_MODAL_TOKEN",
    "STORYRUN_LITE_MODAL_RUN_ID",
)


@pytest.fixture
def clean_vision_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for key in _CONFIG_KEYS:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:8778",
        "http://localhost:8778",
        "http://example.com:8778",
        "http://user@127.0.0.1:8778",
        "http://127.0.0.1:8778?redirect=1",
    ],
)
def test_s2_rejects_non_loopback_endpoint_forms(url: str) -> None:
    with pytest.raises(ValueError, match="HTTP loopback"):
        PhotoVisionBridge(engine=object(), repository=object(), base_url=url)  # type: ignore[arg-type]


def test_s2_accepts_only_literal_ipv4_or_ipv6_loopback() -> None:
    PhotoVisionBridge(engine=object(), repository=object(), base_url="http://127.0.0.1:8778")  # type: ignore[arg-type]
    PhotoVisionBridge(engine=object(), repository=object(), base_url="http://[::1]:8778")  # type: ignore[arg-type]


def test_unconfigured_loopback_vision_never_sends() -> None:
    attempt = UnavailableLoopbackVision().analyze()
    assert attempt.state == "FAILED"
    assert attempt.provider_invoked is False
    assert attempt.error_code == "VISION_LOOPBACK_NOT_CONFIGURED"


@pytest.mark.parametrize(
    "url", [_LIVE_URL, _LIVE_URL + ":443", "https://synthetic-example--vision.us-east.modal.run"]
)
def test_explicit_modal_accepts_https_modal_endpoint_with_complete_config(url: str) -> None:
    bridge = PhotoVisionBridge(
        engine=object(),  # type: ignore[arg-type]
        repository=object(),  # type: ignore[arg-type]
        base_url=url,
        modal_live_token=_TEST_CREDENTIAL,
        modal_live_run_id=_RUN_ID,
    )
    assert _TEST_CREDENTIAL not in repr(bridge)


@pytest.mark.parametrize(
    "url",
    [
        "http://synthetic-example--vision.modal.run",
        "https://modal.run",
        "https://not-modal.example",
        "https://example.modal.run.attacker.example",
        "https://example..us-east.modal.run",
        "https://-example.us-east.modal.run",
        "https://example-.us-east.modal.run",
        "https://" + "a" * 64 + ".us-east.modal.run",
        "https://user@example.modal.run",
        "https://user:pass@example.modal.run",
        "https://example.modal.run:444",
        "https://example.modal.run/v2/vision",
        "https://example.modal.run?",
        "https://example.modal.run#",
        "https://example.modal.run?redirect=1",
        "https://example.modal.run#fragment",
        "https://127.0.0.1",
        "http://127.0.0.1:8778",
    ],
)
def test_modal_mode_rejects_unapproved_endpoints_without_exposing_token(url: str) -> None:
    with pytest.raises(ValueError) as error:
        PhotoVisionBridge(
            engine=object(),  # type: ignore[arg-type]
            repository=object(),  # type: ignore[arg-type]
            base_url=url,
            modal_live_token=_TEST_CREDENTIAL,
            modal_live_run_id=_RUN_ID,
        )
    assert _TEST_CREDENTIAL not in str(error.value)


@pytest.mark.parametrize(
    ("token", "run_id"),
    [
        (None, _RUN_ID),
        (_TEST_CREDENTIAL, None),
        ("", _RUN_ID),
        ("synthetic token", _RUN_ID),
        ("synthetic\ttoken", _RUN_ID),
        ("synthetic\r\ntoken", _RUN_ID),
        ("synthetic\x00token", _RUN_ID),
        (_TEST_CREDENTIAL, ""),
        (_TEST_CREDENTIAL, "not-a-uuid"),
        (_TEST_CREDENTIAL, _RUN_ID.upper()),
        (_TEST_CREDENTIAL, _RUN_ID.replace("-", "")),
        (_TEST_CREDENTIAL, "{" + _RUN_ID + "}"),
    ],
)
def test_modal_mode_requires_safe_token_and_canonical_run_id(
    token: str | None, run_id: str | None
) -> None:
    with pytest.raises(ValueError) as error:
        PhotoVisionBridge(
            engine=object(),  # type: ignore[arg-type]
            repository=object(),  # type: ignore[arg-type]
            base_url=_LIVE_URL,
            modal_live_token=token,
            modal_live_run_id=run_id,
        )
    if token:
        assert token not in str(error.value)


def test_modal_mode_refuses_other_run_before_repository_or_ledger() -> None:
    engine = Mock()
    repository = Mock()
    persist = Mock()
    bridge = PhotoVisionBridge(
        engine=engine,
        repository=repository,
        base_url=_LIVE_URL,
        modal_live_token=_TEST_CREDENTIAL,
        modal_live_run_id=_RUN_ID,
    )
    binding = AssetBinding(
        asset_ref="synthetic-asset",
        asset_version=1,
        media_type="image/png",
        sha256="a" * 64,
        byte_size=10,
        owner_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
        owner_scope_ref="synthetic-parent",
    )
    attempt = bridge.analyze(run_id=_OTHER_RUN_ID, binding=binding, persist_success=persist)
    assert attempt.state == "FAILED"
    assert attempt.error_code == "VISION_ATTEMPT_HOLD"
    assert attempt.provider_invoked is False
    assert attempt.result_committed is False
    assert not engine.mock_calls
    assert not repository.mock_calls
    persist.assert_not_called()


def test_modal_transport_uses_bearer_and_never_reposts_after_sent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = Mock()
    repository.get_dispatch_context.return_value = {
        "provider_job_id": "synthetic-job",
        "provider_attempt_id": "synthetic-attempt",
    }
    guard = Mock()
    guard.state = SimpleNamespace(value="SENT")
    guard.response_metadata = SimpleNamespace(body_sha256=None)
    guard.finalize.return_value = True
    transport = Mock()
    transport.post_json.return_value = {}
    transport_class = Mock(return_value=transport)
    monkeypatch.setattr(photo_bridge_module, "InvocationLedger", Mock())
    monkeypatch.setattr(photo_bridge_module, "InvocationLedgerGuard", Mock(return_value=guard))
    monkeypatch.setattr(photo_bridge_module, "HttpJsonTransport", transport_class)

    def create_adapter(*, transport, **_kwargs):
        adapter = Mock()

        def call_twice(_request):
            transport.post_json("/v2/vision", {})
            transport.post_json("/v2/vision", {})

        adapter.understand.side_effect = call_twice
        return adapter

    monkeypatch.setattr(photo_bridge_module, "LightningVisionV2Adapter", create_adapter)
    bridge = PhotoVisionBridge(
        engine=Mock(),
        repository=repository,
        base_url=_LIVE_URL,
        modal_live_token=_TEST_CREDENTIAL,
        modal_live_run_id=_RUN_ID,
    )
    binding = AssetBinding(
        asset_ref="synthetic-asset",
        asset_version=1,
        media_type="image/png",
        sha256="a" * 64,
        byte_size=10,
        owner_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
        owner_scope_ref="synthetic-parent",
    )
    persist = Mock()
    attempt = bridge.analyze(run_id=_RUN_ID, binding=binding, persist_success=persist)
    assert transport_class.call_args.kwargs["headers"] == {
        "Authorization": f"Bearer {_TEST_CREDENTIAL}"
    }
    transport.post_json.assert_called_once()
    assert attempt.state == "UNKNOWN"
    assert attempt.provider_invoked is True
    assert attempt.result_committed is False
    guard.finalize.assert_called_once()
    persist.assert_not_called()


def test_default_composition_remains_unavailable_without_endpoint(
    clean_vision_env: pytest.MonkeyPatch,
) -> None:
    vision = _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]
    assert isinstance(vision, UnavailableLoopbackVision)


def test_default_composition_preserves_literal_loopback(
    clean_vision_env: pytest.MonkeyPatch,
) -> None:
    clean_vision_env.setenv("STORYRUN_LITE_VISION_LOOPBACK_URL", "http://127.0.0.1:8778")
    vision = _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]
    assert isinstance(vision, PhotoVisionBridge)
    assert vision._base_url == "http://127.0.0.1:8778"


def test_explicit_modal_composition_requires_and_accepts_all_live_fields(
    clean_vision_env: pytest.MonkeyPatch,
) -> None:
    clean_vision_env.setenv("STORYRUN_LITE_VISION_MODE", "modal_live")
    clean_vision_env.setenv("STORYRUN_LITE_MODAL_BASE_URL", _LIVE_URL)
    clean_vision_env.setenv("STORYRUN_LITE_MODAL_TOKEN", _TEST_CREDENTIAL)
    clean_vision_env.setenv("STORYRUN_LITE_MODAL_RUN_ID", _RUN_ID)
    vision = _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]
    assert isinstance(vision, PhotoVisionBridge)
    assert _TEST_CREDENTIAL not in repr(vision)


@pytest.mark.parametrize(
    "missing",
    ["STORYRUN_LITE_MODAL_BASE_URL", "STORYRUN_LITE_MODAL_TOKEN", "STORYRUN_LITE_MODAL_RUN_ID"],
)
def test_explicit_modal_composition_fails_closed_when_a_field_is_missing(
    clean_vision_env: pytest.MonkeyPatch, missing: str
) -> None:
    values = {
        "STORYRUN_LITE_VISION_MODE": "modal_live",
        "STORYRUN_LITE_MODAL_BASE_URL": _LIVE_URL,
        "STORYRUN_LITE_MODAL_TOKEN": _TEST_CREDENTIAL,
        "STORYRUN_LITE_MODAL_RUN_ID": _RUN_ID,
    }
    for key, value in values.items():
        if key != missing:
            clean_vision_env.setenv(key, value)
    with pytest.raises(ValueError) as error:
        _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]
    assert _TEST_CREDENTIAL not in str(error.value)


@pytest.mark.parametrize(
    "values",
    [
        {"STORYRUN_LITE_VISION_MODE": "unknown"},
        {"STORYRUN_LITE_MODAL_BASE_URL": _LIVE_URL},
        {"STORYRUN_LITE_MODAL_TOKEN": _TEST_CREDENTIAL},
        {"STORYRUN_LITE_MODAL_RUN_ID": _RUN_ID},
        {
            "STORYRUN_LITE_VISION_MODE": "modal_live",
            "STORYRUN_LITE_VISION_LOOPBACK_URL": "http://127.0.0.1:8778",
            "STORYRUN_LITE_MODAL_BASE_URL": _LIVE_URL,
            "STORYRUN_LITE_MODAL_TOKEN": _TEST_CREDENTIAL,
            "STORYRUN_LITE_MODAL_RUN_ID": _RUN_ID,
        },
    ],
)
def test_composition_rejects_ambiguous_live_configuration(
    clean_vision_env: pytest.MonkeyPatch, values: dict[str, str]
) -> None:
    for key, value in values.items():
        clean_vision_env.setenv(key, value)
    with pytest.raises(ValueError) as error:
        _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]
    assert _TEST_CREDENTIAL not in str(error.value)


def _tiny_png() -> bytes:
    from PIL import Image

    output = io.BytesIO()
    Image.new("RGB", (12, 12), "white").save(output, format="PNG")
    return output.getvalue()


def _prepared_input():
    source = _tiny_png()
    return source, prepare_drawing_input(
        source_bytes=source,
        source_media_type="image/png",
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        job_id="synthetic-job",
        generation_id="generation-1",
        attempt_id="synthetic-attempt",
    )


def test_modal_drawing_input_is_hash_bound_and_contains_only_worker_references():
    source, prepared = _prepared_input()
    manifest = json.loads(prepared.manifest)

    assert prepared.drawing_png.startswith(b"\x89PNG\r\n\x1a\n")
    assert (
        hashlib.sha256(source).hexdigest() != prepared.drawing_sha256
        or source == prepared.drawing_png
    )
    assert manifest["asset"]["sha256"] == prepared.drawing_sha256
    assert manifest["asset"]["size_bytes"] == len(prepared.drawing_png)
    assert prepared.payload["workload"] == "drawing.analyze"
    assert prepared.payload["input_manifest_sha256"] == prepared.manifest_sha256
    assert set(prepared.payload) == {
        "schema_version",
        "environment",
        "workload",
        "job_id",
        "generation_id",
        "attempt_id",
        "attempt_prefix",
        "input_manifest_ref",
        "input_manifest_sha256",
        "input_bytes",
    }
    assert source not in repr(prepared.payload).encode("utf-8")


def test_modal_function_client_stages_once_invokes_once_and_cleans_attempt_prefix():
    source, prepared = _prepared_input()
    writes: list[tuple[str, bytes]] = []

    class Batch:
        def put_file(self, stream, path):
            writes.append((path, stream.read()))

    class Volume:
        @contextmanager
        def batch_upload(self):
            yield Batch()

        def remove_file(self, path, *, recursive):
            self.removed = (path, recursive)

    output = {
        "schema_version": "sketch2life.modal.worker-output.v1",
        "workload": "drawing.analyze",
        "job_id": prepared.payload["job_id"],
        "generation_id": prepared.payload["generation_id"],
        "attempt_id": prepared.payload["attempt_id"],
        "input_sha256": prepared.drawing_sha256,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "result": {
            "candidate_subject": "con bướm",
            "visible_features": ["hai cặp cánh", "thân dài"],
            "decision": "NEEDS_ADULT_CONFIRMATION",
            "adult_confirmation_required": True,
        },
    }
    handle = Mock()
    handle.object_id = "fc-synthetic-test"
    handle.get.return_value = output
    function = Mock()
    function.spawn.return_value = handle
    volume = Volume()
    result = ModalDrawingFunctionClient(volume=volume, function=function).invoke(prepared)

    function.spawn.assert_called_once_with(prepared.payload)
    handle.get.assert_called_once()
    assert len(writes) == 2
    assert writes[0] == (f"/{prepared.attempt_prefix}input/drawing.png", prepared.drawing_png)
    assert writes[1] == (f"/{prepared.attempt_prefix}input/manifest.json", prepared.manifest)
    assert volume.removed == (f"{prepared.attempt_prefix}input", True)
    assert result.call_id == "fc-synthetic-test"
    assert (
        result.output_sha256 == hashlib.sha256(canonical_json(output).encode("utf-8")).hexdigest()
    )
    assert source not in repr(prepared.payload).encode("utf-8")


def test_modal_function_timeout_keeps_scratch_input_for_pending_worker():
    _source, prepared = _prepared_input()

    class Batch:
        def put_file(self, _stream, _path):
            return None

    class Volume:
        removed = False

        @contextmanager
        def batch_upload(self):
            yield Batch()

        def remove_file(self, _path, *, recursive):
            self.removed = True

    handle = Mock()
    handle.object_id = "fc-synthetic-pending"
    handle.get.side_effect = TimeoutError()
    function = Mock()
    function.spawn.return_value = handle
    volume = Volume()

    with pytest.raises(ModalFunctionOutcomeUnknown) as error:
        ModalDrawingFunctionClient(volume=volume, function=function, timeout_seconds=0.1).invoke(
            prepared
        )

    assert error.value.call_id == "fc-synthetic-pending"
    assert volume.removed is False
    function.spawn.assert_called_once()


def test_modal_function_composition_requires_only_pinned_synthetic_run(
    clean_vision_env: pytest.MonkeyPatch,
) -> None:
    clean_vision_env.setenv("STORYRUN_LITE_VISION_MODE", "modal_function")
    clean_vision_env.setenv("STORYRUN_LITE_MODAL_RUN_ID", _RUN_ID)
    bridge = _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]
    assert isinstance(bridge, ModalFunctionPhotoVisionBridge)
    assert bridge._pinned_run_id == _RUN_ID


def test_modal_function_composition_rejects_missing_or_legacy_credentials(
    clean_vision_env: pytest.MonkeyPatch,
) -> None:
    clean_vision_env.setenv("STORYRUN_LITE_VISION_MODE", "modal_function")
    with pytest.raises(ValueError, match="incomplete or ambiguous"):
        _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]

    clean_vision_env.setenv("STORYRUN_LITE_MODAL_RUN_ID", _RUN_ID)
    clean_vision_env.setenv("STORYRUN_LITE_MODAL_TOKEN", _TEST_CREDENTIAL)
    with pytest.raises(ValueError, match="incomplete or ambiguous") as error:
        _configured_vision(engine=object(), repository=object())  # type: ignore[arg-type]
    assert _TEST_CREDENTIAL not in str(error.value)


def test_modal_function_bridge_persists_only_correlated_adult_review_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, prepared = _prepared_input()
    output = {
        "schema_version": "sketch2life.modal.worker-output.v1",
        "workload": "drawing.analyze",
        "job_id": prepared.payload["job_id"],
        "generation_id": prepared.payload["generation_id"],
        "attempt_id": prepared.payload["attempt_id"],
        "input_sha256": prepared.drawing_sha256,
        "model": {"id": MODEL_ID, "revision": MODEL_REVISION},
        "result": {
            "candidate_subject": "con bướm",
            "visible_features": ["hai cặp cánh"],
            "decision": "NEEDS_ADULT_CONFIRMATION",
            "adult_confirmation_required": True,
        },
    }
    output_sha256 = hashlib.sha256(canonical_json(output).encode("utf-8")).hexdigest()
    modal_result = ModalFunctionResult(
        output=output,
        call_id="fc-synthetic-success",
        output_sha256=output_sha256,
        elapsed_seconds=1.2,
    )
    repository = Mock()
    repository.get_dispatch_context.return_value = {
        "run_id": _RUN_ID,
        "actor_scope_kind": OwnerScopeKind.PARENT_ACCOUNT.value,
        "actor_scope_ref": "synthetic-parent-local-v1",
        "provider_job_id": "synthetic-job",
        "provider_attempt_id": "synthetic-attempt",
        "derived_asset_ref": "synthetic-asset",
        "derived_sha256": hashlib.sha256(source).hexdigest(),
        "derived_media_type": "image/png",
    }
    repository.read_asset.return_value = source
    client = Mock()
    client.invoke.return_value = modal_result

    class Guard:
        state = SimpleNamespace(value="SENT")
        response_metadata = SimpleNamespace(
            status_code=None,
            body_sha256=None,
            body_complete=False,
            json_object=False,
            within_deadline=False,
            bridge_validated=False,
        )

        def claim(self):
            return None

        def mark_sent(self):
            return None

        def record_response(self, **values):
            for key, value in values.items():
                setattr(self.response_metadata, key, value)

        def mark_bridge_outcome_validated(self):
            self.response_metadata.bridge_validated = True

        def finalize(self, _state, _result_sha256):
            return True

    guard = Guard()
    monkeypatch.setattr(photo_bridge_module, "InvocationLedger", Mock())
    monkeypatch.setattr(photo_bridge_module, "InvocationLedgerGuard", Mock(return_value=guard))
    bridge = ModalFunctionPhotoVisionBridge(
        engine=Mock(),
        repository=repository,
        pinned_run_id=_RUN_ID,
        client=client,
    )
    binding = AssetBinding(
        asset_ref="synthetic-asset",
        asset_version=1,
        media_type="image/png",
        sha256=hashlib.sha256(source).hexdigest(),
        byte_size=len(source),
        owner_scope_kind=OwnerScopeKind.PARENT_ACCOUNT,
        owner_scope_ref="synthetic-parent-local-v1",
    )
    persist = Mock(return_value=True)

    attempt = bridge.analyze(run_id=_RUN_ID, binding=binding, persist_success=persist)

    assert attempt.state == "SUCCEEDED"
    assert attempt.provider_invoked is True
    assert attempt.result_committed is True
    persisted = persist.call_args.args[0]
    assert persisted.subject_label == "con bướm"
    assert persisted.confidence == 0.0
    assert persisted.result_snapshot["result"]["adult_confirmation_required"] is True
    client.invoke.assert_called_once()
