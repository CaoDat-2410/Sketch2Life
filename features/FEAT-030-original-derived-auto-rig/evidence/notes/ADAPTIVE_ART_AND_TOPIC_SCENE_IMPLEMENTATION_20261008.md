# Adaptive original-art rendering implementation — 2026-10-08

## Approved scope

Implemented under plan revision 1, approved against pre-approval SHA-256 `FC634C8899AB4B4FC618AF8311BDBD9C7391CC0C952C2F24AF60EC33D12428EF`. The plan file's current SHA-256 is `CD14106E7BC5B920C1A916D15DAC41F8B143A2ECAA714EB6C6844FE323BC3732`; its approval-gate metadata records the already-approved scope.

## Changes

- Added planner request/result schema V3 with a closed renderer-strategy enum, the authoritative selected topic, bounded candidate previews, and a separate allowlisted theme asset ID. The existing post-Gate-B call remains the only planner call.
- Added a deterministic adapter/compiler path that checks strategy against validated rig capability, selected topic, scene asset role, action support, and the existing scene budget. Invalid output remains a typed fail-closed outcome.
- Added ephemeral candidate preview generation from approved/applied, rights-cleared, runtime-eligible environment/prop/effect assets. Preview size and aggregate request size are bounded; preview bytes are never persisted or logged.
- Updated the existing worker endpoint to create one transient contact sheet containing the minimized source crop and candidate previews for the existing multimodal inference. Candidate IDs and confirmed Gate-A/Gate-B context remain explicit; no extra inference was added.
- Added additive renderer envelope V4 and command V6 while retaining older contracts. Pixi renders the theme behind the verified original-derived cutout and disables subject translation for static-source strategy.
- Preserved the existing mask safety thresholds and added a regression proving two individually valid but collectively incomplete part masks are rejected. Uniform same-color silhouettes continue to produce no fabricated anatomy.
- Existing topic-candidate checks reject incompatible style/role assets before the AI sees them. Added adapter checks that reject a hallucinated theme ID and surface planner timeout after one request without retry.

## Verification

- Focused backend suite across planner, candidate-style filtering, asset previews, worker, settings, auto-rig, and part-mask modules: 108 passed.
- Ruff on changed Python implementation/tests: passed.
- Renderer TypeScript check: passed; renderer Vitest: 67 passed.
- Mobile TypeScript check: passed.
- Full backend suite: one unrelated FEAT-020 semantic-personalization age-band fixture failure; five skipped. No changes were made to that separate policy/test.

## Gates still open

No live provider call, real child image, asset promotion, or production activation was performed. Fresh Android visual acceptance, FEAT-028 rights/runtime eligibility, privacy/retention review, L4 latency/VRAM evidence, and the applicable ADR/rollout decision remain pending. The feature tests use synthetic fixtures only and do not establish live model quality or visual acceptance.
