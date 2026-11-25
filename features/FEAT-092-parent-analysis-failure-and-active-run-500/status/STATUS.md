# FEAT-092 status

**State:** Implemented locally; not committed, not pushed.

| Item | Result |
|---|---|
| A. `ParentActivityV1` provenance fields | Added 8 optional fields; `tests/unit/test_parent_main_activity_snapshot_schema.py` passes. |
| B. Worker builtin exception classified terminal | `_is_remote_user_code_failure` in `modal_function_client.py`; 2 new tests in `test_story_run_lite_photo_bridge.py` pass, plus `test_modal_story_function_client.py`. |
| C. App stops spinning on `AWAITING_RECONCILIATION` | `useParentController.ts settleDrawingStage`; `parentPhaseBWiring`/`parentDrawingTerminal` vitest pass. |
| API container rebuilt | `sketch2life-api-1` healthy; no ValidationError after restart. |

Not verified: end-to-end on a device; the Modal `AttributeError` root cause (needs `modal app logs` from the deploy workspace).
Pre-existing, unrelated failures seen: `tools/validate_repository_security.py` (FEAT-085 path, dev-seed script), `tsc` errors in `VideoScreen.tsx`/`ParentVisualPreviewHarness.tsx`, broad contract-test failures in the ad-hoc test container.
