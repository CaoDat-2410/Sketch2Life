# Offline entity path review and next diagnostic proposal

## Completed read-only review and CPU check

- After the owner asked what comes next, the assistant inspected the current server prompt, entity normalization and existing source tests. No Modal command, HTTP request, GPU call, installation, runtime/prompt/profile/contract edit, or protected approval/receipt change was performed.
- `tools/lightning_vision_v2_server.py` permits up to five entities, prioritizes the central visible subject, and ends with a one-entity example. That example could influence output shape/count but this review does not establish a causal prompt defect.
- The server serializes its full typed result, not a selected top entity. `vision_payload_normalizer.py` processes multiple entity records without a top-1 cap or confidence cutoff. It may discard malformed/missing-text records, and canonical entity keys take precedence over aliases rather than merging every possible list. Thus the single observed output does not distinguish a model omission from normalization of a malformed response.
- A local, in-memory Python check sent two valid synthetic entity records through `normalize_provider_payload(..., enable_structural_repair=True)`, then validated them with the actual `EntityCandidateV1` schema and asserted both IDs remained. Output: `OFFLINE_NORMALIZER_TWO_VALID_ENTITIES_PRESERVED`, `model_calls=0; input_entities=2; output_entities=2`. This check passed without editing code or persisting synthetic predictions. It establishes preservation for that valid input shape only, not the unknown shape of the prior raw model response.
- The single remote response's raw body was not saved; do not claim that its missing second entity was caused by the model, prompt or mapper, and do not reconstruct nonexistent output from aggregate counts.

## Proposed next bounded diagnostic — not executed

- Prepare local synthetic controls: house only, sun only, and house plus sun. Preserve the existing house/sun fixture and receipts; any new source must receive an actual image-admission result before it is sent.
- Keep the current model/revision/profile, decoding, prompt, content policy and runtime unchanged so this diagnostic does not silently become prompt tuning. Do not use old FEAT-003 held-out quality fixtures or alter their scoring/ground truth.
- Proposed live scope, after the owner chooses to proceed: one request per image, at most three model requests; stop on a typed failure or invalid identity/config/attempt, with no automatic probe retry. The owner starts/stops the temporary serving session. Do not launch it as part of preparing this proposal.
- Compare observed typed labels transiently against the visible subjects. Persist only sanitized identity/count/status metadata and bounded comparison flags, not raw model or predicted text. A failure on a single-subject control and an omission only in the combined image suggest different directions for further diagnosis; neither alone proves a prompt cause or guarantees mapper correctness for malformed inputs.
- No new fixtures/admission receipts, live calls, quality score, or production-readiness conclusion is claimed by this proposal. If prompt/profile/mapping changes are later desired, prepare a separately scoped proposal and preserve the original approved plan and approval bytes.
