"""Deterministic synthetic fixture catalogue for BE2-01 Phase A (candidate contracts).

Positive DATA-25 and ProviderCopyLifecycle fixtures are produced by running the fake harness
(fake clock/ids), so they are actual outputs of the code under test. Negative fixtures are
explicit mutations that must be rejected. No real child data, provider output or credential.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path
from typing import Any

from sketch2life.application.ports.ai_jobs import CancellationNotice, Principal
from sketch2life.application.services.ai_jobs import (
    FIXTURE_POLL_POLICY,
    FIXTURE_RETRY_POLICY,
    PUBLIC_MESSAGES,
    CancelJobCommand,
)
from sketch2life.contracts.schemas.ai_jobs import (
    AsyncJobChildEnvelopeV1,
    AsyncJobEnvelopeV1,
    JobStatusMetaV1,
)
from sketch2life.domain.ai_jobs.completion import Moderation
from sketch2life.domain.ai_jobs.model import JobProgress, ProgressKind
from sketch2life.domain.ai_jobs.provider_copy import CopyKind, ProviderCopy
from sketch2life.infrastructure.ai_jobs.harness import (
    ADMIN,
    DEVICE,
    ORG,
    TEACHER,
    FixtureHarness,
    build_fixture_harness,
    request_ref,
)

Json = dict[str, Any]
SCHEMA_VERSION = "0.1-candidate"


def _envelope(h: FixtureHarness, principal: Principal, job_id: str) -> Json:
    status = h.service.get_job_status(principal, job_id)
    assert status.view is not None
    meta = JobStatusMetaV1(
        resource_revision=int(status.view["job_revision"]),  # type: ignore[call-overload]
        poll_after_ms=status.view["poll_after_ms"],  # type: ignore[arg-type]
        projection=str(principal.role),  # type: ignore[arg-type]
    )
    model: AsyncJobEnvelopeV1 | AsyncJobChildEnvelopeV1
    if principal.role.value == "device":
        model = AsyncJobChildEnvelopeV1.model_validate(
            {"correlation_id": "corr_fx_poll", "data": status.view, "meta": meta},
            strict=False,
        )
    else:
        model = AsyncJobEnvelopeV1.model_validate(
            {"correlation_id": "corr_fx_poll", "data": status.view, "meta": meta},
            strict=False,
        )
    return {"etag": status.etag, "body": model.model_dump(mode="json")}


def job_state_examples() -> dict[str, Json]:
    """Run the harness through every DATA-25 state and capture Teacher envelopes."""

    out: dict[str, Json] = {}
    h = build_fixture_harness()
    job = h.service.create_job(h.create(key="idem_fx_states_1")).job_id
    out["queued"] = _envelope(h, TEACHER, job)
    message = h.start_next()
    out["running_unknown_progress"] = _envelope(h, TEACHER, job)
    cap = h.capability(job)
    h.service.report_progress(cap, job, message.attempt_id,
                              JobProgress(ProgressKind.STAGES, None, "sketching"))
    out["running_stages"] = _envelope(h, TEACHER, job)
    h.service.report_progress(cap, job, message.attempt_id,
                              JobProgress(ProgressKind.PERCENTAGE, 40.0, None))
    out["running_percentage"] = _envelope(h, TEACHER, job)
    h.service.accept_completion(cap, h.failure_claim(message))
    out["failed_retryable"] = _envelope(h, TEACHER, job)
    h.clock.advance(milliseconds=FIXTURE_RETRY_POLICY.backoff_base_ms)
    h.service.run_due_retries()
    message = h.start_next()
    # B5 Δ8: the retry attempt needs its own attempt-bound capability.
    h.service.accept_completion(h.capability(job), h.success_claim(message))
    out["succeeded_accepted"] = _envelope(h, TEACHER, job)
    out["succeeded_admin_projection"] = _envelope(h, ADMIN, job)
    out["succeeded_device_projection"] = _envelope(h, DEVICE, job)

    stale = h.service.create_job(
        h.create(key="idem_fx_states_2", ref=request_ref("req_fx_stale"))
    ).job_id
    message = h.start_next()
    h.eligibility.context_revisions["req_fx_stale"] = 2
    h.service.accept_completion(h.capability(stale), h.success_claim(message))
    out["succeeded_stale_context"] = _envelope(h, TEACHER, stale)

    exhausted = h.service.create_job(
        h.create(key="idem_fx_states_3", ref=request_ref("req_fx_exhaust"))
    ).job_id
    message = h.start_next()
    h.service.accept_completion(h.capability(exhausted),
                                h.failure_claim(message, code="PROVIDER_ERROR", retryable=False))
    out["failed_exhausted"] = _envelope(h, TEACHER, exhausted)
    out["failed_exhausted_device_projection"] = _envelope(h, DEVICE, exhausted)

    unsafe = h.service.create_job(
        h.create(key="idem_fx_states_4", ref=request_ref("req_fx_unsafe"))
    ).job_id
    message = h.start_next()
    h.service.accept_completion(h.capability(unsafe),
                                h.success_claim(message, moderation=Moderation.UNSAFE))
    out["blocked_unsafe"] = _envelope(h, TEACHER, unsafe)

    cancelled = h.service.create_job(
        h.create(key="idem_fx_states_5", ref=request_ref("req_fx_cancel"))
    ).job_id
    h.service.cancel_job(CancelJobCommand(TEACHER, "idem_fx_cancel_1", cancelled, 1))
    out["cancelled_by_teacher"] = _envelope(h, TEACHER, cancelled)

    revoked = h.service.create_job(
        h.create(key="idem_fx_states_6", ref=request_ref("req_fx_revoke"),
                 subjects=("child_fx_002",))
    ).job_id
    h.service.apply_cancellation_notice(
        CancellationNotice("notice_fx_001", ORG, "CONSENT_REVOKED", subject_ref="child_fx_002")
    )
    out["cancelled_consent_revoked"] = _envelope(h, TEACHER, revoked)
    return out


def provider_copy_report() -> Json:
    h = build_fixture_harness()
    scope = "job_fx_copy_scope"
    profiles = ["fixture-deletes", "fixture-pending", "fixture-unsupported",
                "fixture-exception", "fixture-unverified"]
    kinds = [CopyKind.INPUT, CopyKind.OUTPUT, CopyKind.JOB, CopyKind.CACHE, CopyKind.OUTPUT]
    for index, (profile, kind) in enumerate(zip(profiles, kinds, strict=True), start=1):
        h.copy_service.register_copy(
            ProviderCopy(f"copy_fx{index:03d}", ORG, scope, kind, profile)
        )
    h.copy_service.cancel_scope(ORG, scope)
    outcomes = h.copy_service.purge_scope(ORG, scope, "purge_fx_001")
    late = h.copy_service.register_copy(
        ProviderCopy("copy_fx_late", ORG, scope, CopyKind.OUTPUT, "fixture-pending")
    )
    return {
        "contract_name": "ProviderCopyLifecycleReport",
        "contract_version": SCHEMA_VERSION,
        "contract_owner": "BE2-14",
        "fake_support_owner": "BE2-01",
        "fixture_marker": True,
        "organization_id": ORG,
        "scope_ref": scope,
        "copies": [
            {
                "copy_id": o.copy_id,
                "kind": o.kind,
                "status": o.status,
                "report_label": o.report_label,
                "receipt_id": o.receipt_id,
                "evidence_kind": o.evidence_kind,
                "reason_code": o.reason_code,
                "actual_deletion_proven": o.actual_deletion_proven,
            }
            for o in outcomes
        ]
        + [
            {
                "copy_id": late.copy_id,
                "kind": str(late.kind),
                "status": str(late.status),
                "report_label": str(late.status),
                "receipt_id": None,
                "evidence_kind": None,
                "reason_code": None,
                "actual_deletion_proven": False,
            }
        ],
    }


def _mut(base: Json, fn: Callable[[Json], None]) -> Json:
    value = copy.deepcopy(base)
    fn(value)
    return value


def _set(path: str, value: Any) -> Callable[[Json], None]:
    def apply(target: Json) -> None:
        *parents, leaf = path.split(".")
        node: Any = target
        for part in parents:
            node = node[int(part)] if isinstance(node, list) else node[part]
        node[leaf] = value

    return apply


def _drop(path: str) -> Callable[[Json], None]:
    def apply(target: Json) -> None:
        *parents, leaf = path.split(".")
        node: Any = target
        for part in parents:
            node = node[part]
        del node[leaf]

    return apply


_HASH = sha256(b"synthetic-review-target").hexdigest()
DATA24_SESSION: Json = {
    "contract_name": "ExactContentReview",
    "contract_version": SCHEMA_VERSION,
    "target_kind": "sketch_proposal",
    "target_id": "proposal_fx_001",
    "target_version": 2,
    "target_hash": _HASH,
    "source_context_revision": 4,
    "decision": "approve",
    "reason": None,
    "review_context": {
        "kind": "session_content",
        "session_id": "session_fx_001",
        "audience_context_revision": 3,
        "consent_revision_refs": [{"subject_ref": "child_fx_001", "revision": 1}],
        "review_purpose": "teaching_delivery",
    },
    "audience_scope": {
        "session_id": "session_fx_001",
        "group_ids": ["group_fx_a"],
        "participant_ids": ["participant_fx_001"],
    },
    "review_dimension": None,
    "expected_review_revision": None,
}
DATA24_LIBRARY: Json = {
    "contract_name": "ExactContentReview",
    "contract_version": SCHEMA_VERSION,
    "target_kind": "knowledge_video",
    "target_id": "video_fx_001",
    "target_version": 1,
    "target_hash": _HASH,
    "source_context_revision": 1,
    "decision": "request_changes",
    "reason": "Narration pace too fast for the youngest age band.",
    "review_context": {
        "kind": "generic_library",
        "content_kind": "knowledge_video",
        "age_policy_ref": "age_policy_fx_v1",
        "content_policy_ref": "content_policy_fx_v1",
        "publication_scope": "school_library",
        "review_purpose": "library_publication",
    },
    "audience_scope": {
        "publication_scope": "school_library",
        "age_policy_ref": "age_policy_fx_v1",
        "purpose_codes": ["purpose_fx_library"],
    },
    "review_dimension": "pedagogical",
    "expected_review_revision": 0,
}

SHAPE_POSITIVE: dict[str, Json] = {
    "DATA-21": {
        "canvas_id": "canvas_fx_001",
        "checkpoint_ref": {"checkpoint_id": "ckpt_fx_001", "document_epoch": 1,
                           "server_sequence": 42, "hash": _HASH},
        "target_scope": {"kind": "individual", "participant_id": "participant_fx_001"},
        "target_region_id": None,
        "requested_level": "hint",
        "child_intent": None,
        "request_reason": "child_request",
        "context_revision": 3,
        "client_request_id": "client_req_fx_001",
    },
    "DATA-22": {
        "assistance_id": "assistance_fx_001",
        "expected_request_revision": 1,
        "input_snapshot_ref": "snapshot_fx_001",
        "context_revision": 3,
        "job_id": "job_fx0001",
        "job_attempt_id": "att_fx0001",
        "contract_version": SCHEMA_VERSION,
        "object_candidates": [{"label": "cat", "confidence": None},
                              {"label": "house", "confidence": 0.62}],
        "uncertainty": "model not calibrated; confidence may be null",
        "evidence_refs": [],
        "provenance": {"adapter": "fake_vision", "fixture": True},
        "moderation_outcome": "passed",
    },
    "DATA-23": {
        "proposal_id": "proposal_fx_001",
        "proposal_version": 1,
        "review_revision": 0,
        "assistance_id": "assistance_fx_001",
        "request_revision": 1,
        "source_snapshot_ref": "snapshot_fx_001",
        "context_revision": 3,
        "assistance_level": "hint",
        "display_mode": "side_reference",
        "overlay_asset_ref": None,
        "text_or_question": "What shape could the roof be?",
        "editable_bounds": None,
        "moderation_state": "passed",
        "pipeline_state": "pending_teacher_review",
        "created_at": "2026-10-14T13:00:00Z",
    },
    "DATA-26": {
        "bundle_id": "bundle_fx_001",
        "bundle_version": 1,
        "organization_id": ORG,
        "session_id": "session_fx_001",
        "audience_context_ref": "audience_fx_001",
        "source_snapshot_refs": ["snapshot_fx_001"],
        "confirmed_topic": "butterflies",
        "knowledge_claims": [{"claim_id": "claim_fx_1", "text": "Butterflies have six legs.",
                              "source_ref": "source_fx_1", "verification_state": "reviewed"}],
        "source_records": [{"source_id": "source_fx_1", "title": "Synthetic insect primer",
                            "locator": "fixture://source_fx_1",
                            "reviewed_version_or_date": "2026-10-14"}],
        "script_sections": [],
        "editorial_revision": 1,
        "editorial_state": "draft",
        "created_by": "teacher_fx_001",
        "created_at": "2026-10-14T13:00:00Z",
        "child_imagined_elements": ["a butterfly that sings"],
        "teacher_corrections": [],
    },
    "DATA-27": {
        "bundle_id": "bundle_fx_001",
        "bundle_version": 1,
        "bundle_hash": _HASH,
        "audience_context_revision": 3,
        "strategy": "reviewed_library",
        "candidate_library_asset_ref": "library_asset_fx_001",
        "requested_profile_ref": None,
    },
    "DATA-28": {
        "action": "skip",
        "reason": "Class time is over.",
        "expected_video_version": 1,
        "expected_job_revision": 7,
        "expected_session_revision": 12,
        "retry_authorization_note": None,
    },
    "DATA-29": {
        "activity_ref": {"activity_id": "activity_fx_001", "version": 1, "hash": _HASH},
        "audience_scope": {"session_id": "session_fx_001", "group_ids": ["group_fx_a"]},
        "teacher_adaptations": None,
        "feasibility_confirmation": None,
    },
    "DATA-33": {
        "action": "publish",
        "record_id": "record_fx_001",
        "record_kind": "learning_content",
        "target_version": 2,
        "reason": None,
        "review_ref": {"safety_review_id": "review_fx_s1", "pedagogical_review_id": "review_fx_p1",
                       "review_policy_version": "review_policy_fx_v1"},
    },
}
SHAPE_NEGATIVE: dict[str, tuple[str, Callable[[Json], None]]] = {
    "DATA-21": ("unknown request_reason", _set("request_reason", "inactivity")),
    "DATA-22": ("fabricated confidence above 1", _set("object_candidates.1.confidence", 1.7)),
    "DATA-23": ("unknown display mode", _set("display_mode", "fullscreen")),
    "DATA-26": ("missing child_imagined_elements separation", _drop("child_imagined_elements")),
    "DATA-27": ("unknown strategy", _set("strategy", "auto_best")),
    "DATA-28": ("empty reason", _set("reason", " ")),
    "DATA-29": ("missing audience_scope", _drop("audience_scope")),
    "DATA-33": ("publish without review_ref", _set("review_ref", None)),
}


def data25_negatives(base: Json) -> dict[str, Json]:
    data = base["body"]["data"]
    return {
        "unknown_progress_with_zero": _mut(data, _set("progress", {"kind": "unknown",
                                                                   "value": 0,
                                                                   "stage_label": None})),
        "percentage_over_100": _mut(data, _set("progress", {"kind": "percentage", "value": 150,
                                                            "stage_label": None})),
        "percentage_null": _mut(data, _set("progress", {"kind": "percentage", "value": None,
                                                        "stage_label": None})),
        "stale_as_state": _mut(data, _set("state", "stale")),
        "naive_timestamp": _mut(data, _set("updated_at", "2026-10-14T13:00:00")),
        "revision_as_string": _mut(data, _set("job_revision", "3")),
        "extra_provider_url": _mut(data, _set("provider_url", "https://provider.invalid/x")),
        "missing_correlation_id": _mut(data, _drop("correlation_id")),
        "succeeded_without_disposition": _mut(data, _set("result_disposition", None)),
        "refs_with_stale_disposition": _mut(data, _set("result_disposition", "stale")),
        "terminal_keeps_polling": _mut(data, _set("poll_after_ms", 2000)),
        "bad_input_hash": _mut(data, _set("request_ref.input_hash", "ABC")),
        "attempt_zero": _mut(data, _set("attempt_number", 0)),
        # Q00 R08: result refs only with succeeded + accepted; no disposition before terminal.
        "queued_with_refs": _mut(data, _queued(disposition="accepted")),
        "queued_refs_without_disposition": _mut(data, _queued(disposition=None)),
        "running_with_disposition": _mut(data, _running_with_disposition),
        "cancelled_with_refs": _mut(data, _cancelled_keeping_refs),
    }


def _queued(*, disposition: str | None) -> Callable[[Json], None]:
    def apply(target: Json) -> None:
        target.update(state="queued", started_at=None, completed_at=None, poll_after_ms=2000,
                      result_disposition=disposition)

    return apply


def _running_with_disposition(target: Json) -> None:
    target.update(state="running", completed_at=None, poll_after_ms=2000, result_refs=[],
                  result_disposition="accepted")


def _cancelled_keeping_refs(target: Json) -> None:
    target.update(state="cancelled", failure={"code": "CANCELLED_BY_TEACHER",
                                              "retryable": False,
                                              "public_message": "Cancelled.",
                                              "attempts_remaining": None})


# Q00 R07: enum fields must reject non-string JSON values without raising.
ENUM_FIELDS = {
    "DATA-21": "request_reason",
    "DATA-23": "display_mode",
    "DATA-27": "strategy",
    "DATA-28": "action",
    "DATA-33": "action",
}
NON_STRING_VALUES: dict[str, Any] = {"list": [], "dict": {}, "null": None, "number": 7}


def shape_type_negatives() -> dict[str, Json]:
    return {
        f"{data_id}__{field}__{label}": {
            "data_id": data_id,
            "reason": f"{field} as {label}",
            "payload": _mut(SHAPE_POSITIVE[data_id], _set(field, value)),
        }
        for data_id, field in ENUM_FIELDS.items()
        for label, value in NON_STRING_VALUES.items()
    }


def build_catalog() -> dict[str, Any]:
    states = job_state_examples()
    report = provider_copy_report()
    data25_positive = {
        name: env["body"]["data"]
        for name, env in states.items()
        if not name.endswith("device_projection")
    }
    child_positive = {
        name: env["body"]["data"]
        for name, env in states.items()
        if name.endswith("device_projection")
    }
    succeeded = states["succeeded_accepted"]
    return {
        "data25/positive": data25_positive,
        "data25/negative": data25_negatives(succeeded),
        "data25_child/positive": child_positive,
        "data25_child/negative": {
            "child_with_result_refs": _mut(
                child_positive["succeeded_device_projection"],
                _set("result_refs", succeeded["body"]["data"]["result_refs"]),
            ),
            "child_with_request_ref": _mut(
                child_positive["succeeded_device_projection"],
                _set("request_ref", succeeded["body"]["data"]["request_ref"]),
            ),
            # Q00 R11: same state/failure/poll rules as the full projection.
            "child_terminal_keeps_polling": _mut(
                child_positive["succeeded_device_projection"], _set("poll_after_ms", 2000)
            ),
            "child_failed_without_failure": _mut(
                child_positive["failed_exhausted_device_projection"], _set("failure", None)
            ),
            "child_succeeded_with_failure": _mut(
                child_positive["succeeded_device_projection"],
                _set("failure", {"code": "PROVIDER_ERROR", "retryable": False,
                                 "public_message": "x"}),
            ),
        },
        "data24/positive": {"session_sketch_approve": DATA24_SESSION,
                            "library_request_changes": DATA24_LIBRARY},
        "data24/negative": {
            "reject_without_reason": _mut(DATA24_SESSION, _set("decision", "reject")),
            "library_without_dimension": _mut(DATA24_LIBRARY, _set("review_dimension", None)),
            "sketch_in_library": _mut(DATA24_LIBRARY, _set("target_kind", "sketch_proposal")),
            "audience_kind_mismatch": _mut(
                DATA24_SESSION, _set("audience_scope", DATA24_LIBRARY["audience_scope"])
            ),
            "audience_session_mismatch": _mut(
                DATA24_SESSION, _set("audience_scope.session_id", "session_fx_999")
            ),
            "child_approve_shortcut": _mut(DATA24_SESSION, _set("approve_all", True)),
            "bad_target_hash": _mut(DATA24_SESSION, _set("target_hash", "not-a-hash")),
        },
        "provider_copy/positive": {"fixture_scope_purge": report},
        "provider_copy/negative": {
            "fixture_labelled_deleted": _mut(report, _set("copies.0.report_label", "deleted")),
            "pending_claims_actual": _mut(report, _set("copies.1.actual_deletion_proven", True)),
            "unmarked_fixture_report": _mut(report, _set("fixture_marker", False)),
            "deleted_without_receipt": _mut(report, _set("copies.0.receipt_id", None)),
        },
        "shapes/positive": SHAPE_POSITIVE,
        "shapes/negative": {
            data_id: {"reason": reason, "payload": _mut(SHAPE_POSITIVE[data_id], fn)}
            for data_id, (reason, fn) in SHAPE_NEGATIVE.items()
        },
        "shapes/negative_types": shape_type_negatives(),
        "policies": {
            FIXTURE_RETRY_POLICY.policy_id: {
                "status": FIXTURE_RETRY_POLICY.status,
                "max_attempts": FIXTURE_RETRY_POLICY.max_attempts,
                "backoff_base_ms": FIXTURE_RETRY_POLICY.backoff_base_ms,
                "backoff_multiplier": FIXTURE_RETRY_POLICY.backoff_multiplier,
                "backoff_max_ms": FIXTURE_RETRY_POLICY.backoff_max_ms,
                "attempt_timeout_ms": FIXTURE_RETRY_POLICY.attempt_timeout_ms,
                "source": "SRS v3.1 VIDEO_RETRY_BUDGET PROPOSED; timeout fixture-only",
            },
            FIXTURE_POLL_POLICY.policy_id: {
                "status": FIXTURE_POLL_POLICY.status,
                "min_interval_ms": FIXTURE_POLL_POLICY.min_interval_ms,
                "max_interval_ms": FIXTURE_POLL_POLICY.max_interval_ms,
                "backoff_step_seconds": FIXTURE_POLL_POLICY.backoff_step_seconds,
                "source": "SRS v3.1 JOB_POLL_MIN_INTERVAL PROPOSED",
            },
        },
        "consumer_examples": {
            "p1_job_poll_sequence": {
                "consumer": "P1 / FE",
                "note": "Actual fake-harness Teacher/Device envelopes; ETag per poll.",
                "sequence": [
                    {"step": name, "etag": env["etag"], "body": env["body"]}
                    for name, env in states.items()
                ],
            },
        },
        "error_catalogue": error_catalogue(),
    }


def error_catalogue() -> Json:
    return {
        "contract_version": SCHEMA_VERSION,
        "http_errors": {
            "UNAUTHENTICATED": 401,
            "MALFORMED_REQUEST": 400,
            "RESOURCE_NOT_FOUND": 404,
            "FORBIDDEN_SCOPE": 403,
            "CONSENT_REQUIRED": 403,
            "IDEMPOTENCY_PAYLOAD_MISMATCH": 409,
            "INVALID_STATE": 409,
            "CONTENT_RECALLED": 409,
            "STALE_CONTEXT": 409,
            "POLICY_UNRESOLVED": 409,
            "STALE_AGGREGATE": 412,
            "PRECONDITION_REQUIRED": 428,
            "BUDGET_EXCEEDED": 429,
        },
        "internal_worker_errors": {"WORKER_CAPABILITY_INVALID": 403, "COMPLETION_CONFLICT": 409},
        "job_failure_codes": dict(sorted(PUBLIC_MESSAGES.items())),
        "completion_reason_codes": [
            "JOB_CANCELLED", "JOB_TERMINAL", "ATTEMPT_SUPERSEDED", "INVALID_STATE",
            "INPUT_MISMATCH", "STALE_CONTEXT", "UNSAFE_CONTENT", "OUTPUT_MALFORMED",
            "MALFORMED_CLAIM",
        ],
        "non_authoritative_completion_reasons": [
            "JOB_CANCELLED", "JOB_TERMINAL", "ATTEMPT_SUPERSEDED", "INVALID_STATE",
            "INPUT_MISMATCH", "MALFORMED_CLAIM",
        ],
        "worker_failure_codes_kept_verbatim": [
            "OUTPUT_MALFORMED", "PROVIDER_ERROR", "PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE",
        ],
        "unknown_worker_failure_code_maps_to": "PROVIDER_ERROR",
        "note": "Public messages are safe text; UI localises by code. No diagnostics exposed.",
    }


def _dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def render_files(catalog: dict[str, Any]) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for group, items in catalog.items():
        if group in {"policies", "consumer_examples"}:
            for name, value in items.items():
                files[f"{group}/{name}.json"] = _dump(value)
        elif group == "error_catalogue":
            files["error_catalogue.json"] = _dump(items)
        else:
            for name, value in items.items():
                files[f"{group}/{name}.json"] = _dump(value)
    return files


def manifest(files: dict[str, bytes]) -> bytes:
    return _dump(
        {
            "feature": "FEAT-044-be2-ai-job-foundation",
            "schema_version": SCHEMA_VERSION,
            "synthetic_only": True,
            "files": {path: sha256(body).hexdigest() for path, body in sorted(files.items())},
        }
    )


def write_fixtures(root: Path) -> dict[str, str]:
    files = render_files(build_catalog())
    for path, body in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    (root / "MANIFEST.json").write_bytes(manifest(files))
    return {path: sha256(body).hexdigest() for path, body in files.items()}


def verify_fixtures(root: Path) -> list[str]:
    """Return drift problems between committed fixture files and regenerated content."""

    expected = render_files(build_catalog())
    problems = []
    for path, body in sorted(expected.items()):
        actual = root / path
        if not actual.exists():
            problems.append(f"missing {path}")
        elif actual.read_bytes() != body:
            problems.append(f"drift {path}")
    manifest_path = root / "MANIFEST.json"
    if not manifest_path.exists() or manifest_path.read_bytes() != manifest(expected):
        problems.append("drift MANIFEST.json")
    return problems
