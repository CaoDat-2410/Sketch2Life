# Secure branch publication and dev integration

- Status: APPROVED
- Plan revision: 1
- Implementation status: DONE
- Date: 2026-10-10, Asia/Saigon

## Goal

Publish current codex/pixi-ai-show-20261001 and integrate it into dev as explicitly requested. Preserve existing committed history, source originals and all local pending runtime bytes.

## Scope

Reviewed SRS/scope/team/governance documentation plus necessary security/harness publishing hygiene. Eight pending historical under-nine runtime paths remain local by default; they are not the replacement 36–155-month migration and have a known existing fixture mismatch. The optional scope question received no answer before publication; the stated documentation default was used after a reasonable opportunity to reply. No new product behavior/provider/deployment is authorized. Current context/register, FEAT-039/040, ADR-0014/0015, FEAT-011 publishing policy and read-only runtime/security reviews ground this operation.

## Steps

1. Inspect current branch, dirty state, exact origin/history and relevant approval context.
2. Preserve hashes and ignored local backups, exclude untracked temp/browser/test/external renders/form/capture binaries, normalize machine-specific source prose with original hashes intact, add missing evidence placeholders.
3. Run SRS/task/architecture/harness/security checks; review and stage exact documentation candidates, excluding pending runtime and local binaries.
4. Run security before commit, commit locally, run security immediately before push, push current branch without force.
5. Refresh dev; integrate only by a verified fast-forward or reviewed conflict resolution. If remote requires PR, use supported workflow and attach created PR.
6. Verify remote source/dev SHAs, protected local runtime hashes and final context/evidence/status. No reset, deletion or forced-history update.

## Acceptance criteria

- AC01: owner authorization and publication boundary recorded.
- AC02: SRS v3.1/preserved source hashes and task coverage unchanged.
- AC03: originals/local binaries/temp/credentials excluded; source prose provenance/hashes preserved with local backup.
- AC04: candidate security/harness/architecture/document checks pass and exact staged paths reviewed.
- AC05: current branch pushed; remote dev contains its resulting commit without rewriting history.
- AC06: eight pending runtime paths/bytes preserved, actual Git outcome/evidence/status recorded.

## Risks and mitigations

Dirty runtime remains untouched; stage by reviewed path list. Dev may advance: fetch and verify ancestry, never force. Keep model/runtime approval states distinct from a Git publication approval. Preserve external/local originals; exclusion does not delete files or fabricate evidence.

## Verification plan

SRS/task static validators, architecture/harness/security/skeleton, exact staged diff, source/dev ancestry and remote SHA verification. Runtime/model/device/load tests are not claimed for this documentation publication.

## Evidence plan

Own sanitized raw checks, metrics/PUBLICATION_MANIFEST.json, notes/REVIEW.md and notes/PUBLICATION.md. Record all limitations. Run repository security before every commit/push.

Implementation authorized by direct owner request recorded in approvals/TASK_APPROVAL.md revision 1.

## Completion

Commit 967f643c955332e677facb82a3ec8fe2e65c07d7 was atomically published to source and dev. Remote SHA and unchanged source/artifact/runtime-byte verification PASS. The outcome record is shipped in a follow-up documentation commit under the same approval; see evidence/notes/PUBLICATION.md.
