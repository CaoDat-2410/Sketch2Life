# ADR-030-08: Versioned AI-authored Pixi show planning

- Status: ACCEPTED — implementation authorized by owner approval of FEAT-030 plan revision 4
- Date: 2026-10-01 (Asia/Saigon)
- Branch: `codex/pixi-ai-show-20261001`
- Approval record: `approvals/TASK_APPROVAL.md` (exact pre-approval plan hash recorded there)

## Context

The current renderer accepts FEAT-018 `PixiRendererLaunchV1` and FEAT-030
`PixiRendererLaunchV2`. The current V2 preparation path can fail and silently leave V1 as the
launch, which conceals Pixi preparation failures and animates a different plan than intended.
V2 animation plans are deterministic and do not carry supplemental sprite references or story
beats. FEAT-028 has 144 owner-visually-approved frames, but its catalog still marks rights as
`REVIEW_REQUIRED` and runtime eligibility false. Separately, the current image-processing part
splitter uses nearest-anchor assignment and a fixed confidence, which is not anatomical evidence.

The owner approved one bounded post-Gate-B multimodal planner call, distinct companion sprites,
visual beats only (voice/captions deferred), advisory image subject classification with caregiver
reconfirmation on conflict, and visible typed errors without automatic retry or substitute shows.
The source artwork, Gate A subject decision, Gate B activity, and Montessori objective stay
authoritative.

## Decision

1. Keep FEAT-018 V1/V2 launch and animation schemas unchanged. Add an FEAT-030 versioned Pixi-show
   contract/sidecar and a new renderer envelope that composes the existing V2 launch with the
   validated show plan and capability-bound sprite reads.
2. Add a provider-neutral application port. The initial development adapter uses the already
   configured Lightning/Qwen service; it makes at most one multimodal request after Gate B, never
   from mobile/Pixi, with a minimized server-created source crop where available. No new provider
   or checkpoint is added. The live planner stays disabled unless explicitly configured and remains
   gated on privacy/retention, contract, latency/VRAM, and Android evidence.
3. Build a deterministic approved-only sprite shortlist before inference. Runtime resolution requires
   visual approval, `runtimeEligible=true`, and `licenseStatus=CLEARED`; model output can refer only
   to supplied asset IDs. Because current entries are not rights-cleared, production composition
   remains unavailable until FEAT-028 records the separate rights decision.
4. Parse/validate model intent against a closed schema, Gate A/B identity, subject ontology,
   behavior/action capability, asset allowlists, duration/beat/placement limits, and provenance.
   Compile it through deterministic action templates; never evaluate model code or arbitrary URLs.
5. When the V2 show path fails, return a sanitized typed failure and retain/show the exact original.
   Do not silently return V1, deterministic substitute animation, or automatic retry. A later retry
   may happen only after an explicit user action.
6. Keep SAM2.1 as the preferred part source. Treat image-processing splits as proposals only;
   remove constant confidence, preserve parent-mask containment/provenance, and permit articulation
   only when held-out evidence thresholds pass.

## Consequences

- Old clients remain compatible because existing contracts are untouched; only the new mobile
  client understands the additive envelope.
- Current catalog rights state intentionally yields no eligible production sprite IDs. Unit and
  renderer tests use synthetic fixtures; no asset is promoted by this ADR.
- A planner/model error is visible and source-preserving, but it does not keep the Pixi show moving.
- A Gate-A visual subject disagreement requires caregiver confirmation before playback and cannot
  rewrite session meaning.
- Existing atlas styles may not harmonize with every drawing; the composition path must retain the
  drawing as the lead layer and enforce measured asset/style budgets.

## Verification required before live activation

- Strict backend and TypeScript schema parity; malformed/unknown IDs/actions and subject conflicts
  fail closed.
- Synthetic mask evaluation with frozen thresholds, parent containment and role/detail metrics.
- Repository security validation; no child images, image bytes, provider output, secrets, or raw
  prompts in logs/evidence.
- Rights-cleared FEAT-028 frame review, privacy/retention review for the multimodal request, L4
  latency/VRAM measurements, and fresh Android visual acceptance.
