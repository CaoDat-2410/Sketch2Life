# FEAT-020 Decision Addendum

## D-020-08 — Gate actor

**Status:** confirmed
**Decision:** use `DEMO_OPERATOR` for explicit unattended Gate A, Gate B, and demo feedback records.

## D-020-09 — Deferred video generation

**Status:** confirmed for first demo
**Decision:** create and validate the learning/video context contract, but do not call a video-generation model in the first E2E. Return `VIDEO_DEFERRED` and complete the connected backend context/handoff path.

## D-020-10 — Static PixiJS asset catalog

**Status:** confirmed for FEAT-020
**Decision:** build hand-authored SVG assets and a versioned catalog now. Do not load PixiJS or implement playback. Runtime playback must not generate missing assets with AI; catalog miss and whole-drawing fallback are explicit outcomes.

## D-020-11 — Story-video scope amendment

**Date:** 2026-09-28
**Status:** owner-confirmed product target; implementation not approved by this record
**Decision:** expand the story video to 40–60 seconds; allow illustration redraw as a provenance-linked derivative; use age/readiness context and reviewed educational evidence; retain the current Wan2.2 TI2V-5B profile; create TTS narration separately from silent video rendering.

## D-020-12 — Script revision and pre-image approval

**Date:** 2026-09-28
**Status:** owner-confirmed product target; logical contracts remain proposed
**Decision:** provide both quick edit controls and free-form instructions. A successful edit returns a complete new immutable script revision. An adult must approve the exact current script packet before any image-generation request. Adult can select a supported language and voice category.

## D-020-13 — Documentation boundary

**Date:** 2026-09-28
**Status:** owner authorized documentation update
**Decision:** this request authorizes the two planning documents and master-SRS update only. It does not approve runtime implementation, frontend/UI code, provider execution, model downloads, contract migration, cloud changes, or deployment. New contract definitions are `PROPOSED_UNADOPTED` pending reconciliation/approval.

## D-020-14 — Bird-label normalization and topic priority

**Date:** 2026-09-29
**Status:** proposed; awaiting owner approval through the FEAT-018 cross-boundary plan
**Decision:** evaluate exact reviewed bird aliases and a whole-animal topic priority in the shared topic producer. Preserve claim provenance, do not fuzzy-infer a bird, and retain the existing one-pass VLM/API contract. See FEAT-018 `plan/BIRD_SUBJECT_TOPIC_RECALL_FIX_PLAN_20260929.md`.

## D-020-15 — Child-profile inputs to Montessori ranking

**Date:** 2026-09-29
**Status:** accepted through the approved FEAT-018/020/030 integrated plan (2026-09-29)
**Decision:** audit profile/catalog coverage and design an explicit, adult-editable, versioned
child-context handoff to the deterministic resolver. Apply safety/readiness/material constraints
before preference ranking; distinguish scene relevance from personal preference; never infer
psychology from artwork or equate activity completion with mastery. The approved session-only
contract/resolver path is implemented in part; no catalog expansion or durable persistence is in
scope. Future storage requires explicit privacy/authorization review and a separate ADR. See FEAT-018
`plan/INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_PLAN_20260929.md` and
`docs/adr/ADR-0010-session-scoped-child-learning-context.md`.
