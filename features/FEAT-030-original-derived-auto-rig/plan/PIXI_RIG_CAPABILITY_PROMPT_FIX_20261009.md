# Pixi rig-capability prompt and diagnostics fix

- Feature: FEAT-030 original-derived auto-rig
- Revision: 1
- Status: APPROVED — implemented locally; runtime retest pending
- Date: 2026-10-09
- Owner request: fix the screenshot where `/v4/pixi/show-plan` returned HTTP 200 but the app reported that the verified mask does not support the selected movement.
- Parent approval: `PIXI_ADAPTIVE_ART_AND_TOPIC_SCENE_20261008.md`, revision 1.

## Finding

The V4 prompt currently lists every render strategy and motion action for every rig tier. The deterministic compiler rejects articulated actions unless the matching verified part role exists and the package is `FULL_AUTO_RIG`. It also permits only `STATIC_SOURCE` for `BBOX_VISUAL_FOCUS`, while the prompt groups that tier with incomplete cutouts and suggests cutout strategies. The resulting invalid plan is correctly rejected after the planner endpoint returns 200.

## Scope

- Derive an explicit planner capability whitelist from `rigTier`, validated `partRoles`, and eligible environment candidates already present in the single planner request.
- For full rigs, allow articulated actions only when their required role is verified; for subject-only cutouts, allow only whole-subject actions; for bbox focus, allow only static-source actions.
- Restrict render strategies to those accepted by the existing backend compiler and renderer for the supplied tier. A topic-scene strategy is offered only when an eligible environment candidate exists.
- Keep deterministic backend validation authoritative and fail closed if the model still violates the whitelist.
- Add fixed, sanitized compiler diagnostic reasons for capability rejections. Do not log image, prompt, child/session identifiers, planner output, labels, or asset metadata.

## Acceptance criteria

1. The V4 prompt includes capability-specific source actions and render strategies derived from the request's rig tier and part roles.
2. It does not offer articulated movement without the corresponding verified part role, cutout movement to bbox-only rigs, or topic scenes without an eligible environment candidate.
3. Existing schema, tier, role, topic, and asset validators remain authoritative; no planner output is clamped, rewritten, retried, or replaced.
4. Capability rejection logs contain only a fixed reason code and retain the existing public workflow error.
5. The single-inference boundary and all contracts remain unchanged.

## Verification

- Run Python source compilation for the touched backend modules and `git diff --check`.
- Do not run tests or make a live Lightning/provider request from this workstation.
- Runtime acceptance requires deploying the backend and Lightning prompt change, restarting the services as applicable, and retrying with synthetic artwork.

## Boundaries and risks

- This is a prompt/diagnostic correction within the already approved adaptive-art strategy. It does not weaken mask validation or authorize unsupported articulation.
- If no strategy and source action are supported by the validated tier, the workflow remains fail-closed with a sanitized reason; no automatic substitute show is introduced.
- No contract, model, dependency, provider activation, asset-rights, or production-runtime changes are included.

## Implementation status — 2026-10-09

- Implemented the tier/role/strategy capability whitelist in the existing single V4 planner prompt and compiler.
- Added sanitized compiler rejection reason logs. Python compilation and `git diff --check` passed; tests and live inference were not run.
- Runtime acceptance remains pending deployment and synthetic-artwork retry.
