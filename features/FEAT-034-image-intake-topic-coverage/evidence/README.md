# FEAT-034 evidence index

Plan revision 1 is approved at the exact hash recorded in `../approvals/TASK_APPROVAL.md`. The approved `../plan/PLAN.md` remains unchanged to preserve that hash.

- `reports/CATALOG_TOPIC_MAPPING_AUDIT_V1.json` — metadata-only audit of all 300 active semantic profiles and display cards, with topic × age-band coverage. It reports 300/300 displayable cards, 77 explicit code-level corrections, and 223 rows awaiting qualified Montessori review. It is not pedagogical certification.
- Backend focused contract/unit tests passed: `backend/tests/contract/test_live_image_demo_api.py`, `backend/tests/unit/test_lightning_activity_ranker.py`, `backend/tests/unit/test_topic_activity_matching.py`, and `backend/tests/unit/test_catalog_expansion.py` (54 passed). The full backend suite also passed using a unique feature-local pytest temp directory; pytest emitted only a warning that the repository-level cache directory is not writable.
- Mobile `tsc --noEmit`, `pnpm --dir apps/ui-mobile test`, and `pnpm --dir apps/ui-mobile build:web` passed. Web export is a bundler smoke test, not Android native-runtime proof.
- Ruff passed on changed backend files; `tools/validate_repository_security.py` returned `REPOSITORY_SECURITY_VALID`.
- Android Expo export passed: 907 modules bundled into a 3.25 MB Hermes bundle. The emulator is online and `com.sketch2life.mobile` is installed. The already-running Metro server is rooted at the repository rather than `apps/ui-mobile`, so its bundle URL returned 404. No synthetic image-picker-to-recommendation device run has yet been recorded, and native image-decoder claims remain unverified.
- The audit observes four `ANIMAL_GENERIC` cards in age band 3–6; this is a gap candidate pending Montessori review, not a reason to invent an activity.

Only synthetic fixture hashes, sanitized test output, aggregate runtime measurements, catalog reports, and qualified review notes belong here. Never copy a user image, child data, URI/path, EXIF, credentials, or raw provider output into this directory.
