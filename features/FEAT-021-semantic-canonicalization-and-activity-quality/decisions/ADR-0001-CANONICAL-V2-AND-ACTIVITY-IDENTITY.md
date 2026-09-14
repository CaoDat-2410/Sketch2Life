# ADR-0001 — Canonical V2 and Activity Identity

## Status

Accepted

## Decision

1. `BackendWorkflowResultV2` is the canonical decision contract.
2. V1 is a compatibility projection from V2 and never makes an independent semantic or activity decision.
3. A workflow creates one scene-understanding identity. Age bands consume that identity and vary only age adaptation and catalog ranking.
4. Strong child narration is preferred for `PRIMARY_CHILD_INTEREST`; VLM observations confirm or qualify it.
5. Activity selection is catalog-only. AI may propose an existing catalog ID but cannot create a new activity at runtime.
6. Activity identity is `activity_family_id`, `activity_id`, `activity_version`, `variant_id`, and `catalog_revision`.
7. If no catalog activity survives age, prerequisite, material, safety, and eligibility gates, the age band is `UNAVAILABLE` and is never silently converted to a generic fallback.

## Consequences

- V2 fields are the source consumed by downstream handoffs.
- Legacy data may remain in compatibility output during migration, but it must be derived from V2.
- Scores are separated into concept confidence, child-interest alignment, age fit, safety, catalog quality, and overall personalization.
- Existing profile versions are reconciled against the canonical activity template version.
- PixiJS, video generation, production human gates, and caregiver persistence remain follow-up features.
