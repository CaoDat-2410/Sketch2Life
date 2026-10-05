# FEAT-028 status

- Task approval: APPROVED, plan revision 2 (2026-09-17, project owner follow-up request; see exact plan hash in approvals/TASK_APPROVAL.md).
- Implementation: IN_PROGRESS — 24 atlas PNG drafts / 144 indexed sprite IDs; v2 semantic catalog; backend candidate-context, prompt builder, and allowlist validation implemented.
- Visual assets: owner visual approval is recorded for all 144 catalog v2.0.0 frames and all 148 motion-cycle frames across 37 sheets. On 2026-10-02, the owner visually approved the 30-sheet/120-frame expansion; SHA-256-matched copies are in `assets/approved/`, while generated originals remain preserved. A separately approved local/test-only preview activates two QA-passing cycles from `assets/applied/`; production runtime eligibility and rights clearance remain closed. See `evidence/notes/MOTION_CYCLE_LOCAL_PREVIEW_ACTIVATION_20261002.md`.
- AI selection boundary: implemented and unit-tested as a backend-internal preparation/validation path; no provider call is made and it is not wired into FEAT-018 runtime or a public mobile contract.
- Current integration branch for these drafts: `codex/pixi-ai-show-20261001`.
- Next gates: complete rights/provenance review, per-cycle crop/pivot/loop QA, formal renderer verification, and Android visual acceptance. The bounded local preview is not production clearance. A live model/renderer integration must preserve FEAT-018 frozen versions and separate provider/contract gates.
- Scope guard: do not modify the FEAT-026 untracked SRS artifact; do not change FEAT-018 frozen contracts, source artwork, or provider/privacy boundaries without the required review.
- Validation: 16 selector tests, Ruff, and mypy pass. Catalog loader verifies 144 descriptors, 24 atlas hashes, and frame bounds. Repository harness/security scans remain globally invalid only because of pre-existing untracked FEAT-026 paths and its external SRS PDF; that user-owned folder was preserved unchanged.

## FEAT-035 integration follow-up — 2026-10-03

- The backend now permits a valid source-subject-only Pixi plan when the eligible companion set is
  empty. FEAT-028's approval, provenance, license, QA, and runtime-eligibility gates are unchanged;
  this does not activate any of the 144 descriptors or sprite cycles.
- Evidence and limitations: `../../FEAT-035-branch-review-remediation/evidence/notes/implementation-progress-20261003.md`.

## Local motion-cycle preview — 2026-10-02

- The dedicated preview allowlist contains only `motion.walker-avian.v1` and `motion.walker-corgi.v2`; source PNG hashes match their approved copies. Other cycles remain excluded, including `motion.flyer-songbird.v2` (centroid-drift QA failure).
- Focused backend tests: 22 passed; Ruff passed. Reproducible 37-cycle technical QA passed provenance/hash checks and selected exactly those two preview cycles.
- The app-root Metro configuration now resolves the workspace renderer package; the Android bundle endpoint returned HTTP 200 (8,393,141 bytes) with the app entry present. Backend `/health` returned HTTP 200.
- Android accepted/retrieved the bundle in this run, but no complete image-to-Pixi playback was observed; visible sprite animation remains pending device acceptance. Production runtime remains closed.
