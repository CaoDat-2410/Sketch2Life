# ADR-0012: Complete topic-and-age Montessori discovery

- Status: Accepted within owner-approved FEAT-033 revision 6
- Date: 2026-09-30
- Decision owners: project owner and implementation team
- Scope: Session-scoped activity discovery and selection policy; no durable profile storage
- Supersedes: ADR-0011 only for the primary mobile discovery/selection path; legacy contracts/routes remain supported

## Context

The previous mobile flow generated up to three candidates, asked readiness/material/supervision questions, then finalized a second list. Missing readiness or material answers could therefore produce no activity, and V1 recommendation contracts themselves enforce a three-card maximum. The owner explicitly requested a direct full list matching the confirmed drawing topic and child profile interests, with the readiness/intermediate gate removed. Existing P1 V1–V3 contracts may already be consumed and must not be mutated in place.

## Decision

1. Add `POST /v1/sessions/{session_id}/p1/activity-suggestions` with `P1ActivitySuggestionsRequestV1`. The server takes the confirmed topic only from the session's Gate-A record, and age plus adult-confirmed, allowlisted child preference tags from the bounded request. Adult participation is explicit; ages 0–35 months require caregiver participation.
2. Return an additive `ActivityRecommendationSetV2` with every reviewed activity matching the confirmed topic and exact age. Do not cap at three, truncate by relevance, or deduplicate otherwise matching activity records by family. Use pagination only if a transport/performance limit is established and the client can retrieve every result.
3. Confirmed interests/dislikes rank and explain results only within the topic+age set. They never broaden the topic or suppress otherwise matching results. With no confirmed preference match, retain deterministic catalog order.
4. Discovery does not ask for or filter by child readiness, completed history, or material availability. Materials are displayed as preparation information after selection. Preserve reviewed/active catalog status, exact age, Gate-A topic match, authored safety/policy, adult participation, and age-specific supervision constraints. At 0–35 months a caregiver must participate and direct supervision remains mandatory.
5. Add `P1ContextV4` with an explicit `TOPIC_AGE_SAFETY_DISCOVERY_V1` selection policy for the selected activity's P1 filter/compile path. It does not require child readiness, prior-history, or material-availability fields and does not apply those three gates. The server recomputes the candidate against the Gate-A anchor and current reviewed catalog before compiling; it derives supervision/policy facts from the validated session adult/caregiver context. Unsupported safety/policy constraints remain blocking. Gate B continues to lock exact catalog activity/template/objective identity and version.
6. Keep `P1ContextV1`–`P1ContextV3`, `P1ContextOptionsV1`, `P1ContextOptionsRequestV2`, `ActivityContextCandidateSetV2`, and `ActivityRecommendationSetV1` unchanged for compatibility. The normal mobile flow moves to the new additive request and P1ContextV4.
7. Preference text is classified through the existing backend-owned allowlisted classifier. Adults confirm/edit tags before the suggestions request. Raw preference text remains session-only and is excluded from recommendation requests, logs, analytics, and evidence.

## Consequences

- The normal flow no longer has an intermediate readiness/material checklist or a top-three shortlist. The full topic+age result set is available in the chooser.
- Readiness, completed history and material availability cannot cause an otherwise matching discovery set to be empty.
- Catalog safety, policy, age, topic and supervision rules remain server-enforced. Materials remain part of the selected activity plan and are explained before adult approval/start.
- Legacy two-phase clients are not reinterpreted. This migration changes only the approved mobile flow and keeps earlier wire contracts intact.
- Catalog gaps are surfaced by a true topic+age no-match; the system does not invent activities or silently fall back to unrelated subjects.

## Verification

Add contract and regression cases for full-list cardinality (>3), no family suppression, exact-age boundaries, Gate-A topic isolation, preference order without suppression, absent readiness/history/material answers, true no-match, adult/caregiver rules, unknown policy constraints, Gate-B identity/version locks, and V1–V3 compatibility. Run backend unit/contract tests, mobile UI/type checks, security validation, and the feature-approved Android smoke; store sanitized evidence under FEAT-033.
