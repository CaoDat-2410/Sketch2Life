# Independent six-mutant service recheck

Verdict: PASS for the six requested guard-removal mutants. This is not a whole-component acceptance or runtime review.

Baseline copied source: 262 passed, 0 failed/error/skipped. Each mutant ran all 262 cases and had exit 1 from executed assertion failures, with 0 collection/import errors. No deletion/reset was used; all mutations remain in separate feature-local copies.

| Mutant | Assertion failures | Exact failing nodes |
|---|---:|---|
| M01_drop_AUDIENCE_CHANGED | 1 | `backend/tests/unit/test_knowledge_bundle_service.py::test_same_revision_fact_changes_deny_current_read_and_edit_without_writes[audience]` |
| M04_drop_SOURCE_RECORD_CHANGED | 1 | `backend/tests/unit/test_knowledge_bundle_service.py::test_same_revision_fact_changes_deny_current_read_and_edit_without_writes[source_record]` |
| M06_drop_receipt_content_guard | 3 | `backend/tests/unit/test_knowledge_bundle_service.py::test_corrupt_accepted_receipt_is_rejected_without_writes[body]`<br>`backend/tests/unit/test_knowledge_bundle_service.py::test_corrupt_accepted_receipt_is_rejected_without_writes[readiness]`<br>`backend/tests/unit/test_knowledge_bundle_service.py::test_corrupt_accepted_receipt_is_rejected_without_writes[status]` |
| M07_drop_requested_hash_compare | 2 | `backend/tests/unit/test_knowledge_bundle_adapters.py::test_actual_exact_resolver_rejects_mismatched_requested_pins_without_writes[hash-EXACT_BUNDLE_MISMATCH]`<br>`backend/tests/unit/test_knowledge_bundle_adapters.py::test_actual_exact_resolver_rejects_mismatched_requested_pins_without_writes[other-bundle-id-EXACT_BUNDLE_MISMATCH]` |
| M09_drop_expected_context | 1 | `backend/tests/unit/test_knowledge_bundle_service.py::test_edit_expected_revision_mismatch_rejects_atomically[expected_context_revision-CONTEXT_REVISION_MISMATCH]` |
| M10_drop_expected_audience | 1 | `backend/tests/unit/test_knowledge_bundle_service.py::test_edit_expected_revision_mismatch_rejects_atomically[expected_audience_revision-AUDIENCE_REVISION_MISMATCH]` |

P2-1 copied-source proof: appending a harmless comment to copied backend/src/sketch2life/domain/assistance.py leaves the six product modules at 262 passed. The actual evidence runner backend-baseline assertion was isolated by AST and run against the copied root using the real read-only baseline manifest: unmodified copy exit 0; commented copy exit 1 with AssertionError. Exactly that one file differs among the 572 baseline entries. This verifies that evidence assertion only, not the entire Git/external/final-runner gate.

All 588 real backend source/test files have byte-identical before/after manifests, SHA256 `7bdb557e411d222442af25e5eb4e9d20315163698704c6da4aed53cab65fcd50`. Imported service paths were asserted to point into each copy. Logs, JUnit, command/environment/exits and changed-source hashes are in each case receipt; SUMMARY.json is the index.

M06 removes the complete combined receipt key/status/body guard; the three killed assertions establish this removal is detected, without claiming each conjunct was independently mutated. No product source or test was edited. No stage, commit, push or runtime/provider execution.
