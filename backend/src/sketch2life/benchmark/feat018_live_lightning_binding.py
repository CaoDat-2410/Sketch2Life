"""Synthetic offline caller and metadata handoff for FEAT-018 D1/D11.

These wrappers compose the existing offline coordinator and evidence primitives. They
bind no provider, live capability, numeric live budget or runtime commit. Loader and fact
producers are explicit injected fixture boundaries; hashes identify their synthetic data
and never authorize a live run or prove remote cleanup.
"""

from __future__ import annotations

import json
import math
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from typing import Protocol, TypeVar

from pydantic import BaseModel

from sketch2life.application.ports.vision_content_policy import ObservableContentPolicyV1
from sketch2life.benchmark.feat018_live_lightning_execution import (
    CleanupStatus,
    D11OfflineConfig,
    EffectiveOutcome,
    EvidenceCommitResult,
    Feat018ArtifactInventory,
    Feat018CleanupFailedError,
    Feat018EvidenceCommitWriter,
    Feat018IncidentWriter,
    Feat018LiveSmokeConfig,
    Feat018LiveSmokeFailureCode,
    Feat018LiveSmokeResult,
    LightningAdapterDispatchV1,
    LightningFinalizationFacts,
    LightningPreflightFacts,
    LightningResourceObserverV1,
    LightningSessionControllerV1,
    SmokeFinalizationResult,
    _is_bounded_opaque_identifier,
    _validate_terminal_publication_privacy,
    finalize_smoke_run,
    run_offline_live_smoke,
)
from sketch2life.contracts.schemas.feat018_live_binding import (
    BindingManifestV1,
    BindingPreflightFactsV1,
    BindingTerminalMetadataV1,
)
from sketch2life.contracts.schemas.vision_v2 import (
    VisionUnderstandingRequestV2,
    vision_profile_catalog_hash_v2,
    vision_profile_catalog_v2,
    vision_profile_config_hash_v2,
)
from sketch2life.infrastructure.ai.qwen_vision_runtime_config import QwenVisionRuntimeConfig
from sketch2life.infrastructure.ai.vision_lexical_policy import (
    LexicalRegressionContentPolicy,
    synthetic_prohibited_lexicon,
)


class OfflineBindingError(ValueError):
    """A synthetic binding boundary rejected incomplete or inconsistent fixture facts."""


class RuntimeConfigLoader(Protocol):
    def __call__(
        self, env_file: Path, *, environ: Mapping[str, str]
    ) -> QwenVisionRuntimeConfig: ...


_Model = TypeVar("_Model", bound=BaseModel)


def _validated(value: _Model, expected_type: type[_Model]) -> _Model:
    # Revalidate even frozen instances: model_construct/model_copy can bypass validators.
    if type(value) is not expected_type:
        raise OfflineBindingError("a typed synthetic binding carrier is required")
    if set(value.__dict__) != set(expected_type.model_fields):
        raise OfflineBindingError("a synthetic carrier contains undeclared or missing fields")
    return expected_type.model_validate(value.model_dump(mode="python", warnings="error"))


def runtime_config_sha256(config: QwenVisionRuntimeConfig) -> str:
    """Digest the private typed config, not the selected env file's bytes.

    Only this digest enters metadata. Paths/config values remain private and are never
    included in the evidence serializer; the digest is an offline identity comparison.
    """
    if type(config) is not QwenVisionRuntimeConfig:
        raise OfflineBindingError("an explicit Qwen runtime config is required")
    # The existing dataclass constructor is the authority for its normal value shape.
    checked = QwenVisionRuntimeConfig(**asdict(config))
    if (
        type(checked.device_index) is not int
        or type(checked.allow_model_download) is not bool
        or type(checked.device) is not str
        or not checked.device
        or any(value is not None and not isinstance(value, Path)
               for value in (checked.model_dir, checked.model_cache_dir))
    ):
        raise OfflineBindingError("runtime config values have invalid types")
    values = asdict(checked)
    for key in ("model_dir", "model_cache_dir"):
        value = values[key]
        values[key] = value.as_posix() if value is not None else None
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _selected_relative_env_file(value: Path) -> Path:
    if not isinstance(value, Path):
        raise OfflineBindingError("an explicit relative config-file selection is required")
    text = str(value)
    windows_path = PureWindowsPath(text)
    if (
        value.is_absolute() or windows_path.is_absolute() or windows_path.drive or windows_path.root
        or not text or text == "." or ":" in text
        or any(part in {".", ".."} for part in (*value.parts, *windows_path.parts))
    ):
        raise OfflineBindingError("config-file selection must be relative without traversal")
    return value


@dataclass(frozen=True, slots=True)
class PreparedOfflineBinding:
    manifest: BindingManifestV1
    request: VisionUnderstandingRequestV2
    runtime_config: QwenVisionRuntimeConfig = field(repr=False)
    content_policy: ObservableContentPolicyV1 = field(repr=False)
    prompt: str = field(repr=False)
    approved_env_file: Path = field(repr=False)
    _loader_checked: bool = field(default=False, init=False, repr=False, compare=False)
    _claimed: bool = field(default=False, init=False, repr=False, compare=False)
    _claim_lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False, compare=False
    )

    def claim(self) -> None:
        with self._claim_lock:
            if self._claimed:
                raise OfflineBindingError("a prepared offline invocation cannot be reused")
            object.__setattr__(self, "_claimed", True)


def _verify_prepared_inputs(prepared: PreparedOfflineBinding) -> None:
    if prepared._loader_checked is not True:
        raise OfflineBindingError("the explicit offline caller must prepare this invocation")
    manifest = _validated(prepared.manifest, BindingManifestV1)
    request = _validated(prepared.request, VisionUnderstandingRequestV2)
    inputs = manifest.inputs
    if not isinstance(prepared.prompt, str) or not prepared.prompt:
        raise OfflineBindingError("an explicit nonempty prompt is required")
    if sha256(prepared.prompt.encode("utf-8")).hexdigest() != inputs.prompt_sha256:
        raise OfflineBindingError("prompt identity mismatch")
    if (
        type(prepared.content_policy) is not LexicalRegressionContentPolicy
        or prepared.content_policy._lexicon != synthetic_prohibited_lexicon()
        or getattr(prepared.content_policy, "content_policy_version", None)
        != inputs.content_policy_version
        or getattr(prepared.content_policy, "policy_match_view_version", None)
        != inputs.policy_match_view_version
        or not callable(getattr(prepared.content_policy, "evaluate", None))
    ):
        raise OfflineBindingError("policy identity mismatch")
    if (
        request.correlation_id != inputs.correlation_id
        or request.source_image_ref.sha256 != inputs.source_sha256
    ):
        raise OfflineBindingError("request correlation or source image identity mismatch")
    validation = request.media_validation
    if validation is None or (
        validation.decision != "PASS"
        or validation.validation_artifact_ref != inputs.validation_artifact_ref
        or validation.validation_artifact_sha256 != inputs.validation_artifact_sha256
        or validation.validator_policy_version != inputs.validator_policy_version
    ):
        raise OfflineBindingError("request validation provenance mismatch")
    catalog = vision_profile_catalog_v2()
    profile = catalog.resolve(request.requested_profile_id)
    if (
        request.requested_profile_id.value != inputs.profile_id
        or profile.adapter_version != inputs.adapter_version
        or profile.model_provenance.model_identifier != inputs.model_identifier
        or profile.model_provenance.model_revision != inputs.model_revision
        or vision_profile_config_hash_v2(profile) != inputs.profile_config_hash
        or vision_profile_catalog_hash_v2(catalog) != inputs.profile_catalog_hash
    ):
        raise OfflineBindingError("profile identity mismatch")
    if runtime_config_sha256(prepared.runtime_config) != inputs.runtime_config_identity_sha256:
        raise OfflineBindingError("typed runtime config identity mismatch")
    _selected_relative_env_file(prepared.approved_env_file)


def prepare_offline_binding(
    *,
    manifest: BindingManifestV1,
    request: VisionUnderstandingRequestV2,
    content_policy: ObservableContentPolicyV1,
    prompt: str,
    approved_env_file: Path,
    expected_runtime_config: QwenVisionRuntimeConfig,
    runtime_config_loader: RuntimeConfigLoader,
) -> PreparedOfflineBinding:
    """Prepare one synthetic invocation with an explicit isolated loader boundary.

    A fixture may inject ``QwenVisionRuntimeConfig.from_env_file`` behind a mock. This
    module never selects an env file, reads it directly or loads a model.
    """
    checked_manifest = _validated(manifest, BindingManifestV1)
    checked_request = _validated(request, VisionUnderstandingRequestV2)
    selected_file = _selected_relative_env_file(approved_env_file)
    if not callable(runtime_config_loader):
        raise OfflineBindingError("an explicit fixture runtime-config loader is required")
    expected_digest = runtime_config_sha256(expected_runtime_config)
    if expected_digest != checked_manifest.inputs.runtime_config_identity_sha256:
        raise OfflineBindingError("expected typed runtime config identity mismatch")
    loaded = runtime_config_loader(selected_file, environ={})
    if type(loaded) is not QwenVisionRuntimeConfig or loaded != expected_runtime_config:
        raise OfflineBindingError("loaded runtime config differs from the selected typed config")
    prepared = PreparedOfflineBinding(
        manifest=checked_manifest, request=checked_request, runtime_config=loaded,
        content_policy=content_policy, prompt=prompt, approved_env_file=selected_file,
    )
    # This records only the offline loader sequence, never a live authorization grant.
    object.__setattr__(prepared, "_loader_checked", True)
    _verify_prepared_inputs(prepared)
    return prepared


@dataclass(slots=True)
class OfflineBindingPreflight:
    prepared: PreparedOfflineBinding
    produce_facts: Callable[[str], BindingPreflightFactsV1]
    inventory: Feat018ArtifactInventory
    writer: Feat018EvidenceCommitWriter
    incident: Feat018IncidentWriter
    run_id: str
    _attempted: bool = field(default=False, init=False, repr=False)
    _accepted_facts: BindingPreflightFactsV1 | None = field(default=None, init=False, repr=False)

    @property
    def accepted_facts(self) -> BindingPreflightFactsV1:
        if self._accepted_facts is None:
            raise OfflineBindingError("offline preflight facts have not been accepted")
        return _validated(self._accepted_facts, BindingPreflightFactsV1)

    @property
    def has_accepted_facts(self) -> bool:
        return self._accepted_facts is not None

    def verify(self, *, synthetic_session_id: str) -> LightningPreflightFacts:
        if self._attempted:
            raise OfflineBindingError("offline preflight cannot recapture or reuse its baseline")
        self._attempted = True
        _verify_prepared_inputs(self.prepared)
        if (
            self.writer.fs.exists(self.writer.json_path)
            or self.writer.fs.exists(self.writer.markdown_path)
            or not self.incident._destination_is_approved(self.run_id)
        ):
            raise OfflineBindingError("synthetic evidence destinations are not admissible")
        self.inventory.capture()
        facts = _validated(self.produce_facts(synthetic_session_id), BindingPreflightFactsV1)
        self.prepared.manifest.verify_preflight(facts)
        if facts.artifact_inventory_summary != self.inventory.binding_summary():
            raise OfflineBindingError("fixture summary differs from the captured inventory baseline")
        # These are legacy OFFLINE compatibility gates, not actual session readiness,
        # hardware observations or live authorization. Session facts remain separate.
        accepted = LightningPreflightFacts(
            synthetic_session_id=synthetic_session_id,
            approval_identity_verified=True, checkout_identity_verified=True,
            d4_readiness_verified=True, fixture_digest_verified=True,
            prompt_hash_verified=True, hardware_placement_verified=True,
            policy_identity_verified=True, runtime_inventory_verified=True,
        )
        self._accepted_facts = facts
        return accepted


@dataclass(slots=True)
class OfflineBindingFinalizer:
    prepared: PreparedOfflineBinding
    preflight: OfflineBindingPreflight
    produce_metadata: Callable[[Feat018LiveSmokeResult], BindingTerminalMetadataV1]
    cleanup: Callable[[], CleanupStatus]
    writer: Feat018EvidenceCommitWriter
    incident: Feat018IncidentWriter
    run_id: str
    evidence_id: str
    _attempted: bool = field(default=False, init=False, repr=False)
    _finalization: SmokeFinalizationResult | None = field(default=None, init=False, repr=False)
    _cleanup_status: CleanupStatus | None = field(default=None, init=False, repr=False)
    _cleanup_errors: tuple[Exception, ...] = field(default=(), init=False, repr=False)

    @property
    def finalization(self) -> SmokeFinalizationResult | None:
        return self._finalization

    @property
    def cleanup_status(self) -> CleanupStatus | None:
        return self._cleanup_status

    @property
    def cleanup_errors(self) -> tuple[Exception, ...]:
        """Retain actual callback exceptions and their resource ownership privately."""
        return self._cleanup_errors

    def _cleanup_once(self) -> CleanupStatus:
        if self._cleanup_status is None:
            # Mark the attempt before invoking the callback, including reentrant failure.
            # The supplied callback owns its existing absolute deadline; this wrapper
            # does not create a second window, extend it or retry cleanup.
            self._cleanup_status = CleanupStatus.CLEANUP_FAILED
            try:
                status = self.cleanup()
            except Exception as error:  # noqa: BLE001 - keep ownership, publish no exception
                self._cleanup_errors = (*self._cleanup_errors, error)
            else:
                if status is CleanupStatus.SUCCEEDED:
                    self._cleanup_status = CleanupStatus.SUCCEEDED
        return self._cleanup_status

    def _failure_public_identities_are_safe(self, result: Feat018LiveSmokeResult) -> bool:
        try:
            if self.preflight.run_id != self.run_id or not all(
                _is_bounded_opaque_identifier(identifier)
                for identifier in (self.run_id, self.evidence_id)
            ):
                return False
            paths = (
                self.writer.json_path,
                self.writer.markdown_path,
                self.incident.path,
                self.incident.repository_root,
            )
            _validate_terminal_publication_privacy(
                result,
                (
                    self.run_id,
                    self.preflight.run_id,
                    self.evidence_id,
                    *(str(path) for path in paths if path is not None),
                ),
            )
        except Exception:  # noqa: BLE001 - unsafe identities must fail without publication
            return False
        return True

    def finalize(self, *, result: Feat018LiveSmokeResult) -> LightningFinalizationFacts:
        if self._attempted:
            raise OfflineBindingError("offline finalization cannot be repeated")
        # A pre-authorization rejection owns no runtime finalization or incident path.
        if (
            not self.preflight.has_accepted_facts
            or type(result) is not Feat018LiveSmokeResult or not result.preflight_verified
        ):
            raise OfflineBindingError("a post-preflight typed terminal result is required")
        self._attempted = True
        if not self._failure_public_identities_are_safe(result):
            # This path has already crossed authorization, so preserve the one cleanup
            # attempt and any unresolved ownership, but never construct an unsafe record.
            self._cleanup_once()
            return LightningFinalizationFacts(
                finalization_verified=False,
                evidence_pair_verified=False,
                incident_handling_verified=False,
            )
        try:
            accepted_preflight = self.preflight.accepted_facts
            if (
                self.preflight.prepared is not self.prepared
                or self.preflight.writer is not self.writer
                or self.preflight.incident is not self.incident
                or self.preflight.run_id != self.run_id
            ):
                raise OfflineBindingError("finalization does not own the preflight baseline")
            _verify_prepared_inputs(self.prepared)
            metadata = _validated(self.produce_metadata(result), BindingTerminalMetadataV1)
            if (
                metadata.manifest != self.prepared.manifest
                or metadata.preflight != accepted_preflight
            ):
                raise OfflineBindingError("terminal metadata differs from accepted binding facts")
            metadata.validate_for_terminal(
                adapter_call_count=result.adapter_call_count, attempt_count=result.attempt_count,
                outcome=result.effective_outcome.value,
                failure_code=result.failure_code.value if result.failure_code else None,
                session_ready=result.session_ready,
            )
        except Exception:  # noqa: BLE001 - never serialize producer/config exception details
            # A producer or cleanup callback can mutate publication identity. Recheck on
            # the failure edge, before constructing either public failure record.
            self._cleanup_once()
            if not self._failure_public_identities_are_safe(result):
                return LightningFinalizationFacts(
                    finalization_verified=False,
                    evidence_pair_verified=False,
                    incident_handling_verified=False,
                )
            try:
                incident_approved = self.incident._destination_is_approved(self.run_id)
            except Exception:  # noqa: BLE001 - unverified destinations cannot receive incidents
                incident_approved = False
            if not incident_approved:
                return LightningFinalizationFacts(
                    finalization_verified=False,
                    evidence_pair_verified=False,
                    incident_handling_verified=False,
                )
            evidence = EvidenceCommitResult(
                committed=False, run_id=self.run_id, evidence_id=self.evidence_id,
                failure_reason="offline binding metadata verification failed",
            )
            # A malformed metadata producer cannot make evidence publication possible or
            # release any resource still owned by the cleanup callback.
            self._finalization = SmokeFinalizationResult(
                evidence=evidence, incident_written=self.incident.write(evidence)
            )
        else:
            self._finalization = finalize_smoke_run(
                result, run_id=self.run_id, evidence_id=self.evidence_id,
                inventory=self.preflight.inventory, cleanup=self._cleanup_once,
                writer=self.writer, incident=self.incident, binding_metadata=metadata,
            )
        finalization = self._finalization
        return LightningFinalizationFacts(
            finalization_verified=finalization.evidence.committed,
            evidence_pair_verified=finalization.evidence.committed,
            incident_handling_verified=(finalization.evidence.committed or finalization.incident_written),
        )


def _verify_fixture_configs(
    prepared: PreparedOfflineBinding, config: Feat018LiveSmokeConfig, d11_config: D11OfflineConfig
) -> None:
    if type(config) is not Feat018LiveSmokeConfig or type(d11_config) is not D11OfflineConfig:
        raise OfflineBindingError("explicit typed finite fixture parameters are required")
    budgets = prepared.manifest.budgets
    runner = config.bounded_runner_config
    compared = (
        (runner.per_attempt_timeout_seconds, budgets.per_attempt_timeout_seconds),
        (runner.total_adapter_cap_seconds, budgets.total_adapter_cap_seconds),
        (runner.cleanup_deadline_seconds, budgets.cleanup_timeout_seconds),
        (config.session_provision_timeout_seconds, budgets.session_provision_timeout_seconds),
        (config.session_ttl_seconds, budgets.session_ttl_seconds),
        (config.gpu_minute_cap, budgets.gpu_minute_cap),
        (config.session_termination_deadline_seconds, budgets.session_termination_deadline_seconds),
        (d11_config.cleanup_total_seconds, budgets.cleanup_timeout_seconds),
        (d11_config.grant_max_age_seconds, budgets.grant_max_age_seconds),
    )
    for actual, expected in compared:
        if type(actual) not in (int, float) or not math.isfinite(actual) or actual != expected:
            raise OfflineBindingError("fixture budget differs from its explicit binding")
    for actual in (
        runner.containment_setup_timeout_seconds, runner.posix_confirmation_timeout_seconds,
        runner.posix_confirmation_retry_interval_seconds, runner.poll_interval_seconds,
        d11_config.poll_interval_seconds,
    ):
        if type(actual) not in (int, float) or not math.isfinite(actual) or actual <= 0:
            raise OfflineBindingError("finite positive fixture phase parameters are required")
    ceilings = prepared.manifest.ceilings
    for actual, expected in (
        (runner.raw_output_max_bytes, ceilings.raw_output_bytes),
        (runner.ipc_envelope_max_bytes, ceilings.ipc_result_bytes),
        (runner.stdout_max_bytes, ceilings.stdout_bytes),
        (runner.stderr_max_bytes, ceilings.stderr_bytes),
    ):
        if type(actual) is not int or actual != expected:
            raise OfflineBindingError("fixture byte ceiling differs from its explicit binding")


def run_offline_binding(
    prepared: PreparedOfflineBinding,
    *,
    preflight: OfflineBindingPreflight,
    finalizer: OfflineBindingFinalizer,
    controller: LightningSessionControllerV1,
    adapter_dispatch: LightningAdapterDispatchV1,
    observer: LightningResourceObserverV1,
    config: Feat018LiveSmokeConfig,
    d11_config: D11OfflineConfig,
    session_id: str,
    clock: Callable[[], float] = time.monotonic,
    coordinator: Callable[..., Feat018LiveSmokeResult] = run_offline_live_smoke,
) -> Feat018LiveSmokeResult:
    """Consume one prepared fixture and delegate to the existing offline coordinator.

    ``coordinator`` is the test injection seam for bounded synthetic fixtures. It has the
    existing coordinator contract, including error containment and terminal finalization.
    This wrapper does not implement an additional worker/runner or any live integration.
    """
    rejected = Feat018LiveSmokeResult(
        effective_outcome=EffectiveOutcome.FAILED, adapter_call_count=0, attempt_count=None,
        cleanup_status=CleanupStatus.SUCCEEDED,
        failure_code=Feat018LiveSmokeFailureCode.NOT_AUTHORIZED,
    )
    try:
        if type(prepared) is not PreparedOfflineBinding:
            return rejected
        prepared.claim()
        if (
            type(preflight) is not OfflineBindingPreflight
            or type(finalizer) is not OfflineBindingFinalizer
            or preflight.prepared is not prepared or finalizer.prepared is not prepared
            or finalizer.preflight is not preflight or not callable(coordinator)
        ):
            return rejected
        # Publication identity is fixed before authorization: an unusable evidence id or
        # split writer/incident/run ownership could otherwise leave no pair or incident.
        if (
            not _is_bounded_opaque_identifier(finalizer.evidence_id)
            or not _is_bounded_opaque_identifier(preflight.run_id)
            or finalizer.run_id != preflight.run_id
            or finalizer.writer is not preflight.writer
            or finalizer.incident is not preflight.incident
        ):
            return rejected
        _verify_prepared_inputs(prepared)
        _verify_fixture_configs(prepared, config, d11_config)
    except Exception:  # noqa: BLE001 - pre-authorization rejection has no evidence/finalizer
        return rejected
    result = coordinator(
        prepared.request, prepared.runtime_config, prepared.content_policy, prepared.prompt,
        controller=controller, config=config, session_id=session_id, preflight=preflight,
        finalizer=finalizer, adapter_dispatch=adapter_dispatch, observer=observer,
        d11_config=d11_config, clock=clock,
    )
    if finalizer.cleanup_status is CleanupStatus.CLEANUP_FAILED:
        owned_failures = tuple(error for error in finalizer.cleanup_errors
                               if isinstance(error, Feat018CleanupFailedError))
        retained = list(result.cleanup_failures)
        for error in owned_failures:
            if not any(error is existing for existing in retained):
                retained.append(error)
        return replace(
            result, effective_outcome=EffectiveOutcome.CLEANUP_FAILED,
            cleanup_status=CleanupStatus.CLEANUP_FAILED,
            failure_code=Feat018LiveSmokeFailureCode.LIFECYCLE_CLEANUP_FAILED,
            cleanup_failures=tuple(retained), finalization_verified=False,
        )
    return result
