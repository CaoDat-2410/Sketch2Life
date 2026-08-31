# P2-T3 Phase A approval record

- Status: APPROVED FOR IMPLEMENTATION
- Approved at: 2026-08-31
- Approver: Project owner direct instruction in the current conversation: `APPROVE P2-T3 PHASE A PLAN`
- Authoritative approval record: `../../approvals/TASK_APPROVAL.md`
- Approved plan: `../../plan/P2_T3_VISION_RESEARCH_PLAN.md` (plan revision 4)

## Approved scope

Phase A may implement only the provider-neutral vision contract, deterministic fake catalog and
adapter, adapter-ingress source/P2-T1 integrity validation, versioned lexical regression policy,
synthetic fixture manifest, contract tests, and feature-local evidence defined by the approved
research plan.

## Owner decisions accepted with this approval

1. The prohibited lexicon is synthetic-only, deterministic, and versioned. It may exercise only
   the plan's six closed category identifiers and contains no real child data. The project owner
   reviews it. Changing its category set, governance, or policy/match-view contract needs a new
   plan-and-approval review; a synthetic entry update must bump `lexicon_version` and be recorded
   in feature-local evidence.
2. `label`, `predicate`, and `note` remain open normalized structured text with a non-ground-truth
   language declaration under `ObservedTextV1` / `TextLanguageDeclarationV1`.
3. `AmbiguousRegionCandidateV1` has no geometry and is not an evidence-reference target in Phase A.

## Non-goals and continuing gates

This approval does not allow Qwen dependency/model/weight work, GPU/provider/cloud execution,
runtime profile selection, benchmark execution, real-model provenance, semantic-paraphrase safety
claims, any real child data, credentials, API/UI/mobile/session/job/database/queue/storage work,
P2-T4/P2-T5 work, or any user-facing, Integration Sprint, or Gate A promotion. Those remain
separately gated, including all P2-T3 Phase B work.

## Implementation acceptance boundary

Implementation must satisfy the approved plan's fixture and contract matrix, preserve the P2-T1
boundary and immutable source reference, never expose matched policy text or lexicon entries in a
result, and record validation evidence under this feature. Approval does not itself mark Phase A
implemented or complete.
