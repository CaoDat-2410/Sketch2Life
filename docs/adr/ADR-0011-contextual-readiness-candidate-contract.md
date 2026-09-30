# ADR-0011: Versioned two-phase Montessori context and readiness flow

- Status: Accepted within owner-approved FEAT-033 revision 3
- Date: 2026-09-29
- Decision owners: project owner and implementation team
- Scope: P1 candidate discovery and adult-entered eligibility context; no durable profile storage

## Context

FEAT-033 replaces the profile-level readiness checklist with questions tied to a small,
age/topic-compatible candidate set. The existing P1 V1 options endpoints are already consumed by
the app and tests. The existing catalog also has two distinct cases: explicitly present readiness
metadata (including an authored empty list, meaning no readiness prerequisite) and curated variants
whose readiness metadata has not been authored. Treating both cases as the same empty list either
blocks valid activities or silently treats unknown criteria as satisfied.

## Decision

1. Preserve the existing `P1ContextOptionsRequestV1` and V1 options routes for compatibility.
2. Add `ActivityContextCandidateSetV2` on the read-only
   `GET /v1/sessions/{id}/p1/context-candidates` route. It contains at most three age/topic
   candidates, display text, authored readiness status/criteria, prerequisite IDs, grouped material
   choices and labels, and minimum supervision. This is a question set, not final recommendations.
3. Add `P1ContextOptionsRequestV2` on
   `POST /v1/sessions/{id}/p1/context-options/finalize`. It must include the IDs from the bounded
   candidate set, the adult's session-only profile/context answers, explicit adult participation,
   and per-candidate confirmation that the adult can meet the displayed supervision level. V2
   profile data carries neither fabricated progress nor a profile-level supervision enum. The
   backend recomputes the bounded set and rejects any client-supplied set that differs; final hard
   eligibility and ranking run only within candidates for which supervision was confirmed. Profile
   signals cannot expand the confirmed drawing topic or introduce activities outside the set.
4. A catalog record with authored readiness metadata and no readiness IDs has no readiness
   prerequisite. A record marked `UNSPECIFIED` is not equivalent to an authored empty list. The V2
   candidate discovery route currently excludes `UNSPECIFIED` records before taking its bounded
   shortlist, so incomplete metadata cannot consume all three places and leave no finalizable
   alternatives. The no-profile V1 route preserves its previous candidate behavior. The catalog
   audit reports the excluded metadata gap; no readiness criteria are inferred or fabricated.
5. Materials are asked only for IDs and groups present in the preliminary candidate set. The adult
   can confirm actual material options; backend group semantics remain hard gates.
6. Unknown readiness, prerequisites, materials, and insufficient supervision exclude only the
   dependent candidate. No requirement is inferred from the image, age, interests, or AI tags.
   Supervision confirmation is activity-specific; an adult's general presence does not silently
   imply that every activity's minimum level can be met.
7. The endpoints and child profile remain volatile for the request/session. V1 remains available;
   no storage, authentication, or provider boundary is changed by this decision.
8. Age 0–3 caregiver confirmation must survive beyond the candidate-options response through the
   deterministic P1 filter. `P1ContextV2` carries this explicit session fact and requires
   `caregiver_participating=true` below 36 months. Preserve `P1ContextV1` for existing 36+ clients,
   but reject under-three submissions on V1 because it cannot represent caregiver presence.
9. Add `P1ContextV3` for the revised mobile two-phase candidate flow at every supported age. It
   requires `candidate_selection_mode=CONTEXTUAL_SHORTLIST`; below 36 months it also inherits the
   V2 caregiver requirement. During filtering, the backend recomputes the deterministic, unranked,
   authored-readiness phase-one set, verifies that the selected activity belongs to it, resolves
   only that activity, and then applies the existing P1 compiler hard gates. V1/V2 retain their
   legacy ranked-options behavior. This prevents re-ranking drift while keeping existing clients
   compatible and never trusts an arbitrary client-supplied activity ID.
10. The P1 compiler consumes validated context through an explicit V1 eligibility projection;
    V2/V3-only caregiver and candidate-flow facts remain in the versioned session contract.

## Consequences

- The client cannot treat preliminary candidates as final recommendations and cannot widen the
  final shortlist.
- Missing catalog readiness metadata can reduce the final candidate count. The UI reports this
  honestly; catalog entries are not assigned invented readiness criteria.
- V1/V2 clients remain compatible. The new mobile path is explicit about `P1ContextV3`.
- Under-three P1ContextV2/V3 sessions require caregiver confirmation and cannot bypass the check by
  calling legacy context/filter routes directly. The V3 selected activity must be in the
  server-recomputed phase-one set before any P1 hard-gate evaluation.
- Catalog coverage and readiness-metadata completeness must be reported separately.

## Verification boundary

Contract tests must cover V1/V2 compatibility, the V2 shortlist bound, P1ContextV3 candidate
allowlisting/selection, readiness metadata distinctions, material alternative groups, and fail-closed
candidate-specific behavior. Android and Lightning smoke evidence remain required by FEAT-033
acceptance criteria.
