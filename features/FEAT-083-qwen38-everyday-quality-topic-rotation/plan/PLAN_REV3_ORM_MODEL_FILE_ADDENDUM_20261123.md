# FEAT-083 Plan Rev3 — ORM mapping file clarification

**Date:** 2026-11-23
**Status:** APPROVED under the owner’s direct implementation instruction and the existing FEAT-083 task approval.
**Parent plans:** Rev1 and Rev2 remain in force.

## Change

The durable Parent rotation needs SQLAlchemy mappings in the Parent-owned declarative metadata. The correct existing mapping file is `backend/src/sketch2life/infrastructure/persistence/parent_models.py`; Rev1's filename `be1_models.py` refers to identity lookup models, not Parent-schema tables. The two additive rotation mappings already declared here are therefore authorized at this path. No BE1 identity table or existing Parent data is changed.

This is a source-file allowlist correction only. The approved privacy rules, rotation contract, catalog size, model pin, safety gates, runtime limits, and SRS direction remain unchanged.

## Additional allowed file

- `backend/src/sketch2life/infrastructure/persistence/parent_models.py`

All Rev1 and Rev2 files and constraints continue to apply. No migration execution is authorized.

## Acceptance

- Both ORM mappings match the additive Rev2 migration and remain inside the `parent` schema.
- Existing model/table definitions are preserved.
- The implementation status explicitly states that the migration was not executed and that no live database was verified.
