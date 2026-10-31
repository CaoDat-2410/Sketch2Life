"""S2 photo bridge through the existing V2 adapter and A1 invocation guard."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy import Engine

from sketch2life.application.ports.story_run_lite import (
    AssetBinding,
    StoryRunLiteRepositoryPort,
    ValidatedVisionResult,
    VisionAttemptResult,
)
from sketch2life.application.ports.vision_analysis import InvocationTerminalState
from sketch2life.contracts.schemas.vision import (
    ActionCandidateV1,
    EntityCandidateV1,
    ThemeCandidateV1,
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionProfileIdV2,
    VisionUnderstandingFailureV2,
    VisionUnderstandingRequestV2,
    VisionUnderstandingSuccessV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.domain.ai_jobs.completion import canonical_json
from sketch2life.domain.vision_analysis import document_sha256
from sketch2life.infrastructure.ai.lightning_vision_v2 import LightningVisionV2Adapter
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)
from sketch2life.infrastructure.vision_analysis.invocation_guard import InvocationLedgerGuard
from sketch2life.infrastructure.vision_analysis.ledger import InvocationLedger, InvocationState
from sketch2life.infrastructure.vision_analysis.legacy_v2 import (
    verify_v2_failure,
    verify_v2_success,
)
from sketch2life.infrastructure.vision_analysis.transport import HttpJsonTransport

_TECHNICAL_ORGANIZATION_ID = "storyrun-lite-photo-bridge-v1"
_ENDPOINT_PATH = "/v2/vision"
_MODAL_HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+modal\.run\Z")
_BEARER_PATTERN = re.compile(r"[\x21-\x7e]{1,4096}\Z")


class _RecordingTransport:
    """Retain only the parsed response needed for strict bridge validation."""

    def __init__(self, inner: HttpJsonTransport) -> None:
        self._inner = inner
        self.raw: Mapping[str, object] | None = None
        self.calls = 0

    def post_json(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        if self.calls:
            raise RuntimeError("StoryRun-lite makes at most one V2 request per attempt")
        self.calls += 1
        response = self._inner.post_json(path, payload)
        self.raw = response
        return response


class PhotoVisionBridge:
    """Invoke V2 once for a Core-admitted derived image and commit Story before finalizing A1."""

    def __init__(
        self,
        *,
        engine: Engine,
        repository: StoryRunLiteRepositoryPort,
        base_url: str,
        total_timeout_seconds: float = 160.0,
        modal_live_token: str | None = None,
        modal_live_run_id: str | None = None,
    ) -> None:
        try:
            parsed = urlsplit(base_url)
            port = parsed.port
        except (TypeError, ValueError):
            raise ValueError("StoryRun-lite Vision endpoint configuration is invalid") from None
        live = modal_live_token is not None or modal_live_run_id is not None
        if live:
            try:
                valid_run = modal_live_run_id is not None and str(UUID(modal_live_run_id)) == (
                    modal_live_run_id
                )
            except (TypeError, ValueError):
                valid_run = False
            if (
                not isinstance(modal_live_token, str)
                or _BEARER_PATTERN.fullmatch(modal_live_token) is None
                or not valid_run
                or parsed.scheme != "https"
                or parsed.hostname is None
                or len(parsed.hostname) > 253
                or _MODAL_HOST.fullmatch(parsed.hostname) is None
                or port not in {None, 443}
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or "?" in base_url
                or "#" in base_url
                or parsed.query
                or parsed.fragment
                or not 0 < total_timeout_seconds <= 300
            ):
                raise ValueError("StoryRun-lite Modal live configuration is invalid")
        elif (
            parsed.scheme != "http"
            or parsed.hostname not in {"127.0.0.1", "::1"}
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("StoryRun-lite S2 only permits an HTTP loopback Vision endpoint")
        self._engine = engine
        self._repository = repository
        self._base_url = base_url
        self._timeout = total_timeout_seconds
        self._modal_live_token = modal_live_token
        self._modal_live_run_id = modal_live_run_id

    def analyze(
        self,
        *,
        run_id: str,
        binding: AssetBinding,
        persist_success: Callable[[ValidatedVisionResult], bool],
    ) -> VisionAttemptResult:
        if self._modal_live_run_id is not None and run_id != self._modal_live_run_id:
            return VisionAttemptResult(state="FAILED", error_code="VISION_ATTEMPT_HOLD")
        if binding.media_type not in {"image/jpeg", "image/png"} or binding.byte_size > 5_000_000:
            return VisionAttemptResult(state="FAILED", error_code="MODEL_INPUT_NOT_ADMITTED")
        try:
            context = self._repository.get_dispatch_context(run_id=run_id)
        except Exception:
            return VisionAttemptResult(state="FAILED", error_code="VISION_ATTEMPT_HOLD")
        job_id = str(context["provider_job_id"])
        attempt_id = str(context["provider_attempt_id"])
        ledger = InvocationLedger(self._engine)
        guard = InvocationLedgerGuard(
            ledger=ledger,
            run_id=run_id,
            job_id=job_id,
            attempt_id=attempt_id,
            organization_id=_TECHNICAL_ORGANIZATION_ID,
        )
        try:
            inner = HttpJsonTransport(
                base_url=self._base_url,
                guard=guard,
                total_timeout_seconds=self._timeout,
                headers=(
                    {"Authorization": f"Bearer {self._modal_live_token}"}
                    if self._modal_live_token is not None
                    else None
                ),
            )
        except (TypeError, ValueError):
            return VisionAttemptResult(state="FAILED", error_code="VISION_ENDPOINT_NOT_ALLOWED")
        transport = _RecordingTransport(inner)
        request = self._request(run_id, binding)
        adapter = LightningVisionV2Adapter(
            transport=transport,
            artifact_loader=lambda artifact_ref: self._repository.read_asset(artifact_ref),
            endpoint_path=_ENDPOINT_PATH,
            max_input_bytes=5_000_000,
        )
        try:
            result = adapter.understand(request)
        except Exception:
            return self._terminal_failure(guard, "VISION_ADAPTER_FAILURE")

        raw = transport.raw
        if isinstance(result, VisionUnderstandingSuccessV2):
            try:
                mismatch = self._verify_success(result, request, raw)
            except Exception:
                mismatch = "BRIDGE_VALIDATION_FAILED"
            if mismatch is not None or not _guard_response_ready(guard):
                return self._terminal_unknown(guard, "VISION_RESPONSE_INVALID")
            assert raw is not None
            raw_hash = guard.response_metadata.body_sha256
            canonical_document = canonical_json(result.model_dump(mode="json"))
            canonical_hash = document_sha256(canonical_document)
            if len(canonical_document.encode("utf-8")) > 256 * 1024:
                return self._terminal_unknown(guard, "VISION_RESPONSE_INVALID")
            label, confidence = _subject_projection(result)
            try:
                accepted = persist_success(
                    ValidatedVisionResult(
                        result_snapshot=result.model_dump(mode="json"),
                        subject_label=label,
                        confidence=confidence,
                        canonical_result_sha256=canonical_hash,
                        raw_body_sha256=raw_hash,
                    )
                )
            except Exception:
                return self._terminal_unknown(guard, "STORY_RESULT_PERSISTENCE_UNKNOWN")
            inner.mark_bridge_outcome_validated()
            if not accepted:
                guard.finalize(InvocationTerminalState.FAILED, raw_hash)
                return VisionAttemptResult(
                    state="FAILED",
                    error_code="VISION_RESULT_CAS_LOST",
                    provider_invoked=True,
                    result_committed=False,
                )
            finalized = guard.finalize(InvocationTerminalState.SUCCEEDED, raw_hash)
            if not finalized:
                return VisionAttemptResult(
                    state="UNKNOWN",
                    error_code="VISION_LEDGER_FINALIZATION_UNKNOWN",
                    provider_invoked=True,
                    result_committed=True,
                )
            return VisionAttemptResult(
                state="SUCCEEDED", provider_invoked=True, result_committed=True
            )

        if isinstance(result, VisionUnderstandingFailureV2):
            try:
                mismatch = self._verify_failure(result, request, raw)
            except Exception:
                mismatch = "BRIDGE_VALIDATION_FAILED"
            if mismatch is None and _guard_response_ready(guard):
                raw_hash = guard.response_metadata.body_sha256
                inner.mark_bridge_outcome_validated()
                if guard.finalize(InvocationTerminalState.FAILED, raw_hash):
                    return VisionAttemptResult(
                        state="FAILED",
                        error_code=f"VISION_{result.error_code.value}",
                        provider_invoked=guard.state.value != "FAILED" or raw_hash is not None,
                    )
                return VisionAttemptResult(
                    state="UNKNOWN",
                    error_code="VISION_LEDGER_FINALIZATION_UNKNOWN",
                    provider_invoked=True,
                )
        return self._terminal_unknown(guard, "VISION_RESPONSE_INVALID")

    def reconcile_completed_results(self) -> dict[str, int]:
        """Finish ledger rows for already committed Story results; never dispatch a request."""

        complete = 0
        unavailable = 0
        ledger = InvocationLedger(self._engine)
        rows = self._repository.pending_vision_ledger_reconciliation()
        for row in rows:
            try:
                record = ledger.get(str(row["run_id"]))
                if (
                    record is None
                    or record.job_id != row["provider_job_id"]
                    or record.attempt_id != row["provider_attempt_id"]
                    or record.organization_id != _TECHNICAL_ORGANIZATION_ID
                    or record.state is not InvocationState.SENT
                ):
                    continue
                if ledger.complete(
                    run_id=record.run_id,
                    job_id=record.job_id,
                    attempt_id=record.attempt_id,
                    organization_id=record.organization_id,
                    state=InvocationState.SUCCEEDED.value,
                    result_sha256=str(row["raw_body_sha256"]),
                ):
                    complete += 1
            except Exception:
                unavailable += 1
        return {"completed": complete, "unavailable": unavailable}

    def _request(self, run_id: str, binding: AssetBinding) -> VisionUnderstandingRequestV2:
        evidence = {
            "contract": "StoryRunLitePhotoAdmissionV1",
            "run_ref": run_id,
            "derived_asset_ref": binding.asset_ref,
            "derived_asset_sha256": binding.sha256,
            "derived_media_type": binding.media_type,
            "derived_size_bytes": binding.byte_size,
        }
        evidence_bytes = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
        validation_sha = hashlib.sha256(evidence_bytes).hexdigest()
        return VisionUnderstandingRequestV2(
            correlation_id=run_id,
            source_image_ref=VisionImageReferenceV1(
                artifact_ref=binding.asset_ref,
                sha256=binding.sha256,
            ),
            media_validation=VisionMediaValidationProvenanceV1(
                validation_artifact_ref=f"storyrun-lite-admission:{binding.asset_ref}",
                validation_artifact_sha256=validation_sha,
                decision="PASS",
                validator_policy_version="storyrun-photo-v1",
            ),
            requested_profile_id=VisionProfileIdV2.QWEN3_VL_8B_INSTRUCT_BF16_V1,
        )

    @staticmethod
    def _verify_success(
        result: VisionUnderstandingSuccessV2,
        request: VisionUnderstandingRequestV2,
        raw: Mapping[str, object] | None,
    ) -> str | None:
        catalog = vision_profile_catalog_v2()
        profile = catalog.resolve(request.requested_profile_id)
        policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
        mismatch = verify_v2_success(
            result, request, raw, catalog=catalog, profile=profile, policy=policy
        )
        if mismatch is not None:
            return mismatch
        if result.profile_catalog_hash != vision_profile_catalog_hash_v2(catalog):
            return "CATALOG_HASH_MISMATCH"
        if result.config_hash != vision_profile_config_hash_v2(profile):
            return "CONFIG_HASH_MISMATCH"
        return None

    @staticmethod
    def _verify_failure(
        result: VisionUnderstandingFailureV2,
        request: VisionUnderstandingRequestV2,
        raw: Mapping[str, object] | None,
    ) -> str | None:
        catalog = vision_profile_catalog_v2()
        profile = catalog.resolve(request.requested_profile_id)
        policy = LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())
        return verify_v2_failure(
            result, request, raw, catalog=catalog, profile=profile, policy=policy
        )

    @staticmethod
    def _terminal_failure(guard: InvocationLedgerGuard, code: str) -> VisionAttemptResult:
        if guard.state.value == "SENT":
            return PhotoVisionBridge._terminal_unknown(guard, code)
        if guard.state.value in {"UNKNOWN", "PRIOR_OUTCOME_UNKNOWN"}:
            return VisionAttemptResult(state="UNKNOWN", error_code=code, provider_invoked=True)
        return VisionAttemptResult(state="FAILED", error_code=code, provider_invoked=False)

    @staticmethod
    def _terminal_unknown(guard: InvocationLedgerGuard, code: str) -> VisionAttemptResult:
        was_sent = guard.state.value == "SENT"
        if was_sent:
            guard.finalize(InvocationTerminalState.UNKNOWN, guard.response_metadata.body_sha256)
        prior_outcome_unknown = guard.state.value in {"UNKNOWN", "PRIOR_OUTCOME_UNKNOWN"}
        return VisionAttemptResult(
            state="UNKNOWN" if was_sent or prior_outcome_unknown else "FAILED",
            error_code=code,
            provider_invoked=was_sent or prior_outcome_unknown,
        )


def _subject_projection(result: VisionUnderstandingSuccessV2) -> tuple[str, float]:
    candidates: list[EntityCandidateV1 | ActionCandidateV1 | ThemeCandidateV1] = [
        *result.entities,
        *result.actions,
        *result.themes,
    ]
    if not candidates:
        return "No clear subject", 0.0
    candidate = max(
        candidates,
        key=lambda item: item.confidence if item.confidence is not None else 0.0,
    )
    return (
        candidate.label.value[:256],
        float(candidate.confidence) if candidate.confidence is not None else 0.0,
    )


def _guard_response_ready(guard: InvocationLedgerGuard) -> bool:
    metadata = guard.response_metadata
    return (
        guard.state.value == "SENT"
        and metadata.status_code == 200
        and metadata.body_complete
        and metadata.json_object
        and metadata.within_deadline
        and metadata.body_sha256 is not None
    )


__all__ = ["PhotoVisionBridge"]
