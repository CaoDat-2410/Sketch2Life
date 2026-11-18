# FR-C-08 Allowlist Draft 2 — Independent Cold Review

**Review date:** 2026-11-15  
**Verdict:** CHANGES REQUIRED — 0 P1, 2 P2, 1 P3  
**Boundary:** Read-only plan review. This report is not implementation approval or launch authorization.

## Review identity and scope

- Worktree: .worktrees/m2-s2
- Branch: feature/feat063-m2-s2
- HEAD: 5de30674bc826591ad4b3cc00fca53c7597ead51
- Reviewed target: features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT2_20261115.md
- Target observation: 56,894 bytes; SHA-256 6D0A79408446A4D72A098965CCC78E7ED9FE5E0DE8D065C0DC1BCA1B3B347E70 — MATCH
- The designated report path was absent before review. The worktree was already dirty; only the report path was created.

## Findings

### P2-01 — Classify named-owner assignment as a launch gate

**Target:** §5, issue 4, line 197; compare the B/G definition at line 190 and implementation gate 3 at line 311.

The effect column labels named-owner assignment “B before launch.” The document defines B as an implementation blocker when the answer affects behavior or requires an unapproved contract/schema change, while D-208 requires named accountable owners before launch. The target’s own §9 lists owner assignment as a separate before-launch gate. This makes the blocker/gate classification inconsistent and risks moving the owner deadline earlier than D-208.

**Suggested fix:** Change the effect to “G before launch; names remain OPEN.” Keep the technical owner/contract questions open, and retain the statement that D-208 does not require names before proposing this allowlist.

### P2-02 — Correct the approval-ledger summary

**Target:** §2, TASK_APPROVAL.md input row, line 27.

The row says the pinned approval ledger “Contains S2 approvals only.” The current ledger also records a separate, limited FEAT-047 artifact-metadata overlay and one combined S2 verification authorization (TASK_APPROVAL.md lines 2897–2904). Those authorizations do not approve FR-C-08, so the row’s conclusion is correct but its description of the ledger is incomplete.

**Suggested fix:** State that the ledger contains the D-205/D-207 M2 approvals plus the separate FEAT-047 verification overlay, and that neither authorizes FR-C-08 implementation.

### P3-01 — Do not attribute completed-only eligibility to Allowlist Draft 1

**Target:** §2, Allowlist Draft 1 input row, line 31.

The row calls the historical allowlist’s wording “completed-only DELETE text.” The pinned Allowlist Draft 1 does not define DELETE eligibility as completed-only; its parent-router row says no Teacher route, completed-delete route, progress route, or new path is selected (Draft 1 line 27). That is a path-selection boundary, not an eligibility rule. The current Rev68/D-208 requirement remains clear in Draft 2.

**Suggested fix:** Describe Draft 1 as a historical proposal that did not select a completed-delete route. If the intended reference is a completed-only rule in a companion historical specification, cite that specification explicitly and keep it historical.

## Verified items

- The canonical working source is Rev68 under D-203/D-208 and remains unsigned. The target uses the current SRS authority pointer and does not treat the draft as formal sign-off.
- The operation matrix matches Rev68 UC-11: exactly 13 unfinished cancel states; explicit user-requested DELETE for COMPLETED, FAILED, and ABANDONED; no automatic purge of FAILED/ABANDONED; no new cancel/delete command for DELETE_PENDING or DELETED; DELETE_PENDING remains public until purge is verified, and DELETED follows verification only. The 18-state inventory excludes SCRIPT_GENERATION_UNKNOWN.
- Current Parent ownership or current Teacher assignment/version is required. Former Teacher status and creator provenance alone confer no authority. The target covers immediate access revocation, best-effort job/provider cancellation, late-result fencing, owner-module purge, independent-reference verification for shared assets, quota preservation, and Teacher SAMPLE_USED/claim-time preservation.
- Audit is limited to metadata categories and exclusions in Rev68/D-208. Audit-reader permission, physical field mapping, and the 180/365-day record-type mapping remain open. Parent lifecycle requests remain typed PARENT_ACCOUNT; the target does not invent organization_id, a route, field, receipt schema, event, state, DDL, or retention exception.
- The nine issue themes carried from Lifecycle Plan Draft 2 §7 and Specification Draft 3 §8 are represented in target §5; the Parent-scope/receipt and named-owner parts of the former issue 3 are split into separate questions. The Core Asset reference/deletion gap is explicit, with no guessed Core path. Read sufficiency, current-assignment authorization, revocation evidence, state compatibility, M2 reconciliation, and audit mapping each have an owner question and effect status. P2-01 covers the named-owner status inconsistency.
- Candidate paths are proposals only. The E list is not permission to edit every row; dirty M2 and FEAT-047 collisions are identified, and the target notes that the current Core metadata/reference operation is missing. No migration is E or N, no source-schema mapping is fabricated, and the seven migrations are frozen source references only.
- The Draft 3 cold-review timing note is addressed as proposed sequencing. The target follows D-208’s M2-before-implementation and named-owners-before-launch boundaries without assigning a person or date.
- Every future command in §8 is marked PROPOSED / NOT AUTHORIZED / NOT RUN and has an explicit ceiling. Pytest commands use a fresh GUID child beneath the existing ignored repository-root temp parent and disable pytest’s cache provider. The parent and pinned Python 3.12 executable exist. The target discloses the OpenAPI tag failure and prior pytest temp/cache access errors; M2 command ceilings are not transferred.
- The status is PROPOSED / BLOCKED FOR IMPLEMENTATION / NOT APPROVED / NOT LAUNCHED. D-205/D-207 and the M2 approval do not authorize FR-C-08. The M5/M6 roadmap is treated as historical sequencing context, not current SRS authority.

## Pins checked

- Worktree, branch, HEAD, target byte count, and target SHA-256: all match the requested observations.
- §2 planning inputs: 20 of 20 byte counts and SHA-256 values match.
- §4.1 E paths: 33 of 33 observed byte counts/SHA-256 values match, and recorded clean/dirty states match current Git status.
- §4.2 N paths: all 9 are absent.
- §4.3 frozen non-migration H paths: all 23 current byte counts/SHA-256 values match. The seven frozen migration pins also all match. No migration graph, applied revision, or database contents were queried.
- §7 collision register: all 11 current dirty-source observations match. The 11 historical D-207 byte/hash pairs match the corresponding values in the pinned M2 allowlist. No pin mismatch was found.

## Limitations

No tests, validators, builds, backend/runtime, database, migration, Docker, install, network, provider, Modal, Android, emulator, staging, commit, or push command was run. This review does not establish runtime behavior, effective permissions, token/cache/upload invalidation, provider cancellation, object deletion, migration application, or database contents. The SRS is unsigned; the Parent-scope/receipt, Core Asset, named-owner, lifecycle-read, and audit/retention gates remain open.
