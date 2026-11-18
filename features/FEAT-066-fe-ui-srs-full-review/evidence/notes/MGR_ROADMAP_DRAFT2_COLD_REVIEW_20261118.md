# FEAT-066 Manager API roadmap Draft 2 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort set to high by the caller, read-only by instruction (scratch folder `tmp/feat066-roadmap-review/` created, left empty). The only review round allowed by the owner's replan handoff. Started by the coordinating session (Opus 5.5).
- **Pin reviewed:** `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT2_20261118.md`, 28,657 bytes, SHA-256 `01EAF97E077A19A31199F00E1828D9D98CD364442A6F32D69182D1D79F61B07D`. Pin check passed; the handoff was read in full.
- **What the reviewer did not do (its statement):** no file modified, created or staged outside its scratch folder; no fetch, test, validator, network or database use; the gate secret directory not read. Read-only Git, `sha256sum`, `wc`, Read and Grep only.
- **Verdict:** NOT READY (small corrections) — **P1=0, P2=5, P3=9**. No finding misstates a gate or authorizes anything; the P2 findings are text corrections that do not change the roadmap structure. Under the handoff, the work stops here and returns to the owner; no further review cycle is proposed.
- **Re-verified by the reviewer:** Draft 1, the MGR-2 to MGR-7 plan pins, the MGR-1 disposition, seven review and brief hashes, the MGR-9 plan, its R2 review and the Rev52 audit; the adopted SRS (byte-identical to the blob on `origin/feature/feat063-m2-parent-teacher-foundation`), the Rev60 SRS and `SRS_AUTHORITY.md`; the MGR-8 diff stat and the six per-file pins in Draft 1; both worktree identities and counts (BE untracked now 35 including Draft 2); the M2 branch facts; D-209 and the exact owner quote; every adopted-copy line number in §0. The absence of any repository record of the MGR-8 command authorization was confirmed.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Draft 2 location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| F-01 | §0 "Consequence" | States that MGR-2, MGR-3, MGR-5 and MGR-6 carry a Rev69 crosswalk addendum; MGR-5 has none, and MGR-4 (also citing Rev60) is omitted. Addenda exist only in MGR-2, MGR-3 and MGR-6. | Name MGR-2/3/6 only; add that MGR-4/5 cite Rev60 with no comparison. |
| F-02 | §0 and O-SRS | The basis switch is not reconciled with recorded FEAT-066 text: D-066-63 and the MGR-1 note say the repository authority remains Rev60 and scope the adopted copy to MGR-2; the MGR-2 and MGR-3 plans say the same. | One sentence in §0 listing those statements as superseded by the owner's selection once O-SRS is recorded. |
| F-03 | §1 "Git note" against §10 | The disclosed `git fetch -q origin` was a deviation from the handoff ("Do not fetch"; no network commands), and §10 says no network command ran — a contradiction. | State plainly in §1, §10 and the report that this was a boundary deviation (remote-tracking refs only). |
| F-04 | §6.1 | The two command strings are presented as the owner-authorized commands; the handoff names the commands only by description ("contract + unit tests, then the Lesson Library integration test"); the strings are Draft 1's proposal. | Mark them as Draft 1's proposal, to be confirmed against the owner's authorization text before running. |
| F-05 | §8 O-0, O-SEQ, §5.3 | The O-0 recommendation has no SRS or source basis, ties S-LL to a separately instructed merge, says "rebased" for uncommitted work, and asserts a conflict that is only possible (the S-LL and M2 hunks in the catalog test are adjacent). O-SEQ rests partly on judgment ("narrowest"). | O-0: no recommendation, depends on merge logistics; "may conflict". O-SEQ: keep only the evidence-based reason (no Billing service). |

## P3 findings (summary)

F-06 the cross-lane numbers are wrong: `app.py` 130 insertions / 105 deletions (235 changed lines), the catalog test 59 / 4 (63 changed). F-07 the MGR-5 R1 report has a second P2 (consent-list pagination against §21.1, still open in the plan) and holds the superseded MGR-6 R1 (CHANGES REQUIRED with a P1 on an older pin). F-08 the overlap table is called "measured" but omits `tests/unit/test_lesson_library_receipt_compatibility.py` from S-LL and several candidate files of W-CAP and W-LESSON; the W-ASSIGN "(catalog tests)" cell is not in the MGR-3 allowlist; the conclusions still hold. F-09 no pins for `approvals/TASK_APPROVAL.md` (37,893 bytes, `70919E3C...`), `DECISIONS.md`, `CONTEXT.md`, `STATUS.md`; the six MGR-8 file pins are only referenced. F-10 "SRS-resolved" overreaches: §21.4's stale semantics do not name assignment; same-organization eligibility is D-066-62, not the SRS; O-2d re-asks a point D-066-63 already decided. F-11 the MGR-9 path is split across the DAG, §9 and O-9, with no explicit "one API slice at a time" or "no merge/rebase/cherry-pick/copy" for FE; the class-list pagination gap (MGR-9 plan §4) is not carried. F-12 "no file outside the six changed" conflicts with the four authorized documentation writes. F-13 several located clauses are never used in a card, and there is no Rev60-to-adopted line mapping (for example the §21.2 class row is line 1622 in Rev60 and 1649 in the adopted copy; §23.3 and the §9.8 tables are identical). F-14 "they reach Git with the next FEAT-066 commit" is an unsupported forward claim.

## Requirements A to F of the handoff (reviewer)

A met; B met (authorization shown as owner-reported and absent from records; see F-04); C mostly met (F-05, F-08, F-10); D met (the "mounted but FE-gated" note is accurate; F-07); E partially met (F-11); F mostly met (F-05).

## Not verified (reviewer)

The owner's chat selection of the adopted SRS; the MGR-8 authorization and its "variable absent" result (both only in the handoff); whether the fetch ran (no new reflog entry on `origin/dev`); the real merge outcome between S-LL and M2 (`git merge-tree` not run); runtime, test, OpenAPI or database behavior; a full Rev60-to-adopted clause diff.

## Disposition by the coordinating session

Draft 2 is not edited. The work returns to the owner. The owner had already asked for a Draft 3 that reorganizes the roadmap into the owner's three lanes (seed data; quota — class capacity and video quota, excluding payment; full API-versus-SRS audit and BE–FE API alignment); whether Draft 3 also absorbs F-01 to F-14, and whether Draft 3 gets a review, is the owner's decision.
