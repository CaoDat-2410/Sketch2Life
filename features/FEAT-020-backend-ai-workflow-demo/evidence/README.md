# FEAT-020 Evidence Index

Status: `VALIDATED`

All evidence for this feature must remain in this directory and must be sanitized.

Planned evidence files:

- `preflight.txt` — runtime/model/CUDA checks with secret values redacted;
- `workflow-run-summary.txt` — safe one-command progress and terminal result;
- `workflow-result.json` — sanitized versioned final manifest;
- `e2e-result.txt` — the single real-AI E2E test result;
- `validation-summary.txt` — security, harness, architecture, skeleton, unit, and E2E checks;
- `provenance-check.txt` — original-image immutability and identity continuity checks.
- `implementation/AI_FAILURE_PATCH.md` — sanitized Lightning failure diagnosis and patch validation.

Do not place raw image/audio files, raw prompts, full model outputs, credentials, tokens, or real child data here. Runtime media and large model artifacts must stay in ignored local/Lightning storage.

- implementation/SEMANTIC_PERSONALIZATION_V2_VALIDATION.md — V2 semantic workflow implementation and validation record.
- `notes/STORY_VIDEO_REQUIREMENTS_REVIEW_20260928.md` — owner-confirmed story/video scope amendment, two-plan split, repo pattern review, source-of-truth boundaries, and unresolved implementation decisions; documentation review only, no runtime evidence.
- FEAT-018 shared-producer diagnosis for bird topic omission is indexed under `../FEAT-018-live-image-canvas-flow/evidence/notes/BIRD_SUBJECT_TOPIC_RECALL_DIAGNOSIS_20260929.md`; the implementation plan is awaiting owner approval.
- FEAT-018's child-context audit is indexed under `../FEAT-018-live-image-canvas-flow/evidence/notes/CHILD_CONTEXT_MONTESSORI_AUDIT_20260929.md`; the integrated scope is approved and implementation evidence is indexed under `../FEAT-018-live-image-canvas-flow/evidence/notes/INTEGRATED_CHILD_PROFILE_AND_RIG_QUALITY_IMPLEMENTATION_20260929.md`.
- `notes/CHILD_PROFILE_REQUEST_SCOPED_IMPLEMENTATION_20260929.md` records FEAT-020's session-only API/resolver behavior, catalog coverage and focused verification; Android UI acceptance is cross-indexed to FEAT-018.
- `notes/STORY_VIDEO_REQUIREMENTS_REVIEW_20260928.md` — owner-confirmed story/video scope amendment, two-plan split, repo pattern review, source-of-truth boundaries, and unresolved implementation decisions; documentation review only, no runtime evidence.
