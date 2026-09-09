# P1 engine implementation evidence — 2026-09-09

The approved P1 slice is implemented in three layers:

- `backend/src/sketch2life/contracts/schemas/p1_experience.py` contains the fixture-only versioned contracts. Extra fields are rejected, anchors must carry source claim provenance and adult confirmation, and `ExperienceSpecV1` checks that video, original-art animation, activity and bridge sentence keep one identity.
- `backend/src/sketch2life/infrastructure/catalog/p1_catalog.py` loads the reviewed 20-activity golden overlay and 20 objectives into immutable `ActivityTemplateV1` records. It preserves the catalog record hash, review status and `production_eligible=false`.
- `backend/src/sketch2life/application/services/p1_experience.py` performs adult-context completeness checks, hard eligibility checks, deterministic anchor/template selection, the 30/35/20/15 fit policy, immutable spec hashing and Gate B exact identity/version locking.

Validation evidence:

1. The existing P1 harness validates 100 MVP activities, 20 objectives, 20 golden activities, 40 material options and 74 golden fixture scenarios.
2. The P1 backend tests cover butterfly → wings → symmetry → fold-and-print, unrelated colour sorting rejection, missing adult context, stale template rejection and contract extra-field rejection.
3. The full backend suite passes when its temporary directory is redirected into the workspace; five pre-existing GPU/provider tests remain skipped by their own readiness gates. The default Windows temp location is permission-restricted in this environment, so a workspace temp directory was used for that run.

No live provider, production API, Android release, cloud deployment, raw image, credential or real child data was used. The butterfly fold-and-print record is explicitly a test-only fixture; it does not promote a production catalog activity.
