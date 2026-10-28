# Parent AI line-sketch SRS reconciliation — 2026-10-28

- Evidence ID: EV-063-17
- Related records: SRS/Data Table Register v2.2-draft; Q146; BR-42/44/46; FR-P-11; FR-AI-15; AC-44/45; AT-18/19; Plan Rev24.
- Type: requirements and source-of-truth reconciliation.
- Authority: owner's 2026-10-28 clarification that the Parent sketch option is an AI-generated visual line-sketch, plus the earlier direct request to add it as optional. Plan Rev24 approves documentation changes only.
- Plan Rev24 SHA-256: `59B5CBAAC46AAD60C482B633C43324D6E509BE940CDF0904E6E961E5F72CFF27`.
- Environment: repository document review only.
- Reviewer: Codex.

## Reconciled baseline

- FEAT-063 remains the source of truth. The full SRS and Data Table Register are now revision 2.2-draft.
- Q146 records the optional Parent AI guide: the adult selects a generic approved topic and simple difficulty, then requests a 3–5-step progressive line-sketch or skips it. Skip, failure, timeout, limit refusal or rejected output does not block drawing/capture.
- The model input excludes child profile, exact age, voice, photo and artwork. Output is private, temporary, provenance-tracked and cleaned up by expiry/lifecycle. It is not attached to the profile or StoryRun and does not use video quota; sketch compute/rate controls are separate.
- Teacher's approved-plan, occurrence-wide AI Sketch Deck remains a main-flow step. Parent Sketch Guide is a separate optional capability.
- Q145's interim text-only interpretation is marked superseded and is not retained as a second Parent starter feature.
- The target design uses the existing AI Job, Core Asset/lineage and AI Policy resource tables; it adds a `PARENT_SKETCH_GUIDE` target and temporary asset expiry behavior, but no new table. The logical target count remains 78 active / 48 legacy / 126 projected physical, pending future schema review and live-database validation.
- FEAT-062's old Q-01–Q-07 SRS body remains replaced by a redirect; its current pointers name FEAT-063 v2.2 and Q146 as answered.

## Static reconciliation performed

The SRS records FR-P-11 and FR-AI-15, updates Parent flow/business rules and AI Job contracts, and adds acceptance/edge cases for generic inputs, output validation, cleanup and non-blocking failure. The Data Table Register uses the same target/lifecycle/resource ownership. ADR-0021, FEAT-063 decision/context/status/source records, FEAT-062 retirement pointers, and the global source register identify the same baseline. The SRS catalogue count is 46 BR, 82 FR, 33 NFR, 45 acceptance criteria and 19 edge scenarios.

## Limits

The SRS and Data Table Register remain drafts without full content sign-off. Exact model/provider/license, numerical compute/rate limits and retention duration remain technical/operational gates. No product source, API implementation, database, model/provider, generated image, benchmark, product test/build or deployment was accessed or changed. Existing diagrams/PDFs remain historical snapshots and were not regenerated.
