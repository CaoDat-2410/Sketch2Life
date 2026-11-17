# Feature decisions

Plan revision 1 is approved (see `approvals/TASK_APPROVAL.md`). These decisions govern implementation within its scope.

## Proposed for approval with plan revision 1

- Preserve user-approved asset licensing/runtime review gates. No generated asset is made eligible automatically.
- Decouple a valid source-subject show from optional companion-asset selection. Keep V1/V2 unchanged, put empty companion selection in additive versions, and do not relax rights/readiness filters. ADR-0013 records the accepted contract decision.
- Do not silently downgrade to PIXI_V2 or claim success when an essential show/rig step fails. Keep an actionable typed error and the original artwork available.
- Preserve explicit, user-initiated provider retries only; no automatic retry and no live provider requests by Codex.
- Implement the existing Firebase Authentication decision at the backend boundary; do not add Firebase-hosted storage/database or put AI credentials/endpoints in the app.
- Treat container/resource layout, lockfile ownership, storage/Compose cleanup, and large binary deduplication as decision-gated. Do not remove files/dependencies or select a storage stack as a side effect.

## Decisions/gates still requiring evidence or an ADR during implementation

- Supported image formats and measured normalization/memory limits for the pinned Expo SDK and backend decoder.
- Firebase verifier configuration/test strategy for local emulator vs. deployed runtime; secrets remain owner-managed.
- Canonical workspace lockfile and treatment of unused infrastructure dependencies after checking current repository decisions.
- Whether duplicate source/generated/approved/applied media can be deduplicated without breaking provenance or human review.

All remaining architecture decisions stay gated; approval of this plan does not authorize secret provisioning, external calls, asset promotion, or deployment.

## Commit/push authorization — 2026-10-05

The owner subsequently instructed: “sửa hết lỗi đi, sau đó thì push lên”. This authorizes committing
the validated work and pushing the current branch. It does not authorize provider calls, secret
provisioning, release signing with an unapproved key, asset-rights promotion, or deployment.

## Approval-integrity reconciliation — 2026-10-05

The owner explicitly approved continuation with “approve”. The parent plan file was not edited;
the approval record records its SHA-256
`DCA28C79763AF55C6CC083CD500F19655EEB760D4206928E8334DEE5DEE94A1E`. Work continues within
parent plan revision 1 and retains provider, credential, asset-rights, and deployment gates.

## Subject-linked local sprite preview — 2026-10-05

Under approved mobile runtime plan revision 4, the local walker cycle must share the source
subject's root/show translation and be placed beside (not over) the original drawing. Keep the
cycle capability, production rights gates, source preservation, and local-only preview boundary
unchanged. This is a renderer composition fix; it is not new artwork approval.

The owner has separately authorized validated commit/push (see the authorization above). Provider,
secret, asset-rights, and deployment gates remain closed.

## Runtime performance and Android inset — 2026-10-05

The approved revision-4 emulator follow-up records two additional measured corrections: Android
15+ receives its system status-bar inset before app content, and Home no longer runs its purely
decorative infinite particle/CTA loops. Keep story/Pixi playback motion intact. On the installed
debug preview, an 8-second idle Home interval produced zero rendered frames and zero janky frames.
These changes do not remove functional navigation or playback controls.
