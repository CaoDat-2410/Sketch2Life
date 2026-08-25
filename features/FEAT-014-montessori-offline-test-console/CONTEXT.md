# FEAT-014 Montessori Offline Test Console context

- Status: APPROVED_BLOCKED_BY_PARENT_FIX
- Primary owner: Person 1
- Planning branch: `plan/person-1-montessori-offline-console`
- Plan revision: 1
- Parent input: FEAT-013 Golden Activity v2 overlay at commit `f70f3c9`, with a newly discovered raw-byte hash portability correction awaiting separate approval
- Goal: let the owner and developers exercise one explicitly selected Golden Activity against deterministic eligibility inputs without reading JSON or depending on another workstream.
- Data policy: IDs, enums, numeric ages, and synthetic fixtures only; no names, narration, drawings, observations, or real child data.

## User need

FEAT-013 has strong automated fixture coverage, but a reviewer currently needs to read JSON or invoke pytest to explore a custom combination of age, readiness, prerequisites, materials, supervision, policy, and active status. FEAT-014 proposes a small guided console that exposes the same deterministic behavior and reason codes in a reviewable form.

## Independence boundary

- Reads only committed local FEAT-013 catalog/material artifacts and synthetic inputs.
- Runs entirely offline with Python standard-library code.
- Does not call backend, mobile, AI/Kaggle/Lightning/Runpod, auth, DB, S3, queue, or network.
- Does not consume Person 2, 3, or 4 output.
- Requires the user to select one activity; it never retrieves, scores, ranks, or recommends an activity.
- Is a test/review harness, not production recommendation runtime.

## Authority and safety

- FEAT-013 records are `PROVISIONAL_OWNER_REVIEWED` and `production_eligible=false`.
- Console output is contract evidence only, not a claim that an activity is suitable for a real child.
- Revision 1 was approved by the project owner on 2026-08-25.
- Phase 1 implementation also requires the FEAT-013 portability correction to pass; FEAT-014 must not bypass or weaken the parent validator.
