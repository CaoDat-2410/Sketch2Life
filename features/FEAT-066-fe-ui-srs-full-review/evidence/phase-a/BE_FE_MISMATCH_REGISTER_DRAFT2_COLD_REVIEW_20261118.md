# FEAT-066 A-1 BE–FE mismatch register Draft 2 — cold review (round 2) — 2026-11-18

- **Reviewer:** a Claude subagent with a fresh context, model Sonnet 5.5. The caller requested effort high. The reviewer reported that its prompt gave no explicit effort level, so it cannot confirm "high". It worked read-only by instruction and was started on the owner's instruction ("Review cả hai").
- **Scratch output:** read-only helper scripts and output only, in `tmp/feat066-register-review-d2/` (`cnt.py`, `cmp.py`, `m.py`, `p4out.txt`).
- **Pin reviewed:** `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT2_20261118.md`, 31,860 bytes, SHA-256 `274B21322052A3375A95D86328E80CCC163211BC66BBF31A9C717FECE82FBEAD`.
- **Other pins that matched:** P2, P3, P4, the addendum, roadmap Draft 4, the A-4 brief, Draft 1 and its review record, the `map_p4.py` output, the corrected Rev52 pin (read from the web worktree) and the M2 freeze (`b72228ce…`).
- **What the reviewer did not do (its statement):**
  - It ran no tests, builds, validators, linters, network calls, Bruno runs or state-changing git commands.
  - It opened no `.env`, `.url`, secret or Bruno environment file, and did not open `parentSrsBehavior.test.ts`.
  - It changed no repository file.
- **Verdict:** READY WITH NOTES — **P1=0, P2=3, P3=7**. P1+P2 fell from 5 to 3. The reviewer asks for the three P2 items to be fixed before the register is used as the L3 input for slice approvals.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Round-1 findings (reviewer)

| Finding | Status | Note |
|---|---|---|
| R1-01 | partly | R2-01 |
| R1-02 | resolved | Rule 1 itself reclassifies M17, M18, M20 and M22 (R2-03) |
| R1-03 | resolved | The §7 wording is still wrong (R2-03) |
| R1-04 | resolved | — |
| R1-05 | resolved | — |
| R1-06 | resolved | — |
| R1-07 | resolved | — |
| R1-08 | resolved | — |
| R1-09 | partly | R2-08 |
| R1-10 | resolved | — |
| R1-11 | resolved | A new slip: R2-05 |
| R1-12 | resolved | — |
| R1-13 | resolved | — |
| R1-14 | resolved | — |

## P2 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| R2-01 | §0 "Every NV mark … is carried" | The claim is false. Dropped NV marks:<ul><li>P3 "runtime or complete error statuses NV" on M12, M13, M15, M16, M19 and M21. It is kept only on M17, M18 and M20.</li><li>A06: "does §21.1 apply to the scope snapshot".</li><li>A05 says "not an SRS mandate" where P2 says NV.</li><li>M25: "status/DTO NV".</li></ul> | Add the marks, or name the exceptions in §0 |
| R2-02 | §4/§6 vs §2/§5 | D-171 item 7 (verified in the freeze) marks CB and CD for later deprecation. The 10 touched CB rows (A06–A10, B01–B04, C01) and C02 (PO+CB) still get fix slices. O-L3SCOPE covers only the untouched CB operations, and the register does not say so | Extend O-L3SCOPE to those rows, or add a row note that they sit on a surface the freeze marks for deprecation |
| R2-03 | §1 rule 2; §7 "none left" | The claim "no reclassification left" is untrue:<ul><li>M17, M18, M20 and M22 move from FIX-BE to CONN under rule 1, without an "RC:" mark.</li><li>A10, A12, A13, B02 and B09 lead with OD where the audit leads with FIX-FE or FIX-BE, while A05 leads with GAP.</li><li>A24 gains "also OD" and O-UPLOAD, though the 202 completion is SRS-specified and P2 classes it FIX-BE only.</li></ul> | Mark these "RC:", state a tie-break rule, and drop OD from A24 or justify it |

## P3 findings (summary)

| ID | Finding |
|---|---|
| R2-04 | The §5 G0 gate says "ENV-P1 (done), P1 run". The pinned addendum still lists ENV-P1 as open. The register omits that the P1 rerun stalled and that G0 is blocked on O-P1-STALL. |
| R2-05 | §4 CD row: "renderer" is wrong. P3's demo list includes `POST /v1/sessions/{session_id}/renderer/launch`, a CD operation. |
| R2-06 | §6 lists O-SEQ, O-2a..c and O-SRS, which no row cites, and omits O-SEED and O-MOB. B01/G01 omit O-2a (Draft 4: W-CAP is blocked until O-2a). There is no note on why O-L3SCOPE grows from the addendum's 44 to 86. |
| R2-07 | Cited but not pinned: the M2 limitation ledger (17,463 B, `a82335ec…`), the freeze document, `SOURCE_REGISTER.md`, Billing Draft 7 and the conventions draft. The header's "Sonnet 5.5 high" differs from the round-1 record, which says the reviewer reported default effort. |
| R2-08 | The addendum asks for a per-row next owner. Draft 2 gives owners by slice type only, and G0, CONV-1, C-M and W-* are not mapped to owners. |
| R2-09 | <ul><li>C-M gate omits G0 and CONV-1.</li><li>C-T adds A21, A23 and C01 beyond the addendum.</li><li>MG01 "no BE route" sits next to P4's six `dev`-only routes.</li><li>B02's "use the drifted path" is firmer than P4's "candidate".</li><li>M2 codes OS and OO are missing from the legend.</li><li>M2 ledger O1 (the 11 OO operations with no current authority) is not cited.</li></ul> |

## Checks (reviewer)

- **§2 recount:** 10 / 12 / 13 / 1 / 5 (41).
- **§3 recount:** 16 / 5 / 2 / 4. Path counts: exact 17, counterpart 6, none 4. The M2-allowed 8 are correct.
- **`map_p4.py` re-run:** 151 rows parsed; the Bruno column matched on all 69 rows.
- **§4:** 63 touched / 88 untouched, with the split and the 83 PARTIAL / 5 MISSING confirmed.
- **§5:** coverage is complete.
- **Citations that hold:**
  - M2 ledger O2, O3 and O4;
  - D-171 item 7;
  - the `SOURCE_REGISTER.md` Rev78 entry;
  - the Draft 4 L3 quote;
  - the A-4 brief;
  - C-D1 to C-D10.
- **Rules kept:** no "ready" claim, no resolved owner decision, no cross-inventory totals beyond the defined union, no local absolute paths.

## Not verified (reviewer)

- Row content against the source code.
- The MGR-8 runtime effects.
- SRS clause numbers.
- Billing Draft 7 content.
- The owner's chat answers.
- Whether M26, M27 and A03–A05 should be GAP, given M2 ledger O1.

## Disposition by the coordinating session

Draft 2 is not edited. A Draft 3 that fixes R2-01 to R2-09 is proposed to the owner. This was round 2 under D-171 item 11. The P1+P2 count fell, so a round 3 is allowed.
