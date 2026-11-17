# B4-RT01 local correction and completed Studio package —2026-10-15

> Latest review supersedes this earlier checkpoint: B4-RT01 CLOSED on USER_REPORTED_REMOTE
> exact32-source97PASS/0skip+224PhaseAPASS/all exits0. Full B4 NEEDS_REVISION only B4-R01
> (deferred retry page starvation); B5notstarted. See PHASE_B_B4_CODEX_REVIEW_20261015.md.
> Pending/NOT_RUN language below is historical; original package bytes remain unchanged.

- Current: **B4-RT01 OPEN / FIXED_PENDING_RUNTIME_REVIEW**, B4 not closed; B5 NOT_STARTED.
- Existing Phase B planrev3 approval/cards14/WIP1 unchanged. Original backend executor Claude
  wrote the correction; after user reported Claude's token limit until19:50, Codex completed
  only the operator package/checks/handover. All existing backend bytes were preserved.
- Current worktree/base: `.worktrees/be2-01-ai-job-foundation`,
  `feature/be2-01-ai-job-foundation`, `993a26cae78c0a4fe983033f03881838c886b176` plus dirty source.

## Existing real failure and the local correction

User supplied full initial B4 log: run2026-10-15T10:24:24Z, manifest70b2a160,32hashes verified,
95collected/88passed/7failed/0skip, PhaseA224passed/0skip, defaultfixture20PASS/d17f58a3digest,
outerexit1/RUNNER_RESULTFAIL. Provenance USER_REPORTED_REMOTE. All7failures arose when the fixture
receiver drained an empty RQ2.12 queue and `Queue.pop_job_id()` attempted to decode None.
Those7cases remain FAILED for that snapshot; the unrun correction is not runtime PASS.

Compared with the exact initial32-file manifest, only3files differ in the existing local fix:

| File | Correction |
|---|---|
| infrastructure/ai_jobs/rq_queue.py | fixture receiver uses atomic Redis LPOP, returns None on an empty queue, preserves ID decoding/Job.fetch/envelope reconstruction/deletion |
| infrastructure/ai_jobs/sql/repository.py | integer-times-typed-interval expression preserves timeout arithmetic and avoids SQLAlchemy operator-class deprecation |
| tests/unit/test_ai_job_b4_dispatch.py | two added cases: envelope argument round-trip and empty-queue receiver; timeout SQL compilation checked separately offline |

Paths above are under backend/src/sketch2life or backend/tests as appropriate. Other29manifest
files are unchanged. Independent narrow review PASS,13B4unit tests PASS; byte/string job IDs
and PostgreSQL compilation of timeout arithmetic were checked offline. This is not full B4
independent closure or a substitute for PostgreSQL/Redis runtime results.

## Local checks and packaging proof

- Direct Codex local combined PhaseA/B2/B3/B4 run: **258passed/63skipped**,exit0. Split:
  35offlineB2–B4+223PhaseApass;62PG/Redis+1Pillow-dependentHTTPskip, all skips NOT_RUN.
- Ruff and mypy on the3changedfiles: PASS. No dependency installed or service called.
- Reconstructed previous B4 from pinned base+B2+B3+B3-R01+B4 patches: all32oldhashes match.
  Generated3-filedelta, applied it on scratch: all32correctedhashes match, second apply refused,
  reverse-check against actual local source PASS, real Git index unchanged.
- Independent host-only verification: **8/8PASS**, BashsyntaxPASS. Tests cover old->corrected,
  corrected retry, container125 then safe retry, foreign tracked/untracked/source changes and
  tampered patch rejection. Rejected cases preserve source bytes. Docker was stubbed; Git
  branch/HEAD identity was adapted only in scratch. No real runtime execution is claimed.
- Original source, approved plans/approvals and old package bytes preserved; no staging,
  commit/push/deploy or backend/B5 implementation by Codex packaging.

## Exact new package

Directory: ignored `evidence/local/b4rt01-studio-package-20261015/`.

| Item | sha256 |
|---|---|
| Previous manifest b4_previous.sha256 | 70b2a1600682aec3cfe2dabd80608d45c107f88d24ed25dd18d0e804aff8ef4d |
| b4rt01_delta.patch | 44f3a80db776430b9d693388f2196fb79a2a20ec89c5e28867edc12c2810ec58 |
| b4rt01_source.sha256 (32 files) | 444cfeadd3d7d0d0e1f23663b576270f46692e870fe532071f6cf025ffd9ff01 |
| run_b4rt01_on_studio.sh | 54a1d99e6c9ad887d12689fbf7152740fd039c1f4108245f15ccd4f42a10fbf3 |
| be2-b4rt01-studio-20261015.zip | e1a768674626db631ebe3813790d04013bee92a16a367a977f916102058f88df |

The ZIP contains exactly the four operator files. It upgrades only the reported old B4 snapshot
70b2a160 or verifies an already-corrected444cfead snapshot for retry. Unknown source is refused
without reset/clean or broad overwrite. Metadata/package build status NOT_RUN refers to this
new source, not a new claim that the previous95tests were never run.

## Next operator step

User uploads the new ZIP to `$HOME/be2-b4rt01-package/` on the existing
sketch2life-backend-test Studio, verifies/extracts it and runs run_b4rt01_on_studio.sh with outer
pipefail/status capture. Exact instructions are ignored
`evidence/local/claude/prompts/B4_RT01_STUDIO_RUN_20261015.md`.

Expected current suite:97B2–B4cases(35offline+62PG/Redis),0skip; PhaseA224pass/0skip; fixture
baseline and all suite/log/outer exits0. Capture full output or the B4-RT01 summary plus final
statuses. Do not accept old95-case output as proof of the97-case correction. Attribute user
execution USER_REPORTED_REMOTE; no direct Codex Studio access exists here.

Existing environment was reported rebuilt/healthy in the user log; do not recreate it or install
anything for this package. B4 runtime PASS and independent review are still needed before B5.
Owner-fence remains ASSUMED_CONTRACT; actual integration/provider/live route remain deferred.

Receipts/builders/original docs and protected-source hashes are ignored under
`evidence/local/b4-rt01-codex-package-20261015/`; source/path maps and original diagnostic evidence
are preserved. Prompts/session handover remain local, outside publication candidates.
