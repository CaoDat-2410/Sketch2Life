# Motion sprite batch — owner visual approval — 2026-10-02

- Evidence ID: EV-028-MOTION-APPROVAL-03.
- Reviewer/decision: project owner explicitly said “duyệt sprite” for the requested review batch.
  The decision is recorded in `../../../FEAT-030-original-derived-auto-rig/approvals/TASK_APPROVAL.md`.
- Scope: 30 newly generated behavior-cycle sheets / 120 frames, enumerated by cycle ID and source
  filename in `../../assets/generated/motion-cycle-review-manifest.rev1.json`. This approves visual
  appearance only; it does not approve every future use/context or clear legal rights.
- Preservation/integrity: source PNGs remain in `assets/generated/`. All 37 source/approved pairs
  (the 30-sheet expansion plus seven previously approved sheets) were checked against the manifest
  SHA-256 and each other on 2026-10-02 10:41:39 +07:00: 37 checked, 0 mismatches. The 30 newly approved
  sheets have same-hash copies in `assets/approved/`; none is in `assets/applied/`.
- Specific technical observation: the wooden-cube slide sequence repeats essentially the same pose;
  it is registered as one still frame with bounded transform-driven slide, not a four-frame cycle.
- Remaining gates: full generation prompt transcripts are not archived (manifest has summaries and
  generation output IDs); rights/provenance remains `REVIEW_REQUIRED`; crop/pivot/loop QA remains
  `NOT_QA_VERIFIED`; catalog is `NOT_REGISTERED`; formal renderer review is `NOT_VERIFIED`; and
  `runtimeEligible` remains false. The V4 renderer path is offline-tested but has no fresh Android
  visual acceptance. These gates must pass separately before any runtime read is issued.

## Reproduction

PowerShell parsed the manifest and compared the SHA-256 of every generated PNG and its
`assets/approved/` counterpart with the declared manifest hash. Result: `cycle_sheets=37
hash_verified=37 mismatches=0`. No source file was edited by the check.
