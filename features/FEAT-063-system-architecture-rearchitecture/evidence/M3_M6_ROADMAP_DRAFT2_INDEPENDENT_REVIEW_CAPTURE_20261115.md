# Independent Cold Review Capture — M3–M6 Roadmap Draft 2

Date: 2026-11-15  
Reviewer: fresh-context independent reviewer /root/m3_m6_draft2_cold_review  
Record type: coordinator capture of the reviewer’s final response. The reviewer returned findings in chat and did not create an in-repository report file. This capture preserves that result; it is not owner approval.

## Reviewed inputs and pin verification

- Roadmap Draft 2: 19,493 bytes; SHA-256 4BB75DABD291EE2D9E2ABF2C6B80A18BEF9700F195E471DEC231366EA5CAC663.
- All 11 input-table pins matched when resolved relative to .worktrees/m2-s2.
- Worktree authority pointer: 4,313 bytes; SHA-256 D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60.
- Canonical working Rev68 SRS: 639,948 bytes; SHA-256 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944.
- The enclosing root checkout has a different, older SRS authority pointer (4,054 bytes / 032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F) and Rev60 artifact. The review target and its pin table are explicitly worktree-relative to m2-s2; this is a scope note, not a Draft 2 pin mismatch.

## Verdict

CHANGES REQUIRED — 0 P1, 2 P2, 2 P3.

1. **P2 — M4 Teacher sample selection:** Draft 2 requires an eligible child and Teacher confirmation but omits the equal-probability choice from the eligible set. Rev68 §5.2 step 8 and §31.9 AC-56 require it.
2. **P2 — M4 Teacher guide context:** Draft 2's generic-topic-only sentence narrows the Teacher path. Rev68 §5.2 step 6 allows a lesson-specific guide draft; preserve the lesson context while excluding child data.
3. **P3 — Quota detail:** State Parent-account versus school-organization scope, absence of a Teacher-account quota pool, included-first/FIFO top-up and expiry rules in phase acceptance. Rev68 §23.5 and §31.9 AC-61.
4. **P3 — Parent timing/history:** Specify the 144-hour reminder, 168-hour closeout, and 30-day lesson-history window. Rev68 §§5.1, 6.1.1 and 31.10(3).

Draft 2 fixed all three findings from the Draft 1 review. The reviewer otherwise confirmed Parent text/voice/transcript and image ordering, activity selection, video constraints, age range, optional Parent guide safeguards, Teacher presentation editing/publication, lifecycle, M2, real-data and approval boundaries.

## Boundaries

The review was read-only. No tests, validators, builds, runtime, backend, database, provider or deployment operations were run. The result does not approve implementation, real-data use, or launch.