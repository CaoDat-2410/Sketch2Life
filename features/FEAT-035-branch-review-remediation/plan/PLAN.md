# Feature plan

- Status: APPROVED
- Plan revision: 1
- Implementation status: IN_PROGRESS

## Goal

Verify and close the material correctness, reliability, security, Android, deployment, and quality-gate findings in the review of `7a65890`, without weakening child-media, asset-rights, human-review, provider, or no-fallback rules. Deliver as one approved remediation program with ordered work packages and feature-local evidence.

## Scope

In scope: C-01; H-01 through H-06; M-01 through M-12; and L-01 through L-17 in the supplied review. Each item must be either fixed and verified, or explicitly dispositioned with evidence and an owner-approved follow-up/ADR. Findings labeled “report-only” in the verification ledger must be reproduced before code changes are attributed to them.

Recommended product/contract resolution for C-01 (approval required): decouple a valid subject-only Pixi show from optional catalog companions. A subject-only plan may carry no supplemental asset IDs only when every beat targets the confirmed source subject and the source rig supports the selected behavior. Any supplemental asset remains subject to the existing approved/applied + license-cleared + runtime-eligible filter, exact selection allowlist, and FEAT-028 provenance. A missing subject rig or invalid essential show remains a typed visible failure; do not silently switch to PIXI_V2 or claim the show succeeded. If this changes a versioned contract, add the new version and ADR before implementation. Do not mass-approve the 144 catalog records.

Also in scope: safe normalization for common large images while preserving the immutable original; correct Android microphone permission/build configuration; request/response failure contracts; session/idempotency/state isolation; Firebase-authenticated backend access consistent with ADR-0005; Android release baseline; deployable package resources; and reproducible CI/test gates.

Out of scope: live provider calls or credit use; real child media; SAM 3.x evaluation, model downloads, or fine-tuning; changing Runpod/Lightning production policy; Firebase-hosted media/database; secret provisioning or release-key creation; approving visual assets; deleting/deduplicating binary assets; and unrelated Montessori/catalog redesign. Those require their own human/data/ADR gates.

## Steps

1. **Freeze and reproduce the baseline.** Record target commit, clean/dirty state, dependency versions, exact commands, and a finding ledger. Re-run relevant offline probes and tests. Separate confirmed source behavior, reproduced runtime behavior, and report-only claims. Do not send inference requests.
2. **Restore Pixi's valid success path without weakening gates.** Decide and version the subject-only semantics above; validate every plan against Gate A subject, available rig capabilities, behavior registry, duration, source hash, and any referenced approved assets. An empty eligible-asset catalog must not invalidate a plan that has no supplemental-asset beats. Keep missing/invalid essential rig or plan as a typed error; no PIXI_V2 fallback. Make nonessential companion-frame loading independently recoverable only where the remaining validated plan is still complete. Normalize planner JSON safely and retain serialized GPU/model access.
3. **Repair subject and image intake.** Replace substring/diacritic-collision classification with stable confirmed subject/category IDs and explicit whole-token aliases. Ambiguous labels must not be falsely classified or silently rejected: require correction/confirmation or use only a behavior proven safe for the confirmed rig. Normalize supported photos before expensive decode using bounded dimensions/bytes, orientation-aware decode, and the existing canonical limits; preserve original bytes/hash/provenance. Return an actionable typed error for unsupported/corrupt formats.
4. **Repair backend concurrency and failure contracts.** Ensure synchronous file/decode/service work cannot block the ASGI loop. Use per-session/version fencing for state transitions and release state locks before network, GPU, or image work; retain a separate bounded semaphore for scarce GPU/model work. Normalize connection reset/disconnect/timeout for ASR and planner to stable JSON errors and accurate progress, with no automatic retry. Align client/server total deadlines and progress behavior; do not merely raise timeouts. Make reads atomic and stale results unable to overwrite a newer image/session version.
5. **Repair session/media lifecycle.** Validate session expiry before replaying idempotency receipts; expire/delete every session-scoped receipt. On retake/new image, atomically invalidate image-derived understanding, subject, mask, rig, Pixi plan, cache/job keys, and only the superseded image artifacts; preserve unrelated session/audio/audit data. Key jobs and derived outputs by source revision/hash, not session ID alone. Bound explicit user retries per source revision and keep them user initiated.
6. **Close Android and API security/release issues.** Wire Firebase ID-token verification through the existing provider-neutral backend identity boundary per ADR-0005; enforce authorization server-side, never trust UI role mode, and never expose provider credentials. Keep development networking explicitly scoped. Add microphone permission via the supported Expo config plugin and verify the generated/merged Android manifest; request it only when the adult starts recording and handle denial. Move release signing to injected secret-managed configuration (never a checked-in debug key) and align `apps/ui-mobile` SDK values with ADR-0004; update validators to inspect the actual app.
7. **Make container and local runtime reproducible.** Remove assumptions that repository-root `data/`, `features/`, or renderer files exist relative to `site-packages`. Define an explicit resource root/package-data or mounted read-only resource layout, then prove installed-wheel/container startup, catalog load, and `/renderer` availability. Correct the Android start helper's SDK discovery and reverse the required backend and Metro ports. Document/build the renderer demo artifact as a required step. Do not copy secrets or unreviewed source artwork into an image.
8. **Reconcile contracts, observability, and quality gates.** Fix request validation to typed 4xx responses; make configuration failures actionable but redacted; report live stage progress; remove dead/unreachable routes only after confirming their contracts; centralize behavior IDs; replace runtime `assert` checks with explicit errors. Wire mobile tests into the default test command and resolve the reported failure. Enable the Pydantic-aware mypy configuration, close all code-owned strict errors (including the reported delta), lint/format touched code, and add CI gates for security, harness, architecture, typecheck, backend/mobile/renderer tests, and Android config checks. Resolve missing feature harness paths without fabricating evidence. Inventory lockfile/Babel, unused dependencies/Compose, and duplicate asset issues; do not delete assets or remove infrastructure until their owners and architecture decisions are recorded.
9. **Review, run full gates, and record outcome.** Run synthetic fixture tests, backend concurrency/error tests, mobile tests, renderer tests, security/harness/architecture/skeleton validators, typecheck, installed-package/container smoke, and Android emulator smoke where configured. Capture evidence under this feature and owning feature folders. Review all findings as fixed, accepted, or separately approved/deferred; update owning feature status/context and ADRs. No push or deployment is part of this plan.

## Finding disposition map

| Finding | Proposed disposition |
|---|---|
| C-01 | Active blocker: restore a valid subject-only show path or document an explicit asset-review dependency; preserve rights checks and typed failure. |
| H-01, H-02 | Active: event-loop safety, short/per-session locks, version fencing, and bounded GPU serialization. |
| H-03 | Active: map transport disconnects to stable recoverable JSON; preserve no-auto-retry policy. |
| H-04 | Active: bounded pre-decode normalization; support common photos; keep original immutable and enforce backend limits. |
| H-05 | Active: correct Expo config/manifest and permission-denial flow. |
| H-06 | Active: exact semantic IDs/aliases and safe ambiguity handling; no false animal/object class. |
| M-01 | Active: expire all session receipts and reject replay after session expiry. |
| M-02 | Active with constraint: isolate optional decorations; never silently downgrade renderer or misreport show success. |
| M-03 | Active: align deadlines and progress; no unbounded wait or automatic retry. |
| M-04 | Active: robust fenced-JSON normalization and bounded serialized model scheduling; preserve GPU safety. |
| M-05 | Active: installed wheel/container must load explicit catalogs/resources and renderer. |
| M-06 | Active: verify actual error baseline, configure Pydantic mypy support, close code-owned errors and prevent regressions. |
| M-07 | Active: make the harness reproducible on a clean clone and align STATUS with committed evidence; do not fabricate evidence. |
| M-08 | Active: run `apps/ui-mobile` tests by default, declare the runner, fix failing coverage. |
| M-09 | Active security gate: implement Firebase token verification/authorization per ADR-0005; bind/configure development network deliberately. |
| M-10 | Active release gate: validate `apps/ui-mobile`, release signing, and ADR-0004 SDK baseline. |
| M-11 | Active: user-triggered retry budget is per image revision; retain no automatic retries. |
| M-12 | Active: retake invalidation and job/artifact identity use image revision/hash. |
| L-01 | Fix bounded ASCII integer/header validation and typed 4xx response. |
| L-02 | Audit dead branches; wire only if an approved contract requires them, otherwise remove only after callers/docs are checked. |
| L-03 | One canonical behavior registry with compatibility tests. |
| L-04 | Record dependency/Compose mismatch; defer removal or adoption until the storage/infra ADR is resolved. |
| L-05 | Lint/format touched code and establish a documented baseline; avoid unrelated mass formatting churn. |
| L-06 | Resolve root-vs-app lockfile and Babel major mismatch under the selected pnpm workspace; make frozen install deterministic. |
| L-07 | Use or remove unused timeout/settings, clarify total deadlines, and document placeholder-only environment configuration. |
| L-08 | Emit actionable configuration reason codes with secrets/paths/tokens redacted. |
| L-09 | Constant-time provider-token comparison. |
| L-10 | Produce exact duplicate/blob inventory and lifecycle storage recommendation; no asset deletion in this feature without separate owner review. |
| L-11 | Correct stale setup docs, renderer build prerequisite, SDK discovery, and backend/Metro reverse ports. |
| L-12 | Return one version-consistent immutable read snapshot. |
| L-13 | Catch schema validation before external calls and return typed 4xx, not 500. |
| L-14 | Replace production runtime asserts with explicit invariant failures. |
| L-15 | Reproduce environment gap; document/setup only declared dev dependencies, without committing local environment or secrets. |
| L-16 | Scope retake/hash-mismatch cleanup to superseded image-derived artifacts and preserve unrelated session data. |
| L-17 | Publish real stage transitions with request ID/version, bounded polling, and terminal states. |

## Acceptance criteria

1. Every report ID has a final evidence-backed disposition: fixed, accepted with rationale, or deferred to a named owner/ADR/task. No high/critical report-only item is labeled fixed without reproduction.
2. With zero approved companion assets, a synthetic image and valid Gate A/rig can produce a valid subject-only Pixi plan only when the plan contains no supplemental beats; any supplemental reference must be eligible, approved/applied, license-cleared, and in the candidate allowlist. Invalid essential show/rig returns a typed visible error; no silent PIXI_V2 fallback occurs.
3. Vietnamese regression fixtures include “cà rốt”, “hóa thạch”, “con gà”, “ô tô”, “chim”, and “bướm”; none receives a contradictory class from short substring collisions. Unknown/ambiguous cases cannot execute an incompatible behavior without adult confirmation.
4. 4032×3024 JPEG/PNG and other agreed synthetic fixture sizes follow a bounded normalization path before decode, with orientation verified, byte/pixel limits enforced, original hash unchanged, and typed errors for corrupt/unsupported content. Peak memory/time are recorded on the agreed emulator/backend environment.
5. A deliberately slow fake AI/ASR request does not block health or unrelated session requests; concurrent sessions do not hold a global state lock across provider/GPU/image work; scarce GPU work remains bounded. Tests prove stale results cannot overwrite a retaken image.
6. ASR connection reset, remote disconnect, timeout, malformed provider JSON, planner timeout, and missing optional sprite frames produce contract-compliant JSON/progress; no automatic provider retry or renderer downgrade occurs.
7. Expired sessions cannot replay successful idempotency receipts; expiry removes every session-scoped receipt. Retake invalidates image-derived state/cache without deleting unrelated audio/session records.
8. Unauthenticated/invalid Firebase identity requests are rejected; verified identity is mapped to backend authorization. No provider secret/endpoint is present in mobile build output or committed configuration. Android records audio only after permission is granted; denied permission is an actionable state.
9. `apps/ui-mobile` uses the agreed min/target/compile SDK and release builds cannot sign with the debug key. Generated/merged manifest and release configuration are inspected by automated checks.
10. Clean installed-package and Docker smoke loads activity/topic catalogs, starts the app, and serves renderer assets without repository-relative paths. No secrets or unreviewed media are baked into the image.
11. Default workspace test command executes renderer and mobile tests. Security, harness, architecture, skeleton, typecheck, and CI gates pass on a clean checkout; mypy baseline is zero code-owned strict errors or each remaining third-party issue is narrowly explained and blocked from runtime code.
12. Backend/API state reads and validation errors are version-consistent and typed; production assertions, unsafe header parsing, token comparison, misleading progress, and configuration-error swallowing are corrected or have an explicit accepted rationale.
13. Every test/benchmark/screenshot is stored in the owning feature's evidence tree, synthetic inputs only; statuses and ADRs match committed evidence. Asset rights are never bulk-cleared and duplicate assets are not deleted as part of this work.

## Risks and mitigations

- **Asset rights vs. feature availability:** the current 144 assets are not runtime eligible. Never “fix” this by editing approval/license fields. Use subject-only semantics for subject-only beats, and require human review for every companion asset.
- **Contract migration:** empty selected-asset semantics may be incompatible with PixiShow V1. Version the contract, add an ADR, keep old clients explicit, and gate migration on approval.
- **Concurrency refactor:** shorter locks can introduce stale writes/races. Use session versions/source revisions, cancellation-safe cleanup, deterministic concurrency tests, and bounded GPU semaphores.
- **Privacy/security scope:** Firebase auth requires project config not present in source. Unit-test the verifier boundary with synthetic tokens; do not add credentials. Device integration waits for owner-managed Firebase config.
- **Image memory:** supporting higher-megapixel images must not raise unbounded decode memory. Normalize under explicit compressed-byte, pixel, dimension, and time budgets and measure peak memory.
- **Scope size:** execute work packages in order within this single approved plan; stop at any architecture/asset/credential boundary not covered by approval and record a subdecision rather than silently expanding.
- **Local environment:** report-only test/mypy/CI claims need fresh reproduction; do not treat absence of a local tool/secret as a product-code defect.

## Verification plan

- Offline catalog/contract/compiler tests with synthetic fixtures; no provider calls.
- Backend unit/integration tests using fake blocked/failed adapters for race, timeout, ASR reset, stale versions, idempotency expiry, and exact error contracts.
- Intake property/boundary tests for encoded bytes, dimensions, rotation metadata, accepted formats, corrupt headers, and oversized pixel/edge cases.
- Android generated manifest, permission flow, release signing and SDK validator tests; emulator smoke using synthetic art.
- Installed wheel/Docker startup and renderer/catalog resource tests.
- `python tools/validate_repository_security.py`, `python tools/validate_harness.py`, `python tools/validate_architecture.py`, `python tools/validate_skeleton.py`, backend lint/mypy/tests, renderer tests, and mobile tests; validate from clean clone in CI.
- Before implementation, record exact baseline findings and versions. During implementation, attach raw outputs/metrics under this feature; attach cross-feature evidence to the feature that owns the behavior and link it here.

## Evidence plan

Current verification is summarized in `evidence/notes/priority-verification.md`. Acceptance evidence IDs and exact command/output paths will be added to `evidence/README.md` after approval. No live inference, real child data, screenshots of real children, or production credentials are allowed.

Implementation is blocked until `approvals/TASK_APPROVAL.md` says `APPROVED` for this plan revision.
