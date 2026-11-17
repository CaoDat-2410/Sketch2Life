# Plan Rev65 — Teacher Sketch Deck presentation UI

**Status:** APPROVED for the exact scope below
**Date:** 2026-11-10
**Authority:** FEAT-063 SRS v2.7-draft, Rev60 working copy (unsigned), especially §§6.2.1, FR-T-19, UC-17, BR-43 and NFR-33.

## Goal

Replace the raw JSON dump of the existing Teacher Sketch Deck response with a usable presentation surface in Teacher Web. The view must show every generated slide in a white 16:9 canvas, present the reviewed content in concise Vietnamese, and make the existing generated drawing guide image visible when one is available.

## Current API facts

- `POST /api/teacher/v1/organizations/{organization_id}/ai/sketch-decks` returns a `sketch2life.teacher-sketch-deck.v1` DRAFT with ordered `slides` (`orientation`, `drawing_guide`, `subject_exploration`, `approved_activity`) and `review_required: true`.
- `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals` returns one FLUX-generated composite horizontal guide image for the reviewed drawing steps. It is a separate optional request; the deck endpoint itself does not return an image or per-slide asset references.
- No mounted route currently regenerates one selected deck sketch. Do not call the whole-deck endpoint and present that as single-step regeneration.

## Approved implementation scope

1. Add a Teacher Web presentation component that safely validates and renders the current deck response; remove the `<pre>` JSON display.
2. Render `orientation`, `drawing_guide`, `subject_exploration`, and `approved_activity` slide content from the returned deck only. Add slide navigation, slide selection, previous/next, drawing-step skip, close, and keyboard navigation as ephemeral UI state.
3. Use a white 16:9 slide surface with clear typography, high contrast, visible slide position, and a DRAFT/review-required label. Keep the teacher in control; no auto-advance or edits to generated source content.
4. On the drawing guide slide, display the actual image from the existing FLUX lesson-visual response as a whole sequence image. If absent, show an explicit empty state and an action that calls the existing lesson-visual API. Do not invent per-slide images or represent the composite as separately generated assets.
5. Keep review/creation in the existing UI. Do not add persistence, publish/ready transitions, export, freehand canvas, story video playback, backend/Modal contract changes, model/deployment changes, or a fake regenerate control.
6. Verify the Teacher Web build and inspect the UI with a real Teacher session and live Modal responses (no fixtures). Record one fresh deck and one lesson-visual request if the live environment permits; no video.

## Acceptance criteria

- AC-65-01: Valid `sketch2life.teacher-sketch-deck.v1` output renders as a slide viewer, never as raw JSON; unsupported/malformed slide data shows a clear recoverable error.
- AC-65-02: Presentation canvas remains white and 16:9 with short readable text and a visible draft/review state.
- AC-65-03: Teacher can select any returned slide, move backward/forward, skip a drawing instruction, close presentation, and use keyboard navigation. Controls do not mutate or persist the draft.
- AC-65-04: The drawing guide slide displays the actual FLUX composite image returned by the existing endpoint. Without it, the UI explains that the optional image is not available and can request it through the existing endpoint.
- AC-65-05: Activity slide content comes only from the corresponding approved activity payload; no generated activity is added by the UI.
- AC-65-06: `npm run build` passes, and a live Teacher UI run shows actual Modal-produced deck/visual content. The endpoint’s DRAFT state remains visible.

## Exact file manifest

- `apps/teacher-ui/src/pages/ModalAiLessonFlowPage.tsx`
- `apps/teacher-ui/src/components/TeacherDeckPresentation.tsx` (new)
- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV65_TEACHER_PRESENTATION_UI_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-75_TEACHER_PRESENTATION_UI_20261110.md` (new)
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-75_TEACHER_PRESENTATION_UI_20261110/screenshots/` (new)

Any path outside this manifest requires a scope addendum before editing.

## Risks and known limits

- The current service returns one composite drawing guide image, not distinct image assets per slide or per step. This UI will show that composite on the drawing-guide slide. Individual-step regeneration requires a new versioned backend/Modal contract and is not simulated here.
- The current Teacher AI slice returns an in-memory DRAFT rather than a durable occurrence-pinned deck. This work does not claim persistence, STALE fencing, publication, or production readiness.
- SRS presentation and privacy requirements remain draft requirements awaiting formal SRS sign-off.
