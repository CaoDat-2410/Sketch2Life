# FEAT-066 A-1 BE–FE mismatch register Draft 3 — cold review (round 3) — 2026-11-18

- **Reviewer:** Claude subagent with a fresh context, model Sonnet 5.5, told effort high. It worked read-only by instruction and was started on the owner's instruction ("Review register Draft 3 đi"). Its only scratch output is `cmp.py` and `p4out.txt` in `tmp/feat066-register-review-d3/`.
- **Pin reviewed:** `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT3_20261118.md`, 38,979 bytes, SHA-256 `5EE28948AB3EBC9FD599B994EED556D5C945532AE3629D819DB4FFDB8F33ECB3`. Also matched:
  - all 13 §0 inputs;
  - the MGR-8 evidence note (`BCDACA87…`);
  - the earlier drafts and their review records.
- **What the reviewer did not do (its statement):**
  - It ran no tests, builds, validators, linters, network, database, Docker or Bruno, and changed no git state.
  - It opened no `.env`, `.url`, secret or Bruno environment file, and not `parentSrsBehavior.test.ts`.
  - It edited no repository file.
  - In the `mgr8-diag` outputs it read only the exit-code file and grepped the pass and timeout lines.
- **Verdict:** READY WITH NOTES — **P1=0, P2=0, P3=8**. P1+P2 fell from 3 to 0.
  - Two classes from round 2 recur at P3 level: an unmarked RC (R3-01) and the absolute "every NV mark carried" claim (R3-02).
  - The reviewer recommends fixing the P3 items by a direct edit and closing the register, without a round 4.
  - It finds the register fit as the L3 input for slice approvals once R3-01, R3-02 and R3-03 are fixed. No finding changes any count or slice membership.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Round-2 findings (reviewer)

| ID | Status | Note |
|---|---|---|
| R2-01 | partly | R3-02 |
| R2-02 | resolved | — |
| R2-03 | partly | A21 is missing an RC mark (R3-01) |
| R2-04 | resolved with a caveat | R3-03 |
| R2-05 | resolved | — |
| R2-06 | resolved | — |
| R2-07 | resolved | — |
| R2-08 | partly | R3-04 |
| R2-09 | resolved | — |

## P3 findings

| ID | Finding | Smallest fix |
|---|---|---|
| R3-01 | A21: P2 leads with "OK" and names OD only for path mapping, so the OD primary needs an RC mark, and §7 should list A21. | Add "RC: tie-break (P2 leads with OK)" and list A21 in §7 |
| R3-02 | §0 still claims "every NV mark … carried". Not carried: P2's MGR-6 R3 verdict NV (G06, A12, A13) and P3's NV on request emission for declaration-only methods. | Add these marks, or name the exceptions |
| R3-03 | §5 G0 / §6 O-P1-STALL: "owner chose a diagnostic run" is not in any pinned file. The reviewer also saw `tmp/feat066-phase-a/mgr8-diag/` outputs timestamped 15:47–15:49: d1 exited 0 with 8 passed, and d2 shows "Timeout (0:02:00)". So "pending" may be stale, and these outputs are not recorded as evidence. | Cite the owner's choice and state the diagnostic status |
| R3-04 | §1 Owners maps the C-T and C-A BE parts to "Person 2 / CaoDat", while the addendum has Person 2 only; the departure is not noted. Some Next-slice labels have no owner mapping: Parent Lesson Library, "new … slice", M9-C. | Note the departure and add the missing mappings |
| R3-05 | §5 gate cells omit O-L3SCOPE for A06 (CONV-1), A08 (BRU-0) and B01 (L2). BRU-0 rows A17, A20, A22, A26 and A27 omit G0, although G0 is a prerequisite for every Lesson Library row. | Add the gates, or state the inheritance |
| R3-06 | M26 and M27 stay GAP while M17 and the other E-only rows are CONN. This is defensible, because of the FE header gaps beyond E, but unexplained. | One sentence in rule 1 |
| R3-07 | The OO surface note says "their GAP or OD class", but the OO rows also include FE (M23, M24) and COND (AI1–AI3). | Write "their class" |
| R3-08 | The header "Reviews" sentence reads as if it covers round 1 only. | Reword |

## Checks (reviewer)

- **Tie-break audit of every row:** consistent except A21. A09 leads with OD in P2, so it needs no RC. The COND rows follow P2's own wording.
- **Recounts:**
  - Web: 10 / 11 / 14 / 1 / 5.
  - Mobile: 16 / 5 / 2 / 4.
  - Path counts, the M2-allowed 8, the §4 63/88 split and the §5 queue counts all match.
- **Script re-run:** `map_p4.py` matches the Bruno column on all 69 rows.
- **Citations verified:**
  - M2 ledger O1–O4;
  - D-171 item 7;
  - Rev78 (source register line 703);
  - the C-03 pin;
  - the A-4 brief facts;
  - the MGR-8 note contents.
- **Rules kept:** no "ready" claims, counts per inventory, no owner decision resolved by a row (apart from R3-03's wording), no local absolute paths.

## Not verified (reviewer)

- DTO, status and SRS content against the source.
- The canonical SRS pin (the file was not located by the reviewer).
- Billing Draft 7 content.
- The owner's chat answers.
- Who authorized the diagnostic run.

## Disposition by the coordinating session

Draft 3 is not edited. The reviewer recommends closing with a direct P3 fix and no round 4. The owner decides between two options:
- a Draft 4 with the eight P3 fixes, and no review;
- accepting Draft 3 with these notes.
