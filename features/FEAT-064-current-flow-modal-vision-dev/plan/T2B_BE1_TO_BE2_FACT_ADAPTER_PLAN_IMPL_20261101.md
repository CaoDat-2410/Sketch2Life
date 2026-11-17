# T2B — BE1→BE2 trusted fact adapter (offline)

- **Status:** APPROVED for the bounded, offline adapter described here; no runtime wiring or live provider work is approved.
- **Feature:** FEAT-064 — current-flow Modal Vision dev pilot.
- **Decision authority:** Project owner / Person 2 (`AnhKhoaa157`), direct instruction in this chat on 2026-11-01. This revision supersedes the earlier T2B draft's unresolved-question/stop disposition.
- **Baseline:** branch `feature/feat063-be-foundation`, starting commit `578f3e5ee53ba841a83352a133141cfe80b8c672` (Case X at task start).
- **Purpose:** an injected, read-only infrastructure adapter that can construct only BE2 `MemberFact` and image-only `ContextDecision` for a one-member synthetic development pilot. It is not wired into a router, runtime, composition root, Modal, or GPU.

## 1. Verified boundary and source constraints

Current BE2 ports are `AssistanceOwnerPort.members(organization_id, participant_ids, purpose_code) -> tuple[MemberFact, ...]` and `AnalysisContextPort.current(scope) -> ContextDecision`. `VisionContextSourcePort.resolve(pin, source)` is a separate typed-context source. `ProviderContextMode` is `IMAGE_ONLY` or `TYPED_CONTEXT`. `CanvasFacts`, `GroupRoster`, and `current_turn` are outside this task and proposed for T2C.

Relevant BE1 source facts are in `be1_models.py`, `core_store.py`, `be1_common.py`, and the session/registry routers. Profiles contain age, origin, consent references and state; synthetic proofs contain exact scope, run/session, issue/expiry and revocation fields; memberships and sessions carry their current state. The consent table CHECK currently permits only `pending` and `revoked`, while the existing legal predicate looks for `effective`. Consequently this adapter denies REAL/LEGAL_CONSENT until B4b resolves the legal-consent persistence path.

`ManagedProfileModel.age_months` is written only at profile creation (`be1_registry.py` POST create) and operator synthetic-profile creation (`core_store.py:create_synthetic_profile`); no update route or assignment exists. This is the basis for a fixed age revision in this pilot adapter. If a future age-edit route is introduced, it must add a durable age revision as part of B4b; this task adds no schema column.

## 2. Owner decisions recorded for implementation

| ID | Decision | Implementation rule |
|---|---|---|
| A1 | No schema or migration. Age is write-once in current BE1 paths. | Emit `age_revision=1`; emit `age_provenance_ref=be1-profile-age-v1:{child_id}`. A future age-edit route must first add a durable revision under B4b. A dedicated AST/source test protects the current write-once assumption. |
| A2 | Synthetic facts do not have legal consent references. | In `MemberFact`, `consent_record_ref` and `consent_revision` are both `None` iff `eligibility_basis == SYNTHETIC_DEV`. LEGAL_CONSENT and legacy/no-basis instances require both values. A domain `__post_init__` enforces this. Teacher DTO marks synthetic basis and accepts the pair of null values only for that basis; omission/LEGAL still requires both. |
| A3 | A shared deterministic context-revision helper is used by this and future adapters. | Canonical JSON encoded as UTF-8 with non-ASCII characters emitted directly, sorted keys, compact separators, values only string/integer/boolean/null, no floats; prefix `sketch2life/context-revision/v1\n`; SHA-256; first four digest bytes, big-endian, masked with `0x7FFFFFFF`, zero mapped to one. The result is 1..2,147,483,647 and fits the BE2 `ai_jobs.context_revision` signed 32-bit Integer. Consumers compare equality only. It is a stale-data gate, not a signature; collision probability is approximately 2^-31. Never include `session.revision`. |
| A4 | T2B returns only `MemberFact` and `ContextDecision`. | `CanvasFacts`, `GroupRoster`, and `current_turn` are deferred to a separately named T2C task, using the same digest helper. |
| A5 | Pilot accepts a single member only. | Audience must equal the one requested child exactly. Empty, duplicate, mismatched, or multi-member audiences deny with a typed reason. |
| A6 | Synthetic pilot is image-only; legal path remains fail-closed. | `IMAGE_ONLY` synthetic may be returned only when all current pilot/proof/session/scope checks pass. `TYPED_CONTEXT` synthetic denies; no change to `domain/vision_context.py`. REAL/LEGAL_CONSENT, legacy, pending, or revoked cases deny until B4b. Synthetic booleans remain `consent_effective=False` and `purpose_granted=False`. |

## 3. Frozen context-revision input

The reader's fixed schema is `be1-fact-context-v1`. The digest payload contains exactly these flat keys, all present even when a value is null:

`schema_version`, `organization_id`, `class_id`, `session_id`, `session_state`, `session_run_ref`, `environment`, `pilot_enabled`, `purpose_ref`, `child_id`, `data_origin`, `profile_state`, `age_months`, `age_revision`, `consent_record_ref`, `consent_revision`, `consent_state`, `consent_effective`, `purpose_granted`, `membership_state`, `group_id`, `proof_evidence_id`, `proof_schema_version`, `proof_data_origin`, `proof_organization_id`, `proof_class_id`, `proof_child_id`, `proof_purpose_ref`, `proof_run_ref`, `proof_session_id`, `proof_revocation_revision`, `proof_issued_at`, `proof_expires_at`, `proof_revoked_at`, and `basis_version`.

Proof times are normalized to UTC ISO-8601 with `Z`; a naive time denies before digesting. All IDs/state/origin and versions are server-read values. The digest excludes canvas, turn, provider, source image and `session.revision`; those are not part of this T2B fact snapshot. Every field is versioned by `schema_version`, and basis changes are versioned by `basis_version`. Tests freeze a known vector and prove that changing each payload key changes the output for the selected vector. A 31-bit digest can collide; callers must use it only as an equality fence in addition to fresh eligibility checks, never as cryptographic proof or authorization by itself.

### BE2 field mapping

| BE2 field | Trusted source / mapping |
|---|---|
| `MemberFact.participant_id`, age | Exact requested child and active BE1 profile in the requested organization/class; age from `ManagedProfileModel.age_months`. |
| `MemberFact.age_provenance_ref` | Deterministic `be1-profile-age-v1:{child_id}` under the owner-approved write-once age rule; it is an origin marker, not evidence of a real age-edit revision. |
| `MemberFact.age_revision` | Constant `1` while BE1 has only the two creation paths. Any new age mutation invalidates this assumption and must be blocked until a durable revision is added under B4b. |
| `MemberFact.consent_record_ref`, `consent_revision` | Both `None` for `SYNTHETIC_DEV`, because no consent row/reference exists. For LEGAL_CONSENT/no-basis callers both remain required by the domain invariant; this reader denies the legal path until B4b. |
| Current `consent_state` | Exact BE1 consent row for org/class/child/purpose if present; it is included in the digest. Synthetic rows require it to be absent. Legal states remain fail-closed pending B4b. |
| `MemberFact.consent_effective`, `purpose_granted` | Both `False` for synthetic. No synthetic proof is promoted to consent or purpose grant. |
| `MemberFact.eligibility_basis`, basis version, evidence, scope | `evaluate_eligibility` over current server-read profile, exact proof, session/run, environment and pilot flag; evidence is the proof `evidence_id`; scope is the exact org/class/child/purpose tuple. |
| `ContextDecision.audience_age_months`, `session_active` | Exact one-child profile age and current BE1 session state; only active session is accepted by this reader. |
| `ContextDecision.context_revision` | A3 digest over the frozen §3 flat payload; it is only compared for equality. It never copies `ClassroomSessionModel.revision`. |
| `ContextDecision` eligibility fields | Same current eligibility decision as `MemberFact`; synthetic legal booleans remain false, and basis/version/evidence/scope remain consistent across both facts. |
| `CanvasFacts`, `GroupRoster`, `current_turn` | No mapping in T2B; explicitly deferred to T2C. |

## 4. Reader protocol and decisions

The implementation uses a small injected synchronous `BE1FactSource` protocol. Its `current_facts` read receives an explicit organization/class/session/child/purpose scope and returns one immutable raw snapshot or `None`. It must not import `interfaces/**`, call network/provider code, or trust client facts. The reader rechecks exact identifiers rather than assuming the source honored scope.

The snapshot carries session state/run, environment/pilot flag, profile origin/state/age and consent facts, membership state/group, and optional server-read synthetic-proof fields including the database revocation revision. A proof is converted to the existing `SyntheticEligibilityProof` and passed to `evaluate_eligibility`; in addition, synthetic proof `session_id` must exactly equal the request session (not merely be absent-or-equal). Any missing/malformed fact denies.

For accepted synthetic input, emit exactly one `MemberFact` with the fixed age provenance/revision, both consent refs null, false legal-consent/purpose booleans, `SYNTHETIC_DEV`, `BASIS_VERSION`, proof evidence id and exact `EligibilityScope`. Emit `ContextDecision` with the same basis/evidence/scope/version, digest context revision, `session_active=True`, and exactly one audience age. Reject inactive profile, non-active session, non-admitted membership, wrong group/scope, expired/not-yet-valid/revoked proof, wrong run/environment, disabled pilot, unsupported context mode, or audience cardinality other than one.

Denials use a closed `FactReaderReason` enum and return no partial facts. The adapter is deliberately standalone: no changes to BE2 ports/services, router/runtime/composition, fakes, or existing provider flow.

## 5. Tests and acceptance

Five new tests are required, written before production code and demonstrated red on the starting HEAD:

1. `backend/tests/unit/test_member_fact_consent_rules.py`: null pair iff synthetic basis; legal and no-basis require both; Teacher DTO permits null only with synthetic basis.
2. `backend/tests/unit/test_context_revision.py`: determinism, sorted key behavior, stable vector, result range, all payload keys affect the frozen vector, float/unsupported type rejection, and no session revision field.
3. `backend/tests/unit/test_profile_age_invariant.py`: AST/source guard confirms all current `ManagedProfileModel.age_months` writes are only the two named creation paths; a new mutation path makes the test fail pending a real revision.
4. `backend/tests/unit/test_be1_fact_reader.py`: valid synthetic and each fail-closed case, including malformed/missing/scope/run/session/proof/pilot/state/audience/context-mode cases.
5. `backend/tests/contract/test_be1_fact_reader_contract.py`: returned facts pass the existing image-only BE2 synthetic gates; legal booleans remain false; typed synthetic is denied before `domain/vision_context.py` is called.

Acceptance requires these tests green, the 5-file CI + 2 T1 + supplemental R0 test counts not below baseline, configured Ruff, strict mypy with zero new issues, all three repository validators, clean diff/byte checks, and no edit outside the allowlist. Tests are local contracts only: no database, Alembic, network, Modal, GPU, end-to-end wiring, real child data or provider request.

## 6. Allowlist and exclusions

Authorized code edits: `backend/src/sketch2life/domain/assistance.py`; `backend/src/sketch2life/contracts/schemas/assistance_requests.py`; only the synthetic-null Teacher projection in `backend/src/sketch2life/application/services/assistance.py`.

Authorized new code: `backend/src/sketch2life/infrastructure/assistance/context_revision.py`; `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py`.

Authorized new tests: the five files in §5. Authorized documentation: this plan, T3 REV2 plan, T2B implementation report, and append-only FEAT-064 approval entries for T2B and T3 decision recording.

Explicitly excluded: routes/runtime/composition, fakes, `domain/vision_context.py`, `domain/vision_analysis.py`, BE1 models/core store/Alembic, UI, B5/B6 routes, B4b, T2C (`CanvasFacts`, `GroupRoster`, `current_turn`), Modal/GPU, PostgreSQL, live provider and all seven local owner files. This is not production-readiness approval and does not connect Modal to the classroom flow.

## 7. Completion and follow-up

T2B is complete only as a bounded offline fact adapter and tests. It is not end-to-end runnable until separately approved integration work supplies a production source and wires the BE2 ports. T2C must cover the deferred owner facts and share the A3 digest helper. B4b must resolve effective legal consent and a durable age revision before REAL/LEGAL_CONSENT can be enabled. T3 REV2 records product decisions and blockers only; its code remains unapproved. PostgreSQL/Alembic, Modal/GPU, end-to-end chain, T3 implementation, B5/B6 and B4b remain not run/not done.
