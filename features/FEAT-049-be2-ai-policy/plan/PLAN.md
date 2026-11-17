# BE2-14 — System AI configuration, limits, kill switch và provider-copy lifecycle

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date: 2026-10-17 (Asia/Saigon).
- Feature: FEAT-049-be2-ai-policy; không phải FEAT-014.
- Branch: feature/be2-08-14.
- Planning baseline: f0ff7a840d1910f1f80df327c3fd0239db5ea8e1.
- Owner: receiver BE2-08–14; sender tiếp tục BE2-01–07.

## 1. Mục tiêu và nguồn

Làm toàn card BE2-14, không chỉ một flag kill switch: versioned AI policy,
allowlisted profile/configuration, request pinning/current eligibility, budget/
concurrency/retry ceilings, emergency disable/cancellation, provider-copy
discovery/cancel/purge/receipt verification và redacted operational projections.

Nguồn: canonical SRS v3.1 FR029/030/054/056, UC-036/037 và privacy UC-038,
DATA-25/33/shared35, CMD-48, FIX-GOV-01/P-NFR-13; FEAT-040 card BE2-14;
FEAT-044 BE2_08_14_TEAMMATE_HANDOFF, roadmap/tracker; ADR-0015/0018;
FEAT-048 governance binding và checkpoint C4d. SRS là requirement, không approval.

Baseline inspection: BE2-12 code 6931daa, handoff f0ff7a8; 477 selected local /
33 owned SQL PASS là evidence BE2-12, KHÔNG phải BE2-14 PASS. Foundation vẫn
IN_PROGRESS và OwnerFence ASSUMED, không coi đã tích hợp hoặc merge dev.

## 2. Phạm vi / ranh giới

Giao domain, typed command/query/contracts, application ports/services, own SQL
storage/migration, CMD-48 AI-policy delegate, tests và consumer handoff. Một router
CMD-48 hiện có; không tạo policy endpoint cạnh tranh hoặc sửa content nghiệp vụ.

Không chọn provider/model, tạo credentials, đổi packages/cloud, chạy inference,
deploy/push/merge; không làm BE2-08/13 hoặc core policy BE1-15. Không ghi trực tiếp
BE1/job tables, không đổi foundation migration/shared contract để tiện nối.
Real BE1/P4 wiring để đồng đội làm sau theo owner; adapters/fixtures vẫn nhãn rõ.
Nếu phát hiện cần đổi foundation, lập CR kèm payload/error/tests, không sửa ngầm.

## 3. P1 — quyền, lifecycle và review (đề xuất cần duyệt)

- Capability riêng, scoped organization: author, safety-review, pedagogical-review,
  publish, disable, operations-read và provider-copy lifecycle execution. Tên role
  Super Admin không tự cấp quyền, raw-child access hoặc Teacher approval.
- Author không tự review/publish bản mình viết; non-author có từng capability mới
  review/publish được. Cần cả hai exact safety/pedagogical proofs cho policy version/
  hash/context trước publish; reviewer có thể publish nếu có quyền độc lập.
- AI-policy review là proof có typed policy target, không giả target learning_content
  để tái sử dụng DATA-24. Giữ shared publish review-set IDs/policy-version tương thích
  dispatcher. Nếu SRS/shared owner yêu cầu target amendment, ghi CR trước thay đổi.
  Phê duyệt P1 là chọn governance cho policy, không mở teaching review bypass.
- Dùng tám action CMD-48: create/edit/submit_review/record_review/request_changes/
  publish/recall/archive. Validate là kiểm tra không side effect, không action thứ 9.
  Disable policy version qua recall + reason; emergency kill là scoped blocking
  operation qua internal authorized port, không nhét action lạ vào CMD-48.
- Edit tạo immutable draft version và fresh reviews; global record revision tách
  version/hash/review revision. Non-create cần If-Match, đúng exact target/hash.
- Receipt scoped principal/org/key/body; replay vẫn kiểm quyền/current eligibility;
  stale/conflicting duplicate bị chặn. Giữ history/provenance, không reset version.

## 4. P2 — allowlist, activation và pinning (đề xuất cần duyệt)

Policy body dự kiến strict/extra-forbid, không arbitrary configuration dict:

| Field family | Ý nghĩa / validation |
|---|---|
| title, feature_scope | Metadata; feature codes phải thuộc registry được adopt |
| model_profile_refs | Opaque profile id/version/hash; backend registry resolve; không endpoint/token |
| moderation_policy_ref | Exact reviewed policy; không disable safety/moderation |
| retry_policy_ref | Versioned retry definition compatible foundation; không tự tạo unlimited retry |
| budget_policy_ref | Versioned unit/window/ceiling definition; không suy tiền/credit từ code cũ |
| concurrency_policy_ref | Versioned effective scope/ceiling; không hardcode pilot capacity thành AI limit |
| required_gates | Teacher review/consent/current-source/safety không được cấu hình false |

Refs đều có id/version/hash; nghĩa, giới hạn và độ tương thích được validate
server-side bằng adopted definition/profile registry, không chỉ validate chuỗi.
Numeric values, units/window/TTL/provider/profile chỉ được kích hoạt khi đã được
owner/ADR phù hợp duyệt; fixture values ghi synthetic, không production defaults.
Không có policy/profile hợp lệ thì fail closed, không fallback sang legacy config.

Một effective policy pin cho từng org/feature scope; replacement atomic/CAS,
không overlap mơ hồ. Request/attempt lưu exact policy/profile refs. Publish P2 không
rewrite provenance request P1. Mỗi dispatch/retry/completion/exposure vẫn kiểm current
eligibility/kill/source/consent theo port. Old pin không là authorization vĩnh viễn.
Read projection chỉ metadata allowlisted; không raw prompt/media/identity/secret URL.

## 5. P3 — giới hạn và emergency stop (đề xuất cần duyệt)

- Budget/concurrency reservation có key, exact policy/scope/version và atomic
  accounting; duplicate không giữ quota hai lần. Commit/release/reconcile có receipt,
  không hoàn quota hai lần hoặc tự hết hạn nếu chưa có expiry policy được duyệt.
- Unit/window/cost estimate lấy từ approved definitions, không số tiền/capacity tự
  chọn. Race giữa reserve/disable/dispatch phải fail closed hoặc có một winner rõ.
- Disable/kill chặn work mới ngay khi commit; ghi epoch/reason/audit/outbox cùng tx.
  Enqueue/cancel delivery là at-least-once intent, không giả synchronous all-jobs-stopped.
- In-flight completion phải revalidate, không resurrect/expose sau disable/revoke/
  expiry. Request cancellation qua foundation application ports, không update ai_jobs.
- Re-enable cần explicit authorized reviewed activation; không tự resume job terminal,
  không bỏ Teacher review và không thay pin cũ bằng pin mới.
- Missing worker/provider confirmation phải pending/exception, không báo cancelled
  hoặc purge complete chỉ vì đã gửi intent. Retry/cancellation disposition traceable.

## 6. P4 — ProviderCopyLifecycle (đề xuất cần duyệt)

BE2-14 là contract owner; foundation hiện đã có candidate domain/service/report/
ports và fake/repository support. Inspect/reuse, không viết duplicate lifecycle.
Chỉ bổ sung own adapter/contract khi gap có evidence; changes touching published
foundation/shared surface cần explicit CR/adoption và regression trước khi sửa.

- BE1-15 giữ data-request authority/subject/purpose/expiry và core-copy purge;
  BE2-14 nhận verified scoped command qua guarded port, không nhận caller boolean.
- Registry discovery liệt kê known input/output/job/cache copies; pagination và
  coverage/completeness phải rõ, empty list không chứng minh all-provider deletion.
- Provider-specific hooks do BE2-04/08 cung cấp. No hook -> typed Unsupported/Pending,
  không gọi provider thật hoặc chọn provider mới.
- Cancel/purge key bound org/scope/exact copy/profile/operation, current authority,
  source expiry và immutable receipts. Crash/restart/retry không duplicate effect;
  late registration trong purging scope không được exposed lại.
- Receipt verification do trusted backend verifier, không chỉ client verified=true.
  Deleted chỉ khi đúng exact copy, adopted provider evidence và verification thật.
  Fixture deletion phải fixture-labelled, không actual_deletion_proven.
- Provider không support, timeout, incomplete/forged/mismatched receipt ->
  Unsupported/Pending/Exception có reason. Không gộp thành overall complete giả.
- H-DATA-REQUEST trả per-copy receipts/status cho BE1; không tự đóng request BE1.

## 7. P5 — storage, wiring và evidence (đề xuất cần duyệt)

Propose PostgreSQL17/SQLAlchemy existing dependencies, own ai_policy schema và
forward module Alembic branch cùng môi trường hiện có. Không sửa migration đã
publish. Owned policy/version/review/effective pointer/epoch/reservation/receipt/
event/outbox; normalize theo actual fields, không future-unused columns. Provider
registry tận dụng foundation port, không tạo shadow ai_jobs tables hoặc foreign FK.

Mutation/state/receipt/history/outbox atomic. Policy/current-access fences giữ
đến commit; external owner fence candidate không là real revocation proof. Bind
strict AiPolicy command model/handler vào GovernanceDispatcher.ai_policy hiện có.
Không mount default app bằng fake auth. Redacted operations query để BE1/P4
gateway dùng, không làm dashboard/monitoring platform hoặc reported-cost giả.

Windows dùng existing venv: unit/contract/HTTP/architecture/Ruff/Mypy/security;
PostgreSQL migration/restart/race/rollback theo one consolidated disposable pack.
Approval portable PG trước là BE2-12 scoped: không suy thành quyền provision cho
BE2-14. Khi pack ready, xin duyệt isolated PG17 test/cleanup riêng nếu chưa có
môi trường BE2-14 được duyệt. Không cần GPU hoặc Lightning cho component.

## 8. Acceptance / proof

| ID | Requirement | Evidence cần có |
|---|---|---|
| AC01 | Strict eight-action AI-policy model và sole CMD-48 delegate | full action-union, invalid-before-effects, content/preset/core regression |
| AC02 | Scoped independent auth/review/publish/disable | positive/negative capability, self-approve, cross-org, replay/revoke cases |
| AC03 | Version/hash/CAS/review/pinned provenance | edit fresh-review; P2 new pin/P1 old pin; stale/idempotency tests |
| AC04 | Profile/field allowlist, mandatory safety ceiling | unknown/secret/bypass/missing registry/compatibility negatives |
| AC05 | Atomic effective-policy activation và no stale exposure | real SQL publish/disable/resolve races; completion revalidation |
| AC06 | Budget/concurrency lifecycle | concurrent reserve ceilings, duplicate/release/restart/reconcile cases |
| AC07 | Kill/cancel traceability, no automatic terminal resume | new-work denial; in-flight/late-result/cancellation failure tests |
| AC08 | Scoped ProviderCopyLifecycle discovery/dispatch | authorization, coverage/pagination, exact-copy and missing-hook cases |
| AC09 | Truthful receipt verification / no resurrection | forged/unverified/fixture/deleted/pending/unsupported/exception/restart cases |
| AC10 | Own SQL atomicity, migration isolation | upgrade/rollback/restart, receipt/outbox rollback, immutable records |
| AC11 | Safe metadata operations projections | redaction, unavailable-not-zero, no raw child/token/provider URL |
| AC12 | Reproducible handoff / independent integration gate | source-bound command pack, exact inventories, explicit fixture/runtime limits |

No percentage, production-ready, actual deletion, real cost/load or full-card
DONE from fixture PASS. Real owner integration deferred to teammates by owner,
still NOT_RUN until actual adapters/receipts/conformance exist. Preserve gate list.

## 9. Checkpoints / commits

C0 plan+approval -> C1 domain/typed policy+contracts -> C2 own SQL/migration ->
C3 policy activation/eligibility/budget/kill -> C4 copy lifecycle verification/
registry adapters -> C5 CMD-48/operations queries -> C6 consolidated tests/review/
handoff. Split by coherent code+tests, not each function. Security+diff before
each scoped commit. Never alter validators to manufacture PASS. No push/merge.

## 10. Approval request / next action

Approve revision 1 including P1–P5 to implement this card. P1 review target and
disable mapping, P2 reference-only allowlist, P3 atomic limits/emergency behavior,
P4 truthful provider lifecycle and P5 own storage need explicit acceptance.
This does not adopt unknown runtime values or another owner's contracts. First
implementation step after approval: inspect exact schema binding and foundation
reuse gaps, freeze field/error matrix; flag any required cross-owner CR before code.
