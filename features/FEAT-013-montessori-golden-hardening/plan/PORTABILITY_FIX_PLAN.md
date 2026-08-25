# FEAT-013 checkout portability fix plan

- Status: AWAITING_APPROVAL
- Corrective revision: 1
- Prepared at: 2026-08-25
- Estimate: 1.5-2.5 hours / 0.5 story point
- Implementation: NOT_STARTED

## Defect

FEAT-013 froze baseline integrity with SHA-256 over raw text bytes. The approval-time working copy contained CRLF for three generated FEAT-002 JSON files, while `.gitattributes` requires LF. After a branch checkout, Git correctly materialized LF and the validator failed despite identical parsed JSON and a clean baseline diff.

## Approved-scope proposal

- Add canonical JSON SHA-256 (`json.loads` then UTF-8 `json.dumps` with sorted keys and compact separators) as the versioned baseline-integrity algorithm.
- Record algorithm name and four canonical hashes in the selection manifest and evidence.
- Update FEAT-013 builder and validator to use that canonical algorithm for whole JSON files; retain existing per-record canonical hashes.
- Regenerate only derived FEAT-013 manifests/evidence affected by integrity metadata.
- Add tests proving LF and CRLF representations yield the same canonical hash while a semantic mutation fails.
- Re-run deterministic build, 74 fixtures, all tests, repository gates, and owner-review/non-production guards.

## Acceptance criteria

- `AC-PF-01`: LF and CRLF byte representations of identical JSON produce the same canonical integrity hash.
- `AC-PF-02`: changing parsed JSON content produces a different hash and non-zero validator result.
- `AC-PF-03`: FEAT-002 tracked files and Git blobs remain untouched.
- `AC-PF-04`: FEAT-013 Golden content, activity/material counts, fixture outputs, owner decisions, and `production_eligible=false` remain unchanged.
- `AC-PF-05`: Golden validator passes after a branch checkout under repository `.gitattributes` and records the algorithm explicitly.
- `AC-PF-06`: corrective evidence is stored under FEAT-013 and all repository gates pass.

## Out of scope

- Montessori content edits, new activities, changed owner decisions, ranking, console behavior, integration, providers, or production approval.

## Approval rule

Implementation requires explicit approval of this corrective revision. Approval of FEAT-014 alone does not silently authorize rewriting FEAT-013 integrity semantics.
