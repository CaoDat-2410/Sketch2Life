# FEAT-083 Plan Rev5 — remove legacy Teacher FLUX lesson-visual API

**Date:** 2026-11-23
**Status:** APPROVED by the owner’s direct instruction in this conversation: remove the obsolete API.
**Parent plans:** Rev1–Rev4 remain in force.

## Finding

Source review found that the endpoint is still called by the Teacher lesson workflow page. The owner nevertheless directed that the old API be removed. Remove the endpoint and its UI caller together so the Teacher UI cannot issue a request to a deleted route.

## Allowed changes

- Remove `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals` from `teacher_ai.py`.
- Remove its FLUX provenance constant and worker mapping from `modal_function_client.py`, and remove `lesson.visual.generate` from the Modal L4 worker envelope and current workload registry.
- Remove the corresponding Teacher web service method, page button/state/handler, and presentation-only FLUX image controls.
- Remove the route from existing backend app-composition and OpenAPI contract expectations.
- Keep `flux_image_app.py` and dated FLUX evidence as historical POC source. Because the workload is removed from the accepted worker envelope, that old function must fail closed if invoked directly; do not deploy or call it.
- Update the Modal README, FEAT-063 SRS source snapshot, SRS authority digest, and FEAT-083 records to say the backend/UI route is removed and the target SVG illustration API is still a separate unimplemented path.

## Acceptance

- No current backend route, Teacher web caller, service method, Modal backend mapping, or worker envelope accepts `lesson.visual.generate` / `/lesson-visuals`.
- Existing API contract expectations no longer list the operation.
- The Teacher Sketch Deck remains usable as a text/step presentation; the removed FLUX image action is not replaced or represented as an SVG capability.
- Historical POC source/evidence remains distinguishable from active product dispatch.
- No tests/typecheck, database migration, Modal deploy/inference, API/E2E, emulator, security validation, commit or push are run.
