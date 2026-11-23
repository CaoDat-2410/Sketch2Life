# Platform Admin API and UI completion plan

- Status: APPROVED
- Plan revision: 3
- Implementation status: IN_PROGRESS
- Date: 2026-11-20

## Scope

1. Inventory current Admin routes, authorization, persistence, tests, and UI consumers against the canonical SRS.
2. Complete bounded Admin APIs for organizations, accounts and roles, Content Admin permission, lesson/catalog lifecycle, feedback, operations, lifecycle, audit, inbox/preferences/email delivery, and local/test billing, quota, and capacity.
3. Add the newly approved Admin API slices: organization name/state updates; operator readiness/queue/worker telemetry; and audit-retention policy visibility and safe configuration. Do not enable real-payment processing.
3. Keep authorization server-side, commands idempotent, mutable resources revision-guarded, audit metadata-only, and child media denied by default.
4. Connect every supported Admin UI screen to real APIs with loading, ready, empty, denied, conflict, failure, retry, and success outcomes.
5. Redesign each screen with the existing Admin tokens and components after its API contract is verified.

## Sequence

1. Keep the existing organization/account/content/feedback/sandbox flows intact.
2. Add organization profile and state commands with revision guards and audit events.
3. Add privacy-safe operator health, durable queue, and worker signals; report unavailable dependencies as unavailable, never as healthy.
4. Add audit-retention policy/status APIs. Default to indefinite retention until a duration is explicitly configured. A purge requires a preview and a separate idempotent command; do not delete audit entries on page load or as a side effect of reads.
5. Wire the three slices into the existing Platform Admin web panels and refine the desktop/tablet layouts and all loading, empty, error, stale, and success states. No mobile-app UI work.
6. Review the complete Admin route map and preserve sandbox billing with real payments disabled.

## Acceptance criteria

- Every implemented route rejects missing, inactive, wrong-role, wrong-permission, or wrong-scope principals on the server.
- Content publication enforces independent review and immutable published revisions where required by the SRS.
- Audit responses expose metadata only and preserve the child-data deny boundary.
- UI numbers come from complete API results; no fabricated counts, statuses, or successful mutations.
- Empty and failure states are distinct, actionable, responsive, and keyboard accessible.
- Backend unit/integration checks, frontend build/tests/lint, and focused browser checks pass for each completed slice.
- No production payment call, real child data, secret exposure, destructive database reset, commit, or push is performed.
- Organization edits and state transitions are server-authorized, revision-guarded, idempotent, and audited; no cascade into accounts/classes is inferred.
- Operations metrics are sourced from actual dependencies and durable rows, include freshness/availability, and contain no child/profile identifiers, free text, or provider payloads.
- Audit retention defaults to indefinite. Configured expiration is visible before action; preview is read-only, and pruning is explicit, separately confirmed, bounded, idempotent, and recorded as metadata.
- Admin web screens retain the established Sketch2Life violet/indigo palette with clear contrast, dense but readable data layout, keyboard focus, and truthful loading/empty/error states.

## Open requirements

Production prices, purchase/allocation authority, provider settlement policy, and any future child-media exception remain open per the SRS and are excluded until approved. Audit retention duration is configurable by an authenticated Platform Admin in this slice; the initial policy keeps entries indefinitely, so no retention period or destructive cleanup is invented by default.

## Revision 3 — video quota commerce and real provider integration

- **Status:** APPROVED_FOR_IMPLEMENTATION
- **Approver:** Project owner, direct approval of the five-step implementation sequence in the current conversation (2026-11-22).
- **Canonical product decisions:** Follow FEAT-063 SRS §31.20: Parent purchases for their own account; assigned School Manager purchases for their organization and may allocate/reclaim only unused quota for assigned Teachers; Platform Admin owns offer/price versioning; MoMo and VNPay are selected payment methods; monthly offers allow manual payment or explicitly authorized cancellable auto-renew when the merchant product supports it; top-ups are one-time; no refund after successful settlement.
- **Scope:**
  1. Reconcile and preserve the remaining open quota policies; do not invent unresolved expiry, renewal-failure, role-change, or chargeback behavior.
  2. Complete server-authoritative versioned quota offers/prices, Parent/School purchase scopes, school-to-Teacher allocation/reclaim, payment attempts, immutable settlement evidence, and audit/reconciliation APIs.
  3. Add MoMo/VNPay one-time and supported recurring adapters, starting with provider sandbox configuration and signed server-to-server callbacks. Real dispatch is disabled by default until credentials and merchant configuration are supplied and the integration has been validated.
  4. Connect supported Platform Admin and School Manager web screens to the APIs. Do not add mobile UI. Parent API scope is included; Parent mobile UI is not part of this plan.
  5. Leave video-generation integration for a later task; this slice establishes and exposes quota admission/ledger contracts only.
- **Boundaries:** School-capacity billing stays separate; no hardcoded production prices; no fake payment success; no provider secret in source, reports, or chat; no commit or push.
- **Open prerequisites:** Merchant sandbox credentials and callback URLs must be entered into ignored local environment/secrets by the owner. Provider-specific recurring authorization must only be enabled for an approved merchant product. Remaining SRS open policies remain gated from implementation until the owner resolves them.


## Billing review corrections - 2026-11-23

Within approved Rev3 scope, correct Teacher allocation return, catalog mounted operations, exercise settlement/allocation/callbacks and migration guards with local fixtures, mirror School payment recovery for Parent scope, and address specified type, lint, callback and development-host defects. Preserve provider policy and defer quota consumption.

Acceptance: runtime autoflush-disabled PostgreSQL regression verifies return event and balance; catalog matches mounted routes; payment and migration tests cover requested cases; Parent recovery enforces its own scope and School behavior; checks and baseline comparison are recorded. No live payment, SRS change, migration edit, commit or push.
