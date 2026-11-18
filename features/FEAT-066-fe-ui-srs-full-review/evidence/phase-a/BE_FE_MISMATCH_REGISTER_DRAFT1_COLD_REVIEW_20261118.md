# FEAT-066 A-1 BE–FE mismatch register Draft 1 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5. The caller set effort to high; the reviewer reported "effort not set explicitly in the prompt (default)". Read-only by instruction. Started on the owner's instruction ("làm theo đề xuất").
- **Scratch output:** one file, `tmp/feat066-register-review-d1/m.py`, a copy of the coordinator's mapping script that lists the 88 untouched operations.
- **Pin reviewed:** `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT1_20261118.md`, 25,303 bytes, SHA-256 `3F89EB1DD1650132170D0BDE103CEFBB0E52C4702381EB86692F384FB7BD8842`. These pins also matched: P2, P3, P4, the addendum, roadmap Draft 4 (`63710A9F…`) and the canonical SRS (`B9B1F42D…`).
- **What the reviewer did not do (its statement):**
  - no tests, builds, validators, linters, network, Bruno runs or state-changing git;
  - no `.env`, `.url`, secret, Bruno environment file or `parentSrsBehavior.test.ts` opened;
  - no repository file changed.
- **Verdict:** READY WITH NOTES — **P1=0, P2=5, P3=10** (14 findings). The reviewer asks that the five P2 items be fixed before the register is pinned as Draft 2 or used for slice approvals.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| R1-01 | §2 rows A11, A12, A16, A17, A20, A21, A24, A25, A27; §3 rows M14, M22, M23 | NOT VERIFIED marks from P2 and P3 were dropped. This applies to the response-DTO and alias comparisons, the M14 response DTO, and the M22/M23 presentation callers. A17, A20 and A27 read cleaner than the audit. | Restore the marks per row or in a column. |
| R1-02 | §1 CONN definition vs §2/§3 | Rows whose only defect is the global item E are classed inconsistently. Web E-only rows are CONN, while mobile E-only rows (M17, M18, M20, M22, M26, M27) are GAP, so mobile CONN is 0. One operation gets two primaries: A01 OD vs M27 GAP, and WP CONN vs M15 FE. "GAP (E)" is repeated although §1 says E is not repeated per row. | Use one rule, for example an "E-only" marker. Give one primary per operation, or state that it differs by caller. |
| R1-03 | §3 M12, M13, M23, M24; §7 | Classes differ from P3 without a note. P3 classes all four as FIX-FE; the register has M23 as OD and M24 as COND, with FE dropped from M24's "Also". M12 and M13 gain an "Also OD" that P3 does not give. §7 claims "Also" keeps the audits' classes. COND does not match M24's evidence, which is a legacy flow blocked by M2. | Annotate each row as a coordinator reclassification, restore FE for M24, and fix §7. |
| R1-04 | §5 "Parent Lesson Library slice"; §3 M15–M22 | A new slice, absent from Draft 4 and the addendum. It is gated only by B-1, yet the mobile work also needs O-MOB2, O-9, mobile branch reconciliation and an allowlist decision, because these routes are outside the M2 projection. | Mark it PROPOSED and add those gates. |
| R1-05 | §3 M09 | "(owner: does not block)" implies a decision that no source records. The `[PROPOSAL]` summary is OPEN in M2 ledger O3. The M2 closure's "does not block" concerns the `request_id`/`current_version` reading. | Replace with "OPEN (M2 ledger O3); not decided". |

## P3 findings (summary)

| ID | Finding | Smallest fix |
|---|---|---|
| R1-06 | PX does not apply to A02 either. The M2 exemption is ambiguous for M04/M05/M08/M11, whose called paths are `/api/parent/v1/...`. M12/M13 lack O-9/O-0 in "Blocked by". | — |
| R1-07 | The M2 envelope exemption rests on the extra fields that M2 ledger O4 leaves for Person 2 to confirm. | Cite O4. |
| R1-08 | §5 L2: G10 and MG09 are one capability ("3 IDs / 2 capabilities"). B-1 has "8 primary" for 7 operations (A01 = M27). | Restate both counts. |
| R1-09 | No per-row owner, although the addendum's A-1 acceptance asks for one. "Every slice is Person 2's" conflicts with the addendum's "Person 2 / CaoDat (BE)". MWO is defined but unused. | — |
| R1-10 | The Bruno status codes have no legend, so PARTIAL reads as "partly covered". The addendum and roadmap are not pinned in §0. Addendum C-03 ("correct in A-1") is not carried over. | — |
| R1-11 | The CD row maps 35 operations to mobile `src/demo/api.ts` without evidence. O-L3SCOPE covers only 44 of the 88 unaudited operations. D-171 item 7 (CB/CD are compatibility surfaces to be deprecated) and M2 ledger O2 (cancel) are not cited. | Mark the CD mapping NOT VERIFIED; widen O-L3SCOPE or justify it; add the citations. |
| R1-12 | "Catalog-first" (M25) comes from the source register and needs a citation. | Reword "no route defect" to "no route-specific defect recorded" (§5 B-5 heading). |
| R1-13 | Dropped header facts: M26 sends no bearer or key, and BE adds `email_verified`; M27 sends no X-Request-ID. | — |
| R1-14 | "Touched" in §4 includes 6 operations reached only through counterpart paths. | Define it as "audited or mapped". |

## Checks (reviewer)

- **Script:** ran as specified; parsed 151 rows. Every web template, the probe and every mobile row with a frozen operation matched. The Bruno column matched on every row checked. Stale 004/005 and the 5/8 Parent count agree.
- **Coverage:** every P2 and P3 row and gap is present. The summaries are faithful apart from R1-01 and R1-13.
- **Recounts:**
  - §2: 10/12/13/1/5.
  - §3: 14/6/6/1; exact 17, counterpart 6, none 4.
  - §4: 63 touched / 88 untouched; split CB 44, CD 35, LE 3, PO+CB 4, T 1, PR 1; Bruno 83 PARTIAL / 5 MISSING.
  - §5: every row is covered once, with correct counts.
- **Rules:** no "ready" claims; no cross-inventory totals; no owner decision resolved; no local absolute paths. The `tmp/…`-relative references would break if the document moved into the repository.

## Not verified (reviewer)

- P2 and P3 row content against the source code.
- Runtime behaviour of the six dirty MGR-8 files.
- SRS clause numbers beyond §21.1 and the video-quota row.
- The owner's chat answers.

## Disposition by the coordinating session

Draft 1 is not edited. Register Draft 2, fixing R1-01 to R1-14, is proposed to the owner. This was review round 1 for the register.
