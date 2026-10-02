# FEAT-020 Plan A — Content, Story, Age Personalization, and Script Approval

- **Revision:** 2026-09-28, owner-requested scope expansion
- **Plan status:** `DRAFT_FOR_REVIEW`
- **Implementation status:** `NOT_AUTHORIZED_BY_THIS_DOCUMENT`
- **Contract status:** every new contract below is `PROPOSED_UNADOPTED` until cross-feature review and explicit approval.
- **Related plan:** `VIDEO_STORY_PRODUCTION_PLAN.md`
- **Product baseline:** target age 0–12; current Gate A/Gate B and `ExperienceSpecV1` semantics remain authoritative.

## 1. Purpose and outcome

Replace the current single-prompt story preparation with a reviewable content workflow. The system first understands the source drawing and the child’s narration, then uses the adult-confirmed meaning, selected activity/objective, age/readiness context, and reviewed educational sources to create a script. The adult can revise it with quick controls, free-form instructions, or both. No illustration/image-generation request is allowed until the adult approves the exact script revision and its language/audience/knowledge basis.

This plan is inspired by the separation of director/scene planning in `storyboard-ai` and the typed scene, per-scene narration, and audio-duration timing in `chalkboard`. It proposes patterns only; it does not authorize copying or importing either repository’s implementation.

## 2. Confirmed requirements and proposal boundary

| Decision | State | Requirement |
|---|---|---|
| Video content | `OWNER_CONFIRMED_2026-09-28` | Story video is a short-form experience of about 40–60 seconds. |
| Illustration | `OWNER_CONFIRMED_2026-09-28` | Derived scenes may redraw the child’s subject in an illustration style. |
| Story purpose | `OWNER_CONFIRMED_2026-09-28` | Retell the child’s picture and add age-appropriate knowledge about the depicted subject. |
| Age adaptation | `OWNER_CONFIRMED_2026-09-28` | Knowledge retrieval and script complexity must use the child’s age/Montessori-relevant context. |
| Script editing | `OWNER_CONFIRMED_2026-09-28` | Provide both quick-edit controls and free-form adult instructions. |
| Approval boundary | `OWNER_CONFIRMED_2026-09-28` | AI returns a revised complete script; the adult finalizes it before image generation starts. |
| Voice/language | `OWNER_CONFIRMED_2026-09-28` | Let the adult select language and voice category, with a selector experience similar to translation voice selection. |
| Original source | `OWNER_CONFIRMED_FROM_PRIOR_SRS` | The original drawing/audio remain immutable source artifacts; any redraw is a separately identified derivative. |
| Defaults below | `PROPOSED_UNADOPTED` | Draft scene count, quick-action list, voice dimensions, retry policy, and logical schemas are proposals pending review. |

## 3. Scope

These plans define end-to-end product behavior and backend contracts. FEAT-020 remains a backend workflow feature and does not authorize mobile, Parent Web, or Guide Console code. Screen interactions are specified here for the separate UI feature plan; that feature must consume the same versioned contracts and receive its own scope/approval.

### Included

- Reuse the already validated image/narration admission and provenance flow.
- Build story context only from adult-confirmed `SemanticAnchorSetV1`, selected activity/objective, and the exact approved `ExperienceSpecV1`.
- Reuse the existing age-band policy and activity eligibility rules. The catalog’s current bands are 0–3, 3–6, 6–9, and 9–12 years; per-activity readiness, prerequisite, material, supervision, and safety rules remain authoritative.
- Query a reviewed knowledge source using subject, objective, age band/readiness, locale, and optional adult-selected focus.
- Preserve claim-level source evidence so each educational fact in the script is traceable.
- Produce a complete script draft with segment/scene narration, claim references, age rationale, target duration, and uncertainty warnings.
- Support quick controls and free-form revision instructions, separately or together in one edit command.
- Keep every script revision immutable; show the complete revised script and a human-readable change summary.
- Select output language and TTS voice profile; allow a short voice sample preview before final approval.
- Bind adult approval to exact script, evidence, language, audience, and voice configuration versions.
- Expose clear recovery when knowledge evidence is insufficient, the selected language has no voice, or script constraints cannot be satisfied.

### Excluded

- Automatically inferring the child’s exact age, readiness, identity, emotion, ability, or development from the image/audio.
- Treating VLM labels or child narration as verified scientific facts without adult confirmation and an approved knowledge source.
- Letting an LLM create an untraceable educational claim or silently alter an approved claim during rewrite/translation.
- Generating scene images, video, or full narration from an unapproved script revision.
- Replacing the original drawing/audio with generated assets.
- Publishing new runtime schemas, changing existing contracts, choosing a final knowledge provider, or implementing UI/backend code in this documentation task.

## 4. Preconditions and source-of-truth rules

1. Image admission passed and the immutable source reference/hash are available.
2. Understanding proposal passed schema/policy validation.
3. Gate A has an adult-confirmed meaning and the exact confirmed anchor IDs are recorded.
4. Montessori/P1 filtering has an eligible activity; Gate B has approved the exact activity/objective/template versions; `ExperienceSpecV1` is compiled and hashed.
5. A child audience profile is read from the authorized ChildProfile context or explicitly selected/confirmed by the adult. Do not ask for date of birth if an approved age band is sufficient. No age is inferred from media.
6. Knowledge retrieval returns reviewed, age-applicable evidence. A missing/ambiguous species or low-confidence visual identification produces a clarification choice or a general, safely phrased subject; it must not assert a species as fact.
7. Output locale and script language are selected before the first draft. Voice profile can be selected during review and is included in final approval when it changes pronunciation/locale/rendering.

Authority order for content: immutable source media → adult-confirmed anchors/claims → Gate B approved `ExperienceSpecV1` → reviewed knowledge evidence → generated script proposal → adult-approved script. Model output alone never advances an adult gate.

## 5. Target user flow

| Step | Actor/system | Input | Output / gate |
|---|---|---|---|
| A0. Understanding ready | Backend | Admitted source image and optional child narration/transcript | Understanding proposal with observations, ambiguity, modality conflict, provenance. |
| A1. Confirm meaning | Parent/Guide | Understanding proposal | Gate A decision and immutable confirmed anchors. |
| A2. Choose activity | Parent/Guide | Existing age/readiness/material context and eligible candidates | Gate B decision, objective/template refs, `ExperienceSpecV1`. |
| A3. Set audience/language | Adult, with backend-provided current profile | Child age band/readiness and desired output locale | Versioned audience/language context; changes invalidate downstream draft. |
| A4. Retrieve knowledge | Backend | Confirmed subject/anchor, objective, age/readiness, locale, adult-selected focus | Claim-level evidence set with source/version/applicability and unsupported topics excluded. |
| A5. Create draft | Story planner | Exact source/anchor/spec/profile/evidence refs | `StoryScriptDraftV1`, initially not approved. |
| A6. Review/edit | Adult + story planner | Quick actions, free-form instruction, or both | New complete immutable revision plus changed-field summary and validation report. |
| A7. Choose narration | Adult | Locale, available voice list, style/pace category; sample preview | Versioned voice selection. A preview is not a final narration asset and does not trigger image generation. |
| A8. Finalize script | Adult | Exact latest script, knowledge evidence, age profile, locale, voice settings | `ScriptApprovalV1` bound to hashes/revisions. Approval is required before any image-generation request. |
| A9. Handoff | Backend | Approved script packet | Publish `ApprovedStoryPackageV1` to Plan B; video generation may start. |

Gate A and Gate B remain as they are. Script approval is a separate human review gate and does not substitute for either gate.

## 6. Proposed contract set

All names/shapes in this section are logical proposals, not canonical runtime contracts. JSON examples are illustrative; timestamps are RFC 3339 UTC, hashes are SHA-256 hex, and all refs are immutable `id + version` references.

### 6.1 `LearningAudienceProfileV1`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `contract` | const string | yes | `LearningAudienceProfileV1` |
| `profile_id`, `version` | string, positive integer | yes | Immutable profile revision. |
| `child_profile_ref` | `VersionedRefV1` | yes | Backend-authorized ChildProfile; no client-supplied age is trusted without authorization. |
| `age_band` | `AGE_0_3 \| AGE_3_6 \| AGE_6_9 \| AGE_9_12` | yes | Reuse current catalog band boundaries; do not invent different ranges here. |
| `age_band_source` | enum | yes | `CHILD_PROFILE \| ADULT_CONFIRMED_OVERRIDE`; never `MODEL_INFERRED`. |
| `readiness_ref` | optional `VersionedRefV1` | no | Existing P1 readiness/context record; exact readiness fields remain governed by P1. |
| `language_locale` | BCP-47 string | yes | Controls query/script locale, not the source language of the child’s audio. |
| `selected_by` | adult actor ref | yes | Parent/Guide permission checked server-side. |
| `profile_hash`, `created_at` | SHA-256, timestamp | yes | Approval and cache identity inputs. |

### 6.2 `LearningKnowledgeQueryV1` and `LearningEvidenceSetV1`

`LearningKnowledgeQueryV1` requires `query_id`, `session_id`, `expected_session_version`, `idempotency_key`, `confirmed_anchor_refs[]`, `experience_spec_ref + hash`, `activity/objective refs + versions`, `audience_profile_ref + hash`, `locale`, optional `adult_focus`, `source_policy_id + version`, `created_at`.

`LearningEvidenceSetV1` requires `evidence_set_id + version`, query hash, source-policy version, `status` (`SUFFICIENT | NEEDS_CLARIFICATION | NO_REVIEWED_EVIDENCE`), ordered claims, retrieval provenance, creation time, and aggregate warnings. Each `LearningClaimV1` requires:

- stable `claim_id` and version;
- child-facing statement and optional adult-facing explanation;
- topic/concept key, applicability age-band/readiness refs, locale;
- one or more source citations (`source_id`, source version/revision, exact section/page/URL or dataset record ID, retrieval timestamp, source type and review status);
- link to confirmed anchor/objective refs and intended script segment(s);
- `review_status` (`APPROVED_SOURCE`, `REVIEW_REQUIRED`, `REJECTED`), `claim_kind` (`OBSERVED_FROM_IMAGE`, `EDUCATIONAL_FACT`, `SAFE_NARRATIVE_BRIDGE`), and any qualification/caveat.

Invariants: only `APPROVED_SOURCE` evidence can be rendered as an educational fact; image observation and external fact stay distinct; translated/rephrased claims preserve `claim_id` and citation; no claim may target an out-of-band audience; source text is not copied beyond permitted quotation limits; no unsupported species-specific anatomy/behavior is stated when identity is uncertain. A knowledge source without traceable revision/citation cannot satisfy `SUFFICIENT`.

### 6.3 `StoryDraftRequestV1` and `StoryScriptDraftV1`

`StoryDraftRequestV1` contains:

```json
{
  "contract": "StoryDraftRequestV1",
  "request_id": "uuid",
  "idempotency_key": "opaque-stable-key",
  "session_id": "uuid",
  "expected_session_version": 0,
  "source_image_ref": {"artifact_id": "...", "version": 1, "sha256": "..."},
  "scene_understanding_ref": {"id": "...", "version": 1},
  "confirmed_anchor_set_ref": {"id": "...", "version": 1},
  "experience_spec_ref": {"id": "...", "version": 1, "sha256": "..."},
  "evidence_set_ref": {"id": "...", "version": 1},
  "audience_profile_ref": {"id": "...", "version": 1},
  "locale": "vi-VN",
  "target_duration_seconds": {"min": 40, "max": 60},
  "requested_focus": null
}
```

`StoryScriptDraftV1` requires `draft_id`, monotonic `revision`, `status=PROPOSED`, source/understanding/Gate A/Gate B/ExperienceSpec/evidence/audience refs and hashes, `locale`, `target_duration_seconds`, `estimated_spoken_duration_seconds`, `segments[]`, `story_arc`, `claim_coverage[]`, `content_validation`, warnings, model/planner provenance, `created_at`, and `script_hash`.

Each segment has `segment_id`, order, narrative purpose, complete child-facing narration text, referenced anchor IDs, educational claim IDs, `visual_intent_summary` (description only; not yet an image prompt/artifact), approximate timing hint, transition intent, and safety/uncertainty note. Segment count is intentionally not hard-coded in this plan; the companion video plan proposes an initial default for review.

### 6.4 `ScriptEditCommandV1` and revision result

`ScriptEditCommandV1` requires `command_id`, session/version, `draft_id + expected_revision`, idempotency key, adult actor, `quick_actions[]`, optional `freeform_instruction`, optional selected segment IDs, and `created_at`. Quick actions are a versioned catalog, initially proposed as `SIMPLER_LANGUAGE`, `MORE_DETAIL`, `SHORTER`, `LONGER_WITHIN_LIMIT`, `FOCUS_ON_SUBJECT_PART`, `ADD_EVIDENCE_BACKED_FACT`, `REMOVE_SEGMENT`, `CHANGE_TONE`, and `REORDER_SEGMENTS`. Parameters are typed; action IDs unknown to the active catalog are rejected.

The command must allow quick actions and non-empty free-form text together. The planner returns a **complete new** `StoryScriptDraftV1` revision, never a partial patch presented as the final script. Result includes `supersedes_revision`, `change_summary`, changed segment IDs, `validation_report`, preserved/removed/added claim IDs, and explicit unresolved issues. The adult sees the whole replacement script. Prior revisions remain immutable and auditable.

Revision rules: stale expected revision → `STALE_DRAFT`; invalid combination → `EDIT_CONFLICT`; fact removed/altered without evidence → `CLAIM_GROUNDING_FAILED`; too short/long or not age-compliant → `SCRIPT_CONSTRAINT_FAILED`; retryable model failure → `PLANNER_RETRYABLE_FAILURE`. Failed edits do not modify the active revision.

### 6.5 `NarrationProfileV1`, preview, and approval

`NarrationProfileV1` requires `profile_id + version`, `locale`, provider-neutral `voice_id`, display name, supported language list, voice category (provider capability mapped to stable product labels), style category, pace, optional pronunciation dictionary ref/version, provider/model provenance held backend-side, and catalog timestamp. Proposed product categories: voice presentation/category, warm/storytelling/neutral delivery, and slow/normal pace. Exact list, age-safe review, gender labels, providers, and availability are `OPEN_TBD`; do not promise unsupported languages or voices.

Voice preview request/result binds profile/version and sample locale; stores no child media and does not call image/video generation. Full TTS output is created only from an approved script package. Selection change that changes locale or spoken text invalidates approval; a voice-only change requires a new approval acknowledgment if it changes the audible delivery, but must not cause a script rewrite.

`ScriptApprovalV1` requires approval ID, session ID/version, adult actor, decision `APPROVED`, exact draft ID/revision/script hash, evidence-set ID/hash, anchor/spec/audience refs+hashes, locale, narration-profile ref+hash, content-validation version/result, accepted warnings, timestamp, and idempotency key. Approval is valid only for this exact tuple. Any edit, source/anchor/spec/age/evidence/locale change makes it `STALE`; no generation port accepts a stale approval.

## 7. Validation and safety rules

- Validate all generated language for age band and selected locale; preserve correct uncertainty language and avoid speaking to the child as if the system knows their private traits.
- Each educational fact in narration must link to one or more approved claim IDs and citations. Story bridges can be imaginative but must not masquerade as observed facts or factual biology.
- Run a deterministic schema/invariant validator plus policy/content review. A model self-critique alone cannot return `PASS`.
- If the drawing’s subject is uncertain, keep the script generic or ask an adult to choose/correct it at Gate A. Never query a species-specific fact set from an unconfirmed species.
- No diagnosis, psychological/personality/ability inference, unsafe instruction, or unsupervised activity is permitted.
- Word/speech duration is estimated before approval and measured from actual TTS after approval. If actual narration cannot fit 40–60 seconds, return to script review; never silently truncate approved narration.
- Script approval is independent of video validation and Gate A/Gate B. A video can be generated only from `APPROVED` and current references.

## 8. Logical service/API boundary (proposal)

These are capability names, not adopted endpoint paths:

1. `readAudienceProfile(session_id)` — authorization-scoped current age/readiness/language context.
2. `queryLearningEvidence(LearningKnowledgeQueryV1)` — reviewed-source retrieval; returns `LearningEvidenceSetV1`.
3. `createStoryDraft(StoryDraftRequestV1)` — idempotent async or sync proposal, with explicit `PROPOSED` status.
4. `reviseStoryDraft(ScriptEditCommandV1)` — creates a new revision and never overwrites old revisions.
5. `listNarrationProfiles(locale)` / `previewNarrationVoice(...)` — server-owned catalog and bounded synthetic voice sample.
6. `approveStoryScript(ScriptApprovalV1)` — adult permission, expected session version, idempotency and exact-hash checks.
7. `getStoryPackage(session_id, revision)` — returns only the approved package to the video application service.

Every request carries a correlation ID, request/idempotency key, `session_id`, `expected_session_version`, actor context verified by backend, contract name/version and bounded payload. Client-provided role, child ID, activity eligibility, or source hash is never trusted without server lookup. Raw prompts/model dumps/provider headers are excluded from normal API responses and telemetry.

## 9. State model, stale input, and recovery

```text
EVIDENCE_PENDING → EVIDENCE_READY | NEEDS_CLARIFICATION | NO_REVIEWED_EVIDENCE
        ↓
SCRIPT_DRAFTED → SCRIPT_REVIEW → SCRIPT_REVISED* → VOICE_SELECTED → SCRIPT_APPROVED
        ├── blocked: CONTENT_BLOCKED | AGE_CONTEXT_REQUIRED | GATE_A_REQUIRED | GATE_B_REQUIRED
        ├── recoverable: KNOWLEDGE_RETRYABLE | DRAFT_RETRYABLE | VOICE_UNAVAILABLE
        └── invalidated: SCRIPT_STALE (source/spec/audience/evidence/locale version changed)
```

`SCRIPT_APPROVED` is terminal for Plan A and an input precondition for Plan B. A changed input does not mutate the approved package; it creates a new proposal/revision and invalidates only not-yet-published downstream jobs by reference/hash. Existing published derivatives retain their provenance but are marked `STALE` and cannot be presented as current.

## 10. Acceptance criteria

| ID | Acceptance criterion |
|---|---|
| CE-AC-01 | Story creation requires adult-confirmed Gate A anchors and an approved Gate B `ExperienceSpecV1`; missing gates yield typed blocked status. |
| CE-AC-02 | Age/readiness comes from authorized profile/adult confirmation and uses existing P1/catalog bands and hard rules; AI never infers age/readiness from media. |
| CE-AC-03 | Knowledge query includes confirmed subject, selected objective, age/readiness, locale, and reviewed source policy. |
| CE-AC-04 | Every educational fact maps to a claim and versioned source citation; uncertain subject cannot produce species-specific claims. |
| CE-AC-05 | First draft records source hashes, anchor/spec/profile/evidence versions, locale, duration target, model provenance, and validation. |
| CE-AC-06 | Adult can revise with quick controls, free-form text, and a combined request; each successful edit returns a full new immutable script. |
| CE-AC-07 | Prior revisions remain readable; stale edit commands cannot overwrite a newer revision. |
| CE-AC-08 | Adult can select an available locale/voice category, hear a bounded preview, and see unsupported combinations clearly. |
| CE-AC-09 | Approval binds exact script/evidence/age/spec/locale/voice versions; any relevant change invalidates approval. |
| CE-AC-10 | No illustration or video image-generation request can be issued before valid approval; test through generation-port call history when implemented. |
| CE-AC-11 | The child’s original drawing/narration remains immutable; any later illustration is a provenance-linked derivative. |
| CE-AC-12 | Unsafe, ungrounded, age-inappropriate, out-of-duration, or schema-invalid script cannot become approved. |
| CE-AC-13 | Every failure has a typed code, retryability, and user-action guidance; failure is never represented as a successful draft/approval. |

## 11. Implementation work packages (future, separately gated)

| Order | Work package | Required output |
|---|---|---|
| C0 | Contract reconciliation | Owner-reviewed schemas, compatibility/migration plan, ADRs, exact profile/source ownership. |
| C1 | Audience/knowledge source | Age context resolver, reviewed corpus/source registry, claim provenance and retrieval audit. |
| C2 | Planner | Typed story-draft port/adapter, constrained prompt/model profile, deterministic validators. |
| C3 | Revision UX/API | Quick-action catalog + free-form command + immutable versioned draft history. |
| C4 | Voice selection | Voice catalog, locale capabilities, preview port, TTS profile provenance and unavailable behavior. |
| C5 | Adult approval | UI/API review, hash-bound approval command, invalidation and audit rules. |
| C6 | Integration | `ApprovedStoryPackageV1` handed to Plan B; no provider image call before approval. |
| C7 | Verification/governance | Synthetic-only evidence, privacy/security review, approved implementation task, feature status update. |

## 12. Dependencies and open decisions

Existing dependencies: `ConfirmedSceneUnderstandingV2`, Gate A/`SemanticAnchorSetV1`, P1 `P1ContextV1`, activity catalog age/readiness/safety, Gate B, `ExperienceSpecV1`, session version/idempotency semantics, immutable artifact refs, adult role authorization, current retention/consent policy.

Keep these `OPEN_TBD` until separately decided: authoritative knowledge corpus and reviewer roles; retrieval freshness/citation format; which Montessori/readiness dimensions are stored versus selected per session; exact quick-action catalogue/labels; exact voice providers, styles, gender/presentation labels and languages; subtitle/caption requirement; speech-rate bounds; whether script approval must be repeated after voice-only changes; script/model token/cost ceilings; knowledge-source license policy; response-time SLOs.

## 13. Source references

- `features/FEAT-020-backend-ai-workflow-demo/plan/AGE_VARIATION_POLICY.md`
- `features/FEAT-020-backend-ai-workflow-demo/plan/AGE_BAND_MATRIX.json`
- `features/FEAT-020-backend-ai-workflow-demo/plan/SEMANTIC_PERSONALIZATION_V2_REMEDIATION_PLAN.md`
- `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`
- `https://github.com/yogendra-yatnalkar/storyboard-ai` — conceptual director/global-plan and per-scene orchestration pattern.
- `https://github.com/Atharva-Kanherkar/chalkboard` — conceptual typed scene script, per-scene TTS, audio-led duration, provider boundary pattern.
