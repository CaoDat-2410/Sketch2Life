# FEAT-060 implementation baseline — 2026-10-24

## Authorization and source boundary

- Owner approved Plan Rev3 directly on 2026-10-24. The approved plan SHA-256 is `777F364AFC9ED01456D4F60879BD8377111B6B15A754A6F7826153A767BD2FB4`; see `approvals/TASK_APPROVAL.md`.
- Local branch and HEAD before product-source changes: `dev` / `0a7ce768c153f2104cff930569c3eda6e484532c`.
- The 2026-10-23 FEAT-060 baseline counted 96 pre-existing modified/deleted/untracked entries, including the earlier FEAT-059 and partial FEAT-060 work. The raw current status before product-source changes is preserved in `evidence/raw/implementation-baseline-20261024/git_status_before_implementation.txt`; the tracked diff summary and untracked-path inventory are alongside it. Approval/harness record updates are included in that snapshot. Preserve all prior content; no reset, stash, merge, commit, push, or tag was performed.
- FEAT-059 completed its bounded structure cleanup with 72 files; manifest SHA-256 `87e84a4faedf0572ac0e88b21238b38eb7cd02c9ebc92aea5f4a7931528165ef`. Its prior checks are historical evidence only; FEAT-060 will rerun applicable checks against the current tree.

## Captured source and environment facts

- Selected current FE/BE source hashes before integration edits are recorded in `evidence/raw/implementation-baseline-20261024/selected_source_hashes.json`.
- System Python 3.14 lacks `alembic`; the project `backend/.venv` works. `backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini heads` reports nine separate heads: `20261014_0004` (BE1 core), `20261015_ai_0001` (AI jobs), `20261017_lc_0001` (learning content), `20261018_ap_0009` (AI policy), `20261018_kv_0001` (knowledge video), `20261018_vr_0001` (video review), `20261019_ae_0001` (activity execution), `20261019_pa_0001` (preset automation), and `20261019_vf_0001` (video failure). Do not add a classroom migration until the BE1-owned base/head and upgrade/rollback order are reviewed.
- Fresh current-tree UI baseline: Child `npm run check` stops at typecheck with missing `useEffect`, stale `verifySessionPin` test import, and unsafe `ChildDeviceContext` assertion; Teacher `npm run check` stops at build with stale app-test APIs and `erasableSyntaxOnly` constructor parameter properties in `services/be1Client.ts`; Admin build, lint, and 2 tests pass.
- Fresh current-tree backend baseline: FEAT-059 composition and session HTTP contract tests pass, 10 tests total, using `backend/.venv`. Pytest emitted a cache write permission warning only.
- FEAT-057 remains gated: BE2-07 X01 is partial; BE2-08 lacks its approved shared UoW/finalization boundary; BE2-09 X05d is blocked pending an adopted resolver/fence; BE2-14 has no adopted execution/budget authority. Keep dependent AI/video/activity workflows blocked and do not route to Modal.
- The known source-register/configuration preflight has no configured Firebase project ID, process database URL, Modal adapter or deployed Modal profile. No secret values were read. Live DB/provider tests remain conditional on approved local configuration.
- This baseline is an inventory, not a claim that the current dirty FE/BE sources are internally consistent or tested.
