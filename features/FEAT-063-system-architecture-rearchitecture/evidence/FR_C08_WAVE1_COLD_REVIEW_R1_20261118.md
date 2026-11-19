# FR-C-08 wave 1 — independent cold review, round 1 (2026-11-18)

Record only. This note decides nothing for the owner and approves nothing. It is a new file; no existing record was edited.

## 1. Reviewer identity and one open caveat

- Reviewer: a fresh subagent started by the coordinating Claude session (Opus 5.5) with the model set explicitly to Sonnet 5.5 and the effort parameter set explicitly to "high" in the start call. It reported its model as `claude-sonnet-5-5`.
- Caveat: the reviewer states that the reasoning-effort value visible inside its own session was the numeric value 10, not the label "high", and that it cannot confirm "Sonnet 5.5 high". The coordinator cannot verify which effort was actually applied. Under the repository reviewer rule this round counts only if the owner accepts the effort as satisfying "high"; otherwise round 2 must be treated as the first valid review. This caveat must not be dropped when this note is cited.
- Scope: read-only. The reviewer created and edited nothing, and ran no test, validator, build, database, Docker, network or Modal command.

## 2. Reviewed documents (all pins matched before review)

All in `features/FEAT-063-system-architecture-rearchitecture/plan/`, untracked, planning-only:

| Document | Bytes | SHA-256 |
|---|---:|---|
| FR_C08_LOST_DRAFTS_NOTE_20261118.md | 3,505 | FB972C6D465DC29C5BD00CBE6A0B52A1DF199C5D0211AE98F8B2A5B29D43598A |
| FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT4_20261118.md | 14,866 | ACDC306E79FE1C7AF5CAB6DB46125B75240D9A5C54483F92B3E6C828B93DAE92 |
| FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT6_20261118.md | 18,356 | 724C23DBD822451622312B9B7ECB324713F14DA244938EBA7C6308F6E03A6823 |
| FR_C08_OWNER_QUESTIONS_20261118.md | 12,610 | 1F642E6428958A0E1A8F4216BEDC54EBE051802782F0092A7EB4E7064DCB8D31 |

Producer's pin audit, local and git-ignored: `tmp/frc08-wave1/PIN_AUDIT.md`, 19,629 B, `D106286495AFD9E31688C14F9171B4A84F64376D78D378186F385FF4C02E491C`.

## 3. Verdict: NOT READY — P1 1 / P2 4 / P3 11

Pin check by the reviewer: 142 unique paths re-hashed (all 88 audit rows plus the 4 outputs and all 97 pin occurrences in Allowlist Draft 6); one malformed pin; the 9 candidate N paths are absent; the working tree equals HEAD `08439b22` for the pinned source.

Clean areas reported: hygiene (no dollar sign, no absolute path, no CRLF, no BOM), SRS quotation fidelity (every quotation in the owner questions matches its stated line), source facts about the existing Parent cancel, M2 status wording, and no decision taken for the owner.

## 4. Findings

Verification column: "coordinator-verified" means the coordinator re-checked the point read-only after the report; "reported" means taken from the reviewer without a second check.

| ID | Sev | Where | Finding | Verification |
|---|---|---|---|---|
| R1-F1 | P1 | Allowlist line 5; Owner Questions Q-BASE lines 78-85 | The documents call the latest CONV-1 package an "unreviewed draft" and frame the base-branch question as waiting for its approval. The FEAT-066 records in the working tree say it was reviewed and owner-approved (D-066-71, FEAT-066 TASK_APPROVAL status `APPROVED_FOR_IMPLEMENTATION`, not launched; branch `feature/feat066-conv1` exists locally at `08439b22`). The "unreviewed" premise came from the coordinator's own task brief and is stale. The approved CONV-1 file set also touches shared files such as `app.py` and routers, so an overlap with the Allowlist E rows needs a line. Those FEAT-066 records are uncommitted in the working tree. | Coordinator-verified (status lines found at FEAT-066 DECISIONS.md line 434 and TASK_APPROVAL.md; "unreviewed" at Allowlist line 5 and Q-BASE line 81) |
| R1-F2 | P2 | Allowlist line 30 (`domain/ai_jobs/model.py` row); PIN_AUDIT.md line 66 and its "Mismatches: 0" statement | A 62-character SHA-256 (`512B604636C1A22E231AC3276D3E537AE0DE4D9BB6652CCB064FAB7314DB99`). The real value is `512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99`. The audit marks the row MATCH, so its "Mismatches: 0" claim is false. This is the same defect class that stopped the 2026-11-16 review. | Coordinator-verified (hash recomputed; string length 62 at both locations) |
| R1-F3 | P2 | Owner Questions Q-A lines 5-14; Contract line 12 | Q-A evidence is incomplete. It omits D-208 item 6 (owner disposition 2026-11-15: explicit DELETE permitted for COMPLETED, FAILED and ABANDONED; FAILED and ABANDONED never purged automatically) and the SRS lines that keep FAILED and ABANDONED content until the user deletes it (lines 383, 656 NFR-31, 1064, 1350, 1372, BR-39 at 283). The recommendation "A until the owner clarifies" has no stated trade-off: under A, ABANDONED content would have no user-triggered lifecycle deletion route. Q-A stays open. | D-208 item 6 text coordinator-verified; the SRS line citations are reported |
| R1-F4 | P2 | Contract section 5, bullet at line 69 | The idempotent replay and changed-payload rule ("same key and payload replays; changed payload returns 400 `INVALID_IDEMPOTENCY_KEY`") is attributed to D-066-68 but is not in it. D-066-68 C-D5 covers one 1-128 ASCII value and a missing key giving 400 `INVALID_REQUEST`; C-D6 covers durable receipts. The rule comes from SRS section 21.4 line 1697 and the M2 source. | Reported |
| R1-F5 | P2 | Contract sections 3.1, 4 and 6; Owner Questions | State-set reconciliation has no owner question and is missing from the blocker list. M2 cancel accepts 7 source states, 5 inside the SRS 13-state cancel-eligible set; 8 eligible states are rejected with 409 `INVALID_STATE_TRANSITION`; 2 source-only states are outside the SRS; the response literal lacks ABANDONED and DELETED. | Reported |
| R1-F6 | P3 | Lost Note line 18, Contract line 97, Allowlist sections 3 and 6, PIN_AUDIT line 6 | The pin register is git-ignored and local-only, so references to it do not resolve in a clone; the audit counts are wrong (88 existing rows and 92 total, not 87 and 91); pins of uncommitted FEAT-066 files are not marked as such. | Reported |
| R1-F7 | P3 | Lost Note line 24; Contract section 2 line 18; Allowlist section 1 line 11 | M2 closure sources are cited by heading only. Add TASK_APPROVAL.md lines 3243-3247 and STATUS.md line 876. | Line numbers coordinator-verified earlier in the session |
| R1-F8 | P3 | Contract line 12 | D-209 item 4 names UC-07 and section 21.2, not FR-C-08. | Reported |
| R1-F9 | P3 | Contract section 3.3 line 40 and section 6 line 76 | Directive wording ("should use the existing owner-scoped GET by default"; module responsibilities) leans toward options that stay open. State that these carry D-208 directions allowed by D-209 only where consistent. | Reported |
| R1-F10 | P3 | Owner Questions Q-READ lines 35-42 | Omits the SRS definition of the GET read (lines 780, 805, 1164, 1811: StoryRunDetailV1 with a timeline) and the owner's M2 disposition at TASK_APPROVAL.md line 3250 (missing timeline recorded OPEN-OWNER, not blocking). | Reported |
| R1-F11 | P3 | Owner Questions Q-BASE lines 78-81 and Q-OWNERS lines 87-91 | The attached SRS quotations (line 1674, line 1472) do not support the question and the documents say so. Replace with the relevant governance records or drop the quotation. | Reported |
| R1-F12 | P3 | Allowlist section 2 lines 30, 37-39; section 6 lines 108-111 | Four E rows carry guards that forbid any edit (`be1_models.py`, `story_run_lite/tables.py`, `lesson_library/tables.py`, `ai_jobs/model.py`) and look like H rows. No path covers Core reference-closure or Teacher assignment authorization; `be1_parent_role_adapter.py` is cited as a current-assignment resolver but only reads a Parent role. | Reported |
| R1-F13 | P3 | Allowlist lines 9 and 11 | "OPEN under D-209 Q-A" mixes D-209 with the owner-question ID; "R2 planning preflight" refers to a prompt the reader does not have. | Reported |
| R1-F14 | P3 | All four documents | 36 lines end with two trailing spaces (Lost Note 1, Contract 3, Allowlist 2, Owner Questions 30). `git diff --check` would flag them; not run. | Reported |
| R1-F15 | P3 | Lost Note lines 8 and 18; Contract section 2 | The rollback claim ("five verified task-created files") has no cited source; the lost-draft branch `feature/feat063-m2-s2` still exists at `bc124187`; no disposition for Spec Draft 4 and Lifecycle Plan Draft 4, which still carry the D-208 eligibility reading; no statement whether the D-208 item 8 gate counts as met by the M2 closure. | Reported |
| R1-F16 | P3 | Contract section 4 | No source-fact row for Teacher-side authorization. | Reported |

## 5. Not verified by the reviewer

The effort setting (section 1); FEAT-066 package content (read only for status claims) and any file-set collision between the approved CONV-1 allowlist and the Allowlist E rows; runtime, database, migration, OpenAPI and test evidence (none exists or was sought); whether `be1_registry.py` or `openapi_contract.py` carries a Teacher assignment resolver; the source of the rollback claim; `git diff --check`.

## 6. Round count and next step

Round 1 of at most 5. P1 + P2 = 5. Stop rule: stop and ask the owner if a finding class repeats or if P1 + P2 does not fall. A remediation prompt for round 2 is prepared in `.claude/handoff/` by the coordinator; the owner decides whether to run it. No document under review was edited by the reviewer or by the coordinator.
