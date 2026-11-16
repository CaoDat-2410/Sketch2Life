# FEAT-063 Class and Package Contracts — Rev57 draft

- **Status:** proposed domain/application contract; not generated from database tables and not package approval.
- **Baseline:** SRS/Data Table Register v2.7-draft Rev57; source snapshot ae5707ca188d01d9719ed959b62d768ae927912d.
- Attribute types below are conceptual contract types. Optionality does not declare SQL NULL. IDs are opaque typed references; they are not new table keys.

## 1. Proposed domain class specification

| Class / owner | Attributes and conceptual types | Public operations | Relations / multiplicity | Invariant and trace |
|---|---|---|---|---|
| PrincipalContext / identity | principalRef: OpaquePrincipalRef; authenticated: Boolean; effectiveAssignments: AssignmentRef[]; resolutionRevision: VersionRef | resolveRoleScope(); invalidateOnRevoke() | One verified principal per request; multiple scoped assignments only as allowed by approved role model | Never trust client-supplied role; exactly four product roles; Content Admin is permission. Q-13; §§3/20. |
| PermissionDecision / authorization port | outcome: AllowOrDeny; reason: SafeReason; decisionRevision: VersionRef; evaluatedAt: Instant | authorize(principal, scope, resource, action) -> Decision | One decision for one request/action; decision may cite one active grant version | Fail closed if scope/version cannot be resolved; child media deny by default. Force-close details remain Q-13. |
| ParentProfile / parent_profiles | profileRef: ParentProfileRef; ownerPrincipalRef: OpaquePrincipalRef; profileRevision: VersionRef; lifecycle: ExistingProfileState | createRevision(); buildMinimalContext(policy) | Parent owns one or more profiles; each context snapshot belongs to run input, not school profile | No exact date of birth; new profile range 36–120 months; legacy behavior open. §31.1/Q-05/Q-11. |
| SchoolManagedProfile / BE1 | managedProfileRef: ManagedProfileRef; organizationRef: OrganizationRef; enrollmentRef: EnrollmentRef?; profileRevision: VersionRef | resolveAssignedRoster(); authorizeProfileRead() | Organization owns managed profile; enrollment projection follows BE1 constraints; link to Parent profile optional and unresolved | No match by name; roster access needs tenant/assignment and grant. Q-04. |
| ProfileShareGrant / identity contract | grantRef: OpaqueGrantRef; senderRef: PrincipalRef; recipientRef: PrincipalRef or audienceRef; purpose: PurposeRef; fieldScope: ApprovedFieldSet; grantVersion: VersionRef; expiry: Instant? | accept(namedTeacher); revoke(parent); authorizeRead() | One versioned grant connects sender and named recipient/audience; cardinality and audience acceptor open | Direct named Teacher accepts; Parent may revoke; revoke blocks new read/token and unaccepted jobs. Q-04. |
| DeliveryRecipient / Lesson delivery | recipientRef: OpaqueRecipientRef; organizationRef: OrganizationRef?; occurrenceRef: OccurrenceRef; sourceProfileRef: TypedProfileRef | resolveForDelivery(); authorizeHistoryRead() | One recipient within one occurrence delivery; how identity links Parent and School profiles is open | Not a canonical profile; preserve typed provenance and tenant scope; no cross-owner SQL FK. D-09/Q-04. |
| LessonVersionRefV1 / value object | ownerRef: OpaqueOwnerRef; version: ImmutableVersion; contentHash: SHA256; contractVersion: ContractVersion | verifyExactPin(expectedHash) -> Result | Optional on occurrence/plan/run; never resolves by name/latest | Exact version/hash pin across owner boundary, no SQL FK. §31.2/BR-09. |
| LessonOccurrence / lesson | occurrenceRef: OccurrenceRef; organizationRef: OrganizationRef; classRef: ClassRef; planRef: PlanRevisionRef; lessonVersion: LessonVersionRefV1?; occurrenceRevision: VersionRef | approvePlan(); requestSampleSelection(); confirmSelectedChild(); recordSuccessfulSample(); projectToClass() | Occurrence owns one approved plan pin and at most one successful sample; projection is not canonical state | Child selection is system-random, Teacher confirms; max one successful sample. Eligibility/evidence open Q-01. |
| PlanRevision / lesson | planRef: PlanRevisionRef; revision: ImmutableVersion; hash: SHA256; approval: ApprovedDecisionRef; lessonVersion: LessonVersionRefV1? | approve(); supersedeWith(newRevision); verifyCompletionPin() | Many immutable revisions may belong to one reusable lesson/occurrence | New approved revision does not silently retarget accepted work; supersession effects open M-10. |
| StoryRun / story | runRef: StoryRunRef; ownerRef: PrincipalRef; inputRevision: VersionRef; contextHash: SHA256; lessonVersion: LessonVersionRefV1?; state: ExistingStoryRunState | acceptInput(); confirmScript(); requestAdmission(); cancel(); acceptCompletion(expectedHashes) | One run owns its snapshots/revisions; AI Job references exactly one target | Completion fenced by expected revision and hashes; Parent activity remains post-video. §§6/31.5. |
| VideoGeneration / story | generationRef: GenerationRef; runRef: StoryRunRef; generationNo: Integer; state: ExistingGenerationState; acceptedAt: Instant?; deadlineAt: Instant? | admit(receipts); markReady(safetyProof); rejectByAdult() | One generation belongs to one run | Admission requires owner receipts; accepted deadline six hours; exact plan pin not retargeted. §6.1.1. |
| AiJob / ai_jobs | jobRef: JobRef; targetKind: OneOfEightTargetKinds; targetRef: TypedOpaqueRef; jobState: ExistingAiJobState; attemptNo: Integer; contractVersion: ContractVersion | dispatch(); recordAttempt(); requestCancel(); recordCompletion(disposition, hashes) | Exactly one target per job; Story/Lesson owns business result | Never duplicate child subject field; callbacks fenced; main router not mounted at inspected source. DTR §5.2. |
| QuotaAdmission / billing port | quotaScope: ParentAccount or SchoolOrganization; usageReceipt: ReceiptRef?; computeReservation: ReservationRef?; requestKey: IdempotencyRef | validateAndConsume(); reconcileReceipt() | Billing and AI Policy each own independent receipt | Teacher school scope only; Parent own scope; included current month before top-up FIFO; compute is AI Policy. §31.7. |

A question mark means optional in the logical contract only. Existing...State refers to values already enumerated in SRS; it is not a new state or database enum. No class maps one-to-one to a table.

## 2. Ports and signatures

| Port | Proposed interface | Owner and guarantee |
|---|---|---|
| AuthorizationPort | authorize(principalRef, tenantScope, resourceRef, action, expectedGrantVersion?) -> Allow/Deny(reason, revision) | Identity/BE1 boundary; server-side, deny by default; no child-media grant from admin role. |
| RosterPort | listAssignedCandidates(organizationRef, classRef, teacherRef, policyVersion) -> typed refs | BE1 owner; exact eligible-set policy is OPEN Q-01; never returns an arbitrary teacher-selected child set. |
| ProfileGrantPort | resolveGrant(senderRef, recipientRef, purpose, fieldSet, expectedVersion) -> current grant disposition | Identity owner; direct named Teacher acceptance and Parent revoke known; audience details open Q-04. |
| LessonVersionPort | resolvePinned(opaqueRef, version, hash) -> exact immutable version or denied/stale | Lesson / learning_content owner; never substitutes latest. |
| BillingAdmissionPort | consume(scope, requestKey, amount/version) -> owner-local receipt | Billing owner; school or Parent scope only; amount/pricing open Q-02/Q-12. |
| ComputeReservationPort | reserve(policyScope, requestKey, resourceQuote) -> owner-local receipt | AI Policy owner; compute budget is separate from product quota. |
| AiJobPort | enqueue(targetKind, targetRef, expectedRevision, contractVersion, requestKey) -> jobRef/receipt | AI Jobs owner; exactly one of eight target kinds. Mounted status is not established. |
| AggregateCompletionPort | commitResult(ownerRef, targetRef, expectedRevision, hashes, safeResultRef) -> accepted/stale/rejected | Story or Lesson aggregate owner; idempotent and stale-fenced. |

## 3. Target package ownership and dependency matrix

All rows below are TO-BE package ownership. Matching source folder names are AS-BUILT file observations, not approval that the complete boundary is implemented.

| Package/module owner | Domain responsibility | Application contracts | Adapter/infrastructure responsibility | Allowed dependencies |
|---|---|---|---|---|
| identity / BE1 | principals, organization, roster, managed profile, grant authorization boundary | role/grant resolution ports | BE1 persistence and verified-auth adapter | inward to domain/application contracts; no story or UI DB access |
| parent_profiles | Parent-owned profile revisions and minimal context rules | profile/context commands and reads | owning repository/asset refs | depends on identity ports; not BE1 table writes |
| lesson | reusable lesson, occurrence, plan, deck, delivery, feedback | occurrence/deck/delivery commands | lesson persistence and outbox | other owners via contracts only |
| learning_content | global typed catalog and immutable published versions | catalog query/review/publication ports | catalog repository/HTTP adapter | public contract; no direct Story/Billing table reads |
| story | StoryRun, snapshots, video generation and playback eligibility | run/admission/completion ports | Story repository and outbox | calls Billing/AI Policy/AI Jobs via versioned ports |
| ai_jobs | durable job, attempts, receipts, cancellation and dispatch | enqueue/poll/callback contracts | SQL/queue/provider adapters | no ownership of Story/Lesson result |
| ai_policy | provider/compute policy and reservations | capability/reservation ports | policy store/ledger | no product quota balance ownership |
| billing | subscription, capacity, product quota grants and usage | receipt/purchase/reconciliation ports | payment adapter and billing store | no cross-owner transaction |
| core/assets | asset metadata, lineage, upload sessions and audit metadata | asset/upload/audit ports | object-store adapter and repository | no child data in operational logs |
| interfaces/contracts | HTTP, worker and event adapters | versioned input/output contracts | framework wiring and serializers | depend inward on application; never define domain policy |

| Source layer | Allowed target dependencies | Forbidden dependency direction |
|---|---|---|
| Interfaces/adapters | Application ports/contracts | Direct mutation/query of another owner’s tables |
| Application | Domain and declared ports | Framework/provider/storage/queue implementation details |
| Domain | Domain value types and pure policies | Infrastructure, framework, provider, storage, UI or queue |
| Infrastructure | Domain/application ports it implements | Outward dependency becoming canonical business rule |

## 4. Source import and composition review

Read-only Python AST scan at ae5707ca188d01d9719ed959b62d768ae927912d inspected 559 Python modules under backend/src/sketch2life: zero detected outward-layer import edges for the checked domain/application rule, and one cycle between infrastructure.canvas_render and infrastructure.canvas_render.renderer. Resolve or explicitly accept that source cycle before a source-verified Package diagram. Dynamic imports, DI wiring, UI/mobile language graphs and runtime dependency behavior were not checked.

Source directories for learning_content, ai_jobs and ai_policy exist. Source router ai_jobs.py exists but is not included by the inspected main router_composition.py. This is not proof of a complete module or mounted API. Do not call this package tree AS-BUILT.
