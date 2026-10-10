# Feature decisions

## 2026-10-10

- D01: direct user request authorizes analysis and SRS drafting; record documentation-only approval before creating artifacts.
- D02: create a separate SRS variant so the old v2.0 baseline and uncommitted work remain recoverable. Baseline replacement awaits owner clarification.
- D03: source CONFIRMED/PROPOSED/TBD labels retain their meaning; logical schemas, endpoints, numeric targets and technology changes are proposals.
- D04: repository security invariants continue to apply; product differences are recorded rather than hidden by old runtime defaults.
- D05: independent read-only audits cover backend/AI and frontend/renderer. No agent changes runtime files.

## Owner clarification — 2026-10-10

- D06: owner explicitly replaces old scope. Update canonical Master SRS to v3.0; archive exact current v2.0 in this feature before edits, including its existing uncommitted content.
- D07: Android is confirmed; FastAPI and React Native are retained. Library versions, drawing renderer, sync mechanism, other infrastructure and models remain proposed/TBD.
- D08: old runtime policies remain implemented until separately approved migration; document discrepancies prominently rather than claiming replacement requirements already run.

## Owner refinement — 2026-10-10

- D09: Teacher reviews every Sketch suggestion before child access in pilot (OD02 resolved); no preset preapproval assumed.
- D10: shared tablet uses explicit selected active child by turn (OD03 resolved in principle); selected contributor differs from verified security principal. Switching UX, correction and mixed-device scope still need design.
- D11: after permitted video retries fail, Teacher explicitly chooses retry, skip or end (OD01 resolved); generation still waits, no automatic fallback. Retry counts/timeouts remain TBD.

## Documentation closeout — 2026-10-10

- D12: all independent review findings were fixed and final re-review found no actionable issue. Own static/harness/security-content checks and architecture pass; global checks fail on existing FEAT-037/038 and local-output findings, recorded without modifying unrelated work.
- D13: documentation task is DONE; future stack freeze, implementation, models/providers and publication remain separately gated. Do not interpret SRS replacement as an implemented runtime migration.

## Foundation expansion — revision 3, 2026-10-10

- D14: direct request authorizes deeper v3.1 documentation in the same canonical SRS; preserve exact v3.0 first, draft independent fragments, integrate with review.
- D15: owner selects one-school pilot with expansion preparation, teacher-managed child profile + QR/code without personal child login, and school-collected legal-representative consent evidence recorded by authorized Teacher/Admin.
- D16: detailed field/API/state/UI/NFR defaults are proposals unless sourced/owner-confirmed; no full stack freeze or runtime changes. Design for future organization scoping does not assert multi-tenant operation is implemented or required for pilot.
- D17: owner confirms 36–155 completed months inclusive, from the third birthday to before the thirteenth; age/date computation and mixed-age content need fixtures/review.
- D18: owner selects one simultaneous classroom with at most 40 children as pilot target, not a measured capacity result. Device connections and group/queue topology are separate sizing proposals.
- D19: owner chooses default session/artwork retention 90 days after session end; profile/portfolio/audit and copy/backup/provider policies are distinct. Portfolio links cannot silently retain expired raw source.
- D20: cross-section review fixes receipt replay before new-mutation guards, explicit session start and per-participant leave, group observations vs individual judgements, content publication review, and discovery vs execution preparation. Video skip does not replace off-screen when session continues; prohibited inference remains prohibited regardless evidence/readiness.
- D21: revision 3 documentation is DONE; canonical v3.1 and consolidated artifact are identical, exact v2.0/v3.0 preserved, IDs/JSON/links/anchors/full trace and independent review verified. Proposed measurements/contracts and runtime/stack/privacy release gates remain unadopted, with global pre-existing validator failures recorded.
