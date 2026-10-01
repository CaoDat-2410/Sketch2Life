# FEAT-028 status

- Task approval: APPROVED, plan revision 2 (2026-09-17, project owner follow-up request; see exact plan hash in approvals/TASK_APPROVAL.md).
- Implementation: IN_PROGRESS — 24 atlas PNG drafts / 144 indexed sprite IDs; v2 semantic catalog; backend candidate-context, prompt builder, and allowlist validation implemented.
- Visual assets: owner visual approval recorded for all 144 catalog v2.0.0 frames on 2026-10-01 (catalog SHA-256 and visual-review scope in `assets/REVIEW.md`). Rights clearance remains pending; none is copied to approved/applied or runtime-referenced, and catalog runtime eligibility remains false. Two new 4-pose walker/flyer motion-sheet drafts were added under `assets/generated/`; all eight frames await visual and rights review and are not catalogued.
- AI selection boundary: implemented and unit-tested as a backend-internal preparation/validation path; no provider call is made and it is not wired into FEAT-018 runtime or a public mobile contract.
- Current integration branch for these drafts: `codex/pixi-ai-show-20261001`.
- Next gates: project-owner per-frame visual and rights review; only then can approved entries populate AI candidates. A later live model/renderer integration needs a separate provider/contract review and must not mutate FEAT-018 frozen versions.
- Scope guard: do not modify the FEAT-026 untracked SRS artifact; do not change FEAT-018 frozen contracts, source artwork, or provider/privacy boundaries without the required review.
- Validation: 16 selector tests, Ruff, and mypy pass. Catalog loader verifies 144 descriptors, 24 atlas hashes, and frame bounds. Repository harness/security scans remain globally invalid only because of pre-existing untracked FEAT-026 paths and its external SRS PDF; that user-owned folder was preserved unchanged.
