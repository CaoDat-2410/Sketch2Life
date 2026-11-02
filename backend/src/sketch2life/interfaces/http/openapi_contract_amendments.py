"""FE-facing OpenAPI amendments derived from mounted handlers and DTO schemas."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

BE1_EXPLICIT_ERROR_STATUSES = frozenset({"401", "403", "422"})
PORTFOLIO_OPERATION_KEY = (
    "get",
    "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio",
)

RESTORE_CHECKPOINT_OPERATION_KEY = (
    "post",
    "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore",
)
RESTORE_CHECKPOINT_STATUS_CODES = frozenset(
    {"200", "401", "403", "404", "409", "410", "422", "500", "503"}
)
RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS = {
    "200": "Canvas restored from the saved checkpoint.",
    "401": "A valid bearer token is required.",
    "403": "The caller lacks an active Teacher or School Admin assignment for this class.",
    "404": "The session, group, or checkpoint was not found.",
    "409": "Consent is not effective or the canvas revision has changed.",
    "410": "Checkpoint bytes are unavailable or failed integrity validation.",
    "422": "The request does not match the BE1 API contract.",
    "500": "The server could not complete the request.",
    "503": "Production checkpoint storage has not been selected.",
}
RESTORE_CHECKPOINT_ERROR_EXAMPLES: dict[str, dict[str, Any]] = {
    "401": {
        "authenticationRequired": {
            "summary": "Bearer token required",
            "value": {
                "code": "AUTHENTICATION_REQUIRED",
                "message": "A verified bearer token is required",
                "request_id": "req_example_001",
            },
        }
    },
    "403": {
        "classAssignmentRequired": {
            "summary": "Teacher or school-admin assignment required",
            "value": {
                "code": "SCOPE_DENIED",
                "message": "adult assignment does not cover this organization or class",
                "request_id": "req_example_001",
            },
        }
    },
    "404": {
        "checkpointNotFound": {
            "summary": "Checkpoint not found",
            "value": {
                "code": "CHECKPOINT_NOT_FOUND",
                "message": "Checkpoint was not found",
                "request_id": "req_example_001",
            },
        }
    },
    "409": {
        "staleCanvasRevision": {
            "summary": "Canvas revision changed",
            "value": {
                "code": "STALE_CANVAS_REVISION",
                "message": "Canvas changed; reload before restoring",
                "request_id": "req_example_001",
            },
        },
        "consentNotEffective": {
            "summary": "Consent is not effective",
            "value": {
                "code": "CONSENT_NOT_EFFECTIVE",
                "message": (
                    "Consent verification and purpose approval are pending; "
                    "child data is blocked"
                ),
                "request_id": "req_example_001",
            },
        },
    },
    "410": {
        "checkpointUnavailable": {
            "summary": "Checkpoint bytes unavailable",
            "value": {
                "code": "CHECKPOINT_UNAVAILABLE",
                "message": "Checkpoint bytes are unavailable or failed integrity validation",
                "request_id": "req_example_001",
            },
        }
    },
    "422": {
        "invalidRequest": {
            "summary": "Request validation failed",
            "value": {
                "code": "REQUEST_VALIDATION_FAILED",
                "message": "The request does not match the BE1 API contract",
                "request_id": "req_example_001",
            },
        }
    },
    "500": {
        "internalServerError": {
            "summary": "Unexpected server error",
            "value": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "The server could not complete the request",
                "request_id": "req_example_001",
            },
        }
    },
    "503": {
        "checkpointStorageUnavailable": {
            "summary": "Checkpoint storage is not configured",
            "value": {
                "code": "ARTIFACT_PROVIDER_UNCONFIGURED",
                "message": "Production checkpoint storage has not been selected",
                "request_id": "req_example_001",
            },
        }
    },
}
PUBLIC_TAG_RENAMES = {
    "BE1 — Organizations & Classes": "Organizations & Classes",
    "BE1 — Sessions & Devices": "Sessions & Devices",
    "BE1 — Collaborative Canvas": "Collaborative Canvas",
    "BE1 — Records & Gallery": "Records & Gallery",
    "BE1 — Session Artifacts": "Session Artifacts",
    "Demo — Capture & Understanding": "Local — Capture & Understanding",
    "Demo — Guided Session Workflow": "Local — Guided Session",
    "Demo — Renderer Assets": "Local — Renderer Assets",
    "Demo — Story & Video": "Local — Story & Video",
    "Lesson Library — Upload Session Owner": "Lesson Library — Upload Sessions",
    "Parent & School Manager — Group Membership": "Parent — Group Membership",
    "Parent — Invitations & Lesson Library": "Parent — Lesson Library",
    "School Manager — Sharing & Parent Groups": "School Manager — Sharing",
    "Teacher & School Manager — Lesson Library": "Staff — Lesson Library",
    "Teacher — Lesson Authoring": "Teacher — Lesson Authoring",
    "Local Dev — Storage Examples": "Local — Storage Examples",
    "System — Health": "Health",
}

LOCAL_TAG_NOTE = "Available when a local profile and required services are configured."

BINARY_SUCCESS_RESPONSES: dict[tuple[str, str], tuple[str, str]] = {
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref}",
    ): (
        "application/octet-stream",
        "Binary artifact body. The response Content-Type is the stored artifact media type.",
    ),
    ("get", "/v1/renderer/source"): (
        "application/octet-stream",
        "Binary renderer source. The response Content-Type is selected by "
        "the configured renderer resource.",
    ),
    ("get", "/v1/renderer/rig-package"): (
        "application/octet-stream",
        "Binary rig package. The response Content-Type is selected by the configured rig package.",
    ),
    ("get", "/v1/renderer/rig-mask"): (
        "application/octet-stream",
        "Binary rig mask. The response Content-Type is selected by the configured rig resource.",
    ),
    ("get", "/v1/renderer/pixi-asset"): (
        "image/png",
        "PNG image bytes for the configured Pixi asset.",
    ),
}

SYNTHETIC_RESPONSE_EXAMPLES: dict[tuple[str, str], dict[str, Any]] = {
    ("get", "/api/be1/v1/organizations/{organization_id}"): {
        "contract": "Be1OrganizationV1",
        "organization_id": "org-example-001",
        "display_name": "Example School",
    },
    ("get", "/api/be1/v1/organizations/{organization_id}/me"): {
        "contract": "Be1AdultAssignmentsV1",
        "subject": "adult-example-001",
        "organization_id": "org-example-001",
        "assignments": [{"role": "teacher", "class_id": "class-example-001"}],
    },
    ("post", "/api/be1/v1/organizations/{organization_id}/assignments"): {
        "contract": "Be1AdultAssignmentV1",
        "assignment_id": "assignment-example-001",
        "subject": "adult-example-002",
        "role": "teacher",
        "class_id": "class-example-001",
        "active": True,
    },
    (
        "delete",
        "/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}",
    ): {
        "contract": "Be1AdultAssignmentV1",
        "assignment_id": "assignment-example-001",
        "active": False,
    },
    ("get", "/api/be1/v1/organizations/{organization_id}/classes"): {
        "contract": "Be1ClassListV1",
        "items": [
            {
                "class_id": "class-example-001",
                "display_name": "Example Class",
                "state": "active",
            }
        ],
    },
    ("post", "/api/be1/v1/organizations/{organization_id}/classes"): {
        "contract": "Be1ClassV1",
        "class_id": "class-example-001",
        "display_name": "Example Class",
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
    ): {
        "contract": "Be1ManagedProfileListV1",
        "items": [
            {
                "child_id": "child-example-001",
                "class_id": "class-example-001",
                "display_name": "Example Learner",
                "age_months": 60,
            }
        ],
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
    ): {
        "contract": "Be1ManagedProfileV1",
        "child_id": "child-example-001",
        "class_id": "class-example-001",
        "display_name": "Example Learner",
        "age_months": 60,
        "consent_state": "effective",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents",
    ): {
        "contract": "Be1ConsentV1",
        "consent_id": "consent-example-001",
        "child_id": "child-example-001",
        "purpose_ref": "classroom-learning-v1",
        "state": "pending",
        "effective": False,
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents",
    ): {
        "contract": "Be1ConsentListV1",
        "items": [
            {
                "consent_id": "consent-example-001",
                "child_id": "child-example-001",
                "purpose_ref": "classroom-learning-v1",
                "state": "pending",
                "effective": False,
            }
        ],
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke",
    ): {
        "contract": "Be1ConsentV1",
        "consent_id": "consent-example-001",
        "state": "revoked",
        "effective": False,
    },
    ("post", "/api/be1/v1/organizations/{organization_id}/sessions"): {
        "contract": "Be1SessionV1",
        "session_id": "session-example-001",
        "organization_id": "org-example-001",
        "class_id": "class-example-001",
        "state": "configured",
        "revision": 1,
        "active_phase": "preparation",
        "configuration": {"purpose_ref": "classroom-learning-v1"},
        "started_at": None,
        "ended_at": None,
        "retain_until": None,
        "join_code": "123456",
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}",
    ): {
        "contract": "Be1SessionV1",
        "session_id": "session-example-001",
        "organization_id": "org-example-001",
        "class_id": "class-example-001",
        "state": "active",
        "revision": 3,
        "active_phase": "explore_draw",
        "configuration": {"purpose_ref": "classroom-learning-v1"},
        "started_at": "2026-10-31T10:00:00Z",
        "ended_at": None,
        "retain_until": None,
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage",
    ): {
        "contract": "Be1SharedLearningStageV1",
        "session_id": "session-example-001",
        "stage": "explore_draw",
        "stage_revision": 2,
        "lifecycle_state": "active",
        "entered_at": "2026-10-31T10:00:00Z",
        "last_command_id": "session-start-003",
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/roster",
    ): {
        "contract": "Be1SessionRosterV1",
        "session_id": "session-example-001",
        "session_revision": 3,
        "members": [
            {
                "membership_id": "membership-example-001",
                "child_id": "child-example-001",
                "display_name": "Example Learner",
                "group_id": "group-example-001",
                "progress": "in_progress",
                "admitted_at": "2026-10-31T10:00:00Z",
                "device_grant_id": "grant-example-001",
            }
        ],
        "groups": [
            {
                "group_id": "group-example-001",
                "display_name": "Example Group",
                "state": "active",
            }
        ],
        "turns": [
            {
                "turn_id": "turn-example-001",
                "child_id": "child-example-001",
                "group_id": "group-example-001",
                "canvas_id": "canvas-example-001",
                "state": "active",
                "document_epoch": 1,
                "started_at": "2026-10-31T10:00:00Z",
                "ended_at": None,
            }
        ],
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome",
    ): {
        "contract": "Be1SessionOutcomeReadV1",
        "session_id": "session-example-001",
        "lifecycle_state": "completed",
        "outcome": {
            "value": "completed",
            "reason_category": None,
            "teacher_note": None,
            "outcome_refs": ["artifact:artifact-example-001"],
            "stage_revision": 8,
            "created_at": "2026-10-31T10:30:00Z",
        },
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage/advance",
    ): {
        "contract": "Be1SharedLearningStageReceiptV1",
        "session_id": "session-example-001",
        "stage": "sharing",
        "stage_revision": 4,
        "session_revision": 6,
        "command_id": "stage-advance-example-001",
        "saved_drafts": ["draft-example-001"],
        "assistance_disposition": "not_needed",
    },
    **{
        ("post", f"/api/be1/v1/organizations/{{organization_id}}/sessions/{{session_id}}/{action}"):
        {
            "contract": "Be1SessionV1",
            "session_id": "session-example-001",
            "organization_id": "org-example-001",
            "class_id": "class-example-001",
            "state": state,
            "revision": 2,
            "active_phase": "join" if action == "lobby" else "explore_draw",
            "configuration": {"purpose_ref": "classroom-learning-v1"},
            "started_at": "2026-10-31T10:00:00Z" if action == "start" else None,
            "ended_at": "2026-10-31T10:30:00Z" if action == "finish" else None,
            "retain_until": "2027-01-29T10:30:00Z" if action == "finish" else None,
        }
        for action, state in (
            ("lobby", "lobby"),
            ("start", "active"),
            ("pause", "paused"),
            ("resume", "active"),
            ("finish", "completed"),
        )
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/completion",
    ): {
        "contract": "Be1SessionOutcomeReceiptV1",
        "session_id": "session-example-001",
        "lifecycle_state": "completed",
        "outcome": "completed",
        "reason_category": None,
        "teacher_note": None,
        "stage_revision": 8,
        "session_revision": 9,
        "command_id": "completion-example-001",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join",
    ): {
        "contract": "Be1DeviceJoinV1",
        "grant_id": "grant-example-001",
        "state": "pending",
        "session_revision": 2,
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/room-code/rotate",
    ): {
        "contract": "Be1SharedRoomCodeV1",
        "session_id": "session-example-001",
        "room_code": "123456",
        "state": "lobby",
    },
    ("post", "/api/be1/v1/room-code/join"): {
        "contract": "Be1DeviceJoinV1",
        "grant_id": "grant-example-001",
        "state": "pending",
        "session_revision": 2,
    },
    ("post", "/api/be1/v1/device-grants/{grant_id}/join-status"): {
        "contract": "Be1DeviceJoinStatusV1",
        "grant_id": "grant-example-001",
        "state": "admitted",
        "organization_id": "org-example-001",
        "session_id": "session-example-001",
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests",
    ): {
        "contract": "Be1PendingJoinListV1",
        "items": [
            {"grant_id": "grant-example-001", "requested_at": "2026-10-31T10:00:00Z"}
        ],
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/admit",
    ): {
        "contract": "Be1AdmissionV1",
        "membership_id": "membership-example-001",
        "state": "admitted",
        "session_revision": 3,
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests/{grant_id}/revoke",
    ): {
        "contract": "Be1DeviceGrantV1",
        "grant_id": "grant-example-001",
        "state": "revoked",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh",
    ): {
        "contract": "Be1DeviceGrantRefreshV1",
        "grant_id": "grant-example-001",
        "device_key": "synthetic-device-credential-returned-once",
        "state": "admitted",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups",
    ): {
        "contract": "Be1SessionGroupV1",
        "group_id": "group-example-001",
        "display_name": "Example Group",
        "state": "active",
        "session_revision": 4,
    },
    (
        "put",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/members/{child_id}",
    ): {
        "contract": "Be1GroupAssignmentV1",
        "membership_id": "membership-example-001",
        "group_id": "group-example-001",
        "session_revision": 5,
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control",
    ): {
        "contract": "Be1GroupControlV1",
        "group_id": "group-example-001",
        "state": "locked",
        "session_revision": 5,
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/progress",
    ): {
        "contract": "Be1MemberProgressV1",
        "membership_id": "membership-example-001",
        "progress": "in_progress",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/help",
    ): {
        "contract": "Be1HelpRequestV1",
        "membership_id": "membership-example-001",
        "state": "open",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/memberships/{membership_id}/leave",
    ): {
        "contract": "Be1MembershipStateV1",
        "membership_id": "membership-example-001",
        "state": "left",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/turns/{child_id}",
    ): {
        "contract": "Be1ActiveTurnV1",
        "turn_id": "turn-example-001",
        "child_id": "child-example-001",
        "group_id": "group-example-001",
        "state": "active",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations",
    ): {
        "contract": "Be1CanvasOperationReceiptV1",
        "status": "accepted",
        "canvas_id": "canvas-example-001",
        "resulting_revision": 12,
        "operation_id": "operation-example-001",
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/canvas/operations",
    ): {
        "contract": "Be1CanvasSyncV1",
        "canvas_id": "canvas-example-001",
        "document_epoch": 1,
        "current_revision": 12,
        "operations": [
            {
                "operation_id": "operation-example-001",
                "session_id": "session-example-001",
                "canvas_id": "canvas-example-001",
                "turn_id": "turn-example-001",
                "participant_id": "child-example-001",
                "document_epoch": 1,
                "resulting_revision": 12,
                "operation_payload": {},
                "accepted_at": "2026-10-31T10:05:00Z",
            }
        ],
        "next_after_revision": 12,
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints",
    ): {
        "contract": "Be1CanvasCheckpointV1",
        "checkpoint_id": "checkpoint-example-001",
        "canvas_id": "canvas-example-001",
        "document_epoch": 1,
        "document_revision": 12,
        "checksum_sha256": "0" * 64,
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest",
    ): {
        "contract": "Be1CanvasCheckpointV1",
        "checkpoint_id": "checkpoint-example-001",
        "canvas_id": "canvas-example-001",
        "document_epoch": 1,
        "document_revision": 12,
        "checksum_sha256": "0" * 64,
        "snapshot": {},
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore",
    ): {
        "contract": "Be1CanvasRestoreV1",
        "canvas_id": "canvas-example-001",
        "document_epoch": 2,
        "document_revision": 1,
        "snapshot": {},
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect",
    ): {
        "contract": "Be1CanvasReconnectV1",
        "canvas_id": "canvas-example-001",
        "turn_id": "turn-example-001",
        "document_epoch": 1,
        "current_revision": 12,
            "checkpoint": {
                "checkpoint_id": "checkpoint-example-001",
                "document_epoch": 1,
                "document_revision": 10,
                "snapshot": {},
            },
            "operations": [
                {
                    "operation_id": "operation-example-001",
                    "session_id": "session-example-001",
                    "canvas_id": "canvas-example-001",
                    "turn_id": "turn-example-001",
                    "participant_id": "child-example-001",
                    "document_epoch": 1,
                    "resulting_revision": 12,
                    "operation_payload": {},
                    "accepted_at": "2026-10-31T10:05:00Z",
                }
            ],
    },
    ("post", "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts"): {
        "contract": "Be1SessionArtifactV1",
        "artifact_ref": "artifact-example-001",
        "version": 1,
        "sha256": "0" * 64,
        "media_type": "image/png",
        "byte_length": 1024,
    },
    ("post", "/api/be1/v1/organizations/{organization_id}/gallery"): {
        "contract": "Be1GallerySnapshotV1",
        "gallery_id": "gallery-example-001",
        "state": "draft",
        "audience": "class",
        "artifact_ref": "artifact-example-001",
    },
    ("get", "/api/be1/v1/organizations/{organization_id}/gallery"): {
        "contract": "Be1GalleryListV1",
        "items": [
            {
                "gallery_id": "gallery-example-001",
                "artifact_ref": "artifact-example-001",
                "audience": "class",
                "contributors": ["child-example-001"],
                "caption": "Synthetic classroom artwork",
                "annotations": [
                    {
                        "annotation_id": "annotation-example-001",
                        "author_ref": "adult-example-001",
                        "text": "Synthetic note",
                        "created_at": "2026-10-31T10:10:00Z",
                    }
                ],
                "created_at": "2026-10-31T10:00:00Z",
            }
        ],
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/publish",
    ): {
        "contract": "Be1GallerySnapshotV1",
        "gallery_id": "gallery-example-001",
        "state": "published",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/gallery/{gallery_id}/annotations",
    ): {
        "contract": "Be1GalleryAnnotationV1",
        "annotation_id": "annotation-example-001",
        "gallery_id": "gallery-example-001",
    },
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/observations",
    ): {
        "contract": "Be1ObservationV1",
        "observation_id": "observation-example-001",
        "child_id": "child-example-001",
        "kind": "observation",
    },
    ("post", "/api/be1/v1/organizations/{organization_id}/data-requests"): {
        "contract": "Be1DataRequestV1",
        "request_id": "data-request-example-001",
        "state": "requested",
        "completion_claimed": False,
    },
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/data-requests/{request_id}",
    ): {
        "contract": "Be1DataRequestV1",
        "request_id": "data-request-example-001",
        "request_type": "export",
        "target_ref": "child:child-example-001",
        "state": "requested",
        "unresolved_items": 0,
        "completion_claimed": False,
    },
    ("get", "/api/be1/v1/health"): {
        "status": "ok",
        "database": "configured",
        "api": "be1",
    },
    ("post", "/v1/profile/preferences/classify"): {
        "contract_name": "ChildPreferenceClassificationV1",
        "contract_version": "1.0",
        "request_id": "request-example-001",
        "interest_tags": [
            {
                "concept_id": "ANIMAL_BUTTERFLY",
                "label_vi": "Con bướm",
                "confidence": 0.94,
            }
        ],
        "avoid_tags": [],
        "interest_unmapped": False,
        "avoid_unmapped": False,
    },
    (
        "delete",
        "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}",
    ): {
        "contract": "LessonAccessGrantV1",
        "access_grant_id": "grant-example-001",
        "lesson_id": "lesson-example-001",
        "version_id": "version-example-001",
        "audience_kind": "PRINCIPAL",
        "audience_ref": "parent-example-001",
        "capability": "VIEW",
        "state": "REVOKED",
        "granted_by": "teacher-example-001",
        "approved_by": None,
        "approved_at": None,
        "expires_at": None,
        "revoked_at": "2026-10-31T10:00:00Z",
        "revision": 2,
    },
    (
        "post",
        "/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept",
    ): {
        "contract": "LessonAccessGrantV1",
        "access_grant_id": "grant-example-001",
        "lesson_id": "lesson-example-001",
        "version_id": "version-example-001",
        "audience_kind": "PRINCIPAL",
        "audience_ref": "parent-example-001",
        "capability": "VIEW",
        "state": "ACTIVE",
        "granted_by": "teacher-example-001",
        "approved_by": None,
        "approved_at": None,
        "expires_at": None,
        "revoked_at": None,
        "revision": 2,
    },
    (
        "post",
        "/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline",
    ): {
        "contract": "LessonAccessGrantV1",
        "access_grant_id": "grant-example-001",
        "lesson_id": "lesson-example-001",
        "version_id": "version-example-001",
        "audience_kind": "PRINCIPAL",
        "audience_ref": "parent-example-001",
        "capability": "VIEW",
        "state": "DECLINED",
        "granted_by": "teacher-example-001",
        "approved_by": None,
        "approved_at": None,
        "expires_at": None,
        "revoked_at": None,
        "revision": 2,
    },
}

SYNTHETIC_MULTIPART_EXAMPLES: dict[
    tuple[str, str], tuple[str, dict[str, Any], str]
] = {
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts",
    ): (
        "sessionArtifact",
        {
            "file": "synthetic-session-artifact.png",
            "contributor_ids": ["child-example-001"],
        },
        "Select a synthetic image file in Swagger UI. This protected route also "
        "requires an existing session, valid consent, and a bearer token.",
    ),
    ("post", "/v1/sessions/{session_id}/media/audio"): (
        "localSyntheticAudio",
        {"audio": "synthetic-narration.wav"},
        "Select a synthetic WAV file in Swagger UI. The audio bytes are not "
        "embedded in this example; this local route requires a process-local session.",
    ),
    ("post", "/api/dev/v1/storage-examples/lesson-source-documents"): (
        "localSyntheticLessonSource",
        {"file": "synthetic-lesson-source.pdf"},
        "Select a synthetic PDF/DOCX/PPTX file in Swagger UI. The local storage "
        "example depends on the enabled local storage profile.",
    ),
}

NULLABLE_RESPONSE_FIELDS: dict[tuple[str, str], tuple[tuple[str, ...], ...]] = {
    ("get", "/api/be1/v1/organizations/{organization_id}/me"): (
        ("assignments", "*", "class_id"),
    ),
    ("post", "/api/be1/v1/organizations/{organization_id}/assignments"): (
        ("class_id",),
    ),
    ("post", "/api/be1/v1/organizations/{organization_id}/sessions"): (
        ("started_at",),
        ("ended_at",),
        ("retain_until",),
    ),
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}",
    ): (("started_at",), ("ended_at",), ("retain_until",)),
    (
        "get",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome",
    ): (("outcome",),),
    ("get", "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/reconnect"): (
        ("checkpoint",),
    ),
    (
        "delete",
        "/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}",
    ): (("approved_by",), ("approved_at",), ("expires_at",), ("revoked_at",)),
    (
        "post",
        "/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/accept",
    ): (("approved_by",), ("approved_at",), ("expires_at",), ("revoked_at",)),
    (
        "post",
        "/api/lesson-library/v1/me/lesson-invitations/{access_grant_id}/decline",
    ): (("approved_by",), ("approved_at",), ("expires_at",), ("revoked_at",)),
}

CONDITIONALLY_OMITTED_RESPONSE_FIELDS: dict[
    tuple[str, str], tuple[tuple[str, ...], ...]
] = {
    ("post", "/api/be1/v1/device-grants/{grant_id}/join-status"): (
        ("organization_id",),
        ("session_id",),
    ),
    (
        "post",
        "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh",
    ): (("device_key",),),
}

def public_tags(tag_descriptions: Mapping[str, str]) -> list[dict[str, str]]:
    """Use concise domain/role labels and list local-only groups last."""
    tags: list[dict[str, str]] = []
    for source_name, description in tag_descriptions.items():
        name = public_tag_name(source_name)
        if source_name.startswith(("Demo —", "Local Dev —")):
            description = f"{description} {LOCAL_TAG_NOTE}"
        tags.append({"name": name, "description": description})
    return sorted(
        tags,
        key=lambda tag: (tag["name"].startswith("Local —"), tag["name"]),
    )


def public_tag_name(source_name: str) -> str:
    return PUBLIC_TAG_RENAMES.get(source_name, source_name)


def _schema_for_example(value: Any, *, property_name: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "type": "object",
            "required": list(value),
            "properties": {
                key: _schema_for_example(item, property_name=key)
                for key, item in value.items()
            },
        }
    if isinstance(value, list):
        item_schema = _schema_for_example(value[0]) if value else {}
        return {"type": "array", "items": item_schema}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer"}
    if isinstance(value, float):
        return {"type": "number"}
    if value is None:
        schema = {"type": ["string", "null"]}
        if property_name.endswith(("_at", "_until")):
            schema["format"] = "date-time"
        return schema
    schema: dict[str, Any] = {"type": "string"}
    if property_name.endswith(("_at", "_until")):
        schema["format"] = "date-time"
    if property_name == "sha256":
        schema["pattern"] = "^[a-f0-9]{64}$"
    return schema


def _mark_nullable(schema: dict[str, Any], path: Sequence[str]) -> None:
    if not path:
        current = schema.get("type")
        if isinstance(current, list):
            if "null" not in current:
                schema["type"] = [*current, "null"]
        elif isinstance(current, str):
            schema["type"] = [current, "null"]
        return
    segment, *rest = path
    if segment == "*":
        items = schema.get("items", {})
        if isinstance(items, dict):
            _mark_nullable(items, rest)
        return
    properties = schema.get("properties", {})
    child = properties.get(segment) if isinstance(properties, dict) else None
    if isinstance(child, dict):
        _mark_nullable(child, rest)


def _mark_optional(schema: dict[str, Any], path: Sequence[str]) -> None:
    if not path:
        return
    segment, *rest = path
    if segment == "*":
        items = schema.get("items", {})
        if isinstance(items, dict):
            _mark_optional(items, rest)
        return
    if len(path) == 1:
        required = schema.get("required", [])
        if isinstance(required, list) and segment in required:
            required.remove(segment)
        return
    properties = schema.get("properties", {})
    child = properties.get(segment) if isinstance(properties, dict) else None
    if isinstance(child, dict):
        _mark_optional(child, rest)


def _is_opaque_required_object(schema: Mapping[str, Any], components: Mapping[str, Any]) -> bool:
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        resolved = components.get(ref.rsplit("/", 1)[-1], {})
        return _is_opaque_required_object(resolved, components)
    schema_type = schema.get("type")
    if schema_type == "object" and not schema.get("properties"):
        return True
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    if isinstance(properties, Mapping):
        for name, value in properties.items():
            if (
                isinstance(value, Mapping)
                and name in required
                and _is_opaque_required_object(value, components)
            ):
                return True
    for variant in (*schema.get("anyOf", []), *schema.get("oneOf", []), *schema.get("allOf", [])):
        if isinstance(variant, Mapping) and _is_opaque_required_object(variant, components):
            return True
    return False


def _describe_open_objects(
    schema: Mapping[str, Any], components: Mapping[str, Any], visited: set[str] | None = None
) -> None:
    visited = visited or set()
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        name = ref.rsplit("/", 1)[-1]
        if name in visited:
            return
        visited.add(name)
        resolved = components.get(name)
        if isinstance(resolved, dict):
            _describe_open_objects(resolved, components, visited)
        return
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for _name, child in properties.items():
            if not isinstance(child, dict):
                continue
            if child.get("type") == "object" and not child.get("properties"):
                child.setdefault(
                    "description",
                    "Open object: this contract does not define nested fields "
                    "for this operation-specific value.",
                )
            else:
                _describe_open_objects(child, components, visited)
    for variant_key in ("anyOf", "oneOf", "allOf"):
        for variant in schema.get(variant_key, []):
            if isinstance(variant, dict):
                _describe_open_objects(variant, components, visited)


def _sample_from_schema(
    schema: Mapping[str, Any],
    components: Mapping[str, Any],
    *,
    property_name: str = "",
    depth: int = 0,
) -> Any:
    if depth > 10:
        return None
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        return _sample_from_schema(
            components.get(ref.rsplit("/", 1)[-1], {}),
            components,
            property_name=property_name,
            depth=depth + 1,
        )
    for variant_key in ("anyOf", "oneOf", "allOf"):
        variants = schema.get(variant_key)
        if isinstance(variants, list) and variants:
            usable = [
                variant
                for variant in variants
                if isinstance(variant, Mapping)
                and not (
                    "null" in variant.get("type", [])
                    if isinstance(variant.get("type"), list)
                    else variant.get("type") == "null"
                )
            ]
            if variant_key == "allOf":
                merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
                for variant in variants:
                    if isinstance(variant, Mapping):
                        merged["properties"].update(variant.get("properties", {}))
                        merged["required"].extend(variant.get("required", []))
                return _sample_from_schema(
                    merged, components, property_name=property_name, depth=depth + 1
                )
            if usable:
                return _sample_from_schema(
                    usable[0], components, property_name=property_name, depth=depth + 1
                )
    if "default" in schema:
        return deepcopy(schema["default"])
    enum = schema.get("enum")
    if isinstance(enum, list) and enum:
        return deepcopy(enum[0])
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = next((value for value in schema_type if value != "null"), "string")
    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            return {}
        required = set(schema.get("required", []))
        result: dict[str, Any] = {}
        for name, value in properties.items():
            if name not in required and "default" not in value:
                continue
            result[name] = _sample_from_schema(
                value, components, property_name=name, depth=depth + 1
            )
        return result
    if schema_type == "array":
        if schema.get("minItems", 0) > 0:
            item = _sample_from_schema(schema.get("items", {}), components, depth=depth + 1)
            return [item]
        return []
    if schema_type == "boolean":
        return False
    if schema_type == "integer":
        if property_name == "age_months":
            return max(48, int(schema.get("minimum", 0)))
        return max(1, int(schema.get("minimum", 1)))
    if schema_type == "number":
        return max(0.5, float(schema.get("minimum", 0.5)))
    if schema_type == "string":
        field_format = schema.get("format")
        if field_format == "date-time":
            return "2026-10-31T10:00:00Z"
        if field_format == "date":
            return "2026-10-31"
        if field_format == "uuid":
            return "00000000-0000-4000-8000-000000000001"
        if field_format == "email":
            return "teacher@example.test"
        if field_format == "uri":
            return "https://example.test/resource"
        if property_name in {"sha256", "source_hash"}:
            return "0" * 64
        if property_name in {"file_name"}:
            return "synthetic-example.pdf"
        if property_name in {"media_type"}:
            return "application/pdf"
        if property_name in {"display_name", "caption", "teacher_note"}:
            return "Synthetic example"
        if property_name in {"contract", "contract_name"}:
            return str(schema.get("title", "ExampleContractV1"))
        return "example-value"
    return {}


def add_request_examples(openapi_schema: dict[str, Any]) -> int:
    """Add representative examples where the body schema is determinate."""
    components = openapi_schema.get("components", {}).get("schemas", {})
    if not isinstance(components, Mapping):
        return 0
    added = 0
    for _path, path_item in openapi_schema.get("paths", {}).items():
        if not isinstance(path_item, Mapping):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"post", "put", "patch"} or not isinstance(operation, dict):
                continue
            content = operation.get("requestBody", {}).get("content", {})
            media = content.get("application/json") if isinstance(content, Mapping) else None
            if (
                not isinstance(media, dict)
                or media.get("examples")
                or media.get("example") is not None
            ):
                continue
            schema = media.get("schema", {})
            if isinstance(schema, Mapping):
                _describe_open_objects(schema, components)
            if not isinstance(schema, Mapping) or _is_opaque_required_object(schema, components):
                continue
            sample = _sample_from_schema(schema, components)
            if not isinstance(sample, dict):
                continue
            media["examples"] = {
                "syntheticRequest": {
                    "summary": "Request example",
                    "description": (
                        "Schema-shaped sample with fictional values. Replace example IDs and "
                        "references with records valid in your environment; protected routes "
                        "also require a real bearer token. This is not seeded test data."
                    ),
                    "value": sample,
                }
            }
            added += 1
    return added


def add_multipart_examples(openapi_schema: dict[str, Any]) -> int:
    """Document file fields without pretending a filename is the file contents."""
    added = 0
    for operation_key, (example_name, value, description) in SYNTHETIC_MULTIPART_EXAMPLES.items():
        method, path = operation_key
        operation = openapi_schema.get("paths", {}).get(path, {}).get(method)
        if not isinstance(operation, dict):
            continue
        media = (
            operation.get("requestBody", {})
            .get("content", {})
            .get("multipart/form-data")
        )
        if not isinstance(media, dict) or media.get("examples"):
            continue
        media["examples"] = {
            example_name: {
                "summary": "Upload example",
                "description": description,
                "value": deepcopy(value),
            }
        }
        added += 1
    return added


def add_response_examples(openapi_schema: dict[str, Any]) -> int:
    """Publish representative examples and derive response properties from handlers."""
    added = 0
    for operation_key, example in SYNTHETIC_RESPONSE_EXAMPLES.items():
        method, path = operation_key
        operation = openapi_schema.get("paths", {}).get(path, {}).get(method)
        if not isinstance(operation, dict):
            continue
        responses = operation.get("responses", {})
        success_status = next((status for status in responses if str(status).startswith("2")), None)
        if success_status is None:
            continue
        response = responses[success_status]
        media = response.get("content", {}).get("application/json")
        if not isinstance(media, dict):
            continue
        media["schema"] = _schema_for_example(example)
        for field_path in NULLABLE_RESPONSE_FIELDS.get(operation_key, ()):
            _mark_nullable(media["schema"], field_path)
        for field_path in CONDITIONALLY_OMITTED_RESPONSE_FIELDS.get(operation_key, ()):
            _mark_optional(media["schema"], field_path)
        _describe_open_objects(media["schema"], {})
        media["examples"] = {
            "syntheticResponse": {
                "summary": "Response example",
                "description": (
                    "Illustrative values derived from the current handler response shape. "
                    "Identifiers and records are fictional; list contents vary with stored data."
                ),
                "value": deepcopy(example),
            }
        }
        added += 1
    return added


def add_error_examples(openapi_schema: dict[str, Any]) -> int:
    """Add source-backed failure examples for Restore Checkpoint."""
    method, path = RESTORE_CHECKPOINT_OPERATION_KEY
    operation = openapi_schema.get("paths", {}).get(path, {}).get(method)
    if not isinstance(operation, dict):
        return 0
    added = 0
    for status, examples in RESTORE_CHECKPOINT_ERROR_EXAMPLES.items():
        response = operation.get("responses", {}).get(status)
        media = (
            response.get("content", {}).get("application/json")
            if isinstance(response, dict)
            else None
        )
        if not isinstance(media, dict):
            continue
        media["examples"] = deepcopy(examples)
        added += len(examples)
    return added

def published_responses(
    operation_key: tuple[str, str], responses: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Any], ...]:
    """Publish concise common errors; keep known Restore Checkpoint failures explicit."""
    binary_override = BINARY_SUCCESS_RESPONSES.get(operation_key)
    if operation_key == RESTORE_CHECKPOINT_OPERATION_KEY:
        rows: list[dict[str, Any]] = []
        for source in responses:
            status = str(source["status"])
            if status not in RESTORE_CHECKPOINT_STATUS_CODES:
                continue
            row = dict(source)
            row["description"] = RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS[status]
            rows.append(row)
        return tuple(rows)
    if not operation_key[1].startswith("/api/be1/v1/"):
        published = []
        for source in responses:
            row = dict(source)
            if binary_override and str(row["status"]).startswith("2"):
                row["media_type"] = binary_override[0]
                row["schema_name"] = "binary"
                row["description"] = binary_override[1]
            published.append(row)
        return tuple(published)

    published: list[dict[str, Any]] = []
    grouped_statuses: list[str] = []
    grouped_schema = "Be1Error"
    for source in responses:
        row = dict(source)
        status = str(row["status"])
        if binary_override and status.startswith("2"):
            row["media_type"] = binary_override[0]
            row["schema_name"] = "binary"
            row["description"] = binary_override[1]
        if operation_key == PORTFOLIO_OPERATION_KEY and status == "200":
            # The mounted handler currently has no success path; it returns 409 while
            # the approved portfolio-purpose verifier is unavailable.
            continue
        if operation_key == PORTFOLIO_OPERATION_KEY and status == "409":
            published.append(row)
            continue
        if status in BE1_EXPLICIT_ERROR_STATUSES:
            published.append(row)
        elif status[:1] in {"4", "5"}:
            grouped_statuses.append(status)
            if row.get("schema_name"):
                grouped_schema = str(row["schema_name"])
        else:
            published.append(row)

    if grouped_statuses:
        status_list = ", ".join(sorted(grouped_statuses, key=int))
        published.append(
            {
                "status": "default",
                "description": (
                    "Other documented BE1 failures may use HTTP "
                    f"{status_list}; response body follows `{grouped_schema}`."
                ),
                "media_type": "application/json",
                "schema_name": grouped_schema,
            }
        )
    return tuple(published)


__all__ = [
    "BE1_EXPLICIT_ERROR_STATUSES",
    "add_error_examples",
    "add_request_examples",
    "add_multipart_examples",
    "add_response_examples",
    "public_tag_name",
    "public_tags",
    "published_responses",
]
