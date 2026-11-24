# FEAT-083 Plan Rev2 Amendment — durable rotation and current SRS reconciliation

**Date:** 2026-11-23
**Status:** APPROVED for implementation under the owner’s direct request in this conversation.
**Parent plan:** `PLAN_REV1_QWEN38_EVERYDAY_QUALITY_TOPIC_ROTATION_20261123.md`

## Why this amendment exists

The checked-in `docs/context/SRS_AUTHORITY.md` and canonical SRS currently say the local history reaches Rev73, while the owner-provided repository instructions say Rev67. Preserve the complete SRS history and reconcile the authority pointer to the checked-in canonical document; do not rewrite or remove Rev68–Rev73. Record the owner’s new requirements as Rev74, keep the SRS unsigned, and record this source discrepancy in FEAT-083.

Rev1 also needs to name the implementation adapters/contracts required for durable account-scoped rotation and the current OpenAPI description. This amendment supersedes Rev1 only for those files and for the SRS amendment number; other Rev1 scope and limits remain in force.

## Implementation decisions

1. **Qwen pin:** all active Qwen-backed Parent drawing, story/activity, lesson-text and SVG draft workloads use `Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81`. No automatic Qwen3.5 fallback. Whisper, VieNeu-TTS and LTX-2.5 remain their separate workloads. The FLUX candidate is not an active target and is not promoted by this change.
2. **Rotation:** maintain one server-side ordered cycle per authenticated adult account and catalog revision: one 18-topic sequence, and one nine-or-more-subject sequence per catalog topic. Each request returns the next three IDs. A cycle reshuffles only after its full list is consumed. Serialize allocation with a row lock and persist an idempotent request receipt; request replay returns the same card IDs without advancing the cursor.
3. **Privacy:** rotation rows contain only internal adult account UUID, suggestion kind/topic scope, catalog revision, ordered catalog IDs, cursor/cycle, request/draft UUIDs, opaque set ID and timestamps. Do not persist free text, profile, drawing, voice, story or model prompt/output.
4. **Catalog topic:** a typed topic matching a catalog title/alias resolves to that topic and its rotating subject cards.
5. **Custom topic:** an uncatalogued topic returns `CUSTOM_SUBJECT_REQUIRED` and zero generated subject cards. The adult enters an intended object; the existing generic Qwen validation workload returns ON_TOPIC/OUT_OF_TOPIC/NEEDS_CLARIFICATION. No custom text is sent to the generic subject-card suggestion workload or stored in rotation state.
6. **Retry identity:** topic and subject suggestion requests carry a client-generated UUID `request_id`; an identical retry replays the same response. A deliberate shuffle creates a new request ID.
7. **Quality:** replace marker-expanded Parent activity fallback with substantive structured Qwen output and moderate groundedness/completeness checks. Improve the story prompt for a causal, child-safe everyday-life arc, preserve the current story contract and adult review. Version the LTX compiler and constrain it to approved scene actions and source-drawing identity/props. Do not relax schema, privacy, age, safety, consent, script review, video admission or playback gates.

## Additional acceptance criteria

- **R2-AC1:** each adult sees all 18 topics once per topic cycle before any topic is repeated; each catalog topic’s subject cards rotate in groups of three without repeats until that topic’s subject cycle is exhausted.
- **R2-AC2:** concurrent requests for the same account allocate disjoint next batches; replaying one `request_id` returns its original response and does not advance the cycle.
- **R2-AC3:** unknown topics have no suggested cards and cannot proceed without an adult-entered subject that passes existing Qwen validation.
- **R2-AC4:** active Qwen provenance is the pinned Qwen3.8 ID/revision in worker output and backend checks; no Qwen3.5 fallback path is active.
- **R2-AC5:** catalog subject cards are stable, age-appropriate drawable concepts, with 18 Vietnamese topic groups and at least nine distinct subjects per group.
- **R2-AC6:** activity fallback contains three distinct, complete everyday activities with preparation/materials, 3–5 actionable steps, adult observation focus and relevant safety notes. The selection path remains catalog-first.
- **R2-AC7:** generated stories advance through a clear goal/action/change/resolution and use only confirmed subject/context/activity facts; the LTX prompt remains bounded by the approved story and drawing.
- **R2-AC8:** the canonical SRS is updated to Rev74, the model direction and rotation/custom-topic rules are recorded, the current SRS authority pointer is reconciled, the Data Table Register records new rotation tables, and all documents continue to state unsigned/not runtime-verified.

## Additional implementation file allowlist

- `docs/context/SRS_AUTHORITY.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`
- `backend/src/sketch2life/application/ports/parent_topic_rotation.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_topic_rotation_repository.py`
- `backend/src/sketch2life/resources/__init__.py`
- `backend/src/sketch2life/resources/parent_topic_catalog_vi_v2.py`
- `backend/src/sketch2life/interfaces/http/openapi_contract.py`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`

All other implementation paths remain as listed in Rev1. If source review reveals another required path, add a dated plan amendment before editing it.

## Runtime limits

Code and documentation only. No Modal deploy, model download, GPU inference, live database migration, emulator/E2E/API call, quality-gate bypass, quota/payment bypass, commit or push.
