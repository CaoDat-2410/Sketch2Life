# Feature decisions

## 2026-10-17 23:24 +07:00 — owner component acceptance of A1

- Owner accepted A1 ASSISTANCE_COMPONENT_OFFLINE on A1_CODEX_FINAL_REVIEW_20261017.md; verbatim in
  `approvals/A1_COMPONENT_ACCEPTANCE.md`. Component scope only: no full-card acceptance,
  production adoption, other owners' sign-off or Git publication. No new checkpoint opened.

## 2026-10-17 — Codex A1 final code review

- CODE_REVIEW_PASS (0 P1 / 0 P2), all A1-CR01–CR05 and CR03-F1/F2 closed in the approved
  offline component scope. Root 878/878 pass, 0 skip; positive probes verify actual commit
  ordering, combined epoch, correction/invalidation, rollback and authority re-decision.
- Review evidence/notes/A1_CODEX_FINAL_REVIEW_20261017.md and metrics bind this result to
  current source hashes. Approved plan, approval and previous evidence unchanged.
- No owner acceptance or Git publication is created here. Next: owner disposition of A1
  and separately requested publication planning. BE2-03 NOT_DONE; BE2-02 PARKED;
  BE2-01 WAITING_STUDIO; production/runtime/integration limits remain open.

## 2026-10-17 — A1-CR03 follow-up (within the existing A1 approval)

- **F1:** owner publications are deferred while any coordinated unit (foundation, Vision or
  assistance) is open on the thread and drain after the outermost unit exits (commit or
  rollback), each under the coordinator.
- **F2:** Vision transactions run as coordinated `vision` units via the new
  `CoordinatedAnalysisRepository` decorator; committed Vision writes bump a separate
  `analysis:<org>` epoch, and the decision token is (owner/request epoch, analysis epoch).
  Fake composition only; no production fencing claim. Plan revision 3 and approval unchanged.

## 2026-10-17 — Codex A1 fix re-review

- NEEDS_REVISION (0 P1 / 2 P2): CR03-F1 same-thread owner publication inside an assistance
  unit; CR03-F2 legitimate Vision invalidation commits without changing the decision epoch.
  Original pre-transaction owner race is fixed; CR02/04/05 close in reviewed scope; CR01
  direct disclosure gate works but depends on the remaining lifetime protection.
- Root 868/868 pass, no skip; new witness probes reproduce both remaining issues. See
  evidence/notes/A1_CODEX_REREVIEW_20261017.md and metrics. A deferred revocation after a
  completed handoff is a different valid order; regressions must observe commit order.
- Bounded fixes and re-review remain within existing A1 approval. Approved plan/approval
  and historical evidence unchanged. No acceptance, Git publication or runtime claim.

## 2026-10-17 — A1 code-review fixes (within the existing A1 approval)

- **A1-CR03 decision epoch (fake composition):** submit (incl. cache/disclosure), handoff and
  cancel read the shared `eligibility:<org>` decision epoch before their owner/source/analysis/
  authority reads and commit only while it is unchanged (else bounded re-decision). Owner
  publications bump it through the coordinator (A1-CR02 serializes them). Not production SQL
  owner fencing.
- **A1-CR04:** supersession only on a changed owner-fact digest; same-fact semantic changes are
  debounced/budgeted. **A1-CR05:** normalized intent drives fingerprint/identity/storage.
  **A1-CR01:** cache requires current disclosure of the original. Handoff gate checks the
  owner digest before the analysis read. Plan revision 3 and approval unchanged.

## 2026-10-17 — Codex A1 code review

- NEEDS_REVISION (0 P1 / 5 P2): A1-CR01 cache disclosure, CR02 owner-publication
  coordination, CR03 current decision through handoff commit, CR04 fact supersession
  versus changed semantic payload, CR05 LongText normalization.
- Root 851/851 offline tests and static checks pass, but targeted probes reproduce
  these violations. Details: evidence/notes/A1_CODEX_REVIEW_20261017.md and metrics.
- Existing approval/D1–D11 and approved plan bytes unchanged. Next: bounded A1 fixes,
  regression evidence and re-review; no acceptance, next card or Git publication.

## 2026-10-17 — owner approval and A1 implementation

- **Owner approval (actual):** plan revision 3 SHA256 e1fce645… frozen at
  `plan/PLAN_REV3_APPROVED.md`; D1–D11 selected as recommended; verbatim in
  `approvals/TASK_APPROVAL.md`. Offline component approval only.
- **Work order:** A1 ACTIVE (single implementation slot); BE2-02 PARKED at accepted C2;
  BE2-01 WAITING_STUDIO.
- **Implementation choices within the plan:** see evidence/notes/A1_IMPLEMENTATION_EVIDENCE_20261017.md
  "Routine implementation choices" (committed-snapshot 202 body, 503 for malformed owner audience,
  403/404 split for CMD-33, eligibility denial reasons). IMPL-F1 cache-gate gap found by A1-N17
  and fixed before review.

## 2026-10-17 — Codex revision-3 final plan review

- PLAN_REVIEW_PASS, no blocking finding in A1 offline scope. A1-PR01-F1 and all
  original findings closed at plan level, not runtime or implementation proof.
- Plan SHA256 e1fce645 and prior review evidence unchanged; see
  evidence/notes/PLAN_CODEX_FINAL_REVIEW_20261017.md and metrics. TC-11 coordinator
  is fully specified; the plan's TC-01…TC-10 index wording is a non-blocking note.
- D1–D11 remain recommendations. Next is genuine owner approval of exact revision
  and choices, not automatic implementation or publication. No approval edited.

## 2026-10-17 — plan revision 3 (planning correction under the user's request)

- Revision 2 bytes (SHA256 0894c39b…) kept as ignored local historical draft
  `evidence/local/planning-rev3-20261017/PLAN_REV2_0894c39b_HISTORICAL_DRAFT.md`; never approved.
- **TC-11 shared fake commit coordinator (A1-PR01-F1).** `AssistanceCommitCoordinator` shared by
  a new `CoordinatedAiJobRepository` decorator (each foundation write transaction from hold
  through commit), the assistance fake UoW (state + epoch published together) and
  `AssistanceEligibility` (state + epoch read together). Order coordinator → store lock;
  same-thread publications inside a foundation transaction are deferred until it exits;
  exceptions publish nothing. Routine fake composition detail, not a real OwnerFence ADR or
  production SQL locking claim; no foundation/Vision source edit.
- Clarified: injected scoped Teacher reader for Vision reads with independent device
  disclosure; consumed stays consumed while cleanup is open; D2 revision is not a cache
  validator. D1–D11 unchanged and still recommendations; implementation NOT_STARTED.

## 2026-10-17 — Codex revision-2 re-review

- NEEDS_REVISION (0 P1 / 1 P2): A1-PR01-F1 requires an explicit shared fake
  commit boundary through the foundation transaction and assistance state/epoch
  publication. Late-id cleanup is addressed; PR02–PR05 and both clarifications
  are closed at plan level. Details: evidence/notes/PLAN_CODEX_REREVIEW_20261017.md.
- Next: small planning revision 3 and re-review, no implementation. Revision-2
  bytes and prior reviews unchanged; D1–D11 remain recommendations, not approvals.

## 2026-10-17 — plan revision 2 (planning correction under the user's request)

- Revision 1 bytes (SHA256 bb072cf5…) kept as an ignored local historical draft
  (`evidence/local/planning-rev2-20261017/PLAN_REV1_bb072cf5_HISTORICAL_DRAFT.md`); never approved.
- Revision 2 addresses A1-PR01–PR05 and both clarifications; map in plan §16 and
  `evidence/notes/PLAN_REV2_CHANGES_20261017.md`. The revision-1 review record is unchanged.
- New pending owner decision **D11** (cancel vs completion linearization at the handoff commit).
  D6 recommendation refined (monotonic, settlement-gated release). D1–D11 remain
  recommendations; nothing is approved and implementation stays NOT_STARTED.
- Technical candidates updated below: TC-04 and TC-08 redefined, TC-10 added.

## 2026-10-17 — Codex plan revision 1 review

- NEEDS_REVISION: A1-PR01 late-create cancellation cleanup (P1); A1-PR02 semantic
  pin equivalence, A1-PR03 retry budget evidence, A1-PR04 completion/cancel commit
  ordering and A1-PR05 actual outbox recovery boundary (P2 each).
- Details: evidence/notes/PLAN_CODEX_REVIEW_20261017.md and matching metrics.
  Plan revision 1 SHA256 bb072cf5 and approval record remain unchanged; no D1–D10
  choice adopted. Next is a planning revision/re-review, not implementation.

## 2026-10-17 — planning setup (recorded by Claude under the user's planning request)

- **Mapping.** BE2-03 → FEAT-049 `be2-assistance-orchestration`, created with
  `tools/new_feature.py 49 be2-assistance-orchestration`. BE2-03 does not imply FEAT-003.
- **Stacked base.** Branch from f120c4f (BE2-02 C2 pushed checkpoint) as a candidate-only branch
  under BE2 roadmap §3.1; deviation from "branch from updated dev" is deliberate because dev has
  neither prerequisite. Not dev integration; not approval of BE2-01/02 runtime work.
- **Ignore rule.** `/features/FEAT-049-be2-assistance-orchestration/evidence/local/` added to
  `.gitignore` (same pattern as FEAT-048) for raw logs, scratch and prompts.

## Owner decisions pending (plan §13)

D1–D11 (revision 2; revision 1 had D1–D10) are recommendations only. None is selected until the owner approves an exact plan
revision/SHA256 with those choices.

## Technical candidates (routine, within existing conventions; revisable at review)

- **TC-01 request states** `scheduling`, `scheduled`, `analysis_ready`, `failed`, `cancelled`,
  `stale`; closed `status_reason` tokens. Distinct from DATA-23 pipeline and DATA-25 job states.
- **TC-02 level/policy refs.** `requested_level` is an opaque token allowlisted by the pinned
  policy snapshot; no level taxonomy is fixed (SRS taxonomy 0–4 is PROPOSED).
- **TC-03 purpose.** `purpose_code` comes from the policy/owner scope, never from the client.
- **TC-04 semantic identity (rev2).** Strict canonical SHA256 over org, session, canvas,
  target, region, checkpoint_ref, input_hash, sorted audience, purpose, level, reason class,
  child_intent hash, context_revision, policy ref/version and `assistance_context_digest`.
  Operation identities (assistance id, keys, client_request_id, principal/device/grant/turn,
  correlation, timestamps) are excluded. Same operation target with a different digest
  supersedes the older non-terminal request as `stale` instead of deduplicating.
  (Revision 1 omitted input_hash/audience/digest — A1-PR02.)
- **TC-05 region.** Region must exist in current policy; Child must be permitted in it.
- **TC-06 budget ledger.** Reservation states held/consumed/released, BE2-03-owned ledger; values
  from the policy port.
- **TC-07 cache provenance.** `cache_hit_of{assistance_id,analysis_id}`; Teacher/internal only.
- **TC-08 assistance_context_digest (rev2).** C2 strict canonical rules (reuse
  `strict_canonical_sha256`) over scope, roster/membership and region-policy revisions,
  contributor, exact per-member age months/provenance/revision and consent record/revision/
  purpose, policy, context revision and resolved source/render/input_hash. Never equal to or
  substituted for C2 `payload_digest`/`context_digest` or C1 `input_hash`.
- **TC-10 scheduling/settlement (rev2).** Retained create key `assist:<id>:<rev>:vision`,
  requester principal, RequestRef/JobScope; request-aware fenced `EligibilityPort` decorator;
  read-only job reader (by job id or target scan); internal settlement axis open→settled;
  budget released only when settled with no started attempt in any job's history.
- **TC-09 child_intent.** Accepted only on device-originated requests; Teacher requests carry null.
- **Error codes** reuse B22.1 / BE2-01 codes; disabled policy → 403 `FORBIDDEN_SCOPE`, absent/TBD
  policy → 409 `POLICY_UNRESOLVED`; no new public code in A1.
