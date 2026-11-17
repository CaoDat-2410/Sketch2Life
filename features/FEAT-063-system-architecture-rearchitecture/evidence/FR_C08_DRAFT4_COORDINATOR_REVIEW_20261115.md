# FR-C-08 Draft 4 coordinator review — 2026-11-15

## Review boundary

This is a read-only coordinator review of the Draft 4 planning package against the canonical working SRS Rev68, D-208, and the recorded Draft 3 cold-review findings. It is **not** a fresh independent cold review, implementation approval, Task Approval, launch authorization, or evidence of runtime/database behavior.

## Target pins reviewed

| File | Bytes | SHA-256 |
|---|---:|---|
| `plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT4_20261115.md` | 20,897 | `BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70` |
| `plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT4_20261115.md` | 13,871 | `483A228C65400016964F43C4C52082E49CAF232C49B8AB8E8E6692DB6E21B385` |
| `plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT4_20261115.md` | 65,130 | `F4C76422DDE39A2B34A5364BC6F7F77B3A960331F4DBA00939082FBE54E3512A` |

The allowlist's 24 strict planning-input rows were rehashed: **24 matched, 0 mismatches**. Its E/N implementation-path observations are explicitly carried forward from Draft 3 and were not re-certified; they must be reconciled and rehashed at a future authorized preflight.

## Review findings and corrections

- The Draft 3 review issues are addressed in Draft 4: named accountable people are a pre-launch gate; reconciliation/pinning of the partial, dirty M2 baseline is required before any FR-C-08 implementation; unresolved audit mapping blocks dependent audit writes/reads and full lifecycle acceptance; the earlier 81-pass/1-fail run is distinguished from the later exit-1 run with no aggregate count; and Draft 1 is no longer attributed as defining DELETE eligibility.
- This review found one additional D-208 gate missing from the initial Draft 4 text: the corresponding versioned implementation contract must be updated to the SRS wording and independently reviewed before implementation. The requirement is now explicit in the Spec, Lifecycle Plan, and Allowlist. The documents do not claim that this contract-review gate is complete.
- The reviewed lifecycle policy remains aligned with Rev68/D-208: cancel is limited to the 13 permitted unfinished states; explicit DELETE is user-requested for COMPLETED/FAILED/ABANDONED; no automatic FAILED/ABANDONED purge; current-owner/current-assignment authorization; immediate fencing; best-effort job/provider cancellation and late-result fencing; owning-module verified purge; shared-reference verification; quota/sample-claim preservation; and metadata-only audit with unresolved field/readers/physical-scope/retention decisions kept open.
- No further actionable SRS/D-208 policy mismatch was identified in this coordinator review. The package remains **DRAFT / PROPOSED / BLOCKED FOR IMPLEMENTATION / NOT APPROVED / NOT LAUNCHED**.

## Gates still open

1. A separate fresh independent cold review of the final Draft 4 package remains required; this coordinator review does not satisfy it.
2. The Parent-scope/versioned request and durable receipt contract, lifecycle read predicate, authorization/revocation path, state mapping, Core Asset reference/deletion/retry contract, and audit field/readers/physical-scope/retention map remain implementation blockers for their dependent behavior.
3. The corresponding SRS-aligned implementation contract must be updated and independently reviewed under D-208.
4. The partial/dirty M2 baseline must be reconciled and pinned before any FR-C-08 implementation. M2 approvals and command ceilings do not transfer.
5. A separate FEAT-063 implementation Task Approval, exact selected path set/command ceilings, named accountable owners before launch, and a pinned owner launch prompt are still required at their respective gates.

## Not run / not changed

No source or test file, SRS, DTR, decision, or approval record was changed. No test, typecheck, validator, runtime/backend, database/migration, Docker, network, provider, or Modal command was run. Nothing was staged, committed, or pushed.
