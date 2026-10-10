# Collaborative creative learning scope analysis and SRS plan

- Status: APPROVED
- Plan revision: 3
- Implementation status: COMPLETE — documentation only; runtime NOT_STARTED in this task
- Date: 2026-10-10

## Goal

Analyze the actual Sketch2Life checkout against the user-supplied Product Scope v1.0 and prepare a Vietnamese reuse assessment, architecture proposal and canonical replacement SRS, preserving the old SRS exactly.

## Scope

- Read project context, source register, relevant ADRs, existing SRS v2.0 and actual source/configuration.
- Distinguish source implementation, fixture/demo, infrastructure scaffolding and future proposals.
- Owner confirmed replacement on 2026-10-10. Preserve an exact backup of the current Master SRS v2.0, then revise that same canonical Markdown file to v3.0 for the new scope. Preserve unrelated pre-existing working-tree changes.
- Cover all M01–M14, source AC01–AC18, age bands, child/teacher/admin roles, collaboration, AI review, video waiting, off-screen activities, portfolio, privacy and recovery.
- Owner confirmed Android tablets/phones and retaining FastAPI + React Native. Keep unanswered product/stack decisions explicitly TBD.
- Record a proposed ADR without freezing runtime contracts or changing accepted architecture.
- Update feature context, evidence and project source/context pointers with additive dated entries.

## Steps

1. Capture source provenance and baseline conflicts.
2. Audit backend/AI and clients/renderer independently.
3. Verify relevant current technology capabilities with official documentation.
4. Write reuse/gap analysis, proposed architecture and revised SRS with traceability.
5. Review source coverage, contradictory assumptions, links and repository validators.
6. Deliver artifacts and remaining decision questions.

## Acceptance criteria

- AC-D01: reuse claims cite actual paths and distinguish implementation from scaffold/fixture.
- AC-D02: all 14 modules and 18 source acceptance criteria map to SRS requirements.
- AC-D03: old/new scope conflicts and migration boundaries are explicit.
- AC-D04: proposed architecture preserves inward dependencies, versioned contracts, original/provenance and backend-only AI/storage.
- AC-D05: full confirmed product scope is retained; proposals and TBD are not silently promoted.
- AC-D06: new SRS includes roles, relationships, logical data, lifecycle, FR/NFR, interface proposals, exceptions and verification.
- AC-D07: plan, approval, context, decisions, evidence and status are complete; checks report actual outcomes.

## Risks and verification

Existing documentation contains historical snapshots and current checkout contains uncommitted changes. Use source inspection as implementation evidence, never describe historical tests as current passes. This is documentation-only: no runtime edits, dependency upgrades, provider calls, cloud provisioning, contract migration, asset application or commit/push.

Run harness and repository security validation where the environment permits. Review Markdown links and traceability; product tests are unnecessary because product code does not change.

The feature-local verification script checks document IDs, paths, own harness, approval revision and exact backup/canonical hashes; it performs no product test or provider call.

## Evidence plan

All sources, source hash, audit findings, external documentation and validation results belong under this feature's evidence directory. Preserve the attachment at its supplied local path and do not publish external originals.

## Acceptance closeout — 2026-10-10

AC-D01–AC-D07 are satisfied for the documentation scope. Source-linked audits, 14-module/18-AC coverage, 66 FRs, explicit migration/authority boundaries, independent review, owner decision records and validation are complete. Global pre-existing harness/security failures are recorded with raw output and limitations; this does not claim repository publication readiness. Runtime work remains NOT_STARTED in this task.

## Revision 3 — system-foundation SRS expansion

Owner requested "làm chi tiết hơn nữa, có thể hỏi 1 vài câu, đây sẽ dùng làm nền tảng cho cả cái hệ thống". Preserve exact current v3.0, then expand canonical SRS to v3.1 with an implementation-oriented requirements layer; no runtime edits or stack freeze.

### Expansion scope and steps

1. Ask high-impact product questions while writing independent detailed sections; preserve unanswered decisions explicitly.
2. Write fully specified use cases across all M01–M14: actors, preconditions, trigger/input, ordered main flow, alternatives/errors, postconditions, invariants and Given/When/Then acceptance.
3. Define logical field dictionaries/relations/constraints and proposed API requests/responses, errors, idempotency, pagination, async completion, realtime operation and reconnection contracts.
4. Define session/group/canvas/turn/approval/content states and concurrency, permissions, revocation, recovery and correction rules.
5. Specify screen responsibilities and age-tool matrix, consent/retention/export/delete/audit workflow, NFR measurement profiles and candidate thresholds with approval labels.
6. Add per-requirement verification mapping, synthetic fixture/scenario catalogue, migration boundaries and decision-to-section gates.
7. Integrate owner answers and independent reviews into the same canonical SRS; verify IDs, links, source coverage, preserved hashes and repository checks.

### Additional acceptance criteria

- AC-D08: every FR001–FR066 has detailed use-case and verification references; confirmed modules/ACs remain covered.
- AC-D09: each detailed use case has actor, preconditions, input/trigger, main/alternative paths, persistent outcome and positive/negative acceptance.
- AC-D10: field/schema/API sections identify types, required/nullable rules, scope, authorization and concurrency/error semantics rather than just entity names.
- AC-D11: shared-device selected contributor is separated from verified security principal; undo/lock/offline/pause/revoke/stale work and durable acknowledgement semantics are explicit.
- AC-D12: no proposed detail, performance number, legal interpretation, tenant/login choice or technology candidate is silently labelled owner-confirmed; owner answers are attributable.
- AC-D13: reader can distinguish baseline requirements, proposed refinements, unresolved decision gates, actual source maturity and future implementation approval.
- AC-D14: canonical v3.1 and consolidated feature artifact are identical; v2.0/v3.0 preservation hashes and internal references verified; final independent QA completed.

Evidence uses this feature's own directories. Independent agents own separate draft Markdown fragments only; root integrates and edits canonical. Product tests, real children/provider calls and deployment remain outside authorization.

## Revision 3 acceptance closeout — 2026-10-10

AC-D01–AC-D14 are satisfied for documentation. Canonical v3.1 has 26 sections, 38 detailed UCs/76 ATs, 35 logical DTOs/66 route contracts, 34 screens, 17 candidate quality targets, 16 fixture families and complete integrated 66-FR trace. Six foundation answers are recorded with prior scope/product choices. Exact v2.0/v3.0 hashes are unchanged and feature consolidated v3.1 equals canonical. Independent review findings and final refinements are corrected; static documentation/own harness/security-content, architecture and documentation diff checks pass. Global pre-existing harness/security findings remain separately documented; no repository publication readiness claim. No runtime/model/device/load/legal verification or full stack freeze occurred.
