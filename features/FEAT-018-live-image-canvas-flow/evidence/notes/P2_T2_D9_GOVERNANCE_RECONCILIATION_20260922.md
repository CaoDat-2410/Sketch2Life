# FEAT-018 P2-T2 D9 governance reconciliation

Preparation date: 2026-09-22
Correction date: 2026-09-22 (F-01..F-06 from the first independent review)
Package status: `READY_FOR_FRESH_INDEPENDENT_D9_GOVERNANCE_RECONCILIATION_REREVIEW`
Boundary: `DOCUMENTATION_ONLY_RECONCILIATION`

This is a documentation-only governance reconciliation. It reconciles
`CONTEXT.md`, `DECISIONS.md`, and the live-Lightning execution plan with the
already-committed, already-independently-reviewed D9 stdout/stderr
enforcement correction. It does not modify source, tests, fixtures,
contracts, validators, dependencies, workflows, or `approvals/TASK_APPROVAL.md`.
It does not stage, commit, push, or perform any Lightning, model, GPU,
provider, network, or live-execution activity.

## 1. Authoritative implementation checkpoint

| Fact | Value |
|---|---|
| Branch | `feature/feat018-p2t2-live-lightning` |
| HEAD | `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc` |
| Parent | `552bc5d939f36b2b87dc7f0cea909110e8750107` |
| Commit message | `fix(feat018): close D9 stream enforcement gaps` |
| Source blob | `e1c89536e612b9f801ff2e429e76f3f0d0c370ee` |
| Test blob | `3a4db7fd56185da82749b95dd42ca1a3bdc13c0d` |
| Independent correction review | `tmp/feat018-p2t2-d9-independent-correction-review-20260922/REVIEW.md`, verdict `PASS` |
| Follow-up commit checkpoint | `tmp/feat018-p2t2-d9-followup-commit-checkpoint-20260922/REPORT.md`, verdict `PASS` |

All five facts were independently re-verified in this reconciliation
(`git rev-parse HEAD`, `git rev-parse HEAD^`, `git log -1 --format=%B HEAD`,
`git diff-tree --no-commit-id --raw -r HEAD`) and match exactly.

## 2. Reconciled D9 facts (this document's authority)

- The owner-approved stdout ceiling is `16384` bytes; the owner-approved
  stderr ceiling is `32768` bytes (`approvals/TASK_APPROVAL.md`, "Owner
  approval for FEAT-018 P2-T2 D9 stdout/stderr enforcement implementation
  scope", 2026-09-21). These are owner policy values, not values inferred
  from runtime observation, and are unchanged by this reconciliation.
- The candidate-only D9 numeric ceilings are unchanged:
  `raw_output_max_bytes=65536` and `ipc_envelope_max_bytes=98304` remain
  `OWNER_SELECTED_CANDIDATE_ONLY`. The stdout/stderr approval supersedes
  `SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED` for stdout/stderr only; no
  stdout/stderr value was ever a candidate value.
- D9 offline stdout/stderr enforcement is implemented and committed at
  `86836d24cfcd83ca14c0bc50e79fff1103cb9ecc`.
- F1-F4 (the four correctness gaps identified by the independent post-commit
  review at `tmp/feat018-p2t2-d9-two-commit-post-commit-review-20260922/REVIEW.md`,
  verdict `BLOCKED`) are corrected and independently reviewed with verdict
  `PASS` (`tmp/feat018-p2t2-d9-independent-correction-review-20260922/REVIEW.md`).
- Commit `86836d2` and its two blobs
  (`e1c89536e612b9f801ff2e429e76f3f0d0c370ee`,
  `3a4db7fd56185da82749b95dd42ca1a3bdc13c0d`) are the authoritative D9
  correction checkpoint.
- The committed source and test blobs exactly match the independently
  reviewed blobs (verified by `git diff-tree` above).
- D9 offline stdout/stderr enforcement implementation is complete: raw bytes
  are counted independently per process role and stream before any decoding,
  and are capture-and-discard only.
- No raw stream payload is retained or published; only typed, bounded
  metadata (byte counts, disposition, terminal category, failure code) ever
  crosses a process or evidence boundary.
- D9 creates no retry, additional attempt, adapter call, or session; the
  existing one-adapter-call/at-most-two-attempt cardinality is unchanged and
  independently confirmed.
- The known architecture finding
  (`backend/src/sketch2life/application/services/backend_ai_workflow.py`,
  "application imports an outer layer") is pre-existing and unchanged: its
  blob is `2f339ab982d65ea490c20475baeeb122a57ba5ef` at both HEAD and the
  current worktree, with an empty diff between them.

## 3. Protected state (unchanged by this reconciliation)

```text
D9 offline enforcement implementation = IMPLEMENTED_CORRECTED_AND_INDEPENDENTLY_REVIEWED_PASS
D9_OFFLINE_IMPLEMENTATION_COMMIT = 86836d24cfcd83ca14c0bc50e79fff1103cb9ecc
D9 numeric ceilings (raw_output_max_bytes=65536, ipc_envelope_max_bytes=98304) = OWNER_SELECTED_CANDIDATE_ONLY
reviewed_runtime_code_commit = 9549a341194f40b1a9be419d6fce0d70f1ca0384 (unchanged; NOT rebound to 86836d2)
P2T2-LIVE-D9 = NOT RESOLVED
D9_LIVE_D11_CARRIER_SCOPE = UNKNOWN_UNRESOLVED_PENDING_D11
D11 = BLOCKED
D11.LIVE_SEAM_BINDING = BLOCKED
D1 = BLOCKED_BY_D11
D6 overall = NOT FINALLY RESOLVED (fixture identity remains RESOLVED_WITH_PROPOSED_VALUE)
STAGE_4 = NOT READY
LIVE/MODEL/GPU/PROVIDER/NETWORK/LIGHTNING = NOT AUTHORIZED
NEXT (global; live plan Section 11 CURRENT) = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
```

This reconciliation does not claim full live D9 resolution, does not bind a
new `reviewed_runtime_code_commit`, does not resolve D11, D1, or D6 overall,
and does not open Stage 4. No push or live execution has occurred.

## 4. Distinguishing D9 state (required by the reconciliation goal)

- **Historical pre-implementation D9 package state** (2026-09-21 and
  earlier): the D9 design package
  (`evidence/notes/P2_T2_D9_STDOUT_STDERR_ENFORCEMENT_APPROVAL_PACKAGE_DRAFT_20260921.md`,
  `Package status: DESIGN_RECORD_ONLY`) and the implementation-approval
  package
  (`evidence/notes/P2_T2_D9_STDOUT_STDERR_ENFORCEMENT_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT_20260921.md`,
  `Package status: DRAFT_FOR_OWNER_REVIEW`) recorded candidate-only
  raw-output/IPC ceilings, no selected stdout/stderr value, and a
  design-only, not-yet-implemented state. This history is unchanged and is
  not rewritten by this reconciliation.
- **Completed offline D9 implementation/correction state** (new, reconciled
  by this package): exact stdout/stderr ceilings owner-approved 2026-09-21;
  implemented at `552bc5d939f36b2b87dc7f0cea909110e8750107`; F1-F4 found by
  independent post-commit review (`BLOCKED`); corrected within the same two
  authorized files; independently re-reviewed (`PASS`); committed as
  `86836d2`; independently re-verified by a follow-up commit checkpoint
  (`PASS`).
- **Still-unresolved live D9/D11 carrier state** (unchanged): `P2T2-LIVE-D9`,
  `D9_LIVE_D11_CARRIER_SCOPE`, D11, `D11.LIVE_SEAM_BINDING`, D1, and Stage 4
  remain exactly as recorded in Section 3 above.

## 5. Changed-file scope

Permitted documentation paths only:

- `features/FEAT-018-live-image-canvas-flow/CONTEXT.md`
- `features/FEAT-018-live-image-canvas-flow/DECISIONS.md`
- `features/FEAT-018-live-image-canvas-flow/plan/P2_T2_LIVE_LIGHTNING_EXECUTION_PLAN_DRAFT_20260913.md`
- `features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_D9_GOVERNANCE_RECONCILIATION_20260922.md` (this file, new)

`approvals/TASK_APPROVAL.md` was read for context only and was not modified.
No source, test, fixture, contract, validator, dependency, or workflow file
was modified. The ignored local records are the preparation report
`tmp/feat018-p2t2-d9-governance-reconciliation-20260922/REPORT.md`
(annotated with corrections), the first independent review
`tmp/feat018-p2t2-d9-governance-reconciliation-independent-review-20260922/REVIEW.md`
(verdict `BLOCKED`), and the correction report
`tmp/feat018-p2t2-d9-governance-reconciliation-correction-20260922/REPORT.md`,
which holds the final blobs and the preservation proof.

## 6. Preservation of existing D1/D6 and unrelated work

- The D6 binding draft
  (`evidence/notes/P2_T2_D6_MEDIA_VALIDATION_BINDING_PACKAGE_DRAFT_20260920.md`,
  `b80e4d4d5e565f575155c7e31787a4f6b4c0ddf2`) and the untracked D1
  owner-resolution package draft
  (`evidence/notes/P2_T2_D1_OWNER_RESOLUTION_PACKAGE_DRAFT_20260920.md`,
  `9b42d46c9326f35e952816569d59df5274335993`) were read only and are
  byte-identical to their hashes before this reconciliation.
- `CONTEXT.md` and `DECISIONS.md`: compared blob-to-blob with their
  pre-reconciliation blobs (`f4b9e9e10a027e18426b334c60f4d34e33604255`,
  `63dbca5e6f91757191315ef2004c13bcebfbe79c`), the changes are purely
  additive. Every pre-existing line, including the pre-existing global
  `NEXT = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING` in both files,
  is preserved.
- Live plan: compared with its pre-reconciliation blob
  (`c80e1299c19472f8ba6d8d9933504faf20761cfe`), every pre-existing
  uncommitted added line is preserved verbatim except three disclosed edits:
  1. the header's `Last updated` first line: the date becomes 2026-09-22 and
     the new lead item is prepended; its prior items, including "D9 package
     correction", are retained on the following line;
  2. pointer correction #2 in update-history item 8 ("current" ->
     "historical" Section 12.6 entry);
  3. the Section 9 `P2T2-LIVE-D9` row: its prior text is preserved verbatim
     as a prefix, and a dated 2026-09-22 update is appended.
- Committed (HEAD) lines changed in the live plan are only pointer
  correction #1 (the Section 12.6 heading, `CURRENT` -> `HISTORICAL
  (SUPERSEDED)`) and pointer correction #3 (the Section 12 preamble line
  "Section 12.6 is the current validation record." is replaced by a bullet
  listing Section 12.6 as a historical validation record whose `NEXT` remains
  the current global gate, plus "Section 12.7 is the current validation
  record."). The line "Section 11 `CURRENT` is canonical." is unchanged.
- Correction disclosure: the first version of this reconciliation, which the
  first independent review found `BLOCKED`, had replaced the pre-existing
  `CONTEXT.md` global `NEXT` line (F-01), moved Section 12.6's still-open
  `NEXT` under "satisfied" (F-02), misstated the D9 numeric ceilings (F-03),
  rewritten "Section 11 `CURRENT` is canonical." (F-04), dropped "D9 package
  correction" from the plan header (F-05), and cited "Section 2" for the
  `P2T2-LIVE-D9` section (F-06). Its earlier statement that no pre-existing
  line or hunk was altered was therefore inaccurate for that version. All
  six items are corrected (Section 8).

## 7. Gates

```text
NEXT (global; unchanged) = PREPARE_D1_OWNER_RESOLUTION_AND_D6_FIXTURE_BINDING
D9_RECONCILIATION_PACKAGE_GATE (package-local) = FRESH_INDEPENDENT_D9_GOVERNANCE_RECONCILIATION_REREVIEW
```

The global `NEXT` is the live plan's Section 11 `CURRENT` gate, and it
remains the only current next gate. Section 11 `CURRENT` remains the sole
canonical current-state block. The D9 review gate is package-local to this
reconciliation only; it does not replace, supersede, or satisfy the global
`NEXT`. The first package-local review
(`INDEPENDENT_D9_GOVERNANCE_RECONCILIATION_REVIEW`) returned `BLOCKED`.
After correction, the package-local gate is a fresh independent re-review
in a separate session.

## 8. Correction record (2026-09-22)

| Finding | Correction |
|---|---|
| F-01 | `CONTEXT.md`: the pre-existing global `NEXT` is restored as the final line; the D9 review gate is recorded separately as package-local; preservation statements are corrected (Section 6). |
| F-02 | Plan Section 12 preamble: Section 12.6 is listed as a historical validation record only, and its `NEXT` is stated to remain the current global gate, not satisfied. |
| F-03 | Plan canonical state: the raw-output/IPC ceilings are stated as still `OWNER_SELECTED_CANDIDATE_ONLY`; the stdout/stderr approval is stated separately, superseding `SEPARATE_ENFORCEMENT_APPROVAL_REQUIRED` for stdout/stderr only. |
| F-04 | Plan Section 12 preamble: "Section 11 `CURRENT` is canonical." is restored; the Section 11 addendum is stated to be status-neutral and not a canonical current-state source, with no second global `NEXT`. |
| F-05 | Plan header: "D9 package correction" is restored; the preparation report's "pure rewrap" claim is corrected. |
| F-06 | Plan Section 11 addendum: "(Section 2, above)" becomes "(Section 9, above)". |
