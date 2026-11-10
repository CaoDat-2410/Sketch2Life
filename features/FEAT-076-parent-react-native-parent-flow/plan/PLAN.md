# FEAT-076 Plan Rev1 — Native React Native Parent demo flow

- State: PLANNED pending hash-specific approval record.
- Date: 2026-11-10.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Requirement authority: FEAT-063 system architecture SRS v2.7-draft Rev57 (unsigned working baseline), using the Parent flow requirements already traced in FEAT-075.
- Implementation target: apps/mobile, existing Android-only React Native + TypeScript application.

## Objective

Deliver a runnable native React Native version of the current Parent story-to-video demo flow. Keep the existing ParentWorkflowPort boundary and local demo adapter; do not connect APIs or real device/media/provider services.

## Scope

1. Bring the native Parent journey into SRS order: sign-in/profile selection, drawing and idea, upload/transcript, subject/context review, story review, explicit video preflight/admission, P07 status/READY, playback, post-video activity and history.
2. Repair the P06 to P07 path so “Tạo video ngay” admits the synthetic request, closes preflight, and shows P07; quota rejection keeps the user at preflight. Prevent repeat admission from charging the same run twice. Playback remains gated on READY.
3. Add a native child-profile gender choice and matching boy/girl avatar; let a parent change profile with one tap. Preserve the one-active-run gate and keep the run's child identity consistent.
4. Bring quota and settings screens in line with the recent Parent UI direction: playful but readable child-friendly presentation, grouped account/settings and privacy/security entries, with payment and auth clearly marked as demo-only.
5. Keep no-preset activity behavior undecided; show only the configured pinned lesson fixture and do not add fallback activities.
6. Produce a local Android debug APK if the configured Android build environment supports it. Do not publish, sign a release artifact, commit, push, or deploy.

## Acceptance criteria

- AC1: The synthetic Parent journey can be entered from the mobile app and follows the screen sequence above without API/backend calls.
- AC2: Final script approval is explicit; preflight reports the selected child, story revision, and quota outcome.
- AC3: Successful admission routes to P07 and spends at most one demo quota unit per accepted request; no quota leaves the user on preflight with an explanation.
- AC4: P07 exposes a clear synthetic processing/READY transition without fabricated percentage; playback cannot open before READY.
- AC5: Post-video activity is reachable only after ready playback and remains tied to the pinned lesson fixture; no-preset policy stays open.
- AC6: Profile selection and creation show gender-matched avatars; selecting a profile is a single tap and cannot create a second active run or change an existing run's child.
- AC7: Quota and grouped settings are understandable at phone width and remain usable at tablet width; controls have accessible labels/state and touch targets.
- AC8: A debug APK is produced when Android SDK/Gradle prerequisites are available; report any environment blocker and exact artifact path.
- AC9: Feature context, decisions, approval, status and evidence are updated; unrelated worktree changes remain untouched.

## Exclusions and constraints

- No API, backend, auth provider, persistence, payment, real camera/gallery/microphone, upload, AI/video provider, or storage integration.
- No change to the canonical SRS, contracts, policy, billing, or open questions.
- No external/generated visual assets. Use React Native primitives and existing dependencies.
- Do not modify the web implementation or the separate Fixture lab.
- No release build, signing, commit, push, deployment, or publication.
