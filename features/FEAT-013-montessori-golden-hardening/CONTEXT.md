# FEAT-013 Montessori Golden Catalog hardening context

- Status: NEEDS_REVISION
- Primary owner: Person 1
- Planning branch: `plan/person-1-montessori-golden-hardening`
- Plan revision: 1
- Parent baseline: FEAT-002 activity catalog v1 at commit `2d61528`
- Goal: deeply harden 20 representative Montessori activity fixtures without introducing AI, UI, backend, storage, provider, or another person's runtime dependency.
- Data policy: synthetic/fixture content only; no real child data.
- Review policy: owner review is provisional/non-production; qualified Montessori review remains a production gate.

## Problem being addressed

FEAT-002 provides broad structural coverage with 100 activities, 20 objectives, hard rules, and deterministic fixtures. Its known limitations are intentionally visible: readiness is coarse by age band, many instructions/safety notes are generic, material substitutes are placeholders, progression links are sparse, and localization has not received focused QA.

FEAT-013 optimizes depth rather than increasing catalog size. It creates a traceable golden overlay/version for 20 selected records and leaves the FEAT-002 source artifacts intact.

## Independence contract

- Reads only versioned local FEAT-002 JSON/specifications and registered references.
- Writes versioned domain data, schema, fixtures, harness checks, and feature-local evidence.
- Makes no network, AI/model, database, mobile, auth, storage, queue, or provider call.
- Does not consume Person 2, 3, or 4 output.
- Does not implement recommendation ranking, Gate B runtime, or integration behavior.

## Authority boundary

- The owner approved revision 1 implementation on 2026-08-25; the scope remains bounded by the approval record.
- Existing project-owner review is provisional. FEAT-013 cannot claim qualified pedagogical or production approval.
- Internal source records and external Montessori references inform the draft; they do not justify invented safety, age, or developmental claims.

## Implementation snapshot

- Exactly 20 candidate v2 records exist, five per age band, linked to immutable FEAT-002 records and hashes.
- The local material registry contains 40 concrete options; the progression graph contains 13 validated edges.
- The offline harness replays 74 fixtures, including primary/substitute success, blocked, boundary, multiple-failure, inactive, fixture-mutation, and baseline-mutation paths.
- Deterministic rebuild, unit tests, and repository gates pass.
- The project owner accepted all 20 records and their associated material options provisionally on 2026-08-25.
- All content is `PROVISIONAL_OWNER_REVIEWED` and remains `production_eligible=false`; qualified Montessori review remains the production gate.

## Checkout portability defect found after completion

On 2026-08-25, switching from the pushed FEAT-013 branch to the FEAT-014 planning branch caused Git to materialize baseline JSON using repository-enforced LF endings. Three approval-time hashes had been captured from CRLF working-tree bytes, so `validate_montessori_golden.py` reported a baseline mismatch even though `git diff` showed no baseline content change.

The Golden content, fixtures, owner decisions, and FEAT-002 Git blobs are unchanged. A narrowly scoped canonical-JSON integrity correction is planned in `plan/PORTABILITY_FIX_PLAN.md` and is not implementation-approved yet.
