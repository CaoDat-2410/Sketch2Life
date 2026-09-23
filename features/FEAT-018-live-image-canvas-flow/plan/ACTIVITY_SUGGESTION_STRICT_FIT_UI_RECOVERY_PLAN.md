# FEAT-018 Activity suggestion strict-fit and UI recovery plan

Status: `IMPLEMENTED — VERIFIED WITH UNRELATED HARNESS FINDING`

Feature: `FEAT-018-live-image-canvas-flow`

Branch: `codex/feat-018-contract-plan`

Date: 2026-09-22

## 1. Confirmed owner decisions

The owner confirmed all of the following before this plan was written:

1. The repair may cover both the backend activity resolver and the BaoVC React Native UI.
2. If the highest-ranked activity candidate fails the existing strict fit/continuity gate, the
   backend should evaluate the next reviewed candidate and return the first fully eligible result.
3. After an activity has been prepared successfully, a repeated tap or navigation back to the
   recommendation screen should reopen the existing result instead of starting the P1 chain again.

The owner approved this exact plan on 2026-09-22. Implementation is authorized within the scope and
acceptance criteria below.

## 2. Evidence-backed diagnosis

The Android request reached every P1 route. Access logs alone were misleading because the workflow
uses HTTP 200 for typed `BLOCKED` envelopes. A read-only session check showed that the session
remained at `CANDIDATES_READY`, and a deterministic replay of `PREPARE_EXPERIENCE` returned:

```text
status: BLOCKED
candidate: ACT-0029 v1 / TPL-ACT-0029-V1
fit status: REJECT
drawing relevance: 0
total score: 50 (threshold 80)
reason codes: ANCHOR_TEMPLATE_MISMATCH, FIT_BELOW_THRESHOLD
```

No Lightning, ASR, model, video, or credit-consuming call was made during this diagnosis.

The failure has two independent parts:

- Candidate discovery currently accepts a loose token-overlap score. For a butterfly anchor with
  semantic text such as `động vật` and `chuyển động`, generic tokens including `vật` and `chuyển`
  can make the unrelated activity `Chuyển vật bằng kẹp` appear as a direct P1 option.
- Experience compilation correctly applies the stricter continuity gate and rejects that same
  option because the complete confirmed anchor does not match the activity template. Therefore an
  option exposed by `read_p1_context_options` is not guaranteed to be compilable by
  `prepare_experience`.

The UI then hides the useful reason codes behind the generic message `Không tạo được
ExperienceSpec`, clears the previous recommendation before a replacement succeeds, and uses React
state alone as an in-flight guard. Two taps before the state update can still start duplicate
chains.

## 3. Desired invariant

For one Gate-A-confirmed anchor and adult context:

```text
reviewed candidates
    -> deterministic rank
    -> hard context eligibility
    -> strict anchor/objective continuity
    -> fit threshold
    -> first PASS candidate only
    -> P1ContextOption
    -> P1 filter
    -> ExperienceSpec
    -> Gate B
```

Every option returned as selectable must be capable of producing an ExperienceSpec under the same
anchor, age, readiness, prerequisite, material, supervision, policy, and semantic evidence. A
candidate that fails strict fit must not be exposed as a successful recommendation. The existing
strict Gate B policy must not be weakened.

## 4. Scope

### In scope

- FEAT-018 supervised activity option resolution, strict candidate viability, and deterministic
  next-candidate fallback.
- Existing reviewed exact, alias, semantic-family, and age-baseline candidate sources.
- BaoVC activity recommendation request locking, state preservation, repeat navigation, and typed
  error presentation.
- Focused backend unit/contract tests, frontend deterministic tests or extracted pure-helper tests,
  TypeScript validation, feature-local evidence, and Android Emulator owner smoke instructions.
- Process-local demo state and the existing future auth/persistence seam.

### Out of scope

- Changing FEAT-003 Vision/ASR contracts, Qwen prompts, Lightning deployment, or image admission.
- Relaxing strict P1 continuity, reducing the fit threshold, or allowing high scores to override a
  hard mismatch.
- LLM-generated activities, mobile-side eligibility decisions, mock activity handoff, or silent
  fallback to `MOCK_ACTIVITIES`.
- Video, durable storage, Firebase databases/storage, auth implementation, real child data, or
  provider credentials in mobile.
- Codex-triggered Lightning/model requests.

## 5. Contract strategy

No public contract widening is planned.

- Keep `P1ContextOptionsV1`, `P1ContextV1`, `P1FilterResultV1`, `ExperienceSpecV1`,
  `MobileWorkflowResultV1`, and Gate B unchanged.
- Keep recommendation provenance in the existing additive workflow payload metadata.
- Reuse the existing closed reason codes. If one new application-only reason is necessary, it must
  be finite, sanitized, documented, and carried only in the generic workflow payload; it must not
  silently alter a frozen V1 schema.
- The backend remains the only owner of activity ranking, eligibility, strict fit, and fallback.
- The UI consumes the selected identity and closed diagnostics; it never computes compatibility.

## 6. Detailed implementation plan

### Phase A — Make candidate discovery agree with strict compilation

1. Add a pure application-level candidate viability path that evaluates each ranked candidate with
   the same hard context rules, anchor/objective continuity, semantic evidence, and fit threshold
   used by `P1ExperienceCompiler.compile`.
2. Build the ranked pool from reviewed sources only:
   - exact reviewed phrase;
   - reviewed alias/concept-family match;
   - reviewed age-baseline fallback after personalized candidates are exhausted.
3. Remove the current assumption that any positive token-overlap direct option is safe to expose.
   Token overlap may help gather candidates, but it cannot by itself mark an option viable.
4. Evaluate candidates deterministically. If the first candidate is rejected, retain its closed
   reason codes for diagnostics and continue to the next candidate. Return the first PASS candidate.
5. Ensure recommendation metadata describes the candidate actually returned, including match mode,
   profile/version, score, fallback reason, and selected activity identity.
6. If every reviewed candidate fails, return a typed no-result/blocked outcome with bounded reason
   codes. Do not return an unrelated option merely to keep the demo moving.

### Phase B — Preserve one identity through P1 and ExperienceSpec

1. Make `read_p1_context_options` and `run_p1_filter` use the same resolved candidate/evidence
   decision rather than independently re-running different loose/strict branches.
2. Persist the selected semantic evidence needed by `prepare_experience`; never lose it between the
   read-only option response and P1 filter.
3. Re-evaluate the exact selected candidate at `prepare_experience` as defense in depth. A stale or
   tampered identity still blocks.
4. Preserve exact activity/template/objective versions from option response through P1 filter,
   ExperienceSpec, Gate B, renderer launch, handoff, and feedback.
5. Keep HTTP/envelope semantics compatible. Tests and UI must inspect `MobileWorkflowResultV1.status`
   rather than treating HTTP 200 as workflow success.

### Phase C — Make the UI request atomic and recoverable

1. Add a synchronous `useRef` lock around `prepareActivityWorkflow` so two taps cannot enter before
   `workflowBusy` re-renders.
2. Permit a new P1 chain only from the local `UNDERSTANDING_PROPOSED` state with Gate A confirmed.
3. If the activity is already prepared (`GATE_B_PENDING`, `EXPERIENCE_READY`, or later) and the
   selected backend activity/context are still available, return the existing result immediately
   and navigate to activity detail without any API request.
4. Do not clear `contextOptions`, `selectedBackendActivity`, `activityRecommendation`, or the current
   activity before a replacement chain succeeds. Keep the last valid result on failure.
5. Update the recommendation CTA by state:
   - before request: `Tạo gợi ý thật`;
   - in flight: `Đang lọc hoạt động...` and disabled;
   - result available: `Xem hoạt động đã tạo`;
   - blocked: retain the confirmed topic and show an actionable retry/correction path.
6. Keep the backend activity identity as the only reachable detail/handoff content. Do not fall back
   to the initialized mock activity after an error.

### Phase D — Surface the real failure safely

1. Extend mobile result interpretation for closed P1/Experience reason codes, including
   `ANCHOR_TEMPLATE_MISMATCH`, `FIT_BELOW_THRESHOLD`, `NO_ELIGIBLE_ACTIVITY`, stale version, and
   Gate-A/session-state failures.
2. Prefer a concise Vietnamese message such as `Catalog chưa có hoạt động vượt qua kiểm tra phù hợp
   với chủ đề đã xác nhận` over the internal term `ExperienceSpec`.
3. Keep a developer-safe diagnostic suffix or structured state for testing, but do not expose raw
   exceptions, provider output, prompts, credentials, media bytes, absolute paths, or child data.
4. Treat `status=BLOCKED` as a handled workflow result, not a network error. Keep retryability and
   suggested action explicit.

### Phase E — Verification

1. Backend unit regressions:
   - a butterfly/`chuyển động` anchor must not expose `ACT-0029` solely from token overlap;
   - first candidate strict-fit rejection proceeds to the next reviewed PASS candidate;
   - semantic evidence used during option selection survives into compile;
   - all candidates rejected returns typed no-result without ExperienceSpec;
   - exact and reviewed alias matches remain preferred over age-baseline fallback.
2. Backend HTTP contract regression:
   - Gate A -> options -> P1 context -> filter -> prepare reaches `GATE_B_PENDING`;
   - the option identity equals the P1 filter and ExperienceSpec identity;
   - HTTP 200 plus `BLOCKED` remains correctly represented and reason codes stay bounded;
   - stale version, repeated idempotency key, and Gate-A requirement remain enforced.
3. Frontend regression:
   - two rapid CTA invocations produce one API chain;
   - failure does not erase an existing valid result;
   - returning to the recommendation screen opens the existing activity without API calls;
   - `BLOCKED` displays the mapped Vietnamese reason and never displays a mock activity;
   - success navigates exactly once to activity detail.
4. Run focused tests, the relevant full backend contract collection, Ruff, mypy on changed backend
   modules, mobile TypeScript, any available mobile unit tests, `git diff --check`, architecture
   validation, and `python tools/validate_repository_security.py`.
5. Record sanitized commands/results in this feature's `evidence/` directory. The owner performs the
   Android smoke with synthetic/non-child input. No Lightning call is needed for the P1/UI fix.

## 7. Expected files

Likely implementation files, subject to final code tracing:

- `backend/src/sketch2life/application/services/semantic_activity_resolver.py`
- `backend/src/sketch2life/application/services/supervised_flow.py`
- `backend/src/sketch2life/application/services/p1_experience.py` only if a reusable pure viability
  method is required; strict policy itself must remain unchanged
- `backend/tests/unit/test_topic_activity_matching.py`
- `backend/tests/unit/test_p1_experience.py` if the compiler seam changes
- `backend/tests/contract/test_live_image_demo_api.py`
- `apps/ui-mobile/src/context/AppContext.tsx`
- `apps/ui-mobile/src/screens/Flow2Screens.tsx`
- a focused mobile helper/test file if the current mobile harness supports it
- feature-local context, approval, decision, and evidence records

No `.env`, token, credential, real child data, external document, generated video, or unrelated
FEAT-026 file may be staged.

## 8. Acceptance criteria

1. No activity option presented to BaoVC may later fail ExperienceSpec creation under the unchanged
   anchor/context solely because discovery used a looser compatibility rule.
2. The observed butterfly/`ACT-0029` regression is covered and `ACT-0029` is rejected before it is
   presented as a recommendation.
3. When the first ranked candidate fails strict fit, the next reviewed eligible candidate is used;
   exact/alias matches outrank age fallback.
4. If no candidate passes, the system remains before Gate B with a typed, actionable no-result and
   no mock activity.
5. A successful suggestion reaches `GATE_B_PENDING` and preserves exact activity/template/objective
   identity through ExperienceSpec.
6. Rapid repeated taps cause exactly one backend chain.
7. Returning to the recommendation screen after success reopens the existing result without another
   P1 request.
8. A failed replacement attempt does not erase a previously valid activity.
9. The UI does not show raw `ExperienceSpec` jargon for expected catalog-fit failures and does show
   a safe Vietnamese explanation derived from closed reason codes.
10. Existing Gate A, strict P1 continuity, age/safety/material/readiness/supervision rules, Gate B,
    Pixi source preservation, future auth/save seams, and versioned contracts remain intact.
11. Relevant tests and repository validators pass; evidence is feature-local and contains no
    sensitive data.

## 9. Approval gate

Before implementation:

1. Owner approves this plan in the conversation.
2. Record the approval and the plan SHA-256 in `approvals/TASK_APPROVAL.md`.
3. Change this plan status to `APPROVED — IMPLEMENTATION AUTHORIZED`.
4. Implement only the scope above, verify it, then mark the plan implemented and append evidence.

## 10. Implementation closure — 2026-09-22

The approved scope is implemented. Direct template options now pass the compiler's strict fit policy
before exposure, reviewed semantic candidates are evaluated in deterministic rank order with
next-candidate fallback, and the exact selected evidence/identity remains authoritative through P1
and ExperienceSpec. BaoVC now uses a synchronous request lock, preserves the last valid activity,
reopens an existing prepared result without another API chain, and maps bounded backend reasons to
safe Vietnamese guidance.

The butterfly regression is covered end to end: `ACT-0029` is not exposed from generic token
overlap; the reviewed age fallback reaches `GATE_B_PENDING` with matching option/spec identity.
Focused tests, the full backend collection, Ruff, mypy, mobile TypeScript, architecture validation,
repository security validation, and diff checks passed. The repository harness validator reports
only pre-existing/unrelated missing FEAT-026 `evidence/raw` and `evidence/metrics` directories; this
implementation did not modify FEAT-026. See
`evidence/notes/ACTIVITY_SUGGESTION_STRICT_FIT_UI_RECOVERY_IMPLEMENTATION_20260922.md`.
