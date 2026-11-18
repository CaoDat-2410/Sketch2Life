# FEAT-063 M2-S2 Shared OpenAPI Mapper — Task Approval Draft 1

**Status: DRAFT / FOR OWNER REVIEW / NOT APPROVED / NOT LAUNCHED.** This is a proposed Task Approval record for owner review. It grants no baseline collection, test, typecheck, lint, validation, implementation, or launch authority. This proposal will not edit the FEAT-063 task-specific approval record at `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` or the separate worktree-root ledger at `approvals/TASK_APPROVAL.md`. `OWNER_MODAL_CALL_APPROVED=NO`.

**Date:** 2026-11-16  
**Worktree:** `D:\GitHub\Sketch2Life\.worktrees\m2-s2`  
**Purpose:** Decide whether to open the separate OpenAPI mapper implementation gate. This document is not Draft 11 and does not revise Draft 10 or its cold review.

**Revision note:** Updated in place for the owner's final approval-package directive. The pre-edit working-copy pin was 33,485 bytes / SHA-256 `F29227272DF2F7060A077C248CBDA39240404F64E501914980432DE7DAFE093E`.

**Post-review revision note:** Updated in place after independent SRS-grounded review thread `01a1e38d-4847-7fa2-ba7c-9e571c90823f`. The corrections address all five P2 and one P3 findings; this note records review provenance and does not grant approval or launch authority.

**Second-review revision note:** Updated in place after independent review thread `01a1e3a7-004d-73e2-b652-6e260f777b02` of the 48,629-byte predecessor pinned `53CAB744B9FFBB8D8AD173EDB297507AC55D36D0E51E9DAEEE496C19337EDB5E`. This revision addresses its two P2 findings: baseline/post Mypy and Ruff are separate cards with pinned baseline-manifest comparison, and the runner must confine all output roots to the canonical approved backend `tmp` path while rejecting reparse points. This note does not grant approval or launch authority.

**Third-review revision note:** Updated in place after independent review thread `01a1e3ba-1b1c-7830-80e1-e77ba9b80f24`. The source-state manifest contract now identifies the worktree and every Git-visible changed path, records the E/E/N/R pre/post path-state tuples, and makes any out-of-allowlist status/hash drift fail closed. This addresses the P3 noted in that review; exact runner/exporter/comparator payload bytes and hashes remain owner-supplied launch prerequisites.

**Owner-disposition revision note:** Updated in place from the 58,171-byte / SHA-256 `0F7AE8C6575BDBDAB61F9F81F6DE0D30A29D749EC7E4DAD6181B80AD68549FC4` working copy after the owner supplied nine planning dispositions. This update records those dispositions, prepares review-only payload bytes and hashes in §7, and records the worktree-root ledger pin observed at that revision; the following clarification distinguishes that ledger from the FEAT-063 task-specific approval record. It does not create a new draft, grant implementation approval, or authorize a command or launch.

**Approval-path clarification note:** The previous §1 approval-pin statement conflated two files with the same basename. The FEAT-063 task-specific approval record is `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` (410,676 bytes / SHA-256 `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088`). The separate worktree-root ledger is `approvals/TASK_APPROVAL.md` (32,311 bytes / SHA-256 `114E1C8834B9AB8E4DCAA8E0779CBF37A2855E242BD79D363C2DF88BADB04973`). Both remain unedited; the root-ledger pin is not a change to the feature-local record.

**Cold-review correction note:** Corrected in place after independent review thread 01a1e46d-432b-7673-bdee-2e891708cdaa, which returned NOT READY (2 P1, 3 P2) for the prior exact pin. This planning-only revision addresses those findings and a static cross-payload consistency pass; the authorized additional cold review is pending. It grants no approval or launch authority.

**Next cold-review correction note:** Updated in place from 201,117 bytes / SHA-256 `C0956D002BDD61B95F9E271DEAE0D1266546B1D7246BAF3BEC0EA0D83AA61AD9` under owner authorization after review thread `01a1e4ad-3f16-7111-b4c3-0233b1d7b632` returned NOT READY (0 P1, 3 P2, 1 P3). This planning-only revision addresses those three P2 findings; the P3 duplicate-main finding remains. One fresh independent review is authorized. No approval, baseline or implementation is authorized.

**Additional cold-review correction note:** Updated in place from 207,912 bytes / SHA-256 `D7DEC91E982003EDE1FE9CC481AE58C443719B78C490EE287AF6CCD93EAC21AC` under owner authorization after a NOT READY result with three P2 categories: N post-state enforcement, comparator ABSENT/D enforcement, and interpreter identity evidence. This revision makes the N post-status/content-state distinction explicit, validates changed-path rows in the active comparator path, and cross-binds interpreter path/executable SHA-256 in the exported lock identity. The P3 duplicate-main finding remains out of scope. This note grants no approval or launch authority.

**Comparator row-validation correction note:** Updated in place from 211,541 bytes / SHA-256 `485A22AF20160613C50677AB7243FF15C5428D7113AC14F0B21A3C403AB22FE8` after independent review thread `01a1e4d0-74da-7421-a0e8-b3f906ee6c2f` returned NOT READY (0 P1, 1 P2, 1 P3 category). This planning-only correction rejects Git-invisible PRESENT rows and validates canonical transition/state rows before comparison or report mapping. Duplicate `main()` definitions remain as directed; one fresh read-only review is authorized. No approval or launch authority is granted.

**Cold-review correction note:** Updated in place from 221,869 bytes / SHA-256 0BFB887C0EE52B102FFBC4FC0272378846361E662C79AAA851E1E86B5CF04878 after review thread 01a1e4f3-6272-7a82-bedd-bcaecd0263f2 returned NOT READY (0 P1, 2 P2, 1 P3). This planning-only correction adds canonical no-read path validation to the comparator before changed-path map/report creation and applies the complete lock-resolved environment gate to OpenApiExport, Compare, Pytest and Check, recording only sanitized identity and distribution-map counts/digests. The process-launch artifact gap remains an explicit P3 limitation and is not changed. Exactly one fresh read-only cold review is authorized; no approval, baseline, implementation or launch authority is granted.

**R3 correction note:** Updated in place from 230,361 bytes / SHA-256 `3A81C0FB8E039BB065A8A40129E61A33B3D223AD36945CCDABF5B90173D4FAFE` after independent cold-review thread `01a1e54e-fc9f-7600-9ec8-97b76963983d` returned NOT READY (0 P1, 1 P2, 1 P3). This planning-only correction adds runtime and published OpenAPI document-shape checks to the exporter and pre-export card; the retained process-launch P3 remains. It does not grant approval or launch authority. A fresh independent review of the resulting pin requires separate owner authorization.

**R5 correction note:** Updated in place from 237,461 bytes / SHA-256 A6A568D21C462B6FEA473855DF76B128EC238ACC2352F8AC2B086B5AE93C2127 after cold-review thread 01a1e5c5-5318-7891-a6f2-11b8f2fae99a returned NOT READY (1 P1, 1 P2, 1 P3); its evidence is 2,635 bytes / SHA-256 A310129F0D251AB8F6D2239BF6C9A85035E1533D5BFE8C86CB6BE31B4E38401F. That review reported truncation in the earlier transfer, so the fresh review is gated on explicit complete-part receipt. This planning-only correction validates every source-inventory and Git-status path before path-based file inspection, pins and directly invokes the owner-provided Git executable, and leaves exactly one pytest-bootstrap main(). One fresh independent read-only review of the final exact pin is authorized; no approval, baseline, test, or implementation launch authority is granted.

**R6 correction note:** Updated in place from 245,649 bytes / SHA-256 `F04C21AFE3A6EC87B4479F6786B036F63BB58D098DDCE294FF3A1FBCF5883220` after independent cold-review thread `01a1e791-23ec-7781-8b7b-b1d5f339ae6f` returned NOT READY (0 P1, 3 P2, 2 P3). The review receipt confirmed all 31 parts without truncation. Its feature-local evidence is 4,024 bytes / SHA-256 `9ECCE660644B6D25C5C379F169EF7A928A090942DF47263BFE809A17D30A464A`. Under the owner's later authorization, this planning-only correction addresses the three P2 findings by ordering OpenApiExport source/path preflight before worktree file reads, pinning all current source/test inputs through pre/post export and comparator checks, and binding comparator Git identity to the canonical owner-pinned executable path/hash. Both P3 findings remain disclosed. Exactly one fresh independent cold review of the corrected exact pin is authorized; no approval, baseline or implementation authority is granted.

**R7 correction note:** Updated in place from 262,855 bytes / SHA-256 `32EB2A238EF7F0CDF2D5C7354E1C8897F82AB07C94D8C094CB0DBD5A5CB584B2` after independent cold-review thread `01a1e7b5-f14d-7642-99c0-0af7ea6c6f30` returned NOT READY (0 P1, 1 P2, 3 P3). The R7 report is 3,948 bytes / SHA-256 `268418F53BD58DFD5CB8112C8B385053D2C3D830B958D2B0EA9FF5B74F4D7D43`; it confirmed receipt of all 33 contiguous parts but could not independently recompute the file hash. This planning-only revision addresses the external-path preflight gap, launch-failure evidence, path-free safety diagnostics, and the unaccepted status of criterion 12. It does not change prior review evidence or grant approval or launch authority.

**R7 correction preflight:** Read-only check in `D:\GitHub\Sketch2Life\.worktrees\m2-s2`: branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`, status 92 paths, staged 0. Draft 1 and R7 report matched the pins above. The 92-path status includes pre-existing dirty/untracked paths; this revision is limited to Draft 1, and the next review report will be a separate new evidence file.

**Post-R7 coordinator consistency correction (2026-11-17):** Updated in place from 296,672 bytes / SHA-256 `A0F3AFBC5E7FDC5F4153E6A60A7851D599AAF82F0E067A7D6EC86CBD6697D5D3`, the unreviewed working copy left after the R7 correction. A read-only static pass found that copy internally inconsistent: (1) `task-runner.py` did not parse as Python (`guard_chain` had an unindented `raise`); (2) the §7 hash roster and the runner's embedded `BOOTSTRAP_SHA256` no longer matched the `task-runner.py`, `child-bootstrap.py` and `openapi-export.py` fence bodies; (3) the Pytest, Mypy and Ruff cards defined the path-guard functions but never called them before their first hash, read or launch; (4) the Compare card omitted the runner's required `-PythonPath` argument; (5) the runner hashed the interpreter without the external-file check its cards apply; (6) §4 listed the post-check baseline manifest under the external-file rule although it is a generated artifact under `backend\tmp`; and (7) an unreadable artifact state could not mark failure evidence incomplete. This planning-only correction fixes those seven items, recomputes the roster from the fence bodies under the §7 materialization rule, and normalizes the document's line endings to CRLF. Each of the five payloads was parsed for Python syntax only; none was executed, imported, linted, typechecked or validated. No cold review covers this pin yet; no approval, baseline, test, implementation or launch authority is granted.

**R8 correction note:** Updated in place from 301,590 bytes / SHA-256 `B422538517376D67243A861B771328036BF954F327CA36EA995929011F438699` after independent cold-review session `local_b3ba9d00-276f-41f5-a472-314a0d9f281f` (model `claude-opus-5-5`, effort high, fresh context, read-only by instruction, not OS-sandboxed) returned NOT READY (1 P1, 1 P2, 8 P3). Its evidence is `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R8_20261117.md`, 7,676 bytes / SHA-256 `5A4A096680C6F8BD9842486A2769BE80587C286BE02D91FF67F4659FFEC3C6BB`; the reviewer confirmed contiguous receipt of lines 1–3805. This planning-only revision addresses F1–F9 and discloses F10 as listed in §5. The task-runner and comparator payload hashes in §7 were recomputed; each payload was parsed for Python syntax only and none was executed, imported, linted, typechecked or validated. No approval, baseline, test, implementation or launch authority is granted; a fresh independent review of the resulting pin is still required.

**R9 correction note:** Updated in place from 301,425 bytes / SHA-256 `59878CFB2E9E03579B9284AF981E23E2E7A36414C7B265336C1520A2C431058E` after independent cold-review session `local_84ea267d-41ad-4e40-9faf-5863f70511be` (model `claude-opus-5-5`, effort high, fresh context, read-only by instruction, not OS-sandboxed) returned NOT READY (0 P1, 1 P2, 7 P3). Its evidence is `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R9_20261117.md`, 6,542 bytes / SHA-256 `D833AF294B1DEB491037E6B9DB30DF1339F7581C8FB72FFB8E880C91172D247B`; the reviewer confirmed contiguous receipt of lines 1–3741. This planning-only revision addresses F-A, F-B, F-C and notes N-2, N-4, N-5, tracks N-1 and N-3, and re-pins §1 to the SRS adopted by owner decision D-209. The task-runner and child-bootstrap payload hashes in §7 were recomputed; each payload was parsed for Python syntax only and none was executed, imported, linted, typechecked or validated. No approval, baseline, test, implementation or launch authority is granted; a fresh independent review of the resulting pin is still required.

**R10/R11 correction note:** Updated in place from 305,717 bytes / SHA-256 `CE02785CAFD8F763BF0ACA442BF3B2050BBFB0128CE4E0F75FD930F2371C0F35` after two independent cold reviews of that pin run in parallel: R10, session `local_136697ca-f747-40a7-9cc2-6dd4d47ce999` (model `claude-opus-5-5`, effort high, read-only by instruction, not OS-sandboxed), NOT READY (1 P1, 0 P2, 2 P3), evidence `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R10_20261117.md`, 6,594 bytes / SHA-256 `8E63E09521D3375189240027F019303B250BC2B0ED3493D2AF197AF6A139A1AD`; and R11, Codex session `01a1e819-73f2-71e1-afc2-cd79bc17f45a` (`gpt-6-luna`, read-only sandbox, restricted network), NOT READY (0 P1, 1 P2, 1 P3), evidence `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R11_20261117.md`, 5,921 bytes / SHA-256 `AC37F093C9655C8563DBA0278A224E3DB00919E8952DE1F8BCB4B52C83990408`. Both reviewers confirmed contiguous receipt of lines 1–3759; R11 recomputed the artifact, §1 and §7 hashes. This planning-only revision addresses all five findings as listed in §5. The task-runner, child-bootstrap, schema-comparator and pytest-bootstrap payload hashes in §7 were recomputed; each payload was parsed for Python syntax only and none was executed, imported, linted, typechecked or validated. No approval, baseline, test, implementation or launch authority is granted; a fresh independent review of the resulting pin is still required.

**R12/R13 and rehearsal correction note:** Updated in place from 312,017 bytes / SHA-256 `B2638560DEF35B2B897BBE11BE6A1F6E0B0716698E0A8D78F7FBCFD74862F2D2` after two independent cold reviews of that pin run in parallel and an owner-authorized rehearsal. R12, session `local_ec4cb823-837f-4ce6-b2c2-0981a54aae34` (model `claude-opus-5-5`, effort high, read-only by instruction, not OS-sandboxed), NOT READY (1 P1, 0 P2, 1 P3), evidence `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R12_20261117.md`, 6,468 bytes / SHA-256 `0F723E013A786C00D7982D066DC0A22A4B345F6FD4A9930B856D20407236D266`. R13, Codex `codex exec` in a read-only sandbox with restricted network, NOT READY (0 P1, 2 P2, 0 P3), evidence `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R13_20261117.md`, 4,625 bytes / SHA-256 `070A82BB7A1DE332E4B85B364703595CCA216C9704DB4A7B7796D6F98D560ECD`. Both reviewers confirmed contiguous receipt of lines 1–3787. The rehearsal record is `evidence/M2_S2_SHARED_OPENAPI_MAPPER_PAYLOAD_REHEARSAL_20261117.md`, 5,619 bytes / SHA-256 `33B8C549F705E1CE6114E4A8AE26857F131EA5FE9FA82C4E8EC7A0EE6828675B`. This planning-only revision corrects the exporter environment root, the Mypy diagnostic pattern and two Compare-card guards, records the owner's planning acceptance of criterion 12, and records that one R13 finding was not reproduced; details are in §5. The task-runner, child-bootstrap and openapi-export payload hashes in §7 were recomputed and each payload was parsed for Python syntax. No payload in this pin has been executed against the approved worktree. No approval, baseline, test, implementation or launch authority is granted; a fresh independent review of the resulting pin is still required.

**R14/R15 correction note:** Updated in place from 318,297 bytes / SHA-256 `9A56F151240940FD3119D1B2F5B0CDB7575F743C0764A2A225A504579E18ACA0` after two independent cold reviews of that pin run in parallel. R14, session `local_16fd78ed-8b69-4474-ae7f-eb93cafa9942` (model `claude-opus-5-5`, effort high, read-only by instruction, not OS-sandboxed): 0 P1, 0 P2, 3 P3; evidence `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R14_20261117.md`, 7,709 bytes / SHA-256 `812EB5F8274A4858C1C028EE5B7C74259FC01450D46B0EFB07EF7820EDF0A296`. R15, Codex `codex exec` in a read-only sandbox with restricted network: ACCEPT, no finding; evidence `evidence/M2_S2_SHARED_OPENAPI_MAPPER_TASK_APPROVAL_DRAFT1_COLD_REVIEW_R15_20261117.md`, 4,960 bytes / SHA-256 `678A3D802D0DB817C4DF2B277732E499FF81E03BCE6F7132324B783CE5B632DE`. Both reviewers confirmed contiguous receipt of lines 1–3803; R15 recomputed the artifact, §1, evidence and §7 hashes. This planning-only revision corrects R14's three P3 findings as listed in §5; the child-bootstrap and task-runner payload hashes in §7 were recomputed and each payload was parsed for Python syntax. No approval, baseline, test, implementation or launch authority is granted. The changed lines of this revision still need one delta review.

## 1. Review basis and current status

- Draft 10 is pinned at 63,397 bytes / SHA-256 `8D486CEC1F84B4A195124A13851142827EDE7BFBB635E9F5737798C45531E6EA`.
- Its independent cold review is pinned at 3,508 bytes / SHA-256 `3550014378EB0D27B7D91AE56C8032948ECF0752B8956E5C28CFBF5BF76897FA`. Verdict remains **ACCEPT WITH CORRECTIONS — planning review only**, no P1 and one P2 at §6.
- The P2 is a command-safety gap: Draft 10's ComparisonRoot `New-Item` lacks explicit terminating-error handling and a post-creation success check. The owner-reported probe succeeded once; it did not demonstrate a creation failure or its cause, and does not guarantee a future creation will succeed. The command guard in this proposal addresses that operational risk only. It does **not** change Draft 10's verdict, close the review P2, or make the review CLEAN.
- Current S2 implementation report `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md`: 25,879 bytes / SHA-256 `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55`; status remains **PARTIAL / NOT COMPLETE**.
- Current product requirements use the unsigned canonical working SRS adopted by owner decision D-209 on 2026-11-17, as directed by `docs/context/SRS_AUTHORITY.md` (5,120 bytes / SHA-256 `CACA7EC03CB570F3276AEA3EAF9214F93DDEC19F3030671A47DB590E19F74726`); the SRS file is 701,157 bytes / SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`, and the FEAT-063 `DECISIONS.md` carrying D-209 is 219,748 bytes / SHA-256 `00776DF5428F15F83633FB7205D8AC8F526A60710AC1204FA493B9FF4C303572`. The Rev68 working copy pinned by earlier revisions of this draft (639,948 bytes / SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`) is historical. SRS §§9.6 and 32 keep target API requirements distinct from the current catalog, mounted routes, OpenAPI output, and verified behavior.
- Historical read-only preflight before the prior Draft 1 revision: worktree D:\GitHub\Sketch2Life\.worktrees\m2-s2, branch feature/feat063-m2-s2, HEAD 5de30674bc826591ad4b3cc00fca53c7597ead51; git status --short reported 86 paths (24 modified, 62 untracked), staged count 0. backend/tmp was ABSENT at that preflight. No path was created during that planning correction. No path was cleaned, restored, or overwritten.
- Historical read-only preflight for the R5 correction: worktree D:\GitHub\Sketch2Life\.worktrees\m2-s2, branch feature/feat063-m2-s2, HEAD 5de30674bc826591ad4b3cc00fca53c7597ead51; git status --short reported 90 paths, staged count 0. Draft 1 (237,461 bytes / A6A568D21C462B6FEA473855DF76B128EC238ACC2352F8AC2B086B5AE93C2127), R5 evidence (2,635 bytes / A310129F0D251AB8F6D2239BF6C9A85035E1533D5BFE8C86CB6BE31B4E38401F), Draft 10, its review, S2 report, feature-local approval, Rev68 and SRS authority matched their applicable pins. All 13 present mapper/source/test/pyproject/lock pins in the table below matched; the N-path remained ABSENT. This planning correction edits only this Draft 1 and does not touch other paths.
- Draft 10 review `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT10_COLD_REVIEW_20261116.md` rechecked at 3,508 bytes / SHA-256 `3550014378EB0D27B7D91AE56C8032948ECF0752B8956E5C28CFBF5BF76897FA`; Draft 10 and S2 report pins above match. Mapper source/test inputs, `backend/pyproject.toml`, and `backend/uv.lock` match the hashes recorded below. Drafts 5–9 and their review evidence remain preserved. New mapping test path is currently ABSENT; no pre-implementation hash is claimed.
- The FEAT-063 task-specific approval record `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` is 410,676 bytes / SHA-256 `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088`; this matches the applicable pin and its prior FEAT-063 M2-S2 approvals remain preserved. A read-only search found no mapper-specific approval for this task. It is unedited. The separate worktree-root ledger `approvals/TASK_APPROVAL.md` is 32,311 bytes / SHA-256 `114E1C8834B9AB8E4DCAA8E0779CBF37A2855E242BD79D363C2DF88BADB04973`; it is a different file and its pin is not drift for the feature-local record. It is also unedited. D-207's earlier S2 scope and all prior command ceilings are not authority for this mapper task and are consumed.

- R6 correction preflight (read-only, before this planning revision): branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`, status 91 paths (24 modified, 67 untracked), staged 0. The predecessor Draft 1 pin was 245,649 bytes / SHA-256 `F04C21AFE3A6EC87B4479F6786B036F63BB58D098DDCE294FF3A1FBCF5883220`; R6 evidence was 4,024 bytes / SHA-256 `9ECCE660644B6D25C5C379F169EF7A928A090942DF47263BFE809A17D30A464A`. The S2 report, feature-local approval and Draft 10 review matched the pins in this document. All 13 present source/test/pyproject/lock hashes in the §1 table were rechecked and matched; the N path remained ABSENT. No source or test file was edited by this planning correction.
- Preflight for the R10/R11 correction (read-only hashes, 2026-11-17): the 13 present source/test/project/lock rows in the table below, `docs/context/SRS_AUTHORITY.md`, the canonical SRS and the FEAT-063 `DECISIONS.md` were re-hashed and matched the byte counts and SHA-256 values stated in this section; the N path was absent. The R11 reviewer computed the same values independently in its sandbox.

### Owner-directed SRS reconciliation (planning-only)

- Owner-directed comparison input: `D:\Zalo Received\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md`, 701,157 bytes / SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`. The owner says its update date is stale and directs its use for this comparison. This copy remains unsigned. When that comparison was made the repository baseline was the Rev68 working copy; D-209 has since adopted this copy as the canonical working SRS (last bullet of this section). Neither record signs off the SRS.
- Owner-copy §§9.6 and 9.8 textually match §§9.6 and 9.8 of the Rev68 working copy that it replaced. The mapper is a narrow implementation mechanism and must not freeze the target API inventory or claim product conformance.
- Owner-copy §§32.10 and 32.14 are dated as-built observations from a different snapshot/branch, not proof that this current M2 worktree fails at runtime. They report `GET /openapi.json` returning HTTP 500 because runtime OpenAPI generation could not find the existing Rev37 `SVG catalog contract` response-schema component. Record this as a known OpenAPI risk only; runtime behavior in this worktree has not been verified.
- The four-path E/E/N/R allowlist preserves components and does not authorize adding that missing schema component or otherwise expanding mapper scope. If the proposed pre-export cannot generate the schema, the runtime schema is absent or unreadable, or the missing-component failure is reproduced, stop and report the available failure artifacts without retry. Any scope expansion requires a separate owner decision before work continues.
- The owner copy's §21.2 DELETE row permits deletion only for a completed run and describes a 202 deletion request/status. The replaced Rev68 working copy's §21.2 permitted explicit DELETE for `COMPLETED`, `FAILED`, and `ABANDONED`, with `DELETE_PENDING` retained until purge verification; D-208 likewise directs that `FAILED`/`ABANDONED` are not purged automatically and the next SRS revision align UC-07 and §21.2. This difference is outside the mapper task; D-209 records it as OPEN-OWNER for the FR-C-08 gate. Do not change D-208, either SRS, SRS authority, decisions, approvals, or lifecycle scope.
- D-209 (owner decision, 2026-11-17, recorded in the FEAT-063 `DECISIONS.md`) adopts this owner copy as the single canonical working SRS and replaces the canonical file's bytes with it. The SRS and authority pins in §1 cite the adopted copy. §§9.6 and 9.8 are identical in the adopted copy and in the replaced Rev68 working copy, so the mapper scope and criteria are unchanged. D-209 grants no implementation, test, baseline or launch authority.

### Current source and test pins

| Input | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `backend/src/sketch2life/interfaces/http/app.py` | 74,637 | `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` | Mapper/app factory and runtime schema |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` | Catalog input |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | 49,654 | `E16DE02140E7977A014F32D9CF131DAC8FC63EA622CEDD26B702958D7B92BB09` | Existing tag/response projection |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | 11,122 | `29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3` | Published schema projection |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 | `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` | Route/profile composition |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py` | 16,807 | `62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85` | Runtime/engine construction |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,501 | `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF` | Existing storage-route context |
| `backend/src/sketch2life/infrastructure/config/settings.py` | 5,964 | `B430FA3036B1621CE0EB6283C94642E57AFF367FB8C45F7819E556D7D4180E65` | Settings/env behavior |
| `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` | 3,568 | `43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B` | Explicit S3 credential adapter |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` | Catalog contract fixture/assertions |
| `backend/tests/contract/test_app_composition.py` | 13,507 | `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` | Read-only selected node |
| `backend/tests/contract/test_openapi_schema_catalog_mapping.py` | — | — | ABSENT pre-implementation; do not hash |
| `backend/pyproject.toml` | 3,383 | `35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2` | Dependency groups/constraints |
| `backend/uv.lock` | 398,117 | `830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13` | Lock currently pins FastAPI 0.162.0 |

Any changed pin, route/profile composition, catalog inventory, or relevant source behavior requires stopping and returning to owner review before execution. No source/runtime behavior was re-tested for this draft.

## 2. Proposed implementation scope

This exact four-path allowlist is proposed for a later, separately launched implementation. No other path may be edited.

| Mode | Path | Purpose |
|---|---|---|
| E | `backend/src/sketch2life/interfaces/http/app.py` | Map catalog metadata to generated OpenAPI operations by exact public method/path only; preserve response projection, request-ID amendments, and unrelated examples. No route-tree traversal, private FastAPI route inspection, Python handler-name guard, or callable-identity lookup. |
| E | `backend/tests/contract/test_openapi_contract_catalog.py` | Assert exact runtime/published operation sets, catalog metadata, duplicate declarations, operationId invariants, and permitted schema deltas. |
| N | `backend/tests/contract/test_openapi_schema_catalog_mapping.py` | Pure mapper tests for exact-key hits; missing, unexpected, stale and duplicate keys; adjacent-key isolation; and preservation of unrelated fields. |
| R | `backend/tests/contract/test_app_composition.py` | Read-only input. Do not edit or expand the allowlist to change its fixture. One named node is a verification selection only. |

### Settled design and allowlist choices

- Owner-selected mapper **Option A**: runtime lookup key is exactly `(method.lower(), path)` from the public OpenAPI operation.
- Owner-selected allowlist **Choice A**: the four paths above.
- Existing `operationId` remains unchanged and unique within each pre/post schema. It is an invariant, **not** a runtime lookup key.
- No metadata binding to Python handler names or callable identity. The known stale-entry risk from later handler reuse of the same public method/path remains documented.

### Proposed acceptance criteria

Owner disposition #1 accepts criteria 1–11 for planning only. On 2026-11-17 the owner also accepted criterion 12 for planning (chat reply "Chấp nhận" to the question whether the pinned-input check should be mandatory). Neither acceptance is a formal approval.

1. Every operation lookup uses only the exact lowercase HTTP method and exact path. No route-tree flattening, private FastAPI route introspection, handler-name or callable check.
2. Exact method/path sets are compared, not just counts. For the pinned source and fixture profile only, the existing regression baseline has 151 runtime operations, 134 catalog operations across 118 catalog paths, and exactly 17 classified runtime-only operations; runtime-only keys remain exactly `PILOT_ONLY_OPERATIONS | PR22_UNCATALOGUED_OPERATIONS`. These counts preserve the as-built fixture and do not freeze the SRS target API, approve every listed route, or establish product conformance. Any target API inventory change remains an M0 contract decision under SRS §9.6.
3. Missing, unexpected, stale, or duplicate catalog keys fail explicitly. A source-level declaration audit checks the full declaration stream before dictionary overwrites can hide duplicates: the initial `MOUNTED_OPERATIONS` mapping and every later literal indexed assignment or other recognized mutation. It counts keys across those forms, detects duplicates, and fails closed for dynamic/non-literal keys, unsupported mutation forms, or syntax it cannot recognize; it must not claim success from only the evaluated dictionary.
4. Runtime tags and descriptions must equal the pinned catalog result exactly: the tag is public_tag_name(contract.tag), and the description is the exact catalog purpose plus only the three source-backed local suffixes for POST /v1/sessions, POST /v1/sessions/{session_id}/media/image, and GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio, or the exact Restore Checkpoint Access suffix. No prefix-only or arbitrary-suffix acceptance is allowed. Published tags and descriptions must equal the pinned SRS projection (SRS_V22_OPERATION_TAGS and publicize_openapi_terms) for that exact operation key.
5. No metadata may appear on a neighboring operation with a different key. Uncatalogued operations and all unrelated fields remain unchanged.
6. Runtime schema (application.state.runtime_openapi_schema) and published projection (application.openapi()) are exported before/after using the same route composition, profile, settings, non-mapper amendments and environment identity. FastAPI must be within the owner-accepted 0.162.0–0.162.7 range; every other installed package must match the exact platform/group lock resolution. Before launching every child action (OpenApiExport, Compare, Pytest, Check), the task runner independently validates the cleared action-specific child environment and complete interpreter/platform/lock-resolved installed-distribution identity against the pinned evidence; each run-manifest records a sanitized identity and actual/resolved distribution counts and digests. Each export also records the actual FastAPI version and a separate source-state manifest identifying canonical worktree, branch, HEAD, the exact Git executable path/hash, Git-visible path/status inventory and per-path byte/hash state. Field deltas are reported by schema kind, method, path and JSON pointer; source-state deltas are compared under criterion 11.
7. The comparator permits only the exact catalog tag/description assignments above and the enumerated response transformations in this criterion. It rejects response-status additions and replacements. A status may be removed only when published_responses excludes that exact pre-state status for a path under /api/be1/v1/ or /v1/parent/profiles; the post-state status set must exactly equal the pinned catalog projection. For retained response statuses, preserve the entire response object except its exact catalog description assignment and these source-proven projections only: (a) replace the content object for parent-profile 422 with the exact declared media/schema object; (b) replace content for the five pinned BINARY_SUCCESS_RESPONSES keys with the exact declared binary media/schema object; and (c) add schema.type=object only when the source setdefault rule applies and that field was absent. No other content, schema, media, examples, headers, or response fields may change. Published response objects must exactly equal project_srs_v22_openapi(runtime), with status, description, media, and catalog schema constraints checked against the pinned catalog. Preserve exact operation sets, security, parameters, request bodies, components, and all response headers. While the request-ID inventory is OPEN, every X-Request-ID request-parameter and response-header object must remain exactly equal across pre/post runtime and published schemas, including presence/absence and every field or nested schema value.
8. Each operationId stays unchanged and unique in runtime and published schemas. This is checked as an invariant, never used as the runtime lookup key; every operation must also have a non-empty operationId.
9. The finite request-ID method/path + JSON-pointer inventory remains **OPEN**. No request-ID delta is allowlisted. For each operation and response in both runtime and published schemas, any addition, removal, or value change to an `X-Request-ID` parameter or response-header object—including `name`, `in`, `required`, `description`, `schema`, and recursively nested fields—fails closed and requires an owner decision; do not infer or silently allowlist paths/pointers.
10. After implementation, run exactly one invocation containing the three selections below, with captured exit status and a finalized output manifest. The new N-path selection must exist before invocation. The pinned pytest-bootstrap payload defines exactly one main() and the module entry point invokes that definition. No pre-implementation pytest run or automatic retry is included in this ceiling; any additional invocation requires separate owner authorization. Passing this mapper task does not close M2-S2 or M2-S3; the S2 report remains PARTIAL / NOT COMPLETE until its separate closure evidence is accepted.
11. Before any changed-source path is inspected or read, require an owner-reviewed, owner-provided source-inventory JSON and SHA-256 pin. The inventory has schemaVersion 1, canonical worktree/branch/HEAD, exact sorted unique preChangedPaths and postChangedPaths rows {path, status, disposition} for every Git-visible changed file, and exactly four sorted unique allowlistTransitions rows {path, mode, preStatus, postStatus} for E/E/N/R. Before any branch/status Git invocation that may lead to path inspection, the exporter validates every path string in both preChangedPaths and postChangedPaths and every transition row as a non-empty canonical repository-relative forward-slash path with no absolute/drive/UNC form, backslash, colon, empty/dot/dot-dot component, control or non-printable character, noncanonical separator, or case-insensitive no-read-policy match. It validates raw Git-status path names by the same rules before dictionary insertion. Invalid/disallowed paths fail closed with a generic diagnostic that does not echo the path, and no rejected path reaches _file_kind, file_state, stat, hash or changed-file content-read operations. The exporter writes source-state manifest version 4: allowlistTransitions contains those four exact canonical owner-pinned rows, and allowlistStates contains exactly four sorted unique phase rows {path, mode, status, state, bytes, sha256}. The comparator independently validates both pre/post lists for list type, exact cardinality/schema, canonical order, unique exact E/E/N/R paths, matching modes, and valid two-character porcelain statuses before any dictionary conversion; both transition lists must agree. N transition preStatus is exactly two spaces and postStatus exactly ??. For N pre-state, the path is absent from preChangedPaths and its source-state allowlistStates row is ABSENT/null; for N post-state, postChangedPaths has exactly one HASH row with status ??, and the source-state allowlistStates row is PRESENT with captured bytes and a 64-hex SHA-256 matching that Git-visible row. The exporter requires the owner-pinned post row before file access and actual Git status ??; the active comparator independently checks transition, row membership, status, state, bytes, and hash. Every changedPaths row must have a nonblank valid Git-visible status for PRESENT, nonnegative bytes and a 64-hex SHA-256; Git-visible ABSENT requires a two-character status containing D and null bytes/hash, and the only no-row ABSENT state is exact N pre-state. Before insertion into any changed-path map or report, the comparator also independently rejects paths that are not canonical repository-relative forward-slash paths: absolute/drive/UNC forms, backslashes, colons, empty/dot/dot-dot components, control or nonprintable characters, and noncanonical separators are invalid. It applies the exporter's case-insensitive no-read policy to every component and filename, rejecting .env-prefixed names, secret, credential, service-account, firebase-adminsdk, real-data, child-media, seed-account and seed-user substrings, plus .pem, .key, .p12 and .pfx suffixes. Rejected paths produce a generic diagnostic without echoing the path and are excluded from the report maps; any rejection fails closed. This path check reads only manifest strings, never the referenced file contents. The inventory carries names/status only, no file contents or secret values. The same exact inventory file and hash must be passed to both exports; runner input manifests and source-state manifests record its SHA-256, and the comparator requires pre/post hashes to match. Capture first compares the complete Git path/status set to the pinned inventory before file access; it then checks all dispositions and file metadata before reading any changed-file content. Any set/status mismatch, EXCLUDED_NO_READ row, denylisted/suspicious or unclassifiable path, unsafe file type, or unexpected missing file aborts before hashing any changed file. E paths must be PRESENT with pre/post hashes; N must be ABSENT/null before and PRESENT/hash-matched after; R must remain PRESENT with identical bytes/hash. Every other Git-visible path must retain identical status and content state/hash. Out-of-allowlist drift or any tuple mismatch fails closed before pytest. Never read or hash .env, credentials, service-account files or real-data files; their EXCLUDED_NO_READ disposition always stops capture for owner disposition rather than claiming a clean comparison. For OpenApiExport, the task runner requires an owner-provided canonical absolute Windows git.exe path and SHA-256; the runner and child bootstrap verify that identity, the exporter rechecks the digest immediately before each invocation, and every Git subprocess argument vector starts with that exact absolute executable path. Git is never resolved by name through PATH. The comparator also requires the pre/post source-state manifests to carry the same canonical Git executable path and SHA-256.

12. **Accepted for planning by the owner on 2026-11-17; not a formal approval.** The exporter payload embeds an exact `pinnedInputManifest` matching every currently present source/test/`pyproject.toml`/`uv.lock` pin in §1, plus the N mapping-test path with a null expected pre-hash. After the source inventory paths and complete raw Git path/status set/dispositions have passed validation, and before reading any worktree lock file or importing the application, OpenApiExport captures and verifies `pinnedInputStates`. The pre-export requires every present pin to equal its reviewed SHA-256 and requires the N path to be ABSENT with null size/hash. The post-export allows hash changes only for the two E paths and the N path; N must be PRESENT with Git status `??` and a captured byte count/hash, while every other pinned input, including R, project and lock files, remains PRESENT with its reviewed size/hash. The comparator independently validates the exact manifest and both state maps, requires the pre-state hashes, and fails closed on any changed non-E/N input or malformed/missing/extra row. The task runner's OpenApiExport preflight records worktree project/lock-file verification as deferred, does not read those files or hash arbitrary `InputPaths`, and relies on the exporter's completed safe inventory and pin gate before the exporter reads `pyproject.toml`/`uv.lock` and imports app code. Compare receives the owner-pinned Git executable path/hash; the comparator verifies its canonical absolute form and digest and requires exact equality in both source-state manifests.

**Export artifact integrity and shape:** Each runtime and published schema output must map to exactly one `PRESENT` manifest entry with the expected exact filename, and its recomputed SHA-256 must equal that entry before parsing. The raw JSON root must be an object (not an array, including a singleton array); parsing must succeed; the exact lowercase property names `openapi`, `info`, and `paths` must each occur once without case-variant collisions; `openapi` must be a non-empty string; and `info` and `paths` must be JSON objects. Missing/ambiguous mapping, hash mismatch, absent/unreadable/malformed JSON, non-object root, wrong/missing property names, or wrong field types fail closed, retain all available outputs, and stop without retry. The PowerShell card uses `ConvertFrom-Json -InputObject` only after the raw-root guard and ordinal property enumeration, compatible with Windows PowerShell 5.1 and PowerShell 7.

**Comparator schema-root acceptance:** The comparator payload contains exactly one CLI `main()` definition, and the module entry point invokes it. That main calls `_load_openapi_schema` for runtime pre, published pre, runtime post, and published post before loading environment/source manifests, operation extraction, or comparison. Each call parses its input and requires a JSON object with a non-empty string `openapi`, object-valued `info`, and object-valued `paths`. JSON null, scalar, array, malformed input, or missing/blank/wrongly typed required fields raises a generic failure without echoing schema content. The child exits nonzero; the task runner records child failure and `success: false` in the finalized run manifest; no `passed: true` comparator report is accepted. Retain available outputs and stop without retry.

## 3. Environment and isolation gates

### Lock-resolution evidence and owner-accepted FastAPI range

The owner accepts FastAPI versions from **0.162.0 through 0.162.7 inclusive** for this mapper task as an explicit exception to the exact FastAPI 0.162.0 version in `backend/uv.lock`. This is a task-specific version-range exception; it does not alter `pyproject.toml` or `uv.lock`. Record the exact FastAPI version actually used for every separately authorized run. FastAPI 0.162.7 is permitted by this exception but is **not lock-matched**. All other installed packages must match the lock resolution for the applicable platform and selected dependency groups. No probe was run for this draft. Before any baseline or verification, provide a pre-provisioned environment and sanitized provenance proving:

- canonical absolute interpreter path and SHA-256 of that exact pre-provisioned executable (`interpreterPath`, `interpreterExecutableSha256`), Python version/build/implementation/architecture, and the complete ordered compatible-tag list plus marker environment produced for that interpreter;
- exact backend/pyproject.toml and backend/uv.lock hashes used, target OS/platform identity, and exact selected dependency groups and extras;
- full normalized installed-distribution and platform/group-resolved distribution records, compared by normalized distribution name and version; every non-FastAPI entry must match exactly;
- actual FastAPI version within the owner-accepted inclusive range, with an explicit difference from the uv.lock pin of 0.162.0, and no other package exception;
- sanitized resolution-tool identity (name, version, executable identity hash) and the exact lock comparison method, with artifact hash supplied separately; and
- a sanitized process-boundary identity listing child environment variable names and safe value categories only, with no credential values, credential hashes, or raw environment dump.

**Current prerequisite state: OWNER-PROVIDED / NOT VERIFIED.** FastAPI 0.162.7 is the last recorded version; it is inside the accepted exception range but is not lock-matched to the 0.162.0 pin. No current interpreter identity, platform/group resolution report, actual-version record for a future run, or complete installed-distribution comparison is present. Before any command, the owner must supply the canonical absolute interpreter path and SHA-256 of that exact pre-provisioned executable (`interpreterPath`, `interpreterExecutableSha256`) in lock-evidence schemaVersion 2, plus a completed sanitized lock-resolution comparison covering exact platform markers and selected groups, including the artifact hash and comparison tool/method identity. The owner must also supply the reviewed source-inventory JSON and its SHA-256 as specified in criterion 11. A FastAPI version probe, pip list, or plain freeze alone is insufficient proof. Update 2026-11-17: at the owner's request an evidence package was prepared outside the worktree (lock-exact interpreter, lock-resolution JSON, two Git executable candidates, a draft source inventory). It awaits owner review and pinning and does not change this state until the owner pins it.

**Sequencing decision for this proposal:** lock-provenance evidence is an owner-supplied prerequisite, not a command in this task's ceilings. Do not install, sync, mutate, regenerate the lock, or run an environment probe under this proposal. If the owner wants a local probe to produce that evidence, it needs separate command authorization before any baseline export. Once the completed evidence and all other prerequisites are accepted, the first command in this task can be the separately authorized pre-fix OpenAPI export. No command is authorized by this draft.

### Owner-provided execution-boundary evidence

| Gate | Current state | Exact owner input required before any command |
|---|---|---|
| OS-level egress block | **OWNER-PROVIDED / NOT VERIFIED** | Explicit owner confirmation and the approved OS/sandbox policy identifying the process boundary and blocking outbound network for exporter, comparator and pytest. A source inspection or environment variable is insufficient. |
| No ambient credentials / DB or provider access | **OWNER-PROVIDED / NOT VERIFIED** | Approval of the cleared-child process design and allowlist, including excluded ambient credential sources, loopback DB sentinel, temporary artifact root, dotenv/cache handling and no-secret logging. Do not provide secret values. This remains an execution boundary, not a source-based claim that access is impossible. |
| Exact task runner and child-process bootstrap | **PREPARED IN §7 / NOT APPROVED** | Review the exact bytes and SHA-256 in §7. Before approval, confirm the runner's actions/arguments, cleared process environment, output-root guard, dotenv/cache behavior, manifests and no-retry behavior. Before each child action, the runner validates the action-specific environment allowlist, FastAPI version, interpreter/platform/tag/marker identity, exact installed-distribution inventory versus owner evidence, and every non-FastAPI installed version versus selected lock-resolved records. For OpenApiExport only, it does not read/hash worktree files in its environment preflight; it records project/lock-file hash verification as deferred, rejects arbitrary InputPaths, and launches the pinned exporter. The exporter validates source-inventory paths and the complete Git path/status set, then verifies the fixed source/test pin manifest and pyproject/uv.lock hashes before app import. Other actions retain runner-side project/lock hash checks. For OpenApiExport it also validates and forwards the owner-pinned canonical absolute Git executable path and SHA-256; the exporter invokes that exact path and does not resolve git through PATH. The run-manifest records Git executable identity, sanitized environment identity, and actual/resolved distribution counts and digests only; it never records credential values, credential hashes or raw environment. Before launch, the runner enumerates expected artifacts and writes `invocation.json`; a subprocess launch exception records `FAILED_TO_START`, path-free failure text, the console marker, and each observable artifact state. Success and captureComplete remain false. If any failure record cannot be finalized, `failureEvidenceState=INCOMPLETE` is explicit and the caller stops without retry.
| Exact OpenAPI exporter | **PREPARED IN §7 / NOT APPROVED** | Review the exact bytes and SHA-256 in §7, including same-profile runtime and published schema capture, sanitized environment, source-state capture bound to the owner-provided source-inventory hash, output paths, and engine disposal. It validates all pre/post inventory paths and raw Git-status paths before path-based inspection, fails closed on unsafe/disallowed paths and invokes only the owner-pinned canonical absolute Git executable after checking its SHA-256. Rejected/unsafe/excluded path diagnostics are generic and do not echo path values; accepted path/status rows remain in the required source-state evidence. It compares the full Git-visible path/status set before any changed-file content access and stops on a mismatch or unsafe path. |
| Source-state path/status inventory | **OWNER-PROVIDED / NOT VERIFIED** | Supply one sanitized, owner-reviewed JSON inventory and SHA-256 before any export. It is stored outside the approved worktree and pins canonical worktree/branch/HEAD; exact sorted pre/post Git-visible path/status rows; HASH or EXCLUDED_NO_READ disposition; and exact sorted pre/post status rows for the four E/E/N/R paths. A mismatch, excluded/suspicious/unclassifiable path, or unsafe file state stops before changed-file contents are read or hashed. The same hash is required for pre/post exports and recorded in each source-state and run manifest. It contains path/status metadata only, no file contents or secret values. |
| Exact comparator | **PREPARED IN §7 / NOT APPROVED** | Review the exact bytes and SHA-256 in §7, including the eight schema/environment/source-state inputs, field-level report including runtime global JSON-pointer deltas, source-state comparisons under accepted criterion 11, pinned-input comparisons under criterion 12, invariants, fail-closed rules and exit behavior. Criterion 12 was accepted for planning by the owner on 2026-11-17. It independently validates the embedded exact source/test pin manifest, rejects non-E/N hash drift, and binds both source-state Git identities to the canonical owner-pinned executable path/hash supplied by the Compare card. It also rejects out-of-allowlist status/hash drift and requires matching pre/post source-inventory hashes and exact Git executable path/hash, N pre no-row/ABSENT/null to post `??` row/PRESENT/hash-matched, and `D` status for every other Git-visible ABSENT row. |
| Exact pytest bootstrap | **PREPARED IN §7 / NOT APPROVED** | Review the exact bytes and SHA-256 in §7. It defines exactly one `main()` invoked by the module entry point, disables pytest's cache provider with `-p no:cacheprovider`, clears named settings caches before collection, applies the approved child-process environment, and runs exactly the three §4 selections. The payload bytes are not a launch instruction. |
| Completed lock-resolution evidence | **OWNER-PROVIDED / NOT VERIFIED** | Supply a sanitized JSON artifact and SHA-256 with schemaVersion: 2, interpreterPath (canonical absolute path), interpreterExecutableSha256 (SHA-256 of that exact executable), resolutionTool (name, version, executableIdentitySha256), comparisonMethod, platformIdentity, pythonVersion, pythonImplementation, compatibleTags (full ordered list), markerEnvironment, selectedDependencyGroups and selectedExtras, pyprojectSha256, uvLockSha256, complete installedDistributions and resolvedDistributions records, fastapiInstalledVersion, fastapiLockVersion (0.162.0), and allNonFastApiPackagesMatch=true. The artifact must identify its exact platform/group resolution and show only the FastAPI version exception. Before every child action, the task runner recomputes the installed-distribution map from the pinned interpreter, requires it to equal installedDistributions, compares every non-FastAPI entry to resolvedDistributions, and verifies interpreter path/hash, FastAPI version, Python/platform identity, tags/markers and child environment. For OpenApiExport, it defers reading/hashing worktree project/lock files until the exporter has validated the complete source inventory and pinned source-input map; the exporter verifies pyproject.toml and uv.lock before app import. Other actions retain runner-side project/lock hash checks; pytest bootstrap retains its own checks. Each run-manifest records only sanitized identity plus count and SHA-256 for the normalized installed/resolved maps. The complete distribution records and lock comparison remain owner-provided evidence. No probe is included in these task ceilings.
| Pinned Git executable | OWNER-PROVIDED / NOT VERIFIED | Supply the canonical absolute path to the intended Windows git.exe and its SHA-256. The OpenApiExport card passes both to the task runner; the runner, child bootstrap, and exporter validate the path/hash, and every Git call uses that exact executable path. The Compare card passes the same owner pin to the comparator, which verifies canonical resolution and digest and binds both source-state records to it. No Git lookup through the cleared child PATH is allowed. The run/source-state manifests retain the executable path and hash only. |

The values in this table are not inferred from source. Until the listed owner inputs are provided and pinned, the task is not launch-ready even if the scope and acceptance criteria are approved. Every executable command card in §4 must invoke the exact task runner pinned in the FEAT-063 task-specific approval record (`features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`); the illustrative call shapes below are not runnable while their placeholders remain.

| Pinned source/test input manifest | **EMBEDDED IN §7 / PREPARED, NOT APPROVED** | The exporter and comparator payloads embed the exact expected pin map for all present rows in the §1 source/test/project/lock table plus a null-hash ABSENT pre-state for N. The map is checked before export/app import and rechecked independently by the comparator. Any changed non-E/N hash or N state outside its exact pre/post transition fails closed. |

### Process and runtime isolation gates

- Start exporter and pytest in a **cleared child process environment** with only minimum OS/Python bootstrap variables and the explicit allowlist. The exact child-process launcher must be reviewed and SHA-256 pinned before approval becomes executable.
- Static source confirms Settings uses env_prefix SKETCH2LIFE_ and fields s3_access_key / s3_secret_key; their exact process names are SKETCH2LIFE_S3_ACCESS_KEY and SKETCH2LIFE_S3_SECRET_KEY. Set synthetic-only values under both names before imports/app construction. The S3 adapter passes credentials explicitly only when both are nonempty; otherwise Boto3 can use its default chain. For the exporter, its controlled Settings(_env_file=None) object receives both synthetic values, so that call path supplies explicit credentials. The normalized manifest records variable names and safe categories only; never display or store either value, its hash, or a raw environment dump.
- Export profile: SKETCH2LIFE_ENV=local, synthetic pilot enabled, storage example enabled, StoryRun-lite demo disabled, development auth provider, AI provider disabled, loopback-only synthetic DB sentinel, and artifact root under the isolated run root. The exporter writes normalized environment identity with stable path placeholders and explicit false network/database/provider-isolation proof fields.
- Pytest profile: the process allowlist carries the same synthetic-only S3 variable names/values, storage example disabled, demo disabled, AI provider disabled, loopback DB sentinel, and artifact root under the pytest run root. **The selected composition node directly constructs a Settings object whose S3 fields default to empty and monkeypatches app_module.get_settings; those process S3 values are not used by that object.** Do not claim the fake process variables protect this node: combined-app composition may create lesson_library_storage with access_key=None and secret_key=None, which can invoke Boto3 default credential discovery if it needs credentials. Remaining proposed mitigations are the cleared process allowlist, AWS metadata disabled, AWS config/credentials paths absent under the isolated run root, isolated HOME/USERPROFILE, and owner-confirmed OS-level egress blocking. Pytest bootstrap writes only sanitized environment categories/path placeholders. Injecting credentials into the fixture is a separate allowlist decision and is outside this proposal.
- Set `AWS_EC2_METADATA_DISABLED=true`; point AWS config/credentials variables to distinct paths that do not exist; isolate `HOME`, `USERPROFILE`, `TEMP`, and `TMP` beneath each new GUID root. Do not inherit ambient AWS, Firebase, Google, proxy, database, or provider credentials.
- Disable dotenv for both `Settings` and `CoreDatabaseSettings` in the reviewed process-local bootstrap and clear settings caches before import/use. `_env_file=None` alone does not disable process-environment loading.
- Source inspection shows `STORYRUN_LITE_MAIN_DEMO_ENABLED=0` gives `lifespan=None` and `app.openapi()` builds the schema without starting a server or lifespan. The proposed exporter calls only `create_app()` / `app.openapi()`, retains a loopback DB sentinel and temp artifact root, and disposes the constructed engine in `finally`. Source inspection shows DB access is request/callback based and Firebase Admin is on the token-verification path; this does not prove runtime absence of DB/network/provider access. The selected test's engine disposal is normal-path cleanup, not finally-guaranteed. These statements are static-only, not execution evidence.
- The source-state path-name denylist is only a first guard. Before any authorized source-state capture, the owner must supply and pin the reviewed path/status inventory defined in criterion 11. The exporter first requires an exact path/status set match, then checks all dispositions and file metadata before any content read/hash. Any EXCLUDED_NO_READ, denylisted/suspicious, unclassifiable, unreadable, or possibly sensitive path stops capture before content access. Filename matching alone cannot identify every secret or real-data file.
- **Owner-confirmed OS-level egress blocking is mandatory** before any exporter, comparator or test process. Its current state is **OWNER-PROVIDED / NOT VERIFIED**. Environment variables alone do not establish network isolation. Do not run if the owner has not confirmed the block and the approved boundary.

## 4. Proposed command cards, ceilings and outputs

All cards below are **proposals, not authorization**. The completed lock-resolution evidence in §3 must be supplied and accepted before any command. $TaskRunner must be the exact SHA-256-pinned task-runner.py payload from §7, approved in the FEAT-063 task-specific approval record; invoke it only through the owner-supplied $Python -I. If backend/tmp is absent, the runner creates only that direct child after validating the canonical worktree/backend, then verifies it as an ordinary directory with no reparse points. For each RunRoot, it rejects a GUID collision before writing, creates a new root, and verifies its canonical direct-child path before child launch or artifacts. The Compare card separately creates ComparisonRoot with terminating errors, verifies creation/path/reparse state, and only then writes the initial hash manifest. On any path, collision, creation or verification failure, stop and do not retry. $Python must be the same owner-supplied absolute interpreter for baseline, comparator, tests and checks; its FastAPI version must be in the accepted range and all other installed packages must match the applicable lock resolution. Workdir is D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend unless marked otherwise. Use separate fresh GUID roots beneath the git-ignored backend\tmp; never reuse a root. Do not read .env or print credentials.

### Mandatory file-path preflight

Each PowerShell card must run its inline canonical-path/reparse-point guard before the first `Get-FileHash`, `Get-Content`, or Python launch. The guard checks the approved worktree path and every existing component of each external control/evidence input from the drive root; it requires a drive-rooted canonical absolute path, rejects symlinks/reparse points and rejects a file whose resolved path is equal to or below the canonical worktree. Apply it to the task runner, sibling child bootstrap, owner-supplied interpreter, selected exporter/comparator/pytest payload, lock-evidence JSON, source-inventory JSON and pinned Git executable before reading bytes; the pre-provisioned interpreter must therefore be located outside the approved worktree. A post-check baseline manifest is a generated artifact and follows the generated-artifact rule in the next paragraph, not the external-file rule. The runner repeats these checks before its own reads; direct payload invocation is unsupported. Because Python reads the task-runner source before executing its `main()`, the PowerShell guard and hash check are mandatory before `-I $TaskRunner`.

Generated artifacts are a separate, explicit exception to the external-file rule: schema, environment, source-state, comparator, pytest and check outputs are intentionally stored beneath `backend\tmp`. Before reading one, the caller and runner must verify that its path has no reparse-point component, is a direct child of the exact expected fresh GUID root, has the expected filename, and matches its recorded manifest hash/state. The runner's only pre-Git-status reads of worktree files outside OpenApiExport are the two fixed §1 lock inputs, `backend\pyproject.toml` and `backend\uv.lock`, used for the environment evidence hash comparison; OpenApiExport defers those reads until its source-inventory and pinned-input gates pass. This is the complete, narrow exception to the source-read ordering claim. Do not generalize it to other worktree paths.

### OpenAPI pre/post exports

Pre-fix export occurs before implementation; post-fix export occurs after the exact four-path implementation. Each is a separate invocation and uses the same pinned exporter, interpreter, profile, route composition, process allowlist, owner-pinned Git executable path/hash and immutable source pins.

```powershell
$ErrorActionPreference = 'Stop'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
function Get-CanonicalNoReparsePath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw 'Path is not absolute.' }
  $Full = [IO.Path]::GetFullPath($Path)
  if (-not [string]::Equals($Full,$Path,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path is not canonical.' }
  if ($Full.StartsWith('\\',[StringComparison]::Ordinal)) { throw 'UNC paths are not approved.' }
  $DriveRoot = [IO.Path]::GetPathRoot($Full)
  if ($DriveRoot -notmatch '^[A-Za-z]:\\$') { throw 'Drive-rooted paths are required.' }
  $Current = $DriveRoot
  $Parts = $Full.Substring($DriveRoot.Length).Split([char[]]@('\','/'),[StringSplitOptions]::RemoveEmptyEntries)
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    try { $Item = Get-Item -LiteralPath $Current -Force -ErrorAction Stop } catch { throw 'Path component is missing or unreadable.' }
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in path.' }
  }
  return $Full
}
function Assert-ExternalFile([string]$Path) {
  $Full = Get-CanonicalNoReparsePath $Path
  $WorktreeFull = Get-CanonicalNoReparsePath $ApprovedWorktree
  $WorktreePrefix = $WorktreeFull.TrimEnd('\') + '\'
  if ([string]::Equals($Full,$WorktreeFull,[StringComparison]::OrdinalIgnoreCase) -or $Full.StartsWith($WorktreePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'External input must be outside the approved worktree.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'External input must be a file.' }
  return $Full
}
function Assert-GeneratedArtifact([string]$Path,[string]$ExpectedRootPattern,[string]$ExpectedName) {
  $Full = Get-CanonicalNoReparsePath $Path
  $Parent = Get-CanonicalNoReparsePath ([IO.Path]::GetDirectoryName($Full))
  $Tmp = Get-CanonicalNoReparsePath (Join-Path $Backend 'tmp')
  if ([IO.Path]::GetDirectoryName($Parent) -ine $Tmp -or [IO.Path]::GetFileName($Parent) -notmatch $ExpectedRootPattern -or [IO.Path]::GetFileName($Full) -cne $ExpectedName) { throw 'Generated artifact path is outside its expected GUID root.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'Generated artifact is not a file.' }
  return $Full
}
$TaskRunner = '<absolute path to the exact owner-approved, SHA-256-pinned task-runner.py payload>'
$TaskRunnerSha256 = '<approved 64-hex task-runner SHA-256>'
$Python = '<owner-supplied absolute Python executable; FastAPI 0.162.0–0.162.7 exception; all other packages lock-resolved>'
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$LockEvidencePath = '<absolute path to the owner-provided sanitized lock-resolution JSON>'
$LockEvidenceSha256 = '<64-hex owner-provided lock-resolution evidence SHA-256>'
$GitExecutablePath = '<canonical absolute path to the owner-provided intended Windows git.exe>'
$GitExecutableSha256 = '<64-hex owner-provided Git executable SHA-256>'
$SourceInventoryPath = '<absolute path to the owner-provided sanitized source path/status inventory JSON>'
$SourceInventorySha256 = '<64-hex owner-approved source-inventory SHA-256>'
$Phase = 'pre' # post export: same exact inventory path/hash; use a fresh GUID root and set Phase='post'
$ExporterPayload = '<absolute path to the exact owner-approved openapi-export.py payload>'
$ExporterPayloadSha256 = '<approved 64-hex exporter-payload SHA-256>'
$ChildBootstrapPath = Join-Path (Split-Path -Parent $TaskRunner) 'child-bootstrap.py'
$ChildBootstrapSha256 = '<approved 64-hex child-bootstrap SHA-256>'
$RunRoot = Join-Path (Join-Path $Backend 'tmp') "openapi-mapper-d10-$Phase-$([guid]::NewGuid().ToString('N'))" # fresh GUID root named after $Phase
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID collision; stop before writing; do not retry within this ceiling.' }
$null = Assert-ExternalFile $TaskRunner
$null = Assert-ExternalFile $ChildBootstrapPath
$null = Assert-ExternalFile $Python
$null = Assert-ExternalFile $LockEvidencePath
$null = Assert-ExternalFile $GitExecutablePath
$null = Assert-ExternalFile $SourceInventoryPath
$null = Assert-ExternalFile $ExporterPayload
$RunnerActualHash = (Get-FileHash -LiteralPath $TaskRunner -Algorithm SHA256).Hash
if ($RunnerActualHash -ne $TaskRunnerSha256) { throw 'Task-runner pin mismatch; stop before launch.' }
if ((Get-FileHash -LiteralPath $LockEvidencePath -Algorithm SHA256).Hash -ne $LockEvidenceSha256) { throw 'Lock-resolution evidence pin mismatch; stop before launch.' }
if ((Get-FileHash -LiteralPath $ChildBootstrapPath -Algorithm SHA256).Hash -ne $ChildBootstrapSha256) { throw 'Child-bootstrap pin mismatch; stop before launch.' }
if (-not [IO.Path]::IsPathRooted($GitExecutablePath) -or -not (Test-Path -LiteralPath $GitExecutablePath -PathType Leaf)) { throw 'Git executable path is not an existing absolute file; stop before launch.' }
if ($GitExecutableSha256 -notmatch '^[A-Fa-f0-9]{64}$') { throw 'Git executable SHA-256 is malformed; stop before launch.' }
$GitActualHash = (Get-FileHash -LiteralPath $GitExecutablePath -Algorithm SHA256).Hash
if ($GitActualHash.ToUpperInvariant() -cne $GitExecutableSha256.ToUpperInvariant()) { throw 'Git executable pin mismatch; stop before launch.' }
if ((Get-FileHash -LiteralPath $SourceInventoryPath -Algorithm SHA256).Hash -ne $SourceInventorySha256) { throw 'Source-inventory pin mismatch; stop before export.' }
if ((Get-FileHash -LiteralPath $ExporterPayload -Algorithm SHA256).Hash -ne $ExporterPayloadSha256) { throw 'Exporter payload pin mismatch; stop before export.' }
& $Python -I $TaskRunner -Action OpenApiExport -Phase $Phase -PythonPath $Python -Backend $Backend -RunRoot $RunRoot -PayloadPath $ExporterPayload -PayloadSha256 $ExporterPayloadSha256 -LockEvidencePath $LockEvidencePath -LockEvidenceSha256 $LockEvidenceSha256 -GitExecutablePath $GitExecutablePath -GitExecutableSha256 $GitExecutableSha256 -SourceInventoryPath $SourceInventoryPath -SourceInventorySha256 $SourceInventorySha256
$RunnerExit = $LASTEXITCODE
$RunRoot = Get-CanonicalNoReparsePath $RunRoot
$RunManifest = Join-Path $RunRoot 'run-manifest.json'
if (-not (Test-Path -LiteralPath $RunManifest -PathType Leaf)) { throw 'Task runner did not finalize run-manifest.json; retain the root and stop without retry.' }
$RunManifest = Assert-GeneratedArtifact $RunManifest '^openapi-mapper-d10-(pre|post)-[0-9a-f]{32}$' 'run-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $RunManifest | ConvertFrom-Json -ErrorAction Stop
if ($RunnerExit -ne 0 -or $Manifest.phase -ne $Phase -or $Manifest.childExitCode -ne 0 -or $Manifest.success -ne $true) {
  throw 'OpenAPI export failed or its manifest does not pass; retain all outputs and stop.'
}
foreach ($name in @("runtime-$Phase.json", "published-$Phase.json", 'environment.json', 'source-state.json', 'exporter.console.txt')) {
  $artifactMatches = @($Manifest.artifacts | Where-Object {
    [string]::Equals([string]$_.name, $name, [System.StringComparison]::Ordinal)
  })
  if ($artifactMatches.Count -ne 1) {
    throw "Required export artifact manifest mapping was missing or ambiguous: $name; retain outputs and stop without retry."
  }
  $artifact = $artifactMatches[0]
  if ($artifact.state -cne 'PRESENT' -or [string]$artifact.sha256 -notmatch '^[A-Fa-f0-9]{64}$') {
    throw "Required export artifact was not present and hashed: $name; retain outputs and stop without retry."
  }
}
foreach ($entry in @(
  [pscustomobject]@{ label = 'runtime'; name = "runtime-$Phase.json"; path = (Join-Path $RunRoot "runtime-$Phase.json") },
  [pscustomobject]@{ label = 'published'; name = "published-$Phase.json"; path = (Join-Path $RunRoot "published-$Phase.json") }
)) {
  try {
    $null = Assert-GeneratedArtifact $entry.path "^openapi-mapper-d10-$Phase-[0-9a-f]{32}$" $entry.name
    $manifestMatches = @($Manifest.artifacts | Where-Object {
      [string]::Equals([string]$_.name, [string]$entry.name, [System.StringComparison]::Ordinal)
    })
    if ($manifestMatches.Count -ne 1) { throw 'artifact manifest mapping missing or ambiguous' }
    $artifact = $manifestMatches[0]
    $manifestHash = [string]$artifact.sha256
    if ($artifact.state -cne 'PRESENT' -or $manifestHash -notmatch '^[A-Fa-f0-9]{64}$') {
      throw 'artifact manifest state or SHA-256 is missing or invalid'
    }
    $actualHash = (Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash
    if (-not [string]::Equals($actualHash.ToUpperInvariant(), $manifestHash.ToUpperInvariant(), [System.StringComparison]::Ordinal)) {
      throw 'artifact SHA-256 does not match its manifest entry'
    }
    $rawJson = Get-Content -Raw -LiteralPath $entry.path
    if ([string]::IsNullOrWhiteSpace($rawJson)) { throw 'schema JSON is empty' }
    $trimmedJson = $rawJson.TrimStart()
    if (-not $trimmedJson.StartsWith('{', [System.StringComparison]::Ordinal)) {
      throw 'schema JSON root is not an object'
    }
    $schema = ConvertFrom-Json -InputObject $rawJson -ErrorAction Stop
  } catch {
    throw "Exported $($entry.label) OpenAPI artifact failed manifest mapping/hash or JSON parsing; retain all outputs and stop without retry."
  }
  if ($null -eq $schema -or $schema -isnot [pscustomobject]) {
    throw "Exported $($entry.label) OpenAPI JSON did not parse as an object; retain all outputs and stop without retry."
  }
  $schemaProperties = @($schema.PSObject.Properties)
  $openapiExact = @($schemaProperties | Where-Object { [string]::Equals($_.Name, 'openapi', [System.StringComparison]::Ordinal) })
  $openapiCaseMatches = @($schemaProperties | Where-Object { [string]::Equals($_.Name, 'openapi', [System.StringComparison]::OrdinalIgnoreCase) })
  $infoExact = @($schemaProperties | Where-Object { [string]::Equals($_.Name, 'info', [System.StringComparison]::Ordinal) })
  $infoCaseMatches = @($schemaProperties | Where-Object { [string]::Equals($_.Name, 'info', [System.StringComparison]::OrdinalIgnoreCase) })
  $pathsExact = @($schemaProperties | Where-Object { [string]::Equals($_.Name, 'paths', [System.StringComparison]::Ordinal) })
  $pathsCaseMatches = @($schemaProperties | Where-Object { [string]::Equals($_.Name, 'paths', [System.StringComparison]::OrdinalIgnoreCase) })
  if ($openapiExact.Count -ne 1 -or $openapiCaseMatches.Count -ne 1 -or
      $infoExact.Count -ne 1 -or $infoCaseMatches.Count -ne 1 -or
      $pathsExact.Count -ne 1 -or $pathsCaseMatches.Count -ne 1) {
    throw "Exported $($entry.label) OpenAPI document is missing an exact lowercase property name or has a case-variant collision; retain all outputs and stop without retry."
  }
  $openapiValue = $openapiExact[0].Value
  $infoValue = $infoExact[0].Value
  $pathsValue = $pathsExact[0].Value
  if ($openapiValue -isnot [string] -or [string]::IsNullOrWhiteSpace($openapiValue) -or
      $infoValue -isnot [pscustomobject] -or $pathsValue -isnot [pscustomobject]) {
    throw "Exported $($entry.label) OpenAPI document has an invalid field type or empty openapi value; retain all outputs and stop without retry."
  }
}
Get-FileHash -LiteralPath $RunManifest -Algorithm SHA256
```

Ceilings: pre export 1; post export 1. The task runner validates the complete lock-resolved environment before launching each action. When subprocess.run returns, it captures child exit and console output, then finalizes run-manifest.json with hashes for present artifacts/logs and explicit MISSING/UNREADABLE/UNSAFE states before returning failure. Before launch it records `invocation.json` and the expected artifact list. If subprocess.run raises, it records `FAILED_TO_START`, a fixed path-free console marker, and each observable artifact state; the run manifest has `success: false` and `captureComplete: false`. If any required evidence write fails, it reports `failureEvidenceState=INCOMPLETE` (and writes `failure-evidence.status` if final manifest writing fails). The caller stops and retains artifacts without retry. Outputs are runtime and published JSON, sanitized environment.json, source-state.json, exporter console log, run manifest, invocation record and hashes under each distinct GUID root. The source-state manifest records the Git-visible path/status set and hashes only after it exactly matches the owner-provided, SHA-256-pinned inventory and all paths pass no-read and metadata checks; it stores no file contents and excludes ignored runner outputs under backend/tmp. The same inventory hash is required for pre/post exports. Stop on changed profile/environment/immutable pin, nonzero exit, missing/unreadable output, missing or ambiguous export-manifest mapping, artifact/manifest SHA-256 mismatch, a non-object JSON root (including a singleton array), malformed JSON, missing or wrong-case `openapi`/`info`/`paths`, invalid OpenAPI field types, excluded no-read path, any baseline request-ID delta pending an owner decision, runtime schema-generation failure, absent/unreadable runtime schema, or reproduction of the missing `SVG catalog contract` response-schema component. Retain and report all available failure artifacts without retry; any required scope expansion waits for a separate owner decision. No schema contents or credentials go to console.

Before an export is accepted, the exporter validates both in-memory runtime and published documents before serialization. For each written runtime/published artifact, the PowerShell card requires one exact manifest-name match marked PRESENT, recomputes the file SHA-256, and compares the digest with that manifest entry before parsing. It rejects empty JSON or any raw root whose first non-whitespace character is not `{`, then uses `ConvertFrom-Json -InputObject` rather than a pipeline. It enumerates `PSObject.Properties` and uses ordinal case-sensitive name checks for exactly lowercase `openapi`, `info`, and `paths`, rejecting missing names and case-variant collisions. It then requires a non-empty string `openapi` and JSON-object `info` and `paths`. Mapping, hash, parse, root-kind, property-name, or shape failure retains all outputs and stops without retry. These constructs are statically compatible with Windows PowerShell 5.1 and PowerShell 7; the card was not run. This gate prevents null, singleton-array, wrong-case, malformed, or hash-mismatched artifacts from satisfying the success signal; it does not claim the current worktree has a runtime schema failure.

### Comparator and mandatory ComparisonRoot guard

Comparator inputs are exactly eight files: the four runtime/published pre/post JSON files, the two sanitized environment manifests, and the two source-state manifests from the pinned export roots. The comparator emits every addition/removal/value delta by schema kind (runtime/published), method, path, and RFC 6901 JSON pointer, including runtime global/non-operation fields; includes hashes of all eight inputs, normalized environment identity, source-inventory hash equality, source-state comparison details, invariant results, and passed; and exits 0 only when every invariant passes.

The comparator constructs the exact expected runtime post-schema from the pre-schema and pinned mapper rules. It requires identical pre/post method/path sets, catalog coverage, and the exact published operation set from SRS_V22_INCLUDED_OPERATIONS. The exact fixture runtime-only set is asserted by the selected contract test in the Pytest card, not by the comparator. Catalog metadata is checked by exact post-state values; a neighbor or uncatalogued operation must remain byte-equivalent as a JSON object. OperationId is non-empty, unchanged, and unique in both schemas. Response status additions are always rejected; only the exact source-rule removals in criterion 7 are allowed. Retained response objects are compared in full against the pre-state after applying only the exact description/content projections in criterion 7. Published pre/post schemas must exactly equal the pinned project_srs_v22_openapi projection of their respective runtime schemas, and published catalog status/media/schema/description constraints are checked separately. Components, security, parameters, request bodies, non-operation fields, examples, and all headers are preserved; every X-Request-ID request parameter and response header is compared recursively and fail-closed while its inventory remains OPEN.

The environment manifest contains the exact sorted effective child-process variable-name allowlist and safe category labels only, stable placeholders for GUID-specific paths, source/worktree identity, canonical interpreter path and executable SHA-256, platform/tag/lock identity, and explicit false values for network/database/provider-isolation proof. It never stores raw environment values, synthetic credential values, credential hashes, or an environment dump. The manifest is not evidence of OS-level egress blocking or proof that database/provider access is impossible. For source state, E paths may differ only as implementation inputs and must be PRESENT in both snapshots; N must be ABSENT/null in pre and PRESENT/hash-matched in post; R and every other Git-visible changed path must retain identical status and content state/hash. An expected-present path with no hash or an unclassifiable status fails closed; an explicit ABSENT state is valid only when represented by that path's recorded Git status and remains unchanged outside the one approved N transition.
Comparator invocation card. The caller chooses a fresh GUID root, rejects collision, creates it with terminating errors, and verifies that the new directory is an ordinary direct child of the approved parent before writing the initial hash manifest or invoking the comparator. The pinned task runner then revalidates the created root and writes its run manifest before child launch:

```powershell
$ErrorActionPreference = 'Stop'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
function Get-CanonicalNoReparsePath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw 'Path is not absolute.' }
  $Full = [IO.Path]::GetFullPath($Path)
  if (-not [string]::Equals($Full,$Path,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path is not canonical.' }
  if ($Full.StartsWith('\\',[StringComparison]::Ordinal)) { throw 'UNC paths are not approved.' }
  $DriveRoot = [IO.Path]::GetPathRoot($Full)
  if ($DriveRoot -notmatch '^[A-Za-z]:\\$') { throw 'Drive-rooted paths are required.' }
  $Current = $DriveRoot
  $Parts = $Full.Substring($DriveRoot.Length).Split([char[]]@('\','/'),[StringSplitOptions]::RemoveEmptyEntries)
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    try { $Item = Get-Item -LiteralPath $Current -Force -ErrorAction Stop } catch { throw 'Path component is missing or unreadable.' }
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in path.' }
  }
  return $Full
}
function Assert-ExternalFile([string]$Path) {
  $Full = Get-CanonicalNoReparsePath $Path
  $WorktreeFull = Get-CanonicalNoReparsePath $ApprovedWorktree
  $WorktreePrefix = $WorktreeFull.TrimEnd('\') + '\'
  if ([string]::Equals($Full,$WorktreeFull,[StringComparison]::OrdinalIgnoreCase) -or $Full.StartsWith($WorktreePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'External input must be outside the approved worktree.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'External input must be a file.' }
  return $Full
}
function Assert-GeneratedArtifact([string]$Path,[string]$ExpectedRootPattern,[string]$ExpectedName) {
  $Full = Get-CanonicalNoReparsePath $Path
  $Parent = Get-CanonicalNoReparsePath ([IO.Path]::GetDirectoryName($Full))
  $Tmp = Get-CanonicalNoReparsePath (Join-Path $Backend 'tmp')
  if ([IO.Path]::GetDirectoryName($Parent) -ine $Tmp -or [IO.Path]::GetFileName($Parent) -notmatch $ExpectedRootPattern -or [IO.Path]::GetFileName($Full) -cne $ExpectedName) { throw 'Generated artifact path is outside its expected GUID root.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'Generated artifact is not a file.' }
  return $Full
}
$TaskRunner = '<absolute path to the exact owner-approved, SHA-256-pinned task-runner.py payload>'
$TaskRunnerSha256 = '<approved 64-hex task-runner SHA-256>'
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$Python = '<owner-supplied absolute Python executable; FastAPI 0.162.0–0.162.7 exception; all other packages lock-resolved>'
$ChildBootstrapPath = Join-Path (Split-Path -Parent $TaskRunner) 'child-bootstrap.py'
$ChildBootstrapSha256 = '<approved 64-hex child-bootstrap SHA-256>'
$LockEvidencePath = '<absolute path to the owner-provided sanitized lock-resolution JSON schemaVersion 2>'
$LockEvidenceSha256 = '<64-hex owner-provided lock-resolution evidence SHA-256>'
$ComparatorPayload = '<absolute path to the exact owner-approved schema-comparator.py payload>'
$ComparatorPayloadSha256 = '<approved 64-hex comparator-payload SHA-256>'
$GitExecutablePath = '<canonical absolute path to the owner-provided intended Windows git.exe>'
$GitExecutableSha256 = '<owner-provided 64-hex Git executable SHA-256>'
$RuntimePre = '<absolute path to the pinned pre-fix runtime JSON>'
$RuntimePreSha256 = '<64-hex SHA-256 from successful pre-export manifest>'
$PublishedPre = '<absolute path to the pinned pre-fix published JSON>'
$PublishedPreSha256 = '<64-hex SHA-256 from successful pre-export manifest>'
$PreEnvironment = '<absolute path to the pinned pre-fix sanitized environment manifest>'
$PreEnvironmentSha256 = '<64-hex SHA-256 from successful pre-export manifest>'
$SourceStatePre = '<absolute path to the pinned pre-fix source-state.json>'
$SourceStatePreSha256 = '<64-hex SHA-256 from successful pre-export manifest>'
$RuntimePost = '<absolute path to the pinned post-fix runtime JSON>'
$RuntimePostSha256 = '<64-hex SHA-256 from successful post-export manifest>'
$PublishedPost = '<absolute path to the pinned post-fix published JSON>'
$PublishedPostSha256 = '<64-hex SHA-256 from successful post-export manifest>'
$PostEnvironment = '<absolute path to the pinned post-fix sanitized environment manifest>'
$PostEnvironmentSha256 = '<64-hex SHA-256 from successful post-export manifest>'
$SourceStatePost = '<absolute path to the pinned post-fix source-state.json>'
$SourceStatePostSha256 = '<64-hex SHA-256 from successful post-export manifest>'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
$TmpRoot = Join-Path $Backend 'tmp'
$ExpectedBackend = [IO.Path]::GetFullPath((Join-Path $ApprovedWorktree 'backend'))
if ([IO.Path]::GetFullPath($Backend) -ne $ExpectedBackend) { throw 'Backend path differs from the approved worktree; stop.' }
foreach ($ExistingPath in @($ApprovedWorktree,$Backend)) {
  $ExistingFull = Get-CanonicalNoReparsePath $ExistingPath
  try { $ExistingItem = Get-Item -LiteralPath $ExistingFull -Force -ErrorAction Stop } catch { throw 'Approved worktree or backend path is missing or unreadable.' }
  if (-not $ExistingItem.PSIsContainer) { throw 'Approved worktree/backend path is not a directory.' }
}
$TmpRoot = [IO.Path]::GetFullPath($TmpRoot)
if (Test-Path -LiteralPath $TmpRoot) {
  $TmpRoot = Get-CanonicalNoReparsePath $TmpRoot
  try { $TmpItem = Get-Item -LiteralPath $TmpRoot -Force -ErrorAction Stop } catch { throw 'backend/tmp is missing or unreadable.' }
  if (-not $TmpItem.PSIsContainer) { throw 'backend/tmp is not a directory.' }
} else {
  New-Item -ItemType Directory -Path $TmpRoot -ErrorAction Stop | Out-Null
  $TmpRoot = Get-CanonicalNoReparsePath $TmpRoot
  if ([IO.Path]::GetDirectoryName($TmpRoot) -ine (Get-CanonicalNoReparsePath $Backend)) { throw 'backend/tmp creation failed its direct-child check.' }
}
$TmpFull = Get-CanonicalNoReparsePath $TmpRoot
$ComparisonRoot = Join-Path $TmpFull "openapi-mapper-d10-compare-$([guid]::NewGuid().ToString('N'))"
$ComparisonFull = [IO.Path]::GetFullPath($ComparisonRoot)
if ([IO.Path]::GetDirectoryName($ComparisonFull) -ine $TmpFull) { throw 'ComparisonRoot must be a direct child of backend/tmp; stop.' }
if (Test-Path -LiteralPath $ComparisonRoot) { throw 'GUID collision; stop before writing; do not retry.' }
$null = Assert-ExternalFile $TaskRunner
$null = Assert-ExternalFile $ChildBootstrapPath
$null = Assert-ExternalFile $Python
$null = Assert-ExternalFile $LockEvidencePath
$null = Assert-ExternalFile $ComparatorPayload
$null = Assert-ExternalFile $GitExecutablePath
$null = Assert-GeneratedArtifact $RuntimePre '^openapi-mapper-d10-pre-[0-9a-f]{32}$' 'runtime-pre.json'
$null = Assert-GeneratedArtifact $PublishedPre '^openapi-mapper-d10-pre-[0-9a-f]{32}$' 'published-pre.json'
$null = Assert-GeneratedArtifact $PreEnvironment '^openapi-mapper-d10-pre-[0-9a-f]{32}$' 'environment.json'
$null = Assert-GeneratedArtifact $SourceStatePre '^openapi-mapper-d10-pre-[0-9a-f]{32}$' 'source-state.json'
$null = Assert-GeneratedArtifact $RuntimePost '^openapi-mapper-d10-post-[0-9a-f]{32}$' 'runtime-post.json'
$null = Assert-GeneratedArtifact $PublishedPost '^openapi-mapper-d10-post-[0-9a-f]{32}$' 'published-post.json'
$null = Assert-GeneratedArtifact $PostEnvironment '^openapi-mapper-d10-post-[0-9a-f]{32}$' 'environment.json'
$null = Assert-GeneratedArtifact $SourceStatePost '^openapi-mapper-d10-post-[0-9a-f]{32}$' 'source-state.json'
New-Item -ItemType Directory -Path $ComparisonRoot -ErrorAction Stop | Out-Null
$CreatedRoot = Get-CanonicalNoReparsePath $ComparisonRoot
if (-not (Test-Path -LiteralPath $CreatedRoot -PathType Container) -or $CreatedRoot -ine $ComparisonFull -or [IO.Path]::GetDirectoryName($CreatedRoot) -ine $TmpFull) { throw 'Created ComparisonRoot failed canonical direct-child verification; stop before artifacts.' }
$ComparatorReport = Join-Path $ComparisonRoot 'field-delta-report.json'
$ComparatorLog = Join-Path $ComparisonRoot 'comparator.console.txt'
$ShaManifest = Join-Path $ComparisonRoot 'sha256.txt'
$GuardHashLines = @('ComparisonRoot created and verified before artifacts or comparison')
Set-Content -LiteralPath $ShaManifest -Value $GuardHashLines -Encoding ascii -ErrorAction Stop
$HashRows = @(
  @{ Path=$TaskRunner; Expected=$TaskRunnerSha256; Name='task-runner.py' },
  @{ Path=$ChildBootstrapPath; Expected=$ChildBootstrapSha256; Name='child-bootstrap.py' },
  @{ Path=$LockEvidencePath; Expected=$LockEvidenceSha256; Name='lock-resolution.json' },
  @{ Path=$ComparatorPayload; Expected=$ComparatorPayloadSha256; Name='schema-comparator.py' },
  @{ Path=$GitExecutablePath; Expected=$GitExecutableSha256; Name='git.exe' },
  @{ Path=$RuntimePre; Expected=$RuntimePreSha256; Name='runtime-pre.json' },
  @{ Path=$PublishedPre; Expected=$PublishedPreSha256; Name='published-pre.json' },
  @{ Path=$PreEnvironment; Expected=$PreEnvironmentSha256; Name='pre-environment.json' },
  @{ Path=$SourceStatePre; Expected=$SourceStatePreSha256; Name='pre-source-state.json' },
  @{ Path=$RuntimePost; Expected=$RuntimePostSha256; Name='runtime-post.json' },
  @{ Path=$PublishedPost; Expected=$PublishedPostSha256; Name='published-post.json' },
  @{ Path=$PostEnvironment; Expected=$PostEnvironmentSha256; Name='post-environment.json' },
  @{ Path=$SourceStatePost; Expected=$SourceStatePostSha256; Name='post-source-state.json' }
)
$InitialHashLines = @('ComparisonRoot created and verified before comparator launch')
foreach ($row in $HashRows) {
  if ($row.Expected -notmatch '^[A-Fa-f0-9]{64}$') { throw 'A required input SHA-256 pin is missing or malformed; stop.' }
  $actual = (Get-FileHash -LiteralPath $row.Path -Algorithm SHA256).Hash
  if (-not [string]::Equals($actual,$row.Expected,[StringComparison]::OrdinalIgnoreCase)) { throw 'A pinned comparator input hash differs; retain the initial manifest and stop.' }
  $InitialHashLines += '{0}  {1}' -f $actual,$row.Name
}
Set-Content -LiteralPath $ShaManifest -Value $InitialHashLines -Encoding ascii -ErrorAction Stop
$null = Get-CanonicalNoReparsePath $ComparisonRoot
if ([IO.Path]::GetDirectoryName($ComparatorReport) -ine $ComparisonFull -or [IO.Path]::GetDirectoryName($ComparatorLog) -ine $ComparisonFull -or (Test-Path -LiteralPath $ComparatorReport) -or (Test-Path -LiteralPath $ComparatorLog)) { throw 'Comparator output paths are not new direct children of the verified ComparisonRoot.' }
& $Python -I $TaskRunner -Action Compare -PythonPath $Python -Backend $Backend -RunRoot $ComparisonRoot -RootAlreadyCreated -LockEvidencePath $LockEvidencePath -LockEvidenceSha256 $LockEvidenceSha256 -GitExecutablePath $GitExecutablePath -GitExecutableSha256 $GitExecutableSha256 -InputPaths @($RuntimePre,$PublishedPre,$PreEnvironment,$SourceStatePre,$RuntimePost,$PublishedPost,$PostEnvironment,$SourceStatePost) -PayloadPath $ComparatorPayload -PayloadSha256 $ComparatorPayloadSha256 -ReportPath $ComparatorReport -ConsoleLogPath $ComparatorLog
$RunnerExit = $LASTEXITCODE
$ComparisonRoot = Get-CanonicalNoReparsePath $ComparisonRoot
$RunManifest = Join-Path $ComparisonRoot 'run-manifest.json'
if (-not (Test-Path -LiteralPath $RunManifest -PathType Leaf)) { throw 'Task runner did not finalize run-manifest.json; retain the root and stop without retry.' }
$RunManifest = Assert-GeneratedArtifact $RunManifest '^openapi-mapper-d10-compare-[0-9a-f]{32}$' 'run-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $RunManifest | ConvertFrom-Json -ErrorAction Stop
if ($RunnerExit -ne 0 -or $Manifest.runnerChildExitCode -ne 0 -or $Manifest.childExitCode -ne 0 -or $Manifest.captureComplete -ne $true -or $Manifest.success -ne $true -or $null -eq $Manifest.comparison -or $Manifest.comparison.passed -ne $true) { throw 'Comparator invocation, capture, or comparison failed; retain the finalized manifest and outputs; stop without retry.' }
$ComparatorReport = Assert-GeneratedArtifact $ComparatorReport '^openapi-mapper-d10-compare-[0-9a-f]{32}$' 'field-delta-report.json'
$ComparatorLog = Assert-GeneratedArtifact $ComparatorLog '^openapi-mapper-d10-compare-[0-9a-f]{32}$' 'comparator.console.txt'
$ShaManifest = Assert-GeneratedArtifact $ShaManifest '^openapi-mapper-d10-compare-[0-9a-f]{32}$' 'sha256.txt'
if (-not (Test-Path -LiteralPath $ComparatorReport -PathType Leaf)) { throw 'Comparator report missing; retain outputs and stop.' }
$ComparatorResult = Get-Content -Raw -LiteralPath $ComparatorReport | ConvertFrom-Json -ErrorAction Stop
if ($ComparatorResult.passed -ne $true) { throw 'Comparator report did not pass; retain outputs and stop.' }
Get-FileHash -LiteralPath $RunManifest,$ShaManifest,$ComparatorReport,$ComparatorLog -Algorithm SHA256
```

The Compare action revalidates the approved canonical backend and its ordinary tmp direct child, rejects reparse points along the path chain, and verifies the caller-created root before writing artifacts or launching the comparator. The PowerShell card uses terminating errors, rejects a GUID collision before writing, creates the new root, verifies that it is an ordinary canonical direct child, and writes an initial hash manifest only after that verification and before later hash checks or comparator launch. A path/create/verification failure stops before comparator execution; a later failure retains the manifest and all available artifacts. After successful root verification, the task runner validates the complete lock-resolved environment before every child action. Before launch it records `invocation.json` and expected artifacts. A subprocess launch exception is recorded as `FAILED_TO_START`, with a path-free marker, observable artifact states, `success: false`, and `captureComplete: false`; if evidence finalization fails, the manifest reports `failureEvidenceState=INCOMPLETE` and the caller stops without retry. Normal completion records child exit, artifact hashes and explicit MISSING/UNREADABLE/UNSAFE states in run-manifest.json, and appends the runner-recorded hashes of the eight inputs, Git executable, lock evidence, payload, report, log and invocation record to sha256.txt under a marker line; the card's initial manifest rows are kept. The caller checks the manifest only after preserving available artifacts. This guard addresses the operational risk in the approval proposal only; it does not change Draft 10's ACCEPT WITH CORRECTIONS verdict or close its P2.

Before loading environment/source manifests or performing operation extraction/comparison, the comparator payload must contain exactly one `main()` invoked by the module entry point, and that main must call `_load_openapi_schema` for runtime pre, published pre, runtime post, and published post. If any root is null, scalar, array, malformed, unreadable, or missing a non-empty string `openapi` and object-valued `info` and `paths`, the child exits nonzero with a generic error; the task runner finalizes a failed run manifest and no `passed: true` comparator report is accepted. Retain failure artifacts and stop without retry.

Outputs: `field-delta-report.json`, `comparator.console.txt`, `run-manifest.json`, and `sha256.txt` in the verified ComparisonRoot. Ceiling: 1 invocation. Success requires runner and child exit code 0, finalized manifest success, and JSON `passed: true`; otherwise retain all generated artifacts and stop. **This proposed guard addresses the operational risk in the approval proposal only; it does not change Draft 10's ACCEPT WITH CORRECTIONS verdict or close its P2.**

### Exact pytest selection and isolation card

One invocation contains exactly these three selections:

1. `tests/contract/test_openapi_schema_catalog_mapping.py`
2. `tests/contract/test_openapi_contract_catalog.py`
3. `tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate`

```powershell
$ErrorActionPreference = 'Stop'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
function Get-CanonicalNoReparsePath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw 'Path is not absolute.' }
  $Full = [IO.Path]::GetFullPath($Path)
  if (-not [string]::Equals($Full,$Path,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path is not canonical.' }
  if ($Full.StartsWith('\\',[StringComparison]::Ordinal)) { throw 'UNC paths are not approved.' }
  $DriveRoot = [IO.Path]::GetPathRoot($Full)
  if ($DriveRoot -notmatch '^[A-Za-z]:\\$') { throw 'Drive-rooted paths are required.' }
  $Current = $DriveRoot
  $Parts = $Full.Substring($DriveRoot.Length).Split([char[]]@('\','/'),[StringSplitOptions]::RemoveEmptyEntries)
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    try { $Item = Get-Item -LiteralPath $Current -Force -ErrorAction Stop } catch { throw 'Path component is missing or unreadable.' }
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in path.' }
  }
  return $Full
}
function Assert-ExternalFile([string]$Path) {
  $Full = Get-CanonicalNoReparsePath $Path
  $WorktreeFull = Get-CanonicalNoReparsePath $ApprovedWorktree
  $WorktreePrefix = $WorktreeFull.TrimEnd('\') + '\'
  if ([string]::Equals($Full,$WorktreeFull,[StringComparison]::OrdinalIgnoreCase) -or $Full.StartsWith($WorktreePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'External input must be outside the approved worktree.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'External input must be a file.' }
  return $Full
}
function Assert-GeneratedArtifact([string]$Path,[string]$ExpectedRootPattern,[string]$ExpectedName) {
  $Full = Get-CanonicalNoReparsePath $Path
  $Parent = Get-CanonicalNoReparsePath ([IO.Path]::GetDirectoryName($Full))
  $Tmp = Get-CanonicalNoReparsePath (Join-Path $Backend 'tmp')
  if ([IO.Path]::GetDirectoryName($Parent) -ine $Tmp -or [IO.Path]::GetFileName($Parent) -notmatch $ExpectedRootPattern -or [IO.Path]::GetFileName($Full) -cne $ExpectedName) { throw 'Generated artifact path is outside its expected GUID root.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'Generated artifact is not a file.' }
  return $Full
}
$TaskRunner = '<absolute path to the exact owner-approved, SHA-256-pinned task-runner.py payload>'
$TaskRunnerSha256 = '<approved 64-hex task-runner SHA-256>'
$Python = '<owner-supplied absolute Python executable; FastAPI 0.162.0–0.162.7 exception; all other packages lock-resolved>'
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$RunRoot = Join-Path (Join-Path $Backend 'tmp') "pytest-openapi-d10-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID collision; stop before writing; do not reuse or retry.' }
$Base = Join-Path $RunRoot 'pytest-basetemp'
if (Test-Path -LiteralPath $Base) { throw 'basetemp exists; stop; never delete or reuse it.' }
$Junit = Join-Path $RunRoot 'pytest.junit.xml'
$LockEvidencePath = '<absolute path to the owner-provided sanitized lock-resolution JSON>'
$LockEvidenceSha256 = '<64-hex owner-provided lock-resolution evidence SHA-256>'
$PytestBootstrap = '<absolute path to the exact owner-approved pytest-bootstrap.py payload>'
$PytestBootstrapSha256 = '<approved 64-hex pytest-bootstrap SHA-256>'
$ChildBootstrapPath = Join-Path (Split-Path -Parent $TaskRunner) 'child-bootstrap.py'
$null = Assert-ExternalFile $TaskRunner
$null = Assert-ExternalFile $ChildBootstrapPath
$null = Assert-ExternalFile $Python
$null = Assert-ExternalFile $LockEvidencePath
$null = Assert-ExternalFile $PytestBootstrap
$TaskRunnerActualHash = (Get-FileHash -LiteralPath $TaskRunner -Algorithm SHA256).Hash
if ($TaskRunnerActualHash -ne $TaskRunnerSha256) { throw 'Task-runner pin mismatch; stop before pytest.' }
if ((Get-FileHash -LiteralPath $LockEvidencePath -Algorithm SHA256).Hash -ne $LockEvidenceSha256) { throw 'Lock-resolution evidence pin mismatch; stop before pytest.' }
$ComparisonRoot = '<absolute pinned GUID comparator root>'
$ComparatorReport = Join-Path $ComparisonRoot 'field-delta-report.json'
$ComparatorReportSha256 = '<64-hex SHA-256 of field-delta-report.json printed by the accepted Compare card>'
if (-not (Test-Path -LiteralPath $ComparatorReport -PathType Leaf)) { throw 'Comparator report missing; do not run pytest.' }
$ComparatorReport = Assert-GeneratedArtifact $ComparatorReport '^openapi-mapper-d10-compare-[0-9a-f]{32}$' 'field-delta-report.json'
if ($ComparatorReportSha256 -notmatch '^[A-Fa-f0-9]{64}$' -or (Get-FileHash -LiteralPath $ComparatorReport -Algorithm SHA256).Hash -ne $ComparatorReportSha256) { throw 'Comparator report pin missing or mismatched; do not run pytest.' }
$ComparatorResult = Get-Content -Raw -LiteralPath $ComparatorReport | ConvertFrom-Json -ErrorAction Stop
if ($ComparatorResult.passed -ne $true) { throw 'Comparator did not pass; do not run pytest.' }
# The task runner launches only the three listed selections in the approved cleared child process.
& $Python -I $TaskRunner -Action Pytest -Phase post -PythonPath $Python -Backend $Backend -RunRoot $RunRoot -BaseTemp $Base -JunitPath $Junit -ComparatorReportPath $ComparatorReport -ComparatorReportSha256 $ComparatorReportSha256 -PayloadPath $PytestBootstrap -PayloadSha256 $PytestBootstrapSha256 -LockEvidencePath $LockEvidencePath -LockEvidenceSha256 $LockEvidenceSha256 -Selections @('tests/contract/test_openapi_schema_catalog_mapping.py','tests/contract/test_openapi_contract_catalog.py','tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate')
$RunnerExit = $LASTEXITCODE
$RunManifest = Join-Path $RunRoot 'run-manifest.json'
if (-not (Test-Path -LiteralPath $RunManifest -PathType Leaf)) { throw 'Task runner did not finalize run-manifest.json; retain the root and stop without retry.' }
$RunManifest = Assert-GeneratedArtifact $RunManifest '^pytest-openapi-d10-[0-9a-f]{32}$' 'run-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $RunManifest | ConvertFrom-Json -ErrorAction Stop
$JunitRecord = $Manifest.artifacts | Where-Object { $_.name -eq 'pytest.junit.xml' }
$ComparatorRecord = $Manifest.artifacts | Where-Object { $_.name -eq 'field-delta-report.json' }
$EnvironmentRecord = $Manifest.artifacts | Where-Object { $_.name -eq 'environment.json' }
if (-not (Test-Path -LiteralPath $ComparatorReport -PathType Leaf)) { throw 'Comparator report missing after pytest; retain outputs and stop.' }
$ComparatorReport = Assert-GeneratedArtifact $ComparatorReport '^openapi-mapper-d10-compare-[0-9a-f]{32}$' 'field-delta-report.json'
if ($ComparatorReportSha256 -notmatch '^[A-Fa-f0-9]{64}$' -or (Get-FileHash -LiteralPath $ComparatorReport -Algorithm SHA256).Hash -ne $ComparatorReportSha256) { throw 'Comparator report changed or its pin is malformed after pytest; retain outputs and stop.' }
$ComparatorResult = Get-Content -Raw -LiteralPath $ComparatorReport | ConvertFrom-Json -ErrorAction Stop
if ($RunnerExit -ne 0 -or $Manifest.runnerChildExitCode -ne 0 -or $Manifest.childExitCode -ne 0 -or $Manifest.captureComplete -ne $true -or $Manifest.success -ne $true -or $null -eq $JunitRecord -or $JunitRecord.state -ne 'PRESENT' -or $JunitRecord.sha256 -notmatch '^[A-Fa-f0-9]{64}$' -or $null -eq $EnvironmentRecord -or $EnvironmentRecord.state -ne 'PRESENT' -or $EnvironmentRecord.sha256 -notmatch '^[A-Fa-f0-9]{64}$' -or $null -eq $ComparatorRecord -or $ComparatorRecord.state -ne 'PRESENT' -or $ComparatorRecord.sha256 -notmatch '^[A-Fa-f0-9]{64}$' -or $Manifest.comparatorPassed -ne $true -or $ComparatorResult.passed -ne $true) {
  throw 'Pytest, JUnit, environment, or comparator success condition failed; retain the finalized manifest and outputs; stop without retry.'
}
Get-FileHash -LiteralPath $RunManifest -Algorithm SHA256
```

After process exit, the task runner finalizes run-manifest.json with pytest exit code, console/JUnit/environment/comparator artifact states and hashes (or explicit MISSING/UNREADABLE states), then returns. Success requires runner and child exit code 0, JUnit present and hashed, environment.json present and hashed, and the comparator report present with passed=true; manifest success must also be true. Do not use SilentlyContinue to hide missing outputs. -p no:cacheprovider disables pytest cache provider; cache_dir would only redirect the cache. Every invocation needs a fresh GUID RunRoot and a new absolute basetemp that did not exist at preflight. Ceiling: 1 post-implementation pytest invocation total; no pre-implementation run, automatic retry, or attempt beyond the approved ceiling.

The exporter and pytest bootstrap validate the exact effective child-process variable-name allowlist. Both receive synthetic-only S3 values under SKETCH2LIFE_S3_ACCESS_KEY and SKETCH2LIFE_S3_SECRET_KEY; the selected test node may construct an independent Settings object with empty S3 fields, so those process values do not protect that object. Sanitized environment.json records names, safe value categories, and stable path placeholders only; it does not contain credential values or hashes. Isolated HOME/USERPROFILE, absent AWS files, metadata disablement, cleared child environment, and owner-confirmed OS egress block remain required. The manifest does not prove network, database, or provider isolation.

### Mypy and Ruff baseline/post cards

Run each baseline card before implementation and record its finalized manifest path and SHA-256 from the actual output. Run each matching post card as a later, separate invocation, only after implementation is complete and after copying that exact baseline manifest path and hash into the post card. Do not paste baseline and post commands into one invocation or continue to a post card without the recorded baseline output. The task runner emits a structured manifest with tool, phase, tool exit code, capture success, normalized diagnostic signatures, unparsed diagnostic count, and manifest/output hashes. Each post action consumes the exact baseline manifest; it verifies the supplied manifest hash and tool/version identity, computes the diagnostic delta, and reports a comparison result, baseline-manifest hash, added-signature list and N-path diagnostic count in the post manifest. Signature identity is `(backend-relative path, severity, diagnostic code, normalized message)`; line and column numbers are not part of the identity and are kept only in the raw tool output artifact `check-raw-output.txt`. Missing comparison fields or unparsed diagnostics fail closed. Historical findings are debt, **not a clean pass**. Proposed regression signal: no new normalized signatures; for Ruff, no new E-path signatures and zero N-path diagnostics. A nonzero tool exit or any remaining diagnostics is reported as **NOT CLEAN**, even when the no-new-diagnostics delta is zero. Whether historical debt blocks mapper-task acceptance remains an owner approval choice; no green typecheck/lint claim is allowed from a zero delta alone.

```powershell
# BASELINE MYPY — one invocation before implementation.
$ErrorActionPreference = 'Stop'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
function Get-CanonicalNoReparsePath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw 'Path is not absolute.' }
  $Full = [IO.Path]::GetFullPath($Path)
  if (-not [string]::Equals($Full,$Path,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path is not canonical.' }
  if ($Full.StartsWith('\\',[StringComparison]::Ordinal)) { throw 'UNC paths are not approved.' }
  $DriveRoot = [IO.Path]::GetPathRoot($Full)
  if ($DriveRoot -notmatch '^[A-Za-z]:\\$') { throw 'Drive-rooted paths are required.' }
  $Current = $DriveRoot
  $Parts = $Full.Substring($DriveRoot.Length).Split([char[]]@('\','/'),[StringSplitOptions]::RemoveEmptyEntries)
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    try { $Item = Get-Item -LiteralPath $Current -Force -ErrorAction Stop } catch { throw 'Path component is missing or unreadable.' }
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in path.' }
  }
  return $Full
}
function Assert-ExternalFile([string]$Path) {
  $Full = Get-CanonicalNoReparsePath $Path
  $WorktreeFull = Get-CanonicalNoReparsePath $ApprovedWorktree
  $WorktreePrefix = $WorktreeFull.TrimEnd('\') + '\'
  if ([string]::Equals($Full,$WorktreeFull,[StringComparison]::OrdinalIgnoreCase) -or $Full.StartsWith($WorktreePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'External input must be outside the approved worktree.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'External input must be a file.' }
  return $Full
}
function Assert-GeneratedArtifact([string]$Path,[string]$ExpectedRootPattern,[string]$ExpectedName) {
  $Full = Get-CanonicalNoReparsePath $Path
  $Parent = Get-CanonicalNoReparsePath ([IO.Path]::GetDirectoryName($Full))
  $Tmp = Get-CanonicalNoReparsePath (Join-Path $Backend 'tmp')
  if ([IO.Path]::GetDirectoryName($Parent) -ine $Tmp -or [IO.Path]::GetFileName($Parent) -notmatch $ExpectedRootPattern -or [IO.Path]::GetFileName($Full) -cne $ExpectedName) { throw 'Generated artifact path is outside its expected GUID root.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'Generated artifact is not a file.' }
  return $Full
}
$TaskRunner = '<absolute path to the exact owner-approved, SHA-256-pinned task-runner.py payload>'
$TaskRunnerSha256 = '<approved 64-hex task-runner SHA-256>'
$Python = '<owner-supplied absolute Python executable; FastAPI 0.162.0–0.162.7 exception; all other packages lock-resolved>'
$LockEvidencePath = '<absolute path to the owner-provided sanitized lock-resolution JSON schemaVersion 2>'
$LockEvidenceSha256 = '<64-hex owner-provided lock-resolution evidence SHA-256>'
$ChildBootstrapPath = Join-Path (Split-Path -Parent $TaskRunner) 'child-bootstrap.py'
$null = Assert-ExternalFile $TaskRunner
$null = Assert-ExternalFile $ChildBootstrapPath
$null = Assert-ExternalFile $Python
$null = Assert-ExternalFile $LockEvidencePath
if ((Get-FileHash -LiteralPath $LockEvidencePath -Algorithm SHA256).Hash -ne $LockEvidenceSha256) { throw 'Lock-resolution evidence pin mismatch; stop before check.' }
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$RunRoot = Join-Path (Join-Path $Backend 'tmp') "mypy-openapi-d10-baseline-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID collision; stop without retry or writes.' }
if ((Get-FileHash -LiteralPath $TaskRunner -Algorithm SHA256).Hash -ne $TaskRunnerSha256) { throw 'Task-runner pin mismatch; stop before launch.' }
& $Python -I $TaskRunner -Action Check -Tool Mypy -Phase baseline -PythonPath $Python -Backend $Backend -RunRoot $RunRoot -LockEvidencePath $LockEvidencePath -LockEvidenceSha256 $LockEvidenceSha256 -Paths @('src/sketch2life')
$RunnerExit = $LASTEXITCODE
$RunManifest = Join-Path $RunRoot 'run-manifest.json'
if (-not (Test-Path -LiteralPath $RunManifest -PathType Leaf)) { throw 'Task runner did not finalize run-manifest.json; stop without retry.' }
$RunManifest = Assert-GeneratedArtifact $RunManifest '^mypy-openapi-d10-baseline-[0-9a-f]{32}$' 'run-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $RunManifest | ConvertFrom-Json -ErrorAction Stop
Get-FileHash -LiteralPath $RunManifest -Algorithm SHA256
if ($RunnerExit -ne 0 -or $Manifest.tool -ne 'Mypy' -or $Manifest.phase -ne 'baseline' -or $Manifest.success -ne $true -or $Manifest.captureComplete -ne $true -or $null -eq $Manifest.diagnostics.signatures -or $Manifest.diagnostics.unparsedCount -ne 0) { throw 'Mypy baseline evidence was not captured or parsed completely; retain evidence and stop.' }
```

```powershell
# BASELINE RUFF — one invocation before implementation; N is absent and excluded.
$ErrorActionPreference = 'Stop'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
function Get-CanonicalNoReparsePath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw 'Path is not absolute.' }
  $Full = [IO.Path]::GetFullPath($Path)
  if (-not [string]::Equals($Full,$Path,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path is not canonical.' }
  if ($Full.StartsWith('\\',[StringComparison]::Ordinal)) { throw 'UNC paths are not approved.' }
  $DriveRoot = [IO.Path]::GetPathRoot($Full)
  if ($DriveRoot -notmatch '^[A-Za-z]:\\$') { throw 'Drive-rooted paths are required.' }
  $Current = $DriveRoot
  $Parts = $Full.Substring($DriveRoot.Length).Split([char[]]@('\','/'),[StringSplitOptions]::RemoveEmptyEntries)
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    try { $Item = Get-Item -LiteralPath $Current -Force -ErrorAction Stop } catch { throw 'Path component is missing or unreadable.' }
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in path.' }
  }
  return $Full
}
function Assert-ExternalFile([string]$Path) {
  $Full = Get-CanonicalNoReparsePath $Path
  $WorktreeFull = Get-CanonicalNoReparsePath $ApprovedWorktree
  $WorktreePrefix = $WorktreeFull.TrimEnd('\') + '\'
  if ([string]::Equals($Full,$WorktreeFull,[StringComparison]::OrdinalIgnoreCase) -or $Full.StartsWith($WorktreePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'External input must be outside the approved worktree.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'External input must be a file.' }
  return $Full
}
function Assert-GeneratedArtifact([string]$Path,[string]$ExpectedRootPattern,[string]$ExpectedName) {
  $Full = Get-CanonicalNoReparsePath $Path
  $Parent = Get-CanonicalNoReparsePath ([IO.Path]::GetDirectoryName($Full))
  $Tmp = Get-CanonicalNoReparsePath (Join-Path $Backend 'tmp')
  if ([IO.Path]::GetDirectoryName($Parent) -ine $Tmp -or [IO.Path]::GetFileName($Parent) -notmatch $ExpectedRootPattern -or [IO.Path]::GetFileName($Full) -cne $ExpectedName) { throw 'Generated artifact path is outside its expected GUID root.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'Generated artifact is not a file.' }
  return $Full
}
$TaskRunner = '<absolute path to the exact owner-approved, SHA-256-pinned task-runner.py payload>'
$TaskRunnerSha256 = '<approved 64-hex task-runner SHA-256>'
$Python = '<owner-supplied absolute Python executable; FastAPI 0.162.0–0.162.7 exception; all other packages lock-resolved>'
$LockEvidencePath = '<absolute path to the owner-provided sanitized lock-resolution JSON schemaVersion 2>'
$LockEvidenceSha256 = '<64-hex owner-provided lock-resolution evidence SHA-256>'
$ChildBootstrapPath = Join-Path (Split-Path -Parent $TaskRunner) 'child-bootstrap.py'
$null = Assert-ExternalFile $TaskRunner
$null = Assert-ExternalFile $ChildBootstrapPath
$null = Assert-ExternalFile $Python
$null = Assert-ExternalFile $LockEvidencePath
if ((Get-FileHash -LiteralPath $LockEvidencePath -Algorithm SHA256).Hash -ne $LockEvidenceSha256) { throw 'Lock-resolution evidence pin mismatch; stop before check.' }
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$RunRoot = Join-Path (Join-Path $Backend 'tmp') "ruff-openapi-d10-baseline-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID collision; stop without retry or writes.' }
if ((Get-FileHash -LiteralPath $TaskRunner -Algorithm SHA256).Hash -ne $TaskRunnerSha256) { throw 'Task-runner pin mismatch; stop before launch.' }
& $Python -I $TaskRunner -Action Check -Tool Ruff -Phase baseline -PythonPath $Python -Backend $Backend -RunRoot $RunRoot -LockEvidencePath $LockEvidencePath -LockEvidenceSha256 $LockEvidenceSha256 -Paths @('src/sketch2life/interfaces/http/app.py','tests/contract/test_openapi_contract_catalog.py')
$RunnerExit = $LASTEXITCODE
$RunManifest = Join-Path $RunRoot 'run-manifest.json'
if (-not (Test-Path -LiteralPath $RunManifest -PathType Leaf)) { throw 'Task runner did not finalize run-manifest.json; stop without retry.' }
$RunManifest = Assert-GeneratedArtifact $RunManifest '^ruff-openapi-d10-baseline-[0-9a-f]{32}$' 'run-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $RunManifest | ConvertFrom-Json -ErrorAction Stop
Get-FileHash -LiteralPath $RunManifest -Algorithm SHA256
if ($RunnerExit -ne 0 -or $Manifest.tool -ne 'Ruff' -or $Manifest.phase -ne 'baseline' -or $Manifest.success -ne $true -or $Manifest.captureComplete -ne $true -or $null -eq $Manifest.diagnostics.signatures -or $Manifest.diagnostics.unparsedCount -ne 0 -or $Manifest.newPathDiagnostics.state -ne 'ABSENT_NOT_SELECTED') { throw 'Ruff baseline evidence was not captured or parsed completely; retain evidence and stop.' }
```

```powershell
# POST MYPY — separate invocation, only after approved implementation is complete.
$ErrorActionPreference = 'Stop'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
function Get-CanonicalNoReparsePath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw 'Path is not absolute.' }
  $Full = [IO.Path]::GetFullPath($Path)
  if (-not [string]::Equals($Full,$Path,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path is not canonical.' }
  if ($Full.StartsWith('\\',[StringComparison]::Ordinal)) { throw 'UNC paths are not approved.' }
  $DriveRoot = [IO.Path]::GetPathRoot($Full)
  if ($DriveRoot -notmatch '^[A-Za-z]:\\$') { throw 'Drive-rooted paths are required.' }
  $Current = $DriveRoot
  $Parts = $Full.Substring($DriveRoot.Length).Split([char[]]@('\','/'),[StringSplitOptions]::RemoveEmptyEntries)
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    try { $Item = Get-Item -LiteralPath $Current -Force -ErrorAction Stop } catch { throw 'Path component is missing or unreadable.' }
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in path.' }
  }
  return $Full
}
function Assert-ExternalFile([string]$Path) {
  $Full = Get-CanonicalNoReparsePath $Path
  $WorktreeFull = Get-CanonicalNoReparsePath $ApprovedWorktree
  $WorktreePrefix = $WorktreeFull.TrimEnd('\') + '\'
  if ([string]::Equals($Full,$WorktreeFull,[StringComparison]::OrdinalIgnoreCase) -or $Full.StartsWith($WorktreePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'External input must be outside the approved worktree.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'External input must be a file.' }
  return $Full
}
function Assert-GeneratedArtifact([string]$Path,[string]$ExpectedRootPattern,[string]$ExpectedName) {
  $Full = Get-CanonicalNoReparsePath $Path
  $Parent = Get-CanonicalNoReparsePath ([IO.Path]::GetDirectoryName($Full))
  $Tmp = Get-CanonicalNoReparsePath (Join-Path $Backend 'tmp')
  if ([IO.Path]::GetDirectoryName($Parent) -ine $Tmp -or [IO.Path]::GetFileName($Parent) -notmatch $ExpectedRootPattern -or [IO.Path]::GetFileName($Full) -cne $ExpectedName) { throw 'Generated artifact path is outside its expected GUID root.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'Generated artifact is not a file.' }
  return $Full
}
$TaskRunner = '<absolute path to the exact owner-approved, SHA-256-pinned task-runner.py payload>'
$TaskRunnerSha256 = '<approved 64-hex task-runner SHA-256>'
$Python = '<same owner-supplied Python executable as baseline; FastAPI 0.162.0–0.162.7 exception; all other packages lock-resolved>'
$LockEvidencePath = '<same absolute schemaVersion 2 lock-resolution evidence JSON as baseline>'
$LockEvidenceSha256 = '<same 64-hex lock-resolution evidence SHA-256 as baseline>'
$ChildBootstrapPath = Join-Path (Split-Path -Parent $TaskRunner) 'child-bootstrap.py'
$null = Assert-ExternalFile $TaskRunner
$null = Assert-ExternalFile $ChildBootstrapPath
$null = Assert-ExternalFile $Python
$null = Assert-ExternalFile $LockEvidencePath
if ((Get-FileHash -LiteralPath $LockEvidencePath -Algorithm SHA256).Hash -ne $LockEvidenceSha256) { throw 'Lock-resolution evidence pin mismatch; stop before check.' }
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$BaselineManifest = '<absolute path to the successful baseline Mypy run-manifest.json>'
$BaselineManifestSha256 = '<64-hex SHA-256 reported for that manifest>'
$RunRoot = Join-Path (Join-Path $Backend 'tmp') "mypy-openapi-d10-post-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID collision; stop without retry or writes.' }
if ((Get-FileHash -LiteralPath $TaskRunner -Algorithm SHA256).Hash -ne $TaskRunnerSha256) { throw 'Task-runner pin mismatch; stop before launch.' }
$BaselineManifest = Assert-GeneratedArtifact $BaselineManifest '^mypy-openapi-d10-baseline-[0-9a-f]{32}$' 'run-manifest.json'
if ((Get-FileHash -LiteralPath $BaselineManifest -Algorithm SHA256).Hash -ne $BaselineManifestSha256) { throw 'Baseline Mypy manifest pin mismatch; stop.' }
& $Python -I $TaskRunner -Action Check -Tool Mypy -Phase post -PythonPath $Python -Backend $Backend -RunRoot $RunRoot -LockEvidencePath $LockEvidencePath -LockEvidenceSha256 $LockEvidenceSha256 -Paths @('src/sketch2life') -BaselineManifestPath $BaselineManifest -BaselineManifestSha256 $BaselineManifestSha256
$RunnerExit = $LASTEXITCODE
$RunManifest = Join-Path $RunRoot 'run-manifest.json'
if (-not (Test-Path -LiteralPath $RunManifest -PathType Leaf)) { throw 'Task runner did not finalize run-manifest.json; stop without retry.' }
$RunManifest = Assert-GeneratedArtifact $RunManifest '^mypy-openapi-d10-post-[0-9a-f]{32}$' 'run-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $RunManifest | ConvertFrom-Json -ErrorAction Stop
Get-FileHash -LiteralPath $RunManifest -Algorithm SHA256
if ($RunnerExit -ne 0 -or $Manifest.tool -ne 'Mypy' -or $Manifest.phase -ne 'post' -or $Manifest.success -ne $true -or $Manifest.comparison.passed -ne $true -or $Manifest.comparison.baselineManifestSha256 -ne $BaselineManifestSha256 -or $Manifest.comparison.unparsedCount -ne 0 -or $null -eq $Manifest.comparison.addedSignatures -or $Manifest.comparison.addedSignatures.Count -ne 0) { throw 'Mypy regression-delta comparison or structured evidence failed; retain evidence and stop.' }
if ($Manifest.toolExitCode -ne 0 -or $Manifest.toolClean -ne $true) { Write-Output "NOT CLEAN: Mypy toolExitCode=$($Manifest.toolExitCode), toolClean=$($Manifest.toolClean); retain evidence and stop."; throw 'Mypy post is not a clean tool pass even if the baseline-relative delta is zero.' }
```

```powershell
# POST RUFF — separate invocation, only after approved implementation is complete.
$ErrorActionPreference = 'Stop'
$ApprovedWorktree = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2'
function Get-CanonicalNoReparsePath([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path) -or -not [IO.Path]::IsPathRooted($Path)) { throw 'Path is not absolute.' }
  $Full = [IO.Path]::GetFullPath($Path)
  if (-not [string]::Equals($Full,$Path,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path is not canonical.' }
  if ($Full.StartsWith('\\',[StringComparison]::Ordinal)) { throw 'UNC paths are not approved.' }
  $DriveRoot = [IO.Path]::GetPathRoot($Full)
  if ($DriveRoot -notmatch '^[A-Za-z]:\\$') { throw 'Drive-rooted paths are required.' }
  $Current = $DriveRoot
  $Parts = $Full.Substring($DriveRoot.Length).Split([char[]]@('\','/'),[StringSplitOptions]::RemoveEmptyEntries)
  foreach ($Part in $Parts) {
    $Current = Join-Path $Current $Part
    try { $Item = Get-Item -LiteralPath $Current -Force -ErrorAction Stop } catch { throw 'Path component is missing or unreadable.' }
    if (($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse point in path.' }
  }
  return $Full
}
function Assert-ExternalFile([string]$Path) {
  $Full = Get-CanonicalNoReparsePath $Path
  $WorktreeFull = Get-CanonicalNoReparsePath $ApprovedWorktree
  $WorktreePrefix = $WorktreeFull.TrimEnd('\') + '\'
  if ([string]::Equals($Full,$WorktreeFull,[StringComparison]::OrdinalIgnoreCase) -or $Full.StartsWith($WorktreePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'External input must be outside the approved worktree.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'External input must be a file.' }
  return $Full
}
function Assert-GeneratedArtifact([string]$Path,[string]$ExpectedRootPattern,[string]$ExpectedName) {
  $Full = Get-CanonicalNoReparsePath $Path
  $Parent = Get-CanonicalNoReparsePath ([IO.Path]::GetDirectoryName($Full))
  $Tmp = Get-CanonicalNoReparsePath (Join-Path $Backend 'tmp')
  if ([IO.Path]::GetDirectoryName($Parent) -ine $Tmp -or [IO.Path]::GetFileName($Parent) -notmatch $ExpectedRootPattern -or [IO.Path]::GetFileName($Full) -cne $ExpectedName) { throw 'Generated artifact path is outside its expected GUID root.' }
  try { $Item = Get-Item -LiteralPath $Full -Force -ErrorAction Stop } catch { throw 'Input path is missing or unreadable.' }
  if ($Item.PSIsContainer) { throw 'Generated artifact is not a file.' }
  return $Full
}
$TaskRunner = '<absolute path to the exact owner-approved, SHA-256-pinned task-runner.py payload>'
$TaskRunnerSha256 = '<approved 64-hex task-runner SHA-256>'
$Python = '<same owner-supplied Python executable as baseline; FastAPI 0.162.0–0.162.7 exception; all other packages lock-resolved>'
$LockEvidencePath = '<same absolute schemaVersion 2 lock-resolution evidence JSON as baseline>'
$LockEvidenceSha256 = '<same 64-hex lock-resolution evidence SHA-256 as baseline>'
$ChildBootstrapPath = Join-Path (Split-Path -Parent $TaskRunner) 'child-bootstrap.py'
$null = Assert-ExternalFile $TaskRunner
$null = Assert-ExternalFile $ChildBootstrapPath
$null = Assert-ExternalFile $Python
$null = Assert-ExternalFile $LockEvidencePath
if ((Get-FileHash -LiteralPath $LockEvidencePath -Algorithm SHA256).Hash -ne $LockEvidenceSha256) { throw 'Lock-resolution evidence pin mismatch; stop before check.' }
$Backend = 'D:\GitHub\Sketch2Life\.worktrees\m2-s2\backend'
$BaselineManifest = '<absolute path to the successful baseline Ruff run-manifest.json>'
$BaselineManifestSha256 = '<64-hex SHA-256 reported for that manifest>'
$RunRoot = Join-Path (Join-Path $Backend 'tmp') "ruff-openapi-d10-post-$([guid]::NewGuid().ToString('N'))"
if (Test-Path -LiteralPath $RunRoot) { throw 'GUID collision; stop without retry or writes.' }
if ((Get-FileHash -LiteralPath $TaskRunner -Algorithm SHA256).Hash -ne $TaskRunnerSha256) { throw 'Task-runner pin mismatch; stop before launch.' }
$BaselineManifest = Assert-GeneratedArtifact $BaselineManifest '^ruff-openapi-d10-baseline-[0-9a-f]{32}$' 'run-manifest.json'
if ((Get-FileHash -LiteralPath $BaselineManifest -Algorithm SHA256).Hash -ne $BaselineManifestSha256) { throw 'Baseline Ruff manifest pin mismatch; stop.' }
& $Python -I $TaskRunner -Action Check -Tool Ruff -Phase post -PythonPath $Python -Backend $Backend -RunRoot $RunRoot -LockEvidencePath $LockEvidencePath -LockEvidenceSha256 $LockEvidenceSha256 -Paths @('src/sketch2life/interfaces/http/app.py','tests/contract/test_openapi_contract_catalog.py','tests/contract/test_openapi_schema_catalog_mapping.py') -BaselineManifestPath $BaselineManifest -BaselineManifestSha256 $BaselineManifestSha256
$RunnerExit = $LASTEXITCODE
$RunManifest = Join-Path $RunRoot 'run-manifest.json'
if (-not (Test-Path -LiteralPath $RunManifest -PathType Leaf)) { throw 'Task runner did not finalize run-manifest.json; stop without retry.' }
$RunManifest = Assert-GeneratedArtifact $RunManifest '^ruff-openapi-d10-post-[0-9a-f]{32}$' 'run-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $RunManifest | ConvertFrom-Json -ErrorAction Stop
Get-FileHash -LiteralPath $RunManifest -Algorithm SHA256
if ($RunnerExit -ne 0 -or $Manifest.tool -ne 'Ruff' -or $Manifest.phase -ne 'post' -or $Manifest.success -ne $true -or $Manifest.comparison.passed -ne $true -or $Manifest.comparison.baselineManifestSha256 -ne $BaselineManifestSha256 -or $Manifest.comparison.unparsedCount -ne 0 -or $null -eq $Manifest.comparison.sharedPathAddedSignatures -or $Manifest.comparison.sharedPathAddedSignatures.Count -ne 0 -or $null -eq $Manifest.newPathDiagnostics -or $Manifest.newPathDiagnostics.count -ne 0) { throw 'Ruff regression-delta comparison, zero-new-path diagnostics, or structured evidence failed; retain evidence and stop.' }
if ($Manifest.toolExitCode -ne 0 -or $Manifest.toolClean -ne $true) { Write-Output "NOT CLEAN: Ruff toolExitCode=$($Manifest.toolExitCode), toolClean=$($Manifest.toolClean); retain evidence and stop."; throw 'Ruff post is not a clean tool pass even if the baseline-relative delta is zero.' }
```

The child bootstrap writes the tool's raw output to `check-raw-output.txt` in the run root, and the task runner records that file's state and SHA-256 together with the tool exit code, exact inputs and normalized signatures in `run-manifest.json` before returning, including nonzero tool exits. A nonzero runner/capture failure, unparsed diagnostic, new signature, missing/changed baseline, or (for Ruff) any N-path diagnostic stops the sequence. A captured nonzero Mypy/Ruff tool exit or any remaining diagnostic is **NOT CLEAN**. Each post card explicitly requires toolExitCode == 0 and toolClean == true after the baseline-relative delta check; a zero delta alone cannot pass the command. Baseline Ruff records the N path as `ABSENT_NOT_SELECTED`; it does not claim that path passed. Draft 10's baseline selection included the absent N path; this proposal corrects it. Mypy/Ruff ceilings: 2 invocations per tool (one baseline before edits and one post after edits), no retries. Historical recorded diagnostics were 335 mypy errors and 17 Ruff diagnostics; they are not substitutes for fresh outputs.

### Validator and diff check

Repository security validator: ceiling 0 / not proposed for this mapper verification. `git diff --check`: ceiling 0 / not proposed. Neither ran. Repository security validation remains a separate commit/push governance gate and would require its own authorization; no stage/commit/push is proposed here.

### Proposed ceilings and evidence paths

The completed lock-resolution evidence is a supplied prerequisite and is not counted as a command. No environment-provenance collection command is included in this task's ceilings.

| Command | Workdir | Proposed ceiling | Required outputs / success signal / stop |
|---|---|---:|---|
| OpenAPI pre export | `$Backend` | 1 | `runtime-pre.json`, `published-pre.json`, sanitized `environment.json`, `source-state.json`, console log, finalized `run-manifest.json` and hashes. Stop on nonzero/missing/profile drift. |
| OpenAPI post export | `$Backend` | 1 | `runtime-post.json`, `published-post.json`, sanitized `environment.json`, `source-state.json`, console log, finalized `run-manifest.json` and hashes. Stop on nonzero/missing/environment mismatch. |
| Field-level comparator | `$Backend` | 1 | JSON report with schema and source-state deltas/invariant detail, console log, finalized `run-manifest.json` and `sha256.txt`; require exit 0 and `passed:true`. Stop on any unapproved schema or source-state delta. |
| Three exact post-implementation pytest selections | `$Backend` | 1 total | JUnit + console + comparator report + finalized `run-manifest.json`; require runner/pytest exit 0, JUnit present and comparator `passed:true`. Retain outputs and stop on failure; no pre-run or retry. |
| Mypy baseline/post | `$Backend` | 2 total | Raw tool output (`check-raw-output.txt`), tool exit codes and hashes in distinct GUID roots. Baseline is a capture/reference even with historical findings; post delta requires zero added signatures and zero unparsed diagnostics. If findings or a nonzero tool exit remain, report **NOT CLEAN**, not pass. |
| Ruff baseline/post | `$Backend` | 2 total | Baseline selects E paths only and records N as `ABSENT_NOT_SELECTED`; post selects E+N. Require zero added E signatures, zero N diagnostics and zero unparsed diagnostics. Any remaining finding/nonzero tool exit is **NOT CLEAN**, not pass. |
| Repository validator | repository root | 0 | Not proposed/run for this task. |
| `git diff --check` | repository root | 0 | Not proposed/run for this task. |

Suggested ignored outputs, all under fresh roots in `backend/tmp/`:

- `openapi-mapper-d10-pre-<guid>/` and `openapi-mapper-d10-post-<guid>/` for schema JSON, sanitized environment and source-state manifests, console logs and SHA-256.
- `openapi-mapper-d10-compare-<guid>/field-delta-report.json`, `comparator.console.txt`, and `sha256.txt` for the eight pinned comparison inputs and comparator outputs.
- `pytest-openapi-d10-<guid>/pytest-basetemp/`, `pytest.junit.xml`, `pytest.console.txt`, and `run-manifest.json`.
- `mypy-openapi-d10-baseline-<guid>/`, `mypy-openapi-d10-post-<guid>/`, `ruff-openapi-d10-baseline-<guid>/`, and `ruff-openapi-d10-post-<guid>/` for the raw tool output, console log, exit codes, normalized diagnostic signatures and finalized `run-manifest.json` hashes.
- Proposed feature evidence destination after a separately approved run: `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_SHARED_OPENAPI_MAPPER_IMPLEMENTATION_EVIDENCE_20261116.md`. Do not create it as part of this review draft.

All D-207/FEAT-047/previous S2 command ceilings are consumed. These proposed ceilings are new proposals only and do not authorize a run. Any eventual execution requires the owner-approved exact Task Approval, exact pinned task runner/launcher/exporter/comparator source, completed lock-resolution evidence, confirmed environment/isolation, and a separate direct launch instruction.

## 5. Risks, stop conditions and owner decisions

### R14 and R15 dispositions in this planning revision

R14 (Claude Opus 5.5, not sandboxed) reported 0 P1, 0 P2 and 3 P3; R15 (Codex, read-only sandbox) reported ACCEPT with no finding, on the same pin. Under the stop rule agreed with the owner on 2026-11-17 the full-round review gate is met; the three P3 findings are corrected here and only the changed lines are checked again.

- **R14 F-1 (P3) — rehearsal wording:** §7 and the R12/R13 list now describe the rehearsal as the record does (variants, several runs, wrapper), and the `_safe_changed_path` sample calls are attributed to a separate probe, not to the rehearsal runs.
- **R14 F-2 (P3) — path form:** the R12 F-1 disposition now states the dependency on the card path having the on-disk spelling and letter case; no code change. The command cards build their run roots from the fixed canonical `$Backend` string.
- **R14 F-3 (P3) — blocked Mypy run:** the child bootstrap treats a Mypy exit status of 2 or higher, or output containing "errors prevented further checking", as a failed capture (`captureComplete` and `success` false).
- **R14 unverified items, tracked for the baseline run:** Windows PowerShell 5.1 quoting of native arguments that contain spaces (the Git executable path); Mypy import resolution in the lock-exact environment, which does not install the project; the comparator's choice of the first 2xx status where an operation declares more than one; pytest plugins and conftest files.

### R12, R13 and rehearsal dispositions in this planning revision

R12 (Claude Opus 5.5, not sandboxed) and R13 (Codex, read-only sandbox) reviewed the same pin independently. Between those reviews and this revision the owner authorized a rehearsal of the payloads on a synthetic worktree; its record is `evidence/M2_S2_SHARED_OPENAPI_MAPPER_PAYLOAD_REHEARSAL_20261117.md`, 5,619 bytes / SHA-256 `33B8C549F705E1CE6114E4A8AE26857F131EA5FE9FA82C4E8EC7A0EE6828675B`.

- **R12 F-1 (P1) — exporter environment root:** the exporter now validates the child environment against the run root (`Path(args.RunRoot).absolute()` applied to the run-root string that the child bootstrap forwards after resolving it; the runner builds the environment from the unresolved absolute form of the card's string, so the two agree only when the card's path already has the on-disk spelling and letter case, and a difference fails closed); the worktree root is used only for source identity and lock-file reads. In the rehearsal the reviewed code failed with the predicted mismatch, and the same code with this one-line change passed every check up to the first application import, for both the pre and the post phase.
- **R13 P2 — criterion 12 enforced while unaccepted:** resolved by owner decision. The owner accepted criterion 12 for planning on 2026-11-17, so the pinned-input gate in the exporter and comparator is now part of the accepted planning set. Statements in older disposition lists of this section that call criterion 12 proposed or not accepted describe earlier revisions.
- **R13 P2 — comparator no-read policy and `.env` path components: not reproduced, no change.** The comparator's `NO_READ_PARTS` tuple begins with `.env`, and `_safe_changed_path` rejects a path when any case-folded component contains any of those tokens. In a separate probe on 2026-11-17 that is not one of the runs listed in the rehearsal record, the coordinating session called that function, taken from the reviewed bytes, with sample paths: `.env-cache/file.py`, `a/.env/b.py`, `a/.ENV.local` and `a/b/.env` were rejected, `src/environment.py` and `ok/path/file.py` were accepted.
- **R12 F-2 (P3):** the two `Get-Item` calls of the Compare card that were outside the helpers are wrapped and throw fixed, path-free text.
- **Rehearsal finding (P3) — Mypy file-level diagnostics:** the Mypy output pattern in the child bootstrap now accepts a diagnostic without a line number; such a line was previously counted as unparsed and made the Check action fail closed.
- **Rehearsal observations, disclosed:** pytest's own console output can contain absolute local paths (seen in a collection error) and is stored in the ignored run root like other tool output; the comparator report's `inputs` list and the run manifests record absolute paths by design.
- **What the rehearsal did not cover:** application construction, real runtime and published schema content, the comparator's schema-content rules, the three real pytest selections and Mypy on the real package tree. Those remain reviewed statically only until the separately authorized baseline run.
- **Owner evidence package (not part of this proposal's ceilings):** on 2026-11-17 the owner authorized creating a lock-exact environment outside the worktree and read-only probes. The package lists the interpreter path and SHA-256, a schemaVersion 2 lock-resolution JSON (107 of 107 distributions equal to the lock resolution, FastAPI 0.162.0), two Git executable candidates that both work in the minimal child environment, and a draft source inventory that must be regenerated immediately before the pre export. The runner and exporter accepted that lock-resolution JSON in the rehearsal. It remains OWNER-PROVIDED / NOT VERIFIED until the owner pins it; the OS-level egress confirmation is still outstanding.

### R10 and R11 finding dispositions in this planning revision

R10 (Claude Opus 5.5, not sandboxed) and R11 (Codex, read-only sandbox) reviewed the same pin independently and in parallel.

- **R10 F-1 (P1) — pinned-input cross-check:** the comparator now compares a pinned input with its Git-visible changed-path row over `status`, `state`, `bytes` and `sha256` only. The exporter's `pinnedInputStates` rows carry no `path` key (the path is the map key), so the former five-field comparison could never match.
- **R11 P2 — comparator report pin (completes R8 F2):** the Pytest card passes the pinned report SHA-256 as `-ComparatorReportSha256`. The runner rejects a missing, malformed or mismatched pin before launch; the child bootstrap and the pytest bootstrap each read the report bytes once, compare their SHA-256 with the pin, and parse those same bytes. The card's checks before launch and after pytest remain.
- **R10 F-2 (P3):** the Mypy/Ruff baseline/post delta is a multiset difference, so an additional occurrence of an existing signature counts as added. A null Ruff `code` is normalized to an empty string.
- **R10 F-3 (P3):** the R5-era preflight bullet in §1 is labelled historical and §1 records the pin recheck made for this revision.
- **R11 P3 — PowerShell path guards:** the three path helpers in every card catch `Get-Item` failures and throw fixed, path-free text. Disclosed residual: other cmdlet failures in a card (`Get-FileHash`, `Get-Content`, `New-Item`, `Set-Content`) can print the path of an owner-supplied or generated file on the operator's console; the cards do not write that text to an evidence artifact.
- **R10 informational notes — tracked, not changed:** the runner's appended `sha256.txt` rows use bare file names, so the pre and post `environment.json` and `source-state.json` rows are distinguished by order; the unreachable `sha256.txt` name filter remains; the comparator repeats two imports.

### R9 finding dispositions in this planning revision

- **F-A (P2) — check evidence:** the child bootstrap writes each Mypy or Ruff run's raw output to `check-raw-output.txt` in the run root (Ruff standard error follows a marker line), and the runner lists that file among the Check action's expected artifacts, so its state and SHA-256 are in `run-manifest.json`. The prose now says signatures use the backend-relative path, severity, code and normalized message, and that line and column numbers exist only in the raw artifact. The raw artifact can contain local paths; it stays in the git-ignored run root and must be sanitized before any part of it is copied into repository evidence.
- **F-B (P3) — isolated-mode variables:** the child bootstrap sets `sys.dont_write_bytecode = True` before it extends `sys.path` or runs a payload; the runner starts the child with `-X utf8` and decodes captured output as UTF-8 with replacement, and the bootstrap decodes Ruff output the same way. Disclosed: because the child runs with `-I`, the `PYTHONPATH`, `PYTHONNOUSERSITE`, `PYTHONDONTWRITEBYTECODE` and `PYTHONUTF8` entries of the child environment are ignored by the isolated interpreter itself; their effect is applied in-process as described, they still apply to the non-isolated Ruff subprocess, and the manifests' value categories describe the variable values, not interpreter behaviour. `__pycache__/` is ignored by the worktree `.gitignore`.
- **F-C (P3):** the child bootstrap entry point now converts any exception outside `main()`'s own handler into exit code 1 without a traceback.
- **N-2:** the export card derives the run-root name from `$Phase`.
- **N-4:** the risk bullets are back under the "Risks / dependencies" heading.
- **N-5:** the Compare prose names the invocation record among the appended `sha256.txt` rows.
- **N-1 and N-3 — tracked, not changed:** the exporter and pytest bootstrap parse the lock-evidence JSON before comparing its hash, after the runner has already verified that hash; the Pytest card's artifact lookups do not require exactly one match, and the pinned runner always produces unique artifact names.

### R8 finding dispositions in this planning revision

- **F1 (P1) — Compare input forwarding:** the runner forwards only the eight generated schema/state inputs, in order, as `-InputPaths`; the Git executable and lock evidence stay in the runner's own `inputs` hash list and are no longer forwarded. The comparator's `nargs=8` parser therefore receives exactly eight values. Static cross-check of argument names and counts for every card against the runner, child-bootstrap and payload parsers was repeated by reading; nothing was executed.
- **F2 (P2) — comparator report pin for Pytest:** the Pytest card takes the `field-delta-report.json` SHA-256 printed by the accepted Compare card as a required input, verifies it after the generated-artifact check and before reading the report, and verifies it again after pytest returns.
- **F3 (P3):** the Pytest card defines and guards the pytest-bootstrap payload together with the other external inputs, before its first hash.
- **F4 (P3):** the comparator's duplicate and out-of-allowlist row rejections use fixed text without the rejected path.
- **F5 (P3):** the comparator prose no longer claims the fixture runtime-only set check; that check belongs to the selected contract test in the Pytest card.
- **F6 (P3):** the uncalled `compare_pair` function was removed from the comparator payload.
- **F7 (P3):** the runner appends its hash rows to `sha256.txt` under a marker line; the card's initial rows are kept.
- **F8 (P3):** the runner validates the approved worktree path from the drive root and the worktree-to-backend chain for reparse points before it may create `backend\tmp`.
- **F9 (P3):** the comparator gate text attributes pinned-input comparisons to proposed criterion 12.
- **F10 (P3) — disclosed limitation, not changed:** the comparator imports the catalog, amendments and SRS-projection modules from the worktree at compare time without re-hashing them; it relies on the post-export `pinnedInputStates` record and on the Compare card running immediately after the post export with no source edit in between. A source change between post export and compare is not detected by the comparator itself. Separately, a Python argument-parser usage error prints the offending argument value; the cards pass only validated paths and fixed option names, and this residual is disclosed rather than removed.

### R7 finding dispositions in this planning revision

- **P2 — external-input path/order guard:** the PowerShell cards validate external helper/evidence paths before hashing or launching Python; the runner repeats canonical/reparse/worktree-boundary checks before reading those inputs. Generated `backend\tmp` artifacts and the two fixed project/lock reads are stated as narrowly scoped exceptions above, with their checks and reasons. The ordering claim is limited to those exact reads. Every launch card (OpenApiExport, Compare, Pytest, Mypy baseline/post and Ruff baseline/post) calls the external-file guard for its task runner, sibling bootstrap, interpreter, lock evidence and action payload before its first hash or Python launch, and applies the generated-artifact check to each run manifest, comparator report and baseline manifest before reading it. The runner applies the same external-file check to the interpreter before hashing it.
- **P3 — subprocess launch exception:** before launch, the runner writes one invocation record and enumerates expected artifacts. If `subprocess.run` raises before returning, it writes a fixed launch-failure marker, finalizes each artifact state without treating MISSING as success, and emits a failed run manifest with `success: false`, `captureComplete: false`, and `failureEvidenceState` set to `COMPLETE_FAILURE_RECORD` or `INCOMPLETE`. It never retries. If any required evidence write fails or the final manifest is absent, the caller reports evidence incomplete and stops.
- **P3 — path-bearing diagnostics:** safety errors use fixed codes/generic text and exception type only; they do not interpolate a local filesystem path or exception message. Validated repository-relative path rows remain in the source-state inventory/report as required for comparison. Rejected or excluded paths do not enter report maps. OpenAPI method/path fields in schema deltas remain because they are contract identifiers, not local filesystem paths.
- **P3 — criterion 12 disposition:** criterion 12 is marked proposed/not accepted and excluded from current acceptance criteria. No owner acceptance is inferred.

### Risks / dependencies

- The accepted FastAPI range is a task-specific exception to the exact lock pin. Actual version, exact platform/group resolution, and all other installed distributions remain **OWNER-PROVIDED / NOT VERIFIED**; 0.162.7 must never be called lock-matched.
- Exact review-only payload bytes and hashes are now included in §7, but none are owner-approved or pinned by the FEAT-063 task-specific approval record. The command cards remain non-executable placeholders until that happens.
- Source inspection cannot prove runtime absence of database, network, or provider access. Owner-confirmed OS-level egress blocking remains mandatory.
- Request-ID inventory remains OPEN and fail-closed. Any addition, removal, or value delta to an `X-Request-ID` parameter/header object requires owner decision before comparator acceptance or later pytest.
- Ruff baseline must omit the absent N path and post must include it; this split is owner-accepted as planning direction. Existing diagnostics remain debt, not a pass; the proposed comparison thresholds are conditional on exact payload approval and do not establish clean lint/typecheck.
- Pytest's process-level synthetic S3 values are not consumed by the selected test's directly constructed, monkeypatched `Settings` instance. No test edit or scope expansion is included.
- Draft 10 review remains ACCEPT WITH CORRECTIONS with its one P2. The proposed fail-fast/verification sequence does not alter that verdict.
- M2-S2 remains PARTIAL / NOT COMPLETE. This mapper task does not authorize or close M2-S3.

### Owner dispositions — recorded, planning direction only

| # | Owner-accepted disposition | Current execution/evidence state |
|---:|---|---|
| 1 | **Accepted for planning:** exact E/E/N/R allowlist and acceptance criteria 1–11; criterion 12 was added to the accepted planning set by the owner on 2026-11-17. Preserve mapper Option A (exact public `(method.lower(), path)` lookup) and allowlist Choice A. `operationId` remains unchanged and unique as an invariant, never a lookup key. | Not formal implementation approval. The four-path scope remains the only proposed implementation allowlist. |
| 2 | **Accepted environment policy:** FastAPI `0.162.0` through `0.162.7` inclusive is an explicit task-specific exception to `uv.lock`'s exact `0.162.0` pin. Record the actual version used. Every other installed package must match the applicable platform/group lock resolution. Do not modify `pyproject.toml` or `uv.lock`. | Lock-resolution evidence including canonical interpreter path and executable SHA-256, platform/group resolution and actual version for a future run is **OWNER-PROVIDED / NOT VERIFIED**. `0.162.7` is permitted by this exception, not lock-matched. |
| 3 | **Not confirmed:** OS-level egress blocking and the cleared child-process/credential boundary. | Owner must provide the OS/sandbox policy and confirmation before any exporter, comparator or pytest process. Source inspection and environment variables are insufficient. |
| 4 | **Not approved yet:** review the exact payload bytes and SHA-256 in §7 for task runner, child launcher/bootstrap, exporter, comparator, pytest bootstrap, and source-state manifest contract. | Payloads are prepared in this draft but are not approved, installed, or pinned by the FEAT-063 task-specific approval record. No command may use them yet. |
| 5 | **Conditionally accepted:** proposed ceilings, GUID roots, artifacts, retry limits and stop rules in §4, only after exact runner/payloads are pinned and approved. | Conditional planning decision only; it is not permission to execute any ceiling. D-207/FEAT-047/S2 ceilings remain consumed and are not reused. |
| 6 | **Accepted for planning:** Ruff baseline covers existing E paths only; post covers E plus N; no new shared-path signatures and zero N-path diagnostics. | Historical Ruff diagnostics are debt, not a pass. Baseline/post evidence is still absent. The current N path is ABSENT and has no pre-implementation hash. |
| 7 | **Accepted:** request-ID method/path and JSON-pointer inventory stays OPEN and fail-closed. No request-ID delta or inferred per-path allowlist is authorized. | Any request-ID schema delta blocks comparison and requires a separate owner decision. |
| 8 | **Future conditional step only:** one pre-fix export may be the first command after every prerequisite and formal approval. | This is not a current launch instruction. Baseline collection has not been launched or performed. |
| 9 | **Accepted sequence:** exact-record approval → separate baseline-only instruction → owner review of outputs → separate implementation launch instruction. | No current approval, baseline instruction, or implementation launch instruction exists in this proposal. |

### Prerequisite and evidence checklist

**BE session can prepare from current pinned files (no runtime evidence):**

- Keep the four-path allowlist, acceptance criteria 1–12, Option A, Choice A and request-ID fail-closed inventory pinned in this draft.
- Provide the proposed exact payload bytes/hashes in §7 and command cards/manifest schemas in §§3–4; preserve current source, test, SRS, Draft 10 and review pins.
- Prepare the source-state manifest contract only. Do not claim a current pre-fix manifest or execution result.

**Owner/environment confirmation still required before any command:**

- Supply the canonical pre-provisioned interpreter path and its `interpreterExecutableSha256`, plus sanitized environment identity; exact OS/platform, Python tags/markers, dependency groups/extras, lock and project hashes; a complete installed-distribution versus lock-resolution comparison; and the actual FastAPI version. The sanitized JSON must carry `fastapiInstalledVersion`, `fastapiLockVersion: "0.162.0"`, `allNonFastApiPackagesMatch: true`, the exact platform/Python identity, both current project/lock hashes, selected groups, complete distribution records and resolution method/tool identity. FastAPI must be within 0.162.0–0.162.7; all other distributions must match the selected lock resolution. This evidence is **OWNER-PROVIDED / NOT VERIFIED**.
- Confirm the OS/sandbox egress block for the child-process boundary, the environment allowlist, and exclusion of ambient credentials/database/provider access. No secret values are requested or to be displayed. This evidence is **OWNER-PROVIDED / NOT VERIFIED**.
- Review and approve the exact §7 payload bytes/hashes and the conditional §4 ceilings. The FEAT-063 task-specific approval record currently has no mapper-specific approval and is pinned at 410,676 bytes / `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088`. The separate worktree-root ledger is pinned at 32,311 bytes / `114E1C8834B9AB8E4DCAA8E0779CBF37A2855E242BD79D363C2DF88BADB04973` and is not the FEAT-063 task-specific record.
- Supply and pin the owner-reviewed source path/status inventory required by criterion 11; it must enumerate exact pre/post path/status expectations and HASH/EXCLUDED_NO_READ dispositions without reading changed-file contents. Any excluded or unsafe row stops before content access.
- Separately approve the exact final Task Approval record in the FEAT-063 task-specific approval record through the official process, then issue a direct baseline-only launch instruction naming that approval pin, canonical interpreter path and executable SHA-256, payload hashes, source-inventory path/hash, backend workdir, output root, first command, ceiling and isolation evidence.

**Evidence only after a separate authorized command:**

- One pre-fix export: runtime/published JSON, sanitized environment identity, source-state manifest, log, run manifest and hashes. Return these outputs for owner review; do not run comparator or tests in this step.
- Only after owner reviews baseline and issues a separate implementation launch: exact E/E/N/R source-state transition, post export, field-level comparator report, and the separately approved pytest/Mypy/Ruff outputs within their ceilings.
- Any missing output, failed guard, export-manifest mapping failure, artifact/manifest SHA-256 mismatch, malformed/non-object schema JSON, wrong-case/missing required OpenAPI property, comparator entry point with anything other than one guarded main or any missing/bypassed guard call for the four runtime/published roots, comparator schema-root validation failure, missing comparator report or `passed: true`, pin drift, out-of-allowlist source-state delta, request-ID delta, environment mismatch or nonzero/unparsed command outcome stops the sequence; retain available evidence and wait for owner direction without retry.

## 6. Current execution boundary

This document is a review draft only. No baseline, test, comparator, typecheck, lint, validator, diff check, build, app/runtime, database, migration, Docker, install/sync, network, provider, Modal or emulator command was run for it. No implementation was performed. Draft 10 and its cold-review evidence remain unchanged. No approval is recorded, no launch is authorized, and no S2 completion is claimed. The only executions connected with this draft are the owner-authorized rehearsal on a synthetic worktree and the read-only environment probes recorded in §5; neither wrote to the approved worktree, produced baseline evidence, or counts against any ceiling.

## 7. Exact review-only payload proposal

The five payloads below are prepared for owner review, **NOT APPROVED / NOT LAUNCHABLE**. They are not source or test edits. To materialize them later, copy each code-fence body byte-for-byte as UTF-8 without BOM, normalize line endings to LF, and include exactly one final LF. The fence markers and surrounding prose are excluded from each payload hash. The fixed SHA-256 roster is recorded immediately before the payloads. These scripts have not been executed against the approved worktree, and have not been linted, typechecked or validated. Rehearsal copies of two earlier pins were executed on synthetic worktrees under owner authorization, in several runs: one variant differed from the reviewed bytes only in two path/HEAD constants, a second variant of the first rehearsal also carried the R12 F-1 correction, and each action payload was started through a wrapper that calls its `main()` instead of the child bootstrap's `runpy` call (see the R12/R13 and R14 dispositions in §5); their presence is not evidence that runtime behavior, egress isolation, or dependency compatibility has been verified.

The child process allowlist generates synthetic S3 values in memory and never logs or hashes them. It sets `SKETCH2LIFE_S3_ACCESS_KEY` and `SKETCH2LIFE_S3_SECRET_KEY` before app import/construction for both exporter and pytest. The selected pytest node may explicitly pass empty S3 fields to `Settings` and monkeypatch `app_module.get_settings`; those fields can remain empty and the app may construct a Boto3 client with `None` credentials. The process variables therefore do not protect that object. The isolated HOME/USERPROFILE, absent AWS files, metadata disablement, cleared environment and owner-confirmed OS egress block remain required. A fixture credential change would be a separate allowlist decision.

### Payload hash roster

| Payload | Canonical bytes | SHA-256 | State |
|---|---:|---|---|
| `task-runner.py` | 41458 | `A5E339B1374F23542FD83E2CF42658B307346F380656BE2B2DD7C0A24415351B` | Prepared here; owner approval required |
| `child-bootstrap.py` | 11725 | `2633055A83C5ABEE45AC9A45E6F679DC4168BC1C099B0FD691065C04252120E7` | Prepared here; owner approval required |
| `openapi-export.py` | 36158 | `AAF3F04E1F402871FC4DA948BF0538480E7BE39E2AABDCF129390E66F2F8589F` | Prepared here; owner approval required |
| `schema-comparator.py` | 49730 | `4CB27EA71D419BEBCF99ABB0142D2B789D226A84F2665B2F76C96A5B21402A14` | Prepared here; owner approval required |
| `pytest-bootstrap.py` | 13951 | `8EC5337FA7D97EC59FE6B5291C4EA6F3C874CC2B06EE008CE2D55813EE44AAC4` | Prepared here; owner approval required |

### `task-runner.py`

<!-- payload-begin:task-runner.py -->
```python
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import secrets
import stat
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

from packaging.markers import default_environment
from packaging.tags import sys_tags

WORKTREE = Path(r"D:\GitHub\Sketch2Life\.worktrees\m2-s2")
EXPECTED_BRANCH = "feature/feat063-m2-s2"
EXPECTED_HEAD = "5de30674bc826591ad4b3cc00fca53c7597ead51"
BACKEND = WORKTREE / "backend"
BOOTSTRAP_SHA256 = "2633055A83C5ABEE45AC9A45E6F679DC4168BC1C099B0FD691065C04252120E7"
REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def reparse(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & REPARSE)


def canonical_existing_path(value: str, label: str, kind: str) -> Path:
    if (not isinstance(value, str) or not re.match(r"^[A-Za-z]:[\\/]", value)
            or os.path.normcase(os.path.normpath(value)) != os.path.normcase(value)):
        raise RuntimeError(f"{label} path is not a canonical drive-rooted absolute path")
    candidate = Path(value)
    if not candidate.is_absolute() or ".." in candidate.parts:
        raise RuntimeError(f"{label} path is not canonical")
    current = Path(candidate.anchor)
    try:
        for part in candidate.parts[1:]:
            current = current / part
            if reparse(current):
                raise RuntimeError(f"{label} path contains a symlink or reparse point")
        canonical = candidate.resolve(strict=True)
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError(f"{label} path failed existence or boundary preflight") from None
    if os.path.normcase(str(canonical)) != os.path.normcase(os.path.abspath(value)):
        raise RuntimeError(f"{label} path does not resolve to its supplied canonical path")
    if kind == "file" and not canonical.is_file():
        raise RuntimeError(f"{label} path is not a regular file")
    if kind == "directory" and not canonical.is_dir():
        raise RuntimeError(f"{label} path is not a directory")
    return canonical


def external_file(value: str, label: str) -> Path:
    canonical = canonical_existing_path(value, label, "file")
    worktree = canonical_existing_path(str(WORKTREE), "approved worktree", "directory")
    try:
        common = os.path.commonpath((os.path.normcase(str(canonical)), os.path.normcase(str(worktree))))
    except ValueError:
        common = ""
    if common == os.path.normcase(str(worktree)):
        raise RuntimeError(f"{label} path must be outside the approved worktree")
    return canonical


def generated_artifact(value: str, tmp: Path, label: str, root_pattern: str,
                       expected_name: str) -> Path:
    canonical = canonical_existing_path(value, label, "file")
    canonical_tmp = canonical_existing_path(str(tmp), "approved backend tmp", "directory")
    parent = canonical.parent
    if (parent.parent != canonical_tmp or not re.fullmatch(root_pattern, parent.name)
            or canonical.name != expected_name):
        raise RuntimeError(f"{label} is not an expected artifact under a GUID output root")
    return canonical


def output_child(value: str, root: Path, label: str) -> Path:
    if (not isinstance(value, str) or not re.match(r"^[A-Za-z]:[\\/]", value)
            or os.path.normcase(os.path.normpath(value)) != os.path.normcase(value)):
        raise RuntimeError(f"{label} destination is not a canonical absolute path")
    candidate = Path(value)
    parent = canonical_existing_path(str(candidate.parent), f"{label} parent", "directory")
    if parent != root:
        raise RuntimeError(f"{label} destination must be a direct child of its verified output root")
    try:
        candidate.lstat()
    except FileNotFoundError:
        return candidate
    raise RuntimeError(f"{label} destination already exists")


def guard_chain(path: Path, stop: Path) -> None:
    current = path
    stop = stop.resolve(strict=True)
    while True:
        if reparse(current):
            raise RuntimeError("reparse point rejected")
        if current.resolve(strict=True) == stop:
            return
        if current.parent == current or stop not in current.parents:
            raise RuntimeError("path escaped the approved worktree")
        current = current.parent


def write_json(path: Path, value: object, exclusive: bool = False) -> None:
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-Action", required=True, choices=("OpenApiExport", "Compare", "Pytest", "Check"))
    parser.add_argument("-Phase", default="")
    parser.add_argument("-Tool", default="")
    parser.add_argument("-PythonPath", required=True)
    parser.add_argument("-Backend", required=True)
    parser.add_argument("-RunRoot", required=True)
    parser.add_argument("-RootAlreadyCreated", action="store_true")
    parser.add_argument("-PayloadPath", default="")
    parser.add_argument("-PayloadSha256", default="")
    parser.add_argument("-InputPaths", nargs="*", default=[])
    parser.add_argument("-ReportPath", default="")
    parser.add_argument("-ConsoleLogPath", default="")
    parser.add_argument("-BaseTemp", default="")
    parser.add_argument("-JunitPath", default="")
    parser.add_argument("-ComparatorReportPath", default="")
    parser.add_argument("-ComparatorReportSha256", default="")
    parser.add_argument("-Selections", nargs="*", default=[])
    parser.add_argument("-Paths", nargs="*", default=[])
    parser.add_argument("-BaselineManifestPath", default="")
    parser.add_argument("-BaselineManifestSha256", default="")
    parser.add_argument("-LockEvidencePath", default="")
    parser.add_argument("-LockEvidenceSha256", default="")
    parser.add_argument("-SourceInventoryPath", default="")
    parser.add_argument("-SourceInventorySha256", default="")
    parser.add_argument("-GitExecutablePath", default="")
    parser.add_argument("-GitExecutableSha256", default="")
    return parser.parse_args()


def normalized_distribution_records(records: object, label: str) -> dict[str, str]:
    if not isinstance(records, list):
        raise RuntimeError(f"{label} distribution records are missing")
    result: dict[str, str] = {}
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not isinstance(row.get("version"), str):
            raise RuntimeError(f"{label} distribution record is malformed")
        name = re.sub(r"[-_.]+", "-", row["name"]).lower()
        if not name or name in result:
            raise RuntimeError(f"{label} distribution names are empty or duplicated")
        result[name] = row["version"]
    return result


def installed_distribution_records() -> dict[str, str]:
    records = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if not isinstance(name, str) or not name.strip():
            raise RuntimeError("installed distribution has no normalized name")
        records.append({"name": name, "version": distribution.version})
    return normalized_distribution_records(records, "installed")


def normalized_environment_identity(
    root: Path,
    backend: Path,
    lock_data: dict[str, object],
    lock_evidence_sha256: str,
    environment: dict[str, str],
    action: str,
) -> dict[str, object]:
    normalized_environment: dict[str, str] = {}
    for name, value in environment.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise RuntimeError("effective child environment contains a non-string name or value")
        key = name.upper()
        if key in normalized_environment:
            raise RuntimeError("effective child environment contains case-colliding names")
        normalized_environment[key] = value

    expected_names = {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "PYTHONPATH",
        "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "PYTHONUTF8",
        "PYTHON_DOTENV_DISABLED", "HOME", "USERPROFILE", "TEMP", "TMP", "TMPDIR",
        "AWS_EC2_METADATA_DISABLED", "AWS_CONFIG_FILE", "AWS_SHARED_CREDENTIALS_FILE",
        "AWS_DEFAULT_REGION", "SKETCH2LIFE_ENV", "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "SKETCH2LIFE_BE1_ARTIFACT_ROOT",
        "SKETCH2LIFE_S3_ACCESS_KEY", "SKETCH2LIFE_S3_SECRET_KEY",
        "SKETCH2LIFE_DATABASE_URL", "STORYRUN_LITE_MAIN_DEMO_ENABLED",
    }
    if set(normalized_environment) != expected_names:
        raise RuntimeError("effective child environment variable-name allowlist mismatch")
    env = normalized_environment
    system_root = env.get("SYSTEMROOT", "")
    export_enabled = action == "OpenApiExport"
    expected_values = {
        "WINDIR": system_root,
        "PATH": os.pathsep.join((str(Path(sys.executable).parent), str(Path(system_root) / "System32"))),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PYTHONPATH": str(backend / "src"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "HOME": str(root / "home"),
        "USERPROFILE": str(root / "home"),
        "TEMP": str(root / "temp"),
        "TMP": str(root / "temp"),
        "TMPDIR": str(root / "temp"),
        "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_CONFIG_FILE": str(root / "absent-aws-config"),
        "AWS_SHARED_CREDENTIALS_FILE": str(root / "absent-aws-credentials"),
        "AWS_DEFAULT_REGION": "us-east-1",
        "SKETCH2LIFE_ENV": "local",
        "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED": "true" if export_enabled else "false",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "true" if export_enabled else "false",
        "SKETCH2LIFE_BE1_ARTIFACT_ROOT": str(root / "artifacts"),
        "STORYRUN_LITE_MAIN_DEMO_ENABLED": "0",
    }
    if not system_root or any(env.get(name) != value for name, value in expected_values.items()):
        raise RuntimeError("effective child environment category or path mismatch")
    if (not env["SKETCH2LIFE_S3_ACCESS_KEY"].startswith("synthetic-")
            or not env["SKETCH2LIFE_S3_SECRET_KEY"].startswith("synthetic-")):
        raise RuntimeError("S3 credentials are not synthetic-only")

    database = urlsplit(env["SKETCH2LIFE_DATABASE_URL"])
    if (database.scheme != "postgresql+psycopg" or database.hostname != "127.0.0.1"
            or database.port != 1 or database.path != "/mapper_sentinel"
            or not re.fullmatch(r"[0-9a-f]{24}", database.username or "")
            or not re.fullmatch(r"[0-9a-f]{48}", database.password or "")):
        raise RuntimeError("database sentinel configuration mismatch")
    if (Path(env["AWS_CONFIG_FILE"]).exists()
            or Path(env["AWS_SHARED_CREDENTIALS_FILE"]).exists()):
        raise RuntimeError("AWS credential sentinel path unexpectedly exists")

    interpreter_path = Path(sys.executable).resolve(strict=True)
    interpreter_sha256 = sha(interpreter_path.read_bytes())
    fastapi_version = importlib.metadata.version("fastapi")
    if not re.fullmatch(r"0\.162\.[0-7]", fastapi_version):
        raise RuntimeError("FastAPI version is outside the owner-accepted range")
    actual_tags = [str(tag) for tag in sys_tags()]
    actual_markers = default_environment()
    actual_installed = installed_distribution_records()
    evidenced_installed = normalized_distribution_records(
        lock_data.get("installedDistributions"), "evidence installed"
    )
    resolved = normalized_distribution_records(lock_data.get("resolvedDistributions"), "evidence resolved")
    if actual_installed != evidenced_installed:
        raise RuntimeError("installed distribution inventory differs from owner evidence")
    if ({name: version for name, version in actual_installed.items() if name != "fastapi"}
            != {name: version for name, version in resolved.items() if name != "fastapi"}):
        raise RuntimeError("non-FastAPI installed distributions differ from the selected lock resolution")

    resolution_tool = lock_data.get("resolutionTool")
    selected_groups = lock_data.get("selectedDependencyGroups")
    selected_extras = lock_data.get("selectedExtras")
    if (not isinstance(resolution_tool, dict)
            or not all(isinstance(resolution_tool.get(key), str) and resolution_tool[key]
                       for key in ("name", "version", "executableIdentitySha256"))
            or not re.fullmatch(r"[A-Fa-f0-9]{64}", resolution_tool["executableIdentitySha256"])
            or not isinstance(lock_data.get("comparisonMethod"), str)
            or not lock_data["comparisonMethod"].strip()
            or not isinstance(selected_groups, list)
            or not all(isinstance(item, str) and item for item in selected_groups)
            or selected_groups != sorted(set(selected_groups))
            or not isinstance(selected_extras, list)
            or not all(isinstance(item, str) and item for item in selected_extras)
            or selected_extras != sorted(set(selected_extras))):
        raise RuntimeError("lock-resolution evidence identity is incomplete or noncanonical")
    source_file_pins_deferred = action == "OpenApiExport"
    worktree_lock_files_match = True
    if not source_file_pins_deferred:
        worktree_lock_files_match = (
            lock_data.get("uvLockSha256") == sha((WORKTREE / "backend/uv.lock").read_bytes())
            and lock_data.get("pyprojectSha256") == sha((WORKTREE / "backend/pyproject.toml").read_bytes())
        )
    if (lock_data.get("schemaVersion") != 2
            or lock_data.get("fastapiInstalledVersion") != fastapi_version
            or lock_data.get("fastapiLockVersion") != "0.162.0"
            or lock_data.get("allNonFastApiPackagesMatch") is not True
            or lock_data.get("pythonVersion") != sys.version.split()[0]
            or lock_data.get("pythonImplementation") != platform.python_implementation()
            or lock_data.get("interpreterPath") != str(interpreter_path)
            or lock_data.get("interpreterExecutableSha256") != interpreter_sha256
            or lock_data.get("platformIdentity") != platform.platform()
            or lock_data.get("compatibleTags") != actual_tags
            or lock_data.get("markerEnvironment") != actual_markers
            or not worktree_lock_files_match):
        raise RuntimeError("owner lock-resolution evidence does not match this environment and version exception")
    if resolved.get("fastapi") != "0.162.0" or actual_installed.get("fastapi") != fastapi_version:
        raise RuntimeError("FastAPI lock exception is not represented by the evidence")

    categories = {
        "SYSTEMROOT": "windows-system-root-path",
        "WINDIR": "same-windows-system-root-path",
        "PATH": "interpreter-directory-and-system32-only",
        "PATHEXT": "fixed-windows-extension-list",
        "PYTHONPATH": "worktree-backend-src-path",
        "PYTHONNOUSERSITE": "enabled",
        "PYTHONDONTWRITEBYTECODE": "enabled",
        "PYTHONUTF8": "enabled",
        "PYTHON_DOTENV_DISABLED": "enabled",
        "HOME": "run-root-home-path",
        "USERPROFILE": "same-run-root-home-path",
        "TEMP": "run-root-temp-path",
        "TMP": "same-run-root-temp-path",
        "TMPDIR": "same-run-root-temp-path",
        "AWS_EC2_METADATA_DISABLED": "enabled",
        "AWS_CONFIG_FILE": "absent-file-under-run-root",
        "AWS_SHARED_CREDENTIALS_FILE": "absent-file-under-run-root",
        "AWS_DEFAULT_REGION": "us-east-1",
        "SKETCH2LIFE_ENV": "local",
        "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED": "enabled-for-export" if export_enabled else "disabled",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "enabled-for-export" if export_enabled else "disabled",
        "SKETCH2LIFE_BE1_ARTIFACT_ROOT": "run-root-artifact-path",
        "SKETCH2LIFE_S3_ACCESS_KEY": "synthetic-value-present-omitted",
        "SKETCH2LIFE_S3_SECRET_KEY": "synthetic-value-present-omitted",
        "SKETCH2LIFE_DATABASE_URL": "loopback-sentinel-with-synthetic-auth-omitted",
        "STORYRUN_LITE_MAIN_DEMO_ENABLED": "disabled",
    }
    installed_digest = sha(json.dumps(actual_installed, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    resolved_digest = sha(json.dumps(resolved, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    tags_digest = sha(json.dumps(actual_tags, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
    markers_digest = sha(json.dumps(actual_markers, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return {
        "action": action,
        "interpreter": str(interpreter_path),
        "interpreterExecutableSha256": interpreter_sha256,
        "pythonVersion": sys.version.split()[0],
        "pythonImplementation": platform.python_implementation(),
        "pythonCacheTag": sys.implementation.cache_tag,
        "platformIdentity": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "compatibleTags": {"count": len(actual_tags), "sha256": tags_digest},
        "markerEnvironmentSha256": markers_digest,
        "fastapiVersion": fastapi_version,
        "fastapiVersionExceptionApplied": fastapi_version != "0.162.0",
        "lockIdentity": {
            "evidenceSha256": lock_evidence_sha256.upper(),
            "pyprojectSha256": lock_data["pyprojectSha256"],
            "uvLockSha256": lock_data["uvLockSha256"],
            "fastapiLockVersion": "0.162.0",
            "selectedDependencyGroups": selected_groups,
            "selectedExtras": selected_extras,
            "resolutionTool": {
                "name": resolution_tool["name"],
                "version": resolution_tool["version"],
                "executableIdentitySha256": resolution_tool["executableIdentitySha256"],
            },
            "comparisonMethod": lock_data["comparisonMethod"],
            "installedDistributionMap": {"count": len(actual_installed), "sha256": installed_digest},
            "resolvedDistributionMap": {"count": len(resolved), "sha256": resolved_digest},
            "allNonFastApiPackagesMatch": True,
            "worktreeLockFileVerification": (
                "DEFERRED_TO_EXPORTER_AFTER_SOURCE_INVENTORY_PREFLIGHT"
                if source_file_pins_deferred else "VERIFIED_BY_RUNNER"
            ),
        },
        "effectiveChildEnvironment": {
            "names": sorted(expected_names),
            "valueCategories": categories,
            "syntheticCredentialNames": ["SKETCH2LIFE_S3_ACCESS_KEY", "SKETCH2LIFE_S3_SECRET_KEY"],
            "credentialValuesRecorded": False,
            "credentialHashesRecorded": False,
            "rawEnvironmentRecorded": False,
        },
        "pathTemplates": {
            "runRoot": "<BACKEND_TMP>/<RUN_GUID>",
            "home": "<RUN_ROOT>/home",
            "temp": "<RUN_ROOT>/temp",
            "awsConfig": "<RUN_ROOT>/absent-aws-config",
            "awsCredentials": "<RUN_ROOT>/absent-aws-credentials",
            "artifactRoot": "<RUN_ROOT>/artifacts",
        },
        "runtimeIsolationProven": False,
        "databaseAccessProvenAbsent": False,
        "providerAccessProvenAbsent": False,
        "networkIsolationProven": False,
    }

def main() -> int:
    args = parse()
    root = Path(args.RunRoot).absolute()
    backend = Path(args.Backend).absolute()
    tmp = backend / "tmp"
    if backend.resolve(strict=True) != BACKEND.resolve(strict=True):
        raise RuntimeError("backend path does not match the approved worktree")
    canonical_existing_path(str(WORKTREE), "approved worktree", "directory")
    guard_chain(backend, WORKTREE)
    if tmp.is_symlink():
        raise RuntimeError("backend/tmp must not be a symlink or reparse point")
    if tmp.exists():
        if not tmp.is_dir() or reparse(tmp):
            raise RuntimeError("backend/tmp must be an ordinary directory")
    else:
        tmp.mkdir()
    if (not tmp.is_dir() or reparse(tmp)
            or tmp.parent.resolve(strict=True) != backend.resolve(strict=True)):
        raise RuntimeError("backend/tmp creation failed direct-child or reparse verification")
    guard_chain(tmp, WORKTREE)
    if root.parent.resolve(strict=True) != tmp.resolve(strict=True):
        raise RuntimeError("output root must be a direct child of backend/tmp")
    prefixes = {
        "OpenApiExport": f"openapi-mapper-d10-{args.Phase.lower()}-",
        "Compare": "openapi-mapper-d10-compare-",
        "Pytest": "pytest-openapi-d10-",
        "Check": f"{args.Tool.lower()}-openapi-d10-{args.Phase.lower()}-",
    }
    if not re.fullmatch(re.escape(prefixes[args.Action]) + r"[0-9a-f]{32}", root.name):
        raise RuntimeError("output root name is not an approved fresh-GUID form")
    if args.Action == "Compare" and not args.RootAlreadyCreated:
        raise RuntimeError("Compare requires the guarded PowerShell ComparisonRoot creation step")
    if args.Action == "Check" and args.Tool not in ("Mypy", "Ruff"):
        raise RuntimeError("Check supports only Mypy and Ruff")
    if args.RootAlreadyCreated:
        if not root.is_dir():
            raise RuntimeError("pre-created root is not a directory")
    else:
        if root.exists():
            raise FileExistsError("GUID collision; stop without writing or retry")
        root.mkdir()
    guard_chain(root, WORKTREE)
    if root.parent.resolve(strict=True) != tmp.resolve(strict=True) or reparse(root):
        raise RuntimeError("created output root failed canonical-parent/reparse verification")

    manifest_path = root / "run-manifest.json"
    manifest: dict[str, object] = {
        "action": args.Action, "phase": args.Phase, "tool": args.Tool,
        "root": str(root), "success": False, "captureComplete": False,
        "childExitCode": None, "artifacts": [], "inputs": [], "failure": None,
    }
    write_json(manifest_path, manifest, exclusive=True)
    try:
        # The launcher must validate this file before Python loads it; this check is a second boundary assertion.
        runner_file = external_file(str(Path(__file__)), "task runner")
        bootstrap = external_file(str(Path(__file__).with_name("child-bootstrap.py")), "child bootstrap")
        if args.Action == "OpenApiExport" and args.InputPaths:
            raise RuntimeError("OpenApiExport must not pre-read arbitrary input paths before inventory validation")
        lock_evidence = external_file(args.LockEvidencePath, "lock evidence")
        payload = (external_file(args.PayloadPath, f"{args.Action} payload")
                   if args.Action in ("OpenApiExport", "Compare", "Pytest") else None)
        git_executable_preflight = None
        if args.Action in ("OpenApiExport", "Compare"):
            git_executable_preflight = external_file(args.GitExecutablePath, "owner-pinned Git executable")
        source_inventory = (external_file(args.SourceInventoryPath, "source inventory")
                            if args.Action == "OpenApiExport" else None)
        generated_inputs: list[Path] = []
        if args.Action == "Compare":
            expected_names = ["runtime-pre.json", "published-pre.json", "environment.json", "source-state.json",
                              "runtime-post.json", "published-post.json", "environment.json", "source-state.json"]
            if len(args.InputPaths) != len(expected_names):
                raise RuntimeError("Compare requires the exact eight generated schema/state inputs")
            for index, (value, expected_name) in enumerate(zip(args.InputPaths, expected_names)):
                phase = "pre" if index < 4 else "post"
                generated_inputs.append(generated_artifact(
                    value, tmp, "Compare input",
                    rf"openapi-mapper-d10-{phase}-[0-9a-f]{{32}}", expected_name
                ))
        comparator_report = (generated_artifact(
            args.ComparatorReportPath, tmp, "pytest comparator report",
            r"openapi-mapper-d10-compare-[0-9a-f]{32}", "field-delta-report.json"
        ) if args.Action == "Pytest" else None)
        baseline_manifest = (generated_artifact(
            args.BaselineManifestPath, tmp, "check baseline manifest",
            rf"{args.Tool.lower()}-openapi-d10-baseline-[0-9a-f]{{32}}", "run-manifest.json"
        ) if args.Action == "Check" and args.Phase == "post" else None)
        if args.Action == "Compare":
            args.ReportPath = str(output_child(args.ReportPath, root, "comparator report"))
            args.ConsoleLogPath = str(output_child(args.ConsoleLogPath, root, "comparator console log"))
        if args.Action == "Pytest":
            args.JunitPath = str(output_child(args.JunitPath, root, "pytest JUnit output"))
            base_temp = Path(args.BaseTemp)
            if (not base_temp.is_absolute() or base_temp.parent != root or base_temp.exists()):
                raise RuntimeError("pytest basetemp must be a new direct child of the verified output root")

        python = external_file(args.PythonPath, "interpreter")
        if python != Path(sys.executable).resolve(strict=True):
            raise RuntimeError("runner and child interpreter paths differ")
        if not args.LockEvidencePath or not re.fullmatch(r"[A-Fa-f0-9]{64}", args.LockEvidenceSha256):
            raise RuntimeError("runner requires pinned lock evidence for interpreter identity")
        if digest(lock_evidence).upper() != args.LockEvidenceSha256.upper():
            raise RuntimeError("lock-resolution evidence pin mismatch")
        lock_data = json.loads(lock_evidence.read_text(encoding="utf-8"))
        interpreter_hash = digest(python).upper()
        if (lock_data.get("schemaVersion") != 2
                or lock_data.get("interpreterPath") != str(python)
                or lock_data.get("interpreterExecutableSha256") != interpreter_hash):
            raise RuntimeError("runner interpreter identity differs from lock evidence")
        manifest["interpreter"] = {"path": str(python), "executableSha256": interpreter_hash}
        git_executable = git_executable_preflight
        git_executable_hash = ""
        if args.Action in ("OpenApiExport", "Compare"):
            if (not args.GitExecutablePath
                    or not re.fullmatch(r"[A-Fa-f0-9]{64}", args.GitExecutableSha256)
                    or git_executable is None):
                raise RuntimeError("action requires an absolute owner-pinned Git executable")
            if (not git_executable.is_file() or git_executable.suffix.casefold() != ".exe"
                    or str(git_executable) != args.GitExecutablePath):
                raise RuntimeError("Git executable path is not a canonical absolute git.exe file")
            git_executable_hash = digest(git_executable).upper()
            if git_executable_hash != args.GitExecutableSha256.upper():
                raise RuntimeError("Git executable SHA-256 differs from the owner pin")
            manifest["gitExecutable" if args.Action == "OpenApiExport" else "expectedGitExecutable"] = {
                "path": str(git_executable), "sha256": git_executable_hash
            }
        elif args.GitExecutablePath or args.GitExecutableSha256:
            raise RuntimeError("Git executable inputs are only valid for OpenApiExport or Compare")
        if digest(bootstrap).upper() != BOOTSTRAP_SHA256:
            raise RuntimeError("child-bootstrap pin mismatch")
        inputs = list(generated_inputs)
        if git_executable is not None:
            inputs.append(git_executable)
        if args.Action in ("OpenApiExport", "Compare", "Pytest"):
            if payload is None:
                raise RuntimeError("action payload path is missing")
            if digest(payload).upper() != args.PayloadSha256.upper():
                raise RuntimeError("action payload pin mismatch")
        if args.Action == "Compare":
            if Path(args.ReportPath).parent != root or Path(args.ConsoleLogPath).parent != root:
                raise RuntimeError("comparator outputs must be direct children of ComparisonRoot")
        if args.Action == "Pytest":
            if Path(args.JunitPath).parent != root or root not in Path(args.BaseTemp).parents:
                raise RuntimeError("pytest outputs/basetemp must remain inside the fresh GUID root")
            if Path(args.BaseTemp).exists():
                raise FileExistsError("basetemp collision; stop without deletion or reuse")
        inputs.append(lock_evidence)
        if args.Action == "OpenApiExport":
            if (source_inventory is None or not args.SourceInventoryPath
                    or not re.fullmatch(r"[A-Fa-f0-9]{64}", args.SourceInventorySha256)):
                raise RuntimeError("OpenAPI export requires a pinned source-inventory input")
            if digest(source_inventory).upper() != args.SourceInventorySha256.upper():
                raise RuntimeError("source-inventory input pin mismatch")
            inputs.append(source_inventory)
            manifest["sourceInventory"] = {"path": str(source_inventory), "sha256": digest(source_inventory).upper()}
        if args.Action == "Pytest":
            if comparator_report is None:
                raise RuntimeError("pytest comparator report path is missing")
            if (not re.fullmatch(r"[A-Fa-f0-9]{64}", args.ComparatorReportSha256)
                    or digest(comparator_report).upper() != args.ComparatorReportSha256.upper()):
                raise RuntimeError("pytest comparator report pin is missing or mismatched")
            inputs.append(comparator_report)
        if baseline_manifest is not None:
            inputs.append(baseline_manifest)
        manifest["inputs"] = [{"path": str(p), "sha256": digest(p).upper()} for p in inputs]
        manifest["payloads"] = [{"role": "task-runner", "path": str(Path(__file__).resolve()), "sha256": digest(Path(__file__).resolve()).upper()},
                                {"role": "child-bootstrap", "path": str(bootstrap), "sha256": digest(bootstrap).upper()}]
        if payload:
            manifest["payloads"].append({"role": args.Action, "path": str(payload), "sha256": digest(payload).upper()})
        env = clean_environment(root, backend, python, args.Action)
        manifest["executionEnvironment"] = normalized_environment_identity(
            root, backend, lock_data, args.LockEvidenceSha256, env, args.Action
        )
        manifest["sourceFilePinGate"] = (
            "DEFERRED_TO_EXPORTER_AFTER_SOURCE_INVENTORY_PREFLIGHT"
            if args.Action == "OpenApiExport" else "VERIFIED_BY_RUNNER"
        )
        command = [str(python), "-I", "-X", "utf8", str(bootstrap), "-Action", args.Action,
                   "-Backend", str(backend), "-RunRoot", str(root), "-Phase", args.Phase,
                   "-Tool", args.Tool, "-BootstrapSha256", BOOTSTRAP_SHA256]
        forward = {
            "PayloadPath": str(payload) if payload else "",
            "PayloadSha256": args.PayloadSha256,
            "ReportPath": args.ReportPath,
            "ConsoleLogPath": args.ConsoleLogPath,
            "BaseTemp": args.BaseTemp,
            "JunitPath": args.JunitPath,
            "ComparatorReportPath": args.ComparatorReportPath,
            "ComparatorReportSha256": args.ComparatorReportSha256,
            "BaselineManifestPath": args.BaselineManifestPath,
            "BaselineManifestSha256": args.BaselineManifestSha256,
            "LockEvidencePath": args.LockEvidencePath,
            "LockEvidenceSha256": args.LockEvidenceSha256,
            "SourceInventoryPath": args.SourceInventoryPath,
            "SourceInventorySha256": args.SourceInventorySha256,
            "GitExecutablePath": str(git_executable) if git_executable else "",
            "GitExecutableSha256": git_executable_hash,
        }
        for name, value in forward.items():
            if value:
                command.extend([f"-{name}", value])
        for name, values in (("InputPaths", [str(p) for p in generated_inputs]),
                             ("Selections", args.Selections), ("Paths", args.Paths)):
            if values:
                command.append(f"-{name}")
                command.extend(values)
        log_name = "comparator.console.txt" if args.Action == "Compare" else (
            "pytest.console.txt" if args.Action == "Pytest" else (
                "check.console.txt" if args.Action == "Check" else "exporter.console.txt"))
        log_path = Path(args.ConsoleLogPath) if args.ConsoleLogPath else root / log_name
        expected = expected_artifacts(args, root, log_path)
        manifest["expectedArtifacts"] = [name for name, _ in expected]
        invocation_path = root / "invocation.json"
        invocation = {"action": args.Action, "phase": args.Phase, "state": "PREPARED",
                      "childExitCode": None, "exceptionType": None}
        write_json(invocation_path, invocation, exclusive=True)
        manifest["invocationState"] = "PREPARED"
        write_json(manifest_path, manifest)
        try:
            completed = subprocess.run(command, cwd=backend, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        except Exception as error:
            invocation.update({"state": "FAILED_TO_START", "exceptionType": type(error).__name__})
            manifest.update({"invocationState": "FAILED_TO_START", "failure": "CHILD_PROCESS_LAUNCH_FAILED",
                             "failureType": type(error).__name__, "childExitCode": None,
                             "runnerChildExitCode": None, "captureComplete": False, "success": False})
            try:
                write_json(invocation_path, invocation)
                log_path.write_text("CHILD_PROCESS_LAUNCH_FAILED; diagnostic details withheld.\n",
                                    encoding="utf-8", newline="\n")
                records, states_recorded = capture_artifact_states(expected)
                manifest["artifacts"] = records
                manifest["failureEvidenceState"] = (
                    "COMPLETE_FAILURE_RECORD" if states_recorded else "INCOMPLETE"
                )
            except Exception:
                manifest["failureEvidenceState"] = "INCOMPLETE"
            return 1
        invocation.update({"state": "PROCESS_RETURNED", "childExitCode": completed.returncode})
        write_json(invocation_path, invocation)
        manifest["invocationState"] = "PROCESS_RETURNED"
        log_path.write_text(completed.stdout + completed.stderr, encoding="utf-8", newline="\n")
        child_result_path = root / "child-result.json"
        child_result = json.loads(child_result_path.read_text(encoding="utf-8")) if child_result_path.is_file() else {}
        manifest.update(child_result)
        manifest["childExitCode"] = child_result.get("toolExitCode", completed.returncode)
        manifest["runnerChildExitCode"] = completed.returncode
        records, states_recorded = capture_artifact_states(expected)
        manifest["artifacts"] = records
        if args.Action == "Compare":
            entries = [f"{digest(p).upper()}  {p.name}" for p in inputs]
            if payload:
                entries.append(f"{digest(payload).upper()}  {payload.name}")
            for _, p in expected:
                if p.is_file() and p.name != "sha256.txt":
                    entries.append(f"{digest(p).upper()}  {p.name}")
            with (root / "sha256.txt").open("a", encoding="ascii", newline="\n") as stream:
                stream.write("Runner-recorded hashes after comparator exit\n" + "\n".join(entries) + "\n")
        all_present = all(r["state"] == "PRESENT" for r in records)
        manifest["captureComplete"] = completed.returncode == 0 and all_present and child_result.get("captureComplete", False)
        manifest["success"] = bool(child_result.get("success", False) and manifest["captureComplete"])
        manifest["failureEvidenceState"] = "COMPLETE" if states_recorded else "INCOMPLETE"
        if not manifest["success"]:
            manifest["failure"] = child_result.get("failure") or "action success conditions failed"
    except Exception as error:
        manifest["failure"] = "RUNNER_PREFLIGHT_OR_FINALIZATION_FAILURE"
        manifest["failureType"] = type(error).__name__
        manifest["success"] = False
        manifest["captureComplete"] = False
        if "failureEvidenceState" not in manifest:
            manifest["failureEvidenceState"] = "INCOMPLETE"
    finally:
        try:
            write_json(manifest_path, manifest)
        except Exception:
            try:
                (root / "failure-evidence.status").write_text("EVIDENCE_INCOMPLETE\n", encoding="ascii")
            except Exception:
                pass
            return 1
    return 0 if manifest.get("success") else 1


def clean_environment(root: Path, backend: Path, python: Path, action: str) -> dict[str, str]:
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    home, temp = root / "home", root / "temp"
    home.mkdir(exist_ok=True)
    temp.mkdir(exist_ok=True)
    config, credentials = root / "absent-aws-config", root / "absent-aws-credentials"
    if config.exists() or credentials.exists():
        raise RuntimeError("AWS config/credentials sentinel path unexpectedly exists")
    database_user, database_password = secrets.token_hex(12), secrets.token_hex(24)
    return {
        "SystemRoot": system_root, "WINDIR": system_root,
        "PATH": os.pathsep.join((str(python.parent), str(Path(system_root) / "System32"))),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD", "PYTHONPATH": str(backend / "src"),
        "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
        "PYTHON_DOTENV_DISABLED": "1", "HOME": str(home), "USERPROFILE": str(home),
        "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp),
        "AWS_EC2_METADATA_DISABLED": "true", "AWS_CONFIG_FILE": str(config),
        "AWS_SHARED_CREDENTIALS_FILE": str(credentials), "AWS_DEFAULT_REGION": "us-east-1",
        "SKETCH2LIFE_ENV": "local",
        "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED": "true" if action == "OpenApiExport" else "false",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "true" if action == "OpenApiExport" else "false",
        "SKETCH2LIFE_BE1_ARTIFACT_ROOT": str(root / "artifacts"),
        "SKETCH2LIFE_S3_ACCESS_KEY": "synthetic-" + secrets.token_hex(24),
        "SKETCH2LIFE_S3_SECRET_KEY": "synthetic-" + secrets.token_urlsafe(32),
        "SKETCH2LIFE_DATABASE_URL": f"postgresql+psycopg://{database_user}:{database_password}@127.0.0.1:1/mapper_sentinel",
        "STORYRUN_LITE_MAIN_DEMO_ENABLED": "0",
    }


def expected_artifacts(args: argparse.Namespace, root: Path, log: Path) -> list[tuple[str, Path]]:
    if args.Action == "OpenApiExport":
        return [(f"runtime-{args.Phase}.json", root / f"runtime-{args.Phase}.json"),
                (f"published-{args.Phase}.json", root / f"published-{args.Phase}.json"),
                ("environment.json", root / "environment.json"),
                ("source-state.json", root / "source-state.json"),
                (log.name, log), ("invocation.json", root / "invocation.json")]
    if args.Action == "Compare":
        return [("field-delta-report.json", Path(args.ReportPath)), (log.name, log),
                ("invocation.json", root / "invocation.json")]
    if args.Action == "Pytest":
        return [("pytest.junit.xml", Path(args.JunitPath)),
                ("environment.json", root / "environment.json"),
                ("field-delta-report.json", Path(args.ComparatorReportPath)), (log.name, log),
                ("invocation.json", root / "invocation.json")]
    return [("check-result.json", root / "check-result.json"), ("check-raw-output.txt", root / "check-raw-output.txt"), (log.name, log),
            ("invocation.json", root / "invocation.json")]


def capture_artifact_states(expected: list[tuple[str, Path]]) -> tuple[list[dict[str, object]], bool]:
    records: list[dict[str, object]] = []
    complete = True
    for name, path in expected:
        try:
            info = path.lstat()
            if reparse(path) or not stat.S_ISREG(info.st_mode):
                records.append({"name": name, "state": "UNSAFE"})
            else:
                records.append({"name": name, "state": "PRESENT", "bytes": info.st_size,
                                "sha256": digest(path).upper()})
        except FileNotFoundError:
            records.append({"name": name, "state": "MISSING"})
        except OSError:
            records.append({"name": name, "state": "UNREADABLE"})
            complete = False
    return records, complete
if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(1)
```
<!-- payload-end:task-runner.py -->

### `child-bootstrap.py`

<!-- payload-begin:child-bootstrap.py -->
```python
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import Counter
import sys
import re
from pathlib import Path
from urllib.parse import urlsplit

from packaging.markers import default_environment
from packaging.tags import sys_tags


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-Action", required=True)
    parser.add_argument("-Backend", required=True)
    parser.add_argument("-RunRoot", required=True)
    parser.add_argument("-Phase", default="")
    parser.add_argument("-Tool", default="")
    parser.add_argument("-BootstrapSha256", required=True)
    parser.add_argument("-PayloadPath", default="")
    parser.add_argument("-PayloadSha256", default="")
    parser.add_argument("-InputPaths", nargs="*", default=[])
    parser.add_argument("-ReportPath", default="")
    parser.add_argument("-ConsoleLogPath", default="")
    parser.add_argument("-BaseTemp", default="")
    parser.add_argument("-JunitPath", default="")
    parser.add_argument("-ComparatorReportPath", default="")
    parser.add_argument("-ComparatorReportSha256", default="")
    parser.add_argument("-Selections", nargs="*", default=[])
    parser.add_argument("-Paths", nargs="*", default=[])
    parser.add_argument("-BaselineManifestPath", default="")
    parser.add_argument("-BaselineManifestSha256", default="")
    parser.add_argument("-LockEvidencePath", default="")
    parser.add_argument("-LockEvidenceSha256", default="")
    parser.add_argument("-SourceInventoryPath", default="")
    parser.add_argument("-SourceInventorySha256", default="")
    parser.add_argument("-GitExecutablePath", default="")
    parser.add_argument("-GitExecutableSha256", default="")
    return parser.parse_args()


def main() -> int:
    args = parse()
    backend, root = Path(args.Backend).resolve(strict=True), Path(args.RunRoot).resolve(strict=True)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(backend / "src"))
    result: dict[str, object] = {"captureComplete": False, "success": False}
    rc = 1
    try:
        bootstrap = Path(__file__).resolve(strict=True)
        if sha256(bootstrap) != args.BootstrapSha256.upper():
            raise RuntimeError("bootstrap hash mismatch")
        if args.Action == "Check":
            result, rc = run_check(args, root, backend)
        else:
            payload = Path(args.PayloadPath).resolve(strict=True)
            if sha256(payload) != args.PayloadSha256.upper():
                raise RuntimeError("payload hash mismatch")
            argv = [str(payload)]
            if args.Action == "OpenApiExport":
                inventory_path = Path(args.SourceInventoryPath).resolve(strict=True)
                if sha256(inventory_path) != args.SourceInventorySha256.upper():
                    raise RuntimeError("source-inventory hash mismatch")
                git_executable = Path(args.GitExecutablePath)
                if not git_executable.is_absolute():
                    raise RuntimeError("Git executable path must be absolute")
                git_executable = git_executable.resolve(strict=True)
                if (not git_executable.is_file() or git_executable.suffix.casefold() != ".exe"
                        or str(git_executable) != args.GitExecutablePath
                        or not re.fullmatch(r"[A-Fa-f0-9]{64}", args.GitExecutableSha256)
                        or sha256(git_executable) != args.GitExecutableSha256.upper()):
                    raise RuntimeError("Git executable path or SHA-256 differs from the owner pin")
                argv += ["-Backend", str(backend), "-RunRoot", str(root), "-Phase", args.Phase,
                         "-LockEvidencePath", args.LockEvidencePath,
                         "-LockEvidenceSha256", args.LockEvidenceSha256,
                         "-SourceInventoryPath", str(inventory_path),
                         "-SourceInventorySha256", args.SourceInventorySha256,
                         "-GitExecutablePath", str(git_executable),
                         "-GitExecutableSha256", args.GitExecutableSha256]
            elif args.Action == "Compare":
                argv += ["-Backend", str(backend), "-RunRoot", str(root), "-InputPaths", *args.InputPaths,
                         "-ReportPath", args.ReportPath,
                         "-GitExecutablePath", args.GitExecutablePath,
                         "-GitExecutableSha256", args.GitExecutableSha256]
            elif args.Action == "Pytest":
                argv += ["-Backend", str(backend), "-RunRoot", str(root), "-BaseTemp", args.BaseTemp,
                         "-JunitPath", args.JunitPath, "-ComparatorReportPath", args.ComparatorReportPath, "-ComparatorReportSha256", args.ComparatorReportSha256,
                         "-LockEvidencePath", args.LockEvidencePath,
                         "-LockEvidenceSha256", args.LockEvidenceSha256,
                         "-Selections", *args.Selections]
            else:
                raise RuntimeError("unsupported action")
            sys.argv = argv
            try:
                runpy.run_path(str(payload), run_name="__main__")
                rc = 0
            except SystemExit as exc:
                rc = int(exc.code or 0)
            result["captureComplete"] = rc == 0
            result["success"] = rc == 0
            if args.Action == "Compare" and Path(args.ReportPath).is_file():
                report = json.loads(Path(args.ReportPath).read_text(encoding="utf-8"))
                result["comparison"] = {"passed": report.get("passed") is True}
            if args.Action == "Pytest":
                report_bytes = Path(args.ComparatorReportPath).read_bytes()
                if hashlib.sha256(report_bytes).hexdigest().upper() != args.ComparatorReportSha256.upper():
                    raise RuntimeError("comparator report hash mismatch")
                report = json.loads(report_bytes.decode("utf-8"))
                result["comparatorPassed"] = report.get("passed") is True
                result["success"] = rc == 0 and result["comparatorPassed"] is True
    except Exception as error:
        result["failure"] = "CHILD_BOOTSTRAP_FAILURE"
        result["failureType"] = type(error).__name__
        rc = 1
    (root / "child-result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return rc


def run_check(args: argparse.Namespace, root: Path, backend: Path) -> tuple[dict[str, object], int]:
    import importlib.metadata
    import re
    import subprocess

    if args.Tool == "Mypy":
        from mypy import api as mypy_api
        output, error, tool_rc = mypy_api.run(["--show-error-codes", "--no-color-output",
                                                "--cache-dir", str(root / "mypy-cache"), *args.Paths])
        text = output + error
        version = importlib.metadata.version("mypy")
        signatures, unparsed = [], 0
        pattern = re.compile(r"^(.*?):(?:(\d+):)?(?:(\d+):)?\s*(error|warning|note):\s*(.*?)(?:\s+\[([a-z0-9-]+)\])?$")
        for line in text.splitlines():
            match = pattern.match(line.strip())
            if match:
                path = Path(match.group(1))
                relative = path.as_posix() if not path.is_absolute() else Path(__import__("os").path.relpath(path, backend)).as_posix()
                if relative == ".." or relative.startswith("../"):
                    unparsed += 1
                    continue
                signatures.append({"path": relative, "severity": match.group(4), "code": match.group(6) or "", "message": " ".join(match.group(5).split())})
            elif line.strip() and not re.match(r"^(Found \d+ errors? in|Success: no issues found)", line.strip()):
                unparsed += 1
    elif args.Tool == "Ruff":
        command = [sys.executable, "-m", "ruff", "check", "--no-cache", "--output-format", "json", *args.Paths]
        process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        text, tool_rc = process.stdout, process.returncode
        version = importlib.metadata.version("ruff")
        try:
            parsed = json.loads(text or "[]")
            signatures = [{"path": (Path(__import__("os").path.relpath(item["filename"], backend)).as_posix()
                                    if Path(item["filename"]).is_absolute() else Path(item["filename"]).as_posix()), "severity": "error",
                           "code": item["code"] or "", "message": " ".join(item["message"].split())}
                          for item in parsed]
            unparsed = 0 if not process.stderr.strip() else len(process.stderr.splitlines())
        except Exception:
            signatures, unparsed = [], 1
    else:
        raise RuntimeError("check tool must be Mypy or Ruff")
    raw_output = text if args.Tool == "Mypy" else text + ("\n--- stderr ---\n" + process.stderr if process.stderr else "")
    (root / "check-raw-output.txt").write_text(raw_output, encoding="utf-8", newline="\n")
    signatures = sorted(signatures, key=lambda item: (item["path"], item["code"], item["message"]))
    blocked = args.Tool == "Mypy" and (tool_rc >= 2 or "errors prevented further checking" in text)
    result: dict[str, object] = {"tool": args.Tool, "phase": args.Phase, "toolVersion": version,
        "toolExitCode": tool_rc, "diagnostics": {"signatures": signatures, "unparsedCount": unparsed},
        "toolClean": tool_rc == 0 and not signatures, "captureComplete": unparsed == 0 and not blocked,
        "success": unparsed == 0 and not blocked}
    if args.Tool == "Ruff" and args.Phase == "baseline":
        result["newPathDiagnostics"] = {"state": "ABSENT_NOT_SELECTED", "count": None}
    if args.Phase == "post":
        baseline_path = Path(args.BaselineManifestPath).resolve(strict=True)
        if sha256(baseline_path) != args.BaselineManifestSha256.upper():
            raise RuntimeError("baseline manifest hash mismatch")
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        if baseline.get("tool") != args.Tool or baseline.get("toolVersion") != version or baseline.get("phase") != "baseline":
            raise RuntimeError("baseline tool identity or phase mismatch")
        prior = Counter((x["path"], x["severity"], x["code"], x["message"]) for x in baseline["diagnostics"]["signatures"])
        current = Counter((x["path"], x["severity"], x["code"], x["message"]) for x in signatures)
        added = sorted((current - prior).elements())
        new_path = "tests/contract/test_openapi_schema_catalog_mapping.py"
        new_count = sum(1 for x in signatures if x["path"].replace("\\", "/").endswith(new_path)) if args.Tool == "Ruff" else 0
        shared_added = [x for x in added if not x[0].replace("\\", "/").endswith(new_path)]
        result["comparison"] = {"passed": unparsed == 0 and not shared_added and new_count == 0,
            "baselineManifestSha256": args.BaselineManifestSha256.upper(),
            "addedSignatures": added, "sharedPathAddedSignatures": shared_added, "unparsedCount": unparsed}
        result["newPathDiagnostics"] = {"state": "CHECKED" if args.Tool == "Ruff" else "NOT_APPLICABLE", "count": new_count}
        result["success"] = result["comparison"]["passed"] is True
    (root / "check-result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result, 0 if result["success"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(1)
```
<!-- payload-end:child-bootstrap.py -->

### `openapi-export.py`

<!-- payload-begin:openapi-export.py -->
```python
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import stat
import subprocess
import sys
import re
from pathlib import Path
from urllib.parse import urlsplit

from packaging.markers import default_environment
from packaging.tags import sys_tags

WORKTREE = Path(r"D:\GitHub\Sketch2Life\.worktrees\m2-s2")
EXPECTED_BRANCH = "feature/feat063-m2-s2"
EXPECTED_HEAD = "5de30674bc826591ad4b3cc00fca53c7597ead51"
N_PATH = "backend/tests/contract/test_openapi_schema_catalog_mapping.py"
E_E_N_R = {
    "backend/src/sketch2life/interfaces/http/app.py": "E",
    "backend/tests/contract/test_openapi_contract_catalog.py": "E",
    "backend/tests/contract/test_openapi_schema_catalog_mapping.py": "N",
    "backend/tests/contract/test_app_composition.py": "R",
}
NO_READ_PARTS = (".env", "secret", "credential", "service-account", "firebase-adminsdk",
                 "real-data", "child-media", "seed-account", "seed-user")
PINNED_INPUTS = {
    "backend/pyproject.toml": "35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2",
    "backend/src/sketch2life/infrastructure/config/settings.py": "B430FA3036B1621CE0EB6283C94642E57AFF367FB8C45F7819E556D7D4180E65",
    "backend/src/sketch2life/infrastructure/storage/s3_compatible.py": "43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B",
    "backend/src/sketch2life/interfaces/http/app.py": "E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031",
    "backend/src/sketch2life/interfaces/http/be1_runtime.py": "62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85",
    "backend/src/sketch2life/interfaces/http/openapi_contract.py": "175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE",
    "backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py": "E16DE02140E7977A014F32D9CF131DAC8FC63EA622CEDD26B702958D7B92BB09",
    "backend/src/sketch2life/interfaces/http/openapi_srs_v22.py": "29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3",
    "backend/src/sketch2life/interfaces/http/router_composition.py": "2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463",
    "backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py": "7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF",
    "backend/tests/contract/test_app_composition.py": "1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52",
    "backend/tests/contract/test_openapi_contract_catalog.py": "BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198",
    N_PATH: None,
    "backend/uv.lock": "830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def git(root: Path, executable: Path, executable_sha256: str, *args: str) -> bytes:
    if sha(executable.read_bytes()) != executable_sha256.upper():
        raise RuntimeError("owner-pinned Git executable changed before invocation")
    return subprocess.run([str(executable), *args], cwd=root, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def safe_repo_relative_path(value: object) -> bool:
    if (not isinstance(value, str) or not value or not value.isprintable()
            or ":" in value or "\\" in value or value.startswith("/")):
        return False
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return False
    normalized = Path(value)
    return not normalized.is_absolute() and normalized.as_posix() == value


def no_read(path: str) -> bool:
    parts = [part.lower() for part in path.split("/")]
    name = parts[-1] if parts else ""
    return (any(part == token or token in part or part.startswith(".env")
                for part in parts for token in NO_READ_PARTS)
            or name.endswith((".pem", ".key", ".p12", ".pfx")))



def normalized_distribution_records(records: object, label: str) -> dict[str, str]:
    if not isinstance(records, list):
        raise RuntimeError(f"{label} distribution records are missing")
    result: dict[str, str] = {}
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not isinstance(row.get("version"), str):
            raise RuntimeError(f"{label} distribution record is malformed")
        name = re.sub(r"[-_.]+", "-", row["name"]).lower()
        if not name or name in result:
            raise RuntimeError(f"{label} distribution names are empty or duplicated")
        result[name] = row["version"]
    return result


def installed_distribution_records() -> dict[str, str]:
    records = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if not isinstance(name, str) or not name.strip():
            raise RuntimeError("installed distribution has no normalized name")
        records.append({"name": name, "version": distribution.version})
    return normalized_distribution_records(records, "installed")


def normalized_environment_identity(
    root: Path,
    backend: Path,
    state: dict[str, object],
    lock_data: dict[str, object],
    lock_evidence_sha256: str,
    fastapi_version: str,
) -> dict[str, object]:
    environment = os.environ
    interpreter_path = Path(sys.executable).resolve(strict=True)
    interpreter_sha256 = sha(interpreter_path.read_bytes())
    expected_names = {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "PYTHONPATH",
        "PYTHONNOUSERSITE", "PYTHONDONTWRITEBYTECODE", "PYTHONUTF8",
        "PYTHON_DOTENV_DISABLED", "HOME", "USERPROFILE", "TEMP", "TMP", "TMPDIR",
        "AWS_EC2_METADATA_DISABLED", "AWS_CONFIG_FILE", "AWS_SHARED_CREDENTIALS_FILE",
        "AWS_DEFAULT_REGION", "SKETCH2LIFE_ENV", "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "SKETCH2LIFE_BE1_ARTIFACT_ROOT",
        "SKETCH2LIFE_S3_ACCESS_KEY", "SKETCH2LIFE_S3_SECRET_KEY",
        "SKETCH2LIFE_DATABASE_URL", "STORYRUN_LITE_MAIN_DEMO_ENABLED",
    }
    if set(environment) != expected_names:
        raise RuntimeError("effective child environment variable-name allowlist mismatch")
    system_root = environment.get("SystemRoot", "")
    expected_values = {
        "WINDIR": system_root,
        "PATH": os.pathsep.join((str(Path(sys.executable).parent), str(Path(system_root) / "System32"))),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PYTHONPATH": str(backend / "src"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "HOME": str(root / "home"),
        "USERPROFILE": str(root / "home"),
        "TEMP": str(root / "temp"),
        "TMP": str(root / "temp"),
        "TMPDIR": str(root / "temp"),
        "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_CONFIG_FILE": str(root / "absent-aws-config"),
        "AWS_SHARED_CREDENTIALS_FILE": str(root / "absent-aws-credentials"),
        "AWS_DEFAULT_REGION": "us-east-1",
        "SKETCH2LIFE_ENV": "local",
        "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED": "true",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "true",
        "SKETCH2LIFE_BE1_ARTIFACT_ROOT": str(root / "artifacts"),
        "STORYRUN_LITE_MAIN_DEMO_ENABLED": "0",
    }
    if any(environment.get(name) != value for name, value in expected_values.items()):
        raise RuntimeError("effective child environment category or path mismatch")
    if (not environment["SKETCH2LIFE_S3_ACCESS_KEY"].startswith("synthetic-")
            or not environment["SKETCH2LIFE_S3_SECRET_KEY"].startswith("synthetic-")):
        raise RuntimeError("S3 credentials are not synthetic-only")
    database = urlsplit(environment["SKETCH2LIFE_DATABASE_URL"])
    if (database.scheme != "postgresql+psycopg" or database.hostname != "127.0.0.1"
            or database.port != 1 or database.path != "/mapper_sentinel"
            or not database.username or not database.password):
        raise RuntimeError("database sentinel configuration mismatch")
    if (Path(environment["AWS_CONFIG_FILE"]).exists()
            or Path(environment["AWS_SHARED_CREDENTIALS_FILE"]).exists()):
        raise RuntimeError("AWS credential sentinel path unexpectedly exists")

    fastapi_tuple = tuple(int(part) for part in fastapi_version.split(".")[:3])
    if not ((0, 162, 0) <= fastapi_tuple <= (0, 162, 7)):
        raise RuntimeError("FastAPI version is outside the owner-accepted range")
    actual_tags = [str(tag) for tag in sys_tags()]
    actual_markers = default_environment()
    actual_installed = installed_distribution_records()
    evidenced_installed = normalized_distribution_records(lock_data.get("installedDistributions"), "evidence installed")
    resolved = normalized_distribution_records(lock_data.get("resolvedDistributions"), "evidence resolved")
    if actual_installed != evidenced_installed:
        raise RuntimeError("installed distribution inventory differs from owner evidence")
    if ({name: version for name, version in actual_installed.items() if name != "fastapi"}
            != {name: version for name, version in resolved.items() if name != "fastapi"}):
        raise RuntimeError("non-FastAPI installed distributions differ from the selected lock resolution")
    resolution_tool = lock_data.get("resolutionTool")
    selected_groups = lock_data.get("selectedDependencyGroups")
    selected_extras = lock_data.get("selectedExtras")
    if (not isinstance(resolution_tool, dict)
            or not all(isinstance(resolution_tool.get(key), str) and resolution_tool[key]
                       for key in ("name", "version", "executableIdentitySha256"))
            or not isinstance(lock_data.get("comparisonMethod"), str)
            or not lock_data["comparisonMethod"]
            or not isinstance(selected_groups, list)
            or not all(isinstance(item, str) for item in selected_groups)
            or not isinstance(selected_extras, list)
            or not all(isinstance(item, str) for item in selected_extras)):
        raise RuntimeError("lock-resolution evidence identity is incomplete")
    if (lock_data.get("schemaVersion") != 2
            or lock_data.get("fastapiInstalledVersion") != fastapi_version
            or lock_data.get("fastapiLockVersion") != "0.162.0"
            or lock_data.get("allNonFastApiPackagesMatch") is not True
            or lock_data.get("pythonVersion") != sys.version.split()[0]
            or lock_data.get("pythonImplementation") != platform.python_implementation()
            or lock_data.get("interpreterPath") != str(interpreter_path)
            or lock_data.get("interpreterExecutableSha256") != interpreter_sha256
            or lock_data.get("platformIdentity") != platform.platform()
            or lock_data.get("compatibleTags") != actual_tags
            or lock_data.get("markerEnvironment") != actual_markers
            or lock_data.get("uvLockSha256") != sha((WORKTREE / "backend/uv.lock").read_bytes())
            or lock_data.get("pyprojectSha256") != sha((WORKTREE / "backend/pyproject.toml").read_bytes())):
        raise RuntimeError("owner lock-resolution evidence does not match this environment and version exception")
    if resolved.get("fastapi") != "0.162.0" or actual_installed.get("fastapi") != fastapi_version:
        raise RuntimeError("FastAPI lock exception is not represented by the evidence")

    categories = {
        "SYSTEMROOT": "windows-system-root-path",
        "WINDIR": "same-windows-system-root-path",
        "PATH": "interpreter-directory-and-system32-only",
        "PATHEXT": "fixed-windows-extension-list",
        "PYTHONPATH": "worktree-backend-src-path",
        "PYTHONNOUSERSITE": "enabled",
        "PYTHONDONTWRITEBYTECODE": "enabled",
        "PYTHONUTF8": "enabled",
        "PYTHON_DOTENV_DISABLED": "enabled",
        "HOME": "run-root-home-path",
        "USERPROFILE": "same-run-root-home-path",
        "TEMP": "run-root-temp-path",
        "TMP": "same-run-root-temp-path",
        "TMPDIR": "same-run-root-temp-path",
        "AWS_EC2_METADATA_DISABLED": "enabled",
        "AWS_CONFIG_FILE": "absent-file-under-run-root",
        "AWS_SHARED_CREDENTIALS_FILE": "absent-file-under-run-root",
        "AWS_DEFAULT_REGION": "us-east-1",
        "SKETCH2LIFE_ENV": "local",
        "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED": "enabled-for-export",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "enabled-for-export",
        "SKETCH2LIFE_BE1_ARTIFACT_ROOT": "run-root-artifact-path",
        "SKETCH2LIFE_S3_ACCESS_KEY": "synthetic-value-present-omitted",
        "SKETCH2LIFE_S3_SECRET_KEY": "synthetic-value-present-omitted",
        "SKETCH2LIFE_DATABASE_URL": "loopback-sentinel-with-synthetic-auth-omitted",
        "STORYRUN_LITE_MAIN_DEMO_ENABLED": "disabled",
    }
    return {
        "interpreter": str(interpreter_path),
        "interpreterExecutableSha256": interpreter_sha256,
        "pythonVersion": sys.version.split()[0],
        "pythonImplementation": platform.python_implementation(),
        "pythonCacheTag": sys.implementation.cache_tag,
        "compatibleTags": actual_tags,
        "markerEnvironment": actual_markers,
        "platformIdentity": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "fastapiVersion": fastapi_version,
        "lockIdentity": {
            "evidenceSha256": lock_evidence_sha256.upper(),
            "interpreterPath": str(interpreter_path),
            "interpreterExecutableSha256": interpreter_sha256,
            "pyprojectSha256": lock_data["pyprojectSha256"],
            "uvLockSha256": lock_data["uvLockSha256"],
            "fastapiLockVersion": lock_data["fastapiLockVersion"],
            "selectedDependencyGroups": sorted(selected_groups),
            "selectedExtras": sorted(selected_extras),
            "resolutionTool": resolution_tool,
            "comparisonMethod": lock_data["comparisonMethod"],
            "installedDistributionCount": len(actual_installed),
            "resolvedDistributionCount": len(resolved),
            "allNonFastApiPackagesMatch": True,
        },
        "sourceIdentity": {"worktree": str(WORKTREE.resolve(strict=True)),
                           "branch": state["branch"], "head": state["head"]},
        "effectiveChildEnvironment": {
            "names": sorted(expected_names),
            "valueCategories": categories,
            "syntheticCredentialNames": ["SKETCH2LIFE_S3_ACCESS_KEY", "SKETCH2LIFE_S3_SECRET_KEY"],
            "credentialValuesRecorded": False,
            "credentialHashesRecorded": False,
            "rawEnvironmentRecorded": False,
        },
        "pathTemplates": {
            "runRoot": "<BACKEND_TMP>/<RUN_GUID>",
            "home": "<RUN_ROOT>/home",
            "temp": "<RUN_ROOT>/temp",
            "awsConfig": "<RUN_ROOT>/absent-aws-config",
            "awsCredentials": "<RUN_ROOT>/absent-aws-credentials",
            "artifactRoot": "<RUN_ROOT>/artifacts",
        },
        "profile": "combined-local",
        "storyRunLiteDemo": False,
        "dotenvDisabled": True,
        "awsMetadataDisabled": True,
        "awsConfigPathsAbsent": True,
        "dbSentinelConfigured": True,
        "runtimeIsolationProven": False,
        "databaseAccessProvenAbsent": False,
        "providerAccessProvenAbsent": False,
        "networkIsolationProven": False,
    }

def _file_kind(root: Path, relative: str, status: str, allow_absent: bool = False) -> str:
    candidate = Path(relative)
    if (not relative or candidate.is_absolute() or ".." in candidate.parts
            or "\\" in relative or no_read(relative)):
        return "EXCLUDED_NO_READ" if no_read(relative) else "UNCLASSIFIABLE"
    try:
        current = root
        for part in candidate.parts:
            current = current / part
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
                return "UNREADABLE"
        info = (root / candidate).lstat()
        if stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            return "UNREADABLE"
        if not stat.S_ISREG(info.st_mode):
            return "UNCLASSIFIABLE"
        return "PRESENT"
    except FileNotFoundError:
        return "ABSENT" if allow_absent or "D" in status else "UNCLASSIFIABLE"
    except OSError:
        return "UNREADABLE"


def file_state(root: Path, relative: str, status: str, allow_absent: bool = False) -> dict[str, object]:
    kind = _file_kind(root, relative, status, allow_absent)
    if kind != "PRESENT":
        return {"path": relative, "status": status, "state": kind, "bytes": None, "sha256": None}
    path = root / relative
    try:
        data = path.read_bytes()
        return {"path": relative, "status": status, "state": "PRESENT", "bytes": len(data), "sha256": sha(data)}
    except FileNotFoundError:
        return {"path": relative, "status": status,
                "state": "ABSENT" if allow_absent or "D" in status else "UNCLASSIFIABLE",
                "bytes": None, "sha256": None}
    except OSError:
        return {"path": relative, "status": status, "state": "UNREADABLE", "bytes": None, "sha256": None}


def capture_pinned_input_states(root: Path, phase: str, actual_status: dict[str, str],
                                states: dict[str, dict[str, object]]) -> tuple[dict[str, dict[str, object]], list[str]]:
    captured: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for path, expected_sha256 in sorted(PINNED_INPUTS.items()):
        if not safe_repo_relative_path(path) or no_read(path):
            errors.append("fixed pinned-input manifest contains an unsafe or disallowed path")
            continue
        status = actual_status.get(path, "  ")
        row = states.get(path) or file_state(
            root, path, status, allow_absent=path == N_PATH and phase == "pre"
        )
        state, size, actual_sha256 = row.get("state"), row.get("bytes"), row.get("sha256")
        if expected_sha256 is None:
            expected_state = "ABSENT" if phase == "pre" else "PRESENT"
            if state != expected_state:
                errors.append("pinned N-path state differs from its phase requirement")
            if phase == "pre" and (size is not None or actual_sha256 is not None):
                errors.append("pinned N-path pre-state must have null size and hash")
            if phase == "post" and (
                    isinstance(size, bool) or not isinstance(size, int) or size < 0
                    or not isinstance(actual_sha256, str)
                    or re.fullmatch(r"[A-F0-9]{64}", actual_sha256) is None):
                errors.append("pinned N-path post-state requires captured bytes and SHA-256")
        else:
            if (state != "PRESENT" or isinstance(size, bool) or not isinstance(size, int) or size < 0
                    or not isinstance(actual_sha256, str)
                    or re.fullmatch(r"[A-F0-9]{64}", actual_sha256) is None):
                errors.append("pinned source/test input is missing, unreadable, or malformed")
            elif not (phase == "post" and E_E_N_R.get(path) == "E") and actual_sha256 != expected_sha256:
                errors.append("pinned source/test input SHA-256 differs from its approved pre-state")
        captured[path] = {"status": row.get("status"), "state": state, "bytes": size, "sha256": actual_sha256}
    return captured, errors


def _inventory_rows(value: object, label: str) -> dict[str, dict[str, str]]:
    if not isinstance(value, list):
        raise RuntimeError(f"{label} source-inventory rows are missing")
    result: dict[str, dict[str, str]] = {}
    ordered: list[str] = []
    for row in value:
        if not isinstance(row, dict) or set(row) != {"path", "status", "disposition"}:
            raise RuntimeError(f"{label} source-inventory row is malformed")
        path, status, disposition = row.get("path"), row.get("status"), row.get("disposition")
        if (not safe_repo_relative_path(path) or no_read(path)
                or not isinstance(status, str) or len(status) != 2
                or any(char not in " MADUT?!" for char in status) or status == "  "
                or "R" in status or "C" in status
                or disposition not in ("HASH", "EXCLUDED_NO_READ") or path in result):
            raise RuntimeError(f"{label} source-inventory path/status/disposition is invalid")
        result[path] = {"status": status, "disposition": disposition}
        ordered.append(path)
    if ordered != sorted(ordered):
        raise RuntimeError(f"{label} source-inventory rows are not lexicographically sorted")
    return result


def _inventory_transitions(value: object) -> dict[str, dict[str, str]]:
    if not isinstance(value, list):
        raise RuntimeError("source-inventory E/E/N/R transitions are missing")
    result: dict[str, dict[str, str]] = {}
    ordered: list[str] = []
    for row in value:
        if not isinstance(row, dict) or set(row) != {"path", "mode", "preStatus", "postStatus"}:
            raise RuntimeError("source-inventory E/E/N/R transition is malformed")
        path, mode = row.get("path"), row.get("mode")
        pre_status, post_status = row.get("preStatus"), row.get("postStatus")
        if (not safe_repo_relative_path(path) or no_read(path)
                or path not in E_E_N_R or mode != E_E_N_R.get(path)
                or not isinstance(pre_status, str) or len(pre_status) != 2
                or not isinstance(post_status, str) or len(post_status) != 2
                or any(char not in " MADUT?!" for char in pre_status + post_status)
                or "R" in pre_status + post_status or "C" in pre_status + post_status or path in result):
            raise RuntimeError("source-inventory E/E/N/R transition is invalid")
        if mode == "N" and (pre_status != "  " or post_status != "??"):
            raise RuntimeError("N transition requires blank pre-status and ?? post-status")
        result[path] = {"mode": mode, "preStatus": pre_status, "postStatus": post_status}
        ordered.append(path)
    if set(result) != set(E_E_N_R) or ordered != sorted(ordered):
        raise RuntimeError("source-inventory must list the exact sorted E/E/N/R paths")
    return result


def validate_inventory_path_strings(inventory: dict[str, object]) -> None:
    for label in ("preChangedPaths", "postChangedPaths"):
        rows = inventory.get(label)
        if not isinstance(rows, list):
            raise RuntimeError("source-inventory path list is missing or malformed")
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError("source-inventory path row is malformed")
            path = row.get("path")
            if not safe_repo_relative_path(path) or no_read(path):
                raise RuntimeError("source-inventory contains an unsafe or disallowed path")
    transitions = inventory.get("allowlistTransitions")
    if not isinstance(transitions, list):
        raise RuntimeError("source-inventory transition list is missing or malformed")
    for row in transitions:
        if not isinstance(row, dict):
            raise RuntimeError("source-inventory transition row is malformed")
        path = row.get("path")
        if not safe_repo_relative_path(path) or no_read(path):
            raise RuntimeError("source-inventory contains an unsafe or disallowed transition path")


def source_state(root: Path, phase: str, inventory: dict[str, object], inventory_sha256: str,
                 git_executable: Path, git_executable_sha256: str) -> dict[str, object]:
    validate_inventory_path_strings(inventory)
    canonical = root.resolve(strict=True)
    branch = git(canonical, git_executable, git_executable_sha256, "branch", "--show-current").decode().strip()
    head = git(canonical, git_executable, git_executable_sha256, "rev-parse", "HEAD").decode().strip()
    base: dict[str, object] = {
        "version": 4, "worktree": str(canonical), "branch": branch, "head": head,
        "gitExecutable": {"path": str(git_executable), "sha256": git_executable_sha256.upper()},
        "phase": phase, "sourceInventorySha256": inventory_sha256.upper(),
        "changedPaths": [], "allowlistTransitions": [], "allowlistStates": [], "inventoryComplete": False,
        "safeToCompare": False, "errors": [],
    }
    errors: list[str] = []
    if branch != EXPECTED_BRANCH or head != EXPECTED_HEAD:
        base["errors"] = ["branch or HEAD differs from the approved source pin"]
        return base
    if (inventory.get("schemaVersion") != 1 or inventory.get("worktree") != str(canonical)
            or inventory.get("branch") != branch or inventory.get("head") != head):
        base["errors"] = ["source-inventory identity or schema differs from the approved worktree"]
        return base
    try:
        expected_rows = _inventory_rows(inventory.get(f"{phase}ChangedPaths"), phase)
        transitions = _inventory_transitions(inventory.get("allowlistTransitions"))
    except RuntimeError as error:
        base["errors"] = [str(error)]
        return base
    base["allowlistTransitions"] = [
        {"path": path, **transitions[path]} for path in sorted(transitions)
    ]
    raw = git(canonical, git_executable, git_executable_sha256,
              "-c", "core.quotepath=false", "status", "--porcelain=v1", "-z", "--untracked-files=all")
    tokens, index, actual_status = raw.split(b"\0"), 0, {}
    while index < len(tokens) and tokens[index]:
        record = tokens[index]
        index += 1
        status, name = record[:2].decode("ascii"), record[3:].decode("utf-8", "surrogateescape")
        if ("R" in status or "C" in status or not name
                or not safe_repo_relative_path(name) or no_read(name) or name in actual_status):
            errors.append("rename/copy/duplicate/unclassifiable Git status; fail closed")
            break
        actual_status[name] = status
    if errors:
        base["errors"] = errors
        return base
    expected_status = {path: row["status"] for path, row in expected_rows.items()}
    if actual_status != expected_status:
        errors.append("Git-visible path/status set differs from the owner-pinned source inventory")
        base["changedPaths"] = [{"path": path, "status": status, "state": "NOT_READ", "bytes": None, "sha256": None}
                                for path, status in sorted(actual_status.items())]
        base["errors"] = errors
        return base
    for path, mode in E_E_N_R.items():
        transition = transitions[path]
        expected = transition["preStatus" if phase == "pre" else "postStatus"]
        if mode == "N" and phase == "pre" and (
                transition["preStatus"] != "  " or path in actual_status):
            errors.append("N pre-state requires blank status and no Git-visible path row")
        elif mode == "N" and phase == "post" and (
                transition["postStatus"] != "??" or actual_status.get(path) != "??"
                or expected_rows.get(path) is None
                or expected_rows[path]["status"] != "??"
                or expected_rows[path]["disposition"] != "HASH"):
            errors.append("N post-state requires an owner-pinned HASH row and actual Git-visible ?? status")
        elif transition["mode"] != mode or actual_status.get(path, "  ") != expected:
            errors.append("owner-pinned E/E/N/R status differs")
    for path, row in expected_rows.items():
        if row["disposition"] != "HASH" or no_read(path):
            errors.append("EXCLUDED_NO_READ or unsafe inventory row; no changed-file content was read")
    if errors:
        base["errors"] = errors
        return base

    relevant = dict(actual_status)
    for path in E_E_N_R:
        relevant.setdefault(path, "  ")
    for path, status in sorted(relevant.items()):
        allow_absent = (path == N_PATH and phase == "pre" and path not in actual_status
                        and transitions[path]["preStatus"] == "  ")
        kind = _file_kind(canonical, path, status, allow_absent)
        if kind == "EXCLUDED_NO_READ" or kind in ("UNREADABLE", "UNCLASSIFIABLE"):
            errors.append("unsafe or unclassifiable inventory row; no changed-file content was read")
        elif path in E_E_N_R and E_E_N_R[path] in ("E", "R") and kind != "PRESENT":
            errors.append("E/R allowlist state must be PRESENT")
        elif path == N_PATH and phase == "pre" and kind != "ABSENT":
            errors.append("N path must be ABSENT before implementation")
        elif path == N_PATH and phase == "post" and kind != "PRESENT":
            errors.append("N path must be PRESENT after implementation")
        elif kind == "ABSENT" and not (allow_absent or "D" in status):
            errors.append("ABSENT is not represented by an allowed Git status")
    if errors:
        base["errors"] = errors
        return base

    states = {
        path: file_state(canonical, path, status,
                         allow_absent=(path == N_PATH and phase == "pre"
                                       and path not in actual_status
                                       and transitions[path]["preStatus"] == "  "))
        for path, status in sorted(relevant.items())
    }
    for path, state in states.items():
        if state["state"] in ("EXCLUDED_NO_READ", "UNREADABLE", "UNCLASSIFIABLE"):
            errors.append("file state changed after metadata preflight")
    if errors:
        base["errors"] = errors
        return base
    pinned_states, pinned_errors = capture_pinned_input_states(canonical, phase, actual_status, states)
    errors.extend(pinned_errors)
    changed = [states[path] for path in sorted(actual_status)]
    tuples = []
    for path, mode in sorted(E_E_N_R.items()):
        item = dict(states[path])
        item["mode"] = mode
        tuples.append(item)
    base.update({
        "changedPaths": changed,
        "allowlistStates": tuples,
        "pinnedInputManifest": dict(sorted(PINNED_INPUTS.items())),
        "pinnedInputStates": pinned_states,
        "inventoryComplete": not errors,
        "safeToCompare": not errors,
        "errors": errors,
    })
    return base

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-Backend", required=True)
    parser.add_argument("-RunRoot", required=True)
    parser.add_argument("-Phase", required=True, choices=("pre", "post"))
    parser.add_argument("-LockEvidencePath", required=True)
    parser.add_argument("-LockEvidenceSha256", required=True)
    parser.add_argument("-SourceInventoryPath", required=True)
    parser.add_argument("-SourceInventorySha256", required=True)
    parser.add_argument("-GitExecutablePath", required=True)
    parser.add_argument("-GitExecutableSha256", required=True)
    args = parser.parse_args()
    root = WORKTREE.resolve(strict=True)
    backend = Path(args.Backend).resolve(strict=True)
    if backend != (root / "backend").resolve(strict=True):
        raise RuntimeError("backend path differs from the approved worktree")
    output = Path(args.RunRoot).resolve(strict=True)
    lock_path = Path(args.LockEvidencePath).resolve(strict=True)
    lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    if sha(lock_path.read_bytes()) != args.LockEvidenceSha256.upper():
        raise RuntimeError("lock-resolution evidence hash mismatch")
    inventory_path = Path(args.SourceInventoryPath).resolve(strict=True)
    try:
        inventory_path.relative_to(root)
    except ValueError:
        pass
    else:
        raise RuntimeError("source-inventory input must be stored outside the approved worktree")
    inventory_bytes = inventory_path.read_bytes()
    if sha(inventory_bytes) != args.SourceInventorySha256.upper():
        raise RuntimeError("source-inventory evidence hash mismatch")
    inventory = json.loads(inventory_bytes.decode("utf-8"))
    if not isinstance(inventory, dict):
        raise RuntimeError("source-inventory evidence must be a JSON object")
    validate_inventory_path_strings(inventory)
    git_executable = Path(args.GitExecutablePath)
    if not git_executable.is_absolute():
        raise RuntimeError("owner-pinned Git executable path must be absolute")
    git_executable = git_executable.resolve(strict=True)
    if (not git_executable.is_file() or git_executable.suffix.casefold() != ".exe"
            or str(git_executable) != args.GitExecutablePath
            or not re.fullmatch(r"[A-Fa-f0-9]{64}", args.GitExecutableSha256)
            or sha(git_executable.read_bytes()) != args.GitExecutableSha256.upper()):
        raise RuntimeError("owner-pinned Git executable path or SHA-256 is invalid")
    state = source_state(root, args.Phase, inventory, args.SourceInventorySha256,
                         git_executable, args.GitExecutableSha256)
    (output / "source-state.json").write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if not state["safeToCompare"]:
        raise SystemExit(2)
    fastapi_version = importlib.metadata.version("fastapi")
    identity = normalized_environment_identity(
        Path(args.RunRoot).absolute(), backend, state, lock_data, args.LockEvidenceSha256, fastapi_version
    )
    (output / "environment.json").write_text(
        json.dumps({"phase": args.Phase, "identity": identity}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    from sketch2life.infrastructure.config import settings as settings_module

    original_settings = settings_module.Settings
    original_core = settings_module.CoreDatabaseSettings
    class IsolatedSettings(original_settings):
        model_config = {**original_settings.model_config, "env_file": None}
    class IsolatedCoreSettings(original_core):
        model_config = {**original_core.model_config, "env_file": None}
    settings_module.Settings = IsolatedSettings
    settings_module.CoreDatabaseSettings = IsolatedCoreSettings
    settings_module.get_settings = lambda: IsolatedSettings(_env_file=None)
    settings_module.get_core_database_settings = lambda: IsolatedCoreSettings(_env_file=None)
    from sketch2life.interfaces.http import be1_runtime
    be1_runtime.Settings = IsolatedSettings
    be1_runtime.get_settings = settings_module.get_settings
    be1_runtime.get_core_database_settings = settings_module.get_core_database_settings
    from sketch2life.interfaces.http.app import create_app

    application = None
    try:
        application = create_app()
        published = application.openapi()
        runtime = getattr(application.state, "runtime_openapi_schema", None)
        for label, document in (("runtime", runtime), ("published", published)):
            if (not isinstance(document, dict)
                    or not isinstance(document.get("openapi"), str)
                    or not document["openapi"].strip()
                    or not isinstance(document.get("info"), dict)
                    or not isinstance(document.get("paths"), dict)):
                raise RuntimeError(f"{label} OpenAPI schema is absent or malformed")
        (output / f"runtime-{args.Phase}.json").write_text(json.dumps(runtime, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        (output / f"published-{args.Phase}.json").write_text(json.dumps(published, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    finally:
        runtime = getattr(getattr(application, "state", None), "be1_runtime", None)
        engine = getattr(runtime, "engine", None)
        if engine is not None:
            engine.dispose()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        print("OpenAPI export failed; diagnostic details withheld.", file=sys.stderr)
        raise SystemExit(1) from None
```
<!-- payload-end:openapi-export.py -->

### `schema-comparator.py`

<!-- payload-begin:schema-comparator.py -->
```python
from __future__ import annotations

import argparse
import copy as _copy
import hashlib
import json
import sys
import re
from pathlib import Path
from urllib.parse import urlsplit

from packaging.markers import default_environment
from packaging.tags import sys_tags

METHODS = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}
N_PATH = "backend/tests/contract/test_openapi_schema_catalog_mapping.py"
NO_READ_PARTS = (".env", "secret", "credential", "service-account", "firebase-adminsdk",
                 "real-data", "child-media", "seed-account", "seed-user")
NO_READ_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
E_E_N_R = {
    "backend/src/sketch2life/interfaces/http/app.py": "E",
    "backend/tests/contract/test_openapi_contract_catalog.py": "E",
    N_PATH: "N",
    "backend/tests/contract/test_app_composition.py": "R",
}
PINNED_INPUTS = {
    "backend/pyproject.toml": "35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2",
    "backend/src/sketch2life/infrastructure/config/settings.py": "B430FA3036B1621CE0EB6283C94642E57AFF367FB8C45F7819E556D7D4180E65",
    "backend/src/sketch2life/infrastructure/storage/s3_compatible.py": "43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B",
    "backend/src/sketch2life/interfaces/http/app.py": "E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031",
    "backend/src/sketch2life/interfaces/http/be1_runtime.py": "62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85",
    "backend/src/sketch2life/interfaces/http/openapi_contract.py": "175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE",
    "backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py": "E16DE02140E7977A014F32D9CF131DAC8FC63EA622CEDD26B702958D7B92BB09",
    "backend/src/sketch2life/interfaces/http/openapi_srs_v22.py": "29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3",
    "backend/src/sketch2life/interfaces/http/router_composition.py": "2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463",
    "backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py": "7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF",
    "backend/tests/contract/test_app_composition.py": "1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52",
    "backend/tests/contract/test_openapi_contract_catalog.py": "BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198",
    N_PATH: None,
    "backend/uv.lock": "830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def pointer(parts: list[str]) -> str:
    return "/" + "/".join(str(x).replace("~", "~0").replace("/", "~1") for x in parts)


def walk(before: object, after: object, parts: list[str] | None = None) -> list[dict[str, object]]:
    parts = parts or []
    if type(before) is not type(after):
        return [{"pointer": pointer(parts), "before": before, "after": after}]
    rows = []
    if isinstance(before, dict):
        for key in sorted(set(before) | set(after)):
            next_parts = parts + [str(key)]
            if key not in before:
                rows.append({"pointer": pointer(next_parts), "before": None, "after": after[key], "kind": "addition"})
            elif key not in after:
                rows.append({"pointer": pointer(next_parts), "before": before[key], "after": None, "kind": "removal"})
            else:
                rows.extend(walk(before[key], after[key], next_parts))
    elif isinstance(before, list):
        if len(before) != len(after):
            rows.append({"pointer": pointer(parts), "before": before, "after": after, "kind": "array-change"})
        else:
            for index, (left, right) in enumerate(zip(before, after)):
                rows.extend(walk(left, right, parts + [str(index)]))
    elif before != after:
        rows.append({"pointer": pointer(parts), "before": before, "after": after, "kind": "value-change"})
    return rows


def operations(schema: dict[str, object]) -> dict[tuple[str, str], dict[str, object]]:
    found = {}
    for path, path_item in schema.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() in METHODS and isinstance(operation, dict):
                found[(method.lower(), path)] = operation
    return found


def request_ids(schema: dict[str, object]) -> dict[str, object]:
    found = {}
    for (method, path), operation in sorted(operations(schema).items()):
        request = []
        for index, value in enumerate(operation.get("parameters", [])):
            if isinstance(value, dict) and str(value.get("name", "")).lower() == "x-request-id":
                request.append({"pointer": f"/parameters/{index}", "object": value})
        response = []
        for status, item in operation.get("responses", {}).items():
            headers = item.get("headers", {}) if isinstance(item, dict) else {}
            if isinstance(headers, dict):
                for name, value in headers.items():
                    if name.lower() == "x-request-id":
                        response.append({"pointer": f"/responses/{status}/headers/{name}", "object": value})
        if request or response:
            found[f"{method} {path}"] = {"request": request, "response": response}
    return found


def _valid_porcelain_status(value: object, allow_blank: bool = False) -> bool:
    if not isinstance(value, str) or len(value) != 2:
        return False
    if value == "  ":
        return allow_blank
    if value == "??":
        return True
    return all(char in " MADUT" for char in value)


def _safe_changed_path(value: object) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value or ":" in value:
        return False
    if any(not character.isprintable() for character in value):
        return False
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts) or "/".join(parts) != value:
        return False
    folded_parts = [part.casefold() for part in parts]
    if any(token in part for part in folded_parts for token in NO_READ_PARTS):
        return False
    filename = folded_parts[-1]
    return not filename.startswith(".env") and not filename.endswith(NO_READ_SUFFIXES)


def _validated_changed_paths(source: dict[str, object], phase: str, errors: list[str]) -> dict[str, dict[str, object]]:
    raw_rows = source.get("changedPaths")
    if not isinstance(raw_rows, list):
        errors.append(f"{phase} changedPaths is not a list")
        return {}
    result: dict[str, dict[str, object]] = {}
    previous = ""
    required = {"path", "status", "state", "bytes", "sha256"}
    for row in raw_rows:
        if not isinstance(row, dict) or set(row) != required:
            errors.append(f"{phase} changedPaths contains a malformed row")
            continue
        path, status, state = row.get("path"), row.get("status"), row.get("state")
        if not _safe_changed_path(path):
            errors.append(f"{phase} changedPaths contains an unsafe or excluded path name")
            continue
        if (path in result or path <= previous
                or not _valid_porcelain_status(status, allow_blank=True)):
            errors.append(f"{phase} changedPaths path/status rows are invalid, duplicated, or unsorted")
            continue
        previous = path
        if state == "ABSENT":
            if ("D" not in status or row.get("bytes") is not None
                    or row.get("sha256") is not None):
                errors.append(f"{phase} ABSENT row requires D status and null bytes/hash: {path}")
        elif state == "PRESENT":
            if status == "  ":
                errors.append(f"{phase} PRESENT changedPaths row has no Git-visible status: {path}")
            if (isinstance(row.get("bytes"), bool) or not isinstance(row.get("bytes"), int)
                    or row["bytes"] < 0
                    or not isinstance(row.get("sha256"), str)
                    or not re.fullmatch(r"[A-F0-9]{64}", row["sha256"])):
                errors.append(f"{phase} PRESENT row requires nonnegative bytes and a SHA-256: {path}")
        else:
            errors.append(f"{phase} changedPaths contains an unsafe/non-final state: {path}")
        result[path] = row
    return result


def _validated_allowlist_transitions(
    source: dict[str, object], phase: str, errors: list[str]
) -> dict[str, dict[str, str]]:
    raw_rows = source.get("allowlistTransitions")
    local_errors: list[str] = []
    if not isinstance(raw_rows, list):
        errors.append(f"{phase} allowlistTransitions is not a list")
        return {}
    if len(raw_rows) != len(E_E_N_R):
        local_errors.append(f"{phase} allowlistTransitions must contain exactly four rows")
    required = {"path", "mode", "preStatus", "postStatus"}
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    previous = ""
    for row in raw_rows:
        if not isinstance(row, dict) or set(row) != required:
            local_errors.append(f"{phase} allowlistTransitions contains a malformed row")
            continue
        path, mode = row.get("path"), row.get("mode")
        pre_status, post_status = row.get("preStatus"), row.get("postStatus")
        if not isinstance(path, str) or not path:
            local_errors.append(f"{phase} allowlistTransitions contains an empty/non-string path")
            continue
        if path in seen:
            local_errors.append(f"{phase} allowlistTransitions contains duplicate path")
            continue
        seen.add(path)
        if path <= previous:
            local_errors.append(f"{phase} allowlistTransitions are not in canonical path order")
        previous = path
        if path not in E_E_N_R or mode != E_E_N_R.get(path):
            local_errors.append(f"{phase} allowlistTransitions has an extra path or wrong mode")
            continue
        if (not _valid_porcelain_status(pre_status, allow_blank=True)
                or not _valid_porcelain_status(post_status, allow_blank=True)):
            local_errors.append(f"{phase} allowlistTransitions has an invalid porcelain status: {path}")
            continue
        if mode == "N" and (pre_status != "  " or post_status != "??"):
            local_errors.append("N transition requires blank preStatus and ?? postStatus")
        if mode == "R" and pre_status != post_status:
            local_errors.append(f"R transition status changed: {path}")
        rows.append({"path": path, "mode": mode,
                     "preStatus": pre_status, "postStatus": post_status})
    if set(seen) != set(E_E_N_R):
        local_errors.append(f"{phase} allowlistTransitions do not cover the exact E/E/N/R path set")
    if local_errors:
        errors.extend(local_errors)
        return {}
    return {row["path"]: row for row in rows}


def _validated_allowlist_states(
    source: dict[str, object], phase: str, transitions: dict[str, dict[str, str]], errors: list[str]
) -> dict[str, dict[str, object]]:
    raw_rows = source.get("allowlistStates")
    local_errors: list[str] = []
    if not isinstance(raw_rows, list):
        errors.append(f"{phase} allowlistStates is not a list")
        return {}
    if len(raw_rows) != len(E_E_N_R):
        local_errors.append(f"{phase} allowlistStates must contain exactly four rows")
    required = {"path", "mode", "status", "state", "bytes", "sha256"}
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    previous = ""
    for row in raw_rows:
        if not isinstance(row, dict) or set(row) != required:
            local_errors.append(f"{phase} allowlistStates contains a malformed row")
            continue
        path, mode = row.get("path"), row.get("mode")
        status, state = row.get("status"), row.get("state")
        if not isinstance(path, str) or not path:
            local_errors.append(f"{phase} allowlistStates contains an empty/non-string path")
            continue
        if path in seen:
            local_errors.append(f"{phase} allowlistStates contains duplicate path")
            continue
        seen.add(path)
        if path <= previous:
            local_errors.append(f"{phase} allowlistStates are not in canonical path order")
        previous = path
        if path not in E_E_N_R or mode != E_E_N_R.get(path):
            local_errors.append(f"{phase} allowlistStates has an extra path or wrong mode")
            continue
        transition = transitions.get(path)
        if transition is None:
            local_errors.append(f"{phase} allowlistStates has no validated transition: {path}")
            continue
        expected_status = transition["preStatus" if phase == "pre" else "postStatus"]
        if status != expected_status or not _valid_porcelain_status(status, allow_blank=True):
            local_errors.append(f"{phase} allowlist state status differs from its validated transition: {path}")
        if state == "ABSENT":
            if not (path == N_PATH and phase == "pre" and status == "  "
                    and row.get("bytes") is None and row.get("sha256") is None):
                local_errors.append(f"{phase} ABSENT allowlist state is outside exact N pre-state: {path}")
        elif state == "PRESENT":
            if (isinstance(row.get("bytes"), bool) or not isinstance(row.get("bytes"), int)
                    or row["bytes"] < 0
                    or not isinstance(row.get("sha256"), str)
                    or not re.fullmatch(r"[A-F0-9]{64}", row["sha256"])):
                local_errors.append(f"{phase} PRESENT allowlist state requires bytes and SHA-256: {path}")
            if path == N_PATH and phase == "pre":
                local_errors.append("N pre-state cannot be PRESENT")
        else:
            local_errors.append(f"{phase} allowlist state is unsafe/non-final: {path}")
        rows.append(row)
    if set(seen) != set(E_E_N_R):
        local_errors.append(f"{phase} allowlistStates do not cover the exact E/E/N/R path set")
    if local_errors:
        errors.extend(local_errors)
        return {}
    return {row["path"]: row for row in rows}


def _validated_pinned_input_states(source: dict[str, object], phase: str,
                                   errors: list[str]) -> dict[str, dict[str, object]]:
    manifest = source.get("pinnedInputManifest")
    if manifest != PINNED_INPUTS:
        errors.append(f"{phase} pinned-input manifest differs from the reviewed source pins")
        return {}
    states = source.get("pinnedInputStates")
    if not isinstance(states, dict) or set(states) != set(PINNED_INPUTS):
        errors.append(f"{phase} pinned-input state map is incomplete or has extra paths")
        return {}
    result: dict[str, dict[str, object]] = {}
    for path, expected_sha256 in PINNED_INPUTS.items():
        row = states.get(path)
        if not isinstance(row, dict) or set(row) != {"status", "state", "bytes", "sha256"}:
            errors.append(f"{phase} pinned-input state row is malformed")
            continue
        status, state = row.get("status"), row.get("state")
        size, actual_sha256 = row.get("bytes"), row.get("sha256")
        if not isinstance(status, str) or len(status) != 2:
            errors.append(f"{phase} pinned-input status is malformed")
        if expected_sha256 is None:
            if phase == "pre":
                if status != "  " or state != "ABSENT" or size is not None or actual_sha256 is not None:
                    errors.append("N pre-state must be absent with blank status and null size/hash")
            elif (status != "??" or state != "PRESENT" or isinstance(size, bool)
                  or not isinstance(size, int) or size < 0 or not isinstance(actual_sha256, str)
                  or re.fullmatch(r"[A-F0-9]{64}", actual_sha256) is None):
                errors.append("N post-state must be present with ?? status, captured size and SHA-256")
        elif (state != "PRESENT" or isinstance(size, bool) or not isinstance(size, int) or size < 0
              or not isinstance(actual_sha256, str)
              or re.fullmatch(r"[A-F0-9]{64}", actual_sha256) is None):
            errors.append(f"{phase} pinned source/test input is not a valid present file state")
        elif not (phase == "post" and E_E_N_R.get(path) == "E") and actual_sha256 != expected_sha256:
            errors.append(f"{phase} pinned source/test input differs from its approved SHA-256")
        result[path] = row
    changed_paths = source.get("changedPaths")
    if not isinstance(changed_paths, list):
        errors.append(f"{phase} changed-path inventory is missing for pinned-input cross-check")
    else:
        for path, row in result.items():
            matches = [item for item in changed_paths
                       if isinstance(item, dict) and item.get("path") == path]
            if row.get("status") == "  ":
                if matches:
                    errors.append(f"{phase} unchanged pinned input appears in Git-visible changed paths")
            elif (len(matches) != 1 or any(matches[0].get(key) != row.get(key)
                                           for key in ("status", "state", "bytes", "sha256"))):
                errors.append(f"{phase} pinned-input state differs from its Git-visible changed-path row")
    return result


def source_compare(before: dict[str, object], after: dict[str, object],
                   expected_git_path: str, expected_git_sha256: str) -> list[str]:
    errors = []
    if before.get("version") != 4 or before.get("phase") != "pre":
        errors.append("pre source-state manifest has the wrong schema version or phase")
    if after.get("version") != 4 or after.get("phase") != "post":
        errors.append("post source-state manifest has the wrong schema version or phase")
    before_inventory = before.get("sourceInventorySha256")
    after_inventory = after.get("sourceInventorySha256")
    if (not re.fullmatch(r"[A-F0-9]{64}", str(before_inventory))
            or not re.fullmatch(r"[A-F0-9]{64}", str(after_inventory))
            or before_inventory != after_inventory):
        errors.append("source-inventory hash is missing, malformed, or changed between pre/post states")
    before_git = before.get("gitExecutable")
    after_git = after.get("gitExecutable")
    expected_path = Path(expected_git_path)
    try:
        canonical_expected_path = expected_path.resolve(strict=True)
        valid_expected_git = (
            expected_path.is_absolute() and str(canonical_expected_path) == expected_git_path
            and canonical_expected_path.name.casefold() == "git.exe"
            and re.fullmatch(r"[A-Fa-f0-9]{64}", expected_git_sha256) is not None
            and digest(canonical_expected_path) == expected_git_sha256.upper()
        )
    except (OSError, RuntimeError):
        valid_expected_git = False
        canonical_expected_path = expected_path
    if not valid_expected_git:
        errors.append("owner-pinned Git executable path is not canonical or its SHA-256 differs")
    def valid_git_identity(value: object) -> bool:
        return (isinstance(value, dict) and set(value) == {"path", "sha256"}
                and value.get("path") == expected_git_path
                and value.get("sha256") == expected_git_sha256.upper())
    if not valid_git_identity(before_git) or not valid_git_identity(after_git):
        errors.append("source-state Git executable identity is missing or malformed")
    elif before_git != after_git:
        errors.append("owner-pinned Git executable path or SHA-256 changed between pre/post states")
    before_pins = _validated_pinned_input_states(before, "pre", errors)
    after_pins = _validated_pinned_input_states(after, "post", errors)
    if before_pins and after_pins:
        for path in PINNED_INPUTS:
            if path == N_PATH or E_E_N_R.get(path) == "E":
                continue
            if before_pins.get(path) != after_pins.get(path):
                errors.append("immutable pinned input state changed between pre/post exports")
    for key in ("worktree", "branch", "head"):
        if before.get(key) != after.get(key):
            errors.append(f"source identity changed: {key}")
    if (before.get("safeToCompare") is not True or after.get("safeToCompare") is not True
            or before.get("inventoryComplete") is not True or after.get("inventoryComplete") is not True):
        errors.append("source-state manifest is not safe to compare")
    b_allow = _validated_allowlist_transitions(before, "pre", errors)
    a_allow = _validated_allowlist_transitions(after, "post", errors)
    if b_allow and a_allow and b_allow != a_allow:
        errors.append("owner-pinned allowlistTransitions differ between pre/post source-state manifests")
    before_paths = _validated_changed_paths(before, "pre", errors)
    after_paths = _validated_changed_paths(after, "post", errors)
    b_states = _validated_allowlist_states(before, "pre", b_allow, errors)
    a_states = _validated_allowlist_states(after, "post", a_allow, errors)
    for phase, transitions, states, paths in (
            ("pre", b_allow, b_states, before_paths), ("post", a_allow, a_states, after_paths)):
        status_key = "preStatus" if phase == "pre" else "postStatus"
        for path, transition in transitions.items():
            expected_status = transition[status_key]
            state_row = states.get(path)
            changed_row = paths.get(path)
            if expected_status == "  ":
                if changed_row is not None:
                    errors.append(f"{phase} blank-status allowlist path has a Git-visible changedPaths row: {path}")
            elif (changed_row is None or changed_row.get("status") != expected_status
                    or state_row is None
                    or (changed_row.get("state"), changed_row.get("bytes"), changed_row.get("sha256"))
                    != (state_row.get("state"), state_row.get("bytes"), state_row.get("sha256"))):
                errors.append(f"{phase} changedPaths row differs from its validated allowlist transition/state: {path}")
    for path, mode in E_E_N_R.items():
        left_transition, right_transition = b_allow.get(path), a_allow.get(path)
        left, right = b_states.get(path), a_states.get(path)
        if (not left_transition or not right_transition or not left or not right
                or left_transition.get("mode") != mode or right_transition.get("mode") != mode
                or left.get("mode") != mode or right.get("mode") != mode):
            errors.append(f"missing or wrong E/E/N/R tuple: {path}")
            continue
        if mode == "N":
            post_row = after_paths.get(path)
            if (left_transition.get("preStatus") != "  " or left.get("status") != "  "
                    or path in before_paths):
                errors.append("N pre-state requires blank status and no Git-visible path row")
            if (left.get("state"), left.get("bytes"), left.get("sha256")) != ("ABSENT", None, None):
                errors.append("N pre-state must be ABSENT/null")
            if (right_transition.get("postStatus") != "??" or right.get("status") != "??" or post_row is None
                    or post_row.get("status") != "??" or post_row.get("state") != "PRESENT"
                    or post_row.get("bytes") != right.get("bytes")
                    or post_row.get("sha256") != right.get("sha256")):
                errors.append("N post-state must have a matching Git-visible ?? row")
            if (right.get("state") != "PRESENT"
                    or isinstance(right.get("bytes"), bool)
                    or not isinstance(right.get("bytes"), int) or right["bytes"] < 0
                    or not isinstance(right.get("sha256"), str)
                    or not re.fullmatch(r"[A-F0-9]{64}", right["sha256"])):
                errors.append("N post-state must be PRESENT with nonnegative bytes and a valid SHA-256")
        elif left.get("state") != "PRESENT" or right.get("state") != "PRESENT":
            errors.append(f"E/R path must be PRESENT in both states: {path}")
        if mode == "R" and left != right:
            errors.append("R path changed")
    for path in sorted((set(before_paths) | set(after_paths)) - set(E_E_N_R)):
        if before_paths.get(path) != after_paths.get(path):
            errors.append(f"out-of-allowlist Git-visible path changed: {path}")
    return errors


def _load_openapi_schema(path: Path, label: str) -> dict[str, object]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise RuntimeError(f"{label} OpenAPI input is missing, unreadable, or malformed") from None
    if (not isinstance(document, dict)
            or not isinstance(document.get("openapi"), str)
            or not document["openapi"].strip()
            or not isinstance(document.get("info"), dict)
            or not isinstance(document.get("paths"), dict)):
        raise RuntimeError(f"{label} OpenAPI root is null, non-object, or missing required structure")
    return document


import copy as _copy
import re as _re

_SESSION = ("post", "/v1/sessions")
_IMAGE = ("post", "/v1/sessions/{session_id}/media/image")
_PORTFOLIO = ("get", "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio")
_RESTORE = ("post", "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/restore")
_DESCRIPTION_SUFFIXES = {
    _SESSION: "\n\n**Local synthetic Try it out:** use a fresh UUIDv4 for \x60session_id\x60. Copy \x60observed_session_version\x60 from the response into the next request. This demo session is process-local and makes no persistent database write.",
    _IMAGE: "\n\n**Local synthetic Try it out:** first call \x60POST /v1/sessions\x60, then use its \x60session_id\x60 and \x60observed_session_version\x60. Select the supplied synthetic non-child PNG above, keep \x60normalization_policy\x60 as \x60IDENTITY_V1\x60, and set \x60X-Synthetic-Non-Child-Confirmed\x60 to \x60true\x60. The upload is processed locally without invoking an AI provider.",
    _PORTFOLIO: "\n\n**Implementation gap:** the Rev37 catalog lists a 200 response, but the current handler has no success path. After profile lookup it returns \x60409 CONSENT_NOT_EFFECTIVE\x60 until an approved portfolio-purpose verifier is available.",
    _RESTORE: "\n\n**Access:** a valid bearer token and a Teacher or School Admin assignment for the class. Effective group consent and an existing checkpoint are required. This operation is available in local/test until production checkpoint storage is configured.",
}


def _mapper_description(key: tuple[str, str], purpose: str) -> str:
    return (purpose + _DESCRIPTION_SUFFIXES.get(key, "")).strip()


def _mapper_response_schema(name: str, schema: dict[str, object]) -> dict[str, object]:
    components = schema.get("components", {})
    schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
    if isinstance(schemas, dict) and name in schemas:
        return {"$ref": f"#/components/schemas/{name}"}
    if name == "binary":
        return {"type": "string", "format": "binary"}
    if name == "object":
        return {"type": "object"}
    match = _re.match(r"^list\[([A-Za-z][A-Za-z0-9_]*)", name)
    if match and isinstance(schemas, dict) and match.group(1) in schemas:
        return {"type": "array", "items": {"$ref": f"#/components/schemas/{match.group(1)}"}}
    raise ValueError(f"catalog response schema is absent from components: {name}")


def _mapper_expected_runtime(before: dict[str, object], catalog: object, public_tag_name: object,
                             published_responses: object, restore_descriptions: object,
                             binary_responses: object) -> tuple[dict[str, object], list[str]]:
    expected = _copy.deepcopy(before)
    found = operations(expected)
    errors = []
    for key, contract in catalog.items():
        operation = found.get(key)
        if operation is None:
            errors.append(f"runtime pre-schema missing catalog key: {key}")
            continue
        operation["tags"] = [public_tag_name(contract["tag"])]
        operation["description"] = _mapper_description(key, str(contract["purpose"]))
        rows = {str(row["status"]): row for row in published_responses(key, contract["responses"])}
        responses = operation.get("responses")
        if not isinstance(responses, dict):
            errors.append(f"runtime responses invalid at {key}")
            continue
        if key[1].startswith(("/api/be1/v1/", "/v1/parent/profiles")):
            for status in tuple(responses):
                if status not in rows:
                    del responses[status]
        for status in tuple(responses):
            if status not in rows:
                continue
            response = responses[status]
            if not isinstance(response, dict):
                errors.append(f"retained response is not an object at {key} status {status}")
                continue
            row = rows[status]
            response["description"] = (
                restore_descriptions.get(status, row["description"]) if key == _RESTORE else row["description"]
            )
            media, schema_name = row.get("media_type"), row.get("schema_name")
            if status == "422" and key[1].startswith("/v1/parent/profiles") and media:
                response["content"] = {media: {"schema": _mapper_response_schema(str(schema_name), expected)}}
            if key in binary_responses and status.startswith("2") and media:
                response["content"] = {media: {"schema": _mapper_response_schema(str(schema_name), expected)}}
            if media and schema_name == "object":
                content = response.get("content")
                media_object = content.get(media) if isinstance(content, dict) else None
                response_schema = media_object.get("schema") if isinstance(media_object, dict) else None
                if isinstance(response_schema, dict):
                    response_schema.setdefault("type", "object")
        if set(responses) != set(rows):
            errors.append(f"catalog response status set absent from pre-state at {key}; additions are forbidden")
    return expected, errors


def _schema_refs(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            found.add(ref.rsplit("/", maxsplit=1)[-1])
        for child in value.values():
            found.update(_schema_refs(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_schema_refs(child))
    return found


def _example_schema(key: tuple[str, str], amendments: object) -> dict[str, object]:
    schema = amendments._schema_for_example(amendments.SYNTHETIC_RESPONSE_EXAMPLES[key])
    for field_path in amendments.NULLABLE_RESPONSE_FIELDS.get(key, ()):
        amendments._mark_nullable(schema, field_path)
    for field_path in amendments.CONDITIONALLY_OMITTED_RESPONSE_FIELDS.get(key, ()):
        amendments._mark_optional(schema, field_path)
    amendments._describe_open_objects(schema, {})
    return schema


def _catalog_response_errors(kind: str, operation: dict[str, object], key: tuple[str, str],
                             contract: dict[str, object], published_responses: object,
                             restore_descriptions: object, amendments: object,
                             publicize_openapi_terms: object) -> list[str]:
    errors = []
    rows = {str(row["status"]): row for row in published_responses(key, contract["responses"])}
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        return [f"{kind} responses invalid at {key}"]
    if set(responses) != set(rows):
        errors.append(f"{kind} catalog response status mismatch at {key}")
    success = next((status for status in responses if str(status).startswith("2")), None)
    for status, row in rows.items():
        response = responses.get(status)
        if not isinstance(response, dict):
            errors.append(f"{kind} response missing at {key} status {status}")
            continue
        description = restore_descriptions.get(status, row["description"]) if key == _RESTORE else row["description"]
        if kind == "published":
            description = publicize_openapi_terms(description)
        if response.get("description") != description:
            errors.append(f"{kind} response description mismatch at {key} status {status}")
        media = row.get("media_type")
        content = response.get("content", {})
        if not media:
            if content:
                errors.append(f"{kind} undeclared response content at {key} status {status}")
            continue
        if not isinstance(content, dict) or set(content) != {media}:
            errors.append(f"{kind} response media mismatch at {key} status {status}")
            continue
        media_object = content.get(media)
        schema = media_object.get("schema") if isinstance(media_object, dict) else None
        if not isinstance(schema, dict):
            errors.append(f"{kind} response schema missing at {key} status {status}")
            continue
        name = row.get("schema_name")
        if key in amendments.SYNTHETIC_RESPONSE_EXAMPLES and status == success and media == "application/json":
            expected_schema = _example_schema(key, amendments)
            if kind == "published":
                expected_schema = publicize_openapi_terms(_copy.deepcopy(expected_schema))
            if schema != expected_schema:
                errors.append(f"{kind} example-derived response schema mismatch at {key} status {status}")
        elif name == "binary":
            if schema != {"type": "string", "format": "binary"}:
                errors.append(f"{kind} binary schema mismatch at {key} status {status}")
        elif name == "object":
            if schema.get("type") != "object":
                errors.append(f"{kind} object response schema mismatch at {key} status {status}")
        elif name:
            list_match = _re.match(r"^list\[([A-Za-z][A-Za-z0-9_]*)", str(name))
            expected_name = list_match.group(1) if list_match else str(name)
            if kind == "published":
                expected_name = publicize_openapi_terms(expected_name)
            if expected_name not in _schema_refs(schema):
                errors.append(f"{kind} response schema reference mismatch at {key} status {status}")
            if list_match and schema.get("type") != "array":
                errors.append(f"{kind} list response schema mismatch at {key} status {status}")
    return errors


def _operation_id_errors(kind: str, label: str, schema: dict[str, object]) -> list[str]:
    errors = []
    seen = {}
    for key, operation in operations(schema).items():
        value = operation.get("operationId")
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{kind} {label} operationId missing at {key}")
        elif value in seen:
            errors.append(f"{kind} {label} operationId duplicate at {seen[value]} and {key}")
        else:
            seen[value] = key
    return errors


def _non_operation_schema(schema: dict[str, object]) -> dict[str, object]:
    result = _copy.deepcopy(schema)
    paths = result.get("paths", {})
    if isinstance(paths, dict):
        for path, item in list(paths.items()):
            if isinstance(item, dict):
                paths[path] = {name: value for name, value in item.items()
                               if not isinstance(name, str) or name.lower() not in METHODS}
    return result


def _environment_errors(env: dict[str, object], source: dict[str, object], label: str) -> list[str]:
    errors = []
    identity = env.get("identity")
    if not isinstance(identity, dict):
        return [f"{label} sanitized environment identity missing"]
    required = {
        "interpreter", "interpreterExecutableSha256", "pythonVersion", "pythonImplementation", "pythonCacheTag", "compatibleTags",
        "markerEnvironment", "platformIdentity", "system", "release", "machine", "fastapiVersion",
        "lockIdentity", "sourceIdentity", "effectiveChildEnvironment", "pathTemplates", "profile",
        "storyRunLiteDemo", "dotenvDisabled", "awsMetadataDisabled", "awsConfigPathsAbsent",
        "dbSentinelConfigured", "runtimeIsolationProven", "databaseAccessProvenAbsent",
        "providerAccessProvenAbsent", "networkIsolationProven",
    }
    if set(identity) != required:
        errors.append(f"{label} environment identity has unapproved fields")
    if not _re.fullmatch(r"[A-F0-9]{64}", str(identity.get("interpreterExecutableSha256", ""))):
        errors.append(f"{label} interpreter executable SHA-256 is missing or malformed")
    if (not isinstance(identity.get("interpreter"), str)
            or not Path(identity["interpreter"]).is_absolute()):
        errors.append(f"{label} interpreter path is missing or not absolute")
    allow = identity.get("effectiveChildEnvironment")
    if not isinstance(allow, dict) or set(allow) != {
            "names", "valueCategories", "syntheticCredentialNames", "credentialValuesRecorded",
            "credentialHashesRecorded", "rawEnvironmentRecorded"}:
        errors.append(f"{label} effective environment allowlist invalid")
    else:
        names, categories = allow.get("names"), allow.get("valueCategories")
        if not isinstance(names, list) or names != sorted(names) or not isinstance(categories, dict) or set(names) != set(categories):
            errors.append(f"{label} environment names/categories incomplete or unsorted")
        if allow.get("syntheticCredentialNames") != ["SKETCH2LIFE_S3_ACCESS_KEY", "SKETCH2LIFE_S3_SECRET_KEY"]:
            errors.append(f"{label} synthetic credential names mismatch")
        if any(allow.get(name) is not False for name in ("credentialValuesRecorded", "credentialHashesRecorded", "rawEnvironmentRecorded")):
            errors.append(f"{label} credential/raw environment data is not explicitly excluded")
    expected_paths = {
        "runRoot": "<BACKEND_TMP>/<RUN_GUID>", "home": "<RUN_ROOT>/home", "temp": "<RUN_ROOT>/temp",
        "awsConfig": "<RUN_ROOT>/absent-aws-config", "awsCredentials": "<RUN_ROOT>/absent-aws-credentials",
        "artifactRoot": "<RUN_ROOT>/artifacts",
    }
    if identity.get("pathTemplates") != expected_paths:
        errors.append(f"{label} GUID-specific path templates are not normalized")
    if any(identity.get(name) is not False for name in (
            "runtimeIsolationProven", "databaseAccessProvenAbsent", "providerAccessProvenAbsent", "networkIsolationProven")):
        errors.append(f"{label} manifest incorrectly proves runtime/network/provider isolation")
    if identity.get("sourceIdentity") != {
            "worktree": source.get("worktree"), "branch": source.get("branch"), "head": source.get("head")}:
        errors.append(f"{label} environment/source identity mismatch")
    lock = identity.get("lockIdentity")
    if (not isinstance(lock, dict) or lock.get("fastapiLockVersion") != "0.162.0"
            or not _re.fullmatch(r"[A-F0-9]{64}", str(lock.get("evidenceSha256", "")))
            or lock.get("interpreterPath") != identity.get("interpreter")
            or lock.get("interpreterExecutableSha256") != identity.get("interpreterExecutableSha256")):
        errors.append(f"{label} lock identity is missing or unpinned")
    version = tuple(int(part) for part in str(identity.get("fastapiVersion", "0")).split(".")[:3])
    if not ((0, 162, 0) <= version <= (0, 162, 7)):
        errors.append(f"{label} FastAPI is outside the owner-accepted range")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-Backend", required=True)
    parser.add_argument("-RunRoot", required=True)
    parser.add_argument("-InputPaths", nargs=8, required=True)
    parser.add_argument("-ReportPath", required=True)
    parser.add_argument("-GitExecutablePath", required=True)
    parser.add_argument("-GitExecutableSha256", required=True)
    args = parser.parse_args()
    paths = [Path(value).resolve(strict=True) for value in args.InputPaths]
    runtime_pre = _load_openapi_schema(paths[0], "runtime pre")
    published_pre = _load_openapi_schema(paths[1], "published pre")
    runtime_post = _load_openapi_schema(paths[4], "runtime post")
    published_post = _load_openapi_schema(paths[5], "published post")
    env_pre = json.loads(paths[2].read_text(encoding="utf-8"))
    source_pre = json.loads(paths[3].read_text(encoding="utf-8"))
    env_post = json.loads(paths[6].read_text(encoding="utf-8"))
    source_post = json.loads(paths[7].read_text(encoding="utf-8"))
    from sketch2life.interfaces.http.openapi_contract import MOUNTED_OPERATIONS, TAG_DESCRIPTIONS
    from sketch2life.interfaces.http.openapi_contract_amendments import (
        BINARY_SUCCESS_RESPONSES, RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS, public_tag_name, published_responses,
    )
    from sketch2life.interfaces.http import openapi_contract_amendments as amendments
    from sketch2life.interfaces.http.openapi_srs_v22 import (
        SRS_V22_INCLUDED_OPERATIONS, SRS_V22_OPERATION_TAGS, project_srs_v22_openapi, publicize_openapi_terms,
    )
    errors, deltas = [], []
    catalog_keys = set(MOUNTED_OPERATIONS)
    runtime_before, runtime_after = operations(runtime_pre), operations(runtime_post)
    published_before, published_after = operations(published_pre), operations(published_post)
    for kind, left, right, before_schema, after_schema in (
            ("runtime", runtime_before, runtime_after, runtime_pre, runtime_post),
            ("published", published_before, published_after, published_pre, published_post)):
        if set(left) != set(right):
            errors.append(f"{kind} exact method/path set changed")
        errors.extend(_operation_id_errors(kind, "pre", before_schema))
        errors.extend(_operation_id_errors(kind, "post", after_schema))
        for key in sorted(set(left) | set(right)):
            for row in walk(left.get(key), right.get(key)):
                row.update({"schema": kind, "method": key[0], "path": key[1]})
                deltas.append(row)
    if not catalog_keys.issubset(runtime_after):
        errors.append("runtime is missing a catalog method/path key")
    if set(published_before) != set(SRS_V22_INCLUDED_OPERATIONS) or set(published_after) != set(SRS_V22_INCLUDED_OPERATIONS):
        errors.append("published operation set differs from the pinned SRS projection set")
    expected_runtime, expected_errors = _mapper_expected_runtime(
        runtime_pre, MOUNTED_OPERATIONS, public_tag_name, published_responses,
        RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS, BINARY_SUCCESS_RESPONSES,
    )
    errors.extend(expected_errors)
    if expected_runtime != runtime_post:
        errors.extend(f"unapproved runtime delta at {row['pointer']}" for row in walk(expected_runtime, runtime_post))
    if _non_operation_schema(runtime_pre) != _non_operation_schema(runtime_post):
        errors.append("runtime non-operation fields changed")
    if runtime_pre.get("components") != runtime_post.get("components"):
        errors.append("runtime components changed")
    for kind, schema, operation_map in (("runtime", runtime_post, runtime_after), ("published", published_post, published_after)):
        for key in sorted(catalog_keys & set(operation_map)):
            operation, contract = operation_map[key], MOUNTED_OPERATIONS[key]
            tag = public_tag_name(contract["tag"]) if kind == "runtime" else SRS_V22_OPERATION_TAGS.get(key)
            if contract["tag"] not in TAG_DESCRIPTIONS or operation.get("tags") != [tag]:
                errors.append(f"{kind} catalog tag mismatch at {key}")
            description = _mapper_description(key, str(contract["purpose"]))
            if kind == "published":
                description = publicize_openapi_terms(description)
            if operation.get("description") != description:
                errors.append(f"{kind} exact description mismatch at {key}")
            errors.extend(_catalog_response_errors(
                kind, operation, key, contract, published_responses,
                RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS, amendments, publicize_openapi_terms,
            ))
    for key in set(runtime_before) & set(runtime_after):
        if runtime_before[key].get("operationId") != runtime_after[key].get("operationId"):
            errors.append(f"runtime operationId changed at {key}")
    for key in set(published_before) & set(published_after):
        if published_before[key].get("operationId") != published_after[key].get("operationId"):
            errors.append(f"published operationId changed at {key}")
    try:
        if project_srs_v22_openapi(runtime_pre) != published_pre:
            errors.append("published pre-schema differs from pinned runtime projection")
        if project_srs_v22_openapi(runtime_post) != published_post:
            errors.append("published post-schema differs from pinned runtime projection")
    except Exception as error:
        errors.append(f"pinned projection failed: {type(error).__name__}")
    if _non_operation_schema(published_pre) != _non_operation_schema(published_post):
        errors.append("published non-operation fields changed")
    if published_pre.get("components") != published_post.get("components"):
        errors.append("published components changed")
    for row in walk(_non_operation_schema(runtime_pre), _non_operation_schema(runtime_post)):
        row.update({"schema": "runtime", "method": None, "path": None})
        deltas.append(row)
    for row in walk(published_pre, published_post):
        row.update({"schema": "published", "method": None, "path": None})
        deltas.append(row)
    for kind, before, after in (("runtime", runtime_pre, runtime_post), ("published", published_pre, published_post)):
        if request_ids(before) != request_ids(after):
            errors.append(f"{kind} X-Request-ID inventory changed while OPEN")
    errors.extend(_environment_errors(env_pre, source_pre, "pre"))
    errors.extend(_environment_errors(env_post, source_post, "post"))
    env_deltas = walk(env_pre.get("identity"), env_post.get("identity"))
    for row in env_deltas:
        row.update({"schema": "environment", "method": None, "path": None})
        deltas.append(row)
    if env_deltas:
        errors.append("normalized environment identity changed")
    # This sole CLI main validates all four schema roots before comparison and keeps source-state fail-closed checks on the entry path.
    source_errors = source_compare(
        source_pre, source_post, args.GitExecutablePath, args.GitExecutableSha256
    )
    errors.extend(source_errors)
    report_validation_errors: list[str] = []
    before_paths = _validated_changed_paths(source_pre, "pre", report_validation_errors)
    after_paths = _validated_changed_paths(source_post, "post", report_validation_errors)
    before_transitions = _validated_allowlist_transitions(source_pre, "pre", report_validation_errors)
    after_transitions = _validated_allowlist_transitions(source_post, "post", report_validation_errors)
    before_allow = _validated_allowlist_states(source_pre, "pre", before_transitions, report_validation_errors)
    after_allow = _validated_allowlist_states(source_post, "post", after_transitions, report_validation_errors)
    errors.extend(error for error in report_validation_errors if error not in errors)
    report = {
        "version": 2,
        "inputs": [{"path": str(path), "sha256": digest(path)} for path in paths],
        "environmentIdentity": {"pre": env_pre.get("identity"), "post": env_post.get("identity")},
        "sourceState": {
            "sourceInventorySha256": {
                "pre": source_pre.get("sourceInventorySha256"),
                "post": source_post.get("sourceInventorySha256"),
            },
            "pathDeltas": [{"path": key, "before": before_paths.get(key), "after": after_paths.get(key)}
                           for key in sorted(set(before_paths) | set(after_paths))
                           if before_paths.get(key) != after_paths.get(key)],
            "allowlistTransitionDeltas": [{"path": key, "before": before_transitions.get(key),
                                           "after": after_transitions.get(key)}
                                          for key in sorted(set(before_transitions) | set(after_transitions))
                                          if before_transitions.get(key) != after_transitions.get(key)],
            "allowlistStateDeltas": [{"path": key, "before": before_allow.get(key), "after": after_allow.get(key)}
                                     for key in sorted(set(before_allow) | set(after_allow))
                                     if before_allow.get(key) != after_allow.get(key)],
            "errors": source_errors,
        },
        "fieldDeltas": deltas,
        "invariants": {"passed": not errors, "errors": errors},
        "passed": not errors,
    }
    Path(args.ReportPath).write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 2



if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- payload-end:schema-comparator.py -->

### `pytest-bootstrap.py`

<!-- payload-begin:pytest-bootstrap.py -->
```python
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

SELECTIONS = (
    "tests/contract/test_openapi_schema_catalog_mapping.py",
    "tests/contract/test_openapi_contract_catalog.py",
    "tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate",
)


def _pytest_environment_identity(root: Path, backend: Path, evidence: dict[str, object],
                                evidence_hash: str, fastapi_version: str) -> dict[str, object]:
    import os
    import platform
    import re
    import sys
    from packaging.markers import default_environment
    from packaging.tags import sys_tags
    from urllib.parse import urlsplit

    env = os.environ
    interpreter_path = Path(sys.executable).resolve(strict=True)
    interpreter_sha256 = hashlib.sha256(interpreter_path.read_bytes()).hexdigest().upper()
    names = {
        "SYSTEMROOT", "WINDIR", "PATH", "PATHEXT", "PYTHONPATH", "PYTHONNOUSERSITE",
        "PYTHONDONTWRITEBYTECODE", "PYTHONUTF8", "PYTHON_DOTENV_DISABLED", "HOME",
        "USERPROFILE", "TEMP", "TMP", "TMPDIR", "AWS_EC2_METADATA_DISABLED",
        "AWS_CONFIG_FILE", "AWS_SHARED_CREDENTIALS_FILE", "AWS_DEFAULT_REGION",
        "SKETCH2LIFE_ENV", "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED", "SKETCH2LIFE_BE1_ARTIFACT_ROOT",
        "SKETCH2LIFE_S3_ACCESS_KEY", "SKETCH2LIFE_S3_SECRET_KEY",
        "SKETCH2LIFE_DATABASE_URL", "STORYRUN_LITE_MAIN_DEMO_ENABLED",
    }
    if set(env) != names:
        raise RuntimeError("effective pytest child environment allowlist mismatch")
    system_root = env.get("SystemRoot", "")
    expected = {
        "WINDIR": system_root,
        "PATH": os.pathsep.join((str(Path(sys.executable).parent), str(Path(system_root) / "System32"))),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PYTHONPATH": str(backend / "src"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUTF8": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "HOME": str(root / "home"),
        "USERPROFILE": str(root / "home"),
        "TEMP": str(root / "temp"),
        "TMP": str(root / "temp"),
        "TMPDIR": str(root / "temp"),
        "AWS_EC2_METADATA_DISABLED": "true",
        "AWS_CONFIG_FILE": str(root / "absent-aws-config"),
        "AWS_SHARED_CREDENTIALS_FILE": str(root / "absent-aws-credentials"),
        "AWS_DEFAULT_REGION": "us-east-1",
        "SKETCH2LIFE_ENV": "local",
        "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED": "false",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "false",
        "SKETCH2LIFE_BE1_ARTIFACT_ROOT": str(root / "artifacts"),
        "STORYRUN_LITE_MAIN_DEMO_ENABLED": "0",
    }
    if any(env.get(name) != value for name, value in expected.items()):
        raise RuntimeError("pytest child environment value category or path mismatch")
    if not env["SKETCH2LIFE_S3_ACCESS_KEY"].startswith("synthetic-") or not env["SKETCH2LIFE_S3_SECRET_KEY"].startswith("synthetic-"):
        raise RuntimeError("pytest S3 credentials are not synthetic-only")
    database = urlsplit(env["SKETCH2LIFE_DATABASE_URL"])
    if (database.scheme != "postgresql+psycopg" or database.hostname != "127.0.0.1"
            or database.port != 1 or database.path != "/mapper_sentinel"
            or not database.username or not database.password):
        raise RuntimeError("pytest database sentinel mismatch")
    if Path(env["AWS_CONFIG_FILE"]).exists() or Path(env["AWS_SHARED_CREDENTIALS_FILE"]).exists():
        raise RuntimeError("pytest AWS credential sentinel path unexpectedly exists")

    normalize = lambda value: re.sub(r"[-_.]+", "-", value).lower()
    def records(values: object) -> dict[str, str]:
        if not isinstance(values, list):
            raise RuntimeError("lock evidence distribution records are missing")
        result = {}
        for row in values:
            if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not isinstance(row.get("version"), str):
                raise RuntimeError("lock evidence distribution record is malformed")
            name = normalize(row["name"])
            if name in result:
                raise RuntimeError("lock evidence has duplicate normalized distributions")
            result[name] = row["version"]
        return result

    installed = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if not isinstance(name, str) or not name.strip() or normalize(name) in installed:
            raise RuntimeError("installed distribution inventory is incomplete or duplicated")
        installed[normalize(name)] = distribution.version
    evidenced = records(evidence.get("installedDistributions"))
    resolved = records(evidence.get("resolvedDistributions"))
    if installed != evidenced or {k: v for k, v in installed.items() if k != "fastapi"} != {k: v for k, v in resolved.items() if k != "fastapi"}:
        raise RuntimeError("pytest installed distributions differ from the lock evidence")
    version_tuple = tuple(int(part) for part in fastapi_version.split(".")[:3])
    if (not ((0, 162, 0) <= version_tuple <= (0, 162, 7))
            or installed.get("fastapi") != fastapi_version or resolved.get("fastapi") != "0.162.0"
            or evidence.get("fastapiInstalledVersion") != fastapi_version
            or evidence.get("fastapiLockVersion") != "0.162.0"
            or evidence.get("allNonFastApiPackagesMatch") is not True
            or evidence.get("pythonVersion") != sys.version.split()[0]
            or evidence.get("pythonImplementation") != platform.python_implementation()
            or evidence.get("interpreterPath") != str(interpreter_path)
            or evidence.get("interpreterExecutableSha256") != interpreter_sha256
            or evidence.get("platformIdentity") != platform.platform()
            or evidence.get("compatibleTags") != [str(tag) for tag in sys_tags()]
            or evidence.get("markerEnvironment") != default_environment()
            or evidence.get("uvLockSha256") != hashlib.sha256((backend / "uv.lock").read_bytes()).hexdigest().upper()
            or evidence.get("pyprojectSha256") != hashlib.sha256((backend / "pyproject.toml").read_bytes()).hexdigest().upper()):
        raise RuntimeError("pytest environment differs from the approved lock/platform evidence")
    tool = evidence.get("resolutionTool")
    if (evidence.get("schemaVersion") != 2 or not isinstance(tool, dict)
            or not all(isinstance(tool.get(key), str) and tool[key]
                       for key in ("name", "version", "executableIdentitySha256"))
            or not isinstance(evidence.get("comparisonMethod"), str)
            or not evidence["comparisonMethod"]
            or not isinstance(evidence.get("selectedDependencyGroups"), list)
            or not isinstance(evidence.get("selectedExtras"), list)):
        raise RuntimeError("pytest lock provenance identity is incomplete")
    categories = {
        "SYSTEMROOT": "windows-system-root-path", "WINDIR": "same-windows-system-root-path",
        "PATH": "interpreter-directory-and-system32-only", "PATHEXT": "fixed-windows-extension-list",
        "PYTHONPATH": "worktree-backend-src-path", "PYTHONNOUSERSITE": "enabled",
        "PYTHONDONTWRITEBYTECODE": "enabled", "PYTHONUTF8": "enabled",
        "PYTHON_DOTENV_DISABLED": "enabled", "HOME": "run-root-home-path",
        "USERPROFILE": "same-run-root-home-path", "TEMP": "run-root-temp-path",
        "TMP": "same-run-root-temp-path", "TMPDIR": "same-run-root-temp-path",
        "AWS_EC2_METADATA_DISABLED": "enabled", "AWS_CONFIG_FILE": "absent-file-under-run-root",
        "AWS_SHARED_CREDENTIALS_FILE": "absent-file-under-run-root", "AWS_DEFAULT_REGION": "us-east-1",
        "SKETCH2LIFE_ENV": "local", "SKETCH2LIFE_STORAGE_EXAMPLE_ENABLED": "disabled-for-pytest",
        "SKETCH2LIFE_SYNTHETIC_PILOT_ENABLED": "disabled-for-pytest",
        "SKETCH2LIFE_BE1_ARTIFACT_ROOT": "run-root-artifact-path",
        "SKETCH2LIFE_S3_ACCESS_KEY": "synthetic-value-present-omitted",
        "SKETCH2LIFE_S3_SECRET_KEY": "synthetic-value-present-omitted",
        "SKETCH2LIFE_DATABASE_URL": "loopback-sentinel-with-synthetic-auth-omitted",
        "STORYRUN_LITE_MAIN_DEMO_ENABLED": "disabled",
    }
    return {
        "interpreter": str(interpreter_path),
        "interpreterExecutableSha256": interpreter_sha256,
        "pythonVersion": sys.version.split()[0],
        "pythonImplementation": platform.python_implementation(),
        "pythonCacheTag": sys.implementation.cache_tag,
        "compatibleTags": [str(tag) for tag in sys_tags()],
        "markerEnvironment": default_environment(),
        "platformIdentity": platform.platform(),
        "system": platform.system(), "release": platform.release(), "machine": platform.machine(),
        "fastapiVersion": fastapi_version,
        "lockIdentity": {
            "evidenceSha256": evidence_hash.upper(),
            "interpreterPath": str(interpreter_path),
            "interpreterExecutableSha256": interpreter_sha256,
            "pyprojectSha256": evidence["pyprojectSha256"],
            "uvLockSha256": evidence["uvLockSha256"],
            "fastapiLockVersion": evidence["fastapiLockVersion"],
            "selectedDependencyGroups": sorted(evidence["selectedDependencyGroups"]),
            "selectedExtras": sorted(evidence["selectedExtras"]),
            "resolutionTool": tool, "comparisonMethod": evidence["comparisonMethod"],
            "installedDistributionCount": len(installed), "resolvedDistributionCount": len(resolved),
            "allNonFastApiPackagesMatch": True,
        },
        "sourceIdentity": {
            "worktree": r"D:\GitHub\Sketch2Life\.worktrees\m2-s2",
            "branch": "feature/feat063-m2-s2", "head": "5de30674bc826591ad4b3cc00fca53c7597ead51",
        },
        "effectiveChildEnvironment": {
            "names": sorted(names), "valueCategories": categories,
            "syntheticCredentialNames": ["SKETCH2LIFE_S3_ACCESS_KEY", "SKETCH2LIFE_S3_SECRET_KEY"],
            "credentialValuesRecorded": False, "credentialHashesRecorded": False, "rawEnvironmentRecorded": False,
        },
        "pathTemplates": {
            "runRoot": "<BACKEND_TMP>/<RUN_GUID>", "home": "<RUN_ROOT>/home",
            "temp": "<RUN_ROOT>/temp", "awsConfig": "<RUN_ROOT>/absent-aws-config",
            "awsCredentials": "<RUN_ROOT>/absent-aws-credentials", "artifactRoot": "<RUN_ROOT>/artifacts",
        },
        "profile": "combined-local-pytest-three-selection", "storyRunLiteDemo": False,
        "dotenvDisabled": True, "awsMetadataDisabled": True, "awsConfigPathsAbsent": True,
        "dbSentinelConfigured": True, "runtimeIsolationProven": False,
        "databaseAccessProvenAbsent": False, "providerAccessProvenAbsent": False, "networkIsolationProven": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-Backend", required=True)
    parser.add_argument("-RunRoot", required=True)
    parser.add_argument("-BaseTemp", required=True)
    parser.add_argument("-JunitPath", required=True)
    parser.add_argument("-ComparatorReportPath", required=True)
    parser.add_argument("-ComparatorReportSha256", required=True)
    parser.add_argument("-LockEvidencePath", required=True)
    parser.add_argument("-LockEvidenceSha256", required=True)
    parser.add_argument("-Selections", nargs=3, required=True)
    args = parser.parse_args()
    backend = Path(args.Backend).resolve(strict=True)
    root = Path(args.RunRoot).resolve(strict=True)
    base = Path(args.BaseTemp).absolute()
    if tuple(args.Selections) != SELECTIONS:
        raise RuntimeError("pytest selections differ from the approved exact three")
    evidence_path = Path(args.LockEvidencePath).resolve(strict=True)
    evidence_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest().upper()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if evidence_hash != args.LockEvidenceSha256.upper():
        raise RuntimeError("lock-resolution evidence hash mismatch")
    fastapi_version = importlib.metadata.version("fastapi")
    identity = _pytest_environment_identity(root, backend, evidence, evidence_hash, fastapi_version)
    (root / "environment.json").write_text(
        json.dumps({"phase": "post", "identity": identity}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if root not in base.parents or base.exists():
        raise RuntimeError("basetemp must be a new absolute child of this GUID root")
    report_bytes = Path(args.ComparatorReportPath).read_bytes()
    if hashlib.sha256(report_bytes).hexdigest().upper() != args.ComparatorReportSha256.upper():
        raise RuntimeError("comparator report hash mismatch")
    report = json.loads(report_bytes.decode("utf-8"))
    if report.get("passed") is not True:
        raise RuntimeError("comparator report is missing or not passed")
    import sketch2life.infrastructure.config.settings as settings_module
    original_settings = settings_module.Settings
    original_core = settings_module.CoreDatabaseSettings

    class IsolatedSettings(original_settings):
        model_config = {**original_settings.model_config, "env_file": None}

    class IsolatedCoreSettings(original_core):
        model_config = {**original_core.model_config, "env_file": None}

    settings_module.Settings = IsolatedSettings
    settings_module.CoreDatabaseSettings = IsolatedCoreSettings
    settings_module.get_settings.cache_clear()
    settings_module.get_core_database_settings.cache_clear()
    import pytest
    code = pytest.main(["-p", "no:cacheprovider", "--basetemp", str(base), "--junitxml", args.JunitPath, *args.Selections], plugins=[])
    return int(code)


if __name__ == "__main__":
    raise SystemExit(main())
```
<!-- payload-end:pytest-bootstrap.py -->
