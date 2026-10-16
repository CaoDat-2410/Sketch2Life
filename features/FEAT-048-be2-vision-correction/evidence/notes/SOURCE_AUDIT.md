# BE2-02 source/reuse audit —2026-10-16

Read-only audit at6dcc57ee0b3d053f071c8c92e72aaaee2e98d899. Line pins refer to this snapshot.
Codex used independent requirements and legacy-reuse reviewers. No implementation/test was run.

| Source | Pin / status |
|---|---|
| Master SRS FR022/023/061 |398–399,476 CONFIRMED; context-aware Vision, uncertainty/correction, unsafe/pending gate |
| SRS UC-018 |1265–1274; detailed use cases PROPOSED under B20 preamble1022; Child explains, Teacher confirms |
| SRS DTO/API preamble |1577: logical fields/enums/wire schemas PROPOSED_UNADOPTED |
| SRS DATA-22 / CMD-34 |1650 /1778; correction separate from original, response refs/version/author; device is not Teacher |
| SRS common command rules |1712–1733; current disclosure auth before accepted replay; idempotency/If-Match/distinct errors |
| SRS AT-CS-008 / UC tests |1006 /1273–1274; stale result cannot replace current meaning; cat→tiger provenance |
| FEAT-040 card BE2-02 |522–532; outputs, acceptance, runtime gates; handoffs133/135/137 |

Canonical paths:

- features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md
- features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md
- features/FEAT-044-be2-ai-job-foundation/plan/BE2_ROADMAP.md
- docs/context/SOURCE_REGISTER.md; docs/adr/ADR-0015-four-person-role-and-integration-allocation.md

## Reuse under backend/src/sketch2life/

| Path | Existing seam / gap |
|---|---|
| application/ports/vision_understanding_v2.py | Neutral understand interface; no typed topic/age/context |
| contracts/schemas/vision.py, vision_v2.py | Image/media/profile/observation/provenance; preserve legacy compatibility |
| infrastructure/ai/lightning_vision_v2.py | Injected JsonTransport/artifact_loader/clock; offline FakeTransport tests; source-only, no automatic retry |
| infrastructure/ai/qwen_vision.py | Injectable runner, lazy GPU imports; preserve, do not load model |
| application/ports/core_foundation.py | Checkpoint/asset/identity/consent/profile/membership/revision/scope; not full meaning/context adapter |
| application/ports/ai_jobs.py | Pinned job lineage; create/read/cancel only, no correction action or contributor binding |
| contracts/schemas/ai_contract_candidates.py | Shallow DATA-22 ShapeSpec/fixture, no full schema/CMD-34/persistence |

## Concrete mismatches

1. BE1 checkpoint is JSON; keep checksum/epoch/revision separate from rendered PNG/JPEG hash.
2. Legacy media PASS metadata has no image binding; require trusted admission receipt for exact render.
3. V2 forbids extras and lacks typed topic/age/context. narration_context is an adult hint; do not
   put Child intent there or claim the provider consumed the new context contract.
4. Lightning ignores processing-image refs during transport; first bridge rejects unsupported derived input.
5. New bridge validates canonical catalog/config/model provenance beyond current partial checks.
6. Preserve full typed original (entities/actions/relations/themes/ambiguous regions) and evidence;
   map label.value/nullable confidence, not a top label declared ground truth.
7. Lexical regression PASSED is not comprehensive moderation clearance.
8. Gate-A/old semantic principals and domain/child_age.py under-nine rules are not Teacher/Child
   authority. Current core_foundation.validate_age_months uses36–155 completed months.
9. BE1 effective-consent positive flow has an independent owner gate. Synthetic positive fixtures
   do not prove live class/consent integration or owner sign-off.

Actor interpretation for approval: bound Child may record own statement/proposal; scoped Teacher
confirms authoritative meaning. Exact proposal/confirmation states, uncertainty/provenance and
accepted_status representations are candidate design, not source-defined enums. READ_JOB is not
CORRECT/CONFIRM permission. Field rationale belongs in the plan/decision record before code.

Result: C1 offline component can progress without new infra. Actual typed provider-context support,
runtime quality/persistence and real BE1 adoption remain explicit later gates. BE2-01 approval
does not cover this card.
