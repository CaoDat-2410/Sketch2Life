# Claude follow-up assessment and authored resolver regressions

## External review follow-up — 2026-10-20

Read the independent Claude report retained at
`evidence/local/claude-review-20261020T044951Z/REVIEW.md`. Its later findings supersede any
earlier no-known-findings statement for the full component; previous checkpoint receipts
remain historical. Root assigned this reviewer P2-1 design assessment and P2-3 regression
preparation. No implementation edits were made during this initial assessment.

P2-1 is valid: `test_572_original_backend_files_and_required_batch_profile_are_preserved`
permanently freezes shared backend bytes and the number of07 test files inside the product
suite. The task-specific immutability requirement belongs in the final execution runner.
Existing runner `invariants()` already checks the572 baseline hashes plus tracked history.
Move the remaining profile assertions into an explicitly invoked evidence gate, preserving
the approved50-file baseline and the actual current07 selection without a permanent six-file
limit. Retain baseline/profile artifacts as historical evidence. Finalizer counts should
derive from the recorded selection/profile; do not invent a JUnit pass for a removed node.
X01/X02 must reference concrete executed runner assertions/receipts and their source/JUnit
hashes, with an explicit evidence-gate classification. X02 can additionally retain the
suite-friendly derived-provenance unit assertion. This changes evidence placement, not the
approved immutability or final-batch requirements.

P2-3 is a concrete exact-pin regression gap while current product code behaves correctly.
Proposed real resolver tests use a valid-format wrong hash, unknown ID, another existing
bundle ID combined with the original hash, and wrong version. Assert exact safe reasons,
readyFalse, absent export, unchanged full storage and commit count, plus a positive exact-pin
control. An in-memory mutant deleting only the hash comparison must fail the wrong-hash
assertion. Source/test edits await root's reviewed file allocation.

### P2-3 authored regression checkpoint

After root's explicit plan-review PASS/file allocation, this agent authored only
`backend/tests/unit/test_knowledge_bundle_adapters.py` for product changes. New parametrized
real resolver cases cover a well-formed mismatched hash, unknown ID, another existing bundle
ID paired with the first bundle's hash, and wrong version. Both created bundle IDs/hashes are
asserted distinct. Every case has a valid exact-pin control, checks its exact denial reason
and absent export, and compares full storage plus commit count before/after reads.

Focused new cases:4 passed; full adapter module:19 passed, both zero skips. Ruff on the authored
file passed from backend cwd. Raw logs/JUnit/receipts are in
`local/reviewer-atomic/claude-p2-3-focused/` and `claude-p2-3-adapters/`.
Test-file SHA256: `e9ed452a0cdea915f016d05e1e54c440c8ff5d3ec1169f2ac37d900d3537e61d`.

The removed-hash-guard in-memory mutant fails both the wrong-hash and other-bundle-ID rows;
the unknown-ID and wrong-version controls still pass. Mutant pytest exit1 is the expected
result. Source bytes remain unchanged; exact source/test/log/JUnit hashes are recorded in
`local/reviewer-atomic/claude-p2-3-mutant/receipt.json`, with probe and raw output beside it.
This checkpoint is authored implementation/test evidence, not an independent C verdict for
the newly authored tests. Root's separate `final_review` agent owns that independent review.
