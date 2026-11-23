# FEAT-081 — Plan Revision 35: LMFE Parent activity decoder performance

- **Status:** APPROVED under the owner's continuing direct instruction on 2026-11-20 to keep fixing the real Parent workflow until it works.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>
- **Product authority:** FEAT-063 current working SRS. No user-facing business rule is changed by this runtime optimization.
- **Relationship:** performance follow-up to Plan Revision 34. Its sole remaining live activity attempt is reserved for verification after this fix.

## 1. Goal

Keep Qwen3.5 JSON-constrained generation responsive without removing JSON grammar constraints or weakening final activity validation.

## 2. Evidence and cause

- Revision 34's UI call `fc-01M7V6NPS2G9298TK1W0EZ554R` passed the text-only model input contract, loaded Qwen3.5-9B on an NVIDIA A10 with no CPU/disk offload, and began real generation.
- Generation produced 100 tokens, then was cancelled at about 195 seconds to limit GPU use. Safe worker progress showed 0 tokens at 15/30s, 97 at 45s, 98 at 90s, 99 at 150/165/180s and 100 at 195s.
- LMFE callback telemetry recorded two callbacks at generated tokens 98–99 taking 50.341s and 50.818s, each allowing roughly 246,500 tokens. GPU/model load and the filtered processor input are therefore no longer the primary bottleneck.
- The activity decoder schema expresses sentence punctuation using bounded regular-expression `pattern` fields. In the pinned LMFE 0.11.3 implementation, its JSON free-text shortcut applies only when the active string parser has no regex parser. Regex-constrained prose therefore falls through the expensive tokenizer-prefix traversal.
- Existing `_parse_parent_activity_suggestions` already checks field lengths, required text and ending punctuation after generation. This is the authoritative fail-closed gate for accepting an activity result.

## 3. Implementation and acceptance criteria

### M1 — use fast free-text schema constraints

- In the generation schema only, replace the activity prose `pattern` constraints with equivalent `minLength`/`maxLength` string bounds. Preserve fixed enums and the candidate reference pattern.
- Keep sentence-ending punctuation as a mandatory post-generation check in `_parse_parent_activity_suggestions`; add/update regression tests proving malformed punctuation and out-of-range strings are still rejected.
- Keep the exact JSON object/array/property/enum schema, prompt, output token cap, age band, catalog-first selection rules, safety checks, quality gates and model revision. Do not return unvalidated output.
- Add a focused parser test proving the bounded activity prose string enters LMFE's JSON free-text fast path, plus tests for each affected field's bounds and post-parse punctuation gate.

### M2 — offline validation and deploy

- Run Python compilation and focused worker/activity workload tests.
- Redeploy only the language/audio Modal app, run CPU decoder readiness without a GPU/model load, and verify API health and the existing Parent activity retry screen.

### M3 — final bounded activity verification

- Use the one remaining activity attempt authorized by Revision 34: exactly one real Android UI-driven request, maximum eight minutes. Do not call Modal worker directly.
- Stop immediately on success or failure. No same-build retries. No more activity calls under this amendment.
- On success, proceed under the already approved Rev25/Rev33 limits: select/persist one activity, make one story request and adult review/confirmation, and at most one silent video request only if all gates pass.
- Synthetic-only; no drawing inference, new account/profile, fixtures/mocks, direct DB mutation, quota/payment modification or bypass, secret/`.env` changes, migration, commit/push, or unrelated shutdown. Keep emulator online and clean up only task-owned services after evidence capture.

