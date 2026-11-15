# Plan Rev83.4 — M1/M2 SVG catalog and guide authoring implementation

**Feature:** FEAT-063 — Whole-repository architecture redesign<br>
**Date:** 2026-11-13<br>
**Lifecycle:** APPROVED for source implementation in the exact manifest below.<br>
**Parent plan:** `PLAN_REV83_SVG_ENGINE_AND_PARENT_TEACHER_COMPLETION_20261112.md` (Rev83.3).<br>
**Requirements baseline:** FEAT-063 v2.7-draft SRS Rev67, SHA-256 `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`; unsigned.<br>
**Owner decision:** “Approve these defaults and M1/M2” (2026-11-13).

## 1. Purpose and boundary

Implement only M1 (safe SVG catalog and deterministic renderer) and M2 (progressive guide playback plus manual Teacher guide authoring) from Rev83.3. Preserve existing Parent/Teacher workflows and use real authenticated APIs and persisted revisions. No fixture, canned response, or generated sample may drive a product workflow or be represented as a curated catalog item.

This amendment supersedes Rev83.3's “awaits M0” wording only for M1/M2. M3-A/M3-B, SVG AI activation, Modal calls/deployments/warmups, Parent/Teacher full E2E, video, FLUX retirement, and all other source changes remain separately gated. Do not call any AI provider.

## 2. Approved M0 decisions carried into M1/M2

- Progressive guide contains 4–8 stages.
- A candidate needs at least four independently drawable, safely canonicalized paths before manual grouping. This structural fact does not imply teaching quality.
- Educator review binds to the exact source hash/revision. Platform Admin curator authorization is a separate decision before the source can be automatically grouped or shown as a platform-approved catalog item.
- Guide edits are copy-on-write immutable revisions. Undo/Redo remains local editor state. Autosave debounce is 1.5 seconds. Every save carries the expected revision; a `409` preserves the local buffer and offers reload, resolve, or separate draft.
- Pilot renderer targets: sustained ≥30 FPS; p95 first visible render ≤500 ms after decoded data is available; p95 step transition ≤150 ms; renderer memory growth ≤64 MiB. Results must later name the selected low-end Android emulator and supported Teacher browser. These are acceptance targets, not measured results.
- Three SVG AI capability flags remain OFF by default. This scope does not wire, invoke, deploy, warm, or enable them. A disabled AI capability must make zero Modal dispatches; catalog/manual paths remain available.
- Later M3-B quality threshold: 100% hard safety/schema/render gates and ≥80% of all cases scored ≥4/5 on both recognizability and teachability by two educators; a ≥2-point reviewer disagreement requires a third reviewer. No M3-B run is authorized here.

## 3. M1/M2 implementation decisions

1. Rebase this implementation checkout's canonical FEAT-063 SRS and authority pointer from Rev60 to Rev67 before source changes. Add SRS Rev68 as an unsigned technical amendment recording the approved M0 defaults and the M1/M2 implementation boundary; do not claim formal SRS sign-off.
2. Canonical source SVG is sanitized and normalized by the backend. Clients receive structured, bounded path records and render with native SVG elements; they do not inject server strings as HTML or fetch remote SVG resources.
3. Catalog eligibility is fail-closed. Only entries with required provenance, clean sanitation, exact-revision educator approval, and required curator decision are visible to the corresponding audience. No fixture SVG is promoted. If no reviewed catalog entry exists, Parent/Teacher receive a clear empty/unavailable state.
4. A safe source may be used for manual Teacher authoring even when it is not eligible for automatic grouping, subject to organization scope and explicit Teacher review. `STATIC_ONLY`, `REQUIRES_MANUAL_AUTHORING`, `STROKE_READY`, and `REJECTED` have separate behavior.
5. Persist guide and presentation changes as immutable lesson versions using the existing `lesson.library_versions` JSONB content and structured hash where the crosswalk confirms it is sufficient. Do not add a table for guide revisions if this versioned record supports the required copy-on-write semantics.
6. Add a Core SVG catalog registry/review persistence migration only for the demonstrated gap: current Core asset metadata cannot express platform-owned catalog scope, source license/provenance, deterministic readiness facts, educator review, or curator authorization. Keep the SVG object's canonical bytes under Core Asset/object-storage ownership; the catalog row references its asset version/hash.
7. Do not add curated visual files in this implementation amendment. Catalog import/review must support real, provenance-bearing source files; usable items remain unavailable until the separately required source/educator/curator review is recorded. Existing fixture, generated Pixi, icon, and UI SVG files are not catalog sources.
8. Manual editor is geometry-preserving: reorder stages; edit Vietnamese instructions and part labels; assign existing path IDs; merge/split semantic parts by reassigning existing IDs; preview. It cannot create, delete, or alter path geometry.
9. Parent playback and Teacher preview use the same versioned guide contract and deterministic renderer. Dashed guidance and solid draw-on progress are separate layers; stage navigation does not mutate canonical content.
10. Do not change Docker, seeds, Modal workloads, FLUX, video, Firebase, or unrelated Parent/Teacher screens except the precise SVG catalog/playback/editor integration in the manifest.

## 4. Exact source and documentation manifest

### Required before source implementation

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `docs/context/SRS_AUTHORITY.md`
- `docs/adr/ADR-0024-svg-catalog-and-manual-guide-revisions.md` (new)
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/REV68_SVG_CATALOG_PERSISTENCE_CROSSWALK.md` (new)
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV83_4_M1_M2_APPROVED_IMPLEMENTATION_20261113.md` (this file)
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-93_SVG_ENGINE_M1_M2_20261113/IMPLEMENTATION_REPORT.md` (new; implementation record only, no test/pass claim)

### Backend M1/M2

- `backend/src/sketch2life/domain/svg_engine.py` (new)
- `backend/src/sketch2life/contracts/schemas/svg_engine.py` (new)
- `backend/src/sketch2life/contracts/schemas/lesson_library.py`
- `backend/src/sketch2life/application/ports/svg_catalog.py` (new)
- `backend/src/sketch2life/application/services/svg_catalog.py` (new)
- `backend/src/sketch2life/domain/lesson_library/model.py`
- `backend/src/sketch2life/infrastructure/svg/__init__.py` (new)
- `backend/src/sketch2life/infrastructure/svg/sanitizer.py` (new)
- `backend/src/sketch2life/infrastructure/svg/renderer.py` (new)
- `backend/src/sketch2life/infrastructure/catalog/svg_assets.py` (new)
- `backend/src/sketch2life/infrastructure/persistence/svg_catalog_tables.py` (new)
- `backend/src/sketch2life/infrastructure/persistence/core_models.py`
- `backend/src/sketch2life/infrastructure/lesson_library/service.py`
- `backend/src/sketch2life/interfaces/http/routers/svg_catalog.py` (new)
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/interfaces/http/openapi_contract.py`
- `backend/alembic/versions/20261113_svg_catalog_review.py` (new; only the crosswalk's additive Core platform-asset/catalog/review delta)

### Parent Android M2 playback

- `apps/ui-mobile/src/parent/domain/svgGuide.ts` (new)
- `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts`
- `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts`
- `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts`
- `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx` (new)
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`

### Teacher Web M2 editor and renderer

- `apps/teacher-ui/src/App.tsx`
- `apps/teacher-ui/src/components/TeacherLayout.tsx`
- `apps/teacher-ui/src/domain/svgGuide.ts` (new)
- `apps/teacher-ui/src/services/svgCatalogService.ts` (new)
- `apps/teacher-ui/src/components/SvgGuideRenderer.tsx` (new)
- `apps/teacher-ui/src/components/TeacherSvgGuideEditor.tsx` (new)
- `apps/teacher-ui/src/pages/TeacherSvgGuideEditorPage.tsx` (new)
- `apps/teacher-ui/src/components/TeacherDeckPresentation.tsx`

### Explicit exclusions

No other paths are authorized. In particular: no Modal/deployment files, no FLUX removal, no Docker/Compose/env/seeds, no video/SAM2/Whisper, no unrelated Parent account/profile/library flows, no generated/approved/applied visual asset directories, no migration execution, no test-file additions or test execution, no commit/push/merge, and no destructive cleanup.

If code inspection proves a listed path unnecessary, leave it untouched. If implementation requires an unlisted path or additional table/column, stop before that edit and record the uncovered dependency for a separately approved amendment.

## 5. Acceptance and verification boundary

- Backend sanitizer produces stable canonical bytes/hash for safe allowlisted SVG and rejects active/remote/unbounded input before catalog exposure.
- Structural readiness derives from sanitized canonical geometry and reports count/ratio/filled-shape facts; it never auto-approves teaching quality.
- Exact source, license, hash, parser version, reviewer and curator decision survive retrieval and are enforced by scope.
- Manual guide edits only reference existing path IDs, have 4–8 cumulative stages, preserve source geometry, and create copy-on-write lesson versions with the expected revision.
- `409` responses do not overwrite local editor state; browser-local draft is retained until the Teacher resolves the conflict.
- Parent Android and Teacher Web render the same visible stroke IDs/order, and playback state does not modify canonical guide JSON.
- AI capability controls are not exposed as working actions and no new Modal dependency is added.
- No migration is run and no test/build/UI/API/Modal verification is claimed in this turn. Evidence must list implementation facts and all unverified acceptance criteria as NOT VERIFIED/BLOCKED.
