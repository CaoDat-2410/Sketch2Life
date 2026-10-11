"""Bounded synthetic checks for the offline D1/D11 binding foundation.

All identities, inventories and observations below are fixture data. These tests never
read an env file, contact a provider, load a model or execute a GPU workload.
"""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import ConfigDict, TypeAdapter, ValidationError, field_serializer, model_validator
from pydantic_core import PydanticCustomError

from sketch2life.benchmark import feat018_live_lightning_binding as binding
from sketch2life.benchmark import feat018_live_lightning_execution as execution
from sketch2life.contracts.schemas import feat018_live_binding as contract
from sketch2life.contracts.schemas.vision import (
    VisionImageReferenceV1,
    VisionMediaValidationProvenanceV1,
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


_PROMPT = "synthetic offline binding prompt"
_SOURCE_HASH = "c" * 64
_PROFILE = vision_profile_catalog_v2().profiles[0]
_ASSERTION_NAMES = (
    "nested_spawn", "outer_worker_non_daemon", "containment_before_child_spawn",
    "all_descendants_contained", "no_orphan_after_kill", "both_process_levels_absent",
    "containment_absent", "late_progress_rejected", "attempt_deadline_120_seconds",
    "total_cap_not_reset", "timeout_not_retried", "attempt_count_from_accepted_progress",
    "cleanup_finally_executed", "authoritative_monotonic_control",
    "asr_whisper_not_executed", "no_gate_decision_fabricated",
    "correlation_and_provenance_match", "exact_two_file_inventory",
)


def _runtime_config() -> QwenVisionRuntimeConfig:
    return QwenVisionRuntimeConfig(model_dir=Path("synthetic-private-model"))


def _policy() -> LexicalRegressionContentPolicy:
    return LexicalRegressionContentPolicy(synthetic_prohibited_lexicon())


def _inventory(environment: str) -> contract.RuntimeEnvironmentInventoryV1:
    packages = (("av", "18.1.0"), ("pydantic", "2.11.0")) if environment == "HOST" else (
        ("accelerate", "1.10.1"), ("pydantic", "2.11.0"),
        ("qwen-vl-utils", "0.0.14"), ("torch", "2.8.0"), ("transformers", "4.57.6"),
    )
    return contract.RuntimeEnvironmentInventoryV1(
        environment=environment,
        interpreter=contract.InterpreterIdentityV1(
            implementation="CPython", full_version="3.12.1",
            build_identity="synthetic-build", abi_identity="synthetic-abi",
        ),
        distributions=tuple(contract.DistributionIdentityV1(package=name, version=version)
                            for name, version in packages),
        internal_modules=(contract.ArtifactIdentityV1(
            relative_path="backend/src/sketch2life/benchmark/feat018_live_lightning_execution.py",
            sha256="d" * 64,
        ),),
    )


def _manifest() -> contract.BindingManifestV1:
    policy = _policy()
    return contract.BindingManifestV1(
        inputs=contract.BindingInputIdentityV1(
            reviewed_runtime_code_commit="9549a341194f40b1a9be419d6fce0d70f1ca0384",
            approval_record_commit="b" * 40,
            correlation_id="synthetic-binding-correlation",
            fixture_id="synthetic-fixture", source_sha256=_SOURCE_HASH,
            validation_artifact_ref="fixture:binding:validation",
            validation_artifact_sha256="e" * 64,
            validator_identity="synthetic-validator", validator_policy_version="synthetic-policy-v1",
            model_identifier=_PROFILE.model_provenance.model_identifier,
            model_revision=_PROFILE.model_provenance.model_revision,
            profile_id=_PROFILE.profile_id.value,
            adapter_version=_PROFILE.adapter_version,
            profile_config_hash=vision_profile_config_hash_v2(_PROFILE),
            profile_catalog_hash=vision_profile_catalog_hash_v2(vision_profile_catalog_v2()),
            runtime_config_identity_sha256=binding.runtime_config_sha256(_runtime_config()),
            prompt_protocol_id="synthetic-prompt-v1", prompt_source_identity="synthetic-source",
            prompt_sha256=sha256(_PROMPT.encode("utf-8")).hexdigest(),
            content_policy_version=policy.content_policy_version,
            policy_match_view_version=policy.policy_match_view_version,
            policy_scope="SYNTHETIC_LEXICAL_REGRESSION_ONLY", d12_result="UNBOUND",
            d4_snapshot_sha256="f" * 64, d4_revision=_PROFILE.model_provenance.model_revision,
            staging_method="SYNTHETIC_OFFLINE_FIXTURE",
            staged_reference_class="SESSION_RELATIVE_FIXTURE",
        ),
        host_inventory=_inventory("HOST"), session_inventory=_inventory("SESSION"),
        budgets=contract.BindingBudgetLimitsV1(
            per_attempt_timeout_seconds=120.0, total_adapter_cap_seconds=121.0,
            session_provision_timeout_seconds=3.0, session_ttl_seconds=300.0,
            gpu_minute_cap=2.0, cleanup_timeout_seconds=4.0,
            session_termination_deadline_seconds=2.0, grant_max_age_seconds=1.0,
        ),
        ceilings=contract.BindingOutputCeilingsV1(
            raw_output_bytes=1024, ipc_result_bytes=2048,
            stdout_bytes=execution.D9_STDOUT_MAX_BYTES, stderr_bytes=execution.D9_STDERR_MAX_BYTES,
        ),
    )


def _request() -> VisionUnderstandingRequestV2:
    return VisionUnderstandingRequestV2(
        correlation_id="synthetic-binding-correlation",
        source_image_ref=VisionImageReferenceV1(
            artifact_ref="fixture:binding:source.png", sha256=_SOURCE_HASH,
        ),
        requested_profile_id=_PROFILE.profile_id,
        media_validation=VisionMediaValidationProvenanceV1(
            validation_artifact_ref="fixture:binding:validation",
            validation_artifact_sha256="e" * 64, decision="PASS",
            validator_policy_version="synthetic-policy-v1",
        ),
    )


def _preflight_facts(manifest: contract.BindingManifestV1) -> contract.BindingPreflightFactsV1:
    return contract.BindingPreflightFactsV1(
        inputs=manifest.inputs, admission_outcome="ADMITTED", admission_reason=None,
        media_validation_decision="PASS",
        host_inventory_sha256=manifest.host_inventory.canonical_sha256(),
        host_source_identities=manifest.host_inventory.internal_modules,
        d4_preflight_state="OBSERVED", output_baseline_captured=True,
        evidence_destinations_absent=True, incident_destination_ignored=True,
        observer_ref="synthetic-host-observer",
        artifact_inventory_summary=contract.BindingArtifactInventorySummaryV1(
            baseline_entry_count=1, baseline_file_count=0, baseline_directory_count=1,
            explicit_root_count=1, max_entries=32,
        ),
    )


def _unknown_session() -> contract.BindingSessionFactsV1:
    return contract.BindingSessionFactsV1(
        readiness=contract.BindingReadinessFactsV1(
            state="UNKNOWN", observer_ref=None, status=None, issue_codes=None,
            model_load_performed=None, inference_performed=None,
        ),
        d4=contract.BindingD4FactsV1(
            state="UNKNOWN", observer_ref=None, snapshot_sha256=None, revision=None,
            runtime_config_identity_sha256=None,
        ),
        staging=contract.BindingStagingFactsV1(
            state="UNKNOWN", observer_ref=None, staged_source_sha256=None,
            staging_method=None, staged_reference_class=None, source_mime=None,
            width=None, height=None, image_reference_verified=None,
        ),
        runtime=contract.BindingRuntimeFactsV1(
            state="UNKNOWN", observer_ref=None, manifest=None, runtime_manifest_sha256=None,
            session_inventory_sha256=None, runtime_inputs=None, session_source_identities=None,
            single_device_visible=None,
        ),
        stopped_before="READINESS",
    )


def _observed_session(manifest: contract.BindingManifestV1) -> contract.BindingSessionFactsV1:
    inputs = manifest.inputs
    runtime_manifest = contract.SanitizedRuntimeManifestV1(
        python=contract.ManifestPythonV1(implementation="CPython", version="3.12.1"),
        dependencies=tuple(item for item in manifest.session_inventory.distributions
                           if item.package != "pydantic"),
        cuda=contract.ManifestCudaV1(available=True, device_count=1, runtime_version="12.8"),
        driver=contract.ManifestDriverV1(version="576.1"),
        gpu=contract.ManifestGpuV1(device_index=0, sku="NVIDIA_L4", vram_mib=23034,
                                   bf16_supported=True),
    )
    return contract.BindingSessionFactsV1(
        readiness=contract.BindingReadinessFactsV1(
            state="OBSERVED", observer_ref="fixture-runtime-observer", status="READY",
            issue_codes=(), model_load_performed=False, inference_performed=False,
        ),
        d4=contract.BindingD4FactsV1(
            state="OBSERVED", observer_ref="fixture-runtime-observer",
            snapshot_sha256=inputs.d4_snapshot_sha256, revision=inputs.d4_revision,
            runtime_config_identity_sha256=inputs.runtime_config_identity_sha256,
        ),
        staging=contract.BindingStagingFactsV1(
            state="OBSERVED", observer_ref="fixture-runtime-observer",
            staged_source_sha256=inputs.source_sha256, staging_method=inputs.staging_method,
            staged_reference_class=inputs.staged_reference_class, source_mime="image/png",
            width=16, height=16, image_reference_verified=True,
        ),
        runtime=contract.BindingRuntimeFactsV1(
            state="OBSERVED", observer_ref="fixture-runtime-observer",
            manifest=runtime_manifest, runtime_manifest_sha256=runtime_manifest.canonical_sha256(),
            session_inventory_sha256=manifest.session_inventory.canonical_sha256(),
            runtime_inputs=inputs, session_source_identities=manifest.session_inventory.internal_modules,
            single_device_visible=True,
        ),
        stopped_before=None,
    )


def _metadata(manifest: contract.BindingManifestV1 | None = None,
              preflight: contract.BindingPreflightFactsV1 | None = None,
              *, dispatched: bool = False) -> contract.BindingTerminalMetadataV1:
    manifest = manifest or _manifest()
    return contract.BindingTerminalMetadataV1(
        manifest=manifest, preflight=preflight or _preflight_facts(manifest),
        session=_observed_session(manifest) if dispatched else _unknown_session(),
        assertions=contract.BindingAssertionFactsV1(**{
            name: contract.BindingBooleanObservationV1(state="UNKNOWN", value=None, observer_ref=None)
            for name in _ASSERTION_NAMES
        }),
        result=contract.BindingResultFactsV1(
            v2_state="UNKNOWN", v2_schema_valid=None, v2_status=None, v2_failure_code=None,
            v2_attempt_number=None, raw_state="UNKNOWN", raw_schema_valid=None,
            raw_status=None, raw_failure_code=None, gate_a_required=None, narration_status=None,
            observer_ref=None,
        ),
        consumption=contract.BindingBudgetConsumptionV1(
            state="UNKNOWN", cap_outcome=None, gpu_minutes_consumed=None,
            d9_enforcement="UNCONFIRMED", observer_ref=None,
        ),
    )


def _terminal() -> execution.Feat018LiveSmokeResult:
    provision = execution.LightningProvisionRefV1("synthetic-session", "provision-token")
    operation = execution.LightningOperationRefV1(
        provision, "operation-token", execution.D11OperationKind.PROVISION,
    )
    report = execution.D11CleanupReport(
        deadline_host_monotonic=20.0, generation=1, operations=(operation,),
        unresolved_operations=(),
        observation=execution.D11ResourceObservation(
            provision, "sealed", (("synthetic-session", "terminated"),), (), 11.0,
            "synthetic-independent-probe",
        ),
        verification="VERIFIED_OFFLINE", failure_codes=(),
        dispatch_invocation_accepted=False, generation_progress_known=False,
    )
    return execution.Feat018LiveSmokeResult(
        effective_outcome=execution.EffectiveOutcome.FAILED,
        adapter_call_count=0, attempt_count=None, cleanup_status=execution.CleanupStatus.SUCCEEDED,
        failure_code=execution.Feat018LiveSmokeFailureCode.PROVISION_FAILED,
        preflight_verified=True, d11_report=report,
    )


def _prepared(manifest: contract.BindingManifestV1 | None = None,
              *, loader: Any = None) -> binding.PreparedOfflineBinding:
    return binding.prepare_offline_binding(
        manifest=manifest or _manifest(), request=_request(), content_policy=_policy(), prompt=_PROMPT,
        approved_env_file=Path("synthetic/runtime.env"), expected_runtime_config=_runtime_config(),
        runtime_config_loader=loader or Mock(return_value=_runtime_config()),
    )


def _wrapper_parts(tmp_path: Path, *, facts: Any = None, metadata_producer: Any = None,
                   cleanup: Any = None) -> tuple[Any, Any, Any, Any]:
    prepared = _prepared()
    writer = execution.Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
    incident = execution.Feat018IncidentWriter(
        Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
        repository_root=tmp_path, git_ignored=True,
    )
    preflight = binding.OfflineBindingPreflight(
        prepared=prepared,
        produce_facts=facts or (lambda _session: _preflight_facts(prepared.manifest)),
        inventory=execution.Feat018ArtifactInventory((tmp_path,), max_entries=32),
        writer=writer, incident=incident, run_id="run",
    )
    finalizer = binding.OfflineBindingFinalizer(
        prepared=prepared, preflight=preflight,
        produce_metadata=metadata_producer or (
            lambda _result: _metadata(prepared.manifest, preflight.accepted_facts)
        ),
        cleanup=cleanup or (lambda: execution.CleanupStatus.SUCCEEDED),
        writer=writer, incident=incident, run_id="run", evidence_id="ev",
    )
    return prepared, preflight, finalizer, writer


def _fixture_configs() -> tuple[execution.Feat018LiveSmokeConfig, execution.D11OfflineConfig]:
    runner = execution.Feat018BoundedRunnerConfig(
        total_adapter_cap_seconds=121.0, raw_output_max_bytes=1024,
        ipc_envelope_max_bytes=2048, stdout_max_bytes=execution.D9_STDOUT_MAX_BYTES,
        stderr_max_bytes=execution.D9_STDERR_MAX_BYTES, cleanup_deadline_seconds=4.0,
        containment_setup_timeout_seconds=0.2, posix_confirmation_timeout_seconds=0.2,
        posix_confirmation_retry_interval_seconds=0.01,
        per_attempt_timeout_seconds=120.0, poll_interval_seconds=0.01,
    )
    return execution.Feat018LiveSmokeConfig(
        bounded_runner_config=runner, session_provision_timeout_seconds=3,
        session_ttl_seconds=300, gpu_minute_cap=2, session_termination_deadline_seconds=2,
        placement_approval=execution.LightningPlacementApproval(
            gpu_sku="NVIDIA_L4", device_index=0, device_count=1, minimum_vram_mib=23000,
            cuda_required=True, bf16_required=True, single_device_required=True,
        ),
    ), execution.D11OfflineConfig(4.0, 1.0, 0.01, "synthetic-independent-probe")


class TestStrictBindingCarriers:
    def test_roundtrip_is_immutable_and_explicitly_offline(self) -> None:
        manifest = _manifest()
        restored = contract.BindingManifestV1.model_validate_json(manifest.model_dump_json())
        assert restored == manifest
        assert restored.canonical_sha256() == manifest.canonical_sha256()
        assert manifest.host_inventory.canonical_sha256() != manifest.session_inventory.canonical_sha256()
        assert manifest.live_authorized is False and manifest.live_seam_state == "UNBOUND"
        assert manifest.budgets.budget_scope == "OFFLINE_FIXTURE_ONLY"
        with pytest.raises(ValidationError):
            manifest.live_authorized = True

    @pytest.mark.parametrize("value", [True, "3", float("inf"), float("nan"), 0.0, -1.0, 86401.0])
    def test_budgets_reject_invalid_or_unbounded_fixture_values(self, value: object) -> None:
        data = _manifest().budgets.model_dump(mode="python")
        data["total_adapter_cap_seconds"] = value
        with pytest.raises(ValidationError):
            contract.BindingBudgetLimitsV1(**data)

    @pytest.mark.parametrize("value", [119.0, 121.0, 120, True, "120.0"])
    def test_attempt_budget_is_exact_120_float(self, value: object) -> None:
        data = _manifest().budgets.model_dump(mode="python")
        data["per_attempt_timeout_seconds"] = value
        with pytest.raises(ValidationError):
            contract.BindingBudgetLimitsV1(**data)

    @pytest.mark.parametrize("field,value", [
        ("live_authorized", True), ("live_authorized", 0),
        ("proof_scope", "LIVE"), ("live_seam_state", "BOUND"),
        ("provider_url", "https://invalid.example"),
    ])
    def test_labels_and_extra_fields_cannot_authorize_live(self, field: str, value: object) -> None:
        data = _manifest().model_dump(mode="python")
        data[field] = value
        with pytest.raises(ValidationError):
            contract.BindingManifestV1(**data)

    @pytest.mark.parametrize("path", [
        "../secret.py", "D:/private.py", "backend/src/sketch2life/../secret.py",
        "backend/tests/unit/test_other.py",
    ])
    def test_inventory_rejects_paths_outside_source_closure(self, path: str) -> None:
        data = _inventory("HOST").model_dump(mode="python")
        data["internal_modules"] = ({"relative_path": path, "sha256": "a" * 64},)
        with pytest.raises(ValidationError):
            contract.RuntimeEnvironmentInventoryV1(**data)

    def test_inventory_requires_sorted_unique_exact_distributions(self) -> None:
        inventory = _inventory("HOST")
        for entries in (tuple(reversed(inventory.distributions)), inventory.distributions * 2):
            with pytest.raises(ValidationError):
                contract.RuntimeEnvironmentInventoryV1(
                    **{**inventory.model_dump(mode="python"), "distributions": entries}
                )
        for version in (">=2.11", "2.11 secret", "https://invalid.example"):
            with pytest.raises(ValidationError):
                contract.DistributionIdentityV1(package="pydantic", version=version)

    @pytest.mark.parametrize("field,value", [
        ("admission_outcome", "UNKNOWN"), ("media_validation_decision", "UNKNOWN"),
        ("d4_preflight_state", "UNKNOWN"), ("output_baseline_captured", False),
        ("evidence_destinations_absent", False), ("incident_destination_ignored", False),
        ("host_inventory_sha256", "a" * 64),
    ])
    def test_missing_or_mismatched_preflight_facts_fail_closed(self, field: str, value: object) -> None:
        manifest = _manifest()
        facts = _preflight_facts(manifest).model_copy(update={field: value})
        with pytest.raises(ValueError):
            manifest.verify_preflight(facts)

    def test_observed_readiness_cannot_load_a_model_or_hide_missing_values(self) -> None:
        for load, inference, observer in ((True, False, "fixture"), (False, True, "fixture"),
                                          (False, False, None)):
            with pytest.raises(ValidationError):
                contract.BindingReadinessFactsV1(
                    state="OBSERVED", observer_ref=observer, status="READY", issue_codes=(),
                    model_load_performed=load, inference_performed=inference,
                )
        with pytest.raises(ValidationError):
            contract.BindingBooleanObservationV1(state="UNKNOWN", value=False, observer_ref=None)

    def test_phase_order_and_runtime_manifest_digest_are_checked(self) -> None:
        metadata = _metadata(dispatched=True)
        with pytest.raises(ValidationError):
            contract.BindingRuntimeFactsV1(
                **{**metadata.session.runtime.model_dump(mode="python"),
                   "runtime_manifest_sha256": "a" * 64}
            )
        with pytest.raises(ValidationError):
            contract.BindingSessionFactsV1(
                **{**metadata.session.model_dump(mode="python"), "stopped_before": "READINESS"}
            )

    @pytest.mark.parametrize("mode", ["pin", "interpreter", "single_visibility", "postload_index"])
    def test_matching_manifest_digest_does_not_mask_runtime_inventory_or_hardware_drift(self, mode: str) -> None:
        metadata = _metadata(dispatched=True)
        runtime = metadata.session.runtime
        manifest = runtime.manifest
        if mode == "pin":
            pins = tuple(item.model_copy(update={"version": "2.7.0"})
                         if item.package == "torch" else item for item in manifest.dependencies)
            manifest = manifest.model_copy(update={"dependencies": pins})
        elif mode == "interpreter":
            manifest = manifest.model_copy(update={"python": manifest.python.model_copy(
                update={"version": "3.12.2"}
            )})
        if mode in ("pin", "interpreter"):
            runtime = runtime.model_copy(update={
                "manifest": manifest, "runtime_manifest_sha256": manifest.canonical_sha256(),
            })
        elif mode == "single_visibility":
            runtime = runtime.model_copy(update={"single_device_visible": False})
        else:
            runtime = runtime.model_copy(update={
                "post_load_model_device_index": 1, "post_load_input_device_index": 1,
            })
        drifted = metadata.model_copy(update={"session": metadata.session.model_copy(update={"runtime": runtime})})
        with pytest.raises(ValidationError):
            drifted.revalidated()

    def test_retained_coverage_is_explicit_and_not_a_verification_claim(self) -> None:
        expected = {
            "commit_identity", "source_and_fixture_identity", "admission", "validation_provenance",
            "readiness_no_preload", "d4_runtime_revalidation", "staging_and_reference", "runtime_manifest",
            "environment_closure", "model_profile_prompt_policy", "hardware_and_placement", "d9_output_ceilings",
            "cardinality", "run_failure_code", "typed_v2_raw_terminal", "nested_spawn_and_non_daemon",
            "containment_and_descendants",
            "no_orphan_two_level_cleanup", "late_progress", "attempt_total_deadlines_retry",
            "session_caps_and_consumption", "correlation_and_provenance", "gate_a_no_fabricated_decisions",
            "no_asr_no_narration", "authorized_transition_and_failure_applicability",
            "cleanup_finally_and_failure", "evidence_pair_incident_postflight",
        }
        rows = contract.RETAINED_REQUIREMENT_COVERAGE
        assert {row.requirement for row in rows} == expected
        assert len(rows) == len(expected)
        assert all(row.producer and row.carrier and row.serializer and row.verifier for row in rows)
        assert _metadata().assertions.attempt_deadline_120_seconds.state == "UNKNOWN"


class TestOfflinePreparation:
    def test_selected_env_loader_is_mocked_and_receives_empty_environ(self, monkeypatch: pytest.MonkeyPatch) -> None:
        loader = Mock(return_value=_runtime_config())
        monkeypatch.setattr(QwenVisionRuntimeConfig, "from_env_file", loader)
        prepared = _prepared(loader=QwenVisionRuntimeConfig.from_env_file)
        loader.assert_called_once_with(Path("synthetic/runtime.env"), environ={})
        assert prepared.runtime_config == _runtime_config()
        assert _PROMPT not in repr(prepared)
        assert "synthetic-private-model" not in repr(prepared)

    @pytest.mark.parametrize("selection", [
        Path("../runtime.env"), Path("/runtime.env"), Path("C:/runtime.env"),
        Path("\\\\host\\runtime.env"), Path("."),
    ])
    def test_unsafe_env_selection_is_rejected_before_loader(self, selection: Path) -> None:
        loader = Mock(return_value=_runtime_config())
        with pytest.raises(binding.OfflineBindingError):
            binding.prepare_offline_binding(
                manifest=_manifest(), request=_request(), content_policy=_policy(), prompt=_PROMPT,
                approved_env_file=selection, expected_runtime_config=_runtime_config(),
                runtime_config_loader=loader,
            )
        loader.assert_not_called()

    @pytest.mark.parametrize("change", ["prompt", "policy", "request", "loaded_config", "expected_config"])
    def test_actual_prepared_inputs_must_match_identity_not_just_labels(self, change: str) -> None:
        values: dict[str, Any] = dict(
            manifest=_manifest(), request=_request(), content_policy=_policy(), prompt=_PROMPT,
            approved_env_file=Path("synthetic/runtime.env"), expected_runtime_config=_runtime_config(),
            runtime_config_loader=Mock(return_value=_runtime_config()),
        )
        if change == "prompt":
            values["prompt"] = _PROMPT + " changed"
        elif change == "policy":
            values["content_policy"] = object()
        elif change == "request":
            values["request"] = _request().model_copy(update={
                "source_image_ref": VisionImageReferenceV1(artifact_ref="fixture:other", sha256="a" * 64)
            })
        elif change == "loaded_config":
            values["runtime_config_loader"] = Mock(return_value=replace(_runtime_config(), device_index=1))
        else:
            values["expected_runtime_config"] = replace(_runtime_config(), allow_model_download=True)
        with pytest.raises(binding.OfflineBindingError):
            binding.prepare_offline_binding(**values)

    def test_policy_version_labels_cannot_substitute_for_canonical_fixture_policy(self) -> None:
        canonical = _policy()
        class SpoofPolicy:
            content_policy_version = canonical.content_policy_version
            policy_match_view_version = canonical.policy_match_view_version
            def evaluate(self, _texts: object) -> None:
                return None
        with pytest.raises(binding.OfflineBindingError):
            binding.prepare_offline_binding(
                manifest=_manifest(), request=_request(), content_policy=SpoofPolicy(), prompt=_PROMPT,
                approved_env_file=Path("synthetic/runtime.env"), expected_runtime_config=_runtime_config(),
                runtime_config_loader=Mock(return_value=_runtime_config()),
            )


class TestOfflinePreflightAndCaller:
    def test_baseline_precedes_facts_and_runtime_and_cannot_be_recaptured(self, tmp_path: Path) -> None:
        events: list[str] = []
        prepared, preflight, _, _ = _wrapper_parts(tmp_path)
        class RecordingInventory(execution.Feat018ArtifactInventory):
            def capture(self) -> None:
                events.append("baseline")
                super().capture()
        preflight.inventory = RecordingInventory((tmp_path,), max_entries=32)
        preflight.produce_facts = lambda _session: (
            events.append("facts") or _preflight_facts(prepared.manifest)
        )
        facts = preflight.verify(synthetic_session_id="synthetic-session")
        events.append("runtime")
        assert events == ["baseline", "facts", "runtime"]
        assert facts.synthetic_session_id == "synthetic-session"
        assert preflight.accepted_facts.proof_scope == "OFFLINE_SYNTHETIC"
        with pytest.raises(binding.OfflineBindingError):
            preflight.verify(synthetic_session_id="synthetic-session")
        assert events == ["baseline", "facts", "runtime"]

    @pytest.mark.parametrize("mode", ["unknown", "existing_pair", "incident_unapproved", "summary_mismatch"])
    def test_preflight_rejection_has_no_finalizer_or_evidence(self, tmp_path: Path, mode: str) -> None:
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path)
        producer = Mock(return_value=_metadata(prepared.manifest))
        finalizer.produce_metadata = producer
        if mode == "unknown":
            preflight.produce_facts = lambda _session: _preflight_facts(prepared.manifest).model_copy(
                update={"admission_outcome": "UNKNOWN"}
            )
        elif mode == "existing_pair":
            writer.json_path.write_bytes(b"synthetic-existing-evidence")
        elif mode == "incident_unapproved":
            preflight.incident.git_ignored = False
        else:
            producer_facts = _preflight_facts(prepared.manifest)
            summary = producer_facts.artifact_inventory_summary.model_copy(update={
                "baseline_entry_count": 2, "baseline_file_count": 1,
            })
            preflight.produce_facts = lambda _session: producer_facts.model_copy(
                update={"artifact_inventory_summary": summary}
            )
        config, d11 = _fixture_configs()
        def coordinator(*args: object, **kwargs: Any) -> execution.Feat018LiveSmokeResult:
            try:
                kwargs["preflight"].verify(synthetic_session_id=kwargs["session_id"])
            except ValueError:
                return execution.Feat018LiveSmokeResult(
                    effective_outcome=execution.EffectiveOutcome.FAILED, adapter_call_count=0,
                    attempt_count=None, cleanup_status=execution.CleanupStatus.SUCCEEDED,
                    failure_code=execution.Feat018LiveSmokeFailureCode.PREFLIGHT_FAILED,
                )
            pytest.fail("preflight unexpectedly accepted")
        result = binding.run_offline_binding(
            prepared, preflight=preflight, finalizer=finalizer,
            controller=object(), adapter_dispatch=object(), observer=object(),
            config=config, d11_config=d11, session_id="synthetic-session", clock=lambda: 0.0,
            coordinator=coordinator,
        )
        assert result.adapter_call_count == 0 and result.attempt_count is None
        assert finalizer.finalization is None
        producer.assert_not_called()
        assert not writer.markdown_path.exists()
        assert not preflight.incident.path.exists()
        if mode == "existing_pair":
            assert writer.json_path.read_bytes() == b"synthetic-existing-evidence"
        else:
            assert not writer.json_path.exists()

    def test_inventory_summary_uses_actual_captured_synthetic_counts(self, tmp_path: Path) -> None:
        (tmp_path / "synthetic-input.bin").write_bytes(b"synthetic-original")
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path)
        def producer(_session: str) -> contract.BindingPreflightFactsV1:
            actual_summary = preflight.inventory.binding_summary()
            return _preflight_facts(prepared.manifest).model_copy(update={
                "artifact_inventory_summary": actual_summary,
            }).revalidated()
        preflight.produce_facts = producer
        preflight.verify(synthetic_session_id="synthetic-session")
        summary = preflight.accepted_facts.artifact_inventory_summary
        assert summary.baseline_entry_count == 2
        assert summary.baseline_file_count == 1 and summary.baseline_directory_count == 1
        assert summary.explicit_root_count == 1 and summary.max_entries == 32
        assert summary.expected_evidence_file_count == 2
        finalizer.finalize(result=_terminal())
        assert finalizer.finalization.evidence.committed
        published = json.loads(writer.json_path.read_bytes())["artifact_inventory_summary"]
        assert published == summary.model_dump(mode="json")
        assert published["phase"] == "CAPTURED_PREFLIGHT_BASELINE"
        assert "observed_evidence_file_count" not in published

    def test_changed_budget_is_rejected_before_dispatch_and_reuse_is_blocked(self, tmp_path: Path) -> None:
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path)
        config, d11 = _fixture_configs()
        config = replace(config, bounded_runner_config=replace(config.bounded_runner_config,
                                                                total_adapter_cap_seconds=122.0))
        coordinator = Mock()
        for _ in range(2):
            result = binding.run_offline_binding(
                prepared, preflight=preflight, finalizer=finalizer,
                controller=object(), adapter_dispatch=object(), observer=object(),
                config=config, d11_config=d11, session_id="synthetic-session",
                clock=lambda: 0.0, coordinator=coordinator,
            )
            assert result.failure_code is execution.Feat018LiveSmokeFailureCode.NOT_AUTHORIZED
            assert result.adapter_call_count == 0 and result.attempt_count is None
        coordinator.assert_not_called()
        assert finalizer.finalization is None
        assert not writer.json_path.exists() and not preflight.incident.path.exists()

    def test_direct_prepared_constructor_cannot_bypass_factory(self, tmp_path: Path) -> None:
        accepted, preflight, finalizer, writer = _wrapper_parts(tmp_path)
        prepared = binding.PreparedOfflineBinding(
            manifest=accepted.manifest, request=accepted.request,
            runtime_config=accepted.runtime_config, content_policy=accepted.content_policy,
            prompt=accepted.prompt, approved_env_file=Path("synthetic/runtime.env"),
        )
        preflight.prepared = prepared
        finalizer.prepared = prepared
        config, d11 = _fixture_configs()
        coordinator = Mock()
        result = binding.run_offline_binding(
            prepared, preflight=preflight, finalizer=finalizer,
            controller=object(), adapter_dispatch=object(), observer=object(),
            config=config, d11_config=d11, session_id="synthetic-session",
            clock=lambda: 0.0, coordinator=coordinator,
        )
        assert result.failure_code is execution.Feat018LiveSmokeFailureCode.NOT_AUTHORIZED
        coordinator.assert_not_called()
        assert finalizer.finalization is None and not writer.json_path.exists()


class TestTerminalMetadataHandoff:
    def test_unknown_progress_stays_unknown_and_cannot_satisfy_success(self) -> None:
        metadata = _metadata(dispatched=True)
        metadata.validate_for_terminal(adapter_call_count=1, attempt_count=None, outcome="FAILED",
                                       failure_code="ADAPTER_FAILED", session_ready=True)
        assert metadata.result.v2_state == "UNKNOWN"
        with pytest.raises(ValueError):
            metadata.validate_for_terminal(adapter_call_count=1, attempt_count=1,
                                           outcome="SUCCEEDED", failure_code=None, session_ready=True)
        with pytest.raises(ValueError):
            _metadata().validate_for_terminal(adapter_call_count=1, attempt_count=None,
                                              outcome="FAILED", failure_code="ADAPTER_FAILED")

    def test_full_received_success_carrier_remains_synthetic_not_live_authorization(self) -> None:
        metadata = _metadata(dispatched=True)
        metadata = metadata.model_copy(update={
            "assertions": contract.BindingAssertionFactsV1(**{
                name: contract.BindingBooleanObservationV1(
                    state="OBSERVED", value=True, observer_ref="fixture-assertion-observer",
                ) for name in _ASSERTION_NAMES
            }),
            "result": contract.BindingResultFactsV1(
                v2_state="OBSERVED", v2_schema_valid=True, v2_status="SUCCEEDED",
                v2_failure_code=None, v2_attempt_number=1,
                raw_state="OBSERVED", raw_schema_valid=True, raw_status="SUCCEEDED",
                raw_failure_code=None, gate_a_required=True, narration_status="NOT_SUPPLIED",
                observer_ref="fixture-result-observer",
            ),
            "consumption": contract.BindingBudgetConsumptionV1(
                state="OBSERVED", cap_outcome="WITHIN_CAP", gpu_minutes_consumed=0.25,
                d9_enforcement="CONFIRMED", observer_ref="fixture-cap-observer",
            ),
        }).revalidated()
        metadata.validate_for_terminal(adapter_call_count=1, attempt_count=1,
                                       outcome="SUCCEEDED", failure_code=None, session_ready=True)
        fields = metadata.evidence_fields()
        assert fields["binding_result_facts"]["v2_status"] == "SUCCEEDED"
        assert fields["binding_consumption"]["gpu_minutes_consumed"] == 0.25
        assert fields["binding_live_authorized"] is False
        assert fields["binding_live_cleanup_proven"] is False
        assert fields["binding_live_seam_state"] == "UNBOUND"

    def test_known_attempt_requires_true_accepted_progress_observation(self) -> None:
        metadata = _metadata(dispatched=True)
        assertion = contract.BindingBooleanObservationV1(
            state="OBSERVED", value=False, observer_ref="synthetic-progress-observer",
        )
        metadata = metadata.model_copy(update={"assertions": metadata.assertions.model_copy(
            update={"attempt_count_from_accepted_progress": assertion}
        )})
        with pytest.raises(ValueError):
            metadata.validate_for_terminal(adapter_call_count=1, attempt_count=1, outcome="FAILED",
                                           failure_code="ADAPTER_FAILED", session_ready=True)

    def test_safe_serializer_carries_received_values_and_excludes_private_payloads(self) -> None:
        metadata = _metadata(dispatched=True)
        fields = metadata.evidence_fields()
        assert fields["staged_source_sha256"] == _SOURCE_HASH
        assert fields["source_width"] == 16
        assert fields["prompt_sha256"] == sha256(_PROMPT.encode()).hexdigest()
        assert fields["runtime_manifest_sha256"] == metadata.session.runtime.manifest.canonical_sha256()
        assert fields["binding_live_authorized"] is False
        assert fields["binding_live_cleanup_proven"] is False
        assert fields["binding_live_seam_state"] == "UNBOUND"
        encoded = json.dumps(fields, sort_keys=True)
        for forbidden in (_PROMPT, "synthetic-private-model", "backend/src/", "synthetic-session",
                          "SESSION_ID", "provider_url", "env_file", "wall_clock_ms"):
            assert forbidden not in encoded
        assert "internal_modules" not in encoded and "distributions" not in encoded

    def test_typed_pre_adapter_terminal_commits_failed_metadata_and_json_last(self, tmp_path: Path) -> None:
        events: list[str] = []
        class RecordingFs(execution.RealFilesystemOps):
            def write_new(self, path: Path, content: bytes) -> None:
                events.append("write:" + path.name)
                super().write_new(path, content)
            def rename(self, source: Path, destination: Path) -> None:
                events.append("rename:" + destination.name)
                super().rename(source, destination)
        prepared, preflight, finalizer, writer = _wrapper_parts(
            tmp_path, cleanup=lambda: events.append("cleanup") or execution.CleanupStatus.SUCCEEDED,
        )
        writer.fs = RecordingFs()
        preflight.verify(synthetic_session_id="synthetic-session")
        terminal = _terminal()
        result = finalizer.finalize(result=terminal)
        assert result.evidence_pair_verified and finalizer.finalization.evidence.committed
        assert terminal.adapter_result is None
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["status"] == "FAILED"
        assert payload["adapter_call_count"] == 0 and payload["attempt_count"] is None
        assert payload["generation_progress"] == "UNKNOWN"
        assert payload["readiness_observation_state"] == "UNKNOWN"
        assert "readiness_status" not in payload
        assert payload["source_sha256"] == prepared.manifest.inputs.source_sha256
        assert payload["binding_live_cleanup_proven"] is False
        assert payload["cleanup_verification"] == "VERIFIED_OFFLINE"
        assert events[0] == "cleanup" and events[-2:] == ["rename:evidence.md", "rename:evidence.json"]
        markdown = writer.markdown_path.read_text(encoding="utf-8")
        metadata_fields = json.loads(markdown.split("```json\n", 1)[1].split("\n```", 1)[0])
        assert metadata_fields == {
            **_metadata(prepared.manifest, preflight.accepted_facts).evidence_fields(),
            "terminal_kind": "PRE_ADAPTER", "adapter_call_count": 0, "attempt_count": None,
            "run_failure_code": "PROVISION_FAILED", "generation_progress": "UNKNOWN",
            "cleanup_verification": "VERIFIED_OFFLINE", "cleanup_generation": 1,
            "unresolved_operation_count": 0,
        }
        for key, value in metadata_fields.items():
            assert payload[key] == value
        assert execution.read_committed_pair(writer.json_path, writer.markdown_path).verdict is execution.PairVerdict.AUTHORITATIVE


        with pytest.raises(binding.OfflineBindingError):
            finalizer.finalize(result=terminal)

    @pytest.mark.parametrize("mode", ["producer_raises", "different_manifest", "invalid_construct",
                                     "cleanup_failure", "label_only", "mutated_inventory"])
    def test_invalid_handoff_or_unverified_cleanup_uses_incident_and_no_pair(self, tmp_path: Path, mode: str) -> None:
        cleanup_calls: list[str] = []
        cleanup = lambda: cleanup_calls.append("cleanup") or execution.CleanupStatus.SUCCEEDED
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        preflight.verify(synthetic_session_id="synthetic-session")
        terminal = _terminal()
        if mode == "producer_raises":
            def producer(_result: object) -> Any:
                raise RuntimeError("PRIVATE-PRODUCER-DETAIL")
            finalizer.produce_metadata = producer
        elif mode == "different_manifest":
            other = prepared.manifest.model_copy(update={"inputs": prepared.manifest.inputs.model_copy(
                update={"fixture_id": "other-fixture"}
            )})
            finalizer.produce_metadata = lambda _result: _metadata(other)
        elif mode == "invalid_construct":
            invalid = contract.BindingTerminalMetadataV1.model_construct(
                **{**_metadata(prepared.manifest, preflight.accepted_facts).model_dump(mode="python"),
                   "live_cleanup_proven": True}
            )
            finalizer.produce_metadata = lambda _result: invalid
        elif mode == "cleanup_failure":
            finalizer.cleanup = lambda: cleanup_calls.append("cleanup") or execution.CleanupStatus.CLEANUP_FAILED
        elif mode == "label_only":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, observation=None))
        else:
            (tmp_path / "synthetic-runtime-residual").write_bytes(b"synthetic residual")
        facts = finalizer.finalize(result=terminal)
        assert not facts.evidence_pair_verified
        assert cleanup_calls == ["cleanup"]
        assert finalizer.finalization.incident_written
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert "PRIVATE" not in preflight.incident.path.read_text(encoding="utf-8")

    @pytest.mark.parametrize("identity_field", ["run_id", "evidence_id"])
    @pytest.mark.parametrize("form", ["exact", "prefix", "suffix"])
    @pytest.mark.parametrize("private_token", [
        "provision-token", "operation-token", "known-operation-token",
        "known-session-token", "retained-recovery-token",
    ])
    @pytest.mark.parametrize("failure", ["producer_exception", "invalid_metadata"])
    @pytest.mark.parametrize("malformed_proof", [False, True])
    def test_m3_wrapper_rechecks_mutated_failure_identities_before_incident(
        self, tmp_path: Path, identity_field: str, form: str, private_token: str,
        failure: str, malformed_proof: bool,
    ) -> None:
        cleanup = Mock(return_value=execution.CleanupStatus.SUCCEEDED)
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        preflight.verify(synthetic_session_id="synthetic-session")
        identity = {
            "exact": private_token,
            "prefix": "public-" + private_token,
            "suffix": private_token + "-public",
        }[form]
        terminal = _terminal_with_known_cleanup_session()
        if malformed_proof:
            assert terminal.d11_report is not None
            terminal = replace(
                terminal,
                d11_report=replace(terminal.d11_report, observation=None),
            )
        producer_calls: list[str] = []

        def produce_metadata(_result: object) -> object:
            producer_calls.append("metadata")
            if identity_field == "run_id":
                finalizer.run_id = identity
                preflight.run_id = identity
                preflight.incident.path = (
                    tmp_path / "tmp" / f"feat018-live-lightning-incident-{identity}" / "INCIDENT.md"
                )
            else:
                finalizer.evidence_id = identity
            if failure == "producer_exception":
                raise RuntimeError("private producer detail: " + private_token)
            return object()

        finalizer.produce_metadata = produce_metadata
        facts = finalizer.finalize(result=terminal)

        assert producer_calls == ["metadata"]
        cleanup.assert_called_once_with()
        assert facts == execution.LightningFinalizationFacts(False, False, False)
        assert private_token not in repr(facts)
        assert finalizer.finalization is None
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert not preflight.incident.path.exists()
        assert list(tmp_path.rglob("*")) == []

    def test_m3_wrapper_rejects_private_incident_path_before_metadata_production(
        self, tmp_path: Path,
    ) -> None:
        cleanup = Mock(return_value=execution.CleanupStatus.SUCCEEDED)
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        preflight.verify(synthetic_session_id="synthetic-session")
        token = "provision-token"
        preflight.incident.path = (
            tmp_path / "tmp" / f"feat018-live-lightning-incident-public-{token}" / "INCIDENT.md"
        )
        producer = Mock(side_effect=RuntimeError("private producer detail: " + token))
        finalizer.produce_metadata = producer

        facts = finalizer.finalize(result=_terminal_with_known_cleanup_session())

        producer.assert_not_called()
        cleanup.assert_called_once_with()
        assert facts == execution.LightningFinalizationFacts(False, False, False)
        assert token not in repr(facts)
        assert finalizer.finalization is None
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert not preflight.incident.path.exists()
        assert list(tmp_path.rglob("*")) == []

    def test_m3_wrapper_without_approved_incident_destination_returns_unverified_facts(
        self, tmp_path: Path,
    ) -> None:
        cleanup = Mock(return_value=execution.CleanupStatus.SUCCEEDED)
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        preflight.verify(synthetic_session_id="synthetic-session")
        preflight.incident.path = tmp_path / "tmp" / "unapproved" / "INCIDENT.md"
        finalizer.produce_metadata = Mock(side_effect=RuntimeError("safe synthetic failure"))

        facts = finalizer.finalize(result=_terminal())

        cleanup.assert_called_once_with()
        assert facts == execution.LightningFinalizationFacts(False, False, False)
        assert finalizer.finalization is None
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert not preflight.incident.path.exists()
        assert list(tmp_path.rglob("*")) == []

    def test_m3_wrapper_cleanup_failure_retains_owned_resource_without_public_record(
        self, tmp_path: Path,
    ) -> None:
        resource = object()
        failure = execution.Feat018CleanupFailedError(owned_process=resource)
        cleanup = Mock(side_effect=failure)
        _, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        preflight.verify(synthetic_session_id="synthetic-session")
        finalizer.evidence_id = "public-operation-token"
        finalizer.produce_metadata = Mock(side_effect=RuntimeError("private operation-token"))

        facts = finalizer.finalize(result=_terminal_with_known_cleanup_session())

        cleanup.assert_called_once_with()
        assert finalizer.cleanup_status is execution.CleanupStatus.CLEANUP_FAILED
        assert finalizer.cleanup_errors == (failure,)
        assert finalizer.cleanup_errors[0].owned_process is resource
        assert facts == execution.LightningFinalizationFacts(False, False, False)
        assert "operation-token" not in repr(facts)
        assert finalizer.finalization is None
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert not preflight.incident.path.exists()
        assert list(tmp_path.rglob("*")) == []

    def test_m3_wrapper_safe_identity_metadata_failure_keeps_incident_behavior(self, tmp_path: Path) -> None:
        cleanup = Mock(return_value=execution.CleanupStatus.SUCCEEDED)
        _, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        preflight.verify(synthetic_session_id="synthetic-session")
        finalizer.produce_metadata = Mock(
            side_effect=RuntimeError("private provision-token and operation-token details")
        )

        facts = finalizer.finalize(result=_terminal_with_known_cleanup_session())

        cleanup.assert_called_once_with()
        assert not facts.evidence_pair_verified
        assert facts.incident_handling_verified
        assert finalizer.finalization is not None and finalizer.finalization.incident_written
        assert finalizer.finalization.evidence.run_id == "run"
        assert finalizer.finalization.evidence.evidence_id == "ev"
        incident_text = preflight.incident.path.read_text(encoding="utf-8")
        assert "run_id: run" in incident_text and "evidence_id: ev" in incident_text
        for token in (
            "provision-token", "operation-token", "known-operation-token",
            "known-session-token", "retained-recovery-token",
        ):
            assert token not in repr(facts)
            assert token not in repr(finalizer.finalization)
            assert token not in incident_text
            assert token not in str(preflight.incident.path)
        assert not writer.json_path.exists() and not writer.markdown_path.exists()

    @pytest.mark.parametrize("mode", ["missing_terminal", "unchecked_scope", "cardinality_drift", "undeclared_extra"])
    def test_core_finalizer_revalidates_metadata_without_trusting_wrapper(self, tmp_path: Path, mode: str) -> None:
        inventory = execution.Feat018ArtifactInventory((tmp_path,), max_entries=32)
        inventory.capture()
        writer = execution.Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        metadata = _metadata()
        terminal = _terminal()
        if mode == "unchecked_scope":
            metadata = metadata.model_copy(update={"proof_scope": "LIVE"})
        elif mode == "undeclared_extra":
            metadata = metadata.model_copy(update={"provider_url": "https://invalid.example"})
        elif mode == "cardinality_drift":
            terminal = replace(terminal, adapter_call_count=1)
        cleanup = Mock(return_value=execution.CleanupStatus.SUCCEEDED)
        result = execution.Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=execution.EffectiveOutcome.FAILED,
            cleanup=cleanup, postflight=inventory.verify_provisional,
            terminal_result=None if mode == "missing_terminal" else terminal,
            binding_metadata=metadata,
        )
        cleanup.assert_called_once_with()
        assert not result.committed
        assert not writer.json_path.exists() and not writer.markdown_path.exists()

    def test_offline_identities_and_cleanup_label_leave_live_entry_unauthorized(self) -> None:
        prepared = _prepared()
        assert _terminal().d11_report.resources_released
        coordinator = Mock()
        result = execution.run_live_smoke(
            prepared.request, prepared.runtime_config, prepared.content_policy, prepared.prompt,
            controller=coordinator, preflight=coordinator, finalizer=coordinator,
        )
        assert result.failure_code is execution.Feat018LiveSmokeFailureCode.NOT_AUTHORIZED
        assert result.adapter_call_count == 0 and result.attempt_count is None
        coordinator.assert_not_called()

    def test_cleanup_exception_retains_real_owned_resource_through_caller(self, tmp_path: Path) -> None:
        resource = object()
        failure = execution.Feat018CleanupFailedError(owned_process=resource)
        calls: list[str] = []
        def cleanup() -> execution.CleanupStatus:
            calls.append("cleanup")
            raise failure
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        config, d11 = _fixture_configs()
        def coordinator(*_args: object, **kwargs: Any) -> execution.Feat018LiveSmokeResult:
            kwargs["preflight"].verify(synthetic_session_id=kwargs["session_id"])
            terminal = _terminal()
            kwargs["finalizer"].finalize(result=terminal)
            return terminal
        result = binding.run_offline_binding(
            prepared, preflight=preflight, finalizer=finalizer,
            controller=object(), adapter_dispatch=object(), observer=object(),
            config=config, d11_config=d11, session_id="synthetic-session",
            clock=lambda: 0.0, coordinator=coordinator,
        )
        assert calls == ["cleanup"]
        assert finalizer.cleanup_errors == (failure,)
        assert finalizer.cleanup_errors[0].owned_process is resource
        assert result.cleanup_failures == (failure,)
        assert result.cleanup_failures[0] is failure
        assert result.cleanup_status is execution.CleanupStatus.CLEANUP_FAILED
        assert result.effective_outcome is execution.EffectiveOutcome.CLEANUP_FAILED
        assert not result.finalization_verified and not writer.json_path.exists()
        assert finalizer.finalization.incident_written

    def test_direct_preauthorization_finalizer_call_creates_no_incident_or_cleanup(self, tmp_path: Path) -> None:
        cleanup = Mock(return_value=execution.CleanupStatus.SUCCEEDED)
        _, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        with pytest.raises(binding.OfflineBindingError):
            finalizer.finalize(result=_terminal())
        cleanup.assert_not_called()
        assert finalizer.finalization is None
        assert not writer.json_path.exists() and not preflight.incident.path.exists()

    def test_local_receipt_attempt_does_not_backfill_parent_accepted_progress(self, tmp_path: Path) -> None:
        metadata = _metadata(dispatched=True)
        received = metadata.result.model_copy(update={
            "v2_state": "OBSERVED", "v2_schema_valid": True, "v2_status": "FAILED",
            "v2_failure_code": "VISION_TIMEOUT", "v2_attempt_number": 2,
            "raw_state": "OBSERVED", "raw_schema_valid": True, "raw_status": "FAILED",
            "raw_failure_code": "TIMEOUT", "gate_a_required": True,
            "observer_ref": "fixture-result-observer",
        })
        assertions = metadata.assertions.model_copy(update={
            "attempt_count_from_accepted_progress": contract.BindingBooleanObservationV1(
                state="OBSERVED", value=True, observer_ref="fixture-progress-observer",
            ),
        })
        metadata = metadata.model_copy(update={"result": received, "assertions": assertions}).revalidated()
        terminal = _terminal()
        receipt = execution.SupervisorRunResult(
            final_state=execution.ProgressState.TERMINAL, attempt_count=2,
            terminal_outcome="FAILED", cleanup_status=execution.CleanupStatus.SUCCEEDED,
            effective_outcome=execution.EffectiveOutcome.FAILED, raw_status="FAILED",
        )
        terminal = replace(
            terminal, adapter_call_count=1, attempt_count=1, session_ready=True,
            adapter_result=receipt, placement=_placement(),
            d11_report=replace(terminal.d11_report, dispatch_invocation_accepted=True,
                               generation_progress_known=True),
        )
        inventory = execution.Feat018ArtifactInventory((tmp_path,), max_entries=32)
        inventory.capture()
        writer = execution.Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        result = execution.finalize_smoke_run(
            terminal, run_id="run", evidence_id="ev", inventory=inventory,
            cleanup=lambda: execution.CleanupStatus.SUCCEEDED, writer=writer,
            incident=execution.Feat018IncidentWriter(
                Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
                repository_root=tmp_path, git_ignored=True,
            ),
            binding_metadata=metadata,
        )
        assert result.evidence.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["attempt_count"] == 1
        assert payload["binding_result_facts"]["v2_attempt_number"] == 2
        assert payload["status"] == "FAILED" and payload["generation_progress"] == "ACCEPTED"

    @pytest.mark.parametrize("mode", ["control", "absent_receipt", "local_attempt_drift", "raw_status_drift",
                                     "private_ref", "private_ref_prefix", "missing_ready", "hardware_drift"])
    def test_core_received_facts_are_checked_against_terminal_and_private_ids(self, tmp_path: Path, mode: str) -> None:
        manifest = _manifest()
        if mode in ("private_ref", "private_ref_prefix"):
            # observer_ref is local-only now, so the private-ID guard is exercised through a
            # still-published identity field carried consistently by every expectation.
            manifest = manifest.model_copy(update={"inputs": manifest.inputs.model_copy(update={
                "validation_artifact_ref": "provision-token" if mode == "private_ref"
                else "fixture:provision-token:receipt",
            })})
        metadata = _metadata(manifest, dispatched=True)
        metadata = metadata.model_copy(update={"result": metadata.result.model_copy(update={
            "v2_state": "OBSERVED", "v2_schema_valid": True, "v2_status": "FAILED",
            "v2_failure_code": "VISION_TIMEOUT", "v2_attempt_number": 1,
            "raw_state": "OBSERVED", "raw_schema_valid": True, "raw_status": "FAILED",
            "raw_failure_code": "TIMEOUT", "gate_a_required": True,
            "observer_ref": "fixture-result-observer",
        })}).revalidated()
        terminal = _terminal()
        receipt = execution.SupervisorRunResult(
            final_state=execution.ProgressState.TERMINAL, attempt_count=1,
            terminal_outcome="FAILED", cleanup_status=execution.CleanupStatus.SUCCEEDED,
            effective_outcome=execution.EffectiveOutcome.FAILED, raw_status="FAILED",
        )
        if mode == "local_attempt_drift":
            receipt = replace(receipt, attempt_count=2)
        elif mode == "raw_status_drift":
            receipt = replace(receipt, raw_status="SUCCEEDED")
        terminal = replace(
            terminal, adapter_call_count=1, attempt_count=None, session_ready=mode != "missing_ready",
            adapter_result=None if mode == "absent_receipt" else receipt, placement=_placement(),
            d11_report=replace(terminal.d11_report, dispatch_invocation_accepted=True),
        )
        if mode == "hardware_drift":
            terminal = replace(terminal, placement=execution.LightningPlacementFacts(
                gpu_sku="NVIDIA_L4", device_index=0, device_count=1, vram_mib=23035,
                cuda_available=True, bf16_supported=True, single_device_visible=True,
                model_device_index=0, input_device_index=0,
            ))
        inventory = execution.Feat018ArtifactInventory((tmp_path,), max_entries=32)
        inventory.capture()
        writer = execution.Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        result = execution.Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=execution.EffectiveOutcome.FAILED,
            cleanup=lambda: execution.CleanupStatus.SUCCEEDED, postflight=inventory.verify_provisional,
            terminal_result=terminal, binding_metadata=metadata,
        )
        if mode == "control":
            # Each negative mode differs from this committed control by exactly its own drift.
            assert result.committed
            return
        assert not result.committed
        assert not writer.json_path.exists() and not writer.markdown_path.exists()


_HOSTNAME = "studio-7.cloudspaces.example.ai"


def _placement() -> execution.LightningPlacementFacts:
    return execution.LightningPlacementFacts(
        gpu_sku="NVIDIA_L4", device_index=0, device_count=1, vram_mib=23034,
        cuda_available=True, bf16_supported=True, single_device_visible=True,
        model_device_index=0, input_device_index=0,
    )


def _d9_success_observations() -> tuple[execution.D9StreamObservation, ...]:
    ceilings = {execution.D9StreamName.STDOUT: execution.D9_STDOUT_MAX_BYTES,
                execution.D9StreamName.STDERR: execution.D9_STDERR_MAX_BYTES}
    return tuple(
        execution.D9StreamObservation(
            process_role=role, attempt_number=attempt, stream=stream, bytes_seen=0,
            ceiling=ceilings[stream], disposition=execution.D9StreamDisposition.ACCEPTED,
            terminal_category=execution.D9StreamTerminalCategory.WITHIN_LIMIT,
        )
        for role, attempt in ((execution.D9ProcessRole.OUTER_ADAPTER_WORKER, None),
                              (execution.D9ProcessRole.INNER_GENERATION_CHILD, 1))
        for stream in execution.D9StreamName
    )


def _success_terminal() -> execution.Feat018LiveSmokeResult:
    receipt = execution.SupervisorRunResult(
        final_state=execution.ProgressState.TERMINAL, attempt_count=1, terminal_outcome="SUCCEEDED",
        cleanup_status=execution.CleanupStatus.SUCCEEDED,
        effective_outcome=execution.EffectiveOutcome.SUCCEEDED, raw_status="SUCCEEDED",
        d9_observations=_d9_success_observations(),
    )
    terminal = _terminal()
    return replace(
        terminal, effective_outcome=execution.EffectiveOutcome.SUCCEEDED, failure_code=None,
        adapter_call_count=1, attempt_count=1, session_ready=True, adapter_result=receipt,
        placement=_placement(),
        d11_report=replace(terminal.d11_report, dispatch_invocation_accepted=True,
                           generation_progress_known=True),
    )


def _post_ready_terminal(code: execution.Feat018LiveSmokeFailureCode) -> execution.Feat018LiveSmokeResult:
    """An actual post-SESSION_READY pre-adapter stop with an accepted placement."""
    return replace(_terminal(), session_ready=True, placement=_placement(), failure_code=code)


def _success_metadata(observer: str = "fixture-observer", **staging: object) -> contract.BindingTerminalMetadataV1:
    metadata = _metadata(dispatched=True)
    session = metadata.session
    session = session.model_copy(update={
        name: getattr(session, name).model_copy(update={"observer_ref": observer})
        for name in ("readiness", "d4", "staging", "runtime")
    })
    session = session.model_copy(update={"staging": session.staging.model_copy(update=staging)})
    return metadata.model_copy(update={
        "session": session,
        "assertions": contract.BindingAssertionFactsV1(**{
            name: contract.BindingBooleanObservationV1(state="OBSERVED", value=True, observer_ref=observer)
            for name in _ASSERTION_NAMES
        }),
        "result": contract.BindingResultFactsV1(
            v2_state="OBSERVED", v2_schema_valid=True, v2_status="SUCCEEDED", v2_failure_code=None,
            v2_attempt_number=1, raw_state="OBSERVED", raw_schema_valid=True, raw_status="SUCCEEDED",
            raw_failure_code=None, gate_a_required=True, narration_status="NOT_SUPPLIED",
            observer_ref=observer,
        ),
        "consumption": contract.BindingBudgetConsumptionV1(
            state="OBSERVED", cap_outcome="WITHIN_CAP", gpu_minutes_consumed=0.25,
            d9_enforcement="CONFIRMED", observer_ref=observer,
        ),
    }).revalidated()


def _not_reached(section: Any) -> Any:
    return section.model_copy(update={"state": "NOT_REACHED"})


def _phase_session(blocker: str, *, mismatch: str | None = None,
                   readiness_status: str = "READY") -> contract.BindingSessionFactsV1:
    """A truthful pre-adapter session that stops at ``blocker``; adapter proof is never claimed."""
    manifest = _manifest()
    observed = _observed_session(manifest)
    unknown = _unknown_session()
    readiness = observed.readiness
    if readiness_status != "READY":
        readiness = readiness.model_copy(update={"status": readiness_status, "issue_codes": ("SYNTHETIC_ISSUE",)})
    d4 = observed.d4
    staging = observed.staging.model_copy(update={"image_reference_verified": False})
    runtime = observed.runtime
    if mismatch == "D4":
        d4 = d4.model_copy(update={"state": "OBSERVED_MISMATCH", "snapshot_sha256": "a" * 64})
    elif mismatch == "STAGING":
        staging = staging.model_copy(update={"state": "OBSERVED_MISMATCH", "staged_source_sha256": "a" * 64})
    elif mismatch == "DISPATCH":
        drifted = runtime.manifest.model_copy(update={"dependencies": tuple(
            item.model_copy(update={"version": "2.7.0"}) if item.package == "torch" else item
            for item in runtime.manifest.dependencies
        )})
        runtime = runtime.model_copy(update={
            "state": "OBSERVED_MISMATCH", "manifest": drifted,
            "runtime_manifest_sha256": drifted.canonical_sha256(),
        })
    sections = {"READINESS": (_not_reached(unknown.readiness), _not_reached(unknown.d4),
                              _not_reached(unknown.staging), _not_reached(unknown.runtime)),
                "D4": (readiness, d4, _not_reached(unknown.staging), _not_reached(unknown.runtime)),
                "STAGING": (readiness, d4, staging, _not_reached(unknown.runtime)),
                "DISPATCH": (readiness, d4, staging, runtime)}[blocker]
    if blocker == "READINESS" and readiness_status != "READY":
        sections = (readiness, *sections[1:])
    return contract.BindingSessionFactsV1(
        readiness=sections[0], d4=sections[1], staging=sections[2], runtime=sections[3],
        stopped_before=blocker,
    )


def _with_session(session: contract.BindingSessionFactsV1) -> contract.BindingTerminalMetadataV1:
    return _metadata().model_copy(update={"session": session}).revalidated()


def _publish(tmp_path: Path, metadata: Any, terminal: execution.Feat018LiveSmokeResult,
             outcome: execution.EffectiveOutcome, *, run_id: str = "run",
             evidence_id: str = "ev") -> tuple[execution.EvidenceCommitResult, Any]:
    inventory = execution.Feat018ArtifactInventory((tmp_path,), max_entries=32)
    inventory.capture()
    writer = execution.Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
    result = execution.Feat018EvidenceFinalizer(writer).finalize(
        run_id=run_id, evidence_id=evidence_id, runtime_outcome=outcome,
        cleanup=lambda: execution.CleanupStatus.SUCCEEDED, postflight=inventory.verify_provisional,
        terminal_result=terminal, binding_metadata=metadata,
    )
    return result, writer


class TestOfflineBindingRemediation:
    """Regressions for review findings M-1, M-2 and L-1..L-4 (synthetic, offline only)."""

    def test_success_control_publishes_verified_reference_and_null_failure_code(self, tmp_path: Path) -> None:
        result, writer = _publish(tmp_path, _success_metadata(), _success_terminal(),
                                  execution.EffectiveOutcome.SUCCEEDED)
        assert result.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["status"] == "SUCCEEDED" and payload["image_reference_verified"] is True
        assert payload["run_failure_code"] is None
        assert payload["binding_live_authorized"] is False
        assert payload["binding_live_cleanup_proven"] is False

    def test_m1_success_requires_exact_true_image_reference_verification(self, tmp_path: Path) -> None:
        metadata = _success_metadata(image_reference_verified=False)
        with pytest.raises(ValueError):
            metadata.validate_for_terminal(adapter_call_count=1, attempt_count=1, outcome="SUCCEEDED",
                                           failure_code=None, session_ready=True)
        result, writer = _publish(tmp_path, metadata, _success_terminal(),
                                  execution.EffectiveOutcome.SUCCEEDED)
        assert not result.committed
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        # A dispatched failure may truthfully carry an unverified reference.
        metadata.validate_for_terminal(adapter_call_count=1, attempt_count=None, outcome="FAILED",
                                       failure_code="ADAPTER_FAILED", session_ready=True)

    @pytest.mark.parametrize("blocker,mismatch", [
        ("D4", None), ("STAGING", None), ("DISPATCH", None), ("D4", "D4"),
        ("STAGING", "STAGING"), ("DISPATCH", "DISPATCH"),
    ])
    def test_m2_post_ready_observations_require_actual_session_ready(
        self, tmp_path: Path, blocker: str, mismatch: str | None,
    ) -> None:
        metadata = _with_session(_phase_session(blocker, mismatch=mismatch))
        terminal = _terminal()
        assert terminal.session_ready is False and terminal.placement is None
        with pytest.raises(ValueError):
            metadata.validate_for_terminal(adapter_call_count=0, attempt_count=None, outcome="FAILED",
                                           failure_code="PROVISION_FAILED", session_ready=False)
        result, writer = _publish(tmp_path, metadata, terminal, execution.EffectiveOutcome.FAILED)
        assert not result.committed
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        # The same carrier commits once the actual terminal reached SESSION_READY with placement.
        (tmp_path / "ready").mkdir()
        accepted, _ = _publish(tmp_path / "ready", metadata, _post_ready_terminal(
            execution.Feat018LiveSmokeFailureCode.SESSION_TTL_EXCEEDED,
        ), execution.EffectiveOutcome.FAILED)
        assert accepted.committed

    def test_m2_ready_claim_and_not_ready_contradictions_are_bidirectional(self, tmp_path: Path) -> None:
        ready_only = _with_session(_phase_session("D4").model_copy(update={
            "d4": _not_reached(_unknown_session().d4),
        }))
        for session_ready in (False, None):
            with pytest.raises(ValueError):
                ready_only.validate_for_terminal(adapter_call_count=0, attempt_count=None, outcome="FAILED",
                                                 failure_code="SESSION_NOT_READY", session_ready=session_ready)
        result, writer = _publish(tmp_path, ready_only, replace(
            _terminal(), failure_code=execution.Feat018LiveSmokeFailureCode.SESSION_NOT_READY,
        ), execution.EffectiveOutcome.FAILED)
        assert not result.committed and not writer.json_path.exists()
        not_ready = _with_session(_phase_session("READINESS", readiness_status="NOT_READY"))
        with pytest.raises(ValueError):
            not_ready.validate_for_terminal(adapter_call_count=0, attempt_count=None, outcome="FAILED",
                                            failure_code="SESSION_NOT_READY", session_ready=True)
        # Truthful failure control: an observed NOT_READY without SESSION_READY publishes.
        (tmp_path / "control").mkdir()
        control, control_writer = _publish(tmp_path / "control", not_ready, replace(
            _terminal(), failure_code=execution.Feat018LiveSmokeFailureCode.SESSION_NOT_READY,
        ), execution.EffectiveOutcome.FAILED)
        assert control.committed
        payload = json.loads(control_writer.json_path.read_bytes())
        assert payload["readiness_status"] == "NOT_READY"
        assert payload["run_failure_code"] == "SESSION_NOT_READY"

    @pytest.mark.parametrize("mismatch", [None, "DISPATCH"])
    def test_m2_received_runtime_requires_actual_placement(self, tmp_path: Path, mismatch: str | None) -> None:
        metadata = _with_session(_phase_session("DISPATCH", mismatch=mismatch))
        terminal = replace(_post_ready_terminal(execution.Feat018LiveSmokeFailureCode.SESSION_TTL_EXCEEDED),
                           placement=None)
        result, writer = _publish(tmp_path, metadata, terminal, execution.EffectiveOutcome.FAILED)
        assert not result.committed
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        drifted = replace(terminal, placement=replace(_placement(), vram_mib=23035))
        (tmp_path / "drift").mkdir()
        result, _ = _publish(tmp_path / "drift", metadata, drifted, execution.EffectiveOutcome.FAILED)
        assert not result.committed

    @pytest.mark.parametrize("phase,state_key,value_key,actual", [
        ("D4", "d4_observation_state", "d4_snapshot_sha256", "a" * 64),
        ("STAGING", "staging_observation_state", "staged_source_sha256", "a" * 64),
        ("DISPATCH", "runtime_observation_state", "runtime_manifest", None),
    ])
    def test_l1_truthful_mismatch_publishes_actual_safe_observation(
        self, tmp_path: Path, phase: str, state_key: str, value_key: str, actual: str | None,
    ) -> None:
        metadata = _with_session(_phase_session(phase, mismatch=phase))
        terminal = _post_ready_terminal(execution.Feat018LiveSmokeFailureCode.LIFECYCLE_FACTS_INVALID)
        result, writer = _publish(tmp_path, metadata, terminal, execution.EffectiveOutcome.FAILED)
        assert result.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload[state_key] == "OBSERVED_MISMATCH"
        assert payload["session_phase_blocker"] == phase
        assert payload["status"] == "FAILED" and payload["terminal_kind"] == "PRE_ADAPTER"
        assert payload["adapter_call_count"] == 0 and payload["attempt_count"] is None
        assert payload["run_failure_code"] == "LIFECYCLE_FACTS_INVALID"
        assert payload["source_sha256"] == _SOURCE_HASH
        assert payload["binding_live_authorized"] is False
        if actual is not None:
            assert payload[value_key] == actual
        else:
            torch = [item for item in payload[value_key]["dependencies"] if item["package"] == "torch"]
            assert torch == [{"package": "torch", "version": "2.7.0"}]
        assert "image_reference_verified" not in payload or payload["image_reference_verified"] is False
        allowed = set(_publish_keys_for(tmp_path / "observed", phase))
        assert set(payload) <= allowed

    @pytest.mark.parametrize("mode", [
        "labelled_without_difference", "observed_hides_difference", "not_the_blocker",
        "later_phase_after_mismatch", "readiness_state", "assertion_state",
    ])
    def test_l1_mismatch_construction_rejects_false_or_impossible_claims(self, mode: str) -> None:
        session = _phase_session("STAGING", mismatch="STAGING")
        if mode == "labelled_without_difference":
            session = session.model_copy(update={"staging": session.staging.model_copy(
                update={"staged_source_sha256": _SOURCE_HASH})})
        elif mode == "observed_hides_difference":
            session = session.model_copy(update={"staging": session.staging.model_copy(
                update={"state": "OBSERVED"})})
        elif mode == "not_the_blocker":
            d4_mismatch = _phase_session("D4", mismatch="D4")
            with pytest.raises(ValidationError) as error:
                contract.BindingSessionFactsV1(
                    readiness=d4_mismatch.readiness, d4=d4_mismatch.d4,
                    staging=d4_mismatch.staging, runtime=d4_mismatch.runtime, stopped_before="STAGING",
                )
            assert error.value.error_count() == 1
            assert error.value.errors()[0]["type"] == "value_error"
            assert error.value.errors()[0]["msg"] == "offline contract validation failed"
            return
        elif mode == "later_phase_after_mismatch":
            session = session.model_copy(update={"runtime": _observed_session(_manifest()).runtime})
        elif mode == "readiness_state":
            with pytest.raises(ValidationError):
                contract.BindingReadinessFactsV1(
                    state="OBSERVED_MISMATCH", observer_ref="fixture", status="READY", issue_codes=(),
                    model_load_performed=False, inference_performed=False,
                )
            return
        else:
            with pytest.raises(ValidationError):
                contract.BindingBooleanObservationV1(state="OBSERVED_MISMATCH", value=False, observer_ref="fixture")
            return
        with pytest.raises(ValueError):
            _metadata().model_copy(update={"session": session}).revalidated()

    @pytest.mark.parametrize("call,attempt,outcome", [(1, None, "FAILED"), (1, 1, "SUCCEEDED")])
    def test_l1_mismatch_is_rejected_on_dispatch_and_success(self, call: int, attempt: int | None,
                                                            outcome: str) -> None:
        metadata = _with_session(_phase_session("STAGING", mismatch="STAGING"))
        with pytest.raises(ValueError):
            metadata.validate_for_terminal(
                adapter_call_count=call, attempt_count=attempt, outcome=outcome,
                failure_code=None if outcome == "SUCCEEDED" else "ADAPTER_FAILED", session_ready=True,
            )

    def test_l1_pre_adapter_metadata_cannot_claim_adapter_reference_proof(self) -> None:
        session = _phase_session("DISPATCH")
        claimed = _with_session(session.model_copy(update={"staging": session.staging.model_copy(
            update={"image_reference_verified": True})}))
        with pytest.raises(ValueError):
            claimed.validate_for_terminal(adapter_call_count=0, attempt_count=None, outcome="FAILED",
                                          failure_code="SESSION_TTL_EXCEEDED", session_ready=True)

    @pytest.mark.parametrize("phase,section,identity", [
        ("D4", "d4", "snapshot_sha256"),
        ("STAGING", "staging", "staged_source_sha256"),
        ("DISPATCH", "runtime", "session_inventory_sha256"),
    ])
    @pytest.mark.parametrize("violation", ["malformed_hash", "missing_value", "missing_observer"])
    def test_l1_mismatch_retains_strict_identity_and_provenance(
        self, phase: str, section: str, identity: str, violation: str,
    ) -> None:
        session = _phase_session(phase, mismatch=phase)
        update = {identity: "invalid" if violation == "malformed_hash" else None}
        if violation == "missing_observer":
            update = {"observer_ref": None}
        invalid = session.model_copy(update={section: getattr(session, section).model_copy(update=update)})
        with pytest.raises(ValidationError):
            _metadata().model_copy(update={"session": invalid}).revalidated()

    def test_l1_runtime_mismatch_rejects_forged_actual_manifest_hash(self) -> None:
        session = _phase_session("DISPATCH", mismatch="DISPATCH")
        invalid = session.model_copy(update={"runtime": session.runtime.model_copy(
            update={"runtime_manifest_sha256": "b" * 64})})
        with pytest.raises(ValidationError) as error:
            _metadata().model_copy(update={"session": invalid}).revalidated()
        assert error.value.error_count() == 1
        assert error.value.errors()[0]["type"] == "value_error"
        assert error.value.errors()[0]["msg"] == "offline contract validation failed"

    @pytest.mark.parametrize("mode", ["valid", "evidence_id", "evidence_id_uppercase",
                                      "evidence_id_empty", "evidence_id_long", "evidence_id_type",
                                      "writer", "incident", "run_id"])
    def test_l2_publication_identity_is_checked_before_authorization(self, tmp_path: Path, mode: str) -> None:
        cleanup = Mock(return_value=execution.CleanupStatus.SUCCEEDED)
        prepared, preflight, finalizer, writer = _wrapper_parts(tmp_path, cleanup=cleanup)
        facts = Mock(return_value=_preflight_facts(prepared.manifest))
        metadata = Mock()
        preflight.produce_facts = facts
        finalizer.produce_metadata = metadata
        if mode == "evidence_id":
            finalizer.evidence_id = "NOT VALID"
        elif mode == "evidence_id_uppercase":
            finalizer.evidence_id = "EV"
        elif mode == "evidence_id_empty":
            finalizer.evidence_id = ""
        elif mode == "evidence_id_long":
            finalizer.evidence_id = "e" * 129
        elif mode == "evidence_id_type":
            finalizer.evidence_id = 1
        elif mode == "writer":
            finalizer.writer = execution.Feat018EvidenceCommitWriter(tmp_path / "other.json", tmp_path / "other.md")
        elif mode == "incident":
            finalizer.incident = execution.Feat018IncidentWriter(
                Path("tmp/feat018-live-lightning-incident-run/INCIDENT.md"),
                repository_root=tmp_path, git_ignored=True,
            )
        elif mode == "run_id":
            finalizer.run_id = "other-run"
        coordinator = Mock(return_value=_terminal())
        config, d11 = _fixture_configs()
        result = binding.run_offline_binding(
            prepared, preflight=preflight, finalizer=finalizer,
            controller=object(), adapter_dispatch=object(), observer=object(),
            config=config, d11_config=d11, session_id="synthetic-session",
            clock=lambda: 0.0, coordinator=coordinator,
        )
        if mode == "valid":
            coordinator.assert_called_once()
            return
        assert result.failure_code is execution.Feat018LiveSmokeFailureCode.NOT_AUTHORIZED
        assert result.adapter_call_count == 0 and result.attempt_count is None
        coordinator.assert_not_called()
        facts.assert_not_called()
        metadata.assert_not_called()
        cleanup.assert_not_called()
        assert not preflight.has_accepted_facts and finalizer.finalization is None
        assert finalizer.cleanup_status is None
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert not preflight.incident.path.exists() and not finalizer.incident.path.exists()

    @pytest.mark.parametrize("code", [
        execution.Feat018LiveSmokeFailureCode.PROVISION_FAILED,
        execution.Feat018LiveSmokeFailureCode.SESSION_TERMINATION_FAILED,
    ])
    def test_l3_run_failure_code_equals_actual_terminal_enum(self, tmp_path: Path,
                                                             code: execution.Feat018LiveSmokeFailureCode) -> None:
        result, writer = _publish(tmp_path, _metadata(), replace(_terminal(), failure_code=code),
                                  execution.EffectiveOutcome.FAILED)
        assert result.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["run_failure_code"] == code.value
        assert "run_failure_code" not in _metadata().evidence_fields()

    @pytest.mark.parametrize("mode", ["metadata_supplies_code", "untyped_terminal_code"])
    def test_l3_run_failure_code_cannot_come_from_metadata_or_untyped_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str,
    ) -> None:
        terminal = _terminal()
        metadata: contract.BindingTerminalMetadataV1 | None = _metadata()
        if mode == "metadata_supplies_code":
            original = contract.BindingTerminalMetadataV1.evidence_fields
            monkeypatch.setattr(contract.BindingTerminalMetadataV1, "evidence_fields",
                                lambda self: {**original(self), "run_failure_code": None})
        else:
            # Exercise the terminal serializer directly: only the closed enum is publishable.
            terminal, metadata = replace(terminal, failure_code="PROVISION_FAILED"), None
        result, writer = _publish(tmp_path, metadata, terminal, execution.EffectiveOutcome.FAILED)
        assert not result.committed
        assert not writer.json_path.exists() and not writer.markdown_path.exists()

    def test_l4_hostname_observer_refs_stay_local_in_nested_evidence(self, tmp_path: Path) -> None:
        metadata = _success_metadata(observer=_HOSTNAME)
        metadata = metadata.model_copy(update={"preflight": metadata.preflight.model_copy(
            update={"observer_ref": _HOSTNAME})}).revalidated()
        assert metadata.result.observer_ref == _HOSTNAME  # retained locally, never rewritten
        assert metadata.preflight.observer_ref == _HOSTNAME
        assert _HOSTNAME not in repr(metadata)
        fields = metadata.evidence_fields()
        encoded = json.dumps(fields, sort_keys=True)
        assert _HOSTNAME not in encoded and "observer_ref" not in encoded
        result, writer = _publish(tmp_path, metadata, _success_terminal(),
                                  execution.EffectiveOutcome.SUCCEEDED)
        assert result.committed
        for path in (writer.json_path, writer.markdown_path):
            text = path.read_text(encoding="utf-8")
            assert _HOSTNAME not in text and "observer_ref" not in text

    def test_l4_rejected_publication_diagnostics_exclude_local_provenance(self, tmp_path: Path) -> None:
        metadata = _success_metadata(observer=_HOSTNAME, image_reference_verified=False)
        result, writer = _publish(tmp_path, metadata, _success_terminal(),
                                  execution.EffectiveOutcome.SUCCEEDED)
        assert not result.committed
        assert _HOSTNAME not in (result.failure_reason or "")
        with pytest.raises(ValueError) as error:
            metadata.validate_for_terminal(adapter_call_count=1, attempt_count=1, outcome="SUCCEEDED",
                                           failure_code=None, session_ready=True)
        assert _HOSTNAME not in str(error.value)
        (tmp_path / "wrapper").mkdir()
        _, preflight, finalizer, _ = _wrapper_parts(tmp_path / "wrapper")
        preflight.verify(synthetic_session_id="synthetic-session")
        finalizer.produce_metadata = lambda _result: metadata
        finalizer.finalize(result=_terminal())
        assert finalizer.finalization.incident_written
        assert _HOSTNAME not in preflight.incident.path.read_text(encoding="utf-8")

    @pytest.mark.parametrize("entry", ["constructor", "mapping", "json", "revalidated"])
    def test_l4_invalid_carrier_errors_exclude_local_provenance(self, entry: str) -> None:
        invalid = _success_metadata(observer=_HOSTNAME).session.staging.model_copy(
            update={"state": "UNKNOWN"}
        )
        with pytest.raises(ValidationError) as error:
            if entry == "constructor":
                contract.BindingStagingFactsV1(**invalid.model_dump())
            elif entry == "mapping":
                contract.BindingStagingFactsV1.model_validate(invalid.model_dump())
            elif entry == "json":
                contract.BindingStagingFactsV1.model_validate_json(invalid.model_dump_json())
            else:
                invalid.revalidated()
        # Ordinary exception rendering and structured diagnostics are both publication
        # surfaces; the original observation still retains its private provenance.
        assert invalid.observer_ref == _HOSTNAME
        assert _HOSTNAME not in str(error.value)
        assert _HOSTNAME not in repr(error.value)
        assert _HOSTNAME not in error.value.json()
        assert _HOSTNAME not in str(error.value.errors())

    def test_l4_nested_revalidation_errors_exclude_local_provenance(self) -> None:
        metadata = _success_metadata(observer=_HOSTNAME)
        invalid = metadata.model_copy(update={"session": metadata.session.model_copy(update={
            "staging": metadata.session.staging.model_copy(update={"state": "UNKNOWN"}),
        })})
        with pytest.raises(ValidationError) as error:
            invalid.revalidated()
        assert _HOSTNAME not in str(error.value)
        assert _HOSTNAME not in error.value.json()
        assert _HOSTNAME not in str(error.value.errors())

    @pytest.mark.parametrize("entry", ["constructor", "strings", "frozen_assignment"])
    def test_l4_primitive_and_frozen_errors_exclude_local_provenance(self, entry: str) -> None:
        observation = contract.BindingBooleanObservationV1(
            state="OBSERVED", value=True, observer_ref="fixture-observer",
        )
        with pytest.raises(ValidationError) as error:
            if entry == "constructor":
                contract.BindingBooleanObservationV1(
                    state="OBSERVED", value=True, observer_ref=_HOSTNAME + "/private",
                )
            elif entry == "strings":
                contract.BindingBooleanObservationV1.model_validate_strings({
                    "state": "OBSERVED", "value": "true", "observer_ref": _HOSTNAME + "/private",
                })
            else:
                observation.observer_ref = _HOSTNAME
        assert observation.observer_ref == "fixture-observer"
        assert _HOSTNAME not in str(error.value)
        assert _HOSTNAME not in repr(error.value)
        assert _HOSTNAME not in error.value.json()
        assert _HOSTNAME not in str(error.value.errors())

    @pytest.mark.parametrize("entry", ["constructor", "mapping", "json"])
    def test_l4_extra_field_locations_cannot_publish_local_provenance(self, entry: str) -> None:
        data = {"state": "OBSERVED", "value": True, "observer_ref": _HOSTNAME,
                _HOSTNAME: "synthetic-unexpected-field"}
        with pytest.raises(ValidationError) as error:
            if entry == "constructor":
                contract.BindingBooleanObservationV1(**data)
            elif entry == "mapping":
                contract.BindingBooleanObservationV1.model_validate(data)
            else:
                contract.BindingBooleanObservationV1.model_validate_json(json.dumps(data))
        assert error.value.error_count() == 1
        assert error.value.errors()[0]["type"] == "extra_forbidden"
        assert _HOSTNAME not in str(error.value)
        assert _HOSTNAME not in repr(error.value)
        assert _HOSTNAME not in error.value.json()
        assert _HOSTNAME not in str(error.value.errors())


def _publish_keys_for(tmp_path: Path, phase: str) -> list[str]:
    """Keys published by the matching truthful OBSERVED stop: mismatch adds no field names."""
    tmp_path.mkdir()
    result, writer = _publish(tmp_path, _with_session(_phase_session(phase)), _post_ready_terminal(
        execution.Feat018LiveSmokeFailureCode.LIFECYCLE_FACTS_INVALID,
    ), execution.EffectiveOutcome.FAILED)
    assert result.committed
    return list(json.loads(writer.json_path.read_bytes()))


class TestIndependentReviewRemediation:
    @pytest.mark.parametrize("entry", ["adapter_python", "adapter_json", "core_python", "core_json"])
    @pytest.mark.parametrize("nested", [False, True])
    @pytest.mark.parametrize("violation,expected_type", [
        ("extra_key", "extra_forbidden"),
        ("unobserved_provenance", "value_error"),
        ("invalid_observer", "string_pattern_mismatch"),
    ])
    def test_r1_schema_errors_redact_every_diagnostic_surface(
        self, entry: str, nested: bool, violation: str, expected_type: str,
    ) -> None:
        observation = {"state": "OBSERVED", "value": True, "observer_ref": _HOSTNAME}
        if violation == "extra_key":
            observation[_HOSTNAME] = "synthetic-unexpected-field"
        elif violation == "unobserved_provenance":
            observation.update(state="UNKNOWN", value=None)
        else:
            observation["observer_ref"] = _HOSTNAME + "/private"
        model: Any = contract.BindingBooleanObservationV1
        data: Any = observation
        if nested:
            model = contract.BindingAssertionFactsV1
            data = _metadata().assertions.model_dump(mode="python")
            data["nested_spawn"] = observation
        with pytest.raises(ValidationError) as error:
            if entry == "adapter_python":
                TypeAdapter(model).validate_python(data)
            elif entry == "adapter_json":
                TypeAdapter(model).validate_json(json.dumps(data))
            elif entry == "core_python":
                model.__pydantic_validator__.validate_python(data)
            else:
                model.__pydantic_validator__.validate_json(json.dumps(data))
        assert error.value.error_count() == 1
        detail = error.value.errors()[0]
        assert detail["type"] == expected_type and detail["loc"] == ()
        assert detail.get("input") is None and "ctx" not in detail
        for rendered in (str(error.value), repr(error.value), str(error.value.errors()), error.value.json()):
            assert _HOSTNAME not in rendered

    @pytest.mark.parametrize("construction", ["model_construct", "model_copy"])
    @pytest.mark.parametrize("value", [1, _HOSTNAME])
    @pytest.mark.parametrize("nested", [False, True])
    def test_r1_type_adapter_rejects_unchecked_invalid_instances(
        self, construction: str, value: object, nested: bool,
    ) -> None:
        observation = contract.BindingBooleanObservationV1(
            state="OBSERVED", value=True, observer_ref=_HOSTNAME,
        )
        invalid = (contract.BindingBooleanObservationV1.model_construct(
            **{**observation.model_dump(), "value": value},
        ) if construction == "model_construct" else observation.model_copy(update={"value": value}))
        model: Any = contract.BindingBooleanObservationV1
        if nested:
            model = contract.BindingAssertionFactsV1
            invalid = _metadata().assertions.model_copy(update={"nested_spawn": invalid})
        with pytest.raises(ValidationError) as error:
            TypeAdapter(model).validate_python(invalid)
        assert error.value.errors()[0]["type"] == "bool_type"
        for rendered in (str(error.value), repr(error.value), str(error.value.errors()), error.value.json()):
            assert _HOSTNAME not in rendered

    @pytest.mark.parametrize("violation", ["extra_key", "missing_value"])
    def test_r1_unchecked_fields_cannot_bypass_schema_validation(self, violation: str) -> None:
        observation = contract.BindingBooleanObservationV1(
            state="OBSERVED", value=True, observer_ref=_HOSTNAME,
        )
        if violation == "extra_key":
            invalid = observation.model_copy(update={_HOSTNAME: "synthetic-private-extra"})
            expected = "extra_forbidden"
        else:
            data = observation.model_dump()
            del data["value"]
            invalid = contract.BindingBooleanObservationV1.model_construct(**data)
            expected = "missing"
        with pytest.raises(ValidationError) as error:
            TypeAdapter(contract.BindingBooleanObservationV1).validate_python(invalid)
        assert error.value.errors()[0]["type"] == expected
        assert _HOSTNAME not in error.value.json()

    def test_r1_redaction_does_not_change_unrelated_pydantic_validation(self) -> None:
        with pytest.raises(ValidationError) as error:
            TypeAdapter(bool).validate_python(_HOSTNAME, strict=True)
        assert error.value.errors()[0]["input"] == _HOSTNAME

    def test_r1_json_roundtrip_keeps_python_tuple_validation_strict(self) -> None:
        inventory = _manifest().session_inventory
        restored = TypeAdapter(contract.RuntimeEnvironmentInventoryV1).validate_json(inventory.model_dump_json())
        assert restored == inventory
        assert restored.canonical_sha256() == inventory.canonical_sha256()
        with pytest.raises(ValidationError) as error:
            TypeAdapter(contract.RuntimeEnvironmentInventoryV1).validate_python(inventory.model_dump(mode="json"))
        assert error.value.error_count() == 2
        assert all(detail["type"] == "tuple_type" for detail in error.value.errors())

    @pytest.mark.parametrize("with_metadata", [False, True])
    @pytest.mark.parametrize("contradiction", [
        "failed_promoted", "success_downgraded", "success_failure_code", "failed_without_code",
        "untyped_failure_code", "missing_receipt", "unaccepted_d9", "failed_receipt",
        "receipt_attempt_mismatch", "receipt_bool_attempt", "bool_call_count", "bool_attempt_count",
        "missing_attempt_count", "session_not_ready", "terminal_cleanup_failed", "retained_owner",
        "release_unverified", "dispatch_event_mismatch", "generation_event_mismatch",
        "preflight_not_verified", "report_bool_dispatch", "report_bool_generation", "report_private_generation",
    ])
    def test_r2_supplied_terminal_contradictions_never_publish(
        self, tmp_path: Path, with_metadata: bool, contradiction: str,
    ) -> None:
        terminal = _success_terminal()
        metadata = _success_metadata()
        outcome = execution.EffectiveOutcome.SUCCEEDED
        if contradiction in ("failed_promoted", "failed_without_code", "untyped_failure_code"):
            terminal, metadata = _terminal(), _metadata()
            if contradiction == "failed_without_code":
                terminal = replace(terminal, failure_code=None)
                outcome = execution.EffectiveOutcome.FAILED
            elif contradiction == "untyped_failure_code":
                terminal = replace(terminal, failure_code="PROVISION_FAILED")
                outcome = execution.EffectiveOutcome.FAILED
        elif contradiction == "success_downgraded":
            outcome = execution.EffectiveOutcome.FAILED
        elif contradiction == "success_failure_code":
            terminal = replace(terminal, failure_code=execution.Feat018LiveSmokeFailureCode.ADAPTER_FAILED)
        elif contradiction == "missing_receipt":
            terminal = replace(terminal, adapter_result=None)
        elif contradiction == "unaccepted_d9":
            terminal = replace(terminal, adapter_result=replace(terminal.adapter_result, d9_observations=()))
        elif contradiction == "failed_receipt":
            terminal = replace(terminal, adapter_result=replace(
                terminal.adapter_result, terminal_outcome="FAILED", raw_status="FAILED",
                effective_outcome=execution.EffectiveOutcome.FAILED,
                primary_failure_reason="synthetic-failure",
            ))
        elif contradiction in ("receipt_attempt_mismatch", "receipt_bool_attempt"):
            terminal = replace(terminal, adapter_result=replace(
                terminal.adapter_result, attempt_count=2 if contradiction == "receipt_attempt_mismatch" else True,
            ))
        elif contradiction == "bool_call_count":
            terminal = replace(terminal, adapter_call_count=True)
        elif contradiction == "bool_attempt_count":
            terminal = replace(terminal, attempt_count=True)
        elif contradiction == "missing_attempt_count":
            terminal = replace(terminal, attempt_count=None)
        elif contradiction == "session_not_ready":
            terminal = replace(terminal, session_ready=False)
        elif contradiction == "terminal_cleanup_failed":
            terminal = replace(terminal, cleanup_status=execution.CleanupStatus.CLEANUP_FAILED)
        elif contradiction == "retained_owner":
            terminal = replace(terminal, cleanup_failures=(execution.Feat018CleanupFailedError("synthetic-owner"),))
        elif contradiction == "release_unverified":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, verification="UNVERIFIED"))
        elif contradiction == "dispatch_event_mismatch":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, dispatch_invocation_accepted=False))
        elif contradiction == "generation_event_mismatch":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, generation_progress_known=False))
        elif contradiction == "preflight_not_verified":
            terminal = replace(terminal, preflight_verified=False)
        elif contradiction == "report_bool_dispatch":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, dispatch_invocation_accepted=1))
        elif contradiction == "report_bool_generation":
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, generation_progress_known=1))
        else:
            terminal = replace(terminal, d11_report=replace(terminal.d11_report, generation=_HOSTNAME))
        result, writer = _publish(tmp_path, metadata if with_metadata else None, terminal, outcome)
        assert not result.committed and result.failure_reason is not None
        assert _HOSTNAME not in result.failure_reason
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert list(tmp_path.iterdir()) == []
    @pytest.mark.parametrize("outcome", [execution.EffectiveOutcome.SUCCEEDED, execution.EffectiveOutcome.FAILED])
    def test_r2_legacy_without_terminal_preserves_actual_outcome(
        self, tmp_path: Path, outcome: execution.EffectiveOutcome,
    ) -> None:
        writer = execution.Feat018EvidenceCommitWriter(tmp_path / "evidence.json", tmp_path / "evidence.md")
        inventory = execution.Feat018ArtifactInventory((tmp_path,), max_entries=32)
        inventory.capture()
        result = execution.Feat018EvidenceFinalizer(writer).finalize(
            run_id="run", evidence_id="ev", runtime_outcome=outcome,
            cleanup=lambda: execution.CleanupStatus.SUCCEEDED, postflight=inventory.verify_provisional,
        )
        assert result.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["status"] == outcome.value
        assert not {"run_failure_code", "adapter_call_count", "attempt_count", "terminal_kind"} & payload.keys()
        assert "```json" not in writer.markdown_path.read_text(encoding="utf-8")
        assert execution.read_committed_pair(writer.json_path, writer.markdown_path).verdict is execution.PairVerdict.AUTHORITATIVE

    @pytest.mark.parametrize("with_metadata", [False, True])
    def test_r2_dispatched_failure_keeps_unknown_accepted_progress(
        self, tmp_path: Path, with_metadata: bool,
    ) -> None:
        terminal = _terminal()
        terminal = replace(
            terminal, adapter_call_count=1, session_ready=True, placement=_placement(),
            failure_code=execution.Feat018LiveSmokeFailureCode.ADAPTER_FAILED,
            d11_report=replace(terminal.d11_report, dispatch_invocation_accepted=True),
        )
        result, writer = _publish(tmp_path, _metadata(dispatched=True) if with_metadata else None,
                                  terminal, execution.EffectiveOutcome.FAILED)
        assert result.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["adapter_call_count"] == 1 and payload["attempt_count"] is None
        assert payload["generation_progress"] == "UNKNOWN"
        assert payload["run_failure_code"] == "ADAPTER_FAILED"

    @pytest.mark.parametrize("case", [
        "success", "failure", "success_without_metadata", "failure_without_metadata",
        "D4", "STAGING", "DISPATCH",
    ])
    def test_r3_both_artifacts_have_the_same_validated_metadata(
        self, tmp_path: Path, case: str,
    ) -> None:
        if case.startswith("success"):
            terminal, metadata, outcome = _success_terminal(), _success_metadata(observer=_HOSTNAME), execution.EffectiveOutcome.SUCCEEDED
        elif case.startswith("failure"):
            terminal, metadata, outcome = _terminal(), _metadata(), execution.EffectiveOutcome.FAILED
        else:
            terminal = _post_ready_terminal(execution.Feat018LiveSmokeFailureCode.LIFECYCLE_FACTS_INVALID)
            metadata = _with_session(_phase_session(case, mismatch=case))
            outcome = execution.EffectiveOutcome.FAILED
        if case.endswith("without_metadata"):
            metadata = None
        result, writer = _publish(tmp_path, metadata, terminal, outcome)
        assert result.committed
        payload = json.loads(writer.json_path.read_bytes())
        markdown_bytes = writer.markdown_path.read_bytes()
        markdown = markdown_bytes.decode("utf-8")
        projection = json.loads(markdown.split("```json\n", 1)[1].split("\n```", 1)[0])
        header = dict(line.split(": ", 1) for line in markdown.split("```json\n", 1)[0].splitlines() if ": " in line)
        assert header["run_id"] == payload["run_id"] and header["evidence_id"] == payload["evidence_id"]
        published = {**projection, **{key: header[key] for key in ("status", "cleanup_status", "postflight_status")}}
        envelope = {"run_id", "evidence_id", "companion_markdown_sha256", "commit_state"}
        assert published == {key: value for key, value in payload.items() if key not in envelope}
        assert {"run_failure_code", "adapter_call_count", "attempt_count", "terminal_kind",
                "generation_progress", "cleanup_verification", "cleanup_generation",
                "unresolved_operation_count"} <= projection.keys()
        assert projection["run_failure_code"] == (terminal.failure_code.value if terminal.failure_code else None)
        assert projection["adapter_call_count"] == terminal.adapter_call_count
        assert projection["attempt_count"] == terminal.attempt_count
        assert payload["companion_markdown_sha256"] == sha256(markdown_bytes).hexdigest()
        assert not envelope & projection.keys()
        assert "companion_markdown_sha256" not in markdown
        assert "observer_ref" not in markdown and _HOSTNAME not in markdown
        assert "observer_ref" not in json.dumps(payload) and _HOSTNAME not in json.dumps(payload)
        assert execution.read_committed_pair(writer.json_path, writer.markdown_path).verdict is execution.PairVerdict.AUTHORITATIVE


_PRIVATE_DIAGNOSTIC_MARKER = "synthetic-private-diagnostic-marker"


def _assert_private_diagnostics_absent(error: Exception) -> None:
    rendered = [str(error), repr(error)]
    if isinstance(error, ValidationError):
        rendered.extend((str(error.errors()), error.json()))
        assert error.title == "FEAT018OfflineContract"
        assert all(detail["msg"] == "offline contract validation failed" for detail in error.errors())
    assert all(_PRIVATE_DIAGNOSTIC_MARKER not in text for text in rendered)


def _unchecked_dataclass_update(value: Any, **updates: object) -> Any:
    """Simulate a forged supplied carrier without invoking its normal constructor."""
    unchecked = replace(value)
    for name, update in updates.items():
        object.__setattr__(unchecked, name, update)
    return unchecked


def _terminal_with_known_cleanup_session(*, success: bool = True) -> execution.Feat018LiveSmokeResult:
    terminal = _success_terminal() if success else _terminal()
    report = terminal.d11_report
    assert report is not None and report.observation is not None
    provision = report.operations[0].provision
    session = execution.LightningSessionRefV1(provision, "known-session-token")
    operation = execution.LightningOperationRefV1(
        provision, "known-operation-token", execution.D11OperationKind.WAIT_READY, session,
    )
    recovery = execution.LightningOperationRefV1(
        provision, "cancel-operation-token", execution.D11OperationKind.CANCEL,
        recovery_of="retained-recovery-token",
    )
    return replace(terminal, d11_report=replace(
        report, operations=(*report.operations, operation, recovery),
        observation=replace(report.observation, resources=((session.resource_identity, "terminated"),)),
    ))


class TestFourFindingBatchRemediation:
    @pytest.mark.parametrize("unchecked", [False, True])
    def test_m2_field_deletion_diagnostics_redact_hostile_names(self, unchecked: bool) -> None:
        observation = contract.BindingBooleanObservationV1(
            state="OBSERVED", value=True, observer_ref="fixture-observer",
        )
        if unchecked:
            observation = observation.model_copy(update={_PRIVATE_DIAGNOSTIC_MARKER: True})
        with pytest.raises(ValidationError) as error:
            delattr(observation, _PRIVATE_DIAGNOSTIC_MARKER)
        _assert_private_diagnostics_absent(error.value)

    @pytest.mark.parametrize("entry", ["revalidated", "model_dump", "model_dump_json"])
    def test_m1_unchecked_observation_never_exposes_serialization_input(self, entry: str) -> None:
        observation = contract.BindingBooleanObservationV1(
            state="OBSERVED", value=True, observer_ref=_PRIVATE_DIAGNOSTIC_MARKER,
        ).model_copy(update={"value": _PRIVATE_DIAGNOSTIC_MARKER})
        with pytest.raises((ValidationError, ValueError)) as error:
            if entry == "model_dump":
                observation.model_dump(warnings="error")
            elif entry == "model_dump_json":
                observation.model_dump_json(warnings="error")
            else:
                observation.revalidated()
        _assert_private_diagnostics_absent(error.value)

    @pytest.mark.parametrize("entry", ["revalidated", "prepare"])
    def test_m1_nested_unchecked_manifest_fails_privately_at_supported_entry(self, entry: str) -> None:
        manifest = _manifest()
        invalid = manifest.model_copy(update={"ceilings": manifest.ceilings.model_copy(
            update={"stdout_bytes": _PRIVATE_DIAGNOSTIC_MARKER},
        )})
        loader = Mock(return_value=_runtime_config())
        with pytest.raises((ValidationError, ValueError)) as error:
            if entry == "revalidated":
                invalid.revalidated()
            else:
                _prepared(invalid, loader=loader)
        _assert_private_diagnostics_absent(error.value)
        loader.assert_not_called()

    @pytest.mark.parametrize("entry", ["model_dump", "model_dump_json", "canonical_bytes", "revalidated"])
    def test_m1_private_custom_serializer_errors_are_fixed(self, entry: str) -> None:
        class PrivateSerializerObservation(contract.BindingBooleanObservationV1):
            @field_serializer("value")
            def serialize_value(self, value: bool | None) -> bool | None:
                raise ValueError("private serializer: " + _PRIVATE_DIAGNOSTIC_MARKER)

        observation = PrivateSerializerObservation(
            state="OBSERVED", value=True, observer_ref=_PRIVATE_DIAGNOSTIC_MARKER,
        )
        with pytest.raises(ValueError) as error:
            getattr(observation, entry)()
        _assert_private_diagnostics_absent(error.value)
        assert str(error.value) == "offline contract serialization failed"

    @pytest.mark.parametrize("entry", [
        "constructor", "model_python", "model_json", "model_strings",
        "adapter_python", "adapter_json", "revalidated",
    ])
    @pytest.mark.parametrize("nested", [False, True])
    @pytest.mark.parametrize("violation", [
        "private_message", "private_custom_code", "private_error_title", "private_config_title",
    ])
    def test_m2_subclass_diagnostics_use_fixed_messages_codes_and_titles(
        self, entry: str, nested: bool, violation: str,
    ) -> None:
        validator_calls: list[str] = []

        def reject_private_diagnostic(observer: str) -> Any:
            if violation in ("private_message", "private_config_title"):
                raise ValueError("rejected: " + observer)
            if violation == "private_custom_code":
                raise PydanticCustomError(observer, "rejected: " + observer)
            raise ValidationError.from_exception_data(observer, [{
                "type": PydanticCustomError(observer, "rejected: " + observer),
                "loc": (), "input": observer,
            }])

        @model_validator(mode="after")
        def hostile_validator(self: Any) -> Any:
            validator_calls.append("after")
            return reject_private_diagnostic(self.observer_ref)

        @model_validator(mode="before")
        def hostile_strings_validator(cls: Any, value: object) -> Any:
            validator_calls.append("before")
            return reject_private_diagnostic(_PRIVATE_DIAGNOSTIC_MARKER)

        model_namespace: dict[str, Any] = {
            "hostile_validator": hostile_validator,
        }
        if entry == "model_strings":
            model_namespace["hostile_strings_validator"] = hostile_strings_validator
        if violation == "private_config_title":
            model_namespace["model_config"] = ConfigDict(title=_PRIVATE_DIAGNOSTIC_MARKER)
        model: Any = type(_PRIVATE_DIAGNOSTIC_MARKER, (contract.BindingBooleanObservationV1,), model_namespace)
        observation = {"state": "OBSERVED", "value": True, "observer_ref": _PRIVATE_DIAGNOSTIC_MARKER}
        data: Any = observation
        if nested:
            model = type("nested-" + _PRIVATE_DIAGNOSTIC_MARKER, (contract.BindingAssertionFactsV1,), {
                "__annotations__": {"nested_spawn": model},
            })
            data = _metadata().assertions.model_dump(mode="python")
            data["nested_spawn"] = observation
        with pytest.raises(ValidationError) as error:
            if entry == "constructor":
                model(**data)
            elif entry == "model_python":
                model.model_validate(data)
            elif entry == "model_json":
                model.model_validate_json(json.dumps(data))
            elif entry == "model_strings":
                strings = {"state": "OBSERVED", "value": "true", "observer_ref": _PRIVATE_DIAGNOSTIC_MARKER}
                if nested:
                    string_data = {name: {"state": "UNKNOWN"} for name in _ASSERTION_NAMES}
                    string_data["nested_spawn"] = strings
                    model.model_validate_strings(string_data)
                else:
                    model.model_validate_strings(strings)
            elif entry == "adapter_python":
                TypeAdapter(model).validate_python(data)
            elif entry == "adapter_json":
                TypeAdapter(model).validate_json(json.dumps(data))
            else:
                model.model_construct(**data).revalidated()
        _assert_private_diagnostics_absent(error.value)
        assert validator_calls == ["before" if entry == "model_strings" else "after"]
        assert all(detail["type"] in {"value_error", "bool_type", "missing"} for detail in error.value.errors())
        if entry != "model_strings" or not nested:
            assert error.value.error_count() == 1
            assert error.value.errors()[0]["type"] == "value_error"

    @pytest.mark.parametrize("unchecked_extra", [False, True])
    def test_m2_frozen_deletion_diagnostics_exclude_hostile_field_names(self, unchecked_extra: bool) -> None:
        observation = contract.BindingBooleanObservationV1(
            state="OBSERVED", value=True, observer_ref="fixture-observer",
        )
        if unchecked_extra:
            observation = observation.model_copy(update={_PRIVATE_DIAGNOSTIC_MARKER: "synthetic-extra"})
        with pytest.raises(ValidationError) as error:
            delattr(observation, _PRIVATE_DIAGNOSTIC_MARKER)
        _assert_private_diagnostics_absent(error.value)
        assert error.value.error_count() == 1
        assert error.value.errors()[0]["type"] == "frozen_instance"
        assert observation.value is True

    @pytest.mark.parametrize("with_metadata", [False, True])
    @pytest.mark.parametrize("violation", [
        "foreign_observation", "mixed_provisions", "missing_operation_session", "missing_result_session",
        "malformed_operation", "malformed_operation_provision", "malformed_observation",
        "foreign_operation_session", "empty_operations", "operations_list", "pending_request",
        "active_operation", "unterminated_session", "deadline_zero", "deadline_negative",
        "deadline_nan", "deadline_infinite", "deadline_boolean", "time_negative", "time_nan",
        "time_infinite", "time_at_deadline", "time_after_deadline", "result_deadline_mismatch",
        "result_deadline_nonfinite",
    ])
    def test_h1_supplied_cleanup_proof_cannot_publish_false_release(
        self, tmp_path: Path, with_metadata: bool, violation: str,
    ) -> None:
        terminal = _terminal_with_known_cleanup_session()
        report = terminal.d11_report
        assert report is not None and report.observation is not None
        observation = report.observation
        foreign = execution.LightningProvisionRefV1("foreign-run", "foreign-provision-token")
        if violation == "foreign_observation":
            report = replace(report, observation=replace(observation, provision=foreign))
        elif violation == "mixed_provisions":
            operation = execution.LightningOperationRefV1(
                foreign, "foreign-operation-token", execution.D11OperationKind.PROVISION,
            )
            report = replace(report, operations=(*report.operations, operation))
        elif violation == "missing_operation_session":
            assert terminal.session_identity is None
            report = replace(report, observation=replace(observation, resources=()))
        elif violation == "missing_result_session":
            terminal = replace(terminal, session_identity="unobserved-result-session")
        elif violation == "malformed_operation":
            report = replace(report, operations=(_PRIVATE_DIAGNOSTIC_MARKER,))
        elif violation == "malformed_operation_provision":
            report = replace(report, operations=(
                _unchecked_dataclass_update(report.operations[0], provision=_PRIVATE_DIAGNOSTIC_MARKER),
            ))
        elif violation == "malformed_observation":
            report = replace(report, observation=_PRIVATE_DIAGNOSTIC_MARKER)
        elif violation == "foreign_operation_session":
            operation = report.operations[1]
            session = execution.LightningSessionRefV1(foreign, "known-session-token")
            report = replace(report, operations=(report.operations[0],
                _unchecked_dataclass_update(operation, session=session)))
        elif violation == "empty_operations":
            report = replace(report, operations=())
        elif violation == "operations_list":
            report = replace(report, operations=list(report.operations))
        elif violation == "pending_request":
            report = replace(report, observation=replace(observation, request_state="pending"))
        elif violation == "active_operation":
            report = replace(report, observation=replace(observation, active_operations=("active-token",)))
        elif violation == "unterminated_session":
            report = replace(report, observation=replace(observation, resources=(("known-session-token", "active"),)))
        elif violation.startswith("deadline_"):
            value = {"deadline_zero": 0.0, "deadline_negative": -1.0, "deadline_nan": float("nan"),
                     "deadline_infinite": float("inf"), "deadline_boolean": True}[violation]
            report = replace(report, deadline_host_monotonic=value)
        elif violation.startswith("time_"):
            value = {"time_negative": -1.0, "time_nan": float("nan"), "time_infinite": float("inf"),
                     "time_at_deadline": 20.0, "time_after_deadline": 21.0}[violation]
            report = replace(report, observation=_unchecked_dataclass_update(
                observation, observed_at_host_monotonic=value,
            ))
        else:
            terminal = replace(terminal, session_termination_deadline_monotonic=(
                21.0 if violation == "result_deadline_mismatch" else float("nan")
            ))
        terminal = replace(terminal, d11_report=report)
        result, writer = _publish(tmp_path, _success_metadata() if with_metadata else None,
                                  terminal, execution.EffectiveOutcome.SUCCEEDED)
        assert not result.committed
        assert _PRIVATE_DIAGNOSTIC_MARKER not in str(result) and _PRIVATE_DIAGNOSTIC_MARKER not in repr(result)
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("with_metadata", [False, True])
    @pytest.mark.parametrize("anchor", [
        "provision_start_monotonic", "gpu_minute_budget_start_monotonic",
        "session_ttl_start_monotonic", "adapter_start_monotonic",
    ])
    @pytest.mark.parametrize("value", [-1.0, 12.0, float("nan"), float("inf")])
    def test_h1_supplied_start_anchors_must_be_finite_and_precede_observation(
        self, tmp_path: Path, with_metadata: bool, anchor: str, value: float,
    ) -> None:
        terminal = replace(_terminal_with_known_cleanup_session(), **{anchor: value})
        result, writer = _publish(tmp_path, _success_metadata() if with_metadata else None,
                                  terminal, execution.EffectiveOutcome.SUCCEEDED)
        assert not result.committed
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("with_metadata", [False, True])
    @pytest.mark.parametrize("success", [False, True])
    @pytest.mark.parametrize("anchors_supplied", [False, True])
    def test_h1_valid_cleanup_proofs_keep_optional_anchors_and_fixture_observers(
        self, tmp_path: Path, with_metadata: bool, success: bool, anchors_supplied: bool,
    ) -> None:
        terminal = _terminal_with_known_cleanup_session(success=success)
        report = terminal.d11_report
        assert report is not None and report.observation is not None
        report = replace(report, observation=replace(report.observation, source_identity="another-fixture-observer"))
        terminal = replace(terminal, d11_report=report)
        if anchors_supplied:
            terminal = replace(terminal, provision_start_monotonic=1.0,
                gpu_minute_budget_start_monotonic=2.0, session_ttl_start_monotonic=3.0,
                adapter_start_monotonic=4.0, session_termination_deadline_monotonic=20.0)
        metadata = _success_metadata() if success else _metadata()
        result, writer = _publish(tmp_path, metadata if with_metadata else None,
                                  terminal, terminal.effective_outcome)
        assert result.committed
        payload = json.loads(writer.json_path.read_bytes())
        assert payload["status"] == terminal.effective_outcome.value
        assert payload["cleanup_verification"] == "VERIFIED_OFFLINE"
        assert execution.read_committed_pair(writer.json_path, writer.markdown_path).verdict is execution.PairVerdict.AUTHORITATIVE

    @pytest.mark.parametrize("with_metadata", [False, True])
    @pytest.mark.parametrize("identity_field", ["run_id", "evidence_id"])
    @pytest.mark.parametrize("form", ["exact", "prefix", "suffix"])
    @pytest.mark.parametrize("private_token", [
        "provision-token", "operation-token", "known-operation-token",
        "known-session-token", "retained-recovery-token",
    ])
    def test_m3_terminal_private_tokens_never_enter_publication_envelopes_or_errors(
        self, tmp_path: Path, with_metadata: bool, identity_field: str, form: str, private_token: str,
    ) -> None:
        identity = {"exact": private_token, "prefix": "public-" + private_token,
                    "suffix": private_token + "-public"}[form]
        terminal = _terminal_with_known_cleanup_session()
        result, writer = _publish(tmp_path, _success_metadata() if with_metadata else None,
            terminal, execution.EffectiveOutcome.SUCCEEDED, **{identity_field: identity})
        assert not result.committed
        assert private_token not in str(result) and private_token not in repr(result)
        assert private_token not in (result.failure_reason or "")
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("with_metadata", [False, True])
    @pytest.mark.parametrize("identity_field", ["run_id", "evidence_id"])
    @pytest.mark.parametrize("violation", ["foreign_observation", "malformed_observation", "malformed_operation", "malformed_report"])
    def test_m3_malformed_cleanup_does_not_bypass_publication_token_redaction(
        self, tmp_path: Path, with_metadata: bool, identity_field: str, violation: str,
    ) -> None:
        terminal = _terminal_with_known_cleanup_session()
        report = terminal.d11_report
        assert report is not None and report.observation is not None
        token = "provision-token"
        if violation == "foreign_observation":
            foreign = execution.LightningProvisionRefV1("foreign-run", "foreign-provision-token")
            report = replace(report, observation=replace(report.observation, provision=foreign))
        elif violation == "malformed_observation":
            report = replace(report, observation=_PRIVATE_DIAGNOSTIC_MARKER)
        elif violation == "malformed_operation":
            report = replace(report, operations=(*report.operations, _PRIVATE_DIAGNOSTIC_MARKER))
        else:
            terminal = replace(terminal, session_identity="known-session-token")
            report = _PRIVATE_DIAGNOSTIC_MARKER
            token = "known-session-token"
        terminal = replace(terminal, d11_report=report)
        result, writer = _publish(tmp_path, _success_metadata() if with_metadata else None,
            terminal, execution.EffectiveOutcome.SUCCEEDED, **{identity_field: "public-" + token})
        assert not result.committed
        assert token not in str(result) and token not in repr(result)
        assert _PRIVATE_DIAGNOSTIC_MARKER not in str(result) and _PRIVATE_DIAGNOSTIC_MARKER not in repr(result)
        assert not writer.json_path.exists() and not writer.markdown_path.exists()
        assert list(tmp_path.iterdir()) == []


class TestDevelopmentAttemptContracts:
    """Separate development carriers never authorize provider or Studio effects."""

    @staticmethod
    def identity():
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptIdentityV1
        return DevAttemptIdentityV1(
            studio_ref="private-studio", invocation_ref="private-invocation", nonce="a" * 64,
            python_sha256="b" * 64, entry_sha256="c" * 64, config_sha256="d" * 64,
            source_sha256="e" * 64, request_sha256="f" * 64,
        )

    @staticmethod
    def verification():
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptVerificationV1
        return DevAttemptVerificationV1(
            v2_status="SUCCEEDED", raw_status="SUCCEEDED", v2_schema_verified=True,
            raw_schema_verified=True, source_matched=True, correlation_matched=True,
            provenance_matched=True, gate_a_required=True, narration_status="NOT_SUPPLIED",
        )

    def test_control_private_identity_roundtrip_and_redacted_repr(self) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptControlV1
        identity = self.identity()
        control = DevAttemptControlV1(identity=identity, operation="OPEN", sequence=0)
        assert DevAttemptControlV1.model_validate_json(control.canonical_bytes()) == control
        assert "private-studio" not in repr(identity)
        assert "private-invocation" not in str(control)
        assert identity.nonce not in repr(control)

    @pytest.mark.parametrize("operation", ["OPEN", "START", "CANCEL", "STATUS", "INSPECT", "EOF"])
    def test_closed_controls_roundtrip(self, operation: str) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptControlV1
        value = DevAttemptControlV1(identity=self.identity(), operation=operation)
        assert DevAttemptControlV1.model_validate_json(value.model_dump_json()) == value

    @pytest.mark.parametrize("field,value", [
        ("operation", "RUN"), ("sequence", True), ("sequence", -1), ("sequence", 1025),
        ("sequence", "1"), ("private_body", "private-value"),
    ])
    def test_invalid_control_fails_with_redacted_error(self, field: str, value: object) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptControlV1
        payload = dict(identity=self.identity().model_dump(mode="json"), operation="START", sequence=1)
        payload[field] = value
        with pytest.raises(ValueError) as error:
            DevAttemptControlV1.model_validate_json(json.dumps(payload))
        assert "private-studio" not in str(error.value)
        assert "private-value" not in str(error.value)

    @pytest.mark.parametrize("raw", [b'{"private-token":', b'\xffprivate-token', b'[]'])
    def test_protected_malformed_json_ingress(self, raw: bytes) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptControlV1
        with pytest.raises(ValueError) as error:
            DevAttemptControlV1.model_validate_json(raw)
        assert "private-token" not in str(error.value)
        assert "private-token" not in repr(error.value)

    @pytest.mark.parametrize("changes", [
        {"work_seconds": 0.0}, {"cleanup_seconds": float("inf")}, {"poll_seconds": True},
        {"per_attempt_seconds": 120}, {"per_attempt_seconds": 119.0}, {"poll_seconds": 6.0},
    ])
    def test_budget_rejections(self, changes: dict[str, object]) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptBudgetsV1
        payload = dict(work_seconds=300.0, cleanup_seconds=5.0, poll_seconds=0.05)
        payload.update(changes)
        with pytest.raises(ValueError):
            DevAttemptBudgetsV1.model_validate(payload)

    @pytest.mark.parametrize("field", [
        "v2_schema_verified", "raw_schema_verified", "source_matched", "correlation_matched",
        "provenance_matched", "gate_a_required",
    ])
    def test_verification_success_requires_every_received_fact(self, field: str) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptVerificationV1
        payload = self.verification().model_dump(mode="python")
        payload[field] = False
        with pytest.raises(ValueError):
            DevAttemptVerificationV1.model_validate(payload)
        payload[field] = 1
        with pytest.raises(ValueError):
            DevAttemptVerificationV1.model_validate(payload)

    @pytest.mark.parametrize("changes", [
        {"v2_status": "INVALID", "v2_schema_verified": True},
        {"raw_status": "INVALID", "raw_schema_verified": True},
        {"v2_status": "NOT_REACHED", "source_matched": True},
        {"raw_status": "NOT_REACHED", "gate_a_required": True},
        {"failure_codes": ("PRIVATE_MESSAGE",)},
        {"failure_codes": ("RAW_INVALID", "RAW_INVALID")},
    ])
    def test_verification_rejects_contradiction_and_free_text(self, changes: dict[str, object]) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptVerificationV1
        payload = self.verification().model_dump(mode="python")
        payload.update(changes)
        with pytest.raises(ValueError):
            DevAttemptVerificationV1.model_validate(payload)

    def test_received_invalid_and_unreached_observations_remain_distinct(self) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptVerificationV1
        assert DevAttemptVerificationV1().v2_schema_verified is None
        invalid = DevAttemptVerificationV1(
            v2_status="INVALID", v2_schema_verified=False, failure_codes=("V2_INVALID",),
        )
        assert DevAttemptVerificationV1.model_validate_json(invalid.model_dump_json()) == invalid

    @pytest.mark.parametrize("changes", [
        {"live_authorized": True}, {"studio_release_proven": True}, {"studio_release_proven": 0},
        {"adapter_call_count": True}, {"adapter_call_count": 0}, {"adapter_call_count": None},
        {"attempt_count": True}, {"cleanup": "UNKNOWN"}, {"ownership_retained": True},
        {"verification": None}, {"failure_codes": ("CLEANUP_FAILED",)},
    ])
    def test_summary_success_cannot_forge_authority_counts_or_cleanup(self, changes: dict[str, object]) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptSummaryV1
        payload = dict(outcome="SUCCEEDED", cleanup="VERIFIED_OFFLINE", adapter_call_count=1,
                       attempt_count=1, verification=self.verification())
        payload.update(changes)
        with pytest.raises(ValueError):
            DevAttemptSummaryV1.model_validate(payload)

    def test_success_summary_roundtrip_is_metadata_only(self) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptSummaryV1
        value = DevAttemptSummaryV1(outcome="SUCCEEDED", cleanup="VERIFIED_OFFLINE",
            adapter_call_count=1, attempt_count=2, verification=self.verification())
        assert DevAttemptSummaryV1.model_validate_json(value.canonical_bytes()) == value
        assert value.live_authorized is False and value.studio_release_proven is False
        assert "source_image_ref" not in value.model_dump_json()
        assert "private-invocation" not in value.model_dump_json()

    @pytest.mark.parametrize("cleanup", ["UNKNOWN", "FAILED"])
    def test_unknown_cleanup_keeps_ownership(self, cleanup: str) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptSummaryV1
        with pytest.raises(ValueError):
            DevAttemptSummaryV1(outcome="UNKNOWN", cleanup=cleanup)
        value = DevAttemptSummaryV1(outcome="UNKNOWN", cleanup=cleanup,
                                   adapter_call_count=None, ownership_retained=True)
        assert value.attempt_count is None and value.adapter_call_count is None

    @pytest.mark.parametrize("changes", [
        {"adapter_call_count": 1}, {"cleanup": "VERIFIED_OFFLINE"},
        {"verification": {}}, {"ownership_retained": True},
    ])
    def test_denial_has_no_effect_claims(self, changes: dict[str, object]) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptSummaryV1
        with pytest.raises(ValueError):
            DevAttemptSummaryV1.model_validate(dict(outcome="NOT_AUTHORIZED", **changes))

    @pytest.mark.parametrize("payload", [
        {"kind": "READY", "summary": {"outcome": "RUNNING"}},
        {"kind": "VERIFICATION"}, {"kind": "TERMINAL"},
        {"kind": "PROGRESS"}, {"kind": "PROGRESS", "progress": "ADAPTER_STARTED", "attempt_number": 1},
        {"kind": "PROGRESS", "progress": "GENERATION_ATTEMPT_STARTED"},
        {"kind": "READY", "progress": "ADAPTER_STARTED"},
    ])
    def test_frame_shapes_are_closed(self, payload: dict[str, object]) -> None:
        from sketch2life.contracts.schemas.feat018_live_binding import DevAttemptFrameV1
        with pytest.raises(ValueError):
            DevAttemptFrameV1.model_validate(dict(binding_sha256="a" * 64, sequence=0, **payload))
