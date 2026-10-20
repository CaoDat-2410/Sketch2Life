# C5a — sole CMD-48 policy transport / consumer handoff

2026-10-18 Asia/Saigon, branch feature/be2-08-14 parent0ecff26. Previous goal turn
made concrete progress/commit. Re-read original pasted goal, clean branch/HEAD,
AGENTS/project context/source register, current feature context, pinned approved
revision1 plan and C3c stop plan. Later actual BE2-14 approval governs this card;
original BE2-12 goal not redefined or declared achieved. C5 subplan before code.

## Stop-delivery audit and implemented transport

Foundation CancellationNotice matches OR session/job_type/subject, not original
policy pin/epoch. Delayed stop after new activation could cancel new jobs. No
trusted feature-to-job mapping exists here. Proposed explicit owner adoption CR:
artifacts/CR_KILL_NOTICE_PIN_FENCE.md. No published foundation change, broad notice
creation, delivered_at update or actual cancellation claim. Continue other approved
local work rather than fabricate missing owner semantics.

bind_ai_policy(actual AiPolicyCommands) returns existing StrictDelegateBinding with
strict frozen AiPolicyCommand. Existing GovernanceDispatcher.ai_policy receives
this binding; sole HTTP factory now projects PolicyError through closed own map.
Known auth403/notfound404/precondition400/428/validation422/conflict409/dependency503
codes only. Unknown/internal scope/definition/time errors generic503, no arbitrary
message leak. Existing raw exception handling stays safe500. No route duplication,
new shared payload/action, default app mount, auth fallback or actual adapter.

## Verification

- 51 new actual-service HTTP cases PASS with MEMORY store and ASSUMED registry/
  rights: all8 actions plus exact replay, unknown/cross-org denial, revoked replay,
  stale revision, four malformed payloads before effects, thirty error mapping
  cases, inline OpenAPI/no duplicate routes/unbound branch, unauthenticated denial,
  private exception filtering and two shared precondition checks. Actual command
  composition is not actual runtime authority/SQL/provider integration.
- Initial run46 PASS/1 FAIL: test incorrectly treated valid inline schema title
  AiPolicyWrite as an unresolved reference. Inspected OpenAPI, corrected assertion
  to prohibit $ref instead; production schema unchanged. Then added auth/private-
  exception/precondition cases; final focused HTTP/dispatcher110 PASS.
- Own946 unit/contract PASS, zero fail/error/skip:
  ignored .runtime/be2-14-c5a/component.xml, 21 known warnings as previous C4c7.
- Source-pinned selected regression477 PASS:
  .runtime/learning-content-component/20261017-175857-782965.
- Targeted foundation114 PASS, .runtime/be2-14-c5a/foundation.xml.
- Focused Ruff4 Python files, Mypy3 sources, architecture/harness/security/diff
  checks PASS before commit. Existing router formatting outside changed seam
  preserved. No new migration or SQL tests; existing99 SQL cases remain NOT_RUN.

## Consumer composition (no default activation)

Use the existing factory, supplying verified server identity/adopted ports:

```python
policy = AiPolicyCommands(policy_store, policy_command_boundary)
dispatcher = GovernanceDispatcher(
    content_commands,
    ai_policy=bind_ai_policy(policy),
    preset=adopted_preset_binding,
    core_policy=adopted_core_binding,
)
router = build_governance_commands_router(
    dispatcher, verified_identity_resolver, max_body_bytes=approved_admission_limit,
)
```

All names denote explicit injected dependencies, not defaults provided here.
Unbound delegates stay unavailable; don't infer AI-policy permission from content
rights. Non-create sends strong quoted If-Match; create omits it. Body uses
record_kind=policy/policy_kind=ai and existing eight-action strict contract.
Responses retain existing correlation envelope/no-store/ETag. Known policy error
codes are safe closed metadata, not raw dependency error text. Registry/owner
authority must remain fenced through commit; fixture guards do not prove adoption.

Next C5 safe operational projections/C6 conformance/review; real stop-generation
contract and SQL/provider/current-owner integration external gates. Batch PG pack
preconditions/commands/artifacts stay in artifacts/C2_SQL_RUNTIME.md; no user test
needed piecemeal now. No goal/full-card DONE, live service, push/merge/deploy.
