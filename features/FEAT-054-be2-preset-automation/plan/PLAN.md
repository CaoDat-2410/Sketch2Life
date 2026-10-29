# BE2-13 — Versioned presets, conditional automation and Teacher override

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date:2026-10-19 Asia/Saigon
- Branch: feature/be2-08-14
- Baseline: f821cc2
- Owner: receiver08–14; BE1 owns effective session/config mutation, P4 composition.

## 1. Goal and authority

Deliver reusable immutable preset versions, exact session pin references, bounded
conditional automation intents and authorized Teacher override/disable handoff.
Mandatory review/consent/safety remain independent gates; old automation must not
commit an effect after an effective override/config change invalidates its versions.

Sources: FEAT-040 TEAM_TASK_BREAKDOWN BE2-13; FEAT-044 BE2_ROADMAP/receiver handoff;
FEAT-029 Master SRS v3.1 FR052/053/054/shared056, UC-032/033, DATA-33/shared06/35,
CMD-48/shared12/59, FIX-GOV-01/P-NFR-16; existing12 governance dispatcher and
DATA-33 strict delegate contracts;01 job contracts and14 policy boundaries.

FR052 reuse/conditional automation/Teacher override CONFIRMED. FR053 field and
condition detail, FR054 priority/overload policy remain PROPOSED. Implement versioned
candidate contracts with explicit policy/adoption ports, not secretly adopted
thresholds, timer rules, priority weights, default automation or curriculum policy.
The owner request "task tiếp theo" authorizes inspect/plan, not unseen implementation.
Exact revision1 P1–P4 approval required before code; prior11 approval not inherited.

## 2. Scope and exclusions

Own preset domain/contracts/versioned publication delegate and repository, immutable
pin proposal/intent/outcome records, deterministic bounded condition evaluator,
explicit scheduler/command ports, override/disable reconciliation, own SQL adapter/
new frozen migration, injected existing CMD-48 binding and consolidated evidence.

No second CMD-48 router, direct BE1/session/content/policy DB writes or duplicate
session engine. No new primary CMD-12/59 endpoints. Preset publication is not a
learning_content DATA-24 review masquerade; concrete preset review semantics need
CR13-01 even when shared envelope requires PublicationReviewSet-shaped references.
No unlimited workflow builder, expression eval/imports/scripts, hidden scheduler/
worker, global provider/queue activation, package/model download, Lightning/cloud,
production mount/push/merge/deploy or automatic approval/completion/purge.
No UI assets and no current numeric policy adoption. Real SQL provisioning and
actual BE1/P4 wiring are separate approvals/gates, not prerequisites for local work.

## 3. Inspected dependencies / current gaps

BE2-12 GovernanceDispatcher has one preset slot; StrictDelegateBinding requires
strict frozen extra-forbid owner model, exact envelope/target/review references and
DelegateResult. Shared response/review shape does not supply preset capability or
real policy. All eight actions stay create/edit/submit_review/record_review/
request_changes/publish/recall/archive; non-create exact record revision/version/hash.

BE1 inspected runtime accepts a bounded generic session configuration dictionary
and owns session transitions. That is NOT an adopted atomic preset pin/override/
automation compare-and-apply/receipt port. Define explicit candidate contract and
faithful fake; do not claim existing generic dictionary already implements fences.
01 job and14 policy machinery are reusable boundaries, not approval of scheduler,
priority defaults, teaching permission or actual provider dispatch.

CR13-01: preset field/condition schema, review/publish/recall authority and rules.
CR13-02: BE1 current session/config/stage/automation epoch, exact pin/override/
disable/intent atomic comparison, actual command receipts/recovery/Teacher priority.
CR13-03: scheduler/workload/priority policy and actual BE1/P4/operations composition.
All OPEN_CANDIDATE; generic library IDs/fixture policies not actual adoption.

## 4. Implementation batch after approval

### P1 — Preset library and strict governance delegate

Typed immutable preset body for DATA-33 title/age/tool/canvas/assistance/stage/
notification/video/activity/assessment references and candidate bounded rules.
Topic/config completeness resolved under adopted owner policy, not invented defaults.
Explicit capability/current policy guards per action; immutable body versions,
hash/lineage/history/review references, CAS and scoped native idempotency receipts.
Edits stale prior review/publication as applicable; no active session mutation.
Reviewed exact publish; recall prevents new pins, active-copy disposition explicit.
Bind via existing12 StrictDelegateBinding only. If shared contract genuinely needs
change, record narrow compatibility refinement and tests, not duplicate endpoints
or weakening review/scope/validation to force a successful preset delegate.

### P2 — Pins, bounded evaluator and scoped automation intents

Immutable exact preset ref/body hash +BE1-confirmed effective config/session/stage/
automation versions; draft pin request distinct from accepted effective pin.
Finite typed condition/action registry under explicit approved policy. No arbitrary
JSON/script dispatch. Missing/unknown/stale policy/inputs fails closed with reason.
Evaluation creates scoped intent, never authorizes teaching effect. Check source
recall/current rights/purpose/consent/safety/review and exact audience/current state
before effect through owner ports. No child data copied into public configuration.
Explicit evaluate/enqueue/dispatch seams, no timer thread/scheduler activated.
Stable intent identity/body/version binding and durable decision/receipt history;
duplicate events cannot cause two effects with a conforming BE1 dedup consumer.
Queue deferral/overload visible with reason, no silent drop or automatic approval.
Priority only through injected adopted policy; unknown policy explicitly unavailable.

### P3 — Teacher override, durable recovery and own SQL

Authorized Teacher override/disable routed via BE1 command port, current authority/
expected session/config/stage/automation versions and immutable scoped command ID.
Persist own intent before external effect; BE1 atomically compares versions, applies
allowed config and records native idempotent receipt. Only verified matching receipt
allows own confirmed/effective status; timeout/unknown commit remains pending and
recovery queries/replays original identity, never invents rollback or duplicate edit.
Teacher precedence must hold at BE1 effect boundary, not only local queue cancellation.
Reconcile old queued intents to stale/cancelled with reason; already sent or uncertain
ones remain traceable pending reconciliation, not falsely physically stopped.
Library edits do not retroactively modify pins. Recall active policy remains explicit.
Own SQL schema/CAS/immutable history/intent/receipt/audit, strict codec and frozen new
migration, no crossowner FK/transactions. Do not hold DB transaction over network IO.
Prepare isolated PG17 tests without running/provisioning; no prior SQL permission reuse.

### P4 — Complete local checks, audit and handoff

One reproducible local runner with exact collected node identities/JUnit/no skip,
source closure hashes before/after, own suites +relevant01/12/14/08–11 regression
and existing dispatcher compatibility. SQL collection-only separately reported.
Ruff/Mypy owned modules, architecture/harness/security/diff gates. Keep actual
failed cases/assertions, fix defects then rerun; no invented PASS or weakened pins.
Contract examples/error/current-state matrix, policy/authority adoption register,
BE1/P4 effect-receipt/recovery conformance and actual SQL instructions; internal
completion vs actual runtime/integration acceptance clearly separated.
After exact approval finish all internal P1–P4 continuously; use meaningful scoped
functional/checkpoint commits, no per-function commits or repeated micro approvals.

## 5. Acceptance criteria / negative cases

| ID | Required local behavior | Actual gate not replaced by fixtures |
|---|---|---|
|A1|Strict eight-action preset delegate, action-specific capabilities, exact immutable versions/review/recall/CAS/idempotency, bad envelopes rejected before effects|CR13-01 actual preset policy/review/capabilities and12 binding adoption|
|A2|Exact preset/config pins and independent active state; editing library never updates accepted session snapshot; recalled source denied new pin|Actual BE1 atomic pin/current eligibility and active-copy policy|
|A3|Finite reviewed conditions produce versioned scoped intents, no effect from evaluation; no unsafe action/gate bypass, unknown/stale policy closed|Adopted condition/action rules/current consent/safety/review ports|
|A4|Teacher override/disable exact receipt and version advance; queued old intent stale, in-flight effect cannot win after override|Real BE1 compare-and-apply/current fencing/receipt dedup, not local lock only|
|A5|Recover original intent after lost/foreign/duplicate receipt, concurrency and partial write; no false effective/rollback claim; own atomic SQL surfaces|Actual own PG rollback/CAS/reconnect and actual owner reconciliation|
|A6|Explicit deferred/unsupported/pending/stale outcomes and reason/audit per decision, no silent overflow drop or autoapprove|CR13-03 adopted priority/capacity/scheduler policy; no pilot capacity claim|
|A7|Exact-node/source/JUnit local pack, source unchanged, applicable quality/security gates, complete contract/runtime handoff|Actual SQL/BE1/P4 combined override/race/restart/recall evidence and sign-off|

Required negatives: wrong org/role/session, Child, stale revision/hash/review,
conflicting key, forged result/scope/receipt, unknown fields/conditions/actions,
unreviewed/recall/new-pin races, bad config (field errors, no half apply), library
edit vs pinned use, disabled automation, stale stage/audience/epoch, duplicate event,
same intent/different payload, override vs enqueue/send/commit, lost ACK after effect,
failed own commit after BE1 receipt, delayed old result and reconciliation/restart.
Mandatory per-Sketch/final video approval, consent/safety and source rights cannot
be disabled by preset/Teacher override. No auto-completion/deletion/child achievement.

## 6. Evidence and completion boundary

Capture commands/environment/synthetic fixtures/source/node/JUnit hashes per suite,
not raw child data/secrets. Internal COMPLETE_LOCAL_VERIFIED only after P1–P4 tests/
audit/handoff done. Full card remains IN_PROGRESS_PENDING_EXTERNAL until actual
own SQL/current preset policy/BE1/P4 conformance and required owner acceptance.
External absence is not a reason to stop approved internal work, or to fabricate
effective configuration/success. Actual environment needs separate scoped authority.
