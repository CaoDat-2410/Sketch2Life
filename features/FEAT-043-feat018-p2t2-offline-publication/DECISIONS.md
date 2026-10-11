# Feature decisions

## D-043-01 — Separate publication feature (2026-10-11)

The publication authority is recorded in FEAT-043, not in FEAT-018 `approvals/TASK_APPROVAL.md`.
The FEAT-018 file is under an owner approval-write hold. FEAT-043 was the next feature number
unused on every remote branch at the time.

## D-043-02 — Five commits, byte-identical originals (owner, 2026-10-11)

PUB-P1's five-commit split is kept. The 18 selected originals are published unchanged, so the
historical acceptance pins keep describing exactly what was accepted. Local governance files,
D6 material and the acceptance originals stay unpublished. A derived public summary replaces them.

## D-043-03 — Owner decision A: scanner exclusion semantics (2026-10-11)

For the five PUB-P1 commit trees only, the owner accepts the declared content-exclusion
semantics of scanner SHA-256 `4c8733f6…cfb5c`. The accepted exclusions are exactly the 231
baseline files in `evidence/metrics/SCANNER_EXCLUSIONS_T1_T4.tsv` (SHA-256 `a40f8fed…8c02`) plus
the 8 zero-byte FEAT-043 `.gitkeep` files. This is not a general security PASS and closes no
Security S3/C1–C7 or live gate.

## D-043-04 — Owner decision B1: pre-existing architecture finding (2026-10-11)

`tools/validate_architecture.py` stays FAIL for the unchanged baseline finding in
`backend/src/sketch2life/application/services/backend_ai_workflow.py`. A prepared minimal fix
is not included; FEAT-020 handles it separately.

## D-043-05 — Owner decision C1: lint/type debt (2026-10-11)

Ruff (550 whole-backend findings, 547 new) and mypy strict (115 errors, 112 new) stay FAIL. No
config, ignore, formatting or source/test change is made. Spot checks found no runtime defect in
the inspected clusters; this is not a claim that every finding is a false positive.
