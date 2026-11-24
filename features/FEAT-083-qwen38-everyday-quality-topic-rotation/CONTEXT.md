# FEAT-083 — Qwen3.8 quality and Parent topic rotation

## Goal

Make all active Qwen-backed Sketch2Life workloads use the pinned Qwen3.8-27B-FP8 model, improve the specificity and everyday relevance of Parent activities/stories/video prompts, and replace the seven-topic Parent picker with an 18-topic curated catalog that does not repeat cards for an adult until that rotation cycle is exhausted.

## Authority and boundaries

- Current product authority: the FEAT-063 canonical SRS v2.7-draft file, now recorded through Rev75; it remains unsigned. Rev75 records the legacy Teacher FLUX lesson-visual source removal only. Earlier owner-provided repository instructions named Rev67; that historical discrepancy does not change the current pointer.
- Use Qwen3.8 for active Qwen text and vision workloads. Whisper remains ASR, VieNeu remains TTS, and LTX-2.5 remains video generation; those are separate model jobs, not Qwen substitutions.
- Keep Parent image-first flow, lesson pin, adult subject/activity/script confirmation, age and safety restrictions, and existing video admission/safety gates.
- Do not turn a custom topic into AI-invented subject cards. Resolve known catalog topics to their own rotating subject cards; for an unknown topic, ask the adult to enter the object and use Qwen3.8 only to validate topic/object consistency.
- Rotation history is scoped to the authenticated adult account, is server-side and idempotent across drafts/devices, stores only internal account/draft/request IDs, catalog IDs/revision/cycle and timestamps, and never stores child profile, artwork, voice, story, or custom topic text.
- No secrets, seed accounts, real child data, or Modal credentials may enter this feature.

## Current findings

- Baseline findings before the approved FEAT-083 changes: the topic list was smaller and draft-local, subject cards could repeat across drafts, custom topics could use an AI-generated card fallback, drawing used an older Qwen checkpoint, and activity/story/video wording allowed generic or underdeveloped content.
- Source changes now add an 18-topic Vietnamese catalog with nine drawable subjects per topic and account-scoped durable three-card topic/subject cycles. Replays use persisted request receipts. Unknown topics request an adult-entered subject and do not dispatch an AI subject-card generator.
- Source pins active Qwen text and vision paths to the shared Qwen3.8-27B-FP8 revision. Activity/story prompts and structural/semantic checks now ask for concrete everyday actions and story progression; the LTX prompt version was advanced to preserve approved drawing/story entities. These are source changes only, not live quality evidence.

## Completion state

See `status/STATUS.md`. Source changes are applied within the approved scope, but tests/typecheck, migration execution, Modal deployment/inference, API/E2E, and emulator verification remain not run under the approved runtime limits. Scope is bounded by the Rev1 plan and Rev2–Rev5 amendments. Rev5 removes the legacy Teacher `/lesson-visuals` FLUX API and its UI caller; the SVG illustration API remains unimplemented.
