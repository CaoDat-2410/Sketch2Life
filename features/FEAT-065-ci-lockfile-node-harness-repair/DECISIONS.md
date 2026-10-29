# FEAT-065 decisions

- 2026-10-29: Owner authorizes CI repair, focused validation and commit/push on existing feature/modal-vision-dev. No branch creation.
- Use Node 24.15.0 based on exact package-lock engine metadata. Preserve CI checks and locked installs.
- Refresh lock through resolver; retain existing compatible pins where possible. Never remove --locked or fabricate evidence to make CI green.
- New approval record applies only to FEAT-065 scope; all earlier approvals retain their meaning.

Record feature-local decisions here. Promote cross-feature decisions to `docs/adr/`.
