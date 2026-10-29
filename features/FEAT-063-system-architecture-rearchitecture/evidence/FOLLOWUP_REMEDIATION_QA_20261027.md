# Follow-up remediation QA — 2026-10-27

## Scope

Static consistency review of the FEAT-063 SRS, data-table register, ADR-0021, plan revision 13, approval, context and decisions after owner answers Q127–Q133. This is documentation evidence only; it does not authorize implementation or final diagrams/PDF.

## Reconciled rules

- Q127: the Teacher occurrence claim is consumed permanently after its first playable sample; later quality-regeneration failure never opens a second/recovery run. Pre-claim technical/safety failure does not consume the claim.
- Q128: no refund for any accepted full-video request, including provider/technical/safety failure, cancellation or run deletion. Scene retry is within the accepted request.
- Q129/Q133: every state waiting for adult action, with no active AI job, receives an in-app and best-effort push reminder at 144 hours and closes at 168 hours. `VIDEO_READY` becomes `COMPLETED`; other adult-wait states become `ABANDONED`. Content remains until manual deletion. AI jobs have a separate six-hour deadline.
- Q130: current responsible Teacher assignment is the authorization source. Reassignment transfers run/media access, revokes old access/playback and records metadata audit; active classes require a responsible Teacher. Target-Teacher active-run conflict is a safe 409.
- Q131: browser and mobile push supplement the in-app inbox; browser uses Web Push and Android uses a non-Firebase adapter candidate pending synthetic POC. Payloads carry no child/story/media data.
- Q132: Billing owns grants and the immutable `video_quota_usage` ledger. AI Policy owns only platform GPU/compute resource metering.

## Static consistency checks

- Plan revision 13 and approval revision 13 match SHA-256 `3864CB2AB8B9F80C9180BC73E266B511DA60CF0219E131AA37CEBBCAA85E978C`.
- Table arithmetic is consistent across SRS, register, ADR, context and plan: 86 declared production mappings = 51 retained/refactored + 35 legacy; 51 + 40 new = 91 active; 91 + 35 = 126 physical. Five test fixtures are excluded. The added table rows are Billing quota usage and Notifications push endpoints.
- Product-quota grants/usage have Billing ownership in the canonical owner map, use case, table dictionary and architecture rules; AI Policy no longer owns product quota.
- `run_state` is distinct from durable `job_state`/`job_stage`, including ASR/VLM. Adult-wait has its own `adult_wait_started_at`; polling/heartbeat/push receipt does not reset it. AI-running/reconciliation jobs are not idle-closed.
- The Teacher sample claim, no-refund rule, access transfer, no-default-admin access and media-retention behavior agree across requirements, data invariants and acceptance examples.
- Web/mobile push, Android-provider POC, inbox source-of-truth and Firebase Authentication-only repository boundary agree across SRS, plan, ADR and feature decisions.
- Hard GPU-second request/day caps, an operator circuit breaker, fair owner-scope scheduling, a 45-scene-attempt/request structural bound and 135 attempts/run are documented. Numerical cost caps remain a synthetic-benchmark gate.
- Error mapping includes consistent 403/404 disclosure, `TEACHER_ACTIVE_RUN_CONFLICT`, `TEACHER_ASSIGNMENT_REQUIRED`, `AI_COST_LIMIT_REACHED` and image dimension validation.
- Long-running Modal inference uses persisted FunctionCall references and nonblocking polling/reconciliation; RQ/Temporal comparison is an implementation gate, not an unresolved product choice.
- SRS and data register remain Vietnamese with technical identifiers preserved. No final Mermaid blocks or PDF were created; existing historical diagrams remain unapproved.

## Work not performed

No product tests/builds/benchmarks, database access/migration, provider/payment/Modal call, deployment, real-child data processing, final diagram generation or PDF generation was performed. Both Markdown documents remain drafts awaiting owner review.
