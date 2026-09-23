from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from sketch2life.application.services.ephemeral_sessions import EphemeralSessionService
from sketch2life.application.services.image_admission import Feat018ImageAdmission
from sketch2life.application.services.live_image_demo import LiveImageDemoService
from sketch2life.application.services.p1_experience import P1ExperienceCompiler
from sketch2life.application.services.supervised_flow import SupervisedFlowService
from sketch2life.contracts.schemas.vision import (
    VISION_POLICY_MATCH_VIEW_VERSION,
    EntityCandidateV1,
    ObservedTextV1,
    TextLanguageDeclarationV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.understanding.image_admission import (
    DecodedFrameSignals,
    ImageMetadataSignals,
)
from sketch2life.infrastructure.ai.vision_lexical_policy import synthetic_prohibited_lexicon
from sketch2life.infrastructure.catalog.activity_semantics import load_activity_semantic_catalog
from sketch2life.infrastructure.catalog.activity_semantics_v2 import (
    load_activity_semantic_catalog_v2,
)
from sketch2life.infrastructure.catalog.p1_catalog import load_p1_template_library
from sketch2life.infrastructure.catalog.workflow_metadata import FileWorkflowCatalogMetadata
from sketch2life.infrastructure.storage.in_memory import (
    InMemoryArtifactStore,
    InMemoryIdempotencyStore,
    InMemorySessionRepository,
)
from sketch2life.infrastructure.storage.in_memory_demo_workflow import (
    InMemoryDemoWorkflowStore,
)
from sketch2life.infrastructure.storage.in_memory_renderer_source_grants import (
    InMemoryRendererSourceGrantStore,
)
from sketch2life.interfaces.http.app import create_app

_IMAGE = b"\x89PNG\r\n\x1a\nsynthetic-only-image-fixture"


def _contains_none(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, dict):
        return any(_contains_none(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_none(item) for item in value)
    return False


class _TestImageDecoder:
    def read_metadata(self, snapshot: bytes) -> ImageMetadataSignals | None:
        if not snapshot.startswith(b"\x89PNG\r\n\x1a\n"):
            return None
        return ImageMetadataSignals("png_pipe", "png", "rgb24", 64, 64)

    def probe_frame_count(self, snapshot: bytes) -> int:
        return 1

    def decode_one_frame(self, snapshot: bytes) -> DecodedFrameSignals:
        return DecodedFrameSignals(64, 64, "rgb24")


class _CountingVision:
    def __init__(self, *, label: str = "cây", empty: bool = False) -> None:
        self.calls = 0
        self.label = label
        self.empty = empty

    def understand(self, request: VisionUnderstandingRequestV2) -> VisionUnderstandingSuccessV2:
        self.calls += 1
        catalog = vision_profile_catalog_v2()
        profile = catalog.resolve(request.requested_profile_id)
        policy = synthetic_prohibited_lexicon()
        return VisionUnderstandingSuccessV2(
            correlation_id=request.correlation_id,
            executed_at=datetime(2026, 9, 18, tzinfo=UTC),
            source_image_ref=request.source_image_ref,
            profile_id=profile.profile_id,
            profile_catalog_hash=vision_profile_catalog_hash_v2(catalog),
            attempt_number=1,
            repair_attempted=False,
            content_policy_version=policy.lexicon_version,
            policy_match_view_version=VISION_POLICY_MATCH_VIEW_VERSION,
            policy_execution_state="PASSED",
            status="SUCCEEDED",
            entities=() if self.empty else (
                EntityCandidateV1(
                    observation_id="subject-1",
                    label=ObservedTextV1(
                        value=self.label,
                        language=TextLanguageDeclarationV1(status="DECLARED", tags=("vi",)),
                    ),
                    confidence=0.96,
                ),
            ),
            actions=(),
            relations=(),
            themes=(),
            ambiguous_regions=(),
            adapter_version=profile.adapter_version,
            config_hash=vision_profile_config_hash_v2(profile),
            model_provenance=profile.model_provenance,
        )


def _client(*, vision: _CountingVision | None = None) -> tuple[TestClient, _CountingVision]:
    artifacts = InMemoryArtifactStore()
    idempotency = InMemoryIdempotencyStore()
    sessions = EphemeralSessionService(
        sessions=InMemorySessionRepository(),
        idempotency=idempotency,
        artifacts=artifacts,
        workflow_data=InMemoryDemoWorkflowStore(),
    )
    actual_vision = vision or _CountingVision()
    demo = LiveImageDemoService(
        sessions=sessions,
        artifacts=artifacts,
        idempotency=idempotency,
        admission=Feat018ImageAdmission(_TestImageDecoder()),
        vision=actual_vision,
        renderer_source_grants=InMemoryRendererSourceGrantStore(),
    )
    repo_root = Path(__file__).resolve().parents[3]
    p1_library = load_p1_template_library(
        repo_root, include_mvp=True, include_expansion=True
    )
    semantic_catalog = load_activity_semantic_catalog(repo_root)
    semantic_catalog_v2 = load_activity_semantic_catalog_v2(
        repo_root, include_expansion=True
    )
    supervised_flow = SupervisedFlowService(
        sessions=sessions,
        idempotency=idempotency,
        p1_compiler=P1ExperienceCompiler(
            p1_library.templates,
            p1_library.objective_titles_vi,
        ),
        semantic_catalog=semantic_catalog,
        semantic_catalog_v2=semantic_catalog_v2,
        catalog_metadata=FileWorkflowCatalogMetadata(repo_root),
        renderer_source_capability_issuer=demo.issue_renderer_source_capability,
    )
    return TestClient(
        create_app(
            session_service=sessions,
            live_image_demo_service=demo,
            supervised_flow_service=supervised_flow,
        )
    ), actual_vision


def _create_session(client: TestClient) -> tuple[str, int]:
    session_id = "d5f439fa-3065-4a5e-a06e-52a57514781f"
    response = client.post(
        "/v1/sessions",
        json={
            "request_id": "create-request-1",
            "idempotency_key": "create-key-1",
            "session_id": session_id,
            "expected_session_version": 0,
            "actor_ref": "demo:local",
            "payload": {"operation": "CREATE_SESSION"},
        },
    )
    assert response.status_code == 201
    return session_id, response.json()["observed_session_version"]


def _headers(session_id: str, version: int, key: str) -> dict[str, str]:
    return {
        "X-Request-ID": f"request-{key}",
        "X-Expected-Session-Version": str(version),
        "Idempotency-Key": key,
        "X-Actor-Ref": "demo:local",
        "X-Synthetic-Non-Child-Confirmed": "true",
    }


def _command(
    client: TestClient,
    *,
    session_id: str,
    version: int,
    key: str,
    route: str,
    payload: dict[str, object],
    method: str = "post",
):
    return getattr(client, method)(
        f"/v1/sessions/{session_id}{route}",
        json={
            "request_id": f"request-{key}",
            "idempotency_key": f"idempotency-{key}",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": payload,
        },
    )


def test_session_image_upload_is_admitted_then_requires_an_explicit_understanding_command() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)

    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "upload-1"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )

    assert uploaded.status_code == 200
    uploaded_body = uploaded.json()
    assert uploaded_body["status"] == "SUCCEEDED"
    assert uploaded_body["payload"]["decision"] == "ADMITTED"
    assert uploaded_body["payload"]["narration_status"] == "NOT_SUPPLIED"
    assert vision.calls == 0
    session_version = uploaded_body["observed_session_version"]

    rejected_implicit = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "understanding-request-implicit",
            "idempotency_key": "understanding-key-implicit",
            "session_id": session_id,
            "expected_session_version": session_version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": False},
        },
    )
    assert rejected_implicit.status_code == 422
    assert vision.calls == 0

    started = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "understanding-request-explicit",
            "idempotency_key": "understanding-key-explicit",
            "session_id": session_id,
            "expected_session_version": session_version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )

    assert started.status_code == 200
    assert started.json()["status"] == "SUCCEEDED"
    assert started.json()["payload"]["narration_status"] == "NOT_SUPPLIED"
    directions = started.json()["payload"]["topic_directions"]
    assert 1 <= len(directions) <= 3
    assert directions[0]["title_vi"].startswith("Cùng khám phá")
    assert directions[0]["source_claim_ids"]
    assert all("chi tiết trong tranh" not in item["title_vi"] for item in directions)
    assert vision.calls == 1


def test_image_upload_requires_synthetic_non_child_confirmation_and_is_idempotent() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    headers = _headers(session_id, version, "upload-once")

    first = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=headers,
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    replay = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=headers,
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert replay.json() == first.json()
    assert vision.calls == 0

    missing_confirmation = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers={
            **_headers(session_id, version, "upload-no-confirmation"),
            "X-Synthetic-Non-Child-Confirmed": "false",
        },
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    assert missing_confirmation.status_code == 422
    assert missing_confirmation.json()["failure"]["code"] == (
        "SYNTHETIC_NON_CHILD_CONFIRMATION_REQUIRED"
    )


def test_typed_narration_is_forwarded_as_text_without_an_asr_call() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "typed-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    started = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "typed-understanding",
            "idempotency_key": "typed-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "RUN_UNDERSTANDING",
                "user_initiated": True,
                "narration": {
                    "kind": "TEXT",
                    "text": "Con mèo đang tìm bông hoa.",
                    "language": "vi",
                    "provenance": "TEXT_TYPED",
                },
            },
        },
    )

    assert started.status_code == 200
    body = started.json()
    assert body["status"] == "SUCCEEDED"
    assert body["payload"]["narration_status"] == "TEXT_SUPPLIED"
    assert body["payload"]["narration"]["transcript"] == "Con mèo đang tìm bông hoa."
    assert body["payload"]["asr_claims"][0]["source"] == "TEXT_TYPED"
    assert vision.calls == 1


def test_empty_vision_result_is_blocked_before_gate_a() -> None:
    client, vision = _client(vision=_CountingVision(empty=True))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "empty-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]

    result = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "empty-understanding",
            "idempotency_key": "empty-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )

    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "BLOCKED"
    assert body["payload"]["reason_codes"] == ["NO_GROUNDED_CLAIMS"]
    assert body["payload"]["understanding_progress"]["gate_a_ready"] is False
    assert body["payload"]["understanding_progress"]["stage"] == "BLOCKED_NO_GROUNDED_CLAIMS"
    assert vision.calls == 1


def test_typed_narration_is_fused_with_matching_visual_claim_and_topic_is_bounded() -> None:
    client, vision = _client(vision=_CountingVision(label="butterfly"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "fusion-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    result = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "fusion-understanding",
            "idempotency_key": "fusion-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "RUN_UNDERSTANDING",
                "user_initiated": True,
                "narration": {
                    "kind": "TEXT",
                    "text": "Con bướm đang bay trên bãi cỏ.",
                    "language": "vi",
                    "provenance": "TEXT_TYPED",
                },
            },
        },
    )

    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "SUCCEEDED"
    assert body["payload"]["fused_claims"]
    topic = body["payload"]["understanding_progress"]["topic"]
    assert 10 <= topic["word_count"] <= 18
    assert "con bướm" in topic["text"]
    assert vision.calls == 1


def test_direction_requery_rechecks_the_admitted_image_and_exposes_progress() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "requery-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    first = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "requery-first",
            "idempotency_key": "requery-first-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    version = first.json()["observed_session_version"]
    second = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "requery-second",
            "idempotency_key": "requery-second-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "REQUERY_UNDERSTANDING",
                "user_initiated": True,
                "prior_run_id": "requery-first",
                "direction_revision": 1,
                "selected_direction": "một hướng quan sát khác",
                "correction": "",
            },
        },
    )

    assert second.status_code == 200
    assert second.json()["status"] == "SUCCEEDED"
    assert second.json()["payload"]["understanding_progress"]["direction_revision"] == 1
    assert second.json()["payload"]["understanding_progress"]["stage"] == "TOPIC_READY"
    assert vision.calls == 2

    progress = client.get(
        f"/v1/sessions/{session_id}/understanding/progress",
        headers={"X-Expected-Session-Version": str(second.json()["observed_session_version"])},
    )
    assert progress.status_code == 200
    assert progress.json()["payload"]["understanding_progress"]["run_id"] == "requery-second"


def test_audio_is_stored_after_image_and_never_sent_without_configured_asr() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "audio-image"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    audio = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"synthetic-wav"
    audio_upload = client.post(
        f"/v1/sessions/{session_id}/media/audio",
        headers={
            "X-Request-ID": "audio-upload",
            "X-Expected-Session-Version": str(version),
            "Idempotency-Key": "audio-upload-key",
            "X-Actor-Ref": "demo:local",
        },
        files={"audio": ("narration.wav", audio, "audio/wav")},
    )
    assert audio_upload.status_code == 200
    receipt = audio_upload.json()["payload"]
    assert receipt["content_type"] == "audio/wav"

    run = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "audio-understanding",
            "idempotency_key": "audio-understanding-key",
            "session_id": session_id,
            "expected_session_version": audio_upload.json()["observed_session_version"],
            "actor_ref": "demo:local",
            "payload": {
                "operation": "RUN_UNDERSTANDING",
                "user_initiated": True,
                "narration": {
                    "kind": "AUDIO",
                    "artifact_ref": receipt["artifact_ref"],
                    "sha256": receipt["sha256"],
                    "content_type": receipt["content_type"],
                    "byte_length": receipt["byte_length"],
                    "provenance": "RECORDED_AUDIO",
                },
            },
        },
    )
    assert run.status_code == 503
    assert run.json()["failure"]["code"] == "LIGHTNING_ASR_NOT_CONFIGURED"
    assert vision.calls == 0


def test_openapi_exposes_image_and_optional_narration_routes_but_not_video() -> None:
    client, _vision = _client()
    paths = client.get("/openapi.json").json()["paths"]
    assert "/v1/sessions/{session_id}/media/image" in paths
    assert "/v1/sessions/{session_id}/media/audio" in paths
    assert "/v1/sessions/{session_id}/understanding" in paths
    assert not any("video" in path for path in paths)
    assert "/v1/live-understanding" not in paths


def test_image_upload_transport_enforces_a_hard_multipart_body_cap() -> None:
    client, _vision = _client()
    response = client.post(
        "/v1/sessions/not-created/media/image",
        content=b"x" * 5_100_001,
        headers={"Content-Type": "multipart/form-data; boundary=unused"},
    )
    assert response.status_code == 413
    assert response.json()["failure"]["code"] == "UPLOAD_TOO_LARGE"


def test_gate_a_unlocks_read_only_p1_context_options_matching_adult_entered_age() -> None:
    client, _vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "options-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    inferred = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "options-understanding",
            "idempotency_key": "options-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    version = inferred.json()["observed_session_version"]
    confirmed = client.post(
        f"/v1/sessions/{session_id}/gate-a/confirm",
        json={
            "request_id": "options-gate-a",
            "idempotency_key": "options-gate-a-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "CONFIRM_GATE_A",
                "user_initiated": True,
                "primary_anchor_id": "subject-1",
                "confirmation": {
                    "contract_name": "GateAConfirmationV1",
                    "contract_version": "1.0",
                    "meaning_version": 1,
                    "confirmed_claim_ids": ["subject-1"],
                    "correction": None,
                },
            },
        },
    )
    assert confirmed.status_code == 200
    version = confirmed.json()["observed_session_version"]

    options = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 30},
        headers={
            "X-Request-ID": "p1-options",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )

    assert options.status_code == 200
    payload = options.json()["payload"]
    assert payload["contract_name"] == "P1ContextOptionsV1"
    assert payload["age_months"] == 30
    assert payload["confirmed_anchor_label"] == "cây"
    assert 1 <= len(payload["options"]) <= 3
    assert payload["activity_recommendations"]["options"]
    assert payload["activity_recommendations"]["options"][0]["title_vi"]
    assert options.json()["observed_session_version"] == version


def test_gate_a_never_uses_age_only_fallback_for_background_only_raw_label() -> None:
    client, _vision = _client(vision=_CountingVision(label="grass"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "fallback-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    inferred = client.post(
        f"/v1/sessions/{session_id}/understanding",
        json={
            "request_id": "fallback-understanding",
            "idempotency_key": "fallback-understanding-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {"operation": "RUN_UNDERSTANDING", "user_initiated": True},
        },
    )
    version = inferred.json()["observed_session_version"]
    confirmed = client.post(
        f"/v1/sessions/{session_id}/gate-a/confirm",
        json={
            "request_id": "fallback-gate-a",
            "idempotency_key": "fallback-gate-a-key",
            "session_id": session_id,
            "expected_session_version": version,
            "actor_ref": "demo:local",
            "payload": {
                "operation": "CONFIRM_GATE_A",
                "user_initiated": True,
                "primary_anchor_id": "subject-1",
                "confirmation": {
                    "contract_name": "GateAConfirmationV1",
                    "contract_version": "1.0",
                    "meaning_version": 1,
                    "confirmed_claim_ids": ["subject-1"],
                    "correction": None,
                },
            },
        },
    )
    assert confirmed.status_code == 200

    options = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 60},
        headers={
            "X-Request-ID": "fallback-options",
            "X-Expected-Session-Version": str(confirmed.json()["observed_session_version"]),
            "X-Actor-Ref": "demo:local",
        },
    )

    assert options.status_code == 200
    payload = options.json()["payload"]
    assert payload["options"]
    assert len(payload["options"]) <= 3
    assert all(item["activity_ref"]["id"] != "ACT-0026" for item in payload["options"])
    assert payload["activity_recommendations"]["options"]


def test_butterfly_non_primary_activity_option_is_strict_fit_without_rerunning_vision() -> None:
    client, vision = _client(vision=_CountingVision(label="butterfly"))
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "butterfly-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    version = uploaded.json()["observed_session_version"]
    inferred = _command(
        client,
        session_id=session_id,
        version=version,
        key="butterfly-understanding",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    version = inferred.json()["observed_session_version"]
    gate_a = _command(
        client,
        session_id=session_id,
        version=version,
        key="butterfly-gate-a",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": "subject-1",
            "confirmation": {
                "contract_name": "GateAConfirmationV1",
                "contract_version": "1.0",
                "meaning_version": 1,
                "confirmed_claim_ids": ["subject-1"],
                "correction": None,
            },
        },
    )
    version = gate_a.json()["observed_session_version"]
    options_response = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 60},
        headers={
            "X-Request-ID": "butterfly-options",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )
    payload = options_response.json()["payload"]
    assert len(payload["options"]) >= 2
    option = payload["options"][1]
    assert option["activity_ref"]["id"].startswith("ACT-01")
    assert len(payload["options"]) <= 3
    assert payload["activity_recommendations"]["options"][0]["title_vi"]
    assert all(item["activity_ref"]["id"] != "ACT-0026" for item in payload["options"])
    assert all(item["activity_ref"]["id"] != "ACT-0029" for item in payload["options"])
    assert vision.calls == 1

    context = _command(
        client,
        session_id=session_id,
        version=version,
        key="butterfly-context",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV1",
                "contract_version": "1.0",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 60,
                "readiness_ids": option["readiness_ids"],
                "completed_activity_ids": option["prerequisite_activity_ids"],
                "available_material_option_ids": option["material_option_ids"],
                "supervision_level": option["minimum_supervision"],
                "policy_flags": option["policy_constraints"],
                "candidate_status": "ACTIVE_FIXTURE",
                "gate_a_confirmed": True,
                "selected_activity_id": option["activity_ref"]["id"],
                "selected_activity_version": option["activity_ref"]["version"],
            },
        },
    )
    filtered = _command(
        client,
        session_id=session_id,
        version=context.json()["observed_session_version"],
        key="butterfly-filter",
        route="/p1-filter",
        payload={"operation": "RUN_P1_FILTER", "user_initiated": True},
    )
    prepared = _command(
        client,
        session_id=session_id,
        version=filtered.json()["observed_session_version"],
        key="butterfly-prepare",
        route="/experience/prepare",
        payload={"operation": "PREPARE_EXPERIENCE", "user_initiated": True},
    )

    assert filtered.json()["status"] == "SUCCEEDED"
    assert prepared.json()["status"] == "SUCCEEDED"
    assert prepared.json()["payload"]["status"] == "AWAITING_ADULT_GATE_B"
    assert (
        prepared.json()["payload"]["experience_spec"]["activity_template"]["activity_ref"]
        == option["activity_ref"]
    )


def test_fake_only_image_session_completes_p1_gate_b_p4_handoff_feedback_and_gallery() -> None:
    client, vision = _client()
    session_id, version = _create_session(client)
    uploaded = client.post(
        f"/v1/sessions/{session_id}/media/image",
        headers=_headers(session_id, version, "full-upload"),
        files={"image": ("synthetic.png", _IMAGE, "image/png")},
    )
    assert uploaded.status_code == 200
    version = uploaded.json()["observed_session_version"]

    inferred = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-understanding",
        route="/understanding",
        payload={"operation": "RUN_UNDERSTANDING", "user_initiated": True},
    )
    assert inferred.status_code == 200
    version = inferred.json()["observed_session_version"]

    gate_a = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-gate-a",
        route="/gate-a/confirm",
        payload={
            "operation": "CONFIRM_GATE_A",
            "user_initiated": True,
            "primary_anchor_id": "subject-1",
            "confirmation": {
                "contract_name": "GateAConfirmationV1",
                "contract_version": "1.0",
                "meaning_version": 1,
                "confirmed_claim_ids": ["subject-1"],
                "correction": None,
            },
        },
    )
    assert gate_a.status_code == 200
    version = gate_a.json()["observed_session_version"]

    options = client.get(
        f"/v1/sessions/{session_id}/p1/context-options",
        params={"age_months": 30},
        headers={
            "X-Request-ID": "full-options",
            "X-Expected-Session-Version": str(version),
            "X-Actor-Ref": "demo:local",
        },
    )
    assert options.status_code == 200
    option = options.json()["payload"]["options"][0]
    context = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-context",
        route="/p1-context",
        method="put",
        payload={
            "operation": "SET_P1_CONTEXT",
            "user_initiated": True,
            "context": {
                "contract_name": "P1ContextV1",
                "contract_version": "1.0",
                "session_id": session_id,
                "expected_session_version": version,
                "age_months": 30,
                "readiness_ids": option["readiness_ids"],
                "completed_activity_ids": option["prerequisite_activity_ids"],
                "available_material_option_ids": option["material_option_ids"],
                "supervision_level": option["minimum_supervision"],
                "policy_flags": option["policy_constraints"],
                "candidate_status": "ACTIVE_FIXTURE",
                "gate_a_confirmed": True,
                "selected_activity_id": option["activity_ref"]["id"],
                "selected_activity_version": option["activity_ref"]["version"],
            },
        },
    )
    assert context.status_code == 200
    version = context.json()["observed_session_version"]

    filtered = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-filter",
        route="/p1-filter",
        payload={"operation": "RUN_P1_FILTER", "user_initiated": True},
    )
    assert filtered.status_code == 200
    assert filtered.json()["payload"]["filter_result"]["status"] == "VALID_CANDIDATE"
    version = filtered.json()["observed_session_version"]

    prepared = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-prepare",
        route="/experience/prepare",
        payload={"operation": "PREPARE_EXPERIENCE", "user_initiated": True},
    )
    assert prepared.status_code == 200
    assert prepared.json()["payload"]["status"] == "AWAITING_ADULT_GATE_B"
    assert prepared.json()["payload"]["generation_called"] is False
    assert vision.calls == 1
    version = prepared.json()["observed_session_version"]

    approved = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-gate-b",
        route="/gate-b/approve",
        payload={"operation": "APPROVE_GATE_B", "user_initiated": True, "approved": True},
    )
    assert approved.status_code == 200
    assert approved.json()["payload"]["generation_called"] is False
    assert approved.json()["payload"]["learning_media"]["fallback_type"] == "WHOLE_IMAGE_REVEAL"
    version = approved.json()["observed_session_version"]

    renderer = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-renderer",
        route="/renderer/launch",
        payload={"operation": "PREPARE_RENDERER", "user_initiated": True},
    )
    assert renderer.status_code == 200
    launch = renderer.json()["payload"]["renderer_launch"]
    assert launch["assetManifest"]["providerGenerationCalled"] is False
    assert not _contains_none(launch)
    assert launch["assetManifest"]["assets"][0]["role"] == "ORIGINAL_ART"
    assert (
        launch["animationPlan"]["plan"]["planId"]
        == approved.json()["payload"]["learning_media"]["renderer_plan_id"]
    )
    assert (
        launch["animationPlan"]["experienceSpecRef"] == launch["assetManifest"]["experienceSpecRef"]
    )
    assert [
        motion["kind"] for motion in launch["animationPlan"]["plan"]["motions"]
    ] == ["DRAW_REVEAL", "SCALE", "MOVE_TO", "ROTATE"]
    storyboard = renderer.json()["payload"]["pixi_intro_storyboard"]
    assert storyboard["original_art_preserved"] is True
    assert storyboard["video_placeholder_only"] is True
    assert len(storyboard["beats"]) == 4
    assert renderer.json()["observed_session_version"] == version

    source_headers = {"X-Render-Source-Capability": launch["sourceReadCapability"]}
    source = client.get("/v1/renderer/source", headers=source_headers)
    assert source.status_code == 200
    assert source.headers["Cache-Control"].startswith("no-store")
    assert source.content == _IMAGE
    assert client.get("/v1/renderer/source", headers=source_headers).content == _IMAGE
    assert client.get("/v1/renderer/source", headers=source_headers).status_code == 404

    handoff = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-handoff",
        route="/handoff",
        payload={"operation": "COMPLETE_HANDOFF", "user_initiated": True},
    )
    assert handoff.status_code == 200
    identity = handoff.json()["payload"]["handoff"]
    version = handoff.json()["observed_session_version"]

    recorded = _command(
        client,
        session_id=session_id,
        version=version,
        key="full-feedback",
        route="/feedback",
        payload={
            "operation": "RECORD_FEEDBACK",
            "user_initiated": True,
            "feedback": {
                "completion_status": "COMPLETED",
                "interest_score": 4,
                "independence_score": 3,
                "observation_tags": [],
            },
        },
    )
    assert recorded.status_code == 200
    assert recorded.json()["payload"]["durable"] is False
    assert recorded.json()["payload"]["feedback"]["activity_ref"] == identity["activity_ref"]
    version = recorded.json()["observed_session_version"]

    gallery = client.get(
        f"/v1/sessions/{session_id}/gallery",
        headers={
            "X-Request-ID": "full-gallery",
            "X-Expected-Session-Version": str(version),
            "Idempotency-Key": "full-gallery-key",
            "X-Actor-Ref": "demo:local",
        },
    )
    assert gallery.status_code == 200
    assert gallery.json()["payload"]["media_bytes_included"] is False
    assert gallery.json()["payload"]["durable"] is False
    assert len(gallery.json()["payload"]["entries"]) >= 5
    assert vision.calls == 1
