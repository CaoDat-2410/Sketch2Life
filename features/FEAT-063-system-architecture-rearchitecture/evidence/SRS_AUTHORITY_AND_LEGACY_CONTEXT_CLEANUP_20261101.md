# Canonical SRS authority cleanup — publication evidence

## Scope and source

- Branch base: `origin/dev` at `f68ed2b579c89e8fb1ee3dcf7e4c8f109acd31d8`.
- Publication branch: `codex/feat063-srs-authority-20261101`.
- Approved plan: `plan/PLAN_REV43_PUBLISH_SRS_AUTHORITY_CLEANUP_20261101.md`, SHA-256 `A679446E79548E3D00452AFC6237BD689B31EAB0DE826521892C3D33FD0BD44C`.
- Canonical working SRS: `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.3-draft, still unsigned.
- The reviewed commit manifest is exactly the 36 paths listed in Plan Rev43. This publication does not include any API route/path change.

## Changes and preservation

- Added repository-level agent reading rules and a central SRS authority/reading-order record.
- Marked all 24 older tracked context files in the plan as historical/feature-local.
- Updated FEAT-063 context, decision D-119, source register, approval, status and evidence index.
- Older SRS contents are not included in the changed-path manifest. Files present at the branch base had these pre-change SHA-256 values:

| SRS source | SHA-256 before cleanup |
|---|---|
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | `7EE8CD8511AF722E33DEA08AEE4A324532A8C4A397230D74DD5632387A1B4F8B` |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md` | `D1C4AF0D42A160AAA08D1EC33F1FFD746C4EB33CA75C5D802616A5DD4502E4DE` |
| `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` | `F7F401829955C26A793C94D468C74502DC0ED465F9F35084E364B728C243C646` |

The FEAT-039 v3.5 copy and FEAT-061/062 context files are not tracked at this branch base, so they were not added to this publication. The original dirty workspace retains its separate local edits.

## Pre-commit checks

- Historical SRS hashes after the edits match the pre-cleanup hashes above.
- Historical context notices: 24/24 older tracked contexts present; FEAT-063's own context has the separate authority record.
- Exact plan manifest: 36 expected paths, 36 changed paths, no missing or extra path.
- `git diff --check`: passed.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`, 5,809 publishable files scanned; environment/credential categories excluded and no absolute machine paths found.
- Remote publication receipt is recorded below after push.

## Verification and publication receipt

- Repository security validation: `REPOSITORY_SECURITY_VALID`, 5,809 publishable files scanned; no absolute machine paths found.
- Payload commit: `7e4aaa662aff9af26e0a417f3beef529c5c63a26` (`docs(feat063): establish canonical SRS authority`), containing exactly the approved 36 paths.
- Push: successful, without force, to `origin/codex/feat063-srs-authority-20261101`.
- Remote-ref check after the payload push: `git ls-remote` returned `7e4aaa662aff9af26e0a417f3beef529c5c63a26` for that branch.
- A follow-up documentation commit updates this status/evidence receipt; the final branch head is verified after that push and reported in the delivery message.
