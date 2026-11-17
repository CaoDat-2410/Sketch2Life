# Montessori child-context personalization audit — 2026-09-29

- Type: documentation-only source inspection
- Status: diagnosis complete; proposed plan awaits owner approval
- Runtime/model execution: not performed
- Child records or profile data: not used

## Findings

The current V2 activity resolver receives the confirmed visual/narrated anchor set, age, semantic
catalog, compiler and narration text. It does not receive a persisted child profile or longitudinal
history. Its `child_interest_alignment` value is assigned from primary-versus-secondary visual
anchor ordering, so it describes current scene relevance, not an observed individual preference.
The demo-selected child is mock data; current feedback can capture completion, interest and
independence, but recommendation does not consume that history and completion does not establish
mastery.

The current source loads 100 base and 200 curated catalog profiles/variants. Activity metadata
already covers some age, objective, prerequisite, material, readiness and support dimensions. A
coverage audit is needed to find the exact missing combinations before deciding to expand the
catalog. Durable per-child personalization also requires a separate privacy/consent/persistence
decision; it is not silently authorized by this planning request.

## Source pointers

- `backend/src/sketch2life/application/services/semantic_activity_resolver.py`
- `backend/src/sketch2life/application/services/supervised_flow.py`
- `backend/src/sketch2life/contracts/schemas/workflow_records.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `apps/ui-mobile/src/context/AppContext.tsx` and demo profile fixtures
- Proposed plan: `../../plan/CHILD_CONTEXT_MONTESSORI_PERSONALIZATION_PLAN_20260929.md`

## Interpretation

Current results are age- and image-topic/catalog-aware but not yet history- or explicit-preference-
personalized. The safe next step is a catalog coverage audit plus a reviewed, explicit, minimal
child-context design; it is not an automatic inference of psychology from artwork or a blanket
increase in catalog size.
