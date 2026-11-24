# FEAT-083 Plan Rev4 — align stale Qwen model assertions

**Date:** 2026-11-23
**Status:** APPROVED under the owner’s direct instruction to use Qwen3.8 throughout active Qwen workloads.
**Parent plans:** Rev1–Rev3 remain in force.

## Reason

Source review found that the existing Modal contract test still asserts that drawing uses Qwen3.5 while text uses Qwen3.8, and its test name describes that retired split. The FEAT-083 source and workload registry now pin all active Qwen workloads to the same Qwen3.8 checkpoint. Leaving the old assertions would make the repository’s contract documentation/tests contradict the source.

## Allowed change

- Update the existing assertions and the affected test name in `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py` to require the pinned Qwen3.8 model/revision for drawing and active text workloads.
- Do not add new test cases or change unrelated historical FLUX/worker tests.
- Do not run the test suite, typecheck, Modal inference, API/E2E, migration, emulator, security validation, commit or push.

## Acceptance

- The existing current-registry contract assertion no longer expects Qwen3.5 for drawing or describes the active split as Qwen3.5/Qwen3.8.
- Historical Rev45 evidence and retired worker records remain unchanged.
- Status/evidence state clearly says the edited test was not executed and runtime remains unverified.
