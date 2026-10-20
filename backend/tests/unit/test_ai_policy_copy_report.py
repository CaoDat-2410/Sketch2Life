"""Redacted stored-state report, MEMORY/ASSUMED only; provider-kind cases classifiers."""

from dataclasses import replace

import pytest
from pydantic import ValidationError

from sketch2life.application.ai_policy_copy_inventory import ProviderCopyInventoryService
from sketch2life.application.ai_policy_copy_report import project_copy_report
from sketch2life.application.ports.ai_policy_copy_registry import (
    CopyRegistryPage,
    RegisteredProviderCopy,
)
from sketch2life.contracts.schemas.ai_policy_copy import CopyReceiptReference
from sketch2life.contracts.schemas.ai_policy_copy_lifecycle import CopyLifecycleRecord
from sketch2life.contracts.schemas.ai_policy_copy_report import CopyReportItem, CopyReportPage
from sketch2life.domain.ai_policy.model import PolicyError
from tests.ai_policy_copy_inventory_fixtures import (
    COVERAGE,
    SOURCE,
    context,
    read_request,
    registration,
    setup,
)
from tests.unit.test_ai_policy_copy_resolution import reconcile, service_setup
from tests.unit.test_ai_policy_domain import NOW


def register(service, copy_id="copy"):
    return service.register("operator", "school", context(), registration(copy_id=copy_id), SOURCE)


def test_empty_report_never_means_deletion_or_inventory_completeness():
    service, _, store = setup()
    result = service.report("operator", "school", read_request())
    assert result.records == () and result.inventory_coverage == "unknown"
    assert result.overall_deletion == "not_established" and result.revision == 0
    assert not store.scopes


def test_pagination_current_revision_redacted_and_read_only():
    service, _, store = setup()
    for key in ("a", "b", "c"):
        register(service, key)
    first = service.report("operator", "school", read_request(limit=2))
    assert tuple(item.copy_id for item in first.records) == ("a", "b") and first.next_after == "b"
    state = store.scopes["school", "scope"]
    counts = len(state["events"]), len(state["evidence"]), state["revision"]
    last = service.report(
        "operator",
        "school",
        read_request(limit=2, after=first.next_after, expected_revision=first.revision),
    )
    assert tuple(item.copy_id for item in last.records) == ("c",) and last.next_after is None
    assert counts == (len(state["events"]), len(state["evidence"]), state["revision"])
    encoded = first.model_dump_json()
    for private in (
        "original_profile",
        "data_request",
        "authority",
        "attestation_ref",
        "source",
        "reason",
        "purpose",
        "provider_url",
        "expires_at",
    ):
        assert private not in encoded
    assert set(first.records[0].model_dump()) == {
        "copy_id",
        "kind",
        "revision",
        "label",
        "actual_deletion_proven",
        "purge_receipt",
        "purge_evidence_kind",
        "cancel_acknowledgment",
    }


def test_late_quarantine_and_stale_continuation_not_resurrected():
    service, _, _ = setup()
    register(service, "a")
    before = service.report("operator", "school", read_request())
    service.fence("operator", "school", context())
    register(service, "late")
    result = service.report("operator", "school", read_request())
    assert result.scope_purging and all(item.label == "purge_requested" for item in result.records)
    with pytest.raises(PolicyError, match="AI_POLICY_COPY_REGISTRY_STALE"):
        service.report(
            "operator", "school", read_request(after="a", expected_revision=before.revision)
        )


@pytest.mark.parametrize(
    "sources,coverage", [((), "partial"), (("fixture-source",), "reported_complete")]
)
def test_stored_coverage_never_means_fresh_completeness_or_all_provider_deletion(sources, coverage):
    service, boundary, _ = setup()
    boundary.observation_changes = dict(observed_sources=sources)
    service.coverage("operator", "school", context(), expected_revision=0, reference=COVERAGE)
    result = service.report("operator", "school", read_request())
    assert result.inventory_coverage == coverage
    assert result.coverage_semantics == "stored_attestation_not_current_completeness"
    assert result.overall_deletion == "not_established" and not result.records


@pytest.mark.parametrize("operation", ["purge", "cancel"])
def test_reconciled_fixture_purge_and_cancel_remain_distinct_not_actual(operation):
    reconciliation, _, store, envelope = service_setup(operation)
    reconcile(reconciliation, envelope)
    reporter = ProviderCopyInventoryService(store, store.boundary, clock=lambda: NOW)
    result = reporter.report("operator", "school", read_request())
    item = result.records[0]
    assert not item.actual_deletion_proven and result.overall_deletion == "not_established"
    if operation == "purge":
        assert item.label == "fixture_deleted_not_actual" and item.purge_evidence_kind == "fixture"
        assert item.purge_receipt == CopyReceiptReference(ref="fixture-receipt", hash="c" * 64)
        assert item.cancel_acknowledgment == "not_confirmed"
    else:
        assert item.cancel_acknowledgment == "fixture_confirmed_not_actual"
        assert item.label != "deleted" and item.purge_receipt is None


@pytest.mark.parametrize(
    "status,kind,label,actual",
    [
        ("deleted", "provider", "deleted", True),
        ("deleted", "fixture", "fixture_deleted_not_actual", False),
        ("pending", "provider", "pending", False),
        ("unsupported", "provider", "unsupported", False),
        ("exception", "fixture", "exception", False),
    ],
)
def test_synthetic_provider_kind_is_classifier_not_actual_provider_test(
    status, kind, label, actual
):
    original = registration()
    current = CopyLifecycleRecord(
        registration=original,
        revision=1,
        status=status,
        purge_reference=SOURCE,
        purge_evidence_kind=kind,
    )
    page = CopyRegistryPage(1, True, (RegisteredProviderCopy(original, False),), None, None)
    result = project_copy_report("school", read_request(), page, (current,))
    assert result.records[0].label == label and result.records[0].actual_deletion_proven is actual
    assert result.overall_deletion == "not_established"


@pytest.mark.parametrize("principal,org", [("unknown", "school"), ("operator", "other")])
def test_denial_before_inventory_read(principal, org, monkeypatch):
    service, boundary, store = setup()
    boundary.grant_changes = dict(allowed=False)

    def forbidden(*args, **kwargs):
        pytest.fail("unauthorized report read")

    monkeypatch.setattr(store, "transaction", forbidden)
    with pytest.raises(PolicyError):
        service.report(principal, org, read_request())


def test_revocation_during_read_blocks_result(monkeypatch):
    service, boundary, store = setup()
    register(service)
    original = store.get_copy_lifecycle

    def revoke(key):
        result = original(key)
        boundary.grant_changes = dict(allowed=False)
        return result

    monkeypatch.setattr(store, "get_copy_lifecycle", revoke)
    with pytest.raises(PolicyError, match="AI_POLICY_FORBIDDEN"):
        service.report("operator", "school", read_request())


@pytest.mark.parametrize(
    "change",
    [
        {"revision": True},
        {"scope_purging": 1},
        {"next_after": "other"},
    ],
)
def test_native_malformed_page_fails_closed(change):
    current = CopyLifecycleRecord(registration=registration(), revision=0, status="discovered")
    page = CopyRegistryPage(1, False, (RegisteredProviderCopy(registration(), False),), None, None)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REPORT_STORAGE"):
        project_copy_report("school", read_request(), replace(page, **change), (current,))


@pytest.mark.parametrize(
    "change",
    [
        {"registration": registration(scope_ref="other")},
        {"registration": registration(copy_id="other")},
        {"cancel_confirmed": 1},
    ],
)
def test_current_copy_wrong_scope_or_native_flag_fails_closed(change):
    current = CopyLifecycleRecord(registration=registration(), revision=0, status="discovered")
    page = CopyRegistryPage(1, False, (RegisteredProviderCopy(registration(), False),), None, None)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REPORT_STORAGE"):
        project_copy_report("school", read_request(), page, (current.model_copy(update=change),))


def test_request_query_revalidated_before_guard():
    service, boundary, _ = setup()
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REGISTRY_REQUEST"):
        service.report("operator", "school", read_request().model_copy(update={"limit": True}))
    assert not boundary.held


def test_oversized_storage_page_rejected_before_lifecycle_lookups(monkeypatch):
    service, _, store = setup()
    item = register(service)
    oversized = CopyRegistryPage(1, False, (item, item, item), None, None)
    monkeypatch.setattr(store, "page", lambda **kwargs: oversized)

    def forbidden(*args):
        pytest.fail("must bound page before current-state fanout")

    monkeypatch.setattr(store, "get_copy_lifecycle", forbidden)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REPORT_STORAGE"):
        service.report("operator", "school", read_request())


@pytest.mark.parametrize("mutation", ["coverage", "duplicates", "backward", "stale"])
def test_stored_page_binding_order_and_revision_rejected(mutation):
    from sketch2life.contracts.schemas.ai_policy_copy_registry import CopyCoverageObservation

    current = CopyLifecycleRecord(registration=registration(), revision=0, status="discovered")
    registered = RegisteredProviderCopy(registration(), False)
    page = CopyRegistryPage(1, False, (registered,), None, None)
    states, request = (current,), read_request()
    if mutation == "coverage":
        coverage = CopyCoverageObservation(
            organization_id="other",
            scope_ref="scope",
            expected_revision=0,
            registry_revision="fixture-registry",
            attestation_ref=COVERAGE,
            required_sources=("fixture-source",),
            observed_sources=("fixture-source",),
        )
        page = replace(page, coverage=coverage)
    elif mutation == "duplicates":
        page, states = replace(page, records=(registered, registered)), (current, current)
    elif mutation == "backward":
        request = read_request(after="copy", expected_revision=1)
    else:
        request = read_request(expected_revision=2)
    with pytest.raises(PolicyError, match="AI_POLICY_INVALID_COPY_REPORT_STORAGE"):
        project_copy_report("school", request, page, states)


@pytest.mark.parametrize("extra", [{"overall_deletion": "complete"}, {"provider_url": "private"}])
def test_closed_page_cannot_claim_overall_completion_or_add_private_fields(extra):
    with pytest.raises(ValidationError):
        CopyReportPage(
            organization_id="school",
            scope_ref="scope",
            revision=0,
            scope_purging=False,
            records=(),
            next_after=None,
            inventory_coverage="unknown",
            **extra,
        )


def test_item_cannot_promote_fixture_receipt_to_actual_deletion():
    with pytest.raises(ValidationError):
        CopyReportItem(
            copy_id="copy",
            kind="input",
            revision=1,
            label="deleted",
            actual_deletion_proven=True,
            purge_receipt=SOURCE,
            purge_evidence_kind="fixture",
            cancel_acknowledgment="not_confirmed",
        )
