# FEAT-083 source review — 2026-11-23

## Scope reviewed

Reviewed the FEAT-083 working tree against its approved Rev1–Rev5 plans and the canonical FEAT-063 SRS Rev75. The worktree is based on `feature/fe-mobile-remediation` at HEAD `77635688deed0114ac62c28c3f936da62144d59c`; the FEAT-083 changes remain uncommitted.

## Source changes recorded

- Active Qwen inference paths use the pinned `Qwen/Qwen3.8-27B-FP8` checkpoint revision `c3a462cc3d38cf351f3b26cbd763469eeb74ef81` for the drawing and language workloads.
- Parent catalog rotation is represented by additive account-scoped rotation state and idempotency receipt mappings, a migration, application port/repository, API contract, and mobile use-case/controller changes. The configured catalog contains 18 topics and 9 subjects per topic; a randomized order is consumed in three-card batches and reshuffled only after its cycle is exhausted.
- A catalog topic entered as text resolves to its catalog entry. An unknown topic does not receive invented suggestion cards: the UI asks the adult to enter a subject, and the AI validation path checks only the topic/subject relationship.
- Activity and story prompts/parsers require more concrete, age-appropriate, practical actions and narrative progression. The video prompt plan requires the generated motion to remain grounded in the child’s drawing and approved story elements.
- The legacy topic-card generation workload is disabled and excluded from active backend dispatch; rotation is served from the curated catalog. Custom topic validation remains a separate Qwen3.8 workload.
- Rev5 removes the Teacher `/lesson-visuals` route, its `aiWorkflowService` method, page action/preview state, and presentation image-generation controls. The remaining Sketch Deck presentation displays its text and drawing steps and does not imply a generated image.
- Backend FLUX provenance/dispatch, the `lesson.visual.generate` L4 envelope entry, current workload-registry row, and stale route expectations in backend contract catalogs are removed. The old Teacher lesson-visual function and dated FLUX/OpenAPI evidence remain historical; shared request validation rejects that workload if the old function is called directly. The separate Parent sketch-guide workload is unchanged. Teacher SVG illustration generation remains unimplemented.
- Rev4 updates the existing workload-registry contract assertion that still expected Qwen3.5 for drawing. The test was not run.
- FEAT-063 SRS is updated through Rev75; the Data Table Register remains through Rev74 because this removal adds no entities. `docs/context/SRS_AUTHORITY.md` records the updated canonical SRS size and digest.

## Review limits and outstanding verification

- This is a source review only. No tests or typecheck were run.
- The new database migration was not applied; no live database was inspected.
- No Modal deployment, model download, health check, inference, API request, end-to-end workflow, or Android emulator run was performed.
- Consequently, model availability, parser acceptance rate, rotation behavior under concurrency, API behavior, and generated-content quality are not runtime-verified. The SRS remains unsigned.
- Rev5 did not run tests/typecheck, Modal deployment/inference, API/E2E, migration, emulator, or repository-security validation. No runtime proof of route removal or worker fail-closed behavior is claimed.
