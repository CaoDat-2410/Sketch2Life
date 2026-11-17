"""Validate the synthetic BE1-01 handoff fixtures through domain/application rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend" / "src"))

from in_memory import InMemoryCoreMutationLedger
from sketch2life.application.services.core_foundation import (
    CommandOutcome,
    CommandStatus,
    CoreFoundationApplication,
)
from sketch2life.contracts.schemas.core_foundation import (
    CoreFailureCodeV1,
    CoreFoundationFixtureV1,
    CoreFoundationManifestV1,
)
from sketch2life.domain.core_foundation import (
    ActiveChildTurn,
    AdultRole,
    CanvasOperation,
    ConsentGrant,
    ConsentState,
    CoreRuleViolation,
    CoreScope,
    DataLifecycleRequest,
    DataRequestState,
    GalleryResource,
    IdempotencyReceipt,
    ManagedChildProfile,
    MembershipState,
    PortfolioEntry,
    PrincipalKind,
    PrincipalSource,
    SessionMembership,
    VerifiedPrincipal,
)

FEATURE_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = FEATURE_ROOT / "fixtures"


def _scope(value: Any) -> CoreScope:
    return CoreScope(**value.model_dump())


def _principal(value: Any) -> VerifiedPrincipal:
    role = AdultRole(value.role) if value.role is not None else None
    return VerifiedPrincipal(
        principal_id=value.principal_id,
        kind=PrincipalKind(value.kind),
        organization_id=value.authorized_scope.organization_id,
        source=PrincipalSource(value.role_source),
        verified=value.verified,
        role=role,
        capabilities=frozenset(value.capabilities),
        authorized_scope=_scope(value.authorized_scope),
        device_id=value.device_id,
    )


def _consent(state: Any, *, child_id: str, organization_id: str) -> ConsentGrant:
    return ConsentGrant(
        child_id=child_id,
        organization_id=organization_id,
        state=ConsentState(state.consent_state),
        verification_state=state.verification_state,
        effective_purposes=frozenset(state.effective_purposes),
    )


def evaluate(case: CoreFoundationFixtureV1) -> tuple[CommandOutcome, bool, int | None]:
    command = case.command
    payload = command.payload
    actor = _principal(command.actor)
    scope = _scope(command.scope)
    service = CoreFoundationApplication()
    ledger = InMemoryCoreMutationLedger()

    if payload.kind == "authorization":
        state = case.state
        if not scope.is_within(_scope(state.resource_scope)):
            from sketch2life.domain.core_foundation import CoreErrorCode

            raise CoreRuleViolation(
                CoreErrorCode.SCOPE_DENIED, "requested scope exceeds loaded resource"
            )
        service.authorize(
            actor,
            scope,
            payload.required_capability,
            frozenset(AdultRole(role) for role in payload.allowed_roles),
            authoritative_scope=_scope(state.resource_scope),
        )
        return CommandOutcome(CommandStatus.ACCEPTED), False, None

    if payload.kind == "profile_consent":
        state = case.state
        profile = ManagedChildProfile(
            child_id=state.profile_child_id,
            organization_id=state.profile_organization_id,
            class_id=state.profile_class_id,
            age_months=state.age_months,
        )
        service.authorize(
            actor,
            scope,
            "profile.read",
            frozenset({AdultRole.TEACHER}),
            authoritative_scope=CoreScope(
                organization_id=state.profile_organization_id,
                class_id=state.profile_class_id,
                child_id=state.profile_child_id,
            ),
        )
        service.validate_profile_purpose(
            profile,
            _consent(
                state,
                child_id=profile.child_id,
                organization_id=profile.organization_id,
            ),
            purpose=payload.purpose,
            organization_id=scope.organization_id,
        )
        return CommandOutcome(CommandStatus.ACCEPTED), False, None

    if payload.kind == "session_admission":
        state = case.state
        profile = ManagedChildProfile(
            child_id=state.profile_child_id,
            organization_id=state.profile_organization_id,
            class_id=state.profile_class_id,
            age_months=state.age_months,
        )
        membership = SessionMembership(
            participant_id=state.participant_id,
            child_id=state.profile_child_id,
            organization_id=state.profile_organization_id,
            class_id=state.membership_class_id,
            session_id=state.membership_session_id,
            state=MembershipState(state.membership_state),
            group_id=state.membership_group_id,
        )
        service.admit_participant(
            principal=actor,
            target=scope,
            profile=profile,
            consent=_consent(
                state,
                child_id=profile.child_id,
                organization_id=profile.organization_id,
            ),
            membership=membership,
            purpose=payload.purpose,
            session_open=state.session_open,
        )
        return CommandOutcome(CommandStatus.ACCEPTED), False, None

    if payload.kind == "turn_canvas":
        state = case.state
        assert command.idempotency_key is not None
        idem_scope = f"canvas:{scope.canvas_id}:{payload.document_epoch}"
        ledger.set_revision(scope.canvas_id or "", state.current_document_revision)
        if state.stored_request_fingerprint is not None:
            ledger.seed_receipt(
                IdempotencyReceipt(
                    scope=idem_scope,
                    key=command.idempotency_key,
                    request_fingerprint=state.stored_request_fingerprint,
                    resulting_revision=state.stored_resulting_revision
                    or state.current_document_revision,
                    operation_id=state.stored_operation_id or "op_fixture_previous",
                )
            )
        membership = SessionMembership(
            participant_id=state.membership_participant_id,
            child_id=state.membership_child_id,
            organization_id=scope.organization_id,
            class_id=scope.class_id or "class_fixture_unknown",
            session_id=state.membership_session_id,
            state=MembershipState(state.membership_state),
            allowed_canvas_ids=frozenset(state.allowed_canvas_ids),
        )
        turn = ActiveChildTurn(
            turn_id=state.active_turn_id,
            device_id=state.turn_device_id,
            organization_id=scope.organization_id,
            session_id=state.turn_session_id,
            canvas_id=state.turn_canvas_id,
            participant_id=state.turn_participant_id,
            state=state.active_turn_state,
            revision=state.turn_revision,
        )
        operation = CanvasOperation(
            operation_id=payload.operation_id,
            turn_id=payload.turn_id,
            participant_id=payload.participant_id,
            session_id=scope.session_id or "",
            canvas_id=scope.canvas_id or "",
            document_epoch=payload.document_epoch,
        )
        outcome = service.apply_canvas_operation(
            principal=actor,
            target=scope,
            membership=membership,
            turn=turn,
            operation=operation,
            expected_revision=payload.expected_document_revision,
            idempotency_scope=idem_scope,
            idempotency_key=command.idempotency_key,
            request_fingerprint=payload.request_fingerprint,
            revision_port=ledger,
            receipt_port=ledger,
            transaction_port=ledger,
        )
        return (
            outcome,
            outcome.status.value == "accepted",
            ledger.current_revision(scope.canvas_id or ""),
        )

    if payload.kind == "gallery_portfolio":
        state = case.state
        if payload.view_kind == "portfolio":
            if (
                payload.child_id is None
                or state.portfolio_entry_id is None
                or state.portfolio_child_id is None
            ):
                raise AssertionError(
                    f"{case.fixture_id}: portfolio fixture is missing its entry/child scope"
                )
            entry = PortfolioEntry(
                entry_id=state.portfolio_entry_id,
                organization_id=state.artifact_organization_id,
                child_id=state.portfolio_child_id,
                source_refs=tuple(state.portfolio_source_refs),
                contribution_child_ids=tuple(state.portfolio_contribution_child_ids),
            )
            outcome = service.read_portfolio(
                principal=actor,
                target=_scope(payload.requested_scope),
                entry=entry,
            )
            return outcome, False, None
        resource = GalleryResource(
            artifact_id=state.artifact_id,
            organization_id=state.artifact_organization_id,
            published=state.published,
            audience_scope=_scope(state.audience_scope),
            contributor_ids=tuple(state.contributor_ids),
        )
        outcome = service.read_gallery(
            principal=actor,
            requested_scope=_scope(payload.requested_scope),
            resource=resource,
        )
        return outcome, False, None

    if payload.kind == "data_lifecycle":
        state = case.state
        request = DataLifecycleRequest(
            request_id=payload.request_id,
            organization_id=scope.organization_id,
            state=DataRequestState(state.request_state),
            unresolved_items=state.unresolved_items,
        )
        outcome = service.complete_data_request(
            principal=actor, target=scope, request=request
        )
        return outcome, False, None

    raise AssertionError(f"unknown core fixture payload: {payload.kind}")


def _verify_unknown_field_probe(
    manifest: CoreFoundationManifestV1,
    cases_by_id: dict[str, CoreFoundationFixtureV1],
) -> None:
    for probe in manifest.invalid_contract_probes:
        case = cases_by_id[probe.source_fixture_id]
        raw = case.model_dump(mode="json")
        raw["command"]["undeclared_role"] = "super_admin"
        try:
            CoreFoundationFixtureV1.model_validate_json(json.dumps(raw))
        except ValidationError as exc:
            error_types = {item["type"] for item in exc.errors()}
            if "extra_forbidden" not in error_types:
                raise AssertionError(
                    f"{probe.probe_id}: unexpected schema rejection: {error_types}"
                ) from exc
            print(f"{probe.probe_id}: PASS expected=FIELD_NOT_ALLOWED")
        else:
            raise AssertionError(
                f"{probe.probe_id}: undeclared command field was accepted"
            )


def main() -> int:
    manifest_path = FIXTURE_ROOT / "manifest-v1.json"
    cases_path = FIXTURE_ROOT / "cases-v1.json"
    manifest = CoreFoundationManifestV1.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    pack_raw = json.loads(cases_path.read_text(encoding="utf-8"))
    raw_cases = pack_raw.get("cases")
    if not isinstance(raw_cases, list):
        raise TypeError("fixture pack must contain a cases array")
    case_bytes = json.dumps(
        {
            "contract_name": "CoreFixturePackV1",
            "contract_version": "1.0",
            "synthetic_only": True,
            "cases": raw_cases,
        }
    )
    # Validate the pack envelope and all closed case schemas in one pass.
    from sketch2life.contracts.schemas.core_foundation import CoreFixturePackV1

    pack = CoreFixturePackV1.model_validate_json(case_bytes)
    cases = list(pack.cases)
    cases_by_id = {case.fixture_id: case for case in cases}
    indexed_ids: set[str] = set()
    passed = 0

    for entry in manifest.entries:
        if entry.path != cases_path.name or entry.index >= len(cases):
            raise AssertionError(
                f"manifest entry has invalid path/index: {entry.fixture_id}"
            )
        case = cases[entry.index]
        if (
            case.fixture_id != entry.fixture_id
            or case.command.payload.kind != entry.kind
        ):
            raise AssertionError(f"manifest does not match fixture {entry.fixture_id}")
        if (
            case.contract_status != entry.contract_status
            or case.source_status_labels != entry.source_status_labels
        ):
            raise AssertionError(
                f"manifest source-status metadata differs for {entry.fixture_id}"
            )
        indexed_ids.add(case.fixture_id)
        if case.expected_result.status != entry.expected_status:
            raise AssertionError(f"manifest status differs for {entry.fixture_id}")
        if case.expected_result.failure_code != entry.expected_failure_code:
            raise AssertionError(
                f"manifest failure code differs for {entry.fixture_id}"
            )

        before_revision = (
            case.state.current_document_revision
            if case.state.kind == "turn_canvas"
            else None
        )
        try:
            outcome, mutated, after_revision = evaluate(case)
            actual_status = outcome.status.value
            actual_failure = None
        except CoreRuleViolation as exc:
            actual_status = "rejected"
            actual_failure = CoreFailureCodeV1(exc.code.value)
            mutated = False
            after_revision = before_revision
            outcome = None

        expected = case.expected_result
        if actual_status != expected.status or actual_failure != expected.failure_code:
            raise AssertionError(
                f"{case.fixture_id}: expected {expected.status}/{expected.failure_code}, "
                f"got {actual_status}/{actual_failure}"
            )
        if mutated != expected.mutates_state:
            raise AssertionError(
                f"{case.fixture_id}: mutation flag differs from expected result"
            )
        actual_revision = outcome.resulting_revision if outcome is not None else None
        if actual_revision != expected.resulting_revision:
            raise AssertionError(
                f"{case.fixture_id}: expected revision {expected.resulting_revision}, got {actual_revision}"
            )
        if outcome is not None and outcome.contributor_ids != expected.contributor_ids:
            raise AssertionError(f"{case.fixture_id}: contributor projection differs")
        if outcome is not None and outcome.source_refs != expected.source_refs:
            raise AssertionError(
                f"{case.fixture_id}: source reference projection differs"
            )
        if case.state.kind == "turn_canvas" and not mutated:
            assert after_revision == before_revision

        passed += 1
        suffix = f"/{actual_failure.value}" if actual_failure else ""
        changed = "mutated" if mutated else "unchanged"
        print(
            f"{case.fixture_id}: PASS expected={actual_status}{suffix} state={changed}"
        )

    if indexed_ids != set(cases_by_id):
        raise AssertionError("manifest does not enumerate every fixture case")
    _verify_unknown_field_probe(manifest, cases_by_id)
    print(
        f"summary: {passed} domain fixtures + {len(manifest.invalid_contract_probes)} contract probes passed"
    )
    print("mode: synthetic fixtures only; no live service, provider, or database")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
