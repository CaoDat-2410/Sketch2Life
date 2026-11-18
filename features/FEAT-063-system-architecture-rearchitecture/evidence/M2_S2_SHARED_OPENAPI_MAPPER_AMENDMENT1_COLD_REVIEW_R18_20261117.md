# FEAT-063 M2-S2 Shared OpenAPI Mapper — Comparator Amendment 1 cold review R18 — 2026-11-17

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) on 2026-11-17 at the owner's instruction ("Review Sonnet").
- **Pins reviewed:** draft 8,906 bytes, SHA-256 `DED4781FA2BDC42AD4358CC836E9E03F1B9EE59DFF6031F4D2E48192CA844C66`; amended comparator 55,917 bytes, SHA-256 `573DE1BF0E877994134E80693105D5FA8672C920ED88510070BC9E8A53EDE396`; predecessor 49,730 bytes, SHA-256 `4CB27EA71D419BEBCF99ABB0142D2B789D226A84F2665B2F76C96A5B21402A14`. Reviewer states all three matched and that it made no writes.
- **Verdict:** ACCEPT WITH NOTES — P1=0, P2=3, P3=9. "The amended code is as narrow as the draft claims. I found no wrong result and no unsafe relaxation." All P2 findings concern the draft text, not the code.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report. It was kept outside the worktree while the row set was frozen (working copy SHA-256 `E26CE34F3576D53CDD5A0B0DA05ECC93FA0CB379A8AB9EA5FFD4A239671550BA`) and differs from that copy only in its title and this bullet.
- **After the review:** the amendment text was revised for the text findings and extended with negative controls (answering P2-3); the approved revision is `plan/M2_S2_MAPPER_COMPARATOR_AMENDMENT1_DRAFT_20261117.md`, 14,680 bytes, SHA-256 `A21C3C9F3947E8BB84E9B4EE71E3F28FF473D690FAFA883D2122C3376AC4D66E`. The revised text was not re-reviewed. The amended payload was not changed after the review.

## Findings

| ID | Sev | Finding | Reviewer's smallest fix |
|---|---|---|---|
| P2-1 | P2 | Draft says "Everything else in criterion 7 is unchanged", but criterion 7's last sentence (request-ID objects exactly equal including presence/absence) and "preserve all response headers" contradict amended criterion 9 and the added header. | State that those two clauses are replaced by amended criterion 9 and the exact added-response object. |
| P2-2 | P2 | Authorization quotes truncated hashes and does not pin the eight inputs. | Quote full manifest hashes; say the inputs are the eight files pinned by the two export run manifests and checked by the card. |
| P2-3 | P2 | Only the pass path was exercised; no negative control for: undeclared addition, wrong added object/header, header change on a retained status, request-parameter change, record prefix mismatch, non-append record change. | Say so, or run non-evidence negative rehearsals on mutated copies under `tmp/`. |
| P3-4 | P3 | Launch preconditions not stated (record must stay append-only, LF only; egress probe before the command). | List both as preconditions; re-run the prefix checks right before launch. |
| P3-5 | P3 | Egress deviation of the reused post export is disclosed only in section 5; currency of exports vs worktree not stated. Reviewer verified current `app.py` `AF5DB1BE…`, catalog test `6D7967B6…`, mapping test `A6E5C791…`, HEAD `5de30674` against the post source-state. | Add owner acceptance of the carried deviation to section 4; state the currency checks. |
| P3-6 | P3 | "429" reads like an HTTP status; it is a count. Counts verified: 429 + 55 + 82 + 12 = 578. | Write "429 status entries". |
| P3-7 | P3 | `approvedResponseAdditions` is filled even when the run fails. | Rename, or fill only on equality. |
| P3-8 | P3 | Draft says a header on an added status "must be exactly" the pinned object; code checks only when a header is present (absence is caught by runtime expected-equality and projection equality). | Reword "if present". |
| P3-9 | P3 | Section 3 omits the changed error text; section 2 says "catalog schema reference" though binary/object/list forms exist. | Add both. |
| P3-10 | P3 | Hardening notes, no action: `read_bytes()` follows symlinks; manifest `worktree` not compared with the Backend parent; old `request_ids` is dead code. | None required. |
| P3-11 | P3 | "133 of 134" claim has no supporting artifact among the files read. | Source or soften. |

## Reviewer's "checked and found correct" (summary)

Diff scope limited to the described hunks, all other functions textually identical, single `source_compare` call site; constructed added object equals what `_apply_catalog_metadata` plus the request-ID loop produce (description incl. restore override, content, 422/binary/object rules, header only on the two prefixes); whole-document equality and status-set check intact; criterion 9 still compares request parameters and retained statuses, one-sided operations fail via parameters and operation-set checks; criterion 11 exception limited to the one path with a sound prefix proof, no-read name check passed, worktree root correct; runner, child bootstrap and pytest bootstrap read only `passed`, arguments and exit codes unchanged, Compare card needs only path and hash replaced; draft facts (sizes, hashes, counts) match the artifacts.

## Reviewer's "not checked"

Did not run the comparator or any test; did not evaluate catalog rows or every added response object; did not check the "133 of 134" or "104 rows" claims, the current egress state, or other card files.
