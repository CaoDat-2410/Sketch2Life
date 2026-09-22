# ADR-0008: ChildProfile ownership, Guide assignment, Parent Web and observability boundary

- Status: ACCEPTED FOR REQUIREMENTS BASELINE; PHYSICAL IMPLEMENTATION TBD
- Date: 2026-09-19
- Owner: Sketch2Life project owner
- Refines: ADR-0005 authentication boundary; FEAT-029 master SRS

## Context

The owner clarified the target product model for the master SRS. Children do not authenticate. An adult parent or legal guardian manages one or more child profiles. A child may have multiple Guides, and Guide access must be time-bounded, revocable and visible to the Owner. Parent Web, durable session/audit history, Grafana operations and child-data lifecycle must be represented without violating the existing Firebase-only-authentication and backend-owned-storage boundaries.

The registration form and workflow images contain both product scope and project-deliverable language. This ADR records the owner-approved interpretation for cross-feature requirements. It does not select a final database, object store, queue, Grafana deployment, notification provider or serialized runtime contract.

## Decision

### Ownership and identity

- There is exactly one `OwnerCaregiver` for each `ChildProfile`.
- An OwnerCaregiver may create and manage many ChildProfiles.
- The ChildProfile has no login credential or Firebase identity.
- Parent and legal guardian are represented by the same OwnerCaregiver concept; the legal relationship verification workflow remains a separate policy question.
- Firebase Authentication verifies adult identity only. Backend authorization resolves ownership and delegated access.

### Guide assignment

- A ChildProfile may have multiple Guide assignments, including overlapping assignments.
- A GuideAssignment directly references a Guide and ChildProfile and stores source actor, permission profile, start time, expiry and revoke state.
- Valid share durations are 3, 7, 15 or 30 days.
- Parent-created assignment is effective immediately and notifies the Guide.
- Exceptional Admin-created assignment is effective immediately and notifies both Owner and Guide.
- Owner can revoke an assignment at any time. Revoke does not erase history.
- A Guide may operate one session at a time. Assignment state is checked server-side on every protected command.
- Guide access is delegated and never transfers ChildProfile ownership.

### Session and Parent Web

- A Guide session is associated with exactly one ChildProfile and one adult operator.
- Opening a Guide session creates an Owner notification and a live session projection.
- The Owner can monitor necessary session information in real time; UI data is minimized and excludes internal technical metadata, credentials and provider details.
- Revoking the Guide during an active session immediately stops the session, blocks further Guide commands, shows an in-product message and records event/audit/notification data.
- Mobile and Guide Console are the MVP product surfaces.
- Parent Web is a Phase 2 management and monitoring surface using the same backend authorization model. It manages ChildProfiles, Guide assignments, history, notifications, retention and feedback. It is not implicitly a session-running client.

### MVP experience

- Personalized animation, narrated story and learning micro-video are included in the owner-approved MVP target.
- The physical/off-screen Montessori activity remains outside the digital timer.
- Original child artwork remains immutable; derived media has provenance and must not silently replace the original.

### Data lifecycle and observability

- Owner selects 30, 60 or 90 days for child/session data classes.
- Expired child/session data becomes inaccessible to Parent and Guide in archive storage before purge according to deletion policy.
- Audit retention is separate from child-data retention and must preserve the minimum evidence required by policy.
- Admin raw child-content access is break-glass only, requires a reason and temporary scope, and is fully audited. Dual approval, notice and exact time window remain open policy decisions.
- Durable business/session events and security audit events are the authoritative records.
- Grafana is an operational dashboard layer. Redacted logs, metrics and traces may feed Grafana; raw child media, credentials, tokens and provider secrets must never be placed in telemetry.

## Consequences

- Domain authorization must distinguish OwnerCaregiverOwnership from GuideAssignment.
- Existing class/family grouping may remain for administrative/reporting scope, but it cannot create an additional ChildProfile owner or implicit Guide access.
- API and schema work must use the direct GuideAssignment model or document an approved compatibility mapping before implementation.
- Parent notifications, revoke events, session projections, retention transitions and Admin break-glass reads require durable records and audit coverage.
- Parent Web can reuse backend APIs and policy decisions, but its UI and session-creation capabilities require a separate Phase 2 implementation decision.
- Physical storage, queue, notification, telemetry and Grafana technologies remain open until the relevant ADR/implementation gate.

## Non-decisions kept open

- Exact notification channel combination, retry and dead-letter behavior.
- Guide field-level access to raw media, transcript and historical records.
- Parent Web session creation.
- Break-glass dual approval, notice and time-window policy.
- Physical database/object-storage/queue/Grafana deployment and region.
- Legal-guardian verification and consent/assent handling for children aged 7 and above.
- Backup/provider-copy deletion and legal archive exceptions.
- Production SLO, RPO, RTO, account lifecycle and Admin provisioning.

## Evidence

- `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` sections B20–B29.
- `features/FEAT-029-master-srs/evidence/notes/OWNER_SCOPE_CLOSURE_20260919.md`.
- `features/FEAT-029-master-srs/approvals/TASK_APPROVAL.md` owner scope closure addendum.
- `docs/context/PROJECT_CONTEXT.md` master SRS scope closure entry.
- [Nghị định 13/2023/NĐ-CP](https://vbpl.moj.gov.vn/boyte/Pages/vbpq-toanvan.aspx?ItemID=161106&Keyword=) as a privacy/child-data constraint source.

