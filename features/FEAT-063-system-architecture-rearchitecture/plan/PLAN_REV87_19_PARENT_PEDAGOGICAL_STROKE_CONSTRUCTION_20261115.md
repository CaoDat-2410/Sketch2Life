# Rev87.19 — Parent pedagogical SVG stroke construction

**Date:** 2026-11-15<br>
**Status:** APPROVED<br>
**SRS authority:** FEAT-063 v2.7-draft, §§1–31; especially §31.17.<br>
**Related as-built evidence:** §32.32 and EV-063-113.<br>
**Request:** Owner says the current strokes do not teach young children clearly and asks to review the stroke implementation.

## Review finding

The successful Rev87.18 API call proves transport, schema, source provenance, and exact path coverage. It does not prove that the output is a child-friendly drawing lesson.

The active Modal worker is explicitly an **existing-source-path sequencer**: its prompt prohibits generating or changing geometry, its JSON requires every catalog path ID exactly once, and `_build_openclipart_source_guide` copies those path geometries unchanged. For the saved 11-path kitten result, the first stage assigns `oc_path_001` and says “Vẽ đường viền con mèo.”; later stages add ears, eyes, nose, mouth, and four fur paths. Thus the full outer contour is introduced first and no source path can be omitted, split into simpler strokes, or redrawn as construction shapes. This is a reveal order for the source illustration, not a construction-first lesson. The weak result is structural; changing only the prompt or stage labels cannot fix it.

## Goal

Create a child-readable 4–8-step drawing guide that starts from simple construction marks, progressively forms the same recognizable subject/pose as the selected source, and can omit or simplify illustrative details. Keep the source color illustration as a distinct reference view. The guide remains a draft until an adult review gate passes.

## Proposed design

1. **Keep source retrieval and provenance.** Continue searching the CC0 catalog on Modal Volume. Validate and retain the selected source asset, revision, hash, and license. The source artwork is a visual reference, not a list of mandatory guide strokes.
2. **Separate two documents.** `ReferenceIllustration` keeps the original color SVG unchanged. A versioned `ConstructionStrokeGuideDraft` contains its own normalized, unfilled guide paths plus ordered steps. Do not equate guide path IDs with source path IDs and do not require full source-path coverage.
3. **Author the construction guide from the reference.** The Modal model receives the selected color illustration and a labeled path/region atlas. It returns a constrained vector draft for that subject, with source-feature/landmark references for traceability. It may use simple circles, ovals, arcs, and open curves; split a source feature into several teachable marks; and omit texture or decorative paths. It must preserve the reference's orientation and defining features so the final guide is recognizably the same subject.
4. **Order by how a child draws.** Steps progress from large construction forms to connected major parts and then a few identifying details. Step 1 must not reveal the complete subject outline. Avoid instructions that merely say “draw the outline” or use adult terms such as “silhouette.” Each step adds a small, meaningful group of marks; completed marks remain visible and current marks animate as a guide.
5. **Use simple Vietnamese copy.** Each instruction describes one visible action in a short sentence, using concrete shape/direction words appropriate to the selected age band. The text must accurately describe the strokes shown in that step.
6. **Keep the current safety boundary.** The guide is a private non-persisted draft. The app does not present it as approved until the existing adult review action is completed. An unavailable or rejected guide remains skippable and cannot block mandatory photo capture.

## Contract and quality gates to implement

- Introduce a new versioned worker/API draft contract; retain the current source-path contract for historical evidence and compatibility until its callers are migrated.
- Keep source identity/provenance on the reference object. Guide strokes have their own IDs, normalized geometry, semantic role, and optional source-feature anchors.
- Hard validation: safe SVG subset only; bounded viewBox, stroke/path count, commands and coordinates; no scripts, external references, fills, or unsupported elements; 4–8 sequential nonempty steps; every guide stroke appears exactly once in the guide sequence; all anchors resolve to the selected source; no dependency on full source-path coverage.
- Pedagogical review: no complete silhouette in the first step; progressive construction rather than source-image reveal; instructions match marks; final pose and identifying features match the reference; age-appropriate amount of detail. The automated gate may reject obviously invalid drafts but cannot replace adult/educator review.
- Keep the existing review-only status, quality-gate logging, and failure-safe optional flow. Do not weaken unrelated safety, age, auth, or API gates.

## Verification plan (requires approval for implementation and one new inference)

1. Add focused worker, backend contract, and mobile renderer tests for separate guide geometry, step ordering, source anchors, simplification/omission, child-readable instructions, malformed geometry, and skip behavior.
2. Run a local synthetic contract/render check against a real source SVG without adding a hardcoded guide fixture to the application catalog.
3. After the owner approves this plan, make at most one fresh Modal inference for a generic topic using the existing source catalog; no child profile, photo, voice, consent, or real personal data. Do not retry a terminal failure.
4. Validate the real response and render every cumulative stage plus the separate color reference. Review whether the guide starts with construction marks and forms the same recognizable animal. Keep the result private/review-only.
5. Exercise the Parent UI renderer with the real response if the Android emulator is available; otherwise report API/renderer coverage separately from device coverage.
6. Update evidence, feature context/status, and SRS §32 only. Do not change target requirements §§1–31 unless a separately approved product decision requires it.

## Acceptance criteria

- [ ] Parent guide is a distinct construction drawing, not merely source artwork paths revealed in order.
- [ ] Step 1 does not reveal the completed outer subject contour; 4–8 ordered steps build large forms, connected parts, then identifying details.
- [ ] The guide may simplify or omit source details while preserving the reference's pose and recognizable defining features.
- [ ] Every step instruction is short, child-readable Vietnamese and corresponds to the visible marks.
- [ ] Hard SVG, source provenance, anchor, age, auth, and adult-review gates pass; malformed drafts fail closed and guide failure remains skippable.
- [ ] One real Modal result passes the API contract and all cumulative stages are rendered/reviewed; no fixture replaces the inference.
- [ ] The Parent UI displays the guide progressively and presents the original color source separately at completion.
- [ ] No child data or video is used; no additional Modal inference is sent after a terminal failure.

## Scope and limits

Potential files: `deployment/modal/srs_v23/language_audio_app.py`, the versioned Modal/BE contracts, `backend/src/sketch2life/domain/svg_engine.py`, `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`, Parent mobile guide domain/renderer/screen, focused tests, and FEAT-063 plan/evidence/context/status/SRS §32.

Owner approved this plan with “ok” on 2026-11-15. Authorized scope: implement the separate source-conditioned construction-guide contract, focused worker/backend/mobile tests, deploy the changed Modal worker to dev if needed for verification, then run at most one fresh synthetic-topic Modal inference. Do not retry a terminal result. No database migration, dataset upload, production publication, Teacher presentation change, video, commit, push, or merge. No child data, profile, image, voice, consent, or real personal data. Do not change target SRS §§1–31; append implementation evidence to §32 after verification.

## Execution outcome addendum — 2026-11-15

- The approved plan content above was executed without changing its acceptance criteria. Its pre-execution approved SHA-256 is recorded in `approvals/TASK_APPROVAL.md` as `569C07B61C6BA73D859C0ADE5AE402232AB3EFADB20F112659C03395DC2D8B3B`; this outcome addendum is post-approval evidence, not a new authorization.
- Implemented the separate construction-draft contract and source provenance, worker prompt/parser/diagnostics, backend validation/response, and Parent mobile progressive renderer; added focused backend, Modal worker, and mobile tests.
- Local focused results: backend 12 passed; Modal worker 25 passed with two asyncio deprecation warnings; mobile 3 passed.
- The single approved real synthetic inference (`con mèo`) failed terminally with `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`. The exact subreason is unknown. Local size-limit and diagnostics were corrected, deployed to Modal `dev`, and the app was stopped; the corrected worker was not reinferred. No SVG was returned/rendered. Therefore the live-generation and visual acceptance criteria above remain unchecked and the plan is **PARTIAL**, not complete.
- Full details: `evidence/EV-063-115_PARENT_CONSTRUCTION_MODAL_TEST_20261115/REPORT.md`. No retry, second inference, child data, video, Android UI, commit, push, or merge occurred.
