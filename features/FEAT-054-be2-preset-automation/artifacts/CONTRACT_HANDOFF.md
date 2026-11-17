# BE2-13 candidate contract / owner adoption handoff

Revision1 P1–P4, frozen plan601afab8. Internal components only; no production mount.
Actual CR13-01/02/03 remain OPEN_CANDIDATE. No actual preset policy or BE1 adoption
is implied by candidate fields, assumed policy fixtures or a successful local call.

## Preset governance / sole CMD-48

PresetCommand is strict/frozen/extra-forbid and binds through bind_preset(service)
to existing12 GovernanceDispatcher(preset=...). Existing injected governance router
remains the sole POST /api/collaboration/v1/governance/records. No second router.
Narrow compatibility addition: existing router catches PresetError using own safe
allowlist adapter, like the existing AI policy branch; unknown codes redact to503.
No existing content/AI response/routing/review rules weakened or production binding.

Common envelope: record_kind=preset, contract_version=0.1-candidate, action,
client_request_id. create has body and no target/If-Match. Every other action has
record_id, target_version, target_hash and exact quoted record-revision If-Match.
edit carries new body and returns target_version+1; others return exact target.
record_review carries typed review, publish typed review_ref; request_changes/
recall/archive require reason. Irrelevant action-specific fields rejected.

Body: title, effective_age_policy_ref, tool_policy_ref, canvas_mode,
assistance_policy_ref, stage_rules, notification_rules, video_policy_ref,
activity_policy_ref, assessment_policy_ref. All references validated under actual
adopted schema/allowlist; topic/config completeness remains owning policy check.
Rule candidate vocabulary stage_is or help_pending, expected value, notify_teacher
or request_support. Max32 combined unique rule IDs is a transport/resource bound,
not classroom/curriculum/priority policy. No arbitrary expressions, imports or JSON
action dispatch; no approve/play-unreviewed/complete/purge action.

Review proof is PRESET exact record/version/body digest/dimension/reviewer/policy/
decision, never a fabricated learning_content DATA-24 record. Authenticated current
proof supplied by actual owner. Shared PublicationReviewSet-shaped fields retained
for12 compatibility, not authority. Safety/pedagogical candidate proof pair and
separate publish capability must be adopted via CR13-01. Author cannot self-review/
publish. Actual current proof validity and source policy checked through owner guard.

Library aggregate holds all immutable body versions. Edit latest appends draft;
old publication retained until explicitly recalled/archived. Non-edit can target
an older version using current aggregate revision, so recall is not limited to latest.
Every mutation records actor/action/reason/time; history and original scoped command
receipts retained. Native replay returns historical result plus truthful current
revision/state for that target; it never reapplies old edits or republishes a recall.
Replay capability is current; do not interpret historical published response as new
pin eligibility. Source eligibility must be checked again by actual source guard.

## Session/control seams (not new CMD-12/59 endpoints)

PresetAutomation.prepare(org,session,actor,ControlRequest) persists queued pin/
override/disable intent, not effective config. Caller expected Stamp has session,
config, stage, automation positive versions. Pin requires draft +exact currently
published source record/version/body hash. Override uses exact accepted source pin
from authoritative SessionView; body values/actions require guard.intent adoption.
Scope/age/member/purpose/consent/safety/review cannot be replaced by Teacher preference.

evaluate(org,session,actor,event_id,rule_id) uses authoritative held SessionView,
not client observations; evaluates adopted rule on exact snapshot and records one
Decision: disabled/not_matched/queued/deferred/unsupported. Stable decision/event/
rule identity dedups own enqueue; enqueued Intent includes source snapshot/hash,
observed versions/policy/actor/action/reason/time. Decision does not cause an effect.
QueuePolicy.admit is pure/local policy evaluation on held snapshot, no network IO
or default priority/capacity. Deferral/unsupported are explicit audit dispositions.
Actual scheduler adapter calls evaluate/dispatch with server-verified scope; no
background timer, queue worker, lease or retry policy is activated by this feature.

dispatch is one explicit attempt. It atomically marks queued/deferred sending in
own store, then calls SessionCommands OUTSIDE own transaction. Rechecks current
scope/source/policy/intent/rule/context, queries native receipt first. BE1 execute
MUST compare all versions and current gates at atomic effect commit and durably
dedup original intent ID+hash. Teacher override/disable advances config+automation
versions; old already-dispatched automation cannot commit after that advancement.
Own scoped advisory lock/CAS does NOT implement BE1's authority/priority guarantee.

Exact EffectReceipt binds intent/org/session/hash/observed/effective versions/native
receipt ref and applied/stale/rejected disposition. Manual applied result must
advance config+automation and not regress session/stage. Only verified exact receipt
allows own terminal state; effect receipt+terminal transition commit atomically.
Own applied means that historical command applied, not current config after later
override. Timeout/wrong receipt/failed own ACK persistence leaves sending pending.

SessionCommands.reconcile performs NO new teaching/config effect. Real adopter may
recover original applied receipt or atomically fence the original stale command
and persist exact stale/rejected receipt, preventing future delayed application.
None means uncertain, not cancellation. Lookup absence alone is never a durable
no-effect claim. Recover original ID; never create new command on ambiguous commit.
Local reconcile marks old QUEUED work stale by current versions; SENDING work uses
native receipt recovery. It never enqueues or dispatches fresh queued work implicitly.
Scheduler/owner must enumerate affected IDs and call reconciliation; no hidden sweep.

## Error / conformance checklist

403 wrong scope/capability/revoked/separation,404 absent,409 stale/conflicting key/
target/state/source,422 invalid body/review/rule/reason,428 missing precondition,
400 unexpected precondition,503 missing policy/proof/corrupt storage/unavailable.
Unknown adapter messages never returned; HTTP no-store/ETag use existing transport.
Actual adapter operational exceptions must be sanitized, original uncertain command
retained. No DSN/token/real child data in public configuration, fixture or report.

Required owner tests: real verified Teacher scope, exact published source/pin,
library edit/recall, current policy/consent/review denial, concurrent override vs
enqueue/send/effect commit, disabled automation, lost receipt/own commit/native
restart, durable original-ID/body dedup, late result/receipt after new config,
deferred/unsupported/overload and all stale version axes. Real pilot load/P-NFR-16
capacity is not proved by this local component pack or latency of a fake handler.
