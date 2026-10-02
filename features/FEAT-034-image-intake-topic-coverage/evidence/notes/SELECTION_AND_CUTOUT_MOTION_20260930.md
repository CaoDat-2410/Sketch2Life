# Non-first selection and cutout motion diagnosis/fix

Owner directly requested diagnosis/fix; approved scope is in `../../plan/RECOMMENDATION_SELECTION_PIXI_FOLLOWUP_20260930.md`.

## Measured causes

- Latest running package metadata: unknown archetype, CUTOUT_MICRO_MOTION, no parts, 20-second root track with maximum translation 0.012 stage units. Source/package/mask reads succeeded; this was not a verified full rig. No private source image or capability retained.
- Synthetic contract reproduction selected indices 0–3 from the actual loaded catalog. First passed; ACT-0106/0110/0118 failed with BLOCK_UNSUPPORTED_POLICY_CONSTRAINT. Discovery checked adult presence but not the same unsupported policies as final V4 admission.
- Cutout renderer intentionally applies only root translations, keeping camera/source scale/rotation fixed. Some full-rig plans (bird, flower, biped) authored only scale/rotation or child-bone tracks and thus showed no motion when delivered as cutout.

## Changes

- Shared V4 discovery eligibility function now applies to both listing and final selection, including age/caregiver/adult and fail-closed unsupported policy checks. No catalog constraint erased and no condition assumed satisfied. Actual eligible count may shrink (generic animals age 3–6 currently has one verified selectable family instead of four structurally matching families); restoring those conditional activities requires a supported confirmation source, not silent bypass.
- Giraffe coverage tests now verify caregiver presence below 36 months and compile every emitted option to its exact selected activity. Contract regression asserts known blocked cards never enter the selectable list.
- Cutout deliveries use a dedicated root-translation-only track for every archetype: two visible bounded movement beats, neutral by 14.4 seconds, hold to 20 seconds. No camera movement, scaling, rotation or invented anatomy. Explicit dog/cat/giraffe/rabbit labels map to existing generic-organic, not a new dog skeleton.
- Playback status distinguishes true independent-part motion from subject-only micro-motion. Dogs without independently validated head/body masks remain subject-only, not fully auto-rigged.

## Verification/deployment

136 focused backend tests passed; all 50 renderer tests passed including cutout movement with stationary background/scale/rotation and neutral final pose. Ruff, renderer TypeScript, renderer demo build, diff/security checks passed.

Local backend restarted to PID 53680; health returned 200. Served renderer page references the newly built mobile-BwzfYoVZ.js. Emulator remains connected and ADB reverse on 8081/8000 is intact. In-memory sessions reset; fresh user-flow validation remains pending. No remote provider calls, model deployment or new commit/push performed.

## Readiness/history boundary

Existing legacy engine contracts can use readiness/history, but the active owner-approved complete-discovery V4 flow intentionally omits readiness, material and completed-activity gates. Confirmed stable preferences still rank the list. Owner's question about missing readiness/history is informational; an optional question asks whether to restore them at the initial profile stage without a mid-flow checklist. No restoration implemented without that choice.
